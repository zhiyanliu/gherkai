# Exit Item Drain Test

> 4 nodes · cohesion 0.50

## Key Concepts

- **test_read_events_ignores_exit_item_on_stopped_drain_path()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_put_exit_item()** (5 connections) — `core/tests/test_fargate_engine.py`
- **预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **worker 零事件退出 + exit item 已落：STOPPED 兜底路径（含 _final_drain 强一致终读）同样只读 worker 段。…** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Exit Code Tests](Fargate_Exit_Code_Tests.md) (4 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 10 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*