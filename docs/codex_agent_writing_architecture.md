# Codex 写作 Agent 架构说明

本文说明当前 `policy-writing-agent` 如何由 Codex 作为主 agent，调度多个边界明确的子 agent，基于 NotebookLM 知识库完成一份政策任务或热点研判报告。当前架构把“知识库访问权”和“写作执行器”分开：知识库只走 NotebookLM CLI，章节写作可以按 profile 选择 Codex/local 或 API。

## 当前硬约束

- 只能通过本项目配置的 `notebooklm` CLI 调用 NotebookLM 和知识库资料。
- 不修改 `/Users/hujingkai/.agents/skills/notebooklm/SKILL.md`。
- 不调用浏览器检索、Web 搜索或 ARIS 外部 reviewer。
- Codex 始终是主编排者；`NotebookLMAdapter` 不能切换为 API。
- `notebooklm_only` 下所有写作 agent 都是 Codex/local。
- `api_assisted` 下，已接线的写作 agent 可调用 OpenAI/Anthropic 兼容配置，但只能读取本轮材料包、矩阵、章节契约和 review artifact。
- 缺材料时保留 `MATERIAL_NEEDED` 或 follow-up query，不编造材料。

## 总流程

```text
任务配置
  -> 查询规划
  -> NotebookLM CLI 检索
  -> 材料包
  -> 矩阵
  -> 报告计划
  -> 章节草稿
  -> Review Gates
  -> 最终报告与 Manifest
```

每一步都会落盘。后一步只读取前一步产物继续加工，主 agent 通过运行状态页和任务台账判断当前进度。

## 三层结构

```text
控制面
  runtime_console.html
  src/runtime_console_server.py
  agent_runtime.runtime_profile

编排面
  src/runner.py
  src/progress.py

执行面
  QueryPlannerAgent
  NotebookLMAdapter
  MaterialPackAgent
  MatrixBuilderAgent
  SectionContractAgent
  SectionComposerAgent
  ReviewAgentGroup
  ReportAssembler
  IntegrationAgent
```

## 运行产物

一次运行会生成：

```text
POLICY_REPORT_CONTRACT.md
RUN_STATUS.md
TASK_LEDGER.json
progress.jsonl
workflow_state.json
task_spec.json
query_jobs.json
notebooklm_command_log.jsonl
query_results/*.json
material_packages/*.json
material_package_audit.json
*_matrix.json / *_table.json
POLICY_REPORT_PLAN.md
section_plan.json
section_drafts/*.md
review_reports/*.json
final_report.md
MANIFEST.md
run_summary.json
```

其中：

- `POLICY_REPORT_CONTRACT.md` 是本次报告任务的防漂移合同。
- `RUN_STATUS.md` 是主 agent 恢复任务时第一眼看的状态页。
- `TASK_LEDGER.json` 记录 QueryJob 和章节草稿任务的 owner、状态、输入、输出和时间。
- `progress.jsonl` 记录每个阶段和产物的事件流。
- `MANIFEST.md` 对产物建立 SHA256 索引，便于发现 stale artifact。

## Agent 职责

| Agent | 模块 | 职责边界 |
|---|---|---|
| QueryPlannerAgent | `query_planner.py` | 将任务配置拆成 NotebookLM QueryJob，不直接访问知识库。 |
| NotebookLMAdapter | `notebooklm_adapter.py` | 唯一 CLI 网关，只允许 `auth check`、`source list`、`ask`。 |
| MaterialPackAgent | `material_pack_builder.py` | 将 QueryResult 整理成材料包，暴露缺口问题。 |
| MatrixBuilderAgent | `matrix_builder.py` | 从材料包生成热点-主题、比较、影响、启发和 claim-material 矩阵。 |
| SectionContractAgent | `section_planner.py` | 按章节契约生成报告计划和章节计划。 |
| SectionComposerAgent | `section_composer.py` | 只基于材料包、矩阵和章节契约生成章节草稿；可在 `api_assisted` 下切换到 API 写作。 |
| PlanReviewerAgent | `review_gates.py` | 检查 QueryPlan 是否覆盖任务章节和可运行字段。 |
| RetrievalCompletenessGate | `review_gates.py` | 检查 QueryJob 是否都有结果和必需字段。 |
| MaterialPackAudit | `review_gates.py` | 检查材料包 schema 与缺口。 |
| MaterialCoverageReviewerAgent | `review_gates.py` | 判断材料包是否足以进入写作。 |
| EvidenceUseReviewerAgent | `review_gates.py` | 检查 NotebookLM source/citation refs 是否被传递到材料层。 |
| SectionContractReviewerAgent | `review_gates.py` | 检查章节草稿是否显式满足章节契约。 |
| ClaimAuditAgent | `review_gates.py` | 检查 claim 使用范围、支撑等级和强表述风险。 |
| ReportQualityReviewerAgent | `review_gates.py` | 汇总非绿色 gate，提示报告是否可进入 decision-grade。 |
| DriftReviewerAgent | `review_gates.py` | 复核已审查输入的 SHA256 是否发生变化。 |
| KillArgumentAgent | `review_gates.py` | 从最强反对意见角度检查材料缺口、过度判断和审查状态。 |
| ReportAssembler | `report_assembler.py` | 组装最终报告和审查状态附录。 |
| IntegrationAgent | `runner.py` / `manifest.py` / `progress.py` | 管理运行状态、任务台账、manifest 和 latest 输出。 |

## Codex 主 Agent 如何工作

主 agent 不直接替子 agent 混写全部内容。它负责：

1. 读取 `config/report_task*.yaml`。
2. 校验 `agent_runtime.runtime_profile`、`capability_policy`、provider 和 agent driver。
3. 分派 QueryPlannerAgent 生成 `query_jobs.json`。
4. 让 NotebookLMAdapter 通过 CLI 获取知识库回答。
5. 让 MaterialPackAgent 和 MatrixBuilderAgent 将回答结构化。
6. 让 SectionContractAgent 固化章节契约和报告计划。
7. 让 SectionComposerAgent 生成章节草稿；如果该 agent 配置为 API，Codex 只发送本轮材料和契约构成的 prompt。
8. 让 ReviewAgentGroup 逐层审查。
9. 根据 review verdict 决定是否继续、记录 warning、还是要求下一轮修改。
10. 让 ReportAssembler 与 IntegrationAgent 输出最终报告和 manifest。

主 agent 的关键职责是“规划、分派、审核、统筹、防漂移”，不是越过子 agent 边界直接把检索、材料、章节、审查混成一个不可追溯文本。

## Runtime Profiles

```yaml
agent_runtime:
  runtime_profile: "notebooklm_only"
  default_driver: "codex"
  capability_policy:
    external_calls: ["notebooklm_cli"]
    llm_api: false
    notebooklm_skill_mutation: false
```

`notebooklm_only` 是自动化优化循环的默认安全模式。它允许保留 provider 模板配置，但任何 agent 选择 `driver: api` 都会被 preflight 拒绝。

```yaml
agent_runtime:
  runtime_profile: "api_assisted"
  capability_policy:
    external_calls: ["notebooklm_cli", "llm_api"]
    llm_api: true
    notebooklm_skill_mutation: false
  agents:
    SectionComposerAgent:
      driver: "api"
      provider: "openai"
      model: "<model-name>"
```

`api_assisted` 只改变写作执行器，不改变知识库边界。API agent 收到的是 Codex 组装的材料包、矩阵、claim 和章节契约；它不能直接调用 NotebookLM、浏览器、Web 搜索或本地 skill。

## Review Verdict

Review gate 使用六态：

```text
PASS | WARN | FAIL | BLOCKED | ERROR | NOT_APPLICABLE
```

当前 draft 模式允许带 `WARN` 输出，但会在 `final_report.md` 的审查状态附录和 `review_reports/*.json` 中保留问题。后续若进入更严格 assurance，可让 `FAIL | BLOCKED | ERROR` 阻断最终输出。

## 当前已知差距

- Query prompt 还没有真正加载 `prompts/*.md` 的完整模板。
- `top_k_hotspots` 仍未映射成多个材料包。
- NotebookLM source/citation refs 还没有贯穿到材料包和 claim rows。
- follow-up query 生成后还没有一轮自动补检索。
- 章节草稿还没有显式展开所有 `output_shape` 小标题。

这些差距已经记录在 `docs/optimization_progress.md` 和 `docs/optimization_guardrails.md`，作为后续每 20 分钟自动化优化循环的优先队列。
