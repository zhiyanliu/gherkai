"""`gherkai_runtime.names` 的 Device Farm 命名（ADR 0051 决策 10「区域、项目与权限」、ADR 0033 资源清单第 11 条与 task role 权限表）。

这批命名是部署侧几处共用的硬契约：deploy 按项目名找回或建立项目，stack 校验经 context 传入的项目 ARN、按它拼 task role 的会话资源，
提交侧与 doctor 读同一个 SSM 键。断言落在三件事上：项目名与区域是同一个值；项目 ARN 的形态校验对正反例都判对；会话前缀的账户段与
项目 id 段取自项目 ARN 本身、区域段恒为 Device Farm 唯一的区域——资源少一段或区域跟着后端走，策略模拟器会判允许，真实角色却被拒。
"""
from __future__ import annotations

from fnmatch import fnmatchcase

import pytest

from gherkai_runtime import names

PROJECT_ID = "8f2c1a7e-3b4d-4c5e-9f60-7a8b9c0d1e2f"
ARN = f"arn:aws:devicefarm:us-west-2:111122223333:project:{PROJECT_ID}"


# ---- 项目名与区域 ----
def test_project_name_is_prefix_plus_base():
    assert names.BASE_DEVICE_FARM_PROJECT == "devices"
    assert names.default_name("gherkai-", names.BASE_DEVICE_FARM_PROJECT) == "gherkai-devices"
    assert names.default_name("prod-", names.BASE_DEVICE_FARM_PROJECT) == "prod-devices"


def test_region_is_the_only_device_farm_region():
    assert names.DEVICE_FARM_REGION == "us-west-2"


def test_ssm_key_lives_under_backend_prefix():
    assert names.ssm_path("gherkai-", names.DEVICE_FARM_PROJECT_KEY) == "/gherkai-backend/device-farm-project"


# ---- 「待建立」占位值 ----
def test_pending_placeholder_is_plainly_not_an_arn():
    """占位值经 cdk 的 `-c device_farm_project=<值>` 传给 stack：必须一眼看出不是 ARN、过不了形态校验，且不含空白与 `=`。"""
    value = names.DEVICE_FARM_PROJECT_PENDING
    assert isinstance(value, str) and value
    assert not value.startswith("arn:")
    assert not any(c.isspace() for c in value) and "=" not in value
    with pytest.raises(ValueError):
        names.validate_device_farm_project_arn(value)


# ---- 项目 ARN 形态校验 ----
@pytest.mark.parametrize("arn", [
    ARN,
    "arn:aws:devicefarm:us-west-2:999999999999:project:p-1",
])
def test_validate_accepts_project_arn_in_device_farm_region(arn):
    assert names.validate_device_farm_project_arn(arn) == arn


@pytest.mark.parametrize("arn", [
    f"arn:aws:devicefarm:us-east-1:111122223333:project:{PROJECT_ID}",      # 区域不是 Device Farm 的区域
    f"arn:aws-cn:devicefarm:us-west-2:111122223333:project:{PROJECT_ID}",   # 分区不对
    f"arn:aws:ecs:us-west-2:111122223333:project:{PROJECT_ID}",             # 服务不对
    f"arn:aws:devicefarm:us-west-2:111122223333:session:{PROJECT_ID}/s/00000",  # 会话 ARN
    "arn:aws:devicefarm:us-west-2::device:ABCDEF0123456789",                 # 设备 ARN（账户段为空）
    f"arn:aws:devicefarm:us-west-2:111122223333:devicepool:{PROJECT_ID}/p",  # 设备池 ARN
    f"arn:aws:devicefarm:us-west-2:11112222333:project:{PROJECT_ID}",       # 账户 11 位
    f"arn:aws:devicefarm:us-west-2:1111222233334:project:{PROJECT_ID}",     # 账户 13 位
    f"arn:aws:devicefarm:us-west-2:11112222333x:project:{PROJECT_ID}",      # 账户含字母
    f"arn:aws:devicefarm:us-west-2:{chr(0x0661) * 12}:project:{PROJECT_ID}",  # 账户是非 ASCII 数字
    "arn:aws:devicefarm:us-west-2:111122223333:project:",                    # 项目 id 为空
    "arn:aws:devicefarm:us-west-2:111122223333:project:a/b",                 # 项目 id 含 `/`：拼出的会话前缀会错位
    "arn:aws:devicefarm:us-west-2:111122223333:project:a:b",                 # 项目 id 含 `:`
    "arn:aws:devicefarm:us-west-2:111122223333:project:*",                   # 项目 id 是 IAM 通配：会话授权会扩到本账户全部项目
    "arn:aws:devicefarm:us-west-2:111122223333:project:a?b",                 # 项目 id 含 IAM 单字符通配
    f" {ARN}",                                                               # 首尾空白
    f"{ARN}\n",
    "",
])
def test_validate_rejects_other_shapes(arn):
    with pytest.raises(ValueError) as e:
        names.validate_device_farm_project_arn(arn)
    msg = str(e.value)
    assert repr(arn) in msg                                     # 点名收到的值
    assert "arn:aws:devicefarm:us-west-2:" in msg               # 给出应有的形态


# ---- 项目 id 与会话前缀 ----
def test_project_id_is_the_resource_segment():
    assert names.device_farm_project_id(ARN) == PROJECT_ID


def test_session_prefix_takes_account_and_project_id_from_project_arn():
    assert names.device_farm_session_arn_prefix(ARN) == (
        f"arn:aws:devicefarm:us-west-2:111122223333:session:{PROJECT_ID}/*")
    # 账户段跟着项目 ARN 走，不是写死的某个账户
    other = "arn:aws:devicefarm:us-west-2:444455556666:project:p-2"
    assert names.device_farm_session_arn_prefix(other) == "arn:aws:devicefarm:us-west-2:444455556666:session:p-2/*"


def test_session_prefix_covers_own_sessions_only():
    """IAM 的 `*` 跨 `/` 匹配（fnmatch 同义）：本项目的会话命中，同账户别的项目、别的账户同 id 的项目都不命中。"""
    pattern = names.device_farm_session_arn_prefix(ARN)
    own = f"arn:aws:devicefarm:us-west-2:111122223333:session:{PROJECT_ID}/0a1b2c3d-0000-4000-8000-000000000001/00000"
    other_project = "arn:aws:devicefarm:us-west-2:111122223333:session:p-other/0a1b2c3d/00000"
    other_account = f"arn:aws:devicefarm:us-west-2:444455556666:session:{PROJECT_ID}/0a1b2c3d/00000"
    assert fnmatchcase(own, pattern)
    assert not fnmatchcase(other_project, pattern)
    assert not fnmatchcase(other_account, pattern)


@pytest.mark.parametrize("fn", [names.device_farm_project_id, names.device_farm_session_arn_prefix])
@pytest.mark.parametrize("bad", [
    f"arn:aws:devicefarm:us-east-1:111122223333:project:{PROJECT_ID}",
    "arn:aws:devicefarm:us-west-2:111122223333:project:a/b",
    "arn:aws:devicefarm:us-west-2:111122223333:project:*",
    names.DEVICE_FARM_PROJECT_PENDING,
])
def test_derivations_refuse_malformed_arn(fn, bad):
    """形态不对时抛 ValueError、不拼出半对的结果：错的会话前缀只会在运行期表现为 AccessDenied。"""
    with pytest.raises(ValueError):
        fn(bad)
