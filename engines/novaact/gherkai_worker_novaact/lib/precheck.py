"""建会话前的自检（ADR 0049 决策 7）：用与能力自述同一份 `targets` 核对 Job 携带的测试目标与墙钟预算。

目标不在 targets 里，或墙钟预算超过该目标的 max_session_s，即返回一句产品语言的原因；worker 据此发
`scope_done{status: error, errorType: precheck_failed, message}`、不发 scope_started、零会话费用退出（ADR 0051 决策 4 的执行前失败）。
纯函数、不读 env、不建会话；Job 缺 target 即桌面网页（1.5 之前的 CLI 不写该键，ADR 0024 可选键）。
"""
from __future__ import annotations

_DEVICE_LABEL = {"desktop": "桌面", "android": "Android", "ios": "iOS"}
_UI_KIND_LABEL = {"web": "网页", "app": "应用"}


def target_label(device: str, ui_kind: str) -> str:
    """(device, ui_kind) → 「桌面网页」「iOS 应用」这类名称（产品语言，与命令行工具的呈现同一口径）。"""
    d = _DEVICE_LABEL.get(device, device)
    k = _UI_KIND_LABEL.get(ui_kind, ui_kind)
    return f"{d}{k}" if device == "desktop" else f"{d} {k}"


def supported_label(targets) -> str:
    names = [target_label(t["device"], k) for t in targets for k in t["ui_kinds"]]
    return "、".join(names) if names else "无"


def precheck_target(job: dict, targets) -> str | None:
    """返回拒绝原因（产品语言）；None 表示通过。"""
    target = job.get("target") or {}
    device = target.get("device", "desktop")
    ui_kind = target.get("uiKind", "web")
    entry = next((t for t in targets if t.get("device") == device), None)
    if entry is None or ui_kind not in entry.get("ui_kinds", []):
        return (f"这个 worker 不支持在{target_label(device, ui_kind)}上执行测试（它支持：{supported_label(targets)}）。"
                f"请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。")
    limit = entry.get("max_session_s")
    timeout_s = job.get("timeoutS")
    if limit is not None and isinstance(timeout_s, (int, float)) and timeout_s > limit:
        return (f"这个 job 的墙钟预算 {timeout_s:g} 秒超过了{target_label(device, ui_kind)}的会话上限 {limit:g} 秒。"
                f"请调低这个 scope 的 @timeout 或 --default-job-timeout。")
    return None
