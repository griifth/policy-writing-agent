# 路 D · trend_review reasoning_dna · round_1 · review（对抗式审核）

> 审核员：reasoning_dna 刀对抗式审核员（动向体例），与 dev 不同实例。默认挑刺、不确定即判未过、必须引证。
> 审核对象：`report_modules/trend_review/reasoning_dna/{signal,driver,stage,uncertainty}.md` + `report_modules/trend_review/module.yaml` 的 `reasoning_dna_injection` 映射。
> 元格式 `reasoning_dna/conventions.md`；金样本 `gold_samples/trend_body/`；反例 `gold_samples/shallow_foils/`。
> 结论：**PASS，得分 88/100**。六道硬门全过；扣分项为可在 round_2 处理的非阻断瑕疵。

---

## 硬门逐条裁决（全过才 pass）

### 硬门 1 · 三段式完整 —— 过
四把刀均有且仅有规范三节：`## 必答问题` / `## 什么算答到了（含反例）` / `## 降级扫描要求`，且降级节内含 `**取舍记录格式（逐条留痕）**` 代码块 + `**红线（与 conventions 一致）**`。
- signal.md L6/L16/L29；driver.md L7/L16/L29；stage.md L6/L16/L33；uncertainty.md L6/L15/L28。
- 每刀取舍记录块末行均有 `处理：…` 行（signal L44、driver L42、stage L48、uncertainty L41），即"减法/降级动作"落点，非"写段分析"。

### 硬门 2 · 元问题领域无关 —— 过（borderline，见扣分项）
亲查四刀 `## 必答问题` 节首句（元问题主干）：均为领域无关元问题，无具体选题词作主干。AI / 拔尖人才 / 疫情 / 体育等仅出现在**括注示例**中，conventions L15 只禁选题词进入元问题（"不得出现'AI人才''校园餐'等词"），示例允许。
- signal L8："是真已成形的趋势信号，还是个别国家的孤立事件…"——无选题词。
- driver L9："被什么力量驱动起来的…会持续加力还是衰减反转"——无选题词。
- stage L8："中国相对这条趋势处在哪一步"——无选题词。
- uncertainty L8："把握有多大？在什么条件下会变向…"——无选题词。
- 四刀均含"中国"为对策对象，但这是 trend_review 体例固有结构（module.yaml L8 固定推理链"…→对我国对策"），非选题词，可接受。

### 硬门 3 · 含减法/降级动作（可检查取舍记录），非"写段分析" —— 过
每刀降级节都给出"逐条扫描 → 标注 → 处理（降级/标注/剔除/保留）"的可审查取舍记录，且红线显式要求"做扫描并给结论"而非写段落：
- signal L52 / driver L50 / stage L57 / uncertainty L49 均收尾于"可审查的产物是'扫描+…+处理结论+理由'，不是'写一段X'"。
- 取舍记录格式含明确降级动作动词：signal"降级为'苗头/动向'｜标个案｜剔除（噪音）"；driver"标'成因待补'｜标'持续性存疑慎作长期外推'"；stage"改写为'按中国所处X档…'｜删（镜像建议）"；uncertainty"改写为'有待观察'｜对策放宽为'先试点'｜标'待兑现'"。

### 硬门 4 · 反例锚点（明确写"什么算糊弄/未答"） —— 过
四刀均有显式 `**反例（糊弄 / 未答）：**` 小节，且锚到具体浅稿失败样态（非空泛）：
- signal L23-27："单点升格""条目堆叠冒充趋势归纳"，引 `主要国家教育国际战略趋势和动向.md`。
- driver L23-27："纯枚举无因""贴标签当成因""把发明史当驱动力"，引 `欧美国家主要体育课程模式.md`。
- stage L26-31："镜像翻译（国外有X→我国也搞X）""一律跟进""回避刹车档"。
- uncertainty L22-26："把研判写成定论""把目标当兑现""零变数外推"，引 `主要国家教育国际战略…md`。
- **反例锚点经实证为真**（非杜撰）：`欧美国家主要体育课程模式.md` 实测含"1994年提出/1982年提出/1995年提出"且 why-now 驱动语 0 处——精确命中 driver"把发明史当驱动力"反例；`主要国家教育国际战略…md` 实测含 17 处"提出/计划/旨在/将…到20XX/翻一番"——精确命中 uncertainty"把目标当兑现"反例。

### 硬门 5 · 探针区分力（亲测金样本 vs 浅稿，每刀各判一次） —— 过
取金样本 `trend_body/全球经验-人工智能拔尖人才培养的六大前沿趋势.md`（下称 G）vs 浅稿 `shallow_foils/主要国家教育国际战略趋势和动向.md`（下称 F），逐刀套判据：

| 刀 | 判据 | G（金样本）实测 | F（浅稿）实测 | 判定 |
|---|---|---|---|---|
| signal | 共现广度 + 证据状态①~④ + 持续性 | 多国共现 + 硬数据锚点：2.2万 AI 人才/美占46%中占11%（L21）、半个多世纪深耕（L35）、180 所（L61）→ **真趋势有据** | 逐国平铺战略文件名，从不判"算不算经验证趋势"；17 处目标承诺当事实 → **单点升格/条目堆叠** | G 已答 / F 未答 ✔ |
| driver | 驱动类型 + 归因强度①~③ + 持续性 | why-now 因果显式：拔尖培养"起始于国家危机""起始于70年代石油危机"（L43）、"涌现首先需要群众基础"（L53）、AI"关乎国家安全"（L9）→ **③深层** | why-now 驱动语全文仅 1 处命中，满篇现象无因 → **纯枚举无因/①缺失** | G 已答 / F 未答 ✔ |
| stage | 中国位置四档 + 依据 + 对策方向 + 一致性 | 逐条定位中国：落后→"加快布局"（L55）、已过度→"结构性过剩…预警"（L61）、领跑有隐忧→"徒顶虚名…补短板"（L3/L45）；敢给"刹车"反向方向 | China-stage 定位语 0 处、刹车/预警/纠偏/补配套 0 处（全 31KB）→ **镜像翻译/回避刹车档** | G 已答 / F 未答 ✔ |
| uncertainty | 把握级别 + 变数 + 对策匹配 | 区分确定性/开放性措辞："难以逆转"与"有所预警""结构性过剩"并存（L61）→ 既判趋势又留反向风险 | 17 处目标承诺（翻一番/20%/350亿）平铺当既定走向，无一处"能否兑现" → **把目标当兑现/把研判写成定论** | G 已答 / F 未答 ✔ |

四刀全部把 G 判"已答"、F 判"未答/未做扫描"，**区分得开**。第二反例 `欧美国家主要体育课程模式.md` 对 signal/driver 亦同向区分（仅模型名+提出年份、why-now 驱动语 0 处）。

### 硬门 6 · 注入接通（实跑 dry-run） —— 过
实跑：
```
cd "…/strategic_response_workflow/workflow" && python3 runner.py --report-type trend_review \
  --topic "主要国家中小学AI教育发展动向" --target-country "主要国家" \
  --strategy-domain "中小学AI教育" --notebook-name x --dry-run
```
最新 run：`runs/run-20260624-173415-670fa053/`，EXIT=0。逐项核对：
- **刀锚点存在**：`generated_prompts/pressure_judgment_mapping.md` 含 `## 本步必答逼问（须留降级扫描记录）`（L144，计 1 处）。锚点由 `runner.py:804` 生成。
- **注入接通且符映射**（module.yaml L42-44）：
  - `pressure_judgment_mapping.md` 锚点后注入 `## conventions`(L146) + `## signal`(L176) + `## driver`(L232) + `## stage`(L286)，即 `map_pressure_judgment: [signal, driver, stage]` ✔。
  - `planning.md` 锚点(L263)后注入 `## conventions`(L265) + `## stage`(L295) + `## uncertainty`(L356)，即 `plan_article: [stage, uncertainty]` ✔（stage 双挂兑现）。
  - 注：两文件 L100/L219 出现的 `## driver_analysis` 是 retrieval_type 同名巧合（module.yaml L29），位于锚点之前，非 driver 刀；不影响判定。
- **不破坏流程**：`task_state.md` 16 步全 `done`（grep `| done |` = 16），含 map_pressure_judgment / plan_article / write_draft / export_docx / archive_log。
- **无 traceback**：`run_log.md` + `logs/` 扫 traceback/error/exception 无命中。
- 刀 + conventions 已快照到 `reasoning_dna_snapshot/`（5 文件齐）。

---

## 扣分项（非阻断，建议 round_2 处理；合计 -12）

1. **(-5) signal 与 uncertainty 的"持续性"判据高度重叠，跨刀边界未划清。** signal L13/L34 的"持续性（跨年迭代/单年/一次性）"与 uncertainty L11/L31 的"把握分级（含跨年持续）"在扫描动作上几乎同形；driver L13 又有"持续性（依赖一次性事件可能衰减）"。三刀都扫"持续性"，注入到同一步（map_pressure_judgment 含 signal+driver；plan_article 含 uncertainty）时模型可能三遍重复同一扫描、或互相甩锅。driver 已用 L14"动力 vs 现象（共现是信号刀的事）"对 signal 划界、L5 注明与 cause 刀分工，做得好；但 signal↔uncertainty 的"持续性"无一句互引划界。
   修复：在 uncertainty L13"把握分级"括注后加一句"（持续性证据由 signal 刀已扫，本刀只据其结论定把握级别、不重扫共现/年份）"，或在 signal L34 注"持续性仅作信号成色用，把握度判断交 uncertainty 刀"。

2. **(-4) stage 刀"对策方向"四档与 institution_profile 的落点域未对接，存在越权出策风险。** stage L11-14 让模型直接产出"跟进/补配套/预警刹车/补短板"四类对策方向，但 runner.py 另有 `_with_institution_profile`（L811）把"机构定位与建议落点（必须遵守）"也注入同一批步骤（dry-run 已见 `institution_profile_snapshot.md` 生成）。stage 刀通篇未提"对策方向须落在机构落点域内"，可能与 institution_profile 的落点约束打架（如刀让"刹车"、profile 限定只能在教育机构可达落点提建议）。
   修复：stage L19 或红线处加一句"对策方向为研判定向，具体落点须经 institution_profile 落点域过滤，本刀只定方向不定具体动作"。

3. **(-3) driver 元问题把"中国该不该跟"写进了必答问题主干（L9），轻微侵蚀领域无关性与单刀职责。** driver L9 末"因为驱动是否持续，直接决定下一步'中国该不该跟、跟多久'"——"中国该不该跟"是 stage 刀的落点（stage L8），driver 在元问题里预支了 stage 的结论。虽不算选题词，但让 driver 的元问题绑上了"出对策"职责，与"driver 只问纵向动力与持续性"（L5 自述）自相矛盾。
   修复：driver L9 改为"…直接决定这条趋势稳不稳、能否作为长期外推的前提"（把落点交还 stage/uncertainty），保持 driver 纯归因。

---

## 总裁决
- **PASS**，得分 **88/100**。
- 六硬门：1✔ 2✔ 3✔ 4✔ 5✔ 6✔。
- 探针区分力实测四刀全部金样本"已答"/浅稿"未答"，反例锚点经两篇 foil 实证为真。
- 注入实跑接通：锚点在、映射符 module.yaml、16 步 done、无 traceback、双挂载兑现。
- 扣分三项均为可在 round_2 处理的边界/对接瑕疵，不阻断本轮通过。
