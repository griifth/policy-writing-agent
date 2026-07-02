# 政策报告写作工作流 · 初始化指南

一个中文政策报告自动写作系统。核心是**两个工作流引擎**，外加一组可插拔的 **skill**（迷你工作流）与**注入资产**（文风 DNA / 推理刀 / 机构落点）。本 README 只讲**如何把项目初始化到能跑起来**；具体怎么驱动见 [`report-workflow-runbook/SKILL.md`](report-workflow-runbook/SKILL.md)。

> 本指南以 macOS / Linux 为主。**Windows 移植**请改用 [`WINDOWS_MIGRATION_CHECKLIST.md`](WINDOWS_MIGRATION_CHECKLIST.md)（含 Windows 专属的编码修复、长路径、克隆后必做等）。

---

## 一、这是什么

| 组件 | 位置 | 说明 |
|---|---|---|
| **根引擎**（章节流水线，23 步） | `workflow/` | 国际比较类报告（逐章检索→写作→审查→改写） |
| **战略引擎**（判断流水线，16 步） | `strategic_response_workflow/` | 判断类三体例：`strategic_response` / `experience_response` / `trend_review` |
| **skill（迷你工作流）** | `topic-material-search/`、`distill-report-module/`、`policy-book-distillation/`… | 取料、造体例、蒸馏方法等，模型驱动 |
| **注入资产** | 各引擎内的 `policy_style_dna/`、`institution_profile.md`、`report_modules/` | 只控文风/判断/落点，不控事实 |

两引擎都靠 **DeepSeek**（文本生成）+ **NotebookLM**（材料检索）跑；成稿用 **pandoc** 导出 docx。

---

## 二、前置要求

- **Python 3.10 – 3.13**（用了 `X | None`、`list[str]` 等语法，需 3.10+）
- **DeepSeek API Key**（写作/审查全靠它）
- **notebooklm CLI**（[teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py)，材料检索）—— 若只用现成料包/网搜可跳过，见下方「材料来源」
- **pandoc**（导出 Word；不导 docx 可暂缓）

---

## 三、初始化步骤

### 1. 取得项目
```bash
git clone -b International-Policy-Comparison-Template-Workflow \
  ssh://git@ssh.github.com:443/griifth/policy-writing-agent.git
cd policy-writing-agent/example1        # 下称 PROJECT_ROOT
```

### 2. 建虚拟环境 + 装 Python 依赖
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # 仅 PyYAML + openai，其余全标准库
```
> 战略引擎复用同一套依赖；进它的目录跑时激活同一个 venv 即可。

### 3. 安装外部工具
```bash
# NotebookLM CLI（teng-lin/notebooklm-py，含浏览器自动化；首次 login 会下载 Chromium ~170MB）
pipx install "notebooklm-py[browser]"     # 或 uv tool install "notebooklm-py[browser]"
notebooklm login                          # 浏览器登录 Google
notebooklm auth check --test --json       # 期望 "status":"ok"

# pandoc（导出 docx 用）
brew install pandoc                        # macOS；Linux 用包管理器
```
> NotebookLM CLI 的完整安装、登录、鉴权、知识库准备与排查，见下方 **[七、NotebookLM CLI 配置详解](#七notebooklm-cli-配置详解teng-linnotebooklm-py)**。

### 4. 配置 `.env`（**两处**，含密钥、不入仓库）
```bash
cp .env.example .env
cp strategic_response_workflow/.env.example strategic_response_workflow/.env
```
然后在两个 `.env` 里各填：
```ini
DEEPSEEK_API_KEY=<你的key>
DEEPSEEK_MODEL=deepseek-v4-pro     # 本项目实际模型；缺省时代码回退 deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
NOTEBOOKLM_CLI_PATH=notebooklm     # notebooklm 不在 PATH 时填全路径
```

### 5. 环境自检
```bash
python3 scripts/deploy_selfcheck.py
```
逐项打印 `[OK]/[WARN]/[FAIL]`（Python 版本、PyYAML、notebooklm、pandoc、两处 `.env`、关键资产）。有 FAIL 先按提示补齐。

### 6. Dry-run 验证（不调 LLM / NotebookLM，只验路径与依赖）
```bash
# 根引擎
python3 workflow/runner.py --topic "人工智能+教育" --notebook-name "<你的知识库名>" --dry-run

# 战略引擎（在其目录下跑）
cd strategic_response_workflow
python3 workflow/runner.py --report-type strategic_response \
  --topic "..." --target-country "..." --strategy-domain "..." \
  --notebook-name "<你的知识库名>" --dry-run
cd ..
```
两条都无 error 即环境就绪。

---

## 四、跑第一篇报告

去掉 `--dry-run` 即真跑。完整参数、体例选择、续跑、产物落点见 **[`report-workflow-runbook/SKILL.md`](report-workflow-runbook/SKILL.md)**；任务参数可照 **[`task_config.template.yaml`](task_config.template.yaml)** 填。

- 中断续跑：战略引擎 `--continue` / `--resume <run-id>`；根引擎 `--resume-run <run-id>`。
- 成稿落在 `runs/<run-id>/`（`final_report*.md` / `final_article*.md` + `.docx`）。

---

## 五、材料来源（检索这一步的三种填法）

| 方式 | 怎么用 | 何时 |
|---|---|---|
| **NotebookLM** | 传 `--notebook-name`，需已 `notebooklm login` | 用自有知识库（默认） |
| **复用料包** | `--reuse-materials-run <run-id>`，跳过检索 | 已有现成 `retrieval_outputs/` |
| **网搜 skill** | 跑 `topic-material-search` 出料包 → 同样 `--reuse-materials-run` | 库里没有 / 要公网权威源 |

> 三者殊途同归到同一份材料契约 `retrieval_outputs/<type>.md`（二段式：一、检索内容 / 二、相关文献）。

---

## 六、更多文档

- **[`USAGE.md`](USAGE.md)** — 全流程使用指南（搜资料→检索→识别体例写作→教科院审核优化）
- **[`report-workflow-runbook/SKILL.md`](report-workflow-runbook/SKILL.md)** — 怎么驱动两台引擎（选引擎/命令/续跑/失败处置）
- **[`WINDOWS_MIGRATION_CHECKLIST.md`](WINDOWS_MIGRATION_CHECKLIST.md)** — 移植到 Windows 的完整修复清单
- **[`task_config.template.yaml`](task_config.template.yaml)** — 报告任务配置模板
- `scripts/deploy_selfcheck.py` — 部署自检

---

## 七、NotebookLM CLI 配置详解（teng-lin/notebooklm-py）

> **仓库**：<https://github.com/teng-lin/notebooklm-py> ｜ 官方支持矩阵标注 **Windows / macOS / Linux 均已测试**。

**它是什么**：一个非官方的 NotebookLM 命令行封装，底层用 **Playwright 驱动浏览器**登录 Google。本项目用它做"材料检索"——把提示词发给指定 notebook、取回带引用的回答，落成 `retrieval_outputs/<type>.md`。

### 1. 安装（务必带 `[browser]`，否则不装浏览器自动化）
```bash
pipx install "notebooklm-py[browser]"     # 推荐
# 或
uv tool install "notebooklm-py[browser]"
```
- 支持 Python 3.10–3.14；CLI 命令名就是 `notebooklm`。
- 验证：`notebooklm --version`。

### 2. 首次登录（会下载 Chromium ~170MB）
```bash
notebooklm login                          # 弹浏览器完成 Google 登录
```
- 若报 `Executable doesn't exist` / 浏览器缺失：先 `python -m playwright install chromium` 再重试 `login`（纯净机器首次常见）。
- 也可复用本机浏览器 cookie：`notebooklm login --browser-cookies chrome`（或 `'chrome::Profile 1'`）。

### 3. 验证登录态（本项目强依赖这一步）
```bash
notebooklm auth check --test --json       # 期望 "status":"ok" 且 token_fetch=true
```
- 本项目的 `check_auth` 正是校验 `status==ok` 且 `token_fetch is True`——**仅有本地 cookie 不够**，必须能真实取到 token。
- 登录会过期；报错时先 `notebooklm auth refresh`，不行再重跑 `notebooklm login`。

### 4. 让项目找到它（`.env` 里的 `NOTEBOOKLM_CLI_PATH`）
- 一般装完 `notebooklm` 已在 PATH，两个 `.env` 保持 `NOTEBOOKLM_CLI_PATH=notebooklm` 即可。
- 若不在 PATH 或有多版本，把它填成可执行文件全路径：
  - macOS/Linux：`NOTEBOOKLM_CLI_PATH=/Users/you/.local/bin/notebooklm`
  - Windows：`NOTEBOOKLM_CLI_PATH=C:\Users\you\.local\bin\notebooklm.exe`
- 还可在 `.env` 调 `NOTEBOOKLM_TIMEOUT_SECONDS`（默认 600）。

### 5. 准备知识库（notebook）
本项目用 `--notebook-name "<名称>"` 指定知识库，运行时按名称匹配到 notebook id——**所以要先在你的 NotebookLM 账号里建好知识库并传入源材料**：
```bash
notebooklm metadata --json                # 看你有哪些 notebook 及其源
notebooklm create "AI+教育"               # 新建 notebook
notebooklm source add "./某材料.pdf"      # 加入源材料（也支持 URL / add-research）
```

### 6. 本项目的实际调用契约（排查用）
代码对 CLI 的调用固定为：
```
notebooklm ask --prompt-file <提示词文件> --notebook <notebook_id> --timeout <秒>
```
自然文本 stdout（`ask` 不带 `--json`）。若你装的版本 CLI 参数有变动导致对不上，**pin 回与本项目一致的版本**即可。

---

## 常见坑

- **`.env` 缺失**：`git clone` 不含 `.env`（有意排除），必须按第 4 步在**两处**各建一份，否则 LLM 调用直接失败。
- **NotebookLM 未登录**：clone 不含登录态，必须重跑 `notebooklm login`。
- **中文文件名**：项目满是中文名，传输/压缩务必用 UTF-8 感知工具（推荐直接 `git clone`），别用会退回 GBK 的旧 zip。
- **模型名**：`.env` 显式写的 `DEEPSEEK_MODEL` 会覆盖代码默认；填你端点实际提供的模型（本项目为 `deepseek-v4-pro`）。
