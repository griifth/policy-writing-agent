# -*- coding: utf-8 -*-
"""
盲测集 v2 归一化流水线。
输入：17 篇源稿（6 人稿 + 6 AI 稿 + 5 设计集）
输出：blind_v2/full/T01..T12.md, D01..D05.md + _label_map_DO_NOT_READ.txt
原则：只消除格式指纹，正文措辞一字不改（内容完整性由 canon 比对硬校验）。
"""
import re, os, hashlib, sys

HUMAN_DIR = "/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md"
REPO = "/Users/hujingkai/Documents/New project/example1"
OUT = os.path.join(REPO, "records/ai_judge_human_study_2026-07-08_deep/blind_v2")

# ---------------------------------------------------------------- sources
TEST_SOURCES = [
    # (tag, group, path)
    ("H1", "人", HUMAN_DIR + "/美英德澳培养与聘任体育教师的做法和特点.md"),
    ("H2", "人", HUMAN_DIR + "/国外终身教育改革动向和趋势.md"),
    ("H3", "人", HUMAN_DIR + "/国外生成式人工智能教育应用态度、策略和举措.md"),
    ("H4", "人", HUMAN_DIR + "/警惕美竞争法案对我教育战略带来的重大风险.md"),
    ("H5", "人", HUMAN_DIR + "/世界教育数字化发展态势分析.md"),
    ("H6", "人", HUMAN_DIR + "/从国际经验中优化课后服务推动双减政策落地.md"),
    ("A1", "AI", REPO + "/runs/run-20260706-095808-7906d24e/final_report_reviewed_教科院修订版.md"),
    ("A2", "AI", REPO + "/strategic_response_workflow/runs/run-20260629-115549-ed10468f/final_article_reviewed.md"),
    ("A3", "AI", REPO + "/strategic_response_workflow/runs/run-20260626-131122-452a7eaa/final_article_reviewed.md"),
    # 58d306dd 尾段截断，按任务指示改用 20260625-210305 同主题最终版
    ("A4", "AI", REPO + "/strategic_response_workflow/runs/run-20260625-210305-06e3ea92/final_article_reviewed.md"),
    ("A5", "AI", REPO + "/strategic_response_workflow/runs/run-20260623-151123-50592bc4/final_article_reviewed.md"),
    ("A6", "AI", REPO + "/strategic_response_workflow/runs/run-20260626-111233-dfa77f3b/final_article_reviewed.md"),
]
DESIGN_SOURCES = [
    ("D01", REPO + "/records/ai_judge_human_study_2026-07-07/blind_sets/S01.md"),
    ("D02", REPO + "/records/ai_judge_human_study_2026-07-07/blind_sets/S02.md"),
    ("D03", REPO + "/records/ai_judge_human_study_2026-07-07/blind_sets/S03.md"),
    ("D04", REPO + "/records/ai_judge_human_study_2026-07-07/blind_sets/S04.md"),
    ("D05", REPO + "/records/ai_judge_human_study_2026-07-07/blind_sets/S05.md"),
]

# A2 评审版首两行标题在评审步骤中丢失，从同 run 的 final_article.md 恢复（同一产物链，非内容改动）
A2_TITLE = "主要国家人工智能教育政策的模式、成因与成效——及对我国的分层借鉴建议"

HEADING_PAT = re.compile(r"^(?:[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）)")

def is_heading(line: str) -> bool:
    s = line.strip()
    return bool(HEADING_PAT.match(s)) and len(s) <= 80 and not s.endswith(("。", "？", "！"))

def delete_balanced_note(text: str, opener: str) -> tuple[str, list[str]]:
    """删除以 opener 开头、圆括号配平的括注（如 （编者注：…）），返回(新文本, 删除清单)."""
    removed = []
    out = text
    while True:
        i = out.find(opener)
        if i < 0:
            break
        depth = 0
        j = i
        while j < len(out):
            if out[j] == "（":
                depth += 1
            elif out[j] == "）":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            raise RuntimeError(f"unbalanced note at {i}")
        removed.append(out[i:j+1])
        out = out[:i] + out[j+1:]
    return out, removed

def smart_join(lines):
    """块内多行合并为一段：ASCII/ASCII 边界补空格，其余直接拼接。"""
    buf = lines[0].strip()
    for ln in lines[1:]:
        ln = ln.strip()
        if not ln:
            continue
        a, b = buf[-1], ln[0]
        if a.isascii() and b.isascii():
            buf += " " + ln
        else:
            buf += ln
    return buf

def normalize(tag: str, text: str, log: list) -> str:
    # --- 0 行尾/特殊空白
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("﻿", "")

    # --- 每篇特例（均为格式/装置层，非正文措辞）
    if tag == "H2":
        n0 = len(text)
        text = re.sub(r"^FILE_NAME:.*\n-{3,}\n+", "", text)
        assert len(text) < n0
        log.append("删 FILE_NAME 元信息行 + 顶部 --- 分隔线")
    if tag == "A1":
        n0 = len(text)
        text = re.sub(r"\n人工智能\+教育国际比较研究课题组\n", "\n", text)
        assert len(text) < n0
        log.append("删虚构课题组署名行 1 处")
        text, removed = delete_balanced_note(text, "（编者注")
        assert len(removed) == 4, removed
        log.append(f"删（编者注：…）括注 {len(removed)} 处")
    if tag == "H1":
        n0 = len(text)
        text = re.sub(r"^编者按：[^\n]*\n+", "", text, flags=re.M)
        assert len(text) < n0
        log.append("删编者按段落 1 段（与 AI 组删编者注对称处理）")
    if tag == "A2":
        text = A2_TITLE + "\n\n" + text
        log.append("补回同 run final_article.md 首两行标题（评审步丢失），合并为单行")
    if tag == "A4":
        n_cit = len(re.findall(r"\[\d{1,3}\]", text))
        text = re.sub(r"\[\d{1,3}\]", "", text)
        log.append(f"删正文素材编号引用 [n] 共 {n_cit} 处")
    if tag == "A6":
        cits = re.findall(r"〔[^〕\n]*·[^〕\n]*〕", text)
        text = re.sub(r"〔[^〕\n]*·[^〕\n]*〕", "", text)
        log.append(f"删〔来源·年份〕素材标签引用 {len(cits)} 处")
        # 校验：不误伤公文文号（文号形如 教师〔2025〕1号，不含·）

    # --- 1 脚注（标记 + 定义块）
    n_defs = len(re.findall(r"^\[\^\d+\]:", text, re.M))
    if n_defs:
        text = re.sub(r"^\[\^\d+\]:.*(?:\n(?![\[\n]).*)*\n?", "", text, flags=re.M)
        log.append(f"删文末脚注定义块 {n_defs} 条")
    n_marks = len(re.findall(r"\[\^\d+\]", text))
    if n_marks:
        text = re.sub(r"\[\^\d+\]", "", text)
        log.append(f"删正文脚注标记 {n_marks} 处")

    # --- 2 markdown 结构记号
    n_hr = len(re.findall(r"^\s*-{3,}\s*$", text, re.M))
    if n_hr:
        text = re.sub(r"^\s*-{3,}\s*$\n?", "", text, flags=re.M)
        log.append(f"删 --- 分隔线 {n_hr} 处")
    n_h = len(re.findall(r"^#{1,6}\s*", text, re.M))
    if n_h:
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
        log.append(f"去 # 标题记号 {n_h} 处（标题文字保留）")
    n_bq = len(re.findall(r"^>\s*", text, re.M))
    if n_bq:
        text = re.sub(r"^>\s*", "", text, flags=re.M)
        log.append(f"去 > 引用块记号 {n_bq} 处")
    n_bold = text.count("**") // 2
    if n_bold:
        text = text.replace("**", "")
        log.append(f"去 **加粗** 记号 {n_bold} 对（文字保留）")
    n_esc = len(re.findall(r"\\([\[\]\"'*_#>().!—-])", text))
    if n_esc:
        text = re.sub(r"\\([\[\]\"'*_#>().!—-])", r"\1", text)
        log.append(f"去 pandoc 反斜杠转义 {n_esc} 处")

    # --- 3 引号统一为直引号
    n_q = len(re.findall(r"[“”‘’]", text))
    if n_q:
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        log.append(f"弯引号→直引号 {n_q} 处")

    # --- 4 破折号制式（pandoc 把 — 写成 ---、—— 写成 ------）
    n_d6 = len(re.findall(r"(?<!-)-{6}(?!-)", text))
    if n_d6:
        text = re.sub(r"(?<!-)-{6}(?!-)", "——", text)
        log.append(f"------ → —— {n_d6} 处")
    n_d3 = len(re.findall(r"(?<!-)-{3}(?!-)", text))
    if n_d3:
        text = re.sub(r"(?<!-)-{3}(?!-)", "—", text)
        log.append(f"--- → — {n_d3} 处")

    # --- 5 全半角标点（仅 CJK 邻接处；数字与英文保持半角）
    CJK = "一-鿿"
    for pat, rep, name in [
        (rf"(?<=[{CJK}]),(?=[{CJK}])", "，", "半角逗号→，"),
        (rf"(?<=[{CJK}]);(?=[{CJK}])", "；", "半角分号→；"),
        (rf"(?<=[{CJK}])\.(?=[{CJK}])", "。", "半角句号→。"),
        (rf"\)(?=[{CJK}])", None, None),  # 占位：见下方专项
    ][:3]:
        n = len(re.findall(pat, text))
        if n:
            text = re.sub(pat, rep, text)
            log.append(f"{name} {n} 处")
    # --- 6 段落重排：块内合并（消 pandoc 硬折行），段间单空行，无首行缩进
    blocks_raw = re.split(r"\n\s*\n+", text)
    blocks = []
    for blk in blocks_raw:
        lines = [l.strip() for l in blk.split("\n") if l.strip()]
        if not lines:
            continue
        # 多行块：若中途出现结构性小标题行则在其前后切块（防串段）
        cur = []
        for l in lines:
            if is_heading(l) and cur:
                blocks.append(smart_join(cur))
                cur = [l]
            elif is_heading(l):
                blocks.append(l)
            else:
                cur.append(l)
        if cur:
            blocks.append(smart_join(cur) if not (len(cur) == 1 and is_heading(cur[0])) else cur[0])
    n_join = sum(1 for b in blocks_raw if len([l for l in b.split("\n") if l.strip()]) > 1)
    if n_join:
        log.append(f"合并块内硬折行/引导句独行 {n_join} 个块")
    text = "\n\n".join(blocks) + "\n"

    # --- 7 合并折行后再修：全角（ 开头、半角 ) 收尾的括号对 → 补全角
    n_par = 0
    def fix_paren(m):
        nonlocal n_par
        n_par += 1
        return "（" + m.group(1) + "）"
    text2 = re.sub(rf"（([^（）()\n]*)\)(?=[{CJK}])", fix_paren, text)
    if n_par:
        text = text2
        log.append(f"半角 ) 补为全角 ） {n_par} 处（与全角（ 配对）")

    return text

# ---------------------------------------------------------------- 内容完整性硬校验
def canon(s: str) -> str:
    """归一化到可比对的字符序列：抹掉所有本流水线允许触碰的格式差异。"""
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = re.sub(r"(?<!-)-{6}(?!-)", "——", s)
    s = re.sub(r"(?<!-)-{3}(?!-)", "—", s)
    s = re.sub(r"^\s*-{3,}\s*$", "", s, flags=re.M)
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.M)
    s = re.sub(r"^>\s*", "", s, flags=re.M)
    s = s.replace("**", "")
    s = re.sub(r"\\([\[\]\"'*_#>().!—-])", r"\1", s)
    s = s.replace("，", ",").replace("；", ";").replace("。", ".").replace("）", ")")
    s = re.sub(r"\s+", "", s)
    return s

def source_after_deletions(tag: str, text: str) -> str:
    """对源文本施加与 normalize 相同的删除项（不做格式映射），供 canon 比对。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("﻿", "")
    if tag == "H2":
        text = re.sub(r"^FILE_NAME:.*\n-{3,}\n+", "", text)
    if tag == "A1":
        text = re.sub(r"\n人工智能\+教育国际比较研究课题组\n", "\n", text)
        text, _ = delete_balanced_note(text, "（编者注")
    if tag == "H1":
        text = re.sub(r"^编者按：[^\n]*\n+", "", text, flags=re.M)
    if tag == "A2":
        text = A2_TITLE + "\n\n" + text
    if tag == "A4":
        text = re.sub(r"\[\d{1,3}\]", "", text)
    if tag == "A6":
        text = re.sub(r"〔[^〕\n]*·[^〕\n]*〕", "", text)
    text = re.sub(r"^\[\^\d+\]:.*(?:\n(?![\[\n]).*)*\n?", "", text, flags=re.M)
    text = re.sub(r"\[\^\d+\]", "", text)
    return text

# ---------------------------------------------------------------- run
def main():
    os.makedirs(os.path.join(OUT, "full"), exist_ok=True)
    results = {}   # tag -> (group, path, normalized, log)
    for tag, group, path in TEST_SOURCES:
        log = []
        src = open(path, encoding="utf-8").read()
        norm = normalize(tag, src, log)
        c_src, c_out = canon(source_after_deletions(tag, src)), canon(norm)
        if c_src != c_out:
            # 定位第一处差异
            for k in range(min(len(c_src), len(c_out))):
                if c_src[k] != c_out[k]:
                    print(f"[FATAL] {tag} canon mismatch at {k}: src={c_src[k-30:k+30]!r} out={c_out[k-30:k+30]!r}")
                    sys.exit(1)
            print(f"[FATAL] {tag} canon length mismatch {len(c_src)} vs {len(c_out)}")
            print("tail src:", c_src[-80:]); print("tail out:", c_out[-80:])
            sys.exit(1)
        # 结构校验：小标题行数不因合并/切块而增减
        def count_headings(s):
            return sum(1 for l in s.split("\n") if is_heading(l.strip()) and l.strip())
        h_src = sum(1 for l in source_after_deletions(tag, src).split("\n")
                    if is_heading(re.sub(r"^\s*(?:#{1,6}\s*|>\s*)?", "", l).replace("**", "").strip())
                    and re.sub(r"^\s*(?:#{1,6}\s*|>\s*)?", "", l).replace("**", "").strip())
        h_out = count_headings(norm)
        if h_src != h_out:
            print(f"[FATAL] {tag} heading count changed: {h_src} -> {h_out}"); sys.exit(1)
        results[tag] = (group, path, norm, log)
        print(f"[ok] {tag} {len(norm)} chars, headings={h_out} | " + "；".join(log))

    designs = {}
    for dtag, path in DESIGN_SOURCES:
        log = []
        src = open(path, encoding="utf-8").read()
        norm = normalize(dtag, src, log)
        if canon(source_after_deletions(dtag, src)) != canon(norm):
            print(f"[FATAL] {dtag} canon mismatch"); sys.exit(1)
        h_src = sum(1 for l in source_after_deletions(dtag, src).split("\n")
                    if is_heading(re.sub(r"^\s*(?:#{1,6}\s*|>\s*)?", "", l).replace("**", "").strip())
                    and re.sub(r"^\s*(?:#{1,6}\s*|>\s*)?", "", l).replace("**", "").strip())
        h_out = sum(1 for l in norm.split("\n") if l.strip() and is_heading(l.strip()))
        if h_src != h_out:
            print(f"[FATAL] {dtag} heading count changed: {h_src} -> {h_out}"); sys.exit(1)
        designs[dtag] = (path, norm, log)
        print(f"[ok] {dtag} {len(norm)} chars, headings={h_out} | " + "；".join(log))

    # --- 洗牌：md5(标题+盐) 升序 → T01..T12
    # 盐从 blind_v2_0 起递增，取首个"同组连排 ≤2"的盐（确定性；调度者要求两组必须交错）
    def shuffle_with(salt):
        o = sorted(results.keys(),
                   key=lambda t: hashlib.md5((results[t][2].split("\n")[0] + salt).encode()).hexdigest())
        pat = "".join("H" if results[t][0] == "人" else "A" for t in o)
        return o, pat
    def max_run(pat):
        best = cur = 1
        for i in range(1, len(pat)):
            cur = cur + 1 if pat[i] == pat[i-1] else 1
            best = max(best, cur)
        return best
    n_salt = 0
    while True:
        SALT = f"blind_v2_{n_salt}"
        order, pattern = shuffle_with(SALT)
        if max_run(pattern) <= 2:
            break
        n_salt += 1
    print("shuffle pattern:", pattern, "(salt:", SALT + ")")

    lines_map = []
    for i, tag in enumerate(order, 1):
        group, path, norm, log = results[tag]
        tname = f"T{i:02d}"
        open(os.path.join(OUT, "full", f"{tname}.md"), "w", encoding="utf-8").write(norm)
        lines_map.append(f"{tname}\t{path}\t{group}")
        results[tag] = (group, path, norm, log, tname)
    for dtag, (path, norm, log) in designs.items():
        open(os.path.join(OUT, "full", f"{dtag}.md"), "w", encoding="utf-8").write(norm)

    with open(os.path.join(OUT, "_label_map_DO_NOT_READ.txt"), "w", encoding="utf-8") as f:
        f.write("# 盲测集 v2 测试集映射（评委与调度者在盲测结束前不得读取）\n")
        f.write(f"# 洗牌规则：md5(归一化标题 + 盐) 十六进制升序 → T01..T12；盐自 blind_v2_0 递增，取首个同组连排≤2 的盐（本次盐：{SALT}，两组交错模式：{pattern}）\n")
        f.write("# T编号\t源文件路径\t组别\n")
        f.write("\n".join(lines_map) + "\n")
        f.write("# 设计集：D01..D05 = ai_judge_human_study_2026-07-07/blind_sets/S01..S05（编号原样对应）\n")

    # 处理日志落盘（供 build report 汇编；按源文件名 keyed，不含 T 编号）
    import json
    plog = {}
    for tag in results:
        group, path, norm, log, tname = results[tag]
        plog[os.path.basename(os.path.dirname(path)) + "/" + os.path.basename(path)] = {
            "chars": len(norm), "ops": log}
    for dtag in designs:
        path, norm, log = designs[dtag]
        plog[dtag + "=" + os.path.basename(path)] = {"chars": len(norm), "ops": log}
    open(os.path.join(OUT, "_proc_log.json"), "w", encoding="utf-8").write(
        json.dumps(plog, ensure_ascii=False, indent=1))
    print("done")

if __name__ == "__main__":
    main()
