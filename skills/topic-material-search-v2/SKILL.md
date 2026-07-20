---
name: topic-material-search-v2
description: >-
  For a specified topic, either (A) run SCOUT MODE — a fast, minutes-level reconnaissance of a dozen
  authoritative leads that produces a one-page 态势速览 (situation brief: 谁动了什么/分歧轴/反直觉信号与缺口/候选研究问题)
  to help a writer point-select a 方向书 — or (B) run FULL MODE — the original fine-grained search plan +
  traceable material pack (retrieval_outputs) with DeepSeek review that strategic_response_workflow can consume.
  Scout mode is invoked by report-clarify-v2 触点一定向; full mode runs after the 方向书 is signed and can take
  the 方向书 as input (倾向箭头 weights the search, 禁区 prunes, scout results seed dedup). Use when the user asks
  给某个主题搜资料/侦察态势/做态势速览/生成检索方案/为写作工作流准备检索材料.
  ⚠️沙箱版：属 712测试；本沙箱只测 SCOUT MODE（全量模式沿用原逻辑，方向书入参为新增说明）。
---

# Topic Material Search v2（双模式：侦察 / 全量）

> 路径约定：本文件内相对路径一律以 direction_workflow/ 为根。

两个速度档，**同一套溯源纪律**：

- **侦察模式（SCOUT MODE）· 新增** —— 为**定向点选**服务：十几条权威线索、分钟级、不走完整复审循环，产出一页纸**态势速览**。由 `report-clarify-v2` 触点一调用。
- **全量模式（FULL MODE）· 原逻辑保留** —— 为**写作供料**服务：co-design 检索方案 → 分区/分类 fan-out → DS 复审循环 → 可复用料包（retrieval_outputs）。方向书签字后主力上，并可吃**方向书入参**。

Do not use NotebookLM. 仓库根 `<ROOT>` ＝ 本包 direction_workflow/ 的上一级目录（路径可能含空格，命令加引号）。本沙箱 `<ROOT>/712测试`（历史沙箱目录，仅原机存在；整包移植后不适用）。

## 与原版 topic-material-search 的差异

| 维度 | 原 topic-material-search | 本 v2 |
|---|---|---|
| 模式 | 仅全量模式 | **新增侦察模式**；全量模式原逻辑不变 |
| 服务对象 | 定题之后的写作供料 | 侦察＝定向前的点选辅料；全量＝写作供料 |
| 产出 | retrieval_outputs 料包 + DS 复审 | 侦察＝态势速览一页纸（无料包、无 DS 循环）；全量＝原料包 |
| 入参 | topic + report-type 等 | 全量模式**新增可选方向书入参**：倾向箭头加权 / 禁区剪枝 / 侦察结果作种子 |

---

# 模式 A：侦察模式（SCOUT MODE）

> 目的：给撰写者一页"能对着点方向"的态势速览，不是给写作供料。**反应比生成便宜**——人对着东西挑方向只要几秒。

## Scout 操作纪律（不可违背）

- **分钟级、十几条线索、不走复审循环**：不建 `retrieval_outputs/`、不跑 DS 审校、不做跨类去重、不做 co-design 方案问答。一趟侦察直出速览。
- **溯源不打折**：每条硬事实仍带 `(机构, 文件/报告名, 年份, URL)` + 证据状态 `[已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]`，T1（官方/国际组织/官方统计）优先，T2 次之。侦察允许更浅的覆盖，但**不允许更松的溯源**。
- **反锚定焊死（速览铁律）**：分歧轴每根两端都摆、中立对称，全页禁止倾向性措辞（不出现"应该/更优/正确/落后/领先"等把撰写者往一端引的词）。每栏留逃生口"以上都不是，我关心的是＿＿"。
- **无联网权限**：全页标 `[SIMULATED]`，据模型常识构造合理态势供流程测试，交付时显著告知"侦察为模拟，真实检索待补测"。

## Scout 流程（一趟，分钟级）

1. **接主题**：入参仅需 `topic`（可选 `notes` 传用户已知偏好）。不做 co-design 问答（那是全量模式的事）。
2. **一波检索（十几条）**：围绕主题 WebSearch/WebFetch 打 3–5 组查询——(a) 最新官方文件/纲要/规划（近 2 年）(b) 国际组织/权威统计 (c) **各方争论点/不同主张**（分歧轴原料）(d) 反直觉信号/被质疑的数据。可直接自己搜，或派 1 个 scout 子 agent 快采；**不分区 fan-out、不派 organizer**。
3. **凝练成态势速览四栏**（按 `templates/态势速览模板.md`）：
   - ① **最近谁动了什么**：3–5 条硬事实，每条带源 + 证据状态。
   - ② **分歧轴**：从检索到的不同主张里抽 2–4 根轴，每轴左右端中立对称陈述——两端即候选倾向箭头。
   - ③ **反直觉信号与数据缺口**：与主流叙事相反的信号；决策需要却公开查不到的空白。
   - ④ **候选研究问题**：3–5 个，判断句/研判任务（非名词短语），各标贴合的用途类型（借鉴/趋势研判/差距追赶）。
   - 每栏末尾逃生口。
4. **交付**：把态势速览一页纸交回 `report-clarify-v2` 触点一（或直接给用户），供对着点选方向书。侦察结果一并留存，可作全量模式的**种子**（防重复检索）。

## Scout 质量线（"侦察完成"的判据）

- 至少 3 条 T1/T2 硬事实带真实来源与证据状态（未联网则 `[SIMULATED]` 且已告知）。
- 至少 2 根分歧轴，每根两端中立对称、无倾向性措辞。
- 候选研究问题均为判断句/研判任务，非名词短语，各挂用途类型。
- 四栏逃生口齐全。**未达线不硬凑**：线索不足时如实写"公开线索不足"，列出已有的。

---

# 模式 B：全量模式（FULL MODE）· 原逻辑保留 + 方向书入参

Turn a specified topic into a **search plan first, then a traceable material pack** — not a pile of unsourced facts. 与原 skill 完全一致，仅新增"方向书入参"一节。

Division of labor — **every step names its executor, no double-assignment**:
- **Orchestrating agent (you)** — design the plan, dispatch sub-agents (collectors + organizers), coordinate cross-category dedup, run the DS review loop, finalize & hand off. You orchestrate; you do NOT do the bulk web collection or the per-category consolidation writing yourself.
- **Collector sub-agents** (fan-out, one per plan partition) — run real WebSearch/WebFetch, return sourced fragments to you.
- **Organizer sub-agents** (fan-out, one per `retrieval_type`/category) — consolidate the fragments for their own category, dedup within it, write that category's 二段式 material file.
- **DeepSeek (DS)** — lightweight stateless reviewer.

## Operating Standard (non-negotiable)

- **Only real, traceable facts.** Never fabricate data, agencies, years, or URLs. Anti-scraping/paywalled → keep URL + visible abstract, tag `[未取全文]`.
- **Every key fact carries provenance + evidence status.** Append `(机构, 文件/报告名, 年份, URL)` + one of `[已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]`.
- **Authority tiering.** Prefer T1 (official policy/law, OECD/UNESCO/World Bank, official statistics) and T2 (peer-reviewed). Demote/cut blogs, wikis, secondhand, AI-looking pages.
- **Co-design the plan; don't hardcode depth.** Granularity, entities, angles, and source preferences decided WITH the user through clarifying questions.
- **Plan before fan-out.** Always finalize `search_plan.md` (after the user confirms) before launching collectors.

## Inputs (Full Mode)

Required:
- `topic` — the article/research topic.

Optional (when the pack will feed a report workflow):
- `report-type` — e.g. `experience_response`; if given, read its `module.yaml` and align output filenames to that module's `retrieval_types`.
- `target-country` / `strategy-domain` / `china-response-focus`.
- `run-id` — material run id; default `web-materials-<short-slug>`.

**Optional 方向书入参（v2 新增）** —— 当上游 `report-clarify-v2` 已产出方向书时，把它传进来收窄检索：
- **倾向箭头 → 检索加权**：箭头指向哪端，就给对应查询/实体/角度更高优先级与更深子查询（如箭头=🔴警惕，则加权"风险/挑战/负面评估"类证据；箭头=🟢借鉴，则加权"有效性/可迁移条件"类证据）。加权只调**顺序与深度**，不改溯源纪律，也不剪掉反证——反证栏永远保留。
- **禁区 → 剪枝**：方向书禁区里点名的话题/立场/国别/提法，不作为检索分区展开；若某禁区项与主线强相关无法完全剪除，保留但标注"触禁区，仅供背景，写作勿展开"。
- **侦察结果 → 种子 + 防重复**：把 scout mode 已找到的线索作为已收录种子（进 dedup key list），全量检索不重复打这些查询，只在其上加深与补全。

## Workflow (Full Mode — 原七步不变)

Run in order. Read the referenced file only when that step is active.

1. **Resolve target & schema.** 若给 `report-type`，读 `report_modules/<report-type>/module.yaml` 取 `retrieval_types`（＝输出文件名）。Confirm material contract & DS call: `skills/topic-material-search-v2/references/environment.md`。**若带方向书入参**：先据禁区剪枝候选实体/角度，据倾向箭头标注加权项，把侦察线索登记进 dedup key list。
2. **Co-design the search plan with the user.** Draft `category × entity` matrix, ASK the user to set granularity/angles (which entities, how deep per category, which micro-detail angles, source/language prefs). Only after confirm, finalize `runs/<run-id>/search_plan.md`. Method: `skills/topic-material-search-v2/references/search-plan-method.md`。方向书入参已定的项作为默认带入，仍由用户可改。
3. **Collect (fan-out by partition).** Launch parallel collector sub-agents — one per plan partition — each running real WebSearch/WebFetch, returning **sourced fragments**. Sourcing standard: `skills/topic-material-search-v2/references/sourcing-standard.md`。侦察种子不重复检索。
4. **Organize (fan-out by category).** One organizer per `retrieval_type`/category, given all relevant fragments + shared **dedup key list**（含侦察种子）. Each writes `runs/<run-id>/retrieval_outputs/<type>.md` in 二段式. **Cross-category dedup is YOUR job (barrier)** after all organizers return.
5. **Review micro-loop with DeepSeek.** Assemble organized pack + review standard into `/tmp/review_in.txt`, call DS, act on per-category verdict/gaps by **re-dispatching sub-agents** (not hand-patching). Loop until 通过 or 4 rounds. Standard + exact call: `skills/topic-material-search-v2/references/review-standard.md`. Save `ds_review_round<N>.md`.
6. **Finalize the pack.** Verify every `retrieval_type` file exists, non-shallow, cross-category dedup done. Keep `search_plan.md` and DS verdicts alongside.
7. **Hand off.** Report pack location. If `report-type` given: `runner.py --report-type <type> ... --reuse-materials-run <run-id>` (see environment.md). Offer to run; don't run automatically unless asked.

## Quality bar — Full Mode (what "done" means)

- User-confirmed `search_plan.md` exists; material covers it to agreed depth.
- Each reference entity has ≥1 T1/T2 source; every category substantive.
- `effectiveness_evidence`-type categories have ≥2 facts with real evaluation data.
- No precise-but-unsourced numbers; uncertain items tagged `[未取全文]`/`[待核]`.
- DS returns 通过 (or 4 rounds hit, residual gaps stated).
- Every `retrieval_type` has its own 二段式 file; **no fact duplicated across category files**.
- **若带方向书入参**：禁区项未被展开成检索分区；倾向箭头加权未导致反证栏被剪（诚实供货，反证必留）。

## Pitfalls this skill exists to prevent

- **Coarse angles → shallow material.** Fix: ASK the user how deep each category needs, expand to entity-level sub-queries.
- **Governance/statistics bias.** RAISE curriculum/program-structure, exemplar-institution, appointment-mechanics as candidate angles; note authoritative Chinese secondary literature (CNKI 学报) often carries micro-detail.
- **Imposing depth the user didn't ask for.** Honor "shallower is fine here".
- **Treating intent as proven practice.** Tag evidence status honestly.
- **Silent truncation.** Anti-scraping/paywall → keep URL + abstract, tag `[未取全文]`, log what was not retrieved.
- **Parallel organizers double-count.** Give every organizer a shared 已收录 key list up front; run one orchestrator-side cross-category dedup pass after they return.
- **（v2）倾向箭头加权变成命题裁剪。** 加权只调顺序与深度，**反证栏永远保留**——诚实供货是助手与谄媚机的分界（设计记录 §七）。
