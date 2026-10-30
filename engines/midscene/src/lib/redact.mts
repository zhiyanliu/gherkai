// 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与 core `gherkai_core/redact.py`、Nova worker
// `lib/redact.py` 三份同文（另一种语言，不能共用）；改规则三处同改，用例三份同读 engines/fixtures/redaction-cases.json。
// 规则原文与字符集的理由见 core 那份的模块头。三个正则都带 g：只经 replace 使用，不受 lastIndex 影响（测试锁住）。
// 空白用显式字符类而不是 \s（JS 的 \s 含 \ufeff、Python 的含 \x1c-\x1f 与 \x85），/i 不带 u 标志（非 ASCII 字母不折叠到 ASCII），
// 与 Python 侧的 re.ASCII 同义：三份实现对同一输入同一结果。
const USERINFO = /(?<=:\/\/)[A-Za-z0-9._~%!$&'()*+,;=:-]+@/g;
const QUERY_SECRET = /((?:[?&]|&amp;)(?:X-Amz-Signature|X-Amz-Security-Token|X-Amz-Credential|gherkai_tunnel_token)=)[^&\t\n\r\f\v "#\\<]*/gi;
const ENDPOINT_TOKEN = /(\/remote-endpoint\/)[^/?#@\t\n\r\f\v "\\]+/g;
export const MASK = "***@";
export const SECRET_MASK = "***";

/** 三条规则依次作用于一段文本。 */
export function redactSecrets(text: string): string {
  return text.replace(USERINFO, MASK).replace(QUERY_SECRET, `$1${SECRET_MASK}`).replace(ENDPOINT_TOKEN, `$1${SECRET_MASK}`);
}

// 规则二、三的正则对象另行导出，供 WebdriverIO 日志掩码复用（device/wdio-log.mts，ADR 0051 决策 11）：那边由同一正则对象换算出
// 掩码串，不另写一份。它们带 g 标志，消费方只读 source 与 flags 或经 replace / matchAll 使用，不调 test / exec（会改 lastIndex）。
export { QUERY_SECRET, ENDPOINT_TOKEN };
