"""`Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装（含闭集护栏）、生成的 cdk.json、cdk 调用、VPC 取值三态，
以及 Device Farm 项目在 cdk 之前的找回或建立与只读取值（ADR 0051 决策 10）。

**全部不碰 AWS、不起 cdk**：boto3 句柄、`gherkai_runtime.devicefarm` 的三个入口与 `subprocess.run` 都打桩（Device Farm 那一层
由 autouse 夹具 `df` 默认打桩，漏桩的用例会在构造 Device Farm 客户端时失败，而不是直连真账户）。故这里的证据边界是「拼出来的
东西对不对、编排的先后与分支对不对」——cdk 实际运行（synth/deploy）、真 CloudFormation/SSM/Device Farm 的错误码形态，是另一层
（实际运行 synth 见提交记录；deploy 与部署方无 Device Farm 权限时的真实错误码需真账号）。
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

import pytest
from gherkai_runtime import devicefarm

from gherkai_deploy_aws import cli as provider_cli
from gherkai_deploy_aws import names
from gherkai_deploy_aws.cli import (
    CDK_FEATURE_FLAGS,
    EXIT_FAILED,
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
STORED_ARN = "arn:aws:devicefarm:us-west-2:111122223333:project:stored-0001"     # SSM 里记着的项目
CREATED_ARN = "arn:aws:devicefarm:us-west-2:111122223333:project:created-0002"   # 找回或建立得到的项目
PENDING = names.DEVICE_FARM_PROJECT_PENDING
# 夹具替换之前的真实现：只有专门验它的那条用例调用（见 test_has_aws_credentials_follows_the_credential_chain）
_REAL_HAS_AWS_CREDENTIALS = provider_cli._has_aws_credentials


@pytest.fixture(autouse=True)
def _clean_aws_env(monkeypatch):
    """把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。"""
    for var in ("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE", "AWS_RESOURCE_PREFIX",
                names.LAMBDA_ASSET_DIR_ENV):
        monkeypatch.delenv(var, raising=False)


class _DeviceFarmStub:
    """`gherkai_runtime.devicefarm` 三个入口的替身，并记下调用。默认：SSM 无记录、diff 核对时记录的项目存在、找回或建立的
    结果是新建了 CREATED_ARN、凭证链解析得出凭证。用例改属性即可换分支：`stored` / `read_error` 管读 SSM，
    `project_exists` / `verify_error` 管 diff 的只读核对，`resolution` / `resolve_error` 管找回或建立。"""

    def __init__(self) -> None:
        self.stored: str | None = None
        self.read_error: Exception | None = None
        self.resolution = devicefarm.ProjectResolution(arn=CREATED_ARN, source="created")
        self.resolve_error: Exception | None = None
        self.warn_text: str | None = None     # 给了就在找回或建立前经 warn 回调发出（模拟 SSM 记录的项目已不存在）
        self.project_exists = True
        self.verify_error: Exception | None = None
        self.has_credentials = True
        self.reads: list[str] = []        # 每次读 SSM 项目记录时的 prefix
        self.verifies: list[dict] = []    # 每次只读核对项目的入参
        self.resolves: list[dict] = []    # 每次找回或建立的入参
        self.events: list[str] | None = None  # 给了列表就按调用先后记 "devicefarm"（编排顺序用例用）

    def read_project_arn(self, ssm, prefix):
        self.reads.append(prefix)
        if self.read_error is not None:
            raise self.read_error
        return self.stored

    def verify_project(self, arn, *, profile):
        self.verifies.append({"arn": arn, "profile": profile})
        if self.verify_error is not None:
            raise self.verify_error
        return self.project_exists

    def resolve_or_create_project(self, prefix, *, profile, stored_arn, warn=None):
        self.resolves.append({"prefix": prefix, "profile": profile, "stored_arn": stored_arn})
        if self.events is not None:
            self.events.append("devicefarm")
        if self.warn_text is not None and warn is not None:
            warn(self.warn_text)
        if self.resolve_error is not None:
            raise self.resolve_error
        return self.resolution


@pytest.fixture(autouse=True)
def df(monkeypatch) -> _DeviceFarmStub:
    """Device Farm 与项目记录读取一律打桩（autouse：现有 cdk 用例不经此就会直连真 SSM 与 Device Farm，仓库踩过一次同类坑）。

    另把 Device Farm 客户端的构造点换成直接失败：任何漏桩的调用都会在这里失败并暴露出来，而不是悄悄连到真账户。SSM 句柄默认换成
    「参数不存在」的替身；`_stub_backend` 与个别用例会再覆盖它。
    """
    stub = _DeviceFarmStub()
    monkeypatch.setattr(devicefarm, "read_project_arn", stub.read_project_arn)
    monkeypatch.setattr(devicefarm, "verify_project", stub.verify_project)
    monkeypatch.setattr(devicefarm, "resolve_or_create_project", stub.resolve_or_create_project)

    def _no_client(**kw):
        pytest.fail("单测不该构造 Device Farm 客户端")  # pytest.fail 抛的是 BaseException，provider 的宽 except 接不住

    monkeypatch.setattr(devicefarm, "_make_devicefarm_client", _no_client)
    monkeypatch.setattr(provider_cli, "_has_aws_credentials", lambda **kw: stub.has_credentials)
    monkeypatch.setattr(provider_cli, "_make_ssm_client", lambda **kw: _Ssm(None))
    return stub


def _context_pairs(argv: list[str]) -> dict[str, str]:
    """cdk argv 里经 `-c k=v` 传的 context。"""
    return dict(argv[i + 1].split("=", 1) for i, a in enumerate(argv) if a == "-c")


def _parse(*argv: str) -> argparse.Namespace:
    """走**真 parser**、按真实接线顺序拼（前端先声明命令面 flag，provider 再贴自己的选项）——不用
    SimpleNamespace 手捏 args，那会让 flag 面与消费侧各自漂移（默认值/dest 名笔误在手捏的 namespace 里测不出来）。"""
    # 前端那半边（cli/gherkai_cli/deploy.py）的中立版先贴、provider 再贴——`conflict_handler="resolve"` 令
    # provider 的声明生效（真实接线顺序，见 cli 模块头「两层声明」）。
    parser = argparse.ArgumentParser(prog="gherkai deploy", conflict_handler="resolve")
    parser.add_argument("--allow-vpc-change", action="store_true")
    parser.add_argument("--require-approval", default=None, metavar="MODE")
    Provider().add_arguments(parser)
    args = parser.parse_args(argv)
    args.version = VERSION  # CLI 前端交进来的版本（接缝契约，见 cli 模块头）
    return args


# ---------------------------------------------------------------- flag 面

def test_vpc_absent_parses_but_every_synthesizing_verb_exits_2(cdk, df, monkeypatch, capsys):
    """`--vpc` 无隐式默认（ADR 0037 决策 6：漏给曾被合成为新建整套 VPC 的变更集）——但校验在**运行期**、
    不在 argparse：`--bootstrap` 是账户级动作、不合成 app，不该被拖着要一个无关选项。四个合成动词缺 `--vpc` → 以退出码 2 结束、
    **不调 cdk**，也不读项目记录、不碰 Device Farm。"""
    args = _parse("--prefix", "gherkai-", "--region", "us-east-1")
    assert args.vpc is None
    _stub_backend(monkeypatch, stack_exists=False, stored=None)  # 提示里的「怎么办」半句要读后端；这里钉首次部署那一格
    p = Provider()
    args.synth_only = "out"
    for verb in (p.deploy, p.diff, p.destroy, p.synth_only):
        assert verb(args) == 2, verb.__name__
        err = capsys.readouterr().err
        assert "--vpc default" in err and "--vpc new" in err and "vpc-<id>" in err  # 三种取值各是什么
        assert "首次部署" in err
        assert "WorkerSg" not in err and "变更集" not in err  # 产品面不带 construct 名与 cdk 行话（ADR 0039）
    assert cdk.calls == []  # 一次都没起 cdk
    assert df.reads == [] and df.resolves == []


def test_vpc_absent_hint_names_the_recorded_tier_for_an_existing_environment(cdk, monkeypatch, capsys):
    """环境已存在且后端记着上次的取值 → 提示直接报出那个取值（用户最需要的那句），仍以退出码 2 结束、不起 cdk。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    assert Provider().deploy(_parse("--prefix", "vfy-", "--region", "us-east-1")) == 2
    err = capsys.readouterr().err
    assert "上次部署用的是 `--vpc default`" in err and cdk.calls == []


def test_vpc_absent_hint_for_existing_environment_without_record(cdk, monkeypatch, capsys):
    """环境已存在但没有取值记录（早于登记机制的部署）→ 说明要给当初那个取值，不臆造。"""
    _stub_backend(monkeypatch, stack_exists=True, stored=None)
    assert Provider().deploy(_parse("--prefix", "vfy-", "--region", "us-east-1")) == 2
    err = capsys.readouterr().err
    assert "没有网络取值记录" in err and "上次部署用的是" not in err


def test_vpc_absent_hint_is_best_effort_when_backend_unreadable(cdk, monkeypatch, capsys):
    """读后端失败（凭证 / 权限）→ 提示退回通用版：仍以退出码 2 结束、不抛栈、不多一种失败。"""
    def boom(**kw):
        raise RuntimeError("no credentials")
    monkeypatch.setattr(provider_cli, "_make_hint_clients", boom)
    assert Provider().deploy(_parse("--prefix", "vfy-", "--region", "us-east-1")) == 2
    err = capsys.readouterr().err
    assert "缺 --vpc" in err and "上次部署用的是" not in err and "首次部署" not in err and "Traceback" not in err


def test_hint_clients_carry_a_bounded_timeout_budget():
    """提示专用句柄的超时预算要钉住取值：打桩 `_make_hint_clients` 的用例把它整体换掉，超时值被改大或
    重试配置被摘掉都照不出来。

    这里不打桩、真建两个 boto3 句柄——建句柄不发请求、也不要凭证，只要显式 region。
    重试按总尝试次数断：botocore 解析后落在 `total_max_attempts`，原始配置里的 `max_attempts` 是
    legacy 语义的重试次数（总尝试等于重试次数加一），两种形状折算成同一个数再比。
    """
    clients = provider_cli._make_hint_clients(region="us-east-1", profile=None)
    assert len(clients) == 2
    for client in clients:
        config = client.meta.config
        assert (config.connect_timeout, config.read_timeout) == (2, 3)
        retries = config.retries
        total_attempts = retries.get("total_max_attempts", retries.get("max_attempts", 0) + 1)
        assert total_attempts == 1, retries  # 连不上即放弃：一次尝试，不重试


def test_bootstrap_needs_no_vpc_and_never_loads_the_app(cdk, df, monkeypatch):
    """bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，
    不会执行 app（实际运行核过：带 `--app` 则即使给了显式环境也先执行 app、那就又要 `--vpc`）。不合成 app 也就不需要
    Device Farm 项目：不读项目记录。"""
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
    assert df.reads == [] and df.resolves == []


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
    # 含 `vpc-`（空 id，笔误）与 `new:vpc-1`（后者是 SSM 里的**记账**形态、不是用户可给的取值——
    # 给了就该报错、别静默当 new）
    with pytest.raises(SystemExit):
        _parse("--vpc", value)


def test_contributed_flag_surface_is_exactly_the_provider_specific_set():
    """flag 面全集锁定（枚举型护栏）：三个 context 配置项 flag + AWS 定位二件套 + 两个「前端的中立版的 AWS
    精确化」（见 cli 模块头「两层声明」）+ 查询缓存选项 `--refresh-context`，**就这八个**。

    比全集而非「某个 flag 在不在」：少一个 → 用户够不到某个选项；多一个 → 越界抢走前端的命令面 flag。
    两种都只在接线后才暴露。
    """
    parser = argparse.ArgumentParser()
    Provider().add_arguments(parser)
    options = {opt for action in parser._actions for opt in action.option_strings} - {"-h", "--help"}
    assert options == {"--prefix", "--vpc", "--stop-timeout", "--region", "--profile",
                       "--allow-vpc-change", "--require-approval", "--refresh-context"}


def test_the_two_action_knobs_are_only_on_deploy():
    """`--allow-vpc-change` / `--require-approval` **只贴 deploy**（枚举型全集比对，同上条口径）。

    destroy 两个都不消费：它不做 VPC 取值三态比对，`cdk destroy` 也没有 `--require-approval`——贴上去就是
    `--help` 里两个恒无效的选项，且措辞讲的是 deploy 的变更集。前端的中立版同样只在 deploy 上（见 cli 模块头
    「两层声明」），故 destroy 上这两个 flag 只可能来自本 provider。
    """
    def _flags(prog: str) -> set[str]:
        parser = argparse.ArgumentParser(prog=prog, conflict_handler="resolve")
        Provider().add_arguments(parser)
        return {opt for action in parser._actions for opt in action.option_strings} - {"-h", "--help"}

    shared = {"--prefix", "--vpc", "--stop-timeout", "--region", "--profile", "--refresh-context"}
    # deploy 还多一个 `--container-engine`（第 2 步同步基础镜像要用它）、destroy 多一个 `--yes`——两者各自的专属项
    assert _flags("gherkai deploy") == shared | {"--allow-vpc-change", "--require-approval", "--container-engine"}
    assert _flags("gherkai destroy") == shared | {"--yes"}
    # 行为变化：destroy 上给这两个从「静默忽略」变成 argparse 报错（退出码 2，与 preflight 一致）
    destroy = argparse.ArgumentParser(prog="gherkai destroy", conflict_handler="resolve")
    Provider().add_arguments(destroy)
    for argv in (["--vpc", "default", "--require-approval", "never"],
                 ["--vpc", "default", "--allow-vpc-change"]):
        with pytest.raises(SystemExit):
            destroy.parse_args(argv)


def test_worker_subverb_surface_is_exactly_three_and_only_on_deploy():
    """子动词全集锁定（枚举型护栏）+ **只挂 deploy**。

    挂到 destroy 上不是「多个没用的命令」而是危险：前端的 destroy 分派不看 `_deploy_verb`，
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
    """留口子：以退出码 2 结束并说清「押后的是回收策略」，而不是让人只看到 argparse 的 invalid choice。"""
    rc = Provider().delete_worker(_parse("delete-worker"))
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert "尚未提供" in err and "list-workers" in err


def test_provider_name_is_aws():
    # entry point group `gherkai.deploy` 里的名字（多 provider 时 `--provider aws` 选它）
    assert Provider().name == "aws"


# ---------------------------------------------------------------- context 拼装

def _ctx(*argv: str, project: str | None = None) -> dict[str, str]:
    return Provider().build_context(_parse(*argv), device_farm_project=project)


def test_context_new_dossier_gives_neither_vpc_knob():
    # `new` 表示 stack 自建 → `vpc_id`/`use_default_vpc` 两个配置项都不给（stack._network 的建新分支）
    assert _ctx("--vpc", "new") == {"prefix": "gherkai-", "version": VERSION, "device_farm_project": PENDING}


def test_context_default_dossier_sets_use_default_vpc():
    assert _ctx("--vpc", "default") == {"prefix": "gherkai-", "version": VERSION, "use_default_vpc": "true",
                                        "device_farm_project": PENDING}


def test_context_explicit_vpc_id():
    assert _ctx("--vpc", "vpc-0abc123") == {"prefix": "gherkai-", "version": VERSION, "vpc_id": "vpc-0abc123",
                                            "device_farm_project": PENDING}


def test_context_omits_stop_timeout_unless_given():
    # 不给则不进 context——默认值只在 stack 一处（别在命令侧再写一个 120，两处默认必漂）
    assert "stop_timeout" not in _ctx("--vpc", "new")
    assert _ctx("--vpc", "new", "--stop-timeout", "90")["stop_timeout"] == "90"  # context 值恒是字符串（cdk `-c k=v` 只能是串）


def test_context_prefix_follows_the_runtime_resolution_chain(monkeypatch):
    # prefix 走 compose.resolve_cloud_target 同一条链：flag > AWS_RESOURCE_PREFIX > gherkai-
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "stage-")
    assert _ctx("--vpc", "new")["prefix"] == "stage-"
    assert _ctx("--vpc", "new", "--prefix", "prod-")["prefix"] == "prod-"


def test_version_falls_back_to_installed_dist_version():
    """CLI 前端没交版本 → 本包自报 dist 版本（`==` 同版本 pin 成同一个，不引入第二个真源）。"""
    args = _parse("--vpc", "new")
    del args.version
    assert Provider().build_context(args, device_farm_project=None)["version"]  # 非空即可（dev 版形如 1.3.0.postN.devM+sha.dirty）


def test_context_carries_the_resolved_project_arn_verbatim_and_pending_otherwise():
    """项目 ARN 由调用方解析好传入、原样进 context；没有可用的 ARN（None）时恒给「待建立」占位、不省略这个键：
    cdk 的命令行因此写明本次的取值，其它来源的同名 context 也补不进来。stack 对占位与缺省同样处理（不写参数、不授权）。"""
    assert _ctx("--vpc", "new", project=STORED_ARN)["device_farm_project"] == STORED_ARN
    assert _ctx("--vpc", "new", project=None)["device_farm_project"] == PENDING


def test_build_context_requires_the_project_to_be_decided_by_the_caller():
    """`device_farm_project` 是必给的关键字、没有默认值：漏传若静默成占位，deploy 就会撤掉已部署的设备授权。"""
    with pytest.raises(TypeError):
        Provider().build_context(_parse("--vpc", "new"))


def test_build_context_does_no_io(df, monkeypatch):
    """build_context 是纯推导（ADR 0037 决策 6）：不读 SSM、不碰 Device Farm，找回或建立归 deploy、读现值归 `_run_cdk`。"""
    def _forbidden(**kw):
        raise AssertionError("build_context 不该建 AWS 句柄")

    monkeypatch.setattr(provider_cli, "_make_ssm_client", _forbidden)
    monkeypatch.setattr(provider_cli, "_has_aws_credentials", _forbidden)
    _ctx("--vpc", "default", project=STORED_ARN)
    assert df.reads == [] and df.resolves == []


# ADR 0037 决策 6 的 context 闭集：三个 flag 派生的四个配置项，加命令自派生的 version 与 device_farm_project
CONTEXT_CLOSED_SET = {"prefix", "version", "vpc_id", "use_default_vpc", "stop_timeout", "device_farm_project"}


def _app_context_keys() -> set[str]:
    """stack.py 与 app.py 源码里读的全部 context 键（`try_get_context` / `get_context` 的字面量实参）。"""
    pkg = Path(provider_cli.__file__).parent
    keys: set[str] = set()
    for name in ("stack.py", "app.py"):
        tree = ast.parse((pkg / name).read_text(encoding="utf-8"), filename=name)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("try_get_context", "get_context")):
                arg = node.args[0] if node.args else None
                assert isinstance(arg, ast.Constant) and isinstance(arg.value, str), (
                    f"{name}:{node.lineno} 读 context 须用字面量键，否则本护栏无从核对闭集")
                keys.add(arg.value)
    return keys


def _all_option_dests(parser: argparse.ArgumentParser) -> tuple[set[str], set[str]]:
    """parser 及其子 parser 上全部选项字符串与 dest。"""
    options: set[str] = set()
    dests: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for sub in action.choices.values():
                o, d = _all_option_dests(sub)
                options |= o
                dests |= d
            continue
        options |= set(action.option_strings)
        dests.add(action.dest)
    return options, dests


def test_context_closed_set_matches_what_the_app_reads():
    """差集护栏：build_context 可能产出的键集合、stack 与 app 实际读的键集合、ADR 定的闭集，三者相等。

    命令多拼一个 app 不读的键是死配置；app 多读一个命令不拼的键，就只能从 cdk.json 或用户级配置这类隐式来源补进来——
    两种漂移都只在接线后才暴露。键集合按各条分支的并集取：三种 VPC 取值、给与不给 `--stop-timeout`、有与没有项目 ARN。
    """
    produced: set[str] = set()
    for argv in (("--vpc", "new"), ("--vpc", "default"), ("--vpc", "vpc-0abc123"), ("--vpc", "new", "--stop-timeout", "90")):
        for project in (None, STORED_ARN):
            produced |= set(_ctx(*argv, project=project))
    assert produced == CONTEXT_CLOSED_SET
    assert _app_context_keys() == CONTEXT_CLOSED_SET


def test_command_derived_context_keys_have_no_flag():
    """`version` 与 `device_farm_project` 由命令派生、有意不给 flag（ADR 0037 决策 6）：手填只会多出写错的机会。
    deploy 与 destroy 两个 parser（含子动词）上都不得出现对应的选项或 dest。"""
    for prog in ("gherkai deploy", "gherkai destroy"):
        parser = argparse.ArgumentParser(prog=prog, conflict_handler="resolve")
        Provider().add_arguments(parser)
        options, dests = _all_option_dests(parser)
        assert "device_farm_project" not in dests and "version" not in dests, prog
        assert not any("device-farm" in o or o == "--version" for o in options), (prog, sorted(options))


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
    # 特性开关逐字沿用收编前那一组：换一组就是给已部署 stack 造无意义变更集
    assert data["context"] == CDK_FEATURE_FLAGS
    # 设计参数**不进** cdk.json（一律 `-c` 显式传，免被 cdk.json 静默兜住）
    assert not CONTEXT_CLOSED_SET & set(data["context"])


# ---------------------------------------------------------------- VPC 取值三态（纯逻辑）

@pytest.mark.parametrize("stored,requested,expected", [
    ("default", "default", True),
    ("vpc-0abc", "vpc-0abc", True),
    ("new:vpc-0abc", "new", True),          # new 取值带出所建 id → 按 new: 前缀匹配
    ("new", "new", True),                   # 兜住「值只写了 new」的历史形态
    ("default", "new", False),
    ("vpc-0abc", "vpc-0def", False),
    ("new:vpc-0abc", "vpc-0abc", False),    # 不对称：stack 拥有不等于复用外部 VPC（切换会删掉那个 VPC）
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


# ---------------------------------------------------------------- VPC 取值三态（打桩 boto3）

class _ClientError(Exception):
    """botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"An error occurred ({code}): {message}")
        self.response = {"Error": {"Code": code, "Message": message}}


class _NoCredentials(Exception):
    """替身：类名改成与 botocore 的 NoCredentialsError 相同（provider 按异常类名识别「没有凭证」）。"""


_NoCredentials.__name__ = "NoCredentialsError"
_RECORD_READ_ERRORS = [
    _ClientError("AccessDeniedException", "not authorized to perform ssm:GetParameter"),
    _NoCredentials("Unable to locate credentials"),
    _ClientError("ThrottlingException", "Rate exceeded"),
    ConnectionError("Could not connect to the endpoint URL"),
]
_RECORD_READ_ERROR_IDS = ["access-denied", "no-credentials", "throttling", "network"]


def _assert_record_read_hint(err: str, error: Exception) -> None:
    """读 SSM 记录失败消息的处置半句按错误类别（ADR 0051 决策 10「失败消息的形态」）：无权限列权限、无凭证提示配凭证与 region、
    其余不提权限。"""
    if isinstance(error, _ClientError) and error.response["Error"]["Code"] == "AccessDeniedException":
        assert "ssm:GetParameter" in err
    elif type(error).__name__ == "NoCredentialsError":
        assert "凭证" in err and "region" in err and "ssm:GetParameter" not in err
    else:
        assert "权限" not in err and "ssm:GetParameter" not in err and "稍后重试" in err


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
    """打桩后端读取。**三个钩子都要打**：VPC 取值三态比对走 `_make_cfn_client` / `_make_ssm_client`，
    「缺 --vpc」提示走短超时的 `_make_hint_clients`——同一批桩数据喂两条路径各自的句柄来源。"""
    monkeypatch.setattr(provider_cli, "_make_cfn_client", lambda **kw: _Cfn(stack_exists))
    monkeypatch.setattr(provider_cli, "_make_ssm_client", lambda **kw: _Ssm(stored))
    monkeypatch.setattr(provider_cli, "_make_hint_clients",
                        lambda **kw: (_Cfn(stack_exists), _Ssm(stored)))


def test_guard_first_deploy_proceeds(monkeypatch):
    # ① stack 不存在即真首次部署 → 放行
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    assert Provider()._guard_vpc_spec(_parse("--vpc", "new", "--region", "us-east-1")) is None


def test_guard_unrecorded_blocks_and_points_at_diff(monkeypatch, capsys):
    # ② 参数缺失 + stack 已存在即本机制之前部署的环境（最危险的那一次）→ 以退出码 2 结束，指路 --diff
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
    # ③ 取值一致 → 放行（含 new 取值的 new:<id> 前缀匹配）
    _stub_backend(monkeypatch, stack_exists=True, stored="new:vpc-0abc")
    assert Provider()._guard_vpc_spec(_parse("--vpc", "new", "--region", "us-east-1")) is None


def test_guard_mismatch_blocks(monkeypatch, capsys):
    # ③ 取值不一致 → 以退出码 2 结束（只强制显式给值挡不住第二次 deploy 敲错取值）
    _stub_backend(monkeypatch, stack_exists=True, stored="vpc-0abc123")
    rc = Provider()._guard_vpc_spec(_parse("--vpc", "default", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert "vpc-0abc123" in err and "default" in err  # 两个取值都点名，别让人猜


def test_guard_mismatch_allowed(monkeypatch):
    _stub_backend(monkeypatch, stack_exists=True, stored="vpc-0abc123")
    args = _parse("--vpc", "default", "--region", "us-east-1", "--allow-vpc-change")
    assert Provider()._guard_vpc_spec(args) is None


def test_guard_unexpected_read_error_exits_2_not_traceback(monkeypatch, capsys):
    """凭证/权限/网络故障 → 退出码 2 + 一句话（对用户是「先修凭证」，与 Node 缺失同一类），不抛 traceback。"""
    def boom(**kw):
        raise _ClientError("AccessDenied", "not authorized to perform cloudformation:DescribeStacks")
    monkeypatch.setattr(provider_cli, "_make_cfn_client", lambda **kw: boom())
    rc = Provider()._guard_vpc_spec(_parse("--vpc", "new", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    assert "cloudformation:DescribeStacks" in capsys.readouterr().err


def test_a_bad_profile_exits_2_at_the_entry_not_a_traceback(capsys):
    """`--profile` 名不存在、且未给 `--region`/`AWS_REGION` → 退出码 2 + 一句可读的说明，不抛 botocore 堆栈。

    **这条有意不打桩**、走真实解析链：region 前三级都 miss 时解析会回落读 profile config，不存在的 profile 名
    在 `boto3.session.Session(...)` 构造期就抛 `ProfileNotFound`——抛点排在 `workers._connect` 之前，
    那一层的同类钩子照不到它（实际运行核过：没有这一口，`list-workers` / `push-worker` / `deploy` 三条
    都吐裸堆栈）。故只读动作与 deploy 那条入口各断言一次。解析纯本地推导，这条不碰 AWS。
    """
    rc = Provider().list_workers(_parse("list-workers", "--profile", "definitely-not-a-profile"))
    assert rc == EXIT_PRECONDITION
    assert "连不上 AWS" in capsys.readouterr().err
    rc = Provider()._guard_vpc_spec(_parse("--vpc", "default", "--profile", "definitely-not-a-profile"))
    assert rc == EXIT_PRECONDITION
    assert "连不上 AWS" in capsys.readouterr().err


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
    """容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。"""

    name = "docker"

    def probe(self):
        return None


@pytest.fixture
def cdk(monkeypatch) -> _Recorder:
    """把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。

    **四步必须打桩**：`deploy` 在 cdk 成功后会去连真 SSM/ECR/ECS 并 `docker pull` 基础镜像（ADR 0038）——单测里
    那是「不碰 AWS」这条底线的破口（实际运行过一次：测试直奔 NoCredentialsError 且真拉了一次 GHCR 镜像）。
    调用次数记在 `rec.worker_steps` 上，供「cdk 成功才执行四步」那两条断言。cdk 之前的 Device Farm 项目找回或建立与项目记录
    读取由 autouse 夹具 `df` 打桩，本夹具不重复。
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
    # context 逐项经 -c 传（值形态 k=v）；SSM 没有项目记录 → 项目取「待建立」占位
    pairs = {argv[i + 1] for i, a in enumerate(argv) if a == "-c"}
    assert pairs == {"prefix=prod-", f"version={VERSION}", "use_default_vpc=true", f"device_farm_project={PENDING}"}


def test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json(cdk):
    Provider().diff(_parse("--vpc", "new", "--region", "us-east-1"))
    cwd = Path(cdk.calls[0]["cwd"])
    # cdk 在工作目录里运行（生成的 cdk.json 在那儿，特性开关才生效）
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


def test_deploy_blocked_by_vpc_guard_never_invokes_cdk(cdk, df, monkeypatch, capsys):
    """被 VPC 取值三态拦下 → 不调 cdk，也不碰 Device Farm：找回或建立排在三态之后，被拦的部署不该先在账户里建出项目。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="vpc-0abc")
    rc = Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    assert cdk.calls == [], "被三态拦下时绝不能已经调过 cdk"
    assert df.reads == [] and df.resolves == []


def test_deploy_runs_the_worker_image_steps_after_a_successful_cdk(cdk, monkeypatch):
    """cdk 成功 → 接着执行 worker 镜像第 2/3/4 步（第 1 步随 cdk 事务，ADR 0038）。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert len(cdk.worker_steps) == 1


def test_deploy_skips_the_worker_image_steps_when_cdk_fails(cdk, monkeypatch):
    """cdk 失败 → 不碰镜像（stack 没生效，推上去的 revision 会指着不存在的模板）。退出码透传 cdk 自己的。"""
    cdk.returncode = 7
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 7
    assert cdk.worker_steps == []


def test_deploy_rejects_an_unimplemented_container_engine_before_touching_the_account(monkeypatch, capsys):
    """`GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动
    （区别于「docker 没装」——那只警告，退出码归 cdk 之后的四步）。

    位置与 Node 前置同一类（本地、不花网络、不要凭证）——**先于** VPC 取值比对：给错引擎名的人不该先被要求
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
    原样传会让导出物落进那里、随之消失而命令以退出码 0 结束（实际运行踩过的假成功；早先的测试用绝对 tmp_path、照不出来）。"""
    monkeypatch.chdir(tmp_path)
    args = _parse("--vpc", "new", "--region", "us-east-1")
    args.synth_only = "exported"  # CLI 前端的 --synth-only DIR（接缝契约），相对用户 cwd
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


# ---------------------------------------------------------------- Device Farm 项目：deploy 找回或建立（ADR 0051 决策 10）

def _deploy(*extra: str) -> int:
    return Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1", "--prefix", "vfy-", *extra))


def test_deploy_resolves_the_project_after_the_vpc_guard_and_before_cdk(cdk, df, monkeypatch):
    """编排顺序：VPC 取值三态 → 读项目记录并找回或建立 → cdk。SSM 现值作为 `stored_arn` 交给找回或建立，profile 沿用部署的；
    得到的 ARN 经 `-c device_farm_project=` 交给 stack。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    df.stored = STORED_ARN
    events: list[str] = []
    df.events = events
    guard = Provider._guard_vpc_spec
    monkeypatch.setattr(Provider, "_guard_vpc_spec", lambda self, a: (events.append("vpc"), guard(self, a))[1])

    def _run(argv, **kw):
        events.append("cdk")
        return cdk(argv, **kw)

    monkeypatch.setattr(provider_cli.subprocess, "run", _run)
    assert _deploy("--profile", "acme") == 0
    assert events == ["vpc", "devicefarm", "cdk"]
    assert df.reads == ["vfy-"]
    assert df.resolves == [{"prefix": "vfy-", "profile": "acme", "stored_arn": STORED_ARN}]
    assert _context_pairs(_argv(cdk))["device_farm_project"] == CREATED_ARN


def test_deploy_reports_a_created_project_and_relays_the_resolution_warning(cdk, df, monkeypatch, capsys):
    """新建了项目要说一声（账户里多了一个资源）；部署记录的项目已被删除、转按名称查找时的那句警告经回调原样打到 stderr。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    df.stored = STORED_ARN
    df.resolution = devicefarm.ProjectResolution(arn=CREATED_ARN, source="created")
    df.warn_text = "部署记录的项目已不存在"
    assert _deploy() == 0
    err = capsys.readouterr().err
    assert "警告：部署记录的项目已不存在" in err
    assert CREATED_ARN in err and "建立" in err
    assert _context_pairs(_argv(cdk))["device_farm_project"] == CREATED_ARN


def test_deploy_reports_a_found_same_named_project(cdk, df, monkeypatch, capsys):
    """SSM 没有记录、Device Farm 里已有同名项目 → 按名称找回并说明沿用的是哪一个，ARN 经 context 交给 stack。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    df.resolution = devicefarm.ProjectResolution(arn=CREATED_ARN, source="found")
    assert _deploy() == 0
    err = capsys.readouterr().err
    assert "沿用 Device Farm 里已有的同名项目" in err and CREATED_ARN in err
    assert _context_pairs(_argv(cdk))["device_farm_project"] == CREATED_ARN


def test_deploy_relays_the_not_found_warning_even_when_resolution_then_fails(cdk, df, monkeypatch, capsys):
    """记录的项目已不存在、随后列举被限流：那句警告仍到达 stderr（事实在核对出来时已发出），命令以退出码 1 结束、不调 cdk。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    df.stored = STORED_ARN
    df.warn_text = "部署记录的项目已不存在"
    df.resolve_error = _ClientError("ThrottlingException", "Rate exceeded")
    assert _deploy() == EXIT_FAILED
    err = capsys.readouterr().err
    assert "警告：部署记录的项目已不存在" in err and "Rate exceeded" in err
    assert cdk.calls == []


def test_deploy_with_several_same_named_projects_exits_2_without_cdk(cdk, df, monkeypatch, capsys):
    """同名项目不止一个 → 以退出码 2 结束、点名命中的 ARN，不替部署方挑选，cdk 与镜像步骤一个都不执行。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    df.resolve_error = devicefarm.AmbiguousProject("vfy-devices", [STORED_ARN, CREATED_ARN])
    assert _deploy() == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert STORED_ARN in err and CREATED_ARN in err
    assert cdk.calls == [] and cdk.worker_steps == []


def test_deploy_without_device_farm_permission_keeps_the_recorded_project_and_warns(cdk, df, monkeypatch, capsys):
    """部署方没有 Device Farm 权限、SSM 记着 ARN → 沿用它并警告：已部署的设备支持不因这次部署被撤掉。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    df.stored = STORED_ARN
    df.resolve_error = devicefarm.DeviceFarmAccessDenied("GetProject", "AccessDeniedException")
    assert _deploy() == 0
    err = capsys.readouterr().err
    assert "警告" in err and STORED_ARN in err and "devicefarm:GetProject" in err
    assert "保持不变" in err and "未启用设备支持" not in err and "devicefarm:CreateProject" in err and "us-west-2" in err
    assert _context_pairs(_argv(cdk))["device_farm_project"] == STORED_ARN
    assert len(cdk.worker_steps) == 1  # 降级不影响 cdk 之后的镜像步骤


def test_deploy_without_permission_after_the_recorded_project_vanished_skips_device_support(cdk, df, monkeypatch, capsys):
    """记录的项目已被删除（GetProject 回 NotFound）、按名称找回或新建又没有权限 → 视同没有记录：context 传「待建立」占位
    （stack 不把已不存在的 ARN 写回 SSM、撤掉设备授权），警告说清项目已不存在、本次按未启用设备支持部署、怎么恢复，
    不说「设备支持保持不变」。沿用已不存在的 ARN 会让设备 run 到执行时才失败。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    df.stored = STORED_ARN
    df.resolve_error = devicefarm.DeviceFarmAccessDenied("ListProjects", "AccessDeniedException", stored_project_missing=True)
    assert _deploy() == 0
    err = capsys.readouterr().err
    assert "已不存在" in err and STORED_ARN in err and "未启用设备支持" in err and "保持不变" not in err
    assert "devicefarm:ListProjects" in err and "devicefarm:CreateProject" in err and "gherkai deploy" in err
    assert _context_pairs(_argv(cdk))["device_farm_project"] == PENDING
    assert len(cdk.worker_steps) == 1  # 降级不影响 cdk 之后的镜像步骤


def test_deploy_without_permission_and_without_record_skips_device_support_and_warns(cdk, df, monkeypatch, capsys):
    """没有权限、SSM 也没有记录 → 警告后跳过：context 不带 ARN（传「待建立」占位），stack 照常部署、不启用设备支持。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    df.resolve_error = devicefarm.DeviceFarmAccessDenied("ListProjects", "AccessDeniedException")
    assert _deploy() == 0
    err = capsys.readouterr().err
    assert "警告" in err and "不启用设备支持" in err
    assert "devicefarm:ListProjects" in err and "devicefarm:CreateProject" in err  # 怎么办：要补的权限点名
    assert _context_pairs(_argv(cdk))["device_farm_project"] == PENDING


@pytest.mark.parametrize("error", [
    _ClientError("ThrottlingException", "Rate exceeded"),
    _ClientError("ServiceAccountException", "internal"),
    ConnectionError("Could not connect to the endpoint URL"),
], ids=["throttling", "service", "network"])
def test_deploy_other_device_farm_errors_exit_1_without_guessing(cdk, df, monkeypatch, capsys, error):
    """权限以外的错误（限流、服务端、网络）以退出码 1 结束、不调 cdk：当成「没有项目」会多建一个，当成无权限降级会让
    stack 撤掉设备授权，而这只有到设备 run 执行时才暴露。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    df.stored = STORED_ARN
    df.resolve_error = error
    assert _deploy() == EXIT_FAILED
    err = capsys.readouterr().err
    assert "vfy-devices" in err and "gherkai deploy" in err and "Traceback" not in err
    assert cdk.calls == [] and cdk.worker_steps == []


@pytest.mark.parametrize("error", _RECORD_READ_ERRORS, ids=_RECORD_READ_ERROR_IDS)
def test_deploy_unreadable_project_record_exits_2_without_resolving(cdk, df, monkeypatch, capsys, error):
    """读不到 SSM 里的项目记录（无权限、无凭证、网络、限流）→ 以退出码 2 结束，不找回不建立、不调 cdk：不知道记录在不在，就无从
    判断该沿用还是该建立；当作「没有记录」继续，无权限降级会撤掉已部署的设备授权。处置半句按错误类别：只有无权限才列权限。"""
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    df.read_error = error
    assert _deploy() == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert names.ssm_device_farm_project_path("vfy-") in err and str(error) in err and "Traceback" not in err
    _assert_record_read_hint(err, error)
    assert df.resolves == [] and cdk.calls == []


@pytest.mark.parametrize("verb", ["deploy", "diff", "destroy"])
def test_malformed_project_record_exits_2_and_names_the_parameter(cdk, df, verb, tmp_path, monkeypatch, capsys):
    """SSM 记录不是合法的项目 ARN（只会因手工改动出现）→ deploy 与只读路径都以退出码 2 结束、不调 cdk、不找回不核对，消息点名
    SSM 路径并给出查项目 ARN 的命令；不当作「没有记录」继续（无权限降级会撤掉已部署的授权），也不建议删参数。"""
    monkeypatch.chdir(tmp_path)
    _stub_backend(monkeypatch, stack_exists=True, stored="default")
    df.stored = "arn:aws:devicefarm:us-east-1:111122223333:project:wrong-region"
    if verb == "deploy":
        rc = _deploy()
    else:
        method, args = _verb_call(verb, "--vpc", "default", "--region", "us-east-1", "--prefix", "vfy-")
        rc = method(args)
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert names.ssm_device_farm_project_path("vfy-") in err and "list-projects" in err and "Traceback" not in err
    assert cdk.calls == [] and df.resolves == [] and df.verifies == []


# ---------------------------------------------------------------- Device Farm 项目：diff / --synth-only / destroy 只读

def _verb_call(verb: str, *argv: str):
    """按动作取 Provider 方法与 args（destroy 走真 destroy parser；synth 给导出目录）。"""
    if verb == "destroy":
        return Provider().destroy, _parse_destroy(*argv)
    args = _parse(*argv)
    if verb == "synth":
        args.synth_only = "exported"
        return Provider().synth_only, args
    return Provider().diff, args


READ_ONLY_VERBS = ("diff", "synth", "destroy")


@pytest.mark.parametrize("verb", READ_ONLY_VERBS)
def test_read_only_verbs_use_the_recorded_project_and_never_create_one(cdk, df, verb, tmp_path, monkeypatch):
    """diff / --synth-only / destroy 不建立项目：SSM 有值即沿用（diff 先用 GetProject 核对、项目还在），交给 stack 的是那个 ARN；
    找回或建立一次都不调。"""
    monkeypatch.chdir(tmp_path)
    df.stored = STORED_ARN
    method, args = _verb_call(verb, "--vpc", "new", "--region", "us-east-1", "--prefix", "vfy-")
    assert method(args) == 0
    argv = _argv(cdk)
    assert argv[1] == verb
    assert _context_pairs(argv)["device_farm_project"] == STORED_ARN
    assert df.reads == ["vfy-"] and df.resolves == []
    assert df.verifies == ([{"arn": STORED_ARN, "profile": None}] if verb == "diff" else [])


@pytest.mark.parametrize("verb", READ_ONLY_VERBS)
def test_read_only_verbs_use_pending_when_nothing_is_recorded(cdk, df, verb, tmp_path, monkeypatch, capsys):
    """参数不存在（含 stack 还不存在）→「待建立」占位，仍不建立项目；没有记录也就没有可核对的项目。diff 另提示变更集不含
    设备授权、实际部署会多出项目参数与授权（首次启用设备支持的那次 deploy 会比 diff 多出这两部分）；synth 与 destroy 不提示。"""
    monkeypatch.chdir(tmp_path)
    method, args = _verb_call(verb, "--vpc", "new", "--region", "us-east-1")
    assert method(args) == 0
    assert _context_pairs(_argv(cdk))["device_farm_project"] == PENDING
    assert df.resolves == [] and df.verifies == []
    err = capsys.readouterr().err
    if verb == "diff":
        assert "提示" in err and "gherkai deploy" in err and devicefarm.project_name("gherkai-") in err
    else:
        assert "提示" not in err and "警告" not in err


@pytest.mark.parametrize("verb", READ_ONLY_VERBS)
@pytest.mark.parametrize("error", _RECORD_READ_ERRORS, ids=_RECORD_READ_ERROR_IDS)
def test_read_only_verbs_exit_2_when_the_record_is_unreadable(cdk, df, verb, error, tmp_path, monkeypatch, capsys):
    """读不到项目记录 → 以退出码 2 结束、不调 cdk，消息写明读的是哪个 SSM 路径与原异常；处置半句按错误类别：只有无权限才列权限，
    无凭证提示配凭证与 region，限流与网络不说成权限问题。不回落占位：那会让 diff 把已部署的设备授权显示成删除，误导依据它
    核对变更的人。"""
    monkeypatch.chdir(tmp_path)
    df.read_error = error
    method, args = _verb_call(verb, "--vpc", "new", "--region", "us-east-1", "--prefix", "vfy-")
    assert method(args) == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert names.ssm_device_farm_project_path("vfy-") in err and str(error) in err and "Traceback" not in err
    _assert_record_read_hint(err, error)
    assert cdk.calls == [] and df.resolves == [] and df.verifies == []


def test_diff_shows_pending_and_warns_when_the_recorded_project_is_gone(cdk, df, capsys):
    """SSM 有记录、GetProject 回 NotFound（项目被手动删除）→ diff 以「待建立」占位并警告：下一次 deploy 会按名称找回或新建、
    换成别的 ARN，沿用旧 ARN 的变更集会与真实部署不一致。仍不找回、不建立：CreateProject 只经找回或建立这一入口，
    它一次都没被调用（Device Farm 客户端的构造点也已换成直接失败）。"""
    df.stored = STORED_ARN
    df.project_exists = False
    assert Provider().diff(_parse("--vpc", "new", "--region", "us-east-1", "--prefix", "vfy-")) == 0
    assert _context_pairs(_argv(cdk))["device_farm_project"] == PENDING
    err = capsys.readouterr().err
    assert "警告" in err and STORED_ARN in err and "已不存在" in err
    assert "gherkai deploy" in err and devicefarm.project_name("vfy-") in err
    assert df.verifies == [{"arn": STORED_ARN, "profile": None}] and df.resolves == []


@pytest.mark.parametrize("verb", ("synth", "destroy"))
def test_synth_only_and_destroy_take_the_record_without_verifying_it(cdk, df, verb, tmp_path, monkeypatch, capsys):
    """只有 diff 核对：--synth-only 与 destroy 直接沿用 SSM 现值，即使记录的项目其实已不存在也不调 GetProject、不警告。"""
    monkeypatch.chdir(tmp_path)
    df.stored = STORED_ARN
    df.project_exists = False
    method, args = _verb_call(verb, "--vpc", "new", "--region", "us-east-1")
    assert method(args) == 0
    assert _context_pairs(_argv(cdk))["device_farm_project"] == STORED_ARN
    assert df.verifies == [] and df.resolves == []
    assert "已不存在" not in capsys.readouterr().err


def test_diff_without_get_project_permission_keeps_the_record_and_warns(cdk, df, capsys):
    """GetProject 无权限 → diff 与 deploy 同一降级：按记录里的项目计算变更集（cdk context 带该 ARN）并警告没能核对、点名所需的
    devicefarm:GetProject 权限，不以退出码 2 结束（允许无权限部署方降级部署，就不能让他不能预览变更集）。仍不找回、不建立。"""
    df.stored = STORED_ARN
    df.verify_error = devicefarm.DeviceFarmAccessDenied("GetProject", "AccessDeniedException")
    assert Provider().diff(_parse("--vpc", "new", "--region", "us-east-1", "--prefix", "vfy-")) == 0
    assert _context_pairs(_argv(cdk))["device_farm_project"] == STORED_ARN
    err = capsys.readouterr().err
    assert "警告" in err and STORED_ARN in err and "devicefarm:GetProject" in err and "Traceback" not in err
    assert df.verifies == [{"arn": STORED_ARN, "profile": None}] and df.resolves == []


@pytest.mark.parametrize("error", [
    _ClientError("ThrottlingException", "Rate exceeded"),
    _ClientError("ServiceAccountException", "internal"),
    ConnectionError("Could not connect to the endpoint URL"),
], ids=["throttling", "service", "network"])
def test_diff_exits_2_when_verifying_the_recorded_project_fails_otherwise(cdk, df, error, capsys):
    """GetProject 的其他失败（限流、服务端、网络）→ diff 以退出码 2 结束、不调 cdk，消息点名 SSM 路径、记录的 ARN 与原异常，
    不把它说成缺权限。不回落占位，也不沿用未核对的记录：两者都可能与下一次部署不一致。"""
    df.stored = STORED_ARN
    df.verify_error = error
    assert Provider().diff(_parse("--vpc", "new", "--region", "us-east-1", "--prefix", "vfy-")) == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert names.ssm_device_farm_project_path("vfy-") in err and STORED_ARN in err and str(error) in err
    assert "权限" not in err and "Traceback" not in err
    assert cdk.calls == [] and df.resolves == []


@pytest.mark.parametrize("verb", ("diff", "destroy"))
def test_no_credentials_is_not_an_exception_for_diff_or_destroy(cdk, df, verb, capsys):
    """完全没有凭证时只有 --synth-only 可回落占位；diff 与 destroy 照常去读、读失败以退出码 2 结束。"""
    df.has_credentials = False
    df.read_error = type("NoCredentialsError", (Exception,), {})("Unable to locate credentials")
    method, args = _verb_call(verb, "--vpc", "new", "--region", "us-east-1")
    assert method(args) == EXIT_PRECONDITION
    assert cdk.calls == []


def test_synth_only_without_any_credentials_exports_offline_with_pending_and_warns(cdk, df, tmp_path, monkeypatch, capsys):
    """完全没有凭证（也没有 region）时 --synth-only 照样离线导出：项目取「待建立」占位，并在 stderr 警告导出的模板不含远程
    访问会话的授权、可能与已部署的 stack 不一致。这时不建 SSM 句柄——没有 region 时建句柄本身就会失败。"""
    monkeypatch.chdir(tmp_path)
    df.has_credentials = False

    def _no_ssm(**kw):
        raise AssertionError("没有凭证时不该去读 SSM")

    monkeypatch.setattr(provider_cli, "_make_ssm_client", _no_ssm)
    method, args = _verb_call("synth", "--vpc", "new")
    assert method(args) == 0
    assert _context_pairs(_argv(cdk))["device_farm_project"] == PENDING
    err = capsys.readouterr().err
    assert "警告" in err and "远程访问会话" in err and "不一致" in err
    assert df.reads == [] and df.resolves == []


def test_synth_only_treats_a_credential_lookup_error_as_having_credentials(cdk, df, tmp_path, monkeypatch, capsys):
    """解析凭证链本身出错（如 profile 名不存在）不算「完全没有凭证」：不回落占位，照常去读 SSM，读失败按退出码 2 结束。"""
    monkeypatch.chdir(tmp_path)

    def _lookup_fails(**kw):
        raise RuntimeError("The config profile (nope) could not be found")

    monkeypatch.setattr(provider_cli, "_has_aws_credentials", _lookup_fails)
    df.read_error = RuntimeError("The config profile (nope) could not be found")
    method, args = _verb_call("synth", "--vpc", "new", "--region", "us-east-1", "--prefix", "vfy-")
    assert method(args) == EXIT_PRECONDITION
    assert df.reads == ["vfy-"] and cdk.calls == []


def test_has_aws_credentials_follows_the_credential_chain(monkeypatch, tmp_path):
    """「完全没有凭证」的判据走 boto3 真实的凭证链（只解析、不发请求）：链上什么都没有时为 False，给了环境变量凭证即 True。
    把共享配置、boto 旧配置与实例元数据都指向空处，开发机上已有的凭证才不会让断言飘。"""
    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_SECURITY_TOKEN",
                "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "AWS_CONTAINER_CREDENTIALS_FULL_URI",
                "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_ROLE_ARN"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "no-credentials"))
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "no-config"))
    monkeypatch.setenv("BOTO_CONFIG", str(tmp_path / "no-boto-config"))
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    assert _REAL_HAS_AWS_CREDENTIALS(profile=None) is False
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAEXAMPLEEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "example-secret")
    assert _REAL_HAS_AWS_CREDENTIALS(profile=None) is True


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


def test_missing_cdk_stops_deploy_before_any_aws_read(df, monkeypatch, capsys):
    """有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。

    **不能落到 cdk 调用那一层再退**：那时会多打一条「失败原因见上方 cdk 输出……最常见的是未 bootstrap」，
    而这条路径上 cdk 一行输出都没有，且它建议的 `gherkai deploy --bootstrap` 会以同样的「找不到 cdk」失败。
    """
    monkeypatch.setattr(provider_cli, "check_node", lambda: None)
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: [])
    monkeypatch.setattr(Provider, "_container_engine", staticmethod(lambda args: _FakeEngine()))
    ran = _Recorder()
    monkeypatch.setattr(provider_cli.subprocess, "run", ran)

    aws_reads: list[str] = []

    def _no_aws(**kw):
        aws_reads.append("read")
        raise AssertionError("工具链前置不该先读 AWS")  # 会被 _guard_vpc_spec 的宽 except 吞掉，故另立账

    monkeypatch.setattr(provider_cli, "_make_cfn_client", _no_aws)
    monkeypatch.setattr(provider_cli, "_make_ssm_client", _no_aws)
    monkeypatch.setattr(provider_cli, "_make_hint_clients", _no_aws)  # 建句柄的入口有三个，漏一个就留洞

    rc = Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1"))
    assert rc == EXIT_PRECONDITION
    err = capsys.readouterr().err
    assert "找不到 cdk" in err and "bootstrap" not in err
    assert ran.calls == []   # 一个子进程都没起
    assert aws_reads == []   # 一次 AWS 句柄都没建
    assert df.reads == [] and df.resolves == []  # 也没碰 Device Farm


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


def test_help_does_not_pull_boto3_or_the_device_farm_module():
    """`gherkai deploy --help` / `destroy --help` 只需本模块与 flag 面：boto3 与 `gherkai_runtime.devicefarm` 都在函数内延迟导入。

    子进程里往 `sys.modules` 塞毒（值为 None 时 import 立即失败），再贴两个 parser、生成帮助文本；同时断言 Device Farm 模块
    没被提前导入。放在子进程里，免得本会话其他测试早已 import 过的模块让断言恒绿。
    """
    import subprocess as sp

    code = (
        "import argparse, sys\n"
        "for m in ('boto3', 'botocore'):\n"
        "    sys.modules[m] = None\n"
        "from gherkai_deploy_aws.cli import Provider\n"
        "for prog in ('gherkai deploy', 'gherkai destroy'):\n"
        "    p = argparse.ArgumentParser(prog=prog, conflict_handler='resolve')\n"
        "    Provider().add_arguments(p)\n"
        "    p.format_help()\n"
        "print('gherkai_runtime.devicefarm' in sys.modules)\n"
    )
    out = sp.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False", "帮助路径提前导入了 Device Farm 模块"


def test_tolerates_a_shell_that_declares_neither_command_face_flag(monkeypatch, capsys):
    """别的前端（或编程式调用）没给 `--allow-vpc-change` 时**fail-closed**：取值不符照拦、不因缺 flag 就放行。"""
    parser = argparse.ArgumentParser(prog="other-shell")
    Provider().add_arguments(parser)
    args = parser.parse_args(["--vpc", "default", "--region", "us-east-1"])
    args.version = VERSION
    del args.allow_vpc_change, args.require_approval  # 模拟「前端压根没这两个 flag」
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
    多一轮查询）。缓存按 prefix 持久化在用户缓存目录：第一次运行结束存回；第二次进全新工作目录前先放进去。"""
    cache = _cache_env(monkeypatch, tmp_path)
    rec = _CdkWritingContext()
    monkeypatch.setattr(provider_cli.subprocess, "run", rec)
    assert not cache.exists()
    assert Provider().diff(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert rec.seeded_with == [None]                      # 首次：无缓存可放
    assert cache.exists() and "vpc-cached" in cache.read_text()  # 运行结束存回
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
    # 前端在 destroy parser 上**只**贴 provider 选择那一个 flag：`--allow-vpc-change` / `--require-approval`
    # 的中立版只在 deploy 上（见 `_parse` 与 cli 模块头「两层声明」），故这里不能手工补——补了就掩盖
    # 「destroy 侧根本没有这两个选项」这条接线事实。
    parser = argparse.ArgumentParser(prog="gherkai destroy", conflict_handler="resolve")
    Provider().add_arguments(parser)
    args = parser.parse_args(argv)
    args.version = VERSION
    return args


def test_destroy_yes_passes_force_to_cdk_and_is_off_by_default(cdk):
    """cdk destroy 在非 TTY 下拒绝无确认的销毁（实际运行撞到）；`--yes` 等同于 `--force`，不给则让 cdk 自己问。"""
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
    """容器引擎缺失的前置警告只对**纯发行版**成立：dev/post/本地段版本的 worker 镜像步骤本就走不到「基础镜像同步」
    （ADR 0038 定位链第四级门槛是 is_pure_release），那时警告「之后的镜像步骤会失败」是假警报。"""
    _stub_backend(monkeypatch, stack_exists=False, stored=None)
    monkeypatch.setattr(Provider, "_container_engine", staticmethod(lambda args: _AbsentEngine()))

    monkeypatch.setattr(Provider, "_resolve_version", staticmethod(lambda args: "1.4.0"))
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert "docker 未安装" in capsys.readouterr().err

    monkeypatch.setattr(Provider, "_resolve_version", staticmethod(lambda args: "1.4.0.dev3+g0123abc"))
    assert Provider().deploy(_parse("--vpc", "default", "--region", "us-east-1")) == 0
    assert "docker 未安装" not in capsys.readouterr().err


def test_provider_doctor_reports_toolchain(monkeypatch):
    """`gherkai doctor` 的 provider 段（ADR 0041 决策四）：node、cdk、容器引擎三项均为可选（required=False）；全部只读，不访问 AWS。"""
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
    # provider 段是部署能力清单：三项都 required=False（doctor 不知道这台机器要不要部署；硬拦在 gherkai deploy 自身）
    assert checks["node"]["ok"] and checks["node"]["required"] is False
    assert checks["cdk"]["ok"] and checks["cdk"]["detail"] == "cdk-stub" and checks["cdk"]["required"] is False
    assert checks["container-engine"]["ok"] and checks["container-engine"]["required"] is False

    monkeypatch.setattr(provider_cli, "check_node", lambda: "找不到 node：需要 Node ≥ 22")
    monkeypatch.setattr(provider_cli, "cdk_command", lambda: [])
    checks = {c["name"]: c for c in Provider().doctor(SimpleNamespace())}
    assert not checks["node"]["ok"] and not checks["cdk"]["ok"] and "npx" in checks["cdk"]["detail"]
