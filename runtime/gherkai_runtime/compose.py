"""组合根：把抽象的 core 接线到具体的引擎子进程（ADR 0016）。

core 只认 `EngineResolver`（按 engine 名给一个 `Engine`）；这里 new 出每个引擎的
`SubprocessEngine`（cmd 指向各自语言的 worker），core 永不 import 引擎、不知 worker 是子进程。

WebUI 的 bootstrap 将来复用本模块——组合根逻辑（引擎注册表、读 feature）与命令行皮（argparse、
渲染）分开，故放在 compose.py 而非 __main__.py。
"""
from __future__ import annotations

import importlib.util
import json
import os
import secrets
import shlex
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version
from pathlib import Path

from gherkai_core.adapters.subprocess_engine import SubprocessEngine
from gherkai_core.ports import Engine, ReportStore, ResultStore, RunStore
from gherkai_core.scope import FeatureSource


# Nova 单 act 时间上界（ADR 0024 act 有界返回）——**组合根持单一真值**，同时派生两端（消除漂移）：
# ① 注入 worker 的 NOVA_ACT_TIMEOUT_S env（worker run_scope.py 读它，缺省也是 120、此处显式注入使两端同源；
#    subprocess 档见 build_engines、Fargate 档见 build_fargate_engines——两档都注，否则该档的 worker 落回自带字面量）；
# ② 算 Nova 的 grace 下限（见 engine_min_grace）。env 可覆盖（真跑标定/调优）。
NOVA_ACT_TIMEOUT_S = int(os.environ.get("NOVA_ACT_TIMEOUT_S", "120"))  # SDK 允许 [2,1800]
# grace 余量（ADR 0024/0028 grace 硬约束的 margin）：单 step 最坏耗时 + 会话释放 + 余量。→ Nova grace 下限 ≈
# ACT_TIMEOUT_S + margin。**已真容器标定**（ADR 0032「真容器校准结论」）：4 次真跑实测 SIGTERM 落 act 中途 →
# `stopping→executionStopped` 最坏 21s，但其中 ~11s 已坐实为 ECS 记录 executionStoppedAt 的平台侧滞后（worker 已退），
# subprocess 档不存在该段——真实预算 = 会话释放 ≤9s，故 margin 60→30（grace 下限 180→150）仍留 ~3x 余量。
# env 可覆盖（再标定/调优）。
NOVA_GRACE_MARGIN_S = int(os.environ.get("NOVA_GRACE_MARGIN_S", "30"))

# Midscene 的 grace 下限（ADR 0024 grace 硬约束）：Midscene worker 无「可控 act timeout」概念（不像 Nova 的
# ACT_TIMEOUT_S），但它的 **SIGTERM onSignal 收尾路径本身有确定的超时预算**，grace 必须够它跑完、否则会被
# SIGKILL 打断到一半（会话释放虽由「先释放会话再抢传」的排序 + Stop 预算保住不泄漏，但 worker 退不干净、
# 中断兜底 report 抢传被截断）。下限 = onSignal 最坏串行路径的超时预算之和 + 余量，各段与 worker 常量同源：
#   inflight settle(INFLIGHT_SETTLE_MS≈1.5s) + 会话 Stop(STOP_SESSION_BUDGET_MS≈3s) + browser.close race(≈3s)
#   + 中断兜底 snapshotReport 上传(UPLOAD_TIMEOUT_MS≈10s) ≈ 17.5s，取 25s 留余量。**有界的待真跑标定量**，
# 可 env 覆盖。（历史：曾为 0.0=无下限，导致 midscene-only run 默认 grace 回落 ScheduleOpts 的 5s < 上传超时
# 10s，SIGTERM 时 worker 可能被 SIGKILL、兜底抢传截断——见 ADR 0024 grace 硬约束条。）
MIDSCENE_GRACE_MIN_S = int(os.environ.get("MIDSCENE_GRACE_MIN_S", "25"))


# ============================================================================
# 两层命名（ADR 0033）：`--prefix`（默认 gherkai-）批量决定所有名字类资源的默认名；单资源 override 给完整终值。
# **单一事实源**：CDK 部署吃同一 prefix → CDK 建的名 = cli 推导的默认名，不漂移。覆盖时 prefix 自然不参与
# （覆盖 = 直接给完整名 = 不走「拼默认名」路径，无特判）。prefix 含分隔符、原样拼（用户负责，防粘连——同 S3 prefix 先例）。
# ============================================================================
# 资源命名真源已拆到 gherkai_runtime.names（零依赖，iac 直接 import）；此处 re-export 保既有引用不动。
from gherkai_runtime.names import (  # noqa: E402
    DEFAULT_PREFIX,
    default_name,
    task_def_name,
    container_name,
    ssm_path,
)
from gherkai_runtime import names as _names  # noqa: E402


def engine_min_grace(engine_name: str) -> float:
    """按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。

    Nova：`ACT_TIMEOUT_S + margin`（SIGTERM 落长 act 中途须等 act 有界返回才协作退释放会话）。
    Midscene：`MIDSCENE_GRACE_MIN_S`（无可控 act timeout，但 onSignal 收尾路径的超时预算之和须 < grace，
    否则 worker 被 SIGKILL、中断兜底抢传截断——见该常量注释）。
    组合根算好后作 `ScheduleOpts.min_grace_s` 传给 core，core 只 enforce「grace ≥ 此下限」的引擎无关关系。
    混引擎 run 由调用方取各引擎下限的 max（grace 是 run 级单值）。
    （未来更干净：引擎经 Engine port 自声明 min_grace，替代这里的 engine_name 分支，ADR 0024 记为 defer。）
    """
    if engine_name == "novaact":
        return float(NOVA_ACT_TIMEOUT_S + NOVA_GRACE_MARGIN_S)
    if engine_name == "midscene":
        return float(MIDSCENE_GRACE_MIN_S)
    return 0.0


def new_run_id() -> str:
    """生成一个 run_id（组合根职责，ADR 0027）。

    对调用方不透明，只保证「可排序（时间戳前缀）+ 抗碰撞（随机尾）」。格式是 compose 实现细节、
    不入 ADR 契约。形如 20260629T141207Z-a3f9c1。
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{secrets.token_hex(3)}"


def now_iso() -> str:
    """**唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。

    三个宿主（cli 前台 run / local per-run 进程 / 推进器 Lambda）全调本函数——曾各写一份 `_now_iso`、
    两种 ISO 格式（`isoformat()` 带微秒+`+00:00` vs `strftime` 的 `…Z`），同一份 RunState 内 started_at 与
    claimed_at/ended_at 格式不同，`status --json` 的机读消费者要兼容两种（ADR 0016「组合根取时钟」）。
    """
    return datetime.now(timezone.utc).isoformat()


def parse_iso(ts: str) -> datetime:
    """`now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。

    容 `…Z` 后缀（历史落盘的旧格式，`fromisoformat` 在 3.10 不认它）——读侧宽容，写侧只出 `now_iso()` 一种。
    """
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def run_duration_ms(state) -> float | None:
    """detached run 的 run 级墙钟（毫秒）= RunState `ended_at` − `started_at`（提交落库到 finalize commit，含排队/起容器；
    ADR 0024「三级执行时长」detached 条）。两端任一缺或解析不了 → None（报告显「?」——派生指标，绝不让收尾因它炸）。
    宿主在 finalize_report 前调，算好传给 core。"""
    if state is None or not getattr(state, "started_at", None) or not getattr(state, "ended_at", None):
        return None
    try:
        return (parse_iso(state.ended_at) - parse_iso(state.started_at)).total_seconds() * 1000.0
    except ValueError:
        return None


# ============================================================================
# worker 定位链（ADR 0037 决策 3）：**安装与拉起正交**——四级顺序解析「用什么命令 spawn 某引擎 worker」。
# dev 与分发**同一条链、不设 dev 模式特判**：分发后没有 repo，任何靠 repo 结构的隐式行为都是漂移面
# （这条链取代了曾经上溯定位仓库根、把 cmd 焊在 `engines/*/` 上的 `repo_root()`——它已全部消费点退役）。
# 四级全 miss → WorkerNotFoundError，**退码语义按调用点分叉、不在链里统一退码**：`run`/`submit` 在 spawn 前
# 退 2（不进 job 级 engine_error）、`list-deterministic` 退 2、`plan` 保持 ADR 0036 决策 4 的 best-effort 降级。
# ============================================================================

# 各级的引擎特定供给方（引擎特定值住组合根，core 不认）：
_WORKER_PY_MODULE = {"novaact": "gherkai_worker_novaact"}   # ② 同 venv import 名（仅 Python 引擎有此级）
_WORKER_BIN = {  # ③ PATH 上的可执行名（Python 侧由 console script 提供、Node 侧由 npm i -g 提供）
    "novaact": "gherkai-worker-novaact",
    "midscene": "gherkai-worker-midscene",
}
# ④ 兜底拉起：(拉起器, 拼命令)——拉起器须在 PATH 且版本须是纯发行版，见 resolve_worker_cmd。
# **只有 novaact/uvx**：fd 预演实测 uvx 把 EVENTS_FD 原样传给子进程（同一 pipe inode、事件到达）且转发 SIGTERM；
# npx **不**穿透——node 子进程里 EVENTS_FD 号上是 npm 自己的另一条 FIFO、写即 EBADF，事件全丢——故 midscene 无第四级，
# 前三级全 miss 直接报安装指引（ADR 0037 决策 3「预演不过则降为报错 + 安装指引」）。
_WORKER_FALLBACK = {
    "novaact": ("uvx", lambda v: ["uvx", f"gherkai-worker-novaact=={v}"]),
}
# 全 miss 时给用户的安装指引（每引擎一条，两种语言的地盘不同）。
_WORKER_INSTALL_HINT = {
    "novaact": "装法：uv tool install 'gherkai[local]'（worker 与 CLI 同一个 venv，离线可用）",
    "midscene": "装法：npm i -g @gherkai/worker-midscene（需 Node ≥ 22）",
}


@dataclass(frozen=True)
class WorkerCmd:
    """一个引擎 worker 的拉起方式 = 定位链的解析结果（ADR 0037 决策 3）。

    cmd/cwd 直接喂 `SubprocessEngine`；**cwd 恒可为 None＝继承当前进程 CWD**——worker 不再有专属 cwd
    （故 local 档产物落点必须是绝对路径，见 build_engines）。source 是人读的命中级别描述，只供
    `list-engines` 自省/诊断，**不参与任何分支判断**（别按它做逻辑，否则级别措辞成了隐式契约）。
    """

    cmd: list[str]
    cwd: str | None
    source: str


class WorkerSelfDescribeError(RuntimeError):
    """worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方
    `steps/` 目录里的文件加载失败（ADR 0037 决策 4 的 fail-loud），属使用方代码错误，调用点一律退 2、不降级
    （`plan` 对 miss 降级，对本错误不降级：静默无标注 = 把定制 step 悄悄换成 AI 判定）。"""

    def __init__(self, engine: str, returncode: int, stderr_tail: str, what: str):
        self.engine, self.returncode, self.stderr_tail = engine, returncode, stderr_tail
        super().__init__(f"引擎 {engine} 的 {what}失败（exit {returncode}）：{stderr_tail}")


class WorkerNotFoundError(RuntimeError):
    """定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退码交调用点。

    **继承 RuntimeError 是有意的**：既有「worker 起不来 → RuntimeError」的调用点语义
    （`list-deterministic` 退 2、`plan` best-effort 降级）自动涵盖它；`run`/`submit` 另在 spawn 前
    显式 catch 本类型做 preflight（退 2，不进 job 级 engine_error）。
    """

    def __init__(self, engine: str, hint: str) -> None:
        self.engine = engine
        self.hint = hint
        super().__init__(hint)


class _UnavailableEngine:
    """某引擎这次装配不出来时的「一用即抛」空腿——两档共用（local: ADR 0037 决策 3；cloud: ADR 0038）。

    存在的理由：两个 builder 都恒建两条腿，而一次 run 往往只用一个引擎——某引擎装配不出**不该连坐**
    （local 档 dev 下 midscene 无已安装 npm 包即常态，须走定位链第一级 env 覆写；cloud 档则是「本 run 没用到
    该引擎、故 definition 里也没解析它的 worker revision」，是正常态）。装一条空腿保住「引擎名恒在册」
    （resolver / list-engines 语义不变），把 miss 的爆点挪到真要起它那一刻，且爆的是带修复指引的
    结构化异常——而非 resolver 的「未知引擎」（那会把「没装/未解析」误导成「名字拼错」）。
    正门仍是调用点 preflight：`run`/`submit` 先对本次 plan 用到的引擎 `resolve_worker_cmd`（local）/
    解析 worker variant（cloud）、miss 即退 2。

    **`run_scope` 与 `start_scope` 都抛**：两档的宿主入口不同（同步 run 走 `run_scope`、无状态推进器的
    CloudLauncher 走 `start_scope`），只堵一个会让另一档退化成 `AttributeError`（丢掉带指引的异常）。
    """

    def __init__(self, miss: Exception) -> None:
        self._miss = miss

    def run_scope(self, job, raw_sink=None):
        raise self._miss

    def start_scope(self, job):
        raise self._miss


def is_pure_release(v: str) -> bool:
    """版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。

    dev/post/本地段版本**不可能存在于 PyPI/npm**（它们由 uv-dynamic-versioning 从 tag 之后的 commit 派生，
    ADR 0037 决策 2b），拿它 uvx/npx 只会解析失败——把「worker 没装」的清晰指引换成难懂的网络/解析错误。
    """
    from packaging.version import InvalidVersion, Version

    try:
        pv = Version(v)
    except InvalidVersion:
        return False
    return not (pv.is_devrelease or pv.is_postrelease or pv.local)


_is_pure_release = is_pure_release  # 模块内旧名（定位链/skew 判据处仍用）；跨包（deploy 的基底同步）用公开名


def resolve_worker_cmd(engine: str, *, version: str | None = None) -> WorkerCmd:
    """按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。

    1. env `GHERKAI_WORKER_<ENGINE>_CMD`（`shlex` 拆分）+ 可选配套 `GHERKAI_WORKER_<ENGINE>_CWD`——显式覆写：
       contributor 指向 repo 内源码、调试、自建 worker 都走这里。**cwd 配套存在的理由**：`node --import tsx`
       的裸 specifier `tsx` 按 cwd 上溯 `node_modules` 解析，实测在无关目录下直接 `Cannot find package 'tsx'`。
    2. 同 venv 入口（**仅 Python 引擎**）：`find_spec` 命中 → `[sys.executable, "-m", <import 名>]`。
       **无包装层是硬要求**——EVENTS_FD 经 `pass_fds` 只到**被直接 spawn 的那个进程**（ADR 0024 三通道），
       包装进程会吞 fd3（midscene 换 `--import tsx` 那次踩过：tsx 二进制再 spawn 子-node → fd3 EBADF）。
    3. PATH 上的可执行 `gherkai-worker-<engine>`（Python 侧 console script / Node 侧 `npm i -g`）。
    4. 兜底拉起 `uvx <发行名>==<版本>`（**仅 novaact**），**双条件**：①版本是纯发行版（见 `_is_pure_release`）；
       ②`uvx` 在 PATH。任一不成立即跳过本级（直接判 miss，报安装指引更有用）。
       uvx 是包装进程但**实测不吞 fd3**：子进程里 EVENTS_FD 与父侧同一 pipe inode、事件到达，SIGTERM 也转发。
       midscene **没有本级**：`npx -y <包>@<版本>` 实测把 fd 换掉（node 里该号上是 npm 自己的 FIFO、写即 EBADF），
       事件全丢，按「预演不过则降为报错 + 安装指引」处置（ADR 0037 决策 3）。
    version：第四级 pin 的版本，缺省取本包（gherkai-runtime）版本——worker 与 CLI `==` lockstep
    （ADR 0037 决策 2b），未装成包（源码直跑）时取不到 → 第四级跳过。
    """
    if engine not in _names.ENGINES:
        raise ValueError(f"未知引擎：{engine!r}（可用：{sorted(_names.ENGINES)}）")
    env_key = f"GHERKAI_WORKER_{engine.upper()}_CMD"
    raw = os.environ.get(env_key)
    if raw and raw.strip():
        try:
            argv = shlex.split(raw)
        except ValueError as e:
            # 引号不配对之类：**不静默落到下一级**——用户明确指了一个 worker，悄悄换成别的（或报「没装」）
            # 是最难查的那种错。点名 env 让他修（miss 语义走同一条分叉：调用点退 2 / plan 降级）。
            raise WorkerNotFoundError(
                engine, f"env {env_key} 的值无法解析（{e}）：{raw!r}——修正引号，"
                        f"或 unset 它改用已安装的 worker") from e
        return WorkerCmd(cmd=argv, cwd=os.environ.get(f"GHERKAI_WORKER_{engine.upper()}_CWD"),
                         source=f"env {env_key}")
    module = _WORKER_PY_MODULE.get(engine)
    if module is not None and _find_worker_spec(module):
        # cwd=None：同 venv 的 `-m` 入口不依赖任何相对路径，继承调用者 CWD 即可（也让相对 `steps/` 等
        # 用户视角的路径不被 worker 侧的隐式 cwd 扭曲——落点/steps 一律绝对路径注入）。
        return WorkerCmd(cmd=[sys.executable, "-m", module], cwd=None, source=f"同 venv 模块 {module}")
    bin_name = _WORKER_BIN[engine]
    found = shutil.which(bin_name)
    if found:
        return WorkerCmd(cmd=[found], cwd=None, source=f"PATH 可执行 {bin_name}")
    fallback = _WORKER_FALLBACK.get(engine)  # midscene 无第四级（见 _WORKER_FALLBACK 注）
    v = version if version is not None else _runtime_version()
    if fallback is not None and v is not None and _is_pure_release(v) and shutil.which(fallback[0]):
        launcher, build = fallback
        return WorkerCmd(cmd=build(v), cwd=None, source=f"{launcher} 兜底拉起（版本 {v}）")
    raise WorkerNotFoundError(
        engine,
        f"引擎 {engine} 的 worker 运行时未找到。"
        f"{_WORKER_INSTALL_HINT[engine]}；或用 env {env_key}（+ 可选 "
        f"GHERKAI_WORKER_{engine.upper()}_CWD）显式指向自建/仓库内 worker",
    )


def _find_worker_spec(module: str) -> bool:
    """`find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。"""
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def _runtime_version() -> str | None:
    """本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（源码直跑）→ None。"""
    try:
        return _dist_version("gherkai-runtime")
    except PackageNotFoundError:
        return None


def build_engines(
    *,
    nova_logs_dir: str | Path | None = None,
    midscene_run_dir: str | Path | None = None,
    region: str | None = None,
    profile: str | None = None,
    extra_http_headers: dict[str, str] | None = None,
    steps_dir: str | Path | None = None,
    no_artifacts: bool = False,
    worker_log=None,
) -> dict[str, Engine]:
    """每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。

    worker_log（ADR 0041 决策二）：worker stdout/stderr 透传的落点文件句柄；None = 本进程 stderr（默认）。组合根只转发。

    no_artifacts（`--no-report`，ADR 0037 决策 3）：经 env `GHERKAI_NO_ARTIFACTS=1` 告知 worker **不生成、不上报**引擎
    原生产物（Midscene 关 generateReport；Nova SDK 无关闭开关、不传 logs_directory 让它写进自己 mkdtemp 的临时目录），
    此时两个落点参数应为 None——「真不生成」而非「落临时目录」。

    两个引擎"spawn 子进程 + 讲同一套 ADR 0024 协议"形状一致，故都是同一个 SubprocessEngine 类、
    只是 cmd/cwd 不同——无需两个具名 adapter 类。

    **cmd/cwd 来自 `resolve_worker_cmd` 的四级定位链**（ADR 0037 决策 3），不再由仓库结构推导；
    某引擎 miss 只让那条腿变成「一用即报错」（见 `_UnavailableEngine`），不连坐另一条。

    产物持久落点（两引擎对称，经环境变量传给 SDK，ADR 0027）——**调用方应恒给绝对路径、不给 None**：
    worker 已无专属 cwd（定位链后 cwd 多为 None＝继承调用者 CWD，ADR 0037 决策 3），落 SDK 默认相对目录
    会写进用户 CWD，故 `--no-report` 档也由 CLI 注入系统临时目录下 run 专属的绝对落点。None 仅为兼容
    「真不关心产物落哪」的调用者（回落 SDK 默认，行为随 CWD 漂）：
    - nova_logs_dir → `NOVA_LOGS_DIR` → Nova SDK `logs_directory`，trajectory 落这里。
    - midscene_run_dir → `MIDSCENE_RUN_DIR` → Midscene SDK 的 run 根目录（report/dump/log 全在其下），
      report.html 落这里。**必须传绝对路径**：SDK 用 `path.resolve(process.cwd(), MIDSCENE_RUN_DIR)`
      相对 worker cwd 解析，相对路径会落错地方（与 Nova trajectory 早期踩的 cwd 歧义同源）。

    steps_dir（ADR 0037 决策 4）：使用方确定性 step 目录的**绝对路径**，经 env `GHERKAI_STEPS_DIR` 注给
    **两个** worker（worker 启动时排序递归加载、注册进自己那张注册表）。约定解析（flag > env > `./steps`）
    在提交侧、值随 definition（`RunMeta.steps_dir`）走——本函数只搬运读回的值，**不自己解析 `./steps`**
    （三个宿主 CWD 各不相同，重解析必分叉，ADR 0034）。None＝无使用方 step（worker 只有内建脚手架）。

    **不注入产物 S3 上传落点**（`ARTIFACT_S3_BUCKET`/`PREFIX`）：本函数是 local 档，worker 恒报 `file://`。
    上传落点由 `build_fargate_engines` 注入（cloud 档，ADR 0029）；`subprocess worker + 注入 S3 落点` 的
    内部预演由 `tools/e2e_harness.py` 自拼 env 承载（ADR 0016 决策 B），不经本函数。

    region/profile（ADR 0016 决策 C）——组合根解析后的 AWS region（已由 `resolve_region` 落实成具体字符串：`--region` >
    `AWS_REGION` > `AWS_DEFAULT_REGION` > profile config）与 profile（`--profile` > `AWS_PROFILE`）：非 None 时经 `_inject_aws`
    显式写进注入 env（`AWS_REGION`/`AWS_PROFILE`）覆盖继承值——使 `--region`/`--profile` 真贯通到 subprocess worker
    （EventSink/JobSource/ArtifactUploader/Nova Workflow/Midscene fromNodeProviderChain 建 client 都读它们）、与 core store
    同源、消除分叉。None＝不写（真无值、fail-loud，对齐 store 宽容）。**subprocess 两个引擎都注入**（Nova/Midscene 补建路径见下）。
    注意：本函数**只建 subprocess 两个引擎**（local 执行）。cloud 执行由 `build_fargate_engines` 接管——组合根
    （`__main__`）按 `--backend` 分流：cloud ⇒ `build_fargate_engines`（FargateEngine）、否则本函数（SubprocessEngine）。
    **FargateEngine 侧只注入 region、不注入 profile**（容器用 task role，profile 是本机 `~/.aws` 概念、注入会
    ProfileNotFound 盖过 task role——正确的非对称，ADR 0016 决策 C）。
    """
    # 完整继承当前环境（AWS 凭证等）再叠加产物落点——SubprocessEngine 的 env 非 None 时整体替换，故须带 os.environ。
    # 两引擎共注的附加 env（都是「有值才注、无值零变化」）：
    # - 浏览器 context 级额外请求头（ADR 0035 决策 4，如 ngrok-skip-browser-warning）：JSON 经 env 注给
    #   两个 worker，worker 在 browser context 上 setExtraHTTPHeaders（纯 CDP 命令，无回调）。
    # - 使用方确定性 step 目录（ADR 0037 决策 4）：worker 只认这个 env，绝对路径、约定逻辑不进 worker。
    common_env: dict[str, str] = {}
    if extra_http_headers:
        common_env["GHERKAI_EXTRA_HTTP_HEADERS"] = json.dumps(extra_http_headers, ensure_ascii=False)
    if steps_dir is not None:
        common_env["GHERKAI_STEPS_DIR"] = str(steps_dir)
    if no_artifacts:
        common_env["GHERKAI_NO_ARTIFACTS"] = "1"

    def _inject_aws(env: dict) -> None:
        # --region/--profile 解析值覆盖继承的 AWS_REGION/AWS_PROFILE（None＝不写、留 boto 默认链/profile config
        # 兜底，ADR 0016 决策 C）。subprocess worker 的 EventSink/JobSource/ArtifactUploader/Nova Workflow 都读
        # 这两个 env 建 client——显式写入使 `--region`/`--profile` 真生效、与 core store 侧同源、消除分叉。
        if region is not None:
            env["AWS_REGION"] = region
        if profile is not None:
            env["AWS_PROFILE"] = profile

    def _env(local_dir: str | Path | None, local_key: str) -> dict | None:
        # local 落点 env + 共注附加 env（headers / steps_dir）。全无 → None（worker 全用继承 env + SDK 默认）。
        if local_dir is None and not common_env:
            return None
        env = {**os.environ}
        if local_dir is not None:
            env[local_key] = str(local_dir)
        env.update(common_env)
        _inject_aws(env)
        return env

    nova_env = _env(nova_logs_dir, "NOVA_LOGS_DIR")
    midscene_env = _env(midscene_run_dir, "MIDSCENE_RUN_DIR")
    # Nova 的 act timeout **双端同源**（ADR 0024 grace 硬约束）：组合根持 NOVA_ACT_TIMEOUT_S 单一真值，
    # 显式注入给 worker（消除「worker 私有默认 120」与「组合根 grace 下限」两处独立 120 的漂移）。
    # nova_env 为 None（调用方未给产物落点）时也要建一份注入——故补一个继承 os.environ 的 env。
    if nova_env is None:
        nova_env = {**os.environ}
        _inject_aws(nova_env)  # 补建路径也须叠加 --region/--profile（Nova Workflow 的 nova-act client 读 AWS_REGION/凭证）
    nova_env["NOVA_ACT_TIMEOUT_S"] = str(NOVA_ACT_TIMEOUT_S)
    # Midscene 补建同理（对称，ADR 0016 决策 C）：midscene_env 为 None（未给落点、无共注 env）且 --region/--profile
    # 有值时也须建 env 注入——否则 midscene worker 继承 os.environ、拿不到 --profile 覆盖，而它经 fromNodeProviderChain()
    # 消费凭证做 AgentCore/Bedrock 鉴权（真消费、非无害）。仅在有值时补建（无值则继承 os.environ 本就够、免无谓拷贝）。
    if midscene_env is None and (region is not None or profile is not None):
        midscene_env = {**os.environ}
        _inject_aws(midscene_env)

    def _leg(engine: str, env: dict | None) -> Engine:
        # 定位链解析（ADR 0037 决策 3）。**per-engine 容错**：本函数恒建两条腿、一次 run 却可能只用一个
        # 引擎，故 miss 不连坐——装成一用即报错的空腿（爆点挪到真 spawn 时，带安装指引）。
        # 「worker 必须是被直接 spawn 的那个进程」（fd3 经 pass_fds 继承，ADR 0024）是定位链的不变量，
        # 由各级供给方保证（见 resolve_worker_cmd 第 2 级注释）——本处只转发 cmd/cwd。
        try:
            wc = resolve_worker_cmd(engine)
        except WorkerNotFoundError as miss:
            return _UnavailableEngine(miss)
        return SubprocessEngine(cmd=wc.cmd, cwd=wc.cwd, env=env, log_sink=worker_log)

    return {"novaact": _leg("novaact", nova_env), "midscene": _leg("midscene", midscene_env)}


def _ask_worker(engine: str, flag: str, *, what: str, steps_dir: str | Path | None = None,
                timeout_s: float = 60.0, payload: bytes | None = None) -> list:
    """spawn 一次某引擎 worker 的**自述入口**、收一行 JSON（ADR 0036 决策 2/4 的共同机制）。

    自述入口不建会话、不读 job、零 AWS，秒级返回。两个自述入口（`--list-deterministic` /
    `--match-steps`）只差 flag、stdin 与错误措辞，故共用本体（曾各抄一份 spawn+诊断，会漂移）。
    - worker cmd 走定位链（ADR 0037 决策 3）：miss → WorkerNotFoundError（RuntimeError 子类，调用点分叉）。
    - steps_dir（ADR 0037 决策 4）经 env 注入：三个自述入口同样加载 steps 目录，故 `list-deterministic`
      与 `plan` 标注反映使用方定制 step（注册表 = 内建脚手架 + 加载的使用方模块）。
    引擎名非法 → ValueError；worker 非 0 退出 → WorkerSelfDescribeError（如 steps 加载失败，调用点退 2 不降级）；
    起不来/超时/输出非 JSON → RuntimeError 带诊断。
    """
    import subprocess

    wc = resolve_worker_cmd(engine)  # 引擎名非法 → ValueError（定位链里查一次即够，此处不复刻校验）
    cmd = list(wc.cmd) + [flag]
    env = {**os.environ, "GHERKAI_STEPS_DIR": str(steps_dir)} if steps_dir is not None else None
    try:
        proc = subprocess.run(cmd, cwd=wc.cwd, env=env, capture_output=True,
                              timeout=timeout_s, input=payload)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"引擎 {engine} 的 worker 起不来（{e}）——用的是「{wc.source}」，该命令不可执行？"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"引擎 {engine} 的 {what}超时（{timeout_s:.0f}s）") from e
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", errors="replace")[-400:]
        raise WorkerSelfDescribeError(engine, proc.returncode, tail, what)
    try:
        return json.loads(proc.stdout.decode("utf-8"))
    except ValueError as e:
        raise RuntimeError(f"引擎 {engine} 的 {what}输出非 JSON：{proc.stdout[:200]!r}") from e


def query_deterministic(engine: str, *, steps_dir: str | Path | None = None,
                        timeout_s: float = 60.0) -> list[dict]:
    """查询某引擎 worker 的确定性能力清单（ADR 0036）：spawn `worker --list-deterministic` 收 JSON。

    真值单一：清单由 worker 注册表代码即时生成（内建脚手架 + steps_dir 加载的使用方模块，ADR 0037 决策 4）。
    异常语义见 `_ask_worker`（调用方 `list-deterministic` 归退 2）。
    """
    return _ask_worker(engine, "--list-deterministic", what="worker 自述",
                       steps_dir=steps_dir, timeout_s=timeout_s)


def match_deterministic(engine: str, texts: list[str], *, steps_dir: str | Path | None = None,
                        timeout_s: float = 60.0) -> list[dict | None]:
    """批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。

    spawn `worker --match-steps`、stdin 喂 JSON 文本数组、收逐条结果（None=走 AI /
    {"pattern","description"}=命中 / {"conflict":[...]}=命中多条——真跑将 error，plan 预检提前暴露）。
    匹配语义 100% 在 worker（同一注册表同一 search 实现），CLI 零复刻（ADR 0022「匹配放 worker」红线）。
    异常语义同 query_deterministic（调用方 plan 做 best-effort 降级）。
    """
    return _ask_worker(engine, "--match-steps", what="match 查询", steps_dir=steps_dir,
                       timeout_s=timeout_s, payload=json.dumps(texts, ensure_ascii=False).encode("utf-8"))


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


# ============================================================================
# Store 装配（ADR 0016「cli backend 选择」/ 0030 决定六·七）：两个后端对称、都在 compose 可复用
# （cli 是第一个调用者，WebUI 直接复用这两个函数、不经 cli）。各返回：
#   (run_store, result_store, report_store, make_artifacts)

def local_artifact_locations(report_dir: str, run_id: str) -> dict:
    """local 档一个 run 的产物落点（全 file:// URI）：run_meta / run_state / jobs_dir / report_index。**单点**：
    `run` 结束打印、`status` 终态打印、`--json` 的 artifacts 都从这里拼（曾只在 run 路径的闭包里拼，status 到终态
    只打 ended_at、用户得自己找报告）。report_index 是**约定落点**（LocalReportStore 的 index.html），不代表已写成——
    run 路径拿 finalize 返回值覆盖/省略它（ADR 0030 决定三写失败隔离），status 路径按约定给。"""
    run_dir = (Path(report_dir) / run_id).resolve()
    return {
        "run_meta": run_dir.joinpath("run_meta.json").as_uri(),
        "run_state": run_dir.joinpath("run_state.json").as_uri(),
        "jobs_dir": run_dir.joinpath("jobs").as_uri(),
        "report_index": run_dir.joinpath("index.html").as_uri(),
    }


def cloud_artifact_locations(*, bucket: str, report_prefix: str, table: str, run_id: str) -> dict:
    """cloud 档一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore / S3ReportStore 的 key 布局
    `<report_prefix>/<run_id>/…`），run_meta / run_state 为 ddb:// 诊断指针（纯展示、不被解析）。单点理由同 local。
    report_prefix = 后端 REPORT_DIR（与 submit 的 --report-dir 一致，preflight 已比对）。"""
    pfx = _normalize_prefix(report_prefix)
    return {
        "run_meta": f"ddb://{table}/{run_id}#META",
        "run_state": f"ddb://{table}/{run_id}#STATE",
        "jobs_dir": f"s3://{bucket}/{pfx}{run_id}/jobs/",
        "report_index": f"s3://{bucket}/{pfx}{run_id}/index.html",
    }

# make_artifacts(run_id, report_index) -> dict：把 --json 的 artifacts 落点指针按后端组装、全 URI 化
#   （local file:// / cloud s3://+ddb://）；report_index=None（report 写失败被隔离）则省略该键、不放裸 'None'。
# ============================================================================


def _normalize_prefix(prefix: str) -> str:
    """S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。"""
    return prefix + "/" if prefix and not prefix.endswith("/") else prefix


def build_local_stores(*, report_dir: str | Path):
    """本地文件三层 store + local artifacts descriptor（file:// 完整路径）。

    落 <report_dir>/<run_id>/：RunStore(run_meta+run_state) + ResultStore(jobs/) + ReportStore(index/manifest)。
    """
    from gherkai_core.adapters.report_store.local import LocalReportStore
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore

    root = Path(report_dir)
    run_store: RunStore = LocalRunStore(root)
    result_store: ResultStore = LocalResultStore(root)
    report_store: ReportStore = LocalReportStore(root)

    def make_artifacts(run_id: str, report_index) -> dict:
        # 落点走 local_artifact_locations 单点（status 终态打印同一份）；report_index 以 finalize 返回值为准：
        # None = report 写失败被隔离（ADR 0030 决定三）→ 省略键、不放裸 'None'
        d = local_artifact_locations(str(root), run_id)
        if report_index is not None:
            d["report_index"] = str(report_index)
        else:
            d.pop("report_index", None)
        return d

    return run_store, result_store, report_store, make_artifacts


def resolve_region(explicit_region: str | None, profile: str | None) -> str | None:
    """把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION > profile config。

    **profile config 回落是关键**：Nova worker 的 AgentCore `validate_region` 要求显式合法 region 字符串、不查 boto
    默认链/profile config——若不在此把 profile 里的 region 落实成字符串，profile-only 用户下 worker region=None 会
    `InvalidRegionError` 崩。用 `boto3.Session(profile).region_name` 读 profile config 的 region（探针证实：有则返回、
    无则 None）。boto3 惰性 import（仅前三级都 miss 时才触发）——**缺 boto3（纯 local 未装 aws extra）也不硬依赖**：
    catch ImportError → 返回 None（等价于「无 region」，与真无 region 同走 fail-loud），保住「纯 local 路径绝不
    依赖 boto3」不变量（否则纯 local + 无 region env 的用户跑会撞未捕获 ImportError，而非优雅 fail-loud）。
    真无 region（全 miss / 或缺 boto3 读不到 profile config）→ 返回 None＝fail-loud（worker 报错、不硬编码 east，对齐 store 宽容边界）。
    """
    r = explicit_region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if r:
        return r
    # 前三级 miss：回落 profile config（--profile 或 AWS_PROFILE 指向的 profile 的 region 字段）。
    # 缺 boto3（纯 local 未装 aws extra）→ 当作读不到 → None fail-loud（不让纯 local 硬依赖 boto3）。
    try:
        import boto3
    except ImportError:
        return None
    return boto3.session.Session(profile_name=profile).region_name


@dataclass(frozen=True)
class CloudTarget:
    """一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。

    产品本体知识（`gherkai` 知道云资源，ADR 0016「演进」节）：入口皮只把已解析的 flag 值交进来，
    「prefix 怎么推导默认名、哪个资源有 env 兜底、region 怎么落实成字符串」全在 `resolve_cloud_target`。
    名字类字段一律是**终名**（已叠 prefix / 已被单资源 override 取代），消费者直接用、不再拼。
    """

    prefix: str
    region: str | None
    profile: str | None
    runs_table: str
    events_table: str
    bucket: str
    cluster: str
    kicker_lambda: str
    reconciler_lambda: str
    exit_observer_lambda: str

    @property
    def detached_chain_lambdas(self) -> list[str]:
        """无状态跑批事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序＝链上顺序。"""
        return [self.kicker_lambda, self.reconciler_lambda, self.exit_observer_lambda]


def resolve_cloud_target(
    *, prefix: str | None = None, region: str | None = None, profile: str | None = None,
    runs_table: str | None = None, events_table: str | None = None,
    bucket: str | None = None, cluster: str | None = None,
) -> CloudTarget:
    """把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。

    解析链逐资源不同、**有意非齐整**（保既有 CLI 行为，别为对称乱加 env 兜底）：
    - prefix：flag > `AWS_RESOURCE_PREFIX` > `DEFAULT_PREFIX`；
    - runs_table / bucket：flag > `AWS_DDB_TABLE` / `AWS_S3_BUCKET` > prefix 默认名（历史 env 面）；
    - events_table / cluster / 三 Lambda：flag（Lambda 无 flag）> prefix 默认名，**无 env 兜底**；
    - profile：flag > `AWS_PROFILE`；region 经 `resolve_region` 落实成具体字符串（见其 docstring）。
    """
    profile = profile or os.environ.get("AWS_PROFILE")
    prefix = prefix or os.environ.get("AWS_RESOURCE_PREFIX") or DEFAULT_PREFIX
    return CloudTarget(
        prefix=prefix,
        region=resolve_region(region, profile),
        profile=profile,
        runs_table=(runs_table or os.environ.get("AWS_DDB_TABLE")
                    or default_name(prefix, _names.BASE_RUNS_TABLE)),
        events_table=events_table or default_name(prefix, _names.BASE_EVENTS_TABLE),
        bucket=(bucket or os.environ.get("AWS_S3_BUCKET")
                or default_name(prefix, _names.BASE_BUCKET)),
        cluster=cluster or default_name(prefix, _names.BASE_CLUSTER),
        kicker_lambda=default_name(prefix, _names.BASE_KICKER_LAMBDA),
        reconciler_lambda=default_name(prefix, _names.BASE_RECONCILER_LAMBDA),
        exit_observer_lambda=default_name(prefix, _names.BASE_EXIT_OBSERVER_LAMBDA),
    )


# —— 造 boto3 句柄的两个钩子（抽出来供 cli 测试 monkeypatch，验接线而不连真 AWS）——
def _make_ddb_table(table: str, *, region, profile):
    """boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走 Session。"""
    import boto3
    session = boto3.session.Session(profile_name=profile, region_name=region)
    return session.resource("dynamodb").Table(table)


def _make_s3_client(*, region, profile):
    """boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。"""
    import boto3
    session = boto3.session.Session(profile_name=profile, region_name=region)
    return session.client("s3")


def build_cloud_stores(*, table: str, bucket: str, prefix: str = "",
                       region: str | None = None, profile: str | None = None,
                       detached: bool = False):
    """云端三层 store（RunStore→DDB、Result/ReportStore→S3）+ cloud artifacts descriptor（s3://+ddb://）。

    DDB 吃 `resource.Table`、三个 S3 件套（ResultStore/ReportStore/offloader）**共享一个 client**（喂错句柄
    类型运行时才 AttributeError，ADR 0016）。offloader 生产默认挂载（解 DDB 400KB 限，ADR 0030 决定七）。
    `import boto3` 惰性在 _make_* 钩子里（**纯 local 路径绝不触发 import**；「cli 主依赖不含 boto3，走
    cli[aws]→core[aws] extra」已被 ADR 0037 决策 2c 反转：CLI 发行包 gherkai 硬依赖 `gherkai-runtime[aws]`、
    自带 boto3，库层 `gherkai-core[aws]`/`gherkai-runtime[aws]` extra 保留给库消费者；缺 boto3 抛 ImportError
    由 cli 归到退 2）。prefix 分隔符规范化避粘连 key。
    """
    from gherkai_core.adapters.report_store.s3 import S3ReportStore
    from gherkai_core.adapters.result_store.s3 import S3ResultStore
    from gherkai_core.adapters.run_store.arg_offload import S3StepArgumentOffloader
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    pfx = _normalize_prefix(prefix)
    ddb_table = _make_ddb_table(table, region=region, profile=profile)
    s3 = _make_s3_client(region=region, profile=profile)  # 一个 client 注入三个 S3 件套

    offloader = S3StepArgumentOffloader(s3, bucket, pfx)
    # detached：无状态跑批 submit 传 True → create_run 的 STATE 带 detached 标记、触发 kicker 冷启动；
    # 同步 run 不传 → 不触发（否则双开推进器，ADR 0034）。
    run_store: RunStore = DynamoDBRunStore(ddb_table, arg_offloader=offloader, detached=detached)
    result_store: ResultStore = S3ResultStore(s3, bucket, pfx)
    report_store: ReportStore = S3ReportStore(s3, bucket, pfx)

    def make_artifacts(run_id: str, report_index) -> dict:
        # 落点走 cloud_artifact_locations 单点（status 终态打印同一份）；report_index 以 finalize 返回值为准，
        # None = report 写失败被隔离 → 省略键
        d = cloud_artifact_locations(bucket=bucket, report_prefix=prefix, table=table, run_id=run_id)
        if report_index is not None:
            d["report_index"] = str(report_index)
        else:
            d.pop("report_index", None)
        return d

    return run_store, result_store, report_store, make_artifacts


def read_resource(uri: str, *, s3=None, region: str | None = None, profile: str | None = None) -> bytes:
    """读一个 `ResourceUri` 的字节（`file://`、裸路径、`s3://`）——**皮层解引用产物 ref 的唯一入口**（ADR 0042 决策四）。

    许可边界（ADR 0027 的消费端规则按层收窄、见 0042 决策五）：本函数只提供「按 URI 取字节」这一能力，
    **该不该解引用由调用方按 ref 的 kind 判**——皮层只对 gherkai 自有 schema 的 ref（`kind == "evidence"`）
    解引用，引擎原生产物（report / trajectory / summary）仍只当链接；`model / wire / schedule / ReportStore`
    永不调本函数。

    `file://` 复用 report_store 的 URI→路径解析（唯一一份，不写第三份）；`s3://` 走 boto `get_object`，
    client 经与 `build_cloud_stores` 同一个 `_make_s3_client` 钩子拿（测试可 monkeypatch）。**`s3` 参数优先**：
    调用方读多个对象时建一次复用，别逐次建 session。boto3 仍只惰性 import（`file://` 档零 boto 依赖，
    对齐「纯 local 路径绝不 import boto3」）。
    读不到/解不开一律抛（ValueError 或底层 OSError/botocore 异常），best-effort 由调用方裹 try 决定（0042 决策二）。
    """
    from urllib.parse import urlparse

    parsed = urlparse(uri)
    if parsed.scheme in ("", "file"):
        from gherkai_core.adapters.report_store.local import local_path_from_uri

        path = local_path_from_uri(uri)
        if path is None:  # file://host/…（远端/UNC）：不是本机文件
            raise ValueError(f"不是本机可读的文件 URI：{uri}")
        return path.read_bytes()
    if parsed.scheme == "s3":
        # s3://<bucket>/<key>：key 原样（上传器写 ref 时未做 percent-encoding，见 0029 的 key 计算）
        bucket, key = parsed.netloc, parsed.path.lstrip("/")
        if not bucket or not key:
            raise ValueError(f"s3 URI 缺 bucket 或 key：{uri}")
        if s3 is None:
            s3 = _make_s3_client(region=region, profile=profile)
        return s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    raise ValueError(f"不支持的 URI scheme：{uri}")


# ============================================================================
# Fargate 执行接线（ADR 0033 / 0016 决策 A/C）：--backend cloud 时用 FargateEngine 替代 SubprocessEngine。
# boto3 句柄钩子抽出供测试 monkeypatch（同 store 侧 _make_* 惯例）；import boto3 惰性收在钩子内。
# ============================================================================
def _make_ecs_client(*, region, profile):
    """boto3 ecs client（FargateEngine RunTask/StopTask/DescribeTasks）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("ecs")


def _make_ssm_client(*, region, profile):
    """boto3 ssm client（读 subnet/sg 的确定性路径参数）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("ssm")


def probe_aws_identity(*, region, profile) -> dict:
    """凭证/region 可用性探针（`gherkai doctor`，ADR 0041 决策四）：STS GetCallerIdentity，返 {account, arn, region}。
    只读、零资源；异常原样抛给调用方翻成一句诊断。"""
    import boto3
    sts = boto3.session.Session(profile_name=profile, region_name=region).client("sts")
    ident = sts.get_caller_identity()
    return {"account": ident.get("Account"), "arn": ident.get("Arn"), "region": region}


def _make_lambda_client(*, region, profile):
    """boto3 lambda client（cloud status --wait 接力 invoke kicker Lambda 做 kickoff，ADR 0034）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("lambda")


def _read_ssm_list(ssm, path: str) -> list[str]:
    """读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。

    **空值 fail-fast（低频加固，ADR 0033）**：正常路径 CDK 一定写非空（subnet 取自 `vpc.public_subnets or
    private_subnets`、sg 写默认 SG id，均非空），故空值**几乎不可达**——只可能来自配置异常（参数被改空 / 值为空串）。
    但若不拦，空列表会一路传到 `awsvpcConfiguration` 的 subnets/securityGroups、拖到 **RunTask 才炸**且错误
    不直观（不像"SSM 参数空"那么明确）。故在此就地 fail-fast、点名是哪个 SSM 路径空了，把不可达但代价高的
    静默失败挡在源头（对齐本项目 preflight fail-fast 点名 prefix 的加固风格）。
    """
    resp = ssm.get_parameter(Name=path)
    values = [v for v in resp["Parameter"]["Value"].split(",") if v]
    if not values:
        raise ValueError(
            f"SSM 参数 {path!r} 为空（split 逗号过滤后无值）——预期 CDK 写入非空的 subnet/sg ID 列表。"
            f"检查后端是否已部署（`gherkai deploy`）且该参数未被改空。"
        )
    return values


def resolve_network(
    *, prefix: str, subnets: list[str] | None, security_groups: list[str] | None,
    assign_public_ip: str = "ENABLED", region=None, profile=None, ssm=None,
) -> dict:
    """Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK 写的生成 ID）；
    给了则用字面覆盖。ssm client 可注入（测试）；未注入且需读时惰性建。返回 FargateEngine 的 network_config 形状。"""
    if subnets is None or security_groups is None:
        if ssm is None:
            ssm = _make_ssm_client(region=region, profile=profile)
        if subnets is None:
            subnets = _read_ssm_list(ssm, ssm_path(prefix, _names.SUBNETS_KEY))
        if security_groups is None:
            security_groups = _read_ssm_list(ssm, ssm_path(prefix, _names.SECURITY_GROUPS_KEY))
    return {"subnets": subnets, "securityGroups": security_groups, "assignPublicIp": assign_public_ip}


def build_fargate_engines(
    *, run_id: str, prefix: str, cluster: str, events_table: str, bucket: str, report_dir: str,
    network_config: dict, worker_task_defs: Mapping[str, str],
    region: str | None = None, profile: str | None = None,
    extra_http_headers: dict[str, str] | None = None,
    ecs=None, s3=None, ddb_events_table=None,
    no_artifacts: bool = False,
) -> dict[str, Engine]:
    """每引擎一个 FargateEngine（对称 build_engines 的 SubprocessEngine dict；core 引擎无关，ADR 0026）。

    `--backend cloud` 用它替代 build_engines——决策 A（cloud ⇒ Fargate 执行）从设计落到 CLI 的动作点。
    boto3 句柄组合根注入（adapter 不自建，ADR 0016）。

    **`worker_task_defs`（引擎 → task-def **revision** ARN）必给、无缺省**（ADR 0038 不变量「运行时只用
    definition 里的显式 revision，永不用 family 取最新」）：传 family 名会让 ECS 取该 family 最新 ACTIVE
    revision——多 variant 下任何一次 `push-worker` 都会劫持在跑的 run（中途换 step 集）。**故意不给缺省值**：
    缺省成 family 名就是把这条不变量做成「忘了传就静默破」，改成必给关键字 → 漏传即 `TypeError`，在装配点
    就炸。真值来源两条（都在调用方，本函数只认 ARN）：definition 的 `RunMeta.worker_task_defs`（正常路径，
    提交侧 preflight 解析）、`resolve_default_worker_task_defs`（旧 definition 的兼容路径）。
    映射里**没有的引擎装一条 `_UnavailableEngine` 空腿**（一用即抛、点名该引擎）——本 run 没用到的引擎不该
    连坐，而真去起它时爆的是带指引的异常、不是 `KeyError`。
    - run_id：拼 events PK（`new_run_id()` 后注入，对称 store）。
    - **profile 不传给 FargateEngine**（正确的非对称，ADR 0016 决策 C）：容器用 task role；region 传（已落实成
      具体字符串、经 RunTask overrides 注入 worker）。
    - job-in 落点 = (bucket, `{prefix_key}<run_id>/jobs-in/`)——**jobs-in/ 非 jobs/**（ResultStore 判定真值占 jobs/、
      load_all 枚举它；job-in 独立前缀避撞 key + 误读）。artifact 上传落点 = (bucket, `{prefix_key}<run_id>/`)——与
      report 同前缀镜像 run 树。**artifact_s3 必注入**（cloud 档唯一的上传落点注入点——local 的 `build_engines`
      恒不注入）：否则 Fargate 容器盘停即销毁、引擎产物（trajectory/report）必丢（ADR 0029「cloud 注入不是可选」/0032）。
    句柄可注入（测试 monkeypatch），未注入则惰性建（区分 ecs/s3/ddb resource）。
    """
    from gherkai_core.adapters.fargate_engine import FargateEngine

    if ecs is None:
        ecs = _make_ecs_client(region=region, profile=profile)
    if s3 is None:
        s3 = _make_s3_client(region=region, profile=profile)
    if ddb_events_table is None:
        ddb_events_table = _make_ddb_table(events_table, region=region, profile=profile)

    pfx = _normalize_prefix(report_dir)
    # job-in 落点用 **jobs-in/**（**不是 jobs/**）：ResultStore 判定真值写在 <run_id>/jobs/<quote(scope_id)>.json、
    # 且 load_all 用 `list jobs/ + unquote basename` 枚举判定——job-in（输入）与 ResultStore（输出判定）scope_id 编码
    # 相同、若共用 jobs/ 前缀会撞 key（互相覆盖）+ 被 load_all 误当判定读。故 job-in 独立前缀 jobs-in/。（真跑暴露。）
    job_s3 = (bucket, f"{pfx}{run_id}/jobs-in/")
    # 产物上传落点（ADR 0029）：prefix = <report_dir>/<run_id>/（run 树根，worker 拼产物相对路径；与 report 同前缀镜像
    # run 树）。**cloud 必注入**——否则容器盘停即销毁、产物必丢（ADR 0029「cloud 注入不是可选」）。
    artifact_s3 = (bucket, f"{pfx}{run_id}/")
    # SDK 产物落点 env（容器内路径）——**uploader 靠它算 run_dir/相对 key，缺它 no-op 报 file://、产物丢**（真跑暴露）。
    # 容器内固定 run 根 /tmp/gherkai-run/<run_id>/，按引擎子目录（names.ARTIFACT_SUBDIR，对称 subprocess 侧）：
    # uploader run_dir=父级=<run 根>，S3 key = ARTIFACT_S3_PREFIX(<report_dir>/<run_id>/) + 相对路径 → 与 subprocess 镜像一致。
    container_run_root = f"/tmp/gherkai-run/{run_id}"
    sdk_env_by_engine = {  # 子目录名走 names.ARTIFACT_SUBDIR 单点（与 subprocess 侧同名，S3 key 才能镜像 run 树）
        "novaact": {"NOVA_LOGS_DIR": f"{container_run_root}/{_names.ARTIFACT_SUBDIR['novaact']}"},
        "midscene": {"MIDSCENE_RUN_DIR": f"{container_run_root}/{_names.ARTIFACT_SUBDIR['midscene']}"},
    }
    # 额外请求头（ADR 0035）：对称 build_engines 的 headers_env，经 FargateEngine extra_env 注 RunTask overrides。
    headers_env = (
        {"GHERKAI_EXTRA_HTTP_HEADERS": json.dumps(extra_http_headers, ensure_ascii=False)}
        if extra_http_headers else {}
    )
    if no_artifacts:  # `--backend cloud --no-report`：worker 不生成/不上报原生产物 → 也就不会有 S3 上传（ADR 0037 决策 3）
        headers_env = {**headers_env, "GHERKAI_NO_ARTIFACTS": "1"}
    # 引擎特定 env（同 headers 走 extra_env 注 RunTask overrides）：Nova 的 act timeout **双端同源**
    # （ADR 0024 grace 硬约束）——容器不继承本地 env、RunTask overrides 逐条枚举，故 cloud 档必须显式注，
    # 否则 worker 落回自带字面量：operator 调 NOVA_ACT_TIMEOUT_S 只抬高了 grace 下限、改不动容器内单 act
    # 上界，ADR 0032 明写的逃生舱（「要更长 act 就调这个 env」）在云端静默失效、local/cloud 行为分叉。
    engine_env = {"novaact": {"NOVA_ACT_TIMEOUT_S": str(NOVA_ACT_TIMEOUT_S)}}

    def _engine(engine: str) -> Engine:
        revision_arn = worker_task_defs.get(engine)
        if revision_arn is None:
            # 本 run 没解析该引擎的 worker revision（正常态：没用到它）——空腿，真去起才抛（见 _UnavailableEngine）。
            return _UnavailableEngine(WorkerVariantError(
                f"引擎 {engine!r} 的 worker task-def revision 未随本 run 解析——definition 的 worker_task_defs "
                f"只覆盖 {sorted(worker_task_defs) or '（空）'}。若本 run 真要跑该引擎，重新提交（提交侧 preflight "
                f"会按本 run 用到的引擎逐个解析 variant）。",
                engine=engine))
        return FargateEngine(
            ecs_client=ecs, s3_client=s3, ddb_events_table=ddb_events_table,
            # 显式 revision ARN（ADR 0038 不变量）——**绝不传 family 名**。
            run_id=run_id, cluster=cluster, task_definition=revision_arn,
            network_config=network_config, job_s3=job_s3, events_table_name=events_table,
            container_name=container_name(engine), artifact_s3=artifact_s3,
            sdk_artifact_dir_env=sdk_env_by_engine.get(engine, {}),
            extra_env={**headers_env, **engine_env.get(engine, {})},
            region=region,  # profile 不传（决策 C 非对称）
        )

    return {engine: _engine(engine) for engine in _names.ENGINES}


# ============================================================================
# 版本 skew（ADR 0037 决策 7）：CLI 版本 vs 后端 SSM 版本戳，三态齐全 + 非纯净版本跳过。
# **住产品本体、不住入口皮**：Lambda 推进器 / WebUI 将来同样要比「自己 vs 后端」，判据与措辞单点维护、
# 不在第二处复刻（同 names 抽包的理由）。比对是纯函数（不连 AWS）；读戳是下面 read_backend_version 的事。
# ============================================================================

SKEW_OK = "ok"        # release 段相同
SKEW_WARN = "warn"    # CLI 旧于后端 / 后端无戳——警告不拦
SKEW_BLOCK = "block"  # CLI 新于后端——调用点退 2，无放行口
SKEW_SKIP = "skip"    # 任一侧非纯发行版（或自身版本取不到）——无从比较


def read_backend_version(*, prefix: str, region=None, profile=None, ssm=None) -> str | None:
    """读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR 0037 决策 6）。

    **`ParameterNotFound` → 返回 None、不抛**：戳缺失是本机制之前部署环境的正常态，决策 7 判它「警告不拦」；
    若在此翻成异常一路退 2，所有现存部署会被 preflight 锁死（决策 7 明写要避免的那个后果）。其余 botocore
    异常（凭证/region/权限/网络）照抛——由入口皮归到自己的退出码层（对齐 `resolve_network` 的处理）。
    ssm client 可注入（测试）；未注入则惰性建，与 subnet/sg 同一条 session/region 解析（`_make_ssm_client`）。
    """
    if ssm is None:
        ssm = _make_ssm_client(region=region, profile=profile)
    return _ssm_get(ssm, ssm_path(prefix, _names.BACKEND_VERSION_KEY))  # 「不在 → None、其余照抛、空串视缺失」与 _ssm_get 同一份


def _release_key(v: str) -> tuple[int, ...]:
    """PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。

    只在 `_is_pure_release` 已放行后调用——它对解析不了的版本返回 False，故此处不会撞 `InvalidVersion`。
    """
    from packaging.version import Version

    return Version(v).release


def _release_cmp(a: str, b: str) -> int | None:
    """比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。

    两侧位数不同（`1.4` vs `1.4.0`）时补零再比，避免元组字典序把 `1.4` 判成小于 `1.4.0`。
    抽成一处是因为有两个消费者——`check_version_skew` 的三态判定与 worker variant 解析失败时的提示语分叉
    （ADR 0038：CLI 与后端同版本 → 引导去 push-worker；CLI 旧于后端 → 引导升级 CLI）。补零/纯净判据在两处
    各写一遍必漂。
    """
    if not (a and b and _is_pure_release(a) and _is_pure_release(b)):
        return None
    ra, rb = _release_key(a), _release_key(b)
    n = max(len(ra), len(rb))
    ra += (0,) * (n - len(ra))
    rb += (0,) * (n - len(rb))
    return (ra > rb) - (ra < rb)


def check_version_skew(ssm_version: str | None, cli_version: str | None) -> tuple[str, str]:
    """比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策 7）。

    message 是给人看的整句（ok 档为空串，调用点 `if message:` 即可）；**退码留给调用点**——`block` 一律退 2
    且**无放行口**（决策 7 明拒 `--allow-version-skew`：放行 = 让新 CLI 写的 definition 进旧 Lambda runtime 读，
    后果不可知且静默；uvx 按版本临时跑同版本 CLI 零成本，放行口没有真实需求）。其余三档只打一行、不拦。

    判序——「无从比较」一律先于「比较结果」：
    1. **戳缺失**（`ssm_version` 为 None/空）→ warn + 提示部署方跑一次 `gherkai deploy` 写入。**不可退 2**：
       否则本机制之前部署的所有环境被 preflight 锁死（决策 7 明写要避免的后果）。
    2. **自身版本取不到**（`cli_version` 为 None：未装成包、源码直跑）→ skip。**`cli_version` 必给、不缺省成本包
       版本**：比的对象是「写任务定义那一方」（CLI）的版本，由调用点提供；editable 开发树里各包版本各自漂
       （按各自 git 状态算），缺省读 `gherkai-runtime` 版本会埋一个只在 lockstep 发行态下才等价的第二真源。
    3. **任一侧非纯发行版**（含 `.dev`/`.post`/本地段，或压根解析不了）→ skip：dev 版逐提交前进，逐字比较
       会把每次都判成 skew（判据 `_is_pure_release` 与定位链第四级共用——它靠 2b 的 `dirty=true`/`metadata=true`
       保证「非纯净构建一定带 `+`」才可靠）。
    4. **只比 release 段**（决策 7）：pre/post/dev/本地段不参与，故同 release 段的 rc 与正式版视作同版本。
       两侧位数不同（`1.4` vs `1.4.0`）时补零再比，避免元组字典序把 `1.4` 判成小于 `1.4.0`。
    """
    mine = cli_version
    if not ssm_version:
        return SKEW_WARN, (
            f"提示：后端没有版本戳（SSM /<prefix>backend/{_names.BACKEND_VERSION_KEY}）——这个部署早于版本戳机制，本次不比对版本、不拦。"
            "请部署方跑一次 `gherkai deploy` 把戳写上。"
        )
    if not mine:
        return SKEW_SKIP, "提示：跳过版本比对——本机未以包形式安装（源码直跑），取不到自身版本。"
    cmp = _release_cmp(mine, ssm_version)  # None = 任一侧非纯发行版（判序 3）；补零比较在 _release_cmp
    if cmp is None:
        return SKEW_SKIP, (
            f"提示：跳过版本比对——CLI {mine} / 后端 {ssm_version} 中有非纯发行版本"
            f"（.dev/.post/本地段，逐提交前进，逐字比会把每次都判成 skew）。"
        )
    if cmp == 0:
        return SKEW_OK, ""
    if cmp > 0:
        return SKEW_BLOCK, (
            f"版本 skew：本机 CLI {mine} 新于后端 {ssm_version}——拒绝执行（无放行口：新 CLI 写的"
            f"任务定义由旧后端读是真风险）。两条出路：\n"
            f"  ① 部署方把后端升上来：gherkai deploy（升到 {mine}）\n"
            f"  ② 临时用与后端同版本的 CLI、不动本机安装：uvx --from 'gherkai=={ssm_version}' gherkai …"
        )
    return SKEW_WARN, (
        f"提示：本机 CLI {mine} 旧于后端 {ssm_version}（不拦——旧 CLI 写的任务定义新后端读得懂）。"
        f"要跟上：uv tool upgrade gherkai。"
    )


def check_backend_skew(*, prefix: str, cli_version: str | None, region=None, profile=None,
                       ssm=None) -> tuple[str, str, str | None]:
    """读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /
    推进器任何组合根要做「自己 vs 后端」比对都调这一处，判据、措辞与「戳缺失→警告不拦」的分叉单点维护。
    **调用次序约定：先于 `preflight_cloud_resources`**——skew 的修复动作是部署方跑一次 `gherkai deploy`，那一步
    同时把资源建齐/补齐；先报「表不存在」只会把人引去查 `--prefix`、绕一圈回到同一个动作。
    读戳的异常（凭证/region/权限）原样抛，由调用方归到自己的退出码层（与 `read_backend_version` 一致）。
    **戳一并返回**（第三元）：调用方后续的 worker variant 解析（ADR 0038）要拿同一个戳给出 skew 感知的提示语，
    全程只读一次 SSM、不让调用方为了拿戳绕开本函数自己读一遍。
    """
    stamp = read_backend_version(prefix=prefix, region=region, profile=profile, ssm=ssm)
    verdict, message = check_version_skew(stamp, cli_version)
    return verdict, message, stamp


# ============================================================================
# worker variant 解析（ADR 0038）：variant 名 → 各引擎的 task-def **revision** ARN。
# **住产品本体、不住入口皮**：提交侧 preflight（严格退 2 + 打印）与云端推进器的兼容回落读的是同一批 SSM
# 参数、同一套 miss 判据、同一套提示语分叉——两处各写一遍必漂（同 names 抽包、同 check_backend_skew 的理由）。
# ============================================================================


@dataclass(frozen=True)
class WorkerResolution:
    """一个引擎的 worker variant 解析结果（ADR 0038「运行时与 preflight」）。

    `revision_arn` 是**唯一进 RunTask 的字段**（不变量：显式 revision、永不 family）；`digest` 供 preflight
    打印「这次跑的到底是哪份镜像」——「用的是哪份可见、可查」是本 ADR 要解的问题之一，故一起带回来、
    不让调用方二次读 SSM。（SSM 记录里的 `template_arn` 不带回：解析侧无消费者，「从哪个模板派生」由
    `gherkai deploy list-workers` 从 SSM/血缘 tags 直读展示。）
    """

    engine: str
    variant: str
    revision_arn: str
    digest: str


class WorkerVariantError(Exception):
    """worker variant 解析失败（ADR 0038）——**消息本身即给用户看的整句**（含修复动作），调用点直接打印后退 2。

    `engine` / `variant` 供调用点做分组/结构化展示（如「哪个引擎缺」）；两者都可能是 None——默认指针本身缺失
    时还没轮到任何引擎、也没有 variant 名可言。
    **绝不在任何 miss 分支回落**（默认指针 / family 最新 ACTIVE / 模板 revision 都不回落，见 ADR 0038 被拒方案）：
    回落是静默换 step 集，与「不判 steps 内容、用哪份由使用方声明」这条直接矛盾。
    """

    def __init__(self, message: str, *, engine: str | None = None, variant: str | None = None) -> None:
        super().__init__(message)
        self.engine = engine
        self.variant = variant


def _make_ecr_client(*, region, profile):
    """boto3 ecr client（按 digest `describe_images` 核镜像还在，ADR 0038 preflight「存在性」一项）。"""
    import boto3
    return boto3.session.Session(profile_name=profile, region_name=region).client("ecr")


def _ssm_get(ssm, path: str) -> str | None:
    """读一个 SSM String 参数 → 值（strip 后空串视作缺失）；**`ParameterNotFound` → None，其余异常照抛**。

    把「参数不在」与「凭证/权限/网络坏了」分开：前者是本 ADR 各 miss 分支要翻成带指引提示的正常态，后者该
    原样冒泡给入口皮归到自己的退出码层。**两个 ADR 的读侧共用本函数**：0038 各 variant miss 分支把 None 翻成带指引提示；
    0037 决策 7 的版本戳（`read_backend_version`）缺失必须是 None——翻成异常会把所有本机制之前的部署 preflight 锁死。
    """
    try:
        resp = ssm.get_parameter(Name=path)
    except Exception as e:
        err = getattr(e, "response", None)
        code = (err or {}).get("Error", {}).get("Code") if isinstance(err, dict) else None
        if code == "ParameterNotFound":
            return None
        raise
    return (resp["Parameter"]["Value"] or "").strip() or None


def read_worker_default(*, prefix: str, region=None, profile=None, ssm=None) -> str | None:
    """读部署级默认 variant 指针（SSM `worker-default`，ADR 0038）。缺失 → None（调用方决定怎么报）。

    单独公开是因为有三个消费者：两个解析函数（variant 缺省档）与推进器的兼容路径日志（要点名解析到了哪个
    variant——「用的是哪份」必须在日志里可见）。
    """
    if ssm is None:
        ssm = _make_ssm_client(region=region, profile=profile)
    return _ssm_get(ssm, ssm_path(prefix, _names.WORKER_DEFAULT_KEY))


def _no_default_pointer_error(prefix: str) -> WorkerVariantError:
    return WorkerVariantError(
        f"后端没有 worker 默认 variant 指针（SSM {ssm_path(prefix, _names.WORKER_DEFAULT_KEY)}）——"
        f"这个部署还没走过 worker 镜像交付的初始化。请部署方跑一次 `gherkai deploy`（会把基底同步成 "
        f"`base` 并把默认指针初始化为它），或提交时用 `--worker-variant <名>` 显式指定。"
    )


def _read_worker_image_record(ssm, *, prefix: str, engine: str, tag: str) -> dict | None:
    """读 `worker-image/<engine>/<tag>` 的 JSON 记录 → dict；参数不在 → None。

    JSON 畸形（人手改坏参数）翻成 `WorkerVariantError`——不让 `json.JSONDecodeError` 裸奔到入口皮（那条
    错误看不出是哪个 SSM 参数坏了）。
    """
    import json as _json

    path = ssm_path(prefix, _names.worker_image_key(engine, tag))
    raw = _ssm_get(ssm, path)
    if raw is None:
        return None
    try:
        rec = _json.loads(raw)
    except ValueError as e:
        raise WorkerVariantError(
            f"SSM 参数 {path!r} 的值不是合法 JSON（{e}）——预期 `push-worker` 写入的 "
            f"{{template_arn, revision_arn, digest, pushed_at}} 记录。重推该 variant 可覆盖修复。",
            engine=engine) from e
    if not isinstance(rec, dict) or not rec.get("revision_arn") or not rec.get("digest"):
        raise WorkerVariantError(
            f"SSM 参数 {path!r} 的记录缺 revision_arn/digest——重推该 variant 可覆盖修复。", engine=engine)
    return rec


def _variant_miss_hint(*, engine: str, variant: str, tag: str, what: str,
                       cli_version: str, backend_version: str | None) -> str:
    """variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。

    CLI **旧于**后端（决策 7 里「警告不拦」的那一档）时不能引导去 `push-worker`：那会让人推一个**旧版本
    命名空间**的 tag，推完提交侧还是解析不到当前后端版本的映射、原地绕圈。此档一律引导升级 CLI。
    其余档（同版本 / 无从比较 / 无戳）引导 push-worker——这是真正缺镜像时的修复动作；并给第二条出路
    「临时 `--worker-variant base`」（ADR 0038「升级不重置默认指针」的配套：deploy 已把本版本基底同步成 base，
    等不及部署方推自定义 variant 的人可先跑）。
    """
    if _release_cmp(cli_version, backend_version or "") == -1:
        return (f"引擎 {engine} 的 worker variant {variant!r} 解析失败（{what}）：本机 CLI {cli_version} "
                f"旧于后端 {backend_version}，你看到的是后端版本命名空间下没有这份镜像。"
                f"先把 CLI 升到后端版本（uv tool upgrade gherkai，或 uvx --from 'gherkai=={backend_version}' gherkai …）"
                f"再提交——**别**照旧版本推镜像（推的 tag 后端不解析）。")
    return (f"引擎 {engine} 的 worker variant {variant!r} 解析失败（{what}，镜像 tag {tag}）。"
            f"让部署方推上去：gherkai deploy push-worker <本地镜像> --engine {engine} --variant {variant}"
            f"（build 镜像时必须带 --platform linux/amd64）；或临时用 --worker-variant base 先跑"
            f"（部署方跑过本版本 gherkai deploy 即有）。")


def resolve_worker_variant(
    *, prefix: str, variant: str | None, engines: Iterable[str], cli_version: str,
    backend_version: str | None, region=None, profile=None, ssm=None, ecs=None, ecr=None,
) -> dict[str, WorkerResolution]:
    """把 variant 名解析成**本 run 用到的每个引擎**的 revision ARN（ADR 0038「运行时与 preflight」）。

    提交侧 preflight 的正门：解析成功 → 调用方把结果写进 definition（`RunMeta.worker_variant` /
    `worker_task_defs`）；任一环 miss → 抛 `WorkerVariantError`（调用点退 2）、**绝不回落默认/family/模板**。

    三环校验，全是存在性与一致性、**不判 steps 内容**（越权替使用方判断，见 ADR 0038 被拒方案）：
    ① SSM `worker-image/<engine>/<image_tag(cli_version, variant)>` 有映射；② 其 `revision_arn` 经
    `DescribeTaskDefinition` 仍 `ACTIVE`（退休清理可能已把它注销）；③ 其 `digest` 经 ECR
    `describe_images` 仍在（有人手工删过镜像 → RunTask 会拖到 Fargate 启动期才炸 `manifest unknown`）。

    **只按 `engines` 判**（= 本 run 实际用到的引擎），对齐既有 task-def preflight 的判据「不探全注册表——
    没用到的引擎不该拦」：单引擎团队不必为另一个引擎凭空推镜像。
    `variant=None` → 取部署级默认指针（缺失即抛，提示跑 `gherkai deploy`）。tag 由 `names.image_tag`
    单点拼（推送方与本函数同一个函数，键不会两边算法不同而对不上）；`cli_version` 取不到（源码直跑）时
    无从拼 tag，也抛——fail-loud 好过静默解析成别的版本。
    句柄可注入（测试/复用同一 session）；未注入则惰性建。
    """
    if not cli_version:
        raise WorkerVariantError(
            "取不到本机 CLI 版本（未以包形式安装、源码直跑）——worker 镜像 tag 含 CLI 版本，无从解析。"
            "装成包（uv tool install gherkai / uvx）后再提交 cloud 档。")
    if ssm is None:
        ssm = _make_ssm_client(region=region, profile=profile)
    if variant is None:
        variant = read_worker_default(prefix=prefix, ssm=ssm)
        if variant is None:
            raise _no_default_pointer_error(prefix)
    tag = _names.image_tag(cli_version, variant)  # 非法 variant 名在此抛 ValueError（校验单点）
    if ecs is None:
        ecs = _make_ecs_client(region=region, profile=profile)
    if ecr is None:
        ecr = _make_ecr_client(region=region, profile=profile)

    def _miss(engine: str, what: str) -> WorkerVariantError:
        return WorkerVariantError(
            _variant_miss_hint(engine=engine, variant=variant, tag=tag, what=what,
                               cli_version=cli_version, backend_version=backend_version),
            engine=engine, variant=variant)

    out: dict[str, WorkerResolution] = {}
    for engine in sorted(set(engines)):
        rec = _read_worker_image_record(ssm, prefix=prefix, engine=engine, tag=tag)
        if rec is None:
            raise _miss(engine, "SSM 里没有这个（引擎，variant）的镜像映射")
        revision_arn, digest = rec["revision_arn"], rec["digest"]
        try:
            td = ecs.describe_task_definition(taskDefinition=revision_arn)
        except Exception as e:
            if is_botocore_error(e):
                raise _miss(engine, f"task-def revision {revision_arn} 已不可 Describe（可能已被清理删除）") from e
            raise
        if (td.get("taskDefinition", {}).get("status") or "").upper() != "ACTIVE":
            raise _miss(engine, f"task-def revision {revision_arn} 不是 ACTIVE（已退休/注销，不能再起新 task）")
        repo = _names.ecr_repo_name(prefix, engine)
        try:
            resp = ecr.describe_images(repositoryName=repo, imageIds=[{"imageDigest": digest}])
        except Exception as e:
            if is_botocore_error(e):
                raise _miss(engine, f"ECR 仓库 {repo} 里按 digest {digest} 找不到镜像") from e
            raise
        if not resp.get("imageDetails"):
            raise _miss(engine, f"ECR 仓库 {repo} 里按 digest {digest} 找不到镜像")
        out[engine] = WorkerResolution(
            engine=engine, variant=variant, revision_arn=revision_arn, digest=digest)
    return out


def resolve_default_worker_task_defs(
    *, prefix: str, engines: Iterable[str], backend_version: str | None,
    region=None, profile=None, ssm=None,
) -> dict[str, str]:
    """**宿主的兼容路径**（ADR 0038「读侧兼容口径」）：definition 里没有 `worker_task_defs` 的 run，按**后端
    当前默认指针**解析出引擎 → revision ARN。解析不出即抛，**绝不回落 family 最新 ACTIVE、绝不回落模板 revision**。

    这样的 run 有两个来源：引入本机制的那次升级前提交、升级窗口内仍在跑的 run；以及旧 CLI 提交到新后端的 run
    （ADR 0037 决策 7「CLI 旧于后端 → 警告不拦」允许）。用**后端**版本拼 tag（不是提交方 CLI 版本——definition
    里根本没记，且后端只解析自己版本命名空间下的映射）。

    比 `resolve_worker_variant` 少两环（不 Describe revision、不查 ECR digest）是有意的：这里跑在推进器
    Lambda 的热路径上，而**它拿到的 ARN 立刻要交给 RunTask** ——revision 被注销/镜像被删的话 RunTask 自己就会
    报，多两次 API 调用只是把同一个错误提前一点、换不来新信息。提交侧 preflight 的三环校验是为了「别让用户
    提交完才发现」，宿主没有这个动机。
    """
    if ssm is None:
        ssm = _make_ssm_client(region=region, profile=profile)
    if not backend_version:
        raise WorkerVariantError(
            f"兼容路径无从解析 worker 镜像：读不到后端版本戳（SSM {ssm_path(prefix, _names.BACKEND_VERSION_KEY)}）——"
            f"镜像 tag 含版本。请部署方跑一次 `gherkai deploy` 把戳写上。")
    variant = read_worker_default(prefix=prefix, ssm=ssm)
    if variant is None:
        raise _no_default_pointer_error(prefix)
    tag = _names.image_tag(backend_version, variant)
    out: dict[str, str] = {}
    for engine in sorted(set(engines)):
        rec = _read_worker_image_record(ssm, prefix=prefix, engine=engine, tag=tag)
        if rec is None:
            raise WorkerVariantError(
                f"兼容路径解析失败：引擎 {engine} 在后端版本 {backend_version} 下没有默认 variant {variant!r} "
                f"的镜像映射（SSM {ssm_path(prefix, _names.worker_image_key(engine, tag))}）。"
                f"部署方跑 `gherkai deploy`（同步基底并初始化默认指针），或推上这个 variant："
                f"`gherkai deploy push-worker <本地镜像> --engine {engine} --variant {variant}`。",
                engine=engine, variant=variant)
        out[engine] = rec["revision_arn"]
    return out


def preflight_cloud_resources(
    *, prefix: str, events_table: str, bucket: str, cluster: str, runs_table: str | None = None,
    task_defs: list[str] | None = None, lambda_fns: list[str] | None = None,
    report_dir: str | None = None, declared_max_concurrency: int | None = None, on_warn=None,
    region=None, profile=None, ecs=None, s3=None, ddb=None, lam=None,
) -> str | None:
    """fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句
    **点名 prefix** 的错误串（调用方退 2），全在返回 None。别跑到一半才因资源缺炸；错误要能指向「prefix 配错 /
    CDK 没部署」。

    探**执行必需**（events 表 + cluster + 桶 + `task_defs`——本 run 用到引擎的 task-def）恒探；**runs 表仅落库
    需要**——`runs_table=None`（`--no-report`）时不探（report 与执行正交，ADR 0016 决策 A：`--no-report
    --backend cloud` 仍 Fargate 跑、不落库、故不碰 runs 表）；**`lambda_fns` 仅 detached submit 需要**——事件
    驱动链三 Lambda（kicker/reconciler/exit-observer），任一缺则提交成功但 run 永不推进/收敛，挡在提交前
    （同步 run 进程内推进、不依赖链、不传）。句柄可注入（测试）；未注入惰性建。探法全只读：DDB DescribeTable、
    S3 HeadBucket、ECS DescribeClusters/DescribeTaskDefinition、Lambda GetFunction。
    任一 botocore 异常都翻成「资源 X 不存在——是 --prefix 配错、还是后端未部署（`gherkai deploy`）？」。

    **`report_dir` 非 None 时另比对「推进器的产物前缀」一致性**（存在性之外的唯一语义探针，ADR 0033 preflight 条）：
    detached cloud 档的产物前缀有**两个独立来源**——提交侧 `--report-dir`（offload 的 args/ 落它）与推进侧
    Lambda 的 `REPORT_DIR` env（判定真值 jobs/ 与 RunReport 落它，IaC 有意不注入、由 Lambda 内缺省 `reports` 供给）。
    不一致时提交照样成功、run 照样跑完，但结果落在用户没指定的前缀下（用户在自己给的前缀里找不到报告、
    提交侧留下一批孤儿 args 对象），是典型「静默分裂」，故挡在提交前。只比 `lambda_fns` 里的**两个推进器**
    （kicker/reconciler——名按 prefix 从 `names` 真源推出；exit-observer 不读 REPORT_DIR、不比），
    env 缺该键视作 Lambda 侧缺省 `reports`，两侧都过 `_normalize_prefix` 再比（`reports` 与 `reports/` 不算冲突）。

    **`declared_max_concurrency` + `on_warn` 非 None 时另提示「声明超部署侧 cap」**（ADR 0034 机制四）：读同一批
    推进器的 `MAX_CONCURRENCY` env（缺键视作推进器侧缺省 1），声明 > cap 则经 `on_warn` 警一条（最多一条）、
    **不构成 preflight 失败**。与上面 REPORT_DIR 退 2 的判据分野 = **分岔的后果**：超 cap 只是被钳制，run 照跑、
    结果照落用户给的前缀，分岔对产物是 no-op（只是慢），提示即够；REPORT_DIR 分岔会把产物写去别处（用户在自己
    给的前缀下找不到结果），必须挡在提交前。
    """
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError

    sess = boto3.session.Session(profile_name=profile, region_name=region)
    ddb = ddb or sess.client("dynamodb")
    s3 = s3 or sess.client("s3")
    ecs = ecs or sess.client("ecs")

    def _hint(resource_desc: str) -> str:
        return (f"--backend cloud 资源缺失：{resource_desc}（用 --prefix={prefix!r} 拼出）不存在——"
                f"是 --prefix 配错、还是后端未部署（gherkai deploy）到本 region/账户？")

    if runs_table is not None:  # 仅落库需要；--no-report 下 None、不探
        try:
            ddb.describe_table(TableName=runs_table)
        except (ClientError, BotoCoreError):
            return _hint(f"DynamoDB 表 {runs_table}")
    try:
        ddb.describe_table(TableName=events_table)
    except (ClientError, BotoCoreError):
        return _hint(f"DynamoDB 表 {events_table}")
    try:
        s3.head_bucket(Bucket=bucket)
    except (ClientError, BotoCoreError):
        return _hint(f"S3 桶 {bucket}")
    try:
        resp = ecs.describe_clusters(clusters=[cluster])
        if not resp.get("clusters") or resp["clusters"][0].get("status") != "ACTIVE":
            return _hint(f"ECS cluster {cluster}")
    except (ClientError, BotoCoreError):
        return _hint(f"ECS cluster {cluster}")
    for td in task_defs or []:  # 按本 run 实际用到的引擎探（不探全注册表——没用到的引擎缺 task-def 不该拦）
        try:
            ecs.describe_task_definition(taskDefinition=td)
        except (ClientError, BotoCoreError):
            return _hint(f"ECS task definition {td}")
    if lambda_fns:
        lam = lam or sess.client("lambda")
        # 读 REPORT_DIR / MAX_CONCURRENCY 的只有两个推进器（前者拼 Result/Report/artifact/job-in 前缀，
        # 后者是部署侧 per-run 并发 cap）——exit-observer 两个都不读，不参与比对/提示。
        advancers = {default_name(prefix, _names.BASE_KICKER_LAMBDA),
                     default_name(prefix, _names.BASE_RECONCILER_LAMBDA)}
        warned_cap = False
        for fn in lambda_fns:
            try:
                resp = lam.get_function(FunctionName=fn)  # 返回体已含 Configuration.Environment，无需二次调用
            except (ClientError, BotoCoreError):
                return _hint(f"Lambda 函数 {fn}（无状态跑批事件驱动链）")
            if fn not in advancers:
                continue
            env = (resp.get("Configuration", {}).get("Environment") or {}).get("Variables") or {}
            if declared_max_concurrency is not None and on_warn is not None and not warned_cap:
                # 声明超 cap → 钳制（推进器取 min）。只提示不失败（判据见 docstring：钳制对产物是 no-op）。
                # 两推进器须同值，故只警一条（都警是重复噪声）；env 值畸形时无从比对，静默跳过——
                # 提示是锦上添花，不该为它让 preflight 崩（cap 数值真源在 IaC）。
                try:
                    cap = int(env.get("MAX_CONCURRENCY", "1"))  # 缺键 = 推进器侧保守缺省
                except ValueError:
                    cap = None
                if cap is not None and declared_max_concurrency > cap:
                    on_warn(f"提示：--max-concurrency={declared_max_concurrency} 超过部署侧 per-run 上限 "
                            f"cap={cap}，本 run 将按 {cap} 并行"
                            f"——要更高并发由部署方调高后端 stack（gherkai-deploy-aws）的 MAX_CONCURRENCY 后重新部署。")
                    warned_cap = True
            if report_dir is None:
                continue
            remote = env.get("REPORT_DIR", "reports")  # 缺键 = Lambda 侧走自己的缺省
            if _normalize_prefix(remote) != _normalize_prefix(report_dir):
                return (f"--backend cloud 产物前缀不一致：submit 侧 --report-dir={report_dir!r}，"
                        f"后端 {fn} 的 REPORT_DIR={remote!r}。云端跑完的结果/报告按后端自己的 REPORT_DIR 落，"
                        f"你会在 --report-dir 下找不到结果。改用 --report-dir={remote!r}，"
                        f"或由部署方把后端 stack（gherkai-deploy-aws）的 REPORT_DIR 改成 {report_dir!r} 后重新部署。")
    return None


def is_botocore_error(exc: BaseException) -> bool:
    """是否 botocore 异常（云端不可达/权限/凭证/region 等）——入口皮据此把云端故障归到自己的退出码层。

    惰性 import botocore（cli 主依赖不含 boto3，顶层 import 会在纯 local 环境炸；且只在 cloud 路径才会调到
    这里）。缺 botocore（不该发生，能走到 cloud 就装了 boto3）时保守返回 False。
    """
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:  # pragma: no cover
        return False
    return isinstance(exc, (BotoCoreError, ClientError))


def prune_empty_dirs(root: Path) -> None:
    """自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。

    非空目录（残留产物/文件）自然保留（rmdir 抛 OSError → 吞掉），与 worker「上传失败保留本地」护栏自洽。
    root 不存在则 no-op。用于 cloud 模式清 worker 用完的本地产物暂存区空壳——**本地落点是组合根算出来的、
    故清理归组合根**；core 对本地文件系统无知（ADR 0016 窄腰），不该由 core/store 删。
    """
    if not root.exists():
        return
    for d, _subdirs, _files in os.walk(root, topdown=False):
        try:
            os.rmdir(d)  # 只删空目录；非空 → OSError → 吞掉、保留
        except OSError:
            pass


def load_feature(path: Path) -> FeatureSource:
    """读 .feature 文件 → core 要的 FeatureSource（uri+text）。

    core 不碰文件系统（ADR 0025）：读文件、推导 uri 是组合根的事。uri 是 `scenario_id`/`scope_id` 的前缀
    （`<uri>:<line>`，会进报告目录名与 DDB 键），**取用户给出的路径经规范化后原样**——相对给相对、绝对给绝对，
    不相对任何「根」（ADR 0037 决策 3：分发后没有 repo 根，任何根都随安装位置/CWD 漂移；曾相对仓库根算、
    仓库外退用绝对路径，wheel 装法下会让 scope_id 形状随安装形态变）。
    """
    uri = os.path.normpath(str(path))
    return FeatureSource(uri=uri, text=Path(path).read_text(encoding="utf-8"))
