"""无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。

组合根职责（local 执行环境特有）：把 core 的 reconciler（纯编排）接到真 subprocess 世界——
- **SubprocessLauncher**：机制四认领成功后被 reconciler 调，起一个 worker（复用 SubprocessEngine）、
  在独立线程里读它的 fd3 事件流旁路落 SqliteEventLog（赋 worker 段单调 seq）、worker 退出后 `handle.wait()`
  拿 exitcode 写 task_exited（扮演平台侧退出观察者，机制二 local 对位）；另按墙钟检查这个 job 的截止时刻，到点停 worker。
  worker 不改、对 SQLite 无知（0034）。
- **per-run reconciler 进程**：`submit` 时 setsid fork 出来的轻进程，循环 tick 直到 run 收尾自退；读不到可用的运行定义时以结束写的
  error 变体结束 run（`end_run_for_unusable_definition`）。`status --wait` 接力走同一个循环，另把别人认领、观察链已断的 job 判为
  超时（`_recover_timed_out_claims`）；它读不到运行定义时不写。

守窄腰：gherkai_core.reconcile 对「怎么起 worker」无知（经 Launcher 注入）；本模块在产品本体包 gherkai_runtime（组合根共享层，
ADR 0016「演进」节）、可 import SubprocessEngine/SqliteEventLog，core 不可。云端后端的 Launcher 是
`gherkai_core.adapters.cloud_launcher.CloudLauncher`（ECS RunTask），与本模块共用同一 `gherkai_core.reconcile.tick`。
"""
from __future__ import annotations

import threading
import time
from collections.abc import Collection
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from gherkai_core.adapters.event_log import SqliteEventLog, make_raw_sink
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.adapters.subprocess_engine import SubprocessEngine
from gherkai_core.model import Job, RunMeta, Status
from gherkai_core.reconcile import TickOutcome, tick, write_report_from_record
from gherkai_core.run_deadline import deadline_of, job_cutoff
from gherkai_core.run_status import definition_unavailable_ending
from gherkai_core.serialize import instant_from_iso, instant_to_iso
from gherkai_runtime import compose
from gherkai_runtime import names  # 叶子模块（零依赖，见其模块头）

# 推进进程检查执行中 job 截止时刻的间隔（秒）：每个执行中的 job 一个检查线程，按这个间隔读一次墙钟。它只决定到点之后最多晚多少
# 发出停止请求，不进任何记录；超时的归因与说明由认领时刻、预算与期限重算，与检查的早晚无关。
_CUTOFF_CHECK_INTERVAL_S = 0.25

# 接力判超时的固定余量（秒）：墙钟严格晚于截止时刻加这么多、
# 仍没有退出记录时，接力方补写一条判为超时的未知退出。余量只挡认领方与接力方各自的检查间隔与时钟抖动，比各引擎的停止宽限期短（各引擎
# 自报的值都在数十秒以上），不覆盖认领方到点催停之后 worker 的协作收尾：认领方还在、worker 仍在停止宽限期内收尾时，接力方先写下这一条，
# 认领方随后写下的真实退出记录覆盖它；补写之后、真实退出记录写下之前若有一轮 tick（接力方或认领方的）读到这一条，就按超时为这个
# job 存下判定明细、写下终态，运行态里的这个终态此后不再改变。判定明细按 scope_id 保存：两个推进方重叠、另一方读到的是随后的真实
# 退出时，它存下的明细会覆盖这一份，与运行态里的终态不一致（由判定明细的点名消除）。调大这个值换不来「不抢先」，只推迟认领方真不在
# 时的收敛。
_RECOVERY_MARGIN_S = 10.0


class RunDefinitionMissing(FileNotFoundError):
    """run 的运行态在而提交记录读不到（`build_local_reconcile`）：落点被删、写坏，或 --report-dir 指错。它是 FileNotFoundError 的
    子类，查询命令照旧按「找不到」以退出码 2 结束；后台推进进程是这个 run 的推进器，据此以结束写的 error 变体结束它（与提交记录形态
    违约同一种处理，ADR 0034 机制三「不经推进步骤的收尾」条）。"""


class _ExitOrCutoff:
    """一个 job 的「看到 worker 退出」与「到点决定」之间的互斥（ADR 0054 决策二后台推进条「截止时刻与说明」）。

    推进线程看到退出（读退出时刻、标记已退出、读超时标志）与检查线程的一次到点决定（确认还没有看到退出、读墙钟、已过截止时刻就置
    超时标志）各在同一把锁下一次做完，先后只有一种：推进线程先看到退出的，检查线程之后不再置标志，退出记录带的是看到退出那一刻的
    标志；检查线程先决定的，标志已经置上，退出时刻是推进线程随后读的那一刻。不互斥时，检查线程可以落在推进线程读过退出时刻、还没
    标记已退出的间隔里置上标志，记录成了「退出时刻不晚于截止时刻、却带超时标志」，投影判为超时，而前台在截止时刻之前看到同样的退出
    判的是 worker 自己的错误。

    锁内只读墙钟与改标志：等进程、发停止请求（会等到停止宽限到点）、写退出记录都在锁外，停止请求发出之后推进线程照常看到退出。
    每个 job 一个实例，不同 job 之间互不阻塞。
    """

    def __init__(self, clock: Callable[[], datetime], cutoff_at: datetime) -> None:
        self._clock = clock
        self._cutoff_at = cutoff_at
        self._lock = threading.Lock()
        self._exited = threading.Event()
        self._timed_out = False

    def see_exit(self) -> tuple[datetime, bool]:
        """推进线程看到 worker 退出：读退出时刻、标记已退出、读超时标志，返回 (退出时刻, 超时标志)。"""
        with self._lock:
            exited_at = self._clock()
            self._exited.set()
            return exited_at, self._timed_out

    def stop_due(self) -> bool:
        """检查线程的一次到点决定：还没有看到退出、且墙钟严格晚于截止时刻时置超时标志并返回 True，停止请求由调用方在锁外发出；
        已经看到退出（不再读墙钟）或还没到点时返回 False。"""
        with self._lock:
            if self._exited.is_set() or not self._clock() > self._cutoff_at:
                return False
            self._timed_out = True
            return True

    def wait_for_exit(self, timeout_s: float) -> bool:
        """至多等 timeout_s 秒，推进线程看到退出即返回 True。"""
        return self._exited.wait(timeout_s)


class SubprocessLauncher:
    """local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。

    launch(job, cutoff_at=…)：起 worker（resolver 按 engine 选 SubprocessEngine）→ 后台线程消费 fd3 事件流落 SQLite +
    退出后写 task_exited。非阻塞返回（reconciler 继续 tick，不等 worker 运行结束——那是 fire-and-forget，事件
    异步落 SQLite、下轮 tick 从 SQLite 重放看到进展）。

    同时 enforce 截止时刻：cutoff_at 是 tick 在认领时算好的截止时刻（认领时刻加 job 预算，以运行期限封顶）。
    每个执行中的 job 一个检查线程，按短间隔读注入的墙钟，过了
    cutoff_at 即先置 timed_out 标志再 handle.stop(引擎停止宽限期)（协作停，保会话清理、不持续计费）；停止在检查线程里等完，不阻塞
    推进循环。worker 退出后 _pump 的 record_exit 带上标志与它看到退出的那一刻（退出时刻，读同一个注入的墙钟），project 按起作用的
    截止时刻判：job 的预算到点为 ERROR+timeout，运行期限截断为 ABORTED；起作用的是哪一个由运行态里的认领时刻、预算与期限重算
    （ADR 0034「job timeout」节执行方式表的 local 后台推进进程一行，ADR 0054 决策二后台推进条「截止时刻与说明」）。看到退出与
    到点决定经 `_ExitOrCutoff` 互斥，已经看到退出之后检查线程不再置标志。启动器只记这两项事实、不比较截止时刻：worker 在截止时刻之后、下一次检查之前自己退出时，
    退出记录不带标志，由投影按退出时刻晚于截止时刻判为超时，与前台终结之前的那次检查、云端
    后台的退出记录是同一个判断（内容完整的照旧不改判，由终结函数保证；ADR 0054 决策二后台推进条「截止时刻与说明」）。按墙钟而不按
    单调时钟：截止时刻由认领时刻这个墙钟时刻算出，单调时钟在系统休眠时不走，合盖之后醒来的推进进程按墙钟才知道已经过了截止时刻
    （ADR 0054 决策二「检查用墙钟」一段）。检查一直持续到 worker 进程退出，不止到事件流结束：关了事件通道却不退出的 worker 过了截止
    时刻同样被停下。

    **绑死 SubprocessEngine（不是任意 `Engine`）**：launch 用 `run_scope(job, raw_sink=...)` 拿原始事件行，
    而 `raw_sink` 是 SubprocessEngine 的扩展形参、**不在 Engine port 契约里**（ADR 0034「Engine port 演进」）。
    故 resolver 的返回类型在此收窄——喂进别的 adapter 是运行时 TypeError，类型上先说明白。
    """

    def __init__(self, resolver: Callable[[str], SubprocessEngine], event_log: SqliteEventLog, *,
                 min_grace_fn: Callable[[str], float], clock: Callable[[], datetime]) -> None:
        self._resolver = resolver
        self._event_log = event_log
        # engine→grace 下限，**必传**（组合根传 compose.engine_min_grace；测试传显式 fake）：timeout stop 用它当协作停
        # 宽限（grace 小于引擎自报的收尾下限时，worker 可能在释放会话或保存产物之前被强制终止，ADR 0024 grace 硬约束——
        # 超时停止也不豁免）。不留缺省：任何回落值都必然低于引擎下限（如 Nova 150s），漏注入宁可在构造期抛 TypeError，
        # 别让超时停止静默变成强制终止、丢掉会话清理（同 run_reconcile_loop 的 clock 立场）。
        self._min_grace_fn = min_grace_fn
        # 截止时刻检查与退出时刻读的墙钟，**必传**（组合根传 `compose.now`，与推进循环注入 tick 的是同一个读取点；测试传假墙钟），返回
        # 带时区的 datetime：截止时刻由同一个读取点取的认领时刻算出，检查与投影比较的才是同一个时钟。
        self._clock = clock
        # 本 launcher 起过的 scope（run_reconcile_loop 的接力恢复扫豁免它们——自家 job 的截止时刻有检查线程在管）
        self.owned_scopes: set[str] = set()

    def launch(self, job: Job, *, cutoff_at: datetime) -> None:
        scope_id = job.scope_id
        self.owned_scopes.add(scope_id)
        engine: SubprocessEngine = self._resolver(job.engine)
        # raw_sink：SubprocessEngine 读 fd3 每行原始 JSON（解析前）旁路调它——落 SQLite 存原样、按到达序续号；写法与同步 run 的
        # 记录器同一份（gherkai_core.adapters.event_log.recording，ADR 0042 决策七）。
        raw_sink = make_raw_sink(self._event_log, scope_id)

        # grace 下限要 spawn 一次 worker 自述才能取得（ADR 0024「引擎自报下限」）、**会抛**（旧 worker 不认入口 /
        # 定位不到 / 答非契约）——故必须问在起 worker **之前**：抛在 run_scope 之后就是「worker 已起、_pump 没起」，
        # tick 的 launch 失败补偿（退出码未知的退出记录）前提是「进程没起、平台观察者无从观察」，那时留下的是
        # 没人读 fd3、没人 wait、没人 stop 的孤儿 worker（真会话真计费）+ 泄漏的事件通道 fd。
        grace = self._min_grace_fn(job.engine)
        handle, events = engine.run_scope(job, raw_sink=raw_sink)
        watch = _ExitOrCutoff(self._clock, cutoff_at)
        # 不持线程引用：daemon 线程无人 join（循环何时结束由 tick 的结果决定，正常收尾时每 job 都有
        # _pump 写的退出记录），存下来只会随 job 数单调增长。
        threading.Thread(
            target=self._watch_cutoff, args=(handle, watch, grace), daemon=True,
            name=f"cutoff-{scope_id}",
        ).start()
        threading.Thread(
            target=self._pump, args=(scope_id, handle, events, watch), daemon=True,
            name=f"launcher-{scope_id}",
        ).start()

    def _watch_cutoff(self, handle, watch: _ExitOrCutoff, grace: float) -> None:
        """一个 job 的截止时刻检查：推进线程看到 worker 退出之前，每隔 `_CUTOFF_CHECK_INTERVAL_S` 做一次到点决定，墙钟严格晚于截止
        时刻即停它，只停一次；已经看到退出的不再决定、直接结束。先查再等：启动调用本身拖过了截止时刻时，启动之后立即停。"""
        while not watch.stop_due():  # 到点时标志已在决定里置上：_pump 之后看到的退出必带它（归因链时序）
            if watch.wait_for_exit(_CUTOFF_CHECK_INTERVAL_S):
                return
        try:
            handle.stop(grace)  # 协作停（SIGTERM→grace→SIGKILL 兜底，adapter 既有语义）；在互斥之外发，等宽限期间 _pump 照常看到退出
        except Exception:
            pass  # stop 失败（如进程恰已退）→ 交给 _pump 的 wait 收敛

    def _pump(self, scope_id: str, handle, events, watch: _ExitOrCutoff) -> None:
        """驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写 task_exited。

        迭代 events 只为驱动 fd3 读（每行触发 raw_sink 落库）——迭代产出的 Event 本身丢弃（我们要的是原始行、
        已落库）。异常（含 _read_events 对非零退出码抛的 WorkerExitError：自行异常退出的正码与被信号强杀的负码
        都抛，网络故障码抛其子类 WorkerNetworkError；也含事件行解析失败的 ValueError）吞掉：下面 handle.wait()
        拿真实 exitcode 写 task_exited，让 project 据「两件都要」判终态（机制二）。无论如何都写退出记录——
        否则该 job 永远 RUNNING、reconciler 卡住不收尾。worker 退出之后才结束截止时刻检查（见类 docstring）。

        退出记录带两项事实：超时标志（检查线程已经到点决定停止），与退出时刻（拿到退出码之后读一次注入的墙钟，即推进进程看到 worker
        退出的那一刻；wait 拿不到退出码时同样记这一刻）。两项与标记已退出在 `_ExitOrCutoff.see_exit` 里一次读完，与检查线程的到点决定
        互斥。不在这里比较截止时刻：worker 在截止时刻之后、检查线程下一次到点决定之前自己退出（如异常退出）时，由投影按退出时刻判为
        超时（类 docstring）。
        """
        try:
            for _event in events:
                pass  # 落库已在 raw_sink 完成；此处只驱动 fd3 读到 EOF
        except Exception:
            pass  # worker 异常退出——exitcode 由下面 wait() 拿，经 task_exited 让 project 判 error
        finally:
            try:
                exit_code = handle.wait()
            except Exception:
                # 拿不到退出码 → None（有退出记录却无码 → 投影判 ERROR，**不是**宽限态；ADR 0034 机制二「退出码缺失」条）
                exit_code = None
            # 看到退出：结束截止时刻检查（检查已经决定的停止照常记为超时），落库在互斥之外
            exited_at, timed_out = watch.see_exit()
            self._event_log.record_exit(scope_id, exit_code, timed_out=timed_out, exited_at=exited_at)


def run_reconcile_loop(
    run_id: str,
    meta: RunMeta,
    event_log: SqliteEventLog,
    run_store: LocalRunStore,
    launcher: SubprocessLauncher,
    max_concurrency: int,
    *,
    clock: Callable[[], datetime],
    poll_interval_s: float = 0.5,
    result_store=None,
    report_store=None,
) -> None:
    """per-run 进程的推进循环：反复 tick 直到 run 收尾（ADR 0034「推进器与触发源」第 1 条）。

    clock：**必传**的墙钟（组合根传 `compose.now`；测试传 fake 保确定性），返回带时区的 datetime。tick 经它取时刻，接力判超时按它
    判断截止时刻是否已到，这里写进报告的时刻经 `serialize.instant_to_iso` 从它写出，同一份 RunState 里只有一种时间戳写法，故不留
    缺省。launcher 的截止时刻检查读的是它构造时注入的墙钟，组合根两处传的是同一个读取点。
    tick 幂等——崩了 status --wait 可接力（状态全持久）。循环按 tick 的结果分支（batch shape：运行结束即停、不常驻）：
    - `TickOutcome.COMMITTED`（这一方的写使 run 成为终态）：从记录生成 RunReport 后退出；
    - `TickOutcome.ENDED`（run 已结束、使它成为终态的不是这一方）：不写报告、直接退出。循环只按 run 级的结果结束，不依赖「每个
      job 都会到终态」（ADR 0034 机制三「run 级状态只进不退」条④）；
    - `TickOutcome.CONTINUE`：做接力超时恢复，等一个轮询间隔再 tick。
    退出后由调用方照常拆隧道（`drive_local_reconcile`）。推进进程已不在的 run 过了期限之后由 `status --wait` 进入本循环时，tick 不再
    认领；接力判超时为原推进进程认领、墙钟已过截止时刻加 `_RECOVERY_MARGIN_S` 仍没有退出记录的 job 补写超时的退出记录，下一轮 tick
    先写下这些 job 的终态，没有执行中的 job 之后由到期的结束写结束这个 run，不启动任何 job。

    result_store/report_store（可选）：判定明细（jobs/*.json）由 tick 在每个 job 得出结果的那一轮、写下它的终态之前存下（注入给
    tick；ADR 0030 决定三「后台推进同守」条）；RunReport（index/manifest）在这一方的写使 run 成为终态之后，由
    `write_report_from_record` 从记录生成（派生、失败隔离）：这一次 tick 交给终态写的明细用 tick 交回的那一份，较早轮次写下终态的
    job 的明细从 result_store 按 scope_id 读回。注入 None（测试）则跳过对应的一步，报告只用 tick 交回的明细。
    """
    while True:
        outcome = tick(run_id, meta, event_log, run_store, launcher, max_concurrency,
                       clock=clock, result_store=result_store)
        if outcome.outcome is TickOutcome.ENDED:
            return
        if outcome.outcome is TickOutcome.COMMITTED:
            # 报告从记录生成，入口是 core 唯一的一份，云端推进器 Lambda 调的是同一个。生成在终态写之后、失败无人重试，抛出去会让本进程
            # 带着未写的报告退出，还会跳过拆隧道那步（`drive_local_reconcile` 的 cleanup_tunnel 在本函数返回后才执行）；所以读运行态、
            # 读回较早轮次的明细、组装与写报告整段在入口的失败隔离之内（ADR 0030 决定三「ReportStore.write 失败隔离」框，ADR 0034
            # 机制三「run 级状态只进不退」条④）。
            write_report_from_record(meta, run_store, outcome.details, report_store, result_store=result_store,
                                     created_at=instant_to_iso(clock()))
            return
        _recover_timed_out_claims(run_id, meta, event_log, run_store, launcher.owned_scopes, now=clock())
        time.sleep(poll_interval_s)


def drive_local_reconcile(report_dir: str, run_id: str, max_concurrency: int, *, region=None, profile=None,
                          poll_interval_s: float = 0.5) -> None:
    """local 推进的**唯一入口**：装配 → tick 到 run 收尾 → 拆隧道。per-run 进程与
    `status --wait` 接力都调这里——曾在 cli 两处逐字复写这三句装配，改一处漏一处就让接力者与 per-run 行为分叉。"""
    meta, log, store, launcher, mc, rstore, pstore = build_local_reconcile(
        report_dir, run_id, max_concurrency, region=region, profile=profile)
    run_reconcile_loop(run_id, meta, log, store, launcher, mc, poll_interval_s=poll_interval_s,
                       clock=compose.now, result_store=rstore, report_store=pstore)
    cleanup_tunnel(report_dir, run_id)  # 隧道收尾（有 tunnel.json 才动作，ADR 0035）；接力者同样兜底拆


def _recover_timed_out_claims(run_id: str, meta: RunMeta, event_log, run_store, owned_scopes: Collection[str], *,
                              now: datetime) -> None:
    """接力判超时：**他人认领、本进程无 handle** 的
    RUNNING job，墙钟严格晚于它的截止时刻加 `_RECOVERY_MARGIN_S` 仍没有退出记录时，按观察链已断处理（截止时刻检查随认领方进程丢失，
    worker 因 fd3 断管随之早亡），补写一条判为超时的未知退出收敛，防止 run 一直停在未结束。now 是这一轮的墙钟。

    截止时刻由运行态里的认领时刻、job 预算与期限经 `run_deadline.job_cutoff` 算出，与认领方是同一个算法（以期限封顶）。补写经
    `record_timed_out_if_absent`，是条件写：只在这个 job 还没有退出记录时写入，认领方恰在接力方点查之后、补写之前落下的真实退出记录
    不被盖掉（点查只是省掉一次写）；补写之后才到的真实退出照旧覆盖补写的那一条（INSERT OR REPLACE 同 key）。

    这个判定条件保证不了不抢先：认领方还在、到点催停之后 worker 仍在停止宽限期内收尾时，接力方照样补写；补写之后、真实退出之前读到它
    的那一轮 tick 按超时存下这个 job 的判定明细、写下终态，运行态里的终态此后不再改变，明细仍可能被另一个推进方按真实退出存下的那一份
    覆盖（见 `_RECOVERY_MARGIN_S`）。

    自家 job（owned_scopes）不扫：launch 时的截止时刻检查在管、且要给足协作停宽限。认领时刻缺失、读不出或不带时区的 job 不处置
    （除超时外无权臆断他人认领的死活）。这里按观察链已断处理，补写是唯一的收敛路径。
    """
    state = run_store.load_run_state(run_id)
    if state is None:
        return
    job_by_scope = {j.scope_id: j for j in meta.jobs}
    deadline = deadline_of(meta)
    margin = timedelta(seconds=_RECOVERY_MARGIN_S)
    for sid, js in state.jobs.items():
        if js.status != Status.RUNNING or sid in owned_scopes:
            continue
        job = job_by_scope.get(sid)
        if job is None:
            continue  # 运行定义里没有这个 job，不处置
        try:
            claimed_at = instant_from_iso(js.claimed_at)
        except ValueError:
            continue  # 没有起算点，不处置
        cutoff = job_cutoff(claimed_at, job.timeout_s, deadline).at
        # 廉价过滤都过了才点查退出记录（has_exit 主键点查，对位 cloud `_handle_timeout`），不为判一个 scope 重放整个 run 的事件。
        # 补写本身是条件写：点查之后才落下的真实退出记录不被盖掉
        if now > cutoff + margin and not event_log.has_exit(sid):
            event_log.record_timed_out_if_absent(sid)  # 退出码未知：无观察到的退出码，诚实留空；也没有可观察的退出时刻


# ============================================================================
# per-run 进程：从 run_id + 本地落点重建装配、运行 reconcile loop（submit setsid fork 它）
# ============================================================================


def _paths(report_dir: str, run_id: str):
    """local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/（路径取 compose.events_db_path 单点）。"""
    return Path(report_dir), compose.events_db_path(report_dir, run_id)


def build_local_reconcile(report_dir: str, run_id: str, max_concurrency: int,
                          region: str | None = None, profile: str | None = None):
    """从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。

    per-run 进程自包含、不依赖父进程内存（fork 后父可退）：definition 已由 submit 的 create_run 落 RunStore，
    这里 load_run_meta 读回；SqliteEventLog/LocalRunStore 都是文件路径，从 report_dir+run_id 重建即同一份。
    返回 (meta, log, store, launcher, max_concurrency, result_store, report_store) 供 run_reconcile_loop
    （后两个是判定明细与报告的落点，与 RunStore 同 <report_dir>/<run_id>/）。
    返回的 max_concurrency 优先取 meta（ADR 0034 机制四：随 definition 走），入参只作 meta 缺值时的回落——
    per-run 进程与 `status --wait` 接力者同读 meta，接力者不再拿自己那侧的 flag 值覆盖 submit 时的声明。
    worker cmd 走定位链（ADR 0037 决策 3，不再由仓库结构推导，故本函数不收 repo）；env 覆写对两宿主自然可见
    （per-run 继承提交进程 env、接力者用自己的 env）。
    """
    # region/profile 的解析链与前台 run 同源（`compose.resolve_aws_identity`；顺序见 ADR 0016 决策 C 与 ADR 0053
    # 决策 2）：配置文件那一层由 CLI 在 fork 或接力前解析好、经参数传入，本函数按 ADR 0053 决策 1 不读配置文件，
    # 只补环境变量与 profile 的末段回落。此前原样透传 None：profile-only/config-only 的使用方下 worker env 不注入 AWS_REGION，
    # Nova worker 的 AgentCore validate_region 见 None 即崩（exit 1、零事件；detached 实际运行复现）。
    # 单点在 `compose.resolve_aws_identity`（而非各调用方各写一份）：submit fork 的 per-run /
    # status --wait 接力 / 手动 _reconcile 三路全覆盖。
    region, profile = compose.resolve_aws_identity(region, profile)

    root, db_path = _paths(report_dir, run_id)
    store = LocalRunStore(root)
    meta = store.load_run_meta(run_id)
    if meta is None:
        # 正常路径下 submit 的 create_run 早已落 RunStore，走到这里说明落点被删/写坏或 report_dir 指错。
        # 文案按产品语言给：常见形态已由 `_cmd_status` 的 run 存在性检查翻成退出码 2；这里兜住剩下的两条——
        # run_state 在而 definition 缺（落点被删/写坏）的裸 traceback，以及 per-run 后台进程把它写进 reconcile.log。
        raise RunDefinitionMissing(f"找不到这个 run 的提交记录，无法继续推进：{run_id}"
                                f"（产物目录被删或写坏？也确认 --report-dir 与提交时一致）")
    log = SqliteEventLog(db_path)
    # 产物落点 env 注入（同步 run 路径的 build_engines 一致）：nova/midscene 产物落 <report_dir>/<run_id>/ 下。
    nova_logs_dir = root / run_id / names.ARTIFACT_SUBDIR["novaact"]  # 子目录名单点（三宿主同名，ADR 0029）
    midscene_run_dir = root / run_id / names.ARTIFACT_SUBDIR["midscene"]
    engines = compose.build_engines(
        nova_logs_dir=nova_logs_dir, midscene_run_dir=midscene_run_dir,
        region=region, profile=profile,
        # 额外请求头随 definition 持久化（ADR 0035：submit 进程算好落 META，per-run 重建端读回注入）
        extra_http_headers=dict(meta.extra_http_headers) if meta.extra_http_headers else None,
        session_warmup_url=meta.session_warmup_url,  # 会话预热地址同理随 definition 走（ADR 0051 决策 13）
        # 使用方 step 目录同理随 definition 走（ADR 0037 决策 4）：**读回、绝不在此重解析 `./steps`**——
        # 本函数的两个宿主（per-run 进程 / `status --wait` 接力者）CWD 与提交进程各不相同，
        # 重解析必让同一个 run 在三个宿主下用到不同的确定性 step 集，判定不可复现。
        steps_dir=meta.steps_dir,
        # 本 run 的 id（ADR 0024「run_id + scope_id 注入 worker」条）：经 env RUN_ID 注给 worker，编码会话名的 run 段
        # （ADR 0051 决策 3、4）；取被推进的这个 run，宿主 shell 里的同名值由 build_engines 清掉
        run_id=meta.run_id,
    )
    resolver = compose.make_resolver(engines)
    launcher = SubprocessLauncher(resolver, log, min_grace_fn=compose.engine_min_grace, clock=compose.now)
    # ResultStore + ReportStore（判定明细与报告，落点与 RunStore 同 <report_dir>/<run_id>/，对齐同步 run 路径）
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.report_store.local import LocalReportStore
    result_store = LocalResultStore(root)
    report_store = LocalReportStore(root)
    effective_mc = meta.max_concurrency if meta.max_concurrency is not None else max_concurrency
    return meta, log, store, launcher, effective_mc, result_store, report_store


def end_run_for_unusable_definition(report_dir: str, run_id: str, reason: str) -> bool:
    """本机后台推进进程读不到可用的运行定义时，以结束写的 error 变体结束这个 run（与云端推进器同一写法，ADR 0037 决策 7，ADR 0031
    决定三「结束写」小节「运行定义不可用时」条）：每个未结束的 job（含执行中的）记 error，reason 写进 run 级说明与这些 job 的说明；
    不存明细、不生成报告（报告按运行定义逐个列出 job，读不到运行定义就组装不出）。reason 取 `run_status` 里的几句之一。

    只由 submit 启动的后台推进进程调用：它是这个 run 的推进器。`status --wait` 接力不调用，读不懂运行定义可能只是接力方的版本不同，
    原来的推进进程可能仍在正常推进。返回是否写成：run 已被别处结束或运行态不存在时没有写成，运行态不变。"""
    return LocalRunStore(Path(report_dir)).end_run(run_id, definition_unavailable_ending(reason),
                                                   ended_at=instant_to_iso(compose.now()))


# ============================================================================
# 隧道收尾（ADR 0035 决策 3）：pid 经 tunnel.json 跨进程交棒（submit 写 → per-run/接力者收）
# ============================================================================


def write_tunnel_file(report_dir: str, run_id: str, info) -> None:
    """local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。"""
    import json as _json

    path = Path(report_dir) / run_id / "tunnel.json"
    path.write_text(_json.dumps({"pid": info.pid, "url": info.url, "local_origin": info.local_origin},
                                ensure_ascii=False), encoding="utf-8")


def cleanup_tunnel(report_dir: str, run_id: str) -> None:
    """收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。"""
    import json as _json

    from gherkai_runtime.tunnel import stop_tunnel

    path = Path(report_dir) / run_id / "tunnel.json"
    if not path.exists():
        return
    try:
        stop_tunnel(int(_json.loads(path.read_text(encoding="utf-8"))["pid"]))
        path.unlink()
    except (OSError, ValueError, KeyError):
        pass  # 收尾是 best-effort：文件损坏/已被并发收尾者处理 → 不击穿主流程
