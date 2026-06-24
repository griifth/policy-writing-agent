"""建议核查与延展 · 硬性判定工具（独立增强工具，不进主工作流）。

职责分工：
  - 联网搜索 / 下载政策原文 / 延展研究 / 发散 —— 由 skill 派生的 agent 用 WebSearch/WebFetch 做（需判断）。
  - 目录脚手架 + 硬性判定（舍弃/延展/保留/新增）—— 本工具做（确定性，按规则，不靠模型心情）。

用法：
  python3 tools/suggestion_audit_extend.py scaffold <run_dir>
  python3 tools/suggestion_audit_extend.py decide   <findings.json> [--out <report.md>]

findings.json 由 agent 在联网核查后产出（schema 见 --help / 文末注释 / SKILL.md）。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# 缺口六分类（来源：codex 审核第1点）——只要命中任一，就不该舍弃，应延展
GAP_TYPES = {"覆盖", "执行", "评价", "配套", "区域均衡", "制度化"}

# Web 来源分级（codex 第2点）：tier 越小越权威
#   1 国务院/教育部/部委官网、地方政府官网   2 官方政策数据库
#   3 高校/研究机构                          4 媒体报道（仅作线索，不能单独支撑高置信先例判定）
VALID_TIERS = {1, 2, 3, 4}
STATES = {"full_implemented", "piloted", "proposed_not_landed", "not_found"}
PRECEDENT_STATES = {"full_implemented", "piloted", "proposed_not_landed"}
FORBIDDEN_NOVELTY_CLAIMS = ["首创", "国内尚无", "国内空白", "全国首个", "国内首个", "尚属空白"]


def _best_tier(evidence: list[dict]) -> int:
    tiers = [e.get("source_tier", 4) for e in evidence if e.get("source_tier") in VALID_TIERS]
    return min(tiers) if tiers else 4


def decide_one(s: dict) -> dict:
    """对一条原建议套硬决策表。返回 {verdict, confidence, flags}。"""
    state = s.get("state")
    conf = s.get("confidence", "medium")
    gaps = [g for g in s.get("gaps", []) if g in GAP_TYPES]
    evidence = s.get("evidence", []) or []
    flags: list[str] = []

    if state not in STATES:
        return {"verdict": "待核", "confidence": conf, "flags": [f"state 非法/缺失: {state!r}"]}

    # 先例判定必须有证据 URL（防臆测）
    if state in PRECEDENT_STATES and not evidence:
        return {"verdict": "待核", "confidence": "low",
                "flags": ["判'已实施/试点/提出'却无证据URL → 先例不成立，降为待核"]}

    # 来源分级：已实施/试点 的高置信必须有 tier<=2 官方来源；仅媒体(tier4) → 降级
    if state in {"full_implemented", "piloted"} and conf == "high" and _best_tier(evidence) >= 3:
        conf = "medium"
        flags.append("高置信先例缺 tier≤2 官方来源（仅高校/媒体）→ 置信降为 medium，待官方佐证")

    # 主决策表
    if state == "full_implemented":
        verdict = "延展" if gaps else "舍弃"
        if not gaps:
            flags.append("已全面实施且六类缺口(覆盖/执行/评价/配套/区域均衡/制度化)均无 → 舍弃")
    elif state in {"piloted", "proposed_not_landed"}:
        verdict = "延展"
    else:  # not_found
        verdict = "保留(真新·待人工确认)" if conf == "high" else "降级保留·待核"

    # 延展硬门：必须给出政策缺口依据（引自下载原文），否则不算延展
    if verdict == "延展" and not s.get("gap_evidence"):
        verdict = "待核"
        flags.append("延展缺 gap_evidence（须引下载政策原文指出'已做X缺Y'）→ 降为待核")

    return {"verdict": verdict, "confidence": conf, "flags": flags}


def check_divergent(d: dict) -> dict:
    """发散新增的准入硬门（4 条全过 + 不得伪空白）。"""
    flags: list[str] = []
    need = {"target": "挂靶(回应前文判断)", "domain": "落教育域",
            "container": "国情容器", "three_whys": "三个为什么"}
    missing = [v for k, v in need.items() if not d.get(k)]
    ok = not missing
    if missing:
        flags.append("缺硬门字段: " + "；".join(missing))
    if d.get("state") != "not_found":
        ok = False
        flags.append("发散项须 state=not_found（否则是冗余，不算新增）")
    blob = f"{d.get('title','')} {d.get('note','')}"
    for bad in FORBIDDEN_NOVELTY_CLAIMS:
        if bad in blob:
            ok = False
            flags.append(f"禁止宣称『{bad}』→ 改为『未检索到充分公开先例，待人工确认』")
    return {"verdict": "候选新增" if ok else "驳回", "flags": flags}


def cmd_scaffold(run_dir: Path) -> None:
    base = run_dir / "suggestion_audit"
    (base / "materials").mkdir(parents=True, exist_ok=True)
    for name, stub in {
        "query_log.md": "# 搜索式日志\n\n> 每条建议逐条记录搜索式，供人工复核。\n",
        "extracted_suggestions.md": "# 抽取的建议（含挂靶）\n\n> agent 从 final_article + suggestion_outputs + judgment_outputs 抽取。\n",
        "report.md": "# 建议审计与延展备忘\n\n> 由 decide 生成。\n",
    }.items():
        p = base / name
        if not p.exists():
            p.write_text(stub, encoding="utf-8")
    print(f"✅ 脚手架就绪: {base}")
    print("   materials/  query_log.md  extracted_suggestions.md  report.md")


def cmd_decide(findings_path: Path, out_path: Path | None) -> None:
    data = json.loads(findings_path.read_text(encoding="utf-8"))
    suggestions = data.get("suggestions", [])
    divergent = data.get("divergent", [])

    lines = ["# 建议审计与延展备忘\n",
             "> 硬性判定由 tools/suggestion_audit_extend.py 生成；web 来源仅入本备忘、逐条带 URL，**不自动写回正文**。\n",
             "\n## 一、原建议裁定\n",
             "| 建议 | 先例状态 | 置信 | 裁定 | 说明/旗标 |",
             "| --- | --- | --- | --- | --- |"]
    tally = {"舍弃": 0, "延展": 0, "保留(真新·待人工确认)": 0, "降级保留·待核": 0, "待核": 0}
    for s in suggestions:
        r = decide_one(s)
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        lines.append(f"| {s.get('title','?')} | {s.get('state','?')} | {r['confidence']} | "
                     f"**{r['verdict']}** | {'；'.join(r['flags']) or '—'} |")

    lines += ["\n## 二、发散新增候选\n",
              "| 新建议 | 准入 | 旗标 |",
              "| --- | --- | --- |"]
    div_ok = 0
    for d in divergent:
        r = check_divergent(d)
        if r["verdict"] == "候选新增":
            div_ok += 1
        lines.append(f"| {d.get('title','?')} | **{r['verdict']}** | {'；'.join(r['flags']) or '—'} |")

    hard_redundant = tally.get("舍弃", 0)
    overall = "未达到" if hard_redundant else "基本达到"
    lines += ["\n## 三、汇总\n",
              f"- 舍弃 {tally.get('舍弃',0)} / 延展 {tally.get('延展',0)} / "
              f"保留 {tally.get('保留(真新·待人工确认)',0)} / 待核 {tally.get('待核',0)+tally.get('降级保留·待核',0)}",
              f"- 发散候选(过 4 硬门) {div_ok} / {len(divergent)}",
              f"- **总体结论：{overall}**（有舍弃项=存在硬冗余建议→需改建议清单）",
              "- 删改、是否并入正文：**交人确认**（本工具只判，不改正文）。\n"]

    report = "\n".join(lines) + "\n"
    target = out_path or (findings_path.parent / "report.md")
    target.write_text(report, encoding="utf-8")
    print(f"✅ 裁定完成 → {target}")
    print(f"   舍弃{tally.get('舍弃',0)} 延展{tally.get('延展',0)} "
          f"保留{tally.get('保留(真新·待人工确认)',0)} 待核{tally.get('待核',0)+tally.get('降级保留·待核',0)}"
          f" | 发散候选{div_ok}/{len(divergent)} | 总体:{overall}")


def main() -> int:
    p = argparse.ArgumentParser(description="建议核查与延展 · 硬性判定工具")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("scaffold", help="为某 run 建 suggestion_audit/ 脚手架")
    sp.add_argument("run_dir", type=Path)
    dp = sub.add_parser("decide", help="对 agent 产出的 findings.json 套硬决策表 → report.md")
    dp.add_argument("findings", type=Path)
    dp.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    if args.cmd == "scaffold":
        cmd_scaffold(args.run_dir)
    elif args.cmd == "decide":
        cmd_decide(args.findings, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# ---- findings.json schema（agent 联网核查后产出）----
# {
#   "suggestions": [{
#     "id": "S1", "title": "...",
#     "measure": "对象+工具+机制", "target": "回应的前文靶子",
#     "state": "full_implemented|piloted|proposed_not_landed|not_found",
#     "confidence": "high|medium|low",
#     "evidence": [{"name":"政策名","date":"2026-04","url":"...","source_tier":1}],
#     "gaps": ["配套","评价"],                # 缺口六分类的子集（覆盖/执行/评价/配套/区域均衡/制度化）
#     "gap_evidence": "政策已做X、缺Y（引自下载原文）",  # 延展必填
#     "queries": ["教育部 + AI人才 + 本研贯通 + 试点", "..."]
#   }],
#   "divergent": [{
#     "title": "...", "target": "挂靶", "domain": "教育子域", "container": "国情容器",
#     "three_whys": "为什么做/不照搬/这个版本", "state": "not_found",
#     "confidence": "...", "queries": ["..."], "note": "未检索到充分公开先例，待人工确认"
#   }]
# }
