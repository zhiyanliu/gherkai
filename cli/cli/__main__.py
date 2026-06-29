"""yaozhou-run：执行核心库的命令行皮（ADR 0016）。

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

from core.adapters.report_store.local import LocalReportStore
from core.adapters.run_store.local import LocalRunStore
from core.adapters.result_store.local import LocalResultStore
from core.model import Event, RunMeta, run_state_from_result
from core.scope import PlanConfig, PlanError, plan
from core.schedule import ScheduleOpts, schedule

from cli import compose, render


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="yaozhou-run",
        description="解析 .feature → 分组 scope → 调度两腿 AI 引擎 → 汇总 RunResult（会烧真 AWS 钱）。",
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
        help="AI 断言（Then）投票次数（默认 1=单次判定）；调高（如 3/5）启用抖动检测：跑 N 次取多数票（ADR 0014）",
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
        "--grace", type=float, default=10.0,
        help="停止请求后等 worker 优雅退出的宽限秒（默认 10）",
    )
    run.add_argument("--fail-fast", action="store_true", help="任一 job 崩则中止整批")
    run.add_argument("--json", action="store_true", help="只输出机器可读 JSON（不打进度/文本汇总）")
    run.add_argument("--quiet", action="store_true", help="不打逐事件进度（仍打文本汇总）")
    # RunReport 是 run 的应得产物：默认总归集（manifest.json + index.html）到 <report-dir>/<run_id>/。
    run.add_argument(
        "--report-dir", default="reports", metavar="DIR",
        help="RunReport 归集落点（默认 reports/；每次 run 落 DIR/<run_id>/，ADR 0027）",
    )
    run.add_argument(
        "--no-report", action="store_true",
        help="跳过 RunReport 归集（CI 只看退出码/JSON、或调试时不想落盘的逃生舱）",
    )
    run.add_argument(
        "--materialize", action="store_true",
        help="归集时把本地原生产物按字节拷进 <run_id>/artifacts/（自包含、可搬运/上 S3；默认只链接不拷）",
    )

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


def _progress(*args, **kwargs) -> None:
    """进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。

    这样 `cli run … --json > r.json` 拿到纯净 JSON、`cli run … > summary.txt` 拿到纯净文本汇总，
    进度（plan/event/run_id/RunReport 落点）照样在终端可见、不污染被重定向的主输出。
    """
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)


def _cmd_run(args, repo: Path) -> int:
    use_json = args.json

    # 0) 校验配置：assertion_votes 必须 ≥1。否则 worker 跑 0 次 AI 断言——votes=0 全判失败（假阴性）、
    #    votes<0 更危险：判定 0 > 负数/2 = True → **零 AI 调用却全绿**（假阳性），且 1/1 隐藏渲染看不出。
    #    在入口拦截（退出码 2，与 plan 配置矛盾一致），不让坏值流进 worker 白烧会话。
    if args.assertion_votes < 1:
        _progress(f"--assertion-votes 必须 ≥ 1（收到 {args.assertion_votes}）：投票次数 <1 会让 AI 断言不被执行")
        return 2

    # 1) 读 feature（组合根的事，core 不碰 FS）→ FeatureSource[]
    try:
        features = [compose.load_feature(f, repo) for f in args.features]
    except FileNotFoundError as e:
        _progress(f"读 feature 失败：{e}")
        return 2

    # 2) plan：.feature → Job[]（uri 互异/engine 冲突等违约 → PlanError）
    try:
        jobs = plan(features, PlanConfig(
            default_engine=args.default_engine,
            default_assertion_votes=args.assertion_votes,
        ))
    except PlanError as e:
        _progress(f"plan 失败（配置矛盾，拒绝运行）：{e}")
        return 2

    # 进度走 stderr（不再受 --json 开关；stdout 始终只放核心产出）。--quiet 仍可静音逐事件。
    _progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")
    for j in jobs:
        _progress(f"  - scope={j.scope_id!r} engine={j.engine} scenarios={len(j.scenarios)}")

    # 3) 组合根：构造 RunMeta（definition：生成 run_id + now + plan 产出的 jobs，先于跑批，ADR 0016/0027）
    #    + 注入具体引擎 resolver（core 引擎无关）
    run_id = compose.new_run_id()
    run_meta = RunMeta(run_id=run_id, created_at=compose.now_iso(), jobs=tuple(jobs))
    do_report = not args.no_report  # RunReport 默认生成；--no-report 跳过（逃生舱）
    # 归集时让 Nova trajectory 落到 run 专属持久目录（否则用 SDK 默认临时目录，会被清理）。
    # **必须传绝对路径**：worker 是另起的子进程、cwd 与 cli 不同（cli=cli/，nova worker=engines/novaact/），
    # 相对路径会被两进程各自的 cwd 解析到不同位置 → trajectory 落错地方、且 worker 产出的 file://<相对> 是坏 URI。
    nova_logs_dir = (Path(args.report_dir).resolve() / run_id / "nova-trajectories") if do_report else None
    resolver = compose.make_resolver(compose.build_engines(repo, nova_logs_dir=nova_logs_dir))

    # 4) sink：逐事件进度 → stderr（诊断；--quiet 静音。不再受 --json 影响——走 stderr 不污染 stdout 数据）
    def sink(ev: Event) -> None:
        if not args.quiet:
            _progress(f"  [event] {render.format_event(ev)}")

    _progress(
        f"run_id={run_id}  schedule: 起真 worker → 真 AgentCore 会话（烧钱）"
        f"max_concurrency={args.max_concurrency} job_timeout={args.timeout}s ..."
    )

    # 5) schedule：跑 RunMeta（definition）→ RunResult（timeout<=0 → 不超时）
    result = schedule(
        run_meta, resolver, sink,
        ScheduleOpts(
            max_concurrency=args.max_concurrency,
            fail_fast=args.fail_fast,
            job_timeout_s=args.timeout if args.timeout > 0 else None,
            grace_period_s=args.grace,
        ),
    )

    # 6) 落盘 + 归集（默认开，run 的应得产物；--no-report 跳过；同 <report-dir>/<run_id>/ 落点）
    #    先落盘再渲染：--json 模式要把产物落点折进同一个 JSON 文档（见 7），故产物路径需先备好。
    artifacts: dict[str, str] = {}
    if do_report:
        root = Path(args.report_dir)
        # 6a) RunStore：definition(RunMeta) + 运行态(RunState) 落盘（控制面，不存判定明细，ADR 0016）
        #     断「从 RunResult 反推身份」——meta 是组合根先于跑批构造的 definition，state 从 result 投影运行态
        LocalRunStore(root).save_run(run_meta, run_state_from_result(result))
        # 6b) ResultStore：每 job 判定追加落盘（数据面判定真值唯一权威，CI 读单 scope，ADR 0016）
        result_store = LocalResultStore(root)
        for jr in result.jobs:
            result_store.save_job_result(run_id, jr)
        # 6c) ReportStore：归集 RunReport（人看入口 + manifest，软引用 run_id，ADR 0027）
        index = LocalReportStore(root).write(
            run_id, result, created_at=compose.now_iso(), materialize=args.materialize
        )
        # 三层落点（ADR 0016）：RunResult 不存单一 run.json，分解为 RunStore(run_meta+run_state)
        # + ResultStore(jobs/) + ReportStore(index/manifest)。
        artifacts = {
            "report_index": str(index),
            "run_meta": str(root / run_id / "run_meta.json"),
            "run_state": str(root / run_id / "run_state.json"),
            "jobs_dir": str(root / run_id / "jobs"),
        }

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
        _progress(f"\nRunReport: {artifacts['report_index']}")
        _progress(
            f"RunStore: {artifacts['run_meta']} + run_state.json"
            f" | 判定明细: {artifacts['jobs_dir']}/"
        )

    return 0 if result.status.value == "passed" else 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo = compose.repo_root()

    if args.command == "list-engines":
        return _cmd_list_engines(repo)
    if args.command == "run":
        return _cmd_run(args, repo)

    # 无子命令 → 打帮助
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
