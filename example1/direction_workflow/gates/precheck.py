# -*- coding: utf-8 -*-
"""
机械预检脚本（direction_workflow · 工包三：机械闸 / 预检元件）。

用途：逐篇 markdown 计数六类机械命中项，把结果打印成一张「预检单」到 stdout。
定位：纯机械、零裁量。本脚本只计数、只摘录命中位置，**不打分、不判合格、不给结论**。
      合不合格是人的事；脚本只把可数的东西数清楚、摆出来。

命令行用法：
    python3 precheck.py <markdown文件>

六项指标（全部机械正则，逐篇统一口径）：
  1 链式公式        A→B→C 式因果链堆叠：1-12 字的短段被 → 或 — 连缀，≥3 段（≥2 个连接符）。
  2 评估脚手架      评估器口吻：维度枚举（第X维/从X个维度）＋ 评述套话（优势在于/局限在于/启示在于…）。
  3 元话语宣告      文章自指的宣告腔（本文/综上/呈现X大/如下所示…）。
  4 模糊载体×精确数字  模糊主语/来源（据报道/不少/大量…）与精确数字或百分比同句 —— 伪精确。
  5 军事化语域      词表复用仓库唯一真源，运行时按原路径读取，不在本目录复制：
                    strategic_response_workflow/shared_schema/register_blacklist.md（甲乙丙三类并集）。
  6 段末概括占比    以概括句收尾（总的来看/这表明/由此可见…）的正文段落数 ÷ 正文段落总数。

千字基数 = 全文去空白字符数（供密度类指标换算，非阈值）。
实现风格参考 records/ai_judge_human_study_2026-07-08_deep/blind_v2/V4_precheck.py，独立成文。
"""
import re
import os
import sys


# ─────────────────────────────────────────────────────────────────────────
# 军事化词表：不复制进本目录，运行时按原路径读取唯一真源。
# ─────────────────────────────────────────────────────────────────────────
BLACKLIST_RELPATH = os.path.join(
    "strategic_response_workflow", "shared_schema", "register_blacklist.md"
)


def find_blacklist():
    """从本脚本所在处逐级向上，找到含唯一真源词表的仓库根，返回词表绝对路径。

    找不到即抛错——军事化一项无法机械计数时明确报错，不静默跳过。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    while True:
        cand = os.path.join(d, BLACKLIST_RELPATH)
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    raise FileNotFoundError(
        "未能按原路径找到军事化词表唯一真源：{}（自 {} 起逐级向上未命中）".format(
            BLACKLIST_RELPATH, here
        )
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
# 六项指标的机械正则
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


def run(path):
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
    P("")
    P("军事化词表来源（运行时按原路径读取，未复制进本目录）：")
    P("  {}".format(bl_path))
    P("  载入词条 {} 个：{}".format(len(mil_terms), "、".join(mil_terms)))
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
    P("=" * 60)
    P("预检单结束。以上为机械计数结果，是否返修由后续闸门规程与人工裁量。")


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("用法：python3 precheck.py <markdown文件>\n")
        sys.exit(2)
    target = sys.argv[1]
    if not os.path.isfile(target):
        sys.stderr.write("找不到文件：{}\n".format(target))
        sys.exit(2)
    run(target)


if __name__ == "__main__":
    main()
