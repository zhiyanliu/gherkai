"""job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」第一期）：worker 主流程唯一的 job 读入口。

对称 Midscene 的 lib/job-source.mts（各语言各写、语义契约对称，ADR 0024）+ 对称本腿 ArtifactUploader
的结构骨架（from_env 唯一读 env、退化态是同类实例、外部 client 惰性建）。

`read()` 返回**已解析的 job dict**（非流/句柄）——否则「从哪读」漏进 worker 主流程，S3/stdin 两态就无法
对主流程同形。subprocess 态：读 stdin 首行 JSON（core 侧 job_to_line 写单行 + \\n，ADR 0024）。

第一期只实现 subprocess 态（读 stdin）；S3 态（JOB_S3_URI 指针 + GetObject，因 RunTask overrides 8192
上限塞不下含 feature 的 job）属 WP-Fargate、本组件形状须能容纳但不实现（判据=有没有注入 JOB_S3_URI，非
「是否 Fargate」）。**无「回落调试」分支**：stdin 本就是手动直跑入口，subprocess 态即调试态。
"""
from __future__ import annotations

import json
import os
import sys


class JobSource:
    """按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())——同步读首行、不等 EOF。"""

    def __init__(self, *, uri: str | None) -> None:
        # 私有构造只吃已解析值（对称 ArtifactUploader）：uri 为 None = subprocess 态（读 stdin）。
        self._uri = uri

    @classmethod
    def from_env(cls) -> "JobSource":
        """从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态（Fargate 化，未实现）；无/空串 → stdin 态。

        `or None`：空串统一当「未注入」（对称 Midscene `|| undefined`、ArtifactUploader `bucket or None`）——
        避免两腿对「注入了空串」给出相反语义。
        """
        return cls(uri=os.environ.get("JOB_S3_URI") or None)

    def read(self) -> dict:
        """读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。"""
        # S3 态（Fargate 化，未实现）：注入了 JOB_S3_URI 却跑到这 = 配置错，显式报错、不静默走 stdin（否则
        # Fargate 无 stdin 会挂在 readline；fail-loud 更安全，对称 Midscene）。实现时惰性建 boto3 + GetObject。
        if self._uri is not None:
            raise NotImplementedError(f"JobSource: S3 态未实现（JOB_S3_URI={self._uri}）——属 Fargate 化")
        return json.loads(sys.stdin.readline())
