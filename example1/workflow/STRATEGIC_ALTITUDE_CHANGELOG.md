# 战略高度改造 · 修改记录

- **日期**：2026-06-26
- **目标**：给根工作流（`workflow/`，国际政策比较报告）注入"战略高度"+ 文风/落点/审核，同时不丢其全景广度。
- **基线检查点**：commit `7c5aa64`（改造前）。一键回退根工作流：`git checkout 7c5aa64 -- workflow/`。
- **全程 gated**：删掉 `workflow/policy_style_dna/` 或 `workflow/institution_profile.md` 即回退到注入前行为。

---

## A. 新增资产
1. `workflow/prompts/strategic_framing.md` —— ch0「战略态势卡」prompt（6 字段：全局态势/政策层级演进/路线分野/中国利害/战略命题/证据不足项；硬约束=**只许把材料中已有的高位政策事实上升为战略判断，不得凭 topic 自造态势**）。
2. `workflow/policy_style_dna/` —— 文风 DNA（顶层通则 + 子型 A/B 路由），从 strategic 工作流拷入。
3. `workflow/institution_profile.md` —— 机构落点（建议必落教育域抓手 + 跨域→教育接口 + 中国制度容器 + 稳慎兜底），拷入。

## B. `report_pipeline.py`
- **新增 `ch0.strategic_framing` 步**：插在 `ch1.2a.retrieve` 后、`ch1.1b.write` 前（正确位置，确保影响第一章顶层设计/实施机制写作）；输入 1A/2A 检索材料，产出战略态势卡。
- **3 个 gated 注入钩子**（无资产文件零变化）：`_with_strategic_framing` / `_with_institution_profile` / `_with_policy_style_dna`（根工作流体例=子型 A）。
- **注入接线**：
  - 战略态势卡 → ch1.1b/1.2b/1.3c 写作、ch1.3a/ch2 定题、ch2 维度凝练、ch2 写作、ch3、full.review、full.rewrite（共 10 处）。
  - institution_profile → ch3.write、full.rewrite。
  - 文风 DNA → **（减载后）仅 ch3.write + full.review**。
- **`--reuse-materials-run` 参数 + `_reuse_materials` 方法**：复用指定 run 的 retrieval_outputs、标检索任务为 done、跳过 NotebookLM（同料盲跑用）。
- 辅助：`WORKFLOW_DIR` 常量；`_resolve_notebook` 加 reuse 分支；`_task_output` 加 ch0 条目。

## C. `task_state.py`
- `DEFAULT_TASKS` 插入 `ch0.strategic_framing`（22 步 → 23 步，order 重排）。

## D. 减载（`report_pipeline.py`）
- ch1.1b / ch1.2b / ch1.3c / ch2.write / full.rewrite **撤掉文风 DNA 注入**（战略卡保留），让基线 prompt 的"举措对应来源、成因解释、加粗领句真实归纳"紧凑纪律主导。

## E. 文风 DNA 规则（`policy_style_dna`，根 + strategic 两份同步）
- `forbidden.md`：加"**建议条禁回指前文 / 禁复述各国做法**"（归入"过程信息外露"）。
- `self_check.md`：L2 加"建议条未回指前文"检查项。

## F. 根工作流 prompt（去引用 + 建议简明 + 不回指）
- `workflow/prompts/ch3_writing.md`：①"建议不复述各国做法 / 不以任何形式回指前文"（含禁用开头反例）；②"每条建议 2–4 句、简明扼要、不长篇"；③"正文不标注文件名/机构/年份等引用"。
- `workflow/prompts/writing.md`（ch1 通用约束）：加"正文不在正文标注文件名/机构/年份/脚注等引用信息"；软化"文件名一致性"。
- `多政策的国际比较报告/第二章提示词/第二章凝练维度写作模版.md`：去"写明来源主体、文件名、年份"；删"来源清单"输出。
- `workflow/review_templates/content_structure_review.md`：第 9 节 + 质量底线 6 改为"**对位前文是内在逻辑、只做不说**"，并加"建议回指句"检查项。

## G. 验证记录（三方盲审，/70，标尺=policy_style_dna 子型 A + institution_profile）
| 文章 | 战略高度 | 总分/70 |
|---|:-:|:-:|
| 人类原文（干净 docx） | 6–7 | 37 → 47 |
| 根工作流裸跑基线 | 9 | 62–63 |
| 战略切片（减载版） | 9 | 58 |

- **ch0 战略态势卡有效**：切片战略高度 9 = 基线、> 原文（造出"教育主权/能力标准定义权"框架，远超人类原文）。
- **切片暂未压过基线**：执行厚度 −5（主权重构致第一/二章重叠 + 真比较略浅）；减载只救回了"出处"（不计分维度）。
- **待办**：让"主权高度"只在 ch0 + 各章总起定调，**不重构第二章骨架**（现 ch2 被改成"主权"导致与 ch1 重叠），更外科手术。

## 相关产物
- 战略切片成稿（减载版）：`runs/run-20260626-152506-2528b552/final_report_reviewed.md`
- **整理后干净成篇**（去引用 + 简明七条建议）：`runs/run-20260626-152506-2528b552/final_report_clean.md`
- 三方盲审：`runs/run-20260626-152506-2528b552/ds_3way_slice_v2.md`
