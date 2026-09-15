"""ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。

云端类不在此处 re-export，消费方按模块路径直 import（`from gherkai_core.adapters.result_store.s3 import S3ResultStore`）。
**这是本包的排版惯例、不是 import 开销约束**：`s3.py` 模块级不 import boto3（boto3 依赖由 `adapters/_boto.py` 的
`require_boto3` 在构造时兜底、真早失败在组合根），re-export 并不会让包导入拉 boto3——同目录 `event_log/__init__.py`
就直接 re-export 了云端类 `DdbEventLog`。四个子包口径不统一，改动时勿据此反推 import 期约束。
"""
from gherkai_core.adapters.result_store.local import LocalResultStore

__all__ = ["LocalResultStore"]
