# Policy Writing Agent

This directory contains the executable MVP for the NotebookLM-backed policy hotspot writing agent.

## MVP Scope

The MVP turns a configured policy writing task into a complete run directory:

```text
task_spec.json
query_jobs.json
query_results/*.json
material_packages/*.json
policy_claim_material_matrix.json
POLICY_REPORT_PLAN.md
section_drafts/*.md
review_reports/*.json
final_report.md
MANIFEST.md
workflow_state.json
```

NotebookLM owns source traceability. This agent owns task decomposition, query planning, material package assembly, section contracts, draft composition, and lightweight review gates.

## Run

```bash
cd policy-writing-agent
python3 src/runner.py --task config/report_task.yaml
```

The default config uses `mock` mode so the workflow can run without NotebookLM credentials. Set `execution.mode: real` and provide a valid `notebook_id` to use the NotebookLM CLI through `NotebookLMAdapter`.

## Runtime Console

Start the local console to inspect and edit the NotebookLM-only runtime settings through a browser:

```bash
python3 src/runtime_console_server.py --host 127.0.0.1 --port 8787
```

Open `http://127.0.0.1:8787/`. The console can switch between mock/real configs, show the NotebookLM-only capability boundary, inspect local agent routing, and save YAML. It does not configure OpenAI or Anthropic providers.

## Agent Runtime

The writing workflow is constrained to local orchestration plus NotebookLM CLI retrieval:

```yaml
agent_runtime:
  mode: "local"
  default_driver: "local"
  capability_policy:
    external_calls:
      - "notebooklm_cli"
    llm_api: false
    notebooklm_skill_mutation: false
```

Every agent uses `driver: "local"`. If a config reintroduces `llm_api`, provider defaults, or per-agent API blocks, preflight fails before the workflow runs.

```yaml
agent_runtime:
  agents:
    SectionComposerAgent:
      driver: "local"
```

Every run writes `agent_runtime.json` and `agent_runtime_validation.json` so the capability policy and driver choices are auditable.

## Module Boundaries

```text
agent_runtime.py         local-only agent driver config and capability policy
query_planner.py          ReportTask -> QueryJob[]
notebooklm_adapter.py     QueryJob -> QueryResult
material_pack_builder.py  QueryResult[] -> MaterialPackage[]
matrix_builder.py         MaterialPackage[] -> matrices
section_planner.py        matrices + contracts -> POLICY_REPORT_PLAN.md
section_composer.py       materials + claims -> section drafts
review_gates.py           artifacts -> review_reports
report_assembler.py       section drafts -> final_report.md
manifest.py               run artifacts -> MANIFEST.md
progress.py               run status, task ledger, progress log, contract docs
runner.py                 workflow orchestration
```

## Rules

```text
1. Business modules do not call the NotebookLM CLI directly.
2. Every NotebookLM call must pass notebook_id explicitly.
3. QueryResult raw responses are saved before material processing.
4. Section composition may only use MaterialPackage and claim matrix content.
5. Missing material is represented as MATERIAL_NEEDED, not invented.
6. Reviewers output verdict JSON and do not rewrite artifacts directly.
7. External LLM APIs are disabled in the report generation path.
8. Do not modify the NotebookLM skill; call the local `notebooklm` CLI only.
```
