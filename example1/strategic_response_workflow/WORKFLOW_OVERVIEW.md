# 政策写作工作流总览：从知识库检索到最终审核

> 一句话：把写作拆成一串**可检查、可换件**的环，让模型在每一环只做一件想清楚的事。
> 事实来自 NotebookLM 知识库——模型只在检索到的材料上工作，不编造事实。

---

## 一、四层职责（贯穿全程）

| 层 | 管什么 | 载体 |
|---|---|---|
| **引擎** runner | 顺序、IO、循环、暂停/续跑、审稿者选择、导出、归档 | `workflow/runner.py` |
| **体例模块** | 检索口径、各步提示词、文章模板、示例稿、检索类型 | `report_modules/<体例>/` |
| **reasoning_dna** | 想到哪几层（判断纪律） | 现内嵌在模块判断提示词；规划中抽成 `reasoning_dna/` 可演化层 |
| **style_dna** | 怎么写（文字） | `style_dna/wiki/*` |

**横向**是数据流（事实→判断→构思→文字→审核），**纵向**是四层各管一段、各自可演化、互不绑死。

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
      │  [写作 + style_dna]
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
- **init**：按 `--report-type` 载入体例模块（`report_modules/<type>/module.yaml`），建运行目录，**快照** style_dna 到 `runs/<id>/style_dna_snapshot/`，写 `input.yaml`。
- **为什么**：体例即可插拔模块，引擎不含任何体例知识；快照保证“这次用的哪版 DNA”可追溯。

### 阶段 1 · 检索（从知识库取事实）　〔引擎 + 体例模块〕
- **resolve_notebook**：定位 NotebookLM 知识库（或 `--reuse-materials-run` 复用旧材料省检索）。
- **build_retrieval_prompts**：用模块 `prompts/retrieval.md`，按 `module.yaml` 声明的 `retrieval_types` 逐类拼装。
- **retrieve_materials**：逐类向知识库提问 → `retrieval_outputs/*.md`。
- **为什么**：事实与写作分离。检索口径由体例决定（战略问“压力/威胁”，借鉴问“做法/有效性”），事实落盘后续只在其上工作 → 可核验、不编造。

### 阶段 2 · 判断（把事实抬成判断）　〔体例模块 + reasoning_dna〕
只输出**可检查的中间产物**，不写正文、不吐思维链。
- **redefine_task** → `judgment_outputs/task_redefinition.md`：把“材料题”重定义成“判断题”。
- **assign_material_roles** → `judgment_outputs/material_roles.md`：每份材料“证明什么”，降级不能承重的材料。
- **map_pressure_judgment** → `judgment_outputs/pressure_judgment_mapping.md`：事实压力→判断 + 中国含义，标“不能推出的判断”。
- **为什么**：不让模型从材料一步跳到成文。先逼出可逐条审查的判断产物——这是 reasoning_dna 的着力点。

### 阶段 3 · 构思（判断→结构与建议）　〔体例模块 + reasoning_dna〕
- **plan_article** → `planning_outputs/article_plan.md`：核心判断→二级判断→材料互证→章节功能→推导链→标题结构。
- **build_suggestion_pool** → `suggestion_outputs/suggestion_pool.md`：先扩后筛，每条建议带对象/工具/机制/制度载体/牵头/风险。
- **prioritize_policy_options** → `suggestion_outputs/policy_priority.md`：排近/中/长期、定入稿序。
- **为什么**：把“怎么组织”显性化，防止滑成逐国/逐点平铺的综述；建议在成文前过对象/工具匹配审查，防悬空。

### 阶段 4 · 写作　〔体例模块 + style_dna〕
- **write_draft** → `drafts/current_article.md`：模块 `prompts/writing.md` + `templates/article_template.md` + **注入 style_dna(writing)** + 全部判断/构思产物 + 检索材料。
- **为什么**：文字层独立。同样的判断换 style_dna 就换文风；此时是“把已想清的写出来”，不是边想边写。

### 阶段 5 · 审查—修改循环（可迭代，带门槛）　〔引擎 + 模块 + style/reasoning〕
两种审稿者，**契约相同、可换件**：
- **inline**（默认/原行为）：同后端 LLM 自审，模块 `prompts/review.md` + style_dna(review)。
- **handoff**（`--reviewer handoff`）：跑到这**暂停**，写交接指令（`reviewers/instruction_template.md` 骨架 + **触发范围对应 DNA 的 `review_scope.md`** 决定“审什么”）+ `run_state.json`，退出；在场 agent 派**异源子 agent** 按该 DNA 审、写报告，再 `--resume` 续跑。
- **门槛 `_review_reaches_standard`**：正则扫报告——出现“未达到/硬伤/对象错配/必须重写”等判不达标 → **revise_article**（模块 `prompts/revision.md` + style_dna(revision)）改稿，回到审查；达标则定稿。
- **为什么**：① 异源审稿破“同模型把自己缺点当优点”的共享盲区；② 审稿“审什么”随 DNA 走——文风范围读 style_dna、推理对账范围读 reasoning_dna；③ 迭代门槛防“审查变形式确认”。

### 阶段 6 · 收尾　〔引擎 + style_dna〕
- **compare_with_sample** → `review_reports/template_match_review.md`：生成稿 vs 模块示例稿质量自评。
- **export_docx**：pandoc → `.docx`。
- **archive_log** → `run_log.md`：汇总产物，记体例与所用 DNA 快照。

---

## 四、跨阶段机制

- **审稿契约（reviewer 无关）**：暂停时落盘 `review_io/request_iter{n}.json`（机读）+ `INSTRUCTION_iter{n}.md`（自然语言交接）+ 输出格式契约（报告须含 `总体结论：达到|基本达到|未达到`，故引擎判定不变）。换审稿者只换触发方式，契约不变。
- **handoff 暂停/续跑**：`run_state.json` 记录配置 + 暂停轮次；`--resume <run-id>` 重建并续跑；多轮时每轮都在审稿点暂停。
- **指令由模板 + DNA 驱动**：交接指令不写死在代码里。骨架来自 `reviewers/instruction_template.md`，“审什么”来自触发范围对应 DNA 的 `review_scope.md`（`scope → DNA` 映射在 runner）。改模板或改 DNA，下次自动反映并快照到 `review_io/scope_iter{n}.md`。
- **可回归**：dry-run 字节回归门 + 运行快照；改任一层下次运行自动生效并留痕。

---

## 五、怎么扩展（引擎几乎不动）

| 想做的 | 做法 |
|---|---|
| 加一个新体例 | 在 `report_modules/` 加文件夹（module.yaml + retrieval/prompts/templates/source），`--report-type` 指定 |
| 改文风标准 | 改 `style_dna/wiki/*`、`style_dna/review_scope.md` |
| 改推理/审查标准 | 改 `reasoning_dna/review_scope.md`（刀建成后改 `reasoning_dna/wiki/*`） |
| 换审稿者 | 满足同一份审稿契约：handoff（在场 agent）/ 未来 cmd（`claude -p`、远程 agent）/ inline（同后端） |
| 改交接话术 | 改 `reviewers/instruction_template.md` |

---

## 六、关键路径速查

- 引擎：`workflow/runner.py`
- 体例模块：`report_modules/strategic_response/`、`report_modules/experience_response/`
- 文风层：`style_dna/wiki/`、`style_dna/review_scope.md`
- 推理层：`reasoning_dna/DESIGN.md`、`reasoning_dna/review_scope.md`
- 审稿模板：`reviewers/instruction_template.md`
- 运行产物：`runs/<run-id>/`（`judgment_outputs/`、`drafts/`、`review_reports/`、`review_io/`、`run_state.json`、`run_log.md`）
