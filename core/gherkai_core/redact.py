"""工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则、三份同文实现。

三份同文实现（本文件、Nova worker `lib/redact.py`、Midscene worker `lib/redact.mts`）：Nova worker 零 core 依赖、
Midscene 是另一种语言，故不能共用一份；改规则要三处同改，用例三份同读 `engines/fixtures/redaction-cases.json`。

- 规则 ①：`scheme://userinfo@host` 的 userinfo 段换成 `***`。只作用于 `://` 之后、`@` 之前由 RFC 3986 userinfo 字符
  （字母数字与 `._~%!$&'()*+,;=:-`）组成的一段，所以对已序列化的 JSON 行安全（不含双引号与反斜杠），对中文叙述也安全
  （不含中文与全角标点，「地址，用户邮箱@」不会被误吞）。不含 `://` 的 `用户:口令@主机` 形态不处理（已知残余，见 ADR）。
- 规则 ②：封闭名单里的查询参数（`X-Amz-Signature`、`X-Amz-Security-Token`、`X-Amz-Credential`、`gherkai_tunnel_token`，参数名不区分
  大小写）的值换成 `***`：参数名前是 `?`、`&` 或 XML 实体转义形态的 `&amp;`，值到下一个 `&` 或遇到空白、`"`、`#`、`\\`、`<` 为止
  （不含引号与反斜杠，所以同样能作用在已序列化的 JSON 行上）。`X-Amz-Date` / `Expires` / `Algorithm` / `SignedHeaders` 不是凭证，
  保留明文以便诊断预签名地址过期一类问题。不按「名字含 token 或 signature 就盖」的宽泛形态——会误伤被测应用的普通参数。
- 规则 ③：Device Farm Appium 端点的路径令牌——`/remote-endpoint/` 之后的那一段（到下一个 `/`、`?`、`#`、`@`、空白、`"`、`\\` 为止）
  换成 `***`。该端点没有查询参数，凭据就是这一段。
已知残余：userinfo 里未做百分号编码、又不在 RFC 3986 userinfo 字符集里的字符（`https://u:密钥@h/`、`https://u:p|q@h/`）让那一段不被盖
——字符集取正向的 RFC 3986 userinfo 字符而不是排除式停止字符，是为了中文叙述里「地址，用户邮箱@」不被一路误吞到邮箱的 `@`；
地址里的凭据按 RFC 本就该百分号编码。
"""
from __future__ import annotations

import re
from typing import Any

_USERINFO = re.compile(r"(?<=://)[A-Za-z0-9._~%!$&'()*+,;=:-]+@")
# 空白用显式字符类而不是 \s、大小写折叠限 ASCII：Python 与 JS 对 \s（\x1c-\x1f、\x85、\ufeff）和非 ASCII 大小写折叠（开尔文符号 K 对 k）
# 的语义不同，三份实现要给同一输入同一结果，就不能依赖方言各自的缺省。
_QUERY_SECRET = re.compile(
    r"((?:[?&]|&amp;)(?:X-Amz-Signature|X-Amz-Security-Token|X-Amz-Credential|gherkai_tunnel_token)=)[^&\t\n\r\f\v \"#\\<]*",
    re.IGNORECASE | re.ASCII,
)
_ENDPOINT_TOKEN = re.compile(r"(/remote-endpoint/)[^/?#@\t\n\r\f\v \"\\]+")
MASK = "***@"  # 规则 ① 的替换形态（沿用 pip / git 的显示惯例）
SECRET_MASK = "***"


def redact_secrets(text: str | None) -> str | None:
    """三条规则依次作用于一段文本；None 原样返回。
    `https://u:p@host/x` → `https://***@host/x`；`?gherkai_tunnel_token=T` → `?gherkai_tunnel_token=***`；
    `/remote-endpoint/<令牌>/wd/hub` → `/remote-endpoint/***/wd/hub`。"""
    if text is None:
        return None
    out = _USERINFO.sub(MASK, text)
    out = _QUERY_SECRET.sub(lambda m: m.group(1) + SECRET_MASK, out)
    return _ENDPOINT_TOKEN.sub(lambda m: m.group(1) + SECRET_MASK, out)


def redact_deep(obj: Any) -> Any:
    """递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。"""
    if isinstance(obj, str):
        return redact_secrets(obj)
    if isinstance(obj, dict):
        return {k: redact_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_deep(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(redact_deep(v) for v in obj)
    return obj
