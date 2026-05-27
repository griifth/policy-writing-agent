from __future__ import annotations

from typing import Any

from text_cleaning import strip_citation_markers


def build_hotspot_theme_matrix(material_packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "hotspot": package["hotspot"],
            "main_theme": package["main_theme"],
            "cross_themes": package.get("cross_themes", []),
            "section_targets": package.get("section_targets", []),
        }
        for package in material_packages
    ]


def build_comparison_matrix(material_packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in material_packages:
        for item in package.get("comparison_items", []):
            row = {"hotspot": package["hotspot"], "main_theme": package["main_theme"]}
            row.update(item)
            rows.append(row)
    return rows


def build_impact_table(material_packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in material_packages:
        for item in package.get("impact_items", []):
            row = {"hotspot": package["hotspot"], "main_theme": package["main_theme"]}
            row.update(item)
            rows.append(row)
    return rows


def build_insight_table(material_packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in material_packages:
        raw = package.get("raw_fields", {})
        rows.append(
            {
                "hotspot": package["hotspot"],
                "research_insight": raw.get("research_insight"),
                "governance_insight": raw.get("governance_insight"),
                "practice_insight": raw.get("practice_insight"),
                "monitoring_insight": raw.get("monitoring_insight"),
                "knowledge_base_insight": raw.get("knowledge_base_insight"),
            }
        )
    return rows


def build_policy_claim_material_matrix(material_packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in material_packages:
        for index, claim in enumerate(package.get("claim_candidates", []), start=1):
            rows.append(
                {
                    "claim_id": f"{package['package_id']}_claim_{index}",
                    "claim_text": strip_citation_markers(claim.get("claim")),
                    "claim_type": "hotspot",
                    "material_package_ids": [package["package_id"]],
                    "support_level": claim.get("support_level", "weak"),
                    "allowed_sections": claim.get("allowed_sections", []),
                    "caution_note": strip_citation_markers(claim.get("caution", "")),
                    "source_refs": claim.get("source_refs", package.get("source_refs", [])),
                    "citation_refs": claim.get("citation_refs", package.get("citation_refs", [])),
                    "evidence_trace": claim.get("evidence_trace", package.get("evidence_trace", [])),
                    "missing_fields": [],
                }
            )
    return rows


def build_all_matrices(material_packages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "hotspot_theme_matrix": build_hotspot_theme_matrix(material_packages),
        "comparison_matrix": build_comparison_matrix(material_packages),
        "impact_table": build_impact_table(material_packages),
        "insight_table": build_insight_table(material_packages),
        "policy_claim_material_matrix": build_policy_claim_material_matrix(material_packages),
    }
