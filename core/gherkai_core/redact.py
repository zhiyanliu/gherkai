"""隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。

三份同文实现（本文件、Nova worker `lib/redact.py`、Midscene worker `lib/redact.mts`）：Nova worker 零 core 依赖、
Midscene 是另一种语言，故不能共用一份；改规则要三处同改，测试用例三处同文。

规则只作用于 `://` 之后、`@` 之前由 RFC 3986 userinfo 字符（字母数字与 `._~%!$&'()*+,;=:-`）组成的一段，所以对已序列化的 JSON 行安全（不含引号与反斜杠），对中文叙述也安全（不含中文与全角标点，
「地址，用户邮箱@」不会被误吞）。不含 `://` 的 `用户:口令@主机` 形态不处理（已知残余，见 ADR）。
"""
from __future__ import annotations

import re
from typing import Any

_USERINFO = re.compile(r"(?<=://)[A-Za-z0-9._~%!$&'()*+,;=:-]+@")
MASK = "***@"


def redact_url_userinfo(text: str | None) -> str | None:
    """`https://u:p@host/x` → `https://***@host/x`；None 原样返回。"""
    if text is None:
        return None
    return _USERINFO.sub(MASK, text)


def redact_deep(obj: Any) -> Any:
    """递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。"""
    if isinstance(obj, str):
        return _USERINFO.sub(MASK, obj)
    if isinstance(obj, dict):
        return {k: redact_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_deep(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(redact_deep(v) for v in obj)
    return obj
