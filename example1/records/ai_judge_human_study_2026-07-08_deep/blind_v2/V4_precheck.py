# -*- coding: utf-8 -*-
"""
盲测集 v2 机械预检单生成器（V4）。
对 full/ 下 17 篇归一化全文逐篇计数，precheck/ 下每篇输出一张小表。
只列数字与命中示例，不做任何解读。

指标定义（全部机械正则，17 篇统一）：
1 链式公式数        破折号/箭头连缀≥3项（≥2个连接符）的 A—B—C 式结构；连接符 — 或 →，
                    项为不含标点/空白/破折号的 1-12 字段；"——"行文破折号因中间项为空不计入。
2 评估脚手架密度    (优势在于|局限在于|对我国而言|参考价值|启示在于|值得注意的是|值得关注的是)
                    每千字命中次数。
3 元话语宣告密度    (可概括为|呈现出?[一二三四五六七八九十两三]大|本文|本报告|综上|总体来看|
                    由此可见|需要指出的是) 每千字命中次数。
4 模糊载体×精确数字 (据公开报道|有研究显示|相关研究|数据显示|有分析认为|据统计|据报道)
                    与阿拉伯数字/百分比同句（以。！？切分）共现的句数。
5 军事化语域命中    词表复用仓库唯一真源 strategic_response_workflow/shared_schema/
                    register_blacklist.md（甲乙丙三类并集）；逐处列原文短语。
6 模型指纹词        张力|光谱；上下文±20字含(物理|光学|波长|频谱|色散)者排除并单独注明。
7 段末概括句占比    末句以(总的来看|这表明|由此|可见|综上|换言之|这意味着)开头的正文段落
                    占全部正文段落（不含标题与小标题行）的比例。
千字基数 = 全文去空白字符数。
"""
import re, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
FULL, PRE = os.path.join(BASE, "full"), os.path.join(BASE, "precheck")
os.makedirs(PRE, exist_ok=True)

SEG = r'[^\s，。；、：""\'\'（）【】《》\n—→-]'
CHAIN = re.compile(rf"{SEG}{{1,12}}(?:[—→]{SEG}{{1,12}}){{2,}}")
SCAFFOLD = re.compile(r"优势在于|局限在于|对我国而言|参考价值|启示在于|值得注意的是|值得关注的是")
METATALK = re.compile(r"可概括为|呈现出?[一二三四五六七八九十两三]大|本文|本报告|综上|总体来看|由此可见|需要指出的是")
VAGUE = re.compile(r"据公开报道|有研究显示|相关研究|数据显示|有分析认为|据统计|据报道")
DIGIT = re.compile(r"\d")
# 军事化词表：strategic_response_workflow/shared_schema/register_blacklist.md 甲/乙/丙类并集
MILITARY = re.compile(r"破封锁|钳形攻势|压制矩阵|釜底抽薪|第二战场|反守为攻|绞杀|围堵|遏制|封锁|虹吸|收割"
                      r"|反制|对抗|敌意|蓄意|抢[夺占]?[^，。；\n]{0,4}(?:人才|资源|标准)")
FINGERPRINT = re.compile(r"张力|光谱")
PHYSICS = re.compile(r"物理|光学|波长|频谱|色散")
SUMM_TAIL = re.compile(r"^(总的来看|这表明|由此|可见|综上|换言之|这意味着)")
HEADING = re.compile(r"^(?:[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)")

def is_heading(p):
    return bool(HEADING.match(p)) and len(p) <= 80 and not p.endswith(("。", "？", "！"))

def ctx(text, m, w=12):
    return text[max(0, m.start() - w):m.end() + w].replace("\n", " ")

for path in sorted(glob.glob(os.path.join(FULL, "*.md"))):
    text = open(path, encoding="utf-8").read()
    kchars = len(re.sub(r"\s", "", text)) / 1000.0
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    body = [p for p in paras[1:] if not is_heading(p)]  # 首段视作标题行/首段，正文段落统计从第2块起

    chain_hits = [(m.group(0), ctx(text, m)) for m in CHAIN.finditer(text)]
    scaf_hits = [ctx(text, m) for m in SCAFFOLD.finditer(text)]
    meta_hits = [ctx(text, m) for m in METATALK.finditer(text)]
    sents = re.split(r"[。！？]", text)
    vague_sents = [s.strip()[:60] for s in sents if VAGUE.search(s) and DIGIT.search(s)]
    mil_hits = [ctx(text, m) for m in MILITARY.finditer(text)]
    fp_hits, fp_excl = [], []
    for m in FINGERPRINT.finditer(text):
        c = text[max(0, m.start() - 20):m.end() + 20]
        (fp_excl if PHYSICS.search(c) else fp_hits).append(ctx(text, m))
    summ = [p for p in body
            if SUMM_TAIL.match(([x for x in re.split(r"(?<=[。！？])", p) if x.strip()] or [p])[-1].strip().lstrip('"'))]
    n_body = len(body)

    name = os.path.basename(path)
    L = [f"{name.replace('.md','')} 机械预检单", ""]
    L += ["| 指标 | 值 |", "|---|---|",
          f"| 全文字数（去空白） | {int(kchars*1000)} |",
          f"| 链式公式数（A—B—C式，≥3项） | {len(chain_hits)} |",
          f"| 评估脚手架命中 | {len(scaf_hits)}（{len(scaf_hits)/kchars:.2f}/千字） |",
          f"| 元话语宣告命中 | {len(meta_hits)}（{len(meta_hits)/kchars:.2f}/千字） |",
          f"| 模糊载体×精确数字同句 | {len(vague_sents)} |",
          f"| 军事化语域命中 | {len(mil_hits)} |",
          f"| 模型指纹词（张力/光谱） | {len(fp_hits)}（另有物理语境排除 {len(fp_excl)}） |",
          f"| 段末概括句占比 | {len(summ)}/{n_body}（{100.0*len(summ)/n_body if n_body else 0:.1f}%） |", ""]
    def block(title, items):
        out = [f"命中示例·{title}"]
        out += [f"- {x}" for x in items] if items else ["- （无）"]
        out.append("")
        return out
    L += block("链式公式", [f"{h} ｜ 语境：{c}" for h, c in chain_hits])
    L += block("评估脚手架", scaf_hits)
    L += block("元话语宣告", meta_hits)
    L += block("模糊载体×精确数字（句首60字）", vague_sents)
    L += block("军事化语域", mil_hits)
    L += block("模型指纹词", fp_hits + [f"（排除）{x}" for x in fp_excl])
    L += block("段末概括句（段落前30字）", [p[:30] for p in summ])
    open(os.path.join(PRE, name), "w", encoding="utf-8").write("\n".join(L))
    print(f"{name}: 链式{len(chain_hits)} 脚手架{len(scaf_hits)} 元话语{len(meta_hits)} "
          f"模糊×数字{len(vague_sents)} 军事{len(mil_hits)} 指纹{len(fp_hits)} 段末括{len(summ)}/{n_body}")
