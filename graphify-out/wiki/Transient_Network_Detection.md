# Transient Network Detection

> 28 nodes · cohesion 0.15

## Key Concepts

- **_is_transient_network()** (27 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_transient_network.py** (26 connections) — `engines/novaact/tests/test_transient_network.py`
- **_client_error()** (9 connections) — `engines/novaact/tests/test_transient_network.py`
- **_target_closed()** (4 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_agentcore_permanent_wrapping_chain_not_transient()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_agentcore_startfailed_wrapping_chain_is_transient()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_client_error_5xx_status_is_transient()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_client_error_throttling_is_transient()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_client_error_transient_code_is_transient()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_client_error_validation_is_permanent()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_connecting_flag_does_not_widen_permanent_errors()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_target_closed_by_name_fallback_hits_inside_chain()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_target_closed_not_transient_by_default()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_target_closed_transient_only_when_connecting()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_target_closed_wrapped_chain_transient_when_connecting()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_connect_read_timeout_are_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_connection_error_is_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_eai_again_in_context_chain()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_gaierror_eai_again_is_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_gaierror_eai_noname_is_permanent()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_gaierror_no_args_is_permanent()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_ssl_error_is_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_timeout_is_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_transient_in_cause_chain()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- *... and 3 more nodes in this community*

## Relationships

- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (6 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [Step Dispatch & Voting](Step_Dispatch_%26_Voting.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_transient_network.py`

## Audit Trail

- EXTRACTED: 65 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*