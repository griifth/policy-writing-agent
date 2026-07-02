# 政策写作工作流上下文记录

记录时间：2026-06-22  
工作目录：`/Users/hujingkai/Documents/New project/example1`

## 一、当前核心项目

当前主要工作流目录：

```text
strategic_response_workflow/
```

该工作流用于生成“战略竞争分析 + 中国应对策略建议型”政策文章。典型输入包括：

```text
topic: 美国AI人才战略布局及我国应对策略
target_country: 美国
strategy_domain: AI人才
notebook_name: 中美人才
```

主入口：

```text
strategic_response_workflow/workflow/runner.py
```

对照提示词入口：

```text
strategic_response_workflow/workflow/policy_n_prompt_runner.py
```

## 二、用户设定的边界

1. 工作流应尽量在当前目录内闭环，不随意读取或修改相邻目录。
2. NotebookLM skill 可以调用和查看，但不能修改。
3. 事实材料来自 NotebookLM 知识库，不应由写作模型自行编造。
4. 写作模型可以是 DeepSeek 或 Opus 兼容 API。
5. 不保存或暴露模型思维链。
6. API key 不进入 Git，不写入记录文件。
7. 运行产物放入 `runs/`，运行日志和任务状态可追溯。
8. 工作流要保持通用，不应只为“中美AI人才”写死。

## 三、当前工作流模块

主工作流顺序：

```text
init
resolve_notebook
build_retrieval_prompts
retrieve_materials
redefine_task
assign_material_roles
map_pressure_judgment
plan_article
build_suggestion_pool
prioritize_policy_options
write_draft
review_draft
revise_article
compare_with_sample
export_docx
archive_log
```

对应提示词目录：

```text
strategic_response_workflow/prompts/
```

核心提示词：

```text
retrieval.md
task_redefinition.md
material_roles.md
pressure_judgment_mapping.md
planning.md
suggestion_pool.md
policy_priority.md
writing.md
review.md
revision.md
```

其中真正引导 LLM 做“显性思考产物”的是：

```text
task_redefinition.md
material_roles.md
pressure_judgment_mapping.md
planning.md
suggestion_pool.md
policy_priority.md
```

这些模块不要求输出思维链，而是输出可检查的中间产物，如任务重定义、材料角色、压力映射、论证链构思、建议池、政策优先序。

## 四、已经完成的重要运行

### 1. DeepSeek 版

运行 ID：

```text
run-20260621-153714-85b5e24e
```

路径：

```text
strategic_response_workflow/runs/run-20260621-153714-85b5e24e/
```

产物：

```text
final_article_reviewed.md
final_article_reviewed.docx
review_reports/review_iter1.md
review_reports/review_iter2.md
review_reports/template_match_review.md
```

结论：

- 工作流完整跑通。
- Word 文件通过 `unzip -t` 完整性检查。
- 示例对比报告判断“达到并部分超过示例”。
- 后续发现关键数据曾出现“相关材料显示”模糊引源，已把提示词改为关键数据必须保留报告名、机构名、年份或材料编号。

### 2. Opus API 版

运行 ID：

```text
run-20260621-161750-f4e75d5d
```

路径：

```text
strategic_response_workflow/runs/run-20260621-161750-f4e75d5d/
```

说明：

- 复用了 DeepSeek 那次的 NotebookLM 检索材料。
- 使用 `anthropic_compat` 后端。
- API key 通过临时环境变量传入，没有写入项目文件。

产物：

```text
final_article_reviewed.md
final_article_reviewed.docx
review_reports/review_iter1.md
review_reports/review_iter2.md
review_reports/template_match_review.md
```

结论：

- 两轮审查都判定“达到示例标准”。
- 最终对比报告判定“达到并部分超过示例文章水平”。
- Word 文件通过完整性检查。
- 残余问题：个别英文术语如 `Brain Drain` / `dilemma` 可进一步中文化；少量四字短语略接近口号化；部分数据出处还可更显性。

## 五、GitHub 上传记录

已经提交并推送新工作流。

远端：

```text
ssh://git@ssh.github.com:443/griifth/policy-writing-agent.git
```

分支：

```text
International-Policy-Comparison-Template-Workflow
```

提交：

```text
4f270f2 Add strategic response workflow
```

提交内容：

- `strategic_response_workflow/`
- `README.md`
- `RUN_RECORD.md`
- `.env.example`
- `.gitignore`
- 主工作流代码
- prompt 模板
- style_dna wiki
- 示例文章抽象模板

没有提交：

- `.env`
- `runs/`
- 原始风格素材 `style_dna/raw/`
- 中间处理结果 `style_dna/processed/`
- API key

当前工作区仍有一些旧的未提交改动和未跟踪文件，之前没有处理。

## 六、style_dna 当前状态

当前已有文风 DNA：

```text
strategic_response_workflow/style_dna/wiki/
```

文件：

```text
voice.md
structure.md
sentence.md
forbidden.md
recommendation.md
self_check.md
```

作用：

- `voice.md`：政策研究声音与写作姿态。
- `structure.md`：结构范式与论证递进。
- `sentence.md`：句式、段落组织和表达模板。
- `forbidden.md`：禁用表达、AI 腔、口号化、文学化等失败模式。
- `recommendation.md`：政策建议写作规则和合理性标准。
- `self_check.md`：自动审查分层规则。

加载方式：

- 不是写死在 prompt 里。
- runner 运行时从 `style_dna/wiki/*.md` 读取。
- 写作、审查、修改阶段分别注入不同的 DNA 文件。
- 每次运行会复制快照到 `runs/<run-id>/style_dna_snapshot/`。

关键代码：

```text
strategic_response_workflow/workflow/runner.py
```

函数：

```text
_style_dna_text()
_copy_style_dna_snapshot()
```

## 七、三份稿件评分结果

用户要求派三个子 agent 分别评分：

1. DeepSeek 版
2. Opus 版
3. 人类参考稿《中美AI人才竞争及应对策略.docx》

比较目录：

```text
strategic_response_workflow/runs/compare-ds-opus-reference-20260621/
```

抽取文件：

```text
deepseek.md
opus.md
reference_human.md
```

评分结果：

| 稿件 | 总分 | 结构 | 战略判断 | 建议体系 | 证据严谨 | 文风 |
|---|---:|---:|---:|---:|---:|---:|
| Opus 版 | 83 | 18/20 | 21/25 | 22/25 | 9/15 | 13/15 |
| DeepSeek 版 | 81 | 18/20 | 20/25 | 21/25 | 9/15 | 13/15 |
| 人类参考稿 | 80 | 17/20 | 19/25 | 19/25 | 11/15 | 14/15 |

结论：

- Opus 版分析深度和建议体系最好。
- DeepSeek 版结构成熟，但部分表达更口号化。
- 人类参考稿文风更稳、更成熟，证据严谨性相对更好，但战略机制分析和建议落地不如 Opus。
- 最优方向：以 Opus 版为主体，吸收人类稿的简洁文风，再补事实核验和政策落地状态区分。

## 八、关于“如何引导 LLM 更好思考”的调研

用户要求派子 agent 搜索 GitHub 项目和文章。

子 agent 结论：

不要追求让模型输出完整思维链，而应让模型输出可检查的中间产物，例如：

```text
问题分解表
检索计划
证据矩阵
论点树
反方意见
审查清单
修改指令
```

高价值参考：

1. DSPy  
   链接：`https://github.com/stanfordnlp/dspy`  
   用指标自动优化 prompt / few-shot / pipeline。

2. Instructor / Structured Outputs  
   链接：`https://github.com/567-labs/instructor`  
   用结构化输出约束中间产物。

3. Anthropic: Building Effective Agents  
   链接：`https://www.anthropic.com/research/building-effective-agents`  
   强调 workflow、prompt chaining、routing、evaluator-optimizer。

4. STORM  
   链接：`https://github.com/stanford-oval/storm`  
   长文写作前先做多视角研究、提纲、引用绑定。

5. ReAct  
   链接：`https://github.com/ysymyth/ReAct`  
   检索和推理交替，适合证据绑定。

6. LangGraph  
   链接：`https://github.com/langchain-ai/langgraph`  
   图结构编排 workflow，支持状态持久化和人工介入。

7. Self-Refine  
   链接：`https://github.com/madaan/self-refine`  
   初稿、反馈、修改循环。

8. Reflexion  
   链接：`https://github.com/noahshinn/reflexion`  
   把失败模式沉淀为记忆，用于后续任务。

9. Tree of Thoughts  
   链接：`https://github.com/princeton-nlp/tree-of-thought-llm`  
   多候选构思，再评分选择。

10. Chain-of-Thought / Self-Consistency  
    作为底层启发，不建议公开输出完整思维链。

推荐对现有工作流的改造：

```text
Structured Outputs / schema
证据矩阵
多候选构思
审查问题结构化
失败模式记忆
```

## 九、reasoning_dna 讨论

用户指出：

- 现在已有 style_dna，但没有 reasoning_dna。
- 手头有 30 篇报告，其中 5-6 篇应与当前体例类似。
- 甲方反馈：内容质量是有的，但仍需改进；此外需要一些框架限制，让文章更像一篇报告。

已给出的建议：

新建：

```text
strategic_response_workflow/reasoning_dna/wiki/
```

建议包含 8 个文件：

```text
report_type.md
problem_framing.md
evidence_to_judgment.md
argument_chain.md
pressure_mapping.md
recommendation_logic.md
report_framework.md
failure_patterns.md
```

各文件作用：

1. `report_type.md`  
   定义这类文章是什么，不是什么。不是国际比较综述，不是材料摘要，而是“目标国家战略分析 + 中国应对策略”。

2. `problem_framing.md`  
   规定如何把题目改造成真正的问题。

3. `evidence_to_judgment.md`  
   规定如何从材料推出判断，并区分：
   - 已实施政策
   - 已立法授权
   - 报告建议
   - 拟议机制
   - 战略意图
   - 外部评价

4. `argument_chain.md`  
   固定推导链：

   ```text
   政策事实 -> 工具功能 -> 战略意图 -> 对中国压力 -> 中国短板 -> 应对方向
   ```

5. `pressure_mapping.md`  
   规定压力分类方式，避免随意造分类。

6. `recommendation_logic.md`  
   每条建议必须回答：
   - 回应哪个压力？
   - 针对中国哪个短板？
   - 政策对象是谁？
   - 靠什么工具起作用？
   - 谁牵头？
   - 有什么风险？

7. `report_framework.md`  
   解决“更像一篇报告”的问题，给文章加硬框架。

8. `failure_patterns.md`  
   记录生成稿常见失败模式：
   - 战略腔过重
   - 证据状态混淆
   - 建议宏大但不可执行
   - 标题像口号
   - 缺少章节递进
   - 像评论文章，不像正式报告

建议优先建设顺序：

1. 先做 `report_framework.md`。
2. 再做 `evidence_to_judgment.md` 和 `argument_chain.md`。
3. 最后做 `recommendation_logic.md` 和 `failure_patterns.md`。

## 十、近几轮对话内容记录

### 用户：如何学习人类文稿的文风

回复要点：

- 学人类文风不是仿写句子，而是抽象稳定写作习惯。
- 分四层：
  1. 提取文风 DNA。
  2. 把文风变成规则，不是例句。
  3. 嵌入写作、审查、修改模块。
  4. 形成文风评分器。
- 目标：Opus 的分析深度 + 人类稿的稳、短、准、克制。

### 用户：我们的写作dna呢？

回复要点：

- 已有 `style_dna`。
- 位置：`strategic_response_workflow/style_dna/wiki/`。
- 包含 voice、structure、sentence、forbidden、recommendation、self_check。
- 当前 DNA 是从用户“风格参考”那批政策研究文章中蒸馏出来的，属于通用政策研究文风 DNA。
- 还不是专门从《中美AI人才竞争及应对策略》人类参考稿提取的人类稿 DNA。
- 下一步可以做 `human_reference_style_dna`。

### 用户：现在这个文风dna 是引用进去 的还是写死了

回复要点：

- 不是写死，是运行时引用。
- runner 每次运行从 `style_dna/wiki/*.md` 读取并拼进写作、审查、修改提示词。
- 每次运行复制一份快照到 `runs/<run-id>/style_dna_snapshot/`。
- 改 `style_dna/wiki/*.md` 后下次运行自动生效。

### 用户：引导llm 思考的提示词在哪里

回复要点：

- 主工作流引导 LLM 思考的提示词在 `strategic_response_workflow/prompts/`。
- 核心是：
  - `task_redefinition.md`
  - `material_roles.md`
  - `pressure_judgment_mapping.md`
  - `planning.md`
  - `suggestion_pool.md`
  - `policy_priority.md`
- 这些不是输出思维链，而是输出可检查的中间判断产物。
- 另外 `imported_prompts/zhongmei_talent_policy_n/` 中有带 `<scratchpad>` 的对照提示词，但不是主工作流默认方式。

### 用户：派生一个子agent 去网上搜索如何引导llm 去更好的思考的github 项目或者文章

动作：

- 派出子 agent 搜索并返回项目列表。
- 主结论：优先使用可检查中间产物，而不是公开思维链。
- 推荐：DSPy、Instructor、Anthropic Effective Agents、STORM、ReAct、LangGraph、Self-Refine、Reflexion、Tree of Thoughts、Self-Consistency。

### 用户：我们现在没有推理dna 我们应该怎么构建 一个真正适合这套工作流的推理dna ？我现在 手头有30篇报告里边应该有类似体例的5-6篇，刚才汇报后 甲方反馈 内容质量是有的但是仍需改进 此外还需要一些框架限制显得它更像是一篇报告

回复要点：

- style_dna 管“怎么写”，reasoning_dna 管“怎么判断、组织、推导”。
- 不应把 30 篇报告混在一起蒸馏，应分为：
  1. 核心样本层：5-6 篇类似体例。
  2. 通用政策报告层：其余高质量报告。
  3. 反例层：甲方认为还需改进的生成稿。
- 建议建设 `reasoning_dna/wiki/`，包含 8 个文件。
- 最关键的是 `report_framework.md`，用于解决“更像一篇报告”的框架限制。
- 文章硬框架可设为：

```text
开篇：标志性政策事件 + 重要性 + 核心判断
第一部分：目标国家战略措施
第二部分：战略逻辑和压力机制
第三部分：对中国的影响与短板
第四部分：中国应对策略
```

每章功能：

```text
第一部分回答：对方做了什么？
第二部分回答：为什么这样做，战略意图是什么？
第三部分回答：这对中国意味着什么？
第四部分回答：中国怎么办？
```

## 十一、下一步建议

如果继续推进，建议直接做以下工作：

1. 从 30 篇报告中先挑出 5-6 篇最类似体例的核心样本。
2. 抽取每篇报告的结构、推理链、建议对应关系。
3. 生成 `reasoning_dna/wiki/report_framework.md`。
4. 生成 `reasoning_dna/wiki/evidence_to_judgment.md`。
5. 生成 `reasoning_dna/wiki/argument_chain.md`。
6. 修改 runner，让它像加载 `style_dna` 一样加载 `reasoning_dna`。
7. 用 DeepSeek 或 Opus 复跑，并与人类参考稿再次评分。

最优目标：

```text
Opus 的战略分析深度
+ 人类参考稿的文风克制
+ reasoning_dna 的报告框架与证据推理约束
= 更像正式报告的高质量政策研究稿
```
