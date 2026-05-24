from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from io_utils import utc_timestamp


class NotebookLMAdapter:
    def __init__(self, mode: str = "mock", cli_path: str | None = None) -> None:
        self.mode = mode
        self.cli_path = cli_path or os.environ.get("NOTEBOOKLM_CLI_PATH") or shutil.which("notebooklm")

    def _cli(self) -> str | None:
        if self.cli_path and Path(self.cli_path).exists():
            return self.cli_path
        return shutil.which("notebooklm")

    def check_auth(self) -> dict[str, Any]:
        if self.mode == "mock":
            return {"status": "PASS", "mode": "mock", "summary": "Mock mode does not require NotebookLM auth."}
        cli = self._cli()
        if not cli:
            return {"status": "ERROR", "mode": "real", "summary": "notebooklm CLI was not found on PATH."}
        result = subprocess.run(
            [cli, "auth", "check", "--test", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        return self._parse_cli_result(result)

    def list_sources(self, notebook_id: str) -> list[dict[str, Any]]:
        if self.mode == "mock":
            return [
                {
                    "source_id": "mock-source-1",
                    "title": "Mock AI education policy source",
                    "notebook_id": notebook_id,
                }
            ]
        cli = self._cli()
        if not cli:
            return []
        result = subprocess.run(
            [cli, "source", "list", "-n", notebook_id, "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        parsed = self._parse_cli_result(result)
        return parsed.get("sources", []) if isinstance(parsed, dict) else []

    def ask(self, job: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "mock":
            return self._mock_query_result(job)
        cli = self._cli()
        if not cli:
            return self._cli_missing_result(job)
        notebook_id = job["notebook_id"]
        prompt = job["prompt"]
        result = subprocess.run(
            [cli, "ask", "-n", notebook_id, "--json", prompt],
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
        )
        parsed = self._parse_cli_result(result)
        structured_answer = self._extract_structured_answer(parsed, job.get("expected_fields", []))
        parsed.update(
            {
                "job_id": job["id"],
                "query_type": job["query_type"],
                "section": job["section"],
                "expected_fields": job.get("expected_fields", []),
                "verdict": "PASS" if parsed.get("status") == "PASS" else "ERROR",
                "raw_response": _raw_response_text(parsed),
                "structured_answer": structured_answer,
                "parsed_fields": structured_answer,
                "generated_at": utc_timestamp(),
            }
        )
        return parsed

    def ask_with_prompt_file(self, notebook_id: str, prompt_path: str) -> dict[str, Any]:
        if self.mode == "mock":
            return {
                "status": "PASS",
                "notebook_id": notebook_id,
                "prompt_path": prompt_path,
                "raw_answer": "Mock prompt-file answer.",
                "generated_at": utc_timestamp(),
            }
        cli = self._cli()
        if not cli:
            return {
                "status": "ERROR",
                "verdict": "ERROR",
                "reason_code": "notebooklm_cli_missing",
                "notebook_id": notebook_id,
                "prompt_path": prompt_path,
                "raw_response": "",
                "parsed_fields": {},
                "summary": "notebooklm CLI was not found on PATH.",
                "generated_at": utc_timestamp(),
            }
        result = subprocess.run(
            [cli, "ask", "-n", notebook_id, "--prompt-file", prompt_path, "--json"],
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
        )
        return self._parse_cli_result(result)

    def _parse_cli_result(self, result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        if result.returncode != 0:
            return {
                "status": "ERROR",
                "reason_code": "cli_error",
                "summary": result.stderr.strip() or result.stdout.strip(),
                "raw_stdout": result.stdout,
                "raw_stderr": result.stderr,
            }
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed = {"raw_answer": result.stdout}
        if isinstance(parsed, dict):
            parsed.setdefault("status", "PASS")
            if result.stderr.strip():
                parsed["raw_stderr"] = result.stderr
            return parsed
        payload = {"status": "PASS", "raw_answer": parsed}
        if result.stderr.strip():
            payload["raw_stderr"] = result.stderr
        return payload

    def _extract_structured_answer(self, parsed: dict[str, Any], expected_fields: list[str]) -> dict[str, Any]:
        if isinstance(parsed.get("structured_answer"), dict):
            return parsed["structured_answer"]
        answer = parsed.get("answer") or parsed.get("raw_answer") or ""
        if not isinstance(answer, str):
            return {}
        candidates = [answer.strip()]
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", answer, flags=re.DOTALL)
        candidates.extend(candidate.strip() for candidate in fenced)
        brace_match = re.search(r"\{.*\}", answer, flags=re.DOTALL)
        if brace_match:
            candidates.append(brace_match.group(0))
        for candidate in candidates:
            try:
                decoded = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(decoded, dict):
                return decoded
        return {"answer": answer} if answer and not expected_fields else {}

    def _mock_query_result(self, job: dict[str, Any]) -> dict[str, Any]:
        structured = {field: self._mock_value(job["query_type"], field) for field in job.get("expected_fields", [])}
        return {
            "status": "PASS",
            "verdict": "PASS",
            "reason_code": "mock_result",
            "job_id": job["id"],
            "query_type": job["query_type"],
            "section": job["section"],
            "notebook_id": job["notebook_id"],
            "expected_fields": job.get("expected_fields", []),
            "structured_answer": structured,
            "parsed_fields": structured,
            "raw_answer": f"Mock answer for {job['query_type']} with fields: {', '.join(job.get('expected_fields', []))}",
            "raw_response": f"Mock answer for {job['query_type']} with fields: {', '.join(job.get('expected_fields', []))}",
            "generated_at": utc_timestamp(),
        }

    def _mock_value(self, query_type: str, field: str) -> Any:
        samples: dict[str, Any] = {
            "hotspot_name": "AI 素养",
            "keywords": ["AI literacy", "数字素养", "生成式 AI"],
            "policy_problem": "AI 快速进入教育场景后，学生、教师和学校需要形成可操作的能力框架。",
            "involved_themes": ["AI 素养与数字素养", "教师 AI 能力与专业发展"],
            "rise_reason": "多类政策材料同时关注生成式 AI 应用、风险治理和能力建设。",
            "representative_actors": ["国际组织", "教育主管部门", "研究机构"],
            "material_support_level": "medium",
            "main_theme": "AI 素养与数字素养",
            "sub_theme": "生成式 AI 使用能力",
            "cross_themes": ["教师发展", "课程教学", "数据治理"],
            "classification_reason": "该热点同时涉及学习者能力、教师培训和技术使用规范。",
            "classification_tension": "部分材料把它作为数字教育基础能力，部分材料把它作为 AI 治理前置条件。",
            "policy_points": ["建立面向师生的 AI 素养框架", "将生成式 AI 风险治理纳入学校规则"],
            "policy_tools": ["能力框架", "教师培训", "使用指南", "评估指标"],
            "actors": ["政府部门", "学校", "教师培训机构", "平台企业"],
            "mechanisms": ["课程嵌入", "专业发展", "风险提示", "持续评估"],
            "risks": ["数据隐私", "算法偏见", "学术诚信", "数字鸿沟"],
            "claim_candidates": [
                {
                    "claim": "AI 素养正在从工具使用能力扩展为覆盖治理、伦理和学习方式变革的综合能力。",
                    "support_level": "medium",
                    "allowed_sections": ["hotspot", "comparison", "insight"],
                    "caution": "当前为 mock 材料，真实写作需以 NotebookLM 回答确认。"
                }
            ],
            "missing_questions": [],
            "policy_goal": "提升师生负责任使用 AI 的能力",
            "target_group": "学生、教师、学校管理者",
            "governance_actor": "教育主管部门与学校共同治理",
            "policy_tool": "指南、课程、培训与评价指标",
            "implementation_mechanism": "将 AI 素养要求嵌入课程与教师专业发展体系",
            "evaluation_mechanism": "通过能力指标和学校实践反馈持续评估",
            "risk_governance": "强调隐私、安全、公平和学术诚信",
            "frontier_feature": "从技术部署转向能力建设与风险治理并重",
            "governance_impact": "推动教育治理从设备和平台供给转向能力、规则和责任体系建设。",
            "school_practice_impact": "学校需要建立 AI 使用边界、课程整合和风险处置流程。",
            "teacher_development_impact": "教师培训需要覆盖工具使用、教学设计、伦理风险和评价方法。",
            "student_learning_impact": "学生学习活动更强调批判性使用、协作创造和结果反思。",
            "education_evaluation_impact": "评价体系需要纳入 AI 辅助学习过程和能力表现。",
            "platform_resource_impact": "平台资源建设需要兼顾可用性、透明度和数据治理。",
            "ethics_safety_impact": "伦理安全成为 AI 教育政策从试点走向规模化的重要前置条件。",
            "research_insight": "后续研究可跟踪 AI 素养框架如何落地到课程、评价和教师发展。",
            "governance_insight": "治理上应把能力建设与风险规则同步设计。",
            "practice_insight": "学校实践应从单点工具培训转向场景化使用规范。",
            "monitoring_insight": "持续监测热点材料中的新概念、政策工具和评价机制。",
            "knowledge_base_insight": "知识库应保留主题标签、对象群体、政策工具和风险维度。",
        }
        return samples.get(field, f"{query_type}:{field}")

    def _cli_missing_result(self, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "ERROR",
            "verdict": "ERROR",
            "reason_code": "notebooklm_cli_missing",
            "job_id": job["id"],
            "query_type": job["query_type"],
            "section": job["section"],
            "notebook_id": job["notebook_id"],
            "expected_fields": job.get("expected_fields", []),
            "structured_answer": {},
            "parsed_fields": {},
            "raw_answer": "",
            "raw_response": "",
            "summary": "notebooklm CLI was not found on PATH.",
            "generated_at": utc_timestamp(),
        }


def _raw_response_text(parsed: dict[str, Any]) -> str:
    for key in ("answer", "raw_answer", "summary", "raw_stdout"):
        value = parsed.get(key)
        if isinstance(value, str) and value:
            return value
    return ""
