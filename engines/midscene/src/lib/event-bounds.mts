// 发出事件之前对说明与设备描述的截断（ADR 0024「字段语义」节「单条事件的大小」条）。
//
// 云端的每条事件是 events 表里的一条记录，单条至多 400KB，超出即写不进表、这一步的判定丢失；本机的专用 fd 与云端的 events 表
// 用同一条规则。与 Nova worker 的 `lib/event_bounds.py` 规则相同（另一种语言，不能共用），用例两侧同读
// engines/fixtures/event-truncation-cases.json。规则：
//   - step_done 与 scope_done 的 message 截到 MESSAGE_MAX_BYTES 之内；device.model 与 device.osVersion 各截到 DEVICE_FIELD_MAX_BYTES
//     之内，不论事件类型（协议里只有 session_opened 带 device）。别的事件与别的字段不动，值为 null / undefined、缺键或 device 不是
//     对象（含数组）的保持原样；
//   - 按 UTF-8 字节数计、截在字符边界上；孤立的代理码元按 U+FFFD 编码（Node 的 utf8 编码），返回的文字里因此也是 U+FFFD，不截断时
//     同样如此；
//   - 来源不是字符串的先经 String() 转成字符串；
//   - 先脱敏再截断：截在凭据中间会让脱敏规则认不出它（同 ADR 0042 决策一「一行化规则」第 4 步，脱敏规则见 ADR 0035 决策 5）。
//     要不要截断、要不要写日志都按脱敏之后的长度判断：脱敏可能让文字变短（`用户:口令@` 换成 `***@`），也可能变长（短于 3 个字符的
//     参数值换成 `***`）；
//   - 截断之后再脱敏一次、按结果核对长度：截断点落在已盖住的参数值（`=***`）或端点令牌（`/remote-endpoint/***`）中间时，事件出口
//     对整行的脱敏会把尾部补回 `***`，最多加长 3 字节。这里逐字节后退，取补回之后仍在上限之内的最长前缀，所以出口写出的值不超限；
//   - message 被截断时，截断之前的完整文字（已脱敏）经调用方传入的日志函数写进 worker 日志。
//
// 调用方：EventSink.emit 对每条事件执行一次（两种通道共用的唯一出口，保证不漏）；runStep 在产 evidence 之前也执行一次，使
// evidence.json 冗余记下的说明与 step_done 的一致。已在上限之内且已脱敏的值再经一次结果不变，所以出口那一次不会重复写日志。
// 按字节截断的 truncateUtf8 另供原始控件树的写盘出口使用（device/surface.mts 的 writePageSourceFile）。
import { redactSecrets } from "./redact.mjs";

export const MESSAGE_MAX_BYTES = 8192;
export const DEVICE_FIELD_MAX_BYTES = 255;

const MESSAGE_EVENTS = new Set(["step_done", "scope_done"]);
const DEVICE_FIELDS = ["model", "osVersion"] as const;  // 只截这两项（ADR 0024 点名）；unit 等别的设备字段不动

/** end 之前最近的字符起始字节位置（end 处是续字节时后退）。 */
function charStart(bytes: Buffer, end: number): number {
  let i = end;
  while (i > 0 && (bytes[i] & 0xc0) === 0x80) i--;
  return i;
}

/** 按 UTF-8 字节截断，不切断多字节字符。 */
export function truncateUtf8(text: string, maxBytes: number): { bytes: Buffer; truncated: boolean } {
  const all = Buffer.from(text, "utf-8");
  if (all.length <= maxBytes) return { bytes: all, truncated: false };
  return { bytes: all.subarray(0, charStart(all, maxBytes)), truncated: true };
}

/** 把一个值转成字符串、脱敏，再截到 maxBytes 个 UTF-8 字节之内（规则见模块头）。 */
export function boundText(value: unknown, maxBytes: number): string {
  const data = Buffer.from(redactSecrets(typeof value === "string" ? value : String(value)), "utf-8");
  if (data.length <= maxBytes) return data.toString("utf-8");
  let end = maxBytes;
  for (;;) {
    end = charStart(data, end);
    const out = redactSecrets(data.subarray(0, end).toString("utf-8"));
    if (Buffer.byteLength(out, "utf-8") <= maxBytes) return out;
    end -= 1;
  }
}

/** 返回截断之后的事件（浅拷贝，不改传入的对象；device 改动时另拷一份）。message 被截断时经 log 写一行完整说明。 */
export function boundEvent(event: Record<string, unknown>, log: (msg: string) => void): Record<string, unknown> {
  const out: Record<string, unknown> = { ...event };
  const message = event.message;
  if (MESSAGE_EVENTS.has(event.type as string) && message !== null && message !== undefined) {
    const full = redactSecrets(typeof message === "string" ? message : String(message));
    out.message = boundText(full, MESSAGE_MAX_BYTES);
    const size = Buffer.byteLength(full, "utf-8");
    if (size > MESSAGE_MAX_BYTES) {
      log(`worker: ${where(event)}的说明长 ${size} 字节，超过 ${MESSAGE_MAX_BYTES} 字节的上限，上报的说明只保留开头部分；完整说明：${full}`);
    }
  }
  const device = event.device;
  if (typeof device === "object" && device !== null && !Array.isArray(device)) {
    const bounded: Record<string, unknown> = { ...(device as Record<string, unknown>) };
    for (const key of DEVICE_FIELDS) {
      if (bounded[key] !== null && bounded[key] !== undefined) bounded[key] = boundText(bounded[key], DEVICE_FIELD_MAX_BYTES);
    }
    out.device = bounded;
  }
  return out;
}

function where(event: Record<string, unknown>): string {
  if (event.type === "step_done") return `scenario ${String(event.scenarioId)} 的 step ${String(event.stepIndex)} `;
  return `scope ${String(event.scopeId)} `;
}
