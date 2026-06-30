"""确定性 step 注册表（ADR 0022）——Nova 引擎。

test engineer 用 `@deterministic(pattern)` 把「正则模式 → handler」登记进一张表。worker 派发
每个 step 时**先查这张表**：命中走精确 handler（拿 Playwright/CDP 句柄判定、**不投票、可复现**），
未命中才落到内建 URL 导航 / AI catch-all（ADR 0020/0024）。

为什么匹配放 worker 不放 core（ADR 0022）：确定性 handler 是**引擎特定**的（碰 nova.page 这类
精确 API），匹配表跟着 handler 走最内聚；core 只解析结构 + 调度，对 step 语义无知。

角色边界（ADR 0020）：QA 永远只写自然语言（默认走 AI）；确定性 step 由 test engineer 在
deterministic_steps.py 里注册（QA 不碰）。

handler 约定：
- 签名 `def handler(ctx, **groups)`：ctx 暴露 `page`（Playwright Page）；**groups = 正则的具名组**
  （`(?P<name>...)`）。无具名组则不传额外参数。
- 判定失败抛 `AssertionError` → step 记 **failed**（断言没过）；抛其它异常 → step 记 **error**。
- 不投票（确定性 = 无抖动，与 AI 断言的 votes 区分）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class _Entry:
    pattern: re.Pattern
    handler: Callable
    raw: str  # 原始模式串（报错/调试用）


_REGISTRY: list[_Entry] = []


def deterministic(pattern: str) -> Callable:
    """装饰器：把 handler 按正则 pattern 登记进注册表。

    用法（与脚手架 deterministic_steps.py 的真实锚点一致）：
        @deterministic(r'页面地址匹配 "(?P<pattern>.+)"')
        def url_matches(ctx, pattern):
            assert re.search(pattern, ctx.page.url)
    """
    compiled = re.compile(pattern)

    def register(handler: Callable) -> Callable:
        _REGISTRY.append(_Entry(pattern=compiled, handler=handler, raw=pattern))
        return handler

    return register


class DeterministicConflict(Exception):
    """一个 step 文本命中多条确定性模式（ADR 0022：最多命中一条，多条是配置错误）。"""


def match(text: str):
    """在注册表里找命中 text 的唯一 handler。

    返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 → DeterministicConflict。
    """
    hits = [(e, m) for e in _REGISTRY if (m := e.pattern.search(text))]
    if not hits:
        return None
    if len(hits) > 1:
        raws = ", ".join(repr(e.raw) for e, _ in hits)
        raise DeterministicConflict(
            f"step {text!r} 命中多条确定性模式 [{raws}]（ADR 0022：最多命中一条，请收紧模式）"
        )
    entry, m = hits[0]
    return entry.handler, m.groupdict()


def clear() -> None:
    """清空注册表（仅供测试隔离用）。"""
    _REGISTRY.clear()
