# 政策热点研判写作 Agent 工程调研与方案

## 1. 目标定位

本调研围绕一个具体写作 Agent：基于 NotebookLM 中已经整理好的政策知识库，自动完成“热点梳理、主题归类、政策前沿比较、影响研判、启发建议”的报告写作。

这里不再把“来源可追溯”作为核心工程问题。NotebookLM 本身已经能处理来源引用与出处追踪。写作 Agent 要解决的是：

```text
拆问题
定维度
组织材料包
控制报告结构
把材料转化为文章
```

因此系统的工程目标不是“让模型一次性写报告”，而是构建一个可重复执行的写作流水线：

```text
报告任务
→ 检索问题规划
→ NotebookLM 检索
→ 材料信息包
→ 比较矩阵 / 影响表 / 启发表
→ 分章节写作
→ 结构与逻辑校验
→ 终稿生成
```

## 2. zread.ai 调研记录

本次使用 Kimi WebBridge 在 [zread.ai](https://zread.ai/) 查阅相关开源项目，重点关注“查询规划、RAG 材料组织、Agent 编排、章节生成、质量校验”等工程机制。

| 项目 | zread 链接 | 可借鉴机制 | 对应写作 Agent 功能 |
|---|---|---|---|
| LangGraph | https://zread.ai/langchain-ai/langgraph | StateGraph、节点/边、条件路由、共享状态、Reducer、Checkpoint、子图、多 Agent 模式 | 控制报告结构、自动化步骤执行、失败重跑 |
| Local Deep Researcher | https://zread.ai/langchain-ai/local-deep-researcher | IterDRAG：生成查询、搜索、总结、反思缺口、生成后续查询、循环完善 | 拆问题、补充检索、材料缺口追问 |
| RAGFlow | https://zread.ai/infiniflow/ragflow | 文档理解、模板化分块、摄取流水线、GraphRAG、Agent 画布、MCP 集成 | 材料包组织、维度化抽取、流程节点化 |
| LlamaIndex | https://zread.ai/run-llama/llama_index | 数据连接器、NodeParser、索引、检索器、查询引擎、响应合成器、AgentWorkflow | 检索管线、子问题查询、材料到回答合成 |
| Haystack | https://zread.ai/deepset-ai/haystack | Component、Pipeline、Retriever、Ranker、PromptBuilder、Generator、Router、Joiner | 可组合材料检索流水线 |
| CrewAI | https://zread.ai/crewAIInc/crewAI | Flows 控制流程，Crews 承担智能任务，Agents + Tasks + YAML 配置 | 多角色写作 Agent、任务依赖管理 |
| AutoGen | https://zread.ai/microsoft/autogen | 多 Agent 团队、异步消息、交接、终止条件、GroupChat、MCP 工具集成 | 审稿、反思、角色协作 |
| AI-Researcher | https://zread.ai/HKUDS/AI-Researcher | 研究生命周期自动化、MetaChain、paper_agent、模板化论文生成 | 章节模板、研究流程拆解、成稿器 |
| graph-rag-agent | https://zread.ai/1517005260/graph-rag-agent | GraphRAG + DeepSearch，多跳材料组织 | 跨主题热点关系检索 |
| vibe-writing-workflow | https://zread.ai/Tasihi89/vibe-writing-workflow | 学习 Agent、结构 Agent、写作 Agent、成稿 Agent、知识卡片 | 材料卡片化、章节化写作 |

## 3. 工程问题凝练

### 问题 1：写作任务如何规格化

**问题定义**

用户输入通常是自然语言，例如“围绕政策热点做比较分析，写影响和启发”。系统必须先把它转成可执行任务规格。

**输入**

```text
用户写作需求
目标读者
报告主题
知识库范围
已有主题分类
输出体例
时间范围
重点政策领域
```

**输出**

```json
{
  "report_topic": "政策热点识别与前沿比较分析",
  "sections": ["热点梳理", "主题归类", "比较分析", "影响研判", "启发建议"],
  "knowledge_source": "NotebookLM",
  "writing_style": "政策研究报告",
  "retrieval_mode": "material_extraction",
  "source_trace_mode": "handled_by_notebooklm"
}
```

**关键难点**

要区分“用户想写什么”和“系统怎么执行”。用户说的是写作意图，Agent 需要转成章节、检索问题、维度、输出字段。

**验收标准**

任务规格能直接驱动后续查询规划；报告章节完整；不会把用户没有要求的内容强行加入。

### 问题 2：总任务如何拆成 NotebookLM 可执行的检索问题

**问题定义**

不能直接问 NotebookLM “请写一篇报告”，而要把报告拆成多个可检索、可加工的问题。

**输入**

```text
任务规格
报告章节
已有主题目录
目标分析维度
```

**输出**

`QueryJob` 列表：

```json
{
  "job_id": "hotspot_scan_001",
  "section": "热点梳理",
  "query_type": "full_notebook_scan",
  "prompt": "请基于当前知识库提取近期反复出现、跨主题出现的政策热点...",
  "expected_fields": ["热点名称", "相关关键词", "所属主题", "政策问题", "政策工具", "继续追问方向"],
  "next_use": "生成热点候选表"
}
```

**关键难点**

检索问题过宽会得到泛化答案；过窄会遗漏跨主题信号。需要分层：

```text
全库扫描
→ 按主题检索
→ 单热点深挖
→ 固定维度比较
→ 影响与启发追问
```

**可借鉴方案**

Local Deep Researcher 的 IterDRAG 模式值得借鉴：先生成查询，再检索，再总结，再反思缺口，再生成后续查询。对本任务可改写为：

```text
生成报告检索问题
→ 调用 NotebookLM ask
→ 结构化结果
→ 检查字段缺口
→ 生成补问
→ 更新材料包
```

### 问题 3：分析维度如何固定下来

**问题定义**

比较分析、影响研判、启发建议如果没有固定维度，模型会自由发挥，导致每次报告结构不同。

**输入**

```text
报告类型
政策主题
已有主题分类
用户关注点
```

**输出**

`SchemaRegistry`：

```json
{
  "HotspotSchema": ["热点名称", "关键词", "政策问题", "所属主题", "政策对象", "政策工具", "升温理由"],
  "ThemeSchema": ["主主题", "子主题", "交叉主题", "归类说明", "分类争议"],
  "ComparisonSchema": ["政策目标", "治理主体", "技术路径", "实施机制", "风险治理", "公平取向", "评价机制", "前沿特征"],
  "ImpactSchema": ["教育治理", "学校实践", "教师发展", "学生学习", "教育评价", "平台资源", "伦理安全"],
  "InsightSchema": ["研究启发", "实践启发", "治理启发", "知识库建设启发", "监测启发"]
}
```

**关键难点**

维度太松会失控，太死会漏掉新议题。建议固定主字段，同时保留：

```text
emerging_dimension
caution_note
missing_information
```

**可借鉴方案**

RAGFlow 的组件间数据契约使用模式校验，组件边界处强制结构正确。写作 Agent 也应让每一步输出都按 schema 校验，缺字段就回到 NotebookLM 补问。

### 问题 4：材料包如何从 NotebookLM 检索结果中生成

**问题定义**

NotebookLM 返回的是回答。写作 Agent 需要把回答整理成可复用的材料信息包。这个材料包不是证据包，不承担来源追溯，只承担写作信息编排。

**输入**

```text
NotebookLM ask 返回结果
热点列表
主题分类
维度 schema
```

**输出**

`MaterialPackage`：

```json
{
  "package_id": "hotspot_ai_governance",
  "hotspot": "AI教育治理",
  "section_targets": ["热点梳理", "比较分析", "影响研判"],
  "main_theme": "人工智能教育政策",
  "cross_themes": ["教师发展", "教育评价", "数据安全"],
  "policy_points": [],
  "actors": [],
  "tools": [],
  "mechanisms": [],
  "risks": [],
  "comparison_items": [],
  "impact_items": [],
  "claim_candidates": [],
  "caution_notes": [],
  "missing_questions": []
}
```

**关键难点**

NotebookLM 的回答可能重复、层级不一致、颗粒度不同。需要做三类加工：

```text
去重：合并重复政策观点
归类：把材料放入主题和维度
降级：把推导性判断标为 caution，不直接写成事实
```

**可借鉴方案**

Haystack 的 Pipeline 思路适合这里：把材料处理拆成组件。

```text
NotebookLMResultLoader
→ FieldExtractor
→ DimensionClassifier
→ DuplicateMerger
→ GapDetector
→ MaterialPackageWriter
```

### 问题 5：报告结构如何被流程控制

**问题定义**

报告章节之间存在依赖。如果热点没确定，就不能可靠地做主题归类；如果比较矩阵没形成，影响研判就容易空泛。

**输入**

```text
MaterialPackage
hotspot_candidates
theme_hotspot_matrix
comparison_matrix
impact_table
```

**输出**

章节状态机：

```text
INIT
→ QUERY_PLANNED
→ MATERIAL_RETRIEVED
→ MATERIAL_NORMALIZED
→ SECTION_OUTLINED
→ SECTION_DRAFTED
→ SECTION_CHECKED
→ DONE
```

如果校验失败：

```text
SECTION_CHECKED
→ NEED_MORE_RETRIEVAL
→ QUERY_PLANNED
```

**章节依赖**

```text
热点梳理 DONE
→ 主题归类

热点梳理 + 主题归类 DONE
→ 比较分析

比较分析 DONE
→ 影响研判

影响研判 DONE
→ 启发建议

全部 DONE
→ 终稿整合
```

**可借鉴方案**

LangGraph 是最合适的主控方案。它的 StateGraph、条件边、checkpoint、reducer、可恢复执行，正好对应长流程写作。

建议状态对象：

```json
{
  "task": {},
  "query_jobs": [],
  "materials": {},
  "hotspot_table": [],
  "theme_matrix": [],
  "comparison_matrix": [],
  "impact_table": [],
  "sections": {
    "热点梳理": {"status": "DONE", "draft": "...", "missing": []},
    "主题归类": {"status": "MATERIAL_NORMALIZED", "draft": "", "missing": []}
  },
  "final_report": ""
}
```

### 问题 6：多 Agent 如何分工但不失控

**问题定义**

可以用多个 Agent 分功能，但不能让它们自由聊天。每个 Agent 必须有固定输入、固定输出和责任边界。

**推荐角色**

```text
TaskSpecAgent：任务规格化
QueryPlannerAgent：生成 NotebookLM 检索问题
MaterialPackAgent：整理材料包
ComparisonAgent：生成比较矩阵
ImpactAgent：生成影响表
InsightAgent：生成启发表
SectionWriterAgent：分章节写作
ReviewerAgent：检查维度缺失、章节重复、推导过强
FinalEditorAgent：整合终稿
```

**可借鉴方案**

CrewAI 的核心启发是：Flow 管控制，Crew/Agent 做任务。对本系统来说：

```text
Flow = 报告写作状态机
Agents = 各章节/各功能执行器
Tasks = 固定输入输出的结构化任务
```

AutoGen 的启发是：多 Agent 要有交接规则和终止条件。这里可以设计：

```text
当 SectionWriter 输出后，Reviewer 只能返回：
- PASS
- NEED_MORE_MATERIAL
- NEED_REWRITE
- DIMENSION_MISSING
```

不能让 Reviewer 直接重写全文，否则职责混乱。

### 问题 7：材料如何转化为政策研究报告

**问题定义**

材料包只是结构化素材，不能直接等于文章。需要一个成稿器把材料转成政策研究报告语言，同时避免材料堆砌。

**输入**

```text
章节契约
材料包
比较矩阵
影响表
启发表
文风规则
```

**输出**

```text
章节提纲
章节草稿
审稿问题
修订稿
终稿
```

**章节模板**

```text
热点梳理：
现象判断 + 热点说明 + 热点分级 + 趋势边界

主题归类：
主题框架 + 热点映射 + 交叉关系 + 分类说明

比较分析：
比较维度 + 类型归纳 + 差异解释 + 前沿特征

影响研判：
政策变化 + 作用对象 + 可能影响 + 限制条件

启发建议：
发现归纳 + 行动启发 + 后续监测方向
```

**可借鉴方案**

AI-Researcher 的 paper_agent 提供了“按章节生成”的思路。对政策报告来说，应避免一次性生成全文，而是：

```text
材料包
→ 章节观点提纲
→ 段落任务列表
→ 分段生成
→ 章节内校验
→ 跨章节校验
→ 终稿整合
```

## 4. 推荐系统架构

### 4.1 总体架构

```text
ReportTask
  ↓
TaskSpecAgent
  ↓
QueryPlannerAgent
  ↓
NotebookLMRetriever
  ↓
MaterialPackBuilder
  ↓
MatrixBuilder
  ├─ hotspot_table
  ├─ theme_hotspot_matrix
  ├─ comparison_matrix
  ├─ impact_table
  └─ insight_table
  ↓
SectionStateMachine
  ↓
SectionComposer
  ↓
Reviewer
  ↓
FinalEditor
  ↓
FinalReport
```

### 4.2 核心模块

| 模块 | 职责 | 关键输入 | 关键输出 |
|---|---|---|---|
| TaskSpecAgent | 把自然语言任务转成规格 | 用户需求 | ReportTask |
| QueryPlannerAgent | 拆成 NotebookLM 查询 | ReportTask、SchemaRegistry | QueryJob[] |
| NotebookLMRetriever | 调用 NotebookLM 获取材料 | QueryJob | RawRetrievalResult |
| MaterialPackBuilder | 整理材料包 | RawRetrievalResult | MaterialPackage[] |
| MatrixBuilder | 生成热点表、比较矩阵、影响表 | MaterialPackage[] | Matrix artifacts |
| SectionStateMachine | 控制章节依赖和重跑 | SectionState | 状态转移 |
| SectionComposer | 生成章节草稿 | 章节契约、材料包 | SectionDraft |
| Reviewer | 检查空泛、缺维度、推导过强 | SectionDraft、MaterialPackage | ReviewResult |
| FinalEditor | 合并终稿 | 所有章节 | FinalReport |

## 5. NotebookLM 查询设计

### 5.1 查询任务类型

```text
full_notebook_scan
theme_retrieval
hotspot_deep_dive
comparison_matrix
impact_analysis
insight_generation
gap_followup
```

### 5.2 查询模板示例

**热点扫描**

```text
请基于当前知识库中所有已归类政策文件，提取当前政策热点。

请不要写文章，只输出结构化信息：
1. 热点名称
2. 相关关键词
3. 所属已有主题
4. 涉及的政策问题
5. 主要政策对象
6. 相关政策工具
7. 为什么可视为热点
8. 可继续深入分析的方向
```

**单热点深挖**

```text
请围绕热点【{hotspot}】提取写作所需材料。

请输出：
1. 政策背景
2. 主要回应的问题
3. 不同政策文件中的主要观点
4. 主要政策措施
5. 实施主体
6. 治理机制
7. 风险防控
8. 与其他热点的关系
9. 可用于报告写作的判断句
10. 需要谨慎表述的地方
```

**比较矩阵**

```text
请围绕以下热点，按照固定维度进行政策比较分析。

热点包括：
{hotspot_list}

比较维度包括：
1. 政策目标
2. 治理主体
3. 政策工具
4. 技术路径
5. 实施机制
6. 风险治理
7. 公平与包容
8. 评价与反馈机制
9. 政策前沿特征

请输出比较矩阵，不要写成文章。
```

**影响研判**

```text
请基于知识库材料，分析这些政策热点可能带来的影响。

请按以下维度输出：
1. 对教育治理的影响
2. 对学校实践的影响
3. 对教师发展的影响
4. 对学生学习的影响
5. 对教育评价的影响
6. 对技术平台或资源建设的影响
7. 对公平、伦理、安全的影响

请区分：
- 政策文件明确提出的影响
- 可以根据政策趋势谨慎推导的影响
- 目前材料不足、不能下结论的部分
```

## 6. 问题解决方案

### 方案 A：QueryPlanner 查询规划器

**解决问题**

把报告写作任务拆成 NotebookLM 可执行检索任务。

**核心设计**

每个 QueryJob 绑定：

```text
章节
主题
热点
维度
查询范围
期望字段
后续用途
```

**执行流程**

```text
ReportTask
→ 读取章节结构
→ 套用章节查询模板
→ 生成 QueryJob
→ 执行 NotebookLM ask
→ 检查字段缺口
→ 生成 followup QueryJob
```

**验收标准**

每个章节至少有一个查询任务；重点热点有深挖查询；比较分析有固定维度矩阵查询；影响研判区分事实与推导。

### 方案 B：SchemaRegistry 维度注册表

**解决问题**

防止写作维度漂移。

**核心设计**

为每类中间产物定义 schema：

```text
HotspotSchema
ThemeSchema
MaterialPackageSchema
ComparisonSchema
ImpactSchema
InsightSchema
SectionDraftSchema
ReviewSchema
```

**执行流程**

```text
选择报告类型
→ 加载 schema
→ 从 schema 生成 prompt 字段要求
→ 校验 NotebookLM 返回内容
→ 缺字段触发补问
```

**验收标准**

比较矩阵字段稳定；影响表字段稳定；材料包能被后续章节复用。

### 方案 C：MaterialPackage 材料信息包

**解决问题**

把 NotebookLM 返回结果变成可复用写作素材。

**核心设计**

材料按热点组织，每条材料必须绑定：

```text
章节用途
分析维度
材料类型：事实 / 归纳 / 推导 / 谨慎项
可生成的判断句
缺口问题
```

**执行流程**

```text
RawRetrievalResult
→ 字段抽取
→ 维度分类
→ 去重合并
→ 谨慎项标注
→ 缺口检测
→ MaterialPackage
```

**验收标准**

每个重点热点都有材料包；每个材料包能支撑至少一个章节；无法归入章节的材料不进入正文。

### 方案 D：SectionStateMachine 章节状态机

**解决问题**

控制报告结构和章节依赖。

**核心设计**

用 LangGraph 式状态图实现：

```text
热点梳理
→ 主题归类
→ 比较分析
→ 影响研判
→ 启发建议
→ 终稿整合
```

每个章节有状态：

```text
QUERY_PLANNED
MATERIAL_RETRIEVED
MATERIAL_NORMALIZED
SECTION_OUTLINED
SECTION_DRAFTED
SECTION_CHECKED
DONE
```

**验收标准**

任意时刻能知道每节缺什么材料、卡在哪一步、下一步该问 NotebookLM 什么。

### 方案 E：SectionComposer + Reviewer 成稿与校验

**解决问题**

把材料包转成政策研究报告，而不是材料堆砌。

**核心设计**

先生成章节观点提纲，再生成段落。每个段落绑定材料包中的 claim_candidate。

```text
SectionContract
→ section_outline
→ paragraph_tasks
→ draft
→ review
→ revision
```

**校验规则**

```text
是否回答本节问题
是否跑到其他章节
是否缺少固定维度
是否出现材料包外判断
是否把推导写成事实
是否只是罗列材料
```

**验收标准**

每节有中心判断；比较分析不是文件罗列；影响研判有事实与推导边界；启发建议能回到前文发现。

### 方案 F：Multi-Agent 角色分工

**解决问题**

让多 Agent 提升效率，但不让流程失控。

**核心设计**

主控 Agent 只负责编排，不直接让所有 Agent 自由讨论。

```text
PlannerAgent：输出 QueryJob
RetrieverAgent：执行 NotebookLM 查询
PackagerAgent：输出 MaterialPackage
ComparatorAgent：输出 comparison_matrix
ImpactAgent：输出 impact_table
WriterAgent：输出 section_draft
ReviewerAgent：输出 review_result
EditorAgent：输出 final_report
```

**验收标准**

每个 Agent 有固定输入输出；Reviewer 不直接重写全文；主控流程根据 ReviewResult 决定补检索、重写或通过。

## 7. 推荐落地顺序

建议分三阶段实现。

### 第一阶段：材料检索稳定化

先做三件事：

```text
QueryPlanner
SchemaRegistry
MaterialPackage
```

这三件事解决“如何从 NotebookLM 知识库中稳定检索出所需材料信息”。

### 第二阶段：章节流程控制

再做：

```text
SectionStateMachine
MatrixBuilder
GapDetector
```

这一步解决“写作过程如何自动化分步骤执行”。

### 第三阶段：成稿与审稿

最后做：

```text
SectionComposer
Reviewer
FinalEditor
```

这一步解决“如何把材料转化为政策研究报告”。

## 8. 最小可行版本

MVP 不建议一开始就做完整多 Agent。最小版本可以是：

```text
1. 输入报告任务
2. 生成 5 类 NotebookLM 查询 prompt
3. 手动或自动执行 NotebookLM ask
4. 把返回结果整理成 MaterialPackage JSON
5. 生成 hotspot_table / comparison_matrix / impact_table
6. 按固定章节模板生成 Markdown 报告
7. 用 Reviewer prompt 检查维度缺失和推导过强
```

MVP 文件结构建议：

```text
writing_agent/
  schemas.py
  query_planner.py
  notebooklm_client.py
  material_pack.py
  matrix_builder.py
  section_composer.py
  reviewer.py
  workflow.py
prompts/
  hotspot_scan.txt
  theme_mapping.txt
  hotspot_deep_dive.txt
  comparison_matrix.txt
  impact_analysis.txt
  insight_generation.txt
outputs/
  material_packages/
  matrices/
  drafts/
  final_report.md
```

## 9. 结论

这个写作 Agent 的核心不在“生成文章”，而在三个前置工程能力：

```text
检索问题生成器
材料包生成器
报告结构控制器
```

NotebookLM 已经处理了知识库和来源追溯，写作 Agent 应该围绕 NotebookLM 的问答能力构建上层流程：

```text
拆问题
→ 定 schema
→ 问 NotebookLM
→ 组织材料包
→ 形成矩阵
→ 分章节写作
→ 校验与补问
→ 终稿
```

推荐最终技术组合：

```text
LangGraph 思路做主控状态机
NotebookLM 做知识库检索
Haystack / LlamaIndex 思路做材料管线
RAGFlow 思路做材料结构化与流程节点
CrewAI / AutoGen 思路做多角色分工
AI-Researcher 思路做章节模板化生成
```

最优先实现的不是多 Agent 对话，而是 `QueryPlanner + SchemaRegistry + MaterialPackage`。只要这三者稳定，后面的报告写作就会可控得多。
