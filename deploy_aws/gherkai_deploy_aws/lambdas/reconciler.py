"""reconciler 与 kicker 两个推进 Lambda（ADR 0034）：后端各入口先过同一道闸，再推进一步，run 结束之后清扫它的 task。

两个入口：
- `handler`（reconciler）：events 表开 Stream（NEW_IMAGE），worker PutItem 执行事件 / 退出观察者写 task_exited → Stream 触发。它从一批
  记录里取涉及的 run（按 run 去重），对每个 run 过闸（`_gate`）、推进一步（`_advance`，调 gherkai_core.reconcile.tick：读运行态与
  全量重放、投影写，为这一轮已有结果的 job 各存一份带新标识的明细、写终态并点名它，再由 plan_next 决定认领并起下一个 job 或做到期的
  结束写）。
- `kicker_handler`（kicker）：runs 表 Stream 上 STATE 条目的新建（冷启动起首批）与使 run 成为终态的那次写（清扫），以及 job 到点停止的
  一次性定时触发。只认这几种载荷，其余记一行日志、正常返回。

**闸**（ADR 0054 决策九「落实时，后端各入口先过同一道闸」）：各入口先强一致读运行态、只看公共部分，不存在或已结束即清扫，读不出只记
日志；未结束再读提交记录的头，别的格式写出或运行定义不可用即以结束写的 error 变体结束并清扫；其余装配之后推进。**清扫**
（`_sweep`，同一决策第 2 条）：按 run 标识列出期望状态为运行中的 task、逐个停掉，不写 runs 表。**失败与批的隔离**（`_each_run`）：
一批里每个 run 各自处理，一个的失败不打断别的，全部处理完之后有失败即让这次调用失败、由流或 AWS 的重试再调用。tick 幂等 + CAS/HWM
条件写兜底——Stream 按分片并发触发多个 handler 实例、叠加定时触发，全部安全（真 DDB 已验）。

**本地替身照不出、要在部署之后核的真实行为**：读运行态与读头的强一致（替身不模拟最终一致，测试只在调用参数上守）；流映射在调用
失败或超时时把整批重投、重试用尽即丢弃，同一个 run 的记录落在同一分片、按序投递（`_each_run` 靠抛出换来的重试建立在这上面，
ADR 0033 资源清单 13.）；两条过滤在真实的流上放过哪些写（ADR 0054 实测项 21）；按期望状态列 task 时刚启动与刚停止的 task 列不列得出、
StopTask 对正在停止与已停止的 task 的返回（同一篇实测项 27）；执行角色没有桶的列举权限时，取不存在的 jobs 对象得到的是拒绝访问而不是
「键不存在」（ADR 0033 资源清单 10.）；定时触发的调用失败之后由谁重试、重试几次（ADR 0054 实测项 26）。

**cloud 组合根（Lambda 装配）**：每次调用读 env 造 boto3 client + 三 store adapter（`_backend`），过闸之后再为要推进的 run 装配
FargateEngine + CloudLauncher（`_assemble`）注入纯 reconcile.tick——**是组合根注入、非 ports 内部 env-sniff 全局单例**（[0016] 禁的
GlobalConfigManager 反模式，此处每次 handler 显式构造、无隐式全局态）。core 一行不为 cloud 改（同 local，只换注入的
EventLog/Launcher/RunStore）。

打包：本文件是 **asset 原料**（住在 provider 包 `gherkai_deploy_aws/lambdas/`，摊到 zip 根，ADR 0037 决策 6）。
env：**IaC 注入**（`gherkai_deploy_aws/stack.py` 的 reconciler/kicker Function）的有：
RUNS_TABLE / EVENTS_TABLE / ARTIFACTS_BUCKET / CLUSTER / PREFIX / REGION / SUBNETS / SECURITY_GROUPS /
MAX_CONCURRENCY（**部署侧 per-run 并发 cap**、非真源——真源是 definition 的 `RunMeta.max_concurrency`，取
min，ADR 0034 机制四；数值真源在 IaC 一处，本文件缺省只在 env 漏注时保守回 1、不复制部署值）/ KICKER_ARN / SCHEDULER_ROLE_ARN（job timeout 到点触发器用，ADR 0034「job timeout」节）；**本文件缺省供给、IaC 不注入** 的是 REPORT_DIR（reports）/ ASSIGN_PUBLIC_IP（ENABLED，与公有子网
配套）——要改产物落点前缀或走私有子网时才在 IaC 显式给。

**worker 镜像用哪个 task-def revision 不经 env**（ADR 0038 不变量「运行时只用 definition 里的显式 revision」）：
只读 definition 的 `RunMeta.worker_task_defs`；缺该字段的云端 definition 是定义违约，闸以结束写的 error 变体结束
这个 run、不推进（ADR 0037 决策 7，ADR 0031 决定三「结束写」小节「运行定义不可用时」条）。
**推进器绝不用模板 revision**——其镜像栏是 `latest` 占位，全新 prefix 上从未推过该 tag，拉镜像会拖到
Fargate 启动期才失败（ADR 0038 被拒方案）。故本文件不读任何模板 ARN 类 env。
"""
from __future__ import annotations

import datetime as _dt
import os
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


def _run_ids_from_stream(event) -> set[str]:
    """从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch 可能多条同 run。

    **REMOVE 记录跳过**：events 表开 TTL（`expires_at`，两引擎的 event sink 写 emit+7d），TTL 过期删除同样进
    Stream、同样带 Keys。它不携带任何新信息，本道跳过它、不为它推进一次；推进方本次读到终态即返回（`_gate` 与 tick 的判停）。
    用 `.get` 只排除 REMOVE、**不做 INSERT 白名单**：events 表虽只 PutItem，同键重写（超时处置补写的退出记录
    被迟到的观察者以真退出码/归因重写）在 Stream 上是 MODIFY。
    IaC 侧的事件源 filter 同样滤掉 REMOVE（见 `stack.py` events 表的 `DynamoEventSource`）——那道要重新部署
    才生效，本道不依赖部署。已结束的 run 再被带到（迟到重投/手工重放）由 `_gate` 只清扫、不推演。
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

    触发建在专用 schedule group 里（`group_name`，由组合根按 `names.schedule_group_name` 从部署前缀推出），名字不带 prefix：
    `names.job_timeout_schedule_name(run_id, scope_id)`，确定性（重复 arm 幂等，ConflictException 视作已武装）、合法字符集
    （scope_id 可含中文/路径，不能直接入名）、长度固定。group 名与名字都走命名真源 `gherkai_runtime.names`，IaC 的 IAM 资源域
    `schedule/<group 名>/*` 同源推导（ADR 0033 资源清单 15.，两侧硬契约）。RetryPolicy 不传、取 Scheduler 的缺省（至少投递一次，
    处置幂等）。best-effort：调用方（CloudLauncher）兜异常。
    """

    def __init__(self, scheduler_client, *, kicker_arn: str, role_arn: str, group_name: str) -> None:
        self._client = scheduler_client
        self._kicker_arn = kicker_arn
        self._role_arn = role_arn
        self._group_name = group_name

    def arm(self, run_id: str, scope_id: str, at: _dt.datetime) -> None:
        import json

        from gherkai_runtime import names

        # 到点时刻就是截止时刻本身（tick 认领时算好，与到点复查、防御扫同一算法），arm 晚于认领的间隔不推后到点。
        at_utc = at.astimezone(_dt.timezone.utc)
        try:
            self._client.create_schedule(
                Name=names.job_timeout_schedule_name(run_id, scope_id),
                GroupName=self._group_name,
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
    剩余超过额度时不等待、不处置，打一行诊断、返回 skip-early，保护交给防御扫与之后的推进（宁可不处置也不提前处置）。
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


def _scan_overdue_timeouts(run_id: str, built, *, ecs_client=None) -> None:
    """防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING 且当前时刻已过
    截止时刻加余量的 job 走同一超时处置——CreateSchedule 失败/schedule 丢失时，后续任何事件触发的 tick 都能补救。截止时刻由运行态里的
    认领时刻、预算与期限重算（`_job_cutoff`，与定时触发同一个算法、以期限封顶）；认领时刻缺失或读不出的 job 不碰（无起算点不臆断）。
    纯静默 job（无事件→无 tick）的主保障仍是 Scheduler 到点 invoke。ecs_client 原样交给超时处置（None 时它自己建一个）。"""
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
            _handle_timeout(run_id, sid, built, ecs_client=ecs_client)


# ============================================================================
# 本次调用的组合根：各 run 共用的句柄与三层 store（`_Backend`），过闸之后为要推进的 run 另装配起 task 用的部分（`_assemble`）
# ============================================================================

@dataclass(frozen=True)
class _Backend:
    """一次 Lambda 调用里各 run 共用的组合根部分：读 env 造的 boto3 句柄、三层 store 与部署注入的配置（`_backend` 构造）。

    闸与清扫只用它（ADR 0054 决策九「落实时，后端各入口先过同一道闸」第一、二步）；要推进的入口过闸之后再经 `_assemble` 装配起 task
    用的部分（第三步）。ECS client 只有这一个：清扫、job 到点停止与起 task 共用。"""

    region: str | None
    s3: object
    ecs: object
    events_table: object
    events_table_name: str
    run_store: object  # DynamoDBRunStore：闸要用它在 RunStore 端口之外的几种读与结束写的 error 变体
    result_store: object
    report_store: object
    bucket: str
    report_dir: str
    prefix: str
    cluster: str


def _backend() -> _Backend:
    """cloud 组合根的公共部分：读 env 造 boto3 句柄与三层 store。

    **三层 store 走 compose.build_cloud_stores**（与 submit 侧同一真源、不重造：报告前缀规范化、三个 S3 件套共享一个 client、jobs 对象
    存取的装配都由它保证），句柄注入以复用这里已建的 ddb resource / s3 client。本 Lambda 要读整份运行定义，RunStore 必须带 jobs 对象的
    存取（ADR 0030 决定六「云端提交记录」条的「装配」一项），漏装时读整份运行定义对每个 run 都抛装配缺失，第一次推进即暴露。prefix 用
    REPORT_DIR（判定明细与报告的落点）；jobs 对象在定义前缀下、不随它变化。**不含 run_id**——S3*Store 内部自拼 `{prefix}{run_id}/…`。
    region 不传：它在 build_cloud_stores 里只喂建句柄的那两个钩子，而此处两个句柄都已注入、钩子不会执行。detached 不传（默认
    False）：本 Lambda 只读已存在的 run，不建 run。判定存储是裸的 S3ResultStore，不套本机推进器的保存重试：保存失败让这条记录失败，
    由流的重试或之后的触发再做。"""
    import boto3
    from gherkai_runtime import compose, names

    region = os.environ.get("REGION") or os.environ.get("AWS_REGION")
    ddb = boto3.resource("dynamodb", region_name=region)
    s3 = boto3.client("s3", region_name=region)
    runs_table_name = os.environ["RUNS_TABLE"]
    events_table_name = os.environ["EVENTS_TABLE"]
    bucket = os.environ["ARTIFACTS_BUCKET"]
    report_dir = os.environ.get("REPORT_DIR", "reports")
    run_store, result_store, report_store = compose.build_cloud_stores(
        table=runs_table_name, bucket=bucket, prefix=report_dir,
        ddb_table=ddb.Table(runs_table_name), s3=s3)
    return _Backend(
        region=region, s3=s3, ecs=boto3.client("ecs", region_name=region),
        events_table=ddb.Table(events_table_name), events_table_name=events_table_name,
        run_store=run_store, result_store=result_store, report_store=report_store,
        bucket=bucket, report_dir=report_dir, prefix=os.environ.get("PREFIX", names.DEFAULT_PREFIX),
        cluster=os.environ["CLUSTER"])


class _Assembled(NamedTuple):
    """过闸之后为推进装配好的部分，供推进步骤、job 到点停止与生成报告使用（`_assemble`）。本机后台推进进程的对应装配是
    `detached.assemble_local_run`（它用自己生成的运行定义，不从记录读回）。"""

    meta: object  # RunMeta：闸读回的运行定义
    event_log: object
    run_store: object
    launcher: object
    max_concurrency: int
    result_store: object
    report_store: object


def _assemble(run_id: str, meta, backend: _Backend) -> _Assembled:
    """过闸之后、推进之前的装配（闸的第三步）：事件读写、CloudLauncher 与并发上限。后端到期结束不推进、不装配它们。

    **FargateEngine 装配复用 compose.build_fargate_engines**（单一真源、不重造）——job-in 前缀 / artifact 落点 / container 名 / SDK env
    只在那一处定义（ADR 0016：compose 是组合根逻辑、WebUI/Lambda 都复用、不经 cli）。Lambda 打包带上 gherkai_runtime（不背
    argparse/render）。

    **worker task-def revision 只有一条来源**（ADR 0038）：definition 的 `meta.worker_task_defs`（提交侧 preflight 已把 variant
    解析成各引擎的显式 revision）。缺该字段的云端 definition 是定义违约，闸已以结束写的 error 变体结束这个 run、不交到这里——不按后端
    默认指针回落（那会让运行中的 run 中途换 step 集）、不回落 family 最新 ACTIVE、不回落模板 revision（ADR 0037 决策 7 不留兼容分支）。
    """
    import boto3
    from gherkai_core.adapters.cloud_launcher import CloudLauncher
    from gherkai_core.adapters.event_log import DdbEventLog
    from gherkai_runtime import compose, names

    event_log = DdbEventLog(backend.events_table, run_id, [j.scope_id for j in meta.jobs])
    network = {
        "subnets": os.environ["SUBNETS"].split(","),
        "securityGroups": os.environ["SECURITY_GROUPS"].split(","),
        "assignPublicIp": os.environ.get("ASSIGN_PUBLIC_IP", "ENABLED"),
    }
    engines = compose.build_fargate_engines(
        run_id=run_id, cluster=backend.cluster,
        events_table=backend.events_table_name, bucket=backend.bucket, report_dir=backend.report_dir,
        network_config=network,
        worker_task_defs=dict(meta.worker_task_defs),  # definition 里的显式 revision（ADR 0038 不变量）
        region=backend.region,
        # 额外请求头从 definition 读回（ADR 0035：submit 落 META、此处重建 engine 时注入 RunTask env）
        extra_http_headers=dict(meta.extra_http_headers) if meta.extra_http_headers else None,
        # 会话预热地址同理从 definition 读回（ADR 0051 决策 13）：丢了它，worker 就会按 definition 完整性判 precheck_failed
        session_warmup_url=meta.session_warmup_url,
        ecs=backend.ecs, s3=backend.s3,
    )
    # job timeout 到点触发器（ADR 0034「job timeout」节）：env 齐才装配（KICKER_ARN/SCHEDULER_ROLE_ARN 由 IaC 注入）；缺 → None，
    # CloudLauncher 每次 launch 打降级日志（tick 防御扫仍兜）。触发所在的 group 由部署前缀经命名真源推出，与 IaC 建 group、授 IAM
    # 资源域用的是同一个函数（ADR 0033 资源清单 15.）。
    timeout_watch = None
    kicker_arn = os.environ.get("KICKER_ARN")
    scheduler_role_arn = os.environ.get("SCHEDULER_ROLE_ARN")
    if kicker_arn and scheduler_role_arn:
        timeout_watch = EventBridgeTimeoutWatch(
            boto3.client("scheduler", region_name=backend.region),
            kicker_arn=kicker_arn, role_arn=scheduler_role_arn, group_name=names.schedule_group_name(backend.prefix))
    launcher = CloudLauncher(compose.make_resolver(engines), run_id=run_id, timeout_watch=timeout_watch)
    # 并发上限（ADR 0034 机制四）取 min(definition 声明, 部署侧 cap)。cap 是本 Lambda 的 MAX_CONCURRENCY env（IaC 设）：语义是
    # **部署侧 per-run 上限**、非真源——task 在部署方 cluster 上运行、计入部署方账单，故部署方保留总量控制权，提交侧声明再高也钳到
    # cap。meta 无值（打通前落的旧 definition）按 1，与打通前行为一致；`or` 顺带把 0 也当无值——0 会让 plan_next 永不提议起 job（run
    # 卡死），按 1 运行是保守可收敛的兜底。env 漏注（IaC 改坏/手工建的 Lambda）时保守回 **1**：cap 的数值真源在 IaC 一处，code 不
    # 复制部署值（复制就是两处各一份、IaC 调了 cap 而这里没跟就成隐形漂移）。缺省宁可慢（串行仍收敛），不替部署方放宽闸。
    cap = int(os.environ.get("MAX_CONCURRENCY", "1"))
    max_concurrency = min(meta.max_concurrency or 1, cap)
    return _Assembled(meta, event_log, backend.run_store, launcher, max_concurrency,
                      backend.result_store, backend.report_store)


# ============================================================================
# 结束之后清扫（ADR 0054 决策九第 2 条）
# ============================================================================

# 清扫时 StopTask 的 reason：一句说明，只给看 ECS 控制台的人读。不含超时哨兵 `TIMEOUT_STOP_SENTINEL`：含了它，退出观察者会把这次退出
# 记成超时（ADR 0034「job timeout」节归因链）。StopTask 的 reason 至多 1024 个字符（ADR 0054 实测项 27）。
_SWEEP_STOP_REASON = "gherkai: the run has ended; stopping its remaining task"


def _sweep(run_id: str, backend: _Backend) -> int:
    """清扫：按启动时带的 run 标识（startedBy）列出这个 run 期望状态为运行中的 task，翻页取全，逐个停掉；返回停掉的个数。

    run 结束之后才调用（何时清扫的规则见 ADR 0054 决策九第 2 条①③，调用点都在本模块：闸读到运行态不存在或已结束、error 变体之后、
    推进步骤得知 run 已结束）。cluster 是部署注入的 `{prefix}cluster`；startedBy 与 cluster 两者属跨版本不变的约定（ADR 0037
    决策 7），别的版本起的 task 同样列得出、停得掉。只列期望状态为运行中的：按启动标识再带期望状态是已核过的写法（ADR 0054
    实测项 27）。列到之后才停下的 task 不另作处理：StopTask 对正在停止与已停止的 task 照常成功返回（同一实测项）。不写 runs 表，可以
    重复执行，不要求恰好一次。ListTasks 与 StopTask 的错误原样抛出，记为这条记录的失败（同一条「失败与批的隔离」）：ListTasks 失败时
    什么都不停；某个 task 的 StopTask 失败时先把列出的其余 task 照常停掉，再抛出第一个失败，一个停不掉的 task 不让同一 run 的别的 task
    留到重试。

    每次停掉的是这一次列得出的 task：启动调用还没有返回、或刚启动还列不出来的 task 这一次漏掉，交给之后带到这个 run 的调用。
    调用方有运行态不存在与 run 已结束两种，日志只说这一次列出与停掉了什么，不说 run 怎样了（那一句由调用方记）。"""
    arns: list[str] = []
    token = None
    while True:
        kwargs = {"cluster": backend.cluster, "startedBy": run_id, "desiredStatus": "RUNNING"}
        if token:
            kwargs["nextToken"] = token
        resp = backend.ecs.list_tasks(**kwargs)
        arns.extend(resp.get("taskArns", []))
        token = resp.get("nextToken")
        if not token:
            break
    failures: list[tuple[str, Exception]] = []
    for arn in arns:
        try:
            backend.ecs.stop_task(cluster=backend.cluster, task=arn, reason=_SWEEP_STOP_REASON)
        except Exception as exc:  # 记下、接着停别的，全部试过之后再抛出
            failures.append((arn, exc))
    stopped = len(arns) - len(failures)
    if not arns:
        print(f"sweep: run {run_id}：没有列出仍在执行的 task")
    elif not failures:
        print(f"sweep: run {run_id}：停掉仍在执行的 {stopped} 个 task")
    else:
        print(f"sweep: run {run_id}：列出仍在执行的 {len(arns)} 个 task，停掉 {stopped} 个，"
              f"{len(failures)} 个没有停掉、稍后重试：{'、'.join(arn for arn, _ in failures)}")
        raise failures[0][1]
    return stopped


# ============================================================================
# 后端各入口共用的闸（ADR 0054 决策九「落实时，后端各入口先过同一道闸」）
# ============================================================================

class _Gate(Enum):
    """过闸的结果。"""

    ADMITTED = "admitted"      # 运行态未结束、记录格式与运行定义都可用：交给入口装配之后推进
    SWEPT = "swept"            # 运行态不存在、run 已结束，或这一次以 error 变体结束了它（或它重读到已结束）：已清扫
    UNREADABLE = "unreadable"  # 运行态读不出：只记了日志，不写、不推进、不清扫


@dataclass(frozen=True)
class _GateResult:
    gate: _Gate
    meta: object = None  # RunMeta：只在 ADMITTED 时有，闸读回的整份运行定义


def _gate(run_id: str, backend: _Backend) -> _GateResult:
    """后端各入口共用的闸：reconciler 处理 events 表流的记录，kicker 处理 runs 表流的两种记录与 job 到点停止的触发，都先调它，先于各入口
    的一切动作（ADR 0054 决策九「落实时，后端各入口先过同一道闸」）。同一种情形在各入口得到同一种处理，判断只在这里。

    第一步，强一致读运行态，先只读其中的公共部分（`DynamoDBRunStore.read_state_common`）：
    - 不存在即清扫（何时清扫的规则①），不读提交记录、不写；
    - 公共部分读不出即记一行日志，不写、不推进、不清扫；
    - run 级状态已结束即清扫（规则③「闸读到已结束」）；
    - 未结束即进第二步（`_gate_definition`）。
    读取本身的错误原样抛出，记为这条记录的失败（ADR 0054 决策九第 2 条「失败与批的隔离」）。

    已结束的 run 只读运行态、不读提交记录的头：迟到与重放的事件、到点时已结束的 job 到点停止都在这里只清扫（ADR 0034 端到端 cloud 4.
    「已收尾的 run 不再推演」，判在读运行定义之前）。这道闸是先读后判、不是原子的：别的调用在这次读之后才使 run 成为终态时，推进步骤
    自己读到终态即停止推演（ADR 0034 机制三「run 级状态只进不退」条④），条件写挡下更晚的写。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable

    try:
        common = backend.run_store.read_state_common(run_id)
    except RunStateUnreadable as exc:
        return _unreadable(run_id, exc)
    if common is None:
        print(f"skip: run {run_id} 的运行状态记录不存在，不推进")
        _sweep(run_id, backend)
        return _GateResult(_Gate.SWEPT)
    if common.ended:
        print(f"skip: run {run_id} 已结束，不再改写它的结果")
        _sweep(run_id, backend)
        return _GateResult(_Gate.SWEPT)
    return _gate_definition(run_id, common, backend)


def _gate_definition(run_id: str, common, backend: _Backend) -> _GateResult:
    """闸的第二步（run 未结束）：强一致读提交记录的头（`DynamoDBRunStore.read_head`），按头里的记录格式版本分支。

    - 头不在，或头里的记录格式版本不是整数：以结束写的 error 变体结束，原因取「提交记录不完整或形态不对」那一句，之后清扫；
    - 头里的记录格式版本不是后端的（缺这个属性读作 0）：error 变体，原因取记录格式版本不合的那一句，之后清扫；不取 jobs 对象，也不按
      后端的格式读运行态的其余部分；
    - 是后端的：按后端的格式读运行态的其余部分（`state_from_common`，用第一步读到的条目），读不出与第一步「公共部分读不出」同样处理；
      读得出时取 jobs 对象、读整份运行定义（`meta_from_head`，头不另读），不可用即 error 变体之后清扫：定义违约与 jobs 对象已不在取
      「提交记录不完整或形态不对」那一句，缺任务定义修订取没有记下 worker 镜像的那一句。jobs 对象已不在凭「键不存在」认出（ADR 0030
      决定六「jobs 对象取不到时」的后端一项）：本 Lambda 的执行角色有桶的列举权限（ADR 0033「资源清单」10.），缺键得到的就是它；取回
      jobs 对象时别的错误（含拒绝访问）与读头的错误一样原样抛出，记为这条记录的失败，由之后的触发再读——拒绝访问不能确认对象已不在，
      记成 error 会把一次可能恢复的故障永久定下。
    各句原因的写法在 `run_status`（ADR 0031 决定三「结束写」小节说明表下）。契约异常的原文只进诊断行、不进运行态：它带内部字段名与
    形状描述，是给 contributor 的。error 变体之后不生成报告：报告按运行定义逐个列出 job，读不到运行定义就组装不出（ADR 0034 机制三
    「不经推进步骤的收尾」）。不为旧 definition 留兼容路径：worker_task_defs 缺失不再按后端默认指针回落（ADR 0038 不变量）。

    记录格式版本按后端的那一个比（`serialize.DEFINITION_SCHEMA_VERSION`）。头的顶层是后端的格式、meta_json 里的副本却不是时，两处
    本该恒同而不同，按形态不对处理。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable
    from gherkai_core.adapters.run_store.jobs_object import JobsObjectFailure, JobsObjectUnreadable
    from gherkai_core.errors import DefinitionContractError, UnsupportedDefinitionSchema
    from gherkai_core.run_status import DEFINITION_CONTRACT_REASON, NO_WORKER_IMAGES_REASON, schema_mismatch_reason
    from gherkai_core.serialize import DEFINITION_SCHEMA_VERSION

    run_store = backend.run_store
    head = run_store.read_head(run_id)
    if head is None:
        # 运行态在而提交记录的头不在只会是记录被删去（建 run 先写头、后写运行态，见 DynamoDBRunStore.create_run）
        return _end_as_error(run_id, DEFINITION_CONTRACT_REASON, "提交记录不存在", backend)
    try:
        version = head.schema_version()
    except DefinitionContractError as exc:
        return _end_as_error(run_id, DEFINITION_CONTRACT_REASON, str(exc), backend)
    if version != DEFINITION_SCHEMA_VERSION:
        return _end_as_error(run_id, schema_mismatch_reason(version, DEFINITION_SCHEMA_VERSION, head.cli_version), None,
                             backend)
    try:
        run_store.state_from_common(common)
    except RunStateUnreadable as exc:
        return _unreadable(run_id, exc)
    try:
        meta = run_store.meta_from_head(head)
    except (UnsupportedDefinitionSchema, DefinitionContractError) as exc:
        return _end_as_error(run_id, DEFINITION_CONTRACT_REASON, str(exc), backend)
    except JobsObjectUnreadable as exc:
        if exc.failure is not JobsObjectFailure.MISSING:
            raise
        return _end_as_error(run_id, DEFINITION_CONTRACT_REASON, str(exc), backend)
    if not meta.worker_task_defs:
        return _end_as_error(run_id, NO_WORKER_IMAGES_REASON, None, backend)
    return _GateResult(_Gate.ADMITTED, meta)


def _unreadable(run_id: str, exc: Exception) -> _GateResult:
    """运行态读不出：只记一行日志，不写、不推进、不清扫，同批别的 run 照常；不算这条记录的失败（ADR 0054 决策九「落实时」第一步）。
    读不出就无从做条件写，也分不清 run 是否已结束，清扫可能停掉仍在执行的 task。"""
    print(f"skip: run {run_id} 的运行状态记录读不出，不推进、不改写，也不停它的 task：{exc}")
    return _GateResult(_Gate.UNREADABLE)


def _end_as_error(run_id: str, reason: str, detail: str | None, backend: _Backend) -> _GateResult:
    """以结束写的 error 变体结束这个 run（`DynamoDBRunStore.end_run_as_error`，不在 RunStore 端口上；ADR 0031 决定三「结束写」小节），
    之后清扫：写成即这一次使 run 成为终态；没写成是它重读到 run 已结束（别的写方先使 run 成为终态）或运行态已不在，两者同样清扫
    （ADR 0054 决策九第 2 条③与①）。它重读到的运行态公共部分读不出时不写，按读不出的记录处理、不清扫。

    诊断行在写成之后才记：没有写成时「标为 error」不属实。结束写本身抛错时（写入竞争的重读次数用尽、DynamoDB 调用失败）先记下原因与
    诊断再原样抛出，记为这条记录的失败：这次写可能一直写不成，日志里不能只剩回溯。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable
    from gherkai_runtime import compose

    diagnosis = f"——{reason}" + (f"；诊断：{detail}" if detail else "")
    try:
        ended = backend.run_store.end_run_as_error(run_id, reason, ended_at=compose.now_iso())
    except RunStateUnreadable as exc:
        return _unreadable(run_id, exc)
    except Exception:
        print(f"reject: run {run_id} 不推进{diagnosis}；把它标为 error 的写没有写成")
        raise
    if ended:
        print(f"reject: run {run_id} 不推进、标为 error{diagnosis}")
    else:
        print(f"skip: run {run_id} 已结束或运行状态记录已不在，没有再把它标为 error")
    _sweep(run_id, backend)
    return _GateResult(_Gate.SWEPT)


# ============================================================================
# 过闸之后：推进一步，按推进步骤的结果收尾
# ============================================================================

def _advance(run_id: str, built: _Assembled, backend: _Backend, label: str) -> None:
    """推进一步（`reconcile.tick`），按它的三种结果收尾（`TickOutcome`，ADR 0034 机制三「run 级状态只进不退」条④）：

    - 这一方的写使 run 成为终态（COMMITTED）：从记录生成 RunReport，再清扫（ADR 0054 决策九第 2 条③「生成报告之后」）；
    - run 已结束而使它成为终态的不是这一方（ENDED）：不写报告、不做超时扫，清扫；
    - 继续推进（CONTINUE）：防御性超时扫。

    判定明细由 tick 在写下这一轮各 job 的终态之前存进判定存储，每份带一个新标识，终态写点名它（ADR 0030 决定三「点名」条）；存明细或
    写运行态的异常原样抛出，记为这条记录的失败，由流的重试或之后的触发重做，重做的那一次另存一份、点名新的标识。报告生成与防御性超时
    扫描的失败隔离在调用之内（ADR 0054 决策九第 2 条「失败与批的隔离」）：报告在终态写之后生成、失败无人重试，记为失败只会让流按批
    重试，重试的调用读到 run 已结束只清扫、补不回报告（ADR 0034 端到端 cloud 第 4 步）；防御扫是 Scheduler 到点触发器的双保险，它
    失败不该拖累已经推进成功的这一步。清扫的失败记为这条记录的失败。"""
    from gherkai_core.reconcile import TickOutcome, tick, write_report_from_record
    from gherkai_runtime import compose  # 时钟走 compose.now 单一读取点（同 local/前台两宿主，格式不漂移）

    meta, event_log, run_store, launcher, mc, rstore, pstore = built
    outcome = tick(run_id, meta, event_log, run_store, launcher, mc, clock=compose.now, result_store=rstore)
    if outcome is TickOutcome.ENDED:
        # 闸之后 run 已被别处结束（tick 读运行态之前，或这一方的终态写、结束写之前）：报告不改写
        print(f"{label}: run {run_id} 已结束，不再改写它的结果")
        _sweep(run_id, backend)
    elif outcome is TickOutcome.COMMITTED:
        # 报告从记录生成，入口是 core 唯一的一份，本机后台推进进程调的是同一个；读运行态、按点名的标识读回明细、组装与写报告整段在
        # 入口的失败隔离之内。明细每份一次 GetObject，不列举前缀。
        write_report_from_record(meta, run_store, rstore, pstore, created_at=compose.now_iso())
        print(f"{label}: run {run_id} done + committed")
        _sweep(run_id, backend)
    else:
        print(f"{label}: run {run_id} advanced (not done)")
        try:
            _scan_overdue_timeouts(run_id, built, ecs_client=backend.ecs)
        except Exception as exc:
            print(f"{label}: run {run_id} 超时兜底检查未完成，稍后重试：{exc}")


# ============================================================================
# 失败与批的隔离（ADR 0054 决策九第 2 条「失败与批的隔离」）
# ============================================================================

class _RunsNotDone(RuntimeError):
    """这次调用里有 run 的处理失败：同一批里别的 run 都已各自处理完，抛出它让这次调用失败，由流的重试或 AWS 的重试再调用。
    `failed` 是失败的 run 标识，按处理的次序。"""

    def __init__(self, label: str, failed: list[str]) -> None:
        super().__init__(f"{label}: {len(failed)} 个 run 这次没有处理完，稍后重试：{'、'.join(failed)}")
        self.failed = failed


def _each_run(label: str, work: list[tuple[str, Callable[[], None]]]) -> dict:
    """逐个 run 各自处理（work 是 run 标识与它的处理），任何一个的失败不打断别的；全部处理完之后只要有失败，就抛 `_RunsNotDone`，让这次
    调用失败：流事件由流重试这一批，定时触发的调用（只带一个 run）由 AWS 的重试再调用。重试时已做过的再做一遍，各步幂等、结果不变。

    记为失败的是处理里原样抛出的异常（读运行态、读运行定义、结束写含 error 变体、推进步骤里的读写、job 到点停止、清扫）；报告生成、
    防御性超时扫描与推进里为 job 建到点触发的失败在各自的调用点隔离，运行态读不出只记日志，都不到这里。这一层只管次序与汇总，哪些算
    失败由各调用点决定。"""
    failed: list[str] = []
    done: list[str] = []
    for run_id, step in work:
        try:
            step()
        except Exception:
            failed.append(run_id)
            print(f"{label}: run {run_id} 这次没有处理完，这次调用最后会失败、稍后重试；同一批里别的 run 照常处理：\n"
                  f"{traceback.format_exc()}")
        else:
            done.append(run_id)
    if failed:
        raise _RunsNotDone(label, failed)
    return {"ok": True, "runs": done}


# ============================================================================
# 两个入口
# ============================================================================

def handler(event, context):
    """events 表 Stream 入口（reconciler 主推进）：worker PutItem / task_exited 触发 → 对涉及的每个 run 过闸、推进一步。同一批里按
    run 去重（`_run_ids_from_stream`），各 run 各自处理（`_each_run`）。"""
    run_ids = sorted(_run_ids_from_stream(event))
    if not run_ids:
        return {"ok": True, "runs": []}
    backend = _backend()

    def advance(run_id: str) -> None:
        result = _gate(run_id, backend)
        if result.gate is _Gate.ADMITTED:
            _advance(run_id, _assemble(run_id, result.meta, backend), backend, "reconciler")

    return _each_run("reconciler", [(rid, lambda rid=rid: advance(rid)) for rid in run_ids])


# runs 表流记录的两种（kicker 按记录的种类分辨，不按读到的状态，ADR 0054 决策九第 1 条与被拒方案「按读到的状态决定建不建 run 级
# 触发」；两条过滤的形态见 ADR 0033 资源清单 13.）
_NEW_RUN = "new-run"      # STATE 条目的新建：过闸之后首轮推进
_RUN_ENDED = "run-ended"  # 使 run 成为终态的那次写（新映像的状态分组不是 live 的 STATE 条目）：过闸、只清扫


def _image_s(image, name: str):
    """流记录新映像里一个字符串属性的值；映像或属性不在、不是字符串类型时为 None。"""
    attr = image.get(name) if isinstance(image, dict) else None
    value = attr.get("S") if isinstance(attr, dict) else None
    return value if isinstance(value, str) else None


def _runs_record_kind(rec) -> tuple[str | None, str | None]:
    """一条 runs 表流记录 →（种类, run 标识），认不出时种类为 None。只认两种：eventName 为 INSERT、新映像是 STATE 条目（STATE 的新建）；
    eventName 为 MODIFY、新映像是 STATE 条目且状态分组在而不是 live（使 run 成为终态的那次写）。别的（META 的新建、状态分组仍是 live
    的修改、REMOVE 等过滤本不放过的记录）都认不出。属性名与取值经命名真源，与 core 写下的逐字一致。"""
    from gherkai_runtime import names

    ddb = rec.get("dynamodb") if isinstance(rec, dict) else None
    ddb = ddb if isinstance(ddb, dict) else {}
    run_id = _image_s(ddb.get("Keys"), "run_id")
    image = ddb.get("NewImage")
    if not run_id or _image_s(image, names.RUNS_ITEM_TYPE_ATTR) != names.RUNS_STATE_ITEM:
        return None, run_id
    event_name = rec.get("eventName")
    if event_name == "INSERT":
        return _NEW_RUN, run_id
    group = _image_s(image, names.STATE_STATUS_GROUP_ATTR)
    if event_name == "MODIFY" and group is not None and group != names.STATUS_GROUP_LIVE:
        return _RUN_ENDED, run_id
    return None, run_id


def _runs_from_runs_stream(event) -> dict[str, str]:
    """runs 表流的一批记录 → {run 标识: 种类}，同一批里按 run 去重。同一个 run 在同一批里既有 STATE 的新建又有使它成为终态的写时按
    新建处理：新建一支同样先过闸，读到已结束即只清扫，与终态写那一支结果相同。认不出的记录记一行日志、跳过，不推进、不算失败。"""
    kinds: dict[str, str] = {}
    for rec in event.get("Records") or []:
        kind, run_id = _runs_record_kind(rec)
        if kind is None:
            event_name = rec.get("eventName") if isinstance(rec, dict) else None
            print(f"kicker: 跳过一条认不出的运行状态表流记录（eventName={event_name!r}，run={run_id!r}）")
            continue
        if kinds.get(run_id) != _NEW_RUN:
            kinds[run_id] = kind
    return kinds


def _job_timeout_payload(event) -> tuple[str, str] | None:
    """job 到点停止的触发载荷 `{"run_id", "timeout_scope"}`（`EventBridgeTimeoutWatch.arm` 建的触发投递的）→（run 标识, scope），
    形态不对时为 None。"""
    if not isinstance(event, dict):
        return None
    run_id, scope_id = event.get("run_id"), event.get("timeout_scope")
    if isinstance(run_id, str) and run_id and isinstance(scope_id, str) and scope_id:
        return run_id, scope_id
    return None


def kicker_handler(event, context):
    """kicker 入口：只认几种载荷，按载荷的形态分派（ADR 0034「推进器与触发源」第 2 条）。

    - **runs 表流记录**（`Records`）：按记录的种类分辨、不按读到的状态（`_runs_from_runs_stream`）。STATE 条目的新建：过闸之后做首轮
      推进（冷启动：submit 建 run → kicker 起首批 task）。使 run 成为终态的那次写：过闸，读到已结束即清扫，不推进。各 run 各自处理。
    - **job 到点停止**（`{"run_id","timeout_scope"}`，EventBridge Scheduler 的到点 invoke，ADR 0034「job timeout」节）：先过闸（先看
      run、再看 job），再做 job 到点停止（仍 running 且截止时刻已到才 StopTask/收敛，触发早于截止时刻时先等到那时），然后照常推进一步
      （到点 invoke 本身即一次强制推进）。等待上界在临睡前按本次调用的剩余时间算（复查的读取之后），见 `_timeout_wait_budget_s`。
      定时触发的调用只带一个 run：记为失败的各项与 job 到点停止里的失败让这次调用失败，由 AWS 的重试再调用。
    - 其余载荷（含只带 run 标识的）记一行日志、正常返回，不推进、不抛出：抛出会让异步调用重试一个没有意义的载荷。

    与 reconciler 共用闸、装配与推进一步（三个宿主一份 tick：本机后台推进进程 / kicker / reconciler）。kicker 由 runs 表流上的两条
    过滤触发（ADR 0033 资源清单 13.），投影、认领与 job 状态的写不在其中，不被推进器自己对 runs 表的写唤醒。
    """
    if isinstance(event, dict) and "Records" in event:
        kinds = _runs_from_runs_stream(event)
        if not kinds:
            return {"ok": True, "runs": []}
        backend = _backend()

        def on_record(run_id: str, kind: str) -> None:
            result = _gate(run_id, backend)
            if result.gate is not _Gate.ADMITTED:
                return
            if kind == _RUN_ENDED:
                # 使 run 成为终态的写之后运行态不再变（ADR 0054 决策五），读到未结束只会出自记录被改动；只清扫的这一支不推进
                print(f"kicker: run {run_id} 的终态写之后读到它仍未结束，这次不做别的")
                return
            # STATE 条目的新建。这个 run 的两次 run 级定时触发建在过闸之后、首轮推进之前，即这一行之前（ADR 0054 决策九第 1 条）；
            # 建立尚未实装
            _advance(run_id, _assemble(run_id, result.meta, backend), backend, "kicker")

        return _each_run("kicker", [(rid, lambda rid=rid, kind=kind: on_record(rid, kind)) for rid, kind in kinds.items()])

    timeout = _job_timeout_payload(event)
    if timeout is not None:
        run_id, scope_id = timeout
        backend = _backend()

        def on_timeout() -> None:
            result = _gate(run_id, backend)
            if result.gate is not _Gate.ADMITTED:
                return  # run 不存在或已结束时闸已清扫，不做 job 到点停止（到点时 job 已终态的常态）
            built = _assemble(run_id, result.meta, backend)
            _handle_timeout(run_id, scope_id, built, ecs_client=backend.ecs,
                            wait_budget_fn=lambda: _timeout_wait_budget_s(context))
            _advance(run_id, built, backend, "kicker")

        return _each_run("kicker", [(run_id, on_timeout)])

    keys = sorted(event) if isinstance(event, dict) else type(event).__name__
    print(f"kicker: 认不出的调用载荷，不处理（键：{keys}）")
    return {"ok": True, "runs": []}


def _timeout_wait_budget_s(context) -> float | None:
    """本次 invoke 还能拿多少秒等到 deadline：Lambda 剩余时间减去等完之后处置与 tick 所需的 `_TIMEOUT_HANDLING_RESERVE_S`。
    context 不带剩余时间（测试或直接调用）时返回 None，只受固定等待上界约束。"""
    remaining_ms = getattr(context, "get_remaining_time_in_millis", None)
    if remaining_ms is None:
        return None
    return remaining_ms() / 1000.0 - _TIMEOUT_HANDLING_RESERVE_S
