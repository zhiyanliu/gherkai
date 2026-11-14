"""job 墙钟预算的产品上限不大于各引擎对每种目标能支持的最长预算（ADR 0054 决策十），Nova 侧与产品上限本身。

本引擎能支持的最长预算：带会话上限的目标取能力自述里的 max_session_s（Nova 现在只有桌面网页，不带会话上限）；桌面目标取浏览器会话
存活时间的封顶值减去余量（会话存活时间按预算加余量设定，预算再大就被封顶截短）。引擎一侧的数低于产品上限，本测试即失败。Midscene 侧
由 engines/midscene/src/worker/job-timeout-cap.test.mts 在 npm 测试里核（pytest 的环境里没有 Midscene 的运行时）。
"""
from __future__ import annotations

from gherkai_core.model import MAX_JOB_TIMEOUT_S
from gherkai_worker_novaact import run_scope


def test_novaact_targets_with_a_session_limit_support_the_product_cap():
    limited = [t for t in run_scope.WORKER_TARGETS if t.get("max_session_s") is not None]
    for t in limited:
        assert t["max_session_s"] >= MAX_JOB_TIMEOUT_S, f"{t['device']} 的会话上限 {t['max_session_s']} 秒低于产品上限"


def test_novaact_desktop_browser_session_lasts_for_the_product_cap():
    margin, ceiling = run_scope.BROWSER_SESSION_TIMEOUT_MARGIN_S, run_scope.BROWSER_SESSION_TIMEOUT_MAX_S
    assert ceiling - margin >= MAX_JOB_TIMEOUT_S, f"会话存活时间封顶 {ceiling} 秒减余量 {margin} 秒低于产品上限"
    assert run_scope.browser_session_timeout_s(MAX_JOB_TIMEOUT_S) == MAX_JOB_TIMEOUT_S + margin  # 预算取到上限时不被截短
