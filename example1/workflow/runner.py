"""工作流命令行入口。

该文件只负责解析用户输入并启动报告生成流程，具体步骤由
`report_pipeline.py` 编排。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from report_pipeline import ReportPipeline


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="基于 NotebookLM 和 DeepSeek 的国际政策比较报告 MVP"
    )
    parser.add_argument("--topic", required=True, help="报告主题，例如：人工智能+教育")
    parser.add_argument(
        "--notebook-name",
        required=True,
        help="NotebookLM 知识库名称，例如：The Digital Promise AI Literacy Framework",
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="运行产物目录，默认 runs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只生成运行目录、任务列表和提示词，不调用 NotebookLM 或 DeepSeek",
    )
    parser.add_argument(
        "--resume-run",
        default=None,
        help="从已有 runs/<run_id> 继续执行，跳过已完成任务",
    )
    return parser.parse_args()


def main() -> int:
    """启动工作流。"""
    args = parse_args()
    pipeline = ReportPipeline(
        topic=args.topic,
        notebook_name=args.notebook_name,
        runs_dir=Path(args.runs_dir),
        dry_run=args.dry_run,
        resume_run=args.resume_run,
    )
    pipeline.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
