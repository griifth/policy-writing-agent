// reasoning_dna 蒸馏 · dev↔review 循环模板（配合 distill-reasoning-dna skill）
// 用法：复制本文件，改下面 CONFIG 区，用 Workflow 工具运行（inline script 或 scriptPath）。
// 每轮 dev 写刀 → 新 reviewer 对抗审 → 不过按反馈改 → 至多 4 轮，过线（全硬门 + 分≥85）即停。

export const meta = {
  name: 'distill-reasoning-dna',
  description: '为某体例蒸馏 reasoning_dna 刀，dev↔review 循环到过线',
  phases: [{ title: 'Distill', detail: 'dev↔review 循环' }],
}

// ============ CONFIG（改这里）============
const BASE = '/Users/hujingkai/Documents/New project/example1/strategic_response_workflow'
const REPORT_TYPE = 'trend_review'              // 目标体例（report_modules 下目录名）
const ROUTE = 'route_x'                          // 记录目录名 multiagent_build/<ROUTE>/
const RECOMMENDED_CUTS = 'signal/driver/stage/uncertainty（你勘察金样本后定 2-4 把）'
const GOLD_DIR = `${BASE}/gold_samples/trend_body`   // 该体例的正样本（深稿）
const FOIL_DIR = `${BASE}/gold_samples/shallow_foils` // 浅综述反例（探针判"未答"）
const DRYRUN_ARGS = '--topic "主要国家某领域发展动向" --target-country "主要国家" --strategy-domain "某领域" --notebook-name x'
const PASS_SCORE = 85
const MAX_ROUNDS = 4
// =======================================

const CONVENTIONS = `${BASE}/reasoning_dna/conventions.md`
const CUT_DIR = `${BASE}/report_modules/${REPORT_TYPE}/reasoning_dna`
const MODULE_YAML = `${BASE}/report_modules/${REPORT_TYPE}/module.yaml`

const VERDICT = {
  type: 'object',
  additionalProperties: false,
  properties: {
    pass: { type: 'boolean' },
    score: { type: 'integer' },
    hardGatesFailed: { type: 'array', items: { type: 'string' } },
    feedback: { type: 'string' },
    evidence: { type: 'string' },
  },
  required: ['pass', 'score', 'hardGatesFailed', 'feedback'],
}

const BOUNDARY = `【硬边界】只写 ${CUT_DIR}/<刀>.md + ${MODULE_YAML} 的 reasoning_dna_injection 映射行；禁止改 runner.py、禁止碰其他体例模块或已验证产物；样本只读 ${BASE}/gold_samples/...；不用 API key、不联网；全绝对路径。`

function devPrompt(round, feedback) {
  return `你是 reasoning_dna 刀开发者（体例 ${REPORT_TYPE}）。${BOUNDARY}

## 任务
为 ${REPORT_TYPE} 蒸馏判断刀（推荐：${RECOMMENDED_CUTS}），逐刀写到 ${CUT_DIR}/<刀名>.md，并更新 ${MODULE_YAML} 的 reasoning_dna_injection（step→刀）。

## 先读 & 方法
- 元格式（必读、严格遵守三段式+降级红线）：${CONVENTIONS}
- 完整读金样本逆向抽取"深稿比浅综述多做的推理动作"：${GOLD_DIR}
- 浅综述反例（理解"想浅了"）：${FOIL_DIR}
- 元问题必须**领域无关**（不出现具体选题词）。
- step 用任务 id：assign_material_roles / map_pressure_judgment / plan_article / build_suggestion_pool / prioritize_policy_options，挂到最自然发力的判断步。

${round > 1 ? `## 上一轮审核反馈（逐条回应修订）\n${feedback}\n` : ''}
## 产出
1. 刀文件（绝对路径）+ module.yaml 注入映射。
2. 开发记录 ${BASE}/multiagent_build/${ROUTE}/round_${round}/dev.md（含勘察结论：选哪几刀、从哪几篇抽了什么动作）。
返回总结 + 文件清单。`
}

function reviewPrompt(round) {
  return `你是 reasoning_dna 刀的**对抗式审核员**（体例 ${REPORT_TYPE}），与 dev 不同实例。默认挑刺，不确定即判未过，必须引证。

## 审核对象
${CUT_DIR}/ 下全部刀 + ${MODULE_YAML} 的 reasoning_dna_injection。元格式：${CONVENTIONS}　金样本：${GOLD_DIR}　反例：${FOIL_DIR}

## 硬门（全过才 pass）
1. 三段式完整（必答问题/什么算答到含反例/降级扫描要求）。
2. 元问题领域无关（不出现具体选题词）。
3. 含减法/降级动作（扫描+结论+理由），非"写段分析"。
4. 反例锚点（明确写"什么样算糊弄/未答"）。
5. 探针区分力：亲自拿 1 篇金样本 vs 1 篇反例，用每把刀判据各判一次——金样本"已答"、反例"未答"，区分得开（evidence 写依据）。
6. 注入接通：实跑 dry-run 确认刀被注入且不破坏流程：
   cd "${BASE}/workflow" && python3 runner.py --report-type ${REPORT_TYPE} ${DRYRUN_ARGS} --dry-run
   grep 最新 runs/ 的对应判断步 generated_prompts 是否含锚点"本步必答逼问"+刀内容；确认 16 步 done、无 traceback。

打分(0-100)，列未过硬门，给可执行修改指令(引证)。写审核记录 ${BASE}/multiagent_build/${ROUTE}/round_${round}/review.md。返回结构化结论。`
}

phase('Distill')
let feedback = ''
let last = null
let result = null
for (let n = 1; n <= MAX_ROUNDS; n++) {
  await agent(devPrompt(n, feedback), { label: `${REPORT_TYPE}:dev:r${n}`, phase: 'Distill', agentType: 'general-purpose' })
  const v = await agent(reviewPrompt(n), { label: `${REPORT_TYPE}:review:r${n}`, phase: 'Distill', agentType: 'general-purpose', schema: VERDICT })
  last = v
  if (v && v.pass && v.score >= PASS_SCORE && (!v.hardGatesFailed || v.hardGatesFailed.length === 0)) {
    result = { status: 'passed', round: n, score: v.score, verdict: v }
    break
  }
  feedback = v ? `分数 ${v.score}；未过硬门：${(v.hardGatesFailed || []).join('；')}；修改指令：${v.feedback}` : '（审核无返回，自检三段式+降级红线+探针）'
  log(`${REPORT_TYPE} 第 ${n} 轮：score=${v ? v.score : 'NA'} pass=${v ? v.pass : 'NA'}`)
}
if (!result) result = { status: 'maxed', round: MAX_ROUNDS, score: last ? last.score : null, verdict: last }
return result
