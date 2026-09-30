"""子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。

这是 core 与「进程世界」的 seam——「怎么起 worker、怎么停」的进程/信号知识藏在这里，
schedule 只下逻辑指令（run_scope / handle.stop），对信号/进程无知（ADR 0026）。

形态（三通道分离，ADR 0024）：
- 起 worker：spawn cmd 子进程；把 job JSON 写 stdin、关 stdin；事件走**专用 fd**（自建管道，fd 号经环境变量
  `EVENTS_FD` 告知 worker）→ 逐行 event_from_line → Event 迭代器。
- 停 worker：SIGTERM → 等 grace_period → 未退则 SIGKILL（ADR 0024 终止契约的机制实现）。
- worker stdout（引擎 SDK 的进度噪声，不解析）+ stderr（worker 自己的诊断）都实时透传为日志。

引擎无关：cmd 决定起哪个 worker（Nova Act 的 python worker / Midscene 的 node worker）。
同一个 adapter 类，靠不同 cmd 服务不同引擎——符合「两 adapter 形状一致」（ADR 0024）。
"""
from __future__ import annotations

import subprocess
import os
import sys
import threading
from typing import Callable, Iterator

from gherkai_core.model import Event, Job
from gherkai_core.termcolor import use_color
from gherkai_core.redact import redact_url_userinfo
from gherkai_core.wire import event_from_line, job_to_line, raise_for_worker_exit


class SubprocessWorkerHandle:
    """一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。"""

    def __init__(self, proc: subprocess.Popen, pumps: tuple = ()) -> None:
        self._proc = proc
        self._pumps = pumps  # 透传 worker stdout/stderr 的两条 daemon 线程：stop 后有界 join，让日志尾部落完（ADR 0041 决策二）

    def stop(self, grace_period_s: float) -> None:
        proc = self._proc
        if proc.poll() is not None:
            return  # 已退出
        # SIGTERM —— worker 侧**协作式**响应（ADR 0024 终止契约）：Nova 的 handler 只置停止标志（flag-only、绝不
        # raise），主流程在 act 边界安全点正常退 with 释放 AgentCore 会话；Midscene 的 handler 执行显式 cleanup 序列
        # （会话释放优先）后 process.exit。两侧都不靠异常穿透解栈（raise 模型是 ADR 0024 被拒方案）。
        proc.terminate()
        try:
            proc.wait(timeout=grace_period_s)
        except subprocess.TimeoutExpired:
            proc.kill()  # SIGKILL 兜底（会话清理可能落空，已知代价，ADR 0026）
        # 进程已退 → 管道写端关、pump 读到 EOF 即结束；有界 join 让最后几行（多半是失败原因）先落到 sink，再由调用方关句柄。
        # 必须带超时：定位链第 4 级 uvx 是包装进程，孙进程可能仍持有 stdout 写端。
        _join_pumps(self._pumps, 0.5)

    def wait(self) -> int:
        """阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。

        per-run 进程的 SubprocessLauncher 消费完 fd3 事件流后调此拿 exitcode 写 task_exited——扮演
        「平台侧退出观察者」（cloud 对位是 ECS STOPPED 事件 payload 的 exitCode）。同步 run 路径不用（那条走
        schedule 迭代事件流、_read_events 内部 proc.wait）。SIGKILL 硬杀 → 负码（Python subprocess 约定）。
        """
        return self._proc.wait()


class SubprocessEngine:
    """Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。"""

    def __init__(self, cmd: list[str], cwd: str | None = None, env: dict | None = None,
                 log_sink=None) -> None:
        self._cmd = cmd
        self._cwd = cwd
        self._env = env
        # worker stdout/stderr 透传的落点（ADR 0041 决策二）：None → 本进程 stderr（人看流水，默认）；
        # 文件句柄 → 写它（`run --quiet` 落 worker.log，agent 的上下文不被 SDK 噪声灌满）。只转发、不解析。
        self._log_sink = log_sink

    @property
    def cmd(self) -> list[str]:
        """启 worker 的命令行（只读自省口，不在 Engine port 契约内）。生产路径不经此——CLI 的 list-engines / doctor 走 compose.resolve_worker_cmd 的定位链；现由组合根装配的单测断言接线用。"""
        return list(self._cmd)

    def run_scope(
        self, job: Job, raw_sink: "Callable[[str], None] | None" = None
    ) -> tuple[SubprocessWorkerHandle, Iterator[Event]]:
        # 三通道分离（fd3）：
        #   fd3   ：纯 ADR 0024 事件（adapter 读这个）—— 自建管道，写端映射到子进程 fd3
        #   stdout：引擎 SDK 的进度噪声（adapter 当日志透传，不解析）
        #   stderr：worker 自己的诊断/错误（独立，不被 SDK 噪声淹）
        events_r, events_w = os.pipe()
        # pass_fds 只保证写端被子进程继承，但 fd 号不变（不会重映射成 3）。
        # 故把实际 fd 号通过环境变量 EVENTS_FD 告诉 worker，worker 据此打开事件通道——
        # 比硬编码 fd3 更稳、可移植（worker 不假设具体号）。
        child_env = dict(self._env if self._env is not None else os.environ)
        child_env["EVENTS_FD"] = str(events_w)
        try:
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
        except BaseException:
            # 起 worker 失败（cmd 不存在 / cwd 无效 / 其他 OSError）：管道两端是**裸 fd、没有 GC 兜底**，不显式
            # 关就永久泄漏。调用方（schedule）把「起 worker 失败」吞成本 job 的 error 后继续执行下一个 job，故
            # worker 命令配错这类「每 job 必炸」的场景会按 job 数累积泄漏 → 撞进程 fd 上限。
            os.close(events_r)
            os.close(events_w)
            raise
        os.close(events_w)  # 父进程不写，关掉写端（否则读端永不 EOF）
        # stdout（SDK 噪声）+ stderr（worker 诊断）都实时透传为日志，单独线程读，避免管道满阻塞 worker。
        # 带 scope_id 前缀，多 worker 并发时区分谁在说话（与领域模型对齐、可追溯）。
        # **先起 pump、再写 stdin**：job JSON 可能很大（DataTable/DocString），写 stdin 会在管道满时阻塞；此刻 worker 若已在往
        # stdout/stderr 吐（SDK import 噪声）而无人读，父卡 stdin.write、子卡 stdout.write ——互锁。线程是 daemon、EOF 自然退出，
        # 下面 stdin 失败分支 kill/wait 后它们随管道关闭结束。
        color = _scope_color(job.scope_id)  # 按 job 启动顺序取色，两条流同色（见 _ANSI_COLORS 的注释）
        pumps = (threading.Thread(target=_pump_log, args=(proc.stdout, job.scope_id, "out", self._log_sink, color), daemon=True),
                 threading.Thread(target=_pump_log, args=(proc.stderr, job.scope_id, "err", self._log_sink, color), daemon=True))
        for t in pumps:
            t.start()
        try:
            assert proc.stdin is not None
            proc.stdin.write(job_to_line(job) + "\n")
            proc.stdin.flush()
            proc.stdin.close()
        except BaseException:
            # worker 起来即崩（stdin 写入抛 BrokenPipeError）：events_r 同样是裸 fd、子进程也需 reap——
            # 与上面 Popen 失败支同一「每 job 必炸 → 按 job 数累积泄漏」形态，同样显式收。
            os.close(events_r)
            proc.kill()
            proc.wait()
            raise

        handle = SubprocessWorkerHandle(proc, pumps=pumps)
        return handle, _read_events(proc, events_r, raw_sink, pumps=pumps)


def _join_pumps(pumps, timeout_s: float) -> None:
    """有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。"""
    for t in pumps:
        t.join(timeout_s)


def _read_events(
    proc: subprocess.Popen, events_r: int, raw_sink: "Callable[[str], None] | None" = None, pumps: tuple = ()
) -> Iterator[Event]:
    """逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。

    纯阻塞行读、纯 `Iterator[Event]`——**不掺心跳**。worker 静默卡死时本迭代器会阻塞在读上，由
    schedule 层的 `_heartbeat_wrap`（后台线程 + queue 超时）兜底唤醒并查超时（ADR 0026/0028）。
    心跳是「schedule 对任何慢/静默流的通用兜底」，不渗进端口契约，也不要每个 adapter 各写一遍。

    raw_sink（可选，ADR 0034 无状态批量运行）：非 None 时，每读到一行**原始 JSON 文本**（event_from_line 解析
    **之前**）旁路调它一次——供 SubprocessLauncher 把原始行落 SqliteEventLog（存原样、读回复用 event_from_line，
    零新序列化、不破 wire 单向契约）。同步 run 路径不传（None）→ 零行为变化。sink 异常不打断事件流（吞掉，
    落库失败不该拖垮执行；reconciler 靠事件持久性推进、丢一条下轮 worker 不会重发，但那是 cloud 事件日志（DDB）
    路径的边界，ADR 0034）。
    """
    try:
        with os.fdopen(events_r, "r", encoding="utf-8") as events:
            for line in events:
                line = line.strip()
                if not line:
                    continue
                if raw_sink is not None:
                    try:
                        raw_sink(line)  # 旁路落原始行（无状态批量运行），解析前
                    except Exception:
                        pass
                yield event_from_line(line)  # 解析失败 → 抛 ValueError，schedule 捕获记 error
    finally:
        # 自然 EOF 与被放弃（GeneratorExit，schedule 主动停后不再 next）两条路都有界等 pump 落完日志尾部，
        # 再轮到调用方关 sink 句柄（ADR 0041 决策二）；stop() 路径另有一次 join，两处都在、哪条先到都不裸奔。
        _join_pumps(pumps, 2.0)
    # fd3 耗尽表示 worker 关了事件通道。等它真正退出，拿 returncode。
    proc.wait()
    rc = proc.returncode
    if rc is not None and rc > 0:
        # 此 rc 检查仅在 fd3 自然 EOF（worker 自行退出）后执行——schedule 主动停 worker 走 _stop() 后
        # 即 return、放弃此 generator（GeneratorExit 在 yield 处冒出，不到这里），故主动停的退出码不经此。
        # 0 表示正常；负码表示被 SIGKILL 强杀（grace 超时，schedule 主动停的尾路径，不到此检查）；
        # 正非零表示 worker 自行异常退出（崩溃/会话清理失败 exit 1 / 网络故障退出码 80）→ 抛错让 schedule 记 error。
        # 注：两个引擎 worker 与 echo_worker 均自装 SIGTERM handler 后 process.exit/sys.exit（正码），
        # 故「负码即 SIGTERM」不成立——负码只来自 SIGKILL，且那条路径不经此检查（见上）。
        # 码→异常的翻译在 wire（协议级，与 Fargate adapter 共用一份，ADR 0024「退出码约定」）。
        raise_for_worker_exit(rc, code_label="returncode")


# worker 行前缀的 ANSI 前景色调色板：颜色只标**来源 scope**，与 out/err、与严重程度无关（ADR 0047）。
# 8 色为 33-36（黄/品/蓝/青）与 93-96（各自亮版）。两组有意排除：
#   - 31/91（红）与 32/92（绿）——ADR 0047 起判定汇总里红表示失败、绿表示通过，日志前缀再用红绿会被读成判定；
#   - 37/39/97（白/默认/亮白）——默认前景色保留给 cli main/core 自己的输出（`[core <scope>:event]` 进度、plan:/run_id=
#     等，见 cli/gherkai_cli/__main__.py 的 _progress），core 行与 worker 行的颜色域物理不相交、并发时一眼能分辨。
# 颜色按 job **启动顺序**依次分配（`_scope_color`）：同一次运行内前 8 个 scope 互不撞色，同一 plan 下颜色稳定；曾按
# scope_id 的 Python 哈希取模，4 个 scope 约四成的运行会撞色、且哈希按进程随机化导致每次运行颜色不同。
_ANSI_COLORS = (33, 35, 34, 36, 93, 95, 94, 96)
_scope_colors: dict[str, int] = {}
_scope_colors_lock = threading.Lock()


def _scope_color(scope_id: str) -> int:
    """scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。"""
    with _scope_colors_lock:
        if scope_id not in _scope_colors:
            _scope_colors[scope_id] = _ANSI_COLORS[len(_scope_colors) % len(_ANSI_COLORS)]
        return _scope_colors[scope_id]


def _reset_scope_colors() -> None:
    """测试用：清空进程内的颜色注册表。"""
    with _scope_colors_lock:
        _scope_colors.clear()


def _pump_log(stream, scope_id: str, tag: str, sink=None, color: int | None = None) -> None:
    """把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。

    带 [worker <scope_id>:<tag>] 前缀，多 worker 并发时区分来源。sink=None 写本进程 stderr，是否上色按统一策略
    （`termcolor.use_color(sys.stderr)`：`NO_COLOR` / `FORCE_COLOR` / `TERM=dumb` / 是否终端）——管道/文件/CI 输出纯文本，
    避免 ANSI 乱码；前缀色由 `color` 给出（调用方在 job 启动时取 `_scope_color`，两条流同色），缺省时按 scope_id 取。
    sink 给了文件句柄则写它（无颜色码，逐行 flush 让 tail 可见）。
    """
    if stream is None:
        return
    prefix = f"[worker {scope_id}:{tag}]"
    if sink is not None:
        for line in stream:
            try:
                sink.write(f"{prefix} {redact_url_userinfo(line)}")  # 隧道凭据不进日志（ADR 0035 决策 5）
                sink.flush()
            except ValueError:
                return  # 句柄已关表示本进程正在收尾（join 超时后仍有尾巴的残余路径）：静默停转发，别把 traceback 打到 stderr
        return
    if use_color(sys.stderr):
        if color is None:
            color = _scope_color(scope_id)
        prefix = f"\033[{color}m{prefix}\033[0m"
    for line in stream:
        sys.stderr.write(f"{prefix} {redact_url_userinfo(line)}")
