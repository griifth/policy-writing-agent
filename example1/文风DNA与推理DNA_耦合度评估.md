# 文风DNA × 推理DNA · 耦合度评估

> ⚠️ **本文部分结论已被《文风DNA与推理DNA_内容耦合专项.md》修正，以后者为准。**最关键一处：本文曾判 `style_dna/` 为"无引用死目录、可删"——后经内容层比对确认 `reasoning_dna/conventions.md` 曾把它当语域锚引用，**不能直接删**（正确顺序：先改锚、再归档。2026-07-05 起已按此执行，见《修改执行记录_2026-07-05.md》）。

> 方法：派 3 个子 agent 逐个打开全部 DNA 文件精读——① 文风DNA（policy_style_dna，两引擎共 24 文件 + 死目录 style_dna）；② 推理DNA（reasoning_dna，3 共用 + 9 把体例"判断刀"）；③ 注入机制代码（runner.py / module.yaml / report_pipeline.py）。所有判定基于真实文件:行。

## 一句话结论

**要分两层看，别一概而论：**

- **核心问题——"文风DNA ↔ 推理DNA"两者之间：代码结构上是"真解耦、可各自插拔"（低耦合）。** 这是你们"提示词可插拔"卖点在这一块**成立**的硬证据：独立读取函数、独立资产目录、独立 prompt 锚点、gated 数据驱动注入，且在流水线步骤上物理错开（推理只挂"判断/构思"步，文风只挂"写作/审查"步，交集为空），改一种零波及另一种。
- **但整体不能说"耦合度低"——有 4 笔明确偏高的耦合债**，集中在：跨引擎复制、文风DNA 内部、内容职责泄漏、推理DNA 跨体例重复。这些不改，"可插拔/可维护"会随时间退化。

**总评：结构解耦（好）＋ 内容耦合偏高（需还债）。**

---

## 二、分轴耦合矩阵

| 耦合轴 | 判定 | 一句话 |
|---|---|---|
| **文风DNA ↔ 推理DNA（代码结构）** | 🟢 **低** | 独立函数/目录/锚点、gated 注入、步骤错开，互不波及——**卖点成立** |
| **文风DNA ↔ 推理DNA（内容职责）** | 🟠 **中** | 不完全正交：文风DNA 混入了判断强度/证据分级/建议可行性；推理DNA 混入了语域措辞红线 |
| **文风DNA 内部（wiki 各文件）** | 🔴 **高** | 通则+子型覆盖+self_check 派生汇总三层，交叉引用密集、同一规则重复 6 处，改一处牵动 2–3 处 |
| **推理DNA 内部（各"刀"之间）** | 🟠 **中（同体例内偏高）** | 同体例几把刀是"连环逼问链"、下游吃上游产物（非正交模块）；跨体例松耦合 |
| **推理DNA ↔ conventions 模板** | 🟠 **高但良性** | 9 把刀全遵循同一元格式，改 conventions 波及全体——是刻意的防漂移一致性 |
| **文风DNA 跨引擎重复** | 🔴 **高（且在漂移）** | 两份 policy_style_dna，10/12 逐字节复制、2/12 已各改各的，无单一真源 |
| **推理DNA 跨引擎** | ⚪ 不适用 | 只在 strategic 引擎；根引擎无推理DNA（"待接入"） |
| **文风DNA ↔ 体例** | 🟠 **中** | 宣称全局，但 subtype_a/b 按 report_type 硬路由绑了体例 |
| **推理DNA ↔ 体例** | 🔴 **高（可控）** | 刀 per-体例私有 + 注入绑死步骤；换体例=换整套刀（设计如此） |
| **DNA ↔ 引擎代码** | 🟢 **低** | 纯 markdown，按文件名读取、缺失即零注入，不改代码就能增删 |

---

## 三、好消息：文风↔推理 在代码层是真解耦的

来自"注入机制"agent 的**步骤 × DNA 注入矩阵**（`strategic_response_workflow/workflow/runner.py`）：

| 步骤 | 文风DNA | 推理DNA | 站位 |
|---|:--:|:--:|:--:|
| assign_material_roles（判断） | — | ✅ | — |
| map_pressure_judgment（判断） | — | ✅ | — |
| plan_article（构思） | — | ✅ | ✅ |
| build_suggestion_pool（构思） | — | ✅ | ✅ |
| prioritize_policy_options（构思） | — | ✅ | ✅ |
| **write_draft（写作）** | ✅ | — | ✅ |
| **review_draft（审查）** | ✅ | — | — |
| **revise_article（修改）** | ✅ | — | — |

- **推理只管"想清楚"、文风只管"写/审得像"，步骤集合交集为空。**
- 注入是"末尾各追加一段带独立标题的块"（推理→`## 本步必答逼问`，文风→`## 政策研究文风 DNA`，站位→`## 机构定位与建议落点`），彼此不知情，可单独增删。
- 都是 gated：`runner.py:851-855` 刀文件缺失即返回空串、原样放行；`runner.py:840-841` 文风文件缺失走兜底。**加/减一把刀只需改 module.yaml + 放一个 .md，不动 Python。**
- 移除全部刀 → 写作/审查步文风注入毫发无损；换掉文风 wiki → 判断步的刀毫发无损。**单独替换任一种 DNA，另一种零感知。**

> 结论：**"文风与推理两套 DNA 可各自插拔"这个说法，代码支持得住。**

---

## 四、但有 4 笔偏高的耦合债（该还）

### 债 1 🔴 跨引擎复制耦合（最危险，已在漂移）
`workflow/policy_style_dna/` 与 `strategic_response_workflow/policy_style_dna/` 是**两份拷贝**，`diff`/`md5` 实测：
- **10/12 文件逐字节相同**（靠手工复制保持同步）；
- **2/12 已内容漂移**——`review_scope.md` 重度漂移（strategic 版多出整节"可读性校对/删元说明句"，workflow 版没跟上）、`forbidden.md` 轻度漂移（"素材来源外露"条措辞不同）。
- **没有单一真源**。改一处文风规则要手动同步两处，否则漂移扩大。这是"复制耦合正在退化为漂移"的中间态。
- **建议**：抽一份共享真源（软链/子模块/构建期拷贝脚本），或至少加一个"两份一致性"校验。

### 债 2 🔴 文风DNA 内部高耦合
`voice/structure/sentence/forbidden/recommendation/self_check/subtype_a/subtype_b` 之间：
- 交叉引用密集（voice→subtype、structure→subtype、recommendation→subtype、self_check→L3 子型…）；
- 同一条纪律（"判断∶证据≈1∶N / 先断后证"）在 **6 个文件各写一遍**；
- `self_check.md` 基本是 voice/structure/forbidden 规则的**重复汇总**（派生索引，无独立规则）；
- **subtype_a/b 用"覆盖 voice 通则第 2、4 档"的方式条件改写通则**——voice 说"慎用必须/立即"、subtype_a 说"可用强命令"，靠"子型"隐含开关调和，改 voice 判断强度就会与子型打架。
- **后果**：改任一 wiki 文件几乎必牵动 2–3 个其它文件。

### 债 3 🟠 内容职责泄漏（文风↔推理不完全正交）
名义上"文风只管怎么写、推理只管怎么判"，实际互相串了：
- **文风DNA 里混入了推理内容**：`recommendation.md:9-13` 整节"政治/资源/能力可行 + 可追溯"是纯**可行性判断**；`voice.md:11-18` 的"判断两档强度 / 判断∶证据分级 / 证据分级"本质是**推理纪律**；`review_scope.md` 里"判断强度失当/悬空建议/本土化缺失"是**对策落点+站位**——这些本应属 reasoning_dna / institution_profile。
- **推理DNA 里混入了文风内容**：`conventions.md:24-30` 的"语域红线"（绞杀/围堵/收割等定性词须降级）是**措辞分寸**，每把攻防刀又各自复述一遍。conventions 自己也承认它审两件事（判断深度 + 措辞分寸）。
- 好的一面：两个 `review_scope.md`（一个 `reasoning_compliance` 审判断、一个 `style_and_expression` 审文风）**职责分得干净、无重叠**。
- **建议**：把"判断强度/证据分级/建议可行性"从文风DNA 迁回推理层，让文风DNA 回归"只管怎么写"。

### 债 4 🟠 推理DNA 跨体例重复债
- `cause`（experience）与 `driver`（trend）是**同一逼问复制成两份微调角度**（`driver.md:5` 自认"同名同源"）；
- "证据①②③④分级"这一子逼问在 `efficacy.md:11` / `signal.md:34` / `threat.md:28` **多把刀里各复述一遍**，未抽成共享子刀；
- 同体例内刀是**连环逼问链**（`hedge.md:8` 显式"对冲前面 threat 识别的压力"、`uncertainty` 吃 `stage` 产物）——这是设计使然，但意味着"抽一把刀单独复用"不现实。
- **建议**：把"证据分级""成因归因"这类跨体例复用的子逼问抽到共享层（放 `reasoning_dna/` 根），各刀引用而非复制。

---

## 五、附带发现（顺手值得清理的）

1. **死目录** `strategic_response_workflow/style_dna/`（无 `policy_` 前缀，含 24 篇范文语料）——**无任何代码引用**，是被 policy_style_dna 替代的前身。建议归档（保留 `processed/` 语料作重蒸馏素材）。
2. **死文件**：根引擎 `report_pipeline.py:589` **写死 `files.append("subtype_a.md")`**，永远加载不了 `subtype_b.md`——根引擎里的 subtype_b 是死文件（strategic 引擎才动态路由 a/b）。
3. **推理 review_scope 未接线**：`reasoning_dna/review_scope.md`（`reasoning_compliance` scope）**没接进 runner 的 `_SCOPE_SOURCES`**（只有 style_and_expression / precedent_check）——推理对账目前靠刀注入+快照，那份 scope 走不到审查交接路径。
4. **文档漂移**：`policy_style_dna/README.md` 仍写"根工作流零 style_dna 注入（待办）"，但 `report_pipeline.py:399/440/582` 已接入——README 过期。
5. **DESIGN 与实现脱节**：`reasoning_dna/DESIGN.md` 讲的是 `benchmark_response` 6 刀，磁盘上实际是 `experience_response`(2 刀)+`trend_review`(4 刀)+`strategic_response`(3 刀)。

---

## 六、给你的判断与建议

**回答"耦合度高不高"：**
- **两套 DNA 之间（文风 vs 推理）在工程结构上耦合低、可插拔**——这是好的，卖点站得住。
- **但"内部耦合 + 跨引擎复制 + 内容职责泄漏"三处偏高**，是真正的技术债，会拖累维护和"单独换一套风格/换一套判断"的灵活度。

**最该先解的 3 件（按性价比）：**
1. **消除跨引擎复制（债 1）**——抽单一真源或加一致性校验。**风险最高（已在漂移）、成本低。**
2. **文风DNA 去泄漏（债 3）**——把判断强度/证据分级/建议可行性迁回推理层。**让"可插拔"名副其实。**
3. **文风DNA 内部瘦身（债 2）**——self_check 改为纯引用、subtype 覆盖关系显式化，减少"改一处连锁改多处"。

顺手清掉附带发现里的死目录/死文件/过期文档，能进一步降噪。

---

*本评估由 3 个子 agent 分头精读全部 DNA 文件后整合，所有判定均可回溯到具体文件与行号。*
