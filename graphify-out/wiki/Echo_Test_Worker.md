# Echo Test Worker

> 5 nodes · cohesion 0.60

## Key Concepts

- **echo_worker.py** (4 connections) — `core/tests/fixtures/echo_worker.py`
- **main()** (3 connections) — `core/tests/fixtures/echo_worker.py`
- **emit()** (2 connections) — `core/tests/fixtures/echo_worker.py`
- **_on_sigterm()** (2 connections) — `core/tests/fixtures/echo_worker.py`
- **测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…** (1 connections) — `core/tests/fixtures/echo_worker.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `core/tests/fixtures/echo_worker.py`

## Audit Trail

- EXTRACTED: 5 (83%)
- INFERRED: 1 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*