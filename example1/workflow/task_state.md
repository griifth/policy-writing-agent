# 临时任务列表与运行日志设计

## 1. 目标

每次启动工作流时，系统都要生成一个临时任务列表。Codex 负责查看这个列表、按顺序触发流程、更新完成情况，并在出错时记录错误。

工作流结束后，临时任务列表会归档到运行日志中，成为本次运行的可追溯记录。

## 2. 文件位置

每个运行目录中保存两个状态文件：

```text
runs/<run_id>/
  task_state.md
  run_log.md
```

文件职责：

- `task_state.md`：运行中的临时任务列表，供 Codex 随时查看和更新。
- `run_log.md`：运行结束后的归档日志，记录本次流程的任务完成情况、错误、重试和最终产物。

## 3. 任务状态

任务状态使用自然文本，不要求 JSON。

状态枚举：

- `pending`：尚未开始。
- `running`：正在执行。
- `done`：已完成。
- `failed`：执行失败。
- `skipped`：跳过。
- `blocked`：等待人工确认或外部条件。

## 4. 临时任务列表格式

`task_state.md` 建议格式：

```text
# 临时任务列表

运行 ID：{{run_id}}
报告主题：{{topic}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}
当前状态：running

## 任务列表

| 序号 | 任务 ID | 模块 | 功能 | 执行者 | 状态 | 输入 | 输出 | 错误记录 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | init.resolve_notebook | 解析知识库 | 编排 | Codex | pending | input.yaml | notebook_resolution.md |  |
| 2 | prompt.build_all | 拼装提示词 | 拼装 | Codex | pending | 原始提示词 | generated_prompts/ |  |
| 3 | ch1.1a.retrieve | 1A 顶层设计检索 | 检索 | NotebookLM skill | pending | generated_prompts/ch1_1a.md | retrieval_outputs/chapter1_top_design.md |  |
| 4 | ch1.2a.retrieve | 2A 实施机制检索 | 检索 | NotebookLM skill | pending | generated_prompts/ch1_2a.md | retrieval_outputs/chapter1_implementation.md |  |
| 5 | ch1.1b.write | 1B 顶层设计写作 | 写作 | DeepSeek v4 Pro | pending | 1A 检索结果 | chapter_drafts/chapter1_top_design.md |  |
| 6 | ch1.2b.write | 2B 实施机制写作 | 写作 | DeepSeek v4 Pro | pending | 2A 检索结果 | chapter_drafts/chapter1_implementation.md |  |
| 7 | ch1.3a.plan | 3A 主题特性定题 | 构思 | DeepSeek v4 Pro | pending | topic | extracted_materials/chapter1_topic_specific_title.md |  |
| 8 | ch1.3b.retrieve | 3B 主题特性检索 | 检索 | NotebookLM skill | pending | 3A 构思产物 | retrieval_outputs/chapter1_topic_specific.md |  |
| 9 | ch1.3c.write | 3C 主题特性写作 | 写作 | DeepSeek v4 Pro | pending | 3B 检索结果 | chapter_drafts/chapter1_topic_specific.md |  |
| 10 | ch1.assemble | 第一章组装 | 编排 | Codex | pending | 第一章小节草稿 | chapter_drafts/chapter1.md |  |
| 11 | ch1.review | 第一章审查 | 审查 | DeepSeek v4 Pro | pending | chapter1.md + 检索材料 | review_reports/chapter1_review.md |  |
| 12 | ch2.topic.plan | 第二章目的层定题 | 构思 | DeepSeek v4 Pro | pending | topic | extracted_materials/chapter2_topic.md |  |
| 13 | ch2.retrieve | 第二章资料铺料 | 检索 | NotebookLM skill | pending | 第二章主题 | retrieval_outputs/chapter2_materials.md |  |
| 14 | ch2.dimension.plan | 第二章维度凝练 | 构思 | DeepSeek v4 Pro | pending | 第二章检索结果 | extracted_materials/chapter2_dimensions.md |  |
| 15 | ch2.write | 第二章正文写作 | 写作 | DeepSeek v4 Pro | pending | 第二章检索结果 + 维度 | chapter_drafts/chapter2.md |  |
| 16 | ch2.review | 第二章审查 | 审查 | DeepSeek v4 Pro | pending | chapter2.md + 检索材料 | review_reports/chapter2_review.md |  |
| 17 | ch3.write | 第三章政策建议写作 | 写作 | DeepSeek v4 Pro | pending | chapter1.md + chapter2.md | chapter_drafts/chapter3.md |  |
| 18 | final.assemble | 报告组装 | 编排 | Codex | pending | chapter_drafts/ | final_report.md |  |
| 19 | final.review | 最终审查 | 审查 | DeepSeek v4 Pro | pending | final_report.md + 检索材料 | review_reports/final_review.md |  |
| 20 | full.review | 全文内容结构审查 | 审查 | DeepSeek v4 Pro | pending | final_report.md + 审查意见模板 | review_reports/fulltext_content_structure_review.md |  |
| 21 | full.rewrite | 全文内容结构修改 | 写作/修改 | DeepSeek v4 Pro | pending | final_report.md + 全文审查报告 | final_report_reviewed.md |  |
| 22 | run.archive_log | 归档运行日志 | 编排 | Codex | pending | task_state.md | run_log.md |  |

## 错误详情

暂无。
```

## 5. Codex 调度规则

Codex 每次执行任务前都应查看 `task_state.md`。

调度规则：

1. 找到第一个 `pending` 任务。
2. 检查其依赖输入是否存在。
3. 将任务状态更新为 `running`。
4. 执行对应模块。
5. 成功后写入输出文件，并将状态改为 `done`。
6. 失败后将状态改为 `failed`，在错误记录中写明错误摘要，并在“错误详情”追加完整错误。
7. 如果错误需要用户确认，将状态改为 `blocked`。
8. 如果某模块因设计暂缓而不执行，将状态改为 `skipped` 并写明原因。

## 6. 错误记录格式

错误详情建议格式：

```text
## 错误详情

### {{task_id}}

- 时间：{{timestamp}}
- 状态：failed 或 blocked
- 错误摘要：……
- 触发命令或调用：……
- 已保存输出：……
- 下一步建议：重试 / 人工确认 / 跳过 / 修改输入
```

## 7. 运行日志归档

流程结束后，Codex 将 `task_state.md` 的最终状态复制或汇总到 `run_log.md`。

`run_log.md` 至少包含：

- 运行 ID。
- 输入主题和知识库名称。
- Notebook 解析结果。
- 每个任务的最终状态。
- 错误和重试记录。
- 最终产物列表。
- 是否完整通过审查。

## 8. LLM 查看方式

由于 `task_state.md` 是普通 Markdown，LLM 可以随时读取它，判断：

- 当前流程走到哪一步。
- 哪些任务完成了。
- 哪些任务失败了。
- 失败是否需要重试或人工确认。
- 下一步应该触发哪个模块。
