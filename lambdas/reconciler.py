"""reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。

events 表开 Stream（NEW_IMAGE），worker PutItem 执行事件 / 退出观察者写 task_exited → Stream 触发本 handler。
它从 Stream records 提取涉及的 run_id 集（去重），对每个 run 调 core.reconcile.tick 推进一步（读全量重放 →
project → 条件写 → plan_next → CAS 抢占起下一个 job / finalize）。tick 幂等 + CAS/HWM 条件写兜底——Stream 按
分片并发触发多个本 handler 实例、叠加 status --wait 接力，全部安全（机制三/四，真 DDB 已验）。

**cloud 组合根（Lambda 装配）**：cold-start 读 env 造 boto3 client + 三 store adapter + FargateEngine + CloudLauncher
注入纯 reconcile.tick——**是组合根注入、非 ports 内部 env-sniff 全局单例**（[0016] 禁的 GlobalConfigManager 反模式，
此处每次 handler 显式构造、无隐式全局态）。core 一行不为 cloud 改（同 local，只换注入的 EventLog/Launcher/RunStore）。

打包：本文件 + core 进 Lambda zip。env：**IaC 注入**（iac_aws_backend/stack.py 的 reconciler/kicker Function）=
RUNS_TABLE / EVENTS_TABLE / ARTIFACTS_BUCKET / CLUSTER / PREFIX / REGION / SUBNETS / SECURITY_GROUPS /
MAX_CONCURRENCY（**部署侧 per-run 并发 cap**、非真源——真源是 definition 的 `RunMeta.max_concurrency`，取
min，ADR 0034 机制四；数值真源在 IaC 一处，本文件缺省只在 env 漏注时保守回 1、不复制部署值）/ KICKER_ARN / SCHEDULER_ROLE_ARN（job timeout 到点触发器用，ADR 0034「job timeout」节）；**本文件缺省供给、IaC 不注入** = REPORT_DIR（reports）/ ASSIGN_PUBLIC_IP（ENABLED，与公有子网
配套）——要改产物落点前缀或走私有子网时才在 IaC 显式给。
"""
from __future__ import annotations

import datetime as _dt
import os


def _run_ids_from_stream(event) -> set[str]:
    """从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch 可能多条同 run。"""
    run_ids: set[str] = set()
    for rec in event.get("Records", []):
        keys = rec.get("dynamodb", {}).get("Keys", {})
        pk = keys.get("pk", {}).get("S")
        if pk and "#" in pk:
            run_ids.add(pk.rsplit("#", 1)[0])  # scope_id 不含 #（pk=run_id#scope_id 单层复合），rsplit 1 取前段稳妥
    return run_ids


# ============================================================================
# job timeout（ADR 0034「job timeout」节 cloud 档）：到点触发器 + 超时处置 + 防御扫
# ============================================================================

# StopTask reason 里的超时哨兵串：经 STOPPED 事件 detail.stoppedReason 原样出现（现成通道、零新键空间），
# exit_observer 见它 → task_exited(timed_out=True) → 归因链收敛 ERROR+timeout。exit_observer 从此处 import。
TIMEOUT_STOP_SENTINEL = "gherkai-job-timeout"

# 防御扫（claimed_at ②）的判定余量秒：Scheduler one-time schedule 是主机制（到点准时处置），扫是双保险——
# 余量让主机制先行、避免与在途的 STOPPED→exit_observer 链赛跑。非正确性参数（处置幂等、退出记录在即让路）。
_DEFENSIVE_TIMEOUT_MARGIN_S = 60.0


class EventBridgeTimeoutWatch:
    """job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个
    EventBridge Scheduler **one-time schedule**（at = now+timeout、ActionAfterCompletion=DELETE 到点自动删
    ——无常驻轮询、idle 零成本）→ 到点 invoke kicker（payload {"run_id","timeout_scope"}）走超时处置。

    schedule 名 = `names.job_timeout_schedule_prefix(prefix)` + sha1(run_id#scope_id)[:20]：确定性（重复 arm
    幂等，ConflictException 视作已武装）、合法字符集（scope_id 可含中文/路径，不能直接入名）、≤64 字符。
    名字空间前缀走命名真源 `gherkai.names`——IaC 的 IAM 资源域同源推导（ADR 0033「两层命名」，两侧硬契约）。
    best-effort：调用方（CloudLauncher）兜异常。
    """

    def __init__(self, scheduler_client, *, kicker_arn: str, role_arn: str, prefix: str) -> None:
        self._client = scheduler_client
        self._kicker_arn = kicker_arn
        self._role_arn = role_arn
        self._prefix = prefix

    def schedule_name(self, run_id: str, scope_id: str) -> str:
        import hashlib
        from gherkai import names

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
    """超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id) →
    DescribeTasks 按 overrides env SCOPE_ID 匹配（同 exit_observer 提取术）→ StopTask(reason 含哨兵) →
    STOPPED 事件 → exit_observer 记 task_exited(timed_out=True) → 既有链收敛（stop 后让观察链自然收敛=单一真源）。

    task 无踪且无退出记录（STOPPED 事件丢投等）：预算已尽仍无确认完成 → 直接 record_exit(timed_out=True)
    收敛——对位 local 接力恢复：观察链已断时直接写是唯一收敛路径（亦是「到点 invoke 顺带兜事件丢投」的落点）。
    返回处置结果串（日志/测试断言用）。
    """
    import boto3
    from core.model import Status

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
    arns = ecs.list_tasks(cluster=cluster, startedBy=run_id, desiredStatus="RUNNING").get("taskArns", [])
    target = None
    if arns:
        for t in ecs.describe_tasks(cluster=cluster, tasks=arns).get("tasks", []):
            envs = [e for co in t.get("overrides", {}).get("containerOverrides", [])
                    for e in co.get("environment", [])]
            if any(e.get("name") == "SCOPE_ID" and e.get("value") == scope_id for e in envs):
                target = t["taskArn"]
                break
    if target is not None:
        job = next((j for j in meta.jobs if j.scope_id == scope_id), None)
        budget = f"{job.timeout_s:g}" if job is not None and job.timeout_s else "?"
        ecs.stop_task(cluster=cluster, task=target,
                      reason=f"{TIMEOUT_STOP_SENTINEL}: scope exceeded {budget}s budget")
        print(f"timeout-stop: run={run_id} scope={scope_id} task={target}")
        return "stopped"
    event_log.record_exit(scope_id, None, timed_out=True)
    print(f"timeout-converge: run={run_id} scope={scope_id} task 无踪且无退出记录 → 直接记 timed_out 收敛")
    return "converged-directly"


def _scan_overdue_timeouts(run_id: str, built) -> None:
    """防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对
    RUNNING 且 now-claimed_at > timeout+余量 的 job 走同一超时处置——CreateSchedule 失败/schedule 丢失时，
    后续任何事件触发的 tick 都能补救。纯静默 job（无事件→无 tick）的主保障仍是 Scheduler 到点 invoke。"""
    from core.model import Status
    from gherkai import compose

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


def _build(run_id: str):
    """cloud 组合根：读 env 造 boto3 + 装配（RunStore/EventLog/CloudLauncher + ResultStore/ReportStore）注入。

    返回 (meta, event_log, run_store, launcher, max_concurrency, result_store, report_store)——同 local
    build_local_reconcile 的形状，供 tick + finalize 聚合。meta 从 RunStore 读回（definition）。
    **None = 本 run 不由云端推进器管**（definition 不在库 / 非 detached，见下）——两个 handler 据此整体 no-op。

    **FargateEngine 装配复用 compose.build_fargate_engines（单一真源，不重造）**——job-in 前缀 / artifact 落点 /
    task-def·container 名 / SDK env 全与同步 cloud run 路径一致、零漂移（ADR 0016：compose 是组合根逻辑、WebUI/
    Lambda 都复用、不经 cli——组合根共享层即产品本体包）。Lambda 打包带上 gherkai（不再背 argparse/render）。
    """
    import boto3
    from core.adapters.event_log import DdbEventLog
    from core.adapters.cloud_launcher import CloudLauncher
    from core.adapters.run_store.ddb import DynamoDBRunStore
    from core.adapters.result_store.s3 import S3ResultStore
    from core.adapters.report_store.s3 import S3ReportStore
    from gherkai import compose

    region = os.environ.get("REGION") or os.environ.get("AWS_REGION")
    ddb = boto3.resource("dynamodb", region_name=region)
    s3 = boto3.client("s3", region_name=region)

    runs_table = ddb.Table(os.environ["RUNS_TABLE"])
    events_table = ddb.Table(os.environ["EVENTS_TABLE"])
    bucket = os.environ["ARTIFACTS_BUCKET"]
    report_dir = os.environ.get("REPORT_DIR", "reports")
    prefix = os.environ.get("PREFIX", compose.DEFAULT_PREFIX)

    # arg_offloader 必须注入（ADR 0030 决定七「offloader 生产默认挂载、不给生产选要不要正确」）：
    # submit 侧（build_cloud_stores）把超限 docString/dataTable 正文 offload 到 S3、META 只留指针——
    # 此处不注入则 load_run_meta 的 content_ref 分支被跳过、正文静默还原成 None → worker 拿空参数跑错
    # （moto 复现）。prefix 用 REPORT_DIR 与 submit 侧同源（restore 按绝对 URI 取回、实际不依赖 prefix，
    # 但写读两侧同构造零漂移）。
    from core.adapters.run_store.arg_offload import S3StepArgumentOffloader

    offloader = S3StepArgumentOffloader(s3, bucket, compose._normalize_prefix(report_dir))
    run_store = DynamoDBRunStore(runs_table, arg_offloader=offloader)
    if not run_store.is_detached(run_id):
        # 只推进 detached run（ADR 0034 端到端 cloud 1b）：同步 `run --backend cloud` 由进程内 schedule 推进，
        # 推进器碰它就是双开推进器（抢 claim/RunTask/finalize）。kicker 那扇门由 Stream filter 挡，events 表
        # Stream 这扇门滤不了（events item 无 detached 标记）——同一判据在此判，返回 None = 全 handler no-op。
        # 判在 load_run_meta **之前**：同步 run 的每条 worker 事件都会触发本 Lambda，先判省掉强一致 META
        # 读 + offload 正文的 S3 取回，且推进器在断定「不该碰」前不读对方 definition（STATE 缺失同落此支）。
        print(f"skip: run {run_id} 非 detached（同步 cloud run 由进程内 schedule 推进）")
        return None
    meta = run_store.load_run_meta(run_id)
    if meta is None:
        return None  # definition 不存在（META 尚未落库的极端窗口 / 别的 run）——忽略
    scope_ids = [j.scope_id for j in meta.jobs]
    event_log = DdbEventLog(events_table, run_id, scope_ids)

    # ResultStore/ReportStore：prefix 传 report_dir（**不含 run_id**——S3*Store 内部自拼 {prefix}{run_id}/…，
    # 与 build_cloud_stores 一致；含 run_id 会重复）。共享一个 s3 client。
    result_store = S3ResultStore(s3, bucket, compose._normalize_prefix(report_dir))
    report_store = S3ReportStore(s3, bucket, compose._normalize_prefix(report_dir))

    # CloudLauncher 用 compose.build_fargate_engines 产的 resolver（单一真源、零漂移）。
    network = {
        "subnets": os.environ["SUBNETS"].split(","),
        "securityGroups": os.environ["SECURITY_GROUPS"].split(","),
        "assignPublicIp": os.environ.get("ASSIGN_PUBLIC_IP", "ENABLED"),
    }
    engines = compose.build_fargate_engines(
        run_id=run_id, prefix=prefix, cluster=os.environ["CLUSTER"],
        events_table=os.environ["EVENTS_TABLE"], bucket=bucket, report_dir=report_dir,
        network_config=network, region=region,
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
    # （IaC 设）：语义是**部署侧 per-run 上限**、非真源——task 跑在部署方 cluster、烧部署方账单，故部署方保留
    # 总量控制权，提交侧声明再高也钳到 cap。meta 无值（打通前落的旧 definition）按 1，与打通前行为一致；
    # `or` 顺带把 0 也当无值——0 会让 plan_next 永不提议起 job（run 卡死），按 1 跑是保守可收敛的兜底。
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
    from core.reconcile import tick
    from gherkai import compose  # 时钟走 compose.now_iso 单一真源（同 local/前台两宿主，格式不漂移）

    prebuilt = prebuilt or {}
    for run_id in run_ids:
        built = prebuilt[run_id] if run_id in prebuilt else _build(run_id)
        if built is None:
            continue
        meta, event_log, run_store, launcher, mc, rstore, pstore = built
        done = tick(run_id, meta, event_log, run_store, launcher, mc, now_iso=compose.now_iso())
        if done:
            # 收尾聚合走 core 唯一一份（曾在此双写、与 gherkai/detached.py 漂移风险，已合并）
            from core.reconcile import finalize_artifacts
            finalize_artifacts(run_id, meta, event_log, rstore, pstore, compose.now_iso())
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
