"""产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。

由组合根注入的 S3 落点 env 驱动（`ARTIFACT_S3_BUCKET` + `ARTIFACT_S3_PREFIX`，跟 `--backend cloud` 走）——
**未注入（local / --no-report）→ `to_report_ref` 原样报 `file://`、不上传、不删**（零行为变化）。worker 对
"我在哪跑"无知，只认这组 env 有没有（ADR 0016 注入红线）。

S3 key 镜像本地 run 树（ADR 0029）：任一产物 key = `<prefix><产物相对本地 run 目录的路径>`，与 S3ReportStore/
ResultStore 同 `<prefix>` 前缀。本地 run 目录 = 产物落点目录（`NOVA_LOGS_DIR`）的父级。key 是**确定性纯路径
计算**，不依赖上传，故 `to_report_ref` 可先算 s3:// ref、实时报出。

上传/删除策略（ADR 0029 混合两级 + 整目录，抗 SDK 升级）：
- `to_report_ref(path)`：reportRef 指向的文件 → **实时上传**（不删，记进 `_uploaded`）、报 s3://。失败抛（worker
  可观测、engine_error）——报告链接强保证。
- `flush_and_cleanup(dir)`：scope 末调。walk 整个产物目录**递归**上传剩余文件（已实时传的**跳过**）——**不按
  文件类型/名字挑**（整目录一股脑传，本地清理不损耗任何产物、不受 SDK 升级影响）。剩余上传失败**吞掉**（报告
  链接不依赖它们）。**全部成功**（实时 + 剩余）才 `rmtree` 整目录（本地零残留）；任一失败则整目录保留不删。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path


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
        self._uploaded: set[str] = set()  # 已实时上传的绝对路径（flush 时跳过，不重复传）
        self._flush_ok = True          # 剩余批量是否全成功（任一失败 → 整目录不删）

    @classmethod
    def from_env(cls) -> "ArtifactUploader":
        """从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。"""
        bucket = os.environ.get("ARTIFACT_S3_BUCKET") or None
        prefix = os.environ.get("ARTIFACT_S3_PREFIX", "")
        logs_dir = os.environ.get("NOVA_LOGS_DIR")
        run_dir = Path(logs_dir).parent if logs_dir else None
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
        # （key 确定性可算）。消除对已传兄弟的冗余 PutObject（ADR 0029 review #4）。
        if str(p.resolve()) in self._uploaded:
            return f"s3://{self._bucket}/{key}"
        self._s3().upload_file(str(p), self._bucket, key)  # 实时上传（失败抛 → 可观测、不删）
        self._uploaded.add(str(p.resolve()))               # 记下，flush 时跳过
        return f"s3://{self._bucket}/{key}"

    def flush_and_cleanup(self, artifact_dir: str | Path) -> None:
        """scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。

        no-op（未注入落点）→ 直接返回（不碰本地，保 local 行为）。剩余文件上传失败**吞掉**（只影响该文件、
        报告链接不依赖它们），但会置 `_flush_ok=False` → 整目录不删（本地保留、产物不丢）。
        **不按文件类型/名字挑**——walk 整个目录、一股脑传，抗引擎 SDK 升级（新增/改名文件也照传）。
        """
        if not self.enabled:
            return
        d = Path(artifact_dir)
        if not d.exists():
            return
        for f in d.rglob("*"):
            if not f.is_file():
                continue
            if str(f.resolve()) in self._uploaded:
                continue  # reportRef 文件已实时传，跳过
            try:
                self._s3().upload_file(str(f), self._bucket, self._key_for(f))
            except Exception:  # noqa: BLE001  剩余文件上传失败：吞掉（报告链接不依赖它），但标记 → 整目录不删
                self._flush_ok = False
        # 全部成功（实时 + 剩余）才删整目录——本地零残留；任一失败则保留（产物不丢，ADR 0029 护栏）
        if self._flush_ok:
            shutil.rmtree(d, ignore_errors=True)
