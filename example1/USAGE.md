# 全流程使用指南（从选题到成稿）

本指南把整个项目串成一条可操作的流水：**搜资料 → 检索成料 → 识别体例 + 组织写作 → 教科院 skill 审核优化**。各引擎的启动细节见 [`report-workflow-runbook/SKILL.md`](report-workflow-runbook/SKILL.md)，环境初始化见 [`README.md`](README.md)。

## 全景

```
研究问题
  │
  ▼  ① 搜资料 + 检索成料（研究问题拆成检索维度 → 取材料）
retrieval_outputs/*.md（二段式料包）
  │
  ▼  ② 识别体例（选引擎/report-type）+ 跑写作引擎
runs/<id>/final_*.md + .docx（初稿）
  │
  ▼  ③ 教科院 skill 审核优化（体外人味外审）
成稿
```

---

## ① 搜资料 + 检索成料（研究问题 → 料包）

"搜资料"与"检索问题"是一件事的两面：先把研究问题拆成检索维度，再按维度取材料，落成料包。三条路殊途同归到同一份契约。

| 路径 | 怎么做 | 何时用 |
|---|---|---|
| **NotebookLM** | 引擎按 `--notebook-name` 运行时现查现铺（要素路由→盘点→聚类→深挖→建议，见 `材料获取工作流/`） | 自有知识库已覆盖该主题 |
| **topic-material-search**（skill） | 与你共定 `search_plan` → 并行子 agent 网搜 → DeepSeek 复审循环 → 出料包 | 库里没有 / 要公网权威可溯源源 |
| **复用料包** | 直接 `--reuse-materials-run <run-id>` | 已有现成 `retrieval_outputs/` |

**产出（唯一契约）**：`retrieval_outputs/<type>.md`，二段式（`一、检索内容` / `二、相关文献`），文件名对齐所选体例的 `retrieval_types`。

---

## ② 识别体例 + 组织写作（料包 → 初稿）

### 识别体例（选引擎 / report-type）
| 题材 | 用哪个 |
|---|---|
| 国际比较（逐章横比多国做法） | **根引擎** `workflow/` |
| 战略竞争 + 中国应对 | strategic · `--report-type strategic_response` |
| 国际经验借鉴 + 启示 | strategic · `experience_response` |
| 趋势研判 + 对策 | strategic · `trend_review` |
| 没有合适体例 | 先用 `distill-report-module` skill 从范文造新体例再跑 |

### 跑写作引擎
```bash
# 战略引擎（在其目录下）
cd strategic_response_workflow
python3 workflow/runner.py --report-type experience_response \
  --topic "..." --target-country "..." --strategy-domain "..." \
  --notebook-name "<库名>"          # 或 --reuse-materials-run <id>

# 根引擎
python3 workflow/runner.py --topic "..." --notebook-name "<库名>"
```
引擎内部自动流水：**检索 → 构思（判断刀 + ch0 战略态势卡）→ 写作（文风 DNA + 机构落点）→ 自审 → 改写 → 导出 docx**。中断可 `--continue` / `--resume`（strategic）或 `--resume-run`（根）。

**产出**：`runs/<id>/final_*.md` + `.docx`。

---

## ③ 教科院 skill 审核优化（初稿 → 成稿）

引擎自审是"体内"的；这一层是**体外的人味外审**，不自动跑，对成稿二次打磨：

| Skill | 干什么 |
|---|---|
| **jiaokeyuan-researcher** | 以教科院研究员范式 + 表达 DNA 审改稿件：查体例是否合内参、战略高度够不够、表达是否到位（如补课题组署名、书面化措辞、收束判断），并按研究员视角研判/改写 |
| **audit-extend-suggestions** | 对成稿的对策建议做外部审计：联网核查是否重复中国已有政策、能否基于已有政策往前推（补配套/深化）、有没有真空白可补；独立于主流、不写回正文 |

成稿出来后，把 `final_*.md` 交给这两个 skill——前者管整篇体例/表达/高度，后者专管建议块的防重/补深/找空白，产出审改意见或优化稿。

---

## 一条最短可用路径

```
① topic-material-search 出料包 → 记下 run-id
②a 识别体例：experience_response
②b cd strategic_response_workflow && runner.py --report-type experience_response \
     --topic ... --target-country ... --strategy-domain ... --reuse-materials-run <run-id>
②c 取 runs/<id>/final_article_reviewed.docx
③ jiaokeyuan-researcher 审改整篇 + audit-extend-suggestions 核查建议 → 定稿
```
