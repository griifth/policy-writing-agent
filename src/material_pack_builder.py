from __future__ import annotations

from typing import Any

from schema_validation import validate_required_fields


def build_material_packages(query_results: list[dict[str, Any]], dimensions: dict[str, Any]) -> list[dict[str, Any]]:
    merged: dict[str, Any] = {}
    for result in query_results:
        if result.get("status") != "PASS":
            continue
        structured = result.get("structured_answer", {})
        if isinstance(structured, dict):
            merged.update(structured)

    package = {
        "package_id": "mp_ai_literacy",
        "hotspot": merged.get("hotspot_name", "AI 教育政策热点"),
        "main_theme": merged.get("main_theme", "AI 教育战略与国家规划"),
        "cross_themes": _as_list(merged.get("cross_themes", merged.get("involved_themes", []))),
        "section_targets": ["hotspot", "theme", "comparison", "impact", "insight"],
        "policy_points": _as_list(merged.get("policy_points", [])),
        "policy_tools": _as_list(merged.get("policy_tools", [merged.get("policy_tool")] if merged.get("policy_tool") else [])),
        "actors": _as_list(merged.get("actors", merged.get("representative_actors", []))),
        "target_groups": _as_list([merged.get("target_group")] if merged.get("target_group") else []),
        "mechanisms": _as_list(merged.get("mechanisms", [merged.get("implementation_mechanism")] if merged.get("implementation_mechanism") else [])),
        "risks": _as_list(merged.get("risks", [merged.get("risk_governance")] if merged.get("risk_governance") else [])),
        "comparison_items": [
            {
                "policy_goal": merged.get("policy_goal"),
                "target_group": merged.get("target_group"),
                "governance_actor": merged.get("governance_actor"),
                "policy_tool": merged.get("policy_tool"),
                "implementation_mechanism": merged.get("implementation_mechanism"),
                "evaluation_mechanism": merged.get("evaluation_mechanism"),
                "risk_governance": merged.get("risk_governance"),
                "frontier_feature": merged.get("frontier_feature"),
            }
        ],
        "impact_items": [
            {
                "governance_impact": merged.get("governance_impact"),
                "school_practice_impact": merged.get("school_practice_impact"),
                "teacher_development_impact": merged.get("teacher_development_impact"),
                "student_learning_impact": merged.get("student_learning_impact"),
                "education_evaluation_impact": merged.get("education_evaluation_impact"),
                "platform_resource_impact": merged.get("platform_resource_impact"),
                "ethics_safety_impact": merged.get("ethics_safety_impact"),
            }
        ],
        "claim_candidates": _as_claims(merged.get("claim_candidates", [])),
        "caution_notes": _as_list(merged.get("classification_tension", "")),
        "missing_questions": _as_missing_questions(merged.get("missing_questions", [])),
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


def _as_claims(value: Any) -> list[dict[str, Any]]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [
            {
                "claim": value,
                "support_level": "medium",
                "allowed_sections": ["hotspot", "comparison", "insight"],
                "caution": "由 NotebookLM 返回的字符串判断转换而来，需在审查阶段确认支撑强度。",
            }
        ]
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        claims: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                claims.append(item)
            elif item:
                claims.append(
                    {
                        "claim": str(item),
                        "support_level": "medium",
                        "allowed_sections": ["hotspot", "comparison", "insight"],
                        "caution": "由 NotebookLM 返回的列表项转换而来，需在审查阶段确认支撑强度。",
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
