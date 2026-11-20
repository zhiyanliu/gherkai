"""S3ResultStore：ResultStore port 的 S3 实装（ADR 0030 决定六里定 ResultStore 后端为 S3 的那一条；ADR 0016「留口子：核心注入接口」
的三层 store 后端选型）。

每次保存明细一个 S3 对象，键为 `<prefix><run_id>/jobs/<quote(result_id, safe='')>.json`：只由写入方给出的标识构成，不带 scope_id，同一个
job 的多份互不覆盖，用哪一份由运行态里这个 job 的终态点名（ADR 0030 决定三「点名」条）。读者先读运行态、再按标识直接算出键取那一个
对象，不列举前缀：读明细只要 `s3:GetObject`，不要 `s3:ListBucket`。标识按不透明标识符的惯例编码成键里的一段（`quote(safe='')` 把 `/`
也编码成 `%2F`，不在 S3 里造出假的子前缀），对拍 `LocalResultStore` 的文件名。将来若需「跨 scope 查询/过滤」再加 DDB 索引层（加法
不返工）。**云端 adapter，需 boto3**（`gherkai-core[aws]` extra，缺它 import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

body：`json.dumps(job_result_to_dict(jr))`（自包含，嵌完整 Job def，同 local）；serialize 是单一真理源，标识不写进 body。
云端不在进程内重试保存：保存失败让这次调用失败，由流的重试或之后的触发重做（ADR 0030 决定三「保存明细失败」条）。
"""
from __future__ import annotations

import json
from urllib.parse import quote

from gherkai_core.adapters._boto import require_boto3
from gherkai_core.model import JobResult
from gherkai_core.serialize import job_result_from_dict, job_result_to_dict


class S3ResultStore:
    """ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍 LocalResultStore。"""

    def __init__(self, s3_client, bucket: str, prefix: str = "") -> None:
        """s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。
        prefix：可选 key 前缀（如 'runs/'），默认空。"""
        require_boto3("S3ResultStore")
        self._s3 = s3_client
        self._bucket = bucket
        self._prefix = prefix

    def _key(self, run_id: str, result_id: str) -> str:
        # quote(safe='')：/ 也编码成 %2F，标识恒是单段、不造子前缀（对拍 local 的文件名）
        return f"{self._prefix}{run_id}/jobs/{quote(result_id, safe='')}.json"

    def save_job_result(self, run_id: str, result_id: str, job: JobResult) -> None:
        """把一份明细存成带这个标识的 S3 对象：一次不带条件的 PutObject，单个对象的 PUT 本身是原子的，读者要么取不到、要么取到完整
        的一份。同一个标识再存一次即覆盖，只发生在同一次保存的重做上（内容相同）。"""
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self._key(run_id, result_id),
            Body=json.dumps(job_result_to_dict(job), ensure_ascii=False).encode("utf-8"),
        )

    def load_job_result(self, run_id: str, result_id: str) -> JobResult | None:
        """按标识取那一份（一次 GetObject，不查询、不列举）；这个标识下没有对象（NoSuchKey）时返回 None。

        没有 `s3:ListBucket` 权限时，S3 对不存在的键回 AccessDenied 而不是 NoSuchKey：那时照常抛出，与别的读取失败一样，不读作 None。"""
        try:
            resp = self._s3.get_object(Bucket=self._bucket, Key=self._key(run_id, result_id))
        except self._s3.exceptions.NoSuchKey:
            return None
        return job_result_from_dict(json.loads(resp["Body"].read()))

    def preflight(self) -> None:
        """探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。"""
        self._s3.head_bucket(Bucket=self._bucket)
