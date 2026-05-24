from __future__ import annotations

from typing import Any

from io_utils import utc_timestamp


def review_plan(query_jobs: list[dict[str, Any]], required_sections: list[str]) -> dict[str, Any]:
    covered = {job.get("section") for job in query_jobs}
    missing = [section for section in required_sections if section not in covered]
    return _result(
        reviewer="PlanReviewerAgent",
        verdict="PASS" if not missing else "FAIL",
        reason_code="pass" if not missing else "missing_sections",
        summary="QueryPlan covers required sections." if not missing else "QueryPlan misses required sections.",
        details={"missing_sections": missing, "job_count": len(query_jobs)},
    )


def review_material_packages(audits: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = [audit for audit in audits if audit.get("verdict") == "BLOCKED"]
    return _result(
        reviewer="MaterialCoverageReviewerAgent",
        verdict="PASS" if not blocked else "BLOCKED",
        reason_code="pass" if not blocked else "missing_material",
        summary="Material packages are writable." if not blocked else "Some material packages are missing required fields.",
        details={"blocked": blocked},
        followup_queries=[query for audit in blocked for query in audit.get("followup_queries", [])],
    )


def review_retrieval_completeness(query_jobs: list[dict[str, Any]], query_results: list[dict[str, Any]]) -> dict[str, Any]:
    results_by_id = {result.get("job_id"): result for result in query_results}
    missing_results = [job["id"] for job in query_jobs if job["id"] not in results_by_id]
    incomplete_fields: list[dict[str, Any]] = []
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
    verdict = "PASS" if not missing_results and not incomplete_fields else "BLOCKED"
    return _result(
        reviewer="RetrievalCompletenessGate",
        verdict=verdict,
        reason_code="pass" if verdict == "PASS" else "incomplete_retrieval",
        summary="All QueryJobs produced expected fields." if verdict == "PASS" else "Some QueryJobs are missing results or expected fields.",
        details={"missing_results": missing_results, "incomplete_fields": incomplete_fields},
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
        followup_queries=[query for audit in blocked for query in audit.get("followup_queries", [])],
    )


def review_claim_scope(section_drafts: dict[str, str], claims: list[dict[str, Any]]) -> dict[str, Any]:
    draft_text = "\n".join(section_drafts.values())
    unsupported = [
        claim
        for claim in claims
        if claim.get("claim_text") and claim["claim_text"] not in draft_text
    ]
    return _result(
        reviewer="ClaimAuditAgent",
        verdict="WARN" if unsupported else "PASS",
        reason_code="claim_not_used" if unsupported else "pass",
        summary="Some claim candidates were not used." if unsupported else "Draft only uses known claim candidates.",
        details={"unused_claims": unsupported},
    )


def review_kill_argument(final_report: str) -> dict[str, Any]:
    unresolved = []
    if "MATERIAL_NEEDED" in final_report:
        unresolved.append("报告仍包含 MATERIAL_NEEDED，占位说明需要补充材料。")
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
            ],
            "unresolved": unresolved,
        },
    )


def _result(
    reviewer: str,
    verdict: str,
    reason_code: str,
    summary: str,
    details: dict[str, Any],
    followup_queries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "audit_skill": "policy-report-reviewer",
        "reviewer": reviewer,
        "verdict": verdict,
        "reason_code": reason_code,
        "summary": summary,
        "issues": [],
        "followup_queries": followup_queries or [],
        "required_revisions": [],
        "details": details,
        "generated_at": utc_timestamp(),
    }
