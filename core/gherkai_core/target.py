"""测试目标的定义层结构校验（ADR 0048 决策 3）。

两个时点各核一次：组合根写 definition 之前、推进器读 definition 时（`serialize.job_from_dict`）。只核结构（字段成对、非空、类型、
合法组合），取值域（`billing_method` 的枚举、`os_version` 的点分形态、ARN 前缀）归 CLI；core 不读、不比较任何服务商状态。
plan 形态的 Job（`device_request` 为 None、应用条目只有别名与包名）不走这里。
"""
from __future__ import annotations

import math

from gherkai_core.errors import DefinitionContractError
from gherkai_core.model import VALID_TARGETS, Job


def validate_job_definition(job: Job) -> None:
    """definition 里的一个 job 必须是完整形态，否则抛 DefinitionContractError（推进器与 worker 只见到完整的应用条目与设备请求）。"""
    t = job.target
    where = f"job {job.scope_id!r}"
    if (t.device, t.ui_kind) not in VALID_TARGETS:
        raise DefinitionContractError(f"{where} 的测试目标 {t.device}/{t.ui_kind} 不是合法组合（桌面只有网页；设备可为网页或应用）")
    if (t.ui_kind == "app") != (t.app is not None):
        raise DefinitionContractError(f"{where}：界面类型为应用时必须带应用条目，为网页时不得带（现为 {t.ui_kind}、应用条目{'有' if t.app else '无'}）")
    if t.app is not None:
        for name in ("alias", "app_id", "bucket", "key", "sha256"):
            v = getattr(t.app, name)
            if not isinstance(v, str) or not v:
                raise DefinitionContractError(f"{where} 的应用条目缺 {name}（definition 里的应用条目须五项齐全：别名、包名或 bundle id、安装包的 bucket、key、sha256）")
    dr = job.device_request
    if t.is_desktop != (dr is None):
        raise DefinitionContractError(f"{where}：非桌面目标当且仅当带设备请求（现为目标 {t.as_text()}、设备请求{'有' if dr else '无'}）")
    if dr is not None:
        if dr.provider != "aws-device-farm":
            raise DefinitionContractError(f"{where} 的设备请求服务商未知：{dr.provider!r}")
        if not isinstance(dr.project_arn, str) or not dr.project_arn:
            raise DefinitionContractError(f"{where} 的设备请求缺 project_arn")
        has_arn = isinstance(dr.device_arn, str) and bool(dr.device_arn)
        has_ver = isinstance(dr.os_version, str) and bool(dr.os_version)
        if has_arn == has_ver:
            raise DefinitionContractError(f"{where} 的设备请求须在 device_arn 与 os_version 之间恰给一个（现{'两个都给' if has_arn else '两个都缺'}）")
        if not isinstance(dr.billing_method, str) or not dr.billing_method:
            raise DefinitionContractError(f"{where} 的设备请求缺 billing_method")
        if isinstance(dr.acquire_timeout_s, bool) or not isinstance(dr.acquire_timeout_s, (int, float)) \
                or not math.isfinite(dr.acquire_timeout_s) or dr.acquire_timeout_s <= 0:
            raise DefinitionContractError(f"{where} 的设备请求 acquire_timeout_s 须为有限正数（现为 {dr.acquire_timeout_s!r}）")
    ts = job.timeout_s
    if ts is not None and (isinstance(ts, bool) or not isinstance(ts, (int, float)) or not math.isfinite(ts) or ts <= 0):
        raise DefinitionContractError(f"{where} 的墙钟预算须为有限正数或不设（现为 {ts!r}）")
    if not t.is_desktop and ts is None:
        raise DefinitionContractError(f"{where} 是设备目标却没有墙钟预算（设备 scope 不存在「不超时」）")
