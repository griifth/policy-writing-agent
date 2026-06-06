# 工作流流程图

## 1. 角色分工

```mermaid
flowchart LR
  A["Codex<br/>功能：编排、触发、传输文件、落盘"] --> B["提示词拼装脚本<br/>功能：拼装"]
  B --> C["NotebookLM skill<br/>功能：检索"]
  B --> D["DeepSeek v4 Pro API<br/>功能：构思、归类、写作、审查"]
  C --> E["检索材料与引用"]
  D --> F["章节构思、正文、审查报告"]
  E --> A
  F --> A
```

说明：

- Codex 不直接承担知识判断，主要负责触发流程、传递文件、保存产物、串联模块。
- NotebookLM skill 只负责把工程化检索提示词传给指定知识库，并返回材料与引用。
- DeepSeek v4 Pro 负责 3A、1B、2B、3C、第二章构思、第二章写作和审查。
- DeepSeek 的思考过程不保存、不展示，只保存最终回答。

## 2. 总体流程

```mermaid
flowchart TD
  A["输入<br/>topic + notebook_name<br/>功能：编排"] --> B["解析 NotebookLM 知识库<br/>功能：编排"]
  B --> B1["生成 task_state.md<br/>功能：任务状态"]
  B1 --> C{"是否唯一匹配知识库？"}
  C -- "否" --> C1["停止并请求确认<br/>功能：审查"]
  C -- "是" --> D["复制原始提示词到运行目录<br/>功能：拼装"]
  D --> E["拼装本次运行提示词<br/>功能：拼装"]

  E --> F["第一章流水线<br/>功能：检索 + 构思 + 写作 + 审查"]
  E --> G["第二章流水线<br/>功能：检索 + 构思 + 写作 + 审查"]

  F --> H["前两章统一证据审查<br/>功能：审查"]
  G --> H
  H --> I["第三章政策建议写作<br/>读取第一章和第二章成文<br/>功能：写作"]
  I --> J["组装报告骨架<br/>功能：编排"]
  J --> K["归档 run_log.md<br/>功能：运行日志"]
```

## 2.1 Codex 调度与任务状态

```mermaid
flowchart TD
  A["Codex 读取 task_state.md"] --> B["查找第一个 pending 任务"]
  B --> C{"输入文件是否齐备？"}
  C -- "否" --> C1["标记 blocked<br/>写入错误记录"]
  C -- "是" --> D["标记 running"]
  D --> E["触发对应模块"]
  E --> F{"执行是否成功？"}
  F -- "是" --> G["保存输出文件"]
  G --> H["标记 done"]
  H --> A
  F -- "否" --> I["标记 failed"]
  I --> J["写入错误摘要和错误详情"]
  J --> K{"是否需要人工确认？"}
  K -- "是" --> L["标记 blocked"]
  K -- "否" --> A
  A --> M["全部任务结束后归档 run_log.md"]
```

## 3. 第一章流程

第一章回答“各国如何治理该领域”，由“通用治理骨架”和“主题特性治理机制”组成。

```mermaid
flowchart TD
  A["第一章开始<br/>输入：topic + notebook_id<br/>功能：编排"] --> B["1A 顶层设计检索提示词<br/>执行：NotebookLM skill<br/>功能：检索"]
  A --> C["2A 实施机制检索提示词<br/>执行：NotebookLM skill<br/>功能：检索"]

  B --> D["顶层设计检索材料<br/>功能：材料"]
  C --> E["实施机制检索材料<br/>功能：材料"]

  D --> F["1B 顶层设计归类加写作<br/>执行：DeepSeek v4 Pro<br/>功能：构思 + 写作"]
  E --> G["2B 实施机制归类加写作<br/>执行：DeepSeek v4 Pro<br/>功能：构思 + 写作"]

  A --> H["3A 主题痛点推导<br/>执行：DeepSeek v4 Pro<br/>功能：构思"]
  H --> I["生成主题特性治理小节标题<br/>功能：构思产物"]
  I --> J["3B 主题特性材料检索<br/>执行：NotebookLM skill<br/>功能：检索"]
  J --> K["主题特性检索材料<br/>功能：材料"]
  K --> L["3C 分维度成文<br/>执行：DeepSeek v4 Pro<br/>功能：构思 + 写作"]

  F --> M["组装第一章草稿<br/>执行：Codex<br/>功能：编排"]
  G --> M
  L --> M
  M --> N["第一章证据审查<br/>执行：DeepSeek v4 Pro<br/>功能：审查"]
  N --> O{"是否存在无依据事实？"}
  O -- "是" --> P["返回对应小节修订<br/>执行：DeepSeek v4 Pro<br/>功能：写作 + 审查"]
  P --> N
  O -- "否" --> Q["输出 chapter1.md<br/>功能：写作产物"]
```

第一章模块清单：

| 模块 | 功能 | 执行者 | 输入 | 输出 |
| --- | --- | --- | --- | --- |
| 1A 顶层设计检索 | 检索 | NotebookLM skill | `topic`、`notebook_id`、1A 工程化提示词 | 顶层设计材料 |
| 2A 实施机制检索 | 检索 | NotebookLM skill | `topic`、`notebook_id`、2A 工程化提示词 | 实施机制材料 |
| 1B 顶层设计归类加写作 | 构思、写作 | DeepSeek v4 Pro | 1A 材料、1B 工程化提示词 | 顶层设计小节 |
| 2B 实施机制归类加写作 | 构思、写作 | DeepSeek v4 Pro | 2A 材料、2B 工程化提示词 | 实施机制小节 |
| 3A 主题痛点推导 | 构思 | DeepSeek v4 Pro | `topic`、3A 工程化提示词 | 主题特性治理标题 |
| 3B 主题特性检索 | 检索 | NotebookLM skill | 主题特性标题、`notebook_id`、3B 工程化提示词 | 主题特性材料 |
| 3C 分维度加写作 | 构思、写作 | DeepSeek v4 Pro | 3B 材料、3C 工程化提示词 | 主题特性治理小节 |
| 第一章审查 | 审查 | DeepSeek v4 Pro | 第一章草稿、全部检索材料 | 审查报告和修订建议 |

## 4. 第二章流程

第二章回答“该领域最终要达成什么”，先构思目的层主题，再通过 NotebookLM 获取材料，最后由 DeepSeek 完成维度凝练和写作。

```mermaid
flowchart TD
  A["第二章开始<br/>输入：topic + notebook_id<br/>功能：编排"] --> B["第二章目的层定题<br/>执行：DeepSeek v4 Pro<br/>功能：构思"]
  B --> C["输出第二章主题<br/>功能：构思产物"]
  C --> D["第二章资料铺料提示词<br/>执行：NotebookLM skill<br/>功能：检索"]
  D --> E["第二章原始材料<br/>功能：材料"]
  E --> F["第二章维度凝练<br/>执行：DeepSeek v4 Pro<br/>功能：构思"]
  F --> G["第二章正文写作<br/>执行：DeepSeek v4 Pro<br/>功能：写作"]
  G --> H["第二章来源清单生成<br/>执行：DeepSeek v4 Pro<br/>功能：写作"]
  H --> I["第二章证据审查<br/>执行：DeepSeek v4 Pro<br/>功能：审查"]
  I --> J{"是否存在维度套用或无依据事实？"}
  J -- "是" --> K["返回第二章修订<br/>执行：DeepSeek v4 Pro<br/>功能：构思 + 写作 + 审查"]
  K --> I
  J -- "否" --> L["输出 chapter2.md<br/>功能：写作产物"]
```

第二章模块清单：

| 模块 | 功能 | 执行者 | 输入 | 输出 |
| --- | --- | --- | --- | --- |
| 第二章目的层定题 | 构思 | DeepSeek v4 Pro | `topic`、第二章定题工程化提示词 | 第二章主题 |
| 第二章资料铺料 | 检索 | NotebookLM skill | 第二章主题、`notebook_id`、资料铺料工程化提示词 | 逐主体材料 |
| 第二章维度凝练 | 构思 | DeepSeek v4 Pro | 资料铺料结果、凝练维度工程化提示词 | 2-4 个比较维度 |
| 第二章正文写作 | 写作 | DeepSeek v4 Pro | 资料铺料结果、维度清单、写作约束 | 第二章正文 |
| 第二章审查 | 审查 | DeepSeek v4 Pro | 第二章草稿、第二章材料 | 审查报告和修订建议 |

## 5. 前两章统一审查

```mermaid
flowchart TD
  A["第一章草稿"] --> C["统一证据审查<br/>执行：DeepSeek v4 Pro<br/>功能：审查"]
  B["第二章草稿"] --> C
  D["全部 NotebookLM 检索材料"] --> C
  C --> E["检查文件名、机构、年份、举措、引用"]
  E --> F["检查维度是否从材料中归纳"]
  F --> G["检查是否出现知识库外事实"]
  G --> H{"是否通过？"}
  H -- "否" --> I["生成问题清单和修订任务"]
  H -- "是" --> J["输出前两章可组装版本"]
```

## 6. 第三章政策建议写作

第三章读取第一章和第二章成文内容，由 DeepSeek v4 Pro 生成面向中国问题的政策建议。

```mermaid
flowchart TD
  A["读取 chapter1.md<br/>功能：输入"] --> C["第三章政策建议写作模块<br/>功能：写作"]
  B["读取 chapter2.md<br/>功能：输入"] --> C
  C --> D["输出 chapter3.md<br/>功能：写作正文"]
```

当前确定边界：

- 第三章必须读取第一章和第二章成文内容。
- 第三章遵循“从国际经验中来、到中国问题中去”的转化逻辑。
- 第三章不新增无前文依据的国外案例。
