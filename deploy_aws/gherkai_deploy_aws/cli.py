"""`gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws` 项，ADR 0037 决策 6）。

**本模块是 CLI 皮与 CDK 之间的唯一接缝**，形状由一条硬约束定死：**CLI 绝不 import `aws_cdk`**——它是 jsii 绑定，
import 即起 node 子进程（ADR 0037 决策 6）。故本模块自身也只 import 标准库 + `gherkai_runtime` + 本包 `names`
（零 `aws_cdk`）；stack/app 只经 **cdk CLI 起的子进程** 触达（`app.py`）。CLI 侧 `--help` 因此不付 node 代价。

## 接缝契约（CLI 皮 ↔ Provider）

CLI 皮负责：
- 发现 provider（entry point group `gherkai.deploy`：零个 → 提示装 `gherkai[deploy-aws]`；一个 → 无需
  `--provider`；多个 → 必给），实例化，调 `add_arguments(subparser)` 让 provider 贡献自己的 flag；
- 声明 **provider 中立的命令面 flag** 并据其选调本类哪个方法（ADR 0037 决策 6「命令面」）：
  `--diff` → `diff`、`--synth-only DIR` → `synth_only`（DIR 落 `args.synth_only`）、`--bootstrap` →
  `bootstrap`，都不给 → `deploy`；`gherkai destroy` → `destroy`；
- 先声明 `--require-approval` 与 `--allow-vpc-change` 的**中立版**，使 `deploy --help` 在**没装任何 provider**
  时也列得出这两个动作旋钮；
- 可选把自身版本放进 `args.version`（缺则本包自报 dist 版本，见 `_resolve_version`）。

Provider 负责（CLI 一概不懂）：`--prefix`/`--vpc`/`--stop-timeout` 三个 context 旋钮 + AWS 概念的
`--region`/`--profile`（CLI 皮不在 deploy/destroy 子命令上声明这五个）、context 拼装、`cdk.json` 生成、
cdk CLI 调用、VPC 档三态比对、Node 前置检查。

**`--require-approval` / `--allow-vpc-change` 是有意的两层声明**：皮给中立版（provider 缺席时帮助不残缺），
本类**再声明一次**带 AWS 语义的版本（`--require-approval` 的取值是 cdk 的三档，能 `choices` 校验；
`--allow-vpc-change` 的措辞要点名 VPC 档三态）。皮的 subparser 开了 `conflict_handler="resolve"`，同名即
以后贴的（本类）为准——两层不是重复真源，是「中立占位 + provider 精确化」。本类另经 `getattr` 容忍它们
彻底缺席（别的皮）：缺 `--allow-vpc-change` = 一律不放行（fail-closed）、缺 `--require-approval` = 交给 cdk 默认。

## worker 镜像子动词（ADR 0038 命令族）

`add_arguments(deploy_parser)` 里自贴 `push-worker` / `list-workers` / `delete-worker` 三个子动词，各自
`set_defaults(_deploy_verb=<本类方法>)`——皮的分派**先看 `_deploy_verb`**（皮一行不改，见其契约块）。
云端写操作（推 ECR、注册 task-def revision、写 SSM 指针）全属部署变更，故住本包、不住 CLI 本体；实现在
`workers.py`，容器引擎在 `container.py`。子动词只挂 deploy、不挂 destroy（理由见 `_declares_worker_subverbs`）。

## 退出码

`0` 成功；`2` **前置/校验失败**（Node 缺失、VPC 档不符或无记录、读后端失败、容器引擎名不认、push-worker
的架构/skew 拦截——用户可修，对齐 CLI 既有 preflight 退 2 的口径）；**`1`** = cdk 已成功而 worker 镜像四步失败
（账户已被改动，重跑 `gherkai deploy` 幂等收敛，ADR 0038）；其余 = cdk CLI 自己的返回码（原样透传，
别把 cdk 的失败压成自己的码）。
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from gherkai_deploy_aws import names

PROVIDER_NAME = "aws"

EXIT_OK = 0
EXIT_PRECONDITION = 2  # 前置/校验失败（与 CLI preflight 同一档，见模块头「退出码」）

# Node 下限：与 worker 的 `engines.node` 同一下限（ADR 0037 决策 6「Node 前置是硬事实」，README 一处说清）。
NODE_MIN_MAJOR = 22

# `cdk.json` 的 `context`：CDK **特性开关**（feature flags）。**逐字沿用收编前 `iac_aws_backend/cdk.json` 的那一组**——
# 特性开关会改变合成出的资源形态，换一组就等于给已部署 stack 造出无意义的变更集。加/删任何一项前先 `--diff` 核对。
# （设计旋钮不在这里：prefix/vpc/stop_timeout/version 一律经 `-c k=v` 显式传，不进生成的 cdk.json——见 `build_context`。）
CDK_FEATURE_FLAGS: dict[str, object] = {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": True,
    "@aws-cdk/core:checkSecretUsage": True,
    "@aws-cdk/aws-iam:minimizePolicies": True,
    "@aws-cdk/core:validateSnapshotRemovalPolicy": True,
    "@aws-cdk/aws-ecs:disableExplicitDeploymentControllerForCircuitBreaker": True,
    "@aws-cdk/core:target-partitions": ["aws", "aws-cn"],
}

# VPC 档三态比对的四种判定（ADR 0037 决策 6「VPC 档持久化比对，三态齐全」；`classify_vpc_state` 的返回值）
VPC_FIRST_DEPLOY = "first-deploy"  # ① stack 不存在 = 真首次部署 → 放行
VPC_UNRECORDED = "unrecorded"      # ② 参数缺失且 stack 已存在 = 本机制之前部署的环境 → 退 2（最危险的那一次）
VPC_MATCH = "match"                # ③ 档一致 → 放行
VPC_MISMATCH = "mismatch"          # ③ 档不一致 → 退 2


# ---------------------------------------------------------------------------
# VPC 档（纯逻辑，与 boto3 解耦——三态判定是这套机制的正确性核心，单测直打它）
# ---------------------------------------------------------------------------

def vpc_spec_matches(stored: str, requested: str) -> bool:
    """SSM 里记的生效档 `stored` 是否 == 本次 `--vpc requested`。

    三档形态见 `names.ssm_vpc_path`。`new` 档在 SSM 里是 `new:<所建 vpc-id>`（带出所建 id 以便回溯核对），
    故 `--vpc new` 按 **`new:` 前缀** 匹配、不逐字比。
    **反过来不成立**：`stored="new:vpc-abc"` 与 `--vpc vpc-abc` **不算一致**——前者是「VPC 由本 stack 拥有」、
    后者是「复用一个 stack 外的 VPC」，切换会让 CloudFormation 把它从 stack 里摘出去（= 删掉那个 VPC）。
    """
    if requested == "new":
        return stored == "new" or stored.startswith("new:")
    return stored == requested


def classify_vpc_state(*, stack_exists: bool, stored_spec: str | None, requested: str) -> str:
    """三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。

    判序里 **stack 是否存在先于参数是否存在**：真首次部署时两者都缺，若先看参数就会把首次部署误判成
    「本机制之前部署的环境」而拦下每一个新用户的第一次 deploy。
    """
    if not stack_exists:
        return VPC_FIRST_DEPLOY
    if not stored_spec:
        return VPC_UNRECORDED
    return VPC_MATCH if vpc_spec_matches(stored_spec, requested) else VPC_MISMATCH


def _vpc_flag(value: str) -> str:
    """`--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三档，**无隐式默认**（ADR 0037 决策 6）。"""
    if value in ("default", "new") or (value.startswith("vpc-") and len(value) > len("vpc-")):
        return value
    raise argparse.ArgumentTypeError(
        f"--vpc 须是 default / new / vpc-<id> 之一，得到 {value!r}"
        "（三档与 ADR 0033「VPC 来源：三档」一一对应；不设隐式默认——漏档会合成"
        "「新建整套 VPC + 替换 WorkerSg」的危险变更集，这是真踩过的坑）"
    )


# —— 造 boto3 句柄的两个钩子（抽出来供测试 monkeypatch，验三态逻辑而不连真 AWS；同 compose 的 `_make_*` 惯例）——
def _make_cfn_client(*, region, profile):
    """boto3 cloudformation client（`DescribeStacks` 探 stack 是否已存在）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("cloudformation")


def _make_sts_client(*, region, profile):
    """boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("sts")


def _make_ssm_client(*, region, profile):
    """boto3 ssm client（读生效 VPC 档参数）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("ssm")


def _error_code(exc: Exception) -> str | None:
    """botocore ClientError 的 `Error.Code`（非 ClientError → None）。不 import botocore：本包不该为读一个
    错误码把 botocore 变成 import 期依赖，鸭子类型足够（compose.read_backend_version 同款处理）。"""
    resp = getattr(exc, "response", None)
    if not isinstance(resp, dict):
        return None
    return resp.get("Error", {}).get("Code")


def _stack_exists(cfn, stack_name: str) -> bool:
    """CloudFormation 里是否有这个 stack。

    「不存在」在 CloudFormation 是 `ValidationError` + 「does not exist」文案（**不是** ResourceNotFound）；
    而 `ValidationError` 也用于别的参数问题，故**同时看错误码与文案**——只看码会把真正的参数错误当成
    「真首次部署」放行，那正是三态要挡的那次危险 deploy。
    """
    try:
        cfn.describe_stacks(StackName=stack_name)
        return True
    except Exception as exc:
        code = _error_code(exc)
        if code in ("ValidationError", "ResourceNotFoundException") and "does not exist" in str(exc):
            return False
        raise


def _read_stored_vpc_spec(ssm, prefix: str) -> str | None:
    """读 SSM 里的生效 VPC 档；`ParameterNotFound` → None（= 本机制之前部署的环境，由三态判定处置）。"""
    try:
        resp = ssm.get_parameter(Name=names.ssm_vpc_path(prefix))
    except Exception as exc:
        if _error_code(exc) == "ParameterNotFound":
            return None
        raise
    return (resp["Parameter"]["Value"] or "").strip() or None


class Provider:
    """AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。"""

    name = PROVIDER_NAME

    # ---- flag 面（ADR 0037 决策 6：三 flag 对齐 stack 与 app 的全部 context 旋钮）----
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """把 provider 特有 flag 挂上 CLI 给的 parser。

        `prefix`/`vpc_id`/`use_default_vpc`/`stop_timeout` 四个 context 旋钮映射为**三个** flag：`--vpc`
        一个吞掉 `vpc_id` + `use_default_vpc` 两个旋钮（ADR 0037 决策 6）。`version` 旋钮不给 flag——
        版本是单旋钮、由安装本身决定（决策 7），不让用户手填。
        """
        parser.add_argument(
            "--prefix", default=None, metavar="P",
            help="资源名前缀（默认 gherkai-，或 AWS_RESOURCE_PREFIX）；**须与 run/submit 的 --prefix 一致**",
        )
        parser.add_argument(
            "--vpc", default=None, type=_vpc_flag, metavar="档",
            help="VPC 来源三档：default（账户默认 VPC）/ new（本 stack 新建，2-AZ 零 NAT）/ vpc-<id>（复用现有）。"
                 "deploy / --diff / --synth-only / destroy 必给、无隐式默认；--bootstrap 不需要（账户级动作、不合成 stack）",
        )
        parser.add_argument(
            "--stop-timeout", default=None, type=int, metavar="N",
            help="worker container 的 SIGTERM→SIGKILL 宽限秒数（默认 120，Fargate 硬上限 120）",
        )
        parser.add_argument(
            "--refresh-context", action="store_true",
            help="丢弃本机缓存的 CDK 环境查询结果（VPC/子网/AZ，见 --vpc default|<id> 的 from_lookup）重新查询；"
                 "默认复用缓存（CDK 标准做法，也避免每次为缺失查询预合成占位模板）",
        )
        # 下面两个是**皮已声明的中立版的 AWS 精确化**（`conflict_handler="resolve"` 令本处生效，见模块头
        # 「两层声明」）：一个加 cdk 的取值 `choices`、一个把措辞钉到 VPC 档三态上。
        parser.add_argument(
            "--allow-vpc-change", action="store_true",
            help="放行一次 VPC 档变更/首次登记（默认拦：档与后端记录不符即退 2，先 --diff 核对变更集）",
        )
        parser.add_argument(
            "--require-approval", default=None,
            choices=("never", "any-change", "broadening"),
            help="透传 cdk 的 IAM 变更审批档（不给则用 cdk 自己的默认值）",
        )
        # --region/--profile 归 provider（AWS 概念）：CLI 皮不在本子命令上声明，见模块头接缝契约。
        parser.add_argument("--region", default=None, metavar="R", help="AWS region（默认走 AWS_REGION/profile 配置）")
        parser.add_argument("--profile", default=None, metavar="P", help="AWS profile（默认 AWS_PROFILE）")
        # worker 镜像子动词（ADR 0038 命令族）——**只贴在 deploy 上**，见 `_declares_worker_subverbs`。
        if self._declares_worker_subverbs(parser):
            # deploy 自己也消费容器引擎（第 2 步同步基底 pull/push）——flag 贴在 deploy 上，子动词 push-worker 再贴
            # 一份（子 parser 是独立 namespace，SUPPRESS 默认值让「deploy --container-engine X push-worker …」不被覆写）。
            self._add_container_engine_flag(parser)
            self._add_worker_subverbs(parser)

    # ---- worker 镜像子动词（ADR 0038「命令族」；接缝 = 皮先看 args._deploy_verb，见模块头/皮的契约块）----
    @staticmethod
    def _declares_worker_subverbs(parser: argparse.ArgumentParser) -> bool:
        """这个 parser 是 **deploy** 的那个吗？

        皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用 provider 的 context 旋钮）。子动词只能挂
        deploy：挂上 destroy 的后果不是「多个没用的命令」而是**危险**——皮的 destroy 分派根本不看
        `_deploy_verb`，于是 `gherkai destroy push-worker …` 会解析通过、然后**去拆栈**。
        判据取 `prog` 末段（皮建的是 `sub.add_parser("deploy")` → prog = `<皮> deploy`）；认不出就不贴，
        降级是安全的（子动词本来也只经 deploy 这条路可达）。
        """
        return (parser.prog or "").split()[-1:] == ["deploy"]

    def _add_worker_subverbs(self, parser: argparse.ArgumentParser) -> None:
        """`push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。

        **`required=False`（argparse 默认）是硬约束**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样
        解析得过（皮的契约块明写）。每个子动词 `set_defaults(_deploy_verb=<绑定方法>)`，皮据此优先分派。
        """
        sub = parser.add_subparsers(
            title="worker 镜像子命令（ADR 0038；不给则本命令 = 部署/更新后端）", metavar="[子命令]",
        )
        push = sub.add_parser(
            "push-worker", help="[部署方] 推一个本地镜像并注册为某引擎的一个 variant",
            description="推送一个**已 build 好**的本地镜像到本 prefix 的 ECR，并把它注册成该引擎的一个 variant "
                        "（一个 task-def revision，镜像按 digest 引用）。一次一个引擎；两个引擎跑两次。"
                        "镜像构建不归 gherkai——三行定制镜像模板见 deploy_aws/README.md。",
        )
        push.add_argument("image", metavar="<本地镜像>", help="本地镜像名（任何名字，如 acme-novaact:login）")
        push.add_argument("--engine", required=True, choices=names.ENGINES, help="这个镜像是哪个引擎的 worker")
        push.add_argument("--variant", required=True, metavar="名",
                          help="variant 名（一套具名的确定性 step 集，自取：login / checkout-v2；"
                               "ECR tag = <CLI 版本>-<名>）")
        push.add_argument("--set-default", action="store_true",
                          help="同时把默认指针指向这个 variant（提交时不给 --worker-variant 就用它）")
        self._add_container_engine_flag(push)
        self._add_locator_flags(push)
        push.set_defaults(_deploy_verb=self.push_worker)

        listing = sub.add_parser(
            "list-workers", help="[部署方] 列各引擎当前版本的 variant / digest / 默认指针 / 待清理 revision",
            description="按引擎列出**当前版本**（= 本 CLI 自身版本）的 variant、digest、推送时间与 revision，"
                        "加上默认指针，以及已退休待清理与孤儿 revision。",
        )
        self._add_locator_flags(listing)
        listing.set_defaults(_deploy_verb=self.list_workers)

        delete = sub.add_parser(
            "delete-worker", help="[部署方] （尚未提供）删一个 variant 及其 ECR/SSM 残留",
            description="尚未提供：落地时套 push-worker 同一套清理语义（退休 tag + 静默期 + 在跑 run 安全阀），"
                        "并连带清旧版本 variant 的 ECR tag / untagged 层与 SSM 映射。",
        )
        self._add_locator_flags(delete)
        delete.set_defaults(_deploy_verb=self.delete_worker)

    @staticmethod
    def _add_container_engine_flag(parser: argparse.ArgumentParser) -> None:
        """`--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。"""
        from gherkai_deploy_aws.container import (
            CONTAINER_ENGINE_ENV,
            DEFAULT_CONTAINER_ENGINE,
            SUPPORTED_ENGINES,
        )

        parser.add_argument(
            "--container-engine", default=argparse.SUPPRESS, metavar="名",
            help=f"用哪个容器引擎（默认 {DEFAULT_CONTAINER_ENGINE}，或 env {CONTAINER_ENGINE_ENV}）；"
                 f"这一期只实装 {'/'.join(SUPPORTED_ENGINES)}",
        )

    @staticmethod
    def _add_locator_flags(parser: argparse.ArgumentParser) -> None:
        """子动词也收 `--prefix` / `--region` / `--profile`。

        **`default=SUPPRESS` 是必须的**：argparse 的子 parser 在**新 namespace** 里解析、再整体覆盖回父
        namespace——带普通默认值（None）会把父层已经解析到的 `deploy --prefix prod- push-worker …` 覆写成 None
        （argparse 的经典坑）。SUPPRESS = 子层没给就不产出这个属性、父层的值自然留住，两处给法都成立。
        """
        parser.add_argument("--prefix", default=argparse.SUPPRESS, metavar="P",
                            help="资源名前缀（须与 `gherkai deploy` / run/submit 的 --prefix 一致）")
        parser.add_argument("--region", default=argparse.SUPPRESS, metavar="R", help="AWS region")
        parser.add_argument("--profile", default=argparse.SUPPRESS, metavar="P", help="AWS profile")

    # ---- 命令面（CLI 皮据它自己的 flag 选调；每个方法自成一次完整调用）----
    def deploy(self, args) -> int:
        """供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。"""
        # 工具链前置先于 VPC 档比对：前者不花网络、不要凭证——缺 Node 的人不该先被要求配好 AWS 凭证
        # 才看到「你缺 Node」。`_run_cdk` 里同样查一次（每条命令都要过这一关，不靠调用者记得）。
        node_error = check_node()
        if node_error:
            print(node_error, file=sys.stderr)
            return EXIT_PRECONDITION
        # 容器引擎的两类问题也在这一档处置（本地、不花网络、不要凭证——这一期 deploy 机器需要容器引擎，
        # 同步基底要 pull/push，ADR 0038「容器引擎口子」）：
        # - **名字不认**（env/flag 给了 podman）→ 纯参数问题，退 2、绝不动账户；
        # - **装了但不可用 / 没装** → 只警告：退码语义归 cdk 之后的四步（账户已改 → 退 1、重跑幂等收敛）。
        #   仍要提前说一声——cdk deploy 是分钟级动作，让人跑完才知道「还差个 docker」是白等。
        engine = self._container_engine(args)
        if engine is None:
            return EXIT_PRECONDITION
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        # 探活警告放在 `--vpc` 校验之后：缺 `--vpc` 会直接退 2，先打两行 docker 警告只会盖住真因。
        probe = engine.probe()
        if probe:
            print(f"警告：{probe}\n     stack 会照常部署，但之后的 worker 镜像步骤（同步基底）会失败"
                  f"（退 1）；装好容器引擎后重跑 `gherkai deploy` 幂等收敛。", file=sys.stderr)
        blocked = self._guard_vpc_spec(args)
        if blocked is not None:
            return blocked
        extra = ["--require-approval", args.require_approval] if getattr(args, "require_approval", None) else []
        rc = self._run_cdk("deploy", args, extra=extra)
        if rc != EXIT_OK:
            # cdk 自己的报错已在上面原样打出；只补一条**中性**提示、不改写也不猜它的诊断（失败原因很多：
            # 权限、变更集被拒、模板错……）。未 bootstrap 是首次部署最常见的一种（ADR 0037 决策 6）。
            print("提示：cdk deploy 失败原因见上方 cdk 输出。首次在某账户/region 部署最常见的一种是环境未 bootstrap"
                  "——若报错提到 bootstrap，先跑 `gherkai deploy --bootstrap`（同 --profile/--region）。",
                  file=sys.stderr)
            return rc
        # cdk 成功 → worker 镜像四步（ADR 0038）。第 1 步（登记模板）已随 cdk 事务落地。
        return self._worker_image_steps(args)

    def destroy(self, args) -> int:
        """销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。

        不过 VPC 档三态：destroy 不改 VPC 形态，比对只会拦住「档记错了但想删干净」的人。
        但 `--vpc` 仍必给：destroy 也要合成 app（stack 的网络分支按档走），缺档合成不出同一个 stack。
        """
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        return self._run_cdk("destroy", args)

    def diff(self, args) -> int:
        """只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对——
        对本机制之前部署的环境，`deploy` 退 2 时让人跑的就是它，若它也被拦就无路可走。"""
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        return self._run_cdk("diff", args)

    def synth_only(self, args) -> int:
        """导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的
        reviewer 靶点，ADR 0037 决策 6）。目录由 CLI 皮的 `--synth-only DIR` 提供（接缝契约）。"""
        out = getattr(args, "synth_only", None)
        if not out:
            raise ValueError("synth_only 需要 args.synth_only（CLI 皮的 --synth-only DIR）——见模块头接缝契约")
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        # 用户给的 DIR 相对**用户的** cwd；`_run_cdk` 里把它钉成绝对路径再交给 cdk——cdk 子进程的 cwd 是随后
        # 被删的临时工作目录，相对路径原样传会让导出物落进那里、随之消失而命令却退 0（真跑踩过）。
        return self._run_cdk("synth", args, output=Path(out).expanduser())

    def bootstrap(self, args) -> int:
        """`cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。

        显式给 `aws://<account>/<region>` 且**不带 `--app`**：cdk 有显式环境又没有 app 时直奔凭证与 bootstrap
        stack（真跑核过：带 `--app` 则即使给了显式环境也会先跑 app——那就又要 `--vpc` 了）。
        account 经 STS `GetCallerIdentity` 取（对任何主体恒可用、不算新增权限）；region 走同一条解析链
        （`--region` / AWS_REGION / profile 配置），取不到 → 退 2（bootstrap stack 是按 region 建的，不能猜）。
        """
        node_error = check_node()
        if node_error:
            print(node_error, file=sys.stderr)
            return EXIT_PRECONDITION
        cdk_argv = cdk_command()
        if not cdk_argv:
            print("找不到 cdk 也找不到 npx：cdk CLI 是 npm 物，装 Node（≥ %d）后重试（ADR 0037 决策 6）。"
                  % NODE_MIN_MAJOR, file=sys.stderr)
            return EXIT_PRECONDITION
        target = self._resolve_target(args)
        try:
            sts = _make_sts_client(region=target.region, profile=target.profile)
            account = sts.get_caller_identity()["Account"]
            region = target.region or sts.meta.region_name
        except Exception as exc:
            print(f"取不到账户（STS GetCallerIdentity）：{exc}\n需要可用的凭证与 region（--region / AWS_REGION / "
                  f"--profile 的配置）。", file=sys.stderr)
            return EXIT_PRECONDITION
        if not region:
            print("bootstrap 需要 region（--region / AWS_REGION / profile 配置）：bootstrap stack 按 region 建，不能猜。",
                  file=sys.stderr)
            return EXIT_PRECONDITION
        argv = [*cdk_argv, "bootstrap", f"aws://{account}/{region}"]
        if target.profile:
            argv += ["--profile", target.profile]
        env = os.environ.copy()
        env["AWS_REGION"] = region
        env["AWS_DEFAULT_REGION"] = region
        with self._work_dir() as work_dir:  # 空目录：无 cdk.json、无 app——cdk 不会去找 app
            try:
                return subprocess.run(argv, cwd=str(work_dir), env=env).returncode
            except FileNotFoundError as exc:
                print(f"起不动 cdk CLI：{exc}", file=sys.stderr)
                return EXIT_PRECONDITION

    # ---- 命令面（worker 镜像族，ADR 0038；皮经 args._deploy_verb 分派到这三个）----
    def push_worker(self, args) -> int:
        """`gherkai deploy push-worker <镜像> --engine … --variant …`（八步见 `workers.push_worker`）。"""
        from gherkai_deploy_aws import workers

        engine = self._container_engine(args)
        if engine is None:
            return EXIT_PRECONDITION
        target = self._resolve_target(args)
        return workers.push_worker(
            args.image, engine=args.engine, variant=args.variant,
            set_default=bool(getattr(args, "set_default", False)),
            # tag 用的版本 = **CLI 自身版本**（与写进 SSM 的戳同一个，ADR 0038「preflight」按它解析）
            cli_version=self._resolve_version(args),
            prefix=target.prefix, region=target.region, profile=target.profile, container=engine,
        )

    def list_workers(self, args) -> int:
        """`gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。"""
        from gherkai_deploy_aws import workers

        target = self._resolve_target(args)
        return workers.list_workers(prefix=target.prefix, cli_version=self._resolve_version(args),
                                    region=target.region, profile=target.profile)

    def delete_worker(self, args) -> int:
        """留的口子（ADR 0038「命令族」）：**尚未提供**，退 2 说清为什么与将来怎么落。

        为何占位而不干脆不给这个子命令：不给的话用户敲了只会得到 argparse 的「invalid choice」，读不出
        「这件事是被想过、押后了」——而它押后的是**回收策略**（ECR untagged 层、旧版本 variant），不是忘了。
        """
        print("`delete-worker` 尚未提供。\n"
              "它要连带定回收策略（旧版本 variant 的 ECR tag / 重推顶掉的 untagged 层 / SSM 映射），"
              "并套 push-worker 同一套清理语义（退休 tag + 静默期 + 在跑 run 安全阀）——属 ADR 0038 重议闸门。\n"
              "当前可用的：`gherkai deploy list-workers` 看有哪些 variant 与待清理 revision；"
              "重推同名 variant 直接覆盖，无需先删。", file=sys.stderr)
        return EXIT_PRECONDITION

    # ---- 内部：容器引擎（ADR 0038「容器引擎口子」）----
    @staticmethod
    def _container_engine(args, *, quiet: bool = False):
        """解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。

        **只解析、不探活**：探活（`probe()`）归真要用它的那一步——push-worker 在 skew 前置之后探（skew 拦下的
        人不该先被要求装 docker），deploy 的四步在 cdk 之后探（见 `_worker_image_steps`）。
        """
        from gherkai_deploy_aws.container import UnsupportedContainerEngine, resolve_container_engine

        try:
            return resolve_container_engine(getattr(args, "container_engine", None))
        except UnsupportedContainerEngine as exc:
            if not quiet:
                print(str(exc), file=sys.stderr)
            return None

    def _worker_image_steps(self, args) -> int:
        """cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。

        **不做版本 skew 前置**：deploy 就是改戳的那个动作（ADR 0038）。失败退 1（不是 2）——账户已经被 cdk
        改过了，压成「前置失败」会让人以为什么都没发生。
        """
        from gherkai_deploy_aws import workers

        engine = self._container_engine(args)
        if engine is None:  # `--container-engine podman` 一类：stack 已生效，但这是参数问题、指向重议闸门
            return workers.EXIT_FAILED
        target = self._resolve_target(args)
        return workers.run_deploy_steps(
            prefix=target.prefix, version=self._resolve_version(args), container=engine,
            region=target.region, profile=target.profile,
        )

    @staticmethod
    def _require_vpc(args) -> int | None:
        """凡要合成 app 的动作（deploy / diff / synth / destroy）都必须有 `--vpc`（无隐式默认，ADR 0037 决策 6）；
        缺 → 退 2。不用 argparse 的 `required=True`：那会把 `--bootstrap`（账户级、不合成 app）也拖进来。"""
        if getattr(args, "vpc", None):
            return None
        print("缺 --vpc：VPC 档无隐式默认（default / new / vpc-<id>）——漏给曾合成「新建整套 VPC + 替换 WorkerSg」"
              "的危险变更集（ADR 0037 决策 6）。--bootstrap 不需要它。", file=sys.stderr)
        return EXIT_PRECONDITION

    # ---- context / cdk.json（纯推导，单测直打）----
    def build_context(self, args) -> dict[str, str]:
        """flag → CDK context（app/stack 侧读的那四个旋钮 + 版本戳）。

        `--vpc` 一个 flag 摊成两个旋钮：`default` → `use_default_vpc=true`；`vpc-<id>` → `vpc_id=<id>`；
        `new` → **两个都不给**（stack 的建新分支，见 `stack._network`）。
        `--stop-timeout` 不给则不进 context（让 stack 的默认值说话，不在两处各写一个默认）。
        """
        target = self._resolve_target(args)
        ctx: dict[str, str] = {"prefix": target.prefix, "version": self._resolve_version(args)}
        vpc = getattr(args, "vpc", None)
        if not vpc:  # 调用点已经 _require_vpc 过；这里是契约守卫，不是用户提示
            raise ValueError("build_context 需要 args.vpc（VPC 档无隐式默认，ADR 0037 决策 6）——调用前先过 _require_vpc")
        if vpc == "default":
            ctx["use_default_vpc"] = "true"
        elif vpc != "new":
            ctx["vpc_id"] = vpc
        if getattr(args, "stop_timeout", None) is not None:
            ctx["stop_timeout"] = str(args.stop_timeout)
        return ctx

    def app_command(self) -> str:
        """生成的 `cdk.json` 里的 `app`：用**当前解释器**跑本包的 CDK app。

        必须是 `sys.executable`、不是裸 `python`——部署方多半用 `uv tool install` 装的隔离环境，PATH 上的
        `python` 未必装了 `gherkai-deploy-aws`（asset 还要从**本 venv** 已安装包复制，见 `stack._build_lambda_asset`）。
        `shlex.quote`：cdk 把 `app` 交给 shell 执行，macOS 上解释器路径常带空格。
        """
        return f"{shlex.quote(sys.executable)} -m gherkai_deploy_aws.app"

    def write_cdk_json(self, work_dir: Path) -> Path:
        """在临时工作目录生成 `cdk.json`（ADR 0037 决策 6）——**不再有入库的 cdk.json**：它曾假定自己躺在
        monorepo 里（`app = "uv run python app.py"`），wheel 用户不可达。只写 app + 特性开关；设计旋钮走 `-c`。"""
        path = work_dir / "cdk.json"
        path.write_text(
            json.dumps({"app": self.app_command(), "context": dict(CDK_FEATURE_FLAGS)}, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    # ---- 内部：cdk 调用 ----
    @contextlib.contextmanager
    def _work_dir(self):
        """一次调用的临时工作目录：生成的 `cdk.json` + `cdk.out` + Lambda asset 都在里面，用完即删。

        **不写进仓库/包目录**：wheel 装的包目录不该被写，且 `.lambda_build` 那种仓库内落点对 wheel 用户不存在。
        """
        path = Path(tempfile.mkdtemp(prefix="gherkai-deploy-"))
        try:
            yield path
        finally:
            shutil.rmtree(path, ignore_errors=True)

    def _run_cdk(self, verb: str, args, *, extra=(), output: Path | None = None) -> int:
        node_error = check_node()
        if node_error:
            print(node_error, file=sys.stderr)
            return EXIT_PRECONDITION
        cdk_argv = cdk_command()
        if not cdk_argv:
            print("找不到 cdk 也找不到 npx：cdk CLI 是 npm 物，装 Node（≥ %d）后重试（ADR 0037 决策 6）。"
                  % NODE_MIN_MAJOR, file=sys.stderr)
            return EXIT_PRECONDITION

        target = self._resolve_target(args)
        ctx_cache = context_cache_path(target.prefix)
        with self._work_dir() as work_dir:
            self.write_cdk_json(work_dir)
            # **CDK 环境查询缓存（`cdk.context.json`）跨调用持久化**：工作目录是一次性的，若每次都空着进去，cdk 对
            # `from_lookup`（`--vpc default|<id>`）缺失的值会先用占位 VPC/子网**预合成一遍**再去真查——aws-cdk-lib 的
            # 模板校验器对那份占位模板报错、降级成「Template validation found issues」warning 打出来（真跑抓到、
            # 全新目录 100% 复现、有缓存即消失），而且每次多一轮查询 API。CDK 自己的标准做法就是把该文件保留
            # （它建议入库），这里放在用户缓存目录、按 prefix 一份；`--refresh-context` 丢弃重查（VPC/子网真变了时用）。
            work_ctx = work_dir / "cdk.context.json"
            if getattr(args, "refresh_context", False):
                if ctx_cache.exists():
                    ctx_cache.unlink()
                    print(f"已丢弃 CDK 环境查询缓存 {ctx_cache}，本次重新查询。", file=sys.stderr)
            elif ctx_cache.exists():
                shutil.copyfile(ctx_cache, work_ctx)
            # 用户给的导出目录钉成**绝对**路径：cdk 子进程 cwd = 本次临时工作目录（用完即删），相对路径
            # 原样传会让导出物落进那里、随目录消失而命令退 0（真跑踩过）。默认落工作目录、随之清理。
            out_dir = output.resolve() if output is not None else work_dir / "cdk.out"
            argv = [*cdk_argv, verb, "--app", self.app_command(), "--output", str(out_dir)]
            for key, value in self.build_context(args).items():
                argv += ["-c", f"{key}={value}"]
            if target.profile:
                argv += ["--profile", target.profile]  # cdk 原生 flag（凭证解析归它）
            argv += list(extra)

            env = os.environ.copy()
            # asset 落进本次工作目录（由本方法负责清理）——env 名与「为何走 env 不走 context」见
            # `names.LAMBDA_ASSET_DIR_ENV`，读侧是 `stack.BackendStack._build_lambda_asset`。
            env[names.LAMBDA_ASSET_DIR_ENV] = str(work_dir)
            if target.region:  # cdk 无 --region；region 经 env 传（app 侧由 cdk 注入 CDK_DEFAULT_REGION）
                env["AWS_REGION"] = target.region
                env["AWS_DEFAULT_REGION"] = target.region
            try:
                rc = subprocess.run(argv, cwd=str(work_dir), env=env).returncode
            except FileNotFoundError as exc:  # cdk/npx 在 which 之后消失（极少见）——别抛 traceback
                print(f"起不动 cdk CLI：{exc}", file=sys.stderr)
                return EXIT_PRECONDITION
            if work_ctx.exists():  # cdk 查过/更新过 → 存回缓存（失败与否都存：查到的值本身是对的）
                ctx_cache.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(work_ctx, ctx_cache)
            return rc

    # ---- 内部：VPC 档三态 ----
    def _guard_vpc_spec(self, args) -> int | None:
        """deploy 前的 VPC 档比对。放行 → None；拦 → 退出码（2）。

        只在 deploy 前跑（见 `diff`/`destroy` 的 docstring）。读失败（凭证/权限/网络）也退 2 而非抛 traceback：
        对用户是「先修凭证」，与 Node 缺失同一档。
        """
        target = self._resolve_target(args)
        stack = names.stack_name(target.prefix)
        try:
            cfn = _make_cfn_client(region=target.region, profile=target.profile)
            exists = _stack_exists(cfn, stack)
            stored = None
            if exists:
                ssm = _make_ssm_client(region=target.region, profile=target.profile)
                stored = _read_stored_vpc_spec(ssm, target.prefix)
        except Exception as exc:
            print(f"读不到后端 VPC 档（stack {stack} / SSM {names.ssm_vpc_path(target.prefix)}）：{exc}\n"
                  f"需要 cloudformation:DescribeStacks 与 ssm:GetParameter 权限，以及可用的凭证/region。",
                  file=sys.stderr)
            return EXIT_PRECONDITION

        state = classify_vpc_state(stack_exists=exists, stored_spec=stored, requested=args.vpc)
        if state in (VPC_FIRST_DEPLOY, VPC_MATCH):
            return None

        allow = bool(getattr(args, "allow_vpc_change", False))
        path = names.ssm_vpc_path(target.prefix)
        if state == VPC_UNRECORDED:
            message = (
                f"stack {stack} 已存在，但 {path} 没有 VPC 档记录——这个部署早于 VPC 档登记机制，"
                f"本次 deploy 无从核对 `--vpc {args.vpc}` 是否与当初一致。**这恰是最危险的那一次 deploy**："
                f"档给错会合成「新建整套 VPC + 替换 WorkerSg」的变更集（真踩过）。"
            )
        else:
            message = (
                f"`--vpc {args.vpc}` 与后端记录的 VPC 档 `{stored}` 不一致（{path}）。换档 = VPC 级资源替换，"
                f"worker 网络会被重建。"
            )
        if allow:
            print(f"警告：{message}\n已带 --allow-vpc-change，放行本次（deploy 成功后档会写成 `--vpc {args.vpc}`）。",
                  file=sys.stderr)
            return None
        print(f"{message}\n出路：① 先 `gherkai deploy --diff`（带同一组 flag）核对变更集；"
              f"② 确认无误后带 `--allow-vpc-change` 放行这一次（ADR 0037 决策 6 三态）。", file=sys.stderr)
        return EXIT_PRECONDITION

    # ---- 内部：prefix/region/profile 与版本 ----
    @staticmethod
    def _resolve_target(args):
        """prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR 0016
        决策 C / 0033 两层命名）——部署侧与 run/submit 侧解析出的 prefix 必须恒等，否则 deploy 到一套资源、
        run 连另一套。惰性 import：`--help` 不该为此拉起 core。"""
        from gherkai_runtime import compose

        return compose.resolve_cloud_target(
            prefix=getattr(args, "prefix", None),
            region=getattr(args, "region", None),
            profile=getattr(args, "profile", None),
        )

    @staticmethod
    def _resolve_version(args) -> str:
        """写进 SSM 版本戳的版本（ADR 0037 决策 6「版本戳」/ 决策 7 版本单旋钮）。

        优先 CLI 皮交进来的 `args.version`（= 运行中的 CLI 的版本，决策 7 比对的正是它）；缺则本包自报 dist
        版本——两者被 `==` lockstep pin 成同一个（决策 2b），此回落不引入第二个真源。都取不到 → fail-fast：
        戳写错比缺失更坏（缺失是「警告不拦」，写错会让所有提交者的 skew 判定失真）。
        """
        explicit = getattr(args, "version", None)
        if explicit:
            return str(explicit)
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as dist_version
        try:
            return dist_version("gherkai-deploy-aws")
        except PackageNotFoundError as exc:  # 源码直跑、未装成包
            raise RuntimeError(
                "取不到版本号：本包未以发行包形式安装（源码直跑）。后端版本戳无隐式默认——"
                "装成包（`uv tool install 'gherkai[deploy-aws]'` 或 workspace `uv sync`）后再部署"
            ) from exc


# ---------------------------------------------------------------------------
# Node / cdk CLI 前置（ADR 0037 决策 6「Node 前置是硬事实」）
# ---------------------------------------------------------------------------

def context_cache_path(prefix: str) -> Path:
    """CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省 `~/.cache`）`/gherkai/cdk-context/<prefix>cdk.context.json`。
    按 prefix 一份（各环境可各自 `--refresh-context`，互不牵连）；不入仓库/包目录（wheel 用户没有可写的源码树）。"""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return Path(base) / "gherkai" / "cdk-context" / f"{prefix}cdk.context.json"


def cdk_command() -> list[str]:
    """cdk CLI 的调用前缀：PATH 上的 `cdk` 优先，否则 `npx -y aws-cdk@2`（ADR 0037 决策 6）。都没有 → 空列表。"""
    exe = shutil.which("cdk")
    if exe:
        return [exe]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-y", "aws-cdk@2"]
    return []


def _node_major(node: str) -> int | None:
    """`node --version` 的主版本号；取不到/认不出 → None（**不据此拦**，版本探测失败不该挡住部署）。"""
    try:
        out = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    raw = (out.stdout or "").strip().lstrip("v").split(".")[0]
    return int(raw) if raw.isdigit() else None


def check_node() -> str | None:
    """Node 前置：缺失/过低 → 返回给人看的一句话；OK → None。**不抛 traceback**（ADR 0037 决策 6）。

    为何必查：`aws-cdk-lib` 是 jsii 绑定，**app 子进程 import 即起 node**；cdk CLI 本身也是 npm 物。
    缺 node 的原生症状是 jsii 在子进程里抛一段与 Node 无关的堆栈，对用户是纯噪声。
    """
    node = shutil.which("node")
    if node is None:
        return (
            f"找不到 node：`gherkai deploy` 需要 Node ≥ {NODE_MIN_MAJOR} 在 PATH——CDK 的 Python 绑定是 jsii"
            f"（import 即起 node 子进程），cdk CLI 本身也是 npm 物（ADR 0037 决策 6）。装好 Node 后重试。"
        )
    major = _node_major(node)
    if major is not None and major < NODE_MIN_MAJOR:
        return (
            f"node 版本过低：{node} 是 v{major}，需要 ≥ {NODE_MIN_MAJOR}"
            f"（与 worker 的 engines.node 同一下限，ADR 0037 决策 6）。"
        )
    return None
