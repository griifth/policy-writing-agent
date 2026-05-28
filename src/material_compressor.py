from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from agent_runtime import AgentRuntime
from io_utils import ensure_dir, utc_timestamp, write_json, write_text
from text_cleaning import strip_citation_markers


SECTION_IDS = ["hotspot", "theme", "comparison", "impact", "insight"]
MAX_COMPRESSED_POINT_CHARS = 900
MAX_COMPRESSED_CAUTION_CHARS = 260
MAX_FALLBACK_POINT_CHARS = 700
MAX_COMPRESSION_STRING_CHARS = 900
MAX_COMPRESSION_LIST_ITEMS = 24
TRACE_HEAVY_KEYS = {
    "raw_answer",
    "raw_response",
    "raw_stdout",
    "raw_stderr",
    "structured_answer",
    "parsed_fields",
    "citations",
    "citation_refs",
    "evidence_trace",
    "source_refs",
}
CLAIM_ROW_KEYS = [
    "claim_id",
    "claim",
    "claim_text",
    "claim_type",
    "support_level",
    "allowed_sections",
    "material_package_ids",
    "caution",
    "caution_note",
    "missing_fields",
]
TRANSIENT_ERROR_MARKERS = (
    "Timeout",
    "timed out",
    "URLError",
    "IncompleteRead",
    "BrokenPipe",
    "Connection reset",
    "ConnectionResetError",
    "HTTP 429",
    "HTTP 500",
    "HTTP 502",
    "HTTP 503",
    "HTTP 504",
)
NON_RETRYABLE_ERROR_MARKERS = ("HTTP 400", "HTTP 401", "HTTP 403")


def build_narrative_spine(task_spec: dict[str, Any], section_contracts: dict[str, Any], matrices: dict[str, Any]) -> dict[str, Any]:
    topic = task_spec.get("topic", "政策热点研判")
    rows = matrices.get("hotspot_theme_matrix", [])
    main_theme = rows[0].get("main_theme") if rows and isinstance(rows[0], dict) else ""
    thesis = f"围绕“{topic}”，报告先识别政策热点，再解释主题归属和政策路径差异，最后研判影响并提出启发建议。"
    if main_theme:
        thesis = f"围绕“{topic}”，报告以“{main_theme}”为主线，先识别热点，再比较政策路径，最后研判影响并提出启发建议。"
    return {
        "topic": topic,
        "central_thesis": thesis,
        "throughline": [
            "先说明热点为什么成立。",
            "再把热点放入主题体系。",
            "然后比较不同政策路径。",
            "接着分析影响、风险和不确定性。",
            "最后提出研究、治理、实践和监测启发。",
        ],
        "section_roles": {
            section_id: str(contract.get("function", ""))
            for section_id, contract in section_contracts.items()
        },
        "handoffs": {
            "hotspot": {"previous": "", "next": "由热点成立转向其政策主题归属。"},
            "theme": {"previous": "承接热点的政策问题，解释其主题归属和交叉张力。", "next": "由主题张力转向不同政策路径比较。"},
            "comparison": {"previous": "承接主题张力，比较不同政策主体和治理路径。", "next": "由政策路径差异转向影响研判。"},
            "impact": {"previous": "承接政策路径差异，分析其对治理、学校、教师和学生的影响。", "next": "由影响和风险转向行动启发。"},
            "insight": {"previous": "承接影响研判和风险缺口，提出研究、治理、实践和监测启发。", "next": ""},
        },
        "continuity_rules": [
            "每节只承担本节角色，不重复上一节的大段内容。",
            "使用同一组核心术语，必要时用同义改写但不改变概念含义。",
            "结尾用一两句自然引出下一节，不新增材料包外事实。",
        ],
    }


def compress_materials(
    material_packages: list[dict[str, Any]],
    matrices: dict[str, Any],
    section_contracts: dict[str, Any],
    task_spec: dict[str, Any],
    agent_runtime: AgentRuntime,
    run_dir: Path,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or {}
    compression_dir = ensure_dir(run_dir / "compression")
    chunks_dir = ensure_dir(compression_dir / "chunks")
    narrative_spine = build_narrative_spine(task_spec, section_contracts, matrices)
    write_json(compression_dir / "report_narrative_spine.json", narrative_spine)

    jobs = _build_compression_jobs(material_packages, matrices)
    write_json(compression_dir / "compression_jobs.json", jobs)

    enabled = bool(config.get("enabled", agent_runtime.profile == "api_assisted"))
    use_api = enabled and agent_runtime.driver_for("MaterialCompressionAgent") == "api"
    max_attempts = int(config.get("max_attempts", 3))
    timeout_note = int(config.get("timeout_seconds", 240))
    chunk_results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for job in jobs:
        result = _run_compression_job(job, agent_runtime, use_api, max_attempts, timeout_note, chunks_dir)
        chunk_results.append(result)
        errors.extend(result.get("errors", []))

    section_slices = _merge_section_slices(material_packages, matrices, chunk_results, narrative_spine)
    manifest = {
        "compression_profile": "deepseek_chunked" if use_api else "local_fallback",
        "provider": "deepseek" if use_api else "local",
        "model": agent_runtime.agent_config("MaterialCompressionAgent").get("model") if use_api else "",
        "generated_at": utc_timestamp(),
        "total_input_bytes": sum(job.get("input_bytes", 0) for job in jobs),
        "chunks": [_chunk_manifest_item(result) for result in chunk_results],
        "final_status": _compression_status(chunk_results, errors),
    }

    write_json(compression_dir / "section_slices.json", section_slices)
    write_json(compression_dir / "compression_manifest.json", manifest)
    write_json(compression_dir / "compression_errors.json", errors)
    return {
        "section_slices": section_slices,
        "narrative_spine": narrative_spine,
        "manifest": manifest,
        "errors": errors,
    }


def _build_compression_jobs(material_packages: list[dict[str, Any]], matrices: dict[str, Any]) -> list[dict[str, Any]]:
    package_chunks = [
        {
            "chunk_id": "overview_policy",
            "fields": ["package_id", "hotspot", "main_theme", "cross_themes", "section_targets", "policy_points", "policy_tools", "actors", "target_groups", "mechanisms", "risks", "caution_notes", "missing_questions"],
            "target_sections": ["hotspot", "theme", "insight"],
        },
        {
            "chunk_id": "hotspot_core_lanes",
            "fields": ["hotspot_rationale_items", "core_material_items"],
            "target_sections": ["hotspot", "theme"],
        },
        {
            "chunk_id": "comparison_lanes",
            "fields": ["comparison_items", "comparison_deep_dive_items"],
            "matrix_fields": ["comparison_matrix"],
            "target_sections": ["comparison"],
        },
        {
            "chunk_id": "impact_lanes",
            "fields": ["impact_items", "impact_deep_dive_items"],
            "matrix_fields": ["impact_table"],
            "target_sections": ["impact", "insight"],
        },
        {
            "chunk_id": "claims",
            "fields": ["claim_candidates"],
            "matrix_fields": ["policy_claim_material_matrix"],
            "target_sections": ["hotspot", "comparison", "impact", "insight"],
        },
        {
            "chunk_id": "insight",
            "fields": ["missing_questions", "caution_notes"],
            "matrix_fields": ["insight_table"],
            "target_sections": ["insight"],
        },
    ]
    jobs = []
    for spec in package_chunks:
        raw_chunk = {
            "packages": [
                {
                    "package_id": package.get("package_id"),
                    **{
                        field: _prepare_compression_field(field, package.get(field))
                        for field in spec.get("fields", [])
                        if package.get(field) not in (None, "", [], {})
                    },
                }
                for package in material_packages
            ],
            "matrices": {
                field: _prepare_compression_field(field, matrices.get(field, []))
                for field in spec.get("matrix_fields", [])
                if matrices.get(field, []) not in (None, "", [], {})
            },
        }
        jobs.append(
            {
                "chunk_id": spec["chunk_id"],
                "target_sections": spec["target_sections"],
                "input": raw_chunk,
                "input_bytes": len(json.dumps(raw_chunk, ensure_ascii=False).encode("utf-8")),
            }
        )
    return jobs


def _run_compression_job(
    job: dict[str, Any],
    agent_runtime: AgentRuntime,
    use_api: bool,
    max_attempts: int,
    timeout_note: int,
    chunks_dir: Path,
) -> dict[str, Any]:
    chunk_id = str(job["chunk_id"])
    input_path = chunks_dir / f"{chunk_id}.input.json"
    write_json(input_path, job["input"])
    if not use_api:
        output = _local_compress_chunk(job)
        write_json(chunks_dir / f"{chunk_id}.output.json", output)
        return {
            "chunk_id": chunk_id,
            "status": "PASS_LOCAL",
            "attempts": 0,
            "input_bytes": job.get("input_bytes", 0),
            "output": output,
            "errors": [],
        }

    errors: list[dict[str, Any]] = []
    attempts = 0
    current_jobs = [job]
    while attempts < max_attempts:
        attempts += 1
        started = time.perf_counter()
        try:
            outputs = [_call_compressor_api(agent_runtime, subjob, timeout_note) for subjob in current_jobs]
            merged = _merge_chunk_outputs(chunk_id, job.get("target_sections", []), outputs)
            write_json(chunks_dir / f"{chunk_id}.output.json", merged)
            return {
                "chunk_id": chunk_id,
                "status": "PASS" if attempts == 1 else "PASS_AFTER_RETRY",
                "attempts": attempts,
                "input_bytes": job.get("input_bytes", 0),
                "output": merged,
                "errors": errors,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
            }
        except Exception as exc:  # API boundary: convert failures into audit artifacts.
            error = _compression_error(chunk_id, attempts, exc, job, round(time.perf_counter() - started, 3))
            errors.append(error)
            write_json(chunks_dir / f"{chunk_id}.attempt_{attempts}.error.json", error)
            if attempts >= max_attempts or not _is_retryable(exc):
                output = _local_compress_chunk(job)
                write_json(chunks_dir / f"{chunk_id}.output.json", output)
                return {
                    "chunk_id": chunk_id,
                    "status": "PASS_FALLBACK",
                    "attempts": attempts,
                    "input_bytes": job.get("input_bytes", 0),
                    "output": output,
                    "errors": errors,
                }
            current_jobs = _split_job(job) if attempts == 1 else [_shrink_job(job)]
    output = _local_compress_chunk(job)
    write_json(chunks_dir / f"{chunk_id}.output.json", output)
    return {"chunk_id": chunk_id, "status": "PASS_FALLBACK", "attempts": attempts, "input_bytes": job.get("input_bytes", 0), "output": output, "errors": errors}


def _call_compressor_api(agent_runtime: AgentRuntime, job: dict[str, Any], timeout_note: int) -> dict[str, Any]:
    prompt = _compression_prompt(job, timeout_note)
    content = agent_runtime.complete_text("MaterialCompressionAgent", prompt)
    parsed = _extract_json_object(content)
    if not isinstance(parsed, dict):
        raise ValueError("Compression API did not return a JSON object.")
    parsed.setdefault("chunk_id", job["chunk_id"])
    parsed.setdefault("target_sections", job.get("target_sections", []))
    parsed.setdefault("compressed_points", [])
    parsed.setdefault("missing_needed", [])
    parsed.setdefault("dropped_as_noise", [])
    return parsed


def _compression_prompt(job: dict[str, Any], timeout_note: int) -> str:
    payload = {
        "task": "将当前 chunk 压缩为可供后续分章节写作使用的材料切片。",
        "runtime_constraints": [
            "只能使用输入 JSON，不得新增外部事实。",
            "不得生成报告正文。",
            "不得改写 package_id、source_id、claim_id。",
            "如果信息不足，写 MATERIAL_NEEDED。",
            f"本 chunk 调用应在约 {timeout_note} 秒内完成；优先输出高价值材料而不是穷尽。",
        ],
        "output_schema": {
            "chunk_id": job["chunk_id"],
            "target_sections": job.get("target_sections", []),
            "compressed_points": [
                {
                    "section": "hotspot|theme|comparison|impact|insight",
                    "point": "",
                    "support_level": "strong|medium|weak|unknown",
                    "claim_ids": [],
                    "package_ids": [],
                    "caution": "",
                }
            ],
            "missing_needed": [],
            "dropped_as_noise": [],
        },
        "input": job["input"],
    }
    return "\n".join(
        [
            "你是 MaterialCompressionAgent 的分块压缩器。",
            "输出必须是 JSON object，不要 Markdown，不要代码块。",
            json.dumps(payload, ensure_ascii=False),
        ]
    )


def _local_compress_chunk(job: dict[str, Any]) -> dict[str, Any]:
    points = []
    for package in job.get("input", {}).get("packages", []):
        package_id = package.get("package_id")
        for key, value in package.items():
            if key == "package_id" or value in (None, "", [], {}):
                continue
            for item in _take_values(value, 4):
                points.append(
                    {
                        "section": _section_for_key(key, job.get("target_sections", [])),
                        "point": _truncate_text(item, MAX_FALLBACK_POINT_CHARS),
                        "support_level": "unknown",
                        "claim_ids": [],
                        "package_ids": [package_id] if package_id else [],
                        "caution": "",
                    }
                )
    for name, rows in job.get("input", {}).get("matrices", {}).items():
        for row in _take_values(rows, 4):
            points.append(
                {
                    "section": _section_for_key(name, job.get("target_sections", [])),
                    "point": _truncate_text(row, MAX_FALLBACK_POINT_CHARS),
                    "support_level": "unknown",
                    "claim_ids": [],
                    "package_ids": [],
                    "caution": "",
                }
            )
    return {
        "chunk_id": job["chunk_id"],
        "target_sections": job.get("target_sections", []),
        "compressed_points": points[:24],
        "missing_needed": [],
        "dropped_as_noise": ["local_fallback_truncated_lists"],
    }


def _merge_section_slices(
    material_packages: list[dict[str, Any]],
    matrices: dict[str, Any],
    chunk_results: list[dict[str, Any]],
    narrative_spine: dict[str, Any],
) -> dict[str, Any]:
    slices = {
        section_id: {
            "role": narrative_spine.get("section_roles", {}).get(section_id, ""),
            "handoff": narrative_spine.get("handoffs", {}).get(section_id, {}),
            "materials": [],
            "allowed_claims": [],
            "source_refs": _source_refs_for_section(material_packages, section_id),
            "missing_needed": [],
        }
        for section_id in SECTION_IDS
    }
    for result in chunk_results:
        output = result.get("output", {})
        for point in output.get("compressed_points", []):
            section = str(point.get("section") or "")
            targets = [section] if section in slices else output.get("target_sections", [])
            for target in targets:
                if target in slices:
                    slices[target]["materials"].append(_compact_point(point))
        for missing in output.get("missing_needed", []):
            for target in output.get("target_sections", []):
                if target in slices:
                    slices[target]["missing_needed"].append(strip_citation_markers(missing))

    claims = matrices.get("policy_claim_material_matrix", [])
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        allowed_sections = claim.get("allowed_sections", [])
        for section_id in allowed_sections:
            if section_id in slices:
                slices[section_id]["allowed_claims"].append(_compact_claim_row(claim))
    for section_id in SECTION_IDS:
        slices[section_id]["materials"] = _dedupe_items(slices[section_id]["materials"], "point")[:20]
        slices[section_id]["allowed_claims"] = _dedupe_items(slices[section_id]["allowed_claims"], "claim_text")[:10]
        slices[section_id]["missing_needed"] = _unique_strings(slices[section_id]["missing_needed"])[:8]
    return {
        "compression_summary": {
            "method": "deepseek_chunked_with_local_fallback",
            "source_policy": "source_refs preserved locally; citation_refs and evidence_trace retained only in artifacts",
            "generated_at": utc_timestamp(),
        },
        "narrative_spine": narrative_spine,
        "section_slices": slices,
    }


def _prepare_compression_field(field: str, value: Any) -> Any:
    if field in {"claim_candidates", "policy_claim_material_matrix"}:
        rows = value if isinstance(value, list) else [value]
        return [_compact_claim_like(row) for row in rows[:MAX_COMPRESSION_LIST_ITEMS] if row not in (None, "", [], {})]
    return _prepare_compression_value(value, max_depth=5)


def _prepare_compression_value(value: Any, *, max_depth: int) -> Any:
    if max_depth <= 0:
        return _truncate_text(value, MAX_COMPRESSION_STRING_CHARS)
    if isinstance(value, dict):
        compact: dict[str, Any] = {}
        for key, item in value.items():
            if key in TRACE_HEAVY_KEYS or item in (None, "", [], {}):
                continue
            compact[str(key)] = _prepare_compression_value(item, max_depth=max_depth - 1)
        return compact
    if isinstance(value, list):
        items = [
            _prepare_compression_value(item, max_depth=max_depth - 1)
            for item in value[:MAX_COMPRESSION_LIST_ITEMS]
            if item not in (None, "", [], {})
        ]
        if len(value) > MAX_COMPRESSION_LIST_ITEMS:
            items.append(f"... truncated {len(value) - MAX_COMPRESSION_LIST_ITEMS} more items")
        return items
    return _truncate_text(value, MAX_COMPRESSION_STRING_CHARS)


def _compact_claim_like(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {"claim_text": _truncate_text(row, MAX_COMPRESSED_POINT_CHARS)}
    compact: dict[str, Any] = {}
    for key in CLAIM_ROW_KEYS:
        value = row.get(key)
        if value in (None, "", [], {}):
            continue
        if key == "claim":
            compact["claim_text"] = _truncate_text(value, MAX_COMPRESSED_POINT_CHARS)
        else:
            compact[key] = _prepare_compression_value(value, max_depth=2)
    return compact


def _source_refs_for_section(material_packages: list[dict[str, Any]], section_id: str) -> list[dict[str, Any]]:
    refs = []
    for package in material_packages:
        if section_id not in package.get("section_targets", SECTION_IDS):
            continue
        for ref in package.get("source_refs", []):
            if isinstance(ref, dict):
                refs.append({key: ref.get(key) for key in ["notebook_id", "source_id", "title"] if ref.get(key)})
    return _dedupe_source_refs(refs)[:12]


def _merge_chunk_outputs(chunk_id: str, target_sections: list[str], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    points = []
    missing = []
    dropped = []
    for output in outputs:
        points.extend(output.get("compressed_points", []))
        missing.extend(output.get("missing_needed", []))
        dropped.extend(output.get("dropped_as_noise", []))
    return {
        "chunk_id": chunk_id,
        "target_sections": target_sections,
        "compressed_points": points,
        "missing_needed": _unique_strings([strip_citation_markers(item) for item in missing]),
        "dropped_as_noise": _unique_strings([strip_citation_markers(item) for item in dropped]),
    }


def _split_job(job: dict[str, Any]) -> list[dict[str, Any]]:
    packages = job.get("input", {}).get("packages", [])
    if len(packages) > 1:
        midpoint = max(1, len(packages) // 2)
        return [_job_with_packages(job, packages[:midpoint], "a"), _job_with_packages(job, packages[midpoint:], "b")]
    split_input = _split_first_large_list(job.get("input", {}))
    if split_input:
        return [
            {**job, "chunk_id": f"{job['chunk_id']}_a", "input": split_input[0]},
            {**job, "chunk_id": f"{job['chunk_id']}_b", "input": split_input[1]},
        ]
    return [_shrink_job(job)]


def _job_with_packages(job: dict[str, Any], packages: list[dict[str, Any]], suffix: str) -> dict[str, Any]:
    return {**job, "chunk_id": f"{job['chunk_id']}_{suffix}", "input": {**job.get("input", {}), "packages": packages}}


def _split_first_large_list(value: Any) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if not isinstance(value, dict):
        return None
    for key, item in value.items():
        if isinstance(item, list) and len(item) > 1:
            midpoint = max(1, len(item) // 2)
            left = dict(value)
            right = dict(value)
            left[key] = item[:midpoint]
            right[key] = item[midpoint:]
            return left, right
        if isinstance(item, dict):
            nested = _split_first_large_list(item)
            if nested:
                left = dict(value)
                right = dict(value)
                left[key], right[key] = nested
                return left, right
    return None


def _shrink_job(job: dict[str, Any]) -> dict[str, Any]:
    return {**job, "input": _shrink_value(job.get("input", {}), max_items=3, max_string=700)}


def _shrink_value(value: Any, *, max_items: int, max_string: int) -> Any:
    if isinstance(value, dict):
        return {key: _shrink_value(item, max_items=max_items, max_string=max_string) for key, item in value.items() if item not in (None, "", [], {})}
    if isinstance(value, list):
        return [_shrink_value(item, max_items=max_items, max_string=max_string) for item in value[:max_items]]
    text = strip_citation_markers(value)
    return text if len(text) <= max_string else text[: max_string - 20].rstrip() + " ...[truncated]"


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    candidates = [stripped]
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("No JSON object found in compression output.")


def _compression_error(chunk_id: str, attempt: int, exc: Exception, job: dict[str, Any], elapsed: float) -> dict[str, Any]:
    message = repr(exc)
    return {
        "chunk_id": chunk_id,
        "attempt": attempt,
        "status": "ERROR",
        "error_type": exc.__class__.__name__,
        "message": message,
        "request_bytes": job.get("input_bytes", 0),
        "elapsed_seconds": elapsed,
        "action": "local_fallback" if not _is_retryable(exc) else "split_and_retry",
        "generated_at": utc_timestamp(),
    }


def _is_retryable(exc: Exception) -> bool:
    message = repr(exc)
    if any(marker in message for marker in NON_RETRYABLE_ERROR_MARKERS):
        return False
    return any(marker in message for marker in TRANSIENT_ERROR_MARKERS)


def _chunk_manifest_item(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": result.get("chunk_id"),
        "status": result.get("status"),
        "attempts": result.get("attempts", 0),
        "input_bytes": result.get("input_bytes", 0),
        "output_points": len(result.get("output", {}).get("compressed_points", [])),
        "error_count": len(result.get("errors", [])),
        "elapsed_seconds": result.get("elapsed_seconds"),
    }


def _compression_status(chunk_results: list[dict[str, Any]], errors: list[dict[str, Any]]) -> str:
    if any(result.get("status") == "PASS_FALLBACK" for result in chunk_results):
        return "PASS_WITH_FALLBACK"
    if errors or any(result.get("status") == "PASS_AFTER_RETRY" for result in chunk_results):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def _take_values(value: Any, max_items: int) -> list[str]:
    if isinstance(value, list):
        return [_summarize_fallback_item(item) for item in value[:max_items]]
    if isinstance(value, dict):
        if any(key in value for key in CLAIM_ROW_KEYS):
            return [_summarize_fallback_item(value)]
        return [
            f"{key}: {_summarize_fallback_item(item)}"
            for key, item in list(value.items())[:max_items]
            if item not in (None, "", [], {}) and key not in TRACE_HEAVY_KEYS
        ]
    return [_summarize_fallback_item(value)]


def _summarize_fallback_item(value: Any) -> str:
    if isinstance(value, dict):
        for key in ["claim_text", "claim", "point", "hotspot_signal", "policy_problem", "source_specific_findings", "frontier_feature"]:
            if value.get(key):
                return _truncate_text(value.get(key), MAX_FALLBACK_POINT_CHARS)
        parts = []
        for key, item in value.items():
            if key in TRACE_HEAVY_KEYS or item in (None, "", [], {}):
                continue
            parts.append(f"{key}: {_truncate_text(item, 220)}")
            if len(parts) >= 4:
                break
        return _truncate_text("；".join(parts), MAX_FALLBACK_POINT_CHARS)
    return _truncate_text(value, MAX_FALLBACK_POINT_CHARS)


def _section_for_key(key: str, targets: list[str]) -> str:
    if "comparison" in key:
        return "comparison"
    if "impact" in key:
        return "impact"
    if "insight" in key or "missing" in key:
        return "insight"
    if "theme" in targets:
        return "theme"
    return targets[0] if targets else "hotspot"


def _compact_point(point: dict[str, Any]) -> dict[str, Any]:
    return {
        "point": _truncate_text(point.get("point", ""), MAX_COMPRESSED_POINT_CHARS),
        "support_level": str(point.get("support_level") or "unknown"),
        "claim_ids": point.get("claim_ids", [])[:8] if isinstance(point.get("claim_ids", []), list) else [],
        "package_ids": point.get("package_ids", [])[:6] if isinstance(point.get("package_ids", []), list) else [],
        "caution": _truncate_text(point.get("caution", ""), MAX_COMPRESSED_CAUTION_CHARS),
    }


def _compact_claim_row(claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": claim.get("claim_id"),
        "claim_text": _truncate_text(claim.get("claim_text", ""), MAX_COMPRESSED_POINT_CHARS),
        "support_level": claim.get("support_level", "unknown"),
        "caution_note": _truncate_text(claim.get("caution_note", ""), MAX_COMPRESSED_CAUTION_CHARS),
        "material_package_ids": claim.get("material_package_ids", [])[:6] if isinstance(claim.get("material_package_ids", []), list) else [],
    }


def _dedupe_items(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for item in items:
        value = str(item.get(key, ""))
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(item)
    return result


def _dedupe_source_refs(refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result = []
    for ref in refs:
        key = (str(ref.get("notebook_id", "")), str(ref.get("source_id", "")), str(ref.get("title", "")))
        if key in seen:
            continue
        seen.add(key)
        result.append(ref)
    return result


def _unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result = []
    for value in values:
        text = strip_citation_markers(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _truncate_text(value: Any, max_chars: int) -> str:
    text = strip_citation_markers(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + " ...[truncated]"
