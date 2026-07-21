"""SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。

存原始 JSON 行→读回解析成 Event、退出记录独立键空间、max_seq 续号；records() 喂 project() 得正确 RunState。
纯逻辑 + 本地 SQLite（无 AWS、无 mock 外真实行为）→ 绿即够。
"""
from __future__ import annotations

from core.adapters.event_log import SqliteEventLog
from core.model import Job, RunMeta, Scenario, Status, Step
from core.project import project


def _log(tmp_path) -> SqliteEventLog:
    return SqliteEventLog(tmp_path / "events.db")


def test_append_and_read_back_events(tmp_path):
    log = _log(tmp_path)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a","sessionId":"s1"}', 100.0)
    log.append_event("a", 2, '{"type":"scope_done","scopeId":"a"}', 101.0)
    recs = log.records()
    evs = [r for r in recs if r.kind == "event"]
    assert len(evs) == 2
    assert evs[0].seq == 1 and evs[0].emit_ts == 100.0
    assert evs[0].event.type == "scope_started" and evs[0].event.session_id == "s1"
    assert evs[1].event.type == "scope_done"


def test_exit_record_independent_keyspace(tmp_path):
    """退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。"""
    log = _log(tmp_path)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a"}', 1.0)
    log.record_exit("a", 0)
    recs = log.records()
    exits = [r for r in recs if r.kind == "exit"]
    assert len(exits) == 1
    assert exits[0].exited.scope_id == "a" and exits[0].exited.exit_code == 0
    # events 段的 max_seq 不受 exit 影响
    assert log.max_seq("a") == 1


def test_exit_code_none_stored(tmp_path):
    """exitCode 宽限态（None）可存（机制二兜底）。"""
    log = _log(tmp_path)
    log.record_exit("a", None)
    exits = [r for r in log.records() if r.kind == "exit"]
    assert exits[0].exited.exit_code is None


def test_append_idempotent_same_seq(tmp_path):
    """同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。"""
    log = _log(tmp_path)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a"}', 1.0)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a"}', 2.0)  # 重写
    evs = [r for r in log.records() if r.kind == "event"]
    assert len(evs) == 1  # 不重复
    assert evs[0].emit_ts == 2.0  # 后写覆盖


def test_max_seq_empty_is_zero(tmp_path):
    assert _log(tmp_path).max_seq("nope") == 0


def test_records_feed_project_to_terminal(tmp_path):
    """端到端：SQLite records() → project() 推出正确终态（两件都要齐 → passed）。"""
    log = _log(tmp_path)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a","sessionId":"s"}', 1.0)
    log.append_event("a", 2, '{"type":"scenario_done","scenarioId":"a:1","status":"passed"}', 2.0)
    log.append_event("a", 3, '{"type":"scope_done","scopeId":"a"}', 3.0)
    log.record_exit("a", 0)

    meta = RunMeta(run_id="r", created_at="t", jobs=(
        Job(scope_id="a", scope_name="a", engine="novaact",
            scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),)),
    ))
    state = project(meta, log.records())
    assert state.jobs["a"].status == Status.PASSED
    assert state.jobs["a"].session_id == "s"
    assert state.high_water_mark == 3
