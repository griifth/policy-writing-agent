from __future__ import annotations

from pathlib import Path
from typing import Any

from io_utils import utc_timestamp


def build_manifest(run_dir: str | Path, artifacts: list[dict[str, Any]]) -> str:
    run_dir = Path(run_dir)
    lines = [
        "# MANIFEST",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Generated at: {utc_timestamp()}",
        "",
        "| Artifact | Type | Producer | Path |",
        "|---|---|---|---|",
    ]
    for artifact in artifacts:
        lines.append(f"| {artifact['name']} | {artifact['type']} | {artifact['producer']} | `{artifact['path']}` |")
    lines.append("")
    return "\n".join(lines)


def collect_artifacts(run_dir: str | Path) -> list[dict[str, Any]]:
    run_dir = Path(run_dir)
    artifacts: list[dict[str, Any]] = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file():
            artifacts.append(
                {
                    "name": path.name,
                    "type": path.suffix.lstrip(".") or "file",
                    "producer": _producer_for(path.relative_to(run_dir)),
                    "path": str(path.relative_to(run_dir)),
                }
            )
    return artifacts


def _producer_for(path: Path) -> str:
    parts = path.parts
    name = path.name
    if "query_results" in parts:
        return "NotebookLMAdapter"
    if "material_packages" in parts or name == "material_package_audit.json":
        return "MaterialPackAgent"
    if "section_drafts" in parts:
        return "SectionComposerAgent"
    if "review_reports" in parts:
        return "ReviewAgentGroup"
    if name in {"query_jobs.json"}:
        return "QueryPlannerAgent"
    if name in {"POLICY_REPORT_PLAN.md", "section_plan.json"}:
        return "SectionContractAgent"
    if "matrix" in name or name in {"impact_table.json", "insight_table.json"}:
        return "MatrixBuilderAgent"
    if name == "final_report.md":
        return "ReportAssembler"
    if name == "workflow_state.json":
        return "IntegrationAgent"
    if name in {"agent_runtime.json", "agent_runtime_validation.json"}:
        return "IntegrationAgent"
    return "IntegrationAgent"
