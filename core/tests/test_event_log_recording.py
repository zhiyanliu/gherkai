"""原始事件行记录器（ADR 0042 决策七）：同步 run 经 EventRecordingEngine 把 worker 事件行落 SqliteEventLog，与无状态运行的
launcher 共用 make_raw_sink。纯逻辑加真 SQLite 文件，绿即够。"""
from __future__ import annotations

import json

from gherkai_core.adapters.event_log import EventRecordingEngine, SqliteEventLog, make_raw_sink
from gherkai_core.model import Job, Scenario, Step


def _job(scope_id: str) -> Job:
    return Job(scope_id=scope_id, scope_name=scope_id, engine="novaact",
               scenarios=(Scenario(id=f"{scope_id}:1", name="s", steps=(Step(index=0, keyword="When", text="x"),)),))


class _StubEngine:
    """假装是 SubprocessEngine：run_scope(job, raw_sink) 把几行原始事件喂给 raw_sink 再返回。"""

    cmd = ["fake"]

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.calls: list[tuple[str, bool]] = []

    def run_scope(self, job, raw_sink=None):
        self.calls.append((job.scope_id, raw_sink is not None))
        for line in self.lines:
            raw_sink(line)
        return object(), iter(())


def test_recording_engine_appends_raw_lines_with_arrival_seq_and_forwards_the_rest(tmp_path):
    log = SqliteEventLog(tmp_path / "events.db")
    lines = [json.dumps({"type": "scope_started", "scopeId": "a"}), json.dumps({"type": "scope_done", "scopeId": "a"})]
    inner = _StubEngine(lines)
    engine = EventRecordingEngine(inner, log)
    engine.run_scope(_job("a"))
    assert inner.calls == [("a", True)]
    recs = log.records()
    assert [(r.scope_id, r.seq, r.event.type) for r in recs] == [("a", 1, "scope_started"), ("a", 2, "scope_done")]
    assert all(r.emit_ts is not None and r.emit_ts > 0 for r in recs)
    assert engine.cmd == ["fake"]  # 其余成员原样转发
    # 同一 scope 再起（重试）从已有 max_seq 续号，不覆盖
    engine.run_scope(_job("a"))
    assert [r.seq for r in log.records() if r.scope_id == "a"] == [1, 2, 3, 4]
    # 另一个 scope 独立计数
    engine.run_scope(_job("b"))
    assert [r.seq for r in log.records() if r.scope_id == "b"] == [1, 2]


def test_make_raw_sink_is_the_shared_writer(tmp_path):
    log = SqliteEventLog(tmp_path / "events.db")
    sink = make_raw_sink(log, "x")
    sink(json.dumps({"type": "scope_started", "scopeId": "x"}))
    assert [(r.seq, r.event.type) for r in log.records()] == [(1, "scope_started")]
    assert log.max_seq("x") == 1
