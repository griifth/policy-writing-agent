---
name: audit-extend-suggestions
description: 独立的"建议核查—延展—发散"外部审计工具：抽取一篇已成稿政策报告的对策建议，联网核查它们是否重复中国已有政策，能否基于已有政策往前推（补配套/深化/推动落地），有没有真正空白可补。独立于主写作流、不自动跑、不写回正文。Whenever 需要核查报告建议是否与中国现有政策重复、想基于已有政策延展建议、想找教育领域真空白、或要对一篇成稿的对策做"防重/补深/找空白"外部审计时，use this skill。触发词：建议核查、先例核查、是否已有政策、延展建议、发散新建议、对策审计、防重复。
---

# 建议核查—延展—发散（外部审计工具）

## 定位（先读）
- **独立增强工具**，不进 runner、不自动跑、不改主写作流（主流程仍 100% KB-only）。
- 解决三问：建议**是不是重复中国已有政策** / 能不能**基于已有政策往前推** / 有没有**真正空白**。
- **联网**（WebSearch/WebFetch）。产物是独立《审计与延展备忘》，web 来源逐条带 URL，**不自动写回正文**——是否并入由人决定（并入时那几条按"引用权威公开政策、需标注"处理）。

## 输入
一个 run 目录（或单篇文章）。**若是 run，必须同时读**（否则"挂靶"只能靠猜）：
`final_article_reviewed.md`、`suggestion_outputs/suggestion_pool.md`、`suggestion_outputs/policy_priority.md`、`judgment_outputs/*`。

## 工具与物料区
- 硬性判定工具：`tools/suggestion_audit_extend.py`（scaffold / decide）。
- 核查子程序：`reviewers/precedent_check_scope.md`（四级状态 + 来源分级 + 护栏）。
- 物料区：`runs/<id>/suggestion_audit/`：`materials/`、`query_log.md`、`extracted_suggestions.md`、`findings.json`、`report.md`。

## 流水线（agent 执行 S1–S5，硬判定交工具 S6）

### S0 脚手架
`python3 tools/suggestion_audit_extend.py scaffold <run_dir>`

### S1 抽取建议（含挂靶）
读上述全部输入，逐条抽：`措施(对象+工具+机制)` + `它回应的前文靶子`（靶子要能在 judgment_outputs / 正文诊断段里找到出处，不许凭空）。写 `extracted_suggestions.md`。

### S2 联网核查（按 precedent_check_scope.md）
每条精准 WebSearch → 四级状态（已实施/试点/提出未落地/未搜到）+ 证据（带 `source_tier`）+ confidence。
- **来源分级**：高置信"已实施/试点"必须有 tier≤2 官方来源；仅媒体(tier4)→ 置信 medium。
- **搜索式逐条写入 `query_log.md`**（如 `教育部 + AI本研贯通 + 强基计划 + 试点`）。

### S3 采集政策原文（分级落盘）
对"已实施/试点/提出"的建议，WebFetch 相关政策：
- **官方公开政策** → 存正文到 `materials/<编号>__<政策名>.md`；
- **版权不清/新闻报道** → 只存"**摘录 + 元数据(政策名/发文号/日期) + URL + 抓取时间**"，**不无差别全文落盘**。

### S4 延展研究（基于下载原文 + 40 行 profile）
读 `materials/` 的政策原文 + `institution_profile.md`（教育落点 + 五步桥接），按**缺口六分类**找该政策的缺口：
> **覆盖 / 执行 / 评价 / 配套 / 区域均衡 / 制度化**
只要命中任一缺口 → 写出"已做 X、缺 Y"的 `gap_evidence`（**必须引下载原文**），据此把建议改写为补配套/深化/推动落地。**"无缺口"= 六类全无**，才允许判舍弃。

### S5 发散（找真空白）
在该教育子域里，看现有政策**没覆盖**的空白，提真新建议。每条必须填 4 硬门字段：`target`(挂靶)、`domain`(落教育域)、`container`(国情容器)、`three_whys`(为什么做/不照搬/这个版本)，且 `state` 必须经 S2 核查为 `not_found`。**严禁写"国内尚无/首创/空白"**，只能写"未检索到充分公开先例，待人工确认"。

### S6 硬性判定（工具，不靠模型）
把 S1–S5 汇成 `findings.json`（schema 见工具文件末尾注释），跑：
`python3 tools/suggestion_audit_extend.py decide <run_dir>/suggestion_audit/findings.json`
工具按**决策表**裁定，并强制：先例判定须有证据 URL、媒体单独不支撑高置信、延展须有 gap_evidence、发散须过 4 硬门且不伪空白。

**决策表（工具内置）**：
| 先例状态 | 缺口 | 置信 | 裁定 |
|---|---|---|---|
| 已全面实施 | 六类全无 | 高 | **舍弃** |
| 已全面实施 | 有任一缺口 | 高 | **延展**（凭 gap_evidence）|
| 已试点 / 提出未落地 | — | 中高 | **延展**（扩面/制度化/补配套/推动落地）|
| 未搜到 | — | 高 | **保留(真新·待人工确认)** |
| 未搜到 | — | 低 | **降级保留·待核** |

## 输出（report.md）
物料索引 + 逐条裁定（原建议→状态+证据URL+置信→裁定→延展后建议/缺口依据）+ 发散候选 + 一页汇总（舍/延/留/新增计数）。**总体结论**：有"舍弃"项=存在硬冗余→`未达到`（需改建议清单）。**删改与是否并入正文：交人确认。**

## 边界（写死，勿越）
- web 事实只进本备忘、逐条带 URL，**不自动写回正文**；主写作流 KB-only 不动。
- 凡"已实施/试点"判定无官方来源或无 URL → 不成立，降为待核。
- 不臆测空白、不宣称首创。

## 怎么触发
用户调用本 skill 并给一个 run/文章 → 派生一个带 **Read / WebSearch / WebFetch / Write** 的 agent 跑 S0–S6（建议条数多时按条 fan-out S2/S3）。
