"""ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。"""
from gherkai_core.adapters.report_store.local import LocalReportStore

__all__ = ["LocalReportStore"]
