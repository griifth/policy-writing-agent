from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import shutil
import time
from pathlib import Path
from typing import Any

from agent_runtime import build_agent_runtime
from io_utils import ensure_dir, load_yaml, read_text, timestamp_run_id, update_workflow_state, utc_timestamp, write_json, write_text
from manifest import build_manifest, collect_artifacts
from material_pack_builder import audit_material_package, build_material_packages
from matrix_builder import build_all_matrices
from notebooklm_adapter import NotebookLMAdapter
from query_planner import build_query_jobs
from report_assembler import assemble_report
from review_gates import review_claim_scope, review_kill_argument, review_material_pack_audit, review_material_packages, review_plan, review_retrieval_completeness
from section_composer import compose_section
from section_planner import build_report_plan, build_section_plan


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

    write_json(run_dir / "agent_runtime.json", agent_runtime.manifest())
    runtime_issues = agent_runtime.validate()
    write_json(run_dir / "agent_runtime_validation.json", runtime_issues)
    if runtime_issues:
        update_workflow_state(
            run_dir,
            "preflight",
            "ERROR",
            {"config": str(config_path), "agent_runtime_issues": runtime_issues},
        )
        raise RuntimeError(f"Agent runtime configuration is invalid: {runtime_issues}")
    update_workflow_state(
        run_dir,
        "preflight",
        "PASS",
        {"config": str(config_path), "agent_runtime_mode": agent_runtime.mode},
    )
    dimensions = load_yaml(project_dir / "config" / "dimension_registry.yaml")
    section_contracts = load_yaml(project_dir / "config" / "section_contracts.yaml")

    write_json(run_dir / "task_spec.json", task_spec)
    update_workflow_state(run_dir, "task_spec", "PASS", {"topic": task_spec["topic"]})

    query_jobs = build_query_jobs(task_spec, dimensions, section_contracts, run_dir)
    write_json(run_dir / "query_jobs.json", query_jobs)
    plan_review = review_plan(query_jobs, task_spec.get("sections", []))
    ensure_dir(run_dir / "review_reports")
    write_json(run_dir / "review_reports" / "plan_review.json", plan_review)
    update_workflow_state(run_dir, "query_planning", plan_review["verdict"], {"job_count": len(query_jobs)})

    adapter = NotebookLMAdapter(
        mode=execution.get("mode", "mock"),
        cli_path=execution.get("notebooklm_cli_path"),
    )
    auth_status = adapter.check_auth()
    write_json(run_dir / "notebooklm_auth.json", auth_status)
    sources = adapter.list_sources(task_spec["notebook_id"])
    write_json(run_dir / "notebooklm_sources.json", sources)

    ensure_dir(run_dir / "query_results")
    max_concurrency = _configured_concurrency(execution)
    query_results = _execute_query_jobs(adapter, query_jobs, max_concurrency)
    for result in query_results:
        job = next(job for job in query_jobs if job["id"] == result["job_id"])
        write_json(job["output_target"], result)
    retrieval_review = review_retrieval_completeness(query_jobs, query_results)
    write_json(run_dir / "review_reports" / "retrieval_completeness_review.json", retrieval_review)
    update_workflow_state(run_dir, "retrieval", retrieval_review["verdict"], {"result_count": len(query_results)})

    material_packages = build_material_packages(query_results, dimensions)
    ensure_dir(run_dir / "material_packages")
    material_audits = []
    for package in material_packages:
        write_json(run_dir / "material_packages" / f"{package['package_id']}.json", package)
        material_audits.append(audit_material_package(package, dimensions))
    write_json(run_dir / "material_package_audit.json", material_audits)
    material_pack_audit_review = review_material_pack_audit(material_audits)
    write_json(run_dir / "review_reports" / "material_pack_audit.json", material_pack_audit_review)
    material_review = review_material_packages(material_audits)
    write_json(run_dir / "review_reports" / "material_coverage_review.json", material_review)
    update_workflow_state(run_dir, "material_pack", material_review["verdict"], {"package_count": len(material_packages)})

    matrices = build_all_matrices(material_packages)
    for name, payload in matrices.items():
        write_json(run_dir / f"{name}.json", payload)
    update_workflow_state(run_dir, "matrix_building", "PASS", {"matrix_count": len(matrices)})

    report_plan = _build_report_plan(agent_runtime, task_spec, matrices, section_contracts)
    write_text(run_dir / "POLICY_REPORT_PLAN.md", report_plan)
    section_plan = build_section_plan(section_contracts, matrices)
    write_json(run_dir / "section_plan.json", section_plan)
    update_workflow_state(run_dir, "report_plan", "PASS", {})

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
        draft = _compose_section(
            agent_runtime,
            section_id,
            section_data["contract"],
            material_packages,
            claims,
            matrices,
        )
        section_drafts[section_id] = draft
        write_text(run_dir / "section_drafts" / section_filenames.get(section_id, f"{section_id}.md"), draft)
    claim_review = review_claim_scope(section_drafts, claims)
    write_json(run_dir / "review_reports" / "claim_scope_review.json", claim_review)
    update_workflow_state(run_dir, "section_drafts", claim_review["verdict"], {"section_count": len(section_drafts)})

    review_reports = [plan_review, retrieval_review, material_pack_audit_review, material_review, claim_review]
    final_report = assemble_report(task_spec, section_drafts, review_reports, material_packages, matrices)
    kill_review = review_kill_argument(final_report)
    review_reports.append(kill_review)
    write_json(run_dir / "review_reports" / "kill_argument_review.json", kill_review)
    update_workflow_state(run_dir, "review_gates", kill_review["verdict"], {"review_count": len(review_reports)})
    final_report = assemble_report(task_spec, section_drafts, review_reports, material_packages, matrices)
    write_text(run_dir / "final_report.md", final_report)
    update_workflow_state(run_dir, "final_assembly", kill_review["verdict"], {"path": "final_report.md"})

    artifacts = collect_artifacts(run_dir)
    manifest = build_manifest(run_dir, artifacts)
    write_text(run_dir / "MANIFEST.md", manifest)
    update_workflow_state(run_dir, "manifest", "PASS", {"path": "MANIFEST.md"})
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
        "agent_runtime_mode": agent_runtime.mode,
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


def _build_report_plan(
    agent_runtime: Any,
    task_spec: dict[str, Any],
    matrices: dict[str, Any],
    section_contracts: dict[str, Any],
) -> str:
    local_plan = build_report_plan(task_spec, matrices, section_contracts)
    if agent_runtime.driver_for("SectionContractAgent") != "llm_api":
        return local_plan
    prompt = (
        "你是政策报告写作流程中的 SectionContractAgent。\n"
        "只基于输入的 task_spec、matrices、section_contracts 和 local_plan，生成一份 Markdown 格式的 POLICY_REPORT_PLAN。\n"
        "不要引入材料外事实；如果材料不足，用 MATERIAL_NEEDED 标记。\n\n"
        f"task_spec:\n{_json_block(task_spec)}\n\n"
        f"matrices:\n{_json_block(matrices)}\n\n"
        f"section_contracts:\n{_json_block(section_contracts)}\n\n"
        f"local_plan:\n{local_plan}\n"
    )
    return agent_runtime.complete_text("SectionContractAgent", prompt)


def _compose_section(
    agent_runtime: Any,
    section_id: str,
    contract: dict[str, Any],
    material_packages: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    matrices: dict[str, Any],
) -> str:
    local_draft = compose_section(section_id, contract, material_packages, claims, matrices)
    if agent_runtime.driver_for("SectionComposerAgent") != "llm_api":
        return local_draft
    prompt = (
        "你是政策报告写作流程中的 SectionComposerAgent。\n"
        "请只基于 material_packages、claims、matrices 和 section contract 写本章节 Markdown。\n"
        "不得引入材料外事实；不确定或缺失处用 MATERIAL_NEEDED 标记。\n"
        "保留章节标题，并在末尾保留“本节契约检查”。\n\n"
        f"section_id: {section_id}\n\n"
        f"contract:\n{_json_block(contract)}\n\n"
        f"material_packages:\n{_json_block(material_packages)}\n\n"
        f"claims:\n{_json_block(claims)}\n\n"
        f"matrices:\n{_json_block(matrices)}\n\n"
        f"local_draft_seed:\n{local_draft}\n"
    )
    return agent_runtime.complete_text("SectionComposerAgent", prompt)


def _json_block(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _execute_query_jobs(adapter: NotebookLMAdapter, query_jobs: list[dict[str, Any]], max_concurrency: int) -> list[dict[str, Any]]:
    if max_concurrency <= 1 or len(query_jobs) <= 1:
        return [_ask_with_timing(adapter, job, max_concurrency) for job in query_jobs]

    results_by_id: dict[str, dict[str, Any]] = {}
    with futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        future_by_job_id = {
            executor.submit(_ask_with_timing, adapter, job, max_concurrency): job["id"]
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
    return [results_by_id[job["id"]] for job in query_jobs]


def _ask_with_timing(adapter: NotebookLMAdapter, job: dict[str, Any], max_concurrency: int) -> dict[str, Any]:
    started_at = utc_timestamp()
    started = time.perf_counter()
    result = adapter.ask(job)
    result.update(
        {
            "runner_started_at": started_at,
            "runner_finished_at": utc_timestamp(),
            "runner_duration_sec": round(time.perf_counter() - started, 3),
            "runner_concurrency": max_concurrency,
        }
    )
    return result


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
