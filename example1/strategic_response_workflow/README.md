# 战略竞争分析与应对策略写作工作流

本目录是一套独立工作流，用于生成“目标国家战略分析 + 中国应对策略建议”类型政策文章。

工作流不是围绕单一主题写死的脚本。它接收主题、目标国家、战略领域和 NotebookLM 知识库名称，通过 NotebookLM 检索材料，再由 LLM 完成任务重定义、材料角色判断、压力映射、构思、写作、审查和修改。

## 边界

- 只在本目录内读写工作流文件和运行产物。
- NotebookLM 只用于检索指定知识库材料，不修改 NotebookLM skill 或知识库。
- `.env` 只放在本目录，且不提交到 Git。
- `runs/` 为本地运行记录目录，不进入 Git。
- `style_dna/raw/` 和 `style_dna/processed/` 为本地风格素材与中间处理结果，不进入 Git；仓库只保留可复用的 `style_dna/wiki/` 文风规则。

## 目录

- `workflow/runner.py`：主工作流入口。
- `workflow/policy_n_prompt_runner.py`：用户提供“政策N”提示词组的对照运行入口。
- `workflow/deepseek_client.py`：DeepSeek 调用封装，只返回最终答案。
- `workflow/llm_client.py`：LLM 后端选择器，支持 DeepSeek 和 Anthropic-compatible 接口。
- `workflow/notebooklm_client.py`：NotebookLM CLI 调用封装。
- `prompts/`：检索、判断、构思、写作、审查、修改提示词。
- `templates/`：从示例文章抽象出的文章结构模板。
- `source/`：示例文章及模板抽取材料。
- `style_dna/wiki/`：政策研究文风控制规则。
- `imported_prompts/`：用户提供的对照提示词组。

## 配置

复制 `.env.example` 为 `.env`，填入本地密钥和 NotebookLM CLI 路径。

至少需要：

```bash
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
NOTEBOOKLM_CLI_PATH=notebooklm
```

## 运行主流程

```bash
python workflow/runner.py \
  --topic "美国AI人才战略布局及我国应对策略" \
  --target-country "美国" \
  --strategy-domain "AI人才" \
  --notebook-name "中美人才" \
  --china-response-focus "中国AI人才培养、储备、引进与战略应对" \
  --llm-provider deepseek \
  --max-iterations 2
```

运行后会在 `runs/<run-id>/` 下生成：

- `task_state.md`：临时任务列表和完成状态。
- `run_log.md`：归档运行日志。
- `retrieval_outputs/`：NotebookLM 检索材料。
- `judgment_outputs/`：任务重定义、材料角色、压力映射。
- `planning_outputs/`：文章构思。
- `suggestion_outputs/`：建议池和政策优先序。
- `review_reports/`：审查报告和示例对比报告。
- `final_article_reviewed.md`：最终 Markdown。
- `final_article_reviewed.docx`：最终 Word 文档。

## 验证

本地可先跑 dry-run 检查提示词拼装和流程连通性：

```bash
python workflow/runner.py \
  --topic "美国AI人才战略布局及我国应对策略" \
  --target-country "美国" \
  --strategy-domain "AI人才" \
  --notebook-name "中美人才" \
  --llm-provider deepseek \
  --dry-run \
  --max-iterations 1
```

Word 产物可用以下命令检查：

```bash
unzip -t runs/<run-id>/final_article_reviewed.docx
```
