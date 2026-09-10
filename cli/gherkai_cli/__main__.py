"""gherkai：执行核心库的命令行皮（ADR 0016）。

皮做四件事：解析参数 → 读 feature（compose）→ 注入引擎 resolver 跑 schedule → 渲染结果。
逻辑全在 core；这里只接线 + 表层 IO。WebUI 是另一张皮，复用 compose、不经本文件。

跑（开发期，仓库根）：uv run gherkai run <feature> [--default-engine novaact] [...]；装后直接 `gherkai run …`
真跑会产生 AWS 费用（模型调用 + AgentCore 会话）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

from gherkai_core.model import TERMINAL_STATUSES, Event, RunMeta, Status
from gherkai_core.parse import FeatureParseError
from gherkai_core.persist import RunPersistence
from gherkai_core.scope import PlanConfig, PlanError, plan
from gherkai_core.schedule import ScheduleOpts, schedule

from gherkai_runtime import compose
from gherkai_runtime import names as _names

from gherkai_cli import deploy as _deploy
from gherkai_cli import render


def _dist_version() -> str:
    """发行版本字符串（唯一真源 = git tag，经 uv-dynamic-versioning 写进包元数据，ADR 0037 决策 2b；
    代码内不复制版本号）。未以包形式安装（如直接以源码路径运行）时给可辨识的占位、不抛。"""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("gherkai")
    except PackageNotFoundError:
        return "0+unknown"


def _installed_version() -> "str | None":
    """给**契约比对**用的版本（skew 三态 / worker variant 解析 / 交 provider 写版本戳，ADR 0037 决策 7、0038）：
    未装成包 → None（让产品本体按「取不到自身版本」分叉：skew 跳过、variant 解析 fail-loud 说「装成包后再提交」），
    **不给占位串**——`_dist_version()` 的 `0+unknown` 是给 `--version` 显示用的，喂进契约会被 `image_tag` 归一化成
    `0.unknown-<variant>`、把「你没装成包」误报成「镜像没推」。"""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("gherkai")
    except PackageNotFoundError:
        return None


# `--steps-dir` 的公共 help（run/plan/submit/list-deterministic 四处共用，措辞单点维护、不抄四份）。
# 文案是产品面（不带 ADR/内部机制名）；定制 step 的解析与 fail-loud 判据见 ADR 0037 决策 4。
_STEPS_DIR_HELP = (
    "你自己的确定性 step 目录（默认 ./steps 存在即用；亦可 env GHERKAI_STEPS_DIR）：worker 启动时排序递归"
    "加载其中的 step 定义文件、注册进它的确定性注册表"
)


# deploy/destroy 两个子命令要先解析 provider 才能贴它的 flag（见 _peek_deploy_provider / _build_parser）。
_DEPLOY_COMMANDS = ("deploy", "destroy")


def _peek_deploy_provider(argv: list[str] | None) -> "tuple[object | None, str | None]":
    """从 argv 窥出「是不是 deploy/destroy、有没有 --provider」，据此解析部署 provider（ADR 0037 决策 6）。

    用一个极小的预解析器（不带 help、不认缩写、`parse_known_args`）——它只认「子命令 + --provider」两件事，
    其余全落 unknown 交给真 parser。**故意不在此报任何错**：argv 不成形（子命令拼错、`--provider` 缺值等）
    一律返回 `(None, None)`，让真 parser 出它自己那套完整帮助/诊断，不在预解析层复刻一遍 argparse 的报错。
    """
    if not argv:
        return None, None
    pre = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    pre.add_argument("command", nargs="?")
    pre.add_argument("--provider", default=None)
    try:
        ns, _rest = pre.parse_known_args(argv)
    except SystemExit:  # 预解析器自己的 error（如 --provider 缺值）：留给真 parser 报
        return None, None
    if ns.command not in _DEPLOY_COMMANDS:
        return None, None
    return _deploy.resolve_provider(ns.provider)


def _add_selection_flags(p: argparse.ArgumentParser) -> None:
    """run / plan / submit 共用的 scenario 筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。"""
    p.add_argument(
        "--tags", action="append", default=None, metavar="TAG[,TAG...]",
        help="只跑带这些 tag 的 scenario：一个值内逗号分隔为「任一命中」，重复给本 flag 为「都要命中」；@ 可省。"
             "feature 行的 tag 已传给其下每个 scenario",
    )
    p.add_argument(
        "--scenario", action="append", default=None, metavar="SEL",
        help="只跑这些 scenario（可重复，任一命中）：SEL = <文件>:<行号>，或 行号 / :行号，或标题的一段文字（区分大小写）。"
             "与 --tags 同给时两者都要满足",
    )


def _build_selector(args):
    """把 `--tags` / `--scenario` 组装成 `plan(select=…)` 的谓词；两者都没给 → None（不筛）。

    tag：每个 --tags 值拆逗号、去 @ 归一后取「任一命中」，多个 --tags 之间取「且」。scenario：等于 id（uri:line）/
    行号 / 标题子串，多个之间取「或」。两组之间取「且」。core 不认这些 flag，只收谓词（ADR 0041 决策一）。
    """
    tag_groups = [
        {t.strip().lstrip("@") for t in raw.split(",") if t.strip()}
        for raw in (getattr(args, "tags", None) or [])
    ]
    tag_groups = [g for g in tag_groups if g]
    sels = [s for s in (getattr(args, "scenario", None) or []) if s]
    if not tag_groups and not sels:
        return None

    def _scenario_hit(p) -> bool:
        sid, name = p.scenario.id, p.scenario.name
        # id = <uri>:<声明行>[:<Examples 数据行>]（Scenario Outline 展开，ADR 0025）。用权威 p.uri 切尾、不按冒号反解
        # （uri 可含冒号）；行号命中声明行 = 选中该 outline 的全部 example，命中数据行 = 只选那一条。
        tail = sid[len(p.uri) + 1:] if sid.startswith(p.uri + ":") else sid.rsplit(":", 1)[-1]
        lines = set(tail.split(":"))
        for s in sels:
            if s == sid:  # 一档：完整 scenario id
                return True
            bare = s.lstrip(":")
            if bare.isascii() and bare.isdecimal():  # 二档：行号——纯数字只当行号，不回落标题子串（否则「重试3次」被 --scenario 3 连带选中）
                if bare in lines:
                    return True
                continue
            if s in name:  # 三档：标题子串
                return True
        return False

    def select(p) -> bool:
        tags = {t.lstrip("@") for t in p.tags}
        if any(not (g & tags) for g in tag_groups):
            return False
        return _scenario_hit(p) if sels else True

    return select


def _selection_label(args) -> str:
    bits = [f"--tags {v}" for v in (getattr(args, "tags", None) or [])]
    bits += [f"--scenario {v}" for v in (getattr(args, "scenario", None) or [])]
    return " ".join(bits)


def _build_parser(*, provider: object | None = None, provider_error: str | None = None) -> argparse.ArgumentParser:
    """建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。

    **为何 provider 由 `main` 先解析、而不是在这里按需解析**：贴 flag 必须先加载 provider，而加载 = import 一个
    带 CDK 的包（jsii，import 即起 node 子进程）——不能让 `gherkai run` 也付这个代价，故只在真跑 deploy/destroy
    时解析（见 `_peek_deploy_provider`）。两者都不给时 deploy/destroy 只有皮自己的命令面 flag。
    """
    p = argparse.ArgumentParser(
        prog="gherkai",
        description="解析 .feature → 分组 scope → 调度两个 AI 引擎 → 汇总运行结果（会产生真实 AWS 费用）。",
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
    # 下限判据（Nova 的 act_timeout + 余量、为何必须 ≥ 单个 act 时长）见 ADR 0024；help 只讲怎么用。
    run.add_argument(
        "--grace", type=float, default=None,
        help="停止后等 worker 优雅退出的宽限秒（默认按本 run 引擎推导：Nova≈act_timeout+余量）；"
             "小于单个 act 的时长会让浏览器会话泄漏，给过小值直接退 2",
    )
    # 隧道暴露本机应用的整套机制（凭据轮换、生命周期、谁负责拆）见 ADR 0035。
    run.add_argument(
        "--expose-local", default=None, metavar="ORIGIN",
        help="把「本机可达」的被测应用经隧道暴露给云端浏览器：值=feature 中书写的原始 origin"
             "（如 http://localhost:3000，也可是局域网地址），框架起隧道并把 job 文本中该前缀替换为公网 URL"
             "（含每 run 一换的 basic-auth 凭据）。需已配 ngrok authtoken（NGROK_AUTHTOKEN）",
    )
    run.add_argument(
        "--tunnel", choices=sorted(_tunnel_providers()), default="ngrok",
        help="--expose-local 用的隧道 provider（默认 ngrok，当前唯一实现）",
    )
    _add_selection_flags(run)
    run.add_argument("--fail-fast", action="store_true", help="任一 job 崩则中止整批")
    run.add_argument("--json", action="store_true", help="只输出机器可读 JSON（不打进度/文本汇总）")
    run.add_argument("--quiet", action="store_true",
                     help="少进屏幕/上下文：不打逐事件进度；本机跑时 worker 日志改落 <report-dir>/<run_id>/worker.log（--no-report 时落系统临时目录），"
                          "只打一行位置（cloud 档 worker 在云端跑、日志在 CloudWatch，无此文件）；仍打文本汇总")
    # RunReport 是 run 的应得产物：默认总归集（manifest.json + index.html）到 <report-dir>/<run_id>/。
    run.add_argument(
        "--report-dir", default="reports", metavar="DIR",
        help="归集报告落点（默认 reports/；每次 run 落 DIR/<run_id>/）",
    )
    run.add_argument(
        "--no-report", action="store_true",
        help="跳过报告归集（CI 只看退出码/JSON、或调试时不想落盘的逃生舱）",
    )
    run.add_argument(
        "--steps-dir", default=None, metavar="DIR",
        help=_STEPS_DIR_HELP + "。值随提交记录走，本机后台推进/接力进程都读回同一份；"
             "[--backend cloud] 不生效（云端 worker 的 steps 烙在定制镜像里，警告不拦）",
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
             "须与 `gherkai deploy --prefix` 一致。多环境切换（prod-/stage-）用它。兜底 AWS_RESOURCE_PREFIX",
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
        "--worker-variant", default=None, metavar="NAME",
        help="[--backend cloud] 云端 worker 镜像 variant（= 一套具名的确定性 step 集烙成的定制镜像）："
             "缺省用部署的默认指针（`gherkai deploy` 初始化为 base）。提交时把它解析成本 run 各引擎的"
             "精确 task-def revision 写进提交记录（一个 run 内镜像固定，别人重推同名 variant 不影响在跑的 run）；"
             "某引擎缺该 variant 即退 2、不回落默认。推送归部署方（`gherkai deploy push-worker`）。"
             "local 后端忽略（那边的确定性 step 直接从 --steps-dir 读、不经镜像）",
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
    pl = sub.add_parser("plan", help="预检 .feature：看 scope/job 分组 + 校验配置，不真跑（零费用）")
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
    _add_selection_flags(pl)
    pl.add_argument("--json", action="store_true", help="输出机器可读 JSON（scope/job 分组）")
    pl.add_argument(
        "--steps-dir", default=None, metavar="DIR",
        help=_STEPS_DIR_HELP + "——预检的派发标注据此反映你自己的 step",
    )
    pl.add_argument(
        "--expose-local", default=None, metavar="ORIGIN",
        help="仅作标注：plan 显示替换前的原始地址（plan 不起隧道、零副作用；公网 URL 只在真跑时才有）",
    )

    # ---- 无状态跑批（ADR 0034）：submit 提交完就走 / status 轮询收集 ----
    # local 档：submit setsid fork 一个 per-run 进程跑 reconcile loop（本机推进，无需常驻），CLI 立即退出。
    sm = sub.add_parser("submit", help="[无状态跑批] 提交一批 .feature 到后台跑、立即返回 run_id（提交完就走）")
    sm.add_argument("features", nargs="+", type=Path, help="一个或多个 .feature 路径")
    sm.add_argument("--default-engine", choices=sorted(_names.ENGINES), default="novaact",
                    help="未标 @engine 的 scope 用的默认引擎")
    _add_selection_flags(sm)
    sm.add_argument("--assertion-votes", type=int, default=1, metavar="N", help="AI 断言投票次数（默认 1）")
    sm.add_argument("--max-concurrency", type=int, default=1,
                    help="同时在跑的 worker 上限（默认 1）；随提交记录生效，cloud 档受部署侧上限"
                         "（后端 stack 的 MAX_CONCURRENCY）钳制")
    sm.add_argument(
        "--default-job-timeout", type=float, default=300.0, metavar="S",
        help="未标 @timeout 的 scope 用的 job 墙钟超时秒（默认 300；<=0 表示不超时）；标了 @timeout:N 的按 tag 走",
    )
    sm.add_argument(
        "--expose-local", default=None, metavar="ORIGIN",
        help="经隧道暴露本机可达的被测应用（语义同 run；submit 后隧道由后台进程持有——local=per-run 进程、"
             "cloud=隧道守护进程，本机需保持开机联网直到 run 终态）",
    )
    sm.add_argument(
        "--tunnel", choices=sorted(_tunnel_providers()), default="ngrok",
        help="--expose-local 用的隧道 provider（默认 ngrok）",
    )
    sm.add_argument(
        "--tunnel-ttl", type=float, default=None, metavar="S",
        help="[cloud + --expose-local] 隧道守护进程的兜底 TTL 秒（默认 = 本批各 job 预算之和 + 启动余量）；"
             "给了就用本值。TTL 到点无条件拆隧道，调小可能在 run 未完时断隧道",
    )
    sm.add_argument("--report-dir", default="reports", metavar="DIR",
                    help="归集报告落点（默认 reports/）；cloud 档须与后端部署的 REPORT_DIR 一致"
                         "（preflight 比对，不一致退 2）")
    sm.add_argument(
        "--steps-dir", default=None, metavar="DIR",
        help=_STEPS_DIR_HELP + "。值随提交记录走，本机后台推进/接力进程都读回同一份；"
             "[--backend cloud] 不生效（云端 worker 的 steps 烙在定制镜像里，警告不拦）",
    )
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
    sm.add_argument(
        "--worker-variant", default=None, metavar="NAME",
        help="[cloud] 云端 worker 镜像 variant（语义同 run）：缺省用部署的默认指针；提交时解析成各引擎的"
             "精确 task-def revision 写进提交记录（云端照它起 task）。local 后端忽略",
    )
    # 注：submit 不收 --subnet/--security-group——cloud submit 只写 runs 表、不碰 SSM/ECS（ADR 0034），
    # 网络配置由 IaC 注给 reconciler/kicker Lambda 的 env（曾在此声明过两个从不生效的 flag，已删）。

    st = sub.add_parser("status", help="[无状态跑批] 查一个 run 的进度/结果（--wait 轮询到完成）")
    st.add_argument("run_id", help="submit 返回的 run_id")
    st.add_argument("--backend", choices=["local", "cloud"], default="local", help="须与 submit 一致")
    st.add_argument("--report-dir", default="reports", metavar="DIR",
                    help="run 落点（local）/ 后端报告前缀（cloud）——须与 submit 一致；终态时据此打印报告与判定明细位置")
    st.add_argument("--wait", action="store_true",
                    help="轮询到 run 达终态再返回（两路都支持，接力语义异：local=本机 tick 推进；"
                         "cloud=检测卡住即触发云端接力）")
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

    le = sub.add_parser("list-engines", help="列出可用引擎及其 spawn 命令")
    le.add_argument("--json", action="store_true", help="输出机器可读 JSON（每引擎 available/cmd/source/hint）")

    dr = sub.add_parser("doctor", help="自检环境（只读）：引擎 worker、steps 目录、凭证、后端资源与版本、部署工具链；必修项全过退 0，任一必修项失败退 2（可选能力缺失只标 -）")
    dr.add_argument("--backend", choices=["local", "cloud"], default="local",
                    help="cloud（或给了 --prefix）时连带查凭证与后端；local 只查本机")
    dr.add_argument("--prefix", default=None, metavar="P", help="[cloud] 资源名前缀（须与部署一致）")
    dr.add_argument("--region", default=None, metavar="R")
    dr.add_argument("--profile", default=None, metavar="NAME")
    dr.add_argument("--report-dir", default="reports", metavar="DIR", help="[cloud] 与后端报告前缀比对（须与 submit 用的一致）")
    dr.add_argument("--steps-dir", default=None, metavar="DIR", help=_STEPS_DIR_HELP)
    dr.add_argument("--json", action="store_true", help="输出机器可读 JSON（{ok, checks[]}）")

    # list-deterministic：按引擎查询确定性 step 能力清单（ADR 0036：worker 自述，feature 作者可发现）
    ld = sub.add_parser("list-deterministic", help="列出指定引擎支持的确定性 step（供 feature 作者复用；零费用）")
    ld.add_argument("--engine", choices=sorted(_names.ENGINES), default="novaact",
                    help="查哪个引擎的注册表（默认 novaact，对齐 run 的 --default-engine 缺省）")
    ld.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ld.add_argument(
        "--steps-dir", default=None, metavar="DIR",
        help=_STEPS_DIR_HELP + "——清单据此含使用方定制 step（自述入口同样加载该目录）",
    )

    # [部署方] 云端后端的供给面（ADR 0037 决策 6）：命令面在皮、IaC 在 provider 包（`gherkai[deploy-aws]`）。
    # 皮绝不 import aws_cdk——只发现 provider、贴它的 flag、分派动作（契约见 gherkai_cli/deploy.py 顶部）。
    _deploy.add_parsers(sub, provider=provider, provider_error=provider_error,
                        cli_version=_installed_version())
    return p


def _tunnel_providers() -> list[str]:
    from gherkai_runtime.tunnel import PROVIDERS

    return list(PROVIDERS)


def _steps_dir_or_error(args) -> "tuple[str | None, str | None]":
    """`_resolve_steps_dir` 的**不打印**内核：返回 (绝对路径 | None, 错误串 | None)。doctor 把错误串放进机读 detail；
    其余调用点经 `_resolve_steps_dir` 打印并退 2。判据见 `_resolve_steps_dir` docstring。"""
    for value, origin in ((getattr(args, "steps_dir", None), "--steps-dir"),
                          (os.environ.get("GHERKAI_STEPS_DIR"), "env GHERKAI_STEPS_DIR")):
        if value:
            if not Path(value).is_dir():
                return None, (f"{origin}={value!r} 不是目录：其中的确定性 step 一条都加载不了。"
                              "静默跳过等于把这些 step 悄悄换成 AI 判定（可能假绿），故拒绝运行")
            return str(Path(value).resolve()), None
    default = Path("steps")
    return (str(default.resolve()) if default.is_dir() else None), None


def _resolve_steps_dir(args) -> "str | int | None":
    """解析使用方确定性 step 目录（ADR 0037 决策 4）：`--steps-dir` > env `GHERKAI_STEPS_DIR` > 默认 `./steps`
    （相对**本进程** CWD、存在才用）→ 绝对路径，或 None（无使用方 step，worker 只有内建脚手架）。

    解析只在提交侧做一次（值随 definition 走给起 worker 的宿主，见 `RunMeta.steps_dir`）；**绝对化是硬要求**
    ——worker 是 cwd 与 CLI 不同的子进程（定位链后多为继承调用者 CWD，ADR 0037 决策 3），相对路径两侧解析不同。

    **显式给的（flag / env）不是目录 → 退 2**：静默忽略等于把该目录里的确定性 step 悄悄换成 AI catch-all、
    run 还可能「通过」——本项目最忌的静默降级（与 ADR 0037 决策 4「加载失败 fail-loud」同源立场）。默认
    `./steps` 不同：「没这个目录」是多数项目的常态、不是错，故只在存在时才用。
    返回 int（2）时调用方原样返回（同 `_load_and_plan`/`_setup_tunnel` 的失败即退出码惯例）。
    """
    steps_dir, err = _steps_dir_or_error(args)
    if err:
        _progress(err)
        return 2
    return steps_dir


def _resolve_steps_dir_for_backend(args) -> str | int | None:
    """`_resolve_steps_dir` + cloud 档清零（ADR 0037 决策 4）：cloud 档 steps 烙在定制镜像里（0038），definition
    里的本机路径对云端 worker 无意义 → 不写该字段；用户显式给了则警告不拦（no-op，不改产物落点）。run/submit 共用。"""
    steps_dir = _resolve_steps_dir(args)
    if isinstance(steps_dir, int) or args.backend != "cloud":
        return steps_dir
    if args.steps_dir:
        _progress("注：--backend cloud 下 --steps-dir 不生效——云端 worker 的确定性 step 烙在定制镜像里"
                  "（构建镜像时 COPY steps/），本机目录进不了容器")
    return None


def _preflight_worker_runtimes(jobs, steps_dir: str | None) -> int | None:
    """本次 plan 用到的各引擎：worker 运行时能否定位 + （给了 steps 目录时）能否完成自述（ADR 0037 决策 3/4）。

    - 定位链四级全 miss → 打安装指引 + **退 2**：「运行时没装」是环境/配置问题，属「没开跑就被拒」层，
      不该变成一批 job 级 `engine_error`（更不该跑掉一半才发现）。
    - steps 目录已解析 → 以 `--list-deterministic` 自述入口探一次：worker 非零退出（典型 = 使用方 steps 文件
      加载失败，fail-loud）→ 转述其诊断 + **退 2**。否则 `submit` 会「提交成功」后逐 job error、诊断只落
      reconcile.log——那是静默降级（ADR 0037 决策 4「提交侧同样前置」）。
    **只查本次用到的引擎**——另一个引擎没装不连坐（dev 下 midscene 常态未装）。返回 2 或 None。
    cloud 执行档不调用本函数：那档 worker 在 Fargate 容器里跑，本机定位链无关。
    """
    for engine in sorted({j.engine for j in jobs}):
        try:
            compose.resolve_worker_cmd(engine)
        except compose.WorkerNotFoundError as e:
            _progress(f"引擎运行时缺失，拒绝运行：{e}")
            return 2
        if steps_dir is None:
            continue
        try:
            compose.query_deterministic(engine, steps_dir=steps_dir)
        except compose.WorkerSelfDescribeError as e:
            _progress(f"使用方 steps 加载失败（引擎 {engine}），拒绝运行：{e}")
            return 2
        except (ValueError, RuntimeError) as e:  # 超时/输出非 JSON：worker 连自述都做不到，跑 job 也没戏
            _progress(f"引擎 {engine} 的 worker 自述失败，拒绝运行：{e}")
            return 2
    return None


def _cmd_list_deterministic(args) -> int:
    """按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern
    语义（ADR 0022「匹配放 worker」红线）。纯本地、零 AWS。"""
    steps_dir = _resolve_steps_dir(args)  # 自述入口同样加载 steps 目录 → 清单含定制 step（ADR 0037 决策 4）
    if isinstance(steps_dir, int):
        return steps_dir
    try:
        entries = compose.query_deterministic(args.engine, steps_dir=steps_dir)
    except (ValueError, RuntimeError) as e:  # 含 WorkerNotFoundError（定位链 miss，其消息自带安装指引）
        _progress(f"list-deterministic 失败：{e}")
        return 2
    if args.json:
        print(json.dumps({"engine": args.engine, "deterministic_steps": entries}, ensure_ascii=False, indent=2))
        return 0
    print(f"引擎 {args.engine} 的确定性 step（{len(entries)} 条；由该引擎 worker 的注册表维护）：")
    if not entries:
        print("  （空——该引擎当前没有注册任何确定性 step，全部 step 走 AI）")
    for e in entries:
        print(f"  - {e.get('description', '（无描述）')}")
        print(f"    示例: {e.get('example', '')}")
        print(f"    模式: {e.get('pattern', '')}")
    return 0


def _probe_engines() -> list[dict]:
    """两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source, hint}。list-engines 与 doctor 共用。"""
    rows: list[dict] = []
    for name in sorted(_names.ENGINES):
        try:
            wc = compose.resolve_worker_cmd(name)
            rows.append({"engine": name, "available": True, "cmd": list(wc.cmd), "cwd": wc.cwd, "source": wc.source, "hint": None})
        except compose.WorkerNotFoundError as e:
            rows.append({"engine": name, "available": False, "cmd": None, "cwd": None, "source": None, "hint": str(e)})
    return rows


def _cmd_list_engines(args) -> int:
    """列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。

    **恒退 0**：本命令是「告诉我这台机器上环境什么样」的诊断，某引擎没装正是要展示的信息、不是命令失败
    （要判「装了没」的脚本请看具体引擎那行，或用 run/list-deterministic 的退 2）。--json 给机读行（ADR 0041 决策三）。
    """
    rows = _probe_engines()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    print("可用引擎（本机 worker 运行时的探测结果）：")
    for r in rows:
        if not r["available"]:
            print(f"  - {r['engine']}: <未定位到 worker 运行时>")
            print(f"    {r['hint']}")
            continue
        print(f"  - {r['engine']}: {' '.join(r['cmd'])}")
        print(f"    来源: {r['source']}" + (f"    cwd: {r['cwd']}" if r["cwd"] else ""))
    return 0


def _cmd_doctor(args) -> int:
    """只读自检（ADR 0041 决策四）：一个入口、按组件分组；每项 {section, name, ok, required, detail}。
    **退出码只看 required 项**：全过退 0，任一 required 项 fail 退 2；required=False 的项失败只作能力展示（另一个引擎
    没装、没装 deploy-aws extra、容器引擎 daemon 没起）。不给 --backend cloud / --prefix 时只查本机。
    provider 段经 deploy 接缝调 provider 可选的 `doctor(args) -> list[dict]`（部署方工具链归 provider 自查，入口只编排）。"""
    checks: list[dict] = []

    def add(section: str, name: str, ok: bool, detail: str, *, required: bool = True) -> None:
        checks.append({"section": section, "name": name, "ok": bool(ok), "required": required, "detail": detail})

    add("cli", "version", True, f"gherkai {_dist_version()}，Python {sys.version.split()[0]}", required=False)

    rows = _probe_engines()
    for r in rows:
        add("engines", r["engine"], r["available"],
            (" ".join(r["cmd"]) + f"（{r['source']}）") if r["available"] else r["hint"], required=False)
    any_engine = any(r["available"] for r in rows)
    add("engines", "any", any_engine,
        "至少一个引擎的 worker 可用" if any_engine
        else "两个引擎的 worker 都没定位到：local 档一个 job 也起不来（只提交 cloud 档的人可忽略本项）",
        required=(args.backend != "cloud"))

    steps_dir, steps_err = _steps_dir_or_error(args)
    if steps_err:
        add("steps", "dir", False, steps_err)
    elif steps_dir is None:
        add("steps", "dir", True, "无 steps/ 目录：只有内建确定性 step（多数项目的常态）", required=False)
    else:
        add("steps", "dir", True, steps_dir, required=False)
    if not steps_err:
        # 对每个可用引擎跑一次 worker 自述：有 steps 目录 = 使用方 step 能否加载（必修——加载失败会静默降级成 AI，ADR 0037
        # 决策 4 fail-loud）；没有 = 只验「worker 起得来、能自述」（可选：单引擎不连坐，与 engines.<engine> 同档）
        for r in rows:
            if not r["available"]:
                continue
            try:
                n = len(compose.query_deterministic(r["engine"], steps_dir=steps_dir))
                add("steps", f"load.{r['engine']}", True,
                    f"{n} 条确定性 step（含内建）" + ("" if steps_dir else "；无 steps/ 目录，仅内建"),
                    required=steps_dir is not None)
            except Exception as e:  # 自述失败 = 使用方 steps 加载失败 / worker 起不来，原样转述
                add("steps", f"load.{r['engine']}", False, f"worker 自述失败：{e}", required=steps_dir is not None)

    want_cloud = args.backend == "cloud" or args.prefix is not None
    if not want_cloud:
        add("aws", "identity", True, "未查（给 --backend cloud 或 --prefix 才查云端）", required=False)
        add("backend", "reachability", True, "未查（同上）", required=False)
    else:
        cred_fail = "凭证/region 不可用（--region / AWS_REGION / --profile）：{e}"
        try:
            # region 落实要读 profile config：profile 名不存在在这里就炸，与探针失败共用一句诊断（对 agent 是同一件事）
            target = compose.resolve_cloud_target(prefix=args.prefix, region=args.region, profile=args.profile)
        except Exception as e:
            add("aws", "identity", False, cred_fail.format(e=e))
            add("backend", "reachability", False, "未查：凭证先过不了", required=False)
        else:
            _doctor_cloud(args, target, add, cred_fail)

    _doctor_provider(args, add)

    ok_all = all(c["ok"] or not c["required"] for c in checks)
    if args.json:
        print(json.dumps({"ok": ok_all, "checks": checks}, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            mark = "✓" if c["ok"] else ("✗" if c["required"] else "-")
            print(f"{mark} {c['section']}.{c['name']}: {c['detail']}")
        if any(c["section"] == "provider" and not c["ok"] for c in checks):
            print("\n部署工具链有缺口（provider 段）：只影响 gherkai deploy / push-worker，不影响提交与本机跑")
        print("\n自检通过" if ok_all else "\n自检有失败项（✗ 为必修；- 为可选能力缺失）")
    return 0 if ok_all else 2


def _doctor_cloud(args, target, add, cred_fail: str) -> None:
    """doctor 的 aws / backend 两段（拆出来只为 `_cmd_doctor` 读得下去）：region → 身份 → 版本 → 资源 → 默认 worker variant。"""
    if target.region is None:
        add("aws", "region", False, "没解析出 region：给 --region，或设 AWS_REGION / AWS_DEFAULT_REGION，或让 --profile 指的 profile 配置里带 region")
        add("backend", "reachability", False, "未查：region 还没解析出来", required=False)
        return
    add("aws", "region", True, target.region)
    try:
        ident = compose.probe_aws_identity(region=target.region, profile=target.profile)
    except Exception as e:
        add("aws", "identity", False, cred_fail.format(e=e))
        add("backend", "reachability", False, "未查：凭证先过不了", required=False)
        return
    add("aws", "identity", True, f"身份 {ident['arn']}")
    backend_version = None
    try:
        verdict, msg, backend_version = compose.check_backend_skew(
            prefix=target.prefix, cli_version=_installed_version(), region=target.region, profile=target.profile)
        add("backend", "version", verdict != compose.SKEW_BLOCK,
            msg or f"后端 {backend_version}，CLI {_installed_version()}：一致")
    except Exception as e:
        add("backend", "version", False, f"读不到后端版本戳（prefix 配错或后端未部署？）：{e}")
    try:
        err = compose.preflight_cloud_resources(
            prefix=target.prefix, events_table=target.events_table, bucket=target.bucket,
            cluster=target.cluster, runs_table=target.runs_table,
            task_defs=[compose.task_def_name(target.prefix, e) for e in sorted(_names.ENGINES)],
            lambda_fns=target.detached_chain_lambdas, report_dir=args.report_dir,
            region=target.region, profile=target.profile)
        add("backend", "resources", err is None,
            err or "runs/events 表、桶、cluster、两引擎 task-def、三个 Lambda 都在；报告前缀与 --report-dir 一致")
    except Exception as e:
        add("backend", "resources", False, f"探资源失败：{e}")
    # 默认 worker variant：先读指针，再**逐引擎**解析（单引擎团队不必为另一个引擎推镜像，同 submit 只按用到的引擎判），
    # 至少一个引擎解析得开即算过（聚合项 worker.any，对称 engines.any）
    try:
        default_variant = compose.read_worker_default(prefix=target.prefix, region=target.region, profile=target.profile)
    except Exception as e:
        add("backend", "worker.default", False, f"读不到默认 worker variant 指针：{e}")
        return
    if default_variant is None:
        add("backend", "worker.default", False,
            "后端没有默认 worker variant 指针——请部署方跑一次 gherkai deploy 初始化；或提交时用 --worker-variant 显式指定")
        return
    add("backend", "worker.default", True, f"默认 variant {default_variant}", required=False)
    resolved_any = False
    for eng in sorted(_names.ENGINES):
        try:
            res = compose.resolve_worker_variant(
                prefix=target.prefix, variant=default_variant, engines=[eng], cli_version=_installed_version(),
                backend_version=backend_version, region=target.region, profile=target.profile)
            resolved_any = True
            add("backend", f"worker.{eng}", True, f"variant {res[eng].variant} → {res[eng].revision_arn}", required=False)
        except Exception as e:
            add("backend", f"worker.{eng}", False, str(e), required=False)
    add("backend", "worker.any", resolved_any,
        "至少一个引擎解析到 worker 镜像" if resolved_any
        else "两个引擎都解析不到默认 variant 的镜像：cloud 档一个 job 也起不来（见上各引擎那行的指引）")


def _doctor_provider(args, add) -> None:
    """doctor 的 provider 段：按 entry point 结构化判「没装 / 装了多个 / 装了但坏 / 装了且可自检」，别靠匹配错误文案。
    provider 段是**部署能力清单**：装了但加载失败算必修（明确装了的东西坏了）；provider 自报的工具链缺项按它给的 required
    （缺省可选），入口在人读尾行单独点出。"""
    eps = _deploy.provider_entry_points()
    if not eps:
        add("provider", "deploy-aws", True, "未装 [deploy-aws] extra（只有部署方需要）", required=False)
        return
    provider, perr = _deploy.resolve_provider(None)
    if provider is None and len(eps) > 1:
        add("provider", "deploy-aws", True, perr or "装了多个部署 provider：本项未查", required=False)  # 不是故障，doctor 不替用户猜哪个云
        return
    if provider is None:
        add("provider", "deploy-aws", False, perr or "provider 不可用")
        return
    if not hasattr(provider, "doctor"):
        add("provider", getattr(provider, "name", "provider"), True, "provider 未提供自检", required=False)
        return
    try:
        for c in provider.doctor(args):
            add("provider", c["name"], c["ok"], c["detail"], required=c.get("required", False))
    except Exception as e:
        add("provider", getattr(provider, "name", "provider"), False, f"provider 自检出错：{e}", required=False)


def _load_and_plan(args) -> "list | int":
    """plan 与 run 的共享前置装配：votes 校验 → 读 feature → plan。

    成功返回 `Job[]`；任一前置失败返回**退出码 2**（配置矛盾/读不到/语法错，均"没开跑就被拒"，
    对齐 cli/README 退出码分层）。_cmd_plan 与 _cmd_run 都调它（曾各手抄一份、会漂移）。
    """
    # 0) 校验：assertion_votes 必须 ≥1。否则 worker 跑 0 次 AI 断言——votes=0 全判失败（假阴性）、
    #    votes<0 更危险：0 > 负数/2 = True → **零 AI 调用却全绿**（假阳性）。入口拦截，不让坏值流进 worker。
    if args.assertion_votes < 1:
        _progress(f"--assertion-votes 必须 ≥ 1（收到 {args.assertion_votes}）：投票次数 <1 会让 AI 断言不被执行")
        return 2
    # 筛选 flag 的空值拒收（ADR 0041 决策一）：空值静默降级成「不筛、跑全批」是最贵的静默错误（整批真跑）
    for raw in (getattr(args, "tags", None) or []):
        if not {t.strip().lstrip("@") for t in raw.split(",") if t.strip().lstrip("@")}:
            _progress(f"--tags 的值不能为空（收到 {raw!r}）：想跑全部 scenario 就别给这个 flag")
            return 2
    for raw in (getattr(args, "scenario", None) or []):
        if not raw.strip():
            _progress("--scenario 的值不能为空：给 <文件>:<行号>、行号，或标题的一段文字")
            return 2
    # 1) 读 feature（组合根的事，core 不碰 FS）→ FeatureSource[]
    try:
        features = [compose.load_feature(f) for f in args.features]
    except (OSError, UnicodeDecodeError) as e:
        # 不止「文件不存在」：给了目录（IsADirectoryError）/ 无读权限 / 非 UTF-8 编码同属「没开跑就被拒」
        # 的输入问题，一律退 2（退码语义 ADR 0021），不让它们以 traceback 形态逃出。
        _progress(f"读 feature 失败：{e}")
        return 2
    # 2) plan：.feature → Job[]（uri 互异/engine 冲突等违约 → PlanError；gherkin 语法错 → FeatureParseError）
    try:
        cfg = PlanConfig(
            default_engine=args.default_engine,
            default_assertion_votes=args.assertion_votes,
            # 两层设定的缺省层（ADR 0019 @timeout / ADR 0034「job timeout」节）：标了 @timeout: 的 scope
            # 按 tag 走，未标的用本缺省；<=0 → None=不超时。载体在 definition（Job.timeout_s），
            # 三路推进器（同步 schedule / local per-run / cloud）各自 enforce。
            default_job_timeout_s=(args.default_job_timeout if args.default_job_timeout > 0 else None),
        )
        select = _build_selector(args)
        jobs = plan(features, cfg, select=select)
        if select is not None:
            # 筛选（ADR 0041 决策一）：筛空退 2 并列全部候选——别静默跑空批；有筛掉的就打一行 N/M 让人/agent 确认没选错。
            # 候选与总数直接 parse（不再调一次 plan：那会把跨文件 scope 合并的 warning 打两遍），顺带带上 tags 便于改 --tags。
            from gherkai_core.parse import parse_feature
            everything = [p for f in features for p in parse_feature(f.uri, f.text)]
            picked = sum(len(j.scenarios) for j in jobs)
            if not jobs:
                _progress(f"没有 scenario 匹配 {_selection_label(args)}。本批可选（id  标题  tags）：")
                for p in everything:
                    _progress(f"  {p.scenario.id}  {p.scenario.name}  {' '.join(p.tags)}")
                return 2
            if picked < len(everything):
                _progress(f"筛选：{picked}/{len(everything)} scenario（{_selection_label(args)}）")
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
        _progress(f"--max-concurrency={mc} 无效：须 ≥ 1（<=0 会让 run 永不起 job、卡死在 pending）")
        return False
    return True


def _validate_worker_variant(args) -> bool:
    """`--worker-variant` 入口校验 + local 档提示（对齐 `--max-concurrency` 的入口校验惯例，ADR 0038）。

    **校验点复用 `names.image_tag`**：variant 名最终要拼进 ECR/docker 镜像 tag，字符集与归一化由那一处单点
    持有（ADR 0038「tag 命名 = 单一真源、同时是单一校验点」）——此处拿本 CLI 自己的版本试拼一次，坏名字在
    「没开跑就被拒」层退 2，而不是拖到 preflight 读 SSM 后报一句绕远的「该 variant 没有映射」。
    **local 档只提示不校验**：该 flag 在 local 完全不参与（确定性 step 直接从 steps 目录读、不经镜像），
    对一个从不消费的值做硬校验没有意义——同 cloud 档遇到 `--steps-dir` 时「警告不拦」的口径。
    用 getattr 取值：`plan` 等子命令没有这个 flag（也没有 `--backend`），取不到就不校验。返回 False = 调用方退 2。
    """
    variant = getattr(args, "worker_variant", None)
    if variant is None:
        return True
    if getattr(args, "backend", None) != "cloud":
        _progress("--worker-variant 不生效：worker 镜像 variant 只作用于 --backend cloud"
                  "（local 档的确定性 step 直接从 steps 目录读、不经镜像）")
        return True
    try:
        _names.image_tag(_dist_version(), variant)
    except ValueError as e:
        _progress(f"--worker-variant 无效：{e}")
        return False
    return True


def _probe_deterministic_dispatch(jobs, steps_dir: str | None) -> dict | None:
    """plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。

    返回 {(scope_id, scenario_id, step_index): probe} 或 None（全部引擎都没问成）。match 用**裸 step 文本**
    ——与 worker 真跑派发的匹配面完全一致（不 unquote、不拼 argument，ADR 0024）。按引擎 best-effort：
    某引擎查询失败只让该引擎的 job 无标注（stderr 警告），不影响其他引擎与 plan 本体——**含定位链 miss**
    （该引擎运行时没装，ADR 0037 决策 3 明确 plan 保持本降级、不像 run/submit 那样退 2）。**例外**：worker
    起来了但自述非零退出（WorkerSelfDescribeError，典型 = 使用方 steps 加载失败）原样抛出、由 `_cmd_plan` 退 2
    ——那是使用方代码错误，降级成无标注等于静默把定制 step 换成 AI（ADR 0037 决策 4）。
    steps_dir 透传给 worker 自述入口，使标注反映使用方定制 step（ADR 0037 决策 4）。
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
            probes = compose.match_deterministic(engine, [t for _, t in items], steps_dir=steps_dir)
        except compose.WorkerSelfDescribeError:
            raise  # 使用方 steps 加载失败：不降级、由 _cmd_plan 退 2（ADR 0037 决策 4「提交侧同样前置」）
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


def _cmd_plan(args) -> int:
    """plan 预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。
    **零 AWS、零花费、零副作用**（标注会起本地瞬时 worker 子进程做 match 自述——非跑 job；失败自动降级）。

    与 _cmd_run 共用 `_load_and_plan`（votes 校验 + load_feature + plan），但到此为止——
    省钱验证 feature 写法、看分组、暴露 PlanError。退出码与 run 一致（0 ok / 2 配置错）。
    """
    jobs = _load_and_plan(args)
    if isinstance(jobs, int):  # 前置失败 → 退出码
        return jobs
    steps_dir = _resolve_steps_dir(args)
    if isinstance(steps_dir, int):
        return steps_dir

    # 派发预期标注（ADR 0036 决策 4）：按引擎批量问 worker「哪些 step 命中确定性」。best-effort——
    # 引擎环境未装/查询失败只降级为无标注+stderr 警告，plan 核心功能保持零依赖（不因标注挂掉）。
    try:
        dispatch = _probe_deterministic_dispatch(jobs, steps_dir)
    except compose.WorkerSelfDescribeError as e:
        _progress(f"使用方 steps 加载失败，plan 拒绝出结果（否则标注静默缺失 = 定制 step 被悄悄换成 AI）：{e}")
        return 2

    # 核心产出 → stdout（与 run 的输出契约一致：--json 单文档 / 否则人看文本）
    if args.json:
        print(json.dumps(render.plan_to_dict(jobs, args.default_engine, dispatch), ensure_ascii=False, indent=2))
    else:
        print(render.render_plan_text(jobs, args.default_engine, dispatch))
    if dispatch and any(p_ and "conflict" in p_ for p_ in dispatch.values()):
        # 「一条 step 最多命中一条模式」是注册表侧的硬约束（判据见 ADR 0022）；下面这句是产品面文案。
        _progress("⚠ 存在命中多条确定性模式的 step（见上标注）：真跑时这些 step 将 error——"
                  "请收紧注册表模式，让每条 step 只命中一条。")
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


def _cmd_submit(args) -> int:
    """[无状态跑批] 提交完就走（ADR 0034）：plan → 写 RunMeta+全 pending → 起首轮推进 → 打印 run_id → 立即退出。

    - **local**：setsid fork per-run 进程跑 reconcile loop 本机推进（无需常驻服务/云）；崩了 status --wait 接力。
    - **cloud**：只 create_run 写 definition 到 DDB（不起 task）→ 之后云端 Lambda 事件驱动链推进
      （runs Stream INSERT→kicker 起首批→events Stream→reconciler→…→finalize），**提交完真关机也跑完**。
      CLI 不留本机进程、submit 机器零 ECS 权限。
    退出码 = 提交成功与否（非 run 判定；判定由 status 查）。
    """
    if not _validate_max_concurrency(args):  # 最早：读 feature/起隧道/preflight 之前（真零副作用）
        return 2
    if not _validate_worker_variant(args):   # 同上层（入口校验，ADR 0038）；local 档在此只打一行「不生效」
        return 2
    jobs = _load_and_plan(args)
    if isinstance(jobs, int):
        return jobs
    _progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")

    # worker 运行时 preflight（ADR 0037 决策 3 miss 分叉）：**仅 local 档**——per-run 进程在本机 spawn worker，
    # 定位链 miss 要在提交前退 2（否则提交成功、后台每个 job 都 engine_error）。cloud 档 worker 在 Fargate，
    # 本机没有也正常（cloud 的镜像/task-def 由 _submit_cloud 的 preflight 探）。**排在起隧道之前**（零副作用）。
    # 使用方确定性 step 目录（ADR 0037 决策 4）：提交侧解析一次、随 definition 走给 per-run/接力宿主。
    steps_dir = _resolve_steps_dir_for_backend(args)
    if isinstance(steps_dir, int):
        return steps_dir
    if args.backend != "cloud":
        miss = _preflight_worker_runtimes(jobs, steps_dir)
        if miss is not None:
            return miss

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
                       max_concurrency=args.max_concurrency,
                       steps_dir=steps_dir)  # cloud 档恒 None（上面已置），local 档随 definition 到达宿主
    from gherkai_core.model import JobState, RunState
    initial = RunState(
        run_id=run_id, status=Status.PENDING,
        jobs={j.scope_id: JobState(scope_id=j.scope_id, status=Status.PENDING) for j in jobs},
        started_at=compose.now_iso(), high_water_mark=0,
    )

    if args.backend == "cloud":
        rc_ = _submit_cloud(args, run_id, run_meta, initial, tunnel_info=tunnel_info)
    else:
        rc_ = _submit_local(args, run_id, run_meta, initial, tunnel_info=tunnel_info)
    if rc_ != 0 and tunnel_info is not None:
        from gherkai_runtime.tunnel import stop_tunnel

        stop_tunnel(tunnel_info.pid)  # 提交失败 → 隧道无宿主可交棒，就地拆（成功路径由后台宿主收尾）
    return rc_


def _submit_local(args, run_id: str, run_meta, initial, *, tunnel_info=None) -> int:
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
    # cwd 继承提交进程、不再指向仓库根（分发后没有 repo，ADR 0037 决策 3）；per-run 所需路径都经参数/definition 传。
    _sp.Popen(cmd, start_new_session=True,
              stdin=_sp.DEVNULL, stdout=log_f, stderr=log_f)
    log_f.close()  # 子进程已持有 fd（Popen 继承），父进程侧句柄即关
    _progress(f"已提交（本机后台推进中）。查进度：gherkai status {run_id} --report-dir {args.report_dir}")
    print(run_id)
    return 0


def _cloud_skew_gate(target) -> "tuple[int | None, str | None]":
    """cloud 路径的**第一道闸**：CLI 与后端的版本 skew 三态（ADR 0037 决策 7）。
    返回 `(退出码 or None, 后端版本戳 or None)`——放行 = `(None, 戳)`，拦下 = `(2, …)`。

    **必须先于资源 preflight**（决策 7 的次序）：skew 的修复动作是部署方跑一次 `gherkai deploy`，而那一步同时
    把资源建齐/补齐——先报「表/task-def 不存在」只会把人引去查 `--prefix`，绕一圈回到同一个动作。
    三个不拦的档（戳缺失 / CLI 偏旧 / 任一侧 dev 版）只打一行提示；**block 无放行 flag**（决策 7 明拒）。

    **戳一并返回、全程只读一次**：worker variant 解析（ADR 0038「运行时与 preflight」）要拿同一个戳给出
    skew 感知的提示语（与后端同版本 → 指向 `push-worker`；CLI 偏旧 → 指向升级 CLI，不引导去推一个旧版本
    tag 的镜像）。读戳 + 判定住产品本体（`compose.check_backend_skew`，第三元即戳；WebUI/推进器同调，措辞单点），
    本函数只把 verdict 翻成退出码。
    比的是**本 CLI 自己的**版本（`_installed_version()`，而非产品本体包的）——`gherkai deploy` 往 SSM 写的戳就是它，
    它也是写任务定义的那一方；两者靠 `==` lockstep 恒同版本，显式传免得读者去猜哪个；未装成包 → None → 跳过。
    读戳与 subnet/sg 同一条 session/region 解析，且戳落在已授的 `/{prefix}backend/*` 通配内、不新增授权。
    """
    try:
        verdict, msg, backend_version = compose.check_backend_skew(
            prefix=target.prefix, cli_version=_installed_version(), region=target.region, profile=target.profile)
    except ImportError as e:
        _progress(f"--backend cloud 需要 boto3：{e}")
        return 2, None
    except Exception as e:
        if compose.is_botocore_error(e):
            _progress(f"--backend cloud 读版本戳失败（SSM {_names.ssm_path(target.prefix, _names.BACKEND_VERSION_KEY)}"
                      f"——凭证/region/权限？）：{e}")
            return 2, None
        raise
    if msg:
        _progress(msg)
    return (2 if verdict == compose.SKEW_BLOCK else None), backend_version


def _cloud_worker_variant_gate(args, target, engines, *, backend_version) -> "int | dict":
    """cloud preflight 的**第三道闸**：把 `--worker-variant`（缺省 = 部署级默认指针）解析成本 run 用到的
    每个引擎的 task-def revision（ADR 0038「运行时与 preflight」）。放行 → `{engine: WorkerResolution}`；拦下 → 2。

    **次序 = 版本 skew → 资源 preflight → 本闸**（ADR 0038 明写）：skew 的修复动作（`gherkai deploy`）本身就是
    镜像重推的前置，反过来先报「variant 没推」会让用户白推一轮（推完还得因 skew 重来）。
    **engines 只含本 run 真用到的引擎**——对齐既有 task-def 判据「不探全注册表，没用到的引擎不该拦」：单引擎
    团队不必为另一个引擎凭空推镜像。
    **严格退 2、不回落默认**：静默换一套确定性 step 集与「不判 steps 内容」的分工矛盾（ADR 0038 被拒方案）；
    提示语（含「同版本 → push-worker」/「CLI 偏旧 → 升级 CLI」的分叉）由 `WorkerVariantError` 自带，此处原样转述。
    """
    try:
        resolutions = compose.resolve_worker_variant(
            prefix=target.prefix, variant=getattr(args, "worker_variant", None),
            engines=engines, cli_version=_installed_version(), backend_version=backend_version,
            region=target.region, profile=target.profile,
        )
    except compose.WorkerVariantError as e:
        _progress(str(e))
        return 2
    except ValueError as e:
        # `names.image_tag` 的字符集校验（唯一 ValueError 来源）。显式给的 `--worker-variant` 已在入口拦过，
        # 走到这里只剩「后端默认指针本身是个非法名」——部署侧写坏的值，同样是可修的配置错、不该冒 traceback。
        _progress(f"--backend cloud 的 worker variant 名不合法（若未给 --worker-variant，检查后端默认指针 "
                  f"SSM /{target.prefix}backend/{_names.WORKER_DEFAULT_KEY}）：{e}")
        return 2
    except ImportError as e:
        _progress(f"--backend cloud 需要 boto3：{e}")
        return 2
    except Exception as e:
        if compose.is_botocore_error(e):
            _progress(f"--backend cloud 解析 worker 镜像 variant 失败（读 SSM /{target.prefix}backend/worker-* "
                      f"或探 ECS/ECR——凭证/region/权限？）：{e}")
            return 2
        raise
    if not getattr(args, "quiet", False):  # submit 没有 --quiet（恒打印，同它其它进度行）
        for engine in sorted(resolutions):
            r = resolutions[engine]
            _progress(f"{engine}: variant {r.variant} · digest {_names.short_digest(r.digest)} · revision {r.revision_arn}")
    return resolutions


def _worker_meta_fields(resolutions: dict) -> dict:
    """variant 解析结果 → definition 字段（ADR 0038）：人读的 variant 名 + 引擎 → revision ARN。

    variant 名取任一条解析结果——「**一个 run 一个 variant 名、跨引擎同名**」是 ADR 0038 的不变量
    （某引擎缺该 variant 时上面那道闸已退 2），故各条 resolution 的 variant 恒同。
    空 dict（理论上不会有：plan 至少产一个 job）→ 两个字段都 None，走 serialize 的 omit-when-None。
    """
    if not resolutions:
        return {"worker_variant": None, "worker_task_defs": None}
    return {
        "worker_variant": next(iter(resolutions.values())).variant,
        "worker_task_defs": {e: r.revision_arn for e, r in resolutions.items()},
    }


def _submit_cloud(args, run_id: str, run_meta, initial, *, tunnel_info=None) -> int:
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

    # 版本 skew 先于资源 preflight（ADR 0037 决策 7 的次序）；戳一并拿回，供下面的 variant 解析（ADR 0038）
    skew_rc, backend_version = _cloud_skew_gate(target)
    if skew_rc is not None:
        return skew_rc

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

    # worker 镜像 variant 解析（ADR 0038）：**在资源 preflight 之后**，把 variant 落成各引擎的精确 revision ARN
    # 写进 definition——云端推进器（kicker/reconciler）照 definition 起 task，故不写进去就到不了它们。
    resolutions = _cloud_worker_variant_gate(
        args, target, sorted({j.engine for j in run_meta.jobs}), backend_version=backend_version)
    if isinstance(resolutions, int):
        return resolutions
    run_meta = replace(run_meta, **_worker_meta_fields(resolutions))

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
            _sp.Popen(cmd, start_new_session=True,  # cwd 继承提交进程（ADR 0037 决策 3），同 per-run 进程
                      stdin=_sp.DEVNULL, stdout=lf, stderr=lf)
        _progress(f"隧道由守护进程持有（日志 {watch_log}）：run 终态即拆、TTL 兜底 {ttl_s:.0f}s"
                  f"（= 各 job 预算之和 + 启动余量；`--tunnel-ttl` 可覆盖）。"
                  f"**本机需保持开机联网直到 run 终态**——关机=隧道断=测试将以导航失败告终。")
        _progress(f"已提交到云端（提交记录已落库，云端已接管推进）。查进度：gherkai status {run_id} --backend cloud --prefix {target.prefix}")
    else:
        _progress(f"已提交到云端（提交记录已落库，云端已接管推进，可关机）。查进度：gherkai status {run_id} --backend cloud --prefix {target.prefix}")
    print(run_id)
    return 0


def _render_status(state, args, *, wait_hint: str, locations: dict) -> int:
    """渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR 0034）。

    state 已确认非 None（调用方先查）。wait_hint = 各自的 `status --wait` 接力命令示例（local 用 --report-dir、
    cloud 用 --backend cloud --prefix，触发逻辑同、只命令示例异）。locations = 该 run 的产物落点（compose 单点拼，
    与 `run` 结束时打的同一份）：人读档终态才打那三行——报告/判定明细在 finalize 才落，未终态打了是空指针。
    --json 机读：RunState 键形状不变，另**附加** `artifacts`（约定落点、无论终态都给，终态后才真有内容，ADR 0041 决策三）；
    人读提示一律不打（pending 提示的触发条件见下方注释）。
    退出码：PASSED→0 / pending·running（未达终态、非 --wait）→0（查询本身成功）/ 其余终态→1。
    """
    if args.json:
        from gherkai_core.serialize import run_state_to_dict
        doc = run_state_to_dict(state)
        doc["artifacts"] = locations  # 附加键（ADR 0041 决策三）：RunState 部分形状不变；位置是约定落点、终态才真有
        print(json.dumps(doc, ensure_ascii=False, indent=2))
    else:
        print(render.render_run_state(state))
        if state.status in TERMINAL_STATUSES:
            # 与 `run` 结束时同款三行（对标输出，S3/本地路径可直接复制）；report 写失败被隔离时这里给的是约定落点
            _progress(f"\n报告: {locations['report_index']}")
            _progress(f"运行元信息: {locations['run_meta']}、{locations['run_state']}")
            _progress(f"判定明细: {locations['jobs_dir']}")
    # 疑似卡住诊断（两路一致）：非 --wait、非 json、**所有 job 仍 pending** → 提示 --wait 接力（**只提示、不自动
    # kickoff/tick**——保「查看」纯只读无副作用；救活决定权留用户，走 --wait）。判据不能只看 run 级 status：
    # 推进器 claim（CAS pending→running）只动那个 job、run 级 status 要等下一次 tick 的投影写才翻 running，而
    # 下一次 tick 要等 worker 发出第一个事件——Fargate 拉起那几十秒里恒是「job running、run pending」，此时推进
    # 早已开始，提示「推进可能未启动」是误报（真跑 submit 后连查三次撞见）。任一 job 已 claim 即闭嘴。
    all_jobs_pending = all(js.status == Status.PENDING for js in state.jobs.values())
    if not args.wait and not args.json and state.status == Status.PENDING and all_jobs_pending:
        _progress(f"提示：run 仍 pending。若已提交较久，推进可能未启动——`{wait_hint}` 可接力推进。")
    if state.status == Status.PASSED:
        return 0
    if state.status not in TERMINAL_STATUSES:  # 未达终态（查询本身成功，判定退出码留给 --wait）
        return 0
    return 1


def _cmd_status(args) -> int:
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
        # 与 per-run 进程同一入口（装配/推进/拆隧道三句只在 detached.drive_local_reconcile 写一份）。
        detached.drive_local_reconcile(str(report_root), args.run_id, args.max_concurrency,
                                       region=args.region, profile=args.profile)

    state = run_store.load_run_state(args.run_id)
    if state is None:  # 不可达（上面已查过），保险分支
        _progress(f"未找到 run：{args.run_id}（--report-dir 是否与 submit 一致？）")
        return 2
    return _render_status(state, args, wait_hint=f"gherkai status {args.run_id} --report-dir {args.report_dir} --wait",
                          locations=compose.local_artifact_locations(str(report_root), args.run_id))


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

    # 版本 skew 先于任何云端读（ADR 0037 决策 7 的次序）。**status 不解析 variant**（ADR 0038）：它只读运行态、
    # 不起 task，definition 里的 revision 是提交时定死的，重解析既无用又会把「镜像已退休」误报成查询失败。
    skew_rc, _backend_version = _cloud_skew_gate(target)
    if skew_rc is not None:
        return skew_rc

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
                        _progress(f"status --wait 接力失败：接力 Lambda {kicker_fn}（用 --prefix={target.prefix!r} 拼出）"
                                  f"不存在——是 --prefix 配错、还是后端未部署（`gherkai deploy`）？")
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
                          wait_hint=f"gherkai status {args.run_id} --backend cloud --prefix {target.prefix} --wait",
                          locations=compose.cloud_artifact_locations(
                              bucket=target.bucket, report_prefix=args.report_dir, table=target.runs_table,
                              run_id=args.run_id))


def _cmd_reconcile(args) -> int:
    """per-run 进程入口（submit setsid fork 它，非用户直接调）：跑 reconcile loop 到全 done 自退（ADR 0034）。

    **无 `--steps-dir` flag**：使用方 step 目录随 definition 走（`RunMeta.steps_dir`），由
    `build_local_reconcile` 从 RunStore 读回——本进程 CWD 与提交进程不同，重解析 `./steps` 必分叉
    （ADR 0037 决策 4）。
    """
    from gherkai_runtime import detached

    if not _validate_max_concurrency(args):  # 回落值同校验（meta 缺值时它就是并发闸）
        return 2
    report_root = Path(args.report_dir).resolve()
    detached.drive_local_reconcile(str(report_root), args.run_id, args.max_concurrency,
                                   region=args.region, profile=args.profile)
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


def _cmd_run(args) -> int:
    use_json = args.json

    if not _validate_max_concurrency(args):  # 最早：读 feature/起隧道/preflight/begin 之前（真零副作用）
        return 2
    if not _validate_worker_variant(args):   # 同上层（入口校验，ADR 0038）；local 档在此只打一行「不生效」
        return 2
    # 0/1/2) votes 校验 + 读 feature + plan（与 _cmd_plan 共享；前置失败返回退出码 2，见 _load_and_plan）
    jobs = _load_and_plan(args)
    if isinstance(jobs, int):
        return jobs

    # 进度走 stderr（不再受 --json 开关；stdout 始终只放核心产出）。--quiet 仍可静音逐事件。
    _progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")
    for j in jobs:
        _progress(f"  - scope={j.scope_id!r} engine={j.engine} scenarios={len(j.scenarios)}")

    # worker 运行时 preflight（ADR 0037 决策 3 miss 分叉）：**仅 local 执行档**（cloud 档 worker 在 Fargate，
    # 本机定位链无关）。定位链 miss → 退 2，**在 spawn 前**、不进 job 级 engine_error。排在起隧道/preflight/
    # begin 之前（只依赖 jobs，早拒才真零副作用——同 votes/grace 校验的位置理由）。
    # 使用方确定性 step 目录（ADR 0037 决策 4）：解析一次 → 写进 definition + 注给本进程起的 worker。
    steps_dir = _resolve_steps_dir_for_backend(args)
    if isinstance(steps_dir, int):
        return steps_dir
    if args.backend != "cloud":
        miss = _preflight_worker_runtimes(jobs, steps_dir)
        if miss is not None:
            return miss

    # 2a) grace 硬约束（ADR 0024）：按本 run 各引擎的下限取 max（grace 是 run 级单值）。引擎特定下限住组合根。
    #     显式给了过小 grace → 入口友好拒绝（对齐 votes 校验惯例，退 2「没开跑就被拒」）。core 侧还有 enforce
    #     兜底（任何前端都受同一护栏），此处只为在 cli 给出清晰诊断、避免 core ValueError 冒到用户面。
    #     **必须排在起隧道 / cloud preflight / persistence.begin 之前**：只依赖 jobs，早拒才真「零副作用」——
    #     否则配置错也已起 ngrok、产生云端调用费用、并落下永不 finalize 的半成品 run 记录。
    min_grace = max((compose.engine_min_grace(j.engine) for j in jobs), default=0.0)
    import math as _math
    if args.grace is not None and (not _math.isfinite(args.grace) or args.grace <= 0 or args.grace < min_grace):
        # nan/inf 同拒：inf 会让 SIGKILL 兜底永不触发（软停失效 = 挂死），与 --tunnel-ttl / @timeout 的判据同形。
        _progress(
            f"--grace={args.grace} 无效：须为有限正数且 ≥ {min_grace}s"
            "（Nova act_timeout+余量；小于单个 act 的时长会让软停失效、浏览器会话泄漏）"
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
                       max_concurrency=args.max_concurrency,
                       steps_dir=steps_dir)  # cloud 档恒 None（上面已置）
    do_report = not args.no_report  # RunReport 默认生成；--no-report 跳过（逃生舱）
    worker_log_fh = None  # --quiet（local 执行档）时打开的 worker 日志句柄，见 build_engines 处
    worker_log_path: Path | None = None
    # 两个引擎的产物落点（ADR 0027/0037 决策 3）：
    # - 归集档（默认）：落 <report_dir>/<run_id>/ 下**本次 run 专属的绝对路径**目录，与 RunReport 同处、长期留存。
    #   **必须绝对路径**：worker 是 cwd 与 cli 不同的子进程，相对路径两侧解析到不同位置 → 产物落错地方，
    #   且 worker 产出的 file://<相对> 是坏 URI。
    # - `--no-report` 档：**真不生成**——不注入落点，并经 no_artifacts 令 worker 不产生/不上报引擎原生产物
    #   （Midscene 关 generateReport；Nova SDK 无关闭开关、不给目录时写进自己 mkdtemp 的临时目录、不上报）。
    #   曾一度改为「落系统临时目录、不清」，被否：用户要的 --no-report 就是不生成 report。
    report_root = Path(args.report_dir).resolve()
    if do_report:
        artifact_root = report_root / run_id
        nova_logs_dir: Path | None = artifact_root / _names.ARTIFACT_SUBDIR["novaact"]  # 子目录名单点（三宿主同名，ADR 0029）
        midscene_run_dir: Path | None = artifact_root / _names.ARTIFACT_SUBDIR["midscene"]
    else:
        nova_logs_dir = midscene_run_dir = None
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
        # 版本 skew 先于资源 preflight（ADR 0037 决策 7 的次序）；戳一并拿回，供下面的 variant 解析（ADR 0038）
        skew_rc, backend_version = _cloud_skew_gate(target)
        if skew_rc is not None:
            return skew_rc
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
        # worker 镜像 variant 解析（ADR 0038）：**在资源 preflight 之后**（次序理由见 _cloud_worker_variant_gate）。
        # 同步 run 的 FargateEngine 也一律照 definition 里的显式 revision 起 task（不用 family 取最新）。
        resolutions = _cloud_worker_variant_gate(
            args, target, sorted({j.engine for j in jobs}), backend_version=backend_version)
        if isinstance(resolutions, int):
            return resolutions
        worker_meta = _worker_meta_fields(resolutions)
        run_meta = replace(run_meta, **worker_meta)  # 落进 definition（下面 persistence.begin 写它）
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
                         "network_config": network_config,
                         # 引擎 → 显式 revision ARN（ADR 0038 不变量：永不用 family 取最新）
                         "worker_task_defs": worker_meta["worker_task_defs"] or {}}

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
            no_artifacts=not do_report,  # --no-report：worker 不生成/不上报原生产物（ADR 0037 决策 3）
            run_id=run_id, prefix=cloud_fargate["prefix"], cluster=cloud_fargate["cluster"],
            events_table=cloud_fargate["events_table"], bucket=cloud_fargate["bucket"],
            report_dir=args.report_dir, network_config=cloud_fargate["network_config"],
            # 每引擎的显式 task-def revision ARN（ADR 0038）：preflight 解析出的那一批，与写进 definition 的同源
            worker_task_defs=cloud_fargate["worker_task_defs"],
            region=target.region, profile=target.profile,
            extra_http_headers=tunnel_headers,  # 隧道模式的额外请求头（ADR 0035 决策 4；None=不注入）
        )
    else:
        if args.quiet:
            # --quiet 也管 worker 日志（ADR 0041 决策二）：落 <run_dir>/worker.log（--no-report 时落系统临时目录），
            # 结束只打一行位置——agent 的上下文别被 SDK 的 think/act 流水灌满；人看流水走默认档。
            import tempfile as _tf
            worker_log_path = ((report_root / run_id / "worker.log") if do_report
                               else Path(_tf.gettempdir()) / f"gherkai-worker-{run_id}.log")
            worker_log_path.parent.mkdir(parents=True, exist_ok=True)
            worker_log_fh = open(worker_log_path, "a", encoding="utf-8")
        engines = compose.build_engines(
            no_artifacts=not do_report,  # --no-report：worker 不生成/不上报原生产物（ADR 0037 决策 3）
            nova_logs_dir=nova_logs_dir, midscene_run_dir=midscene_run_dir,
            region=target.region, profile=target.profile,
            extra_http_headers=tunnel_headers,  # 同上（ADR 0035）
            steps_dir=steps_dir,  # 使用方确定性 step 目录（ADR 0037 决策 4；与写进 definition 的同一个值）
            worker_log=worker_log_fh,  # --quiet 时的 worker 日志落点；None = stderr 透传（默认）
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

    try:
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
    finally:
        if worker_log_fh is not None:
            worker_log_fh.close()  # 任何路径都关（异常/提前 return 也不留句柄）；下面只读它的路径

    # 6) commit point（ADR 0030 决定三）：各 job 判定真值已由 on_job_complete 逐个流式落；此处只剩
    #    finalize（写总 status + ended_at）+ 归集 ReportStore（派生、永远最后）。「finalize 一落 = run 已提交」。
    #    artifacts 落点指针由 compose 的 make_artifacts 按 backend URI 化组装（local file:// / cloud s3://+ddb://）。
    artifacts: dict[str, str] = {}
    if persistence:
        index = persistence.finalize(result, ended_at=compose.now_iso())
        artifacts = make_artifacts(run_id, index)  # report_index=None（report 写失败被隔离）时该键省略
    if worker_log_fh is not None:
        artifacts = {**artifacts, "worker_log": worker_log_path.as_uri()}  # --quiet 落盘的 worker 日志位置

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
    if "run_meta" in artifacts:  # 落过库才有这三行（--quiet --no-report 时 artifacts 只有 worker_log）
        # report_index 键可能缺席（report 写失败被隔离，ADR 0030 决定三）——缺则提示写失败、不打裸值
        report_line = artifacts.get("report_index", "<报告写入失败，已跳过；判定结果不受影响、仍已落库>")
        _progress(f"\n报告: {report_line}")
        _progress(f"运行元信息: {artifacts['run_meta']}、{artifacts['run_state']}")
        _progress(f"判定明细: {artifacts['jobs_dir']}")
    if worker_log_fh is not None:
        _progress(f"worker 日志: {artifacts['worker_log']}")

    # 退出码基于 run 级 status（ADR 0031 决定五）：读 schedule 返回的内存终值（必是终态，不回读落库态）。
    # PASSED→0，其余（failed/error，含必伴随 error 的 skipped/aborted 批次）→1。对未来新态稳健。
    return 0 if result.status == Status.PASSED else 1


def _deploy_provider(args) -> "object | None":
    """取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。

    两个 None 分支是**保险分支**：走 `main` 时 provider 恒已解析、失败也已在那里退 2（早于 argparse，见 main），
    但 parser 也可能被别的调用方不带 provider 构出来——那时就地补一次解析，而不是拿 None 去调方法。
    """
    provider = getattr(args, "_provider_obj", None)
    err = getattr(args, "_provider_error", None)
    if provider is None and err is None:
        provider, err = _deploy.resolve_provider(getattr(args, "provider", None))
    if provider is None:
        _progress(err or "没有可用的部署 provider。")
    return provider


def _cmd_deploy(args) -> int:
    """[部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。皮零 IaC 知识。

    退出码即 provider 的返回值——皮只在「provider 不可用」时自己退 2（VPC 档不一致/未 bootstrap 这类
    诊断与退码归 provider，它才知道自己的账户状态）。
    """
    provider = _deploy_provider(args)
    if provider is None:
        return 2
    # provider 贴的子动词（worker 镜像族 push-worker/list-workers，ADR 0038）优先——接缝见 deploy.py 契约块。
    verb = getattr(args, "_deploy_verb", None)
    if verb is not None:
        conflict = _deploy.readonly_flag_conflict(args)  # 子动词 + 只读 flag 同给 → 拒，别让预览变成真推镜像
        if conflict:
            _progress(conflict)
            return 2
        return verb(args)
    if args.bootstrap:
        return provider.bootstrap(args)
    if args.diff:
        return provider.diff(args)
    if args.synth_only is not None:
        return provider.synth_only(args)
    return provider.deploy(args)


def _cmd_destroy(args) -> int:
    """[部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。"""
    provider = _deploy_provider(args)
    return 2 if provider is None else provider.destroy(args)


def main(argv: list[str] | None = None) -> int:
    # argv 落实成具体 list：要先窥一眼才知道该不该为它加载部署 provider（见 _peek_deploy_provider）。
    argv = list(sys.argv[1:] if argv is None else argv)
    provider, provider_err = _peek_deploy_provider(argv)
    parser = _build_parser(provider=provider, provider_error=provider_err)
    # provider 不可用时抢在 argparse 之前报它：它的旋钮没贴上，用户敲的 `--vpc default` 会被报成
    # 「unrecognized arguments」、把真因（没装 / 装坏了）盖掉。**-h/--help 例外**——帮助恒可用，
    # 降级的帮助自己在 epilog 里交代原因（provider_err 只在子命令是 deploy/destroy 时才非 None）。
    if provider_err is not None and not any(a in ("-h", "--help") for a in argv):
        _progress(provider_err)
        return 2
    args = parser.parse_args(argv)

    if args.command == "list-deterministic":
        return _cmd_list_deterministic(args)
    if args.command == "list-engines":
        return _cmd_list_engines(args)
    if args.command == "doctor":
        return _cmd_doctor(args)
    if args.command == "plan":
        return _cmd_plan(args)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "submit":
        return _cmd_submit(args)
    if args.command == "status":
        return _cmd_status(args)
    if args.command == "_tunnel_watch":
        return _cmd_tunnel_watch(args)
    if args.command == "_reconcile":
        return _cmd_reconcile(args)
    if args.command == "deploy":
        return _cmd_deploy(args)
    if args.command == "destroy":
        return _cmd_destroy(args)

    # 无子命令 → 打帮助
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
