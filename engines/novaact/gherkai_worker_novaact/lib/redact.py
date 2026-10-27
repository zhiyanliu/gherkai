"""工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与 `gherkai_core/redact.py`、Midscene worker
`lib/redact.mts` 三份同文。本包零 core 依赖（ADR 0024 / 0037），故复制一份而不 import；改规则三处同改，用例三份同读
`engines/fixtures/redaction-cases.json`。规则原文与字符集的理由见 core 那份的模块头。
"""
from __future__ import annotations

import re

_USERINFO = re.compile(r"(?<=://)[A-Za-z0-9._~%!$&'()*+,;=:-]+@")
# 空白用显式字符类而不是 \s、大小写折叠限 ASCII：Python 与 JS 对 \s（\x1c-\x1f、\x85、\ufeff）和非 ASCII 大小写折叠（开尔文符号 K 对 k）
# 的语义不同，三份实现要给同一输入同一结果，就不能依赖方言各自的缺省。
_QUERY_SECRET = re.compile(
    r"((?:[?&]|&amp;)(?:X-Amz-Signature|X-Amz-Security-Token|X-Amz-Credential|gherkai_tunnel_token)=)[^&\t\n\r\f\v \"#\\<]*",
    re.IGNORECASE | re.ASCII,
)
_ENDPOINT_TOKEN = re.compile(r"(/remote-endpoint/)[^/?#@\t\n\r\f\v \"\\]+")
MASK = "***@"
SECRET_MASK = "***"


def redact_secrets(text: str | None) -> str | None:
    """三条规则依次作用于一段文本；None 原样返回。"""
    if text is None:
        return None
    out = _USERINFO.sub(MASK, text)
    out = _QUERY_SECRET.sub(lambda m: m.group(1) + SECRET_MASK, out)
    return _ENDPOINT_TOKEN.sub(lambda m: m.group(1) + SECRET_MASK, out)
