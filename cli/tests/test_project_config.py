"""项目配置文件 gherkai.toml（ADR 0053）的护栏：键集差集、定位、取值顺序（含「配置不越过环境变量」）、错误形态、
设备段与应用段的形态、路径基准、doctor 的配置文件行。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_cli import config as cfgmod
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
    for name in m._CONFIG_COMMANDS:
        flags = {s for a in m._subparser(parser, name)._actions for s in a.option_strings if s.startswith("--")} - {"--help"}
        unclassified = flags - PER_CALL - COMMON - CLOUD - set(DEVICE)
        assert not unclassified, f"{name} 的选项 {sorted(unclassified)} 没归入按次选择型 / [common] / [cloud] / 设备映射表任一类"
    keys = m._configurable_keys(parser)
    assert keys["common"] == {f[2:] for f in COMMON}
    assert keys["cloud"] == {f[2:] for f in CLOUD}
    assert {f[2:].replace("-", "_") for f in DEVICE} == set(m._DEVICE_OPTIONS)
    assert {"--" + d.replace("_", "-"): v for d, v in m._DEVICE_OPTIONS.items()} == DEVICE
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
])
def test_config_errors_exit_2_naming_file_section_and_key(tmp_path, monkeypatch, capsys, body, needle):
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, body)
    assert m.main(["submit", str(_feature(tmp_path)), "--backend", "cloud"]) == 2
    err = capsys.readouterr().err
    assert "gherkai.toml" in err and needle in err


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
    assert m._apply_project_config(args, parser) is None
    assert (args.default_engine, args.assertion_votes, args.max_concurrency, args.report_dir, args.backend, args.tunnel) == \
        ("novaact", 1, m.DEFAULT_MAX_CONCURRENCY, "reports", "local", "ngrok")
    assert args.project_config is cfgmod.NO_CONFIG and args.config_values == {}


def test_config_steps_dir_sits_below_env_and_is_relative_to_config_dir(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "proj"; (cfg_dir / "my-steps").mkdir(parents=True)
    env_steps = tmp_path / "env-steps"; env_steps.mkdir()
    _toml(cfg_dir, "[common]\nsteps-dir = 'my-steps'\n")
    monkeypatch.chdir(tmp_path)  # CWD 不是配置文件目录：相对路径仍按配置文件目录解析
    parser = m._build_parser()
    args = parser.parse_args(["plan", str(_feature(tmp_path)), "--config", str(cfg_dir / "gherkai.toml")])
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    assert m._apply_project_config(args, parser) is None
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


def test_report_dir_relative_to_config_dir_only_for_local_backend(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "proj"; cfg_dir.mkdir()
    _toml(cfg_dir, "[common]\nreport-dir = 'out'\n")
    monkeypatch.chdir(tmp_path)
    parser = m._build_parser()
    cfg = str(cfg_dir / "gherkai.toml")
    local = parser.parse_args(["submit", str(_feature(tmp_path)), "--config", cfg])
    assert m._apply_project_config(local, parser) is None
    assert local.report_dir == str((cfg_dir / "out").resolve())
    cloud = parser.parse_args(["submit", str(_feature(tmp_path)), "--config", cfg, "--backend", "cloud"])
    assert m._apply_project_config(cloud, parser) is None
    assert cloud.report_dir == "out"   # 云端是桶内键前缀，原样
    flagged = parser.parse_args(["submit", str(_feature(tmp_path)), "--config", cfg, "--report-dir", "rel"])
    assert m._apply_project_config(flagged, parser) is None
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
