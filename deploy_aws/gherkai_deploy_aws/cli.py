"""`gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws` 项，ADR 0037 决策 6）。

**本模块是 CLI 前端与 CDK 之间的唯一接缝**，形状由一条硬约束定死：**CLI 绝不 import `aws_cdk`**——它是 jsii 绑定，
import 即起 node 子进程（ADR 0037 决策 6）。故本模块自身**模块级**只 import 标准库 + 本包 `names`，其余
（`boto3`、`gherkai_runtime.compose`、`gherkai_runtime.devicefarm`、本包 `container` / `workers`）一律函数内惰性 import——一律零 `aws_cdk`；
stack/app 只经 **cdk CLI 起的子进程** 触达（`app.py`）。CLI 侧 `--help` 因此不付 node 代价。

## 接缝契约（CLI 前端 ↔ Provider）

CLI 前端负责：
- 发现 provider（entry point group `gherkai.deploy`：零个 → 提示装 `gherkai[deploy-aws]`；一个 → 无需
  `--provider`；多个 → 必给），实例化，调 `add_arguments(subparser)` 让 provider 贡献自己的 flag；
- 声明 **provider 中立的命令面 flag** 并据其选调本类哪个方法（ADR 0037 决策 6「命令面」）：
  `--diff` → `diff`、`--synth-only DIR` → `synth_only`（DIR 落 `args.synth_only`）、`--bootstrap` →
  `bootstrap`，都不给 → `deploy`；`gherkai destroy` → `destroy`；
- 先声明 `--require-approval` 与 `--allow-vpc-change` 的**中立版**，使 `deploy --help` 在**没装任何 provider**
  时也列得出这两个动作选项；
- 可选把自身版本放进 `args.version`（缺则本包自报 dist 版本，见 `_resolve_version`）；
- `gherkai doctor` 时若 provider 提供**可选**的 `doctor(args) -> list[dict]`（每项 `{name, ok, detail}` + 可选 `required`，
  缺省 False；只读、不返退出码），把它并进自检输出的 provider 段（ADR 0041 决策四）。

Provider 负责（CLI 一概不懂）：`--prefix`/`--vpc`/`--stop-timeout` 三个 context 配置项 + AWS 概念的
`--region`/`--profile`（CLI 前端不在 deploy/destroy 子命令上声明这五个）、context 拼装、`cdk.json` 生成、
cdk CLI 调用、VPC 取值三态比对、工具链前置检查（Node ≥ 22 与 cdk CLI 可定位，见 `_toolchain_gate`），以及云端 Device Farm
项目 `{prefix}devices`：deploy 在 VPC 取值三态之后、cdk 之前找回或建立它（经 `gherkai_runtime.devicefarm`），ARN 作为命令
派生的 context `device_farm_project` 交给 stack；diff / --synth-only / destroy 不建立项目，只读 SSM 现值，diff 另用 GetProject
核对记录的项目是否还在（ADR 0051 决策 10，见 `_resolve_device_farm_project_for_deploy` 与 `_stored_device_farm_project`）。

**`--require-approval` / `--allow-vpc-change` 是有意的两层声明**：前端给中立版（provider 缺席时帮助不残缺），
本类**再声明一次**带 AWS 语义的版本（`--require-approval` 的取值是 cdk 的三个审批级别，能 `choices` 校验；
`--allow-vpc-change` 的措辞要点名 VPC 取值三态）。前端的 subparser 开了 `conflict_handler="resolve"`，同名即
以后贴的（本类）为准——两层不是重复真源，是「中立占位 + provider 精确化」。两层都**只贴 deploy**：destroy
不消费它们（不做 VPC 取值三态比对，cdk destroy 也没有 `--require-approval`），前端的中立版同样只在 deploy 上。
本类另经 `getattr` 容忍它们彻底缺席（别的前端）：缺 `--allow-vpc-change` 即一律不放行（fail-closed）、
缺 `--require-approval` 即交给 cdk 默认。

## worker 镜像子动词（ADR 0038 命令族）

`add_arguments(deploy_parser)` 里自贴 `push-worker` / `list-workers` / `delete-worker` 三个子动词，各自
`set_defaults(_deploy_verb=<本类方法>)`——前端的分派**先看 `_deploy_verb`**（前端一行不改，见其契约块）。
云端写操作（推 ECR、注册 task-def revision、写 SSM 指针）全属部署变更，故住本包、不住 CLI 本体；实现在
`workers.py`，容器引擎在 `container.py`。子动词只挂 deploy、不挂 destroy（理由见 `_declares_worker_subverbs`）。

## 退出码

`0` 成功；`2` **前置/校验失败**（Node 缺失或 cdk CLI 定位不到、VPC 取值不符或无记录、prefix/region/profile 解析不出
（`--profile` 名不存在等，见 `_resolve_target_or_report`）、读后端失败（含读不到 SSM 里的 Device Farm 项目记录、记录不是合法的项目 ARN、diff 核对记录里的项目时
遇到权限以外的错误）、同名 Device Farm 项目不止一个、容器引擎名不认、push-worker 的架构/skew 拦截——部署方可修，对齐 CLI 既有
preflight 退出码 2 的口径）；**`1`** 表示 cdk 已成功而 worker 镜像四步失败（账户已被改动，重新运行 `gherkai deploy` 幂等收敛，
ADR 0038），或 deploy 在 cdk 之前找回或建立 Device Farm 项目时遇到权限以外的错误（限流、网络、服务端故障；不猜测，
stack 未改动，重新运行会沿用已建立的同名项目，ADR 0051 决策 10）；其余是 cdk CLI 自己的返回码（原样透传，
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
EXIT_FAILED = 1        # 执行失败、可重新运行收敛（与 `workers.EXIT_FAILED` 同值，见模块头「退出码」）
EXIT_PRECONDITION = 2  # 前置/校验失败（与 CLI preflight 同一类，见模块头「退出码」）

# `_run_cdk` 的 `device_farm_project` 缺省值：调用方没有找回或建立项目，由 `_run_cdk` 只读 SSM 现值（diff / --synth-only /
# destroy）。用哨兵而不是 None：None 是「已解析、本次没有可用的 ARN」（deploy 无权限且无记录时），两者处置不同。
_READ_STORED_PROJECT = object()

# Node 下限：与 worker 的 `engines.node` 同一下限（ADR 0037 决策 6「Node 前置是硬事实」，README 一处说清）。
NODE_MIN_MAJOR = 22

# `cdk.json` 的 `context`：CDK **特性开关**（feature flags）。**逐字沿用收编前 `iac_aws_backend/cdk.json` 的那一组**——
# 特性开关会改变合成出的资源形态，换一组就等于给已部署 stack 造出无意义的变更集。加/删任何一项前先 `--diff` 核对。
# （设计参数不在这里：prefix/vpc/stop_timeout/version/device_farm_project 一律经 `-c k=v` 显式传，不进生成的 cdk.json——见 `build_context`。）
CDK_FEATURE_FLAGS: dict[str, object] = {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": True,
    "@aws-cdk/core:checkSecretUsage": True,
    "@aws-cdk/aws-iam:minimizePolicies": True,
    "@aws-cdk/core:validateSnapshotRemovalPolicy": True,
    "@aws-cdk/aws-ecs:disableExplicitDeploymentControllerForCircuitBreaker": True,
    "@aws-cdk/core:target-partitions": ["aws", "aws-cn"],
}

# VPC 取值比对的四种判定（ADR 0037 决策 6「VPC 取值持久化比对，三态齐全」——「三态」指 stack / 记录 / 参数三个输入；`classify_vpc_state` 的返回值）
VPC_FIRST_DEPLOY = "first-deploy"  # ① stack 不存在即真首次部署 → 放行
VPC_UNRECORDED = "unrecorded"      # ② 参数缺失且 stack 已存在即本机制之前部署的环境 → 以退出码 2 结束（最危险的那一次）
VPC_MATCH = "match"                # ③ 取值一致 → 放行
VPC_MISMATCH = "mismatch"          # ③ 取值不一致 → 以退出码 2 结束

# `delete-worker` 的占位文案（ADR 0038「命令族」）：`--help` 的 description 与真敲下去看到的那句**同源**，
# 别让帮助与运行时给出两种说法。清理规则不写死时长——真源是 `workers.RETIRE_QUIET_PERIOD`，写死即漂移。
DELETE_WORKER_PLACEHOLDER = (
    "`delete-worker` 尚未提供。\n"
    "将来提供时会沿用 push-worker 的同一套清理规则（退休一段时间、且没有未结束的 run 还在用它才真删），"
    "并一并回收旧版本 variant 的 ECR 标签、重推时被顶掉的旧镜像层与 worker 镜像映射。\n"
    "当前可用的：`gherkai deploy list-workers` 看有哪些 variant 与待清理 revision；"
    "重推同名 variant 直接覆盖，无需先删。"
)


# ---------------------------------------------------------------------------
# VPC 取值（纯逻辑，与 boto3 解耦——三态判定是这套机制的正确性核心，单测直打它）
# ---------------------------------------------------------------------------

def vpc_spec_matches(stored: str, requested: str) -> bool:
    """SSM 里记的生效取值 `stored` 是否与本次 `--vpc requested` 一致。

    三种取值形态见 `names.ssm_vpc_path`。`new` 取值在 SSM 里是 `new:<所建 vpc-id>`（带出所建 id 以便回溯核对），
    故 `--vpc new` 按 **`new:` 前缀** 匹配、不逐字比。
    **反过来不成立**：`stored="new:vpc-abc"` 与 `--vpc vpc-abc` **不算一致**——前者是「VPC 由本 stack 拥有」、
    后者是「复用一个 stack 外的 VPC」，切换会让 CloudFormation 把它从 stack 里摘出去（即删掉那个 VPC）。
    """
    if requested == "new":
        return stored == "new" or stored.startswith("new:")
    return stored == requested


def classify_vpc_state(*, stack_exists: bool, stored_spec: str | None, requested: str) -> str:
    """三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。

    判序里 **stack 是否存在先于参数是否存在**：真首次部署时两者都缺，若先看参数就会把首次部署误判成
    「本机制之前部署的环境」而拦下每一个新环境的第一次 deploy。
    """
    if not stack_exists:
        return VPC_FIRST_DEPLOY
    if not stored_spec:
        return VPC_UNRECORDED
    return VPC_MATCH if vpc_spec_matches(stored_spec, requested) else VPC_MISMATCH


def _vpc_flag(value: str) -> str:
    """`--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三种取值，**无隐式默认**（ADR 0037 决策 6；
    三者与 ADR 0033「VPC 来源：三种取值」一节一一对应）。"""
    if value in ("default", "new") or (value.startswith("vpc-") and len(value) > len("vpc-")):
        return value
    raise argparse.ArgumentTypeError(
        f"--vpc 须是 default（用账户的默认 VPC）/ new（新建一套）/ vpc-<id>（用现有的某个）之一，得到 {value!r}"
    )


# —— 造 boto3 句柄的几个钩子（抽出来供测试 monkeypatch，验三态逻辑而不连真 AWS；同 compose 的 `_make_*` 惯例）——
def _make_cfn_client(*, region, profile):
    """boto3 cloudformation client（`DescribeStacks` 探 stack 是否已存在）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("cloudformation")


def _make_sts_client(*, region, profile):
    """boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("sts")


def _make_ssm_client(*, region, profile):
    """boto3 ssm client（读生效 VPC 取值参数）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("ssm")


def _has_aws_credentials(*, profile) -> bool:
    """凭证链能否解析出任何凭证（`--synth-only` 判断「完全没有凭证」用，ADR 0051 决策 10 的唯一例外）。

    不调用 AWS 服务的 API，也不需要 region。凭证链前面各项都为空时，boto3 会向实例元数据端点发两次请求（取令牌、取凭证，各有
    1 秒连接超时），所以在 EC2 之外完全没有凭证时离线导出会延迟约 2 秒。凭证过期或无效不在这里判断，由之后实际读取时的报错处理。
    """
    import boto3
    return boto3.session.Session(profile_name=profile).get_credentials() is not None


def _make_hint_clients(*, region, profile):
    """「缺 --vpc」提示专用的短超时句柄：纯参数错误不该被网络拖住（连不上即放弃、不重试）。

    与 `_make_cfn_client` / `_make_ssm_client` 分开是有意的：那两个服务的是机制正确性（VPC 取值三态）、
    值得等；这一个只为把提示写具体，超时预算必须有上限。
    """
    import boto3
    session = boto3.session.Session(profile_name=profile, region_name=region)
    # `total_max_attempts` 数的是**总尝试次数**；legacy 语义的 `max_attempts` 数的是重试次数
    # （给 1 就是共两次尝试、超时预算翻倍），这里要的是「只试一次」。
    config = boto3.session.Config(connect_timeout=2, read_timeout=3, retries={"total_max_attempts": 1})
    return session.client("cloudformation", config=config), session.client("ssm", config=config)


# 凭证、region 或配置不可用一类的 botocore 异常：按异常类的 MRO 类名匹配（基类名覆盖子类，如 SSOError 覆盖 SSOTokenLoadError），
# 不 import botocore；另加令牌类的错误码。签名错误（InvalidSignatureException 等）不在此列：代理改写已签名请求也会产生它，断不了
# 是凭证问题，留给兜底提示。读 SSM 记录失败时据此提示去配凭证与 region，而不是列权限。
_CREDENTIAL_ERROR_NAMES = frozenset({
    "NoCredentialsError", "PartialCredentialsError", "CredentialRetrievalError", "TokenRetrievalError", "NoAuthTokenError",
    "RefreshWithMFAUnsupportedError", "SSOError", "LoginError",
    "NoRegionError", "InvalidRegionError", "ProfileNotFound", "ConfigNotFound", "ConfigParseError", "InvalidConfigError",
})
_CREDENTIAL_ERROR_CODES = frozenset({
    "ExpiredToken", "ExpiredTokenException", "InvalidClientTokenId", "UnrecognizedClientException",
    "MissingAuthenticationToken", "MissingAuthenticationTokenException",
})


def _is_credential_error(exc: BaseException) -> bool:
    """凭证、region 或配置不可用一类的错误：异常类 MRO 上任一类名在 `_CREDENTIAL_ERROR_NAMES`，或错误码在 `_CREDENTIAL_ERROR_CODES`。"""
    return bool({c.__name__ for c in type(exc).__mro__} & _CREDENTIAL_ERROR_NAMES) or _error_code(exc) in _CREDENTIAL_ERROR_CODES


def _ssm_read_failure_hint(exc: BaseException) -> str:
    """读 SSM 里的 Device Farm 项目记录失败时的「怎么办」半句（ADR 0051 决策 10「失败消息的形态」）：只有 GetParameter 本身被拒才
    列权限；凭证链里别的调用被拒（如 profile 配置的 AssumeRole）、凭证或 region 一类的异常提示去配；其余（限流、网络、服务端故障）
    不猜原因、不说成权限问题。无权限的判定与 Device Farm 侧共用同一份错误码集合。"""
    from gherkai_runtime import devicefarm

    denied = devicefarm.is_access_denied(exc)
    if denied and getattr(exc, "operation_name", None) == "GetParameter":
        return "需要该参数的 ssm:GetParameter 权限。"
    if denied or _is_credential_error(exc):
        return "需要可用的凭证与 region（--profile / AWS_PROFILE，--region / AWS_REGION）。"
    return "请按上面的错误信息处理；限流、网络或服务端故障可稍后重试。"


def _error_code(exc: Exception) -> str | None:
    """botocore ClientError 的 `Error.Code`（非 ClientError → None）。不 import botocore：本包不该为读一个
    错误码把 botocore 变成 import 期依赖，鸭子类型足够（compose.read_backend_version 同样处理）。"""
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
    """读 SSM 里的生效 VPC 取值；`ParameterNotFound` → None（即本机制之前部署的环境，由三态判定处置）。"""
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

    # ---- flag 面（ADR 0037 决策 6：三 flag 对齐 stack 与 app 的全部 context 配置项）----
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """把 provider 特有 flag 挂上 CLI 给的 parser。

        `prefix`/`vpc_id`/`use_default_vpc`/`stop_timeout` 四个 context 配置项映射为**三个** flag：`--vpc`
        一个吞掉 `vpc_id` + `use_default_vpc` 两个配置项（ADR 0037 决策 6）。`version` 这一项不给 flag——
        版本按版本真源来、由安装本身决定（决策 7），不让部署方手填。`device_farm_project` 同样不给 flag：ARN 由命令
        找回或建立、或读 SSM 现值得到（ADR 0051 决策 10），手填只会多出写错的机会。
        """
        parser.add_argument(
            "--prefix", default=None, metavar="P",
            help="资源名前缀（默认 gherkai-，或 AWS_RESOURCE_PREFIX）；**须与 run/submit 的 --prefix 一致**",
        )
        parser.add_argument(
            "--vpc", default=None, type=_vpc_flag, metavar="取值",
            help="VPC 来源三种取值：default（账户默认 VPC）/ new（本 stack 新建，2-AZ 零 NAT）/ vpc-<id>（复用现有）。"
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
        # 下面两个是**前端已声明的中立版的 AWS 精确化**（`conflict_handler="resolve"` 令本处生效，见模块头
        # 「两层声明」）：一个加 cdk 的取值 `choices`、一个把措辞钉到 VPC 取值三态上。
        # **只贴 deploy**：destroy 两个都不消费（不做 VPC 取值三态比对，cdk destroy 也没有 `--require-approval`），
        # 贴上去就是 `--help` 里两个恒无效的选项。`prog` 认不出时仍贴（同 `_is_destroy_parser` 的降级口径：
        # 无 prog 的 parser 要拿得到全集）。
        if not self._is_destroy_parser(parser):
            parser.add_argument(
                "--allow-vpc-change", action="store_true",
                help="放行一次 VPC 取值变更/首次登记（默认拦：取值与后端记录不符即以退出码 2 结束，先 --diff 核对变更集）",
            )
            parser.add_argument(
                "--require-approval", default=None,
                choices=("never", "any-change", "broadening"),
                help="透传 cdk 的 IAM 变更审批级别（不给则用 cdk 自己的默认值）",
            )
        # --region/--profile 归 provider（AWS 概念）：CLI 前端不在本子命令上声明，见模块头接缝契约。
        parser.add_argument("--region", default=None, metavar="R", help="AWS region（默认走 AWS_REGION/profile 配置）")
        parser.add_argument("--profile", default=None, metavar="P", help="AWS profile（默认 AWS_PROFILE）")
        if self._is_destroy_parser(parser):
            # destroy 专属：cdk destroy 在非 TTY 下**拒绝**无确认的销毁（「terminal (TTY) is not attached」，以退出码 1 结束，实际运行撞到）。
            # 默认保留 cdk 的交互确认（销毁不可逆，两道确认不多）；脚本/跳板机 nohup 这类非交互场景显式 --yes。
            parser.add_argument(
                "--yes", action="store_true",
                help="不再询问确认（即 cdk destroy --force）；非交互/脚本用，交互终端下默认由 cdk 询问一次",
            )
        # worker 镜像子动词（ADR 0038 命令族）——**只贴在 deploy 上**，见 `_declares_worker_subverbs`。
        if self._declares_worker_subverbs(parser):
            # deploy 自己也消费容器引擎（第 2 步同步基础镜像 pull/push）——flag 贴在 deploy 上，子动词 push-worker 再贴
            # 一份（子 parser 是独立 namespace，SUPPRESS 默认值让「deploy --container-engine X push-worker …」不被覆写）。
            self._add_container_engine_flag(parser)
            self._add_worker_subverbs(parser)

    @staticmethod
    def _is_destroy_parser(parser: argparse.ArgumentParser) -> bool:
        """这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。"""
        return (parser.prog or "").split()[-1:] == ["destroy"]

    # ---- worker 镜像子动词（ADR 0038「命令族」；接缝是前端先看 args._deploy_verb，见模块头/前端的契约块）----
    @staticmethod
    def _declares_worker_subverbs(parser: argparse.ArgumentParser) -> bool:
        """这个 parser 是 **deploy** 的那个吗？

        前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用 provider 的 context 配置项）。子动词只能挂
        deploy：挂上 destroy 的后果不是「多个没用的命令」而是**危险**——前端的 destroy 分派根本不看
        `_deploy_verb`，于是 `gherkai destroy push-worker …` 会解析通过、然后**去拆栈**。
        判据取 `prog` 末段（前端建的是 `sub.add_parser("deploy")` → prog 是 `<前端> deploy`）；认不出就不贴，
        降级是安全的（子动词本来也只经 deploy 这条路可达）。
        """
        return (parser.prog or "").split()[-1:] == ["deploy"]

    def _add_worker_subverbs(self, parser: argparse.ArgumentParser) -> None:
        """`push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。

        **`required=False`（argparse 默认）是硬约束**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样
        解析得过（前端的契约块明写）。每个子动词 `set_defaults(_deploy_verb=<绑定方法>)`，前端据此优先分派。
        """
        sub = parser.add_subparsers(
            title="worker 镜像子命令（不给则本命令是部署/更新后端）", metavar="[子命令]",
        )
        push = sub.add_parser(
            "push-worker", help="[部署方] 推一个本地镜像并注册为某引擎的一个 variant",
            description="推送一个**已 build 好**的本地镜像到本 prefix 的 ECR，并把它注册成该引擎的一个 variant "
                        "（一个 task-def revision，镜像按 digest 引用）。一次一个引擎；两个引擎要分两次执行本命令。"
                        "镜像构建不归 gherkai——定制镜像的 Dockerfile 模板见 https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md 。",
        )
        push.add_argument("image", metavar="<本地镜像>", help="本地镜像名（任何名字，如 acme-novaact:login）")
        push.add_argument("--engine", required=True, choices=names.ENGINES, help="这个镜像是哪个引擎的 worker")
        push.add_argument("--variant", required=True, metavar="名",
                          help="variant 名（一套具名的确定性 step 集，自取：login / checkout-v2；"
                               "ECR tag 形如 <CLI 版本>-<名>）")
        push.add_argument("--set-default", action="store_true",
                          help="同时把默认指针指向这个 variant（提交时不给 --worker-variant 就用它）")
        self._add_container_engine_flag(push)
        self._add_locator_flags(push)
        push.set_defaults(_deploy_verb=self.push_worker)

        listing = sub.add_parser(
            "list-workers", help="[部署方] 列各引擎当前版本的 variant / digest / 默认指针 / 待清理 revision",
            description="按引擎列出**当前版本**（即本 CLI 自身版本）的 variant、digest、推送时间与 revision，"
                        "加上默认指针，以及已退休待清理与孤儿 revision。",
        )
        self._add_locator_flags(listing)
        listing.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                             help="输出机器可读 JSON（prefix/version/default_variant/engines）")
        listing.set_defaults(_deploy_verb=self.list_workers)

        delete = sub.add_parser(
            "delete-worker", help="[部署方] （尚未提供）删一个 variant 及其 ECR/SSM 残留",
            # 取占位文案的前两句（末句「当前可用的…」是敲下去之后的出路，帮助里由别的子命令自陈）
            description="\n".join(DELETE_WORKER_PLACEHOLDER.splitlines()[:2]),
        )
        self._add_locator_flags(delete)
        delete.set_defaults(_deploy_verb=self.delete_worker)

    @staticmethod
    def _add_container_engine_flag(parser: argparse.ArgumentParser) -> None:
        """`--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。"""
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
        （argparse 的经典坑）。SUPPRESS 表示子层没给就不产出这个属性、父层的值自然留住，两处给法都成立。
        """
        parser.add_argument("--prefix", default=argparse.SUPPRESS, metavar="P",
                            help="资源名前缀（须与 `gherkai deploy` / run/submit 的 --prefix 一致）")
        parser.add_argument("--region", default=argparse.SUPPRESS, metavar="R", help="AWS region")
        parser.add_argument("--profile", default=argparse.SUPPRESS, metavar="P", help="AWS profile")

    # ---- 命令面（CLI 前端据它自己的 flag 选调；每个方法自成一次完整调用）----
    def deploy(self, args) -> int:
        """供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），再找回或建立 Device Farm 项目（ADR 0051 决策 10），
        过了才调 `cdk deploy`。项目排在三态之后：被三态拦下的部署不该先在账户里建出项目。"""
        # 工具链前置（Node + cdk CLI）先于 VPC 取值比对，理由见 `_toolchain_gate`。**cdk 可定位性必须也在这一关**：
        # 若只在 `_run_cdk` 里拦，就要等读过后端、比对过 VPC 取值之后才以退出码 2 结束，而那条路径上 cdk 一行输出都没有——
        # 底下「失败原因见上方 cdk 输出」的提示会变成误导（它建议的 `--bootstrap` 也会以同样的原因失败）。
        toolchain = self._toolchain_gate()
        if toolchain is not None:
            return toolchain
        # 容器引擎的两类问题也在这一关处置（本地、不花网络、不要凭证——这一期 deploy 机器需要容器引擎，
        # 同步基础镜像要 pull/push，ADR 0038「容器引擎口子」）：
        # - **名字不认**（env/flag 给了 podman）→ 纯参数问题，以退出码 2 结束、绝不动账户；
        # - **装了但不可用 / 没装** → 只警告：退出码语义归 cdk 之后的四步（账户已改 → 退出码 1、重新运行幂等收敛）。
        #   仍要提前说一声——cdk deploy 是分钟级动作，让人等到运行结束才知道「还差个 docker」是白等。
        engine = self._container_engine(args)
        if engine is None:
            return EXIT_PRECONDITION
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        # 探活警告放在 `--vpc` 校验之后：缺 `--vpc` 会直接以退出码 2 结束，先打两行 docker 警告只会盖住真因。
        # **只对纯发行版探**：非纯发行版（.dev/.post/本地段）第 2 步整步跳过、根本不碰容器引擎（判据与
        # `workers.run_deploy_steps` 共用同一个 `compose.is_pure_release`，ADR 0038「容器引擎口子」），对它们预告
        # 「之后会失败（退出码 1）」是假警告，还会与 `sync_base` 的「跳过基础镜像同步」自相矛盾。
        from gherkai_runtime import compose
        if compose.is_pure_release(self._resolve_version(args)):
            probe = engine.probe()
            if probe:
                print(f"警告：{probe}\n     stack 会照常部署，但之后的 worker 镜像步骤（同步基础镜像）会失败"
                      f"（退出码 1）；装好容器引擎后重新运行 `gherkai deploy` 幂等收敛。", file=sys.stderr)
        blocked = self._guard_vpc_spec(args)
        if blocked is not None:
            return blocked
        blocked, project = self._resolve_device_farm_project_for_deploy(args)
        if blocked is not None:
            return blocked
        extra = ["--require-approval", args.require_approval] if getattr(args, "require_approval", None) else []
        rc = self._run_cdk("deploy", args, extra=extra, device_farm_project=project)
        if rc != EXIT_OK:
            # cdk 自己的报错已在上面原样打出；只补一条**中性**提示、不改写也不猜它的诊断（失败原因很多：
            # 权限、变更集被拒、模板错……）。未 bootstrap 是首次部署最常见的一种（ADR 0037 决策 6）。
            print("提示：cdk deploy 失败原因见上方 cdk 输出。首次在某账户/region 部署最常见的一种是环境未 bootstrap"
                  "——若报错提到 bootstrap，先运行 `gherkai deploy --bootstrap`（同 --profile/--region）。",
                  file=sys.stderr)
            return rc
        # cdk 成功 → worker 镜像四步（ADR 0038）。第 1 步（登记模板）已随 cdk 事务落地。
        return self._worker_image_steps(args, engine)

    def destroy(self, args) -> int:
        """销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。

        不过 VPC 取值三态：destroy 不改 VPC 形态，比对只会拦住「取值记错了但想删干净」的人。
        但 `--vpc` 仍必给：destroy 也要合成 app（stack 的网络分支按取值走），缺了它合成不出同一个 stack。
        Device Farm 项目只读 SSM 现值（见 `_stored_device_farm_project`）；项目本身不归 stack 管理，destroy 保留它
        （含会话记录与录像，ADR 0051 决策 10），stack 写的那个 SSM 参数随 stack 删除。
        """
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        extra = ["--force"] if getattr(args, "yes", False) else []  # 见 add_arguments 的 --yes
        return self._run_cdk("destroy", args, extra=extra)

    def diff(self, args) -> int:
        """只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对——
        对本机制之前部署的环境，`deploy` 以退出码 2 结束时让人运行的就是它，若它也被拦就无路可走。

        **diff 不建立 Device Farm 项目**（ADR 0051 决策 10）：SSM 有记录且 GetProject 核对成功就用记录里的 ARN，没有记录（提示）
        或项目已不存在（警告）就以「待建立」占位。占位时用于计算变更集的模板不含设备支持相关的授权与项目 ARN 参数：已部署的
        模板含它们时（记录的项目已被删除），变更集会显示移除它们；真 deploy 会先找回或建立项目、再带着 ARN 合成，所以首次启用
        设备支持（或记录的项目已被删除）后的那次 deploy 会比 diff 多出这两部分，提示与警告都把这一点说给使用方。读不到记录、记录不是合法的项目 ARN、核对遇到权限以外的失败则以退出码 2 结束；核对被拒则沿用
        记录并警告（见 `_stored_device_farm_project`）。"""
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        return self._run_cdk("diff", args)

    def synth_only(self, args) -> int:
        """导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的
        reviewer 靶点，ADR 0037 决策 6）。目录由 CLI 前端的 `--synth-only DIR` 提供（接缝契约）。

        Device Farm 项目与 diff 同样只读 SSM 现值、不建立；唯一不同是完全没有凭证时回落「待建立」占位并警告，
        保住无凭证离线导出这项既有能力（ADR 0051 决策 10，见 `_stored_device_farm_project`）。"""
        out = getattr(args, "synth_only", None)
        if not out:
            raise ValueError("synth_only 需要 args.synth_only（--synth-only DIR）")
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
        # 部署方给的 DIR 相对**他的** cwd；`_run_cdk` 里把它钉成绝对路径再交给 cdk——cdk 子进程的 cwd 是随后
        # 被删的临时工作目录，相对路径原样传会让导出物落进那里、随之消失而命令却以退出码 0 结束（实际运行踩过）。
        return self._run_cdk("synth", args, output=Path(out).expanduser())

    def bootstrap(self, args) -> int:
        """`cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。

        显式给 `aws://<account>/<region>` 且**不带 `--app`**：cdk 有显式环境又没有 app 时直奔凭证与 bootstrap
        stack（实际运行核过：带 `--app` 则即使给了显式环境也会先执行 app——那就又要 `--vpc` 了）。
        account 经 STS `GetCallerIdentity` 取（对任何主体恒可用、不算新增权限）；region 走同一条解析链
        （`--region` / AWS_REGION / profile 配置），取不到 → 以退出码 2 结束（bootstrap stack 是按 region 建的，不能猜）。
        """
        blocked = self._toolchain_gate()
        if blocked is not None:
            return blocked
        cdk_argv = cdk_command()
        target = self._resolve_target_or_report(args)
        if target is None:
            return EXIT_PRECONDITION
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

    # ---- 命令面（worker 镜像族，ADR 0038「命令族」；前端经 args._deploy_verb 分派到 push_worker / list_workers / delete_worker）----
    def push_worker(self, args) -> int:
        """`gherkai deploy push-worker <镜像> --engine … --variant …`（八步见 `workers.push_worker`）。"""
        from gherkai_deploy_aws import workers

        engine = self._container_engine(args)
        if engine is None:
            return EXIT_PRECONDITION
        target = self._resolve_target_or_report(args)
        if target is None:
            return EXIT_PRECONDITION
        return workers.push_worker(
            args.image, engine=args.engine, variant=args.variant,
            set_default=bool(getattr(args, "set_default", False)),
            # tag 用的版本是 **CLI 自身版本**（与写进 SSM 的戳同一个，ADR 0038「preflight」按它解析）
            cli_version=self._resolve_version(args),
            prefix=target.prefix, region=target.region, profile=target.profile, container=engine,
        )

    def list_workers(self, args) -> int:
        """`gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。"""
        from gherkai_deploy_aws import workers

        target = self._resolve_target_or_report(args)
        if target is None:
            return EXIT_PRECONDITION
        return workers.list_workers(prefix=target.prefix, cli_version=self._resolve_version(args),
                                    region=target.region, profile=target.profile,
                                    as_json=getattr(args, "json", False))

    # ---- 命令面（doctor 的 provider 段，ADR 0041 决策四；由 `gherkai doctor` 入口直调，不属 worker 镜像族、不经 _deploy_verb）----
    def doctor(self, args) -> list[dict]:
        """`gherkai doctor` 的 provider 段（ADR 0041 决策四）：部署方工具链**只读**自检——Node ≥ 22、cdk 可定位、容器引擎可用。

        收的是 doctor 的 Namespace（不是 deploy 的），故一律 getattr 取值。三项一律 required=False：provider 段是**部署
        能力清单**——doctor 不知道这台机器要不要部署，装了 extra 的提交者缺 node 不该被判环境坏掉；真正的硬拦在
        `gherkai deploy` 自身（check_node / 容器引擎探活，ADR 0038）。缺项由入口在人读尾行单独点出。"""
        from gherkai_deploy_aws.container import UnsupportedContainerEngine, resolve_container_engine

        checks: list[dict] = []
        node_err = check_node()
        checks.append({"name": "node", "ok": node_err is None, "required": False,
                       "detail": node_err or f"node {shutil.which('node')}"})
        cdk = cdk_command()
        checks.append({"name": "cdk", "ok": bool(cdk), "required": False,
                       "detail": " ".join(cdk) if cdk else "找不到 cdk 也找不到 npx：装 Node（自带 npx）或 npm i -g aws-cdk"})
        try:
            engine = resolve_container_engine(getattr(args, "container_engine", None))
            probe = engine.probe()
            checks.append({"name": "container-engine", "ok": probe is None, "required": False,
                           "detail": probe or f"{engine.name} 可用（同步基础镜像 / push-worker 用）"})
        except UnsupportedContainerEngine as exc:
            checks.append({"name": "container-engine", "ok": False, "required": False, "detail": str(exc)})
        return checks

    # ---- 命令面（worker 镜像族续，ADR 0038「命令族」）----
    def delete_worker(self, args) -> int:
        """留的口子（ADR 0038「命令族」）：**尚未提供**，以退出码 2 结束并说清为什么与将来怎么落。

        为何占位而不干脆不给这个子命令：不给的话部署方敲了只会得到 argparse 的「invalid choice」，读不出
        「这件事是被想过、押后了」——而它押后的是**回收策略**（ECR untagged 层、旧版本 variant），不是忘了
        （属 ADR 0038 重议闸门）。
        """
        print(DELETE_WORKER_PLACEHOLDER, file=sys.stderr)
        return EXIT_PRECONDITION

    # ---- 内部：容器引擎（ADR 0038「容器引擎口子」）----
    @staticmethod
    def _container_engine(args):
        """解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点以退出码 2 结束）。

        **只解析、不探活**：探活（`probe()`）归真要用它的那一步——push-worker 在 skew 前置之后探（skew 拦下的
        人不该先被要求装 docker），deploy 的四步在 cdk 之后探（见 `_worker_image_steps`）。
        """
        from gherkai_deploy_aws.container import UnsupportedContainerEngine, resolve_container_engine

        try:
            return resolve_container_engine(getattr(args, "container_engine", None))
        except UnsupportedContainerEngine as exc:
            print(str(exc), file=sys.stderr)
            return None

    def _worker_image_steps(self, args, engine) -> int:
        """cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。

        `engine` 由 `deploy` 解析好传进来：名字不认在 cdk 之前就以退出码 2 结束了（ADR 0038「容器引擎口子」），到这里必是
        已实装的引擎；「装了但不可用」归 `workers.run_deploy_steps`（退出码 1）。

        **不做版本 skew 前置**：deploy 就是改戳的那个动作（ADR 0038）。失败给退出码 1（不是 2）——账户已经被 cdk
        改过了，压成「前置失败」会让人以为什么都没发生。
        """
        from gherkai_deploy_aws import workers

        target = self._resolve_target_or_report(args)
        if target is None:
            # 退出码归属按本方法契约（见 docstring）：cdk 之后的失败给退出码 1，措辞与 `workers.run_deploy_steps`
            # 建不出句柄时那一支相同——对部署方是同一件事。
            print("stack 已生效；worker 镜像步骤未完成——重新运行 `gherkai deploy` 幂等收敛。", file=sys.stderr)
            return workers.EXIT_FAILED
        return workers.run_deploy_steps(
            prefix=target.prefix, version=self._resolve_version(args), container=engine,
            region=target.region, profile=target.profile,
        )

    # ---- 内部：部署工具链前置（Node / cdk；ADR 0037 决策 6）——与下面的容器引擎口子无关 ----
    @staticmethod
    def _toolchain_gate() -> int | None:
        """Node 与 cdk CLI 两个前置：缺 → 打一句话、以退出码 2 结束；齐 → None。

        `deploy` / `bootstrap` / `_run_cdk` 三处共用（每条命令都要过这一关，不靠调用者记得）。**排在动任何
        AWS 读之前**：工具链缺失不花网络、不要凭证——缺工具的人不该先被要求配好 AWS 凭证才看到「你缺工具」。
        """
        for error in (check_node(), check_cdk()):
            if error:
                print(error, file=sys.stderr)
                return EXIT_PRECONDITION
        return None

    def _require_vpc(self, args) -> int | None:
        """凡要合成 app 的动作（deploy / diff / synth / destroy）都必须有 `--vpc`（无隐式默认，ADR 0037 决策 6：
        漏给曾被合成为「新建整套 VPC + 替换 WorkerSg」的变更集）；缺 → 以退出码 2 结束。不用 argparse 的 `required=True`：
        那会把 `--bootstrap`（账户级、不合成 app）也拖进来。

        提示按 ADR 0039 只说三种取值各是什么、为什么不给默认、怎么办；「怎么办」尽量具体——环境已存在且后端记着上次的
        取值时直接报出那个取值（读 SSM 是 best-effort：读不到就不给这半句，不因提示而多一种失败）。"""
        if getattr(args, "vpc", None):
            return None
        print("缺 --vpc：部署要显式选网络——`--vpc default`（用账户的默认 VPC）/ `--vpc new`（新建一套）/ "
              "`--vpc vpc-<id>`（用现有的某个）。不给默认值是有意的：漏选会被当成「新建网络」、悄悄换掉在用的那套。"
              f"{self._stored_vpc_hint(args)}（`--bootstrap` 不需要此项。）", file=sys.stderr)
        return EXIT_PRECONDITION

    def _stored_vpc_hint(self, args) -> str:
        """给缺 `--vpc` 的提示配「怎么办」：环境已存在 → 报后端记录的上次那个取值；无记录 → 说明要给当初那个取值；
        stack 不在 → 首次部署按需选。任何读取失败（凭证 / region / 权限）→ 空串，提示退回通用版。"""
        try:
            target = self._resolve_target(args)
            cfn, ssm = _make_hint_clients(region=target.region, profile=target.profile)
            if not _stack_exists(cfn, names.stack_name(target.prefix)):
                return "首次部署按需选一个。"
            stored = _read_stored_vpc_spec(ssm, target.prefix)
        except Exception:
            return ""
        if stored:
            return f"这个环境上次部署用的是 `--vpc {stored}`，沿用即可。"
        return "这个环境已存在但后端没有网络取值记录，请给当初部署用的那个取值。"

    # ---- context / cdk.json（纯推导，单测直打）----
    def build_context(self, args, *, device_farm_project: str | None) -> dict[str, str]:
        """flag → CDK context（app/stack 侧读的那四个配置项 + 命令派生的版本戳与 Device Farm 项目 ARN）。

        `--vpc` 一个 flag 摊成两个配置项：`default` → `use_default_vpc=true`；`vpc-<id>` → `vpc_id=<id>`；
        `new` → **两个都不给**（stack 的建新分支，见 `stack._network`）。
        `--stop-timeout` 不给则不进 context（让 stack 的默认值说话，不在两处各写一个默认）。

        `device_farm_project` 是调用方已解析好的项目 ARN（deploy 找回或建立，其余动作读 SSM 现值；本方法不做 IO，
        ADR 0037 决策 6）。None 表示本次没有可用的 ARN，此时给「待建立」占位 `names.DEVICE_FARM_PROJECT_PENDING`
        而不省略这个键：stack 对占位与缺省同样处理（不写项目 ARN 参数、不授设备权限），恒给出这个键是为了让 cdk 的
        命令行写明本次的取值，也免得其它来源的同名 context（如用户级 cdk 配置）补进来。ARN 形态由 stack 在合成期校验。
        **关键字必给、没有默认值**：漏传若静默成占位，deploy 就会撤掉已部署的设备授权。
        """
        target = self._resolve_target(args)
        ctx: dict[str, str] = {"prefix": target.prefix, "version": self._resolve_version(args)}
        vpc = getattr(args, "vpc", None)
        if not vpc:  # 调用点已经 _require_vpc 过；这里是契约守卫，不是给部署方看的提示
            raise ValueError("build_context 需要 args.vpc：VPC 取值无隐式默认，调用前先做缺值检查")
        if vpc == "default":
            ctx["use_default_vpc"] = "true"
        elif vpc != "new":
            ctx["vpc_id"] = vpc
        if getattr(args, "stop_timeout", None) is not None:
            ctx["stop_timeout"] = str(args.stop_timeout)
        ctx["device_farm_project"] = device_farm_project or names.DEVICE_FARM_PROJECT_PENDING
        return ctx

    def app_command(self) -> str:
        """生成的 `cdk.json` 里的 `app`：用**当前解释器**运行本包的 CDK app。

        必须是 `sys.executable`、不是裸 `python`——部署方多半用 `uv tool install` 装的隔离环境，PATH 上的
        `python` 未必装了 `gherkai-deploy-aws`（asset 还要从**本 venv** 已安装包复制，见 `stack._build_lambda_asset`）。
        `shlex.quote`：cdk 把 `app` 交给 shell 执行，macOS 上解释器路径常带空格。
        """
        return f"{shlex.quote(sys.executable)} -m gherkai_deploy_aws.app"

    def write_cdk_json(self, work_dir: Path) -> Path:
        """在临时工作目录生成 `cdk.json`（ADR 0037 决策 6）——**不再有入库的 cdk.json**：它曾假定自己躺在
        monorepo 里（`app = "uv run python app.py"`），以 wheel 安装的部署方到不了那里。只写 app + 特性开关；设计参数走 `-c`。"""
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

        **不写进仓库/包目录**：wheel 装的包目录不该被写，且 `.lambda_build` 那种仓库内落点对以 wheel 安装的部署方不存在。
        """
        path = Path(tempfile.mkdtemp(prefix="gherkai-deploy-"))
        try:
            yield path
        finally:
            shutil.rmtree(path, ignore_errors=True)

    def _run_cdk(self, verb: str, args, *, extra=(), output: Path | None = None,
                 device_farm_project=_READ_STORED_PROJECT) -> int:
        """拼 context 与 argv、在一次性工作目录里调 cdk CLI，返回它的退出码。

        `device_farm_project`：只有 deploy 传（已在 cdk 之前找回或建立，None 即本次不启用设备支持）；其余动作不传，
        由本方法在工具链前置与目标解析之后只读 SSM 现值（diff 另用 GetProject 核对，见 `_stored_device_farm_project`），
        读不到或核对失败即以退出码 2 结束。
        """
        blocked = self._toolchain_gate()
        if blocked is not None:
            return blocked
        cdk_argv = cdk_command()

        target = self._resolve_target_or_report(args)
        if target is None:
            return EXIT_PRECONDITION
        if device_farm_project is _READ_STORED_PROJECT:
            blocked, device_farm_project = self._stored_device_farm_project(verb, target)
            if blocked is not None:
                return blocked
        ctx_cache = context_cache_path(target.prefix)
        with self._work_dir() as work_dir:
            self.write_cdk_json(work_dir)
            # **CDK 环境查询缓存（`cdk.context.json`）跨调用持久化**：工作目录是一次性的，若每次都空着进去，cdk 对
            # `from_lookup`（`--vpc default|<id>`）缺失的值会先用占位 VPC/子网**预合成一遍**再去真查——aws-cdk-lib 的
            # 模板校验器对那份占位模板报错、降级成「Template validation found issues」warning 打出来（实际运行抓到、
            # 全新目录 100% 复现、有缓存即消失），而且每次多一轮查询 API。CDK 自己的标准做法就是把该文件保留
            # （它建议入库），这里放在用户缓存目录、按 prefix 一份；`--refresh-context` 丢弃重查（VPC/子网真变了时用）。
            work_ctx = work_dir / "cdk.context.json"
            if getattr(args, "refresh_context", False):
                if ctx_cache.exists():
                    ctx_cache.unlink()
                    print(f"已丢弃 CDK 环境查询缓存 {ctx_cache}，本次重新查询。", file=sys.stderr)
            elif ctx_cache.exists():
                shutil.copyfile(ctx_cache, work_ctx)
            # 部署方给的导出目录钉成**绝对**路径：cdk 子进程 cwd 是本次临时工作目录（用完即删），相对路径
            # 原样传会让导出物落进那里、随目录消失而命令以退出码 0 结束（实际运行踩过）。默认落工作目录、随之清理。
            out_dir = output.resolve() if output is not None else work_dir / "cdk.out"
            argv = [*cdk_argv, verb, "--app", self.app_command(), "--output", str(out_dir)]
            for key, value in self.build_context(args, device_farm_project=device_farm_project).items():
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

    # ---- 内部：VPC 取值三态 ----
    def _guard_vpc_spec(self, args) -> int | None:
        """deploy 前的 VPC 取值比对。放行 → None；拦 → 退出码（2）。

        只在 deploy 前执行（见 `diff`/`destroy` 的 docstring）。解析 prefix/region/profile 失败与读后端失败
        （凭证/权限/网络）都以退出码 2 结束而非抛 traceback：对部署方是「先修凭证」，与 Node 缺失同一类。
        """
        target = self._resolve_target_or_report(args)
        if target is None:
            return EXIT_PRECONDITION
        stack = names.stack_name(target.prefix)
        try:
            cfn = _make_cfn_client(region=target.region, profile=target.profile)
            exists = _stack_exists(cfn, stack)
            stored = None
            if exists:
                ssm = _make_ssm_client(region=target.region, profile=target.profile)
                stored = _read_stored_vpc_spec(ssm, target.prefix)
        except Exception as exc:
            print(f"读不到后端 VPC 取值（stack {stack} / SSM {names.ssm_vpc_path(target.prefix)}）：{exc}\n"
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
                f"stack {stack} 已存在，但 {path} 没有 VPC 取值记录——这个部署早于 VPC 取值登记机制，"
                f"本次 deploy 无从核对 `--vpc {args.vpc}` 是否与当初一致。**这恰是最危险的那一次 deploy**："
                f"取值给错会被当成新建一套网络、把在用的整套换掉。"
            )
        else:
            message = (
                f"`--vpc {args.vpc}` 与后端记录的 VPC 取值 `{stored}` 不一致（{path}）。改这个取值就是 VPC 级资源替换，"
                f"worker 网络会被重建。"
            )
        if allow:
            print(f"警告：{message}\n已带 --allow-vpc-change，放行本次（deploy 成功后，后端会把这次的 `--vpc {args.vpc}` 记下来）。",
                  file=sys.stderr)
            return None
        print(f"{message}\n出路：① 先 `gherkai deploy --diff`（带同一组 flag）核对变更集；"
              f"② 确认无误后带 `--allow-vpc-change` 放行这一次。", file=sys.stderr)
        return EXIT_PRECONDITION

    # ---- 内部：Device Farm 项目（ADR 0051 决策 10「项目」与无权限降级；ADR 0037 决策 6 的 context 闭集）----
    def _resolve_device_farm_project_for_deploy(self, args) -> tuple[int | None, str | None]:
        """deploy 在 cdk 之前找回或建立项目 `{prefix}devices`。返回 (退出码, ARN)：退出码不为 None 即就此结束、不调 cdk；
        否则把 ARN 交给 cdk（None 表示本次不启用设备支持，context 里是「待建立」占位）。

        先读 SSM 现值，再交 `devicefarm.resolve_or_create_project` 核对、按名称找回或建立。分支：
        - 读不到 SSM 记录（无权限、无凭证、网络、限流）→ 退出码 2：不知道记录在不在，就分不清该沿用还是该建立；当作「没有记录」
          继续，遇上无权限降级会撤掉已部署的设备授权。与 VPC 取值比对读后端失败同一处置（见 `_guard_vpc_spec`）；处置半句按错误
          类别给（`_ssm_read_failure_hint`）。记录存在但不是合法的项目 ARN（只会因手工改动出现）同样退出码 2，不当作没有记录。
        - 同名项目不止一个 → 退出码 2，点名命中的 ARN，不替部署方挑选。
        - 部署方没有 Device Farm 权限 → 降级：SSM 有 ARN 且核对被拒就沿用并警告；没有记录，或记录的项目已核对为不存在而找回或新建
          又被拒，就警告并按未启用设备支持部署（不把已不存在的 ARN 写回 SSM、不给不存在的项目授权）。
        - 其余错误（限流、网络、服务端故障）→ 退出码 1，不猜测：当成「没有项目」会多建一个，当成无权限会撤掉设备授权，
          而这只有到设备 run 执行时才会暴露。stack 未改动；CreateProject 若已在服务端生效，重新运行会按名称找回它。
        runtime.devicefarm 在函数内导入：`--help` 不为它拉起 AWS SDK。
        """
        from gherkai_runtime import devicefarm

        target = self._resolve_target_or_report(args)
        if target is None:
            return EXIT_PRECONDITION, None
        path = names.ssm_device_farm_project_path(target.prefix)
        try:
            stored = devicefarm.read_project_arn(
                _make_ssm_client(region=target.region, profile=target.profile), target.prefix)
        except Exception as exc:
            print(f"读不到 Device Farm 项目记录（SSM 参数 {path}）：{exc}\n"
                  f"{_ssm_read_failure_hint(exc)}本次没有改动后端。", file=sys.stderr)
            return EXIT_PRECONDITION, None
        if stored is not None:
            blocked = self._report_malformed_device_farm_record(target, path, stored)
            if blocked is not None:
                return blocked, None

        name = devicefarm.project_name(target.prefix)
        try:
            resolution = devicefarm.resolve_or_create_project(
                target.prefix, profile=target.profile, stored_arn=stored,
                warn=lambda text: print(f"警告：{text}", file=sys.stderr))
        except devicefarm.AmbiguousProject as exc:
            print(f"{exc}\n本次没有改动后端。", file=sys.stderr)
            return EXIT_PRECONDITION, None
        except devicefarm.DeviceFarmAccessDenied as exc:
            print(self._device_farm_denied_warning(exc, stored), file=sys.stderr)
            return None, None if exc.stored_project_missing else stored
        except Exception as exc:
            print(f"没能在 Device Farm 找回或建立项目 {name}：{exc}\n"
                  f"这类错误不按权限不足处理（多为限流、网络或服务端故障），为免误改设备授权，本次没有部署 stack。"
                  f"稍后重新运行 `gherkai deploy` 即可；项目若已建立，会按名称找回、不会重复建立。", file=sys.stderr)
            return EXIT_FAILED, None
        if resolution.source == "created":
            print(f"已在 Device Farm（{names.DEVICE_FARM_REGION}）建立项目 {name}：{resolution.arn}", file=sys.stderr)
        elif resolution.source == "found":
            print(f"沿用 Device Farm 里已有的同名项目 {name}：{resolution.arn}", file=sys.stderr)
        return None, resolution.arn

    @staticmethod
    def _device_farm_denied_warning(exc, stored: str | None) -> str:
        """部署方没有 Device Farm 权限时的警告，按「有没有记录、记录的项目还在不在」分三种说法（ADR 0051 决策 10 的无权限降级）。

        记录的项目已不存在而又无法找回或新建时（`exc.stored_project_missing`），本次按未启用设备支持部署：沿用一个已不存在的
        ARN 只是不撤授权，带设备目标的 run 仍会失败、且推迟到执行时才暴露。项目已不存在由找回或建立时经 warn 回调发出的前一条
        警告说明，这里只说授权撤了、怎么恢复。
        """
        perms = f"{names.DEVICE_FARM_REGION} 上的 devicefarm:GetProject、devicefarm:ListProjects 与 devicefarm:CreateProject"
        if stored is None:
            return (f"警告：{exc}，无法找回或建立 Device Farm 项目。本次部署不启用设备支持，提交带设备目标的云端 run 会被拒绝。\n"
                    f"     要启用，请给部署用的凭证加上 {perms} 权限，再重新运行 `gherkai deploy`。")
        if exc.stored_project_missing:
            return (f"警告：{exc}，无法按名称找回或新建 Device Farm 项目。"
                    f"本次按未启用设备支持部署：后端不再记录项目 {stored}、Midscene worker 的设备授权随之撤掉，提交带设备目标的云端 run 会被拒绝。\n"
                    f"     要恢复，请给部署用的凭证加上 {perms} 权限，再重新运行 `gherkai deploy`。")
        return (f"警告：{exc}，无法核对部署记录的 Device Farm 项目。本次沿用记录里的项目 {stored}，设备支持保持不变。\n"
                f"     要让部署能核对、找回或建立项目，请给部署用的凭证加上 {perms} 权限。")

    def _stored_device_farm_project(self, verb: str, target) -> tuple[int | None, str | None]:
        """diff / --synth-only / destroy 用的项目 ARN：只读 SSM 现值，不找回、不建立（ADR 0051 决策 10、ADR 0037 决策 6）。

        返回 (退出码, ARN)，含义同 `_resolve_device_farm_project_for_deploy`。参数不存在（含 stack 不存在）返回 None，经
        `build_context` 成为「待建立」占位，diff 此时提示用于计算变更集的模板不含设备支持相关授权与项目 ARN 参数、实际部署会多出这两部分。记录存在但
        不是合法的项目 ARN（只会因手工改动出现）以退出码 2 结束并点名 SSM 路径（`_report_malformed_device_farm_record`）。SSM 有
        合法值时，diff 按 deploy 的同一规则用 GetProject 只读核对（`devicefarm.verify_project`）：
        成功即沿用；项目已不存在（被手动删除）时警告并以占位显示，因为用有 Device Farm 权限的凭证 deploy 时会按名称找回或新建、
        换成别的 ARN。
        --synth-only 与 destroy 不核对、直接沿用 SSM 现值。

        读 SSM 失败（无凭证、无权限、网络、限流、取不到 region）以退出码 2 结束、不回落占位：回落会让 diff 把已部署的设备授权
        显示成删除，误导依据它核对变更的人；处置半句按错误类别给（`_ssm_read_failure_hint`）。唯一例外是 --synth-only 在完全没有
        凭证时回落占位并警告，因为无凭证离线导出是既有能力；此时也不建 SSM 句柄（没有 region 时建句柄本身就会失败）。

        GetProject 核对被拒（所用凭证没有 Device Farm 权限）时与 deploy 同一降级：按记录里的项目计算变更集并警告没能核对——允许
        无权限的部署方降级部署，就不能反过来让他不能预览变更集。GetProject 的其他失败（限流、网络、服务端故障）以退出码 2 结束，
        既不回落占位、也不沿用未核对的记录，消息点名 SSM 路径与原异常、不说成缺权限（ADR 0051 决策 10）。
        """
        from gherkai_runtime import devicefarm

        if verb == "synth":
            try:
                has_credentials = _has_aws_credentials(profile=target.profile)
            except Exception:  # profile 名不存在等配置错误不算「没有凭证」，交给下面真去读时报错
                has_credentials = True
            if not has_credentials:
                print("警告：没有可用的 AWS 凭证，读不到已部署后端的 Device Farm 项目记录。导出的模板按未启用设备支持生成，"
                      "不含远程访问会话的授权，可能与已部署的 stack 不一致；需要与已部署一致的模板时，配好凭证后重新导出。",
                      file=sys.stderr)
                return None, None
        path = names.ssm_device_farm_project_path(target.prefix)
        try:
            stored = devicefarm.read_project_arn(
                _make_ssm_client(region=target.region, profile=target.profile), target.prefix)
        except Exception as exc:
            print(f"读不到 Device Farm 项目记录（SSM 参数 {path}）：{exc}\n"
                  f"{_ssm_read_failure_hint(exc)}读不到时不按「未启用设备支持」继续，以免结果与已部署的后端不一致。",
                  file=sys.stderr)
            return EXIT_PRECONDITION, None
        if stored is not None:
            blocked = self._report_malformed_device_farm_record(target, path, stored)
            if blocked is not None:
                return blocked, None
        if verb != "diff":
            return None, stored
        if stored is None:
            print(f"提示：后端没有 Device Farm 项目记录（SSM 参数 {path}），用于计算变更集的模板按未启用设备支持生成、不含设备支持"
                  f"相关的授权与项目 ARN 参数；用有 Device Farm 权限的凭证执行 `gherkai deploy` 时会先按名称 "
                  f"{devicefarm.project_name(target.prefix)} 找回或建立项目，实际变更会比这里多出这两部分。", file=sys.stderr)
            return None, None

        try:
            exists = devicefarm.verify_project(stored, profile=target.profile)
        except devicefarm.DeviceFarmAccessDenied as exc:
            print(f"警告：{exc}，无法核对部署记录的 Device Farm 项目是否还在。变更集按记录里的项目 {stored} 计算，设备支持保持不变；"
                  f"项目若已被手动删除，用有 Device Farm 权限的凭证执行 `gherkai deploy` 时会按名称找回或新建，变更集会与这里显示的不同。\n"
                  f"     要让 `gherkai deploy --diff` 能核对，请给所用凭证加上该项目的 devicefarm:GetProject 权限（Device Farm 位于 "
                  f"{names.DEVICE_FARM_REGION}）。", file=sys.stderr)
            return None, stored
        except Exception as exc:
            print(f"无法核对 Device Farm 项目记录（SSM 参数 {path} 记的是 {stored}），GetProject 调用出错：{exc}\n"
                  f"这类错误多为限流、网络或服务端故障，稍后重试即可。核对不了就无法判断变更集应按记录里的项目还是按尚未建立"
                  f"项目来显示，所以本次不输出变更集。", file=sys.stderr)
            return EXIT_PRECONDITION, None
        if exists:
            return None, stored
        print(f"警告：部署记录的 Device Farm 项目 {stored} 已不存在（可能已被手动删除），用不含设备支持相关授权与项目 ARN 参数的"
              f"模板计算变更集，已部署的模板含这些授权与参数时变更集会显示移除它们；用有 Device Farm 权限的凭证执行 "
              f"`gherkai deploy` 时会按名称 {devicefarm.project_name(target.prefix)} 找回或新建项目。", file=sys.stderr)
        return None, None

    @staticmethod
    def _report_malformed_device_farm_record(target, path: str, stored: str) -> int | None:
        """SSM 记录不是合法的项目 ARN 时报错并返回退出码 2，合法返回 None。

        这种值只会因手工改动出现（stack 只写校验过的值）。不当作「没有记录」继续：那会在无权限降级时撤掉已部署的授权；也不建议
        删除参数：它归 stack 管理，删掉后只要找回的 ARN 与上次相同，CloudFormation 不会重建它；不给写回参数的命令：参数归 stack
        管理，给了等于默许手工写回。stack 合成期的形态校验保留，作接线错误的兜底（ADR 0037 决策 6）。查项目的命令带上本次用的
        profile（与 doctor 的停止命令同一做法），照抄不会落到另一套凭证。
        """
        from gherkai_runtime import devicefarm

        try:
            names.validate_device_farm_project_arn(stored)
        except ValueError as exc:
            profile_flag = f" --profile {shlex.quote(target.profile)}" if target.profile else ""
            print(f"后端记录的 Device Farm 项目 ARN 不合法（SSM 参数 {path}）：{exc}\n"
                  f"这个参数由 `gherkai deploy` 写入，通常是被手工改过。请查到名为 {devicefarm.project_name(target.prefix)} 的项目 ARN：\n"
                  f"  aws devicefarm list-projects --region {names.DEVICE_FARM_REGION}{profile_flag}\n"
                  f"把参数改回这个值后重新执行原命令；本次没有改动后端。", file=sys.stderr)
            return EXIT_PRECONDITION
        return None

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

    def _resolve_target_or_report(self, args):
        """解析链的诊断归口：解析得出 → target；失败 → 打一句诊断、返 None（调用点归退出码）。

        **每个动作在碰 AWS 之前都要经这一口**：不存在的 `--profile` 名在解析链回落读 profile config 的
        `boto3.session.Session(...)` **构造期**就抛 `ProfileNotFound`（回落只在未给 `--region`/`AWS_REGION`
        时发生，故 profile-only 的部署方是唯一撞得到的人——而 profile config 里写着 region 是被支持的形态，
        见 `compose.resolve_region`）。这一层裸着就是裸 botocore 堆栈：实际运行核过 `list-workers` /
        `push-worker` / `deploy` 三条都如此，且这一口**排在 `workers._connect` 之前**，那一层包不到它。
        文案与 `workers._connect` 相同——对部署方是同一件事「先修凭证/region」。
        """
        try:
            return self._resolve_target(args)
        except Exception as exc:
            print(f"连不上 AWS：{exc}\n需要可用的凭证与 region（--region / AWS_REGION / --profile）。",
                  file=sys.stderr)
            return None

    @staticmethod
    def _resolve_version(args) -> str:
        """写进 SSM 版本戳的版本（ADR 0037 决策 6「版本戳」/ 决策 7 版本真源）。

        优先 CLI 前端交进来的 `args.version`（即运行中的 CLI 的版本，决策 7 比对的正是它）；缺则本包自报 dist
        版本——两者被 `==` 同版本 pin 成同一个（决策 2b），此回落不引入第二个真源。都取不到 → fail-fast：
        戳写错比缺失更坏（缺失是「警告不拦」，写错会让所有提交者的 skew 判定失真）。
        """
        explicit = getattr(args, "version", None)
        if explicit:
            return str(explicit)
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as dist_version
        try:
            return dist_version("gherkai-deploy-aws")
        except PackageNotFoundError as exc:  # 从源码直接运行、未装成包
            raise RuntimeError(
                "取不到版本号：本包未以发行包形式安装（源码直接运行）。后端版本戳无隐式默认——"
                "装成包（`uv tool install 'gherkai[deploy-aws]'` 或 workspace `uv sync`）后再部署"
            ) from exc


# ---------------------------------------------------------------------------
# Node / cdk CLI 前置（ADR 0037 决策 6「Node 前置是硬事实」）
# ---------------------------------------------------------------------------

def context_cache_path(prefix: str) -> Path:
    """CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省 `~/.cache`）`/gherkai/cdk-context/<prefix>cdk.context.json`。
    按 prefix 一份（各环境可各自 `--refresh-context`，互不牵连）；不入仓库/包目录（以 wheel 安装的部署方没有可写的源码树）。"""
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


def check_cdk() -> str | None:
    """cdk CLI 前置：PATH 上既无 `cdk` 也无 `npx` → 返回给人看的一句话；能定位 → None。

    与 `check_node()` 写法相同（**不抛 traceback**，ADR 0037 决策 6）。消息在此单点维护——`deploy` / `bootstrap` /
    `_run_cdk` 三处共用（`doctor` 的 detail 是自检清单的另一种措辞，另写）。
    """
    if cdk_command():
        return None
    return f"找不到 cdk 也找不到 npx：cdk CLI 是 npm 物，装 Node（≥ {NODE_MIN_MAJOR}）后重试。"


def check_node() -> str | None:
    """Node 前置：缺失/过低 → 返回给人看的一句话；OK → None。**不抛 traceback**（ADR 0037 决策 6）。

    为何必查：`aws-cdk-lib` 是 jsii 绑定，**app 子进程 import 即起 node**；cdk CLI 本身也是 npm 物。
    缺 node 的原生症状是 jsii 在子进程里抛一段与 Node 无关的堆栈，对部署方是纯噪声。
    """
    node = shutil.which("node")
    if node is None:
        return (
            f"找不到 node：`gherkai deploy` 需要 Node ≥ {NODE_MIN_MAJOR} 在 PATH——CDK 的 Python 绑定是 jsii"
            f"（import 即起 node 子进程），cdk CLI 本身也是 npm 物。装好 Node 后重试。"
        )
    major = _node_major(node)
    if major is not None and major < NODE_MIN_MAJOR:
        # 下限与 worker 镜像的 `engines.node` 同一个（见上 NODE_MIN_MAJOR 的注释）。
        return f"node 版本过低：{node} 是 v{major}，需要 ≥ {NODE_MIN_MAJOR}。"
    return None
