// 所属进程核验单测（ADR 0024 终止契约「父进程消失」条）。运行：node --import tsx --test。
import { test } from "node:test";
import assert from "node:assert";
import { ownerPidFromEnv, processAlive, startParentWatchdog } from "../lib/parent-watchdog.mjs";

const tick = (ms: number) => new Promise((r) => setTimeout(r, ms));

test("所属进程退出后调一次 onGone，之后不再核验", async () => {
  const alive = [true, true, false, false];
  let polls = 0;
  let gone = 0;
  const stop = startParentWatchdog(() => { gone += 1; }, { ownerPid: 4242, isAlive: () => alive[Math.min(polls++, alive.length - 1)], intervalMs: 2 });
  await tick(60);
  stop();
  assert.equal(gone, 1);
  assert.equal(polls, 3);  // 启动时核验一次，之后一次存活、再一次已退出即停
});

test("所属进程一直存活则不触发", async () => {
  let gone = 0;
  const stop = startParentWatchdog(() => { gone += 1; }, { ownerPid: 4242, isAlive: () => true, intervalMs: 2 });
  await tick(30);
  stop();
  assert.equal(gone, 0);
});

test("装上之前所属进程已退出：首次核验即触发（不把当前父进程号当基准）", () => {
  let gone = 0;
  startParentWatchdog(() => { gone += 1; }, { ownerPid: 4242, isAlive: () => false, intervalMs: 2 });
  assert.equal(gone, 1);
});

test("未传入所属进程号（容器主进程）则不启动", async () => {
  let polls = 0;
  startParentWatchdog(() => assert.fail("不应触发"), { ownerPid: null, isAlive: () => { polls += 1; return false; }, intervalMs: 2 });
  await tick(20);
  assert.equal(polls, 0);
});

test("直接子进程：所属进程退出后尚未被回收（空信号仍报存在）也靠父进程号变化触发", async () => {
  const ppids = [4242, 4242, 1, 1];
  let polls = 0;
  let gone = 0;
  const stop = startParentWatchdog(() => { gone += 1; }, {
    ownerPid: 4242, isAlive: () => true, getPpid: () => ppids[Math.min(polls++, ppids.length - 1)], intervalMs: 2,
  });
  await tick(60);
  stop();
  assert.equal(gone, 1);
});

test("经包装进程启动（父进程不是所属进程）：父进程号变化不作依据，只看所属进程是否存活", async () => {
  const alive = [true, true, true, false];
  let polls = 0;
  let gone = 0;
  const stop = startParentWatchdog(() => { gone += 1; }, {
    ownerPid: 4242, isAlive: () => alive[Math.min(polls++, alive.length - 1)], getPpid: () => 9999, intervalMs: 2,
  });
  await tick(60);
  stop();
  assert.equal(gone, 1);
  assert.equal(polls, 4);
});

test("环境变量解析：正整数取用，缺失或非法为 null", () => {
  assert.equal(ownerPidFromEnv({ GHERKAI_PARENT_PID: "123" }), 123);
  assert.equal(ownerPidFromEnv({}), null);
  assert.equal(ownerPidFromEnv({ GHERKAI_PARENT_PID: "" }), null);
  assert.equal(ownerPidFromEnv({ GHERKAI_PARENT_PID: "abc" }), null);
  assert.equal(ownerPidFromEnv({ GHERKAI_PARENT_PID: "0" }), null);
});

test("processAlive：本进程存活；已退出的子进程不存活", async () => {
  assert.equal(processAlive(process.pid), true);
  const { spawn } = await import("node:child_process");
  const child = spawn(process.execPath, ["-e", "0"]);
  const pid = child.pid!;
  await new Promise((r) => child.on("exit", r));
  assert.equal(processAlive(pid), false);  // 已被回收的进程：ESRCH
});
