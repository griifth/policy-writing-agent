#!/usr/bin/env python3
# 〔快照 2026-07-13〕真源：example1/scripts/neican_docx.py（只读移植入 direction_workflow/tools/，除本头注外未改动一字）。
# 依赖：python3 ＋ python-docx（pip install python-docx）。真源改动后须重新快照，勿只改此副本。
"""内参版式 docx 导出器（默认格式：课题组研究报告体·像素级内参版式）。

用法：
    python3 scripts/neican_docx.py <input.md> <output.docx>

版式规格（默认，可按需微调）：
- 页面 A4，页边距 上下 2.54cm / 左右 2.8cm
- 标题：小二号(18pt) 黑体，居中
- 署名：三号(16pt) 楷体_GB2312，居中
- 一级标题「一、」：三号 黑体，独占一行，不缩进（内参惯例，非加粗以合课题组干净体）
- 二级标题「（一）」：三号 楷体_GB2312，独占一行，不缩进
- 正文：三号(16pt) 仿宋_GB2312，首行缩进 2 字，固定行距 28 磅
- 行内 **加粗** 论点句 → 加粗 run（仿宋，段首论点句加粗、例证内嵌）
- 政策文件《…》就地标注，不加角标、文末不列引用

约定输入 md（课题组干净体）：
- 第 1 行非空 = 标题；第 2 行非空 = 署名（含"课题组"）
- 行首匹配 ^[一二三四五六七八九十]+、  → 一级
- 行首匹配 ^（[一二三四五六七八九十]+）  → 二级
- 末行若含"课题组" → 居中署名
- 其余为正文；行内 **…** 记为加粗
"""
import sys, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

TITLE_FONT = "黑体"
NAME_FONT = "楷体_GB2312"
H1_FONT = "黑体"
H2_FONT = "楷体_GB2312"
BODY_FONT = "仿宋_GB2312"

def set_run(run, cn_font, size_pt, bold=False):
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.name = cn_font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = rpr.makeelement(qn('w:rFonts'), {})
        rpr.insert(0, rfonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rfonts.set(qn(attr), cn_font)

def add_para(doc, align=None, first_indent_chars=0, size_pt=16, space_after=0, line_pt=28):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    if align is not None:
        p.alignment = align
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    if line_pt:
        pf.line_spacing = Pt(line_pt)
    if first_indent_chars:
        pf.first_line_indent = Pt(size_pt * first_indent_chars)
    return p

def emit_runs(p, text, cn_font, size_pt):
    """把 **加粗** 片段拆成加粗/非加粗 run。"""
    for i, seg in enumerate(re.split(r'\*\*(.+?)\*\*', text)):
        if seg == '':
            continue
        set_run(p.add_run(seg), cn_font, size_pt, bold=(i % 2 == 1))

def build(md_path, out_path):
    lines = [l.rstrip('\n') for l in open(md_path, encoding='utf-8')]
    nonempty = [l for l in lines if l.strip()]
    title = nonempty[0].strip()
    byline = nonempty[1].strip()

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(2.54); sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(2.8); sec.right_margin = Cm(2.8)
    # Normal 缺省
    normal = doc.styles['Normal']
    normal.font.size = Pt(16); normal.font.name = BODY_FONT
    normal.element.rPr.rFonts.set(qn('w:eastAsia'), BODY_FONT)

    # 标题
    p = add_para(doc, WD_ALIGN_PARAGRAPH.CENTER, 0, 18, space_after=6, line_pt=32)
    set_run(p.add_run(title), TITLE_FONT, 18, bold=True)
    # 署名
    p = add_para(doc, WD_ALIGN_PARAGRAPH.CENTER, 0, 16, space_after=12)
    set_run(p.add_run(byline), NAME_FONT, 16, bold=False)

    body = nonempty[2:]
    last_is_name = body and ('课题组' in body[-1]) and (len(body[-1]) < 30)
    if last_is_name:
        tail_name = body[-1].strip(); body = body[:-1]
    else:
        tail_name = None

    h1 = re.compile(r'^[一二三四五六七八九十]+、')
    h2 = re.compile(r'^（[一二三四五六七八九十]+）')

    for raw in body:
        t = raw.strip()
        if h1.match(t):
            p = add_para(doc, WD_ALIGN_PARAGRAPH.LEFT, 0, 16, space_after=4, line_pt=28)
            set_run(p.add_run(t), H1_FONT, 16, bold=False)
        elif h2.match(t):
            p = add_para(doc, WD_ALIGN_PARAGRAPH.LEFT, 0, 16, space_after=4, line_pt=28)
            set_run(p.add_run(t), H2_FONT, 16, bold=False)
        elif t.startswith('（说明') or t.startswith('(说明'):
            p = add_para(doc, WD_ALIGN_PARAGRAPH.LEFT, 2, 14, space_after=0, line_pt=26)
            emit_runs(p, t, "楷体_GB2312", 14)
        else:
            p = add_para(doc, WD_ALIGN_PARAGRAPH.LEFT, 2, 16, space_after=0, line_pt=28)
            emit_runs(p, t, BODY_FONT, 16)

    if tail_name:
        add_para(doc, line_pt=28)  # 空行
        p = add_para(doc, WD_ALIGN_PARAGRAPH.RIGHT, 0, 16, space_after=0)
        set_run(p.add_run(tail_name), NAME_FONT, 16, bold=False)

    doc.save(out_path)
    print(f"已生成内参版式 docx：{out_path}")

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
