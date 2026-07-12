# P5 · AI 产物盘点（人稿 vs AI稿盲测 · AI侧候选）

盘点日期：2026-07-08｜盘点员：语料盘点 agent
盘点范围：`runs/`（根引擎 workflow/ 产物）、`strategic_response_workflow/runs/`（主引擎产物）、`strategic_response_workflow/experiments/`（agent 直写实验）。
人稿侧参照：`/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md/` 38 篇真实内参标题（仅核对标题，未读内容）。

字数口径说明：表中"字数"为汉字字符数（候选篇目为精确统计）；非候选篇目按 UTF-8 字节数 ÷3 估算，前缀"约"。早期用 `wc -m` 得到的数值实为字节数，勿直接当字数用。

---

## 一、总表 A：根引擎 `runs/`（26 条）

引擎判定：目录结构含 `chapter_drafts/ + extracted_materials/ + generated_prompts/ + notebook_resolution.md`，均为根引擎（workflow/）产物；`notebook_name: web-collected / 占位` 者为网搜料包变体。日期取自目录名。

| run id | 日期 | 主题 | 引擎 | 可用成稿（链条最终版） | 字数 | 备注 |
|---|---|---|---|---|---|---|
| run-20260604-152349-66e190e0 | 06-04 | 人工智能+教育 | 根 | 无 final_report | — | **剔除**：中断，无成稿 |
| run-20260604-152402-10ca8b23 | 06-04 | 人工智能+教育 | 根 | final_report.md（434B） | — | **剔除**：DRY RUN 占位 |
| run-20260604-152432-36657c10 | 06-04 | 人工智能+教育 | 根 | 无 | — | **剔除**：中断 |
| run-20260604-152457-dd7145df | 06-04 | 人工智能+教育 | 根 | 无 | — | **剔除**：中断 |
| run-20260604-152518-2a39f7d9 | 06-04 | 人工智能+教育 | 根 | final_report.md（434B） | — | **剔除**：DRY RUN 占位 |
| run-20260604-152840-fa201c5b | 06-04 | 人工智能+教育 | 根 | final_report.md | 约1.0万 | 完整但过老（6/4），不入选 |
| run-20260604-163852-c9c40bc7 | 06-04 | 人工智能+教育 | 根 | final_report_reviewed.md | 约1.25万 | 过老，不入选 |
| run-20260607-002722-60484b83 | 06-07 | 人工智能+教育 | 根 | final_report.md（448B） | — | **剔除**：DRY RUN |
| run-20260607-005518-1d35a33f | 06-07 | 人工智能+教育 | 根 | 448B/56B | — | **剔除**：DRY RUN |
| run-20260607-005629-02756c41 | 06-07 | 人工智能+教育 | 根 | 448B/56B | — | **剔除**：DRY RUN |
| subagent-writing-20260608-171008 | 06-08 | 人工智能+教育 | 根·子agent变体 | final_report.md | 约1.2万 | 完整，子agent写作变体；过老不入选 |
| run-20260625-112544-ccb86ce5 | 06-25 | 人工智能+教育 | 根 | final_report_reviewed.md | 10,372 | 完整，三章长报告体；篇幅偏长，备选 |
| run-20260626-143122-a8da71cd | 06-26 | 人工智能+教育 | 根·网搜料包 | final_report_reviewed.md | 约8.4千 | 完整；含 ds_3way 实验残件 |
| run-20260626-152506-2528b552 | 06-26 | 人工智能+教育 | 根·网搜料包 | final_report_reviewed.md | 7,998 | 完整；正文残留素材标签引用（tell 重），备选需清洗 |
| run-20260629-135438-5d05ff8e | 06-29 | 人工智能+教育 | 根 | 449B/56B | — | **剔除**：DRY RUN |
| run-20260629-135517-ad6e8a80 | 06-29 | 人工智能+教育 | 根 | 449B/56B | — | **剔除**：DRY RUN |
| run-20260629-135550-2de13806 | 06-29 | AI+教育 | 根 | 439B/56B | — | **剔除**：DRY RUN |
| run-20260629-135800-4c6cf4b0 | 06-29 | 人工智能+教育 | 根 | final_report_agent_reviewed.md | 约8.0千 | reviewed.md 仅3,149B 系残缺，以 agent_reviewed 为最终版；有伴生 docx |
| run-20260701-104825-f67a0f53 | 07-01 | AI+教育 | 根 | 439B/56B | — | **剔除**：DRY RUN |
| run-20260706-095808-7906d24e | 07-06 | AI+教育三类治理模式 | 根 | final_report_reviewed_教科院修订版.md | 6,244 | ★候选。全链最全：原稿→reviewed→教科院修订版，各带 .score.md；伴生 docx |
| run-20260706-155954-0d7cc7e6 | 07-06 | AI+教育治理模式（顶层×实施） | 根 | final_report.md（547B） | — | **剔除**：DRY RUN |
| run-20260706-162205-fe530c2b | 07-06 | AI+教育四种治理逻辑 | 根·网搜料包 | final_report_教科院修订版.md | 6,344 | ★候选。原稿→reviewed→教科院修订版；伴生内参版式 docx |
| run-20260706-181435-7f38e1f2 | 07-06 | AI+教育治理模式 | 根 | final_report_reviewed.md | 约6.1千 | 完整；与 095808/162205 同题，备选 |
| run-20260706-184334-9f600ec2 | 07-06 | AI+教育治理模式 | 根 | 无 final_report | — | **剔除**：中断（只到检索/提示词步） |
| run-20260706-193854-4dab90d1 | 07-06 | AI+教育治理模式 | 根 | final_report_reviewed.md | 6,129 | 完整；同题备选 |

另：`runs/panel_eval/`（article_A / article_C / article_MINE 及甲乙丙盲评件）非 run 产物，系全文重写步选型实验（commit 8aea824）的盲评材料，其中含AI稿与人类稿混排，**不宜直接作AI侧候选**（溯源需回实验存档确认哪篇是谁）。`runs/live_run.log` 为日志。

要点：根引擎 25 个 run **全部同一主题**（人工智能+教育国际比较），主题分散性只能靠主引擎补。

---

## 二、总表 B：主引擎 `strategic_response_workflow/runs/`（实产出 17 条 + 汇总行）

引擎判定：目录在 `strategic_response_workflow/runs/` 下、成稿名为 `final_article*.md`，均为主引擎（内参短文体例，3-5千字）。约 **93 个 run 为 DRY RUN 占位**（final_article 仅 56-57B"DRY RUN：未调用 deepseek"），一并剔除，不逐条列出。

| run id | 日期 | 主题/标题 | 可用成稿（最终版） | 字数 | 备注 |
|---|---|---|---|---|---|
| run-20260615-002602-1a26a3c4 | 06-15 | 美国AI人才战略布局及我国应对策略 | final_article_reviewed.md | 约3.4千 | 过老 |
| run-20260615-101803-37285a0b | 06-15 | 美国AI人才（带"——基于NSCAI报告…"副题） | final_article_reviewed.md | 约4.1千 | 过老 |
| run-20260615-111333-review-deepseek-0febc3 | 06-15 | 美国AI人才（review-only run） | final_article_reviewed.md | 约3.9千 | 仅审查步产物 |
| run-20260616-005153-8ebbf426 | 06-16 | 美国AI人才竞争：从双重挤压到中国协同破局 | final_article_reviewed.md | 约5.1千 | 过老 |
| run-20260621-153714-85b5e24e | 06-21 | 从被动承压到主动破局：美国对华AI人才体系化竞争 | final_article_reviewed.md | 约4.4千 | |
| run-20260621-161750-f4e75d5d | 06-21 | 美国人工智能人才战略布局及我国应对策略 | final_article_reviewed.md | 约5.8千 | 即 compare-ds-opus 实验中 opus.md 之源（Opus 引擎跑法），非常规双引擎产物 |
| run-20260623-095643-2d8344d5 | 06-23 | 美国AI人才战略布局及我国应对策略 | final_article_claude_revised.md | 约4.7千 | 有 claude_revised 额外修订版 |
| run-20260623-151123-50592bc4 | 06-23 | 专业化优先：美英德澳体育教师培养聘任 | final_article_reviewed.md（另有 clean/plain_rewrite 实验版） | 4,031 | ★候选。与人稿同题直配 |
| run-20260624-122346-401f099b | 06-24 | 体系化遏制下的破局之道：美国AI人才 | final_article_reviewed.md | 约4.2千 | |
| run-20260624-131559-ca96ee20 | 06-24 | 从虹吸到封锁：美国AI人才…我国教育战略应对 | final_article_reviewed.md | 约4.3千 | |
| run-20260625-093924-6cafa873 | 06-25 | 美国AI人才战略布局及我国应对策略 | final_article_reviewed.md | 约4.1千 | |
| run-20260625-103054-fbfa44f2 | 06-25 | 美国人工智能人才战略布局及我国应对策略 | final_article_reviewed.md | 约4.2千 | |
| run-20260625-210305-06e3ea92 | 06-25 | 美国AI人才战略的全政府竞争转向·教育域应对 | final_article_reviewed.md | 3,846 | 候选替补（若不用 100648） |
| run-20260626-111233-dfa77f3b | 06-26 | 从碎片到制度：国际终身教育"框架—认证—资助" | final_article_reviewed.md（另有 clarified 版） | 4,102 | ★候选。终身教育，同题直配 |
| run-20260626-131122-452a7eaa | 06-26 | 从风险共识到审慎行动：人工智能教育的国际做法 | final_article_reviewed.md | 4,689 | ★候选 |
| run-20260629-100648-58f306dd | 06-29 | 从被动承压到主动破局：美国AI人才…教育领域应对 | final_article_reviewed.md | 3,968 | ★候选。AI人才系里最新 |
| run-20260629-115549-ed10468f | 06-29 | 主要国家人工智能教育政策的模式、成因与成效 | final_article_reviewed.md | 4,929 | ★候选。注意：reviewed 版首行标题被审掉了（正文直接开篇），标题在 final_article.md 里 |

其他非 run 目录：`policy-n-20260616-104415-6d8e7461`（政策N提示词集实验，final_article_policy_n_prompt_set.md 约4.7千字，可用但属提示词实验线）；`policy-n-…-077c0498`（DRY RUN）；`compare-ds-opus-reference-20260621/`（deepseek.md / opus.md / **reference_human.md 是人类稿**，勿混入AI侧）；`dna-eval-*`×3（无成稿）；`materials-tiyu-jiaoshi/`、`web-materials-*`×4（料包，非成稿）。

---

## 三、experiments 检查（任务第5点）

- `strategic_response_workflow/experiments/agent_run_subtypeA/agent_draft.md`：**可用**。《美国AI人才战略布局及我国应对策略》，3,885 字，完整成文（文件日期 2026-06-26）。
- `strategic_response_workflow/experiments/agent_run_subtypeA_v2/agent_draft.md`：**可用**。《美国AI人才战略布局及我国教育域应对策略》，2,763 字，完整成文（2026-06-26）。
- 性质：agent 直写路线实验稿，**无 review 链**，各带 conception_trace.md 与 ds_3way 三方盲评件。可作"agent直写"代表入盲测，但与主引擎产物不是同一生成路线，若盲测想控制变量则降为备选。

---

## 四、AI成稿 ↔ 人稿 近题配对（全部发现）

| 人稿（38篇内） | AI成稿 | 配对强度 |
|---|---|---|
| 人工智能+教育国际比较报告.md | 根引擎全系（尤其 run-20260706-095808 / 162205 / 193854 / 181435）；主引擎 run-20260626-131122、run-20260629-115549 | **同题** |
| 中美AI人才竞争及应对策略.md | 主引擎"美国AI人才"全系（最新：run-20260629-100648）；experiments agent_draft ×2 | **同题** |
| 警惕美竞争法案对我教育战略带来的重大风险.md | 同上AI人才系（均以 USICA/NSCAI 为分析对象） | 近题（同一法案素材） |
| 美英澳等国新一轮国际人才争夺的长短线招数及其破解.md | 同上AI人才系 | 近题 |
| 美英德澳培养与聘任体育教师的做法和特点.md | 主引擎 run-20260623-151123（专业化优先：美英德澳体育教师） | **同题直配**（连国别组合都一致） |
| 国外终身教育改革动向和趋势.md；2016-2020年国际终身教育改革发展趋势.md；主要国际组织和国家推动终身学习主要路径.md | 主引擎 run-20260626-111233（国际终身教育三位一体） | **同题**（一对三） |
| 国外生成式人工智能教育应用态度、策略和举措.md | 主引擎 run-20260626-131122、run-20260629-115549 | 近题 |
| 全球经验-人工智能拔尖人才培养的六大前沿趋势.md | AI人才系（涉拔尖人才培养段落） | 弱近题 |

覆盖不到的人稿主题（课后服务、校服治理、中考改革、校园餐、学制、微认证等）在 AI 侧无对应成稿——盲测人稿抽样宜偏向上表左列。

---

## 五、推荐盲测 AI 侧候选（8 篇 + 替补）

按"6月下旬后 + 链条最终版 + 主题尽量分散"选出。主题簇实际只有 4 个（AI+教育治理、AI教育政策、美国AI人才、体育教师、终身教育——后两簇各 1 篇），受语料限制无法更散。

| # | 路径（相对仓库根） | 主题 | 日期/引擎 | 字数 | 近题人稿 |
|---|---|---|---|---|---|
| 1 | `runs/run-20260706-095808-7906d24e/final_report_reviewed_教科院修订版.md` | AI+教育三类治理模式 | 07-06 根引擎 | 6,244 | 人工智能+教育国际比较报告 |
| 2 | `runs/run-20260706-162205-fe530c2b/final_report_教科院修订版.md` | AI+教育四种治理逻辑（网搜料包） | 07-06 根引擎 | 6,344 | 同上（与#1同题不同料源/分类轴，嫌密可二选一） |
| 3 | `strategic_response_workflow/runs/run-20260629-115549-ed10468f/final_article_reviewed.md` | 各国AI教育政策模式·成因·成效 | 06-29 主引擎 | 4,929 | 人工智能+教育国际比较报告；国外生成式AI教育应用 |
| 4 | `strategic_response_workflow/runs/run-20260626-131122-452a7eaa/final_article_reviewed.md` | AI教育国际做法与成效检视 | 06-26 主引擎 | 4,689 | 同上 |
| 5 | `strategic_response_workflow/runs/run-20260629-100648-58f306dd/final_article_reviewed.md` | 美国AI人才竞争布局·教育领域应对 | 06-29 主引擎 | 3,968 | 中美AI人才竞争及应对策略；警惕美竞争法案 |
| 6 | `strategic_response_workflow/runs/run-20260623-151123-50592bc4/final_article_reviewed.md` | 美英德澳体育教师培养聘任 | 06-23 主引擎 | 4,031 | 美英德澳培养与聘任体育教师的做法和特点（直配） |
| 7 | `strategic_response_workflow/runs/run-20260626-111233-dfa77f3b/final_article_reviewed.md` | 国际终身教育"框架—认证—资助" | 06-26 主引擎 | 4,102 | 国外终身教育改革动向和趋势 等3篇 |
| 8 | `strategic_response_workflow/experiments/agent_run_subtypeA_v2/agent_draft.md` | 美国AI人才·教育域（agent直写） | 06-26 实验线 | 2,763 | 中美AI人才竞争及应对策略（备选性质：无审查链） |

替补：`strategic_response_workflow/runs/run-20260625-210305-06e3ea92/final_article_reviewed.md`（AI人才·教育域，3,846字，替#5或#8）；`runs/run-20260706-193854-4dab90d1/final_report_reviewed.md`（6,129字，替#1/#2）；`runs/run-20260626-152506-2528b552/final_report_reviewed.md`（7,998字，含素材标签引用，须先清洗）。

注意事项：
- #5 尾段疑似轻微截断（正文止于"初期可选取基础数学、理论物理等中方具优势且美方限制较少的领域"，句子完整性待人工复核；若不放心换 20260625-210305）。
- #3 的 reviewed 版无标题行（正文直接开篇），匿名化时可从 final_article.md 取标题《主要国家人工智能教育政策的模式、成因与成效》补上或统一去标题。
- 根引擎稿（#1/#2）6千余字，主引擎稿4-5千字，人稿内参多为3-6千字——篇幅上主引擎更贴人稿，根引擎稿如需对齐可注意篇幅这一潜在 tell。

---

## 六、表面 tell 清单（匿名化处理参考）

成稿正文内**没有**生成时间戳或元信息头（时间只在目录名/伴生文件里），主要 tell 是格式与套话层面：

1. **Markdown 结构记号**：`#`/`##`/`###` 标题、段首 `**加粗领起句**`、`（一）（二）`+`**粗体**` 混排。人稿是 OCR 转 md，格式形态不同，需统一为素纹本。
2. **章节体例差**：根引擎用"第一章/第二章"（人稿内参惯用"一、二、"）；主引擎已是"一、二、"但小节领起句高度模板化（"第一，…第二，…""**在……方面，**"）。
3. **素材标签引用**：`[U.S. Department of Education. 3_AI_Future_Teaching_Learning_2023.pdf]` 式方括号文件名引用——6/26 网搜料包 runs（尤其 run-20260626-152506）正文大量残留；7/6 后的稿已由后处理清除，但候选仍需通读复查。
4. **编者注/方法说明括注**：#1 尾部"（编者注：若报送稿需给出资金规模、启动年度等量化目标，宜由主管部门据财政口径核定后填入，本报告不作无据估算。）"；#2 尾部"（说明：本报告依托公开政策文本与国际组织资料的系统检索归纳……）"——一眼AI，必删。
5. **虚构课题组署名/落款**："人工智能+教育国际比较研究课题组""人工智能与教育政策国际比较研究课题组"，#2 文首文尾双落款。人稿有真实署名习惯，需统一匿名。
6. **方法论自陈套话**："本报告依次比较……并落脚到……""是本文要回答的核心问题。总体判断是：""据现有检索材料""从现有材料看"——暴露料包工作方式。
7. **对策条自我标注**：主引擎对策段惯用"此条是对……的审慎回应""该对策回应……趋势研判""此项属需创造条件、分步试点的长期布局"等元话语，密度远高于人稿。
8. **内部引证格式**：`〔上海市教委·2021〕`方头括号标注（run-20260626-111233）。
9. **标题破折号副题**："——基于NSCAI报告的分析"式副题在AI人才系高频出现。
10. **英文原词括注偏密**："Brain Drain""两难境地（dilemma）"等直译痕迹。
11. **文件层面**（不入正文但交付时注意）：`.score.md`、伴生 docx、`final_article` 以 `**加粗行**` 而非标题行开题——重命名/重排版即可抹平。

---

## 七、剔除汇总

- 根引擎 `runs/`：13 个 run 剔除（DRY RUN 占位 10 个、无成稿中断 3 个）；panel_eval 非 run。
- 主引擎：约 93 个 DRY RUN run 剔除；policy-n 一个 DRY RUN；dna-eval×3 无成稿；compare-ds-opus-reference 内含人类参照稿，禁入AI侧。
- 残缺件：`runs/run-20260629-135800-4c6cf4b0/final_report_reviewed.md`（3,149B，审查中断残稿）——该 run 以 `final_report_agent_reviewed.md` 为准。
