---
name: topic-material-search
description: For a specified topic, design a fine-grained search plan and collect authoritative, traceable source material from the web (no NotebookLM), then have DeepSeek review it until it passes, producing a reusable material pack (retrieval_outputs) that the strategic_response_workflow can consume directly. Use when the user asks 给某个主题搜资料/搜集权威资料/做检索材料/生成检索方案/自己检索代替 NotebookLM/为写作工作流准备六类检索材料, or wants topic-specific web research with strict sourcing and evidence-status tagging before running an experience_response or other report workflow. Claude collects/organizes; DeepSeek reviews.
---

# Topic Material Search

Turn a specified topic into a **search plan first, then a traceable material pack** — not a pile of unsourced facts. The plan is the point: a coarse plan produces shallow material. But granularity is **never hardcoded** — the skill co-designs the plan WITH the user, asking which entities, how deep, and which angles matter (including the easy-to-miss ones: curriculum/program structure, exemplar institutions, hiring/appointment mechanics), then searches to the agreed depth.

Division of labor: **you (Claude) design the plan, collect, retrieve, organize, and write the material files; DeepSeek (DS) is a lightweight stateless reviewer.** Do not use NotebookLM.

## Operating Standard (non-negotiable)

- **Only real, traceable facts.** Never fabricate data, agencies, years, or URLs from model memory. Anti-scraping/paywalled sources → keep the URL + visible abstract, tag `[未取全文]`.
- **Every key fact carries provenance + evidence status.** Append `(机构, 文件/报告名, 年份, URL)` and one of `[已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]`.
- **Authority tiering.** Prefer T1 (official policy/law, OECD/UNESCO/World Bank, official statistics) and T2 (peer-reviewed). Demote/cut blogs, wikis, secondhand, AI-looking pages — except for purely procedural description, which must be labeled and never used for statistics.
- **Co-design the plan; don't hardcode depth.** Granularity, entities, angles, and source preferences are decided WITH the user through clarifying questions — never imposed by a fixed checklist. Propose options, ask, refine, then fan out.
- **Plan before fan-out.** Always finalize `search_plan.md` (after the user confirms) before launching collectors.

## Inputs

Required:
- `topic` — the article/research topic.

Optional (when the pack will feed a report workflow):
- `report-type` — e.g. `experience_response`; if given, read its `module.yaml` and align output filenames to that module's `retrieval_types`.
- `target-country` / `strategy-domain` / `china-response-focus` — parameters for comparative/policy topics.
- `run-id` — material run id; default `web-materials-<short-slug>`.

If `report-type` is absent, default to a generic 6-category schema (see [references/search-plan-method.md](references/search-plan-method.md)).

## Workflow

Run in order. Read the referenced file only when that step is active.

1. **Resolve target & schema.** If `report-type` is given, read `report_modules/<report-type>/module.yaml` to get the exact `retrieval_types` (these become the output filenames). Confirm the material contract and DS call from [references/environment.md](references/environment.md).

2. **Co-design the search plan with the user (core step).** Draft a candidate `category × entity` matrix, then ASK the user to set granularity and angles — which entities to cover, how deep per category, which micro-detail angles to include (curriculum / exemplar institution / appointment mechanics / effectiveness), and source/language preferences. Use AskUserQuestion for the choices that actually change the plan; propose a sensible default but let the user decide. Only after the user confirms, finalize `runs/<run-id>/search_plan.md`. Method + elicitation guide: [references/search-plan-method.md](references/search-plan-method.md).

3. **Collect (fan-out).** Launch parallel research sub-agents — one per plan partition (e.g. per country, or per category) — each running real WebSearch/WebFetch (and ai4scholar scholar tools when useful). Each must return facts with provenance + evidence status + a T1/T2 source table, under the sourcing standard: [references/sourcing-standard.md](references/sourcing-standard.md).

4. **Review micro-loop with DeepSeek.** Assemble collected material + the review standard into `/tmp/review_in.txt`, call DS, and act on its per-category verdict and gap list. Loop until DS says 通过 or 4 rounds. Standard + exact DS call: [references/review-standard.md](references/review-standard.md). Save each round's verdict as `ds_review_round<N>.md`.

5. **Land the material pack.** Write the category files into `runs/<run-id>/retrieval_outputs/` using the resolved filenames (one per retrieval type), in the standard 二段式 format (一、检索内容 / 二、相关文献). Keep `search_plan.md` and DS verdicts alongside.

6. **Hand off.** Report the pack location. If a `report-type` was given, the pack is directly reusable: `runner.py --report-type <type> ... --reuse-materials-run <run-id>` (see [references/environment.md](references/environment.md)). Offer to run it; do not run automatically unless asked.

## Quality bar (what "done" means)

- A user-confirmed `search_plan.md` exists, and the material covers it to the agreed depth (no category shallower than agreed).
- Each reference entity (e.g. each country) has ≥1 T1/T2 source; every category has substantive content.
- `effectiveness_evidence`-type categories have ≥2 facts with real evaluation data, not only intent.
- No precise-but-unsourced numbers remain; uncertain items are tagged `[未取全文]`/`[待核]`.
- DS returns 通过 (or the loop hit 4 rounds and the residual gaps are stated explicitly).

## Pitfalls this skill exists to prevent

- **Coarse angles → shallow material.** The fix is NOT to auto-force a fixed depth, but to ASK the user how deep each category needs to be and expand to entity-level sub-queries accordingly.
- **Governance/statistics bias.** Official sites yield standards and workforce numbers easily but starve micro-detail; when relevant, RAISE curriculum/program-structure, exemplar-institution, and appointment-mechanics as candidate angles for the user to opt into, and note that authoritative Chinese secondary literature (e.g. CNKI 学报) often carries that micro-detail.
- **Imposing depth the user didn't ask for.** Don't bloat the plan with angles the user declined; co-design means honoring "shallower is fine here" too.
- **Treating intent as proven practice.** Tag evidence status honestly; do not let `[意图或建议]` masquerade as `[评估数据]`.
- **Silent truncation.** If anti-scraping/paywall blocks a source, keep the URL + abstract and tag `[未取全文]`; log what was not fully retrieved.
