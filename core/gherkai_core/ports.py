"""核心注入接口（ADR 0016，业界称 ports & adapters）：核心的主要注入口在此（另两个见末段），具体 adapter 由组合根注入。

四个 port（关注点拆开，不揉成上帝 module）：
- Engine        —— 真正运行一个 scope（spawn worker、讲 ADR 0024 协议）；adapter 有子进程与 Fargate 两种
- RunStore      —— 控制面：run/job 状态、血缘、起止（频繁读写，撑轮询接力与无状态批量运行的条件写）
- ResultStore   —— 数据面：每 scenario 判定真值、投票（追加为主）
- ReportStore   —— 归集报告产物为派生只读导航视图（RunReport：manifest + index，ADR 0027）

禁止：port 内部 env-sniff 自选实现（Midscene GlobalConfigManager 反模式）。adapter 一律组合根注入。
接口先定（逼清边界）；四个 port 的 local + 云端 adapter 均已实装（RunStore: local/ddb、Result/ReportStore:
local/s3、Engine: subprocess/fargate），组合根按 `--backend` 注入。

**另两个 port 不在本模块**：`EventLog` 与 `Launcher` 定义在 `reconcile.py`、与消费它们的 reconciler 同处——
两个 port 的推进语义（reconciler 读全量 events 重放、认领成功后起一个 job）只服务无状态推进路径，与本模块那批
「同步 `run` 也用」的口生命周期不同；`EventLog` 的实装另被同步 `run` 用来落事件流与退出记录（组合根给引擎包一层
`EventRecordingEngine`，ADR 0042 决策七）、被 `explain` 用来读（本机 `SqliteEventLog`、云端 `DdbEventLog`）
（ADR 0016「`EventLog` / `Launcher` 两个 port 定义在 `reconcile.py`」条；
亦见 ADR 0034「Engine port 演进」）。同样组合根注入、各两个实装：
`EventLog` 的实装是 `adapters/event_log/sqlite.py`（local）与 `adapters/event_log/ddb.py`（cloud）；`Launcher` 的
实装是 `runtime/gherkai_runtime/detached.py` 的 `SubprocessLauncher`（local）与 `adapters/cloud_launcher.py` 的
`CloudLauncher`（cloud）。盘点 core 的注入接缝时**两处都要看**。
"""
from __future__ import annotations

from typing import Iterator, Protocol, Sequence

from gherkai_core.model import (
    Event,
    Job,
    JobResult,
    JobState,
    ResourceUri,
    RunListing,
    RunMeta,
    RunResult,
    RunState,
    Status,
)


# ============================================================================
# Engine port（ADR 0024/0026）：运行一个 scope，流式回事件，可优雅停
# ============================================================================


class WorkerHandle(Protocol):
    """一个正在运行的 worker 的句柄（schedule 持有，用于 stop）。

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
        """起一个 worker 运行这个 job，返回 (句柄, ADR 0024 事件流迭代器)。

        事件流逐条产出（ADR 0024 流式）；迭代结束表示 worker 正常退出。
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
# schedule 在主线程等待 job 完成的循环（`wait(FIRST_COMPLETED)`）里串行 fire，故实现无需自己加锁。
class JobSink(Protocol):
    def __call__(self, job: JobResult) -> None: ...


# ============================================================================
# 状态/结果/报告 port（ADR 0016 三层切分）。local adapter 均已建：RunStore 落 RunMeta(definition)+
# RunState(运行态)；ResultStore 落 JobResult(判定真值)；ReportStore 归集 RunReport(0027)。控制面的 jobId
# 仍 defer（待真实需求逼出）；起止时刻 / DDB 表 / 轮询读取面已由 v1.2 落地（ADR 0016/0034）。
# ============================================================================


class RunStore(Protocol):
    """控制面：一次 run 的 **definition（RunMeta）+ 运行态（RunState）**，不存判定明细（ADR 0016 三层切分）。

    definition（run_id/created_at/执行哪些 job）执行前确定；运行态（总 status/各 job status/血缘/起止）
    执行后产生。判定明细真值在 ResultStore（不在此）。local adapter 是 LocalRunStore（落 run_meta.json + run_state.json）。

    实时写（ADR 0030）：run 生命周期按三段落库——create_run（开始：写 definition + 初始全 pending 态）→
    update_job_state（每 job 开始运行/完成：按 scope_id 刷单个 JobState）→ finalize_run（commit point：写总 status + ended_at）。
    save_run 保留作「一次性写完整态」便捷方法（可由 create_run+finalize 组合）。
    """

    # —— 实时写三段（ADR 0030，同步 run 路径；单进程内 RunPersistence._lock 串行，调用方不需要条件写）——
    def create_run(self, meta: RunMeta, initial_state: RunState) -> None: ...
    def update_job_state(self, run_id: str, job_state: JobState) -> None:
        """按 scope_id 写单个 job 的运行态；运行态不存在则抛 FileNotFoundError（须先 create_run）。

        写入的 job 态不是 PENDING 时，同一次写把未收尾的 run 级推进为 RUNNING；run 已收尾时 job 照写、run 级不变
        （ADR 0034 机制三「run 级状态只进不退」条③）。写入 PENDING 时只写 job。调用方不需要记「是否第一次」。
        """
        ...

    def finalize_run(self, run_id: str, status: Status, ended_at: str) -> None: ...
    # —— 一次性写便捷方法（保留）——
    def save_run(self, meta: RunMeta, state: RunState) -> None: ...
    def load_run_meta(self, run_id: str) -> RunMeta | None: ...
    def load_run_state(self, run_id: str) -> RunState | None: ...
    # —— definition 的结构版本与写端版本（ADR 0037 决策 7）：status / explain 在读任何别的东西之前先核它，只取这两个值、
    #    不读整份 definition（云端 META 可能带 S3 卸载指针，整读会多一次 S3 取回与一份权限）。run 不存在返回 None；
    #    缺结构版本号读作 0（早于结构版本号的写端）。——
    def peek_definition_header(self, run_id: str) -> tuple[int, str | None] | None: ...

    # —— 列举（ADR 0041 决策七「core 端口」）：`list-runs` 用，只读 ——
    def list_runs(self, statuses: Sequence[Status], *, limit: int | None) -> list[RunListing]:
        """列出经这些状态找到的 run，每项带读回的**当前**运行态、detached 标记与提交记录头部，按 run_id 降序、run_id 不重复。

        - **找**：云端按 `statuses` 的给定顺序逐个查状态分区（调用方据此安排先查 pending 再查 running）；本机没有分区，逐个 run
          目录读回后按读回的状态归入。`limit` 为正整数时每个状态取按 run_id 降序的前 `limit` 条可读的 run（云端在分区里补读到
          凑满或分区读完为止），为 None 时不截断。
        - **不按状态复筛**：返回的是读回时的状态，可能已不在 `statuses` 里（找到之后、读回之前换了状态，或云端索引尚未跟上），
          按所请求状态过滤是调用方的事。复筛会让两次调用之间换状态的 run 在两份结果里都被筛掉。
        - **无法读取的行**（`RunListing.state` 为 None）没有可用的状态，不参与归入与截取、不占 `limit` 的名额，找到即列出：
          云端是被查分区里凑满名额之前遇到的、读回解析不了的 run；本机是读回解析不了的全部 run 目录（状态值本版本不认识的 run
          本机看得到、云端看不到）。
        - **一致性**：云端行内容强一致（读回走强一致读），成员资格最终一致（索引只有最终一致读）：刚换状态的 run 可能短暂仍在旧
          分区、刚建的 run 可能短暂不在任何分区；读回时 run 已不在（运行态缺失）的行跳过。
        - **访问失败照常抛出**（本机目录不可读、云端权限 / 网络 / 索引缺失、批量读回重试耗尽），不给出缺行的清单。本机报告落点
          目录不存在时返回空列表。

        端口不认后端、不承载默认清单的口径（列哪些状态、终态取几条、两次调用怎么合并都在调用方）。
        """
        ...

    # —— 探活（ADR 0030 决定七）：begin 前探底层可达（云端探表/桶），配置错一律 begin 暴露 → 以退出码 2 结束；
    #    local adapter no-op（本地无「表不存在」问题）。RunPersistence.begin 在 create_run 前调。——
    def preflight(self) -> None: ...

    # —— 无状态批量运行的条件写三方（ADR 0034；reconciler 跨进程/跨实例并发调用，靠条件写而非进程内锁）——
    # 与上面「实时写三段」并存、职责不同：那三段假定单编排进程内锁串行；这三方假定并发多写者、
    # 每个方法自身是原子条件写、返回是否成功让调用方（reconciler）据此决定要不要 RunTask/收尾。
    def try_claim_job(self, run_id: str, scope_id: str, *, claimed_at: str | None = None) -> bool:
        """认领：仅当该 job 当前是 PENDING 且 run 未收尾才置 RUNNING，成功返回 True（机制四）。

        多个 reconciler 实例并发认领同一 pending job，只有一个 CAS 成功（返回 True）去真 RunTask/spawn，
        其余返回 False 跳过——严格 max_concurrency 的并发闸（不靠进程内线程池）。job 不存在/已非 pending/run 已收尾
        （run 级为终态）→ False，三种原因不区分。
        同一条条件写把 run 级置 RUNNING（ADR 0034 机制三「run 级状态只进不退」条①）：认领成功后 run 级即为 RUNNING；
        run 已收尾后不再接受新认领，此前已成功的认领不由此撤销。HWM 不变。

        claimed_at（ISO 串，调用方注入时钟）：CAS 成功时随写 JobState.claimed_at——job timeout 的起算点
        （ADR 0034「job timeout」节：local 接力恢复 deadline / cloud tick 防御性超时扫 / status 显示时长）。
        """
        ...

    def project_state(self, run_id: str, state: RunState) -> bool:
        """HWM 条件写投影：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。

        写入的只有 HWM、run 级 status（按下段规则）与各 job 态；state 上的 started_at、ended_at、message 不用，库中值原样保留。
        stale 实例（读到更少 events、hwm 更小）的写被挡（返回 False），防把已推进的态覆盖回旧态。
        state.high_water_mark 为 None 按 0 处理，守卫与落库都用 0（最弱守卫：库中 hwm>0 时必被挡）——reconciler 路径恒带 hwm，
        不该走到这里。库中 run 级已是终态时同样被挡（返回 False）。

        传入的 run 级 status 不落库：投影里任一 job 已离开 PENDING 时 run 级写 RUNNING，全 job 仍 PENDING 时不写 run 级、
        保留库中值，因而不会把认领写成的 RUNNING 改回 PENDING（取值规则见 `project.projected_run_status`，ADR 0034
        机制三「run 级状态只进不退」条②）。各 job 态与库中现态按生命周期序逐 job 单调合并（机制三②）。
        """
        ...

    def try_finalize(self, run_id: str, status: Status, ended_at: str, *, message: str | None = None) -> bool:
        """状态机单调条件写：仅当 run 总 status 当前为非终态（pending/running）才写终态，成功 True（机制三）。

        挡「已 finalize 的 run 被 stale 投影刷回」+ 保 commit 恰一次（多实例同时见全终态、只有一个写成功、
        触发一次 RunReport 聚合）。已是终态 → False（幂等：别人已 finalize）。
        message 是 run 级消息（ADR 0037 决策 7）：推进器不经任何 job 就把 run 置为终态时的原因，与终态同一次写入；
        正常收尾不给；为 None 时不写这一项，库中值原样保留。
        """
        ...


class ResultStore(Protocol):
    """数据面：每 job（即 scope）判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它，ADR 0016）。

    local adapter 是 LocalResultStore（每 job 落 <root>/<run_id>/jobs/<encoded_scope_id>.json）。
    """

    def save_job_result(self, run_id: str, job: JobResult) -> None: ...
    def load_job_result(self, run_id: str, scope_id: str) -> JobResult | None: ...
    def load_all(self, run_id: str) -> list[JobResult]: ...
    def preflight(self) -> None: ...  # 探活（ADR 0030 决定七）：云端探桶、local no-op


class ReportStore(Protocol):
    """归集报告产物为一份**派生只读导航视图**（RunReport，ADR 0027）：manifest.json + index.html。

    纯派生：可从 RunResult 完全重建，**永不作 CI 判定源**（判定真值在 RunResult/ResultStore）。
    读 report_refs + 各级标识（scope_id/scenario_id/step index）与 status/时长/成本 + job 级 engine/session_id
    + job/step 级 error_type·message（失败原因原文；step 级 message 见 ADR 0042 决策三）+ step 级 votes/shortcircuited 渲染「人看」视图；
    不拿产物内容、不按 kind 分支（不透明搬运，ADR 0027）。
    """

    def write(self, run_id: str, result: RunResult, *, created_at: str = "") -> ResourceUri:
        """从 RunResult 归集出 <report_root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 ResourceUri。

        返回 ResourceUri 而非 Path：本地 adapter 回 file://…/index.html，S3 adapter 回 s3://…/index.html
        ——同一签名容两种落点，消费端（cli/WebUI）只当 URI 用（不 stat/open）。这统一了 ReportRef.ref 与
        本方法返回值的语义：都是「带 scheme 的资源指针」（ADR 0027）。

        created_at: 组合根生成的时间戳字符串（core 不取时钟；进 manifest 信封）。

        index.html 的导航链接（href）指向产物原位、不拷贝产物：local adapter 把 run 树内的 file:// 产物
        相对化（目录可整体搬走、链接不断），其余情形 href 等于 ref；S3 adapter 的 href 恒等于 ref。href 是 core 自算的导航链接、
        不受不透明铁律约束；ref 永远原样保留（铁律圈的是 ref，ADR 0027）。（产物拷贝式 materialize 已否决。）
        """
        ...

    def preflight(self) -> None: ...  # 探活（ADR 0030 决定七）：云端探桶、local no-op
