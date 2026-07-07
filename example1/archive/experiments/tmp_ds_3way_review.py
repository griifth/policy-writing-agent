"""临时脚本：用 DeepSeek 对三篇同题报告做盲审三方对比。
文章一=这一版(DeepSeek流水线·路由前DNA) 文章二=agent版(子型A路由) 文章三=人类原文(sample)。
DeepSeek 盲审（只见文章一/二/三），输出评分+排序+差距分析。映射 key 由本脚本另存。"""
from __future__ import annotations
from pathlib import Path
from deepseek_client import DeepSeekClient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "agent_run_subtypeA"

paths = {
    "文章一": ROOT / "runs/run-20260625-210305-06e3ea92/final_article_reviewed.md",
    "文章二": OUT / "agent_draft.md",
    "文章三": ROOT / "report_modules/strategic_response/source/sample.md",
}
arts = {k: v.read_text(encoding="utf-8") for k, v in paths.items()}

# 评判标尺：新路由 DNA 的子型A + 通则
rubric_files = ["voice.md", "structure.md", "forbidden.md", "recommendation.md", "subtype_a.md", "self_check.md"]
rubric = "\n\n".join(
    f"## {n}\n\n{(ROOT / 'policy_style_dna' / 'wiki' / n).read_text(encoding='utf-8')}"
    for n in rubric_files if (ROOT / 'policy_style_dna' / 'wiki' / n).is_file()
)

prompt = f"""你是政策报告盲审评委。下面是三篇**同题**（美国AI人才战略布局及我国应对策略）报告，体例均为"战略竞争分析+中国应对策略"（子型A）。请**只依据文本**盲审，不要猜测哪篇是人写/机写。

【评判标尺（policy_style_dna 子型A + 通则）】
{rubric}

【六个评分维度】每维度给三篇各打 1–10 分并一句话依据：
1. 结构严密（国际/对手→我国差距→镜像对策 三段闭环、镜像对位是否严格）
2. 判断纵深（先断后证、判断∶证据≈1∶N、有无真比较=差异+原因+适用条件）
3. 建议操作性（四要素尤其"实施机制"是否落地、是否点名部委层级、稳慎兜底）
4. 语域契合子型A（冷峻克制、升格+兜底双声部、对华语气得当、无情绪化/军事化滥用）
5. 文风禁区（有无过程外露/元话语、伪比较罗列、空泛大词、AI腔、出处缺失）
6. 本土化与事实严谨（中国话语转译、数字/法案出处线索、无杜撰）

【输出】
A. 三栏评分表（维度×文章一/二/三，含分数与一句依据）。
B. 总分与排序。
C. **差距分析**：分别说清"文章二 vs 文章三""文章二 vs 文章一""文章一 vs 文章三"在各维度的具体差距，引文章中的具体片段为证。
D. 一句话结论：每篇相对其它两篇"达到/接近/超过/不及"在哪。

==== 文章一 ====
{arts['文章一']}

==== 文章二 ====
{arts['文章二']}

==== 文章三 ====
{arts['文章三']}
"""

client = DeepSeekClient()
print("calling deepseek (reasoning_effort=max)...", flush=True)
verdict = client.ask(prompt, reasoning_effort="max")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "ds_3way_review.md").write_text(verdict, encoding="utf-8")
(OUT / "ds_3way_key.md").write_text(
    "# 盲审映射 key\n"
    "- 文章一 = 这一版（DeepSeek 流水线，路由前 DNA，run-20260625-210305-06e3ea92）\n"
    "- 文章二 = agent 版（Claude agent，子型A 路由后 DNA）\n"
    "- 文章三 = 人类原文（report_modules/strategic_response/source/sample.md）\n",
    encoding="utf-8",
)
print("done. wrote ds_3way_review.md (", len(verdict), "chars )")
