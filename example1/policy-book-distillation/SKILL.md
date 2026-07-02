---
name: policy-book-distillation
description: Distill policy research books, monographs, chapters, PDFs, TXT, DOCX, notes, and online previews into reusable analytical methods and implicit thinking models. Use when the user asks to 提炼政策研究书籍的方法, 蒸馏作者隐含思考模型, 从政策分析著作中抽取框架, 把一本书转成可复用 prompt 或 skill, or compare how different policy authors frame problems, mechanisms, implementation, and evaluation. Prefer full local text; if only TOC, previews, or summaries are available, produce a clearly labeled low-confidence structural distillation only.
---

# Policy Book Distillation

Turn policy research books into reusable analytical machinery rather than ordinary summaries.

## Operating Standard

Treat the task as method extraction plus model inference.

- Extract `显性方法` from what the text states directly.
- Infer `隐含模型` only from repeated structure, recurring contrasts, choice of evidence, and durable omissions.
- Separate evidence from inference every time.
- State confidence from source coverage, not from rhetorical certainty.

Do not impersonate the author. Use formulations such as `基于该书可提炼出` or `从作者反复使用的论证路径看`.

## Workflow

Follow this sequence unless the user explicitly asks for a narrower output.

1. Assess source quality and coverage.
2. Build a basic record for the material actually seen.
3. Extract explicit analytical method.
4. Infer the implicit thinking model.
5. Convert findings into the requested reusable artifact.
6. Label confidence, blind spots, and transfer limits.

Read the referenced file only when that step is active:

- Source assessment: [references/source-assessment.md](references/source-assessment.md)
- Extraction fields: [references/extraction-schema.md](references/extraction-schema.md)
- Inference rules: [references/implicit-model-rules.md](references/implicit-model-rules.md)
- Output formats: [references/output-templates.md](references/output-templates.md)

## Step 1: Assess Source Before Interpreting

Classify coverage first:

- `A`: full or near-complete text
- `B`: several substantial chapters or long excerpts
- `C`: preface/introduction/conclusion plus TOC
- `D`: metadata, review, or short preview only

Then classify the source form:

- single-author policy analysis book
- policy process or governance theory book
- comparative policy book
- case-based monograph
- edited volume
- practitioner handbook
- ideological or advocacy-oriented book

Handle limits strictly:

- For `C`, infer probable architecture but avoid strong claims about blind spots or hidden method unless repeated evidence exists.
- For `D`, do discovery and tentative orientation only. Do not claim a real hidden-model distillation.
- For edited volumes, separate editor framing from chapter-author method.

## Step 2: Build The Record

Use [references/extraction-schema.md](references/extraction-schema.md) as the default record shape.

Always capture:

- exact materials used
- coverage level
- chapter or section evidence anchors
- unknown fields that remain unknown

If local text exists, search targeted terms before broad rereading. Useful seed patterns include:

```bash
rg -n "政策过程|政策工具|实施|评估|机制|治理|制度|比较|案例|方法|框架" <text-files>
```

## Step 3: Extract Explicit Method

Prioritize signals that the book states or formalizes:

- named frameworks, stages, typologies, or models
- definitions of policy problem, actors, institutions, tools, implementation, evaluation
- repeated analytical verbs such as `解释/比较/评估/设计/治理/协调/执行`
- chapter architecture that repeats the same analytical order
- explicit recommendations about how policy research should be done

When evidence is weak, write `未见充分证据` instead of filling gaps with plausible guesses.

## Step 4: Infer The Implicit Thinking Model

Read [references/implicit-model-rules.md](references/implicit-model-rules.md) before inferring.

Infer only from repeated evidence. Look for:

- default unit of analysis
- preferred explanatory starting point
- favored evidence type
- where agency is placed
- recurring tradeoffs
- what the author compresses or leaves undertheorized
- how policy recommendations are generated from diagnosis

Always keep this separation visible:

- `显性方法`: directly stated or formally named
- `隐含模型`: inferred from repeated textual behavior

## Step 5: Convert Findings Into Reusable Outputs

Use [references/output-templates.md](references/output-templates.md) and emit only the formats the user needs.

Default priority order:

1. one-sentence thesis of the method
2. explicit framework
3. implicit thinking model
4. reusable heuristics
5. boundaries and failure modes
6. evidence basis and confidence

Common deliverables:

- single-book method card
- author thinking model card
- cross-book comparison matrix
- reusable policy-analysis prompt
- skill seed draft
- literature review backbone

## Step 6: Label Confidence And Transfer Limits

Use confidence labels that match evidence quality:

- `high`: full text or broad chapter coverage with repeated stable signals
- `medium`: substantial excerpts with stable recurring patterns
- `low`: previews, TOC, reviews, or scattered passages only

Also state:

- what could not be verified
- what may reflect genre rather than author method
- where transfer to another policy domain may fail

## Heuristics Specific To Policy Books

Check these slots whenever evidence allows:

- problem framing
- actor map
- institutional arrangement
- policy instruments
- mechanism or causal chain
- implementation logic
- evaluation criteria
- historical or comparative baseline
- hidden normative assumption
- implied recommendation generator

If the book is rhetorically strong but methodologically thin, say so directly.

## Multi-Book Use

When working across multiple books:

1. Normalize every book with the same extraction schema.
2. Compare units of analysis before comparing conclusions.
3. Compare definitions of effective policy or good governance.
4. Compare omissions and compression patterns.
5. Synthesize only after disagreement is preserved.

Do not merge books too early into one generic policy-cycle summary.

## Output Rules

- Prefer Chinese unless the user asks otherwise.
- Quote only short source phrases when necessary.
- Name the exact chapter, section, or file behind major claims when possible.
- Mark provisional results clearly when coverage is partial.
- Avoid biography, fandom, and style imitation. Produce reusable analytical machinery.
