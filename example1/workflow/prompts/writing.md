# 写作功能提示词块

执行者：DeepSeek v4 Pro

目标：只产出可直接入稿的正文内容。

## 1. 通用写作输出约束

所有写作模块统一追加以下输出约束：

```text
【工程化输出要求】
只输出可直接入稿的正文内容。
不要输出写作说明。
不要输出构思过程。
不要输出审查意见。
不要输出思考过程。
不要输出 JSON。
不得引入外部知识。
不得补写材料中不存在的国家、机构、文件、年份或政策举措。
凡涉及的政策举措须与传入材料保持一致、不得脑补。
如果材料缺失，不要编造；可以不写该内容，或在必要处标注“材料不足”。
正文以政策做法与研究判断为主，不在正文标注文件名、机构、年份、脚注等引用信息（忠于材料、不杜撰即可，无须逐一溯源、无须列来源清单）。
正文严禁出现暴露原始材料/检索来源的字样与标签：“【素材来源：…】”、直接写出的 .pdf 文件名、“根据材料/材料显示/据材料/材料[编号]/检索材料表明”，以及 NotebookLM 引用序号 [1][2] 等，一律不得入文；忠于材料即可，不把“材料/来源标签”写进正文。
```

## 2. 1B 顶层设计归类加写作

原始提示词：

```text
多政策的国际比较报告/第一章提示词/模块 1B：顶层设计 · 归类加写作
```

拼装输入：

```text
报告主题：{{topic}}
1A 检索内容：
{{ch1_1a_retrieval_content}}
1A 相关文献：
{{ch1_1a_related_literature}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
1A 检索内容：
{{ch1_1a_retrieval_content}}
1A 相关文献：
{{ch1_1a_related_literature}}

【原始提示词】
{{将 1B 原始提示词中的【主题】替换为 topic}}

【工程化输出要求】
{{通用写作输出约束}}
```

输出内容：

```text
1. 顶层设计的主要类型

……

【分类依据】……
```

## 3. 2B 实施机制归类加写作

原始提示词：

```text
多政策的国际比较报告/第一章提示词/2B：实施机制 · 归类
```

拼装输入：

```text
报告主题：{{topic}}
2A 检索内容：
{{ch1_2a_retrieval_content}}
2A 相关文献：
{{ch1_2a_related_literature}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
2A 检索内容：
{{ch1_2a_retrieval_content}}
2A 相关文献：
{{ch1_2a_related_literature}}

【原始提示词】
{{将 2B 原始提示词中的【主题】替换为 topic}}

【工程化输出要求】
{{通用写作输出约束}}
```

输出内容：

```text
2. 实施机制的主要类型

……

【分类依据】……
```

## 4. 3C 主题特性分维度写作

原始提示词：

```text
多政策的国际比较报告/第一章提示词/3c 分维度加写作
```

拼装输入：

```text
报告主题：{{topic}}
主题特性小节标题：{{chapter1_topic_specific_title}}
3B 检索内容：
{{ch1_3b_retrieval_content}}
3B 相关文献：
{{ch1_3b_related_literature}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
本节子标题：{{chapter1_topic_specific_title}}
3B 检索内容：
{{ch1_3b_retrieval_content}}
3B 相关文献：
{{ch1_3b_related_literature}}

【原始提示词】
{{将 3C 原始提示词中的本节子标题替换为 chapter1_topic_specific_title，并填入 3B 检索内容}}

【工程化输出要求】
{{通用写作输出约束}}
```

输出内容：

```text
{{chapter1_topic_specific_title}}

……
```

## 5. 第二章正文写作

原始提示词：

```text
多政策的国际比较报告/第二章提示词/第二章凝练维度写作模版.md
```

拼装输入：

```text
报告主题：{{topic}}
第二章主题：{{chapter2_topic}}
第二章维度凝练产物：
{{chapter2_dimension_plan}}
第二章检索内容：
{{chapter2_retrieval_content}}
第二章相关文献：
{{chapter2_related_literature}}
```

拼装方式：

```text
【本次输入】
报告主题：{{topic}}
第二章主题：{{chapter2_topic}}
第二章维度凝练产物：
{{chapter2_dimension_plan}}
第二章检索内容：
{{chapter2_retrieval_content}}
第二章相关文献：
{{chapter2_related_literature}}

【原始提示词】
{{复制第二章凝练维度写作模板中“第二步——按以下范式撰写正文”的任务要求}}

【工程化输出要求】
{{通用写作输出约束}}
```

输出内容：

```text
{{chapter2_topic}}

……

来源清单：
……
```
