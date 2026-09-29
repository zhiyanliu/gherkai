"""隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。

与 `gherkai_core/redact.py`、Midscene worker `lib/redact.mts` 三份同文：本包零 core 依赖（ADR 0024 / 0037），
故复制一份而不 import；改规则三处同改。规则只作用于 `://` 之后、`@` 之前由 RFC 3986 userinfo 字符（字母数字与 `._~%!$&'()*+,;=:-`）组成的一段，
对已序列化的 JSON 行安全，对中文叙述也安全（不含中文与全角标点）。
"""
from __future__ import annotations

import re

_USERINFO = re.compile(r"(?<=://)[A-Za-z0-9._~%!$&'()*+,;=:-]+@")
MASK = "***@"


def redact_url_userinfo(text: str | None) -> str | None:
    """`https://u:p@host/x` → `https://***@host/x`；None 原样返回。"""
    if text is None:
        return None
    return _USERINFO.sub(MASK, text)
