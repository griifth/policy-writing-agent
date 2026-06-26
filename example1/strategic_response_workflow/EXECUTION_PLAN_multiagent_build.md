# 多 Agent 循环构建 · 详细执行方案 v2

> 目标：三路"开发↔审核"循环，并行产出 ① strategic reasoning_dna ② 动向研判体例模块 ③ experience reasoning_dna 两刀，各自迭代到收敛。
> 编排者负责：开发/审核边界、循环与通过标准、动已验证引擎的前置工作。
> 日期：2026-06-24　分支：International-Policy-Comparison-Template-Workflow

## v2 变更（纳入 Codex 审核，6 点全采纳）
1. reasoning_dna 路径统一为**体例自带**：`report_modules/<report_type>/reasoning_dna/*.md`（刀）+ 顶层 `reasoning_dna/conventions.md`（共享元格式）。与 DESIGN.md 一致。
2. 写死三路 **step→刀映射**（见 P2 / §2），不留 dev 自由发挥。
3. P3 重生成命令改为**完整命令**（runner 复用材料仍强制 topic 等）。
4. 新增 **P0**：把金样本复制进 `gold_samples/` 并写 manifest，解除"dev 限定工作流内"与"样本在工作流外"的冲突。
5. 路 A 结果门改为**三 judge 盲审中位数**判据，不被单次评分波动误杀。
6. 路 B 样本资产规范化：`source/sample.md` + `source/gold_samples/` + `source/sample_manifest.md`（标注趋势主体/对策落点/反例）。
7. 三路固定产物目录 `multiagent_build/route_{a,b,c}/round_{n}/{dev,review,decision}.md`。

---

## 0. 总体编排

```
前置（编排者亲自做）
  P0 gold_samples/ 落盘 + manifest（解除样本边界冲突）
  P1 reasoning_dna/conventions.md（三段式 + 降级红线，A/C 共用）
  P2 runner 注入 reasoning_dna：_reasoning_dna_text(step)（gated + 字节回归）+ module.yaml step→刀映射
  P3 重生成 + 三 judge 盲审脚手架（路 A 结果门）

阶段1（Workflow 三路并行，各自 dev↔review 循环到收敛）
  路A strategic reasoning_dna（intent/threat/hedge）—— 末加三 judge 盲审结果门
  路B 动向研判模块 trend_review —— 强制中国对策落点 + 混搭取样
  路C experience reasoning_dna 两刀（cause/efficacy）

阶段2（收口）跨路一致性 + 完整性总检 → 汇总报告交编排者裁决
```

依赖：路 B 不依赖前置；路 A/C 依赖 P1；路 A 还依赖 P2/P3；P3 依赖 P2（重生成需刀已注入）。

---

## 1. 前置（编排者亲自做）

### P0 · gold_samples 落盘
建 `strategic_response_workflow/gold_samples/`（gitignored，与 style_dna/raw 同类），复制并分组：
```
gold_samples/
  strategic/      中美AI人才竞争及应对策略.md / 警惕美竞争法案….md / 美英澳…长短线….md
  experience/     从国际经验中优化课后服务推动双减….md / 美英德澳…体育教师….md / 拔尖创新人才早期培养国际经验及启示.md / 国外学制发展特点 趋势及启示.md
  trend_body/     国际工程教育改革动向和趋势.md / 国际基础教育阶段学生培养目标 评价指标….md / 全球经验-人工智能拔尖人才….md / 世界教育数字化发展态势分析.md
  shallow_foils/  主要国家教育国际战略趋势和动向.md / 欧美国家主要体育课程模式.md（"条目堆叠/无对策"反面，供探针判"未答"）
  judge_set/      human.md（=中美AI人才竞争及应对策略.md）/ old_gen.md（=run-20260623-095643 最终稿）
  MANIFEST.md     每篇负责什么（金样本/趋势主体/对策落点/反例/judge）
```
dev 一律引用 `gold_samples/...` 固定路径，不出工作流。

### P1 · `reasoning_dna/conventions.md`（共享元格式）
- 三段式：`必答问题` / `什么算答到（含反例）` / `降级扫描要求`。
- 红线（v2）：每刀产物=完成降级扫描 + 留可审查取舍记录，**不强逼造否定**；审查查"有没有发生降级扫描并给结论"。

### P2 · runner 注入 reasoning_dna（碰已验证引擎，编排者做，gated）
- 新增 `_reasoning_dna_text(step)`：镜像 `_style_dna_text`，按 **module.yaml 的 `reasoning_dna_injection` 映射**从 `report_modules/<module>/reasoning_dna/<cut>.md` 读取，外加共享 `reasoning_dna/conventions.md`，拼到该判断步 prompt 末尾锚点 `## 本步必答逼问（须留降级扫描记录）`。
- **Gated**：映射缺/刀文件缺 → 空串、prompt 不变；故"现有模块尚无刀"时**字节零变化**。
- 快照：active module 的刀 + conventions → run 内 `reasoning_dna_snapshot/`（沿用现有 `_SCOPE_SOURCES` 的 reasoning_compliance 快照子目录）。
- **写死的初版 step→刀映射**（写进各 module.yaml）：

  strategic_response：
  ```yaml
  reasoning_dna_injection:
    map_pressure_judgment: [intent, threat]
    plan_article:          [intent, threat]
    build_suggestion_pool: [hedge]
    prioritize_policy_options: [hedge]
  ```
  experience_response（MVP 两刀）：
  ```yaml
  reasoning_dna_injection:
    assign_material_roles: [efficacy]
    map_pressure_judgment: [cause]
  ```
  trend_review：本批不配刀（先建模块），映射留空。
- **验收**：无刀时 dry-run 18 个 generated_prompts 与基线逐字节一致；有刀时对应步 prompt 变化（预期）。

### P3 · 重生成 + 三 judge 盲审脚手架
- 重生成（**完整命令**，复用现成中美AI人才材料）：
  ```bash
  python3 workflow/runner.py \
    --topic "美国AI人才战略布局及我国应对策略" \
    --target-country "美国" --strategy-domain "AI人才" --notebook-name "中美人才" \
    --report-type strategic_response \
    --reuse-materials-run run-20260621-153714-85b5e24e --reviewer inline
  ```
- 盲审：三篇（新生成 / `gold_samples/judge_set/human.md` / `gold_samples/judge_set/old_gen.md`）**匿名 + 随机排序**，喂 **3 个独立 judge agent**，各按评分表（总分100：结构15/战略判断20/建议体系20/证据严谨15/**语域适报15**/文风15）打分。
  - **语域适报15**：以人类金样本为语域上限锚（见 `style_dna/wiki/voice.md` + `report_modules/strategic_response/source/sample.md`）。正文判对方用陈述句、写自身用建设句，警觉只入标题/总起 → 高分；满纸无对方明示文本支撑的情绪化/军事化定性（遏制/绞杀/虹吸/钳形攻势/压制矩阵/第二战场/反守为攻…）→ 低分。**克制但证据扎实给高分，狠但定性无据给低分。**

---

## 2. 三路任务（开发边界 = 产出规格）

### 路 A · strategic reasoning_dna
- **产出**：`report_modules/strategic_response/reasoning_dna/{intent,threat,hedge}.md`（引用 `reasoning_dna/conventions.md`）+ 在该 module.yaml 写入上方 strategic 映射。
- **金样本**：`gold_samples/strategic/*`（3 篇）。**反例**：`gold_samples/shallow_foils/*`（探针用）。
- **方法**：逆向抽取"战略深稿比综述多做的推理动作"，元问题**领域无关**。
- **硬边界**：只写自己的刀文件 + 本模块 module.yaml 映射行；不改 runner、不碰其他模块。

### 路 B · 动向研判模块 `report_modules/trend_review/`
- **产出**：module.yaml + retrieval.md + prompts/全套 + templates/article_template.md + `source/{sample.md, gold_samples/, sample_manifest.md}`。
- **推理链**：`信号识别 → 趋势归纳 → 阶段研判 → 对我国的影响与对策建议`；**中国对策强制收尾**（本工作流的存在意义）。
- **骨架**：**复用现有 16 步骨架**（macro-shape 体例无关），仅把判断步 prompt 内容换成"信号→趋势研判"；不重做骨架、不改 runner。
- **取样（混搭，dev 第一步勘察后定）**：趋势主体 → `gold_samples/trend_body/*` 选 2–3 篇最成熟；**对策落点 → 移植 `gold_samples/strategic|experience/*`**（C 样本此段普遍塌，不照抄）；`source/sample_manifest.md` 标注每篇角色（趋势主体/对策落点/反例）。
- **硬边界**：只在 `report_modules/trend_review/` 内新建；不改 runner、不碰其他模块。

### 路 C · experience reasoning_dna 两刀
- **产出**：`report_modules/experience_response/reasoning_dna/{cause,efficacy}.md`（引用 conventions）+ 在该 module.yaml 写入 experience 映射。
- **金样本**：`gold_samples/experience/*`。**反例**：`gold_samples/shallow_foils/*`。
- **方法/边界**：同路 A（领域无关、逆向抽取、降级红线、不碰 runner）。

---

## 3. 三个审核 Agent（审核边界 = 标准）

### A/C 共用评审（推理 DNA）—— 硬门（全过才算通过）
1. 三段式完整（必答问题 / 什么算答到含反例 / 降级扫描要求）。
2. 元问题**领域无关**（不出现具体选题词）。
3. 含**减法/降级动作**（可检查的取舍），非"写段分析"。
4. 有**反例锚点**（明确写"什么样算糊弄/未答"）。
5. **探针区分力**：用 `gold_samples/<对应>/` 1 篇金样本 vs `gold_samples/shallow_foils/` 1 篇浅稿套这把刀 → 金样本判"已答"、浅稿判"未答"，区分得开。

### 路 A 追加 · 三 judge 盲审结果门（最终验收，非每轮）
工件级硬门全过后，跑 P3 重生成 + 三 judge 盲审，**通过须同时满足**：
- 新生成版在 **≥ 2/3 judge 排第 1**；
- 新生成版**总分中位数 > 旧版（old_gen）中位数**；
- 新生成版**任一核心维度中位数不低于人类稿对应维度 2 分以上**（即不显著差于人类稿）；
- **语域闸（新增硬门）**：新生成版**语域适报维度中位数不得低于人类金样本**——即不得靠"写得更狠"取胜；任一篇正文出现 ≥3 处无对方明示文本支撑的情绪化/军事化定性，该篇语域维度记 ≤6 且不得排第 1。
未过 → 把盲审差距点喂回 dev 精修刀再重生成（**重生成 ≤ 3 次**）。

### 路 B 评审（动向模块）—— 硬门
1. **实跑** `python3 workflow/runner.py --report-type trend_review --dry-run`（补全 topic 等）能载入、16 步跑完。
2. 推理链是"动向研判"而非经验借鉴/战略对抗。
3. **必有独立"对我国对策建议"章节**，建议由前文研判推导、不悬空；**对策成熟度对标 `gold_samples/strategic|experience`**，不是 C 样本弱收尾。
4. 趋势主体确为"归纳+研判"，非逐条堆叠。
5. 不破坏 inline 默认路径（既有体例 dry-run 仍正常）。

### 三 reviewer 通则
- 对抗式：默认挑刺，红线/结果项不确定即判**未过**；
- 必须**引证**（引样本原文或 dev 产物具体行）；
- 与对应 dev 不同实例，**每轮换新 reviewer 实例**（防橡皮图章）。

---

## 4. 循环机制与通过标准

每路：`dev 产出 → 新 reviewer 评 → 未过则 dev 按意见修订 → 再评 …`，各轮落 `multiagent_build/route_{a,b,c}/round_{n}/{dev,review,decision}.md`。

- **质量分** 0–100（锐度/可操作性/与样本贴合/不与现有 prompt 重复；路 B：体例契合/防堆叠/对策成熟度）。
- **通过** = 全部硬门通过 **且** 质量分 ≥ **85**（路 A 还须过三 judge 结果门）。
- **收敛**：通过后再迭代一轮提升 **< 3 分即停**。
- **硬上限 4 轮**；4 轮仍未过 → 停，产"未通过 + 残留清单"交编排者裁决。

---

## 5. 全局护栏

**Dev**：只新建/改自己 deliverable 的文件；**禁止改 runner.py、禁止碰其他模块或已验证产物**；样本只读 `gold_samples/...`；不用 API key、不联网；全部限定在 `strategic_response_workflow/` 内。
**Review**：对抗式、引证、不确定即判未过；路 B reviewer 必须实跑 dry-run；与 dev 不同实例、每轮换新。
**互不破坏**：任一路不得动既有 inline 路径、现有两个模块、runner 控制流（reasoning_dna 注入由编排者 P2 一次性 gated 完成）。

---

## 6. 资源 · 成本 · 上限
阶段1 ≈ 3 路 × ≤4 轮 ×（1 dev+1 review）≈ ~24 agent；+ 前置/收口 ≈ ~30 agent；+ 路 A 结果门 ≤3 次真实 DeepSeek 重生成 × 3 judge。硬上限兜底。

## 7. 执行清单
- [ ] P0 gold_samples 落盘 + MANIFEST + gitignore
- [ ] P1 conventions.md
- [ ] P2 runner 注入（gated）+ 各 module.yaml 映射 + 无刀字节回归
- [ ] P3 重生成（完整命令）+ 三 judge 盲审脚手架
- [ ] Workflow 起三路 dev↔review 循环
- [ ] 阶段2 收口 → 编排者验收 → 落盘提交

## 8. 风险与回退
| 风险 | 缓解 |
|---|---|
| P2 改 runner 破坏既有路径 | gated（无刀零变化）+ 字节回归门 |
| 刀退化成模版 | conventions 红线 + 探针区分力硬门 + 对抗式审 |
| 动向模块抄进 C 样本"无对策"病 | 对策落点强制移植金样本 + reviewer 对标金样本 |
| 结果门单评分波动 | 三 judge 中位数 + ≥2/3 排第1 + 维度下限 |
| 成本失控 | 4 轮 / ≤3 重生成 硬上限 |

## 9. 参数（默认）
通过分 **85**｜收敛阈 **3**｜单路上限 **4 轮**｜重生成上限 **3**｜动向模块名 **trend_review**
