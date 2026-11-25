"""发出事件之前对说明与设备描述的截断（ADR 0024「字段语义」节「单条事件的大小」条）。

云端的每条事件是 events 表里的一条记录，单条至多 400KB，超出即写不进表、这一步的判定丢失；本机的专用 fd 与云端的 events 表
用同一条规则。与 Midscene worker 的 `lib/event-bounds.mts` 规则相同（另一种语言，不能共用），用例两侧同读
`engines/fixtures/event-truncation-cases.json`。规则：

- `step_done` 与 `scope_done` 的 `message` 截到 `MESSAGE_MAX_BYTES` 之内；`device.model` 与 `device.osVersion` 各截到
  `DEVICE_FIELD_MAX_BYTES` 之内，不论事件类型（协议里只有 `session_opened` 带 `device`）。别的事件与别的字段不动，值为 None、
  缺键或 `device` 不是字典的保持原样。
- 按 UTF-8 字节数计、截在字符边界上；孤立的代理码元按 U+FFFD 编码（与 Node 的 utf8 编码一致），返回的文字里因此也是 U+FFFD，
  不截断时同样如此。
- 来源不是字符串的先经 `str()` 转成字符串。
- 先脱敏再截断：截在凭据中间会让脱敏规则认不出它（同 ADR 0042 决策一「一行化规则」第 4 步，脱敏规则见 ADR 0035 决策 5）。
  要不要截断、要不要写日志都按脱敏之后的长度判断：脱敏可能让文字变短（`用户:口令@` 换成 `***@`），也可能变长（短于 3 个字符的
  参数值换成 `***`）。
- 截断之后再脱敏一次、按结果核对长度：截断点落在已盖住的参数值（`=***`）或端点令牌（`/remote-endpoint/***`）中间时，事件出口
  对整行的脱敏会把尾部补回 `***`，最多加长 3 字节。这里逐字节后退，取补回之后仍在上限之内的最长前缀，所以出口写出的值不超限。
- `message` 被截断时，截断之前的完整文字（已脱敏）经调用方传入的日志函数写进 worker 日志。

调用方：`EventSink.emit` 对每条事件执行一次（两种通道共用的唯一出口，保证不漏）；有 AI 调用的 step 在产 evidence 之前也执行
一次，使 evidence.json 冗余记下的说明与 `step_done` 的一致（`run_scope._emit_step_done`）。已在上限之内且已脱敏的值再经一次
结果不变，所以出口那一次不会重复写日志。
"""
from __future__ import annotations

from typing import Callable

from gherkai_worker_novaact.lib.redact import redact_secrets

MESSAGE_MAX_BYTES = 8192
DEVICE_FIELD_MAX_BYTES = 255

_MESSAGE_EVENTS = frozenset({"step_done", "scope_done"})
_DEVICE_FIELDS = ("model", "osVersion")  # 只截这两项（ADR 0024 点名）；unit 等别的设备字段不动


def utf8_bytes(text: str) -> bytes:
    """按 UTF-8 编码；孤立的代理码元按 U+FFFD 编码，与 Midscene 侧（Node 的 utf8 编码）一致。"""
    return "".join("\ufffd" if 0xD800 <= ord(ch) <= 0xDFFF else ch for ch in text).encode("utf-8")


def bound_text(value: object, max_bytes: int) -> str:
    """把一个值转成字符串、脱敏，再截到 `max_bytes` 个 UTF-8 字节之内（规则见模块头）。"""
    text = redact_secrets(value if isinstance(value, str) else str(value))
    data = utf8_bytes(text)
    if len(data) <= max_bytes:
        return data.decode("utf-8")
    end = max_bytes
    while True:
        while end > 0 and (data[end] & 0xC0) == 0x80:
            end -= 1  # 退到字符起始字节，不切断多字节字符
        out = redact_secrets(data[:end].decode("utf-8"))
        if len(out.encode("utf-8")) <= max_bytes:
            return out
        end -= 1


def bound_event(event: dict, log: Callable[[str], None]) -> dict:
    """返回截断之后的事件（浅拷贝，不改传入的字典；`device` 改动时另拷一份）。`message` 被截断时经 `log` 写一行完整说明。"""
    out = dict(event)
    kind = event.get("type")
    if kind in _MESSAGE_EVENTS and event.get("message") is not None:
        full = redact_secrets(event["message"] if isinstance(event["message"], str) else str(event["message"]))
        out["message"] = bound_text(full, MESSAGE_MAX_BYTES)
        size = len(utf8_bytes(full))
        if size > MESSAGE_MAX_BYTES:
            log(f"worker: {_where(event)}的说明长 {size} 字节，超过 {MESSAGE_MAX_BYTES} 字节的上限，上报的说明只保留开头部分；"
                f"完整说明：{full}")
    device = event.get("device")
    if isinstance(device, dict):
        bounded = dict(device)
        for key in _DEVICE_FIELDS:
            if bounded.get(key) is not None:
                bounded[key] = bound_text(bounded[key], DEVICE_FIELD_MAX_BYTES)
        out["device"] = bounded
    return out


def _where(event: dict) -> str:
    if event.get("type") == "step_done":
        return f"scenario {event.get('scenarioId')} 的 step {event.get('stepIndex')} "
    return f"scope {event.get('scopeId')} "
