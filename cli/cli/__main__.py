"""yaozhou-run：执行核心库的命令行皮（ADR 0016）。

皮做四件事：解析参数 → 读 feature（compose）→ 注入引擎 resolver 跑 schedule → 渲染结果。
逻辑全在 core；这里只接线 + 表层 IO。WebUI 是另一张皮，复用 compose、不经本文件。

跑（开发期）：cd cli && uv run python -m cli <feature> [--engine novaact] [...]
真跑会烧 AWS 钱（模型调用 + AgentCore 会话）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.adapters.report_store.local import LocalReportStore
from core.model import Event
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
        "--engine", default="novaact",
        help="未标 @engine 的 scope 用的默认引擎（默认 novaact）",
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


def _cmd_run(args, repo: Path) -> int:
    use_json = args.json

    # 1) 读 feature（组合根的事，core 不碰 FS）→ FeatureSource[]
    try:
        features = [compose.load_feature(f, repo) for f in args.features]
    except FileNotFoundError as e:
        print(f"读 feature 失败：{e}", file=sys.stderr)
        return 2

    # 2) plan：.feature → Job[]（uri 互异/engine 冲突等违约 → PlanError）
    try:
        jobs = plan(features, PlanConfig(default_engine=args.engine))
    except PlanError as e:
        print(f"plan 失败（配置矛盾，拒绝运行）：{e}", file=sys.stderr)
        return 2

    if not use_json:
        print(f"plan: {len(jobs)} job(s)  (default_engine={args.engine})")
        for j in jobs:
            print(f"  - scope={j.scope_id!r} engine={j.engine} scenarios={len(j.scenarios)}")

    # 3) 组合根：mint run_id（先于跑批，ADR 0027）+ 注入具体引擎 resolver（core 引擎无关）
    run_id = compose.new_run_id()
    do_report = not args.no_report  # RunReport 默认生成；--no-report 跳过（逃生舱）
    # 归集时让 Nova trajectory 落到 run 专属持久目录（否则用 SDK 默认临时目录，会被清理）
    nova_logs_dir = (Path(args.report_dir) / run_id / "nova-trajectories") if do_report else None
    resolver = compose.make_resolver(compose.build_engines(repo, nova_logs_dir=nova_logs_dir))

    # 4) sink：逐事件进度（--json/--quiet 时关掉）
    def sink(ev: Event) -> None:
        if not use_json and not args.quiet:
            print(f"  [event] {render.format_event(ev)}")

    if not use_json:
        print(
            f"run_id={run_id}  schedule: 起真 worker → 真 AgentCore 会话（烧钱）"
            f"max_concurrency={args.max_concurrency} job_timeout={args.timeout}s ..."
        )

    # 5) schedule：跑（timeout<=0 → 不超时）
    result = schedule(
        jobs, resolver, sink, run_id,
        ScheduleOpts(
            max_concurrency=args.max_concurrency,
            fail_fast=args.fail_fast,
            job_timeout_s=args.timeout if args.timeout > 0 else None,
            grace_period_s=args.grace,
        ),
    )

    # 6) 渲染
    if use_json:
        print(json.dumps(render.to_dict(result), ensure_ascii=False, indent=2))
    else:
        print(render.render_text(result))

    # 7) 归集 RunReport（默认生成，run 的应得产物；--no-report 跳过，ADR 0027）
    if do_report:
        store = LocalReportStore(Path(args.report_dir))
        index = store.write(run_id, result, created_at=compose.now_iso(), materialize=args.materialize)
        if use_json:
            print(json.dumps({"report_index": str(index)}, ensure_ascii=False))
        else:
            print(f"\nRunReport: {index}")

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
