"""`gherkai_deploy_aws.names` 的 Device Farm、安装包、定义前缀与一次性定时触发的命名：re-export 与产品本体是同一个对象，SSM 便捷路径与提交侧、doctor 读的是同一个键。

stack 与 provider 取命名时经本模块（`cli.py` 不能 import `stack.py`，两侧唯一的共同 import 是它），re-export 漏一项就会逼调用点写裸
字面量或绕道另一个模块。Device Farm 项目名是例外：provider 经 `gherkai_runtime.devicefarm.project_name` 获取，不经本模块。
便捷路径若自己拼一遍，stack 写的参数与提交侧读的参数就可能对不上（ADR 0038「SSM 参数与命名真源」、ADR 0051 决策 9 与决策 10）。
"""
from __future__ import annotations

import pytest

from gherkai_runtime import names as runtime_names

from gherkai_deploy_aws import names


@pytest.mark.parametrize("attr", [
    "DEVICE_FARM_PROJECT_KEY",
    "DEVICE_FARM_REGION",
    "DEVICE_FARM_PROJECT_PENDING",
    "validate_device_farm_project_arn",
    "device_farm_session_arn_prefix",
    "device_farm_interactive_endpoint_resource",
    "APP_OBJECT_PREFIX",
    "APP_OBJECT_TAG",
    "APP_OBJECT_EXPIRE_DAYS",
    "DEFINITIONS_PREFIX",
    # 一次性定时触发的配套（ADR 0033 资源清单 15.）：stack 建 group 与执行角色、拼 IAM 资源域与推进器建触发用的是同一批
    "BASE_SCHEDULE_GROUP",
    "BASE_RUN_TIMER_SCHEDULE",
    "BASE_TIMEOUT_SCHEDULER_ROLE",
    "RUN_TIMER_KINDS",
    "SCHEDULE_NAME_DIGEST_LEN",
    "IAM_ROLE_NAME_MAX_LEN",
    "schedule_group_name",
    "job_timeout_schedule_name",
    "run_timer_schedule_name",
    "timeout_scheduler_role_name",
    "prefix_max_len",
    # kicker 的流过滤按 runs 表的条目与状态分组匹配（ADR 0033 资源清单 13.）：stack 写过滤用的是同一批
    "RUNS_ITEM_TYPE_ATTR",
    "RUNS_STATE_ITEM",
    "STATE_STATUS_GROUP_ATTR",
    "STATUS_GROUP_LIVE",
])
def test_device_farm_and_app_names_are_reexported_from_runtime(attr):
    assert getattr(names, attr) is getattr(runtime_names, attr)


def test_ssm_device_farm_project_path_is_the_shared_key():
    for prefix in ("gherkai-", "prod-"):
        assert names.ssm_device_farm_project_path(prefix) == runtime_names.ssm_path(
            prefix, runtime_names.DEVICE_FARM_PROJECT_KEY)
    assert names.ssm_device_farm_project_path("gherkai-") == "/gherkai-backend/device-farm-project"
