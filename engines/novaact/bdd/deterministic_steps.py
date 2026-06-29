"""确定性锚点脚手架（ADR 0020/0022）—— 给 TEST ENGINEER（会写代码的角色），不是 QA。

用途：少数"必须精确、不容 AI 抖动"的断言（如 URL 精确、关键 DOM），用底层 Playwright
（`ctx.page`）直接查、**不走 AI、不投票**。这是 ADR 0015 的"确定性逃生舱"。

机制（ADR 0022）：worker 派发每个 step 时**先查确定性注册表**（命中走这里的 handler），
未命中才落 AI catch-all。在此用 `@deterministic(正则)` 注册即可——worker 启动时 import
本模块，顶层的 @deterministic 副作用把锚点登记进表。

角色边界（ADR 0020）：
  - 本文件由 test engineer 维护；QA 永远只在 .feature 写人话（默认走 AI，见 test_generic_steps.py）。
  - 仅当某断言确需精确、不能容忍 AI 非确定性时，test engineer 在此加一个项目专属锚点。

handler 约定（见 worker/deterministic.py）：
  - 签名 `def h(ctx, **groups)`：ctx.page = Playwright Page；groups = 正则具名组 (?P<name>...)。
  - 判定失败抛 AssertionError → step 记 failed；抛其它 → error。

Midscene 侧的对齐脚手架见 engines/midscene/bdd/steps/deterministic.steps.ts。
"""
from __future__ import annotations

import re

from deterministic import deterministic


@deterministic(r'页面地址(?:精确)?匹配 "(?P<pattern>.+)"')
def url_matches(ctx, pattern: str) -> None:
    """确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。

    .feature 写法（test engineer 约定的带关键词措辞，与 QA 的纯人话 Then 区分）：
        Then 页面地址匹配 "/wiki/OpenAI"
    """
    url = ctx.page.url
    assert re.search(pattern, url), f'URL 应匹配 {pattern!r}，实际 {url!r}'


# 更多锚点示例（需要时取消注释并改成你的项目所需）：
#
# @deterministic(r'元素 "(?P<sel>.+)" 可见')
# def element_visible(ctx, sel: str) -> None:
#     assert ctx.page.locator(sel).is_visible(), f'元素 {sel!r} 应可见'
