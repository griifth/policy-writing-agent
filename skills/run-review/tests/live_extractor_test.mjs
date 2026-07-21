// 实时抽取器自检：从 overview_template.html 抽出 /*__LIVE_EXTRACTOR__*/ 块，
// 接 node fs 适配器跑真实 runs/，与 runs/回顾总览.html 内嵌快照做语义比对。
// 用法：node skills/run-review/tests/live_extractor_test.mjs
import { readFile, readdir, writeFile, rm } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "../../.."); // direction_workflow/
const RUNS = join(ROOT, "runs");

// 1) 从模板抽出抽取器块，写成临时模块并 import
const tpl = await readFile(join(ROOT, "skills/run-review/references/overview_template.html"), "utf8");
const m = tpl.match(/\/\*__LIVE_EXTRACTOR_START__\*\/([\s\S]*?)\/\*__LIVE_EXTRACTOR_END__\*\//);
if (!m) { console.error("FAIL: 模板中找不到 LIVE_EXTRACTOR 标记块"); process.exit(1); }
const tmpMod = join("/tmp", `live_extractor_${process.pid}.mjs`);
await writeFile(tmpMod, m[1] + "\nexport { liveExtractAll, parseLedger, parseDirectionType };\n", "utf8");
const { liveExtractAll } = await import(pathToFileURL(tmpMod).href);

// 2) node fs → io 适配器（与浏览器 FS API 适配器同签名）
const io = {
  async listRuns() {
    const es = await readdir(RUNS, { withFileTypes: true });
    return es.filter(e => e.isDirectory()).map(e => e.name);
  },
  async readText(runId, rel) {
    try { return await readFile(join(RUNS, runId, rel), "utf8"); } catch { return null; }
  },
  async exists(runId, rel) {
    try { await readdir(join(RUNS, runId, rel.split("/").slice(0, -1).join("/") || ".")); } catch { return false; }
    try { await readFile(join(RUNS, runId, rel)); return true; } catch {
      // docx 是二进制，readFile 不报错——能读即在场
      return false;
    }
  },
};

// 修正 exists：用 stat 而非 readFile（docx 也能判在场）
import { stat } from "node:fs/promises";
io.exists = async (runId, rel) => { try { await stat(join(RUNS, runId, rel)); return true; } catch { return false; } };

// 3) 跑实时抽取
const live = await liveExtractAll(io);

// 4) 取内嵌快照作期望集
const page = await readFile(join(RUNS, "回顾总览.html"), "utf8");
const pm = page.match(/const OVERVIEW_DATA = (\{[\s\S]*?\n\});/);
if (!pm) { console.error("FAIL: 回顾总览.html 中找不到内嵌 OVERVIEW_DATA"); process.exit(1); }
const snap = JSON.parse(pm[1]);

// 5) 语义比对
let fail = 0;
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const snapById = Object.fromEntries(snap.runs.map(r => [r.runId, r]));

const liveIds = live.runs.map(r => r.runId);
const snapIds = snap.runs.map(r => r.runId);
if (!eq(liveIds, snapIds)) {
  console.error("FAIL runId 集合/顺序不一致:\n live:", liveIds, "\n snap:", snapIds);
  fail++;
} else {
  console.log("OK runId 集合与顺序一致（" + liveIds.length + " 单，新单在上）");
}

for (const r of live.runs) {
  const s = snapById[r.runId];
  if (!s) { console.error("FAIL 快照中无此 run:", r.runId); fail++; continue; }
  const critical = [
    ["date", r.date, s.date],
    ["title", r.title, s.title],
    ["deliverables", r.deliverables, s.deliverables],
    ["reviewPage", r.reviewPage, s.reviewPage],
    ["panxingLabel", r.panxingLabel, s.panxingLabel],
  ];
  for (const [k, a, b] of critical) {
    if (eq(a, b)) console.log(`OK   ${r.runId} · ${k}`);
    else { console.error(`FAIL ${r.runId} · ${k}\n  live: ${JSON.stringify(a)}\n  snap: ${JSON.stringify(b)}`); fail++; }
  }
  // 长文本字段：机械端口取单元格原文，允许与 agent 精修快照有措辞差——列差异，不判负
  for (const k of ["panxing", "gouxuanlv", "engine"]) {
    const a = r[k] || "", b = s[k] || "";
    if (a === b) console.log(`OK   ${r.runId} · ${k}（与快照逐字一致）`);
    else if (b && a.includes(b.slice(0, 12))) console.log(`DIFF ${r.runId} · ${k}（前缀吻合，实时取原文更长，属预期）\n  live: ${a.slice(0, 80)}\n  snap: ${b.slice(0, 80)}`);
    else console.log(`DIFF ${r.runId} · ${k}（措辞有差，人工复核）\n  live: ${a.slice(0, 80)}\n  snap: ${b.slice(0, 80)}`);
  }
}

console.log("\n实时 extractionNotes:", live.extractionNotes.length, "条（快照:", snap.extractionNotes.length, "条）");
live.extractionNotes.forEach(n => console.log("  -", n.field + "：", n.note));

await rm(tmpMod, { force: true });
if (fail) { console.error(`\nFAIL: ${fail} 处关键字段不一致`); process.exit(1); }
console.log("\nPASS: 关键字段（runId/date/title/deliverables/reviewPage/panxingLabel）全部一致");
