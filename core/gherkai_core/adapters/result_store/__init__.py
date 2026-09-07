"""ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。"""
from gherkai_core.adapters.result_store.local import LocalResultStore

__all__ = ["LocalResultStore"]
