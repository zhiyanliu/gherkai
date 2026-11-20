"""测试用的 `subprocess.Popen` 替身：submit 启动的两种后台进程在同一进程的线程里执行真实的主体（ADR 0035 决策 3）。

submit 与它启动的后台进程之间的交接用真实的管道：替身认出 `_reconcile`（本机后台推进进程）与 `_tunnel_watch`（云端隧道守护进程）的
启动命令，先 `os.dup` 父进程交来的回报写端与标准输入读端（父进程随后关掉自己那一份，线程与父进程共用描述符表），再在线程里照进程入口
的做法读一行输入、解码，执行真实的 `__main__._advance_submitted` 或 `tunnel_host.hold_tunnel_for_cloud_run`。两端都是生产代码，管道的
文件结束、EPIPE 与非阻塞读都是真实的；主体返回或抛出之后，替身在 `finally` 里关闭它 dup 出来的两个描述符，就像进程退出时那样。

替身只换掉三样进程层面的东西，并各自说明：
- **改接输出**：主体的 `redirect_output` 换成不做 `dup2` 的记录函数（dup2 会改掉测试进程自己的 fd 1 与 2）。它收下日志描述符，此后
  这个线程经 `sys.stdout` / `sys.stderr` 写出的文字按线程写进那个日志描述符，其余线程照常写到原来的流；所以 submit 的标准错误里只有
  回报之前后台进程写的字，回报之后的写进真实的 `reconcile.log` 或守护进程日志。
- **回报之前不启动子进程**：后台进程改接输出之前，`subprocess.Popen`、`os.fork`、`os.posix_spawn` 被调用即记一次违规并抛错，收尾时
  判失败（ADR 0035 决策 3「输出」：回报之前起的子进程会继承接在 submit 标准错误上的描述符）。
- **崩溃**：主体抛出的异常记进 `InlineChild.error`，不打回溯；进程入口里它会打在 submit 的标准错误上、随后进程退出。用例要么用
  `expect_error` 认领它，要么收尾时判失败。

推进本身由用例把 `detached.advance_local_run` 换成记录调用的函数，不起 worker；守护进程的轮询经 `watch_kwargs` 注入存储与墙钟。
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from dataclasses import dataclass, field

import pytest

import gherkai_cli.__main__ as m
from gherkai_core.model import RunState, Status
from gherkai_runtime import handoff, tunnel_host

ENTRIES = ("_reconcile", "_tunnel_watch")


class SpawnBeforeReport(AssertionError):
    """后台进程在改接输出之前启动了子进程。"""


class TerminalStore:
    """守护进程轮询用的假 RunStore：任何 run 都已是 passed，守护进程第一次读到即关闭会话、退出。"""

    def __init__(self) -> None:
        self.reads: list[str] = []

    def load_run_state(self, run_id):
        self.reads.append(run_id)
        return RunState(run_id=run_id, status=Status.PASSED, jobs={})


@dataclass(eq=False)
class InlineChild:
    """一个在线程里执行的后台进程。"""

    argv: list
    kwargs: dict
    entry: str
    report_fd: int
    input_fd: int
    done: threading.Event = field(default_factory=threading.Event)
    redirected: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None
    returncode: int | None = None
    error: BaseException | None = None
    error_claimed: bool = False
    log_fd: int | None = None
    notes: list = field(default_factory=list)

    def redirect(self, log_fd: int) -> None:
        """替代 `handoff.redirect_output`：收下日志描述符，此后这个线程的输出写进它。"""
        self.log_fd = log_fd
        self.redirected.set()

    def note(self, s: str) -> None:
        """守护进程主体的 `note`，与进程入口的写法相同：以 `tunnel-watch:` 开头写到标准输出（这时已是日志）。"""
        self.notes.append(s)
        print(f"tunnel-watch: {s}", flush=True)

    def expect_error(self, kind: type[BaseException]) -> BaseException:
        assert isinstance(self.error, kind), f"后台进程应以 {kind.__name__} 结束，实际是 {self.error!r}"
        self.error_claimed = True
        return self.error

    def wait(self, timeout: float = 10.0) -> None:
        assert self.done.wait(timeout), f"后台进程 {self.entry} 在 {timeout} 秒内没有结束"


class _RoutedStream:
    """按线程分流的输出流：改接过输出的后台进程线程写进它的日志描述符，其余线程写到原来的流。"""

    def __init__(self, default, routes: dict) -> None:
        self._default = default
        self._routes = routes

    def write(self, s: str) -> int:
        fd = self._routes.get(threading.get_ident())
        if fd is None:
            return self._default.write(s)
        os.write(fd, s.encode("utf-8"))
        return len(s)

    def flush(self) -> None:
        if threading.get_ident() not in self._routes:
            self._default.flush()

    def __getattr__(self, name):
        return getattr(self._default, name)


class InlineChildren:
    """替换 `subprocess.Popen`；`children` 依次记下被启动的后台进程。"""

    def __init__(self, monkeypatch) -> None:
        self.children: list[InlineChild] = []
        self.violations: list[str] = []
        self.popen_error: OSError | None = None  # 给了即模拟「起不来后台进程」：Popen 抛它
        self.before_child = None                  # 后台进程线程开始时调用 before_child(child)
        self.on_spawn = None                      # Popen 被调用、线程启动之前在调用方线程里调用 on_spawn(argv, kwargs)
        self.watch_kwargs: dict = {"open_store": TerminalStore, "poll_interval_s": 0.05}
        self._routes: dict[int, int] = {}
        self._streams = None
        self._real_popen = subprocess.Popen
        monkeypatch.setattr(subprocess, "Popen", self.popen)
        for name in ("fork", "posix_spawn", "posix_spawnp"):
            if hasattr(os, name):
                monkeypatch.setattr(os, name, self._guarded(name, getattr(os, name)))

    # ---- 回报之前不启动子进程 ----

    def _pre_report(self) -> list[InlineChild]:
        return [c for c in self.children if not c.done.is_set() and not c.redirected.is_set()]

    def _guarded(self, name: str, real):
        def guarded(*a, **k):
            early = self._pre_report()
            if early:
                self.violations.append(f"{early[0].entry} 改接输出之前调用了 os.{name}")
                raise SpawnBeforeReport(f"后台进程在回报之前调用了 os.{name}")
            return real(*a, **k)
        return guarded

    # ---- Popen ----

    def popen(self, argv, **kwargs):
        early = self._pre_report()
        if early:
            self.violations.append(f"{early[0].entry} 改接输出之前启动了子进程 {argv!r}")
            raise SpawnBeforeReport(f"后台进程在回报之前启动了子进程 {argv!r}")
        entry = next((a for a in argv if a in ENTRIES), None)
        if entry is None:
            if threading.current_thread() is not threading.main_thread():
                raise AssertionError(f"替身不起 worker：请把推进换成记录调用的函数（收到 {argv!r}）")
            return self._real_popen(argv, **kwargs)
        if self.popen_error is not None:
            raise self.popen_error
        if self.on_spawn is not None:
            self.on_spawn(argv, kwargs)
        report_w = int(argv[argv.index("--report-fd") + 1])
        stdin = kwargs["stdin"]
        assert isinstance(stdin, int), f"后台进程的标准输入应是管道的读端描述符，收到 {stdin!r}"
        child = InlineChild(argv=list(argv), kwargs=dict(kwargs), entry=entry,
                            report_fd=os.dup(report_w), input_fd=os.dup(stdin))
        self._install_streams()
        child.thread = threading.Thread(target=self._run, args=(child,), name=f"inline{entry}", daemon=True)
        self.children.append(child)
        child.thread.start()
        return _Proc()

    def _run(self, child: InlineChild) -> None:
        try:
            if self.before_child is not None:
                self.before_child(child)
            line = handoff.read_line(child.input_fd)  # 同进程入口：读到文件结束即以 2 结束、不输出
            if not line:
                child.returncode = 2
                return
            if child.entry == "_reconcile":
                child.returncode = m._advance_submitted(
                    handoff.decode_advancer_input(line), report_fd=child.report_fd, input_fd=child.input_fd,
                    redirect_output=self._redirector(child))
            else:
                child.returncode = tunnel_host.hold_tunnel_for_cloud_run(
                    handoff.decode_watch_input(line), report_fd=child.report_fd, input_fd=child.input_fd,
                    note=child.note, redirect_output=self._redirector(child), **self.watch_kwargs)
        except BaseException as e:  # noqa: BLE001 —— 进程里它会打出回溯、进程退出；这里记下，由用例认领
            child.error = e
        finally:
            self._routes.pop(threading.get_ident(), None)
            handoff.close_quietly(child.report_fd)
            handoff.close_quietly(child.input_fd)
            if child.log_fd is not None:
                handoff.close_quietly(child.log_fd)
            child.done.set()

    def _redirector(self, child: InlineChild):
        def redirect(log_fd: int) -> None:
            child.redirect(log_fd)
            self._routes[threading.get_ident()] = log_fd
        return redirect

    def _install_streams(self) -> None:
        if self._streams is None:
            self._streams = (sys.stdout, sys.stderr)
            sys.stdout = _RoutedStream(sys.stdout, self._routes)
            sys.stderr = _RoutedStream(sys.stderr, self._routes)

    # ---- 收尾 ----

    def only(self) -> InlineChild:
        assert len(self.children) == 1, f"应启动恰好一个后台进程，实际 {len(self.children)} 个"
        return self.children[0]

    def settle(self, timeout: float = 10.0) -> None:
        """等全部后台进程结束，判回报之前启动子进程的违规。崩溃由用例在这之后用 `expect_error` 认领，没有认领的在收尾时判失败。"""
        for c in self.children:
            c.wait(timeout)
        if self.violations:
            pytest.fail("；".join(self.violations))

    def check_unclaimed_errors(self) -> None:
        for c in self.children:
            if c.error is not None and not c.error_claimed:
                pytest.fail(f"后台进程 {c.entry} 意外崩溃：{c.error!r}")

    def close(self) -> None:
        for c in self.children:
            c.done.wait(10.0)
        if self._streams is not None:
            out, err = self._streams
            if isinstance(sys.stdout, _RoutedStream):
                sys.stdout = out
            if isinstance(sys.stderr, _RoutedStream):
                sys.stderr = err
            self._streams = None


class _Proc:
    """返回给 submit 的进程对象：submit 不用它（交接只经两条管道）。"""

    pid = 0
    returncode = None


@pytest.fixture
def inline_children(monkeypatch, tmp_path):
    """submit 启动的后台进程改在线程里执行（见模块头）。守护进程的日志落在用例的临时目录：`handoff.watch_log_path` 取系统临时目录。"""
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    children = InlineChildren(monkeypatch)
    try:
        yield children
        children.settle()
        children.check_unclaimed_errors()
    finally:
        children.close()
