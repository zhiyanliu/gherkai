"""建会话前的自检（ADR 0049 决策 7；0048 决策 3、4；0024 的结构版本）：job 行的 schemaVersion 不等于本 worker 认的、目标不在 targets 里、
预算超过会话上限都拒绝；target 必有，缺键即版本不一致；消息是产品语言、不带内部指代；与能力自述同一份 WORKER_TARGETS。"""
from __future__ import annotations

from gherkai_worker_novaact import run_scope as rs
from gherkai_worker_novaact.lib.precheck import PROTOCOL_SCHEMA_VERSION, precheck_job, precheck_schema, precheck_target, target_label

DEVICE_TARGETS = [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8000}]


def test_desktop_job_passes_and_missing_target_is_a_version_mismatch():
    assert precheck_target({"target": {"device": "desktop", "uiKind": "web"}, "timeoutS": 300}, rs.WORKER_TARGETS) is None
    assert precheck_target({"target": {"device": "desktop", "uiKind": "web"}, "timeoutS": None}, rs.WORKER_TARGETS) is None  # 不超时写 null
    msg = precheck_target({"scope": {"id": "s"}}, rs.WORKER_TARGETS)  # 键集固定：缺 target 不再当桌面
    assert msg is not None and "没有带测试目标" in msg and "同一版本" in msg


def test_schema_version_is_checked_first_and_pinned_by_golden():
    """job 行的结构版本（ADR 0024）：不等于本 worker 认的（含缺键）即拒绝、先于目标核对；本 worker 认的值与跨语言 golden 一致。"""
    import json
    from pathlib import Path

    assert precheck_schema({"schemaVersion": PROTOCOL_SCHEMA_VERSION}) is None
    assert "缺失" in precheck_schema({}) and "同一版本" in precheck_schema({})
    assert precheck_schema({"schemaVersion": True}) is not None and precheck_schema({"schemaVersion": "1"}) is not None  # true 与 "1" 都不是 1
    assert f"格式版本是 {PROTOCOL_SCHEMA_VERSION + 1}" in precheck_schema({"schemaVersion": PROTOCOL_SCHEMA_VERSION + 1})
    bad = {"schemaVersion": PROTOCOL_SCHEMA_VERSION + 1, "target": {"device": "ios", "uiKind": "app"}}
    assert "格式版本" in precheck_job(bad, rs.WORKER_TARGETS)  # 版本先于目标
    ok = {"schemaVersion": PROTOCOL_SCHEMA_VERSION, "target": {"device": "desktop", "uiKind": "web"}, "timeoutS": None}
    assert precheck_job(ok, rs.WORKER_TARGETS) is None
    fixture = json.loads((Path(__file__).resolve().parents[3] / "engines" / "fixtures" / "job-lines.json").read_text(encoding="utf-8"))
    assert {j["schemaVersion"] for j in fixture["jobs"].values()} == {PROTOCOL_SCHEMA_VERSION}
    assert rs._capabilities()["schema_version"] == PROTOCOL_SCHEMA_VERSION  # 能力自述写的是同一个协议版本


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
    job = {"schemaVersion": 1, "scope": {"id": "dev", "name": "dev"}, "engine": "novaact", "assertionVotes": 1, "timeoutS": 1500,
           "target": {"device": "android", "uiKind": "web"}, "deviceRequest": None,
           "scenarios": [{"id": "d.feature:3", "name": "s", "steps": [{"index": 0, "keyword": "Given", "text": "https://x/"}]}]}
    proc = subprocess.run([sys.executable, "-m", "gherkai_worker_novaact"], input=(json.dumps(job) + "\n").encode("utf-8"),
                          capture_output=True, timeout=120, env=env)
    assert proc.returncode == 0, proc.stderr.decode()[-800:]
    events = [json.loads(l) for l in proc.stdout.decode("utf-8").splitlines() if l.startswith("{") and '"type"' in l]
    assert [e["type"] for e in events] == ["scope_done"], (events, proc.stderr.decode()[-500:])
    assert (events[0]["status"], events[0]["errorType"]) == ("error", "precheck_failed") and "不支持在 Android 网页上" in events[0]["message"]


def test_target_label_matches_cli_wording():
    assert target_label("desktop", "web") == "桌面网页" and target_label("android", "app") == "Android 应用" and target_label("ios", "web") == "iOS 网页"


def test_main_entry_rejects_job_without_schema_version_before_reading_anything_else():
    """版本核对先于读 job 行的任何别的键：缺 schemaVersion 的桌面 job（scenarios 也缺）只得到一条 precheck_failed，不是 KeyError 退出。"""
    import json
    import os
    import subprocess
    import sys

    keep = ("PATH", "PYTHONPATH", "PYTHONHOME", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "VIRTUAL_ENV")
    env = {k: v for k, v in os.environ.items() if k in keep}
    env["AWS_EC2_METADATA_DISABLED"] = "true"
    job = {"scope": {"id": "old", "name": "old"}, "engine": "novaact", "assertionVotes": 1}
    proc = subprocess.run([sys.executable, "-m", "gherkai_worker_novaact"], input=(json.dumps(job) + "\n").encode("utf-8"),
                          capture_output=True, timeout=120, env=env)
    assert proc.returncode == 0, proc.stderr.decode()[-800:]
    events = [json.loads(l) for l in proc.stdout.decode("utf-8").splitlines() if l.startswith("{") and '"type"' in l]
    assert [e["type"] for e in events] == ["scope_done"], (events, proc.stderr.decode()[-500:])
    assert events[0]["scopeId"] == "old" and events[0]["errorType"] == "precheck_failed" and "格式版本是 缺失" in events[0]["message"]
