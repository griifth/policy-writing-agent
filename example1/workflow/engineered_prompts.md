# 工程化提示词索引

当前阶段不要求模型输出 JSON，也不要求模型直接适配 schema。

工程化提示词只做一件事：在原始提示词基础上，由脚本注入本次主题、NotebookLM 知识库信息、上游材料，并补充最小输出约束。

分块文件：

- `workflow/prompts/README.md`：提示词拼装总原则。
- `workflow/prompts/retrieval.md`：检索功能提示词块。
- `workflow/prompts/planning.md`：构思功能提示词块。
- `workflow/prompts/writing.md`：写作功能提示词块。
- `workflow/prompts/fulltext_review.md`：全文内容结构审查提示词块。
- `workflow/prompts/fulltext_rewrite.md`：全文内容结构修改提示词块。
- `workflow/review_templates/content_structure_review.md`：固定审查意见模板。

五类输出约束：

| 功能 | 执行者 | 输出 |
| --- | --- | --- |
| 检索 | NotebookLM skill | `一、检索内容` + `二、相关文献` |
| 构思 | DeepSeek v4 Pro | 构思产物 |
| 写作 | DeepSeek v4 Pro | 可直接入稿的正文内容 |
| 审查 | DeepSeek v4 Pro | 自然语言审查报告 |
| 修改 | DeepSeek v4 Pro | 修改后的完整报告正文 |

后续如果需要结构化，由脚本在模型返回后包装，不要求模型在当前调用中输出 JSON。
