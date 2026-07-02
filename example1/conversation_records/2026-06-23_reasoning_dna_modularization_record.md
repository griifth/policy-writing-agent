# 2026-06-23 reasoning_dna 审核与体例模块化记录

## 一、当前背景

本轮讨论围绕 `strategic_response_workflow/reasoning_dna/DESIGN.md` 展开。该文档由 Claude 起草，目标是给现有政策写作工作流增加 `reasoning_dna`，用于约束和提升 LLM 的推理质量，使文章不只是材料综述，而能形成更像政策研究报告的判断链、取舍链和建议链。

现有工作流已经能生成“战略竞争分析 + 中国应对策略建议型”文章，例如“美国 AI 人才战略布局及我国应对策略”。当前问题是：如果继续扩展到“国际经验借鉴 / 单一政策分析 + 中国应对”类文章，不能再把战略对抗体例硬写在主流程里。

## 二、审核对象

审核文件：

`strategic_response_workflow/reasoning_dna/DESIGN.md`

核对过的相关代码和提示词包括：

- `strategic_response_workflow/workflow/runner.py`
- `strategic_response_workflow/prompts/retrieval.md`
- `strategic_response_workflow/prompts/task_redefinition.md`
- `strategic_response_workflow/prompts/material_roles.md`
- `strategic_response_workflow/prompts/pressure_judgment_mapping.md`
- `strategic_response_workflow/prompts/planning.md`
- `strategic_response_workflow/prompts/suggestion_pool.md`
- `strategic_response_workflow/prompts/policy_priority.md`
- `strategic_response_workflow/templates/article_template.md`

## 三、对 Claude 方案的总体判断

Claude 方案的核心方向是对的：`style_dna` 管文风，`reasoning_dna` 管判断和推理深度，这个职责划分成立。

它也准确识别了当前工作流的问题：现有 6 个判断/构思步骤基本都是硬写在 prompt 中，缺少像 `style_dna` 那样可运行时加载、可演化的推理规则层。

但该方案不能直接照做。它低估了现有工作流中“战略应对型”被写死的范围。当前不是只有 4 个判断 prompt 绑定了战略竞争体例，检索、文章模板、政策优先序也都绑定了“目标国家战略分析 + 中国应对策略”。

## 四、主要审核意见

### 1. 只改 4 个 prompt 不够

Claude 方案提出改造：

- `task_redefinition.md`
- `material_roles.md`
- `planning.md`
- `suggestion_pool.md`

但实际还必须处理：

- `retrieval.md`：当前检索任务围绕国际竞争、国家安全、产业竞争、科技竞争、中国压力等展开。
- `policy_priority.md`：当前排序标准包含核心压力、国家安全、关键技术、长期竞争等战略应对逻辑。
- `article_template.md`：当前模板是“目标国家战略布局及我国应对策略”，不是国际经验借鉴模板。

因此，如果只按 Claude 方案改 4 个 prompt，会得到一个表面可切换、实际仍被旧战略模板牵引的混合系统。

### 2. “默认体例是借鉴”不宜直接采用

当前 `runner.py` 顶部说明和实际流程都服务于“目标国家战略分析 + 中国应对策略建议”。已有 DeepSeek 和 Opus 跑通过该体例，并形成了比较好的产出。

因此不应贸然把默认体例改成“借鉴”。更稳的方式是引入 `report_type`：

- `strategic_response`：战略竞争分析 + 中国应对。
- `benchmark_response`：国际经验借鉴 / 单一政策分析 + 中国应对。
- `auto`：后续可选，由路由模块判断。

### 3. 路由机制需要工程化

Claude 方案提到“由选题元数据或一道判别逼问决定体例”，但没有说明结果如何保存和复现。

建议新增固定产物：

- `judgment_outputs/report_type_route.md`
- `input.yaml` 中记录 `report_type`
- `logs/run_log.md` 中记录本次加载了哪个体例模块

这样后续才能解释为什么某次任务走了战略应对体例，另一次任务走了经验借鉴体例。

### 4. reasoning_dna 需要进入审查闭环

Claude 方案主要把 reasoning_dna 注入判断和构思阶段，但写作、审查、修改阶段也要读取 reasoning_dna 的关键约束。

尤其要审查：

- 正文是否违反了前面已经做出的“证据降级”。
- 是否把“动向”写成了“成熟经验”。
- 是否把“不可照搬”写成了“直接借鉴”。
- 是否把“前提不成立”的建议写成了立即推进。
- 是否超出了 `no_overreach` 中列出的证据边界。

### 5. “必须至少发生一个降级”这类要求需要放松

Claude 方案中有些规则要求至少有一条做法被判定为不可照搬、至少一个迁移前提不成立。

这个方向能防止文章过度乐观，但如果写得太硬，会诱导模型为了满足格式而制造问题。

更合理的表述是：

必须完成降级扫描；如果没有降级，也要说明证据为何足以支持。重点不是强行否定一条，而是留下可审查的取舍记录。

## 五、形成的新架构判断

本轮讨论形成了新的架构方向：

不应继续把“战略竞争分析”写死在主工作流里。主工作流应拆成：

1. 通用流程引擎。
2. 可载入的文章体例模块。
3. 共用的 style_dna 文风层。
4. 各体例自己的 reasoning_dna 推理层。

现有战略应对工作流不删除，而是从主流程中分离出来，变成一个可载入模块。

## 六、建议目标结构

建议改造为：

```text
strategic_response_workflow/
├── workflow/
│   └── runner.py
├── report_modules/
│   ├── strategic_response/
│   │   ├── module.yaml
│   │   ├── retrieval.md
│   │   ├── prompts/
│   │   ├── templates/
│   │   │   └── article_template.md
│   │   └── reasoning_dna/
│   └── benchmark_response/
│       ├── module.yaml
│       ├── retrieval.md
│       ├── prompts/
│       ├── templates/
│       │   └── article_template.md
│       └── reasoning_dna/
├── style_dna/
└── runs/
```

其中：

- `workflow/runner.py` 只负责调度、文件传输、NotebookLM 调用、LLM 调用、日志、审查循环、导出 Word。
- `report_modules/strategic_response/` 保存现有战略应对型体例。
- `report_modules/benchmark_response/` 新增国际经验借鉴 / 单一政策分析 + 中国应对体例。
- `style_dna/` 作为共用文风层，不绑定某个体例。
- 每个模块可以有自己的 `reasoning_dna/`。

## 七、两个体例的核心推理链

### strategic_response：战略竞争分析 + 中国应对

适用于：

- 美国 AI 人才战略布局及我国应对策略
- 某国某战略对我国的影响及应对建议
- 目标国家战略动向、竞争布局、规则塑造、技术封锁、人才争夺等主题

核心推理链：

```text
目标国家措施 -> 战略意图 -> 对中国压力 -> 中国短板 -> 应对策略
```

### benchmark_response：国际经验借鉴 / 单一政策分析 + 中国应对

适用于：

- 国外校园餐政策经验及启示
- 主要国家学制改革经验及我国应对
- 国外体育教师培养聘任政策及启示
- 主要国家超常儿童培养政策及中国建议

核心推理链：

```text
外部政策做法 -> 成因条件 -> 有效性证据 -> 迁移前提 -> 中国适配建议
```

## 八、reasoning_dna 的定位

reasoning_dna 不应替代文章模板，也不应替代流程 prompt。

它的职责是作为“推理检查与逼问层”，要求模型在关键判断处回答：

- 这是不是证据支持的判断？
- 这是成熟经验，还是政策动向？
- 这是普遍规律，还是特定国情产物？
- 这条建议能否迁移到中国？
- 迁移前提是否成立？
- 如果不成立，应该先补什么制度条件？
- 哪些判断材料不足，不能写进正文？

它应产出可审查的中间判断，而不是隐藏思维链。

## 九、后续建议实施顺序

### 第一步：体例模块化重构

把现有战略体例完整迁移到：

`report_modules/strategic_response/`

要求迁移后原有主题仍能跑通，不能破坏当前已经验证过的战略应对工作流。

### 第二步：新增 `report_type`

在命令行和配置中加入：

```bash
--report-type strategic_response
--report-type benchmark_response
--report-type auto
```

先实现显式指定，不急着做自动路由。

### 第三步：建设借鉴体例模块

新增：

`report_modules/benchmark_response/`

包含：

- 借鉴体例检索提示词。
- 借鉴体例任务重定义提示词。
- 借鉴体例材料角色提示词。
- 借鉴体例构思提示词。
- 借鉴体例建议池提示词。
- 借鉴体例政策优先序提示词。
- 借鉴体例文章模板。

### 第四步：接入 reasoning_dna

先做 MVP 两刀：

- `cause.md`：成因刀，防止只罗列差异。
- `efficacy.md`：有效性刀，防止把政策动向当成熟经验。

后续再加入：

- `commonality.md`
- `typology.md`
- `tension.md`
- `transfer.md`
- `no_overreach.md`

### 第五步：审查闭环

审查和修改阶段必须读取本次模块的 reasoning_dna，并检查正文是否违反前期判断。

## 十、当前共识

可以把战略体例从原有工作流中分离出来，变成可载入模块；同时新增一个借鉴体例模块，形成一个更完整、更通用的“外部政策分析 + 中国应对”写作系统。

这个方向比继续在旧 prompt 上叠规则更稳，也更适合后续扩展多种政策报告类型。

当前推荐路线：

```text
先模块化现有战略体例
-> 再新增借鉴体例
-> 再接入 reasoning_dna
-> 最后做自动路由和多体例评测
```

## 十一、新增要求：体例应由 agent 自动判断

用户进一步明确：agent 在运行 workflow 时，不应只依赖人工指定体例，而应根据文章主题、检索材料和自己的政策写作判断，主动选择合适体例。

因此后续架构应加入一个前置体例判断模块：

```text
输入主题 + 知识库名称 + 初步任务信息
-> agent 判断文章问题类型
-> 输出体例选择卡
-> 加载对应 report_module
-> 进入检索、构思、写作、审查流程
```

体例选择不应只输出一个标签，而应说明：

- 本文更像哪类文章。
- 为什么选择该体例。
- 是否存在混合体例特征。
- 是否需要叠加其他体例的局部 reasoning_dna。
- 如果体例判断不确定，应如何降级处理。

建议运行产物固定保存为：

`judgment_outputs/report_type_route.md`

并在 `input.yaml` 和运行日志中记录最终加载的体例模块。

后续命令行中的 `--report-type` 可以保留，但建议语义改为：

- `--report-type auto`：默认，由 agent 自动判断。
- `--report-type strategic_response`：人工强制战略应对体例。
- `--report-type benchmark_response`：人工强制经验借鉴体例。

默认应采用 `auto`，这样工作流更接近“agent 根据主题和思路选择写作路线”，而不是简单执行固定模板。
