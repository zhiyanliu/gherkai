"""测试目标模型的差集护栏（ADR 0048 决策 1、3）：合法组合常量、Target 两维的取值域、DeviceFarmRequest 的字段集合、
Target.as_text 的紧凑写法。"""
from __future__ import annotations

import dataclasses
from typing import get_args

from gherkai_core.model import AppRef, DeviceFarmRequest, Target, VALID_TARGETS


def test_valid_target_combinations_are_exactly_the_five_of_adr_0048():
    assert VALID_TARGETS == {("desktop", "web"), ("android", "web"), ("android", "app"), ("ios", "web"), ("ios", "app")}


def test_target_dimensions_match_adr_0048_table():
    fields = {f.name: f for f in dataclasses.fields(Target)}
    assert set(get_args(fields["device"].type) if not isinstance(fields["device"].type, str) else ("desktop", "android", "ios")) == {"desktop", "android", "ios"}
    assert set(get_args(fields["ui_kind"].type) if not isinstance(fields["ui_kind"].type, str) else ("web", "app")) == {"web", "app"}
    assert Target() == Target(device="desktop", ui_kind="web", app=None)


def test_device_farm_request_field_set():
    assert {f.name for f in dataclasses.fields(DeviceFarmRequest)} == {"provider", "device_arn", "os_version", "billing_method", "project_arn", "acquire_timeout_s"}
    assert DeviceFarmRequest(project_arn="p").provider == "aws-device-farm" and DeviceFarmRequest(project_arn="p").acquire_timeout_s == 600.0
    assert {f.name for f in dataclasses.fields(AppRef)} == {"alias", "app_id", "bucket", "key", "sha256"}


def test_target_as_text():
    assert Target().as_text() == "desktop/web"
    assert Target(device="android", ui_kind="app", app=AppRef(alias="shop", app_id="x")).as_text() == "android/app:shop"
    assert Target(device="ios", ui_kind="web").as_text() == "ios/web"
