# Optimization Guardrails

This file is the main-agent anti-drift checklist for the ARIS-inspired optimization loop.

## Fixed Goal

Build a NotebookLM-backed writing agent that can produce a policy task or hotspot report from a configured topic and notebook.

## Hard Boundaries

- Only call NotebookLM and knowledge sources through the local `notebooklm` CLI.
- Do not edit or rewrite `/Users/hujingkai/.agents/skills/notebooklm/SKILL.md`.
- Do not add browser, web-search, or ARIS external reviewer calls to the report generation path.
- OpenAI/Anthropic/DeepSeek-compatible APIs are allowed only as writing executors in `api_assisted`, and may consume only run artifacts prepared by Codex.
- Keep the automation default in `notebooklm_only` unless the round explicitly tests API-assisted writing.
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

1. Load prompt files into QueryJobs and make prompts schema-backed.
2. Build one material package per hotspot instead of one hardcoded package.
3. Propagate NotebookLM source/citation refs into material packages and claim rows.
4. Add one bounded follow-up retrieval loop for missing material fields.
5. Make section drafts explicitly satisfy section contract output shapes.
