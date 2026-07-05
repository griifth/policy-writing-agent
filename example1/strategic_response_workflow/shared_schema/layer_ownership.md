# 层归属表（layer_ownership · 规则的属主登记）

> 治理文档：**不注入 prompt**（runner 只注入 evidence_maturity / register_blacklist / strength_gate 三件）。
> 用途：判定"某类规则该写在哪个文件"；也是 `tools/check_dna.py`（阶段 5）"越界即报错"的规则来源。

## 归属表

| 规则类 | 属层 | canonical 文件（唯一真源） |
|---|---|---|
| 语气 / 语域 / 句式 / 渲染禁词 | **文风层**（policy_style_dna） | `policy_style_dna/wiki/voice.md`（语域总纲）、`sentence.md`（句式）、`forbidden.md`（禁区，§4 渲染/文学化词）、`subtype_a.md` / `subtype_b.md`（子型语域上限） |
| 判断纪律 / 证据分级 / 军事化定性词 / 降级扫描 | **推理层**（reasoning_dna + shared_schema） | `strategic_response_workflow/reasoning_dna/conventions.md`（刀的元格式与红线）、`report_modules/<体例>/reasoning_dna/*.md`（各刀）、`strategic_response_workflow/shared_schema/evidence_maturity.md`（证据分级）、`register_blacklist.md`（军事化/对攻定性词）、`strength_gate.md`（强度双钥门） |
| 建议落点 / 桥接链 / 国情容器 | **机构层** | `example1/institution_profile.md` |
| 终审判分 | **终审层** | `strategic_response_workflow/quality_rubric.md` ＋ `strategic_response_workflow/reviewers/jiaokeyuan_review_scope.md` |

## 跨层件说明

- `strength_gate.md` 连接文风钥（子型语域上限）与推理钥（证据准入）：文件归推理层持有，文风层文件只准"摘要＋指针"式引用。
- `register_blacklist.md`（军事化/对攻词，推理层）与 `forbidden.md` §4（渲染/文学化词，文风层）分属两层、互为交叉引用，词目不重复。

## 越界规则

> **越界新增规则视为缺陷**（如在刀文件里内联重定义证据分级、在文风文件里新设证据门槛）。修复方式 = **移回属主文件 + 原地留一行指针**，不得两处并存。

> 纠错记录：`2026-07-05 建表：三层规则此前互相越界重抄（词表四处、证据分级三套、强度判据三处）→ 登记属主与 canonical，越界即缺陷 → 已建立`
