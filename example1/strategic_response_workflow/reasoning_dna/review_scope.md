# 推理对账审查范围（scope = reasoning_compliance）

逐条核对正文是否违反 `judgment_outputs/` 中已做出的判断与证据降级：

- 是否把“**动向 / 政策意图**”写成了“**成熟经验**”。
- 是否把判为“**不可照搬**”的做法写成了“**直接借鉴**”。
- 是否把“**前提不成立**”的建议写成了**立即推进**。
- 是否**超出** judgment_outputs 中标注的证据边界 / “不能推出的判断”。
- 每条对外经验是否**带了迁移前提**；前提不成立时是否如实标注。

判据：拿 `judgment_outputs/` 的降级记录逐条对照正文，指出违反处并**引原文**。最后给一行 `总体结论：达到 | 基本达到 | 未达到`。

> 说明：各把“刀”现建于 `report_modules/<体例>/reasoning_dna/`（strategic_response：intent/threat/hedge；trend_review：signal/driver/stage/uncertainty；experience_response：cause/efficacy），共享证据分级与词表在 `shared_schema/`（evidence_maturity / register_blacklist / strength_gate）；本次运行实际使用的刀已快照于 `runs/<id>/reasoning_dna_snapshot/`，对账以快照为准。（2026-07-05 修复悬空引用：原承诺的 `reasoning_dna/wiki/` 未实现、已作废。）
