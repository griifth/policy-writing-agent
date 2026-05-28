# Optimization Progress

## 2026-05-27 Round 16: Source Deep Dive All Candidates

### Main-Agent Decision

User changed the retrieval policy: after base retrieval/citation sweep resolves source candidates, the workflow should select every resolved source candidate, not only three. Each selected source still runs the same four writing lanes.

Implementation:

- `source_deep_dive_limit: "all"` now means no candidate cap.
- `source_deep_dive_limit: 0` still disables source deep dive.
- Mock, real, and education-evaluation configs now use `source_deep_dive_limit: "all"`.
- The source set is still bounded by resolved candidates from base retrieval/citation sweep, not by every source file in the whole NotebookLM notebook.

### Files Changed

- `src/source_deep_dive.py`
- `src/runner.py`
- `config/report_task.yaml`
- `config/report_task.real.yaml`
- `config/report_task.education_evaluation.real.yaml`
- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from runner import _configured_source_deep_dive_limit, _source_deep_dive_enabled
from source_deep_dive import build_source_deep_dive_candidates

sources = [
    {'notebook_id':'nb','id':'s1','title':'A.pdf'},
    {'notebook_id':'nb','id':'s2','title':'B.pdf'},
    {'notebook_id':'nb','id':'s3','title':'C.pdf'},
]
trace = {'trace_id':'t1','job_id':'j','query_type':'q','text':'evidence','citation_ids':['1','2','3'],'source_refs':[{'notebook_id':'nb','source_id':'s1'},{'notebook_id':'nb','source_id':'s2'},{'notebook_id':'nb','source_id':'s3'}]}
results = [{'status':'PASS','evidence_trace':[trace]}]
for raw in ['all', 2, 0, 'bad']:
    limit = _configured_source_deep_dive_limit({'source_deep_dive_limit': raw})
    candidates = build_source_deep_dive_candidates(results, sources, limit)
    print(raw, 'limit=', limit, 'enabled=', _source_deep_dive_enabled(limit), 'count=', len(candidates), [c['source_id'] for c in candidates])
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id source_deep_dive_all_mock_20260527
git diff --check
```

Result:

- `all` produced all 3 candidates in targeted smoke.
- Integer `2` produced 2 candidates.
- `0` disabled source deep dive and produced 0 candidates.
- Full mock workflow `source_deep_dive_all_mock_20260527` completed with all review gates PASS.

### Known Warnings

- Real runs can become much longer because source lane calls now equal `resolved_source_count * 4`.
- Need clearer run-status messaging that reports the resolved source count before source deep dive begins.

### Next Round Target

If rerunning real mode, inspect `source_deep_dive_candidates.json` first and decide whether the number of resolved sources is operationally acceptable for a full source-lane pass.

## 2026-05-27 Round 15: Education Evaluation Real Rerun After Source Breadth Fix

### Main-Agent Decision

Reran the user's report query “教育评价在人工智能时代的转变” after the display citation cleanup and source breadth parser fix.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.education_evaluation.real.yaml --run-id education_evaluation_ai_real_rerun_20260527
```

Generated report:

`runs/education_evaluation_ai_real_rerun_20260527/final_report.md`

### Validation

Result:

- Run completed with final status `WARN`, not `ERROR`.
- `PlanReviewerAgent`: PASS.
- `NotebookLMPreflightGate`: PASS.
- `RetrievalCompletenessGate`: PASS.
- `MaterialPackAudit`: PASS.
- `MaterialCoverageReviewerAgent`: PASS.
- `EvidenceUseReviewerAgent`: PASS.
- `SectionContractReviewerAgent`: PASS.
- `KillArgumentAgent`: PASS.
- `DriftReviewerAgent`: PASS.
- `ClaimAuditAgent`: WARN.
- `ReportQualityReviewerAgent`: WARN because upstream claim audit was WARN.

Source breadth result:

- `source_deep_dive_candidates.json` contains 3 source candidates.
- `source_deep_dive_jobs.json` contains 12 jobs.
- Selected sources:
  - `Exploring Effective Uses of Generative AI in Education.pdf`
  - `AI_and_education_protecting_the_rights_of_learners_UNESCO_2025.pdf`
  - `教师生成式人工智能应用指引.docx`
- The run did not need `citation_sweep`; first-stage `comparison` evidence already resolved 3 source candidates.

Display result:

- `rg -n "\[[0-9]+(?:[-,，、][0-9]+)*\]" runs/education_evaluation_ai_real_rerun_20260527/final_report.md` returned no matches.
- Reader-facing report no longer shows NotebookLM `[n]` citation markers.

### Known Warnings

- `ClaimAuditAgent` still warns because medium-support claims appear in sections with strong policy language.
- Some list-valued fields still render awkwardly in Markdown, especially in “前沿判断” and impact rows.
- The appendix source labels are highly verbose because claim rows inherit broad package-level source refs.

### Next Round Target

Improve writing polish: normalize list-valued fields into clean bullets, reduce appendix source label verbosity, and soften medium-support claim wording so `ClaimAuditAgent` can pass.

## 2026-05-27 Round 14: Citation Sweep Prompt Parameterization Cleanup

### Main-Agent Decision

User clarified that the task topic must not be hardcoded and that the sentence “必须尽量列出 3 个互不相同的 source_title” should be removed. The code already injects the topic through `task_spec["topic"]`; this round verified that behavior and updated the prompt wording plus documentation.

### Files Changed

- `src/source_deep_dive.py`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from source_deep_dive import build_citation_sweep_job
job = build_citation_sweep_job({'topic': '临时传入主题ABC', 'notebook_id': 'nb'}, '/tmp/run', 7)
prompt = job['prompt']
print('has_dynamic_topic', '临时传入主题ABC' in prompt)
print('has_old_phrase', '必须尽量列出 3 个互不相同的 source_title' in prompt)
print('has_hardcoded_education_eval', '教育评价在人工智能时代的转变' in prompt)
PY
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
```

Result:

- `has_dynamic_topic True`
- `has_old_phrase False`
- `has_hardcoded_education_eval False`
- Python compile passed.

## 2026-05-27 Round 13: Citation Sweep Source Breadth Fix

### ARIS Capability Reviewed

本轮针对“sweep 后应选 3 个不同 source 深挖”的执行偏差做诊断和修复。目标是让 source selection 使用 NotebookLM 回答中可解析的多文件标题，而不是被 CLI 顶层 `references` 的单一 source id 压扁。

### Subagent Proposals Considered

- Retrieval subagent: 上次教育评价 real run 的 `citation_sweep` 内嵌 JSON 已列出 9 个不同 source title，说明 NotebookLM 确实找到了多来源材料。
- Parser subagent: 顶层 CLI `references` 将 9 个 citation 都映射到 `01_Navigating_Artificial_Intelligence_in_Postsecondary_Education.pdf`，当前 adapter 优先使用顶层 references，导致候选源只剩一个。
- Prompt subagent: `citation_sweep` prompt 没明确要求 3 个不同 source，也没有输出 `source_candidates`，需要把 source breadth 写进 prompt contract。

### Main-Agent Decision

修复三点：

1. `NotebookLMAdapter` 在结构化回答中存在 `citations` 时优先使用内嵌 `citations.title`，再 fallback 到顶层 `references`。这样 `citations.title` 可通过 `notebooklm_sources.json` 解析为真实 source id。
2. `citation_sweep` prompt 和 output contract 新增 `source_candidates`，要求尽量列出 3 个不同 `source_title`。
3. `SourceDeepDivePlannerAgent` 不再每个 evidence trace 只取第一个 source，而是遍历同一句中的多个 citation/source；并支持从 `structured_answer.source_candidates` fallback 生成 candidates。

### Actual Prompt After Fix

```text
任务主题：“{task.topic}”。
请基于当前 NotebookLM 知识库，找出最值得深挖的政策热点证据句。重点关注反复出现、跨主题出现或具有政策前沿意义的内容。
必须尽量覆盖 3 个不同 source 文件；如果知识库中确实不足 3 个相关 source，才少于 3 个。不要把所有引用集中到同一个 source。
请严格只返回一个 JSON object，不要 Markdown 代码块，不要额外解释。
返回格式必须是：
{
  "answer": "带 [n] 引用标记的纯文本回答。每一句关键判断都要带至少一个 [n]。",
  "citations": [
    {"id": 1, "title": "报告名称"}
  ],
  "source_candidates": [
    {"source_title": "报告名称", "reason": "为什么值得 source-specific deep dive", "citation_ids": [1]}
  ]
}
source_candidates 中的 source_title 必须和 citations.title 一致。不要写完整报告；只给能指导 source-specific deep dive 的证据句。
```

### Files Changed

- `src/notebooklm_adapter.py`
- `src/source_deep_dive.py`
- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json
from pathlib import Path
from notebooklm_adapter import _extract_evidence_trace, _normalize_citations, _with_notebook_id
from source_deep_dive import build_citation_sweep_job, build_source_deep_dive_candidates

notebook_id = 'b3d4fcf7-cefc-4cbc-8ccf-481b65b2651f'
run = Path('runs/education_evaluation_ai_real_20260527')
sweep = json.loads((run / 'query_results/07_citation_sweep.json').read_text(encoding='utf-8'))
sources = json.loads((run / 'notebooklm_sources.json').read_text(encoding='utf-8'))
for source in sources:
    source.setdefault('notebook_id', notebook_id)
structured = sweep['structured_answer']
citations = _with_notebook_id(_normalize_citations(structured['citations']), notebook_id)
job = {'id': sweep['job_id'], 'notebook_id': notebook_id, 'query_type': sweep['query_type'], 'section': sweep['section']}
trace = _extract_evidence_trace(structured['answer'], citations, job)
result = dict(sweep)
result['evidence_trace'] = trace
result['citation_refs'] = citations
result['source_refs'] = []
result['structured_answer'] = structured
candidates = build_source_deep_dive_candidates([result], sources, 3)
print('candidate_count', len(candidates))
for candidate in candidates:
    print(candidate['source_id'], candidate['source_title'], candidate['citation_ids'])
print(build_citation_sweep_job({'topic':'任意任务主题','notebook_id':notebook_id}, '/tmp/sweep_prompt', 7)['prompt'])
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id source_breadth_candidate_mock_20260527
git diff --check
```

Result:

- Python compile passed.
- Replaying the previous real sweep with embedded citation titles produced 3 distinct candidates:
  - `AI_and_the_future_of_education_disruptions_dilemmas_directions_UNESCO_2025.pdf`
  - `Exploring Effective Uses of Generative AI in Education.pdf`
  - `中国智慧教育白皮书_2025年5月_教育部.pdf`
- Full mock workflow `source_breadth_candidate_mock_20260527` completed with all review gates PASS.

### Known Warnings

- The previous real report was not rerun after this fix; it still reflects the old one-source deep dive.
- A future real run should verify that the new prompt plus parser actually produces 3 source-specific lane groups in live NotebookLM execution.

### Next Round Target

Rerun the education-evaluation real query with the new citation sweep prompt and parser, then check whether source deep dive expands to three source candidates and twelve lane jobs.

## 2026-05-27 Round 12: Display Citation Cleanup And Notebook-Scoped Trace

### ARIS Capability Reviewed

本轮区分“读者可见写作层”和“审计可回溯 artifact 层”：正文不应暴露 NotebookLM 的 `[n]` 引用标记，但 trace artifact 必须保留 citation/source，并且要能跨 notebook 区分同名或同号引用。

### Subagent Proposals Considered

- Report-writing subagent: 最终报告和章节草稿中删除 `[1]`、`[2-4]` 等方括号引用，避免把 NotebookLM 内部 citation 标记带入正文。
- Traceability subagent: 不删除 JSON artifact 中的 citation/source trace；相反，应给 `citation_refs`、`source_refs` 和 `evidence_trace` 补充 `notebook_id`。
- Integration subagent: appendix 的 source label 可以显示 `title (notebook_id/source_id)`，用于审计区分；正文段落不显示 citation marker。

### Main-Agent Decision

新增 `src/text_cleaning.py`，在 section composer、claim matrix 和 report assembler 的显示路径清理方括号 citation marker。NotebookLMAdapter 现在把 `notebook_id` 写入 normalized citation refs、source refs 和 evidence trace；source list 也补 `notebook_id`。Material package 去重 key 改为包含 `notebook_id`，避免不同 notebook 下相同 `source_id/title/citation id` 造成混淆。

这映射到报告写作目标：读者看到的是自然报告文本，而不是 NotebookLM citation 语法；审查者仍可通过 artifacts 回到具体 notebook/source/citation。

### Files Changed

- `src/text_cleaning.py`
- `src/section_composer.py`
- `src/report_assembler.py`
- `src/matrix_builder.py`
- `src/notebooklm_adapter.py`
- `src/material_pack_builder.py`
- `src/source_deep_dive.py`
- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from notebooklm_adapter import NotebookLMAdapter
from report_assembler import assemble_report
from text_cleaning import strip_citation_markers

print(strip_citation_markers('判断[1]，还有[2-4]。'))
adapter = NotebookLMAdapter(mode='mock')
job = {'id':'01_global_scan','query_type':'global_scan','section':'hotspot','notebook_id':'mock-notebook','expected_fields':['hotspot_name','claim_candidates']}
result = adapter.ask(job)
print(result['citation_refs'][0])
print(result['source_refs'][0])
print(result['evidence_trace'][0]['notebook_id'])
report = assemble_report({'topic':'测试'}, {'hotspot':'# 一、热点\n\n判断[1]。'}, [], [], {'policy_claim_material_matrix':[{'claim_text':'判断[1]。','support_level':'medium','allowed_sections':['hotspot'],'source_refs':result['source_refs'],'caution_note':'谨慎[2]。'}]})
print('[1]' in report, '[2]' in report)
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id citation_display_trace_mock_20260527
rg -n "\[[0-9]+(?:[-,，、][0-9]+)*\]" runs/citation_display_trace_mock_20260527/final_report.md || true
git diff --check
```

Result:

- Python compile passed.
- Targeted smoke stripped visible `[1]` and `[2-4]`.
- Mock NotebookLM query result preserved `citation_refs/source_refs/evidence_trace` and included `notebook_id`.
- Full mock workflow `citation_display_trace_mock_20260527` completed with all review gates PASS.
- `rg` found no bracket citation markers in the mock final report.

### Known Warnings

- Existing real report `education_evaluation_ai_real_20260527` was generated before this display cleanup; rerun or reassemble is needed for a cleaned real report artifact.
- Source selection breadth still needs improvement to reach the intended three distinct sources after sweep.

### Next Round Target

Rerun the education-evaluation real query after improving source sweep breadth, so the regenerated report both omits visible `[n]` markers and covers more than one source.

## 2026-05-27 Round 11: Real Query Run For Education Evaluation Topic

### ARIS Capability Reviewed

本轮验证“用户 query -> 配置化任务 -> NotebookLM real retrieval -> 材料包 -> 报告”的完整 MVP 写作链路。目标不是新增外部知识入口，而是用真实 topic 检查当前系统是否能按 NotebookLM-only 边界产出报告。

### Subagent Proposals Considered

- Runtime subagent: 为用户 query 单独新增任务配置，避免覆盖默认 `report_task.real.yaml`。
- Retrieval subagent: 继续使用真实 NotebookLM notebook、串行问答和 `source_deep_dive_limit: 3`，观察 sweep 后实际 source 覆盖数量。
- Review subagent: 以 review gates 判定报告是否可用；如果 WARN，记录具体 gate，而不是把 WARN 包装成全绿。

### Main-Agent Decision

新增 `config/report_task.education_evaluation.real.yaml`，将 topic 设置为“教育评价在人工智能时代的转变”，并执行完整 real workflow：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.education_evaluation.real.yaml --run-id education_evaluation_ai_real_20260527
```

生成报告路径：

`runs/education_evaluation_ai_real_20260527/final_report.md`

### Files Changed

- `config/report_task.education_evaluation.real.yaml`
- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

Result:

- Run completed with final status `WARN`, not `ERROR`.
- `PlanReviewerAgent`: PASS.
- `NotebookLMPreflightGate`: PASS.
- `RetrievalCompletenessGate`: PASS; all QueryJobs produced expected fields.
- `MaterialPackAudit`: PASS.
- `MaterialCoverageReviewerAgent`: PASS.
- `EvidenceUseReviewerAgent`: PASS.
- `SectionContractReviewerAgent`: PASS.
- `KillArgumentAgent`: PASS.
- `DriftReviewerAgent`: PASS.
- `ClaimAuditAgent`: WARN because medium-support claims appeared in sections containing strong policy language.
- `ReportQualityReviewerAgent`: WARN only because upstream `ClaimAuditAgent` was WARN.

Generated artifacts include:

- `query_results/01_global_scan.json` through `query_results/06_insight.json`
- `query_results/07_citation_sweep.json`
- `query_results/08_hotspot_rationale_deep_dive_1.json`
- `query_results/09_core_material_deep_dive_1.json`
- `query_results/10_comparison_deep_dive_1.json`
- `query_results/11_impact_deep_dive_1.json`
- `material_packages/mp_ai_literacy.json`
- `final_report.md`

### Post-Implementation Review

The workflow successfully answered the user's query with a real NotebookLM-backed report. The report identified the main hotspot as “生成式人工智能冲击下的教育评价范式重构与多维伴随式评价转型” and produced sections for hotspot, theme, comparison, impact, and insight.

However, the run exposed an important retrieval breadth gap: although `source_deep_dive_limit` was 3, citation sweep resolved only one source candidate, `01_Navigating_Artificial_Intelligence_in_Postsecondary_Education.pdf`, so source-specific deep dive covered one source rather than the intended three-source breadth. This is a source-selection/prompt breadth issue, not a CLI/auth failure.

### Known Warnings

- Final report is usable as a draft, but not decision-grade green because claim language should be softened for medium-support claims.
- Sweep/source candidate selection needs improvement so a default 3-source deep dive actually selects up to three distinct sources when the notebook contains enough relevant sources.
- The section composer currently renders some list-valued fields awkwardly in Markdown, e.g. Python-style list strings in “前沿判断” and impact subsections.

### Next Round Target

Improve citation sweep/source selection breadth so it asks for and resolves 3 distinct source candidates by default, then rerun the education evaluation topic. Separately, soften medium-support claim language in section drafts to clear `ClaimAuditAgent`.

## 2026-05-27 Round 10: Source Deep Dive Breadth Decision

### ARIS Capability Reviewed

本轮只做策略收束：source-specific deep dive 不应无限追问，而应在 sweep 后选少量高价值 source 做深挖，保持 NotebookLM 调用成本可控。

### Subagent Proposals Considered

- Retrieval subagent: sweep 后选择 3-4 个 source 能覆盖多个证据来源，比只选 1 个 source 更适合正式报告。
- Runtime subagent: 现有机制是每个 source 展开 4 条 lane；如果选 4 个 source，会产生 16 次 source-lane NotebookLM ask，因此默认不应盲目扩大。
- Report-writing subagent: 单主热点深挖报告优先 3 个 source；top-k 热点清单或热点比较报告、或者材料包 coverage 不足时，才扩展到 4 个 source。

### Main-Agent Decision

保留 `source_deep_dive_limit: 3` 作为默认真实运行策略，并把 4 个 source 定义为有条件上限，而不是默认值。这样正式 real run 会在 sweep 后选中三个高价值 source 做进一步提问；如报告目标明确是 top-k 热点比较、或前三个 source 不能覆盖 comparison/impact 材料，再临时升到 4。

这映射到报告写作目标：报告材料来源不再过窄，但也避免把 NotebookLM 提问次数从基础查询扩张到不可控。当前四 lane 机制下，3 个 source 约等于 12 次 source deep dive，4 个 source 约等于 16 次 source deep dive。

### Files Changed

- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

No runtime validation was needed because this round did not change code or config. Current configs already set `source_deep_dive_limit: 3` in both mock and real task files.

### Known Warnings

- Full real workflow still needs an end-to-end run using the default 3-source limit.
- If a later run raises the limit to 4, the run record must explain why the extra source was needed.

### Next Round Target

Run full real mode with the default three-source source deep dive limit if runtime budget allows.

## 2026-05-27 Round 9: Bounded Real-Mode Source Lane Validation

### ARIS Capability Reviewed

本轮不扩展架构，只验证“有界真实运行先暴露 artifact 契约问题，再做最小修复”的主 agent 工作方式。验证对象是 NotebookLM CLI 真实返回的 citation/source trace 是否能驱动 source-specific deep dive lane。

### Subagent Proposals Considered

- Runtime-boundary subagent: 只使用 `config/report_task.real.yaml` 中配置的本地 NotebookLM CLI，不浏览网页，不增加外部检索。
- Retrieval subagent: 不直接跑完整 6+12 查询链，而是先跑 `citation_sweep + 1 个 source candidate + 4 条 source lane` 的 bounded smoke，验证 `source_id`、`-s` 限定和 lane prompt。
- Parser subagent: 若真实 CLI 字段与 mock 不一致，优先修 NotebookLMAdapter 的字段归一化，不改 NotebookLM skill，不放宽 review gate。

### Main-Agent Decision

执行真实 NotebookLM bounded smoke。第一次运行 `real_bounded_source_lane_smoke_20260527` 通过 auth/source/citation sweep，但没有生成 source candidate。原因是真实 CLI 的 `references` 使用 `citation_number + source_id`，而 adapter 只识别 `id/citation_id/ref_id`，导致 evidence trace 中的 `[n]` 退化成伪 source id。

实施最小修复：`NotebookLMAdapter._normalize_citations()` 识别 `citation_number`。修复后重跑 `real_bounded_source_lane_smoke_fixed_20260527`，成功从真实 NotebookLM citation trace 解析出 source candidate，并用 `-s 5d843033-f83a-4864-8d2e-1d03c9986fb3` 跑通四条 lane。

这映射到报告写作目标：真实知识库中的 citation/source trace 现在能进入二阶段 source-specific deep dive，材料包可以在后续完整 real run 中消费四类写作材料，而不是停留在 mock 证明。

### Files Changed

- `src/notebooklm_adapter.py`
- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

```bash
/Users/hujingkai/Desktop/notebookcli2report/notebooklm-py-main/.venv/bin/notebooklm auth check --test --json
/Users/hujingkai/Desktop/notebookcli2report/notebooklm-py-main/.venv/bin/notebooklm source list -n b3d4fcf7-cefc-4cbc-8ccf-481b65b2651f --json
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from notebooklm_adapter import _normalize_citations, _extract_evidence_trace
from source_deep_dive import build_source_deep_dive_candidates
job = {'id':'01_citation_sweep','query_type':'citation_sweep','section':'hotspot'}
refs = [{'citation_number': 1, 'source_id': 'source-uuid'}]
trace = _extract_evidence_trace('测试判断[1]。', _normalize_citations(refs), job)
sources = [{'id': 'source-uuid', 'title': 'Real Source.pdf'}]
print(build_source_deep_dive_candidates([{'status':'PASS','evidence_trace':trace}], sources, 1))
PY
```

Result:

- NotebookLM auth check returned `ok`.
- Real notebook source list returned 35 ready sources.
- First bounded smoke `real_bounded_source_lane_smoke_20260527`: `citation_sweep_status=PASS`, `citation_count=7`, `evidence_trace_count=5`, but `candidate_count=0`; this exposed the `citation_number` parser gap.
- Local parser smoke confirmed `citation_number` now maps `[1]` to a real `source_id` candidate.
- Second bounded smoke `real_bounded_source_lane_smoke_fixed_20260527`: `status=PASS`, `candidate_count=1`, `lane_job_count=4`.
- Candidate source: `01_Navigating_Artificial_Intelligence_in_Postsecondary_Education.pdf` / `5d843033-f83a-4864-8d2e-1d03c9986fb3`.
- Four lane jobs all returned `PASS` with no missing expected fields:
  - `hotspot_rationale_deep_dive`
  - `core_material_deep_dive`
  - `comparison_deep_dive`
  - `impact_deep_dive`

### Post-Implementation Review

Review subagent critique: the fix is correctly bounded to NotebookLM response normalization. It does not add a new knowledge path and does not change the file-level source precision rule. The real smoke validates source ID parsing and `-s` lane execution on one source, but it is still not a complete real-mode full workflow run.

### Known Warnings

- Full `config/report_task.real.yaml` workflow has not yet been rerun end-to-end after the parser fix.
- Real citation title enrichment is still partial when CLI `references` omit title; source ID resolution is sufficient for `-s`, but report-facing source labels may depend on the source list.
- Material package fan-out remains a separate decision only for top-k hotspot inventory/comparison reports.

### Next Round Target

Run one full real-mode workflow only if rate limits and runtime budget allow; otherwise make source title enrichment from `notebooklm_sources.json` explicit in artifacts before full real run.

## 2026-05-27 Round 8: Explicit Section Contract Output Shapes

### ARIS Capability Reviewed

ARIS 的可迁移能力是“生产 artifact 与审查 gate 使用同一份显式契约”。本项目此前已经有 `section_contracts.yaml`，但章节生产方没有把 `output_shape` 逐字渲染成可见结构，导致 reviewer 只能给出 WARN。

### Subagent Proposals Considered

- Section-contract reviewer: `SectionContractReviewerAgent` 逐字检查 `output_shape`，所以改动应落在 `SectionComposerAgent`，而不是放宽 reviewer。
- Report-writing subagent: 每个章节应把契约项作为自然标题使用，例如“热点总述”“热点列表”“升温原因”“可继续分析的重点热点”，这样既满足 gate，也改善读者扫描。
- Runtime-boundary subagent: API-assisted writer 仍只能消费 Codex 准备的材料包、矩阵、claims 和 section contract；prompt 需要明确要求逐字保留 `contract.output_shape`。

### Main-Agent Decision

让 `SectionComposerAgent` 将每个章节契约的 `output_shape` 显式渲染为 Markdown 标题，并更新 API writer prompt，要求 API-assisted 模式也逐字保留这些标题。没有放宽审查标准，也没有添加外部知识。

这映射到报告写作目标：章节不再只是“内容大致覆盖”，而是把报告读者需要看到的结构显式呈现出来，使热点梳理、主题归类、政策比较、影响研判和启发建议都能按契约检查和人工阅读。

### Files Changed

- `src/section_composer.py`
- `src/material_pack_builder.py`
- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from io_utils import load_yaml
from review_gates import review_section_contracts
from section_composer import compose_section

contracts = load_yaml('config/section_contracts.yaml')
materials = [{'package_id':'mp','hotspot':'AI 素养','main_theme':'AI 素养','cross_themes':['教师发展'],'section_targets':['hotspot'], 'actors':['学校'], 'raw_fields': {'policy_problem':'能力框架不足','rise_reason':'材料反复出现'}}]
matrices = {
 'hotspot_theme_matrix':[{'hotspot':'AI 素养','main_theme':'AI 素养','cross_themes':['教师发展']}],
 'comparison_matrix':[{'hotspot':'AI 素养','policy_goal':'提升能力','target_group':'教师','policy_tool':'培训','implementation_mechanism':'课程嵌入','risk_governance':'隐私治理','frontier_feature':'能力与治理并重'}],
 'impact_table':[{'governance_impact':'治理规则','school_practice_impact':'学校流程','teacher_development_impact':'教师培训','student_learning_impact':'学生使用','education_evaluation_impact':'评价变化','platform_resource_impact':'平台治理','ethics_safety_impact':'伦理安全','explicit_impacts':['学校流程'],'cautious_inferences':['能力扩展'],'uncertainty':'需持续观察'}],
 'insight_table':[{'research_insight':'研究课程落地','governance_insight':'同步规则','practice_insight':'场景规范','monitoring_insight':'持续监测','knowledge_base_insight':'保留主题标签'}],
}
claims = [{'claim_text':'AI 素养成为综合能力','support_level':'medium','allowed_sections':['hotspot']}]
drafts = {sid: compose_section(sid, contract, materials, claims, matrices) for sid, contract in contracts.items()}
review = review_section_contracts(drafts, contracts)
print(review['verdict'])
print(review['details']['issues'])
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id section_contract_explicit_dedup_mock_20260527
git diff --check
```

Result:

- Python compile passed.
- Targeted section-contract smoke returned `PASS` with no issues.
- Full mock workflow `section_contract_explicit_dedup_mock_20260527` completed in `notebooklm_only`.
- All review gates returned `PASS`, including `SectionContractReviewerAgent` and `ReportQualityReviewerAgent`.
- Comparison and impact rows now dedupe repeated base/lane rows in the material package.
- `git diff --check` passed.

### Post-Implementation Review

Review subagent critique: the fix addresses the actual reviewer contract instead of weakening the gate. It improves final report readability and keeps knowledge boundaries intact. The four-lane deep dive buckets are available in material packages, but the current composer still mainly consumes matrices/material package fields rather than every lane bucket directly.

### Known Warnings

- No mock-mode review gates remain WARN in `section_contract_explicit_mock_20260527`.
- Real-mode validation is still needed for NotebookLM source ID resolution and lane prompt behavior.
- Multi-hotspot material package fan-out remains a separate architectural decision for hotspot-list reports.

### Next Round Target

Run a real-mode bounded validation if NotebookLM auth/rate limits permit; otherwise implement a small lane-material rendering pass so section drafts can visibly cite which deep dive lane supplied key materials.

## 2026-05-27 Round 7: Four-Lane Source Deep Dive Adaptation

### ARIS Capability Reviewed

ARIS 的可迁移能力是“把一个大任务拆成职责清楚、产物契约不同的小型子任务，再由主 agent 判断哪些子任务结果进入最终写作链”。本轮只借鉴这种任务边界和 artifact contract，不引入 ARIS 的外部检索、论文流程或通用 agent 基建。

### Subagent Proposals Considered

- Prompt-contract subagent: source-specific deep dive 不应只有一个泛化提示词，应按写作目的拆成热点形成依据、核心材料、比较材料、影响材料四类 lane，每类都有不同字段。
- Programmer subagent: 在现有 `source_deep_dive_candidates.json` 基础上生成多 lane QueryJobs，仍由 NotebookLM CLI 串行执行，材料包只消费 QueryResult，不让 NotebookLM 以外的执行器接触知识库。
- Report-writing subagent: `hotspot_rationale_deep_dive` 服务“为什么这是热点”，`core_material_deep_dive` 服务主体论证，`comparison_deep_dive` 服务政策比较表，`impact_deep_dive` 服务影响研判；`insight` 暂不独立 deep dive，而从前面材料综合。

### Main-Agent Decision

实施四条有界 source deep dive lane：每个被 citation trace 命中的 source，在 `source_deep_dive_limit` 控制下展开为 `hotspot_rationale_deep_dive`、`core_material_deep_dive`、`comparison_deep_dive`、`impact_deep_dive` 四个 NotebookLM job。每个 job 仍带 `source_ids`，由 CLI 加 `-s <source_id>` 限定文件级 source；默认 `max_concurrency: 1` 保持串行问答。

这映射到报告写作目标：材料包现在能区分“热点为什么成立”“主体分析材料”“比较矩阵材料”“影响研判材料”，避免所有深挖结果混成一组泛化字段，后续章节可以按写作功能消费材料。

### Files Changed

- `src/source_deep_dive.py`
- `src/runner.py`
- `src/notebooklm_adapter.py`
- `src/material_pack_builder.py`
- `config/dimension_registry.yaml`
- `config/report_task.yaml`
- `config/report_task.real.yaml`
- `docs/optimization_guardrails.md`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from io_utils import load_yaml
from material_pack_builder import build_material_packages
from notebooklm_adapter import NotebookLMAdapter
from source_deep_dive import build_source_deep_dive_candidates, build_source_deep_dive_jobs

cfg = load_yaml('config/report_task.yaml')
dim = load_yaml('config/dimension_registry.yaml')
task = cfg['task']
lanes = cfg['execution']['source_deep_dive_lanes']
adapter = NotebookLMAdapter(mode='mock')
base_job = {'id': '01_global_scan', 'query_type': 'global_scan', 'section': 'hotspot', 'notebook_id': 'mock', 'expected_fields': ['hotspot_name']}
base_result = adapter.ask(base_job)
sources = [{'source_id': 'mock-source-1', 'title': 'Mock AI education policy source'}]
candidates = build_source_deep_dive_candidates([base_result], sources, 3)
jobs = build_source_deep_dive_jobs(candidates, task, '/tmp/four_lane_deep_dive_smoke', 1, lanes)
results = [adapter.ask(job) for job in jobs]
package = build_material_packages([base_result, *results], dim)[0]
print('jobs', len(jobs))
print('lanes', [job['query_type'] for job in jobs])
print('lane_counts', {lane: len(items) for lane, items in package['deep_dive_materials'].items()})
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id four_lane_deep_dive_mock_rerun_20260527
git diff --check
```

Result:

- Python compile passed.
- Targeted smoke produced one source candidate and four lane jobs: `hotspot_rationale_deep_dive`, `core_material_deep_dive`, `comparison_deep_dive`, `impact_deep_dive`.
- Material package stored one item in each lane bucket, and comparison/impact matrices received lane-enriched rows.
- Full mock workflow completed in `notebooklm_only`.
- `PlanReviewerAgent`, `NotebookLMPreflightGate`, `RetrievalCompletenessGate`, `MaterialPackAudit`, `MaterialCoverageReviewerAgent`, `EvidenceUseReviewerAgent`, `ClaimAuditAgent`, `KillArgumentAgent`, and `DriftReviewerAgent` returned `PASS`.
- `git diff --check` passed.

### Post-Implementation Review

Review subagent critique: the implementation keeps boundaries explicit. `SourceDeepDivePlannerAgent` plans lane jobs; `NotebookLMAdapter` only executes NotebookLM CLI calls and carries job metadata; `MaterialPackAgent` only buckets already-returned QueryResults. The change does not validate NotebookLM factual accuracy locally, does not preserve chapter metadata, and does not add external knowledge.

### Known Warnings

- `SectionContractReviewerAgent` remains `WARN` because section drafts still do not explicitly render every configured output-shape label.
- `ReportQualityReviewerAgent` remains `WARN` because upstream section-contract warnings are surfaced.
- Real-mode validation still needs a live NotebookLM run to confirm source ID resolution and lane prompts behave with actual report files.
- The flow still has one material package in this worktree; four-lane deep dive enriches that package but does not yet implement multi-hotspot fan-out.

### Next Round Target

Make `SectionComposerAgent` render every section-contract `output_shape` item as a visible heading or label, then decide whether multi-hotspot package fan-out should be restored before real-mode runs.

## 2026-05-26 Round 6: Bounded Source-Specific Deep Dive Loop

### ARIS Capability Reviewed

ARIS 的可迁移能力是“先用审计 artifact 找到值得深挖的证据，再把深挖任务作为有界子任务调度”。在本项目里，这个模式对应用户提出的两步资料包获取：第一阶段全库 citation sweep，第二阶段对被引用 source 单独追问。

### Subagent Proposals Considered

- Retrieval-planning subagent: 从第一阶段 `evidence_trace` 中选择可解析到 NotebookLM source ID 的候选，生成 `source_deep_dive_candidates.json`。
- NotebookLM-boundary subagent: 使用本地 CLI 已支持的 `notebooklm ask -s <source_id> --json`，不增加浏览器、网页检索或 NotebookLM skill 修改。
- Material-package subagent: 第二阶段结果不单独生成报告，而是作为普通 QueryResult 进入 retrieval completeness、材料包和 claim matrix，保持产物链统一。

### Main-Agent Decision

实现一个有界 source-specific deep dive loop。`SourceDeepDivePlannerAgent` 从第一阶段引用 trace 中解析 source，按 `source_deep_dive_limit` 生成少量 `source_deep_dive` QueryJobs；`NotebookLMAdapter` 对带 `source_ids` 的 job 追加 `-s <source_id>` 参数；`runner.py` 在初始检索后执行这些 source-scoped jobs，并把结果合并进后续 retrieval review 与材料包构建。

这映射到报告写作目标：材料包不再只依赖全库泛问，而能对已被 citation 命中的 source 做二次深挖，从而提高政策点、工具、机制、风险和 claim 的来源精度。

User clarification: source-specific deep dive only needs file-level precision. The pipeline now resolves citations to `source_id/title` and does not extract, preserve, or pass chapter-level metadata into source deep-dive jobs. NotebookLM question execution defaults to serial execution (`max_concurrency: 1`) to reduce conversation-state, rate-limit, and source-scoping interference.

### Files Changed

- `src/source_deep_dive.py`
- `src/runner.py`
- `src/notebooklm_adapter.py`
- `config/report_task.yaml`
- `config/report_task.real.yaml`
- `config/dimension_registry.yaml`
- `docs/optimization_guardrails.md`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from notebooklm_adapter import NotebookLMAdapter
from source_deep_dive import build_source_deep_dive_candidates, build_source_deep_dive_jobs
adapter = NotebookLMAdapter(mode='mock')
job = {'id': '01_global_scan', 'query_type': 'global_scan', 'section': 'hotspot', 'notebook_id': 'mock', 'expected_fields': ['hotspot_name']}
result = adapter.ask(job)
sources = [{'source_id': 'mock-source-1', 'title': 'Mock AI education policy source'}]
candidates = build_source_deep_dive_candidates([result], sources, 3)
jobs = build_source_deep_dive_jobs(candidates, {'topic': 'AI 教育政策热点识别与前沿研判', 'notebook_id': 'mock'}, '/tmp/source_deep_dive_smoke', 1)
print(candidates)
print(jobs)
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id source_deep_dive_loop_automation_20260526
```

Result:

- Python compile passed.
- Targeted smoke produced one source-specific candidate and one `source_deep_dive` job with `source_ids`.
- Full mock workflow completed in `notebooklm_only`.
- `source_deep_dive_candidates.json`, `source_deep_dive_jobs.json`, and `query_results/07_source_deep_dive_1.json` were produced.
- `RetrievalCompletenessGate`, `MaterialPackAudit`, `EvidenceUseReviewerAgent`, and `ClaimAuditAgent` all returned `PASS`.

### Post-Implementation Review

Review subagent critique: the implementation preserves agent boundaries. `SourceDeepDivePlannerAgent` selects candidates; `NotebookLMAdapter` only executes CLI calls; `MaterialPackAgent` only consumes QueryResults. The loop is bounded by config and remains NotebookLM-only.

### Known Warnings

- `SectionContractReviewerAgent` remains `WARN` because section drafts still do not explicitly render every configured output-shape label.
- `ReportQualityReviewerAgent` remains `WARN` because upstream section-contract warnings are surfaced.
- Current material package fan-out still collapses into one package in this worktree.
- Real-mode validation still needs a live run to confirm citation source IDs always resolve from NotebookLM `citations` or `source list`.

### Next Round Target

Implement per-hotspot material package fan-out using citation-grounded candidates, then make section composer render every `output_shape` label explicitly.

## 2026-05-26 Round 5: Citation-First Material Trace Propagation

### ARIS Capability Reviewed

ARIS 的可迁移能力不是外部检索或论文流程，而是“每个判断必须可回放到证据 artifact”的审计链。用户指出 NotebookLM CLI 的 `--json` 回答天然包含 `answer` 中的 `[n]` 标记和 `citations` 列表，这可以作为资料包证据链的第一层。

### Subagent Proposals Considered

- Retrieval subagent: 在 NotebookLM `ask --json` 结果中解析 `answer + citations`，先形成句子级 `evidence_trace`，再进入材料包。
- Material-package subagent: 不再只保存结构化字段，应把 `source_refs`、`citation_refs` 和 `evidence_trace` 贯通到 `MaterialPackage` 与 claim candidates。
- Boundary subagent: 允许使用 `notebooklm ask -s <source_id>` 作为下一步二次追问能力，因为 CLI 已支持 `-s/--source`，但本轮只实现解析与贯通，不扩大为完整两阶段检索。

### Main-Agent Decision

实现 citation-first 的最小闭环：`NotebookLMAdapter` 解析 NotebookLM JSON 中的 `citations`，把带 `[n]` 的回答拆成句子级 `evidence_trace`；`MaterialPackAgent` 聚合 query result 的 `source_refs`、`citation_refs`、`evidence_trace` 并写入材料包；`MatrixBuilderAgent` 把这些证据字段传入 `policy_claim_material_matrix`；最终报告附录显示材料包 source/citation 数和 claim 的 source 标签。

这直接服务报告写作目标：报告中的判断不再只是来自材料包字段，而是能沿 claim -> material package -> evidence trace 回到 NotebookLM 引用的 source。

### Files Changed

- `src/notebooklm_adapter.py`
- `src/material_pack_builder.py`
- `src/matrix_builder.py`
- `src/review_gates.py`
- `src/report_assembler.py`
- `config/dimension_registry.yaml`
- `docs/optimization_guardrails.md`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from notebooklm_adapter import _extract_evidence_trace, _normalize_citations, _source_refs_from_citations
job = {'id': 'citation_sweep', 'query_type': 'source_sweep', 'section': 'hotspot'}
payload = {
    'answer': 'AI 素养正在从工具使用能力扩展为治理议题。[1]\n教师发展与学校规则成为政策落点。[2]',
    'citations': [{'id': 1, 'title': '报告A'}, {'id': 2, 'title': '报告B'}],
}
citations = _normalize_citations(payload['citations'])
print(_source_refs_from_citations(citations))
print(_extract_evidence_trace(payload['answer'], citations, job))
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id citation_trace_material_pack_automation_20260526
```

Result:

- Python compile passed.
- User-proposed `answer + citations` shape parsed into two sentence-level evidence trace rows.
- Full mock workflow completed in `notebooklm_only`.
- `EvidenceUseReviewerAgent` changed from `WARN` to `PASS`.
- Final report appendices now show material package source/citation counts and claim source labels.

### Post-Implementation Review

Review subagent critique: the implementation keeps NotebookLM access inside the CLI boundary and does not add external search. It is a valid first step toward the user's two-stage retrieval design, but it does not yet perform source-specific `notebooklm ask -s` deep dives.

### Known Warnings

- `SectionContractReviewerAgent` remains `WARN` because section drafts still do not explicitly render every configured output-shape label.
- `ReportQualityReviewerAgent` remains `WARN` because upstream section-contract warnings are surfaced.
- The current material-package builder still merges query results into one package; multi-hotspot fan-out remains incomplete in this worktree.
- Source-specific second-stage deep dive is designed but not yet wired into the runner.

### Next Round Target

Add a bounded two-stage retrieval loop: all-source citation sweep -> select depth candidates -> source-specific `notebooklm ask -s <source_id>` follow-up queries -> per-hotspot material packages.

## 2026-05-26 Round 4: Schema-Backed Query Prompt Contracts

### ARIS Capability Reviewed

ARIS uses explicit artifact contracts between executor and reviewer skills: a producing agent writes a known artifact shape, and downstream reviewers reject missing contract fields instead of inferring intent from prose. The transferable pattern for this policy-writing MVP is not ARIS web/literature tooling, but its contract discipline around prompts, schemas, and review gates.

### Simulated Subagent Reviews

- Query-planning reviewer: current QueryJobs used inline prompts and did not treat `prompts/*.md` as canonical task instructions, making prompt updates invisible to runtime behavior.
- Schema-contract reviewer: `deep_dive` had expected fields in code but no registry schema name, so the retrieval plan could not be audited as a complete schema-backed artifact.
- Boundary reviewer: the change must stay inside NotebookLM query planning; no direct web search, no NotebookLM skill edits, and no API writer expansion are needed.

### Main-Agent Decision

Implement schema-backed query prompts as the highest-value bounded change because it directly improves report-writing reliability before retrieval or drafting. `QueryPlannerAgent` now loads prompt files from `prompts/*.md`, appends an explicit JSON output contract, attaches `schema_name` and `output_contract` to every QueryJob, and gives follow-up jobs the same metadata shape. `PlanReviewerAgent` now treats missing schema metadata as a malformed QueryJob.

This maps to the report-writing goal by making NotebookLM retrieval requests auditable: each hotspot, theme, deep-dive, comparison, impact, and insight query now has a visible schema contract before the material package and section-writing stages consume it.

### Files Changed

- `src/query_planner.py`
- `src/review_gates.py`
- `config/dimension_registry.yaml`
- `docs/optimization_guardrails.md`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from io_utils import load_yaml
from query_planner import build_query_jobs
from review_gates import review_plan
cfg = load_yaml('config/report_task.yaml')
dim = load_yaml('config/dimension_registry.yaml')
contracts = load_yaml('config/section_contracts.yaml')
jobs = build_query_jobs(cfg['task'], dim, contracts, '/tmp/schema_prompt_contract_smoke')
print(len(jobs))
print([job['schema_name'] for job in jobs])
print(all(job.get('output_contract') for job in jobs))
print('prompt_file_text', '提取近期反复出现' in jobs[0]['prompt'])
print('output_contract', jobs[0]['output_contract'])
print(review_plan(jobs, cfg['task'].get('sections', []))['verdict'])
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id schema_prompt_contract_automation_20260526
```

Result:

- Python compile passed.
- Targeted planner smoke produced six QueryJobs with schema names: `hotspot`, `theme_mapping`, `deep_dive`, `comparison`, `impact`, and `insight`.
- Prompt-file text from `prompts/01_hotspot_scan.md` is present in the generated prompt.
- Every QueryJob has an `output_contract`.
- `PlanReviewerAgent` returned `PASS`.
- Full mock workflow completed in `notebooklm_only`.

### Post-Implementation Review

Review subagent critique: the implementation improves prompt/schema auditability without crossing the NotebookLM-only knowledge boundary. It remains intentionally narrow and does not attempt to solve material source tracing or section-contract prose in the same round.

### Known Warnings

- `EvidenceUseReviewerAgent` remains `WARN` because NotebookLM source/citation refs are still not propagated into material packages and claim rows.
- `SectionContractReviewerAgent` remains `WARN` because section drafts still do not explicitly expose every configured output-shape heading.
- `ReportQualityReviewerAgent` remains `WARN` because upstream warnings are surfaced instead of hidden.

### Next Round Target

Propagate NotebookLM source/citation refs into material packages and claim rows, then make final-report appendices expose those refs for human audit.

## 2026-05-25 Round 3: DeepSeek API Provider Defaults

### Main-Agent Decision

Add DeepSeek as an OpenAI-compatible writing provider without storing secrets in the repository. The runtime now treats `deepseek` as an allowed API provider for `api_assisted` writing, with `DEEPSEEK_API_KEY` as the required environment variable, `https://api.deepseek.com` as the base URL, `deepseek-v4-pro` as the default model, and `100000` as the max token setting.

The default workflow remains `runtime_profile: notebooklm_only` and `SectionComposerAgent.driver: codex`, so this change does not trigger live API calls unless the user explicitly switches the writer to API mode.

### Files Changed

- `src/agent_runtime.py`
- `runtime_console.html`
- `config/report_task.yaml`
- `config/report_task.real.yaml`
- `agent.md`
- `docs/codex_agent_writing_architecture.md`
- `docs/optimization_guardrails.md`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from io_utils import load_yaml
from agent_runtime import build_agent_runtime
for path in ['config/report_task.yaml','config/report_task.real.yaml']:
    cfg = load_yaml(path)
    issues = build_agent_runtime(cfg.get('agent_runtime', {})).validate()
    print(path, 'PASS' if not issues else issues)
PY
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 DEEPSEEK_API_KEY=dummy python3 - <<'PY'
from copy import deepcopy
from io_utils import load_yaml
from agent_runtime import build_agent_runtime
cfg = load_yaml('config/report_task.yaml')['agent_runtime']
api_cfg = deepcopy(cfg)
api_cfg['runtime_profile'] = 'api_assisted'
api_cfg['capability_policy'] = {'external_calls': ['notebooklm_cli', 'llm_api'], 'llm_api': True, 'notebooklm_skill_mutation': False}
api_cfg['agents']['SectionComposerAgent']['driver'] = 'api'
print(build_agent_runtime(api_cfg).validate())
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id deepseek_provider_final_smoke
python3 src/runtime_console_server.py --host 127.0.0.1 --port 8791
```

Result:

- Python compile passed.
- Default mock and real configs validate with no runtime issues.
- Synthetic `api_assisted` config with a present `DEEPSEEK_API_KEY` validates.
- Mock workflow completed in default `notebooklm_only` mode without triggering a live API call.
- Runtime console shows DeepSeek as a provider option and displays `deepseek-v4-pro` with `100000` max tokens for `SectionComposerAgent`.

### Known Warnings

- No secret is written to tracked files; runtime validation still requires `DEEPSEEK_API_KEY` to exist in the process environment before a DeepSeek-backed API run.
- No live DeepSeek completion has been run yet in this round.

## 2026-05-25 Round 2: Runtime Profile Split For API-Assisted Writing

### Main-Agent Decision

The earlier boundary was too broad: it treated "only NotebookLM CLI" as if the whole writing workflow could never use an LLM API. The corrected boundary is:

- Knowledge-base access stays NotebookLM CLI only.
- Codex remains the main orchestrator.
- Writing executors may be `codex` or `api` only when `runtime_profile: api_assisted` explicitly enables `llm_api`.
- API writing agents receive only Codex-prepared run artifacts and cannot access NotebookLM, browse, search, or add external facts.

This preserves the anti-drift goal while allowing configurable writing agents.

### Files Changed

- `src/agent_runtime.py`
- `src/section_composer.py`
- `src/runner.py`
- `src/runtime_console_server.py`
- `runtime_console.html`
- `config/report_task.yaml`
- `config/report_task.real.yaml`
- `src/progress.py`
- `agent.md`
- `docs/codex_agent_writing_architecture.md`
- `docs/optimization_guardrails.md`
- `docs/optimization_progress.md`

### Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from io_utils import load_yaml
from agent_runtime import build_agent_runtime
for path in ['config/report_task.yaml','config/report_task.real.yaml']:
    cfg = load_yaml(path)
    print(path, build_agent_runtime(cfg.get('agent_runtime', {})).validate())
PY
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENAI_API_KEY=dummy python3 - <<'PY'
from copy import deepcopy
from io_utils import load_yaml
from agent_runtime import build_agent_runtime
cfg = load_yaml('config/report_task.yaml')['agent_runtime']
bad = deepcopy(cfg)
bad['agents']['SectionComposerAgent']['driver'] = 'api'
print('notebooklm_only_api_driver:', build_agent_runtime(bad).validate())
good = deepcopy(cfg)
good['runtime_profile'] = 'api_assisted'
good['capability_policy'] = {'external_calls': ['notebooklm_cli', 'llm_api'], 'llm_api': True, 'notebooklm_skill_mutation': False}
good['agents']['SectionComposerAgent']['driver'] = 'api'
good['agents']['SectionComposerAgent']['provider'] = 'openai'
good['agents']['SectionComposerAgent']['model'] = 'test-model'
print('api_assisted_api_driver:', build_agent_runtime(good).validate())
bad_calls = deepcopy(good)
bad_calls['capability_policy']['external_calls'] = ['notebooklm_cli', 'web_search']
print('bad_external_calls:', build_agent_runtime(bad_calls).validate())
PY
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.yaml --run-id api_profile_smoke_final
python3 src/runtime_console_server.py --host 127.0.0.1 --port 8790
```

Result:

- Python compile passed.
- Default mock and real configs validate with no runtime issues.
- `notebooklm_only` rejects an API-driven `SectionComposerAgent`.
- `api_assisted` accepts an API-driven `SectionComposerAgent` when provider env and model are present.
- Unsupported external calls such as `web_search` are rejected.
- Mock workflow completed with `agent_runtime_profile: notebooklm_only`.
- Runtime console shows both profiles, editable OpenAI/Anthropic provider metadata, and `SectionComposerAgent` Codex/API routing.
- Runtime console validation reports missing model and missing `OPENAI_API_KEY` when `SectionComposerAgent` is switched to API without complete provider setup.

### Known Warnings

- API execution is currently wired only for `SectionComposerAgent`; review gates remain local deterministic guards.
- The workflow did not perform a live OpenAI/Anthropic completion because no real API key/model was configured in the project defaults.
- Existing report-quality warnings remain: source refs are not yet propagated through materials, section output shapes are still partly implicit, and upstream warnings keep final quality at `WARN`.

### Next Round Target

Wire schema-backed prompt loading and source refs before expanding API execution to additional writing/revision agents. API reviewers should not replace deterministic gates until they can return strict JSON with auditable input hashes.

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

## 2026-05-27 DeepSeek Writing Run Attempt

### Objective

Rerun the education-evaluation report task for `教育评价在人工智能时代的转变` with NotebookLM as the only knowledge gateway and DeepSeek as the API-assisted section-writing executor.

### Main-Agent Decision

Added a separate API-assisted task config instead of mutating the existing NotebookLM-only real config. The new config keeps real-mode NotebookLM CLI retrieval, serial Q&A, all resolved source candidates for source deep dive, and the four source-lane prompts. Only `SectionComposerAgent` is switched to the `deepseek` API driver.

### Files Changed

- `config/report_task.education_evaluation.deepseek.yaml`
- `src/agent_runtime.py`
- `src/notebooklm_adapter.py`
- `src/runner.py`
- `src/section_composer.py`
- `docs/optimization_progress.md`
- `docs/optimization_guardrails.md`

### Validation

```bash
env | rg 'DEEPSEEK|OPENAI|ANTHROPIC' || true
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from io_utils import load_yaml
from agent_runtime import build_agent_runtime
cfg = load_yaml('config/report_task.education_evaluation.deepseek.yaml')
rt = build_agent_runtime(cfg['agent_runtime'])
print(rt.validate())
PY
DEEPSEEK_API_KEY=dummy PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from io_utils import load_yaml
from agent_runtime import build_agent_runtime
cfg = load_yaml('config/report_task.education_evaluation.deepseek.yaml')
rt = build_agent_runtime(cfg['agent_runtime'])
print(rt.validate())
PY
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/*.py
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.education_evaluation.deepseek.yaml --run-id education_evaluation_ai_deepseek_20260527
PYTHONDONTWRITEBYTECODE=1 python3 src/runner.py --task config/report_task.education_evaluation.deepseek.yaml --run-id education_evaluation_ai_deepseek_20260527_retry2
rg '\[[0-9]+\]' runs/education_evaluation_ai_deepseek_20260527_retry2/final_report.md || true
```

Result:

- The current process environment does not expose `DEEPSEEK_API_KEY`.
- Runtime validation blocks the real DeepSeek run with `Missing environment variable for API provider: DEEPSEEK_API_KEY`.
- With a dummy key present, runtime validation returns no issues, confirming the config shape and capability policy are valid.
- Python compile validation passes.
- After a real DeepSeek key was supplied for the process environment, runtime validation passed and the workflow started.
- The run then blocked at `NotebookLMPreflightGate` before retrieval: NotebookLM storage/cookies exist, but token fetch failed with `CSRF token not found in HTML`, source count was `0`, and the run wrote `runs/education_evaluation_ai_deepseek_20260527/RUN_STATUS.md` with status `BLOCKED`.
- After NotebookLM auth was refreshed, `education_evaluation_ai_deepseek_20260527_retry` passed NotebookLM preflight and reached retrieval, but the original 180-second NotebookLM `ask` timeout caused `03_deep_dive` to raise `TimeoutExpired`.
- Added `execution.notebooklm_ask_timeout_seconds` and timeout handling so NotebookLM CLI timeouts become structured command results instead of Python process crashes.
- `education_evaluation_ai_deepseek_20260527_retry` then reached DeepSeek section writing but failed on the first API call with `Connection reset by peer`; a minimal DeepSeek API smoke test with low `max_tokens` succeeded.
- Added API POST retry behavior, reduced `SectionComposerAgent.max_tokens` to `8000`, and compacted the API section prompt inputs.
- `education_evaluation_ai_deepseek_20260527_retry2` completed end-to-end and generated `runs/education_evaluation_ai_deepseek_20260527_retry2/final_report.md`.
- DeepSeek wrote all five section drafts: hotspot, theme, comparison, impact, and insight.
- NotebookLM preflight passed, source list loaded, 5 of 6 base query jobs passed, 1 base impact query returned ERROR, and 16 source-specific deep dive lane jobs completed for 4 selected sources.
- Final report contains no visible NotebookLM `[n]` citation markers.
- Final verdicts: `PlanReviewerAgent`, `NotebookLMPreflightGate`, `MaterialPackAudit`, `MaterialCoverageReviewerAgent`, `EvidenceUseReviewerAgent`, and `DriftReviewerAgent` passed; `RetrievalCompletenessGate` was `BLOCKED`; `SectionContractReviewerAgent`, `ClaimAuditAgent`, `ReportQualityReviewerAgent`, and `KillArgumentAgent` warned.

### Known Warnings

- DeepSeek API-assisted writing is now proven end-to-end, but the run remains non-green because one base NotebookLM query returned ERROR.
- `RUN_STATUS.md` ends as `BLOCKED` because retrieval completeness is non-green, even though a full final report was assembled.
- DeepSeek output improved synthesis quality compared with the local template writer, but section contract and claim-scope gates still warn on implicit/missing expectations and stronger-than-material wording.
- API prompts are now compacted, but future work should make section-specific prompt payloads smaller by passing only the fields each section contract requires.
- User constraint update: NotebookLM single `ask` calls should be capped at 240 seconds. Updated the DeepSeek task config from 600 seconds to 240 seconds; longer retrievals should be treated as structured retrieval errors rather than extended waits.

### Next Round Target

Add a bounded retry/follow-up path for failed base NotebookLM query jobs, starting with `05_impact`, before material-pack assembly. Then improve section-specific API prompt packing so each DeepSeek section receives only its required material slices.
