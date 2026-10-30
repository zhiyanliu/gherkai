"""`gherkai_deploy_aws.names` 的 Device Farm 与安装包命名：re-export 与产品本体是同一个对象，SSM 便捷路径与提交侧、doctor 读的是同一个键。

stack 与 provider 只经本模块取命名（`cli.py` 不能 import `stack.py`，两侧唯一的共同 import 是它），re-export 漏一项就会逼调用点写裸
字面量或绕道另一个模块；便捷路径若自己拼一遍，stack 写的参数与提交侧读的参数就可能对不上（ADR 0038「SSM 参数与命名真源」、
ADR 0051 决策 9 与决策 10）。
"""
from __future__ import annotations

import pytest

from gherkai_runtime import names as runtime_names

from gherkai_deploy_aws import names


@pytest.mark.parametrize("attr", [
    "BASE_DEVICE_FARM_PROJECT",
    "DEVICE_FARM_PROJECT_KEY",
    "DEVICE_FARM_REGION",
    "DEVICE_FARM_PROJECT_PENDING",
    "validate_device_farm_project_arn",
    "device_farm_project_id",
    "device_farm_session_arn_prefix",
    "APP_OBJECT_PREFIX",
    "APP_OBJECT_TAG",
    "APP_OBJECT_EXPIRE_DAYS",
    "APP_OBJECT_RETAIN_DAYS",
])
def test_device_farm_and_app_names_are_reexported_from_runtime(attr):
    assert getattr(names, attr) is getattr(runtime_names, attr)


def test_ssm_device_farm_project_path_is_the_shared_key():
    for prefix in ("gherkai-", "prod-"):
        assert names.ssm_device_farm_project_path(prefix) == runtime_names.ssm_path(
            prefix, runtime_names.DEVICE_FARM_PROJECT_KEY)
    assert names.ssm_device_farm_project_path("gherkai-") == "/gherkai-backend/device-farm-project"
