# 路 D · trend_review reasoning_dna · round_1 · dev

> 体例：trend_review（国际动向研判 + 中国对策）
> 范围：仅本路 deliverable，即 `report_modules/trend_review/reasoning_dna/{signal,driver,stage,uncertainty}.md` 四把刀 + `report_modules/trend_review/module.yaml` 的 `reasoning_dna_injection` 映射行。未碰 runner.py、未碰其他体例模块或已验证产物。样本只读 `gold_samples/`。无 API、未联网。全部绝对路径。

## 本轮做了什么

- 先读 `reasoning_dna/conventions.md`（强制三段式：必答问题 / 什么算答到了（含反例）/ 降级扫描要求；红线＝"完成降级扫描 + 留可审查取舍记录"，不强求造否定）。
- 风格参照 strategic_response 的 {threat,intent,hedge} 与 experience_response 的 {cause,efficacy}（学形态，不抄内容）。
- 完整阅读 4 篇 trend_body 金样本 + 2 篇 shallow_foils，逆向抽取"深稿比条目堆叠综述多做的推理动作"。
- 勘察结论：trend_review 的推理链是"信号识别→趋势归纳→阶段研判→对我国对策"，深稿 vs 浅稿的分水岭集中在四处推理动作 → 定稿 4 把刀。元问题均写成**领域无关**（无"AI/工程/数字化/体育"等选题词），三段式 + 降级红线齐备，每段反例锚定到具体浅综述失败样态。
- 这是 round_1，无上轮 review 反馈；按 conventions 自校并预留探针区分力（金样本判"已答"、浅稿判"未答/未做扫描"）。

## 勘察结论：为什么选这 4 把刀

逐篇看下来，trend_body 金样本在"信号→趋势→阶段→对策"四环各自比 shallow_foil 多做了一个可检查的推理动作，恰好对应四把刀：
- **signal（信号刀）**：金样本把零散现象收敛成"有名有姓的趋势条"并给共现/数据/持续性依据；浅稿只逐国平铺战略文件名。
- **driver（成因刀）**：金样本问"被什么力量推着走、动力是否续"；浅稿从不问"为什么此刻发生"。
- **stage（阶段刀，最关键）**：金样本把中国定位到"落后/缺配套/已过度/领跑有隐忧"某一档再定对策方向；浅稿把每条趋势镜像翻成"国外有X→我国也搞X"。
- **uncertainty（不确定性刀）**：金样本区分"已成定局"与"正在形成/有待观察"、点出反转风险；浅稿把目标承诺当兑现、零变数线性外推。
未增删合并：四环各保留一刀，stage 与 uncertainty 因同时服务"研判核心步"与"落笔步"做双挂载。

## 每刀从哪几篇样本抽取了什么推理动作

### signal.md（信号刀）— 真趋势 vs 个案/噪音
- **世界教育数字化发展态势分析**：以"OECD 一半以上成员国都发布专门数字教育战略"等**多国共现**支撑趋势成立 → 抽出"共现广度"判据。
- **全球经验·AI 拔尖人才六大趋势**：用"全球 2.2 万 AI 拔尖人才中美占 46%、中国 11%"等**数据**坐实趋势规模 → 抽出"证据状态"分级（数据/立法/文件/媒体）。
- **国际工程教育改革动向和趋势**：国际工程联盟框架"出到第 4 版"、学位学徒分阶段推进 → 抽出"持续性/跨年迭代"判据。
- **国际基础教育阶段培养目标与评价改革动向**：荷兰"与水共处"水教育、日本海洋立国 → 抽出"单国特色个案不得冒充全球趋势"。
- **shallow_foil 主要国家教育国际战略趋势和动向**：逐国罗列战略文件名 + "提出/计划/旨在/将"，从不判"这算不算经验证的趋势" → 定为"单点升格 / 条目堆叠冒充趋势归纳"反例。
- 抽象扫描：逐趋势标 共现广度 + 证据状态①~④ + 持续性 → 单国③④级降为"苗头/动向"或标个案。

### driver.md（成因刀）— 被什么驱动、动力是否持续
- **全球经验·AI 拔尖人才六大趋势**：纵观教育史"拔尖人才培养普遍起始于国家危机"（美苏争霸、石油危机）、AI 视为关乎国家安全的战略资源 → 抽出"驱动力归类（含地缘竞争/危机催化）"。
- **世界教育数字化发展态势分析**：在线/混合教学"面对世纪疫情挑战"骤兴 → 抽出"持续性：依赖一次性事件（疫情）冲击退去可能回落"。
- **国际工程教育改革动向和趋势**：可持续发展+数字化"两大转型方向"由 SDGs 理念与计算科学突破共同驱动 → 抽出"技术/制度/思潮多源驱动"。
- **shallow_foil 欧美国家主要体育课程模式**：每模式只标"谁哪年提出（Siedentop 1994 等）"、不说被什么力量推广 → 定为"把发明史当驱动力"反例。
- **shallow_foil 主要国家教育国际战略**：满篇现象、从不问"为什么这个国家此时推" → 定为"纯枚举无因"反例。
- 抽象扫描：逐趋势标 驱动类型 + 归因强度①~③ + 持续性 → ①②层标"成因待补"、依赖一次性事件者禁线性外推（为 stage 埋前提）。
- 注：与 experience 的 cause 刀同名同源但角度不同（cause 问横向国别差异，driver 问纵向动力与持续性），dev 内已注明，避免两体例刀重名混淆。

### stage.md（阶段刀，核心枢纽）— 中国处在哪一步决定对策方向
- **全球经验·AI 拔尖人才六大趋势**（本刀主范本，stage 推理最完整）：
  - 落后/空白 → "低龄入手"段"我国虽有零星实践，但明确意识和清晰路径尚未形成，有必要参照加快布局"；
  - **已过度/有特异风险 → 刹车**："拔高地位"段"中国新增 AI 独立专业已达 180 所，但脱不开粗放浮躁，有必要对未来结构性过剩的前景有所预警"——同一条"独立专业"国际趋势上，对中国给出与"跟进"**相反**的方向；
  - 领跑有隐忧 → "中国从粗放数据看处于第一梯队，但理论创新不足、关键技术存在空白，避免后劲乏力、徒顶虚名"。
  - 这三处共同抽出本刀骨架：**决定对策的不是国外做法本身，而是中国的阶段位置**，四档（落后/缺配套/已过度/领跑有隐忧）→ 四种对策方向（跟进/补配套/预警刹车/补短板防虚顶）。
- **国际工程教育改革动向和趋势**：第八节"我国中小学工程教育交叉程度较弱…可继续加强融入技术教育、在科学数学中整合"→ 抽出"已上马缺配套→补配套"档。
- **shallow_foil 两篇**：通篇只夸国外、落到中国仅"可为我国…提供参考"一句，无中国阶段定位 → 定为"镜像翻译 / 只夸国外不提中国 / 回避刹车档"反例。
- 抽象扫描：逐趋势标 中国位置 + 定位依据 a/b/c + 对策方向 + 方向—位置一致性 → 镜像翻译须补定位后改写或删；漏判"已过度"档即视为未做阶段研判。

### uncertainty.md（不确定性刀）— 把握度与变向条件
- **全球经验·AI 拔尖人才六大趋势**：开篇"避免后劲乏力、徒顶虚名"、"独立专业"段既认其为"难以逆转的趋势"又同时"对结构性过剩预警" → 抽出"既判趋势又留反向风险/把握度"。
- **国际工程教育改革动向和趋势**："独立"本身"确是世界范围内难以逆转的趋势" → 抽出"高把握＝可用确定性措辞"的正例标尺。
- **世界教育数字化**：疫情催化的远程教学（接 driver 的持续性判断）→ 抽出"驱动衰减则趋势可能回落"的变向条件。
- **shallow_foil 主要国家教育国际战略**：把"2025 翻一番""提高到 20%""350 亿英镑"等**目标承诺**当既定走向平铺 → 定为"把目标当兑现 / 把研判写成定论"反例。
- 抽象扫描：逐研判标 把握级别 高/中/低 + 关键变数 + 对策强度匹配 → 低把握禁用"必然/不可逆"、对策须留试点/观察余地、指标为承诺须标"待兑现"。

## reasoning_dna_injection 映射（已写入 module.yaml）

按任务建议挂载（step 用任务 id）：
```yaml
reasoning_dna_injection:
  map_pressure_judgment: [signal, driver, stage]   # 趋势研判核心步：信号→成因→阶段
  plan_article: [stage, uncertainty]               # 落笔步：定阶段对策 + 标把握度
```
- assign_material_roles / build_suggestion_pool / prioritize_policy_options 本轮不挂（MVP 四刀聚焦研判与落笔两步，gated：刀缺失则该步零注入，不影响运行）。
- stage 双挂（研判时定位中国阶段、落笔时据位置出对策方向），与 conventions 的"一刀可在多步复用"不冲突。
- 已用 `python3 -c "import yaml; ..."` 校验 module.yaml 解析正常，映射读出无误。

## 如何回应上轮反馈

round_1，无上轮 review。已自查对齐：
1. 严格三段式齐全（必答问题 / 什么算答到了（含反例）/ 降级扫描要求 + 取舍记录格式 + 红线）。
2. 元问题领域无关（四刀均无具体选题词）。
3. 红线＝扫描+结论+理由、不强逼否定，四刀均给"无需降级须说明依据"的出口。
4. 反例直接引金样本/浅综述失败样态，确保探针能把金样本（判"已答"）与浅稿（判"未答/未做扫描"）区分开——尤以 stage 刀的"镜像翻译"反例对照 shallow_foil 的"国外有X→我国也搞X"最直接。
待 review 给出区分力/反例充分性意见后于 round_2 修订。

## 产出文件（绝对路径）
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/report_modules/trend_review/reasoning_dna/signal.md
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/report_modules/trend_review/reasoning_dna/driver.md
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/report_modules/trend_review/reasoning_dna/stage.md
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/report_modules/trend_review/reasoning_dna/uncertainty.md
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/report_modules/trend_review/module.yaml（仅 reasoning_dna_injection 映射）
- /Users/hujingkai/Documents/New project/example1/strategic_response_workflow/multiagent_build/route_d/round_1/dev.md
