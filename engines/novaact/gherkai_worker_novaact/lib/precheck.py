"""建会话前的自检（ADR 0049 决策 7；ADR 0024「job 行的结构版本与固定键集」）：先核 job 行的 schemaVersion，再用与能力自述同一份
`targets` 核对 Job 携带的测试目标与墙钟预算。

结构版本不等于本 worker 认的（含缺键）、目标不在 targets 里、墙钟预算超过该目标的 max_session_s，都返回一句产品语言的原因；worker 据此发
`scope_done{status: error, errorType: precheck_failed, message}`、不发 scope_started、零会话费用退出（ADR 0051 决策 4 的执行前失败）。
纯函数、不读 env、不建会话。job 行的键集固定（target 恒为对象、桌面也写 desktop/web），缺键不再当桌面：那是命令行工具与 worker 版本不一致的信号。
"""
from __future__ import annotations

# 本 worker 认的 worker↔core 协议版本（ADR 0024）：一个数、两个方向各带——能力自述写进 schema_version、job 行核 schemaVersion；
# 与 core 的 wire.PROTOCOL_SCHEMA_VERSION 同值，由 engines/fixtures/job-lines.json 的 golden 钉住。
PROTOCOL_SCHEMA_VERSION = 1

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


def _spaced(label: str) -> str:
    """名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」），全中文的名称原样；与命令行工具同一规则。"""
    head = " " if label[:1].isascii() and label[:1].isalnum() else ""
    tail = " " if label[-1:].isascii() and label[-1:].isalnum() else ""
    return f"{head}{label}{tail}"


def _num(v) -> str:
    """秒数的写法：整数值不带小数点（1500 而不是 1500.0），其余按原值；与 Midscene 侧的插值结果一致。"""
    return str(int(v)) if float(v).is_integer() else str(v)


def precheck_schema(job: dict) -> str | None:
    """job 行的结构版本不等于本 worker 认的（含缺键）→ 拒绝原因（产品语言）；None 表示通过。"""
    found = job.get("schemaVersion")
    if found != PROTOCOL_SCHEMA_VERSION:
        shown = "缺失" if found is None else str(found)
        return (f"这个 job 的格式版本是 {shown}，这个 worker 认的是 {PROTOCOL_SCHEMA_VERSION}：命令行工具与 worker 的版本不一致，"
                f"请把两者装成同一版本（云端用与命令行工具同版本的 worker 镜像）。")
    return None


def precheck_job(job: dict, targets) -> str | None:
    """建会话前的全部自检：结构版本先于目标与预算。返回拒绝原因；None 表示通过。"""
    return precheck_schema(job) or precheck_target(job, targets)


def precheck_target(job: dict, targets) -> str | None:
    """返回拒绝原因（产品语言）；None 表示通过。target 须为对象（键集固定、桌面也写 desktop/web）。"""
    target = job.get("target")
    if not isinstance(target, dict):
        return "这个 job 没有带测试目标：命令行工具与 worker 的版本不一致，请把两者装成同一版本。"
    device = target.get("device")
    ui_kind = target.get("uiKind")
    entry = next((t for t in targets if t.get("device") == device), None)
    if entry is None or ui_kind not in entry.get("ui_kinds", []):
        return (f"这个 worker 不支持在{_spaced(target_label(device, ui_kind))}上执行测试（它支持：{supported_label(targets)}）。"
                f"请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。")
    limit = entry.get("max_session_s")
    timeout_s = job.get("timeoutS")
    if limit is not None and isinstance(timeout_s, (int, float)) and timeout_s > limit:
        return (f"这个 job 的墙钟预算 {_num(timeout_s)} 秒超过了{_spaced(target_label(device, ui_kind))}的会话上限 {_num(limit)} 秒。"
                f"请调低这个 scope 的 @timeout 或 --default-job-timeout。")
    return None
