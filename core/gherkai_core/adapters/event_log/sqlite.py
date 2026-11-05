"""SqliteEventLog（ADR 0034；ADR 0042 决策七起同步 run 也写）：本机后端的持久事件通道。

worker 事件（原始 ADR 0024 JSON 行 + worker 段单调 seq）+ 平台侧退出记录（task_exited，独立键空间）
都落一个本机 SQLite 文件；reconciler 从这里全量重放（`records()` → `project()` 的 EventRecord 列表）。

**为何存原始 JSON 行、不存结构化 Event**：worker fd3 吐的本就是 ADR 0024 JSON 行；存原样 + 读回用现有
`wire.event_from_line`（零新序列化，不在 wire 加 event_to_json 破坏其 worker→core 单向契约）。

**表结构镜像 DDB events 表**（[0024]/[0034]）：
- events 表：(scope_id, seq) 复合主键，line 存原始 JSON 行，emit_ts 存 worker emit 墙钟（reduce_event 的 now）。
  worker 段单调数值 seq——per-run 进程读 fd3 时按到达顺序 1,2,3… 赋（worker 一个 scope 串行 emit）。
- exits 表：(scope_id) 主键，exit_code（NULL 表示退出码未知，仅超时处置直写时出现；投影判 ERROR、非宽限）+ timed_out（超时处置
  所致退出的归因标志，[0034]「job timeout」节）+ reason（退出原因的归因串，与 `PLATFORM_FAILED_EXIT` 哨兵一起写：本机只有
  tick 的 launch 失败补偿写它，内容为「起 worker 失败：异常文本」，per-run 进程与 `status --wait` 接力者推进时都可能写；
  观察到真实退出码的记录不带）。独立表即独立键空间（机制一：退出记录不占 worker 数值 seq 段、不参与断号）。

并发：detached 下 per-run 进程写、reconciler 读（同进程内两职责）；`status --wait` 接力者在另一进程里同样启动 worker、写同一文件
（事件、退出记录、为观察链已断的他人 claim 补写的超时退出记录），它不探测 per-run 进程是否存活、可能与之同时推进——同一 job
只被一方 claim（LocalRunStore 跨进程文件锁下的 CAS），两个进程的写由 WAL 写锁串行（ADR 0034「端到端流程」的 local 节）；
explain 在另一进程只读。同步 run 下 schedule 的各 worker 读线程各持一个 scope 的闭包写（每条一次连接加一次提交，SQLite 文件锁
串行）。SQLite WAL 模式 + 短事务，多读少写足够。`records()` 的两表在同一读事务内读取，保证一份快照：WAL 下自动提交模式每条
SELECT 各取一个快照，分两次读可能读到某 scope 的退出记录、却漏掉在它之前提交的末尾事件（如 scope_done），投影会把它判成 ERROR。
"""
from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from gherkai_core.project import EventRecord, TaskExited
from gherkai_core.wire import event_from_line


class SqliteEventLog:
    """本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。"""

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextlib.contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """一次调用一个短连接：块正常结束时提交、异常时回滚，随后关闭连接。

        `with sqlite3.connect(...)` 只管事务、不关连接，靠垃圾回收收尾会逐个发 ResourceWarning，故此处显式关闭。"""
        conn = sqlite3.connect(str(self._path), timeout=30.0)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            # 多读单写并发（reconciler 读 + per-run 写）；WAL 是库文件级的持久设置，建库时设一次即可，不必每次连接都设
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "  scope_id TEXT NOT NULL,"
                "  seq INTEGER NOT NULL,"
                "  line TEXT NOT NULL,"       # 原始 ADR 0024 JSON 行
                "  emit_ts REAL NOT NULL,"    # worker emit 墙钟（reduce_event 的 now）
                "  PRIMARY KEY (scope_id, seq)"  # 镜像 DDB 的 (PK, SK) 段；幂等重写同 (scope,seq) 无副作用
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS exits ("
                "  scope_id TEXT PRIMARY KEY,"  # 独立键空间（机制一）：退出记录不占 events 的 seq 段
                "  exit_code INTEGER,"          # NULL 表示退出码未知（仅超时处置直写；投影判 ERROR，机制二「退出码缺失」条）
                "  timed_out INTEGER NOT NULL DEFAULT 0,"  # 超时归因（ADR 0034「job timeout」节）
                "  reason TEXT"                 # 平台侧归因串（观察者落哨兵时带）
                ")"
            )
            # 不做加列迁移：读端在打开本库之前先核对 definition 结构版本、拒绝旧版本写出的 run（ADR 0037 决策 7），本库只会
            # 遇到当前结构；以后改表结构须同时把结构版本加 1，旧结构的库才会在同一处被拒。

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
        reason：退出原因的归因串（port 对称 DDB）。本机宿主拿得到真实退出码，观察到的退出不带它；只有 tick 的 launch 失败
        补偿（worker 没能启动、无退出码可观察，记 `PLATFORM_FAILED_EXIT` 哨兵）带「起 worker 失败：异常文本」。"""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO exits (scope_id, exit_code, timed_out, reason) VALUES (?, ?, ?, ?)",
                (scope_id, exit_code, 1 if timed_out else 0, reason),
            )

    def has_exit(self, scope_id: str) -> bool:
        """单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。"""
        with self._connect() as conn:
            return conn.execute(
                "SELECT 1 FROM exits WHERE scope_id = ?", (scope_id,)).fetchone() is not None

    def records(self) -> list[EventRecord]:
        """读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。

        events 行的原始 JSON 用 wire.event_from_line 解析回 model.Event（零新序列化）；exits 行成 TaskExited。
        两表在同一读事务内读取，保证一份快照（见模块头「并发」段）：读到某 scope 的退出记录时，写端在它之前提交的
        事件必然也在。
        """
        recs: list[EventRecord] = []
        with self._connect() as conn:
            # deferred 读事务：WAL 下第一条 SELECT 起固定单一快照，块结束时提交即结束读事务
            conn.execute("BEGIN")
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
