"""gherkai：执行核心库的命令行皮（ADR 0016）。

皮做四件事：解析参数 → 读 feature（compose）→ 注入引擎 resolver 跑 schedule → 渲染结果。
逻辑全在 core；这里只接线 + 表层 IO。WebUI 是另一张皮，复用 compose、不经本文件。

跑（开发期）：cd cli && uv run python -m cli <feature> [--default-engine novaact] [...]
真跑会烧 AWS 钱（模型调用 + AgentCore 会话）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gherkai_core.model import TERMINAL_STATUSES, Event, RunMeta, Status
from gherkai_core.parse import FeatureParseError
from gherkai_core.persist import RunPersistence
from gherkai_core.scope import PlanConfig, PlanError, plan
from gherkai_core.schedule import ScheduleOpts, schedule

from gherkai_runtime import compose
from gherkai_runtime import names as _names

from gherkai_cli import render


def _dist_version() -> str:
    """发行版本字符串（唯一真源 = git tag，经 uv-dynamic-versioning 写进包元数据，ADR 0037 决策 2b；
    代码内不复制版本号）。未以包形式安装（如直接以源码路径运行）时给可辨识的占位、不抛。"""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("gherkai")
    except PackageNotFoundError:
        return "0+unknown"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gherkai",
        description="解析 .feature → 分组 scope → 调度两个 AI 引擎 → 汇总运行结果（会烧真 AWS 钱）。",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {_dist_version()}")
    sub = p.add_subparsers(dest="command")

    run = sub.add_parser("run", help="跑一个或多个 .feature")
    run.add_argument("features", nargs="+", type=Path, help="一个或多个 .feature 路径")
    run.add_argument(
        "--default-engine", choices=sorted(_names.ENGINES), default="novaact",
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
        "--default-job-timeout", type=float, default=300.0, metavar="S",
        help="未标 @timeout 的 scope 用的 job 墙钟超时秒（默认 300；<=0 表示不超时）；"
             "标了 @timeout:N tag 的按 tag 走（同 @engine/--default-engine 模式）",
    )
    run.add_argument(
        "--grace", type=float, default=None,
        help="停止后等 worker 优雅退出的宽限秒（默认按本 run 引擎推导：Nova≈act_timeout+余量、"
             "确保 grace≥单 act 时长否则会话泄漏，ADR 0024；显式给过小值会被拒退 2）",
    )
    run.add_argument(
        "--expose-local", default=None, metavar="ORIGIN",
        help="把「本机可达」的被测应用经隧道暴露给云端浏览器（ADR 0035）：值=feature 中书写的原始 origin"
             "（如 http://localhost:3000，也可是局域网地址），框架起隧道并把 job 文本中该前缀替换为公网 URL"
             "（含每 run 一换的 basic-auth 凭据）。需已配 ngrok authtoken（NGROK_AUTHTOKEN）",
    )
    run.add_argument(
        "--tunnel", choices=sorted(_tunnel_providers()), default="ngrok",
        help="--expose-local 用的隧道 provider（默认 ngrok，当前唯一实现）",
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

    # plan 预检（dry-run）：纯本地解析 + 分组；**零 AWS、零花费、零副作用**（ADR 0036——派发标注会起本地
    # 瞬时 worker 自述子进程做 match，不跑 job）。
    pl = sub.add_parser("plan", help="预检 .feature：看 scope/job 分组 + 校验配置，不真跑（不烧钱）")
    pl.add_argument("features", nargs="+", type=Path, help="一个或多个 .feature 路径")
    pl.add_argument(
        "--default-job-timeout", type=float, default=300.0, metavar="S",
        help="未标 @timeout 的 scope 用的 job 墙钟超时秒（默认 300；<=0 表示不超时）——与 run/submit 同源，"
             "让 plan 预检出的 Job 与真跑一致",
    )
    pl.add_argument(
        "--default-engine", choices=sorted(_names.ENGINES), default="novaact",
        help="未标 @engine 的 scope 用的默认引擎（默认 novaact）——影响分组结果，故预检也可设",
    )
    pl.add_argument(
        "--assertion-votes", type=int, default=1, metavar="N",
        help="AI 断言投票次数（默认 1）——影响分组产出的投票次数，故预检也可设",
    )
    pl.add_argument("--json", action="store_true", help="输出机器可读 JSON（scope/job 分组）")
    pl.add_argument(
        "--expose-local", default=None, metavar="ORIGIN",
        help="仅作标注：plan 显示替换前的原始地址（隧道 URL 是运行时产物，plan 零副作用不起隧道，ADR 0035）",
    )

    # ---- 无状态跑批（ADR 0034）：submit 提交完就走 / status 轮询收集 ----
    # local 档：submit setsid fork 一个 per-run 进程跑 reconcile loop（本机推进，无需常驻），CLI 立即退出。
    sm = sub.add_parser("submit", help="[无状态跑批] 提交一批 .feature 到后台跑、立即返回 run_id（提交完就走）")
    sm.add_argument("features", nargs="+", type=Path, help="一个或多个 .feature 路径")
    sm.add_argument("--default-engine", choices=sorted(_names.ENGINES), default="novaact",
                    help="未标 @engine 的 scope 用的默认引擎")
    sm.add_argument("--assertion-votes", type=int, default=1, metavar="N", help="AI 断言投票次数（默认 1）")
    sm.add_argument("--max-concurrency", type=int, default=1,
                    help="同时在跑的 worker 上限（默认 1）；随 definition 到达推进器，cloud 档受部署侧 cap"
                         "（推进器 Lambda env MAX_CONCURRENCY）钳制")
    sm.add_argument(
        "--default-job-timeout", type=float, default=300.0, metavar="S",
        help="未标 @timeout 的 scope 用的 job 墙钟超时秒（默认 300；<=0 表示不超时）；标了 @timeout:N 的按 tag 走",
    )
    sm.add_argument(
        "--expose-local", default=None, metavar="ORIGIN",
        help="经隧道暴露本机可达的被测应用（语义同 run；submit 后隧道由后台进程持有——local=per-run 进程、"
             "cloud=隧道守护进程，本机需保持开机联网直到 run 终态，ADR 0035）",
    )
    sm.add_argument(
        "--tunnel", choices=sorted(_tunnel_providers()), default="ngrok",
        help="--expose-local 用的隧道 provider（默认 ngrok）",
    )
    sm.add_argument(
        "--tunnel-ttl", type=float, default=None, metavar="S",
        help="[cloud + --expose-local] 隧道守护进程的兜底 TTL 秒（默认按 definition 算：各 job 预算之和 + "
             "启动余量，ADR 0035 决策 3）；给了就用本值。TTL 到点无条件拆隧道，调小可能在 run 未完时断隧道",
    )
    sm.add_argument("--report-dir", default="reports", metavar="DIR",
                    help="归集报告落点（默认 reports/）；cloud 档须与推进器 Lambda 的 REPORT_DIR 一致"
                         "（preflight 比对，不一致退 2）")
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
    # 注：submit 不收 --subnet/--security-group——cloud submit 只写 runs 表、不碰 SSM/ECS（ADR 0034），
    # 网络配置由 IaC 注给 reconciler/kicker Lambda 的 env（曾在此声明过两个从不生效的 flag，已删）。

    st = sub.add_parser("status", help="[无状态跑批] 查一个 run 的进度/结果（--wait 轮询到完成）")
    st.add_argument("run_id", help="submit 返回的 run_id")
    st.add_argument("--backend", choices=["local", "cloud"], default="local", help="须与 submit 一致")
    st.add_argument("--report-dir", default="reports", metavar="DIR", help="[local] run 落点（须与 submit 一致）")
    st.add_argument("--wait", action="store_true",
                    help="轮询到 run 达终态再返回（两路都支持，接力语义异：local=本机 tick 推进；"
                         "cloud=检测卡住即 invoke kicker Lambda 接力）")
    st.add_argument("--max-concurrency", type=int, default=1,
                    help="[local --wait] 接力推进并发上限的回落值（meta 带值时以 meta 为准）")
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

    # _tunnel_watch：cloud submit 的隧道守护进程入口（submit setsid fork 它，非用户直接调，ADR 0035 决策 3）：
    # 轮询 run 终态即拆隧道；TTL 兜底自杀防泄漏。
    tw = sub.add_parser("_tunnel_watch", help=argparse.SUPPRESS)
    tw.add_argument("run_id")
    tw.add_argument("--tunnel-pid", type=int, required=True)
    # --ttl 必给、无默认：TTL 按 definition 算（submit 侧 tunnel_host.compute_watch_ttl_s，用户可用
    # submit --tunnel-ttl 覆盖）。给个「没有生产写入者的默认值」正是本 flag 曾恒为 1h 的病根，故不留默认。
    tw.add_argument("--ttl", type=float, required=True)
    tw.add_argument("--ddb-table", required=True)
    tw.add_argument("--region", default=None)
    tw.add_argument("--profile", default=None)

    sub.add_parser("list-engines", help="列出可用引擎及其 spawn 命令")

    # list-deterministic：按引擎查询确定性 step 能力清单（ADR 0036：worker 自述，feature 作者可发现）
    ld = sub.add_parser("list-deterministic", help="列出指定引擎支持的确定性 step（供 feature 作者复用；不烧钱）")
    ld.add_argument("--engine", choices=sorted(_names.ENGINES), default="novaact",
                    help="查哪个引擎的注册表（默认 novaact，对齐 run 的 --default-engine 缺省）")
    ld.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    return p


def _tunnel_providers() -> list[str]:
    from gherkai_runtime.tunnel import PROVIDERS

    return list(PROVIDERS)


def _cmd_list_deterministic(args, repo: Path) -> int:
    """按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern
    语义（ADR 0022「匹配放 worker」红线）。纯本地、零 AWS。"""
    try:
        entries = compose.query_deterministic(repo, args.engine)
    except (ValueError, RuntimeError) as e:
        _progress(f"list-deterministic 失败：{e}")
        return 2
    if args.json:
        print(json.dumps({"engine": args.engine, "deterministic_steps": entries}, ensure_ascii=False, indent=2))
        return 0
    print(f"引擎 {args.engine} 的确定性 step（{len(entries)} 条；test engineer 在 worker 注册表维护，ADR 0022/0036）：")
    if not entries:
        print("  （空——该引擎当前没有注册任何确定性 step，全部 step 走 AI）")
    for e in entries:
        print(f"  - {e.get('description', '（无描述）')}")
        print(f"    示例: {e.get('example', '')}")
        print(f"    模式: {e.get('pattern', '')}")
    return 0


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
    对齐 cli/README 退出码分层）。_cmd_plan 与 _cmd_run 都调它（曾各手抄一份、会漂移）。
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
        jobs = plan(features, PlanConfig(
            default_engine=args.default_engine,
            default_assertion_votes=args.assertion_votes,
            # 两层设定的缺省层（ADR 0019 @timeout / ADR 0034「job timeout」节）：标了 @timeout: 的 scope
            # 按 tag 走，未标的用本缺省；<=0 → None=不超时。载体在 definition（Job.timeout_s），
            # 三路推进器（同步 schedule / local per-run / cloud）各自 enforce。
            default_job_timeout_s=(args.default_job_timeout if args.default_job_timeout > 0 else None),
        ))
        # 引擎名预检（配置错在 plan 层即拦、退 2——否则 local run 要到起 job 时 resolver 才炸，已开跑退 1
        # 且错误形态差）。--default-engine 已被 argparse choices 拦，此处兜的是 @engine tag 拼错。
        unknown = sorted({j.engine for j in jobs} - set(_names.ENGINES))
        if unknown:
            _progress(f"未知引擎 {unknown}（可用：{sorted(_names.ENGINES)}）——@engine tag 拼错？")
            return 2
        return jobs
    except PlanError as e:
        _progress(f"plan 失败（配置矛盾，拒绝运行）：{e}")
        return 2
    except FeatureParseError as e:
        _progress(f"feature 语法错误（gherkin 解析失败，含行:列）：\n{e}")
        return 2


def _validate_max_concurrency(args) -> bool:
    """`--max-concurrency` 入口校验（对齐 `--tunnel-ttl`/`--grace`/`--assertion-votes` 的入口校验惯例）。

    <1 不是「慢一点」而是**永远不动**：并发闸取 min(声明, cap) 后 <=0 会让 `plan_next` 永不提议起 job——
    三路推进器（同步 schedule / local per-run / cloud 推进器）都空转，run 提交出去却卡死在 pending。
    入口拦截（退 2「没开跑就被拒」），不让坏值流进 definition。返回 False = 调用方退 2。

    用 getattr 取值：`plan` 子命令没有这个 flag（纯本地不跑 job），取不到就不校验。
    """
    mc = getattr(args, "max_concurrency", None)
    if mc is not None and mc < 1:
        _progress(f"--max-concurrency={mc} 无效：须 ≥ 1（<=0 会让推进器永不起 job、run 卡死在 pending）")
        return False
    return True


def _probe_deterministic_dispatch(repo: Path, jobs) -> dict | None:
    """plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。

    返回 {(scope_id, scenario_id, step_index): probe} 或 None（全部引擎都没问成）。match 用**裸 step 文本**
    ——与 worker 真跑派发的匹配面完全一致（不 unquote、不拼 argument，ADR 0024）。按引擎 best-effort：
    某引擎查询失败只让该引擎的 job 无标注（stderr 警告），不影响其他引擎与 plan 本体。
    """
    by_engine: dict[str, list[tuple[tuple, str]]] = {}
    for j in jobs:
        for sc in j.scenarios:
            for st in sc.steps:
                by_engine.setdefault(j.engine, []).append(((j.scope_id, sc.id, st.index), st.text))
    dispatch: dict = {}
    ok_any = False
    for engine, items in by_engine.items():
        try:
            probes = compose.match_deterministic(repo, engine, [t for _, t in items])
        except (ValueError, RuntimeError) as e:
            _progress(f"（标注降级）引擎 {engine} 的确定性命中查询失败，该引擎 step 无派发标注：{e}")
            continue
        ok_any = True
        for (key, _), probe in zip(items, probes):
            if probe:  # 只记命中/冲突（AI=None 不进表，渲染端缺失即不标）
                dispatch[key] = probe
    return dispatch if ok_any else None


def _setup_tunnel(args, jobs):
    """`--expose-local` 的 argparse 侧接线：编排在 `gherkai_runtime.tunnel_host`（ADR 0035 决策 1/2/4）。

    返回 (jobs, headers, info)——未给 flag 时 (jobs, None, None)；隧道起不来返回退出码 2
    （「没开跑就被拒」层，与 preflight 同级）。
    """
    if not getattr(args, "expose_local", None):
        return jobs, None, None
    from gherkai_runtime import tunnel as _tunnel
    from gherkai_runtime import tunnel_host

    try:
        setup = tunnel_host.start_tunnel_for_jobs(
            jobs, local_origin=args.expose_local, provider=args.tunnel)
    except _tunnel.TunnelError as e:
        _progress(f"--expose-local 隧道未就绪：{e}")
        return 2
    _progress(f"隧道已建立：{args.expose_local} → {setup.info.url}"
              f"（basic-auth 已启用，凭据每 run 一换、终态即拆）")
    return setup.jobs, setup.extra_http_headers, setup.info


def _cmd_plan(args, repo: Path) -> int:
    """plan 预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。
    **零 AWS、零花费、零副作用**（标注会起本地瞬时 worker 子进程做 match 自述——非跑 job；失败自动降级）。

    与 _cmd_run 共用 `_load_and_plan`（votes 校验 + load_feature + plan），但到此为止——
    省钱验证 feature 写法、看分组、暴露 PlanError。退出码与 run 一致（0 ok / 2 配置错）。
    """
    jobs = _load_and_plan(args, repo)
    if isinstance(jobs, int):  # 前置失败 → 退出码
        return jobs

    # 派发预期标注（ADR 0036 决策 4）：按引擎批量问 worker「哪些 step 命中确定性」。best-effort——
    # 引擎环境未装/查询失败只降级为无标注+stderr 警告，plan 核心功能保持零依赖（不因标注挂掉）。
    dispatch = _probe_deterministic_dispatch(repo, jobs)

    # 核心产出 → stdout（与 run 的输出契约一致：--json 单文档 / 否则人看文本）
    if args.json:
        print(json.dumps(render.plan_to_dict(jobs, args.default_engine, dispatch), ensure_ascii=False, indent=2))
    else:
        print(render.render_plan_text(jobs, args.default_engine, dispatch))
    if dispatch and any(p_ and "conflict" in p_ for p_ in dispatch.values()):
        _progress("⚠ 存在命中多条确定性模式的 step（见上标注）：真跑时这些 step 将 error——请工程侧收紧注册表模式（ADR 0022）。")
    if getattr(args, "expose_local", None):
        # 标注而不替换（ADR 0035 决策 2）：隧道 URL 是运行时产物，plan 零副作用、显示原始地址
        _progress(f"注：{args.expose_local} 将在 run/submit 时经隧道替换为公网 URL（plan 显示原始地址）")
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


def _cmd_submit(args, repo: Path) -> int:
    """[无状态跑批] 提交完就走（ADR 0034）：plan → 写 RunMeta+全 pending → 起首轮推进 → 打印 run_id → 立即退出。

    - **local**：setsid fork per-run 进程跑 reconcile loop 本机推进（无需常驻服务/云）；崩了 status --wait 接力。
    - **cloud**：只 create_run 写 definition 到 DDB（不起 task）→ 之后云端 Lambda 事件驱动链推进
      （runs Stream INSERT→kicker 起首批→events Stream→reconciler→…→finalize），**提交完真关机也跑完**。
      CLI 不留本机进程、submit 机器零 ECS 权限。
    退出码 = 提交成功与否（非 run 判定；判定由 status 查）。
    """
    if not _validate_max_concurrency(args):  # 最早：读 feature/起隧道/preflight 之前（真零副作用）
        return 2
    jobs = _load_and_plan(args, repo)
    if isinstance(jobs, int):
        return jobs
    _progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")

    # --tunnel-ttl 校验（对齐 --grace/--assertion-votes 的入口校验惯例，退 2「没开跑就被拒」）：
    # <=0 等于隧道刚起就被拆。**必须排在起隧道之前**——早拒才真零副作用（否则配置错也已起 ngrok）。
    # isfinite 与 @timeout: 校验同一理由（float() 收 nan/inf；nan 使守护的 monotonic()<deadline 首轮即
    # False → 隧道 submit 后立刻被拆，兜底反成失败源）。
    import math as _math
    if args.tunnel_ttl is not None and (not _math.isfinite(args.tunnel_ttl) or args.tunnel_ttl <= 0):
        _progress(f"--tunnel-ttl={args.tunnel_ttl} 无效：须为有限正数（TTL 到点无条件拆隧道，<=0/nan/inf 均拒）")
        return 2

    # --expose-local：起隧道 + 映射 jobs（ADR 0035）。submit 的隧道生命周期交给后台宿主
    # （local=per-run 进程、cloud=隧道守护进程）；分流失败（preflight/落库不过）时在此拆掉防泄漏。
    tunneled = _setup_tunnel(args, jobs)
    if isinstance(tunneled, int):
        return tunneled
    jobs, tunnel_headers, tunnel_info = tunneled

    run_id = compose.new_run_id()
    run_meta = RunMeta(run_id=run_id, created_at=compose.now_iso(), jobs=tuple(jobs),
                       extra_http_headers=tuple(tunnel_headers.items()) if tunnel_headers else None,
                       max_concurrency=args.max_concurrency)
    from gherkai_core.model import JobState, RunState
    initial = RunState(
        run_id=run_id, status=Status.PENDING,
        jobs={j.scope_id: JobState(scope_id=j.scope_id, status=Status.PENDING) for j in jobs},
        started_at=compose.now_iso(), high_water_mark=0,
    )

    if args.backend == "cloud":
        rc_ = _submit_cloud(args, repo, run_id, run_meta, initial, tunnel_info=tunnel_info)
    else:
        rc_ = _submit_local(args, repo, run_id, run_meta, initial, tunnel_info=tunnel_info)
    if rc_ != 0 and tunnel_info is not None:
        from gherkai_runtime.tunnel import stop_tunnel

        stop_tunnel(tunnel_info.pid)  # 提交失败 → 隧道无宿主可交棒，就地拆（成功路径由后台宿主收尾）
    return rc_


def _submit_local(args, repo: Path, run_id: str, run_meta, initial, *, tunnel_info=None) -> int:
    """local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。"""
    import subprocess as _sp
    from gherkai_core.adapters.event_log import SqliteEventLog

    report_root = Path(args.report_dir).resolve()
    run_store, _rs, _rp, _mk = compose.build_local_stores(report_dir=str(report_root))
    run_store.create_run(run_meta, initial)
    SqliteEventLog(report_root / run_id / "events.db")  # 建库（schema），per-run/status 共用
    if tunnel_info is not None:
        # 隧道收尾凭据落盘（ADR 0035 决策 3）：pid 经 tunnel.json 交给收尾者（per-run 终态后拆；
        # per-run 崩了由 status --wait 接力拆）。进程对象句柄跨进程传不过去，落盘是唯一通道。
        from gherkai_runtime.detached import write_tunnel_file

        write_tunnel_file(str(report_root), run_id, tunnel_info)
        _progress(f"隧道由本机 per-run 进程持有（pid 记录于 {report_root / run_id / 'tunnel.json'}）：run 终态即拆。")

    # setsid fork per-run 进程（start_new_session=True = 脱离 CLI 进程组，CLI 退出不带走它，ADR 0034）。
    cmd = [sys.executable, "-m", "gherkai_cli", "_reconcile", run_id,
           "--report-dir", str(report_root), "--max-concurrency", str(args.max_concurrency)]
    if args.region:
        cmd += ["--region", args.region]
    if args.profile:
        cmd += ["--profile", args.profile]
    # per-run 的 stdout/stderr 落 <run_dir>/reconcile.log（曾全 DEVNULL：worker 崩溃 traceback 零落地，
    # detached 排障只能手工复刻 per-run 前台重跑——真实案例：worker region=None 崩、error 无任何线索）。
    # 子进程持有 fd，父进程开完即交给 Popen；append 模式容多次接力追加。
    log_f = open(report_root / run_id / "reconcile.log", "ab")
    _sp.Popen(cmd, cwd=str(repo), start_new_session=True,
              stdin=_sp.DEVNULL, stdout=log_f, stderr=log_f)
    log_f.close()  # 子进程已持有 fd（Popen 继承），父进程侧句柄即关
    _progress(f"已提交（本机后台推进中）。查进度：gherkai status {run_id} --report-dir {args.report_dir}")
    print(run_id)
    return 0


def _submit_cloud(args, repo: Path, run_id: str, run_meta, initial, *, tunnel_info=None) -> int:
    """cloud submit：只 create_run 写 definition 到 DDB（不起 task）→ 云端 Lambda 事件驱动链接管推进。

    冷启动由 kicker Lambda 做：create_run 写 definition（INSERT）→ runs 表 Stream 触发 kicker → tick 起首批 →
    events Stream → reconciler 接管（补起后续 / finalize）。submit 只写 DDB、不碰 ECS——机器权限收窄到只剩
    「runs 表写 + preflight」（见下正文注释）。CLI 写完即退、不留本机进程。
    """
    target = compose.resolve_cloud_target(
        prefix=args.prefix, region=args.region, profile=args.profile,
        runs_table=args.ddb_table, events_table=args.events_table,
        bucket=args.s3_bucket, cluster=args.cluster,
    )

    # preflight（events 表/cluster/桶/runs 表 + 本 run 用到引擎的 task-def + 事件驱动链三 Lambda + 推进器
    # REPORT_DIR 与 --report-dir 一致性）——配置错在提交前暴露、退 2。链上任一 Lambda 缺 = 提交成功但 run 永不
    # 推进/收敛（kicker 缺=卡 pending、reconciler 缺=无人接力、exit-observer 缺=退出信号断链）；前缀不一致 =
    # 跑完了但结果落在用户没指定的前缀下。都必须挡在提交前（ADR 0033 preflight 条）。探针全只读，权限收窄不破。
    try:
        err = compose.preflight_cloud_resources(
            prefix=target.prefix, events_table=target.events_table, bucket=target.bucket,
            cluster=target.cluster, runs_table=target.runs_table,
            task_defs=[compose.task_def_name(target.prefix, e)
                       for e in sorted({j.engine for j in run_meta.jobs})],
            lambda_fns=target.detached_chain_lambdas, report_dir=args.report_dir,
            # 声明超部署侧 cap 时提示（ADR 0034 机制四）：钳制不改产物落点、run 照跑，故只警不退 2
            # （对照上面 REPORT_DIR 的退 2——判据是分岔后果：钳制是 no-op，产物写去别处不是）。
            declared_max_concurrency=args.max_concurrency, on_warn=_progress,
            region=target.region, profile=target.profile,
        )
    except ImportError as e:
        _progress(f"submit --backend cloud 需要 boto3：{e}")
        return 2
    if err:
        _progress(err)
        return 2

    # **只 create_run 写 definition 到 runs 表**——不起任何 task、不读 SSM 网络、不碰 ECS（ADR 0034）：
    # 冷启动由 kicker Lambda 做（runs 表 Stream 的 INSERT 触发它 tick 起首批）。submit 机器权限面因此收窄到
    # 只剩「runs 表写 + preflight（探表/桶/cluster 可达）」——无需 RunTask/PassRole/SSM 读，契合「提交完就走、
    # 只需提交那一下的最小权限」（受限 CI runner / 临时凭证场景）。之后全程云端 Lambda 链推进、不依赖 submit 机器。
    run_store, _rs, _rp, _mk = compose.build_cloud_stores(
        table=target.runs_table, bucket=target.bucket, prefix=args.report_dir,
        region=target.region, profile=target.profile,
        detached=True,  # STATE 带 detached 标记 → kicker filter 认它冷启动（同步 run 不带，ADR 0034）
    )
    try:
        run_store.create_run(run_meta, initial)  # 写 definition（INSERT）→ runs Stream → kicker Lambda 冷启动
    except Exception as e:
        if compose.is_botocore_error(e):
            _progress(f"submit --backend cloud 云端不可达（表/桶/凭证/region）：{e}")
            return 2
        raise

    if tunnel_info is not None:
        # 隧道守护进程（ADR 0035 决策 3）：cloud submit 的 CLI 立即退出、本机没有 per-run 进程——fork 一个
        # 轻量守护持有隧道：轮询 run 终态即拆 + TTL 兜底自杀。日志落系统临时目录（诊断可寻）。
        import subprocess as _sp
        import tempfile as _tf

        from gherkai_runtime import tunnel_host

        # TTL 按 definition 算（tunnel_host.compute_watch_ttl_s）而非拍一个常数——TTL 短于 run 实际预算时
        # 守护会在 run 还在跑时拆隧道，剩余 job 在被测应用不可达下继续跑、以假失败告终（ADR 0035 决策 3）。
        # `--tunnel-ttl` 给了就用用户值（显式覆盖旋钮）。
        ttl_s = (args.tunnel_ttl if args.tunnel_ttl is not None
                 else tunnel_host.compute_watch_ttl_s(run_meta.jobs))
        watch_log = Path(_tf.gettempdir()) / f"gherkai-tunnel-watch-{run_id}.log"
        cmd = [sys.executable, "-m", "gherkai_cli", "_tunnel_watch", run_id,
               "--tunnel-pid", str(tunnel_info.pid), "--ddb-table", target.runs_table,
               "--ttl", str(ttl_s)]
        if target.region:
            cmd += ["--region", target.region]
        if target.profile:
            cmd += ["--profile", target.profile]
        with open(watch_log, "ab") as lf:
            _sp.Popen(cmd, cwd=str(repo), start_new_session=True,
                      stdin=_sp.DEVNULL, stdout=lf, stderr=lf)
        _progress(f"隧道由守护进程持有（日志 {watch_log}）：run 终态即拆、TTL 兜底 {ttl_s:.0f}s"
                  f"（= 各 job 预算之和 + 启动余量；`--tunnel-ttl` 可覆盖）。"
                  f"**本机需保持开机联网直到 run 终态**——关机=隧道断=测试将以导航失败告终（ADR 0035）。")
        _progress(f"已提交到云端（definition 已落库；kicker Lambda 起首批、云端链推进中）。查进度：gherkai status {run_id} --backend cloud --prefix {target.prefix}")
    else:
        _progress(f"已提交到云端（definition 已落库；kicker Lambda 起首批、云端链推进中，可关机）。查进度：gherkai status {run_id} --backend cloud --prefix {target.prefix}")
    print(run_id)
    return 0


def _render_status(state, args, *, wait_hint: str) -> int:
    """渲染 RunState + pending 诊断提示 + 退出码——**local/cloud 共享一份**（保两路一致，ADR 0034）。

    state 已确认非 None（调用方先查）。wait_hint = 各自的 `status --wait` 接力命令示例（local 用 --report-dir、
    cloud 用 --backend cloud --prefix，触发逻辑同、只命令示例异）。--json 机读、不打人读提示。
    退出码：PASSED→0 / pending·running（未达终态、非 --wait）→0（查询本身成功）/ 其余终态→1。
    """
    if args.json:
        from gherkai_core.serialize import run_state_to_dict
        print(json.dumps(run_state_to_dict(state), ensure_ascii=False, indent=2))
    else:
        print(render.render_run_state(state))
    # 疑似卡住诊断（两路一致）：非 --wait、非 json、仍 pending → 提示 --wait 接力（**只提示、不自动 kickoff/tick**——
    # 保「查看」纯只读无副作用；救活决定权留用户，走 --wait）。running/终态不提示。
    if not args.wait and not args.json and state.status == Status.PENDING:
        _progress(f"提示：run 仍 pending。若已提交较久，推进可能未启动——`{wait_hint}` 可接力推进。")
    if state.status == Status.PASSED:
        return 0
    if state.status not in TERMINAL_STATUSES:  # 未达终态（查询本身成功，判定退出码留给 --wait）
        return 0
    return 1


def _cmd_status(args, repo: Path) -> int:
    """[无状态跑批] 查 run 进度/结果。

    - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-run 崩了人来查也能续、须跑到底）。
    - cloud：读 DDB RunState；--wait 则检测卡住时 invoke kicker Lambda 做 kickoff 接力（踢一脚即可、云端链自接管）。
    渲染+提示+退出码经 _render_status 共享（两路一致，ADR 0034）。
    """
    from gherkai_runtime import detached

    if not _validate_max_concurrency(args):  # --wait 接力的回落值同校验（meta 缺值时它就是并发闸）
        return 2
    if args.backend == "cloud":
        return _status_cloud(args)

    report_root = Path(args.report_dir).resolve()
    run_store, _rs, _rp, _mk = compose.build_local_stores(report_dir=str(report_root))

    # run 存在性检查先于 --wait 接力：不存在的 run 走统一的「退 2 + 提示」，
    # 别让 build_local_reconcile 的 FileNotFoundError 裸 traceback 退 1（README 契约：查不到 run → 2）。
    if run_store.load_run_state(args.run_id) is None:
        _progress(f"未找到 run：{args.run_id}（--report-dir 是否与 submit 一致？）")
        return 2

    if args.wait:
        # 接力推进：per-run 进程崩了/慢了，人来查即自己 tick 到终态（状态全持久、tick 幂等，断点续）。
        meta, log, store, launcher, mc, rstore, pstore = detached.build_local_reconcile(
            repo, str(report_root), args.run_id, args.max_concurrency,
            region=args.region, profile=args.profile,
        )
        detached.run_reconcile_loop(args.run_id, meta, log, store, launcher, mc,
                                    poll_interval_s=0.5, now_iso_fn=compose.now_iso,
                                    result_store=rstore, report_store=pstore)
        detached.cleanup_tunnel(str(report_root), args.run_id)  # 接力者兜底拆隧道（per-run 崩时，ADR 0035）

    state = run_store.load_run_state(args.run_id)
    if state is None:  # 不可达（上面已查过），保险分支
        _progress(f"未找到 run：{args.run_id}（--report-dir 是否与 submit 一致？）")
        return 2
    return _render_status(state, args, wait_hint=f"gherkai status {args.run_id} --report-dir {args.report_dir} --wait")


def _status_cloud(args) -> int:
    """cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做 kickoff
    + 重读，直到终态（ADR 0034 三触发源之一）。

    **接力 invoke kicker（非本机 tick）保 status 机器零 ECS 权限**：起 task 走 Lambda 的角色（有 RunTask/PassRole），
    status 机器只需 `lambda:InvokeFunction`。kicker 名 `{prefix}kicker` 从 --prefix 确定性推理（compose 单一命名
    真源、cli↔IaC 同源）——用户无感。检测卡住（状态连续 K 轮无变化才 kickoff、非每轮无脑踢）：正常推进时不 kickoff、
    避免无效 invoke；卡住（冷启动丢投卡 pending / 中途丢投卡 running）时 kickoff 救回。kickoff 幂等（CAS/HWM 兜底）。
    """
    import time as _time

    target = compose.resolve_cloud_target(prefix=args.prefix, region=args.region,
                                          profile=args.profile, runs_table=args.ddb_table)
    kicker_fn = target.kicker_lambda  # {prefix}kicker，从 prefix 推理出、无需用户配

    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    run_store = DynamoDBRunStore(compose._make_ddb_table(
        target.runs_table, region=target.region, profile=target.profile))

    def _read():
        try:
            return run_store.load_run_state(args.run_id)
        except Exception as e:
            if compose.is_botocore_error(e):
                _progress(f"status --backend cloud 云端不可达（表/凭证/region）：{e}")
                return 2  # 哨兵：调用方转退出码
            raise

    state = _read()
    if state == 2:
        return 2
    if args.wait:
        # 接力循环：轮询到终态；**只在检测到「卡住」时才 invoke kicker 做 kickoff**（非每轮无脑踢——正常推进时
        # 云端链自跑、kickoff 也 no-op 白耗，对齐零空转，ADR 0034 三触发源 cloud 侧）。「卡住」= 状态连续 _STALL_KICK
        # 轮无变化（记 (status, hwm) 快照比对）。检测纯本地内存比较、零额外 AWS 调用/权限。
        _STALL_KICK = 3  # 连续 3 轮（约 9s）状态不变判卡住、踢一次（覆盖冷启动丢投卡 pending / 中途丢投卡 running）
        lam = None
        last_snap = (state.status, state.high_water_mark) if state is not None else None
        stall = 0
        while state is not None and state.status not in TERMINAL_STATUSES:
            snap = (state.status, state.high_water_mark)
            stall = stall + 1 if snap == last_snap else 0  # 有变化即重置（推进中不踢）
            last_snap = snap
            if stall >= _STALL_KICK:
                if lam is None:
                    lam = compose._make_lambda_client(region=target.region, profile=target.profile)
                try:
                    # payload {"run_id": ...}：kicker _run_ids_from_runs_stream 认此「直接 kickoff」格式（区别于
                    # Stream records），对该 run tick 起首批。异步 invoke（Event、不等返回）。
                    lam.invoke(FunctionName=kicker_fn, InvocationType="Event",
                               Payload=json.dumps({"run_id": args.run_id}).encode())
                except Exception as e:
                    if not compose.is_botocore_error(e):
                        raise  # 非 AWS 错才抛
                    # kicker 不存在 → 接力对象缺失，轮询死等无意义：点名 prefix fail-fast（ADR 0033 preflight 条）。
                    # 其他 AWS 错（限流/瞬时/无权限）仍吞——不致命，下轮再踢/靠云端链。
                    if getattr(e, "response", {}).get("Error", {}).get("Code") == "ResourceNotFoundException":
                        _progress(f"status --wait 接力失败：kicker Lambda {kicker_fn}（用 --prefix={target.prefix!r} 拼出）"
                                  f"不存在——是 --prefix 配错、还是 iac_aws_backend（CDK）未部署？")
                        return 2
                stall = 0  # kickoff 后重置，给云端链时间响应（下一个 _STALL_KICK 窗口再判是否仍卡）
            _time.sleep(3.0)
            state = _read()
            if state == 2:
                return 2

    if state is None:
        _progress(f"未找到 run：{args.run_id}（--prefix/--ddb-table 是否与 submit 一致？）")
        return 2
    return _render_status(state, args,
                          wait_hint=f"gherkai status {args.run_id} --backend cloud --prefix {target.prefix} --wait")


def _cmd_reconcile(args, repo: Path) -> int:
    """per-run 进程入口（submit setsid fork 它，非用户直接调）：跑 reconcile loop 到全 done 自退（ADR 0034）。"""
    from gherkai_runtime import detached

    if not _validate_max_concurrency(args):  # 回落值同校验（meta 缺值时它就是并发闸）
        return 2
    report_root = Path(args.report_dir).resolve()
    meta, log, store, launcher, mc, rstore, pstore = detached.build_local_reconcile(
        repo, str(report_root), args.run_id, args.max_concurrency,
        region=args.region, profile=args.profile,
    )
    detached.run_reconcile_loop(args.run_id, meta, log, store, launcher, mc,
                                poll_interval_s=0.5, now_iso_fn=compose.now_iso,
                                result_store=rstore, report_store=pstore)
    detached.cleanup_tunnel(str(report_root), args.run_id)  # 隧道收尾（有 tunnel.json 才动作，ADR 0035）
    return 0


def _cmd_tunnel_watch(args) -> int:
    """隧道守护进程入口（cloud submit setsid fork 它，非用户直接调，ADR 0035 决策 3）。

    守护主体在 `gherkai_runtime.tunnel_host.watch_run_and_stop_tunnel`（产品本体）；此处只接线 + 打印
    （stdout 已被 submit 重定向到 /tmp 的守护日志，故诊断走 print 而非 _progress 的 stderr 惯例）。
    """
    from gherkai_runtime import tunnel_host

    reason = tunnel_host.watch_run_and_stop_tunnel(
        args.run_id, tunnel_pid=args.tunnel_pid, runs_table=args.ddb_table, ttl_s=args.ttl,
        region=args.region, profile=args.profile,
        on_warn=lambda msg: print(f"tunnel-watch: {msg}"),
    )
    print(f"tunnel-watch: 隧道已拆（{reason}）run={args.run_id} pid={args.tunnel_pid}")
    return 0


def _cmd_run(args, repo: Path) -> int:
    use_json = args.json

    if not _validate_max_concurrency(args):  # 最早：读 feature/起隧道/preflight/begin 之前（真零副作用）
        return 2
    # 0/1/2) votes 校验 + 读 feature + plan（与 _cmd_plan 共享；前置失败返回退出码 2，见 _load_and_plan）
    jobs = _load_and_plan(args, repo)
    if isinstance(jobs, int):
        return jobs

    # 进度走 stderr（不再受 --json 开关；stdout 始终只放核心产出）。--quiet 仍可静音逐事件。
    _progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")
    for j in jobs:
        _progress(f"  - scope={j.scope_id!r} engine={j.engine} scenarios={len(j.scenarios)}")

    # 2a) grace 硬约束（ADR 0024）：按本 run 各引擎的下限取 max（grace 是 run 级单值）。引擎特定下限住组合根。
    #     显式给了过小 grace → 入口友好拒绝（对齐 votes 校验惯例，退 2「没开跑就被拒」）。core 侧还有 enforce
    #     兜底（任何前端都受同一护栏），此处只为在 cli 给出清晰诊断、避免 core ValueError 冒到用户面。
    #     **必须排在起隧道 / cloud preflight / persistence.begin 之前**：只依赖 jobs，早拒才真「零副作用」——
    #     否则配置错也已起 ngrok、烧掉云端调用、并落下永不 finalize 的半成品 run 记录。
    min_grace = max((compose.engine_min_grace(j.engine) for j in jobs), default=0.0)
    if args.grace is not None and (args.grace <= 0 or args.grace < min_grace):
        _progress(
            f"--grace={args.grace} 太小：须 > 0 且 ≥ {min_grace}s（Nova act_timeout+余量；grace < 单 act 时长会致"
            "会话泄漏、软停失效，ADR 0024 grace 硬约束）"
        )
        return 2
    # --grace 哨兵默认（None）→ 跟随本 run 引擎推导（Nova run 自然 ≥act_timeout+余量；midscene-only 回到小值）。
    grace = args.grace if args.grace is not None else max(min_grace, ScheduleOpts.grace_period_s)

    # 2b) --expose-local：起隧道 + 把 jobs 文本中的 origin 替换成公网 URL（ADR 0035）。前台 run 的隧道
    #     跟 CLI 进程走——atexit 拆（正常结束/Ctrl-C 都收；SIGTERM 直杀的极端泄漏由 ngrok 进程可见性兜）。
    tunneled = _setup_tunnel(args, jobs)
    if isinstance(tunneled, int):
        return tunneled
    jobs, tunnel_headers, tunnel_info = tunneled
    if tunnel_info is not None:
        import atexit

        from gherkai_runtime.tunnel import stop_tunnel
        atexit.register(stop_tunnel, tunnel_info.pid)

    # 3) 组合根：构造 RunMeta（definition：生成 run_id + now + plan 产出的 jobs，先于跑批，ADR 0016/0027）
    #    + 注入具体引擎 resolver（core 引擎无关）
    run_id = compose.new_run_id()
    run_meta = RunMeta(run_id=run_id, created_at=compose.now_iso(), jobs=tuple(jobs),
                       extra_http_headers=tuple(tunnel_headers.items()) if tunnel_headers else None,
                       max_concurrency=args.max_concurrency)
    do_report = not args.no_report  # RunReport 默认生成；--no-report 跳过（逃生舱）
    # 归集时让两个引擎的产物都落到 run 专属持久目录（否则用 SDK 默认：Nova 临时目录会被清理、Midscene
    # 落相对 worker cwd 的固定 midscene_run/ 每 run 覆盖）。两引擎对称落 reports/<run_id>/ 下（ADR 0027）。
    # **必须传绝对路径**：worker 是另起的子进程、cwd 与 cli 不同（cli=cli/，worker=engines/*/），相对路径
    # 会被两进程各自的 cwd 解析到不同位置 → 产物落错地方、且 worker 产出的 file://<相对> 是坏 URI。
    report_root = Path(args.report_dir).resolve()
    nova_logs_dir = (report_root / run_id / "nova-trajectories") if do_report else None
    midscene_run_dir = (report_root / run_id / "midscene-run") if do_report else None
    # 产物 S3 落点：cloud（Fargate）由 build_fargate_engines 内部按 (bucket, <report_dir>/<run_id>/) 自算注入；
    # local（subprocess）CLI 恒不注入（worker 报 file://、不上传）——「subprocess+注入 S3 落点」是内部预演档
    # （ADR 0016 决策 B / 0029），由 tools/e2e_harness.py 自拼 worker env 直起 worker 实现，不经 CLI/compose。
    cloud_fargate: dict | None = None  # cloud 分支置值（ADR 0033）：Fargate 执行配置，供 build_fargate_engines；None＝走 subprocess
    # 目标解析（compose.resolve_cloud_target 一次吐 prefix + 各资源终名 + region/profile，ADR 0033 两层命名）。
    # **local 档也解析**：region/profile 两路都要（喂 subprocess worker + store），云资源名多算几个纯字符串、不用即弃。
    # region/profile 是「正确的非对称」（ADR 0016 决策 C）：
    # - profile：--profile > AWS_PROFILE。仅 subprocess worker 注入（继承本机 ~/.aws、profile 合法）；
    #   **Fargate 绝不注入**（容器无 ~/.aws、用 task role，注入不存在的 profile 名会 ProfileNotFound 盖过 task role）。
    # - region：解析链落实成**具体字符串**（见 compose.resolve_region）。profile config 回落是关键：AgentCore
    #   validate_region 不吃 profile config、要显式 region 字符串，不落实则 profile-only 下 worker InvalidRegionError
    #   崩。落实后 subprocess env + FargateEngine overrides + store 三处同源、消除分叉。
    # 均可为 None＝真无（fail-loud、不硬编码 east，对齐 store 宽容边界）。
    target = compose.resolve_cloud_target(
        prefix=args.prefix, region=args.region, profile=args.profile,
        runs_table=args.ddb_table, events_table=args.events_table,
        bucket=args.s3_bucket, cluster=args.cluster,
    )

    # 3a) 执行轴（ADR 0016 决策 A / 0033）：--backend cloud ⇒ Fargate 执行，**与 report 正交**——`--no-report` 只关
    #     不落库、不碰「在哪执行」。故 cloud 的 Fargate 执行配置解析在 do_report **之外**：`--no-report --backend cloud`
    #     仍在 Fargate 跑，只是不生成 report。cloud_fargate 置值 = 下面 resolver 用 FargateEngine（否则 SubprocessEngine）。
    if args.backend == "cloud":
        # preflight 执行必需资源（events 表 + cluster + 本 run 用到引擎的 task-def；桶=job-in/产物上传也执行
        # 需要）——fail-fast 点名 prefix。runs 表仅落库需要，故只在 do_report 时探（见 3b begin 探活）；此处
        # 不探 runs 表（--no-report 下用不到）。不探 Lambda——同步 run 进程内推进、不依赖事件驱动链（ADR 0033）。
        try:
            err = compose.preflight_cloud_resources(
                prefix=target.prefix, events_table=target.events_table, bucket=target.bucket,
                cluster=target.cluster,
                task_defs=[compose.task_def_name(target.prefix, e) for e in sorted({j.engine for j in jobs})],
                runs_table=target.runs_table if do_report else None,  # runs 表仅 do_report 探（落库需要）
                region=target.region, profile=target.profile,
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
                prefix=target.prefix, subnets=args.subnet, security_groups=args.security_group,
                region=target.region, profile=target.profile,
            )
        except Exception as e:
            if compose.is_botocore_error(e):
                _progress(f"--backend cloud 读 subnet/sg SSM 失败（/{target.prefix}backend/*——CDK 未写或无权限？）：{e}")
                return 2
            raise
        cloud_fargate = {"prefix": target.prefix, "cluster": target.cluster,
                         "events_table": target.events_table, "bucket": target.bucket,
                         "network_config": network_config}

    # 3b) 落库轴（ADR 0030）：组合根按 --backend 注入 local/cloud 两套 store adapter，RunPersistence 负责「随进度落库」
    #     的统一编排（commit-point 写序 / RUNNING 中间态 / 按 scope_id 增量刷）。--no-report 则不落库（逃生舱）：
    #     persistence=None，schedule 不接回调、零落盘——**但执行仍按 3a 的 backend 走**（report 与执行正交）。
    #     **need_cloud gated**（ADR 0030 决定七）：云端 store 校验/import/异常只在 do_report and backend==cloud 时生效。
    need_cloud = do_report and args.backend == "cloud"
    persistence: RunPersistence | None = None
    make_artifacts = None  # compose 返回的 artifacts 落点组装器（按 backend URI 化）
    if do_report:
        if args.backend == "cloud":
            try:
                # cloud 装配下沉 compose（可复用）；import boto3 惰性在 _make_* 钩子里，缺 boto3 抛 ImportError
                # 表/桶取 target（与 3a 的 preflight/Fargate 配置同一份解析，不再各自重拼）
                run_store, result_store, report_store, make_artifacts = compose.build_cloud_stores(
                    table=target.runs_table, bucket=target.bucket, prefix=args.report_dir,
                    region=target.region, profile=target.profile,
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
            if need_cloud and compose.is_botocore_error(e):
                _progress(f"--backend cloud 云端不可达（表/桶不存在或无权限/凭证·region 缺）：{e}")
                return 2
            raise

    # 组合根注入引擎 resolver（延后到此：需 run_id + store 装配后）。
    # **决策 A 落到 CLI（ADR 0016/0033）**：cloud ⇒ FargateEngine（云执行，产物落点内部自算）；否则 SubprocessEngine（本地，不注入 S3 落点）。
    # cloud_fargate 在 3a 的 `backend=='cloud'` 分支**无条件置值**（与 do_report 正交，report⊥执行）——故
    # `--backend cloud --no-report` 仍走 Fargate（cloud_fargate 非 None），只是不落库、不生成 report。
    # `--no-report` 的逃生舱只作用于 store 轴（persistence=None、不构造三个 store），绝不改执行环境（见 3a 注释 + ADR 0016 决策 A）。
    if cloud_fargate is not None:
        engines = compose.build_fargate_engines(
            run_id=run_id, prefix=cloud_fargate["prefix"], cluster=cloud_fargate["cluster"],
            events_table=cloud_fargate["events_table"], bucket=cloud_fargate["bucket"],
            report_dir=args.report_dir, network_config=cloud_fargate["network_config"],
            region=target.region, profile=target.profile,
            extra_http_headers=tunnel_headers,  # 隧道模式的额外请求头（ADR 0035 决策 4；None=不注入）
        )
    else:
        engines = compose.build_engines(
            repo, nova_logs_dir=nova_logs_dir, midscene_run_dir=midscene_run_dir,
            region=target.region, profile=target.profile,
            extra_http_headers=tunnel_headers,  # 同上（ADR 0035）
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
        f"max_concurrency={args.max_concurrency} default_job_timeout={args.default_job_timeout}s ..."
    )

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
            if compose.is_botocore_error(e):
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
        compose.prune_empty_dirs(report_root / run_id)

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

    if args.command == "list-deterministic":
        return _cmd_list_deterministic(args, repo)
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
    if args.command == "_tunnel_watch":
        return _cmd_tunnel_watch(args)
    if args.command == "_reconcile":
        return _cmd_reconcile(args, repo)

    # 无子命令 → 打帮助
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
