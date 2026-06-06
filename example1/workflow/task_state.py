"""临时任务列表与运行日志模块。

状态文件采用 Markdown 保存，便于 Codex 和人工同时阅读；本模块负责把
Markdown 表格解析成任务对象，并在状态变化时重新写回文件。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Iterable

try:
    from .file_store import create_run_dir, markdown_path, read_markdown, write_markdown
except ImportError:  # 支持 `python workflow/runner.py` 这种脚本方式运行
    from file_store import create_run_dir, markdown_path, read_markdown, write_markdown


TASK_STATE_FILENAME = "task_state.md"
RUN_LOG_FILENAME = "run_log.md"
VALID_STATUSES = {"pending", "running", "done", "failed", "skipped", "blocked"}


@dataclass(frozen=True)
class Task:
    """单个工作流任务。"""

    order: int
    task_id: str
    module: str
    function: str
    actor: str
    status: str = "pending"
    input: str = ""
    output: str = ""
    error: str = ""


@dataclass(frozen=True)
class TaskState:
    """一次运行的任务状态。"""

    run_id: str
    topic: str = ""
    notebook_name: str = ""
    notebook_id: str = ""
    current_status: str = "running"
    tasks: tuple[Task, ...] = ()
    error_details: str = "暂无。"


DEFAULT_TASKS: tuple[Task, ...] = (
    Task(1, "init.resolve_notebook", "解析知识库", "编排", "Codex", input="input.yaml", output="notebook_resolution.md"),
    Task(2, "prompt.build_all", "拼装提示词", "拼装", "Codex", input="原始提示词", output="generated_prompts/"),
    Task(3, "ch1.1a.retrieve", "1A 顶层设计检索", "检索", "NotebookLM skill", input="generated_prompts/ch1_1a.md", output="retrieval_outputs/chapter1_top_design.md"),
    Task(4, "ch1.2a.retrieve", "2A 实施机制检索", "检索", "NotebookLM skill", input="generated_prompts/ch1_2a.md", output="retrieval_outputs/chapter1_implementation.md"),
    Task(5, "ch1.1b.write", "1B 顶层设计写作", "写作", "DeepSeek v4 Pro", input="1A 检索结果", output="chapter_drafts/chapter1_top_design.md"),
    Task(6, "ch1.2b.write", "2B 实施机制写作", "写作", "DeepSeek v4 Pro", input="2A 检索结果", output="chapter_drafts/chapter1_implementation.md"),
    Task(7, "ch1.3a.plan", "3A 主题特性定题", "构思", "DeepSeek v4 Pro", input="topic", output="extracted_materials/chapter1_topic_specific_title.md"),
    Task(8, "ch1.3b.retrieve", "3B 主题特性检索", "检索", "NotebookLM skill", input="3A 构思产物", output="retrieval_outputs/chapter1_topic_specific.md"),
    Task(9, "ch1.3c.write", "3C 主题特性写作", "写作", "DeepSeek v4 Pro", input="3B 检索结果", output="chapter_drafts/chapter1_topic_specific.md"),
    Task(10, "ch1.assemble", "第一章组装", "编排", "Codex", input="第一章小节草稿", output="chapter_drafts/chapter1.md"),
    Task(11, "ch1.review", "第一章审查", "审查", "DeepSeek v4 Pro", input="chapter1.md + 检索材料", output="review_reports/chapter1_review.md"),
    Task(12, "ch2.topic.plan", "第二章目的层定题", "构思", "DeepSeek v4 Pro", input="topic", output="extracted_materials/chapter2_topic.md"),
    Task(13, "ch2.retrieve", "第二章资料铺料", "检索", "NotebookLM skill", input="第二章主题", output="retrieval_outputs/chapter2_materials.md"),
    Task(14, "ch2.dimension.plan", "第二章维度凝练", "构思", "DeepSeek v4 Pro", input="第二章检索结果", output="extracted_materials/chapter2_dimensions.md"),
    Task(15, "ch2.write", "第二章正文写作", "写作", "DeepSeek v4 Pro", input="第二章检索结果 + 维度", output="chapter_drafts/chapter2.md"),
    Task(16, "ch2.review", "第二章审查", "审查", "DeepSeek v4 Pro", input="chapter2.md + 检索材料", output="review_reports/chapter2_review.md"),
    Task(17, "ch3.write", "第三章政策建议写作", "写作", "DeepSeek v4 Pro", input="chapter1.md + chapter2.md", output="chapter_drafts/chapter3.md"),
    Task(18, "final.assemble", "报告组装", "编排", "Codex", input="chapter_drafts/", output="final_report.md"),
    Task(19, "final.review", "最终审查", "审查", "DeepSeek v4 Pro", input="final_report.md + 检索材料", output="review_reports/final_review.md"),
    Task(20, "run.archive_log", "归档运行日志", "编排", "Codex", input="task_state.md", output="run_log.md"),
)


def start_run(
    topic: str = "",
    notebook_name: str = "",
    notebook_id: str = "",
    run_id: str | None = None,
    tasks: Iterable[Task] | None = None,
) -> tuple[str, Path]:
    """创建运行目录，并生成初始 task_state.md。"""

    actual_run_id, run_dir = create_run_dir(run_id)
    create_task_state(
        run_dir=run_dir,
        run_id=actual_run_id,
        topic=topic,
        notebook_name=notebook_name,
        notebook_id=notebook_id,
        tasks=tasks,
    )
    return actual_run_id, run_dir


def create_task_state(
    run_dir: str | Path,
    run_id: str,
    topic: str = "",
    notebook_name: str = "",
    notebook_id: str = "",
    tasks: Iterable[Task] | None = None,
    current_status: str = "running",
) -> Path:
    """写入初始临时任务列表。"""

    _validate_status(current_status)
    state = TaskState(
        run_id=run_id,
        topic=topic,
        notebook_name=notebook_name,
        notebook_id=notebook_id,
        current_status=current_status,
        tasks=tuple(tasks or DEFAULT_TASKS),
    )
    return _save_state(run_dir, state)


def load_task_state(run_dir: str | Path) -> TaskState:
    """读取并解析 task_state.md。"""

    path = markdown_path(run_dir, TASK_STATE_FILENAME)
    return parse_task_state(read_markdown(path))


def parse_task_state(content: str) -> TaskState:
    """从 Markdown 文本解析任务状态。"""

    lines = content.splitlines()
    meta = {
        "run_id": "",
        "topic": "",
        "notebook_name": "",
        "notebook_id": "",
        "current_status": "running",
    }
    tasks: list[Task] = []
    in_table = False
    error_details: list[str] = []
    in_errors = False

    for line in lines:
        if line.startswith("运行 ID："):
            meta["run_id"] = line.removeprefix("运行 ID：").strip()
        elif line.startswith("报告主题："):
            meta["topic"] = line.removeprefix("报告主题：").strip()
        elif line.startswith("知识库名称："):
            meta["notebook_name"] = line.removeprefix("知识库名称：").strip()
        elif line.startswith("Notebook ID："):
            meta["notebook_id"] = line.removeprefix("Notebook ID：").strip()
        elif line.startswith("当前状态："):
            meta["current_status"] = line.removeprefix("当前状态：").strip()
        elif line == "## 错误详情":
            in_errors = True
            in_table = False
            continue

        if in_errors:
            error_details.append(line)
            continue

        if line.startswith("| 序号 |"):
            in_table = True
            continue
        if in_table and line.startswith("| ---"):
            continue
        if in_table and line.startswith("|"):
            tasks.append(_parse_task_row(line))
        elif in_table and not line.strip():
            in_table = False

    current_status = meta["current_status"] or "running"
    _validate_status(current_status)

    return TaskState(
        run_id=meta["run_id"],
        topic=meta["topic"],
        notebook_name=meta["notebook_name"],
        notebook_id=meta["notebook_id"],
        current_status=current_status,
        tasks=tuple(tasks),
        error_details="\n".join(error_details).strip() or "暂无。",
    )


def next_pending_task(run_dir: str | Path) -> Task | None:
    """返回第一个 pending 任务；如果没有则返回 None。"""

    state = load_task_state(run_dir)
    return next((task for task in state.tasks if task.status == "pending"), None)


def update_task_status(
    run_dir: str | Path,
    task_id: str,
    status: str,
    output: str | None = None,
    error_summary: str | None = None,
) -> Path:
    """更新单个任务状态，可同时更新输出和错误摘要。"""

    _validate_status(status)
    state = load_task_state(run_dir)
    updated_tasks = []
    found = False

    for task in state.tasks:
        if task.task_id == task_id:
            found = True
            updated_tasks.append(
                replace(
                    task,
                    status=status,
                    output=task.output if output is None else output,
                    error=task.error if error_summary is None else error_summary,
                )
            )
        else:
            updated_tasks.append(task)

    if not found:
        raise KeyError(f"未找到任务：{task_id}")

    return _save_state(run_dir, replace(state, tasks=tuple(updated_tasks)))


def record_task_output(run_dir: str | Path, task_id: str, output: str, status: str = "done") -> Path:
    """记录任务输出，并默认将任务标记为 done。"""

    return update_task_status(run_dir, task_id, status=status, output=output, error_summary="")


def record_task_error(
    run_dir: str | Path,
    task_id: str,
    error_summary: str,
    status: str = "failed",
    command: str = "",
    saved_output: str = "",
    suggestion: str = "重试 / 人工确认 / 跳过 / 修改输入",
) -> Path:
    """记录错误摘要和完整错误详情。"""

    if status not in {"failed", "blocked"}:
        raise ValueError("错误详情只支持 failed 或 blocked 状态")

    state = load_task_state(run_dir)
    updated_tasks = []
    found = False

    for task in state.tasks:
        if task.task_id == task_id:
            found = True
            updated_tasks.append(replace(task, status=status, error=error_summary))
        else:
            updated_tasks.append(task)

    if not found:
        raise KeyError(f"未找到任务：{task_id}")

    details = _append_error_details(
        state.error_details,
        task_id=task_id,
        status=status,
        error_summary=error_summary,
        command=command,
        saved_output=saved_output,
        suggestion=suggestion,
    )
    return _save_state(run_dir, replace(state, tasks=tuple(updated_tasks), error_details=details))


def archive_run_log(
    run_dir: str | Path,
    final_status: str = "done",
    final_outputs: Iterable[str] | None = None,
    review_passed: bool | None = None,
) -> Path:
    """生成并归档 run_log.md。

    如果任务列表中存在 run.archive_log，会在归档前将其标记为 done。
    """

    _validate_status(final_status)
    state = load_task_state(run_dir)
    tasks = tuple(
        replace(task, status="done", output=RUN_LOG_FILENAME)
        if task.task_id == "run.archive_log" and task.status != "done"
        else task
        for task in state.tasks
    )
    state = replace(state, current_status=final_status, tasks=tasks)
    _save_state(run_dir, state)

    log_path = markdown_path(run_dir, RUN_LOG_FILENAME)
    write_markdown(log_path, render_run_log(state, final_outputs=final_outputs, review_passed=review_passed))
    return log_path


def render_task_state(state: TaskState) -> str:
    """渲染 task_state.md 内容。"""

    rows = "\n".join(_render_task_row(task) for task in state.tasks)
    return f"""# 临时任务列表

运行 ID：{state.run_id}
报告主题：{state.topic}
知识库名称：{state.notebook_name}
Notebook ID：{state.notebook_id}
当前状态：{state.current_status}

## 任务列表

| 序号 | 任务 ID | 模块 | 功能 | 执行者 | 状态 | 输入 | 输出 | 错误记录 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{rows}

## 错误详情

{state.error_details or "暂无。"}
"""


def render_run_log(
    state: TaskState,
    final_outputs: Iterable[str] | None = None,
    review_passed: bool | None = None,
) -> str:
    """渲染归档运行日志。"""

    outputs = tuple(final_outputs or _collect_outputs(state.tasks))
    output_lines = "\n".join(f"- {item}" for item in outputs) if outputs else "- 未记录"
    review_text = "未记录" if review_passed is None else ("是" if review_passed else "否")
    task_rows = "\n".join(_render_task_row(task) for task in state.tasks)

    return f"""# 运行日志

运行 ID：{state.run_id}
报告主题：{state.topic}
知识库名称：{state.notebook_name}
Notebook ID：{state.notebook_id}
最终状态：{state.current_status}
归档时间：{_now_text()}

## Notebook 解析结果

- 知识库名称：{state.notebook_name or "未记录"}
- Notebook ID：{state.notebook_id or "未记录"}

## 任务最终状态

| 序号 | 任务 ID | 模块 | 功能 | 执行者 | 状态 | 输入 | 输出 | 错误记录 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{task_rows}

## 错误和重试记录

{state.error_details or "暂无。"}

## 最终产物列表

{output_lines}

## 是否完整通过审查

{review_text}
"""


def _save_state(run_dir: str | Path, state: TaskState) -> Path:
    path = markdown_path(run_dir, TASK_STATE_FILENAME)
    write_markdown(path, render_task_state(state))
    return path


def _validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"不支持的任务状态：{status}")


def _render_task_row(task: Task) -> str:
    return (
        f"| {task.order} | {_escape_cell(task.task_id)} | {_escape_cell(task.module)} | "
        f"{_escape_cell(task.function)} | {_escape_cell(task.actor)} | {_escape_cell(task.status)} | "
        f"{_escape_cell(task.input)} | {_escape_cell(task.output)} | {_escape_cell(task.error)} |"
    )


def _parse_task_row(line: str) -> Task:
    cells = [_unescape_cell(cell.strip()) for cell in _split_markdown_row(line)]
    if len(cells) != 9:
        raise ValueError(f"任务表格列数不正确：{line}")

    status = cells[5]
    _validate_status(status)
    return Task(
        order=int(cells[0]),
        task_id=cells[1],
        module=cells[2],
        function=cells[3],
        actor=cells[4],
        status=status,
        input=cells[6],
        output=cells[7],
        error=cells[8],
    )


def _split_markdown_row(line: str) -> list[str]:
    """拆分 Markdown 表格行，支持使用反斜杠转义竖线。"""

    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in stripped:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
            current.append(char)
        elif char == "|":
            cells.append("".join(current))
            current = []
        else:
            current.append(char)
    cells.append("".join(current))
    return cells


def _escape_cell(value: str) -> str:
    return str(value).replace("\n", "<br>").replace("|", r"\|")


def _unescape_cell(value: str) -> str:
    return value.replace(r"\|", "|").replace("<br>", "\n")


def _append_error_details(
    current: str,
    task_id: str,
    status: str,
    error_summary: str,
    command: str,
    saved_output: str,
    suggestion: str,
) -> str:
    base = "" if current.strip() == "暂无。" else current.rstrip()
    entry = f"""
### {task_id}

- 时间：{_now_text()}
- 状态：{status}
- 错误摘要：{error_summary}
- 触发命令或调用：{command or "未记录"}
- 已保存输出：{saved_output or "未记录"}
- 下一步建议：{suggestion}
""".strip()
    return f"{base}\n\n{entry}".strip()


def _collect_outputs(tasks: Iterable[Task]) -> tuple[str, ...]:
    seen: set[str] = set()
    outputs: list[str] = []
    for task in tasks:
        if task.status == "done" and task.output and task.output not in seen:
            seen.add(task.output)
            outputs.append(task.output)
    return tuple(outputs)


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
