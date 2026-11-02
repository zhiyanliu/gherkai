"""原始事件行记录器（ADR 0042 决策七）：同步 run 经 EventRecordingEngine 把 worker 事件行落 SqliteEventLog，与无状态运行的
launcher 共用 make_raw_sink。纯逻辑加真 SQLite 文件，绿即够。"""
from __future__ import annotations

import json

import pytest

from gherkai_core.adapters.event_log import EventRecordingEngine, SqliteEventLog, make_raw_sink
from gherkai_core.model import Job, Scenario, Step


def _job(scope_id: str) -> Job:
    return Job(scope_id=scope_id, scope_name=scope_id, engine="novaact",
               scenarios=(Scenario(id=f"{scope_id}:1", name="s", steps=(Step(index=0, keyword="When", text="x"),)),))


class _StubHandle:
    def __init__(self, rc: int | None = 0, *, rc_after_stop: int | None = -15, rc_after_wait: int | None = None) -> None:
        self.rc = rc
        self.rc_after_stop = rc_after_stop
        self.rc_after_wait = rc_after_wait
        self.stopped: list[float] = []
        self.waited: list[float | None] = []

    def returncode(self):
        return self.rc

    def stop(self, grace):
        self.stopped.append(grace)
        self.rc = self.rc_after_stop  # 协作停：stop 等到整组消失，退出码就位（SIGTERM 的负码）

    def wait(self, timeout=None):
        self.waited.append(timeout)
        if self.rc_after_wait is None:
            import subprocess
            raise subprocess.TimeoutExpired("fake", timeout)
        self.rc = self.rc_after_wait
        return self.rc


class _StubEngine:
    """假装是 SubprocessEngine：run_scope(job, raw_sink) 把几行原始事件喂给 raw_sink，返回可控的句柄与事件迭代器。"""

    cmd = ["fake"]

    def __init__(self, lines: list[str], *, events=(), exit_error: Exception | None = None, handle: _StubHandle | None = None) -> None:
        self.lines = lines
        self.events = list(events)
        self.exit_error = exit_error
        self.handle = handle or _StubHandle()
        self.calls: list[tuple[str, bool]] = []

    def _iter(self):
        yield from self.events
        if self.exit_error is not None:
            raise self.exit_error

    def run_scope(self, job, raw_sink=None):
        self.calls.append((job.scope_id, raw_sink is not None))
        for line in self.lines:
            raw_sink(line)
        return self.handle, self._iter()


def test_recording_engine_appends_raw_lines_with_arrival_seq_and_forwards_the_rest(tmp_path):
    log = SqliteEventLog(tmp_path / "events.db")
    lines = [json.dumps({"type": "scope_started", "scopeId": "a"}), json.dumps({"type": "scope_done", "scopeId": "a"})]
    inner = _StubEngine(lines)
    engine = EventRecordingEngine(inner, log)
    _handle, events = engine.run_scope(_job("a"))
    assert inner.calls == [("a", True)]
    recs = [r for r in log.records() if r.kind == "event"]
    assert [(r.scope_id, r.seq, r.event.type) for r in recs] == [("a", 1, "scope_started"), ("a", 2, "scope_done")]
    assert all(r.emit_ts is not None and r.emit_ts > 0 for r in recs)
    assert engine.cmd == ["fake"]  # 其余成员原样转发
    assert not [r for r in log.records() if r.kind == "exit"]  # 事件流还没迭代完：退出记录未写
    list(events)
    assert [(r.scope_id, r.exited.exit_code) for r in log.records() if r.kind == "exit"] == [("a", 0)]  # 自然结束：按退出码 0 记
    # 同一 scope 再起（重试）从已有 max_seq 续号，不覆盖
    engine.run_scope(_job("a"))
    assert [r.seq for r in log.records() if r.scope_id == "a" and r.kind == "event"] == [1, 2, 3, 4]
    # 另一个 scope 独立计数
    engine.run_scope(_job("b"))
    assert [r.seq for r in log.records() if r.scope_id == "b" and r.kind == "event"] == [1, 2]


def test_recording_engine_writes_the_exit_record_on_nonzero_exit_and_on_stop(tmp_path):
    """worker 以非零退出码结束：按异常携带的退出码写退出记录并原样抛给调用方；schedule 主动 stop：停止完成后记（迭代器被放弃时不记），只记一次。"""
    from gherkai_core.errors import WorkerExitError
    log = SqliteEventLog(tmp_path / "events.db")
    failing = _StubEngine([], exit_error=WorkerExitError(80, "worker 异常退出 returncode=80"))
    _h, events = EventRecordingEngine(failing, log).run_scope(_job("a"))
    try:
        list(events)
    except WorkerExitError as e:
        assert e.exit_code == 80
    else:
        raise AssertionError("应原样抛出 WorkerExitError")
    assert [(r.scope_id, r.exited.exit_code) for r in log.records() if r.kind == "exit"] == [("a", 80)]
    stopped = _StubEngine([], handle=_StubHandle(rc=None))
    handle, events = EventRecordingEngine(stopped, log).run_scope(_job("b"))
    it = iter(events)
    it.close()  # schedule 停止后放弃迭代：不记
    assert not [r for r in log.records() if r.kind == "exit" and r.scope_id == "b"]
    handle.stop(5.0)
    assert stopped.handle.stopped == [5.0]
    assert [(r.scope_id, r.exited.exit_code) for r in log.records() if r.kind == "exit" and r.scope_id == "b"] == [("b", -15)]
    handle.stop(5.0)  # 再 stop 不重复记
    assert len([r for r in log.records() if r.kind == "exit" and r.scope_id == "b"]) == 1


def test_recording_handle_waits_briefly_for_the_exit_code_when_stop_returns_before_the_process_is_reaped(tmp_path):
    """stop 的 SIGKILL 兜底与二次中断都是发出即返回、不等内核回收，此刻 poll 还看不到码：记录器带超时 wait 一次取真码；
    仍拿不到才按退出码未知写（投影判 ERROR）。"""
    log = SqliteEventLog(tmp_path / "events.db")
    killed = _StubEngine([], handle=_StubHandle(rc=None, rc_after_stop=None, rc_after_wait=-9))
    handle, _events = EventRecordingEngine(killed, log).run_scope(_job("k"))
    handle.stop(0)
    assert killed.handle.waited == [2.0]
    assert [(r.scope_id, r.exited.exit_code) for r in log.records() if r.kind == "exit"] == [("k", -9)]
    stuck = _StubEngine([], handle=_StubHandle(rc=None, rc_after_stop=None, rc_after_wait=None))
    handle, _events = EventRecordingEngine(stuck, log).run_scope(_job("s"))
    handle.stop(0)
    assert [(r.scope_id, r.exited.exit_code) for r in log.records() if r.kind == "exit" and r.scope_id == "s"] == [("s", None)]


def test_make_raw_sink_is_the_shared_writer(tmp_path):
    log = SqliteEventLog(tmp_path / "events.db")
    sink = make_raw_sink(log, "x")
    sink(json.dumps({"type": "scope_started", "scopeId": "x"}))
    assert [(r.seq, r.event.type) for r in log.records() if r.kind == "event"] == [(1, "scope_started")]
    assert log.max_seq("x") == 1


def test_recording_engine_overwrites_an_unknown_exit_code_with_the_real_one_from_the_event_stream(tmp_path):
    """stop 的强杀分支返回时码仍未就位、有界 wait 也没等到：先按未知码写；随后 schedule 排空事件流读到带码的 WorkerExitError，
    用真码覆盖（同键 INSERT OR REPLACE）。反向不成立：已有真码时再来一个未知码不改。"""
    from gherkai_core.errors import WorkerExitError
    log = SqliteEventLog(tmp_path / "events.db")
    eng = _StubEngine([], exit_error=WorkerExitError(-9, "worker 被强制结束"), handle=_StubHandle(rc=None, rc_after_stop=None, rc_after_wait=None))
    handle, events = EventRecordingEngine(eng, log).run_scope(_job("k"))
    handle.stop(0)
    exits = lambda: [(r.scope_id, r.exited.exit_code) for r in log.records() if r.kind == "exit"]
    assert exits() == [("k", None)]
    with pytest.raises(WorkerExitError):
        list(events)
    assert exits() == [("k", -9)]
    handle.stop(0)  # 再 stop：码已就位为 None 的 stub 会再给 None，不覆盖真码
    assert exits() == [("k", -9)]


def test_exit_recorder_serializes_the_stop_thread_and_the_event_thread(tmp_path):
    """停止线程按未知码写、落库中途被挂起，事件线程同时拿到真码：两次写入串行、真码后写——终值是真码，不会被恢复的停止线程覆盖成未知码。"""
    import threading
    from gherkai_core.adapters.event_log.recording import _ExitRecorder

    writes: list[int | None] = []
    entered, release = threading.Event(), threading.Event()

    class _SlowLog:
        def record_exit(self, scope_id, exit_code, **kw):
            if exit_code is None:  # 只挂起未知码的落库（停止线程）：真码的写入不阻塞，没有锁时事件线程会抢先写、随后被恢复的停止线程覆盖
                entered.set()
                assert release.wait(5)
            writes.append(exit_code)

    rec = _ExitRecorder(_SlowLog(), "s", _StubHandle())
    stopper = threading.Thread(target=rec.record, args=(None,))
    stopper.start()
    assert entered.wait(5)
    eventer = threading.Thread(target=rec.record, args=(-9,))
    eventer.start()
    eventer.join(0.3)
    assert eventer.is_alive() and writes == []  # 事件线程在锁上等，没有抢先写
    release.set()
    stopper.join(5)
    eventer.join(5)
    assert writes == [None, -9]  # 未知码先落、真码覆盖；再来一个未知码不改
    rec.record(None)
    assert writes == [None, -9]
