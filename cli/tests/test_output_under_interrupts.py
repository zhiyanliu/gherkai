"""装只记标志的中断处理器的三个命令（前台 `run`、`settle-runs`、本机等待中的 `status --wait`）在处理器还装着时写完标准输出（ADR 0054
决策八「中断」：输出在处理器还装着时写完并刷新，只有让命令少做了事的中断才改变结果）。

证据边界：真实进程、真实信号、真实管道。标准输出接在一个预先写满、先不读的管道上，命令此后写出的任何内容都要等读端读走：命令卡在
写输出时收到 SIGTERM 与 SIGINT，再读管道。标准输出按块缓冲，命令的输出小于缓冲时，不在命令里写出就要到解释器退出时才写，那时处理器
已经恢复，SIGTERM 即结束进程、输出一个字节都不出现。run 目录、生命期锁与运行态是真实的（`test_settle_runs` 的 `_create`）；前台 `run`
的执行由子进程里的 sitecustomize 换成直接判通过的替身（这里核的是执行结束之后的输出，不是执行本身），worker 只回答能力自述。
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path

import pytest

from gherkai_core.model import Status
from test_settle_runs import _child_env, _cli, _create, _kill_and_reap, _state, _wait_until, holders  # noqa: F401 —— holders 是夹具

# 子进程里的 sitecustomize：GHERKAI_TEST_MARK_AT 列出的各个函数（`模块:属性`，逗号分隔）被调用时先在 GHERKAI_TEST_MARK_DIR 里放一个
# output 文件，再照常执行，测试据此知道命令已开始输出；GHERKAI_TEST_PASSING_SCHEDULE 为 1 时把执行换成判全部 job 通过的替身（每个 job
# 照常经 on_job_complete 写下结果）。只用 ASCII
_MARK_OUTPUT = r"""
import importlib, os

_dir = os.environ.get("GHERKAI_TEST_MARK_DIR")


def _wrap(spec):
    mod_name, attr = spec.split(":")
    mod = importlib.import_module(mod_name)
    real = getattr(mod, attr)

    def wrapped(*a, **k):
        open(os.path.join(_dir, "output"), "w").close()
        return real(*a, **k)

    setattr(mod, attr, wrapped)


if _dir:
    for _spec in os.environ.get("GHERKAI_TEST_MARK_AT", "").split(","):
        if _spec:
            _wrap(_spec)

if os.environ.get("GHERKAI_TEST_PASSING_SCHEDULE") == "1":
    import gherkai_core.schedule as _schedule
    from gherkai_core.model import JobResult, Status

    def _passing(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        results = tuple(JobResult(job=j, status=Status.PASSED) for j in run_meta.jobs)
        for jr in results:
            if on_job_complete is not None:
                on_job_complete(jr)
        return _schedule.Execution(run_meta=run_meta, results=results, stopped_by=None, duration_ms=0.0)

    _schedule.schedule = _passing
"""


def _full_pipe() -> tuple[int, int, int]:
    """一个已经写满的管道：返回 (读端, 写端, 预先写进的字节数)。先以不阻塞的方式按从大到小的块写到连 1 个字节都写不进（macOS 的管道在
    大块写入时会扩容，大块在前使它扩到上限），再把写端改回阻塞。"""
    r, w = os.pipe()
    os.set_blocking(w, False)
    filled = 0
    for size in (65536, 4096, 512, 1):
        while True:
            try:
                filled += os.write(w, b"x" * size)
            except BlockingIOError:
                break
    os.set_blocking(w, True)
    return r, w, filled


def _read_all(fd: int) -> bytes:
    data = bytearray()
    while chunk := os.read(fd, 65536):
        data += chunk
    return bytes(data)


def _signal_while_writing_the_output(tmp_path: Path, argv: list[str], *, mark_at: str, env_extra: "dict | None" = None
                                     ) -> tuple[int, str, str]:
    """以预先写满的管道作标准输出启动命令；等它开始输出（sitecustomize 放下 output 文件）之后再等 1 秒，让它停在写标准输出上，对它依次发
    SIGTERM 与 SIGINT，核对它没有因此退出，然后读走管道、等它结束。返回 (退出码, 去掉预先写进的部分之后的标准输出, 标准错误)。"""
    hook, mark = tmp_path / "hook", tmp_path / "mark"
    hook.mkdir()
    mark.mkdir()
    (hook / "sitecustomize.py").write_text(_MARK_OUTPUT, encoding="utf-8")
    env = _child_env(tmp_path)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(hook), env.get("PYTHONPATH")) if p)
    env.update(GHERKAI_TEST_MARK_DIR=str(mark), GHERKAI_TEST_MARK_AT=mark_at, **(env_extra or {}))
    r, w, filled = _full_pipe()
    err_path = tmp_path / "stderr.txt"
    try:
        with open(err_path, "wb") as err_file:
            proc = subprocess.Popen(_cli(*argv), cwd=tmp_path, env=env, stdin=subprocess.DEVNULL, stdout=w, stderr=err_file)
        os.close(w)
        w = -1
        try:
            _wait_until(lambda: (mark / "output").exists(), proc, "开始输出")
            time.sleep(1.0)
            assert proc.poll() is None, "标准输出写满时命令应停在写输出上"
            proc.send_signal(signal.SIGTERM)
            proc.send_signal(signal.SIGINT)
            time.sleep(0.5)
            assert proc.poll() is None, f"停在写输出上时收到的信号结束了进程（退出码 {proc.returncode}）"
            data = _read_all(r)
            proc.wait(timeout=60)
        finally:
            if proc.poll() is None:
                _kill_and_reap(proc)
    finally:
        if w != -1:
            os.close(w)
        os.close(r)
    assert data[:filled] == b"x" * filled
    return proc.returncode, data[filled:].decode("utf-8"), err_path.read_text(encoding="utf-8")


@pytest.mark.real_filesystem
@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_settle_runs_writes_its_whole_output_while_the_handler_is_installed(machine, tmp_path, holders):
    """`settle-runs` 处置完两个 run、标准输出写不进时收到 SIGTERM 与 SIGINT：进程不因此退出；读走管道之后输出完整（--json 恰好一个对象、
    两项都在；人读表格两行都在），退出码与没有中断时相同（0），没有停止的说明；两个 run 都已记为已结束。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    rc, out, err = _signal_while_writing_the_output(
        tmp_path, ["settle-runs", "--report-dir", str(root), *(["--json"] if machine else [])],
        mark_at="gherkai_cli.render:settle_runs_to_dict,gherkai_cli.render:render_settle_runs")
    assert (rc, err) == (0, ""), err
    if machine:
        doc = json.loads(out)
        assert [(r["run_id"], r["outcome"]) for r in doc["runs"]] == [(first, "settled"), (second, "settled")]
    else:
        rows = [ln for ln in out.splitlines() if first in ln or second in ln]
        assert len(rows) == 2 and all("已记为已结束" in ln for ln in rows), out
    assert _state(root, first).status is Status.ABORTED and _state(root, second).status is Status.ABORTED


@pytest.mark.real_filesystem
@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_status_wait_writes_its_whole_display_while_the_handler_is_installed(machine, tmp_path, holders):
    """等待中的 `status --wait` 处置之后显示这个 run、标准输出写不进时收到 SIGTERM 与 SIGINT：进程不因此退出；读走管道之后显示完整
    （--json 恰好一个文档），退出码与没有中断时相同（aborted 为 1），没有停止等待的说明。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    rc, out, err = _signal_while_writing_the_output(
        tmp_path, ["status", run_id, "--report-dir", str(root), "--wait", *(["--json"] if machine else [])],
        mark_at="gherkai_core.serialize:run_state_to_dict,gherkai_cli.render:render_run_state")
    assert rc == 1, err
    assert "已停止" not in err
    if machine:
        assert err == ""
        assert (json.loads(out)["run_id"], json.loads(out)["status"]) == (run_id, "aborted")
    else:
        assert err.splitlines()[0] == f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出。"
        assert out.splitlines()[0] == f"run {run_id}: aborted"


@pytest.mark.real_filesystem
@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_run_writes_its_whole_summary_while_the_handler_is_installed(machine, tmp_path):
    """前台 `run` 执行结束、标准输出写不进汇总时收到 SIGTERM 与 SIGINT：进程不因此退出；读走管道之后汇总完整（--json 恰好一个文档），
    退出码与没有中断时相同（判通过为 0），记录里 run 为 passed。"""
    root = tmp_path / "reports"
    feature = tmp_path / "t.feature"
    feature.write_text('Feature: t\n  Scenario: s\n    When "打开首页"\n', encoding="utf-8")
    rc, out, err = _signal_while_writing_the_output(
        tmp_path, ["run", str(feature), "--report-dir", str(root), *(["--json"] if machine else [])],
        mark_at="gherkai_cli.render:to_dict,gherkai_cli.render:render_text", env_extra={"GHERKAI_TEST_PASSING_SCHEDULE": "1"})
    assert rc == 0, err
    assert "Traceback" not in err and "收到中断信号" not in err
    [run_id] = [n for n in os.listdir(root) if not n.startswith(".")]
    if machine:
        doc = json.loads(out)
        assert (doc["run_id"], doc["status"]) == (run_id, "passed")
    else:
        assert "passed" in out and out.endswith("\n")
    assert _state(root, run_id).status is Status.PASSED
