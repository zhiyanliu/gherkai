"""RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030 决定六）。
云端类不在此处 re-export（按模块路径直 import，避免包导入即拉 boto3）。"""
from gherkai_core.adapters.run_store.local import LocalRunStore

__all__ = ["LocalRunStore"]
