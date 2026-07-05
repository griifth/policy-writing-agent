---
name: report-clarify
description: >-
  写报告前的探索式澄清（S1）：用户只有模糊主题或兴趣领域时，先预检索 3–5 条权威线索，
  凝练候选研究问题供点选，再走"写作前五问"（读者层级/体例/核心观点/维度逻辑/文风子型），
  最后拼出可直接执行的工作流启动命令。自动判定一律只做预填默认项，拍板权在用户。
  触发词：写报告前澄清、帮我定题、只有模糊主题、选体例、写作前五问、探索性追问、
  不知道写什么题目、把兴趣领域变成研究问题。用户说"想写XX方向但没想好具体问题"也应触发。
---

# 写作前澄清（Report Clarify）

把"模糊主题"变成"可启动的写作任务"：路线判定 → 预检索 → 候选问题点选 → 五问点选 → 拼命令启动。
本 skill **不改引擎、不产料包、不代替检索工作流**——它只负责启动前的澄清与决策记录。

仓库根：`/Users/hujingkai/Documents/New project/example1`（下称 `<ROOT>`，路径含空格，命令必须加引号）。

## 总原则（会议共识，不可违背）

- **自动判定只做预填默认项，用户拍板**。体例、读者层级、研究问题都可能被 AI 判错——所以一切判定只作为 AskUserQuestion 的推荐默认项呈现，由用户点选确认。"判不准"的风险由此绕开。
- **拿不准一律走追问**：无法确定用户问题是否已明确时，缺省走预检索追问路线，宁多问一步。
- **证据不足如实标注**：预检索搜不到就写"线索不足"，不硬凑、不编造来源。

## 流程（五步，判定逻辑详见 [references/clarify_scope.md](references/clarify_scope.md)）

### ① 路线判定

读用户输入，按 clarify_scope 的判据分流：
- **问题已明确**（有明确对象国/领域/落点，能直接回答"研判什么、写给谁"）→ 跳到 ④ 五问清单。
- **仅有兴趣领域/模糊主题**（如"想写 AI 教育方向""关注人才竞争"）→ 走 ②。
- **拿不准 → 一律走 ②**（缺省追问兜底）。

### ② 预检索（浅采集，复用 topic-material-search 的纪律）

只做**浅采集**，不出全料包：
- 围绕主题搜 **3–5 条权威线索**（T1 官方政策/国际组织/官方统计优先，T2 学术次之），每条带 `(机构, 文件/报告名, 年份, URL)` 与证据状态标签——溯源纪律同 `topic-material-search/references/sourcing-standard.md`。
- 可由你直接 WebSearch，或派一个 collector 子 agent；**不建 retrieval_outputs、不跑 DS 审校循环**（那是 topic-material-search 的全量模式，等任务定题后再用）。
- 搜不满 3 条 → 如实向用户标注"该方向公开线索不足"，列出已找到的，不硬凑。

### ③ 凝练候选研究问题

基于预检索线索，凝练 **3–5 个候选研究问题**（凝练要点见 clarify_scope）：
- 每个候选问题**标注契合哪种体例**（战略应对/经验借鉴/趋势研判/国际比较）及一句理由。
- 用 **AskUserQuestion** 呈现点选（含"都不合适，我重新描述"逃生选项）；用户选定后进 ④。

### ④ 五问清单（AskUserQuestion，逐问点选；已明确路线从这里进入）

逐问呈现，每问给推荐默认项（依据见 clarify_scope），用户可改：

| # | 问题 | 选项（选项值即引擎参数值） |
|---|---|---|
| Q1 | 目标读者层级 | `national_leader` 国家领导/宏观战略 ｜ `moe_leadership` 部党组/中观制度 ｜ `bureau` 司局/微观操作 |
| Q2 | 研究目的与体例 | `strategic_response` 战略应对 ｜ `experience_response` 经验借鉴 ｜ `trend_review` 趋势研判 ｜ `intl_comparison` 国际比较（根引擎） |
| Q3 | 核心观点或初始判断 | 用户一句话输入；可选"暂无，由检索归纳" |
| Q4 | 维度逻辑 | 如 顶层设计×实施机制 ｜ 宏观/中观/微观 ｜ 举措→趋势→对策 ｜ 用户自拟 |
| Q5 | 文风子型 | `auto`（按体例自动）｜ `a` 战略建议/预警 ｜ `b` 机制/趋势综述 |

- Q2 前三个选项**就是 `strategic_response_workflow/report_modules/` 目录名**，直接作 `--report-type`；`intl_comparison` 路由到根引擎。若 `report_modules/` 日后出现国际比较体例目录，国际比较改走 strategic 引擎该体例。
- Q3 选"暂无"合法——流水线的 redefine_task 步会从材料归纳判断。

### ⑤ 回填与启动

1. **落盘 `clarify_decision.md`**：先写临时位置（如 `/tmp/clarify_decision_<slug>.md`），格式三节——五问答案（Q1–Q5 及理由）／候选研究问题（含未选中的，备改题）／预检索线索（3–5 条带溯源）。启动后 run 目录生成，即拷入 `runs/<run-id>/clarify_decision.md` 归档。
2. **拼完整启动命令**（参数细节按 `report-workflow-runbook/SKILL.md` 核对，不臆造）：
   - **Q2 = `intl_comparison` → 根引擎**（在 `<ROOT>` 下）：
     `python3 workflow/runner.py --topic "<定稿题目>" --notebook-name "<知识库名>"`
     （根引擎无 `--report-type/--audience-level/--style-subtype`；Q1/Q4/Q5 记入 clarify_decision.md 供写作与终审参考。）
   - **其余 → strategic 引擎**（在 `<ROOT>/strategic_response_workflow` 下）：
     `python3 workflow/runner.py --topic "<定稿题目>" --target-country "<对象国>" --strategy-domain "<领域>" --notebook-name "<知识库名>" --report-type <Q2值> --audience-level <Q1值> --style-subtype <Q5值>`
     （`--target-country/--strategy-domain` 从选定的研究问题里抽；材料走网搜料包时按 runbook 用 `--reuse-materials-run`。）
3. Q3/Q4 进入流水线的通道是**题目措辞**：把核心判断与维度逻辑凝进 `--topic` 的表述（如"美国AI人才战略布局（顶层设计×实施机制）及我国应对"），不改引擎。
4. **把命令与 clarify_decision.md 摘要一并呈现给用户确认，确认后才执行**；建议先 `--dry-run` 自检再真跑（runbook 第 7 节）。

## 边界

- 本 skill 到"命令启动"为止；跑流水线的中断续跑、失败处置归 `report-workflow-runbook`。
- 全量检索料包归 `topic-material-search`（定题之后需要网搜材料时再触发它）。
- 不猜测知识库名：用户未提供 `--notebook-name` 且不用料包复用时，直接问。
