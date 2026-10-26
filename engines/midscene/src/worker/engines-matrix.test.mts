// 引擎能力矩阵（docs/user-guide/engines.md）的差集护栏，Midscene 侧（ADR 0049 决策 8）。
//
// 真值集是本 worker 在无环境变量覆盖时的能力自述：目标列对 targets、默认模型列对 model_id、句柄列由目标按 ADR 0050
// 决策 1 的固定规则推出（desktop → playwright，设备 → webdriver）。Nova 的行与表格结构由 cli/tests/test_engines_matrix.py
// 在 pytest 里核；两侧分开是因为 pytest 的 CI job 装不出 Midscene 的 dist。**真起子进程**：矩阵对的是实际会自报的值，
// in-process 读常量证不到「自报的就是这个」。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import { spawn } from "node:child_process";

const MATRIX = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../../../../docs/user-guide/engines.md");
const HANDLE_BY_DEVICE: Record<string, string> = { desktop: "playwright", android: "webdriver", ios: "webdriver" };
// 目标的产品语言名称（与 cli/gherkai_cli/render.py 的 target_label 同一口径；文档用的是人读名称，不是协议取值）
const DEVICE_LABEL: Record<string, string> = { desktop: "桌面", android: "Android", ios: "iOS" };
const UI_KIND_LABEL: Record<string, string> = { web: "网页", app: "应用" };
const targetLabel = (device: string, kind: string) =>
  device === "desktop" ? `${DEVICE_LABEL[device]}${UI_KIND_LABEL[kind]}` : `${DEVICE_LABEL[device]} ${UI_KIND_LABEL[kind]}`;

interface Row { engine: string; target: string; handle: string; model: string }

function matrixRows(): Row[] {
  const lines = fs.readFileSync(MATRIX, "utf8").split(/\r?\n/);
  const start = lines.findIndex((ln) => ln.startsWith("| 引擎 |"));
  assert.ok(start >= 0, "engines.md 里找不到以「| 引擎 |」开头的矩阵表");
  const rows: Row[] = [];
  for (const ln of lines.slice(start + 2)) {
    if (!ln.startsWith("|")) break;
    const cells = ln.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
    const code = /`([a-z]+)`/.exec(cells[0]); const handle = /`([a-z]+)`/.exec(cells[2]); const model = /`([^`]+)`/.exec(cells[3]);
    assert.ok(code && handle && model, `矩阵行形态不对：${ln}`);
    rows.push({ engine: code![1], target: cells[1], handle: handle![1], model: model![1] });
  }
  return rows;
}

test("engines.md 的 Midscene 行与 worker 无覆盖时的自述逐行一致（多一行、少一行、值不符都失败，ADR 0049 决策 8）", async () => {
  // 剥掉模型覆盖与 steps 目录：矩阵写的是发行版默认值
  const env = Object.fromEntries(Object.entries(process.env).filter(([k]) =>
    !k.startsWith("MIDSCENE_") && !k.startsWith("GHERKAI_") && !k.startsWith("AWS_")));
  const proc = spawn(process.execPath, [
    "--import", import.meta.resolve("tsx"), path.join(import.meta.dirname, "..", "bin.mts"), "--capabilities",
  ], { stdio: ["ignore", "pipe", "pipe"], env });
  const out: Buffer[] = []; const err: Buffer[] = [];
  proc.stdout.on("data", (c) => out.push(c)); proc.stderr.on("data", (c) => err.push(c));
  const code: number = await new Promise((r) => proc.on("close", r));
  assert.equal(code, 0, Buffer.concat(err).toString("utf-8"));
  const caps = JSON.parse(Buffer.concat(out).toString("utf-8"));
  assert.equal(caps.engine, "midscene");
  const expected: Row[] = [];
  for (const t of caps.targets as Array<{ device: string; ui_kinds: string[] }>) {
    for (const k of t.ui_kinds) {
      expected.push({ engine: "midscene", target: targetLabel(t.device, k), handle: HANDLE_BY_DEVICE[t.device], model: caps.model_id });
    }
  }
  const documented = matrixRows().filter((r) => r.engine === "midscene");
  assert.deepEqual(documented, expected,
    `docs/user-guide/engines.md 的 Midscene 行与 worker 自述不一致：\n文档 ${JSON.stringify(documented)}\n自述推出 ${JSON.stringify(expected)}`);
});
