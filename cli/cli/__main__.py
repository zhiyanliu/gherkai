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
        "--ddb-table", default=None, metavar="NAME",
        help="[--backend cloud] DynamoDB 表名（分区键 run_id + 排序键 item_type）；兜底环境变量 AWS_DDB_TABLE。表需预先建好",
    )
    run.add_argument(
        "--s3-bucket", default=None, metavar="NAME",
        help="[--backend cloud] S3 桶名（存判定结果、报告与引擎产物）；兜底 AWS_S3_BUCKET。桶需预先建好",
    )
    run.add_argument(
        "--region", default=None, metavar="R",
        help="[--backend cloud] AWS region（不给走 boto3 默认链：AWS_REGION/profile 的 config）",
    )
    run.add_argument(
        "--profile", default=None, metavar="P",
        help="[--backend cloud] AWS profile（不给用 default）；注意 profile 没配 region 时仍需 --region",
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
    # engines 的 resolver 延后到 store 装配之后构造——cloud 时要把 S3 上传落点（bucket + <report_dir>/<run_id>/
    # 前缀）注入给 worker（ADR 0029 第一期），而 bucket 在下面 cloud 分支才确定。artifact_s3 默认 None（local
    # / --no-report → worker 报 file://、不上传）。
    artifact_s3: tuple[str, str] | None = None

    # 3b) 实时写编排（ADR 0030）：组合根按 --backend 注入 local/cloud 两套 store adapter，RunPersistence
    #     负责「随进度落库」的统一编排（commit-point 写序 / RUNNING 中间态 / 按 scope_id 增量刷）。
    #     --no-report 则不落库（逃生舱）：persistence=None，schedule 不接回调、零落盘。
    #     **need_cloud gated**（ADR 0030 决定七）：所有云端校验/import/异常只在 do_report and backend==cloud 时生效——
    #     --backend cloud --no-report 是合法逃生舱（跳过一切云端检查、三个 store 一次不构造）。
    need_cloud = do_report and args.backend == "cloud"
    persistence: RunPersistence | None = None
    make_artifacts = None  # compose 返回的 artifacts 落点组装器（按 backend URI 化）
    if do_report:
        if args.backend == "cloud":
            # cloud 定位参数：flag > 环境变量兜底（ADR 0016）。缺任一 → 入口退 2（否则 None 流进 adapter 运行时才炸）
            table = args.ddb_table or os.environ.get("AWS_DDB_TABLE")
            bucket = args.s3_bucket or os.environ.get("AWS_S3_BUCKET")
            missing = [n for n, v in (("--ddb-table/AWS_DDB_TABLE", table), ("--s3-bucket/AWS_S3_BUCKET", bucket)) if not v]
            if missing:
                _progress(f"--backend cloud 缺必需配置：{', '.join(missing)}（表/桶需预先建好）")
                return 2
            try:
                # cloud 装配下沉 compose（可复用）；import boto3 惰性在 _make_* 钩子里，缺 boto3 抛 ImportError
                run_store, result_store, report_store, make_artifacts = compose.build_cloud_stores(
                    table=table, bucket=bucket, prefix=args.report_dir,
                    region=args.region, profile=args.profile,
                )
            except ImportError as e:
                _progress(f"--backend cloud 需要 boto3：{e}")
                return 2
            # 产物 S3 上传落点（ADR 0029 第一期）：跟 --backend cloud 走。prefix 与 S3ReportStore/ResultStore
            # 同规范化（compose._normalize_prefix，补尾 /），再拼 <run_id>/ → worker 上传 key 与 report 同前缀、
            # 镜像本地 run 树（worker 拼 s3://<bucket>/<prefix><产物相对 run 树路径>）。
            assert bucket  # 上面 missing 校验已保证非 None（收窄类型）
            artifact_s3 = (bucket, f"{compose._normalize_prefix(args.report_dir)}{run_id}/")
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

    # 组合根注入引擎 resolver（延后到此：cloud 时 artifact_s3 已在上面确定，一并注入给 worker，ADR 0029）。
    resolver = compose.make_resolver(
        compose.build_engines(
            repo, nova_logs_dir=nova_logs_dir, midscene_run_dir=midscene_run_dir, artifact_s3=artifact_s3,
        )
    )

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
    # 只删空目录（若某腿整目录 flush 失败保留了产物、其目录非空则自然不删，与 worker「上传失败保留本地」护栏自洽）。
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

    # 无子命令 → 打帮助
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
