from __future__ import annotations

from pathlib import Path
from typing import Any


LANE_DEEP_DIVE_SCHEMAS: dict[str, dict[str, Any]] = {
    "hotspot_rationale_deep_dive": {
        "section": "hotspot",
        "purpose": "判断为什么这个热点值得进入报告，而不是直接扩写完整正文。",
        "fields": [
            "hotspot_signal",
            "repeated_signal",
            "policy_problem",
            "rise_reason",
            "actors",
            "support_level",
            "caution",
            "answer",
        ],
    },
    "core_material_deep_dive": {
        "section": "hotspot",
        "purpose": "提取能支撑报告主体分析的政策点、工具、行动者、机制、风险和可写 claim。",
        "fields": [
            "policy_points",
            "policy_tools",
            "actors",
            "target_groups",
            "mechanisms",
            "risks",
            "claim_candidates",
            "missing_questions",
            "source_specific_findings",
        ],
    },
    "comparison_deep_dive": {
        "section": "comparison",
        "purpose": "把限定 source 中可用于横向比较的政策目标、对象、工具、机制和风险治理维度结构化。",
        "fields": [
            "policy_goal",
            "target_group",
            "governance_actor",
            "policy_tool",
            "implementation_mechanism",
            "evaluation_mechanism",
            "risk_governance",
            "frontier_feature",
            "comparable_unit",
        ],
    },
    "impact_deep_dive": {
        "section": "impact",
        "purpose": "区分 source 明示影响与谨慎推断影响，为影响研判段落提供可控材料。",
        "fields": [
            "explicit_impacts",
            "cautious_inferences",
            "governance_impact",
            "school_practice_impact",
            "teacher_development_impact",
            "student_learning_impact",
            "education_evaluation_impact",
            "platform_resource_impact",
            "ethics_safety_impact",
            "uncertainty",
        ],
    },
}

DEFAULT_SOURCE_DEEP_DIVE_LANES = list(LANE_DEEP_DIVE_SCHEMAS)


def build_citation_sweep_job(task_spec: dict[str, Any], run_dir: str | Path, job_index: int) -> dict[str, Any]:
    job_id = f"{job_index:02d}_citation_sweep"
    return {
        "id": job_id,
        "section": "hotspot",
        "query_type": "citation_sweep",
        "schema_name": "citation_sweep",
        "notebook_id": task_spec["notebook_id"],
        "prompt_file": None,
        "prompt": _citation_sweep_prompt(task_spec),
        "expected_fields": ["answer", "citations", "source_candidates"],
        "output_contract": {
            "type": "json_object",
            "schema_name": "citation_sweep",
            "required_fields": ["answer", "citations", "source_candidates"],
        },
        "output_target": str(Path(run_dir) / "query_results" / f"{job_id}.json"),
    }


def build_source_deep_dive_candidates(
    query_results: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    limit: int | None = 3,
) -> list[dict[str, Any]]:
    if limit == 0:
        return []
    source_index = _source_index(sources)
    candidates: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, str]] = set()

    for result in query_results:
        if result.get("status") != "PASS":
            continue
        for trace in result.get("evidence_trace", []):
            if not isinstance(trace, dict):
                continue
            for resolved in _resolve_trace_sources(trace, source_index):
                if _append_candidate_from_source(candidates, seen_sources, resolved, trace):
                    if _candidate_limit_reached(candidates, limit):
                        return candidates
        for item in _structured_source_candidates(result):
            resolved = _resolve_candidate_source(item, source_index)
            if not resolved:
                continue
            trace = {
                "trace_id": item.get("candidate_id") or item.get("id"),
                "job_id": result.get("job_id"),
                "query_type": result.get("query_type"),
                "text": item.get("reason") or item.get("evidence_sentence") or item.get("seed_text") or "",
                "citation_ids": item.get("citation_ids", []),
            }
            if _append_candidate_from_source(candidates, seen_sources, resolved, trace):
                if _candidate_limit_reached(candidates, limit):
                    return candidates
    return candidates


def _candidate_limit_reached(candidates: list[dict[str, Any]], limit: int | None) -> bool:
    return limit is not None and len(candidates) >= limit


def build_source_deep_dive_jobs(
    candidates: list[dict[str, Any]],
    task_spec: dict[str, Any],
    run_dir: str | Path,
    start_index: int,
    lanes: list[str] | None = None,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    run_dir = Path(run_dir)
    lane_names = _valid_lanes(lanes)
    job_counter = 0
    for candidate_index, candidate in enumerate(candidates, start=1):
        for lane in lane_names:
            job_counter += 1
            schema = LANE_DEEP_DIVE_SCHEMAS[lane]
            job_index = start_index + job_counter
            job_id = f"{job_index:02d}_{lane}_{candidate_index}"
            prompt = _source_deep_dive_prompt(task_spec, candidate, lane, schema)
            fields = list(schema["fields"])
            jobs.append(
                {
                    "id": job_id,
                    "section": schema["section"],
                    "query_type": lane,
                    "schema_name": lane,
                    "notebook_id": task_spec["notebook_id"],
                    "source_ids": [candidate["source_id"]],
                    "source_title": candidate.get("source_title", ""),
                    "source_candidate_id": candidate.get("candidate_id"),
                    "deep_dive_lane": lane,
                    "seed_trace_id": candidate.get("seed_trace_id"),
                    "seed_query_job_id": candidate.get("seed_query_job_id"),
                    "seed_query_type": candidate.get("seed_query_type"),
                    "seed_text": candidate.get("seed_text", ""),
                    "deep_dive_reason": candidate.get("deep_dive_reason", ""),
                    "prompt_file": None,
                    "prompt": prompt,
                    "expected_fields": fields,
                    "output_contract": {
                        "type": "json_object",
                        "schema_name": lane,
                        "required_fields": fields,
                    },
                    "output_target": str(run_dir / "query_results" / f"{job_id}.json"),
                }
            )
    return jobs


def _citation_sweep_prompt(task_spec: dict[str, Any]) -> str:
    return (
        f"任务主题：“{task_spec['topic']}”。\n"
        "请基于当前 NotebookLM 知识库，找出最值得深挖的政策热点证据句。"
        "重点关注反复出现、跨主题出现或具有政策前沿意义的内容。\n"
        "必须尽量覆盖 3 个不同 source 文件；如果知识库中确实不足 3 个相关 source，才少于 3 个。"
        "不要把所有引用集中到同一个 source。\n"
        "请严格只返回一个 JSON object，不要 Markdown 代码块，不要额外解释。\n"
        "返回格式必须是：\n"
        "{\n"
        '  "answer": "带 [n] 引用标记的纯文本回答。每一句关键判断都要带至少一个 [n]。",\n'
        '  "citations": [\n'
        '    {"id": 1, "title": "报告名称"}\n'
        "  ],\n"
        '  "source_candidates": [\n'
        '    {"source_title": "报告名称", "reason": "为什么值得 source-specific deep dive", "citation_ids": [1]}\n'
        "  ]\n"
        "}\n"
        "source_candidates 中的 source_title 必须和 citations.title 一致。"
        "不要写完整报告；只给能指导 source-specific deep dive 的证据句。"
    )


def _source_deep_dive_prompt(
    task_spec: dict[str, Any],
    candidate: dict[str, Any],
    lane: str,
    schema: dict[str, Any],
) -> str:
    field_lines = ",\n".join(f'  "{field}": ""' for field in schema["fields"])
    return (
        f"任务主题：“{task_spec['topic']}”。\n"
        "你正在执行第二阶段 source-specific deep dive。当前 NotebookLM 查询已经被 CLI 限定到一个 source。\n"
        f"Source title: {candidate.get('source_title', '')}\n"
        f"第一阶段证据句：{candidate.get('seed_text', '')}\n"
        f"本轮 lane：{lane}\n"
        f"本轮目标：{schema['purpose']}\n\n"
        "请只基于当前限定 source，围绕上述证据句提取可进入政策研判材料包的信息。"
        "不要使用其他 source，不要使用常识补齐，不要验证 NotebookLM 知识库准确性。\n"
        "请严格只返回一个 JSON object，不要 Markdown 代码块，不要额外解释。\n"
        "字段值可以是字符串、对象数组或字符串数组，但必须与字段名语义对应。\n"
        "如果 NotebookLM 返回引用标记，请在关键字段值中保留 [n]，不要把引用改写成章节名。\n"
        "JSON object 必须包含以下字段：\n"
        "{\n"
        f'  "_schema": "{lane}",\n'
        f"{field_lines}\n"
        "}\n"
        "如果 source 内没有对应材料，字段值请写空数组或说明缺口，不要用其他 source 或常识补齐。"
    )


def _valid_lanes(lanes: list[str] | None) -> list[str]:
    if not lanes:
        return DEFAULT_SOURCE_DEEP_DIVE_LANES
    valid = [lane for lane in lanes if lane in LANE_DEEP_DIVE_SCHEMAS]
    return valid or DEFAULT_SOURCE_DEEP_DIVE_LANES


def _source_index(sources: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    by_title: dict[str, dict[str, str]] = {}
    for source in sources:
        source_id = str(source.get("source_id") or source.get("id") or source.get("uuid") or "")
        title = str(source.get("title") or source.get("name") or "")
        if not source_id and not title:
            continue
        normalized = {"notebook_id": str(source.get("notebook_id") or ""), "source_id": source_id or title, "title": title}
        if source_id:
            by_id[source_id] = normalized
        if title:
            by_title[title] = normalized
    return {"by_id": by_id, "by_title": by_title}


def _resolve_trace_sources(trace: dict[str, Any], source_index: dict[str, dict[str, dict[str, str]]]) -> list[dict[str, str]]:
    by_id = source_index.get("by_id", {})
    by_title = source_index.get("by_title", {})
    resolved_sources: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for ref in trace.get("source_refs", []):
        if not isinstance(ref, dict):
            continue
        source_id = str(ref.get("source_id") or "")
        title = str(ref.get("title") or "")
        if source_id and source_id in by_id:
            resolved = by_id[source_id]
        elif title and title in by_title:
            resolved = by_title[title]
        else:
            continue
        key = (resolved.get("notebook_id", ""), resolved["source_id"])
        if key in seen:
            continue
        seen.add(key)
        resolved_sources.append(resolved)
    return resolved_sources


def _resolve_trace_source(trace: dict[str, Any], source_index: dict[str, dict[str, dict[str, str]]]) -> dict[str, str] | None:
    resolved = _resolve_trace_sources(trace, source_index)
    return resolved[0] if resolved else None


def _append_candidate_from_source(
    candidates: list[dict[str, Any]],
    seen_sources: set[tuple[str, str]],
    resolved: dict[str, str],
    trace: dict[str, Any],
) -> bool:
    source_id = resolved["source_id"]
    key = (resolved.get("notebook_id", ""), source_id)
    if key in seen_sources:
        return False
    seen_sources.add(key)
    candidates.append(
        {
            "candidate_id": f"source_candidate_{len(candidates) + 1}",
            "notebook_id": resolved.get("notebook_id", ""),
            "source_id": source_id,
            "source_title": resolved.get("title", ""),
            "seed_trace_id": trace.get("trace_id"),
            "seed_query_job_id": trace.get("job_id"),
            "seed_query_type": trace.get("query_type"),
            "seed_text": trace.get("text", ""),
            "citation_ids": trace.get("citation_ids", []),
            "deep_dive_reason": _deep_dive_reason(trace),
        }
    )
    return True


def _structured_source_candidates(result: dict[str, Any]) -> list[dict[str, Any]]:
    structured = result.get("structured_answer")
    if not isinstance(structured, dict):
        return []
    value = structured.get("source_candidates")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _resolve_candidate_source(item: dict[str, Any], source_index: dict[str, dict[str, dict[str, str]]]) -> dict[str, str] | None:
    by_id = source_index.get("by_id", {})
    by_title = source_index.get("by_title", {})
    source_id = str(item.get("source_id") or "")
    title = str(item.get("source_title") or item.get("title") or "")
    if source_id and source_id in by_id:
        return by_id[source_id]
    if title and title in by_title:
        return by_title[title]
    return None


def _deep_dive_reason(trace: dict[str, Any]) -> str:
    query_type = trace.get("query_type", "unknown")
    text = trace.get("text", "")
    return f"第一阶段 {query_type} 回答包含可引用证据句，适合限定 source 深挖：{text[:80]}"
