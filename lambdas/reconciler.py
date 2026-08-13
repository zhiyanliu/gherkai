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
MAX_CONCURRENCY；**本文件缺省供给、IaC 不注入** = REPORT_DIR（reports）/ ASSIGN_PUBLIC_IP（ENABLED，与公有子网
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


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build(run_id: str):
    """cloud 组合根：读 env 造 boto3 + 装配（RunStore/EventLog/CloudLauncher + ResultStore/ReportStore）注入。

    返回 (meta, event_log, run_store, launcher, max_concurrency, result_store, report_store)——同 local
    build_local_reconcile 的形状，供 tick + finalize 聚合。meta 从 RunStore 读回（definition）。

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
    meta = run_store.load_run_meta(run_id)
    if meta is None:
        return None  # definition 不存在（submit 未落库 / 别的 run）——忽略
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
        ecs=boto3.client("ecs", region_name=region), s3=s3, ddb_events_table=events_table,
    )
    launcher = CloudLauncher(compose.make_resolver(engines))
    max_concurrency = int(os.environ.get("MAX_CONCURRENCY", "1"))
    return meta, event_log, run_store, launcher, max_concurrency, result_store, report_store


def _run_ids_from_runs_stream(event) -> set[str]:
    """提取 kicker 要 tick 的 run_id 集。两种 event 源（kicker 同时服务两者）：

    ① runs 表 Stream（冷启动主路径）：`Records[].dynamodb.Keys.run_id`（runs 表 PK=run_id，非复合、直接取）。
    ② 直接 invoke 的 kickoff（cloud `status --wait` 接力兜底，ADR 0034）：payload `{"run_id": "..."}`——
       Stream 丢投卡 pending 时 status --wait 绕过 Stream 直接 invoke kicker，故须认此格式（否则空转、救不了）。
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


def _tick_runs(run_ids: set[str], label: str) -> dict:
    """对每个 run tick 一步；done 则聚合收尾。reconciler（events Stream）与 kicker（runs Stream）共用。"""
    from core.reconcile import tick

    for run_id in run_ids:
        built = _build(run_id)
        if built is None:
            continue
        meta, event_log, run_store, launcher, mc, rstore, pstore = built
        done = tick(run_id, meta, event_log, run_store, launcher, mc, now_iso=_now_iso())
        if done:
            # 收尾聚合走 core 唯一一份（曾在此双写、与 cli/detached.py 漂移风险，已合并）
            from core.reconcile import finalize_artifacts
            finalize_artifacts(run_id, meta, event_log, rstore, pstore, _now_iso())
            print(f"{label}: run {run_id} done + finalized")
        else:
            print(f"{label}: run {run_id} advanced (not done)")
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
    """
    return _tick_runs(_run_ids_from_runs_stream(event), "kicker")
