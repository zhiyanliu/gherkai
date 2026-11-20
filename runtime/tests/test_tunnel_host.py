"""tunnel_host 单测（ADR 0035 决策 3）：起隧道并映射运行定义、云端守护进程的轮询与主体。

证据边界：隧道服务是假的（登记进 `tunnel.PROVIDERS` 的假 provider，或注入假 SDK 的 `NgrokTunnel`），云端存储与墙钟是注入的；
守护进程主体与 `submit` 一侧之间用真实的 `os.pipe` 与线程，`submit` 一侧用生产代码的 `handoff.WatchChannel`，管道的文件结束、EPIPE
与非阻塞读都是真实的。一次读一直不返回时守护进程在到点时刻结束，用真实线程与真实时间（读阻塞在 Event 上）；被放弃的读不妨碍进程
退出，用真实进程。SDK 与 ngrok 服务的真实行为、真实云端的读取不在这些用例的证据之内（ADR 0035「实测项」）。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.model import Job, RunState, Scenario, Status, Step
from gherkai_core.serialize import instant_to_iso
from gherkai_runtime import compose, handoff, tunnel_host
from gherkai_runtime import tunnel as gtunnel

ORIGIN = "http://localhost:3000"
PUBLIC = "https://t.ngrok-free.app"
TOKEN = "a" * 32
WARMUP = gtunnel.warmup_url_for(PUBLIC, TOKEN)
# 远在过去的时刻：用例若读了真实的墙钟，就会当成早已过了到点时刻
T0 = datetime(2001, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
CLOSES_AT = T0 + timedelta(hours=1)
CLOSES_AT_ISO = instant_to_iso(CLOSES_AT)


def _job(scope_id: str, timeout_s: float = 300.0) -> Job:
    return Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", timeout_s=timeout_s,
               scenarios=(Scenario(id=f"{scope_id}:1", name="sc",
                                   steps=(Step(0, "Given", f'"{ORIGIN}/a"'),)),))


def _state(status: Status) -> RunState:
    return RunState(run_id="r1", status=status, jobs={})


class _FakeProvider:
    """登记进 `tunnel.PROVIDERS` 的假隧道服务：记下 start 的参数与关闭会话的调用。"""

    def __init__(self, events: list) -> None:
        self.events = events
        self.starts: list[dict] = []
        self.closes = 0
        self.error: BaseException | None = None

    def check_prerequisites(self) -> None:
        pass

    def start(self, local_origin, *, closes_at, timeout_s=gtunnel.START_TIMEOUT_S):
        self.starts.append({"local_origin": local_origin, "closes_at": closes_at, "timeout_s": timeout_s})
        if self.error is not None:
            raise self.error
        return gtunnel.TunnelInfo(url=PUBLIC, local_origin=local_origin, warmup_url=WARMUP, closer=self._close)

    def _close(self) -> None:
        self.closes += 1
        self.events.append("close")


class _Clock:
    """注入的墙钟：只在注入的 sleep 里前进。"""

    def __init__(self, t: datetime) -> None:
        self.t = t
        self.sleeps: list[float] = []

    def __call__(self) -> datetime:
        return self.t

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.t += timedelta(seconds=s)


class _Script:
    """注入的墙钟：依次给出脚本里的时刻，用完之后停在最后一个。"""

    def __init__(self, *ts: datetime) -> None:
        self.ts = list(ts)

    def __call__(self) -> datetime:
        return self.ts.pop(0) if len(self.ts) > 1 else self.ts[0]


class _Store:
    """假的 RunStore：依次给出序列里的运行态（或抛出序列里的异常），用完之后重复最后一个。"""

    def __init__(self, seq) -> None:
        self.seq = list(seq)
        self.reads = 0

    def load_run_state(self, run_id):
        assert run_id == "r1"
        self.reads += 1
        got = self.seq.pop(0) if len(self.seq) > 1 else self.seq[0]
        if isinstance(got, BaseException):
            raise got
        return got


def _watch(store, clock, notes, **kw):
    return tunnel_host.watch_cloud_run(
        "r1", runs_table="tbl", region="us-east-1", profile=None, closes_at=CLOSES_AT, on_note=notes.append,
        clock=clock, sleep=clock.sleep, poll_interval_s=5.0, open_store=lambda: store, **kw)


# ---- map_jobs_to_tunnel 与 start_tunnel_for_jobs：映射运行定义、恒注入请求头（决策 1、2、4）----

def test_map_jobs_to_tunnel_maps_text_and_gives_a_fresh_header_dict():
    jobs = [_job("s1")]
    mapped, headers = tunnel_host.map_jobs_to_tunnel(jobs, local_origin=ORIGIN, public_url=PUBLIC)
    assert isinstance(mapped, tuple)
    assert mapped[0].scenarios[0].steps[0].text == f'"{PUBLIC}/a"'
    assert jobs[0].scenarios[0].steps[0].text == f'"{ORIGIN}/a"'  # 原 jobs 不动
    assert headers == {"ngrok-skip-browser-warning": "1"}
    headers["x"] = "y"  # 调用方改返回的 dict 不影响下一次
    assert tunnel_host.map_jobs_to_tunnel(jobs, local_origin=ORIGIN, public_url=PUBLIC)[1] == {
        "ngrok-skip-browser-warning": "1"}


def test_map_jobs_to_tunnel_rejects_a_value_that_is_not_an_origin():
    with pytest.raises(gtunnel.TunnelError, match="不是 origin"):
        tunnel_host.map_jobs_to_tunnel([_job("s1")], local_origin=f"{ORIGIN}/app", public_url=PUBLIC)


def test_start_tunnel_for_jobs_starts_with_closes_at_then_maps(world):
    jobs = [_job("s1")]
    setup = tunnel_host.start_tunnel_for_jobs(jobs, local_origin=ORIGIN, provider="fake", closes_at=CLOSES_AT)
    assert world.provider.starts == [{"local_origin": ORIGIN, "closes_at": CLOSES_AT, "timeout_s": gtunnel.START_TIMEOUT_S}]
    assert setup.info.url == PUBLIC and setup.info.warmup_url == WARMUP
    assert setup.extra_http_headers == {"ngrok-skip-browser-warning": "1"}
    assert setup.jobs[0].scenarios[0].steps[0].text == f'"{PUBLIC}/a"'
    assert jobs[0].scenarios[0].steps[0].text == f'"{ORIGIN}/a"'
    assert TOKEN not in repr(setup) and TOKEN not in str(setup)  # 令牌不进 repr（日志与异常里打印对象时不带出来）
    assert world.provider.closes == 0  # 会话交给调用方持有


def test_start_tunnel_for_jobs_passes_timeout_through(world):
    tunnel_host.start_tunnel_for_jobs([_job("s1")], local_origin=ORIGIN, provider="fake", closes_at=CLOSES_AT,
                                      timeout_s=3.0)
    assert world.provider.starts[0]["timeout_s"] == 3.0


def test_start_tunnel_for_jobs_propagates_tunnel_error(world):
    """起不来即 TunnelError 原样冒给调用方（前端归「没开始执行就被拒」、退出码 2），没有会话要关闭。"""
    world.provider.error = gtunnel.TunnelError("隧道没有建成：x（ERR_NGROK_105）。")
    with pytest.raises(gtunnel.TunnelError, match="ERR_NGROK_105"):
        tunnel_host.start_tunnel_for_jobs([_job("s1")], local_origin=ORIGIN, provider="fake", closes_at=CLOSES_AT)
    assert world.provider.closes == 0
    with pytest.raises(gtunnel.TunnelError, match="未知隧道 provider"):
        tunnel_host.start_tunnel_for_jobs([_job("s1")], local_origin=ORIGIN, provider="nope", closes_at=CLOSES_AT)


def test_start_tunnel_for_jobs_closes_the_session_when_mapping_fails(world):
    """隧道建成之后映射失败：调用方拿不到 TunnelInfo，会话在抛出之前关闭。假 provider 不校验取值，映射那一步才拒绝。"""
    with pytest.raises(gtunnel.TunnelError, match="不是 origin"):
        tunnel_host.start_tunnel_for_jobs([_job("s1")], local_origin="localhost:3000", provider="fake",
                                          closes_at=CLOSES_AT)
    assert len(world.provider.starts) == 1 and world.provider.closes == 1


# ---- watch_cloud_run：按墙钟与终态结束，按种类记一句（决策 3「云端 submit」）----

def test_watch_poll_interval_is_five_seconds():
    """守护进程轮询 run 状态的间隔 5 秒：这个取值写在 ADR 0035 决策 3「云端 `submit`」的「轮询」一条里，用户文档与变更记录也引用了它
    （「每 5 秒查一次 run 的状态」）。其余用例只拿这个符号比较，取值变了只有这一条报出；改它时 ADR 与用户文档一并改。"""
    assert tunnel_host.WATCH_POLL_INTERVAL_S == 5.0


def test_watch_returns_run_ended_with_the_terminal_status():
    store, clock, notes = _Store([_state(Status.RUNNING), _state(Status.PENDING), _state(Status.FAILED)]), _Clock(T0), []
    assert _watch(store, clock, notes) == tunnel_host.WatchEnd(reason="run_ended", status=Status.FAILED)
    assert store.reads == 3 and clock.sleeps == [5.0, 5.0] and notes == []


def test_watch_ends_only_when_the_clock_is_strictly_past_closes_at():
    # 恰等于到点时刻：不结束，照常读一次
    store, clock, notes = _Store([_state(Status.RUNNING)]), _Clock(CLOSES_AT), []
    assert _watch(store, clock, notes) == tunnel_host.WatchEnd(reason="past_closes_at", status=None)
    assert store.reads == 1 and clock.sleeps == [0.05]
    # 严格晚于：一次也不读
    store, clock = _Store([_state(Status.PASSED)]), _Clock(CLOSES_AT + timedelta(microseconds=1))
    assert _watch(store, clock, notes).reason == "past_closes_at"
    assert store.reads == 0 and notes == []


def test_watch_sleeps_no_longer_than_the_time_left():
    """每轮睡轮询间隔与余量中较小的一段，下限 0.05 秒：到点之后不多睡满一个间隔。"""
    store, clock, notes = _Store([_state(Status.RUNNING)]), _Clock(CLOSES_AT - timedelta(seconds=12)), []
    assert _watch(store, clock, notes).reason == "past_closes_at"
    assert clock.sleeps == [5.0, 5.0, 2.0, 0.05]


def test_watch_notes_once_per_change_of_kind_not_per_message():
    """读不到、读失败、恢复读到：种类变化时各记一句；两次读失败的说明不同，种类相同，只记第一次。"""
    store = _Store([None, None, RuntimeError("ddb down"), RuntimeError("throttled\nretry later"),
                    _state(Status.RUNNING), _state(Status.RUNNING), None, _state(Status.PASSED)])
    clock, notes = _Clock(T0), []
    assert _watch(store, clock, notes) == tunnel_host.WatchEnd(reason="run_ended", status=Status.PASSED)
    assert notes == ["读不到这个 run，继续轮询", "读 run 的状态失败（ddb down），继续轮询", "恢复读到 run 的状态",
                     "读不到这个 run，继续轮询"]
    assert store.reads == 8


def test_watch_retries_store_assembly_on_the_next_round():
    """装配存储失败按读失败处理：记一句，下一轮再装。"""
    store, clock, notes, opens = _Store([_state(Status.PASSED)]), _Clock(T0), [], []

    def open_store():
        opens.append(1)
        if len(opens) == 1:
            raise RuntimeError("no region")
        return store

    end = tunnel_host.watch_cloud_run(
        "r1", runs_table="tbl", region=None, profile=None, closes_at=CLOSES_AT, on_note=notes.append,
        clock=clock, sleep=clock.sleep, poll_interval_s=5.0, open_store=open_store)
    assert end == tunnel_host.WatchEnd(reason="run_ended", status=Status.PASSED)
    assert len(opens) == 2 and store.reads == 1
    assert notes == ["读 run 的状态失败（no region），继续轮询"]


def test_watch_reads_only_the_injected_clock(monkeypatch):
    """全程只读注入的墙钟：compose.now 被调用即失败；T0 远在过去，读了真实时钟会当成已过到点时刻。"""
    monkeypatch.setattr(compose, "now", lambda: pytest.fail("读了注入之外的墙钟"))
    store, clock, notes = _Store([_state(Status.RUNNING), _state(Status.PASSED)]), _Clock(T0), []
    assert _watch(store, clock, notes).reason == "run_ended"


def test_watch_takes_the_clock_and_sleep_at_call_time_when_not_injected(monkeypatch):
    """不注入时在调用那一刻取 compose.now 与 time.sleep：对它们打桩的上层测试照样管得到守护进程。"""
    clock = _Clock(T0)
    monkeypatch.setattr(compose, "now", clock)
    monkeypatch.setattr(time, "sleep", clock.sleep)
    store, notes = _Store([_state(Status.RUNNING), _state(Status.PASSED)]), []
    end = tunnel_host.watch_cloud_run("r1", runs_table="tbl", region=None, profile=None, closes_at=CLOSES_AT,
                                      on_note=notes.append, open_store=lambda: store)
    assert end.reason == "run_ended" and clock.sleeps == [tunnel_host.WATCH_POLL_INTERVAL_S]


def test_watch_does_not_take_an_interrupt_for_a_read_failure():
    """只有 Exception 算读失败：KeyboardInterrupt、SystemExit 照常抛出，不记一句、不继续轮询。"""
    for exc in (KeyboardInterrupt(), SystemExit(143)):
        store, clock, notes = _Store([_state(Status.RUNNING), exc]), _Clock(T0), []
        with pytest.raises(type(exc)):
            _watch(store, clock, notes)
        assert store.reads == 2 and notes == []


def test_watch_default_store_uses_the_handed_over_table_region_and_profile(monkeypatch):
    """缺省的存储按交来的 runs 表、region、profile 装配，不再解析（守护进程不读配置文件）。"""
    made = []

    class _Table:
        def get_item(self, **kw):
            return {}

    def make_table(table, *, region, profile):
        made.append((table, region, profile))
        return _Table()

    monkeypatch.setattr(compose, "_make_ddb_table", make_table)
    monkeypatch.setattr(compose, "resolve_aws_identity", lambda *a, **kw: pytest.fail("守护进程不应再解析身份"))
    clock, notes = _Script(T0, CLOSES_AT + timedelta(seconds=1)), []
    end = tunnel_host.watch_cloud_run("r1", runs_table="tbl", region="eu-west-1", profile="dev", closes_at=CLOSES_AT,
                                      on_note=notes.append, clock=clock, sleep=lambda s: None)
    assert made == [("tbl", "eu-west-1", "dev")]
    assert end.reason == "past_closes_at" and notes == ["读不到这个 run，继续轮询"]


# ---- watch_cloud_run：一次读不返回时，到点时刻照样是上限（决策 3「云端 submit」）----

class _BlockedStore:
    """读 run 状态时阻塞在一个 Event 上的假 RunStore（等待时释放解释器锁，同网络 IO）；放开之后答 `then`。"""

    def __init__(self, gate: threading.Event, then=None) -> None:
        self.gate = gate
        self.then = then if then is not None else _state(Status.PASSED)
        self.reads = 0
        self.entered = threading.Event()

    def load_run_state(self, run_id):
        self.reads += 1
        self.entered.set()
        self.gate.wait(30)
        return self.then


class _ClockedWait:
    """注入的 `wait_read`：不真的等，把注入的墙钟向前拨这一段、记下段长，再看这次读是否已经回来；`release_at` 给出第几段之后放开读。"""

    def __init__(self, clock: _Clock, gate: threading.Event | None = None, release_at: int | None = None) -> None:
        self.clock, self.gate, self.release_at = clock, gate, release_at
        self.waits: list[float] = []

    def __call__(self, event: threading.Event, timeout_s: float) -> bool:
        self.waits.append(timeout_s)
        self.clock.t += timedelta(seconds=timeout_s)
        if self.release_at is not None and len(self.waits) == self.release_at:
            self.gate.set()
            return event.wait(5)
        return event.is_set()


def _real_clock() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.parametrize("blocked", ["read", "assembly"])
def test_watch_returns_at_closes_at_while_one_read_never_returns(blocked):
    """读 run 的状态（或装配存储，如取凭证）一直不返回：守护进程按真实的墙钟在到点时刻返回「已过到点时刻」，不等这次读；期间分段
    等了多次，没有起第二次读。真实线程、真实时间。"""
    gate = threading.Event()
    store = _BlockedStore(gate) if blocked == "read" else _Store([_state(Status.PASSED)])
    opens: list[int] = []

    def open_store():
        opens.append(1)
        if blocked == "assembly":
            gate.wait(30)
        return store

    closes_at = _real_clock() + timedelta(seconds=0.4)
    notes: list[str] = []
    try:
        started = time.monotonic()
        end = tunnel_host.watch_cloud_run("r1", runs_table="tbl", region=None, profile=None, closes_at=closes_at,
                                          on_note=notes.append, clock=_real_clock, poll_interval_s=0.05,
                                          open_store=open_store)
        elapsed = time.monotonic() - started
        assert _real_clock() > closes_at
    finally:
        gate.set()
    assert end == tunnel_host.WatchEnd(reason="past_closes_at", status=None)
    assert 0.3 <= elapsed < 1.5
    assert opens == [1] and store.reads == (1 if blocked == "read" else 0)
    assert notes == []


def test_watch_waits_for_a_pending_read_in_segments_and_rereads_the_clock():
    """一次读没有回来：按轮询间隔与距到点时刻的余量取小分段等待（下限 0.05 秒），每段之后重读墙钟，过了到点时刻即结束；整个期间只有
    这一次读。"""
    gate = threading.Event()
    store, clock, notes = _BlockedStore(gate), _Clock(CLOSES_AT - timedelta(seconds=12)), []
    wait = _ClockedWait(clock)
    try:
        end = _watch(store, clock, notes, wait_read=wait)
    finally:
        gate.set()
    assert end == tunnel_host.WatchEnd(reason="past_closes_at", status=None)
    assert wait.waits == [5.0, 5.0, 2.0, 0.05] and clock.sleeps == []
    assert store.reads == 1 and notes == []


def test_watch_takes_a_read_that_returns_after_some_segments_by_the_usual_rules():
    """读在第二段等待里回来、离到点时刻还远：照常处理它的结果（这里是终态）；没有另起一次读。"""
    gate = threading.Event()
    store, clock, notes = _BlockedStore(gate, then=_state(Status.FAILED)), _Clock(T0), []
    wait = _ClockedWait(clock, gate=gate, release_at=2)
    end = _watch(store, clock, notes, wait_read=wait)
    assert end == tunnel_host.WatchEnd(reason="run_ended", status=Status.FAILED)
    assert wait.waits == [5.0, 5.0] and store.reads == 1 and clock.sleeps == []


def test_watch_abandoned_read_does_not_keep_the_process_alive():
    """真实进程：到点时刻过了、那次读还卡着，watch_cloud_run 返回之后进程照常退出（读的线程是守护线程）。"""
    code = (
        "import threading\n"
        "from datetime import datetime, timedelta, timezone\n"
        "from gherkai_runtime import tunnel_host\n"
        "class Stuck:\n"
        "    def load_run_state(self, run_id):\n"
        "        threading.Event().wait()\n"
        "now = lambda: datetime.now(timezone.utc)\n"
        "end = tunnel_host.watch_cloud_run('r1', runs_table='t', region=None, profile=None,\n"
        "    closes_at=now() + timedelta(seconds=0.2), on_note=print, clock=now, poll_interval_s=0.05,\n"
        "    open_store=Stuck)\n"
        "print(end.reason)\n")
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30,
                          stdin=subprocess.DEVNULL)
    assert (proc.returncode, proc.stdout, proc.stderr) == (0, "past_closes_at\n", "")


# ---- hold_tunnel_for_cloud_run：云端守护进程的主体（真实管道与线程）----

class _World:
    """守护进程主体的外部世界：假隧道服务、按发生次序记下的事件（note、redirect_output、关闭会话）、日志所在的临时目录。"""

    def __init__(self, monkeypatch, tmp_path) -> None:
        self.events: list = []
        self.provider = _FakeProvider(self.events)
        monkeypatch.setitem(gtunnel.PROVIDERS, "fake", lambda: self.provider)
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
        self.redirected: list[os.stat_result] = []
        self.clock = _Clock(T0)
        self.store = _Store([_state(Status.PASSED)])

    @property
    def notes(self) -> list[str]:
        return [e[1] for e in self.events if isinstance(e, tuple)]

    def note(self, s: str) -> None:
        self.events.append(("note", s))

    def redirect(self, fd: int) -> None:
        # 不做 dup2（会破坏测试进程的标准输出）：记下交来的是哪个文件，再像真实实现一样关闭它
        self.events.append("redirect")
        self.redirected.append(os.fstat(fd))
        os.close(fd)

    def kw(self, **over) -> dict:
        kw = dict(note=self.note, redirect_output=self.redirect, clock=self.clock, sleep=self.clock.sleep,
                  poll_interval_s=0.05, open_store=lambda: self.store)
        kw.update(over)
        return kw


@pytest.fixture
def world(monkeypatch, tmp_path) -> _World:
    return _World(monkeypatch, tmp_path)


def _input(provider: str = "fake") -> handoff.WatchInput:
    return handoff.WatchInput(local_origin=ORIGIN, tunnel_provider=provider, closes_at=CLOSES_AT_ISO,
                              runs_table="tbl", region="us-east-1", profile=None)


class _Daemon:
    """在线程里执行守护进程的主体。标准输入与回报管道是真实的 os.pipe，`submit` 一侧的两端（标准输入写端、回报读端）留在测试手里，
    或经 `channel` 交给生产代码的 WatchChannel。主体不关闭交给它的两个描述符，由这里在线程结束之后关闭。"""

    def __init__(self, inp: handoff.WatchInput, **kw) -> None:
        self.in_r, self.in_w = os.pipe()
        self.rep_r, self.rep_w = os.pipe()
        self._owned = {self.in_r, self.in_w, self.rep_r, self.rep_w}
        self._channel: handoff.WatchChannel | None = None
        self.outcome: dict = {}
        self._thread = threading.Thread(target=self._body, args=(inp, kw), daemon=True)

    def _body(self, inp, kw) -> None:
        try:
            self.outcome["rc"] = tunnel_host.hold_tunnel_for_cloud_run(
                inp, report_fd=self.rep_w, input_fd=self.in_r, **kw)
        except BaseException as e:  # noqa: BLE001 —— 交给用例断言
            self.outcome["error"] = e

    def __enter__(self) -> _Daemon:
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        # 用例中途失败时让等待中的主体读到文件结束、退出；线程还活着就不关它的描述符（宁可泄漏，不让号被复用后关错）
        if self._channel is not None:
            self._channel.release()
        self.close(self.in_w)
        self._thread.join(5.0)
        if not self._thread.is_alive():
            for fd in list(self._owned):
                self.close(fd)

    @property
    def alive(self) -> bool:
        return self._thread.is_alive()

    def close(self, fd: int) -> None:
        if fd in self._owned:
            self._owned.discard(fd)
            os.close(fd)

    def report(self) -> handoff.WatchReport:
        assert handoff.wait_readable(self.rep_r, 5.0), "守护进程没有回报"
        line = handoff.read_line(self.rep_r)
        assert line, "回报管道在回报之前关闭"
        return handoff.decode_watch_report(line)

    def channel(self, report: handoff.WatchReport) -> handoff.WatchChannel:
        """把标准输入写端与回报读端交给 submit 一侧的 WatchChannel（它负责关闭这两个描述符）。"""
        self._owned -= {self.in_w, self.rep_r}
        self._channel = handoff.WatchChannel(public_url=report.public_url, warmup_url=report.warmup_url,
                                             stdin_fd=self.in_w, report_fd=self.rep_r)
        return self._channel

    def wait(self, timeout: float = 5.0) -> dict:
        self._thread.join(timeout)
        assert not self._thread.is_alive(), "守护进程主体没有在时限内返回"
        return self.outcome


def test_hold_reports_start_failure_with_exit_code_2_and_never_closes(world, capfd):
    world.provider.error = gtunnel.TunnelError("隧道没有建成：bad token（ERR_NGROK_105）。")
    with _Daemon(_input(), **world.kw()) as d:
        report = d.report()
        outcome = d.wait()
    assert outcome == {"rc": 2}
    assert report == handoff.WatchReport(public_url=None, warmup_url=None, exit_code=2,
                                         message="隧道没有建成：bad token（ERR_NGROK_105）。")
    assert world.provider.starts == [{"local_origin": ORIGIN, "closes_at": CLOSES_AT,
                                      "timeout_s": gtunnel.START_TIMEOUT_S}]
    assert world.provider.closes == 0  # 没有建成的会话不关闭
    assert world.events == []  # 没有 note、没有改接输出
    assert capfd.readouterr() == ("", "")  # 回报之前不往标准输出与标准错误写字


def test_hold_closes_the_session_when_the_report_cannot_be_written(world):
    d = _Daemon(_input(), **world.kw())
    d.close(d.rep_r)  # submit 已不在：回报管道的读端已关闭
    with d:
        outcome = d.wait()
    assert outcome == {"rc": 0}
    assert world.provider.closes == 1 and world.events == ["close"]


def test_hold_keeps_the_report_open_until_the_run_id_then_closes_on_stdin_eof(world, capfd):
    """回报之后、收到 run 标识之前回报写端保持打开（submit 据此判断守护进程还在）；submit 没有交出标识就关闭了标准输入：
    守护进程关闭会话、返回 0，全程没有调用 note 与 redirect_output。"""
    with _Daemon(_input(), **world.kw()) as d:
        report = d.report()
        assert report == handoff.WatchReport(public_url=PUBLIC, warmup_url=WARMUP, exit_code=0, message=None)
        ch = d.channel(report)
        time.sleep(0.2)  # 让主体进入等 run 标识的阶段
        assert d.alive and ch.daemon_gone() is False
        assert world.provider.closes == 0
        ch.release()  # 建 run 失败的出口：关闭标准输入
        outcome = d.wait()
    assert outcome == {"rc": 0}
    assert world.events == ["close"]
    assert capfd.readouterr() == ("", "")


def test_hold_stops_waiting_for_the_run_id_after_closes_at(world):
    """过了到点时刻还没有等到 run 标识：关闭会话、返回 0；标准输入还开着（submit 卡住了）也不再等。两个描述符都留给调用方：
    主体返回之后回报写端仍开着。"""
    clock = _Script(CLOSES_AT - timedelta(seconds=0.2), CLOSES_AT + timedelta(seconds=1))
    with _Daemon(_input(), **world.kw(clock=clock, poll_interval_s=5.0)) as d:
        d.report()
        started = time.monotonic()
        outcome = d.wait()
        assert time.monotonic() - started < 2.0
        assert outcome == {"rc": 0}
        assert world.events == ["close"]
        assert handoff.peer_closed(d.rep_r) is False  # 写端由调用方关闭（进程入口里即进程退出）
        d.close(d.rep_w)
        assert handoff.peer_closed(d.rep_r) is True


def test_hold_polls_to_the_terminal_state_then_closes_and_notes(world, monkeypatch, tmp_path):
    """收到 run 标识之后：先改接输出到这个 run 的日志，再记开头一句；轮询到终态，关闭会话之后才记「隧道已关闭」。全程不启动子进程。"""
    spawned = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: spawned.append(a) or pytest.fail("启动了子进程"))
    monkeypatch.setattr(os, "fork", lambda: spawned.append("fork") or pytest.fail("启动了子进程"))
    monkeypatch.setattr(os, "posix_spawn", lambda *a, **kw: spawned.append(a) or pytest.fail("启动了子进程"))
    world.store = _Store([_state(Status.RUNNING), _state(Status.PASSED)])
    with _Daemon(_input(), **world.kw()) as d:
        ch = d.channel(d.report())
        assert ch.daemon_gone() is False
        assert ch.hand_over("r1") is True
        outcome = d.wait()
    assert outcome == {"rc": 0}
    log = tmp_path / "gherkai-tunnel-watch-r1.log"
    assert len(world.redirected) == 1 and os.path.samestat(world.redirected[0], os.stat(log))
    assert world.events == [
        "redirect",
        ("note", f"隧道已建立，等待 run r1 结束（最晚到 {CLOSES_AT_ISO} 关闭）"),
        "close",
        ("note", "run r1 已结束（passed），隧道已关闭"),
    ]
    assert world.store.reads == 2 and world.clock.sleeps == [0.05]
    assert spawned == []


def test_hold_ends_at_closes_at_while_polling(world):
    world.store = _Store([_state(Status.RUNNING)])
    world.clock.t = CLOSES_AT - timedelta(seconds=0.1)
    with _Daemon(_input(), **world.kw()) as d:
        assert d.channel(d.report()).hand_over("r1")
        outcome = d.wait()
    assert outcome == {"rc": 0}
    assert world.events[-2:] == ["close", ("note", f"已到 {CLOSES_AT_ISO}，隧道已关闭（run r1）")]


def test_hold_takes_a_run_id_already_in_the_pipe_when_past_closes_at(world, tmp_path):
    """过了到点时刻时 run 标识已经在管道里：照常收下、打开日志、记两句，轮询随即按到点时刻结束（不读 run 的状态）。"""
    clock = _Script(CLOSES_AT + timedelta(seconds=1))
    d = _Daemon(_input(), **world.kw(clock=clock))
    assert handoff.write_all(d.in_w, b"r1\n")
    with d:
        d.report()
        outcome = d.wait()
    assert outcome == {"rc": 0}
    assert os.path.samestat(world.redirected[0], os.stat(tmp_path / "gherkai-tunnel-watch-r1.log"))
    assert world.notes[-1] == f"已到 {CLOSES_AT_ISO}，隧道已关闭（run r1）"
    assert world.store.reads == 0


def test_hold_keeps_the_tunnel_when_the_log_cannot_be_opened(world, monkeypatch, tmp_path):
    """日志打不开时改接空设备，照常持有隧道到终态：持有隧道是守护进程唯一的职责，日志只是旁证。"""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "missing"))
    with _Daemon(_input(), **world.kw()) as d:
        assert d.channel(d.report()).hand_over("r1")
        outcome = d.wait()
    assert outcome == {"rc": 0}
    assert os.path.samestat(world.redirected[0], os.stat(os.devnull))
    assert world.notes[-1] == "run r1 已结束（passed），隧道已关闭"
    assert world.provider.closes == 1


def test_hold_closes_the_session_when_polling_is_interrupted(world):
    """轮询被非 Exception 打断（如 KeyboardInterrupt）：异常照常抛出，会话在 finally 里关闭，不记结束的那一句。"""
    world.store = _Store([_state(Status.RUNNING), KeyboardInterrupt()])
    with _Daemon(_input(), **world.kw()) as d:
        assert d.channel(d.report()).hand_over("r1")
        outcome = d.wait()
    assert isinstance(outcome.get("error"), KeyboardInterrupt) and "rc" not in outcome
    assert world.provider.closes == 1
    assert world.events[-1] == "close" and len(world.notes) == 1


def test_hold_rejects_a_run_id_that_is_not_a_single_path_component(world):
    """run 标识要进日志文件名：带路径分隔符的以 ValueError 拒绝，不在临时目录之外建文件；会话照样关闭。"""
    d = _Daemon(_input(), **world.kw())
    assert handoff.write_all(d.in_w, b"../r1\n")
    with d:
        d.report()
        outcome = d.wait()
    assert isinstance(outcome.get("error"), ValueError)
    assert world.events == ["close"]


class _FakeListener:
    def __init__(self, url: str) -> None:
        self._url = url

    def url(self) -> str:
        return self._url


class _FakeSdk:
    """只模仿 SDK 的外部表面：forward 记下参数、返回只有 url() 的监听对象；disconnect 记下调用。"""

    def __init__(self) -> None:
        self.forwards: list[tuple[str, dict]] = []
        self.disconnects: list[str] = []

    def forward(self, addr, **options):
        self.forwards.append((addr, options))
        return _FakeListener(PUBLIC)

    def disconnect(self, url) -> None:
        self.disconnects.append(url)


def test_hold_with_the_ngrok_provider_puts_closes_at_into_the_policy_and_disconnects_once(world, monkeypatch):
    """经真实的 NgrokTunnel（假 SDK）：交给 SDK 的流量策略带交来的到点时刻与回报里预热地址的令牌，会话只关闭一次。"""
    sdk = _FakeSdk()
    monkeypatch.setitem(gtunnel.PROVIDERS, "ngrok", lambda: gtunnel.NgrokTunnel(load_sdk=lambda: sdk))
    with _Daemon(_input(provider="ngrok"), **world.kw()) as d:
        report = d.report()
        ch = d.channel(report)
        assert ch.hand_over("r1")
        outcome = d.wait()
    assert outcome == {"rc": 0}
    assert report.public_url == PUBLIC and report.warmup_url.startswith(f"{PUBLIC}{gtunnel.WARMUP_PATH}?")
    token = report.warmup_url.rsplit("=", 1)[1]
    [(addr, options)] = sdk.forwards
    assert addr == ORIGIN and options["authtoken_from_env"] is True
    assert f"timestamp('{gtunnel.policy_instant(CLOSES_AT)}')" in options["traffic_policy"]
    assert f"'{token}' in req.url.query_params" in options["traffic_policy"]
    assert sdk.disconnects == [PUBLIC]
