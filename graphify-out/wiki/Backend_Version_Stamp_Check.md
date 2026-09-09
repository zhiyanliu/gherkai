# Backend Version Stamp Check

> 20 nodes · cohesion 0.15

## Key Concepts

- **_StampSsm** (12 connections) — `runtime/tests/test_compose.py`
- **read_backend_version()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **check_backend_skew()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_client_error()** (5 connections) — `runtime/tests/test_compose.py`
- **test_check_backend_skew_propagates_read_errors()** (5 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_missing_parameter_is_none_not_raise()** (5 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_other_aws_error_propagates()** (5 connections) — `runtime/tests/test_compose.py`
- **test_check_backend_skew_missing_stamp_warns_not_raises()** (4 connections) — `runtime/tests/test_compose.py`
- **test_check_backend_skew_reads_stamp_then_judges()** (4 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_blank_value_is_none()** (3 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_reads_prefixed_path()** (3 connections) — `runtime/tests/test_compose.py`
- **读后端版本戳 SSM 参数（`ssm_path(prefix, "version")`，由 stack 资源随部署事务写入，ADR 0037 决策 6）。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。** (1 connections) — `runtime/tests/test_compose.py`
- **读戳 + 判定一步到位（编排住产品本体，入口皮只翻退出码）。** (1 connections) — `runtime/tests/test_compose.py`
- **凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到≠放过。** (1 connections) — `runtime/tests/test_compose.py`
- **假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。** (1 connections) — `runtime/tests/test_compose.py`
- **`ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。** (1 connections) — `runtime/tests/test_compose.py`
- **.get_parameter()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Worker Command Resolution](Worker_Command_Resolution.md) (9 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (4 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (1 shared connections)
- [Feature Planning to Jobs](Feature_Planning_to_Jobs.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 42 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*