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

## 退出码

`0` 成功；`2` **前置/校验失败**（Node 缺失、VPC 档不符或无记录、读后端失败——用户可修，对齐 CLI 既有
preflight 退 2 的口径）；其余 = cdk CLI 自己的返回码（原样透传，别把 cdk 的失败压成自己的码）。
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

    # ---- 命令面（CLI 皮据它自己的 flag 选调；每个方法自成一次完整调用）----
    def deploy(self, args) -> int:
        """供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。"""
        # 工具链前置先于 VPC 档比对：前者不花网络、不要凭证——缺 Node 的人不该先被要求配好 AWS 凭证
        # 才看到「你缺 Node」。`_run_cdk` 里同样查一次（每条命令都要过这一关，不靠调用者记得）。
        node_error = check_node()
        if node_error:
            print(node_error, file=sys.stderr)
            return EXIT_PRECONDITION
        missing = self._require_vpc(args)
        if missing is not None:
            return missing
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
        with self._work_dir() as work_dir:
            self.write_cdk_json(work_dir)
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
                return subprocess.run(argv, cwd=str(work_dir), env=env).returncode
            except FileNotFoundError as exc:  # cdk/npx 在 which 之后消失（极少见）——别抛 traceback
                print(f"起不动 cdk CLI：{exc}", file=sys.stderr)
                return EXIT_PRECONDITION

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
