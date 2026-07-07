# 文风/推理 DNA 蒸馏方法 · 评估与改进

> **问题**：我们当前提炼文风 DNA 与推理 DNA 的**方法**是否有待改进？应如何改进？
> **方法**：派 9 个 agent 审计——5 个盘点三套蒸馏方法现状 + 5 篇展示样例 + Kimi 语料；4 个批判方法缺陷并给改进，且把每个方法缺陷**连回**此前已发现的 DNA 问题（pid 见《待解决问题清单_移交设计.md》）。共产出 **29 条方法缺陷 + 29 条改进**。
> **一句话结论**：**有，且待改进的空间很大。** 我们此前挖出的近 30 个 DNA 问题（双份漂移、证据分级①级相反、语域黑名单三抄、DESIGN 脱节、错锚…）几乎**全部是"蒸馏方法"的结构性缺陷在下游的投影**——现在的方法"只教怎么造 DNA，不管产物落哪、不先定共享词汇、用复制代替引用、验收只到能跑"。把方法补上"共享 schema 前置 + 单一真源 + 引用而非复制 + 对账 + 盲测合入 + 金样本准入"这套闭环，能一次性根治其中大半。

---

## 目录
1. [现状：我们现在怎么造 DNA](#一现状我们现在怎么造-dna)
2. [核心诊断：方法的 7 个系统性根缺陷](#二核心诊断方法的-7-个系统性根缺陷)
3. [分方法的缺陷与改进](#三分方法的缺陷与改进)
4. [改进路线图（P0/P1/P2）](#四改进路线图p0p1p2)
5. [展示样例盘点（5 篇 A–E）](#五展示样例盘点5-篇-ae)
6. [Kimi OCR 语料盘点（38 篇）](#六kimi-ocr-语料盘点38-篇)
7. [附：改进后的"统一蒸馏闭环"示意](#七附改进后的统一蒸馏闭环示意)

---

## 一、现状：我们现在怎么造 DNA

我们其实有**三套并行的蒸馏方法 + 一个元蒸馏引擎**，彼此独立、各写各的：

| 方法 | 干什么 | 关键文件 | 产物 |
|---|---|---|---|
| **文风蒸馏** | 从人类成稿逐篇抽"声音/结构/句式/禁区" | `policy_style_dna/prompts/distill_style_wiki.md`（现行）；`style_dna/prompts/…`（旧版） | `policy_style_dna/wiki/` 9 个 md |
| **推理蒸馏** | 从金样本 dev↔review 对抗循环逆抽"判断刀" | `distill-reasoning-dna` skill；`reasoning_dna/DESIGN.md` + `conventions.md` | 每体例 `reasoning_dna/*.md`（2–4 把刀） |
| **体例蒸馏** | 从范文造一个可运行的 `report_modules/<体例>/` | `distill-report-module/`（SKILL + blueprint/environment/module-emit） | module.yaml + 10 prompts + template + sample |
| （范文书蒸馏） | 从政策分析"书"抽思维框架 | `policy-book-distillation/` | 思维框架 md（如 bardach-eightfold-path） |
| （元引擎） | 造"人物 skill" | `huashu-nuwa`（女娲造人） | 人物思维 skill |

**两条重要现状事实**（后面诊断都挂在这上面）：
1. **文风已换过一代**：旧 `style_dna/` 蒸自 **24 篇学术期刊论文**（第一人称"本研究"），现行 `policy_style_dna/` 蒸自 **38 篇决策咨询内参**（第三人称零自称）。旧目录运行期已无 `.py` 引用，但**方法文档与推理层仍锚在旧目录**（见 X-D1）。
2. **蒸馏成熟度各体例天差地别**：`trend_review` 已有 `source/gold_samples/`（`foil__`负样本 + `policy_landing__`/`trend_body__`正样本 + manifest）的完整策展；而 `strategic_response`/`experience_response` **只有单篇 `source/sample.md`**。这套"策展"从没被逆向写回方法，是一次性手工产物。

---

## 二、核心诊断：方法的 7 个系统性根缺陷

> 4 个批判 agent 强烈收敛到同一组根因。下游那近 30 个问题，本质是这 7 个方法缺陷的投影。

| # | 方法根缺陷 | 一句话 | 下游被它制造的问题(pid) |
|---|---|---|---|
| **R1** | **只定义"产物长什么样"，不定义"产物落哪、只能有一份"** | 方法把"造"和"住"当两回事，只管造、不管住；落地就被复制成两份/四份并各自漂移 | STY-1, G1, G2, G3, G4 |
| **R2** | **没有"先定共享词汇表(schema-first)再蒸任何单元"的 phase-0** | 证据分级/语域黑名单/对策纪律这些跨刀跨层共享的词表，被"每蒸一个单元顺手各定义一遍" | RSN-1(①级相反), RSN-2(黑名单三抄), E3, STY-2(判断:证据6抄) |
| **R3** | **落盘一律"物理复制/cp -R 克隆"，无"引用/include"原语** | self_check 被设计成手工汇总、造体例 cp -R 整目录"轻改标题"，重复是方法的默认输出 | STY-4, STY-3, RSN-3(cause/driver近重复), D8(步骤键复用) |
| **R4** | **文风↔推理边界靠散文提醒，无"每类规则唯一归属层 + 跨层只准引用"的护栏** | 蒸文风时把判断强度/证据/对策纪律当"味道"一起收了；推理元格式又反把语域规则内联、还锚到文风旧副本 | X-D1(错锚), E4/F(对策纪律跨层重写), RSN-2 |
| **R5** | **没有"设计↔实现↔文档"三方对账步骤** | DESIGN.md 是永不回写的一次性草案；改名/缩刀/迁移都不回写 | RSN-5(DESIGN脱节), D7(悬空引用), J1(README漂移), RSN-4(scope未接线) |
| **R6** | **验收只到"能跑/单刀过线"，无跨刀一致性门、无"改DNA→盲测→过线才合入"闭环，且评委即选手** | 六条硬门全是单刀自洽检查，任何跨刀矛盾在每次单刀评审里都"通过"；盲测/打分器停在 tmp 脚本 | RSN-1, RSN-2, RSN-3 一路过线；M-S11/S12 资产未接线 |
| **R7** | **金样本策展非标配、不分 provenance(人写/AI)** | 方法在"输入质量"这最关键处最松：单篇 sample 就能定体例、不问人写还是 AI 写 | I2(主题污染), 成熟度不均, "学到AI腔"劣化闭环 |
| （R8） | **方法层错引用**（R4/R5 的具体一例，单列因影响大） | `distill-report-module/SKILL.md` 仍称"文风DNA=`style_dna/`（全局自动套用）"——指废弃旧目录；照此造的新体例、照 `conventions.md:27` 设的语域锚都会锚错 | X-D1 |

**为什么这套方法会长成这样**：三套蒸馏的**心智模型都停在"单元级"**——造出一个 wiki / 一把刀 / 一个体例目录就算完，没有"维护一个有单一归属、彼此对账、盲测验证过的规则库"的系统观。于是每蒸一次就多一份靠人肉同步的副本，必然漂移。

---

## 三、分方法的缺陷与改进

> 每条：缺陷 → 根因 → 连回问题；改进 → 怎么改 → 解决什么 → 工作量。证据 file:line 来自 agent 核对。

### 3.1 文风 DNA 蒸馏方法

**缺陷**
- **F-W1（high）产物无家**：`distill_style_wiki.md:24-30` 的"输出"章只规定生成 6 个 wiki 的内容，没有一条说"这套 wiki 唯一权威副本住哪、别的引擎只准引用不准复制"。→ 复制成两份、`forbidden.md`/`review_scope.md` 已漂移。连回 **STY-1/G1-4**。
- **F-W2（high）self_check 被当独立产物手写**：`prompts:30` 把 self_check.md 列为"第 6 个要写的文件"，要求人工把 voice/structure/forbidden 汇编成 L1–L5。→ 手写汇编必与源不同步（`self_check.md:11`≈`voice.md:16`、`:19`≈`forbidden.md:14`）。连回 **STY-4/STY-2**。
- **F-W3（high）规则无 ID、每文件求"自足可读"→ 自足=复制**：无"一条规则只定义一次、他处用 ID 引用"的机制。→"判断∶证据1∶N"在 6 文件各写、各封"头号"命名不一。连回 **STY-2/C4**。
- **F-W4（high）蒸文风时把推理内容当"味道"收了**：`prompts:17-23` 的"体例分水岭"把判断分层、镜像推导建议·四要素·实施机制、升格兜底双声部当文风特征抽进 voice/recommendation/subtype_a。连回 **RSN-1/RSN-2、"必须/立即"两把闸门打架**。
- **F-W5（medium）subtype 是蒸馏发现的知识却没蒸成数据**：`self_check.md:32` L5 记录 06-25 才拆出 A/B 子型，但只写进文本、没产出"report_type→subtype"映射，只能硬编码进 `runner.py:802-806`。连回 **STY-5/D8**。
- **F-W6（low）把八股套路当核心 DNA 固化**：`prompts:19-22` 把"加粗领起/镜像三段/四字动宾"当必抽骨架，与会议 S7"软性优先、不硬套政策腔"有张力。连回 **STY-2**。

**改进**
- **F-I1（中）** 蒸馏 prompt 加"落地契约"：文风 DNA 只有一个 SSOT 目录，引擎只准引用/软链、禁复制；先把两份合并成一份、另一份改软链；CI 加"出现第二份且 diff 非空即报错"。→ 解决 **STY-1/G1-4**。
- **F-I2（中）** self_check 改为**脚本从源规则生成**：给 voice/structure/forbidden 每条规则打稳定 ID，`build_self_check.py` 自动拼 L1–L5，文件头标"勿手改"；输出清单删掉 `=== self_check.md ===`。→ **STY-4/STY-2**。
- **F-I3（中）** 引入**规则 ID + 单点定义 + 引用**：一条规则只在 canonical 文件定义一次带 ID，他处写"见 VOICE-JUDGE-EVIDENCE-1N"；去掉各自"头号"别名；加 dup-linter 检测跨文件近重复。→ **STY-2/C4/STY-4**。
- **F-I4（大）** 蒸馏前**先画文风/推理边界**（"不蒸什么"一节）：判断强度、证据分级、建议可行性、对策↔靶子挂钩、"必须/立即"开关——一律不进 voice/recommendation，改引用推理刀。→ **RSN-1/RSN-2/STY-2**。
- **F-I5（小）** subtype 路由**蒸成数据**：`module.yaml` 加 `style_subtype: a|b`，runner 只读不判、删 `802-806` 字典。→ **STY-5/D8**。
- **F-I6（小）** 把"**观点鲜明·逻辑清晰·精炼准确**为最高准则、对仗/镜像/动宾仅自然贴合时用、不得为形害意"升为蒸馏总纲。→ 回应会议 S7。

### 3.2 推理 DNA（判断刀）蒸馏方法

**缺陷**
- **R-W1（high）无"先定共享证据分级、各刀再引用"的前置步**：每把刀在自己的《降级扫描》里各造一套量表。→ `efficacy.md:11` ①=最弱、`signal.md:33`/`threat.md:28` ①=最强、`intent.md:33` 改用 A/B/C/D，同一"①"语义相反。连回 **RSN-1**。
- **R-W2（high）逐刀独立产出、无"共享层抽取"**：`conventions.md:24-30` 已放语域红线，但硬门只查"本刀三段式完整"，反而激励每刀把黑名单塞满自己（threat/intent/hedge 各抄、词表 9/6/5 不一）。连回 **RSN-2**。
- **R-W3（high）无跨体例去重环节**：SKILL 只叫"看已有刀学结构再各写"，作用域被锁死单体例。→ `cause`(experience) 与 `driver`(trend) 逐字近重复，`driver.md:5` 靠一句手写"同名同源"免责。连回 **RSN-3**。
- **R-W4（high）无"设计↔实现对账"**：`DESIGN.md` 规划 benchmark_response+6刀+`no_overreach.md`，磁盘是另一套且这些全不存在；`review_scope.md:13` 悬空引用不存在的 `reasoning_dna/wiki/`。连回 **RSN-5/D7**。
- **R-W5（high）过线标尺="同源 general-purpose agent 打分≥85"，评委即选手、无跨刀门**：reviewer 与 dev 同 agentType，六硬门全是单刀自洽，无一条查"证据级方向是否跨刀一致/是否与别刀重复/黑名单是否该让位 conventions"。连回 **RSN-1/2/3/5**。
- **R-W6（medium）步骤键沿用战略语义**：SKILL 强制 step 从固定清单选，含 `map_pressure_judgment`，被 experience/trend 复用（`module.yaml`）。连回 **D8**。
- **R-W7（medium）金样本/foil 策展可选非标配**：trend_review 有完整策展、其他只有单篇 → 单篇易过拟合到该篇主题(AI人才/校园餐)与 AI 腔。连回 **RSN-5/RSN-3**。

**改进**
- **R-I1（中）** conventions 增《统一证据分级(体例无关)》，用**带方向的具名量表**（如 E-INTENT<E-BUILT<E-OPERATIONAL<E-EVALUATED，弃裸序号①②③④），dev 写刀前必读、只准引用；review 加"证据级引用一致性"硬门；efficacy/signal/intent 回改。→ **RSN-1**。
- **R-I2（中）** conventions 建**共享规则块**（REGISTER-BLACKLIST / ATTRIBUTION-SCALE），各刀"见 conventions#…"引用；SKILL 加"共享层抽取"步 + "无重抄"硬门。→ **RSN-2**。
- **R-I3（大）** 造刀前先建**判断刀语义地图**，重合者抽为**共享刀 + 薄适配层**（`reasoning_dna/shared/attribution.md`，cause/driver 各留 5–10 行侧重）；放宽 BOUNDARY 允许跨体例盘点、设"编排者"抽共享刀。→ **RSN-3/STY-1**。
- **R-I4（中）** 收敛加**设计↔磁盘对账门**：比对 DESIGN 承诺 vs 磁盘 vs 路径引用是否真实存在，作废项须标注；DESIGN 头部状态更新或归档。→ **RSN-5/D7**。
- **R-I5（中）** 对抗循环加**跨刀一致性硬门 + 异构评委**：第 7 条硬门由"视野横跨全部刀的总审"跑；reviewer 换不同模型/人设；探针加"人写 vs AI 稿"对照（judge_set 已有 human.md/old_gen.md）判"是否在奖励 AI 腔"。→ **RSN-1/2/3/5**。
- **R-I6（中）** 每体例在 `module.yaml` 声明**语义化判断步**（experience 用 mechanism_judgment、trend 用 trend_synthesis），runner 从模块读、不用全局单表。→ **D8**。
- **R-I7（中）** 把 trend_review 的 **gold/foil 策展定为所有体例标配前提**（≥3 篇跨主题正样本 + ≥1 foil、人写优先），strategic/experience 补齐后重蒸。→ **RSN-3/RSN-5**。

### 3.3 体例蒸馏方法 + 样本/语料策展

**缺陷**
- **M-W1（high）方法文档把文风 DNA 锚到废弃 `style_dna/`**：`distill-report-module/SKILL.md:3/10/17` + `blueprint-method.md:26` 三处称"style_dna 全局自动套用"，与运行时只读 `policy_style_dna/` 相反、且两份 voice.md 人称规则相反。→ 每个照此造的新体例都锚错。连回 **X-D1/STY-1**。
- **M-W2（high）"抽掉主题只留架构"只是口号、无主题分离验收**：`blueprint-method.md:3-10` 反复强调抽主题，但输出侧无闸；实测 strategic_response 的 `writing.md:88`/`review.md`/`revision.md` 把"美国AI人才/H-1B式举例"焊进通用 prompt。连回 **I2/D8**。
- **M-W3（high）检索 schema 双轨、通用 schema 键名不匹配任何体例**：`search-plan-method.md:9-17` 的 generic 6-category（background/key_practices…）不等于任何真实体例的 retrieval_types；`review-standard.md:17` 还把 experience 的键写死为必查 → strategic/trend 料包文件名与审核对不上、缺文件让 runner 抛 FileNotFoundError。连回 **I1**。
- **M-W4（high）无"只从人写金样本蒸馏、AI 稿只作 foil"的纪律**：蒸馏对样本人写/AI 写完全无感（`extraction-schema.md` 无 author 栏）。→ 拿 AI 稿当范文会把 AI 腔当"结构"学进去（会议盲测证 A/B/D 劣于 C/E）。连回 **STY-4/RSN-1**。
- **M-W5（high）三套蒸馏缺统一"→单一真源→对账→盲测"闭环**：质量线只有"dry-run 16/16 无 error"这种存在性校验。连回 **STY-1/2/4、RSN-1/2/5**。
- **M-W6（medium）落盘是 `cp -R` 克隆再"轻改标题"**：`module-emit.md:12-16` cp -R 最近体例、`:32-36` 多文件标"轻改"→ 用复制代替共享，是各写一遍/近重复的落盘侧源头。连回 **RSN-2/RSN-3/D8**。
- **M-W7（medium）策展纪律没写进方法**：grep "gold/foil/金样本/盲测/SSOT" 在三个 skill 目录全空；成熟的策展只作为 trend_review 一次性产物存在。连回 **RSN-3**。

**改进**
- **M-I1（小）** 把方法文档目录指针改"从引擎读出"：`SKILL.md:10/17` 的 `style_dna/`→`policy_style_dna/`，加"说明书引用目录必须与 runner 实际加载一致"自测；同步修 `conventions.md:27` 语域锚（**改锚后再归档旧目录，勿先删**）。→ **X-D1/STY-1**。
- **M-I2（中）** 加**主题外提验收硬门**：落盘前扫 prompts/module.yaml 的专有名词（国名/领域/机构/H-1B式举例），一律替占位符或移入 sample；清掉 strategic 现存"美国AI人才"词表。→ **I2**。
- **M-I3（中）** 建 **retrieval_types 单一登记表**，造体例与备料两 skill 都引用它；`topic-material-search` 去掉通用默认 schema（缺 report-type 就报错）；`review-standard.md:17` 改为从目标体例 module.yaml 动态读必查类别。→ **I1**。
- **M-I4（中）** 把 trend_review 策展逆向写成 **`curation-standard.md`**：每体例 source/ 必备人写金样本≥N（角色前缀标注）+ foil≥1 + manifest；质量线加"source/ 达策展标准"。→ **RSN-3**。
- **M-I5（小）** 立**样本来源分级纪律**：extraction-schema/blueprint 加必填 `author=人写/AI写`；DNA 只从人写金样本蒸馏，AI 稿只作 foil。→ **STY-4/RSN-1**。
- **M-I6（大）** 三套蒸馏统一 **"→单一真源→对账→盲测验证"** 收尾：①每条规则指定唯一属主、他处引用；②落盘后跑跨文件对账（同概念多定义/冲突清零）；③以人写金样本为 gold 基准盲测过线才算完成。→ **STY-1/2/4、RSN-1/2/5**。
- **M-I7（大）** 落盘从 cp -R 改**脚手架引用共享层**：通用件（角色标签、语域黑名单、对策纪律、通用步骤键、cause/driver 共同判据）抽到 `report_modules/_shared/`，体例引用而非复制；非战略体例步骤键改名。→ **RSN-2/RSN-3/D8**。

---

## 四、改进路线图（P0/P1/P2）

> 系统性 completeness critic 的排序，已与上面分方法改进合并去重。

### 🔴 P0（先做，一次消除最多下游问题）
1. **共享词汇表 schema（phase-0）**：新建 `shared_schema/{evidence_grades,register_blacklist,policy_discipline,layer_ownership}.md`，作为蒸任何单元的前置；三套 SKILL 改为"先读、只引用、禁内联重定义"。→ 一次消除 **RSN-1、RSN-2、E3、STY-2**。
2. **SSOT 契约 + 资产账本**：`assets_registry.yaml` 登记每份规则的 canonical 路径与引用者；policy_style_dna / institution_profile / review_scope 各收敛为一份，第二引擎软链；落盘出现重复 canonical 即失败。→ **STY-1、G1-4**。
3. **修错锚**（R8/M-I1）：`conventions.md:27` 与 `distill-report-module/SKILL.md` 的 `style_dna/`→`policy_style_dna/`；改锚后再归档旧目录。→ **X-D1**。

### 🟠 P1（机制补齐）
4. **引用而非复制 + dup-linter**：建 include 原语，self_check 改纯 include；dup-linter 扫近重复即报错。→ **STY-4/STY-3/STY-2/RSN-2**。
5. **验收升级为"改DNA→自动重测→过线才合入" + 三方对账**：把 `tmp_ds_3way_review.py`/`tmp_ds_score_clarified.py` 固化为 CI（去硬编码路径、接 run 参数），任何 DNA 改动须重生成→7 维打分不低于基线且盲测装刀版≥2/3 排第一才合入；加 design-sync 对账。→ **RSN-5/D7/J1/RSN-4 + M-S11/S12 落地**。
6. **金样本准入门**：三套方法统一 gold-sample gate（人写优先/同结构≥2 篇异主题/必配 foil/标 provenance）；strategic/experience 补齐策展集后重蒸。→ **I2、成熟度不均、"学AI腔"**。
7. **跨体例共享刀 + 薄适配层**：cause/driver 等归并。→ **RSN-3/D8**。

### 🟡 P2（收口）
8. **层边界 linter**：`layer_ownership.md`（语气/语域=文风、判断/证据=推理、落点=机构）+ "越界即报错"。→ **X-D1/E4/F/RSN-2**。
9. **主题外提门 + schema 对齐校验**（造体例落盘时）。→ **I2/I1/STY-5**。
10. **subtype/步骤键蒸成数据**（module.yaml 声明，runner 只读）。→ **STY-5/D8**。

---

## 五、展示样例盘点（5 篇 A–E）

> 路径 `method_audit/samples/`（已从微信 `2026-07/展示样例/` 拷入）。这正是会议盲测的 A–E。**揭盲：C、E 人写（质量更高），A、B、D AI 写。**

| 维度 | A | B | C | D | E |
|---|---|---|---|---|---|
| 题材 | AI+教育 | 美AI人才→我 | AI+教育 | 终身教育 | 中美AI人才 |
| 体例 | 国际比较 | 战略应对 | 国际比较 | 趋势研判 | 战略应对 |
| 人/AI | **AI** | **AI** | **人(优)** | **AI** | **人(优)** |
| 字数 | 8944 | 3141 | 7743 | 5810 | 3120 |
| 核心方法动作 | 单轴三分型 | 对手-对策对位 | **双轴正交分类+证据甄别** | **成熟度分级+反例+证据降级** | **史料抽结构+条款级对照** |
| 同题对照 | 与 C | 与 E | 与 A | 独一 | 与 B |

**用作蒸馏样本的建议（gold/foil 归属）：**
- **国际比较 gold → 文章C（人写）**：双轴正交分类（顶层设计×实施机制）+ 对材料真伪的批判甄别（明说澳某"框架"不能算政策规划）。A 作对照正样本，教"英文原始文件名+年份"引证纪律（A 的引证密度反而更高）。
- **趋势研判 gold → 文章D（AI 写但方法骨架好）**：成熟度光谱、反例陷阱、证据降级、对策时间分层完整。**注意**：用作 gold 须剥离/标注其**未核验的精确数字**（AI 精确数字幻觉的典型），只蒸方法骨架。
- **战略应对 gold → 文章E（人写）** 为主 + **文章B（AI）为"对位句式"辅助**：E 教"从史实抽结构、条款级对照、可操作对策"，B 教"每条对策咬住对手一个动作"的因-应闭环句式。
- **天然 foil 配对**：**A vs C**（资料归档 vs 分析研判）、**B vs E**（形式对位/弱信源 vs 实质对照/史料厚度）、**D 的数字**单独作"AI 精确数字幻觉"负样本。

**人写强在哪（这决定"该从什么样本蒸推理 DNA"）**：① 分类**多轴**（C 双轴 vs A 单轴）；② 对材料有**质量判断/证伪**（C/E）；③ 对策落到**可执行抓手**（E"职称单列/科学家驻校"）。AI 稿的可见指纹：超长平铺段（A）、模板化对位排比（B）、精确数字不可核验（D）。→ **推理 DNA 优先从 C/E 蒸这四类判断动作；A/B 更宜作 foil 反向定义"不合格"。**

---

## 六、Kimi OCR 语料盘点（38 篇）

> 路径 `/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md/`。约 70 万字，教育政策内参四大类。**总体可用性：高。**

**质量分档（gold 7 / foil 8 / 中 23）：**
- **文风 gold（7 篇，学表达骨架）**：中美AI人才竞争及应对策略、警惕美竞争法案带来的重大风险、美英澳新一轮人才争夺及破解（**前三 ZL 类是"风险预警→建议闭环"最纯范式，首选**）、人工智能+教育国际比较报告、拔尖创新人才早期培养国际经验及启示、从国际经验优化课后服务、主要国家将超常儿童上升为国家战略。
- **推理 foil（约 8 篇，逆抽判断刀的负样本）**：**主要国家教育国际战略趋势和动向、欧美国家主要体育课程模式**（两篇已被 reasoning_dna 点名当反例，确认适配）、主要国家学校体育发展综述、美英德澳体育教师做法、国外终身教育改革动向、2016-2020国际终身教育趋势、主要国际组织推动终身学习路径、国外K12计算思维测评。共性：**逐国罗列、有"是什么"无"为什么"、无对我国诊断与对策**。
- **中间层（约 23 篇）**：不整篇投喂，仅需"比较结构模板/表格化呈现"时按段抽取。

**OCR 质量抽查结论**：文件夹名"文本缺失"是保守警示，**实际保真度高**——无替换字符/方框乱码、表格完整、脚注保留、无一篇被截断。**唯一要清的 3 处一次性瑕疵（非缺字）**：① 3 篇首行残留 `FILE_NAME:` 元数据（2016-2020终身教育、中考改革国际比较、国外终身教育改革动向）；② 2 篇标题"国外/国际"错配；③ 个别标题因文件名合规折成两行。

**投喂口径**：按 gold 7 / foil 8 / 中 23 三档分流；投喂前清掉 3 处 `FILE_NAME:` 残留（否则污染文风样本）。这批语料可直接作教育政策内参体例的蒸馏底座，与 `jiaokeyuan-researcher`、`distill-reasoning-dna` 两个 skill 配套。

---

## 七、附：改进后的"统一蒸馏闭环"示意

现状（各自为政、复制落盘、只验能跑）：
```
范文/金样本 → [各套 SKILL 逐单元蒸] → 写一堆 md 文件 → dry-run 能跑 → 完
              (各造术语)   (物理复制)              (无对账/无盲测)
```

改进后（schema 前置、单一真源、引用、对账、盲测合入）：
```
                     ┌─ phase-0: 共享词汇表 schema（证据分级/语域黑名单/对策纪律/层归属）先定义一次 ─┐
                     ▼                                                                          │
人写金样本(≥2篇异主题)+foil ─► [蒸单元:只引用schema,不内联] ─► 落"单一真源"(assets_registry) ─► 引用而非复制
   ▲(gold准入门:标provenance)                                                      │
   │                                                                              ▼
   └───────────── 盲测合入门(人稿为gold基准,过线才合) ◄─ 跨文件对账 + 设计↔实现↔文档对账 ◄─ dup-linter/越界linter
```
**六个卡点**：① 金样本准入（人写优先）② schema 前置 ③ 单一真源落盘 ④ 引用而非复制 ⑤ 三方对账 ⑥ 盲测合入。任一不过不许收敛。

---

*本评估由 9 个 agent（5 盘点 + 4 批判）产出，共 29 条方法缺陷 + 29 条改进，均连回具体问题 pid 与 file:line。与《待解决问题清单_移交设计.md》《文风DNA与推理DNA_内容耦合专项.md》互为上下游：那两份是"问题"，本份是"造成问题的方法根因与改法"。*
