"""--expose-local 与两种 submit 的交接在命令行一侧的测试（ADR 0035 决策 1 到 3）。

证据边界：隧道服务是登记进 `tunnel.PROVIDERS` 的假实现，只模仿口子的外部表面（前置检查的用例改为对 `tunnel._import_sdk` 打桩、走
真实的 `NgrokTunnel`）；云端存储是记录调用的假句柄，不连 AWS、不联网。submit 与后台进程之间用真实的管道与线程
（`_inline_children`）：两端都是生产代码，文件结束、EPIPE、非阻塞读与 Ctrl-C 的 SIGINT 都是真实的。SDK 与 ngrok 服务的真实行为、
跨进程的会话不在这些用例的证据之内（ADR 0035「实测项」）；进程入口的读输入与信号处置、submit 写出 run 标识之后到达的 Ctrl-C、前台 run
与本机后台推进进程建 run 期间到达的 SIGINT 另有用例真的启动子进程（不起隧道）。后台进程对 SIGINT 的缺省处置由进程入口设下，线程
替身直接执行主体、不经入口，所以它只由真实进程的用例核。

本机建 run 的边界检查与生命期锁（ADR 0054 决策三、四）在这里核前台 run 与本机 submit 两边同一情形同一句、会话先关再回报、推进期间
持锁：取锁、换名、改名都在真实文件系统上执行，文件系统类型经 conftest 的替身取本平台清单的第一项，只在要拒绝的用例里换成清单之外的
类型；起真实子进程、带 `real_filesystem` 标记的用例取宿主真实的类型（含真实内核上被拒的那一种）。
"""
from __future__ import annotations

import atexit
import errno
import json
import os
import signal
import sqlite3
import stat
import subprocess
import sys
import threading
import time
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import gherkai_cli.__main__ as m
from gherkai_core import run_deadline
from gherkai_core.adapters.run_store import run_dir
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobResult, Scenario, Status, Step
from gherkai_core.schedule import Execution
from gherkai_core.serialize import instant_from_iso, instant_to_iso
from gherkai_runtime import compose, detached, handoff
from gherkai_runtime import tunnel as gtunnel

from _inline_children import inline_children  # noqa: F401 —— 夹具：后台进程在线程里执行
from test_backend_cloud import _definition, _patch_cloud_handles

ORIGIN = "http://localhost:3000"
PUBLIC = "https://t.ngrok-free.app"
TOKEN = "a" * 32
WARMUP = gtunnel.warmup_url_for(PUBLIC, TOKEN)
ESTABLISHED = f"隧道已建立：{ORIGIN} → {PUBLIC}（访问受本次运行专用的会话保护；持有隧道的 gherkai 进程退出时隧道随之关闭）"
# 假墙钟的起点：整秒，远离真实时刻，用例若读了真实的钟就对不上
T0 = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
FAR_FUTURE = datetime(2100, 1, 1, tzinfo=timezone.utc)
FIXED_RUN_ID = "20300102T030405Z-abcdef"


def _write_feature(tmp_path: Path) -> Path:
    f = tmp_path / "t.feature"
    f.write_text('Feature: t\n  Scenario: s\n    When "打开 http://localhost:3000/login"\n', encoding="utf-8")
    return f


def _run_dirs(root: Path) -> list[Path]:
    return sorted(d for d in root.iterdir() if d.is_dir()) if root.exists() else []


class FakeTunnel:
    """登记进 `tunnel.PROVIDERS` 的假隧道服务：只模仿口子的外部表面（前置检查、起隧道、返回对象的 close），记下调用与先后。

    `events` 与假墙钟共用：起隧道记 ("start", closes_at)、第一次关闭记 ("close",)。close 照口子的约定可以重复调用、只有第一次动作。"""

    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.made = 0
        self.starts: list[dict] = []
        self.closed = False
        self.start_error: BaseException | None = None
        self.on_start = None  # 起隧道时（在起隧道的那个线程里）、返回之前调用

    def provider(self) -> "FakeTunnel":
        self.made += 1
        return self

    def check_prerequisites(self) -> None:
        self.events.append(("prereq",))

    def start(self, local_origin, *, closes_at, timeout_s=gtunnel.START_TIMEOUT_S):
        self.events.append(("start", closes_at))
        self.starts.append({"local_origin": local_origin, "closes_at": closes_at, "timeout_s": timeout_s})
        if self.on_start is not None:
            self.on_start()
        if self.start_error is not None:
            raise self.start_error
        return gtunnel.TunnelInfo(url=PUBLIC, local_origin=gtunnel.normalize_origin(local_origin), warmup_url=WARMUP,
                                  closer=self._close)

    def _close(self) -> None:
        if not self.closed:
            self.closed = True
            self.events.append(("close",))


class Clock:
    """`compose.now` 的替身：每读一次前进一秒，读数记进与假隧道服务共用的事件表，用来核对先后。"""

    def __init__(self, events: list, t0: datetime = T0) -> None:
        self.events = events
        self.t = t0

    def __call__(self) -> datetime:
        t = self.t
        self.t += timedelta(seconds=1)
        self.events.append(("now", t))
        return t


@pytest.fixture
def tunnel_service(monkeypatch) -> FakeTunnel:
    fake = FakeTunnel()
    monkeypatch.setitem(gtunnel.PROVIDERS, "ngrok", fake.provider)
    return fake


@pytest.fixture
def advanced(monkeypatch) -> list:
    """把后台推进进程的推进换成记录调用的函数：不起 worker，记下它收到的运行定义。"""
    calls: list = []
    monkeypatch.setattr(detached, "advance_local_run", lambda advancer, meta, **kw: calls.append((advancer, meta)))
    return calls


@pytest.fixture
def interrupt_submit(monkeypatch):
    """在后台进程的线程里给主线程（submit）发 SIGINT，等 submit 打出含 `marker` 的那一句之后再返回：Ctrl-C 落在 submit 等待期间。"""
    main_ident = threading.main_thread().ident
    seen: dict[str, threading.Event] = {}
    real_progress = m._progress

    def progress(*a, **k):
        real_progress(*a, **k)
        text = " ".join(str(x) for x in a)
        for marker, ev in seen.items():
            if marker in text:
                ev.set()

    monkeypatch.setattr(m, "_progress", progress)

    def make(marker: str):
        ev = seen.setdefault(marker, threading.Event())

        def interrupt() -> None:
            signal.pthread_kill(main_ident, signal.SIGINT)
            assert ev.wait(5), f"submit 没有在 5 秒内打出「{marker}」"
        return interrupt
    return make


def _main(argv: list[str]) -> int:
    """m.main，但 KeyboardInterrupt 漏出来即判失败（否则它会中止整个测试会话）。"""
    try:
        return m.main(argv)
    except KeyboardInterrupt:
        pytest.fail("Ctrl-C 没有被 submit 接住")


def _local_submit_argv(tmp_path: Path, *extra: str) -> list[str]:
    return ["submit", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports"),
            "--region", "us-east-1", *extra]


def _cloud_submit_argv(tmp_path: Path, *extra: str) -> list[str]:
    return ["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--ddb-table", "T", "--s3-bucket", "B",
            "--region", "us-east-1", *extra]


def _fake_schedule(box: dict):
    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        box["run_meta"] = run_meta
        return Execution(run_meta=run_meta, stopped_by=None, duration_ms=0.0,
                         results=tuple(JobResult(job=j, status=Status.PASSED) for j in run_meta.jobs))
    return fake_schedule


# ---- 前台 run（ADR 0035 决策 3「前台 `run`」）----

def test_run_expose_local_maps_jobs_and_injects_headers(tmp_path, monkeypatch, capsys, tunnel_service):
    """run --expose-local：job 文本中的 origin → 干净的隧道地址；skip 头与会话预热地址一起进 RunMeta（ADR 0035 决策 2/4；0051 决策 13）；
    公网地址那一行是三种组合共用的那一句。"""
    box: dict = {}
    monkeypatch.setattr(m, "schedule", _fake_schedule(box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--expose-local", ORIGIN])
    assert rc == 0
    meta = box["run_meta"]
    step = meta.jobs[0].scenarios[0].steps[0]
    assert f"{PUBLIC}/login" in step.text  # 替换成干净的隧道地址，不内嵌凭据、不附令牌
    assert "localhost:3000" not in step.text and TOKEN not in step.text
    assert dict(meta.extra_http_headers) == {"ngrok-skip-browser-warning": "1"}
    assert meta.session_warmup_url == WARMUP  # 预热地址随 definition 走
    assert [s["local_origin"] for s in tunnel_service.starts] == [ORIGIN]
    assert ESTABLISHED in capsys.readouterr().err.splitlines()


def test_run_takes_the_creation_instant_before_starting_the_tunnel_and_closes_it_at_exit(tmp_path, monkeypatch,
                                                                                          tunnel_service):
    """前台 run 的次序（ADR 0035 决策 3「三种组合的宿主与次序」）：先取创建时刻，再起隧道，再生成运行定义；隧道的到点时刻是运行期限加
    300 秒；run_id 的时间前缀取同一次读数。会话经 atexit 关闭：执行期间不关，退出时关（ADR 0035 决策 3「寿命」）。"""
    box: dict = {}
    registered: list = []
    monkeypatch.setattr(compose, "now", Clock(tunnel_service.events))
    monkeypatch.setattr(m, "schedule", _fake_schedule(box))
    monkeypatch.setattr(atexit, "register", lambda fn, *a, **k: registered.append(fn) or fn)
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--expose-local", ORIGIN]) == 0
    meta = box["run_meta"]
    created = instant_from_iso(meta.created_at)
    events = tunnel_service.events
    assert events.index(("now", created)) < events.index(("start", tunnel_service.starts[0]["closes_at"]))
    assert tunnel_service.starts[0]["closes_at"] == run_deadline.overdue_at(instant_from_iso(meta.deadline_at))
    assert meta.run_id.startswith(created.strftime("%Y%m%dT%H%M%SZ"))
    closers = [fn for fn in registered if isinstance(getattr(fn, "__self__", None), gtunnel.TunnelInfo)]
    assert len(closers) == 1 and not tunnel_service.closed
    closers[0]()
    assert tunnel_service.closed


def test_run_wires_session_warmup_url_into_local_engines(tmp_path, monkeypatch, tunnel_service):
    """同步本机 run：注给 build_engines 的预热地址与写进 definition 的是同一个值（ADR 0051 决策 13）——预热地址四处接线之一；
    丢了它 worker 会按 definition 完整性判 precheck_failed，而单测 fake 掉 schedule 后没有任何事能暴露这一处漏接。"""
    box: dict = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box["kwargs"] = kwargs
        return real_build(run_id=kwargs["run_id"])

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule(box))
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--expose-local", ORIGIN]) == 0
    assert box["kwargs"]["session_warmup_url"] == WARMUP == box["run_meta"].session_warmup_url
    assert box["kwargs"]["extra_http_headers"] == {"ngrok-skip-browser-warning": "1"}


def test_run_without_expose_local_zero_change(tmp_path, monkeypatch, tunnel_service):
    """不给 --expose-local：隧道服务一次都没有构造（前置检查也不做），meta 无 headers（默认路径零变化，ADR 0035 边界）。"""
    box: dict = {}
    monkeypatch.setattr(m, "schedule", _fake_schedule(box))
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report"]) == 0
    assert tunnel_service.made == 0
    assert box["run_meta"].extra_http_headers is None and box["run_meta"].session_warmup_url is None


def test_run_tunnel_failure_prints_the_sentence_as_is_and_exits_2(tmp_path, monkeypatch, capsys, tunnel_service):
    """隧道起不来：原样打印隧道给出的那一句（不另加前缀）、退出码 2，不开始执行；会话没有建成，所以没有关闭调用。"""
    sentence = "隧道没有建成：authentication failed（ERR_NGROK_105）。"
    tunnel_service.start_error = gtunnel.TunnelError(sentence)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("隧道起不来时不该开始执行"))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--expose-local", ORIGIN])
    assert rc == 2
    cap = capsys.readouterr()
    assert sentence in cap.err.splitlines() and cap.out == ""
    assert not tunnel_service.closed


def test_ctrl_c_while_starting_the_tunnel_stops_run_with_one_sentence(tmp_path, monkeypatch, capsys, tunnel_service):
    """前台 run 在起隧道期间按 Ctrl-C：一句「已停止，没有开始执行。」、退出码 130，不打回溯，不开始执行、不落库；与本机 submit 在同一
    时段被中断时一样只给一句说明。"""
    tunnel_service.start_error = KeyboardInterrupt()
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("起隧道被中断时不该开始执行"))
    reports = tmp_path / "reports"
    rc = _main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--expose-local", ORIGIN])
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == ""
    assert "已停止，没有开始执行。" in cap.err.splitlines() and "Traceback" not in cap.err
    assert len(tunnel_service.starts) == 1 and not reports.exists()


def _report_dir_is_a_file(tmp_path: Path) -> tuple[Path, int]:
    occupied = tmp_path / "reports"
    occupied.write_text("not a directory", encoding="utf-8")
    return occupied, errno.ENOTDIR


def _report_dir_under_a_closed_directory(tmp_path: Path) -> tuple[Path, int]:
    if os.geteuid() == 0:
        pytest.skip("root 不受目录权限限制")
    closed = tmp_path / "closed"
    closed.mkdir(mode=0o000)
    return closed / "reports", errno.EACCES


def _report_dir_is_a_symlink_loop(tmp_path: Path) -> tuple[Path, int]:
    (tmp_path / "loop-a").symlink_to(tmp_path / "loop-b")
    (tmp_path / "loop-b").symlink_to(tmp_path / "loop-a")
    return tmp_path / "loop-a", errno.ELOOP


@pytest.mark.parametrize("arrange", [_report_dir_is_a_file, _report_dir_under_a_closed_directory,
                                     _report_dir_is_a_symlink_loop], ids=["file", "no-permission", "symlink-loop"])
@pytest.mark.parametrize("command", ["run", "submit"])
def test_report_dir_that_cannot_be_opened_is_reported_before_the_tunnel_as_a_record_write_failure(
        command, arrange, tmp_path, monkeypatch, capsys, tunnel_service, inline_children, advanced):
    """报告目录打不开（位置被文件占着、上级没有权限、符号链接成环）：run 与本机 submit 在前置检查里给出写记录失败的同一句，退出码 2、
    不打回溯（ADR 0054 决策四：这类失败按写记录失败报，不当作判断不了）；不补全运行定义、不起隧道，submit 不启动后台推进进程。"""
    target, code = arrange(tmp_path)
    monkeypatch.setattr(m, "_complete_local_definition", _forbid("补全本机运行定义"))
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("写记录失败时不该开始执行"))
    extra = ["--region", "us-east-1"] if command == "submit" else []
    try:
        rc = m.main([command, str(_write_feature(tmp_path)), "--report-dir", str(target), *extra, "--expose-local", ORIGIN])
    finally:
        if target.parent.name == "closed":
            target.parent.chmod(0o755)
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == "" and "Traceback" not in cap.err
    assert cap.err.splitlines()[-1] == (
        f"在报告目录 {target} 里写这个 run 的记录失败：[Errno {code}] {os.strerror(code)}: '{target}'。"
        "还没有开始执行；请检查这个目录的读写权限与所在磁盘的剩余空间后重新执行。")
    assert tunnel_service.starts == [] and inline_children.children == []


def test_run_event_store_failure_after_the_record_exits_2_and_leaves_the_run_pending(tmp_path, monkeypatch, capsys):
    """前台 run 的记录已写下、建事件库失败（sqlite3.Error 不是 OSError）：说明记录已写下、停在 pending，给出把它记为已结束的 settle-runs
    整条命令再重新执行（经 submit 报出的那一句说重新提交），退出码 2、不打回溯。起好隧道之后装上的中断处理器在这个出口同样恢复原状。"""
    from gherkai_core.adapters import event_log

    def broken_event_log(path):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(event_log, "SqliteEventLog", broken_event_log)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("准备执行用的文件失败时不该开始执行"))
    reports = tmp_path / "reports"
    before = (signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    assert rc == 2
    assert (signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)) == before
    (run_dir,) = _run_dirs(reports)
    err = capsys.readouterr().err
    assert err.splitlines()[-1] == (
        f"run {run_dir.name} 的记录已经写下，但在报告目录 {reports} 里准备执行用的文件失败：unable to open database file。"
        "还没有开始执行，这个 run 在记录里停在 pending。请检查这个目录所在磁盘的剩余空间与读写权限，再用 "
        f"gherkai settle-runs {run_dir.name} --report-dir {reports} 把这个 run 记为已结束，然后重新执行。")
    assert "Traceback" not in err
    assert LocalRunStore(reports).load_run_state(run_dir.name).status == Status.PENDING


def _raise_signal_at(when: str, monkeypatch, signum: int = signal.SIGINT) -> None:
    """在前台 run 起好隧道之后、启动第一个 job 之前的某一步里给本进程发一次真实的信号（`signal.raise_signal`；用例在主线程里执行，命令
    装的只记标志的处理器照常收到）。when：`before-the-call` 在建 run 的 store 装配时（建 run 的调用开始之前）；`before-rename`、
    `after-rename` 在建 run 的调用里，真实的改名之前或之后；`after-the-call` 在建 run 返回之后、建事件库时；`assembling-engines` 在
    建 run 之后、装配引擎时；`finalize` 在前台进程按中断做结束写的那一步的入口（RunPersistence.finalize 被调用、还没有写的时候）。"""
    if when == "before-the-call":
        real_build = compose.build_local_stores
        calls: list = []

        def build(**kw):
            calls.append(kw)
            if len(calls) == 1:  # 说明读运行态时还会再装配一次，那一次不发
                signal.raise_signal(signum)
            return real_build(**kw)

        monkeypatch.setattr(compose, "build_local_stores", build)
    elif when == "after-the-call":
        from gherkai_core.adapters import event_log

        real_event_log = event_log.SqliteEventLog

        def make_event_log(path):
            signal.raise_signal(signum)
            return real_event_log(path)

        monkeypatch.setattr(event_log, "SqliteEventLog", make_event_log)
    elif when == "assembling-engines":
        real_engines = compose.build_engines

        def build_engines(**kw):
            signal.raise_signal(signum)
            return real_engines(**kw)

        monkeypatch.setattr(compose, "build_engines", build_engines)
    elif when == "finalize":
        from gherkai_core.persist import RunPersistence

        real_finalize = RunPersistence.finalize

        def finalize(self, execution):
            signal.raise_signal(signum)
            return real_finalize(self, execution)

        monkeypatch.setattr(RunPersistence, "finalize", finalize)
    else:
        real_rename = os.rename

        def rename(src, dst, *a, **k):
            if not Path(src).name.startswith(run_dir.STAGING_PREFIX):
                return real_rename(src, dst, *a, **k)
            if when == "before-rename":
                signal.raise_signal(signum)
            real_rename(src, dst, *a, **k)
            if when == "after-rename":
                signal.raise_signal(signum)

        monkeypatch.setattr(os, "rename", rename)


def _assert_ended_by_the_interrupt(reports: Path) -> None:
    """建 run 之后、开始执行之前被中断的那个 run：由前台进程自己按说明表「使用方中断」一行结束（全部 job 记 skipped，run 记 aborted
    与那一句），报告已生成；没有留下暂存目录。"""
    assert os.listdir(reports) == [FIXED_RUN_ID]
    state = LocalRunStore(reports).load_run_state(FIXED_RUN_ID)
    assert (state.status, state.message) == (Status.ABORTED, "收到中断信号，余下的 job 不再启动")
    assert [(js.status, js.message) for js in state.jobs.values()] == [(Status.SKIPPED, "收到中断信号，本 job 没有启动")]
    assert state.ended_at is not None and (reports / FIXED_RUN_ID / "index.html").is_file()


def _ended_by_the_interrupt_line(reports) -> str:
    return (f"已停止：run {FIXED_RUN_ID} 已因中断记为已结束，没有 job 开始执行；"
            f"可用 gherkai status {FIXED_RUN_ID} --report-dir {reports} 查看。")


@pytest.mark.parametrize("when", ["before-the-call", "before-rename", "after-rename", "after-the-call", "assembling-engines"])
def test_ctrl_c_around_creating_the_run_ends_the_run_it_created(when, tmp_path, monkeypatch, capsys, lock_holder):
    """前台 run 起好隧道之后收到真实的 SIGINT：只记标志的处理器已装上，信号不打断正在做的一步，退出码 130，标准输出为空、不打回溯，命令
    结束之后信号的处置恢复原状。建 run 之前看到中断（信号在建 run 的调用开始之前到达）：不建 run、什么都没有留下，与起隧道期间被中断是
    同一句。信号在建 run 的调用里（改名之前或之后）、建事件库时或装配引擎时到达：run 照常建成，调用 schedule 之前看到中断，不启动任何
    job，这个进程持着锁、就是推进器，由它自己按「使用方中断」那一行做结束写并生成报告（ADR 0035 决策 3「前台 `run`」一条），末句说这个
    run 已因中断记为已结束；持有者收到的描述符与 run 目录同 inode、进程退出之前另开一次取锁得到「已被持有」。"""
    _fix_run_id(monkeypatch)
    _raise_signal_at(when, monkeypatch)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("启动第一个 job 之前已收到中断时不该调用 schedule"))
    reports = tmp_path / "reports"
    rc = _main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == "" and "Traceback" not in cap.err
    assert signal.getsignal(signal.SIGINT) is signal.default_int_handler  # 命令装的处理器已恢复
    if when == "before-the-call":
        assert cap.err.splitlines()[-1] == "已停止，没有开始执行。"
        assert (os.listdir(reports) if reports.exists() else []) == [] and lock_holder.fds == []
        return
    assert cap.err.splitlines()[-1] == _ended_by_the_interrupt_line(reports)
    _assert_ended_by_the_interrupt(reports)
    run = reports / FIXED_RUN_ID
    (fd,) = lock_holder.fds
    assert _same_inode(fd, run)
    another = os.open(run, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert run_dir.try_lock(another).state is run_dir.LockState.HELD
    finally:
        os.close(another)


@pytest.mark.parametrize("second", ["assembling-engines", "finalize"])
def test_ctrl_c_twice_around_creating_the_run_still_ends_it_by_the_interrupt(second, tmp_path, monkeypatch, capsys):
    """建 run 期间按一次 Ctrl-C、之后再按一次（第二次在装配引擎时，或在前台进程开始做那次结束写的入口）：两次都只记下，run 照常建成，
    由前台进程自己按「使用方中断」做结束写、生成报告；说已因中断记为已结束的那一句与记录、报告一致，退出码 130，不打回溯。"""
    _fix_run_id(monkeypatch)
    _raise_signal_at("after-rename", monkeypatch)
    _raise_signal_at(second, monkeypatch)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("启动第一个 job 之前已收到中断时不该调用 schedule"))
    reports = tmp_path / "reports"
    rc = _main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == "" and "Traceback" not in cap.err
    assert cap.err.splitlines()[-1] == _ended_by_the_interrupt_line(reports)
    _assert_ended_by_the_interrupt(reports)


def test_sigterm_before_the_first_job_ends_the_run_by_the_interrupt_and_exits_143(tmp_path, monkeypatch, capsys):
    """建 run 之后、启动第一个 job 之前收到的 SIGTERM 由同一个处理器记下：与 Ctrl-C 同一个出口（不启动 job，由前台进程自己按「使用方
    中断」做结束写、生成报告，同一句说明），退出码按信号取 143；SIGTERM 的处置随后恢复原状。"""
    _fix_run_id(monkeypatch)
    _raise_signal_at("assembling-engines", monkeypatch, signum=signal.SIGTERM)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("启动第一个 job 之前已收到中断时不该调用 schedule"))
    before = signal.getsignal(signal.SIGTERM)
    reports = tmp_path / "reports"
    rc = _main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 143 and cap.out == ""
    assert cap.err.splitlines()[-1] == _ended_by_the_interrupt_line(reports)
    _assert_ended_by_the_interrupt(reports)
    assert signal.getsignal(signal.SIGTERM) is before


def test_ctrl_c_before_the_first_job_without_a_record_says_nothing_started(tmp_path, monkeypatch, capsys):
    """`--no-report` 没有记录：装配引擎时收到的 Ctrl-C 在调用 schedule 之前看到，不启动任何 job，与建 run 之前被中断同一句，130。"""
    _raise_signal_at("assembling-engines", monkeypatch)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("启动第一个 job 之前已收到中断时不该调用 schedule"))
    rc = _main(["run", str(_write_feature(tmp_path)), "--no-report"])
    cap = capsys.readouterr()
    assert (rc, cap.out) == (130, "") and cap.err.splitlines()[-1] == "已停止，没有开始执行。"


def test_ctrl_c_again_while_ending_the_interrupted_run_does_not_cut_the_end_write(tmp_path, monkeypatch, capsys):
    """建 run 之后被中断、前台进程正在做那次结束写时又按了一次 Ctrl-C（这里在真实的结束写里发出）：只记下，不打断结束写与生成报告，
    结果与只按一次相同，不打回溯。"""
    _fix_run_id(monkeypatch)
    _raise_signal_at("after-the-call", monkeypatch)
    real_end_run = LocalRunStore.end_run

    def end_run(self, run_id, ending, *, ended_at):
        signal.raise_signal(signal.SIGINT)
        return real_end_run(self, run_id, ending, ended_at=ended_at)

    monkeypatch.setattr(LocalRunStore, "end_run", end_run)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("启动第一个 job 之前已收到中断时不该调用 schedule"))
    reports = tmp_path / "reports"
    rc = _main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == "" and "Traceback" not in cap.err
    assert cap.err.splitlines()[-1] == _ended_by_the_interrupt_line(reports)
    _assert_ended_by_the_interrupt(reports)


def test_end_write_failure_after_an_interrupt_before_execution_is_reported_without_a_traceback(tmp_path, monkeypatch,
                                                                                               capsys):
    """建 run 之后被中断、那次结束写本身失败（磁盘写不进）：不说已记为已结束，按运行期落库失败的说明结束，退出码仍按信号取 130，不打
    回溯；run 停在 pending。"""
    _fix_run_id(monkeypatch)
    _raise_signal_at("after-the-call", monkeypatch)

    def end_run(self, run_id, ending, *, ended_at):
        raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    monkeypatch.setattr(LocalRunStore, "end_run", end_run)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("启动第一个 job 之前已收到中断时不该调用 schedule"))
    reports = tmp_path / "reports"
    rc = _main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == "" and "Traceback" not in cap.err
    assert cap.err.splitlines()[-1].startswith(f"run {FIXED_RUN_ID} 读写本机的运行记录失败，执行已停止，没有输出汇总：")
    assert f"gherkai settle-runs {FIXED_RUN_ID} --report-dir {reports} 把这个 run 记为已结束，然后重新执行。" in cap.err
    assert "已因中断记为已结束" not in cap.err
    assert LocalRunStore(reports).load_run_state(FIXED_RUN_ID).status == Status.PENDING


def test_run_json_masks_tunnel_credentials_but_run_meta_keeps_them(tmp_path, monkeypatch, capsys, tunnel_service):
    """run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。

    stdout 里预热地址的令牌是 `***`、判定消息里的 userinfo 是 `***@`；run_meta.json 要被推进器读回执行，令牌必须原样在；
    jobs/*.json 只被 status / explain 读、step 文本已不含秘密。"""
    import json

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        results = []
        for j in run_meta.jobs:
            jr = JobResult(job=j, status=Status.FAILED, message="页面停在 https://u1:p1@t.ngrok-free.app/login 未跳转")
            results.append(jr)
            if on_job_complete is not None:
                on_job_complete(jr)
        return Execution(run_meta=run_meta, results=tuple(results), stopped_by=None, duration_ms=0.0)

    monkeypatch.setattr(m, "schedule", fake_schedule)
    report_dir = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--json", "--report-dir", str(report_dir), "--expose-local", ORIGIN])
    assert rc == 1
    out = capsys.readouterr().out
    doc = json.loads(out)                                   # 脱敏后仍是单一可解析文档
    assert "u1:p1@" not in out and TOKEN not in out
    step_text = doc["run_meta"]["jobs"][0]["scenarios"][0]["steps"][0]["text"]
    assert f"{PUBLIC}/login" in step_text  # step 文本本就不含秘密
    assert doc["run_meta"]["session_warmup_url"].endswith("gherkai_tunnel_token=***")  # 预热地址的令牌盖住
    assert doc["jobs"][0]["message"] == "页面停在 https://***@t.ngrok-free.app/login 未跳转"
    assert doc["artifacts"]["run_meta"].endswith("run_meta.json")   # 产物落点照常折进同一文档
    (run_dir,) = _run_dirs(report_dir)
    assert TOKEN in (run_dir / "run_meta.json").read_text(encoding="utf-8")  # 落盘的 definition 保留明文
    for jf in (run_dir / "jobs").glob("*.json"):
        assert TOKEN not in jf.read_text(encoding="utf-8")


def test_expose_local_rejects_worker_without_session_warmup_before_starting_tunnel(tmp_path, monkeypatch, capsys,
                                                                                   tunnel_service):
    """本机后端 --expose-local：worker 自述不声明会话预热支持 → 退出码 2，且隧道没有起（拒绝点在起隧道之前，ADR 0051 决策 13）。"""
    real = compose.query_capabilities
    monkeypatch.setattr(compose, "query_capabilities",
                        lambda engine, **kw: {k: v for k, v in real(engine, **kw).items() if k != compose.SESSION_WARMUP_KEY})
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--expose-local", ORIGIN])
    assert rc == 2
    assert "会话预热" in capsys.readouterr().err and tunnel_service.starts == []


# ---- plan 与入口校验（ADR 0035 决策 2）----

def test_plan_expose_local_annotates_not_replaces(tmp_path, capsys):
    """plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）；也不做隧道的前置检查——这里没有登记假的隧道服务，
    导入 SDK 就会被自动夹具判失败。"""
    rc = m.main(["plan", str(_write_feature(tmp_path)), "--expose-local", ORIGIN])
    assert rc == 0
    captured = capsys.readouterr()
    assert ORIGIN in captured.out  # 原始地址（替换前）
    assert "原始地址" in captured.err  # 标注在 stderr（诊断面）


@pytest.mark.parametrize("argv", [
    ["plan"],
    ["run", "--no-report"],
    ["submit"],
    ["submit", "--backend", "cloud"],
], ids=["plan", "run", "submit-local", "submit-cloud"])
def test_expose_local_rejects_non_origin_value_at_entry_before_starting_tunnel(argv, tmp_path, monkeypatch, capsys,
                                                                               tunnel_service, inline_children):
    """--expose-local 的取值带路径：plan / run / submit 在共享的入口校验阶段以退出码 2 结束，stderr 说明取值不是 origin，
    隧道没有起、submit 没有起后台进程、也没有落库（ADR 0035 决策 2）。"""
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("取值不是 origin 时不该进入执行"))
    reports = tmp_path / "reports"
    extra = ["--report-dir", str(reports)] if argv[0] == "submit" else []
    rc = m.main([argv[0], str(_write_feature(tmp_path)), *argv[1:], *extra, "--expose-local", f"{ORIGIN}/login"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "不是 origin" in err and f"{ORIGIN}/login" in err and "Traceback" not in err
    assert tunnel_service.starts == [] and inline_children.children == []
    assert not reports.exists()


def test_expose_local_trailing_slash_is_normalized_for_plan_and_tunnel(tmp_path, monkeypatch, capsys, tunnel_service):
    """末尾恰好一个斜杠：plan 通过、标注行显示归一化后的 origin；run 起隧道与映射用的是同一个归一化值（ADR 0035 决策 2）。"""
    feat = _write_feature(tmp_path)
    assert m.main(["plan", str(feat), "--expose-local", f"{ORIGIN}/"]) == 0
    assert f"注：{ORIGIN} 将在" in capsys.readouterr().err

    box: dict = {}
    monkeypatch.setattr(m, "schedule", _fake_schedule(box))
    assert m.main(["run", str(feat), "--no-report", "--expose-local", f"{ORIGIN}/"]) == 0
    assert [s["local_origin"] for s in tunnel_service.starts] == [ORIGIN]
    assert f"隧道已建立：{ORIGIN} → " in capsys.readouterr().err
    assert f"{PUBLIC}/login" in box["run_meta"].jobs[0].scenarios[0].steps[0].text


# ---- 隧道的前置检查（ADR 0035 决策 1「前置条件」）----

def _forbid(what: str):
    def forbidden(*a, **k):
        pytest.fail(f"前置检查不过时不该{what}")
    return forbidden


@pytest.mark.parametrize("missing", ["sdk", "token"])
@pytest.mark.parametrize("argv", [["run", "--no-report"], ["submit"], ["submit", "--backend", "cloud"]],
                         ids=["run", "submit-local", "submit-cloud"])
def test_tunnel_prerequisites_are_checked_before_upload_background_process_and_aws(argv, missing, tmp_path, monkeypatch,
                                                                                    capsys, inline_children):
    """缺隧道组件或令牌：run、本机 submit、云端 submit 都在共享的前置里以退出码 2 结束，给出同一句；不补全运行定义（不上传、不比对
    账号）、不解析 AWS 身份、不起后台进程、不落库，云端也没有解析后端。走真实的 NgrokTunnel，只对导入 SDK 那一处打桩。"""
    if missing == "sdk":
        def no_sdk():
            raise ModuleNotFoundError("No module named 'ngrok'", name="ngrok")
        monkeypatch.setattr(gtunnel, "_import_sdk", no_sdk)
        sentence = ("--expose-local 要用的隧道组件没有安装。请在安装 gherkai 时加上 tunnel 组件后重新执行，"
                    "例如 uv tool install 'gherkai[local,tunnel]'（已经装了别的组件的，要一并列出）。")
    else:
        sdk = types.SimpleNamespace(forward=_forbid("起隧道"), disconnect=_forbid("关闭会话"))
        monkeypatch.setattr(gtunnel, "_import_sdk", lambda: sdk)
        sentence = ("--expose-local 需要 ngrok 的令牌，但环境变量 NGROK_AUTHTOKEN 没有设置。"
                    "请在 ngrok 控制台取得令牌，设置 NGROK_AUTHTOKEN 后重新执行。")
    monkeypatch.setattr(m, "_complete_local_definition", _forbid("补全本机运行定义"))
    monkeypatch.setattr(m, "_complete_cloud_definition", _forbid("补全云端运行定义"))
    monkeypatch.setattr(m.compose, "resolve_aws_identity", _forbid("解析 AWS 身份"))
    monkeypatch.setattr(m.compose, "resolve_cloud_target", _forbid("解析云端后端"))
    monkeypatch.setattr(m, "schedule", _forbid("开始执行"))
    reports = tmp_path / "reports"
    rc = m.main([argv[0], str(_write_feature(tmp_path)), *argv[1:], "--report-dir", str(reports), "--expose-local", ORIGIN])
    assert rc == 2
    err = capsys.readouterr().err
    assert sentence in err.splitlines() and "Traceback" not in err
    assert inline_children.children == [] and not reports.exists()


# ---- 本机 submit：提交进程与后台推进进程（ADR 0035 决策 3「本机 `submit`」）----

def test_local_submit_hands_over_to_the_advancer_which_builds_and_advances_the_run(tmp_path, monkeypatch, capsys,
                                                                                    inline_children, tunnel_service,
                                                                                    advanced):
    """建成的一次：提交进程自己不建 run，以 `-P`、新会话启动后台推进进程，后台推进进程取创建时刻、起隧道、生成运行定义、建 run、
    回报；提交进程的 stdout 只有 run 标识，stderr 有公网地址那一行与查进度的命令。推进用的是写进记录的那一份运行定义，推进结束后
    会话被关闭。推进用的就是内存里生成的那一份（不从记录读回）：交给建 run、装配与推进的是同一个对象。"""
    monkeypatch.setattr(compose, "now", Clock(tunnel_service.events))
    handed: dict[str, list] = {"create_run": [], "assemble": []}
    real_create = LocalRunStore.create_run

    def spy_create(self, meta, initial_state):
        handed["create_run"].append(meta)
        return real_create(self, meta, initial_state)

    monkeypatch.setattr(LocalRunStore, "create_run", spy_create)
    real_assemble = detached.assemble_local_run

    def spy_assemble(meta, report_dir, **kw):
        handed["assemble"].append(meta)
        return real_assemble(meta, report_dir, **kw)

    monkeypatch.setattr(detached, "assemble_local_run", spy_assemble)
    reports = tmp_path / "reports"
    spawned: dict = {}
    inline_children.on_spawn = lambda argv, kw: spawned.update(argv=argv, kw=kw, run_dirs=_run_dirs(reports))
    rc = m.main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 0
    (run_dir,) = _run_dirs(reports)
    run_id = run_dir.name
    assert cap.out == f"{run_id}\n"
    assert ESTABLISHED in cap.err.splitlines()
    assert f"已提交（本机后台推进中）。查进度：gherkai status {run_id} --report-dir {reports}" in cap.err
    # 启动方式
    argv, kw = spawned["argv"], spawned["kw"]
    assert argv[:7] == [sys.executable, "-P", "-m", "gherkai_cli", "_reconcile", "--report-fd", argv[6]]
    assert kw["pass_fds"] == (int(argv[6]),) and kw["stdout"] == 2 and kw["stderr"] == 2
    assert kw["start_new_session"] is True
    assert spawned["run_dirs"] == []  # 启动后台推进进程时还没有任何 run：提交进程自己不建 run
    # 创建时刻先于起隧道；到点时刻是运行期限加 300 秒；run_id 的时间前缀取同一次读数
    meta = LocalRunStore(reports).load_run_meta(run_id)
    created = instant_from_iso(meta.created_at)
    closes_at = tunnel_service.starts[0]["closes_at"]
    assert tunnel_service.events.index(("now", created)) < tunnel_service.events.index(("start", closes_at))
    assert closes_at == run_deadline.overdue_at(instant_from_iso(meta.deadline_at))
    assert run_id.startswith(created.strftime("%Y%m%dT%H%M%SZ"))
    assert meta.session_warmup_url == WARMUP and dict(meta.extra_http_headers) == {"ngrok-skip-browser-warning": "1"}
    assert f"{PUBLIC}/login" in meta.jobs[0].scenarios[0].steps[0].text
    # 推进用的就是写进记录的那一份，且是内存里的同一个对象（不读回）；运行态带后台执行标记（只作描述）
    ((_advancer, advanced_meta),) = advanced
    assert advanced_meta == meta
    ((created_meta,), (assembled_meta,)) = handed["create_run"], handed["assemble"]
    assert created_meta is assembled_meta and assembled_meta is advanced_meta
    assert json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))["detached"] is True
    assert (run_dir / "reconcile.log").exists() and (run_dir / "events.db").exists()
    child = inline_children.only()
    assert child.returncode == 0 and child.redirected.is_set()
    assert tunnel_service.closed


def test_local_submit_without_expose_local_never_touches_the_tunnel(tmp_path, capsys, inline_children, tunnel_service,
                                                                    advanced):
    """不给 --expose-local：隧道服务一次都没有构造，没有公网地址那一行，照常建成。"""
    reports = tmp_path / "reports"
    rc = m.main(_local_submit_argv(tmp_path))
    inline_children.settle()
    cap = capsys.readouterr()
    (run_dir,) = _run_dirs(reports)
    assert rc == 0 and cap.out == f"{run_dir.name}\n"
    assert "隧道已建立" not in cap.err and tunnel_service.made == 0
    assert LocalRunStore(reports).load_run_meta(run_dir.name).session_warmup_url is None
    assert len(advanced) == 1


def test_local_submit_tunnel_failure_is_reported_by_submit_and_builds_no_run(tmp_path, capsys, inline_children,
                                                                             tunnel_service, advanced):
    """后台推进进程起不来隧道：回报原因，提交进程原样打出那一句、退出码 2，stdout 为空；没有 run 目录，会话没有建成、没有关闭调用。"""
    sentence = ("隧道没有建成：这个 ngrok 账号上另一条在线的隧道占用了同一个地址（ERR_NGROK_334）。"
                "请等那条隧道下线之后再试；如果它属于另一个带 --expose-local 的 gherkai 运行，持有它的进程退出之后它就会下线。")
    tunnel_service.start_error = gtunnel.TunnelError(sentence)
    rc = m.main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert sentence in cap.err.splitlines() and "已提交" not in cap.err
    assert _run_dirs(tmp_path / "reports") == [] and advanced == []
    assert inline_children.only().returncode == 2 and not tunnel_service.closed


def test_local_submit_reports_when_the_advancer_exits_before_reporting(tmp_path, monkeypatch, capsys, inline_children,
                                                                       tunnel_service, advanced):
    """后台推进进程在回报之前崩溃（这里是生成运行定义时）：提交进程读到回报管道的文件结束，说明它退出了、可能已经建立 run，给出不带
    run 标识的 settle-runs 整条命令（把执行它的进程已不在的 run 记为已结束、同时清理暂存目录），退出码 2；后台推进进程的 finally 照样
    关闭会话。"""
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(m, "_build_run_meta", boom)
    inline_children.expect_crash_before_report()
    reports = tmp_path / "reports"
    rc = m.main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert cap.err.splitlines()[-1] == (
        "后台推进进程在给出提交结果之前退出了，提交没有完成；它退出之前如果有输出，原因在上面。它退出之前可能已经建立了这个 run："
        f"可以用 gherkai settle-runs --report-dir {reports} 把执行它的进程已不在的 run 记为已结束，同时清理建立 run 时中断留下的暂存目录。"
        "处理好原因之后请重新提交。")
    inline_children.only().expect_error(RuntimeError)
    assert tunnel_service.closed and _run_dirs(reports) == [] and advanced == []


def _stopped_waiting(reports: Path) -> str:
    """本机 submit 等回报时被 Ctrl-C 打断的那一句：后台推进进程只在建 run 之前查一次提交命令是否还在，查过之后才被打断的照常建成，
    所以这一句只说可能建立、请先确认，不说不再建立。"""
    return ("已停止等待提交结果。这次提交可能仍会建立 run 并执行：后台推进进程在建立 run 之前查到提交命令已经退出时不建立、自行退出，"
            f"查过之后照常建立并执行。请先用 gherkai list-runs --report-dir {reports} 确认，再决定是否重新提交。")


def test_ctrl_c_while_waiting_lets_the_advancer_see_submit_gone_before_building_the_run(tmp_path, capsys,
                                                                                       inline_children, tunnel_service,
                                                                                       advanced, interrupt_submit):
    """Ctrl-C 落在后台推进进程起隧道期间（它查 submit 是否还在之前）：提交进程关闭标准输入、说明已停止等待、以 130 结束；后台推进进程
    查到标准输入读到文件结束，不建 run、不输出，关闭会话、以 2 退出。"""
    marker = "已停止等待提交结果。"
    tunnel_service.on_start = interrupt_submit(marker)
    reports = tmp_path / "reports"
    rc = _main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == ""
    assert _stopped_waiting(reports) in cap.err.splitlines()
    assert inline_children.only().returncode == 2
    assert _run_dirs(reports) == [] and advanced == [] and tunnel_service.closed


def test_ctrl_c_after_the_built_report_says_the_run_was_submitted(tmp_path, monkeypatch, capsys, inline_children,
                                                                 tunnel_service, advanced):
    """中断落在提交进程读到并解码了「建成」的回报之后、输出结果之前：run 已经提交，说明与云端 submit 建 run 之后被中断同型（run 的
    标识与查进度的命令），130，标准输出不输出；后台推进进程照常推进。"""
    real_progress = m._progress

    def progress(*a, **k):
        if a and str(a[0]).startswith("隧道已建立"):   # 解码回报之后的第一句输出
            raise KeyboardInterrupt
        real_progress(*a, **k)

    monkeypatch.setattr(m, "_progress", progress)
    reports = tmp_path / "reports"
    rc = _main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    (run_dir,) = _run_dirs(reports)
    run_id = run_dir.name
    assert rc == 130 and cap.out == ""
    assert (f"run {run_id} 已经提交，提交命令随后被中断。查进度：gherkai status {run_id} --report-dir {reports}"
            in cap.err.splitlines())
    assert "已停止等待提交结果" not in cap.err
    assert inline_children.only().returncode == 0 and len(advanced) == 1 and tunnel_service.closed


def test_submit_gone_after_the_check_leaves_the_run_advancing_with_a_log_line(tmp_path, monkeypatch, capsys,
                                                                              inline_children, tunnel_service, advanced,
                                                                              interrupt_submit):
    """Ctrl-C 落在后台推进进程查过 submit 之后（装配期间）：run 已经建成，回报写不出去，后台推进进程照常推进，只在 reconcile.log 记一句；
    提交进程以 130 结束，说明与查之前被打断的同一句（它只说可能建立、请先确认）。"""
    marker = "已停止等待提交结果。"
    interrupt = interrupt_submit(marker)
    real_assemble = detached.assemble_local_run

    def assemble_after_submit_left(*a, **k):
        interrupt()
        return real_assemble(*a, **k)

    monkeypatch.setattr(detached, "assemble_local_run", assemble_after_submit_left)
    reports = tmp_path / "reports"
    rc = _main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == ""
    assert _stopped_waiting(reports) in cap.err.splitlines()
    (run_dir,) = _run_dirs(reports)
    log = (run_dir / "reconcile.log").read_text(encoding="utf-8")
    assert f"提交命令在收到提交结果之前已经退出；run {run_dir.name} 已经建立，照常执行。" in log
    assert inline_children.only().returncode == 0 and len(advanced) == 1 and tunnel_service.closed


def _fix_run_id(monkeypatch) -> None:
    monkeypatch.setattr(compose, "new_run_id", lambda at=None: FIXED_RUN_ID)


def _occupy_with_existing_run(reports: Path, monkeypatch) -> None:
    _fix_run_id(monkeypatch)
    (reports / FIXED_RUN_ID).mkdir(parents=True)
    (reports / FIXED_RUN_ID / "run_state.json").write_text("{}", encoding="utf-8")


def _occupy_with_a_file(reports: Path, monkeypatch) -> None:
    _fix_run_id(monkeypatch)
    reports.mkdir(parents=True)
    (reports / FIXED_RUN_ID).write_text("not a directory", encoding="utf-8")


def _break_assembly(reports: Path, monkeypatch) -> None:
    _fix_run_id(monkeypatch)

    def broken(*a, **k):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(detached, "assemble_local_run", broken)


def _break_reconcile_log(reports: Path, monkeypatch) -> None:
    _fix_run_id(monkeypatch)
    real_assemble = detached.assemble_local_run

    def assemble_then_block_the_log(meta, report_dir, **k):
        parts = real_assemble(meta, report_dir, **k)
        (Path(report_dir) / meta.run_id / "reconcile.log").mkdir()  # 日志的位置被一个目录占着：打开失败
        return parts

    monkeypatch.setattr(detached, "assemble_local_run", assemble_then_block_the_log)


@pytest.mark.parametrize("arrange, expected", [
    (_occupy_with_existing_run, f"run {FIXED_RUN_ID} 已经存在，没有重新建立。请重新执行这条命令。"),
    (_occupy_with_a_file, "里写这个 run 的记录失败："),
    (_break_assembly, f"run {FIXED_RUN_ID} 的记录已经写下，但在报告目录 {{reports}} 里准备执行用的文件失败：unable to open database file。"
                      "还没有开始执行，这个 run 在记录里停在 pending。请检查这个目录所在磁盘的剩余空间与读写权限，再用 "
                      f"gherkai settle-runs {FIXED_RUN_ID} --report-dir {{reports}} 把这个 run 记为已结束，然后重新提交。"),
    (_break_reconcile_log, f"run {FIXED_RUN_ID} 的记录已经写下，但在报告目录 {{reports}} 里准备执行用的文件失败："),
], ids=["run-exists", "record-not-written", "assembly-fails", "log-fails"])
def test_local_submit_record_failures_are_reported_with_the_session_closed_first(arrange, expected, tmp_path,
                                                                                 monkeypatch, capsys, inline_children,
                                                                                 tunnel_service, advanced):
    """建 run 的三类失败（run 已存在、记录还没有写下、记录已写下而装配或打开 reconcile.log 失败）：后台推进进程回报那一句，提交进程原样
    打出、退出码 2、没有「已提交」，stdout 为空；后台推进进程写回报时会话已经关闭（先关会话再回报：submit 一退出使用者可能立刻重试）。"""
    reports = tmp_path / "reports"
    arrange(reports, monkeypatch)
    closed_when_reported: list[bool] = []
    real_write_all = handoff.write_all

    def write_and_note(fd, data):
        if threading.current_thread() is not threading.main_thread():  # 后台推进进程那一侧的写：只有回报
            closed_when_reported.append(tunnel_service.closed)
        return real_write_all(fd, data)

    monkeypatch.setattr(handoff, "write_all", write_and_note)
    rc = m.main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert expected.format(reports=reports) in cap.err and "已提交" not in cap.err and "Traceback" not in cap.err
    assert closed_when_reported == [True]
    assert inline_children.only().returncode == 2 and advanced == []
    assert not [n for n in os.listdir(reports) if n.startswith(run_dir.STAGING_PREFIX)]  # 暂存目录不留下
    if arrange is _occupy_with_existing_run:
        assert (reports / FIXED_RUN_ID / "run_state.json").read_text(encoding="utf-8") == "{}"
    if arrange in (_break_assembly, _break_reconcile_log):
        assert LocalRunStore(reports).load_run_state(FIXED_RUN_ID).status == Status.PENDING


# ---- 报告目录的边界检查与生命期锁：run 与本机 submit 同一情形同一句（ADR 0054 决策三、四）----
# 故障只注入在边界上的原语：取文件系统类型（`run_dir.filesystem_type`，测试的替换点）、`fcntl.flock`、`os.mkdir` 之后由另一次打开
# 真的取锁；判断、取锁、换名与收拾都是生产代码在真实文件系统上执行。

_PLATFORM_NAMES = {"darwin": "macOS", "linux": "Linux"}
_FS_LIST = "；".join(f"{_PLATFORM_NAMES[p]} 支持 {'、'.join(types)}" for p, types in run_dir.ALLOWED_FILESYSTEMS.items())
_NOT_KNOWABLE = "在这样的目录上无法确认执行 run 的 gherkai 进程是否还在，没有建立 run。"
_MOVE = f"请把报告目录（--report-dir 选项，或配置文件里的 report-dir）换到本机磁盘上的目录（{_FS_LIST}）"


def _same_inode(fd: int, path: Path) -> bool:
    st, sp = os.fstat(fd), os.stat(path, follow_symlinks=False)
    return (st.st_dev, st.st_ino) == (sp.st_dev, sp.st_ino)


def _at_or_inside(fd: int, reports: Path) -> bool:
    """fd 打开的是报告目录本身或它里面的一层（暂存目录）：按 inode 与目录里真实的条目比。"""
    if not reports.is_dir():
        return False
    return any(_same_inode(fd, p) for p in (reports, *reports.iterdir()))


def _foreign_everywhere(reports, monkeypatch, held):
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs")


def _foreign_existing(reports, monkeypatch, held):
    reports.mkdir()
    _foreign_everywhere(reports, monkeypatch, held)


def _unknowable(reports, monkeypatch, held):
    def unknown(fd):
        raise run_dir.FilesystemUnknown("读不到挂载信息：Permission denied")
    monkeypatch.setattr(run_dir, "filesystem_type", unknown)


def _foreign_once_created(reports, monkeypatch, held):
    """前置检查与建 run 时对报告目录的检查都落在还不存在的报告目录的上级上、放行；报告目录建出之后，它与里面的暂存目录在另一种
    文件系统上（如建出之后被挂上的网络盘）：对暂存目录描述符的那一次检查拒绝。"""
    allowed = run_dir.ALLOWED_FILESYSTEMS[sys.platform][0]
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs" if _at_or_inside(fd, reports) else allowed)


def _flock_unavailable(reports, monkeypatch, held):
    import fcntl

    real_flock = fcntl.flock

    def flock(fd, operation):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))
        return real_flock(fd, operation)
    monkeypatch.setattr(fcntl, "flock", flock)


def _staging_held_by_another_open(reports, monkeypatch, held):
    """每个暂存目录建出之后，另一次打开立刻真的取到排他锁（像清理方那样）：建 run 的一方取锁得到「已被持有」。"""
    import fcntl

    real_mkdir = os.mkdir

    def mkdir(path, *a, **k):
        real_mkdir(path, *a, **k)
        if Path(path).name.startswith(run_dir.STAGING_PREFIX):
            fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
            held.append(fd)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    monkeypatch.setattr(os, "mkdir", mkdir)


def _run_id_taken_by_a_file(reports, monkeypatch, held):
    reports.mkdir()
    (reports / FIXED_RUN_ID).write_text("not a directory", encoding="utf-8")


def _nothing_left(reports, held):
    assert not reports.exists()


def _empty_report_dir(reports, held):
    assert os.listdir(reports) == []  # 报告目录是这次建出的；暂存目录已删去


def _others_staging_untouched(reports, held):
    names = sorted(os.listdir(reports))
    assert len(names) == 3 and all(n.startswith(run_dir.STAGING_PREFIX) for n in names)
    assert all(os.listdir(reports / n) == [] for n in names)
    # 留下的正是另一次打开持有的那三个，锁仍在它们手里
    assert sorted(os.fstat(fd).st_ino for fd in held) == sorted(os.stat(reports / n).st_ino for n in names)
    for n in names:
        fd = os.open(reports / n, os.O_RDONLY | os.O_DIRECTORY)
        try:
            assert run_dir.try_lock(fd).state is run_dir.LockState.HELD
        finally:
            os.close(fd)


def _only_the_file(reports, held):
    assert os.listdir(reports) == [FIXED_RUN_ID] and (reports / FIXED_RUN_ID).is_file()


_REPORT_DIR_SITUATIONS = {
    # id: (布置, 是否在前置检查里被拒, 那一句, 报告目录里留下什么)
    "rejected-before-missing": (
        _foreign_everywhere, True,
        lambda r: f"报告目录 {r} 还不存在，按最近一层已存在的上级 {r.parent} 判断，它所在的文件系统是 nfs，本机后端不支持："
                  f"{_NOT_KNOWABLE}{_MOVE}；多台机器共用运行记录请用云端后端。",
        _nothing_left),
    "rejected-before-existing": (
        _foreign_existing, True,
        lambda r: f"报告目录 {r} 所在的文件系统是 nfs，本机后端不支持：{_NOT_KNOWABLE}{_MOVE}；多台机器共用运行记录请用云端后端。",
        _empty_report_dir),
    "unknown-before": (
        _unknowable, True,
        lambda r: f"无法判断报告目录 {r} 所在的文件系统（读不到挂载信息：Permission denied）：{_NOT_KNOWABLE}{_MOVE}"
                  "；仍然判断不了时可以改用云端后端。",
        _nothing_left),
    "rejected-at-create": (
        _foreign_once_created, False,
        lambda r: f"报告目录 {r} 所在的文件系统是 nfs，本机后端不支持：{_NOT_KNOWABLE}{_MOVE}；多台机器共用运行记录请用云端后端。",
        _empty_report_dir),
    "lock-unavailable": (
        _flock_unavailable, False,
        lambda r: f"在报告目录 {r} 里给这个 run 的目录加锁失败（{os.strerror(errno.ENOLCK)}），没有建立 run：不能加锁的目录上"
                  "无法确认执行 run 的 gherkai 进程是否还在。请检查这个目录所在的文件系统与访问权限后重新执行。",
        _empty_report_dir),
    "staging-contended": (
        _staging_held_by_another_open, False,
        lambda r: f"在报告目录 {r} 里准备这个 run 的目录时，连续 3 次遇到另一个进程同时在处理同一个暂存目录，没有建立 run。"
                  "请稍后重新执行。",
        _others_staging_untouched),
    "run-id-taken-by-a-file": (
        _run_id_taken_by_a_file, False,
        lambda r: f"在报告目录 {r} 里写这个 run 的记录失败：[Errno {errno.ENOTDIR}] {os.strerror(errno.ENOTDIR)}: "
                  f"'{r / FIXED_RUN_ID}'。还没有开始执行；请检查这个目录的读写权限与所在磁盘的剩余空间后重新执行。",
        _only_the_file),
}


@pytest.fixture
def other_opens():
    """用例自己另开的描述符（模拟另一个进程持有暂存目录），用例结束时关闭。"""
    fds: list[int] = []
    yield fds
    for fd in fds:
        os.close(fd)


@pytest.mark.parametrize("command", ["run", "submit"])
@pytest.mark.parametrize("situation", list(_REPORT_DIR_SITUATIONS))
def test_report_dir_and_lock_failures_give_one_sentence_for_run_and_local_submit(
        situation, command, tmp_path, monkeypatch, capsys, inline_children, tunnel_service, advanced, lock_holder,
        other_opens):
    """同一情形，前台 run 与本机 submit 给出逐字相同的一句（两种命令都与同一个期望句相等）、退出码 2，以 run 标识命名的目录没有出现，
    持有者什么都没收到（ADR 0054 决策三、四）。前置检查里被拒的：不补全运行定义、不起隧道，submit 不启动后台推进进程。建 run 时才
    失败的：前台的会话已建成、留给进程退出时关闭；后台推进进程先关会话、再回报。"""
    arrange, before, sentence, leftover = _REPORT_DIR_SITUATIONS[situation]
    reports = tmp_path / "reports"
    _fix_run_id(monkeypatch)
    arrange(reports, monkeypatch, other_opens)
    if before:
        monkeypatch.setattr(m, "_complete_local_definition", _forbid("补全本机运行定义"))
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("建 run 失败时不该开始执行"))
    monkeypatch.setattr(atexit, "register", lambda fn, *a, **k: fn)
    closed_when_reported: list[bool] = []
    real_write_all = handoff.write_all

    def write_and_note(fd, data):
        if threading.current_thread() is not threading.main_thread():  # 后台推进进程那一侧的写：只有回报
            closed_when_reported.append(tunnel_service.closed)
        return real_write_all(fd, data)

    monkeypatch.setattr(handoff, "write_all", write_and_note)
    argv = (_local_submit_argv(tmp_path, "--expose-local", ORIGIN) if command == "submit"
            else ["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--expose-local", ORIGIN])
    rc = m.main(argv)
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == "" and "Traceback" not in cap.err
    assert cap.err.splitlines()[-1] == sentence(reports)
    assert not (reports / FIXED_RUN_ID).is_dir() and lock_holder.fds == []
    leftover(reports, other_opens)
    if before:
        assert tunnel_service.starts == [] and inline_children.children == []
    elif command == "submit":
        assert inline_children.only().returncode == 2 and advanced == [] and closed_when_reported == [True]
    else:
        assert len(tunnel_service.starts) == 1 and not tunnel_service.closed  # 会话由 atexit 在进程退出时关闭


@pytest.mark.parametrize("command", ["run", "submit"])
def test_report_dir_given_as_a_dangling_symlink_is_judged_and_created_at_the_link_target(
        command, tmp_path, monkeypatch, capsys, inline_children, advanced):
    """报告目录经一个悬空的符号链接给出（链接的目标与它的上级都还不存在）：入口把报告目录解析成链接的目标，前台与后台都按目标最近
    一层已存在的上级判断、在目标处建出目录与 run（ADR 0054 决策四）；链接本身不被改动。"""
    target = tmp_path / "elsewhere" / "reports"
    link = tmp_path / "reports-link"
    link.symlink_to(target)

    def schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        results = tuple(JobResult(job=j, status=Status.PASSED) for j in run_meta.jobs)
        for jr in results:
            on_job_complete(jr)
        return Execution(run_meta=run_meta, results=results, stopped_by=None, duration_ms=0.0)

    monkeypatch.setattr(m, "schedule", schedule)
    extra = ["--region", "us-east-1"] if command == "submit" else []
    rc = m.main([command, str(_write_feature(tmp_path)), "--report-dir", str(link), *extra])
    inline_children.settle()
    assert rc == 0, capsys.readouterr().err
    (run,) = _run_dirs(target)
    assert {"run_meta.json", "run_state.json"} <= {p.name for p in run.iterdir()}
    assert link.is_symlink() and Path(os.readlink(link)) == target
    assert LocalRunStore(target).load_run_state(run.name) is not None


@pytest.mark.parametrize("command", ["run", "submit"])
def test_a_dangling_symlink_to_an_unsupported_filesystem_is_rejected_before_anything_is_prepared(
        command, tmp_path, monkeypatch, capsys, inline_children, tunnel_service, advanced):
    """报告目录是一个悬空的符号链接，目标在一个清单之外的文件系统上（目标的上级已存在、目标还不存在）：前置检查按解析之后的路径
    判断，取目标最近一层已存在的上级，run 与本机 submit 在这里就给出那一句、退出码 2；补全运行定义的那一步没有被调用，没有起隧道，
    submit 不启动后台推进进程（ADR 0054 决策四）。类型按目录的 inode 给出：只有目标的上级是 nfs，链接所在的目录在清单里。"""
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    target = foreign / "reports"
    link = tmp_path / "reports-link"
    link.symlink_to(target)
    foreign_id = (os.stat(foreign).st_dev, os.stat(foreign).st_ino)
    allowed = run_dir.ALLOWED_FILESYSTEMS[sys.platform][0]

    def by_directory(fd):
        st = os.fstat(fd)
        return "nfs" if (st.st_dev, st.st_ino) == foreign_id else allowed

    monkeypatch.setattr(run_dir, "filesystem_type", by_directory)
    monkeypatch.setattr(m, "_complete_local_definition", lambda *a, **k: pytest.fail("前置检查被拒时不该补全运行定义"))
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("前置检查被拒时不该开始执行"))
    extra = ["--region", "us-east-1"] if command == "submit" else []
    rc = m.main([command, str(_write_feature(tmp_path)), "--report-dir", str(link), *extra, "--expose-local", ORIGIN])
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == "" and "Traceback" not in cap.err
    assert cap.err.splitlines()[-1] == (
        f"报告目录 {target} 还不存在，按最近一层已存在的上级 {foreign} 判断，它所在的文件系统是 nfs，本机后端不支持："
        f"{_NOT_KNOWABLE}{_MOVE}；多台机器共用运行记录请用云端后端。")
    assert tunnel_service.starts == [] and inline_children.children == []
    assert not target.exists() and link.is_symlink()


@pytest.mark.parametrize("command", ["run-no-report", "submit-cloud", "plan"])
def test_commands_that_build_no_local_run_skip_the_report_dir_check(command, tmp_path, monkeypatch, capsys,
                                                                    inline_children):
    """不建本机 run 的命令不做报告目录的边界检查（ADR 0054 决策四）：文件系统类型一律取成清单之外的 nfs，`run --no-report` 照常开始
    执行、以判定的退出码结束；云端 `submit` 越过这项检查，照常写下 run；`plan` 以退出码 0 结束。云端 submit 的报告目录取缺省的
    相对路径，当前目录换到用例的临时目录。"""
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs")
    monkeypatch.chdir(tmp_path)
    feature = str(_write_feature(tmp_path))
    if command == "run-no-report":
        box: dict = {}
        monkeypatch.setattr(m, "schedule", _fake_schedule(box))
        assert m.main(["run", feature, "--no-report", "--report-dir", str(tmp_path / "reports")]) == 0
        assert "run_meta" in box
    elif command == "submit-cloud":
        record: list = []
        _patch_cloud_handles(monkeypatch, record)
        assert m.main(_cloud_submit_argv(tmp_path)) == 0
        assert ("ddb", "put_item") in record
    else:
        assert m.main(["plan", feature]) == 0
    assert "本机后端不支持" not in capsys.readouterr().err


def _lock_seen_while_advancing(holder, run: Path) -> tuple[int, bool, run_dir.LockState]:
    """推进中看到的生命期锁：持有者收下了几个描述符、只有一个时它是不是 run 目录，另开一次 run 目录取锁得到什么。"""
    fds = list(holder.fds)
    another = os.open(run, os.O_RDONLY | os.O_DIRECTORY)
    try:
        state = run_dir.try_lock(another).state
    finally:
        os.close(another)
    return len(fds), len(fds) == 1 and _same_inode(fds[0], run), state


def test_foreground_run_holds_the_lifetime_lock_while_advancing(tmp_path, monkeypatch, capsys, lock_holder):
    """前台 run 推进期间持有生命期锁（ADR 0054 决策三）：调度循环执行的时候，本进程的持有者恰好收下一个描述符，它与 run 目录是同一个
    inode，另开一次对 run 目录取锁得到「已被持有」。"""
    reports = tmp_path / "reports"
    seen: list = []

    def schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        seen.append(_lock_seen_while_advancing(lock_holder, reports / run_meta.run_id))
        results = tuple(JobResult(job=j, status=Status.PASSED) for j in run_meta.jobs)
        for jr in results:
            on_job_complete(jr)
        return Execution(run_meta=run_meta, results=results, stopped_by=None, duration_ms=0.0)

    monkeypatch.setattr(m, "schedule", schedule)
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0, capsys.readouterr().err
    assert seen == [(1, True, run_dir.LockState.HELD)]


def test_local_advancer_holds_the_lifetime_lock_while_advancing(tmp_path, monkeypatch, capsys, inline_children,
                                                                lock_holder):
    """本机后台推进进程推进期间持有生命期锁（ADR 0054 决策三）：推进执行的时候，持有者恰好收下一个描述符，它与 run 目录是同一个
    inode，另开一次对 run 目录取锁得到「已被持有」。后台推进进程的主体在线程里执行（`_inline_children`），持有者是同一个。"""
    reports = tmp_path / "reports"
    seen: list = []
    monkeypatch.setattr(detached, "advance_local_run",
                        lambda advancer, meta, **kw: seen.append(_lock_seen_while_advancing(lock_holder,
                                                                                            reports / meta.run_id)))
    rc = m.main(_local_submit_argv(tmp_path))
    inline_children.settle()
    assert rc == 0, capsys.readouterr().err
    assert inline_children.only().returncode == 0
    assert seen == [(1, True, run_dir.LockState.HELD)]


def test_local_submit_store_failure_while_advancing_is_logged_and_the_advancer_exits_1(tmp_path, monkeypatch, capsys,
                                                                                      inline_children, tunnel_service):
    """推进中读写本机运行记录失败：提交进程早已以 0 结束（已提交）；后台推进进程在 reconcile.log 记一句、以 1 退出，关闭会话。"""
    def failing_advance(advancer, meta, **kw):
        raise OSError("No space left on device")

    monkeypatch.setattr(detached, "advance_local_run", failing_advance)
    reports = tmp_path / "reports"
    rc = m.main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    assert rc == 0 and "已提交（本机后台推进中）" in capsys.readouterr().err
    (run_dir,) = _run_dirs(reports)
    log = (run_dir / "reconcile.log").read_text(encoding="utf-8")
    assert f"run {run_dir.name} 读写本机的运行记录失败，后台推进已停止：No space left on device。" in log
    assert inline_children.only().returncode == 1 and tunnel_service.closed


def test_local_submit_cannot_start_the_advancer(tmp_path, capsys, inline_children, tunnel_service):
    """起不来后台推进进程：一句说明、退出码 2，没有提交、没有起隧道。"""
    inline_children.popen_error = OSError("Cannot allocate memory")
    rc = m.main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert "无法启动后台推进进程：Cannot allocate memory。没有提交。" in cap.err
    assert tunnel_service.starts == [] and _run_dirs(tmp_path / "reports") == []


def test_advancer_uses_the_values_handed_over_and_reads_no_config_file(tmp_path, monkeypatch, capsys, inline_children,
                                                                       advanced):
    """后台推进进程不读配置文件（ADR 0053 决策 1）：配置文件给的 steps 目录与并发上限由 submit 解析后经标准输入交来；后台推进进程在另一个
    工作目录（那里有别的配置文件与 steps 目录）里得到的仍是提交时的值。"""
    project = tmp_path / "project"
    (project / "mysteps").mkdir(parents=True)
    (project / "gherkai.toml").write_text("[common]\nsteps-dir = 'mysteps'\nmax-concurrency = 3\n", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "steps").mkdir(parents=True)
    (elsewhere / "gherkai.toml").write_text("[common]\nmax-concurrency = 7\n", encoding="utf-8")
    monkeypatch.chdir(project)
    inline_children.before_child = lambda child: os.chdir(elsewhere)
    reports = tmp_path / "reports"
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--region", "us-east-1"])
    inline_children.settle()
    assert rc == 0, capsys.readouterr().err
    (run_dir,) = _run_dirs(reports)
    meta = LocalRunStore(reports).load_run_meta(run_dir.name)
    assert meta.steps_dir == str((project / "mysteps").resolve()) and meta.max_concurrency == 3
    assert advanced[0][1].steps_dir == meta.steps_dir


# ---- 进程入口（真的启动子进程或读 fd 0，不起隧道）----

@pytest.mark.parametrize("entry", ["_reconcile", "_tunnel_watch"])
def test_background_entry_exits_2_silently_when_submit_left_before_handing_the_input(entry):
    """后台进程读输入时读到文件结束（submit 在交完输入之前已不在）：不输出、不回报，以退出码 2 结束。真的以 `-P` 启动子进程。"""
    report_r, report_w = os.pipe()
    try:
        proc = subprocess.run([sys.executable, "-P", "-m", "gherkai_cli", entry, "--report-fd", str(report_w)],
                              stdin=subprocess.DEVNULL, capture_output=True, pass_fds=(report_w,), timeout=120)
    finally:
        os.close(report_w)
    try:
        reported = os.read(report_r, 4096)
    finally:
        os.close(report_r)
    assert (proc.returncode, proc.stdout, proc.stderr, reported) == (2, b"", b"", b"")


@pytest.mark.parametrize("inherited", ["ignored", "blocked"])
@pytest.mark.parametrize("signum", [signal.SIGHUP, signal.SIGTERM, signal.SIGINT], ids=["SIGHUP", "SIGTERM", "SIGINT"])
@pytest.mark.parametrize("entry", ["_reconcile", "_tunnel_watch"])
def test_background_entry_is_ended_by_the_signal_even_when_the_parent_ignores_or_blocks_it(entry, signum, inherited):
    """启动方把这个信号设成了忽略（如经 nohup 启动的 submit 之于 SIGHUP），或屏蔽着它，后台进程继承了这份处置或屏蔽字：入口进门即
    设成缺省处置并解除屏蔽，对它发这个信号即结束它。SIGINT 同样按缺省处置结束进程，不在解释器里变成中断：标准错误为空，没有回溯、
    没有 KeyboardInterrupt。真实进程、真实信号：父进程先设忽略或屏蔽再启动，标准输入保持打开、不交输入（后台进程停在读输入，不起
    隧道）；入口设好处置之前到达的信号会被忽略或挂起，所以每 0.2 秒发一次，直到它退出或到 10 秒。"""
    report_r, report_w = os.pipe()
    stdin_r, stdin_w = os.pipe()
    env = {k: v for k, v in os.environ.items() if k != "NGROK_AUTHTOKEN"}
    if inherited == "ignored":
        previous = signal.signal(signum, signal.SIG_IGN)
        restore = lambda: signal.signal(signum, previous)  # noqa: E731
    else:
        before = signal.pthread_sigmask(signal.SIG_BLOCK, {signum})
        restore = lambda: signal.pthread_sigmask(signal.SIG_SETMASK, before)  # noqa: E731
    try:
        proc = subprocess.Popen([sys.executable, "-P", "-m", "gherkai_cli", entry, "--report-fd", str(report_w)],
                                stdin=stdin_r, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(report_w,),
                                start_new_session=True, env=env)
    finally:
        restore()
        os.close(report_w)
        os.close(stdin_r)
    try:
        deadline = time.monotonic() + 10
        while proc.poll() is None and time.monotonic() < deadline:
            proc.send_signal(signum)
            try:
                proc.wait(0.2)
            except subprocess.TimeoutExpired:
                pass
    finally:
        os.close(stdin_w)  # 没有被信号结束的，读到文件结束即以 2 退出
        out, err = proc.communicate(timeout=60)
        os.close(report_r)
    assert (proc.returncode, out, err) == (-signum, b"", b"")


def test_building_the_parser_does_not_import_the_tunnel_sdk():
    """隧道组件只在给了 --expose-local 时导入（ADR 0037 决策 2c）：导入命令行入口并建一次解析器之后 SDK 不在已导入的模块里。
    同进程里别的用例可能已导入它，所以在子进程里查。"""
    code = ("import sys, gherkai_runtime.tunnel, gherkai_cli.__main__ as m; m._build_parser(); "
            "print('ngrok' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=True)
    assert out.stdout.strip() == "False"


class _Fd0:
    """把一条真实管道的读端接到本进程的 fd 0（测试结束时恢复）；`write` / `close_writer` 操作写端，关闭只做一次。"""

    def __init__(self) -> None:
        r, self._w = os.pipe()
        self._saved = os.dup(0)
        os.dup2(r, 0)
        os.close(r)

    def write(self, data: bytes) -> None:
        assert handoff.write_all(self._w, data)

    def close_writer(self) -> None:
        if self._w is not None:
            w, self._w = self._w, None
            os.close(w)

    def restore(self) -> None:
        self.close_writer()
        os.dup2(self._saved, 0)
        os.close(self._saved)


@pytest.fixture
def fd0():
    pipe = _Fd0()
    try:
        yield pipe
    finally:
        pipe.restore()


def test_tunnel_watch_entry_holds_the_tunnel_until_stdin_closes_and_installs_no_signal_handler(fd0, tunnel_service,
                                                                                               monkeypatch):
    """`_tunnel_watch` 入口：回报描述符设为不可继承，从 fd 0 读输入、交给守护进程的主体（记日志的一句经 `_tunnel_watch_note`）；主体
    回报公网地址与预热地址，submit 没有交出 run 标识就关闭了标准输入时关闭会话、以 0 返回。入口不装信号处理器：SIGTERM、SIGHUP、
    SIGINT 都是缺省处置（ADR 0035 决策 3）。"""
    report_r, report_w = os.pipe()
    os.set_inheritable(report_w, True)
    fd0.write(handoff.encode_watch_input(handoff.WatchInput(
        local_origin=ORIGIN, tunnel_provider="ngrok", closes_at=instant_to_iso(FAR_FUTURE), runs_table="T",
        region="us-east-1", profile=None)))
    reports: list = []

    def read_report_then_close_stdin() -> None:
        reports.append(handoff.read_line(report_r))
        fd0.close_writer()

    reader = threading.Thread(target=read_report_then_close_stdin, daemon=True)
    reader.start()
    from gherkai_runtime import tunnel_host
    notes_given: list = []
    real_hold = tunnel_host.hold_tunnel_for_cloud_run

    def spy_hold(inp, **kw):
        notes_given.append(kw["note"])
        return real_hold(inp, **kw)

    monkeypatch.setattr(tunnel_host, "hold_tunnel_for_cloud_run", spy_hold)
    try:
        rc = m.main(["_tunnel_watch", "--report-fd", str(report_w)])
        reader.join(5)
        assert not os.get_inheritable(report_w)
    finally:
        os.close(report_w)
        os.close(report_r)
    assert rc == 0
    report = handoff.decode_watch_report(reports[0])
    assert (report.public_url, report.warmup_url, report.exit_code) == (PUBLIC, WARMUP, 0)
    assert tunnel_service.closed
    assert tunnel_service.starts[0]["closes_at"] == FAR_FUTURE
    assert notes_given == [m._tunnel_watch_note]
    assert [signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)] == [signal.SIG_DFL] * 3


def test_tunnel_watch_note_writes_one_prefixed_line_to_stdout(capsys):
    """守护进程记日志的一句：以 `tunnel-watch: ` 开头、一句一行，写到标准输出（收到 run 的标识之后它已是守护进程的日志），标准错误
    不写。线程替身复用同一个函数，所以这里钉住的就是用例里守护进程日志的形态。"""
    m._tunnel_watch_note("隧道已建立，等待 run r1 结束")
    m._tunnel_watch_note("run r1 已结束（passed），隧道已关闭")
    cap = capsys.readouterr()
    assert cap.out == "tunnel-watch: 隧道已建立，等待 run r1 结束\ntunnel-watch: run r1 已结束（passed），隧道已关闭\n"
    assert cap.err == ""


def test_reconcile_entry_reads_its_input_from_stdin_and_reports_a_tunnel_failure(tmp_path, fd0, tunnel_service):
    """`_reconcile` 入口：回报描述符设为不可继承，从 fd 0 读输入、交给后台推进进程的主体；起隧道失败时回报那一句与退出码 2，不建 run。"""
    tunnel_service.start_error = gtunnel.TunnelError("隧道没有建成：x。")
    job = Job(scope_id="s", scope_name="s", engine="novaact", timeout_s=300.0,
              scenarios=(Scenario(id="t.feature:2", name="s", steps=(Step(0, "When", f"打开 {ORIGIN}/login"),)),))
    reports = tmp_path / "reports"
    fd0.write(handoff.encode_advancer_input(handoff.AdvancerInput(
        jobs=(job,), steps_dir=None, max_concurrency=1, per_job_tail_s=310.0, expose_local=ORIGIN,
        tunnel_provider="ngrok", region="us-east-1", profile=None, report_dir=str(reports))))
    report_r, report_w = os.pipe()
    os.set_inheritable(report_w, True)
    try:
        rc = m.main(["_reconcile", "--report-fd", str(report_w)])
        assert not os.get_inheritable(report_w)   # 进门即设为不可继承：之后起的 worker 拿不到回报写端
    finally:
        os.close(report_w)
    try:
        report = handoff.decode_advancer_report(handoff.read_line(report_r))
    finally:
        os.close(report_r)
    assert rc == 2
    assert (report.run_id, report.exit_code, report.message) == (None, 2, "隧道没有建成：x。")
    assert not reports.exists()


# ---- 云端 submit 与隧道守护进程（ADR 0035 决策 3「云端 `submit`」）----

@pytest.mark.parametrize("gate", ["skew", "preflight", "variant", "definition"])
def test_cloud_gates_run_before_the_daemon_is_started(gate, tmp_path, monkeypatch, capsys, inline_children,
                                                      tunnel_service):
    """云端的各道闸（版本 skew、资源 preflight、worker variant、补全运行定义）任一拦下：退出码 2，守护进程没有启动、隧道没有起。"""
    record: list = []
    kwargs = {"skew": ("block", "后端版本更旧")} if gate == "skew" else {}
    if gate == "preflight":
        kwargs["preflight_err"] = "资源缺失：ECS cluster gherkai-cluster 不存在"
    if gate == "variant":
        kwargs["variant_err"] = compose.WorkerVariantError("这个 variant 没有推")
    _patch_cloud_handles(monkeypatch, record, **kwargs)
    if gate == "definition":
        monkeypatch.setattr(m, "_complete_cloud_definition", lambda *a, **k: 2)
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    assert rc == 2
    assert inline_children.children == [] and tunnel_service.starts == []
    assert ("ddb", "put_item") not in record


@pytest.mark.parametrize("expose, expected", [(True, True), (False, False)], ids=["tunneled", "plain"])
def test_cloud_version_gate_requires_a_stamp_when_expose_local_is_given(expose, expected, tmp_path, monkeypatch,
                                                                       inline_children, tunnel_service):
    """缺戳例外按有没有给 --expose-local 判断（版本闸早于起隧道，这时还没有预热地址可看，ADR 0037 决策 7）：桌面目标、不带隧道时不要求。"""
    seen: list = []
    _patch_cloud_handles(monkeypatch, [])
    monkeypatch.setattr(m.compose, "check_version_skew", lambda *a, **kw: seen.append(kw) or ("ok", ""))
    extra = ["--expose-local", ORIGIN] if expose else []
    assert m.main(_cloud_submit_argv(tmp_path, *extra)) == 0
    inline_children.settle()
    assert [kw["requires_stamp"] for kw in seen] == [expected]


def test_cloud_submit_with_tunnel_maps_the_definition_and_hands_the_run_id_to_the_daemon(tmp_path, monkeypatch, capsys,
                                                                                         inline_children, tunnel_service):
    """带隧道建成的一次：以 `-P`、新会话启动守护进程，它起隧道（到点时刻是运行期限加 300 秒）并回报；提交记录里的 job 已映射、带请求头
    与预热地址；交出 run 标识之后守护进程照它轮询，读到终态即关闭会话。stdout 只有 run 标识，stderr 有公网地址那一行、守护进程那一句
    （带日志位置）与查进度的命令。"""
    record: list = []
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)
    spawned: dict = {}
    inline_children.on_spawn = lambda argv, kw: spawned.update(argv=argv, kw=kw)
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    meta = _definition(made["ddb_tables"][0])
    run_id = meta["run_id"]
    assert rc == 0 and cap.out == f"{run_id}\n"
    argv, kw = spawned["argv"], spawned["kw"]
    assert argv[:7] == [sys.executable, "-P", "-m", "gherkai_cli", "_tunnel_watch", "--report-fd", argv[6]]
    assert kw["pass_fds"] == (int(argv[6]),) and kw["start_new_session"] is True
    assert kw["stdout"] == 2 and kw["stderr"] == 2
    assert meta["session_warmup_url"] == WARMUP
    assert dict(meta["extra_http_headers"]) == {"ngrok-skip-browser-warning": "1"}
    assert f"{PUBLIC}/login" in meta["jobs"][0]["scenarios"][0]["steps"][0]["text"]
    assert tunnel_service.starts[0]["closes_at"] == run_deadline.overdue_at(instant_from_iso(meta["deadline_at"]))
    watch_log = tmp_path / f"gherkai-tunnel-watch-{run_id}.log"
    assert ESTABLISHED in cap.err.splitlines()
    assert (f"隧道由本机的后台进程持有（日志 {watch_log}），它在 run 结束时关闭隧道。注意：本机需保持开机联网直到 run 终态——"
            "关机或断网会断开隧道，之后要访问被测应用的 job 将以导航失败告终。") in cap.err
    assert "已提交到云端（提交记录已落库，云端已接管推进）。查进度：gherkai status " in cap.err and "可关机" not in cap.err
    child = inline_children.only()
    assert child.returncode == 0 and tunnel_service.closed
    assert child.notes[0].startswith(f"隧道已建立，等待 run {run_id} 结束（最晚到 ")
    assert child.notes[-1] == f"run {run_id} 已结束（passed），隧道已关闭"
    assert f"tunnel-watch: 隧道已建立，等待 run {run_id} 结束" in watch_log.read_text(encoding="utf-8")


def test_cloud_submit_without_tunnel_starts_no_daemon(tmp_path, monkeypatch, capsys, inline_children, tunnel_service):
    """不给 --expose-local：不启动守护进程、不碰隧道服务，提交记录里没有预热地址，提示可关机。"""
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, [])
    rc = m.main(_cloud_submit_argv(tmp_path))
    cap = capsys.readouterr()
    meta = _definition(made["ddb_tables"][0])
    assert rc == 0 and cap.out == f"{meta['run_id']}\n"
    assert "已提交到云端（提交记录已落库，云端已接管推进，可关机）" in cap.err
    assert inline_children.children == [] and tunnel_service.made == 0 and meta["session_warmup_url"] is None


def test_cloud_submit_builds_no_run_when_the_daemon_is_gone_before_the_check(tmp_path, monkeypatch, capsys,
                                                                              inline_children, tunnel_service):
    """守护进程回报之后、submit 建 run 之前退出（这里是它的墙钟已过到点时刻）：submit 对回报管道的读端读到文件结束，不建 run、退出码 2。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    inline_children.watch_kwargs["clock"] = lambda: FAR_FUTURE
    real_gone = handoff.WatchChannel.daemon_gone

    def gone_after_the_daemon_exits(self):
        inline_children.only().wait()
        return real_gone(self)

    monkeypatch.setattr(handoff.WatchChannel, "daemon_gone", gone_after_the_daemon_exits)
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert "持有隧道的本机后台进程退出了，没有提交；它退出之前如果有输出，原因在上面。处理好原因之后请重新执行。" in cap.err
    assert ("ddb", "put_item") not in record
    assert inline_children.only().returncode == 0 and tunnel_service.closed


def test_cloud_submit_releases_the_daemon_before_reporting_a_failed_create(tmp_path, monkeypatch, capsys,
                                                                           inline_children, tunnel_service):
    """建 run 撞 AWS 错：退出码 2、一句诊断。submit 先关闭守护进程的标准输入、等它退出再打出诊断：这句打出时守护进程的主体已经关闭
    会话、返回。替身不另加等待，这一点由 submit 自己的等待保证。"""
    from botocore.exceptions import ClientError

    _patch_cloud_handles(monkeypatch, [])
    real_make = m.compose._make_ddb_table

    def make_failing(table, *, region, profile):
        t = real_make(table, region=region, profile=profile)

        def boom_put(**kw):
            raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "PutItem")

        t.put_item = boom_put
        return t

    monkeypatch.setattr(m.compose, "_make_ddb_table", make_failing)
    daemon_at_report: list[tuple] = []
    real_progress = m._progress

    def progress(*a, **k):
        if a and "云端不可达" in str(a[0]):
            daemon_at_report.append((tunnel_service.closed, inline_children.only().returncode))
        real_progress(*a, **k)

    monkeypatch.setattr(m, "_progress", progress)
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == "" and "已提交" not in cap.err
    assert daemon_at_report == [(True, 0)]   # 会话已关闭，主体已经返回
    assert inline_children.only().returncode == 0 and tunnel_service.closed
    assert inline_children.only().notes == []  # 守护进程没有收到 run 的标识


def test_cloud_submit_stops_waiting_for_the_daemon_after_the_close_limit(tmp_path, monkeypatch, capsys,
                                                                          inline_children, tunnel_service):
    """建 run 失败、守护进程关闭会话一直没有完成（不退出）：submit 等到关闭会话的时限加 1 秒就不再等，照样报错、退出码 2。用例把
    关闭会话的时限调成 0，等待即为 1 秒。"""
    from botocore.exceptions import ClientError

    _patch_cloud_handles(monkeypatch, [])
    monkeypatch.setattr(gtunnel, "CLOSE_TIMEOUT_S", 0.0)
    real_make = m.compose._make_ddb_table

    def make_failing(table, *, region, profile):
        t = real_make(table, region=region, profile=profile)

        def boom_put(**kw):
            raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "PutItem")

        t.put_item = boom_put
        return t

    monkeypatch.setattr(m.compose, "_make_ddb_table", make_failing)
    unblock = threading.Event()
    real_close = tunnel_service._close

    def stuck_close():
        unblock.wait(10)
        real_close()

    monkeypatch.setattr(tunnel_service, "_close", stuck_close)
    seen: dict = {}
    real_release = handoff.WatchChannel.release

    def timed_release(self, *, wait_s=0.0):
        seen.setdefault("release", (time.monotonic(), wait_s))
        return real_release(self, wait_s=wait_s)

    monkeypatch.setattr(handoff.WatchChannel, "release", timed_release)
    real_progress = m._progress

    def progress(*a, **k):
        if a and "云端不可达" in str(a[0]):
            seen["reported"] = (time.monotonic(), tunnel_service.closed)
        real_progress(*a, **k)

    monkeypatch.setattr(m, "_progress", progress)
    try:
        rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    finally:
        unblock.set()
    inline_children.settle()
    assert rc == 2 and capsys.readouterr().out == ""
    (released_at, wait_s), (reported_at, closed_when_reported) = seen["release"], seen["reported"]
    assert wait_s == 1.0 and not closed_when_reported
    assert 1.0 <= reported_at - released_at < 3.0
    assert inline_children.only().returncode == 0 and tunnel_service.closed


def test_cloud_submit_still_succeeds_when_the_daemon_is_gone_after_the_check(tmp_path, monkeypatch, capsys,
                                                                             inline_children, tunnel_service):
    """查过之后守护进程才没了：run 已经建成、由云端推进，交出 run 标识写不进去；照常输出 run 标识、退出码 0，另说明隧道已不再可用。"""
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, [])
    gate = threading.Event()
    real_now = compose.now
    inline_children.watch_kwargs["clock"] = lambda: FAR_FUTURE if gate.is_set() else real_now()
    real_hand_over = handoff.WatchChannel.hand_over

    def hand_over_after_the_daemon_exits(self, run_id):
        gate.set()
        inline_children.only().wait()
        return real_hand_over(self, run_id)

    monkeypatch.setattr(handoff.WatchChannel, "hand_over", hand_over_after_the_daemon_exits)
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    run_id = _definition(made["ddb_tables"][0])["run_id"]
    assert rc == 0 and cap.out == f"{run_id}\n"
    assert (f"run {run_id} 已经提交，但持有隧道的本机后台进程已经退出（它退出之前如果有输出，原因在上面），隧道已不再可用："
            "这个 run 里要访问被测应用的 job 会失败。处理好原因之后请重新提交。") in cap.err
    assert ESTABLISHED not in cap.err.splitlines()
    assert "已提交到云端（提交记录已落库，云端已接管推进）。" in cap.err
    assert tunnel_service.closed


def test_cloud_submit_checks_the_daemon_right_before_creating_the_run(tmp_path, monkeypatch, capsys, inline_children,
                                                                      tunnel_service):
    """建 run 之前查一次守护进程还在不在：查在装配存储之后、紧挨建 run，查过之后到建 run 之间不再装配别的东西。"""
    _patch_cloud_handles(monkeypatch, [])
    order: list[str] = []
    real_build = m.compose.build_cloud_stores

    def build(**kw):
        order.append("build_cloud_stores")
        run_store, result_store, report_store = real_build(**kw)
        real_create = run_store.create_run

        def create(meta, initial_state):
            order.append("create_run")
            return real_create(meta, initial_state)

        run_store.create_run = create
        return run_store, result_store, report_store

    monkeypatch.setattr(m.compose, "build_cloud_stores", build)
    real_gone = handoff.WatchChannel.daemon_gone

    def gone(self):
        order.append("daemon_gone")
        return real_gone(self)

    monkeypatch.setattr(handoff.WatchChannel, "daemon_gone", gone)
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    assert rc == 0, capsys.readouterr().err
    assert order == ["build_cloud_stores", "daemon_gone", "create_run"]


def test_ctrl_c_while_waiting_for_the_daemon_builds_no_run(tmp_path, monkeypatch, capsys, inline_children,
                                                           tunnel_service, interrupt_submit):
    """等守护进程回报时 Ctrl-C：「已停止提交，没有建立 run。」、130；守护进程回报写不出去，关闭会话、退出。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    tunnel_service.on_start = interrupt_submit("已停止提交，没有建立 run。")
    rc = _main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == "" and "已停止提交，没有建立 run。" in cap.err
    assert ("ddb", "put_item") not in record
    assert inline_children.only().returncode == 0 and tunnel_service.closed


class _InterruptedCreate:
    """create_run 里被 Ctrl-C 打断的假 RunStore。"""

    def create_run(self, meta, state):
        raise KeyboardInterrupt


@pytest.mark.parametrize("expose", [True, False], ids=["tunneled", "plain"])
def test_ctrl_c_inside_create_run_says_the_run_may_exist(expose, tmp_path, monkeypatch, capsys, inline_children,
                                                         tunnel_service):
    """中断落在建 run 里面（给不给 --expose-local 都接）：说明 run 可能已经写入云端、给出确认用的命令，130，stdout 不输出；带隧道时
    另说明隧道已不再可用，守护进程读到标准输入关闭即关闭会话。"""
    _patch_cloud_handles(monkeypatch, [])
    _fix_run_id(monkeypatch)
    monkeypatch.setattr(m.compose, "build_cloud_stores", lambda **kw: (_InterruptedCreate(), object(), object()))
    extra = ["--expose-local", ORIGIN] if expose else []
    rc = _main(_cloud_submit_argv(tmp_path, *extra))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == ""
    assert (f"提交被中断。run {FIXED_RUN_ID} 可能已经写入云端，可以用 gherkai list-runs --backend cloud --prefix "
            in cap.err)
    tunnel_clause = "隧道已不再可用，这个 run 如果已经写入，其中要访问被测应用的 job 会失败。"
    assert (tunnel_clause in cap.err) is expose
    if expose:
        assert inline_children.only().returncode == 0 and tunnel_service.closed


def test_ctrl_c_after_create_run_before_handing_over_says_the_tunnel_is_unusable(tmp_path, monkeypatch, capsys,
                                                                                  inline_children, tunnel_service):
    """建 run 已经返回、交出 run 标识之前 Ctrl-C：说明 run 已经提交、隧道已不再可用，给出查进度的命令，130、stdout 不输出；
    守护进程没有收到标识，读到标准输入关闭即关闭会话。"""
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, [])

    def interrupted_hand_over(self, run_id):
        raise KeyboardInterrupt

    monkeypatch.setattr(handoff.WatchChannel, "hand_over", interrupted_hand_over)
    rc = _main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    run_id = _definition(made["ddb_tables"][0])["run_id"]
    assert rc == 130 and cap.out == ""
    assert (f"run {run_id} 已经提交，提交命令随后被中断。隧道已不再可用，这个 run 里要访问被测应用的 job 会失败。"
            f"查进度：gherkai status {run_id} --backend cloud --prefix ") in cap.err
    child = inline_children.only()
    assert child.returncode == 0 and child.notes == [] and tunnel_service.closed


def test_ctrl_c_between_handing_over_and_noting_it_does_not_claim_the_tunnel_is_unusable(tmp_path, monkeypatch, capsys,
                                                                                          inline_children,
                                                                                          tunnel_service):
    """SIGINT 恰在 run 标识写进守护进程之后、submit 记下「交成了」之前到达：推迟到记下之后才按中断处理，所以说明里没有「隧道已不再
    可用」——守护进程确实收到了标识，照常持有隧道到 run 结束。"""
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, [])
    real_hand_over = handoff.WatchChannel.hand_over

    def hand_over_then_sigint(self, run_id):
        delivered = real_hand_over(self, run_id)
        signal.raise_signal(signal.SIGINT)
        return delivered

    monkeypatch.setattr(handoff.WatchChannel, "hand_over", hand_over_then_sigint)
    rc = _main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    run_id = _definition(made["ddb_tables"][0])["run_id"]
    assert rc == 130 and cap.out == ""
    assert f"run {run_id} 已经提交，提交命令随后被中断。查进度：gherkai status {run_id} --backend cloud --prefix " in cap.err
    assert "隧道已不再可用" not in cap.err
    child = inline_children.only()
    assert child.notes[0].startswith(f"隧道已建立，等待 run {run_id} 结束")
    assert child.returncode == 0 and tunnel_service.closed
    assert signal.getsignal(signal.SIGINT) is signal.default_int_handler  # 推迟期间换上的处置已恢复


def test_ctrl_c_while_printing_the_result_of_a_plain_cloud_submit(tmp_path, monkeypatch, capsys, inline_children):
    """不带隧道、建 run 之后输出结果时 Ctrl-C：说明 run 已经提交、给出查进度的命令，不提隧道，130。"""
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, [])
    real_progress = m._progress

    def progress(*a, **k):
        if a and str(a[0]).startswith("已提交到云端"):
            raise KeyboardInterrupt
        real_progress(*a, **k)

    monkeypatch.setattr(m, "_progress", progress)
    rc = _main(_cloud_submit_argv(tmp_path))
    cap = capsys.readouterr()
    run_id = _definition(made["ddb_tables"][0])["run_id"]
    assert rc == 130 and cap.out == ""
    assert f"run {run_id} 已经提交，提交命令随后被中断。查进度：gherkai status {run_id} --backend cloud --prefix " in cap.err
    assert "隧道" not in cap.err


# ---- 真实进程、真实内核上的边界检查（ADR 0054 决策四）----

# 两个平台上不用挂载就有的、不在清单里的文件系统：macOS 的 /dev（devfs），Linux 的 /proc（proc）
_PSEUDO_FILESYSTEM = {"darwin": ("/dev", "devfs"), "linux": ("/proc", "proc")}
# 假 worker：经 GHERKAI_WORKER_<引擎>_CMD 起，能力自述原样给出参数里那份文件的内容，匹配查询逐条答作走 AI，别的入口以 3 退出
_FAKE_WORKER = """\
import json, sys
caps, flag = sys.argv[1], sys.argv[2]
if flag == "--capabilities":
    print(open(caps, encoding="utf-8").read())
elif flag == "--match-steps":
    print(json.dumps([None for _ in json.load(sys.stdin)]))
else:
    sys.exit(3)
"""


def _isolated_child_env(tmp_path: Path) -> dict[str, str]:
    """起真实子进程执行 gherkai 时的环境：两个引擎的 worker 都换成 `_FAKE_WORKER`（能力自述取 `_fake_worker` 里的值），不读配置文件
    与 steps 目录的环境变量，不带隧道令牌；AWS 用假凭证、端点指向本机一个不监听的端口，子进程碰到 AWS 也只会在本机失败。"""
    import json
    import shlex

    from _fake_worker import FAKE_DETERMINISTIC_STEPS, FAKE_MIN_GRACE_S, FAKE_MODEL_ID
    from gherkai_core.wire import PROTOCOL_SCHEMA_VERSION

    worker = tmp_path / "fake_worker.py"
    worker.write_text(_FAKE_WORKER, encoding="utf-8")
    env = {k: v for k, v in os.environ.items()
           if k not in ("NGROK_AUTHTOKEN", "GHERKAI_CONFIG", "GHERKAI_STEPS_DIR", "AWS_PROFILE")}
    for engine, grace in FAKE_MIN_GRACE_S.items():
        caps = tmp_path / f"caps-{engine}.json"
        caps.write_text(json.dumps({
            "schema_version": PROTOCOL_SCHEMA_VERSION, "engine": engine, "min_grace_s": grace,
            "targets": [{"device": "desktop", "ui_kinds": ["web"]}], "deterministic_steps": FAKE_DETERMINISTIC_STEPS,
            "model_id": FAKE_MODEL_ID[engine], compose.SESSION_WARMUP_KEY: True}), encoding="utf-8")
        env[f"GHERKAI_WORKER_{engine.upper()}_CMD"] = shlex.join([sys.executable, str(worker), str(caps)])
        env.pop(f"GHERKAI_WORKER_{engine.upper()}_CWD", None)
    env.update(AWS_ENDPOINT_URL="http://127.0.0.1:9", AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing",
               AWS_EC2_METADATA_DISABLED="true")
    return env


@pytest.mark.real_filesystem
def test_run_in_a_real_process_rejects_a_report_dir_on_a_pseudo_filesystem_of_the_kernel(tmp_path):
    """真实进程、真实内核：报告目录在 macOS 的 /dev（Linux 上是 /proc）之下一个不存在的位置，`gherkai run` 在前置检查里按最近一层
    已存在的上级判断，以退出码 2 结束，标准输出为空，标准错误的末行是文件系统不受支持的那一句，什么都不建。子进程里没有测试的替身，
    文件系统类型是真实取到的；worker 是假的（不会被问到：被拒发生在问 worker 之前）。"""
    if sys.platform not in _PSEUDO_FILESYSTEM:
        pytest.skip("只核 macOS 与 Linux")
    base, fs_type = _PSEUDO_FILESYSTEM[sys.platform]
    report_dir = Path(base) / f"gherkai-missing-{os.getpid()}-{time.monotonic_ns()}" / "reports"
    assert not report_dir.parent.exists()
    proc = subprocess.run([sys.executable, "-P", "-m", "gherkai_cli", "run", str(_write_feature(tmp_path)),
                           "--report-dir", str(report_dir)],
                          cwd=tmp_path, env=_isolated_child_env(tmp_path), stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=120)
    assert (proc.returncode, proc.stdout) == (2, ""), proc.stderr
    assert proc.stderr.splitlines()[-1] == (
        f"报告目录 {report_dir} 还不存在，按最近一层已存在的上级 {base} 判断，它所在的文件系统是 {fs_type}，本机后端不支持："
        f"{_NOT_KNOWABLE}{_MOVE}；多台机器共用运行记录请用云端后端。")
    assert not report_dir.parent.exists()


def _lock_state_of(path: Path) -> run_dir.LockState:
    """另开一次 path、不阻塞地取排他锁，随即关闭（拿到的锁随之放开）。"""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        return run_dir.try_lock(fd).state
    finally:
        os.close(fd)


def _wait_for_file(path: Path, proc: subprocess.Popen, what: str) -> None:
    deadline = time.monotonic() + 60
    while not path.exists():
        assert proc.poll() is None, proc.communicate()
        assert time.monotonic() < deadline, f"子进程没有在时限内{what}"
        time.sleep(0.02)


def _signal_while_paused(proc: subprocess.Popen, held: Path, release: Path) -> None:
    """子进程停在某一步里时对它发 SIGINT：等一会儿让信号送达，核对它没有因此退出（处理器只记下、不打断这一步）、held 上的锁仍被持有，
    再放行。"""
    assert _lock_state_of(held) is run_dir.LockState.HELD
    proc.send_signal(signal.SIGINT)
    time.sleep(0.5)
    assert proc.poll() is None, "收到的 SIGINT 打断了正在做的一步"
    assert _lock_state_of(held) is run_dir.LockState.HELD
    release.touch()


# 在指定的几步里依次停下等 SIGINT 的前台 run：第一个参数是逗号分隔的停点，before-rename / after-rename 在打了补丁的 os.rename 里、
# 真实的改名之前或之后，engines 在装配引擎时，finalize 在按中断做结束写的那一步的入口；第 n 个停点停下时在工作目录里放 ready-n，
# 等到 release-n 出现再接着执行。持有者是生产用的（这个进程里没有测试的替身），能力自述取 _fake_worker 的替身，不开始执行。只用 ASCII
_INTERRUPTED_CREATE_DRIVER = r"""
import os, sys, time
from pathlib import Path
points, work, feature, tests_dir, run_id = sys.argv[1].split(","), Path(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
sys.path.insert(0, tests_dir)
import gherkai_cli.__main__ as m
from gherkai_core.adapters.run_store import run_dir
from gherkai_core.persist import RunPersistence
from gherkai_runtime import compose
from _fake_worker import fake_query_capabilities
compose.query_capabilities = fake_query_capabilities
compose.new_run_id = lambda at=None: run_id
real_rename, real_engines, real_finalize = os.rename, compose.build_engines, RunPersistence.finalize
passed = []

def at(point):
    if point not in points:
        return
    passed.append(point)
    n = len(passed)
    (work / ("ready-%d" % n)).touch()
    deadline = time.monotonic() + 60
    while not (work / ("release-%d" % n)).exists() and time.monotonic() < deadline:
        time.sleep(0.01)

def rename(src, dst, *a, **k):
    staging = Path(src).name.startswith(run_dir.STAGING_PREFIX)
    if staging:
        at("before-rename")
    real_rename(src, dst, *a, **k)
    if staging:
        at("after-rename")

def build_engines(**kw):
    at("engines")
    return real_engines(**kw)

def finalize(self, execution):
    at("finalize")
    return real_finalize(self, execution)

def no_schedule(*a, **k):
    raise SystemExit(99)

os.rename, compose.build_engines, RunPersistence.finalize, m.schedule = rename, build_engines, finalize, no_schedule
sys.exit(m.main(["run", feature, "--report-dir", str(work / "reports")]))
"""


@pytest.mark.real_filesystem
@pytest.mark.parametrize("points", ["after-rename", "before-rename", "engines", "after-rename,finalize"],
                         ids=["after-rename", "before-rename", "assembling-engines", "twice"])
def test_a_real_ctrl_c_while_creating_the_run_is_handled_after_the_run_is_created(points, tmp_path):
    """真实进程、真实信号：前台 run 停在建 run 的调用里（真实的改名之前或之后）或建 run 之后的装配引擎时收到 SIGINT；`twice` 在改名之后
    按一次、在按中断做结束写的那一步的入口再按一次。处理器只记下，所以进程不在这时退出，发信号之前与之后锁都被持有（改名之前是暂存目录
    上的、之后是 run 目录上的）；放行之后建 run 照常完成，启动第一个 job 之前看到中断，由这个进程自己按「使用方中断」那一行做结束写、
    生成报告，以 130 结束，标准输出为空、不打回溯，末行说这个 run 已因中断记为已结束，与记录、报告一致；没有留下暂存目录，进程退出之后
    锁随即拿得到。各种时机结果相同。"""
    reports = tmp_path / "reports"
    proc = subprocess.Popen(
        [sys.executable, "-P", "-c", _INTERRUPTED_CREATE_DRIVER, points, str(tmp_path),
         str(_write_feature(tmp_path)), str(Path(__file__).parent), FIXED_RUN_ID],
        cwd=tmp_path, env=_isolated_child_env(tmp_path), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    try:
        for n, point in enumerate(points.split(","), start=1):
            _wait_for_file(tmp_path / f"ready-{n}", proc, f"停到第 {n} 个停点")
            [name] = os.listdir(reports)
            assert name.startswith(run_dir.STAGING_PREFIX) if point == "before-rename" else name == FIXED_RUN_ID
            _signal_while_paused(proc, reports / name, tmp_path / f"release-{n}")
        out, err = proc.communicate(timeout=60)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()
    assert (proc.returncode, out, "Traceback" in err) == (130, "", False), err
    assert err.splitlines()[-1] == _ended_by_the_interrupt_line(reports)
    _assert_ended_by_the_interrupt(reports)
    assert _lock_state_of(reports / FIXED_RUN_ID) is run_dir.LockState.ACQUIRED


# 本机后台推进进程的模块搜索路径上放的 sitecustomize：给 os.rename 打补丁，改名暂存目录之前在 PAUSE 目录里放一个 paused 文件，
# 等到 release 文件出现再改名。只用 ASCII
_PAUSE_BEFORE_THE_RENAME = r"""
import os, time
_dir = os.environ.get("GHERKAI_TEST_PAUSE_DIR")
if _dir:
    _real_rename = os.rename

    def _rename(src, dst, *a, **k):
        if os.path.basename(os.fspath(src)).startswith(".gherkai-creating-"):
            open(os.path.join(_dir, "paused"), "w").close()
            deadline = time.monotonic() + 60
            while not os.path.exists(os.path.join(_dir, "release")) and time.monotonic() < deadline:
                time.sleep(0.01)
        return _real_rename(src, dst, *a, **k)

    os.rename = _rename
"""


@pytest.mark.real_filesystem
def test_a_real_sigint_while_the_advancer_creates_the_run_ends_it_and_leaves_the_staging_directory(tmp_path):
    """真实进程、真实信号：本机后台推进进程（以 `-P`、新会话启动的 `_reconcile` 入口，测试一侧充当 submit：经标准输入交出输入、
    读回报管道，标准输入的写端一直开着）停在建 run 的调用里、真实的改名之前时收到 SIGINT。它对 SIGINT 取缺省处置，随即被这个信号
    结束：标准错误没有回溯、没有 KeyboardInterrupt，没有回报，提交的一方读到的是回报管道的文件结束；报告目录里留下的是暂存目录
    （与被 SIGKILL 结束时相同），没有以 run 标识命名的目录，暂存目录上的锁随进程退出拿得到。"""
    hook, pause, reports = tmp_path / "hook", tmp_path / "pause", tmp_path / "reports"
    hook.mkdir()
    pause.mkdir()
    (hook / "sitecustomize.py").write_text(_PAUSE_BEFORE_THE_RENAME, encoding="utf-8")
    env = _isolated_child_env(tmp_path)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(hook), env.get("PYTHONPATH")) if p)
    env["GHERKAI_TEST_PAUSE_DIR"] = str(pause)
    job = Job(scope_id="s", scope_name="s", engine="novaact", timeout_s=300.0,
              scenarios=(Scenario(id="t.feature:2", name="s", steps=(Step(0, "When", "打开首页"),)),))
    line = handoff.encode_advancer_input(handoff.AdvancerInput(
        jobs=(job,), steps_dir=None, max_concurrency=1, per_job_tail_s=310.0, expose_local=None,
        tunnel_provider="ngrok", region="us-east-1", profile=None, report_dir=str(reports)))
    report_r, report_w = os.pipe()
    stdin_r, stdin_w = os.pipe()
    try:
        proc = subprocess.Popen([sys.executable, "-P", "-m", "gherkai_cli", "_reconcile", "--report-fd", str(report_w)],
                                stdin=stdin_r, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(report_w,),
                                start_new_session=True, cwd=tmp_path, env=env)
    finally:
        os.close(report_w)
        os.close(stdin_r)
    try:
        assert handoff.write_all(stdin_w, line)
        _wait_for_file(pause / "paused", proc, "停到建 run 的调用里")
        [staging] = os.listdir(reports)
        assert staging.startswith(run_dir.STAGING_PREFIX)
        assert _lock_state_of(reports / staging) is run_dir.LockState.HELD
        proc.send_signal(signal.SIGINT)
        out, err = proc.communicate(timeout=20)  # 被信号结束即刻返回；停在建 run 里没有结束的，到时限报出
        reported = handoff.read_line(report_r)
    finally:
        (pause / "release").touch()  # 没有被信号结束的，放行之后照常执行，下面的断言报出
        if proc.poll() is None:
            proc.kill()
            proc.communicate()
        os.close(stdin_w)
        os.close(report_r)
    text = err.decode("utf-8", "replace")
    assert (proc.returncode, out, reported) == (-signal.SIGINT, b"", b""), text
    assert "Traceback" not in text and "KeyboardInterrupt" not in text, text
    assert os.listdir(reports) == [staging]
    assert sorted(os.listdir(reports / staging)) == ["run_meta.json", "run_state.json"]
    assert _lock_state_of(reports / staging) is run_dir.LockState.ACQUIRED


# ---- 开始写出 run 标识之后到达的 Ctrl-C（ADR 0035 决策 3）----

_SUBMIT_DRIVER = Path(__file__).with_name("_submit_driver.py")


@pytest.mark.parametrize("backend", [pytest.param("local", marks=pytest.mark.real_filesystem), "cloud"])
def test_ctrl_c_after_the_run_id_is_written_does_not_change_the_result(backend, tmp_path):
    """真实进程、真实信号：submit 在标准输出写出 run 标识之后立刻收到 SIGINT，结果不变，退出码 0、标准输出恰为 run 标识。提交进程是
    `_submit_driver.py`（后台进程是线程替身，回报经真实管道）：它写出第一行之后停在放行描述符上，用例读到这一行、发出 SIGINT、再放行，
    信号落在标识已经写进管道、`print` 还没有返回的那一刻。本机后端的那一次在子进程里取真实的文件系统类型（`real_filesystem`）。"""
    hold_r, hold_w = os.pipe()
    env = {k: v for k, v in os.environ.items() if k != "NGROK_AUTHTOKEN"}
    try:
        proc = subprocess.Popen([sys.executable, str(_SUBMIT_DRIVER), backend, str(tmp_path), str(hold_r)],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                pass_fds=(hold_r,), cwd=tmp_path, env=env)
    finally:
        os.close(hold_r)
    try:
        first = proc.stdout.readline()
        if first:
            proc.send_signal(signal.SIGINT)
            time.sleep(0.2)  # 让信号在放行之前送达
    finally:
        os.close(hold_w)  # 放行：提交进程读到文件结束，从写出的那一步接着执行
    rest, err = proc.communicate(timeout=60)
    assert (proc.returncode, first + rest) == (0, f"{FIXED_RUN_ID}\n".encode()), err.decode("utf-8", "replace")
    if backend == "local":
        run = tmp_path / "reports" / FIXED_RUN_ID
        assert (run / "run_state.json").exists()
        fd = os.open(run, os.O_RDONLY | os.O_DIRECTORY)  # 建 run 的进程已退出、被回收：它持有的锁随之释放
        try:
            assert run_dir.try_lock(fd).state is run_dir.LockState.ACQUIRED
        finally:
            os.close(fd)


def test_ignore_interrupts_from_here_ignores_sigint_in_the_main_thread_and_does_nothing_elsewhere():
    """在主线程里把 SIGINT 的处置设为忽略；在别的线程里（测试从别的线程调用入口时）什么都不做、不抛错。"""
    errors: list = []

    def elsewhere():
        try:
            m._ignore_interrupts_from_here()
        except BaseException as e:  # noqa: BLE001 —— 交给下面断言
            errors.append(e)

    t = threading.Thread(target=elsewhere)
    t.start()
    t.join(5)
    assert errors == [] and signal.getsignal(signal.SIGINT) is signal.default_int_handler
    m._ignore_interrupts_from_here()
    assert signal.getsignal(signal.SIGINT) == signal.SIG_IGN  # 收尾的夹具恢复原处置


@pytest.mark.parametrize("backend", ["local", "cloud"])
def test_ctrl_c_that_surfaces_at_the_boundary_still_exits_130_with_nothing_written(backend, tmp_path, monkeypatch,
                                                                                   capsys, inline_children,
                                                                                   tunnel_service, advanced):
    """边界之前已经到达、在设置忽略时才抛出的中断：仍走 130 的出口，标准输出为空，说明 run 已经提交。"""
    if backend == "cloud":
        _patch_cloud_handles(monkeypatch, [])
    _fix_run_id(monkeypatch)
    real_ignore = m._ignore_interrupts_from_here

    def interrupted_then_ignore():
        signal.raise_signal(signal.SIGINT)
        real_ignore()

    monkeypatch.setattr(m, "_ignore_interrupts_from_here", interrupted_then_ignore)
    argv = _local_submit_argv(tmp_path) if backend == "local" else _cloud_submit_argv(tmp_path)
    rc = _main([*argv, "--expose-local", ORIGIN])
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 130 and cap.out == ""
    assert f"run {FIXED_RUN_ID} 已经提交，提交命令随后被中断。" in cap.err
