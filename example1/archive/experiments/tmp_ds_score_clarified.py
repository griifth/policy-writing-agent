"""给 trend_review 清晰版成稿单篇评分（子型B + 教育域 + 体例标尺）。"""
from __future__ import annotations
from pathlib import Path
from llm_client import create_llm_client

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "run-20260626-111233-dfa77f3b"
art = (RUN / "final_article_clarified.md").read_text(encoding="utf-8")

wiki = ROOT / "policy_style_dna" / "wiki"
rubric_files = ["voice.md", "structure.md", "forbidden.md", "recommendation.md", "subtype_b.md", "self_check.md"]
rubric = "\n\n".join(f"## {n}\n\n{(wiki / n).read_text(encoding='utf-8')}" for n in rubric_files if (wiki / n).is_file())
rubric += "\n\n## institution_profile.md（建议必须落教育域）\n\n" + (ROOT / "institution_profile.md").read_text(encoding="utf-8")

prompt = f"""你是政策报告评分评委。下面是一篇**国际动向研判 + 中国对策（trend_review·子型B）**报告，主题"国外终身教育改革动向和趋势"，出自教育研究机构（对策须落教育域）。请按标尺给出**量化评分**。

【评判标尺（policy_style_dna 子型B + 通则 + 机构 profile）】
{rubric}

【七个维度，各 1–10 分，每维一句依据】
1. 结构与体例契合：是否走通"各国信号→趋势归纳→成因与阶段研判→中国现状差距→教育域对策"闭环；趋势主体是否类型化收拢（非逐国罗列）；对策是否不塌尾
2. 趋势研判深度：是否区分真趋势vs噪音、给出成因与阶段成熟度判断；有无"真比较"（差异+原因+适用条件）
3. 对策质量：是否全部落教育抓手、四要素尤其"实施机制"是否落地、点名教育部门层级、不悬空
4. 语域契合子型B：冷静研判、单声部机制声、判断后必缀实证(1∶N)、无情绪化/无强行升格双声部
5. 文风禁区：有无伪比较罗列、过程外露/元话语、空泛大词、AI腔、衔接词堆砌
6. 清晰度与可读性：主题句是否先行、术语是否给白话解释、引用是否"先讲清事实再带出处并点明支撑什么判断"
7. 出处严谨：关键事实是否带出处与证据状态、有无杜撰或精确数字无源

【输出】
A. 七维评分表（维度 | 分数 | 一句依据）。
B. 总分（/70）与等级（优秀≥60 / 良好52–59 / 合格45–51 / 不合格<45），并一句话定位它更接近"观点锋利的决策内参"还是"资料扎实的综述"。
C. 还差哪 2–3 点能更高分（具体、可执行）。

==== 待评文章 ====
{art}
"""

c = create_llm_client("deepseek")
r = c.ask(prompt)
out = r or "<EMPTY>"
(RUN / "ds_score_clarified.md").write_text(out, encoding="utf-8")
print("SCORE LEN", len(out))
