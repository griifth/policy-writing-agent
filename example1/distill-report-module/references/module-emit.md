# 体例落盘法（第 3 步）

策略：**克隆现有最近体例为脚手架，再按蓝图改写**——这样文件清单、占位符、runner 约定天然对齐，不会漏文件。

## 1. 选脚手架并克隆

挑 `report_modules/` 里推理链/结构最接近蓝图的体例：
- 借鉴/经验类 → `experience_response`
- 对方威胁/竞争应对类 → `strategic_response`
- 趋势/动向研判类 → `trend_review`

```bash
cd ".../strategic_response_workflow/report_modules"
cp -R <最近体例> <新slug>
rm -f <新slug>/.DS_Store <新slug>/*/.DS_Store 2>/dev/null
```

## 2. 文件清单与改写强度

runner 按固定路径加载，**一个都不能少**：

| 文件 | 改写强度 | 依据 |
|---|---|---|
| `module.yaml` | **必改** | name=slug；label=中文；retrieval_types=蓝图检索类型；reasoning_dna_injection **留空/注释掉（gated）** |
| `prompts/retrieval.md` | **必改** | 蓝图的检索类型，逐类写"问什么、关注点"，带证据状态线索 |
| `prompts/task_redefinition.md` | **必改** | 按蓝图文体定位写"应是/不应是/防滑点 + 重定义句 + 合格判断" |
| `prompts/pressure_judgment_mapping.md` | **必改** | 按蓝图推理链的"判断锻造"步：从材料抽判断的固定输出格式 |
| `prompts/planning.md` | **必改** | 核心问题→核心判断→二级判断→归类→章节功能→推导路径（套蓝图推理链） |
| `prompts/writing.md` | **必改** | 写作总原则 + 蓝图分段结构 + 建议写法 + 段落功能要求 |
| `templates/article_template.md` | **必改** | 蓝图分段的填空式模板 + 写作校验清单 |
| `source/sample.md` | **必改** | 放入输入范文（多篇取主范文；可做反例标注） |
| `prompts/material_roles.md` | 轻改 | 只改首行标题为新体例名；角色标签基本通用 |
| `prompts/suggestion_pool.md` | 轻改 | 改标题 + 把"借鉴建议"等措辞对齐蓝图（如"对策"） |
| `prompts/policy_priority.md` | 轻改 | 改标题 + 措辞对齐 |
| `prompts/review.md` | 轻改 | 改标题 + 审查重点改为蓝图的体例红线（如"是否按类型归类、是否落对策收尾"） |
| `prompts/revision.md` | 轻改 | 改标题 |

> 注意：克隆来的 `reasoning_dna/` 里可能带着旧体例的刀（如 cause/efficacy）。默认 module.yaml **不映射**它们（gated 零注入）。要保留某把通用刀也行，但 v1 默认不开。

## 3. 占位符约定（所有 prompt 通用）

runner 的 `_fill_common` 会把这些占位符替换为 CLI 参数，写 prompt 时照用：
- `【主题】` ← --topic
- `【目标国家】` ← --target-country
- `【战略领域】` ← --strategy-domain
- `【中国应对主题】` ← --china-response-focus

## 4. module.yaml 模板

```yaml
# 体例模块：<中文 label>
# 适用：……
# 推理链：<蓝图推理链>
name: <ascii-slug>
label: <中文 label>
retrieval_types:
  - <key1>   # 职责
  - <key2>
  - …        # 5–6 类
# reasoning_dna_injection:   # v1 gated 零注入；后续用 distill-reasoning-dna 补刀后再开
#   plan_article: [<cut>]
```

## 5. 改写纪律

- 体裁相关文件里旧体例措辞（"国际经验借鉴/战略竞争/趋势研判"等）必须改干净，别留痕。
- 文件名、目录结构严格对齐脚手架，不增不减必需文件。
- 写作/模板里强调蓝图的体例红线（强制收尾、归类而非罗列、证据状态等）。
