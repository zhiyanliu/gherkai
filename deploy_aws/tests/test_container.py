"""容器引擎口子测试（ADR 0038「容器引擎口子」）。

**两层证据，分清边界**：
- 大部分用一个**假 docker**（记 argv/stdin 的 python 脚本）——验的是「拼出的命令与 stdin 用法」，这层纯逻辑。
- 末尾三条用**真 docker**（`skipif` 保护）——验 ADR 里那两条只有真引擎才成立的事实：本地未推送镜像的
  `RepoDigests` 为空、`--platform linux/arm64` 拉下来的镜像会被架构判据拒。这两条 mock 不出来（「绿≠对」）。
真 push 不在这里也不在任何单测里：本机无 AWS 凭证，推 ECR 只能真账号验。
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from gherkai_deploy_aws.container import (
    CONTAINER_ENGINE_ENV,
    ContainerEngine,
    ContainerError,
    ImageInfo,
    UnsupportedContainerEngine,
    digest_for_repo,
    resolve_container_engine,
)

ECR_REPO = "000000000000.dkr.ecr.us-east-1.amazonaws.com/gherkai-novaact-worker"

# 假 docker：把每次调用（argv + login 的 stdin）追加到 FAKE_DOCKER_LOG，按 FAKE_DOCKER_SPEC 决定 rc/输出。
# **只有 login 读 stdin**：无条件 read 会在继承 pytest 的 fd 0 时挂住。
_SHIM = '''#!/usr/bin/env python3
import json, os, sys
entry = {"argv": sys.argv[1:], "stdin": None}
if sys.argv[1:2] == ["login"]:
    entry["stdin"] = sys.stdin.read()
with open(os.environ["FAKE_DOCKER_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\\n")
spec = json.loads(os.environ.get("FAKE_DOCKER_SPEC") or "{}")
r = spec.get(" ".join(sys.argv[1:3])) or spec.get(sys.argv[1]) or {}
sys.stdout.write(r.get("stdout", ""))
sys.stderr.write(r.get("stderr", ""))
sys.exit(int(r.get("rc", 0)))
'''


class _Fake:
    """假 docker 的把手：`engine` 是指着 shim 的 ContainerEngine，`calls` 读回它收到了什么。"""

    def __init__(self, tmp_path, monkeypatch, spec: dict | None = None) -> None:
        script = tmp_path / "fake-docker"
        script.write_text(_SHIM, encoding="utf-8")
        script.chmod(0o755)
        self.log = tmp_path / "calls.jsonl"
        monkeypatch.setenv("FAKE_DOCKER_LOG", str(self.log))
        monkeypatch.setenv("FAKE_DOCKER_SPEC", json.dumps(spec or {}))
        self.engine = ContainerEngine("docker", binary=str(script))

    @property
    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]


def _inspect_spec(**fields) -> dict:
    return {"image inspect": {"rc": 0, "stdout": json.dumps(fields)}}


# ---------------------------------------------------------------- 引擎选择

def test_default_is_docker():
    assert resolve_container_engine().name == "docker"


def test_env_selects_engine_and_flag_wins(monkeypatch):
    monkeypatch.setenv(CONTAINER_ENGINE_ENV, "docker")
    assert resolve_container_engine().name == "docker"
    monkeypatch.setenv(CONTAINER_ENGINE_ENV, "podman")
    with pytest.raises(UnsupportedContainerEngine):
        resolve_container_engine()          # env 也照拦
    assert resolve_container_engine("docker").name == "docker"  # flag 优先于 env


def test_unsupported_engine_is_rejected_not_silently_downgraded():
    """`--container-engine podman` **不静默回落 docker**：回落会让人以为自己验过 podman 路径（ADR 0038）。"""
    with pytest.raises(UnsupportedContainerEngine) as exc:
        resolve_container_engine("podman")
    # 文案是产品面（不带内部机制名，判据见 CLAUDE.md「产品面文案不带内部指代」）——断言点名了引擎与「未实装」。
    assert "podman" in str(exc.value) and "未实装" in str(exc.value)


# ---------------------------------------------------------------- digest 挑选（正确性支点）

def test_digest_picked_by_repo_not_first_entry():
    """基底同步先 pull 过 GHCR → `RepoDigests` 多条；**取第一条就会把 GHCR 的 digest 写进 task-def**
    （ECR 里不存在它，RunTask 拉镜像才炸，ADR 0038 步 4）。"""
    entries = [f"ghcr.io/zhiyanliu/gherkai-worker-novaact@sha256:{'a' * 64}",
               f"{ECR_REPO}@sha256:{'b' * 64}"]
    assert digest_for_repo(entries, ECR_REPO) == f"sha256:{'b' * 64}"


def test_digest_none_when_repo_absent_or_empty():
    assert digest_for_repo([], ECR_REPO) is None
    assert digest_for_repo([f"other/repo@sha256:{'c' * 64}"], ECR_REPO) is None


def test_target_platform_judgement():
    assert ImageInfo(exists=True, os="linux", architecture="amd64").matches_target_platform()
    assert not ImageInfo(exists=True, os="linux", architecture="arm64").matches_target_platform()
    assert not ImageInfo(exists=True, os="windows", architecture="amd64").matches_target_platform()
    assert ImageInfo(exists=False).platform == "?/?"


# ---------------------------------------------------------------- 五动词的命令面（假 docker）

def test_inspect_parses_os_arch_and_repo_digests(tmp_path, monkeypatch):
    fake = _Fake(tmp_path, monkeypatch, _inspect_spec(
        Os="linux", Architecture="amd64", RepoDigests=[f"{ECR_REPO}@sha256:{'d' * 64}"]))
    info = fake.engine.inspect("acme:login")
    assert (info.exists, info.os, info.architecture) == (True, "linux", "amd64")
    assert info.repo_digests == (f"{ECR_REPO}@sha256:{'d' * 64}",)
    assert fake.calls[0]["argv"] == ["image", "inspect", "acme:login", "--format", "{{json .}}"]


def test_inspect_missing_image_is_not_an_error(tmp_path, monkeypatch):
    """「本地没这个镜像」是正常分叉（调用方给专属提示），不是异常。"""
    fake = _Fake(tmp_path, monkeypatch, {"image inspect": {"rc": 1, "stderr": "Error: No such image: x:y"}})
    assert fake.engine.inspect("x:y") == ImageInfo(exists=False)


def test_inspect_other_failure_raises(tmp_path, monkeypatch):
    fake = _Fake(tmp_path, monkeypatch, {"image inspect": {"rc": 1, "stderr": "Cannot connect to the Docker daemon"}})
    with pytest.raises(ContainerError, match="daemon"):
        fake.engine.inspect("x:y")


def test_login_password_goes_through_stdin_never_argv(tmp_path, monkeypatch):
    """**密码绝不进 argv**（同机任何进程 `ps` 可见，ECR 令牌 12 小时有效）——`--password-stdin`。"""
    fake = _Fake(tmp_path, monkeypatch)
    fake.engine.login("reg.example.com", "AWS", "s3cr3t-token")
    call = fake.calls[0]
    assert call["argv"] == ["login", "--username", "AWS", "--password-stdin", "reg.example.com"]
    assert "s3cr3t-token" not in " ".join(call["argv"])
    assert call["stdin"] == "s3cr3t-token"


def test_tag_push_pull_command_shape(tmp_path, monkeypatch):
    fake = _Fake(tmp_path, monkeypatch)
    fake.engine.tag("acme:login", f"{ECR_REPO}:1.4.0-login")
    fake.engine.push(f"{ECR_REPO}:1.4.0-login")
    fake.engine.pull("ghcr.io/zhiyanliu/gherkai-worker-novaact:1.4.0", platform="linux/amd64")
    assert [c["argv"] for c in fake.calls] == [
        ["tag", "acme:login", f"{ECR_REPO}:1.4.0-login"],
        ["push", f"{ECR_REPO}:1.4.0-login"],
        ["pull", "--platform", "linux/amd64", "ghcr.io/zhiyanliu/gherkai-worker-novaact:1.4.0"],
    ]


def test_push_failure_raises_container_error(tmp_path, monkeypatch):
    fake = _Fake(tmp_path, monkeypatch, {"push": {"rc": 1}})
    with pytest.raises(ContainerError, match="失败"):
        fake.engine.push(f"{ECR_REPO}:1.4.0-login")


def test_probe_reports_missing_binary_without_raising():
    msg = ContainerEngine("docker", binary="definitely-not-a-container-engine").probe()
    assert msg and "找不到容器引擎" in msg


# ---------------------------------------------------------------- 真 docker（mock 不出来的那两条 ADR 事实）

def _docker_ok() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                          capture_output=True).returncode == 0


def _has_image(ref: str) -> bool:
    return subprocess.run(["docker", "image", "inspect", ref], capture_output=True).returncode == 0


real_docker = pytest.mark.skipif(not _docker_ok(), reason="需要可用的 docker daemon（真引擎事实，非纯逻辑）")


@real_docker
@pytest.mark.skipif(not _has_image("gherkai-worker-novaact:dev"),
                    reason="需要本地 build 好的 gherkai-worker-novaact:dev")
def test_real_local_image_has_no_repo_digests_and_is_amd64():
    """ADR 0038 步 2 那条事实：**本地 build、从未推过的镜像 `RepoDigests` 为空** → 推送前拿不到 digest。

    这是「digest 只在推送后取」的全部理由（`.Id` 是 config digest、注册能过而 RunTask 才 `manifest unknown`）。
    单测里 mock 一个空列表证明不了它——只有真引擎说话才算数。
    """
    info = resolve_container_engine().inspect("gherkai-worker-novaact:dev")
    assert info.exists and info.matches_target_platform(), info
    assert info.repo_digests == (), f"从未推送的本地镜像不该有 registry digest：{info.repo_digests}"


@real_docker
def test_real_arm64_image_is_rejected_by_the_platform_gate():
    """arm 变体真镜像 → 架构判据拒（= push-worker 退 2 那一支）。

    用 alpine（小）代替真 worker 镜像：判据只看 `Os`/`Architecture`，与镜像内容无关。arm Mac 上漏
    `--platform linux/amd64` build 出来的就是这个形态，其后果本会拖到 Fargate 启动期 `exec format error`。
    """
    engine = resolve_container_engine()
    assert subprocess.run(["docker", "pull", "--platform", "linux/arm64", "alpine:3.20"],
                          capture_output=True).returncode == 0, "拉 arm64 alpine 失败（需要网络）"
    info = engine.inspect("alpine:3.20")
    assert info.exists and info.architecture == "arm64", info
    assert not info.matches_target_platform()


@real_docker
@pytest.mark.skipif(not _has_image("gherkai-worker-novaact:dev"),
                    reason="需要本地 build 好的 gherkai-worker-novaact:dev")
def test_real_tag_to_ecr_ref_still_has_no_digest():
    """`docker tag` 到 ECR ref **不会**产生 registry digest（只有 push 才会）——第二次确认「推送后才取 digest」。"""
    engine = resolve_container_engine()
    target = f"{ECR_REPO}:test-only-never-pushed"
    engine.tag("gherkai-worker-novaact:dev", target)
    try:
        info = engine.inspect(target)
        assert info.exists and info.matches_target_platform()
        assert digest_for_repo(info.repo_digests, ECR_REPO) is None, info.repo_digests
    finally:
        subprocess.run(["docker", "image", "rm", target], capture_output=True)
