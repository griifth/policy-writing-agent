from __future__ import annotations

from pathlib import Path
from typing import Any


SECTION_TO_QUERY = {
    "hotspot": ("global_scan", "01_hotspot_scan.md", "hotspot_candidates.json"),
    "theme": ("theme_scan", "02_theme_mapping.md", "theme_hotspot_matrix.json"),
    "comparison": ("comparison", "04_comparison_matrix.md", "comparison_matrix.json"),
    "impact": ("impact", "05_impact_analysis.md", "impact_table.json"),
    "insight": ("insight", "06_insight_generation.md", "insight_table.json"),
}


QUERY_SCHEMA_NAMES = {
    "global_scan": "hotspot",
    "theme_scan": "theme_mapping",
    "deep_dive": "deep_dive",
    "comparison": "comparison",
    "impact": "impact",
    "insight": "insight",
}


QUERY_FIELDS = {
    "global_scan": [
        "hotspot_name",
        "keywords",
        "policy_problem",
        "involved_themes",
        "rise_reason",
        "representative_actors",
        "material_support_level",
    ],
    "theme_scan": [
        "main_theme",
        "sub_theme",
        "cross_themes",
        "classification_reason",
        "classification_tension",
    ],
    "deep_dive": [
        "policy_points",
        "policy_tools",
        "actors",
        "mechanisms",
        "risks",
        "claim_candidates",
        "missing_questions",
    ],
    "comparison": [
        "policy_goal",
        "target_group",
        "governance_actor",
        "policy_tool",
        "implementation_mechanism",
        "evaluation_mechanism",
        "risk_governance",
        "frontier_feature",
    ],
    "impact": [
        "governance_impact",
        "school_practice_impact",
        "teacher_development_impact",
        "student_learning_impact",
        "education_evaluation_impact",
        "platform_resource_impact",
        "ethics_safety_impact",
    ],
    "insight": [
        "research_insight",
        "governance_insight",
        "practice_insight",
        "monitoring_insight",
        "knowledge_base_insight",
    ],
}


def _prompt_text(
    topic: str,
    query_type: str,
    expected_fields: list[str],
    prompt_file: str | None,
    dimensions: dict[str, Any],
) -> str:
    base_prompt = _load_prompt_file(prompt_file)
    output_contract = _output_contract(query_type, expected_fields)
    theme_taxonomy = _theme_taxonomy(dimensions)
    return (
        f"任务主题：“{topic}”。\n"
        f"查询类型：{query_type}。\n\n"
        f"{base_prompt}\n\n"
        f"{theme_taxonomy}\n"
        "输出契约：\n"
        "请严格只返回一个 JSON object，不要 Markdown 代码块，不要额外解释。\n"
        "JSON object 必须包含以下字段；字段值可以是字符串、字符串数组或对象数组：\n"
        f"{output_contract}\n"
        "不要直接生成完整报告。"
    )


def _load_prompt_file(prompt_file: str | None) -> str:
    if not prompt_file:
        return "请补充缺失材料。"
    path = Path(prompt_file)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    if not path.exists():
        return f"请执行 {prompt_file} 对应的结构化检索任务。"
    return path.read_text(encoding="utf-8").strip()


def _output_contract(query_type: str, expected_fields: list[str]) -> str:
    fields = ",\n".join(f'  "{field}": ""' for field in expected_fields)
    schema_name = QUERY_SCHEMA_NAMES.get(query_type, query_type)
    return "{\n" f'  "_schema": "{schema_name}",\n' f"{fields}\n" "}"


def _theme_taxonomy(dimensions: dict[str, Any]) -> str:
    schema_names = [name for name in dimensions if name != "material_package"]
    if not schema_names:
        return "主题体系：按知识库材料中的政策主题归类。"
    return "可用结构化 schema：" + "、".join(schema_names) + "。"


def build_query_jobs(
    task_spec: dict[str, Any],
    dimensions: dict[str, Any],
    section_contracts: dict[str, Any],
    run_dir: str | Path = "runs/latest",
    missing_questions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    topic = task_spec["topic"]
    notebook_id = task_spec["notebook_id"]
    sections = task_spec.get("sections", ["hotspot", "theme", "comparison", "impact", "insight"])
    run_dir = Path(run_dir)
    ordered_specs: list[tuple[str, str, str]] = []
    if "hotspot" in sections:
        ordered_specs.append(("hotspot", "global_scan", "01_hotspot_scan.md"))
    if "theme" in sections:
        ordered_specs.append(("theme", "theme_scan", "02_theme_mapping.md"))
    if "hotspot" in sections:
        ordered_specs.append(("hotspot", "deep_dive", "03_hotspot_deep_dive.md"))
    if "comparison" in sections:
        ordered_specs.append(("comparison", "comparison", "04_comparison_matrix.md"))
    if "impact" in sections:
        ordered_specs.append(("impact", "impact", "05_impact_analysis.md"))
    if "insight" in sections:
        ordered_specs.append(("insight", "insight", "06_insight_generation.md"))

    jobs: list[dict[str, Any]] = []
    for index, (section, query_type, prompt_file) in enumerate(ordered_specs, start=1):
        expected_fields = QUERY_FIELDS[query_type]
        schema_name = QUERY_SCHEMA_NAMES[query_type]
        prompt_path = str(Path("prompts") / prompt_file)
        job_id = f"{index:02d}_{query_type}"
        jobs.append(
            {
                "id": job_id,
                "section": section,
                "query_type": query_type,
                "schema_name": schema_name,
                "notebook_id": notebook_id,
                "prompt_file": prompt_path,
                "prompt": _prompt_text(topic, query_type, expected_fields, prompt_path, dimensions),
                "expected_fields": expected_fields,
                "output_contract": {
                    "type": "json_object",
                    "schema_name": schema_name,
                    "required_fields": expected_fields,
                },
                "output_target": str(run_dir / "query_results" / f"{job_id}.json"),
            }
        )

    for question in missing_questions or []:
        followup_id = f"{len(jobs) + 1:02d}_followup_{question.get('field', 'material')}"
        expected_fields = question.get("expected_fields", [])
        jobs.append(
            {
                "id": followup_id,
                "section": question.get("section", "unknown"),
                "query_type": "followup",
                "schema_name": question.get("schema_name", "followup"),
                "notebook_id": notebook_id,
                "prompt_file": None,
                "prompt": question.get("question", "请补充缺失材料。"),
                "expected_fields": expected_fields,
                "output_contract": {
                    "type": "json_object",
                    "schema_name": question.get("schema_name", "followup"),
                    "required_fields": expected_fields,
                },
                "output_target": str(run_dir / "query_results" / f"{followup_id}.json"),
            }
        )

    return jobs
