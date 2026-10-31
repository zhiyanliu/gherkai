"""项目配置文件 gherkai.toml（ADR 0053）的护栏：键集差集、定位、取值顺序（含「配置不越过环境变量」）、错误形态、
设备段与应用段的形态、路径基准、doctor 的配置文件行。"""
from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_cli import config as cfgmod
from gherkai_cli import settings
from gherkai_cli import device_selection as devsel
from gherkai_runtime import compose

from test_main import _fake_locator, _fake_schedule_factory, _no_provider

FEATURE = 'Feature: F\n  Scenario: a\n    When "做事"\n'
DEVICE_FEATURE = '@device:android\nFeature: F\n  Scenario: a\n    When "做事"\n'

# ADR 0053 决策 3 的三份名单，在测试里显式列出：新增选项必须有意识地归入其中一类（决策 6「键集差集」）
PER_CALL = {"--scope", "--tags", "--scenario", "--step", "--json", "--quiet", "--wait", "--all", "--full",
            "--fail-fast", "--no-report", "--engine", "--config"}
COMMON = {"--default-engine", "--assertion-votes", "--max-concurrency", "--default-job-timeout", "--grace", "--expose-local",
          "--tunnel", "--tunnel-ttl", "--report-dir", "--steps-dir", "--backend", "--region", "--profile"}
CLOUD = {"--prefix", "--ddb-table", "--s3-bucket", "--events-table", "--cluster", "--subnet", "--security-group", "--worker-variant"}
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
    return {"schema_version": 1, "engine": engine, "min_grace_s": 150.0, "deterministic_steps": [], "model_id": "m",
            "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8000.0}]}


def _no_match(*a, **k):
    raise RuntimeError("查询失败")


# ---- 键集差集（ADR 0053 决策 6）----

def test_every_long_option_is_classified_and_the_derived_key_sets_match():
    """七个读配置命令的每个长选项都落在四份名单之一；由 argparse 推出的 [common] / [cloud] 接受集恰等于名单（多一键或少一键都红）。"""
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
    ("[common]\ntunnel-ttl = 'x'\n", "应为数字"),
])
def test_config_errors_exit_2_naming_file_section_and_key(tmp_path, monkeypatch, capsys, body, needle):
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, body)
    assert m.main(["submit", str(_feature(tmp_path)), "--backend", "cloud"]) == 2
    err = capsys.readouterr().err
    assert "gherkai.toml" in err and needle in err


def test_config_numbers_keep_native_types_and_reasons_are_product_language():
    """按 TOML 原生类型校验（ADR 0053 决策 3）：整数给浮点选项成浮点、自定义校验函数拿到数字本身、整数选项收整数；内建类型失败时
    解释器的英文原文不进消息。"""
    p = m._build_parser()

    def conv(dest, raw):
        return settings.convert_config_value(settings.find_option_action(p, dest), raw, section="common", key=dest.replace("_", "-"), path="x.toml")

    assert conv("tunnel_ttl", 30) == 30.0 and conv("default_job_timeout", 600) == 600.0 and conv("max_concurrency", 3) == 3
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
    (["run", "F", "--backend", "cloud"], "[common]\ngrace = 300\n", None, True),                 # 云端：跳过、只提示
    (["run", "F"], "[common]\nbackend = 'cloud'\ngrace = 300\n", None, True),                    # 后端由配置给出同样按云端处理
    (["run", "F", "--backend", "cloud"], "[common]\ngrace = 'abc'\n", None, True),               # 用不到的值不做校验、不拦
    (["submit", "F", "--backend", "cloud"], "[common]\ngrace = 300\n", None, True),              # submit 没有 --grace，云端照样提示
    (["submit", "F"], "[common]\ngrace = 300\n", None, False),                                    # 本机提交：对当前命令不适用，静默忽略
    (["status", "r", "--backend", "cloud"], "[common]\ngrace = 300\n", None, False),             # 只在运行与提交两个命令上提示
])
def test_config_grace_only_applies_to_local_backend(tmp_path, monkeypatch, capsys, argv, body, applied, notice):
    """[common] grace 只对本机后端起作用（ADR 0053 决策 3）：--backend cloud 下配置层跳过、不写进 args，run / submit 上提示一句，
    不以退出码 2 结束；本机后端照常取文件里的值。"""
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


def test_config_grace_does_not_block_cloud_run_or_submit(tmp_path, monkeypatch, capsys):
    """配置了 [common] grace 又给 --backend cloud：run 与 submit 都照常完成（退出码不是 2），开始前各打一行提示；run 的停止宽限
    回落内建默认，文件里的值不进入 grace 校验。命令行上显式给 --grace 仍以退出码 2 结束，见 test_backend_cloud。"""
    from test_backend_cloud import _patch_cloud_handles

    monkeypatch.chdir(tmp_path)
    for var in ("AWS_DDB_TABLE", "AWS_S3_BUCKET", "AWS_RESOURCE_PREFIX"):
        monkeypatch.delenv(var, raising=False)
    _toml(tmp_path, "[common]\ngrace = 300\n")
    _patch_cloud_handles(monkeypatch, [])
    box, inner = {}, _fake_schedule_factory()

    def capturing(run_meta, engines, sink, opts=None, **kw):
        box["opts"] = opts
        return inner(run_meta, engines, sink, opts=opts, **kw)

    monkeypatch.setattr(m, "schedule", capturing)
    feat = str(_feature(tmp_path))
    assert m.main(["run", feat, "--backend", "cloud", "--region", "us-east-1", "--quiet"]) == 0
    err = capsys.readouterr().err
    assert _GRACE_NOTICE in err and "gherkai deploy --stop-timeout" in err
    assert "--grace 在云端不生效" not in err   # 不是对命令行选项的拒绝
    assert box["opts"].grace_period_s == m.ScheduleOpts.grace_period_s and box["opts"].min_grace_s == 0.0
    assert m.main(["submit", feat, "--backend", "cloud", "--region", "us-east-1"]) == 0
    assert _GRACE_NOTICE in capsys.readouterr().err


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


def test_submit_local_passes_config_region_to_per_run_process(tmp_path, monkeypatch):
    """per-run 进程不读配置文件：提交侧按「选项 > 环境变量 > 配置文件」解析后的 region 经 argv 传给它。"""
    import subprocess

    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[common]\nregion = 'eu-west-1'\n")
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    forked: list = []

    class _P:
        pid = 1

    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd) or _P())
    assert m.main(["submit", str(_feature(tmp_path)), "--report-dir", str(tmp_path / "r")]) == 0
    argv = forked[0]
    assert argv[argv.index("--region") + 1] == "eu-west-1"
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    assert m.main(["submit", str(_feature(tmp_path)), "--report-dir", str(tmp_path / "r")]) == 0
    argv = forked[1]
    assert argv[argv.index("--region") + 1] == "ap-south-1"   # 环境变量胜过配置文件


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
    assert "已上传到 s3://my-apps/" in capsys.readouterr().err


def test_local_run_notes_once_when_app_bucket_is_in_another_region(tmp_path, monkeypatch, capsys):
    import hashlib

    from gherkai_runtime import app_upload

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: _UploadS3())
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    sha = hashlib.sha256(b"apk-bytes").hexdigest()
    monkeypatch.setattr(app_upload, "ensure_app_object", lambda bucket, file, **kw: app_upload.AppLocation(
        bucket, f"apps/{sha}/app.apk", sha, uploaded=False, refreshed=False, bucket_region="eu-west-1"))
    assert m.main(["run", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--report-dir", str(tmp_path / "r")]) == 0
    err = capsys.readouterr().err
    assert "注意：应用桶 my-apps 在 eu-west-1，当前区域配置为 " in err
    assert err.count("注意：应用桶") == 1   # 两个 scope 同一个桶：只提示一次


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


def test_invalid_grace_or_ttl_is_rejected_before_any_aws_call(tmp_path, monkeypatch, capsys):
    """本机后端的账号比对（STS）与安装包上传排在 run 的 --grace、submit 的 --tunnel-ttl 校验之后：配置错的 run 不该先上传再被拒。"""
    import subprocess

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    s3 = _UploadS3()
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: s3)

    sts_calls = []
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: sts_calls.append(1))  # 记次数：抛 AssertionError 会被当成「核对失败」吞掉
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: (_ for _ in ()).throw(AssertionError("不该走到 fork")))
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _feature(tmp_path, APP_FEATURE_TWO_SCOPES)
    assert m.main(["run", str(feat), "--no-report", "--grace", "0"]) == 2
    assert "--grace" in capsys.readouterr().err and s3.uploads == [] and sts_calls == []
    assert m.main(["submit", str(feat), "--report-dir", str(tmp_path / "r"), "--tunnel-ttl", "0"]) == 2
    assert "--tunnel-ttl" in capsys.readouterr().err and s3.uploads == [] and sts_calls == []


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


def test_cloud_run_uploads_installer_into_artifacts_bucket(tmp_path, monkeypatch, capsys):
    from test_backend_cloud import _patch_cloud_handles

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    s3 = _UploadS3()
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: s3)
    monkeypatch.setattr(compose, "read_device_farm_project", lambda **kw: "arn:aws:devicefarm:us-west-2:333333333333:project:cloud")
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--backend", "cloud", "--region", "us-east-1", "--prefix", "p-",
                   "--quiet", "--no-report"]) == 0
    assert len(s3.uploads) == 1 and s3.uploads[0][1] == "p-artifacts" and s3.uploads[0][3] == {"Tagging": "gherkai=app"}


def test_local_relay_host_reads_definition_not_the_config_file(tmp_path, monkeypatch):
    """ADR 0053 决策 6「宿主不读文件」：提交后换到带另一份 gherkai.toml 的目录，接力宿主从 definition 读回的设备与应用值仍是提交时的；
    宿主代码结构上也不引用 CLI 的配置模块。"""
    import inspect
    import subprocess

    import gherkai_runtime.detached as detached

    monkeypatch.chdir(tmp_path)
    _android_env(monkeypatch)
    monkeypatch.delenv("GHERKAI_APP_BUCKET", raising=False)
    _app_project(tmp_path)
    s3 = _UploadS3()
    monkeypatch.setattr(compose, "_make_s3_client", lambda *, region, profile: s3)
    monkeypatch.setattr(compose, "probe_aws_identity", lambda **kw: {"account": "111111111111", "arn": "x", "region": "us-east-1"})

    class _P:
        pid = 1

    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: _P())
    reports = tmp_path / "r"
    assert m.main(["submit", str(_feature(tmp_path, APP_FEATURE_TWO_SCOPES)), "--report-dir", str(reports)]) == 0
    run_id = next(d for d in reports.iterdir() if d.is_dir()).name
    other = tmp_path / "elsewhere"
    other.mkdir()
    _toml(other, "[devices]\nproject-arn = 'arn:aws:devicefarm:us-west-2:999999999999:project:other'\n[devices.android]\nos-version = '99'\n")
    monkeypatch.chdir(other)
    monkeypatch.setattr(compose, "build_engines", lambda **kw: {})  # 不起 worker
    meta = detached.build_local_reconcile(str(reports), run_id, 1)[0]
    for job in meta.jobs:
        assert job.device_request.project_arn == PROJECT_ARN and job.device_request.device_arn == DEV_ARN
        assert job.target.app.bucket == "my-apps"
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
