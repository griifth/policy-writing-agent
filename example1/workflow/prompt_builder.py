"""工程化提示词拼装模块。

本模块只负责读取原始提示词副本、替换主题占位符、拼装工程化提示词，
并把生成结果写入运行目录的 generated_prompts/ 下。原始提示词文件保持只读。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# 通用输出约束来自 workflow/prompts/*.md。这里内置为稳定常量，调用方不需要再读取说明文档。
RETRIEVAL_OUTPUT_CONTRACT = """请只输出以下两部分：

一、检索内容
按照原始提示词要求罗列检索材料。
尽量保留来源主体、文件名称、年份、具体做法或关键表述、引用标记。
不同来源主体、不同文件、不同举措尽量拆开写，不要为了简洁而合并。
如果知识库未见相关内容，直接写“未见”。
本部分只做检索和铺料，不做分类、不归纳维度、不写对比结论、不提出对策。

二、相关文献
集中列出本次检索命中的相关文献。
每条尽量包含：来源主体、文件名称、年份、发布机构、引用标记。
相关文献只需集中列出，不需要与“一、检索内容”逐条对应。"""


PLANNING_OUTPUT_CONTRACT = """只输出构思产物。
不要输出正文。
不要输出写作说明。
不要输出思考过程。
不要输出 JSON。
如果材料或输入不足，请在构思产物中直接标注“材料不足”或“需要人工确认”。"""


WRITING_OUTPUT_CONTRACT = """只输出可直接入稿的正文内容。
不要输出写作说明。
不要输出构思过程。
不要输出审查意见。
不要输出思考过程。
不要输出 JSON。
不要保留 NotebookLM 检索材料中的数字引用序号，例如 [1]、[2][3]。
正文严禁出现暴露原始材料/检索来源的字样与标签：“【素材来源：…】”、直接写出的 .pdf 文件名、“根据材料/材料显示/据材料/材料[编号]/检索材料表明”等一律不得入文（忠于材料即可，不把来源标签写进正文）。
不要输出“【分类依据】”段落；分类依据只用于内部构思，不进入正式正文。
不得引入外部知识。
不得补写材料中不存在的国家、机构、文件、年份或政策举措。
文件名、机构名、年份、举措必须与传入材料保持一致。
如果材料缺失，不要编造；可以不写该内容，或在必要处标注“材料不足”。"""


REVIEW_OUTPUT_CONTRACT = """只输出审查报告。
不要输出修改后的全文。
不要输出思考过程。
不要输出 JSON。
不要处理引用编号、参考文献格式、脚注尾注格式、文件来源格式等引用类问题。
审查重点必须放在全文内容、章节结构、比较逻辑、论证链条、政策建议落点和政策研究文体上。
指出问题时尽量定位到章节、标题或段落，并说明为什么会影响报告质量。
如果未发现明显问题，也要说明剩余风险。"""


REVISION_OUTPUT_CONTRACT = """只输出修改后的完整报告正文。
不要输出修改说明。
不要输出审查意见。
不要输出思考过程。
不要输出 JSON。
不得新增未经原文或 NotebookLM 检索材料支撑的国外政策事实。
不得处理或改写引用编号、参考文献格式、脚注尾注格式、文件来源格式等引用类问题。
但必须删除正文中暴露原始材料/检索来源的字样与标签：“【素材来源：…】”、.pdf 文件名、“根据材料/材料显示/据材料/材料[编号]/检索材料表明”等（这属越界内容，须清除，不在上述“不处理的引用格式”范畴内）。
可以调整标题、小标题、段落顺序、过渡句、总起句和政策建议表达。
修改目标是让全文结构更清晰、论证链条更完整、政策建议更能体现“从国际经验中来、到中国问题中去”。"""


@dataclass(frozen=True)
class PromptSpec:
    """单个工程化提示词任务的配置。"""

    prompt_type: str
    original_path: str
    input_builder: Callable[[Mapping[str, str]], str]
    output_contract: str
    original_transform: Callable[[str, Mapping[str, str]], str]
    default_filename: str


def _require_value(values: Mapping[str, str], key: str) -> str:
    """读取必填参数，避免生成带空洞的提示词。"""

    value = values.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"缺少必填参数：{key}")
    return str(value)


def _optional_value(values: Mapping[str, str], key: str) -> str:
    """读取可选参数，未传时返回空字符串。"""

    value = values.get(key)
    if value is None:
        return ""
    return str(value)


def _resolve_project_path(relative_path: str | Path) -> Path:
    """把项目内相对路径解析为绝对路径，并阻止越界读取父目录或相邻目录。"""

    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("只接受项目内相对路径，不接受绝对路径")
    if any(part == ".." for part in path.parts):
        raise ValueError("相对路径不能包含 '..'")

    resolved = (PROJECT_ROOT / path).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError("路径越过当前项目目录边界") from exc
    return resolved


def read_original_prompt(relative_path: str | Path) -> str:
    """读取项目内原始提示词文件内容。

    参数使用相对项目根目录的路径，例如：
    多政策的国际比较报告/第一章提示词/1A:顶层设计 - 检索
    """

    path = _resolve_project_path(relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"原始提示词不存在：{relative_path}")
    return path.read_text(encoding="utf-8")


def replace_topic_placeholders(
    text: str,
    *,
    topic: str | None = None,
    replacements: Mapping[str, str] | None = None,
) -> str:
    """替换常见中文方括号主题占位符。

    replacements 的键可以直接写占位符原文，也可以写不带书名号的占位名。
    例如 {"【本次主题】": "人才培养"} 与 {"本次主题": "人才培养"} 都可用。
    """

    normalized: dict[str, str] = {}
    if topic is not None:
        normalized.update(
            {
                "【主题】": topic,
                "【本次主题】": topic,
                "【本章主题】": topic,
                "【在此填大主题，如：人工智能+教育】": topic,
            }
        )

    for key, value in (replacements or {}).items():
        placeholder = key if key.startswith("【") and key.endswith("】") else f"【{key}】"
        normalized[placeholder] = str(value)

    for placeholder, value in normalized.items():
        text = text.replace(placeholder, value)
    return text


def _replace_standard_topics(
    text: str,
    values: Mapping[str, str],
    *,
    topic_key: str = "topic",
) -> str:
    """按任务参数替换原始提示词中的通用主题占位符。"""

    return replace_topic_placeholders(text, topic=_require_value(values, topic_key))


def _replace_chapter1_specific_title(text: str, values: Mapping[str, str]) -> str:
    """替换第一章主题特性小节相关占位符。"""

    title = _require_value(values, "chapter1_topic_specific_title")
    return replace_topic_placeholders(
        text,
        topic=_require_value(values, "topic"),
        replacements={
            "【在此填主题词 / 子标题，如：教育领域AI的伦理与安全治理】": title,
            "【在此填子标题，如：AI+教育伦理与安全治理机制】": title,
            "【在此粘贴阶段二检索出的全部素材】": _optional_value(
                values, "ch1_3b_retrieval_content"
            ),
        },
    )


def _replace_chapter2_topic(text: str, values: Mapping[str, str]) -> str:
    """替换第二章主题相关占位符。"""

    return replace_topic_placeholders(
        text,
        topic=_require_value(values, "topic"),
        replacements={"【本次主题】": _require_value(values, "chapter2_topic")},
    )


def _extract_between(text: str, start_marker: str, end_marker: str | None = None) -> str:
    """从原始模板中截取指定任务片段。"""

    start = text.find(start_marker)
    if start == -1:
        raise ValueError(f"原始提示词缺少片段起点：{start_marker}")
    if end_marker is None:
        return text[start:].strip()

    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        raise ValueError(f"原始提示词缺少片段终点：{end_marker}")
    return text[start:end].strip()


def _chapter2_dimension_transform(text: str, values: Mapping[str, str]) -> str:
    """提取第二章模板中的“第一步”作为维度凝练构思提示词。"""

    first_step = _extract_between(text, "第一步——自下而上凝练维度", "第二步——按以下范式撰写正文")
    return replace_topic_placeholders(
        first_step,
        topic=_require_value(values, "topic"),
        replacements={"【本章主题】": _require_value(values, "chapter2_topic")},
    )


def _chapter2_body_transform(text: str, values: Mapping[str, str]) -> str:
    """提取第二章模板中的“第二步”作为正文写作提示词。"""

    second_step = _extract_between(text, "第二步——按以下范式撰写正文", "约束：")
    return replace_topic_placeholders(
        second_step,
        topic=_require_value(values, "topic"),
        replacements={"【本章主题】": _require_value(values, "chapter2_topic")},
    )


def _input_block(lines: list[tuple[str, str]]) -> str:
    """把输入字段组装为稳定的“本次输入”文本。"""

    rendered: list[str] = []
    for label, value in lines:
        if "\n" in value:
            rendered.append(f"{label}：\n{value}")
        else:
            rendered.append(f"{label}：{value}")
    return "\n".join(rendered)


def _input_retrieval_1a(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("知识库名称", _require_value(values, "notebook_name")),
            ("Notebook ID", _require_value(values, "notebook_id")),
        ]
    )


def _input_retrieval_3b(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("检索主题", _require_value(values, "chapter1_topic_specific_title")),
            ("知识库名称", _require_value(values, "notebook_name")),
            ("Notebook ID", _require_value(values, "notebook_id")),
        ]
    )


def _input_retrieval_chapter2(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("本次主题", _require_value(values, "chapter2_topic")),
            ("知识库名称", _require_value(values, "notebook_name")),
            ("Notebook ID", _require_value(values, "notebook_id")),
        ]
    )


def _input_planning_3a(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("既定同级子主题", "顶层设计与实施机制"),
        ]
    )


def _input_planning_chapter2_topic(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("报告结构", "第一章讲各国怎么治理这个领域，第二章纵深展开目的层，第三章讲中国对策。"),
        ]
    )


def _input_planning_chapter2_dimensions(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("第二章主题", _require_value(values, "chapter2_topic")),
            ("第二章检索内容", _require_value(values, "chapter2_retrieval_content")),
            ("第二章相关文献", _require_value(values, "chapter2_related_literature")),
        ]
    )


def _input_writing_1b(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("1A 检索内容", _require_value(values, "ch1_1a_retrieval_content")),
            ("1A 相关文献", _require_value(values, "ch1_1a_related_literature")),
        ]
    )


def _input_writing_2b(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("2A 检索内容", _require_value(values, "ch1_2a_retrieval_content")),
            ("2A 相关文献", _require_value(values, "ch1_2a_related_literature")),
        ]
    )


def _input_writing_3c(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("本节子标题", _require_value(values, "chapter1_topic_specific_title")),
            ("3B 检索内容", _require_value(values, "ch1_3b_retrieval_content")),
            ("3B 相关文献", _require_value(values, "ch1_3b_related_literature")),
        ]
    )


def _input_writing_chapter2(values: Mapping[str, str]) -> str:
    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("第二章主题", _require_value(values, "chapter2_topic")),
            ("第二章维度凝练产物", _require_value(values, "chapter2_dimension_plan")),
            ("第二章检索内容", _require_value(values, "chapter2_retrieval_content")),
            ("第二章相关文献", _require_value(values, "chapter2_related_literature")),
        ]
    )


def _input_writing_chapter3(values: Mapping[str, str]) -> str:
    """第三章基于前两章成文做综合转化写作。"""

    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("第一章成文", _require_value(values, "chapter1_draft")),
            ("第二章成文", _require_value(values, "chapter2_draft")),
        ]
    )


def _chapter3_transform(text: str, values: Mapping[str, str]) -> str:
    """第三章提示词不依赖原始占位符，只做主题占位替换。"""

    return replace_topic_placeholders(text, topic=_require_value(values, "topic"))


def _identity_transform(text: str, values: Mapping[str, str]) -> str:
    """只做主题占位替换，适用于本项目自有模板。"""

    return replace_topic_placeholders(text, topic=_require_value(values, "topic"))


def _input_fulltext_review(values: Mapping[str, str]) -> str:
    """全文内容结构审查需要读取完整原文和固定审查模板。"""

    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("审查意见模板", _require_value(values, "review_template")),
            ("待审查全文", _require_value(values, "full_report")),
        ]
    )


def _input_fulltext_revision(values: Mapping[str, str]) -> str:
    """全文修改需要同时读取原文、固定模板和本次审查报告。"""

    return _input_block(
        [
            ("报告主题", _require_value(values, "topic")),
            ("审查意见模板", _require_value(values, "review_template")),
            ("本次审查报告", _require_value(values, "review_report")),
            ("待修改全文", _require_value(values, "full_report")),
        ]
    )


PROMPT_SPECS: dict[str, PromptSpec] = {
    "retrieval.ch1_1a": PromptSpec(
        prompt_type="retrieval",
        original_path="多政策的国际比较报告/第一章提示词/1A:顶层设计 - 检索",
        input_builder=_input_retrieval_1a,
        output_contract=RETRIEVAL_OUTPUT_CONTRACT,
        original_transform=_replace_standard_topics,
        default_filename="retrieval_ch1_1a.md",
    ),
    "retrieval.ch1_2a": PromptSpec(
        prompt_type="retrieval",
        original_path="多政策的国际比较报告/第一章提示词/2A：实施机制-检索",
        input_builder=_input_retrieval_1a,
        output_contract=RETRIEVAL_OUTPUT_CONTRACT,
        original_transform=_replace_standard_topics,
        default_filename="retrieval_ch1_2a.md",
    ),
    "retrieval.ch1_3b": PromptSpec(
        prompt_type="retrieval",
        original_path="多政策的国际比较报告/第一章提示词/3b 检索",
        input_builder=_input_retrieval_3b,
        output_contract=RETRIEVAL_OUTPUT_CONTRACT,
        original_transform=_replace_chapter1_specific_title,
        default_filename="retrieval_ch1_3b.md",
    ),
    "retrieval.chapter2_materials": PromptSpec(
        prompt_type="retrieval",
        original_path="多政策的国际比较报告/第二章提示词/第二章所需资料提示词.md",
        input_builder=_input_retrieval_chapter2,
        output_contract=RETRIEVAL_OUTPUT_CONTRACT,
        original_transform=_replace_chapter2_topic,
        default_filename="retrieval_chapter2_materials.md",
    ),
    "planning.ch1_3a": PromptSpec(
        prompt_type="planning",
        original_path="多政策的国际比较报告/第一章提示词/3a 主题痛点",
        input_builder=_input_planning_3a,
        output_contract=PLANNING_OUTPUT_CONTRACT,
        original_transform=_replace_standard_topics,
        default_filename="planning_ch1_3a.md",
    ),
    "planning.chapter2_topic": PromptSpec(
        prompt_type="planning",
        original_path="多政策的国际比较报告/第二章提示词/第二部分定题.md",
        input_builder=_input_planning_chapter2_topic,
        output_contract=PLANNING_OUTPUT_CONTRACT,
        original_transform=_replace_standard_topics,
        default_filename="planning_chapter2_topic.md",
    ),
    "planning.chapter2_dimensions": PromptSpec(
        prompt_type="planning",
        original_path="多政策的国际比较报告/第二章提示词/第二章凝练维度写作模版.md",
        input_builder=_input_planning_chapter2_dimensions,
        output_contract=PLANNING_OUTPUT_CONTRACT,
        original_transform=_chapter2_dimension_transform,
        default_filename="planning_chapter2_dimensions.md",
    ),
    "writing.ch1_1b": PromptSpec(
        prompt_type="writing",
        original_path="多政策的国际比较报告/第一章提示词/模块 1B:顶层设计 · 归类加写作",
        input_builder=_input_writing_1b,
        output_contract=WRITING_OUTPUT_CONTRACT,
        original_transform=_replace_standard_topics,
        default_filename="writing_ch1_1b.md",
    ),
    "writing.ch1_2b": PromptSpec(
        prompt_type="writing",
        original_path="多政策的国际比较报告/第一章提示词/ 2B:实施机制 · 归类",
        input_builder=_input_writing_2b,
        output_contract=WRITING_OUTPUT_CONTRACT,
        original_transform=_replace_standard_topics,
        default_filename="writing_ch1_2b.md",
    ),
    "writing.ch1_3c": PromptSpec(
        prompt_type="writing",
        original_path="多政策的国际比较报告/第一章提示词/3c 分维度加写作",
        input_builder=_input_writing_3c,
        output_contract=WRITING_OUTPUT_CONTRACT,
        original_transform=_replace_chapter1_specific_title,
        default_filename="writing_ch1_3c.md",
    ),
    "writing.chapter2_body": PromptSpec(
        prompt_type="writing",
        original_path="多政策的国际比较报告/第二章提示词/第二章凝练维度写作模版.md",
        input_builder=_input_writing_chapter2,
        output_contract=WRITING_OUTPUT_CONTRACT,
        original_transform=_chapter2_body_transform,
        default_filename="writing_chapter2_body.md",
    ),
    "writing.chapter3_body": PromptSpec(
        prompt_type="writing",
        original_path="workflow/prompts/ch3_writing.md",
        input_builder=_input_writing_chapter3,
        output_contract=WRITING_OUTPUT_CONTRACT,
        original_transform=_chapter3_transform,
        default_filename="writing_chapter3_body.md",
    ),
    "review.fulltext_content_structure": PromptSpec(
        prompt_type="review",
        original_path="workflow/prompts/fulltext_review.md",
        input_builder=_input_fulltext_review,
        output_contract=REVIEW_OUTPUT_CONTRACT,
        original_transform=_identity_transform,
        default_filename="review_fulltext_content_structure.md",
    ),
    "revision.fulltext_content_structure": PromptSpec(
        prompt_type="revision",
        original_path="workflow/prompts/fulltext_rewrite.md",
        input_builder=_input_fulltext_revision,
        output_contract=REVISION_OUTPUT_CONTRACT,
        original_transform=_identity_transform,
        default_filename="revision_fulltext_content_structure.md",
    ),
}


def list_prompt_ids(prompt_type: str | None = None) -> list[str]:
    """列出可用的工程化提示词任务 ID。"""

    if prompt_type is None:
        return sorted(PROMPT_SPECS)
    return sorted(prompt_id for prompt_id, spec in PROMPT_SPECS.items() if spec.prompt_type == prompt_type)


def build_engineered_prompt(prompt_id: str, **kwargs: str) -> str:
    """按任务 ID 生成工程化提示词文本。

    常用 prompt_id：
    - retrieval.ch1_1a / retrieval.ch1_2a / retrieval.ch1_3b / retrieval.chapter2_materials
    - planning.ch1_3a / planning.chapter2_topic / planning.chapter2_dimensions
    - writing.ch1_1b / writing.ch1_2b / writing.ch1_3c / writing.chapter2_body / writing.chapter3_body
    - review.fulltext_content_structure
    - revision.fulltext_content_structure
    """

    try:
        spec = PROMPT_SPECS[prompt_id]
    except KeyError as exc:
        available = "、".join(list_prompt_ids())
        raise KeyError(f"未知提示词任务 ID：{prompt_id}。可用 ID：{available}") from exc

    values: Mapping[str, str] = kwargs
    original_prompt = read_original_prompt(spec.original_path)
    original_prompt = spec.original_transform(original_prompt, values)

    return "\n\n".join(
        [
            "【本次输入】\n" + spec.input_builder(values),
            "【原始提示词】\n" + original_prompt.strip(),
            "【工程化输出要求】\n" + spec.output_contract.strip(),
        ]
    ).strip() + "\n"


def build_retrieval_prompt(prompt_id: str, **kwargs: str) -> str:
    """生成检索类工程化提示词。prompt_id 可省略 retrieval. 前缀。"""

    normalized = prompt_id if prompt_id.startswith("retrieval.") else f"retrieval.{prompt_id}"
    return build_engineered_prompt(normalized, **kwargs)


def build_planning_prompt(prompt_id: str, **kwargs: str) -> str:
    """生成构思类工程化提示词。prompt_id 可省略 planning. 前缀。"""

    normalized = prompt_id if prompt_id.startswith("planning.") else f"planning.{prompt_id}"
    return build_engineered_prompt(normalized, **kwargs)


def build_writing_prompt(prompt_id: str, **kwargs: str) -> str:
    """生成写作类工程化提示词。prompt_id 可省略 writing. 前缀。"""

    normalized = prompt_id if prompt_id.startswith("writing.") else f"writing.{prompt_id}"
    return build_engineered_prompt(normalized, **kwargs)


def build_review_prompt(prompt_id: str, **kwargs: str) -> str:
    """生成审查类工程化提示词。prompt_id 可省略 review. 前缀。"""

    normalized = prompt_id if prompt_id.startswith("review.") else f"review.{prompt_id}"
    return build_engineered_prompt(normalized, **kwargs)


def build_revision_prompt(prompt_id: str, **kwargs: str) -> str:
    """生成全文修改类工程化提示词。prompt_id 可省略 revision. 前缀。"""

    normalized = prompt_id if prompt_id.startswith("revision.") else f"revision.{prompt_id}"
    return build_engineered_prompt(normalized, **kwargs)


def save_prompt(
    content: str,
    filename: str | Path,
    *,
    run_dir: str | Path = ".",
) -> Path:
    """把提示词写入运行目录的 generated_prompts/。

    run_dir 必须位于当前项目内；filename 只允许是文件名，不允许包含目录层级。
    """

    run_path = _resolve_project_path(run_dir)
    if not run_path.exists():
        run_path.mkdir(parents=True, exist_ok=True)
    if not run_path.is_dir():
        raise NotADirectoryError(f"运行目录不是文件夹：{run_dir}")

    name = Path(filename)
    if name.is_absolute() or len(name.parts) != 1:
        raise ValueError("filename 只允许传文件名，不允许包含目录")

    output_dir = run_path / "generated_prompts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = (output_dir / name).resolve()
    output_path.write_text(content, encoding="utf-8")
    return output_path


def build_and_save_prompt(
    prompt_id: str,
    *,
    run_dir: str | Path = ".",
    filename: str | Path | None = None,
    **kwargs: str,
) -> Path:
    """生成指定任务的工程化提示词，并保存到 generated_prompts/。"""

    try:
        spec = PROMPT_SPECS[prompt_id]
    except KeyError as exc:
        available = "、".join(list_prompt_ids())
        raise KeyError(f"未知提示词任务 ID：{prompt_id}。可用 ID：{available}") from exc

    content = build_engineered_prompt(prompt_id, **kwargs)
    return save_prompt(content, filename or spec.default_filename, run_dir=run_dir)


__all__ = [
    "PROMPT_SPECS",
    "PROJECT_ROOT",
    "PromptSpec",
    "build_and_save_prompt",
    "build_engineered_prompt",
    "build_planning_prompt",
    "build_retrieval_prompt",
    "build_review_prompt",
    "build_revision_prompt",
    "build_writing_prompt",
    "list_prompt_ids",
    "read_original_prompt",
    "replace_topic_placeholders",
    "save_prompt",
]
