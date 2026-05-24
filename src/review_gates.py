from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from io_utils import utc_timestamp


VERDICTS = {"PASS", "WARN", "FAIL", "BLOCKED", "ERROR", "NOT_APPLICABLE"}
STRONG_POLICY_WORDS = ("必须", "必然", "确定", "全面", "立刻", "应当立即", "唯一")


def review_plan(query_jobs: list[dict[str, Any]], required_sections: list[str]) -> dict[str, Any]:
    covered = {job.get("section") for job in query_jobs}
    missing = [section for section in required_sections if section not in covered]
    malformed = [
        job["id"]
        for job in query_jobs
        if not job.get("prompt") or not job.get("expected_fields") or not job.get("notebook_id")
    ]
    verdict = "PASS" if not missing and not malformed else "FAIL"
    return _result(
        reviewer="PlanReviewerAgent",
        verdict=verdict,
        reason_code="pass" if verdict == "PASS" else "query_plan_contract_gap",
        summary="QueryPlan covers required sections and has runnable query jobs." if verdict == "PASS" else "QueryPlan is missing sections or runnable fields.",
        details={"missing_sections": missing, "malformed_jobs": malformed, "job_count": len(query_jobs)},
        issues=[
            {"severity": "FAIL", "message": f"Missing section query coverage: {section}"}
            for section in missing
        ]
        + [
            {"severity": "FAIL", "message": f"Malformed QueryJob: {job_id}"}
            for job_id in malformed
        ],
        required_revisions=[
            {"target": "QueryPlannerAgent", "action": "Add or repair QueryJob coverage before retrieval."}
        ]
        if verdict != "PASS"
        else [],
    )


def review_retrieval_completeness(query_jobs: list[dict[str, Any]], query_results: list[dict[str, Any]]) -> dict[str, Any]:
    results_by_id = {result.get("job_id"): result for result in query_results}
    missing_results = [job["id"] for job in query_jobs if job["id"] not in results_by_id]
    incomplete_fields: list[dict[str, Any]] = []
    error_results = [
        {"job_id": result.get("job_id"), "reason_code": result.get("reason_code"), "summary": result.get("summary", "")}
        for result in query_results
        if result.get("status") != "PASS" and result.get("verdict") != "PASS"
    ]
    for job in query_jobs:
        result = results_by_id.get(job["id"], {})
        parsed = result.get("parsed_fields") or result.get("structured_answer") or {}
        missing = [
            field
            for field in job.get("expected_fields", [])
            if field not in parsed or parsed.get(field) is None or parsed.get(field) == ""
        ]
        if missing:
            incomplete_fields.append({"job_id": job["id"], "missing_fields": missing})
    verdict = "PASS" if not missing_results and not incomplete_fields and not error_results else "BLOCKED"
    return _result(
        reviewer="RetrievalCompletenessGate",
        verdict=verdict,
        reason_code="pass" if verdict == "PASS" else "incomplete_retrieval",
        summary="All QueryJobs produced expected fields." if verdict == "PASS" else "Some QueryJobs are missing results, expected fields, or successful NotebookLM responses.",
        details={"missing_results": missing_results, "incomplete_fields": incomplete_fields, "error_results": error_results},
        issues=[
            {"severity": "BLOCKED", "message": f"Missing QueryJob result: {job_id}"}
            for job_id in missing_results
        ]
        + [
            {"severity": "BLOCKED", "message": f"QueryJob {item['job_id']} missing fields: {', '.join(item['missing_fields'])}"}
            for item in incomplete_fields
        ]
        + [
            {"severity": "BLOCKED", "message": f"QueryJob {item['job_id']} failed: {item.get('summary') or item.get('reason_code')}"}
            for item in error_results
        ],
        followup_queries=[
            {
                "field": field,
                "section": next((job["section"] for job in query_jobs if job["id"] == item["job_id"]), "unknown"),
                "question": f"请补充 QueryJob {item['job_id']} 缺失字段 {field}。",
                "expected_fields": [field],
            }
            for item in incomplete_fields
            for field in item["missing_fields"]
        ],
        required_revisions=[
            {"target": "NotebookLMAdapter", "action": "Run bounded follow-up retrieval before polished output."}
        ]
        if verdict != "PASS"
        else [],
    )


def review_notebooklm_preflight(auth_status: dict[str, Any], sources: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    if mode == "mock":
        return _result(
            reviewer="NotebookLMPreflightGate",
            verdict="PASS",
            reason_code="mock_mode",
            summary="Mock mode does not require NotebookLM auth.",
            details={"auth_status": auth_status, "source_count": len(sources), "mode": mode},
        )
    issues: list[dict[str, Any]] = []
    if auth_status.get("status") not in {"PASS", "ok"}:
        issues.append({"severity": "BLOCKED", "message": auth_status.get("summary", "NotebookLM auth check failed."), "reason_code": auth_status.get("reason_code", "auth_failed")})
    if not sources:
        issues.append({"severity": "WARN", "message": "NotebookLM source list is empty or unavailable."})
    hard = [issue for issue in issues if issue["severity"] in {"BLOCKED", "FAIL", "ERROR"}]
    verdict = "BLOCKED" if hard else "WARN" if issues else "PASS"
    return _result(
        reviewer="NotebookLMPreflightGate",
        verdict=verdict,
        reason_code="pass" if verdict == "PASS" else "notebooklm_preflight_issue",
        summary="NotebookLM real-mode preflight completed." if verdict == "PASS" else "NotebookLM real-mode preflight found issues.",
        details={"auth_status": auth_status, "source_count": len(sources), "mode": mode},
        issues=issues,
        required_revisions=[
            {"target": "NotebookLMAdapter", "action": "Fix NotebookLM CLI path/auth before retrieval."}
        ]
        if hard
        else [],
    )


def review_material_pack_audit(audits: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [audit for audit in audits if audit.get("verdict") == "BLOCKED"]
    errors = [audit for audit in audits if audit.get("verdict") == "ERROR"]
    if errors:
        verdict = "ERROR"
        reason_code = "material_audit_error"
    elif blocked:
        verdict = "BLOCKED"
        reason_code = "missing_material_fields"
    else:
        verdict = "PASS"
        reason_code = "pass"
    return _result(
        reviewer="MaterialPackAudit",
        verdict=verdict,
        reason_code=reason_code,
        summary="Material package audit completed.",
        details={"audits": audits},
        issues=[
            {"severity": audit.get("verdict", "WARN"), "message": audit.get("summary", "Material package audit issue."), "package_id": audit.get("package_id")}
            for audit in blocked + errors
        ],
        followup_queries=[query for audit in blocked for query in audit.get("followup_queries", [])],
        required_revisions=[
            {"target": "MaterialPackAgent", "action": "Resolve missing material fields or keep gaps visible."}
        ]
        if verdict != "PASS"
        else [],
    )


def review_material_packages(audits: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [audit for audit in audits if audit.get("verdict") == "BLOCKED"]
    return _result(
        reviewer="MaterialCoverageReviewerAgent",
        verdict="PASS" if not blocked else "BLOCKED",
        reason_code="pass" if not blocked else "missing_material",
        summary="Material packages are writable." if not blocked else "Some material packages are missing required fields.",
        details={"blocked": blocked},
        issues=[
            {"severity": "BLOCKED", "message": audit.get("summary", "Missing material."), "package_id": audit.get("package_id")}
            for audit in blocked
        ],
        followup_queries=[query for audit in blocked for query in audit.get("followup_queries", [])],
        required_revisions=[
            {"target": "MaterialPackAgent", "action": "Run follow-up queries or leave explicit MATERIAL_NEEDED markers."}
        ]
        if blocked
        else [],
    )


def review_evidence_use(query_results: list[dict[str, Any]], material_packages: list[dict[str, Any]]) -> dict[str, Any]:
    source_signals = 0
    citation_signals = 0
    for result in query_results:
        for key in ("sources", "source_refs", "references"):
            value = result.get(key)
            if isinstance(value, list):
                source_signals += len(value)
        for key in ("citations", "citation_refs"):
            value = result.get(key)
            if isinstance(value, list):
                citation_signals += len(value)
    package_refs = sum(len(package.get("source_refs", [])) for package in material_packages if isinstance(package.get("source_refs", []), list))
    verdict = "PASS" if source_signals or citation_signals or package_refs else "WARN"
    return _result(
        reviewer="EvidenceUseReviewerAgent",
        verdict=verdict,
        reason_code="pass" if verdict == "PASS" else "no_source_trace_signals",
        summary="Evidence/source trace signals were found." if verdict == "PASS" else "No explicit source or citation signals were found in query results or material packages.",
        details={
            "query_result_source_signals": source_signals,
            "query_result_citation_signals": citation_signals,
            "material_package_source_refs": package_refs,
        },
        issues=[
            {
                "severity": "WARN",
                "message": "NotebookLM answers were parsed, but source/citation references are not yet propagated into material packages.",
            }
        ]
        if verdict == "WARN"
        else [],
        required_revisions=[
            {"target": "NotebookLMAdapter/MaterialPackAgent", "action": "Propagate NotebookLM source refs into material packages and claim rows."}
        ]
        if verdict == "WARN"
        else [],
    )


def review_section_contracts(section_drafts: dict[str, str], section_contracts: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for section_id, contract in section_contracts.items():
        draft = section_drafts.get(section_id, "")
        body = _section_body(draft)
        if not body.strip():
            issues.append({"severity": "BLOCKED", "section": section_id, "message": "Section draft is missing."})
            continue
        for output_item in contract.get("output_shape", []):
            if output_item and output_item not in body:
                issues.append({"severity": "WARN", "section": section_id, "message": f"Output-shape item is not explicit in draft: {output_item}"})
        for forbidden in contract.get("forbidden", []):
            if forbidden and forbidden in body and not _is_negated_forbidden(body, forbidden):
                issues.append({"severity": "WARN", "section": section_id, "message": f"Forbidden wording appears literally: {forbidden}"})
        if "MATERIAL_NEEDED" in body:
            issues.append({"severity": "WARN", "section": section_id, "message": "Section still contains MATERIAL_NEEDED."})
    hard = [issue for issue in issues if issue["severity"] in {"BLOCKED", "FAIL", "ERROR"}]
    verdict = "BLOCKED" if hard else "WARN" if issues else "PASS"
    return _result(
        reviewer="SectionContractReviewerAgent",
        verdict=verdict,
        reason_code="pass" if verdict == "PASS" else "section_contract_gaps",
        summary="Section drafts satisfy visible contract checks." if verdict == "PASS" else "Some section contract expectations are missing or only implicit.",
        details={"issues": issues},
        issues=issues,
        required_revisions=[
            {"target": "SectionComposerAgent", "action": "Make required output-shape and material gaps explicit in section drafts."}
        ]
        if issues
        else [],
    )


def review_claim_scope(section_drafts: dict[str, str], claims: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    draft_by_section = section_drafts
    used_claim_ids: set[str] = set()
    for claim in claims:
        claim_id = claim.get("claim_id")
        claim_text = claim.get("claim_text") or ""
        if not claim_text:
            continue
        support = str(claim.get("support_level", "")).lower()
        allowed_sections = set(claim.get("allowed_sections", []))
        for section_id, draft in draft_by_section.items():
            body = _section_body(draft)
            if claim_text not in body:
                continue
            used_claim_ids.add(str(claim_id))
            if allowed_sections and section_id not in allowed_sections:
                issues.append({"severity": "WARN", "claim_id": claim_id, "section": section_id, "message": "Claim appears outside allowed sections."})
            if support in {"weak", "medium"} and any(word in body for word in STRONG_POLICY_WORDS):
                issues.append({"severity": "WARN", "claim_id": claim_id, "section": section_id, "message": "Weak/medium support claim appears in a section with strong policy language."})
    unused = [claim for claim in claims if claim.get("claim_id") and str(claim.get("claim_id")) not in used_claim_ids]
    for claim in unused:
        issues.append({"severity": "WARN", "claim_id": claim.get("claim_id"), "message": "Claim candidate was not used in drafts."})
    return _result(
        reviewer="ClaimAuditAgent",
        verdict="WARN" if issues else "PASS",
        reason_code="claim_scope_warnings" if issues else "pass",
        summary="Claim scope audit found warnings." if issues else "Draft claim use stays within known claim candidates.",
        details={"unused_claims": unused, "issues": issues},
        issues=issues,
        required_revisions=[
            {"target": "SectionComposerAgent", "action": "Bind claims to allowed sections and avoid over-strong language for weak/medium support."}
        ]
        if issues
        else [],
    )


def review_report_quality(final_report: str, review_reports: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    non_green = [
        {"reviewer": report.get("reviewer"), "verdict": report.get("verdict"), "reason_code": report.get("reason_code")}
        for report in review_reports
        if report.get("verdict") not in {"PASS", "NOT_APPLICABLE"}
    ]
    if non_green:
        issues.append({"severity": "WARN", "message": "Upstream review gates are not all green.", "reports": non_green})
    if "MATERIAL_NEEDED" in final_report:
        issues.append({"severity": "WARN", "message": "Final report still contains MATERIAL_NEEDED."})
    if "附录一：材料包索引" not in final_report or "附录四：审查状态" not in final_report:
        issues.append({"severity": "WARN", "message": "Final report is missing expected audit appendices."})
    return _result(
        reviewer="ReportQualityReviewerAgent",
        verdict="WARN" if issues else "PASS",
        reason_code="report_quality_warnings" if issues else "pass",
        summary="Report quality gate completed.",
        details={"issues": issues},
        issues=issues,
        required_revisions=[
            {"target": "MainAgent", "action": "Resolve non-green gates before decision-grade output."}
        ]
        if issues
        else [],
    )


def review_kill_argument(final_report: str) -> dict[str, Any]:
    unresolved = []
    if "MATERIAL_NEEDED" in final_report:
        unresolved.append("报告仍包含 MATERIAL_NEEDED，占位说明需要补充材料。")
    if "附录四：审查状态" not in final_report:
        unresolved.append("报告缺少审查状态附录，无法快速判断非绿色 gate。")
    return _result(
        reviewer="KillArgumentAgent",
        verdict="WARN" if unresolved else "PASS",
        reason_code="material_needed_remaining" if unresolved else "pass",
        summary="Strongest objection review completed.",
        details={
            "strongest_objections": [
                "材料是否足以支撑热点升温判断。",
                "比较维度是否对所有热点一致。",
                "影响与建议是否超出 NotebookLM 材料包。",
                "非绿色审查 gate 是否仍被包装成完整结论。",
            ],
            "unresolved": unresolved,
        },
        issues=[{"severity": "WARN", "message": item} for item in unresolved],
    )


def review_drift(review_reports: list[dict[str, Any]], base_dir: str | Path) -> dict[str, Any]:
    stale: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    base_dir = Path(base_dir)
    for report in review_reports:
        for path, old_hash in (report.get("audited_input_hashes") or {}).items():
            if old_hash == "MISSING":
                missing.append({"path": path, "reviewer": str(report.get("reviewer"))})
                continue
            target = Path(path)
            if not target.is_absolute():
                target = base_dir / target
            if not target.exists():
                missing.append({"path": path, "reviewer": str(report.get("reviewer"))})
                continue
            new_hash = file_sha256(target)
            if new_hash != old_hash:
                stale.append({"path": path, "reviewer": str(report.get("reviewer")), "old_hash": old_hash, "new_hash": new_hash})
    verdict = "PASS" if not stale and not missing else "ERROR"
    return _result(
        reviewer="DriftReviewerAgent",
        verdict=verdict,
        reason_code="pass" if verdict == "PASS" else "reviewed_input_changed",
        summary="No reviewed input drift detected." if verdict == "PASS" else "Reviewed input hashes are stale or missing.",
        details={"stale": stale, "missing": missing},
        issues=[
            {"severity": "ERROR", "message": f"Reviewed input changed after audit: {item['path']}", "reviewer": item["reviewer"]}
            for item in stale
        ]
        + [
            {"severity": "ERROR", "message": f"Reviewed input missing after audit: {item['path']}", "reviewer": item["reviewer"]}
            for item in missing
        ],
        required_revisions=[
            {"target": "MainAgent", "action": "Rerun affected review gates after artifact changes."}
        ]
        if verdict != "PASS"
        else [],
    )


def attach_audited_hashes(report: dict[str, Any], paths: list[str | Path], base_dir: str | Path | None = None) -> dict[str, Any]:
    report = dict(report)
    report["audited_input_hashes"] = hash_artifacts(paths, base_dir)
    return report


def hash_artifacts(paths: list[str | Path], base_dir: str | Path | None = None) -> dict[str, str]:
    hashes: dict[str, str] = {}
    base = Path(base_dir) if base_dir else None
    for path in paths:
        target = Path(path)
        key = str(target)
        if not target.is_absolute() and base is not None:
            target = base / target
        if base and target.is_relative_to(base):
            key = str(target.relative_to(base))
        else:
            key = str(target)
        hashes[key] = file_sha256(target) if target.exists() and target.is_file() else "MISSING"
    return hashes


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _result(
    reviewer: str,
    verdict: str,
    reason_code: str,
    summary: str,
    details: dict[str, Any],
    followup_queries: list[dict[str, Any]] | None = None,
    issues: list[dict[str, Any]] | None = None,
    required_revisions: list[dict[str, Any]] | None = None,
    audited_input_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    if verdict not in VERDICTS:
        verdict = "ERROR"
        reason_code = "invalid_verdict"
    return {
        "audit_skill": "policy-report-reviewer",
        "reviewer": reviewer,
        "verdict": verdict,
        "reason_code": reason_code,
        "summary": summary,
        "issues": issues or [],
        "followup_queries": followup_queries or [],
        "required_revisions": required_revisions or [],
        "audited_input_hashes": audited_input_hashes or {},
        "details": details,
        "generated_at": utc_timestamp(),
    }


def _section_body(draft: str) -> str:
    marker = "\n## 本节契约检查"
    if marker not in draft:
        return draft
    return draft.split(marker, 1)[0]


def _is_negated_forbidden(text: str, phrase: str) -> bool:
    index = text.find(phrase)
    if index < 0:
        return False
    prefix = text[max(0, index - 8):index]
    return any(marker in prefix for marker in ("避免", "不要", "不得", "不能", "禁止"))
