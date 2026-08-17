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
    raw: str  # 原始模式串（报错/调试/自述用）
    description: str  # 人话元数据（ADR 0036）：这步做什么（给 feature 作者读）
    example: str  # feature 里怎么写（可直接抄的 step 文本）


_REGISTRY: list[_Entry] = []


def deterministic(pattern: str, *, description: str, example: str) -> Callable:
    """装饰器：把 handler 按正则 pattern 登记进注册表。

    description/example 必填（ADR 0036：注册即暴露——缺元数据的能力不可被 feature 作者发现，fail-loud）。
    用法（与脚手架 deterministic_steps.py 的真实锚点一致）：
        @deterministic(r'页面地址(?:精确)?匹配 "(?P<pattern>[^"]+)"',
                       description="断言当前页面 URL 匹配给定正则",
                       example='Then 页面地址匹配 "/wiki/OpenAI"')
        def url_matches(ctx, pattern):
            assert re.search(pattern, ctx.page.url)
    """
    if not description or not example:
        raise ValueError(f"deterministic({pattern!r}) 注册缺 description/example（ADR 0036：能力必须可发现）")
    compiled = re.compile(pattern)

    def register(handler: Callable) -> Callable:
        _REGISTRY.append(_Entry(pattern=compiled, handler=handler, raw=pattern,
                                description=description, example=example))
        return handler

    return register


def list_registry() -> list[dict]:
    """注册表自述（ADR 0036）：worker --list-deterministic 时 dump 成 JSON 给 CLI 转述。"""
    return [{"pattern": e.raw, "description": e.description, "example": e.example} for e in _REGISTRY]


class DeterministicConflict(Exception):
    """一个 step 文本命中多条确定性模式（ADR 0022：最多命中一条，多条是配置错误）。"""

    def __init__(self, message: str, patterns: list[str] | None = None) -> None:
        super().__init__(message)
        self.patterns = patterns or []


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
            f"step {text!r} 命中多条确定性模式 [{raws}]（ADR 0022：最多命中一条，请收紧模式）",
            patterns=[e.raw for e, _ in hits],
        )
    entry, m = hits[0]
    return entry.handler, m.groupdict()


def match_batch(texts: list[str]) -> list[dict | None]:
    """批量 match 查询（ADR 0036 第二期）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。

    匹配语义与 match() 同一实现面（同一 _REGISTRY、同一 search 语义），冲突不抛、结构化返回
    （plan 是预检不是执行）。返回元素：None | {"pattern","description"} | {"conflict": [patterns]}。
    """
    out: list[dict | None] = []
    for text in texts:
        hits = [e for e in _REGISTRY if e.pattern.search(text)]
        if not hits:
            out.append(None)
        elif len(hits) > 1:
            out.append({"conflict": [e.raw for e in hits]})
        else:
            out.append({"pattern": hits[0].raw, "description": hits[0].description})
    return out


def clear() -> None:
    """清空注册表（仅供测试隔离用）。"""
    _REGISTRY.clear()
