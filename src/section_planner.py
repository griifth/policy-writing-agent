from __future__ import annotations

from typing import Any


def build_report_plan(task_spec: dict[str, Any], matrices: dict[str, Any], section_contracts: dict[str, Any]) -> str:
    lines = [
        "# POLICY_REPORT_PLAN",
        "",
        "## Metadata",
        f"- Topic: {task_spec['topic']}",
        f"- Notebook ID: {task_spec['notebook_id']}",
        f"- Audience: {task_spec.get('audience', '')}",
        f"- Assurance: {task_spec.get('assurance', 'draft')}",
        f"- Traceability Owner: {task_spec.get('traceability_owner', 'notebooklm')}",
        "",
        "## Hotspot Candidates",
        "| Hotspot | Main Theme | Cross Themes |",
        "|---|---|---|",
    ]
    for row in matrices.get("hotspot_theme_matrix", []):
        lines.append(
            f"| {row.get('hotspot')} | {row.get('main_theme')} | {', '.join(row.get('cross_themes', []))} |"
        )

    lines.extend(["", "## PolicyClaim-Material Matrix", "| Claim | Material Package | Sections | Support | Caution |", "|---|---|---|---|---|"])
    for row in matrices.get("policy_claim_material_matrix", []):
        lines.append(
            "| {claim} | {packages} | {sections} | {support} | {caution} |".format(
                claim=row.get("claim_text"),
                packages=", ".join(row.get("material_package_ids", [])),
                sections=", ".join(row.get("allowed_sections", [])),
                support=row.get("support_level"),
                caution=row.get("caution_note", ""),
            )
        )

    lines.extend(["", "## Section Contracts"])
    for section_id, contract in section_contracts.items():
        lines.extend(
            [
                f"### {contract.get('title', section_id)}",
                f"- Function: {contract.get('function', '')}",
                f"- Required Inputs: {', '.join(contract.get('required_inputs', []))}",
                f"- Must Answer: {'; '.join(contract.get('must_answer', []))}",
                f"- Forbidden: {'; '.join(contract.get('forbidden', []))}",
                f"- Output Shape: {'; '.join(contract.get('output_shape', []))}",
                "",
            ]
        )

    lines.extend(
        [
            "## Entry Decision",
            "",
            "Draft writing is allowed when material packages are PASS or WARN. BLOCKED packages must generate follow-up QueryJobs before polished/submission output.",
            "",
        ]
    )
    return "\n".join(lines)


def build_section_plan(section_contracts: dict[str, Any], matrices: dict[str, Any]) -> dict[str, Any]:
    claims = matrices.get("policy_claim_material_matrix", [])
    return {
        section_id: {
            "contract": contract,
            "claim_ids": [
                claim["claim_id"]
                for claim in claims
                if section_id in claim.get("allowed_sections", [])
            ],
            "status": "PASS",
        }
        for section_id, contract in section_contracts.items()
    }
