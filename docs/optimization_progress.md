# Optimization Progress

## 2026-05-25 Round 1: Capability Boundary And Auditability

### Main-Agent Decision

The first round prioritized the foundation needed for safe iterative optimization:

- Enforce the NotebookLM-only capability boundary.
- Make each run recoverable through status, ledger, progress log, and contract artifacts.
- Upgrade review outputs to ARIS-style six-state verdict artifacts with issues, required revisions, and audited input hashes.

This was chosen before prompt or material-package improvements because API-driver drift and missing run telemetry would make later automation hard to audit.

### Subagent Inputs Considered

- Capability-boundary review: found OpenAI/Anthropic API runtime support conflicted with the NotebookLM-only premise.
- Orchestration/status review: recommended `RUN_STATUS.md`, `TASK_LEDGER.json`, `progress.jsonl`, and a per-run report contract.
- Review-gate review: recommended six-state verdicts, evidence-use checks, section-contract checks, report-quality checks, and drift hashes.
- Prompt/run-spec review: identified next-round work on schema-backed prompt loading, multi-hotspot material packages, and follow-up retrieval.

### Files Changed

- `src/agent_runtime.py`
- `src/runtime_console_server.py`
- `runtime_console.html`
- `config/report_task.yaml`
- `config/report_task.real.yaml`
- `src/notebooklm_adapter.py`
- `src/progress.py`
- `src/review_gates.py`
- `src/manifest.py`
- `src/runner.py`
- `agent.md`
- `docs/codex_agent_writing_architecture.md`
- `docs/optimization_guardrails.md`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id first_aris_optimization_smoke_v2
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id first_aris_optimization_smoke_v4
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id first_aris_optimization_smoke_v6
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.real.yaml --run-id first_aris_optimization_real_v1
```

Result:

- Workflow completed in mock mode.
- Retrieval, material package, claim, kill-argument, and drift gates passed.
- Evidence-use, section-contract, and report-quality gates warned as expected.
- Run produced `RUN_STATUS.md`, `TASK_LEDGER.json`, `progress.jsonl`, `POLICY_REPORT_CONTRACT.md`, review reports, and SHA256 manifest entries.
- Runtime console API returned the NotebookLM-only schema on port `8789`.
- Invalid JSON POST now returns HTTP 400 instead of throwing a server exception.
- A synthetic bad `llm_api` config is rejected by preflight validation.
- A synthetic bad `capability_policy` with extra external calls, `llm_api: true`, and skill mutation enabled is rejected.
- A synthetic real-mode NotebookLM auth failure returns `NotebookLMPreflightGate: BLOCKED`.
- Final `RUN_STATUS.md` now preserves non-green gate status (`WARN`) instead of being overwritten by manifest `PASS`.
- Real NotebookLM CLI validation completed with `NotebookLMPreflightGate: PASS`, proving CLI path/auth/source access works.
- Real validation ended with `RUN_STATUS.md: BLOCKED` because `03_deep_dive` returned a NotebookLM `UNEXPECTED_ERROR`, retrieval completeness was incomplete, and material package fields were missing. This confirms the next optimization should address prompt/schema robustness and follow-up retrieval before deeper writing improvements.

### Post-Implementation Review Fixes

The review subagent requested changes on:

- Capability policy value validation.
- Real-mode NotebookLM auth/CLI blocking behavior.
- Final run status hiding non-green gates.
- Missing-artifact hashes being silently omitted.
- Active-task visibility during retrieval.

Implemented fixes:

- `AgentRuntime.validate()` now rejects any capability policy beyond `external_calls: [notebooklm_cli]`, `llm_api: false`, and `notebooklm_skill_mutation: false`.
- Added `NotebookLMPreflightGate`; real-mode auth/CLI hard failures now raise before retrieval.
- Manifest phase status now uses the max review verdict instead of unconditional `PASS`.
- Missing audited artifacts are recorded as `MISSING` and drift review flags them.
- Retrieval phase passes active QueryJob IDs into `RUN_STATUS.md`.

### Known Warnings

- `EvidenceUseReviewerAgent` warns because NotebookLM source/citation refs are not yet propagated into material packages.
- `SectionContractReviewerAgent` warns because section drafts do not explicitly expose every configured output-shape heading.
- `ReportQualityReviewerAgent` warns because upstream gates are not all green.
- Real mode currently blocks when NotebookLM returns a partial/error response for one query job; the workflow records this correctly but still writes a diagnostic `final_report.md` with visible `MATERIAL_NEEDED`.

### Next Round Target

Implement schema-backed query prompts that actually load `prompts/*.md`, then build material packages per hotspot with `source_refs`, `support_level`, `caution_note`, and `missing_questions`.
