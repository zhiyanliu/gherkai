"""ports 层（ADR 0016 六边形架构）：核心只依赖这些接口，具体 adapter 由组合根注入。

四个 port（关注点拆开，不揉成上帝 module）：
- Engine        —— 真正跑一个 scope（spawn worker、讲 ADR 0024 协议）；adapter = 子进程/未来 Fargate
- RunStore      —— 控制面：run/job 状态、血缘、起止（频繁读写，撑轮询续跑；未来 DDB 主要服务它）
- ResultStore   —— 数据面：每 scenario 判定真值、投票（追加为主）
- ReportStore   —— 归集报告产物为派生只读导航视图（RunReport：manifest + index，ADR 0027）

禁止：port 内部 env-sniff 自选实现（Midscene GlobalConfigManager 反模式）。adapter 一律组合根注入。
rule-of-three 克制：接口现在定（逼清边界），实现只写 local，云端 adapter 真需要时再填。
"""
from __future__ import annotations

from pathlib import Path
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
    """执行引擎 port（ADR 0016）。

    schedule 经此起 worker；adapter 形状一致（spawn node / spawn python / 未来 Fargate），schedule 对腿无知。
    """

    def run_scope(self, job: Job) -> tuple[WorkerHandle, Iterator[Event]]:
        """起一个 worker 跑这个 job，返回 (句柄, ADR 0024 事件流迭代器)。

        事件流逐条产出（ADR 0024 流式）；迭代结束 = worker 正常退出。
        句柄供 schedule 在超时/fail-fast 时 stop（ADR 0026）。
        """
        ...


# EngineResolver：按 job.engine 解析出 Engine（schedule 对腿数/腿名无知，ADR 0026）
@runtime_checkable
class EngineResolver(Protocol):
    def __call__(self, engine_name: str) -> Engine: ...


# Sink：接收 ADR 0024 原始流式事件的回调（pass-through，供进度/落地；与 RunResult 是同一事件流的两个视图，ADR 0026）
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
    """数据面：每 scenario 判定、投票抖动、报告指针（追加为主；CI 读判定真值靠它）。"""

    def save_job_result(self, run_id: str, job: JobResult) -> None: ...


@runtime_checkable
class ReportStore(Protocol):
    """归集报告产物为一份**派生只读导航视图**（RunReport，ADR 0027）：manifest.json + index.html。

    纯派生：可从 RunResult 完全重建，**永不作 CI 判定源**（判定真值在 RunResult/ResultStore）。
    只读 result 的 report_refs + scope_id/scenario_id/engine/status/时长/成本做导航，
    不读 votes/steps 细节、不拿产物内容、不按 kind 分支（不透明搬运）。
    """

    def write(self, run_id: str, result: RunResult, *, created_at: str = "", materialize: bool = False) -> Path:
        """从 RunResult 归集出 <report_root>/<run_id>/{manifest.json, index.html}，返回 index.html 路径。

        created_at: 组合根 mint 的时间戳字符串（core 不取时钟；进 manifest 信封）。
        materialize=False（默认）：不拷贝产物，index.html 链接直接指向各 ReportRef.ref（本地够用）。
        materialize=True（opt-in）：按字节把产物拷进 <run_id>/artifacts/，链接转相对 → 目录自包含
          （可整体搬走/上 S3）。按字节拷贝/移动允许；解析/重写/合并产物内容禁止（ADR 0027）。
        """
        ...
