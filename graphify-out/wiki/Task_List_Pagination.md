# Task List Pagination

> 6 nodes · cohesion 0.33

## Key Concepts

- **test_handle_timeout_finds_stopped_target_on_second_page()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_pages_task_lists_and_batches_describe()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_stopped_filler()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。 ECS…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **目标落在 STOPPED 列表第二页、且没有退出记录 → 仍按 DescribeTasks 落它的真退出码，不臆造超时。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (3 shared connections)
- [ECS Timeout Handling Tests](ECS_Timeout_Handling_Tests.md) (2 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*