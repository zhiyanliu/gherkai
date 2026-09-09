# Worker Exit Code Mapping

> 8 nodes · cohesion 0.25

## Key Concepts

- **raise_for_worker_exit()** (12 connections) — `core/gherkai_core/wire.py`
- **test_raise_for_worker_exit_maps_codes_with_fargate_label()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_raise_for_worker_exit_label_names_the_transport_field()** (3 connections) — `core/tests/test_wire.py`
- **test_raise_for_worker_exit_maps_codes()** (3 connections) — `core/tests/test_wire.py`
- **worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。 80 →…** (1 connections) — `core/gherkai_core/wire.py`
- **码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…** (1 connections) — `core/tests/test_fargate_engine.py`
- **码→异常的分类（schedule 按类型分流：WorkerNetworkError→network_error 可重试 /…** (1 connections) — `core/tests/test_wire.py`
- **两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。** (1 connections) — `core/tests/test_wire.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (3 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Fargate Engine](Fargate_Engine.md) (1 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (1 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (1 shared connections)

## Source Files

- `core/gherkai_core/wire.py`
- `core/tests/test_fargate_engine.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 18 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*