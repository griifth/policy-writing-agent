# cao-thinking / yongjun-thinking 改名方案（上线准备）

> 编写：2026-07-20。背景：项目上线，两个以真人（曹培杰、张永军）命名的人物 skill 需要改名。
> 本方案给出：候选新名、全部改动触点清单（已 grep 逐一定位）、执行顺序、不改区与三个待拍板决策点。

---

## 一、候选新名（推荐第一组）

两个 skill 的实际分工（宪法第 6 条）：yongjun-thinking→定题与立论，cao-thinking→结构与预读。按功能去人名化：

| 现名 | 推荐新名 | 中文显示名（openai.yaml） | 备选 |
|---|---|---|---|
| yongjun-thinking | **topic-ideation** | 定题立论顾问 | method-advisor / research-framing |
| cao-thinking | **strategy-preread** | 结构预读顾问 | structure-advisor / report-preread |

命名原则：①不含真人姓名与谐音；②名字自述分工，装配工提示词里「谁干什么」不再需要背景知识；③两名对仗（动名结构），与 policy-report-assembler 风格一致。

若倾向保留「-thinking」后缀的既有风格，备选整组：`method-thinking` ＋ `strategy-thinking`。

## 二、改动触点清单（已逐处定位）

### 批次 1 · 目录与 skill 本体（direction_workflow/skills/ 内）

| 文件 | 改动 |
|---|---|
| `skills/yongjun-thinking/` → `skills/<新名>/`；`skills/cao-thinking/` 同理 | 目录改名 |
| 两个 `SKILL.md` frontmatter | `name:` 改新名；`description:` 中的真人姓名表述改为「基于某教育科学研究院所长论文与会议证据蒸馏」类去名化措辞（见决策点 2） |
| 两个 `agents/openai.yaml` | `display_name` 改中文显示名；`default_prompt` 中的 `$cao-thinking` / `$yongjun-thinking` 改 `$<新名>` |
| SKILL.md 正文标题与自述（「曹 · 报送场景…」「永军 · 研究方法论…」「不模拟张永军本人」等句） | 随决策点 2 一并处理 |

### 批次 2 · 包内引用（运行件，必改）

| 文件 | 位置 | 内容 |
|---|---|---|
| `skills/policy-report-assembler/SKILL.md` | 第 34、35、37、80、94、104 行 | skill 路径清单、调用方式声明、第 5/8/10 步的注入说明（「yongjun＋cao 各 3–5 个考题」等） |
| `templates/预读提词单模板.md` | 第 4、9、19、29 行 | 「曹 / 永军口吻」「曹的三翻模拟」→ 改为新显示名口吻（如「结构预读顾问口吻」） |
| `README.md`、`USAGE.md`、`移植说明.md` | 多处 | 部件表、流程图、安装命令 `cp -R …/{yongjun-thinking,cao-thinking}` 等全部替换 |

### 批次 3 · 三张图纸（先改真源、再刷快照——维护纪律第 1 条）

| 真源（records/） | 快照（blueprints/） | 位置 |
|---|---|---|
| `records/装配式图纸_2026-07-12/调度宪法_SKILL草案.md` | `blueprints/调度宪法_SKILL草案.md` | **第 6 条**「yongjun-thinking→定题与立论；cao-thinking→结构与预读」 |
| `records/装配式图纸_2026-07-12/元模块契约.md` | `blueprints/元模块契约.md` | 第 41 行（契约②注入点）、第 100 行（契约③注入点）、第 139 行（预读提词单「以曹/永军口吻」） |

**治理要点**：宪法一直保持「零改动」纪录。本次属**名称映射，不是规则变更**——建议不静默改字，而是在宪法文末加一条日期化《改名备注》（旧名→新名对照＋理由「上线去人名化」），正文第 6 条同步替换为新名。契约同理在文末修订记录里记一笔。改完真源后按惯例刷新 blueprints/ 快照（保留〔快照〕头注、更新日期）。

### 批次 4 · 本机安装件（~/.claude/skills/）

按新名重装两个 skill（从包内复制），并同步重装 policy-report-assembler（其安装件里也引用旧名）；旧名目录删除或留档见决策点 3。注意本机安装件的图纸路径是绝对路径指向 records/ 真源（问题反馈录 #02 裁决），重装时保持该策略。

### 批次 5 · 不改区（历史留痕原则，明确不动）

- `runs/`：晨报、预读提词单、yongjun逼问记录 等 50+ 处旧名——当时实况，勿改。
- `_skill_snapshots/`：三份 2026-07-13 快照——历史留痕，勿改。可另存两份新名 SKILL.md 快照（如 `<新名>_SKILL_20260720.md`）作为改名后的版本记录。
- `finishing/`、`gates/`、`engine/`、`tools/`：已核实零处引用旧名，无需动。

## 三、执行顺序与验证

1. 用户拍板三个决策点（见下）→ 2. 批次 3 真源（宪法/契约）→ 3. 刷新 blueprints/ 快照 → 4. 批次 1 目录与本体 → 5. 批次 2 包内引用 → 6. 批次 4 本机重装 → 7. 新名快照入 `_skill_snapshots/` → 8. 验证 → 9. git 提交。

**验证三条**：
- `grep -rn "cao-thinking\|yongjun-thinking" direction_workflow/ --include='*.md' --include='*.yaml' | grep -v runs/ | grep -v _skill_snapshots/` → 应零命中；
- 新会话按名触发两个新名 skill，各出一次预读提词，行为与旧名一致；
- 装配工按包内路径读新名 SKILL.md 走一遍第 10 步（预读提词），提词单口吻标签为新显示名。

## 四、待拍板决策点

1. **新名选哪组**：推荐 `topic-ideation` ＋ `strategy-preread`；若要保留 -thinking 风格则 `method-thinking` ＋ `strategy-thinking`。
2. **内文真名是否同步脱敏**：改名只动「外壳」的话，SKILL.md description/正文、`references/蒸馏报告.md`（张永军 ×10、曹培杰 ×2）、`references/会议证据.md`、yongjun 的 CNKI 检索 csv 文件名等仍含真人姓名。**上线若对外可见，建议至少脱敏 frontmatter description 与 SKILL.md 正文**；references/ 属内部溯源件，可选择保留（内部可见）或整体不随上线包分发。这直接决定批次 1 的改动深度。
3. **旧名处置**：本机 `~/.claude/skills/` 旧名目录直接删除（推荐，避免双源），还是保留一段兼容期（旧名可触发但内容指向新名）。

（改名不影响自包含性检查方案的任何结论；两方案可并行执行，建议改名先行，避免检查方案的 L3 演练跑在旧名上。）
