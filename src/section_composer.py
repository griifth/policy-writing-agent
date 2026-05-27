from __future__ import annotations

import json
from typing import Any

from text_cleaning import strip_citation_markers


def _bullet_list(values: list[Any]) -> str:
    cleaned = [strip_citation_markers(value) for value in values if value]
    if not cleaned:
        return "- MATERIAL_NEEDED: 缺少可写材料"
    return "\n".join(f"- {value}" for value in cleaned)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "、".join(strip_citation_markers(item) for item in value if item)
    if isinstance(value, dict):
        return "；".join(f"{key}: {strip_citation_markers(val)}" for key, val in value.items() if val)
    return strip_citation_markers(value)


def _first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return strip_citation_markers(value)
    return ""


def compose_section(
    section_id: str,
    contract: dict[str, Any],
    materials: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    matrices: dict[str, Any],
) -> str:
    title = contract.get("title", section_id)
    lines = [f"# {title}", ""]

    if section_id == "hotspot":
        lines.extend(_compose_hotspot(materials, claims))
    elif section_id == "theme":
        lines.extend(_compose_theme(matrices))
    elif section_id == "comparison":
        lines.extend(_compose_comparison(matrices))
    elif section_id == "impact":
        lines.extend(_compose_impact(matrices))
    elif section_id == "insight":
        lines.extend(_compose_insight(matrices, claims))
    else:
        lines.append("MATERIAL_NEEDED: 未识别章节类型。")

    lines.extend(["", "## 本节契约检查", ""])
    lines.append(f"- 功能：{contract.get('function', '')}")
    lines.append(f"- 必答问题：{'；'.join(contract.get('must_answer', []))}")
    return strip_citation_markers("\n".join(lines)) + "\n"


def build_section_prompt(
    section_id: str,
    contract: dict[str, Any],
    materials: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    matrices: dict[str, Any],
) -> str:
    payload = {
        "section_id": section_id,
        "contract": contract,
        "material_packages": materials,
        "claims": claims,
        "matrices": {
            "hotspot_theme_matrix": matrices.get("hotspot_theme_matrix", []),
            "comparison_matrix": matrices.get("comparison_matrix", []),
            "impact_table": matrices.get("impact_table", []),
            "insight_table": matrices.get("insight_table", []),
        },
    }
    return "\n".join(
        [
            "你是 SectionComposerAgent，负责生成政策研究报告的一个章节。",
            "边界：只能使用下方 JSON 中的材料包、矩阵、claim 和章节契约，不得新增外部事实。",
            "如果材料不足，必须显式写出 MATERIAL_NEEDED，不要用常识补齐。",
            "输出：中文 Markdown，第一行使用一级标题；必须把 contract.output_shape 中每一项逐字渲染为可见标题；最后保留“本节契约检查”。",
            "",
            "```json",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "```",
        ]
    )


def _compose_hotspot(materials: list[dict[str, Any]], claims: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## 热点总述",
        "",
        "本节根据材料包识别可继续展开的政策热点，并说明其升温原因和材料基础。",
        "",
        "## 热点列表",
        "",
    ]
    for package in materials:
        raw = package.get("raw_fields", {})
        rationale_items = package.get("hotspot_rationale_items", [])
        rationale = rationale_items[0] if rationale_items else {}
        lines.extend(
            [
                f"### {package['hotspot']}",
                "",
                f"{package['hotspot']}的核心政策问题是：{_first_value(rationale.get('policy_problem'), raw.get('policy_problem'), 'MATERIAL_NEEDED: 缺少政策问题材料')}",
                "",
                f"热点信号：{_first_value(rationale.get('hotspot_signal'), raw.get('hotspot_name'), package.get('hotspot'))}",
                "",
                "代表性主体：",
                _bullet_list(package.get("actors", [])),
                "",
            ]
        )
    lines.extend(["## 升温原因", ""])
    for package in materials:
        raw = package.get("raw_fields", {})
        rationale_items = package.get("hotspot_rationale_items", [])
        rationale = rationale_items[0] if rationale_items else {}
        lines.extend(
            [
                f"### {package['hotspot']}",
                _bullet_list(
                    [
                        _first_value(rationale.get("repeated_signal"), raw.get("rise_reason")),
                        _first_value(rationale.get("rise_reason"), raw.get("rise_reason")),
                        rationale.get("caution"),
                    ]
                ),
                "",
            ]
        )
    lines.extend(["## 可继续分析的重点热点", ""])
    if claims:
        lines.extend(_bullet_list([claim.get("claim_text") for claim in claims]).splitlines())
    else:
        lines.append("MATERIAL_NEEDED: 缺少可继续分析的重点热点判断。")
    return lines


def _compose_theme(matrices: dict[str, Any]) -> list[str]:
    rows = matrices.get("hotspot_theme_matrix", [])
    lines = [
        "## 归类原则",
        "",
        "本节将热点放回既有主题体系，并保留交叉主题和分类张力；同一热点可以跨越多个主题，不强行写成互斥分类。",
        "",
        "## 热点-主题矩阵",
        "",
        "| 热点 | 主主题 | 交叉主题 |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row.get('hotspot')} | {row.get('main_theme')} | {', '.join(row.get('cross_themes', []))} |")
    if not rows:
        lines.append("| MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED |")
    lines.extend(["", "## 交叉主题说明", ""])
    if rows:
        for row in rows:
            lines.append(f"- {row.get('hotspot')}：{', '.join(row.get('cross_themes', [])) or 'MATERIAL_NEEDED: 缺少交叉主题材料'}")
    else:
        lines.append("- MATERIAL_NEEDED: 缺少交叉主题说明。")
    return lines


def _compose_comparison(matrices: dict[str, Any]) -> list[str]:
    rows = matrices.get("comparison_matrix", [])
    lines = [
        "## 比较总述",
        "",
        "本节按统一维度比较政策前沿，避免逐文件流水账。",
        "",
        "## 维度化比较",
        "",
        "| 热点 | 政策目标 | 对象群体 | 政策工具 | 实施机制 | 风险治理 | 前沿特征 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {hotspot} | {goal} | {target} | {tool} | {mechanism} | {risk} | {frontier} |".format(
                hotspot=row.get("hotspot"),
                goal=_cell(row.get("policy_goal")),
                target=_cell(row.get("target_group")),
                tool=_cell(row.get("policy_tool")),
                mechanism=_cell(row.get("implementation_mechanism")),
                risk=_cell(row.get("risk_governance")),
                frontier=_cell(row.get("frontier_feature")),
            )
        )
    if not rows:
        lines.append("| MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED |")
    lines.extend(["", "## 关键差异解释", ""])
    if rows:
        for row in rows:
            lines.append(
                f"- {row.get('hotspot')}：政策工具侧重{_cell(row.get('policy_tool')) or 'MATERIAL_NEEDED'}，实施机制侧重{_cell(row.get('implementation_mechanism')) or 'MATERIAL_NEEDED'}。"
            )
    else:
        lines.append("- MATERIAL_NEEDED: 缺少可比较材料。")
    lines.extend(["", "## 前沿判断", ""])
    if rows:
        lines.extend(_bullet_list([row.get("frontier_feature") for row in rows]).splitlines())
    else:
        lines.append("- MATERIAL_NEEDED: 缺少前沿特征材料。")
    return lines


def _compose_impact(matrices: dict[str, Any]) -> list[str]:
    rows = matrices.get("impact_table", [])
    lines = ["## 影响总述", "", "本节区分材料明确提出的影响和基于材料的谨慎推导。", ""]
    if not rows:
        return lines + [
            "MATERIAL_NEEDED: 缺少影响研判材料。",
            "",
            "## 分对象影响",
            "",
            "MATERIAL_NEEDED: 缺少分对象影响材料。",
            "",
            "## 风险与不确定性",
            "",
            "MATERIAL_NEEDED: 缺少风险与不确定性材料。",
        ]
    row = rows[0]
    lines.extend(
        [
            "## 分对象影响",
            "",
            f"- 教育治理：{row.get('governance_impact')}",
            f"- 学校实践：{row.get('school_practice_impact')}",
            f"- 教师发展：{row.get('teacher_development_impact')}",
            f"- 学生学习：{row.get('student_learning_impact')}",
            f"- 教育评价：{row.get('education_evaluation_impact')}",
            f"- 平台资源：{row.get('platform_resource_impact')}",
            f"- 伦理安全：{row.get('ethics_safety_impact')}",
            "",
            "## 风险与不确定性",
            "",
            f"- 明示影响：{_cell(row.get('explicit_impacts')) or 'MATERIAL_NEEDED: 缺少明示影响材料'}",
            f"- 谨慎推断：{_cell(row.get('cautious_inferences')) or 'MATERIAL_NEEDED: 缺少谨慎推断材料'}",
            f"- 不确定性：{_cell(row.get('uncertainty')) or 'MATERIAL_NEEDED: 缺少不确定性材料'}",
        ]
    )
    return lines


def _compose_insight(matrices: dict[str, Any], claims: list[dict[str, Any]]) -> list[str]:
    rows = matrices.get("insight_table", [])
    lines = ["本节从热点、比较和影响反推启发建议，不新增材料包外判断。", ""]
    if not rows:
        return lines + ["MATERIAL_NEEDED: 缺少启发建议材料。"]
    row = rows[0]
    lines.extend(
        [
            "## 研究启发",
            "",
            f"{row.get('research_insight')}",
            "",
            "## 治理启发",
            "",
            f"{row.get('governance_insight')}",
            "",
            "## 实践启发",
            "",
            f"{row.get('practice_insight')}",
            "",
            "## 监测启发",
            "",
            f"{row.get('monitoring_insight')}",
            "",
            f"知识库建设启发：{row.get('knowledge_base_insight')}",
            "",
            "对应判断：",
            _bullet_list([claim.get("claim_text") for claim in claims]),
        ]
    )
    return lines
