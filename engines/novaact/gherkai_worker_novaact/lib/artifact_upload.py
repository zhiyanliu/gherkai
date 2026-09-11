"""产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。

由组合根注入的 S3 落点 env 驱动（`ARTIFACT_S3_BUCKET` + `ARTIFACT_S3_PREFIX`，跟 `--backend cloud` 走）——
**未注入落点（local 路径；或手动直跑/脚手架没给这组 env）→ `to_report_ref` 原样报 `file://`、不上传、不删**
（零行为变化）。判据是「有没有注入落点」，与 `--no-report` **正交**——那个 flag 只管落库/渲染报告，不管产物
上传落点。worker 对"我在哪跑"无知，只认这组 env 有没有（ADR 0016 注入红线）。

S3 key 镜像本地 run 树（ADR 0029）：任一产物 key = `<prefix><产物相对本地 run 目录的路径>`，与 S3ReportStore/
ResultStore 同 `<prefix>` 前缀。本地 run 目录 = 产物落点目录（`NOVA_LOGS_DIR`）的父级。key 是**确定性纯路径
计算**，不依赖上传，故 `to_report_ref` 可先算 s3:// ref、实时报出。

上传/删除策略（ADR 0029 混合两级 + 整目录，抗 SDK 升级；后台队列一级由 ADR 0042 决策一加入）：
- `to_report_ref(path)`：reportRef 指向的文件 → **实时上传**（不删，记进 `_uploaded`）、报 s3://。失败抛（worker
  可观测、engine_error）——报告链接强保证。
- `ref_for(path)`：只算 ref、不上传（key 是确定性纯路径计算）。
- `enqueue(paths)` / `drain(timeout_s)`：**后台单线程 FIFO 队列**（ADR 0042 决策一「上传时机分两类」）。evidence
  的截图在 `step_done` 发出**之后**入队，字节在下个 step 跑的同时上传——既不压判定临界路径，也不拖到 scope 末
  才第一次尝试。每项失败重试一次后记一行日志放弃（文件仍在目录里，flush 还有一次机会）；成功即记进 `_uploaded`
  让 flush 跳过。收尾（scope 末 / 提前退出路径）用 `drain` **有界**等它传完，超时就交给 flush 兜。
- `flush_and_cleanup(dir)`：scope 末调。walk 整个产物目录**递归**上传剩余文件（已实时传/队列已传的**跳过**）——
  **不按文件类型/名字挑**（整目录一股脑传，本地清理不损耗任何产物、不受 SDK 升级影响）。每个文件同样重试一次；
  剩余上传失败**吞掉**（报告链接不依赖它们）。**全部成功**（实时 + 队列 + 剩余）才 `rmtree` 整目录（本地零残留）；
  任一失败则整目录保留不删。

线程安全：boto3 低层 client 本身线程安全（单 client 不变），需守的是 `_uploaded` 集合——主流程与队列线程都读写它，
故一律经 `_lock`。
"""
from __future__ import annotations

import os
import queue
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Iterable

# 按后缀显式打 Content-Type（与 Midscene uploader 同一规则，ADR 0024 两引擎语义对称）：boto3/s3transfer
# **不猜** content type，默认落成 binary/octet-stream → presigned/控制台直开 trajectory .html（ADR 0027 选
# .html 就是为「人能看」）会被当附件下载而非渲染。未列后缀不设（走 S3 默认）。
# 图片/json 同理（ADR 0042 决策一）：evidence 的截图与 evidence.json 都要能直开渲染（截图被当附件下载、
# json 被当二进制，agent 与人取证都得先另存），两引擎同规则同步改。
_CONTENT_TYPE_BY_SUFFIX = {
    ".html": "text/html; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".json": "application/json",
}


def _log(msg: str) -> None:
    """诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。

    本模块**不 import run_scope 的 log**（那边 import 本模块，反向依赖会成环）；队列线程与主流程并发写 stderr
    安全（BufferedWriter 自带锁；「非重入」那个坑只在信号 handler 里写才撞，见 run_scope._on_signal）。
    """
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


def _extra_args(local_abs: Path) -> dict:
    """upload_file 的 ExtraArgs（两处上传共用，避免第三处漂移）：仅在有映射时带 ContentType。"""
    ct = _CONTENT_TYPE_BY_SUFFIX.get(local_abs.suffix.lower())
    return {"ContentType": ct} if ct else {}


class ArtifactUploader:
    """按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。

    组合根经 env 注入（ADR 0029）：`ARTIFACT_S3_BUCKET` / `ARTIFACT_S3_PREFIX`（`<report_dir>/<run_id>/`，
    已含尾 /）；`run_dir`（本地 run 树根 = NOVA_LOGS_DIR 父级）用于算产物相对路径 → 镜像成 S3 key。
    """

    def __init__(self, *, bucket: str | None, prefix: str, run_dir: Path | None) -> None:
        self._bucket = bucket
        self._prefix = prefix
        self._run_dir = run_dir
        self._client = None            # 惰性建（仅真上传时，避免 no-op 路径 import boto3）
        self._uploaded: set[str] = set()  # 已上传的绝对路径（实时/队列/flush 三处共用，跳过重复传）
        self._flush_ok = True          # 剩余批量是否全成功（任一失败 → 整目录不删）
        # `_uploaded` 被主流程与队列线程同时读写 → 一律经这把锁（boto3 低层 client 自身线程安全，不必守）
        self._lock = threading.Lock()
        # 后台上传队列（ADR 0042 决策一）：单线程 FIFO、惰性起（首次 enqueue 才起，no-op 档永不起）
        self._q: "queue.Queue[str]" = queue.Queue()
        self._worker: threading.Thread | None = None
        self._pending = 0              # 入队未处理完的项数（含在途那一项）——drain 等它归零
        self._idle = threading.Condition()  # 配 _pending：归零时 notify，drain 有界等

    @classmethod
    def from_env(cls) -> "ArtifactUploader":
        """从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。"""
        bucket = os.environ.get("ARTIFACT_S3_BUCKET") or None
        prefix = os.environ.get("ARTIFACT_S3_PREFIX", "")
        logs_dir = os.environ.get("NOVA_LOGS_DIR")
        run_dir = Path(logs_dir).parent if logs_dir else None
        if bucket is not None and run_dir is None:
            # fail-loud：注入了桶却没给 SDK 落点（NOVA_LOGS_DIR）= 组合根配置矛盾，非降级档——静默 no-op
            # 会让产物报 file:// 且随容器盘销毁必丢（ADR 0033 真跑事故「只注①不注②等于没上传」）。
            raise ValueError(
                "产物上传：已注入 ARTIFACT_S3_BUCKET 但缺 NOVA_LOGS_DIR，算不出产物落点、无法上传"
                "（起 worker 的一方须同时注入两者，否则产物随容器盘销毁）")
        return cls(bucket=bucket, prefix=prefix, run_dir=run_dir)

    @property
    def enabled(self) -> bool:
        """是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。"""
        return self._bucket is not None and self._run_dir is not None

    def _s3(self):
        if self._client is None:
            import boto3
            from botocore.config import Config
            # 套超时（ADR 0029「上传必须套超时」/ 退出时间有界护栏）：boto3 默认 connect/read 各 60s + 重试，
            # 退化网络下单次上传最坏分钟级、拖住 worker 退出 → 等 grace 耗尽被 SIGKILL → 跳过会话清理 → 泄漏。
            # 显式设短超时 + 关重试，使上传快速失败、best-effort 放弃（抢传/flush 均吞错）。超时 « grace（ADR 0024）。
            # **max_attempts=0 才是「关重试、单次尝试」**：botocore 语义里 max_attempts=N 是「重试次数」、总尝试
            # = N+1，故 =1 其实是「1 次重试=共 2 次尝试 + 中间退避 sleep」，与「快速失败」相悖；=0 → 总尝试 1、零退避。
            cfg = Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 0})
            self._client = boto3.client("s3", region_name=os.environ.get("AWS_REGION"), config=cfg)
        return self._client

    def _key_for(self, local_abs: Path) -> str:
        """产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。"""
        rel = local_abs.resolve().relative_to(self._run_dir.resolve())  # type: ignore[union-attr]
        return f"{self._prefix}{rel.as_posix()}"

    def to_report_ref(self, local_path: str) -> str:
        """reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。

        失败原样抛（worker 记 engine_error、可观测）——报告链接强保证，不吞。
        no-op 路径**不 resolve**（保调用方 abspath 语义、不展开 symlink，与旧 `file://{abspath}` 一致）。
        """
        if not self.enabled:
            return f"file://{local_path}"  # no-op（local / 未注入落点）；调用方已 abspath
        p = Path(local_path)
        key = self._key_for(p)
        # 幂等短路：已成功传过（同一文件被 except 重建 reportRefs 再调，或多次引用）→ 直接返 s3:// ref、不重传
        # （key 确定性可算）。消除对已传兄弟的冗余 PutObject（ADR 0029 幂等去重）。
        if self._is_uploaded(p):
            return f"s3://{self._bucket}/{key}"
        self._s3().upload_file(str(p), self._bucket, key, ExtraArgs=_extra_args(p))  # 实时上传（失败抛 → 可观测、不删）
        self._mark_uploaded(p)                             # 记下，队列/flush 时跳过
        return f"s3://{self._bucket}/{key}"

    def ref_for(self, local_path: str) -> str:
        """**只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。

        给 evidence 的截图用（ADR 0042 决策一「上传时机分两类」）：即时上传是逐文件串行 PutObject 且套了短超时，
        把 K×票数 次 PutObject 压在判定临界路径上会把已成的判定拖在网络上；key 是确定性纯路径计算，故可先算
        URI 写进 evidence.json、字节交给 `enqueue` 的后台队列（收尾有界 `drain`，漏网的由 flush 兜；总字节不变）。
        代价：cloud 档若 worker 被硬杀，最后一个 step 在途的一两张截图 URI 可能悬空（json 已传、图没传）——
        消费端按「读不到」处理；本地档 `file://` 无此问题。
        """
        if not self.enabled:
            return f"file://{local_path}"  # 与 to_report_ref 的 no-op 分支同形（不 resolve，保调用方 abspath 语义）
        return f"s3://{self._bucket}/{self._key_for(Path(local_path))}"

    # ---- 已传集合的两个访问点（主流程 + 队列线程共用，故一律经锁）----
    def _is_uploaded(self, local_abs: Path) -> bool:
        with self._lock:
            return str(local_abs.resolve()) in self._uploaded

    def _mark_uploaded(self, local_abs: Path) -> None:
        with self._lock:
            self._uploaded.add(str(local_abs.resolve()))

    def _upload_once_with_retry(self, local_abs: Path) -> bool:
        """传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。

        队列与 flush 共用（key 规则与 ExtraArgs 只此一处，不复刻——`to_report_ref` 的 key 由同一 `_key_for` 算，
        故三条路径给出的 key 逐字一致，`ref_for` 先算的 URI 才不会悬空）。
        **重试之间不 sleep**：client 侧本就 connect 5s / read 10s、零退避（见 `_s3`），两次尝试最坏 ~30s——收尾
        排空的预算按此量级取（有界，ADR 0029「退出时间有界」）。
        """
        for _ in range(2):          # 首次 + 重试一次
            try:
                self._s3().upload_file(str(local_abs), self._bucket, self._key_for(local_abs),
                                       ExtraArgs=_extra_args(local_abs))
            except Exception:  # noqa: BLE001  含 key 算不出（文件不在 run 树内）等一切故障：best-effort
                continue
            self._mark_uploaded(local_abs)
            return True
        return False

    # ---- 后台队列（ADR 0042 决策一「上传时机分两类」）----
    def enqueue(self, paths: Iterable[str]) -> None:
        """把文件交给后台队列顺序上传（**不阻塞调用方**）；no-op 档直接返回。

        调用点在 `step_done` **emit 之后**（ADR 0042 决策一：截图字节绝不压判定临界路径）。队列线程惰性起、
        daemon（进程退出不被它拖住；收尾靠 `drain` 有界等）。
        """
        if not self.enabled:
            return
        items = [str(p) for p in paths]
        if not items:
            return
        with self._idle:
            for item in items:
                self._q.put(item)
                self._pending += 1
        self._ensure_worker()

    def drain(self, timeout_s: float) -> bool:
        """有界等队列传完（含在途那一项）：全部处理完 True，超时 False（剩下的交给 flush 兜）。

        收尾（scope 末 / 提前退出路径）调，位置**排在会话释放之后**（ADR 0024「会话释放优先」）——退出路径的
        预算计入 grace（调用方给的 timeout_s 就是那份预算）。no-op 档立即 True（队列永远是空的）。
        """
        if not self.enabled:
            return True
        deadline = time.monotonic() + timeout_s
        with self._idle:
            while self._pending > 0:
                left = deadline - time.monotonic()
                if left <= 0:
                    return False
                self._idle.wait(left)
        return True

    def _ensure_worker(self) -> None:
        with self._lock:
            if self._worker is None:
                self._worker = threading.Thread(
                    target=self._queue_loop, name="gherkai-artifact-upload", daemon=True)
                self._worker.start()

    def _queue_loop(self) -> None:
        """队列线程主体：FIFO 逐个传，**绝不因单项失败而死**（死了 = 后面的截图全不传且无人察觉）。"""
        while True:
            item = self._q.get()
            try:
                self._upload_queued(item)
            except Exception:  # noqa: BLE001  兜住 `_upload_queued` 意外抛出的一切，保线程活着
                pass
            finally:
                with self._idle:
                    self._pending -= 1
                    if self._pending == 0:
                        self._idle.notify_all()   # 唤醒 drain

    def _upload_queued(self, path: str) -> None:
        p = Path(path)
        if self._is_uploaded(p):
            return          # 已被实时上传/flush 传过（幂等去重，ADR 0029）
        if not self._upload_once_with_retry(p):
            # 放弃：只一行产品语言的日志（文件仍在产物目录里 → scope 末 flush 还有一次机会）
            _log(f"证据截图上传失败（收尾时再试一次）：{p.name}")

    def flush_and_cleanup(self, artifact_dir: str | Path) -> None:
        """scope 末：整目录递归上传剩余文件（跳过已传的）+ 全成功则 rmtree 整目录（ADR 0029）。

        no-op（未注入落点）→ 直接返回（不碰本地，保 local 行为）。剩余文件各**重试一次**（同后台队列，
        ADR 0042 决策一），两次都失败则**吞掉**（只影响该文件、报告链接不依赖它们），但会置 `_flush_ok=False`
        → 整目录不删（本地保留、产物不丢）。
        **不按文件类型/名字挑**——walk 整个目录、一股脑传，抗引擎 SDK 升级（新增/改名文件也照传）。
        **调用方应先 `drain`**（ADR 0042 决策一）：队列传完的这里跳过，只兜漏网的。真撞上「队列在途、这里又
        walk 到同一文件」也无害——同字节同 key 的 PutObject 幂等（只多一次请求）。
        """
        if not self.enabled:
            return
        d = Path(artifact_dir)
        if not d.exists():
            return
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            if self._is_uploaded(f):
                continue  # 已实时传（reportRef）或已由后台队列传完，跳过
            # 失败吞掉（报告链接不依赖它），但标记 → 整目录不删。重试一次同队列（ADR 0042 决策一：一次 S3
            # 抖动不该等于一个永久 404 的截图 URI）。
            if not self._upload_once_with_retry(f):
                self._flush_ok = False
        # 全部成功（实时 + 剩余）才删整目录——本地零残留；任一失败则保留（产物不丢，ADR 0029 护栏）
        if self._flush_ok:
            shutil.rmtree(d, ignore_errors=True)
