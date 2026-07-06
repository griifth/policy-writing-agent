# 战略竞争分析与应对策略写作工作流

本目录是一套独立工作流，用于生成“目标国家战略分析 + 中国应对策略建议”类型政策文章。

工作流不是围绕单一主题写死的脚本。它接收主题、目标国家、战略领域和 NotebookLM 知识库名称，通过 NotebookLM 检索材料，再由 LLM 完成任务重定义、材料角色判断、压力映射、构思、写作、审查和修改。

## 边界

- 只在本目录内读写工作流文件和运行产物。
- NotebookLM 只用于检索指定知识库材料，不修改 NotebookLM skill 或知识库。
- `.env` 只放在本目录，且不提交到 Git。
- `runs/` 为本地运行记录目录，不进入 Git。
- 文风 DNA 已收敛为**仓根** `example1/policy_style_dna/`（SSOT，两引擎共读，2026-07-05 起）；原始人类语料不进 Git（目录内只留 `raw/source_manifest.csv` 清单）。旧 `style_dna/` 已归档至 `example1/archive/style_dna_v1/`。

## 目录

- `workflow/runner.py`：主工作流入口（含评分门循环 `_review_revise_loop` / `_parse_review_verdict`）。
- `workflow/policy_n_prompt_runner.py`：用户提供“政策N”提示词组的对照运行入口。
- `workflow/deepseek_client.py`：DeepSeek 调用封装，只返回最终答案。
- `workflow/llm_client.py`：LLM 后端选择器，支持 DeepSeek 和 Anthropic-compatible 接口。
- `workflow/notebooklm_client.py`：NotebookLM CLI 调用封装。
- `report_modules/<体例>/`：可插拔体例（module.yaml + 10 prompts + 模板 + 示例 + reasoning_dna 刀）。
- `shared_schema/`：跨刀共享词汇真源（证据成熟度 E0–E4 / 军事化词表 / 强度双钥门 / 层归属，2026-07-05 建）。
- `reasoning_dna/`：刀的共享元格式（conventions）与推理审查尺子。
- `audience_profiles/`：读者站位三档（national_leader / moe_leadership / bureau，`--audience-level` 选用）。
- `quality_rubric.md`：**唯一评分真源**（六维加权 + 硬伤集 + 1/2/3 分档 + 盲测锚点）。
- `reviewers/`：审稿尺子（instruction_template + 文风外的四个 scope：先例核查 / 教科院终审 / 推理对账 / 站位互校验）。
- `tools/score_article.py`：单篇终审打分工具（终审人格 + rubric，出报告与评分 JSON）。
- `gold_samples/`：金样本与评委校准集（judge_set）。
- `prompts/`、`templates/`、`source/`、`imported_prompts/`：早期单体例时代的提示词/模板/示例与对照组（现行体例资产以 `report_modules/` 为准）。
- `../policy_style_dna/wiki/`（仓根）：政策研究文风控制规则（本引擎经 `REPO_ROOT` 读取）。
- `../institution_profile.md`（仓根）：机构站位与建议落点（两引擎共读）。

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

常用可选参数：`--report-type`（三体例）、`--audience-level`（读者站位三档，不选零注入）、`--reviewer handoff --review-scope <尺子>`（外部审稿，五个 scope 含教科院终审 `jiaokeyuan_final_review`）、`--style-subtype`、`--max-iterations`（评分门返修上限）。完整说明见 `../report-workflow-runbook/SKILL.md`。

**审改评分门（2026-07-05 起）**：审查报告末尾带六维评分 JSON（标尺 `quality_rubric.md`）；`grade=1` 或总分 ≥85 且零硬伤才定稿，否则带审查意见自动返修再评，到 `--max-iterations` 上限带病定稿。全程留痕 `review_gate_result.json`。外部老式报告（只有"总体结论"行）自动回退兼容。

运行后会在 `runs/<run-id>/` 下生成：

- `task_state.md`：临时任务列表和完成状态。
- `run_log.md`：归档运行日志；`input.yaml`：本次输入（含 audience_level）。
- `*_snapshot*`：本次所用规则快照（文风 wiki+评分标尺 / 刀+conventions+shared_schema / 机构 / 读者站位）。
- `retrieval_outputs/`：NotebookLM 检索材料。
- `judgment_outputs/`：任务重定义、材料角色、压力映射。
- `planning_outputs/`：文章构思。
- `suggestion_outputs/`：建议池和政策优先序。
- `review_reports/`：审查报告（末尾含评分 JSON）和示例对比报告。
- `review_gate_result.json`：评分门留痕（每轮 grade/total/硬伤、停机原因）。
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
