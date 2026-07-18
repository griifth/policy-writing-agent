# -*- coding: utf-8 -*-
"""
机械预检脚本（direction_workflow · 工包三：机械闸 / 预检元件）。

用途：逐篇 markdown 计数机械命中项，把结果打印成一张「预检单」到 stdout。
定位：纯机械、零裁量。本脚本只计数、只摘录命中位置，**不打分、不判合格、不给结论**。
      合不合格是人的事；脚本只把可数的东西数清楚、摆出来。

命令行用法：
    python3 precheck.py <markdown文件> [结构单.md]
    （第二个参数可选：给出本篇结构单，脚本追打「成稿标题序 vs 结构单标题序」对照，供
     主线保真检查项2 人工/规程逐位比对；脚本不判等、不下结论。）

机械指标（全部机械正则，逐篇统一口径）：
  1 链式公式        A→B→C 式因果链堆叠：1-12 字的短段被 → 或 — 连缀，≥3 段（≥2 个连接符）。
  2 评估脚手架      评估器口吻：维度枚举（第X维/从X个维度）＋ 评述套话（优势在于/局限在于/启示在于…）。
  3 元话语宣告      文章自指的宣告腔（本文/综上/呈现X大/如下所示…）。
  4 模糊载体×精确数字  模糊主语/来源（据报道/不少/大量…）与精确数字或百分比同句 —— 伪精确。
  5 军事化语域      词表读取包内快照 gates/register_blacklist.md（甲乙丙三类并集）。
                    真源：strategic_response_workflow/shared_schema/register_blacklist.md，
                    真源改动后须重新快照进包（见 移植说明.md）。
  6 段末概括占比    以概括句收尾（总的来看/这表明/由此可见…）的正文段落数 ÷ 正文段落总数。
  7 生造词/内部词命中  独立读 gates/lexicon_blacklist.md（direction_workflow 自有真源）：
                    丁类生造复合词＋戊类内部术语外漏＋己类学术模型名（硬禁，计入命中）；
                    庚类"语境慎用"（下行风险）单列提示、**不计入命中**（W1.4 图纸 Q4）。
                    本项与第5项军事化语域**并列、互不合并**（DEV-03）。

第5项军事化语域与第7项生造词/内部词命中读两张**不同的表**、走两个**独立函数**
（load_military_terms 读 register_blacklist、load_lexicon_terms 读 lexicon_blacklist），
互不干扰；第5项逻辑与触发线原样不动、不放松。

千字基数 = 全文去空白字符数（供密度类指标换算，非阈值）。
实现风格参考 records/ai_judge_human_study_2026-07-08_deep/blind_v2/V4_precheck.py，独立成文。
"""
import re
import os
import sys


# ─────────────────────────────────────────────────────────────────────────
# 军事化词表：读取与本脚本同目录的包内快照 gates/register_blacklist.md。
# 真源在 strategic_response_workflow/shared_schema/register_blacklist.md，
# 真源改动后须重新快照进包，勿只改快照副本。
# ─────────────────────────────────────────────────────────────────────────
BLACKLIST_FILENAME = "register_blacklist.md"


def find_blacklist():
    """返回与本脚本同目录的词表快照绝对路径。

    找不到即抛错——军事化一项无法机械计数时明确报错，不静默跳过。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(here, BLACKLIST_FILENAME)
    if os.path.isfile(cand):
        return cand
    raise FileNotFoundError(
        "未找到军事化词表快照：{}（应与 precheck.py 同目录；"
        "真源为 strategic_response_workflow/shared_schema/register_blacklist.md）".format(cand)
    )


def load_military_terms(path):
    """从 register_blacklist.md 解析甲/乙/丙三类词，取并集去重。

    解析规则（贴合该文件现行体例）：
      - 定位 `**甲类`/`**乙类`/`**丙类` 三行加粗小标题，取其紧邻的下一非空正文行为词表行；
      - 词表行以全角竖线 ｜ 切分为若干条目；
      - 每条目：先摘出其中的引号内短语（作字面变体一并纳入），再剥离所有括注（（）与半角()），
        剩余部分按 / 、 空白再切，取非空词；
      - 丢弃 “组合式变体” 这类元标签（本身不是可匹配的文本）。
    返回：去重后的词列表（保持稳定顺序）。
    """
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    header = re.compile(r"^\*\*[甲乙丙]类")
    quoted = re.compile(r"[\"“”'']([^\"“”'']{1,20})[\"“”'']")
    paren = re.compile(r"（[^）]*）|\([^)]*\)")
    META_LABELS = {"组合式变体"}

    terms = []
    seen = set()

    def add(w):
        w = w.strip().strip("\"“”''").strip()
        if not w or w in META_LABELS or w in seen:
            return
        seen.add(w)
        terms.append(w)

    i = 0
    while i < len(lines):
        if header.match(lines[i].strip()):
            # 取紧邻的下一非空行作词表行
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                row = lines[j]
                for seg in row.split("｜"):
                    for q in quoted.findall(seg):   # 括注/引号内的字面变体
                        add(q)
                    core = paren.sub("", seg)        # 去括注后的主词
                    for piece in re.split(r"[/、\s]+", core):
                        add(piece)
            i = j
        i += 1
    return terms


# ─────────────────────────────────────────────────────────────────────────
# 生造词/内部词表：读取与本脚本同目录的 direction_workflow 自有真源
# gates/lexicon_blacklist.md（丁类生造复合词/戊类内部术语外漏/己类学术模型名/庚类语境慎用）。
# 本表即真源、非快照；与军事化 register_blacklist 各归其层、互不合并（DEV-03 / W1.4 图纸③）。
# 本函数与 load_military_terms 完全独立，互不干扰；军事化第5项逻辑一字不动。
# ─────────────────────────────────────────────────────────────────────────
LEXICON_FILENAME = "lexicon_blacklist.md"


def find_lexicon():
    """返回与本脚本同目录的生造词/内部词表绝对路径。

    找不到即抛错——本项无法机械计数时明确报错，不静默跳过。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(here, LEXICON_FILENAME)
    if os.path.isfile(cand):
        return cand
    raise FileNotFoundError(
        "未找到生造词/内部词表：{}（应与 precheck.py 同目录；"
        "direction_workflow 自有真源，非快照）".format(cand)
    )


def load_lexicon_terms(path, classes):
    """从 lexicon_blacklist.md 解析指定类的词，取并集去重。

    classes：要加载的类字符元组，如 ("丁", "戊", "己")（硬禁）或 ("庚",)（语境慎用）。
    解析规则（贴合该文件体例，但与 load_military_terms 独立）：
      - 定位 `**丁类`/`**戊类`/`**己类`/`**庚类` 加粗小标题行，类字符须在 classes 内；
      - 取其紧邻的下一非空正文行为词表行；
      - 词表行**只**以全角竖线 ｜ 切分（不再按 / 或空白切——保全 "Policy Transfer"
        "CIPP 模型" "期望-绩效差距理论" 等含空格/连字符的整词）；
      - 每条目剥离所有括注（（）与半角()，如"（开放清单，实测新命中追加）"）后取非空词。
    返回：去重后的词列表（保持稳定顺序）。
    """
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    header = re.compile(r"^\*\*([丁戊己庚])类")
    paren = re.compile(r"（[^）]*）|\([^)]*\)")

    terms = []
    seen = set()

    def add(seg):
        w = paren.sub("", seg).strip().strip("｜").strip()
        if not w or w in seen:
            return
        seen.add(w)
        terms.append(w)

    i = 0
    while i < len(lines):
        m = header.match(lines[i].strip())
        if m and m.group(1) in classes:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                for seg in lines[j].split("｜"):
                    add(seg)
            i = j
        i += 1
    return terms


# ─────────────────────────────────────────────────────────────────────────
# 标题序提取（供主线保真检查项2：成稿标题序 vs 结构单序 人工/规程比对）
# 纯提取、不判等、不下结论。
# ─────────────────────────────────────────────────────────────────────────
MD_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
ZH_HEADING = re.compile(r"^((?:[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)\s*.*\S)\s*$")


def extract_headings(text):
    """按文档顺序摘出小标题：markdown 标题(# …)与中文标题式行(一、/（一）…)。

    返回：[标题文本, …]（去掉 # 号，保留中文序号）。纯提取、供人工比对，不判等。
    """
    out = []
    for line in text.splitlines():
        s = line.rstrip()
        m = MD_HEADING.match(s)
        if m:
            out.append(m.group(2).strip())
            continue
        z = ZH_HEADING.match(s.lstrip())
        if z:
            out.append(z.group(1).strip())
    return out


# ─────────────────────────────────────────────────────────────────────────
# 机械指标的正则
# ─────────────────────────────────────────────────────────────────────────
# 1 链式公式：1-12 字短段被 → 或 — 连缀，≥3 段（≥2 个连接符）。"——"行文破折号中间项为空不计。
SEG = r'[^\s，。；、：""\'\'（）【】《》\n—→⇒-]'
CHAIN = re.compile(rf"{SEG}{{1,12}}(?:[—→⇒]{SEG}{{1,12}}){{2,}}")

# 2 评估脚手架：维度枚举器 + 评述套话
SCAFFOLD = re.compile(
    r"第[一二三四五六七八九十]+[维层面点]"
    r"|从[一二三四五六七八九十\d]+个?(?:维度|方面|层面)"
    r"|[一二三四五六七八九十]+个维度"
    r"|优势在于|局限在于|不足在于|问题在于|关键在于"
    r"|对我国而言|参考价值|借鉴意义|启示在于|值得注意的是|值得关注的是"
)

# 3 元话语宣告：文章自指宣告腔
METATALK = re.compile(
    r"(?<!日)本文(?!部)|本报告|本节|下文将|如下所示|如上所述|综上所述|综上|总体来看"
    r"|可概括为|呈现出?[一二三四五六七八九十两三]大|由此可见|需要指出的是"
)

# 4 模糊载体：模糊来源 + 模糊数量主语
VAGUE = re.compile(
    r"据公开报道|有研究显示|相关研究|数据显示|有分析认为|据统计|据报道|据悉|有观点认为"
    r"|不少|大量|许多|多数|众多|相当一部分|绝大多数|普遍认为|广泛"
)
# 精确数字/百分比
DIGIT = re.compile(r"\d|百分之[一二三四五六七八九十百千零点]+")

# 6 段末概括标记：末句以概括腔起头
SUMM_TAIL = re.compile(
    r"^(?:总的来看|总体来看|总体而言|总之|综上|由此可见|由此|可见|这表明|"
    r"这意味着|换言之|因此|归根结底|不难看出|足见)"
)

# 段落形态：标题式行 / 非正文块的识别
HEADING_ZH = re.compile(r"^(?:[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)")


def ctx(text, m, w=14):
    return text[max(0, m.start() - w): m.end() + w].replace("\n", " ").strip()


def is_body_paragraph(block):
    """判定一个 markdown 段落块是否算「正文散文段落」（供段末概括占比统计）。

    排除：markdown 标题(# )、引用(>)、列表(- * 数字.)、表格(|)、代码围栏、
          中文标题式短行（一、/（一）且短且不以句末标点收尾）。
    """
    s = block.strip()
    if not s:
        return False
    first = s.splitlines()[0].lstrip()
    if first.startswith(("#", ">", "|", "```", "- ", "* ", "+ ")):
        return False
    if re.match(r"^\d+[.、)]", first):
        return False
    if HEADING_ZH.match(s) and len(s) <= 80 and not s.endswith(("。", "？", "！", "”")):
        return False
    return True


def last_sentence(block):
    parts = [x for x in re.split(r"(?<=[。！？])", block) if x.strip()]
    tail = (parts or [block])[-1].strip()
    return tail.lstrip("\"“”'' 　")


def run(path, struct_path=None):
    text = open(path, encoding="utf-8").read()
    kchars = len(re.sub(r"\s", "", text)) / 1000.0
    blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]

    # 1 链式公式
    chain_hits = [(m.group(0), ctx(text, m)) for m in CHAIN.finditer(text)]

    # 2 评估脚手架
    scaf_hits = [ctx(text, m) for m in SCAFFOLD.finditer(text)]

    # 3 元话语宣告
    meta_hits = [ctx(text, m) for m in METATALK.finditer(text)]

    # 4 模糊载体 × 精确数字（同句共现）
    sents = re.split(r"[。！？\n]", text)
    vague_sents = [s.strip()[:70] for s in sents if VAGUE.search(s) and DIGIT.search(s)]

    # 5 军事化语域（词表运行时读原路径）
    bl_path = find_blacklist()
    mil_terms = load_military_terms(bl_path)
    mil_re = re.compile("|".join(re.escape(t) for t in mil_terms)) if mil_terms else None
    mil_hits = [ctx(text, m) for m in mil_re.finditer(text)] if mil_re else []

    # 6 段末概括占比
    body = [b for b in blocks if is_body_paragraph(b)]
    summ = [b for b in body if SUMM_TAIL.match(last_sentence(b))]
    n_body = len(body)

    # 7 生造词/内部词命中（独立读 lexicon_blacklist.md，与第5项互不干扰）
    lex_path = find_lexicon()
    lex_hard = load_lexicon_terms(lex_path, ("丁", "戊", "己"))   # 硬禁：计入命中
    lex_soft = load_lexicon_terms(lex_path, ("庚",))              # 语境慎用：不计入命中
    lex_re = re.compile("|".join(re.escape(t) for t in lex_hard)) if lex_hard else None
    lex_hits = [ctx(text, m) for m in lex_re.finditer(text)] if lex_re else []
    soft_re = re.compile("|".join(re.escape(t) for t in lex_soft)) if lex_soft else None
    soft_hits = [ctx(text, m) for m in soft_re.finditer(text)] if soft_re else []

    # 标题序（供主线保真检查项2 人工/规程比对；纯提取、不判等）
    doc_headings = extract_headings(text)
    struct_headings = None
    if struct_path:
        struct_headings = extract_headings(open(struct_path, encoding="utf-8").read())

    # ── 打印预检单（只列命中，不判合格）──
    name = os.path.basename(path)
    P = print
    P("=" * 60)
    P("{} · 机械预检单".format(name))
    P("（纯机械计数；不打分、不判合格。判断留人工。）")
    P("=" * 60)
    P("| 指标 | 命中数 |")
    P("|---|---|")
    P("| 全文字数（去空白） | {} |".format(int(kchars * 1000)))
    P("| 1 链式公式（A→B→C 式，≥3 段） | {} |".format(len(chain_hits)))
    P("| 2 评估脚手架 | {}（{:.2f}/千字） |".format(len(scaf_hits), len(scaf_hits) / kchars if kchars else 0))
    P("| 3 元话语宣告 | {}（{:.2f}/千字） |".format(len(meta_hits), len(meta_hits) / kchars if kchars else 0))
    P("| 4 模糊载体×精确数字（同句） | {} |".format(len(vague_sents)))
    P("| 5 军事化语域 | {} |".format(len(mil_hits)))
    P("| 6 段末概括占比 | {}/{}（{:.1f}%） |".format(
        len(summ), n_body, 100.0 * len(summ) / n_body if n_body else 0))
    P("| 7 生造词/内部词命中（lexicon 丁/戊/己类·硬禁） | {} |".format(len(lex_hits)))
    P("| └ 语境慎用（庚类·不计入命中） | {} |".format(len(soft_hits)))
    P("")
    P("军事化词表来源（包内快照 gates/register_blacklist.md，真源见 移植说明.md）：")
    P("  {}".format(bl_path))
    P("  载入词条 {} 个：{}".format(len(mil_terms), "、".join(mil_terms)))
    P("")
    P("生造词/内部词表来源（direction_workflow 自有真源 gates/lexicon_blacklist.md，非快照）：")
    P("  {}".format(lex_path))
    P("  硬禁词条（丁/戊/己类）{} 个：{}".format(len(lex_hard), "、".join(lex_hard)))
    P("  语境慎用词条（庚类·不计入命中）{} 个：{}".format(len(lex_soft), "、".join(lex_soft)))
    P("")

    def block_out(title, items):
        P("── 命中摘录 · {} ──".format(title))
        if items:
            for x in items:
                P("  - {}".format(x))
        else:
            P("  -（无命中）")
        P("")

    block_out("1 链式公式", ["{} ｜ 语境：{}".format(h, c) for h, c in chain_hits])
    block_out("2 评估脚手架", scaf_hits)
    block_out("3 元话语宣告", meta_hits)
    block_out("4 模糊载体×精确数字（句首70字）", vague_sents)
    block_out("5 军事化语域", mil_hits)
    block_out("6 段末概括句（段落前30字）", [b.strip()[:30] for b in summ])
    block_out("7 生造词/内部词命中（lexicon 丁/戊/己类·硬禁）", lex_hits)
    block_out("7附 语境慎用（庚类·仅提示·不计入命中·是否改写交人工）", soft_hits)

    # 标题序对照（供主线保真检查项2；纯提取、脚本不判等、不下结论）
    P("── 标题序（供主线保真检查项2 人工/规程比对；脚本不判等、不下结论）──")
    P("  成稿标题序（共 {} 条）：".format(len(doc_headings)))
    if doc_headings:
        for k, h in enumerate(doc_headings, 1):
            P("    {}. {}".format(k, h))
    else:
        P("    -（未提取到 markdown/中文式小标题）")
    if struct_headings is not None:
        P("  结构单标题序（共 {} 条，来自 {}）：".format(
            len(struct_headings), os.path.basename(struct_path)))
        if struct_headings:
            for k, h in enumerate(struct_headings, 1):
                P("    {}. {}".format(k, h))
        else:
            P("    -（未从结构单提取到标题式行——结构单「主线段-节问题链」新格式节序机检不可靠，"
              "等序判定按规程/人工先行，见 W2.3 脚本欠账）")
    else:
        P("  结构单标题序：未提供结构单参数；等序判定按主线保真检查项2 规程/人工先行。")
    P("")
    P("=" * 60)
    P("预检单结束。以上为机械计数结果，是否返修由后续闸门规程与人工裁量。")


def main():
    if len(sys.argv) not in (2, 3):
        sys.stderr.write("用法：python3 precheck.py <markdown文件> [结构单.md]\n")
        sys.exit(2)
    target = sys.argv[1]
    if not os.path.isfile(target):
        sys.stderr.write("找不到文件：{}\n".format(target))
        sys.exit(2)
    struct = sys.argv[2] if len(sys.argv) == 3 else None
    if struct is not None and not os.path.isfile(struct):
        sys.stderr.write("找不到结构单文件：{}\n".format(struct))
        sys.exit(2)
    run(target, struct)


if __name__ == "__main__":
    main()
