"""战略应对型政策文章工作流入口。

本脚本服务于通用文章类型：目标国家战略分析 + 中国应对策略建议。
测试主题可以是“中美AI人才竞争及应对策略”，但流程不能写死该主题。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
from llm_client import create_llm_client
from notebooklm_client import NotebookLMClient


TASKS = [
    ("init", "初始化运行目录", "编排"),
    ("resolve_notebook", "解析 NotebookLM 知识库", "编排"),
    ("build_retrieval_prompts", "拼装检索提示词", "拼装"),
    ("retrieve_materials", "NotebookLM 检索材料", "检索"),
    ("redefine_task", "重定义写作任务", "判断"),
    ("assign_material_roles", "分配材料论证角色", "判断"),
    ("map_pressure_judgment", "映射压力与判断", "判断"),
    ("plan_article", "构思论证链和文章结构", "构思"),
    ("build_suggestion_pool", "生成候选建议池", "构思"),
    ("prioritize_policy_options", "排序政策优先序", "构思"),
    ("write_draft", "写作初稿", "写作"),
    ("review_draft", "审查初稿", "审查"),
    ("revise_article", "修改成稿", "修改"),
    ("compare_with_sample", "与示例文章对比", "审查"),
    ("export_docx", "导出 Word 文档", "编排"),
    ("archive_log", "归档运行日志", "编排"),
]

@dataclass(frozen=True)
class Config:
    """命令行输入配置。"""

    topic: str
    target_country: str
    strategy_domain: str
    notebook_name: str
    china_response_focus: str
    report_type: str = "strategic_response"
    llm_provider: str = "deepseek"
    reuse_materials_run: str | None = None
    dry_run: bool = False
    max_iterations: int = 2
    reviewer: str = "inline"
    review_scope: str = "style_and_expression"


class ReviewHandoff(Exception):
    """信号：运行在审稿步暂停，等待外部审稿报告，可 --resume 续跑。"""

    def __init__(self, index: int) -> None:
        super().__init__(f"awaiting external review at iter{index}")
        self.index = index


class StrategicResponsePipeline:
    """通用战略应对型文章生成流程。"""

    def __init__(
        self, config: Config, *, run_id: str | None = None, resume: bool = False
    ) -> None:
        self.config = config
        self.resume = resume
        self._start_index = 1
        self.module_root = WORKFLOW_ROOT / "report_modules" / config.report_type
        if not self.module_root.is_dir():
            raise FileNotFoundError(f"体例模块不存在: {self.module_root}")
        self.module_meta = yaml.safe_load(
            (self.module_root / "module.yaml").read_text(encoding="utf-8")
        )
        self.retrieval_types: list[str] = list(self.module_meta["retrieval_types"])
        self.run_id = run_id or self._make_run_id()
        self.run_dir = WORKFLOW_ROOT / "runs" / self.run_id
        self.notebook_id = ""
        self.llm = None if config.dry_run else create_llm_client(config.llm_provider)
        self.notebooklm = NotebookLMClient(cwd=WORKFLOW_ROOT)
        self.completed_tasks: set[str] = set()
        self.failed_tasks: set[str] = set()

    def run(self) -> None:
        """执行完整流程；reviewer=handoff 时在审稿步暂停，可 --resume 续跑。"""

        paused = False
        try:
            if self.resume:
                for task_id, _, _ in TASKS:
                    if task_id == "review_draft":
                        break
                    self.completed_tasks.add(task_id)
            else:
                self._run_task("init", self._init_run)
                self._run_task("resolve_notebook", self._resolve_notebook)
                self._run_task("build_retrieval_prompts", self._build_retrieval_prompts)
                self._run_task("retrieve_materials", self._retrieve_materials)
                self._run_task("redefine_task", self._redefine_task)
                self._run_task("assign_material_roles", self._assign_material_roles)
                self._run_task("map_pressure_judgment", self._map_pressure_judgment)
                self._run_task("plan_article", self._plan_article)
                self._run_task("build_suggestion_pool", self._build_suggestion_pool)
                self._run_task("prioritize_policy_options", self._prioritize_policy_options)
                self._run_task("write_draft", self._write_draft)

            self._review_revise_loop(self._start_index)

            self._run_task("compare_with_sample", self._compare_with_sample)
            self._run_task("export_docx", self._export_docx)
        except ReviewHandoff as pause:
            paused = True
            self._emit_pause_notice(pause.index)
        finally:
            if not paused:
                self._run_task("archive_log", self._archive_log, stop_on_error=False)

    def _review_revise_loop(self, start_index: int) -> None:
        """审查—修改循环；reviewer=handoff 且报告缺失时抛 ReviewHandoff 暂停。"""

        for index in range(start_index, self.config.max_iterations + 1):
            self._do_review(index)
            if self._review_reaches_standard(index):
                self._copy("drafts/current_article.md", "final_article_reviewed.md")
                return
            self._run_task(
                f"revise_article.iter{index}",
                lambda i=index: self._revise_article(i),
            )
        self._copy("drafts/current_article.md", "final_article_reviewed.md")

    def _do_review(self, index: int) -> None:
        """inline=调 LLM 自审；handoff=确保有外部报告，否则写交接并暂停。"""

        if self.config.reviewer == "handoff":
            report_rel = f"review_reports/review_iter{index}.md"
            if not (self.run_dir / report_rel).exists():
                self._emit_review_handoff(index)
                self._save_resume_state(index)
                raise ReviewHandoff(index)
            self.completed_tasks.add(f"review_draft.iter{index}")
            self.completed_tasks.add("review_draft")
            self._render_task_state(current_task=f"review_draft.iter{index}")
            return
        self._run_task(
            f"review_draft.iter{index}", lambda i=index: self._review_draft(i)
        )

    # scope -> (拥有该范围审查标准的 DNA 目录, 该 DNA 在 run 内的快照子目录)
    # 触发哪个范围，就读哪个 DNA 的 review_scope.md 作为“审什么”。
    _SCOPE_SOURCES = {
        "style_and_expression": ("style_dna", "style_dna_snapshot"),
        "reasoning_compliance": ("reasoning_dna", "reasoning_dna_snapshot"),
    }

    def _existing_relpaths(self, subdir: str) -> list[str]:
        directory = self.run_dir / subdir
        if not directory.is_dir():
            return []
        return sorted(f"{subdir}/{item.name}" for item in directory.glob("*.md"))

    def _emit_review_handoff(self, index: int) -> None:
        """写审稿契约请求 + 由模板与 DNA 驱动的交接指令，供在场 agent 派生子 agent。

        指令不写死在代码里：骨架来自 reviewers/instruction_template.md，
        “审什么”来自本次触发范围对应 DNA 的 review_scope.md。改模板或改 DNA，下次自动反映。
        """

        scope = self.config.review_scope
        dna_dir, snapshot_subdir = self._SCOPE_SOURCES.get(
            scope, ("style_dna", "style_dna_snapshot")
        )
        scope_src = WORKFLOW_ROOT / dna_dir / "review_scope.md"
        scope_desc = (
            scope_src.read_text(encoding="utf-8").strip()
            if scope_src.is_file()
            else f"（未找到 {dna_dir}/review_scope.md，按 scope 名「{scope}」审查）"
        )
        standard_files = self._existing_relpaths(snapshot_subdir)
        judgment_files = self._existing_relpaths("judgment_outputs")
        output_rel = f"review_reports/review_iter{index}.md"

        request = {
            "run_id": self.run_id,
            "report_type": self.config.report_type,
            "label": self.module_meta.get("label", ""),
            "iteration": index,
            "scope": scope,
            "scope_source": f"{dna_dir}/review_scope.md",
            "draft": "drafts/current_article.md",
            "standard_files": standard_files,
            "context": {
                "judgment_outputs": judgment_files,
                "sample": "source/sample.md",
            },
            "output_path": output_rel,
            "output_contract": "报告必须含一行：总体结论：达到 | 基本达到 | 未达到；发现硬伤须写明",
            "resume_command": f"python3 workflow/runner.py --resume {self.run_id}",
        }
        self._write(
            f"review_io/request_iter{index}.json",
            json.dumps(request, ensure_ascii=False, indent=2),
        )

        template = (WORKFLOW_ROOT / "reviewers" / "instruction_template.md").read_text(
            encoding="utf-8"
        )
        standard_block = (
            "\n".join(f"   - runs/{self.run_id}/{p}" for p in standard_files)
            or "   - （本范围暂无快照标准文件）"
        )
        context_block = (
            "\n".join(f"   - runs/{self.run_id}/{p}" for p in judgment_files) or "   - （无）"
        )
        replacements = {
            "{{ITERATION}}": str(index),
            "{{SCOPE}}": scope,
            "{{SCOPE_DESC}}": scope_desc,
            "{{DRAFT_PATH}}": f"runs/{self.run_id}/drafts/current_article.md",
            "{{STANDARD_FILES}}": standard_block,
            "{{OUTPUT_PATH}}": f"runs/{self.run_id}/{output_rel}",
            "{{CONTEXT_FILES}}": context_block,
            "{{RESUME_CMD}}": f"python3 workflow/runner.py --resume {self.run_id}",
            "{{RUN_ID}}": self.run_id,
        }
        instruction = template
        for key, value in replacements.items():
            instruction = instruction.replace(key, value)
        self._write(f"review_io/INSTRUCTION_iter{index}.md", instruction)
        self._write(f"review_io/scope_iter{index}.md", scope_desc + "\n")
        self._write(
            "HANDOFF.md",
            f"# 等待外部审稿（第 {index} 轮）\n\n"
            f"运行 `{self.run_id}` 已暂停，等待审稿报告。\n\n"
            f"- 审稿范围：{scope}（标准源 `{dna_dir}/review_scope.md`）\n"
            f"- 交接指令：`review_io/INSTRUCTION_iter{index}.md`\n"
            f"- 机读请求：`review_io/request_iter{index}.json`\n"
            f"- 报告应写到：`{output_rel}`\n"
            f"- 续跑：`python3 workflow/runner.py --resume {self.run_id}`\n",
        )

    def _save_resume_state(self, index: int) -> None:
        """落盘续跑所需的配置与暂停轮次。"""

        config = self.config
        state = {
            "run_id": self.run_id,
            "status": "awaiting_review",
            "paused_index": index,
            "config": {
                "topic": config.topic,
                "target_country": config.target_country,
                "strategy_domain": config.strategy_domain,
                "notebook_name": config.notebook_name,
                "china_response_focus": config.china_response_focus,
                "report_type": config.report_type,
                "llm_provider": config.llm_provider,
                "reuse_materials_run": config.reuse_materials_run,
                "dry_run": config.dry_run,
                "max_iterations": config.max_iterations,
                "reviewer": config.reviewer,
                "review_scope": config.review_scope,
            },
        }
        self._write("run_state.json", json.dumps(state, ensure_ascii=False, indent=2))

    def _emit_pause_notice(self, index: int) -> None:
        print(
            "\n".join(
                [
                    "",
                    "==================== 等待外部审稿 ====================",
                    f"运行 ID   : {self.run_id}",
                    f"轮次      : 第 {index} 轮",
                    f"审稿范围  : {self.config.review_scope}",
                    f"交接指令  : runs/{self.run_id}/review_io/INSTRUCTION_iter{index}.md",
                    f"报告写到  : runs/{self.run_id}/review_reports/review_iter{index}.md",
                    f"续跑命令  : python3 workflow/runner.py --resume {self.run_id}",
                    "====================================================",
                ]
            )
        )

    @classmethod
    def resume_run(cls, run_id: str) -> "StrategicResponsePipeline":
        """从 run_state.json 重建流程以续跑。"""

        run_dir = cls._resolve_run_dir(run_id)
        state_path = run_dir / "run_state.json"
        if not state_path.is_file():
            raise FileNotFoundError(f"找不到续跑状态文件: {state_path}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        pipeline = cls(Config(**state["config"]), run_id=run_id, resume=True)
        pipeline._start_index = int(state.get("paused_index", 1))
        return pipeline

    def _init_run(self) -> None:
        """创建运行目录、输入文件和临时任务列表。"""

        for folder in [
            "generated_prompts",
            "retrieval_outputs",
            "judgment_outputs",
            "planning_outputs",
            "suggestion_outputs",
            "style_dna_snapshot",
            "drafts",
            "review_reports",
            "review_io",
            "logs",
        ]:
            (self.run_dir / folder).mkdir(parents=True, exist_ok=True)

        self._copy_style_dna_snapshot()
        self._copy_reasoning_dna_snapshot()

        self._write(
            "input.yaml",
            "\n".join(
                [
                    f'report_type: "{self.config.report_type}"',
                    f'topic: "{self.config.topic}"',
                    f'target_country: "{self.config.target_country}"',
                    f'strategy_domain: "{self.config.strategy_domain}"',
                    f'notebook_name: "{self.config.notebook_name}"',
                    f'china_response_focus: "{self.config.china_response_focus}"',
                    f'llm_provider: "{self.config.llm_provider}"',
                    f'reuse_materials_run: "{self.config.reuse_materials_run or ""}"',
                ]
            ),
        )
        self._render_task_state(current_task="init")

    def _resolve_notebook(self) -> None:
        """解析 NotebookLM 知识库。"""

        if self.config.reuse_materials_run:
            self.notebook_id = "REUSED_MATERIALS"
        elif self.config.dry_run:
            self.notebook_id = "DRY_RUN_NOTEBOOK_ID"
        else:
            self.notebooklm.check_auth()
            notebook = self.notebooklm.find_notebook(self.config.notebook_name)
            self.notebook_id = notebook.id

        self._write(
            "notebook_resolution.md",
            f"# Notebook 解析结果\n\n"
            f"- 知识库名称：{self.config.notebook_name}\n"
            f"- Notebook ID：{self.notebook_id}\n",
        )

    def _build_retrieval_prompts(self) -> None:
        """按六类通用检索任务拼装 NotebookLM 提示词。"""

        template = self._read_module("prompts/retrieval.md")
        for retrieval_type in self.retrieval_types:
            prompt = self._fill_common(template)
            prompt += f"\n\n【本次检索任务】\n请执行 `{retrieval_type}` 对应的检索任务。\n"
            self._write(f"generated_prompts/retrieval_{retrieval_type}.md", prompt)

    def _retrieve_materials(self) -> None:
        """调用 NotebookLM 完成材料检索。"""

        if self.config.reuse_materials_run:
            self._copy_retrieval_outputs(self.config.reuse_materials_run)
            return

        for retrieval_type in self.retrieval_types:
            prompt_path = self.run_dir / "generated_prompts" / f"retrieval_{retrieval_type}.md"
            output = f"retrieval_outputs/{retrieval_type}.md"
            if self.config.dry_run:
                self._write(output, "一、检索内容\n\nDRY RUN。\n\n二、相关文献\n\nDRY RUN。\n")
            else:
                content = self.notebooklm.ask_notebook(self.notebook_id, prompt_path)
                self._write(output, content)

    def _redefine_task(self) -> None:
        """把题目重定义为可写作的判断问题。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/task_redefinition.md")),
                "【示例文章抽象模板】",
                self._read_module("templates/article_template.md"),
                "【检索材料】",
                self._all_retrieval_text(),
            ]
        )
        self._write("generated_prompts/task_redefinition.md", prompt)
        self._ask_llm(prompt, "judgment_outputs/task_redefinition.md")

    def _assign_material_roles(self) -> None:
        """判断每类材料在论证链中负责证明什么。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/material_roles.md")),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【检索材料】",
                self._all_retrieval_text(),
            ]
        )
        prompt = self._with_reasoning_dna(prompt, "assign_material_roles")
        self._write("generated_prompts/material_roles.md", prompt)
        self._ask_llm(prompt, "judgment_outputs/material_roles.md")

    def _map_pressure_judgment(self) -> None:
        """把事实压力转化为文章判断和中国含义。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/pressure_judgment_mapping.md")),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【材料角色分配】",
                self._read("judgment_outputs/material_roles.md"),
                "【检索材料】",
                self._all_retrieval_text(),
            ]
        )
        prompt = self._with_reasoning_dna(prompt, "map_pressure_judgment")
        self._write("generated_prompts/pressure_judgment_mapping.md", prompt)
        self._ask_llm(prompt, "judgment_outputs/pressure_judgment_mapping.md")

    def _plan_article(self) -> None:
        """调用 LLM 做论证链构思。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/planning.md")),
                "【示例文章抽象模板】",
                self._read_module("templates/article_template.md"),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【材料角色分配】",
                self._read("judgment_outputs/material_roles.md"),
                "【压力-判断映射】",
                self._read("judgment_outputs/pressure_judgment_mapping.md"),
                "【检索材料】",
                self._all_retrieval_text(),
            ]
        )
        prompt = self._with_reasoning_dna(prompt, "plan_article")
        self._write("generated_prompts/planning.md", prompt)
        self._ask_llm(prompt, "planning_outputs/article_plan.md")

    def _build_suggestion_pool(self) -> None:
        """先生成候选建议池，避免正文阶段凭空列建议。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/suggestion_pool.md")),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【材料角色分配】",
                self._read("judgment_outputs/material_roles.md"),
                "【压力-判断映射】",
                self._read("judgment_outputs/pressure_judgment_mapping.md"),
                "【文章论证链构思】",
                self._read("planning_outputs/article_plan.md"),
                "【检索材料】",
                self._all_retrieval_text(),
            ]
        )
        prompt = self._with_reasoning_dna(prompt, "build_suggestion_pool")
        self._write("generated_prompts/suggestion_pool.md", prompt)
        self._ask_llm(prompt, "suggestion_outputs/suggestion_pool.md")

    def _prioritize_policy_options(self) -> None:
        """对候选建议进行近期、中期、长期排序。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/policy_priority.md")),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【压力-判断映射】",
                self._read("judgment_outputs/pressure_judgment_mapping.md"),
                "【候选建议池】",
                self._read("suggestion_outputs/suggestion_pool.md"),
            ]
        )
        prompt = self._with_reasoning_dna(prompt, "prioritize_policy_options")
        self._write("generated_prompts/policy_priority.md", prompt)
        self._ask_llm(prompt, "suggestion_outputs/policy_priority.md")

    def _write_draft(self) -> None:
        """基于构思和检索材料生成初稿。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/writing.md")),
                "【政策研究文风 DNA】",
                self._style_dna_text("writing"),
                "【示例文章抽象模板】",
                self._read_module("templates/article_template.md"),
                "【文章构思】",
                self._read("planning_outputs/article_plan.md"),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【材料角色分配】",
                self._read("judgment_outputs/material_roles.md"),
                "【压力-判断映射】",
                self._read("judgment_outputs/pressure_judgment_mapping.md"),
                "【候选建议池】",
                self._read("suggestion_outputs/suggestion_pool.md"),
                "【政策优先序】",
                self._read("suggestion_outputs/policy_priority.md"),
                "【检索材料】",
                self._all_retrieval_text(),
            ]
        )
        self._write("generated_prompts/writing.md", prompt)
        self._ask_llm(prompt, "drafts/current_article.md")
        self._copy("drafts/current_article.md", "final_article.md")

    def _review_draft(self, index: int) -> None:
        """对当前稿进行质量审查。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/review.md")),
                "【政策研究文风 DNA】",
                self._style_dna_text("review"),
                "【示例文章原文】",
                self._read_module("source/sample.md"),
                "【示例文章抽象模板】",
                self._read_module("templates/article_template.md"),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【材料角色分配】",
                self._read("judgment_outputs/material_roles.md"),
                "【压力-判断映射】",
                self._read("judgment_outputs/pressure_judgment_mapping.md"),
                "【政策优先序】",
                self._read("suggestion_outputs/policy_priority.md"),
                "【当前文章】",
                self._read("drafts/current_article.md"),
            ]
        )
        self._write(f"generated_prompts/review_iter{index}.md", prompt)
        self._ask_llm(prompt, f"review_reports/review_iter{index}.md")

    def _revise_article(self, index: int) -> None:
        """根据审查报告修改文章。"""

        prompt = "\n\n".join(
            [
                self._fill_common(self._read_module("prompts/revision.md")),
                "【政策研究文风 DNA】",
                self._style_dna_text("revision"),
                "【示例文章抽象模板】",
                self._read_module("templates/article_template.md"),
                "【文章构思】",
                self._read("planning_outputs/article_plan.md"),
                "【任务重定义】",
                self._read("judgment_outputs/task_redefinition.md"),
                "【材料角色分配】",
                self._read("judgment_outputs/material_roles.md"),
                "【压力-判断映射】",
                self._read("judgment_outputs/pressure_judgment_mapping.md"),
                "【候选建议池】",
                self._read("suggestion_outputs/suggestion_pool.md"),
                "【政策优先序】",
                self._read("suggestion_outputs/policy_priority.md"),
                "【审查报告】",
                self._read(f"review_reports/review_iter{index}.md"),
                "【当前文章】",
                self._read("drafts/current_article.md"),
                "【必要检索材料】",
                self._all_retrieval_text(),
            ]
        )
        self._write(f"generated_prompts/revision_iter{index}.md", prompt)
        self._ask_llm(prompt, "drafts/current_article.md")

    def _compare_with_sample(self) -> None:
        """生成最终对比报告。"""

        prompt = f"""你是政策文章质量评估专家。请比较示例文章和生成文章。

【比较维度】
1. 结构是否匹配“{self.module_meta.get('label', self.config.report_type)}”体例。
2. 表达是否接近示例文章的凝练政策文风。
3. 深度是否体现明确的判断与分析，而不只是资料汇编。
4. 建议是否具体、成体系、回应前文。
5. 生成文章是否达到、接近或超过示例文章。
6. 是否符合 style_dna 中“冷峻审慎、证据驱动、建设性建议”的政策研究声音。
7. 是否存在 style_dna 明确禁止的 AI 腔、过程信息外露、建议悬空或过度学术化。

【政策研究文风 DNA】
{self._style_dna_text("review")}

【示例文章】
{self._read_module("source/sample.md")}

【生成文章】
{self._read("final_article_reviewed.md")}

请输出自然语言对比报告，给出明确结论和后续提示词改进建议。
"""
        self._write("generated_prompts/compare_with_sample.md", prompt)
        self._ask_llm(prompt, "review_reports/template_match_review.md")

    def _export_docx(self) -> None:
        """导出 Word 文档。"""

        source = self.run_dir / "final_article_reviewed.md"
        target = self.run_dir / "final_article_reviewed.docx"
        if self.config.dry_run:
            self._write("final_article_reviewed.docx.txt", "DRY RUN：未导出 docx。")
            return
        subprocess.run(["pandoc", str(source), "-o", str(target)], check=True)

    def _archive_log(self) -> None:
        """归档运行日志。"""

        outputs = [
            "style_dna_snapshot/voice.md",
            "style_dna_snapshot/structure.md",
            "style_dna_snapshot/sentence.md",
            "style_dna_snapshot/forbidden.md",
            "style_dna_snapshot/recommendation.md",
            "style_dna_snapshot/self_check.md",
            "judgment_outputs/task_redefinition.md",
            "judgment_outputs/material_roles.md",
            "judgment_outputs/pressure_judgment_mapping.md",
            "planning_outputs/article_plan.md",
            "suggestion_outputs/suggestion_pool.md",
            "suggestion_outputs/policy_priority.md",
            "final_article.md",
            "final_article_reviewed.md",
            "final_article_reviewed.docx",
            "review_reports/review_iter1.md",
            "review_reports/review_iter2.md",
            "review_reports/template_match_review.md",
        ]
        existing = [item for item in outputs if (self.run_dir / item).exists()]
        self._write(
            "run_log.md",
            "# 运行日志\n\n"
            f"- 运行 ID：{self.run_id}\n"
            f"- 体例模块：{self.config.report_type}（{self.module_meta.get('label', '')}）\n"
            f"- 主题：{self.config.topic}\n"
            f"- 目标国家：{self.config.target_country}\n"
            f"- 战略领域：{self.config.strategy_domain}\n"
            f"- 知识库：{self.config.notebook_name}\n"
            f"- LLM 后端：{self.config.llm_provider}\n"
            f"- 复用材料运行：{self.config.reuse_materials_run or '否'}\n"
            f"- 归档时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "## 最终产物\n\n"
            + "\n".join(f"- {item}" for item in existing)
            + "\n",
        )
        self._render_task_state(current_task="archive_log", done=True)

    def _ask_llm(self, prompt: str, output: str) -> None:
        """调用当前 LLM 后端；dry-run 时写占位内容。"""

        if self.config.dry_run:
            self._write(
                output,
                f"DRY RUN：未调用 {self.config.llm_provider}。\n\n提示词长度：{len(prompt)}\n",
            )
            return
        if self.llm is None:
            raise RuntimeError("LLM 客户端未初始化")
        content = self.llm.ask(prompt)
        self._write(output, content)

    def _review_reaches_standard(self, index: int) -> bool:
        """根据审查报告判断是否可以停止迭代。

        “基本达到”但仍出现不合理建议、对象错配、工具错配或必须重写时，
        不能提前停下，否则审查只会变成形式确认。
        """

        text = self._read(f"review_reports/review_iter{index}.md")
        blocker_patterns = [
            r"总体结论[：:]\s*未达到",
            r"未达到示例标准",
            r"(?:判定|结论)[：:]\s*不合理",
            r"(?:判定为|被判为|属于)\s*不合理",
            r"(?:存在|出现|仍有|发现|属于|判定为|被判为).{0,12}对象错配",
            r"(?:存在|出现|仍有|发现|属于|判定为|被判为).{0,12}工具错配",
            r"(?:存在|出现|仍有|发现|属于|判定为|被判为).{0,12}制度不适配",
            r"必须重写",
            r"需要重构",
            r"(?:存在|仍有|发现).{0,12}硬伤",
        ]
        if any(re.search(pattern, text) for pattern in blocker_patterns):
            return False
        return "总体结论：达到" in text or "总体结论：基本达到" in text

    def _all_retrieval_text(self) -> str:
        """汇总全部检索材料。"""

        blocks = []
        for retrieval_type in self.retrieval_types:
            path = f"retrieval_outputs/{retrieval_type}.md"
            blocks.append(f"## {retrieval_type}\n\n{self._read(path)}")
        return "\n\n".join(blocks)

    def _copy_style_dna_snapshot(self) -> None:
        """把本次使用的文风规则复制到运行目录，便于复查。"""
        source_dir = WORKFLOW_ROOT / "style_dna" / "wiki"
        if not source_dir.is_dir():
            return
        for name in [
            "voice.md",
            "structure.md",
            "sentence.md",
            "forbidden.md",
            "recommendation.md",
            "self_check.md",
        ]:
            source = source_dir / name
            if source.is_file():
                shutil.copyfile(source, self.run_dir / "style_dna_snapshot" / name)

    def _style_dna_text(self, mode: str) -> str:
        """读取写作、审查、修改阶段需要的文风规则。"""
        mode_to_files = {
            "writing": [
                "voice.md",
                "structure.md",
                "sentence.md",
                "recommendation.md",
                "forbidden.md",
            ],
            "review": [
                "voice.md",
                "structure.md",
                "forbidden.md",
                "recommendation.md",
                "self_check.md",
            ],
            "revision": [
                "voice.md",
                "sentence.md",
                "forbidden.md",
                "recommendation.md",
                "self_check.md",
            ],
        }
        files = mode_to_files.get(mode, mode_to_files["writing"])
        blocks = []
        for name in files:
            path = WORKFLOW_ROOT / "style_dna" / "wiki" / name
            if path.is_file():
                blocks.append(f"## {name}\n\n{path.read_text(encoding='utf-8')}")
        if not blocks:
            return "未发现 style_dna/wiki 规则，本次按基础提示词运行。"
        return "\n\n".join(blocks)

    def _reasoning_dna_text(self, step_id: str) -> str:
        """按 module.yaml 的 reasoning_dna_injection 映射，取该步对应的刀 + 共享 conventions。

        映射缺、或所列刀文件全缺 → 返回空串（gated：现有模块尚无刀时行为零变化）。
        """
        injection = (self.module_meta or {}).get("reasoning_dna_injection") or {}
        cuts = injection.get(step_id) or []
        present = [
            c for c in cuts if (self.module_root / "reasoning_dna" / f"{c}.md").is_file()
        ]
        if not present:
            return ""
        blocks = []
        conventions = WORKFLOW_ROOT / "reasoning_dna" / "conventions.md"
        if conventions.is_file():
            blocks.append(f"## conventions\n\n{conventions.read_text(encoding='utf-8')}")
        for cut in present:
            path = self.module_root / "reasoning_dna" / f"{cut}.md"
            blocks.append(f"## {cut}\n\n{path.read_text(encoding='utf-8')}")
        return "\n\n".join(blocks)

    def _with_reasoning_dna(self, prompt: str, step_id: str) -> str:
        """把该步的 reasoning_dna 逼问追加到 prompt 末尾锚点；无刀则原样返回。"""
        block = self._reasoning_dna_text(step_id)
        if not block:
            return prompt
        return prompt + "\n\n## 本步必答逼问（须留降级扫描记录）\n\n" + block

    def _copy_reasoning_dna_snapshot(self) -> None:
        """把本次模块的刀 + 共享 conventions 复制到 run 目录，便于复查。"""
        target = self.run_dir / "reasoning_dna_snapshot"
        conventions = WORKFLOW_ROOT / "reasoning_dna" / "conventions.md"
        if conventions.is_file():
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(conventions, target / "conventions.md")
        cut_dir = self.module_root / "reasoning_dna"
        if cut_dir.is_dir():
            for path in sorted(cut_dir.glob("*.md")):
                target.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target / path.name)

    def _copy_retrieval_outputs(self, run_id: str) -> None:
        """从既有运行目录复用 NotebookLM 检索材料。"""
        source_dir = self._resolve_run_dir(run_id) / "retrieval_outputs"
        if not source_dir.is_dir():
            raise FileNotFoundError(f"复用材料目录不存在: {source_dir}")

        for retrieval_type in self.retrieval_types:
            source = source_dir / f"{retrieval_type}.md"
            if not source.is_file():
                raise FileNotFoundError(f"缺少复用材料文件: {source}")
            target = self.run_dir / "retrieval_outputs" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

        self._write(
            "retrieval_outputs/reuse_note.md",
            f"# 复用材料说明\n\n"
            f"本次未重新调用 NotebookLM，已复用 `{run_id}` 的六类检索材料。\n",
        )

    @staticmethod
    def _resolve_run_dir(run_id: str) -> Path:
        """把运行 ID 解析为 workflow/runs 下的目录，避免越界读取。"""
        if "/" in run_id or "\\" in run_id or run_id in {"", ".", ".."}:
            raise ValueError(f"运行 ID 非法: {run_id}")
        run_dir = (WORKFLOW_ROOT / "runs" / run_id).resolve()
        runs_root = (WORKFLOW_ROOT / "runs").resolve()
        if runs_root != run_dir and runs_root not in run_dir.parents:
            raise ValueError(f"运行目录超出 runs 边界: {run_dir}")
        return run_dir

    def _fill_common(self, text: str) -> str:
        """替换通用变量占位符。"""

        replacements = {
            "【主题】": self.config.topic,
            "【目标国家】": self.config.target_country,
            "【战略领域】": self.config.strategy_domain,
            "【中国应对主题】": self.config.china_response_focus,
        }
        for key, value in replacements.items():
            text = text.replace(key, value)
        return text

    def _run_task(self, task_id: str, func, stop_on_error: bool = True) -> None:
        """执行任务并记录状态。"""

        self._render_task_state(current_task=task_id)
        try:
            func()
        except Exception:  # noqa: BLE001 - 需要把完整错误落盘
            self._write(f"logs/{task_id}_traceback.md", traceback.format_exc())
            self.failed_tasks.add(task_id)
            self.failed_tasks.add(task_id.split(".", 1)[0])
            self._render_task_state(current_task=task_id, failed=True)
            if stop_on_error:
                raise
        else:
            self.completed_tasks.add(task_id)
            self.completed_tasks.add(task_id.split(".", 1)[0])
            self._render_task_state(current_task=task_id)

    def _render_task_state(
        self,
        current_task: str,
        done: bool = False,
        failed: bool = False,
    ) -> None:
        """写入可读的临时任务状态。"""

        current_base_task = current_task.split(".", 1)[0]
        rows = []
        for task_id, name, function in TASKS:
            status = "pending"
            if done or task_id in self.completed_tasks:
                status = "done"
            elif task_id in self.failed_tasks:
                status = "failed"
            elif task_id == current_base_task:
                status = "failed" if failed else "running"
            rows.append(f"| {task_id} | {name} | {function} | {status} |")
        self._write(
            "task_state.md",
            "# 临时任务列表\n\n"
            f"- 运行 ID：{self.run_id}\n"
            f"- 主题：{self.config.topic}\n"
            f"- 目标国家：{self.config.target_country}\n"
            f"- 战略领域：{self.config.strategy_domain}\n\n"
            f"- LLM 后端：{self.config.llm_provider}\n\n"
            "| 任务 ID | 模块 | 功能 | 状态 |\n"
            "| --- | --- | --- | --- |\n"
            + "\n".join(rows)
            + "\n",
        )

    def _read(self, relative_path: str) -> str:
        return (self.run_dir / relative_path).read_text(encoding="utf-8")

    def _read_module(self, relative_path: str) -> str:
        return (self.module_root / relative_path).read_text(encoding="utf-8")

    def _write(self, relative_path: str, content: str) -> Path:
        path = self.run_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        return path

    def _copy(self, source: str, target: str) -> None:
        self._write(target, self._read(source))

    @staticmethod
    def _make_run_id() -> str:
        return f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="政策文章工作流（多体例可载入）")
    parser.add_argument(
        "--resume",
        metavar="RUN_ID",
        help="续跑指定 run-id：从其暂停的审稿步继续（reviewer=handoff 用）",
    )
    parser.add_argument("--topic")
    parser.add_argument("--target-country")
    parser.add_argument("--strategy-domain")
    parser.add_argument("--notebook-name")
    parser.add_argument("--china-response-focus", default="中国应对策略")
    parser.add_argument(
        "--reviewer",
        default="inline",
        choices=["inline", "handoff"],
        help="审稿方式：inline=同后端 LLM 自审（默认，原行为）；handoff=暂停交外部 agent 审稿后 --resume 续跑",
    )
    parser.add_argument(
        "--review-scope",
        default="style_and_expression",
        choices=["style_and_expression", "reasoning_compliance"],
        help="handoff 审稿范围；默认只审文风与表述",
    )
    modules_root = WORKFLOW_ROOT / "report_modules"
    available_modules = sorted(
        p.name for p in modules_root.iterdir() if p.is_dir()
    ) if modules_root.is_dir() else []
    available_hint = "、".join(available_modules) if available_modules else "（未找到）"
    parser.add_argument(
        "--report-type",
        default="strategic_response",
        help=f"体例模块，对应 report_modules/ 下的目录名；当前可用：{available_hint}",
    )
    parser.add_argument(
        "--llm-provider",
        default="deepseek",
        choices=["deepseek", "anthropic_compat"],
        help="文本生成后端；默认 deepseek，可切换为 anthropic_compat",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=2)
    parser.add_argument(
        "--reuse-materials-run",
        help="复用指定 run-id 的 retrieval_outputs，跳过 NotebookLM 重新检索",
    )
    return parser.parse_args()


def main() -> int:
    """启动流程。"""

    args = parse_args()

    if args.resume:
        StrategicResponsePipeline.resume_run(args.resume).run()
        return 0

    missing = [
        name
        for name in ("topic", "target_country", "strategy_domain", "notebook_name")
        if not getattr(args, name)
    ]
    if missing:
        flags = ", ".join("--" + name.replace("_", "-") for name in missing)
        raise SystemExit(f"缺少必填参数: {flags}（或用 --resume <run-id> 续跑）")

    config = Config(
        topic=args.topic,
        target_country=args.target_country,
        strategy_domain=args.strategy_domain,
        notebook_name=args.notebook_name,
        china_response_focus=args.china_response_focus,
        report_type=args.report_type,
        llm_provider=args.llm_provider,
        reuse_materials_run=args.reuse_materials_run,
        dry_run=args.dry_run,
        max_iterations=max(1, args.max_iterations),
        reviewer=args.reviewer,
        review_scope=args.review_scope,
    )
    StrategicResponsePipeline(config).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
