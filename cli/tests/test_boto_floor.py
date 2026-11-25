"""云端提交所需的 boto3 / botocore 下限（理由写在 core/pyproject.toml 的 aws extra 旁）。

建 run 时写 jobs 对象带「键不存在才写」的条件，即 PutObject 的 IfNoneMatch 参数（ADR 0030 决定六「建 run 是条件写」条，
`S3JobsObjects.put`）。botocore 默认在客户端按服务模型校验参数：模型里没有这个参数的版本（1.34 系列即是，1.34.11 与 1.34.131 的
S3 模型核过）在请求发出之前就抛 ParamValidationError。它是 BotoCoreError，`submit` 会把它当成云端不可达，每一次云端提交都失败。

本文件守三件事：几个包声明的同名下限取同一个值；这个值不低于第一个带该参数的版本（按 botocore 的变更记录是 1.35.2，S3 条件写
随它加进服务模型）；当前装上的 botocore 的模型里确有这个参数。下限取哪个版本以变更记录为据，这里只把它固定下来，不证明它。
"""
from __future__ import annotations

import re
import tomllib

import botocore
import botocore.session
from packaging.requirements import Requirement
from packaging.version import Version

from _doc_rules import REPO

_CONDITIONAL_PUT_FLOOR = Version("1.35.2")


def _floor(spec: str) -> Version:
    """一条依赖声明里 `>=` 给出的下限。"""
    bounds = [Version(s.version) for s in Requirement(spec).specifier if s.operator == ">="]
    assert len(bounds) == 1, f"{spec!r} 应恰有一个 >= 下限"
    return bounds[0]


def _declared_floors() -> dict[str, Version]:
    """各处 boto3 / botocore 声明的下限：「文件 · 位置 · 包名」到版本。"""
    def load(rel: str) -> dict:
        return tomllib.loads((REPO / rel).read_text(encoding="utf-8"))

    sites = {
        "core/pyproject.toml · [aws]": load("core/pyproject.toml")["project"]["optional-dependencies"]["aws"],
        "runtime/pyproject.toml · [aws]": (load("runtime/pyproject.toml")["tool"]["hatch"]["metadata"]["hooks"]
                                           ["uv-dynamic-versioning"]["optional-dependencies"]["aws"]),
        "deploy_aws/pyproject.toml · dependencies": (load("deploy_aws/pyproject.toml")["tool"]["hatch"]["metadata"]
                                                     ["hooks"]["uv-dynamic-versioning"]["dependencies"]),
        "pyproject.toml · dev": load("pyproject.toml")["dependency-groups"]["dev"],
    }
    out = {}
    for site, specs in sites.items():
        for spec in specs:
            # 先按名字筛：同一清单里的 `gherkai-core[aws]=={{ version }}` 带构建期才替换的占位符，不是合法的依赖声明
            name = re.match(r"[A-Za-z0-9_.-]+", spec).group()
            if name in ("boto3", "botocore"):
                out[f"{site} · {name}"] = _floor(spec)
    return out


def test_boto_floors_agree_and_cover_conditional_put():
    """几处同名下限取同一个值，且不低于第一个带 PutObject IfNoneMatch 的版本。"""
    floors = _declared_floors()
    expected = {"core/pyproject.toml · [aws] · boto3", "runtime/pyproject.toml · [aws] · boto3",
                "runtime/pyproject.toml · [aws] · botocore", "deploy_aws/pyproject.toml · dependencies · boto3",
                "pyproject.toml · dev · boto3"}
    assert set(floors) == expected, f"声明的位置变了，核对本测试的清单：{sorted(floors)}"
    assert len(set(floors.values())) == 1, f"各处下限不一致：{floors}"
    low = min(floors.values())
    assert low >= _CONDITIONAL_PUT_FLOOR, f"下限 {low} 低于 {_CONDITIONAL_PUT_FLOOR}：更早的 botocore 不认 IfNoneMatch"


def test_installed_botocore_knows_put_object_if_none_match():
    """当前装上的 botocore 不低于声明的下限，它的 S3 模型里 PutObject 有 IfNoneMatch（不建 client、不需要凭证与网络）。"""
    assert Version(botocore.__version__) >= _CONDITIONAL_PUT_FLOOR
    model = botocore.session.get_session().get_service_model("s3")
    assert "IfNoneMatch" in model.operation_model("PutObject").input_shape.members
