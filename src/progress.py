from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from io_utils import load_json, utc_timestamp, write_json, write_text


_LEDGER_LOCK = threading.Lock()


def write_policy_report_contract(run_dir: str | Path, task_spec: dict[str, Any]) -> None:
    run_dir = Path(run_dir)
    lines = [
        "# POLICY_REPORT_CONTRACT",
        "",
        f"- Topic: {task_spec.get('topic')}",
        f"- Notebook ID: {task_spec.get('notebook_id')}",
        f"- Knowledge Mode: {task_spec.get('knowledge_mode', 'notebooklm')}",
        f"- Audience: {task_spec.get('audience', '')}",
        f"- Style: {task_spec.get('style', '')}",
        f"- Language: {task_spec.get('language', '')}",
        f"- Assurance: {task_spec.get('assurance', 'draft')}",
        f"- Traceability Owner: {task_spec.get('traceability_owner', 'notebooklm')}",
        "",
        "## Capability Boundary",
        "",
        "- Only NotebookLM CLI may access external knowledge.",
        "- Do not edit or rewrite the NotebookLM skill.",
        "- Writing agents may use only material packages, matrices, section contracts, and review reports generated in this run.",
        "- If api_assisted is enabled, external LLM APIs may write from run artifacts but may not access NotebookLM or external knowledge directly.",
        "- Missing material must remain visible as MATERIAL_NEEDED or follow-up queries.",
        "",
        "## Drift Guard",
        "",
        "- Do not expand into generic agent infrastructure.",
        "- Do not add browser, web-search, or ARIS external reviewer calls to the report generation path.",
        "- Do not let API-assisted writing agents bypass NotebookLM-derived material packages or review artifacts.",
        "- Do not import ARIS paper/LaTeX submission workflows; adapt only bounded patterns that serve policy task or hotspot reports.",
        "- Keep every implementation change tied to the report-writing goal.",
        "",
    ]
    write_text(run_dir / "POLICY_REPORT_CONTRACT.md", "\n".join(lines))


def write_run_status_md(run_dir: str | Path, status: dict[str, Any]) -> None:
    run_dir = Path(run_dir)
    active_tasks = status.get("active_tasks", [])
    lines = [
        "# RUN_STATUS",
        "",
        f"- Last updated: {utc_timestamp()}",
        f"- Stage: {status.get('stage', 'unknown')}",
        f"- Status: {status.get('status', 'unknown')}",
        f"- Main agent next action: {status.get('next_action', '')}",
        f"- Contract: `POLICY_REPORT_CONTRACT.md`",
        f"- Task ledger: `TASK_LEDGER.json`",
        f"- Progress log: `progress.jsonl`",
        "",
        "## Active Tasks",
        "",
    ]
    if active_tasks:
        lines.extend(f"- {task}" for task in active_tasks)
    else:
        lines.append("- None")
    if status.get("details"):
        lines.extend(["", "## Details", "", "```json", json.dumps(status["details"], ensure_ascii=False, indent=2), "```"])
    lines.append("")
    write_text(run_dir / "RUN_STATUS.md", "\n".join(lines))


def append_progress_log(run_dir: str | Path, event: dict[str, Any]) -> None:
    path = Path(run_dir) / "progress.jsonl"
    payload = {"generated_at": utc_timestamp(), **event}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def update_task_ledger(run_dir: str | Path, task_id: str, patch: dict[str, Any]) -> None:
    path = Path(run_dir) / "TASK_LEDGER.json"
    with _LEDGER_LOCK:
        if path.exists() and path.stat().st_size > 0:
            ledger = load_json(path)
        else:
            ledger = {"tasks": {}}
        tasks = ledger.setdefault("tasks", {})
        task = tasks.setdefault(task_id, {"task_id": task_id, "created_at": utc_timestamp()})
        task.update(patch)
        task["updated_at"] = utc_timestamp()
        write_json(path, ledger)


def record_artifact_event(
    run_dir: str | Path,
    stage: str,
    producer: str,
    path: str | Path,
    description: str,
    status: str = "PASS",
) -> None:
    relative = _relative_to_run(run_dir, path)
    append_progress_log(
        run_dir,
        {
            "event": "artifact",
            "stage": stage,
            "producer": producer,
            "path": relative,
            "description": description,
            "status": status,
        },
    )


def _relative_to_run(run_dir: str | Path, path: str | Path) -> str:
    run_dir = Path(run_dir)
    target = Path(path)
    try:
        return str(target.relative_to(run_dir))
    except ValueError:
        return str(target)
