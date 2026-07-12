# Search Plan Method (the core of this skill)

The search plan is what fixes the coarse-grained failure — but it is **co-designed with the user, not auto-generated and not hardcoded**. The skill drafts a candidate matrix, asks the user to set entities/depth/angles, and only then finalizes `runs/<run-id>/search_plan.md`. Granularity is a decision the user owns; the skill's job is to propose good options and make the trade-offs visible.

## 1. Pick the category schema (rows of the plan)

- If a `report-type` is given: rows = that module's `retrieval_types` (read `report_modules/<report-type>/module.yaml`). For `experience_response` they are:
  `practice_background, key_practices, enabling_conditions, effectiveness_evidence, china_status_and_gaps, adaptation_evidence`.
- Else, default generic 6-category schema:
  1. `background` — problem context & overall situation
  2. `key_practices` — concrete practices/instruments
  3. `enabling_conditions` — causes, institutional preconditions
  4. `effectiveness_evidence` — implementation effects & effectiveness (with evidence status)
  5. `china_status_and_gaps` — China status, shortcomings, constraints (for borrowing topics)
  6. `adaptation_evidence` — transferability & local-adaptation basis

The output filenames MUST equal these row keys (`<key>.md`).

## 2. Pick the entities (columns of the plan)

Entities are the axes you must cover per category. For a comparative policy topic: the reference countries/regions + China. For a single-system topic: the key actors/instruments/levels. The plan is the matrix `category × entity`, each cell holding 1–3 concrete sub-queries.

## 3. Decompose each cell into granular sub-queries

For each `category × entity` cell, write concrete queries that name the entity, the instrument, and the artifact you want — not headline phrases.

- Bad (coarse): `Germany PE teacher policy`
- Good (granular): `Sport Lehramt Studienordnung Modulhandbuch Leistungspunkte`, `Referendariat Sport Dauer Bundesland`, `Sportlehrer Verbeamtung Einstellung Quereinstieg Statistik`

## 4. Propose micro-detail angles and ASK the user (co-design granularity)

Do not force angles in. Instead, present a candidate menu and let the user choose depth per category. Use AskUserQuestion (multi-select) for the choices that actually change the plan. Typical menu when the topic involves training/qualification/employment of a profession (adapt wording to the domain):

- **培养方案 / 课程结构**: curriculum, course modules, credit hours, signature pedagogy, practicum length.
- **典型院校 / 旗舰项目**: a named exemplar institution/program with concrete numbers.
- **聘任 / 准入机制**: hiring route, qualification/registration, certification exam, salary/contract type, tenure/establishment equivalent.
- **有效性 / 评估**: evaluation/RCT/audit/official statistics (recommend keeping this — it is what makes later judgments defensible).

Questions worth asking the user before finalizing:
1. Which entities to cover, and is any entity primary vs. context-only?
2. For each category, how deep — headline overview, or micro-detail (which of the angles above)?
3. Source/language preference — primary-only, or allow authoritative secondary literature (e.g. CNKI 学报) for micro-detail?
4. Any must-include sources, institutions, or time window; anything explicitly out of scope?

Record the user's answers as the plan's agreed granularity. If the user wants a category kept shallow, honor that — do not pad it.

## 5. Set sourcing rules per angle

In the plan, annotate each angle with: preferred source tier (T1/T2), language preference, and whether authoritative secondary literature is allowed. Rule of thumb:
- Standards/law/statistics/effectiveness → T1/T2 primary, original language or official English.
- Curriculum/program micro-detail → university program pages allowed; **authoritative Chinese secondary literature (CNKI 学报、教育部直属机构报告) explicitly allowed** here, because it pre-digests program detail that primary English sources bury.

## 6. Plan template (write this to search_plan.md)

```
# 检索方案：<topic>
- 运行ID：<run-id>    报告类型：<report-type 或 generic>
- 实体（覆盖轴）：<entity1, entity2, ... , 中国>
- 类别（= 输出文件名）：<category keys>

## 矩阵（category × entity → 子查询 + 来源层级 + 语言/二手许可）
### <category 1>
- <entity A>：
  - 子查询：<q1>; <q2>
  - 微观角度：<培养方案/典型院校/聘任机制 中至少一条>
  - 来源：T1/T2；语言：<原文/英文/中文二手许可>
- <entity B>： ...
### <category 2>
...

## 与用户共同确定的颗粒度（记录用户决定，不是写死的清单）
- 实体覆盖与主次：<用户决定>
- 各类别深度：<逐类记录：概览 / 微观（含哪些角度）>
- 来源与语言：<是否允许中文二手文献承担微观角度>
- 必含/排除项：<用户指定>

## 分工与并发
- 每个分区（按实体或按类别）派 1 个研究子代理并行执行。
- 子代理交付：事实清单（每条挂出处+证据状态）+ T1/T2 来源表。
```

## 7. Checkpoint (a dialogue, not a one-way show)

The plan is co-created: draft → ask → revise → confirm. Do not fan out until the user confirms the matrix and the agreed granularity. If the user changes entities/angles/depth at any point, update `search_plan.md` first. "Shallower is fine here" is a valid answer — record it and honor it.
