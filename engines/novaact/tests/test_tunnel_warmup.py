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
        s = self._statuses.pop(0)
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
    assert f is not None and f.error_type == "engine_error" and "已重试 3 次" in f.message and len(page.gotos) == 3


def test_no_marker_within_budget_is_engine_error():
    page = _FakePage([200, 200, 200], ["gherkai-tunnel-warmup"])
    f = _warm(page)
    assert f is not None and f.error_type == "engine_error" and "没有给出任何标记" in f.message


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
    monkeypatch.setattr(W, "warmup_session",
                        lambda page, url, *, log: real_warmup(page, url, log=log, sleep=lambda s: None, monotonic=_clock()))
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
    assert box["page"].gotos == [WARMUP_URL]  # 恰一次，且在 scope_started 之前（scenarios 为空、不会再导航）
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


def test_no_tunnel_env_is_zero_change(driven):
    trace, sink, box = driven
    assert rs.main() == 0
    assert [e["type"] for e in sink.events] == ["scope_started", "scope_done"] and box["page"].gotos == []


def test_capabilities_declare_session_warmup():
    assert rs._capabilities()[C.SESSION_WARMUP_KEY] is True
