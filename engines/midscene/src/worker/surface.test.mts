// 界面接缝契约里唯一有运行期行为的部分：执行异常归类标记的读写（ADR 0052 决策 6「执行异常的归类由守卫带给 runStep」）。
// 运行：npm test（node --import tsx --test "src/**/*.test.mts"）。接口与类型本身由 `npm run build` 的类型检查守住。
//
// 锁住的是 runStep 依赖的几条读法：标记挂上后原样读回、不改异常对外的文本与可枚举键；沿 cause 链向内找，最外层的标记优先
// （执行窗口把守卫记下的归类重新挂到 Midscene 包装后的异常上时，读到的必须是这一层）；不认封闭集合之外的类别；
// 抛出物不是可扩展的 Error 时包成一个新的 Error 再挂，原抛出物留在 cause 里。另外锁住标记上「会话已确认仍为 RUNNING」这项
// 事实的读写：只认 true、没有时读回的对象不带这个键，再挂一次不带它的标记即清除（驱动适配器据它决定能否按驱动文本再归类）。
import { test } from "node:test";
import assert from "node:assert";
import {
  STEP_ERROR_TYPES, attachClassification, readClassification, type StepClassification, type StepFailure,
} from "./surface.mjs";

const lost: StepFailure = { errorType: "session_lost", message: "远程访问会话在执行中途结束" };
const unknownResult: StepFailure = { errorType: "engine_error", message: "设备在等待时间内没有回应，这一步可能已执行也可能未执行" };

test("attachClassification / readClassification：挂上后原样读回，返回同一个异常对象", () => {
  const e = new Error("UND_ERR_CLOSED");
  const marked = attachClassification(e, lost);
  assert.strictEqual(marked, e);
  assert.deepEqual(readClassification(marked), lost);
});

test("标记不改异常的 message、name 与可枚举键（日志与 errorText 的输出不变）", () => {
  const e = Object.assign(new Error("socket hang up"), { code: "ECONNRESET" });
  const before = { keys: Object.keys(e), json: JSON.stringify(e), message: e.message, name: e.name };
  attachClassification(e, unknownResult);
  assert.deepEqual({ keys: Object.keys(e), json: JSON.stringify(e), message: e.message, name: e.name }, before);
});

test("读回的是副本：改写读回的对象或传入的对象都不影响异常上已挂的标记", () => {
  const input: StepFailure = { ...lost };
  const e = attachClassification(new Error("x"), input);
  input.message = "改过";
  const first = readClassification(e)!;
  first.message = "也改过";
  assert.deepEqual(readClassification(e), lost);
});

test("再次挂标记覆盖前一次（同一异常只带一个归类）", () => {
  const e = attachClassification(new Error("x"), unknownResult);
  attachClassification(e, lost);
  assert.deepEqual(readClassification(e), lost);
});

test("没有标记的异常与非对象抛出物读回 null", () => {
  assert.equal(readClassification(new Error("plain")), null);
  for (const v of [undefined, null, "boom", 42, true]) assert.equal(readClassification(v), null);
});

test("沿 cause 链向内找：标记挂在内层异常上也能读到", () => {
  const inner = attachClassification(new Error("guard"), lost);
  const outer = new Error("task runner is in error state", { cause: new Error("wrapped", { cause: inner }) });
  assert.deepEqual(readClassification(outer), lost);
});

test("内外两层都有标记时取最外层（执行窗口重新挂上的那一个）", () => {
  const inner = attachClassification(new Error("guard"), { errorType: "capability_unavailable", message: "内层" });
  const outer = attachClassification(new Error("midscene", { cause: inner }), lost);
  assert.deepEqual(readClassification(outer), lost);
});

test("cause 链成环或过深不会死循环：有界查找，找不到即 null", () => {
  const a: Error & { cause?: unknown } = new Error("a");
  const b: Error & { cause?: unknown } = new Error("b", { cause: a });
  a.cause = b;
  assert.equal(readClassification(a), null);
  let deep: Error = attachClassification(new Error("最内层"), lost);
  for (let i = 0; i < 20; i++) deep = new Error(`第 ${i} 层`, { cause: deep });
  assert.equal(readClassification(deep), null);
});

test("封闭集合之外的类别与缺消息的标记都不认（读回 null）", () => {
  const forged = attachClassification(new Error("x"), { errorType: "network_error", message: "m" } as unknown as StepFailure);
  assert.equal(readClassification(forged), null);
  const noMessage = attachClassification(new Error("y"), { errorType: "engine_error" } as unknown as StepFailure);
  assert.equal(readClassification(noMessage), null);
});

test("封闭集合恰为三类：会话丢失、执行出错、设备不提供所需能力", () => {
  assert.deepEqual([...STEP_ERROR_TYPES].sort(), ["capability_unavailable", "engine_error", "session_lost"]);
});

test("抛出物不是可扩展的 Error（字符串、冻结的异常、裸对象）时包成新 Error 挂标记，原物留在 cause", () => {
  const fromString = attachClassification("boom", lost);
  assert.ok(fromString instanceof Error);
  assert.equal(fromString.message, lost.message);
  assert.equal((fromString as Error & { cause?: unknown }).cause, "boom");
  assert.deepEqual(readClassification(fromString), lost);

  const frozen = Object.freeze(new Error("frozen"));
  const fromFrozen = attachClassification(frozen, lost);
  assert.notStrictEqual(fromFrozen, frozen);
  assert.equal((fromFrozen as Error & { cause?: unknown }).cause, frozen);
  assert.deepEqual(readClassification(fromFrozen), lost);

  const plain = { code: "ECONNRESET" };
  const fromPlain = attachClassification(plain, unknownResult);
  assert.ok(fromPlain instanceof Error);
  assert.equal((fromPlain as Error & { cause?: unknown }).cause, plain);
  assert.deepEqual(readClassification(fromPlain), unknownResult);
});

// ---- 会话已确认仍为 RUNNING 的事实（ADR 0051 决策 4「仍为 RUNNING 时才允许匹配两条实测过的驱动错误文本」）----

const knownFailure: StepFailure = { errorType: "engine_error", message: "设备命令执行失败：unknown error" };

test("会话已确认仍为 RUNNING 的事实随标记原样读回", () => {
  const confirmed: StepClassification = { ...knownFailure, sessionRunningConfirmed: true };
  const e = attachClassification(new Error("unknown error"), confirmed);
  assert.deepEqual(readClassification(e), confirmed);
});

test("没有这项事实的标记读回的对象不带这个键（会话状态没查过或查询失败的结果已知失败）", () => {
  const e = attachClassification(new Error("unknown error"), knownFailure);
  const mark = readClassification(e)!;
  assert.deepEqual(mark, knownFailure);
  assert.ok(!("sessionRunningConfirmed" in mark));
});

test("这项事实只认 true：其它取值一律视为没有，类别与消息照常读回", () => {
  for (const forged of [false, "true", 1, null]) {
    const e = attachClassification(new Error("x"), { ...knownFailure, sessionRunningConfirmed: forged } as unknown as StepClassification);
    const mark = readClassification(e)!;
    assert.deepEqual(mark, knownFailure, JSON.stringify(forged));
    assert.ok(!("sessionRunningConfirmed" in mark), JSON.stringify(forged));
  }
});

test("再挂一次不带这项事实的标记即清除它（驱动适配器改归类后的标记不再带着它）", () => {
  const e = attachClassification(new Error("unable to resolve Intent"), { ...knownFailure, sessionRunningConfirmed: true });
  attachClassification(e, { errorType: "capability_unavailable", message: "被测应用未处理该地址" });
  assert.deepEqual(readClassification(e), { errorType: "capability_unavailable", message: "被测应用未处理该地址" });
});

test("读回的事实是副本的一部分：改写读回的对象不影响异常上的标记", () => {
  const e = attachClassification(new Error("x"), { ...knownFailure, sessionRunningConfirmed: true });
  const first = readClassification(e)! as { sessionRunningConfirmed?: unknown };
  delete first.sessionRunningConfirmed;
  assert.equal(readClassification(e)?.sessionRunningConfirmed, true);
});
