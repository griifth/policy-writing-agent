# -*- coding: utf-8 -*-
"""盲测集 v2 泄漏自查：对 full/ 下 17 篇逐一扫 13 类格式 tell，全部应为 0。"""
import re, os, glob, sys

FULL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "full")

CJK = "一-鿿"
CHECKS = [
    ("01 pandoc三连杠分隔线", re.compile(r"^\s*-{3,}\s*$", re.M)),
    ("02 弯引号", re.compile(r"[“”‘’]")),
    ("04a #标题记号", re.compile(r"^#{1,6}\s", re.M)),
    ("04b **加粗记号", re.compile(r"\*\*|(?<!\*)\*(?!\*)")),
    ("04c >引用块记号", re.compile(r"^>\s?", re.M)),
    ("05 第X章体例", re.compile(r"第[一二三四五六七八九十]+章")),
    ("06a 素材文件标签", re.compile(r"\[[^\]\n]*\.(?:pdf|docx?|md|txt)[^\]\n]*\]", re.I)),
    ("06b 数字编号引用[n]", re.compile(r"\[\d{1,3}\]")),
    ("06c 〔来源·〕标签", re.compile(r"〔[^〕\n]*·[^〕\n]*〕")),
    ("07a 脚注标记", re.compile(r"\[\^")),
    ("07b 参考文献块", re.compile(r"^参考文献", re.M)),
    ("08a 编者注", re.compile(r"编者注")),
    ("08b 编者按", re.compile(r"编者按")),
    ("08c 方法说明括注", re.compile(r"（本报告[^）]{0,60}(?:生成|方法)[^）]*）")),
    ("09a 课题组署名行", re.compile(r"^.{0,30}课题组\s*$", re.M)),
    ("09b 日期落款行", re.compile(r"^\s*\d{4}年\d{1,2}月(?:\d{1,2}日)?\s*$", re.M)),
    ("10 基于XX报告式副题", re.compile(r"^——?基于.{2,40}的(?:分析|研究|报告)", re.M)),
    ("11 独立元信息行", re.compile(r"^(?:据现有检索材料|据检索材料|基于现有材料)[^\n]{0,80}$", re.M)),
    ("12a CJK邻接半角逗号", re.compile(rf"[{CJK}],|,[{CJK}]")),
    ("12b CJK邻接半角句号", re.compile(rf"[{CJK}]\.(?![a-zA-Z0-9])")),
    ("12c CJK邻接半角分/冒号", re.compile(rf"[{CJK}][;:](?![a-zA-Z0-9/])")),
    ("12d 全角（半角)错配", re.compile(rf"（[^（）()\n]*\)|\([^（）()\n]*）")),
    ("12e 残留连字杠(3+)", re.compile(r"-{3,}")),
    ("12f 全角字母数字", re.compile(r"[０-９ａ-ｚＡ-Ｚ]")),
    ("13a 首行缩进", re.compile(r"^[ \t　]+\S", re.M)),
    ("13b 连续多空行", re.compile(r"\n{3,}")),
    ("13c 行尾空白", re.compile(r"[ \t]+$", re.M)),
    ("13d 制表符/不可见字符", re.compile(r"[\t ​‎﻿]")),
    ("x1 pandoc转义残留", re.compile(r"\\[\[\]\"'*_#>().!—-]")),
    ("x2 FILE_NAME元信息", re.compile(r"FILE_NAME")),
    ("x3 markdown链接/图片", re.compile(r"!\[|\]\(")),
    ("x4 html标签", re.compile(r"</?(?:p|br|div|span|img|b|i|em|strong)\b", re.I)),
]
# 合法 camelCase 白名单（已逐一人工核对为机构/产品名，非 OCR 吞空格）
CAMEL_WHITELIST = {"LifeComp", "OpenCerts", "BitDegree", "aSSIST", "DigCompEdu",
                   "EduCloud", "NeurIPS", "DfE", "SkillsFuture", "ChatGPT"}  # 若扫出新词须人工复核

fail = 0
files = sorted(glob.glob(FULL + "/*.md"))
assert len(files) == 17, files
print(f"{'file':8s} 泄漏项")
for f in files:
    t = open(f, encoding="utf-8").read()
    bad = []
    for name, pat in CHECKS:
        hits = pat.findall(t)
        if hits:
            bad.append(f"{name}×{len(hits)}({str(hits[:2])[:60]})")
    # OCR 吞空格：camelCase 逐个对白名单
    for m in re.finditer(r"[A-Za-z]*[a-z][A-Z][A-Za-z]*", t):
        w = m.group(0)
        if not any(w in ww or ww in w for ww in CAMEL_WHITELIST):
            bad.append(f"03 未核对camelCase:{w}")
    # 文件级制式
    if not t.endswith("\n") or t.endswith("\n\n"):
        bad.append("13e 文件尾换行制式")
    lines = t.split("\n")
    if not lines[0].strip():
        bad.append("13f 首行为空")
    if bad:
        fail += 1
        print(f"{os.path.basename(f):8s} " + "; ".join(bad))
    else:
        print(f"{os.path.basename(f):8s} 全部 0")
print()
print("RESULT:", "FAIL" if fail else "ALL CLEAN (17/17)")
sys.exit(1 if fail else 0)
