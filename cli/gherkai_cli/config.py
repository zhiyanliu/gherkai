"""项目配置文件 gherkai.toml：定位、读取与形态校验（ADR 0053）。

只有运行侧 CLI 读它（决策 1）。本模块只产出**原始配置**（按节分开的值与来源路径）；把它合成到选项与环境变量之间
（决策 2 的取值顺序）是 `__main__._apply_project_config` 的事——`[common]` / `[cloud]` 的键是否合法取决于 argparse 的
选项面，由调用方把允许的键集传进来，本模块不 import argparse、不知道命令。
路径类值（决策 2）相对配置文件所在目录：`[apps]` 的 `file` 在这里绝对化；`steps-dir` 与 `report-dir` 由调用方经
`ProjectConfig.resolve_path` 绝对化（`report-dir` 只在本机后端下是路径，云端是桶内键前缀、原样使用，后端在本模块之外才知道）。
所有 `ConfigError` 的消息都是给使用方看的整句（点名文件、节、键与改法），调用点直接打印后以退出码 2 结束。
"""
from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from gherkai_core.model import MAX_ACQUIRE_TIMEOUT_S

CONFIG_FILE_NAME = "gherkai.toml"
CONFIG_ENV = "GHERKAI_CONFIG"
SECTIONS = ("common", "cloud", "devices", "apps")
# [devices] 顶层键与平台子表键（ADR 0053 决策 3 键表；护栏 test_project_config 逐项对照）
DEVICES_KEYS = ("billing-method", "acquire-timeout-s", "project-arn", "app-bucket")
DEVICE_PLATFORMS = ("android", "ios")
PLATFORM_KEYS = ("arn", "os-version", "billing-method")
BILLING_METHODS = ("METERED", "UNMETERED")
# [apps.<别名>.<平台>] 条目：安装包 file 加该平台的应用标识键（Android 包名 / iOS bundle id），两者都必须显式给出
APP_ID_KEY = {"android": "package", "ios": "bundle-id"}
_OS_VERSION_RE = re.compile(r"^\d+(\.\d+)*$")


class ConfigError(ValueError):
    """配置文件不可用（找不到显式给出的文件、不是合法 TOML、不认识的节或键、取值形态不对）。消息即给使用方看的整句。"""


@dataclass(frozen=True)
class DevicePlatformConfig:
    """`[devices.<平台>]`：arn 与 os-version 恰给一个；billing-method 覆盖 `[devices]` 顶层的值。"""

    arn: str | None = None
    os_version: str | None = None
    billing_method: str | None = None


@dataclass(frozen=True)
class DevicesConfig:
    billing_method: str | None = None
    acquire_timeout_s: float | None = None
    project_arn: str | None = None   # 只供本机后端（ADR 0053 决策 3）
    app_bucket: str | None = None    # 只供本机后端
    platforms: dict[str, DevicePlatformConfig] = field(default_factory=dict)


@dataclass(frozen=True)
class AppPlatformConfig:
    file: Path       # 已按配置文件目录绝对化；是否存在到 plan / run 时才核对
    app_id: str      # Android 包名或 iOS bundle id


@dataclass(frozen=True)
class ProjectConfig:
    """读出来的项目配置。`path` 为 None 表示没有配置文件（缺省位置不存在不算错，决策 1），四节都为空。

    `common` / `cloud` 的值保持 TOML 原始类型（str / int / float / list[str]），按选项的 argparse 类型转换与取值范围校验
    由调用方做（决策 3：非法值的报错形态与命令行上给错一致）。
    """

    path: Path | None = None
    common: dict[str, object] = field(default_factory=dict)
    cloud: dict[str, object] = field(default_factory=dict)
    devices: DevicesConfig | None = None
    apps: dict[str, dict[str, AppPlatformConfig]] = field(default_factory=dict)  # 别名 → 平台 → 条目

    @property
    def base_dir(self) -> Path | None:
        return self.path.parent if self.path is not None else None

    def resolve_path(self, value: str) -> str:
        """路径类值相对配置文件所在目录绝对化（决策 2）；没有配置文件时原样返回（不该被调到，保险起见）。"""
        if self.base_dir is None:
            return value
        return str((self.base_dir / os.path.expanduser(value)).resolve())

    def app_ids(self) -> dict[str, dict[str, str]]:
        """给 plan 层的纯数据表：别名 → 平台 → 包名或 bundle id（core 据此核对 @app，不带文件路径）。"""
        return {alias: {platform: entry.app_id for platform, entry in platforms.items()}
                for alias, platforms in self.apps.items()}


NO_CONFIG = ProjectConfig()


def locate_config(explicit: str | None, *, env: Mapping[str, str] | None = None,
                  cwd: Path | None = None) -> tuple[Path | None, str]:
    """按 `--config` > `GHERKAI_CONFIG` > 当前目录的 gherkai.toml 定位（决策 1），返回 (路径或 None, 来源说明)。

    前两层是显式给出的：文件不存在即 ConfigError（静默忽略会让「我配的为什么没生效」无从排查）。缺省位置不存在不算错。
    不向上级目录查找（monorepo 子目录里会静默拿到另一个项目的文件）。
    """
    env = os.environ if env is None else env
    cwd = Path.cwd() if cwd is None else cwd
    for raw, origin in ((explicit, "--config"), (env.get(CONFIG_ENV), f"环境变量 {CONFIG_ENV}")):
        if raw:
            path = (cwd / os.path.expanduser(raw)).resolve()
            if not path.is_file():
                raise ConfigError(f"配置文件 {path} 不存在或不是文件（来自 {origin}）")
            return path, origin
    default = (cwd / CONFIG_FILE_NAME).resolve()
    if default.is_file():
        return default, f"当前目录的 {CONFIG_FILE_NAME}"
    return None, "未使用配置文件"


def load_project_config(path: Path | None, *, common_keys: Collection[str], cloud_keys: Collection[str]) -> ProjectConfig:
    """读并校验一份 gherkai.toml。`common_keys` / `cloud_keys` 是两节各自允许的键（选项长名去掉 `--`），由调用方从 argparse 推出。"""
    if path is None:
        return NO_CONFIG
    try:
        with open(path, "rb") as fh:
            doc = tomllib.load(fh)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"配置文件 {path} 不是合法的 TOML：{e}") from None
    except OSError as e:
        raise ConfigError(f"配置文件 {path} 读不了：{e}") from None
    unknown = sorted(set(doc) - set(SECTIONS))
    if unknown:
        raise ConfigError(f"配置文件 {path} 里有不认识的节 [{unknown[0]}]；可用的节：{'、'.join(SECTIONS)}")
    return ProjectConfig(
        path=path,
        common=_option_section(doc, "common", common_keys, path),
        cloud=_option_section(doc, "cloud", cloud_keys, path),
        devices=_devices_section(doc.get("devices"), path),
        apps=_apps_section(doc.get("apps"), path),
    )


def _table(value, where: str, path: Path) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"配置文件 {path} 的 {where} 应是一个表（用 [{where.strip('[]')}] 开节），现为 {value!r}")
    return value


def _option_section(doc: dict, name: str, allowed: Collection[str], path: Path) -> dict[str, object]:
    """`[common]` / `[cloud]`：键须在允许集内；值只接受文本、数字或文本列表（可重复给的选项），其它类型在这里拒掉。"""
    raw = doc.get(name)
    if raw is None:
        return {}
    table = _table(raw, f"[{name}]", path)
    out: dict[str, object] = {}
    for key, value in table.items():
        if key not in allowed:
            raise ConfigError(f"配置文件 {path} 的 [{name}] 里有不认识的键 {key}；"
                              f"可用的键：{'、'.join(sorted(allowed)) or '（无）'}")
        if isinstance(value, bool) or not isinstance(value, (str, int, float, list)) \
                or (isinstance(value, list) and not all(isinstance(x, str) for x in value)):
            raise ConfigError(f"配置文件 {path} 的 [{name}] {key} 取值 {value!r} 类型不对：这里只接受文本、数字，或文本的列表")
        out[key] = value
    return out


def _text(value, where: str, key: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"配置文件 {path} 的 {where} {key} 须为非空文本，现为 {value!r}")
    return value


def _billing_method(value, where: str, path: Path) -> str:
    if value not in BILLING_METHODS:
        raise ConfigError(f"配置文件 {path} 的 {where} billing-method 只能是 {' 或 '.join(BILLING_METHODS)}，现为 {value!r}")
    return value


def _devices_section(raw, path: Path) -> DevicesConfig | None:
    if raw is None:
        return None
    table = _table(raw, "[devices]", path)
    allowed = set(DEVICES_KEYS) | set(DEVICE_PLATFORMS)
    for key in table:
        if key not in allowed:
            raise ConfigError(f"配置文件 {path} 的 [devices] 里有不认识的键 {key}；"
                              f"可用的键：{'、'.join(DEVICES_KEYS)}，以及平台子表 {' / '.join(f'[devices.{p}]' for p in DEVICE_PLATFORMS)}")
    billing = _billing_method(table["billing-method"], "[devices]", path) if "billing-method" in table else None
    acquire = None
    if "acquire-timeout-s" in table:
        v = table["acquire-timeout-s"]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (0 < v <= MAX_ACQUIRE_TIMEOUT_S):
            raise ConfigError(f"配置文件 {path} 的 [devices] acquire-timeout-s 须为 1 到 {MAX_ACQUIRE_TIMEOUT_S:g} 之间的秒数，现为 {v!r}")
        acquire = float(v)
    platforms: dict[str, DevicePlatformConfig] = {}
    for platform in DEVICE_PLATFORMS:
        if platform in table:
            platforms[platform] = _platform_table(table[platform], platform, path)
    return DevicesConfig(
        billing_method=billing, acquire_timeout_s=acquire,
        project_arn=_text(table["project-arn"], "[devices]", "project-arn", path) if "project-arn" in table else None,
        app_bucket=_text(table["app-bucket"], "[devices]", "app-bucket", path) if "app-bucket" in table else None,
        platforms=platforms,
    )


def _platform_table(raw, platform: str, path: Path) -> DevicePlatformConfig:
    where = f"[devices.{platform}]"
    table = _table(raw, where, path)
    for key in table:
        if key not in PLATFORM_KEYS:
            raise ConfigError(f"配置文件 {path} 的 {where} 里有不认识的键 {key}；可用的键：{'、'.join(PLATFORM_KEYS)}")
    has_arn, has_ver = "arn" in table, "os-version" in table
    if has_arn and has_ver:
        raise ConfigError(f"配置文件 {path} 的 {where} 里 arn 与 os-version 只能给一个（指定一台设备，或按系统版本挑选），现在两个都给了")
    if not has_arn and not has_ver:
        raise ConfigError(f"配置文件 {path} 的 {where} 须给 arn（指定一台设备）或 os-version（按系统版本挑选）之一")
    os_version = None
    if has_ver:
        v = table["os-version"]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            raise ConfigError(f"配置文件 {path} 的 {where} os-version = {v} 要写成字符串、加引号（os-version = \"{v}\"），"
                              f"否则会被当作数字读、版本号末尾的 0 会丢失")
        os_version = _text(v, where, "os-version", path)
        if not _OS_VERSION_RE.match(os_version):
            raise ConfigError(f"配置文件 {path} 的 {where} os-version {os_version!r} 要写成点分的版本号，如 \"18\" 或 \"18.6\"")
    return DevicePlatformConfig(
        arn=_text(table["arn"], where, "arn", path) if has_arn else None,
        os_version=os_version,
        billing_method=_billing_method(table["billing-method"], where, path) if "billing-method" in table else None,
    )


def _apps_section(raw, path: Path) -> dict[str, dict[str, AppPlatformConfig]]:
    if raw is None:
        return {}
    table = _table(raw, "[apps]", path)
    out: dict[str, dict[str, AppPlatformConfig]] = {}
    for alias, platforms in table.items():
        where = f"[apps.{alias}]"
        ptable = _table(platforms, where, path)
        entries: dict[str, AppPlatformConfig] = {}
        for platform, entry in ptable.items():
            if platform not in APP_ID_KEY:
                raise ConfigError(f"配置文件 {path} 的 {where} 下只认 {' 与 '.join(APP_ID_KEY)} 两个平台，现有 {platform}")
            ewhere = f"[apps.{alias}.{platform}]"
            etable = _table(entry, ewhere, path)
            id_key = APP_ID_KEY[platform]
            for key in etable:
                if key not in ("file", id_key):
                    raise ConfigError(f"配置文件 {path} 的 {ewhere} 里有不认识的键 {key}；可用的键：file、{id_key}")
            if "file" not in etable:
                raise ConfigError(f"配置文件 {path} 的 {ewhere} 缺 file（安装包路径，相对配置文件所在目录）")
            if id_key not in etable:
                what = "Android 包名" if platform == "android" else "iOS bundle id"
                raise ConfigError(f"配置文件 {path} 的 {ewhere} 缺 {id_key}（{what}；要显式给出，不由安装包推断）")
            file_text = _text(etable["file"], ewhere, "file", path)
            entries[platform] = AppPlatformConfig(
                file=(path.parent / os.path.expanduser(file_text)).resolve(),
                app_id=_text(etable[id_key], ewhere, id_key, path),
            )
        if not entries:
            raise ConfigError(f"配置文件 {path} 的 {where} 下至少要给一个平台的条目（[apps.{alias}.android] 或 [apps.{alias}.ios]）")
        out[alias] = entries
    return out
