"""topic-material-search 第4步：DeepSeek 材料复核（一轮）。装配审核标准+方案颗粒度+6文件→DS→落盘。"""
from __future__ import annotations
from pathlib import Path
from llm_client import create_llm_client

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "web-materials-lifelong-edu"
CATS = ["trend_signals", "cross_country_practices", "driver_analysis",
        "maturity_assessment", "china_status_and_gaps", "response_evidence"]

STD = """【审核标准（请严格据此判定）】
A. 信息源标准
1. 权威分级：每个源标 T1（官方政策/法规、国际组织报告如OECD/UNESCO、官方统计）/ T2（同行评议研究）/ 剔除（博客、百科、二手转述、无出处、疑似AI生成）。
2. 覆盖度：每个参照实体（国家/机构）是否都有 T1 或 T2 源；每个检索类别是否都有实质来源。
3. 出处完整：每个源是否有 机构 + 文件/报告名 + 年份 + URL；缺项的降级。
4. 时效：政策类优先近 5–8 年；历史背景类可放宽但需标年份。
B. 检索信息质量标准
1. 可溯源：每条关键事实是否带出处，能否回到具体来源；不可溯源的判为不可用。
2. 证据状态：是否标注 [已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]；把意图/转述当成熟经验的，判不达标。
3. 充分性：每个类别是否都有足以支撑写作的实质内容。
4. 颗粒度（按与用户共同确定的方案判定，非固定标准）：约定要微观细节（政策工具与制度）的类别是否做到；约定保持概览的类别不因"不够细"而扣分。
5. 无幻觉：是否存在看起来精确但无来源的数字、机构、年份；有则必须剔除或降级。
C. 通过线
- 每个参照实体均有 ≥1 个 T1/T2 源；各类别均"达标"；maturity_assessment 至少有 2 条带评估数据的证据；覆盖度与深度达到方案要求；无未溯源的精确数字残留。
- 任一不满足 → 总判定"继续补充"，并给出具体缺口。

【输出要求】逐类给【达标/不达标】+缺口；最后给【总判定：通过 / 继续补充】+ 若继续补充给出"下一轮补搜清单"。"""

granularity = """【与用户共同确定的检索方案（用于判定覆盖度与颗粒度）】
- 实体：UNESCO/OECD/欧盟 + 德/日/韩/新/芬/英 + 中国。
- 深度角度：只往深里搜「政策工具与制度」（资历框架/微证书/个人学习账户/成人继续教育立法）；有效性评估、治理载体、驱动力/阶段三角度保持适度、不强求微观。
- 来源：仅一手 T1/T2，原文/英文（中国部分允许中国官方一手中文）；不用 CNKI/中文二手承担微观角度。
- 时间窗：2015–2025。"""

parts = [STD, "\n\n" + granularity, "\n\n【待审材料】\n"]
for c in CATS:
    parts.append(f"\n===== 文件: {c}.md =====\n")
    parts.append((RUN / "retrieval_outputs" / f"{c}.md").read_text(encoding="utf-8"))
review_in = "".join(parts)
Path("/tmp/review_in.txt").write_text(review_in, encoding="utf-8")

c = create_llm_client("deepseek")
r = c.ask(review_in)
out = r or "<EMPTY>"
(RUN / "ds_review_round4.md").write_text(out, encoding="utf-8")
print("REVIEW LEN", len(out))
