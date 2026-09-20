// 失败原因的一行有界文本（ADR 0042 决策一映射表 `act.error` / 决策三 `step_done.message`）——两处同一
// 规则，故规则住一处。Nova 引擎 run_scope.py 的 `_error_text` 是其对称版，两侧必须格式相同（同一份 feature
// 在两个引擎上运行，`explain` 与报告页的「原因」不该一侧一行、另一侧上千字符）。
//
// 规则：取首个非空行 → 折叠内部空白 → 封顶 `ERROR_TEXT_MAX` 个**码点**（不是码元，见下）。**为什么要压**：Playwright / Midscene
// 的异常 `.message` 惯常拖着多行 call log，SDK 的 `errorMessage` 同理；整段进 message 会把 run 的 step 行、
// `explain` 的「原因」与判定明细 JSON 撑成一条超长行（下游只折不截：报告页原样进 HTML）。message 是一句
// 原因、不是堆栈——完整异常留在 worker 日志里。
const ERROR_TEXT_MAX = 300;

/** 多行文本 → 一行有界原因。非字符串按 `String()` 取值；无内容 → 空串（由调用方决定空值语义）。 */
export function oneLineError(text: unknown): string {
  const raw = typeof text === "string" ? text : text === undefined || text === null ? "" : String(text);
  const first = raw.split(/\r\n|\r|\n/).find((ln) => ln.trim() !== "") ?? "";
  return [...first.trim().split(/\s+/).join(" ")].slice(0, ERROR_TEXT_MAX).join("");  // 按码点截（同 Nova 的 [:300]）：按码元截会切出孤立代理项，下游 utf-8 落盘即抛
}

/** 异常 → 一行「类型: 信息」。信息为空只留类型；连 `name` 都没有的抛出物（字符串/裸对象）整体压成一行。 */
export function errorText(e: unknown): string {
  const o = (e ?? {}) as { name?: unknown; message?: unknown };
  const name = typeof o.name === "string" ? o.name.trim() : "";
  const first = oneLineError(typeof o.message === "string" ? o.message : name === "" ? e : "");
  if (name === "") return first === "" ? "Error" : first;
  return first === "" ? name : `${name}: ${first}`;
}
