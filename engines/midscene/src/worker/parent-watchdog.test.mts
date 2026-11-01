// 父进程核对单测（ADR 0024 终止契约「父进程消失」条）。运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import { startParentWatchdog } from "../lib/parent-watchdog.mjs";

test("父进程号变了即调一次 onGone，之后不再核对", async () => {
  const ppids = [100, 100, 1, 1, 1];
  let polls = 0;
  let gone = 0;
  const stop = startParentWatchdog(() => { gone += 1; }, { getPpid: () => ppids[Math.min(polls++, ppids.length - 1)], intervalMs: 2 });
  await new Promise((r) => setTimeout(r, 60));
  stop();
  assert.equal(gone, 1);
  assert.equal(polls, 3);  // 启动时取一次，之后一次相同、再一次变化即停
});

test("父进程号不变则不触发", async () => {
  let gone = 0;
  const stop = startParentWatchdog(() => { gone += 1; }, { getPpid: () => 4242, intervalMs: 2 });
  await new Promise((r) => setTimeout(r, 30));
  stop();
  assert.equal(gone, 0);
});

test("不是作为子进程启动（父进程号不大于 1）则不启动", async () => {
  let polls = 0;
  for (const ppid of [1, 0]) {
    startParentWatchdog(() => assert.fail("不应触发"), { getPpid: () => { polls += 1; return ppid; }, intervalMs: 2 });
  }
  await new Promise((r) => setTimeout(r, 20));
  assert.equal(polls, 2);  // 只有启动时那一次读取
});
