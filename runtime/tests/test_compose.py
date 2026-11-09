"""compose（组合根逻辑）单测：不起任何子进程、零费用。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from gherkai_runtime import compose
from gherkai_runtime import names
from gherkai_core.scope import FeatureSource


# dev 环境里 midscene 恒走定位链第一级（env 覆写）——它没有已安装的 npm 包、也没有 PATH 上的 bin
# （ADR 0037 决策 3「contributor 代价点」）。build_engines 的 env 注入类断言要两个引擎项都是真 SubprocessEngine，
# 故这些用例统一用本 fixture 给 midscene 一个假 cmd（不 spawn，只查接线）。
@pytest.fixture
def midscene_env_cmd(monkeypatch):
    monkeypatch.setenv("GHERKAI_WORKER_MIDSCENE_CMD", "node /fake/midscene-worker.mjs")
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CWD", raising=False)
    return "node /fake/midscene-worker.mjs"


# ---- worker 定位链（ADR 0037 决策 3）：四级顺序 + miss 语义 ----

def test_chain_level1_env_cmd_wins_with_optional_cwd(monkeypatch):
    """第一级 env 覆写最高优先（shlex 拆分）+ 可选配套 _CWD：contributor 指向 repo 内源码/自建 worker 走这里。"""
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CMD", "python -m my.worker --flag 'a b'")
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CWD", "/tmp/somewhere")
    wc = compose.resolve_worker_cmd("novaact")
    assert wc.cmd == ["python", "-m", "my.worker", "--flag", "a b"]  # shlex：带引号的整体是一个 arg
    assert wc.cwd == "/tmp/somewhere"
    assert "GHERKAI_WORKER_NOVAACT_CMD" in wc.source


def test_chain_level1_env_cmd_without_cwd_gives_none(monkeypatch):
    # _CWD 是**可选**配套：不给则 cwd 为 None，即继承调用者 CWD（worker 不再有专属 cwd）
    monkeypatch.setenv("GHERKAI_WORKER_MIDSCENE_CMD", "node worker.mjs")
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CWD", raising=False)
    assert compose.resolve_worker_cmd("midscene").cwd is None


def test_chain_level1_blank_env_falls_through(monkeypatch):
    # 空/纯空白的 env 值不算覆写（shlex 拆出空表）——否则 `export ...CMD=` 会把定位链整条掐死、只报 miss
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CMD", "   ")
    wc = compose.resolve_worker_cmd("novaact")
    assert wc.cmd == [sys.executable, "-m", "gherkai_worker_novaact"]  # 落到第二级


def test_chain_level1_unparsable_env_fails_loud(monkeypatch):
    """第一级 env 值 shlex 解析不了（引号不配对）→ **不静默落下一级**，报 miss 并点名该 env。

    悄悄换用别的 worker（或报「没装」）是最难查的错：使用方明确指了一个，就该指明这一个哪儿不对。
    """
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CMD", 'python -m "unclosed')
    with pytest.raises(compose.WorkerNotFoundError, match="GHERKAI_WORKER_NOVAACT_CMD"):
        compose.resolve_worker_cmd("novaact")


def test_chain_level2_same_venv_module_no_wrapper(monkeypatch):
    """第二级（仅 Python 引擎）：find_spec 命中 → `sys.executable -m <import 名>`、cwd=None。

    **无包装层**是硬要求：EVENTS_FD 经 pass_fds 只到被直接 spawn 的那个进程（ADR 0024 三通道）——
    故这一级恒是 `python -m`，不是任何脚本/wrapper。
    """
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CMD", raising=False)
    wc = compose.resolve_worker_cmd("novaact")
    assert wc.cmd == [sys.executable, "-m", "gherkai_worker_novaact"]
    assert wc.cwd is None and "gherkai_worker_novaact" in wc.source


def test_chain_level3_path_executable(monkeypatch):
    # 第二级 miss（非 Python 引擎 / 包没装）→ 第三级 PATH 可执行 `gherkai-worker-<engine>`
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which",
                        lambda n: "/usr/local/bin/gherkai-worker-midscene" if n == "gherkai-worker-midscene" else None)
    wc = compose.resolve_worker_cmd("midscene")
    assert wc.cmd == ["/usr/local/bin/gherkai-worker-midscene"] and wc.cwd is None
    assert "PATH" in wc.source


def test_chain_level2_skipped_when_module_missing(monkeypatch):
    # Python 引擎的第二级只在 find_spec 命中时用（否则继续往下）——防「包没装也拼 -m」拼出必崩的 cmd
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CMD", raising=False)
    monkeypatch.setattr(compose, "_find_worker_spec", lambda mod: False)
    monkeypatch.setattr(compose.shutil, "which",
                        lambda n: "/opt/bin/gherkai-worker-novaact" if n == "gherkai-worker-novaact" else None)
    assert compose.resolve_worker_cmd("novaact").cmd == ["/opt/bin/gherkai-worker-novaact"]


def test_chain_level4_uvx_only_on_pure_release(monkeypatch):
    """第四级兜底拉起只有 novaact/uvx：版本是纯发行版 + uvx 在 PATH → 按 CLI 版本 pin（worker 与 CLI 须同版本）。
    midscene **没有第四级**——fd 预演实测 npx 把 EVENTS_FD 换成 npm 自己的 FIFO（写即 EBADF、事件全丢），
    即使 npx 在 PATH、版本纯净，也直接 miss 报安装指引（ADR 0037 决策 3「预演不过则降为报错 + 安装指引」）。"""
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CMD", raising=False)
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose, "_find_worker_spec", lambda mod: False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: f"/bin/{n}" if n in ("uvx", "npx") else None)
    nova = compose.resolve_worker_cmd("novaact", version="1.4.0")
    assert nova.cmd == ["uvx", "gherkai-worker-novaact==1.4.0"]
    with pytest.raises(compose.WorkerNotFoundError) as ei:
        compose.resolve_worker_cmd("midscene", version="1.4.0")
    assert "npm i -g @gherkai/worker-midscene" in str(ei.value)


@pytest.mark.parametrize("dev_version", ["1.4.0.post10.dev0+abc123.dirty", "1.4.0.dev1", "1.4.0.post3",
                                         "1.4.0+local.1"])
def test_chain_level4_skipped_on_non_release_version(monkeypatch, dev_version):
    """dev/post/本地段版本**不在 PyPI/npm 上**（ADR 0037 决策 2b 的派生形态）→ 第四级跳过、直接 miss 报安装指引。

    否则 contributor 在 dev 版下会拿到「uvx 解析不到这个版本」的难懂网络错误，而不是「worker 没装、这样装」。
    """
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CMD", raising=False)
    monkeypatch.setattr(compose, "_find_worker_spec", lambda mod: False)
    # 只有 uvx 在 PATH（worker bin 不在）→ 前三级全 miss，第四级是否成立全看版本
    monkeypatch.setattr(compose.shutil, "which", lambda n: f"/bin/{n}" if n == "uvx" else None)
    with pytest.raises(compose.WorkerNotFoundError):
        compose.resolve_worker_cmd("novaact", version=dev_version)


def test_chain_level4_skipped_when_launcher_absent(monkeypatch):
    # 第二条件：uvx 不在 PATH → 跳过第四级、报安装指引
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CMD", raising=False)
    monkeypatch.setattr(compose, "_find_worker_spec", lambda mod: False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    with pytest.raises(compose.WorkerNotFoundError):
        compose.resolve_worker_cmd("novaact", version="1.4.0")


def test_chain_all_miss_raises_with_install_hint(monkeypatch):
    """四级全 miss → WorkerNotFoundError 带引擎名 + 该引擎的安装指引 + env 覆写指引（退出码交调用点）。"""
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    with pytest.raises(compose.WorkerNotFoundError) as ei:
        compose.resolve_worker_cmd("midscene")
    e = ei.value
    assert e.engine == "midscene"
    assert "npm i -g @gherkai/worker-midscene" in str(e) and "Node ≥ 22" in str(e)
    assert "GHERKAI_WORKER_MIDSCENE_CMD" in str(e)
    assert isinstance(e, RuntimeError)  # 既有「worker 起不来→RuntimeError」的调用点语义自动涵盖它


def test_chain_novaact_miss_hint_is_python_side(monkeypatch):
    # 安装指引按引擎分（两种语言两个地盘）：novaact 指 uv tool install 'gherkai[local]'
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CMD", raising=False)
    monkeypatch.setattr(compose, "_find_worker_spec", lambda mod: False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    with pytest.raises(compose.WorkerNotFoundError, match=r"gherkai\[local\]"):
        compose.resolve_worker_cmd("novaact")


def test_resolve_worker_cmd_unknown_engine():
    with pytest.raises(ValueError, match="未知引擎"):
        compose.resolve_worker_cmd("nope")


def test_pure_release_predicate():
    # 第四级门槛的判据（PEP 440）：纯发行版才可能在 PyPI/npm 上
    assert compose.is_pure_release("1.4.0") and compose.is_pure_release("1.4.0rc1")
    assert not compose.is_pure_release("1.4.0.dev1")
    assert not compose.is_pure_release("1.3.0.post10.dev0+f2efc49.dirty")
    assert not compose.is_pure_release("1.4.0+dirty")
    assert not compose.is_pure_release("not-a-version")


# ---- build_engines：cmd/cwd 走定位链 + env 注入 ----

# build_engines 的 run_id 是必给参数（本机 worker 缺 RUN_ID 会在建会话前退出）；不针对 run_id 的用例统一传这个值
_RUN_ID = "20261030T000000Z-abc123"


def test_build_engines_has_both_legs(midscene_env_cmd):
    engines = compose.build_engines(run_id=_RUN_ID)
    assert set(engines) == {"novaact", "midscene"}
    # cmd 来自定位链（不实际起进程，只查接线）：novaact 在 dev 命中第二级、midscene 命中 env 覆写
    assert engines["novaact"].cmd == [sys.executable, "-m", "gherkai_worker_novaact"]
    assert engines["midscene"].cmd == ["node", "/fake/midscene-worker.mjs"]


def test_build_engines_miss_leg_does_not_break_the_other(monkeypatch):
    """某引擎定位链 miss **不影响**另一个引擎项（ADR 0037 决策 3）：dev 下 midscene 未装是常态，
    novaact-only 的 run 必须照常运行；miss 的那个引擎项一用即抛 WorkerNotFoundError（带安装指引），
    **不是** resolver 的「未知引擎」（那会把「没装」误导成「拼错名」）。"""
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    engines = compose.build_engines(run_id=_RUN_ID)
    assert set(engines) == {"novaact", "midscene"}  # 引擎名恒在册
    assert engines["novaact"].cmd[-1] == "gherkai_worker_novaact"
    with pytest.raises(compose.WorkerNotFoundError, match="npm i -g"):
        engines["midscene"].run_scope(object())


def test_build_engines_wraps_subprocess_legs_with_event_recorder_when_event_log_given(tmp_path: Path, monkeypatch, midscene_env_cmd):
    """event_log（ADR 0042 决策七）：两个真引擎项都包成 EventRecordingEngine（Engine port 形状不变、cmd 等成员转发）；定位 miss 的占位
    项不包，安装指引照常在 run_scope 时抛出；不传 event_log 时不包。"""
    from gherkai_core.adapters.event_log import EventRecordingEngine, SqliteEventLog
    log = SqliteEventLog(tmp_path / "events.db")
    engines = compose.build_engines(run_id=_RUN_ID, event_log=log)
    assert all(isinstance(e, EventRecordingEngine) for e in engines.values())
    assert engines["midscene"].cmd == ["node", "/fake/midscene-worker.mjs"]
    assert not any(isinstance(e, EventRecordingEngine) for e in compose.build_engines(run_id=_RUN_ID).values())
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    engines2 = compose.build_engines(run_id=_RUN_ID, event_log=log)
    assert not isinstance(engines2["midscene"], EventRecordingEngine)
    with pytest.raises(compose.WorkerNotFoundError, match="npm i -g"):
        engines2["midscene"].run_scope(object())


def test_events_db_path_and_local_event_log(tmp_path: Path):
    """事件库路径单点 <report_dir>/<run_id>/events.db；库不存在时 build_local_event_log 给 None（旧版本执行的 run 或 --no-report）。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    assert compose.events_db_path(tmp_path, "r1") == tmp_path / "r1" / "events.db"
    assert compose.build_local_event_log(tmp_path, "r1") is None
    (tmp_path / "r1").mkdir()
    SqliteEventLog(tmp_path / "r1" / "events.db")
    assert isinstance(compose.build_local_event_log(tmp_path, "r1"), SqliteEventLog)


def test_build_cloud_event_log_uses_injected_table(tmp_path: Path):
    """云端事件流读取按 run 与 scope 列表装配 DdbEventLog；句柄可注入、不碰 boto3。"""
    from gherkai_core.adapters.event_log import DdbEventLog
    log = compose.build_cloud_event_log(events_table="t-events", run_id="r1", scope_ids=["a", "b"], ddb_table=object())
    assert isinstance(log, DdbEventLog)


def test_build_engines_injects_extra_http_headers_env(monkeypatch, midscene_env_cmd):
    """extra_http_headers（ADR 0035 决策 4）→ 两 worker env 注 GHERKAI_EXTRA_HTTP_HEADERS（JSON）；
    不传则**不注入、且清掉宿主继承的同名值**（该键由组合根拥有，见 compose._COMPOSE_OWNED_WORKER_ENV）。"""
    import json as _json

    engines = compose.build_engines(run_id=_RUN_ID, extra_http_headers={"ngrok-skip-browser-warning": "1"})
    for name in ("novaact", "midscene"):
        env = engines[name]._env
        assert env is not None, name
        assert _json.loads(env["GHERKAI_EXTRA_HTTP_HEADERS"]) == {"ngrok-skip-browser-warning": "1"}
    # 宿主 shell 里有同名值时不传 headers：两个引擎项都必须建 env（非 None）且该键已被清掉。
    # 断言不写成 `env2 is None or key not in env2`——env2 为 None 时那种写法空过，恰好照不出继承泄漏。
    monkeypatch.setenv("GHERKAI_EXTRA_HTTP_HEADERS", '{"leaked": "1"}')
    engines2 = compose.build_engines(run_id=_RUN_ID)
    for name in ("novaact", "midscene"):
        env2 = engines2[name]._env
        assert env2 is not None, name
        assert "GHERKAI_EXTRA_HTTP_HEADERS" not in env2, name


def test_build_engines_injects_steps_dir_env_both_legs(tmp_path: Path, monkeypatch, midscene_env_cmd):
    """steps_dir（ADR 0037 决策 4）→ **两个** worker 都注 GHERKAI_STEPS_DIR（两引擎扫同一目录、各取自己的
    扩展名）；不传则不注入、且清掉宿主继承的同名值（worker 只剩内建脚手架）。约定逻辑不进 worker。"""
    steps = tmp_path / "steps"
    engines = compose.build_engines(run_id=_RUN_ID, steps_dir=steps)
    for name in ("novaact", "midscene"):
        assert engines[name]._env["GHERKAI_STEPS_DIR"] == str(steps), name
    # 同上：宿主 env 有值时收紧成「env2 必非 None 且不含该键」，不用会空过的 or 写法
    monkeypatch.setenv("GHERKAI_STEPS_DIR", "/host/steps")
    engines2 = compose.build_engines(run_id=_RUN_ID)
    for name in ("novaact", "midscene"):
        env2 = engines2[name]._env
        assert env2 is not None, name
        assert "GHERKAI_STEPS_DIR" not in env2, name


def test_build_engines_scrubs_inherited_owned_env(monkeypatch, midscene_env_cmd):
    """组合根拥有的 worker env 先清后注（ADR 0037 决策 4/3 + ADR 0035 决策 4 + ADR 0051 决策 13 + ADR 0024「run_id + scope_id
    注入 worker」条）：入参说没有的四个键，宿主 shell 里的同名值**不得**越过组合根直达 worker；必给的 `RUN_ID` 只取入参的值。

    真实触发形态：提交时既无 `--steps-dir`、也无 `./steps`，于是 definition 里 steps_dir 为 None；之后在 export 了
    GHERKAI_STEPS_DIR 的 shell 里 `status <run> --wait` 接力推进——只做加法的注入会让 worker 加载接力者那台机器的
    step 目录，本 run 用到的确定性 step 集与 definition 不符、判定不可复现。
    """
    import os

    monkeypatch.setenv("GHERKAI_STEPS_DIR", "/host/steps")
    monkeypatch.setenv("GHERKAI_NO_ARTIFACTS", "1")
    monkeypatch.setenv("GHERKAI_EXTRA_HTTP_HEADERS", '{"leaked": "1"}')
    monkeypatch.setenv("GHERKAI_SESSION_WARMUP_URL", "https://leaked/")
    monkeypatch.setenv("RUN_ID", "host-run")
    assert {"GHERKAI_STEPS_DIR", "GHERKAI_NO_ARTIFACTS", "GHERKAI_EXTRA_HTTP_HEADERS", "GHERKAI_SESSION_WARMUP_URL",
            "RUN_ID"} == set(compose._COMPOSE_OWNED_WORKER_ENV)  # 宿主值全部预置，下面的逐键断言才覆盖整族
    engines = compose.build_engines(run_id=_RUN_ID)  # 只给必给的 run id，其余都不传（即 definition 里都没有）
    for name in ("novaact", "midscene"):
        env = engines[name]._env
        assert env["RUN_ID"] == _RUN_ID, name  # 宿主的 host-run 被入参覆盖
        for key in set(compose._COMPOSE_OWNED_WORKER_ENV) - {"RUN_ID"}:
            assert key not in env, (name, key)
        assert env.get("PATH") == os.environ.get("PATH"), name  # 只清组合根拥有的键，其余（PATH/AWS 凭证等）照常继承


def test_resolver_known_and_unknown(midscene_env_cmd):
    engines = compose.build_engines(run_id=_RUN_ID)
    resolver = compose.make_resolver(engines)
    assert resolver("novaact") is engines["novaact"]
    with pytest.raises(ValueError, match="未知引擎"):
        resolver("nope")


def test_load_feature_uri_is_given_path_normalized(tmp_path: Path, monkeypatch):
    """uri 即使用方给出的路径规范化后原样（ADR 0037 决策 3）：相对给相对（`./` 折掉、`..` 保留），不相对任何根。"""
    feat = tmp_path / "features" / "demo.feature"
    feat.parent.mkdir(parents=True)
    feat.write_text("Feature: x\n  Scenario: y\n    When \"做点啥\"\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    fs = compose.load_feature(Path("./features/demo.feature"))
    assert isinstance(fs, FeatureSource)
    assert fs.uri == "features/demo.feature"
    assert "Scenario: y" in fs.text
    monkeypatch.chdir(tmp_path / "features")
    assert compose.load_feature(Path("../features/demo.feature")).uri == "../features/demo.feature"


def test_load_feature_absolute_path_stays_absolute(tmp_path: Path):
    # 绝对路径给绝对路径（不做 relative_to 任何根、不 resolve 符号链接）
    outside = tmp_path / "other.feature"
    outside.write_text("Feature: z\n", encoding="utf-8")
    fs = compose.load_feature(outside)
    assert fs.uri == str(outside)


def test_no_repo_root_consumer_remains():
    """`repo_root()` 已整体退役（ADR 0037 决策 3）：分发后没有 repo，任何靠仓库结构的隐式行为都是漂移面。

    结构性护栏——名字回来（连同「从本文件上溯几层」的推导）就是回归，且这种回归在单测里天然隐形
    （dev 树下上溯恰好成立、wheel 安装的使用方那里才失败）。
    """
    assert not hasattr(compose, "repo_root")
    src = Path(compose.__file__).read_text(encoding="utf-8")
    assert "parents[2]" not in src, "compose 又出现了上溯仓库根的推导"


def test_build_engines_injects_artifact_dirs_symmetrically(tmp_path: Path, midscene_env_cmd):
    # 两引擎对称：产物落点经环境变量注入各自 worker 的 env（ADR 0027 产物归位）。
    nova_dir = tmp_path / "r1" / "nova-trajectories"
    mid_dir = tmp_path / "r1" / "midscene-run"
    engines = compose.build_engines(run_id=_RUN_ID, nova_logs_dir=nova_dir, midscene_run_dir=mid_dir)
    assert engines["novaact"]._env["NOVA_LOGS_DIR"] == str(nova_dir)
    assert engines["midscene"]._env["MIDSCENE_RUN_DIR"] == str(mid_dir)
    # 完整继承 os.environ（叠加而非替换）——否则 worker 丢 AWS 凭证等
    import os
    assert engines["midscene"]._env.get("PATH") == os.environ.get("PATH")


def test_build_engines_no_dirs_injects_no_artifact_dir_env(monkeypatch, midscene_env_cmd):
    # 不传落点：两个引擎都不注落点 env（回落 SDK 默认），但 env 照常新建——必给的 RUN_ID 恒要注入，
    # 其余继承 os.environ（PATH/AWS 凭证等），不是整份替换。
    import os

    monkeypatch.delenv("NOVA_LOGS_DIR", raising=False)
    monkeypatch.delenv("MIDSCENE_RUN_DIR", raising=False)
    engines = compose.build_engines(run_id=_RUN_ID)
    for name in ("novaact", "midscene"):
        env = engines[name]._env
        assert env["RUN_ID"] == _RUN_ID, name
        assert "NOVA_LOGS_DIR" not in env and "MIDSCENE_RUN_DIR" not in env, name
        assert env.get("PATH") == os.environ.get("PATH"), name


def test_build_engines_nova_always_has_act_timeout(midscene_env_cmd):
    # Nova env **恒非 None**：即便无产物落点，组合根也要注入 NOVA_ACT_TIMEOUT_S（双端同源，ADR 0024 grace 硬约束）——
    # worker 读它作 act timeout、自报的 grace 下限也按同一个注入值算，消除两处独立 120 的漂移。
    engines = compose.build_engines(run_id=_RUN_ID)
    assert engines["novaact"]._env is not None
    assert engines["novaact"]._env["NOVA_ACT_TIMEOUT_S"] == str(compose.nova_act_timeout_s())


def test_build_engines_never_injects_artifact_s3_env(tmp_path: Path, midscene_env_cmd):
    # 本机后端**恒不注入** S3 上传落点（worker 据「有没有这组 env」决定上传，无 → 报 file://，ADR 0029）：
    # 上传落点只由云端后端的 build_fargate_engines 注入，预演由 e2e_harness 自拼 env（ADR 0016 决策 B）。
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    mid_dir = tmp_path / "rid" / "midscene-run"
    engines = compose.build_engines(run_id=_RUN_ID, nova_logs_dir=nova_dir, midscene_run_dir=mid_dir)
    for eng in ("novaact", "midscene"):
        assert "ARTIFACT_S3_BUCKET" not in engines[eng]._env
        assert "ARTIFACT_S3_PREFIX" not in engines[eng]._env


def test_build_engines_region_profile_override_env(tmp_path: Path, monkeypatch, midscene_env_cmd):
    # ADR 0016 决策 C：--region/--profile 解析值**覆盖**继承的 AWS_REGION/AWS_PROFILE（参数 > env），使二者真贯通到
    # worker（EventSink/JobSource/ArtifactUploader/Nova Workflow 建 client 都读它们），与 core store 同源、消除分叉。
    monkeypatch.setenv("AWS_REGION", "us-east-1")   # shell 里是 east
    monkeypatch.setenv("AWS_PROFILE", "shell-prof")  # shell 里是另一个 profile
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    mid_dir = tmp_path / "rid" / "midscene-run"
    engines = compose.build_engines(
        run_id=_RUN_ID, nova_logs_dir=nova_dir, midscene_run_dir=mid_dir,
        region="us-west-2", profile="cli-prof",  # --region west / --profile cli-prof
    )
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["AWS_REGION"] == "us-west-2"    # 参数覆盖 env，非继承的 east
        assert engines[eng]._env["AWS_PROFILE"] == "cli-prof"    # profile 同理覆盖


def test_build_engines_region_profile_none_preserve_inherited(tmp_path: Path, monkeypatch, midscene_env_cmd):
    # region/profile=None（未给参数、__main__ 解析出 None）：不干预，保留继承的 env（若 shell 有）——
    # 组合根不硬写、留 env/boto 默认链/profile config 兜底（现有宽容）。
    monkeypatch.setenv("AWS_REGION", "eu-central-1")
    monkeypatch.setenv("AWS_PROFILE", "inherited-prof")
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    engines = compose.build_engines(run_id=_RUN_ID, nova_logs_dir=nova_dir, region=None, profile=None)
    assert engines["novaact"]._env["AWS_REGION"] == "eu-central-1"      # 原样继承、未被抹掉
    assert engines["novaact"]._env["AWS_PROFILE"] == "inherited-prof"


def test_build_engines_region_profile_injected_without_artifact_dirs_both_legs(monkeypatch, midscene_env_cmd):
    # 不给产物落点时 region/profile 同样注入**两个引擎**：Nova Workflow 的 nova-act client 读 AWS_REGION 与凭证；
    # Midscene worker 经 fromNodeProviderChain 消费 profile 做 AgentCore/Bedrock 鉴权（真消费、非无害，ADR 0016 决策 C），
    # 少注一边，该引擎就拿不到 --profile 覆盖。
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    engines = compose.build_engines(run_id=_RUN_ID, region="ap-southeast-1", profile="cli-prof")  # 无 dirs
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["AWS_REGION"] == "ap-southeast-1"  # 参数覆盖继承的 east
        assert engines[eng]._env["AWS_PROFILE"] == "cli-prof"


def test_build_engines_region_profile_none_writes_no_aws_keys_both_legs(monkeypatch, midscene_env_cmd):
    # 对称边界：region/profile 均 None 时两个引擎都不写 AWS_REGION/AWS_PROFILE（宿主也没有时 env 里就没有，
    # 留 boto 默认链与 profile config 兜底）；env 本身照常新建，带必给的 RUN_ID，Nova 另带 NOVA_ACT_TIMEOUT_S。
    for key in ("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE"):
        monkeypatch.delenv(key, raising=False)
    engines = compose.build_engines(run_id=_RUN_ID, region=None, profile=None)
    for eng in ("novaact", "midscene"):
        env = engines[eng]._env
        assert env["RUN_ID"] == _RUN_ID, eng
        assert "AWS_REGION" not in env and "AWS_PROFILE" not in env, eng
    assert "NOVA_ACT_TIMEOUT_S" in engines["novaact"]._env


# ---- resolve_region：region 落实成具体字符串（ADR 0016 决策 C，修 AgentCore profile-only 崩）----
def test_resolve_region_explicit_wins(monkeypatch):
    # --region 显式最高优先，不碰 env/profile
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-2")
    assert compose.resolve_region("us-west-2", "some-prof") == "us-west-2"


def test_resolve_region_env_chain(monkeypatch):
    # 无 --region：AWS_REGION > AWS_DEFAULT_REGION
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")
    assert compose.resolve_region(None, None) == "ap-south-1"
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    assert compose.resolve_region(None, None) == "eu-west-1"  # AWS_REGION 优先于 DEFAULT


def test_resolve_region_falls_back_to_profile_config(monkeypatch):
    # 关键（profile-only region 落实）：--region/env 全 miss → 回落 boto3.Session(profile).region_name 读 profile config 的 region。
    # 不落实则只配了 profile 的使用方下 worker AgentCore validate_region(None) → InvalidRegionError 崩。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    captured = {}

    class _FakeSession:
        def __init__(self, profile_name=None):
            captured["profile"] = profile_name
            self.region_name = "eu-west-2"  # 模拟 profile config 里 region=eu-west-2

    import boto3
    monkeypatch.setattr(boto3.session, "Session", _FakeSession)
    assert compose.resolve_region(None, "myprofile") == "eu-west-2"
    assert captured["profile"] == "myprofile"  # 确实按解析出的 profile 读 config


def test_resolve_region_none_when_all_miss(monkeypatch):
    # 全 miss（无 --region/env、profile config 也无 region）→ 返回 None，即 fail-loud（worker 报错、不硬编码 east）。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    class _NoRegionSession:
        def __init__(self, profile_name=None):
            self.region_name = None  # profile 无 region 字段

    import boto3
    monkeypatch.setattr(boto3.session, "Session", _NoRegionSession)
    assert compose.resolve_region(None, None) is None


def test_resolve_region_no_boto3_returns_none_not_crash(monkeypatch):
    # 纯 local 不依赖 boto3：--region/env 全 miss 需回落 profile config，但**缺 boto3（未装 aws extra）时**
    # 不能抛未捕获 ImportError——catch → None fail-loud（等价「无 region」）。绿≠对：dev 装了 boto3 恒绿掩盖此路径，
    # 故拦截 `import boto3` 抛 ImportError，实际验证这条路径。守「纯 local 路径绝不依赖 boto3」不变量（ADR 0016 决策 C；
    # boto3 走库层 `gherkai-core[aws]` extra——CLI 发行包 gherkai 已硬依赖它（ADR 0037 决策 2c），但本不变量
    # 与安装期装没装 boto3 无关）。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    import builtins
    _orig_import = builtins.__import__

    def _no_boto3(name, *a, **k):
        if name == "boto3":
            raise ImportError("simulated pure-local: boto3 not installed")
        return _orig_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_boto3)
    assert compose.resolve_region(None, "someprofile") is None  # 缺 boto3 读不到 profile config → None、不崩


# ---- resolve_aws_identity：profile + region 解析链的唯一实现（ADR 0016 决策 C）----
def test_resolve_aws_identity_takes_profile_from_env(monkeypatch):
    """profile 入参为 None 时取 `AWS_PROFILE`，并把它喂给 region 解析（profile config 那一级要用它）。"""
    monkeypatch.setenv("AWS_PROFILE", "env-prof")
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: f"region-of-{p}")  # 不摸真 ~/.aws
    assert compose.resolve_aws_identity(None, None) == ("region-of-env-prof", "env-prof")


def test_resolve_aws_identity_flag_wins_over_env(monkeypatch):
    """对偶（防「恒取 env」的假绿反面）：显式 profile 覆盖 `AWS_PROFILE`；显式 region 照样过 resolve_region。"""
    monkeypatch.setenv("AWS_PROFILE", "env-prof")
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: r)
    assert compose.resolve_aws_identity("us-west-2", "flag-prof") == ("us-west-2", "flag-prof")


def test_resolve_cloud_target_goes_through_resolve_aws_identity(monkeypatch):
    """cloud 目标解析不自写一份身份解析链——换掉唯一实现即整条链改变（单一事实源锁定）。"""
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setattr(compose, "resolve_aws_identity", lambda r, p, **kw: ("region-x", "profile-x"))
    t = compose.resolve_cloud_target(prefix="p-")
    assert (t.region, t.profile) == ("region-x", "profile-x")


# ---- query_capabilities：整份自述对象 + 契约校验 + 按（引擎, steps 目录）缓存（ADR 0036「5.」）----

@pytest.fixture
def fresh_caps_cache(monkeypatch):
    """每个用例一份空缓存：模块级缓存跨用例泄漏会让「问了几次」的断言与失败情形全部失真。"""
    monkeypatch.setattr(compose, "_CAPABILITIES_CACHE", {})


def _caps_json(engine: str = "novaact", min_grace_s=150, steps: str = "[]",
               model_id: str | None = None) -> bytes:
    """一份合契约的自述对象（五个键，ADR 0036「5.」）；模型 id 不给就按引擎取该引擎真实会自报的那个。"""
    model_id = model_id or ("nova-act-v1.0" if engine == "novaact" else "qwen.qwen3-vl-235b-a22b")
    return (f'{{"schema_version": 2, "engine": "{engine}", "min_grace_s": {min_grace_s}, '
            f'"targets": [{{"device": "desktop", "ui_kinds": ["web"]}}], '
            f'"deterministic_steps": {steps}, "model_id": "{model_id}"}}').encode()


def _fake_caps_proc(payload: bytes, returncode: int = 0, stderr: bytes = b""):
    class _P:
        pass
    _P.returncode, _P.stdout, _P.stderr = returncode, payload, stderr
    return _P


def test_query_capabilities_returns_whole_object(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """整份自述对象原样返回（六个键：schema_version / engine / min_grace_s / targets / deterministic_steps / model_id）——
    清单、grace 下限、steps 加载结果、当前模型 id 都出自**这一次** spawn（ADR 0036「5.」「加键不加入口」）。

    Nova 查询**必须注入 NOVA_ACT_TIMEOUT_S**：worker 自报的下限是这个注入值 + 它自己的 margin，不注入则它按
    自带缺省算，operator 调大单 act 上界后下限静默偏低（组合根持单一取值点的意义就在此）。
    """
    import os
    import subprocess

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"], captured["env"] = cmd, kw.get("env")
        return _fake_caps_proc(_caps_json(steps='[{"pattern": "p", "description": "d", "example": "e"}]'))

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("GHERKAI_STEPS_DIR", "/host/steps")  # 先把宿主 shell 弄脏，否则下面「不含该键」的断言空过
    assert compose.query_capabilities("novaact") == {
        "schema_version": 2, "engine": "novaact", "min_grace_s": 150, "targets": [{"device": "desktop", "ui_kinds": ["web"]}],
        "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e"}],
        "model_id": "nova-act-v1.0"}
    assert captured["cmd"] == ["/fake/novaact-worker", "--capabilities"]  # 定位链 cmd + 唯一的自述 flag
    assert captured["env"]["NOVA_ACT_TIMEOUT_S"] == str(compose.nova_act_timeout_s())
    # 未给 steps 目录：env 仍自建一份——组合根拥有的键「有值注、无值清」，宿主 shell 的 GHERKAI_STEPS_DIR 不得
    # 越过调用方解析出的结果（清单要与本次要运行的 step 集一致）；其余环境照常继承。
    assert "GHERKAI_STEPS_DIR" not in captured["env"]
    assert captured["env"].get("PATH") == os.environ.get("PATH")


def test_query_capabilities_injects_steps_dir_env(monkeypatch, novaact_env_cmd, fresh_caps_cache, tmp_path):
    """该入口同样加载 steps 目录（ADR 0037 决策 4）→ steps_dir 经 env 注入：清单因此含使用方定制 step，
    使用方 steps 加载失败也在这一次 spawn 里 fail-loud。注入是叠加（保 os.environ，否则 worker 丢 PATH/凭证）。"""
    import os
    import subprocess

    captured = {}
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: captured.update(kw) or _fake_caps_proc(_caps_json()))
    compose.query_capabilities("novaact", steps_dir=tmp_path / "steps")
    assert captured["env"]["GHERKAI_STEPS_DIR"] == str(tmp_path / "steps")
    assert captured["env"].get("PATH") == os.environ.get("PATH")
    assert captured["cwd"] is None  # 定位链未给 cwd → 继承本进程 CWD（worker 无专属 cwd，ADR 0037 决策 3）


def test_query_capabilities_caches_per_engine_and_steps_dir(monkeypatch, novaact_env_cmd, fresh_caps_cache, tmp_path):
    """缓存键是（引擎, steps 目录）二元组：同键第二次不 spawn；换引擎、换目录、无目录各自一份（清单随目录变，
    Nova 每次 spawn 都要 import SDK，多问一次不便宜）。"""
    import subprocess

    calls: list[str] = []

    def fake_run(cmd, **kw):
        calls.append(cmd[0])
        engine = "novaact" if "novaact" in cmd[0] else "midscene"
        return _fake_caps_proc(_caps_json(engine, 150 if engine == "novaact" else 31))

    monkeypatch.setattr(subprocess, "run", fake_run)
    a, b = tmp_path / "a", tmp_path / "b"
    assert compose.query_capabilities("novaact", steps_dir=a)["min_grace_s"] == 150
    assert compose.query_capabilities("novaact", steps_dir=a)["min_grace_s"] == 150  # 同键 → 走缓存
    assert calls == ["/fake/novaact-worker"]
    compose.query_capabilities("novaact", steps_dir=b)   # 换 steps 目录 → 另一份（清单可能不同）
    compose.query_capabilities("novaact")                # 无 steps 又一份
    compose.query_capabilities("midscene", steps_dir=a)  # 换引擎 → 另一份
    assert len(calls) == 4
    assert set(compose._CAPABILITIES_CACHE) == {("novaact", str(a)), ("novaact", str(b)),
                                                ("novaact", None), ("midscene", str(a))}


def test_query_capabilities_worker_failure_fails_loud_verbatim(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """worker 非零退出 → WorkerSelfDescribeError **原样上抛**（转述 stderr）、不写缓存、不回落任何常量。

    **组合根不再追加「不认识能力自述 → 须同版本安装」那句断言**：该入口现在会加载使用方 steps（ADR 0037
    决策 4），非零退出不再只剩「版本不一致的 worker 不认这个 flag」一种成因（更常见的是使用方 steps 文件报错）
    ——在这里替使用方断定成因会误导，两种可能由调用点用中性文案一起点到。
    """
    import subprocess

    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(
        b"", returncode=2, stderr="steps/demo.py：SyntaxError".encode()))
    with pytest.raises(compose.WorkerSelfDescribeError) as ei:
        compose.query_capabilities("novaact", steps_dir="/tmp/steps")
    assert "steps/demo.py：SyntaxError" in str(ei.value)
    assert "同版本安装" not in str(ei.value)
    assert compose._CAPABILITIES_CACHE == {}


# 身份位与必有的顶层 targets 合法，让每个用例只有一处缺陷（后面显式给的 targets 会覆盖这里的，JSON 重复键取后者）
_OK_HEAD = b'"schema_version": 2, "engine": "novaact", "targets": [{"device": "desktop", "ui_kinds": ["web"]}]'
_OK_STEPS = b', "deterministic_steps": []'
_OK_MODEL = b', "model_id": "nova-act-v1.0"'
_OK_TAIL = _OK_STEPS + _OK_MODEL  # 两个合法的尾键：拿它填「缺陷在下限/身份位」那批用例


@pytest.mark.parametrize("payload", [
    b'{' + _OK_HEAD + _OK_TAIL + b'}',                                   # 缺下限键
    b'{' + _OK_HEAD + b', "min_grace_s": "150"' + _OK_TAIL + b'}',       # 字符串
    b'{' + _OK_HEAD + b', "min_grace_s": true' + _OK_TAIL + b'}',        # bool（是 int 子类，须单独挡）
    b'{' + _OK_HEAD + b', "min_grace_s": -1' + _OK_TAIL + b'}',          # 负数
    b'{' + _OK_HEAD + b', "min_grace_s": Infinity' + _OK_TAIL + b'}',    # 非有限（json 认它）
    b'{' + _OK_HEAD + b', "min_grace_s": 150' + _OK_MODEL + b'}',        # 缺清单键
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": {}' + _OK_MODEL + b'}',  # 清单不是数组
    b'{' + _OK_HEAD + b', "min_grace_s": 150' + _OK_STEPS + b'}',                   # 缺模型 id 键
    b'{' + _OK_HEAD + b', "min_grace_s": 150' + _OK_STEPS + b', "model_id": ""}',   # 模型 id 空串
    b'{' + _OK_HEAD + b', "min_grace_s": 150' + _OK_STEPS + b', "model_id": 1}',    # 模型 id 不是字符串
    b'[{' + _OK_HEAD + b', "min_grace_s": 150' + _OK_TAIL + b'}]',       # 不是 JSON 对象
    b'{"schema_version": 2, "engine": "midscene", "min_grace_s": 31' + _OK_TAIL + b'}',  # 自称另一引擎
    b'{"schema_version": 1, "engine": "novaact", "min_grace_s": 150' + _OK_TAIL + b'}',   # 版本不认识（1.4 的 worker 报 1）
    b'{"schema_version": 3, "engine": "novaact", "min_grace_s": 150' + _OK_TAIL + b'}',   # 版本不认识（比命令行工具新）
    b'{"engine": "novaact", "min_grace_s": 150' + _OK_TAIL + b'}',                        # 缺格式版本
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": []}]' + _OK_MODEL + b'}',          # keywords 空
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": ["And"]}]' + _OK_MODEL + b'}',     # keywords 未知取值
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": ["Then", "Then"]}]' + _OK_MODEL + b'}',  # keywords 重复
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": null}]' + _OK_MODEL + b'}',  # keywords 显式 null（只有缺键算旧 worker）
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": "Given"}]' + _OK_MODEL + b'}',  # keywords 不是数组
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": [["Given"]]}]' + _OK_MODEL + b'}',  # 元素不是字符串（进 set 会 TypeError，须先核类型）
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": ["p"]' + _OK_MODEL + b'}',  # 清单项不是对象（消费者 e.get 会崩在无关处）
    # ---- 测试目标相关键（ADR 0049 决策 1）：顶层 targets ----
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": {}' + _OK_TAIL + b'}',                                                  # targets 不是数组
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "tv", "ui_kinds": ["web"]}]' + _OK_TAIL + b'}',              # 未知 device
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": []}]' + _OK_TAIL + b'}',              # ui_kinds 空
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web", "web"]}]' + _OK_TAIL + b'}',  # ui_kinds 重复
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["tv"]}]' + _OK_TAIL + b'}',          # 未知 ui_kind
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "desktop", "ui_kinds": ["web", "app"]}]' + _OK_TAIL + b'}',  # desktop 带 app
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": 0}]' + _OK_TAIL + b'}',        # max_session_s 为 0
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": -1}]' + _OK_TAIL + b'}',       # 负数
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": "8880"}]' + _OK_TAIL + b'}',   # 字符串
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": true}]' + _OK_TAIL + b'}',     # bool
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": 1e999}]' + _OK_TAIL + b'}',    # Infinity
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["app"], "max_session_s": 10}]' + _OK_TAIL + b'}',  # 顶层 device 重复
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]}]' + _OK_TAIL + b'}',  # 顶层条目不带 requires
    # ---- step 级 targets ----
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": "desktop"}]' + _OK_MODEL + b'}',  # 不是数组
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "android", "ui_kinds": ["web"], "requires": "web_context"}]}]' + _OK_MODEL + b'}',  # requires 不是数组
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "android", "ui_kinds": ["web"], "requires": ["web_context", "web_context"]}]}]' + _OK_MODEL + b'}',  # requires 重复
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": 10}]}]' + _OK_MODEL + b'}',  # step 级条目不带 max_session_s
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "android", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web"]}]}]' + _OK_MODEL + b'}',  # 完全重复的 step 级条目
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": null' + _OK_TAIL + b'}',  # 顶层 targets 显式 null（必有且须为数组）
    b'{"schema_version": 2, "engine": "novaact", "min_grace_s": 150' + _OK_TAIL + b'}',  # 顶层缺 targets：版本不一致、不兜缺省
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web", 1]}]' + _OK_TAIL + b'}',  # ui_kinds 元素不是字符串
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": 10}, {"device": "android", "ui_kinds": ["app"], "max_session_s": 20}]' + _OK_TAIL + b'}',  # 同 device 两条都带 max_session_s
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "targets": [{"device": "android", "ui_kinds": ["web"], "max_session_s": 1' + b"0" * 400 + b'}]' + _OK_TAIL + b'}',  # 超出 float 范围的整数
    b'{' + _OK_HEAD + b', "min_grace_s": 1' + b"0" * 400 + _OK_TAIL + b'}',  # min_grace_s 同样的超大整数（同一判定）
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": null}]' + _OK_MODEL + b'}',  # step 级 targets 显式 null
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "android", "ui_kinds": ["web"], "requires": null}]}]' + _OK_MODEL + b'}',  # requires 显式 null
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "android", "ui_kinds": ["web"], "requires": ["web_context", 1]}]}]' + _OK_MODEL + b'}',  # requires 元素不是字符串
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "android", "ui_kinds": ["web", "app"]}, {"device": "android", "ui_kinds": ["app", "web"]}]}]' + _OK_MODEL + b'}',  # 只是顺序不同的重复 step 级条目
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "tv", "ui_kinds": ["web"]}]}]' + _OK_MODEL + b'}',  # step 级未知 device
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "targets": [{"device": "desktop", "ui_kinds": ["web", "app"]}]}]' + _OK_MODEL + b'}',  # step 级 desktop 带 app
    # ---- 会话预热支持键 ----
    b'{' + _OK_HEAD + b', "min_grace_s": 150, "session_warmup": "yes"' + _OK_TAIL + b'}',  # 预热键不是 bool
])
def test_query_capabilities_rejects_off_contract_answer(monkeypatch, novaact_env_cmd, fresh_caps_cache, payload):
    """自述不合契约 → fail-loud，且不写缓存。校验放在这一个函数里，**每个消费者
    （run 前置 / list-deterministic / doctor / engine_min_grace / plan）都受同一道**：下限当 0 处理会让 core 的 grace
    护栏形同废除；身份位（engine / schema_version）不核则 `GHERKAI_WORKER_NOVAACT_CMD` 指到 midscene bin 时
    Nova 静默拿 31s（grace < 单 act 上界 → SIGTERM 落 act 中途必被硬杀）；清单不是数组则消费者 len() 崩在无关处；
    模型 id 缺/空/非串则 doctor 的模型行显示成没信息的「模型 」，把「不知道用的哪个模型」伪装成「知道了」
    （模型选择本身是 ADR 0004「模型版本选择策略」的显式决策，展示不实等于让 env 覆盖不可见）。
    失败类是「取到了、不兼容」（WorkerIncompatibleError），不是取不到：plan 据类区分，只对取不到降级（ADR 0036 决策 4）；
    除身份位指错引擎那一句外，诊断都以版本不一致那一句收尾。
    """
    import subprocess

    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(payload))
    with pytest.raises(compose.WorkerIncompatibleError) as ei:
        compose.query_capabilities("novaact")
    assert not isinstance(ei.value, compose.WorkerUnavailableError)
    assert str(ei.value).endswith(compose.VERSION_MISMATCH_ADVICE) or "自称 'midscene'" in str(ei.value)
    assert compose._CAPABILITIES_CACHE == {}


@pytest.mark.parametrize("version_part, shown", [(b'"schema_version": 1, ', "1"), (b"", "缺失"), (b'"schema_version": "2", ', '"2"')])
def test_query_capabilities_version_mismatch_uses_the_worker_sentence(monkeypatch, novaact_env_cmd, fresh_caps_cache,
                                                                     version_part, shown):
    """协议版本不等（含缺键）→ 诊断先点明两个版本号、再接版本不一致那一句，与 worker 拒绝不合版本的 job 行和 match 查询输入时同一句
    （ADR 0036 决策 4）；run / submit / list-deterministic / plan 转述的都是这一句。格式版本先于其余载荷键核对：1.4 的自述不带
    targets，诊断仍是版本不一致、不是「缺 targets」。"""
    import subprocess

    payload = b'{' + version_part + b'"engine": "novaact", "min_grace_s": 150' + _OK_TAIL + b'}'
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(payload))
    with pytest.raises(compose.WorkerIncompatibleError) as ei:
        compose.query_capabilities("novaact")
    assert str(ei.value) == (f"引擎 novaact 的能力自述格式版本是 {shown}，这个命令行工具认的是 {compose.PROTOCOL_SCHEMA_VERSION}："
                             "命令行工具与 worker 的版本不一致，请把两者装成同一版本。")
    assert compose.VERSION_MISMATCH_ADVICE == "命令行工具与 worker 的版本不一致，请把两者装成同一版本。"


def test_ask_worker_timeout_and_non_json_are_unavailable(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """超时与 stdout 不是合法 JSON 归入「取不到」（WorkerUnavailableError）：plan 只对这一类降级，与「取到了、不兼容」分开
    （ADR 0036「5.」末段的三类）；两个非 job 入口同一机制。"""
    import subprocess

    def timeout(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(compose.WorkerUnavailableError, match="能力自述超时"):
        compose.query_capabilities("novaact")
    with pytest.raises(compose.WorkerUnavailableError, match="确定性 step 查询超时"):
        compose.match_deterministic("novaact", [{"keyword": None, "text": "x"}])
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(b"Traceback (most recent call last):"))
    with pytest.raises(compose.WorkerUnavailableError, match="输出非 JSON"):
        compose.query_capabilities("novaact")
    with pytest.raises(compose.WorkerUnavailableError, match="输出非 JSON"):
        compose.match_deterministic("novaact", [{"keyword": None, "text": "x"}])
    assert compose._CAPABILITIES_CACHE == {}


def test_query_capabilities_accepts_keywords_declaration_and_missing_key(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """keywords 合契约的形态都放行：声明子集、声明全部、缺键（旧 worker，视为接受全部）——反例见上一条。"""
    import subprocess

    payload = (b'{' + _OK_HEAD + b', "min_grace_s": 150, "deterministic_steps": ['
               b'{"pattern": "a", "description": "d", "example": "e", "keywords": ["Given", "When"]}, '
               b'{"pattern": "b", "description": "d", "example": "e", "keywords": ["Given", "When", "Then"]}, '
               b'{"pattern": "c", "description": "d", "example": "e"}]' + _OK_MODEL + b'}')
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(payload))
    caps = compose.query_capabilities("novaact")
    assert [e.get("keywords") for e in caps["deterministic_steps"]] == [["Given", "When"], ["Given", "When", "Then"], None]


def test_query_capabilities_accepts_target_keys_and_keeps_unknown_requires(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """测试目标相关键合契约的形态都放行（ADR 0049 决策 1）：顶层多 device、设备条目带 max_session_s、step 级条目带 requires
    （取值不核：未知字符串如 "foo" 原样保留，取值集合归 worker 注册期校验）、预热键为 bool；同一 device 与 ui_kind 只是
    requires 不同的两个 step 级条目不算重复；未知的顶层键照旧容忍（向前兼容）。"""
    import subprocess

    payload = (b'{' + _OK_HEAD + b', "min_grace_s": 150, "session_warmup": true, "future_key": 1, "targets": ['
               b'{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8880}], '
               b'"deterministic_steps": [{"pattern": "a", "description": "d", "example": "e", "targets": ['
               b'{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]}, '
               b'{"device": "android", "ui_kinds": ["web"], "requires": ["foo"]}]}]' + _OK_MODEL + b'}')
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(payload))
    caps = compose.query_capabilities("novaact")
    assert caps["targets"][1]["max_session_s"] == 8880
    assert caps["deterministic_steps"][0]["targets"][2]["requires"] == ["foo"]  # 原样保留
    assert compose._CAPABILITIES_CACHE != {}


def test_target_defaults_follow_missing_key_semantics():
    """ADR 0049 决策 2：顶层缺 targets 不兜缺省（版本不一致，fail-loud）；step 级缺 targets 归一为桌面网页——不是「全部目标」、不是「未知放行」；
    缺 max_session_s 即无上限（键不出现）；有键时原样取、返回的是副本。"""
    with pytest.raises(compose.WorkerIncompatibleError, match="缺 targets"):
        compose.worker_targets({"deterministic_steps": []})
    assert compose.step_targets({"pattern": "p"}) == [{"device": "desktop", "ui_kinds": ["web"]}]
    caps = {"targets": [{"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8880}]}
    got = compose.worker_targets(caps)
    assert got == caps["targets"] and got is not caps["targets"] and got[0] is not caps["targets"][0]
    assert "max_session_s" not in compose.worker_targets({"targets": [{"device": "desktop", "ui_kinds": ["web"]}]})[0]
    entry = {"targets": [{"device": "ios", "ui_kinds": ["web"], "requires": ["web_context"]}]}
    assert compose.step_targets(entry) == entry["targets"] and compose.step_targets(entry)[0] is not entry["targets"][0]


def test_available_and_unsupported_targets_are_pure_set_operations():
    """交集（ADR 0049 决策 3）：按 device 匹配、ui_kinds 取交、空则丢弃；requires 原样带入；同一 device 与 ui_kind 只是 requires
    不同的两条各自保留、不合并。差集给出「声明了但不支持」的部分：整个 device 不支持则整条保留，部分 ui_kind 不支持则只剩那部分。"""
    declared = [{"device": "desktop", "ui_kinds": ["web"]},
                {"device": "android", "ui_kinds": ["web", "app"], "requires": ["web_context"]},
                {"device": "android", "ui_kinds": ["web"]},
                {"device": "ios", "ui_kinds": ["web"]}]
    only_desktop = [{"device": "desktop", "ui_kinds": ["web"]}]
    assert compose.available_targets(declared, only_desktop) == [{"device": "desktop", "ui_kinds": ["web"]}]
    assert compose.unsupported_targets(declared, only_desktop) == [
        {"device": "android", "ui_kinds": ["web", "app"], "requires": ["web_context"]},
        {"device": "android", "ui_kinds": ["web"]},
        {"device": "ios", "ui_kinds": ["web"]}]
    android_web = only_desktop + [{"device": "android", "ui_kinds": ["web"], "max_session_s": 8880}]
    assert compose.available_targets(declared, android_web) == [
        {"device": "desktop", "ui_kinds": ["web"]},
        {"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]},  # web 与 app 交出 web，requires 原样
        {"device": "android", "ui_kinds": ["web"]}]  # 与上一条只差 requires：各自成条
    assert compose.unsupported_targets(declared, android_web) == [
        {"device": "android", "ui_kinds": ["app"], "requires": ["web_context"]},
        {"device": "ios", "ui_kinds": ["web"]}]
    assert compose.available_targets([], android_web) == [] and compose.unsupported_targets([], android_web) == []
    # 同 device 但界面类型无交集 → 整条丢弃；结果按声明顺序、不按 worker 顺序
    only_app = [{"device": "android", "ui_kinds": ["app"]}]
    assert compose.available_targets([{"device": "android", "ui_kinds": ["web"]}], only_app) == []
    assert compose.unsupported_targets([{"device": "android", "ui_kinds": ["web"]}], only_app) == [{"device": "android", "ui_kinds": ["web"]}]
    reversed_decl = [{"device": "ios", "ui_kinds": ["web"]}, {"device": "desktop", "ui_kinds": ["web"]}]
    both = [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "ios", "ui_kinds": ["web"]}]
    assert [t["device"] for t in compose.available_targets(reversed_decl, both)] == ["ios", "desktop"]


def test_query_capabilities_wrong_engine_names_the_misconfiguration(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """自称的引擎对不上 → 诊断点名「路径指错」并给出要查的配置项（而不是泛泛的「版本不一致」）。"""
    import subprocess

    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(_caps_json("midscene", 31)))
    with pytest.raises(compose.WorkerIncompatibleError, match="自称 'midscene'.*GHERKAI_WORKER_"):
        compose.query_capabilities("novaact")


def test_ask_worker_no_payload_entry_does_not_inherit_stdin(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """无 stdin 载荷的入口（`--capabilities`）显式 stdin=DEVNULL、不继承调用者 stdin：不认该 flag 的 worker
    （版本不一致）会掉进 job 模式读 stdin，继承来的 TTY 让它挂到超时才被判「自述超时」（诊断指错方向、还吞使用方
    键入）；DEVNULL 让它立刻读到 EOF 非零退出 → 「不认该入口即 fail-loud」才真落地。
    `--match-steps` 有 stdin 载荷（input=…），subprocess 不许同时给 stdin，故那条不设。"""
    import subprocess

    captured: list[dict] = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: captured.append(kw) or _fake_caps_proc(
        _caps_json() if "--capabilities" in cmd else b"[]"))
    compose.query_capabilities("novaact")
    compose.match_deterministic("novaact", [{"keyword": None, "text": "x"}])
    assert [kw.get("stdin") for kw in captured] == [subprocess.DEVNULL, None]
    assert captured[1]["input"] == b'[{"keyword": null, "text": "x"}]'


def test_query_capabilities_unknown_engine_raises(fresh_caps_cache):
    with pytest.raises(ValueError, match="未知引擎"):
        compose.query_capabilities("nope")


def test_query_capabilities_midscene_gets_no_nova_env(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """NOVA_ACT_TIMEOUT_S 只注给 Nova（它是 Nova 的配置项）——Midscene 的下限由它自己的收尾预算算出。"""
    import subprocess

    captured = {}
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: captured.update(kw) or _fake_caps_proc(_caps_json("midscene", 31)))
    monkeypatch.delenv("NOVA_ACT_TIMEOUT_S", raising=False)
    assert compose.query_capabilities("midscene")["min_grace_s"] == 31
    assert "NOVA_ACT_TIMEOUT_S" not in captured["env"]


# ---- _ask_worker：起不来的各种 OSError 都收成取不到（WorkerUnavailableError，调用点据类分叉、不冒 traceback）----
# 真起子进程（不 mock subprocess）：要验的正是 subprocess.run 在这几种情形下实际抛什么，mock 掉就验不到。

def test_ask_worker_non_executable_override_is_unavailable(monkeypatch, fresh_caps_cache, tmp_path):
    """env 覆写指向一个没有执行权限的文件 → subprocess 抛 PermissionError（不是 FileNotFoundError），也要收成取不到。"""
    script = tmp_path / "worker.sh"
    script.write_text("#!/bin/sh\necho '{}'\n", encoding="utf-8")
    script.chmod(0o644)
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CMD", str(script))
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CWD", raising=False)
    with pytest.raises(compose.WorkerUnavailableError, match="起不来") as e:
        compose.query_capabilities("novaact")
    assert isinstance(e.value.__cause__, PermissionError)
    assert "GHERKAI_WORKER_NOVAACT_CMD" in str(e.value)  # 点名用的是哪一级的命令
    assert compose._CAPABILITIES_CACHE == {}


def test_ask_worker_cwd_not_a_directory_is_unavailable(monkeypatch, fresh_caps_cache, tmp_path):
    """配套的 _CWD 指向普通文件 → subprocess 抛 NotADirectoryError，同样收成取不到。"""
    import shlex

    not_a_dir = tmp_path / "plain-file"
    not_a_dir.write_text("x", encoding="utf-8")
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CMD", shlex.quote(sys.executable))
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CWD", str(not_a_dir))
    with pytest.raises(compose.WorkerUnavailableError, match="起不来") as e:
        compose.query_capabilities("novaact")
    assert isinstance(e.value.__cause__, NotADirectoryError)


# ---- nova_act_timeout_s：惰性取值、坏值给产品语言的 ValueError（不在 import 时求值）----

@pytest.fixture
def fresh_nova_timeout(monkeypatch):
    """清空取值缓存（monkeypatch 在用例结束时还原原值）：缓存跨用例泄漏会让「环境变量怎么设就取到什么」的断言失真。"""
    monkeypatch.setattr(compose, "_nova_act_timeout_cached", None)


def test_nova_act_timeout_default_and_override(monkeypatch, fresh_nova_timeout):
    monkeypatch.delenv("NOVA_ACT_TIMEOUT_S", raising=False)
    assert compose.nova_act_timeout_s() == 120
    monkeypatch.setattr(compose, "_nova_act_timeout_cached", None)
    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", "300")
    assert compose.nova_act_timeout_s() == 300


def test_nova_act_timeout_is_cached_after_first_read(monkeypatch, fresh_nova_timeout):
    """一个进程内只解析一次：注给 worker 的值与自述查询用的值是同一个（自述缓存不设失效的前提）。"""
    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", "200")
    assert compose.nova_act_timeout_s() == 200
    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", "500")
    assert compose.nova_act_timeout_s() == 200


@pytest.mark.parametrize("bad", ["120s", "150.5", "", "0", "-5", "abc"])
def test_nova_act_timeout_bad_value_raises_product_message(monkeypatch, fresh_nova_timeout, bad):
    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", bad)
    with pytest.raises(ValueError, match="NOVA_ACT_TIMEOUT_S") as e:
        compose.nova_act_timeout_s()
    assert repr(bad) in str(e.value)
    # 坏值不进缓存：改对之后立刻生效
    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", "90")
    assert compose.nova_act_timeout_s() == 90


def test_bad_nova_act_timeout_does_not_break_import(tmp_path):
    """坏值不在 import 时抛异常：CLI 顶层 import 本模块，import 期抛异常会让 --version、plan 这些与 Nova 无关的命令也以 traceback 结束。"""
    import os
    import subprocess

    env = {**os.environ, "NOVA_ACT_TIMEOUT_S": "120s"}
    proc = subprocess.run([sys.executable, "-c", "import gherkai_runtime.compose"], env=env,
                          capture_output=True, cwd=tmp_path, timeout=60)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")


def test_bad_nova_act_timeout_only_disables_nova_leg(monkeypatch, fresh_nova_timeout, midscene_env_cmd):
    """本机后端：坏值只让 Nova 引擎项变成一用即抛的占位项，Midscene 照常装配（不受影响）。"""
    from gherkai_core.adapters.subprocess_engine import SubprocessEngine

    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", "120s")
    engines = compose.build_engines(run_id=_RUN_ID)
    assert isinstance(engines["midscene"], SubprocessEngine)
    for call in (lambda: engines["novaact"].run_scope(object()), lambda: engines["novaact"].start_scope(object())):
        with pytest.raises(ValueError, match="NOVA_ACT_TIMEOUT_S"):
            call()


def test_bad_nova_act_timeout_fails_nova_capabilities_query(monkeypatch, fresh_nova_timeout, novaact_env_cmd,
                                                            fresh_caps_cache):
    """能力自述查询同样取这个值：用到 Nova 的本机 run 在运行前检查就以退出码 2 结束（调用点收 ValueError），不 spawn。"""
    import subprocess

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: pytest.fail("坏值不应 spawn worker"))
    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", "150.5")
    with pytest.raises(ValueError, match="NOVA_ACT_TIMEOUT_S"):
        compose.query_capabilities("novaact")
    assert compose._CAPABILITIES_CACHE == {}


def test_bad_nova_act_timeout_only_disables_nova_fargate_leg(monkeypatch, fresh_nova_timeout):
    """云端后端同理：装配本身不抛，Nova 引擎项一用即抛，Midscene 照常构造。"""
    from gherkai_core.adapters import fargate_engine as fe

    captured: list = []
    monkeypatch.setattr(fe, "FargateEngine", lambda **kw: captured.append(kw) or "fake")
    monkeypatch.setenv("NOVA_ACT_TIMEOUT_S", "0")
    engines = compose.build_fargate_engines(
        run_id="rid-1", cluster="c", events_table="e", bucket="b", report_dir="runs",
        network_config={"subnets": ["subnet-x"]}, worker_task_defs={"novaact": "arn:rev:1", "midscene": "arn:rev:2"},
        region="us-west-2", ecs=object(), s3=object(), ddb_events_table=object())
    assert engines["midscene"] == "fake" and len(captured) == 1
    assert "NOVA_ACT_TIMEOUT_S" not in captured[0]["extra_env"]
    with pytest.raises(ValueError, match="NOVA_ACT_TIMEOUT_S"):
        engines["novaact"].start_scope(object())


# ---- engine_min_grace：下限取自自述对象、复用该引擎任一份缓存（ADR 0024「引擎自报下限」）----

def test_engine_min_grace_takes_worker_self_reported_value(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """下限取 worker 自报值（组合根不再持任何引擎特定常量）；一份缓存都没有时**不带 steps 目录**问一次
    （下限是引擎自己的收尾预算、与使用方 step 无关）。"""
    import subprocess

    captured, calls = {}, []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: (
        calls.append(cmd), captured.update(kw, cmd=cmd))[0] or _fake_caps_proc(_caps_json()))
    monkeypatch.setenv("GHERKAI_STEPS_DIR", "/host/steps")  # 弄脏宿主 env，否则下面的断言空过
    assert compose.engine_min_grace("novaact") == 150.0
    assert captured["cmd"] == ["/fake/novaact-worker", "--capabilities"]
    assert "GHERKAI_STEPS_DIR" not in captured["env"]
    assert compose.engine_min_grace("novaact") == 150.0  # 第二次走 query_capabilities 写下的缓存
    assert len(calls) == 1


def test_engine_min_grace_reuses_capabilities_asked_with_steps_dir(
        monkeypatch, novaact_env_cmd, fresh_caps_cache, tmp_path):
    """运行前检查带着 steps 目录问过 → 下限直接取那份缓存对象、**不再 spawn**（下限与 step 无关，故不挑目录）：
    这就是「本机 run 每引擎只 spawn 一次自述」的落点。另一引擎不共用缓存项。"""
    import subprocess

    calls: list[str] = []

    def fake_run(cmd, **kw):
        calls.append(cmd[0])
        engine = "novaact" if "novaact" in cmd[0] else "midscene"
        return _fake_caps_proc(_caps_json(engine, 150 if engine == "novaact" else 31))

    monkeypatch.setattr(subprocess, "run", fake_run)
    compose.query_capabilities("novaact", steps_dir=tmp_path / "steps")  # run 的运行前检查那一次
    assert calls == ["/fake/novaact-worker"]
    assert compose.engine_min_grace("novaact") == 150.0
    assert calls == ["/fake/novaact-worker"]  # 没有第二次 spawn
    assert compose.engine_min_grace("midscene") == 31.0
    assert calls == ["/fake/novaact-worker", "/fake/midscene-worker"]


def test_engine_min_grace_worker_failure_fails_loud(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """取不到就抛（异常原样冒上去、调用点以退出码 2 结束）——**绝不回落猜的常量**：那等于 grace 默默不够、收尾被强杀。"""
    import subprocess

    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(b"", returncode=2))
    with pytest.raises(compose.WorkerSelfDescribeError):
        compose.engine_min_grace("novaact")
    assert compose._CAPABILITIES_CACHE == {}


def test_engine_min_grace_unknown_engine_raises(fresh_caps_cache):
    # 未知引擎在定位链的单点校验处抛（不再静默给 0.0——那会让 core 的 grace 护栏对拼错的引擎名形同废除）
    with pytest.raises(ValueError, match="未知引擎"):
        compose.engine_min_grace("unknown")


def test_engine_min_grace_miss_raises_worker_not_found(monkeypatch, fresh_caps_cache):
    """本机没定位到该引擎 worker → WorkerNotFoundError（doctor 据此跳过比对、run 据此以退出码 2 结束并带安装指引）。"""
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    with pytest.raises(compose.WorkerNotFoundError):
        compose.engine_min_grace("midscene")


# ---- 两层命名（ADR 0033）：prefix + 基名推导 / task-def / container / SSM 路径 ----
def test_default_name_prefix_original_concat():
    # prefix 按原样拼接基名（分隔符由部署方负责，不带分隔符即与基名粘连；与 S3 key 前缀由 _normalize_prefix 补 / 的做法相反）
    assert names.default_name("gherkai-", "runs") == "gherkai-runs"
    assert names.default_name("prod-", "events") == "prod-events"
    assert names.default_name("nodash", "runs") == "nodashruns"  # 无分隔符 → 粘连（部署方负责）


def test_task_def_and_container_name():
    # task-def family 带 prefix、按引擎；container 名不带 prefix（随 task-def 走，避冗余）
    assert names.task_def_name("prod-", "novaact") == "prod-novaact-worker"
    assert names.task_def_name("gherkai-", "midscene") == "gherkai-midscene-worker"
    assert names.container_name("novaact") == "novaact-worker"
    assert names.container_name("midscene") == "midscene-worker"


def test_ssm_path_contains_prefix():
    # SSM 路径含 prefix（cli 已知 prefix 拼路径读 subnet/sg，无循环——ADR 0033）
    assert names.ssm_path("prod-", "subnets") == "/prod-backend/subnets"
    assert names.ssm_path("gherkai-", "security-groups") == "/gherkai-backend/security-groups"


# ---- resolve_cloud_target：入口前端的 flag/env → 各资源终名 + region/profile（ADR 0033 / 0016 决策 C）----
def _clear_aws_env(monkeypatch):
    for k in ("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE", "AWS_RESOURCE_PREFIX",
              "AWS_DDB_TABLE", "AWS_S3_BUCKET"):
        monkeypatch.delenv(k, raising=False)


def test_resolve_cloud_target_derives_all_names_from_prefix(monkeypatch):
    _clear_aws_env(monkeypatch)
    t = compose.resolve_cloud_target(prefix="prod-", region="us-west-2")
    assert (t.prefix, t.region, t.profile) == ("prod-", "us-west-2", None)
    assert (t.runs_table, t.events_table, t.bucket, t.cluster) == (
        "prod-runs", "prod-events", "prod-artifacts", "prod-cluster")
    # 三 Lambda 名同源推导；detached_chain_lambdas 顺序即链上顺序（kicker→reconciler→exit-observer）
    assert t.detached_chain_lambdas == ["prod-kicker", "prod-reconciler", "prod-exit-observer"]


def test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven(monkeypatch):
    _clear_aws_env(monkeypatch)
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "stage-")
    monkeypatch.setenv("AWS_DDB_TABLE", "env-runs")
    monkeypatch.setenv("AWS_S3_BUCKET", "env-bucket")
    monkeypatch.setenv("AWS_PROFILE", "env-prof")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    t = compose.resolve_cloud_target()
    assert (t.prefix, t.profile, t.region) == ("stage-", "env-prof", "eu-west-1")
    assert (t.runs_table, t.bucket) == ("env-runs", "env-bucket")  # 这两个有历史 env 面
    # events 表/cluster **无** env 兜底（保既有 CLI 行为，别为对称乱加）——仍走 prefix 默认名
    assert (t.events_table, t.cluster) == ("stage-events", "stage-cluster")


def test_resolve_cloud_target_flags_win_over_env(monkeypatch):
    _clear_aws_env(monkeypatch)
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "stage-")
    monkeypatch.setenv("AWS_DDB_TABLE", "env-runs")
    monkeypatch.setenv("AWS_PROFILE", "env-prof")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    t = compose.resolve_cloud_target(prefix="prod-", runs_table="flag-runs", bucket="flag-bucket",
                                     events_table="flag-events", cluster="flag-cluster",
                                     profile="flag-prof", region="ap-south-1")
    assert (t.prefix, t.profile, t.region) == ("prod-", "flag-prof", "ap-south-1")
    assert (t.runs_table, t.bucket, t.events_table, t.cluster) == (
        "flag-runs", "flag-bucket", "flag-events", "flag-cluster")
    assert t.kicker_lambda == "prod-kicker"  # 单资源覆盖不影响别的资源仍按 prefix 推导


def test_resolve_cloud_target_default_prefix_when_nothing_given(monkeypatch):
    _clear_aws_env(monkeypatch)
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: None)  # 不摸真 ~/.aws
    t = compose.resolve_cloud_target()
    assert t.prefix == names.DEFAULT_PREFIX and t.runs_table == f"{names.DEFAULT_PREFIX}runs"
    assert t.region is None and t.profile is None  # 真无 → fail-loud，不硬编码 east


# ---- prune_empty_dirs（cloud 清本地空壳，ADR 0029）：只删空目录、非空保留 ----
def test_prune_empty_dirs_removes_empty_tree(tmp_path):
    # worker 上传后 rmtree 了子目录，run 根只剩空壳（含空中间目录）→ 整个删掉
    run_dir = tmp_path / "reports" / "rid"
    (run_dir / "nova-trajectories" / "sess").mkdir(parents=True)  # 全空
    (run_dir / "midscene-run" / "report").mkdir(parents=True)     # 全空
    compose.prune_empty_dirs(run_dir)
    assert not run_dir.exists()  # 空壳整个清掉


def test_prune_empty_dirs_keeps_nonempty(tmp_path):
    # 某个引擎 flush 失败保留了产物（目录非空）→ 该目录及其祖先保留（护栏：不误删产物）
    run_dir = tmp_path / "reports" / "rid"
    kept = run_dir / "nova-trajectories" / "sess"
    kept.mkdir(parents=True)
    (kept / "act_0.html").write_text("残留产物")           # 非空
    (run_dir / "midscene-run").mkdir(parents=True)          # 空
    compose.prune_empty_dirs(run_dir)
    assert run_dir.exists()                                  # 因含非空子树而保留
    assert (kept / "act_0.html").exists()                   # 产物没被误删
    assert not (run_dir / "midscene-run").exists()           # 空的那支仍被清


def test_prune_empty_dirs_noop_when_missing(tmp_path):
    compose.prune_empty_dirs(tmp_path / "nonexistent")  # 不存在 → no-op、不抛


def test_is_botocore_error_classifies():
    from botocore.exceptions import ClientError

    assert compose.is_botocore_error(ClientError({"Error": {"Code": "X"}}, "Op"))
    assert not compose.is_botocore_error(ValueError("不是云端故障"))


# ---- resolve_network（ADR 0033）：subnet/sg 覆盖 or 读 SSM ----
def test_resolve_network_explicit_overrides_skip_ssm():
    # 显式给 subnet/sg → 不读 SSM（ssm 注入一个一调用就抛异常的哨兵，验它没被调）
    class _BoomSsm:
        def get_parameter(self, **kw):
            raise AssertionError("显式给 subnet/sg 时不该读 SSM")
    net = compose.resolve_network(
        prefix="prod-", subnets=["subnet-a", "subnet-b"], security_groups=["sg-1"],
        assign_public_ip="DISABLED", ssm=_BoomSsm(),
    )
    assert net == {"subnets": ["subnet-a", "subnet-b"], "securityGroups": ["sg-1"], "assignPublicIp": "DISABLED"}


def test_resolve_network_reads_ssm_when_missing():
    # 未给 subnet/sg → 读含 prefix 的 SSM 路径（CDK 写的生成 ID，逗号分隔 StringList）
    reads = []

    class _FakeSsm:
        def get_parameter(self, Name):
            reads.append(Name)
            val = "subnet-x,subnet-y" if Name.endswith("subnets") else "sg-z"
            return {"Parameter": {"Value": val}}

    net = compose.resolve_network(prefix="prod-", subnets=None, security_groups=None, ssm=_FakeSsm())
    assert net["subnets"] == ["subnet-x", "subnet-y"]
    assert net["securityGroups"] == ["sg-z"]
    assert reads == ["/prod-backend/subnets", "/prod-backend/security-groups"]  # 路径含 prefix


def test_resolve_network_partial_override_reads_only_missing():
    # 只给 subnet、不给 sg → 只读 sg 的 SSM（subnet 用显式）
    reads = []

    class _FakeSsm:
        def get_parameter(self, Name):
            reads.append(Name)
            return {"Parameter": {"Value": "sg-only"}}

    net = compose.resolve_network(prefix="g-", subnets=["subnet-explicit"], security_groups=None, ssm=_FakeSsm())
    assert net["subnets"] == ["subnet-explicit"]
    assert net["securityGroups"] == ["sg-only"]
    assert reads == ["/g-backend/security-groups"]  # 只读缺的那个


def test_resolve_network_empty_ssm_fails_fast():
    # 空值 fail-fast（低频加固，ADR 0033）：SSM 参数空（值空串 → split 过滤后 []）→ 就地报错点名路径，
    # 不把空列表传到 awsvpcConfiguration、拖到 RunTask 才失败。空串 / 纯逗号 两种空形态都拦。
    import pytest

    class _EmptySsm:
        def __init__(self, val): self._val = val
        def get_parameter(self, Name):
            return {"Parameter": {"Value": self._val}}

    for empty_val in ("", ",", ",,"):  # 空串 / 逗号无值——过滤后都是 []
        with pytest.raises(ValueError, match="为空"):
            compose.resolve_network(prefix="g-", subnets=None, security_groups=None, ssm=_EmptySsm(empty_val))
    # 错误须点名是哪个 SSM 路径（subnets 先读、先报错）
    try:
        compose.resolve_network(prefix="g-", subnets=None, security_groups=None, ssm=_EmptySsm(""))
        assert False, "应 fail-fast"
    except ValueError as e:
        assert "/g-backend/subnets" in str(e)  # 点名路径，便于排障


# ---- build_fargate_engines（ADR 0033/0016 决策 A/C + 0038 显式 revision）----
_REV = {"novaact": "arn:aws:ecs:us-west-2:1:task-definition/prod-novaact-worker:7",
        "midscene": "arn:aws:ecs:us-west-2:1:task-definition/prod-midscene-worker:3"}


def test_build_fargate_engines_per_engine_taskdef_and_region_no_profile(monkeypatch):
    # 注入 fake FargateEngine 捕获构造参数（不连 AWS、不 require boto3）
    import gherkai_core.adapters.fargate_engine as fe
    captured = []

    class _FakeFargate:
        def __init__(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr(fe, "FargateEngine", _FakeFargate)
    engines = compose.build_fargate_engines(
        run_id="rid-1", cluster="prod-cluster", events_table="prod-events",
        bucket="prod-artifacts", report_dir="runs", network_config={"subnets": ["subnet-x"]},
        worker_task_defs=_REV, region="us-west-2", profile="myprof",
        ecs=object(), s3=object(), ddb_events_table=object(),  # 注入句柄免惰性建
    )
    assert set(engines) == {"novaact", "midscene"}
    by_engine = {k["task_definition"]: k for k in captured}
    # **显式 revision ARN**（ADR 0038 不变量：永不传 family 名——family 取最新 ACTIVE 会被任何一次 push 劫持）
    assert set(by_engine) == set(_REV.values())
    nova = by_engine[_REV["novaact"]]
    assert nova["container_name"] == "novaact-worker"
    assert nova["run_id"] == "rid-1" and nova["cluster"] == "prod-cluster"
    assert nova["events_table_name"] == "prod-events"
    assert nova["region"] == "us-west-2"          # region 注入（决策 C）
    assert "profile" not in nova                    # **profile 不传 FargateEngine**（正确非对称，决策 C）
    # job_s3 = (bucket, "{report_dir}/{run_id}/jobs-in/")——**jobs-in/ 非 jobs/**（避与 ResultStore 判定 key 撞，实际运行暴露）
    assert nova["job_s3"] == ("prod-artifacts", "runs/rid-1/jobs-in/")
    # artifact_s3 = (bucket, "{report_dir}/{run_id}/")——**cloud 必注入**（否则容器盘销毁产物必丢，ADR 0029）
    assert nova["artifact_s3"] == ("prod-artifacts", "runs/rid-1/")
    # SDK 产物落点 env（按引擎、容器内路径）——**uploader 靠它算 run_dir，缺它 no-op 报 file://、产物丢**（实际运行暴露）。
    assert nova["sdk_artifact_dir_env"] == {"NOVA_LOGS_DIR": "/tmp/gherkai-run/rid-1/nova-trajectories"}
    # Nova act timeout **双端同源**（ADR 0024 grace 硬约束）：云端后端也须显式注入——容器不继承本地 env，
    # 缺它则 worker 落回自带字面量、调 NOVA_ACT_TIMEOUT_S 只抬高 grace 下限、改不动容器内单 act 上界。
    assert nova["extra_env"]["NOVA_ACT_TIMEOUT_S"] == str(compose.nova_act_timeout_s())
    mid = by_engine[_REV["midscene"]]
    assert mid["sdk_artifact_dir_env"] == {"MIDSCENE_RUN_DIR": "/tmp/gherkai-run/rid-1/midscene-run"}
    assert "NOVA_ACT_TIMEOUT_S" not in mid["extra_env"]  # 引擎特定值只给该引擎（Midscene 无可控 act timeout）


# ---- build_cloud_stores（ADR 0016 组合根注入 / 0030 决定七 offloader 默认挂载）----

def _fake_store_ctors(monkeypatch) -> dict:
    """把 build_cloud_stores 用的四个 adapter 换成只记构造参数的 fake（不 require boto3、不连 AWS）。"""
    import gherkai_core.adapters.report_store.s3 as _rp
    import gherkai_core.adapters.result_store.s3 as _rs
    import gherkai_core.adapters.run_store.arg_offload as _ao
    import gherkai_core.adapters.run_store.ddb as _ddb
    seen: dict = {}

    def _rec(name):
        def _ctor(*args, **kwargs):
            seen[name] = (args, kwargs)
            return f"<{name}>"
        return _ctor

    monkeypatch.setattr(_ao, "S3StepArgumentOffloader", _rec("offloader"))
    monkeypatch.setattr(_ddb, "DynamoDBRunStore", _rec("run_store"))
    monkeypatch.setattr(_rs, "S3ResultStore", _rec("result_store"))
    monkeypatch.setattr(_rp, "S3ReportStore", _rec("report_store"))
    return seen


def test_build_cloud_stores_uses_injected_handles_without_building_clients(monkeypatch):
    """注入 ddb_table/s3 → 原样喂给 store，绝不另建 client（Lambda 组合根靠这条复用它已建的那批句柄，
    而不是手工重造这套装配——重造那份的 prefix 规范化与 offloader 挂载会各自漂）。"""
    seen = _fake_store_ctors(monkeypatch)

    def _boom(*a, **kw):
        raise AssertionError("注入句柄后不该再建 client")

    monkeypatch.setattr(compose, "_make_ddb_table", _boom)
    monkeypatch.setattr(compose, "_make_s3_client", _boom)
    ddb_table, s3 = object(), object()
    run_store, result_store, report_store, _mk = compose.build_cloud_stores(
        table="prod-runs", bucket="prod-artifacts", prefix="reports", region="us-west-2",
        ddb_table=ddb_table, s3=s3)

    assert (run_store, result_store, report_store) == ("<run_store>", "<result_store>", "<report_store>")
    assert seen["run_store"][0] == (ddb_table,)     # DDB 吃注入的 resource.Table，不另建
    # 三个 S3 件套共享注入的那**一个** client（喂错句柄类型运行时才 AttributeError，ADR 0016），
    # prefix 规范化仍由本函数一处做（"reports" → "reports/"，避粘连 key）
    for name in ("offloader", "result_store", "report_store"):
        assert seen[name][0] == (s3, "prod-artifacts", "reports/")
    # offloader 默认挂载（ADR 0030 决定七）：漏挂则 META 里的 content_ref 正文静默还原成 None；列举用的索引名由这里注入
    # （命名真源在 runtime，ADR 0041 决策七）
    assert seen["run_store"][1] == {"arg_offloader": "<offloader>", "detached": False,
                                    "list_index_name": names.RUNS_STATUS_RUN_ID_GSI}


def test_build_cloud_stores_builds_handles_when_not_injected(monkeypatch):
    """不注入则走 _make_* 钩子惰性建（table/region/profile 照传）——注入是可选口子、不改默认路径。"""
    seen = _fake_store_ctors(monkeypatch)
    made = {}
    monkeypatch.setattr(compose, "_make_ddb_table",
                        lambda table, *, region, profile: made.setdefault("ddb", (table, region, profile)))
    monkeypatch.setattr(compose, "_make_s3_client",
                        lambda *, region, profile: made.setdefault("s3", (region, profile)))
    compose.build_cloud_stores(table="prod-runs", bucket="prod-artifacts", prefix="reports",
                               region="us-west-2", profile="myprof", detached=True)

    assert made["ddb"] == ("prod-runs", "us-west-2", "myprof")
    assert made["s3"] == ("us-west-2", "myprof")
    assert seen["run_store"][0] == (made["ddb"],)               # 建出来的句柄就是喂进去的那个
    assert seen["result_store"][0] == (made["s3"], "prod-artifacts", "reports/")
    assert seen["run_store"][1]["detached"] is True             # submit 方式标记透传（ADR 0034）


# ---- list-runs 的云端装配（ADR 0041 决策七）：索引就绪检查在装配路径上，DescribeTable 用 moto 模拟响应 ----

def _moto_runs_table(*, with_list_index: bool):
    """moto 下建一张 runs 表（主键 run_id 与 item_type，与部署侧的键结构相同）：with_list_index 决定有没有列举用的 GSI。"""
    import boto3
    gsis = [{"IndexName": names.RUNS_STATUS_GSI, "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}],
             "Projection": {"ProjectionType": "KEYS_ONLY"}}]
    if with_list_index:
        gsis.append({"IndexName": names.RUNS_STATUS_RUN_ID_GSI,
                     "KeySchema": [{"AttributeName": "status", "KeyType": "HASH"}, {"AttributeName": "run_id", "KeyType": "RANGE"}],
                     "Projection": {"ProjectionType": "KEYS_ONLY"}})
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    return ddb.create_table(
        TableName="vfy-runs", BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"}, {"AttributeName": "item_type", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": a, "AttributeType": "S"} for a in ("run_id", "item_type", "status")],
        GlobalSecondaryIndexes=gsis)


@pytest.mark.parametrize("with_list_index", [True, False])
def test_build_cloud_run_list_store_checks_the_index_before_assembling(with_list_index, monkeypatch):
    """索引就绪（moto 建出的 GSI 为 ACTIVE）才装配出能列举的 store；索引缺失抛产品语言的整句、点名表与索引，不装配。
    只读命令不起 S3 client。"""
    from moto import mock_aws

    for k, v in (("AWS_ACCESS_KEY_ID", "testing"), ("AWS_SECRET_ACCESS_KEY", "testing"), ("AWS_DEFAULT_REGION", "us-east-1")):
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(compose, "_make_s3_client", lambda **kw: pytest.fail("清单不该起 S3 client"))
    with mock_aws():
        table = _moto_runs_table(with_list_index=with_list_index)
        if not with_list_index:
            with pytest.raises(compose.RunListIndexUnavailable, match=f"vfy-runs.*{names.RUNS_STATUS_RUN_ID_GSI}"):
                compose.build_cloud_run_list_store(table="vfy-runs", ddb_table=table)
            return
        from gherkai_core.model import Status

        store = compose.build_cloud_run_list_store(table="vfy-runs", ddb_table=table)
        assert store.list_runs([Status.PENDING, Status.RUNNING], limit=None) == []  # 注入了索引名：能对它 Query


@pytest.mark.parametrize("status, ok", [("ACTIVE", True), ("UPDATING", True), ("CREATING", False), ("DELETING", False),
                                        ("SOMETHING_NEW", False)])
def test_check_run_list_index_lets_active_and_updating_through(status, ok):
    """判据取自 DescribeTable 的 IndexStatus：ACTIVE 与 UPDATING 放行，回填中、删除中与不认识的状态都拦下。"""
    from types import SimpleNamespace

    def describe_table(*, TableName):
        return {"Table": {"GlobalSecondaryIndexes": [{"IndexName": names.RUNS_STATUS_RUN_ID_GSI, "IndexStatus": status}]}}

    table = SimpleNamespace(name="t", meta=SimpleNamespace(client=SimpleNamespace(describe_table=describe_table)))
    if ok:
        compose.check_run_list_index(table)
    else:
        with pytest.raises(compose.RunListIndexUnavailable):
            compose.check_run_list_index(table)


def test_run_list_locations_are_the_single_source_of_the_list_runs_top_level_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert compose.local_run_list_location("reports") == {"backend": "local", "report_dir": str((tmp_path / "reports").resolve())}
    assert compose.cloud_run_list_location(prefix="p-", region="us-east-1", table="p-runs") == {
        "backend": "cloud", "prefix": "p-", "region": "us-east-1", "ddb_table": "p-runs"}


# ---- preflight_cloud_resources（ADR 0033）：探资源存在性、缺则点名 prefix ----
class _FakeDdbClient:
    def __init__(self, existing):
        self._existing = existing
    def describe_table(self, TableName):
        if TableName not in self._existing:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "x"}}, "DescribeTable")
        return {"Table": {"TableName": TableName}}


class _FakeS3Client:
    def __init__(self, existing):
        self._existing = existing
    def head_bucket(self, Bucket):
        if Bucket not in self._existing:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "404", "Message": "x"}}, "HeadBucket")


class _FakeEcsClient:
    def __init__(self, active, task_defs=()):
        self._active = active
        self._task_defs = set(task_defs)
    def describe_clusters(self, clusters):
        return {"clusters": [{"status": "ACTIVE" if c in self._active else "INACTIVE"} for c in clusters]}
    def describe_task_definition(self, taskDefinition):
        if taskDefinition not in self._task_defs:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "ClientException", "Message": "Unable to describe task definition"}},
                              "DescribeTaskDefinition")
        return {"taskDefinition": {"family": taskDefinition}}


class _FakeLambdaClient:
    def __init__(self, existing, env_by_fn=None):
        self._existing = set(existing)
        self._env_by_fn = env_by_fn or {}  # fn → env dict（缺项表示该 Lambda 没配 env，同真实返回体省略 Environment）

    def get_function(self, FunctionName):
        if FunctionName not in self._existing:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "x"}}, "GetFunction")
        cfg = {"FunctionName": FunctionName}
        if FunctionName in self._env_by_fn:
            cfg["Environment"] = {"Variables": dict(self._env_by_fn[FunctionName])}
        return {"Configuration": cfg}


def test_preflight_all_present_returns_none():
    err = compose.preflight_cloud_resources(
        prefix="gherkai-", runs_table="gherkai-runs", events_table="gherkai-events",
        bucket="gherkai-artifacts", cluster="gherkai-cluster",
        ddb=_FakeDdbClient({"gherkai-runs", "gherkai-events"}),
        s3=_FakeS3Client({"gherkai-artifacts"}),
        ecs=_FakeEcsClient({"gherkai-cluster"}),
    )
    assert err is None


def test_preflight_missing_events_table_names_prefix():
    err = compose.preflight_cloud_resources(
        prefix="prod-", runs_table="prod-runs", events_table="prod-events",
        bucket="prod-artifacts", cluster="prod-cluster",
        ddb=_FakeDdbClient({"prod-runs"}),  # events 表缺
        s3=_FakeS3Client({"prod-artifacts"}),
        ecs=_FakeEcsClient({"prod-cluster"}),
    )
    assert err is not None
    assert "prod-events" in err and "--prefix='prod-'" in err and "gherkai deploy" in err  # 点名 prefix + 引导


def test_preflight_missing_task_def_names_prefix():
    # task-def 维度的 prefix 配错（原先漏到 RunTask 才失败、退出码 1 且不点名）→ 现 preflight 点名 fail-fast（ADR 0033）
    err = compose.preflight_cloud_resources(
        prefix="prod-", events_table="prod-events", bucket="prod-artifacts", cluster="prod-cluster",
        task_defs=["prod-novaact-worker"],
        ddb=_FakeDdbClient({"prod-events"}), s3=_FakeS3Client({"prod-artifacts"}),
        ecs=_FakeEcsClient({"prod-cluster"}),  # task-def 集为空 → 缺
    )
    assert err is not None
    assert "prod-novaact-worker" in err and "--prefix='prod-'" in err


def test_preflight_missing_chain_lambda_names_prefix():
    # detached 链三 Lambda 任一缺即提交成功但 run 永不推进/收敛 → 挡在提交前（ADR 0033）
    err = compose.preflight_cloud_resources(
        prefix="g-", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        lambda_fns=["g-kicker", "g-reconciler", "g-exit-observer"],
        ddb=_FakeDdbClient({"g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient({"g-kicker", "g-exit-observer"}),  # reconciler 缺
    )
    assert err is not None and "g-reconciler" in err
    assert "后台运行" in err  # 说使用者能指认的用途，不说内部机制名


def test_preflight_task_defs_and_lambdas_all_present():
    err = compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        task_defs=["g-novaact-worker", "g-midscene-worker"],
        lambda_fns=["g-kicker", "g-reconciler", "g-exit-observer"],
        ddb=_FakeDdbClient({"g-runs", "g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}, task_defs={"g-novaact-worker", "g-midscene-worker"}),
        lam=_FakeLambdaClient({"g-kicker", "g-reconciler", "g-exit-observer"}),
    )
    assert err is None


# ---- preflight 的产物前缀一致性（ADR 0033）：--report-dir vs 推进器 REPORT_DIR ----
_CHAIN = ["g-kicker", "g-reconciler", "g-exit-observer"]


def _preflight_report_dir(report_dir, env_by_fn=None):
    return compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts",
        cluster="g-cluster", lambda_fns=_CHAIN, report_dir=report_dir,
        ddb=_FakeDdbClient({"g-runs", "g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient(_CHAIN, env_by_fn=env_by_fn),
    )


def test_preflight_report_dir_mismatch_fails_fast_naming_both_sides():
    # --report-dir 与推进器 REPORT_DIR 分裂即运行完成但结果落在提交者没指定的前缀下（静默分裂）→ 挡在提交前、点名两侧值。
    # kicker 对上、reconciler 没对上 → 两个推进器都比（不是只看第一个）
    err = _preflight_report_dir("mine", env_by_fn={"g-kicker": {"REPORT_DIR": "mine"},
                                                  "g-reconciler": {"REPORT_DIR": "reports"}})
    assert err is not None
    assert "'mine'" in err and "'reports'" in err and "g-reconciler" in err


def test_preflight_report_dir_mismatch_detected_when_lambda_env_absent():
    # 推进器没配 REPORT_DIR（IaC 有意不注入、Lambda 内缺省 reports）→ 缺键视作 reports，非默认 --report-dir 仍要拦
    err = _preflight_report_dir("mine")
    assert err is not None and "'reports'" in err


def test_preflight_report_dir_match_returns_none():
    # 对偶（防「恒报错」）：两侧一致 → 放行；尾斜杠差异不算冲突（同 S3 前缀规范化）
    assert _preflight_report_dir("reports") is None
    assert _preflight_report_dir("reports/") is None
    assert _preflight_report_dir("mine", env_by_fn={fn: {"REPORT_DIR": "mine"} for fn in _CHAIN}) is None


def test_preflight_report_dir_ignores_exit_observer_env():
    # exit-observer 不读 REPORT_DIR（只写 task_exited）→ 它的 env 不参与比对，别拿它造假冲突
    assert _preflight_report_dir(
        "mine", env_by_fn={"g-kicker": {"REPORT_DIR": "mine"}, "g-reconciler": {"REPORT_DIR": "mine"},
                           "g-exit-observer": {"REPORT_DIR": "reports"}}) is None


def test_preflight_report_dir_not_checked_when_not_passed():
    # 同步 run 不传 report_dir（也不传 lambda_fns）→ 一致性探针整体不生效，只探存在性
    assert _preflight_report_dir(None, env_by_fn={"g-reconciler": {"REPORT_DIR": "whatever"}}) is None


# ---- preflight 的「声明超部署侧 cap」提示（ADR 0034 机制四）：警但不失败 ----

def _preflight_cap(declared, cap_env, warns):
    """运行一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。"""
    return compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts",
        cluster="g-cluster", lambda_fns=_CHAIN,
        declared_max_concurrency=declared, on_warn=warns.append,
        ddb=_FakeDdbClient({"g-runs", "g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient(_CHAIN, env_by_fn={fn: {"MAX_CONCURRENCY": cap_env} for fn in _CHAIN}),
    )


def test_preflight_warns_once_when_declared_max_concurrency_exceeds_cap():
    # 声明 8 > cap 4 → 提交时就告知「本 run 只会按 4 并行」（否则提交者以为按 8 运行、只看到莫名慢）。
    # 但**不构成 preflight 失败**：钳制不改产物落点、run 照常运行（对照 REPORT_DIR 分岔的退出码为 2——判据是分岔后果）。
    warns = []
    err = _preflight_cap(8, "4", warns)
    assert err is None                       # 只警不拦
    assert len(warns) == 1                   # 两推进器同值 → 只警一条，不重复噪声
    assert "8" in warns[0] and "4" in warns[0] and "MAX_CONCURRENCY" in warns[0]


def test_preflight_no_cap_warn_when_declared_within_cap():
    # 对偶（防「恒警」）：声明 2 ≤ cap 4 → 一句不警（提交侧在 cap 以内说了算，没有钳制发生）。
    warns = []
    assert _preflight_cap(2, "4", warns) is None
    assert warns == []


def test_preflight_missing_cluster_detected():
    err = compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        ddb=_FakeDdbClient({"g-runs", "g-events"}),
        s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient(set()),  # cluster 非 ACTIVE
    )
    assert err is not None and "g-cluster" in err


# ---- 自述入口（ADR 0036）：spawn worker 收 JSON、fake subprocess ----

@pytest.fixture
def novaact_env_cmd(monkeypatch):
    """定位链第一级固定一个假 novaact cmd：自述用例只验「组合根怎么拼命令/收结果」，不依赖本机装了什么。"""
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CMD", "/fake/novaact-worker")
    monkeypatch.setenv("GHERKAI_WORKER_MIDSCENE_CMD", "/fake/midscene-worker")
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CWD", raising=False)
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CWD", raising=False)


def test_self_describe_miss_raises_worker_not_found(monkeypatch, fresh_caps_cache):
    """定位链 miss 时**两个非 job 入口**都抛 WorkerNotFoundError（取不到里专带安装指引的一种）——
    调用点据此分叉：list-deterministic / run 以退出码 2 结束并打安装指引、plan 标注降级（它是 WorkerUnavailableError 的子类，
    plan 按取不到处置，ADR 0036「5.」末段）。"""
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    with pytest.raises(compose.WorkerNotFoundError) as ei:
        compose.query_capabilities("midscene")
    assert isinstance(ei.value, compose.WorkerUnavailableError) and ei.value.engine == "midscene"
    with pytest.raises(compose.WorkerNotFoundError):
        compose.match_deterministic("midscene", [{"keyword": None, "text": "a"}])


def test_match_deterministic_feeds_stdin_and_parses(monkeypatch, novaact_env_cmd):
    import subprocess

    class _P:
        returncode = 0
        stdout = b'[{"pattern": "p", "description": "d"}, null]'
        stderr = b""

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"], captured["input"] = cmd, kw.get("input")
        return _P()

    monkeypatch.setattr(subprocess, "run", fake_run)
    plain = [{"keyword": None, "text": "a"}, {"keyword": None, "text": "b"}]
    got = compose.match_deterministic("midscene", plain)
    assert got == [{"pattern": "p", "description": "d"}, None]
    assert captured["cmd"][-1] == "--match-steps"
    import json as _json
    assert _json.loads(captured["input"].decode()) == plain  # keyword 为 null 照样写出这个键（缺键是版本不一致，ADR 0036 决策 4）
    # 每项 {keyword, text} 原样送进 stdin（ADR 0036 决策 4、0050 决策 1），四态里的 keyword_mismatch 原样回传
    _P.stdout = b'[{"keyword_mismatch": "nav", "keywords": ["Given", "When"]}, null]'
    items = [{"keyword": "Then", "text": '"https://x.example/"'}, {"keyword": "When", "text": "没有这条"}]
    assert compose.match_deterministic("midscene", items) == [{"keyword_mismatch": "nav", "keywords": ["Given", "When"]}, None]
    assert _json.loads(captured["input"].decode()) == items
    # 失败文案是用户可见文本（plan 以它收尾、退出码 2）：说「确定性 step 查询失败」，不带 --match-steps 这类协议名（ADR 0039）
    _P.returncode, _P.stderr = 2, b"demo.py: SyntaxError"
    with pytest.raises(compose.WorkerSelfDescribeError) as ei:
        compose.match_deterministic("midscene", items)
    assert "确定性 step 查询失败" in str(ei.value) and "match" not in str(ei.value).lower()
    # worker 拒绝输入形状时写的那一句原样进异常文本（plan 以退出码 2 结束时转述它，ADR 0036 决策 4）
    sentence = "收到的确定性 step 查询不是这个 worker 认的格式：命令行工具与 worker 的版本不一致，请把两者装成同一版本。"
    _P.returncode, _P.stderr = 2, f"worker: {sentence}\n".encode()
    with pytest.raises(compose.WorkerSelfDescribeError) as ei:
        compose.match_deterministic("midscene", items)
    assert sentence in str(ei.value)


# ---- read_task_def_stop_timeout（doctor 的 cloud 侧对照值，ADR 0032 真容器校准结论 4）----

class _StopTimeoutEcs:
    def __init__(self, containers: list[dict]):
        self._containers, self.asked = containers, []

    def describe_task_definition(self, *, taskDefinition):
        self.asked.append(taskDefinition)
        return {"taskDefinition": {"containerDefinitions": self._containers}}


def test_read_task_def_stop_timeout_reads_worker_container():
    # 按 container 名（与 IaC 同源的 `{engine}-worker`）认，不取碰巧第一个 container 的值
    ecs = _StopTimeoutEcs([{"name": "sidecar", "stopTimeout": 5},
                           {"name": names.container_name("novaact"), "stopTimeout": 120}])
    assert compose.read_task_def_stop_timeout("arn:td:7", engine="novaact", ecs=ecs) == 120
    assert ecs.asked == ["arn:td:7"]


def test_read_task_def_stop_timeout_none_when_unset_or_container_absent():
    # 没设 stopTimeout / task-def 里没这个 container → None（「比不了」，调用方不猜值）
    assert compose.read_task_def_stop_timeout(
        "arn:td:7", engine="novaact",
        ecs=_StopTimeoutEcs([{"name": names.container_name("novaact")}])) is None
    assert compose.read_task_def_stop_timeout(
        "arn:td:7", engine="novaact", ecs=_StopTimeoutEcs([{"name": "other", "stopTimeout": 90}])) is None


# ---- 云端同步 run 的停止后等待预算（ADR 0034 机制二「停止后继续有界消费完整事件流」条）：stopTimeout 随 variant 解析带回 ----

class _VariantAws:
    """variant 解析要读的三个面（SSM 映射、ECS revision、ECR 镜像）的最小假替身：每个引擎的 revision 都 ACTIVE、镜像都在，
    task-def 的 containerDefinitions 按引擎给定。只为验 stop_timeout_s 的取法；解析的 miss 分支由 moto 覆盖（test_worker_variant）。"""

    def __init__(self, containers_by_engine: dict[str, list[dict]]):
        self._containers = containers_by_engine
        self.describes: list[str] = []
        outer = self

        class _Ssm:
            def get_parameter(self, *, Name):
                engine = next(e for e in outer._containers if f"/{e}/" in Name)
                return {"Parameter": {"Value": json.dumps({"revision_arn": f"arn:td/{engine}:3", "digest": "sha256:0"})}}

        class _Ecs:
            def describe_task_definition(self, *, taskDefinition):
                outer.describes.append(taskDefinition)
                engine = taskDefinition.split("/")[1].split(":")[0]
                return {"taskDefinition": {"status": "ACTIVE", "containerDefinitions": outer._containers[engine]}}

        class _Ecr:
            def describe_images(self, **kw):
                return {"imageDetails": [{}]}

        self.ssm, self.ecs, self.ecr = _Ssm(), _Ecs(), _Ecr()

    def resolve(self):
        return compose.resolve_worker_variant(
            prefix="t-", variant="base", engines=sorted(self._containers), cli_version="1.5.0", backend_version="1.5.0",
            ssm=self.ssm, ecs=self.ecs, ecr=self.ecr)


@pytest.mark.parametrize("containers, expected", [
    ([{"name": "sidecar", "stopTimeout": 5}, {"name": names.container_name("novaact"), "stopTimeout": 90}], 90),  # 按名认，不取第一个
    ([{"name": names.container_name("novaact")}], None),  # 该 container 没设 stopTimeout
    ([{"name": "not-the-worker", "stopTimeout": 60}], None),  # task-def 里找不到该 container
], ids=["set", "unset", "container-absent"])
def test_resolve_worker_variant_carries_worker_container_stop_timeout(containers, expected):
    # 认法与 doctor 比对用的 read_task_def_stop_timeout 同一份；取自校验 revision 仍 ACTIVE 的那次 Describe，不另发调用
    aws = _VariantAws({"novaact": containers, "midscene": [{"name": names.container_name("midscene"), "stopTimeout": 30}]})
    got = aws.resolve()
    assert {e: r.stop_timeout_s for e, r in got.items()} == {"novaact": expected, "midscene": 30}
    assert sorted(aws.describes) == sorted(r.revision_arn for r in got.values())  # 每个引擎恰一次
    assert compose.read_task_def_stop_timeout(got["novaact"].revision_arn, engine="novaact", ecs=aws.ecs) == expected


def _res(engine: str, stop_timeout_s):
    return compose.WorkerResolution(engine=engine, variant="base", revision_arn=f"arn:{engine}", digest="sha256:0",
                                    stop_timeout_s=stop_timeout_s)


def test_cloud_stop_bound_takes_max_stop_timeout_plus_ecs_stopped_lag():
    # 各引擎 stopTimeout 取最大，再加 ECS 记下 STOPPED 的滞后余量；不含 core 的排空余量
    assert compose.cloud_stop_bound_s([_res("novaact", 90), _res("midscene", 30)]) == 90 + compose.ECS_STOPPED_LAG_MARGIN_S
    assert compose.cloud_stop_bound_s([_res("midscene", 30)]) == 30 + 20.0
    # 没设 / 找不到 container（None）按 Fargate 平台上限 120 秒计：预算宁大勿小，即使别的引擎设得更小
    assert compose.cloud_stop_bound_s([_res("novaact", None), _res("midscene", 30)]) == 120 + 20.0
    assert compose.FARGATE_STOP_TIMEOUT_MAX_S == 120
    assert compose.cloud_stop_bound_s([]) == 120 + 20.0


# ---- 版本 skew（ADR 0037 决策 7）：读戳 + 三态齐全 + 非纯净跳过 ----

class _StampSsm:
    """假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。"""

    def __init__(self, value, *, error=None):
        self.value, self.error, self.reads = value, error, []

    def get_parameter(self, Name):
        self.reads.append(Name)
        if self.error is not None:
            raise self.error
        return {"Parameter": {"Value": self.value}}


def _client_error(code):
    from botocore.exceptions import ClientError

    return ClientError({"Error": {"Code": code, "Message": "x"}}, "GetParameter")


def test_read_backend_version_reads_prefixed_path():
    ssm = _StampSsm("1.4.0")
    assert compose.read_backend_version(prefix="prod-", ssm=ssm) == "1.4.0"
    assert ssm.reads == ["/prod-backend/version"]  # 路径含 prefix，与 subnet/sg 同族


def test_read_backend_version_missing_parameter_is_none_not_raise():
    """`ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。"""
    ssm = _StampSsm(None, error=_client_error("ParameterNotFound"))
    assert compose.read_backend_version(prefix="g-", ssm=ssm) is None


def test_read_backend_version_other_aws_error_propagates():
    """凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。"""
    ssm = _StampSsm(None, error=_client_error("AccessDeniedException"))
    with pytest.raises(Exception) as e:
        compose.read_backend_version(prefix="g-", ssm=ssm)
    assert "AccessDenied" in str(e.value)


def test_read_backend_version_blank_value_is_none():
    assert compose.read_backend_version(prefix="g-", ssm=_StampSsm("  ")) is None


def test_skew_ok_same_release_is_silent():
    verdict, msg = compose.check_version_skew("1.4.0", "1.4.0", prefix="g-")
    assert (verdict, msg) == (compose.SKEW_OK, "")


def test_skew_block_when_cli_newer_names_both_exits():
    """CLI 新于后端 → block，且消息必须点名**两条**出路（决策 7 不设放行口，只有这两条）。"""
    verdict, msg = compose.check_version_skew("1.3.0", "1.4.0", prefix="g-")
    assert verdict == compose.SKEW_BLOCK
    assert "gherkai deploy" in msg                      # ① 部署方升后端
    assert "uvx --from 'gherkai==1.3.0'" in msg         # ② 临时运行同版本 CLI（点名后端版本）
    assert "1.4.0" in msg


def test_skew_warn_when_cli_older():
    verdict, msg = compose.check_version_skew("1.4.0", "1.3.0", prefix="g-")
    assert verdict == compose.SKEW_WARN and "旧于" in msg


def test_skew_warn_when_stamp_missing_points_at_deploy():
    """戳缺失表示本机制之前部署的环境 → warn（不拦）+ 提示运行一次 `gherkai deploy` 写入；消息写出该部署的参数路径、不留占位。"""
    verdict, msg = compose.check_version_skew(None, "1.4.0", prefix="g-")
    assert verdict == compose.SKEW_WARN and "gherkai deploy" in msg
    assert "/g-backend/version" in msg and "<prefix>" not in msg


def test_skew_skip_when_either_side_impure():
    """任一侧带 .dev/.post/本地段 → skip（dev 逐提交前进，逐字比会把每次都判成 skew）。"""
    for stamp, cli in [("1.4.0", "1.4.0.post3.dev0+abc.dirty"), ("1.4.0.dev1", "1.4.0"),
                       ("1.4.0", "1.4.0+local"), ("1.4.0", "0+unknown")]:
        verdict, msg = compose.check_version_skew(stamp, cli, prefix="g-")
        assert verdict == compose.SKEW_SKIP, (stamp, cli)
        assert msg


def test_skew_skip_when_own_version_unknown():
    """未装成包（从源码直接运行）→ 调用点取不到自身版本、传 None → skip，不误判成 skew。"""
    verdict, msg = compose.check_version_skew("1.4.0", None, prefix="g-")
    assert verdict == compose.SKEW_SKIP and msg


def test_skew_compares_release_segment_only():
    """只比 release 段（决策 7）：位数不同补零后比；同 release 段的 rc 与正式版视作同版本。"""
    assert compose.check_version_skew("1.4.0", "1.4", prefix="g-")[0] == compose.SKEW_OK
    assert compose.check_version_skew("1.4", "1.4.0", prefix="g-")[0] == compose.SKEW_OK
    assert compose.check_version_skew("1.4.0", "1.4.0rc1", prefix="g-")[0] == compose.SKEW_OK
    assert compose.check_version_skew("1.4.0", "1.4.1", prefix="g-")[0] == compose.SKEW_BLOCK
    assert compose.check_version_skew("1.4.1", "1.4.0", prefix="g-")[0] == compose.SKEW_WARN


def test_skew_cli_version_is_mandatory_no_runtime_fallback():
    """`cli_version` 必给（决策 7 比的是「写任务定义那一方」的版本）：不缺省成 gherkai-runtime 的版本——
    editable 树里各包版本各自漂，缺省会埋一个只在各包同版本的发行态下才等价的第二真源。"""
    with pytest.raises(TypeError):
        compose.check_version_skew("1.0.0", prefix="g-")  # type: ignore[call-arg]


def test_check_backend_skew_reads_stamp_then_judges():
    """读戳 + 判定一步到位（编排住产品本体，入口前端只翻退出码）。"""
    ssm = _StampSsm("1.3.0")
    verdict, msg, stamp = compose.check_backend_skew(prefix="prod-", cli_version="1.4.0", ssm=ssm)
    assert verdict == compose.SKEW_BLOCK and "gherkai deploy" in msg
    assert stamp == "1.3.0"  # 戳一并返回：调用方的 variant 解析复用，不二次读 SSM
    assert ssm.reads == ["/prod-backend/version"]


def test_check_backend_skew_missing_stamp_warns_not_raises():
    ssm = _StampSsm(None, error=_client_error("ParameterNotFound"))
    verdict, msg, stamp = compose.check_backend_skew(prefix="stage-", cli_version="1.4.0", ssm=ssm)
    assert verdict == compose.SKEW_WARN and "gherkai deploy" in msg and stamp is None
    assert "/stage-backend/version" in msg  # prefix 经 check_backend_skew 传到缺戳消息


def test_check_backend_skew_propagates_read_errors():
    """凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到不等于放过。"""
    from botocore.exceptions import ClientError
    ssm = _StampSsm(None, error=_client_error("AccessDeniedException"))
    with pytest.raises(ClientError):
        compose.check_backend_skew(prefix="g-", cli_version="1.4.0", ssm=ssm)


def test_variant_miss_hint_offers_push_and_base_fallback():
    """同版本这一种情形的 variant miss 提示须同时给两条出路（ADR 0038「升级不重置默认指针」条）：
    让部署方 push-worker，或临时用 --worker-variant base 先运行。"""
    from gherkai_runtime.compose import _variant_miss_hint

    msg = _variant_miss_hint(engine="midscene", variant="common", tag="1.4.0-common",
                             what="SSM 里没有映射", cli_version="1.4.0", backend_version="1.4.0")
    assert "push-worker" in msg and "--variant common" in msg
    assert "--worker-variant base" in msg


def test_variant_miss_hint_older_cli_only_guides_upgrade():
    """CLI 旧于后端那一种判定只引导升级 CLI，不给 push、也不给 base 兜底（推旧命名空间的 tag 是原地绕圈）。"""
    from gherkai_runtime.compose import _variant_miss_hint

    msg = _variant_miss_hint(engine="novaact", variant="common", tag="1.3.0-common",
                             what="SSM 里没有映射", cli_version="1.3.0", backend_version="1.4.0")
    assert "升到后端版本" in msg or "升" in msg
    assert "push-worker" not in msg and "--worker-variant base" not in msg


# ---- run_duration_ms：detached run 级墙钟取 RunState ended_at 减 started_at（ADR 0024「三级执行时长」detached 条）----
def test_run_duration_ms_from_run_state_timestamps():
    from gherkai_core.model import RunState, Status

    st = RunState(run_id="r", status=Status.PASSED, jobs={}, high_water_mark=0,
                  started_at="2026-09-09T09:40:38.625792+00:00", ended_at="2026-09-09T09:42:53.215060+00:00")
    assert compose.run_duration_ms(st) == pytest.approx(134589.268)
    assert compose.run_duration_ms(RunState(run_id="r", status=Status.RUNNING, jobs={}, high_water_mark=0,
                                            started_at="2026-09-09T09:40:38+00:00")) is None  # 未 finalize
    assert compose.run_duration_ms(None) is None
    assert compose.run_duration_ms(RunState(run_id="r", status=Status.PASSED, jobs={}, high_water_mark=0,
                                            started_at="t0", ended_at="t9")) is None  # 解析不了 → 派生指标显「?」，不让收尾失败


# ---- 配置文件层（ADR 0053 决策 2）：排在环境变量之后、默认之前 ----

def test_resolve_region_config_layer_after_env_before_profile_config(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    import boto3

    def _never(*a, **k):
        raise AssertionError("配置文件给了 region 就不该再读 profile config")

    monkeypatch.setattr(boto3.session, "Session", _never)
    assert compose.resolve_region(None, "prof", config_region="eu-west-1") == "eu-west-1"
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")
    assert compose.resolve_region(None, "prof", config_region="eu-west-1") == "ap-south-1"  # 环境变量胜过配置文件
    assert compose.resolve_region("us-west-2", "prof", config_region="eu-west-1") == "us-west-2"


def test_resolve_aws_identity_config_profile_after_env(monkeypatch):
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: (r, p, kw.get("config_region")))
    assert compose.resolve_aws_identity(None, None, config_region="cfg-r", config_profile="cfg-p") == ((None, "cfg-p", "cfg-r"), "cfg-p")
    monkeypatch.setenv("AWS_PROFILE", "env-p")
    assert compose.resolve_aws_identity(None, None, config_profile="cfg-p")[1] == "env-p"
    assert compose.resolve_aws_identity(None, "flag-p", config_profile="cfg-p")[1] == "flag-p"


def test_resolve_cloud_target_config_layer_after_env_before_default(monkeypatch):
    _clear_aws_env(monkeypatch)
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: None)
    t = compose.resolve_cloud_target(config_prefix="cfg-", config_runs_table="cfg-runs", config_bucket="cfg-bucket")
    assert (t.prefix, t.runs_table, t.bucket, t.events_table) == ("cfg-", "cfg-runs", "cfg-bucket", "cfg-events")
    monkeypatch.setenv("AWS_RESOURCE_PREFIX", "env-")
    monkeypatch.setenv("AWS_DDB_TABLE", "env-runs")
    monkeypatch.setenv("AWS_S3_BUCKET", "env-bucket")
    t = compose.resolve_cloud_target(config_prefix="cfg-", config_runs_table="cfg-runs", config_bucket="cfg-bucket")
    assert (t.prefix, t.runs_table, t.bucket) == ("env-", "env-runs", "env-bucket")   # 配置文件不越过环境变量
    t = compose.resolve_cloud_target(prefix="flag-", runs_table="flag-runs", bucket="flag-bucket",
                                     config_prefix="cfg-", config_runs_table="cfg-runs", config_bucket="cfg-bucket")
    assert (t.prefix, t.runs_table, t.bucket) == ("flag-", "flag-runs", "flag-bucket")


# ---- 缺戳例外（ADR 0037 决策 7）：带设备目标或会话预热地址的 run 遇无戳后端即 block ----

def test_skew_missing_stamp_blocks_when_run_requires_it():
    verdict, msg = compose.check_version_skew(None, "1.5.0", prefix="g-", requires_stamp=True)
    assert verdict == compose.SKEW_BLOCK and "没有版本戳" in msg and "gherkai deploy" in msg
    assert "/g-backend/version" in msg and "<prefix>" not in msg
    verdict, msg = compose.check_version_skew(None, "1.5.0", prefix="g-", requires_stamp=False)
    assert verdict == compose.SKEW_WARN
    assert compose.check_version_skew("1.5.0", "1.5.0", prefix="g-", requires_stamp=True) == (compose.SKEW_OK, "")  # 有戳照常比对


def test_run_requires_backend_stamp_predicate():
    from gherkai_core.model import Job, RunMeta, Scenario, Step, Target

    scs = (Scenario(id="f:1", name="n", steps=(Step(0, "When", "x"),)),)
    desktop = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=scs, timeout_s=300.0)
    device = Job(scope_id="a", scope_name="a", engine="midscene", scenarios=scs, timeout_s=1500.0, target=Target(device="android", ui_kind="web"))
    assert compose.run_requires_backend_stamp(RunMeta(run_id="r", created_at="t", jobs=(desktop,))) is False
    assert compose.run_requires_backend_stamp(RunMeta(run_id="r", created_at="t", jobs=(desktop, device))) is True
    assert compose.run_requires_backend_stamp(RunMeta(run_id="r", created_at="t", jobs=(desktop,),
                                                      session_warmup_url="https://h/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T")) is True


def test_capabilities_schema_version_must_be_an_integer(monkeypatch, novaact_env_cmd, fresh_caps_cache):
    """能力自述的协议版本比较整数严格：布尔值、字符串 "2"、浮点数 2.0 都不等于整数 2（与 worker 核 job 行 schemaVersion 的口径对称）。"""
    import subprocess

    for bad in (b"true", b'"2"', b"2.0"):
        payload = b'{"schema_version": ' + bad + b', "engine": "novaact", "min_grace_s": 150, "targets": [{"device": "desktop", "ui_kinds": ["web"]}]' + _OK_TAIL + b'}'
        monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _fake_caps_proc(payload))
        with pytest.raises(compose.WorkerIncompatibleError, match="格式版本"):
            compose.query_capabilities("novaact")
        assert compose._CAPABILITIES_CACHE == {}


def test_step_targets_from_registry_fixture_pass_the_cli_contract_check():
    """worker 由句柄推出的 step 级 targets（跨语言 fixture 的全部合法用例）都能通过 CLI 唯一的自述契约校验（ADR 0049 决策 1、0050 决策 1）：
    两侧 worker 的输出形态与 CLI 的接受形态由同一份 fixture 串起来，推出规则改了而契约没跟上时这条测试失败。"""
    import json
    from pathlib import Path

    fx = json.loads((Path(__file__).resolve().parents[2] / "engines" / "fixtures" / "deterministic-handles.json").read_text(encoding="utf-8"))
    for case in fx["valid"]:
        compose._validate_targets("midscene", case["targets"], where=f"确定性 step（{case['name']}）", top_level=False)


def test_session_warmup_url_is_owned_env_injected_to_both_engines_and_scrubbed_otherwise(monkeypatch, midscene_env_cmd):
    """会话预热地址（ADR 0051 决策 13）是组合根拥有的 worker env：有值注给两个引擎、无值时宿主继承的同名值被清掉（随 definition 走，
    三个宿主下同一个 run 用同一个值）。"""
    assert "GHERKAI_SESSION_WARMUP_URL" in compose._COMPOSE_OWNED_WORKER_ENV
    url = "https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "a" * 32
    engines = compose.build_engines(run_id=_RUN_ID, extra_http_headers={"ngrok-skip-browser-warning": "1"}, session_warmup_url=url)
    for name in ("novaact", "midscene"):
        assert engines[name]._env["GHERKAI_SESSION_WARMUP_URL"] == url, name
    monkeypatch.setenv("GHERKAI_SESSION_WARMUP_URL", "https://leaked/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=x")
    engines2 = compose.build_engines(run_id=_RUN_ID)
    for name in ("novaact", "midscene"):
        env2 = engines2[name]._env
        assert env2 is not None and "GHERKAI_SESSION_WARMUP_URL" not in env2, name


def test_run_id_is_required_owned_env_injected_to_both_engines(monkeypatch, midscene_env_cmd):
    """本 run 的 id（ADR 0024「run_id + scope_id 注入 worker」条、ADR 0037 决策 4）是组合根拥有的 worker env、build_engines 的必给参数：
    以 RUN_ID 注给两个引擎，与云端 RunTask overrides 同名（worker 用它编码会话名的 run 段）；宿主 shell 里继承的同名值被入参覆盖——
    会话名里的 run 段只认组合根给的值。漏传在装配点报 TypeError、空值报 ValueError，不留到 worker 建会话前才退出。
    本机不注 SCOPE_ID，也不注 EVENTS_DDB_TABLE：worker 的事件出口仍是 fd 态。"""
    assert "RUN_ID" in compose._COMPOSE_OWNED_WORKER_ENV
    monkeypatch.setenv("RUN_ID", "host-run")
    engines = compose.build_engines(run_id="20261030T000000Z-def456")
    for name in ("novaact", "midscene"):
        env = engines[name]._env
        assert env["RUN_ID"] == "20261030T000000Z-def456", name
        assert "SCOPE_ID" not in env and "EVENTS_DDB_TABLE" not in env, name
    with pytest.raises(TypeError, match="run_id"):
        compose.build_engines()
    for bad in ("", None):
        with pytest.raises(ValueError, match="run_id"):
            compose.build_engines(run_id=bad)


def test_fargate_engines_leave_run_id_to_the_engine_adapter(monkeypatch):
    """云端后端的 RUN_ID 由执行 adapter（core 的 FargateEngine）随 SCOPE_ID 一起写进 RunTask overrides：组合根只经 run_id 参数交给它，
    附加 env 里不再出现同名键，否则 overrides 里同一个键会有两项。"""
    from gherkai_core.adapters import fargate_engine as fe

    captured: list = []

    class _FakeFargate:
        def __init__(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr(fe, "FargateEngine", _FakeFargate)
    compose.build_fargate_engines(run_id="rid-1", cluster="c", events_table="e", bucket="b", report_dir="runs",
                                  network_config={"subnets": ["subnet-x"]},
                                  worker_task_defs={"novaact": "arn:rev:1", "midscene": "arn:rev:2"},
                                  region="us-west-2", ecs=object(), s3=object(), ddb_events_table=object())
    assert len(captured) == 2
    assert all(k["run_id"] == "rid-1" and "RUN_ID" not in k["extra_env"] for k in captured)


def test_fargate_engines_carry_session_warmup_url_in_extra_env_only_when_given(monkeypatch):
    """云端后端：预热地址随额外请求头一起进 RunTask overrides 的 env（容器不继承宿主 env，必须显式注）；无值时不出现该键。"""
    from gherkai_core.adapters import fargate_engine as fe

    captured: list = []

    class _FakeFargate:
        def __init__(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr(fe, "FargateEngine", _FakeFargate)
    common = dict(run_id="rid-1", cluster="c", events_table="e", bucket="b", report_dir="runs",
                  network_config={"subnets": ["subnet-x"]}, worker_task_defs={"novaact": "arn:rev:1", "midscene": "arn:rev:2"},
                  region="us-west-2", ecs=object(), s3=object(), ddb_events_table=object())
    url = "https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "a" * 32
    compose.build_fargate_engines(extra_http_headers={"ngrok-skip-browser-warning": "1"}, session_warmup_url=url, **common)
    assert all(k["extra_env"]["GHERKAI_SESSION_WARMUP_URL"] == url for k in captured)
    captured.clear()
    compose.build_fargate_engines(**common)
    assert all("GHERKAI_SESSION_WARMUP_URL" not in k["extra_env"] for k in captured)
