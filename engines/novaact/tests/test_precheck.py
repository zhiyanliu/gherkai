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
    assert msg == ("这个 worker 不支持在 iOS 应用上执行测试（它支持：桌面网页）。请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。")
    assert "ADR" not in msg and "precheck" not in msg


def test_unsupported_ui_kind_on_supported_device_is_rejected():
    assert "不支持在 Android 应用上" in precheck_target({"target": {"device": "android", "uiKind": "app"}}, [{"device": "android", "ui_kinds": ["web"]}])


def test_timeout_over_session_limit_is_rejected_and_within_passes():
    over = precheck_target({"target": {"device": "android", "uiKind": "web"}, "timeoutS": 9000}, DEVICE_TARGETS)
    assert over is not None and "墙钟预算 9000 秒超过了 Android 网页的会话上限 8000 秒" in over and "--default-job-timeout" in over
    assert "预算 1500.5 秒" in precheck_target({"target": {"device": "android", "uiKind": "web"}, "timeoutS": 1500.5}, [{"device": "android", "ui_kinds": ["web"], "max_session_s": 10}])
    assert precheck_target({"target": {"device": "android", "uiKind": "web"}, "timeoutS": 8000}, DEVICE_TARGETS) is None
    assert precheck_target({"target": {"device": "android", "uiKind": "web"}}, DEVICE_TARGETS) is None  # 没带预算（不超时）不比较
    assert precheck_target({"target": {"device": "desktop", "uiKind": "web"}, "timeoutS": 10 ** 9}, DEVICE_TARGETS) is None  # 桌面无上限


def test_main_entry_rejects_device_job_before_any_session():
    """自检接在主入口建会话之前（ADR 0049 决策 7）：真子进程、剥掉 AWS 环境、喂一个 android/web 的 job——唯一的事件是
    scope_done{status: error, errorType: precheck_failed, message}，不发 scope_started，退出码 0。"""
    import json
    import os
    import subprocess
    import sys

    keep = ("PATH", "PYTHONPATH", "PYTHONHOME", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "VIRTUAL_ENV")
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["AWS_EC2_METADATA_DISABLED"] = "true"
    job = {"scope": {"id": "dev", "name": "dev"}, "engine": "novaact", "assertionVotes": 1, "timeoutS": 1500,
           "target": {"device": "android", "uiKind": "web"},
           "scenarios": [{"id": "d.feature:3", "name": "s", "steps": [{"index": 0, "keyword": "Given", "text": "https://x/"}]}]}
    proc = subprocess.run([sys.executable, "-m", "gherkai_worker_novaact"], input=(json.dumps(job) + "\n").encode("utf-8"),
                          capture_output=True, timeout=120, env=env)
    assert proc.returncode == 0, proc.stderr.decode()[-800:]
    events = [json.loads(l) for l in proc.stdout.decode("utf-8").splitlines() if l.startswith("{") and '"type"' in l]
    assert [e["type"] for e in events] == ["scope_done"], (events, proc.stderr.decode()[-500:])
    assert (events[0]["status"], events[0]["errorType"]) == ("error", "precheck_failed") and "不支持在 Android 网页上" in events[0]["message"]


def test_target_label_matches_cli_wording():
    assert target_label("desktop", "web") == "桌面网页" and target_label("android", "app") == "Android 应用" and target_label("ios", "web") == "iOS 网页"
