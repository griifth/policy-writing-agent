# 路 C · experience_response reasoning_dna · round_1 · dev

> 体例：experience_response（国际经验借鉴 + 中国应对）
> 范围：仅本路 deliverable，即 `report_modules/experience_response/reasoning_dna/{cause,efficacy}.md`。未碰 runner.py、未碰其他体例模块或已验证产物。样本只读 `gold_samples/`。无 API、未联网。

## 本轮做了什么

- 先读 `reasoning_dna/conventions.md`（强制三段式：必答问题 / 什么算答到了（含反例）/ 降级扫描要求；红线＝"完成降级扫描 + 留可审查取舍记录"，不强求造否定）与 `DESIGN.md`（§5.2 给定 cause/efficacy 的元问题与扫描动作）、`review_scope.md`。
- 完整阅读 4 篇 experience 金样本 + 2 篇 shallow_foils，逆向抽取"深稿比浅综述多做的推理动作"。
- 写成 2 把刀：`cause.md`、`efficacy.md`，元问题均写成**领域无关**（无"天才/体育/课后服务/学制"等选题词），三段式 + 降级红线齐备，每段反例都锚定到具体浅综述失败样态。
- 这是 round_1，上一轮无 review 反馈可回应；本轮按 DESIGN §8 第四步（MVP 两刀）+ §5.2/§6 红线自校，并预留探针区分力（金样本判"已答"、浅稿判"未答"）。

## 每刀从哪几篇样本抽取了什么推理动作

### cause.md（成因刀）
- **国外学制发展特点 趋势及启示**：日本战后"绝对平等主义"→禁天才教育、英/德天才教育"沉寂期/停滞期"归因于社会思潮+保守党执政+"浪费金钱"批评 → 抽出"路径**可变性/中断回潮**也要归因"这一动作；启示段"每个国家学制调整都有其特定历史背景、现实需求"→抽出"差异有成因"。
- **拔尖创新人才早期培养国际经验及启示**：日本"以才能取代天才"归因"受平等文化影响"、芬兰"转化天赋"概念"更符合芬兰国情" → 抽出"概念/做法挂可核对条件，而非贴标签"；分权体制（加/德/澳各州独立立法）解释国别差异 → 抽出"国别差异的根子＝体制/文化"。
- **shallow_foil 主要国家教育国际战略趋势和动向**：逐国罗列战略文件名与指标、从不问"为什么这个国家此时推这条" → 定为"纯枚举"反例。
- **shallow_foil 欧美国家主要体育课程模式**：每个模式只标"谁哪年提出" → 定为"把发明史当成因"反例（人名年份≠成因）。
- 抽象出的扫描：逐做法标**归因层级**①缺失/②贴标签/③深层 + 可变性，①必降、②应降。

### efficacy.md（有效性刀）
- **从国际经验中优化课后服务推动双减政策落地**：用瑞典 83% 参与率、韩国素质课程占比 77%/54%/16% 等**运行数据**支撑结论，制度类点明立法/资格证书 → 抽出"证据等级＝意图/制度/规模数据/评估"四级，并把数据级当可学经验。
- **拔尖创新人才早期培养国际经验及启示**：英国项目"进入停滞期"、日本多次起停 → 抽出"持久性/负面轨迹也要查，目标值≠业绩"。
- **shallow_foil 主要国家教育国际战略趋势和动向**：满篇"提出/计划/旨在/将…翻一番/达到100万"，把**未兑现的战略目标**当经验 → 定为本刀首要反例"把动向当经验"。
- **shallow_foil 欧美国家主要体育课程模式**：以"实践证明能有效促进…"一句自证、无母国规模/评估 → 定为"理念自证"反例。
- 抽象出的扫描：逐做法打证据等级①意图/②立法建制/③规模数据/④评估，①与"仅媒体转述"应降级为"动向"，并要求**正文措辞随等级走**（经验 vs 计划/正在推进）。

## 如何回应上轮反馈

round_1，无上轮 review。已自查对齐：(1) 严格三段式齐全；(2) 元问题领域无关；(3) 红线＝扫描+结论+理由、不强逼否定，两刀均给"无需降级须说明依据"的出口；(4) 反例直接引浅综述失败样态，确保探针能把金样本/浅稿区分开。待 review 给出区分力/反例充分性意见后于 round_2 修订。

## 产出文件（绝对路径）
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/report_modules/experience_response/reasoning_dna/cause.md
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/report_modules/experience_response/reasoning_dna/efficacy.md
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/multiagent_build/route_c/round_1/dev.md
