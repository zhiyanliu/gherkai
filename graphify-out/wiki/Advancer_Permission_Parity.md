# Advancer Permission Parity

> 5 nodes · cohesion 0.40

## Key Concepts

- **_advancer_stmts()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **test_reconciler_and_kicker_have_the_same_permission_face()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **Template** (2 connections)
- **某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…** (1 connections) — `deploy_aws/tests/test_stack.py`
- **两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…** (1 connections) — `deploy_aws/tests/test_stack.py`

## Relationships

- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (4 shared connections)

## Source Files

- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*