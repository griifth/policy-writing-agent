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

Start the local console to edit agent runtime settings through a browser:

```bash
python3 src/runtime_console_server.py --host 127.0.0.1 --port 8787
```

Open `http://127.0.0.1:8787/`. The console can switch between Codex/local and API-assisted mode, edit OpenAI/Anthropic defaults, and route supported writing agents to API mode. It writes only environment variable names such as `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`; it never stores API key values.

## Agent Runtime

The writing workflow has two driver modes:

```yaml
agent_runtime:
  mode: "local"          # local | llm_api
  default_driver: "local"
```

`local` keeps the current deterministic/Codex-owned writing workflow. `llm_api` enables external LLM API execution for agents that are switched to that driver. API keys must be referenced through environment variables, not stored in YAML.

Per-agent API configuration follows this shape:

```yaml
agent_runtime:
  provider_defaults:
    openai:
      provider: "openai"
      api_key_env: "OPENAI_API_KEY"
      base_url: "https://api.openai.com/v1"
      model_env: "OPENAI_MODEL"
      model: "gpt-4.1-mini"
      temperature: 0.2
      max_tokens: 1600
      timeout_sec: 120
    anthropic:
      provider: "anthropic"
      api_key_env: "ANTHROPIC_API_KEY"
      base_url: "https://api.anthropic.com"
      anthropic_version: "2023-06-01"
      model_env: "ANTHROPIC_MODEL"
      model: "claude-3-5-sonnet-latest"
      temperature: 0.2
      max_tokens: 1600
      timeout_sec: 120
  agents:
    SectionComposerAgent:
      driver: "llm_api"
      api:
        provider: "anthropic"
```

Every run writes `agent_runtime.json` and `agent_runtime_validation.json` so the driver choice and redacted provider settings are auditable.

## Module Boundaries

```text
agent_runtime.py         local/API agent driver config and optional LLM API client
query_planner.py          ReportTask -> QueryJob[]
notebooklm_adapter.py     QueryJob -> QueryResult
material_pack_builder.py  QueryResult[] -> MaterialPackage[]
matrix_builder.py         MaterialPackage[] -> matrices
section_planner.py        matrices + contracts -> POLICY_REPORT_PLAN.md
section_composer.py       materials + claims -> section drafts
review_gates.py           artifacts -> review_reports
report_assembler.py       section drafts -> final_report.md
manifest.py               run artifacts -> MANIFEST.md
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
```
