"""SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。

worker 事件（原始 ADR 0024 JSON 行 + worker 段单调 seq）+ 平台侧退出记录（task_exited，独立键空间）
都落一个本机 SQLite 文件；reconciler 从这里全量重放（`records()` → `project()` 的 EventRecord 列表）。

**为何存原始 JSON 行、不存结构化 Event**：worker fd3 吐的本就是 ADR 0024 JSON 行；存原样 + 读回用现有
`wire.event_from_line`（零新序列化，不在 wire 加 event_to_json 破坏其 worker→core 单向契约）。

**表结构镜像 DDB events 表**（[0024]/[0034]）：
- events 表：(scope_id, seq) 复合主键，line=原始 JSON 行，emit_ts=worker emit 墙钟（reduce_event 的 now）。
  worker 段单调数值 seq——per-run 进程读 fd3 时按到达顺序 1,2,3… 赋（worker 一个 scope 串行 emit）。
- exits 表：(scope_id) 主键，exit_code（NULL=退出码未知，仅超时处置直写时出现；投影判 ERROR、非宽限）+ timed_out（超时处置
  所致退出的归因标志，[0034]「job timeout」节）+ reason（平台侧归因串，cloud 观察者落哨兵时带；local 恒空）。独立表 = 独立键空间（机制一：退出记录不占 worker 数值 seq 段、不参与断号）。

并发：per-run 进程写、reconciler 读（同进程内两职责，也可能 status --wait 另进程读）。SQLite WAL 模式 +
短事务，多读单写足够；跨进程写并发不在 local 目标内（写只有 per-run 进程一个）。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from gherkai_core.project import EventRecord, TaskExited
from gherkai_core.wire import event_from_line


class SqliteEventLog:
    """本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。"""

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path), timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # 多读单写并发（reconciler 读 + per-run 写）
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "  scope_id TEXT NOT NULL,"
                "  seq INTEGER NOT NULL,"
                "  line TEXT NOT NULL,"       # 原始 ADR 0024 JSON 行
                "  emit_ts REAL NOT NULL,"    # worker emit 墙钟（reduce_event 的 now）
                "  PRIMARY KEY (scope_id, seq)"  # 镜像 DDB PK=scope_id/SK=seq；幂等重写同 (scope,seq) 无副作用
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS exits ("
                "  scope_id TEXT PRIMARY KEY,"  # 独立键空间（机制一）：退出记录不占 events 的 seq 段
                "  exit_code INTEGER,"          # NULL = 退出码未知（仅超时处置直写；投影判 ERROR，机制二「退出码缺失」条）
                "  timed_out INTEGER NOT NULL DEFAULT 0,"  # 超时归因（ADR 0034「job timeout」节）
                "  reason TEXT"                 # 平台侧归因串（观察者落哨兵时带）
                ")"
            )
            # 旧库迁移（加列幂等）：只保留**已发行版本建过缺列 schema** 的那一列——v1.4.0 建的 exits 表没有 reason，新版接力
            # （status --wait）同一 run 的 events.db 时补列；已有列 → OperationalError，忽略。timed_out 的补列已删：首个含本文件
            # 的发行版 v1.3.0 的 CREATE TABLE 就带它、迁移不可达（判据 = git tag 真值集；新加列时照此加一条 ALTER，等最老
            # 受支持发行版都带它时再删）。
            try:
                conn.execute("ALTER TABLE exits ADD COLUMN reason TEXT")
            except sqlite3.OperationalError:
                pass

    def append_event(self, scope_id: str, seq: int, line: str, emit_ts: float) -> None:
        """追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。"""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO events (scope_id, seq, line, emit_ts) VALUES (?, ?, ?, ?)",
                (scope_id, seq, line, emit_ts),
            )

    def record_exit(self, scope_id: str, exit_code: int | None, *, timed_out: bool = False,
                    reason: str | None = None) -> None:
        """写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。

        timed_out：本次退出由超时处置的 stop 所致（launcher timer 标志，ADR 0034「job timeout」节归因链）。
        reason：平台侧归因串（port 对称 DDB；local 宿主拿得到真实退出码、通常不传）。"""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO exits (scope_id, exit_code, timed_out, reason) VALUES (?, ?, ?, ?)",
                (scope_id, exit_code, 1 if timed_out else 0, reason),
            )

    def has_exit(self, scope_id: str) -> bool:
        """单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。"""
        with self._connect() as conn:
            return conn.execute(
                "SELECT 1 FROM exits WHERE scope_id = ?", (scope_id,)).fetchone() is not None

    def records(self) -> list[EventRecord]:
        """读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。

        events 行的原始 JSON 用 wire.event_from_line 解析回 model.Event（零新序列化）；exits 行成 TaskExited。
        """
        recs: list[EventRecord] = []
        with self._connect() as conn:
            for scope_id, seq, line, emit_ts in conn.execute(
                "SELECT scope_id, seq, line, emit_ts FROM events ORDER BY scope_id, seq"
            ):
                recs.append(EventRecord(
                    scope_id=scope_id, kind="event", seq=seq,
                    event=event_from_line(line), emit_ts=emit_ts,
                ))
            for scope_id, exit_code, timed_out, reason in conn.execute(
                "SELECT scope_id, exit_code, timed_out, reason FROM exits"
            ):
                recs.append(EventRecord(
                    scope_id=scope_id, kind="exit",
                    exited=TaskExited(scope_id=scope_id, exit_code=exit_code, timed_out=bool(timed_out), reason=reason),
                ))
        return recs

    def max_seq(self, scope_id: str) -> int:
        """某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。"""
        with self._connect() as conn:
            row = conn.execute("SELECT MAX(seq) FROM events WHERE scope_id = ?", (scope_id,)).fetchone()
            return row[0] or 0 if row else 0
