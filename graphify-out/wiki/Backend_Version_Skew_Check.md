# Backend Version Skew Check

> 16 nodes · cohesion 0.15

## Key Concepts

- **_StampSsm** (14 connections) — `runtime/tests/test_compose.py`
- **_client_error()** (5 connections) — `runtime/tests/test_compose.py`
- **test_check_backend_skew_propagates_read_errors()** (5 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_missing_parameter_is_none_not_raise()** (5 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_other_aws_error_propagates()** (5 connections) — `runtime/tests/test_compose.py`
- **test_check_backend_skew_missing_stamp_warns_not_raises()** (4 connections) — `runtime/tests/test_compose.py`
- **test_check_backend_skew_reads_stamp_then_judges()** (4 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_blank_value_is_none()** (3 connections) — `runtime/tests/test_compose.py`
- **test_read_backend_version_reads_prefixed_path()** (3 connections) — `runtime/tests/test_compose.py`
- **假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。** (1 connections) — `runtime/tests/test_compose.py`
- **`ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。** (1 connections) — `runtime/tests/test_compose.py`
- **凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。** (1 connections) — `runtime/tests/test_compose.py`
- **读戳 + 判定一步到位（编排住产品本体，入口前端只翻退出码）。** (1 connections) — `runtime/tests/test_compose.py`
- **凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到不等于放过。** (1 connections) — `runtime/tests/test_compose.py`
- **.get_parameter()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (9 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (1 shared connections)

## Source Files

- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 34 (92%)
- INFERRED: 3 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*