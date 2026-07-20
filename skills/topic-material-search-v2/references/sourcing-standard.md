# Sourcing Standard (for collectors and for the material files)

## Sub-agent collection brief (give this to each research sub-agent)

Each collector runs real WebSearch/WebFetch (and ai4scholar scholar tools when useful) for its assigned plan partition, and returns data only — its final message IS the data, no preamble.

Hard rules to embed in every collector prompt:
- ONLY report facts actually found via search and traceable to a real source. DO NOT fabricate data, agencies, years, or URLs from memory.
- Prioritize T1 (government/ministry, official agencies & statistics, OECD/UNESCO/World Bank) and T2 (peer-reviewed). Reject blogs/wikis/secondhand; tier-3 procedural pages allowed only to describe process, never for statistics, and must be labeled.
- For EACH key fact append `(机构, 文件/报告名, 年份, URL)` + evidence status `[已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]`.
- Paywalled/anti-scraping → keep source URL + visible abstract, tag `[未取全文]`.
- Verify the most important URLs by actually fetching them.
- Honor the micro-detail angles from the plan (curriculum/exemplar institution/appointment mechanics): return concrete numbers (modules, credits, weeks, salary, registration cycle), not headlines.

Return format per partition: for each angle, a bullet list of facts each ending with the parenthetical source + evidence tag; then a SOURCES table: `Title | Org | Year | Type(法规/报告/统计/研究) | Tier(T1/T2) | URL`.

## Material file format (one file per retrieval type)

Write each `runs/<run-id>/retrieval_outputs/<category>.md` as:

```
一、检索内容

<按要点组织的事实；每条关键事实后用括号标出处：(机构, 文件/报告名, 年份, URL)，
 并标注证据状态：[已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]。
 按实体（国别/机构）分小节组织；每个类别保留 ≥1 条微观细节（课程/学分/院校/聘任流程）。>

二、相关文献

- <标题> | <机构> | <年份> | <类型:法规/报告/统计/研究> | <权威分级 T1/T2> | <URL>
- ...
```

Regroup the per-partition agent findings BY category into these files (collectors return per-entity; files are per-category). Only write facts that are sourced; drop or tag `[待核]` anything that could not be traced to a real URL.
