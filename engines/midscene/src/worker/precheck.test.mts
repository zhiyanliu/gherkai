// 建会话前的自检（ADR 0049 决策 7；0048 决策 3、4）：对称 Nova 的 test_precheck.py。运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import { precheckTarget, targetLabel } from "../lib/precheck.mjs";
import { WORKER_TARGETS } from "./run-scope.mjs";

const DEVICE_TARGETS = [{ device: "desktop", ui_kinds: ["web"] }, { device: "android", ui_kinds: ["web", "app"], max_session_s: 8000 }];

test("桌面 job（含不带 target 键的旧形态）对真实 WORKER_TARGETS 通过", () => {
  assert.equal(precheckTarget({}, WORKER_TARGETS), null);
  assert.equal(precheckTarget({ target: { device: "desktop", uiKind: "web" }, timeoutS: 300 }, WORKER_TARGETS), null);
});

test("设备 job 被当前只声明桌面网页的 worker 拒绝，消息是产品语言", () => {
  const msg = precheckTarget({ target: { device: "ios", uiKind: "app" }, timeoutS: 1500 }, WORKER_TARGETS);
  assert.equal(msg, "这个 worker 不支持在iOS 应用上执行测试（它支持：桌面网页）。请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。");
  assert.ok(!msg!.includes("ADR") && !msg!.includes("precheck"));
});

test("墙钟预算超过会话上限被拒绝；等于上限、没带预算、桌面无上限都通过", () => {
  const over = precheckTarget({ target: { device: "android", uiKind: "web" }, timeoutS: 9000 }, DEVICE_TARGETS);
  assert.ok(over !== null && over.includes("超过了Android 网页的会话上限 8000 秒") && over.includes("--default-job-timeout"));
  assert.equal(precheckTarget({ target: { device: "android", uiKind: "web" }, timeoutS: 8000 }, DEVICE_TARGETS), null);
  assert.equal(precheckTarget({ target: { device: "android", uiKind: "web" } }, DEVICE_TARGETS), null);
  assert.equal(precheckTarget({ target: { device: "desktop", uiKind: "web" }, timeoutS: 1e9 }, DEVICE_TARGETS), null);
});

test("目标名称与命令行工具同一口径", () => {
  assert.equal(targetLabel("desktop", "web"), "桌面网页");
  assert.equal(targetLabel("android", "app"), "Android 应用");
  assert.equal(targetLabel("ios", "web"), "iOS 网页");
});
