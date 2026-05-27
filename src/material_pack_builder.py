from __future__ import annotations

from typing import Any

from schema_validation import validate_required_fields


SOURCE_DEEP_DIVE_LANES = [
    "hotspot_rationale_deep_dive",
    "core_material_deep_dive",
    "comparison_deep_dive",
    "impact_deep_dive",
]


def build_material_packages(query_results: list[dict[str, Any]], dimensions: dict[str, Any]) -> list[dict[str, Any]]:
    merged: dict[str, Any] = {}
    deep_dive_materials: dict[str, list[dict[str, Any]]] = {lane: [] for lane in SOURCE_DEEP_DIVE_LANES}
    evidence_trace: list[dict[str, Any]] = []
    source_refs: list[dict[str, Any]] = []
    citation_refs: list[dict[str, Any]] = []
    for result in query_results:
        if result.get("status") != "PASS":
            continue
        structured = result.get("structured_answer", {})
        if isinstance(structured, dict):
            merged.update(structured)
            lane = result.get("deep_dive_lane") or result.get("query_type")
            if lane in deep_dive_materials:
                deep_dive_materials[lane].append(_lane_material_item(result, structured))
        evidence_trace.extend(_as_dict_list(result.get("evidence_trace", [])))
        source_refs.extend(_as_dict_list(result.get("source_refs", [])))
        citation_refs.extend(_as_dict_list(result.get("citation_refs", result.get("citations", []))))

    source_refs = _dedupe_refs(source_refs, ("notebook_id", "source_id", "title"))
    citation_refs = _dedupe_refs(citation_refs, ("notebook_id", "id", "title", "source_id"))
    hotspot_rationale_items = deep_dive_materials["hotspot_rationale_deep_dive"]
    core_material_items = deep_dive_materials["core_material_deep_dive"]
    comparison_deep_dive_items = deep_dive_materials["comparison_deep_dive"]
    impact_deep_dive_items = deep_dive_materials["impact_deep_dive"]

    package = {
        "package_id": "mp_ai_literacy",
        "hotspot": merged.get("hotspot_name", "AI 教育政策热点"),
        "main_theme": merged.get("main_theme", "AI 教育战略与国家规划"),
        "cross_themes": _as_list(merged.get("cross_themes", merged.get("involved_themes", []))),
        "section_targets": ["hotspot", "theme", "comparison", "impact", "insight"],
        "policy_points": _collect_field(merged, core_material_items, "policy_points"),
        "policy_tools": _collect_field(merged, core_material_items, "policy_tools", [merged.get("policy_tool")] if merged.get("policy_tool") else []),
        "actors": _collect_field(merged, [*hotspot_rationale_items, *core_material_items], "actors", merged.get("representative_actors", [])),
        "target_groups": _collect_field(merged, core_material_items, "target_groups", [merged.get("target_group")] if merged.get("target_group") else []),
        "mechanisms": _collect_field(merged, core_material_items, "mechanisms", [merged.get("implementation_mechanism")] if merged.get("implementation_mechanism") else []),
        "risks": _collect_field(merged, core_material_items, "risks", [merged.get("risk_governance")] if merged.get("risk_governance") else []),
        "comparison_items": _comparison_items(merged, comparison_deep_dive_items),
        "impact_items": _impact_items(merged, impact_deep_dive_items),
        "claim_candidates": _collect_claims(core_material_items, merged, source_refs, citation_refs, evidence_trace),
        "caution_notes": _as_list(merged.get("classification_tension", "")),
        "missing_questions": _as_missing_questions(_collect_field(merged, core_material_items, "missing_questions")),
        "deep_dive_materials": deep_dive_materials,
        "hotspot_rationale_items": hotspot_rationale_items,
        "core_material_items": core_material_items,
        "comparison_deep_dive_items": comparison_deep_dive_items,
        "impact_deep_dive_items": impact_deep_dive_items,
        "source_refs": source_refs,
        "citation_refs": citation_refs,
        "evidence_trace": evidence_trace,
        "raw_fields": merged,
    }

    audit = validate_required_fields(package, "material_package", dimensions)
    if audit["verdict"] == "BLOCKED":
        package["missing_questions"] = [
            {
                "field": field,
                "section": "material_package",
                "question": f"请补充材料包字段 {field} 所需信息。",
                "expected_fields": [field],
            }
            for field in audit["missing_fields"]
        ]
    return [package]


def audit_material_package(package: dict[str, Any], dimensions: dict[str, Any]) -> dict[str, Any]:
    audit = validate_required_fields(package, "material_package", dimensions)
    audit.update(
        {
            "audit_skill": "material-pack-audit",
            "package_id": package.get("package_id"),
            "followup_queries": package.get("missing_questions", []),
        }
    )
    return audit


def _as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def _as_claims(
    value: Any,
    source_refs: list[dict[str, Any]] | None = None,
    citation_refs: list[dict[str, Any]] | None = None,
    evidence_trace: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    source_refs = source_refs or []
    citation_refs = citation_refs or []
    evidence_trace = evidence_trace or []
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [
            {
                "claim": value,
                "support_level": "medium",
                "allowed_sections": ["hotspot", "comparison", "insight"],
                "caution": "由 NotebookLM 返回的字符串判断转换而来，需在审查阶段确认支撑强度。",
                "source_refs": source_refs,
                "citation_refs": citation_refs,
                "evidence_trace": evidence_trace,
            }
        ]
    if isinstance(value, dict):
        return [_with_trace(value, source_refs, citation_refs, evidence_trace)]
    if isinstance(value, list):
        claims: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                claims.append(_with_trace(item, source_refs, citation_refs, evidence_trace))
            elif item:
                claims.append(
                    {
                        "claim": str(item),
                        "support_level": "medium",
                        "allowed_sections": ["hotspot", "comparison", "insight"],
                        "caution": "由 NotebookLM 返回的列表项转换而来，需在审查阶段确认支撑强度。",
                        "source_refs": source_refs,
                        "citation_refs": citation_refs,
                        "evidence_trace": evidence_trace,
                    }
                )
        return claims
    return []


def _as_missing_questions(value: Any) -> list[dict[str, Any]]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        result: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                result.append(item)
            elif item:
                result.append({"question": str(item)})
        return result
    if isinstance(value, dict):
        return [value]
    return [{"question": str(value)}]


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _lane_material_item(result: dict[str, Any], structured: dict[str, Any]) -> dict[str, Any]:
    item = dict(structured)
    item.update(
        {
            "job_id": result.get("job_id"),
            "query_type": result.get("query_type"),
            "deep_dive_lane": result.get("deep_dive_lane") or result.get("query_type"),
            "source_ids": result.get("source_ids", []),
            "source_title": result.get("source_title", ""),
            "seed_trace_id": result.get("seed_trace_id"),
            "seed_text": result.get("seed_text", ""),
            "source_refs": _as_dict_list(result.get("source_refs", [])),
            "citation_refs": _as_dict_list(result.get("citation_refs", result.get("citations", []))),
            "evidence_trace": _as_dict_list(result.get("evidence_trace", [])),
        }
    )
    return item


def _collect_field(
    merged: dict[str, Any],
    items: list[dict[str, Any]],
    field: str,
    fallback: Any = None,
) -> list[Any]:
    values: list[Any] = []
    values.extend(_as_list(merged.get(field, fallback if fallback is not None else [])))
    for item in items:
        values.extend(_as_list(item.get(field, [])))
    return _dedupe_values(values)


def _collect_claims(
    core_items: list[dict[str, Any]],
    merged: dict[str, Any],
    source_refs: list[dict[str, Any]],
    citation_refs: list[dict[str, Any]],
    evidence_trace: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    claims = _as_claims(merged.get("claim_candidates", []), source_refs, citation_refs, evidence_trace)
    for item in core_items:
        claims.extend(
            _as_claims(
                item.get("claim_candidates", []),
                _as_dict_list(item.get("source_refs", [])) or source_refs,
                _as_dict_list(item.get("citation_refs", [])) or citation_refs,
                _as_dict_list(item.get("evidence_trace", [])) or evidence_trace,
            )
        )
    return _dedupe_claims(claims)


def _comparison_items(merged: dict[str, Any], lane_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "policy_goal",
        "target_group",
        "governance_actor",
        "policy_tool",
        "implementation_mechanism",
        "evaluation_mechanism",
        "risk_governance",
        "frontier_feature",
        "comparable_unit",
    ]
    items = [_select_fields(merged, fields)]
    items.extend(_select_fields(item, fields + ["source_title", "source_refs", "citation_refs", "evidence_trace"]) for item in lane_items)
    return _dedupe_items([item for item in items if any(value not in (None, "", [], {}) for value in item.values())], fields)


def _impact_items(merged: dict[str, Any], lane_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
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
    ]
    items = [_select_fields(merged, fields)]
    items.extend(_select_fields(item, fields + ["source_title", "source_refs", "citation_refs", "evidence_trace"]) for item in lane_items)
    return _dedupe_items([item for item in items if any(value not in (None, "", [], {}) for value in item.values())], fields)


def _select_fields(payload: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: payload.get(field) for field in fields if field in payload}


def _dedupe_refs(refs: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for ref in refs:
        key = tuple(str(ref.get(field, "")) for field in keys)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped


def _dedupe_values(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    deduped: list[Any] = []
    for value in values:
        if value in (None, "", [], {}):
            continue
        key = repr(value)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


def _dedupe_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for claim in claims:
        key = str(claim.get("claim") or claim)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)
    return deduped


def _dedupe_items(items: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    seen: set[tuple[str, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = tuple(repr(item.get(field)) for field in keys)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _with_trace(
    claim: dict[str, Any],
    source_refs: list[dict[str, Any]],
    citation_refs: list[dict[str, Any]],
    evidence_trace: list[dict[str, Any]],
) -> dict[str, Any]:
    enriched = dict(claim)
    enriched.setdefault("source_refs", source_refs)
    enriched.setdefault("citation_refs", citation_refs)
    enriched.setdefault("evidence_trace", evidence_trace)
    return enriched
