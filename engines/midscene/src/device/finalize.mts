// 终结块（ADR 0052 决策 3；ADR 0051 决策 3、4、5、7）：实现 device/surface.mts 的 DeviceFinalizer 端口——释放的两种模式与终结的
// 前三个阶段，并为每个会话发恰一条 session_closed、为仍待核的尝试发一对 attempted。与 Device Farm 会话块（device/session.mts）共享
// 同一份会话登记，Device Farm 的调用也经会话块发出。
//
// 两种模式（ADR 0051 决策 5）：
//   - normal（正常收尾、执行前失败与 scope 级终止）：调用方先结束 Midscene 侧与有界上传；这里 Appium 会话已建成、远程访问会话
//     又不是 STOPPING / COMPLETED 时先 deleteSession（至多 5 秒、不重试、不阻塞 Stop），再终结核对、释放、发 session_closed；
//     返回之后调用方发 scope_done、排空上传队列。deleteSession 能缩短停止到 COMPLETED 的时间、少计设备分钟（实测 52 秒对 73 秒）。
//   - interrupt（停止信号与进程级异常）：不调 deleteSession（Stop 决定计费，deleteSession 只是 Appium 侧的收尾）。
// 两种模式都按同一组阶段执行，前三个阶段依次接续，各阶段的截止线在本阶段开始时取定、之后不再延后；中断路径上阶段之间没有别的
// 等待，三段之和不超过进入终结后的 10 + 5 + 25 秒（ADR 0051 决策 5 的各阶段截止线）。attempted 事件与释放并行写出，
// 不占这三段：
//   1. 等在途的 Create（10 秒）：返回即已登记 ARN（session_opened(created) 的写出可能仍在进行，本阶段不等它；已登记的不再记为
//      待核）；到线仍未返回的记为待核，终结核对结束之后才返回的只记日志、不再登记（它已按 attempted 上报）。正常模式下不会有
//      在途的 Create（获取已经返回），这一段为空。
//   2. 终结核对（5 秒）：按名列举处理全部待核尝试，扫到分页结束（全部名字都已命中也继续翻页，列举出错或到截止线即停），同名的
//      每个 ARN 都登记进待清理集并发 session_opened(discovered)；阶段结束仍待核的各发 session_opened(attempted) 与
//      session_closed(unconfirmed)，与阶段 3 并行写出。列举为空不构成排除。按名找回之后，原 Create 晚到的失败或没带 ARN 的返回
//      不再记为待核；本阶段结束之后晚到的结果也不再记（会话块的 markPending）。
//   3. 释放（25 秒，全部会话并行、共享截止线）：每个会话先 Get；状态不是 STOPPING / COMPLETED（含排队中的 PENDING_CONCURRENCY、
//      准备中的 PREPARING 与 RUNNING）或 Get 失败时发 Stop；Stop 报错或返回体不是这两个状态时补查一次 Get；仍未确认则退避后再
//      Stop 一次、再补查。确认只认 STOPPING / COMPLETED，到线仍未确认记 unconfirmed。被拒方案是「仍为 RUNNING 才发 Stop」：排队或
//      准备中的会话不 Stop 就不会撤回，之后照常进入 RUNNING 并计费到 150 分钟上限。换台时被替换的会话与获取期按名找回的会话，
//      获取侧已按同一规则处理过一次；等到 RUNNING 期间读到 STOPPING / COMPLETED 的会话，获取侧在读到时即记为确认。已确认的不再查，
//      没确认的在这里照常处理（获取侧在终结接手前已发出的 Stop 不撤回，这里照常先 Get 再决定；observedS 的止点仍按 observedSeconds
//      取第一次发出 Stop 或确认已停止的时刻中较早者，含获取侧的那次处理）。
// 阶段 4 的中断兜底上传与截图队列排空归调用方（worker/run-scope.mts 的收尾序列），在本块返回之后执行。
//
// 只进入一次：重复调用（信号重复、超时与信号交叠、两种模式先后到达）返回同一个结果，四阶段不重新进入。每个真实会话按 ARN 只发
// 一条 session_closed，不先发 unconfirmed 再补 confirmed（会话事件出口另按配对键去重，见 device/device-session.mts）。
// releaseFailed 为真表示有会话未能确认停止或发过 attempted，是退出码 1 的依据。
import { errorText } from "../worker/error-text.mjs";
import type { ReleaseMode } from "../worker/surface.mjs";
import type { DeviceFinalizer, FinalizeHooks } from "./surface.mjs";
import type { SessionClosedFact } from "./device-session.mjs";
import { isStopped, minutesOf, type DeviceFarmSessionBlock, type TrackedSession } from "./session.mjs";
import {
  DELETE_SESSION_TIMEOUT_MS, DEVICE_RELIST_DELAY_MS, FINALIZE_AWAIT_CREATE_MS, FINALIZE_GET_TIMEOUT_MS, FINALIZE_RECONCILE_MS,
  FINALIZE_RELEASE_MS, STOP_CALL_TIMEOUT_MS,
} from "./limits.mjs";

/** 释放阶段第二次 Stop 之前的退避：取与零候选重列相同的短间隔，使 Get、Stop、补查、退避、再 Stop、再补查都不响应时
 *  （5 + 3 + 5 + 2 + 3 + 5，合计 23 秒）仍落在 25 秒的释放截止线之内（实施期校准、真机验收后可调）。 */
export const RELEASE_RETRY_DELAY_MS = DEVICE_RELIST_DELAY_MS;

/** worker 观察到一个会话的秒数（ADR 0051 决策 7）：起点为 Create 返回或列举发现的时刻，止点为第一次发出 Stop 或确认已停止的
 *  时刻（取较早者）；两者都没有时为 null，不用 0 代替缺失。 */
export function observedSeconds(t: Pick<TrackedSession, "observedFrom" | "stopSentAt" | "confirmedAt">): number | null {
  const ends = [t.stopSentAt, t.confirmedAt].filter((v): v is number => v !== null);
  if (ends.length === 0) return null;
  return Math.max(0, Math.min(...ends) - t.observedFrom) / 1000;
}

/** 终结块的构造（部件工厂调用）：传入同一个会话块，两者共享会话登记。 */
export function createDeviceFinalizer(sessions: DeviceFarmSessionBlock): DeviceFinalizer {
  let entered: Promise<{ releaseFailed: boolean }> | null = null;
  return {
    finalize(mode: ReleaseMode, hooks: FinalizeHooks) {
      entered ??= finalizeOnce(sessions, mode, hooks);
      return entered;
    },
  };
}

async function finalizeOnce(s: DeviceFarmSessionBlock, mode: ReleaseMode, hooks: FinalizeHooks): Promise<{ releaseFailed: boolean }> {
  const reg = s.registry;
  reg.closed = true;  // 同步置位：此后获取侧不再发新的 Create，也不再对不再使用的会话发新的 Get / Stop

  // 阶段 1：等在途的 Create。
  const inflight = [...reg.inflight];
  if (inflight.length > 0) {
    await settleBy(s, Promise.allSettled(inflight.map((e) => e.recorded)), s.now() + FINALIZE_AWAIT_CREATE_MS);
    for (const e of inflight) {
      if (!e.settled) s.markPending(e.name, e.attempt, "建立远程访问会话的请求在等待时间内没有返回", "");
    }
  }

  if (mode === "normal" && hooks.deleteAppiumSession) await deleteAppiumSession(s, hooks.deleteAppiumSession);

  // 阶段 2：终结核对。截止线之后列举即使返回也不再改登记：先取下仍待核的名字、清空待核集，晚到的命中因此不会出现在 attempted 之后。
  if (reg.pending.size > 0) {
    const deadline = s.now() + FINALIZE_RECONCILE_MS;
    await settleBy(s, s.reconcile({ deadline, outer: null }), deadline);
  }
  reg.attemptedFrozen = true;  // 此后晚到的 Create 结果只记日志：它已在下面按结果未知上报，再登记会多出不成对的 session_opened
  const attempted = [...reg.pending.keys()];
  reg.pending.clear();

  // 阶段 3：释放。截止线在写 attempted 事件之前取定，各会话的 Get / Stop 先发出，attempted 事件随后与释放并行写出：事件出口的写入
  // 可能要数秒一条，不能推迟 Stop、也不占释放截止线。截止线一到即取下各会话的结论，之后返回的调用不再改它。
  const targets = [...reg.sessions.values()];
  const frozen = { value: false };
  const deadline = s.now() + FINALIZE_RELEASE_MS;
  const releasing = settleBy(s, Promise.all(targets.map((t) => releaseOne(s, t, deadline, frozen))), deadline)
    .then(() => { frozen.value = true; });
  for (const name of attempted) await emitAttempted(s, name);
  await releasing;
  const facts: SessionClosedFact[] = targets.map((t) => ({
    sessionId: t.arn,
    name: t.name,
    release: t.confirmedAt !== null ? "confirmed" : "unconfirmed",
    observedS: observedSeconds(t),
    providerMinutes: t.providerMinutes,
  }));

  // 每会话一条 session_closed，排在它自己的 session_opened 之后。
  for (const [i, fact] of facts.entries()) {
    if (fact.release === "unconfirmed") {
      s.log(`worker: 远程访问会话 ${fact.name}（${fact.sessionId}）未能确认停止，可能仍在计费，请在设备控制台核对并手动停止`);
    }
    await targets[i].opened;
    await emit(s, () => s.events.closed(fact));
  }
  return { releaseFailed: attempted.length > 0 || facts.some((f) => f.release === "unconfirmed") };
}

/** 正常模式的 deleteSession：执行所用的远程访问会话已是 STOPPING / COMPLETED 时不调（会话已结束，再调只会报连接已关、并把端点
 *  带进错误文本）。查状态与其余 Device Farm 调用一样由阶段兜底截住，至多等 FINALIZE_GET_TIMEOUT_MS；失败或到线没有返回时按状态
 *  未知照常调用。deleteSession 至多等 DELETE_SESSION_TIMEOUT_MS，出错只记日志。 */
async function deleteAppiumSession(s: DeviceFarmSessionBlock, del: () => Promise<void>): Promise<void> {
  const current = s.registry.current;
  if (current !== null) {
    const getDeadline = s.now() + FINALIZE_GET_TIMEOUT_MS;
    const got: { info?: Awaited<ReturnType<DeviceFarmSessionBlock["getWithin"]>> } = {};
    const query = s.getWithin(current.arn, FINALIZE_GET_TIMEOUT_MS, { deadline: getDeadline, outer: null });
    await settleBy(s, query.then((v) => { got.info = v; }), getDeadline);
    const info = got.info;
    if (isStopped(info?.status)) {
      current.confirmedAt ??= s.now();
      current.providerMinutes = minutesOf(info) ?? current.providerMinutes;
      return;
    }
  }
  let work: Promise<void>;
  try {
    work = del();
  } catch (e) {
    work = Promise.reject(e);
  }
  const logged = work.catch((e: unknown) => {
    s.log(`worker: 结束 Appium 会话时出错（不影响释放远程访问会话）：${errorText(e)}`);
  });
  if (!(await settleBy(s, logged, s.now() + DELETE_SESSION_TIMEOUT_MS))) {
    s.log(`worker: 结束 Appium 会话在 ${DELETE_SESSION_TIMEOUT_MS / 1000} 秒内没有完成，继续释放远程访问会话`);
  }
}

/** 释放一个会话（Stop 规则见文件头）。frozen 置位之后不再发调用、不再改结论。 */
async function releaseOne(s: DeviceFarmSessionBlock, t: TrackedSession, deadline: number, frozen: { value: boolean }): Promise<void> {
  // 获取侧已确认停止：换台或按名找回时 Get 或 Stop 的返回体为 STOPPING / COMPLETED，或等到 RUNNING 期间读到这两个状态
  if (t.confirmedAt !== null) return;
  const bound = { deadline, outer: null };
  const confirm = (info: Awaited<ReturnType<DeviceFarmSessionBlock["getWithin"]>>): boolean => {
    if (frozen.value || !isStopped(info?.status)) return false;
    t.confirmedAt = s.now();
    t.providerMinutes = minutesOf(info) ?? t.providerMinutes;
    return true;
  };
  if (confirm(await s.getWithin(t.arn, FINALIZE_GET_TIMEOUT_MS, bound))) return;
  for (let round = 0; round < 2; round++) {
    if (frozen.value) return;
    if (round > 0 && !(await s.sleepWithin(RELEASE_RETRY_DELAY_MS, deadline))) return;
    const signal = s.boundedSignal(STOP_CALL_TIMEOUT_MS, bound);
    if (signal === null || frozen.value) return;
    try {
      if (confirm(await s.stopOnce(t, t.arn, signal))) return;
    } catch (e) {
      s.log(`worker: 停止远程访问会话 ${t.arn} 时出错，补查一次状态：${errorText(e)}`);
    }
    if (frozen.value) return;
    if (confirm(await s.getWithin(t.arn, FINALIZE_GET_TIMEOUT_MS, bound))) return;
  }
}

/** 一对 attempted 事件：结果未知、终结时仍未排除的创建尝试（ADR 0051 决策 4）。 */
async function emitAttempted(s: DeviceFarmSessionBlock, name: string): Promise<void> {
  s.log(`worker: 建会话请求（会话名 ${name}）的结果没能核实，可能留下了仍在计费的远程访问会话，请在设备控制台按这个会话名核对并手动停止`);
  await emit(s, () => s.events.opened({ sessionId: null, name, origin: "attempted" }));
  await emit(s, () => s.events.closed({ sessionId: null, name, release: "unconfirmed", observedS: null }));
}

async function emit(s: DeviceFarmSessionBlock, send: () => Promise<void>): Promise<void> {
  try {
    await send();
  } catch (e) {
    s.log(`worker: 会话事件没能写出：${errorText(e)}`);
  }
}

/** 等 work 落定，但不越过 deadline；返回是否在截止线之前落定。到线即不再等它：Device Farm 的每次调用另带不越过截止线的中止信号，
 *  这里只兜底不响应中止的调用与 deleteSession。Device Farm 客户端是无状态的 HTTP 调用，一次被放下的请求不会阻塞同一客户端上
 *  后续的 Get / Stop，所以不是 ADR 0052 被拒的「放弃挂住的命令再在同一 WebDriver 客户端上继续发命令」；deleteSession 被放下
 *  之后不再经 Appium 客户端发任何命令。 */
function settleBy(s: DeviceFarmSessionBlock, work: Promise<unknown>, deadline: number): Promise<boolean> {
  return new Promise<boolean>((resolve) => {
    const stop = new AbortController();
    const finish = (settled: boolean): void => { stop.abort(); resolve(settled); };
    work.then(() => finish(true), () => finish(true));
    s.timers.sleep(Math.max(0, deadline - s.now()), stop.signal).then(() => finish(false), () => undefined);
  });
}
