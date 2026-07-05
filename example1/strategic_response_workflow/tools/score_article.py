"""单篇报告终审打分器（quality_rubric 六维 × 教科院终审人三遍读法）。

用法（在 strategic_response_workflow/ 下）：
    python3 tools/score_article.py --article <path> [--out <path>] [--label <str>]

逻辑：读 `quality_rubric.md`（唯一评分真源）+ `reviewers/jiaokeyuan_review_scope.md`（终审人
角色与三遍读法）拼评审提示词 → DeepSeek 出终审报告（末尾附 rubric 第五节 JSON 评分块）→
报告落盘（缺省 <article 同目录>/<stem>.score.md）→ stdout 打一行摘要供批量校准：
    LABEL total=NN grade=X hard_faults=[...]
JSON 抽取失败 → 打 `LABEL PARSE_FAIL` 并 exit 2（报告仍落盘，便于人工检视）。

前身：workflow/tmp_ds_score_clarified.py（内嵌七维，已归档 archive/experiments/）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

WORKFLOW_ROOT = Path(__file__).resolve().parents[1]
# 从 tools/ 独立运行时，llm_client 及其依赖在 workflow/ 目录下
sys.path.insert(0, str(WORKFLOW_ROOT / "workflow"))

from llm_client import create_llm_client  # noqa: E402


def build_prompt(article_text: str, label: str) -> str:
    """终审人角色（scope）＋评分标尺（rubric）＋待评文章 → 评审提示词。"""

    rubric = (WORKFLOW_ROOT / "quality_rubric.md").read_text(encoding="utf-8")
    scope = (WORKFLOW_ROOT / "reviewers" / "jiaokeyuan_review_scope.md").read_text(
        encoding="utf-8"
    )
    return "\n\n".join(
        [
            "你将扮演下述终审人，独立终审一篇政策研究报告。严格按【角色与三遍读法】审读，"
            "按【报告质量评分标尺】（唯一评分真源）计分，禁止另立分值体系。",
            "【角色与三遍读法（reviewers/jiaokeyuan_review_scope.md）】",
            scope,
            "【报告质量评分标尺（quality_rubric.md · 唯一评分真源）】",
            rubric,
            "【定标纪律（先于打分执行，标尺第四节）】",
            "打分前必须先做锚点定位：对照标尺第四节盲测锚点表（A–E），判断本文最像哪一篇并给一句理由；"
            "以该锚的锚定档为基准起算，除非能逐条列出本文与该锚的具体优劣差异，总分档位不得偏离锚定档超过一档。"
            "同时执行第四节「校准注意」：人写瑕疵（错别字/笔误）不降档；引证密度高≠研判深；"
            "溯源只查行文内线索在不在（文件名/机构/年份），不得以缺学术脚注、章节页码或英文原名为由扣分。",
            "【输出要求】",
            "按 scope「输出（顺序固定）」出具终审报告：首行总体结论、三遍读法发现（引原文→指问题→给改法）、"
            "终审意见书（最像哪个盲测锚点、离上一档差什么、改文字还是须重构）。"
            "报告末尾必须附一个 ```json 围栏包裹的评分块，字段与格式严格遵循标尺第五节，"
            "不得省略任何字段。",
            f"==== 待评报告（{label}）====",
            article_text,
        ]
    )


def extract_score(report_text: str) -> dict | None:
    """抽报告末尾最后一个 ```json 围栏块并解析；失败返回 None。"""

    blocks = re.findall(r"```json\s*(.*?)```", report_text, flags=re.DOTALL)
    if not blocks:
        return None
    try:
        data = json.loads(blocks[-1])
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="单篇报告终审打分（quality_rubric 六维 + 教科院终审人）"
    )
    parser.add_argument("--article", required=True, help="待评文章路径（.md/.txt）")
    parser.add_argument(
        "--out", help="评分报告输出路径；缺省=article 同目录 <stem>.score.md"
    )
    parser.add_argument("--label", help="样本标签（报告抬头与 stdout 摘要用）；缺省=文件名")
    args = parser.parse_args()

    article_path = Path(args.article).expanduser()
    if not article_path.is_file():
        parser.error(f"文章不存在: {article_path}")
    label = args.label or article_path.stem
    out_path = (
        Path(args.out).expanduser()
        if args.out
        else article_path.with_name(f"{article_path.stem}.score.md")
    )

    article_text = article_path.read_text(encoding="utf-8")
    prompt = build_prompt(article_text, label)
    client = create_llm_client("deepseek")
    report = client.ask(prompt) or "<EMPTY>"

    header = (
        f"# 终审评分报告：{label}\n\n"
        f"> 待评文章：`{article_path}`\n"
        f"> 标尺：`quality_rubric.md`（六维加权百分制）｜终审人：`reviewers/jiaokeyuan_review_scope.md`\n"
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + report.rstrip() + "\n", encoding="utf-8")

    score = extract_score(report)
    if score is None:
        print(f"{label} PARSE_FAIL")
        return 2
    total = score.get("total")
    grade = score.get("grade")
    hard_faults = score.get("hard_faults") or []
    print(
        f"{label} total={total} grade={grade} "
        f"hard_faults={json.dumps(hard_faults, ensure_ascii=False)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
