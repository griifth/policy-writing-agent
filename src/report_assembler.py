from __future__ import annotations

import re
from typing import Any

from text_cleaning import strip_citation_markers


def assemble_report(
    task_spec: dict[str, Any],
    section_drafts: dict[str, str],
    review_reports: list[dict[str, Any]],
    material_packages: list[dict[str, Any]] | None = None,
    matrices: dict[str, Any] | None = None,
    abstract_text: str | None = None,
) -> str:
    title = task_spec.get("topic", "政策热点研判报告")
    lines = [
        f"# {title}",
        "",
        "## 摘要",
        "",
        strip_citation_markers(abstract_text).strip() if abstract_text else _build_abstract(title, section_drafts),
        "",
    ]
    for section_id in ["hotspot", "theme", "comparison", "impact", "insight"]:
        draft = section_drafts.get(section_id)
        if draft:
            lines.append(strip_citation_markers(_strip_contract_check(draft)).strip())
            lines.append("")

    material_packages = material_packages or []
    matrices = matrices or {}

    lines.extend(["# 附录一：材料包索引", "", "| Package | Hotspot | Main Theme | Sections | Sources | Citations |", "|---|---|---|---|---|---|"])
    for package in material_packages:
        lines.append(
            f"| {package.get('package_id')} | {strip_citation_markers(package.get('hotspot'))} | {strip_citation_markers(package.get('main_theme'))} | {', '.join(package.get('section_targets', []))} | {len(package.get('source_refs', []))} | {len(package.get('citation_refs', []))} |"
        )
    if not material_packages:
        lines.append("| MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED |")

    lines.extend(["", "# 附录二：缺口问题", ""])
    gaps = [question for package in material_packages for question in package.get("missing_questions", [])]
    if gaps:
        for gap in gaps:
            lines.append(f"- {strip_citation_markers(gap.get('question', gap))}")
    else:
        lines.append("- 当前材料包未记录阻断性缺口。")

    lines.extend(["", "# 附录三：关键判断表", "", "| Claim | Support | Sections | Sources | Caution |", "|---|---|---|---|---|"])
    for claim in matrices.get("policy_claim_material_matrix", []):
        lines.append(
            f"| {strip_citation_markers(claim.get('claim_text'))} | {claim.get('support_level')} | {', '.join(claim.get('allowed_sections', []))} | {_source_labels(claim.get('source_refs', []))} | {strip_citation_markers(claim.get('caution_note', ''))} |"
        )
    if not matrices.get("policy_claim_material_matrix"):
        lines.append("| MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED | MATERIAL_NEEDED |")

    lines.extend(["", "# 附录四：审查状态", "", "| Reviewer | Verdict | Reason |", "|---|---|---|"])
    for report in review_reports:
        lines.append(f"| {report.get('reviewer')} | {report.get('verdict')} | {report.get('reason_code')} |")
    lines.append("")
    return strip_citation_markers("\n".join(lines))


def build_abstract_prompt(task_spec: dict[str, Any], section_drafts: dict[str, str]) -> str:
    title = task_spec.get("topic", "政策热点研判报告")
    body = _abstract_source_body(section_drafts)
    return "\n".join(
        [
            "你是 AbstractComposerAgent，负责在报告正文完成后生成正式摘要。",
            "边界：只能使用下方已生成的报告正文，不得新增外部事实，不得描述写作 Agent、NotebookLM、材料包、矩阵、章节契约或工作流。",
            "写作要求：输出一段中文摘要，180-260字；概括研究对象、核心发现、主要比较维度、影响判断和关键建议；语言像正式政策研究报告。",
            "如果正文中存在 MATERIAL_NEEDED，只能概括为“仍需补充证据/机制细节”，不要保留 MATERIAL_NEEDED 字样。",
            "不要输出标题、列表、Markdown、引用编号或来源编号。",
            "",
            f"报告题目：{strip_citation_markers(title)}",
            "",
            "报告正文：",
            body,
        ]
    )


def _abstract_source_body(section_drafts: dict[str, str], max_chars: int = 45000) -> str:
    parts = []
    for section_id in ["hotspot", "theme", "comparison", "impact", "insight"]:
        draft = section_drafts.get(section_id, "")
        cleaned = strip_citation_markers(_strip_contract_check(draft)).strip()
        if cleaned:
            parts.append(cleaned)
    body = "\n\n".join(parts)
    body = body.replace("MATERIAL_NEEDED", "证据缺口")
    if len(body) <= max_chars:
        return body
    return body[: max_chars - 20].rstrip() + "\n...[truncated]"


def _build_abstract(title: str, section_drafts: dict[str, str]) -> str:
    snippets = [
        _first_content_sentence(section_drafts.get("hotspot", "")),
        _first_content_sentence(section_drafts.get("theme", "")),
        _first_content_sentence(section_drafts.get("comparison", "")),
        _first_content_sentence(section_drafts.get("impact", "")),
        _first_content_sentence(section_drafts.get("insight", "")),
    ]
    snippets = [snippet for snippet in snippets if snippet]
    if not snippets:
        return f"本报告围绕“{strip_citation_markers(title)}”展开分析；当前章节正文不足，摘要需在正文补齐后生成。"
    body = " ".join(snippets[:5])
    return f"本报告围绕“{strip_citation_markers(title)}”展开分析。{body}"


def _first_content_sentence(markdown: str) -> str:
    text = _strip_contract_check(markdown)
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", "|", "-", ">", "```")) or set(line) <= {"-", "|", " "}:
            continue
        if "本节契约检查" in line:
            continue
        line = _clean_content_line(line)
        if _looks_like_label(line):
            continue
        sentence = _first_sentence(line)
        if sentence:
            return sentence
    return ""


def _looks_like_label(line: str) -> bool:
    stripped = line.strip("*：: ")
    if not stripped:
        return True
    label_prefixes = ("维度", "热点", "研究启发", "治理启发", "实践启发", "监测启发", "共性", "差异", "注意")
    if stripped.startswith(label_prefixes) and len(stripped) <= 28:
        return True
    if line.startswith("**") and line.endswith("**") and len(stripped) <= 40:
        return True
    return False


def _clean_content_line(line: str) -> str:
    line = line.lstrip("-*0123456789.、) ")
    line = line.split("MATERIAL_NEEDED", 1)[0]
    line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
    line = re.sub(r"`([^`]+)`", r"\1", line)
    return line.strip(" ：:")


def _first_sentence(text: str) -> str:
    cleaned = strip_citation_markers(text)
    if cleaned.endswith(("：", ":")):
        return ""
    for separator in ["。", "！", "？"]:
        index = cleaned.find(separator)
        if 0 <= index < 180:
            return cleaned[: index + 1]
    return ""


def _strip_contract_check(draft: str) -> str:
    marker = "\n## 本节契约检查"
    if marker not in draft:
        return draft
    return draft.split(marker, 1)[0]


def _source_labels(source_refs: Any) -> str:
    if not isinstance(source_refs, list):
        return ""
    labels = []
    for ref in source_refs:
        if not isinstance(ref, dict):
            continue
        title = str(ref.get("title") or "")
        source_id = str(ref.get("source_id") or "")
        notebook_id = str(ref.get("notebook_id") or "")
        if title and notebook_id and source_id:
            labels.append(f"{title} ({notebook_id}/{source_id})")
        elif title:
            labels.append(title)
        elif notebook_id and source_id:
            labels.append(f"{notebook_id}/{source_id}")
        else:
            labels.append(source_id)
    return "；".join(label for label in labels if label)
