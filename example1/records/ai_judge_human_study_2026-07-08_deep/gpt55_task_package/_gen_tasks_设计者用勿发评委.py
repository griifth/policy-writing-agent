# -*- coding: utf-8 -*-
"""生成 GPT-5.5 盲测任务文件 J01-J19。"""
import os

BASE = "/Users/hujingkai/Documents/New project/example1/records/ai_judge_human_study_2026-07-08_deep"
PKG = os.path.join(BASE, "gpt55_task_package")
BV2 = os.path.join(BASE, "blind_v2")
TASKS = os.path.join(PKG, "tasks")
os.makedirs(TASKS, exist_ok=True)

ORDER1 = ["T07","T02","T11","T05","T09","T12","T01","T08","T03","T10","T06","T04"]
ORDER2 = list(reversed(ORDER1))
ORDER3 = ["T03","T12","T05","T10","T02","T08","T06","T01","T11","T04","T07","T09"]

RULES = """## 评审铁律（违反任何一条＝本次评审作废）

1. 本任务必须在**全新会话**中执行；除本文件内容外，你不应带有任何关于本研究的先验信息。
2. 你**只准读取**本文件"评审标尺"与"评审材料"两节列出的文件路径，一个都不能多。禁止浏览这些文件所在的目录、禁止读取仓库其他任何文件、禁止读取路径中含 `_label_map`、`_normalize`、`agent_notes`、`工作日志`、`实验设计`、`最终结论`、`评审割裂`、`人类稿优势` 字样的文件、禁止运行任何脚本、禁止联网检索稿件内容、禁止查看 git 历史。
3. 稿件集中人写稿与 AI 稿的构成比例未知。**对来源的任何猜测不得以任何方式影响评分。**
4. 一切评价按稿件成稿时点进行：不因材料非 2026 年最新而扣价值分。个别错字、格式碎裂视为扫描噪声，不计入评分。
5. 每条评语/理由必须引用稿件原文（≤30 字）作为证据；引不出原文的理由不要写。
6. 先完成并**锁定**全部评分与排名，最后一步才填 JSON 中的 `source_guess` 字段（来源猜测附加题）；填完后不得回改 JSON 的任何其他字段。
"""

GUESS = """## 附加题：来源猜测（评分锁定后、最后一步才填）

对每篇稿件猜测来源：`人写` / `AI` / `不确定`，并给信心 1–3。此题仅用于研究，与评分无关。答案填入同一 JSON 块的 `source_guess` 字段（该字段留到最后填写，填写后不得回改其他字段）。
"""

def header(tid, cond, judge, extra=""):
    return f"# 任务 {tid} · 条件 {cond} · 评委 {judge}\n\n你是一名独立盲审评委，评审对象为政策研究/内参类稿件。{extra}\n\n{RULES}\n"

def materials_section(docs, kind):
    lines = ["## 评审材料（严格按以下顺序逐篇评审）\n"]
    for i, d in enumerate(docs, 1):
        if kind == "full":
            lines.append(f"{i}. `{BV2}/full/{d}.md`")
        elif kind == "excerpt":
            lines.append(f"{i}. `{BV2}/excerpt/{d}.md`（摘片）")
        elif kind == "full+pre":
            lines.append(f"{i}. `{BV2}/full/{d}.md` ＋ 预检单 `{BV2}/precheck/{d}.md`")
    return "\n".join(lines) + "\n"

def rubric_section(rfile):
    return f"## 评审标尺\n\n读取并严格执行：`{PKG}/rubrics/{rfile}`\n"

def output_section(tid, body_spec, json_tmpl, notes):
    notes_md = "\n".join(f"- {n}" for n in notes)
    return f"""## 输出

把完整评审报告写入文件：`{PKG}/results/{tid}.md`

报告结构：

{body_spec}

报告末尾必须附**合法 JSON 块**（```json 围栏），模式如下（分数为示意占位）：

```json
{json_tmpl}
```

### 输出补充规则

- JSON 中 `docs`（或 `pairs`）与 `source_guess` 必须覆盖本任务的**全部**稿件/对；模板只展示了一条示例。
- 分数键名以模板为准（系标尺维度名的缩写，一一对应）。
{notes_md}

{GUESS}"""

def write(tid, content):
    with open(os.path.join(TASKS, f"{tid}.md"), "w", encoding="utf-8") as f:
        f.write(content)

# ---------- 条件 N ----------
N_BODY = """1. 逐篇：六维分数表 + 总分 + 两句话总评（各引原文一处，≤30字）。
2. 全部 12 篇按总分从高到低的排名（同分强制排序并说明理由）。"""
N_JSON = '''{"task":"%s","condition":"N","judge":%d,
 "docs":{"T01":{"结构":8,"论证":7,"材料":8,"语言":9,"建议":7,"可提交":8,"total":47}},
 "ranking":["T05","T01"],
 "source_guess":{"T01":{"guess":"不确定","confidence":1}}}'''
for j, (tid, order) in enumerate([("J01",ORDER1),("J02",ORDER2),("J03",ORDER3)], 1):
    c = header(tid, "N（基线评分）", j)
    c += rubric_section("R_N.md") + "\n"
    c += materials_section(order, "full") + "\n"
    c += output_section(tid, N_BODY, N_JSON % (tid, j), ["排名不允许并列；总分同分时以\"整体可提交\"维度高者在前，并在正文说明。"])
    write(tid, c)

# ---------- 条件 V31 ----------
V31_BODY = """1. 逐篇：用途类型 → A 档（附各维分数与三条理由，引原文）→ B 档（附各维分数与理由，引原文）→ 组合含义一句话 → 若 A/B 冲突，解释冲突来源。
2. 全部 12 篇按"重点参考价值"（以 A 档为主、A 分为辅）从高到低排名。"""
V31_JSON = '''{"task":"%s","condition":"V31","judge":%d,
 "docs":{"T01":{"type":"趋势研判","A":"A1","A_scores":{"首屏":16,"抓手":20,"记忆":12,"压缩":11,"读者":8,"接手":12},"B":"B2","B_scores":{"事实":15,"语域":12,"权限":15,"耦合":11,"闭合":12,"边界":10}}},
 "ranking_by_reference_value":["T05","T01"],
 "source_guess":{"T01":{"guess":"不确定","confidence":1}}}'''
for j, (tid, order) in enumerate([("J04",ORDER1),("J05",ORDER2),("J06",ORDER3)], 1):
    c = header(tid, "V31（双通道评分）", j)
    c += rubric_section("R_V31.md") + "\n"
    c += materials_section(order, "full") + "\n"
    c += output_section(tid, V31_BODY, V31_JSON % (tid, j), ["排名不允许并列；先按 A 档、同档按 A 总分、再同按\"决策抓手\"分排序。","用途类型如跨类，取主导类型的单一标签。"])
    write(tid, c)

# ---------- 条件 V4A（测试集，摘片） ----------
V4A_BODY = """1. 逐篇：用途类型（政策设计地图/风险预警/趋势研判/经验借鉴/资料底稿）→ A 档 → 各维分数 → 三条快读理由（各自引**摘片**原文，≤30字）→ 一句话核心判断复述（复述不出来＝无记忆点，如实写"无"）→ 最小返修清单（针对快读价值）。
2. 全部 12 篇按 A 通道价值从高到低排名。"""
V4A_JSON = '''{"task":"%s","condition":"V4A","judge":%d,
 "docs":{"T01":{"type":"趋势研判","A":"A2","scores":{"三件套":14,"轴即拍板":18,"记忆点":12,"接手":10,"压缩":9},"memory_point":"一句话复述或：无"}},
 "ranking_by_A":["T05","T01"],
 "source_guess":{"T01":{"guess":"不确定","confidence":1}}}'''
for j, (tid, order) in enumerate([("J07",ORDER2),("J08",ORDER3),("J09",ORDER1)], 1):
    c = header(tid, "V4-A（快读价值·截断输入）", j,
               extra="**你只拿到每篇的摘片，拿不到全文——这是实验设计，不是资料缺失；不得索要全文，摘片里看不到的内容视为不存在。**")
    c += rubric_section("R_V4A.md") + "\n"
    c += materials_section(order, "excerpt") + "\n"
    c += output_section(tid, V4A_BODY, V4A_JSON % (tid, j), ["排名不允许并列；先按 A 档、同档按总分、再同按\"轴即拍板\"分排序。","用途类型如跨类，取主导类型的单一标签。","摘片中\"（无建议/对策类条目）\"等提取占位说明可直接引作证据。"])
    write(tid, c)

# ---------- 条件 V4B（测试集，全文+预检单） ----------
V4B_BODY = """1. 逐篇：用途类型 → B 档 → 各维分数与逐维理由（引全文原文，≤30字；对每处显性声明注明"有证据支撑/表演"判定）→ 目标读者与其拍板事项 → 担责总纲一问的回答 → 最小返修清单（针对报送安全）。
2. 全部 12 篇按 B 通道报送安全性从高到低排名。"""
V4B_JSON = '''{"task":"%s","condition":"V4B","judge":%d,
 "docs":{"T01":{"type":"趋势研判","B":"B2","scores":{"证据颗粒":18,"可拍板":16,"咬合":10,"担责":10,"语域":9,"权限耦合":7},"performance_flags":2}},
 "ranking_by_B":["T05","T01"],
 "source_guess":{"T01":{"guess":"不确定","confidence":1}}}'''
for j, (tid, order) in enumerate([("J10",ORDER3),("J11",ORDER1),("J12",ORDER2)], 1):
    c = header(tid, "V4-B（细读裁决·全文＋预检单）", j,
               extra="每篇稿件附带一份程序生成的《机械预检单》，用法见标尺。")
    c += rubric_section("R_V4B.md") + "\n"
    c += materials_section(order, "full+pre") + "\n"
    c += output_section(tid, V4B_BODY, V4B_JSON % (tid, j), ["排名不允许并列；先按 B 档、同档按总分、再同按\"证据颗粒与归属\"分排序。","用途类型如跨类，取主导类型的单一标签。","performance_flags 填你判定为\"表演\"（显性声明无证据支撑）的处数。"])
    write(tid, c)

# ---------- 条件 PW ----------
PAIRS = {"P1":("T03","T09"),"P2":("T04","T07"),"P3":("T01","T02"),"P4":("T05","T12"),"P5":("T08","T10")}
PW_ORDERS = {
    "J13": (["P2","P5","P1","P4","P3"], "listed"),
    "J14": (["P4","P1","P3","P5","P2"], "reversed"),
    "J15": (["P5","P3","P2","P1","P4"], "alternate"),
}
PW_BODY = """1. 逐对：Q1 胜者＋信心＋三条理由（引原文≤30字并注明出自哪篇）；Q2 同格式。Q1 与 Q2 允许不同答案。
2. 不允许平局；信心 1=勉强 2=明显 3=悬殊。"""
PW_JSON = '''{"task":"%s","condition":"PW","judge":%d,
 "pairs":{"P1":{"Q1_winner":"T03","Q1_conf":2,"Q2_winner":"T09","Q2_conf":1}},
 "source_guess":{"T03":{"guess":"不确定","confidence":1}}}'''
for j, (tid, (porder, mode)) in enumerate(PW_ORDERS.items(), 1):
    lines = ["## 评审材料（严格按以下顺序逐对评审；每对内先读第一篇再读第二篇）\n"]
    involved = []
    for k, pid in enumerate(porder):
        a, b = PAIRS[pid]
        if mode == "reversed" or (mode == "alternate" and k % 2 == 1):
            a, b = b, a
        involved += [a, b]
        lines.append(f"{k+1}. 对 {pid}：第一篇 `{BV2}/full/{a}.md`　第二篇 `{BV2}/full/{b}.md`")
    c = header(tid, "PW（同题成对比较）", j,
               extra="共 5 对同题/近题稿件，每对二选一。")
    c += rubric_section("R_PW.md") + "\n"
    c += "\n".join(lines) + "\n\n"
    c += output_section(tid, PW_BODY, PW_JSON % (tid, j), ["每对两问均强制二选一，不允许平局。"])
    # 补充 source_guess 覆盖说明
    c += "\n（来源猜测须覆盖本任务读过的全部 10 篇。）\n"
    write(tid, c)

# ---------- 设计集 V4A ----------
DSA = {"J16": ["D03","D01","D05","D02","D04"], "J17": ["D04","D02","D01","D05","D03"]}
for j, (tid, order) in enumerate(DSA.items(), 1):
    c = header(tid, "V4-A·设计集（快读价值·截断输入）", j,
               extra="**你只拿到每篇的摘片，拿不到全文——这是实验设计；不得索要全文。**")
    c += rubric_section("R_V4A_ds.md") + "\n"
    c += materials_section(order, "excerpt") + "\n"
    body = V4A_BODY.replace("12 篇", "5 篇")
    jt = V4A_JSON % (tid, j)
    jt = jt.replace('"T01"', '"D01"').replace('["T05","T01"]', '["D05","D01"]').replace('"condition":"V4A"', '"condition":"V4A_ds"')
    c += output_section(tid, body, jt, ["排名不允许并列；先按 A 档、同档按总分、再同按\"轴即拍板\"分排序。","用途类型如跨类，取主导类型的单一标签。","摘片中\"（无建议/对策类条目）\"等提取占位说明可直接引作证据。"])
    write(tid, c)

# ---------- 设计集 V4B ----------
DSB = {"J18": ["D02","D05","D01","D04","D03"], "J19": ["D05","D03","D04","D01","D02"]}
for j, (tid, order) in enumerate(DSB.items(), 1):
    c = header(tid, "V4-B·设计集（细读裁决·全文＋预检单）", j,
               extra="每篇稿件附带一份程序生成的《机械预检单》，用法见标尺。")
    c += rubric_section("R_V4B_ds.md") + "\n"
    c += materials_section(order, "full+pre") + "\n"
    body = V4B_BODY.replace("12 篇", "5 篇")
    jt = V4B_JSON % (tid, j)
    jt = jt.replace('"T01"', '"D01"').replace('["T05","T01"]', '["D05","D01"]').replace('"condition":"V4B"', '"condition":"V4B_ds"')
    c += output_section(tid, body, jt, ["排名不允许并列；先按 B 档、同档按总分、再同按\"证据颗粒与归属\"分排序。","用途类型如跨类，取主导类型的单一标签。","performance_flags 填你判定为\"表演\"（显性声明无证据支撑）的处数。"])
    write(tid, c)

print("生成完成：", sorted(os.listdir(TASKS)))
