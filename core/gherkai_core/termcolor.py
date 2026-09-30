"""终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。

规则：`NO_COLOR` 为非空值或 `TERM=dumb` 时不上色；`FORCE_COLOR` 为非空值时上色（如 `| less -R`）；两者都未设时看目标流
是否为终端。`NO_COLOR` / `FORCE_COLOR` 的非空语义同 no-color.org 与 rich。

住 core 的原因：worker 日志转发（`adapters/subprocess_engine`，写 stderr）与 runtime 的 `textui`（写 stdout）要用同一份
判定，而 core 不能依赖 runtime；本模块零依赖。
"""

from __future__ import annotations

import os


def color_env_override() -> bool | None:
    """环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR` 非空）、None（由目标流决定）。"""
    if os.environ.get("NO_COLOR", "") != "" or os.environ.get("TERM") == "dumb":
        return False
    if os.environ.get("FORCE_COLOR", "") != "":
        return True
    return None


def stream_is_tty(stream) -> bool:
    try:
        return stream is not None and stream.isatty()
    except (AttributeError, ValueError):
        return False


def use_color(stream) -> bool:
    """写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。"""
    override = color_env_override()
    if override is not None:
        return override
    return stream_is_tty(stream)
