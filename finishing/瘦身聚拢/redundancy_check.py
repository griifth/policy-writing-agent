# -*- coding: utf-8 -*-
"""
瘦身工序 · 机械冗余检测脚本（direction_workflow · finishing/瘦身工序_试点 / 甲段元件）。

用途：逐篇 markdown 检测三类机械冗余命中，把结果打印成一张 markdown《冗余登记表》到 stdout。
定位：纯机械、零裁量，不调用模型。本脚本只登记、只摘录命中位置与原句，
      **不判哪处该删、不改一个字**。合并与保留是瘦身工序乙段（agent 按登记表操作）
      与丙段（独立复核）的事；脚本只把重复的东西数清楚、摆出来。

命令行用法：
    python3 redundancy_check.py <成稿markdown> > <冗余登记表输出路径>

三项指标（全部机械正则/统计，逐篇统一口径）：
  1 锚重复        同一来源锚（S1/D2/E5/X1/P4/G2/R1/O6/C1/I1 等字母+数字式，「缺口N」式
                  工作流缺口锚，及「料包」引用、自然引述括注）在 ≥2 个章节出现，且其中 ≥2 处所在句 >30 字（即解释性
                  文字被复述了不止一遍；首引全述一处是应保留的，不算冗余）→ 该锚全部
                  落点逐条登记，供乙段挑「承重最好的一处」保全述、余处压指代。
  2 近逐字重复    跨章句子相似：每章切句（。！？分割，忽略 <15 字短句），两两跨章比较；
                  字符 6-gram Jaccard ≥ 0.5，**或**最长公共子串 ≥ 10 字（并联判据，
                  调参新增，见下）→ 登记一对，输出两句原文与所在章。
  3 高频判断短语  (a) 书名号/引号包裹的短语（按全文出现回数计）跨 ≥2 章出现；
                  (b) 4-20 字重复子串（下界原设 8，调参下修，见下）跨 ≥3 章、全文 ≥4 次、
                  含 ≥3 个汉字，且做最长化去包含（短串已被登记的长串覆盖则不重复登记）。

章节切分口径：## / ### 标题行、「一、二、」式标题行、独行加粗行（如 **边角料箱**）均起新章；
首个标题前的题名与定位区记为第 0 章「标题与定位」。

调参记录（拔尖篇实测，2026-07-14）：
  - 指标二原仅设 Jaccard ≥ 0.5 一道判据：漏掉 g=0.09 在四、六两章的近逐字对——两句
    枝叶措辞不同（「加速者与更年长的未加速者在学业表现上无显著差异」vs「加速者与更年长
    未加速者无显著差异」），6-gram Jaccard 实测仅 ~0.17，但核心子串「无显著差异（g=0.09」
    逐字相同 → 增设「最长公共子串 ≥ LCS_TH（10 字）」并联判据后命中。
  - 指标三重复子串下界原设 8 字：漏掉「识别标准与证据基座缺位」这组变体复述——四处
    出现的是变体（「…尚未就位」「…的缺位」「…应先于…」），8 字以上无逐字共串，变体间
    稳定内核是 4 字级的「证据基座」「识别标准」→ SUB_MIN 由 8 下修至 4，同时以
    「跨 ≥3 章 × 全文 ≥4 次 × 含 ≥3 汉字 × 最长化去包含」四道机械过滤压噪。
  - 引号短语章跨线设 ≥2（低于子串的 ≥3）：作者加引号本身即「判断短语/自造术语」信号，
    两章复用即值得登记（「识别标准与证据基座」在题名与第七章标题两处，≥3 会漏）。

实现风格参考 gates/precheck.py，独立成文。
"""
import os
import re
import sys
from collections import OrderedDict, defaultdict

# ─────────────────────────────────────────────────────────────────────────
# 可调参数（改动须在文件头「调参记录」补一行，不许静默改线）
# ─────────────────────────────────────────────────────────────────────────
EXPLAIN_LEN = 30          # 指标一：解释性句长线（去空白字符数）
MIN_SENT = 15             # 指标二：参与比较的最短句长（去空白）
NGRAM = 6                 # 指标二：字符 n-gram 长度
JACCARD_TH = 0.5          # 指标二：n-gram Jaccard 登记线
LCS_TH = 10               # 指标二：最长公共子串登记线（并联判据）
SUB_MIN, SUB_MAX = 4, 20  # 指标三：重复子串长度界（SUB_MIN 原设 8，实测调至 4）
SUB_SPREAD = 3            # 指标三：重复子串章跨线
SUB_FREQ = 4              # 指标三：重复子串全文频次线
SUB_MIN_CJK = 3           # 指标三：重复子串至少含几个汉字（滤纯年份/纯编码）
QUOTE_SPREAD = 2          # 指标三：引号/书名号短语章跨线

# ─────────────────────────────────────────────────────────────────────────
# 机械正则
# ─────────────────────────────────────────────────────────────────────────
HEAD_RE = re.compile(
    r"^(#{2,3}\s+\S.*"                        # ## / ### 标题行
    r"|[一二三四五六七八九十]+、\S.*"           # 「一、二、」式标题行
    r"|\*\*[^*\n]{1,24}\*\*\s*)$"             # 独行加粗（**边角料箱** 类组稿区标题）
)
ANCHOR_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z]\d{1,2})(?![0-9A-Za-z])")
ANCHOR_EXCLUDE = {"K12", "K9", "G20"}         # 常见非锚缩写（学段/组织名），非来源锚
GAP_RE = re.compile(r"缺口\d{1,2}")            # 本工作流的缺口锚（缺口1/缺口2…）
LIAOBAO = "料包"
# 自然引述括注（清稿后字母锚被还原为「作者＋年份」时的兜底锚形）；
# 括注内已含字母锚的不重复计（避免同一处双登记）。
NATCITE_RE = re.compile(r"（([^（）]{2,16}[，,]\s*(?:19|20)\d{2}[^（）]{0,10})）")
QUOTE_RE = re.compile(r"[“「]([^”」\n]{2,25})[”」]|《([^》\n]{2,30})》")
CJK_RE = re.compile(r"[一-鿿]")
PARTICLE_EDGE = "的了是与和在对以及之等而或从被把也均并"  # 指标三(b)：首末虚词串过滤
RUN_RE = re.compile(r"[一-鿿A-Za-z0-9=.%]+")  # 指标三取连续词串（不跨标点）


def norm(s):
    """去掉一切非汉字/字母/数字字符，供长度与 n-gram/LCS 比较（引号、锚括注等版面差异不干扰逐字判定）。"""
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", s)


def split_sections(text):
    """按章节切分口径切章，返回 [(章序, 章题, 章文本)]，空章丢弃。"""
    lines = text.splitlines()
    raw = []
    cur_title, cur = "标题与定位", []
    for ln in lines:
        if HEAD_RE.match(ln.strip()):
            raw.append((cur_title, "\n".join(cur)))
            cur_title = ln.strip().lstrip("#").strip().strip("*").strip()
            cur = [ln]
        else:
            cur.append(ln)
    raw.append((cur_title, "\n".join(cur)))
    return [(i, t, body) for i, (t, body) in enumerate([r for r in raw if r[1].strip()])]


def sentences(body):
    """章内切句：。！？与换行切分，剥掉引用符/加粗符/标题井号后返回非空句。"""
    out = []
    for raw in re.split(r"[。！？\n]", body):
        s = re.sub(r"^[>#\-*+\s]+", "", raw.strip())   # 剥引用符/井号/列表符
        s = s.replace("**", "").strip()                 # 剥加粗符（不动内容）
        if s:
            out.append(s)
    return out


def short_title(t, n=18):
    return t if len(t) <= n else t[:n] + "…"


# ─────────────────────────────────────────────────────────────────────────
# 指标一 · 锚重复
# ─────────────────────────────────────────────────────────────────────────
def collect_anchor_hits(sections):
    """返回 OrderedDict：锚 → [(章序, 章题, 原句, 去空白句长)]，仅收「跨≥2章且解释性落点≥2」的锚。"""
    hits = OrderedDict()
    for idx, title, body in sections:
        for sent in sentences(body):
            zlen = len(norm(sent))
            found = set(a for a in ANCHOR_RE.findall(sent) if a not in ANCHOR_EXCLUDE)
            found |= set(GAP_RE.findall(sent))
            if LIAOBAO in sent:
                found.add(LIAOBAO)
            for m in NATCITE_RE.finditer(sent):
                inner = m.group(1)
                if not ANCHOR_RE.search(inner):
                    found.add("引述·" + re.sub(r"\s+", "", inner)[:14])
            for a in sorted(found):
                hits.setdefault(a, []).append((idx, title, sent, zlen))
    reg = OrderedDict()
    for a, locs in hits.items():
        secs = {l[0] for l in locs}
        n_expl = sum(1 for l in locs if l[3] > EXPLAIN_LEN)
        if len(secs) >= 2 and n_expl >= 2:
            reg[a] = locs
    return reg


# ─────────────────────────────────────────────────────────────────────────
# 指标二 · 近逐字重复
# ─────────────────────────────────────────────────────────────────────────
def lcs_len(a, b):
    """最长公共子串长度（经典滚动 DP）。"""
    if len(a) > len(b):
        a, b = b, a
    prev = [0] * (len(a) + 1)
    best = 0
    for ch in b:
        curr = [0] * (len(a) + 1)
        for j in range(1, len(a) + 1):
            if a[j - 1] == ch:
                curr[j] = prev[j - 1] + 1
                if curr[j] > best:
                    best = curr[j]
        prev = curr
    return best


def collect_near_dup_pairs(sections):
    """跨章句对：Jaccard ≥ JACCARD_TH 或（共享 gram 足量时）LCS ≥ LCS_TH。返回登记句对列表。"""
    items = []
    for idx, title, body in sections:
        for sent in sentences(body):
            z = norm(sent)
            if len(z) >= MIN_SENT:
                g = set(z[i:i + NGRAM] for i in range(len(z) - NGRAM + 1))
                items.append((idx, title, sent, g, z))
    pairs, seen = [], set()
    min_shared = LCS_TH - NGRAM + 1  # 公共子串≥LCS_TH 必致共享 gram≥此数，先以此剪枝
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if a[0] == b[0]:
                continue  # 只比跨章
            inter = a[3] & b[3]
            if not inter:
                continue
            union = a[3] | b[3]
            jac = float(len(inter)) / len(union) if union else 0.0
            verdict = None
            if jac >= JACCARD_TH:
                verdict = "Jaccard {:.2f}".format(jac)
            elif len(inter) >= min_shared:
                L = lcs_len(a[4], b[4])
                if L >= LCS_TH:
                    verdict = "公共子串 {} 字（Jaccard {:.2f}）".format(L, jac)
            if verdict:
                key = (a[4][:24], b[4][:24])
                if key in seen:
                    continue
                seen.add(key)
                pairs.append((a, b, verdict, jac))
    pairs.sort(key=lambda p: -p[3])
    return pairs


# ─────────────────────────────────────────────────────────────────────────
# 指标三 · 高频判断短语
# ─────────────────────────────────────────────────────────────────────────
def collect_phrases(sections, full_text):
    """(a) 引号/书名号短语跨 ≥QUOTE_SPREAD 章；(b) SUB_MIN-SUB_MAX 字重复子串跨 ≥SUB_SPREAD 章、≥SUB_FREQ 次。"""
    # (a) 引号短语：先收集全文所有被包裹短语，再按全文明文回数统计章跨
    quoted = OrderedDict()
    for m in QUOTE_RE.finditer(full_text):
        ph = (m.group(1) or m.group(2)).strip()
        if len(norm(ph)) >= 4 and ph not in quoted:
            quoted[ph] = None
    q_reg = []
    for ph in quoted:
        spread, total = [], 0
        for idx, title, body in sections:
            c = body.count(ph)
            if c:
                spread.append((idx, title, c))
                total += c
        if len(spread) >= QUOTE_SPREAD:
            q_reg.append((ph, total, spread))
    q_reg.sort(key=lambda x: (-len(x[2]), -x[1]))

    # (b) 重复子串：连续词串内取 SUB_MIN..SUB_MAX 字 gram，长→短登记并做去包含
    gram_stats = defaultdict(lambda: [0, set()])
    sec_runs = [(idx, RUN_RE.findall(body)) for idx, _, body in sections]
    for idx, runs_ in sec_runs:
        for run_ in runs_:
            L = len(run_)
            for n in range(SUB_MIN, min(SUB_MAX, L) + 1):
                for i in range(L - n + 1):
                    st = gram_stats[run_[i:i + n]]
                    st[0] += 1
                    st[1].add(idx)
    titles = {idx: t for idx, t, _ in sections}
    sub_reg = []
    for n in range(SUB_MAX, SUB_MIN - 1, -1):
        cands = []
        for g, (tot, secs) in gram_stats.items():
            if len(g) != n or tot < SUB_FREQ or len(secs) < SUB_SPREAD:
                continue
            if len(CJK_RE.findall(g)) < SUB_MIN_CJK:
                continue
            if g[0] in PARTICLE_EDGE or g[-1] in PARTICLE_EDGE:
                continue  # 首末为虚词的截断串（如「的纵向追踪」），其实核由更长/更短串承载
            cands.append((g, tot, secs))
        for g, tot, secs in sorted(cands, key=lambda x: (-x[1], x[0])):
            if any(g in longer for longer, _, _ in sub_reg):
                continue  # 已被更长登记串覆盖
            sub_reg.append((g, tot, secs))
    sub_reg.sort(key=lambda x: (-len(x[2]), -x[1], -len(x[0])))
    return q_reg, sub_reg, titles


# ─────────────────────────────────────────────────────────────────────────
# 登记表输出（markdown）
# ─────────────────────────────────────────────────────────────────────────
def run(path):
    text = open(path, encoding="utf-8").read()
    zchars = len(re.sub(r"\s", "", text))
    sections = split_sections(text)
    anchor_reg = collect_anchor_hits(sections)
    pairs = collect_near_dup_pairs(sections)
    q_reg, sub_reg, _titles = collect_phrases(sections, text)

    # 估算冗余字数（粗估）：
    #   指标一：每锚除「首个解释性落点」外的解释性落点句长（按句去重，跨锚不重复计）；
    #   指标二：每对取较短句长（句子已被指标一计入的不再计）；
    #   指标三：重复子串按 长度×(回数-1) 计。三部分之间仍可能与指标三重叠，故通篇标注粗估。
    counted = set()
    est1 = 0
    for a, locs in anchor_reg.items():
        expl = [l for l in locs if l[3] > EXPLAIN_LEN]
        for l in expl[1:]:
            key = norm(l[2])
            if key not in counted:
                counted.add(key)
                est1 += l[3]
    est2 = 0
    for a, b, _v, _j in pairs:
        shorter = a if len(a[4]) <= len(b[4]) else b
        key = shorter[4]
        if key not in counted:
            counted.add(key)
            est2 += len(key)
    est3 = sum(len(g) * (tot - 1) for g, tot, _s in sub_reg)
    est_total = est1 + est2 + est3

    name = os.path.basename(path)
    n_loc = sum(len(v) for v in anchor_reg.values())
    P = print
    P("# 冗余登记表 · {}".format(name))
    P("")
    P("> 瘦身工序·甲段机械检测产物（redundancy_check.py，纯正则/统计，不调用模型）。")
    P("> 只登记、不裁断：每条合并与否、如何合并，由乙段按《瘦身工序规程_草案.md》操作，丙段复核。")
    P("> 条目清零方式二选一：完成合并，或在本表该条下写明保留理由。")
    P("")
    P("## 汇总统计")
    P("")
    P("| 项 | 值 |")
    P("|---|---|")
    P("| 全文字数（去空白） | {} |".format(zchars))
    P("| 章节数（切分口径见脚本头注） | {} |".format(len(sections)))
    P("| 指标一·锚重复 | {} 锚 / {} 落点 |".format(len(anchor_reg), n_loc))
    P("| 指标二·近逐字重复 | {} 对 |".format(len(pairs)))
    P("| 指标三·高频判断短语 | 引号短语 {} 条 / 重复子串 {} 条 |".format(len(q_reg), len(sub_reg)))
    P("| 估算冗余字数（粗估，三指标间有重叠，不可当删减额） | 约 {} 字（指标一 {} ＋ 指标二 {} ＋ 指标三 {}） |".format(
        est_total, est1, est2, est3))
    P("")

    P("## 指标一 · 锚重复（同锚多章带解释性文字）")
    P("")
    P("口径：同一来源锚跨 ≥2 章出现，且 >{}字解释性落点 ≥2 处。首个解释性落点通常即「首引全述」".format(EXPLAIN_LEN))
    P("保留位，其余落点为合并候选（压成指代）；何处承重最好由乙段裁量，脚本不指定。")
    P("")
    if anchor_reg:
        for a, locs in sorted(anchor_reg.items(), key=lambda kv: (-len({l[0] for l in kv[1]}), -len(kv[1]))):
            secs = {l[0] for l in locs}
            n_expl = sum(1 for l in locs if l[3] > EXPLAIN_LEN)
            P("### 锚 {} —— 跨 {} 章 · {} 处落点（解释性 {} 处）".format(a, len(secs), len(locs), n_expl))
            P("")
            for k, (idx, title, sent, zlen) in enumerate(locs, 1):
                tag = "解释性" if zlen > EXPLAIN_LEN else "短引"
                P("{}. 【{}】（{}，{}字）{}".format(k, short_title(title), tag, zlen, sent))
            P("")
    else:
        P("（本指标无登记。）")
        P("")

    P("## 指标二 · 近逐字重复（跨章句对）")
    P("")
    P("口径：跨章句对，字符 {}-gram Jaccard ≥ {}，或最长公共子串 ≥ {} 字（比较前已剥离标点/引号/空白）。".format(
        NGRAM, JACCARD_TH, LCS_TH))
    P("")
    if pairs:
        for k, (a, b, verdict, _j) in enumerate(pairs, 1):
            P("### 对 {} ｜ 判据：{}".format(k, verdict))
            P("")
            P("- 甲【{}】{}".format(short_title(a[1]), a[2]))
            P("- 乙【{}】{}".format(short_title(b[1]), b[2]))
            P("")
    else:
        P("（本指标无登记。）")
        P("")

    P("## 指标三 · 高频判断短语")
    P("")
    P("### (a) 引号/书名号短语，跨 ≥{} 章".format(QUOTE_SPREAD))
    P("")
    if q_reg:
        for ph, total, spread in q_reg:
            where = "、".join("{}（×{}）".format(short_title(t, 12), c) for _i, t, c in spread)
            P("- 「{}」 全文 ×{} · 跨 {} 章：{}".format(ph, total, len(spread), where))
    else:
        P("（无登记。）")
    P("")
    P("### (b) 重复子串（{}-{} 字，跨 ≥{} 章、全文 ≥{} 次，最长化去包含）".format(
        SUB_MIN, SUB_MAX, SUB_SPREAD, SUB_FREQ))
    P("")
    if sub_reg:
        for g, tot, secs in sub_reg:
            names = "、".join(short_title(_titles_lookup(sections, i), 10) for i in sorted(secs))
            P("- 「{}」 全文 ×{} · 跨 {} 章：{}".format(g, tot, len(secs), names))
    else:
        P("（无登记。）")
    P("")
    P("---")
    P("")
    P("以上为机械登记结果。合并后请复跑本脚本：三指标条数与估算冗余字数应下降；")
    P("未降项如实报告，交人裁量，不许为压读数硬删内容（与清稿规程守恒约束同款纪律）。")


def _titles_lookup(sections, idx):
    for i, t, _b in sections:
        if i == idx:
            return t
    return "?"


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("用法：python3 redundancy_check.py <成稿markdown文件>\n")
        sys.exit(2)
    target = sys.argv[1]
    if not os.path.isfile(target):
        sys.stderr.write("找不到文件：{}\n".format(target))
        sys.exit(2)
    run(target)


if __name__ == "__main__":
    main()
