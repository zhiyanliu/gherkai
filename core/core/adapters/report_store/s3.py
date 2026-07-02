"""S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。

把一次 run 的 RunReport（manifest.json + index.html）**本体**写到 S3，返回 `s3://…/index.html` 的 ResourceUri。
对拍 `LocalReportStore` 的产出（manifest 形态、index 渲染），只换落点为 S3。**云端 adapter，需 boto3**
（`core[aws]` extra，缺它 import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

**注意区分**（[0027]/[0029]）：S3ReportStore 是把 **RunReport 自身**（core 派生的 manifest/index）写 S3，
与「worker 把**自己的产物**（trajectory/report.html）上传 S3」是两回事（后者是 per-worker by-design、[0029]）。

**href 恒 ==ref（[0027]/[0029]）**：cloud 报告用 `s3://` 绝对链接——`s3://` 全局可寻址、拷/分享不断，
无相对化必要（不 presign、不做产物拷贝）。故 make_href 恒返 rr.ref。（产物拷贝式 materialize 已否决，
见 [0027]「被拒方案」——曾计划 S3 版 copy_object 进 artifacts/，因 s3:// 已可移植而零收益。）

复用 LocalReportStore 的渲染真理源（`_render_index_html`/`SCHEMA_VERSION`）——不重写、两 adapter 同一份 index 渲染。
"""
from __future__ import annotations

import json

from core.adapters._boto import require_boto3
from core.model import ResourceUri, RunResult

# 复用 report 的单一真理源：index.html 渲染 + schema 版本 + report_index 三级投影（S3 与 Local 出一致的 report）
from core.adapters.report_store.local import SCHEMA_VERSION, _render_index_html, collect_report_index


class S3ReportStore:
    """ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍 LocalReportStore。"""

    def __init__(self, s3_client, bucket: str, prefix: str = "") -> None:
        """s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。
        prefix：可选 key 前缀（如 'runs/'），默认空。"""
        require_boto3("S3ReportStore")
        self._s3 = s3_client
        self._bucket = bucket
        self._prefix = prefix

    def write(self, run_id: str, result: RunResult, *, created_at: str = "") -> ResourceUri:
        """把 manifest.json + index.html 写到 `s3://bucket/<prefix><run_id>/`，返回 index.html 的 s3:// ResourceUri。"""
        base = f"{self._prefix}{run_id}"
        # report_index：复用共享三级投影（与 Local 同一真理源，形状/顺序不再靠人肉同步）。
        # href 恒 ==ref：s3:// 全局可寻址、无相对化必要（见模块 docstring）。
        index_entries = collect_report_index(result, make_href=lambda rr: rr.ref)

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
