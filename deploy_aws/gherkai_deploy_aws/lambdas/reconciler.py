"""reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。

events 表开 Stream（NEW_IMAGE），worker PutItem 执行事件 / 退出观察者写 task_exited → Stream 触发本 handler。
它从 Stream records 提取涉及的 run_id 集（去重），对每个 run 调 gherkai_core.reconcile.tick 推进一步（读运行态与全量重放、
投影写，为这一轮已有结果的 job 各存一份带新标识的明细、写终态并点名它，再由 plan_next 决定认领并起下一个 job 或做到期的结束写）。tick 幂等 +
CAS/HWM 条件写兜底——Stream 按分片并发触发多个本 handler 实例、叠加 status --wait 接力，全部安全（真 DDB 已验）。

**cloud 组合根（Lambda 装配）**：cold-start 读 env 造 boto3 client + 三 store adapter + FargateEngine + CloudLauncher
注入纯 reconcile.tick——**是组合根注入、非 ports 内部 env-sniff 全局单例**（[0016] 禁的 GlobalConfigManager 反模式，
此处每次 handler 显式构造、无隐式全局态）。core 一行不为 cloud 改（同 local，只换注入的 EventLog/Launcher/RunStore）。

打包：本文件是 **asset 原料**（住在 provider 包 `gherkai_deploy_aws/lambdas/`，摊到 zip 根，ADR 0037 决策 6）。
env：**IaC 注入**（`gherkai_deploy_aws/stack.py` 的 reconciler/kicker Function）的有：
RUNS_TABLE / EVENTS_TABLE / ARTIFACTS_BUCKET / CLUSTER / PREFIX / REGION / SUBNETS / SECURITY_GROUPS /
MAX_CONCURRENCY（**部署侧 per-run 并发 cap**、非真源——真源是 definition 的 `RunMeta.max_concurrency`，取
min，ADR 0034 机制四；数值真源在 IaC 一处，本文件缺省只在 env 漏注时保守回 1、不复制部署值）/ KICKER_ARN / SCHEDULER_ROLE_ARN（job timeout 到点触发器用，ADR 0034「job timeout」节）；**本文件缺省供给、IaC 不注入** 的是 REPORT_DIR（reports）/ ASSIGN_PUBLIC_IP（ENABLED，与公有子网
配套）——要改产物落点前缀或走私有子网时才在 IaC 显式给。

**worker 镜像用哪个 task-def revision 不经 env**（ADR 0038 不变量「运行时只用 definition 里的显式 revision」）：
只读 definition 的 `RunMeta.worker_task_defs`；缺该字段的云端 definition 是定义违约，`_load_definition` 以结束写的 error 变体结束
这个 run、不推进（ADR 0037 决策 7，ADR 0031 决定三「结束写」小节「运行定义不可用时」条）。
**推进器绝不用模板 revision**——其镜像栏是 `latest` 占位，全新 prefix 上从未推过该 tag，拉镜像会拖到
Fargate 启动期才失败（ADR 0038 被拒方案）。故本文件不读任何模板 ARN 类 env。
"""
from __future__ import annotations

import datetime as _dt
import os
import time


def _run_ids_from_stream(event) -> set[str]:
    """从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch 可能多条同 run。

    **REMOVE 记录跳过**：events 表开 TTL（`expires_at`，两引擎的 event sink 写 emit+7d），TTL 过期删除同样进
    Stream、同样带 Keys。它不携带任何新信息，本道跳过它、不为它推进一次；推进方本次读到终态即返回（`_build` 的
    语义闸与 tick 的判停）。
    用 `.get` 只排除 REMOVE、**不做 INSERT 白名单**：events 表虽只 PutItem，同键重写（超时处置补写的退出记录
    被迟到的观察者以真退出码/归因重写）在 Stream 上是 MODIFY。
    IaC 侧的事件源 filter 同样滤掉 REMOVE（见 `stack.py` events 表的 `DynamoEventSource`）——那道要重新部署
    才生效，本道不依赖部署。语义闸另有一道在 `_build`（已终态的 run 整体 no-op），挡迟到重投/手工重放。
    """
    run_ids: set[str] = set()
    for rec in event.get("Records", []):
        if rec.get("eventName") == "REMOVE":
            continue
        keys = rec.get("dynamodb", {}).get("Keys", {})
        pk = keys.get("pk", {}).get("S")
        if pk and "#" in pk:
            # pk=run_id#scope_id：run_id 由 compose.new_run_id 生成、格式固定不含 #，scope_id 是 @scope 的用户文本、
            # 可能含 #——从左切（split 1）在任何输入下都取到正确 run_id；从右切遇含 # 的 scope_id 会切错、整条 Stream 静默 no-op。
            run_ids.add(pk.split("#", 1)[0])
    return run_ids


# ============================================================================
# job timeout（ADR 0034「job timeout」节的云端后端一侧）：到点触发器 + 超时处置 + 防御扫
# ============================================================================

# StopTask reason 里的超时哨兵串：经 STOPPED 事件 detail.stoppedReason 原样出现（现成通道、零新键空间），
# exit_observer 见它 → task_exited(timed_out=True) → 归因链收敛 ERROR+timeout。哨兵串的比对封在 `exit_from_task`
# 里，观察者 Lambda 与超时处置经该函数共用（都不各自 import 本常量）。reason 的其余部分按起作用的截止时刻分别写
# （`_stop_reason`），只给看 ECS 控制台的人读；归因不读它，job 的说明由投影按认领时刻、预算与期限重算。
TIMEOUT_STOP_SENTINEL = "gherkai-job-timeout"

# 日志里对起作用的那个截止时刻的说法：job 自己的墙钟预算到点，还是 run 的期限封顶（ADR 0054 决策二第 2 条）。
_CUTOFF_BY_TEXT = {"budget": "job 的墙钟预算用尽", "deadline": "run 已到允许运行的时间"}


def _job_cutoff(meta, job, claimed_at):
    """由运行态里的认领时刻、job 预算与运行期限重算这个 job 的截止时刻（`run_deadline.job_cutoff`，与推进步骤认领时算的、交给定时
    触发的是同一个算法，以期限封顶）。运行定义里没有这个 job，或认领时刻缺失、读不出、不带时区时返回 None——各调用点按各自现有的
    「缺认领时刻」分支处理。"""
    from gherkai_core.run_deadline import deadline_of, job_cutoff
    from gherkai_core.serialize import instant_from_iso

    if job is None:
        return None
    try:
        claimed = instant_from_iso(claimed_at)
    except ValueError:
        return None
    return job_cutoff(claimed, job.timeout_s, deadline_of(meta))


def _stop_reason(job, cutoff) -> str:
    """StopTask 的 reason：哨兵串在前（`exit_from_task` 靠它归因），后面说明是哪一个截止时刻到了。重算不出截止时刻时（缺认领时刻）
    只说到了时间上限。"""
    if cutoff is None:
        return f"{TIMEOUT_STOP_SENTINEL}: scope reached its time limit"
    if cutoff.by == "deadline":
        return f"{TIMEOUT_STOP_SENTINEL}: run deadline {cutoff.at.isoformat()} reached"
    return f"{TIMEOUT_STOP_SENTINEL}: scope exceeded {job.timeout_s:g}s budget"


def exit_from_task(task: dict) -> tuple[int, bool, str | None, _dt.datetime | None]:
    """ECS task 对象 → 退出记录四元组 (exit_code, timed_out, reason, exited_at)。**观察者与超时处置共用**（ADR 0034 机制二）。

    STOPPED 事件的 `detail` 与 `DescribeTasks` 的 `tasks[i]` 是同一个 Task 形状，故同一 task 两边算出同一内容、
    PutItem 同键幂等——超时处置对「已 STOPPED 却无退出记录」（事件丢投）落的记录，与迟到的观察者写入不互撞。
    exit_code：containers[] 首个带 exitCode 的（worker 是 essential 单容器）；**缺 → PLATFORM_FAILED_EXIT 哨兵**
    + reason=`stopCode: stoppedReason`（容器没能开始运行，机制二「退出码缺失」条）。哨兵与归因串的拼法都住 core
    （`platform_exit_reason`）。timed_out：stoppedReason
    含本模块 StopTask 时写入的哨兵串，即发过超时的停止请求（「job timeout」节归因链）。exited_at：task 的执行停止时刻，见
    `_task_stopped_at`。只记事实：是否已过截止时刻由投影判断，观察者读不到运行态与运行定义，也不需要读（ADR 0054 决策二后台推进条
    「截止时刻与说明」）。
    """
    from gherkai_core.project import PLATFORM_FAILED_EXIT, platform_exit_reason

    exit_code = None
    for c in task.get("containers", []) or []:
        if c.get("exitCode") is not None:
            exit_code = int(c["exitCode"])
            break
    stopped_reason = task.get("stoppedReason") or ""
    timed_out = TIMEOUT_STOP_SENTINEL in stopped_reason
    reason = None
    if exit_code is None:
        exit_code = PLATFORM_FAILED_EXIT
        reason = platform_exit_reason(task.get("stopCode"), stopped_reason)
    return exit_code, timed_out, reason, _task_stopped_at(task)


def _task_stopped_at(task: dict) -> _dt.datetime | None:
    """task 对象里的执行停止时刻（带时区）：`executionStoppedAt`（容器实际停下的时刻），没有时取 `stoppedAt`（ECS 记下 task 已停止的
    时刻，晚于前者，中间是平台的清理开销），都没有或读不出时为 None（退出记录不带退出时刻）。

    两种来源给出两种形态，分开处理：
    - STOPPED 事件的 detail 里是 ISO 串（带 `Z`）。串一律经 core 的 `serialize.instant_from_iso` 解析，与记录里的时刻同一处严格解析：
      不带时区或读不出的串当作这个字段没有值，按上面的次序取下一个字段。不补成 UTC：串里没写时区，补哪个时区都是猜。
    - boto3 的 DescribeTasks 回来的是 datetime（botocore 由纪元秒换算而来，带时区）。这是平台对象的归一化：不带时区的 datetime 按 UTC，
      带时区的保持原样。
    同一个时刻在两种形态下得到同一个值，写进退出记录的 ISO 串也就相同（同键先后写入内容不变）。读不出时不抛：观察者只有这一次机会
    写下退出记录，宁可缺退出时刻也不丢整条记录。"""
    from gherkai_core.serialize import instant_from_iso

    for key in ("executionStoppedAt", "stoppedAt"):
        value = task.get(key)
        if isinstance(value, _dt.datetime):
            return value.replace(tzinfo=_dt.timezone.utc) if value.tzinfo is None else value
        if isinstance(value, str):
            try:
                return instant_from_iso(value)
            except ValueError:
                continue
    return None


def _task_scope_id(task: dict) -> str | None:
    """RunTask 注入的 env SCOPE_ID 原样在 overrides.containerOverrides[].environment（观察者/超时处置同一提取术）。"""
    for co in task.get("overrides", {}).get("containerOverrides", []):
        for e in co.get("environment", []):
            if e.get("name") == "SCOPE_ID":
                return e.get("value")
    return None

# DescribeTasks 一次能收的 ARN 上限（AWS API 硬上限，超了直接 InvalidParameterException）——调用点据此分批。
_DESCRIBE_TASKS_MAX = 100

# 防御扫（claimed_at ②）的判定余量秒：Scheduler one-time schedule 是主机制，扫是双保险。余量是经验值：覆盖主机制的调度
# 精度分量（Scheduler 在截止时刻所在那一分钟内偏晚触发，不到 60 秒）加一次处置的常态耗时（异步 invoke 的排队、列 task、
# 停 task，秒级、没有硬上界），让主机制在常态下先于扫处置、也避开与在途的 STOPPED→exit_observer 链形成竞态；不是上界。
# 非正确性参数：两者先后颠倒也无害（处置幂等，复查截止时刻与退出记录后才动手）。
_DEFENSIVE_TIMEOUT_MARGIN_S = 120.0

# 到点处置复查截止时刻时的等待上界秒（ADR 0034「job timeout」节「到点不早于 deadline」条②）：Scheduler 只承诺
# 60 秒精度，按文档精度触发时离截止时刻至多约 59 秒；剩余超过它说明触发早于文档精度，此时不等待、不处置。醒来之后重读时钟
# 仍未到而接着等时，一次处置里各次等待之和同样不超过它。
_TIMEOUT_EARLY_WAIT_MAX_S = 60.0

# 每次等待的下限（秒）。「已到」指读到的墙钟严格晚于截止时刻（与本机启动器的检查、投影比较退出时刻的取法相同）：恰好等于时
# 剩余为零，只差不到一秒时剩余很小，按剩余时长等待都可能让循环空转。所以每次至少等这个固定量，同样计入等待额度：墙钟不前进时
# （测试注入的时钟、出故障的系统时钟）不论它停在哪里，至多约 60 次就用完额度、按不处置返回；每次醒来都要重读 job 状态与退出
# 记录，次数必须有界。代价是停止最多晚不到一秒，与分钟精度的定时触发相比可以忽略；它只会让停止更晚，不会提前。
_TIMEOUT_TIE_WAIT_S = 1.0

# 等到截止时刻之后本次调用还要完成的工作所留的秒数：处置（ListTasks 翻页、DescribeTasks、StopTask）与随后的一次 tick
# （读写 runs/events 表，可能起下一个 task）。kicker 用 Lambda 剩余时间减去它作为本次可等待的上界，免得等完被超时截断。
_TIMEOUT_HANDLING_RESERVE_S = 30.0


class EventBridgeTimeoutWatch:
    """job 截止时刻的云端到点触发器（ADR 0034「job timeout」节；`cloud_launcher.TimeoutWatch` 的实现）：CloudLauncher 起 task 前 arm 一个
    EventBridge Scheduler **one-time schedule**（at 取 core 传来的截止时刻，即认领时刻加预算、以运行期限封顶，带秒；
    ActionAfterCompletion=DELETE 到点自动删——无常驻轮询、idle 零成本）→ 到点 invoke kicker（payload {"run_id","timeout_scope"}）走超时处置。
    Scheduler 只承诺分钟精度、可能早于截止时刻触发，「不早于截止时刻」由处置侧复查保证（`_handle_timeout`），不靠 at 的秒数。

    schedule 名是 `names.job_timeout_schedule_prefix(prefix)` + sha1(run_id#scope_id) 的前 `names.JOB_TIMEOUT_DIGEST_LEN`
    位：确定性（重复 arm 幂等，ConflictException 视作已武装）、合法字符集（scope_id 可含中文/路径，不能直接入名）、≤64 字符
    （前提是 prefix 不超过 `names.prefix_max_len()`，由 stack 合成期校验保证）。
    名字空间前缀走命名真源 `gherkai_runtime.names`——IaC 的 IAM 资源域同源推导（ADR 0033「两层命名」，两侧硬契约）。
    best-effort：调用方（CloudLauncher）兜异常。
    """

    def __init__(self, scheduler_client, *, kicker_arn: str, role_arn: str, prefix: str) -> None:
        self._client = scheduler_client
        self._kicker_arn = kicker_arn
        self._role_arn = role_arn
        self._prefix = prefix

    def schedule_name(self, run_id: str, scope_id: str) -> str:
        import hashlib
        from gherkai_runtime import names

        digest = hashlib.sha1(f"{run_id}#{scope_id}".encode("utf-8")).hexdigest()[:names.JOB_TIMEOUT_DIGEST_LEN]
        return f"{names.job_timeout_schedule_prefix(self._prefix)}{digest}"

    def arm(self, run_id: str, scope_id: str, at: _dt.datetime) -> None:
        import json

        # 到点时刻就是截止时刻本身（tick 认领时算好，与到点复查、防御扫同一算法），arm 晚于认领的间隔不推后到点。
        at_utc = at.astimezone(_dt.timezone.utc)
        try:
            self._client.create_schedule(
                Name=self.schedule_name(run_id, scope_id),
                # at() 表达式不带时区后缀（Scheduler 默认 UTC）、只收到秒，小数秒截去。带秒而不取整到分钟：触发早于截止时刻
                # 的部分由处置侧复查补足，取整只会把取整与调度精度引入的推迟分量翻倍，异步投递与处置耗时另计（ADR 0034「job timeout」节被拒方案）。
                ScheduleExpression=f"at({at_utc.strftime('%Y-%m-%dT%H:%M:%S')})",
                FlexibleTimeWindow={"Mode": "OFF"},
                ActionAfterCompletion="DELETE",  # 到点触发即自动删（IAM 需随附 scheduler:DeleteSchedule）
                Target={
                    "Arn": self._kicker_arn,
                    "RoleArn": self._role_arn,  # Scheduler 服务 assume 它 invoke kicker（IaC 建）
                    "Input": json.dumps({"run_id": run_id, "timeout_scope": scope_id}),
                },
            )
        except self._client.exceptions.ConflictException:
            pass  # 同名已在（同 run+scope 重复 arm）→ 已武装，幂等


def _handle_timeout(run_id: str, scope_id: str, built, ecs_client=None, *, wait_budget_fn=None,
                    now_fn=None, sleep_fn=None) -> str:
    """超时处置（ADR 0034「job timeout」节的云端后端一侧）：仍 running 且截止时刻已到才动手。

    **先复查截止时刻**：Scheduler 只承诺分钟精度，触发可能早于截止时刻。job 已不在 running 或退出记录已在时照常 no-op、
    不等待（该节「到点不早于 deadline」条②）；仍 running 时由运行态里的认领时刻、Job.timeout_s 与运行期限重算截止时刻
    （`_job_cutoff`，以期限封顶，ADR 0054 决策二后台推进条「截止时刻与说明」）复查——已到直接处置；未到且剩余不超过等待额度
    （`_TIMEOUT_EARLY_WAIT_MAX_S` 与本次调用还能等的秒数取小）则等到截止时刻，重读 job 状态与退出记录、仍需处置才往下；
    剩余超过额度时不等待、不处置，打一行诊断、返回 skip-early，保护交给防御扫与 status --wait（宁可不处置也不提前处置）。
    「已到」指读到的墙钟严格晚于截止时刻，与本机启动器的检查、投影比较退出时刻的取法相同；恰好等于截止时刻算没到，按
    `_TIMEOUT_TIE_WAIT_S` 再等一次。醒来之后重新读墙钟：还没到（等待期间系统时钟被回拨，或恰好读到截止时刻）就在同一份额度内
    接着等，各次等待之和不超过额度；额度用完仍没到的同样返回 skip-early。发出停止之前因此必须有一次读到已过截止时刻（同一条
    「截止时刻与说明」）。
    认领时刻缺失、读不出或运行定义里没有这个 job 时无从复查，按已到处理。防御扫只对过了截止时刻加余量的 job 调本函数，复查直接通过。
    wait_budget_fn：返回本次调用还能用于等待的秒数（kicker 按 Lambda 剩余时间给出），**临睡前才调用**——复查前的两次读取
    也在消耗本次调用的时间，提前采样会把慢读取的耗时算进可等的额度、挤占处置与 tick 的预留；None 表示只受固定上界约束；
    now_fn / sleep_fn：时钟与等待，供测试注入；时钟缺省取组合根唯一的墙钟读取点 `compose.now`。

    处置：ListTasks(startedBy=run_id) **同时列 RUNNING 与 STOPPED**（后者 ECS 保留约 1h）→ DescribeTasks 按 overrides
    env SCOPE_ID 匹配 → 按 task 状态三路：
    - 运行中 → StopTask(reason 含哨兵，其余部分按起作用的是预算还是期限分别写，`_stop_reason`) → STOPPED 事件 → exit_observer
      记 task_exited(timed_out=True)（stop 后让观察链自然收敛，保住单一真源）；
    - **正在停止**（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不动、等观察者。曾只列 RUNNING、把它判成
      「无踪」直写 timed_out，与几秒后到达的真退出记录同键互覆——恰在预算点运行结束的 passed job 可被终判成 timeout；
    - **已 STOPPED 却无退出记录**（STOPPED 事件丢投）→ 用与观察者同一提取函数 `exit_from_task` 从 task 对象落真退出
      记录（同内容同键、幂等，含 task 的执行停止时刻），不臆造 timed_out：task 在截止时刻之后自己异常退出的，由投影按退出时刻判为超时。
    两个列表都无踪且无退出记录：预算已尽仍无确认完成 → 补写一条判为超时的未知退出收敛（`record_timed_out_if_absent`）——观察链已断时
    补写是唯一收敛路径。补写只在还没有退出记录时成立：观察者恰在上面的点查之后、补写之前落下真实的退出记录时
    补写不成立，按退出记录已在返回。返回处置结果串（日志/测试断言用）。
    """
    import boto3
    from gherkai_core.model import Status
    from gherkai_runtime import compose

    meta, event_log, run_store, *_ = built
    now_fn = now_fn or compose.now
    sleep_fn = sleep_fn or time.sleep

    def _check() -> tuple[str | None, str | None]:
        """读一次 job 状态：返回 (no-op 结果串, claimed_at)，结果串为 None 表示仍需处置。"""
        state = run_store.load_run_state(run_id)
        js = state.jobs.get(scope_id) if state is not None else None
        if js is None or js.status != Status.RUNNING:
            return "noop-not-running", None  # 到点时 job 早收敛/未知 → 幂等 no-op（best-effort 边界）
        # 只查本 scope（`DdbEventLog.has_exit` 单点查）——一个 scope 的处置不该逐 scope 重放整 run 的 events。
        if event_log.has_exit(scope_id):
            return "noop-exit-in-flight", None  # 退出记录已在、投影在途 → 让既有链收敛，不动手
        return None, js.claimed_at

    noop, claimed_at = _check()
    if noop:
        return noop
    job = next((j for j in meta.jobs if j.scope_id == scope_id), None)
    cutoff = _job_cutoff(meta, job, claimed_at)
    if cutoff is not None:
        # 发出停止之前必须有一次读到已过截止时刻（墙钟严格晚于截止时刻）：每次醒来都重读墙钟，等待期间时钟被回拨或恰好读到截止
        # 时刻时还没到，就在这次调用的等待额度内接着等。额度在第一次临睡前定下（固定上界与本次调用还能等的秒数取小），之后各次等待
        # 的总和不超过它；累计按请求等待的秒数，不按墙钟之差，墙钟正是可能被调整的那个量。
        now = now_fn()
        cap: float | None = None
        waited = 0.0
        while not now > cutoff.at:
            remaining = (cutoff.at - now).total_seconds()
            tie = remaining <= 0  # 恰好读到截止时刻（只用来选日志里的说法）
            wait = max(remaining, _TIMEOUT_TIE_WAIT_S)  # 每次至少等固定量，见常量注释
            if cap is None:
                budget = wait_budget_fn() if wait_budget_fn is not None else None  # 临睡前采样：此前的读取已花掉的时间不再算进额度
                cap = _TIMEOUT_EARLY_WAIT_MAX_S if budget is None else min(_TIMEOUT_EARLY_WAIT_MAX_S, budget)
            if waited + wait > cap:
                if waited > 0:
                    cause = "读到的恰好是截止时刻" if tie else "等待期间系统时钟被回拨"
                    why = f"已等过 {waited:.0f} 秒仍未到（{cause}），本次调用的等待额度只剩 {max(cap - waited, 0):.0f} 秒"
                elif remaining > _TIMEOUT_EARLY_WAIT_MAX_S:
                    why = "早于定时服务承诺的触发精度"
                else:
                    why = f"本次调用剩余的时间只够等 {max(cap, 0):.0f} 秒"
                by = _CUTOFF_BY_TEXT[cutoff.by]
                where = f"读到的时刻恰好是截止时刻（{by}）" if tie else f"离截止时刻（{by}）还有 {remaining:.0f} 秒"
                print(f"timeout-skip: run={run_id} scope={scope_id} {where}，{why} → 本次不停止，过了截止时刻后由之后的推进检查收尾")
                return "skip-early"
            if tie:
                print(f"timeout-wait: run={run_id} scope={scope_id} 读到的时刻恰好是截止时刻、还没有过 → 再等 {wait:g} 秒")
            elif waited > 0:
                print(f"timeout-wait: run={run_id} scope={scope_id} 等待之后读到的时刻仍早于截止时刻 {remaining:.1f} 秒"
                      "（等待期间系统时钟被回拨）→ 接着等")
            else:
                print(f"timeout-wait: run={run_id} scope={scope_id} 定时触发早于截止时刻 {remaining:.1f} 秒 → 等到那时再处置")
            sleep_fn(wait)
            waited += wait
            noop, _ = _check()  # 等待期间 job 自行结束或退出记录已到 → 照常 no-op
            if noop:
                return noop
            now = now_fn()
    ecs = ecs_client if ecs_client is not None else boto3.client(
        "ecs", region_name=os.environ.get("REGION") or os.environ.get("AWS_REGION"))
    cluster = os.environ["CLUSTER"]
    arns: list[str] = []
    seen: set[str] = set()
    for desired in ("RUNNING", "STOPPED"):  # 正在停止/刚停止的不在 RUNNING 列表里——必须两个都列，否则误判「无踪」
        # ListTasks 单页最多 100 条，必须翻页：大 run 的 STOPPED task（ECS 保留约 1h）会超过一页，只取首页
        # 会把仍在运行的目标判成「无踪」、直写 timed_out，把正常运行完的 job 误判成超时。
        token = None
        while True:
            kwargs = {"cluster": cluster, "startedBy": run_id, "desiredStatus": desired}
            if token:
                kwargs["nextToken"] = token
            resp = ecs.list_tasks(**kwargs)
            for arn in resp.get("taskArns", []):
                if arn not in seen:  # 两个 desiredStatus 各翻一遍，中途转态的 task 会两边都出现
                    seen.add(arn)
                    arns.append(arn)
            token = resp.get("nextToken")
            if not token:
                break
    target = None
    # DescribeTasks 的 tasks 硬上限 100 个 ARN，分批传；**找到即停**——RUNNING 的 ARN 排在前面，命中即无须再问
    for i in range(0, len(arns), _DESCRIBE_TASKS_MAX):
        for t in ecs.describe_tasks(cluster=cluster, tasks=arns[i:i + _DESCRIBE_TASKS_MAX]).get("tasks", []):
            if _task_scope_id(t) == scope_id:
                target = t
                break
        if target is not None:
            break
    if target is not None:
        arn = target["taskArn"]
        if target.get("lastStatus") == "STOPPED":
            # 已停但观察者没写（STOPPED 事件丢投）：从 task 对象落真退出记录——与观察者同一算法、同键幂等
            exit_code, timed_out, reason, exited_at = exit_from_task(target)
            event_log.record_exit(scope_id, exit_code, timed_out=timed_out, reason=reason, exited_at=exited_at)
            print(f"timeout-converge: run={run_id} scope={scope_id} task={arn} 已 STOPPED 无退出记录 → 按 DescribeTasks 落 exit={exit_code}")
            return "converged-from-describe"
        if target.get("desiredStatus") == "STOPPED":
            # 不抢着写：退出记录由 exit_observer 收到 STOPPED 事件时落（本函数 docstring「正在停止」那路）
            print(f"timeout-noop: run={run_id} scope={scope_id} task={arn} 正在停止 → 等它的退出事件到达再收尾")
            return "noop-stopping"
        ecs.stop_task(cluster=cluster, task=arn, reason=_stop_reason(job, cutoff))
        why = _CUTOFF_BY_TEXT[cutoff.by] if cutoff is not None else "截止时刻无从复查，按已到处理"
        print(f"timeout-stop: run={run_id} scope={scope_id} task={arn}（{why}）")
        return "stopped"
    if not event_log.record_timed_out_if_absent(scope_id):
        # 列 task 期间观察者写下了真实的退出记录：让既有链收敛，不盖掉它
        print(f"timeout-noop: run={run_id} scope={scope_id} 找不到这个 task，但它的退出记录刚刚写下 → 按那条记录收尾")
        return "noop-exit-in-flight"
    print(f"timeout-converge: run={run_id} scope={scope_id} 找不到这个 task、也没有它的退出记录 → 直接按超时结案")
    return "converged-directly"


def _scan_overdue_timeouts(run_id: str, built) -> None:
    """防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING 且当前时刻已过
    截止时刻加余量的 job 走同一超时处置——CreateSchedule 失败/schedule 丢失时，后续任何事件触发的 tick 都能补救。截止时刻由运行态里的
    认领时刻、预算与期限重算（`_job_cutoff`，与定时触发同一个算法、以期限封顶）；认领时刻缺失或读不出的 job 不碰（无起算点不臆断）。
    纯静默 job（无事件→无 tick）的主保障仍是 Scheduler 到点 invoke。"""
    from gherkai_core.model import Status
    from gherkai_runtime import compose

    meta, event_log, run_store, *_ = built
    state = run_store.load_run_state(run_id)
    if state is None:
        return
    job_by_scope = {j.scope_id: j for j in meta.jobs}
    now = compose.now()
    for sid, js in state.jobs.items():
        if js.status != Status.RUNNING:
            continue
        cutoff = _job_cutoff(meta, job_by_scope.get(sid), js.claimed_at)
        if cutoff is None:
            continue
        overdue = (now - cutoff.at).total_seconds()
        if overdue > _DEFENSIVE_TIMEOUT_MARGIN_S:
            print(f"defensive-timeout: run={run_id} scope={sid} 已过截止时刻（{_CUTOFF_BY_TEXT[cutoff.by]}）{overdue:.0f} 秒，"
                  f"超过余量 {_DEFENSIVE_TIMEOUT_MARGIN_S:.0f} 秒")
            _handle_timeout(run_id, sid, built)


def _load_definition(run_store, run_id: str):
    """读 definition（云端读端）：结构版本不是本后端认的、或定义形态违约（含云端 definition 缺 worker_task_defs），
    **不推进该 run、记一条诊断，以结束写的 error 变体结束它**（ADR 0037 决策 7，ADR 0031 决定三「结束写」小节）：每个未结束的 job
    （含执行中的）记 error，run 随之为 error，原因同时写进运行态的 run 级说明与这些 job 的说明。重放投影没有退出码可交给使用方，只
    「不推进」会让 run 一直停在未结束（ADR 0034 对无法收敛的 run 一律反对）；error 是能被 `status` 看见的终态，说明让 `status` 看得见
    原因（团队成员未必有 CloudWatch 的读权限）。说明是产品语言的整句、长度有界，几种原因的句子在 `run_status`（本机没有这种情形）；
    契约异常的原文只进 CloudWatch 的诊断行、不进运行态——它带内部字段名与形状描述，是给 contributor 的。这一写不存明细、不生成报告：
    报告按运行定义逐个列出 job，读不到运行定义就组装不出。不为旧 definition 留兼容路径：worker_task_defs 缺失不再按后端默认指针回落
    （那会让一个 run 内的镜像不再固定，ADR 0038 不变量）。

    返回 RunMeta；definition 不存在或读不到可用的运行定义时返回 None。结束写写成才记诊断行；没写成只会是 run 已被别处结束、运行态不存在
    （都不记），或它重读到的运行态公共部分读不出（只记一行说明读不出的日志）。结束写本身的失败（写入竞争的重读次数用尽、DynamoDB 调用
    失败）原样抛出、本次调用失败，与装配期其它 AWS 调用失败同一处理。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable
    from gherkai_core.errors import DefinitionContractError, UnsupportedDefinitionSchema
    from gherkai_core.run_status import DEFINITION_CONTRACT_REASON, NO_WORKER_IMAGES_REASON, schema_mismatch_reason
    from gherkai_runtime import compose

    def _end_as_error(reason: str) -> bool:
        # 结束写的 error 变体在 DDB adapter 上（`DynamoDBRunStore.end_run_as_error`，不在 RunStore 端口上）。它重读到的运行态公共部分
        # 读不出时不写，这里按读不出的记录处理：只记一行日志、不推进，不算这条记录的失败（ADR 0054 决策九「落实时，后端各入口先过
        # 同一道闸」第一步）
        try:
            return run_store.end_run_as_error(run_id, reason, ended_at=compose.now_iso())
        except RunStateUnreadable:
            print(f"skip: run {run_id} 的运行状态记录读不出，不推进，也没有把它标为 error")
            return False

    def _mark(reason: str, detail: str | None = None):
        # 诊断行在写成之后才记：没有写成（run 已被别处结束、运行态不在，或公共部分读不出）时「标为 error」不属实。结束写本身抛错时
        # （写入竞争的重读次数用尽、DynamoDB 调用失败）先记下原因与诊断再抛出：这次写可能一直写不成，日志里不能只剩回溯
        diagnosis = f"——{reason}" + (f"；诊断：{detail}" if detail else "")
        try:
            ended = _end_as_error(reason)
        except Exception:
            print(f"reject: run {run_id} 不推进{diagnosis}；把它标为 error 的写没有写成")
            raise
        if ended:
            print(f"reject: run {run_id} 不推进、标为 error{diagnosis}")
        return None

    try:
        meta = run_store.load_run_meta(run_id)
    except UnsupportedDefinitionSchema as exc:
        return _mark(schema_mismatch_reason(exc.found, exc.supported, exc.cli_version))
    except DefinitionContractError as exc:
        return _mark(DEFINITION_CONTRACT_REASON, str(exc))
    if meta is None:
        # 提交记录不在。运行态在而提交记录不在只会是记录被删去（建 run 先写提交记录、后写运行态，见 DynamoDBRunStore.create_run）：
        # 与形态违约同样以结束写的 error 变体结束。运行态也不在（不属于这张表的 run、已被清理的 run）时这次写不成立，什么都不做。
        if _end_as_error(DEFINITION_CONTRACT_REASON):
            print(f"reject: run {run_id} 不推进、标为 error——{DEFINITION_CONTRACT_REASON}；诊断：提交记录不存在")
        return None
    if not meta.worker_task_defs:
        return _mark(NO_WORKER_IMAGES_REASON)
    return meta


def _build(run_id: str):
    """cloud 组合根：读 env 造 boto3 + 装配（RunStore/EventLog/CloudLauncher + ResultStore/ReportStore）注入。

    返回 (meta, event_log, run_store, launcher, max_concurrency, result_store, report_store)，供 tick 与生成报告使用；本机后台推进进程的
    对应装配是 `detached.assemble_local_run`（它用自己生成的运行定义，不从记录读回）。meta 从 RunStore 读回（definition）。
    **None 表示本 run 云端推进器不该动**（非 detached / 已收尾 / definition 不在库，三支见下）——两个 handler
    据此整体 no-op。

    **store 与 FargateEngine 装配都复用 compose（`build_cloud_stores` / `build_fargate_engines`，单一真源、
    不重造）**——三层 store 的 prefix 规范化与 offloader 挂载与 submit 侧同一份；job-in 前缀 / artifact 落点 / container 名 /
    SDK env 只在 `build_fargate_engines` 一处定义（ADR 0016：compose 是组合根逻辑、WebUI/Lambda 都复用、
    不经 cli——组合根共享层即产品本体包）。Lambda 打包带上 gherkai_runtime（不背 argparse/render）。

    **worker task-def revision 只有一条来源**（ADR 0038）：definition 的 `meta.worker_task_defs`（提交侧 preflight 已把 variant
    解析成各引擎的显式 revision）。缺该字段的云端 definition 是定义违约，由 `_load_definition` 以结束写的 error 变体结束 run、
    不推进——不按后端默认指针回落（那会让运行中的 run 中途换 step 集）、不回落 family 最新 ACTIVE、不回落模板 revision（ADR 0037
    决策 7 不留兼容分支）。
    """
    import boto3
    from gherkai_core.adapters.event_log import DdbEventLog
    from gherkai_core.adapters.cloud_launcher import CloudLauncher
    from gherkai_core.model import TERMINAL_STATUSES
    from gherkai_runtime import compose, names

    region = os.environ.get("REGION") or os.environ.get("AWS_REGION")
    ddb = boto3.resource("dynamodb", region_name=region)
    s3 = boto3.client("s3", region_name=region)

    runs_table_name = os.environ["RUNS_TABLE"]
    runs_table = ddb.Table(runs_table_name)
    events_table = ddb.Table(os.environ["EVENTS_TABLE"])
    bucket = os.environ["ARTIFACTS_BUCKET"]
    report_dir = os.environ.get("REPORT_DIR", "reports")
    prefix = os.environ.get("PREFIX", names.DEFAULT_PREFIX)

    # 三层 store 走 compose.build_cloud_stores（与 submit 侧同一真源、不重造：prefix 规范化、三个 S3 件套共享
    # 一个 client、**arg_offloader 默认挂载**都由它保证），句柄注入以复用本函数已建的 ddb resource / s3 client。
    # offloader 尤其不能漏（ADR 0030 决定七「生产默认挂载、不给生产选要不要正确」）：submit 侧把 docString/
    # dataTable 正文 offload 到 S3、META 只留指针，漏挂则 load_run_meta 对含指针的 META 直接 fail-loud 抛，
    # 云端推进器整条链停在装配上。prefix 用 REPORT_DIR 与 submit 侧同源（restore 按绝对 URI 取回、实际不依赖
    # prefix，但写读两侧同构造零漂移）；**不含 run_id**——S3*Store 内部自拼 `{prefix}{run_id}/…`。
    # region 不传：它在 build_cloud_stores 里只喂建句柄的那两个钩子，而此处两个句柄都已注入、钩子不会执行。
    # detached 不传（默认 False）：本 Lambda 只读已存在的 run，不 create_run、不写 detached 标记。
    # 判定存储是裸的 S3ResultStore，不套本机推进器的保存重试：保存失败让本次调用失败，由流的重试或之后的触发再做。
    run_store, result_store, report_store = compose.build_cloud_stores(
        table=runs_table_name, bucket=bucket, prefix=report_dir,
        ddb_table=runs_table, s3=s3)
    # `is_detached` 是 DDB adapter 上的方法、不在 RunStore 端口面上——云端后端这个 store 恒是 DDB 实现。
    if not run_store.is_detached(run_id):
        # 只推进 detached run：同步 `run --backend cloud` 由进程内 schedule 推进，
        # 推进器碰它就是双开推进器（认领、RunTask、终态写）。kicker 那扇门由 Stream filter 挡，events 表
        # Stream 这扇门滤不了（events item 无 detached 标记）——同一判据在此判，返回 None 表示全 handler no-op。
        # 判在 load_run_meta **之前**：同步 run 的每条 worker 事件都会触发本 Lambda，先判省掉强一致 META
        # 读 + offload 正文的 S3 取回，且推进器在断定「不该碰」前不读对方 definition（STATE 缺失同落此支）。
        print(f"skip: run {run_id} 不是 submit 提交到后台执行的 run（同步的 `run --backend cloud` 由发起它的命令自己推进）")
        return None
    # **已收尾的 run 不再推演**：已收尾的 run 若被重放推演，会拿「此刻还剩下的事件」重算一遍并覆盖写（写序无条件执行）
    # ——events 表开 TTL，7 天后 worker 事件已被删、只剩永不过期的退出记录，重算结果是「每个 job 都 error、零 scenario」，
    # 把权威的判定真值静默销毁。触发面不只 TTL 的 REMOVE（那道已在 `_run_ids_from_stream` 与 IaC filter 挡）：迟到重投、
    # 手工重放同一批 Stream 记录、
    # 超时到点触发器的 payload 都落到这里——后者读到终态时不做超时处置（与 ADR 0034「job timeout」节
    # 「到点时 job 已终态 → tick no-op」一致）。
    # **明确接受的代价**：从此没有「重 tick 一个已收尾的 run 来补写丢失的报告」这条路——报告只由使 run 成为终态的
    # 那一方生成（本 Lambda 与 detached 宿主两个调用点），本就没有独立的重生成命令，而事件过期后重 tick 只会推演出错的结果。
    # 判在 `load_run_meta` 之前同上一支的理由：省掉强一致 META 读 + offload 正文的 S3 取回。tick 自身也先读运行态、
    # 已收尾即停止推演，覆盖本闸之后才插入的收尾；本闸保留，是因为它在读 definition 之前，tick 内的判停管不到这一段
    # （ADR 0034 机制三「run 级状态只进不退」条④）。
    state = run_store.load_run_state(run_id)
    if state is not None and state.status in TERMINAL_STATUSES:
        print(f"skip: run {run_id} 已结束，不再改写它的结果")
        return None
    # 结构版本不合与定义违约时以结束写的 error 变体结束 run、不推进（ADR 0037 决策 7，ADR 0031 决定三「结束写」小节）
    meta = _load_definition(run_store, run_id)
    if meta is None:
        return None
    scope_ids = [j.scope_id for j in meta.jobs]
    event_log = DdbEventLog(events_table, run_id, scope_ids)

    # CloudLauncher 用 compose.build_fargate_engines 产的 resolver（单一真源、零漂移）。
    network = {
        "subnets": os.environ["SUBNETS"].split(","),
        "securityGroups": os.environ["SECURITY_GROUPS"].split(","),
        "assignPublicIp": os.environ.get("ASSIGN_PUBLIC_IP", "ENABLED"),
    }
    worker_task_defs = dict(meta.worker_task_defs)  # definition 里的显式 revision（ADR 0038 不变量）；缺值时 _load_definition 已结束这个 run
    engines = compose.build_fargate_engines(
        run_id=run_id, cluster=os.environ["CLUSTER"],
        events_table=os.environ["EVENTS_TABLE"], bucket=bucket, report_dir=report_dir,
        network_config=network, worker_task_defs=worker_task_defs, region=region,
        # 额外请求头从 definition 读回（ADR 0035：submit 落 META、此处重建 engine 时注入 RunTask env）
        extra_http_headers=dict(meta.extra_http_headers) if meta.extra_http_headers else None,
        # 会话预热地址同理从 definition 读回（ADR 0051 决策 13）：丢了它，worker 就会按 definition 完整性判 precheck_failed
        session_warmup_url=meta.session_warmup_url,
        ecs=boto3.client("ecs", region_name=region), s3=s3,
    )
    # job timeout 到点触发器（ADR 0034「job timeout」节）：env 齐才装配（KICKER_ARN/SCHEDULER_ROLE_ARN 由
    # IaC 注入）；缺 → None，CloudLauncher 每次 launch 打降级日志（tick 防御扫仍兜）。
    timeout_watch = None
    kicker_arn = os.environ.get("KICKER_ARN")
    scheduler_role_arn = os.environ.get("SCHEDULER_ROLE_ARN")
    if kicker_arn and scheduler_role_arn:
        timeout_watch = EventBridgeTimeoutWatch(
            boto3.client("scheduler", region_name=region),
            kicker_arn=kicker_arn, role_arn=scheduler_role_arn, prefix=prefix)
    launcher = CloudLauncher(compose.make_resolver(engines), run_id=run_id, timeout_watch=timeout_watch)
    # 并发上限（ADR 0034 机制四）取 min(definition 声明, 部署侧 cap)。cap 是本 Lambda 的 MAX_CONCURRENCY env
    # （IaC 设）：语义是**部署侧 per-run 上限**、非真源——task 在部署方 cluster 上运行、计入部署方账单，故部署方保留
    # 总量控制权，提交侧声明再高也钳到 cap。meta 无值（打通前落的旧 definition）按 1，与打通前行为一致；
    # `or` 顺带把 0 也当无值——0 会让 plan_next 永不提议起 job（run 卡死），按 1 运行是保守可收敛的兜底。
    # env 漏注（IaC 改坏/手工建的 Lambda）时保守回 **1**：cap 的数值真源在 IaC 一处，code 不复制部署值
    # （复制就是两处各一份、IaC 调了 cap 而这里没跟就成隐形漂移）。缺省宁可慢（串行仍收敛），不替部署方放宽闸。
    cap = int(os.environ.get("MAX_CONCURRENCY", "1"))
    max_concurrency = min(meta.max_concurrency or 1, cap)
    return meta, event_log, run_store, launcher, max_concurrency, result_store, report_store


def _run_ids_from_runs_stream(event) -> set[str]:
    """提取 kicker 要 tick 的 run_id 集。两种 event 源（kicker 同时服务两者）：

    ① runs 表 Stream（冷启动主路径）：`Records[].dynamodb.Keys.run_id`（runs 表 PK=run_id，非复合、直接取）。
    ② 直接 invoke 的 kickoff（cloud `status --wait` 接力兜底）：payload `{"run_id": "..."}`——
       Stream 丢投卡 pending 时 status --wait 绕过 Stream 直接 invoke kicker，故须认此格式（否则空转、救不了）。
       job timeout 的 Scheduler 到点 invoke（payload 另带 `timeout_scope`，kicker_handler 先行处置）也走
       此形状——到点 invoke 本身即一次强制 tick（顺带兜事件丢投，ADR 0034「job timeout」节）。
    """
    run_ids: set[str] = set()
    for rec in event.get("Records", []):  # ① Stream
        rid = rec.get("dynamodb", {}).get("Keys", {}).get("run_id", {}).get("S")
        if rid:
            run_ids.add(rid)
    rid = event.get("run_id")  # ② 直接 invoke kickoff
    if rid:
        run_ids.add(rid)
    return run_ids


def _tick_runs(run_ids: set[str], label: str, *, prebuilt: dict | None = None) -> dict:
    """对每个 run tick 一步，按结果分支。reconciler（events Stream）与 kicker（runs Stream）共用。

    tick 的三种结果（`TickOutcome`，ADR 0034 机制三「run 级状态只进不退」条④）：这一方的写使 run 成为终态 → 从记录生成
    RunReport；run 已结束而使它成为终态的不是这一方 → 不写报告、不做超时扫；继续推进 → 防御性超时扫。

    prebuilt：本次 invoke 已装配好的组合根（run_id → `_build` 结果，**含 None**，表示该 run 不由云端推进器管），
    有则复用、不重装——超时路径先 `_build` 做处置再落到此处 tick 同一个 run，重装一次是纯重复工作
    （每次 `_build` 造 4 个 boto3 client + 强一致读 META + 可能的 S3 offload 正文还原）。
    """
    from gherkai_core.reconcile import TickOutcome, tick, write_report_from_record
    from gherkai_runtime import compose  # 时钟走 compose.now 单一读取点（同 local/前台两宿主，格式不漂移）

    prebuilt = prebuilt or {}
    for run_id in run_ids:
        # definition 本身的问题（结构版本不合、定义违约、缺 worker_task_defs）由 _load_definition 以结束写的 error 变体结束
        # 那个 run、返回 None，不在这里抛、不影响同批其它 run；装配期的 AWS 调用失败（含那次结束写本身的失败）照常抛出、本次
        # invocation 失败、events Stream 重试本批。
        built = prebuilt[run_id] if run_id in prebuilt else _build(run_id)
        if built is None:
            continue
        meta, event_log, run_store, launcher, mc, rstore, pstore = built
        # 判定明细由 tick 在写下这一轮各 job 的终态之前存进 rstore，每份带一个新标识，终态写点名它（ADR 0030 决定三「点名」条、
        # 「后台推进同守」条）；rstore 不在进程内重试，存明细或写运行态的异常原样抛出 → 本次 invocation 失败 → events Stream 事件源
        # 重试本批，重做的那一次另存一份、点名新的标识（终态写之后再失败就没人重试了）。
        outcome = tick(run_id, meta, event_log, run_store, launcher, mc, clock=compose.now, result_store=rstore)
        if outcome is TickOutcome.ENDED:
            # 装配时的语义闸之后 run 已被别处结束（tick 读运行态之前，或这一方的终态写、结束写之前）：与那道闸同一处置，报告不改写
            print(f"{label}: run {run_id} 已结束，不再改写它的结果")
        elif outcome is TickOutcome.COMMITTED:
            # 报告从记录生成，入口是 core 唯一的一份，本机后台推进进程调的是同一个。生成在终态写之后执行、失败无人重试，抛出去还会让
            # 本次 invocation 失败、events Stream 本批重试耗尽后整批丢弃，同批其它 run 的事件随之丢失（同下面超时兜底检查的隔离
            # 理由）；所以读运行态（强一致读，会因限流或瞬时 5xx 抛）、按点名的标识读回明细、组装与写报告整段在入口的失败隔离之内
            # （ADR 0034「端到端流程」cloud 第 ④ 步）。明细每份一次 GetObject，不列举前缀。
            write_report_from_record(meta, run_store, rstore, pstore, created_at=compose.now_iso())
            print(f"{label}: run {run_id} done + committed")
        else:
            print(f"{label}: run {run_id} advanced (not done)")
            # 防御性超时扫（claimed_at ②）是 Scheduler 到点触发器的双保险、best-effort：它失败不该拖累已经
            # 推进成功的这一步——抛出去会让本次 invocation 失败、events Stream 本批重试耗尽后整批丢弃，
            # 同批其它 run 的事件一并永久丢失（同上面生成报告的隔离理由）。
            try:
                _scan_overdue_timeouts(run_id, built)
            except Exception as exc:
                print(f"{label}: run {run_id} 超时兜底检查未完成，稍后重试：{exc}")
    return {"ok": True, "runs": list(run_ids)}


def handler(event, context):
    """events 表 Stream 入口（reconciler 主推进）：worker PutItem / task_exited 触发 → 对涉及 run tick 续推。"""
    return _tick_runs(_run_ids_from_stream(event), "reconciler")


def kicker_handler(event, context):
    """kicker（踢启器）入口——两个触发源：runs 表 Stream 的 **INSERT**（冷启动：submit create_run 写 definition
    即触发 → tick 起首批）+ status --wait 的直接 invoke kickoff（卡住救活：payload `{"run_id":...}`）。

    与 reconciler 共用 tick（起首批就是 tick 的 CAS start 分支）——四宿主一份 tick（submit-local / kicker /
    reconciler / status 接力）。kicker **只被 runs Stream 的 INSERT 触发**（filter 在 IaC 配），故 reconciler
    之后写 runs 表（MODIFY）不触发它——无自触发放大。
    与 reconciler 的分工：kicker 负责「让 run 动起来」（冷启动第一脚 + 卡住时补 kickoff），reconciler 负责
    「推着走」（events Stream 持续推进）。

    到点触发（ADR 0034「job timeout」节）：EventBridge Scheduler 的到点 invoke，payload
    `{"run_id","timeout_scope"}`——先超时处置（仍 running 且 deadline 已到才 StopTask/收敛，触发早于 deadline 时先等到
    deadline），再照常 tick（处置用的组合根经 prebuilt 交给 tick 复用，同一 run 只装配一次）。等待上界在临睡前按本次
    调用的剩余时间算（复查的读取之后），见 `_timeout_wait_budget_s`。
    """
    timeout_scope = event.get("timeout_scope")
    rid = event.get("run_id")
    prebuilt: dict = {}
    if timeout_scope and rid:
        built = _build(rid)
        prebuilt[rid] = built  # 含 None（本 run 不该推进）——tick 侧据此也不重装
        if built is not None:
            _handle_timeout(rid, timeout_scope, built, wait_budget_fn=lambda: _timeout_wait_budget_s(context))
    return _tick_runs(_run_ids_from_runs_stream(event), "kicker", prebuilt=prebuilt)


def _timeout_wait_budget_s(context) -> float | None:
    """本次 invoke 还能拿多少秒等到 deadline：Lambda 剩余时间减去等完之后处置与 tick 所需的 `_TIMEOUT_HANDLING_RESERVE_S`。
    context 不带剩余时间（测试或直接调用）时返回 None，只受固定等待上界约束。"""
    remaining_ms = getattr(context, "get_remaining_time_in_millis", None)
    if remaining_ms is None:
        return None
    return remaining_ms() / 1000.0 - _TIMEOUT_HANDLING_RESERVE_S
