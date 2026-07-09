"""job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」第一期）：worker 主流程唯一的 job 读入口。

对称 Midscene 的 lib/job-source.mts（各语言各写、语义契约对称，ADR 0024）+ 对称本腿 ArtifactUploader
的结构骨架（from_env 唯一读 env、退化态是同类实例、外部 client 惰性建）。

`read()` 返回**已解析的 job dict**（非流/句柄）——否则「从哪读」漏进 worker 主流程，S3/stdin 两态就无法
对主流程同形。subprocess 态：读 stdin 首行 JSON（core 侧 job_to_line 写单行 + \\n，ADR 0024）。

两态（ADR 0024）：subprocess 态读 stdin 首行 JSON；S3 态（JOB_S3_URI 指针 + GetObject，因 RunTask overrides
8192 上限塞不下含 feature 的 job）Fargate 化用。判据=有没有注入 JOB_S3_URI，非「是否 Fargate」（ADR 0016 红线）。
**无「回落调试」分支**：stdin 本就是手动直跑入口，subprocess 态即调试态。
"""
from __future__ import annotations

import json
import os
import sys


class JobSource:
    """按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3 态：GetObject(JOB_S3_URI)。"""

    def __init__(self, *, uri: str | None) -> None:
        # 私有构造只吃已解析值（对称 ArtifactUploader）：uri 为 None = subprocess 态（读 stdin）、非 None = S3 态。
        self._uri = uri

    @classmethod
    def from_env(cls) -> "JobSource":
        """从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。

        `or None`：空串统一当「未注入」（对称 Midscene `|| undefined`、ArtifactUploader `bucket or None`）——
        避免两腿对「注入了空串」给出相反语义。
        """
        return cls(uri=os.environ.get("JOB_S3_URI") or None)

    def read(self) -> dict:
        """读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。

        S3 态（Fargate 化）：JOB_S3_URI = `s3://bucket/key`，惰性建 boto3 + GetObject + json.loads。不静默走 stdin
        （否则 Fargate 无 stdin 会挂在 readline；判 uri 分流，fail-loud，对称 Midscene）。
        """
        if self._uri is not None:
            return self._read_s3(self._uri)
        return json.loads(sys.stdin.readline())

    @staticmethod
    def _read_s3(uri: str) -> dict:
        """s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称 ArtifactUploader._s3 Config）。"""
        if not uri.startswith("s3://"):
            raise ValueError(f"JobSource: JOB_S3_URI 须为 s3:// URI，得到 {uri!r}")
        bucket, _, key = uri[len("s3://"):].partition("/")
        import boto3
        from botocore.config import Config
        cfg = Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 0})
        s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION"), config=cfg)
        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        return json.loads(body.split("\n")[0])  # job 是单行 JSON（core job_to_line + \n）
