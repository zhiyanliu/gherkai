"""`submit` 与它启动的后台进程之间的交接协议：消息、编解码与原始描述符的读写（ADR 0035 决策 3）。

两种用法共用这一组读写函数：
- **本机 `submit` 与后台推进进程**：`submit` 以新会话启动后台推进进程，经它的标准输入交一行 `AdvancerInput`，另给它一条回报管道
  的写端。后台推进进程起隧道、建 run、装配、打开 `reconcile.log` 之后，经回报管道交回一行 `AdvancerReport` 并关闭它；没有建成时
  回报里是原因与退出码。`submit` 手里的标准输入写端一直开到收到回报。
- **云端 `submit` 与隧道守护进程**：`submit` 经守护进程的标准输入交一行 `WatchInput`，守护进程起隧道之后经回报管道交回一行
  `WatchReport`，并保持回报管道的写端打开；`submit` 建 run 之后经标准输入交出 run 的标识（一行），守护进程等这一行以到点时刻为上限
  （`wait_readable`）。`WatchChannel` 是 `submit` 一侧持有这两个描述符的句柄。

**对端还在不在**（两种用法、两个方向同一条判据，ADR 0035 决策 3）：对一条由对端独占写端的管道的读端做一次非阻塞读，读到文件结束
即对端已不在（`peer_closed`）。本机：后台推进进程在建 run 之前查标准输入，写端只在 `submit` 手里；云端：`submit` 在建 run 之前查
回报管道的读端，写端只在守护进程手里。依据是 POSIX 的读语义：写端的最后一份副本关闭之后（含持有它的进程被强杀）读端读到文件结束，
写端还开着而没有数据时非阻塞读立即以 EAGAIN 返回；macOS 与 Linux 上实测同义。判据成立的前提是写端只在对端一个进程里：回报管道的
写端经 `pass_fds` 交给对端之后，启动方关掉自己那一份，对端把它设为不可继承；标准输入的写端由启动方用 `os.pipe()` 建出、只留在启动方，
按 PEP 446 本来不可继承。

消息一律是一行 JSON：以换行结束，正文里的换行都已转义。协议严格一问一答，一方读到一行之前另一方不会再写，所以读一行时换行之后
不会有别的字节。两端是同一个安装包、同一个解释器，消息不带版本号；解码只认各自固定的键集，形态不对抛 ValueError。

本模块只依赖标准库与 core：两端的入口在 cli，起隧道与轮询在 `tunnel` 与 `tunnel_host`，这里只管消息与描述符。
"""
from __future__ import annotations

import contextlib
import json
import os
import select
import sys
import tempfile
from dataclasses import dataclass, field, fields
from pathlib import Path

from gherkai_core.model import Job
from gherkai_core.serialize import job_from_dict, job_to_dict

_READ_CHUNK = 65536


# ============================================================================
# 消息
# ============================================================================


@dataclass(frozen=True)
class AdvancerInput:
    """本机 `submit` 经标准输入一次交给后台推进进程的输入。

    不带的东西各有来处：CLI 版本与创建时刻由后台推进进程自己取（同一个安装包、同一个钟）；环境变量（ngrok 令牌、AWS 凭证、
    worker 命令的覆盖）经 `Popen` 继承。后台推进进程不读项目配置文件：凡来自配置的值都在这里按解析之后的值给出（ADR 0053）。"""

    jobs: tuple[Job, ...]   # 补全之后、隧道映射之前的 job（definition 形态，经 serialize 的 job 编解码）
    steps_dir: str | None
    max_concurrency: int
    per_job_tail_s: float   # 提交进程按各引擎自报的宽限算好的每 job 尾段
    expose_local: str | None   # 已归一化的 origin；不经隧道为 None
    tunnel_provider: str
    region: str | None
    profile: str | None
    report_dir: str          # 绝对路径


@dataclass(frozen=True)
class AdvancerReport:
    """后台推进进程经回报管道交回的结果：建成时 `exit_code` 为 0、带 run 的标识与公网地址（不经隧道为 None）；
    没有建成时 `exit_code` 非零，`message` 是提交进程原样输出的整句。"""

    run_id: str | None
    public_url: str | None
    exit_code: int
    message: str | None


@dataclass(frozen=True)
class WatchInput:
    """云端 `submit` 经标准输入交给隧道守护进程的输入。"""

    local_origin: str
    tunnel_provider: str
    closes_at: str   # 到点时刻（运行期限加 300 秒），记录里的 ISO 写法
    runs_table: str
    region: str | None
    profile: str | None


@dataclass(frozen=True)
class WatchReport:
    """隧道守护进程经回报管道交回的结果。预热地址含令牌：只经管道交给 `submit`，不进 repr、不进任何日志。"""

    public_url: str | None
    warmup_url: str | None = field(repr=False)
    exit_code: int = 0
    message: str | None = None


# ============================================================================
# 编解码：一行 JSON
# ============================================================================


def _encode(d: dict) -> bytes:
    # json.dumps 不带缩进时不输出原始换行（字符串里的换行写成转义），所以结尾的换行是这一行唯一的换行；
    # allow_nan=False：NaN 与无穷不是 JSON，写出来另一端读不回
    return (json.dumps(d, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _decode(line: bytes, cls: type) -> dict:
    what = cls.__name__
    try:
        d = json.loads(line)
    except ValueError as e:   # 含 JSONDecodeError 与 UnicodeDecodeError
        raise ValueError(f"交接消息 {what} 不是一行 JSON：{e}") from e
    if not isinstance(d, dict):
        raise ValueError(f"交接消息 {what} 须为 JSON 对象，现为 {type(d).__name__}")
    want = {f.name for f in fields(cls)}
    if set(d) != want:
        raise ValueError(f"交接消息 {what} 的键不符：缺 {sorted(want - set(d))}，多 {sorted(set(d) - want)}")
    return d


def _plain_fields(x) -> dict:
    return {f.name: getattr(x, f.name) for f in fields(x)}


def encode_advancer_input(x: AdvancerInput) -> bytes:
    return _encode({**_plain_fields(x), "jobs": [job_to_dict(j) for j in x.jobs]})


def decode_advancer_input(line: bytes) -> AdvancerInput:
    """job 经 `job_from_dict` 读回，读时恒做 definition 的结构校验：形态不对抛 DefinitionContractError（ValueError 的子类）。"""
    d = _decode(line, AdvancerInput)
    jobs = d["jobs"]
    if not isinstance(jobs, list):
        raise ValueError(f"交接消息 AdvancerInput 的 jobs 须为数组，现为 {type(jobs).__name__}")
    return AdvancerInput(**{**d, "jobs": tuple(job_from_dict(j) for j in jobs)})


def encode_advancer_report(r: AdvancerReport) -> bytes:
    return _encode(_plain_fields(r))


def decode_advancer_report(line: bytes) -> AdvancerReport:
    return AdvancerReport(**_decode(line, AdvancerReport))


def encode_watch_input(x: WatchInput) -> bytes:
    return _encode(_plain_fields(x))


def decode_watch_input(line: bytes) -> WatchInput:
    return WatchInput(**_decode(line, WatchInput))


def encode_watch_report(r: WatchReport) -> bytes:
    return _encode(_plain_fields(r))


def decode_watch_report(line: bytes) -> WatchReport:
    return WatchReport(**_decode(line, WatchReport))


# ============================================================================
# 原始描述符的读写
# ============================================================================


def read_line(fd: int) -> bytes:
    """从原始描述符分块读到第一个换行，返回含结尾换行的这一行；换行之前读到文件结束（对端没交完就关了写端）返回 b""。

    返回值保留换行，空字节串因此只表示文件结束。读到的块里换行之后还有字节即抛 ValueError：协议一问一答，
    出现了说明协议被破坏。同一条管道上先后交来的两行（云端守护进程的标准输入：先是输入，收到回报之后才有 run 的标识）
    各读一次，前一次不会读走后一行。"""
    buf = bytearray()
    while True:
        chunk = os.read(fd, _READ_CHUNK)
        if not chunk:
            return b""
        start = len(buf)
        buf += chunk
        i = buf.find(b"\n", start)
        if i < 0:
            continue
        if i != len(buf) - 1:
            raise ValueError(f"交接消息之后还有 {len(buf) - i - 1} 个字节：一方读到一行之前另一方不应再写")
        return bytes(buf)


def peer_closed(fd: int) -> bool:
    """对管道的读端做一次非阻塞读：读到文件结束（写端已全部关闭）为 True；写端还开着、没有数据（EAGAIN）为 False。

    读完把描述符的阻塞模式恢复成读之前的样子（两种用法里都是阻塞的）。阻塞模式是这条管道读端的打开文件描述上的标志，
    同一描述的其它持有者在这一刻同样看到非阻塞；两种用法里读端都只在本进程手里，不受影响。读到数据即抛 ValueError：
    两种用法里对端在这一刻都不会再写，读到了说明协议被破坏，读走的字节也无法放回。"""
    was_blocking = os.get_blocking(fd)
    os.set_blocking(fd, False)
    try:
        data = os.read(fd, 1)
    except BlockingIOError:
        return False
    finally:
        os.set_blocking(fd, was_blocking)
    if data:
        raise ValueError("检查对端是否还在时读到了数据：此时对端不应再写")
    return True


def wait_readable(fd: int, timeout_s: float) -> bool:
    """等描述符可读（有数据或文件结束）：等到即 True，到时限仍不可读即 False；不读走任何字节。`timeout_s` 不大于 0 时只查一次。"""
    readable, _, _ = select.select([fd], [], [], max(0.0, timeout_s))
    return bool(readable)


def write_all(fd: int, data: bytes) -> bool:
    """循环写满整段数据；对端已关闭读端（BrokenPipeError）返回 False，不抛。不关闭描述符。

    Python 启动时把 SIGPIPE 设为忽略，写到读端已关闭的管道得到的是 EPIPE 而不是信号。"""
    view = memoryview(data)
    while view:
        try:
            n = os.write(fd, view)
        except BrokenPipeError:
            return False
        view = view[n:]
    return True


def close_quietly(fd: int) -> None:
    """关闭描述符，忽略 OSError。描述符号会被复用：同一个号只能关一次，由调用方保证。"""
    with contextlib.suppress(OSError):
        os.close(fd)


def open_log(path: Path) -> int:
    """以追加方式打开（不存在即建立）日志文件，返回描述符；打不开抛 OSError。描述符不可继承（PEP 446），交给 `redirect_output`。"""
    return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)


def redirect_output(log_fd: int) -> None:
    """后台进程回报之后调用：把标准输出与标准错误改接日志，标准输入改接空设备，再关闭 `log_fd`。

    先冲刷 `sys.stdout` 与 `sys.stderr`：回报之前缓冲着的输出仍写到原处（`submit` 的标准错误），不混进日志；`submit` 已经不在、
    冲刷失败时丢弃。改接之后本进程的输出与之后启动的子进程（如 worker）继承到的描述符都是日志。回报之前后台进程不启动子进程、
    不往标准错误写字（崩溃的回溯除外）：子进程会继承接在 `submit` 标准错误上的描述符，调用方经管道捕获 `submit` 的输出时要等那个
    子进程退出才读到文件结束（ADR 0035 决策 3「输出」一条）。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:
            with contextlib.suppress(OSError, ValueError):
                stream.flush()
    os.dup2(log_fd, 1)
    os.dup2(log_fd, 2)
    null_fd = os.open(os.devnull, os.O_RDONLY)
    try:
        os.dup2(null_fd, 0)
    finally:
        os.close(null_fd)
    if log_fd > 2:
        os.close(log_fd)


def watch_log_path(run_id: str) -> Path:
    """隧道守护进程的日志位置：系统临时目录里的 `gherkai-tunnel-watch-<run_id>.log`。提交进程（给使用者的那一句）与守护进程
    （写日志）都由这里取；守护进程经 `Popen` 继承提交进程的环境，两者得到的临时目录相同。"""
    return Path(tempfile.gettempdir()) / f"gherkai-tunnel-watch-{run_id}.log"


# ============================================================================
# 云端 submit 一侧的守护进程句柄
# ============================================================================


@dataclass
class WatchChannel:
    """云端 `submit` 持有的守护进程句柄：守护进程标准输入的写端与回报管道的读端，外加守护进程回报的两个地址。

    句柄拥有这两个描述符：`release` 关闭它们，调用方不要再经别的对象（如 `Popen.stdin` 的文件对象）持有或关闭同一个描述符，
    否则同一个号会被关两次。`release` 之后 `daemon_gone` 与 `hand_over` 抛 ValueError，与读写已关闭的文件同一处理。"""

    public_url: str
    warmup_url: str = field(repr=False)   # 含令牌
    stdin_fd: int = field(kw_only=True)    # 守护进程标准输入的写端
    report_fd: int = field(kw_only=True)   # 回报管道的读端
    _released: bool = field(default=False, init=False, repr=False, compare=False)

    def daemon_gone(self) -> bool:
        """守护进程是否已不在：对回报管道的读端做一次非阻塞读，读到文件结束即已不在（写端只在守护进程手里）。"""
        self._require_open()
        return peer_closed(self.report_fd)

    def hand_over(self, run_id: str) -> bool:
        """经标准输入交出 run 的标识（一行）；守护进程已不在（写不进）返回 False。

        不先查一次再写：写入本身就给出结果，先查后写之间守护进程照样可能退出。"""
        self._require_open()
        if not run_id or "\n" in run_id:
            raise ValueError(f"run 的标识须为不含换行的非空文本，现为 {run_id!r}")
        return write_all(self.stdin_fd, (run_id + "\n").encode("utf-8"))

    def release(self) -> None:
        """关闭标准输入的写端与回报管道的读端（守护进程还在等 run 的标识时随之读到文件结束、关闭会话退出）。可重复调用，只关一次。"""
        if self._released:
            return
        self._released = True   # 先记下再关：关到一半被打断时，再次调用也不会把已经复用的号再关一次
        close_quietly(self.stdin_fd)
        close_quietly(self.report_fd)

    def _require_open(self) -> None:
        if self._released:
            raise ValueError("守护进程的句柄已经释放")
