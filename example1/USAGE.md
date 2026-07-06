# 全流程使用指南（从选题到成稿）

本指南把整个项目串成一条可操作的流水：**⓪ 写作前澄清 → ① 搜资料/检索成料 → ② 跑写作引擎（内置评分门）→ ③ 终审与外审**。各引擎的启动细节见 [`report-workflow-runbook/SKILL.md`](report-workflow-runbook/SKILL.md)，环境初始化见 [`README.md`](README.md)。

> 2026-07-05 起的三处大变化：**写作前澄清**（report-clarify skill，五问点选后自动拼命令）、**评分门**（不达标自动带意见返修，以 `quality_rubric.md` 六维为唯一标尺）、**教科院终审**（`--review-scope jiaokeyuan_final_review`，三遍读法判分）。

## 全景

```
模糊主题/明确问题
  │
  ▼  ⓪ 写作前澄清（report-clarify skill：预检索→候选问题→五问点选→拼命令，你拍板）
clarify_decision.md + 完整启动命令
  │
  ▼  ① 搜资料 + 检索成料（三条路殊途同归到同一料包契约）
retrieval_outputs/*.md（二段式料包）
  │
  ▼  ② 跑写作引擎：判断(推理刀+共享词汇) → 构思 → 写作(文风DNA+机构落点+读者站位)
  │                → 审查评分门（六维打分，不达标自动返修，max-iterations 兜底）
runs/<id>/final_article_reviewed.md + .docx + review_gate_result.json
  │
  ▼  ③ 终审与外审（教科院终审 scope / 单篇打分工具 / 建议外部审计）
成稿
```

---

## ⓪ 写作前澄清（模糊主题 → 可执行命令）

对 agent 说「**帮我定题 / 写报告前澄清**」即触发 [`report-clarify`](report-clarify/SKILL.md)：

1. **路线判定**：问题已明确 → 直接进五问；只有兴趣领域 → 先预检索（3–5 条权威线索，不出全料包）→ 凝练 3–5 个候选研究问题（标注各自契合的体例）供点选。
2. **五问点选**：Q1 目标读者层级（国家领导/部党组/司局）｜ Q2 体例（选项就是引擎能跑的类型）｜ Q3 核心观点 ｜ Q4 维度逻辑 ｜ Q5 风格子型。
3. **回填**：产出 `clarify_decision.md` 并**自动拼好完整启动命令**（Q1→`--audience-level`，Q2→`--report-type` 或根引擎，Q5→`--style-subtype`），你确认后执行。

原则：自动判定只做**预填默认项**，一切由你点选拍板——绕开"AI 判不准"。题目和体例都已明确时可跳过本步，直接照 §② 手拼命令。

---

## ① 搜资料 + 检索成料（研究问题 → 料包）

三条路殊途同归到同一份契约：

| 路径 | 怎么做 | 何时用 |
|---|---|---|
| **NotebookLM** | 引擎按 `--notebook-name` 运行时现查现铺 | 自有知识库已覆盖该主题 |
| **topic-material-search**（skill） | 与你共定 `search_plan` → 并行子 agent 网搜 → DeepSeek 复审循环 → 出料包 | 库里没有 / 要公网权威可溯源源 |
| **复用料包** | 直接 `--reuse-materials-run <run-id>` | 已有现成 `retrieval_outputs/` |

**产出（唯一契约）**：`retrieval_outputs/<type>.md`，二段式（`一、检索内容` / `二、相关文献`），文件名对齐所选体例的 `retrieval_types`。

---

## ② 跑写作引擎（料包 → 过了评分门的初稿）

### 识别体例（⓪ 已点选的可跳过）

| 题材 | 用哪个 |
|---|---|
| 国际比较（逐章横比多国做法） | **根引擎** `workflow/`（暂无推理刀与评分门） |
| 战略竞争 + 中国应对 | strategic · `--report-type strategic_response` |
| 国际经验借鉴 + 启示 | strategic · `experience_response` |
| 趋势研判 + 对策 | strategic · `trend_review` |
| 没有合适体例 | 先用 `distill-report-module` skill 从范文造新体例再跑 |

### 跑引擎

```bash
# 战略引擎（在其目录下）
cd strategic_response_workflow
python3 workflow/runner.py --report-type experience_response \
  --topic "..." --target-country "..." --strategy-domain "..." \
  --notebook-name "<库名>" \            # 或 --reuse-materials-run <id>
  --audience-level moe_leadership       # 可选：读者站位三档，不选则零注入

# 根引擎
python3 workflow/runner.py --topic "..." --notebook-name "<库名>"
```

战略引擎内部自动流水：**检索 → 判断（推理刀 + shared_schema 统一证据分级/词表/强度门）→ 构思 → 写作（文风 DNA·仓根真源 + 机构落点 + 读者站位）→ 审查评分门**。

**评分门（新）**：审查报告末尾带六维评分 JSON（标尺=`strategic_response_workflow/quality_rubric.md`）。**1 档（总分 ≥85 且六项硬伤零命中）才算合格放行**；不达标自动带审查意见返修再评，到 `--max-iterations` 上限带病定稿并留痕 `review_gate_result.json`（每轮 grade/total/硬伤可查）。

中断可 `--continue` / `--resume`（strategic）或 `--resume-run`（根）。**产出**：`runs/<id>/final_article_reviewed.md` + `.docx`，以及本次所用全部规则的快照（文风+评分标尺 / 推理刀+共享词汇 / 机构 / 读者站位）。

---

## ③ 终审与外审（初稿 → 成稿）

按需三选（可叠加），前两个是本轮新增：

| 方式 | 干什么 | 怎么用 |
|---|---|---|
| **教科院终审（引擎内 handoff）** | 教科院终审人三遍读法（领导速读→范式六查→防伪六查），按 rubric 判档、给"最像哪个盲测锚点/离上一档差什么/改文字还是须重构" | 启动时加 `--reviewer handoff --review-scope jiaokeyuan_final_review`，暂停后由在场 agent 派子 agent 审，写报告后 `--resume` |
| **单篇打分工具（体外，任何稿件）** | 同一终审人格 + rubric 出评分报告与 JSON | `python3 tools/score_article.py --article <稿件.md>` |
| **audit-extend-suggestions**（skill） | 对成稿的对策建议联网核查防重/补深/找空白；不写回正文 | 把 `final_*.md` 交给该 skill |

handoff 还有另外三把尺子可选：`style_and_expression`（文风）、`reasoning_compliance`（推理对账，对照判断步降级留痕）、`audience_alignment`（读者站位互校验）。`jiaokeyuan-researcher` skill 仍可用于体外整篇审改/改写（终审 scope 即其审稿化身）。

---

## 一条最短可用路径

```
⓪ 对 agent 说"帮我定题：<你的模糊主题>" → 点选五问 → 拿到拼好的命令
① 命令里若走 topic-material-search，先出料包记下 run-id
② 执行命令（评分门自动把关：不达标自动返修，留痕 review_gate_result.json）
③ 取 runs/<id>/final_article_reviewed.docx；
   要更严 → tools/score_article.py 复核档位，或 handoff 教科院终审；
   建议块 → audit-extend-suggestions 防重/补深 → 定稿
```
