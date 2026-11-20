"""交接协议（ADR 0035 决策 3）：消息的往返、原始描述符的读写与「对端还在不在」的判据。

描述符的用例一律用真实的 `os.pipe`、真实的线程与子进程：文件结束、EAGAIN、EPIPE 都来自操作系统，不用假管道。
`redirect_output` 的用例放在子进程里：它用 `dup2` 改写标准输入、输出与错误，在测试进程里执行会改掉 pytest 自己的输出。
"""
from __future__ import annotations

import json
import os
import select
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

from gherkai_core.model import AppRef, DeviceFarmRequest, Job, Scenario, Step, StepArgument, Target
from gherkai_runtime import handoff

_SECRET = "tok-3f9c1a"
_WARMUP = f"https://abc.ngrok-free.app/__gherkai_warmup?token={_SECRET}"
_BIG = 4 * 1024 * 1024   # 大于两个平台上管道缓冲的上限


# ── 辅助 ────────────────────────────────────────────────────────────────────


def _jobs() -> tuple[Job, ...]:
    """桌面网页、Android 网页（按系统版本选设备）、iOS 应用（指定设备、带安装包位置）三种 definition 形态的 job。"""
    steps = (
        Step(0, "Given", "打开 http://localhost:3000/"),
        Step(1, "When", "填写备注", argument=StepArgument(kind="docString", content="第一行\n第二行")),
        Step(2, "Then", "看到列表", argument=StepArgument(kind="dataTable", rows=(("名称", "数量"), ("苹果", "2")))),
    )
    scs = (Scenario(id="features/shop.feature:3", name="下单", steps=steps),)
    project = "arn:aws:devicefarm:us-west-2:123456789012:project:p"
    return (
        Job(scope_id="web", scope_name="网页", engine="novaact", scenarios=scs, assertion_votes=3, timeout_s=300.0),
        Job(scope_id="aw", scope_name="aw", engine="midscene", scenarios=scs, timeout_s=1500.0,
            target=Target(device="android", ui_kind="web"),
            device_request=DeviceFarmRequest(project_arn=project, os_version="15", billing_method="METERED",
                                             acquire_timeout_s=600.0)),
        Job(scope_id="ia", scope_name="ia", engine="midscene", scenarios=scs, timeout_s=900.0,
            target=Target(device="ios", ui_kind="app",
                          app=AppRef(alias="shop", app_id="com.example.Shop", bucket="gherkai-apps",
                                     key="apps/ab12/shop.ipa", sha256="ab" * 32)),
            device_request=DeviceFarmRequest(project_arn=project, device_arn="arn:aws:devicefarm:us-west-2::device:D1",
                                             billing_method="UNMETERED", acquire_timeout_s=900.0)),
    )


def _advancer_input(**over) -> handoff.AdvancerInput:
    base = dict(jobs=_jobs(), steps_dir="/work/project/features/steps", max_concurrency=4, per_job_tail_s=72.0,
                expose_local="http://localhost:3000", tunnel_provider="ngrok", region="us-west-2", profile="dev",
                report_dir="/work/project/gherkai-reports")
    return handoff.AdvancerInput(**{**base, **over})


def _watch_input() -> handoff.WatchInput:
    return handoff.WatchInput(local_origin="http://localhost:3000", tunnel_provider="ngrok",
                              closes_at="2026-11-20T09:35:00+00:00", runs_table="gherkai-runs", region=None,
                              profile="dev")


def _in_thread(fn, *args, timeout_s: float = 10.0):
    """在守护线程里调用 `fn`，限时等它返回：被测函数阻塞时用例以失败结束，而不是挂住整个测试进程。"""
    out: dict = {}

    def target() -> None:
        try:
            out["value"] = fn(*args)
        except BaseException as e:   # 原样交回主线程
            out["error"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout_s)
    assert not t.is_alive(), f"{getattr(fn, '__name__', fn)} 在 {timeout_s} 秒内没有返回"
    if "error" in out:
        raise out["error"]
    return out["value"]


@pytest.fixture
def pipe():
    """一条真实管道 (读端, 写端)；用例自己关掉的一端不再关。"""
    r, w = os.pipe()
    fds = {"r": r, "w": w}
    yield fds
    for fd in fds.values():
        if fd is not None:
            handoff.close_quietly(fd)


def _close(fds: dict, end: str) -> None:
    os.close(fds[end])
    fds[end] = None


# ── 消息的往返 ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("msg, encode, decode", [
    (_advancer_input(), handoff.encode_advancer_input, handoff.decode_advancer_input),
    (_advancer_input(steps_dir=None, expose_local=None, region=None, profile=None),
     handoff.encode_advancer_input, handoff.decode_advancer_input),
    (handoff.AdvancerReport(run_id="20261120T080000Z-a3f9c1", public_url="https://abc.ngrok-free.app", exit_code=0,
                            message=None), handoff.encode_advancer_report, handoff.decode_advancer_report),
    (handoff.AdvancerReport(run_id=None, public_url=None, exit_code=2, message="隧道没有建成：第一行\n第二行。"),
     handoff.encode_advancer_report, handoff.decode_advancer_report),
    (_watch_input(), handoff.encode_watch_input, handoff.decode_watch_input),
    (handoff.WatchReport(public_url="https://abc.ngrok-free.app", warmup_url=_WARMUP),
     handoff.encode_watch_report, handoff.decode_watch_report),
    (handoff.WatchReport(public_url=None, warmup_url=None, exit_code=2, message="隧道没有建成：20 秒内没有连上隧道服务。"),
     handoff.encode_watch_report, handoff.decode_watch_report),
], ids=["advancer-input", "advancer-input-nulls", "advancer-report-ok", "advancer-report-failed", "watch-input",
        "watch-report-ok", "watch-report-failed"])
def test_messages_round_trip_as_exactly_one_line(msg, encode, decode):
    line = encode(msg)
    assert isinstance(line, bytes) and line.endswith(b"\n") and line.count(b"\n") == 1  # 正文里的换行已转义
    assert decode(line) == msg
    assert decode(line.rstrip(b"\n")) == msg


def test_advancer_input_round_trip_keeps_device_requests_and_app_locations():
    back = handoff.decode_advancer_input(handoff.encode_advancer_input(_advancer_input()))
    assert isinstance(back.jobs, tuple)
    by = {j.scope_id: j for j in back.jobs}
    assert by["aw"].device_request == DeviceFarmRequest(
        project_arn="arn:aws:devicefarm:us-west-2:123456789012:project:p", os_version="15", billing_method="METERED",
        acquire_timeout_s=600.0)
    assert by["ia"].target.app == AppRef(alias="shop", app_id="com.example.Shop", bucket="gherkai-apps",
                                         key="apps/ab12/shop.ipa", sha256="ab" * 32)
    assert by["ia"].device_request.device_arn == "arn:aws:devicefarm:us-west-2::device:D1"
    assert by["web"].device_request is None and by["web"].assertion_votes == 3


def test_watch_report_and_channel_reprs_leave_out_the_warmup_url(pipe):
    report = handoff.WatchReport(public_url="https://abc.ngrok-free.app", warmup_url=_WARMUP)
    assert _SECRET not in repr(report) and "abc.ngrok-free.app" in repr(report)
    ch = handoff.WatchChannel("https://abc.ngrok-free.app", _WARMUP, stdin_fd=pipe["w"], report_fd=pipe["r"])
    assert _SECRET not in repr(ch) and "abc.ngrok-free.app" in repr(ch)
    assert ch.warmup_url == _WARMUP


def _without_app_location(line: bytes) -> bytes:
    d = json.loads(line)
    for k in ("bucket", "key", "sha256"):
        d["jobs"][2]["target"]["app"].pop(k)
    return json.dumps(d).encode()


@pytest.mark.parametrize("make_line, decode", [
    (lambda: b"not json\n", handoff.decode_watch_input),
    (lambda: b"[1, 2]\n", handoff.decode_watch_input),
    (lambda: b'{"run_id": "\x80"}\n', handoff.decode_advancer_report),
    (lambda: json.dumps({k: v for k, v in json.loads(handoff.encode_watch_input(_watch_input())).items()
                         if k != "runs_table"}).encode(), handoff.decode_watch_input),
    (lambda: json.dumps({**json.loads(handoff.encode_watch_input(_watch_input())), "ttl": 60}).encode(),
     handoff.decode_watch_input),
    (lambda: handoff.encode_watch_report(handoff.WatchReport("https://x", "https://x/w")), handoff.decode_advancer_report),
    (lambda: _without_app_location(handoff.encode_advancer_input(_advancer_input())), handoff.decode_advancer_input),
], ids=["not-json", "not-object", "not-utf8", "missing-key", "extra-key", "other-message", "plan-form-job"])
def test_decoders_reject_malformed_lines_with_value_error(make_line, decode):
    with pytest.raises(ValueError):
        decode(make_line())


# ── read_line ───────────────────────────────────────────────────────────────


def test_read_line_returns_one_line_with_its_newline(pipe):
    os.write(pipe["w"], b'{"a":1}\n')
    assert handoff.read_line(pipe["r"]) == b'{"a":1}\n'
    os.write(pipe["w"], b"\n")
    assert handoff.read_line(pipe["r"]) == b"\n"   # 空行与文件结束可以分开


def test_read_line_returns_at_the_newline_without_waiting_for_eof(pipe):
    """一行大于管道缓冲：写端在另一个线程里分多次写满，写完不关；读端读到换行即返回。"""
    line = b"x" * _BIG + b"\n"
    writer = threading.Thread(target=handoff.write_all, args=(pipe["w"], line))
    writer.start()
    assert _in_thread(handoff.read_line, pipe["r"]) == line
    writer.join(10)


def test_read_line_returns_empty_bytes_on_eof_before_the_newline(pipe):
    os.write(pipe["w"], b'{"partial":')
    _close(pipe, "w")
    assert handoff.read_line(pipe["r"]) == b""


def test_read_line_returns_empty_bytes_on_immediate_eof(pipe):
    _close(pipe, "w")
    assert handoff.read_line(pipe["r"]) == b""


def test_read_line_rejects_bytes_after_the_newline(pipe):
    os.write(pipe["w"], b"first\nsecond")   # 一次写入，读端一次读到两段
    with pytest.raises(ValueError):
        handoff.read_line(pipe["r"])


def test_read_line_leaves_a_later_line_for_the_next_read(pipe):
    """云端守护进程的标准输入：先交输入、收到回报之后才交 run 的标识，两行各读一次。"""
    os.write(pipe["w"], b"input\n")
    assert handoff.read_line(pipe["r"]) == b"input\n"
    os.write(pipe["w"], b"20261120T080000Z-a3f9c1\n")
    assert handoff.read_line(pipe["r"]) == b"20261120T080000Z-a3f9c1\n"


# ── peer_closed ─────────────────────────────────────────────────────────────


def test_peer_closed_is_false_while_the_write_end_is_open_and_true_after_it_closes(pipe):
    assert handoff.peer_closed(pipe["r"]) is False
    assert os.get_blocking(pipe["r"]) is True
    _close(pipe, "w")
    assert handoff.peer_closed(pipe["r"]) is True
    assert os.get_blocking(pipe["r"]) is True


def test_peer_closed_reports_eof_once_the_process_holding_the_write_end_is_killed(pipe):
    """写端只在另一个进程里（启动方交出之后关掉自己那一份）：它活着时为假，被 SIGKILL 之后为真。"""
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], pass_fds=(pipe["w"],),
                              stdin=subprocess.DEVNULL)
    try:
        _close(pipe, "w")
        assert handoff.peer_closed(pipe["r"]) is False
        holder.kill()
        holder.wait(timeout=10)
        assert handoff.peer_closed(pipe["r"]) is True
        assert os.get_blocking(pipe["r"]) is True
    finally:
        holder.kill()
        holder.wait(timeout=10)


def test_peer_closed_rejects_unexpected_data_and_still_restores_blocking_mode(pipe):
    os.write(pipe["w"], b"x")
    with pytest.raises(ValueError):
        handoff.peer_closed(pipe["r"])
    assert os.get_blocking(pipe["r"]) is True


# ── wait_readable ───────────────────────────────────────────────────────────


def test_wait_readable_is_true_on_data_and_leaves_the_data_unread(pipe):
    os.write(pipe["w"], b"20261120T080000Z-a3f9c1\n")
    assert handoff.wait_readable(pipe["r"], 5.0) is True
    assert handoff.read_line(pipe["r"]) == b"20261120T080000Z-a3f9c1\n"


def test_wait_readable_is_true_on_eof(pipe):
    _close(pipe, "w")
    assert handoff.wait_readable(pipe["r"], 5.0) is True
    assert handoff.read_line(pipe["r"]) == b""


def test_wait_readable_is_false_after_the_timeout(pipe):
    t0 = time.monotonic()
    assert handoff.wait_readable(pipe["r"], 0.2) is False
    assert 0.15 <= time.monotonic() - t0 < 5.0


def test_wait_readable_wakes_when_data_arrives_during_the_wait(pipe):
    timer = threading.Timer(0.1, os.write, args=(pipe["w"], b"late\n"))
    timer.start()
    try:
        t0 = time.monotonic()
        assert handoff.wait_readable(pipe["r"], 30.0) is True
        assert time.monotonic() - t0 < 10.0
    finally:
        timer.join(10)


@pytest.mark.parametrize("timeout_s", [0.0, -5.0])
def test_wait_readable_checks_once_when_the_timeout_is_not_positive(pipe, timeout_s):
    t0 = time.monotonic()
    assert handoff.wait_readable(pipe["r"], timeout_s) is False
    assert time.monotonic() - t0 < 1.0
    os.write(pipe["w"], b"x\n")
    assert handoff.wait_readable(pipe["r"], timeout_s) is True


# ── write_all ───────────────────────────────────────────────────────────────


def test_write_all_delivers_data_larger_than_the_pipe_buffer(pipe):
    data = os.urandom(_BIG)
    got = bytearray()

    def reader() -> None:
        while chunk := os.read(pipe["r"], 65536):
            got.extend(chunk)

    t = threading.Thread(target=reader)
    t.start()
    try:
        assert handoff.write_all(pipe["w"], data) is True
    finally:
        _close(pipe, "w")
        t.join(10)
    assert not t.is_alive() and bytes(got) == data


def test_write_all_returns_false_when_the_read_end_is_already_closed(pipe):
    _close(pipe, "r")
    assert handoff.write_all(pipe["w"], b"20261120T080000Z-a3f9c1\n") is False
    os.fstat(pipe["w"])   # 描述符没有被关闭


def test_write_all_returns_false_when_the_reader_goes_away_midway(pipe):
    """读端读到第一个字节之后关闭：写端此时阻塞在写满的管道上，随后得到 EPIPE，返回假、不抛。"""
    r = pipe["r"]
    pipe["r"] = None

    def reader() -> None:
        os.read(r, 1)
        os.close(r)

    t = threading.Thread(target=reader)
    t.start()
    assert _in_thread(handoff.write_all, pipe["w"], b"x" * _BIG) is False
    t.join(10)
    os.fstat(pipe["w"])


# ── close_quietly、open_log、watch_log_path ────────────────────────────────


def test_close_quietly_closes_and_ignores_an_already_closed_descriptor():
    r, w = os.pipe()
    os.close(r)
    handoff.close_quietly(w)
    with pytest.raises(OSError):
        os.fstat(w)
    handoff.close_quietly(w)   # 已经关闭：不抛


def test_open_log_appends_and_creates_with_mode_0644(tmp_path):
    log = tmp_path / "reconcile.log"
    log.write_bytes(b"earlier\n")
    fd = handoff.open_log(log)
    try:
        os.write(fd, b"later\n")
    finally:
        os.close(fd)
    assert log.read_bytes() == b"earlier\nlater\n"

    fresh = tmp_path / "fresh.log"
    os.close(handoff.open_log(fresh))
    umask = os.umask(0)
    os.umask(umask)
    assert stat.S_IMODE(fresh.stat().st_mode) == 0o644 & ~umask


def test_open_log_raises_os_error_when_the_directory_is_missing(tmp_path):
    with pytest.raises(OSError):
        handoff.open_log(tmp_path / "no-such-run" / "reconcile.log")


def test_watch_log_path_is_in_the_system_temp_dir():
    p = handoff.watch_log_path("20261120T080000Z-a3f9c1")
    assert p == Path(tempfile.gettempdir()) / "gherkai-tunnel-watch-20261120T080000Z-a3f9c1.log"


# ── redirect_output（在子进程里执行）──────────────────────────────────────


_REDIRECT_CHILD = r'''
import os, subprocess, sys
from pathlib import Path
from gherkai_runtime import handoff

log_path, release_fd = Path(sys.argv[1]), int(sys.argv[2])
print("before-stdout")                       # 不显式冲刷：标准输出接在管道上，按块缓冲
print("before-stderr", file=sys.stderr)
log_fd = handoff.open_log(log_path)
handoff.redirect_output(log_fd)
print("after-stdout", flush=True)
print("after-stderr", file=sys.stderr, flush=True)
try:
    os.fstat(log_fd)
    print("log-fd-still-open", flush=True)
except OSError:
    print("log-fd-closed", flush=True)
print("stdin-read:" + repr(os.read(0, 1)), flush=True)   # 改接空设备之后立即读到文件结束；没改接时会一直等
subprocess.run([sys.executable, "-c", "print('grandchild-stdout')"], check=True)
os.read(release_fd, 1)                       # 等父进程核对完捕获管道再继续
print("released", flush=True)
'''


def _read_until_eof(fds: list[int], timeout_s: float) -> list[bytes]:
    bufs = {fd: bytearray() for fd in fds}
    pending = set(fds)
    deadline = time.monotonic() + timeout_s
    while pending:
        left = deadline - time.monotonic()
        if left <= 0:
            pytest.fail(f"{timeout_s} 秒内捕获管道没有读到文件结束；已读到 {[bytes(bufs[fd]) for fd in fds]}")
        ready, _, _ = select.select(sorted(pending), [], [], left)
        for fd in ready:
            chunk = os.read(fd, 65536)
            if chunk:
                bufs[fd] += chunk
            else:
                pending.discard(fd)
    return [bytes(bufs[fd]) for fd in fds]


def test_redirect_output_moves_later_output_to_the_log_and_releases_the_capture_pipes(tmp_path):
    """子进程改接之后：父进程捕获它标准输出与错误的管道随即读到文件结束（子进程这时还在），改接之前缓冲的输出留在原处，
    改接之后的输出、它再启动的子进程的输出都在日志里；标准输入改接空设备。"""
    log = tmp_path / "reconcile.log"
    release_r, release_w = os.pipe()
    env = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}
    proc = subprocess.Popen([sys.executable, "-c", _REDIRECT_CHILD, str(log), str(release_r)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            pass_fds=(release_r,), cwd=tmp_path, env=env)
    os.close(release_r)
    try:
        out, err = _read_until_eof([proc.stdout.fileno(), proc.stderr.fileno()], timeout_s=30.0)
        assert proc.poll() is None, "捕获管道读到文件结束时子进程应当还在"
    finally:
        os.close(release_w)   # 放行：子进程读到文件结束同样继续
        try:
            rc = proc.wait(timeout=30)
        finally:
            proc.kill()
            proc.wait()
            proc.stdin.close()
            proc.stdout.close()
            proc.stderr.close()
    assert rc == 0, err.decode()
    assert b"before-stdout" in out and b"after" not in out
    assert b"before-stderr" in err and b"after" not in err
    text = log.read_text(encoding="utf-8")
    for want in ("after-stdout", "after-stderr", "log-fd-closed", "stdin-read:b''", "grandchild-stdout", "released"):
        assert want in text
    assert "before-" not in text


# ── WatchChannel ────────────────────────────────────────────────────────────


@pytest.fixture
def channel_pipes():
    """守护进程的两条管道：标准输入 (读端在守护进程, 写端在 submit)、回报 (读端在 submit, 写端在守护进程)。"""
    stdin_r, stdin_w = os.pipe()
    report_r, report_w = os.pipe()
    fds = {"stdin_r": stdin_r, "stdin_w": stdin_w, "report_r": report_r, "report_w": report_w}
    yield fds
    for name in ("stdin_r", "report_w"):   # 守护进程一侧；submit 一侧由通道关闭
        if fds[name] is not None:
            handoff.close_quietly(fds[name])


def _channel(fds: dict) -> handoff.WatchChannel:
    return handoff.WatchChannel("https://abc.ngrok-free.app", _WARMUP, stdin_fd=fds["stdin_w"], report_fd=fds["report_r"])


def test_daemon_gone_is_false_while_the_report_write_end_is_open_and_true_after(channel_pipes):
    ch = _channel(channel_pipes)
    try:
        assert ch.daemon_gone() is False
        _close(channel_pipes, "report_w")
        assert ch.daemon_gone() is True
    finally:
        ch.release()


def test_hand_over_delivers_one_line_and_returns_false_once_the_daemon_side_is_closed(channel_pipes):
    ch = _channel(channel_pipes)
    try:
        assert ch.hand_over("20261120T080000Z-a3f9c1") is True
        assert handoff.read_line(channel_pipes["stdin_r"]) == b"20261120T080000Z-a3f9c1\n"
        _close(channel_pipes, "stdin_r")
        assert ch.hand_over("20261120T080000Z-a3f9c1") is False
    finally:
        ch.release()


@pytest.mark.parametrize("run_id", ["", "a\nb"])
def test_hand_over_rejects_ids_that_would_break_the_line(channel_pipes, run_id):
    ch = _channel(channel_pipes)
    try:
        with pytest.raises(ValueError):
            ch.hand_over(run_id)
    finally:
        ch.release()


def test_release_closes_both_ends_once_and_is_idempotent(channel_pipes):
    ch = _channel(channel_pipes)
    ch.release()
    # 守护进程一侧看到的结果：标准输入读到文件结束，往回报管道写得到 EPIPE
    assert handoff.read_line(channel_pipes["stdin_r"]) == b""
    assert handoff.write_all(channel_pipes["report_w"], b"x") is False
    # 再建一条管道，多半复用刚释放的两个号；再次 release 不能把它关掉
    r, w = os.pipe()
    try:
        ch.release()
        assert handoff.write_all(w, b"still-open\n") is True
        assert handoff.read_line(r) == b"still-open\n"
    finally:
        os.close(r)
        os.close(w)
    with pytest.raises(ValueError):
        ch.daemon_gone()
    with pytest.raises(ValueError):
        ch.hand_over("20261120T080000Z-a3f9c1")
