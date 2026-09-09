"""compose（组合根逻辑）单测：不起任何子进程、零费用。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from gherkai_runtime import compose
from gherkai_core.scope import FeatureSource


# dev 环境里 midscene 恒走定位链第一级（env 覆写）——它没有已安装的 npm 包、也没有 PATH 上的 bin
# （ADR 0037 决策 3「contributor 代价点」）。build_engines 的 env 注入类断言要两条腿都是真 SubprocessEngine，
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
    # _CWD 是**可选**配套：不给则 cwd=None＝继承调用者 CWD（worker 不再有专属 cwd）
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

    悄悄换用别的 worker（或报「没装」）是最难查的错：用户明确指了一个，就该告诉他这一个哪儿不对。
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
    """第四级兜底拉起只有 novaact/uvx：版本是纯发行版 + uvx 在 PATH → 按 CLI 版本 pin（worker 与 CLI lockstep）。
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
    """四级全 miss → WorkerNotFoundError 带引擎名 + 该引擎的安装指引 + env 覆写指引（退码交调用点）。"""
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
    assert compose._is_pure_release("1.4.0") and compose._is_pure_release("1.4.0rc1")
    assert not compose._is_pure_release("1.4.0.dev1")
    assert not compose._is_pure_release("1.3.0.post10.dev0+f2efc49.dirty")
    assert not compose._is_pure_release("1.4.0+dirty")
    assert not compose._is_pure_release("not-a-version")


# ---- build_engines：cmd/cwd 走定位链 + env 注入 ----

def test_build_engines_has_both_legs(midscene_env_cmd):
    engines = compose.build_engines()
    assert set(engines) == {"novaact", "midscene"}
    # cmd 来自定位链（不实际起进程，只查接线）：novaact 在 dev 命中第二级、midscene 命中 env 覆写
    assert engines["novaact"].cmd == [sys.executable, "-m", "gherkai_worker_novaact"]
    assert engines["midscene"].cmd == ["node", "/fake/midscene-worker.mjs"]


def test_build_engines_miss_leg_does_not_break_the_other(monkeypatch):
    """某引擎定位链 miss **不连坐**另一条腿（ADR 0037 决策 3）：dev 下 midscene 未装是常态，
    novaact-only 的 run 必须照跑；miss 的那条腿一用即抛 WorkerNotFoundError（带安装指引），
    **不是** resolver 的「未知引擎」（那会把「没装」误导成「拼错名」）。"""
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    engines = compose.build_engines()
    assert set(engines) == {"novaact", "midscene"}  # 引擎名恒在册
    assert engines["novaact"].cmd[-1] == "gherkai_worker_novaact"
    with pytest.raises(compose.WorkerNotFoundError, match="npm i -g"):
        engines["midscene"].run_scope(object())


def test_build_engines_injects_extra_http_headers_env(midscene_env_cmd):
    """extra_http_headers（ADR 0035 决策 4）→ 两 worker env 注 GHERKAI_EXTRA_HTTP_HEADERS（JSON）；
    不传则不注入（默认路径零变化）。"""
    import json as _json

    engines = compose.build_engines(extra_http_headers={"ngrok-skip-browser-warning": "1"})
    for name in ("novaact", "midscene"):
        env = engines[name]._env
        assert env is not None, name
        assert _json.loads(env["GHERKAI_EXTRA_HTTP_HEADERS"]) == {"ngrok-skip-browser-warning": "1"}
    engines2 = compose.build_engines()
    for name in ("novaact", "midscene"):
        env2 = engines2[name]._env
        assert env2 is None or "GHERKAI_EXTRA_HTTP_HEADERS" not in env2, name


def test_build_engines_injects_steps_dir_env_both_legs(tmp_path: Path, midscene_env_cmd):
    """steps_dir（ADR 0037 决策 4）→ **两个** worker 都注 GHERKAI_STEPS_DIR（两引擎扫同一目录、各取自己的
    扩展名）；不传则不注入（worker 只有内建脚手架注册）。worker 只认这个 env，约定逻辑不进 worker。"""
    steps = tmp_path / "steps"
    engines = compose.build_engines(steps_dir=steps)
    for name in ("novaact", "midscene"):
        assert engines[name]._env["GHERKAI_STEPS_DIR"] == str(steps), name
    engines2 = compose.build_engines()
    for name in ("novaact", "midscene"):
        env2 = engines2[name]._env
        assert env2 is None or "GHERKAI_STEPS_DIR" not in env2, name


def test_resolver_known_and_unknown(midscene_env_cmd):
    engines = compose.build_engines()
    resolver = compose.make_resolver(engines)
    assert resolver("novaact") is engines["novaact"]
    with pytest.raises(ValueError, match="未知引擎"):
        resolver("nope")


def test_load_feature_uri_is_given_path_normalized(tmp_path: Path, monkeypatch):
    """uri = 用户给出的路径规范化后原样（ADR 0037 决策 3）：相对给相对（`./` 折掉、`..` 保留），不相对任何根。"""
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
    （dev 树下上溯恰好成立、wheel 用户才炸）。
    """
    assert not hasattr(compose, "repo_root")
    src = Path(compose.__file__).read_text(encoding="utf-8")
    assert "parents[2]" not in src, "compose 又出现了上溯仓库根的推导"


def test_build_engines_injects_artifact_dirs_symmetrically(tmp_path: Path, midscene_env_cmd):
    # 两引擎对称：产物落点经环境变量注入各自 worker 的 env（ADR 0027 产物归位）。
    nova_dir = tmp_path / "r1" / "nova-trajectories"
    mid_dir = tmp_path / "r1" / "midscene-run"
    engines = compose.build_engines(nova_logs_dir=nova_dir, midscene_run_dir=mid_dir)
    assert engines["novaact"]._env["NOVA_LOGS_DIR"] == str(nova_dir)
    assert engines["midscene"]._env["MIDSCENE_RUN_DIR"] == str(mid_dir)
    # 完整继承 os.environ（叠加而非替换）——否则 worker 丢 AWS 凭证等
    import os
    assert engines["midscene"]._env.get("PATH") == os.environ.get("PATH")


def test_build_engines_no_dirs_midscene_env_none(midscene_env_cmd):
    # 不传落点、也无共注 env：midscene env 保持 None，SubprocessEngine 回落继承 os.environ（不硬替换）。
    engines = compose.build_engines()
    assert engines["midscene"]._env is None


def test_build_engines_nova_always_has_act_timeout(midscene_env_cmd):
    # Nova env **恒非 None**：即便无产物落点，组合根也要注入 NOVA_ACT_TIMEOUT_S（双端同源，ADR 0024 grace 硬约束）——
    # worker 读它作 act timeout、组合根用同一常量算 grace 下限，消除两处独立 120 的漂移。
    engines = compose.build_engines()
    assert engines["novaact"]._env is not None
    assert engines["novaact"]._env["NOVA_ACT_TIMEOUT_S"] == str(compose.NOVA_ACT_TIMEOUT_S)


def test_build_engines_never_injects_artifact_s3_env(tmp_path: Path, midscene_env_cmd):
    # local 档**恒不注入** S3 上传落点（worker 据「有没有这组 env」决定上传，无 → 报 file://，ADR 0029）：
    # 上传落点只由 cloud 档的 build_fargate_engines 注入，预演由 e2e_harness 自拼 env（ADR 0016 决策 B）。
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    mid_dir = tmp_path / "rid" / "midscene-run"
    engines = compose.build_engines(nova_logs_dir=nova_dir, midscene_run_dir=mid_dir)
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
        nova_logs_dir=nova_dir, midscene_run_dir=mid_dir,
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
    engines = compose.build_engines(nova_logs_dir=nova_dir, region=None, profile=None)
    assert engines["novaact"]._env["AWS_REGION"] == "eu-central-1"      # 原样继承、未被抹掉
    assert engines["novaact"]._env["AWS_PROFILE"] == "inherited-prof"


def test_build_engines_region_profile_injected_on_rebuild_path_both_legs(monkeypatch, midscene_env_cmd):
    # 补建路径（无产物落点、无共注 env → _env 返回 None）：region/profile 须在**两个引擎**补建路径都注入——
    # Nova 恒补建（塞 NOVA_ACT_TIMEOUT_S，_inject_aws 搭便车）；Midscene 在 region/profile 有值时也补建（否则
    # midscene worker 继承 os.environ、拿不到 --profile 覆盖，而它经 fromNodeProviderChain 消费 profile 做
    # AgentCore/Bedrock 鉴权——真消费、非无害，ADR 0016 决策 C）。
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    engines = compose.build_engines(region="ap-southeast-1", profile="cli-prof")  # 无 dirs → 两个引擎走补建
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["AWS_REGION"] == "ap-southeast-1"  # 补建路径也覆盖生效
        assert engines[eng]._env["AWS_PROFILE"] == "cli-prof"


def test_build_engines_midscene_no_rebuild_when_no_region_profile(monkeypatch, midscene_env_cmd):
    # 对称边界：无落点、无共注 env 且 region/profile 均 None 时 Midscene **不**补建（env=None、继承 os.environ
    # 本就够，免无谓拷贝）——补建只为 region/profile 覆盖，无值则不建。Nova 仍补建（NOVA_ACT_TIMEOUT_S 恒需）。
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    engines = compose.build_engines(region=None, profile=None)
    assert engines["midscene"]._env is None       # 不补建
    assert engines["novaact"]._env is not None     # Nova 恒补建（timeout）


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
    # 不落实则 profile-only 用户下 worker AgentCore validate_region(None) → InvalidRegionError 崩。
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
    # 全 miss（无 --region/env、profile config 也无 region）→ None＝fail-loud（worker 报错、不硬编码 east）。
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
    # 故拦截 `import boto3` 抛 ImportError 真验。守「纯 local 路径绝不依赖 boto3」不变量（ADR 0016 决策 C；
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


# ---- engine_min_grace：按引擎给 grace 下限（ADR 0024 grace 硬约束）----
def test_engine_min_grace_nova_covers_act_timeout_plus_margin():
    # 断言语义关系而非重述公式（否则同义反复、测不出常量漂移）：Nova 下限须**严格大于**单 act 上界——
    # 才留得出会话释放余量（SIGTERM 落长 act 中途须等 act 有界返回才协作退释放会话，ADR 0024）。
    # 若 margin 误设为 0（违 ADR「grace 须留会话释放余量」红线），下限=act_timeout，此断言会红。
    g = compose.engine_min_grace("novaact")
    assert g > compose.NOVA_ACT_TIMEOUT_S, "Nova grace 下限须 > 单 act 上界（留会话释放余量）"
    assert compose.NOVA_GRACE_MARGIN_S > 0, "margin 须 > 0（ADR 0024 会话释放余量红线）"


def test_engine_min_grace_midscene_nonzero_covers_onsignal_budget():
    # Midscene 下限 = MIDSCENE_GRACE_MIN_S（非零）：onSignal 收尾路径超时预算之和须 < grace，否则 worker 被
    # SIGKILL、中断兜底 report 抢传截断（ADR 0024 grace 硬约束；曾为 0.0 致 midscene-only run grace 回落 5s < 上传 10s）。
    assert compose.engine_min_grace("midscene") == float(compose.MIDSCENE_GRACE_MIN_S)
    assert compose.engine_min_grace("midscene") > 0.0
    # 必须够 onSignal 最坏串行路径（会话 Stop + browser.close + 中断兜底上传超时），且 > Midscene 上传超时 10s。
    assert compose.MIDSCENE_GRACE_MIN_S >= 10


def test_engine_min_grace_unknown_engine_zero():
    # 未知引擎无下限（0.0）——保守：core enforce grace > 0 仍兜底。
    assert compose.engine_min_grace("unknown") == 0.0


def test_engine_min_grace_mixed_run_takes_max():
    # 混引擎 run 的 min_grace = 各引擎下限的 max（grace 是 run 级单值，__main__ 取 max）——Nova 下限最大、支配。
    legs = ["novaact", "midscene"]
    assert max(compose.engine_min_grace(e) for e in legs) == compose.engine_min_grace("novaact")


# ---- 两层命名（ADR 0033）：prefix + 基名推导 / task-def / container / SSM 路径 ----
def test_default_name_prefix_original_concat():
    # prefix 原样拼基名（含分隔符由用户负责，防粘连——同 S3 prefix 先例）
    assert compose.default_name("gherkai-", "runs") == "gherkai-runs"
    assert compose.default_name("prod-", "events") == "prod-events"
    assert compose.default_name("nodash", "runs") == "nodashruns"  # 无分隔符 → 粘连（用户负责）


def test_task_def_and_container_name():
    # task-def family 带 prefix、按引擎；container 名不带 prefix（随 task-def 走，避冗余）
    assert compose.task_def_name("prod-", "novaact") == "prod-novaact-worker"
    assert compose.task_def_name("gherkai-", "midscene") == "gherkai-midscene-worker"
    assert compose.container_name("novaact") == "novaact-worker"
    assert compose.container_name("midscene") == "midscene-worker"


def test_ssm_path_contains_prefix():
    # SSM 路径含 prefix（cli 已知 prefix 拼路径读 subnet/sg，无循环——ADR 0033）
    assert compose.ssm_path("prod-", "subnets") == "/prod-backend/subnets"
    assert compose.ssm_path("gherkai-", "security-groups") == "/gherkai-backend/security-groups"


# ---- resolve_cloud_target：入口皮的 flag/env → 各资源终名 + region/profile（ADR 0033 / 0016 决策 C）----
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
    # 三 Lambda 名同源推导；detached_chain_lambdas 顺序 = 链上顺序（kicker→reconciler→exit-observer）
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
    monkeypatch.setattr(compose, "resolve_region", lambda r, p: None)  # 不摸真 ~/.aws
    t = compose.resolve_cloud_target()
    assert t.prefix == compose.DEFAULT_PREFIX and t.runs_table == f"{compose.DEFAULT_PREFIX}runs"
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
    # 显式给 subnet/sg → 不读 SSM（ssm 注入个会炸的哨兵，验它没被调）
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
    # 不把空列表传到 awsvpcConfiguration、拖到 RunTask 才炸。空串 / 纯逗号 两种空形态都拦。
    import pytest

    class _EmptySsm:
        def __init__(self, val): self._val = val
        def get_parameter(self, Name):
            return {"Parameter": {"Value": self._val}}

    for empty_val in ("", ",", ",,"):  # 空串 / 逗号无值——过滤后都是 []
        with pytest.raises(ValueError, match="为空"):
            compose.resolve_network(prefix="g-", subnets=None, security_groups=None, ssm=_EmptySsm(empty_val))
    # 错误须点名是哪个 SSM 路径（subnets 先读、先炸）
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
        run_id="rid-1", prefix="prod-", cluster="prod-cluster", events_table="prod-events",
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
    # job_s3 = (bucket, "{report_dir}/{run_id}/jobs-in/")——**jobs-in/ 非 jobs/**（避与 ResultStore 判定 key 撞，真跑暴露）
    assert nova["job_s3"] == ("prod-artifacts", "runs/rid-1/jobs-in/")
    # artifact_s3 = (bucket, "{report_dir}/{run_id}/")——**cloud 必注入**（否则容器盘销毁产物必丢，ADR 0029）
    assert nova["artifact_s3"] == ("prod-artifacts", "runs/rid-1/")
    # SDK 产物落点 env（按引擎、容器内路径）——**uploader 靠它算 run_dir，缺它 no-op 报 file://、产物丢**（真跑暴露）。
    assert nova["sdk_artifact_dir_env"] == {"NOVA_LOGS_DIR": "/tmp/gherkai-run/rid-1/nova-trajectories"}
    # Nova act timeout **双端同源**（ADR 0024 grace 硬约束）：cloud 档也须显式注入——容器不继承本地 env，
    # 缺它则 worker 落回自带字面量、调 NOVA_ACT_TIMEOUT_S 只抬高 grace 下限、改不动容器内单 act 上界。
    assert nova["extra_env"]["NOVA_ACT_TIMEOUT_S"] == str(compose.NOVA_ACT_TIMEOUT_S)
    mid = by_engine[_REV["midscene"]]
    assert mid["sdk_artifact_dir_env"] == {"MIDSCENE_RUN_DIR": "/tmp/gherkai-run/rid-1/midscene-run"}
    assert "NOVA_ACT_TIMEOUT_S" not in mid["extra_env"]  # 引擎特定值只给该引擎（Midscene 无可控 act timeout）


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
        self._env_by_fn = env_by_fn or {}  # fn → env dict（缺项 = 该 Lambda 没配 env，同真实返回体省略 Environment）

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
    # task-def 维度的 prefix 配错（原漏到 RunTask 才炸、退 1 不点名）→ 现 preflight 点名 fail-fast（ADR 0033）
    err = compose.preflight_cloud_resources(
        prefix="prod-", events_table="prod-events", bucket="prod-artifacts", cluster="prod-cluster",
        task_defs=["prod-novaact-worker"],
        ddb=_FakeDdbClient({"prod-events"}), s3=_FakeS3Client({"prod-artifacts"}),
        ecs=_FakeEcsClient({"prod-cluster"}),  # task-def 集为空 → 缺
    )
    assert err is not None
    assert "prod-novaact-worker" in err and "--prefix='prod-'" in err


def test_preflight_missing_chain_lambda_names_prefix():
    # detached 链三 Lambda 任一缺 = 提交成功但 run 永不推进/收敛 → 挡在提交前（ADR 0033）
    err = compose.preflight_cloud_resources(
        prefix="g-", events_table="g-events", bucket="g-artifacts", cluster="g-cluster",
        lambda_fns=["g-kicker", "g-reconciler", "g-exit-observer"],
        ddb=_FakeDdbClient({"g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient({"g-kicker", "g-exit-observer"}),  # reconciler 缺
    )
    assert err is not None and "g-reconciler" in err


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
    # --report-dir 与推进器 REPORT_DIR 分裂 = 跑完但结果落在用户没指定的前缀下（静默分裂）→ 挡在提交前、点名两侧值。
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
    """跑一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。"""
    return compose.preflight_cloud_resources(
        prefix="g-", runs_table="g-runs", events_table="g-events", bucket="g-artifacts",
        cluster="g-cluster", lambda_fns=_CHAIN,
        declared_max_concurrency=declared, on_warn=warns.append,
        ddb=_FakeDdbClient({"g-runs", "g-events"}), s3=_FakeS3Client({"g-artifacts"}),
        ecs=_FakeEcsClient({"g-cluster"}),
        lam=_FakeLambdaClient(_CHAIN, env_by_fn={fn: {"MAX_CONCURRENCY": cap_env} for fn in _CHAIN}),
    )


def test_preflight_warns_once_when_declared_max_concurrency_exceeds_cap():
    # 声明 8 > cap 4 → 提交时就告知「本 run 只会按 4 并行」（否则用户以为按 8 跑、只看到莫名慢）。
    # 但**不构成 preflight 失败**：钳制不改产物落点、run 照跑（对照 REPORT_DIR 分岔的退 2——判据 = 分岔后果）。
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
    """定位链第一级钉死一个假 novaact cmd：自述用例只验「组合根怎么拼命令/收结果」，不依赖本机装了什么。"""
    monkeypatch.setenv("GHERKAI_WORKER_NOVAACT_CMD", "/fake/novaact-worker")
    monkeypatch.setenv("GHERKAI_WORKER_MIDSCENE_CMD", "/fake/midscene-worker")
    monkeypatch.delenv("GHERKAI_WORKER_NOVAACT_CWD", raising=False)
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CWD", raising=False)


def test_query_deterministic_parses_worker_json(monkeypatch, novaact_env_cmd):
    import subprocess

    class _P:
        returncode = 0
        stdout = b'[{"pattern": "p", "description": "d", "example": "e"}]'
        stderr = b""

    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["cwd"] = kw.get("cwd")
        captured["env"] = kw.get("env")
        return _P()

    monkeypatch.setattr(subprocess, "run", fake_run)
    got = compose.query_deterministic("novaact")
    assert got == [{"pattern": "p", "description": "d", "example": "e"}]
    assert captured["cmd"] == ["/fake/novaact-worker", "--list-deterministic"]  # 定位链 cmd + 自述 flag
    assert captured["cwd"] is None      # 定位链未给 cwd → 继承本进程 CWD（worker 无专属 cwd，ADR 0037 决策 3）
    assert captured["env"] is None      # 无 steps_dir → 不动 env（worker 继承本进程环境）


def test_query_deterministic_injects_steps_dir_env(monkeypatch, novaact_env_cmd, tmp_path):
    """自述入口同样加载 steps 目录（ADR 0037 决策 4）→ steps_dir 经 env 注入，故 list-deterministic 的清单
    含使用方定制 step。注入是叠加（保 os.environ，否则 worker 丢 PATH/凭证）。"""
    import os
    import subprocess

    class _P:
        returncode = 0
        stdout = b"[]"
        stderr = b""

    captured = {}
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: captured.update(kw) or _P())
    compose.query_deterministic("novaact", steps_dir=tmp_path / "steps")
    assert captured["env"]["GHERKAI_STEPS_DIR"] == str(tmp_path / "steps")
    assert captured["env"].get("PATH") == os.environ.get("PATH")


def test_query_deterministic_unknown_engine():
    with pytest.raises(ValueError, match="未知引擎"):
        compose.query_deterministic("nope")


def test_query_deterministic_worker_failure_raises(monkeypatch, novaact_env_cmd):
    import subprocess

    class _P:
        returncode = 1
        stdout = b""
        stderr = "worker exploded".encode()

    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _P())
    with pytest.raises(RuntimeError, match="自述失败"):
        compose.query_deterministic("midscene")


def test_self_describe_miss_raises_worker_not_found(monkeypatch):
    """定位链 miss 时自述入口抛 WorkerNotFoundError（而非「起不来」的通用 RuntimeError）——
    调用点据此分叉：list-deterministic 退 2 打安装指引、plan 降级。"""
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CMD", raising=False)
    monkeypatch.setattr(compose.shutil, "which", lambda n: None)
    monkeypatch.setattr(compose, "_runtime_version", lambda: None)
    with pytest.raises(compose.WorkerNotFoundError):
        compose.query_deterministic("midscene")
    with pytest.raises(compose.WorkerNotFoundError):
        compose.match_deterministic("midscene", ["a"])


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
    got = compose.match_deterministic("midscene", ["a", "b"])
    assert got == [{"pattern": "p", "description": "d"}, None]
    assert captured["cmd"][-1] == "--match-steps"
    import json as _json
    assert _json.loads(captured["input"].decode()) == ["a", "b"]


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
    """凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。"""
    ssm = _StampSsm(None, error=_client_error("AccessDeniedException"))
    with pytest.raises(Exception) as e:
        compose.read_backend_version(prefix="g-", ssm=ssm)
    assert "AccessDenied" in str(e.value)


def test_read_backend_version_blank_value_is_none():
    assert compose.read_backend_version(prefix="g-", ssm=_StampSsm("  ")) is None


def test_skew_ok_same_release_is_silent():
    verdict, msg = compose.check_version_skew("1.4.0", "1.4.0")
    assert (verdict, msg) == (compose.SKEW_OK, "")


def test_skew_block_when_cli_newer_names_both_exits():
    """CLI 新于后端 → block，且消息必须点名**两条**出路（决策 7 不设放行口，只有这两条）。"""
    verdict, msg = compose.check_version_skew("1.3.0", "1.4.0")
    assert verdict == compose.SKEW_BLOCK
    assert "gherkai deploy" in msg                      # ① 部署方升后端
    assert "uvx --from 'gherkai==1.3.0'" in msg         # ② 临时跑同版本 CLI（点名后端版本）
    assert "1.4.0" in msg


def test_skew_warn_when_cli_older():
    verdict, msg = compose.check_version_skew("1.4.0", "1.3.0")
    assert verdict == compose.SKEW_WARN and "旧于" in msg


def test_skew_warn_when_stamp_missing_points_at_deploy():
    """戳缺失 = 本机制之前部署的环境 → warn（不拦）+ 提示跑一次 `gherkai deploy` 写入。"""
    verdict, msg = compose.check_version_skew(None, "1.4.0")
    assert verdict == compose.SKEW_WARN and "gherkai deploy" in msg


def test_skew_skip_when_either_side_impure():
    """任一侧带 .dev/.post/本地段 → skip（dev 逐提交前进，逐字比会把每次都判成 skew）。"""
    for stamp, cli in [("1.4.0", "1.4.0.post3.dev0+abc.dirty"), ("1.4.0.dev1", "1.4.0"),
                       ("1.4.0", "1.4.0+local"), ("1.4.0", "0+unknown")]:
        verdict, msg = compose.check_version_skew(stamp, cli)
        assert verdict == compose.SKEW_SKIP, (stamp, cli)
        assert msg


def test_skew_skip_when_own_version_unknown():
    """未装成包（源码直跑）→ 调用点取不到自身版本、传 None → skip，不误判成 skew。"""
    verdict, msg = compose.check_version_skew("1.4.0", None)
    assert verdict == compose.SKEW_SKIP and msg


def test_skew_compares_release_segment_only():
    """只比 release 段（决策 7）：位数不同补零后比；同 release 段的 rc 与正式版视作同版本。"""
    assert compose.check_version_skew("1.4.0", "1.4")[0] == compose.SKEW_OK
    assert compose.check_version_skew("1.4", "1.4.0")[0] == compose.SKEW_OK
    assert compose.check_version_skew("1.4.0", "1.4.0rc1")[0] == compose.SKEW_OK
    assert compose.check_version_skew("1.4.0", "1.4.1")[0] == compose.SKEW_BLOCK
    assert compose.check_version_skew("1.4.1", "1.4.0")[0] == compose.SKEW_WARN


def test_skew_cli_version_is_mandatory_no_runtime_fallback():
    """`cli_version` 必给（决策 7 比的是「写任务定义那一方」的版本）：不缺省成 gherkai-runtime 的版本——
    editable 树里各包版本各自漂，缺省会埋一个只在 lockstep 发行态下才等价的第二真源。"""
    with pytest.raises(TypeError):
        compose.check_version_skew("1.0.0")  # type: ignore[call-arg]


def test_check_backend_skew_reads_stamp_then_judges():
    """读戳 + 判定一步到位（编排住产品本体，入口皮只翻退出码）。"""
    ssm = _StampSsm("1.3.0")
    verdict, msg, stamp = compose.check_backend_skew(prefix="prod-", cli_version="1.4.0", ssm=ssm)
    assert verdict == compose.SKEW_BLOCK and "gherkai deploy" in msg
    assert stamp == "1.3.0"  # 戳一并返回：调用方的 variant 解析复用，不二次读 SSM
    assert ssm.reads == ["/prod-backend/version"]


def test_check_backend_skew_missing_stamp_warns_not_raises():
    ssm = _StampSsm(None, error=_client_error("ParameterNotFound"))
    verdict, msg, stamp = compose.check_backend_skew(prefix="g-", cli_version="1.4.0", ssm=ssm)
    assert verdict == compose.SKEW_WARN and "gherkai deploy" in msg and stamp is None


def test_check_backend_skew_propagates_read_errors():
    """凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到≠放过。"""
    from botocore.exceptions import ClientError
    ssm = _StampSsm(None, error=_client_error("AccessDeniedException"))
    with pytest.raises(ClientError):
        compose.check_backend_skew(prefix="g-", cli_version="1.4.0", ssm=ssm)


def test_variant_miss_hint_offers_push_and_base_fallback():
    """同版本档的 variant miss 提示须同时给两条出路（ADR 0038「升级不重置默认指针」条）：
    让部署方 push-worker，或临时 --worker-variant base 先跑。"""
    from gherkai_runtime.compose import _variant_miss_hint

    msg = _variant_miss_hint(engine="midscene", variant="common", tag="1.4.0-common",
                             what="SSM 里没有映射", cli_version="1.4.0", backend_version="1.4.0")
    assert "push-worker" in msg and "--variant common" in msg
    assert "--worker-variant base" in msg


def test_variant_miss_hint_older_cli_only_guides_upgrade():
    """CLI 旧于后端那一档只引导升级 CLI，不给 push、也不给 base 兜底（推旧命名空间的 tag 是原地绕圈）。"""
    from gherkai_runtime.compose import _variant_miss_hint

    msg = _variant_miss_hint(engine="novaact", variant="common", tag="1.3.0-common",
                             what="SSM 里没有映射", cli_version="1.3.0", backend_version="1.4.0")
    assert "升到后端版本" in msg or "升" in msg
    assert "push-worker" not in msg and "--worker-variant base" not in msg
