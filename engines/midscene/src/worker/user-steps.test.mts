// 使用方 steps/ 目录加载的单测（ADR 0037 决策 4）——遍历规则 + 两条 fail-loud。
// 跑：npm test（node --import tsx --test "src/**/*.test.mts"）。
//
// **分两层，刻意**：
//   - 纯逻辑层（遍历排序/扩展名过滤、注入 importer+size 后的 fail-loud 判定）→ 注入依赖、不碰真 ESM 加载器；
//   - **真跑层**（文件末）→ spawn 真入口 `bin.mts`、真 temp 目录（repo 外）、真 dynamic import：裸 specifier
//     `@gherkai/worker-midscene` 的 resolve hook 与「同一模块实例」这两条**只在真 loader 里成立**，
//     注 fake 的单测看不见（ADR 0037 实测项 3 明写「在 repo 内预演会被 repo 自己的 node_modules 掩盖成假绿」）。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { spawn } from "node:child_process";
import { collectStepFiles, loadUserSteps } from "./user-steps.mjs";

function tmpSteps(files: Record<string, string>): string {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-steps-test-"));
  for (const [rel, content] of Object.entries(files)) {
    const p = path.join(root, rel);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, content);
  }
  return root;
}

// ---- 遍历规则：排序、递归、扩展名、排除 *.test.* ----
test("collectStepFiles: 排序递归、只取 .mts/.mjs、排除 *.test.*", () => {
  const root = tmpSteps({
    "b.mts": "", "a.mjs": "", "a.test.mts": "", "notes.md": "", "old.ts": "",
    "z/deep/x.mts": "", "m/y.mjs": "", "m/y.test.mjs": "",
  });
  const got = collectStepFiles(root).map((f) => path.relative(root, f));
  assert.deepEqual(got, ["a.mjs", "b.mts", path.join("m", "y.mjs"), path.join("z", "deep", "x.mts")]);
});

// ---- env 未设 / 目录缺失 ----
test("loadUserSteps: stepsDir 未给 → no-op（返回空）", async () => {
  assert.deepEqual(await loadUserSteps({ stepsDir: undefined }), []);
});

test("loadUserSteps: 目录不存在 → 抛（没开跑就被拒，不装作没有确定性 step）", async () => {
  await assert.rejects(
    () => loadUserSteps({ stepsDir: path.join(os.tmpdir(), "gherkai-not-here-" + Date.now()) }),
    /不是目录/,
  );
});

// ---- fail-loud ①：import 失败 ----
test("loadUserSteps: 某文件 import 失败 → 抛，带文件名 + 原因压成一行", async () => {
  const root = tmpSteps({ "boom.mts": "" });
  await assert.rejects(
    () => loadUserSteps({
      stepsDir: root,
      importer: async () => { throw new Error("Transform failed\n  第二行细节"); },
      size: () => 0,
    }),
    (e: Error) => {
      assert.match(e.message, /boom\.mts/);
      assert.match(e.message, /Transform failed \| 第二行细节/);
      assert.equal(e.message.includes("\n"), false, "诊断行须是一行");
      return true;
    },
  );
});

// ---- fail-loud ②：零注册（双实例守卫）----
test("loadUserSteps: 文件一条都没注册 → 抛并点名该文件（双实例守卫）", async () => {
  const root = tmpSteps({ "silent.mts": "" });
  await assert.rejects(
    () => loadUserSteps({ stepsDir: root, importer: async () => {}, size: () => 7 }),
    /silent\.mts 一条确定性 step 都没注册/,
  );
});

test("loadUserSteps: 每个文件都注册 → 返回加载清单（逐文件比对增量，非只看总量）", async () => {
  const root = tmpSteps({ "a.mts": "", "b.mts": "" });
  let n = 0;
  const files = await loadUserSteps({
    stepsDir: root,
    importer: async () => { n += 1; },   // 每个文件注册一条
    size: () => n,
    logFn: () => {},
  });
  assert.deepEqual(files.map((f) => path.basename(f)), ["a.mts", "b.mts"]);
});

// ---- 真跑层：spawn 真入口，验 resolve hook + 同一注册表实例 + fail-loud 真触发 ----
// steps 目录建在 os.tmpdir()（**repo 外**）：目录里没有 node_modules、没有 package.json，
// 裸 specifier 只能靠 bin 注册的 resolve hook 解析——这正是「全局装 / npx」形态下使用方的真实处境。
const BIN = path.join(import.meta.dirname, "..", "bin.mts");
// 起源码形态的 bin 要有 TS 转译能力。`--import tsx` 的裸 specifier 会按 **cwd** 上溯 node_modules 解析
// （ADR 0037 决策 3 实测过的坑），而本测试刻意把 cwd 放在 repo 外 → 故把 tsx 的 loader 解析成**绝对 URL**
// 再传（从本文件解析，与 cwd 无关）。也不靠 Node 的原生 type stripping（那要 Node ≥22.18，而包只声明 >=22）。
const TSX_LOADER = import.meta.resolve("tsx");
function runBin(stepsDir: string): Promise<{ code: number; out: string; err: string }> {
  const proc = spawn(process.execPath, ["--import", TSX_LOADER, BIN, "--list-deterministic"], {
    cwd: os.tmpdir(),  // cwd 也在 repo 外：任何靠 cwd 上溯 node_modules 的解析都会现形
    env: { ...process.env, GHERKAI_STEPS_DIR: stepsDir },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const out: Buffer[] = []; const err: Buffer[] = [];
  proc.stdout.on("data", (c) => out.push(c));
  proc.stderr.on("data", (c) => err.push(c));
  return new Promise((r) => proc.on("close", (code) =>
    r({ code: code ?? -1, out: Buffer.concat(out).toString(), err: Buffer.concat(err).toString() })));
}

test("真跑: repo 外 steps 目录里的 .mts/.mjs 注册进**同一张**注册表（裸 specifier 经 resolve hook）", async () => {
  const root = tmpSteps({
    "demo.mts": `import { deterministic } from "@gherkai/worker-midscene";
deterministic('自定义锚点 "(?<x>[^"]+)"', () => {}, { description: "d", example: "e" });\n`,
    "sub/nested.mjs": `import { deterministic } from "@gherkai/worker-midscene";
deterministic('嵌套锚点', () => {}, { description: "d2", example: "e2" });\n`,
  });
  const { code, out, err } = await runBin(root);
  assert.equal(code, 0, `应退 0，stderr=${err}`);
  const patterns = JSON.parse(out).map((e: { pattern: string }) => e.pattern);
  // 内建脚手架 + 两个使用方 step 同在一张表里（ADR 0036「真值单一」：注册表 = 内建 + 使用方）。
  assert.ok(patterns.some((p: string) => p.includes("页面地址")), `内建该在：${patterns}`);
  assert.ok(patterns.includes('自定义锚点 "(?<x>[^"]+)"'), `使用方 .mts 该在：${patterns}`);
  assert.ok(patterns.includes("嵌套锚点"), `使用方 .mjs 该在：${patterns}`);
});

test("真跑: 语法错的 steps 文件 → 非零退出 + stderr 点名该文件（绝不静默跳过）", async () => {
  const root = tmpSteps({ "broken.mts": `import { deterministic } from "@gherkai/worker-midscene"; deterministic(\n` });
  const { code, err } = await runBin(root);
  assert.notEqual(code, 0, "加载失败必须非零退出");
  assert.match(err, /broken\.mts/);
});

test("真跑: 一条都不注册的 steps 文件 → 非零退出 + 点名（双实例守卫的显式失败）", async () => {
  const root = tmpSteps({ "noop.mts": "export const nothing = 1;\n" });
  const { code, err } = await runBin(root);
  assert.notEqual(code, 0);
  assert.match(err, /noop\.mts 一条确定性 step 都没注册/);
});
