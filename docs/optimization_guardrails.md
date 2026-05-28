# Optimization Guardrails

This file is the main-agent anti-drift checklist for the ARIS-inspired optimization loop.

## Fixed Goal

Build a NotebookLM-backed writing agent that can produce a policy task or hotspot report from a configured topic and notebook.

## Hard Boundaries

- Only call NotebookLM and knowledge sources through the local `notebooklm` CLI.
- Do not edit or rewrite `/Users/hujingkai/.agents/skills/notebooklm/SKILL.md`.
- Do not add browser, web-search, or ARIS external reviewer calls to the report generation path.
- Do not render NotebookLM `[n]` citation markers in reader-facing report text; keep citation/source trace in JSON artifacts instead.
- OpenAI/Anthropic/DeepSeek-compatible APIs are allowed only as writing executors in `api_assisted`, and may consume only run artifacts prepared by Codex.
- Keep the automation default in `notebooklm_only` unless the round explicitly tests API-assisted writing.
- For DeepSeek-assisted writing runs, require `DEEPSEEK_API_KEY` in the process environment before starting the real workflow; do not silently fall back to Codex/local section writing.
- Keep NotebookLM Q&A serial by default (`max_concurrency: 1`) unless a round explicitly tests parallelism.
- Keep each NotebookLM `ask` bounded at no more than 240 seconds; longer-running questions should fail as structured retrieval errors and be handled by retry/follow-up logic.
- Source-specific deep dive is file-level: use `source_id/title`, not chapter-level citation validation.
- Trace refs should be notebook-scoped: carry `notebook_id` with `source_refs`, `citation_refs`, and `evidence_trace` so identical citation numbers or titles in different notebooks remain distinguishable.
- Source-specific deep dive breadth should default to all resolved source candidates from base retrieval/citation sweep; this does not mean all files in the NotebookLM notebook.
- Citation sweep must ask for distinct `source_candidates`; parser should prefer embedded `citations.title` when present and use top-level `references` only as fallback, because real CLI references can collapse multiple title citations to one source id.
- Do not broaden the project into a generic agent framework, LaTeX paper submission workflow, or ARIS clone.
- Keep each subagent boundary explicit: planning, NotebookLM retrieval, material packaging, matrix building, section planning, section writing, review, assembly, integration.

## Main Agent Role

- Set the round objective.
- Dispatch bounded subagent reviews.
- Decide which proposals fit the report-writing goal.
- Assign disjoint implementation scopes.
- Review validation results and record remaining gaps.
- Stop or redirect work when a proposal violates the hard boundaries.

## Required Per-Round Record

Every optimization round must update `docs/optimization_progress.md` with:

- ARIS capability or pattern reviewed.
- Subagent proposals considered.
- Main-agent adaptation decision.
- Files changed.
- Validation commands and verdicts.
- Known warnings and next round target.

## Current Priority Queue

1. Done: load prompt files into QueryJobs and make prompts schema-backed.
2. Done: propagate NotebookLM source/citation refs into material packages and claim rows.
3. Done: add all-source citation sweep plus source-specific `notebooklm ask -s <source_id>` deep dive.
4. Done: adapt source-specific deep dive into four writing lanes: hotspot rationale, core material, comparison, and impact.
5. Done: make section drafts explicitly satisfy section contract output shapes.
6. Done: run bounded real-mode validation for citation sweep -> source candidate -> four source lanes; fix `references.citation_number` parsing.
7. Done: set source deep dive breadth to all resolved source candidates, with `0` reserved for disabling the loop.
8. Build one material package per hotspot only when the report target is a top-k hotspot inventory or comparison report.
9. Add one bounded follow-up retrieval loop for missing material fields.

## Current Residual Warnings

- Evidence refs: first-pass source/citation propagation is wired; bounded real-mode smoke exposed and fixed `references.citation_number` parsing.
- Citation display: mock workflow now strips visible `[n]` markers from final report while preserving trace artifacts.
- Source-specific deep dive: bounded real-mode smoke validated one source candidate and all four `-s <source_id>` writing lanes; the education-evaluation real query run also completed one source with four lanes.
- Source breadth: current mock and real configs use `source_deep_dive_limit: "all"`; source-lane calls scale as resolved source candidates times four lanes.
- Real rerun: `education_evaluation_ai_real_rerun_20260527` verified 3 source candidates and 12 source-lane jobs in live real mode.
- Lane materials: material packages preserve lane buckets, but current report drafting does not yet explicitly consume every bucket in a section-specific way.
- Section contracts: generated drafts now render configured output-shape items as visible headings in mock mode.
- Source labels: real CLI `references` may omit title; source ID is enough for `-s`, and refs now carry `notebook_id`, but report-facing title enrichment should keep using `notebooklm_sources.json`.
- Section wording: real report drafts can still trigger `ClaimAuditAgent` when medium-support claims appear near strong policy language.
- Markdown rendering: section drafts can render list-valued NotebookLM fields awkwardly; normalize list display before polished output.
- Appendix source refs: package-level source refs can make claim source labels too verbose; keep trace in artifacts but summarize labels in reader-facing appendices.
- Report quality: mock-mode report quality is green after section-contract explicitness; the education-evaluation real run completed with WARN due to claim wording.
- DeepSeek run: `education_evaluation_ai_deepseek_20260527_retry2` completed end-to-end with DeepSeek section writing and produced `final_report.md`, but the run status remains `BLOCKED` because one base NotebookLM query returned ERROR and `RetrievalCompletenessGate` stayed non-green.
- API section-writing prompts should be compact and artifact-bound; do not pass raw NotebookLM responses, full evidence traces, or full citation arrays into DeepSeek when a section only needs curated material fields.
- DeepSeek material compression is allowed only after Codex has built local artifacts; it must consume bounded chunks, preserve `source_refs` locally, keep `citation_refs`/`evidence_trace` out of API compression prompts, and write `compression_manifest.json` plus `compression_errors.json`.
- Compression inputs must strip trace-heavy fields before API calls and fallback paths: `citation_refs`, `evidence_trace`, `source_refs`, raw responses, parsed response blobs, and other NotebookLM trace payloads stay in artifacts, not in DeepSeek prompts.
- Section writing prompts must apply a final hard size cap to section slices even when upstream compression is marked PASS.
- Final report abstracts must summarize the generated report content; they must not describe the agent workflow, retrieval pipeline, material package construction, or section-contract execution process.
- DeepSeek `AbstractComposerAgent` may run only after section drafts are complete, and must consume only the generated section text. It must not receive raw NotebookLM traces, source refs, material-package internals, or external knowledge.
- OpenAI-compatible API calls should retry bounded transient transport failures such as `IncompleteRead`, timeout, connection reset, and broken pipe; HTTP auth/config errors should still fail visibly.
- If a compression chunk fails after bounded retries, fall back to deterministic local compression rather than blocking report assembly, and surface the fallback in compression artifacts.
- Compressed DeepSeek real rerun `education_evaluation_ai_deepseek_compressed_20260528` produced a report with compression PASS and no visible `[n]` citation markers, but retrieval completeness stayed `BLOCKED` because four NotebookLM query jobs returned structured errors.
