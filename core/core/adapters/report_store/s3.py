"""S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。

把一次 run 的 RunReport（manifest.json + index.html）**本体**写到 S3，返回 `s3://…/index.html` 的 ResourceUri。
对拍 `LocalReportStore` 的产出（manifest 形态、index 渲染），只换落点为 S3。**云端 adapter，需 boto3**
（`core[aws]` extra，缺它 import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

**注意区分**（[0027]/[0029]）：S3ReportStore 是把 **RunReport 自身**（core 派生的 manifest/index）写 S3，
与「worker 把**自己的产物**（trajectory/report.html）上传 S3」是两回事（后者是 per-worker by-design、[0029]）。

**materialize v1.1 当 no-op**（[0029]）：第一版只把核心事做对——写 manifest+index 上 S3、`href==ref`
（index 里链接原样指向 worker 报的 ref）。产物收拢进 `s3://…/<run_id>/artifacts/` 求自包含的目标语义已定
（对标 Local，见 [0029]），但第一版**收到 materialize=True 也忽略、不报错**（cli 会透传 --materialize，报错会炸）。
交付的是「链接可能不完全可点」的 S3 RunReport（file:// 链接跨机器断、s3:// 链接待 presign）——已知、接受的取舍。

复用 LocalReportStore 的渲染真理源（`_render_index_html`/`SCHEMA_VERSION`）——不重写、两 adapter 同一份 index 渲染。
"""
from __future__ import annotations

import json

from core.adapters._boto import require_boto3
from core.model import ReportRef, ResourceUri, RunResult

# 复用 report 渲染的单一真理源（index.html 拼装 + schema 版本）——S3 与 Local 出一致的 report
from core.adapters.report_store.local import SCHEMA_VERSION, _render_index_html


def _index_entry(scope_id: str, scenario_id: str | None, engine: str, rr: ReportRef) -> dict:
    """report_index 一条扁平项（materialize=no-op：href==ref，不拷贝产物）。形状对拍 LocalReportStore._entry。"""
    return {
        "scope_id": scope_id,
        "scenario_id": scenario_id,
        "engine": engine,
        "kind": rr.kind,
        "ref": rr.ref,
        "href": rr.ref,   # no-op：链接原样指向 worker 报的 ref（第一版取舍，[0029]）
        "label": rr.label,
    }


class S3ReportStore:
    """ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍 LocalReportStore。"""

    def __init__(self, s3_client, bucket: str, prefix: str = "") -> None:
        """s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。
        prefix：可选 key 前缀（如 'runs/'），默认空。"""
        require_boto3("S3ReportStore")
        self._s3 = s3_client
        self._bucket = bucket
        self._prefix = prefix

    def write(self, run_id: str, result: RunResult, *, created_at: str = "", materialize: bool = False) -> ResourceUri:
        """把 manifest.json + index.html 写到 `s3://bucket/<prefix><run_id>/`，返回 index.html 的 s3:// ResourceUri。

        materialize 当 no-op（第一版，见模块 docstring）——收到 True 也忽略、不报错。
        """
        base = f"{self._prefix}{run_id}"
        # report_index 顺序对拍 LocalReportStore._collect：每 job 内先 scope 级（scenario_id=None）后 scenario 级
        index_entries: list[dict] = []
        for jr in result.jobs:
            for rr in jr.report_refs:
                index_entries.append(_index_entry(jr.scope_id, None, jr.engine, rr))
            for sr in jr.scenarios:
                for rr in sr.report_refs:
                    index_entries.append(_index_entry(jr.scope_id, sr.scenario_id, jr.engine, rr))

        # manifest = 纯派生导航视图（同 Local，[0027]）：不内嵌 result 真值，靠 run_id 软引用
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "created_at": created_at,
            "report_index": index_entries,
        }
        self._s3.put_object(
            Bucket=self._bucket, Key=f"{base}/manifest.json",
            Body=json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json; charset=utf-8",  # 与 index.html 一致，presigned 浏览器直开不被当二进制
        )
        # index.html 复用 Local 的渲染（单一真理源）——两 adapter 出一致的入口页
        self._s3.put_object(
            Bucket=self._bucket, Key=f"{base}/index.html",
            Body=_render_index_html(manifest, result).encode("utf-8"),
            ContentType="text/html; charset=utf-8",
        )
        return ResourceUri(f"s3://{self._bucket}/{base}/index.html")

    def preflight(self) -> None:
        """探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。"""
        self._s3.head_bucket(Bucket=self._bucket)
