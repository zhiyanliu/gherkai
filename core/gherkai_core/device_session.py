"""设备会话的呈现辅助（ADR 0051 决策 8「scope 表头由 session_opened.device 与 scope_started.sessionId 派生」「explain 给出控制台链接」）。

core 的报告入口页（adapters/report_store/local.py）与 cli 的 render 都要用同一份：设备描述一行、会话 ARN 对应的控制台链接。
纯函数、不发请求。device 字典对 core 不透明（worker 原样报出的 platform / model / osVersion / unit），这里只按固定顺序拼人读文本。
"""
from __future__ import annotations

import re

# 远程访问会话 ARN：arn:aws:devicefarm:<region>:<account>:session:<project>/<session>/<n>（ADR 0051 决策 4 的会话血缘载体）
_SESSION_ARN = re.compile(r"^arn:aws:devicefarm:(?P<region>[a-z0-9-]+):\d{12}:session:(?P<project>[^/]+)/(?P<session>[^/]+)(?:/[^/]*)?$")


def device_label(device: dict | None) -> str | None:
    """worker 报的设备描述 → 一行人读文本（platform model osVersion，unit 另括注）；没有描述返回 None。"""
    if not isinstance(device, dict):
        return None
    bits = [str(device[k]) for k in ("platform", "model", "osVersion") if device.get(k)]
    unit = device.get("unit")
    if unit:
        bits.append(f"（{unit}）")
    return " ".join(bits) if bits else None


def console_url(session_arn: str | None) -> str | None:
    """会话 ARN → Device Farm 控制台的远程访问会话页链接；不是会话 ARN 时返回 None。

    路径按控制台「项目 → 远程访问会话」的层级拼出；首次拿到真实会话时须实际打开一次、核对链接可达（这是呈现层唯一
    不能由单测证明的事实）。
    """
    if not session_arn:
        return None
    m = _SESSION_ARN.match(session_arn)
    if m is None:
        return None
    region, project, session = m.group("region"), m.group("project"), m.group("session")
    return f"https://{region}.console.aws.amazon.com/devicefarm/home?region={region}#/mobile/projects/{project}/sessions/{session}"


def representative_device(sessions, session_id: str | None) -> dict | None:
    """scope 表头用的设备描述：代表会话（session_id）那条记录的 device；它没有时取首条带 device 的记录。"""
    for s in sessions:
        if session_id is not None and s.session_id == session_id and s.device:
            return s.device
    for s in sessions:
        if s.device:
            return s.device
    return None
