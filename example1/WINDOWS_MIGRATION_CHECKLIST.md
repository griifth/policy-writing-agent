# Windows 移植修复清单（macOS → Windows）

本清单面向**执行 agent**：项目是一个中文政策报告写作系统，含两个引擎（根引擎 `workflow/`、战略引擎 `strategic_response_workflow/`），需从 macOS 移植到 Windows。请严格按 A→B→C→D→E 顺序执行。

> 术语：`PROJECT_ROOT` = 项目根目录，在本机为 `/Users/hujingkai/Documents/New project/example1`，移植到 Windows 后建议放在 `C:\proj\example1`（见 C 区长路径）。

---

## ⚠️ 克隆后必做两件事（`git clone` 不会带来的东西）

> 项目通过 `git clone` 移植，以下两项**被有意排除在仓库外**，clone 下来一定缺，缺了任一项都会在运行时失败。放在最前面提醒，别漏。

1. **重建 `.env`（含密钥，未入仓库）**：仓库里只有 `.env.example`，没有真实 `.env`。必须在**两个**位置各复制一份并填值：
   - `PROJECT_ROOT\.env`（复制 `PROJECT_ROOT\.env.example`）
   - `strategic_response_workflow\.env`（复制 `strategic_response_workflow\.env.example`）
   - 至少填 `DEEPSEEK_API_KEY=<你的key>`；`DEEPSEEK_MODEL` 保持 `deepseek-v4-pro`（本项目实际模型）。详见 **A7**。
2. **重新登录 NotebookLM（登录态未入仓库）**：clone 不含任何登录凭证。必须在 Windows 上重跑 `notebooklm login` 并通过 `notebooklm auth check --test --json`。详见 **A4**。

> 这两项也在 A 区有完整步骤；此处只作"克隆即缺、必补"的醒目提示。`python scripts\deploy_selfcheck.py` 会显式检查这两项，未补会报 FAIL/WARN。

---

## 给执行 agent 的须知（先读，务必遵守）

1. **幂等**：每一步都应可重复执行而不产生副作用。安装类命令先检查是否已装（`--version` / `where`）再决定是否安装；配置类改动改前先确认当前值，已是目标值则跳过并打勾。
2. **改前先备份**：B 区任何代码改动前，先复制一份 `.bak`（如 `copy notebooklm_client.py notebooklm_client.py.bak`）。若改动后校验失败，用备份回滚。
3. **每步做完打勾**：完成一条就把该条的 `- [ ]` 改成 `- [x]`，保持清单为唯一进度真相。
4. **B 区改完必须 import 通过**：B 区所有代码改动完成后，必须能成功 import（见 B 区末尾的“B 区整体完成判据”），import 不通过不得进入 C 区。
5. **不要臆造**：本清单所有 file:line 已由审计核对（见文末），若实际行号有偏移，以“函数名 + before 代码块精确匹配”为准，不要盲改行号。
6. **中文优先**：本项目满是中文文件名与中文内容，任何涉及文件读写/传输的操作都要保证 UTF-8，禁止用会退回 GBK/cp936 的旧工具。

---

## A. 环境安装

- [ ] **A1. 安装 Python 3.10–3.13**
  - 做什么：安装 64 位 Python（推荐 3.11 或 3.12，范围 3.10–3.13），安装时勾选 “Add python.exe to PATH”。
  - 为什么：代码用了 `X | None`、`list[str]` 等语法，需 3.10+；3.13 以上未验证，避免用。
  - 命令：`winget install Python.Python.3.12`（或官网安装包）。
  - 完成判据：`python --version` 输出 3.10–3.13；`python -c "import sys;print(sys.version)"` 正常。

- [ ] **A2. 为每个引擎各建虚拟环境并装依赖**
  - 做什么：分别在 `PROJECT_ROOT` 和 `strategic_response_workflow/` 下建 venv 并安装依赖。依赖清单是 `PROJECT_ROOT\requirements.txt`（已由另一 agent 生成，内含 `PyYAML>=6.0`、`openai>=1.0`；其余均为标准库）。
  - 为什么：两个引擎独立运行，隔离环境避免污染系统 Python。
  - 命令（在 `PROJECT_ROOT`）：
    ```bat
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```
    战略引擎同理（若其目录下无独立 requirements.txt，则复用根目录那份：`pip install -r ..\requirements.txt`）。
  - 完成判据：`pip show pyyaml openai` 均能显示版本；`python -c "import yaml, openai"` 无报错。

- [ ] **A3. 安装 notebooklm CLI（teng-lin/notebooklm-py，官方支持 Windows）**
  - 做什么：用 pipx（或 uv）全局安装带浏览器扩展的 CLI。
  - 为什么：本项目通过 subprocess 调用 `notebooklm` 命令做资料检索；它是**独立 CLI**，不在 requirements.txt 里。
  - 命令：
    ```bat
    python -m pip install --user pipx
    python -m pipx ensurepath
    pipx install "notebooklm-py[browser]"
    ```
    （或 `uv tool install "notebooklm-py[browser]"`）
  - **版本 pin（重要）**：必须 pin 与 macOS 上**相同的 notebooklm-py 版本**，避免 CLI 参数漂移。本项目对 CLI 的调用契约是固定的：
    - `notebooklm ask --prompt-file <path> --notebook <id> --timeout <n>`（返回**自然文本 stdout**，`ask` 子命令**无 `--json`**）
    - `notebooklm list --json`、`notebooklm auth check --test --json`
    先在 macOS 上 `notebooklm --version` 记下版本号，Windows 上 `pipx install "notebooklm-py[browser]==<该版本>"`。
  - 完成判据：`notebooklm --version` 与 macOS 一致；`notebooklm ask --help` 中存在 `--prompt-file` / `--notebook` / `--timeout` 参数。

- [ ] **A4. notebooklm 登录 + 认证校验**
  - 做什么：浏览器登录 Google，首次会下载 Chromium（~170MB，Playwright 依赖）。
  - 命令：`notebooklm login`（弹浏览器完成 Google 登录）→ `notebooklm auth check --test --json`
  - 兜底：若 `login` 报 `Executable doesn't exist` / Playwright 浏览器缺失，先跑 `python -m playwright install chromium` 手动装浏览器再重试 `login`（纯净 Windows 首次常见）。
  - 为什么：`--test` 会发起真实网络校验（代码 `check_auth` 要求 `status==ok` 且 `checks.token_fetch is True`），仅本地 cookie 不够。
  - 完成判据：`notebooklm auth check --test --json` 输出 `"status":"ok"` 且 `token_fetch` 为 `true`。

- [ ] **A5. （可选）设置 NOTEBOOKLM_CLI_PATH**
  - 做什么：若 `notebooklm` 不在 PATH，或想固定用某个 exe，在两个 `.env` 里设 `NOTEBOOKLM_CLI_PATH=C:\path\to\notebooklm.exe`（全路径，指向 `notebooklm.exe`）。
  - 为什么：`_load_cli_path()` 优先读环境变量 `NOTEBOOKLM_CLI_PATH`，其次读 `.env`，最后回退到裸命令 `notebooklm`（依赖 PATH）。
  - 完成判据：`where notebooklm` 能定位，或 `.env` 中 `NOTEBOOKLM_CLI_PATH` 指向真实存在的 exe。

- [ ] **A6. 安装 pandoc（外部二进制，加入 PATH）**
  - 做什么：安装 Windows 版 pandoc 并确保在 PATH。
  - 为什么：导出 docx 通过 `subprocess.run(["pandoc", ...], check=True)`（`check=True`，找不到会直接抛异常终止导出步骤）。见 `strategic_response_workflow/workflow/runner.py:700` 与 `strategic_response_workflow/workflow/policy_n_prompt_runner.py:310`。
  - 命令：`winget install JohnMacFarlane.Pandoc`（或官网安装包）；装完**重开终端**刷新 PATH。
  - 完成判据：`pandoc --version` 正常输出。

- [ ] **A7. 重建两个 `.env`（不入仓库）**
  - 做什么：在 Windows 上分别创建 `PROJECT_ROOT\.env` 和 `strategic_response_workflow\.env`，从 `strategic_response_workflow\.env.example` 复制模板并填入真实凭据。
  - 为什么：`.env` 含密钥，不进仓库，必须在目标机手动重建。两个引擎的 key 集合一致（已核对两处 `.env` 与 `deepseek_client.py`）。
  - **需要的 key 列表**（值须真实填写）：
    ```
    # DeepSeek（LLM，经 openai SDK 调用）
    DEEPSEEK_API_KEY=
    DEEPSEEK_BASE_URL=https://api.deepseek.com
    DEEPSEEK_MODEL=deepseek-v4-pro
    DEEPSEEK_TIMEOUT_SECONDS=600
    DEEPSEEK_MAX_TOKENS=12000
    DEEPSEEK_REASONING_EFFORT=max
    DEEPSEEK_THINKING_ENABLED=true
    DEEPSEEK_STORE_REASONING=          # 本机 .env 中存在此键，一并带上
    # Anthropic 兼容端点（可选，留空即可）
    ANTHROPIC_COMPAT_API_KEY=
    ANTHROPIC_COMPAT_BASE_URL=
    ANTHROPIC_COMPAT_MODEL=
    ANTHROPIC_COMPAT_TIMEOUT_SECONDS=300
    ANTHROPIC_COMPAT_MAX_TOKENS=12000
    # NotebookLM CLI
    NOTEBOOKLM_CLI_PATH=notebooklm     # 或填 notebooklm.exe 全路径
    NOTEBOOKLM_TIMEOUT_SECONDS=600
    ```
    （唯一必填的凭据是 `DEEPSEEK_API_KEY`；`deepseek_client.py` 缺它会抛 `缺少 DEEPSEEK_API_KEY`。ANTHROPIC_COMPAT_* 为可选，可留空。）
  - 完成判据：两个 `.env` 均存在且含 `DEEPSEEK_API_KEY`（非空）；`.env` 未被 git 跟踪（`git status` 中不出现）。

---

## B. 代码修复（含精确 patch）

> 本区两处改动内容**完全相同**（两个引擎各一份同名文件），但**必须都改**。改前备份，改后按“B 区整体完成判据”验证 import。

- [ ] **B1. 修复根引擎 subprocess 中文乱码**
  - 文件：`workflow/notebooklm_client.py`，函数 `_run_text`（第 131–153 行），`subprocess.run(...)` 在**第 135 行**起。
  - 为什么：`capture_output=True, text=True` 但**未指定 `encoding=`**。Windows 中文系统默认用 cp936(GBK) 解码子进程 stdout，而 notebooklm 输出的是 UTF-8 中文 → 检索结果乱码，且 `_run_json` 会因乱码 JSON 解析失败。
  - before（第 135–142 行）：
    ```python
            completed = subprocess.run(
                command,
                cwd=self.cwd,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
    ```
  - after：
    ```python
            completed = subprocess.run(
                command,
                cwd=self.cwd,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
            )
    ```
  - 完成判据：文件中 `subprocess.run(` 块内出现 `encoding="utf-8"` 与 `errors="replace"`；见 B 区末统一 import 校验。

- [ ] **B2. 修复战略引擎 subprocess 中文乱码**
  - 文件：`strategic_response_workflow/workflow/notebooklm_client.py`，函数 `_run_text`（第 131–153 行），`subprocess.run(...)` 在**第 135 行**起。
  - before / after：与 B1 **完全一致**（两文件该段代码逐字节相同）。
  - 完成判据：同 B1。

- [ ] **B 区整体完成判据（import 必须通过）**
  - 分别在各引擎的 venv 激活状态下执行，均无异常输出即通过：
    ```bat
    cd C:\proj\example1
    python -c "import ast; ast.parse(open(r'workflow\notebooklm_client.py',encoding='utf-8').read()); print('root OK')"
    python -c "import sys; sys.path.insert(0,'workflow'); import notebooklm_client; print('root import OK')"

    cd C:\proj\example1\strategic_response_workflow
    python -c "import sys; sys.path.insert(0,'workflow'); import notebooklm_client; print('strategic import OK')"
    ```
  - 判据：三条均打印 OK，无 SyntaxError / ImportError。未通过则用 `.bak` 回滚重改。

---

## C. Windows 平台加固

- [ ] **C1. 开启长路径支持**
  - 做什么：二选一（或都做）——
    1. 管理员 PowerShell 开注册表：
       ```powershell
       New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
       ```
    2. 让 git 允许长路径：`git config --system core.longpaths true`
  - 为什么：Windows 默认 MAX_PATH=260 字符。本项目深层中文目录 + `runs/<run_id>/review_reports/<中文名>.md` 极易超限，导致写文件失败。
  - 完成判据：`(Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem").LongPathsEnabled` 为 1；或 `git config --system --get core.longpaths` 为 true。

- [ ] **C2. 项目放盘根短路径**
  - 做什么：把项目放在 `C:\proj\example1`，不要放在 `C:\Users\<长中文名>\Documents\...` 之类深路径下。
  - 为什么：进一步压缩路径长度余量，配合 C1 双保险。
  - 完成判据：项目根路径长度 < 30 字符（如 `C:\proj\example1`）。

- [ ] **C3. 传输时保护中文文件名（UTF-8 感知）**
  - 做什么：用 git clone/pull，或用 7-Zip（勾选 UTF-8 文件名）搬运；**禁止**用会按 GBK 编码文件名的旧版系统 zip / WinRAR 旧模式。
  - 为什么：项目满是中文文件名，非 UTF-8 感知的压缩工具会把中文名压成乱码，解压后路径断裂。
  - 完成判据：解压/克隆后随机抽查 3 个中文文件名（如 `多政策的国际比较报告` 相关目录）显示正常，无 `??`/乱码。

- [x] **C4. 文件名 Windows 非法字符（已在源码修复，Win 上复验）**
  - 背景：`多政策的国际比较报告/第一章提示词/` 下曾有 3 个提示词文件名含**半角冒号 `:`**（Windows 非法，`git clone` 检出会报 `0x80070057 参数错误` / `invalid path`），且被 `prompt_builder.py` 运行时读取。已统一改为**全角 `：`** 并同步全部引用（见本次提交）。
  - Win 上复验：clone 后确认这三个文件存在且能打开——
    ```powershell
    dir "多政策的国际比较报告\第一章提示词\"
    ```
    应看到 `1A：顶层设计 - 检索`、`2B：实施机制 · 归类`、`模块 1B：顶层设计 · 归类加写作`（全角冒号），无检出报错。
  - 若日后新增提示词文件：文件名**禁用** `: * ? " < > |` 及前后空格（这些在 Windows 非法）；需要冒号一律用全角 `：`。
  - 完成判据：`git clone` 全程无 `invalid path` 报错；上述三文件可正常打开。

---

## D. 打包剔除（移植前删除，不随包带走）

> 目的：这些是可再生产物 / 一次性脚本 / 系统垃圾，体积大且部分含 macOS 专属硬编码。移植前删除（若用 git，确保它们在 `.gitignore` 或未被跟踪）。删前可先确认存在。

- [ ] **D1. 删除 `runs/`（两处，可再生且巨大）**
  - 路径：`PROJECT_ROOT\runs`（约 7.1M）与 `strategic_response_workflow\runs`（约 43M）。
  - 为什么：运行产物，目标机重跑即可再生；且内含深层中文路径，是 C1 长路径问题的主要来源。
  - 命令：`rmdir /s /q runs` 与 `rmdir /s /q strategic_response_workflow\runs`（或搬运前就不打包这两个目录）。
  - 完成判据：两个 `runs\` 不存在（或不在传输包内）。

- [ ] **D2. 删除一次性调试脚本 `tmp_*.py`（strategic 6 个 + 根引擎 1 个）**
  - 路径：`strategic_response_workflow\workflow\` 下 6 个
    （`tmp_ds_3way_aiedu.py`、`tmp_ds_3way_review.py`、`tmp_ds_3way_review_v2.py`、`tmp_ds_3way_slice.py`、`tmp_ds_material_review.py`、`tmp_ds_score_clarified.py`）
    **＋ 根引擎 `workflow\tmp_ch2_topic_probe.py`（1 个，易漏）**。
  - 为什么：一次性调试脚本，非流水线依赖；`tmp_ds_material_review.py:40` 有 macOS 硬编码 `Path("/tmp/review_in.txt")`（Windows 无 `/tmp`）且含直接接触原始材料的代码；`workflow\tmp_ch2_topic_probe.py` 硬编码了不存在的 RUN_ID、用私有属性，纯属调试残留。
  - 命令：`del strategic_response_workflow\workflow\tmp_*.py workflow\tmp_*.py`
  - 完成判据：`dir strategic_response_workflow\workflow\tmp_*.py workflow\tmp_*.py` 均无匹配。

- [ ] **D3. 清除 `.DS_Store`（约 33 个）**
  - 为什么：macOS Finder 垃圾文件，对 Windows 无用。
  - 命令（PowerShell，在项目根）：`Get-ChildItem -Recurse -Force -Filter .DS_Store | Remove-Item -Force`
  - 完成判据：`Get-ChildItem -Recurse -Force -Filter .DS_Store` 无结果。

- [ ] **D4. 清除 `__pycache__/`（约 4 个）**
  - 为什么：编译缓存，跨平台/跨版本无意义，重跑自动再生。
  - 命令：`Get-ChildItem -Recurse -Force -Directory -Filter __pycache__ | Remove-Item -Recurse -Force`
  - 完成判据：无 `__pycache__` 目录残留。

- [ ] **D5. 删除各类 `*.zip`**
  - 已知：`PROJECT_ROOT\多政策的国际比较报告.zip`（以及 git status 显示的其它 zip）。
  - 为什么：打包中间物，非源码，避免重复搬运与中文名损坏风险。
  - 命令：`del "多政策的国际比较报告.zip"`（按实际清点删除全部 zip）。
  - 完成判据：项目内无 `*.zip`（或不在传输包内）。

---

## E. 验收

- [ ] **E1. notebooklm 认证通过**
  - 命令：`notebooklm auth check --test --json`
  - 完成判据：`status=ok`、`token_fetch=true`（同 A4，此处作为端到端前置复核）。

- [ ] **E2. 根引擎 dry-run（不调 LLM/NotebookLM，验路径与依赖导入）**
  - 命令（在 `PROJECT_ROOT`，激活其 venv）：
    ```bat
    python workflow\runner.py --topic "人工智能+教育" --notebook-name "<你的NotebookLM库名>" --dry-run
    ```
    注意：根引擎的 `--notebook-name` 是**必填**参数（与 `--topic` 一样 required）。
  - 为什么：`--dry-run` 只建目录、任务列表、提示词，不联网，用来验证路径写入（含中文/长路径）与所有 import。
  - 完成判据：进程退出码 0；`runs\<新run_id>\` 生成，内含任务列表/提示词文件，无编码或路径异常报错。

- [ ] **E3. 战略引擎 dry-run**
  - 命令（在 `strategic_response_workflow\`，激活其 venv）：
    ```bat
    python workflow\runner.py --report-type experience_response --topic "..." --target-country "..." --strategy-domain "..." --notebook-name "<库名>" --dry-run
    ```
  - 完成判据：退出码 0；生成 run 目录；`_export_docx` 在 dry-run 下写 `final_article_reviewed.docx.txt`（占位）而非调 pandoc，无报错。

- [ ] **E4. 真实小样出稿（两个引擎各一次）**
  - 做什么：去掉 `--dry-run`，跑一次真实的小主题，产出成稿；战略引擎会真实调用 pandoc 导出 docx。
  - 为什么：验证 B 区中文编码修复生效（检索结果不乱码）、DeepSeek 凭据可用、pandoc 导出成功、长路径不再报错。
  - 完成判据：
    - 根引擎：`runs\<run_id>\` 出现最终 markdown 成稿，中文正常无乱码。
    - 战略引擎：生成 `final_article_reviewed.docx`（pandoc 真实导出成功），中文正常。
    - 全程无 `UnicodeDecodeError` / cp936 相关报错、无路径超限报错。

---

## 附：审计已核对的 file:line（证明无臆造）

- `workflow/notebooklm_client.py` — `_run_text` 定义 L131–153；`subprocess.run(` 起于 L135，缺 `encoding=`（B1）。
- `strategic_response_workflow/workflow/notebooklm_client.py` — `_run_text` 定义 L131–153；`subprocess.run(` 起于 L135，缺 `encoding=`（B2）。两文件该段逐字节一致。
- `strategic_response_workflow/workflow/runner.py:700` — `subprocess.run(["pandoc", str(source), "-o", str(target)], check=True)`（`_export_docx`，dry-run 分支在 L697–698）。
- `strategic_response_workflow/workflow/policy_n_prompt_runner.py:310` — 同款 pandoc 调用。
- `workflow/notebooklm_client.py:221` / `:234` — `NOTEBOOKLM_CLI_PATH` 优先环境变量、回退裸 `notebooklm`。
- `workflow/deepseek_client.py:108–125` — 读取 `DEEPSEEK_API_KEY`（必需）等 key。
- `strategic_response_workflow/.env.example` — DeepSeek / ANTHROPIC_COMPAT / NOTEBOOKLM 全 key 列表。
- 本机 `.env`（根与 strategic）实际含键：DEEPSEEK_* + DEEPSEEK_STORE_REASONING + NOTEBOOKLM_*（已比对）。
- `workflow/runner.py:20,22–25,32,37,42` — 根引擎 CLI：`--topic`(required)、`--notebook-name`(required)、`--dry-run`、`--resume-run`、`--reuse-materials-run`。
- `strategic_response_workflow/workflow/runner.py:1026–1071` — 战略引擎 CLI 全参数。
- `strategic_response_workflow/workflow/tmp_ds_material_review.py:40` — `Path("/tmp/review_in.txt")` macOS 硬编码。
- 剔除目标实测：`runs`(7.1M)、`strategic_response_workflow/runs`(43M)；`tmp_ds_*.py` 共 6 个；`.DS_Store` 33 个；`__pycache__` 4 个；`多政策的国际比较报告.zip`。
- `requirements.txt` 位于 `PROJECT_ROOT`（example1/），内容 `PyYAML>=6.0`、`openai>=1.0`，并注明 notebooklm CLI 与 pandoc 为外部工具。
