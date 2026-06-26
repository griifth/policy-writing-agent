# 改造计划 · 国际比较报告工作流升级为 strategic_response 风格

> 目标：让根工作流（`workflow/`，国际政策比较报告 MVP，分章 22 步）的产出**达到甚至超越人类金样本**。
> 方法论复用：strategic_response_workflow 已验证的「逆向金样本抽判断刀 + style_dna 语域 + 盲审结果门」（终版 95 分压过人类 72）。
> 架构决策：**方案 B —— 嫁接**。保留分章 macro-shape，只加 4 件武器，改动集中在 `report_pipeline.py` 注入钩子。日期：2026-06-25。

## 0. 金样本集（体例：AI+教育国际比较 / 治理模式 + 类型化 + 中国落点）

来源（**人类政策比较报告成稿**）：`/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md/`（约 38 篇）。

### 0.1 直接对标的"原文章"（要超越的那篇）
- **`人工智能+教育国际比较报告.md`**（人类原版，111 行，结构：一、AI+教育政策国际比较 → 二、AI人才培养国际比较 → 三、政策建议）——**与我们 AI 报告 macro-shape 完全同构**，是头对头基线（AI run-20260625-112544-ccb86ce5 vs 此篇）。

### 0.2 抽刀金样本集（同体例国际比较成稿，逆向抽判断动作）
- `中考改革的国际比较.md`、`中小学校服治理国际比较.md`、`主要发达国家高校分类管理机制.md`、`美国新加坡韩国基础教育信息化评估政策比较.md`、`拔尖创新人才早期培养国际经验及启示.md`、`校外教育治理的国际趋势与经验.md`

P0 把上述拷进 `workflow/gold_samples/intl_comparison/`（gitignore 敏感人类素材）+ 反例若干（浅综述/一国一国平铺稿）作探针。

### 0.3 OCR 缺文注意（来源文件夹名标了"文本缺失"）
- 抽刀前须**抽查金样本完整性**：不从有整段缺失的报告抽刀；
- 头对头评分时，**不因 OCR 丢掉的内容惩罚/抬高人类原文**——比的是判断动作与语域，不是 OCR 残留字数。

## 1. 四件要移植的武器（映射根工作流文件）

### 1.1 reasoning_dna 刀（国际比较专属）—— 新建 `workflow/reasoning_dna/`
- `conventions.md`：复用 strategic 现成的元格式 + 语域红线（已含金样本=语域上限、定性词降级）。
- 4 把刀（领域无关元问题，逆向从金样本抽）：
  - **typology（类型化刀）**：是否把各国政策"收拢成能命名的类型"，而非一国一国平铺。
  - **comparability（可比性刀）**：比较维度是否同层、是否真比较（差异+原因+适用条件），而非并列罗列。
  - **applicability（适用条件刀）**：每条国际经验是否说清"在什么制度条件下成立、移植到中国要满足什么前提"。
  - **localization（中国落点刀）**：第三章建议是否从前两章比较发现推导、完成中国制度语境转化（防悬空、防照搬）。

### 1.2 style_dna 语域 —— 移植 strategic 的 `style_dna/wiki/`（体例无关）
根工作流当前零 style_dna 注入。复制 voice/structure/sentence/recommendation/forbidden/self_check，接到写作/审查/修改三步。

### 1.3 金样本锚 —— 把人类范文设为质量+语域上限
注入各章审查（`ch*.review`）与全文审查（`full.review`），对标"达到/超越原文章"。

### 1.4 盲审结果门 —— 3 评委双轴盲审
新稿 vs 金样本 vs 上次未装刀产出（run-20260625-112544-ccb86ce5）。判据见 §4。

## 2. 注入钩子（report_pipeline.py 改动，gated）

仿 strategic runner 的 `_with_reasoning_dna(prompt, step_id)` + `_style_dna_text(mode)`，无刀文件时**零变化**。接入步：
- `ch1_3a.plan` / `ch2.dimension.plan`（定题/凝练维度）← typology + comparability
- `ch1_*.write` / `ch2.write`（各章写作）← style_dna + applicability
- `ch3.write`（政策建议）← localization + style_dna
- `full.rewrite`（全文改写）← 全部刀 + 语域闸（**重点：参考 strategic 的 revision 教训，这步必须装语域闸，否则改写会反向加激进/堆砌**）

注入映射写进 `workflow/intl_comparison.module.yaml`（或在 pipeline 内建 step→cuts 表），便于改映射不动代码。

## 3. 分阶段执行

- **P0 金样本落盘**：gold_samples/intl_comparison/ + judge_set（human=18或合成、baseline=ccb86ce5）+ 反例。
- **P1 conventions + 语域红线**：复用 strategic 现成 conventions（含语域红线），拷到 workflow/reasoning_dna/。
- **P2 蒸馏 4 把刀**：用 `distill-reasoning-dna` skill 跑 dev↔review 对抗循环逆向抽刀，过硬门（三段式/领域无关/降级动作/反例锚点/探针区分力）。
- **P3 注入钩子接进 report_pipeline.py**：加 `_with_reasoning_dna` + `_style_dna_text`；dry-run 验证 gated 零变化、装刀后目标步带刀。
- **P4 重生成 + 3 评委盲审结果门**：达标算 PASS；未过把差距喂回精修刀，重生成 ≤ 3 次。

## 4. 验收标准（量化"达到甚至超越原文章"）

3 评委盲审中位数，**同时满足**：
| 轴 | 指标 | 阈值 |
|---|---|---|
| 综合 | 新稿 ≥2/3 judge 排第1 | 是 |
| 纵深 | 类型化 / 可比性 / 适用条件 各维度中位数 | **≥ 金样本** |
| 语域 | 适报维度中位数 | **≥ 金样本** |
| 防退化 | 总分中位数 | **> 上次未装刀产出（ccb86ce5）** |

## 5. 边界 / 风险

- 只改根工作流；不动 strategic_response_workflow。
- 注入全程 gated（无刀=旧行为），可随时回退。
- 金样本是期刊论文（非"国际比较报告"成稿）——体例同构但篇幅/章法略异，抽刀时取其"判断动作"（类型化/可比/适用条件/中国落点），不抄其章节формат。
- 写作步非确定性（DeepSeek 每次略有差异），故 full.rewrite 语域闸是必需兜底。
