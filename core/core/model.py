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
    """step 级成本信封（ADR 0024）。cost_usd 跨引擎可汇总；evidence 由 basis 判别。"""

    cost_usd: float | None  # 一等、对称、可 sum() 汇总（产品价值）
    precision: Literal["exact", "estimated"]  # 由 basis 派生：tokens→exact / agent_time→estimated
    basis: Literal["tokens", "agent_time"]  # 结构判别器：决定 evidence 形状
    evidence: dict  # basis=tokens → {prompt_tokens,completion_tokens,total_tokens}
    #                  basis=agent_time → {time_worked_s,human_wait_time_s,num_steps_executed}


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


# --- 四种事件（worker 按此顺序流式 emit；core 假定有序，ADR 0024）---


@dataclass(frozen=True)
class ScenarioStarted:
    scenario_id: str
    type: Literal["scenario_started"] = "scenario_started"


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
    cost_rate: dict | None = None  # {nova_act_usd_per_agent_hour: 4.75} 等配置常量
    type: Literal["scope_done"] = "scope_done"


Event = ScenarioStarted | StepDone | ScenarioDone | ScopeDone


# ============================================================================
# 汇总：RunResult（schedule 对事件流的归约终值，ADR 0016/0026）
# ============================================================================


@dataclass
class ScenarioResult:
    """单个 scenario 的归约结果。"""

    scenario_id: str
    status: Status
    report_refs: tuple[ReportRef, ...] = ()


@dataclass
class JobResult:
    """单个 job(=scope) 的归约结果。"""

    scope_id: str
    status: Status  # 汇总：任一 scenario error→error；任一 failed→failed；全 passed→passed
    scenarios: list[ScenarioResult] = field(default_factory=list)
    session_id: str | None = None
    error_type: str | None = None  # job 级失败（worker 崩/超时）时有
    message: str | None = None


@dataclass
class RunResult:
    """一次执行的机器可读汇总判定（给退出码/CI，ADR 0016）。

    RunResult 是 schedule 对事件流的归约终值；sink 收的是同一事件流的原始流式视图（ADR 0026）。
    """

    status: Status  # 总判定：任一 job error→error；任一 failed→failed；全 passed→passed
    jobs: list[JobResult] = field(default_factory=list)
    total_cost_usd: float | None = None  # 跨 job 累加（None 表示无任何成本数据）
