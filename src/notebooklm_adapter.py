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
    ALLOWED_COMMANDS = {
        ("auth", "check"),
        ("source", "list"),
        ("ask",),
    }

    def __init__(self, mode: str = "mock", cli_path: str | None = None, command_log_path: str | Path | None = None) -> None:
        self.mode = mode
        self.cli_path = cli_path or os.environ.get("NOTEBOOKLM_CLI_PATH") or shutil.which("notebooklm")
        self.command_log_path = Path(command_log_path) if command_log_path else None

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
        result = self._run_cli(cli, ["auth", "check", "--test", "--json"])
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
        result = self._run_cli(cli, ["source", "list", "-n", notebook_id, "--json"])
        parsed = self._parse_cli_result(result)
        sources = parsed.get("sources", []) if isinstance(parsed, dict) else []
        for source in sources:
            if isinstance(source, dict):
                source.setdefault("notebook_id", notebook_id)
        return sources

    def ask(self, job: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "mock":
            return self._mock_query_result(job)
        cli = self._cli()
        if not cli:
            return self._cli_missing_result(job)
        notebook_id = job["notebook_id"]
        prompt = job["prompt"]
        source_args = _source_args(job.get("source_ids", []))
        result = self._run_cli(
            cli,
            ["ask", "-n", notebook_id, "--json", *source_args, prompt],
            timeout=180,
            log_args=["ask", "-n", notebook_id, "--json", *source_args, "<prompt>"],
        )
        parsed = self._parse_cli_result(result)
        structured_answer = self._extract_structured_answer(parsed, job.get("expected_fields", []))
        embedded_answer = structured_answer.get("answer") if isinstance(structured_answer.get("answer"), str) else ""
        embedded_citations = structured_answer.get("citations") if isinstance(structured_answer.get("citations"), list) else []
        citations = _with_notebook_id(
            _normalize_citations(
                embedded_citations
                or parsed.get("citations")
                or parsed.get("references")
                or parsed.get("citation_refs")
            ),
            notebook_id,
        )
        raw_response = embedded_answer or _raw_response_text(parsed)
        evidence_trace = _extract_evidence_trace(raw_response, citations, job)
        source_refs = _merge_source_refs(_source_refs_from_citations(citations), _source_refs_from_job(job))
        parsed.update(
            {
                "job_id": job["id"],
                "query_type": job["query_type"],
                "section": job["section"],
                "deep_dive_lane": job.get("deep_dive_lane"),
                "source_ids": job.get("source_ids", []),
                "source_title": job.get("source_title", ""),
                "seed_trace_id": job.get("seed_trace_id"),
                "seed_text": job.get("seed_text", ""),
                "expected_fields": job.get("expected_fields", []),
                "verdict": "PASS" if parsed.get("status") == "PASS" else "ERROR",
                "raw_response": raw_response,
                "citations": citations,
                "citation_refs": citations,
                "source_refs": source_refs,
                "evidence_trace": evidence_trace,
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
        result = self._run_cli(
            cli,
            ["ask", "-n", notebook_id, "--prompt-file", prompt_path, "--json"],
            timeout=180,
            log_args=["ask", "-n", notebook_id, "--prompt-file", prompt_path, "--json"],
        )
        return self._parse_cli_result(result)

    def _run_cli(
        self,
        cli: str,
        args: list[str],
        timeout: int | None = None,
        log_args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command_key = tuple(args[:2]) if args[:2] in (["auth", "check"], ["source", "list"]) else tuple(args[:1])
        if command_key not in self.ALLOWED_COMMANDS:
            raise RuntimeError(f"NotebookLM command is not allowed by capability policy: {' '.join(args)}")
        started_at = utc_timestamp()
        result = subprocess.run(
            [cli, *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        self._append_command_log(
            {
                "started_at": started_at,
                "finished_at": utc_timestamp(),
                "mode": self.mode,
                "cli": cli,
                "args": log_args or args,
                "returncode": result.returncode,
                "stdout_bytes": len(result.stdout.encode("utf-8")),
                "stderr_bytes": len(result.stderr.encode("utf-8")),
            }
        )
        return result

    def _append_command_log(self, event: dict[str, Any]) -> None:
        if not self.command_log_path:
            return
        self.command_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.command_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

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
        source_id = _first_source_id(job.get("source_ids", [])) or "mock-source-1"
        source_title = job.get("source_title") or "Mock AI education policy source"
        citations = _with_notebook_id([
            {
                "id": 1,
                "source_id": source_id,
                "title": source_title,
            }
        ], job["notebook_id"])
        raw_answer = f"Mock answer for {job['query_type']} with fields: {', '.join(job.get('expected_fields', []))} [1]"
        source_refs = _merge_source_refs(_source_refs_from_citations(citations), _source_refs_from_job(job))
        return {
            "status": "PASS",
            "verdict": "PASS",
            "reason_code": "mock_result",
            "job_id": job["id"],
            "query_type": job["query_type"],
            "section": job["section"],
            "deep_dive_lane": job.get("deep_dive_lane"),
            "source_ids": job.get("source_ids", []),
            "source_title": job.get("source_title", ""),
            "seed_trace_id": job.get("seed_trace_id"),
            "seed_text": job.get("seed_text", ""),
            "notebook_id": job["notebook_id"],
            "expected_fields": job.get("expected_fields", []),
            "structured_answer": structured,
            "parsed_fields": structured,
            "answer": raw_answer,
            "raw_answer": raw_answer,
            "raw_response": raw_answer,
            "citations": citations,
            "citation_refs": citations,
            "source_refs": source_refs,
            "evidence_trace": _extract_evidence_trace(raw_answer, citations, job),
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
            "hotspot_signal": "多份材料把 AI 素养、生成式 AI 应用和风险治理作为同一组政策问题反复提出。",
            "repeated_signal": "能力建设、教师支持、学校规则和伦理安全在材料中重复出现。",
            "support_level": "medium",
            "caution": "mock 材料只验证流程，不代表真实 NotebookLM 知识库结论。",
            "answer": "AI 素养热点的形成来自能力建设和风险治理的共同上升。[1]",
            "main_theme": "AI 素养与数字素养",
            "sub_theme": "生成式 AI 使用能力",
            "cross_themes": ["教师发展", "课程教学", "数据治理"],
            "classification_reason": "该热点同时涉及学习者能力、教师培训和技术使用规范。",
            "classification_tension": "部分材料把它作为数字教育基础能力，部分材料把它作为 AI 治理前置条件。",
            "policy_points": ["建立面向师生的 AI 素养框架", "将生成式 AI 风险治理纳入学校规则"],
            "policy_tools": ["能力框架", "教师培训", "使用指南", "评估指标"],
            "actors": ["政府部门", "学校", "教师培训机构", "平台企业"],
            "target_groups": ["学生", "教师", "学校管理者"],
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
            "source_specific_findings": ["限定 source 中把 AI 素养与教师发展、学校规则和风险治理连接起来。"],
            "policy_goal": "提升师生负责任使用 AI 的能力",
            "target_group": "学生、教师、学校管理者",
            "governance_actor": "教育主管部门与学校共同治理",
            "policy_tool": "指南、课程、培训与评价指标",
            "implementation_mechanism": "将 AI 素养要求嵌入课程与教师专业发展体系",
            "evaluation_mechanism": "通过能力指标和学校实践反馈持续评估",
            "risk_governance": "强调隐私、安全、公平和学术诚信",
            "frontier_feature": "从技术部署转向能力建设与风险治理并重",
            "comparable_unit": "AI 素养政策工具组合",
            "explicit_impacts": ["学校需要建立生成式 AI 使用边界", "教师培训内容需要扩展到风险治理"],
            "cautious_inferences": ["AI 素养可能成为课程、教师发展和治理规则之间的连接性议题"],
            "governance_impact": "推动教育治理从设备和平台供给转向能力、规则和责任体系建设。",
            "school_practice_impact": "学校需要建立 AI 使用边界、课程整合和风险处置流程。",
            "teacher_development_impact": "教师培训需要覆盖工具使用、教学设计、伦理风险和评价方法。",
            "student_learning_impact": "学生学习活动更强调批判性使用、协作创造和结果反思。",
            "education_evaluation_impact": "评价体系需要纳入 AI 辅助学习过程和能力表现。",
            "platform_resource_impact": "平台资源建设需要兼顾可用性、透明度和数据治理。",
            "ethics_safety_impact": "伦理安全成为 AI 教育政策从试点走向规模化的重要前置条件。",
            "uncertainty": "真实影响强度需要在 live NotebookLM 检索材料中进一步区分明示证据和推断。",
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
            "deep_dive_lane": job.get("deep_dive_lane"),
            "source_ids": job.get("source_ids", []),
            "source_title": job.get("source_title", ""),
            "seed_trace_id": job.get("seed_trace_id"),
            "seed_text": job.get("seed_text", ""),
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


def _source_args(source_ids: Any) -> list[str]:
    if not isinstance(source_ids, list):
        return []
    args: list[str] = []
    for source_id in source_ids:
        if not source_id:
            continue
        args.extend(["-s", str(source_id)])
    return args


def _first_source_id(source_ids: Any) -> str:
    if not isinstance(source_ids, list):
        return ""
    for source_id in source_ids:
        if source_id:
            return str(source_id)
    return ""


def _normalize_citations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        citation_id = item.get("id", item.get("citation_id", item.get("ref_id", item.get("citation_number"))))
        title = item.get("title") or item.get("source_title") or item.get("name") or ""
        source_id = item.get("source_id") or item.get("sourceId") or item.get("source") or item.get("document_id")
        normalized.append(
            {
                "id": citation_id,
                "title": title,
                "source_id": source_id,
            }
        )
    return normalized


def _with_notebook_id(refs: list[dict[str, Any]], notebook_id: str) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for ref in refs:
        item = dict(ref)
        item.setdefault("notebook_id", notebook_id)
        enriched.append(item)
    return enriched


def _source_refs_from_citations(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for citation in citations:
        title = str(citation.get("title") or "")
        source_id = str(citation.get("source_id") or title or citation.get("id") or "")
        notebook_id = str(citation.get("notebook_id") or "")
        key = (notebook_id, source_id, title)
        if not source_id and not title:
            continue
        if key in seen:
            continue
        seen.add(key)
        refs.append(
            {
                "notebook_id": notebook_id,
                "source_id": source_id,
                "title": title,
                "citation_ids": [citation.get("id")] if citation.get("id") is not None else [],
            }
        )
    return refs


def _source_refs_from_job(job: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    source_title = str(job.get("source_title") or "")
    notebook_id = str(job.get("notebook_id") or "")
    source_ids = job.get("source_ids", [])
    if not isinstance(source_ids, list):
        return refs
    for source_id in source_ids:
        if not source_id and not source_title:
            continue
        refs.append(
            {
                "notebook_id": notebook_id,
                "source_id": str(source_id or source_title),
                "title": source_title,
                "citation_ids": [],
            }
        )
    return refs


def _merge_source_refs(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for group in groups:
        for ref in group:
            notebook_id = str(ref.get("notebook_id") or "")
            source_id = str(ref.get("source_id") or "")
            title = str(ref.get("title") or "")
            key = (notebook_id, source_id, title)
            if key in seen:
                continue
            seen.add(key)
            refs.append(ref)
    return refs


def _extract_evidence_trace(answer: str, citations: list[dict[str, Any]], job: dict[str, Any]) -> list[dict[str, Any]]:
    if not answer or not citations:
        return []
    citation_by_id = {str(citation.get("id")): citation for citation in citations if citation.get("id") is not None}
    trace: list[dict[str, Any]] = []
    for index, sentence in enumerate(_split_cited_sentences(answer), start=1):
        citation_ids = _unique(re.findall(r"\[(\d+)\]", sentence))
        if not citation_ids:
            continue
        sentence_citations = [citation_by_id.get(citation_id, {"id": citation_id, "title": "", "source_id": None}) for citation_id in citation_ids]
        trace.append(
            {
                "trace_id": f"{job.get('id', 'query')}_evidence_{index}",
                "job_id": job.get("id"),
                "notebook_id": job.get("notebook_id"),
                "query_type": job.get("query_type"),
                "section": job.get("section"),
                "text": re.sub(r"\s*\[\d+\]", "", sentence).strip(),
                "citation_ids": citation_ids,
                "source_refs": _source_refs_from_citations(sentence_citations),
                "citation_refs": sentence_citations,
            }
        )
    return trace


def _split_cited_sentences(answer: str) -> list[str]:
    chunks: list[str] = []
    for line in answer.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        normalized = re.sub(
            r"([。！？!?])((?:\s*\[\d+\])+)",
            lambda match: f"{match.group(2).strip()}{match.group(1)}",
            stripped,
        )
        parts = [part.strip() for part in re.split(r"(?<=[。！？!?])\s*", normalized) if part.strip()]
        chunks.extend(parts or [normalized])
    return chunks


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
