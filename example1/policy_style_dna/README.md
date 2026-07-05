# policy_style_dna（文风 DNA · 单一真源）

两台引擎共用的**文风 DNA 唯一权威副本（SSOT）**。蒸馏自 38 篇人类成稿决策咨询报告（内参/简报体）。

> **落地契约（2026-07-05 起）**：本目录位于仓根 `example1/policy_style_dna/`，是全仓唯一副本——根引擎（`workflow/`）与战略引擎（`strategic_response_workflow/`）的 loader 都指向这里（各自代码中的 `REPO_ROOT` 常量）。**禁止再复制副本**；历史副本已归档至 `archive/policy_style_dna_workflow_copy/`（合并记录见 `wiki/forbidden.md` 第 2 节文末注与 `wiki/self_check.md` L5）。
> 它不是事实知识库；只控写作姿态、结构、句式与审查标准，**不得作为事实来源**——不得从中新增政策事实、年份、机构、项目或数据。

## 目录

- `wiki/`：文风规则本体（voice / structure / sentence / forbidden / recommendation / self_check / subtype_a / subtype_b），详见 `wiki/README.md`。
- `review_scope.md`：文风/表述审查范围（scope = style_and_expression），A（handoff 子 agent）与 B（inline 自审）两模式共用的单一尺子，**适用全部体例**。
- `prompts/distill_style_wiki.md`：蒸馏 prompt（指向语料清单，不内嵌全文）。
- `raw/source_manifest.csv`：语料清单（38 篇）。

## 接入现状（勿手抄清单，以代码为准）

两引擎均已接入，按"写作/审查/修改"模式选读 wiki 子集并自动追加子型文件（subtype_a/b）：

- 根引擎：`workflow/report_pipeline.py` 的 `_policy_style_dna_text()`（写作:399 / 审查:440 注入）。
- 战略引擎：`strategic_response_workflow/workflow/runner.py` 的 `_policy_style_dna_text()` 与 `_style_review_scope_text()`；每次运行把所用规则快照到 `runs/<run-id>/policy_style_dna_snapshot/`。

> 各模式具体读哪些文件，**以上述两个函数的 `mode_to_files` 为准**——README 不再手抄清单（手抄必漂移，这正是 2026-07 审计发现的 J1/J3 问题；本节即其修复）。

## 与旧 style_dna 的关系

旧 `style_dna/`（蒸自 24 篇学术期刊论文，第一人称"本研究"，与本目录第三人称规则相反）已于 2026-07-05 归档至 `archive/style_dna_v1/`，任何文档不得再引用它作语域锚。

## 维护

- 原始人类语料属敏感素材，不进仓库（仅留 `raw/source_manifest.csv` 清单）。
- 补语料或换体例后，用 `prompts/distill_style_wiki.md` 重跑蒸馏覆盖 `wiki/`；改动后须对锚点样例（`method_audit/samples/`）重跑打分，档位漂移 >1 档视为回归。
- 规则变更一律在 `wiki/self_check.md` L5 纠错记录留痕。
