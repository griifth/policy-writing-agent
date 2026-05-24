from __future__ import annotations

from typing import Any


def assemble_report(
    task_spec: dict[str, Any],
    section_drafts: dict[str, str],
    review_reports: list[dict[str, Any]],
    material_packages: list[dict[str, Any]] | None = None,
    matrices: dict[str, Any] | None = None,
) -> str:
    title = task_spec.get("topic", "政策热点研判报告")
    lines = [
        f"# {title}",
        "",
        "## 摘要",
        "",
        "本报告由 NotebookLM 支持的政策热点研判写作 Agent 生成。报告先拆解检索问题，再形成材料包和判断-材料矩阵，最后按章节契约生成热点梳理、主题归类、政策前沿比较、影响研判和启发建议。",
        "",
    ]
    for section_id in ["hotspot", "theme", "comparison", "impact", "insight"]:
        draft = section_drafts.get(section_id)
        if draft:
            lines.append(_strip_contract_check(draft).strip())
            lines.append("")

    material_packages = material_packages or []
    matrices = matrices or {}

    lines.extend(["# 附录一：材料包索引", "", "| Package | Hotspot | Main Theme | Sections |", "|---|---|---|---|"])
    for package in material_packages:
        lines.append(
            f"| {package.get('package_id')} | {package.get('hotspot')} | {package.get('main_theme')} | {', '.join(package.get('section_targets', []))} |"
        )
    if not material_packages:
        lines.append("| MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED |")

    lines.extend(["", "# 附录二：缺口问题", ""])
    gaps = [question for package in material_packages for question in package.get("missing_questions", [])]
    if gaps:
        for gap in gaps:
            lines.append(f"- {gap.get('question', gap)}")
    else:
        lines.append("- 当前材料包未记录阻断性缺口。")

    lines.extend(["", "# 附录三：关键判断表", "", "| Claim | Support | Sections | Caution |", "|---|---|---|---|"])
    for claim in matrices.get("policy_claim_material_matrix", []):
        lines.append(
            f"| {claim.get('claim_text')} | {claim.get('support_level')} | {', '.join(claim.get('allowed_sections', []))} | {claim.get('caution_note', '')} |"
        )
    if not matrices.get("policy_claim_material_matrix"):
        lines.append("| MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED |")

    lines.extend(["", "# 附录四：审查状态", "", "| Reviewer | Verdict | Reason |", "|---|---|---|"])
    for report in review_reports:
        lines.append(f"| {report.get('reviewer')} | {report.get('verdict')} | {report.get('reason_code')} |")
    lines.append("")
    return "\n".join(lines)


def _strip_contract_check(draft: str) -> str:
    marker = "\n## 本节契约检查"
    if marker not in draft:
        return draft
    return draft.split(marker, 1)[0]
