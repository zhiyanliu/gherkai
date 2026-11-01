// AgentCore 浏览器会话超时的取值规则（ADR 0024 终止契约「泄漏兜底」条）：与 Nova 桌面 worker 经 engines/fixtures/browser-session-timeout.json 对拍。
// 运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs";
import * as path from "node:path";
import { BROWSER_SESSION_TIMEOUT, browserSessionTimeoutS } from "./surface-desktop.mjs";

const fixture = JSON.parse(fs.readFileSync(path.resolve(import.meta.dirname, "..", "..", "..", "fixtures", "browser-session-timeout.json"), "utf-8"));

test("余量与区间与共用夹具一致", () => {
  assert.deepEqual([BROWSER_SESSION_TIMEOUT.marginS, BROWSER_SESSION_TIMEOUT.minS, BROWSER_SESSION_TIMEOUT.maxS],
    [fixture.margin_s, fixture.min_s, fixture.max_s]);
});

test("各用例：预算为空不传，其余向上取整加余量并夹在区间内", () => {
  for (const c of fixture.cases) assert.equal(browserSessionTimeoutS(c.timeout_s), c.expected, JSON.stringify(c));
  assert.equal(browserSessionTimeoutS(undefined), null);
});
