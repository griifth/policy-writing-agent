# 政策写作工作流总览：从知识库检索到最终审核

> 一句话：把写作拆成一串**可检查、可换件**的环，让模型在每一环只做一件想清楚的事。
> 事实来自 NotebookLM 知识库——模型只在检索到的材料上工作，不编造事实。

---

## 一、五层职责（贯穿全程）

| 层 | 管什么 | 载体 |
|---|---|---|
| **引擎** runner | 顺序、IO、循环、暂停/续跑、审稿者选择、导出、归档 | `workflow/runner.py` |
| **体例模块** | 分析路径：检索口径、各步提示词、文章模板、示例稿、检索类型 | `report_modules/<体例>/` |
| **reasoning_dna** | 想到哪几层（判断纪律，"刀"） | 共享元格式 `reasoning_dna/conventions.md` + 各体例自带 `report_modules/<体例>/reasoning_dna/*.md`（gated 注入判断步） |
| **policy_style_dna** | 怎么写（文字） | 仓根 `../policy_style_dna/wiki/*`（SSOT，两引擎共读，2026-07-05 收敛） |
| **institution_profile** | 机构站位 + 对策落在什么域 + 怎么从国情+前文推对策 | 仓根 `../institution_profile.md`（跨体例共享、always-on，注入框问题/构思/建议/写作步） |

**横向**是数据流（事实→判断→构思→文字→审核），**纵向**是五层各管一段、各自可演化、互不绑死。
其中 reasoning_dna / policy_style_dna / institution_profile 三层都是**运行时加载、gated（无文件则零注入）、每次运行快照留痕**。

---

## 二、流水线全景（数据流）

```
知识库(NotebookLM)
      │  [检索]
      ▼
 retrieval_outputs/        ← 事实落盘，后续只在其上工作
      │  [判断]
      ▼
 judgment_outputs/         ← 重定义 / 材料角色 / 压力映射（可逐条审）
      │  [构思]
      ▼
 planning_outputs/ + suggestion_outputs/
      │  [写作 + policy_style_dna]
      ▼
 drafts/current_article    ──[审查×N]──► review_reports/   ◄─┐
      │                         │ 未达标                     │
      │                         └──[改稿 revise]─────────────┘
      ▼  达标定稿
 final_article_reviewed →  [对比示例 / 导出 docx / 归档]
```

每一环的产物都落盘、可读、可审、可回归。

---

## 三、阶段详解（按执行顺序）

### 阶段 0 · 路由与初始化　〔引擎〕
- **init**：按 `--report-type` 载入体例模块（`report_modules/<type>/module.yaml`），建运行目录，**快照** policy_style_dna / reasoning_dna / institution_profile 到 `runs/<id>/`（`policy_style_dna_snapshot/`、`reasoning_dna_snapshot/`、`institution_profile_snapshot.md`），写 `input.yaml`。
- **为什么**：体例即可插拔模块，引擎不含任何体例知识；快照保证“这次用的哪版 DNA”可追溯。

### 阶段 1 · 检索（从知识库取事实）　〔引擎 + 体例模块〕
- **resolve_notebook**：定位 NotebookLM 知识库（或 `--reuse-materials-run` 复用旧材料省检索）。
- **build_retrieval_prompts**：用模块 `prompts/retrieval.md`，按 `module.yaml` 声明的 `retrieval_types` 逐类拼装。
- **retrieve_materials**：逐类向知识库提问 → `retrieval_outputs/*.md`。
- **为什么**：事实与写作分离。检索口径由体例决定（战略问“压力/威胁”，借鉴问“做法/有效性”），事实落盘后续只在其上工作 → 可核验、不编造。

### 阶段 2 · 判断（把事实抬成判断）　〔体例模块 + reasoning_dna〕
只输出**可检查的中间产物**，不写正文、不吐思维链。
- **redefine_task** → `judgment_outputs/task_redefinition.md`：把“材料题”重定义成“判断题”（注入 institution_profile，按机构站位把真问题框到本机构落点域，如教育）。
- **assign_material_roles** → `judgment_outputs/material_roles.md`：每份材料“证明什么”，降级不能承重的材料。
- **map_pressure_judgment** → `judgment_outputs/pressure_judgment_mapping.md`：事实压力→判断 + 中国含义，标“不能推出的判断”。
- **为什么**：不让模型从材料一步跳到成文。先逼出可逐条审查的判断产物——这是 reasoning_dna 的着力点。

### 阶段 3 · 构思（判断→结构与建议）　〔体例模块 + reasoning_dna + institution_profile〕
- **plan_article** → `planning_outputs/article_plan.md`：核心判断→二级判断→材料互证→章节功能→推导链→标题结构。
- **build_suggestion_pool** → `suggestion_outputs/suggestion_pool.md`：先扩后筛，每条建议带对象/工具/机制/制度载体/牵头/风险。
- **prioritize_policy_options** → `suggestion_outputs/policy_priority.md`：排近/中/长期、定入稿序。
- **为什么**：把“怎么组织”显性化，防止滑成逐国/逐点平铺的综述；建议在成文前过对象/工具匹配审查，防悬空。

### 阶段 4 · 写作　〔体例模块 + policy_style_dna + institution_profile〕
- **write_draft** → `drafts/current_article.md`：模块 `prompts/writing.md` + `templates/article_template.md` + **注入 policy_style_dna(writing)** + **institution_profile（对策锁定落点域）** + 全部判断/构思产物 + 检索材料。
- **为什么**：文字层独立。同样的判断换 policy_style_dna 就换文风；此时是“把已想清的写出来”，不是边想边写。

### 阶段 5 · 审查—修改循环（可迭代，带门槛）　〔引擎 + 模块 + style/reasoning〕
两种审稿者，**契约相同、可换件**：
- **inline**（默认/原行为）：同后端 LLM 自审，模块 `prompts/review.md` + policy_style_dna(review)。
- **handoff**（`--reviewer handoff`）：跑到这**暂停**，写交接指令（`reviewers/instruction_template.md` 骨架 + **触发范围对应 DNA 的 `review_scope.md`** 决定“审什么”）+ `run_state.json`，退出；在场 agent 派**异源子 agent** 按该 DNA 审、写报告，再 `--resume` 续跑。
- **评分门 `_parse_review_verdict`**：解析审查报告末尾的 ```json 评分块（契约=`quality_rubric.md` 第五节，六维加权百分制）——`grade=="1"`，或 `total≥85` 且硬伤为空 → 达标定稿（任一硬伤 H1–H6 命中即 3 档，不看总分）；未达标 → **revise_article**（模块 `prompts/revision.md` + policy_style_dna(revision)）带审查报告改稿，回到审查；到 `--max-iterations` 上限仍未过门 → 停止返修、带病定稿，每轮 grade/total/硬伤与停机原因落盘 `review_gate_result.json`。报告无 JSON 或解析失败（如外部 handoff 老报告）→ 回退按「总体结论：达到/基本达到/未达到」行匹配，老交接路径不崩。
- **为什么**：① 异源审稿破“同模型把自己缺点当优点”的共享盲区；② 审稿“审什么”随 DNA 走——文风范围读 policy_style_dna、推理对账范围读 reasoning_dna；③ 迭代门槛防“审查变形式确认”。

### 阶段 6 · 收尾　〔引擎 + policy_style_dna〕
- **compare_with_sample** → `review_reports/template_match_review.md`：生成稿 vs 模块示例稿质量自评。
- **export_docx**：pandoc → `.docx`。
- **archive_log** → `run_log.md`：汇总产物，记体例与所用 DNA 快照。

---

## 四、跨阶段机制

- **审稿契约（reviewer 无关）**：暂停时落盘 `review_io/request_iter{n}.json`（机读）+ `INSTRUCTION_iter{n}.md`（自然语言交接）+ 输出格式契约（报告须含 `总体结论：达到|基本达到|未达到`，故引擎判定不变）。换审稿者只换触发方式，契约不变。
- **handoff 暂停/续跑**：`run_state.json` 记录配置 + 暂停轮次；`--resume <run-id>` 重建并续跑；多轮时每轮都在审稿点暂停。
- **指令由模板 + DNA 驱动**：交接指令不写死在代码里。骨架来自 `reviewers/instruction_template.md`，“审什么”来自触发范围对应 DNA 的 `review_scope.md`（`scope → DNA` 映射在 runner）。改模板或改 DNA，下次自动反映并快照到 `review_io/scope_iter{n}.md`。
- **reasoning_dna 注入（gated）**：各体例 `module.yaml` 的 `reasoning_dna_injection` 声明 step→刀映射，runner `_with_reasoning_dna` 把刀 + 共享 conventions 拼到对应判断步；无刀则零注入。当前三体例齐：strategic(intent/threat/hedge)、experience(cause/efficacy)、trend(signal/driver/stage/uncertainty)。
- **institution_profile 注入（gated、跨体例共享）**：`_with_institution_profile` 把 `institution_profile.md`（机构站位 + 落点域 + 五步桥接对策思路）注入 框问题/构思/建议/优先序/写作 五步；引擎层共享，三体例自动同吃一份，改一处全生效，新体例自动带上。
- **可回归**：dry-run 字节回归门 + 运行快照；改任一层下次运行自动生效并留痕。

---

## 五、怎么扩展（引擎几乎不动）

| 想做的 | 做法 |
|---|---|
| 加一个新体例 | 在 `report_modules/` 加文件夹（module.yaml + retrieval/prompts/templates/source），`--report-type` 指定；institution_profile 自动带上 |
| 改某体例的推理刀 | 改 `report_modules/<体例>/reasoning_dna/*.md` + module.yaml 的 `reasoning_dna_injection` 映射 |
| 改对策落点域 / 机构站位 | 改 `institution_profile.md`（三体例全生效；换机构只改这一处） |
| 改文风标准 | 改 `policy_style_dna/wiki/*`、`policy_style_dna/review_scope.md` |
| 改推理审查标准 | 改 `reasoning_dna/review_scope.md`、`reasoning_dna/conventions.md` |
| 换审稿者 | 满足同一份审稿契约：handoff（在场 agent）/ 未来 cmd（`claude -p`、远程 agent）/ inline（同后端） |
| 改交接话术 | 改 `reviewers/instruction_template.md` |

---

## 六、关键路径速查

- 引擎：`workflow/runner.py`
- 体例模块：`report_modules/{strategic_response,experience_response,trend_review}/`（各含 `reasoning_dna/` 刀）
- 推理层共享：`reasoning_dna/conventions.md`、`reasoning_dna/review_scope.md`、`reasoning_dna/DESIGN.md`
- 文风层：`policy_style_dna/wiki/`、`policy_style_dna/review_scope.md`
- 机构层：`institution_profile.md`、`institution_profile/CORPUS_RECOMMENDATION_LOGIC.md`（对策生成思路，从38篇蒸馏）
- 审稿：`reviewers/instruction_template.md`；三维 scope = style_and_expression / reasoning_compliance / precedent_check（`reviewers/precedent_check_scope.md`）
- 配套 skill：`.claude/skills/{distill-reasoning-dna, audit-extend-suggestions}/`
- 独立工具：`tools/suggestion_audit_extend.py`（建议核查—延展硬判定）
- 运行产物：`runs/<run-id>/`（`judgment_outputs/`、`drafts/`、`review_reports/`、`review_io/`、`suggestion_audit/`、`*_snapshot*`、`run_state.json`、`run_log.md`）

---

## 七、配套 skill / 工具（复用本套方法的固化件）

| 名称 | 类型 | 干什么 | 位置 | 进主链路？ |
|---|---|---|---|---|
| **distill-reasoning-dna** | skill | 为某体例蒸馏 reasoning_dna 判断"刀"：dev↔review 对抗循环，从金样本逆向抽取、写盘、接注入、过线（6 硬门 + 探针区分力） | `.claude/skills/distill-reasoning-dna/`（含 `scripts/distill_loop_template.js`） | 否（建库时用） |
| **audit-extend-suggestions** | skill + 工具 | 独立的建议"防重—补深—找空白"外部审计：抽取成稿建议→联网核查中国先例→下载政策原文→按缺口六分类延展→发散找真空白→**代码硬判定**舍弃/延展/保留/新增 | `.claude/skills/audit-extend-suggestions/` + `tools/suggestion_audit_extend.py` + `reviewers/precedent_check_scope.md` | **否**（独立增强，联网；不写回正文，主链路仍 KB-only） |

要点：
- 两者都**不进 runner 自动链路**——distill 在"建库"时用，audit-extend 在"成稿后"作外部审计用。
- audit-extend 的**硬判定是代码**（`tools/suggestion_audit_extend.py decide`）：决策表 + 来源分级（媒体不单独撑高置信）+ 延展须 gap_evidence + 发散 4 硬门 + 禁伪空白；联网事实只入 `runs/<id>/suggestion_audit/`、逐条带 URL，删改与并入正文**交人确认**。
