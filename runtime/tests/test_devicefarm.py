"""Python 侧 Device Farm 客户端的行为（ADR 0051 决策 10「项目」「调用归属」、决策 6 的 doctor 列出未结束会话）。

用 botocore Stubber 包住真 devicefarm / ssm 客户端，按服务模型核对请求参数与响应形态，不连真 AWS。断言落在 ADR 定下的分支上：
- SSM 有值且 GetProject 成功时直接沿用，不按名列举；
- 没有 SSM 值、或 SSM 值指向的项目已被删除（NotFound，先经回调发出警告、之后无论列举或建立怎样失败都不丢）时按名称
  `{prefix}devices` 翻页列举：零个就建立、一个就复用、多个抛专用异常；
- 无权限单独分类成一种异常（deploy 据此降级），记录的项目已不存在、随后列举或建立又被拒时异常带 `stored_project_missing` 标记；
  限流、网络等其他错误原样抛出，不被当成「项目不存在」去新建；
- diff 用的只读核对只调 GetProject：成功为 True、NotFound 为 False，不列举、不建立；无权限与其他错误的分类同上；
- 客户端区域恒为 Device Farm 唯一的区域，与后端区域（环境变量或 profile 给的）无关；
- 列会话过滤掉 COMPLETED、保留排队中的各状态，且本模块不创建、不停止会话。
真实错误码经受限角色实测为 AccessDeniedException、真实会话状态取值（PREPARING 等）经真会话核过（ADR 0051 实测依据），Stubber 只能核形态。
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from botocore.stub import Stubber

from gherkai_runtime import devicefarm, names

PREFIX = "gherkai-"
NAME = "gherkai-devices"
ACCOUNT = "111122223333"
STORED = f"arn:aws:devicefarm:us-west-2:{ACCOUNT}:project:stored-0000"
FOUND = f"arn:aws:devicefarm:us-west-2:{ACCOUNT}:project:found-1111"
FOUND_2 = f"arn:aws:devicefarm:us-west-2:{ACCOUNT}:project:found-2222"
OTHER = f"arn:aws:devicefarm:us-west-2:{ACCOUNT}:project:other-9999"
CREATED = f"arn:aws:devicefarm:us-west-2:{ACCOUNT}:project:created-3333"
T0 = datetime(2026, 10, 29, 8, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _isolated_aws_env(tmp_path, monkeypatch):
    """不读本机的 AWS 配置与凭证：假凭证、空配置文件，后端区域给 us-east-1（用来反证客户端没有跟着后端区域走）。"""
    config = tmp_path / "aws-config"
    config.write_text("[profile backend]\nregion = us-east-1\n", encoding="utf-8")
    creds = tmp_path / "aws-credentials"
    creds.write_text("[backend]\naws_access_key_id = AKIDEXAMPLE\naws_secret_access_key = secret\n", encoding="utf-8")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(creds))
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIDEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    for var in ("AWS_PROFILE", "AWS_DEFAULT_PROFILE", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def df(monkeypatch):
    """真 devicefarm 客户端外包 Stubber，并替换模块的客户端工厂；记录工厂收到的 profile。"""
    client = devicefarm._make_devicefarm_client(profile=None)
    stubber = Stubber(client)
    profiles: list = []

    def _factory(*, profile):
        profiles.append(profile)
        return client

    monkeypatch.setattr(devicefarm, "_make_devicefarm_client", _factory)
    with stubber:
        yield stubber, profiles
        stubber.assert_no_pending_responses()


def _project(arn: str, name: str) -> dict:
    return {"arn": arn, "name": name}


def _stub_list_pages(stubber: Stubber, pages: list[list[dict]]) -> None:
    """按页排 ListProjects 响应：除末页外都带 nextToken，并核对第二页起请求带上了上一页的 token。"""
    for i, projects in enumerate(pages):
        resp: dict = {"projects": projects}
        if i < len(pages) - 1:
            resp["nextToken"] = f"token-{i + 1}"
        stubber.add_response("list_projects", resp, {} if i == 0 else {"nextToken": f"token-{i}"})


def _stub_get_not_found(stubber: Stubber, arn: str) -> None:
    stubber.add_client_error("get_project", service_error_code="NotFoundException", service_message="not found",
                             http_status_code=404, expected_params={"arn": arn})


# ---- 项目：SSM 有值且核对成功 ----
def test_stored_arn_verified_by_get_project_is_reused_without_listing(df):
    stubber, profiles = df
    stubber.add_response("get_project", {"project": _project(STORED, NAME)}, {"arn": STORED})
    res = devicefarm.resolve_or_create_project(PREFIX, profile="backend", stored_arn=STORED)
    assert res == devicefarm.ProjectResolution(arn=STORED, source="ssm")
    assert profiles == ["backend"]   # 凭证沿用调用方的 profile


# ---- 项目：按名翻页列举，零 / 一 / 多三种结果；没有 SSM 值与 SSM 值已失效两种入口 ----
ENTRIES = ["no-stored-arn", "stored-arn-not-found"]


def _enter(stubber: Stubber, entry: str) -> str | None:
    if entry == "stored-arn-not-found":
        _stub_get_not_found(stubber, STORED)
        return STORED
    return None


def _assert_warning(warnings: list[str], entry: str) -> None:
    """SSM 值已失效时恰发出一句警告（点名旧 ARN 与要找的名称）；没有 SSM 值时一句都不发。"""
    if entry == "stored-arn-not-found":
        assert len(warnings) == 1 and STORED in warnings[0] and NAME in warnings[0]
    else:
        assert warnings == []


@pytest.mark.parametrize("entry", ENTRIES)
def test_single_name_match_across_pages_is_reused(df, entry):
    stubber, _ = df
    stored = _enter(stubber, entry)
    _stub_list_pages(stubber, [[_project(OTHER, "someone-else")], [_project(OTHER, "gherkai-devices-old"),
                                                                    _project(FOUND, NAME)]])
    warnings: list[str] = []
    res = devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=stored, warn=warnings.append)
    assert (res.arn, res.source) == (FOUND, "found")
    _assert_warning(warnings, entry)


@pytest.mark.parametrize("entry", ENTRIES)
def test_no_name_match_across_pages_creates_project_with_prefixed_name(df, entry):
    stubber, _ = df
    stored = _enter(stubber, entry)
    _stub_list_pages(stubber, [[_project(OTHER, "someone-else")], [], [_project(OTHER, "prod-devices")]])
    stubber.add_response("create_project", {"project": _project(CREATED, NAME)}, {"name": NAME})
    warnings: list[str] = []
    res = devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=stored, warn=warnings.append)
    assert (res.arn, res.source) == (CREATED, "created")
    _assert_warning(warnings, entry)


@pytest.mark.parametrize("entry", ENTRIES)
def test_several_name_matches_across_pages_raise_ambiguous_without_creating(df, entry):
    stubber, _ = df
    stored = _enter(stubber, entry)
    _stub_list_pages(stubber, [[_project(FOUND, NAME)], [_project(OTHER, "someone-else"), _project(FOUND_2, NAME)]])
    warnings: list[str] = []
    with pytest.raises(devicefarm.AmbiguousProject) as ei:
        devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=stored, warn=warnings.append)
    _assert_warning(warnings, entry)   # 「记录的项目已不存在」这一事实在同名歧义之前就已发出
    assert ei.value.name == NAME
    assert ei.value.arns == [FOUND, FOUND_2]
    assert FOUND in str(ei.value) and FOUND_2 in str(ei.value)   # 消息即给使用方看的整句：点名每个同名项目


def test_project_name_follows_prefix(df):
    stubber, _ = df
    _stub_list_pages(stubber, [[_project(OTHER, NAME)]])
    stubber.add_response("create_project", {"project": _project(CREATED, "prod-devices")}, {"name": "prod-devices"})
    res = devicefarm.resolve_or_create_project("prod-", profile=None, stored_arn=None)
    assert res.arn == CREATED
    assert devicefarm.project_name("prod-") == names.default_name("prod-", names.BASE_DEVICE_FARM_PROJECT)


def test_not_found_warning_is_emitted_before_listing_fails(df):
    """SSM 值已失效、随后列举被限流：警告在核对出 NotFound 时已经发出，异常照常抛出——事实不随后续失败丢失。"""
    stubber, _ = df
    _stub_get_not_found(stubber, STORED)
    stubber.add_client_error("list_projects", service_error_code="ThrottlingException", http_status_code=400,
                             expected_params={})
    warnings: list[str] = []
    with pytest.raises(ClientError):
        devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=STORED, warn=warnings.append)
    assert len(warnings) == 1 and STORED in warnings[0]


# ---- 项目：无权限单独分类；其他错误原样抛出、不猜测 ----
DENIED_CODES = ["AccessDeniedException", "AccessDenied", "NotAuthorized", "UnauthorizedOperation"]


@pytest.mark.parametrize("code", DENIED_CODES)
@pytest.mark.parametrize("stage", ["get_project", "list_projects", "create_project"])
def test_access_denied_on_any_project_call_is_classified(df, stage, code):
    stubber, _ = df
    stored = STORED if stage == "get_project" else None
    if stage == "create_project":
        _stub_list_pages(stubber, [[]])
    params = {"get_project": {"arn": STORED}, "list_projects": {}, "create_project": {"name": NAME}}[stage]
    stubber.add_client_error(stage, service_error_code=code, service_message="not authorized", http_status_code=403,
                             expected_params=params)
    with pytest.raises(devicefarm.DeviceFarmAccessDenied) as ei:
        devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=stored)
    assert ei.value.code == code
    assert ei.value.operation == {"get_project": "GetProject", "list_projects": "ListProjects", "create_project": "CreateProject"}[stage]
    assert isinstance(ei.value.__cause__, ClientError)
    assert ei.value.stored_project_missing is False  # 记录核对被拒、或根本没有记录：不是「记录已失效」


@pytest.mark.parametrize("code", DENIED_CODES)
@pytest.mark.parametrize("stage", ["list_projects", "create_project"])
def test_access_denied_after_the_stored_project_vanished_is_flagged(df, stage, code):
    """SSM 记录的项目已核对为不存在（NotFound）、随后按名称列举或建立被拒：异常带 `stored_project_missing=True`，
    deploy 据此视同没有记录（不把已不存在的 ARN 写回 SSM、不给不存在的项目授权），而不是沿用记录。"""
    stubber, _ = df
    _stub_get_not_found(stubber, STORED)
    if stage == "create_project":
        _stub_list_pages(stubber, [[]])
    params = {"list_projects": {}, "create_project": {"name": NAME}}[stage]
    stubber.add_client_error(stage, service_error_code=code, service_message="not authorized", http_status_code=403,
                             expected_params=params)
    with pytest.raises(devicefarm.DeviceFarmAccessDenied) as ei:
        devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=STORED)
    assert ei.value.stored_project_missing is True
    assert ei.value.operation == {"list_projects": "ListProjects", "create_project": "CreateProject"}[stage]


@pytest.mark.parametrize("code", ["ThrottlingException", "LimitExceededException", "ServiceAccountException",
                                  "ArgumentException"])
def test_other_errors_on_get_project_propagate_without_listing(df, code):
    """GetProject 的非 NotFound 错误不转入按名列举：限流或服务端故障被当成「项目不存在」会多建一个项目。"""
    stubber, _ = df
    stubber.add_client_error("get_project", service_error_code=code, http_status_code=400,
                             expected_params={"arn": STORED})
    with pytest.raises(ClientError) as ei:
        devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=STORED)
    assert not isinstance(ei.value, devicefarm.DeviceFarmAccessDenied)
    assert ei.value.response["Error"]["Code"] == code


@pytest.mark.parametrize("stage", ["list_projects", "create_project"])
def test_throttling_on_list_or_create_propagates(df, stage):
    stubber, _ = df
    if stage == "create_project":
        _stub_list_pages(stubber, [[]])
    stubber.add_client_error(stage, service_error_code="ThrottlingException", http_status_code=400,
                             expected_params={"list_projects": {}, "create_project": {"name": NAME}}[stage])
    with pytest.raises(ClientError) as ei:
        devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=None)
    assert ei.value.response["Error"]["Code"] == "ThrottlingException"


class _UnreachableClient:
    """网络故障：botocore 抛的不是 ClientError，Stubber 排不出这种失败，故用假客户端。"""

    def get_project(self, **kw):
        raise EndpointConnectionError(endpoint_url="https://devicefarm.us-west-2.amazonaws.com/")

    def get_paginator(self, name):  # pragma: no cover - 走到这里即说明网络故障被当成了「项目不存在」
        raise AssertionError("网络故障不应转入按名列举")


def test_network_error_propagates_without_listing(monkeypatch):
    monkeypatch.setattr(devicefarm, "_make_devicefarm_client", lambda *, profile: _UnreachableClient())
    with pytest.raises(EndpointConnectionError):
        devicefarm.resolve_or_create_project(PREFIX, profile=None, stored_arn=STORED)


# ---- diff 的只读核对：只调 GetProject，不列举、不建立 ----
def test_verify_project_existing_project_is_true(df):
    stubber, profiles = df
    stubber.add_response("get_project", {"project": _project(STORED, NAME)}, {"arn": STORED})
    assert devicefarm.verify_project(STORED, profile="backend") is True
    assert profiles == ["backend"]   # 凭证沿用调用方的 profile


def test_verify_project_not_found_is_false_without_listing_or_creating(df):
    """项目已被手动删除：返回 False 交给调用方处置。Stubber 只排了 GetProject，任何列举或建立的调用都会因没有排好的响应而失败。"""
    stubber, _ = df
    _stub_get_not_found(stubber, STORED)
    assert devicefarm.verify_project(STORED, profile=None) is False


@pytest.mark.parametrize("code", DENIED_CODES)
def test_verify_project_access_denied_is_classified(df, code):
    stubber, _ = df
    stubber.add_client_error("get_project", service_error_code=code, service_message="not authorized", http_status_code=403,
                             expected_params={"arn": STORED})
    with pytest.raises(devicefarm.DeviceFarmAccessDenied) as ei:
        devicefarm.verify_project(STORED, profile=None)
    assert (ei.value.operation, ei.value.code) == ("GetProject", code)
    assert isinstance(ei.value.__cause__, ClientError)


@pytest.mark.parametrize("code", ["ThrottlingException", "LimitExceededException", "ServiceAccountException",
                                  "ArgumentException"])
def test_verify_project_other_client_errors_propagate_unchanged(df, code):
    """非 NotFound、非无权限的错误原样抛出：既不当成「项目不存在」，也不当成无权限。"""
    stubber, _ = df
    stubber.add_client_error("get_project", service_error_code=code, http_status_code=400, expected_params={"arn": STORED})
    with pytest.raises(ClientError) as ei:
        devicefarm.verify_project(STORED, profile=None)
    assert not isinstance(ei.value, devicefarm.DeviceFarmAccessDenied)
    assert ei.value.response["Error"]["Code"] == code


def test_verify_project_network_error_propagates(monkeypatch):
    monkeypatch.setattr(devicefarm, "_make_devicefarm_client", lambda *, profile: _UnreachableClient())
    with pytest.raises(EndpointConnectionError):
        devicefarm.verify_project(STORED, profile=None)


# ---- 客户端区域恒为 Device Farm 的区域 ----
@pytest.mark.parametrize("profile", [None, "backend"])
def test_client_region_is_device_farm_region_regardless_of_backend_region(profile):
    """环境变量与 profile 都把后端区域给成 us-east-1，客户端仍落在 us-west-2。"""
    client = devicefarm._make_devicefarm_client(profile=profile)
    assert client.meta.region_name == names.DEVICE_FARM_REGION == "us-west-2"
    assert "us-west-2" in client.meta.endpoint_url and "us-east-1" not in client.meta.endpoint_url


# ---- doctor 列出未结束的会话 ----
def _session(arn_tail: str, status: str, name: str | None = "gherkai:r1:ab12:1:login") -> dict:
    s = {"arn": f"arn:aws:devicefarm:us-west-2:{ACCOUNT}:session:found-1111/{arn_tail}/00000", "status": status, "created": T0}
    if name is not None:
        s["name"] = name
    return s


def test_list_open_sessions_drops_completed_and_keeps_queued_states(df):
    stubber, profiles = df
    page1 = [_session("s1", "PENDING"), _session("s2", "COMPLETED"), _session("s3", "PENDING_CONCURRENCY")]
    page2 = [_session("s4", "RUNNING"), _session("s5", "COMPLETED"), _session("s6", "PENDING_DEVICE", name=None),
             _session("s7", "STOPPING")]
    stubber.add_response("list_remote_access_sessions", {"remoteAccessSessions": page1, "nextToken": "token-1"}, {"arn": FOUND})
    stubber.add_response("list_remote_access_sessions", {"remoteAccessSessions": page2},
                         {"arn": FOUND, "nextToken": "token-1"})
    sessions = devicefarm.list_open_sessions(FOUND, profile="backend")
    assert [(s.arn.split("/")[1], s.status) for s in sessions] == [
        ("s1", "PENDING"), ("s3", "PENDING_CONCURRENCY"), ("s4", "RUNNING"), ("s6", "PENDING_DEVICE"), ("s7", "STOPPING")]
    first = sessions[0]
    assert first == devicefarm.OpenSession(arn=page1[0]["arn"], name="gherkai:r1:ab12:1:login", status="PENDING", created=T0)
    assert sessions[3].name is None
    assert profiles == ["backend"]


def test_list_open_sessions_empty_project(df):
    stubber, _ = df
    stubber.add_response("list_remote_access_sessions", {"remoteAccessSessions": []}, {"arn": FOUND})
    assert devicefarm.list_open_sessions(FOUND, profile=None) == []


@pytest.mark.parametrize("code", DENIED_CODES)
def test_list_open_sessions_access_denied_is_classified(df, code):
    stubber, _ = df
    stubber.add_client_error("list_remote_access_sessions", service_error_code=code, http_status_code=403,
                             expected_params={"arn": FOUND})
    with pytest.raises(devicefarm.DeviceFarmAccessDenied) as ei:
        devicefarm.list_open_sessions(FOUND, profile=None)
    assert ei.value.code == code
    assert ei.value.operation == "ListRemoteAccessSessions"


def test_list_open_sessions_other_errors_propagate(df):
    stubber, _ = df
    stubber.add_client_error("list_remote_access_sessions", service_error_code="ThrottlingException", http_status_code=400,
                             expected_params={"arn": FOUND})
    with pytest.raises(ClientError) as ei:
        devicefarm.list_open_sessions(FOUND, profile=None)
    assert not isinstance(ei.value, devicefarm.DeviceFarmAccessDenied)


def test_module_never_creates_or_stops_sessions():
    """会话的生命周期只归 worker：本模块只列举，不出现建立或停止会话的调用（ADR 0051 决策 6「不做回收器」）。"""
    tree = ast.parse(Path(devicefarm.__file__).read_text(encoding="utf-8"))
    forbidden = {"create_remote_access_session", "stop_remote_access_session", "delete_remote_access_session",
                 "CreateRemoteAccessSession", "StopRemoteAccessSession", "DeleteRemoteAccessSession"}
    # 属性访问全查（不限于直接调用）：先取属性再经别名调用的写法同样拦住
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    # 字符串常量也查：getattr(client, "...") 与 _make_api_call("...") 这类间接调用不带属性调用的形态；docstring 除外，说明性文字
    # 提到这些动作名不算调用
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                  and node.body and isinstance(node.body[0], ast.Expr)
                  and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)}
    literals = {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings}
    assert not attrs & forbidden
    assert not {lit for lit in literals if any(f in lit for f in forbidden)}


# ---- 从后端区域的 SSM 读项目 ARN ----
@pytest.fixture
def ssm():
    from botocore.session import get_session

    client = get_session().create_client("ssm", region_name="us-east-1")
    with Stubber(client) as stubber:
        yield client, stubber
        stubber.assert_no_pending_responses()


PATH = "/gherkai-backend/device-farm-project"


def test_read_project_arn_returns_stored_value(ssm):
    client, stubber = ssm
    stubber.add_response("get_parameter", {"Parameter": {"Name": PATH, "Value": STORED}}, {"Name": PATH})
    assert devicefarm.read_project_arn(client, PREFIX) == STORED
    assert PATH == names.ssm_path(PREFIX, names.DEVICE_FARM_PROJECT_KEY)


def test_read_project_arn_missing_parameter_is_none(ssm):
    client, stubber = ssm
    stubber.add_client_error("get_parameter", service_error_code="ParameterNotFound", http_status_code=400,
                             expected_params={"Name": PATH})
    assert devicefarm.read_project_arn(client, PREFIX) is None


@pytest.mark.parametrize("code", ["AccessDeniedException", "ThrottlingException"])
def test_read_project_arn_other_errors_propagate(ssm, code):
    """读不到不等于没有：其他错误回落「待建立」会让 diff 把已部署的设备授权显示成删除，由调用方决定退出码（ADR 0051 决策 10）。"""
    client, stubber = ssm
    stubber.add_client_error("get_parameter", service_error_code=code, http_status_code=400, expected_params={"Name": PATH})
    with pytest.raises(ClientError) as ei:
        devicefarm.read_project_arn(client, PREFIX)
    assert ei.value.response["Error"]["Code"] == code
