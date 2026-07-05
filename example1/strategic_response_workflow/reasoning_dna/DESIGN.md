# reasoning_dna + 体例模块化 设计方案（v0.2，待审核）

> ⚠️ 状态（2026-07-05）：v0.2 为历史设计稿，与磁盘不符处**以磁盘为准**。其中 benchmark_response 体例、共享刀 no_overreach.md、reasoning_dna/wiki/ 目录均未实现、已作废；现行刀在 `report_modules/<体例>/reasoning_dna/`（strategic_response / trend_review / experience_response），共享词汇在 `shared_schema/`（evidence_maturity / register_blacklist / strength_gate / layer_ownership）；文中 style_dna/ 已于 2026-07-05 合并提升为仓根 `policy_style_dna/`。
> 状态：草案，等待审核后再动任何源码。
> 适用工作流：`strategic_response_workflow/`
> 起草：2026-06-22（v0.1）｜修订：2026-06-23（v0.2，纳入 GPT + 用户审核意见）

## 版本变更（v0.1 → v0.2）

| # | 变更 | 来源 |
|---|---|---|
| 1 | 体例绑定范围更正：不止 4 个判断 prompt，`retrieval.md`、`article_template.md`、`policy_priority.md` 判据、`runner.py` docstring 也绑定战略体例 | 审核核实 |
| 2 | **撤回**"policy_priority 体例中立"的错误判断（结构中立、判据偏战略） | 审核核实 |
| 3 | 架构从"在原 prompt 上参数化 4 处门禁"改为**体例模块化**：runner 退成通用引擎 + 可载入体例模块 | GPT 审核 |
| 4 | **撤回**"默认体例=借鉴"。改为显式 `report_type`，默认保留 `strategic_response`（不破坏已验证路径），`auto` 后置 | GPT 审核 |
| 5 | 路由工程化：新增 `report_type_route.md` / `input.yaml` 记录 / `run_log` 记录加载了哪个模块 | GPT 审核 |
| 6 | **反模版红线放松**：从"必须至少一条降级"改为"必须完成降级扫描 + 留可审查取舍记录" | GPT 审核 |
| 7 | reasoning_dna 进入**写作/审查/修改闭环**，核对正文是否违反前期降级判断 | GPT 审核 |
| 8 | 新增**回归硬门**：搬迁与新功能分离，搬完先重跑旧主题对比 | 本次补充 |
| 9 | 新增**刀的区分力先验证**：探针测试早于建完整借鉴模块 | 本次补充 |
| 10 | 拆分**共享元格式/红线**（体例无关）与**刀的内容**（分模块） | 本次补充 |

---

## 0. 一句话

reasoning_dna 是一组**按体例可切换的"深度逼问清单"**，注入判断/构思阶段并被写作/审查阶段回查；它规定每一步"必须被砍到哪几刀、必须留下什么可审查的取舍记录"。它不管文字（style_dna），不管走哪几步、用什么模板（体例模块的流程 prompt 与 article_template）。它管：**想到哪几层、哪条判断必须留痕**。

本方案同时回答一个更大的问题：**不要继续把"战略竞争"写死在主流程里，而是把工作流拆成"通用引擎 + 可载入体例模块"。** reasoning_dna 是模块内的推理层。

---

## 1. 问题定位

### 1.1 经源码核实：战略体例绑定是**全流程**的，不是局部

| 环节 | 文件 | 绑定证据 |
|---|---|---|
| 入口定性 | `runner.py:1-4` | docstring "战略应对型政策文章工作流入口" |
| 检索 | `prompts/retrieval.md` | 6 个检索类型全是 strategy_background / strategic_intent_and_impact / china_status_and_gaps 等 |
| 任务重定义 | `task_redefinition.md` L41-42,L56 | Y 必须含冲突压力；必须体现战略压力 |
| 材料角色 | `material_roles.md` L26-33 | 角色库=战略诊断/现实短板 |
| 压力-判断 | `pressure_judgment_mapping.md` | 整步围绕"对华压力" |
| 论证链 | `planning.md` L65 | 措施→战略意图→对华压力→短板→应对 |
| 建议池 | `suggestion_pool.md` L29 | 不得照搬目标国家工具 |
| 优先序 | `policy_priority.md` 排序标准 1-2 | 核心压力/国家安全/关键技术/战略能力 |
| 文章模板 | `templates/article_template.md` | 通篇"战略布局及中国应对"，措施→战略支点→应对建议 |

**推论：** 在原 prompt 上"参数化几处门禁"会做出一个表面可切换、实际仍被旧战略模板牵引的混合系统。绑定既然是全流程的，正确解法是**按体例拆模块**。

### 1.2 不变的判断（v0.1 仍成立）

- "想"那半边没有可演化层：`_style_dna_text` 只喂写作/审查/修改/对比四步；判断步骤无 DNA 注入。
- 三层职责：流程 prompt 管"走哪几步"，reasoning_dna 管"想到哪几层"，style_dna 管"文字"。

---

## 2. 目标架构：通用引擎 + 可载入体例模块 + 共享文风层

```text
strategic_response_workflow/
├── workflow/
│   └── runner.py                  # 通用引擎：调度/文件传输/NotebookLM/LLM/日志/审查循环/导出docx
├── report_modules/
│   ├── strategic_response/        # 现有战略体例，整体迁入（行为不变）
│   │   ├── module.yaml            # 体例元信息 + 流程步骤 + 注入映射
│   │   ├── retrieval.md
│   │   ├── prompts/               # task_redefinition / material_roles / ... / policy_priority
│   │   ├── templates/article_template.md
│   │   └── reasoning_dna/         # 战略体例的刀：意图/威胁/对冲
│   └── benchmark_response/        # 新增：国际经验借鉴 / 单一政策分析 + 中国应对
│       ├── module.yaml
│       ├── retrieval.md
│       ├── prompts/
│       ├── templates/article_template.md
│       └── reasoning_dna/         # 借鉴体例的刀：成因/有效性/共性个性/归类/张力/迁移前提
├── reasoning_dna/                 # 【共享基底】刀的元格式 + 降级扫描红线（体例无关）
│   └── conventions.md
├── style_dna/                     # 共享文风层，不绑定体例
└── runs/
```

职责边界：
- `runner.py` 不含任何体例知识，只按 `report_type` 载入对应模块。
- 每个模块自带 检索/流程 prompt/模板/reasoning_dna。
- `reasoning_dna/conventions.md`（共享）定义"一把刀长什么样"+ 降级扫描红线；各模块 `reasoning_dna/` 只放**刀的内容**，不重写元格式（避免两套体例的反模版纪律漂移）。
- `style_dna/` 共享。

---

## 3. report_type 与路由（工程化，可复现）

### 3.1 取值（显式优先，auto 后置）

```bash
--report-type strategic_response   # 战略竞争分析 + 中国应对（现有，默认）
--report-type benchmark_response   # 国际经验借鉴/单一政策分析 + 中国应对（新增）
--report-type auto                 # 后续：由判别逼问路由
```

**默认 = `strategic_response`**：保留已验证行为，不破坏 DeepSeek/Opus 已跑通的路径。**不设"默认借鉴"**（v0.1 错误，已撤回）。

### 3.2 路由产物（每次运行固定留痕）

- `input.yaml` 记录本次 `report_type`。
- `judgment_outputs/report_type_route.md` 记录判定结果与理由（显式指定时记录"显式指定"）。
- `logs/run_log.md` 记录本次加载了哪个体例模块、哪些 reasoning_dna 文件。

auto 落地后，路由**判"主体例 + 是否叠加对抗子刀"**，不输出非此即彼，允许"AI教育国际比较"这类混合题以借鉴为主、叠一刀竞争含义。

---

## 4. 两个体例的核心推理链

| | strategic_response | benchmark_response |
|---|---|---|
| 适用 | 美国AI人才战略布局及应对；某国战略对我国影响及应对 | 国外校园餐经验及启示；学制改革经验及应对；体育教师培养及启示；超常儿童培养及建议 |
| 推理链 | 目标国家措施 → 战略意图 → 对中国压力 → 中国短板 → 应对策略 | 外部政策做法 → 成因条件 → 有效性证据 → 迁移前提 → 中国适配建议 |
| 检索口径 | 竞争/安全/技术封锁/人才争夺 | 做法/制度背景/实施效果/适配约束 |
| 模板 | 措施 → 战略支点 → 中国应对 | 做法分类 → 成因与有效性 → 适配判断 → 中国建议 |

---

## 5. reasoning_dna：刀（核心设计）

### 5.1 共享元格式（`reasoning_dna/conventions.md`，体例无关）

每把刀强制三段式：

```
## 必答问题      —— 这一刀的领域无关元问题
## 什么算答到了  —— 正例判据 + 反例（什么样是糊弄）
## 降级扫描要求  —— 必须做的扫描动作 + 取舍记录格式
```

### 5.2 借鉴体例 6 刀（`report_modules/benchmark_response/reasoning_dna/`）

| 刀 | 文件 | 必答元问题 | 防住的"想浅了" |
|---|---|---|---|
| 成因刀 | cause.md | 为什么各国在此走了不同路径？ | 只罗列差异不解释 |
| 共性/个性刀 | commonality.md | 哪些是普遍规律、哪些是特定国情产物？ | 默认一切皆可借鉴 |
| 归类刀 | typology.md | 能否把 N 国做法归成 2-3 种模式并判适用条件？ | 逐国平铺 |
| 有效性刀 | efficacy.md | 这个做法在母国真有效吗？证据什么状态？ | 把动向当经验 |
| 张力刀 | tension.md | 这领域真正的核心取舍是什么？ | 面面俱到没骨头 |
| 迁移前提刀 | transfer.md | 经验迁到中国，前提成不成立？ | 悬空建议 |
| （共享）no_overreach.md | | 哪些判断材料不足、不能写进正文？ | 过度拔高 |

### 5.3 战略体例的刀（`report_modules/strategic_response/reasoning_dna/`）

意图刀 / 威胁刀 / 对冲刀，承接现有"措施→意图→压力→短板→应对"链。

---

## 6. 反模版红线（v0.2 修订，唯一不可让步的精神不变，强度放松）

> **每一刀必须完成"降级扫描"，并留下可审查的取舍记录；不要求强行制造否定。**

- 原 v0.1："至少一条不可照搬 / 至少一个前提不成立" → **撤回**（会诱导模型为凑格式造问题）。
- v0.2：必须**做扫描**并给**结论**；结论可以是"存在 N 处需降级"，也可以是"无需降级，因为证据满足 X"。**可检查的产物是"扫描 + 结论 + 理由"，不是"一条否定"。**

各刀的扫描动作（举例）：
- 有效性刀 → 逐做法标证据等级（①政策意图②试点③有评估数据④媒体转述）；①④**应**降级为"动向"，若不降级须说明证据为何足够。
- 共性/个性刀 → 逐条做"可照搬性"扫描；判为"可照搬"的须给迁移前提。
- 迁移前提刀 → 每条启示挂前提并标"成立/不成立/需先补"；全部"成立"须给依据。

**审查判据：查"有没有发生过降级扫描并留下结论"，不查"有没有对应小节"，也不要求"必须有一条否定"。** 模版能造小节，造不出"我扫描后判 X 不降级、依据是 Y"这种可核对的取舍痕迹。

---

## 7. 注入与审查闭环（v0.2 补：进入写作/审查/修改）

### 7.1 判断阶段注入（镜像 `_style_dna_text`）

新增 `_reasoning_dna_text(step, module)`，结构照抄 `_style_dna_text`（runner.py:532）：`step→[files]`、逐个读、拼接、get 不中降级到纯 prompt。从**当前载入模块**的 `reasoning_dna/` + 共享 `conventions.md` 取文件。追加在 prompt 末尾固定锚点 `## 本步必答逼问（须留降级扫描记录）`，不替换现有字段槽。

step→刀 映射（benchmark 体例）：

| 步骤 | 注入 |
|---|---|
| material_roles | efficacy |
| pressure_judgment_mapping（借鉴态可改名 mechanism_judgment） | cause + tension + no_overreach |
| planning | commonality + typology |
| suggestion_pool | transfer |
| policy_priority | （借鉴态判据需重写，见 §2 模块自带） |

### 7.2 写作/审查/修改闭环（v0.2 新增）

写作、审查、修改阶段必须回读本次 `judgment_outputs/` 的降级记录 + reasoning_dna 检查项，审查正文是否：
- 违反了已做出的证据降级；
- 把"动向"写成"成熟经验"；
- 把"不可照搬"写成"直接借鉴"；
- 把"前提不成立"的建议写成立即推进；
- 超出 `no_overreach` 的证据边界。

### 7.3 快照

`_copy_style_dna_snapshot`（runner.py:515）旁并列加 reasoning_dna 快照 → `runs/<id>/reasoning_dna_snapshot/`，与已快照的 `judgment_outputs/`（"答"）构成审计对。

---

## 8. 实施顺序（含两道硬门）

### 第一步：体例模块化重构（**纯机械搬迁，零行为变化**）

把现有战略体例完整迁入 `report_modules/strategic_response/`，runner 退成通用引擎按 report_type 载入。

> **【回归硬门 ①】** 搬迁后用旧主题"中美AI人才"重跑一次，与已验证产物 `runs/run-20260621-161750-f4e75d5d`（Opus 版）对比：流程步骤、judgment_outputs 结构、最终文章结构一致，无退化。**不过门不准进第二步。** 不允许"搬迁 + 加新体例"同一步做。

### 第二步：新增 `report_type`（显式，不做 auto）

CLI/配置加 `--report-type`，三取值，默认 `strategic_response`。落地 §3.2 路由产物。

### 第三步：建 benchmark 体例模块

新增 `report_modules/benchmark_response/`：借鉴态 检索 / 任务重定义 / 材料角色 / 构思 / 建议池 / 优先序 prompt + 借鉴态 article_template（做法→成因有效性→适配→建议）。

### 第四步：接入 reasoning_dna（MVP 两刀）

先建 `cause.md` + `efficacy.md`（最具体、有可证伪量表、最不易塌成模版，命中甲方两大痛点）+ 共享 `conventions.md`。加 `_reasoning_dna_text`，接 material_roles(efficacy) 与 mechanism_judgment(cause)。

> **【验证门 ②】 刀的区分力先验证（早于铺满）：** 回归探针测试——4 篇闭环深稿喂进 cause/efficacy 探针 → 应判"已答"；浅综述 → 应判"糊弄/未做扫描"。**探针区分不开 = 红线机制是假的，停，回去加反例。** 此测试不需要整个模块，可在第三步并行先跑。

### 第五步：A/B + 审查闭环

拿"国外校园餐"开/关 reasoning_dna 各跑一遍，对比 judgment_outputs 是否出现证据降级、成因句而非现象罗列。接 §7.2 审查闭环。区分得开、A/B 有差，再铺其余 4 刀 + 战略体例的刀。

### 第六步（后置）：auto 路由 + 多体例评测

---

## 9. 蒸馏机制

抄 `style_dna/prompts/distill_style_wiki.md`，新建 `distill_reasoning_wiki.md`。喂**对照组**（4 篇闭环深稿 vs 多篇浅综述），任务="提炼深稿比浅综述**多做的推理动作**"。6 刀元问题**人工写成领域无关**，蒸馏只用来发现"多做了什么"，不交它定义刀本身（防过拟合到校园餐/学制等领域）。语料源 `style_dna/processed/cleaned_samples/`（24 篇）+ 指认的 4 篇深稿。

---

## 10. 风险与裁定

| # | 风险 | 缓解 |
|---|---|---|
| 1 | 6 刀退化成模版填空（最大杠杆） | §6 红线：降级扫描 + 取舍记录 + 反例划下限 + 审查查"有没有扫描留痕" |
| 2 | 搬迁重构破坏已验证战略路径 | §8 回归硬门①：纯机械搬迁 + 重跑对比，过门才继续 |
| 3 | 在没用的刀上建完整借鉴模块 | §8 验证门②：探针先验证区分力 |
| 4 | 强逼降级诱导模型造假 | §6：只要求扫描+结论，不要求强行否定 |
| 5 | 判断纪律传不到正文 | §7.2 写作/审查/修改回读降级记录 |
| 6 | 路由不可复现 | §3.2 三处留痕 |
| 7 | 两套体例反模版纪律漂移 | 共享 conventions.md，模块只放刀内容 |
| 8 | 模块化工程量被低估 | 显式分步 + 两道门 + 先 MVP 后铺满 |

---

## 11. 待你拍板的决策点

1. **整体走模块化重构**（runner 退成通用引擎 + report_modules/），认可吗？这是比 v0.1 大的工程，回归面更大，但更稳更可扩展。
2. **命名**：`reasoning_dna` 沿用，还是换名提示"它要求一次性体例模块化"？
3. **report_type 默认值**：确认默认 `strategic_response`（保留已验证行为）？
4. **MVP 范围**：先 2 刀（成因+有效性）接 benchmark 模块，认可吗？
5. **核心样本**：4 篇闭环深稿最终指认（候选：拔尖创新人才早期培养国际经验及启示 / 国外学制发展特点趋势及启示 / 美英德澳培养与聘任体育教师 / 主要国家将超常儿童培养上升为国家战略）。
6. **第一步起点**：是否同意"先纯机械搬迁现有战略体例 + 过回归门"，再碰任何新体例？
```
