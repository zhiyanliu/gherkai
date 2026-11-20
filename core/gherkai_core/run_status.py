"""run 的状态只由 job 的终态算出（ADR 0031 决定三）：取法、结束写的说明表，以及两种使 job 成为终态的写对运行态的作用。

- `run_status_of`：run 状态的取法（ADR 0031 决定三「取法」）。除投影写之外，两个 RunStore adapter 写下 job 状态的写入口都在同一次写
  里按它写 run 状态；投影写不按它对整份 jobs 重算，只在把某个 job 写成 running 时写下 running（零个 job 时取法给出 passed，见
  `RunStore.project_state`）。后台每一轮的无状态推演（`project.project`）同样按它给出 run 级值，推进步骤不把这个值写进记录；scenario
  判定到 job 判定的归约是另一条路径（`project._aggregate`）。
- `RunEnding` 与 `RUN_ENDINGS`：结束写的说明表（ADR 0031 决定三「结束写」小节），各条来路的句子只在这里；运行定义不可用的变体由
  `definition_unavailable_ending` 带上读不到定义的原因，几种原因的句子同样只在这里（`schema_mismatch_reason`、
  `DEFINITION_CONTRACT_REASON`、`NO_WORKER_IMAGES_REASON`），由云端推进器使用（本机后台推进进程用自己生成的运行定义；status --wait
  接力从记录读回，读不出时不写）。
- `ending_applied` 与 `commit_applied`：结束写（`RunStore.end_run`）与带结果的 job 终态写（`RunStore.commit_job_states`）对一份运行态
  的作用。两个 RunStore adapter 都用它们算出要写下的运行态，adapter 只负责写的条件与落盘，同一调用顺序下两端的落库结果相同。
- `state_without_record`：没有记录的执行（`run --no-report`）按同一组作用在内存里算出的运行态（ADR 0031 决定五「数据源」）。
- `StopSource`：前台执行里余下的 job 不再启动的来源，作结束写的来路（ADR 0031 决定三「结束写」小节「一次结束写只带一行说明」条）。
- `check_running_write`：执行中的写（`RunStore.update_job_state`）的参数校验，两个 adapter 共用。

说明文字只是描述，这里与 adapter 都不解释它（ADR 0031 决定一「状态是一切计算的唯一依据」条）：写成与否、job 与 run 记成什么，都不看
说明有没有、是什么；结束写成立与否只看运行态与 `RunEnding` 的两个结构字段 `ends_running_jobs`、`definition_unavailable`。说明表一行的
形态校验（`RunEnding` 构造时核对哪几格带说明）是参数的校验，不在其内。
本模块是纯函数、无 I/O、不取时钟：结束时刻由调用方给出。
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
from typing import Final, Literal

from gherkai_core.model import TERMINAL_STATUSES, JobResult, JobState, RunMeta, RunState, Status


def run_status_of(job_statuses: Iterable[Status]) -> Status:
    """run 状态的取法（ADR 0031 决定三「取法」）。

    有 job 未结束时，全部是 pending 为 pending，否则为 running。全部结束时按序取第一条成立的：有 error 则 error；否则有 failed 则
    failed；否则有 aborted 或 skipped 则 aborted（这个 run 没有执行完）；否则 passed。空清单给出 passed，它不对应任何记录（建 run 的入口拒绝没有 job 的运行定义，见 `check_new_run`）。结果是终态，当且仅当
    每个 job 都是终态。"""
    statuses = list(job_statuses)
    if any(s not in TERMINAL_STATUSES for s in statuses):
        return Status.PENDING if all(s == Status.PENDING for s in statuses) else Status.RUNNING
    if Status.ERROR in statuses:
        return Status.ERROR
    if Status.FAILED in statuses:
        return Status.FAILED
    if Status.ABORTED in statuses or Status.SKIPPED in statuses:
        return Status.ABORTED
    return Status.PASSED


# ============================================================================
# 结束写的说明表（ADR 0031 决定三「结束写」小节）
# ============================================================================


@dataclass(frozen=True)
class RunEnding:
    """说明表的一行：一次结束写写下的说明，以及这条来路结束什么样的 run。

    结构字段（结束写成立与否、各 job 记成什么，只由它们与运行态决定）：
    - ends_running_jobs：这条来路是否结束有执行中 job 的 run。为 False 的来路（执行方自己到期、fail-fast、使用方中断）的条件本来就
      要求执行中的 job 都已结束（ADR 0031 决定三「结束写」小节），运行态里有 running 的 job 时结束写不成立；为 True 的来路（处置的
      两行、运行定义不可用的变体）把 running 的 job 一并结束。
    - definition_unavailable：运行定义不可用的变体。每个未结束的 job 记 error，说明同 run 级。

    说明（只是描述，写进运行态；结束写成立与否、各 job 记成什么都不看它们）：
    - run_message：run 级说明，写进运行态的 run 级 message。
    - skipped_message：运行态里是 pending 的 job 记 skipped 时带的说明。
    - aborted_message：运行态里是 running 的 job 记 aborted 时带的说明。

    形态只有三种，构造时不符即抛 ValueError：不结束执行中 job 的来路带 skipped_message、不带 aborted_message（说明表里这一格「不
    出现」）；结束执行中 job 的来路两句都带；运行定义不可用的变体 ends_running_jobs 为 True、两句都不带。
    """

    run_message: str
    skipped_message: str | None = None
    aborted_message: str | None = None
    ends_running_jobs: bool = False
    definition_unavailable: bool = False

    def __post_init__(self) -> None:
        if self.definition_unavailable:
            if self.skipped_message is not None or self.aborted_message is not None:
                raise ValueError("运行定义不可用的结束写只带 run 级说明：未结束的 job 都记 error，说明同 run 级")
            if not self.ends_running_jobs:
                raise ValueError("运行定义不可用的结束写把执行中的 job 一并记 error，ends_running_jobs 须为 True")
            return
        if self.skipped_message is None:
            raise ValueError("结束写要带 pending 的 job 记 skipped 时的说明")
        if self.ends_running_jobs != (self.aborted_message is not None):
            raise ValueError("结束执行中 job 的来路要带 running 的 job 记 aborted 时的说明，不结束它们的来路不带")


# 说明表的来路：执行方自己到期、fail-fast、使用方中断、处置的两行（锁拿到了，即执行这个 run 的进程已退出；已过期限加 300 秒，含云端
# 后端到期）。前三个与 `StopSource` 里的同名，也与调度循环的中止来源（`project.AbortCause`）同名。
EndingRoute = Literal["deadline", "fail-fast", "interrupt", "settle-advancer-exited", "settle-past-deadline"]

# 前台执行里余下的 job 不再启动的来源（起 worker 与重试之前的检查项）：已过停止启动的时刻（deadline）、run 因 fail-fast 或使用方中断
# 而中止，或已发现 run 被别处记为已结束（ended-elsewhere）。调度循环记下最先登记的那一条交给落库服务；前三条是说明表里的来路，作结束
# 写的说明（ADR 0031 决定三「结束写」小节「一次结束写只带一行说明」条），ended-elsewhere 时记录已是终态，不做结束写。
StopSource = Literal["deadline", "fail-fast", "interrupt", "ended-elsewhere"]

_PAST_DEADLINE = "已超过允许运行的时间"
_PAST_DEADLINE_NOT_STARTED = "这个 run 已超过允许运行的时间，job 没有启动"
_PAST_DEADLINE_NO_RESULT = "这个 run 已超过允许运行的时间，job 没有结果"
_ADVANCER_EXITED = "执行这个 run 的 gherkai 进程已退出"


def _settled(run_message: str, skipped_message: str, aborted_message: str) -> RunEnding:
    """处置的一行：结束执行中的 job，各句末尾另加「（已记为已结束）」。"""
    suffix = "（已记为已结束）"
    return RunEnding(run_message + suffix, skipped_message + suffix, aborted_message + suffix, ends_running_jobs=True)


RUN_ENDINGS: Mapping[EndingRoute, RunEnding] = MappingProxyType({
    "deadline": RunEnding(_PAST_DEADLINE, _PAST_DEADLINE_NOT_STARTED),
    "fail-fast": RunEnding("有 job 出错，余下的 job 不再启动（fail-fast）", "fail-fast：其他 job 出错，本 job 没有启动"),
    "interrupt": RunEnding("收到中断信号，余下的 job 不再启动", "收到中断信号，本 job 没有启动"),
    "settle-advancer-exited": _settled(_ADVANCER_EXITED, f"{_ADVANCER_EXITED}，job 没有启动",
                                       f"{_ADVANCER_EXITED}，job 没有结果"),
    "settle-past-deadline": _settled(_PAST_DEADLINE, _PAST_DEADLINE_NOT_STARTED, _PAST_DEADLINE_NO_RESULT),
})


def definition_unavailable_ending(reason: str) -> RunEnding:
    """运行定义不可用时的结束写：reason 是读不到定义的原因（ADR 0037 决策 7 的几句），既是 run 级说明，也是每个未结束的 job 的说明。
    执行中的 job 同样记 error。"""
    return RunEnding(reason, ends_running_jobs=True, definition_unavailable=True)


# 读不到可用的运行定义时的几种原因（ADR 0037 决策 7）：产品语言的整句、长度有界，说清哪里不对与怎么办；契约异常的原文只进推进器的
# 日志。用它们的是云端推进器：它从记录读回运行定义，读不出时以结束写的 error 变体结束这个 run。
DEFINITION_CONTRACT_REASON: Final = "提交记录不完整或形态不对，后端不能执行它；请用与后端同版本的 gherkai 重新提交"
NO_WORKER_IMAGES_REASON: Final = "提交记录没有记 worker 镜像版本，后端不能执行它；请用与后端同版本的 gherkai 重新提交"


def schema_mismatch_reason(found: int, supported: int, cli_version: str | None) -> str:
    """推进器读到结构版本不等于自己认的提交记录时的原因（ADR 0037 决策 7）：谁写的、两边各第几版、怎么办。found 是记录的结构版本，
    supported 是推进器认的版本，cli_version 是写出记录的命令行工具版本（记录自带，可以为空）。

    与命令行读端对同一事件的说法分开写：命令行的出路是升级本机或用写端版本查看，这里的出路是升级后端或用后端版本重新提交。写端版本
    来自提交记录、不受信，截到 40 个字符再拼进句子，损坏的值不会把运行态条目撑大。"""
    by = f"gherkai {str(cli_version)[:40]}" if cli_version else "gherkai（版本未知）"
    if found > supported:
        return (f"提交记录由更新版本的 {by} 写出（记录是第 {found} 版，后端只认第 {supported} 版），后端不能执行它；"
                "请部署方把后端升级到提交侧的版本，或用后端版本的 gherkai 重新提交")
    return (f"提交记录由更早版本的 {by} 写出（记录是第 {found} 版，后端只认第 {supported} 版），后端不能执行它；"
            "请把提交侧的 gherkai 升级到后端的版本后重新提交")


# ============================================================================
# 两种使 job 成为终态的写对运行态的作用（RunStore 的 end_run 与 commit_job_states 共用）
# ============================================================================


def ending_applied(state: RunState, ending: RunEnding, *, ended_at: str) -> RunState | None:
    """结束写对一份运行态的作用：返回要写下的运行态；结束写不成立时返回 None。

    不成立的情形：run 已是终态；或这条来路不结束执行中的 job（`ending.ends_running_jobs` 为 False）而运行态里有 running 的 job。
    成立时，每个未结束的 job 写成终态并带一句说明：pending 的记 skipped、running 的记 aborted；运行定义不可用的变体都记 error、说明同
    run 级。会话与认领时刻原样保留，已是终态的 job 不变（它们点名的标识随之保留）。结束写不点名：由它结束的 job 没有标识。run 状态按
    取法随之成为终态，同一次写下 run 级说明与结束时刻；HWM、认领计数与开始时刻不变。判断只看这份运行态与 ending 的结构字段，不看说明：
    不读事件，不涉及判定明细。"""
    if state.status in TERMINAL_STATUSES:
        return None
    if not ending.ends_running_jobs and any(js.status == Status.RUNNING for js in state.jobs.values()):
        return None
    jobs: dict[str, JobState] = {}
    for sid, js in state.jobs.items():
        if js.status in TERMINAL_STATUSES:
            jobs[sid] = js
        elif ending.definition_unavailable:
            jobs[sid] = replace(js, status=Status.ERROR, message=ending.run_message)
        elif js.status == Status.PENDING:
            jobs[sid] = replace(js, status=Status.SKIPPED, message=ending.skipped_message)
        else:  # running：到这里 ending.ends_running_jobs 为 True，构造时已保证带 aborted 的说明
            jobs[sid] = replace(js, status=Status.ABORTED, message=ending.aborted_message)
    return replace(state, status=run_status_of(js.status for js in jobs.values()), jobs=jobs,
                   ended_at=ended_at, message=ending.run_message)


class CommitOutcome(str, Enum):
    """带结果的 job 终态写的结果（`RunStore.commit_job_states` 的返回值）。

    run 成为终态只发生一次，使它成为终态的那次写的写入方生成报告（ADR 0027「ReportStore 接口：整 run 一次写」节），所以调用方要从这次
    写本身分出三种结果，不靠写后读回推断。
    """

    OPEN = "open"  # 写成，run 在这次写之后仍未结束（给出的 job 里已是终态的不被改写）
    ENDED_RUN = "ended_run"  # 写成，这次写使 run 成为终态
    ALREADY_ENDED = "already_ended"  # 没有写成：run 在这次写之前已是终态，运行态不变


def _committed(current: JobState, given: JobState) -> JobState:
    """终态写记下的 job 条目：库中未结束的条目 current 与调用方给出的终态 given 按字段合并（ADR 0030 决定四）。

    - 状态取 given 的终态。
    - 认领时刻取库中的：认领那次写是它的来源；库中没有时取 given 的。
    - 会话取 given 的：它是产出这个结果的那次执行的会话；given 没有时保留库中的，不以空值覆盖。
    - 点名的标识取 given 的（ADR 0030 决定三「点名」条）：它是与这个终态出自同一个执行结果的那一份明细。库中未结束的条目没有标识（只由
      终态写写下，执行中的写不接受它，见 `check_running_write`）；given 没有标识（没有存明细）即不点名。
    - job 级说明保留库中的：它只由结束写写下，given 带的不写下。
    合并的依据是读到的这份条目（本机在锁内读，云端每次重读之后重算）。调用方准备参数之后、写成之前别的写为这个 job 写下的认领时刻因此
    留下；那段时间里写下的会话只在 given 没有会话时留下，given 带了会话即取 given 的。两者都不被空值覆盖。云端重读再算时 given 不变，
    点名的仍是同一个标识。"""
    return replace(current, status=given.status,
                   session_id=given.session_id if given.session_id is not None else current.session_id,
                   claimed_at=current.claimed_at if current.claimed_at is not None else given.claimed_at,
                   result_id=given.result_id)


def commit_applied(state: RunState, job_states: Sequence[JobState], *,
                   ended_at: str) -> tuple[RunState | None, CommitOutcome]:
    """带结果的 job 终态写对一份运行态的作用：返回要写下的运行态（没有写成时为 None）与这次写的结果。

    给出的每个 job 都要是终态，scope_id 不重复、都在这份运行态的 job 里，至少一个；不满足即抛 ValueError、不写任何东西。run 已是终态时
    没有写成（ALREADY_ENDED）。否则库中已是终态的 job 不被改写（终态只写一次，ADR 0031 决定一·补；别的写入方点名的标识原样保留），
    其余给出的 job 按 `_committed` 的字段规则与库中的条目合并（ADR 0030 决定四），各点名各自给出的标识；run 状态按取法随之写下，成为
    终态时同一次写下结束时刻（ENDED_RUN），否则为 OPEN。HWM、认领计数、开始时刻与 run 级说明不变。不要求给出的终态带标识：没有记录的
    执行（`state_without_record`）不存明细，写下的终态不点名。"""
    job_states = tuple(job_states)
    if not job_states:
        raise ValueError("终态写至少要给出一个 job")
    seen: set[str] = set()
    for js in job_states:
        if js.scope_id in seen:
            raise ValueError(f"终态写里 job {js.scope_id} 出现了不止一次")
        seen.add(js.scope_id)
        if js.status not in TERMINAL_STATUSES:
            raise ValueError(f"终态写只记终态，job {js.scope_id} 的状态是 {js.status.value}")
        if js.scope_id not in state.jobs:
            raise ValueError(f"job {js.scope_id} 不在 run {state.run_id} 的运行态里")
    if state.status in TERMINAL_STATUSES:
        return None, CommitOutcome.ALREADY_ENDED
    jobs = dict(state.jobs)
    for js in job_states:
        current = state.jobs[js.scope_id]
        if current.status not in TERMINAL_STATUSES:
            jobs[js.scope_id] = _committed(current, js)
    status = run_status_of(js.status for js in jobs.values())
    if status in TERMINAL_STATUSES:
        return replace(state, status=status, jobs=jobs, ended_at=ended_at), CommitOutcome.ENDED_RUN
    return replace(state, status=status, jobs=jobs), CommitOutcome.OPEN


def check_new_run(meta: RunMeta) -> None:
    """建 run（`RunStore.create_run`）的参数校验：运行定义里没有 job 即抛 ValueError、不写（ADR 0031 决定三「取法」）。run 的终态
    只由 job 的终态写与结束写带出，没有 job 的 run 没有任何一次写能使它结束；命令行在这之前已以退出码 2 拒绝零个 scenario 的批次，
    这里守的是直接调用端口的调用方。"""
    if not meta.jobs:
        raise ValueError(f"run {meta.run_id} 的运行定义里没有 job，不建立")


def check_running_write(job_state: JobState) -> None:
    """执行中的写（`RunStore.update_job_state`）的参数校验：写入的 job 态只能是 running，否则抛 ValueError、不写（ADR 0030 决定四）。
    pending 只由建 run 写下，终态由终态写与结束写写下；与 `commit_applied` 对非终态抛错对称。带点名的标识同样抛 ValueError：点名只由
    带结果的终态写写下（ADR 0030 决定三「点名」条），执行中的写整项替换 job 的条目，带进去的标识会随之后结束写的 `replace` 留在一个
    由结束写结束的 job 上，读者会把它当成由执行结果结束。"""
    if job_state.status != Status.RUNNING:
        raise ValueError(f"执行中的写只记 running，job {job_state.scope_id} 的状态是 {job_state.status.value}")
    if job_state.result_id is not None:
        raise ValueError(f"执行中的写不点名判定明细，job {job_state.scope_id} 带了标识 {job_state.result_id}")


# ============================================================================
# 没有记录的执行：按同一组作用在内存里算出运行态（ADR 0031 决定五「数据源」）
# ============================================================================


def ending_of_stop(stopped_by: StopSource | None) -> RunEnding:
    """前台执行结束时仍有没有结束的 job：给出结束它们的那一行结束写（`RUN_ENDINGS` 里与 stopped_by 同名的一行）。有记录的收尾
    （`persist.RunPersistence.finalize`）与没有记录时的内存计算（`state_without_record`）共用这一处。

    stopped_by 为空（余下的 job 没有结束的来路）或为 ended-elsewhere（已被别处结束的 run 不由这次执行结束）时，执行事实与「仍有 job
    没有结束」不相容，抛 ValueError。"""
    if stopped_by is None or stopped_by == "ended-elsewhere":
        raise ValueError(f"仍有没有结束的 job，而这次执行没有给出可用于结束它们的来路（{stopped_by!r}）")
    return RUN_ENDINGS[stopped_by]


def state_without_record(meta: RunMeta, results: Sequence[JobResult], stopped_by: StopSource | None, *,
                         ended_at: str) -> RunState:
    """没有记录的执行（`run --no-report`）的运行态：与有记录时两个写入口对运行态的作用相同，在内存里依次算出。

    从全部 job 为 pending 的初始运行态出发：先把 results（判出结果的 job）经 `commit_applied` 记为终态；run 还没到终态时，余下的 job
    由 stopped_by 这条来路的结束写结束（`ending_applied`）。这时没有执行中的 job，结束写恒成立。会话取明细里的；没有认领写，认领时刻
    为空；没有判定存储，终态不点名（明细就是调用方手里的 results）。

    参数错误抛 ValueError：仍有 job 没有结果而 stopped_by 给不出结束它们的来路（`ending_of_stop`，与有记录时同一处检查）；results
    不满足 `commit_applied` 的要求（不是终态、重复、不在运行定义里）。"""
    state = RunState(run_id=meta.run_id, status=Status.PENDING,
                     jobs={j.scope_id: JobState(scope_id=j.scope_id, status=Status.PENDING) for j in meta.jobs})
    if results:
        committed, _outcome = commit_applied(
            state, [JobState(scope_id=jr.scope_id, status=jr.status, session_id=jr.session_id) for jr in results],
            ended_at=ended_at)
        assert committed is not None  # 初始运行态未结束，终态写总能写成
        state = committed
    if state.status not in TERMINAL_STATUSES:
        ended = ending_applied(state, ending_of_stop(stopped_by), ended_at=ended_at)
        assert ended is not None  # 未结束、没有 running 的 job，结束写总能成立
        state = ended
    return state
