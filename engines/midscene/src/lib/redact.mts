// 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。
// 与 core `gherkai_core/redact.py`、Nova worker `lib/redact.py` 三份同文（另一种语言，不能共用）；改规则三处同改。
// 规则只作用于 `://` 之后、`@` 之前由 RFC 3986 userinfo 字符（字母数字与 `._~%!$&'()*+,;=:-`）组成的一段：
// 不含引号与反斜杠，所以对已序列化的 JSON 行安全；不含中文与全角标点，所以「地址，用户邮箱@」这类中文叙述不会被误吞。
const USERINFO = /(?<=:\/\/)[A-Za-z0-9._~%!$&'()*+,;=:-]+@/g;
export const MASK = "***@";

/** `https://u:p@host/x` → `https://***@host/x`。 */
export function redactUrlUserinfo(text: string): string {
  return text.replace(USERINFO, MASK);
}
