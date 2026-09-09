# Transient Error Classification

> 32 nodes · cohesion 0.12

## Key Concepts

- **_is_transient_network()** (27 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_transient_network.py** (26 connections) — `engines/novaact/tests/test_transient_network.py`
- **_client_error()** (9 connections) — `engines/novaact/tests/test_transient_network.py`
- **_is_transient_client_error()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_target_closed()** (4 connections) — `engines/novaact/tests/test_transient_network.py`
- **BaseException** (3 connections)
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
- **test_value_error_not_transient()** (3 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_connect_read_timeout_are_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_connection_error_is_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_eai_again_in_context_chain()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_gaierror_eai_again_is_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_gaierror_eai_noname_is_permanent()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_gaierror_no_args_is_permanent()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- **test_ssl_error_is_transient()** (2 connections) — `engines/novaact/tests/test_transient_network.py`
- *... and 7 more nodes in this community*

## Relationships

- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (5 shared connections)
- [Step Dispatch & Error Mapping](Step_Dispatch_%26_Error_Mapping.md) (2 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_transient_network.py`

## Audit Trail

- EXTRACTED: 69 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*