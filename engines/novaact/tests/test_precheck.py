"""建会话前的自检（ADR 0049 决策 7；0048 决策 3、4）：目标不在 targets 里或预算超过会话上限即拒绝；缺 target 即桌面网页；
消息是产品语言、不带内部指代；与能力自述同一份 WORKER_TARGETS。"""
from __future__ import annotations

from gherkai_worker_novaact import run_scope as rs
from gherkai_worker_novaact.lib.precheck import precheck_target, target_label

DEVICE_TARGETS = [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8000}]


def test_desktop_job_without_target_key_passes_against_real_worker_targets():
    assert precheck_target({"scope": {"id": "s"}}, rs.WORKER_TARGETS) is None  # 1.5 之前的 CLI 不写 target：桌面网页
    assert precheck_target({"target": {"device": "desktop", "uiKind": "web"}, "timeoutS": 300}, rs.WORKER_TARGETS) is None


def test_device_job_rejected_by_nova_with_product_message():
    msg = precheck_target({"target": {"device": "ios", "uiKind": "app", "app": {"alias": "shop"}}, "timeoutS": 1500}, rs.WORKER_TARGETS)
    assert msg == ("这个 worker 不支持在iOS 应用上执行测试（它支持：桌面网页）。请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。")
    assert "ADR" not in msg and "precheck" not in msg


def test_unsupported_ui_kind_on_supported_device_is_rejected():
    assert "不支持在Android 应用" in precheck_target({"target": {"device": "android", "uiKind": "app"}}, [{"device": "android", "ui_kinds": ["web"]}])


def test_timeout_over_session_limit_is_rejected_and_within_passes():
    over = precheck_target({"target": {"device": "android", "uiKind": "web"}, "timeoutS": 9000}, DEVICE_TARGETS)
    assert over is not None and "超过了Android 网页的会话上限 8000 秒" in over and "--default-job-timeout" in over
    assert precheck_target({"target": {"device": "android", "uiKind": "web"}, "timeoutS": 8000}, DEVICE_TARGETS) is None
    assert precheck_target({"target": {"device": "android", "uiKind": "web"}}, DEVICE_TARGETS) is None  # 没带预算（不超时）不比较
    assert precheck_target({"target": {"device": "desktop", "uiKind": "web"}, "timeoutS": 10 ** 9}, DEVICE_TARGETS) is None  # 桌面无上限


def test_target_label_matches_cli_wording():
    assert target_label("desktop", "web") == "桌面网页" and target_label("android", "app") == "Android 应用" and target_label("ios", "web") == "iOS 网页"
