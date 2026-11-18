"""核心注入接口（ADR 0016，业界称 ports & adapters）：核心的主要注入口在此（另两个见末段），具体 adapter 由组合根注入。

四个 port（关注点拆开，不揉成上帝 module）：
- Engine        —— 真正运行一个 scope（spawn worker、讲 ADR 0024 协议）；adapter 有子进程与 Fargate 两种
- RunStore      —— 控制面：run/job 状态、血缘、起止（频繁读写，撑轮询接力与无状态批量运行的条件写）
- ResultStore   —— 数据面：每 scenario 判定真值、投票（追加为主）
- ReportStore   —— 归集报告产物为派生只读导航视图（RunReport：manifest + index，ADR 0027）

另有调度循环用的回调与能力类型（EngineResolver / Sink / JobSink / RunRecord），同样由组合根注入；RunRecord 的实现是 core 自己的落库服务
`persist.RunPersistence`，不是 adapter。

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

from datetime import datetime
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

    不暴露进程/信号细节——「怎么停」的机制藏在 adapter 内部：子进程 SIGTERM→宽限→SIGKILL（真用运行期 grace）；
    Fargate `StopTask`（忽略运行期 grace 入参，宽限由 task-def 期 `stopTimeout` 定）。
    """

    def stop(self, grace_period_s: float) -> None:
        """请求优雅停止：adapter 内部翻成具体机制；worker 收到后停会话、退出（ADR 0024 终止契约）。"""
        ...


class Engine(Protocol):
    """执行引擎 port。

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
        未解析的行落持久 events sink）——那是**该 adapter 的扩展形参、不在 port 契约内**（`FargateEngine.run_scope`
        不接受它）。要它的调用方须把类型收窄到具体 adapter（local 无状态
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


# RunRecord：调度循环服从这次 run 的记录所用的三项能力（ADR 0054 决策五「执行方服从记录」）。schedule 不碰 store（ADR 0030
# 决定一），有记录的执行由组合根注入落库服务（`RunPersistence` 实现本协议），没有记录的执行（`run --no-report`、测试）不注入。
class RunRecord(Protocol):
    def claim(self, scope_id: str, claimed_at: datetime) -> bool:
        """认领一个 job：只在 run 级未结束、这个 job 仍为 pending 时成立，认领时刻随认领写进运行态。每个 job 只在第一次起 worker
        之前调一次，claimed_at 是调用方在这次调用之前取的墙钟。返回 False 即认领被拒，调用方按「run 已被别处记为已结束」处理。
        存储不可达等失败照常抛出，调用方按运行期落库失败处理。"""
        ...

    def still_open(self) -> bool:
        """读一次 run 级状态：pending 或 running 时为 True，已是终态为 False。job 级重试重新起 worker 之前调用（重试不再认领）。
        读取失败照常抛出。"""
        ...

    def ended_elsewhere(self) -> bool:
        """停手信号：是否已发现这个 run 被别处记为已结束。认领被拒、`still_open` 读到终态、写 job 状态时得知 run 级已结束，三处的
        发现都汇到这里，成立之后不再撤销。写 job 状态时的发现要在那次落库回调返回之前成立：调度循环在回调返回之后当场读它，据此
        确定中止来源的先后。只读进程内的标记、不碰存储，调用方可以频繁轮询。"""
        ...


# ============================================================================
# 状态/结果/报告 port（ADR 0016 三层切分）。local adapter 均已建：RunStore 落 RunMeta(definition)+
# RunState(运行态)；ResultStore 落 JobResult(判定真值)；ReportStore 归集 RunReport(0027)。控制面的 jobId
# 仍 defer（待真实需求逼出）；起止时刻 / DDB 表 / 轮询读取面已由 v1.2 落地（ADR 0016/0034）。
# ============================================================================


class RunStore(Protocol):
    """控制面：一次 run 的 **definition（RunMeta）+ 运行态（RunState）**，不存判定明细（ADR 0016 三层切分）。

    definition（run_id/created_at/执行哪些 job）执行前确定；运行态（总 status/各 job status/血缘/起止）
    执行后产生。判定明细真值在 ResultStore（不在此）。local adapter 是 LocalRunStore（落 run_meta.json + run_state.json）。

    生命周期：create_run（开始：写 definition + 初始全 pending 态）→ update_job_state（每 job 开始运行/完成：按
    scope_id 刷单个 JobState）→ try_finalize（commit point：以条件写落定总 status + ended_at）。前台执行（同步 `run`）与后台推进
    （reconciler）用同一组写入口；两者起 worker 之前都先经 try_claim_job 认领（前台每个 job 只认领一次，ADR 0054 决策五），后台推进另用 project_state。

    **每个写入口对并发的别的写入方都是安全的**，调用方不靠进程内的锁保证正确：同一个 run 可能同时有多个写入方（前台执行者
    之外，还有后台推进的多个实例与接力者），本机 adapter 在文件锁内读改写、云端 adapter 的每一次写都带条件。这不是事务保证：
    create_run 分两次写（definition 在前、运行态在后），云端的 project_state 先写标量、再逐 job 写；中间态对读的一方可见，
    中途失败时已写成的部分留在库里。**run 级终态不可变**
    （ADR 0054 决策五）：run 级状态只从 pending 到 running 再到终态，到了终态任何写入口都不再改它；没有无条件改写终态或整份
    重写运行态的入口。
    """

    # —— 生命周期写入口 ——
    def create_run(self, meta: RunMeta, initial_state: RunState) -> None:
        """写 definition 与初始运行态，只在这个 run 还不存在时成立（ADR 0054 决策五）：run 已存在则抛 FileExistsError、
        不改任何东西（本机的判据是 run 目录里已有运行态文件，云端是 META 或 STATE 条目已在）。初始运行态原样写入，新建的
        运行态各 job 为 pending、认领计数为 0。
        """
        ...

    def update_job_state(self, run_id: str, job_state: JobState) -> bool:
        """按 scope_id 写单个 job 的运行态；运行态不存在则抛 FileNotFoundError（须先 create_run）。

        写入的 job 态不是 PENDING 时，同一次写把未收尾的 run 级推进为 RUNNING；run 已收尾时 job 照写、run 级不变。
        写入 PENDING 时只写 job。调用方不需要记「是否第一次」。
        认领计数、HWM、起止时刻与 run 级 message 不变。

        返回 run 级在这次写时是否仍未结束：True 表示 job 落下的那一刻 run 级为 pending 或 running，False 表示
        run 级已是终态、这次只写了 job。对写入的任何 job 态（含 PENDING）都按写的那一刻如实给出，不是写前另读一次的结果。前台执行者
        据 False 得知 run 已被别处记为已结束、停止启动新的 job；不关心的调用方可以忽略。
        """
        ...

    def try_finalize(self, run_id: str, status: Status, ended_at: str, *, message: str | None = None,
                     expected_claim_count: int | None = None) -> bool:
        """收尾（commit point）：仅当 run 总 status 当前为非终态（pending/running）才写终态与 ended_at，成功 True。

        所有写入方共用这一个收尾入口（前台执行者与后台推进）：已是终态 → False，库中值不变，保证 commit
        恰一次（多实例同时见全终态、只有一个写成功、触发一次 RunReport 聚合）。运行态不存在同样 → False，两种原因不区分。
        message 是 run 级消息：没有任何 job 能承载的原因，与终态同一次写入——推进器不经任何 job 就把 run
        置为终态时的原因，或执行方按运行期限收尾时的「已超过允许运行的时间」；按各 job 判定聚合的
        收尾不给；为 None 时不写这一项，库中值原样保留。

        expected_claim_count：给出时另要求库中的认领计数等于它，判定自调用方读到运行态以来
        没有新的认领；不等 → False、不写。为 None 时不判计数。认领计数本身不变。
        """
        ...

    def load_run_meta(self, run_id: str) -> RunMeta | None: ...
    def load_run_state(self, run_id: str) -> RunState | None: ...
    # —— definition 的结构版本与写端版本（ADR 0037 决策 7）：status / explain 在读任何别的东西之前先核它，只取这两个值、
    #    不读整份 definition（云端 META 可能带 S3 卸载指针，整读会多一次 S3 取回与一份权限）。run 不存在返回 None；
    #    缺结构版本号读作 0（早于结构版本号的写端）。——
    def peek_definition_header(self, run_id: str) -> tuple[int, str | None] | None: ...

    # —— 列举（ADR 0041 决策七「core 端口」）：`list-runs` 用，只读 ——
    def list_runs(self, statuses: Sequence[Status], *, limit: int | None) -> list[RunListing]:
        """列出经这些状态找到的 run，每项带读回的**当前**运行态、detached 标记与提交记录头部，按 run_id 降序、run_id 不重复。

        - **找**：云端按状态分组查索引：所请求的非终态共用一个分组、只查一次，所请求的终态各查同名的分组；本机没有索引，逐个 run
          目录读回后按读回的状态归入。`limit` 为正整数时每个状态取按 run_id 降序的前 `limit` 条可读的 run（云端在分组里补读到
          凑满或分组读完为止；非终态共用分组时按读回的状态分别计各状态的名额），为 None 时不截断。
        - **不按状态复筛**：返回的是读回时的状态，可能已不在 `statuses` 里（找到之后、读回之前换了状态，或云端索引尚未跟上），
          按所请求状态过滤是调用方的事。复筛会让两次调用之间换状态的 run 在两份结果里都被筛掉。**例外适用于经非终态分组找到的行**：读回为
          未被请求的非终态的行不列出（如只请求 pending 时读回为 running 的行）；读回已到终态的行照常列出、不计入非终态的名额。
          同一个 run 也经所请求的终态分组找到时，仍按终态分组不复筛的规则列出。本机本来就按读回的状态归入，两端规则相同。
        - **无法读取的行**（`RunListing.state` 为 None）没有可用的状态，不参与归入与截取、不占 `limit` 的名额，找到即列出：
          云端是被查分组里凑满名额之前遇到的、读回解析不了的 run；本机是读回解析不了的全部 run 目录（状态值本版本不认识的 run
          本机都看得到；云端只看得到非终态的那些，前提是写出它的版本沿用同一分组规则）。
        - **一致性**：云端行内容强一致（读回走强一致读），成员资格最终一致（索引只有最终一致读）：刚收尾的 run 可能短暂仍在
          非终态的分组、刚建的 run 可能短暂不在任何分组；读回时 run 已不在（运行态缺失）的行跳过。
        - **访问失败照常抛出**（本机目录不可读、云端权限 / 网络 / 索引缺失、批量读回重试耗尽），不给出缺行的清单。本机报告落点
          目录不存在时返回空列表。

        端口不认后端、不承载默认清单的口径（列哪些状态、终态取几条、两次调用怎么合并都在调用方）。
        """
        ...

    # —— 探活（ADR 0030 决定七）：begin 前探底层可达（云端探表/桶），配置错一律 begin 暴露 → 以退出码 2 结束；
    #    local adapter no-op（本地无「表不存在」问题）。RunPersistence.begin 在 create_run 前调。——
    def preflight(self) -> None: ...

    # —— 认领与投影（认领由前台执行者与后台推进共用，后台推进跨进程/跨实例并发调用）——
    # 返回是否写成，调用方（前台的落库服务、后台的 reconciler）据此决定要不要起 worker。
    def try_claim_job(self, run_id: str, scope_id: str, *, claimed_at: str | None = None) -> bool:
        """认领：仅当该 job 当前是 PENDING 且 run 未收尾才置 RUNNING，成功返回 True（机制四）。

        多个 reconciler 实例并发认领同一 pending job，只有一个 CAS 成功（返回 True）去真 RunTask/spawn，
        其余返回 False 跳过——严格 max_concurrency 的并发闸（不靠进程内线程池）。job 不存在/已非 pending/run 已收尾
        （run 级为终态）→ False，三种原因不区分。
        同一条条件写把 run 级置 RUNNING（ADR 0034 机制三「run 级状态只进不退」条①）：认领成功后 run 级即为 RUNNING；
        run 已收尾后不再接受新认领，此前已成功的认领不由此撤销。HWM 不变。
        认领成功时同一次写把认领计数加一（ADR 0034 机制三「run 级状态只进不退」条①）；认领失败不改它。

        claimed_at（ISO 串，调用方注入时钟）：CAS 成功时随写 JobState.claimed_at——job timeout 的起算点
        （local 接力恢复 deadline / cloud tick 防御性超时扫 / status 显示时长）。
        """
        ...

    def project_state(self, run_id: str, state: RunState) -> bool:
        """HWM 条件写投影：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。

        写入的只有 HWM、run 级 status（按下段规则）与各 job 态；state 上的 started_at、ended_at、message、认领计数不用，
        库中值原样保留。
        stale 实例（读到更少 events、hwm 更小）的写被挡（返回 False），防把已推进的态覆盖回旧态。
        state.high_water_mark 为 None 按 0 处理，守卫与落库都用 0（最弱守卫：库中 hwm>0 时必被挡）——reconciler 路径恒带 hwm，
        不该走到这里。库中 run 级已是终态时同样被挡（返回 False）。

        传入的 run 级 status 不落库：投影里任一 job 已离开 PENDING 时 run 级写 RUNNING，全 job 仍 PENDING 时不写 run 级、
        保留库中值，因而不会把认领写成的 RUNNING 改回 PENDING（取值规则见 `project.projected_run_status`）。
        各 job 态与库中现态按生命周期序逐 job 单调合并（机制三②）。
        """
        ...


class ResultStore(Protocol):
    """数据面：每 job（即 scope）判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它）。

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
