"""容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。

**只五个动词**：`inspect`（存在 + 架构；**推送后**才取 digest）/ `tag` / `login` / `push` / `pull`。
push-worker 与 `gherkai deploy` 的基底同步之外，CLI / runtime / CDK 一概不碰容器引擎——口子收在这里，
将来 podman（同形子命令）或「免容器引擎的 registry 直拷」（ADR 0038 重议闸门）都只改本文件。

**这一期只实现 docker**：`--container-engine` / env `GHERKAI_CONTAINER_ENGINE` 认得别的名字，但给别的名字
是退 2（`UnsupportedContainerEngine`），不是静默回落 docker——静默回落会让人以为自己在用 podman。

## 两条与 ADR 绑死的事实（别「优化」掉）

- **推送前不取 digest**：本地 build 出来、从未推过的镜像 `RepoDigests` 为空（**真机核过**：
  `gherkai-worker-novaact:dev` → `RepoDigests=[]`），而 `.Id` 是 **config digest**、不是 `repo@sha256:`
  需要的 manifest digest——拿它注册 ECS 只校格式、RunTask 拉镜像时才 `manifest unknown`
  （ADR 0038 被拒方案「推送前用本地 inspect 的 image Id 当 digest」）。故本类的 `inspect` 只负责「存在 + 架构」，
  digest 由调用方在**推送后**再 `inspect` 一次、经 `digest_for_repo` 按仓库挑。
- **digest 要按仓库挑、不能取 `RepoDigests` 第一条**：基底同步路径先 `pull` 过 GHCR，同一个本地镜像会同时
  挂着 GHCR 与 ECR 两条 repo digest（`docker pull` 后的 `alpine:3.20` 就带着 `alpine@sha256:…`，真机核过）。

## 密码永不进 argv

`login` 一律 `--password-stdin`：argv 在同机任何进程的 `ps` 里可见，ECR 令牌 12 小时有效——够别人拿去推镜像。
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field

# `--container-engine` 的 env 等价物（flag 优先）。名字与 flag 同源，见 `resolve_container_engine`。
CONTAINER_ENGINE_ENV = "GHERKAI_CONTAINER_ENGINE"
DEFAULT_CONTAINER_ENGINE = "docker"
# 这一期实装的引擎全集。podman 同形子命令、接得进来，但**没跑过就不敢说支持**（ADR 0038 重议闸门）。
SUPPORTED_ENGINES = ("docker",)

# worker 镜像的目标平台（ADR 0038「架构」：固定 linux/amd64，模板 revision 的 runtimePlatform = X86_64）。
TARGET_OS = "linux"
TARGET_ARCH = "amd64"


class ContainerError(Exception):
    """容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。

    `str(exc)` 即给人看的整句；调用方按自己的退出码层归码（push-worker 退 2、deploy 四步退 1）。
    """


class UnsupportedContainerEngine(ContainerError):
    """要求了本期未实装的容器引擎（ADR 0038：只 docker）。"""


@dataclass(frozen=True)
class ImageInfo:
    """`inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。

    `repo_digests` 是 `<repo>@sha256:<hex>` 形态的原始条目（可能多条、可能空，见模块头两条事实）。
    """

    exists: bool
    os: str | None = None
    architecture: str | None = None
    repo_digests: tuple[str, ...] = field(default_factory=tuple)

    @property
    def platform(self) -> str:
        """`linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。"""
        return f"{self.os or '?'}/{self.architecture or '?'}"

    def matches_target_platform(self) -> bool:
        """是否 linux/amd64（ADR 0038 固定架构）。"""
        return self.os == TARGET_OS and self.architecture == TARGET_ARCH


def digest_for_repo(repo_digests, repo_uri: str) -> str | None:
    """从 `RepoDigests` 里挑出**本仓库**那条的 digest（`sha256:<hex>`）；没有 → None。

    **绝不取第一条**：基底同步先 `pull` 过 GHCR，同一镜像会挂着多个仓库的 digest，取错了写进 task-def 就是
    「ECR 里不存在这个 digest」——RunTask 拉镜像时才炸（ADR 0038 步 4）。
    """
    for entry in repo_digests or ():
        repo, _, digest = str(entry).partition("@")
        if repo == repo_uri and digest:
            return digest
    return None


class ContainerEngine:
    """docker CLI 的五动词薄壳（子进程调用；不用 SDK——多一个依赖、且 podman 的 SDK 不同形）。

    `binary` 是可执行名/路径（测试可指向假脚本）。构造**不探活**（构造在参数解析期发生、探活要花时间且需要
    daemon）；探活是显式的 `probe()`——调用方在真要用之前调一次，把「引擎没装/daemon 没起」与「push 失败」
    两类错误分开报。
    """

    def __init__(self, name: str = DEFAULT_CONTAINER_ENGINE, *, binary: str | None = None) -> None:
        self.name = name
        self.binary = binary or name

    # ---- 探活 ----
    def probe(self) -> str | None:
        """引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。

        两级：PATH 上有没有这个可执行文件（`which`）→ daemon 通不通（`version --format '{{.Server.Version}}'`
        要连 daemon，`--version` 不连、探不出「装了但没起」）。
        """
        if shutil.which(self.binary) is None:
            return (f"找不到容器引擎 `{self.binary}`：push-worker 与 deploy 同步基底镜像都要用它推/拉。"
                    f"装好后重试。")
        try:
            out = subprocess.run([self.binary, "version", "--format", "{{.Server.Version}}"],
                                 capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as exc:
            return f"`{self.binary} version` 起不动：{exc}"
        if out.returncode != 0:
            return (f"`{self.binary}` 在 PATH 上但连不上 daemon（exit {out.returncode}）："
                    f"{_tail(out.stderr) or _tail(out.stdout)}\n先把容器引擎的 daemon 起起来。")
        return None

    # ---- 五动词 ----
    def inspect(self, ref: str) -> ImageInfo:
        """本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：
        「本地没这个镜像」是调用方要给专属提示的正常分叉）。其余失败（daemon 挂了）→ `ContainerError`。"""
        out = subprocess.run([self.binary, "image", "inspect", ref, "--format", "{{json .}}"],
                             capture_output=True, text=True)
        if out.returncode != 0:
            err = (out.stderr or "") + (out.stdout or "")
            if "No such image" in err or "no such image" in err:
                return ImageInfo(exists=False)
            raise ContainerError(f"`{self.binary} image inspect {ref}` 失败（exit {out.returncode}）：{_tail(err)}")
        try:
            data = json.loads(out.stdout.strip().splitlines()[0])
        except (ValueError, IndexError) as exc:
            raise ContainerError(f"读不懂 `{self.binary} image inspect {ref}` 的输出：{exc}") from exc
        digests = data.get("RepoDigests") or []
        return ImageInfo(
            exists=True,
            os=data.get("Os"),
            architecture=data.get("Architecture"),
            repo_digests=tuple(str(d) for d in digests),
        )

    def tag(self, src: str, dst: str) -> None:
        self._run(["tag", src, dst])

    def login(self, registry: str, username: str, password: str) -> None:
        """登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。"""
        self._run(["login", "--username", username, "--password-stdin", registry], stdin_text=password)

    def push(self, ref: str) -> None:
        """推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。"""
        self._stream(["push", ref])

    def pull(self, ref: str, *, platform: str | None = None) -> None:
        """拉镜像（基底同步用）。`platform` 给了就显式指定，避免在 arm Mac 上拉到 arm 变体。"""
        argv = ["pull", *(["--platform", platform] if platform else []), ref]
        self._stream(argv)

    # ---- 内部 ----
    def _run(self, argv: list[str], *, stdin_text: str | None = None) -> str:
        """短命令：捕输出、失败即抛（**stderr 不直通**——login 的失败要能包进我们的文案里）。"""
        try:
            out = subprocess.run([self.binary, *argv], capture_output=True, text=True, input=stdin_text)
        except OSError as exc:
            raise ContainerError(f"起不动 `{self.binary} {argv[0]}`：{exc}") from exc
        if out.returncode != 0:
            raise ContainerError(f"`{self.binary} {' '.join(argv)}` 失败（exit {out.returncode}）："
                                 f"{_tail(out.stderr) or _tail(out.stdout)}")
        return out.stdout or ""

    def _stream(self, argv: list[str]) -> None:
        """长命令（push/pull）：stdio 直通、只看返回码。进度条对用户有价值，捕下来反而是把它憋住。"""
        try:
            rc = subprocess.run([self.binary, *argv]).returncode
        except OSError as exc:
            raise ContainerError(f"起不动 `{self.binary} {argv[0]}`：{exc}") from exc
        if rc != 0:
            raise ContainerError(f"`{self.binary} {' '.join(argv)}` 失败（exit {rc}）——诊断见上方 {self.binary} 输出。")


def resolve_container_engine(requested: str | None = None) -> ContainerEngine:
    """选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。

    本期外的名字 → `UnsupportedContainerEngine`（调用方退 2）。**不静默回落 docker**：给了 `--container-engine
    podman` 却跑 docker，用户会以为自己验过 podman 路径（ADR 0038 只实现 docker）。
    """
    import os

    name = (requested or os.environ.get(CONTAINER_ENGINE_ENV) or DEFAULT_CONTAINER_ENGINE).strip()
    if name not in SUPPORTED_ENGINES:
        raise UnsupportedContainerEngine(
            f"容器引擎 `{name}` 这一期未实装（只有 {'/'.join(SUPPORTED_ENGINES)}）。"
            f"podman 等 docker 兼容引擎当前走不通；需要就提，别指望它已经能用。"
        )
    return ContainerEngine(name)


def _tail(text: str | None, limit: int = 600) -> str:
    """报错里带的引擎输出：去空白 + 只留尾部（docker 的失败原因在最后几行，前面全是层进度）。"""
    s = (text or "").strip()
    return s if len(s) <= limit else "…" + s[-limit:]
