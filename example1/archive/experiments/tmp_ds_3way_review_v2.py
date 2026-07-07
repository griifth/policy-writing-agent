"""公平版三方盲审：文章二换成带 institution_profile 的 agent v2 稿；标尺加入 institution_profile（教育域落点）。
文章一=这一版(DeepSeek流水线,2轮审改) 文章二=agent v2(子型A+教育域,单遍) 文章三=人类原文。"""
from __future__ import annotations
from pathlib import Path
from deepseek_client import DeepSeekClient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "agent_run_subtypeA_v2"

paths = {
    "文章一": ROOT / "runs/run-20260625-210305-06e3ea92/final_article_reviewed.md",
    "文章二": OUT / "agent_draft.md",
    "文章三": ROOT / "report_modules/strategic_response/source/sample.md",
}
arts = {k: v.read_text(encoding="utf-8") for k, v in paths.items()}

wiki = ROOT / "policy_style_dna" / "wiki"
rubric_files = ["voice.md", "structure.md", "forbidden.md", "recommendation.md", "subtype_a.md", "self_check.md"]
rubric = "\n\n".join(
    f"## {n}\n\n{(wiki / n).read_text(encoding='utf-8')}" for n in rubric_files if (wiki / n).is_file()
)
rubric += "\n\n## institution_profile.md（建议落点域：必须落教育抓手）\n\n" + (ROOT / "institution_profile.md").read_text(encoding="utf-8")

prompt = f"""你是政策报告盲审评委。下面三篇**同题**（美国AI人才战略布局及我国教育域应对策略）报告，体例为"战略竞争分析+中国应对策略"（子型A），且**出自教育研究机构，对策建议必须落在教育域抓手**。请**只依据文本**盲审，不要猜测哪篇人写/机写。

【评判标尺（policy_style_dna 子型A + 通则 + 机构 profile）】
{rubric}

【七个评分维度】每维度给三篇各打 1–10 分并一句话依据：
1. 结构严密（国际/对手→我国差距→镜像对策 三段闭环、镜像对位）
2. 判断纵深（先断后证、判断∶证据≈1∶N、真比较=差异+原因+适用条件）
3. 建议操作性（四要素尤其"实施机制"落地、点名部委层级、稳慎兜底）
4. **教育域落点（关键）**：对策是否全部落在教育抓手（学科/培养/课程/师资/拔尖/产教/留学治理/教育数字化），跨域议题是否落回教育接口；写成纯产业/外交/科技政策的扣分
5. 语域契合子型A（冷峻克制、升格+兜底双声部、对华语气得当、无情绪化/军事化滥用）
6. 文风禁区（过程外露/元话语、伪比较罗列、空泛大词、AI腔、出处缺失）
7. 本土化与事实严谨（中国教育制度容器、数字/法案出处线索、无杜撰）

【输出】
A. 三栏评分表（维度×文章一/二/三，含分数与一句依据）。
B. 总分与排序。
C. **差距分析**：分别说清"文章二 vs 文章三""文章二 vs 文章一""文章一 vs 文章三"在各维度的具体差距，引文为证；**特别点评第4维教育域落点三篇各自表现**。
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
(OUT / "ds_3way_review_v2.md").write_text(verdict, encoding="utf-8")
(OUT / "ds_3way_key_v2.md").write_text(
    "# 盲审映射 key（v2·公平版，含教育域标尺）\n"
    "- 文章一 = 这一版（DeepSeek 流水线，2 轮审改，run-20260625-210305-06e3ea92）\n"
    "- 文章二 = agent v2（Claude，子型A 路由 + institution_profile 教育域，单遍无审改）\n"
    "- 文章三 = 人类原文（report_modules/strategic_response/source/sample.md）\n",
    encoding="utf-8",
)
print("done. wrote ds_3way_review_v2.md (", len(verdict), "chars )")
