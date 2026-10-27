// 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与 core `gherkai_core/redact.py`、Nova worker
// `lib/redact.py` 三份同文（另一种语言，不能共用）；改规则三处同改，用例三份同读 engines/fixtures/redaction-cases.json。
// 规则原文与字符集的理由见 core 那份的模块头。三个正则都带 g：只经 replace 使用，不受 lastIndex 影响（测试锁住）。
const USERINFO = /(?<=:\/\/)[A-Za-z0-9._~%!$&'()*+,;=:-]+@/g;
const QUERY_SECRET = /((?:[?&]|&amp;)(?:X-Amz-Signature|X-Amz-Security-Token|X-Amz-Credential|gherkai_tunnel_token)=)[^&\s"#\\<]*/gi;
const ENDPOINT_TOKEN = /(\/remote-endpoint\/)[^/?#@\s"\\]+/g;
export const MASK = "***@";
export const SECRET_MASK = "***";

/** 三条规则依次作用于一段文本。 */
export function redactSecrets(text: string): string {
  return text.replace(USERINFO, MASK).replace(QUERY_SECRET, `$1${SECRET_MASK}`).replace(ENDPOINT_TOKEN, `$1${SECRET_MASK}`);
}
