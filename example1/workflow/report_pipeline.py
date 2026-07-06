"""报告生成主流程。

Codex 在这里扮演调度者：创建运行目录、维护 `task_state.md`、调用
NotebookLM/DeepSeek、传输对应文件并落盘。
"""

from __future__ import annotations

import re
import shutil
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import file_store
import prompt_builder
import task_state
from deepseek_client import DeepSeekClient, DeepSeekEmptyResponseError
from notebooklm_client import NotebookLMClient

WORKFLOW_DIR = Path(__file__).resolve().parent
# 仓根：跨引擎共享的 SSOT 资产（policy_style_dna/、institution_profile.md）
# 自 2026-07-05 起收敛于仓根（example1/），两引擎共读一份，禁止再复制副本。
REPO_ROOT = WORKFLOW_DIR.parent


@dataclass(frozen=True)
class PipelineConfig:
    """流程运行所需的最小配置。"""

    topic: str
    notebook_name: str
    runs_dir: Path
    dry_run: bool = False
    resume_run: str | None = None
    reuse_materials_run: str | None = None


class ReportPipeline:
    """国际政策比较报告自动生成流程。"""

    def __init__(
        self,
        topic: str,
        notebook_name: str,
        runs_dir: Path,
        dry_run: bool = False,
        resume_run: str | None = None,
        reuse_materials_run: str | None = None,
    ) -> None:
        self.config = PipelineConfig(
            topic=topic,
            notebook_name=notebook_name,
            runs_dir=runs_dir,
            dry_run=dry_run,
            resume_run=resume_run,
            reuse_materials_run=reuse_materials_run,
        )
        if resume_run:
            self.run_id = resume_run
            self.run_dir = file_store.get_run_dir(resume_run)
        else:
            self.run_id, self.run_dir = file_store.create_run_dir()
        self.notebooklm = NotebookLMClient()
        self.deepseek = DeepSeekClient()
        if resume_run:
            self._migrate_task_state_for_chapter3()
            self._migrate_task_state_for_full_review()
        self.notebook_id = self._load_notebook_id_from_state() if resume_run else ""

    def run(self) -> None:
        """执行完整 MVP 流程。"""
        if not self.config.resume_run:
            self._write(
                "input.yaml",
                f'topic: "{self.config.topic}"\n'
                f'notebook_name: "{self.config.notebook_name}"\n',
            )
            task_state.create_task_state(
                run_dir=self.run_dir,
                run_id=self.run_id,
                topic=self.config.topic,
                notebook_name=self.config.notebook_name,
            )
            if self.config.reuse_materials_run:
                self._reuse_materials()

        try:
            self._run_task("init.resolve_notebook", self._resolve_notebook)
            self._run_task("prompt.build_all", self._build_prompts)

            self._run_task("ch1.1a.retrieve", self._retrieve_ch1_1a)
            self._run_task("ch1.2a.retrieve", self._retrieve_ch1_2a)
            self._run_task("ch0.strategic_framing", self._strategic_framing)
            self._run_task("ch1.1b.write", self._write_ch1_1b)
            self._run_task("ch1.2b.write", self._write_ch1_2b)
            self._run_task("ch1.3a.plan", self._plan_ch1_3a)
            self._run_task("ch1.3b.retrieve", self._retrieve_ch1_3b)
            self._run_task("ch1.3c.write", self._write_ch1_3c)
            self._run_task("ch1.assemble", self._assemble_ch1)
            self._run_task("ch1.review", self._review_ch1)

            self._run_task("ch2.topic.plan", self._plan_ch2_topic)
            self._run_task("ch2.retrieve", self._retrieve_ch2)
            self._run_task("ch2.dimension.plan", self._plan_ch2_dimensions)
            self._run_task("ch2.write", self._write_ch2)
            self._run_task("ch2.review", self._review_ch2)

            self._run_task("ch3.write", self._write_ch3)
            self._run_task("final.assemble", self._assemble_final)
            self._run_task("final.review", self._review_final)
            self._run_task("full.review", self._review_full_content_structure)
            self._run_task("full.rewrite", self._rewrite_full_report)
        finally:
            self._run_task(
                "run.archive_log",
                self._archive_log,
                stop_on_error=False,
                skip_done=False,
            )

    def _run_task(
        self,
        task_id: str,
        func: Callable[[], None],
        stop_on_error: bool = True,
        skip_done: bool = True,
    ) -> None:
        """运行单个任务并维护状态文件。"""
        current = self._task_status(task_id)
        if skip_done and current == "done":
            return
        task_state.update_task_status(self.run_dir, task_id, "running")
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - 这里需要把所有错误写入运行日志
            task_state.record_task_error(
                self.run_dir,
                task_id,
                error_summary=str(exc),
                command=func.__name__,
                suggestion="检查 task_state.md 中的错误详情后重试",
            )
            detail_path = self.run_dir / "review_reports" / f"{task_id.replace('.', '_')}_traceback.md"
            file_store.write_markdown(detail_path, traceback.format_exc())
            if stop_on_error:
                raise
        else:
            task_state.record_task_output(self.run_dir, task_id, output=self._task_output(task_id))

    def _resolve_notebook(self) -> None:
        """解析 NotebookLM 知识库名称。"""
        if self.config.dry_run:
            self.notebook_id = "DRY_RUN_NOTEBOOK_ID"
            self._write(
                "notebook_resolution.md",
                f"# Notebook 解析结果\n\n"
                f"- 知识库名称：{self.config.notebook_name}\n"
                f"- Notebook ID：{self.notebook_id}\n"
                f"- 状态：dry-run\n",
            )
            self._refresh_task_state_notebook_id()
            return

        if self.config.reuse_materials_run:
            self.notebook_id = "REUSED_MATERIALS"
            self._write(
                "notebook_resolution.md",
                f"# Notebook 解析结果\n\n- 复用材料运行：{self.config.reuse_materials_run}\n- Notebook ID：{self.notebook_id}\n",
            )
            self._refresh_task_state_notebook_id()
            return

        self.notebooklm.check_auth()
        notebook = self.notebooklm.find_notebook(self.config.notebook_name)
        self.notebook_id = notebook.id
        self._write(
            "notebook_resolution.md",
            f"# Notebook 解析结果\n\n"
            f"- 输入知识库名称：{self.config.notebook_name}\n"
            f"- 匹配知识库名称：{notebook.name}\n"
            f"- Notebook ID：{notebook.id}\n",
        )
        self._refresh_task_state_notebook_id()

    def _build_prompts(self) -> None:
        """生成无需上游材料即可确定的初始提示词。"""
        self._save_prompt(
            "retrieval.ch1_1a",
            "ch1_1a_retrieval.md",
            topic=self.config.topic,
            notebook_name=self.config.notebook_name,
            notebook_id=self.notebook_id,
        )
        self._save_prompt(
            "retrieval.ch1_2a",
            "ch1_2a_retrieval.md",
            topic=self.config.topic,
            notebook_name=self.config.notebook_name,
            notebook_id=self.notebook_id,
        )
        self._save_prompt(
            "planning.ch1_3a",
            "ch1_3a_planning.md",
            topic=self.config.topic,
        )
        self._save_prompt(
            "planning.chapter2_topic",
            "ch2_topic_planning.md",
            topic=self.config.topic,
        )

    def _retrieve_ch1_1a(self) -> None:
        self._ask_notebooklm(
            prompt="generated_prompts/ch1_1a_retrieval.md",
            output="retrieval_outputs/chapter1_top_design.md",
        )

    def _retrieve_ch1_2a(self) -> None:
        self._ask_notebooklm(
            prompt="generated_prompts/ch1_2a_retrieval.md",
            output="retrieval_outputs/chapter1_implementation.md",
        )

    def _write_ch1_1b(self) -> None:
        prompt = prompt_builder.build_writing_prompt(
            "ch1_1b",
            topic=self.config.topic,
            ch1_1a_retrieval_content=self._split_retrieval_content(
                self._read("retrieval_outputs/chapter1_top_design.md")
            )[0],
            ch1_1a_related_literature=self._split_retrieval_content(
                self._read("retrieval_outputs/chapter1_top_design.md")
            )[1],
        )
        prompt = self._with_strategic_framing(prompt)
        self._save_generated_prompt("ch1_1b_writing.md", prompt)
        self._ask_deepseek(prompt, "chapter_drafts/chapter1_top_design.md")
        self._postprocess_ch1_governance_draft("chapter_drafts/chapter1_top_design.md")

    def _write_ch1_2b(self) -> None:
        retrieval_content, related_literature = self._split_retrieval_content(
            self._read("retrieval_outputs/chapter1_implementation.md")
        )
        prompt = prompt_builder.build_writing_prompt(
            "ch1_2b",
            topic=self.config.topic,
            ch1_2a_retrieval_content=retrieval_content,
            ch1_2a_related_literature=related_literature,
        )
        prompt = self._with_strategic_framing(prompt)
        self._save_generated_prompt("ch1_2b_writing.md", prompt)
        self._ask_deepseek(prompt, "chapter_drafts/chapter1_implementation.md")
        self._postprocess_ch1_governance_draft("chapter_drafts/chapter1_implementation.md")

    def _plan_ch1_3a(self) -> None:
        prompt = self._read("generated_prompts/ch1_3a_planning.md")
        prompt = self._with_strategic_framing(prompt)
        self._save_generated_prompt("ch1_3a_planning.md", prompt)
        self._ask_deepseek(prompt, "extracted_materials/chapter1_topic_specific_title.md")

    def _retrieve_ch1_3b(self) -> None:
        title = self._read("extracted_materials/chapter1_topic_specific_title.md")
        path = self._save_prompt(
            "retrieval.ch1_3b",
            "ch1_3b_retrieval.md",
            topic=self.config.topic,
            notebook_name=self.config.notebook_name,
            notebook_id=self.notebook_id,
            chapter1_topic_specific_title=title,
        )
        self._ask_notebooklm(
            prompt=path.relative_to(self.run_dir),
            output="retrieval_outputs/chapter1_topic_specific.md",
        )

    def _write_ch1_3c(self) -> None:
        retrieval_content, related_literature = self._split_retrieval_content(
            self._read("retrieval_outputs/chapter1_topic_specific.md")
        )
        prompt = prompt_builder.build_writing_prompt(
            "ch1_3c",
            topic=self.config.topic,
            chapter1_topic_specific_title=self._read(
                "extracted_materials/chapter1_topic_specific_title.md"
            ),
            ch1_3b_retrieval_content=retrieval_content,
            ch1_3b_related_literature=related_literature,
        )
        prompt = self._with_strategic_framing(prompt)
        self._save_generated_prompt("ch1_3c_writing.md", prompt)
        self._ask_deepseek(prompt, "chapter_drafts/chapter1_topic_specific.md")
        self._ensure_ch1_topic_specific_heading("chapter_drafts/chapter1_topic_specific.md")

    def _assemble_ch1(self) -> None:
        content = "\n\n".join(
            [
                "# 第一章 各国治理模式\n",
                self._read("chapter_drafts/chapter1_top_design.md"),
                self._read("chapter_drafts/chapter1_implementation.md"),
                self._read("chapter_drafts/chapter1_topic_specific.md"),
            ]
        )
        self._write("chapter_drafts/chapter1.md", content)

    def _review_ch1(self) -> None:
        prompt = self._build_review_prompt(
            chapter_name="第一章",
            draft=self._read("chapter_drafts/chapter1.md"),
            materials="\n\n".join(
                [
                    self._read("retrieval_outputs/chapter1_top_design.md"),
                    self._read("retrieval_outputs/chapter1_implementation.md"),
                    self._read("retrieval_outputs/chapter1_topic_specific.md"),
                ]
            ),
        )
        self._save_generated_prompt("ch1_review.md", prompt)
        self._ask_deepseek(prompt, "review_reports/chapter1_review.md")

    def _plan_ch2_topic(self) -> None:
        prompt = self._read("generated_prompts/ch2_topic_planning.md")
        prompt = self._with_strategic_framing(prompt)
        self._save_generated_prompt("ch2_topic_planning.md", prompt)
        self._ask_deepseek(
            prompt,
            "extracted_materials/chapter2_topic.md",
            reasoning_effort="max",
        )

    def _retrieve_ch2(self) -> None:
        path = self._save_prompt(
            "retrieval.chapter2_materials",
            "ch2_materials_retrieval.md",
            topic=self.config.topic,
            notebook_name=self.config.notebook_name,
            notebook_id=self.notebook_id,
            chapter2_topic=self._read("extracted_materials/chapter2_topic.md"),
        )
        self._ask_notebooklm(
            prompt=path.relative_to(self.run_dir),
            output="retrieval_outputs/chapter2_materials.md",
        )

    def _plan_ch2_dimensions(self) -> None:
        retrieval_content, related_literature = self._split_retrieval_content(
            self._read("retrieval_outputs/chapter2_materials.md")
        )
        prompt = prompt_builder.build_planning_prompt(
            "chapter2_dimensions",
            topic=self.config.topic,
            chapter2_topic=self._read("extracted_materials/chapter2_topic.md"),
            chapter2_retrieval_content=retrieval_content,
            chapter2_related_literature=related_literature,
        )
        prompt = self._with_strategic_framing(prompt)
        prompt = "\n\n".join(
            [
                prompt,
                "【战略仰角校准（硬约束）】自下而上凝出维度后再向上校准一次：维度须落在“国家战略布局/路线选择”的高度可比，而非停在技术做法层；若维度过于技术化，参照战略态势卡的“全局态势”与“政策层级演进”向上抽一层重命名。仅可依据材料中已有的高位政策事实做此提升，不得自造战略叙事。",
            ]
        )
        self._save_generated_prompt("ch2_dimensions_planning.md", prompt)
        self._ask_deepseek(prompt, "extracted_materials/chapter2_dimensions.md")

    def _write_ch2(self) -> None:
        retrieval_content, related_literature = self._split_retrieval_content(
            self._read("retrieval_outputs/chapter2_materials.md")
        )
        prompt = prompt_builder.build_writing_prompt(
            "chapter2_body",
            topic=self.config.topic,
            chapter2_topic=self._read("extracted_materials/chapter2_topic.md"),
            chapter2_dimension_plan=self._read("extracted_materials/chapter2_dimensions.md"),
            chapter2_retrieval_content=retrieval_content,
            chapter2_related_literature=related_literature,
        )
        prompt = self._with_strategic_framing(prompt)
        self._save_generated_prompt("ch2_writing.md", prompt)
        self._ask_deepseek(prompt, "chapter_drafts/chapter2.md")
        self._ensure_chapter2_heading("chapter_drafts/chapter2.md")

    def _review_ch2(self) -> None:
        prompt = self._build_review_prompt(
            chapter_name="第二章",
            draft=self._read("chapter_drafts/chapter2.md"),
            materials=self._read("retrieval_outputs/chapter2_materials.md"),
        )
        self._save_generated_prompt("ch2_review.md", prompt)
        self._ask_deepseek(prompt, "review_reports/chapter2_review.md")

    def _write_ch3(self) -> None:
        prompt = prompt_builder.build_writing_prompt(
            "chapter3_body",
            topic=self.config.topic,
            chapter1_draft=self._read("chapter_drafts/chapter1.md"),
            chapter2_draft=self._read("chapter_drafts/chapter2.md"),
        )
        prompt = self._with_strategic_framing(prompt)
        prompt = self._with_institution_profile(prompt)
        prompt = self._with_policy_style_dna(prompt, "writing")
        self._save_generated_prompt("ch3_writing.md", prompt)
        self._ask_deepseek(prompt, "chapter_drafts/chapter3.md")

    def _assemble_final(self) -> None:
        content = "\n\n".join(
            [
                f"# {self.config.topic}国际政策比较报告",
                self._read("chapter_drafts/chapter1.md"),
                self._read("chapter_drafts/chapter2.md"),
                self._read("chapter_drafts/chapter3.md"),
            ]
        )
        self._write("final_report.md", content)

    def _review_final(self) -> None:
        prompt = self._build_review_prompt(
            chapter_name="全报告",
            draft=self._read("final_report.md"),
            materials="\n\n".join(
                [
                    self._read("retrieval_outputs/chapter1_top_design.md"),
                    self._read("retrieval_outputs/chapter1_implementation.md"),
                    self._read("retrieval_outputs/chapter1_topic_specific.md"),
                    self._read("retrieval_outputs/chapter2_materials.md"),
                ]
            ),
        )
        self._save_generated_prompt("final_review.md", prompt)
        self._ask_deepseek(prompt, "review_reports/final_review.md")

    def _review_full_content_structure(self) -> None:
        """基于固定模板审查全文内容与结构。"""

        prompt = prompt_builder.build_review_prompt(
            "fulltext_content_structure",
            topic=self.config.topic,
            review_template=self._read_review_template(),
            full_report=self._read("final_report.md"),
        )
        prompt = self._with_strategic_framing(prompt)
        prompt = self._with_policy_style_dna(prompt, "review")
        self._save_generated_prompt("fulltext_content_structure_review.md", prompt)
        self._ask_deepseek(prompt, "review_reports/fulltext_content_structure_review.md")

    def _rewrite_full_report(self) -> None:
        """根据全文审查意见生成修改后的完整报告。"""

        prompt = prompt_builder.build_revision_prompt(
            "fulltext_content_structure",
            topic=self.config.topic,
            review_template=self._read_review_template(),
            review_report=self._read("review_reports/fulltext_content_structure_review.md"),
            full_report=self._read("final_report.md"),
        )
        prompt = self._with_strategic_framing(prompt)
        prompt = self._with_institution_profile(prompt)
        self._save_generated_prompt("fulltext_content_structure_rewrite.md", prompt)
        self._ask_deepseek(prompt, "final_report_reviewed.md")

    def _archive_log(self) -> None:
        """归档运行日志。"""
        state = task_state.load_task_state(self.run_dir)
        final_status = (
            "failed"
            if any(item.status in {"failed", "blocked"} for item in state.tasks)
            else "done"
        )
        candidate_outputs = [
            "final_report_reviewed.md",
            "final_report.md",
            "review_reports/fulltext_content_structure_review.md",
            "chapter_drafts/chapter1.md",
            "chapter_drafts/chapter2.md",
            "chapter_drafts/chapter3.md",
        ]
        existing_outputs = [
            item for item in candidate_outputs if (self.run_dir / item).exists()
        ]
        task_state.archive_run_log(
            self.run_dir,
            final_status=final_status,
            final_outputs=existing_outputs,
        )

    def _ask_notebooklm(self, prompt: str | Path, output: str | Path) -> None:
        """调用 NotebookLM 或在 dry-run 下写占位结果。"""
        if self.config.dry_run:
            self._write(
                output,
                "一、检索内容\n\nDRY RUN：未调用 NotebookLM。\n\n"
                "二、相关文献\n\nDRY RUN：未调用 NotebookLM。\n",
            )
            return

        content = self.notebooklm.ask_notebook(
            notebook_id=self.notebook_id,
            prompt_file=self.run_dir / prompt,
        )
        self._write(output, content)

    def _ask_deepseek(
        self,
        prompt: str,
        output: str | Path,
        reasoning_effort: str | None = None,
    ) -> None:
        """调用 DeepSeek 或在 dry-run 下写占位结果。"""
        if self.config.dry_run:
            self._write(output, f"DRY RUN：未调用 DeepSeek。\n\n提示词长度：{len(prompt)}\n")
            return

        # 空响应几乎总是推理（thinking）烧穿 max_tokens（finish_reason=length），
        # 逐级降低推理强度重试：原参数 → effort=low → 关闭 thinking。
        attempt_kwargs: list[dict[str, object]] = [
            {"reasoning_effort": reasoning_effort},
            {"reasoning_effort": "low"},
            {"reasoning_effort": "low", "thinking_enabled": False},
        ]
        last_error: DeepSeekEmptyResponseError | None = None
        for attempt, kwargs in enumerate(attempt_kwargs):
            try:
                content = self.deepseek.ask(prompt, **kwargs)  # type: ignore[arg-type]
                break
            except DeepSeekEmptyResponseError as exc:
                last_error = exc
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"DeepSeek 降级重试 3 次仍返回空响应，任务中止：{last_error}")
        self._write(output, content)

    def _save_prompt(self, prompt_id: str, filename: str, **kwargs: str) -> Path:
        """生成并保存工程化提示词。"""
        content = prompt_builder.build_engineered_prompt(prompt_id, **kwargs)
        return self._write(Path("generated_prompts") / filename, content)

    def _save_generated_prompt(self, filename: str, content: str) -> Path:
        """保存运行中动态生成的提示词。"""
        return self._write(Path("generated_prompts") / filename, content)

    def _read(self, relative_path: str | Path) -> str:
        """读取运行目录内文本。"""
        return file_store.read_markdown(self.run_dir / relative_path)

    def _write(self, relative_path: str | Path, content: str) -> Path:
        """写入运行目录内文本。"""
        return file_store.write_markdown(self.run_dir / relative_path, content)

    def _read_review_template(self) -> str:
        """读取固定的全文内容结构审查模板。"""

        return prompt_builder.read_original_prompt(
            "workflow/review_templates/content_structure_review.md"
        )

    # ---- ch0 战略态势研判 + gated 注入钩子（无资产文件时零变化）----
    def _strategic_framing(self) -> None:
        """ch0：基于 1A/2A 检索材料产出「战略态势卡」，为全篇提供高位战略锚。"""
        template = (WORKFLOW_DIR / "prompts" / "strategic_framing.md").read_text(encoding="utf-8")
        material = "\n\n".join(
            [
                "【1A 顶层设计检索材料】",
                self._read("retrieval_outputs/chapter1_top_design.md"),
                "【2A 实施机制检索材料】",
                self._read("retrieval_outputs/chapter1_implementation.md"),
            ]
        )
        prompt = template.replace("{{topic}}", self.config.topic) + "\n\n【检索材料】\n\n" + material
        self._save_generated_prompt("ch0_strategic_framing.md", prompt)
        self._ask_deepseek(
            prompt, "extracted_materials/strategic_framing.md", reasoning_effort="max"
        )

    def _strategic_framing_text(self) -> str:
        path = self.run_dir / "extracted_materials" / "strategic_framing.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def _with_strategic_framing(self, prompt: str) -> str:
        text = self._strategic_framing_text()
        if not text.strip():
            return prompt
        return "\n\n".join(
            [
                prompt,
                "【战略态势卡（贯穿全文的高位战略锚；只可引用其中已溯源的高位政策事实，不得据此自造态势；本卡不预设类型划分，各小节分类由其写作模块按自身锁定的差异轴独立完成）】",
                text,
            ]
        )

    def _institution_profile_text(self) -> str:
        path = REPO_ROOT / "institution_profile.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def _with_institution_profile(self, prompt: str) -> str:
        text = self._institution_profile_text()
        if not text.strip():
            return prompt
        return "\n\n".join([prompt, "【机构定位与建议落点（建议必须落到教育域抓手）】", text])

    def _policy_style_dna_text(self, mode: str) -> str:
        mode_to_files = {
            "writing": ["voice.md", "structure.md", "sentence.md", "recommendation.md", "forbidden.md"],
            "review": ["voice.md", "structure.md", "forbidden.md", "recommendation.md", "self_check.md"],
            "revision": ["voice.md", "sentence.md", "forbidden.md", "recommendation.md", "self_check.md"],
        }
        files = list(mode_to_files.get(mode, mode_to_files["writing"]))
        files.append("subtype_a.md")
        blocks = []
        for name in files:
            path = REPO_ROOT / "policy_style_dna" / "wiki" / name
            if path.is_file():
                blocks.append(f"## {name}\n\n{path.read_text(encoding='utf-8')}")
        return "\n\n".join(blocks)

    def _with_policy_style_dna(self, prompt: str, mode: str) -> str:
        text = self._policy_style_dna_text(mode)
        if not text.strip():
            return prompt
        return "\n\n".join(
            [
                prompt,
                "【政策研究文风 DNA（只控写作姿态/结构/句式/审查标准，不作事实来源；不得新增其中政策事实/年份/机构/数据；正文不得输出文件名或分类过程）】",
                text,
            ]
        )

    def _reuse_materials(self) -> None:
        """复用指定 run 的 retrieval_outputs（盲跑），并把检索任务标记为已完成、跳过 NotebookLM。"""
        src = file_store.get_run_dir(self.config.reuse_materials_run) / "retrieval_outputs"
        dst = self.run_dir / "retrieval_outputs"
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob("*.md")):
            shutil.copyfile(f, dst / f.name)
        for task_id in ("ch1.1a.retrieve", "ch1.2a.retrieve", "ch1.3b.retrieve", "ch2.retrieve"):
            task_state.record_task_output(self.run_dir, task_id, output=self._task_output(task_id))

    def _refresh_task_state_notebook_id(self) -> None:
        """Notebook ID 解析后，更新 task_state.md 头部信息。"""
        state = task_state.load_task_state(self.run_dir)
        updated = task_state.TaskState(
            run_id=state.run_id,
            topic=state.topic,
            notebook_name=state.notebook_name,
            notebook_id=self.notebook_id,
            current_status=state.current_status,
            tasks=state.tasks,
            error_details=state.error_details,
        )
        file_store.write_markdown(
            self.run_dir / task_state.TASK_STATE_FILENAME,
            task_state.render_task_state(updated),
        )

    def _migrate_task_state_for_full_review(self) -> None:
        """恢复旧运行时补齐全文内容结构审查与修改任务。

        旧运行没有 `full.review` 和 `full.rewrite`。补齐后把归档任务放到最后，
        让 Codex 可以继续执行新增审核链条并重新生成运行日志。
        """

        state = task_state.load_task_state(self.run_dir)
        task_ids = {item.task_id for item in state.tasks}
        if "full.review" in task_ids and "full.rewrite" in task_ids:
            return

        review_done = (
            self.run_dir / "review_reports" / "fulltext_content_structure_review.md"
        ).exists()
        rewrite_done = (self.run_dir / "final_report_reviewed.md").exists()
        inserted = False
        updated_tasks: list[task_state.Task] = []

        def full_review_task(order: int) -> task_state.Task:
            """构造全文内容结构审查任务。"""

            return task_state.Task(
                order,
                "full.review",
                "全文内容结构审查",
                "审查",
                "DeepSeek v4 Pro",
                status="done" if review_done else "pending",
                input="final_report.md + 审查意见模板",
                output="review_reports/fulltext_content_structure_review.md",
            )

        def full_rewrite_task(order: int) -> task_state.Task:
            """构造全文内容结构修改任务。"""

            return task_state.Task(
                order,
                "full.rewrite",
                "全文内容结构修改",
                "写作/修改",
                "DeepSeek v4 Pro",
                status="done" if rewrite_done else "pending",
                input="final_report.md + 全文审查报告",
                output="final_report_reviewed.md",
            )

        for item in state.tasks:
            if item.task_id == "run.archive_log" and not inserted:
                next_order = item.order
                if "full.review" not in task_ids:
                    updated_tasks.append(full_review_task(next_order))
                    next_order += 1
                if "full.rewrite" not in task_ids:
                    updated_tasks.append(full_rewrite_task(next_order))
                    next_order += 1
                updated_tasks.append(
                    task_state.Task(
                        next_order,
                        item.task_id,
                        item.module,
                        item.function,
                        item.actor,
                        status="pending",
                        input=item.input,
                        output=item.output,
                    )
                )
                inserted = True
            else:
                updated_tasks.append(item)

        if not inserted:
            max_order = max((item.order for item in updated_tasks), default=0)
            if "full.review" not in task_ids:
                max_order += 1
                updated_tasks.append(full_review_task(max_order))
            if "full.rewrite" not in task_ids:
                max_order += 1
                updated_tasks.append(full_rewrite_task(max_order))

        updated = task_state.TaskState(
            run_id=state.run_id,
            topic=state.topic,
            notebook_name=state.notebook_name,
            notebook_id=state.notebook_id,
            current_status="running",
            tasks=tuple(updated_tasks),
            error_details=state.error_details,
        )
        file_store.write_markdown(
            self.run_dir / task_state.TASK_STATE_FILENAME,
            task_state.render_task_state(updated),
        )

    def _migrate_task_state_for_chapter3(self) -> None:
        """把旧运行中的第三章占位任务迁移为正式写作任务。

        早期运行只保存 `ch3.placeholder`。恢复旧运行时需要把它替换为
        `ch3.write`，并让最终组装和审查重新执行，确保最终报告读入正式第三章。
        """

        state = task_state.load_task_state(self.run_dir)
        task_ids = {item.task_id for item in state.tasks}
        if "ch3.write" in task_ids or "ch3.placeholder" not in task_ids:
            return

        chapter3_exists = (self.run_dir / "chapter_drafts" / "chapter3.md").exists()
        updated_tasks: list[task_state.Task] = []
        for item in state.tasks:
            if item.task_id == "ch3.placeholder":
                updated_tasks.append(
                    task_state.Task(
                        item.order,
                        "ch3.write",
                        "第三章政策建议写作",
                        "写作",
                        "DeepSeek v4 Pro",
                        status="done" if chapter3_exists else "pending",
                        input="chapter1.md + chapter2.md",
                        output="chapter_drafts/chapter3.md",
                    )
                )
            elif item.task_id in {"final.assemble", "final.review"}:
                updated_tasks.append(
                    task_state.Task(
                        item.order,
                        item.task_id,
                        item.module,
                        item.function,
                        item.actor,
                        status="pending",
                        input=item.input,
                        output=item.output,
                    )
                )
            else:
                updated_tasks.append(item)

        updated = task_state.TaskState(
            run_id=state.run_id,
            topic=state.topic,
            notebook_name=state.notebook_name,
            notebook_id=state.notebook_id,
            current_status="running",
            tasks=tuple(updated_tasks),
            error_details=state.error_details,
        )
        file_store.write_markdown(
            self.run_dir / task_state.TASK_STATE_FILENAME,
            task_state.render_task_state(updated),
        )

    def _split_retrieval_content(self, text: str) -> tuple[str, str]:
        """把检索结果拆成检索内容和相关文献。

        如果 NotebookLM 没有严格按标题输出，则全文作为检索内容，相关文献留空。
        """
        marker = "二、相关文献"
        if marker not in text:
            return text.strip(), "未单独列出；详见检索内容。"

        before, after = text.split(marker, 1)
        before = before.replace("一、检索内容", "", 1).strip()
        related = after.strip() or "未单独列出；详见检索内容。"
        return before, related

    def _postprocess_ch1_governance_draft(self, relative_path: str | Path) -> None:
        """清理第一章治理模式正文中不入稿的检索痕迹。"""

        text = self._read(relative_path)
        self._write(relative_path, self._clean_ch1_governance_text(text))

    def _clean_ch1_governance_text(self, text: str) -> str:
        """去掉数字引用序号和“分类依据”段落。

        NotebookLM 检索原文继续保留引用标记；这里只处理 DeepSeek 写作正文。
        """

        paragraphs = re.split(r"\n{2,}", text.strip())
        paragraphs = [
            paragraph.strip()
            for paragraph in paragraphs
            if not paragraph.lstrip().startswith("【分类依据】")
        ]
        cleaned = "\n\n".join(paragraphs)
        cleaned = re.sub(r"\[\d+\]", "", cleaned)
        cleaned = re.sub(r"\[\^\d+\]", "", cleaned)
        # 引用体例统一为课题组研究报告体：残留的"脚注[…]"式标注一律清除（兜底）。
        cleaned = re.sub(r"脚注\[[^\]]*\]", "", cleaned)
        cleaned = re.sub(r"(?m)^\[\^\d+\]:.*(?:\n|$)", "", cleaned)
        cleaned = re.sub(r"[ \t]+([，。；：、！？])", r"\1", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip() + "\n"

    def _ensure_ch1_topic_specific_heading(self, relative_path: str | Path) -> None:
        """确保第一章第三部分带有主题特性小标题。"""

        content = self._read(relative_path).strip()
        title = self._extract_ch1_topic_specific_title()
        heading = f"3. {title}"
        if content.startswith(heading):
            return
        if content.startswith("3. "):
            return
        self._write(relative_path, f"{heading}\n\n{content}\n")

    def _extract_ch1_topic_specific_title(self) -> str:
        """从 3A 构思产物中提取第一章第三部分小标题。"""

        title_text = self._read("extracted_materials/chapter1_topic_specific_title.md")
        first_line = next(
            (line.strip() for line in title_text.splitlines() if line.strip()),
            "主题特性专题",
        )
        title = re.sub(r"^\d+[.、]\s*", "", first_line)
        title = re.sub(r"[*_`#]", "", title).strip()
        return title or "主题特性专题"

    def _ensure_chapter2_heading(self, relative_path: str | Path) -> None:
        """确保第二章正文带有章标题。"""

        content = self._read(relative_path).strip()
        title = self._extract_chapter2_title()
        heading = f"# 第二章 {title}"
        if content.startswith("# 第二章"):
            cleaned = re.sub(
                r"^(# 第二章[^\n]*\n+)\*\*第二章[^*\n]*\*\*\s*",
                r"\1",
                content,
            )
            if cleaned != content:
                self._write(relative_path, cleaned.strip() + "\n")
            return
        content = re.sub(r"^\*\*第二章[^*\n]*\*\*\s*", "", content)
        self._write(relative_path, f"{heading}\n\n{content}\n")

    def _extract_chapter2_title(self) -> str:
        """从第二章主题构思产物中提取可入稿标题。"""

        topic_text = self._read("extracted_materials/chapter2_topic.md")
        match = re.search(r"第二章主题[:：]\s*(.+)", topic_text)
        if match:
            title = match.group(1).splitlines()[0]
        else:
            title = next(
                (line.strip() for line in topic_text.splitlines() if line.strip()),
                "待定主题",
            )
        title = re.sub(r"[*_`#]", "", title).strip()
        return title or "待定主题"

    def _build_review_prompt(self, chapter_name: str, draft: str, materials: str) -> str:
        """构造自然语言审查提示词。"""
        return f"""【角色与边界】
你是政策报告材料依据审查模块。你的任务不是润色，而是检查草稿是否被检索材料支撑。
只能依据传入的章节草稿和 NotebookLM 检索材料进行审查。
不要输出 JSON。

【审查对象】
{chapter_name}

【章节草稿】
{draft}

【NotebookLM 检索材料】
{materials}

【输出要求】
请输出自然语言审查报告，至少包括：
1. 总体结论：通过 / 需要修改 / 不通过。
2. 问题清单：逐条指出无依据、依据不足、文件名年份机构不一致、跨文件混写、材料未见却补写等问题。
3. 修改建议：删除、改写、补充检索或人工确认。
4. 若未发现明显问题，说明剩余风险。
"""

    def _task_output(self, task_id: str) -> str:
        """返回任务默认输出路径，用于 task_state.md。"""
        outputs = {
            "init.resolve_notebook": "notebook_resolution.md",
            "prompt.build_all": "generated_prompts/",
            "ch1.1a.retrieve": "retrieval_outputs/chapter1_top_design.md",
            "ch1.2a.retrieve": "retrieval_outputs/chapter1_implementation.md",
            "ch0.strategic_framing": "extracted_materials/strategic_framing.md",
            "ch1.1b.write": "chapter_drafts/chapter1_top_design.md",
            "ch1.2b.write": "chapter_drafts/chapter1_implementation.md",
            "ch1.3a.plan": "extracted_materials/chapter1_topic_specific_title.md",
            "ch1.3b.retrieve": "retrieval_outputs/chapter1_topic_specific.md",
            "ch1.3c.write": "chapter_drafts/chapter1_topic_specific.md",
            "ch1.assemble": "chapter_drafts/chapter1.md",
            "ch1.review": "review_reports/chapter1_review.md",
            "ch2.topic.plan": "extracted_materials/chapter2_topic.md",
            "ch2.retrieve": "retrieval_outputs/chapter2_materials.md",
            "ch2.dimension.plan": "extracted_materials/chapter2_dimensions.md",
            "ch2.write": "chapter_drafts/chapter2.md",
            "ch2.review": "review_reports/chapter2_review.md",
            "ch3.write": "chapter_drafts/chapter3.md",
            "final.assemble": "final_report.md",
            "final.review": "review_reports/final_review.md",
            "full.review": "review_reports/fulltext_content_structure_review.md",
            "full.rewrite": "final_report_reviewed.md",
            "run.archive_log": "run_log.md",
        }
        return outputs.get(task_id, "")

    def _task_status(self, task_id: str) -> str:
        """读取任务当前状态。"""
        state = task_state.load_task_state(self.run_dir)
        for item in state.tasks:
            if item.task_id == task_id:
                return item.status
        raise KeyError(f"未找到任务：{task_id}")

    def _load_notebook_id_from_state(self) -> str:
        """恢复运行时，从 task_state.md 读取 notebook id。"""
        state = task_state.load_task_state(file_store.get_run_dir(self.config.resume_run))
        return state.notebook_id
