"""领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。

无逻辑、无 I/O——只是 core 各模块之间、core↔worker 之间传递的形状。
parse 产出 Scenario/Step；scope 组装 Job；worker 回 Event 流；schedule 归约成 RunResult。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, NewType

# 资源 URI：带 scheme 的统一资源指针（本地 file://、未来云端 s3://、https://）。
# 把一个本就存在的约定（见 ReportRef.ref / ReportStore.write）提升成命名类型——比裸 str
# 多一层意图（「这是带 scheme 的 URI、不是本地路径」），又不像 pathlib.Path 那样会把 s3:// 折坏
# （Path("s3://b/x") → "s3:/b/x"）。零运行时成本、零依赖：NewType 仅供命名/静态意图，运行时即 str。
ResourceUri = NewType("ResourceUri", str)

# ============================================================================
# 输入侧：plan(ADR 0025) 产出、喂给 worker(ADR 0024 输入) 的形状
# ============================================================================


@dataclass(frozen=True)
class StepArgument:
    """step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。

    不透传 gherkin pickle 的子 dict 形状（`{docString:{content}}` / `{dataTable:{rows:[{cells:[{value}]}]}}`），
    归一成下面两种之一：kind="docString" 用 content；kind="dataTable" 用 rows（行×单元格的纯字符串二维表）。
    """

    kind: Literal["docString", "dataTable"]
    content: str | None = None  # docString 时有
    rows: tuple[tuple[str, ...], ...] | None = None  # dataTable 时有


@dataclass(frozen=True)
class Step:
    """一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。"""

    index: int  # scenario 内 0-based 书写序号（parse 合成；pickle 无此字段），回指键、不参与重排
    keyword: Literal["Given", "When", "Then"]  # 由 pickle type(Context/Action/Outcome) 映射
    text: str
    argument: StepArgument | None = None


@dataclass(frozen=True)
class Scenario:
    """一个 scenario（Outline 已展开成独立 Scenario，ADR 0025）。"""

    id: str  # <uri>:<行号>[:<example行号>]，RunStore/RunReport 关联键
    name: str  # 标题（已插值；Outline 多个加 Examples 行标识以可区分）
    steps: tuple[Step, ...]


@dataclass(frozen=True)
class Job:
    """一个 job = 一个 scope = 一个会话边界 = schedule 交给单个 worker 的活（ADR 0016/0024/0025）。"""

    scope_id: str  # 有 @scope:X 用 X；无标用 scenario 的 id
    scope_name: str  # @scope 原值（人写名）；无标用 scenario 标题
    engine: str  # 已完成冲突校验的引擎名（如 "midscene"/"novaact"）
    scenarios: tuple[Scenario, ...]
    # AI 断言（Then）投票次数（治种类A抖动，ADR 0014）：worker 跑该断言 N 次取多数票。
    # 默认 1（不抖动检测，结果/日志最直观）；调高（如 3/5）才启用抖动治理。组合根经 --assertion-votes 设。
    assertion_votes: int = 1
    # job 墙钟预算秒（ADR 0034「job timeout」节）：@timeout:N tag 或组合根填充的 --default-job-timeout；
    # None=不超时。载体=definition（timeout 是「要跑什么」的预算约束），推进器各自 enforce、worker 不消费。
    timeout_s: float | None = None


# ============================================================================
# 成本信封（ADR 0024）：engine 只报原生量（tokens / time_worked_s），core 只合计、不折美元
# ============================================================================


@dataclass(frozen=True)
class Cost:
    """step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。

    原则：core 不算、不折美元、不判可信度——engine 提供什么就报什么，core 只各自合计。
    哪个量有值，本身就说明该 engine 按什么计费（Nova 报 time_worked_s、Midscene 报 tokens）；
    美元折算交给消费者（用自己 AWS 账户的真实费率），框架不追会过期的单价表。
    """

    tokens: int | None = None          # LLM token 用量（Midscene/Bedrock 原生给；Nova 拿不到）
    time_worked_s: float | None = None  # agent 工作时长秒（Nova SDK 原生给；Midscene 无此概念）


# ============================================================================
# 输出侧：worker → core 的流式事件（ADR 0024，JSON Lines）
# ============================================================================


class Status(str, Enum):
    """判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。

    worker 经 wire 只报前三态（passed/failed/error，ADR 0024）；后四态是 **core 内态、永不进 wire**：
    - skipped/aborted：fail-fast 派生的 job 级**终态**（ADR 0031 决定一）。
    - pending/running：实时写的 job 级**生命周期前置态**（ADR 0031 决定一·补），只活在 JobState/RunState，
      不进 JobResult.status（终态判定只会是 passed/failed/error/skipped/aborted）、不参与 severity 比较。
    """

    PASSED = "passed"  # 测试通过
    FAILED = "failed"  # 断言投票没过 = 测试发现了问题
    ERROR = "error"  # 引擎抛异常 = 没能跑完测试
    SKIPPED = "skipped"  # core 派生终态：fail-fast 下 worker 从未 spawn。没执行/没花钱/可无脑重跑（ADR 0031）
    ABORTED = "aborted"  # core 派生终态：fail-fast 下跑一半被掐。有副作用/有现场可查（ADR 0031）
    PENDING = "pending"  # 前置态：run 开始 create_run 时占位（ADR 0030/0031）
    RUNNING = "running"  # 前置态：worker 起了、收到 scope_started 后刷（ADR 0030/0031）


# severity 数值序（ADR 0031 决定二）：**仅用于终态**的比较/排序/单调聚合。
# 钉死 'error'<'failed' 字母序反向坑——绝不拿 Status 字符串比大小，一律查这张表。
# 前置态 pending/running 不在此表（它们不是判定结论，不参与 severity 比较，见 _NON_VERDICT）。
_STATUS_SEVERITY: dict[Status, int] = {
    Status.SKIPPED: -1,  # 最轻：没执行，最该被无视
    Status.PASSED: 0,
    Status.FAILED: 1,
    Status.ERROR: 2,
    Status.ABORTED: 3,  # 最重：有现场，最该被人看
}

# run 级聚合的过滤名单（ADR 0031 决定三）：终态判定之外的态都不进 run 级聚合。
# 含 skipped/aborted（派生终态、单写者、必伴随 error 同批，见 ADR 0031）+ pending/running（前置态）。
# 两路共用（ADR 0031 决定三 / 0034）：schedule 沿事件流实时聚合，喂的都是终态、过滤是 no-op；
# project 的无状态投影真实喂入 pending/running（未起/在跑的 job），此处过滤**承重**——否则前置态会污染
# run 级 status。
_NON_VERDICT: frozenset[Status] = frozenset(
    {Status.SKIPPED, Status.ABORTED, Status.PENDING, Status.RUNNING}
)


def severity(status: Status) -> int:
    """终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。"""
    return _STATUS_SEVERITY[status]


# errorType 规范化类别集（ADR 0024，可随真实失败样本扩充）。
# 本 Literal 是协议类别集的**单一事实源**（ADR 0024/0028），有意**不作字段注解**——wire 需容忍 worker
# 报的未知类别（引擎先报、core 后补枚举，不能反序列化即炸），故各 error_type 字段一律标 str | None。
ErrorType = Literal[
    "assertion_failed",  # failed 态：断言没过
    "timeout",  # error 态：超时
    "guardrail",  # error 态：引擎护栏拦截
    "engine_error",  # error 态：引擎内部/通用异常（Midscene 通用 Error 归此）
    "navigation_error",  # error 态：导航失败
    "network_error",  # error 态：网络/SSL/连接层瞬时故障（建连失败，可重试，ADR 0028）
]


@dataclass(frozen=True)
class Votes:
    """AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。"""

    yes: int
    total: int


@dataclass(frozen=True)
class ReportRef:
    """原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、
    不 stat/fetch ref、不按 kind 分支。新引擎报任意 kind 都零改 core（扩展性契约）。

    kind:  **产物类型**（开放字符串，引擎自报）。约定值 "report"（完整报告页）/"trajectory"（轨迹页）/
           "summary"（数字汇总），未来可 "video"/"trace"/"har"…（非枚举）。**粒度不由 kind 表达**，而由
           report_ref 挂在 StepResult/ScenarioResult/JobResult 哪一级表达（二者正交，ADR 0027）。
    ref:   统一指针 URI（ResourceUri）——不假定是本地文件。本地产物用 file:// 前缀；未来可 s3://、https://。
    label: 可选人类可读锚文本；缺省由消费端（cli/WebUI 皮层）回落 kind。
    """

    kind: str
    ref: ResourceUri
    label: str | None = None


# --- 事件（worker 按序流式 emit；core 假定有序，ADR 0024）---
# 三级 started/done 对齐：scope_started/scenario_started/step_started 与各自 *_done 配对。
# started 事件让 core 用事件到达时间戳算各级墙钟时长（性能指标，与 cost 正交）。


@dataclass(frozen=True)
class ScopeStarted:
    scope_id: str
    # 会话血缘随**首个**事件即回传（不再等 scope_done）——这样超时/SIGTERM 中途打断、scope_done
    # 从未 emit 时，core 仍能记下 session_id（诊断/计费血缘，ADR 0024/0028）。scope_done 仍带它（冗余兜底）。
    session_id: str | None = None
    type: Literal["scope_started"] = "scope_started"


@dataclass(frozen=True)
class ScenarioStarted:
    scenario_id: str
    type: Literal["scenario_started"] = "scenario_started"


@dataclass(frozen=True)
class StepStarted:
    scenario_id: str
    step_index: int
    type: Literal["step_started"] = "step_started"


@dataclass(frozen=True)
class StepDone:
    scenario_id: str
    step_index: int
    status: Status
    votes: Votes | None = None  # AI 断言才有
    cost: Cost | None = None
    error_type: str | None = None  # ErrorType；failed/error 两态均可带
    message: str | None = None
    report_refs: tuple[ReportRef, ...] = ()  # step 级原生产物（Nova：本 step 的 act 轨迹，kind=trajectory，ADR 0027）
    type: Literal["step_done"] = "step_done"


@dataclass(frozen=True)
class StepSkipped:
    """scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。

    **独立事件、平行于 StepDone，不是 status 第 4 态**——wire 严格三态（ADR 0024），「这步没跑」是
    执行事实、非判定结论，故不塞进 StepDone.status。无 status/votes/cost 字段（没跑，无从谈判定/成本）。
    core 收到它 → 本地构造 StepResult(status=SKIPPED, shortcircuited=True)：SKIPPED 复用既有枚举（在
    StepResult 层直观表「没跑」），但由 core 本地赋、不经 wire（同 job 级 skipped/aborted 的 core 派生态性质）。
    """

    scenario_id: str
    step_index: int
    type: Literal["step_skipped"] = "step_skipped"


@dataclass(frozen=True)
class ScenarioDone:
    scenario_id: str
    status: Status
    report_refs: tuple[ReportRef, ...] = ()
    type: Literal["scenario_done"] = "scenario_done"


@dataclass(frozen=True)
class ScopeDone:
    scope_id: str
    session_id: str | None = None  # AgentCore 会话血缘
    report_refs: tuple[ReportRef, ...] = ()
    type: Literal["scope_done"] = "scope_done"


Event = (
    ScopeStarted | ScenarioStarted | StepStarted | StepDone | StepSkipped | ScenarioDone | ScopeDone
)


# ============================================================================
# 汇总：RunResult（schedule 对事件流的归约终值，ADR 0016/0026）
# ============================================================================


@dataclass
class StepResult:
    """单个 step 的归约结果（core 保留 step 级粒度，ADR 0024）。

    duration_ms = step 墙钟时长（core 用 step_started→step_done 的事件到达时间戳算）。
    """

    index: int
    status: Status
    duration_ms: float | None = None  # 墙钟时长（性能指标，与 cost 的 time_worked_s 正交）
    votes: Votes | None = None
    error_type: str | None = None
    report_refs: tuple[ReportRef, ...] = ()  # step 级原生产物指针（Nova：本 step 的 act 轨迹，kind=trajectory，ADR 0027）
    # 与判定轴（status）正交的第二维（ADR 0031 决定六）：True = 本 step 因上游 error 被 scope 内短路而跳过、没跑。
    # 仅在 status==SKIPPED（由 step_skipped 事件派生）时为 True；渲染层的连锁失败旁注据此判定（比"按 status 顺序猜"精确）。
    shortcircuited: bool = False


@dataclass
class ScenarioResult:
    """单个 scenario 的归约结果。"""

    scenario_id: str
    status: Status
    steps: list[StepResult] = field(default_factory=list)
    duration_ms: float | None = None  # 墙钟时长（scenario_started→scenario_done）
    report_refs: tuple[ReportRef, ...] = ()


@dataclass
class JobResult:
    """单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。

    **持有 `job`（definition）而非重复抄它的字段**（ADR 0016 三层切分）：scope_id/scope_name/engine
    经 property 从 `job` 取，消除「抄字段抄漏」病根（旧版抄了 engine 漏了 scope_name）。
    本类只背**判定**：status/scenarios/session_id/cost/duration/report_refs/error_type/message。
    """

    job: Job  # 这个 job 的 definition（plan 产出；scope_id/scope_name/engine/scenarios 的唯一真值）
    status: Status  # 汇总：任一 scenario error→error；任一 failed→failed；全 passed→passed
    scenarios: list[ScenarioResult] = field(default_factory=list)
    session_id: str | None = None
    # 成本：core 只各自合计 engine 报的原生量（None=该引擎没报这个量）。美元折算交消费者。
    total_tokens: int | None = None  # scope 级 token 合计（如 Midscene）
    total_time_worked_s: float | None = None  # scope 级 agent 工作时长合计（如 Nova）
    duration_ms: float | None = None  # scope 墙钟时长（scope_started→scope_done；性能指标，与成本正交）
    report_refs: tuple[ReportRef, ...] = ()  # scope 级原生报告产物指针（来自 scope_done，进 RunReport，ADR 0024）
    error_type: str | None = None  # job 级失败（worker 崩/超时）时有
    message: str | None = None

    # definition 字段经 property delegate 给 job（读法稳定、存储唯一，ADR 0016）
    @property
    def scope_id(self) -> str:
        return self.job.scope_id

    @property
    def scope_name(self) -> str:
        return self.job.scope_name

    @property
    def engine(self) -> str:
        return self.job.engine


@dataclass
class RunResult:
    """一次执行的机器可读汇总判定 = **definition（run_meta）+ 判定（jobs）的显式合成**（ADR 0016/0026）。

    RunResult 是 schedule 对事件流的归约终值；sink 收的是同一事件流的原始流式视图（ADR 0026）。

    成本（ADR 0024）：core 不算、不折美元——只各自合计 engine 报的**原生量**
    （token 用量 / agent 工作时长）。哪个有值取决于哪些引擎报了它（Nova 报时长、Midscene 报 token）；
    美元折算交给消费者（用自己 AWS 账户的真实费率）。None=无任何引擎报这个量。
    """

    run_meta: RunMeta  # 这次 run 的 definition（run_id/created_at/jobs；执行前确定，不从结果反推）
    status: Status  # 总判定：任一 job error→error；任一 failed→failed；全 passed→passed
    jobs: list[JobResult] = field(default_factory=list)
    total_tokens: int | None = None  # 跨 job 的 token 合计（None=无引擎报 token）
    total_time_worked_s: float | None = None  # 跨 job 的 agent 工作时长合计（None=无引擎报时长）
    duration_ms: float | None = None  # 整个 run 的墙钟时长（schedule 整体包住；含并发，≠ 各 scope 时长之和）

    @property
    def run_id(self) -> str:
        return self.run_meta.run_id


# ============================================================================
# definition（前置身份）与控制面运行态（ADR 0016 三层切分）
# ============================================================================


@dataclass(frozen=True)
class RunMeta:
    """一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。

    含「要跑什么」的全部：run_id + created_at + 完整 Job 列表（Job 含 scope/engine/scenarios/steps）。
    **不含 status/判定**（那是执行后才有，属控制面运行态 RunState / 数据面 ResultStore）。
    """

    run_id: str  # 组合根生成（RunReport 主键 / 未来 RunStore PK）
    created_at: str  # 组合根生成的时间戳（core 不取时钟）
    jobs: tuple[Job, ...]  # 这次跑哪些 job（完整 definition，来自 plan 产出）


@dataclass(frozen=True)
class JobState:
    """单个 job 的控制面运行态（执行后才有）。"""

    scope_id: str
    status: Status
    session_id: str | None = None  # AgentCore 会话血缘
    # claim（CAS pending→running）时刻 ISO 串（ADR 0034「job timeout」节 claimed_at）：local 接力恢复
    # deadline / cloud tick 防御性超时扫 / status 显示时长。timeout 从此刻起算（含启动开销）。
    claimed_at: str | None = None


@dataclass(frozen=True)
class RunState:
    """一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。

    与 RunMeta（definition）分开：definition 执行前确定、不变；运行态随执行产生。实时写下随进度增量更新
    （ADR 0030：create_run 写初始全 pending → 每 job 完成/起跑刷 jobs[scope_id] → finalize 写总 status）。
    started_at/ended_at 实时写下按生命周期出现（create_run 填 started、finalize 填 ended）。

    **jobs 是 Map（scope_id → JobState），非 list**（ADR 0030 决定五）：实时按单个 job 刷状态需「按 scope_id
    定位」，list 只能按下标定位（DDB 更无法按属性值定位 list 元素）。Map 下各 scope 互不干扰、支持单元素更新。
    内存模型是 Map；落盘 JSON 仍是 list（serialize 负责转换，保 run_state.json 向后兼容）。
    """

    run_id: str
    status: Status
    jobs: dict[str, JobState]  # scope_id → JobState（Map，ADR 0030 决定五）
    started_at: str | None = None
    ended_at: str | None = None
    # 无状态跑批的并发写守卫（ADR 0034 机制三）：reconciler 跨进程/跨 Lambda 并发投影写 RunState 时，
    # high_water_mark = 本次投影已处理的 worker 段 max seq。RunStore 条件写「我处理到的 seq ≥ 库中记录的才写」，
    # 挡 stale 实例的 lost-update（把 passed 刷回 running）。仅无状态路径（submit/reconciler）用；同步 run
    # 路径单进程内 RunPersistence._lock 串行、不并发写，此字段留 None（不参与、不落盘键，向后兼容旧 run_state.json）。
    high_water_mark: int | None = None


def run_state_from_result(result: RunResult) -> RunState:
    """从 RunResult 投影出控制面运行态（ADR 0016/0027）。

    投影的是**运行态**（status/session_id，本就执行后才有），非从结果反推 definition 身份——
    scope_id 经 jr.job 取（definition 本在 job 里）。jobs 投影成 Map（scope_id → JobState，ADR 0030）。
    """
    return RunState(
        run_id=result.run_id,
        status=result.status,
        jobs={
            jr.scope_id: JobState(scope_id=jr.scope_id, status=jr.status, session_id=jr.session_id)
            for jr in result.jobs
        },
    )
