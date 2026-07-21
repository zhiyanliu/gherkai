"""gherkai：执行核心库的命令行皮（ADR 0016）。

皮做四件事：解析参数 → 读 feature（compose）→ 注入引擎 resolver 跑 schedule → 渲染结果。
逻辑全在 core；这里只接线 + 表层 IO。WebUI 是另一张皮，复用 compose、不经本文件。

跑（开发期）：cd cli && uv run python -m cli <feature> [--default-engine novaact] [...]
真跑会烧 AWS 钱（模型调用 + AgentCore 会话）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from core.model import Event, RunMeta, Status
from core.parse import FeatureParseError
from core.persist import RunPersistence
from core.scope import PlanConfig, PlanError, plan
from core.schedule import ScheduleOpts, schedule

from cli import compose, render


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gherkai",
        description="解析 .feature → 分组 scope → 调度两个 AI 引擎 → 汇总运行结果（会烧真 AWS 钱）。",
    )
    sub = p.add_subparsers(dest="command")

    run = sub.add_parser("run", help="跑一个或多个 .feature")
    run.add_argument("features", nargs="+", type=Path, help="一个或多个 .feature 路径")
    run.add_argument(
        "--default-engine", default="novaact",
        help="未标 @engine 的 scope 用的默认引擎（默认 novaact）；标了 @engine: 的 scope 按 tag 走、不受此影响",
    )
    run.add_argument(
        "--assertion-votes", type=int, default=1, metavar="N",
        help="AI 断言（Then）投票次数（默认 1=单次判定）；调高（如 3/5）启用抖动检测：跑 N 次取多数票",
    )
    run.add_argument(
        "--max-concurrency", type=int, default=1,
        help="同时在跑的 worker 上限（默认 1，护真实 AWS 成本/配额）",
    )
    run.add_argument(
        "--timeout", type=float, default=300.0,
        help="单 job 墙钟超时秒（默认 300；<=0 表示不超时）",
    )
    run.add_argument(
        "--grace", type=float, default=None,
        help="停止后等 worker 优雅退出的宽限秒（默认按本 run 引擎推导：Nova≈act_timeout+余量、"
             "确保 grace≥单 act 时长否则会话泄漏，ADR 0024；显式给过小值会被拒退 2）",
    )
    run.add_argument("--fail-fast", action="store_true", help="任一 job 崩则中止整批")
    run.add_argument("--json", action="store_true", help="只输出机器可读 JSON（不打进度/文本汇总）")
    run.add_argument("--quiet", action="store_true", help="不打逐事件进度（仍打文本汇总）")
    # RunReport 是 run 的应得产物：默认总归集（manifest.json + index.html）到 <report-dir>/<run_id>/。
    run.add_argument(
        "--report-dir", default="reports", metavar="DIR",
        help="归集报告落点（默认 reports/；每次 run 落 DIR/<run_id>/）",
    )
    run.add_argument(
        "--no-report", action="store_true",
        help="跳过报告归集（CI 只看退出码/JSON、或调试时不想落盘的逃生舱）",
    )
    # backend 选择（ADR 0016「cli backend 选择」/ 0030 决定七）：local=文件落盘（默认）；cloud=DDB/S3。
    # 仅 run 加（plan 纯本地不落库、不连 AWS，不加）。cloud 一次换齐三层（RunStore→DDB、Result/Report→S3）。
    run.add_argument(
        "--backend", choices=["local", "cloud"], default="local",
        help="落库后端：local=文件落 --report-dir（默认）；cloud=状态落 DynamoDB、结果与报告落 S3",
    )
    run.add_argument(
        "--prefix", default=None, metavar="P",
        help=f"[--backend cloud] 资源名前缀（默认 {compose.DEFAULT_PREFIX!r}）：批量决定表/桶/cluster/task-def 默认名；"
             "须与 CDK（iac_aws_backend）部署用的 prefix 一致。多环境切换（prod-/stage-）用它。兜底 AWS_RESOURCE_PREFIX",
    )
    run.add_argument(
        "--ddb-table", default=None, metavar="NAME",
        help="[--backend cloud] RunStore DynamoDB 表名（覆盖 prefix 默认 {prefix}runs）；兜底 AWS_DDB_TABLE",
    )
    run.add_argument(
        "--s3-bucket", default=None, metavar="NAME",
        help="[--backend cloud] S3 桶名（覆盖 prefix 默认 {prefix}artifacts）；兜底 AWS_S3_BUCKET",
    )
    run.add_argument(
        "--events-table", default=None, metavar="NAME",
        help="[--backend cloud] events DynamoDB 表名（覆盖 prefix 默认 {prefix}events）；worker PutItem 目标",
    )
    run.add_argument(
        "--cluster", default=None, metavar="NAME",
        help="[--backend cloud] ECS cluster 名（覆盖 prefix 默认 {prefix}cluster）",
    )
    run.add_argument(
        "--subnet", action="append", default=None, metavar="ID",
        help="[--backend cloud] Fargate 子网 ID（可多次；不给则读 SSM /{prefix}backend/subnets——CDK 写的生成 ID）",
    )
    run.add_argument(
        "--security-group", action="append", default=None, metavar="ID",
        help="[--backend cloud] Fargate 安全组 ID（可多次；不给则读 SSM /{prefix}backend/security-groups）",
    )
    run.add_argument(
        "--region", default=None, metavar="R",
        help="AWS region（解析链 --region > AWS_REGION > AWS_DEFAULT_REGION > profile config；喂 store + worker）",
    )
    run.add_argument(
        "--profile", default=None, metavar="P",
        help="AWS profile（--profile > AWS_PROFILE）；喂 store + subprocess worker（其 region 字段也作 --region 兜底）",
    )

    # plan 预检（dry-run）：纯本地解析 + 分组，不起 worker、不连 AWS、不烧钱。
    pl = sub.add_parser("plan", help="预检 .feature：看 scope/job 分组 + 校验配置，不真跑（不烧钱）")
    pl.add_argument("features", nargs="+", type=Path, help="一个或多个 .feature 路径")
    pl.add_argument(
        "--default-engine", default="novaact",
        help="未标 @engine 的 scope 用的默认引擎（默认 novaact）——影响分组结果，故预检也可设",
    )
    pl.add_argument(
        "--assertion-votes", type=int, default=1, metavar="N",
        help="AI 断言投票次数（默认 1）——影响分组产出的投票次数，故预检也可设",
    )
    pl.add_argument("--json", action="store_true", help="输出机器可读 JSON（scope/job 分组）")

    # ---- 无状态跑批（ADR 0034）：submit 提交完就走 / status 轮询收集 ----
    # local 档：submit setsid fork 一个 per-run 进程跑 reconcile loop（本机推进，无需常驻），CLI 立即退出。
    sm = sub.add_parser("submit", help="[无状态跑批] 提交一批 .feature 到后台跑、立即返回 run_id（提交完就走）")
    sm.add_argument("features", nargs="+", type=Path, help="一个或多个 .feature 路径")
    sm.add_argument("--default-engine", default="novaact", help="未标 @engine 的 scope 用的默认引擎")
    sm.add_argument("--assertion-votes", type=int, default=1, metavar="N", help="AI 断言投票次数（默认 1）")
    sm.add_argument("--max-concurrency", type=int, default=1, help="同时在跑的 worker 上限（默认 1）")
    sm.add_argument("--report-dir", default="reports", metavar="DIR", help="归集报告落点（默认 reports/）")
    sm.add_argument("--region", default=None, metavar="R", help="AWS region（喂 worker）")
    sm.add_argument("--profile", default=None, metavar="P", help="AWS profile（喂 subprocess worker）")
    # backend：local（默认，per-run 进程本机推进）/ cloud（Fargate + 云端 Lambda 事件驱动链推进，ADR 0034）。
    sm.add_argument("--backend", choices=["local", "cloud"], default="local",
                    help="local=本机 per-run 进程推进（默认）；cloud=Fargate + 云端 Lambda 事件驱动链推进（提交完真关机也跑完）")
    sm.add_argument("--prefix", default=None, metavar="P", help="[cloud] 资源名前缀（默认 gherkai-；须与 CDK 一致）")
    sm.add_argument("--ddb-table", default=None, metavar="NAME", help="[cloud] RunStore DDB 表名")
    sm.add_argument("--s3-bucket", default=None, metavar="NAME", help="[cloud] S3 桶名")
    sm.add_argument("--events-table", default=None, metavar="NAME", help="[cloud] events DDB 表名")
    sm.add_argument("--cluster", default=None, metavar="NAME", help="[cloud] ECS cluster 名")
    sm.add_argument("--subnet", action="append", default=None, metavar="ID", help="[cloud] Fargate 子网 ID")
    sm.add_argument("--security-group", action="append", default=None, metavar="ID", help="[cloud] Fargate 安全组 ID")

    st = sub.add_parser("status", help="[无状态跑批] 查一个 run 的进度/结果（--wait 轮询到完成）")
    st.add_argument("run_id", help="submit 返回的 run_id")
    st.add_argument("--backend", choices=["local", "cloud"], default="local", help="须与 submit 一致")
    st.add_argument("--report-dir", default="reports", metavar="DIR", help="[local] run 落点（须与 submit 一致）")
    st.add_argument("--wait", action="store_true", help="[local] 轮询到 run 达终态再返回（接力推进）")
    st.add_argument("--max-concurrency", type=int, default=1, help="[local --wait] 接力推进并发上限")
    st.add_argument("--json", action="store_true", help="输出机器可读 JSON（RunState）")
    st.add_argument("--prefix", default=None, metavar="P", help="[cloud] 资源名前缀（读 DDB RunState）")
    st.add_argument("--ddb-table", default=None, metavar="NAME", help="[cloud] RunStore DDB 表名")
    st.add_argument("--region", default=None, metavar="R")
    st.add_argument("--profile", default=None, metavar="P")

    # _reconcile：per-run 进程入口（submit setsid fork 它，非用户直接调）。跑 reconcile loop 到全 done。
    rc = sub.add_parser("_reconcile", help=argparse.SUPPRESS)
    rc.add_argument("run_id")
    rc.add_argument("--report-dir", default="reports")
    rc.add_argument("--max-concurrency", type=int, default=1)
    rc.add_argument("--region", default=None)
    rc.add_argument("--profile", default=None)

    sub.add_parser("list-engines", help="列出可用引擎及其 spawn 命令")
    return p


def _cmd_list_engines(repo: Path) -> int:
    engines = compose.build_engines(repo)
    print(f"可用引擎（仓库根 {repo}）：")
    for name in sorted(engines):
        eng = engines[name]
        cmd = " ".join(getattr(eng, "cmd", []))  # SubprocessEngine 持有 cmd
        print(f"  - {name}: {cmd}")
    return 0


def _load_and_plan(args, repo: Path) -> "list | int":
    """plan 与 run 的共享前置装配：votes 校验 → 读 feature → plan。

    成功返回 `Job[]`；任一前置失败返回**退出码 2**（配置矛盾/读不到/语法错，均"没开跑就被拒"，
    对齐 cli/README 退出码分层）。_cmd_plan 与 _cmd_run 都调它，避免两份手抄的前置逻辑漂移（N10）。
    """
    # 0) 校验：assertion_votes 必须 ≥1。否则 worker 跑 0 次 AI 断言——votes=0 全判失败（假阴性）、
    #    votes<0 更危险：0 > 负数/2 = True → **零 AI 调用却全绿**（假阳性）。入口拦截，不让坏值流进 worker。
    if args.assertion_votes < 1:
        _progress(f"--assertion-votes 必须 ≥ 1（收到 {args.assertion_votes}）：投票次数 <1 会让 AI 断言不被执行")
        return 2
    # 1) 读 feature（组合根的事，core 不碰 FS）→ FeatureSource[]
    try:
        features = [compose.load_feature(f, repo) for f in args.features]
    except FileNotFoundError as e:
        _progress(f"读 feature 失败：{e}")
        return 2
    # 2) plan：.feature → Job[]（uri 互异/engine 冲突等违约 → PlanError；gherkin 语法错 → FeatureParseError）
    try:
        return plan(features, PlanConfig(
            default_engine=args.default_engine,
            default_assertion_votes=args.assertion_votes,
        ))
    except PlanError as e:
        _progress(f"plan 失败（配置矛盾，拒绝运行）：{e}")
        return 2
    except FeatureParseError as e:
        _progress(f"feature 语法错误（gherkin 解析失败，含行:列）：\n{e}")
        return 2


def _cmd_plan(args, repo: Path) -> int:
    """plan 预检：读 feature → plan → 渲染 scope/job 分组。**不起 worker、不连 AWS、不烧钱**。

    与 _cmd_run 共用 `_load_and_plan`（votes 校验 + load_feature + plan），但到此为止——
    省钱验证 feature 写法、看分组、暴露 PlanError。退出码与 run 一致（0 ok / 2 配置错）。
    """
    jobs = _load_and_plan(args, repo)
    if isinstance(jobs, int):  # 前置失败 → 退出码
        return jobs

    # 核心产出 → stdout（与 run 的输出契约一致：--json 单文档 / 否则人看文本）
    if args.json:
        print(json.dumps(render.plan_to_dict(jobs, args.default_engine), ensure_ascii=False, indent=2))
    else:
        print(render.render_plan_text(jobs, args.default_engine))
    return 0


def _progress(*args, **kwargs) -> None:
    """进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。

    这样 `cli run … --json > r.json` 拿到纯净 JSON、`cli run … > summary.txt` 拿到纯净文本汇总，
    进度（plan/event/run_id/RunReport 落点）照样在终端可见、不污染被重定向的主输出。

    **不上色（= 终端默认前景色）是有意约定**：默认色专属 cli main/core 的输出（含 `[core …:event]`），
    与 worker 透传行的调色板物理不相交——worker 调色板有意排除白/默认色（见 subprocess_engine._ANSI_COLORS），
    故并发跑批时「core 说的」恒默认色、「worker 透传的」恒有色，一眼可分。给 core 输出加色前先想清这条约定。
    """
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)


def _prune_empty_dirs(root: Path) -> None:
    """自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。

    非空目录（残留产物/文件）自然保留（rmdir 抛 OSError → 吞掉），与 worker「上传失败保留本地」护栏自洽。
    root 不存在则 no-op。用于 cloud 模式清 worker 用完的本地产物暂存区空壳。
    """
    if not root.exists():
        return
    for d, _subdirs, _files in os.walk(root, topdown=False):
        try:
            os.rmdir(d)  # 只删空目录；非空 → OSError → 吞掉、保留
        except OSError:
            pass


def _is_botocore_error(exc: BaseException) -> bool:
    """是否 botocore 异常（云端不可达/权限/凭证/region 等）。

    惰性 import botocore（cli 主依赖不含 boto3，顶层 import 会在纯 local 环境炸；且只在 --backend cloud
    路径才会调到这里）。缺 botocore（不该发生，能走到 cloud 就装了 boto3）时保守返回 False。
    """
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:  # pragma: no cover
        return False
    return isinstance(exc, (BotoCoreError, ClientError))


def _cmd_submit(args, repo: Path) -> int:
    """[无状态跑批] 提交完就走（ADR 0034）：plan → 写 RunMeta+全 pending → 起首轮推进 → 打印 run_id → 立即退出。

    - **local**：setsid fork per-run 进程跑 reconcile loop 本机推进（无需常驻服务/云）；崩了 status --wait 接力。
    - **cloud**：create_run 到 DDB + 首批 RunTask 起 Fargate task（踢首轮）→ 之后云端 Lambda 事件驱动链推进
      （ECS STOPPED→退出观察者→task_exited→Stream→reconciler），**提交完真关机也跑完**。CLI 不留本机进程。
    退出码 = 提交成功与否（非 run 判定；判定由 status 查）。
    """
    jobs = _load_and_plan(args, repo)
    if isinstance(jobs, int):
        return jobs
    _progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")

    run_id = compose.new_run_id()
    run_meta = RunMeta(run_id=run_id, created_at=compose.now_iso(), jobs=tuple(jobs))
    from core.model import JobState, RunState
    initial = RunState(
        run_id=run_id, status=Status.PENDING,
        jobs={j.scope_id: JobState(scope_id=j.scope_id, status=Status.PENDING) for j in jobs},
        started_at=compose.now_iso(), high_water_mark=0,
    )

    if args.backend == "cloud":
        return _submit_cloud(args, repo, run_id, run_meta, initial)
    return _submit_local(args, repo, run_id, run_meta, initial)


def _submit_local(args, repo: Path, run_id: str, run_meta, initial) -> int:
    """local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。"""
    import subprocess as _sp
    from core.adapters.event_log import SqliteEventLog

    report_root = Path(args.report_dir).resolve()
    run_store, _rs, _rp, _mk = compose.build_local_stores(report_dir=str(report_root))
    run_store.create_run(run_meta, initial)
    SqliteEventLog(report_root / run_id / "events.db")  # 建库（schema），per-run/status 共用

    # setsid fork per-run 进程（start_new_session=True = 脱离 CLI 进程组，CLI 退出不带走它，ADR 0034）。
    cmd = [sys.executable, "-m", "cli", "_reconcile", run_id,
           "--report-dir", str(report_root), "--max-concurrency", str(args.max_concurrency)]
    if args.region:
        cmd += ["--region", args.region]
    if args.profile:
        cmd += ["--profile", args.profile]
    _sp.Popen(cmd, cwd=str(repo), start_new_session=True,
              stdin=_sp.DEVNULL, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    _progress(f"已提交（本机后台推进中）。查进度：gherkai status {run_id} --report-dir {args.report_dir}")
    print(run_id)
    return 0


def _submit_cloud(args, repo: Path, run_id: str, run_meta, initial) -> int:
    """cloud submit：create_run 到 DDB + 首批 RunTask 踢首轮 → 云端 Lambda 事件驱动链接管推进。

    首轮踢一脚（起首批 task）是必需的——纯事件驱动链的冷启动：无 events / 无 STOPPED，Stream/EventBridge
    都不会触发第一次 reconciler。故 submit 调 reconcile.tick 一次（CAS 抢占起首批 ≤max_concurrency 个 task）；
    之后首批 task 产 events → Stream → reconciler Lambda 接管（补起后续 / finalize）。CLI 起完首批即退、不留进程。
    """
    resolved_profile = args.profile or os.environ.get("AWS_PROFILE")
    resolved_region = compose.resolve_region(args.region, resolved_profile)
    prefix = args.prefix or os.environ.get("AWS_RESOURCE_PREFIX") or compose.DEFAULT_PREFIX
    events_table = args.events_table or compose.default_name(prefix, compose._BASE_EVENTS_TABLE)
    cluster = args.cluster or compose.default_name(prefix, compose._BASE_CLUSTER)
    bucket = args.s3_bucket or os.environ.get("AWS_S3_BUCKET") or compose.default_name(prefix, compose._BASE_BUCKET)
    table = args.ddb_table or os.environ.get("AWS_DDB_TABLE") or compose.default_name(prefix, compose._BASE_RUNS_TABLE)

    # preflight（events 表/cluster/桶/runs 表）——配置错在提交前暴露、退 2。
    try:
        err = compose.preflight_cloud_resources(
            prefix=prefix, events_table=events_table, bucket=bucket, cluster=cluster,
            runs_table=table, region=resolved_region, profile=resolved_profile,
        )
    except ImportError as e:
        _progress(f"submit --backend cloud 需要 boto3：{e}")
        return 2
    if err:
        _progress(err)
        return 2
    try:
        network_config = compose.resolve_network(
            prefix=prefix, subnets=args.subnet, security_groups=args.security_group,
            region=resolved_region, profile=resolved_profile,
        )
    except Exception as e:
        if _is_botocore_error(e):
            _progress(f"submit --backend cloud 读 subnet/sg SSM 失败：{e}")
            return 2
        raise

    # 装配：DDB RunStore（create_run）+ DdbEventLog + CloudLauncher（build_fargate_engines 单一真源）。
    from core.adapters.event_log import DdbEventLog
    from core.adapters.cloud_launcher import CloudLauncher
    from core.reconcile import tick

    run_store, _rs, _rp, _mk = compose.build_cloud_stores(
        table=table, bucket=bucket, prefix=args.report_dir,
        region=resolved_region, profile=resolved_profile,
    )
    try:
        run_store.create_run(run_meta, initial)
    except Exception as e:
        if _is_botocore_error(e):
            _progress(f"submit --backend cloud 云端不可达（表/桶/凭证/region）：{e}")
            return 2
        raise

    events_tbl = compose._make_ddb_table(events_table, region=resolved_region, profile=resolved_profile)
    scope_ids = [j.scope_id for j in run_meta.jobs]
    event_log = DdbEventLog(events_tbl, run_id, scope_ids)
    engines = compose.build_fargate_engines(
        run_id=run_id, prefix=prefix, cluster=cluster, events_table=events_table, bucket=bucket,
        report_dir=args.report_dir, network_config=network_config, region=resolved_region,
    )
    launcher = CloudLauncher(compose.make_resolver(engines))
    # 踢首轮：起首批 ≤max_concurrency 个 task（CAS）。之后云端 Lambda 链接管（首批 task 产 events → Stream → reconciler）。
    tick(run_id, run_meta, event_log, run_store, launcher, args.max_concurrency, now_iso=compose.now_iso())

    _progress(f"已提交到云端（首批 task 已起，云端 Lambda 链推进中，可关机）。查进度：gherkai status {run_id} --backend cloud --prefix {prefix}")
    print(run_id)
    return 0


def _cmd_status(args, repo: Path) -> int:
    """[无状态跑批] 查 run 进度/结果。

    - local：读文件 RunState；--wait 则接力 tick 到终态（三触发源之一，per-run 崩了人来查也能续）。
    - cloud：读 DDB RunState（云端 Lambda 链推进，status 只读、不接力——推进不依赖本机）。
    """
    from cli import detached

    if args.backend == "cloud":
        return _status_cloud(args)

    report_root = Path(args.report_dir).resolve()
    run_store, _rs, _rp, _mk = compose.build_local_stores(report_dir=str(report_root))

    if args.wait:
        # 接力推进：per-run 进程崩了/慢了，人来查即自己 tick 到终态（状态全持久、tick 幂等，断点续）。
        meta, log, store, launcher, mc, rstore, pstore = detached.build_local_reconcile(
            repo, str(report_root), args.run_id, args.max_concurrency,
            region=args.region, profile=args.profile,
        )
        detached.run_reconcile_loop(args.run_id, meta, log, store, launcher, mc,
                                    poll_interval_s=0.5, now_iso_fn=compose.now_iso,
                                    result_store=rstore, report_store=pstore)

    state = run_store.load_run_state(args.run_id)
    if state is None:
        _progress(f"未找到 run：{args.run_id}（--report-dir 是否与 submit 一致？）")
        return 2
    if args.json:
        from core.serialize import run_state_to_dict
        print(json.dumps(run_state_to_dict(state), ensure_ascii=False, indent=2))
    else:
        print(detached.render_run_state(state))
    # 退出码：达终态按判定（PASSED→0 / 其余→1）；未达终态（还在跑，非 --wait）→ 0（提交/查询本身成功）
    if state.status == Status.PASSED:
        return 0
    if state.status in (Status.PENDING, Status.RUNNING):
        return 0
    return 1


def _status_cloud(args) -> int:
    """cloud status：读 DDB RunState 渲染（云端 Lambda 链推进，只读、不接力）。"""
    from cli import detached

    resolved_profile = args.profile or os.environ.get("AWS_PROFILE")
    resolved_region = compose.resolve_region(args.region, resolved_profile)
    prefix = args.prefix or os.environ.get("AWS_RESOURCE_PREFIX") or compose.DEFAULT_PREFIX
    table = args.ddb_table or os.environ.get("AWS_DDB_TABLE") or compose.default_name(prefix, compose._BASE_RUNS_TABLE)

    from core.adapters.run_store.ddb import DynamoDBRunStore
    run_store = DynamoDBRunStore(compose._make_ddb_table(table, region=resolved_region, profile=resolved_profile))
    try:
        state = run_store.load_run_state(args.run_id)
    except Exception as e:
        if _is_botocore_error(e):
            _progress(f"status --backend cloud 云端不可达（表/凭证/region）：{e}")
            return 2
        raise
    if state is None:
        _progress(f"未找到 run：{args.run_id}（--prefix/--ddb-table 是否与 submit 一致？）")
        return 2
    if args.json:
        from core.serialize import run_state_to_dict
        print(json.dumps(run_state_to_dict(state), ensure_ascii=False, indent=2))
    else:
        print(detached.render_run_state(state))
    if state.status == Status.PASSED:
        return 0
    if state.status in (Status.PENDING, Status.RUNNING):
        return 0
    return 1


def _cmd_reconcile(args, repo: Path) -> int:
    """per-run 进程入口（submit setsid fork 它，非用户直接调）：跑 reconcile loop 到全 done 自退（ADR 0034）。"""
    from cli import detached

    report_root = Path(args.report_dir).resolve()
    meta, log, store, launcher, mc, rstore, pstore = detached.build_local_reconcile(
        repo, str(report_root), args.run_id, args.max_concurrency,
        region=args.region, profile=args.profile,
    )
    detached.run_reconcile_loop(args.run_id, meta, log, store, launcher, mc,
                                poll_interval_s=0.5, now_iso_fn=compose.now_iso,
                                result_store=rstore, report_store=pstore)
    return 0


def _cmd_run(args, repo: Path) -> int:
    use_json = args.json

    # 0/1/2) votes 校验 + 读 feature + plan（与 _cmd_plan 共享；前置失败返回退出码 2，见 _load_and_plan）
    jobs = _load_and_plan(args, repo)
    if isinstance(jobs, int):
        return jobs

    # 进度走 stderr（不再受 --json 开关；stdout 始终只放核心产出）。--quiet 仍可静音逐事件。
    _progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")
    for j in jobs:
        _progress(f"  - scope={j.scope_id!r} engine={j.engine} scenarios={len(j.scenarios)}")

    # 3) 组合根：构造 RunMeta（definition：生成 run_id + now + plan 产出的 jobs，先于跑批，ADR 0016/0027）
    #    + 注入具体引擎 resolver（core 引擎无关）
    run_id = compose.new_run_id()
    run_meta = RunMeta(run_id=run_id, created_at=compose.now_iso(), jobs=tuple(jobs))
    do_report = not args.no_report  # RunReport 默认生成；--no-report 跳过（逃生舱）
    # 归集时让两个引擎的产物都落到 run 专属持久目录（否则用 SDK 默认：Nova 临时目录会被清理、Midscene
    # 落相对 worker cwd 的固定 midscene_run/ 每 run 覆盖）。两引擎对称落 reports/<run_id>/ 下（ADR 0027）。
    # **必须传绝对路径**：worker 是另起的子进程、cwd 与 cli 不同（cli=cli/，worker=engines/*/），相对路径
    # 会被两进程各自的 cwd 解析到不同位置 → 产物落错地方、且 worker 产出的 file://<相对> 是坏 URI。
    report_root = Path(args.report_dir).resolve()
    nova_logs_dir = (report_root / run_id / "nova-trajectories") if do_report else None
    midscene_run_dir = (report_root / run_id / "midscene-run") if do_report else None
    # artifact_s3 = 产物 S3 上传落点，仅 local（subprocess）路径经 build_engines 注入给 worker（ADR 0029）：
    # 默认 None（local / --no-report → worker 报 file://、不上传）。**cloud（Fargate）路径不走这里**——其产物落点
    # 由 build_fargate_engines 内部按 (bucket, <report_dir>/<run_id>/) 自算并注入 FargateEngine（见下 resolver 分流）。
    artifact_s3: tuple[str, str] | None = None
    cloud_fargate: dict | None = None  # cloud 分支置值（ADR 0033）：Fargate 执行配置，供 build_fargate_engines；None＝走 subprocess
    # region/profile 解析（ADR 0016 决策 C——region 与 profile 是「正确的非对称」）：
    # - profile：--profile > AWS_PROFILE。仅 subprocess worker 注入（继承本机 ~/.aws、profile 合法）；
    #   **Fargate 绝不注入**（容器无 ~/.aws、用 task role，注入不存在的 profile 名会 ProfileNotFound 盖过 task role）。
    # - region：--region > AWS_REGION > AWS_DEFAULT_REGION > profile config（compose.resolve_region 落实成**具体字符串**）。
    #   profile config 回落是关键：AgentCore validate_region 不吃 profile config、要显式 region 字符串，不落实则 profile-only
    #   下 worker InvalidRegionError 崩。落实后 subprocess env + FargateEngine overrides + store 三处同源、消除分叉
    #   （cloud ⇒ FargateEngine 执行、见下 3a/build_fargate_engines）。
    # 均可为 None＝真无（fail-loud、不硬编码 east，对齐 store 宽容边界）。
    resolved_profile = args.profile or os.environ.get("AWS_PROFILE")
    resolved_region = compose.resolve_region(args.region, resolved_profile)

    # cloud 资源名前缀（ADR 0033 两层命名）：prefix（--prefix > AWS_RESOURCE_PREFIX > 默认 gherkai-）批量推导默认名，
    # 单资源 --xxx 覆盖。须与 CDK（iac_aws_backend）部署用的 prefix 一致（preflight 探活时点名 prefix 引导排错）。
    prefix = args.prefix or os.environ.get("AWS_RESOURCE_PREFIX") or compose.DEFAULT_PREFIX

    # 3a) 执行轴（ADR 0016 决策 A / 0033）：--backend cloud ⇒ Fargate 执行，**与 report 正交**——`--no-report` 只关
    #     不落库、不碰「在哪执行」。故 cloud 的 Fargate 执行配置解析在 do_report **之外**：`--no-report --backend cloud`
    #     仍在 Fargate 跑，只是不生成 report。cloud_fargate 置值 = 下面 resolver 用 FargateEngine（否则 SubprocessEngine）。
    if args.backend == "cloud":
        events_table = args.events_table or compose.default_name(prefix, compose._BASE_EVENTS_TABLE)
        cluster = args.cluster or compose.default_name(prefix, compose._BASE_CLUSTER)
        bucket = args.s3_bucket or os.environ.get("AWS_S3_BUCKET") or compose.default_name(prefix, compose._BASE_BUCKET)
        # preflight 执行必需资源（events 表 + cluster；桶=job-in/产物上传也执行需要）——fail-fast 点名 prefix。
        # runs 表仅落库需要，故只在 do_report 时探（见 3b begin 探活）；此处不探 runs 表（--no-report 下用不到）。
        try:
            err = compose.preflight_cloud_resources(
                prefix=prefix, events_table=events_table, bucket=bucket, cluster=cluster,
                runs_table=(args.ddb_table or os.environ.get("AWS_DDB_TABLE") or compose.default_name(prefix, compose._BASE_RUNS_TABLE))
                            if do_report else None,  # runs 表仅 do_report 探（落库需要）
                region=resolved_region, profile=resolved_profile,
            )
        except ImportError as e:
            _progress(f"--backend cloud 需要 boto3：{e}")
            return 2
        if err:
            _progress(err)
            return 2
        # network 解析（subnet/sg：--xxx 覆盖 or 读 SSM）——需 prefix + region/profile 都已定。
        try:
            network_config = compose.resolve_network(
                prefix=prefix, subnets=args.subnet, security_groups=args.security_group,
                region=resolved_region, profile=resolved_profile,
            )
        except Exception as e:
            if _is_botocore_error(e):
                _progress(f"--backend cloud 读 subnet/sg SSM 失败（/{prefix}backend/*——CDK 未写或无权限？）：{e}")
                return 2
            raise
        cloud_fargate = {"prefix": prefix, "cluster": cluster, "events_table": events_table,
                         "bucket": bucket, "network_config": network_config}

    # 3b) 落库轴（ADR 0030）：组合根按 --backend 注入 local/cloud 两套 store adapter，RunPersistence 负责「随进度落库」
    #     的统一编排（commit-point 写序 / RUNNING 中间态 / 按 scope_id 增量刷）。--no-report 则不落库（逃生舱）：
    #     persistence=None，schedule 不接回调、零落盘——**但执行仍按 3a 的 backend 走**（report 与执行正交）。
    #     **need_cloud gated**（ADR 0030 决定七）：云端 store 校验/import/异常只在 do_report and backend==cloud 时生效。
    need_cloud = do_report and args.backend == "cloud"
    persistence: RunPersistence | None = None
    make_artifacts = None  # compose 返回的 artifacts 落点组装器（按 backend URI 化）
    if do_report:
        if args.backend == "cloud":
            # cloud store 表/桶：table 走 prefix 推导或 --ddb-table 覆盖；bucket 复用 3a 已解析的（cloud_fargate 必已置值，
            # 因 do_report+cloud ⊆ backend==cloud）——不依赖 3a 的局部 `bucket` 还在作用域（消 possibly-unbound）。
            table = args.ddb_table or os.environ.get("AWS_DDB_TABLE") or compose.default_name(prefix, compose._BASE_RUNS_TABLE)
            assert cloud_fargate is not None  # backend==cloud → 3a 已置值（收窄类型）
            cloud_bucket = cloud_fargate["bucket"]
            try:
                # cloud 装配下沉 compose（可复用）；import boto3 惰性在 _make_* 钩子里，缺 boto3 抛 ImportError
                run_store, result_store, report_store, make_artifacts = compose.build_cloud_stores(
                    table=table, bucket=cloud_bucket, prefix=args.report_dir,
                    region=resolved_region, profile=resolved_profile,
                )
            except ImportError as e:
                _progress(f"--backend cloud 需要 boto3：{e}")
                return 2
        else:
            run_store, result_store, report_store, make_artifacts = compose.build_local_stores(report_dir=args.report_dir)
        persistence = RunPersistence(
            run_id, run_store=run_store, result_store=result_store, report_store=report_store,
        )
        # begin 必在 schedule 之前：先 preflight 探活（云端探表/桶失败即抛）再写 definition + 初始全 pending 态
        # （满足「提交即返回 runId」，ADR 0027）。cloud 探活失败 → 下面 gated except 归到退 2。
        try:
            persistence.begin(run_meta, started_at=compose.now_iso())
        except Exception as e:
            if need_cloud and _is_botocore_error(e):
                _progress(f"--backend cloud 云端不可达（表/桶不存在或无权限/凭证·region 缺）：{e}")
                return 2
            raise

    # 组合根注入引擎 resolver（延后到此：需 run_id + store 装配后）。
    # **决策 A 落到 CLI（ADR 0016/0033）**：cloud ⇒ FargateEngine（云执行，产物落点内部自算）；否则 SubprocessEngine（本地，注入 artifact_s3）。
    # cloud_fargate 在 3a 的 `backend=='cloud'` 分支**无条件置值**（与 do_report 正交，report⊥执行）——故
    # `--backend cloud --no-report` 仍走 Fargate（cloud_fargate 非 None），只是不落库、不生成 report。
    # `--no-report` 的逃生舱只作用于 store 轴（persistence=None、不构造三个 store），绝不改执行环境（见 3a 注释 + ADR 0016 决策 A）。
    if cloud_fargate is not None:
        engines = compose.build_fargate_engines(
            run_id=run_id, prefix=cloud_fargate["prefix"], cluster=cloud_fargate["cluster"],
            events_table=cloud_fargate["events_table"], bucket=cloud_fargate["bucket"],
            report_dir=args.report_dir, network_config=cloud_fargate["network_config"],
            region=resolved_region, profile=resolved_profile,
        )
    else:
        engines = compose.build_engines(
            repo, nova_logs_dir=nova_logs_dir, midscene_run_dir=midscene_run_dir, artifact_s3=artifact_s3,
            region=resolved_region, profile=resolved_profile,
        )
    resolver = compose.make_resolver(engines)

    # 4) sink：逐事件进度 → stderr（诊断；--quiet 静音。不再受 --json 影响——走 stderr 不污染 stdout 数据）
    #    前缀 `[core <scope>:event]` 与 worker 透传行 `[worker <scope>:err]` **同一视觉骨架**
    #    `[producer scope:kind]` 且都顶格——并发跑批时多 scope 的行交错，读者只认一个模式即可分辨来源。
    #    事件天然带的标识：scope_*=scope_id、scenario_*/step_*=scenario_id；故先从 plan 的 jobs 建
    #    scenario_id→scope_id 映射，sink 据此把任何事件解析回所属 scope（纯展示，不碰 core/协议）。
    _scenario_to_scope = {sc.id: j.scope_id for j in jobs for sc in j.scenarios}

    def progress_sink(ev: Event) -> None:
        if args.quiet:
            return
        scope = getattr(ev, "scope_id", None) or _scenario_to_scope.get(getattr(ev, "scenario_id", None), "?")
        _progress(f"[core {scope}:event] {render.format_event(ev)}")

    # 实时写（ADR 0030）：sink 始终是纯进度（不再装饰落库）；落库走两个旁路注入——
    #   on_event（sink_lock 外，收 ScopeStarted 刷 RUNNING+血缘，不阻塞别 worker 进度显示）
    #   on_job_complete（主线程，每 job 完成落数据面+控制面终态）。--no-report（persistence=None）则裸跑、两者皆 None。
    on_event = persistence.on_event if persistence else None
    on_job_complete = persistence.on_job_complete if persistence else None

    _progress(
        f"run_id={run_id}  schedule: 启动 worker 建立 AgentCore 云端浏览器会话（将产生 AWS 费用）  "
        f"max_concurrency={args.max_concurrency} job_timeout={args.timeout}s ..."
    )

    # grace 硬约束（ADR 0024）：按本 run 各引擎的下限取 max（grace 是 run 级单值）。引擎特定下限住组合根。
    min_grace = max((compose.engine_min_grace(j.engine) for j in jobs), default=0.0)
    # --grace 哨兵默认（None）→ 跟随本 run 引擎推导（Nova run 自然 ≥act_timeout+余量；midscene-only 回到小值）。
    grace = args.grace if args.grace is not None else max(min_grace, ScheduleOpts.grace_period_s)
    # 显式给了过小 grace → 入口友好拒绝（对齐 votes 校验惯例，退 2「没开跑就被拒」）。core 侧还有 enforce 兜底
    # （任何前端都受同一护栏），此处只为在 cli 给出清晰诊断、避免 core ValueError 冒到用户面。
    if args.grace is not None and (args.grace <= 0 or args.grace < min_grace):
        _progress(
            f"--grace={args.grace} 太小：须 > 0 且 ≥ {min_grace}s（Nova act_timeout+余量；grace < 单 act 时长会致"
            "会话泄漏、软停失效，ADR 0024 grace 硬约束）"
        )
        return 2

    # 5) schedule：跑 RunMeta（definition）→ RunResult（timeout<=0 → 不超时）。
    #    job 一完成即经 on_job_complete 实时落库（数据面判定真值先写，ADR 0030）。
    #    **cloud 运行期兜底（ADR 0030 决定七）**：run 已开跑，落库回调（on_event/on_job_complete）中途抛 botocore
    #    异常（如桶被删）——schedule 会先 stop 所有 worker 再冒泡；need_cloud 时接住归到退 1（error 级）。
    #    单一 schedule 调用点 + 条件 try（不复制两份，避免回调/opts 透传漂移）。
    def _run_schedule():
        return schedule(
            run_meta, resolver, progress_sink,
            ScheduleOpts(
                max_concurrency=args.max_concurrency,
                fail_fast=args.fail_fast,
                job_timeout_s=args.timeout if args.timeout > 0 else None,
                grace_period_s=grace,
                min_grace_s=min_grace,  # core enforce grace ≥ 此下限（引擎无关关系，ADR 0024）
            ),
            on_job_complete=on_job_complete,
            on_event=on_event,
        )

    if need_cloud:
        try:
            result = _run_schedule()
        except Exception as e:
            if _is_botocore_error(e):
                _progress(f"--backend cloud 运行期落库失败（DDB/S3 中途不可达，run 已开跑）：{e}")
                return 1
            raise
    else:
        result = _run_schedule()

    # 6) commit point（ADR 0030 决定三）：各 job 判定真值已由 on_job_complete 逐个流式落；此处只剩
    #    finalize（写总 status + ended_at）+ 归集 ReportStore（派生、永远最后）。「finalize 一落 = run 已提交」。
    #    artifacts 落点指针由 compose 的 make_artifacts 按 backend URI 化组装（local file:// / cloud s3://+ddb://）。
    artifacts: dict[str, str] = {}
    if persistence:
        index = persistence.finalize(result, ended_at=compose.now_iso())
        artifacts = make_artifacts(run_id, index)  # report_index=None（report 写失败被隔离）时该键省略

    # cloud 模式：清理本地 run 根的空壳（ADR 0029）。cloud 下 <report_dir>/<run_id>/ 只是 worker 写产物的临时
    # 暂存区——产物已上传 S3、worker 已 rmtree 各自子目录（nova-trajectories/midscene-run），只剩空目录。
    # 只删空目录（若某个引擎整目录 flush 失败保留了产物、其目录非空则自然不删，与 worker「上传失败保留本地」护栏自洽）。
    # 这是 cli 组合根清自己算出的本地落点——core 对本地文件系统无知（0016 窄腰），不该由 core/store 删。
    # local 模式不清（产物就该留本地当最终落点）。
    if args.backend == "cloud":
        _prune_empty_dirs(report_root / run_id)

    # 7) 核心产出 → stdout（--json：单一 JSON 文档，把产物落点折进同一对象保可解析；否则人看文本汇总）。
    #    产物落点提示属诊断 → stderr（不论模式），不污染被重定向的 stdout 主输出。
    if use_json:
        out = render.to_dict(result)
        if artifacts:
            out["artifacts"] = artifacts
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render.render_text(result))
    if artifacts:
        # report_index 键可能缺席（report 写失败被隔离，ADR 0030 决定三）——缺则提示写失败、不打裸值
        report_line = artifacts.get("report_index", "<报告写入失败，已跳过；判定结果不受影响、仍已落库>")
        _progress(f"\n报告: {report_line}")
        _progress(f"运行元信息: {artifacts['run_meta']}、{artifacts['run_state']}")
        _progress(f"判定明细: {artifacts['jobs_dir']}")

    # 退出码基于 run 级 status（ADR 0031 决定五）：读 schedule 返回的内存终值（必是终态，不回读落库态）。
    # PASSED→0，其余（failed/error，含必伴随 error 的 skipped/aborted 批次）→1。对未来新态稳健。
    return 0 if result.status == Status.PASSED else 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo = compose.repo_root()

    if args.command == "list-engines":
        return _cmd_list_engines(repo)
    if args.command == "plan":
        return _cmd_plan(args, repo)
    if args.command == "run":
        return _cmd_run(args, repo)
    if args.command == "submit":
        return _cmd_submit(args, repo)
    if args.command == "status":
        return _cmd_status(args, repo)
    if args.command == "_reconcile":
        return _cmd_reconcile(args, repo)

    # 无子命令 → 打帮助
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
