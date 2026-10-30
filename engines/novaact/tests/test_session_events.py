"""桌面会话事件与浏览器会话的请求名（ADR 0051 决策 3、4；ADR 0028「会话已起 ⟷ scope_started 已 emit」之间的血缘窗口条）。

Nova worker 对每个建起的 AgentCore 浏览器会话成对发 session_opened / session_closed：Start 返回后、取连接头与进 NovaAct 之前发
session_opened（origin 为 created，sessionId 与 name 都取会话 id，不带 device）；每条收尾路径（正常收尾、停止信号、会话预热失败、
建连重试丢弃的 attempt）都为每个会话发恰一条 session_closed，Stop 成功即 confirmed、失败或超过预算即 unconfirmed，桌面不带
observedS 与 providerMinutes。停止信号到达时 Start 仍在途、等待窗口内没有返回，发一对 attempted 事件（sessionId 为 null，name 取
请求名）并以退出码 1 结束；在窗口内返回、或停止信号落在 Start 返回之后与 scope_started 之前，会话照样成对、不发 scope_started
（它表示被测对象已就绪，ADR 0051 决策 4）。每次 Start 都带请求名，规则与 Midscene worker 的会话名模块相同、上限 100。

事件形状以 core/gherkai_core/wire.py 的校验为准：worker 包零 core 依赖，这里逐条重述那几条校验（下面的 _check_wire_shape），
不 import core。下面的假 SDK 只覆盖 worker 自己的次序与配对逻辑；Start 与 Stop 在真实 AgentCore 上的返回时机不在 mock 之内，
桌面真实执行核对见 tools/e2e_harness.py。
"""
from __future__ import annotations

import hashlib
import json
import threading
import time

import pytest

from gherkai_worker_novaact import run_scope as rs
from gherkai_worker_novaact.lib import constants as C
from gherkai_worker_novaact.lib import tunnel_warmup as W

RUN = "20260629T141207Z-a3f9c1"
CHECKOUT_HASH = "c7761e58969f7edd"  # sha256("checkout") 的前 16 位，另算后写死（与 Midscene 侧会话名单测同一组期望值）
CJK_SCOPE = "登录 流程/a~b:c"
CJK_HASH = "ab5bc226428ff117"
CJK_ENCODED = "%E7%99%BB%E5%BD%95%20%E6%B5%81%E7%A8%8B%2Fa%7Eb%3Ac"
SCOPE_ID = "features/登录.feature"
WARMUP_URL = "https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "a" * 32


# ---- 请求名的规则（与 Midscene 侧同一组用例）----

def test_request_name_has_five_segments_in_order():
    assert rs.session_request_name(RUN, "checkout", 1) == f"gherkai:{RUN}:{CHECKOUT_HASH}:1:checkout"
    assert rs.session_request_name(RUN, "checkout", 0) == f"gherkai:{RUN}:{CHECKOUT_HASH}:0:checkout"
    assert rs.session_request_name(RUN, "checkout", 27) == f"gherkai:{RUN}:{CHECKOUT_HASH}:27:checkout"
    # 这条超过桌面的 100 字符上限，按 Device Farm 的 256 上限比对完整编码（截断另有用例）
    assert rs.session_request_name(RUN, CJK_SCOPE, 2, max_length=256) == f"gherkai:{RUN}:{CJK_HASH}:2:{CJK_ENCODED}"


def test_request_name_percent_encodes_everything_outside_the_unreserved_set():
    def seg(scope_id: str) -> str:
        return rs.session_request_name(RUN, scope_id, 1, max_length=256).rsplit(":", 1)[1]

    assert seg("AZaz09._-") == "AZaz09._-"
    assert seg("!'()*~") == "%21%27%28%29%2A%7E"  # urllib.parse.quote 缺省放行的 ~ 这里也编码
    assert seg("a:b%c d+e/f") == "a%3Ab%25c%20d%2Be%2Ff"  # 冒号与百分号也编码，编码段里没有分隔符
    assert seg("é") == "%C3%A9"
    assert seg("😀") == "%F0%9F%98%80"
    assert seg(CJK_SCOPE) == CJK_ENCODED


def test_lone_surrogate_is_encoded_as_the_replacement_character_like_the_midscene_side():
    """JSON 里的孤立代理码元：按 U+FFFD 编码与求哈希（Node 的 utf8 编码就是这样做的），不在 Python 侧抛 UnicodeEncodeError。"""
    name = rs.session_request_name(RUN, "a\ud800", 1)
    assert name == f"gherkai:{RUN}:{hashlib.sha256('a�'.encode()).hexdigest()[:16]}:1:a%EF%BF%BD"


def test_request_name_is_capped_at_100_and_only_the_last_segment_is_truncated():
    assert rs.AGENTCORE_SESSION_NAME_MAX == 100
    long = "scope-" * 80
    name = rs.session_request_name(RUN, long, 3)
    head = f"gherkai:{RUN}:{hashlib.sha256(long.encode()).hexdigest()[:16]}:3:"
    assert name.startswith(head) and len(name) == 100 and long.startswith(name[len(head):])
    assert len(rs.session_request_name(RUN, long, 3, max_length=256)) == 256
    exact = "a" * (100 - len(f"gherkai:{RUN}:{hashlib.sha256(b'x').hexdigest()[:16]}:1:"))
    assert rs.session_request_name(RUN, exact, 1).endswith(f":{exact}") and len(rs.session_request_name(RUN, exact, 1)) == 100


def test_truncation_keeps_whole_characters_and_never_splits_a_percent_escape():
    scope_id = "流程" * 60  # 每个字符编码成 9 个字符
    seg = rs.session_request_name(RUN, scope_id, 1).rsplit(":", 1)[1]
    assert len(seg) % 9 == 0 and len(rs.session_request_name(RUN, scope_id, 1)) > 100 - 9
    from urllib.parse import unquote
    assert scope_id.startswith(unquote(seg))
    head = f"gherkai:{RUN}:{hashlib.sha256('ab😀'.encode()).hexdigest()[:16]}:1:"
    assert rs.session_request_name(RUN, "ab😀", 1, max_length=len(head) + 5) == f"{head}ab"


def test_hash_always_covers_the_full_scope_id():
    a, b = "x" * 300 + "-a", "x" * 300 + "-b"
    na, nb = rs.session_request_name(RUN, a, 1), rs.session_request_name(RUN, b, 1)
    assert na.rsplit(":", 1)[1] == nb.rsplit(":", 1)[1] and na != nb


def test_fixed_segments_that_do_not_fit_and_invalid_arguments_are_rejected():
    with pytest.raises(ValueError, match="会话名"):
        rs.session_request_name("r" * 120, "checkout", 1)
    head = f"gherkai:{RUN}:{CHECKOUT_HASH}:1:"
    assert rs.session_request_name(RUN, "checkout", 1, max_length=len(head)) == head  # 固定四段恰好占满时编码段为空
    for bad in (-1, 1.5, True):
        with pytest.raises(ValueError):
            rs.session_request_name(RUN, "checkout", bad)
    with pytest.raises(ValueError):
        rs.session_request_name("", "checkout", 1)
    for bad in (0, -5):
        with pytest.raises(ValueError):
            rs.session_request_name(RUN, "checkout", 1, max_length=bad)


# ---- main 级：假 SDK 驱动 ----

def _check_wire_shape(ev: dict) -> None:
    """core/gherkai_core/wire.py 对会话事件的校验逐条重述，外加桌面专属的两条（不带 device，不带 observedS 与 providerMinutes）。"""
    t = ev["type"]
    if t not in ("session_opened", "session_closed"):
        return
    assert isinstance(ev["scopeId"], str) and ev["scopeId"]
    assert isinstance(ev["name"], str) and ev["name"], ev  # name 是配对键的回退，必须非空
    assert ev["sessionId"] is None or (isinstance(ev["sessionId"], str) and ev["sessionId"]), ev
    if t == "session_opened":
        assert ev["origin"] in ("created", "discovered", "attempted"), ev
        assert ev["origin"] != "discovered", ev  # 桌面没有按名列举
        assert set(ev) == {"type", "scopeId", "sessionId", "name", "origin"}, ev
    else:
        assert ev["release"] in ("confirmed", "unconfirmed"), ev
        assert set(ev) == {"type", "scopeId", "sessionId", "name", "release"}, ev


def _assert_paired(events: list[dict]) -> None:
    """每个会话恰有一条 session_opened 与一条 session_closed，closed 在 opened 之后；配对键是 sessionId，缺省回退为 name。"""
    open_keys: list = []
    closed_keys: list = []
    for ev in events:
        key = ev.get("sessionId") or ev.get("name")
        if ev["type"] == "session_opened":
            assert key not in open_keys, f"同一会话发了两次 session_opened：{key}"
            open_keys.append(key)
        elif ev["type"] == "session_closed":
            assert key in open_keys, f"session_closed 先于 session_opened：{key}"
            assert key not in closed_keys, f"同一会话发了两次 session_closed：{key}"
            closed_keys.append(key)
    assert open_keys == closed_keys, (open_keys, closed_keys)


def _session_events(events: list[dict]) -> list[dict]:
    return [e for e in events if e["type"] in ("session_opened", "session_closed")]


class _Sink:
    def __init__(self, trace):
        self.events: list[dict] = []
        self._trace = trace

    def emit(self, ev):
        _check_wire_shape(ev)
        json.dumps(ev, ensure_ascii=False)  # 能按 JSON 写出（sessionId 的 null 是 None，不是别的哨兵）
        self.events.append(ev)
        self._trace.append(("emit", ev["type"]))

    def flush(self):
        pass


class _Cm:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _World:
    """假 SDK 的共享状态：每次 Start 依次取 start_plan 的一项（None 成功；异常实例即抛；callable 先调用再成功），会话 id 按次编号。"""

    def __init__(self):
        self.trace: list = []
        self.start_kwargs: list[dict] = []
        self.start_plan: list = []
        self.stop_plan: list = []      # 按次给 Stop 的结果：None 成功；异常实例即抛
        self.nova_plan: list = []      # 按次给 NovaAct 构造的结果：None 成功；异常实例即抛
        self.ws_plan: list = []        # 按次给取连接头的结果
        self.n_start = 0
        self.page = _Page([200], [C.WARMUP_TITLES["ready"]])


class _Client:
    def __init__(self, world: _World):
        self._w = world
        self.session_id = None
        self.identifier = None

    def start(self, **kw):
        self._w.start_kwargs.append(kw)
        self._w.trace.append(("start", kw.get("name")))
        step = self._w.start_plan.pop(0) if self._w.start_plan else None
        if isinstance(step, BaseException):
            raise step
        if callable(step):
            step()
        self._w.n_start += 1
        self.identifier, self.session_id = "aws.browser.v1", f"sess-{self._w.n_start}"
        return self.session_id

    def generate_ws_headers(self):
        self._w.trace.append(("ws_headers",))
        step = self._w.ws_plan.pop(0) if self._w.ws_plan else None
        if step is not None:
            raise step
        return ("ws://fake", {})

    def stop(self):
        self._w.trace.append(("stop", self.session_id))
        step = self._w.stop_plan.pop(0) if self._w.stop_plan else None
        if callable(step) and not isinstance(step, BaseException):
            step()
        elif step is not None:
            raise step
        self.session_id = self.identifier = None
        return True


class _Nova:
    def __init__(self, world: _World):
        self._w = world
        self.page = world.page
        world.trace.append(("nova_init",))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self._w.trace.append(("nova_exit",))
        return False

    def get_session_id(self):
        return "nova-sess"


class _Resp:
    def __init__(self, status):
        self.status = status


class _Page:
    def __init__(self, statuses, titles):
        self._statuses, self._titles = list(statuses), list(titles)
        self.context = type("Ctx", (), {"set_extra_http_headers": staticmethod(lambda h: None)})()

    def goto(self, url, **kw):
        s = self._statuses.pop(0) if self._statuses else None
        if isinstance(s, BaseException):
            raise s
        return None if s is None else _Resp(s)

    def title(self):
        return self._titles.pop(0) if len(self._titles) > 1 else (self._titles[0] if self._titles else "")


def _job(scope_id: str = SCOPE_ID, n_scenarios: int = 1, target: dict | None = None) -> str:
    return json.dumps({
        "schemaVersion": 1, "scope": {"id": scope_id, "name": "s"}, "engine": "novaact", "assertionVotes": 1,
        "timeoutS": None, "deviceRequest": None, "target": target or {"device": "desktop", "uiKind": "web"},
        "scenarios": [{"id": f"{scope_id}:{i}", "name": "s", "steps": [{"index": 0, "keyword": "Given", "text": "a"}]}
                      for i in range(n_scenarios)]})


@pytest.fixture
def world(monkeypatch, tmp_path):
    w = _World()
    sink = _Sink(w.trace)
    w.sink = sink
    w.job = _job()
    monkeypatch.setattr(rs.signal, "signal", lambda s, h: None)
    monkeypatch.setattr(rs.sys, "stdin", type("S", (), {"readline": staticmethod(lambda: w.job)})())
    monkeypatch.setattr(rs, "ensure_workflow_definition", lambda *a, **k: None)
    monkeypatch.setattr(rs, "Workflow", lambda **k: _Cm())
    monkeypatch.setattr(rs, "get_current_workflow", lambda: None)
    monkeypatch.setattr(rs, "set_current_workflow", lambda wf: None)
    monkeypatch.setattr(rs, "BrowserClient", lambda region=None: _Client(w))

    def nova_factory(**k):
        step = w.nova_plan.pop(0) if w.nova_plan else None
        if step is not None:
            raise step
        return _Nova(w)

    monkeypatch.setattr(rs, "NovaAct", nova_factory)
    monkeypatch.setattr(rs, "EventSink", type("E", (), {"from_env": staticmethod(lambda: sink)}))
    monkeypatch.setattr(rs, "_run_scenario",
                        lambda nova, sid, steps, votes_n, sink, *, scope_id: w.trace.append(("run_scenario", sid)) or ["passed"])
    monkeypatch.setattr(rs, "_backoff_interrupted", lambda attempt: rs._stop.is_set())
    real_warmup = W.warmup_session
    monkeypatch.setattr(W, "warmup_session", lambda page, url, *, log, sleep=None, stop=lambda: False: real_warmup(
        page, url, log=log, sleep=lambda s: None, monotonic=iter(range(0, 10_000)).__next__, stop=stop))
    monkeypatch.setenv("RUN_ID", RUN)
    monkeypatch.setenv("NOVA_LOGS_DIR", str(tmp_path))
    monkeypatch.delenv("ARTIFACT_S3_BUCKET", raising=False)
    monkeypatch.delenv(C.EXTRA_HTTP_HEADERS_ENV, raising=False)
    monkeypatch.delenv(C.SESSION_WARMUP_URL_ENV, raising=False)
    rs._stop.clear()
    yield w
    rs._stop.clear()


def _types(w: _World) -> list[str]:
    return [e["type"] for e in w.sink.events]


def _opened(sid: str) -> dict:
    return {"type": "session_opened", "scopeId": SCOPE_ID, "sessionId": sid, "name": sid, "origin": "created"}


def _closed(sid: str, release: str = "confirmed") -> dict:
    return {"type": "session_closed", "scopeId": SCOPE_ID, "sessionId": sid, "name": sid, "release": release}


def test_normal_path_pairs_the_session_and_closes_it_before_scope_done(world):
    assert rs.main() == 0
    assert _types(world) == ["session_opened", "scope_started", "scenario_started", "scenario_done", "session_closed", "scope_done"]
    assert _session_events(world.sink.events) == [_opened("sess-1"), _closed("sess-1")]
    _assert_paired(world.sink.events)


def test_session_opened_follows_start_before_any_long_running_step(world):
    """Start 返回后、取连接头与进 NovaAct 之前就发：建连中途被打断时血缘已在 core 手里。"""
    assert rs.main() == 0
    t = world.trace
    assert t.index(("start", world.start_kwargs[0]["name"])) < t.index(("emit", "session_opened")) < t.index(("ws_headers",)) < t.index(("nova_init",))
    assert t.index(("stop", "sess-1")) < t.index(("emit", "session_closed")) < t.index(("emit", "scope_done"))


def test_every_start_carries_the_request_name_and_nothing_else(world):
    assert rs.main() == 0
    assert world.start_kwargs == [{"name": rs.session_request_name(RUN, SCOPE_ID, 1)}]  # 不带 profile 配置、用默认浏览器标识
    name = world.start_kwargs[0]["name"]
    assert name.startswith(f"gherkai:{RUN}:") and ":1:features%2F" in name and len(name) <= 100


def test_long_scope_id_still_fits_the_agentcore_name_limit(world):
    world.job = _job(scope_id="features/" + "很长的场景目录/" * 30 + "x.feature")
    assert rs.main() == 0
    assert len(world.start_kwargs[0]["name"]) <= rs.AGENTCORE_SESSION_NAME_MAX


def test_stop_failure_closes_the_session_unconfirmed_keeps_the_verdict_and_exits_1(world):
    world.stop_plan = [RuntimeError("AccessDenied")]
    assert rs.main() == 1
    assert _session_events(world.sink.events) == [_opened("sess-1"), _closed("sess-1", "unconfirmed")]
    assert _types(world)[-2:] == ["session_closed", "scope_done"]  # 释放结果先于 scope_done 写进事件流
    _assert_paired(world.sink.events)


def test_stop_over_budget_is_unconfirmed(world, monkeypatch):
    monkeypatch.setattr(rs, "SESSION_STOP_BUDGET_S", 0.05)
    world.stop_plan = [lambda: threading.Event().wait(0.5)]
    assert rs.main() == 1
    assert _session_events(world.sink.events)[-1] == _closed("sess-1", "unconfirmed")


def test_novaact_close_failure_alone_does_not_unconfirm_a_stopped_session(world, monkeypatch):
    """确认只认 StopBrowserSession 成功：关 NovaAct 连接出错仍记释放失败（退出码 1），但会话本身已停、记 confirmed。"""
    class _LeakyNova(_Nova):
        def __exit__(self, *a):
            super().__exit__(*a)
            raise RuntimeError("cdp close failed")

    monkeypatch.setattr(rs, "NovaAct", lambda **k: _LeakyNova(world))
    assert rs.main() == 1
    assert _session_events(world.sink.events) == [_opened("sess-1"), _closed("sess-1")]


def test_stop_signal_between_scenarios_pairs_the_session_without_scope_done(world, monkeypatch):
    world.job = _job(n_scenarios=2)

    def stop_after_first(nova, sid, steps, votes_n, sink, *, scope_id):
        world.trace.append(("run_scenario", sid))
        rs._stop.set()
        return ["passed"]

    monkeypatch.setattr(rs, "_run_scenario", stop_after_first)
    assert rs.main() == 0
    assert _types(world) == ["session_opened", "scope_started", "scenario_started", "session_closed"]
    assert _session_events(world.sink.events) == [_opened("sess-1"), _closed("sess-1")]


def test_stop_signal_with_a_failed_stop_exits_1(world, monkeypatch):
    world.stop_plan = [ConnectionError("reset")]
    monkeypatch.setattr(rs, "_run_scenario", lambda *a, **k: rs._stop.set() or ["passed"])
    assert rs.main() == 1
    assert _session_events(world.sink.events) == [_opened("sess-1"), _closed("sess-1", "unconfirmed")]
    assert "scope_done" not in _types(world)


def test_warmup_failure_releases_and_pairs_the_session_before_scope_done(world, monkeypatch):
    world.page = _Page([401], [C.WARMUP_TITLES["auth_required"]])
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0
    assert _types(world) == ["session_opened", "session_closed", "scope_done"]
    assert world.sink.events[-1]["errorType"] == "precheck_failed"
    assert _session_events(world.sink.events) == [_opened("sess-1"), _closed("sess-1")]


def test_stop_signal_during_warmup_pairs_the_session_only(world, monkeypatch):
    class _StopPage(_Page):
        def goto(self, url, **kw):
            rs._stop.set()
            return super().goto(url, **kw)

    world.page = _StopPage([200], ["gherkai-tunnel-warmup"])
    monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
    monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0
    assert world.sink.events == [_opened("sess-1"), _closed("sess-1")]


def test_connect_retry_pairs_the_discarded_attempt_and_names_each_attempt(world):
    world.nova_plan = [ConnectionError("reset")]
    assert rs.main() == 0
    assert _types(world) == ["session_opened", "session_closed", "session_opened", "scope_started", "scenario_started",
                             "scenario_done", "session_closed", "scope_done"]
    assert _session_events(world.sink.events) == [_opened("sess-1"), _closed("sess-1"), _opened("sess-2"), _closed("sess-2")]
    assert world.sink.events[3] == {"type": "scope_started", "scopeId": SCOPE_ID, "sessionId": "sess-2"}
    assert [kw["name"] for kw in world.start_kwargs] == [rs.session_request_name(RUN, SCOPE_ID, n) for n in (1, 2)]
    _assert_paired(world.sink.events)


def test_discarded_attempt_with_a_failed_stop_is_unconfirmed_and_exits_1(world):
    world.nova_plan = [ConnectionError("reset")]
    world.stop_plan = [RuntimeError("stop failed")]
    assert rs.main() == 1
    assert _session_events(world.sink.events) == [
        _opened("sess-1"), _closed("sess-1", "unconfirmed"), _opened("sess-2"), _closed("sess-2")]


def test_connect_exhaustion_keeps_exit_80_with_every_session_paired_and_confirmed(world, monkeypatch):
    monkeypatch.setattr(rs, "_backoff_interrupted", lambda attempt: False)
    world.nova_plan = [ConnectionError("reset")] * rs._CONNECT_ATTEMPTS
    assert rs.main() == rs.EX_WORKER_NETWORK
    sids = [f"sess-{n}" for n in range(1, rs._CONNECT_ATTEMPTS + 1)]
    assert world.sink.events == [ev for sid in sids for ev in (_opened(sid), _closed(sid))]


def test_connect_exhaustion_with_an_unconfirmed_session_exits_1(world, monkeypatch):
    monkeypatch.setattr(rs, "_backoff_interrupted", lambda attempt: False)
    world.nova_plan = [ConnectionError("reset")] * rs._CONNECT_ATTEMPTS
    world.stop_plan = [None, RuntimeError("stop failed")]
    assert rs.main() == 1
    assert _session_events(world.sink.events)[3] == _closed("sess-2", "unconfirmed")


def test_start_failure_has_no_session_and_no_session_events(world, monkeypatch):
    monkeypatch.setattr(rs, "_backoff_interrupted", lambda attempt: False)
    world.start_plan = [ConnectionError("reset")] * rs._CONNECT_ATTEMPTS
    assert rs.main() == rs.EX_WORKER_NETWORK
    assert world.sink.events == [] and not any(t[0] == "stop" for t in world.trace)


def test_stop_signal_while_start_is_unanswered_emits_one_attempted_pair_and_exits_1(world, monkeypatch):
    """Start 已发出、停止信号到达、等待窗口内仍没有返回：会话 id 不在手里，发一对 attempted（sessionId 为 null、name 取请求名），
    不发 Stop、不进 NovaAct，以退出码 1 结束；等待有界，不等 Start 返回。"""
    monkeypatch.setattr(rs, "START_SETTLE_S", 0.2)
    unblock = threading.Event()

    def hang():
        rs._stop.set()
        unblock.wait(10)

    world.start_plan = [hang]
    t0 = time.monotonic()
    try:
        assert rs.main() == 1
        elapsed = time.monotonic() - t0
    finally:
        unblock.set()
    name = rs.session_request_name(RUN, SCOPE_ID, 1)
    assert world.sink.events == [
        {"type": "session_opened", "scopeId": SCOPE_ID, "sessionId": None, "name": name, "origin": "attempted"},
        {"type": "session_closed", "scopeId": SCOPE_ID, "sessionId": None, "name": name, "release": "unconfirmed"},
    ]
    assert not any(t[0] in ("stop", "nova_init", "ws_headers") for t in world.trace)
    assert elapsed < 5
    _assert_paired(world.sink.events)


def test_stop_signal_while_start_answers_within_the_window_pairs_a_created_session(world, monkeypatch):
    """停止信号到达时 Start 在途、在等待窗口内返回：会话已建起，发 session_opened（血缘）后直接按停止释放——不取连接头、不建
    NovaAct 连接、不发 scope_started（它表示被测对象已就绪、下一事件是首个 scenario_started，ADR 0051 决策 4），以 0 退出。"""
    monkeypatch.setattr(rs, "START_SETTLE_S", 2.0)

    def late():
        rs._stop.set()
        time.sleep(0.1)

    world.start_plan = [late]
    assert rs.main() == 0
    assert world.sink.events == [_opened("sess-1"), _closed("sess-1")]
    assert "scope_started" not in _types(world)
    assert not any(e.get("origin") == "attempted" for e in world.sink.events)
    assert not any(t[0] in ("ws_headers", "nova_init") for t in world.trace)
    assert ("stop", "sess-1") in world.trace


@pytest.mark.parametrize("arrival", ["novaact_connect", "extra_headers", "warmup_leave"])
def test_stop_signal_after_start_but_before_scope_started_pairs_the_session_without_scope_started(world, monkeypatch, arrival):
    """停止信号落在会话建立之后、scope_started 之前的任一处（建 NovaAct 连接、设置额外请求头、预热就绪后离开预热页）：
    不发 scope_started、不进 scenario，关掉 NovaAct 连接并释放会话，会话照样成对，以 0 退出。"""
    if arrival == "novaact_connect":
        def nova_factory(**k):
            rs._stop.set()
            return _Nova(world)

        monkeypatch.setattr(rs, "NovaAct", nova_factory)
    elif arrival == "extra_headers":
        world.page.context = type("Ctx", (), {"set_extra_http_headers": staticmethod(lambda h: rs._stop.set())})()
        monkeypatch.setenv(C.EXTRA_HTTP_HEADERS_ENV, '{"ngrok-skip-browser-warning": "1"}')
        monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)  # 带额外请求头的 job 总有预热地址
    else:
        class _StopOnLeavePage(_Page):
            def goto(self, url, **kw):
                if url == "about:blank":  # 预热已读到就绪标记，正在离开预热页
                    rs._stop.set()
                return super().goto(url, **kw)

        world.page = _StopOnLeavePage([200], [C.WARMUP_TITLES["ready"]])
        monkeypatch.setenv(C.SESSION_WARMUP_URL_ENV, WARMUP_URL)
    assert rs.main() == 0
    assert world.sink.events == [_opened("sess-1"), _closed("sess-1")]
    assert ("nova_exit",) in world.trace and ("stop", "sess-1") in world.trace
    assert not any(t[0] == "run_scenario" for t in world.trace)


def test_start_raising_after_the_stop_signal_is_a_plain_connect_failure(world, monkeypatch):
    """停止信号后 Start 在窗口内报错：没有会话、结果已知，不发 attempted，按停止路径以 0 退出。"""
    monkeypatch.setattr(rs, "START_SETTLE_S", 2.0)

    def fail():
        rs._stop.set()
        raise ConnectionError("reset")

    world.start_plan = [fail]
    assert rs.main() == 0
    assert world.sink.events == []


def test_missing_run_id_fails_before_any_session_with_a_product_message(world, monkeypatch, capsys):
    for value in (None, ""):
        if value is None:
            monkeypatch.delenv("RUN_ID", raising=False)
        else:
            monkeypatch.setenv("RUN_ID", value)
        assert rs.main() == 1
        assert world.start_kwargs == [] and world.sink.events == []
        err = capsys.readouterr().err
        assert "RUN_ID" in err and "命名" in err
        for internal in ("ADR", "决策", "session_request_name", "run_scope"):
            assert internal not in err, err


def test_precheck_rejection_does_not_need_run_id(world, monkeypatch):
    monkeypatch.delenv("RUN_ID", raising=False)
    world.job = _job(target={"device": "android", "uiKind": "web"})
    assert rs.main() == 0
    assert _types(world) == ["scope_done"] and world.sink.events[0]["errorType"] == "precheck_failed"
