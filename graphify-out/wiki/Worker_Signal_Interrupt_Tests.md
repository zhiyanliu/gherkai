# Worker Signal Interrupt Tests

> 10 nodes · cohesion 0.24

## Key Concepts

- **_spawn_and_wait_ready()** (5 connections) — `engines/novaact/tests/test_interrupt_process.py`
- **test_interrupt_process.py** (4 connections) — `engines/novaact/tests/test_interrupt_process.py`
- **test_worker_cooperative_stop_on_signal()** (4 connections) — `engines/novaact/tests/test_interrupt_process.py`
- **test_worker_runs_until_signaled()** (3 connections) — `engines/novaact/tests/test_interrupt_process.py`
- **parametrize** (1 connections)
- **Popen** (1 connections)
- **进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…** (1 connections) — `engines/novaact/tests/test_interrupt_process.py`
- **spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。** (1 connections) — `engines/novaact/tests/test_interrupt_process.py`
- **真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。** (1 connections) — `engines/novaact/tests/test_interrupt_process.py`
- **反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。** (1 connections) — `engines/novaact/tests/test_interrupt_process.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `engines/novaact/tests/test_interrupt_process.py`

## Audit Trail

- EXTRACTED: 11 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*