// `--no-report` 档（GHERKAI_NO_ARTIFACTS=1，ADR 0037 决策 3）下 scope 末不 flush 引擎原生产物。
// NO_ARTIFACTS 在 run-scope.mts **模块加载时**读 env，故本用例独占一个测试文件（node --test 每文件一进程），
// 在 import 之前置 env；对照组（未置 env → 返回解析后的 MIDSCENE_RUN_DIR）在 run-scope.test.mts。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

process.env.GHERKAI_NO_ARTIFACTS = "1";
process.env.MIDSCENE_RUN_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "gherkai-noart-"));

test("artifactFlushRoot: --no-report 档即便 MIDSCENE_RUN_DIR 已设（SDK 内部 log 落点）也不给 flush 根", async () => {
  const { artifactFlushRoot } = await import("./run-scope.mjs");
  assert.equal(artifactFlushRoot(), undefined);
});
