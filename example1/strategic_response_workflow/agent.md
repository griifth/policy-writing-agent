# Agent Instructions

## Scope Boundary

This workflow is a standalone project for writing policy analysis articles of the type:

`Target-country strategy analysis + China response recommendations`.

The agent may operate only inside this workflow directory when building or running this workflow.

- Do not modify the source example document outside this directory.
- The copied example document under `source/sample.docx` may be read and converted.
- Use relative paths in workflow documentation, prompts, and run logs.
- NotebookLM may be called for retrieval, but the NotebookLM skill and external notebooks must not be modified.
- Generated run artifacts must be written under `runs/`.

## Workflow Goal

Build a reusable workflow that accepts:

1. A report topic.
2. A target country or actor.
3. A strategy domain.
4. A NotebookLM knowledge base name.
5. Optional China response focus areas.

The workflow should produce a policy article that analyzes the target country's strategic layout in the selected domain and proposes China-oriented response strategies.

The test case is:

- Topic: `中美AI人才竞争及应对策略`
- Target country: `美国`
- Strategy domain: `AI人才`
- NotebookLM knowledge base: `中美人才`

This test case must not hard-code the workflow. Prompts and code should remain reusable for other target countries and strategy domains.

## Article Type

The article is not a general international comparison report. It should follow this logic:

1. Why the target-country strategy matters.
2. What strategic goals the target country is pursuing.
3. What policy tools and implementation mechanisms are used.
4. What pressure, risks, or constraints this creates for China.
5. What structural gaps China faces in the same domain.
6. What concrete response strategies China should adopt.

## Prompt Categories

Prompts are divided into:

- Retrieval.
- Task redefinition.
- Material role assignment.
- Pressure-judgment mapping.
- Argument-chain planning.
- Suggestion pool generation.
- Policy priority sorting.
- Writing.
- Review.
- Revision.

The prompts should guide the LLM to act like a policy expert and writing expert, not a material summarizer.

## Agent Role Boundary

Codex is the workflow orchestrator. It is responsible for:

- Triggering NotebookLM retrieval.
- Passing files and prompts between modules.
- Maintaining task state and run logs.
- Checking outputs and deciding whether another review/revision loop is needed.

Writing LLM modules are responsible for bounded tasks only:

- Retrieval materials come from NotebookLM.
- Judgment nodes produce task definition, material roles, pressure mapping, suggestion pool, and priority order.
- Writing nodes draft and revise the article.
- Review nodes must explicitly judge recommendation rationality and may require rewriting.

No agent should modify NotebookLM skill code, source example files outside this workflow, or adjacent project directories.

## Evidence Rules

- Use NotebookLM retrieval outputs as the main evidence boundary.
- Do not invent target-country policies, institutions, years, laws, programs, or measures.
- If source evidence is missing, mark the gap or weaken the claim.
- Distinguish between facts, judgments, and recommendations.
- The article should analyze and advise, not merely list materials.

## Iteration Rule

After the workflow produces a draft, compare it with the example article on:

- Structure.
- Strategic judgment.
- Material use.
- China problem orientation.
- Recommendation quality.
- Policy writing style.

If the generated article does not reach the example standard, revise prompts or workflow steps and rerun the weak modules until the article is comparable to or better than the example.

Review must not pass a draft merely because the structure is complete. It must check whether each recommendation is reasonable:

- Does it respond to a real pressure identified earlier?
- Is the policy object correct?
- Is the policy tool suitable for China's institutional context?
- Is the recommendation prioritized appropriately?
- Are risks and side effects acknowledged?
- If a recommendation is directionally correct but object/tool mismatched, it must be rewritten, not polished.
