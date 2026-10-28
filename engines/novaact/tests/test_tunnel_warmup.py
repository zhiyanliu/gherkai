"""隧道会话预热（ADR 0051 决策 13；ADR 0035「边界与不变量」）——Nova worker 侧。

纯逻辑部分（三种可见结果的归因、有界重试）用假 page 覆盖；main 级用假会话驱动，验「完整性判据在建会话之前」「预热在 scope_started 之前」
「失败经 scope_done 传递、会话已释放、不退 EX_WORKER_NETWORK」。真边界（AgentCore 浏览器上 Set-Cookie 真写进 cookie 库、业务请求真带上）
在跳板机上真实执行核对。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_worker_novaact import run_scope as rs
from gherkai_worker_novaact.lib import constants as C
from gherkai_worker_novaact.lib import tunnel_warmup as W

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "tunnel-warmup.json"
WARMUP_URL = "https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "a" * 32


def test_edge_contract_constants_match_the_cross_language_fixture():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert (C.WARMUP_PATH, C.CHECK_PATH, C.TOKEN_PARAM, C.COOKIE_NAME) == (fx["warmup_path"], fx["check_path"], fx["token_param"], fx["cookie_name"])
    assert C.WARMUP_TITLES == fx["titles"] and C.WARMUP_MARKERS == fx["markers"]
    assert (C.SESSION_WARMUP_URL_ENV, C.EXTRA_HTTP_HEADERS_ENV, C.SESSION_WARMUP_KEY) == (fx["env"]["warmup_url"], fx["env"]["extra_http_headers"], fx["capability_key"])
    # 三条产品语言的消息也同源：两个 worker 对同一种失败给同一句话（排障文档只写一遍）
    assert (C.INCOMPLETE_DEFINITION_MESSAGE, C.WARMUP_DENIED_MESSAGE, C.WARMUP_ERROR_MESSAGE) == (
        fx["messages"]["incomplete_definition"], fx["messages"]["denied"], fx["messages"]["error_template"])


class _Resp:
    def __init__(self, status):
        self.status = status


class _FakePage:
    """每次 goto 按序给出一个结果（int 状态码 / None / 异常实例）；title 按序给出，最后一个值一直保持。"""

    def __init__(self, statuses, titles):
        self._statuses = list(statuses)
        self._titles = list(titles)
        self.gotos: list[str] = []
        self.context = type("Ctx", (), {"set_extra_http_headers": staticmethod(lambda h: None)})()  # 建会话后注额外请求头的面

    def goto(self, url, **kw):
        self.gotos.append(url)
        s = self._statuses.pop(0) if self._statuses else None  # 预热后离开到 about:blank 的那次导航不消耗预设状态
        if isinstance(s, BaseException):
            raise s
        return None if s is None else _Resp(s)

    def title(self):
        if len(self._titles) > 1:
            return self._titles.pop(0)
        return self._titles[0] if self._titles else ""


def _clock():
    """假时钟：每读一次前进 5 秒——等标记的 10 秒预算两次就到。"""
    t = [0.0]

    def monotonic():
        t[0] += 5.0
        return t[0]

    return monotonic


def _warm(page):
    return W.warmup_session(page, WARMUP_URL, log=lambda s: None, sleep=lambda s: None, monotonic=_clock())


def test_ready_marker_is_success_after_one_navigation():
    page = _FakePage([200], ["gherkai-tunnel-warmup", C.WARMUP_TITLES["ready"]])
    assert _warm(page) is None and page.gotos == [WARMUP_URL]


@pytest.mark.parametrize("statuses, titles", [
    ([401], ["gherkai-tunnel-auth-required"]),            # 令牌错：预热路径直接 401 页
    ([200], [C.WARMUP_TITLES["denied"]]),                 # 边缘不接受 cookie：脚本对校验路径得到 401
    ([200], [C.WARMUP_TITLES["auth_required"]]),
])
def test_denied_and_auth_required_are_deterministic_rejections_without_retry(statuses, titles):
    page = _FakePage(statuses, titles)
    f = _warm(page)
    assert f is not None and f.error_type == "precheck_failed" and f.message == C.WARMUP_DENIED_MESSAGE
    assert len(page.gotos) == 1


def test_error_marker_retries_then_ready():
    page = _FakePage([200, 200], [C.WARMUP_TITLES["error"], C.WARMUP_TITLES["ready"]])
    assert _warm(page) is None and len(page.gotos) == 2


def test_navigation_exceptions_are_swallowed_into_engine_error_not_raised():
    """导航抛网络类异常：不向上抛（外层的建连重试域看不到它、不会以退出码 80 收场），有界重试后归 engine_error。"""
    page = _FakePage([ConnectionError("reset"), TimeoutError("slow"), ConnectionError("reset")], [""])
    f = _warm(page)
    assert f is not None and f.error_type == "engine_error" and "已尝试 3 次" in f.message and len(page.gotos) == 3


def test_no_marker_within_budget_is_engine_error():
    page = _FakePage([200, 200, 200], ["gherkai-tunnel-warmup"])
    f = _warm(page)
    assert f is not None and f.error_type == "engine_error" and "没有给出任何标记" in f.message
    assert "响应状态 200，页面标题 gherkai-tunnel-warmup" in f.message
    f2 = _warm(_FakePage([None, None, None], [""]))  # 没有响应对象、空标题：说「未知」「空」，不把 None / 空字符串字面量塞进产品消息
    assert f2 is not None and "响应状态 未知，页面标题 空" in f2.message and "None" not in f2.message and "''" not in f2.message


def test_stop_signal_interrupts_warmup_before_navigation_and_during_marker_wait():
    """停止信号（ADR 0024 flag-only）：预热的退避与等标记都看 stop，收到即抛 WarmupStopped——不算失败、不发 scope_done。
    预热最坏要一两分钟（3 次导航各 30 秒超时加 10 秒等标记），不能让 SIGTERM 等满它再撞 SIGKILL。"""
    page = _FakePage([200], ["gherkai-tunnel-warmup"])
    with pytest.raises(W.WarmupStopped):
        W.warmup_session(page, WARMUP_URL, log=lambda s: None, sleep=lambda s: None, monotonic=_clock(), stop=lambda: True)
    assert page.gotos == []  # 导航之前就停

    flag = {"stop": False}

    class _StopAfterGoto(_FakePage):
        def goto(self, url, **kw):
            flag["stop"] = True  # 导航期间收到信号
            return super().goto(url, **kw)

    page2 = _StopAfterGoto([200], ["gherkai-tunnel-warmup"])
    with pytest.raises(W.WarmupStopped):
        W.warmup_session(page2, WARMUP_URL, log=lambda s: None, sleep=lambda s: None, monotonic=lambda: 0.0, stop=lambda: flag["stop"])
    assert page2.gotos == [WARMUP_URL]  # 等标记的预算远没到（假时钟不动），是停止信号让它退出


def test_stop_signal_during_backoff_is_honored_before_the_next_navigation():
    """退避期间（sleep 即 _stop.wait）收到停止信号：下一次导航之前就抛 WarmupStopped——否则还要再等一次最长 30 秒的导航，
    而且那次若恰好 READY 就会照发 scope_started、直到 scenario 边界才停。"""
    flag = {"stop": False}

    def sleep_then_stop(seconds):
        flag["stop"] = True  # 退避中信号到达（真实里是 _stop.wait 被唤醒后返回）

    page = _FakePage([200, 200], [C.WARMUP_TITLES["error"]])
    with pytest.raises(W.WarmupStopped):
        W.warmup_session(page, WARMUP_URL, log=lambda s: None, sleep=sleep_then_stop, monotonic=_clock(), stop=lambda: flag["stop"])
    assert len(page.gotos) == 1


# ---- main 级：假会话驱动（对称 test_evidence 的 main_fakes）----

class _Sink:
    def __init__(self, trace):
        self.events: list[dict] = []
        self._trace = trace

    def emit(self, ev):
        self.events.append(ev)
        self._trace.append(("emit", ev["type"]))

    def flush(self):
        pass


class _FakeCdp:
    def __init__(self, trace):
        self._trace = trace

    def __enter__(self):
        return ("ws://fake", {})

    def __exit__(self, *a):
        self._trace.append(("cdp_exit",))
        return False


class _FakeNovaAct:
    def __init__(self, page, trace, **kw):
        self.page = page
        self._trace = trace
        trace.append(("nova_init",))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self._trace.append(("nova_exit",))
        return False

    def get_session_id(self):
        return "sess-fake"


@pytest.fixture
def driven(monkeypatch, tmp_path):
    """main() 的 SDK 面全 fake：job 走 stdin（scenarios 空）、事件进内存 sink、会话与 cdp 的进出记进 trace。返回 (trace, sink, set_page)。"""
    trace: list = []
    sink = _Sink(trace)
    box: dict = {"page": _FakePage([200], [C.WARMUP_TITLES["ready"]])}
    monkeypatch.setattr(rs.signal, "signal", lambda s, h: None)
    monkeypatch.setattr(rs.sys, "stdin", type("S", (), {"readline": staticmethod(
        lambda: json.dumps({"schemaVersion": 1, "scope": {"id": "x", "name": "x"}, "scenarios": [],
                            "target": {"device": "desktop", "uiKind": "web"}, "engine": "novaact", "assertionVotes": 1,
                            "timeoutS": None, "deviceRequest": None}))})())
    monkeypatch.setattr(rs, "ensure_workflow_definition", lambda *a, **k: None)
    monkeypatch.setattr(rs, "Workflow", lambda **k: _FakeCdp([]))
    monkeypatch.setattr(rs, "get_current_workflow", lambda: None)
    monkeypatch.setattr(rs, "set_current_workflow", lambda w: None)
    monkeypatch.setattr(rs, "NovaAct", lambda **k: _FakeNovaAct(box["page"], trace, **k))

    class _P:
        def __init__(self, region=None):
            pass

        def cdp_session(self):
            return _FakeCdp(trace)

    monkeypatch.setattr(rs, "AgentCoreBrowserSessionProvider", _P)
    monkeypatch.setattr(rs, "EventSink", type("E", (), {"from_env": staticmethod(lambda: sink)}))
    real_warmup = W.warmup_session  # 先取真函数再打桩：桩里不能再经模块属性引用（那已是桩自己）

    def stub(page, url, *, log, sleep=None, stop=lambda: False):
        assert sleep == rs._stop.wait  # 生产接线（绑定方法每次取都是新对象，比较相等而不是同一）：退避与等标记都用 _stop.wait，停止信号才能唤醒它（ADR 0024 flag-only）
        return real_warmup(page, url, log=log, sleep=lambda s: None, monotonic=_clock(), stop=stop)

    monkeypatch.setattr(W, "warmup_session", stub)
    monkeypatch.setenv("NOVA_LOGS_DIR", str(tmp_path))
    monkeypatch.delenv("ARTIFACT_S3_BUCKET", raising=False)
    monkeypatch.delenv(C.EXTRA_HTTP_HEADERS_ENV, raising=False)
    monkeypatch.delenv(C.SESSION_WARMUP_URL_ENV, raising=False)
    rs._stop.clear()
    yield trace, sink, box
    rs._stop.clear()


def test_headers_without_warmup_url_is_precheck_failed_before_any_session(driven, monkeypatch):
    trace, sink, _ = driven
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    assert rs.main() == 0
    assert [e["type"] for e in sink.events] == ["scope_done"]
    assert sink.events[0]["status"] == "error" and sink.events[0]["errorType"] == "precheck_failed"
    assert sink.events[0]["message"] == C.INCOMPLETE_DEFINITION_MESSAGE
    assert ("nova_init",) not in trace  # 没建会话：零会话费用


def test_warmup_ready_navigates_once_before_scope_started(driven, monkeypatch):
    trace, sink, box = driven
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0
    assert [e["type"] for e in sink.events] == ["scope_started", "scope_done"]
    assert box["page"].gotos == [WARMUP_URL, "about:blank"]  # 预热恰一次、随即离开预热页（令牌不留在当前地址），都在 scope_started 之前
    assert "status" not in sink.events[1]


def test_warmup_rejected_releases_session_then_reports_scope_level_error(driven, monkeypatch):
    trace, sink, box = driven
    box["page"] = _FakePage([401], ["gherkai-tunnel-auth-required"])
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0  # 不是 EX_WORKER_NETWORK、不是 worker fatal
    assert [e["type"] for e in sink.events] == ["scope_done"]
    ev = sink.events[0]
    assert ev["status"] == "error" and ev["errorType"] == "precheck_failed" and ev["sessionId"] == "sess-fake"
    assert trace.index(("nova_exit",)) < trace.index(("emit", "scope_done"))  # 先释放会话再发事件（ADR 0051 决策 5）


def test_warmup_navigation_failures_end_as_engine_error_with_exit_0(driven, monkeypatch):
    trace, sink, box = driven
    box["page"] = _FakePage([ConnectionError("reset")] * 3, [""])
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0
    assert [e["type"] for e in sink.events] == ["scope_done"] and sink.events[0]["errorType"] == "engine_error"
    assert trace.count(("nova_init",)) == 1  # 预热的导航失败不进建连重试域：没有重建会话


def test_warmup_precedes_scope_started_and_scenarios(driven, monkeypatch):
    """次序：预热导航 → scope_started → scenario_started → 执行 → scenario_done → scope_done；预热只做一次，不按 scenario 重做。"""
    trace, sink, box = driven
    monkeypatch.setattr(rs.sys, "stdin", type("S", (), {"readline": staticmethod(
        lambda: json.dumps({"schemaVersion": 1, "scope": {"id": "x", "name": "x"},
                            "scenarios": [{"id": "x:1", "name": "s", "steps": [{"index": 0, "keyword": "Given", "text": "a"}]},
                                          {"id": "x:2", "name": "t", "steps": [{"index": 0, "keyword": "Given", "text": "b"}]}],
                            "target": {"device": "desktop", "uiKind": "web"}, "engine": "novaact", "assertionVotes": 1,
                            "timeoutS": None, "deviceRequest": None}))})())

    class _TracingPage(_FakePage):
        def goto(self, url, **kw):
            trace.append(("goto", url))
            return super().goto(url, **kw)

    box["page"] = _TracingPage([200], [C.WARMUP_TITLES["ready"]])
    monkeypatch.setattr(rs, "_run_scenario",
                        lambda nova, sid, steps, votes_n, sink, *, scope_id: trace.append(("run_scenario", sid)) or ["passed"])
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0
    assert [t for t in trace if t[0] in ("goto", "emit", "run_scenario")] == [
        ("goto", WARMUP_URL), ("goto", "about:blank"), ("emit", "scope_started"),
        ("emit", "scenario_started"), ("run_scenario", "x:1"), ("emit", "scenario_done"),
        ("emit", "scenario_started"), ("run_scenario", "x:2"), ("emit", "scenario_done"),
        ("emit", "scope_done")]


def test_release_failure_after_warmup_rejection_exits_1_without_reconnecting(driven, monkeypatch):
    """预热失败后释放会话出错：不进建连重试域（不重建会话）、归因不被覆盖、scope_done 照发、退出码 1 让泄漏可观测
    （ADR 0051 决策 5 与 13；对照 Midscene 的 cleanupFailed）。"""
    trace, sink, box = driven
    box["page"] = _FakePage([401], ["gherkai-tunnel-auth-required"])

    class _LeakyNovaAct(_FakeNovaAct):
        def __exit__(self, *a):
            super().__exit__(*a)
            raise RuntimeError("stop session failed")

    monkeypatch.setattr(rs, "NovaAct", lambda **k: _LeakyNovaAct(box["page"], trace, **k))
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 1
    assert [e["type"] for e in sink.events] == ["scope_done"]
    assert sink.events[0]["status"] == "error" and sink.events[0]["errorType"] == "precheck_failed"
    assert trace.count(("nova_init",)) == 1  # 释放失败不是建连失败：没有重建会话


def test_stop_during_warmup_releases_session_quietly_with_exit_0(driven, monkeypatch):
    """预热途中收到停止信号：正常 return 释放会话、不发任何事件、退出码 0——与 scenario 边界的协作停走同一条路径（ADR 0024 flag-only）。"""
    trace, sink, box = driven

    class _StopPage(_FakePage):
        def goto(self, url, **kw):
            rs._stop.set()
            return super().goto(url, **kw)

    box["page"] = _StopPage([200], ["gherkai-tunnel-warmup"])
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0
    assert sink.events == [] and ("nova_exit",) in trace


def test_release_failure_with_stop_after_warmup_rejection_still_exits_1(driven, monkeypatch):
    """预热被拒、释放会话出错、同时停止信号已置位：停止路径不发事件，但退出码仍是 1——释放失败不能被停止分支的 return 0 吞掉
    （ADR 0051 决策 5：退出码 1 表示有会话未确认停止，桌面只靠它让泄漏可观测）。"""
    trace, sink, box = driven

    class _StopPage(_FakePage):
        def goto(self, url, **kw):
            rs._stop.set()  # 导航期间收到信号；响应 401 → 预热判拒
            return super().goto(url, **kw)

    class _LeakyNovaAct(_FakeNovaAct):
        def __exit__(self, *a):
            super().__exit__(*a)
            raise RuntimeError("stop session failed")

    box["page"] = _StopPage([401], ["gherkai-tunnel-auth-required"])
    monkeypatch.setattr(rs, "NovaAct", lambda **k: _LeakyNovaAct(box["page"], trace, **k))
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 1
    assert sink.events == [] and trace.count(("nova_init",)) == 1


def test_release_failure_after_stopped_warmup_exits_1_without_reconnecting(driven, monkeypatch):
    """预热被停止信号打断后释放会话抛网络类异常：不是建连失败——不进建连重试域（不重建会话）、不发事件、退出码 1。
    此前这条路径会被当成瞬时网络错进退避、再被循环顶的停止检查放过，以 0 退出把释放失败吞掉。"""
    trace, sink, box = driven

    class _StopPage(_FakePage):
        def goto(self, url, **kw):
            rs._stop.set()  # 导航期间收到信号；页面无标记 → WarmupStopped
            return super().goto(url, **kw)

    class _LeakyNovaAct(_FakeNovaAct):
        def __exit__(self, *a):
            super().__exit__(*a)
            raise ConnectionError("reset")

    box["page"] = _StopPage([200], ["gherkai-tunnel-warmup"])
    monkeypatch.setattr(rs, "NovaAct", lambda **k: _LeakyNovaAct(box["page"], trace, **k))
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 1
    assert sink.events == [] and trace.count(("nova_init",)) == 1


def test_no_tunnel_env_is_zero_change(driven):
    trace, sink, box = driven
    assert rs.main() == 0
    assert [e["type"] for e in sink.events] == ["scope_started", "scope_done"] and box["page"].gotos == []


class _LeakyCdp(_FakeCdp):
    """AgentCore 会话释放失败的替身：第一次 __exit__ 抛（SDK 的 cdp_session 在 finally 里 stop，stop 抛出就是这形态）。"""

    def __init__(self, trace, exc):
        super().__init__(trace)
        self._exc = exc

    def __exit__(self, *a):
        super().__exit__(*a)
        if self._exc is not None:
            exc, self._exc = self._exc, None
            raise exc


def _leaky_provider(monkeypatch, trace, *, first_exit_exc):
    """只有第一个 cdp 会话的释放会抛；后续 attempt 的会话正常释放（可观察重试是否发生）。"""
    state = {"n": 0}

    class _P:
        def __init__(self, region=None):
            pass

        def cdp_session(self):
            state["n"] += 1
            return _LeakyCdp(trace, first_exit_exc if state["n"] == 1 else None)

    monkeypatch.setattr(rs, "AgentCoreBrowserSessionProvider", _P)
    return state


def test_release_failure_of_the_agentcore_session_after_connect_failure_is_not_a_connect_failure(driven, monkeypatch):
    """AgentCore 会话已建起、NovaAct 进入时抛网络错、随后释放会话又抛：释放异常不冒泡、不进建连重试判定；建连失败照常重试，
    重试成功后判定照发，但退出码为 1 让第一个会话的泄漏可观测（ADR 0024 释放优先、失败可观测；ADR 0051 决策 5）。
    此前释放异常顶替建连异常冒泡、又带着原来的网络错当 __context__ 被判成瞬时错——重试成功后整次以 0 退出，泄漏没有任何信号。"""
    trace, sink, box = driven
    state = _leaky_provider(monkeypatch, trace, first_exit_exc=RuntimeError("stop failed"))
    real_factory = {"n": 0}

    def nova_factory(**k):
        real_factory["n"] += 1
        if real_factory["n"] == 1:
            raise ConnectionError("reset")  # 第一次建连失败
        return _FakeNovaAct(box["page"], trace, **k)

    monkeypatch.setattr(rs, "NovaAct", nova_factory)
    monkeypatch.setattr(rs, "_backoff_interrupted", lambda attempt: _stop_is_set())
    assert rs.main() == 1
    assert [e["type"] for e in sink.events] == ["scope_started", "scope_done"]
    assert state["n"] == 2 and trace.count(("cdp_exit",)) == 2  # 重试建了第二个会话、两个都走到释放


def _stop_is_set():
    return rs._stop.is_set()


def test_release_failure_of_the_agentcore_session_with_stop_exits_1_without_retry(driven, monkeypatch):
    """同一窗口里停止信号已置位：不再重试、不发事件，退出码 1——释放失败不能被停止分支吞成 0。"""
    trace, sink, box = driven
    state = _leaky_provider(monkeypatch, trace, first_exit_exc=ConnectionError("stop reset"))

    def nova_factory(**k):
        rs._stop.set()
        raise ConnectionError("reset")

    monkeypatch.setattr(rs, "NovaAct", nova_factory)
    monkeypatch.setattr(rs, "_backoff_interrupted", lambda attempt: _stop_is_set())
    assert rs.main() == 1
    assert sink.events == [] and state["n"] == 1


def test_connect_failure_with_stop_and_no_session_exits_0(driven, monkeypatch):
    """建连期间收到停止信号且建连抛网络错、会话正常释放：这是建连失败不是释放失败——按停止路径以 0 退出、零事件。
    守住「只有释放阶段抛出才记 release_error」：把建连异常也记成释放失败会向桌面误报有会话未确认停止。"""
    trace, sink, box = driven

    def nova_factory(**k):
        rs._stop.set()
        raise ConnectionError("reset")

    monkeypatch.setattr(rs, "NovaAct", nova_factory)
    monkeypatch.setattr(rs, "_backoff_interrupted", lambda attempt: _stop_is_set())
    assert rs.main() == 0
    assert sink.events == [] and trace.count(("cdp_exit",)) == 1


def test_release_failure_on_the_normal_path_keeps_the_verdict_and_exits_1(driven, monkeypatch):
    """正常路径（无隧道）释放 AgentCore 会话失败：判定照发（scope_started、scope_done），退出码 1——对称 Midscene 的 cleanupFailed。"""
    trace, sink, box = driven
    _leaky_provider(monkeypatch, trace, first_exit_exc=RuntimeError("stop failed"))
    assert rs.main() == 1
    assert [e["type"] for e in sink.events] == ["scope_started", "scope_done"]


def test_capabilities_declare_session_warmup():
    assert rs._capabilities()[C.SESSION_WARMUP_KEY] is True
