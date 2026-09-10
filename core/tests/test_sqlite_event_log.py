"""SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。

存原始 JSON 行→读回解析成 Event、退出记录独立键空间、max_seq 续号；records() 喂 project() 得正确 RunState。
纯逻辑 + 本地 SQLite（无 AWS、无 mock 外真实行为）→ 绿即够。
"""
from __future__ import annotations

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.model import Job, RunMeta, Scenario, Status, Step
from gherkai_core.project import project


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


def test_has_exit_single_scope(tmp_path):
    """has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。"""
    log = _log(tmp_path)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a"}', 1.0)
    assert log.has_exit("a") is False
    log.record_exit("a", None)  # exit_code=None（退出码未知，超时直写形态）也算「退出记录已在」
    assert log.has_exit("a") is True
    assert log.has_exit("b") is False


def test_exit_code_none_stored(tmp_path):
    """exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034 机制二「退出码缺失」条）。"""
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


def test_record_exit_reason_roundtrip(tmp_path):
    """reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。"""
    log = _log(tmp_path)
    log.record_exit("a", 255, reason="TaskFailedToStart: CannotPullContainerError")
    log.record_exit("b", 0)
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert exits["a"].exit_code == 255 and exits["a"].reason == "TaskFailedToStart: CannotPullContainerError"
    assert exits["b"].reason is None


def test_opening_a_v140_shaped_db_adds_the_reason_column(tmp_path):
    """唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时
    `_init_schema` 补列且旧行照常读回。删这条 ALTER 前先看到这里变红——「不可达就删」的判据是 git tag 真值集，
    v1.4.0 的 CREATE TABLE 逐字：scope_id / exit_code / timed_out，无 reason。"""
    import sqlite3

    path = tmp_path / "events.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE exits (scope_id TEXT PRIMARY KEY, exit_code INTEGER, timed_out INTEGER NOT NULL DEFAULT 0)")
        conn.execute("INSERT INTO exits (scope_id, exit_code, timed_out) VALUES ('old', 0, 0)")
    log = SqliteEventLog(path)
    with sqlite3.connect(path) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(exits)")}
    assert "reason" in cols
    log.record_exit("new", 255, reason="TaskFailedToStart: x")
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert exits["old"].exit_code == 0 and exits["old"].reason is None
    assert exits["new"].reason == "TaskFailedToStart: x"
