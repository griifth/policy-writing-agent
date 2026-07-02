# 2026-06-24 体例模块化 · handoff 审稿 · 语料扩充与提交记录

工作目录：`/Users/hujingkai/Documents/New project/example1/strategic_response_workflow`
分支：`International-Policy-Comparison-Template-Workflow`

## 一、本轮主线

把"政策写作工作流"从单体战略体例，重构为"通用引擎 + 可载入体例模块 + 共享 DNA 层"，并打通跨模型审稿的 handoff 机制；同时扩充参考语料并重新分类。

## 二、已完成（已提交并推送）

### 1. 体例模块化（提交 4bbfe63）
- `runner.py` 退成通用引擎，按 `--report-type` 载入 `report_modules/<体例>/`。
- 战略体例整体迁入 `report_modules/strategic_response/`（prompts/templates/source），`retrieval_types` 从 `module.yaml` 读取。
- 回归门：dry-run 18 个拼装提示词逐字节一致 + 真实 DeepSeek 重跑"中美AI人才"端到端健康（质量与旧版相当）。

### 2. report_type 与默认值
- 新增 `--report-type`，默认 `strategic_response`（保留已验证行为，不设"默认借鉴"）。
- `input.yaml` / `run_log` 记录体例模块。

### 3. handoff 审稿契约 + 暂停/续跑（提交 4bbfe63）
- `--reviewer inline`（默认，同后端自审，原行为）/ `--reviewer handoff`（暂停交外部 agent 审，`--resume <run-id>` 续跑）。
- 契约：`review_io/request_iter{n}.json`（机读）+ `INSTRUCTION_iter{n}.md`（交接指令）+ 输出格式契约（报告须含 `总体结论：达到|基本达到|未达到`，引擎判定不变）。
- 多轮验证：未达到→改稿→再次暂停→达到→收尾，全通过。

### 4. 指令由模板 + DNA 驱动（提交 4bbfe63）
- 交接指令不写死在代码：骨架 `reviewers/instruction_template.md`，"审什么"来自触发范围对应 DNA 的 `review_scope.md`。
- `scope → DNA` 映射：`style_and_expression → style_dna/review_scope.md`；`reasoning_compliance → reasoning_dna/review_scope.md`。
- 验证：改 `review_scope.md` → 下一轮指令立即反映，引擎不动。

### 5. experience_response 借鉴体例模块（提交 e950be5）
- 推理链：做法→成因→有效性→迁移前提→中国适配建议。
- 已真实跑出高质量稿（美英德澳体育教师培养聘任借鉴），借鉴体例的"刀"（成因/有效性/共性个性/归类/张力/迁移前提）在输出中明显生效。

### 6. 文档（提交 1f1e804）
- `reasoning_dna/DESIGN.md`（v0.2，纳入审核意见）。
- `WORKFLOW_OVERVIEW.md`（全流程总览：四层职责、六阶段、跨阶段机制、扩展方式）。

### 7. 异源审稿验证（实测）
- 用 Claude 异源子 agent 审 DeepSeek 稿，抓出 DeepSeek 自审漏看、甚至当亮点夸的"口号化/四字格"问题——证实"同模型共享盲区"，异源审有效。审稿范围按约定只审文风/表述。

## 三、配置修复（cc-switch 还原）

- 发现 `~/.claude/settings.json` 被 cc-switch 改成把 Claude 模型路由到 `deepseek-v4-pro`，导致辅助模型/子 agent 报错。
- 已移除该 env 块（备份 `~/.claude/settings.json.bak-cc-switch-20260623-111037`），重启后恢复官方 Anthropic 模型。
- DeepSeek 工作流配置另存于 `strategic_response_workflow/.env`（gitignored）。

## 四、参考语料扩充与分类

语料目录：`/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md/`（已从 31 → 38 篇）。

新增 7 篇（docx→md）分类：

| 文件 | 体例 | 对应模块 | 金样本 |
|---|---|---|---|
| 中美AI人才竞争及应对策略 | 战略应对 | strategic_response | 是（标杆，亦为旧人类参考稿） |
| 警惕美竞争法案对我教育战略的重大风险 | 战略应对 | strategic_response | 是（标杆） |
| 美英澳新一轮国际人才争夺的长短线招数及其破解 | 战略应对 | strategic_response | 是 |
| 从国际经验中优化课后服务推动双减 | B 经验借鉴 | experience_response | 是（闭环最干净） |
| 人工智能+教育国际比较报告 | A 国际比较 | experience_response | 否（迁移链偏松） |
| 全球经验·AI拔尖人才六大前沿趋势 | C 动向综述 | (C未建) | 否 |
| 校外教育治理的国际趋势与经验 | C 动向综述 | (C未建) | 否 |

更新后全景（38 篇）：
- 战略应对型 3（**新补金样本——原 30 篇几乎没有此体例**）→ strategic_response ✅
- A 国际比较 8 + B 经验借鉴 9 = 17 → experience_response ✅
- **C 动向综述型 11（+2，最大缺口，未建）**
- D 专题机制型 6（未建）

## 五、关键结论

1. **strategic_response 现在有 3 篇金样本**，可真正蒸馏其 reasoning_dna（此前只有 1 篇人类参考稿）。
2. **C-动向综述型 11 篇是最大缺口**，推理链应为 `信号识别→趋势归纳→阶段研判→对我国含义（含不确定性）`。
3. 两个已建模块都有金样本可蒸馏 reasoning_dna。

## 六、提交与推送

```
1f1e804  补充 reasoning_dna 设计稿与工作流总览文档
e950be5  新增 experience_response 借鉴体例模块
4bbfe63  工作流体例模块化 + report_type + handoff 审稿交接
```
已推送到 `origin/International-Policy-Comparison-Template-Workflow`（`policy-writing-agent.git`）。
未提交：`.env`、`runs/`（gitignored）；`strategic_response_workflow/experiments/`（用户自有）。

## 七、下一步候选

1. 从 3 篇 strategic 金样本蒸馏 strategic_response 的 reasoning_dna。
2. 建 C-动向综述模块（最大缺口）。
3. 从课后服务等样本做 experience_response 的 reasoning_dna MVP 两刀（成因 + 有效性）；两刀建好后 `reasoning_compliance` 审稿范围的"尺子"即自动有内容。
