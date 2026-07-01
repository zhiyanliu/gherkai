"""组合根：把抽象的 core 接线到具体的引擎子进程（ADR 0016）。

core 只认 `EngineResolver`（按 engine 名给一个 `Engine`）；这里 new 出每个引擎的
`SubprocessEngine`（cmd 指向各自语言的 worker），core 永不 import 引擎、不知 worker 是子进程。

WebUI 的 bootstrap 将来复用本模块——组合根逻辑（引擎注册表、读 feature）与命令行皮（argparse、
渲染）分开，故放在 compose.py 而非 __main__.py。
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from core.adapters.subprocess_engine import SubprocessEngine
from core.ports import Engine
from core.scope import FeatureSource


def new_run_id() -> str:
    """生成一个 run_id（组合根职责，ADR 0027）。

    对调用方不透明，只保证「可排序（时间戳前缀）+ 抗碰撞（随机尾）」。格式是 compose 实现细节、
    不入 ADR 契约。形如 20260629T141207Z-a3f9c1。
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{secrets.token_hex(3)}"


def now_iso() -> str:
    """manifest created_at 时间戳（组合根取时钟，core 不取，ADR 0027）。"""
    return datetime.now(timezone.utc).isoformat()


def repo_root(start: Path | None = None) -> Path:
    """定位仓库根（含 core/ 与 engines/ 的目录）。

    从本文件位置上溯：cli/cli/compose.py → cli/ → 仓库根。允许传入覆盖（测试用）。
    """
    if start is not None:
        return start
    return Path(__file__).resolve().parents[2]


def build_engines(
    repo: Path,
    *,
    nova_logs_dir: str | Path | None = None,
    midscene_run_dir: str | Path | None = None,
) -> dict[str, Engine]:
    """每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。

    两个引擎"spawn 子进程 + 讲同一套 ADR 0024 协议"形状一致，故都是同一个 SubprocessEngine 类、
    只是 cmd/cwd 不同——无需两个具名 adapter 类。

    产物持久落点（两引擎对称，经环境变量传给 SDK，ADR 0027）——None 时各自用 SDK 默认（相对 worker cwd
    的固定目录 / 系统临时目录，会被清理或每 run 覆盖）：
    - nova_logs_dir → `NOVA_LOGS_DIR` → Nova SDK `logs_directory`，trajectory 落这里。
    - midscene_run_dir → `MIDSCENE_RUN_DIR` → Midscene SDK 的 run 根目录（report/dump/log 全在其下），
      report.html 落这里。**必须传绝对路径**：SDK 用 `path.resolve(process.cwd(), MIDSCENE_RUN_DIR)`
      相对 worker cwd 解析，相对路径会落错地方（与 Nova trajectory 早期踩的 cwd 歧义同源）。
    """
    novaact_dir = repo / "engines" / "novaact"
    midscene_dir = repo / "engines" / "midscene"

    # 完整继承当前环境（AWS 凭证等）再叠加产物落点——SubprocessEngine 的 env 非 None 时整体替换，故须带 os.environ。
    nova_env = {**os.environ, "NOVA_LOGS_DIR": str(nova_logs_dir)} if nova_logs_dir is not None else None
    midscene_env = {**os.environ, "MIDSCENE_RUN_DIR": str(midscene_run_dir)} if midscene_run_dir is not None else None
    return {
        # Nova Act 引擎：novaact venv 的 python 跑 worker
        "novaact": SubprocessEngine(
            cmd=[
                str(novaact_dir / ".venv" / "bin" / "python"),
                str(novaact_dir / "worker" / "run_scope.py"),
            ],
            cwd=str(novaact_dir),
            env=nova_env,
        ),
        # Midscene 引擎：node --import tsx 跑 TS worker。
        # 用 `--import tsx`（不是 tsx 二进制、也不是 `tsx/esm`）：tsx loader 加载进**同一个** node
        # 进程，不 spawn 子-node——否则 EVENTS_FD（经 pass_fds 继承）只到 tsx 包装器、传不到真正跑
        # worker 的子进程 → fd3 EBADF（实测踩过）。`--import tsx` 既继承 fd、又能跑 .ts。
        "midscene": SubprocessEngine(
            cmd=["node", "--import", "tsx", str(midscene_dir / "worker" / "run-scope.ts")],
            cwd=str(midscene_dir),
            env=midscene_env,
        ),
    }


def make_resolver(engines: dict[str, Engine]):
    """dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。"""

    def resolver(engine_name: str) -> Engine:
        try:
            return engines[engine_name]
        except KeyError:
            raise ValueError(
                f"未知引擎 {engine_name!r}（支持 {'/'.join(sorted(engines))}）"
            ) from None

    return resolver


def load_feature(path: Path, repo: Path) -> FeatureSource:
    """读 .feature 文件 → core 要的 FeatureSource（uri+text）。

    core 不碰文件系统（ADR 0025）：读文件、推导稳定 uri 是组合根的事。
    uri 取相对仓库根的路径（稳定可读的 id 前缀）；不在仓库内则退用绝对路径。
    """
    resolved = path.resolve()
    try:
        uri = str(resolved.relative_to(repo))
    except ValueError:
        uri = str(resolved)
    return FeatureSource(uri=uri, text=resolved.read_text(encoding="utf-8"))
