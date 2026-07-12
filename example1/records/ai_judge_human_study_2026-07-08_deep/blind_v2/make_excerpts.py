# -*- coding: utf-8 -*-
"""
盲测集 v2 A通道截断摘片生成器（纯机械，无人工挑选）。
输入：full/T01..T12.md, D01..D05.md（归一化全文，段间单空行，首行为标题）
输出：excerpt/ 同名文件，格式：
    【标题】
    【小标题目录】（全部一二级小标题，按原顺序）
    【首屏】（正文开头前600字，不含标题与小标题行，保留段落分隔）
    【建议条目首句】（建议/对策/启示类章节下每个条目的第一句）

机械规则（全部17篇统一）：
- 标题 = 首行，若首行长度>60或以句读号结尾则视为无独立标题行，记（原文无独立标题行）。
- 小标题 = 独立成段、以"一、/（一）"等编号领起、长度≤80、不以句号问号叹号结尾的行。
- 建议章节 = 一级标题含（建议|对策|启示|应对|借鉴）之一的章节；
  若均不含，则取末章且其标题含（我国|中国）者；两者皆无则记（无）。
- 条目 = 建议章节内以"第X，"或"X是"领起的段落；另若章节内有二级小标题、
  且其后首段不属于前述两型，则该首段亦计为一个条目。
- 第一句 = 段首至首个 。？！ 止（其后紧跟的引号/括号并入）。
"""
import re, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
FULL, EXC = os.path.join(BASE, "full"), os.path.join(BASE, "excerpt")
os.makedirs(EXC, exist_ok=True)

H1_PAT = re.compile(r"^[一二三四五六七八九十]+、")
H2_PAT = re.compile(r"^（[一二三四五六七八九十]+）")
ENTRY_PAT = re.compile(r"^(?:第[一二三四五六七八九十]+，|[一二三四五六七八九十]+是)")
KEYWORDS = re.compile(r"建议|对策|启示|应对|借鉴")
CN_FALLBACK = re.compile(r"我国|中国")

def is_heading(p, pat):
    return bool(pat.match(p)) and len(p) <= 80 and not p.endswith(("。", "？", "！"))

def first_sentence(p):
    m = re.search(r'^.*?[。？！]["）]?', p)
    return m.group(0) if m else p

for path in sorted(glob.glob(os.path.join(FULL, "*.md"))):
    paras = [p.strip() for p in open(path, encoding="utf-8").read().split("\n\n") if p.strip()]
    # 标题
    if len(paras[0]) <= 60 and not paras[0].endswith(("。", "？", "！", "；", "，")):
        title, body = paras[0], paras[1:]
    else:
        title, body = "（原文无独立标题行）", paras
    # 小标题目录
    toc = [p for p in body if is_heading(p, H1_PAT) or is_heading(p, H2_PAT)]
    # 首屏600字
    shown, acc = [], 0
    for p in body:
        if p in toc:
            continue
        if acc + len(p) <= 600:
            shown.append(p); acc += len(p)
        else:
            shown.append(p[:600 - acc]); acc = 600
        if acc >= 600:
            break
    # 建议章节定位
    h1_idx = [i for i, p in enumerate(body) if is_heading(p, H1_PAT)]
    chapters = []  # (heading, [paras])
    for k, i in enumerate(h1_idx):
        j = h1_idx[k + 1] if k + 1 < len(h1_idx) else len(body)
        chapters.append((body[i], body[i + 1:j]))
    sel = [c for c in chapters if KEYWORDS.search(c[0])]
    if not sel and chapters and CN_FALLBACK.search(chapters[-1][0]):
        sel = [chapters[-1]]
    # 条目首句
    firsts = []
    for _, paras_c in sel:
        prev_h2 = False
        for p in paras_c:
            if is_heading(p, H2_PAT):
                prev_h2 = True
                continue
            if ENTRY_PAT.match(p):
                firsts.append(first_sentence(p))
            elif prev_h2:
                firsts.append(first_sentence(p))
            prev_h2 = False
    out = ["【标题】", title, "", "【小标题目录】"]
    out += toc if toc else ["（无）"]
    out += ["", "【首屏】"] + shown + ["", "【建议条目首句】"]
    out += ["- " + s for s in firsts] if firsts else ["（无建议/对策/启示类章节或未提取到条目）"]
    name = os.path.basename(path)
    open(os.path.join(EXC, name), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"{name}: toc={len(toc)} 首屏={acc}字 条目={len(firsts)}")
