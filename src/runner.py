from __future__ import annotations

import argparse
import concurrent.futures as futures
import shutil
import time
from pathlib import Path
from typing import Any

from agent_runtime import build_agent_runtime
from io_utils import ensure_dir, load_yaml, timestamp_run_id, update_workflow_state, utc_timestamp, write_json, write_text
from manifest import build_manifest, collect_artifacts
from material_pack_builder import audit_material_package, build_material_packages
from material_compressor import compress_materials
from matrix_builder import build_all_matrices
from notebooklm_adapter import NotebookLMAdapter
from progress import append_progress_log, record_artifact_event, update_task_ledger, write_policy_report_contract, write_run_status_md
from query_planner import build_query_jobs
from report_assembler import assemble_report, build_abstract_prompt
from review_gates import (
    attach_audited_hashes,
    review_claim_scope,
    review_drift,
    review_evidence_use,
    review_kill_argument,
    review_material_pack_audit,
    review_material_packages,
    review_notebooklm_preflight,
    review_plan,
    review_report_quality,
    review_retrieval_completeness,
    review_section_contracts,
)
from section_composer import build_section_prompt, compose_section
from section_planner import build_report_plan, build_section_plan
from source_deep_dive import (
    DEFAULT_SOURCE_DEEP_DIVE_LANES,
    build_citation_sweep_job,
    build_source_deep_dive_candidates,
    build_source_deep_dive_jobs,
)


def run_workflow(task_config_path: str, run_id: str | None = None) -> dict[str, Any]:
    project_dir = Path(__file__).resolve().parents[1]
    config_path = Path(task_config_path)
    if not config_path.is_absolute():
        config_path = project_dir / config_path

    config = load_yaml(config_path)
    task_spec = config["task"]
    execution = config.get("execution", {})
    agent_runtime = build_agent_runtime(config.get("agent_runtime", {}))
    run_id = run_id or timestamp_run_id()
    output_root = project_dir / execution.get("output_root", "runs")
    run_dir = ensure_dir(output_root / run_id)
    ensure_dir(run_dir / "review_reports")
    write_policy_report_contract(run_dir, task_spec)
    _mark_phase(run_dir, "preflight", "RUNNING", "Validate runtime capability policy.", {"config": str(config_path)})
    record_artifact_event(run_dir, "preflight", "IntegrationAgent", run_dir / "POLICY_REPORT_CONTRACT.md", "Per-run anti-drift contract.")

    write_json(run_dir / "agent_runtime.json", agent_runtime.manifest())
    record_artifact_event(run_dir, "preflight", "IntegrationAgent", run_dir / "agent_runtime.json", "Agent runtime manifest.")
    runtime_issues = agent_runtime.validate()
    write_json(run_dir / "agent_runtime_validation.json", runtime_issues)
    record_artifact_event(run_dir, "preflight", "IntegrationAgent", run_dir / "agent_runtime_validation.json", "Runtime validation result.", "ERROR" if runtime_issues else "PASS")
    if runtime_issues:
        _mark_phase(
            run_dir,
            "preflight",
            "ERROR",
            "Fix agent runtime config before running.",
            {"config": str(config_path), "agent_runtime_issues": runtime_issues},
        )
        raise RuntimeError(f"Agent runtime configuration is invalid: {runtime_issues}")
    _mark_phase(
        run_dir,
        "preflight",
        "PASS",
        "Load dimension and section contracts.",
        {"config": str(config_path), "agent_runtime_profile": agent_runtime.profile},
    )
    dimensions = load_yaml(project_dir / "config" / "dimension_registry.yaml")
    section_contracts = load_yaml(project_dir / "config" / "section_contracts.yaml")

    write_json(run_dir / "task_spec.json", task_spec)
    record_artifact_event(run_dir, "task_spec", "IntegrationAgent", run_dir / "task_spec.json", "Normalized task specification.")
    _mark_phase(run_dir, "task_spec", "PASS", "Build NotebookLM query plan.", {"topic": task_spec["topic"]})

    query_jobs = build_query_jobs(task_spec, dimensions, section_contracts, run_dir)
    write_json(run_dir / "query_jobs.json", query_jobs)
    record_artifact_event(run_dir, "query_planning", "QueryPlannerAgent", run_dir / "query_jobs.json", "NotebookLM query jobs.")
    for job in query_jobs:
        update_task_ledger(
            run_dir,
            job["id"],
            {
                "owner_agent": "NotebookLMAdapter",
                "stage": "retrieval",
                "status": "PENDING",
                "inputs": [job.get("prompt_file")],
                "outputs": [job.get("output_target")],
                "notebook_id": job.get("notebook_id"),
                "query_type": job.get("query_type"),
            },
        )
    plan_review = review_plan(query_jobs, task_spec.get("sections", []))
    plan_review = attach_audited_hashes(plan_review, ["task_spec.json", "query_jobs.json"], run_dir)
    write_json(run_dir / "review_reports" / "plan_review.json", plan_review)
    record_artifact_event(run_dir, "query_planning", "PlanReviewerAgent", run_dir / "review_reports" / "plan_review.json", "Query plan review.", plan_review["verdict"])
    _mark_phase(run_dir, "query_planning", plan_review["verdict"], "Check NotebookLM auth and sources.", {"job_count": len(query_jobs)})

    adapter = NotebookLMAdapter(
        mode=execution.get("mode", "mock"),
        cli_path=execution.get("notebooklm_cli_path"),
        command_log_path=run_dir / "notebooklm_command_log.jsonl",
        ask_timeout_seconds=int(execution.get("notebooklm_ask_timeout_seconds", 180)),
    )
    auth_status = adapter.check_auth()
    write_json(run_dir / "notebooklm_auth.json", auth_status)
    record_artifact_event(run_dir, "notebooklm", "NotebookLMAdapter", run_dir / "notebooklm_auth.json", "NotebookLM auth check result.", auth_status.get("status", "PASS"))
    sources = adapter.list_sources(task_spec["notebook_id"])
    write_json(run_dir / "notebooklm_sources.json", sources)
    record_artifact_event(run_dir, "notebooklm", "NotebookLMAdapter", run_dir / "notebooklm_sources.json", "NotebookLM source list.")
    notebooklm_preflight = review_notebooklm_preflight(auth_status, sources, execution.get("mode", "mock"))
    notebooklm_preflight = attach_audited_hashes(notebooklm_preflight, ["notebooklm_auth.json", "notebooklm_sources.json"], run_dir)
    write_json(run_dir / "review_reports" / "notebooklm_preflight_review.json", notebooklm_preflight)
    record_artifact_event(run_dir, "notebooklm", "NotebookLMPreflightGate", run_dir / "review_reports" / "notebooklm_preflight_review.json", "NotebookLM preflight review.", notebooklm_preflight["verdict"])
    if notebooklm_preflight["verdict"] in {"BLOCKED", "FAIL", "ERROR"}:
        _mark_phase(run_dir, "notebooklm", notebooklm_preflight["verdict"], "Fix NotebookLM CLI/auth before retrieval.", {"auth_status": auth_status, "source_count": len(sources)})
        raise RuntimeError(f"NotebookLM preflight failed: {notebooklm_preflight}")

    ensure_dir(run_dir / "query_results")
    max_concurrency = _configured_concurrency(execution)
    _mark_phase(run_dir, "retrieval", "RUNNING", "Execute bounded NotebookLM query jobs.", {"max_concurrency": max_concurrency}, active_tasks=[job["id"] for job in query_jobs])
    query_results = _execute_query_jobs(adapter, query_jobs, max_concurrency, run_dir)
    for result in query_results:
        job = next(job for job in query_jobs if job["id"] == result["job_id"])
        write_json(job["output_target"], result)
        record_artifact_event(run_dir, "retrieval", "NotebookLMAdapter", job["output_target"], f"Query result for {job['id']}.", result.get("verdict", result.get("status", "PASS")))

    source_deep_dive_limit = _configured_source_deep_dive_limit(execution)
    source_deep_dive_lanes = _configured_source_deep_dive_lanes(execution)
    citation_sweep_jobs = []
    source_deep_dive_candidates = build_source_deep_dive_candidates(query_results, sources, source_deep_dive_limit)
    if not source_deep_dive_candidates and _source_deep_dive_enabled(source_deep_dive_limit):
        citation_sweep_job = build_citation_sweep_job(task_spec, run_dir, len(query_jobs) + 1)
        citation_sweep_jobs.append(citation_sweep_job)
        write_json(run_dir / "citation_sweep_jobs.json", citation_sweep_jobs)
        record_artifact_event(run_dir, "citation_sweep", "SourceDeepDivePlannerAgent", run_dir / "citation_sweep_jobs.json", "Citation sweep NotebookLM query jobs.")
        update_task_ledger(
            run_dir,
            citation_sweep_job["id"],
            {
                "owner_agent": "NotebookLMAdapter",
                "stage": "citation_sweep",
                "status": "PENDING",
                "inputs": ["notebooklm_sources.json"],
                "outputs": [citation_sweep_job.get("output_target")],
                "notebook_id": citation_sweep_job.get("notebook_id"),
                "query_type": citation_sweep_job.get("query_type"),
            },
        )
        _mark_phase(
            run_dir,
            "citation_sweep",
            "RUNNING",
            "Execute citation sweep before source-specific deep dive.",
            {"job_count": 1},
            active_tasks=[citation_sweep_job["id"]],
        )
        citation_sweep_results = _execute_query_jobs(adapter, citation_sweep_jobs, max_concurrency, run_dir)
        for result in citation_sweep_results:
            write_json(citation_sweep_job["output_target"], result)
            record_artifact_event(run_dir, "citation_sweep", "NotebookLMAdapter", citation_sweep_job["output_target"], f"Citation sweep result for {citation_sweep_job['id']}.", result.get("verdict", result.get("status", "PASS")))
        query_results.extend(citation_sweep_results)
        source_deep_dive_candidates = build_source_deep_dive_candidates(query_results, sources, source_deep_dive_limit)
        _mark_phase(run_dir, "citation_sweep", "PASS", "Plan source-specific deep dive jobs.", {"candidate_count": len(source_deep_dive_candidates)})
    else:
        write_json(run_dir / "citation_sweep_jobs.json", citation_sweep_jobs)
        record_artifact_event(run_dir, "citation_sweep", "SourceDeepDivePlannerAgent", run_dir / "citation_sweep_jobs.json", "Citation sweep skipped because first-stage citations were sufficient.")
    source_deep_dive_jobs = build_source_deep_dive_jobs(
        source_deep_dive_candidates,
        task_spec,
        run_dir,
        len(query_jobs) + len(citation_sweep_jobs),
        source_deep_dive_lanes,
    )
    write_json(run_dir / "source_deep_dive_candidates.json", source_deep_dive_candidates)
    record_artifact_event(run_dir, "source_deep_dive", "SourceDeepDivePlannerAgent", run_dir / "source_deep_dive_candidates.json", "Source-specific deep dive candidates.")
    write_json(run_dir / "source_deep_dive_jobs.json", source_deep_dive_jobs)
    record_artifact_event(run_dir, "source_deep_dive", "SourceDeepDivePlannerAgent", run_dir / "source_deep_dive_jobs.json", "Source-specific NotebookLM query jobs.")
    if source_deep_dive_jobs:
        for job in source_deep_dive_jobs:
            update_task_ledger(
                run_dir,
                job["id"],
                {
                    "owner_agent": "NotebookLMAdapter",
                    "stage": "source_deep_dive",
                    "status": "PENDING",
                    "inputs": [job.get("seed_trace_id"), job.get("source_title")],
                    "outputs": [job.get("output_target")],
                    "notebook_id": job.get("notebook_id"),
                    "query_type": job.get("query_type"),
                    "deep_dive_lane": job.get("deep_dive_lane"),
                    "source_ids": job.get("source_ids", []),
                },
            )
        _mark_phase(
            run_dir,
            "source_deep_dive",
            "RUNNING",
            "Execute bounded source-specific NotebookLM query jobs.",
            {"job_count": len(source_deep_dive_jobs), "limit": source_deep_dive_limit, "lanes": source_deep_dive_lanes},
            active_tasks=[job["id"] for job in source_deep_dive_jobs],
        )
        source_deep_dive_results = _execute_query_jobs(adapter, source_deep_dive_jobs, max_concurrency, run_dir)
        for result in source_deep_dive_results:
            job = next(job for job in source_deep_dive_jobs if job["id"] == result["job_id"])
            write_json(job["output_target"], result)
            record_artifact_event(run_dir, "source_deep_dive", "NotebookLMAdapter", job["output_target"], f"Source deep dive result for {job['id']}.", result.get("verdict", result.get("status", "PASS")))
        query_results.extend(source_deep_dive_results)
        _mark_phase(run_dir, "source_deep_dive", "PASS", "Review complete retrieval set.", {"result_count": len(query_results)})
    else:
        _mark_phase(
            run_dir,
            "source_deep_dive",
            "NOT_APPLICABLE",
            "No resolvable cited sources found for source-specific deep dive.",
            {"candidate_count": len(source_deep_dive_candidates), "limit": source_deep_dive_limit},
        )

    all_query_jobs = [*query_jobs, *citation_sweep_jobs, *source_deep_dive_jobs]
    retrieval_review = review_retrieval_completeness(all_query_jobs, query_results)
    retrieval_review = attach_audited_hashes(
        retrieval_review,
        [
            "query_jobs.json",
            "citation_sweep_jobs.json",
            "source_deep_dive_jobs.json",
            *[Path(job["output_target"]).relative_to(run_dir) for job in all_query_jobs],
        ],
        run_dir,
    )
    write_json(run_dir / "review_reports" / "retrieval_completeness_review.json", retrieval_review)
    record_artifact_event(run_dir, "retrieval", "RetrievalCompletenessGate", run_dir / "review_reports" / "retrieval_completeness_review.json", "Retrieval completeness review.", retrieval_review["verdict"])
    _mark_phase(run_dir, "retrieval", retrieval_review["verdict"], "Build material packages.", {"result_count": len(query_results)})

    material_packages = build_material_packages(query_results, dimensions)
    ensure_dir(run_dir / "material_packages")
    material_audits = []
    for package in material_packages:
        write_json(run_dir / "material_packages" / f"{package['package_id']}.json", package)
        record_artifact_event(run_dir, "material_pack", "MaterialPackAgent", run_dir / "material_packages" / f"{package['package_id']}.json", f"Material package {package['package_id']}.")
        material_audits.append(audit_material_package(package, dimensions))
    write_json(run_dir / "material_package_audit.json", material_audits)
    record_artifact_event(run_dir, "material_pack", "MaterialPackAudit", run_dir / "material_package_audit.json", "Raw material package audit list.")
    material_pack_audit_review = review_material_pack_audit(material_audits)
    material_pack_audit_review = attach_audited_hashes(material_pack_audit_review, ["material_package_audit.json"], run_dir)
    write_json(run_dir / "review_reports" / "material_pack_audit.json", material_pack_audit_review)
    record_artifact_event(run_dir, "material_pack", "MaterialPackAudit", run_dir / "review_reports" / "material_pack_audit.json", "Material package audit review.", material_pack_audit_review["verdict"])
    material_review = review_material_packages(material_audits)
    material_review = attach_audited_hashes(material_review, ["material_package_audit.json"], run_dir)
    write_json(run_dir / "review_reports" / "material_coverage_review.json", material_review)
    record_artifact_event(run_dir, "material_pack", "MaterialCoverageReviewerAgent", run_dir / "review_reports" / "material_coverage_review.json", "Material coverage review.", material_review["verdict"])
    evidence_review = review_evidence_use(query_results, material_packages)
    evidence_review = attach_audited_hashes(
        evidence_review,
        [*[Path(job["output_target"]).relative_to(run_dir) for job in query_jobs], *[Path("material_packages") / f"{package['package_id']}.json" for package in material_packages]],
        run_dir,
    )
    write_json(run_dir / "review_reports" / "evidence_use_review.json", evidence_review)
    record_artifact_event(run_dir, "material_pack", "EvidenceUseReviewerAgent", run_dir / "review_reports" / "evidence_use_review.json", "Evidence/source trace review.", evidence_review["verdict"])
    _mark_phase(run_dir, "material_pack", material_review["verdict"], "Build report matrices.", {"package_count": len(material_packages)})

    matrices = build_all_matrices(material_packages)
    for name, payload in matrices.items():
        write_json(run_dir / f"{name}.json", payload)
        record_artifact_event(run_dir, "matrix_building", "MatrixBuilderAgent", run_dir / f"{name}.json", f"Matrix artifact {name}.")
    _mark_phase(run_dir, "matrix_building", "PASS", "Build report plan and section plan.", {"matrix_count": len(matrices)})

    compression_result: dict[str, Any] | None = None
    compression_config = execution.get("material_compression", {})
    if compression_config.get("enabled", agent_runtime.profile == "api_assisted"):
        _mark_phase(
            run_dir,
            "material_compression",
            "RUNNING",
            "Compress material packages into section slices.",
            {"profile": compression_config.get("profile", "deepseek_chunked" if agent_runtime.profile == "api_assisted" else "local_fallback")},
        )
        compression_result = compress_materials(
            material_packages,
            matrices,
            section_contracts,
            task_spec,
            agent_runtime,
            run_dir,
            compression_config,
        )
        compression_manifest = compression_result["manifest"]
        record_artifact_event(run_dir, "material_compression", "MaterialCompressionAgent", run_dir / "compression" / "compression_jobs.json", "Material compression jobs.")
        record_artifact_event(run_dir, "material_compression", "MaterialCompressionAgent", run_dir / "compression" / "report_narrative_spine.json", "Report narrative spine.")
        compression_verdict = "PASS" if compression_manifest.get("final_status") == "PASS" else "WARN"
        record_artifact_event(run_dir, "material_compression", "MaterialCompressionAgent", run_dir / "compression" / "section_slices.json", "Section-specific material slices.", compression_verdict)
        record_artifact_event(run_dir, "material_compression", "MaterialCompressionAgent", run_dir / "compression" / "compression_manifest.json", "Material compression manifest.", compression_verdict)
        record_artifact_event(run_dir, "material_compression", "MaterialCompressionAgent", run_dir / "compression" / "compression_errors.json", "Material compression errors.", "WARN" if compression_result.get("errors") else "PASS")
        _mark_phase(
            run_dir,
            "material_compression",
            compression_verdict,
            "Build report plan and section plan.",
            {"chunk_count": len(compression_manifest.get("chunks", [])), "error_count": len(compression_result.get("errors", [])), "final_status": compression_manifest.get("final_status")},
        )

    report_plan = build_report_plan(task_spec, matrices, section_contracts)
    write_text(run_dir / "POLICY_REPORT_PLAN.md", report_plan)
    record_artifact_event(run_dir, "report_plan", "SectionContractAgent", run_dir / "POLICY_REPORT_PLAN.md", "Report plan.")
    section_plan = build_section_plan(section_contracts, matrices)
    write_json(run_dir / "section_plan.json", section_plan)
    record_artifact_event(run_dir, "report_plan", "SectionContractAgent", run_dir / "section_plan.json", "Section plan.")
    _mark_phase(run_dir, "report_plan", "PASS", "Compose section drafts.", {})

    ensure_dir(run_dir / "section_drafts")
    claims = matrices["policy_claim_material_matrix"]
    section_drafts: dict[str, str] = {}
    section_filenames = {
        "hotspot": "01_hotspot.md",
        "theme": "02_theme.md",
        "comparison": "03_comparison.md",
        "impact": "04_impact.md",
        "insight": "05_insight.md",
    }
    for section_id, section_data in section_plan.items():
        task_id = f"compose_{section_id}"
        output_path = run_dir / "section_drafts" / section_filenames.get(section_id, f"{section_id}.md")
        update_task_ledger(
            run_dir,
            task_id,
            {
                "owner_agent": "SectionComposerAgent",
                "stage": "section_drafts",
                "status": "RUNNING",
                "inputs": ["section_plan.json", "material_packages/", "policy_claim_material_matrix.json"],
                "outputs": [str(output_path)],
                "section_id": section_id,
                "started_at": utc_timestamp(),
            },
        )
        if agent_runtime.driver_for("SectionComposerAgent") == "api":
            section_prompt = build_section_prompt(
                section_id,
                section_data["contract"],
                material_packages,
                claims,
                matrices,
                compression_result["section_slices"] if compression_result else None,
            )
            write_text(run_dir / "section_drafts" / f"{section_id}.prompt.md", section_prompt)
            record_artifact_event(
                run_dir,
                "section_drafts",
                "SectionComposerAgent",
                run_dir / "section_drafts" / f"{section_id}.prompt.md",
                f"API prompt for section draft {section_id}.",
            )
            draft = agent_runtime.complete_text("SectionComposerAgent", section_prompt)
        else:
            draft = compose_section(section_id, section_data["contract"], material_packages, claims, matrices)
        section_drafts[section_id] = draft
        write_text(output_path, draft)
        update_task_ledger(run_dir, task_id, {"status": "PASS", "finished_at": utc_timestamp()})
        record_artifact_event(run_dir, "section_drafts", "SectionComposerAgent", output_path, f"Section draft {section_id}.")
    section_contract_review = review_section_contracts(section_drafts, section_contracts)
    section_contract_review = attach_audited_hashes(
        section_contract_review,
        [Path("section_drafts") / filename for filename in section_filenames.values()],
        run_dir,
    )
    write_json(run_dir / "review_reports" / "section_contract_review.json", section_contract_review)
    record_artifact_event(run_dir, "section_drafts", "SectionContractReviewerAgent", run_dir / "review_reports" / "section_contract_review.json", "Section contract review.", section_contract_review["verdict"])
    claim_review = review_claim_scope(section_drafts, claims)
    claim_review = attach_audited_hashes(
        claim_review,
        ["policy_claim_material_matrix.json", *[Path("section_drafts") / filename for filename in section_filenames.values()]],
        run_dir,
    )
    write_json(run_dir / "review_reports" / "claim_scope_review.json", claim_review)
    record_artifact_event(run_dir, "section_drafts", "ClaimAuditAgent", run_dir / "review_reports" / "claim_scope_review.json", "Claim scope review.", claim_review["verdict"])
    _mark_phase(run_dir, "section_drafts", _max_verdict([section_contract_review, claim_review]), "Assemble and review final report.", {"section_count": len(section_drafts)})

    abstract_text = None
    if agent_runtime.driver_for("AbstractComposerAgent") == "api":
        _mark_phase(run_dir, "abstract", "RUNNING", "Generate final abstract from completed section drafts.", {})
        abstract_prompt = build_abstract_prompt(task_spec, section_drafts)
        write_text(run_dir / "abstract.prompt.md", abstract_prompt)
        record_artifact_event(run_dir, "abstract", "AbstractComposerAgent", run_dir / "abstract.prompt.md", "API prompt for final abstract.")
        abstract_text = agent_runtime.complete_text("AbstractComposerAgent", abstract_prompt)
        write_text(run_dir / "abstract.md", abstract_text)
        record_artifact_event(run_dir, "abstract", "AbstractComposerAgent", run_dir / "abstract.md", "Generated final abstract.")
        _mark_phase(run_dir, "abstract", "PASS", "Review final report.", {"abstract_bytes": len(abstract_text.encode("utf-8"))})

    review_reports = [plan_review, notebooklm_preflight, retrieval_review, material_pack_audit_review, material_review, evidence_review, section_contract_review, claim_review]
    final_report = assemble_report(task_spec, section_drafts, review_reports, material_packages, matrices, abstract_text)
    report_quality_review = review_report_quality(final_report, review_reports)
    report_quality_review = attach_audited_hashes(report_quality_review, [*[Path("section_drafts") / filename for filename in section_filenames.values()]], run_dir)
    review_reports.append(report_quality_review)
    write_json(run_dir / "review_reports" / "report_quality_review.json", report_quality_review)
    record_artifact_event(run_dir, "review_gates", "ReportQualityReviewerAgent", run_dir / "review_reports" / "report_quality_review.json", "Report quality review.", report_quality_review["verdict"])
    kill_review = review_kill_argument(final_report)
    kill_review = attach_audited_hashes(kill_review, [*[Path("section_drafts") / filename for filename in section_filenames.values()]], run_dir)
    review_reports.append(kill_review)
    write_json(run_dir / "review_reports" / "kill_argument_review.json", kill_review)
    record_artifact_event(run_dir, "review_gates", "KillArgumentAgent", run_dir / "review_reports" / "kill_argument_review.json", "Kill argument review.", kill_review["verdict"])
    drift_review = review_drift(review_reports, run_dir)
    review_reports.append(drift_review)
    write_json(run_dir / "review_reports" / "drift_review.json", drift_review)
    record_artifact_event(run_dir, "review_gates", "DriftReviewerAgent", run_dir / "review_reports" / "drift_review.json", "Reviewed input drift review.", drift_review["verdict"])
    _mark_phase(run_dir, "review_gates", _max_verdict(review_reports), "Write final report and manifest.", {"review_count": len(review_reports)})
    final_report = assemble_report(task_spec, section_drafts, review_reports, material_packages, matrices, abstract_text)
    write_text(run_dir / "final_report.md", final_report)
    record_artifact_event(run_dir, "final_assembly", "ReportAssembler", run_dir / "final_report.md", "Final report.", _max_verdict(review_reports))
    _mark_phase(run_dir, "final_assembly", _max_verdict(review_reports), "Collect manifest.", {"path": "final_report.md"})

    artifacts = collect_artifacts(run_dir)
    manifest = build_manifest(run_dir, artifacts)
    write_text(run_dir / "MANIFEST.md", manifest)
    record_artifact_event(run_dir, "manifest", "IntegrationAgent", run_dir / "MANIFEST.md", "Final artifact manifest with hashes.")
    final_status = _max_verdict(review_reports)
    _mark_phase(run_dir, "manifest", final_status, "Run complete; inspect review_reports for non-green gates." if final_status != "PASS" else "Run complete.", {"path": "MANIFEST.md"})
    if execution.get("overwrite_latest", True):
        latest_dir = output_root / "latest"
        if latest_dir.exists() or latest_dir.is_symlink():
            if latest_dir.is_symlink() or latest_dir.is_file():
                latest_dir.unlink()
            else:
                shutil.rmtree(latest_dir)
        shutil.copytree(run_dir, latest_dir)

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "final_report": str(run_dir / "final_report.md"),
        "agent_runtime_profile": agent_runtime.profile,
        "verdicts": {
            report["reviewer"]: report["verdict"]
            for report in review_reports
        },
    }


def _configured_concurrency(execution: dict[str, Any]) -> int:
    try:
        configured = int(execution.get("max_concurrency", 1))
    except (TypeError, ValueError):
        return 1
    return max(1, configured)


def _configured_source_deep_dive_limit(execution: dict[str, Any]) -> int | None:
    raw = execution.get("source_deep_dive_limit", 3)
    if isinstance(raw, str) and raw.strip().lower() in {"all", "unlimited", "none"}:
        return None
    try:
        configured = int(raw)
    except (TypeError, ValueError):
        return 3
    return max(0, configured)


def _source_deep_dive_enabled(limit: int | None) -> bool:
    return limit is None or limit > 0


def _configured_source_deep_dive_lanes(execution: dict[str, Any]) -> list[str]:
    configured = execution.get("source_deep_dive_lanes")
    if not isinstance(configured, list):
        return DEFAULT_SOURCE_DEEP_DIVE_LANES
    lanes = [str(lane) for lane in configured if lane]
    return lanes or DEFAULT_SOURCE_DEEP_DIVE_LANES


def _execute_query_jobs(adapter: NotebookLMAdapter, query_jobs: list[dict[str, Any]], max_concurrency: int, run_dir: Path) -> list[dict[str, Any]]:
    if max_concurrency <= 1 or len(query_jobs) <= 1:
        results = []
        for job in query_jobs:
            results.append(_ask_with_timing(adapter, job, max_concurrency, run_dir))
        return results

    results_by_id: dict[str, dict[str, Any]] = {}
    with futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        future_by_job_id = {
            executor.submit(_ask_with_timing, adapter, job, max_concurrency, run_dir): job["id"]
            for job in query_jobs
        }
        for future in futures.as_completed(future_by_job_id):
            job_id = future_by_job_id[future]
            try:
                results_by_id[job_id] = future.result()
            except Exception as exc:  # pragma: no cover - defensive guard for subprocess/runtime failures
                results_by_id[job_id] = {
                    "status": "ERROR",
                    "verdict": "ERROR",
                    "reason_code": "query_execution_exception",
                    "job_id": job_id,
                    "summary": str(exc),
                    "parsed_fields": {},
                    "structured_answer": {},
                    "runner_concurrency": max_concurrency,
                    "runner_finished_at": utc_timestamp(),
                }
            update_task_ledger(
                run_dir,
                job_id,
                {
                    "status": results_by_id[job_id].get("verdict", results_by_id[job_id].get("status", "ERROR")),
                    "reason_code": results_by_id[job_id].get("reason_code", ""),
                    "finished_at": utc_timestamp(),
                },
            )
    return [results_by_id[job["id"]] for job in query_jobs]


def _ask_with_timing(adapter: NotebookLMAdapter, job: dict[str, Any], max_concurrency: int, run_dir: Path) -> dict[str, Any]:
    started_at = utc_timestamp()
    started = time.perf_counter()
    update_task_ledger(run_dir, job["id"], {"status": "RUNNING", "started_at": started_at})
    result = adapter.ask(job)
    result.update(
        {
            "runner_started_at": started_at,
            "runner_finished_at": utc_timestamp(),
            "runner_duration_sec": round(time.perf_counter() - started, 3),
            "runner_concurrency": max_concurrency,
        }
    )
    update_task_ledger(
        run_dir,
        job["id"],
        {
            "status": result.get("verdict", result.get("status", "PASS")),
            "reason_code": result.get("reason_code", ""),
            "finished_at": result["runner_finished_at"],
            "duration_sec": result["runner_duration_sec"],
        },
    )
    return result


def _mark_phase(run_dir: Path, phase: str, status: str, next_action: str, details: dict[str, Any] | None = None, active_tasks: list[str] | None = None) -> None:
    update_workflow_state(run_dir, phase, status, details)
    write_run_status_md(
        run_dir,
        {
            "stage": phase,
            "status": status,
            "next_action": next_action,
            "details": details or {},
            "active_tasks": active_tasks or [],
        },
    )
    append_progress_log(run_dir, {"event": "phase", "stage": phase, "status": status, "next_action": next_action, "details": details or {}})


def _max_verdict(reports: list[dict[str, Any]]) -> str:
    order = {"ERROR": 5, "FAIL": 4, "BLOCKED": 3, "WARN": 2, "PASS": 1, "NOT_APPLICABLE": 0}
    verdict = "PASS"
    for report in reports:
        candidate = str(report.get("verdict", "PASS"))
        if order.get(candidate, 5) > order.get(verdict, 1):
            verdict = candidate
    return verdict


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the policy writing agent MVP.")
    parser.add_argument("--task", default="config/report_task.yaml", help="Task config path.")
    parser.add_argument("--run-id", default=None, help="Optional run id.")
    args = parser.parse_args()
    result = run_workflow(args.task, args.run_id)
    write_json(Path(result["run_dir"]) / "run_summary.json", result)
    print(result)


if __name__ == "__main__":
    main()
