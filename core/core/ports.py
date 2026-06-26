"""ports 层（ADR 0016 六边形架构）：核心只依赖这些接口，具体 adapter 由组合根注入。

四个 port（关注点拆开，不揉成上帝 module）：
- Engine        —— 真正跑一个 scope（spawn worker、讲 0024 协议）；adapter = 子进程/未来 Fargate
- RunStore      —— 控制面：run/job 状态、血缘、起止（频繁读写，撑轮询续跑；未来 DDB 主要服务它）
- ResultStore   —— 数据面：每 scenario 判定、投票、报告指针（追加为主）
- ReportStore   —— 归集报告产物（local FS → S3）

禁止：port 内部 env-sniff 自选实现（Midscene GlobalConfigManager 反模式）。adapter 一律组合根注入。
rule-of-three 克制：接口现在定（逼清边界），实现只写 local，云端 adapter 真需要时再填。
"""
from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable

from core.model import Event, Job, JobResult, RunResult


# ============================================================================
# Engine port（ADR 0024/0026）：跑一个 scope，流式回事件，可优雅停
# ============================================================================


@runtime_checkable
class WorkerHandle(Protocol):
    """一个在跑的 worker 的句柄（schedule 持有，用于 stop）。

    不暴露进程/信号细节——「怎么停」的机制（SIGTERM→宽限→SIGKILL / 未来 StopTask）藏在 adapter 内部（ADR 0026）。
    """

    def stop(self, grace_period_s: float) -> None:
        """请求优雅停止：adapter 内部翻成具体机制；worker 收到后停会话、退出（ADR 0024 终止契约）。"""
        ...


@runtime_checkable
class Engine(Protocol):
    """执行引擎 port（早先名 ExecutionBackend，ADR 0016 重命名）。

    schedule 经此起 worker；adapter 形状一致（spawn node / spawn python / 未来 Fargate），schedule 对腿无知。
    """

    def run_scope(self, job: Job) -> tuple[WorkerHandle, Iterator[Event]]:
        """起一个 worker 跑这个 job，返回 (句柄, 0024 事件流迭代器)。

        事件流逐条产出（ADR 0024 流式）；迭代结束 = worker 正常退出。
        句柄供 schedule 在超时/fail-fast 时 stop（ADR 0026）。
        """
        ...


# EngineResolver：按 job.engine 解析出 Engine（schedule 对腿数/腿名无知，ADR 0026）
@runtime_checkable
class EngineResolver(Protocol):
    def __call__(self, engine_name: str) -> Engine: ...


# Sink：接收 0024 原始流式事件的回调（pass-through，供进度/落地；与 RunResult 是同一事件流的两个视图，ADR 0026）
@runtime_checkable
class Sink(Protocol):
    def __call__(self, event: Event) -> None: ...


# ============================================================================
# 状态/结果/报告 port（ADR 0016；现仅定义，local adapter 与 schedule 同期或稍后填）
# ============================================================================


@runtime_checkable
class RunStore(Protocol):
    """控制面：run/job 生命周期状态、status、起止、会话血缘（撑轮询/续跑/WebUI 进度）。"""

    def save_run(self, result: RunResult) -> None: ...
    def load_run(self, run_id: str) -> RunResult | None: ...


@runtime_checkable
class ResultStore(Protocol):
    """数据面：每 scenario 判定、投票抖动、报告指针（追加为主；RunReport 归集与 CI 读判定靠它）。"""

    def save_job_result(self, run_id: str, job: JobResult) -> None: ...


@runtime_checkable
class ReportStore(Protocol):
    """归集报告产物（local FS → S3）。v1.0 先「散着」（ADR 0016 版本切分），此接口留口子。"""

    def save_report_ref(self, run_id: str, scope_id: str, path: str, granularity: str) -> None: ...
