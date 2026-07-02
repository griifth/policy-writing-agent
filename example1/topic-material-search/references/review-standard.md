# DeepSeek Review Standard & Call

DeepSeek is a stateless lightweight reviewer. Assemble `/tmp/review_in.txt` = the review standard below + `【待审材料】` + the full text of all category files, call DS, read its verdict, patch gaps, loop until 通过 or 4 rounds.

## Review standard (put this verbatim at the top of /tmp/review_in.txt)

```
【审核标准（请严格据此判定）】
A. 信息源标准
1. 权威分级：每个源标 T1（官方政策/法规、国际组织报告如OECD/UNESCO、官方统计）/ T2（同行评议研究）/ 剔除（博客、百科、二手转述、无出处、疑似AI生成）。
2. 覆盖度：每个参照实体（国家/机构）是否都有 T1 或 T2 源；每个检索类别是否都有实质来源。
3. 出处完整：每个源是否有 机构 + 文件/报告名 + 年份 + URL；缺项的降级。
4. 时效：政策类优先近 5–8 年；历史背景类可放宽但需标年份。
B. 检索信息质量标准
1. 可溯源：每条关键事实是否带出处，能否回到具体来源；不可溯源的判为不可用。
2. 证据状态：是否标注 [已实施]/[试点]/[评估数据]/[意图或建议]/[媒体转述]；把意图/转述当成熟经验的，判不达标。
3. 充分性：每个类别是否都有足以支撑写作的实质内容——尤其 key_practices（做法可归出 2–3 种模式且含微观细节）、effectiveness_evidence（至少部分做法有评估数据，而非全是意图）、china_status_and_gaps（有中国侧现状与短板）。
4. 颗粒度（按与用户共同确定的方案判定，非固定标准）：材料是否达到方案中为各类别约定的深度——约定要微观细节（课程/学分/典型院校/聘任流程）的类别是否做到；约定保持概览的类别不因"不够细"而扣分。
5. 无幻觉：是否存在看起来精确但无来源的数字、机构、年份；有则必须剔除或降级。
C. 通过线
- 每个参照实体均有 ≥1 个 T1/T2 源；各类别均"达标"；effectiveness_evidence 至少有 2 条带评估数据的有效性证据；覆盖度与深度达到与用户共同确定的方案要求；无未溯源的精确数字残留。
- 任一不满足 → 总判定"继续补充"，并给出具体缺口。

【输出要求】逐类给【达标/不达标】+缺口；最后给【总判定：通过 / 继续补充】+ 若继续补充给出"下一轮补搜清单"。
```

Then append `\n\n【与用户共同确定的检索方案（用于判定覆盖度与颗粒度）】\n` + the agreed granularity block from `search_plan.md`, so DS judges depth against what was agreed (not a fixed bar). Then append `\n\n【待审材料】\n` followed by each file's content under a `===== 文件: <category>.md =====` header.

## DS call (run from the workflow dir)

```bash
cd "/Users/hujingkai/Documents/New project/example1/strategic_response_workflow/workflow"
python3 -c "
from llm_client import create_llm_client
c = create_llm_client('deepseek')
r = c.ask(open('/tmp/review_in.txt', encoding='utf-8').read())
open('/tmp/review_out.txt','w',encoding='utf-8').write(r or '<EMPTY>')
print('LEN', len(r or ''))
"
```

Read `/tmp/review_out.txt`. Save it as `runs/<run-id>/ds_review_round<N>.md`. If 总判定 = 继续补充, run targeted re-search ONLY for the listed gaps, regenerate the affected files, and re-review. Note: `c.ask` may return a long string; redirect to a file rather than `tail` an inline print (an inline `print` can come back empty under some shells).

## Loop control

- Round 1: collect all entities × all categories per the plan.
- Rounds 2–4: patch only DS-listed gaps.
- Stop at 通过, or after round 4 — if still not passed, land what passed and state residual gaps explicitly in the hand-off.
