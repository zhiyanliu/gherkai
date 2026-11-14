// job 墙钟预算的产品上限不大于本引擎对每种目标能支持的最长预算（ADR 0054 决策十），Midscene 侧。
//
// 产品上限是 core 的常数（core/gherkai_core/model.py 的 MAX_JOB_TIMEOUT_S），这里从源文件读出它，不另抄一份。本引擎能支持的最长预算：
// 设备目标取能力自述里的 max_session_s；桌面目标取浏览器会话存活时间的封顶值减去余量（会话存活时间按预算加余量设定，预算再大就被封顶截短）。
// 引擎一侧的任何一个数低于产品上限，本测试即失败。Nova 侧由 cli/tests/test_job_timeout_cap.py 核。
// 运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import { BROWSER_SESSION_TIMEOUT, browserSessionTimeoutS } from "./surface-desktop.mjs";

const MODEL_PY = path.resolve(import.meta.dirname, "..", "..", "..", "..", "core", "gherkai_core", "model.py");

function productCapS(): number {
  const m = /^MAX_JOB_TIMEOUT_S = ([0-9.]+)$/m.exec(fs.readFileSync(MODEL_PY, "utf-8"));
  assert.ok(m, `${MODEL_PY} 里找不到 MAX_JOB_TIMEOUT_S 的赋值行（改了写法要同步这里的读取）`);
  const cap = Number(m![1]);
  assert.ok(Number.isFinite(cap) && cap > 0, `读出的产品上限不是正数：${m![1]}`);
  return cap;
}

test("设备目标：能力自述里每个带会话上限的目标，上限不低于产品上限", async () => {
  const cap = productCapS();
  const { WORKER_TARGETS } = await import("./run-scope.mjs");
  const limited = WORKER_TARGETS.filter((t) => t.max_session_s !== undefined);
  assert.ok(limited.length > 0, "能力自述里没有带会话上限的目标（设备目标应当带）");
  for (const t of limited) assert.ok(t.max_session_s! >= cap, `${t.device} 的会话上限 ${t.max_session_s} 秒低于产品上限 ${cap} 秒`);
});

test("桌面目标：浏览器会话存活时间的封顶值减去余量不低于产品上限，预算取到上限时存活时间不被截短", () => {
  const cap = productCapS();
  assert.ok(BROWSER_SESSION_TIMEOUT.maxS - BROWSER_SESSION_TIMEOUT.marginS >= cap,
    `会话存活时间封顶 ${BROWSER_SESSION_TIMEOUT.maxS} 秒减余量 ${BROWSER_SESSION_TIMEOUT.marginS} 秒低于产品上限 ${cap} 秒`);
  assert.equal(browserSessionTimeoutS(cap), Math.ceil(cap) + BROWSER_SESSION_TIMEOUT.marginS);
});
