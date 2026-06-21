# Style DNA

本目录用于沉淀政策研究报告的文风控制规则。它不是事实知识库；事实材料仍由 NotebookLM 检索和工作流中间产物提供。

## 当前素材

- 原始来源：用户提供的“风格参考”PDF 文件。
- 来源清单：`raw/source_manifest.csv`
- 推荐使用的抽取文本：`raw/samples_txt_raw/`
- 推荐使用的清洗文本：`processed/cleaned_samples_raw/`
- 文风摘录语料包：`processed/style_excerpt_corpus.md`
- 单篇摘录：`processed/style_excerpts/`

说明：`raw/samples_txt/` 与 `processed/cleaned_samples/` 是首次 layout 模式抽取的中间结果，双栏中文论文顺序较差。后续蒸馏和工作流接入应以 raw 模式生成的 `samples_txt_raw/`、`cleaned_samples_raw/` 和 `style_excerpt_corpus.md` 为准。

仓库版本默认不提交 `raw/` 和 `processed/`。这两个目录属于本地素材和中间处理结果；可复用的文风控制成果以 `wiki/` 为准。

## Wiki 文件

- `wiki/voice.md`：政策研究声音与写作姿态。
- `wiki/structure.md`：结构范式与论证递进方式。
- `wiki/sentence.md`：句式、段落组织和可复用表达。
- `wiki/forbidden.md`：禁用表达、AI 腔和失败模式。
- `wiki/recommendation.md`：政策建议写作规则和合理性标准。
- `wiki/self_check.md`：L1-L5 自检体系。

## 接入原则

写作模块读取 `voice.md`、`structure.md`、`sentence.md`、`recommendation.md`；审查和修改模块读取 `forbidden.md`、`recommendation.md`、`self_check.md`。最终正文不得输出文风分析过程、分类依据、比较维度或建议映射表，除非用户明确要求保留。
