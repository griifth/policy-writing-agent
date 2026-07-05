---
name: distill-report-module
description: 体例合成器——喂入一篇或几篇同类范文，蒸馏出该文体的"推理链 + 分段结构 + 检索角度 + 归类与建议写法"，先产出一份可确认的"体例蓝图"，确认后自动生成一个完整的 report_modules/<新体例>/ 目录（module.yaml + 10 个 prompts + template + sample），让现有 strategic_response_workflow 引擎原样运行它。Use when 用户想从范文动态生成一个新写作体例/工作流、觉得固定体例太死板、想把一篇示例文章变成可复用的写作流水线、或要给 strategic_response_workflow 加新 report-type。触发词：生成体例、合成工作流、从范文造体例、新体例、把这篇变成工作流、distill report module。风格 DNA 全局自动套用；推理 DNA 默认先 gated 零注入，可后续用 distill-reasoning-dna 补刀。
---

# Distill Report Module（体例合成器）

把一篇/几篇同类范文，变成 strategic_response_workflow 可直接运行的一个新"体例"（report module）。

**核心认知**：引擎（`workflow/runner.py`）本身不死板——它是通用解释器，运行时按 `--report-type` 加载一个 `report_modules/<x>/` 目录就跑。死板的只是"体例靠手写"。本 skill 自动化"从范文造体例"这一步；**风格 DNA（`policy_style_dna/`，位于仓根）本来就是全局的，任何新体例自动套用**；推理 DNA（判断刀）默认先 gated 零注入，以后可用 `distill-reasoning-dna` skill 补。
> ⚠️ 自测规则：本说明书引用的 DNA 目录名必须与 runner 实际加载一致（现行为 `policy_style_dna/`；旧 `style_dna/` 已于 2026-07-05 归档至 `archive/style_dna_v1/`，勿再引用）。

## 三块拼图

| 拼图 | 谁负责 |
|---|---|
| 体例结构（推理链/分段/检索角度/归类与建议写法） | **本 skill 从范文蒸馏** |
| 文风（声音/句式/禁用/自检） | `policy_style_dna/`（仓根），全局，新体例零配置自动套用 |
| 判断刀（reasoning_dna） | 默认 gated 零注入；要强化时用 `distill-reasoning-dna` skill |

## 输入

- 必填：1 篇或几篇**同一文体**的范文（路径，支持 .md/.docx/.pdf/.txt）。多篇时取"共识结构"，差异处以蓝图标注。**最好喂同结构、不同主题的范文**——结构相同能取共识，主题各异能把"结构"与"主题"分离干净，体例更通用；主题也雷同则易夹带主题痕迹、做窄。
- 可选：体例名（ascii 短 slug，如 `comparative_review`；缺省由你按文体起）、体例中文 label。
- 可选（要顺带实跑时）：topic / target-country / strategy-domain / china-response-focus + 一份资料包（见 environment）。

## 工作流

按序执行。只在该步激活时读对应 reference。

1. **读范文、提结构（抽掉主题、只留架构）。** 抽取范文干净正文（docx/pdf 先转文本）。按 [references/blueprint-method.md](references/blueprint-method.md) 蒸馏，并**按"检索 / 构思 / 写作 / 审查"四阶段组织**（这就是引擎主轴）：总纲（文体定位 + 推理链）→ 检索阶段（检索类型）→ 构思阶段（归类方式 + 判断锻造 + 建议推导）→ 写作阶段（分段结构 + 建议写法）→ 审查阶段（体例红线）。多篇取共识。

2. **产出"体例蓝图"，交用户确认（强制 checkpoint）。** 把蓝图按模板输出给用户，**不要直接落盘**。用户可改推理链/检索类型/分段/体例名。用户确认或改定后才进入第 3 步。

3. **克隆最近体例为脚手架，按蓝图改写。** 选 `report_modules/` 中现有最接近的体例（experience_response / strategic_response / trend_review）`cp -R` 为 `report_modules/<新slug>/`，再按蓝图改写体裁相关文件、轻改其余文件标题。哪些必改、哪些轻改、module.yaml schema、占位符约定，见 [references/module-emit.md](references/module-emit.md)。reasoning_dna 注入默认留空（gated）。

4. **dry-run 验证。** 用 `runner.py --dry-run --report-type <新slug>` 跑通全流程（不调 LLM/NotebookLM），确认 16/16 阶段无 error、生成的 retrieval 提示词用的是新检索类型。命令见 [references/environment.md](references/environment.md)。验证后删掉这次 dry-run 占位 run 目录。

5. **（可选）实跑 + 询问留存。** 若用户给了 topic 与资料包，按 environment 的命令实跑出成稿。无论是否实跑，最后**问用户：把这个体例存为正式体例，还是删除**（默认本次为临时产物）。删除即 `rm -rf report_modules/<新slug>/`。

## 质量线（"做完"的标准）

- 蓝图经用户确认；体例名是合法 ascii slug。
- 生成的 `report_modules/<新slug>/` 含：`module.yaml` + `prompts/` 10 个 + `templates/article_template.md` + `source/sample.md`，文件名与 runner 约定完全一致（缺一个 runner 就 FileNotFoundError）。
- `--dry-run` 16/16 阶段无 error；retrieval 提示词使用蓝图里的新检索类型。
- 体裁相关文件（module.yaml/retrieval/task_redefinition/pressure_judgment_mapping/planning/writing/template/sample）确实按蓝图改写，而非残留旧体例内容。

## 反模式（本 skill 要避免）

- **改引擎。** 不要动 `runner.py`；新体例只是数据目录。要"临时"就生成后删，不要为 ephemeral 去改引擎。
- **跳过蓝图直接落盘。** 必须先给用户看蓝图、可改、确认。
- **凭空写体例结构。** 推理链/分段/归类必须从范文里读出来，证据不足的结构如实标注、问用户，不要套用旧体例硬凑。
- **过度承诺判断刀。** 默认 gated 零注入；不要假装新体例已有专属判断刀。要补刀走 `distill-reasoning-dna`。
- **残留旧体例痕迹。** 克隆脚手架后，体裁相关文件里"国际经验借鉴/战略竞争/趋势研判"等旧措辞必须改干净。
