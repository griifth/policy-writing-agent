"""战略高度切片 三方盲审：文章一=根工作流裸跑基线 / 文章二=战略高度切片产出 / 文章三=干净人类原文。
专设"战略高度"维度。标尺=policy_style_dna 子型A + institution_profile。"""
from __future__ import annotations
from pathlib import Path
from llm_client import create_llm_client

ROOT = Path(__file__).resolve().parents[1]      # strategic_response_workflow
EX1 = ROOT.parent                                # example1
paths = {
    "文章一": EX1 / "runs/run-20260625-112544-ccb86ce5/final_report_reviewed.md",
    "文章二": EX1 / "runs/run-20260626-152506-2528b552/final_report_reviewed.md",
    "文章三": ROOT / "runs/run-20260626-131122-452a7eaa/human_original_clean.md",
}
arts = {k: v.read_text(encoding="utf-8") for k, v in paths.items()}

wiki = ROOT / "policy_style_dna" / "wiki"
rf = ["voice.md", "structure.md", "forbidden.md", "recommendation.md", "subtype_a.md", "self_check.md"]
rubric = "\n\n".join(f"## {n}\n\n{(wiki/n).read_text(encoding='utf-8')}" for n in rf if (wiki/n).is_file())
rubric += "\n\n## institution_profile.md（建议必须落教育域）\n\n" + (ROOT / "institution_profile.md").read_text(encoding="utf-8")

prompt = f"""你是政策报告盲审评委。下面三篇**同题**报告（人工智能+教育的国际比较与我国应对），出自教育研究机构（对策须落教育域）。**只依据文本**盲审，不要猜哪篇人写/机写。

【评判标尺（policy_style_dna 子型A + 通则 + 机构 profile）】
{rubric}

【七维，各 1–10 分，每维一句依据】
1. **战略高度（关键）**：是否站在国家战略/国际竞争格局俯瞰全局；是否把各国做法读成"国家战略路线选择"（而非技术清单）；政策推动层级/态势是否点明；建议是否有国家战略分量
2. 结构与体例契合：国际经验→类型化归并→中国现状→借鉴应对 闭环；先类型化非逐国罗列；对策不塌尾
3. 判断纵深：类型化+成因解释+真比较（差异+原因+适用条件）+证据状态区分（已实施/试点/评估/意图）
4. 对策质量：是否落教育抓手、四要素尤其实施机制、不悬空、本土容器
5. 证据严谨：关键事实带出处+证据状态、无杜撰、不把意图当成效
6. 语域与文风：冷峻审慎、判断后必缀实证、无空泛大词裸奔/AI腔/伪比较罗列
7. 本土化与中国适配：中国教育制度容器、迁移前提/适配条件

【输出】
A. 三栏评分表（维度 | 文章一 | 文章二 | 文章三，含分+一句依据）。
B. 总分（/70）与排序。
C. 差距分析：分别说清"文章二 vs 文章三""文章二 vs 文章一""文章一 vs 文章三"，**重点点评第1维战略高度三篇各自表现**，引文为证。
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
OUT = EX1 / "runs/run-20260626-152506-2528b552"
(OUT / "ds_3way_slice_v2.md").write_text(out, encoding="utf-8")
(OUT / "ds_3way_slice_key.md").write_text(
    "# 映射 key\n- 文章一 = 根工作流裸跑基线（ccb86ce5，无加持）\n"
    "- 文章二 = 战略高度切片产出（ch0战略态势卡+全链路注入，run-20260626-152506-2528b552）\n"
    "- 文章三 = 干净人类原文（人工智能+教育国际比较报告.docx）\n", encoding="utf-8")
print("LEN", len(out))
