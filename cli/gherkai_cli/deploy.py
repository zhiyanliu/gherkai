"""`gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC 知识**（ADR 0037 决策 6）。

本模块是「命令 provider 中立」那条决策在 code 里的落点：**皮只做三件事**——按 entry point group 发现已装的
provider 包、把 provider 的 flag 接到自己的 subparser 上、把动作分派给 provider。
**皮绝不 import `aws_cdk` / 不碰 CDK 的 boto3 用法**：那些只住在 provider 包（`gherkai-deploy-aws`，经 CLI 的
`[deploy-aws]` extra 隔离——只有部署方装它，只提交 run 的人不必背 CDK + Node）。皮对 provider 的全部认识 =
下面 `Provider` 契约那几个方法名。

**为何有 provider 这层间接**：非 AWS 后端出现时新增一个 `gherkai-deploy-<provider>` 包即可，命令面不动
（ADR 0037「重议闸门」）；当下只有 aws 一个 provider，故单 provider 时**无需** `--provider`。
"""
from __future__ import annotations

import argparse
from importlib.metadata import EntryPoint, entry_points

# provider 发现面（ADR 0037 决策 6）：provider 包在自己的 `[project.entry-points."gherkai.deploy"]` 下登记
# `<名> = "<模块>:<Provider 类>"`；名（如 `aws`）即 `--provider` 的取值，**列名不需要加载 provider**
# （entry point 名住在包元数据里）——零个/多个的诊断因此不会被 provider 自身的 import 代价或故障牵连。
PROVIDER_GROUP = "gherkai.deploy"

# ============================================================================
# Provider 契约（皮对 provider 的全部要求；provider 侧的实现与 IaC 细节见 gherkai-deploy-aws）
# ----------------------------------------------------------------------------
#   name                        provider 自述名（诊断/日志用）。**皮的选择键是 entry point 名、不是它**——
#                               选择要在「未加载」时就能做（见上 PROVIDER_GROUP）。
#   add_arguments(parser)       往 deploy/destroy 两个 subparser 各贴一次自己的 flag。AWS provider 贴的是
#                               stack+app 那四个 context 旋钮映射成的三 flag（`--prefix` / `--vpc` /
#                               `--stop-timeout`），外加它自己的 AWS 概念 flag（`--region` / `--profile` 等）。
#   deploy(args) -> int         默认动作：真部署/更新。
#   destroy(args) -> int        拆栈（RETAIN 语义见 ADR 0033）。
#   diff(args) -> int           `--diff`：只呈变更集、不改账户。
#   synth_only(args) -> int     `--synth-only DIR`：只导模板到 `args.synth_only`、不连账户改动。
#   bootstrap(args) -> int      `--bootstrap`：透传 provider 的账户初始化（cdk bootstrap）。
# 全部收**已解析的 argparse.Namespace**、返回**进程退出码**：provider 自己声明的 flag 自己读，皮声明的命令面
# flag（`--require-approval` / `--allow-vpc-change`）也在同一个 Namespace 上，provider 按需取。
# 皮**不代 provider 做**：VPC 档 SSM 三态比对、版本戳写入、Node 前置检查、cdk 调用——全在 provider 内
# （它们要连 AWS / 起 node，是被 `[deploy-aws]` extra 隔离的那半边）。
#
# **子动词接缝**（`gherkai deploy push-worker` / `list-workers` 那族 worker 镜像命令，ADR 0038）：provider 在
# `add_arguments(deploy_parser)` 里自己 `add_subparsers()`，并给每个子动词 `set_defaults(_deploy_verb=<可调用>)`；
# 皮的分派**先看 `_deploy_verb`**，有就交给它、没有才走 `--diff/--synth-only/--bootstrap/deploy` 那四路。
# **组合规则**：子动词与三个「不真部署」flag 同给 → 皮退 2（`readonly_flag_conflict`）——子动词会真写账户（推镜像/
# 注册 task-def），若让它静默盖过用户点名要的只读预览，正是那三个 flag 要防的事（ADR 0037 决策 6 的 reviewer 靶点）。
# 这样那族命令落地时**皮一行不改**（它们要读 SSM/ECR/task-def、碰容器引擎，全属 provider 那半边）。
# 子动词 subparser 不可设 `required=True`——否则裸 `gherkai deploy`（默认动作 = 真部署）会被 argparse 拒。
# ============================================================================


def provider_entry_points() -> list[EntryPoint]:
    """已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。"""
    return sorted(entry_points(group=PROVIDER_GROUP), key=lambda ep: ep.name)


def resolve_provider(name: str | None) -> tuple[object | None, str | None]:
    """按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None, 人读的一句)`。

    三分叉（ADR 0037 决策 6）：**零个** → 提示装 `gherkai[deploy-aws]`；**一个** → 直接用、无需 `--provider`；
    **多个** → 必须 `--provider <名>`，否则列出名字让人选（皮不替用户猜「哪个云」）。全部失败档由调用点退 2。

    加载 = `ep.load()`：拿到**类**则实例化（entry point 惯例指向 `Provider` 类），拿到现成对象/单例则原样用。
    加载失败（provider 包半装 / 版本不匹配 / 它自己的 import 链炸）不让 traceback 裸奔——翻成点名 entry point
    的一句诊断（用户视角这是「装了但不可用」，与「没装」是两回事，措辞必须分开）。
    """
    eps = provider_entry_points()
    if not eps:
        return None, (
            "没有可用的部署 provider：装 `gherkai[deploy-aws]`（AWS 后端；带 Python CDK，另需 Node ≥22 在 PATH）。"
            "只有**部署方**需要装它——只提交 run 的人不必。"
        )
    names = ", ".join(ep.name for ep in eps)
    if name is None:
        if len(eps) > 1:
            return None, f"装了多个部署 provider（{names}）：用 --provider <名> 指定其一。"
        ep = eps[0]
    else:
        match = [ep for ep in eps if ep.name == name]
        if not match:
            return None, f"未知 provider {name!r}（已装：{names}）。"
        ep = match[0]
    try:
        loaded = ep.load()
        obj = loaded() if isinstance(loaded, type) else loaded  # 实例化也算「加载」：__init__ 炸同属装了但不可用
    except Exception as e:  # 半装 / 版本不匹配 / provider 自己的 import 链或 __init__ 炸
        return None, (
            f"部署 provider {ep.name!r} 加载失败（entry point {ep.value}）：{type(e).__name__}: {e}"
            f"——装了但不可用（版本不匹配？半装？），重装 `gherkai[deploy-aws]` 或 --provider 换一个。"
        )
    return obj, None


def readonly_flag_conflict(args) -> str | None:
    """provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-only/--bootstrap` 同给 →
    一句产品语言的诊断（调用点退 2）；否则 None。三 flag 是「先看清再改账户」的只读/准备靶点（ADR 0037 决策 6），
    子动词的分派优先级若把它们静默吞掉，用户要的预览会变成真推镜像——见模块头「组合规则」。"""
    if getattr(args, "_deploy_verb", None) is None:
        return None
    given = [flag for flag, on in (("--diff", getattr(args, "diff", False)),
                                   ("--synth-only", getattr(args, "synth_only", None) is not None),
                                   ("--bootstrap", getattr(args, "bootstrap", False))) if on]
    if not given:
        return None
    return (f"{' / '.join(given)} 是只读/准备动作，不能与 worker 镜像子命令同用（子命令会真推镜像、改账户）："
            f"去掉它再跑子命令，或单独跑 `gherkai deploy {given[0]}` 看变更集。")


def add_parsers(sub, *, provider: object | None = None, provider_error: str | None = None,
                cli_version: str | None = None) -> None:
    """把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。

    解析结果经 `set_defaults` 落到两个 subparser 上（`_provider_obj` / `_provider_error`），分派侧直接取——
    provider 只加载一次，不在「贴 flag」与「跑动作」之间解析两遍。

    `provider=None`（未解析或解析失败）时只有皮自己的命令面 flag——保住 `gherkai --help` / `gherkai deploy --help`
    **恒可用**（帮助不该因为没装 provider 而失败），真动作时再由调用点报 `provider_error` 并退 2。

    **`conflict_handler="resolve"`**：命令面 flag 由皮声明、provider 旋钮由 provider 声明，两侧同名时以
    provider 为准而非抛 `ArgumentError`——同名即同义（旋钮的真源在 provider 那半边），让 `--help` 因重名崩掉
    是最没价值的失败方式。**这不是假想情形**：AWS provider 就重声明了 `--allow-vpc-change` /
    `--require-approval`（带上自己的 choices 与措辞），resolve 让它的声明生效、皮的那份自然让位。
    不同义的重名属集成 bug，会在分派读不到自己的 dest 时暴露（皮只读自己那三个动作 flag）。
    """
    # provider 缺席时把原因写进 epilog：不然「帮助里没有 --prefix/--vpc」看着像 flag 面残缺，
    # 而真相是 provider 没解析出来（没装 / 装坏了）——降级的帮助必须自解释。
    epilog = (f"注意：provider 的旋钮（如 --prefix / --vpc / --stop-timeout）未列在上面——{provider_error}"
              if provider is None and provider_error else None)
    dp = sub.add_parser(
        "deploy", conflict_handler="resolve", epilog=epilog,
        help="[部署方] 部署/更新云端后端",
        description="部署/更新云端后端（表/桶/cluster/task-def/Lambda 链/VPC 等）。"
                    "IaC 由 provider 包供给（装 `gherkai[deploy-aws]`；需 Node ≥22 在 PATH）。"
                    "默认动作 = 真部署；下面三个 flag 各自换成一个只读/准备动作。",
    )
    _add_provider_flag(dp)
    # 三个互斥的「不真部署」动作（ADR 0037 决策 6 的命令面）：给 reviewer/谨慎的人留靶点——
    # 不让一个 0.x 工具在没人看过变更集之前改自己的生产账号。
    act = dp.add_mutually_exclusive_group()
    act.add_argument(
        "--diff", action="store_true",
        help="只呈变更集、不部署（先看清这次会改什么，尤其网络/IAM）",
    )
    act.add_argument(
        "--synth-only", default=None, metavar="DIR",
        help="只把 IaC 合成的模板导出到 DIR、不连账户改动（逃生舱：交给自己的审批/发布流水线去 apply）",
    )
    act.add_argument(
        "--bootstrap", action="store_true",
        help="只做 provider 的账户初始化（AWS = cdk bootstrap，每账户+region 一次）；未初始化就 deploy 会报错指回本 flag",
    )
    dp.add_argument(
        "--require-approval", default=None, metavar="MODE",
        help="权限/IAM 变更的审批档，原样透传给 provider（AWS provider = cdk 的 never / any-change / broadening）；"
             "不给则用 provider 自己的默认",
    )
    dp.add_argument(
        "--allow-vpc-change", action="store_true",
        help="放行 VPC 档变更：本次的档与后端记着的上次生效档不一致、或 stack 已存在但后端还没有档记录时，deploy 退 2、"
             "要你先 `--diff` 核对变更集；核对完带本 flag 放行一次——漏给 VPC 档会合成"
             "「新建整套 VPC + 替换安全组」的危险变更集（真踩过）",
    )

    dsp = sub.add_parser(
        "destroy", conflict_handler="resolve", epilog=epilog,
        help="[部署方] 拆掉云端后端（数据类资源保留、不随之删）",
        description="拆掉云端后端 stack。数据类资源（runs 表/桶/ECR 仓库）按 IaC 的 RETAIN 标记保留、"
                    "不随 stack 删除；版本戳等 stack 自己的参数随删。",
    )
    _add_provider_flag(dsp)

    # provider 的旋钮两个子命令都要（destroy 也得知道拆哪个 prefix、且 provider 合成时要同一套 context）。
    # **贴两次是有意的**：argparse 的父子 parser 不共享 action 实例，且 provider 才知道自己有哪些旋钮。
    if provider is not None:
        provider.add_arguments(dp)
        provider.add_arguments(dsp)
    for p in (dp, dsp):
        # `version` = **CLI 自己的**发行版本，交给 provider 写进后端版本戳（ADR 0037 决策 6/7）：戳必须是
        # 「写任务定义那一方」的版本，因为 run/submit 的 skew 闸拿它比。发行态下五个包 `==` lockstep 恒同版本，
        # 但 editable 的开发树里各包版本会各自漂（各自按 git 状态算），故显式传、不让 provider 自报。
        p.set_defaults(_provider_obj=provider, _provider_error=provider_error, version=cli_version)


def _add_provider_flag(p: argparse.ArgumentParser) -> None:
    """`--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。"""
    p.add_argument(
        "--provider", default=None, metavar="NAME",
        help="用哪个部署 provider（entry point 名，如 aws）；装了一个时不必给、装了多个时必给",
    )
