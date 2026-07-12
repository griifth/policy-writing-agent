# -*- coding: utf-8 -*-
"""
P1 文笔微观层面定量对比：人类专家内参 vs AI 生成报告
输出:
  P1_metrics_by_doc.csv      每篇文档的全部指标
  P1_group_summary.csv       两组均值对比
  P1_number_sentences_sample.csv  含数字句抽样(供人工判读“数字是否嵌在机制句里”)
  P1_sentence_lengths.csv    每篇句长明细(供画分布/复核)
"""
import re, csv, statistics, random, os

BASE_H = "/Users/hujingkai/Downloads/Kimi_Agent_OCR转MD文本缺失/md"
BASE_A = "/Users/hujingkai/Documents/New project/example1/records/ai_judge_human_study_2026-07-07/extracted_samples"
BASE_R = "/Users/hujingkai/Documents/New project/example1/runs"
OUT = "/Users/hujingkai/Documents/New project/example1/records/ai_judge_human_study_2026-07-08_deep/agent_notes"

DOCS = [
    # (组, 简名, 路径)
    ("human", "E_中美AI人才竞争", f"{BASE_H}/中美AI人才竞争及应对策略.md"),
    ("human", "C_人工智能+教育国际比较", f"{BASE_H}/人工智能+教育国际比较报告.md"),
    ("human", "H_终身教育趋势2016-2020", f"{BASE_H}/2016-2020年国际终身教育改革发展趋势.md"),
    ("human", "H_校服治理国际比较", f"{BASE_H}/中小学校服治理国际比较.md"),
    ("human", "H_超常儿童国家战略", f"{BASE_H}/主要国家将超常儿童培养上升为国家战略.md"),
    ("human", "H_学生饮用奶政策", f"{BASE_H}/国外学生饮用奶相关政策及实施路径.md"),
    ("human", "H_警惕美竞争法案", f"{BASE_H}/警惕美竞争法案对我教育战略带来的重大风险.md"),
    ("human", "H_课后服务双减", f"{BASE_H}/从国际经验中优化课后服务推动双减政策落地.md"),
    ("ai", "A_AI教育政策比较(盲测A)", f"{BASE_A}/文章A人工智能+教育国际政策比较报告_.md"),
    ("ai", "B_美国AI人才战略(盲测B)", f"{BASE_A}/文章B美国AI人才战略布局及我国应对策略.md"),
    ("ai", "D_终身教育研判(盲测D)", f"{BASE_A}/文章D国际终身教育趋势研判报告.md"),
    ("ai", "R_run0626-152506", f"{BASE_R}/run-20260626-152506-2528b552/final_report_reviewed.md"),
    ("ai", "R_run0706-095808", f"{BASE_R}/run-20260706-095808-7906d24e/final_report_reviewed.md"),
    ("ai", "R_run0706-193854", f"{BASE_R}/run-20260706-193854-4dab90d1/final_report_reviewed.md"),
]

HAN = re.compile(r'[一-鿿]')

def clean(text):
    """去掉 markdown 结构噪声, 保留正文."""
    lines = []
    for ln in text.split('\n'):
        s = ln.strip()
        if not s: lines.append(''); continue
        if s.startswith('FILE_NAME'): continue
        if s.startswith('[^'): continue            # 脚注定义
        if s.startswith('|'): continue             # 表格
        if re.match(r'^-{3,}$', s): continue
        s = re.sub(r'^#{1,6}\s*', '', s)
        s = re.sub(r'^>\s*', '', s)
        s = s.replace('**', '')
        s = re.sub(r'\[\^\d+\]', '', s)            # 脚注引用
        s = re.sub(r'https?://\S+', '', s)
        lines.append(s)
    return '\n'.join(lines)

def paragraphs(text):
    paras, cur = [], []
    for ln in text.split('\n'):
        if ln.strip(): cur.append(ln.strip())
        else:
            if cur: paras.append(''.join(cur)); cur=[]
    if cur: paras.append(''.join(cur))
    # 只保留含≥10个汉字的段(去掉孤立标题行)
    return [p for p in paras if len(HAN.findall(p)) >= 10]

def sentences(text):
    """按 。！？分句, 句长=汉字数(近似)"""
    body = re.sub(r'\n+', '', text)
    parts = re.split(r'[。！？]', body)
    sents = []
    for p in parts:
        n = len(HAN.findall(p))
        if n >= 3:
            sents.append((p, n))
    return sents

# ---------- 词表 ----------
META_ANNOUNCE = [  # 显性元话语: 宣告"我在总结/我有判断/我在组织结构"
    '总体来看','总体而言','整体来看','整体而言','从整体','综上','综观','纵观',
    '可概括为','可归纳为','可归并为','大致可分为','可分为','呈现出','这表明','这意味着',
    '由此可见','可见，','可见,','换言之','概言之','本文','本报告','本章','本节',
    '值得注意的是','值得关注的是','更值得注意','需要注意的是','需要指出','必须指出',
    '不难发现','研究发现表明','其核心特征是','核心特征是','其共同逻辑','共同逻辑是',
    '共性在于','本质上在于','比较而言','相较而言','综合来看','据此','基于上述',
]
META_LINK = [      # 衔接/对举
    '与此同时','一方面','另一方面','此外','同时，','同时,','进一步','在此基础上',
    '不仅如此','更为重要的是','更重要的是','尤为','特别是','尤其是',
]
TYPE_NAMING = [    # 类型化命名领起(正则)
    r'第[一二三四五六七八九十]类是', r'第[一二三四五六七八九十]种是',
    r'第[一二三四五六七八九十]条主线', r'[三四五六]大[一-鿿]{2,6}',
    r'呈现[出]?[一二三四五六七八九十]{1,2}[个条种类]', r'分为[一二三四五六七八九十]{1,2}[个条种类]',
    r'形成[一二三四五六七八九十]{1,2}[条类种]', r'[三四五六]类[一-鿿]{0,4}模式',
    r'[三四五六]种[一-鿿]{0,4}(类型|模式|路径|机制|取向)',
]
COINED_TYPE = re.compile(r'[一-鿿]{2,7}型(?=[、。，；：""“”)）]|$)')
TYPE_EXCLUDE = re.compile(r'(典型|大型|小型|新型|转型|模型|类型|微型|中型|成型|定型|字型|巨型|重型|轻型|智能型$)')
CHENGYU = [  # 政策文本常见四字格(两组同一把尺)
    '一脉相承','一举奠定','一以贯之','雷霆手段','绣花功夫','精耕细作','喜闻乐见','千方百计',
    '野心勃勃','迫在眉睫','瞬息万变','源源不断','急起直追','因材施教','融合贯通','顺畅衔接',
    '起起落落','格外珍视','高度重视','统筹谋划','科学设计','多措并举','齐头并进','协同共生',
    '互为支撑','另起炉灶','自说自话','宁缺毋滥','一步之遥','暗流涌动','现出原形','合二为一',
    '各有侧重','上下联动','多元投入','双轮驱动','精准施策','分类施策','稳慎有序','先行先试',
    '不言而喻','不容忽视','日益凸显','日益严峻','日益激烈','不断加剧','层出不穷','方兴未艾',
    '深谋远虑','未雨绸缪','防患未然','厚积薄发','行稳致远','久久为功','驰而不息','善作善成',
    '全力以赴','蹄疾步稳','纲举目张','提纲挈领','�female而合','不谋而合','殊途同归','异曲同工',
    '一票否决','一锤定音','立竿见影','水到渠成','顺势而为','乘势而上','借势发力','蓄势待发',
]
CHENGYU = [c for c in CHENGYU if 'female' not in c]

def count_terms(text, terms):
    return sum(text.count(t) for t in terms)

def count_regex(text, patterns):
    return sum(len(re.findall(p, text)) for p in patterns)

ENUM_HEAD = re.compile(r'^(一是|二是|三是|四是|五是|六是|七是|第[一二三四五六七八九十]+[，、,]|（[一二三四五六七八九十]+）|\([一二三四五六七八九十]+\)|[一二三四五六七八九十]+、|\d+[\.、])')
NUM_PAT = re.compile(r'\d[\d,\.]*\s*[%％]?|[一二三四五六七八九十百千]+分之[一二三四五六七八九十]+')
YEAR_PAT = re.compile(r'(19|20)\d{2}')
CHAIN_PAT = re.compile(r'[一-鿿]{1,8}(?:—{1,2}|-{2,3}|→|—)[一-鿿]{1,8}(?:(?:—{1,2}|-{2,3}|→|—)[一-鿿]{1,8})+')
DOUBLET4 = re.compile(r'[一-鿿]{4}、[一-鿿]{4}')

rows, sent_rows, num_samples = [], [], []
random.seed(42)

for group, name, path in DOCS:
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    body = clean(raw)
    paras = paragraphs(body)
    body_join = '\n'.join(paras)          # 只统计正文段
    sents = sentences(body_join)
    hanzi = len(HAN.findall(body_join))
    k = hanzi / 1000.0

    lens = [n for _, n in sents]
    mean_len = statistics.mean(lens)
    std_len = statistics.pstdev(lens)
    cv = std_len / mean_len
    short = sum(1 for n in lens if n < 15) / len(lens)
    long40 = sum(1 for n in lens if n > 60) / len(lens)

    for _, n in sents:
        sent_rows.append([group, name, n])

    # 元话语
    m_ann = count_terms(body_join, META_ANNOUNCE)
    m_link = count_terms(body_join, META_LINK)
    # 类型化命名
    t_lead = count_regex(body_join, TYPE_NAMING)
    coined = [m.group(0) for m in COINED_TYPE.finditer(body_join) if not TYPE_EXCLUDE.search(m.group(0))]
    # 四字格
    cy = count_terms(body_join, CHENGYU)
    dbl = len(DOUBLET4.findall(body_join))
    # 数字
    nums = NUM_PAT.findall(body_join)
    # 链式公式/箭头
    chains = CHAIN_PAT.findall(body_join)
    # 段落
    p_lens = [len(HAN.findall(p)) for p in paras]
    enum_paras = sum(1 for p in paras if ENUM_HEAD.match(p))
    # 段首元话语 vs 段首事实
    p_meta0 = 0; p_fact0 = 0
    for p in paras:
        head = p[:40]
        if any(t in head for t in META_ANNOUNCE+META_LINK) or any(re.search(pt, head) for pt in TYPE_NAMING):
            p_meta0 += 1
        if YEAR_PAT.search(head) or re.search(r'\d', head):
            p_fact0 += 1

    # 抽样含数字句
    numsents = [s for s, n in sents if NUM_PAT.search(s) and n > 10]
    for s in random.sample(numsents, min(6, len(numsents))):
        num_samples.append([group, name, s[:180]])

    rows.append({
        '组': group, '文档': name, '汉字数': hanzi, '句数': len(sents),
        '句长均值': round(mean_len,1), '句长标准差': round(std_len,1),
        '句长变异系数CV': round(cv,3), '最长句': max(lens),
        '短句<15字占比%': round(short*100,1), '长句>60字占比%': round(long40*100,1),
        '元话语宣告/千字': round(m_ann/k,2), '衔接对举/千字': round(m_link/k,2),
        '类型命名领起/千字': round(t_lead/k,2), '自造X型词次数': len(coined),
        '自造X型词/千字': round(len(coined)/k,2),
        '四字格(词表)/千字': round(cy/k,2), '四字并列对/千字': round(dbl/k,2),
        '数字/千字': round(len(nums)/k,1),
        '链式公式(A—B—C)次数': len(chains),
        '段数': len(paras), '段均汉字': round(statistics.mean(p_lens),0),
        '编号领起段占比%': round(enum_paras/len(paras)*100,1),
        '段首显性元话语占比%': round(p_meta0/len(paras)*100,1),
        '段首含数字/年份占比%': round(p_fact0/len(paras)*100,1),
        '自造X型词样例': '|'.join(sorted(set(coined))[:12]),
        '链式公式样例': '|'.join(chains[:4]),
    })

# 写每篇明细
keys = list(rows[0].keys())
with open(f'{OUT}/P1_metrics_by_doc.csv','w',newline='',encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)

# 组均值
numeric = [k for k in keys if k not in ('组','文档','自造X型词样例','链式公式样例')]
with open(f'{OUT}/P1_group_summary.csv','w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['指标','human均值','ai均值','ai/human'])
    for kk in numeric:
        hv = statistics.mean(r[kk] for r in rows if r['组']=='human')
        av = statistics.mean(r[kk] for r in rows if r['组']=='ai')
        ratio = round(av/hv,2) if hv else ''
        w.writerow([kk, round(hv,2), round(av,2), ratio])

with open(f'{OUT}/P1_number_sentences_sample.csv','w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['组','文档','含数字句(截断180字)']); w.writerows(num_samples)

with open(f'{OUT}/P1_sentence_lengths.csv','w',newline='',encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['组','文档','句长汉字数']); w.writerows(sent_rows)

# 终端打印组对比
print(f"{'指标':<22}{'human':>10}{'ai':>10}{'ai/h':>8}")
for kk in numeric:
    hv = statistics.mean(r[kk] for r in rows if r['组']=='human')
    av = statistics.mean(r[kk] for r in rows if r['组']=='ai')
    print(f"{kk:<22}{hv:>10.2f}{av:>10.2f}{(av/hv if hv else 0):>8.2f}")
print('\n--- 自造X型词样例 ---')
for r in rows:
    if r['自造X型词样例']:
        print(r['组'], r['文档'], '=>', r['自造X型词样例'])
print('\n--- 链式公式样例 ---')
for r in rows:
    if r['链式公式样例']:
        print(r['组'], r['文档'], '=>', r['链式公式样例'])
