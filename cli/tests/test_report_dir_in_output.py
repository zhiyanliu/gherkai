"""输出里的本机路径一律是解析之后的绝对路径（ADR 0041 决策六「输出里的本机路径」）：给使用者照抄执行的整条命令（查进度、列出 run、把
run 记为已结束）带的 `--report-dir`，以及输出里出现的报告目录、run 目录与文件的位置，都取入口（`_local_report_root`）解析之后的那一个，
不回显使用者原样给的写法。

两种写法各核一遍：相对路径（相对当前工作目录），与经符号链接的路径（链接指向另一处）。照抄的命令换到另一个工作目录下执行仍找到这个
run：进程内的用例在另一个工作目录下以同一个入口执行它；另有两条真实进程的用例（本机 submit 之后照提示执行 status；记录写下之后准备执行
用的文件失败时照提示执行 settle-runs），工作目录与执行命令的进程都是真实的。机读输出的 `report_dir` 字段本来就取解析之后的绝对路径，
它的用例在 `test_settle_runs.py` 与 `test_main.py`，这里不重复。
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

import gherkai_cli.__main__ as m
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Status
from gherkai_runtime import handoff

from _inline_children import inline_children  # noqa: F401 —— 夹具：本机 submit 启动的后台推进进程在线程里执行
from test_main import _disk_full, _fake_schedule_factory, _no_wait_save_retry, _write_feature, advanced  # noqa: F401
from test_settle_runs import _create, _lock_state, _sigint_inside_end_run, holders  # noqa: F401 —— holders 是夹具
from test_tunnel_cli import FIXED_RUN_ID, _fix_run_id, _isolated_child_env, _main, _raise_sigint_at


@pytest.fixture(params=["relative", "symlink"])
def given(request, tmp_path, monkeypatch) -> tuple[str, Path]:
    """`--report-dir` 的一种写法与它解析之后的绝对路径。当前工作目录换成 tmp_path/work：相对路径的那种是 `reports`；经符号链接的那种
    是 work/link/reports，link 指向 tmp_path/elsewhere。"""
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    if request.param == "relative":
        return "reports", (work / "reports").resolve()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (work / "link").symlink_to(elsewhere)
    return str(work / "link" / "reports"), (elsewhere / "reports").resolve()


@pytest.fixture
def another_dir(tmp_path) -> Path:
    other = tmp_path / "another"
    other.mkdir()
    return other


def _report_dir_of(command: str, verb: str) -> str:
    argv = shlex.split(command)
    assert argv[:2] == ["gherkai", verb], command
    return argv[argv.index("--report-dir") + 1]


def _run_here(monkeypatch, where: Path, command: str, capsys) -> tuple[int, str, str]:
    """在 where 这个工作目录下以同一个入口执行照抄来的整条命令。"""
    capsys.readouterr()
    monkeypatch.chdir(where)
    rc = m.main(shlex.split(command)[1:])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


# ---- submit ----

def test_submit_progress_hint_gives_the_resolved_report_dir_and_works_elsewhere(given, another_dir, tmp_path, monkeypatch,
                                                                              capsys, inline_children, advanced):
    """本机 submit 的查进度命令带解析之后的报告目录：换一个工作目录照抄执行找到这个 run；经符号链接给出的，链接随后改指向一个空目录，
    照抄的命令仍找到它。"""
    written, resolved = given
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", written]) == 0
    inline_children.settle()
    cap = capsys.readouterr()
    run_id = cap.out.strip()
    hint = re.search(r"查进度：(gherkai status .*)$", cap.err, re.M).group(1)
    assert _report_dir_of(hint, "status") == str(resolved)
    link = tmp_path / "work" / "link"
    if link.is_symlink():
        (tmp_path / "empty").mkdir()
        link.unlink()
        link.symlink_to(tmp_path / "empty")
    rc, out, _err = _run_here(monkeypatch, another_dir, hint, capsys)
    assert rc == 0 and out.splitlines()[0] == f"run {run_id}: pending"


def _interrupt_on_the_first_line_after_the_report(monkeypatch) -> None:
    real_progress = m._progress

    def progress(*a, **k):
        if a and str(a[0]).startswith("已提交（本机后台推进中）"):
            raise KeyboardInterrupt
        real_progress(*a, **k)

    monkeypatch.setattr(m, "_progress", progress)


def _interrupt_right_after_reading_the_report(monkeypatch) -> None:
    import threading

    real_read_line = handoff.read_line

    def read_line(fd):
        line = real_read_line(fd)
        if threading.current_thread() is threading.main_thread():  # 提交进程读回报的那一次；线程里的后台推进进程照常读输入
            raise KeyboardInterrupt  # 回报已经读到，run 已经建成；中断落在记下它之前
        return line

    monkeypatch.setattr(handoff, "read_line", read_line)


def _crash_before_reporting(monkeypatch, inline_children) -> None:
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(m, "_build_run_meta", boom)
    inline_children.expect_crash_before_report()


@pytest.mark.parametrize("case", ["interrupted-after-the-report", "interrupted-before-recording-the-report",
                                  "advancer-exited-before-reporting"])
def test_submit_failure_hints_give_the_resolved_report_dir(case, given, another_dir, tmp_path, monkeypatch, capsys,
                                                           inline_children, advanced):
    """本机 submit 没有正常给出结果的三种出口：收到回报之后被打断（查进度的 status 命令）、读到回报还没有记下就被打断（确认用的 list-runs
    命令）、后台推进进程在回报之前退出（不带 run 标识的 settle-runs 命令）。三条命令带的都是解析之后的报告目录，换一个工作目录照抄执行
    看到的是同一个报告目录。"""
    written, resolved = given
    if case == "interrupted-after-the-report":
        _interrupt_on_the_first_line_after_the_report(monkeypatch)
    elif case == "interrupted-before-recording-the-report":
        _interrupt_right_after_reading_the_report(monkeypatch)
    else:
        _crash_before_reporting(monkeypatch, inline_children)
    rc = _main(["submit", str(_write_feature(tmp_path)), "--report-dir", written])
    inline_children.settle()
    err = capsys.readouterr().err
    if case == "advancer-exited-before-reporting":
        inline_children.only().expect_error(RuntimeError)
        assert rc == 2
        command = re.search(r"可以用 (gherkai settle-runs .*?) 把执行它的进程已不在的 run", err).group(1)
        assert _report_dir_of(command, "settle-runs") == str(resolved)
        rc, out, _err = _run_here(monkeypatch, another_dir, command + " --json", capsys)
        assert rc == 0 and json.loads(out)["report_dir"] == str(resolved)
        return
    assert rc == 130
    [run_id] = os.listdir(resolved)
    if case == "interrupted-after-the-report":
        command = re.search(r"查进度：(gherkai status .*)$", err, re.M).group(1)
        assert _report_dir_of(command, "status") == str(resolved)
        rc, out, _err = _run_here(monkeypatch, another_dir, command, capsys)
        assert rc == 0 and out.splitlines()[0] == f"run {run_id}: pending"
    else:
        command = re.search(r"请先用 (gherkai list-runs .*?) 确认", err).group(1)
        assert _report_dir_of(command, "list-runs") == str(resolved)
        rc, out, _err = _run_here(monkeypatch, another_dir, command + " --json", capsys)
        assert rc == 0 and [r["run_id"] for r in json.loads(out)["runs"]] == [run_id]


# ---- status、status --wait ----

def test_status_wait_interrupted_after_settling_gives_the_resolved_report_dir(given, another_dir, holders, monkeypatch,
                                                                              capsys):
    """等待中的 status --wait 处置之后被 Ctrl-C 打断：给出的查看命令带解析之后的报告目录，换一个工作目录照抄执行看到被记为已结束的 run。"""
    written, resolved = given
    run_id = "20300101T000000Z-aaaaaa"
    _create(resolved, run_id, holders).release()
    _sigint_inside_end_run(monkeypatch)
    assert m.main(["status", run_id, "--report-dir", written, "--wait"]) == 130
    err = capsys.readouterr().err
    assert err.splitlines() == [f"已停止：本命令已把 run {run_id} 记为已结束，可用 gherkai status {run_id} --report-dir {resolved} 查看。"]
    command = re.search(r"可用 (gherkai status .*?) 查看", err).group(1)
    rc, out, _err = _run_here(monkeypatch, another_dir, command, capsys)
    assert rc == 1 and out.splitlines()[0] == f"run {run_id}: aborted"


@pytest.mark.parametrize("wait", [False, True], ids=["status", "status-wait"])
def test_status_failure_notices_name_the_resolved_run_dir(wait, given, holders, capsys):
    """运行态读不出时 status 与 status --wait 同一句，点名解析之后的 run 目录。"""
    written, resolved = given
    run_id = "20300101T000000Z-aaaaaa"
    _create(resolved, run_id, holders).release()
    (resolved / run_id / "run_state.json").write_text("{broken", encoding="utf-8")
    assert m.main(["status", run_id, "--report-dir", written, *(["--wait"] if wait else [])]) == 2
    assert f"确认不需要之后可以手工移走 run 目录 {resolved / run_id}。" in capsys.readouterr().err


def test_status_wait_that_cannot_decide_names_the_resolved_paths(given, holders, monkeypatch, capsys):
    """锁不可用、提交记录也读不出时以 2 结束的那一句：点名的 run 目录与给出的查看命令都用解析之后的路径。"""
    import errno
    import fcntl

    real_flock = fcntl.flock

    def flock(fd, op):
        if op & fcntl.LOCK_NB:
            raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))
        return real_flock(fd, op)

    written, resolved = given
    run_id = "20300101T000000Z-aaaaaa"
    _create(resolved, run_id, holders).release()
    (resolved / run_id / "run_meta.json").unlink()
    monkeypatch.setattr(fcntl, "flock", flock)
    assert m.main(["status", run_id, "--report-dir", written, "--wait"]) == 2
    err = capsys.readouterr().err
    assert f"请检查 run 目录 {resolved / run_id} 所在的文件系统" in err
    assert _report_dir_of(re.search(r"只查看它现在的状态可用 (gherkai status .*?)。", err).group(1), "status") == str(resolved)


# ---- explain、list-runs、settle-runs ----

def test_explain_wait_hint_gives_the_resolved_report_dir(given, another_dir, holders, monkeypatch, capsys):
    written, resolved = given
    run_id = "20300101T000000Z-aaaaaa"
    _create(resolved, run_id, holders)
    assert m.main(["explain", run_id, "--report-dir", written]) == 0
    command = re.search(r"可先用 (gherkai status .*? --wait) 等到终态", capsys.readouterr().err).group(1)
    assert _report_dir_of(command, "status") == str(resolved)
    rc, out, _err = _run_here(monkeypatch, another_dir, command.removesuffix(" --wait"), capsys)
    assert rc == 0 and out.splitlines()[0] == f"run {run_id}: running"


def test_list_runs_and_settle_runs_name_the_resolved_report_dir(given, capsys):
    """报告目录还不存在时两个命令的那一句都点名解析之后的报告目录。"""
    written, resolved = given
    assert m.main(["list-runs", "--report-dir", written]) == 0
    assert f"本机后端的报告目录 {resolved} 不存在，这里还没有 run。" in capsys.readouterr().out
    assert m.main(["settle-runs", "--report-dir", written]) == 0
    assert capsys.readouterr().out == f"报告目录 {resolved} 不存在，这里还没有 run。\n"


# ---- 前台 run 的几种出口 ----

def test_run_interrupted_before_starting_gives_the_resolved_report_dir(given, another_dir, tmp_path, monkeypatch, capsys):
    """前台 run 建 run 之后、开始执行之前被中断：自己记为已结束，给出的查看命令带解析之后的报告目录。"""
    written, resolved = given
    _fix_run_id(monkeypatch)
    _raise_sigint_at("after-the-call", monkeypatch)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("建 run 被中断时不该开始执行"))
    assert _main(["run", str(_write_feature(tmp_path)), "--report-dir", written]) == 130
    err = capsys.readouterr().err
    assert err.splitlines()[-1] == (f"已停止：run {FIXED_RUN_ID} 已因中断记为已结束，没有 job 开始执行；"
                                    f"可用 gherkai status {FIXED_RUN_ID} --report-dir {resolved} 查看。")
    rc, out, _err = _run_here(monkeypatch, another_dir, re.search(r"可用 (gherkai status .*?) 查看", err).group(1), capsys)
    assert rc == 1 and out.splitlines()[0] == f"run {FIXED_RUN_ID}: aborted"


def test_run_storage_failure_notice_gives_the_resolved_paths(given, another_dir, tmp_path, monkeypatch, capsys, lock_holder):
    """运行期读写记录失败：说明里的记录位置、查看命令与 settle-runs 命令都用解析之后的路径；照抄的 settle-runs 在另一个工作目录下把它
    记为已结束（本用例里持锁的是测试进程的持有者，放开之后即管它的进程已不在）。"""
    from gherkai_core.adapters.result_store.local import LocalResultStore

    written, resolved = given
    _no_wait_save_retry(monkeypatch)
    monkeypatch.setattr(LocalResultStore, "save_job_result", lambda self, run_id, result_id, job: _disk_full())
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", written]) == 1
    err = capsys.readouterr().err
    [run_id] = os.listdir(resolved)
    assert f"记录在 {resolved / run_id}，" in err
    assert _report_dir_of(re.search(r"可用 (gherkai status .*?) 查看", err).group(1), "status") == str(resolved)
    settle = re.search(r"再用 (gherkai settle-runs .*?) 把这个 run 记为已结束", err).group(1)
    assert _report_dir_of(settle, "settle-runs") == str(resolved)
    lock_holder.close_all()
    rc, out, _err = _run_here(monkeypatch, another_dir, settle + " --json", capsys)
    assert rc == 0 and json.loads(out)["runs"] == [
        {"run_id": run_id, "outcome": "settled", "reason": "advancer_exited", "report_written": True}]


# ---- 真实进程：照抄提示里的命令，在另一个工作目录下执行 ----

def _gherkai(*argv) -> list[str]:
    return [sys.executable, "-P", "-m", "gherkai_cli", *argv]


@pytest.mark.real_filesystem
def test_a_real_submit_progress_hint_finds_the_run_from_another_directory(tmp_path):
    """真实进程：在 work 下以相对的 --report-dir 执行本机 submit（后台推进进程真实启动，假 worker 一执行即退出，run 随即以出错结束），
    照它给出的查进度命令在另一个工作目录下执行 status：找到的是同一个 run。等后台推进进程放开锁、退出之后才结束。"""
    work, other = tmp_path / "work", tmp_path / "another"
    work.mkdir()
    other.mkdir()
    env = _isolated_child_env(tmp_path)
    submitted = subprocess.run(_gherkai("submit", str(_write_feature(tmp_path)), "--report-dir", "reports", "--region", "us-east-1"),
                               cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    assert submitted.returncode == 0, submitted.stderr
    run_id = submitted.stdout.strip()
    resolved = (work / "reports").resolve()
    hint = re.search(r"查进度：(gherkai status .*)$", submitted.stderr, re.M).group(1)
    assert _report_dir_of(hint, "status") == str(resolved)
    try:
        shown = subprocess.run(_gherkai(*shlex.split(hint)[1:]), cwd=other, env=env, stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=120)
        assert shown.returncode in (0, 1), shown.stderr
        assert shown.stdout.splitlines()[0].startswith(f"run {run_id}: "), shown.stdout
    finally:
        _wait_for_the_advancer_to_leave(resolved / run_id)


def _wait_for_the_advancer_to_leave(run_path: Path, timeout: float = 60.0) -> None:
    """后台推进进程在 run 结束之后放开锁、退出：等到 run 是终态且锁拿得到为止。"""
    import time

    from gherkai_core.adapters.run_store import run_dir

    deadline = time.monotonic() + timeout
    while True:
        state = LocalRunStore(run_path.parent).load_run_state(run_path.name)
        if state is not None and state.status not in (Status.PENDING, Status.RUNNING) \
                and _lock_state(run_path) is run_dir.LockState.ACQUIRED:
            return
        assert time.monotonic() < deadline, "后台推进进程没有在时限内结束"
        time.sleep(0.05)


# 前台 run 的子进程里把事件库换成建不出的那一种：记录写下之后准备执行用的文件失败（只用 ASCII）
_BROKEN_EVENT_LOG = """\
import sqlite3
from gherkai_core.adapters import event_log


def _broken(path):
    raise sqlite3.OperationalError("unable to open database file")


event_log.SqliteEventLog = _broken
"""


@pytest.mark.real_filesystem
def test_a_real_settle_runs_hint_finds_the_run_from_another_directory(tmp_path):
    """真实进程：在 work 下以相对的 --report-dir 执行 run，记录写下之后建事件库失败（子进程里的 sitecustomize 换掉事件库），以 2 结束、
    run 停在 pending；照说明里的 settle-runs 命令在另一个工作目录下执行（另一个不带替换的真实进程）：找到这个 run，执行它的进程已退出，
    把它记为已结束。"""
    work, other, hook = tmp_path / "work", tmp_path / "another", tmp_path / "hook"
    for d in (work, other, hook):
        d.mkdir()
    (hook / "sitecustomize.py").write_text(_BROKEN_EVENT_LOG, encoding="utf-8")
    env = _isolated_child_env(tmp_path)
    broken_env = {**env, "PYTHONPATH": os.pathsep.join(p for p in (str(hook), env.get("PYTHONPATH")) if p)}
    failed = subprocess.run(_gherkai("run", str(_write_feature(tmp_path)), "--report-dir", "reports"), cwd=work, env=broken_env,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    assert failed.returncode == 2, failed.stderr
    resolved = (work / "reports").resolve()
    [run_id] = os.listdir(resolved)
    hint = re.search(r"再用 (gherkai settle-runs .*?) 把这个 run 记为已结束", failed.stderr).group(1)
    assert shlex.split(hint)[2] == run_id and _report_dir_of(hint, "settle-runs") == str(resolved)
    settled = subprocess.run(_gherkai(*shlex.split(hint)[1:], "--json"), cwd=other, env=env, stdin=subprocess.DEVNULL,
                             capture_output=True, text=True, timeout=120)
    assert settled.returncode == 0, settled.stderr
    assert json.loads(settled.stdout)["runs"] == [
        {"run_id": run_id, "outcome": "settled", "reason": "advancer_exited", "report_written": True}]
    assert LocalRunStore(resolved).load_run_state(run_id).status is Status.ABORTED
