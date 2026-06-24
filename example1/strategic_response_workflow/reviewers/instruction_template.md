# 审稿交接（第 {{ITERATION}} 轮）

工作流已生成草稿并**暂停**，等待外部审稿。请由在场编排 agent **派生一个子 agent** 完成审稿，然后续跑工作流。

> 本指令由 `reviewers/instruction_template.md` 模板 + 本次触发的 DNA（`{{SCOPE}}`）的 `review_scope.md` 在运行时生成。改模板或改对应 DNA，下次 handoff 自动反映。

## 审稿范围：{{SCOPE}}
{{SCOPE_DESC}}

## 子 agent 任务
1. 阅读草稿：`{{DRAFT_PATH}}`
2. 以下列标准为尺子（由本次触发的 DNA 决定）：
{{STANDARD_FILES}}
3. 把审查报告写到：`{{OUTPUT_PATH}}`
4. 报告**必须包含一行**：`总体结论：达到` / `总体结论：基本达到` / `总体结论：未达到`。
   发现硬伤要写明（报告含“硬伤/对象错配/工具错配/必须重写”等会判为不达标，触发再修改）。

## 可对账材料（判断产物；reasoning 类范围需逐条核对）
{{CONTEXT_FILES}}

## 写完报告后，续跑工作流
    {{RESUME_CMD}}

机器可读请求：`runs/{{RUN_ID}}/review_io/request_iter{{ITERATION}}.json`
