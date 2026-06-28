"""子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 0024 协议的 worker 子进程。

这是 core 与「进程世界」的 seam——「怎么起 worker、怎么停」的进程/信号知识藏在这里，
schedule 只下逻辑指令（run_scope / handle.stop），对信号/进程无知（ADR 0026）。

形态：
- 起 worker：spawn cmd 子进程；把 job JSON 写 stdin、关 stdin；逐行读 stdout → event_from_line → Event 迭代器。
- 停 worker：SIGTERM → 等 grace_period → 未退则 SIGKILL（ADR 0024 终止契约的机制实现）。
- worker stderr 实时透传到本进程 stderr（日志/调试）。

引擎无关：cmd 决定起哪个 worker（Nova Act 的 python worker / 未来 Midscene 的 node worker）。
同一个 adapter 类，靠不同 cmd 服务不同腿——符合「两 adapter 形状一致」（ADR 0024）。
"""
from __future__ import annotations

import subprocess
import os
import sys
import threading
from typing import Iterator

from core.model import Event, Job
from core.wire import event_from_line, job_to_line


class SubprocessWorkerHandle:
    """一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。"""

    def __init__(self, proc: subprocess.Popen) -> None:
        self._proc = proc

    def stop(self, grace_period_s: float) -> None:
        proc = self._proc
        if proc.poll() is not None:
            return  # 已退出
        proc.terminate()  # SIGTERM —— worker 捕获后 finally 停 AgentCore 会话再退（ADR 0024）
        try:
            proc.wait(timeout=grace_period_s)
        except subprocess.TimeoutExpired:
            proc.kill()  # SIGKILL 兜底（会话清理可能落空，已知代价，ADR 0026）


class SubprocessEngine:
    """Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。"""

    def __init__(self, cmd: list[str], cwd: str | None = None, env: dict | None = None) -> None:
        self._cmd = cmd
        self._cwd = cwd
        self._env = env

    def run_scope(self, job: Job) -> tuple[SubprocessWorkerHandle, Iterator[Event]]:
        # 三通道分离（fd3）：
        #   fd3   = 纯 0024 事件（adapter 读这个）—— 自建管道，写端映射到子进程 fd3
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
        return handle, _read_events(proc, events_r)


def _read_events(proc: subprocess.Popen, events_r: int) -> Iterator[Event]:
    """逐行读 fd3（纯 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。"""
    with os.fdopen(events_r, "r", encoding="utf-8") as events:
        for line in events:
            line = line.strip()
            if not line:
                continue
            yield event_from_line(line)  # 解析失败 → 抛 ValueError，schedule 捕获记 error
    # fd3 耗尽 = worker 关了事件通道。等它真正退出，拿 returncode。
    proc.wait()
    if proc.returncode is not None and proc.returncode > 0:
        # 正零 = 正常；负 = 被信号杀（-SIGTERM/-SIGKILL，schedule 主动停的，属正常中止）；
        # 正非零 = worker 自身崩了但没吐完整事件流 → 抛错让 schedule 记 error。
        raise RuntimeError(f"worker 异常退出 returncode={proc.returncode}")


# 8 色 ANSI 前景色（按 scope_id 哈希挑一个，保证同一 worker 每次同色）
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
