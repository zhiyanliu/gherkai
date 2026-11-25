"""隧道宿主编排（ADR 0035 决策 3）：起隧道并映射运行定义，以及云端 `submit` 的隧道守护进程的主体。

**宿主**指持有隧道会话的那个进程（ADR 0035 决策 3 的三种组合：前台 `run` 的 CLI 进程、本机 `submit` 的后台推进进程、云端 `submit`
的隧道守护进程）。会话建在宿主进程里，宿主怎样退出会话都随之消失（ADR 0035 决策 3「寿命」）；正常路径上由宿主自己关闭
（`TunnelInfo.close()`）。本模块住产品本体层（`gherkai_runtime` 知道 run 的生命周期，ADR 0016「演进」节）；入口前端（cli、未来的
WebUI）只负责 argparse、打印与退出码：

- `map_jobs_to_tunnel`：把运行定义里的 origin 换成公网地址，并给出隧道模式恒注入的额外请求头（决策 2、4）。映射与请求头只有这一处：
  前台 `run` 与本机后台推进进程经 `start_tunnel_for_jobs`（起隧道之后映射），云端 `submit` 拿到守护进程回报的地址之后直接调用它。
- `hold_tunnel_for_cloud_run`：云端 `submit` 的隧道守护进程的主体：起隧道、回报、等 run 的标识、轮询到终态或到点时刻
  （`watch_cloud_run`），最后关闭会话。

**术语护栏**（同 ADR 0016「演进」节的命名护栏）：叫 host（宿主，取自 ADR 0035 决策 3 的表头术语），不叫 worker：worker 在 ADR 0024
里专指被启动来执行 scope 的引擎进程，与隧道宿主无关。
"""
from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from gherkai_core.model import TERMINAL_STATUSES, Job, Status
from gherkai_core.serialize import instant_from_iso

from gherkai_runtime import compose, handoff
from gherkai_runtime import tunnel as _tunnel

if TYPE_CHECKING:
    from gherkai_core.model import RunState
    from gherkai_core.ports import RunStore

# 隧道模式恒注入的额外请求头（ADR 0035 决策 4）：ngrok 免费层对浏览器返回 interstitial 警告页（对自动化
# 致命），带任意值的该头即绕过；付费户带着无害（服务端忽略）→ 不做付费检测、隧道模式下恒注入。
TUNNEL_EXTRA_HTTP_HEADERS = {"ngrok-skip-browser-warning": "1"}

# 云端守护进程轮询 run 状态的间隔（秒，ADR 0035 决策 3「云端 `submit`」里「轮询」一条）。等 run 的标识与等一次读的结果时也按它
# 分段等待、每段之后重读墙钟：等待的时限按单调时钟计，系统休眠的时段可能不计入，分段之后到点时刻照样按墙钟判断。
WATCH_POLL_INTERVAL_S: Final = 5.0
# 每段等待的下限（秒）：离到点时刻只剩极短一段时也不空转。
_MIN_WAIT_S: Final = 0.05


@dataclass(frozen=True)
class TunnelSetup:
    """隧道建成之后的三件产物：映射过的运行定义、隧道模式的额外请求头、隧道事实（含关闭会话的方法）。
    会话预热地址在 `info.warmup_url`（ADR 0035 决策 1），隧道模式下与额外请求头**恒同时给出**（含只有设备目标的 run），
    worker 侧的 definition 完整性判据（有请求头必有预热地址，ADR 0035「边界与不变量」）才在任何目标上都成立。"""

    jobs: tuple[Job, ...]
    extra_http_headers: dict[str, str]
    info: _tunnel.TunnelInfo


def map_jobs_to_tunnel(jobs, *, local_origin: str, public_url: str) -> tuple[tuple[Job, ...], dict[str, str]]:
    """把 job 文本里的 origin 换成干净的公网地址，并给出隧道模式恒注入的额外请求头（ADR 0035 决策 2、4）。

    映射产出新 Job（definition 不可变，见 `tunnel.map_origin_in_jobs`），原 jobs 不动；请求头每次给一份新的 dict，调用方改它不影响
    模块常量。`local_origin` 不是 origin 时抛 `tunnel.TunnelError`。"""
    mapped = _tunnel.map_origin_in_jobs(list(jobs), local_origin, public_url)  # 干净的隧道地址，不内嵌凭据（ADR 0051 决策 13）
    return tuple(mapped), dict(TUNNEL_EXTRA_HTTP_HEADERS)


def start_tunnel_for_jobs(jobs, *, local_origin: str, provider: str, closes_at: datetime,
                          timeout_s: float = _tunnel.START_TIMEOUT_S) -> TunnelSetup:
    """起隧道（流量策略带到 `closes_at` 为止的到点拒绝），再把运行定义映射到它的公网地址（ADR 0035 决策 1、2、4）。

    起不来（provider 未知、前置缺失、SDK 报错或超时）抛 `tunnel.TunnelError`，调用方归「没开始执行就被拒」、退出码 2。
    隧道建成之后映射失败（含被中断）时先关闭会话再把异常抛出：调用方拿不到 `TunnelInfo`，会话不能留给它关闭。"""
    info = _tunnel.make_tunnel(provider).start(local_origin, closes_at=closes_at, timeout_s=timeout_s)
    try:
        mapped, headers = map_jobs_to_tunnel(jobs, local_origin=local_origin, public_url=info.url)
    except BaseException:
        info.close()
        raise
    return TunnelSetup(jobs=mapped, extra_http_headers=headers, info=info)


# ============================================================================
# 云端 submit 的隧道守护进程
# ============================================================================


@dataclass(frozen=True)
class WatchEnd:
    """`watch_cloud_run` 为什么结束：读到 run 的终态（`status` 是那个终态），或墙钟已过到点时刻（`status` 为 None）。"""

    reason: Literal["run_ended", "past_closes_at"]
    status: Status | None


# 读不到或读不出 run 时的情形种类：None 表示读到了、run 还没有结束。
_ReadKind = Literal["missing", "read_error"] | None


def _bounded_wait_s(closes_at: datetime, now: datetime, poll_interval_s: float) -> float:
    """一段等待的时长：轮询间隔与距到点时刻的余量取小者，下限 `_MIN_WAIT_S`。"""
    remaining = (closes_at - now).total_seconds()
    return max(_MIN_WAIT_S, min(poll_interval_s, remaining))


def _open_cloud_run_store(runs_table: str, *, region: str | None, profile: str | None) -> RunStore:
    """守护进程读 run 状态用的 RunStore：runs 表、region 与 profile 是 `submit` 解析之后交来的值，这里不再解析（守护进程不读配置
    文件）。只读 STATE，不注入 jobs 对象的存取与列举索引。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    return DynamoDBRunStore(compose._make_ddb_table(runs_table, region=region, profile=profile))


@dataclass(eq=False)
class _PendingRead:
    """一次在守护线程里进行的读：装配存储（还没有装配时）并读 run 的状态。`done` 置位之前其余字段只由读的线程写，之后只由轮询读。"""

    store: RunStore | None
    done: threading.Event = field(default_factory=threading.Event)
    state: RunState | None = None
    error: BaseException | None = None


def _start_read(run_id: str, store: RunStore | None, opener: Callable[[], RunStore]) -> _PendingRead:
    """在一个守护线程里装配存储（`store` 为 None 时）并读一次 run 的状态，立即返回这次读。线程里的异常（含 BaseException）记进这次
    读、不外抛，不经线程的缺省异常处理写到标准错误；被放弃的读的线程不妨碍进程退出。"""
    pending = _PendingRead(store=store)

    def _target() -> None:
        try:
            if pending.store is None:
                pending.store = opener()
            pending.state = pending.store.load_run_state(run_id)
        except BaseException as e:  # noqa: BLE001 —— 交给轮询按种类处理或原样抛出
            pending.error = e
        finally:
            pending.done.set()

    threading.Thread(target=_target, name="gherkai-watch-read", daemon=True).start()
    return pending


def _one_line(text: str) -> str:
    return " ".join(text.split())


def watch_cloud_run(run_id: str, *, runs_table: str, region: str | None, profile: str | None,
                    closes_at: datetime, on_note: Callable[[str], None],
                    clock: Callable[[], datetime] | None = None, sleep: Callable[[float], None] | None = None,
                    poll_interval_s: float = WATCH_POLL_INTERVAL_S,
                    open_store: Callable[[], RunStore] | None = None,
                    wait_read: Callable[[threading.Event, float], bool] = threading.Event.wait) -> WatchEnd:
    """轮询云端 run 的状态，直到读到终态或墙钟严格晚于 `closes_at`（ADR 0035 决策 3「云端 `submit`」；到点时刻即运行期限加 300 秒）。

    每轮先读墙钟（只读 `clock`，缺省在调用时取 `compose.now`），已过到点时刻即结束；否则起一次读，终态即结束。到点这个上限不依赖一次读
    何时返回：装配存储与读运行态在一个守护线程里进行（`_start_read`），这里按轮询间隔与距到点时刻的余量中较小的一段分段等这次读的结果
    （`wait_read(事件, 秒数)`，读完为 True），每段之后重读墙钟；墙钟过了到点时刻而这次读还没有回来时放弃它、结束。一次读可以不返回：
    取凭证时 botocore 等 `credential_process` 不带时限，网络不回应时按 boto3 的缺省一次读也可以阻塞十几分钟。一次读没有回来之前不另起
    一次读。

    存储在第一次读之前装配，装配失败与读失败同一处理，下一轮再装。读不到这个 run、读失败、恢复读到三种情形按种类判断：种类变化时经
    `on_note` 记一句，同一种类连续出现不重复记，判断只看种类、不看说明文字（这种情形可能一直持续到到点时刻，每轮记一句只会淹没日志）。
    只有 Exception 算读失败，读里抛出的 KeyboardInterrupt、SystemExit 在这里照常抛出。每轮之后睡轮询间隔与距到点时刻的余量中较小的
    一段，下限 0.05 秒。`wait_read` 供测试注入，缺省是 `threading.Event.wait`。"""
    read_clock = clock if clock is not None else compose.now
    do_sleep = sleep if sleep is not None else time.sleep
    opener = open_store if open_store is not None else (
        lambda: _open_cloud_run_store(runs_table, region=region, profile=profile))

    store: RunStore | None = None
    last_kind: _ReadKind = None
    while True:
        now = read_clock()
        if now > closes_at:
            return WatchEnd(reason="past_closes_at", status=None)
        read = _start_read(run_id, store, opener)
        while not wait_read(read.done, _bounded_wait_s(closes_at, now, poll_interval_s)):
            now = read_clock()
            if now > closes_at:
                return WatchEnd(reason="past_closes_at", status=None)  # 放弃还没有回来的这次读
        store = read.store
        kind: _ReadKind = None
        error: BaseException | None = read.error
        if error is not None:
            if not isinstance(error, Exception):
                raise error
            kind = "read_error"  # 瞬时的网络、限流与凭证问题都按读失败继续轮询，到点时刻是上限
        elif read.state is None:
            kind = "missing"
        elif read.state.status in TERMINAL_STATUSES:
            return WatchEnd(reason="run_ended", status=read.state.status)
        if kind != last_kind:
            if kind == "missing":
                on_note("读不到这个 run，继续轮询")
            elif kind == "read_error":
                on_note(f"读 run 的状态失败（{_one_line(str(error)) or type(error).__name__}），继续轮询")
            else:
                on_note("恢复读到 run 的状态")
            last_kind = kind
        do_sleep(_bounded_wait_s(closes_at, read_clock(), poll_interval_s))


def _wait_for_run_id(input_fd: int, *, closes_at: datetime, clock: Callable[[], datetime],
                     poll_interval_s: float) -> bool:
    """等标准输入可读（`submit` 交来 run 的标识，或关闭了标准输入），以到点时刻为上限；等到为 True，过了到点时刻还不可读为 False。

    过了到点时刻之后再查一次（不等待）：run 的标识已经在管道里时照常收下，日志照常打开、写下开头与结束的两句，轮询随即按到点时刻
    结束。"""
    while True:
        now = clock()
        past = now > closes_at
        wait_s = 0.0 if past else _bounded_wait_s(closes_at, now, poll_interval_s)
        if handoff.wait_readable(input_fd, wait_s):
            return True
        if past:
            return False


def _open_watch_log(run_id: str) -> int:
    """打开守护进程的日志；打不开时改接空设备：持有隧道是守护进程唯一的职责，日志只是旁证（ADR 0035 决策 3）。"""
    try:
        return handoff.open_log(handoff.watch_log_path(run_id))
    except OSError:
        return os.open(os.devnull, os.O_WRONLY)


def _run_id_from_line(line: bytes) -> str:
    """标准输入上的第二行是 run 的标识；它要作为日志文件名的一部分，所以只接受单个路径分量。"""
    run_id = line.decode("utf-8").strip()
    if not run_id or run_id in (".", "..") or Path(run_id).name != run_id:
        raise ValueError(f"收到的 run 标识不是单个路径分量：{run_id!r}")
    return run_id


def hold_tunnel_for_cloud_run(inp: handoff.WatchInput, *, report_fd: int, input_fd: int,
                              note: Callable[[str], None],
                              redirect_output: Callable[[int], None] = handoff.redirect_output,
                              clock: Callable[[], datetime] | None = None,
                              sleep: Callable[[float], None] | None = None,
                              poll_interval_s: float = WATCH_POLL_INTERVAL_S,
                              open_store: Callable[[], RunStore] | None = None) -> int:
    """云端 `submit` 的隧道守护进程的主体（ADR 0035 决策 3「云端 `submit`」），返回进程的退出码。

    1. 起隧道（到点时刻取自 `inp.closes_at`）；起不来即经回报管道交回原因与退出码 2，返回 2。
    2. 经回报管道交回公网地址与预热地址；写不进（`submit` 已不在）即返回 0。回报管道的写端保持打开：`submit` 在建 run 之前对读端做一次
       非阻塞读，据此判断守护进程是否还在。
    3. 等 run 的标识，以到点时刻为上限：读到文件结束（`submit` 没有交出标识就关闭了标准输入）或过了到点时刻即返回 0。
    4. 收到标识之后把输出改接日志（`redirect_output`），日志打不开时接空设备；此后各句经 `note` 写进日志。
    5. 轮询到终态或到点时刻（`watch_cloud_run`），关闭会话之后记一句结束的原因，返回 0。

    收到 run 的标识之前不启动子进程、不调用 `note`：这时标准错误还接在 `submit` 上，子进程会继承它（ADR 0035 决策 3「输出」一条）。
    一切出口（含未捕获的异常）都在 `finally` 里关闭会话，且只关一次；结束的那一句在 `finally` 之后才写，「隧道已关闭」写出时会话已经
    关闭。不装信号处理器，被信号结束时会话随进程消失。

    两个描述符都归调用方关闭（进程入口里即进程退出）：回报写端在本函数返回之前一直开着，异常路径上回溯因此先于文件结束写到 `submit`
    的标准错误，`submit` 读到文件结束时说「原因在上面」才成立。`clock`、`sleep`、`poll_interval_s`、`open_store` 原样交给
    `watch_cloud_run`（等 run 的标识时也只读这个 `clock`），测试经它们注入。"""
    read_clock = clock if clock is not None else compose.now
    closes_at = instant_from_iso(inp.closes_at)
    info: _tunnel.TunnelInfo | None = None
    try:
        try:
            info = _tunnel.make_tunnel(inp.tunnel_provider).start(inp.local_origin, closes_at=closes_at)
        except _tunnel.TunnelError as e:
            handoff.write_all(report_fd, handoff.encode_watch_report(
                handoff.WatchReport(public_url=None, warmup_url=None, exit_code=2, message=str(e))))
            return 2
        delivered = handoff.write_all(report_fd, handoff.encode_watch_report(
            handoff.WatchReport(public_url=info.url, warmup_url=info.warmup_url, exit_code=0, message=None)))
        if not delivered:
            return 0
        if not _wait_for_run_id(input_fd, closes_at=closes_at, clock=read_clock, poll_interval_s=poll_interval_s):
            return 0
        line = handoff.read_line(input_fd)
        if not line:
            return 0
        run_id = _run_id_from_line(line)
        redirect_output(_open_watch_log(run_id))
        note(f"隧道已建立，等待 run {run_id} 结束（最晚到 {inp.closes_at} 关闭）")
        end = watch_cloud_run(
            run_id, runs_table=inp.runs_table, region=inp.region, profile=inp.profile, closes_at=closes_at,
            on_note=note, clock=read_clock, sleep=sleep, poll_interval_s=poll_interval_s, open_store=open_store)
    finally:
        if info is not None:
            info.close()
    # 只有轮询正常结束才走到这里：上面的各个 return 与异常都不经过
    if end.reason == "past_closes_at":
        note(f"已到 {inp.closes_at}，隧道已关闭（run {run_id}）")
    else:
        note(f"run {run_id} 已结束（{Status(end.status).value}），隧道已关闭")
    return 0
