"""项目配置文件 gherkai.toml（ADR 0053）的护栏：键集差集、定位、取值顺序（含「配置不越过环境变量」）、错误形态、
设备段与应用段的形态、路径基准、doctor 的配置文件行，以及后台宿主（本机后台推进进程、云端隧道守护进程、status --wait 接力）不读
配置文件。"""
from __future__ import annotations

import json
import os
from types import SimpleNamespace
from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_cli import config as cfgmod
from gherkai_cli import settings
from gherkai_cli import device_selection as devsel
from gherkai_runtime import compose

from _inline_children import inline_children  # noqa: F401 —— 夹具：submit 启动的后台进程在线程里执行
from test_main import _fake_locator, _fake_schedule_factory, _no_provider

FEATURE = 'Feature: F\n  Scenario: a\n    When "做事"\n'
DEVICE_FEATURE = '@device:android\nFeature: F\n  Scenario: a\n    When "做事"\n'

# 三份名单，在测试里显式列出：新增选项必须有意识地归入其中一类（决策 6「键集差集」）
PER_CALL = {"--scope", "--tags", "--scenario", "--step", "--json", "--quiet", "--wait", "--all", "--full",
            "--fail-fast", "--no-report", "--engine", "--status", "--limit", "--config"}
COMMON = {"--default-engine", "--assertion-votes", "--max-concurrency", "--default-job-timeout", "--grace", "--expose-local",
          "--tunnel", "--report-dir", "--steps-dir", "--backend", "--region", "--profile"}
CLOUD = {"--prefix", "--ddb-table", "--s3-bucket", "--worker-variant"}
DEVICE = {"--android-device-arn": ("devices.android", "arn"), "--ios-device-arn": ("devices.ios", "arn"),
          "--device-farm-project-arn": ("devices", "project-arn"), "--app-bucket": ("devices", "app-bucket")}


def _feature(tmp_path: Path, text: str = FEATURE) -> Path:
    f = tmp_path / "f.feature"
    f.write_text(text, encoding="utf-8")
    return f


def _toml(tmp_path: Path, body: str, name: str = "gherkai.toml") -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def _plan_json(argv: list[str], capsys) -> dict:
    assert m.main(["plan", *argv, "--json"]) == 0, capsys.readouterr().err
    return json.loads(capsys.readouterr().out)


def _android_caps(engine, *, steps_dir=None, timeout_s=60.0):
    return {"schema_version": 2, "engine": engine, "min_grace_s": 150.0, "deterministic_steps": [], "model_id": "m",
            "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8000.0}]}


def _no_match(engine, *a, **k):
    # 取不到结果（plan 只对这一类降级，ADR 0036 决策 4）：这些用例只看 plan 本体的输出
    raise compose.WorkerUnavailableError(engine, f"引擎 {engine} 的确定性 step 查询超时（60s）")


# ---- 键集差集（ADR 0053 决策 6）----

def test_every_long_option_is_classified_and_the_derived_key_sets_match():
    """八个读配置命令的每个长选项都落在四份名单之一；由 argparse 推出的 [common] / [cloud] 接受集恰等于名单（多一键或少一键都红）。"""
    parser = m._build_parser()
    for name in settings.CONFIG_COMMANDS:
        flags = {s for a in settings.subparser(parser, name)._actions for s in a.option_strings if s.startswith("--")} - {"--help"}
        unclassified = flags - PER_CALL - COMMON - CLOUD - set(DEVICE)
        assert not unclassified, f"{name} 的选项 {sorted(unclassified)} 没归入按次选择型 / [common] / [cloud] / 设备映射表任一类"
    keys = settings.configurable_keys(parser)
    assert keys["common"] == {f[2:] for f in COMMON}
    assert keys["cloud"] == {f[2:] for f in CLOUD}
    assert {f[2:].replace("-", "_") for f in DEVICE} == set(settings.DEVICE_OPTIONS)
    assert {"--" + d.replace("_", "-"): v for d, v in settings.DEVICE_OPTIONS.items()} == DEVICE
    # [devices] 的键表直接对照 ADR 0053 决策 3（没有对应选项的键由此守）
    assert cfgmod.DEVICES_KEYS == ("billing-method", "acquire-timeout-s", "project-arn", "app-bucket")
    assert cfgmod.PLATFORM_KEYS == ("arn", "os-version", "billing-method")
    assert cfgmod.DEVICE_PLATFORMS == ("android", "ios") and cfgmod.BILLING_METHODS == ("METERED", "UNMETERED")
    assert cfgmod.DEFAULT_BILLING_METHOD == "METERED"   # 决策 3：billing-method 内建默认


# ---- 定位（决策 1）----

def test_locate_flag_then_env_then_cwd_and_never_parent(tmp_path):
    cwd = tmp_path / "proj"; sub = cwd / "sub"; sub.mkdir(parents=True)
    default = _toml(cwd, "")
    explicit = _toml(tmp_path, "", name="x.toml")
    env_file = _toml(tmp_path, "", name="e.toml")
    assert cfgmod.locate_config(None, env={}, cwd=cwd) == (default.resolve(), "当前目录的 gherkai.toml")
    assert cfgmod.locate_config(None, env={"GHERKAI_CONFIG": str(env_file)}, cwd=cwd)[0] == env_file.resolve()
    assert cfgmod.locate_config(str(explicit), env={"GHERKAI_CONFIG": str(env_file)}, cwd=cwd)[0] == explicit.resolve()
    assert cfgmod.locate_config(None, env={}, cwd=sub) == (None, "未使用配置文件")  # 不向上级目录查找
    with pytest.raises(cfgmod.ConfigError, match="--config"):
        cfgmod.locate_config(str(tmp_path / "nope.toml"), env={}, cwd=cwd)
    with pytest.raises(cfgmod.ConfigError, match="GHERKAI_CONFIG"):
        cfgmod.locate_config(None, env={"GHERKAI_CONFIG": str(tmp_path / "nope.toml")}, cwd=cwd)


def test_explicit_missing_config_exits_2_before_anything_else(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert m.main(["plan", str(_feature(tmp_path)), "--config", "nope.toml"]) == 2
    err = capsys.readouterr().err
    assert "nope.toml" in err and "--config" in err
    monkeypatch.setenv("GHERKAI_CONFIG", str(tmp_path / "also-nope.toml"))
    assert m.main(["plan", str(_feature(tmp_path))]) == 2
    assert "GHERKAI_CONFIG" in capsys.readouterr().err


# ---- 错误形态（决策 1、3）----

@pytest.mark.parametrize("body, needle", [
    ("[common\n", "line"),                                              # 非法 TOML：点名位置
    ("[commn]\ndefault-engine = 'midscene'\n", "[commn]"),              # 不认识的节
    ("[common]\ndefault-engin = 'midscene'\n", "default-engin"),        # 不认识的键
    ("[common]\ndefault-engine = 'nope'\n", "--default-engine"),        # choices 不合法：报错与命令行上给错同一形态
    ("[common]\nassertion-votes = 'x'\n", "assertion-votes"),           # 类型不合法
    ("[common]\ndefault-job-timeout = 'nan'\n", "default-job-timeout"), # 非有限数与命令行同拒
    ("[common]\nmax-concurrency = true\n", "类型不对"),                   # 布尔不是任何选项的合法类型
    ("[common]\ndefault-engine = ['midscene']\n", "不接受列表"),           # 单值选项给了列表
    ("[cloud]\nscope = 'x'\n", "[cloud]"),                               # 按次选择型不进配置文件
    ("[common]\nmax-concurrency = 4.7\n", "应为整数"),                      # 整数选项给浮点：不截断，与命令行同拒
    ("[common]\nassertion-votes = 2.0\n", "应为整数"),
    ("[common]\nmax-concurrency = inf\n", "应为整数"),                      # 无穷大不成为裸 OverflowError
    ("[common]\nmax-concurrency = 'abc'\n", "应为整数"),                    # 内建类型的失败给产品语言理由
    ("[common]\nmax-concurrency = '4'\n", "应为整数"),                      # 数字选项不收文本：TOML 里 "4" 是文本
    ("[common]\ndefault-job-timeout = 1" + "0" * 400 + "\n", "不是可接受的数字"),  # 自定义校验吞不下的数：不带解释器原文
    # 事件表、cluster、子网与安全组不是 [cloud] 的键，写了即未知键：推进器的这几项取自部署注入的环境变量（ADR 0016 决策 C）
    ("[cloud]\nevents-table = 'x'\n", "events-table"),
    ("[cloud]\ncluster = 'x'\n", "cluster"),
    ("[cloud]\nsubnet = ['subnet-1']\n", "subnet"),
    ("[cloud]\nsecurity-group = ['sg-1']\n", "security-group"),
])
def test_config_errors_exit_2_naming_file_section_and_key(tmp_path, monkeypatch, capsys, body, needle):
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, body)
    assert m.main(["submit", str(_feature(tmp_path)), "--backend", "cloud"]) == 2
    err = capsys.readouterr().err
    assert "gherkai.toml" in err and needle in err


def test_removed_tunnel_ttl_is_unknown_on_the_command_line_and_in_the_config_file(tmp_path, monkeypatch, capsys):
    """submit 不再有 --tunnel-ttl（隧道随持有它的进程退出而关闭，ADR 0035 决策 3）：命令行上给它是不认识的参数，退出码 2；配置文件的
    键由选项派生（ADR 0053 决策 6），同名的键随之成为不认识的键，同样以退出码 2 结束、点名文件、节与键，不提示可用的键里有它。"""
    monkeypatch.chdir(tmp_path)
    feat = str(_feature(tmp_path))
    with pytest.raises(SystemExit) as ei:
        m.main(["submit", feat, "--tunnel-ttl", "5"])
    assert ei.value.code == 2
    assert "unrecognized arguments: --tunnel-ttl 5" in capsys.readouterr().err
    cfg = _toml(tmp_path, "[common]\ntunnel-ttl = 30\n")
    assert m.main(["submit", feat]) == 2
    err = capsys.readouterr().err
    assert f"配置文件 {cfg.resolve()} 的 [common] 里有不认识的键 tunnel-ttl；" in err
    assert err.count("tunnel-ttl") == 1 and "Traceback" not in err


@pytest.mark.parametrize("argv", [["run"], ["run", "f.feature"], ["submit", "f.feature"]],
                         ids=["run-without-feature", "run", "submit"])
@pytest.mark.parametrize("key", ["steps-dir", "report-dir"])
def test_config_path_that_cannot_be_resolved_is_a_config_error(tmp_path, monkeypatch, capsys, argv, key):
    """配置文件里的路径解析不了（如含空字符）：以配置错误结束、退出码 2、点名文件与取值，解析路径的内部异常不冒到终端。
    run 没有给 feature 时也是这一句：配置不可用排在缺少 features 之前。"""
    monkeypatch.chdir(tmp_path)
    _feature(tmp_path)
    _toml(tmp_path, f'[common]\nbackend = "local"\n{key} = "\\u0000"\n')
    assert m.main(argv) == 2
    err = capsys.readouterr().err
    assert "gherkai.toml" in err and "不是可用的路径" in err
    assert "Traceback" not in err and "embedded null" not in err


def test_app_entry_path_that_cannot_be_resolved_is_a_config_error(tmp_path, monkeypatch, capsys):
    """`[apps.<别名>.<平台>]` 的 file 解析不了时同样是配置错误：退出码 2，点名文件与那一节，内部异常不冒到终端。"""
    monkeypatch.chdir(tmp_path)
    id_key = cfgmod.APP_ID_KEY["android"]
    _toml(tmp_path, f'[apps.demo.android]\nfile = "\\u0000"\n{id_key} = "com.example.demo"\n')
    assert m.main(["run", str(_feature(tmp_path))]) == 2
    err = capsys.readouterr().err
    assert "gherkai.toml" in err and "apps.demo.android" in err and "不是可用的路径" in err
    assert "Traceback" not in err


def test_config_numbers_keep_native_types_and_reasons_are_product_language():
    """按 TOML 原生类型校验（ADR 0053 决策 3）：整数给浮点选项成浮点、自定义校验函数拿到数字本身、整数选项收整数；内建类型失败时
    解释器的英文原文不进消息。"""
    p = m._build_parser()

    def conv(dest, raw):
        return settings.convert_config_value(settings.find_option_action(p, dest), raw, section="common", key=dest.replace("_", "-"), path="x.toml")

    assert conv("grace", 30) == 30.0 and conv("default_job_timeout", 600) == 600.0 and conv("max_concurrency", 3) == 3
    received = []
    recording = SimpleNamespace(type=lambda v: received.append(type(v)) or v, choices=None, option_strings=["--x"], dest="x", nargs=None)
    assert settings.convert_config_value(recording, 30, section="common", key="x", path="x.toml") == 30
    assert settings.convert_config_value(recording, 2.5, section="common", key="x", path="x.toml") == 2.5
    assert received == [int, float]   # 校验函数拿到的是数字本身、不是字符串化再转回
    with pytest.raises(cfgmod.ConfigError) as e:
        conv("max_concurrency", "abc")
    assert "应为整数" in str(e.value) and "invalid literal" not in str(e.value)
    with pytest.raises(cfgmod.ConfigError) as e:
        conv("grace", "x")
    assert "应为数字" in str(e.value) and "could not convert" not in str(e.value)


def test_default_location_absent_is_not_an_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert _plan_json([str(_feature(tmp_path))], capsys)["default_engine"] == "novaact"


# ---- 取值顺序（决策 2）----

def test_flag_beats_config_beats_builtin(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    feat = _feature(tmp_path)
    _toml(tmp_path, "[common]\ndefault-engine = 'midscene'\nassertion-votes = 3\n")
    doc = _plan_json([str(feat)], capsys)
    assert doc["default_engine"] == "midscene" and doc["jobs"][0]["assertion_votes"] == 3
    doc = _plan_json([str(feat), "--default-engine", "novaact", "--assertion-votes", "2"], capsys)
    assert doc["default_engine"] == "novaact" and doc["jobs"][0]["assertion_votes"] == 2


def test_builtin_defaults_fill_after_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parser = m._build_parser()
    args = parser.parse_args(["run", str(_feature(tmp_path))])
    assert settings.apply_project_config(args, parser) is None
    assert (args.default_engine, args.assertion_votes, args.max_concurrency, args.report_dir, args.backend, args.tunnel) == \
        ("novaact", 1, settings.DEFAULT_MAX_CONCURRENCY, "reports", "local", "ngrok")
    assert args.project_config is cfgmod.NO_CONFIG and args.config_values == {}


def test_config_steps_dir_sits_below_env_and_is_relative_to_config_dir(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "proj"; (cfg_dir / "my-steps").mkdir(parents=True)
    env_steps = tmp_path / "env-steps"; env_steps.mkdir()
    _toml(cfg_dir, "[common]\nsteps-dir = 'my-steps'\n")
    monkeypatch.chdir(tmp_path)  # CWD 不是配置文件目录：相对路径仍按配置文件目录解析
    parser = m._build_parser()
    args = parser.parse_args(["plan", str(_feature(tmp_path)), "--config", str(cfg_dir / "gherkai.toml")])
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    assert settings.apply_project_config(args, parser) is None
    assert m._steps_dir_or_error(args) == (str((cfg_dir / "my-steps").resolve()), None)
    monkeypatch.setenv("GHERKAI_STEPS_DIR", str(env_steps))
    assert m._steps_dir_or_error(args) == (str(env_steps.resolve()), None)   # 环境变量胜过配置文件


def test_config_steps_dir_that_is_not_a_directory_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    _toml(tmp_path, "[common]\nsteps-dir = 'missing'\n")
    assert m.main(["plan", str(_feature(tmp_path))]) == 2
    assert "steps-dir" in capsys.readouterr().err


def test_config_prefix_sits_below_env_and_flag(tmp_path, monkeypatch, capsys):
    """[cloud] prefix 经 config 形参进解析链：没有环境变量时生效、AWS_RESOURCE_PREFIX 在时让位、--prefix 最高。"""
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[common]\nbackend = 'cloud'\n[cloud]\nprefix = 'cfg-'\n")
    seen: list = []

    def gate(target):
        seen.append(target.prefix)
        return 2, None

    monkeypatch.setattr(m, "_cloud_skew_gate", gate)
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: "us-east-1")
    monkeypatch.delenv("AWS_RESOURCE_PREFIX", raising=False)
    assert m.main(["status", "r"]) == 2                     # backend 由配置给出 → 走云端
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "env-")
    assert m.main(["status", "r"]) == 2
    assert m.main(["status", "r", "--prefix", "flag-"]) == 2
    assert seen == ["cfg-", "env-", "flag-"]


def test_cloud_section_is_silent_under_local_backend(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[cloud]\nworker-variant = 'with-steps'\nprefix = 'x-'\n")
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_feature(tmp_path)), "--no-report"]) == 0
    assert "不生效" not in capsys.readouterr().err


_GRACE_NOTICE = "[common] grace 本次未生效"


@pytest.mark.parametrize("argv, body, applied, notice", [
    (["run", "F"], "[common]\ngrace = 300\n", 300.0, False),                                     # 本机后端照常生效
    (["run", "F", "--backend", "cloud"], "[common]\ngrace = 300\n", None, False),                # 云端：跳过；run 由入口以退出码 2 结束，不另提示
    (["run", "F"], "[common]\nbackend = 'cloud'\ngrace = 300\n", None, False),                   # 后端由配置给出同样按云端处理
    (["submit", "F", "--backend", "cloud"], "[common]\ngrace = 300\n", None, True),              # submit 没有 --grace，云端照样提示
    (["submit", "F", "--backend", "cloud"], "[common]\ngrace = 'abc'\n", None, True),            # 用不到的值不做校验、不拦
    (["submit", "F"], "[common]\ngrace = 300\n", None, False),                                    # 本机提交：对当前命令不适用，静默忽略
    (["status", "r", "--backend", "cloud"], "[common]\ngrace = 300\n", None, False),             # 只在提交命令上提示
])
def test_config_grace_only_applies_to_local_backend(tmp_path, monkeypatch, capsys, argv, body, applied, notice):
    """[common] grace 只对本机后端起作用：--backend cloud 下配置层跳过、不写进 args、不做校验，submit 上提示一句
    （ADR 0053 决策 3「只对本机后端起作用的 [common] 键」条）；本机后端照常取文件里的值。run 给出云端后端时由入口以退出码 2 结束、
    指向 submit（同决策「[common] 的 backend 设为 cloud 时」条），配置层不为它提示。"""
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, body)
    parser = m._build_parser()
    args = parser.parse_args([str(_feature(tmp_path)) if a == "F" else a for a in argv])
    assert settings.apply_project_config(args, parser) is None
    assert getattr(args, "grace", None) == applied
    assert ("grace" in args.config_filled) is (applied is not None)
    err = capsys.readouterr().err
    assert (_GRACE_NOTICE in err) is notice
    if notice:
        assert "只对本机运行起作用" in err and "gherkai deploy --stop-timeout" in err and str(tmp_path / "gherkai.toml") in err


def test_config_backend_cloud_makes_run_exit_2_and_leaves_cloud_submit_unblocked(tmp_path, monkeypatch, capsys):
    """配置文件 [common] backend 设为 cloud（ADR 0053 决策 3「[common] 的 backend 设为 cloud 时」条；ADR 0016 决策 A）：run 与命令行给出
    --backend cloud 时相同，以退出码 2 结束并指向 submit，说明点名配置文件与键、另说怎样在本机执行；一次云端调用都不发、不落库，
    文件里的 grace 也不为 run 提示。给 --backend local 即照常在本机执行（选项优先于配置文件）。同一份文件下云端 submit 照常提交，
    文件里的 grace 只提示一句、不拦。"""
    from test_backend_cloud import _patch_cloud_handles

    monkeypatch.chdir(tmp_path)
    for var in ("AWS_DDB_TABLE", "AWS_S3_BUCKET", "AWS_RESOURCE_PREFIX"):
        monkeypatch.delenv(var, raising=False)
    cfg = _toml(tmp_path, "[common]\nbackend = 'cloud'\ngrace = 300\n")
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    called = []
    monkeypatch.setattr(m, "schedule", lambda *a, **k: called.append(1))
    feat = str(_feature(tmp_path))
    reports = tmp_path / "reports"
    assert m.main(["run", feat, "--report-dir", str(reports)]) == 2
    err = capsys.readouterr().err
    assert "gherkai run 只在本机执行" in err and "gherkai submit --backend cloud" in err
    assert f"配置文件 {cfg.resolve()} 的 [common] backend" in err and "--backend local" in err
    assert _GRACE_NOTICE not in err
    assert called == [] and record == [] and preflight_calls == [] and not reports.exists()

    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", feat, "--backend", "local", "--report-dir", str(reports), "--quiet"]) == 0
    capsys.readouterr()
    assert m.main(["submit", feat, "--region", "us-east-1"]) == 0   # 后端由同一份配置给出：云端
    err = capsys.readouterr().err
    assert _GRACE_NOTICE in err and "gherkai deploy --stop-timeout" in err


def test_report_dir_relative_to_config_dir_only_for_local_backend(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "proj"; cfg_dir.mkdir()
    _toml(cfg_dir, "[common]\nreport-dir = 'out'\n")
    monkeypatch.chdir(tmp_path)
    parser = m._build_parser()
    cfg = str(cfg_dir / "gherkai.toml")
    local = parser.parse_args(["submit", str(_feature(tmp_path)), "--config", cfg])
    assert settings.apply_project_config(local, parser) is None
    assert local.report_dir == str((cfg_dir / "out").resolve())
    cloud = parser.parse_args(["submit", str(_feature(tmp_path)), "--config", cfg, "--backend", "cloud"])
    assert settings.apply_project_config(cloud, parser) is None
    assert cloud.report_dir == "out"   # 云端是桶内键前缀，原样
    flagged = parser.parse_args(["submit", str(_feature(tmp_path)), "--config", cfg, "--report-dir", "rel"])
    assert settings.apply_project_config(flagged, parser) is None
    assert flagged.report_dir == "rel"  # 选项给的路径仍相对当前目录、不碰


def test_local_run_from_subdir_lands_report_under_config_dir(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "proj"; sub = cfg_dir / "sub"; sub.mkdir(parents=True)
    _toml(cfg_dir, "[common]\nreport-dir = 'out'\n")
    monkeypatch.chdir(sub)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_feature(tmp_path)), "--config", "../gherkai.toml"]) == 0
    assert list((cfg_dir / "out").glob("*/run_meta.json")), "报告应落在配置文件目录下的 out/"
    assert not (sub / "out").exists()


def test_submit_local_hands_the_config_region_to_the_background_advancer(tmp_path, monkeypatch, capsys, inline_children):
    """本机后台推进进程不读配置文件（ADR 0053 决策 1）：提交侧按「选项 > 环境变量 > 配置文件」解析后的 region 经标准输入交给它，
    它装配引擎时用的就是这个值；它的工作目录里另有一份写着别的 region 的配置文件也不影响。"""
    import gherkai_runtime.detached as detached

    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[common]\nregion = 'eu-west-1'\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _toml(elsewhere, "[common]\nregion = 'sa-east-1'\n")
    inline_children.before_child = lambda child: os.chdir(elsewhere)
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    engine_regions: list = []
    monkeypatch.setattr(compose, "build_engines", lambda **kw: engine_regions.append(kw["region"]) or {})  # 不起 worker
    monkeypatch.setattr(detached, "advance_local_run", lambda advancer, meta, **kw: None)

    def region_the_advancer_used() -> str:
        os.chdir(tmp_path)   # 上一次的后台推进进程把工作目录换到了别处
        assert m.main(["submit", str(_feature(tmp_path)), "--report-dir", str(tmp_path / "r")]) == 0, capsys.readouterr().err
        inline_children.children[-1].wait()
        return engine_regions[-1]

    assert region_the_advancer_used() == "eu-west-1"
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    assert region_the_advancer_used() == "ap-south-1"   # 环境变量胜过配置文件
    assert len(engine_regions) == 2


# ---- doctor（决策 1）----

def test_doctor_shows_loaded_config_file_or_none(tmp_path, monkeypatch, capsys):
    _fake_locator(monkeypatch)
    _no_provider(monkeypatch)
    monkeypatch.chdir(tmp_path)
    assert m.main(["doctor", "--json"]) == 0
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert "未使用配置文件" in by[("config", "file")]["detail"] and by[("config", "file")]["required"] is False
    cfg = _toml(tmp_path, "[common]\ndefault-engine = 'novaact'\n")
    assert m.main(["doctor", "--json"]) == 0
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert by[("config", "file")]["detail"] == str(cfg.resolve())


# ---- [devices] / [apps] 的形态（决策 3、6）----

@pytest.mark.parametrize("body, needle", [
    ("[devices.android]\narn = 'arn:x'\nos-version = '14'\n", "只能给一个"),
    ("[devices.android]\nbilling-method = 'METERED'\n", "须给 arn"),
    ("[devices.ios]\nos-version = 18.6\n", "加引号"),
    ("[devices.ios]\nos-version = '18.6-beta'\n", "点分的版本号"),
    ("[devices]\nbilling-method = 'FREE'\n", "METERED 或 UNMETERED"),
    ("[devices]\nacquire-timeout-s = 4000\n", "3600"),
    ("[devices]\nproject-arn = ''\n", "非空文本"),
    ("[devices.windows]\narn = 'x'\n", "[devices]"),
    ("[devices.android]\nmodel = 'pixel'\n", "model"),
    ("[apps.wiki]\nandroid = { file = 'a.apk' }\n", "package"),
    ("[apps.wiki]\nios = { file = 'a.ipa' }\n", "bundle-id"),
    ("[apps.wiki]\nandroid = { package = 'org.x' }\n", "file"),
    ("[apps.wiki]\nwindows = { file = 'a', package = 'b' }\n", "android 与 ios"),
    ("[apps.wiki]\nandroid = { file = 'a.apk', package = 'org.x', extra = 1 }\n", "extra"),
])
def test_devices_and_apps_shape_errors_exit_2(tmp_path, monkeypatch, capsys, body, needle):
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, body)
    assert m.main(["plan", str(_feature(tmp_path))]) == 2
    err = capsys.readouterr().err
    assert "gherkai.toml" in err and needle in err


def test_devices_and_apps_parse_into_typed_config(tmp_path):
    cfg = _toml(tmp_path, (
        "[devices]\nbilling-method = 'METERED'\nacquire-timeout-s = 900\nproject-arn = 'arn:aws:devicefarm:us-west-2:123456789012:project:p'\n"
        "app-bucket = 'my-apps'\n[devices.android]\narn = 'arn:aws:devicefarm:us-west-2::device:d'\nbilling-method = 'UNMETERED'\n"
        "[devices.ios]\nos-version = '18.6'\n[apps.wiki]\nandroid = { file = 'build/app.apk', package = 'org.wikipedia' }\n"
        "ios = { file = 'build/Wikipedia.ipa', bundle-id = 'org.wikimedia.wikipedia' }\n"))
    pc = cfgmod.load_project_config(cfg, common_keys=set(), cloud_keys=set())
    d = pc.devices
    assert (d.billing_method, d.acquire_timeout_s, d.app_bucket) == ("METERED", 900.0, "my-apps")
    assert d.project_arn.endswith(":project:p")
    assert d.platforms["android"] == cfgmod.DevicePlatformConfig(arn="arn:aws:devicefarm:us-west-2::device:d", billing_method="UNMETERED")
    assert d.platforms["ios"] == cfgmod.DevicePlatformConfig(os_version="18.6")
    assert pc.apps["wiki"]["android"].file == (tmp_path / "build" / "app.apk").resolve()   # 相对配置文件目录
    assert pc.app_ids() == {"wiki": {"android": "org.wikipedia", "ios": "org.wikimedia.wikipedia"}}


def test_billing_method_platform_table_then_top_level_then_builtin_default(tmp_path):
    """计费方式的来源顺序（决策 3）：平台子表覆盖 [devices] 顶层，两处都没有给出时取 CLI 的内建缺省。"""
    def load(body):
        return cfgmod.load_project_config(_toml(tmp_path, body), common_keys=set(), cloud_keys=set())

    pc = load("[devices]\nbilling-method = 'UNMETERED'\n[devices.android]\narn = 'arn:aws:devicefarm:us-west-2::device:d'\nbilling-method = 'METERED'\n")
    assert (devsel.billing_method_for("android", pc), devsel.billing_method_for("ios", pc)) == ("METERED", "UNMETERED")
    assert devsel.billing_method_for("android", load("[devices]\nacquire-timeout-s = 900\n")) == cfgmod.DEFAULT_BILLING_METHOD
    assert devsel.billing_method_for("ios", cfgmod.NO_CONFIG) == cfgmod.DEFAULT_BILLING_METHOD


def test_apps_table_reaches_plan_as_alias_to_app_id(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.apk").write_bytes(b"x")   # plan 只核对安装包存在
    _toml(tmp_path, "[apps.wiki]\nandroid = { file = 'app.apk', package = 'org.wikipedia' }\n")
    monkeypatch.setattr(compose, "query_capabilities", _android_caps)
    monkeypatch.setattr(compose, "match_deterministic", _no_match)
    feat = _feature(tmp_path, "@device:android @app:wiki\nFeature: F\n  Scenario: a\n    When \"做事\"\n")
    doc = _plan_json([str(feat)], capsys)
    assert doc["jobs"][0]["target"] == {"device": "android", "ui_kind": "app", "app": {"alias": "wiki", "app_id": "org.wikipedia"}}
    assert m.main(["plan", str(feat)]) == 0
    assert "target=android/app:wiki" in capsys.readouterr().out
    feat2 = _feature(tmp_path, "@device:ios @app:wiki\nFeature: F\n  Scenario: a\n    When \"做事\"\n")
    assert m.main(["plan", str(feat2)]) == 2
    assert "[apps.wiki.ios]" in capsys.readouterr().err   # 别名缺本平台条目：core 的契约错误、指向配置文件


def test_acquire_timeout_from_config_moves_device_default_and_floor(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[devices]\nacquire-timeout-s = 900\n")
    monkeypatch.setattr(compose, "query_capabilities", _android_caps)
    monkeypatch.setattr(compose, "match_deterministic", _no_match)
    feat = _feature(tmp_path, DEVICE_FEATURE)
    assert _plan_json([str(feat)], capsys)["jobs"][0]["timeout_s"] == 1800.0   # 900 + 900
    assert m.main(["plan", str(feat), "--default-job-timeout", "1000"]) == 2
    assert "下限 1080 秒" in capsys.readouterr().err                           # 900 + 180


# ---- 设备选择与设备请求（ADR 0053 决策 4、ADR 0048 决策 3、ADR 0051 决策 2）----

DEV_ARN = "arn:aws:devicefarm:us-west-2::device:D1"
PROJECT_ARN = "arn:aws:devicefarm:us-west-2:111111111111:project:p-1"


def _android_env(monkeypatch):
    monkeypatch.setattr(compose, "query_capabilities", _android_caps)
    monkeypatch.setattr(compose, "match_deterministic", _no_match)
    monkeypatch.delenv("GHERKAI_ANDROID_DEVICE_ARN", raising=False)
    monkeypatch.delenv("GHERKAI_DEVICE_FARM_PROJECT_ARN", raising=False)


def test_device_flags_are_on_run_and_submit_and_only_device_arns_on_plan():
    parser = m._build_parser()
    for name in ("run", "submit"):
        assert set(DEVICE) <= {s for a in settings.subparser(parser, name)._actions for s in a.option_strings}
    plan_flags = {s for a in settings.subparser(parser, "plan")._actions for s in a.option_strings}
    assert {"--android-device-arn", "--ios-device-arn"} <= plan_flags
    assert not ({"--device-farm-project-arn", "--app-bucket"} & plan_flags)   # 对 plan 的输出没有作用、不收


def test_device_selection_precedence_flag_env_config(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    _toml(tmp_path, "[devices.android]\nos-version = '14'\n")
    feat = _feature(tmp_path, DEVICE_FEATURE)
    cfg_path = (tmp_path / "gherkai.toml").resolve()
    assert _plan_json([str(feat)], capsys)["devices"] == {"android": {"os_version": "14", "source": f"配置文件 {cfg_path} 的 [devices.android] os-version"}}
    monkeypatch.setenv("GHERKAI_ANDROID_DEVICE_ARN", DEV_ARN)
    assert _plan_json([str(feat)], capsys)["devices"]["android"] == {"arn": DEV_ARN, "source": "环境变量 GHERKAI_ANDROID_DEVICE_ARN"}
    flag_arn = "arn:aws:devicefarm:us-west-2::device:D2"
    assert _plan_json([str(feat), "--android-device-arn", flag_arn], capsys)["devices"]["android"] == {"arn": flag_arn, "source": "--android-device-arn"}
    assert m.main(["plan", str(feat), "--android-device-arn", flag_arn]) == 0
    assert f"设备 android：{flag_arn}（来自 --android-device-arn）" in capsys.readouterr().out
    monkeypatch.delenv("GHERKAI_ANDROID_DEVICE_ARN", raising=False)
    assert m.main(["plan", str(feat)]) == 0
    assert "按系统版本 14 挑选" in capsys.readouterr().out


def test_os_version_selection_label_always_carries_match_range_and_pinning_hint():
    """plan 不调用 Device Farm、无从判断某个值是否已写全，所以按系统版本挑选的平台一律注明命中范围并提示写全版本号可以固定。"""
    hint = "设备池新增版本时实际分到的版本可能改变，写全版本号可以固定"
    for version in ("18", "18.6.2"):
        label = devsel.selection_label(devsel.DeviceSelection("ios", "配置文件", os_version=version), "ios")
        assert f"命中 {version} 与 {version}.x" in label and hint in label
    assert hint not in devsel.selection_label(devsel.DeviceSelection("ios", "配置文件", arn=DEV_ARN), "ios")


def test_unspecified_device_plan_warns_but_run_and_submit_exit_2_before_any_cloud_call(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    feat = _feature(tmp_path, DEVICE_FEATURE)
    assert m.main(["plan", str(feat), "--json"]) == 0
    cap = capsys.readouterr()
    assert json.loads(cap.out)["devices"] == {"android": None} and "没有指定用哪台设备" in cap.err
    assert m.main(["plan", str(feat)]) == 0
    assert "设备 android：未指定" in capsys.readouterr().out
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(feat), "--no-report"]) == 2
    err = capsys.readouterr().err
    assert "没有指定用哪台设备" in err and "[devices.android]" in err and "--android-device-arn" in err

    def forbidden(*a, **k):
        raise AssertionError("未指定设备应在提交前被拒，不该走到云端解析")

    monkeypatch.setattr(compose, "resolve_cloud_target", forbidden)
    assert m.main(["submit", str(feat), "--backend", "cloud"]) == 2
    assert "没有指定用哪台设备" in capsys.readouterr().err


def test_arn_type_segment_is_checked_and_names_the_pasted_kind(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    feat = _feature(tmp_path, DEVICE_FEATURE)
    assert m.main(["plan", str(feat), "--android-device-arn", PROJECT_ARN]) == 2
    err = capsys.readouterr().err
    assert "项目 ARN、不是设备 ARN" in err and "--android-device-arn" in err
    _toml(tmp_path, f"[devices.android]\narn = '{DEV_ARN}'\n[devices]\nproject-arn = '{DEV_ARN}'\n")
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(feat), "--no-report"]) == 2
    err = capsys.readouterr().err
    assert "项目 ARN 形态不对" in err and "设备 ARN、不是项目 ARN" in err
    assert m.main(["plan", str(feat), "--android-device-arn", "not-an-arn"]) == 2
    assert "设备 ARN 形态不对" in capsys.readouterr().err


def test_local_run_fills_device_request_and_only_warns_on_account_mismatch(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    _toml(tmp_path, (f"[devices]\nproject-arn = '{PROJECT_ARN}'\nacquire-timeout-s = 900\nbilling-method = 'METERED'\n"
                     f"[devices.android]\narn = '{DEV_ARN}'\nbilling-method = 'UNMETERED'\n"))
    feat = _feature(tmp_path, DEVICE_FEATURE)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})
    resolved = []
    real_resolve = devsel.resolve_local_project_arn
    monkeypatch.setattr(devsel, "resolve_local_project_arn", lambda **kw: (resolved.append(1), real_resolve(**kw))[1])
    reports = tmp_path / "r"
    assert m.main(["run", str(feat), "--report-dir", str(reports)]) == 0
    assert "不一致" not in capsys.readouterr().err
    assert len(resolved) == 1   # 项目 ARN 连来源只解析一次、随 Prepared 走（不在账号比对时再解析一遍）
    meta = json.loads(next(reports.glob("*/run_meta.json")).read_text(encoding="utf-8"))
    assert meta["jobs"][0]["device_request"] == {"provider": "aws-device-farm", "billing_method": "UNMETERED", "project_arn": PROJECT_ARN,
                                                 "acquire_timeout_s": 900.0, "device_arn": DEV_ARN}   # 平台子表的计费覆盖顶层；获取预算来自配置
    assert meta["jobs"][0]["timeout_s"] == 1800.0   # 设备缺省墙钟是获取预算 900 秒加 900 秒
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "222222222222", "arn": "x", "region": "us-east-1"})
    assert m.main(["run", str(feat), "--report-dir", str(tmp_path / "r2")]) == 0
    err = capsys.readouterr().err
    assert "111111111111" in err and "222222222222" in err and "不一致" in err   # 警告点名两个账号、不拦
    assert "gherkai.toml" in err and "[devices] project-arn" in err and len(resolved) == 2   # 来源说明来自 Prepared 里那一次解析

    def boom(**kw):
        from botocore.exceptions import NoCredentialsError
        raise NoCredentialsError()

    monkeypatch.setattr(compose, "probe_aws_identity", boom)
    assert m.main(["run", str(feat), "--report-dir", str(tmp_path / "r3")]) == 0
    assert "未能核对" in capsys.readouterr().err


def test_local_device_run_without_project_arn_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    _toml(tmp_path, f"[devices.android]\narn = '{DEV_ARN}'\n")
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_feature(tmp_path, DEVICE_FEATURE)), "--no-report"]) == 2
    err = capsys.readouterr().err
    assert "Device Farm 项目" in err and "project-arn" in err and "--device-farm-project-arn" in err


def test_cloud_submit_reads_project_arn_from_ssm_after_preflight_and_rejects_when_absent(tmp_path, monkeypatch, capsys):
    from test_backend_cloud import _definition, _patch_cloud_handles

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    _toml(tmp_path, f"[devices]\nproject-arn = '{PROJECT_ARN}'\n[devices.android]\narn = '{DEV_ARN}'\n")
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    order: list = []
    monkeypatch.setattr(compose, "preflight_cloud_resources", lambda **kw: (order.append("preflight"), None)[1])
    monkeypatch.setattr(compose, "read_device_farm_project",
                        lambda **kw: (order.append(("ssm", kw["prefix"])), "arn:aws:devicefarm:us-west-2:333333333333:project:cloud")[1])
    feat = _feature(tmp_path, DEVICE_FEATURE)
    assert m.main(["submit", str(feat), "--backend", "cloud", "--region", "us-east-1", "--prefix", "p-"]) == 0
    err = capsys.readouterr().err
    assert "project-arn 不生效" in err   # 配置文件里的项目 ARN 在云端不生效，只提示
    assert order == ["preflight", ("ssm", "p-")]   # SSM 读在资源 preflight 之后
    d = _definition(made["ddb_tables"][0])
    assert d["jobs"][0]["device_request"]["project_arn"].endswith(":project:cloud") and d["jobs"][0]["device_request"]["device_arn"] == DEV_ARN
    tables_before = len(made["ddb_tables"])
    monkeypatch.setattr(compose, "read_device_farm_project", lambda **kw: None)
    assert m.main(["submit", str(feat), "--backend", "cloud", "--region", "us-east-1", "--prefix", "p-"]) == 2
    assert "部署未启用设备支持" in capsys.readouterr().err
    assert len(made["ddb_tables"]) == tables_before   # 没落库


def test_cloud_submit_only_notes_a_malformed_local_project_arn(tmp_path, monkeypatch, capsys):
    """本机给的项目 ARN 在云端只提示、不拦截（ADR 0053 决策 3）：形态不对也不在云端核对、不以退出码 2 结束。"""
    from test_backend_cloud import _patch_cloud_handles

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    _toml(tmp_path, f"[devices.android]\narn = '{DEV_ARN}'\n")
    monkeypatch.setenv("GHERKAI_DEVICE_FARM_PROJECT_ARN", DEV_ARN)   # 贴错类型：本机会拒绝，云端只提示
    _patch_cloud_handles(monkeypatch, [])
    monkeypatch.setattr(compose, "preflight_cloud_resources", lambda **kw: None)
    monkeypatch.setattr(compose, "read_device_farm_project", lambda **kw: "arn:aws:devicefarm:us-west-2:333333333333:project:cloud")
    assert m.main(["submit", str(_feature(tmp_path, DEVICE_FEATURE)), "--backend", "cloud", "--region", "us-east-1", "--prefix", "p-"]) == 0
    assert "project-arn 不生效" in capsys.readouterr().err


# ---- 应用安装包：定位、上传与填位置（ADR 0051 决策 9、ADR 0048 决策 3）----

APP_FEATURE_TWO_SCOPES = ("Feature: F\n  @scope:a @device:android @app:wiki\n  Scenario: a\n    When \"做事\"\n"
                          "  @scope:b @device:android @app:wiki\n  Scenario: b\n    When \"做事\"\n")


class _UploadS3:
    """假 S3 client：对象不存在（404）→ 记录 upload_file 入参；可让首次上传失败。也顶替云端三件套的 client（head_bucket / put_object 空操作）。"""

    def __init__(self, *, upload_error: Exception | None = None):
        self.uploads: list = []
        self._upload_error = upload_error

    def head_bucket(self, **kw):
        return {}

    def put_object(self, **kw):
        return {}

    def head_object(self, **kw):
        from botocore.exceptions import ClientError
        raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}, "ResponseMetadata": {"HTTPStatusCode": 404}}, "HeadObject")

    def upload_file(self, Filename, Bucket, Key, ExtraArgs=None):
        if self._upload_error is not None:
            raise self._upload_error
        self.uploads.append((Filename, Bucket, Key, ExtraArgs))


def _app_project(tmp_path: Path, *, app_bucket: str | None = "my-apps") -> Path:
    (tmp_path / "build").mkdir(exist_ok=True)
    (tmp_path / "build" / "app.apk").write_bytes(b"apk-bytes")
    bucket_line = f"app-bucket = '{app_bucket}'\n" if app_bucket else ""
    _toml(tmp_path, (f"[devices]\nproject-arn = '{PROJECT_ARN}'\n{bucket_line}[devices.android]\narn = '{DEV_ARN}'\n"
                     "[apps.wiki]\nandroid = { file = 'build/app.apk', package = 'org.wikipedia' }\n"))
    return tmp_path / "build" / "app.apk"


def test_local_run_uploads_each_installer_once_and_fills_app_location(tmp_path, monkeypatch, capsys):
    import hashlib

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    apk = _app_project(tmp_path)
    s3 = _UploadS3()
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: s3)
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    reports = tmp_path / "r"
    assert m.main(["run", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--report-dir", str(reports)]) == 0
    sha = hashlib.sha256(b"apk-bytes").hexdigest()
    assert s3.uploads == [(str(apk), "my-apps", f"apps/{sha}/app.apk", None)]   # 两个 scope 同一文件：只传一次、本机桶不打标签
    meta = json.loads(next(reports.glob("*/run_meta.json")).read_text(encoding="utf-8"))
    for job in meta["jobs"]:
        assert job["target"]["app"] == {"alias": "wiki", "app_id": "org.wikipedia", "bucket": "my-apps", "key": f"apps/{sha}/app.apk", "sha256": sha}
    err = capsys.readouterr().err
    assert "已上传到 s3://my-apps/" in err
    # 开场提示按目标说明会建立哪种会话：只有设备 scope 时说远程访问会话、不提云端浏览器
    assert "开始运行：启动 worker 建立Device Farm 远程访问会话（将产生 AWS 费用）" in err
    assert "AgentCore 云端浏览器会话" not in err


@pytest.mark.parametrize("regions", [("eu-west-1", "eu-west-1"), (None, "eu-west-1")],
                         ids=["both-files-see-region", "first-file-region-unknown"])
def test_local_run_notes_once_when_app_bucket_is_in_another_region(tmp_path, monkeypatch, capsys, regions):
    import hashlib

    from gherkai_runtime import app_upload

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    # 第二个别名指向另一个文件：两个文件都走上传分支、落在同一个桶，提示只能出现一次
    (tmp_path / "build" / "app2.apk").write_bytes(b"apk2-bytes")
    _toml(tmp_path, (tmp_path / "gherkai.toml").read_text(encoding="utf-8")
          + "\n[apps.wiki2]\nandroid = { file = 'build/app2.apk', package = 'org.wikipedia' }\n")
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: _UploadS3())
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    calls: list = []

    def ensure(bucket, file, **kw):
        calls.append(file.name)
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        return app_upload.AppLocation(bucket, f"apps/{digest}/{file.name}", digest, uploaded=False, refreshed=False,
                                      bucket_region=regions[len(calls) - 1])

    monkeypatch.setattr(app_upload, "ensure_app_object", ensure)
    feature = APP_FEATURE_TWO_SCOPES.replace("@scope:b @device:android @app:wiki", "@scope:b @device:android @app:wiki2")
    # 区域显式给出：提示比较的是解析出的区域配置，不让宿主的 AWS_REGION 决定用例结果
    assert m.main(["run", str(_feature(tmp_path, feature)), "--region", "us-east-1", "--report-dir", str(tmp_path / "r")]) == 0
    assert calls == ["app.apk", "app2.apk"]
    err = capsys.readouterr().err
    assert "注意：应用桶 my-apps 在 eu-west-1，当前区域配置为 us-east-1" in err
    # 两个文件同一个桶：只提示一次；第一个文件没查到桶所在区域时，由第二个文件提示
    assert err.count("注意：应用桶") == 1


def test_missing_installer_exits_2_in_plan_and_run(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    _app_project(tmp_path)
    (tmp_path / "build" / "app.apk").unlink()
    feat = _feature(tmp_path, APP_FEATURE_TWO_SCOPES)
    assert m.main(["plan", str(feat)]) == 2
    assert "安装包不存在" in capsys.readouterr().err
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(feat), "--no-report"]) == 2
    assert "[apps.wiki.android]" in capsys.readouterr().err


def test_local_app_run_without_bucket_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path, app_bucket=None)
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--no-report"]) == 2
    err = capsys.readouterr().err
    assert "app-bucket" in err and "--app-bucket" in err and "GHERKAI_APP_BUCKET" in err


def test_local_app_bucket_and_project_arn_sources_follow_flag_env_config_order():
    """应用桶与项目 ARN 的三处来源（ADR 0053 决策 2、3）：选项 > 环境变量 > 配置文件，空串视同没有给、继续取下一处；
    云端用的「是否给了项目 ARN」只看有没有值，形态不对也不抛。"""
    cfg = cfgmod.ProjectConfig(devices=cfgmod.DevicesConfig(app_bucket="cfg-apps", project_arn="not-an-arn"))
    env = {devsel.APP_BUCKET_ENV: "env-apps"}
    assert devsel.resolve_local_app_bucket(flag="flag-apps", env=env, config=cfg) == "flag-apps"
    assert devsel.resolve_local_app_bucket(flag="", env=env, config=cfg) == "env-apps"
    assert devsel.resolve_local_app_bucket(flag=None, env={devsel.APP_BUCKET_ENV: ""}, config=cfg) == "cfg-apps"
    empty = cfgmod.ProjectConfig(devices=cfgmod.DevicesConfig(app_bucket=""))
    assert devsel.resolve_local_app_bucket(flag="", env={devsel.APP_BUCKET_ENV: ""}, config=empty) is None
    assert devsel.resolve_local_app_bucket(flag=None, env={}, config=cfgmod.NO_CONFIG) is None
    assert devsel.local_project_arn_given(flag_arn=None, env={}, config=cfg)   # 形态不对也算给了
    assert devsel.local_project_arn_given(flag_arn="", env={devsel.PROJECT_ARN_ENV: "x"}, config=cfgmod.NO_CONFIG)
    assert not devsel.local_project_arn_given(flag_arn="", env={devsel.PROJECT_ARN_ENV: ""}, config=empty)


def test_cloud_submit_puts_installer_in_artifacts_bucket_with_tag(tmp_path, monkeypatch, capsys):
    import hashlib

    from test_backend_cloud import _definition, _patch_cloud_handles

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)   # 配置里的 app-bucket 在云端不生效
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    s3 = _UploadS3()
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: s3)
    monkeypatch.setattr(compose, "read_device_farm_project", lambda **kw: "arn:aws:devicefarm:us-west-2:333333333333:project:cloud")
    assert m.main(["submit", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--backend", "cloud", "--region", "us-east-1", "--prefix", "p-"]) == 0
    err = capsys.readouterr().err
    assert "app-bucket 不生效" in err
    sha = hashlib.sha256(b"apk-bytes").hexdigest()
    assert len(s3.uploads) == 1 and s3.uploads[0][1:] == ("p-artifacts", f"apps/{sha}/app.apk", {"Tagging": "gherkai=app"})
    d = _definition(made["ddb_tables"][0])
    assert d["jobs"][0]["target"]["app"]["bucket"] == "p-artifacts" and d["jobs"][0]["target"]["app"]["sha256"] == sha


# ---- 复核处置：配置层对没有对应选项的命令同样生效、doctor 只给 --prefix、消息按来源指路、次序 ----

def test_cloud_resource_names_from_config_reach_commands_without_the_flag(tmp_path, monkeypatch):
    """[cloud] ddb-table / s3-bucket 与 [common] region / profile 对没有对应选项的命令同样生效（explain 没有 --s3-bucket、doctor 两个
    资源名选项都没有）：同一份文件不能让 submit 写一个桶、explain 去另一个桶读。"""
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[common]\nbackend = 'cloud'\nregion = 'eu-west-1'\nprofile = 'team'\n[cloud]\nprefix = 'p-'\nddb-table = 'team-runs'\ns3-bucket = 'team-artifacts'\n")
    for v in ("AWS_RESOURCE_PREFIX", "AWS_DDB_TABLE", "AWS_S3_BUCKET", "AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: r or kw.get("config_region"))  # 不摸 profile config
    seen: list = []

    def gate(target, **kw):
        seen.append((target.prefix, target.runs_table, target.bucket, target.region, target.profile))
        return 2, None

    monkeypatch.setattr(m, "_cloud_skew_gate", gate)
    assert m.main(["status", "r"]) == 2
    assert m.main(["explain", "r"]) == 2
    assert seen == [("p-", "team-runs", "team-artifacts", "eu-west-1", "team")] * 2
    captured: dict = {}

    def spy(**kw):
        captured.update(kw)
        raise RuntimeError("stop here")

    monkeypatch.setattr(compose, "resolve_cloud_target", spy)
    _fake_locator(monkeypatch)
    _no_provider(monkeypatch)
    assert m.main(["doctor", "--json", "--prefix", "stage-"]) == 2
    assert (captured["config_runs_table"], captured["config_bucket"], captured["config_region"], captured["config_profile"]) == \
        ("team-runs", "team-artifacts", "eu-west-1", "team")


def test_doctor_with_prefix_only_treats_report_dir_as_key_prefix_and_applies_cloud_section(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[common]\nreport-dir = 'reports'\n[cloud]\nprefix = 'p-'\n")
    parser = m._build_parser()
    args = parser.parse_args(["doctor", "--prefix", "stage-"])
    assert settings.apply_project_config(args, parser) is None
    assert args.report_dir == "reports" and args.config_values.get("prefix") == "p-"   # 云端：键前缀原样；[cloud] 生效（选项 prefix 在解析链里更高）
    local = parser.parse_args(["doctor"])
    assert settings.apply_project_config(local, parser) is None
    assert local.report_dir == str((tmp_path / "reports").resolve()) and "prefix" not in local.config_values


def test_invalid_values_from_config_are_reported_with_the_config_source(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    feat = _feature(tmp_path)
    _toml(tmp_path, "[common]\nassertion-votes = 0\n")
    assert m.main(["plan", str(feat)]) == 2
    err = capsys.readouterr().err
    assert "[common] assertion-votes" in err and "gherkai.toml" in err
    _toml(tmp_path, "[common]\nmax-concurrency = 0\n")
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(feat), "--no-report"]) == 2
    assert "[common] max-concurrency" in capsys.readouterr().err
    assert m.main(["plan", str(feat), "--assertion-votes", "0"]) == 2
    assert "--assertion-votes 必须" in capsys.readouterr().err   # 选项给的仍点名选项


def test_config_sourced_arn_errors_name_the_config_file(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    cfg = _toml(tmp_path, f"[devices.android]\narn = '{PROJECT_ARN}'\n")
    assert m.main(["plan", str(_feature(tmp_path, DEVICE_FEATURE))]) == 2
    err = capsys.readouterr().err
    assert str(cfg.resolve()) in err and "[devices.android]" in err and "项目 ARN、不是设备 ARN" in err


def test_arn_check_only_looks_at_service_and_resource_type_segments(tmp_path, monkeypatch, capsys):
    """只核服务与资源类型段：分区、区域、账号与资源 id 的形态不管（ADR 0053 决策 4）。"""
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    odd = "arn:aws-cn:devicefarm:cn-north-1:123:device:anything-goes"
    assert _plan_json([str(_feature(tmp_path, DEVICE_FEATURE)), "--android-device-arn", odd], capsys)["devices"]["android"]["arn"] == odd


def test_invalid_grace_or_failed_engine_self_description_is_rejected_before_any_aws_call(tmp_path, monkeypatch, capsys):
    """本机后端的账号比对（STS）与安装包上传排在 run 的 --grace 校验、submit 向引擎问停止宽限之后：配置错或引擎自述失败的 run 不该
    先上传再被拒，submit 也不启动后台推进进程。"""
    import subprocess

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    s3 = _UploadS3()
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: s3)

    sts_calls = []
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: sts_calls.append(1))  # 记次数：抛 AssertionError 会被当成「核对失败」吞掉
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: (_ for _ in ()).throw(AssertionError("不该启动后台推进进程")))
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _feature(tmp_path, APP_FEATURE_TWO_SCOPES)
    assert m.main(["run", str(feat), "--no-report", "--grace", "0"]) == 2
    assert "--grace" in capsys.readouterr().err and s3.uploads == [] and sts_calls == []

    def self_description_fails(engine):
        raise RuntimeError("worker 没有在时限内答出能力自述")

    monkeypatch.setattr(compose, "engine_min_grace", self_description_fails)
    assert m.main(["submit", str(feat), "--report-dir", str(tmp_path / "r")]) == 2
    err = capsys.readouterr().err
    assert "引擎 novaact 的 worker 自述失败，拒绝提交：worker 没有在时限内答出能力自述" in err
    assert s3.uploads == [] and sts_calls == [] and not (tmp_path / "r").exists()


def test_first_upload_failure_exits_2_with_product_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: _UploadS3(upload_error=RuntimeError("S3UploadFailedError: NoSuchBucket")))
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--no-report"]) == 2
    err = capsys.readouterr().err
    assert "上传安装包" in err and "失败" in err and "NoSuchBucket" in err and "Traceback" not in err


def _app_run_with_another_project_elsewhere(tmp_path: Path, monkeypatch) -> tuple[Path, Path, list]:
    """带设备与应用的 run 的提交环境，外加另一个目录：那里的 gherkai.toml 给出别的项目 ARN、设备选择、应用桶与安装包。后台推进进程的
    推进换成记录它收到的运行定义的函数，不起 worker。返回 (报告目录, 另一个目录, 推进收到的运行定义)。"""
    import gherkai_runtime.detached as detached

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: _UploadS3())
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})
    monkeypatch.setattr(compose, "build_engines", lambda **kw: {})  # 不起 worker
    advanced: list = []
    monkeypatch.setattr(detached, "advance_local_run", lambda advancer, meta, **kw: advanced.append(meta))
    other = tmp_path / "elsewhere"
    (other / "build").mkdir(parents=True)
    (other / "build" / "other.apk").write_bytes(b"other-apk-bytes")
    _toml(other, ("[devices]\nproject-arn = 'arn:aws:devicefarm:us-west-2:999999999999:project:other'\n"
                  "app-bucket = 'other-apps'\n[devices.android]\nos-version = '99'\n"
                  "[apps.wiki]\nandroid = { file = 'build/other.apk', package = 'org.other' }\n"))
    return tmp_path / "r", other, advanced


def _assert_submitted_device_and_app_values(meta) -> None:
    for job in meta.jobs:
        assert job.device_request.project_arn == PROJECT_ARN and job.device_request.device_arn == DEV_ARN
        assert job.target.app.bucket == "my-apps" and job.target.app.app_id == "org.wikipedia"


def test_local_background_advancer_uses_the_handed_over_device_and_app_values(tmp_path, monkeypatch, capsys,
                                                                              inline_children):
    """本机后台推进进程不读配置文件（ADR 0053 决策 1、决策 6 的护栏）：它在另一个工作目录（那里的 gherkai.toml 写着别的项目 ARN、
    设备与应用）里建 run，写下的运行定义与推进用的那一份里的设备与应用值仍是提交时解析、经标准输入交来的。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    reports, other, advanced = _app_run_with_another_project_elsewhere(tmp_path, monkeypatch)
    inline_children.before_child = lambda child: os.chdir(other)
    assert m.main(["submit", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--report-dir", str(reports)]) == 0, \
        capsys.readouterr().err
    inline_children.settle()
    run_id = capsys.readouterr().out.strip()
    assert Path.cwd() == other.resolve()   # 后台推进进程确实在另一个目录里建的 run
    written = LocalRunStore(reports).load_run_meta(run_id)
    _assert_submitted_device_and_app_values(written)
    assert advanced == [written]


def test_cloud_tunnel_daemon_reads_the_run_with_the_values_submit_resolved(tmp_path, monkeypatch, capsys,
                                                                           inline_children):
    """云端的隧道守护进程同样不读配置文件（ADR 0053 决策 1）：配置文件给的 runs 表、region 与 profile 由 submit 解析后经标准输入交来；
    守护进程在另一个工作目录（那里的 gherkai.toml 写着别的值）里照这三个值打开 runs 表、读这个 run 的状态，读到终态即关闭会话。"""
    import threading

    from test_backend_cloud import ORIGIN, _install_fake_tunnel, _patch_cloud_handles

    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[common]\nregion = 'eu-west-1'\nprofile = 'team'\n[cloud]\nddb-table = 'team-runs'\n")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _toml(elsewhere, "[common]\nregion = 'sa-east-1'\nprofile = 'other'\n[cloud]\nddb-table = 'other-runs'\n")
    for v in ("AWS_RESOURCE_PREFIX", "AWS_DDB_TABLE", "AWS_S3_BUCKET", "AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE"):
        monkeypatch.delenv(v, raising=False)
    _patch_cloud_handles(monkeypatch, [])
    service = _install_fake_tunnel(monkeypatch)
    opened_by_daemon: list = []
    submit_side_make = compose._make_ddb_table

    def make(table, *, region, profile, config=None):
        t = submit_side_make(table, region=region, profile=profile)
        if threading.current_thread() is not threading.main_thread():   # 守护进程那一侧：这个 run 已经 passed
            opened_by_daemon.append((table, region, profile))
            t.get_item = lambda **kw: {"Item": {"run_id": kw["Key"]["run_id"], "item_type": "STATE", "status": "passed",
                                                "jobs": {}}}
        return t

    monkeypatch.setattr(compose, "_make_ddb_table", make)
    inline_children.watch_kwargs = {"poll_interval_s": 0.05}   # 不注入存储：守护进程按交来的值自己打开 runs 表
    inline_children.before_child = lambda child: os.chdir(elsewhere)
    assert m.main(["submit", str(_feature(tmp_path)), "--backend", "cloud", "--expose-local", ORIGIN]) == 0, \
        capsys.readouterr().err
    inline_children.settle()
    run_id = capsys.readouterr().out.strip()
    assert opened_by_daemon == [("team-runs", "eu-west-1", "team")]
    child = inline_children.only()
    assert child.notes[-1] == f"run {run_id} 已结束（passed），隧道已关闭"
    assert child.returncode == 0 and service.closed


def test_local_relay_host_reads_definition_not_the_config_file(tmp_path, monkeypatch, capsys, inline_children):
    """提交后换到带另一份 gherkai.toml 的目录，接力宿主从 definition 读回的设备与应用值仍是提交时的；
    宿主代码结构上也不引用 CLI 的配置模块。"""
    import inspect

    import gherkai_runtime.detached as detached

    reports, other, _advanced = _app_run_with_another_project_elsewhere(tmp_path, monkeypatch)
    assert m.main(["submit", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--report-dir", str(reports)]) == 0, \
        capsys.readouterr().err
    inline_children.settle()
    run_id = capsys.readouterr().out.strip()
    monkeypatch.chdir(other)
    _assert_submitted_device_and_app_values(detached.build_local_reconcile(str(reports), run_id, 1)[0])
    assert "gherkai_cli" not in inspect.getsource(detached)


def test_account_check_only_swallows_credential_and_network_failures(monkeypatch, capsys):
    """账号比对是辅助提示（ADR 0053 决策 3）：凭证 / 网络类失败（botocore）只提示一句、继续；别的异常是程序错误，原样上抛、不吞。"""
    from botocore.exceptions import NoCredentialsError

    from gherkai_cli import submission

    args = SimpleNamespace(region="us-east-1", profile=None, project_config=cfgmod.NO_CONFIG)

    def raise_(exc):
        def _f(**kw):
            raise exc
        return _f

    monkeypatch.setattr(compose, "probe_aws_identity", raise_(NoCredentialsError()))
    submission.warn_project_account(args, PROJECT_ARN, "x")
    assert "未能核对" in capsys.readouterr().err
    monkeypatch.setattr(compose, "probe_aws_identity", raise_(RuntimeError("bug")))
    with pytest.raises(RuntimeError):
        submission.warn_project_account(args, PROJECT_ARN, "x")
