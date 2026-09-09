"""`gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 + flag 贡献 + 分派。

**全程 stub entry point 与 provider**：皮的契约只有「按 entry point group 发现 → 调 `add_arguments` 贴 flag →
按自己的命令面 flag 选调方法 → 透传退出码」，真 provider（`gherkai-deploy-aws`，带 CDK + Node）不该是皮的
测试依赖——它的 IaC 行为、VPC 档比对、cdk 调用都在它自己那边验。皮的硬不变量「**皮不 import `aws_cdk`**」
与「非 deploy 子命令**不加载** provider」也在此断言（后者是「别让 `gherkai run` 付 jsii 起 node 的代价」）。
"""
from __future__ import annotations

import sys

import pytest

from gherkai_cli import __main__ as m
from gherkai_cli import deploy as dp


class _StubProvider:
    """按 deploy.py 契约块实现的假 provider：贴三个旋钮、记录被调的动作与拿到的 args。"""

    name = "stub"

    def __init__(self, rc: int = 0):
        self.rc = rc
        self.calls: list[tuple[str, object]] = []

    def add_arguments(self, parser):  # 模仿 AWS provider 的三 flag（ADR 0037 决策 6 的四个 context 旋钮）
        parser.add_argument("--prefix", default=None)
        parser.add_argument("--vpc", default=None)
        parser.add_argument("--stop-timeout", type=int, default=None)

    def _record(self, verb, args):
        self.calls.append((verb, args))
        return self.rc

    def deploy(self, args): return self._record("deploy", args)
    def destroy(self, args): return self._record("destroy", args)
    def diff(self, args): return self._record("diff", args)
    def synth_only(self, args): return self._record("synth_only", args)
    def bootstrap(self, args): return self._record("bootstrap", args)


class _FakeEP:
    """假 entry point：`.name`/`.value` 供发现与诊断，`.load()` 给出 provider（或抛，模拟半装）。"""

    def __init__(self, name, obj=None, *, load_error=None):
        self.name = name
        self.value = f"stub_{name}.cli:Provider"
        self._obj = obj
        self._err = load_error

    def load(self):
        if self._err is not None:
            raise self._err
        return self._obj


def _patch_eps(monkeypatch, *eps):
    """把 provider 发现面换成给定的假 entry point（不碰本机真装的 provider）。"""
    monkeypatch.setattr(dp, "entry_points", lambda group: list(eps) if group == dp.PROVIDER_GROUP else [])


# ---- provider 发现：零个 / 一个 / 多个（ADR 0037 决策 6）----

def test_zero_providers_points_at_the_extra(monkeypatch, capsys):
    """没装 provider → 退 2 且提示装 `gherkai[deploy-aws]`（不是「未知命令」也不是 traceback）。"""
    _patch_eps(monkeypatch)
    assert m.main(["deploy"]) == 2
    err = capsys.readouterr().err
    assert "gherkai[deploy-aws]" in err and "部署方" in err


def test_single_provider_needs_no_provider_flag(monkeypatch):
    """装一个 → 直接用它、无需 `--provider`（决策 6：单 provider 时不让用户敲废话）。"""
    prov = _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    assert m.main(["deploy"]) == 0
    assert [c[0] for c in prov.calls] == ["deploy"]


def test_multiple_providers_require_provider_flag(monkeypatch, capsys):
    """装多个 + 不给 `--provider` → 退 2 并列出名字（皮不替用户猜「往哪个云部署」）。"""
    a, b = _StubProvider(), _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", a), _FakeEP("zzz", b))
    assert m.main(["deploy"]) == 2
    err = capsys.readouterr().err
    assert "--provider" in err and "aws" in err and "zzz" in err
    assert not a.calls and not b.calls


def test_multiple_providers_selected_by_name(monkeypatch):
    """装多个 + `--provider <名>` → 用点名的那个（名 = entry point 名）。"""
    a, b = _StubProvider(), _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", a), _FakeEP("zzz", b))
    assert m.main(["deploy", "--provider", "zzz"]) == 0
    assert not a.calls and [c[0] for c in b.calls] == ["deploy"]


def test_unknown_provider_name_lists_installed(monkeypatch, capsys):
    _patch_eps(monkeypatch, _FakeEP("aws", _StubProvider()))
    assert m.main(["deploy", "--provider", "gcp"]) == 2
    err = capsys.readouterr().err
    assert "gcp" in err and "aws" in err


def test_provider_load_failure_is_named_not_traceback(monkeypatch, capsys):
    """provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。

    「装了但不可用」与「没装」是两种处境、措辞必须分开（前者不该被劝去 `pip install`）。
    """
    _patch_eps(monkeypatch, _FakeEP("aws", load_error=ImportError("No module named 'x'")))
    assert m.main(["deploy"]) == 2
    err = capsys.readouterr().err
    assert "stub_aws.cli:Provider" in err and "ImportError" in err


def test_entry_point_class_gets_instantiated(monkeypatch):
    """entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。"""
    _patch_eps(monkeypatch, _FakeEP("aws", _StubProvider))
    prov, err = dp.resolve_provider(None)
    assert err is None and isinstance(prov, _StubProvider)

    ready = _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", ready))
    prov2, err2 = dp.resolve_provider(None)
    assert err2 is None and prov2 is ready


# ---- flag 贡献与分派 ----

def test_provider_flags_contributed_and_reach_provider(monkeypatch):
    """provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。"""
    prov = _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    assert m.main(["deploy", "--vpc", "default", "--prefix", "p-", "--stop-timeout", "30"]) == 0
    verb, args = prov.calls[0]
    assert verb == "deploy"
    assert (args.vpc, args.prefix, args.stop_timeout) == ("default", "p-", 30)


def test_command_face_flags_reach_provider(monkeypatch):
    """皮自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给 provider 取。"""
    prov = _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    assert m.main(["deploy", "--require-approval", "never", "--allow-vpc-change"]) == 0
    _verb, args = prov.calls[0]
    assert args.require_approval == "never" and args.allow_vpc_change is True


@pytest.mark.parametrize("argv,verb", [
    (["deploy"], "deploy"),
    (["deploy", "--diff"], "diff"),
    (["deploy", "--synth-only", "/tmp/out"], "synth_only"),
    (["deploy", "--bootstrap"], "bootstrap"),
    (["destroy"], "destroy"),
])
def test_dispatch_maps_command_face_to_provider_method(monkeypatch, argv, verb):
    """命令面 → provider 方法的映射（决策 6 的四路 + destroy）。皮只做这一件事、零 IaC 知识。"""
    prov = _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    assert m.main(argv) == 0
    assert [c[0] for c in prov.calls] == [verb]


def test_synth_only_dir_lands_on_args(monkeypatch):
    """`--synth-only DIR` 的 DIR 经 `args.synth_only` 交给 provider（皮不建目录、不碰模板）。"""
    prov = _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    m.main(["deploy", "--synth-only", "/tmp/out"])
    assert prov.calls[0][1].synth_only == "/tmp/out"


def test_three_actions_are_mutually_exclusive(monkeypatch):
    """`--diff` / `--synth-only` / `--bootstrap` 三个动作互斥（同时给 → argparse 退 2，不猜意图）。"""
    _patch_eps(monkeypatch, _FakeEP("aws", _StubProvider()))
    with pytest.raises(SystemExit) as e:
        m.main(["deploy", "--diff", "--bootstrap"])
    assert e.value.code == 2


def test_provider_exit_code_is_passed_through(monkeypatch):
    """退出码原样透传（provider 里 cdk 的失败码不被压成皮自己的码）。"""
    prov = _StubProvider(rc=7)
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    assert m.main(["deploy"]) == 7


def test_cli_version_is_handed_to_provider(monkeypatch):
    """CLI 把**自己的**版本放进 `args.version` 供 provider 写后端版本戳（ADR 0037 决策 6/7）。

    戳必须是「写任务定义那一方」的版本——run/submit 的 skew 闸拿它比（决策 7）。
    """
    prov = _StubProvider()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    m.main(["deploy"])
    assert prov.calls[0][1].version == m._dist_version()


def test_provider_subverb_seam_takes_precedence(monkeypatch):
    """0038 的子动词接缝：provider 在 `add_arguments` 里挂 subparser + `set_defaults(_deploy_verb=…)`，
    皮先看它、不再走默认的真部署（`gherkai deploy push-worker …` 那族命令届时皮一行不改）。"""
    seen: list[str] = []

    class _WithVerb(_StubProvider):
        def add_arguments(self, parser):
            super().add_arguments(parser)
            verbs = parser.add_subparsers(dest="worker_verb")  # 不设 required：裸 deploy 仍走真部署
            pw = verbs.add_parser("push-worker")
            pw.add_argument("image")
            pw.set_defaults(_deploy_verb=lambda args: (seen.append(args.image), 0)[1])

    prov = _WithVerb()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    assert m.main(["deploy", "push-worker", "img:tag"]) == 0
    assert seen == ["img:tag"] and not prov.calls  # 走了子动词、没走 provider.deploy
    assert m.main(["deploy"]) == 0 and [c[0] for c in prov.calls] == ["deploy"]  # 裸 deploy 仍是真部署


# ---- 不变量 ----

def test_help_works_without_provider_and_explains_why(monkeypatch, capsys):
    """`deploy --help` **恒可用**（帮助不该因没装 provider 而失败），且 epilog 自陈「旋钮为何没列出来」。"""
    _patch_eps(monkeypatch)
    with pytest.raises(SystemExit) as e:
        m.main(["deploy", "--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "--diff" in out and "gherkai[deploy-aws]" in out


def test_cli_does_not_import_aws_cdk(monkeypatch):
    """**皮不 import `aws_cdk`**（jsii 绑定，import 即起 node 子进程，ADR 0037 决策 6）。

    做法 = 往 `sys.modules` 塞毒（值为 `None` 时 `import aws_cdk` 立即 ImportError），**不是**事后断言
    `"aws_cdk" not in sys.modules`——后者依赖「本 session 没有别的测试 import 过它」，而 provider 包自己的
    CDK 合成测试就会 import 它，跑全量时那种断言会因执行顺序假失败。塞毒与顺序无关：皮真去 import 就炸。
    只测皮这半边（provider 被 stub）：真 provider 的 import 面由它自己守（其模块头钉了同一条）。
    """
    monkeypatch.setitem(sys.modules, "aws_cdk", None)
    _patch_eps(monkeypatch, _FakeEP("aws", _StubProvider()))
    with pytest.raises(SystemExit):  # --help 路径（贴 flag + 打帮助）
        m.main(["deploy", "--help"])
    assert m.main(["deploy"]) == 0   # 真分派路径同样不碰它


def test_non_deploy_command_does_not_load_any_provider(monkeypatch):
    """非 deploy/destroy 的子命令**不碰 provider 发现面**——否则每次 `gherkai run` 都付一次 provider import。"""
    def _boom(**kwargs):
        raise AssertionError("非部署子命令不该去发现 provider")

    monkeypatch.setattr(dp, "entry_points", _boom)
    assert m.main(["list-engines"]) == 0


def test_readonly_flags_cannot_be_combined_with_a_provider_subverb(monkeypatch, capsys):
    """`--diff/--synth-only/--bootstrap` 与写账户的子动词同给 → 退 2、子动词不跑（ADR 0037 决策 6：三 flag 是
    reviewer 的只读靶点；子动词的分派优先级不得把它们静默吞成真推镜像）。"""
    seen: list[str] = []

    class _WithVerb(_StubProvider):
        def add_arguments(self, parser):
            super().add_arguments(parser)
            verbs = parser.add_subparsers(dest="worker_verb")
            pw = verbs.add_parser("push-worker")
            pw.add_argument("image")
            pw.set_defaults(_deploy_verb=lambda args: (seen.append(args.image), 0)[1])

    prov = _WithVerb()
    _patch_eps(monkeypatch, _FakeEP("aws", prov))
    for flags in (["--diff"], ["--synth-only", "/tmp/out"], ["--bootstrap"]):
        assert m.main(["deploy", *flags, "push-worker", "img:tag"]) == 2, flags
        assert flags[0] in capsys.readouterr().err
    assert seen == [] and not prov.calls  # 子动词与 provider 的四路都没被调


def test_provider_init_failure_is_named_not_traceback(monkeypatch, capsys):
    """entry point 指向类、但实例化炸（provider 的 __init__ 依赖缺失）→ 同「装了但不可用」的诊断，不裸奔 traceback。"""

    class _Broken(_StubProvider):
        def __init__(self):
            raise RuntimeError("provider 初始化失败：缺 X")

    _patch_eps(monkeypatch, _FakeEP("aws", _Broken))
    assert m.main(["deploy"]) == 2
    err = capsys.readouterr().err
    assert "stub_aws.cli:Provider" in err and "RuntimeError" in err
