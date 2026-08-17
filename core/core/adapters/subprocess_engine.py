"""子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。

这是 core 与「进程世界」的 seam——「怎么起 worker、怎么停」的进程/信号知识藏在这里，
schedule 只下逻辑指令（run_scope / handle.stop），对信号/进程无知（ADR 0026）。

形态（三通道分离，ADR 0024）：
- 起 worker：spawn cmd 子进程；把 job JSON 写 stdin、关 stdin；事件走**专用 fd**（自建管道，fd 号经环境变量
  `EVENTS_FD` 告知 worker）→ 逐行 event_from_line → Event 迭代器。
- 停 worker：SIGTERM → 等 grace_period → 未退则 SIGKILL（ADR 0024 终止契约的机制实现）。
- worker stdout（引擎 SDK 的进度噪声，不解析）+ stderr（worker 自己的诊断）都实时透传为日志。

引擎无关：cmd 决定起哪个 worker（Nova Act 的 python worker / 未来 Midscene 的 node worker）。
同一个 adapter 类，靠不同 cmd 服务不同引擎——符合「两 adapter 形状一致」（ADR 0024）。
"""
from __future__ import annotations

import subprocess
import os
import sys
import threading
from typing import Callable, Iterator

from core.errors import WorkerNetworkError
from core.model import Event, Job
from core.wire import event_from_line, job_to_line

# worker 网络专用退出码（ADR 0028）：worker 建连失败、重试耗尽时以此码退出，作 out-of-band 信号
# （建连失败发生在任何事件 emit 之前，无法走事件通道）。值避开 POSIX sysexits(64-78)/signal 保留区。
# **两个引擎 worker 必须用同一个值**（Nova run_scope.py / Midscene run-scope.ts 各自硬编码 80）。
EX_WORKER_NETWORK = 80


class SubprocessWorkerHandle:
    """一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。"""

    def __init__(self, proc: subprocess.Popen) -> None:
        self._proc = proc

    def stop(self, grace_period_s: float) -> None:
        proc = self._proc
        if proc.poll() is not None:
            return  # 已退出
        proc.terminate()  # SIGTERM —— worker 捕获后 raise→with __exit__ 解栈停 AgentCore 会话再退（ADR 0024）
        try:
            proc.wait(timeout=grace_period_s)
        except subprocess.TimeoutExpired:
            proc.kill()  # SIGKILL 兜底（会话清理可能落空，已知代价，ADR 0026）

    def wait(self) -> int:
        """阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。

        per-run 进程的 SubprocessLauncher 消费完 fd3 事件流后调此拿 exitcode 写 task_exited——扮演
        「平台侧退出观察者」（cloud 对位=ECS STOPPED 事件 payload 的 exitCode）。同步 run 路径不用（那条走
        schedule 迭代事件流、_read_events 内部 proc.wait）。SIGKILL 硬杀 → 负码（Python subprocess 约定）。
        """
        return self._proc.wait()


class SubprocessEngine:
    """Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。"""

    def __init__(self, cmd: list[str], cwd: str | None = None, env: dict | None = None) -> None:
        self._cmd = cmd
        self._cwd = cwd
        self._env = env

    @property
    def cmd(self) -> list[str]:
        """启 worker 的命令行（只读，供组合根自省/日志，如 CLI 的 list-engines）。"""
        return list(self._cmd)

    @property
    def cwd(self) -> str | None:
        """worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。"""
        return self._cwd

    def run_scope(
        self, job: Job, raw_sink: "Callable[[str], None] | None" = None
    ) -> tuple[SubprocessWorkerHandle, Iterator[Event]]:
        # 三通道分离（fd3）：
        #   fd3   = 纯 ADR 0024 事件（adapter 读这个）—— 自建管道，写端映射到子进程 fd3
        #   stdout= 引擎 SDK 的进度噪声（adapter 当日志透传，不解析）
        #   stderr= worker 自己的诊断/错误（独立，不被 SDK 噪声淹）
        events_r, events_w = os.pipe()
        # pass_fds 只保证写端被子进程继承，但 fd 号不变（不会重映射成 3）。
        # 故把实际 fd 号通过环境变量 EVENTS_FD 告诉 worker，worker 据此打开事件通道——
        # 比硬编码 fd3 更稳、可移植（worker 不假设具体号）。
        child_env = dict(self._env if self._env is not None else os.environ)
        child_env["EVENTS_FD"] = str(events_w)
        proc = subprocess.Popen(
            self._cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._cwd,
            env=child_env,
            text=True,
            encoding="utf-8",
            bufsize=1,  # 行缓冲：worker 每吐一行即可读到（流式，ADR 0024）
            pass_fds=(events_w,),  # 让子进程继承写端
        )
        os.close(events_w)  # 父进程不写，关掉写端（否则读端永不 EOF）
        assert proc.stdin is not None
        proc.stdin.write(job_to_line(job) + "\n")
        proc.stdin.flush()
        proc.stdin.close()

        # stdout（SDK 噪声）+ stderr（worker 诊断）都实时透传为日志，单独线程读，避免管道满阻塞 worker。
        # 带 scope_id 前缀，多 worker 并发时区分谁在说话（与领域模型对齐、可追溯）。
        threading.Thread(target=_pump_log, args=(proc.stdout, job.scope_id, "out"), daemon=True).start()
        threading.Thread(target=_pump_log, args=(proc.stderr, job.scope_id, "err"), daemon=True).start()

        handle = SubprocessWorkerHandle(proc)
        return handle, _read_events(proc, events_r, raw_sink)


def _read_events(
    proc: subprocess.Popen, events_r: int, raw_sink: "Callable[[str], None] | None" = None
) -> Iterator[Event]:
    """逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。

    纯阻塞行读、纯 `Iterator[Event]`——**不掺心跳**。worker 静默卡死时本迭代器会阻塞在读上，由
    schedule 层的 `_heartbeat_wrap`（后台线程 + queue 超时）兜底唤醒并查超时（ADR 0026/0028）。
    心跳是「schedule 对任何慢/静默流的通用兜底」，不渗进端口契约，也不要每个 adapter 各写一遍。

    raw_sink（可选，ADR 0034 无状态跑批）：非 None 时，每读到一行**原始 JSON 文本**（event_from_line 解析
    **之前**）旁路调它一次——供 SubprocessLauncher 把原始行落 SqliteEventLog（存原样、读回复用 event_from_line，
    零新序列化、不破 wire 单向契约）。同步 run 路径不传（None）→ 零行为变化。sink 异常不打断事件流（吞掉，
    落库失败不该拖垮执行；reconciler 靠事件持久性推进、丢一条下轮 worker 不会重发，但那是 cloud 事件日志（DDB）
    路径的边界，ADR 0034）。
    """
    with os.fdopen(events_r, "r", encoding="utf-8") as events:
        for line in events:
            line = line.strip()
            if not line:
                continue
            if raw_sink is not None:
                try:
                    raw_sink(line)  # 旁路落原始行（无状态跑批），解析前
                except Exception:
                    pass
            yield event_from_line(line)  # 解析失败 → 抛 ValueError，schedule 捕获记 error
    # fd3 耗尽 = worker 关了事件通道。等它真正退出，拿 returncode。
    proc.wait()
    rc = proc.returncode
    if rc is not None and rc > 0:
        # 此 rc 检查仅在 fd3 自然 EOF（worker 自行退出）后执行——schedule 主动停 worker 走 _stop() 后
        # 即 return、放弃此 generator（GeneratorExit 在 yield 处冒出，不到这里），故主动停的退出码不经此。
        # 0 = 正常；负 = 被 SIGKILL 强杀（grace 超时，schedule 主动停的尾路径，不到此检查）；
        # 正非零 = worker 自行异常退出（崩溃/会话清理失败 exit 1 / 网络码 80）→ 抛错让 schedule 记 error。
        # 注：两个引擎 worker 与 echo_worker 均自装 SIGTERM handler 后 process.exit/sys.exit（正码），
        # 故「负码=SIGTERM」不成立——负码只来自 SIGKILL，且那条路径不经此检查（见上）。
        if rc == EX_WORKER_NETWORK:
            # worker 以网络专用退出码退出（建连失败、重试耗尽，ADR 0028）：抛类型化异常，
            # schedule 据此记 network_error 并可选择性重试整 job。
            raise WorkerNetworkError(f"worker 建连失败（网络/SSL 瞬时故障），退出码 {rc}")
        raise RuntimeError(f"worker 异常退出 returncode={rc}")


# worker 行的 ANSI 前景色调色板（按 scope_id 哈希挑一个，保证同一 worker 每次同色）。
# 12 色 = 31-36（红/绿/黄/蓝/品/青）+ 91-96（各自亮版）。
# **有意排除 37/39/97（白/默认/亮白）**：默认前景色保留给 cli main/core 自己的输出
# （`[core <scope>:event]` 进度、plan:/run_id=/RunReport: 等，它们一律不上色 = 默认色，见 cli/__main__.py
# 的 _progress）。这样 core 行与 worker 行的颜色域**物理不相交**、并发跑批时一眼能分辨「core 说的」vs
# 「worker 透传的」。改本调色板时**勿加入 37/39/97**，否则会与 core 的默认色撞、破坏这条约定。
_ANSI_COLORS = (31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96)


def _pump_log(stream, scope_id: str, tag: str) -> None:
    """把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。

    带 [worker <scope_id>:<tag>] 前缀，多 worker 并发时区分来源。
    仅当本进程 stderr 是终端（isatty）时才上色——管道/文件/CI 输出纯文本，避免 ANSI 乱码。
    """
    if stream is None:
        return
    prefix = f"[worker {scope_id}:{tag}]"
    if sys.stderr.isatty():
        color = _ANSI_COLORS[hash(scope_id) % len(_ANSI_COLORS)]
        prefix = f"\033[{color}m{prefix}\033[0m"
    for line in stream:
        sys.stderr.write(f"{prefix} {line}")
