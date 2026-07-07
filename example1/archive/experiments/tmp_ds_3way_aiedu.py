"""AI+教育 三方盲审：文章一=根工作流裸跑基线 / 文章二=strategic加持稿 / 文章三=人类原文。
体例 experience_response（国际经验借鉴+中国应对），标尺=policy_style_dna 子型A + institution_profile。"""
from __future__ import annotations
from pathlib import Path
from llm_client import create_llm_client

ROOT = Path(__file__).resolve().parents[1]            # strategic_response_workflow
EX1 = ROOT.parent                                      # example1
paths = {
    "文章一": EX1 / "runs/run-20260625-112544-ccb86ce5/final_report_reviewed.md",
    "文章二": ROOT / "runs/run-20260626-131122-452a7eaa/final_article_reviewed.md",
    "文章三": ROOT / "runs/run-20260626-131122-452a7eaa/human_original_clean.md",
}
arts = {k: v.read_text(encoding="utf-8") for k, v in paths.items()}

wiki = ROOT / "policy_style_dna" / "wiki"
rf = ["voice.md", "structure.md", "forbidden.md", "recommendation.md", "subtype_a.md", "self_check.md"]
rubric = "\n\n".join(f"## {n}\n\n{(wiki/n).read_text(encoding='utf-8')}" for n in rf if (wiki/n).is_file())
rubric += "\n\n## institution_profile.md（建议必须落教育域）\n\n" + (ROOT / "institution_profile.md").read_text(encoding="utf-8")

prompt = f"""你是政策报告盲审评委。下面三篇**同题**报告（人工智能+教育的国际经验/比较与我国应对），体例为"国际经验借鉴 + 中国应对"，出自教育研究机构（对策须落教育域）。**只依据文本**盲审，不要猜哪篇人写/机写。

【评判标尺（policy_style_dna 子型A + 通则 + 机构 profile）】
{rubric}

【七维，各 1–10 分，每维一句依据】
1. 结构与体例契合：是否走通"国际经验→模式归类→成因/适用条件→中国现状→借鉴应对"闭环；是否先类型化（非逐国罗列）；对策是否不塌尾
2. 判断纵深：模式归类+成因解释+真比较（差异+原因+适用条件）；是否诚实区分证据状态（已实施/试点/评估数据/意图）
3. 对策质量：是否落教育抓手、四要素尤其实施机制、是否到"谁来做/在哪试/怎么评/错了如何停"、本土容器
4. 证据严谨：关键事实是否带出处+证据状态、有无杜撰、是否把"意图"当"成效"
5. 语域契合：冷峻审慎、判断后必缀实证、无情绪化/军事化滥用
6. 文风禁区：伪比较罗列、过程外露/元话语、空泛大词、AI腔
7. 本土化与中国适配：中国教育制度容器、迁移前提/适配条件是否讲清

【输出】
A. 三栏评分表（维度 | 文章一 | 文章二 | 文章三，含分+一句依据）。
B. 总分（/70）与排序。
C. 差距分析：分别说清"文章二 vs 文章三""文章二 vs 文章一""文章一 vs 文章三"在各维度差距，引文为证。
D. 一句话结论：每篇相对其它两篇"达到/接近/超过/不及"在哪。

==== 文章一 ====
{arts['文章一']}

==== 文章二 ====
{arts['文章二']}

==== 文章三 ====
{arts['文章三']}
"""

c = create_llm_client("deepseek")
r = c.ask(prompt)
out = r or "<EMPTY>"
OUT = ROOT / "runs/run-20260626-131122-452a7eaa"
(OUT / "ds_3way_aiedu_clean.md").write_text(out, encoding="utf-8")
(OUT / "ds_3way_aiedu_key.md").write_text(
    "# 映射 key\n- 文章一 = 根工作流裸跑基线（run-20260625-112544-ccb86ce5，无文风/推理/审核加持）\n"
    "- 文章二 = strategic 加持稿（experience_response，子型A，run-20260626-131122-452a7eaa）\n"
    "- 文章三 = 人类原文（人工智能+教育国际比较报告.md）\n", encoding="utf-8")
print("LEN", len(out))
