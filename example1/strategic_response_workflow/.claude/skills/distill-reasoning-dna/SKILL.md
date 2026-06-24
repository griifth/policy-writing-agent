---
name: distill-reasoning-dna
description: 为某个体例（report_modules/<体例>）蒸馏 reasoning_dna 判断"刀"的标准流程——用 dev↔review 对抗循环从金样本逆向抽取"逼问刀"，写盘、接进 runner 注入、验证到过线。Whenever you need to build or add reasoning_dna cuts for a report genre/体例 in this policy-writing workflow（新建体例后给它配刀、给已有体例补刀、想用"判断纪律"提升某体例的推理深度、或复现路A/C/D那套蒸馏），use this skill. 触发词：reasoning_dna、蒸馏刀、给体例配刀/补刀、判断纪律、dev↔review 循环建刀。
---

# 蒸馏 reasoning_dna（为体例建判断"刀"）

## 这是什么
reasoning_dna 的一把"刀" = 一刀**逼问**：逼写作模型在某个角度想透、并留下**可检查的取舍记录**（约束"想到哪几层"，不规定文体）。一个体例的几把刀，运行时被 gated 注入到该体例的判断/构思步，让产出更深、可审。

本 skill 把"为一个体例蒸馏出合格刀"的流程固化下来——核心是 **dev 写刀 ↔ 独立 reviewer 对抗审** 的循环，**从金样本逆向抽取、不凭空写**。

**产物**：`report_modules/<体例>/reasoning_dna/<刀>.md`（每刀严格三段式）+ 该模块 `module.yaml` 的 `reasoning_dna_injection` 映射 + 各轮记录。

## 权威与已有范例（先读）
- 刀的**元格式（必须遵守）**：`reasoning_dna/conventions.md`（三段式 + 降级红线）。
- 已建三套刀做参照（勿照抄内容，学结构）：`report_modules/strategic_response/reasoning_dna/`（intent/threat/hedge）、`report_modules/experience_response/reasoning_dna/`（cause/efficacy）、`report_modules/trend_review/reasoning_dna/`（signal/driver/stage/uncertainty）。
- 注入机制：runner 的 `_reasoning_dna_text` / `_with_reasoning_dna`，按 `module.yaml` 的 `reasoning_dna_injection`（step→刀）拼到判断步末尾锚点。
- 可复用的循环脚本模板：本 skill 的 `scripts/distill_loop_template.js`（用 Workflow 工具跑）。

## 前提（开跑前确认，缺则先补）
1. **conventions.md 在**：`reasoning_dna/conventions.md` 存在（元格式 + 降级红线）。无则先写。
2. **金样本 + 反例已落盘工作流内**：`gold_samples/<该体例的正样本>/`（深稿，逆向抽取用）+ `gold_samples/shallow_foils/`（浅综述/堆叠稿，探针判"未答"用）。样本须在 `strategic_response_workflow/` 内（dev 不出工作流）。
3. **注入机制已接通**：runner 有 `_reasoning_dna_text` 注入 + 该 `module.yaml` 有 `reasoning_dna_injection` 字段位（值可先空，gated 零注入）。无则先按已有体例补这段引擎代码（这步**碰已验证引擎，由编排者亲自做并字节回归**，不交 dev）。

## 流程：dev↔review 循环（每路一个体例）

用 **Workflow 工具**跑（模板见 `scripts/distill_loop_template.js`），每轮 `dev 写刀 → 新 reviewer 审 → 不过则按反馈改 → 再审`，至多 **4 轮**，过线即停。

### dev agent（每轮）
- **边界**：只写 `report_modules/<体例>/reasoning_dna/<刀>.md` + 本模块 `module.yaml` 的注入映射行；**禁止改 runner、禁止碰其他模块**；样本只读 `gold_samples/...`；不用 API key、不联网；全绝对路径。
- **方法**：先读 conventions；**完整读金样本**，逆向抽取"深稿比浅综述多做的推理动作"；元问题写成**领域无关**（不出现具体选题词，如"AI人才""校园餐"）；每刀严格三段式 + 降级红线。
- **定刀数**：先勘察金样本再定 2–4 把刀（够覆盖该体例的核心推理动作即可）。
- **写注入映射**：step 用任务 id（assign_material_roles / map_pressure_judgment / plan_article / build_suggestion_pool / prioritize_policy_options），把刀挂到最自然发力的判断步。
- 写开发记录 `multiagent_build/route_<x>/round_<n>/dev.md`。

### review agent（每轮，与 dev 不同实例、每轮换新）
对抗式：默认挑刺，不确定即判未过，必须**引证**。返回结构化 `{pass, score, hardGatesFailed[], feedback, evidence}`。

**硬门（全过才算 pass）**：
1. **三段式完整**：每刀含 必答问题 / 什么算答到了（含反例）/ 降级扫描要求。
2. **元问题领域无关**：不出现具体选题词。
3. **含减法/降级动作**：产物是"扫描+结论+理由"，不是"写段分析"。
4. **反例锚点**：每刀明确写"什么样算糊弄/未答"。
5. **探针区分力**：亲自拿 1 篇金样本 vs 1 篇 shallow_foil，用每把刀判据各判一次——金样本"已答"、浅稿"未答"，区分得开（evidence 写依据）。
6. **注入接通**：实跑该体例 dry-run，确认刀被注入且不破坏流程（见"验证"）。

**质量分**（0–100）：锐度 / 可操作性 / 与金样本贴合 / 不与现有判断 prompt 重复。

### 过线与收敛标准
- **通过** = 全部硬门通过 **且** 质量分 **≥ 85**。
- **硬上限 4 轮**；4 轮仍不过 → 停，产"未通过 + 残留清单"交人裁决，不死循环。
- 各轮落 `multiagent_build/route_<x>/round_<n>/{dev,review,decision}.md`（decision 由编排者据 verdict 补写）。

## 验证（接通 + 真生效）
过线后亲自验证一遍：
```
cd strategic_response_workflow/workflow
python3 runner.py --report-type <体例> --topic "测试选题" --target-country x --strategy-domain y --notebook-name z --dry-run
```
检查最新 `runs/<id>/`：
- `generated_prompts/` 中对应判断步含锚点 `本步必答逼问`，且含 `## <刀名>` 内容；
- `reasoning_dna_snapshot/` 有刀 + conventions；
- `task_state.md` 16 步全 done、`logs/` 无 traceback。
并确认**其它体例 dry-run 仍正常**（不破坏既有路径）。

## （可选）结果门：刀真能让文章更好吗
对值得的体例，可加一道结果门（参考路 A）：装刀后用现成材料**真实重生成一篇该体例选题**，3 个独立 judge **盲审**对比"装刀版 vs 未装刀版 vs 人类稿"，装刀版须 ≥2/3 排第1 且总分中位数 > 未装刀版。打不过 → 把盲审差距喂回 dev 精修（重生成 ≤3 次）。

## 用 Workflow 跑
把 `scripts/distill_loop_template.js` 复制改参（BASE、体例、cuts、金样本路径、step→刀建议），用 Workflow 工具运行。它已内置 VERDICT schema、硬门、4 轮循环、过线判定。

## 常见失败模式（写刀时主动规避）
- 刀退化成**模版**（只剩小节名、无降级动作）→ 守住 conventions 红线"必须做降级扫描留痕"。
- 元问题**绑定选题**（带"AI人才"等词）→ 抽象成元问题。
- 刀之间**重复扫描**同一维度（如都扫"持续性"）→ 加跨刀边界说明。
- 刀**抢 institution_profile 的活**（直接给落点域对策）→ 刀只给"判断方向"，落点交 institution_profile。
