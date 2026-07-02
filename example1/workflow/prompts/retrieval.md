# 检索功能提示词块

执行者：NotebookLM skill

目标：把工程化检索提示词传给指定 NotebookLM 知识库，返回材料。

## 1. 通用检索输出约束

所有检索模块统一追加以下输出约束：

```text
【工程化输出要求】
请只输出以下两部分：

一、检索内容
按照原始提示词要求罗列检索材料。
尽量保留来源主体、文件名称、年份、具体做法或关键表述、引用标记。
不同来源主体、不同文件、不同举措尽量拆开写，不要为了简洁而合并。
如果知识库未见相关内容，直接写“未见”。
本部分只做检索和铺料，不做分类、不归纳维度、不写对比结论、不提出对策。

二、相关文献
集中列出本次检索命中的相关文献。
每条尽量包含：来源主体、文件名称、年份、发布机构、引用标记。
相关文献只需集中列出，不需要与“一、检索内容”逐条对应。
```

## 2. 1A 顶层设计检索

原始提示词：

```text
多政策的国际比较报告/第一章提示词/1A：顶层设计 - 检索
```

拼装输入：

```text
报告主题：{{topic}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}

【原始提示词】
{{将 1A 原始提示词中的【主题】替换为 topic}}

【工程化输出要求】
{{通用检索输出约束}}
```

输出内容：

```text
一、检索内容
……

二、相关文献
……
```

## 3. 2A 实施机制检索

原始提示词：

```text
多政策的国际比较报告/第一章提示词/2A：实施机制-检索
```

拼装输入：

```text
报告主题：{{topic}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}

【原始提示词】
{{将 2A 原始提示词中的【主题】替换为 topic}}

【工程化输出要求】
{{通用检索输出约束}}
```

输出内容：

```text
一、检索内容
……

二、相关文献
……
```

## 4. 3B 主题特性材料检索

原始提示词：

```text
多政策的国际比较报告/第一章提示词/3b 检索
```

拼装输入：

```text
报告主题：{{topic}}
主题特性小节标题：{{chapter1_topic_specific_title}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
检索主题：{{chapter1_topic_specific_title}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}

【原始提示词】
{{将 3B 原始提示词中的检索主题替换为 chapter1_topic_specific_title}}

【工程化输出要求】
{{通用检索输出约束}}
```

输出内容：

```text
一、检索内容
……

二、相关文献
……
```

## 5. 第二章资料铺料检索

原始提示词：

```text
多政策的国际比较报告/第二章提示词/第二章所需资料提示词.md
```

拼装输入：

```text
报告主题：{{topic}}
第二章主题：{{chapter2_topic}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
本次主题：{{chapter2_topic}}
知识库名称：{{notebook_name}}
Notebook ID：{{notebook_id}}

【原始提示词】
{{将第二章资料铺料原始提示词中的【本次主题】替换为 chapter2_topic}}

【工程化输出要求】
{{通用检索输出约束}}
```

输出内容：

```text
一、检索内容
……

二、相关文献
……
```
