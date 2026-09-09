"""ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。
云端类不在此处 re-export（按模块路径直 import，避免包导入即拉 boto3）。"""
from gherkai_core.adapters.report_store.local import LocalReportStore

__all__ = ["LocalReportStore"]
