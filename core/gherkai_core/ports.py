"""ports 层（ADR 0016 六边形架构）：核心只依赖这些接口，具体 adapter 由组合根注入。

四个 port（关注点拆开，不揉成上帝 module）：
- Engine        —— 真正跑一个 scope（spawn worker、讲 ADR 0024 协议）；adapter = 子进程/Fargate
- RunStore      —— 控制面：run/job 状态、血缘、起止（频繁读写，撑轮询续跑与无状态跑批的条件写）
- ResultStore   —— 数据面：每 scenario 判定真值、投票（追加为主）
- ReportStore   —— 归集报告产物为派生只读导航视图（RunReport：manifest + index，ADR 0027）

禁止：port 内部 env-sniff 自选实现（Midscene GlobalConfigManager 反模式）。adapter 一律组合根注入。
接口先定（逼清边界）；四个 port 的 local + 云端 adapter 均已实装（RunStore: local/ddb、Result/ReportStore:
local/s3、Engine: subprocess/fargate），组合根按 `--backend` 注入。
"""
from __future__ import annotations

from typing import Iterator, Protocol

from gherkai_core.model import (
    Event,
    Job,
    JobResult,
    JobState,
    ResourceUri,
    RunMeta,
    RunResult,
    RunState,
    Status,
)


# ============================================================================
# Engine port（ADR 0024/0026）：跑一个 scope，流式回事件，可优雅停
# ============================================================================


class WorkerHandle(Protocol):
    """一个在跑的 worker 的句柄（schedule 持有，用于 stop）。

    不暴露进程/信号细节——「怎么停」的机制藏在 adapter 内部（ADR 0026）：子进程 SIGTERM→宽限→SIGKILL（真用运行期 grace）；
    Fargate `StopTask`（忽略运行期 grace 入参，宽限由 task-def 期 `stopTimeout` 定，ADR 0024「终止契约」）。
    """

    def stop(self, grace_period_s: float) -> None:
        """请求优雅停止：adapter 内部翻成具体机制；worker 收到后停会话、退出（ADR 0024 终止契约）。"""
        ...


class Engine(Protocol):
    """执行引擎 port（ADR 0016）。

    schedule 经此起 worker；adapter 形状一致（spawn node 子进程 / spawn python 子进程 / Fargate task），schedule 对引擎无知。
    """

    def run_scope(self, job: Job) -> tuple[WorkerHandle, Iterator[Event]]:
        """起一个 worker 跑这个 job，返回 (句柄, ADR 0024 事件流迭代器)。

        事件流逐条产出（ADR 0024 流式）；迭代结束 = worker 正常退出。
        句柄供 schedule 在超时/fail-fast 时 stop（ADR 0026）。

        **纯事件流**：adapter 只产领域事件，不掺心跳/哨兵——worker 静默卡死时迭代器自然阻塞在读上，
        由 schedule 层统一兜底（后台线程 + 超时唤醒查 deadline，ADR 0026/0028）。心跳是消费方策略，
        不进端口契约，也不必每个 adapter 各实现一遍。

        **本签名即全部契约**：`SubprocessEngine.run_scope` 另有 `raw_sink`（原始事件行旁路，供无状态路径把
        未解析的行落持久 events sink）——那是**该 adapter 的扩展形参、不在 port 契约内**（ADR 0034「Engine port
        演进」；`FargateEngine.run_scope` 不接受它）。要它的调用方须把类型收窄到具体 adapter（local 无状态
        路径的 `SubprocessLauncher` 即如此），别经 `Engine` 标注调它——那样换 adapter 只在运行时 TypeError。
        """
        ...


# EngineResolver：按 job.engine 解析出 Engine（schedule 对引擎数/引擎名无知，ADR 0026）
class EngineResolver(Protocol):
    def __call__(self, engine_name: str) -> Engine: ...


# Sink：接收 ADR 0024 原始流式事件的回调（pass-through，供进度/落地；与 RunResult 是同一事件流的两个视图，ADR 0026）
class Sink(Protocol):
    def __call__(self, event: Event) -> None: ...


# JobSink：每个 job 完成时的回调，收 schedule **已归约好的** JobResult（非原始 Event）——供实时落库（ADR 0030 决定一）。
# 与 Sink 同性质（都是注入回调、可注入 no-op、schedule 不碰 store），但粒度是「整 job 完成」而非「单个事件」。
# schedule 在 as_completed 主线程串行 fire，故实现无需自己加锁。
class JobSink(Protocol):
    def __call__(self, job: JobResult) -> None: ...


# ============================================================================
# 状态/结果/报告 port（ADR 0016 三层切分）。local adapter 均已建：RunStore 落 RunMeta(definition)+
# RunState(运行态)；ResultStore 落 JobResult(判定真值)；ReportStore 归集 RunReport(0027)。控制面的 jobId
# 仍 defer（待真实需求逼出）；起止时刻 / DDB 表 / 轮询读取面已由 v1.2 落地（ADR 0016/0034）。
# ============================================================================


class RunStore(Protocol):
    """控制面：一次 run 的 **definition（RunMeta）+ 运行态（RunState）**，不存判定明细（ADR 0016 三层切分）。

    definition（run_id/created_at/跑哪些 job）执行前确定；运行态（总 status/各 job status/血缘/起止）
    执行后产生。判定明细真值在 ResultStore（不在此）。local adapter = LocalRunStore（落 run_meta.json + run_state.json）。

    实时写（ADR 0030）：run 生命周期按三段落库——create_run（开始：写 definition + 初始全 pending 态）→
    update_job_state（每 job 起跑/完成：按 scope_id 刷单个 JobState）→ finalize_run（commit point：写总 status + ended_at）。
    save_run 保留作「一次性写完整态」便捷方法（可由 create_run+finalize 组合）。
    """

    # —— 实时写三段（ADR 0030，同步 run 路径；单进程内 RunPersistence._lock 串行、不带条件）——
    def create_run(self, meta: RunMeta, initial_state: RunState) -> None: ...
    def update_job_state(self, run_id: str, job_state: JobState) -> None: ...
    def finalize_run(self, run_id: str, status: Status, ended_at: str) -> None: ...
    # —— 一次性写便捷方法（保留）——
    def save_run(self, meta: RunMeta, state: RunState) -> None: ...
    def load_run_meta(self, run_id: str) -> RunMeta | None: ...
    def load_run_state(self, run_id: str) -> RunState | None: ...
    # —— 探活（ADR 0030 决定七）：begin 前探底层可达（云端探表/桶），配置错一律 begin 暴露→退 2；
    #    local adapter no-op（本地无「表不存在」问题）。RunPersistence.begin 在 create_run 前调。——
    def preflight(self) -> None: ...

    # —— 无状态跑批的条件写三方（ADR 0034；reconciler 跨进程/跨实例并发调用，靠条件写而非进程内锁）——
    # 与上面「实时写三段」并存、职责不同：那三段假定单编排进程内锁串行；这三方假定并发多写者、
    # 每个方法自身是原子条件写、返回是否成功让调用方（reconciler）据此决定要不要 RunTask/收尾。
    def try_claim_job(self, run_id: str, scope_id: str, *, claimed_at: str | None = None) -> bool:
        """CAS 抢占：仅当该 job 当前是 PENDING 才置 RUNNING，成功返回 True（机制四）。

        多个 reconciler 实例并发抢同一 pending job，只有一个 CAS 成功（返回 True）去真 RunTask/spawn，
        其余返回 False 跳过——严格 max_concurrency 的并发闸（不靠进程内线程池）。job 不存在/已非 pending → False。

        claimed_at（ISO 串，调用方注入时钟）：CAS 成功时随写 JobState.claimed_at——job timeout 的起算点
        （ADR 0034「job timeout」节：local 接力恢复 deadline / cloud tick 防御性超时扫 / status 显示时长）。
        """
        ...

    def project_state(self, run_id: str, state: RunState) -> bool:
        """HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。

        stale 实例（读到更少 events、hwm 更小）的写被挡（返回 False），防把已推进的态覆盖回旧态。
        state.high_water_mark 为 None 按 0 处理（最弱守卫：库中 hwm>0 时必被挡）——reconciler 路径恒带 hwm，
        不该走到这里。
        """
        ...

    def try_finalize(self, run_id: str, status: Status, ended_at: str) -> bool:
        """状态机单调条件写：仅当 run 总 status 当前为非终态（pending/running）才写终态，成功 True（机制三）。

        挡「已 finalize 的 run 被 stale 投影刷回」+ 保 commit 恰一次（多实例同时见全终态、只有一个写成功、
        触发一次 RunReport 聚合）。已是终态 → False（幂等：别人已 finalize）。
        """
        ...


class ResultStore(Protocol):
    """数据面：每 job(=scope) 判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它，ADR 0016）。

    local adapter = LocalResultStore（每 job 落 <root>/<run_id>/jobs/<encoded_scope_id>.json）。
    """

    def save_job_result(self, run_id: str, job: JobResult) -> None: ...
    def load_job_result(self, run_id: str, scope_id: str) -> JobResult | None: ...
    def load_all(self, run_id: str) -> list[JobResult]: ...
    def preflight(self) -> None: ...  # 探活（ADR 0030 决定七）：云端探桶、local no-op


class ReportStore(Protocol):
    """归集报告产物为一份**派生只读导航视图**（RunReport，ADR 0027）：manifest.json + index.html。

    纯派生：可从 RunResult 完全重建，**永不作 CI 判定源**（判定真值在 RunResult/ResultStore）。
    读 report_refs + 各级 status/时长/成本 + step 级 votes/error_type/shortcircuited 渲染「人看」视图；
    不拿产物内容、不按 kind 分支（不透明搬运，ADR 0027）。
    """

    def write(self, run_id: str, result: RunResult, *, created_at: str = "") -> ResourceUri:
        """从 RunResult 归集出 <report_root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 ResourceUri。

        返回 ResourceUri 而非 Path：本地 adapter 回 file://…/index.html，S3 adapter 回 s3://…/index.html
        ——同一签名容两种落点，消费端（cli/WebUI）只当 URI 用（不 stat/open）。这统一了 ReportRef.ref 与
        本方法返回值的语义：都是「带 scheme 的资源指针」（ADR 0027）。

        created_at: 组合根生成的时间戳字符串（core 不取时钟；进 manifest 信封）。

        index.html 的导航链接（href）指向产物原位、不拷贝产物：local adapter 把 run 树内的 file:// 产物
        相对化（目录可整体搬走、链接不断）、否则 ==ref；S3 adapter 恒 ==ref。href 是 core 自算的导航链接、
        不受不透明铁律约束；ref 永远原样保留（铁律圈的是 ref，ADR 0027）。（产物拷贝式 materialize 已否决。）
        """
        ...

    def preflight(self) -> None: ...  # 探活（ADR 0030 决定七）：云端探桶、local no-op
