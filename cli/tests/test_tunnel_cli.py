"""--expose-local 与两种 submit 的交接在命令行一侧的测试（ADR 0035 决策 1 到 3）。

证据边界：隧道服务是登记进 `tunnel.PROVIDERS` 的假实现，只模仿口子的外部表面（前置检查的用例改为对 `tunnel._import_sdk` 打桩、走
真实的 `NgrokTunnel`）；云端存储是记录调用的假句柄，不连 AWS、不联网。submit 与后台进程之间用真实的管道与线程
（`_inline_children`）：两端都是生产代码，文件结束、EPIPE、非阻塞读与 Ctrl-C 的 SIGINT 都是真实的。SDK 与 ngrok 服务的真实行为、
跨进程的会话不在这些用例的证据之内（ADR 0035「实测项」）；进程入口的读输入与信号处置、submit 写出 run 标识之后到达的 Ctrl-C 另有
用例真的启动子进程（不起隧道）。
"""
from __future__ import annotations

import atexit
import os
import signal
import sqlite3
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


def test_run_record_write_failure_exits_2_with_one_sentence(tmp_path, monkeypatch, capsys, tunnel_service):
    """前台 run 建 run 写记录失败（报告目录的位置被一个文件占着）：一句说明、退出码 2、不打回溯，不开始执行（ADR 0030 决定七）；
    与本机后台推进进程是同一句。"""
    occupied = tmp_path / "reports"
    occupied.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("写记录失败时不该开始执行"))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(occupied), "--expose-local", ORIGIN])
    assert rc == 2
    cap = capsys.readouterr()
    assert f"在报告目录 {occupied} 里写这个 run 的记录失败：" in cap.err
    assert "还没有开始执行；请检查这个目录的读写权限与所在磁盘的剩余空间后重新执行。" in cap.err
    assert "Traceback" not in cap.err and cap.out == ""


def test_run_event_store_failure_after_the_record_exits_2_and_leaves_the_run_pending(tmp_path, monkeypatch, capsys):
    """前台 run 的记录已写下、建事件库失败（sqlite3.Error 不是 OSError）：说明记录已写下、停在 pending，退出码 2、不打回溯。"""
    from gherkai_core.adapters import event_log

    def broken_event_log(path):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(event_log, "SqliteEventLog", broken_event_log)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("准备执行用的文件失败时不该开始执行"))
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    assert rc == 2
    (run_dir,) = _run_dirs(reports)
    err = capsys.readouterr().err
    assert (f"run {run_dir.name} 的记录已经写下，但在报告目录 {reports} 里准备执行用的文件失败：unable to open database file。"
            "还没有开始执行，这个 run 在记录里停在 pending。") in err
    assert "Traceback" not in err
    assert LocalRunStore(reports).load_run_state(run_dir.name).status == Status.PENDING


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
        pytest.fail(f"隧道的前置缺失时不该{what}")
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
    # 推进用的就是写进记录的那一份，且是内存里的同一个对象（不读回）；运行态带后台执行标记（status --wait 据此认它可接力）
    ((_advancer, advanced_meta),) = advanced
    assert advanced_meta == meta
    ((created_meta,), (assembled_meta,)) = handed["create_run"], handed["assemble"]
    assert created_meta is assembled_meta and assembled_meta is advanced_meta
    assert LocalRunStore(reports).is_detached(run_id)
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
    """后台推进进程在回报之前崩溃（这里是生成运行定义时）：提交进程读到回报管道的文件结束，说明它退出了、可能已经建立 run、可以用
    list-runs 查看，退出码 2；后台推进进程的 finally 照样关闭会话。"""
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(m, "_build_run_meta", boom)
    inline_children.expect_crash_before_report()
    reports = tmp_path / "reports"
    rc = m.main(_local_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert ("后台推进进程在给出提交结果之前退出了，提交没有完成；它退出之前如果有输出，原因在上面。它退出之前可能已经建立了这个 run，"
            f"可以用 gherkai list-runs --report-dir {reports} 查看。处理好原因之后请重新提交。") in cap.err
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
                      "还没有开始执行，这个 run 在记录里停在 pending。"),
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
    if arrange in (_break_assembly, _break_reconcile_log):
        assert LocalRunStore(reports).load_run_state(FIXED_RUN_ID).status == Status.PENDING


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


@pytest.mark.parametrize("signum", [signal.SIGHUP, signal.SIGTERM], ids=["SIGHUP", "SIGTERM"])
@pytest.mark.parametrize("entry", ["_reconcile", "_tunnel_watch"])
def test_background_entry_is_ended_by_the_signal_even_when_the_parent_ignores_it(entry, signum):
    """启动方把这个信号设成了忽略（如经 nohup 启动的 submit 之于 SIGHUP），后台进程继承了它：入口进门即恢复成缺省处置，对它发这个
    信号即结束它。真实进程、真实信号：父进程先设忽略再启动，标准输入保持打开、不交输入（后台进程停在读输入，不起隧道）；入口恢复处置
    之前到达的信号会被忽略，所以每 0.2 秒发一次，直到它退出或到 10 秒。"""
    report_r, report_w = os.pipe()
    stdin_r, stdin_w = os.pipe()
    env = {k: v for k, v in os.environ.items() if k != "NGROK_AUTHTOKEN"}
    previous = signal.signal(signum, signal.SIG_IGN)
    try:
        proc = subprocess.Popen([sys.executable, "-P", "-m", "gherkai_cli", entry, "--report-fd", str(report_w)],
                                stdin=stdin_r, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(report_w,),
                                start_new_session=True, env=env)
    finally:
        signal.signal(signum, previous)
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
    回报公网地址与预热地址，submit 没有交出 run 标识就关闭了标准输入时关闭会话、以 0 返回。入口不装信号处理器：SIGTERM、SIGHUP 仍是
    缺省处置（ADR 0035 决策 3）。"""
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
    assert signal.getsignal(signal.SIGTERM) == signal.SIG_DFL and signal.getsignal(signal.SIGHUP) == signal.SIG_DFL


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


# ---- 开始写出 run 标识之后到达的 Ctrl-C（ADR 0035 决策 3）----

_SUBMIT_DRIVER = Path(__file__).with_name("_submit_driver.py")


@pytest.mark.parametrize("backend", ["local", "cloud"])
def test_ctrl_c_after_the_run_id_is_written_does_not_change_the_result(backend, tmp_path):
    """真实进程、真实信号：submit 在标准输出写出 run 标识之后立刻收到 SIGINT，结果不变，退出码 0、标准输出恰为 run 标识。提交进程是
    `_submit_driver.py`（后台进程是线程替身，回报经真实管道）：它写出第一行之后停在放行描述符上，用例读到这一行、发出 SIGINT、再放行，
    信号落在标识已经写进管道、`print` 还没有返回的那一刻。"""
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
        assert (tmp_path / "reports" / FIXED_RUN_ID / "run_state.json").exists()


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
