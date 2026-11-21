"""SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。

存原始 JSON 行→读回解析成 Event、退出记录独立键空间、max_seq 续号；records() 喂 project() 得正确 RunState。
纯逻辑 + 本地 SQLite（无 AWS、无 mock 外真实行为）→ 绿即够。库文件路径的长度上限（`DB_PATH_MAX_BYTES`）是解释器自带的 SQLite
的真实行为，用真实的长路径打开一次守住前提（ADR 0030 决定四「报告目录的路径长度」条）。
"""
from __future__ import annotations

import os

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.adapters.event_log.sqlite import DB_PATH_MAX_BYTES
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


def test_exit_code_none_stored(tmp_path):
    """exit_code=None（退出码未知：启动失败补偿、wait 取不到退出码等）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034 机制二「退出码缺失」条）。"""
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
            scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0),
    ), deadline_at="2026-01-01T01:00:00+00:00")
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


def test_record_exit_exited_at_roundtrip(tmp_path):
    """退出时刻（带时区）随退出记录落库、读回为同一时刻；记录里写成 UTC 的 ISO 串（serialize.instant_to_iso）。不传则 None。"""
    import contextlib
    import sqlite3
    from datetime import datetime, timedelta, timezone

    log = _log(tmp_path)
    at = datetime(2026, 7, 19, 8, 0, 1, 250000, tzinfo=timezone(timedelta(hours=8)))
    log.record_exit("a", 3, exited_at=at)
    log.record_exit("b", 0)
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert exits["a"].exited_at == at and exits["a"].exited_at.utcoffset() == timedelta(0)
    assert exits["b"].exited_at is None
    with contextlib.closing(sqlite3.connect(tmp_path / "events.db")) as conn:
        stored = dict(conn.execute("SELECT scope_id, exited_at FROM exits"))
    assert stored == {"a": "2026-07-19T00:00:01.250000+00:00", "b": None}


def test_record_exit_overwrites_the_same_scope(tmp_path):
    """退出记录按 scope 覆盖同键（INSERT OR REPLACE）：同一个 scope 后写的一条整条替换先写的一条（含超时标志与退出时刻），别的 scope
    不受影响。"""
    from datetime import datetime, timezone

    log = _log(tmp_path)
    at = datetime(2026, 7, 19, tzinfo=timezone.utc)
    log.record_exit("a", None, timed_out=True)
    log.record_exit("b", 1)
    log.record_exit("a", 0, exited_at=at)
    exits = {r.scope_id: r.exited for r in log.records() if r.kind == "exit"}
    assert (exits["a"].exit_code, exits["a"].timed_out, exits["a"].exited_at) == (0, False, at)
    assert (exits["b"].exit_code, exits["b"].timed_out) == (1, False)


def test_records_reads_events_and_exits_from_one_snapshot(tmp_path, monkeypatch):
    """records() 的两表在同一读事务内读取：读 events 期间另一连接提交了末尾事件与退出记录，结果里两者要么都在、要么都不在。

    分两次各取快照时会读到退出记录、却漏掉在它之前提交的 scope_done，投影把「退出码 0、无 scope_done」判成 ERROR。"""
    from gherkai_core.adapters.event_log import sqlite as sqlite_mod

    path = tmp_path / "events.db"
    reader = SqliteEventLog(path)
    writer = SqliteEventLog(path)
    reader.append_event("a", 1, '{"type":"scope_started","scopeId":"a"}', 1.0)
    reader.append_event("a", 2, '{"type":"scenario_done","scenarioId":"a:1","status":"passed"}', 2.0)

    real_event_from_line = sqlite_mod.event_from_line
    calls = {"n": 0}

    def interleaving_event_from_line(line):
        calls["n"] += 1
        if calls["n"] == 1:  # reader 正在逐行解析 events 结果集时，写端按真实次序先提交事件、再提交退出记录
            writer.append_event("a", 3, '{"type":"scope_done","scopeId":"a"}', 3.0)
            writer.record_exit("a", 0)
        return real_event_from_line(line)

    monkeypatch.setattr(sqlite_mod, "event_from_line", interleaving_event_from_line)
    recs = reader.records()
    seqs = {r.seq for r in recs if r.kind == "event"}
    got_exit = any(r.kind == "exit" for r in recs)
    assert (3 in seqs) == got_exit


def test_every_call_closes_its_connection(tmp_path):
    """每次调用的短连接都显式关闭：`with sqlite3.connect(...)` 只管事务，不关闭的连接被回收时逐个发 ResourceWarning。"""
    import gc
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        log = _log(tmp_path)
        log.append_event("a", 1, '{"type":"scope_started","scopeId":"a"}', 1.0)
        log.record_exit("a", 0)
        log.records()
        log.max_seq("a")
        gc.collect()
    assert [w for w in caught if issubclass(w.category, ResourceWarning)] == []


def _path_of_exactly(base, total: int, *, filename: str = "events.db"):
    """base 之下一条按文件系统编码恰好 total 字节的库文件路径（base 先解析成真实路径：SQLite 按解析之后的真实路径计长度）。中间
    各层名字不超过 200 字节，最后一层是 filename。"""
    base = base.resolve()
    fixed = len(os.fsencode(str(base / filename)))
    room = total - fixed  # 中间各层连同各自前面的「/」共占的字节数
    assert room >= 2, "前提：临时目录的路径比上限短"
    parts = []
    while room > 0:
        take = min(201, room)  # 一层：「/」加至多 200 字节的名字
        if room - take == 1:   # 不留下只够一个「/」的零头
            take -= 1
        parts.append("d" * (take - 1))
        room -= take
    path = base.joinpath(*parts, filename)
    assert len(os.fsencode(str(path))) == total
    return path


def test_a_database_path_of_exactly_the_limit_opens_with_this_interpreters_sqlite(tmp_path):
    """前提守护：当前解释器链接的 SQLite 打开恰好 `DB_PATH_MAX_BYTES` 字节的库文件路径成功（WAL 模式，写入与读回各一次）。报告目录
    的长度上限由这个数推出；所用的 SQLite 上限更小时这条失败，470 字节之内的报告目录上也可能打不开事件库（ADR 0030 决定四「报告
    目录的路径长度」条）。"""
    import contextlib
    import sqlite3

    path = _path_of_exactly(tmp_path, DB_PATH_MAX_BYTES)
    log = SqliteEventLog(path)
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a"}', 1.0)
    log.record_exit("a", 0)
    assert [r.kind for r in log.records()] == ["event", "exit"]
    with contextlib.closing(sqlite3.connect(str(path))) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone() == ("wal",)
