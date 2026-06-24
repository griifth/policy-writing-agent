# 路 B · 动向研判体例模块 trend_review — 开发记录（round_1）

- 体例模块：`report_modules/trend_review/`
- 体例：国际动向研判 + 中国对策
- 固定推理链：信号识别 → 趋势归纳 → 阶段研判 → **对我国的影响与对策建议**
- 脚手架起点：`report_modules/experience_response/`（改写，非新造骨架）
- 硬边界遵守：仅在 `report_modules/trend_review/` 内新建；未改 `workflow/runner.py`；未碰其他体例模块或已验证产物；gold_samples 只读。

## 一、第一步结构勘察结论（取样定稿）

### 趋势主体取样（参照 `gold_samples/trend_body/`，选最成熟者）
逐篇勘察 4 篇 trend_body：
- **`AI拔尖人才六大前沿趋势`**——首选。中美对比开篇 + 六大趋势归纳，**逐趋势带中国位置研判**，趋势主体最成熟，最贴合“信号→趋势→阶段”。但其收尾为反思式“值得我国重视/有所布局”，属对策塌尾。
- **`国际工程教育改革动向和趋势`**——参照。8 大改革特征归纳成熟，提供多趋势并归骨架；**全文无中国对策收尾**，是“只判趋势、不出对策”的典型。
- **`世界教育数字化发展态势分析`**——参照。多维度态势八条归纳；同样**无对策收尾**。
- `国际基础教育阶段学生培养目标…`——三段式（目标—指标—改革），偏指标罗列，趋势研判力弱于上三篇，未入选。

**选定 3 篇趋势主体：AI拔尖人才六大前沿趋势（首选）+ 国际工程教育改革动向和趋势 + 世界教育数字化发展态势分析。**

### 对策落点取样（移植 `gold_samples/strategic|experience/`，**不照抄 trend_body 收尾**）
- **`strategic/中美AI人才竞争及应对策略`**——首选对策范本。闭环最完整：措施→意图→对华压力→中国短板→六条加粗领起句建议，每条含专项/牵头部门/试点/评价机制等抓手。
- **`experience/拔尖创新人才早期培养国际经验及启示`**——辅助对策范本。七条建议逐条回扣前文经验，提供“每条对策回扣前文研判”的纪律参照。

### 反例
- **`shallow_foils/主要国家教育国际战略趋势和动向`**——十大趋势条目逐条堆叠、每条逐国铺陈、无递进无阶段研判、完全不落中国对策。审查/探针据此判“未答”。

### 关键判断（决定主范文构造）
三篇趋势主体的对策收尾均**塌尾或缺失**。因此主范文 `source/sample.md` 的对策段**不取自趋势主体**，而移植自战略金样本：
- 趋势主体（一、二节）= 取自 `AI拔尖人才六大前沿趋势` 真实文本；
- 对策收尾（三、四节）= 移植 `中美AI人才竞争及应对策略` 真实政策建议；
- 两段同属 AI 拔尖人才领域，自然衔接，未编造事实。
这样使“强制对策落点”这一体例红线在标杆范文里就已坐实，避免动向模块抄进 C 样本/trend_body 的“无对策”病。

## 二、改写要点（相对 experience_response 脚手架）

| 文件 | 改写 |
|---|---|
| `module.yaml` | name: trend_review；label: 国际动向研判 + 中国对策；retrieval_types 改为动向/信号口径 6 类：`trend_signals / cross_country_practices / driver_analysis / maturity_assessment / china_status_and_gaps / response_evidence`（非照搬战略六类）；写入固定推理链与“强制对策收尾”体例红线注释；`reasoning_dna_injection: {}`（本批不配刀，gated 留空）。 |
| `prompts/retrieval.md` | 六类检索任务全部改为“信号—趋势—驱动—阶段—中国现状—对策依据”口径；强调按所处阶段/成熟度带出证据状态。 |
| `prompts/task_redefinition.md` | 从“趋势综述题”重定义为“判断型动向研判题”；新增**“对策落点约束（强制）”**段，要求独立对策收尾且对策可回扣。 |
| `prompts/material_roles.md` | 角色标签改为 信号源/趋势佐证/驱动证据/阶段证据/…/对策依据；互证关系改为 信号→趋势→阶段、中国短板+对策依据→对我国对策。 |
| `prompts/pressure_judgment_mapping.md` | 判断步内容换为“信号→趋势研判+阶段定位”，每条趋势**预埋“对我国意味着什么”**接口，作为通往对策的枢纽。 |
| `prompts/planning.md` | 章节序列强制落到“信号→趋势→阶段→对我国对策”，对策章独立收尾；新增**“从研判到对策的推导路径（强制）”**，逐条标注对策由哪条研判推导。 |
| `prompts/suggestion_pool.md` | 对策池：每条对策回扣字段 + 中国制度载体 + 与趋势成熟度匹配（萌芽信号只能前瞻布局）；写法移植金样本成熟收尾。 |
| `prompts/policy_priority.md` | 近期/中期/长期排序以“趋势成熟度 + 中国承接条件”为主依据；萌芽趋势降级到长期前瞻布局。 |
| `prompts/writing.md` | 写作总原则锁定固定四段链；新增独立**“体例红线（强制）”**段（必须有对我国对策收尾、严禁照搬趋势主体塌尾）；第四章为“对我国的对策建议（强制收尾章节）”，每条对策含回扣句。 |
| `prompts/review.md` | 审查维度新增“对策落点（重点）/对策回扣/成熟度匹配”；否决规则**首条**即“无独立对策收尾或对策塌缩”。 |
| `prompts/revision.md` | 修改要求与重写触发条件首条均为“补写/重写独立对策收尾、消除悬空对策”。 |
| `templates/article_template.md` | 结构：开篇研判 + 一、趋势主线归纳 + 二、成因与阶段研判 + 三、我国现状差距影响 + **四、对我国对策建议（强制收尾，加粗领起句 + 回扣 + 抓手）**；含写作校验清单。 |
| `source/sample.md` | 合成标杆范文（趋势主体 + 对策落点，见上“关键判断”）。 |
| `source/gold_samples/` | 6 篇只读参考拷贝，文件名前缀标注角色（trend_body__ / policy_landing__ / foil__）。 |
| `source/sample_manifest.md` | 标注每篇“趋势主体/对策落点/反例”角色 + dev 取样结论。 |

## 三、自验（dry-run 实跑）

命令：
```
python3 workflow/runner.py --report-type trend_review --dry-run \
  --topic "人工智能拔尖人才培养国际前沿趋势研判及我国对策" \
  --target-country "美国、英国、日本" \
  --strategy-domain "人工智能拔尖人才培养" \
  --notebook-name "dummy_notebook" \
  --china-response-focus "人工智能拔尖人才培养对策"
```
结果（退出码 0，16 步全跑通）：
- run_log 确认 `体例模块：trend_review（国际动向研判 + 中国对策）`——正确载入。
- 6 个新 retrieval_types 各自生成检索提示词（trend_signals / cross_country_practices / driver_analysis / maturity_assessment / china_status_and_gaps / response_evidence）。
- task_redefinition → material_roles → 判断 → planning → suggestion_pool → policy_priority → writing → review×2 + revision×2 → template_match 全部产出。
- `reasoning_dna_injection: {}` 被 gated 正常处理（reasoning_dna_snapshot 正常生成）。
- 内容核验：生成的 writing 提示词内嵌固定链“信号识别→趋势归纳→阶段研判→对我国影响与对策建议”与强制对策收尾红线；战略体例措辞零泄漏（`对中国压力`/`战略意图及其对中国` 命中 0），确认是动向研判体例而非借用战略/经验体例。

自验用的临时 run 目录已删除，未留测试产物。

## 四、交接给 reviewer 的对标点
- 推理链是否为“动向研判”而非经验借鉴/战略对抗——见 prompts 全套与 module.yaml 注释。
- 防堆叠：是否要求把信号归并为 2-3 条趋势主线（对照反例 foil__）。
- **对策成熟度（最关键）**：是否有独立、不悬空的“对我国对策建议”收尾，对策是否回扣前文研判、是否有抓手（对标 policy_landing__ 金样本，而非 trend_body__ 塌尾）。
