"""部署与诊断用的 Device Farm 客户端：`deploy` 找回或建立项目、`diff` 只读核对项目、`doctor` 列出未结束的会话（ADR 0051 决策 10
「调用归属」「项目」、决策 6）。

Python 侧唯一构造 devicefarm 客户端的地方（护栏 `runtime/tests/test_devicefarm_client_placement.py`）：执行期调用 Device Farm 的只有
worker 的设备模块，core 不认识它，推进器不调它。客户端恒用 `names.DEVICE_FARM_REGION`（Device Farm 只在这一个区域提供，是 ADR 0033
「region 全可配」的唯一例外），凭证沿用调用方的 profile；SSM 读仍走调用方按后端区域建的客户端，由调用方注入。

本模块不创建、也不停止远程访问会话：会话的生命周期只归 worker，第二个持有者会与 worker 的收尾竞争（ADR 0051 决策 6「不做回收器」）。

错误分三类交给调用方处置，本模块不决定退出码：
- 无权限（`DeviceFarmAccessDenied`）：deploy 与 diff 据此降级——SSM 已有 ARN 且核对被拒就沿用并警告；没有记录、或记录的项目已核对为
  不存在而找回或新建又被拒（`stored_project_missing`）就警告并按未启用设备支持处理；doctor 单独列一行说明。
- 同名项目不止一个（`AmbiguousProject`）：deploy 不替使用方挑选，以退出码 2 结束。
- 其余 botocore 异常（限流、网络、服务端故障）原样抛出、不猜测：把偶发故障当成「项目不存在」会多建一个项目，当成无权限降级
  会让 stack 撤掉 Midscene 的 Device Farm 授权，而这只有到设备 run 执行时才会暴露。
`DeviceFarmAccessDenied` 与 `AmbiguousProject` 的消息都是给使用方看的整句。

boto3 在函数内延迟导入（`gherkai-runtime[aws]`）：CLI 与 deploy 的 `--help` 不为本模块拉起 AWS SDK。
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, NoReturn

from gherkai_runtime import compose as _compose
from gherkai_runtime import names as _names

ProjectSource = Literal["ssm", "found", "created"]

# 授权失败的错误码。Device Farm 服务模型自己不声明授权错误（IAM 拒绝由 AWS 的公共层返回），这里收 AWS 公共错误表里的
# AccessDeniedException / NotAuthorized，加其他协议服务的写法 AccessDenied（S3、STS 等）与 UnauthorizedOperation（EC2）；部署方没有
# Device Farm 权限时真实账户回 AccessDeniedException（受限角色实测，ADR 0051 实测依据）。provider 读 SSM 记录失败时也用这份集合判定「是否为无权限」（`is_access_denied`）。
_ACCESS_DENIED_CODES = frozenset({"AccessDeniedException", "AccessDenied", "NotAuthorized", "UnauthorizedOperation"})
_NOT_FOUND_CODE = "NotFoundException"
_COMPLETED = "COMPLETED"   # 远程访问会话的终态；其余状态（排队、准备、执行、停止中）都可能还在占用设备


class DeviceFarmAccessDenied(Exception):
    """当前凭证没有调用某个 Device Farm 动作的权限。`operation` 是 API 动作名，`code` 是服务回的错误码；原 ClientError 在 `__cause__`。

    `stored_project_missing` 只由 `resolve_or_create_project` 置真：SSM 记录的项目已核对为不存在，随后按名称列举或建立时被拒。
    调用方据此区分「核对不了、沿用记录」与「记录已失效又无法重建、视同没有记录」（ADR 0051 决策 10 的无权限降级）。
    """

    def __init__(self, operation: str, code: str, *, stored_project_missing: bool = False):
        self.operation = operation
        self.code = code
        self.stored_project_missing = stored_project_missing
        super().__init__(f"当前凭证没有 Device Farm 的 devicefarm:{operation} 权限（{code}）")


class AmbiguousProject(Exception):
    """Device Farm 里有不止一个与部署同名的项目，无从判断该用哪一个。"""

    def __init__(self, name: str, arns: list[str]):
        self.name = name
        self.arns = list(arns)
        listed = "、".join(self.arns)
        super().__init__(
            f"Device Farm（{_names.DEVICE_FARM_REGION}）里有 {len(self.arns)} 个名为 {name} 的项目，无法确定该用哪一个：{listed}。"
            f"请只保留一个同名项目后重试；删除项目会一并删除其中的会话记录与录像，命令为 "
            f"aws devicefarm delete-project --region {_names.DEVICE_FARM_REGION} --arn <项目 ARN>"
        )


@dataclass(frozen=True)
class ProjectResolution:
    """`resolve_or_create_project` 的结果。`source` 说明 ARN 从哪来：`ssm` 沿用 SSM 里核对过的值，`found` 按名称找回，`created` 新建。"""

    arn: str
    source: ProjectSource


@dataclass(frozen=True)
class OpenSession:
    """一个未到 COMPLETED 的远程访问会话（doctor 据此给出控制台链接与停止命令）。`name` 与 `created` 在服务没有返回时为 None。"""

    arn: str
    name: str | None
    status: str
    created: datetime | None


def project_name(prefix: str) -> str:
    """云端 Device Farm 项目名 `{prefix}devices`。"""
    return _names.default_name(prefix, _names.BASE_DEVICE_FARM_PROJECT)


def read_project_arn(ssm_client, prefix: str) -> str | None:
    """从后端区域的 SSM 读项目 ARN（`ssm_path(prefix, DEVICE_FARM_PROJECT_KEY)`，stack 资源写入）。

    参数不存在时返回 None；其余 botocore 异常（无凭证、无权限、网络、限流）原样抛出：读不到不等于没有，回落「待建立」会让 `diff`
    把已部署的设备授权显示成删除，退出码由调用方按 ADR 0051 决策 10 决定。读取规则与提交侧共用 `compose` 里的同一份实现。
    """
    return _compose.read_device_farm_project(prefix=prefix, ssm=ssm_client)


def resolve_or_create_project(prefix: str, *, profile: str | None, stored_arn: str | None,
                              warn: Callable[[str], None] | None = None) -> ProjectResolution:
    """找回或建立项目 `{prefix}devices`（只供 `deploy` 在 cdk 之前调用，ADR 0051 决策 10「项目」）。

    `stored_arn` 是 SSM 里的现值：有值时先 GetProject 核对，成功即沿用；NotFound（项目被手动删除）时先经 `warn` 发出一句给使用方看的
    警告、再转入按名称查找——警告在核对出这一事实时立即发出，之后无论列举被限流、建立失败还是同名歧义，这个事实都不会丢。
    按名称翻页列举 ListProjects：命中一个用它，零个就 CreateProject，多个抛 `AmbiguousProject`。任一调用无权限抛
    `DeviceFarmAccessDenied`，记录的项目已核对为不存在、随后列举或建立被拒时异常带 `stored_project_missing=True`；
    其余 botocore 异常原样抛出（GetProject 的非 NotFound 错误也不转入列举，限流不等于项目不存在）。
    """
    client = _make_devicefarm_client(profile=profile)
    name = project_name(prefix)
    stored_missing = False
    if stored_arn is not None:
        if _project_exists(client, stored_arn):
            return ProjectResolution(arn=stored_arn, source="ssm")
        stored_missing = True
        if warn is not None:
            warn(f"部署记录的 Device Farm 项目 {stored_arn} 已不存在（可能已被手动删除），改为按名称 {name} 查找，找不到就尝试新建；"
                 f"旧项目的会话记录与录像已随项目删除，指向旧会话的控制台链接不再可用。")

    try:
        matches = [p["arn"] for page in client.get_paginator("list_projects").paginate()
                   for p in page.get("projects", []) if p.get("name") == name]
    except Exception as e:
        _raise_classified(e, stored_project_missing=stored_missing)
    if len(matches) > 1:
        raise AmbiguousProject(name, matches)
    if matches:
        return ProjectResolution(arn=matches[0], source="found")

    try:
        created = client.create_project(name=name)["project"]["arn"]
    except Exception as e:
        _raise_classified(e, stored_project_missing=stored_missing)
    return ProjectResolution(arn=created, source="created")


def verify_project(arn: str, *, profile: str | None) -> bool:
    """用 GetProject 只读核对项目是否还在（供 `diff` 核对 SSM 记录的 ARN，ADR 0051 决策 10「项目」）：在则 True，NotFound
    （项目被手动删除）则 False。只核对、不按名称列举、不建立，判定规则与 `resolve_or_create_project` 核对 `stored_arn` 共用一份。

    无权限抛 `DeviceFarmAccessDenied`；其余 botocore 异常（限流、网络、服务端故障）原样抛出，不当成「项目不存在」。
    """
    return _project_exists(_make_devicefarm_client(profile=profile), arn)


def list_open_sessions(project_arn: str, *, profile: str | None) -> list[OpenSession]:
    """列出项目里所有未到 COMPLETED 的远程访问会话，含排队中的（ADR 0051 决策 6 的泄漏护栏，供 doctor 用）。

    翻页列举 ListRemoteAccessSessions，按服务返回的顺序给出。只列举、不停止。无权限抛 `DeviceFarmAccessDenied`，其余 botocore 异常原样抛出。
    """
    client = _make_devicefarm_client(profile=profile)
    try:
        return [OpenSession(arn=s["arn"], name=s.get("name"), status=s.get("status", ""), created=s.get("created"))
                for page in client.get_paginator("list_remote_access_sessions").paginate(arn=project_arn)
                for s in page.get("remoteAccessSessions", []) if s.get("status") != _COMPLETED]
    except Exception as e:
        _raise_classified(e)


def is_access_denied(e: BaseException) -> bool:
    """botocore 异常是否为授权失败（错误码在 `_ACCESS_DENIED_CODES` 里）。provider 读 SSM 记录失败时据此决定失败消息是否列权限
    （ADR 0051 决策 10「失败消息的形态」），与本模块对 Device Farm 调用的分类用同一份错误码集合。"""
    return _error_code(e) in _ACCESS_DENIED_CODES


def _make_devicefarm_client(*, profile: str | None):
    """devicefarm 客户端：区域恒为 DEVICE_FARM_REGION，与 profile 或环境变量给的后端区域无关。抽出来供测试替换。"""
    import boto3

    return boto3.session.Session(profile_name=profile).client("devicefarm", region_name=_names.DEVICE_FARM_REGION)


def _project_exists(client, arn: str) -> bool:
    """GetProject 成功为 True，NotFound 为 False；无权限翻成 `DeviceFarmAccessDenied`，其余原样再抛。"""
    try:
        client.get_project(arn=arn)
    except Exception as e:
        if _error_code(e) != _NOT_FOUND_CODE:
            _raise_classified(e)
        return False
    return True


def _error_code(e: BaseException) -> str | None:
    """botocore ClientError 的 `Error.Code`；不是 ClientError（网络、无凭证等）时为 None。按属性读，不为此 import botocore。"""
    resp = getattr(e, "response", None)
    if not isinstance(resp, dict):
        return None
    code = (resp.get("Error") or {}).get("Code")
    return str(code) if code else None


def _raise_classified(e: Exception, *, stored_project_missing: bool = False) -> NoReturn:
    """无权限翻成 `DeviceFarmAccessDenied`（带上调用方给的 `stored_project_missing`），其余原样再抛。只在 except 块里调用。"""
    code = _error_code(e)
    if code in _ACCESS_DENIED_CODES:
        raise DeviceFarmAccessDenied(getattr(e, "operation_name", None) or "unknown", code,
                                     stored_project_missing=stored_project_missing) from e
    raise e
