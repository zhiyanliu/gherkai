"""run 处置（ADR 0054 决策六到八）：判定与动作只在这里，等待中的 `status --wait`、`settle-runs` 与云端的后端到期结束（推进 Lambda
在期限加 300 秒那一次定时触发里做的处置，ADR 0054 决策九第 1 条）三方都调它，各方不另写判定。处置目标按后端装配：本机是
`local_target`，云端是 `cloud_target`。

- **一次处置**（`settle_run`）按 ADR 0054 决策八「处置的次序」依次做：读一次提交记录（结构版本不是本版本认的即给出
  `other_version`；读得出的记下期限，读不出的即期限读不出）；读运行态，不碰锁（读不出、已结束即给出结果）；本机以只读方式打开 run
  目录、对这次打开做边界检查、不阻塞地试拿（`LocalRunDirs.probe_run_dir`）；判定（`decide`），取一次墙钟，结束时刻用同一个读数；结束写；
  写成之后生成报告；最后关闭描述符，锁随之放开，所以锁持有到报告生成之后。云端没有打开、边界检查与试拿三步（`SettleTarget.run_dirs`
  为 None）。
- **只有结束写改记录**：它自带 run 未结束的条件，前面各步之间别的一方插进来的变化都由它裁定，不在锁内重读运行态（ADR 0054「被拒
  方案」）；`dry_run` 只判定、不写，拿到的锁随即放开。
- **「不存在」即这个名字下已没有 run**（`RunGone`）：读运行态读到不存在，或之后打开 run 目录、结束写时这个名字下已没有目录或文件。
  别的读写失败（OSError）原样交给调用方：它们是读写记录失败，不是一种 reason（ADR 0054 决策三「结果的判读」、决策八）。
- **报告**：写成的一方按被处置的那个 run 标识生成（`reconcile.generate_report_from_record`，复制出来的 run 目录里它与提交记录里的
  标识不同，ADR 0054 决策七「报告」）；提交记录读不出的 run 没有报告。生成的失败隔离在这里，结果里带「报告是否生成」与没有生成的原因
  （类别与说明分开），不记日志：两个入口在使用者的终端上说明，不把回溯打到终端（ADR 0039）。
- **不给 run 标识时处理哪些 run**：`unfinished_run_ids` 列出要处置的 run 与次序。逐个处置与逐个清理暂存目录（`LocalRunDirs` 的
  `staging_names` 与 `sweep_staging_dir`，协议在 core 的 `run_dir.sweep_staging_dir`）的循环在命令行一侧：每一项之前看一次中断的
  标志，已处理的部分与列举出的 run 由命令自己记下（ADR 0016「run 处置」一句与紧邻的被拒方案）。

判定只看状态值与结构化字段（锁的结果、期限是否读得出、边界检查的结论），结果里的说明片段只供入口拼说明。
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Protocol

from gherkai_core.adapters.run_store import run_dir
from gherkai_core.errors import NamedDetailMissing, UnsupportedDefinitionSchema
from gherkai_core.model import TERMINAL_STATUSES, RunMeta, Status
from gherkai_core.ports import ReportStore, ResultStore, RunStore
from gherkai_core.reconcile import generate_report_from_record
from gherkai_core.run_deadline import deadline_of, past_overdue
from gherkai_core.run_status import RUN_ENDINGS
from gherkai_core.serialize import UNREADABLE_RECORD_ERRORS, instant_to_iso
from gherkai_runtime import compose


class Reason(str, Enum):
    """处置结果的原因，取第一条成立的（ADR 0054 决策八「settle-runs」一条），值即 `settle-runs --json` 里 `runs[].reason` 的取值。
    次序即定义的次序。"""

    OTHER_VERSION = "other_version"                     # 提交记录由别的版本写出：本版本不处置它
    UNREADABLE = "unreadable"                           # 运行态读不出（内容解析不了）：无从做条件写
    ALREADY_FINISHED = "already_finished"               # 已结束，含结束写被别处抢先
    UNSUPPORTED_FILESYSTEM = "unsupported_filesystem"   # run 目录不过边界检查：没有试拿
    ADVANCER_EXITED = "advancer_exited"                 # 锁拿到了：管它的进程已不在
    PAST_DEADLINE = "past_deadline"                     # 已过运行期限加 300 秒
    LOCK_HELD = "lock_held"                             # 锁被持有（未必是推进器，另一个处置方也持有它）
    UNDETERMINED = "undetermined"                       # 锁不可用、或期限读不出（云端），期限一条也不成立
    WITHIN_DEADLINE = "within_deadline"                 # 云端：期限读得出、还没有过期限加 300 秒


class Outcome(str, Enum):
    """处置结果，值即 `settle-runs --json` 里 `runs[].outcome` 的取值。"""

    SETTLED = "settled"             # 这一次的结束写写成
    WOULD_SETTLE = "would_settle"   # dry_run：条件成立，没有写
    SKIPPED = "skipped"


class DefinitionRead(Enum):
    """读提交记录的结果。判定只看由它得出的期限是否读得出，以及是不是 OTHER_VERSION。"""

    READABLE = "readable"
    MISSING = "missing"               # 提交记录不存在
    OTHER_VERSION = "other_version"   # 头读得出、结构版本不是本版本认的
    MALFORMED = "malformed"           # 内容不是 JSON 对象、定义违约（含 deadline_at 缺失或不合法）


class ReportMissing(str, Enum):
    """处置写成之后报告没有生成的原因类别。说明另在 `ReportNotWritten.detail`。"""

    DEFINITION_UNREADABLE = "definition_unreadable"   # 提交记录读不出：报告按运行定义逐个列出 job，组装不出
    DETAIL_MISSING = "detail_missing"                 # 运行态点名的判定明细读不到
    RECORD_UNREADABLE = "record_unreadable"           # 记录读到了而解析不了，或运行态与运行定义对不上
    ACCESS_FAILED = "access_failed"                   # 读写报告目录里的文件失败（含 run 目录在结束写之后被删去）
    OTHER = "other"                                   # 别的异常


_SETTLE_ROUTES = {
    # 处置的两个 reason 对应结束写说明表里的两行（ADR 0031 决定三「结束写」小节）；两个条件同时成立时 decide 已取锁那一行
    Reason.ADVANCER_EXITED: "settle-advancer-exited",
    Reason.PAST_DEADLINE: "settle-past-deadline",
}

# 提交记录读不出时报告没有生成的说明片段（产品语言，入口拼进「报告没有生成：…」）
_DEFINITION_UNREADABLE_DETAIL = {
    DefinitionRead.MISSING: "这个 run 的提交记录不存在，报告要按提交记录列出各个 job",
    DefinitionRead.MALFORMED: "这个 run 的提交记录不完整或形态不对，报告要按提交记录列出各个 job",
}


class RunGone(LookupError):
    """这个名字下已没有 run：读运行态读到不存在（含标识不合名字规则），或之后打开 run 目录、结束写时这个名字下已没有目录或文件
    （ADR 0054 决策八「处置的次序」）。`run_id` 是被处置的标识。"""

    def __init__(self, run_id: str) -> None:
        super().__init__(run_id)
        self.run_id = run_id


class LocalRunDirs(Protocol):
    """本机 run 目录的专属入口（`LocalRunStore` 上、不在 RunStore 端口上，ADR 0030 决定四）：试拿生命期锁与清理暂存目录。"""

    def probe_run_dir(self, run_id: str) -> AbstractContextManager[run_dir.RunDirProbe]: ...

    def staging_names(self) -> list[str]: ...

    def sweep_staging_dir(self, name: str, *, dry_run: bool) -> run_dir.StagingSweep | None: ...


@dataclass(frozen=True)
class SettleTarget:
    """处置要用的各部分。`run_dirs`：本机是 run_store 本身（`LocalRunStore`），云端没有锁也没有暂存目录，为 None。"""

    run_store: RunStore
    result_store: ResultStore
    report_store: ReportStore
    run_dirs: LocalRunDirs | None


def local_target(report_root: str | Path) -> SettleTarget:
    """本机报告目录上的处置目标：`compose.build_local_stores` 装配的三个存储，不带锁的持有者（处置方不建 run）。report_root 是入口
    解析并检查过的那个路径。"""
    run_store, result_store, report_store, _artifacts = compose.build_local_stores(report_dir=report_root)
    return SettleTarget(run_store=run_store, result_store=result_store, report_store=report_store, run_dirs=run_store)


def cloud_target(*, table: str, bucket: str, report_dir: str, region: str | None = None, profile: str | None = None,
                 ddb_table=None, s3=None) -> SettleTarget:
    """云端后端上的处置目标：`compose.build_cloud_stores` 装配的三个存储，没有锁与暂存目录（`run_dirs` 为 None，ADR 0054 决策八「处置
    的次序」：云端没有打开、边界检查与试拿三步）。

    RunStore 带 jobs 对象的存取：判定读整份运行定义（ADR 0054 决策六），漏装时对每个 run 都报装配缺失。判定存储与报告存储在产物桶里
    `report_dir` 这个报告前缀之下，处置写成之后的报告写在这里。推进 Lambda 的后端到期结束传它自己的 `REPORT_DIR` 与已建的句柄
    （`ddb_table`、`s3`，句柄都注入时 region 与 profile 不起作用）；命令行一侧的云端处置传 `--report-dir` 与定位参数。不能列举 run：
    要处置全部未结束 run 的调用方另经列举的装配取 run 标识。"""
    run_store, result_store, report_store = compose.build_cloud_stores(
        table=table, bucket=bucket, prefix=report_dir, region=region, profile=profile, ddb_table=ddb_table, s3=s3)
    return SettleTarget(run_store=run_store, result_store=result_store, report_store=report_store, run_dirs=None)


@dataclass(frozen=True)
class ReportNotWritten:
    """报告没有生成：`kind` 是类别，`detail` 是说明片段（产品语言，只供入口拼说明），`error` 是原异常（提交记录不存在时为 None）。"""

    kind: ReportMissing
    detail: str
    error: Exception | None = None


@dataclass(frozen=True)
class SettleResult:
    """一次处置的结果。判断只看 `outcome`、`reason` 与各结构化字段；说明由入口按它们选句。

    - `definition`：读提交记录的结果；`deadline` 在它为 READABLE 时是期限，否则为 None（期限读不出）；`definition_error` 是
      OTHER_VERSION（`UnsupportedDefinitionSchema`，带 found、supported、cli_version）与 MALFORMED 时读端的原异常。
    - `state_error`：UNREADABLE 时解析运行态的原异常。
    - `boundary`：打开 run 目录之后对这次打开的边界检查（本机、走到这一步时）；UNSUPPORTED_FILESYSTEM 时据它说明文件系统类型或判断不了的原因。
    - `lock`、`lock_error`：试拿的结果与锁不可用时的原错误（本机、边界检查通过时）。
    - `report_written`：只在 SETTLED 时有值，报告是否生成；没有生成时 `report_missing` 带原因。
    """

    run_id: str
    outcome: Outcome
    reason: Reason
    definition: DefinitionRead
    deadline: datetime | None = None
    definition_error: Exception | None = None
    state_error: Exception | None = None
    boundary: run_dir.BoundaryCheck | None = None
    lock: run_dir.LockState | None = None
    lock_error: OSError | None = None
    report_written: bool | None = None
    report_missing: ReportNotWritten | None = None

    def __post_init__(self) -> None:
        # 参数形态的校验：报告的两项只在写成时出现、且互相对得上；不参与任何判定
        settled = self.outcome is Outcome.SETTLED
        if settled != (self.report_written is not None) or (self.report_written is False) != (self.report_missing is not None):
            raise ValueError(f"处置结果的报告字段与结果不相符：outcome={self.outcome}, report_written={self.report_written}, "
                             f"report_missing={self.report_missing}")


def decide(*, lock: run_dir.LockState | None, deadline: datetime | None, now: datetime) -> Reason:
    """由锁与期限决定的五个 reason（ADR 0054 决策六、八），按次序取第一条成立的：锁拿到了为 ADVANCER_EXITED；期限读得出且 now 严格
    晚于期限加 300 秒为 PAST_DEADLINE；锁被持有为 LOCK_HELD；锁不可用为 UNDETERMINED；lock 为 None（云端，没有锁）时期限读不出为
    UNDETERMINED、否则 WITHIN_DEADLINE。纯函数，now 由调用方读一次墙钟给出。"""
    if lock is run_dir.LockState.ACQUIRED:
        return Reason.ADVANCER_EXITED
    if deadline is not None and past_overdue(now, deadline):
        return Reason.PAST_DEADLINE
    if lock is run_dir.LockState.HELD:
        return Reason.LOCK_HELD
    if lock is run_dir.LockState.UNAVAILABLE or deadline is None:
        return Reason.UNDETERMINED
    return Reason.WITHIN_DEADLINE


def _read_definition(run_store: RunStore, run_id: str) -> tuple[DefinitionRead, RunMeta | None, Exception | None]:
    """读一次提交记录：(结果, 读得出时的运行定义, 读端的原异常)。结构版本不认先于别的读不出判断：`UnsupportedDefinitionSchema` 也是
    「读不出」口径里的一类（ValueError 的子类）。读取本身的失败（OSError）原样抛出。"""
    try:
        meta = run_store.load_run_meta(run_id)
    except UnsupportedDefinitionSchema as e:
        return DefinitionRead.OTHER_VERSION, None, e
    except UNREADABLE_RECORD_ERRORS as e:
        return DefinitionRead.MALFORMED, None, e
    if meta is None:
        return DefinitionRead.MISSING, None, None
    return DefinitionRead.READABLE, meta, None


def settle_run(target: SettleTarget, run_id: str, *, clock: Callable[[], datetime], dry_run: bool) -> SettleResult:
    """处置一个 run（次序见模块头）。这个名字下已没有 run 抛 `RunGone`；读写记录失败（OSError，含打开 run 目录时「不存在」之外的
    失败）原样抛出，抛出时这个 run 没有改动：结束写之前的各步只读，结束写本身是原子写，之后生成报告的失败隔离在这里。其余情形都以
    `SettleResult` 返回。

    clock 是注入的墙钟（组合根传 `compose.now`），读两次：判定与结束时刻共用一个读数，报告的生成时刻另读一次。dry_run 给出判定那一刻
    的结果、不写；同一时刻不带它执行时，读运行态之后才结束的 run 由结束写得到 ALREADY_FINISHED，两者可能不同。"""
    definition, meta, definition_error = _read_definition(target.run_store, run_id)
    if definition is DefinitionRead.OTHER_VERSION:
        return SettleResult(run_id, Outcome.SKIPPED, Reason.OTHER_VERSION, definition, definition_error=definition_error)
    deadline = None if meta is None else deadline_of(meta)
    read = {"definition": definition, "deadline": deadline, "definition_error": definition_error}

    try:
        state = target.run_store.load_run_state(run_id)
    except UNREADABLE_RECORD_ERRORS as e:
        return SettleResult(run_id, Outcome.SKIPPED, Reason.UNREADABLE, state_error=e, **read)
    if state is None:
        raise RunGone(run_id)
    if state.status in TERMINAL_STATUSES:
        return SettleResult(run_id, Outcome.SKIPPED, Reason.ALREADY_FINISHED, **read)

    with ExitStack() as held:
        lock: run_dir.LockAttempt | None = None
        seen: dict = {}
        if target.run_dirs is not None:
            try:
                probe = held.enter_context(target.run_dirs.probe_run_dir(run_id))
            except run_dir.RunDirGone as e:
                raise RunGone(run_id) from e
            seen["boundary"] = probe.boundary
            if probe.boundary.verdict is not run_dir.Boundary.INSIDE:
                return SettleResult(run_id, Outcome.SKIPPED, Reason.UNSUPPORTED_FILESYSTEM, **read, **seen)
            lock = probe.lock
            seen.update(lock=lock.state, lock_error=lock.error)
        now = clock()
        reason = decide(lock=None if lock is None else lock.state, deadline=deadline, now=now)
        if reason not in _SETTLE_ROUTES:
            return SettleResult(run_id, Outcome.SKIPPED, reason, **read, **seen)
        if dry_run:
            return SettleResult(run_id, Outcome.WOULD_SETTLE, reason, **read, **seen)
        ended = _end(target.run_store, run_id, reason, now=now)
        if ended is not None:
            return SettleResult(run_id, Outcome.SKIPPED, ended[0], state_error=ended[1], **read, **seen)
        missing = _generate_report(target, run_id, meta, definition, definition_error, clock=clock)
        return SettleResult(run_id, Outcome.SETTLED, reason, **read, **seen,
                            report_written=missing is None, report_missing=missing)


def _end(run_store: RunStore, run_id: str, reason: Reason, *, now: datetime) -> tuple[Reason, Exception | None] | None:
    """结束写。写成返回 None；没有写成返回 (UNREADABLE, 原异常) 或 (ALREADY_FINISHED, None)；这个名字下已没有 run 抛 `RunGone`。

    处置的两行结束执行中的 job，结束写只在 run 已结束或运行态不存在时写不成（`run_status.ending_applied`），所以写不成之后重读一次分出
    两者：重读到终态即已结束（含被别处抢先）；重读到不存在即 run 已不在。重读到未结束说明结束写那一刻运行态不存在（终态不会变回未结束），
    现在这个名字下是另一个 run，同样按原来那个已不在处理。"""
    try:
        if run_store.end_run(run_id, RUN_ENDINGS[_SETTLE_ROUTES[reason]], ended_at=instant_to_iso(now)):
            return None
    except (FileNotFoundError, NotADirectoryError) as e:
        raise RunGone(run_id) from e  # 写的中途这个名字下已没有目录或文件
    except UNREADABLE_RECORD_ERRORS as e:
        return Reason.UNREADABLE, e  # 锁内读到的运行态解析不了
    try:
        state = run_store.load_run_state(run_id)
    except UNREADABLE_RECORD_ERRORS as e:
        return Reason.UNREADABLE, e
    if state is None or state.status not in TERMINAL_STATUSES:
        raise RunGone(run_id)
    return Reason.ALREADY_FINISHED, None


def _generate_report(target: SettleTarget, run_id: str, meta: RunMeta | None, definition: DefinitionRead,
                     definition_error: Exception | None, *, clock: Callable[[], datetime]) -> ReportNotWritten | None:
    """写成之后按被处置的 run 标识生成报告；生成了返回 None，没有生成返回原因。失败隔离在这里，不记日志、不抛出：报告是派生视图，
    处置已经写成（ADR 0054 决策七「报告」）。"""
    if meta is None:
        return ReportNotWritten(ReportMissing.DEFINITION_UNREADABLE, _DEFINITION_UNREADABLE_DETAIL[definition], definition_error)
    try:
        generate_report_from_record(run_id, meta, target.run_store, target.result_store, target.report_store,
                                    created_at=instant_to_iso(clock()))
    except NamedDetailMissing as e:
        return ReportNotWritten(ReportMissing.DETAIL_MISSING, str(e), e)
    except UNREADABLE_RECORD_ERRORS as e:
        return ReportNotWritten(ReportMissing.RECORD_UNREADABLE, f"这个 run 的记录读不出：{e}", e)
    except OSError as e:
        return ReportNotWritten(ReportMissing.ACCESS_FAILED, f"读写这个 run 的记录或报告失败：{e}", e)
    except Exception as e:  # 派生视图的失败不改变处置已写成这一结果
        return ReportNotWritten(ReportMissing.OTHER, f"生成报告时出错：{e}", e)
    return None


# ---- 不给 run 标识时：处理哪些 run ----


def unfinished_run_ids(target: SettleTarget) -> list[str]:
    """不给 run 标识时要处置的 run：全部未结束（pending、running）与运行态读不出的 run，按 run 标识降序（ADR 0054 决策八「settle-runs」
    一条）。经 `RunStore.list_runs` 列举，读失败原样抛出。"""
    return [row.run_id for row in target.run_store.list_runs([Status.PENDING, Status.RUNNING], limit=None)]

