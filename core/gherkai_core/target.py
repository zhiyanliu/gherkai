"""测试目标的定义层结构校验（ADR 0048 决策 3）。

两个时点各核一次：组合根写 definition 之前（run / submit 的共享前置）、推进器读 definition 时（`serialize.job_from_dict`）。只核结构
（字段成对、非空、类型、合法组合），取值域（`billing_method` 的枚举、`os_version` 的点分形态、ARN 的服务与资源类型段）归 CLI；core 不读、不比较任何服务商状态。
plan 形态的 Job（`device_request` 为 None、应用条目只有别名与包名）不走这里。
"""
from __future__ import annotations

import math

from gherkai_core.errors import DefinitionContractError
from gherkai_core.model import VALID_TARGETS, Job


def _is_text(v) -> bool:
    return isinstance(v, str) and bool(v)


def _is_positive_number(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    try:
        return math.isfinite(v) and v > 0
    except (OverflowError, TypeError):  # 超出 float 范围的整数：不是有限数
        return False


def validate_job_definition(job: Job) -> None:
    """definition 里的一个 job 必须是完整形态，否则抛 DefinitionContractError（推进器与 worker 只见到完整的应用条目与设备请求）。"""
    t = job.target
    where = f"job {job.scope_id!r}"
    if not isinstance(t.device, str) or not isinstance(t.ui_kind, str) or (t.device, t.ui_kind) not in VALID_TARGETS:
        raise DefinitionContractError(f"{where} 的测试目标 {t.device!r}/{t.ui_kind!r} 不是合法组合（桌面只有网页；设备可为网页或应用）")
    if (t.ui_kind == "app") != (t.app is not None):
        raise DefinitionContractError(f"{where}：界面类型为应用时必须带应用条目，为网页时不得带（现为 {t.ui_kind}、应用条目{'有' if t.app else '无'}）")
    if t.app is not None:
        for name in ("alias", "app_id", "bucket", "key", "sha256"):
            if not _is_text(getattr(t.app, name, None)):
                raise DefinitionContractError(f"{where} 的应用条目缺 {name}（definition 里的应用条目须五项齐全且为非空文本：别名、包名或 bundle id、安装包的 bucket、key、sha256）")
    dr = job.device_request
    if t.is_desktop != (dr is None):
        raise DefinitionContractError(f"{where}：非桌面目标当且仅当带设备请求（现为目标 {t.as_text()}、设备请求{'有' if dr else '无'}）")
    if dr is not None:
        if dr.provider != "aws-device-farm":
            raise DefinitionContractError(f"{where} 的设备请求服务商未知：{dr.provider!r}")
        if not _is_text(dr.project_arn):
            raise DefinitionContractError(f"{where} 的设备请求缺 project_arn")
        for name in ("device_arn", "os_version"):
            v = getattr(dr, name)
            if v is not None and not _is_text(v):
                raise DefinitionContractError(f"{where} 的设备请求 {name} 须为非空文本或不设（现为 {v!r}）")
        if (dr.device_arn is None) == (dr.os_version is None):
            raise DefinitionContractError(f"{where} 的设备请求须在 device_arn 与 os_version 之间恰给一个（现{'两个都给' if dr.device_arn is not None else '两个都缺'}）")
        if not _is_text(dr.billing_method):
            raise DefinitionContractError(f"{where} 的设备请求缺 billing_method")
        if not _is_positive_number(dr.acquire_timeout_s):
            raise DefinitionContractError(f"{where} 的设备请求 acquire_timeout_s 须为有限正数（现为 {dr.acquire_timeout_s!r}）")
    ts = job.timeout_s
    if ts is not None and not _is_positive_number(ts):
        raise DefinitionContractError(f"{where} 的墙钟预算须为有限正数或不设（现为 {ts!r}）")
    if not t.is_desktop and ts is None:
        raise DefinitionContractError(f"{where} 是设备目标却没有墙钟预算（设备 scope 不存在「不超时」）")
