# Environment、验证与运行（第 4–5 步）

路径固定，照用。

## 项目布局

- 工作流项目根：`/Users/hujingkai/Documents/New project/example1/strategic_response_workflow`
- 引擎入口：`workflow/runner.py`（运行前 cd 进 `workflow/`，否则 import 失败）
- 体例目录：`report_modules/<slug>/`；runs 落在 `strategic_response_workflow/runs/`
- 风格 DNA：`policy_style_dna/`（位于仓根 `example1/`，全局，新体例零配置自动套用）
- DeepSeek 已配置：`.env` 内有 key，`--llm-provider deepseek`

## 解析/确认范文文本（第 1 步）

```bash
# docx → markdown
pandoc "<范文.docx>" -t markdown -o /tmp/sample_src.md
# pdf：优先 pandoc 或 pdftotext；扫描件走 OCR
```

## dry-run 验证（第 4 步，必做）

```bash
cd "/Users/hujingkai/Documents/New project/example1/strategic_response_workflow/workflow"
python3 runner.py \
  --report-type <slug> \
  --topic "占位主题" --target-country "占位" \
  --strategy-domain "占位" --china-response-focus "占位" \
  --notebook-name "dry" --llm-provider deepseek --dry-run
```

验证点：
- 退出码 0；新 run 目录 `task_state.md` 全 `done`、无 `pending/running/error`（16 阶段）。
- `generated_prompts/` 下出现 `retrieval_<新检索类型>.md`（用的是蓝图的 key，不是旧体例的）。
- 验证完删占位 run 目录：`rm -rf runs/<那个 run-id>`。

## 实跑（第 5 步，可选；需资料包）

资料包契约：`runs/<materials-id>/retrieval_outputs/` 下放**正好**蓝图那几个 `<检索类型>.md`（可由 `topic-material-search` skill 产出）。

```bash
cd "/Users/hujingkai/Documents/New project/example1/strategic_response_workflow/workflow"
python3 runner.py \
  --report-type <slug> \
  --topic "<真实主题>" --target-country "…" \
  --strategy-domain "…" --china-response-focus "…" \
  --notebook-name "web-collected" --llm-provider deepseek \
  --reuse-materials-run <materials-id>
```

成稿在最新 `runs/run-*/final_article_reviewed.md`。

## 留存 / 删除（第 5 步收尾，必问）

本次体例默认是临时产物。最后问用户：
- **存为正式体例** → 留在 `report_modules/<slug>/`，可顺手提议用 `distill-reasoning-dna` 给它补判断刀。
- **删除** → `rm -rf report_modules/<slug>/`（实跑产生的 runs 目录视需要保留或清理）。

## 配套 skill

- 采料：`topic-material-search`（给主题生成检索方案→搜集→DS 审核→产出资料包）。
- 补刀：`distill-reasoning-dna`（为体例蒸馏 reasoning_dna 判断刀，再开 module.yaml 注入）。
