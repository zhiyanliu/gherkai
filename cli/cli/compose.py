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
from core.ports import Engine, ReportStore, ResultStore, RunStore
from core.scope import FeatureSource


# Nova 单 act 时间上界（ADR 0024 act 有界返回）——**组合根持单一真值**，同时派生两端（消除漂移）：
# ① 注入 worker 的 NOVA_ACT_TIMEOUT_S env（worker run_scope.py 读它，缺省也是 120、此处显式注入使两端同源）；
# ② 算 Nova 的 grace 下限（见 engine_min_grace）。env 可覆盖（真跑标定/调优）。
NOVA_ACT_TIMEOUT_S = int(os.environ.get("NOVA_ACT_TIMEOUT_S", "120"))  # SDK 允许 [2,1800]
# grace 余量（ADR 0024/0028 grace 硬约束的 margin）：单 step 最坏耗时 + 会话释放 + 余量。**有界的待真跑标定量**，
# 保守起点 60s（→ Nova grace 下限 ≈ 180s）。标定完改这一处。
NOVA_GRACE_MARGIN_S = int(os.environ.get("NOVA_GRACE_MARGIN_S", "60"))


def engine_min_grace(engine_name: str) -> float:
    """按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。

    Nova：`ACT_TIMEOUT_S + margin`（SIGTERM 落长 act 中途须等 act 有界返回才协作退释放会话）。
    其余引擎（Midscene 无 worker 可控 act timeout 概念）：0.0=无下限。
    组合根算好后作 `ScheduleOpts.min_grace_s` 传给 core，core 只 enforce「grace ≥ 此下限」的引擎无关关系。
    （未来更干净：引擎经 Engine port 自声明 min_grace，替代这里的 engine_name 分支，ADR 0024 记为 defer。）
    """
    if engine_name == "novaact":
        return float(NOVA_ACT_TIMEOUT_S + NOVA_GRACE_MARGIN_S)
    return 0.0


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
    artifact_s3: tuple[str, str] | None = None,
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

    产物 S3 上传落点（ADR 0029「第一期实现定论」）——`artifact_s3=(bucket, prefix)` 非 None 时（跟
    `--backend cloud` 走、由组合根注入、非 env-sniff）给两腿 worker 叠加 `ARTIFACT_S3_BUCKET`/
    `ARTIFACT_S3_PREFIX` env：worker 据此上传产物→报 `s3://`→删本地。**None（local）→ 不注入 → worker
    走原 `file://` 路径、零行为变化**。worker 只认"有没有这组 env"，对"我在哪跑"无知（ADR 0016 注入红线）。
    prefix 约定 = `<report_dir>/<run_id>/`（与 S3ReportStore/ResultStore 同前缀，key 镜像本地 run 树）。
    """
    novaact_dir = repo / "engines" / "novaact"
    midscene_dir = repo / "engines" / "midscene"

    # 完整继承当前环境（AWS 凭证等）再叠加产物落点——SubprocessEngine 的 env 非 None 时整体替换，故须带 os.environ。
    # S3 上传 env（cloud 时注入两腿共用）：worker 拼 s3://<bucket>/<prefix><产物在 run 树内相对路径>（ADR 0029）。
    s3_env = (
        {"ARTIFACT_S3_BUCKET": artifact_s3[0], "ARTIFACT_S3_PREFIX": artifact_s3[1]}
        if artifact_s3 is not None else {}
    )

    def _env(local_dir: str | Path | None, local_key: str) -> dict | None:
        # local 落点 env + 可选 S3 上传 env。两者都无 → None（worker 全用 SDK 默认、报 file://）。
        if local_dir is None and not s3_env:
            return None
        env = {**os.environ}
        if local_dir is not None:
            env[local_key] = str(local_dir)
        env.update(s3_env)
        return env

    nova_env = _env(nova_logs_dir, "NOVA_LOGS_DIR")
    midscene_env = _env(midscene_run_dir, "MIDSCENE_RUN_DIR")
    # Nova 的 act timeout **双端同源**（ADR 0024 grace 硬约束）：组合根持 NOVA_ACT_TIMEOUT_S 单一真值，
    # 显式注入给 worker（消除「worker 私有默认 120」与「组合根 grace 下限」两处独立 120 的漂移）。
    # nova_env 为 None（无产物落点，如 --no-report）时也要建一份注入——故补一个继承 os.environ 的 env。
    if nova_env is None:
        nova_env = {**os.environ}
    nova_env["NOVA_ACT_TIMEOUT_S"] = str(NOVA_ACT_TIMEOUT_S)
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


# ============================================================================
# Store 装配（ADR 0016「cli backend 选择」/ 0030 决定六·七）：两个后端对称、都在 compose 可复用
# （cli 是第一个调用者，WebUI 直接复用这两个函数、不经 cli）。各返回：
#   (run_store, result_store, report_store, make_artifacts)
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
    from core.adapters.report_store.local import LocalReportStore
    from core.adapters.result_store.local import LocalResultStore
    from core.adapters.run_store.local import LocalRunStore

    root = Path(report_dir)
    run_store: RunStore = LocalRunStore(root)
    result_store: ResultStore = LocalResultStore(root)
    report_store: ReportStore = LocalReportStore(root)

    def make_artifacts(run_id: str, report_index) -> dict:
        # 全 file:// URI（与 cloud s3:// 同形工整）；run_meta/run_state/jobs_dir 是本地落点、report_index 取 finalize 返回
        run_dir = (root / run_id).resolve()
        d = {
            "run_meta": run_dir.joinpath("run_meta.json").as_uri(),
            "run_state": run_dir.joinpath("run_state.json").as_uri(),
            "jobs_dir": run_dir.joinpath("jobs").as_uri(),
        }
        if report_index is not None:  # None = report 写失败被隔离（ADR 0030 决定三），省略键、不放裸 'None'
            d["report_index"] = str(report_index)
        return d

    return run_store, result_store, report_store, make_artifacts


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
                       region: str | None = None, profile: str | None = None):
    """云端三层 store（RunStore→DDB、Result/ReportStore→S3）+ cloud artifacts descriptor（s3://+ddb://）。

    DDB 吃 `resource.Table`、三个 S3 件套（ResultStore/ReportStore/offloader）**共享一个 client**（喂错句柄
    类型运行时才 AttributeError，ADR 0016）。offloader 生产默认挂载（解 DDB 400KB 限，ADR 0030 决定七）。
    `import boto3` 惰性在 _make_* 钩子里（cli 主依赖不含 boto3，走 cli[aws]→core[aws] extra；缺 boto3 抛
    ImportError 由 cli 归到退 2）。prefix 分隔符规范化避粘连 key。
    """
    from core.adapters.report_store.s3 import S3ReportStore
    from core.adapters.result_store.s3 import S3ResultStore
    from core.adapters.run_store.arg_offload import S3StepArgumentOffloader
    from core.adapters.run_store.ddb import DynamoDBRunStore

    pfx = _normalize_prefix(prefix)
    ddb_table = _make_ddb_table(table, region=region, profile=profile)
    s3 = _make_s3_client(region=region, profile=profile)  # 一个 client 注入三个 S3 件套

    offloader = S3StepArgumentOffloader(s3, bucket, pfx)
    run_store: RunStore = DynamoDBRunStore(ddb_table, arg_offloader=offloader)
    result_store: ResultStore = S3ResultStore(s3, bucket, pfx)
    report_store: ReportStore = S3ReportStore(s3, bucket, pfx)

    def make_artifacts(run_id: str, report_index) -> dict:
        # jobs_dir=s3://（对拍 S3ResultStore key 布局）；run_meta/run_state=ddb:// 诊断指针（纯展示、不被解析）
        d = {
            "run_meta": f"ddb://{table}/{run_id}#META",
            "run_state": f"ddb://{table}/{run_id}#STATE",
            "jobs_dir": f"s3://{bucket}/{pfx}{run_id}/jobs/",
        }
        if report_index is not None:  # None = report 写失败被隔离，省略键
            d["report_index"] = str(report_index)
        return d

    return run_store, result_store, report_store, make_artifacts


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
