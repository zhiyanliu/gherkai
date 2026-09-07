"""S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。

数据面判定真值——每个 job(=scope) 一个 S3 对象。对拍 `LocalResultStore` 行为（save/load/load_all round-trip、
scope_id 不透明编码），只把落点从本地文件换成 S3 对象。**云端 adapter，需 boto3**（`core[aws]` extra，缺它
import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

**这坐实 ADR 里原「待定」的 ResultStore 后端 = S3**：赌 CI 按 run_id+scope_id 键取判定（key 直接算得出、
无需查询）；将来若需「跨 scope 查询/过滤」再加 DDB 索引层（加法不返工，[0016]）。

**key = `<prefix><run_id>/jobs/<quote(scope_id, safe='')>.json`**：scope_id 是不透明标识（可含 `/`:空格/中文，
[0025]），`quote(safe='')` 把 `/` 也编码成 `%2F`——否则 scope_id 里的 `/` 会在 S3 里造出假的子前缀、
让 `load_all` 的 prefix 反解歧义。对拍 LocalResultStore 的可逆编码。`load_all` 用 list_objects prefix + unquote basename 还原。

body：`json.dumps(job_result_to_dict(jr))`（自包含，嵌完整 Job def，同 local）；serialize 是单一真理源。
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

    def _jobs_prefix(self, run_id: str) -> str:
        return f"{self._prefix}{run_id}/jobs/"

    def _key(self, run_id: str, scope_id: str) -> str:
        # quote(safe='')：/ 也编码成 %2F，scope_id 恒是单段、不造子前缀（对拍 local 文件名可逆编码）
        return f"{self._jobs_prefix(run_id)}{quote(scope_id, safe='')}.json"

    def save_job_result(self, run_id: str, job: JobResult) -> None:
        """把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。"""
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self._key(run_id, job.scope_id),
            Body=json.dumps(job_result_to_dict(job), ensure_ascii=False).encode("utf-8"),
        )

    def load_job_result(self, run_id: str, scope_id: str) -> JobResult | None:
        """读回单个 JobResult（按键取，无需查询）；不存在返回 None。"""
        try:
            resp = self._s3.get_object(Bucket=self._bucket, Key=self._key(run_id, scope_id))
        except self._s3.exceptions.NoSuchKey:
            return None
        return job_result_from_dict(json.loads(resp["Body"].read()))

    def load_all(self, run_id: str) -> list[JobResult]:
        """读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。

        **必须翻页**：list_objects_v2 单页硬上限 1000 key，一次 run 可 >1000 scope。只读单页会静默截断、
        丢判定真值——而 ResultStore 是判定真值唯一权威（ADR 0016）、CI 据此判退出码，截断会让本该红的 run
        误判全绿。故用 paginator 收全部页（对拍 LocalResultStore.load_all 的 glob 无上限语义）。
        按 key 排序保稳定输出（对拍 local 的 sorted glob）。
        """
        prefix = self._jobs_prefix(run_id)
        paginator = self._s3.get_paginator("list_objects_v2")
        keys = sorted(
            obj["Key"]
            for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix)
            for obj in page.get("Contents", [])
        )
        results: list[JobResult] = []
        for key in keys:
            body = self._s3.get_object(Bucket=self._bucket, Key=key)["Body"].read()
            results.append(job_result_from_dict(json.loads(body)))
        return results

    def preflight(self) -> None:
        """探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。"""
        self._s3.head_bucket(Bucket=self._bucket)
