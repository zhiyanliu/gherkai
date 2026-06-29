"""RunStore adapters（ADR 0016）。当前只有 local；未来 ddb。"""
from core.adapters.run_store.local import LocalRunStore

__all__ = ["LocalRunStore"]
