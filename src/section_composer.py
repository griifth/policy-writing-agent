from __future__ import annotations

from typing import Any


def _bullet_list(values: list[Any]) -> str:
    cleaned = [str(value) for value in values if value]
    if not cleaned:
        return "- MATERIAL_NEEDED: 缺少可写材料"
    return "\n".join(f"- {value}" for value in cleaned)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "、".join(str(item) for item in value if item)
    if isinstance(value, dict):
        return "；".join(f"{key}: {val}" for key, val in value.items() if val)
    return str(value)


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
    return "\n".join(lines) + "\n"


def _compose_hotspot(materials: list[dict[str, Any]], claims: list[dict[str, Any]]) -> list[str]:
    lines = ["本节根据材料包识别可继续展开的政策热点，并说明其升温原因。", ""]
    for package in materials:
        raw = package.get("raw_fields", {})
        lines.extend(
            [
                f"## {package['hotspot']}",
                "",
                f"{package['hotspot']}的核心政策问题是：{raw.get('policy_problem', 'MATERIAL_NEEDED: 缺少政策问题材料')}",
                "",
                "升温原因：",
                _bullet_list([raw.get("rise_reason")]),
                "",
                "代表性主体：",
                _bullet_list(package.get("actors", [])),
                "",
            ]
        )
    if claims:
        lines.extend(["可写判断：", _bullet_list([claim.get("claim_text") for claim in claims])])
    return lines


def _compose_theme(matrices: dict[str, Any]) -> list[str]:
    rows = matrices.get("hotspot_theme_matrix", [])
    lines = ["本节将热点放回既有主题体系，并保留交叉主题和分类张力。", "", "| 热点 | 主主题 | 交叉主题 |", "|---|---|---|"]
    for row in rows:
        lines.append(f"| {row.get('hotspot')} | {row.get('main_theme')} | {', '.join(row.get('cross_themes', []))} |")
    if not rows:
        lines.append("| MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED |")
    return lines


def _compose_comparison(matrices: dict[str, Any]) -> list[str]:
    rows = matrices.get("comparison_matrix", [])
    lines = [
        "本节按统一维度比较政策前沿，避免逐文件流水账。",
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
    return lines


def _compose_impact(matrices: dict[str, Any]) -> list[str]:
    rows = matrices.get("impact_table", [])
    lines = ["本节区分材料明确提出的影响和基于材料的谨慎推导。", ""]
    if not rows:
        return lines + ["MATERIAL_NEEDED: 缺少影响研判材料。"]
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
            f"- 研究启发：{row.get('research_insight')}",
            f"- 治理启发：{row.get('governance_insight')}",
            f"- 实践启发：{row.get('practice_insight')}",
            f"- 监测启发：{row.get('monitoring_insight')}",
            f"- 知识库建设启发：{row.get('knowledge_base_insight')}",
            "",
            "对应判断：",
            _bullet_list([claim.get("claim_text") for claim in claims]),
        ]
    )
    return lines
