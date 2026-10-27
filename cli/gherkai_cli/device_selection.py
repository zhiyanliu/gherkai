"""设备选择与设备请求的解析（ADR 0053 决策 4、ADR 0048 决策 3、ADR 0051 决策 2）：选项 > 环境变量 > 配置文件，解析成 Job 的具名设备请求。

只有运行侧 CLI 读这些来源，解析出的具体值随 definition 走、宿主不重解析（ADR 0053 决策 1）。本模块是纯函数、不连 AWS：云端的
Device Farm 项目 ARN 由调用方读 SSM 后传入，本机的由选项 / 环境变量 / 配置文件给出。
ARN 只核对服务与资源类型段（ADR 0053 决策 4）：拦「贴错类型」这一种最常见的错（把项目 ARN 贴进设备 ARN 之类），零 AWS 调用；
设备不存在、已下架、不支持远程访问等由 worker 建会话时记 precheck_failed。
所有 `DeviceSelectionError` 的消息都是给使用方看的整句，调用点直接打印后以退出码 2 结束。
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from gherkai_core.model import DEFAULT_ACQUIRE_TIMEOUT_S, DeviceFarmRequest

from gherkai_cli.config import ProjectConfig

PLATFORM_FLAG = {"android": "--android-device-arn", "ios": "--ios-device-arn"}
PLATFORM_ENV = {"android": "GHERKAI_ANDROID_DEVICE_ARN", "ios": "GHERKAI_IOS_DEVICE_ARN"}
PROJECT_ARN_FLAG = "--device-farm-project-arn"
PROJECT_ARN_ENV = "GHERKAI_DEVICE_FARM_PROJECT_ARN"
APP_BUCKET_FLAG = "--app-bucket"
APP_BUCKET_ENV = "GHERKAI_APP_BUCKET"
_PLATFORM_LABEL = {"android": "Android", "ios": "iOS"}
# 只核 ARN 的服务段与资源类型段（ADR 0053 决策 4）：分区、区域、账号与资源 id 的形态不管——拦的是贴错类型，不是替服务商校验 ARN。
_DEVICE_ARN_RE = re.compile(r"^arn:[^:]+:devicefarm:[^:]*:[^:]*:device:.+$")
_PROJECT_ARN_RE = re.compile(r"^arn:[^:]+:devicefarm:[^:]*:[^:]*:project:.+$")
_ARN_KINDS = ((":project:", "项目 ARN"), (":devicepool:", "设备池 ARN"), (":session:", "会话 ARN"), (":device:", "设备 ARN"))


class DeviceSelectionError(ValueError):
    """设备选择或项目 ARN 不可用（没有指定、ARN 形态不对）。消息即给使用方看的整句。"""


@dataclass(frozen=True)
class DeviceSelection:
    """某个平台选哪台设备：`arn` 指定一台，`os_version` 按系统版本族挑选（二者恰一）。`source` 是产品语言的来源说明，进提示与 plan 标注。"""

    platform: str
    source: str
    arn: str | None = None
    os_version: str | None = None


def platform_label(platform: str) -> str:
    return _PLATFORM_LABEL.get(platform, platform)


def _arn_kind(arn: str) -> str | None:
    for marker, name in _ARN_KINDS:
        if marker in arn:
            return name
    return None


def check_device_arn(arn: str, *, source: str) -> None:
    """设备 ARN 的服务与资源类型段（ADR 0053 决策 4）：不对即抛，消息点名来源与贴错的类型。"""
    if _DEVICE_ARN_RE.match(arn):
        return
    kind = _arn_kind(arn)
    hint = f"这看起来是{kind}、不是设备 ARN；" if kind and kind != "设备 ARN" else ""
    raise DeviceSelectionError(f"{source}给的设备 ARN 形态不对：{hint}设备 ARN 形如 arn:aws:devicefarm:<区域>::device:<设备 id>，"
                               f"现在是 {arn!r}")


def check_project_arn(arn: str, *, source: str) -> None:
    if _PROJECT_ARN_RE.match(arn):
        return
    kind = _arn_kind(arn)
    hint = f"这看起来是{kind}、不是项目 ARN；" if kind and kind != "项目 ARN" else ""
    raise DeviceSelectionError(f"{source}给的 Device Farm 项目 ARN 形态不对：{hint}项目 ARN 形如 "
                               f"arn:aws:devicefarm:<区域>:<12 位账号>:project:<项目 id>，现在是 {arn!r}")


def resolve_device_selection(platform: str, *, flag_arn: str | None, env: Mapping[str, str],
                             config: ProjectConfig) -> DeviceSelection | None:
    """某平台的设备选择：选项 > 环境变量 > 配置文件 `[devices.<平台>]`（arn 或 os-version）；都没有返回 None（由调用方按命令处置：
    run / submit 以退出码 2 结束，plan 只标注与警告，ADR 0053 决策 4）。命令行与环境变量只接受 ARN。"""
    if flag_arn:
        check_device_arn(flag_arn, source=f"选项 {PLATFORM_FLAG[platform]} ")
        return DeviceSelection(platform, PLATFORM_FLAG[platform], arn=flag_arn)
    env_arn = env.get(PLATFORM_ENV[platform])
    if env_arn:
        check_device_arn(env_arn, source=f"环境变量 {PLATFORM_ENV[platform]} ")
        return DeviceSelection(platform, f"环境变量 {PLATFORM_ENV[platform]}", arn=env_arn)
    sub = config.devices.platforms.get(platform) if config.devices is not None else None
    if sub is None:
        return None
    where = f"配置文件 {config.path} 的 [devices.{platform}]"
    if sub.arn is not None:
        check_device_arn(sub.arn, source=f"{where} 的 arn ")
        return DeviceSelection(platform, f"{where} arn", arn=sub.arn)
    return DeviceSelection(platform, f"{where} os-version", os_version=sub.os_version)


def unspecified_message(platform: str) -> str:
    """ADR 0053 决策 4 的用户可见消息：有该平台的设备 scope，却没有任何来源指定设备。"""
    return (f"这个 run 里有在 {platform_label(platform)} 设备上执行的 scope，但没有指定用哪台设备。"
            f"请在 gherkai.toml 的 [devices.{platform}] 里给出 arn 或 os-version，或用 {PLATFORM_FLAG[platform]} 指定。")


def selection_label(sel: DeviceSelection | None, platform: str) -> str:
    """plan 标注用的一句（产品语言）：原样展示 ARN 或筛选条件与来源；未指定时说明 run / submit 会拒绝。"""
    if sel is None:
        return f"设备 {platform}：未指定（run / submit 会以退出码 2 结束；在 gherkai.toml 的 [devices.{platform}] 给出 arn 或 os-version，或用 {PLATFORM_FLAG[platform]} 指定）"
    if sel.arn is not None:
        return f"设备 {platform}：{sel.arn}（来自 {sel.source}）"
    return (f"设备 {platform}：按系统版本 {sel.os_version} 挑选（来自 {sel.source}；命中 {sel.os_version} 与 {sel.os_version}.x，"
            f"写得越全、实际分到的设备越固定）")


def selection_to_dict(sel: DeviceSelection | None) -> dict | None:
    """plan --json 的 `devices.<平台>`：指定一台时 `{arn, source}`，按版本挑选时 `{os_version, source}`，未指定 null。"""
    if sel is None:
        return None
    if sel.arn is not None:
        return {"arn": sel.arn, "source": sel.source}
    return {"os_version": sel.os_version, "source": sel.source}


def billing_method_for(platform: str, config: ProjectConfig) -> str:
    """计费方式：平台子表 > [devices] 顶层 > METERED（ADR 0053 决策 3）。"""
    devices = config.devices
    if devices is not None:
        sub = devices.platforms.get(platform)
        if sub is not None and sub.billing_method is not None:
            return sub.billing_method
        if devices.billing_method is not None:
            return devices.billing_method
    return "METERED"


def acquire_timeout_for(config: ProjectConfig) -> float:
    """获取预算：配置文件 [devices] acquire-timeout-s > 内建默认（ADR 0051 决策 2；上界在读配置时已核）。"""
    if config.devices is not None and config.devices.acquire_timeout_s is not None:
        return config.devices.acquire_timeout_s
    return DEFAULT_ACQUIRE_TIMEOUT_S


def resolve_local_project_arn(*, flag_arn: str | None, env: Mapping[str, str], config: ProjectConfig) -> tuple[str, str]:
    """本机后端的 Device Farm 项目 ARN：选项 > 环境变量 > 配置文件 [devices] project-arn（ADR 0053 决策 3）；缺失即抛。返回 (ARN, 来源)。"""
    if flag_arn:
        check_project_arn(flag_arn, source=f"选项 {PROJECT_ARN_FLAG} ")
        return flag_arn, PROJECT_ARN_FLAG
    env_arn = env.get(PROJECT_ARN_ENV)
    if env_arn:
        check_project_arn(env_arn, source=f"环境变量 {PROJECT_ARN_ENV} ")
        return env_arn, f"环境变量 {PROJECT_ARN_ENV}"
    cfg_arn = config.devices.project_arn if config.devices is not None else None
    if cfg_arn:
        check_project_arn(cfg_arn, source=f"配置文件 {config.path} 的 [devices] project-arn ")
        return cfg_arn, f"配置文件 {config.path} 的 [devices] project-arn"
    raise DeviceSelectionError(
        "本机运行设备 scope 需要一个 Device Farm 项目，但没有指定：请在 gherkai.toml 的 [devices] 里给出 project-arn，"
        f"或用 {PROJECT_ARN_FLAG} / 环境变量 {PROJECT_ARN_ENV} 指定。"
    )


def account_of(arn: str) -> str:
    """ARN 的账号段（项目 ARN 的第五段）。"""
    return arn.split(":")[4]


def build_device_request(sel: DeviceSelection, *, project_arn: str, billing_method: str, acquire_timeout_s: float) -> DeviceFarmRequest:
    """把一个平台的设备选择与项目、计费、预算合成 Job 的具名设备请求（ADR 0048 决策 3）。"""
    return DeviceFarmRequest(project_arn=project_arn, device_arn=sel.arn, os_version=sel.os_version,
                             billing_method=billing_method, acquire_timeout_s=acquire_timeout_s)
