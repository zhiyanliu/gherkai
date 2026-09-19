"""reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。

events 表开 Stream（NEW_IMAGE），worker PutItem 执行事件 / 退出观察者写 task_exited → Stream 触发本 handler。
它从 Stream records 提取涉及的 run_id 集（去重），对每个 run 调 gherkai_core.reconcile.tick 推进一步（读全量重放 →
project → 条件写 → plan_next → CAS 抢占起下一个 job / finalize）。tick 幂等 + CAS/HWM 条件写兜底——Stream 按
分片并发触发多个本 handler 实例、叠加 status --wait 接力，全部安全（机制三/四，真 DDB 已验）。

**cloud 组合根（Lambda 装配）**：cold-start 读 env 造 boto3 client + 三 store adapter + FargateEngine + CloudLauncher
注入纯 reconcile.tick——**是组合根注入、非 ports 内部 env-sniff 全局单例**（[0016] 禁的 GlobalConfigManager 反模式，
此处每次 handler 显式构造、无隐式全局态）。core 一行不为 cloud 改（同 local，只换注入的 EventLog/Launcher/RunStore）。

打包：本文件是 **asset 原料**（住在 provider 包 `gherkai_deploy_aws/lambdas/`，摊到 zip 根，ADR 0037 决策 6）。
env：**IaC 注入**（`gherkai_deploy_aws/stack.py` 的 reconciler/kicker Function）=
RUNS_TABLE / EVENTS_TABLE / ARTIFACTS_BUCKET / CLUSTER / PREFIX / REGION / SUBNETS / SECURITY_GROUPS /
MAX_CONCURRENCY（**部署侧 per-run 并发 cap**、非真源——真源是 definition 的 `RunMeta.max_concurrency`，取
min，ADR 0034 机制四；数值真源在 IaC 一处，本文件缺省只在 env 漏注时保守回 1、不复制部署值）/ KICKER_ARN / SCHEDULER_ROLE_ARN（job timeout 到点触发器用，ADR 0034「job timeout」节）；**本文件缺省供给、IaC 不注入** = REPORT_DIR（reports）/ ASSIGN_PUBLIC_IP（ENABLED，与公有子网
配套）——要改产物落点前缀或走私有子网时才在 IaC 显式给。

**worker 镜像用哪个 task-def revision 不经 env**（ADR 0038 不变量「运行时只用 definition 里的显式 revision」）：
正常路径读 definition 的 `RunMeta.worker_task_defs`；旧 definition 缺该字段时按**后端当前默认指针**从 SSM
解析（见 `_build` 的兼容路径）。**推进器绝不用模板 revision**——其镜像栏是 `latest` 占位，全新 prefix 上从未
推过该 tag，拉镜像会拖到 Fargate 启动期才炸（ADR 0038 被拒方案）。故本文件不读任何模板 ARN 类 env。
"""
from __future__ import annotations

import datetime as _dt
import os


def _run_ids_from_stream(event) -> set[str]:
    """从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch 可能多条同 run。

    **REMOVE 记录跳过**：events 表开 TTL（`expires_at`，两引擎的 event sink 写 emit+7d），TTL 过期删除同样进
    Stream、同样带 Keys。它不携带任何新信息，却会让本 handler 对一个早已收尾的 run 重新运行一次全量重放——那时
    worker 事件已被删、只剩不带 `expires_at`（永不过期）的退出记录，推演出的每个 job 都成 error 并按 ADR 0030
    决定三的写序覆盖 ResultStore 里的判定真值。用 `.get` 只排除 REMOVE、**不做 INSERT 白名单**：events 表虽只
    PutItem，同键重写（超时处置直写的退出记录被迟到的观察者以真退出码/归因重写）在 Stream 上是 MODIFY。
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
# job timeout（ADR 0034「job timeout」节 cloud 档）：到点触发器 + 超时处置 + 防御扫
# ============================================================================

# StopTask reason 里的超时哨兵串：经 STOPPED 事件 detail.stoppedReason 原样出现（现成通道、零新键空间），
# exit_observer 见它 → task_exited(timed_out=True) → 归因链收敛 ERROR+timeout。哨兵串的比对封在 `exit_from_task`
# 里，观察者 Lambda 与超时处置经该函数共用（都不各自 import 本常量）。
TIMEOUT_STOP_SENTINEL = "gherkai-job-timeout"


def exit_from_task(task: dict) -> tuple[int, bool, str | None]:
    """ECS task 对象 → 退出记录三元组 (exit_code, timed_out, reason)。**观察者与超时处置共用**（ADR 0034 机制二）。

    STOPPED 事件的 `detail` 与 `DescribeTasks` 的 `tasks[i]` 是同一个 Task 形状，故同一 task 两边算出同一内容、
    PutItem 同键幂等——超时处置对「已 STOPPED 却无退出记录」（事件丢投）落的记录，与迟到的观察者写入不互撞。
    exit_code：containers[] 首个带 exitCode 的（worker 是 essential 单容器）；**缺 → PLATFORM_FAILED_EXIT 哨兵**
    + reason=`stopCode: stoppedReason`（容器没能开始运行，机制二「退出码缺失」条）。timed_out：stoppedReason 含本模块
    StopTask 时写入的哨兵串（「job timeout」节归因链）。
    """
    from gherkai_core.project import PLATFORM_FAILED_EXIT

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
        reason = ": ".join(x for x in (task.get("stopCode"), stopped_reason) if x) or "平台未给出退出码与原因"
    return exit_code, timed_out, reason


def _task_scope_id(task: dict) -> str | None:
    """RunTask 注入的 env SCOPE_ID 原样在 overrides.containerOverrides[].environment（观察者/超时处置同一提取术）。"""
    for co in task.get("overrides", {}).get("containerOverrides", []):
        for e in co.get("environment", []):
            if e.get("name") == "SCOPE_ID":
                return e.get("value")
    return None

# 防御扫（claimed_at ②）的判定余量秒：Scheduler one-time schedule 是主机制（到点准时处置），扫是双保险——
# 余量让主机制先行、避免与在途的 STOPPED→exit_observer 链形成竞态。非正确性参数（处置幂等、退出记录在即让路）。
_DEFENSIVE_TIMEOUT_MARGIN_S = 60.0


class EventBridgeTimeoutWatch:
    """job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个
    EventBridge Scheduler **one-time schedule**（at = now+timeout、ActionAfterCompletion=DELETE 到点自动删
    ——无常驻轮询、idle 零成本）→ 到点 invoke kicker（payload {"run_id","timeout_scope"}）走超时处置。

    schedule 名 = `names.job_timeout_schedule_prefix(prefix)` + sha1(run_id#scope_id)[:20]：确定性（重复 arm
    幂等，ConflictException 视作已武装）、合法字符集（scope_id 可含中文/路径，不能直接入名）、≤64 字符。
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

        digest = hashlib.sha1(f"{run_id}#{scope_id}".encode("utf-8")).hexdigest()[:20]
        return f"{names.job_timeout_schedule_prefix(self._prefix)}{digest}"

    def arm(self, run_id: str, scope_id: str, timeout_s: float) -> None:
        import json

        at = _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(seconds=timeout_s)
        try:
            self._client.create_schedule(
                Name=self.schedule_name(run_id, scope_id),
                # at() 表达式不带时区后缀（Scheduler 默认 UTC）；秒级精度足够（timeout 是分钟级预算）
                ScheduleExpression=f"at({at.strftime('%Y-%m-%dT%H:%M:%S')})",
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


def _handle_timeout(run_id: str, scope_id: str, built, ecs_client=None) -> str:
    """超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id) **同时列
    RUNNING 与 STOPPED**（后者 ECS 保留约 1h）→ DescribeTasks 按 overrides env SCOPE_ID 匹配 → 按 task 状态三路：
    - 运行中 → StopTask(reason 含哨兵) → STOPPED 事件 → exit_observer 记 task_exited(timed_out=True)（stop 后让观察链
      自然收敛 = 单一真源）；
    - **正在停止**（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不动、等观察者。曾只列 RUNNING、把它判成
      「无踪」直写 timed_out，与几秒后到达的真退出记录同键互覆——恰在预算点运行结束的 passed job 可被终判成 timeout；
    - **已 STOPPED 却无退出记录**（STOPPED 事件丢投）→ 用与观察者同一提取函数 `exit_from_task` 从 task 对象落真退出
      记录（同内容同键、幂等），不臆造 timed_out。
    两个列表都无踪且无退出记录：预算已尽仍无确认完成 → 直接 record_exit(timed_out=True) 收敛——对位 local 接力恢复，
    观察链已断时直接写是唯一收敛路径。返回处置结果串（日志/测试断言用）。
    """
    import boto3
    from gherkai_core.model import Status

    meta, event_log, run_store, *_ = built
    state = run_store.load_run_state(run_id)
    js = state.jobs.get(scope_id) if state is not None else None
    if js is None or js.status != Status.RUNNING:
        return "noop-not-running"  # 到点时 job 早收敛/未知 → 幂等 no-op（best-effort 边界）
    # 只查本 scope（EventLog.has_exit 单点查）——一个 scope 的处置不该逐 scope 重放整 run 的 events。
    if event_log.has_exit(scope_id):
        return "noop-exit-in-flight"  # 退出记录已在、投影在途 → 让既有链收敛，不动手
    ecs = ecs_client if ecs_client is not None else boto3.client(
        "ecs", region_name=os.environ.get("REGION") or os.environ.get("AWS_REGION"))
    cluster = os.environ["CLUSTER"]
    arns: list[str] = []
    for desired in ("RUNNING", "STOPPED"):  # 正在停止/刚停止的不在 RUNNING 列表里——必须两个都列，否则误判「无踪」
        for arn in ecs.list_tasks(cluster=cluster, startedBy=run_id, desiredStatus=desired).get("taskArns", []):
            if arn not in arns:
                arns.append(arn)
    target = None
    if arns:
        for t in ecs.describe_tasks(cluster=cluster, tasks=arns).get("tasks", []):
            if _task_scope_id(t) == scope_id:
                target = t
                break
    if target is not None:
        arn = target["taskArn"]
        if target.get("lastStatus") == "STOPPED":
            # 已停但观察者没写（STOPPED 事件丢投）：从 task 对象落真退出记录——与观察者同一算法、同键幂等
            exit_code, timed_out, reason = exit_from_task(target)
            event_log.record_exit(scope_id, exit_code, timed_out=timed_out, reason=reason)
            print(f"timeout-converge: run={run_id} scope={scope_id} task={arn} 已 STOPPED 无退出记录 → 按 DescribeTasks 落 exit={exit_code}")
            return "converged-from-describe"
        if target.get("desiredStatus") == "STOPPED":
            # 不抢着写：退出记录由 exit_observer 收到 STOPPED 事件时落（本函数 docstring「正在停止」那路）
            print(f"timeout-noop: run={run_id} scope={scope_id} task={arn} 正在停止 → 等它的退出事件到达再收尾")
            return "noop-stopping"
        job = next((j for j in meta.jobs if j.scope_id == scope_id), None)
        budget = f"{job.timeout_s:g}" if job is not None and job.timeout_s else "?"
        ecs.stop_task(cluster=cluster, task=arn,
                      reason=f"{TIMEOUT_STOP_SENTINEL}: scope exceeded {budget}s budget")
        print(f"timeout-stop: run={run_id} scope={scope_id} task={arn}")
        return "stopped"
    event_log.record_exit(scope_id, None, timed_out=True)
    print(f"timeout-converge: run={run_id} scope={scope_id} 找不到这个 task、也没有它的退出记录 → 直接按超时结案")
    return "converged-directly"


def _scan_overdue_timeouts(run_id: str, built) -> None:
    """防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对
    RUNNING 且 now-claimed_at > timeout+余量 的 job 走同一超时处置——CreateSchedule 失败/schedule 丢失时，
    后续任何事件触发的 tick 都能补救。纯静默 job（无事件→无 tick）的主保障仍是 Scheduler 到点 invoke。"""
    from gherkai_core.model import Status
    from gherkai_runtime import compose

    meta, event_log, run_store, *_ = built
    state = run_store.load_run_state(run_id)
    if state is None:
        return
    job_by_scope = {j.scope_id: j for j in meta.jobs}
    now = _dt.datetime.now(_dt.timezone.utc)  # 纯时间差比较、不落库（落库的时间戳一律 compose.now_iso）
    for sid, js in state.jobs.items():
        job = job_by_scope.get(sid)
        if js.status != Status.RUNNING or not js.claimed_at or job is None or not job.timeout_s:
            continue
        elapsed = (now - compose.parse_iso(js.claimed_at)).total_seconds()
        if elapsed > job.timeout_s + _DEFENSIVE_TIMEOUT_MARGIN_S:
            print(f"defensive-timeout: run={run_id} scope={sid} elapsed={elapsed:.0f}s > 预算 {job.timeout_s}s+余量")
            _handle_timeout(run_id, sid, built)


def _resolve_worker_task_defs(meta, *, prefix: str, region: str | None, ssm=None) -> dict[str, str]:
    """本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。

    ① definition 带 `worker_task_defs` → **原样用**（提交侧 preflight 解析的结果，一个 run 内镜像固定：期间
       别人重推同名 variant 不影响运行中的 run）。
    ② 缺该字段（引入本机制的升级前提交、升级窗口内仍在运行的 run；或旧 CLI 提交到新后端——ADR 0037 决策 7
       「CLI 旧于后端 → 警告不拦」允许）→ 按**后端当前默认指针**解析，并**打一行点名兼容路径 + 解析到的
       variant** 的日志（「用的是哪份」必须可见、可查）。

    只解析**本 run 用到的引擎**（对齐 preflight 的判据「没用到的引擎不该拦」）。解析不出则 `WorkerVariantError`
    冒泡——本次 invoke 失败、Stream 重投；**不回落 family / 模板 revision**（ADR 0038 被拒方案两条）。
    """
    from gherkai_runtime import compose

    if meta.worker_task_defs:
        return dict(meta.worker_task_defs)
    engines = sorted({j.engine for j in meta.jobs})
    if ssm is None:
        import boto3
        ssm = boto3.client("ssm", region_name=region)
    backend_version = compose.read_backend_version(prefix=prefix, ssm=ssm)
    # 默认指针在此单独读一次**只为日志点名 variant**（`resolve_default_worker_task_defs` 内部还会读一次）——
    # 多一次 GetParameter 换「这次运行的是哪份」在 CloudWatch 里可见，值得；且兼容路径是过渡态（所有新
    # definition 都带字段、直接走 ① 分支），不是热路径。
    variant = compose.read_worker_default(prefix=prefix, ssm=ssm)
    task_defs = compose.resolve_default_worker_task_defs(
        prefix=prefix, engines=engines, backend_version=backend_version, ssm=ssm)
    print(f"worker-compat: run {meta.run_id} 的任务定义没记 worker 镜像版本（旧版 CLI 或升级前提交）→ 走兼容路径，"
          f"按后端默认指针解析 variant={variant!r} 版本={backend_version} 引擎={engines}")
    return task_defs


def _build(run_id: str):
    """cloud 组合根：读 env 造 boto3 + 装配（RunStore/EventLog/CloudLauncher + ResultStore/ReportStore）注入。

    返回 (meta, event_log, run_store, launcher, max_concurrency, result_store, report_store)——同 local
    build_local_reconcile 的形状，供 tick + finalize 聚合。meta 从 RunStore 读回（definition）。
    **None = 本 run 云端推进器不该动**（非 detached / 已收尾 / definition 不在库，三支见下）——两个 handler
    据此整体 no-op。

    **store 与 FargateEngine 装配都复用 compose（`build_cloud_stores` / `build_fargate_engines`，单一真源、
    不重造）**——三层 store 的 prefix 规范化与 offloader 挂载、job-in 前缀 / artifact 落点 / container 名 /
    SDK env 全与同步 cloud run 路径一致、零漂移（ADR 0016：compose 是组合根逻辑、WebUI/Lambda 都复用、
    不经 cli——组合根共享层即产品本体包）。Lambda 打包带上 gherkai（不再背 argparse/render）。

    **worker task-def revision 两条来源**（ADR 0038）：① definition 的 `meta.worker_task_defs`（正常路径，提交侧
    preflight 已把 variant 解析成各引擎的显式 revision）；② 缺该字段 → **兼容路径**（`_resolve_worker_task_defs`）
    按后端当前默认指针解析。解析不出即抛（本次 invoke 失败、Stream 重投），**不回落 family 最新 ACTIVE、不回落
    模板 revision**——前者等于让运行中的 run 中途换 step 集，后者的 `latest` 占位在全新 prefix 上根本拉不到镜像。
    """
    import boto3
    from gherkai_core.adapters.event_log import DdbEventLog
    from gherkai_core.adapters.cloud_launcher import CloudLauncher
    from gherkai_core.model import TERMINAL_STATUSES
    from gherkai_runtime import compose

    region = os.environ.get("REGION") or os.environ.get("AWS_REGION")
    ddb = boto3.resource("dynamodb", region_name=region)
    s3 = boto3.client("s3", region_name=region)

    runs_table_name = os.environ["RUNS_TABLE"]
    runs_table = ddb.Table(runs_table_name)
    events_table = ddb.Table(os.environ["EVENTS_TABLE"])
    bucket = os.environ["ARTIFACTS_BUCKET"]
    report_dir = os.environ.get("REPORT_DIR", "reports")
    prefix = os.environ.get("PREFIX", compose.DEFAULT_PREFIX)

    # 三层 store 走 compose.build_cloud_stores（与 submit 侧同一真源、不重造：prefix 规范化、三个 S3 件套共享
    # 一个 client、**arg_offloader 默认挂载**都由它保证），句柄注入以复用本函数已建的 ddb resource / s3 client。
    # offloader 尤其不能漏（ADR 0030 决定七「生产默认挂载、不给生产选要不要正确」）：submit 侧把 docString/
    # dataTable 正文 offload 到 S3、META 只留指针，漏挂则 load_run_meta 对含指针的 META 直接 fail-loud 抛，
    # 云端推进器整条链停在装配上。prefix 用 REPORT_DIR 与 submit 侧同源（restore 按绝对 URI 取回、实际不依赖
    # prefix，但写读两侧同构造零漂移）；**不含 run_id**——S3*Store 内部自拼 `{prefix}{run_id}/…`。
    # region 不传：它在 build_cloud_stores 里只喂建句柄的那两个钩子，而此处两个句柄都已注入、钩子不会执行。
    # detached 不传（默认 False）：本 Lambda 只读已存在的 run，不 create_run、不写 detached 标记。
    # 第四项 make_artifacts 是同步 run 打落点用的，云端推进器不打、丢弃。
    run_store, result_store, report_store, _ = compose.build_cloud_stores(
        table=runs_table_name, bucket=bucket, prefix=report_dir,
        ddb_table=runs_table, s3=s3)
    # `is_detached` 是 DDB adapter 上的方法、不在 RunStore 端口面上——cloud 档这个 store 恒是 DDB 实现。
    if not run_store.is_detached(run_id):
        # 只推进 detached run（ADR 0034 端到端 cloud 1b）：同步 `run --backend cloud` 由进程内 schedule 推进，
        # 推进器碰它就是双开推进器（抢 claim/RunTask/finalize）。kicker 那扇门由 Stream filter 挡，events 表
        # Stream 这扇门滤不了（events item 无 detached 标记）——同一判据在此判，返回 None = 全 handler no-op。
        # 判在 load_run_meta **之前**：同步 run 的每条 worker 事件都会触发本 Lambda，先判省掉强一致 META
        # 读 + offload 正文的 S3 取回，且推进器在断定「不该碰」前不读对方 definition（STATE 缺失同落此支）。
        print(f"skip: run {run_id} 不是 submit 提交的后台批次（同步的 `run --backend cloud` 由发起它的命令自己推进）")
        return None
    # **已收尾的 run 不再推演**：run 到终态时判定真值与报告都已落库，再 tick 一次只会拿「此刻还剩下的事件」
    # 重算一遍并覆盖写（ADR 0030 决定三的写序无条件执行）——events 表开 TTL，7 天后 worker 事件已被删、只剩
    # 永不过期的退出记录，重算结果是「每个 job 都 error、零 scenario」，把权威的判定真值静默销毁。触发面不只
    # TTL 的 REMOVE（那道已在 `_run_ids_from_stream` 与 IaC filter 挡）：迟到重投、手工重放同一批 Stream 记录、
    # 超时到点触发器的 payload 都落到这里——后者与 ADR 0034「到点时 job 已终态 → 处置 no-op」一致，且 run
    # 终态的前提就是每个 job 都已有退出记录或已判超时，不会漏 StopTask。
    # **明确接受的代价**：从此没有「重 tick 一个已收尾的 run 来补写丢失的报告」这条路——finalize_report 只有
    # 本 Lambda 与 detached 宿主两个调用点、本就没有独立的重生成命令，而事件过期后重 tick 只会生成错报告。
    # 判在 `load_run_meta` 之前同上一支的理由：省掉强一致 META 读 + offload 正文的 S3 取回。
    state = run_store.load_run_state(run_id)
    if state is not None and state.status in TERMINAL_STATUSES:
        print(f"skip: run {run_id} 已结束，不再改写它的结果")
        return None
    meta = run_store.load_run_meta(run_id)
    if meta is None:
        return None  # definition 不存在（META 尚未落库的极端窗口 / 别的 run）——忽略
    scope_ids = [j.scope_id for j in meta.jobs]
    event_log = DdbEventLog(events_table, run_id, scope_ids)

    # CloudLauncher 用 compose.build_fargate_engines 产的 resolver（单一真源、零漂移）。
    network = {
        "subnets": os.environ["SUBNETS"].split(","),
        "securityGroups": os.environ["SECURITY_GROUPS"].split(","),
        "assignPublicIp": os.environ.get("ASSIGN_PUBLIC_IP", "ENABLED"),
    }
    worker_task_defs = _resolve_worker_task_defs(meta, prefix=prefix, region=region)
    engines = compose.build_fargate_engines(
        run_id=run_id, prefix=prefix, cluster=os.environ["CLUSTER"],
        events_table=os.environ["EVENTS_TABLE"], bucket=bucket, report_dir=report_dir,
        network_config=network, worker_task_defs=worker_task_defs, region=region,
        # 额外请求头从 definition 读回（ADR 0035：submit 落 META、此处重建 engine 时注入 RunTask env）
        extra_http_headers=dict(meta.extra_http_headers) if meta.extra_http_headers else None,
        ecs=boto3.client("ecs", region_name=region), s3=s3, ddb_events_table=events_table,
    )
    # job timeout 到点触发器（ADR 0034「job timeout」节）：env 齐才装配（KICKER_ARN/SCHEDULER_ROLE_ARN 由
    # IaC 注入）；缺 → None，CloudLauncher 对有预算的 job 打降级日志（tick 防御扫仍兜）。
    timeout_watch = None
    kicker_arn = os.environ.get("KICKER_ARN")
    scheduler_role_arn = os.environ.get("SCHEDULER_ROLE_ARN")
    if kicker_arn and scheduler_role_arn:
        timeout_watch = EventBridgeTimeoutWatch(
            boto3.client("scheduler", region_name=region),
            kicker_arn=kicker_arn, role_arn=scheduler_role_arn, prefix=prefix)
    launcher = CloudLauncher(compose.make_resolver(engines), run_id=run_id, timeout_watch=timeout_watch)
    # 并发上限（ADR 0034 机制四）= min(definition 声明, 部署侧 cap)。cap = 本 Lambda 的 MAX_CONCURRENCY env
    # （IaC 设）：语义是**部署侧 per-run 上限**、非真源——task 在部署方 cluster 上运行、计入部署方账单，故部署方保留
    # 总量控制权，提交侧声明再高也钳到 cap。meta 无值（打通前落的旧 definition）按 1，与打通前行为一致；
    # `or` 顺带把 0 也当无值——0 会让 plan_next 永不提议起 job（run 卡死），按 1 运行是保守可收敛的兜底。
    # env 漏注（IaC 改坏/手工建的 Lambda）时保守回 **1**：cap 的数值真源在 IaC 一处，code 不复制部署值
    # （复制 = 两处各一份、IaC 调了 cap 而这里没跟就成隐形漂移）。缺省宁可慢（串行仍收敛），不替部署方放宽闸。
    cap = int(os.environ.get("MAX_CONCURRENCY", "1"))
    max_concurrency = min(meta.max_concurrency or 1, cap)
    return meta, event_log, run_store, launcher, max_concurrency, result_store, report_store


def _run_ids_from_runs_stream(event) -> set[str]:
    """提取 kicker 要 tick 的 run_id 集。两种 event 源（kicker 同时服务两者）：

    ① runs 表 Stream（冷启动主路径）：`Records[].dynamodb.Keys.run_id`（runs 表 PK=run_id，非复合、直接取）。
    ② 直接 invoke 的 kickoff（cloud `status --wait` 接力兜底，ADR 0034）：payload `{"run_id": "..."}`——
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
    """对每个 run tick 一步；done 则聚合收尾。reconciler（events Stream）与 kicker（runs Stream）共用。

    prebuilt：本次 invoke 已装配好的组合根（run_id → `_build` 结果，**含 None**=该 run 不由云端推进器管），
    有则复用、不重装——超时路径先 `_build` 做处置再落到此处 tick 同一个 run，重装一次是纯重复工作
    （每次 `_build` 造 4 个 boto3 client + 强一致读 META + 可能的 S3 offload 正文还原）。
    """
    from gherkai_core.reconcile import tick
    from gherkai_runtime import compose  # 时钟走 compose.now_iso 单一真源（同 local/前台两宿主，格式不漂移）

    from gherkai_runtime.compose import WorkerVariantError

    prebuilt = prebuilt or {}
    for run_id in run_ids:
        # 逐 run 隔离：一个 run 的 worker revision 解析不出（兼容路径：旧 definition 撞上「默认 variant 在某引擎
        # 无映射」这种合法稳态，ADR 0038 `--set-default` 只警告不拦）不能连坐同批其它 run——events Stream 一个
        # batch 含多个 run，抛出去 = ESM 重试后整批丢弃、别的 run 事件永久丢失。该 run 记一行、留给下批。
        # 「不回落 family/模板」不受影响：拒的是换镜像，不是拒隔离失败。
        try:
            built = prebuilt[run_id] if run_id in prebuilt else _build(run_id)
        except WorkerVariantError as exc:
            print(f"{label}: run {run_id} 本批跳过——worker revision 解析失败：{exc}")
            continue
        if built is None:
            continue
        meta, event_log, run_store, launcher, mc, rstore, pstore = built
        # 判定真值由 tick 在 finalize CAS 之前落 rstore（ADR 0030 决定三写序）；聚合异常裸穿 → 本次 invocation 失败 →
        # events Stream 事件源重试本批（commit 之后再失败就没人重试了）。
        done = tick(run_id, meta, event_log, run_store, launcher, mc, now_iso=compose.now_iso(), result_store=rstore)
        if done:
            # 报告收尾走 core 唯一一份（曾在此双写、与 runtime/gherkai_runtime/detached.py 漂移风险，已合并）
            from gherkai_core.reconcile import finalize_report
            # run 级墙钟是**派生指标**（缺则报告里显「?」），取它要多读一次 RunState——强一致读、会因限流/
            # 瞬时 5xx 抛，而这一步在 finalize 的 commit point **之后**执行：commit 后的失败无人重试（ADR 0030
            # 决定三），抛出去还会让本次 invocation 失败、events Stream 本批重试耗尽后整批丢弃，连坐同批其它
            # run 的事件（同上面 WorkerVariantError 逐 run 隔离的理由）。故整段隔离、失败按缺值走
            # （ADR 0034 收尾节把 run 级墙钟划在「派生、失败隔离」那一侧）。
            try:
                duration_ms = compose.run_duration_ms(run_store.load_run_state(run_id))
            except Exception:
                duration_ms = None
            finalize_report(run_id, meta, event_log, pstore, compose.now_iso(),
                            run_duration_ms=duration_ms)
            print(f"{label}: run {run_id} done + finalized")
        else:
            print(f"{label}: run {run_id} advanced (not done)")
            _scan_overdue_timeouts(run_id, built)  # 防御性超时扫（claimed_at ②，Scheduler 双保险）
    return {"ok": True, "runs": list(run_ids)}


def handler(event, context):
    """events 表 Stream 入口（reconciler 主推进）：worker PutItem / task_exited 触发 → 对涉及 run tick 续推。"""
    return _tick_runs(_run_ids_from_stream(event), "reconciler")


def kicker_handler(event, context):
    """kicker（踢启器）入口——两个触发源：runs 表 Stream 的 **INSERT**（冷启动：submit create_run 写 definition
    即触发 → tick 起首批）+ status --wait 的直接 invoke kickoff（卡住救活：payload `{"run_id":...}`）。

    与 reconciler 共用 tick（起首批 = tick 的 CAS start 分支）——四宿主一份 tick（submit-local / kicker /
    reconciler / status 接力）。kicker **只被 runs Stream 的 INSERT 触发**（filter 在 IaC 配），故 reconciler
    之后写 runs 表（MODIFY）不触发它——无自触发放大（ADR 0034 被拒方案「runs Stream 触发 reconciler」）。
    与 reconciler 的分工：kicker 负责「让 run 动起来」（冷启动第一脚 + 卡住时补 kickoff），reconciler 负责
    「推着走」（events Stream 持续推进）。

    第三触发源（ADR 0034「job timeout」节）：EventBridge Scheduler 的到点 invoke，payload
    `{"run_id","timeout_scope"}`——先超时处置（仍 running 才 StopTask/收敛），再照常 tick
    （处置用的组合根经 prebuilt 交给 tick 复用，同一 run 只装配一次）。
    """
    timeout_scope = event.get("timeout_scope")
    rid = event.get("run_id")
    prebuilt: dict = {}
    if timeout_scope and rid:
        built = _build(rid)
        prebuilt[rid] = built  # 含 None（本 run 不该推进）——tick 侧据此也不重装
        if built is not None:
            _handle_timeout(rid, timeout_scope, built)
    return _tick_runs(_run_ids_from_runs_stream(event), "kicker", prebuilt=prebuilt)
