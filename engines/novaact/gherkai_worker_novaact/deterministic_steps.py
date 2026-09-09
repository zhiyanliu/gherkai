"""确定性锚点脚手架（ADR 0020/0022）—— **本包内建**的示范锚点，随 worker 发行。

用途：少数"必须精确、不容 AI 抖动"的断言（如 URL 精确、关键 DOM），用底层 Playwright
（`ctx.page`）直接查、**不走 AI、不投票**。这是 ADR 0015 的"确定性逃生舱"。

机制（ADR 0022）：worker 派发每个 step 时**先查确定性注册表**（命中走这里的 handler），
未命中才落 AI catch-all。用 `@deterministic(正则)` 注册即可——worker 启动时 import
本模块，顶层的 @deterministic 副作用把锚点登记进表。

**使用方的定制锚点不写在这里**（ADR 0037 决策 4）：本文件是发行包内容、装在 site-packages 里，
改它等于 fork。使用方（测试开发）把自己的锚点写进**项目里的 `steps/` 目录**（`steps/*.py`，
顶层 `from gherkai_worker_novaact.deterministic import deterministic` 后同样 `@deterministic` 注册），
worker 启动时按 env `GHERKAI_STEPS_DIR` 加载进**同一张表**（见 `user_steps.py`）。故本文件只保留
一条示范锚点 + 注释里的写法样例，不承载项目专属内容。撞 pattern 按 ADR 0036 的 conflict 语义处理
（`plan` 预检暴露），**内建与使用方之间没有优先级覆盖**。

角色边界（ADR 0020）：
  - 确定性锚点由测试开发（会写代码的角色）维护；QA 永远只在 .feature 写自然语言
    （默认走 AI catch-all，见 `run_scope.py` `_run_step` 派发③ / ADR 0024「worker 派发」）。
  - 仅当某断言确需精确、不能容忍 AI 非确定性时才加锚点。

handler 约定（见 `deterministic.py`）：
  - 签名 `def h(ctx, **groups)`：ctx.page = Playwright Page；groups = 正则具名组 (?P<name>...)。
  - 判定失败抛 AssertionError → step 记 failed；抛其它 → error。

Midscene 侧的对齐脚手架见 `@gherkai/worker-midscene` 的 `worker/deterministic.steps` 模块。
"""
from __future__ import annotations

import re

from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'页面地址(?:精确)?匹配 "(?P<pattern>[^"]+)"',  # [^"]+（非 .+）：防第二对引号时贪婪跨引号捕获
               description="断言当前页面 URL 匹配给定正则（精确判定，不走 AI、不投票）",
               example='Then 页面地址匹配 "/wiki/OpenAI"')
def url_matches(ctx, pattern: str) -> None:
    """确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。

    .feature 写法（测试开发约定的带关键词措辞，与 QA 的纯自然语言 Then 区分）：
        Then 页面地址匹配 "/wiki/OpenAI"
    """
    url = ctx.page.url
    assert re.search(pattern, url), f'URL 应匹配 {pattern!r}，实际 {url!r}'


# 更多锚点写法示例（**抄进你项目的 `steps/*.py` 里改**，别改本文件——见上「使用方的定制锚点不写在这里」）：
#
# @deterministic(r'元素 "(?P<sel>[^"]+)" 可见',
#                description="断言选择器命中的元素可见",
#                example='Then 元素 "#submit" 可见')
# def element_visible(ctx, sel: str) -> None:
#     assert ctx.page.locator(sel).is_visible(), f'元素 {sel!r} 应可见'
