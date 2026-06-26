# policy_style_dna

根工作流（`workflow/`，国际政策比较报告）的**体例原生文风 DNA**。蒸馏自 38 篇人类成稿国际比较报告，体例为**国际比较·决策咨询体**（内参/简报）。

> 它不是事实知识库；事实材料仍由检索与工作流中间产物提供。`policy_style_dna` 只控制写作姿态、结构、句式与审查标准，**不得作为事实来源**——不得从中新增政策事实、年份、机构、项目或数据。

## 与既有 style_dna 的区别
`strategic_response_workflow/style_dna/` 蒸馏自学术期刊论文（含摘要/关键词/文献综述/理论框架）。本模块蒸馏自决策咨询体国际比较成稿，分水岭：**编者按/数据导语开篇、加粗短语断言、先类型化再填国名、镜像推导建议、去国名虚指、稳慎兜底**。`EXECUTION_PLAN_intl_comparison_upgrade.md` §1.2 原计划直接复制学术版 style_dna；本模块以体例原生版本替代之，更贴合根工作流的人类金样本。

## 目录
- `raw/source_manifest.csv`：语料清单（38 篇，来源 `/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md/`）。
- `prompts/distill_style_wiki.md`：蒸馏 prompt（指向清单，不内嵌全文）。
- `wiki/`：可复用文风规则成果（详见 `wiki/README.md`）。
- `review_scope.md`：文风/表述审查范围（scope = style_and_expression）。

## 接入原则
写作模块读 `wiki/voice.md`、`structure.md`、`sentence.md`、`recommendation.md`；审查与修改模块读 `forbidden.md`、`recommendation.md`、`self_check.md`。最终正文不得输出文风分析过程、分类依据、比较维度或建议映射表，除非用户明确要求保留。

## 接入钩子（待办）
根工作流 `report_pipeline.py` 当前零 style_dna 注入。接入时仿 strategic runner 增 `_style_dna_text(mode)`，从本目录 `wiki/` 读取并拼到写作/审查/修改三步末尾；无 wiki 文件时零变化（gated）。对应执行计划 §1.2 / §2 / P3。

## 维护
- 原始人类语料属敏感素材，不进仓库（仅留 `raw/source_manifest.csv` 这一清单）。
- 补语料或换体例后，用 `prompts/distill_style_wiki.md` 重跑蒸馏覆盖 `wiki/`。
