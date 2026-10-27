"""隧道会话预热（ADR 0051 决策 13）：worker 在第一个 scenario 之前对预热地址导航一次换到会话 cookie，并按页面的可见结果归因。

三种可见结果、三端同一条判据（桌面读响应状态与 document.title，设备在控件树里找正文标记）：
- READY：就绪；
- DENIED（预热页面脚本向校验路径请求得到 401）或 AUTH REQUIRED（令牌错，预热路径直接 401 页）：确定性拒绝，`precheck_failed`，不重试；
- ERROR（脚本请求失败）或预算内没有任何标记、导航本身抛出：原地重导航有界重试，耗尽后 `engine_error`。
两者都不归 `network_error`（ADR 0028 的分类红线：鉴权失败与拿不准的失败不得归瞬时网络故障），一律经 scope_done{status, errorType}
传递（ADR 0051 决策 4）——所以本模块把导航异常吞在自己的重试里、绝不向上抛，外层的建连重试域看不到它。
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from gherkai_worker_novaact.lib.constants import (
    WARMUP_ATTEMPTS,
    WARMUP_DENIED_MESSAGE,
    WARMUP_ERROR_MESSAGE,
    WARMUP_MARKER_WAIT_S,
    WARMUP_NAV_TIMEOUT_MS,
    WARMUP_TITLES,
)
from gherkai_worker_novaact.lib.redact import redact_secrets

_TERMINAL_TITLES = frozenset(WARMUP_TITLES.values())


@dataclass(frozen=True)
class WarmupFailure:
    error_type: str  # precheck_failed / engine_error
    message: str


def _one_line(text: str) -> str:
    first = next((ln.strip() for ln in str(text).splitlines() if ln.strip()), "")
    return redact_secrets(" ".join(first.split()))[:200]


def warmup_session(page, url: str, *, log: Callable[[str], None], sleep=time.sleep, monotonic=time.monotonic) -> WarmupFailure | None:
    """对 `page` 导航预热地址、等页面标题落成四个标记之一；返回 None 表示就绪，否则返回归因与产品语言的消息。
    `page` 是 Playwright 同步 Page（Nova SDK 的 nova.page）。"""
    last = "没有拿到预热页面"
    for attempt in range(WARMUP_ATTEMPTS):
        if attempt:
            sleep(min(2.0 * attempt, 5.0))
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=WARMUP_NAV_TIMEOUT_MS)
        except Exception as e:  # noqa: BLE001  导航失败（含网络类异常）走 ERROR 路线：有界重试、不向上抛、不进建连重试域
            last = f"预热导航失败：{_one_line(e)}"
            log(f"worker: tunnel warmup navigation failed (attempt {attempt + 1}): {last}")
            continue
        status = None
        try:
            status = resp.status if resp is not None else None
        except Exception:  # noqa: BLE001
            status = None
        if status == 401:  # 令牌错：预热路径直接 401 页（AUTH REQUIRED）
            return WarmupFailure("precheck_failed", WARMUP_DENIED_MESSAGE)
        title = _wait_for_marker(page, sleep=sleep, monotonic=monotonic)
        if title == WARMUP_TITLES["ready"]:
            return None
        if title in (WARMUP_TITLES["denied"], WARMUP_TITLES["auth_required"]):
            return WarmupFailure("precheck_failed", WARMUP_DENIED_MESSAGE)
        last = (f"预热页面标记为 {title}" if title == WARMUP_TITLES["error"]
                else f"预热页面在 {WARMUP_MARKER_WAIT_S:g} 秒内没有给出任何标记（响应状态 {status}，页面标题 {title!r}）")
        log(f"worker: tunnel warmup not ready (attempt {attempt + 1}): {last}")
    return WarmupFailure("engine_error", WARMUP_ERROR_MESSAGE.format(attempts=WARMUP_ATTEMPTS, reason=last))


def _wait_for_marker(page, *, sleep, monotonic) -> str | None:
    deadline = monotonic() + WARMUP_MARKER_WAIT_S
    title: str | None = None
    while True:
        try:
            title = page.title()
        except Exception:  # noqa: BLE001
            title = None
        if title in _TERMINAL_TITLES:
            return title
        if monotonic() >= deadline:
            return title
        sleep(0.25)
