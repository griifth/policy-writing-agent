# archive/ 归档说明（2026-07-05 SSOT 收敛）

本目录存放被"单一真源（SSOT）"改造替换下来的历史副本，**运行时一律不读**。保留原因与替代物：

| 归档物 | 由来 | 替代物（canonical） | 备注 |
|---|---|---|---|
| `style_dna_v1/` | policy_style_dna 的前身，蒸自 24 篇学术期刊论文（第一人称"本研究"，与现行第三人称规则相反） | `../policy_style_dna/`（仓根） | 原始语料（`raw/samples_txt*`、`processed/`）**仅本地保留、不入 Git**（.gitignore 已覆盖），可用作对照/foil；入库的只有 `raw/source_manifest.csv` 清单与 `wiki/` 规则。勿再被任何文档引用为语域锚 |
| `policy_style_dna_workflow_copy/` | 根引擎侧的完整拷贝，曾与战略侧漂移（forbidden.md L13、review_scope.md） | `../policy_style_dna/`（仓根，已取两版并集/超集） | 合并记录见 canonical 的 forbidden.md 第 2 节文末注 |
| `institution_profile_workflow_copy.md` | 根引擎侧拷贝（归档时与战略侧 md5 相同） | `../institution_profile.md`（仓根） | |
