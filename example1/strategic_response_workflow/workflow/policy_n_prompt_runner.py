"""政策N提示词组对照运行入口。

本脚本用于完整试跑用户提供的“政策N + 历史关联 + 对策建议”提示词组。
它不替换主工作流，只生成一版可比较的对照稿。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
from llm_client import create_llm_client
from notebooklm_client import NotebookLMClient


PROMPT_SET_DIR = WORKFLOW_ROOT / "imported_prompts" / "zhongmei_talent_policy_n"

PROMPT_FILES = {
    "module0": "模块0：前置声明与角色锚定.txt",
    "a1": "模块A1：政策核心举措·检索.txt",
    "a2": "模块A2：历史关联政策·检索.txt",
    "a3": "模块A3：对策建议素材·检索.txt",
    "b1": "模块B1：核心举措·归类加写作（内嵌思维链）.txt",
    "b2": "模块B2：历史镜鉴·归类加写作.txt",
    "b3": "模块B3：政策建议·归类加写作.txt",
    "c": "模块C：终审与质量校验.txt",
}

TASKS = [
    ("init", "初始化运行目录", "编排"),
    ("resolve_notebook", "解析 NotebookLM 知识库", "编排"),
    ("copy_prompt_set", "复制提示词组快照", "编排"),
    ("build_a1_prompt", "拼装A1检索提示词", "拼装"),
    ("retrieve_a1", "检索政策核心举措", "检索"),
    ("build_a2_prompt", "拼装A2历史关联提示词", "拼装"),
    ("retrieve_a2", "检索历史关联政策", "检索"),
    ("build_a3_prompt", "拼装A3建议素材提示词", "拼装"),
    ("retrieve_a3", "检索对策建议素材", "检索"),
    ("write_b1", "写作第一部分", "写作"),
    ("write_b2", "写作第二部分", "写作"),
    ("write_b3", "写作第三部分", "写作"),
    ("assemble_article", "合成完整稿", "编排"),
    ("review_c", "终审与质量校验", "审查"),
    ("export_docx", "导出 Word 文档", "编排"),
    ("archive_log", "归档运行日志", "编排"),
]


@dataclass(frozen=True)
class Config:
    """命令行输入配置。"""

    topic: str
    target_country: str
    domain: str
    notebook_name: str
    llm_provider: str
    dry_run: bool = False


class PolicyNPromptPipeline:
    """完整执行“政策N提示词组”的对照流程。"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.run_id = self._make_run_id()
        self.run_dir = WORKFLOW_ROOT / "runs" / self.run_id
        self.notebook_id = ""
        self.llm = None if config.dry_run else create_llm_client(config.llm_provider)
        self.notebooklm = NotebookLMClient(cwd=WORKFLOW_ROOT)
        self.completed_tasks: set[str] = set()
        self.failed_tasks: set[str] = set()

    def run(self) -> None:
        """执行完整对照流程。"""

        try:
            self._run_task("init", self._init_run)
            self._run_task("resolve_notebook", self._resolve_notebook)
            self._run_task("copy_prompt_set", self._copy_prompt_set)
            self._run_task("build_a1_prompt", self._build_a1_prompt)
            self._run_task("retrieve_a1", self._retrieve_a1)
            self._run_task("build_a2_prompt", self._build_a2_prompt)
            self._run_task("retrieve_a2", self._retrieve_a2)
            self._run_task("build_a3_prompt", self._build_a3_prompt)
            self._run_task("retrieve_a3", self._retrieve_a3)
            self._run_task("write_b1", self._write_b1)
            self._run_task("write_b2", self._write_b2)
            self._run_task("write_b3", self._write_b3)
            self._run_task("assemble_article", self._assemble_article)
            self._run_task("review_c", self._review_c)
            self._run_task("export_docx", self._export_docx)
        finally:
            self._run_task("archive_log", self._archive_log, stop_on_error=False)

    def _init_run(self) -> None:
        """创建运行目录和临时任务列表。"""

        for folder in [
            "prompt_set_snapshot",
            "generated_prompts",
            "retrieval_outputs",
            "drafts",
            "review_reports",
            "logs",
        ]:
            (self.run_dir / folder).mkdir(parents=True, exist_ok=True)

        self._write(
            "input.yaml",
            "\n".join(
                [
                    'workflow_type: "policy_n_prompt_set"',
                    f'topic: "{self.config.topic}"',
                    f'target_country: "{self.config.target_country}"',
                    f'domain: "{self.config.domain}"',
                    f'notebook_name: "{self.config.notebook_name}"',
                    f'llm_provider: "{self.config.llm_provider}"',
                ]
            ),
        )
        self._render_task_state("init")

    def _resolve_notebook(self) -> None:
        """解析 NotebookLM 知识库。"""

        if self.config.dry_run:
            self.notebook_id = "DRY_RUN_NOTEBOOK_ID"
        else:
            self.notebooklm.check_auth()
            notebook = self.notebooklm.find_notebook(self.config.notebook_name)
            self.notebook_id = notebook.id

        self._write(
            "notebook_resolution.md",
            "# Notebook 解析结果\n\n"
            f"- 知识库名称：{self.config.notebook_name}\n"
            f"- Notebook ID：{self.notebook_id}\n",
        )

    def _copy_prompt_set(self) -> None:
        """把提示词组复制为本次运行快照，保证可复查。"""

        for filename in PROMPT_FILES.values():
            source = PROMPT_SET_DIR / filename
            if not source.is_file():
                raise FileNotFoundError(f"缺少提示词文件: {source}")
            shutil.copyfile(source, self.run_dir / "prompt_set_snapshot" / filename)

    def _build_a1_prompt(self) -> None:
        """拼装A1检索提示词。"""

        prompt = self._compose_prompt(
            "a1",
            [
                "【执行要求】",
                "请从知识库中识别目标国家在本领域最新或最核心的政策文件、战略文件、法案、报告或政策组合，作为“政策N”处理。",
                "如果知识库中并非单一文件，而是多份文件共同构成战略布局，请明确写作“政策N组合”，但仍按A1结构输出。",
            ],
        )
        self._write("generated_prompts/a1_retrieval.md", prompt)

    def _retrieve_a1(self) -> None:
        """调用 NotebookLM 检索政策核心举措。"""

        self._ask_notebook("generated_prompts/a1_retrieval.md", "retrieval_outputs/a1_policy_measures.md")

    def _build_a2_prompt(self) -> None:
        """拼装A2历史关联检索提示词。"""

        prompt = self._compose_prompt(
            "a2",
            [
                "【A1检索结果】",
                self._read("retrieval_outputs/a1_policy_measures.md"),
                "【执行要求】",
                "请严格根据A1中出现的历史关联线索判断是否触发A2。",
                "若未发现明确历史政策关联，请直接说明“未触发A2”，不要主动扩展历史政策。",
            ],
        )
        self._write("generated_prompts/a2_history_retrieval.md", prompt)

    def _retrieve_a2(self) -> None:
        """调用 NotebookLM 检索历史关联政策。"""

        self._ask_notebook("generated_prompts/a2_history_retrieval.md", "retrieval_outputs/a2_history_policy.md")

    def _build_a3_prompt(self) -> None:
        """拼装A3对策建议素材检索提示词。"""

        prompt = self._compose_prompt(
            "a3",
            [
                "【A1检索结果】",
                self._read("retrieval_outputs/a1_policy_measures.md"),
                "【A2检索结果】",
                self._read("retrieval_outputs/a2_history_policy.md"),
                "【执行要求】",
                "请围绕前文比较发现、本国现实短板、国家战略导向检索建议素材；只输出素材，不直接写成政策建议正文。",
            ],
        )
        self._write("generated_prompts/a3_suggestion_retrieval.md", prompt)

    def _retrieve_a3(self) -> None:
        """调用 NotebookLM 检索建议素材。"""

        self._ask_notebook("generated_prompts/a3_suggestion_retrieval.md", "retrieval_outputs/a3_suggestion_materials.md")

    def _write_b1(self) -> None:
        """基于A1写作第一部分。"""

        prompt = self._compose_prompt(
            "b1",
            [
                "【附件报告/示例风格】",
                self._read_workflow("source/sample.md"),
                "【A1产出的政策N核心举措素材】",
                self._read("retrieval_outputs/a1_policy_measures.md"),
                "【输出边界】",
                "只输出B1模块要求的“一、主要措施”正文及其模块原要求的附加核查信息。",
            ],
        )
        self._write("generated_prompts/b1_writing.md", prompt)
        self._ask_llm(prompt, "drafts/part1_main_measures.md")

    def _write_b2(self) -> None:
        """基于A2写作第二部分。"""

        prompt = self._compose_prompt(
            "b2",
            [
                "【附件报告/示例风格】",
                self._read_workflow("source/sample.md"),
                "【A2产出的历史关联政策素材】",
                self._read("retrieval_outputs/a2_history_policy.md"),
                "【输出边界】",
                "若A2明确未触发，请不要虚构历史政策，可按模块0要求压缩为背景分析；否则输出B2模块要求的第二部分正文及其模块原要求的附加核查信息。",
            ],
        )
        self._write("generated_prompts/b2_writing.md", prompt)
        self._ask_llm(prompt, "drafts/part2_history_or_background.md")

    def _write_b3(self) -> None:
        """基于前文和A3写作第三部分。"""

        prompt = self._compose_prompt(
            "b3",
            [
                "【附件报告/示例风格】",
                self._read_workflow("source/sample.md"),
                "【前文第一部分】",
                self._read("drafts/part1_main_measures.md"),
                "【前文第二部分】",
                self._read("drafts/part2_history_or_background.md"),
                "【A3产出的对策建议素材】",
                self._read("retrieval_outputs/a3_suggestion_materials.md"),
                "【输出边界】",
                "只输出B3模块要求的“三、政策建议”正文及其模块原要求的附加核查信息。",
            ],
        )
        self._write("generated_prompts/b3_writing.md", prompt)
        self._ask_llm(prompt, "drafts/part3_policy_suggestions.md")

    def _assemble_article(self) -> None:
        """合成完整文章。"""

        article = "\n\n".join(
            [
                f"# {self.config.topic}",
                self._read("drafts/part1_main_measures.md"),
                self._read("drafts/part2_history_or_background.md"),
                self._read("drafts/part3_policy_suggestions.md"),
            ]
        )
        self._write("final_article_policy_n_prompt_set.md", article)

    def _review_c(self) -> None:
        """执行C模块终审。"""

        prompt = self._compose_prompt(
            "c",
            [
                "【附件报告/示例风格】",
                self._read_workflow("source/sample.md"),
                "【待终审文章】",
                self._read("final_article_policy_n_prompt_set.md"),
                "【输出要求】",
                "请输出逐项终审意见、主要问题、可保留优点和明确总体结论。",
            ],
        )
        self._write("generated_prompts/c_final_review.md", prompt)
        self._ask_llm(prompt, "review_reports/c_final_review.md")

    def _export_docx(self) -> None:
        """导出 Word 文档。"""

        source = self.run_dir / "final_article_policy_n_prompt_set.md"
        target = self.run_dir / "final_article_policy_n_prompt_set.docx"
        if self.config.dry_run:
            self._write("final_article_policy_n_prompt_set.docx.txt", "DRY RUN：未导出 docx。")
            return
        subprocess.run(["pandoc", str(source), "-o", str(target)], check=True)

    def _archive_log(self) -> None:
        """归档运行日志。"""

        outputs = [
            "retrieval_outputs/a1_policy_measures.md",
            "retrieval_outputs/a2_history_policy.md",
            "retrieval_outputs/a3_suggestion_materials.md",
            "drafts/part1_main_measures.md",
            "drafts/part2_history_or_background.md",
            "drafts/part3_policy_suggestions.md",
            "final_article_policy_n_prompt_set.md",
            "final_article_policy_n_prompt_set.docx",
            "review_reports/c_final_review.md",
        ]
        existing = [item for item in outputs if (self.run_dir / item).exists()]
        self._write(
            "run_log.md",
            "# 政策N提示词组对照运行日志\n\n"
            f"- 运行 ID：{self.run_id}\n"
            f"- 主题：{self.config.topic}\n"
            f"- 目标国家：{self.config.target_country}\n"
            f"- 领域：{self.config.domain}\n"
            f"- 知识库：{self.config.notebook_name}\n"
            f"- LLM 后端：{self.config.llm_provider}\n"
            f"- 归档时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "## 产物\n\n"
            + "\n".join(f"- {item}" for item in existing)
            + "\n",
        )
        self._render_task_state("archive_log", done=True)

    def _compose_prompt(self, module_key: str, blocks: list[str]) -> str:
        """把模块0、运行参数、目标模块和上下文材料拼装为完整提示词。"""

        module0 = self._fill_common(self._read_prompt("module0"))
        module = self._fill_common(self._read_prompt(module_key))
        return "\n\n".join(
            [
                "【本次运行参数】",
                f"- 报告题目：{self.config.topic}",
                f"- 目标国家/经济体：{self.config.target_country}",
                f"- 研究领域：{self.config.domain}",
                "- 本国立场：中国",
                f"- NotebookLM 知识库：{self.config.notebook_name}",
                module0,
                module,
                *blocks,
            ]
        )

    def _ask_notebook(self, prompt: str, output: str) -> None:
        """调用 NotebookLM；dry-run 时写占位内容。"""

        if self.config.dry_run:
            self._write(output, "DRY RUN：未调用 NotebookLM。\n")
            return
        content = self.notebooklm.ask_notebook(self.notebook_id, self.run_dir / prompt)
        self._write(output, content)

    def _ask_llm(self, prompt: str, output: str) -> None:
        """调用文本生成模型；dry-run 时写占位内容。"""

        if self.config.dry_run:
            self._write(output, f"DRY RUN：未调用 {self.config.llm_provider}。\n提示词长度：{len(prompt)}\n")
            return
        if self.llm is None:
            raise RuntimeError("LLM 客户端未初始化")
        self._write(output, self.llm.ask(prompt))

    def _fill_common(self, text: str) -> str:
        """替换提示词中的通用占位符。"""

        return (
            text.replace("【主题】", self.config.domain)
            .replace("目标国家", self.config.target_country)
            .replace("政策N", "政策N")
        )

    def _run_task(self, task_id: str, func, stop_on_error: bool = True) -> None:
        """执行单个任务并记录状态。"""

        self._render_task_state(task_id)
        try:
            func()
        except Exception:  # noqa: BLE001 - 工作流需要把完整异常落盘
            self._write(f"logs/{task_id}_traceback.md", traceback.format_exc())
            self.failed_tasks.add(task_id)
            self._render_task_state(task_id, failed=True)
            if stop_on_error:
                raise
        else:
            self.completed_tasks.add(task_id)
            self._render_task_state(task_id)

    def _render_task_state(self, current_task: str, done: bool = False, failed: bool = False) -> None:
        """写入当前临时任务状态。"""

        rows = []
        for task_id, name, function in TASKS:
            status = "pending"
            if done or task_id in self.completed_tasks:
                status = "done"
            elif task_id in self.failed_tasks:
                status = "failed"
            elif task_id == current_task:
                status = "failed" if failed else "running"
            rows.append(f"| {task_id} | {name} | {function} | {status} |")

        self._write(
            "task_state.md",
            "# 临时任务列表\n\n"
            f"- 运行 ID：{self.run_id}\n"
            f"- 主题：{self.config.topic}\n"
            f"- 目标国家：{self.config.target_country}\n"
            f"- 领域：{self.config.domain}\n\n"
            "| 任务 ID | 模块 | 功能 | 状态 |\n"
            "| --- | --- | --- | --- |\n"
            + "\n".join(rows)
            + "\n",
        )

    def _read_prompt(self, key: str) -> str:
        return (PROMPT_SET_DIR / PROMPT_FILES[key]).read_text(encoding="utf-8")

    def _read(self, relative_path: str) -> str:
        return (self.run_dir / relative_path).read_text(encoding="utf-8")

    def _read_workflow(self, relative_path: str) -> str:
        return (WORKFLOW_ROOT / relative_path).read_text(encoding="utf-8")

    def _write(self, relative_path: str, content: str) -> Path:
        path = self.run_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _make_run_id() -> str:
        return f"policy-n-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description="政策N提示词组对照工作流")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--target-country", default="美国")
    parser.add_argument("--domain", default="AI人才")
    parser.add_argument("--notebook-name", required=True)
    parser.add_argument(
        "--llm-provider",
        default="deepseek",
        choices=["deepseek", "anthropic_compat"],
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    """启动对照流程。"""

    args = parse_args()
    config = Config(
        topic=args.topic,
        target_country=args.target_country,
        domain=args.domain,
        notebook_name=args.notebook_name,
        llm_provider=args.llm_provider,
        dry_run=args.dry_run,
    )
    PolicyNPromptPipeline(config).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
