"""领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。

无逻辑、无 I/O——只是 core 各模块之间、core↔worker 之间传递的形状。
parse 产出 Scenario/Step；scope 组装 Job；worker 回 Event 流；schedule 归约成 RunResult。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

# ============================================================================
# 输入侧：plan(0025) 产出、喂给 worker(0024 输入) 的形状
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


# ============================================================================
# 成本信封（ADR 0024）：dollar 轴对称、token 轴非对称
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
    """scenario/step 三态（ADR 0024）。"""

    PASSED = "passed"  # 测试通过
    FAILED = "failed"  # 断言投票没过 = 测试发现了问题
    ERROR = "error"  # 引擎抛异常 = 没能跑完测试


# errorType 规范化类别集（ADR 0024，可随真实失败样本扩充）
ErrorType = Literal[
    "assertion_failed",  # failed 态：断言没过
    "timeout",  # error 态：超时
    "guardrail",  # error 态：引擎护栏拦截
    "engine_error",  # error 态：引擎内部/通用异常（Midscene 通用 Error 归此）
    "navigation_error",  # error 态：导航失败
]


@dataclass(frozen=True)
class Votes:
    """AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。"""

    yes: int
    total: int


@dataclass(frozen=True)
class ReportRef:
    """原生报告产物指针（ADR 0024/0010）。core 不按 granularity 分支，原样归 RunReport。"""

    granularity: Literal["scope", "act"]
    path: str


# --- 事件（worker 按序流式 emit；core 假定有序，ADR 0024）---
# 三级 started/done 对齐：scope_started/scenario_started/step_started 与各自 *_done 配对。
# started 事件让 core 用事件到达时间戳算各级墙钟时长（性能指标，与 cost 正交）。


@dataclass(frozen=True)
class ScopeStarted:
    scope_id: str
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
    type: Literal["step_done"] = "step_done"


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
    ScopeStarted | ScenarioStarted | StepStarted | StepDone | ScenarioDone | ScopeDone
)


# ============================================================================
# 汇总：RunResult（schedule 对事件流的归约终值，ADR 0016/0026）
# ============================================================================


@dataclass
class StepResult:
    """单个 step 的归约结果（core 首次保留 step 级粒度，ADR 0024）。

    duration_ms = step 墙钟时长（core 用 step_started→step_done 的事件到达时间戳算）。
    """

    index: int
    status: Status
    duration_ms: float | None = None  # 墙钟时长（性能指标，与 cost 的 time_worked_s 正交）
    votes: Votes | None = None
    error_type: str | None = None


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
    """单个 job(=scope) 的归约结果。"""

    scope_id: str
    status: Status  # 汇总：任一 scenario error→error；任一 failed→failed；全 passed→passed
    scenarios: list[ScenarioResult] = field(default_factory=list)
    session_id: str | None = None
    # 成本：core 只各自合计 engine 报的原生量（None=该腿没报这个量）。美元折算交消费者。
    total_tokens: int | None = None  # scope 级 token 合计（如 Midscene）
    total_time_worked_s: float | None = None  # scope 级 agent 工作时长合计（如 Nova）
    duration_ms: float | None = None  # scope 墙钟时长（scope_started→scope_done；性能指标，与成本正交）
    report_refs: tuple[ReportRef, ...] = ()  # scope 级原生报告产物指针（来自 scope_done，进 RunReport，ADR 0024）
    error_type: str | None = None  # job 级失败（worker 崩/超时）时有
    message: str | None = None


@dataclass
class RunResult:
    """一次执行的机器可读汇总判定（给退出码/CI，ADR 0016）。

    RunResult 是 schedule 对事件流的归约终值；sink 收的是同一事件流的原始流式视图（ADR 0026）。

    成本（ADR 0024）：core 不算、不折美元——只各自合计 engine 报的**原生量**
    （token 用量 / agent 工作时长）。哪个有值取决于哪些腿报了它（Nova 报时长、Midscene 报 token）；
    美元折算交给消费者（用自己 AWS 账户的真实费率）。None=无任何腿报这个量。
    """

    status: Status  # 总判定：任一 job error→error；任一 failed→failed；全 passed→passed
    jobs: list[JobResult] = field(default_factory=list)
    total_tokens: int | None = None  # 跨 job 的 token 合计（None=无腿报 token）
    total_time_worked_s: float | None = None  # 跨 job 的 agent 工作时长合计（None=无腿报时长）
    duration_ms: float | None = None  # 整个 run 的墙钟时长（schedule 整体包住；含并发，≠ 各 scope 时长之和）
