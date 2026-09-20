# Advancer IAM Permissions

> 12 nodes · cohesion 0.17

## Key Concepts

- **_events_table_actions()** (5 connections) — `deploy_aws/tests/test_stack.py`
- **_advancer_stmts()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **test_advancer_events_table_face_is_read_plus_putitem()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **test_exit_observer_can_only_putitem_on_events_table()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **test_reconciler_and_kicker_have_the_same_permission_face()** (4 connections) — `deploy_aws/tests/test_stack.py`
- **Template** (3 connections)
- **parametrize** (1 connections)
- **某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。** (1 connections) — `deploy_aws/tests/test_stack.py`
- **退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…** (1 connections) — `deploy_aws/tests/test_stack.py`
- **两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…** (1 connections) — `deploy_aws/tests/test_stack.py`
- **某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…** (1 connections) — `deploy_aws/tests/test_stack.py`
- **两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…** (1 connections) — `deploy_aws/tests/test_stack.py`

## Relationships

- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (8 shared connections)

## Source Files

- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*