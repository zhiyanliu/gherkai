"""`Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。

**全部不碰 AWS、不起 cdk**：boto3 句柄与 `subprocess.run` 都打桩。故这里的证据边界是「拼出来的东西对不对」——
cdk 真跑（synth/deploy）、真 CloudFormation/SSM 的错误码形态，是另一层（真跑 synth 见提交记录；deploy 需真账号）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from gherkai_deploy_aws import cli as provider_cli
from gherkai_deploy_aws import names
from gherkai_deploy_aws.cli import (
    CDK_FEATURE_FLAGS,
    EXIT_PRECONDITION,
    VPC_FIRST_DEPLOY,
    VPC_MATCH,
    VPC_MISMATCH,
    VPC_UNRECORDED,
    Provider,
    classify_vpc_state,
    vpc_spec_matches,
)

VERSION = "1.4.0"


@pytest.fixture(autouse=True)
def _clean_aws_env(monkeypatch):
    """把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。"""
    for var in ("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE", "AWS_RESOURCE_PREFIX",
                names.LAMBDA_ASSET_DIR_ENV):
        monkeypatch.delenv(var, raising=False)


def _parse(*argv: str) -> argparse.Namespace:
    """走**真 parser**、按真实接线顺序拼（皮先声明命令面 flag，provider 再贴自己的旋钮）——不用
    SimpleNamespace 手捏 args，那会让 flag 面与消费侧各自漂移（默认值/dest 名笔误在手捏的 namespace 里测不出来）。"""
    # 皮那半边（cli/gherkai_cli/deploy.py）的中立版先贴、provider 再贴——`conflict_handler="resolve"` 令
    # provider 的声明生效（真实接线顺序，见 cli 模块头「两层声明」）。
    parser = argparse.ArgumentParser(prog="gherkai deploy", conflict_handler="resolve")
    parser.add_argument("--allow-vpc-change", action="store_true")
    parser.add_argument("--require-approval", default=None, metavar="MODE")
    Provider().add_arguments(parser)
    args = parser.parse_args(argv)
    args.version = VERSION  # CLI 皮交进来的版本（接缝契约，见 cli 模块头）
    return args


# ---------------------------------------------------------------- flag 面

def test_vpc_absent_parses_but_every_synthesizing_verb_exits_2(cdk, capsys):
    """`--vpc` 无隐式默认（漏档会合成「新建整套 VPC + 替换 WorkerSg」，ADR 0037 决策 6）——但校验在**运行期**、
    不在 argparse：`--bootstrap` 是账户级动作、不合成 app，不该被拖着要一个无关旋钮。四个合成动词缺档 → 退 2、
    **不调 cdk**。"""
    args = _parse("--prefix", "gherkai-", "--region", "us-east-1")
    assert args.vpc is None
    p = Provider()
    args.synth_only = "out"
    for verb in (p.deploy, p.diff, p.destroy, p.synth_only):
        assert verb(args) == 2, verb.__name__
        assert "--vpc" in capsys.readouterr().err
    assert cdk.calls == []  # 一次都没起 cdk


def test_bootstrap_needs_no_vpc_and_never_loads_the_app(cdk, monkeypatch):
    """bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，
    不会跑 app（真跑核过：带 `--app` 则即使给了显式环境也先跑 app、那就又要 `--vpc`）。"""
    class _Sts:
        class meta:
            region_name = "us-east-1"

        @staticmethod
        def get_caller_identity():
            return {"Account": "123456789012"}

    monkeypatch.setattr(provider_cli, "_make_sts_client", lambda **kw: _Sts())
    rc = Provider().bootstrap(_parse("--prefix", "gherkai-"))
    assert rc == 0
    argv = _argv(cdk)
    assert argv[:3] == ["cdk-stub", "bootstrap", "aws://123456789012/us-east-1"]
    assert "--app" not in argv and "-c" not in argv


def test_bootstrap_without_resolvable_region_exits_2(cdk, monkeypatch, capsys):
    class _Sts:
        class meta:
            region_name = None

        @staticmethod
        def get_caller_identity():
            return {"Account": "123456789012"}

    monkeypatch.setattr(provider_cli, "_make_sts_client", lambda **kw: _Sts())
    assert Provider().bootstrap(_parse("--prefix", "gherkai-")) == 2
    assert "region" in capsys.readouterr().err and cdk.calls == []


@pytest.mark.parametrize("value", ["default", "new", "vpc-0abc123"])
def test_vpc_accepts_three_dossiers(value):
    assert _parse("--vpc", value).vpc == value


@pytest.mark.parametrize("value", ["", "defaults", "sg-123", "vpc", "vpc-", "new:vpc-1"])
def test_vpc_rejects_anything_else(value):
    # 含 `vpc-`（空 id，笔误）与 `new:vpc-1`（后者是 SSM 里的**记账**形态、不是用户可给的档——
    # 给了就该报错、别静默当 new）
    with pytest.raises(SystemExit):
        _parse("--vpc", value)


def test_contributed_flag_surface_is_exactly_the_provider_specific_set():
    """flag 面全集钉死（枚举型护栏）：三个 context 旋钮 flag + AWS 定位二件套 + 两个「皮的中立版的 AWS
    精确化」（见 cli 模块头「两层声明」）+ 查询缓存旋钮 `--refresh-context`，**就这八个**。

    比全集而非「某个 flag 在不在」：少一个 → 用户够不到某个旋钮；多一个 → 越界抢皮的命令面 flag。
    两种都只在接线后才暴露。
    """
    parser = argparse.ArgumentParser()
    Provider().add_arguments(parser)
    options = {opt for action in parser._actions for opt in action.option_strings} - {"-h", "--help"}
    assert options == {"--prefix", "--vpc", "--stop-timeout", "--region", "--profile",
                       "--allow-vpc-change", "--require-approval", "--refresh-context"}


def test_worker_subverb_surface_is_exactly_three_and_only_on_deploy():
    """子动词全集钉死（枚举型护栏）+ **只挂 deploy**。

    挂到 destroy 上不是「多个没用的命令」而是危险：皮的 destroy 分派不看 `_deploy_verb`，
    `gherkai destroy push-worker …` 会解析通过、然后去拆栈（见 `Provider._declares_worker_subverbs`）。
    """
    def _verbs(prog: str) -> set[str] | None:
        parser = argparse.ArgumentParser(prog=prog)
        Provider().add_arguments(parser)
        subs = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
        return set(subs[0].choices) if subs else None

    assert _verbs("gherkai deploy") == {"push-worker", "list-workers", "delete-worker"}
    assert _verbs("gherkai destroy") is None
    assert _verbs("gherkai") is None  # 认不出就不贴（降级安全：子动词只经 deploy 可达）


def test_bare_deploy_still_parses_with_subverbs_present():
    """子动词 subparser **不可 required=True**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样过。"""
    args = _parse("--vpc", "default")
    assert getattr(args, "_deploy_verb", None) is None
    assert args.vpc == "default"


def test_push_worker_subverb_parses_and_binds_the_verb():
    args = _parse("push-worker", "acme-novaact:login", "--engine", "novaact", "--variant", "login",
                  "--set-default")
    assert args._deploy_verb.__func__ is Provider.push_worker
    assert (args.image, args.engine, args.variant, args.set_default) == (
        "acme-novaact:login", "novaact", "login", True)
    assert getattr(args, "container_engine", None) is None  # SUPPRESS 默认：不给则属性缺席，父层的值不被覆写


def test_push_worker_requires_engine_and_variant():
    for argv in (("push-worker", "img"), ("push-worker", "img", "--engine", "novaact"),
                 ("push-worker", "img", "--variant", "v"),
                 ("push-worker", "img", "--engine", "nope", "--variant", "v")):
        with pytest.raises(SystemExit):
            _parse(*argv)


def test_locator_flags_work_on_either_side_of_the_subverb():
    """`--prefix` 在子动词**前**给也必须留住——子 parser 在新 namespace 里解析后整体覆盖回父层，
    普通默认值（None）会把父层已解析的值覆写掉（argparse 的经典坑，故子层用 `SUPPRESS`）。"""
    before = _parse("--prefix", "prod-", "push-worker", "img", "--engine", "novaact", "--variant", "v")
    assert before.prefix == "prod-"
    after = _parse("push-worker", "img", "--engine", "novaact", "--variant", "v", "--prefix", "prod-")
    assert after.prefix == "prod-"
    neither = _parse("list-workers")
    assert neither.prefix is None  # 父层默认仍在（解析链自己兜 AWS_RESOURCE_PREFIX）


def test_list_and_delete_worker_bind_their_verbs():
    assert _parse("list-workers")._deploy_verb.__func__ is Provider.list_workers
    assert _parse("delete-worker")._deploy_verb.__func__ is Provider.delete_worker


def test_delete_worker_is_a_documented_placeholder(capsys):
    """留口子：退 2 并说清「押后的是回收策略」，而不是让人只看到 argparse 的 invalid choice。"""
    rc = Provider().delete_worker(_parse("delete-worker"))
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert "尚未提供" in err and "list-workers" in err


def test_provider_name_is_aws():
    # entry point group `gherkai.deploy` 里的名字（多 provider 时 `--provider aws` 选它）
    assert Provider().name == "aws"


# ---------------------------------------------------------------- context 拼装

def test_context_new_dossier_gives_neither_vpc_knob():
    # `new` = stack 自建 → `vpc_id`/`use_default_vpc` 两个旋钮都不给（stack._network 的建新分支）
    ctx = Provider().build_context(_parse("--vpc", "new"))
    assert ctx == {"prefix": "gherkai-", "version": VERSION}


def test_context_default_dossier_sets_use_default_vpc():
    ctx = Provider().build_context(_parse("--vpc", "default"))
    assert ctx == {"prefix": "gherkai-", "version": VERSION, "use_default_vpc": "true"}


def test_context_explicit_vpc_id():
    ctx = Provider().build_context(_parse("--vpc", "vpc-0abc123"))
    assert ctx == {"prefix": "gherkai-", "version": VERSION, "vpc_id": "vpc-0abc123"}


def test_context_omits_stop_timeout_unless_given():
    # 不给则不进 context——默认值只在 stack 一处（别在命令侧再写一个 120，两处默认必漂）
    assert "stop_timeout" not in Provider().build_context(_parse("--vpc", "new"))
    ctx = Provider().build_context(_parse("--vpc", "new", "--stop-timeout", "90"))
    assert ctx["stop_timeout"] == "90"  # context 值恒是字符串（cdk `-c k=v` 只能是串）


def test_context_prefix_follows_the_runtime_resolution_chain(monkeypatch):
    # prefix 走 compose.resolve_cloud_target 同一条链：flag > AWS_RESOURCE_PREFIX > gherkai-
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "stage-")
    assert Provider().build_context(_parse("--vpc", "new"))["prefix"] == "stage-"
    assert Provider().build_context(_parse("--vpc", "new", "--prefix", "prod-"))["prefix"] == "prod-"


def test_version_falls_back_to_installed_dist_version():
    """CLI 皮没交版本 → 本包自报 dist 版本（`==` lockstep pin 成同一个，不引入第二个真源）。"""
    args = _parse("--vpc", "new")
    del args.version
    assert Provider().build_context(args)["version"]  # 非空即可（dev 版形如 1.3.0.postN.devM+sha.dirty）


# ---------------------------------------------------------------- 生成的 cdk.json

def test_app_command_uses_current_interpreter_and_module():
    cmd = Provider().app_command()
    assert cmd.endswith(" -m gherkai_deploy_aws.app")
    # **当前解释器**：PATH 上的 python 未必装了本包（uv tool 的隔离环境），且 asset 要从本 venv 复制
    assert sys.executable in cmd


def test_generated_cdk_json_carries_app_and_feature_flags_verbatim(tmp_path):
    path = Provider().write_cdk_json(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "cdk.json" and path.parent == tmp_path
    assert data["app"] == Provider().app_command()
    # 特性开关逐字沿用收编前那一组：换一组 = 给已部署 stack 造无意义变更集
    assert data["context"] == CDK_FEATURE_FLAGS
    # 设计旋钮**不进** cdk.json（一律 `-c` 显式传，免被 cdk.json 静默兜住）
    assert not {"prefix", "version", "vpc_id", "use_default_vpc", "stop_timeout"} & set(data["context"])


# ---------------------------------------------------------------- VPC 档三态（纯逻辑）

@pytest.mark.parametrize("stored,requested,expected", [
    ("default", "default", True),
    ("vpc-0abc", "vpc-0abc", True),
    ("new:vpc-0abc", "new", True),          # new 档带出所建 id → 按 new: 前缀匹配
    ("new", "new", True),                   # 兜住「值只写了 new」的历史形态
    ("default", "new", False),
    ("vpc-0abc", "vpc-0def", False),
    ("new:vpc-0abc", "vpc-0abc", False),    # 不对称：stack 拥有 ≠ 复用外部 VPC（切换会删掉那个 VPC）
])
def test_vpc_spec_matches(stored, requested, expected):
    assert vpc_spec_matches(stored, requested) is expected


def test_classify_stack_absent_is_first_deploy_even_without_param():
    # 判序：stack 存在性**先于**参数存在性——否则每个新用户的第一次 deploy 都被当「无记录环境」拦下
    assert classify_vpc_state(stack_exists=False, stored_spec=None, requested="new") == VPC_FIRST_DEPLOY


def test_classify_four_states():
    assert classify_vpc_state(stack_exists=True, stored_spec=None, requested="new") == VPC_UNRECORDED
    assert classify_vpc_state(stack_exists=True, stored_spec="default", requested="default") == VPC_MATCH
    assert classify_vpc_state(stack_exists=True, stored_spec="default", requested="new") == VPC_MISMATCH


# ---------------------------------------------------------------- VPC 档三态（打桩 boto3）

class _ClientError(Exception):
    """botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"An error occurred ({code}): {message}")
        self.response = {"Error": {"Code": code, "Message": message}}


class _Cfn:
    def __init__(self, exists: bool) -> None:
        self._exists = exists

    def describe_stacks(self, StackName):  # noqa: N803（boto3 参数名）
        if self._exists:
            return {"Stacks": [{"StackName": StackName}]}
        raise _ClientError("ValidationError", f"Stack with id {StackName} does not exist")


class _Ssm:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def get_parameter(self, Name):  # noqa: N803
        if self._value is None:
            raise _ClientError("ParameterNotFound", f"Parameter {Name} not found.")
        return {"Parameter": {"Name": Name, "Value": self._value}}


def _stub_backend(monkeypatch, *, stack_exists: bool, stored: str | None) -> None:
    monkeypatch.setattr(provider_cli, "_make_cfn_client", lambda **kw: _Cfn(stack_exists))
    monkeypatch.setattr(provider_cli, "_make_ssm_client", lambda **kw: _Ssm(stored))


def test_guard_first_deploy_proceeds(monkeypatch):
    # ① stack 不存在 = 真首次部署 → 放行
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    assert Provider()._guard_vpc_spec(_parse("--vpc", "new", "--region", "us-east-1")) is None


def test_guard_unrecorded_blocks_and_points_at_diff(monkeypatch, capsys):
    # ② 参数缺失 + stack 已存在 = 本机制之前部署的环境（最危险的那一次）→ 退 2，指路 --diff
    _stub_backend(monkeypatch, stack_exists=True, stored=None)
    rc = Provider()._guard_vpc_spec(_parse("--vpc", "default", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert "--diff" in err and "--allow-vpc-change" in err


def test_guard_unrecorded_allowed_once(monkeypatch, capsys):
    _stub_backend(monkeypatch, stack_exists=True, stored=None)
    args = _parse("--vpc", "default", "--region", "us-east-1", "--allow-vpc-change")
    assert Provider()._guard_vpc_spec(args) is None
    assert "警告" in capsys.readouterr().err  # 放行也要留声（不静默改 VPC 形态）


def test_guard_match_proceeds(monkeypatch):
    # ③ 档一致 → 放行（含 new 档的 new:<id> 前缀匹配）
    _stub_backend(monkeypatch, stack_exists=True, stored="new:vpc-0abc")
    assert Provider()._guard_vpc_spec(_parse("--vpc", "new", "--region", "us-east-1")) is None


def test_guard_mismatch_blocks(monkeypatch, capsys):
    # ③ 档不一致 → 退 2（只强制显式给值挡不住第二次 deploy 敲错档）
    _stub_backend(monkeypatch, stack_exists=True, stored="vpc-0abc123")
    rc = Provider()._guard_vpc_spec(_parse("--vpc", "default", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert "vpc-0abc123" in err and "default" in err  # 两个档都点名，别让人猜


def test_guard_mismatch_allowed(monkeypatch):
    _stub_backend(monkeypatch, stack_exists=True, stored="vpc-0abc123")
    args = _parse("--vpc", "default", "--region", "us-east-1", "--allow-vpc-change")
    assert Provider()._guard_vpc_spec(args) is None


def test_guard_unexpected_read_error_exits_2_not_traceback(monkeypatch, capsys):
    """凭证/权限/网络故障 → 退 2 + 一句话（对用户是「先修凭证」，与 Node 缺失同一档），不抛 traceback。"""
    def boom(**kw):
        raise _ClientError("AccessDenied", "not authorized to perform cloudformation:DescribeStacks")
    monkeypatch.setattr(provider_cli, "_make_cfn_client", lambda **kw: boom())
    rc = Provider()._guard_vpc_spec(_parse("--vpc", "new", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    assert "cloudformation:DescribeStacks" in capsys.readouterr().err


def test_stack_not_found_detection_needs_both_code_and_text():
    """`ValidationError` 也用于别的参数问题——只看错误码会把真正的参数错误当「真首次部署」放行，
    那正是三态要挡的那次危险 deploy。故文案不含 does not exist 时必须照抛。"""
    class _Weird:
        def describe_stacks(self, StackName):  # noqa: N803
            raise _ClientError("ValidationError", "1 validation error detected: value at 'stackName' failed")

    with pytest.raises(_ClientError):
        provider_cli._stack_exists(_Weird(), "BackendStack-gherkai")


# ---------------------------------------------------------------- cdk 调用

class _Recorder:
    """`subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。"""

    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.calls: list[dict] = []
        self.worker_steps: list = []  # `Provider._worker_image_steps` 的调用记录（见 `cdk` 夹具）

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "cwd": kwargs.get("cwd"), "env": kwargs.get("env")})
        return type("R", (), {"returncode": self.returncode})()


class _FakeEngine:
    """容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。"""

    name = "docker"

    def probe(self):
        return None


@pytest.fixture
def cdk(monkeypatch) -> _Recorder:
    """把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。

    **四步必须打桩**：`deploy` 在 cdk 成功后会去连真 SSM/ECR/ECS 并 `docker pull` 基底（ADR 0038）——单测里
    那是「不碰 AWS」这条底线的破口（真跑过一次：测试直奔 NoCredentialsError 且真拉了一次 GHCR 镜像）。
    调用次数记在 `rec.worker_steps` 上，供「cdk 成功才跑四步」那两条断言。
    """
    rec = _Recorder()
    monkeypatch.setattr(provider_cli, "check_node", lambda: None)
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: ["cdk-stub"])
    monkeypatch.setattr(provider_cli.subprocess, "run", rec)
    monkeypatch.setattr(Provider, "_container_engine", staticmethod(lambda args: _FakeEngine()))

    def _steps(self, args, engine=None):
        rec.worker_steps.append(args)
        return 0

    monkeypatch.setattr(Provider, "_worker_image_steps", _steps)
    return rec


def _argv(rec: _Recorder) -> list[str]:
    assert len(rec.calls) == 1, f"应恰调一次 cdk，实际 {len(rec.calls)}"
    return rec.calls[0]["argv"]


def test_diff_invokes_cdk_with_app_output_and_context(cdk):
    rc = Provider().diff(_parse("--vpc", "default", "--region", "us-east-1", "--prefix", "prod-"))
    assert rc == 0
    argv = _argv(cdk)
    assert argv[0] == "cdk-stub" and argv[1] == "diff"
    assert "--app" in argv and argv[argv.index("--app") + 1] == Provider().app_command()
    out = argv[argv.index("--output") + 1]
    assert Path(out).name == "cdk.out"
    # context 逐项经 -c 传（值形态 k=v）
    pairs = {argv[i + 1] for i, a in enumerate(argv) if a == "-c"}
    assert pairs == {"prefix=prod-", f"version={VERSION}", "use_default_vpc=true"}


def test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json(cdk):
    Provider().diff(_parse("--vpc", "new", "--region", "us-east-1"))
    cwd = Path(cdk.calls[0]["cwd"])
    # cdk 在工作目录里跑（生成的 cdk.json 在那儿，特性开关才生效）
    assert cwd.name.startswith("gherkai-deploy-")
    # 用完即删（不留临时目录，也不写仓库）
    assert not cwd.exists()


def test_asset_dir_env_points_into_the_work_dir(cdk):
    Provider().diff(_parse("--vpc", "new", "--region", "us-east-1"))
    call = cdk.calls[0]
    assert call["env"][names.LAMBDA_ASSET_DIR_ENV] == call["cwd"]


def test_region_goes_through_env_and_profile_through_cdk_flag(cdk):
    Provider().diff(_parse("--vpc", "new", "--region", "eu-west-1", "--profile", "acme"))
    call = cdk.calls[0]
    assert call["env"]["AWS_REGION"] == "eu-west-1"       # cdk 无 --region，只能经 env
    assert call["env"]["AWS_DEFAULT_REGION"] == "eu-west-1"
    argv = call["argv"]
    assert argv[argv.index("--profile") + 1] == "acme"    # profile 是 cdk 原生 flag


def test_deploy_passes_require_approval_through(cdk, monkeypatch):
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    Provider().deploy(_parse("--vpc", "new", "--region", "us-east-1", "--require-approval", "never"))
    argv = _argv(cdk)
    assert argv[1] == "deploy"
    assert argv[argv.index("--require-approval") + 1] == "never"


def test_deploy_without_require_approval_leaves_it_to_cdk(cdk, monkeypatch):
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    Provider().deploy(_parse("--vpc", "new", "--region", "us-east-1"))
    assert "--require-approval" not in _argv(cdk)


def test_deploy_blocked_by_vpc_guard_never_invokes_cdk(cdk, monkeypatch, capsys):
    _stub_backend(monkeypatch, stack_exists=True, stored="vpc-0abc")
    rc = Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    assert cdk.calls == [], "被三态拦下时绝不能已经调过 cdk"


def test_deploy_runs_the_worker_image_steps_after_a_successful_cdk(cdk, monkeypatch):
    """cdk 成功 → 接着跑 worker 镜像第 2/3/4 步（第 1 步随 cdk 事务，ADR 0038）。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert len(cdk.worker_steps) == 1


def test_deploy_skips_the_worker_image_steps_when_cdk_fails(cdk, monkeypatch):
    """cdk 失败 → 不碰镜像（stack 没生效，推上去的 revision 会指着不存在的模板）。退码透传 cdk 自己的。"""
    cdk.returncode = 7
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 7
    assert cdk.worker_steps == []


def test_deploy_rejects_an_unimplemented_container_engine_before_touching_the_account(monkeypatch, capsys):
    """`GHERKAI_CONTAINER_ENGINE=podman` → 退 2 且**不调 cdk**：纯参数问题，账户一个字节都不该动
    （区别于「docker 没装」——那只警告，退码归 cdk 之后的四步）。

    位置与 Node 前置同一档（本地、不花网络、不要凭证）——**先于** VPC 档比对：给错引擎名的人不该先被要求
    配好 AWS 凭证才看到「这个引擎本期没实装」（同 `deploy` 里 check_node 先于三态比对的理由）。
    """
    rec = _Recorder()
    monkeypatch.setattr(provider_cli, "check_node", lambda: None)
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: ["cdk-stub"])
    monkeypatch.setattr(provider_cli.subprocess, "run", rec)
    monkeypatch.setenv("GHERKAI_CONTAINER_ENGINE", "podman")
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == EXIT_PRECONDITION
    assert rec.calls == []
    assert "podman" in capsys.readouterr().err


def test_destroy_invokes_cdk_destroy_with_same_context(cdk):
    Provider().destroy(_parse("--vpc", "default", "--region", "us-east-1"))
    argv = _argv(cdk)
    assert argv[1] == "destroy"
    assert "use_default_vpc=true" in {argv[i + 1] for i, a in enumerate(argv) if a == "-c"}


def test_synth_only_pins_a_relative_dir_to_the_callers_cwd(cdk, tmp_path, monkeypatch):
    """用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径
    原样传会让导出物落进那里、随之消失而命令退 0（真跑踩过的假成功；早先的测试用绝对 tmp_path、照不出来）。"""
    monkeypatch.chdir(tmp_path)
    args = _parse("--vpc", "new", "--region", "us-east-1")
    args.synth_only = "exported"  # CLI 皮的 --synth-only DIR（接缝契约），相对用户 cwd
    Provider().synth_only(args)
    argv = _argv(cdk)
    assert argv[1] == "synth"
    out = Path(argv[argv.index("--output") + 1])
    assert out.is_absolute() and out == (tmp_path / "exported").resolve()
    assert out != Path(cdk.calls[0]["cwd"]) / "exported"  # 不是工作目录下的那个


def test_synth_only_without_dir_is_a_contract_error(cdk):
    with pytest.raises(ValueError, match="synth_only"):
        Provider().synth_only(_parse("--vpc", "new", "--region", "us-east-1"))


def test_cdk_returncode_is_passed_through(monkeypatch):
    rec = _Recorder(returncode=7)
    monkeypatch.setattr(provider_cli, "check_node", lambda: None)
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: ["cdk-stub"])
    monkeypatch.setattr(provider_cli.subprocess, "run", rec)
    # cdk 自己的失败码原样透传（别压成自己的 1/2——排障要能分辨是谁失败）
    assert Provider().diff(_parse("--vpc", "new", "--region", "us-east-1")) == 7


# ---------------------------------------------------------------- Node / cdk CLI 前置

def test_missing_node_reports_cleanly_and_skips_cdk(monkeypatch, capsys):
    monkeypatch.setattr(provider_cli.shutil, "which", lambda name: None)
    ran = _Recorder()
    monkeypatch.setattr(provider_cli.subprocess, "run", ran)
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    rc = Provider().deploy(_parse("--vpc", "new", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert "node" in err and "22" in err  # 点名 Node 与下限，不是一段 jsii 堆栈
    assert ran.calls == []


def test_node_too_old_is_rejected(monkeypatch, capsys):
    monkeypatch.setattr(provider_cli.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(provider_cli, "_node_major", lambda node: 18)
    assert "过低" in (provider_cli.check_node() or "")


def test_unparseable_node_version_does_not_block(monkeypatch):
    # 版本探测失败不该挡住部署（探测是善意提示、不是闸门）
    monkeypatch.setattr(provider_cli.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(provider_cli, "_node_major", lambda node: None)
    assert provider_cli.check_node() is None


def test_cdk_command_prefers_path_cdk_then_npx(monkeypatch):
    monkeypatch.setattr(provider_cli.shutil, "which", lambda name: "/opt/bin/cdk" if name == "cdk" else None)
    assert provider_cli.cdk_command() == ["/opt/bin/cdk"]
    monkeypatch.setattr(provider_cli.shutil, "which", lambda name: "/opt/bin/npx" if name == "npx" else None)
    assert provider_cli.cdk_command() == ["/opt/bin/npx", "-y", "aws-cdk@2"]
    monkeypatch.setattr(provider_cli.shutil, "which", lambda name: None)
    assert provider_cli.cdk_command() == []


# ---------------------------------------------------------------- 接缝：CLI 不该付 aws_cdk 的代价

def test_provider_module_does_not_import_aws_cdk():
    """CLI 经 entry point import 本模块拿 `Provider`；`aws_cdk` 是 jsii 绑定、**import 即起 node 子进程**
    （ADR 0037 决策 6）。故本模块（及其 import 闭环里 CLI 会走到的部分）不得把 aws_cdk 拉进来——
    否则 `gherkai deploy --help` 也要付一次 node 启动。"""
    import subprocess as sp

    code = (
        "import sys;"
        "import gherkai_deploy_aws.cli as m;"
        "m.Provider();"
        "print(any(k == 'aws_cdk' or k.startswith('aws_cdk.') for k in sys.modules))"
    )
    out = sp.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False", f"cli 模块把 aws_cdk 拉进来了：{out.stdout}"


def test_tolerates_a_shell_that_declares_neither_command_face_flag(monkeypatch, capsys):
    """别的皮（或编程式调用）没给 `--allow-vpc-change` 时**fail-closed**：档不符照拦、不因缺 flag 就放行。"""
    parser = argparse.ArgumentParser(prog="other-shell")
    Provider().add_arguments(parser)
    args = parser.parse_args(["--vpc", "default", "--region", "us-east-1"])
    args.version = VERSION
    del args.allow_vpc_change, args.require_approval  # 模拟「皮压根没这两个 flag」
    _stub_backend(monkeypatch, stack_exists=True, stored="vpc-0abc")
    assert Provider()._guard_vpc_spec(args) == EXIT_PRECONDITION


# ---------------------------------------------------------------- CDK 环境查询缓存（cdk.context.json 跨调用持久化）

class _CdkWritingContext(_Recorder):
    """`subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进 cwd 时那文件是否已在。"""

    def __init__(self, content: str = '{"vpc-provider:account=1:region=us-east-1": {"vpcId": "vpc-cached"}}') -> None:
        super().__init__()
        self.content = content
        self.seeded_with: list = []

    def __call__(self, argv, **kwargs):
        cwd = Path(kwargs["cwd"])
        existing = cwd / "cdk.context.json"
        self.seeded_with.append(existing.read_text() if existing.exists() else None)
        existing.write_text(self.content)
        return super().__call__(argv, **kwargs)


def _cache_env(monkeypatch, tmp_path) -> Path:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(provider_cli, "check_node", lambda: None)
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: ["cdk-stub"])
    return provider_cli.context_cache_path("gherkai-")


def test_context_cache_is_saved_after_the_run_and_seeded_into_the_next_fresh_work_dir(monkeypatch, tmp_path):
    """工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、
    多一轮查询）。缓存按 prefix 持久化在用户缓存目录：第一次跑完存回；第二次进全新工作目录前先放进去。"""
    cache = _cache_env(monkeypatch, tmp_path)
    rec = _CdkWritingContext()
    monkeypatch.setattr(provider_cli.subprocess, "run", rec)
    assert not cache.exists()
    assert Provider().diff(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert rec.seeded_with == [None]                      # 首次：无缓存可放
    assert cache.exists() and "vpc-cached" in cache.read_text()  # 跑完存回
    assert Provider().diff(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert rec.seeded_with[1] == rec.content              # 第二次：全新工作目录里已被放进缓存


def test_context_cache_survives_a_failed_cdk_run(monkeypatch, tmp_path):
    """cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。"""
    cache = _cache_env(monkeypatch, tmp_path)
    rec = _CdkWritingContext(); rec.returncode = 1
    monkeypatch.setattr(provider_cli.subprocess, "run", rec)
    assert Provider().diff(_parse("--vpc", "default", "--region", "us-east-1")) == 1
    assert cache.exists()


def test_refresh_context_discards_the_cache_before_running(monkeypatch, tmp_path, capsys):
    cache = _cache_env(monkeypatch, tmp_path)
    cache.parent.mkdir(parents=True)
    cache.write_text("stale")
    rec = _CdkWritingContext()
    monkeypatch.setattr(provider_cli.subprocess, "run", rec)
    assert Provider().diff(_parse("--vpc", "default", "--region", "us-east-1", "--refresh-context")) == 0
    assert rec.seeded_with == [None]                      # 旧缓存没被放进工作目录
    assert cache.read_text() == rec.content               # 新查到的存回
    assert "丢弃" in capsys.readouterr().err


def test_context_cache_is_per_prefix(monkeypatch, tmp_path):
    _cache_env(monkeypatch, tmp_path)
    assert provider_cli.context_cache_path("a-") != provider_cli.context_cache_path("b-")
    assert provider_cli.context_cache_path("a-").name == "a-cdk.context.json"


# ---------------------------------------------------------------- destroy --yes（非交互销毁）

def _parse_destroy(*argv: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="gherkai destroy", conflict_handler="resolve")
    parser.add_argument("--allow-vpc-change", action="store_true")
    parser.add_argument("--require-approval", default=None, metavar="MODE")
    Provider().add_arguments(parser)
    args = parser.parse_args(argv)
    args.version = VERSION
    return args


def test_destroy_yes_passes_force_to_cdk_and_is_off_by_default(cdk):
    """cdk destroy 在非 TTY 下拒绝无确认的销毁（真跑撞到）；`--yes` = `--force`，不给则让 cdk 自己问。"""
    Provider().destroy(_parse_destroy("--vpc", "default", "--region", "us-east-1"))
    assert "--force" not in _argv(cdk)
    cdk.calls.clear()
    Provider().destroy(_parse_destroy("--vpc", "default", "--region", "us-east-1", "--yes"))
    argv = _argv(cdk)
    assert argv[1] == "destroy" and "--force" in argv


def test_yes_is_destroy_only():
    deploy = argparse.ArgumentParser(prog="gherkai deploy", conflict_handler="resolve")
    Provider().add_arguments(deploy)
    assert "--yes" not in {o for a in deploy._actions for o in a.option_strings}


class _AbsentEngine:
    """容器引擎替身：`probe()` 说「docker 没装」。"""

    name = "docker"

    def probe(self):
        return "docker 未安装或 daemon 未起"


def test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions(cdk, monkeypatch, capsys):
    """容器引擎缺失的前置警告只对**纯发行版**成立：dev/post/本地段版本的 worker 镜像步骤本就走不到「同步基底」
    （ADR 0038 定位链第四级门槛 = is_pure_release），那时警告「之后的镜像步骤会失败」是假警报。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    monkeypatch.setattr(Provider, "_container_engine", staticmethod(lambda args: _AbsentEngine()))

    monkeypatch.setattr(Provider, "_resolve_version", staticmethod(lambda args: "1.4.0"))
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert "docker 未安装" in capsys.readouterr().err

    monkeypatch.setattr(Provider, "_resolve_version", staticmethod(lambda args: "1.4.0.dev3+g0123abc"))
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert "docker 未安装" not in capsys.readouterr().err


def test_provider_doctor_reports_toolchain(monkeypatch):
    """`gherkai doctor` 的 provider 段（ADR 0041 决策四）：node / cdk 必需，容器引擎可选；全部只读、不碰 AWS。"""
    from types import SimpleNamespace

    from gherkai_deploy_aws import container as container_mod

    class _Engine:
        name = "docker"
        def probe(self):
            return None

    monkeypatch.setattr(provider_cli, "check_node", lambda: None)
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: ["cdk-stub"])
    monkeypatch.setattr(container_mod, "resolve_container_engine", lambda requested=None: _Engine())
    checks = {c["name"]: c for c in Provider().doctor(SimpleNamespace())}
    assert checks["node"]["ok"] and checks["node"]["required"]
    assert checks["cdk"]["ok"] and checks["cdk"]["detail"] == "cdk-stub"
    assert checks["container-engine"]["ok"] and checks["container-engine"]["required"] is False

    monkeypatch.setattr(provider_cli, "check_node", lambda: "找不到 node：需要 Node ≥ 22")
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: [])
    checks = {c["name"]: c for c in Provider().doctor(SimpleNamespace())}
    assert not checks["node"]["ok"] and not checks["cdk"]["ok"] and "npx" in checks["cdk"]["detail"]
