"""`gherkai_runtime.names` 的 worker 镜像交付命名（ADR 0038「tag 命名 = 单一真源、同时是单一校验点」）。

这批命名是**跨包硬契约**：`push-worker` 用它拼推送目标与 SSM 键、提交侧 preflight 与云端推进器用同一函数
反向解析。故断言落在「同一入参恒得同一串」与「非法入参一定抛」两件事上——任一侧单独改算法即两边对不上。
"""
from __future__ import annotations

import pytest

from gherkai_runtime import names


# ---- ecr_repo_name == task_def_name（收拢曾散在 stack.py 注释与推送脚本内联副本里的那条规则）----
def test_ecr_repo_name_is_task_def_name():
    for prefix in ("gherkai-", "prod-", ""):
        for engine in names.ENGINES:
            assert names.ecr_repo_name(prefix, engine) == names.task_def_name(prefix, engine)
    assert names.ecr_repo_name("prod-", "novaact") == "prod-novaact-worker"


# ---- image_tag：PEP 440 归一化（`+` 本地段 / `!` epoch 不在 docker/ECR tag 字符集内）----
def test_image_tag_normalizes_local_version_segment():
    # 实测过的那串：`docker tag` 对带 `+` 的 ref 直接 invalid reference format
    assert names.image_tag("1.4.0.post3.dev0+28c1684", "login") == "1.4.0.post3.dev0.28c1684-login"


def test_image_tag_normalizes_epoch():
    assert names.image_tag("1!2.0", "base") == "1.2.0-base"


def test_image_tag_plain_release():
    assert names.image_tag("1.4.0", "base") == "1.4.0-base"


@pytest.mark.parametrize("variant", [
    "",             # 空
    "-login",       # 首字符非法（`-` 不在首字符集内）
    ".login",       # 同上（`.`）
    "log in",       # 空格
    "log/in",       # `/`（会被 docker 解析成 registry 路径）
    "log:in",       # `:`（tag 分隔符）
    "登录",          # 非 ASCII
])
def test_image_tag_rejects_invalid_variant(variant):
    with pytest.raises(ValueError) as e:
        names.image_tag("1.4.0", variant)
    assert "variant" in str(e.value)  # 报的是 variant 那一层，不是拼出来的 tag


def test_image_tag_rejects_overlong_tag():
    """variant 本身合法但拼出来超 128 字符 → 报 tag 那一层（两类错误分开报，见 names 里两个正则的注释）。"""
    with pytest.raises(ValueError) as e:
        names.image_tag("1.4.0", "v" * 200)
    assert "镜像 tag" in str(e.value)


def test_image_tag_rejects_version_with_illegal_leading_char():
    """版本串首字符非法（归一化只管 `+`/`!`）→ tag 层拒，不静默产出 docker 不认的 ref。"""
    with pytest.raises(ValueError):
        names.image_tag(".1.4.0", "base")


# ---- SSM 键（相对键，全路径 = ssm_path(prefix, key)）----
def test_worker_ssm_keys():
    assert names.WORKER_DEFAULT_KEY == "worker-default"
    assert names.worker_template_key("novaact") == "worker-template/novaact"
    assert names.worker_image_key("midscene", "1.4.0-base") == "worker-image/midscene/1.4.0-base"
    # 全路径落在 ADR 0033 已授的 /{prefix}backend/* 通配内
    assert names.ssm_path("gherkai-", names.worker_image_key("novaact", "1.4.0-login")) == \
        "/gherkai-backend/worker-image/novaact/1.4.0-login"


# ---- 血缘 / 退休 tag 键（承载在 task-def revision 上、不进 SSM）----
def test_lineage_tag_keys():
    assert (names.TAG_VARIANT, names.TAG_VERSION, names.TAG_DIGEST,
            names.TAG_TEMPLATE, names.TAG_RETIRED_AT) == (
        "gherkai:variant", "gherkai:version", "gherkai:digest",
        "gherkai:template", "gherkai:retired-at")


# ---- 跨层对拍：STATE 顶层属性名的写端在 core、读端命名真源在 names（core 不 import 组合根共享层）----
def test_state_worker_task_def_arns_attr_matches_ddb_writer():
    """`names` 的读端常量与 `DynamoDBRunStore` 的写端字面量必须逐字一致（ADR 0038 清理 pass 的安全阀按它查）。

    两处各有字面量是依赖方向逼出来的（core 是窄腰下层、不 import `gherkai_runtime`），本测试是那条注释里
    承诺的护栏——只有 runtime 侧同时看得见两边。
    """
    from gherkai_core.adapters.run_store import ddb

    assert names.STATE_WORKER_TASK_DEF_ARNS_ATTR == ddb._WORKER_TASK_DEF_ARNS_ATTR
