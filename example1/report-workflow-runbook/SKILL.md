---
name: report-workflow-runbook
description: >-
  驱动本仓两套政策报告写作流水线的 agent-facing 操作手册。覆盖「国际比较章节流水线」（根引擎 workflow/runner.py）
  与「判断类三体例流水线」（strategic 引擎 strategic_response_workflow/workflow/runner.py，体例
  experience_response / strategic_response / trend_review）。给出选引擎、拼启动命令、三种材料源、
  中断续跑、产物定位、失败处置、dry-run 自检的可照抄步骤。
  触发词：跑报告工作流、驱动写作流水线、启动政策报告、续跑、换体例、复用料包、审稿 handoff、
  国际比较报告、战略应对报告、趋势研判、经验借鉴。
---

# 政策报告工作流 · Agent 操作手册（Runbook）

本手册给**驱动流水线的 agent** 照抄。所有命令/参数/路径已对源码核对，不要臆造。
仓库根：`/Users/hujingkai/Documents/New project/example1`（下称 `<ROOT>`）。

---

## 0. 两套引擎与工作目录

| 引擎 | 入口脚本（相对该引擎目录运行） | 引擎目录 | runs 落点 |
| --- | --- | --- | --- |
| 根引擎（国际比较章节流水线，23 步） | `python workflow/runner.py` | `<ROOT>` | `<ROOT>/runs/<run-id>/` |
| strategic 引擎（判断类三体例，16 步） | `python workflow/runner.py` | `<ROOT>/strategic_response_workflow` | `<ROOT>/strategic_response_workflow/runs/<run-id>/` |

两个入口脚本同名都叫 `workflow/runner.py`，**靠 cwd 区分**。根引擎从 `<ROOT>` 跑；strategic 引擎必须先进入
`<ROOT>/strategic_response_workflow` 再跑（避免用 `cd` 触发权限弹窗时，可用子 shell：
`(cd "<ROOT>/strategic_response_workflow" && python workflow/runner.py ...)`）。

---

## 1. 题目 → 用哪个引擎 / 哪个 report-type

| 题目形态 | 引擎 | `--report-type` |
| --- | --- | --- |
| 「XX国际比较」「多国政策比较」「分章节的比较报告」 | 根引擎 | 无（根引擎无此参数） |
| 「XX国际经验与启示」「借鉴XX经验」 | strategic | `experience_response` |
| 「XX战略布局及我国应对」「我国应对策略/风险预警」 | strategic | `strategic_response`（默认） |
| 「XX趋势研判」「机制综述」「态势综述」 | strategic | `trend_review` |

strategic 可用体例即 `strategic_response_workflow/report_modules/` 下目录名，已核对为
`experience_response`、`strategic_response`、`trend_review`。

---

## 2. 完整启动命令

### 2A. 根引擎（国际比较）

参数来源：`<ROOT>/workflow/runner.py` argparse（第 15–46 行）。

```bash
python workflow/runner.py \
  --topic "AI+教育" \
  --notebook-name "The Digital Promise AI Literacy Framework"
```

- `--topic`（**必填**）：报告主题。
- `--notebook-name`（**必填**）：NotebookLM 知识库名称。
- `--runs-dir`（可选，默认 `runs`）：产物根目录。
- `--dry-run`（可选）：只建目录/任务列表/提示词，不调 NotebookLM 与 DeepSeek。
- `--resume-run <run-id>`（可选）：从已有 `runs/<run-id>` 继续，跳过已完成任务。
- `--reuse-materials-run <run-id>`（可选）：复用指定 run 的 `retrieval_outputs`，跳过 NotebookLM。

### 2B. strategic 引擎（三体例）

参数来源：`<ROOT>/strategic_response_workflow/workflow/runner.py` argparse（第 1021–1077 行）。
在 `<ROOT>/strategic_response_workflow` 目录下跑。

```bash
python workflow/runner.py \
  --topic "美国AI人才战略布局及我国应对策略" \
  --target-country "美国" \
  --strategy-domain "AI人才" \
  --notebook-name "中美人才" \
  --report-type strategic_response \
  --china-response-focus "中国AI人才培养、储备、引进与战略应对" \
  --llm-provider deepseek \
  --max-iterations 2
```

首跑必填四项（缺任一会 `SystemExit`，见 runner.py 第 1093–1100 行）：
`--topic`、`--target-country`、`--strategy-domain`、`--notebook-name`。

- `--report-type`（可选，默认 `strategic_response`）：体例，取 `report_modules/` 目录名。
- `--china-response-focus`（可选，默认 `中国应对策略`）：中国侧落点聚焦。
- `--llm-provider`（可选，默认 `deepseek`，可选 `anthropic_compat`）：文本生成后端。
- `--max-iterations`（可选，默认 `2`，运行时按 `max(1, N)` 取值）：审改上限。
- `--reviewer`（可选，默认 `inline`，可选 `handoff`）：`inline`=同后端 LLM 自审；`handoff`=在审稿步暂停交外部 agent。
- `--review-scope`（可选，默认 `style_and_expression`，可选 `precedent_check` / `jiaokeyuan_final_review` / `reasoning_compliance`）：handoff 审稿范围；`jiaokeyuan_final_review`=教科院终审判分（按 quality_rubric 六维出评分 JSON），`reasoning_compliance`=推理对账（对照 judgment_outputs 降级记录）。
- `--style-subtype`（可选，默认 `auto`，可选 `a`/`b`）：policy_style_dna 子型路由，`auto` 按体例自动。
- `--dry-run`（可选）：不调 NotebookLM/LLM，写占位。
- `--reuse-materials-run <run-id>`（可选）：复用材料，跳过检索。
- `--resume <run-id>`（可选）：从暂停的审稿步续跑（handoff 用）。
- `--continue <run-id>`（可选）：从第一个产物不全的步骤接着跑。

注意：strategic 用的是 `--resume` 与 `--continue`；**根引擎用的是 `--resume-run`**，两者不通用。

---

## 3. 三种材料源怎么选与怎么传

### (a) NotebookLM（默认）
不传 `--reuse-materials-run` 即走此路。要求：`notebooklm` CLI 已安装并登录；strategic 传对 `--notebook-name`，
根引擎传 `--notebook-name`。strategic 首跑会先 `check_auth()`（runner.py 第 419 行），失败即报「NotebookLM 认证不可用」。

### (b) 复用已有 run 的料包
```bash
# strategic
python workflow/runner.py --topic "..." --target-country "..." --strategy-domain "..." \
  --notebook-name "占位" --reuse-materials-run run-20260625-210305-06e3ea92
# 根引擎
python workflow/runner.py --topic "..." --notebook-name "占位" \
  --reuse-materials-run <run-id>
```
传了 `--reuse-materials-run` 后 `retrieve_materials` 直接拷贝旧料，跳过 NotebookLM（strategic runner.py 第 442–443 行）。
`--notebook-name` 仍是必填占位，可随便填。

### (c) 网搜 skill 产出的料包
同样走 `--reuse-materials-run`：把网搜产物按料包契约写进某个 run 的 `retrieval_outputs/`，再用该 run-id 复用。

### 料包契约（必须遵守，否则下游判断步读不到）
- 目录：`<run-dir>/retrieval_outputs/`
- 文件名：`<retrieval_type>.md`，`<retrieval_type>` 由体例的 `module.yaml` 里 `retrieval_types` 决定
  （strategic 每个 type 一个文件，runner.py 第 446–453 行；根引擎见第 4 节的固定文件名）。
- 每份 md 二段式：`一、检索内容` + `二、相关文献`（dry-run 占位就是这个结构，runner.py 第 450 行）。

---

## 4. 产物在哪

### 根引擎 `runs/<run-id>/`
（任务与产物见 `<ROOT>/workflow/task_state.py` DEFAULT_TASKS，第 53–77 行，共 23 步）
- `task_state.md` / `run_log.md`
- `retrieval_outputs/`：如 `chapter1_top_design.md`、`chapter1_implementation.md`、`chapter1_topic_specific.md`、`chapter2_materials.md`
- `extracted_materials/`（含 `strategic_framing.md` 战略态势卡）、`generated_prompts/`
- `chapter_drafts/`：`chapter1.md`、`chapter2.md`、`chapter3.md`
- `review_reports/`：各章审查 + `final_review.md` + `fulltext_content_structure_review.md`
- 成稿：`final_report.md`（组装）、`final_report_reviewed.md`（全文修改后定稿）

### strategic 引擎 `runs/<run-id>/`
（步骤见 runner.py 第 29–44 行 TASKS 与第 128–142 行 pipeline_steps）
- `task_state.md` / `run_log.md`、`input.yaml`、`notebook_resolution.md`
- `generated_prompts/`、`retrieval_outputs/<type>.md`
- `judgment_outputs/`：`task_redefinition.md`、`material_roles.md`、`pressure_judgment_mapping.md`
- `planning_outputs/article_plan.md`、`suggestion_outputs/`（`suggestion_pool.md`、`policy_priority.md`）
- `drafts/current_article.md`、`review_reports/`（`review_iterN.md`、`template_match_review.md`）
- 成稿：`final_article.md`、`final_article_reviewed.md`、`final_article_reviewed.docx`

---

## 5. 中断与续跑：读 task_state.md 判进度

先 Read `<run-dir>/task_state.md` 判断跑到哪。两引擎表格结构不同：

- **根引擎** 9 列表：`| 序号 | 任务 ID | 模块 | 功能 | 执行者 | 状态 | 输入 | 输出 | 错误记录 |`，
  顶部有 `当前状态：`；状态取值 `pending/running/done/failed/skipped/blocked`（task_state.py 第 22 行）。
  底部 `## 错误详情` 段记录失败堆栈与「下一步建议」。
- **strategic** 4 列表：`| 任务 ID | 模块 | 功能 | 状态 |`（示例：
  `strategic_response_workflow/runs/run-20260625-210305-06e3ea92/task_state.md`）。

判读规则：
1. 找第一个非 `done` 的行 = 下一步。
2. 若有行为 `failed`/`blocked` = 卡住，先看根引擎 `## 错误详情` 或 strategic 的暂停提示，处置后再续跑。
3. 全 `done` = 已完成，去第 4 节取成稿。

续跑命令：
- 根引擎：`python workflow/runner.py --topic "<原题>" --notebook-name "<原库>" --resume-run <run-id>`
  （跳过已完成任务；resume 时会从 state 里载 notebook_id）。
- strategic 一般中断：`python workflow/runner.py --continue <run-id>`
  （从第一个产物不全的步骤接着跑，复用已产检索/判断/构思，不重查 NotebookLM；判据见 runner.py 第 144–160 行 `_step_done`）。
- strategic handoff 审稿续跑：首跑加 `--reviewer handoff`，会在 `review_draft` 步暂停并写出交接指令
  （runner.py 第 178–183 行），外部 agent 把审稿报告写到 `<run-dir>/review_reports/review_iterN.md` 后，
  执行 `python workflow/runner.py --resume <run-id>` 续跑。

---

## 6. 失败处置

| 现象 | 根因 | 动作 |
| --- | --- | --- |
| `NotebookLM 认证不可用` / `未找到 notebooklm CLI，请先安装并登录` | notebooklm CLI 未装或未登录 | 装并登录 CLI；或改用 `--reuse-materials-run` 走复用料包/网搜料包 |
| `NotebookLM CLI 调用超时` | 检索超时 | 重试；必要时调大 `NOTEBOOKLM_TIMEOUT_SECONDS`（须为正整数） |
| `未找到 notebook` / `精确匹配不唯一` / `模糊匹配不唯一` | `--notebook-name` 不对或重名 | 校正知识库名到唯一精确匹配 |
| `缺少 DEEPSEEK_API_KEY` | DeepSeek key 未配 | 在 `<引擎目录>/.env` 或进程环境设 `DEEPSEEK_API_KEY`（进程环境优先） |
| `缺少 ANTHROPIC_COMPAT_API_KEY` | 用了 `--llm-provider anthropic_compat` 但未配 key | 设 `ANTHROPIC_COMPAT_API_KEY`，或改回 `deepseek` |
| `pandoc` 报错 / export_docx 失败 | 未装 pandoc | `brew install pandoc`（strategic runner.py 第 700 行 `subprocess.run(["pandoc", ...], check=True)`）；急用可看 `final_article_reviewed.md` |
| handoff 一直停在审稿步 | 审稿报告未回填 | 把报告写到 `review_reports/review_iterN.md` 后再 `--resume <run-id>` |
| 中途报错想继续 | 某步失败 | 根引擎 `--resume-run`；strategic `--continue`；先读 task_state.md 定位失败步 |

---

## 7. dry-run 自检（先验通再真跑）

真跑前一定先 dry-run，验提示词拼装与流程连通，不烧 token / 不调外部服务。

```bash
# 根引擎
python workflow/runner.py --topic "AI+教育" --notebook-name "占位" --dry-run

# strategic
python workflow/runner.py --topic "美国AI人才战略布局及我国应对策略" \
  --target-country "美国" --strategy-domain "AI人才" --notebook-name "占位" \
  --report-type strategic_response --dry-run --max-iterations 1
```

dry-run 通过标准：run 目录生成、`task_state.md` 全 `done`、`generated_prompts/` 与 `retrieval_outputs/`（占位二段式）齐全、
无异常退出。通过后去掉 `--dry-run` 真跑。docx 可用 `unzip -t <run-dir>/final_article_reviewed.docx` 抽检。
