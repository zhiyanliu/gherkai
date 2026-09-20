# Worker Main Fakes

> 30 nodes · cohesion 0.08

## Key Concepts

- **_RecUploader** (12 connections) — `engines/novaact/tests/test_evidence.py`
- **_FakeNovaAct** (8 connections) — `engines/novaact/tests/test_evidence.py`
- **test_exception_path_drains_and_still_raises()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **test_stop_signal_path_drains_after_session_release()** (6 connections) — `engines/novaact/tests/test_evidence.py`
- **_FakeCdp** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **_install_provider()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **main_fakes()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **test_scope_end_drains_before_flush()** (5 connections) — `engines/novaact/tests/test_evidence.py`
- **test_drain_logs_one_line_when_not_fully_drained()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_drain_timeout_before_flush_promises_flush_not_broken_links()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **test_network_exhausted_path_drains()** (4 connections) — `engines/novaact/tests/test_evidence.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_evidence.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_evidence.py`
- **.__enter__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__exit__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__enter__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.__exit__()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **.get_session_id()** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **正常完成：先有界排空队列（30s）、再整目录 flush（flush 只兜漏网的）。顺序反了就等于没有队列。** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **协作停：三层 with 已退出（会话已释放）之后才排空，用退出段预算；不 flush（中断产物留本地）。 会话释放的两个 __exit__ 也进同一条…** (1 connections) — `engines/novaact/tests/test_evidence.py`
- *... and 5 more nodes in this community*

## Relationships

- [Evidence Artifact Upload](Evidence_Artifact_Upload.md) (12 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (6 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (1 shared connections)

## Source Files

- `engines/novaact/tests/test_evidence.py`

## Audit Trail

- EXTRACTED: 52 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*