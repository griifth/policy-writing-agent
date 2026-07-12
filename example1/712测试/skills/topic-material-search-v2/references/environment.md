# Environment, Paths & Material Contract

All paths are fixed; use them verbatim.

## Project layout

- Workflow project root: `/Users/hujingkai/Documents/New project/example1/strategic_response_workflow`
- Workflow entry: `workflow/runner.py` — **cd into `workflow/` before running**, or internal imports fail.
- DeepSeek is pre-configured: `strategic_response_workflow/.env` holds the key; callable in one line from `workflow/` via `llm_client` (see [review-standard.md](review-standard.md)).
- Report modules: `report_modules/<report-type>/` — `module.yaml` lists the `retrieval_types`; the prompts live under `prompts/`. You do NOT modify modules.
- Runs live under `strategic_response_workflow/runs/` (resolved as `WORKFLOW_ROOT/runs`, where `WORKFLOW_ROOT` is the parent of `workflow/`).

## Material contract (must match exactly)

- Put the pack at `strategic_response_workflow/runs/<run-id>/retrieval_outputs/`.
- Provide **exactly one file per retrieval type**, named `<retrieval_type>.md`. Missing any one → `runner.py` raises `FileNotFoundError` when reused.
- Confirm the retrieval types by reading `report_modules/<report-type>/module.yaml`. For `experience_response`:
  `practice_background, key_practices, enabling_conditions, effectiveness_evidence, china_status_and_gaps, adaptation_evidence`.
- `<run-id>` must be a bare directory name (no slashes), e.g. `web-materials-<short-slug>`.

## Resolve module retrieval types

```bash
cd "/Users/hujingkai/Documents/New project/example1/strategic_response_workflow"
python3 -c "import yaml,sys; print('\n'.join(yaml.safe_load(open('report_modules/%s/module.yaml'%sys.argv[1]))['retrieval_types']))" experience_response
```

## Hand-off: feed the writing workflow (optional, only if asked)

```bash
cd "/Users/hujingkai/Documents/New project/example1/strategic_response_workflow/workflow"
python3 runner.py \
  --report-type <report-type> \
  --topic "<topic>" \
  --target-country "<...>" \
  --strategy-domain "<...>" \
  --china-response-focus "<...>" \
  --notebook-name "web-collected" \
  --llm-provider deepseek \
  --reuse-materials-run <run-id>
```

`--notebook-name` is required but ignored when materials are reused (placeholder is fine). The reviewed article lands at the new `runs/run-*/final_article_reviewed.md`.

## Note

This chain is an automation experiment; human spot-checking of `retrieval_outputs/` (especially `[未取全文]`/`[待核]`/`[媒体转述]` items) is still advised afterward.
