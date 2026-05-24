# Codex 写作 Agent 架构说明

本文说明 Codex 如何调度一组写作 agent，基于 NotebookLM 知识库完成一次政策研究报告写作任务。它描述的是当前 `policy-writing-agent` MVP 的实际架构：NotebookLM 负责知识库检索，Codex 负责流程编排、材料整理、章节生成和审查控制；部分写作 agent 可以切换到 OpenAI 或 Anthropic API 驱动。

## 一句话概览

一次写作任务不是让单个模型直接“写一篇报告”，而是由 Codex 按固定工作流操作多个 agent：

```text
任务配置 -> 查询规划 -> NotebookLM 检索 -> 材料包 -> 矩阵 -> 报告计划 -> 章节草稿 -> Review Gates -> 最终报告
```

每一步都会落盘为结构化产物，后一步只能读取前一步的产物继续加工。这样做的目的，是把“知识库信息”“写作组织判断”“审查结论”分开，避免报告看起来完整但无法追溯。

## 三层架构

当前系统可以分成三层。

```text
┌─────────────────────────────────────────────────────┐
│ 控制面 Control Plane                                 │
│ runtime_console.html / runtime_console_server.py     │
│ 选择 real/mock、Codex/API 模式、provider、agent driver │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│ 编排面 Orchestration                                 │
│ runner.py                                            │
│ 读取配置、调度 agent、控制并发、写 workflow_state       │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│ 执行面 Agent Runtime                                 │
│ QueryPlanner / NotebookLMAdapter / MaterialPackAgent │
│ MatrixBuilder / SectionComposer / ReviewAgentGroup   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│ 产物面 Artifacts                                     │
│ query_results / material_packages / matrices          │
│ section_drafts / review_reports / final_report         │
└─────────────────────────────────────────────────────┘
```

## 关键配置

一次任务由 YAML 配置驱动。真实知识库任务使用：

```text
config/report_task.real.yaml
```

mock 回归任务使用：

```text
config/report_task.yaml
```

核心配置分三块：

```yaml
task:
  topic: "AI 教育政策热点识别与前沿研判"
  notebook_id: "..."
  sections:
    - hotspot
    - theme
    - comparison
    - impact
    - insight

execution:
  mode: "real"
  notebooklm_cli_path: "/.../.venv/bin/notebooklm"
  max_concurrency: 2

agent_runtime:
  mode: "local"
  default_driver: "local"
  provider_defaults:
    openai: ...
    anthropic: ...
  agents:
    SectionComposerAgent:
      driver: "local"
      api:
        provider: "anthropic"
```

`task` 定义报告要做什么；`execution` 定义 NotebookLM 和运行参数；`agent_runtime` 定义每个写作 agent 由 Codex/local 驱动，还是由 OpenAI/Anthropic API 驱动。

## 控制台如何参与

控制台由两个文件组成：

```text
runtime_console.html
src/runtime_console_server.py
```

启动方式：

```bash
cd /Users/hujingkai/Documents/New\ project/policy-writing-agent
python3 src/runtime_console_server.py --host 127.0.0.1 --port 8787
```

浏览器打开：

```text
http://127.0.0.1:8787/
```

控制台负责：

- 在 `real` 与 `mock` 配置之间切换。
- 在 `Codex / Local` 与 `API Assisted` 之间切换。
- 编辑 OpenAI / Anthropic 的 `base_url`、`model`、`temperature`、`max_tokens` 等配置。
- 给每个 agent 选择 `local` 或 `llm_api` driver。
- 保存回 YAML。
- 校验 API 环境变量是否存在。

控制台不保存 API key 明文，只保存环境变量名：

```yaml
api_key_env: "OPENAI_API_KEY"
api_key_env: "ANTHROPIC_API_KEY"
```

## Codex 在一次写作任务中的职责

Codex 是整个流程的总编排者。它不只是生成文本，而是按以下方式操作 agent：

1. 读取任务配置。
2. 校验 agent runtime 配置。
3. 生成查询任务。
4. 调用 NotebookLM CLI 获取知识库回答。
5. 把回答整理成材料包。
6. 生成矩阵和章节契约。
7. 调用本地或 API 驱动的写作 agent 生成计划和章节。
8. 执行 review gates。
9. 组装最终报告和 manifest。

Codex 的核心控制入口是：

```text
src/runner.py
```

`runner.py` 负责把各个模块串起来，并把每个阶段写入：

```text
runs/<run_id>/workflow_state.json
```

## Agent 职责表

| Agent | 模块 | 主要输入 | 主要输出 | 当前驱动 |
|---|---|---|---|---|
| QueryPlannerAgent | `query_planner.py` | `task_spec`、章节列表 | `query_jobs.json` | local |
| NotebookLMAdapter | `notebooklm_adapter.py` | QueryJob、Notebook ID | `query_results/*.json` | NotebookLM CLI |
| MaterialPackAgent | `material_pack_builder.py` | QueryResult | `material_packages/*.json` | local |
| MatrixBuilderAgent | `matrix_builder.py` | MaterialPackage | 各类矩阵 JSON | local |
| SectionContractAgent | `section_planner.py` | task、matrices、contracts | `POLICY_REPORT_PLAN.md`、`section_plan.json` | local 或 API |
| SectionComposerAgent | `section_composer.py` | material packages、claims、matrices | `section_drafts/*.md` | local 或 API |
| PlanReviewerAgent | `review_gates.py` | query jobs | `plan_review.json` | local |
| RetrievalCompletenessGate | `review_gates.py` | query jobs/results | `retrieval_completeness_review.json` | local |
| MaterialPackAudit | `review_gates.py` | material package audit | `material_pack_audit.json` | local |
| MaterialCoverageReviewerAgent | `review_gates.py` | material audits | `material_coverage_review.json` | local |
| ClaimAuditAgent | `review_gates.py` | section drafts、claims | `claim_scope_review.json` | local |
| KillArgumentAgent | `review_gates.py` | final report | `kill_argument_review.json` | local |
| ReportAssembler | `report_assembler.py` | section drafts、reviews、matrices | `final_report.md` | local |
| IntegrationAgent | `runner.py` / `manifest.py` | run artifacts | `MANIFEST.md`、`run_summary.json` | local |

目前 API 驱动已经接线到：

```text
SectionContractAgent
SectionComposerAgent
```

其他 reviewer 和材料处理 agent 仍保持 local，是为了避免审查逻辑被非确定性模型改写。

## 每个 Agent 详解

本节逐个说明当前 MVP 中的 agent。这里的 agent 不是都对应一个独立进程，而是 Codex 在 `runner.py` 中按阶段调用的一组明确职责模块。它们共同形成“可追溯写作流水线”。

### 1. QueryPlannerAgent

`QueryPlannerAgent` 负责把用户的报告任务拆成一组 NotebookLM 查询任务。

对应模块：

```text
src/query_planner.py
```

主要输入：

```text
task_spec.json
config/dimension_registry.yaml
config/section_contracts.yaml
```

主要输出：

```text
query_jobs.json
```

它会读取任务主题、Notebook ID、需要生成的章节，然后生成一组 QueryJob。当前默认包括：

```text
01_global_scan
02_theme_scan
03_deep_dive
04_comparison
05_impact
06_insight
```

每个 QueryJob 都会指定：

- 应该问哪个 notebook；
- 属于哪个章节；
- 是什么 query type；
- prompt 是什么；
- 预期返回哪些字段；
- 结果应该写入哪个文件。

它的核心价值是把“写一篇报告”拆成可检查的小问题。如果没有这个 agent，后续 NotebookLM 检索会变成一次性大 prompt，难以知道缺了什么材料。

当前实现方式是 local deterministic。也就是说，它由代码规则生成 QueryJob，不调用外部 LLM API。这样做的好处是稳定、可复现；缺点是 query planning 还不够智能，后续可以让它根据材料质量自动生成 follow-up query。

失败风险：

- 没覆盖 required section；
- 预期字段设计不合理；
- prompt 太宽，导致 NotebookLM 返回一个大综合主题；
- query type 与 section contract 不匹配。

对应审查：

```text
review_reports/plan_review.json
```

目前这个 review 主要检查 section coverage，后续应升级为真正的 QueryPlan quality review。

### 2. NotebookLMAdapter

`NotebookLMAdapter` 是系统中唯一直接调用 NotebookLM CLI 的 agent。

对应模块：

```text
src/notebooklm_adapter.py
```

主要输入：

```text
query_jobs.json
notebook_id
notebooklm_cli_path
```

主要输出：

```text
notebooklm_auth.json
notebooklm_sources.json
query_results/*.json
```

它负责三件事：

1. 检查 NotebookLM 登录状态；
2. 列出 notebook 中的 sources；
3. 对每个 QueryJob 调用 `notebooklm ask`。

真实调用形态大致是：

```bash
notebooklm ask -n <notebook_id> --json "<prompt>"
```

它还会解析 NotebookLM 返回内容，把 JSON 字段提取到：

```text
structured_answer
parsed_fields
```

runner 会额外记录每个请求的耗时：

```text
runner_started_at
runner_finished_at
runner_duration_sec
runner_concurrency
```

当前并发由配置控制：

```yaml
execution:
  max_concurrency: 2
```

它的核心价值是把 NotebookLM 变成一个可编排的信息检索层，而不是让写作 agent 直接访问网页或自己编造材料。

当前实现方式是 NotebookLM CLI，不是 OpenAI/Anthropic API。这个 agent 不应该切到写作 API，因为它的职责是知识库检索。

失败风险：

- NotebookLM auth 失效；
- CLI 不在路径中；
- NotebookLM 返回非 JSON；
- 单次请求超时；
- 并发时共享 notebook conversation，造成上下文污染；
- `references` 为空，导致来源链路不足。

对应审查：

```text
review_reports/retrieval_completeness_review.json
```

### 3. MaterialPackAgent

`MaterialPackAgent` 负责把 NotebookLM 的多份回答整理成写作材料包。

对应模块：

```text
src/material_pack_builder.py
```

主要输入：

```text
query_results/*.json
config/dimension_registry.yaml
```

主要输出：

```text
material_packages/*.json
material_package_audit.json
```

NotebookLM 返回的是按问题组织的答案，而报告写作需要的是按“热点/主题/判断”组织的材料。MaterialPackAgent 就负责做这种结构转换。

一个材料包通常包含：

- `package_id`
- `hotspot`
- `main_theme`
- `cross_themes`
- `policy_points`
- `policy_tools`
- `actors`
- `mechanisms`
- `risks`
- `claim_candidates`
- `caution_notes`
- `missing_questions`
- `raw_fields`

它的核心价值是把知识库回答压缩成“可写单元”。后续章节不能直接任意使用 NotebookLM 原始回答，而应该通过 MaterialPackage 取材。

当前实现方式是 local deterministic。它会合并 query results，并做一些字段标准化。

当前限制比较重要：MVP 里仍偏向生成单一材料包，比如：

```text
mp_ai_literacy
```

这会把多个真实热点压成一个综合主题。后续应该改成多热点多材料包，每个热点一个包。

失败风险：

- 多个 query result 同名字段互相覆盖；
- 热点边界丢失；
- NotebookLM 的 `missing_questions` 没有进入 follow-up loop；
- 来源引用没有下传；
- 材料包字段完整，但实际论证粒度过粗。

对应审查：

```text
material_package_audit.json
review_reports/material_pack_audit.json
review_reports/material_coverage_review.json
```

### 4. MatrixBuilderAgent

`MatrixBuilderAgent` 负责把材料包转换成报告结构矩阵。

对应模块：

```text
src/matrix_builder.py
```

主要输入：

```text
material_packages/*.json
```

主要输出：

```text
hotspot_theme_matrix.json
comparison_matrix.json
impact_table.json
insight_table.json
policy_claim_material_matrix.json
```

它把“材料包”进一步变成“章节可消费的数据结构”。例如：

`hotspot_theme_matrix` 用于回答：

- 这个热点是什么？
- 属于哪个主主题？
- 有哪些交叉主题？

`comparison_matrix` 用于回答：

- 政策目标是什么？
- 目标群体是谁？
- 政策工具是什么？
- 风险治理怎么设计？

`impact_table` 用于回答：

- 对教育治理有什么影响？
- 对学校实践有什么影响？
- 对教师发展有什么影响？
- 对学生学习和教育评价有什么影响？

`policy_claim_material_matrix` 用于约束：

- 哪些 claim 可以写？
- 每个 claim 对应哪些 material package？
- 允许进入哪些章节？
- 支撑强度是什么？
- 需要什么 caution？

它的核心价值是让章节写作不直接面对杂乱材料，而是面对已经结构化的中间表。

当前实现方式是 local deterministic。它适合保持 deterministic，因为矩阵是报告可追溯性的骨架，不宜完全交给非确定性模型自由生成。

失败风险：

- 矩阵行数不足；
- 单一材料包导致 comparison 不是真比较；
- claim 没有绑定到足够章节；
- support_level 与材料强度不一致；
- 矩阵没有 `package_id`，追溯不够细。

### 5. SectionContractAgent

`SectionContractAgent` 负责生成报告计划和章节契约执行计划。

对应模块：

```text
src/section_planner.py
```

主要输入：

```text
task_spec.json
hotspot_theme_matrix.json
comparison_matrix.json
impact_table.json
insight_table.json
policy_claim_material_matrix.json
config/section_contracts.yaml
```

主要输出：

```text
POLICY_REPORT_PLAN.md
section_plan.json
```

它要解决的问题是：有了材料和矩阵之后，报告应该怎样展开。

`POLICY_REPORT_PLAN.md` 通常包括：

- Metadata；
- Hotspot Candidates；
- PolicyClaim-Material Matrix；
- Section Contracts；
- Entry Decision。

`section_plan.json` 则给每个章节列出：

- 使用哪个 section contract；
- 绑定哪些 claim；
- 当前 status 是什么。

这个 agent 是当前已经接线 API 的 agent 之一。

local 模式下：

```text
section_planner.py
```

会按模板生成计划，稳定但比较机械。

API 模式下：

Codex 会把 task、matrices、section contracts 和 local seed plan 一起发给 OpenAI/Anthropic，让模型生成更自然、更像正式写作流程的计划。

约束是：API 只能组织已有材料，不能新增材料外事实。

失败风险：

- 计划没有反映材料缺口；
- Entry Decision 只是模板句；
- 章节契约与实际矩阵不匹配；
- top_k_hotspots 没达到，但计划仍写成通过；
- 比较章没有比较对象。

后续应新增真正的 `ReportPlanQualityReview` 来审这个 agent 的输出。

### 6. SectionComposerAgent

`SectionComposerAgent` 负责生成每个章节的 Markdown 草稿。

对应模块：

```text
src/section_composer.py
```

主要输入：

```text
section_plan.json
material_packages/*.json
policy_claim_material_matrix.json
hotspot_theme_matrix.json
comparison_matrix.json
impact_table.json
insight_table.json
```

主要输出：

```text
section_drafts/01_hotspot.md
section_drafts/02_theme.md
section_drafts/03_comparison.md
section_drafts/04_impact.md
section_drafts/05_insight.md
```

它负责把结构化材料写成读者能看的章节。

当前章节包括：

- 热点梳理；
- 主题归类；
- 政策前沿比较；
- 影响研判；
- 启发建议。

这个 agent 也是当前已经接线 API 的 agent。

local 模式下：

`section_composer.py` 使用模板和表格拼出章节，优点是稳定、不会乱发挥；缺点是文字偏机械，过渡和论证力度有限。

API 模式下：

Codex 会把以下内容发给 OpenAI/Anthropic：

- 当前章节 ID；
- 章节契约；
- 材料包；
- claim matrix；
- 各类矩阵；
- local draft seed。

并要求：

```text
不得引入材料外事实。
不确定或缺失处用 MATERIAL_NEEDED 标记。
保留章节标题。
保留本节契约检查。
```

它的核心价值是把“结构正确的材料”转成“可读的报告章节”。

失败风险：

- 复述材料但没有形成段落逻辑；
- 建议章新增材料外判断；
- 影响章和建议章重复；
- claim 没有支撑；
- 忽略 `MATERIAL_NEEDED`；
- API 模式下语言更自然但边界更难控。

对应审查：

```text
review_reports/claim_scope_review.json
review_reports/kill_argument_review.json
```

后续还应新增 ReverseOutlineStructureReviewer，专门审章节结构。

### 7. PlanReviewerAgent

`PlanReviewerAgent` 当前负责检查 query plan 是否覆盖了所需章节。

对应模块：

```text
src/review_gates.py
```

主要输入：

```text
query_jobs.json
task.sections
```

主要输出：

```text
review_reports/plan_review.json
```

当前它做的事情很简单：检查任务要求的章节是否都至少有一个 QueryJob 覆盖。

它的核心价值是防止流程一开始就漏掉章节。例如任务要求生成 `impact` 章，但没有生成 impact query，那后续报告一定缺材料。

当前限制也很明显：它并不真正审 `POLICY_REPORT_PLAN.md` 的质量。因此“PlanReviewerAgent”这个名字现在偏大，实际更像 `QueryPlanCoverageGate`。

失败风险：

- 章节覆盖了，但 query type 不对；
- prompt 不够好；
- 预期字段和维度 registry 不一致；
- 报告计划质量差但仍 PASS。

后续建议：

- 保留当前 coverage gate；
- 新增 `ReportPlanQualityReviewerAgent`，专门审报告计划质量。

### 8. RetrievalCompletenessGate

`RetrievalCompletenessGate` 负责检查 NotebookLM 查询结果是否完整。

对应模块：

```text
src/review_gates.py
```

主要输入：

```text
query_jobs.json
query_results/*.json
```

主要输出：

```text
review_reports/retrieval_completeness_review.json
```

它会逐个检查：

- 每个 QueryJob 是否都有结果；
- 每个结果是否有 `parsed_fields`；
- `parsed_fields` 是否包含 expected fields。

如果缺结果或缺字段，就会生成：

```text
followup_queries
```

并把 verdict 设成：

```text
BLOCKED
```

它的核心价值是阻止“材料没取到，但报告继续写”的情况。

当前限制：follow-up query 还没有真正回流执行。也就是说，系统能发现缺口，但还没有自动进入“补问 NotebookLM -> 重建材料包”的闭环。

失败风险：

- NotebookLM 返回了自然语言，无法解析 JSON；
- expected fields 过于严格；
- NotebookLM 回答空字段；
- CLI 报错但流程没有及时停止。

### 9. MaterialPackAudit

`MaterialPackAudit` 负责审查材料包字段是否满足 schema 要求。

对应模块：

```text
src/material_pack_builder.py
src/review_gates.py
```

主要输入：

```text
material_packages/*.json
config/dimension_registry.yaml
```

主要输出：

```text
material_package_audit.json
review_reports/material_pack_audit.json
```

它会检查每个材料包是否包含最小 required fields。比如热点名称、主题、政策点、风险、claim candidates 等。

它的核心价值是防止章节写作阶段面对空材料或半成品材料。

失败风险：

- schema 字段存在，但内容过泛；
- `missing_questions` 有值，但 audit 仍 PASS；
- 材料包字段由多个 query 粗暴合并，丢掉来源边界；
- 多热点被压缩成一个材料包。

后续应把 audit 从“字段存在”升级为“字段质量 + 来源引用 + 支撑强度”审查。

### 10. MaterialCoverageReviewerAgent

`MaterialCoverageReviewerAgent` 负责从整体上判断材料包集合是否足够进入写作。

对应模块：

```text
src/review_gates.py
```

主要输入：

```text
material_package_audit.json
```

主要输出：

```text
review_reports/material_coverage_review.json
```

它和 `MaterialPackAudit` 的区别是：

- `MaterialPackAudit` 看每个包有没有缺字段；
- `MaterialCoverageReviewerAgent` 看整个材料集合是否还有 blocked package。

它的核心价值是作为材料阶段的总闸门。只要还有 BLOCKED 材料包，原则上就不应该进入 polished 写作。

当前限制：它只看 audit verdict，没有真正判断材料覆盖面是否足够。例如只有一个热点也可以 PASS。

后续应增加：

- 热点数量检查；
- 主题覆盖检查；
- source coverage 检查；
- follow-up gap 检查。

### 11. ClaimAuditAgent

`ClaimAuditAgent` 负责审查章节草稿中的判断是否受材料约束。

对应模块：

```text
src/review_gates.py
```

主要输入：

```text
section_drafts/*.md
policy_claim_material_matrix.json
```

主要输出：

```text
review_reports/claim_scope_review.json
```

当前实现比较轻：它主要检查 claim candidates 是否出现在草稿中。如果候选 claim 没有被使用，会给出 WARN。

它的核心价值是提醒写作阶段不要脱离 claim-material matrix。

但当前它还不是严格意义上的“断言审计”。真正严格的 ClaimAudit 应该做：

- 从章节草稿中抽取每个判断句；
- 判断该句是 source_grounded、derived、agent_structural 还是 unsupported；
- 每个 source_grounded/derived 判断都要绑定 material package 和来源；
- unsupported 判断必须移除或降级为待追问。

失败风险：

- agent 写了材料外结论；
- claim matrix 太粗，无法覆盖章节中每个判断；
- 弱支撑 claim 被写成强结论；
- API 生成文本更自然，但引入未经支撑的扩展判断。

### 12. KillArgumentAgent

`KillArgumentAgent` 负责对最终报告做最后一轮反证审查。

对应模块：

```text
src/review_gates.py
```

主要输入：

```text
final_report.md
```

主要输出：

```text
review_reports/kill_argument_review.json
```

当前它重点检查最终报告中是否还有：

```text
MATERIAL_NEEDED
```

并列出几个最强反对意见，例如：

- 材料是否足以支撑热点升温判断；
- 比较维度是否对所有热点一致；
- 影响与建议是否超出 NotebookLM 材料包。

它的核心价值是模拟“最严格 reviewer”在报告交付前提出反对意见。

当前限制：它还只是规则检查，没有真正逐段反驳报告论证。

后续可以升级为：

- 对每章提出 strongest objection；
- 检查结论是否过度推断；
- 检查建议是否超出材料；
- 检查是否有政策语气过强但支撑不足的表达。

### 13. ReportAssembler

`ReportAssembler` 负责把章节草稿、材料包、矩阵和 review reports 组装成最终报告。

对应模块：

```text
src/report_assembler.py
```

主要输入：

```text
section_drafts/*.md
material_packages/*.json
matrices
review_reports/*.json
```

主要输出：

```text
final_report.md
```

它的职责不是重新写作，而是整合已经生成的章节和审查信息。

最终报告通常包括：

- 报告说明；
- 各章节正文；
- 材料包附录；
- 判断-材料矩阵；
- review gate 汇总。

它的核心价值是保证最终报告不是一个孤立 Markdown，而是带着材料和审查轨迹一起交付。

失败风险：

- 章节顺序错误；
- 附录信息太少；
- review report 没有被完整纳入；
- final report 与 section drafts 不一致。

### 14. IntegrationAgent

`IntegrationAgent` 是 Codex 在 `runner.py` 中承担的整体集成角色。

对应模块：

```text
src/runner.py
src/manifest.py
```

主要输入：

```text
所有 run artifacts
```

主要输出：

```text
workflow_state.json
MANIFEST.md
run_summary.json
runs/latest
```

它负责：

- 创建 run 目录；
- 写入每个阶段的 workflow state；
- 处理 latest 目录；
- 收集 artifacts；
- 生成 manifest；
- 返回 run summary。

它的核心价值是让一次写作任务成为一个可复盘、可审计、可比较的 run，而不是一堆散落文件。

失败风险：

- 某个阶段失败后仍继续；
- latest 被 mock run 覆盖；
- manifest 没有记录关键产物；
- review pass 但输入文件后来被改动，导致审查陈旧。

后续应为 IntegrationAgent 增加：

- artifact hash；
- stale check；
- review trace path；
- run-level verification。

## 一次写作任务的完整时序

### 1. Preflight

Codex 先读取 YAML 配置，并构造 agent runtime：

```text
src/agent_runtime.py
```

它会生成：

```text
agent_runtime.json
agent_runtime_validation.json
```

如果某个 agent 被配置为 `llm_api`，但缺少 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`，preflight 会报错，不会继续生成报告。

### 2. Task Spec

Codex 把 `task` 配置落盘：

```text
task_spec.json
```

这一步锁定本次写作任务的主题、受众、Notebook ID、章节范围和追溯责任人。

### 3. Query Planning

`QueryPlannerAgent` 把报告任务拆成 NotebookLM 查询任务：

```text
query_jobs.json
```

当前默认生成 6 类查询：

```text
01_global_scan
02_theme_scan
03_deep_dive
04_comparison
05_impact
06_insight
```

每个 QueryJob 包含：

- `id`
- `section`
- `query_type`
- `notebook_id`
- `prompt`
- `expected_fields`
- `output_target`

### 4. NotebookLM Retrieval

`NotebookLMAdapter` 调用本地 CLI：

```bash
/Users/hujingkai/Desktop/notebookcli2report/notebooklm-py-main/.venv/bin/notebooklm ask -n <notebook_id> --json "<prompt>"
```

所有查询结果保存到：

```text
query_results/*.json
```

当前真实模式下支持并发：

```yaml
execution:
  max_concurrency: 2
```

runner 会为每个结果记录：

```json
{
  "runner_started_at": "...",
  "runner_finished_at": "...",
  "runner_duration_sec": 49.938,
  "runner_concurrency": 2
}
```

这让后续可以判断 NotebookLM 响应速度、retry 情况和查询瓶颈。

### 5. Retrieval Review

`RetrievalCompletenessGate` 检查每个 QueryJob 是否有结果，以及结果里是否包含预期字段。

输出：

```text
review_reports/retrieval_completeness_review.json
```

如果缺结果或缺字段，会返回 `BLOCKED`。这里的 `BLOCKED` 是 workflow gate 状态，不是 NotebookLM 的限流状态。

### 6. Material Package

`MaterialPackAgent` 把 NotebookLM 的多轮回答合并成材料包：

```text
material_packages/*.json
```

材料包是章节写作的最小可信输入。它把知识库回答整理成：

- 热点名称
- 主题归类
- 政策工具
- 关键主体
- 实施机制
- 风险
- claim candidates
- caution notes
- missing questions

当前 MVP 仍主要生成一个材料包：

```text
material_packages/mp_ai_literacy.json
```

后续优化方向是多热点多材料包，每个热点一个 `MaterialPackage`。

### 7. Material Audit

材料包生成后，系统会执行两类审查：

```text
material_package_audit.json
review_reports/material_pack_audit.json
review_reports/material_coverage_review.json
```

这一步检查材料包是否具备最小可写字段。如果缺少必需字段，报告不应该继续进入 polished 写作。

### 8. Matrix Building

`MatrixBuilderAgent` 把材料包转换成报告写作可用的中间矩阵：

```text
hotspot_theme_matrix.json
comparison_matrix.json
impact_table.json
insight_table.json
policy_claim_material_matrix.json
```

矩阵的作用是把材料从“回答文本”变成“章节结构”。例如：

- `hotspot_theme_matrix` 支撑热点梳理和主题归类。
- `comparison_matrix` 支撑政策前沿比较。
- `impact_table` 支撑影响研判。
- `policy_claim_material_matrix` 约束哪些判断可以进入哪些章节。

### 9. Report Plan

`SectionContractAgent` 根据 task、matrices 和 section contracts 生成：

```text
POLICY_REPORT_PLAN.md
section_plan.json
```

如果该 agent 使用 local driver，计划由 `section_planner.py` 的规则生成。

如果该 agent 使用 API driver，Codex 会把 task、matrices、section contracts 和 local seed plan 发送给 OpenAI/Anthropic，让 API 生成更自然的计划文本。

关键约束是：API 只能基于输入产物写计划，不能新增材料外事实。

### 10. Section Drafting

`SectionComposerAgent` 逐章生成草稿：

```text
section_drafts/01_hotspot.md
section_drafts/02_theme.md
section_drafts/03_comparison.md
section_drafts/04_impact.md
section_drafts/05_insight.md
```

local 模式下，章节由 `section_composer.py` 规则拼接。

API 模式下，Codex 会把以下内容作为上下文发给外部模型：

- 当前 section id
- section contract
- material packages
- claims
- matrices
- local draft seed

并要求模型遵守：

```text
不得引入材料外事实。
不确定或缺失处用 MATERIAL_NEEDED 标记。
保留章节标题和“本节契约检查”。
```

### 11. Claim Review

`ClaimAuditAgent` 检查章节草稿是否只使用已知 claim candidates。

输出：

```text
review_reports/claim_scope_review.json
```

当前 MVP 的 claim review 仍偏轻，只检查候选 claim 是否被使用。后续应升级成“报告每个断言都能追溯到材料”的强审查。

### 12. Final Assembly

`ReportAssembler` 汇总章节草稿、材料包、矩阵和 review reports，生成：

```text
final_report.md
```

最终报告通常包含：

- 摘要
- 热点梳理
- 主题归类
- 政策前沿比较
- 影响研判
- 启发建议
- 附录：材料包、矩阵、审查表

### 13. Kill Argument Review

`KillArgumentAgent` 对最终报告做最后一轮反证审查，当前重点检查是否仍有：

```text
MATERIAL_NEEDED
```

输出：

```text
review_reports/kill_argument_review.json
```

### 14. Manifest and Summary

最后，系统生成：

```text
MANIFEST.md
run_summary.json
workflow_state.json
```

`MANIFEST.md` 列出本次 run 的所有产物和生产者。

`run_summary.json` 给出最终报告路径和各 reviewer verdict。

`workflow_state.json` 记录每个阶段的状态，便于排查失败点。

## Codex/local 与 API Assisted 的差异

### Codex / Local 模式

```yaml
agent_runtime:
  mode: "local"
```

特点：

- 不调用 OpenAI/Anthropic 写作 API。
- 章节结构稳定，结果可预测。
- 适合 smoke test、流程验证、回归测试。
- 写法偏模板化，表达自然度有限。

### API Assisted 模式

```yaml
agent_runtime:
  mode: "llm_api"
```

特点：

- 支持把已接线 agent 切到 `llm_api`。
- 目前主要用于报告计划和章节草稿。
- 可以提高表达质量、段落连贯性和可读性。
- 必须通过 review gates 约束，避免模型新增材料外判断。

示例：

```yaml
SectionComposerAgent:
  driver: "llm_api"
  api:
    provider: "anthropic"
```

或者：

```yaml
SectionContractAgent:
  driver: "llm_api"
  api:
    provider: "openai"
```

## 知识库信息与写作信息的边界

系统里有两类信息来源。

第一类是知识库信息，来自 NotebookLM：

```text
query_results/*.json
```

它负责回答：

- 材料中有哪些热点？
- 哪些政策工具被提到？
- 哪些风险和影响被材料支持？
- 哪些问题还缺材料？

第二类是写作组织信息，由 Codex 或 API agent 生成：

```text
POLICY_REPORT_PLAN.md
section_drafts/*.md
final_report.md
review_reports/*.json
```

它负责回答：

- 报告按什么结构展开？
- 哪些材料进入哪个章节？
- 哪些 claim 可以写成判断？
- 哪些地方需要 caution 或 MATERIAL_NEEDED？
- 最终报告如何组装？

原则是：写作 agent 可以组织、压缩、命名和排序材料，但不能创造知识库外事实。

## 并发模型

NotebookLM 查询由 `runner.py` 控制并发。

当前建议配置：

```yaml
execution:
  max_concurrency: 2
```

2 并发是当前验证过的稳定档位。3 并发能跑通，但更容易出现 `ReadTimeout` 和 retry。由于 NotebookLM CLI 默认会继续同一个 notebook conversation，并发查询也可能共享 server-side conversation，因此 prompt 必须写成独立问题，不能依赖上一轮对话。

## BLOCKED 的含义

`BLOCKED` 是 workflow 自己的审查状态，不是 NotebookLM 的网络状态。

常见原因：

- 某个 QueryJob 没有结果。
- NotebookLM 返回内容无法解析成预期字段。
- 材料包缺少 required fields。
- 后续升级后，引用缺失、热点数不足、审查 stale 等也可以触发 `WARN` 或 `BLOCKED`。

当前系统已经能记录 follow-up questions，但还没有完整实现自动 follow-up loop。后续应在 `runner.py` 中加入：

```text
retrieval -> material audit -> gap detection -> follow-up query -> material rebuild
```

## 当前限制

当前 MVP 已经跑通端到端写作，但还不是最终形态。

主要限制：

- NotebookLM 的引用没有完整下传到材料包和最终报告。
- 材料包仍偏单包，多个热点会被压成一个综合主题。
- follow-up questions 还不会自动回流执行。
- ReviewGate 还没有输入哈希、trace path 和 stale check。
- PlanReview 目前偏 query coverage，不是真正的报告计划质量审查。
- Reverse Outline 结构审查尚未接入，影响章和建议章可能重复。

## 推荐的下一步演进

优先级建议如下：

1. P0：把 NotebookLM 来源引用结构化下传。
2. P0：把单一 MaterialPackage 改成多热点多包。
3. P0：实现 follow-up query loop。
4. P1：把 ReviewGate 升级成带哈希和 trace 的审计记录。
5. P1：新增真正的 ReportPlanQualityReview。
6. P2：新增 ReverseOutlineStructureReviewer。
7. P2：逐步把更多 reviewer 接入 API，但保留 deterministic verifier。

## 读者如何判断一次 run 是否成功

一个成功 run 至少应该满足：

```text
run_summary.json 中所有 verdict 为 PASS 或可接受 WARN
workflow_state.json 没有 ERROR/BLOCKED 阶段
query_results/*.json 都有 expected fields
material_package_audit.json 没有 missing_fields
final_report.md 不含 MATERIAL_NEEDED
MANIFEST.md 能列出所有关键产物
```

如果启用了 API Assisted，还应检查：

```text
agent_runtime.json
agent_runtime_validation.json
```

确认哪些 agent 使用了 API，哪些仍由 Codex/local 驱动。
