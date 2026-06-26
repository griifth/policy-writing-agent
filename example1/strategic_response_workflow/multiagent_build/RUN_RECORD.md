# 多 Agent 构建 · 总运行记录

> 方案：../EXECUTION_PLAN_multiagent_build.md（v2）。日期：2026-06-24。

## 前置（编排者亲自做）
- [x] P0 gold_samples 落盘 + MANIFEST（15 篇，gitignored）
- [x] P1 reasoning_dna/conventions.md（三段式 + 降级红线）
- [x] P2 runner 注入 reasoning_dna（gated）+ 两 module.yaml 注入映射
  - 验证：编译通过；无刀时 dry-run 18 个 generated_prompts 逐字节一致（gated 零变化）；reasoning_dna_snapshot 生成正常
- [x] P3 重生成命令（完整参数）+ 三 judge 盲审判据 就绪（命令见方案 P3）

## 阶段1 · 三路 dev↔review 循环（Workflow w19jg649s，6 agent / 516k tokens / ~30min）
- [x] 路 A strategic reasoning_dna（intent/threat/hedge）—— **PASS 第1轮，分 88**
- [x] 路 B 动向研判模块 trend_review（强制中国对策）—— **PASS 第1轮，分 92**（reviewer 实跑 dry-run 16步过）
- [x] 路 C experience reasoning_dna 两刀（cause/efficacy）—— **PASS 第1轮，分 88**

三路均第1轮过线（全硬门 + ≥85），无返工。各路记录见 `route_{a,b,c}/round_1/{dev,review,decision}.md`。
注入已确认生效：装刀后 strategic dry-run，pressure_judgment/planning/suggestion_pool/policy_priority 四步带上刀内容。

## 路 A 结果门（编排者亲自做）—— **PASS** ✅
- [x] 装刀重生成中美AI人才（run-20260624-122346）→ 三 judge 盲审
  - 新版(乙)中位数 91，3/3 judge 排第1；旧版(甲)89，人类(丙)69
  - 三条判据全过（≥2/3排第1 / 中位数>旧版 / 各维度≥人类-2）。详见 route_a/result_gate/RESULT.md
  - 诚实：对旧版窄胜（中位数差2分），赢在建议体系+证据严谨；显著超人类稿(~+20)

## 阶段2 · 收口 —— 完成
- [x] 最终冒烟：strategic/experience/trend_review 三模块装刀后 dry-run 全 16/16 步过、无 traceback
- [x] 敏感人类素材拷贝 gitignore；提交

## 补做 · trend 体例 reasoning_dna 刀（路 D，Workflow w23cdjusz）
- [x] signal / driver / stage / uncertainty 四刀 —— **PASS 第1轮，分 88**
- 注入：map_pressure_judgment[signal,driver,stage] + plan_article[stage,uncertainty]，dry-run 确认接通
- **至此三体例 reasoning_dna 齐整**：strategic(intent/threat/hedge)、experience(cause/efficacy)、trend(signal/driver/stage/uncertainty)
- 记录见 route_d/round_1/{dev,review,decision}.md；非阻断锐化 3 条留待后续

---

## 补做 · 语域校准（2026-06-25）—— **PASS** ✅

> 背景：旧装刀版（乙）正文充斥"绞杀/压制矩阵/釜底抽薪/钳形攻势/第二战场/反守为攻"等无对方明示文本支撑的军事化定性，远比人类金样本（丙）激进。诊断：刀的降级红线只管"证据等级"、不管"语域"，且盲审判据把"中性=未答"，反向激励激进——丙(69)被打成最低、乙(91)最高，优化目标与人类标准相反。

- **双轴分离原则**：判断纵深（刀逼 intent/threat/hedge，保留）与语域分寸（单独设闸，克制≠浅）分开。
- **全链路语域闸（5 落点）**：
  1. `reasoning_dna/conventions.md`：加"语域红线"+审查判据翻正（中性≠未答；狠而无据=超标；金样本=语域上限锚）。
  2. 三把刀 `intent/threat/hedge.md`：各加"语域降级"——定性词无 A 级（对方原话）支撑→降为陈述句/建设句。
  3. 中间产物 prompt（注入层）`pressure_judgment_mapping / suggestion_pool / policy_priority`：加语域闸，让对抗腔写不进映射/建议池。
  4. 写作端 `writing.md`：禁用词表扩容到真实违例词 + 锚定金样本语域上限。
  5. 审稿/盲审 `review.md`（维度22+否决规则）+ `EXECUTION_PLAN`（评分表加"语域适报15"+语域硬闸）。
- **重生成验证**（run-20260625-093924，复用材料、inline 自审，16 步无 traceback）→ 四篇双轴盲审（新稿/乙/丙/甲）：
  - 总分中位数：**新稿 92（3/3 排第1）** ｜ 乙 77 ｜ 甲 72 ｜ 丙 72。
  - 语域维度中位数：新稿 12 ｜ 丙 14 ｜ 乙 5 ｜ 甲 4 —— 军事化堆叠的乙/甲被语域重罚跌到中段。
  - 纵深（战略判断+建议体系+结构）中位数：新稿 52 ≥ 乙 46 —— 去激进后纵深不降反升。
- **诚实记录**：
  - 上一轮"让丙夺冠"是错误成功标准——丙语域最干净(14)但战略判断/建议体系真实单薄（总分仍 72 垫底），其"激进"只在标题、克制背后藏着弱分析。正确目标是"丙的克制语域 + 乙的系统纵深"，新稿即此。
  - 残留小项（已修，见下）：新稿v1"虹吸"5 次，语域 12 略低于丙 14。

- **补落点 6 · revision 语域闸（2026-06-25）**：定位到残留"虹吸"是 revise 步引入的——初稿(没看原文)本就克制，但 `revision.md` 只装旧款窄闸（仅认"抽血/咽喉式打击/战争机器"3 词），漏掉"虹吸/蓄意加剧/技术压制"，且 reviser 主指令"强化战略判断"反把语域改激进。
  - 修：给 `revision.md:24` 补与 writing.md/conventions 同款的升级语域闸（金样本上限锚 + 扩容禁用词映射 + "强化判断≠升级语气"）。
  - 重生成验证（run-20260625-103054，16 步无 traceback）：本轮初稿因写作步随机波动反更糙（虹吸5+釜底抽薪1），但 revision 闸把终稿净化到**虹吸 1**（上一版终稿是 5）——修改环节从"语域放大器"变成"语域净化器"。
  - 三评委单篇绝对评分：总分中位数 **95**（95/92/96），语域适报中位数 **14**——**追平人类金样本丙(14)，"语域≥丙"达成**；纵深保留（结构14/战略18/建议19）。
  - 发现：写作步非 100% 确定性（DeepSeek 每次略有差异，偶仍吐"虹吸"），故 revision 闸是必需兜底——不论初稿糙否都能收口。至此语域闸 **6 落点**齐整：conventions / 三把刀 / 三中间产物 prompt / writing.md / **revision.md** / review.md+EXECUTION_PLAN。

## 进度日志
- 2026-06-24　P0/P1/P2 完成并验证；阶段1 三路 Workflow 全第1轮过线（A88/B92/C88）；
  路A结果门 PASS（新版3/3排第1，压过旧版+人类）；三模块冒烟全过；落盘提交。
- 2026-06-24　补 trend 体例四刀（路 D，PASS 88）；三体例 reasoning_dna 齐整。
- 2026-06-25　语域校准：6 落点全链路语域闸落盘（含 revision 兜底）+ 两轮重生成验证 PASS。终版总分中位数 95、语域 14（追平人类丙），纵深保留；乙/甲军事化堆叠被语域罚到中段（77/72）。
