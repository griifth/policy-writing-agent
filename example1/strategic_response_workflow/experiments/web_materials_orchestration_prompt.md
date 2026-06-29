# 交接提示词：网络搜集权威资料 → 自检索 → experience_response 写作 → 与原文对比

> 把本文件整体作为任务交给一个具备 WebSearch / WebFetch / Bash / Write / Agent 能力的 Claude 编排 agent。
> 它不依赖本对话的任何记忆，所有路径、命令、标准都写在下面。

---

## 0. 你的身份与总目标

你是一个编排 agent。目标：**不使用 NotebookLM**，由你自己从网络搜集权威资料、自行从中检索信息、整理成工作流所需的检索材料，然后调用已有的 `experience_response` 写作工作流生成一篇“国际经验借鉴 + 中国应对”政策文章，最后与一篇人类原文对比，给出差距报告。

分工：**你（Claude）负责搜集、检索、整理材料、编排、写 retrieval_outputs、跑工作流、最后对比；审核用 DeepSeek（DS）做一个轻量审核器。**

## 1. 本次题目（可替换）

- 主题(topic)：美英德澳体育教师培养与聘任的经验及我国借鉴
- 参照国家/地区(target-country)：美国、英国、德国、澳大利亚
- 政策领域(strategy-domain)：体育教师培养与聘任
- 中国应对主题(china-response-focus)：体育教师队伍建设

## 2. 环境与关键路径（务必照用）

- 项目根：`/Users/hujingkai/Documents/New project/example1/strategic_response_workflow`
- 工作流入口：`workflow/runner.py`（运行前先 `cd` 进 `workflow/` 目录，否则内部 import 失败）
- DeepSeek 已配置好：`strategic_response_workflow/.env` 内有 key；在 `workflow/` 目录下可一行调用（见 §5）。
- 材料目录契约：工作流通过 `--reuse-materials-run <id>` 复用 `runs/<id>/retrieval_outputs/` 下的 6 个文件。
- 体例模块：`report_modules/experience_response/`（检索类型、提示词都在里面，你不用改它）。
- 对比用人类原文（**只在最后一步 §7 打开，前面绝不要读它，避免抄袭/趋同**）：
  `/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md/美英德澳培养与聘任体育教师的做法和特点.md`

## 3. 六类检索材料（你最终要产出的东西）

在 `runs/web-materials-<自取一个短id>/retrieval_outputs/` 下产出**正好这 6 个文件名**（对应 experience_response 的 retrieval_types）：

1. `practice_background.md` —— 政策领域的问题背景与各国总体情况
2. `key_practices.md` —— 各国具体政策做法与工具
3. `enabling_conditions.md` —— 做法背后的成因、制度条件、国情前提
4. `effectiveness_evidence.md` —— 实施效果/有效性证据（含证据状态）
5. `china_status_and_gaps.md` —— 中国现状、短板与制度约束
6. `adaptation_evidence.md` —— 可迁移性与中国适配的依据

每个文件的格式：

```
一、检索内容

<按要点组织的事实；每条关键事实后用括号标出处：(发布机构, 文件/报告名, 年份, URL)，
 并标注证据状态：[已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]>

二、相关文献

- <标题> | <机构> | <年份> | <类型:法规/报告/统计/研究> | <权威分级 T1/T2> | <URL>
- ...
```

**硬规则**：只写你**真的搜到、能溯源**的信息；不得凭模型记忆编造数据、机构、年份或链接。反扒/付费打不开正文的，就只保留信息源 URL 与可见的摘要，并标注 `[未取全文]`。

## 4. 总流程

```
Phase 1  搜集↔审核 微循环（核心，见 §5）
Phase 2  把通过审核的材料落成 §3 的 6 个文件
Phase 3  跑 experience_response 工作流（§6）
Phase 4  与人类原文对比，出差距报告（§7）
```

## 5. Phase 1：搜集↔审核 微循环

反复执行下面三步，直到 DS 审核判定“通过”，或达到上限 4 轮：

### 5a 搜集（你做）
- 用 WebSearch（学术类可用 ai4scholar MCP，若可用）按国家 × 6 类检索角度搜索权威源。
- 优先权威源：各国教育部/部委官网、师范教育与教师资格主管机构、OECD（如 TALIS 教师调查）、UNESCO、本领域同行评议研究、官方统计。
- 对每条有用的信息，记录：事实要点 + 出处(机构/报告名/年份/URL) + 证据状态。
- 第一轮尽量覆盖全部 4 国 × 6 类；后续轮只补 DS 指出的缺口。

### 5b 审核（用 DeepSeek，见 §5 的调用方式 + §8 审核标准）
- 把“当前已搜集的材料汇总 + §8 审核标准”写进一个临时文件，调用 DS，让它按标准逐类判定并输出缺口清单。

### 5c 补充（你做）
- 若 DS 判“未通过”，就针对它列出的缺口做定向补搜，回到 5b。
- 若“通过”，进入 Phase 2。

### DeepSeek 审核器调用方式（轻量，无状态）
在 `workflow/` 目录下执行（把审核输入写进 `/tmp/review_in.txt`）：

```bash
cd "/Users/hujingkai/Documents/New project/example1/strategic_response_workflow/workflow"
python3 -c "
from llm_client import create_llm_client
c = create_llm_client('deepseek')
print(c.ask(open('/tmp/review_in.txt', encoding='utf-8').read()))
"
```

`/tmp/review_in.txt` 的内容 = §8 的审核标准全文 + 「【待审材料】」+ 你当前搜集到的全部材料文本。DS 的返回就是审核结论，你据此决定继续补充还是放行。

## 6. Phase 3：跑写作工作流

材料落盘后，执行：

```bash
cd "/Users/hujingkai/Documents/New project/example1/strategic_response_workflow/workflow"
python3 runner.py \
  --report-type experience_response \
  --topic "美英德澳体育教师培养与聘任的经验及我国借鉴" \
  --target-country "美国、英国、德国、澳大利亚" \
  --strategy-domain "体育教师培养与聘任" \
  --china-response-focus "体育教师队伍建设" \
  --notebook-name "web-collected" \
  --llm-provider deepseek \
  --reuse-materials-run web-materials-<你的id>
```

（`--notebook-name` 必填但复用材料时不会真的调用 NotebookLM，填任意占位即可。）
跑完后，生成的文章在最新的 `runs/run-*/final_article_reviewed.md`。

## 7. Phase 4：与人类原文对比

**到这一步才打开** §2 给的人类原文。对比维度：结构、模式归类、成因解释、有效性与证据状态区分、共性/个性区分、中国短板与差距、借鉴建议质量（是否带迁移前提）、文风、证据严谨（出处）。
输出一份《差距报告》：我们的稿 vs 人类原文，逐维度判优劣，并指出我们这套“网络自采集 + 工作流”链条的明显短板和可改进点。

## 8. 审核标准（DS 审核器据此判定，必须严格执行）

> 输出要求（让 DS 这样输出）：逐类给【达标/不达标】+ 缺口；最后给【总判定：通过 / 继续补充】+ 若继续补充，给出“下一轮补搜清单”。

### A. 信息源标准
1. **权威分级**：每个源标 T1（官方政策/法规、国际组织报告如 OECD/UNESCO、官方统计）/ T2（同行评议研究）/ 剔除（博客、百科、二手转述、无出处、疑似 AI 生成）。
2. **覆盖度**：4 个参照国家是否都有 T1 或 T2 源；6 类检索是否每类都有实质来源。
3. **出处完整**：每个源是否有 机构 + 文件/报告名 + 年份 + URL；缺项的降级。
4. **时效**：政策类优先近 5–8 年；历史背景类可放宽但需标年份。

### B. 检索信息质量标准
1. **可溯源**：每条关键事实是否带出处，能否回到具体来源；不可溯源的判为不可用。
2. **证据状态**：是否标注 [已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]；把意图/转述当成熟经验的，判不达标。
3. **充分性**：6 类是否都有足以支撑写作的实质内容——尤其 `key_practices`（各国做法可归出 2–3 种模式）、`effectiveness_evidence`（至少部分做法有评估数据，而非全是意图）、`china_status_and_gaps`（有中国侧现状与短板）。
4. **无幻觉**：是否存在看起来精确但无来源的数字、机构、年份；有则必须剔除或降级。

### C. 通过线
- 4 国均有 ≥1 个 T1/T2 源；6 类均“达标”；`effectiveness_evidence` 至少有 2 条带评估数据的有效性证据；无未溯源的精确数字残留。
- 任一不满足 → 总判定“继续补充”，并给出具体缺口。

## 9. 全局约束

- 不用 NotebookLM。
- 权威 + 出处强制；只用真实搜到、可溯源的信息；反扒的只留 URL。
- 审核用 DS；搜集/检索/整理/编排/对比用你（Claude）。
- 不臆造数据。拿不准的信息宁可标“未取全文/待核”，不要写成既成事实。
- 注意：本链条是自动化试验，人工核验仍建议在事后对 `retrieval_outputs/` 与差距报告做抽检。
