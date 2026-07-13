# -*- coding: utf-8 -*-
"""run_entity.py —— 写作/构思实体的 DeepSeek 执行入口（direction_workflow · 执行引擎）。

用途：读入自包含四节实体提示词（装配工按宪法第 4 条制造），交 DeepSeek 执行，产出落盘。
stdout 打印 token 用量与降级留痕；不打分、不改产物、不打印任何密钥。

命令行用法：
    python3 engine/run_entity.py <实体提示词文件> <输出文件> [--attach 材料文件 ...]
                                 [--env .env路径] [--effort max|high|medium|low]

    --attach  可多次：把实体提示词第 3 节【本篇材料】所引路径的文件内容内联进提示词
              （DeepSeek 不能读盘，自包含化靠内联；内联即留痕，见 stdout 与提示词尾节）。
    --env     指定 .env 位置（默认旧引擎既有位置 example1/.env；只读路径，密钥不进本目录）。
    --effort  首次尝试的 reasoning_effort（默认取 .env / DEEPSEEK_REASONING_EFFORT）。

降级重试（移植自旧引擎 workflow/report_pipeline._ask_deepseek，血换逻辑原样保留）：
    空响应几乎总是推理（thinking）烧穿 max_tokens（finish_reason=length），
    逐级降低推理强度重试：原参数 → effort=low → effort=low+关闭 thinking；
    三级仍空 → 报错中止，绝不把空产物落盘。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deepseek_client import (  # noqa: E402
    DeepSeekClient,
    DeepSeekEmptyResponseError,
    load_deepseek_config,
)

ATTACH_HEADER = (
    "# 附件材料（由 engine/run_entity.py 内联；"
    "系上文【本篇材料】节所引路径文件的原文照录，供执行引擎直读）"
)


def build_prompt(prompt_path: Path, attachments: list[Path]) -> str:
    """读实体提示词；如有附件则内联为自包含提示词（内联本身即留痕）。"""
    prompt = prompt_path.read_text(encoding="utf-8")
    if not attachments:
        return prompt
    parts = [prompt, "\n\n---\n\n" + ATTACH_HEADER]
    for path in attachments:
        parts.append(
            f"\n\n## 附件：{path.name}\n\n{path.read_text(encoding='utf-8')}"
        )
    return "".join(parts)


def format_meta(meta: dict | None) -> str:
    """把 token 用量留痕格式化为一行（无密钥字段）。"""
    if not meta:
        return "（无用量信息）"
    return (
        f"prompt_tokens={meta.get('prompt_tokens')} "
        f"completion_tokens={meta.get('completion_tokens')} "
        f"reasoning_tokens={meta.get('reasoning_tokens')} "
        f"total_tokens={meta.get('total_tokens')} "
        f"finish_reason={meta.get('finish_reason')} "
        f"model={meta.get('model')}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="实体提示词 → DeepSeek 执行 → 产出落盘")
    parser.add_argument("prompt_file", help="自包含四节实体提示词文件")
    parser.add_argument("output_file", help="产出落盘路径")
    parser.add_argument(
        "--attach", action="append", default=[], metavar="FILE",
        help="内联进提示词的材料文件（可多次；对应实体提示词第 3 节所引路径）",
    )
    parser.add_argument("--env", default=None, help=".env 路径（默认旧引擎既有位置 example1/.env）")
    parser.add_argument("--effort", default=None, help="首次尝试的 reasoning_effort（默认取配置）")
    args = parser.parse_args()

    prompt_path = Path(args.prompt_file)
    if not prompt_path.is_file():
        sys.stderr.write(f"找不到实体提示词文件：{prompt_path}\n")
        sys.exit(2)
    attachments = [Path(p) for p in args.attach]
    for path in attachments:
        if not path.is_file():
            sys.stderr.write(f"找不到附件材料文件：{path}\n")
            sys.exit(2)

    config = load_deepseek_config(args.env) if args.env else load_deepseek_config()
    client = DeepSeekClient(config)

    prompt = build_prompt(prompt_path, attachments)
    print("=" * 60)
    print("run_entity · DeepSeek 执行留痕")
    print("=" * 60)
    print(f"实体提示词：{prompt_path}")
    for path in attachments:
        print(f"内联附件：{path}（{len(path.read_text(encoding='utf-8'))} 字符）")
    print(f"最终提示词长度：{len(prompt)} 字符")
    print(f"模型：{config.model}　base_url：{config.base_url}　max_tokens：{config.max_tokens}")
    print(f"配置 reasoning_effort：{config.reasoning_effort}　thinking_enabled：{config.thinking_enabled}")

    # 降级梯子（与旧引擎 report_pipeline._ask_deepseek 同款，原样保留）：
    # 空响应几乎总是推理（thinking）烧穿 max_tokens（finish_reason=length），
    # 逐级降低推理强度重试：原参数 → effort=low → 关闭 thinking。
    attempt_kwargs: list[dict[str, object]] = [
        {"reasoning_effort": args.effort},
        {"reasoning_effort": "low"},
        {"reasoning_effort": "low", "thinking_enabled": False},
    ]
    last_error: DeepSeekEmptyResponseError | None = None
    content: str | None = None
    for attempt, kwargs in enumerate(attempt_kwargs):
        label = f"第 {attempt + 1}/3 级"
        started = time.time()
        try:
            content = client.ask(prompt, **kwargs)  # type: ignore[arg-type]
            elapsed = time.time() - started
            print(f"[降级留痕] {label} 参数 {kwargs} → 成功（{elapsed:.1f}s）")
            print(f"[token用量] {format_meta(client.last_meta)}")
            break
        except DeepSeekEmptyResponseError as exc:
            elapsed = time.time() - started
            last_error = exc
            print(f"[降级留痕] {label} 参数 {kwargs} → 空响应（{elapsed:.1f}s）：{exc}")
            print(f"[token用量] {format_meta(client.last_meta)}")
            time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f"DeepSeek 降级重试 3 次仍返回空响应，任务中止：{last_error}")

    assert content is not None
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"产出落盘：{output_path}（{len(content)} 字符）")
    print("=" * 60)


if __name__ == "__main__":
    main()
