// 失败原因的一行有界文本（ADR 0042 决策一映射表 `act.error` / 决策三 `step_done.message`）——两处同一
// 规则，故规则住一处。Nova 引擎 run_scope.py 的 `_one_line` / `_error_text` 是其对称版，两侧必须逐字相同（同一份 feature
// 在两个引擎上运行，`explain` 与报告页的「原因」不该一侧一行、另一侧上千字符，同一段异常文本也不该在两侧得出不同的一行）。
// 本模块是 Midscene 唯一一份一行化实现：把异常或服务端文本压成一行、嵌进其他消息的地方（桌面与设备上的会话预热失败消息里的
// 原因、设备模块的日志与消息）也调用 `oneLineError`，各处只有封顶不同（预热原因用 lib/tunnel-warmup.mts 的 `WARMUP_REASON_MAX`）。
//
// 规则按序四步（ADR 0042 决策一「一行化规则」）：分行只认 CR、LF 与 CRLF → 取首个含空白字符集 W 以外字符的行 → 行内 W 的
// 连续段折成一个空格、只去首尾的空格 → 先脱敏再按**码点**取前 N 个（不是码元，见下），截断恰在词间空格之后时去掉末尾的空格。
// **为什么要压**：Playwright / Midscene 的异常 `.message` 惯常拖着多行 call log，SDK 的 `errorMessage` 同理；整段进 message
// 会把 run 的 step 行、`explain` 的「原因」与判定明细 JSON 撑成一条超长行（下游只折不截：报告页原样进 HTML）。message 是一句
// 原因、不是堆栈——完整异常留在 worker 日志里。
import { redactSecrets } from "./redact.mjs";  // 截断前先脱敏：截在 userinfo 中间会丢掉 `@`、让出口处的规则失效（ADR 0035 决策 5）

const ERROR_TEXT_MAX = 300;

// 空白字符集 W：Python isspace 集合与 JS `\s` 集合之并，与 Nova 的字符类逐字相同。不用 `\s` / trim()：W 含 `\s` 以外的字符
// （U+001C 到 U+001F、U+0085），`\s` 的 Unicode 空格部分又随引擎所带的 Unicode 版本变化。写转义、不写字符本身：U+2028 与
// U+2029 是 JS 源码的行终止符，原样写进正则字面量即为语法错误。
const W = /[\x09-\x0d\x1c-\x20\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]/;
const W_ONLY = new RegExp(`^${W.source}*$`);
const W_RUN = new RegExp(`${W.source}+`, "g");
const W_EDGES = new RegExp(`^${W.source}+|${W.source}+$`, "g");

/** 多行文本 → 一行有界原因，封顶 `max` 个码点。非字符串按 `String()` 取值；无内容 → 空串（由调用方决定空值语义）。 */
export function oneLineError(text: unknown, max: number = ERROR_TEXT_MAX): string {
  const raw = typeof text === "string" ? text : text === undefined || text === null ? "" : String(text);
  const first = raw.split(/\r\n|\r|\n/).find((ln) => !W_ONLY.test(ln)) ?? "";
  const folded = first.replace(W_RUN, " ").replace(/^ | $/g, "");
  const out = [...redactSecrets(folded)].slice(0, max).join("");  // 按码点截：按码元截会切出孤立代理项，下游 utf-8 落盘即抛
  return out.endsWith(" ") ? out.slice(0, -1) : out;
}

/** 异常 → 一行「类型: 信息」。信息为空只留类型；连 `name` 都没有的抛出物（字符串/裸对象）整体压成一行。 */
export function errorText(e: unknown): string {
  const o = (e ?? {}) as { name?: unknown; message?: unknown };
  const name = typeof o.name === "string" ? o.name.replace(W_EDGES, "") : "";
  const first = oneLineError(typeof o.message === "string" ? o.message : name === "" ? e : "");
  if (name === "") return first === "" ? "Error" : first;
  return first === "" ? name : `${name}: ${first}`;
}
