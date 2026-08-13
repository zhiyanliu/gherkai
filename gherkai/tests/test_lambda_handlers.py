"""Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler _run_ids_from_stream。

只测**事件格式解析**（最易错、最该测的纯逻辑）——用 P4 真验抓到的真实 ECS STOPPED event / DDB Stream event 形状。
handler 的装配部分（造 boto3/core、tick）靠 P4d 真跑验（moto 测不到真 Stream 触发/真 Fargate）。

lambdas/ 在仓库根，测试经 sys.path 加它（Lambda 部署时 handler + core + cli 打进同一 zip）。
"""
from __future__ import annotations

import sys
from pathlib import Path

# lambdas/ 在仓库根（cli/ 的上一级）
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lambdas"))

import exit_observer  # noqa: E402
import reconciler  # noqa: E402


# ---------- 退出观察者 _extract（从 STOPPED event detail 拿 run_id/scope_id/exit_code）----------

def _stopped_detail(run_id, scope_id, exit_code):
    """构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。"""
    return {
        "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/gherkai-cluster/abc",
        "lastStatus": "STOPPED",
        "overrides": {"containerOverrides": [{"environment": [
            {"name": "JOB_S3_URI", "value": "s3://b/x.json"},
            {"name": "RUN_ID", "value": run_id},
            {"name": "SCOPE_ID", "value": scope_id},
        ]}]},
        "containers": [{"name": "novaact-worker", "exitCode": exit_code}],
    }


def test_extract_run_scope_exit():
    run_id, scope_id, exit_code, timed_out = exit_observer._extract(_stopped_detail("run-1", "a", 0))
    assert run_id == "run-1" and scope_id == "a" and exit_code == 0
    assert timed_out is False  # 普通退出（无超时哨兵）不误标


def test_extract_nonzero_exit():
    _r, _s, exit_code, _t = exit_observer._extract(_stopped_detail("run-1", "a", 137))
    assert exit_code == 137


def test_extract_missing_exitcode_is_none():
    """container 缺 exitCode（宽限态）→ None（机制二保守）。"""
    detail = _stopped_detail("run-1", "a", 0)
    detail["containers"] = [{"name": "novaact-worker"}]  # 无 exitCode
    _r, _s, exit_code, _t = exit_observer._extract(detail)
    assert exit_code is None


def test_extract_missing_env_returns_none():
    """非本框架起的 task（env 无 RUN_ID/SCOPE_ID）→ (None, None, ...)，handler 会跳过。"""
    detail = {"overrides": {"containerOverrides": [{"environment": []}]}, "containers": []}
    run_id, scope_id, _e, _t = exit_observer._extract(detail)
    assert run_id is None and scope_id is None


def test_extract_timed_out_from_stopped_reason_sentinel():
    """stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True
    （ADR 0034「job timeout」节归因链：exit_observer 据此写 task_exited(timed_out=True)）。"""
    detail = _stopped_detail("run-1", "a", 143)
    detail["stoppedReason"] = f"{reconciler.TIMEOUT_STOP_SENTINEL}: scope exceeded 300s budget"
    _r, _s, exit_code, timed_out = exit_observer._extract(detail)
    assert exit_code == 143 and timed_out is True
    # 普通 stop（如同步路径的 "core requested stop"）不含哨兵 → False
    detail["stoppedReason"] = "core requested stop"
    assert exit_observer._extract(detail)[3] is False


def test_handler_skips_when_no_run_id():
    """handler 对缺 run_id 的事件返回 skipped（不崩、不误处理别的 cluster 负载）。"""
    r = exit_observer.handler({"detail": {"overrides": {"containerOverrides": []}, "containers": []}}, None)
    assert r.get("skipped") is True


# ---------- reconciler _run_ids_from_stream（从 DDB Stream records 提取 run_id 集）----------

def _stream_record(pk):
    return {"dynamodb": {"Keys": {"pk": {"S": pk}, "seq": {"N": "1"}}}}


def test_run_ids_single():
    event = {"Records": [_stream_record("run-1#features/x.feature:7")]}
    assert reconciler._run_ids_from_stream(event) == {"run-1"}


def test_run_ids_dedup_multi_scope_same_run():
    """同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。"""
    event = {"Records": [
        _stream_record("run-1#a"), _stream_record("run-1#b"), _stream_record("run-1#a"),
    ]}
    assert reconciler._run_ids_from_stream(event) == {"run-1"}


def test_run_ids_multi_run():
    event = {"Records": [_stream_record("run-1#a"), _stream_record("run-2#b")]}
    assert reconciler._run_ids_from_stream(event) == {"run-1", "run-2"}


def test_run_ids_scope_with_colon_not_hash():
    """scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。"""
    event = {"Records": [_stream_record("20260719T04Z-abc#features/deterministic_anchor.feature:7")]}
    assert reconciler._run_ids_from_stream(event) == {"20260719T04Z-abc"}


# ---------- 启动器 _run_ids_from_runs_stream（两种 event 源，ADR 0034 status --wait 接力 bug 回归）----------

def _runs_stream_record(run_id):
    return {"dynamodb": {"Keys": {"run_id": {"S": run_id}, "item_type": {"S": "META"}}}}


def test_starter_run_ids_from_runs_stream():
    """① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。"""
    event = {"Records": [_runs_stream_record("run-1"), _runs_stream_record("run-2")]}
    assert reconciler._run_ids_from_runs_stream(event) == {"run-1", "run-2"}


def test_starter_run_ids_from_direct_kick():
    """② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug：
    原启动器只认 Stream records、忽略此格式 → status --wait invoke 空转救不了卡 pending 的 run。"""
    assert reconciler._run_ids_from_runs_stream({"run_id": "run-x"}) == {"run-x"}


def test_starter_run_ids_both_sources():
    """Stream records + 直接 run_id 并存时都提取（健壮）。"""
    event = {"Records": [_runs_stream_record("run-1")], "run_id": "run-2"}
    assert reconciler._run_ids_from_runs_stream(event) == {"run-1", "run-2"}


def test_starter_run_ids_empty_when_neither():
    """既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。"""
    assert reconciler._run_ids_from_runs_stream({"test": "kick"}) == set()


# ---------- job timeout（ADR 0034「job timeout」节 cloud 档）----------

from core.adapters.event_log import SqliteEventLog  # noqa: E402
from core.adapters.run_store.local import LocalRunStore  # noqa: E402
from core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step  # noqa: E402


class _FakeSchedulerClient:
    """create_schedule 记录器（含 exceptions.ConflictException 形状，兼容 boto3 client 异常访问路径）。"""

    class exceptions:  # noqa: N801 —— 模仿 boto3 client.exceptions 命名
        class ConflictException(Exception):
            pass

    def __init__(self, conflict: bool = False):
        self.calls: list[dict] = []
        self._conflict = conflict

    def create_schedule(self, **kw):
        if self._conflict:
            raise self.exceptions.ConflictException("exists")
        self.calls.append(kw)


def test_timeout_watch_creates_one_time_schedule():
    client = _FakeSchedulerClient()
    watch = reconciler.EventBridgeTimeoutWatch(
        client, kicker_arn="arn:aws:lambda:us-east-1:000000000000:function:gherkai-kicker",
        role_arn="arn:aws:iam::000000000000:role/gherkai-timeout-scheduler", prefix="gherkai-")
    watch.arm("run-1", "features/x.feature:7", 300.0)
    assert len(client.calls) == 1
    kw = client.calls[0]
    assert kw["Name"].startswith("gherkai-job-timeout-") and len(kw["Name"]) <= 64  # 哈希名（scope_id 可含非法字符）
    assert kw["ScheduleExpression"].startswith("at(")
    assert kw["ActionAfterCompletion"] == "DELETE"  # 到点自动删（idle 零成本）
    assert kw["FlexibleTimeWindow"] == {"Mode": "OFF"}
    import json as _json
    payload = _json.loads(kw["Target"]["Input"])
    assert payload == {"run_id": "run-1", "timeout_scope": "features/x.feature:7"}


def test_timeout_watch_conflict_is_idempotent():
    """同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。"""
    watch = reconciler.EventBridgeTimeoutWatch(
        _FakeSchedulerClient(conflict=True), kicker_arn="arn:k", role_arn="arn:r", prefix="gherkai-")
    watch.arm("run-1", "a", 60.0)  # 不抛即过


def _timeout_built(tmp_path, *, status=Status.RUNNING, claimed_at=None, with_exit=False):
    """构造 _handle_timeout 需要的 built 元组（真 LocalRunStore + SqliteEventLog，meta 带 timeout 预算）。"""
    job = Job(scope_id="a", scope_name="a", engine="novaact", timeout_s=300.0,
              scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),))
    meta = RunMeta(run_id="run-1", created_at="t0", jobs=(job,))
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(
        run_id="run-1", status=Status.RUNNING,
        jobs={"a": JobState("a", status, claimed_at=claimed_at)},
        started_at="t0", high_water_mark=0))
    log = SqliteEventLog(tmp_path / "run-1" / "events.db")
    if with_exit:
        log.record_exit("a", 137)
    return meta, log, store, None, 1, None, None


class _FakeEcs:
    """list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。"""

    def __init__(self, task_arns=(), scope_id="a"):
        self._arns = list(task_arns)
        self._scope_id = scope_id
        self.stopped: list[dict] = []

    def list_tasks(self, **kw):
        return {"taskArns": self._arns}

    def describe_tasks(self, **kw):
        return {"tasks": [
            {"taskArn": arn,
             "overrides": {"containerOverrides": [{"environment": [
                 {"name": "SCOPE_ID", "value": self._scope_id}]}]}}
            for arn in kw["tasks"]]}

    def stop_task(self, **kw):
        self.stopped.append(kw)
        return {}


def test_handle_timeout_stops_matching_task(tmp_path, monkeypatch):
    """仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer 既有链收敛（单一真源）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path), ecs_client=ecs)
    assert r == "stopped"
    assert len(ecs.stopped) == 1
    assert reconciler.TIMEOUT_STOP_SENTINEL in ecs.stopped[0]["reason"]
    assert ecs.stopped[0]["task"] == "arn:task/1"


def test_handle_timeout_noop_when_job_terminal(tmp_path, monkeypatch):
    """到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path, status=Status.PASSED), ecs_client=ecs)
    assert r == "noop-not-running" and ecs.stopped == []


def test_handle_timeout_noop_when_exit_in_flight(tmp_path, monkeypatch):
    """退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path, with_exit=True), ecs_client=ecs)
    assert r == "noop-exit-in-flight" and ecs.stopped == []


def test_handle_timeout_converges_directly_when_task_gone(tmp_path, monkeypatch):
    """task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛
    （对位 local 接力恢复；「到点 invoke 顺带兜事件丢投」的落点）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    built = _timeout_built(tmp_path, claimed_at="2026-08-13T00:00:00Z")
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=_FakeEcs(task_arns=[]))
    assert r == "converged-directly"
    exits = [rec for rec in built[1].records() if rec.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.timed_out is True and exits[0].exited.exit_code is None


def test_kicker_routes_timeout_scope_payload(monkeypatch):
    """Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick bonus）。"""
    calls = {}
    monkeypatch.setattr(reconciler, "_build", lambda rid: ("BUILT",))
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built: calls.update(handled=(rid, sid, built)))
    monkeypatch.setattr(reconciler, "_tick_runs", lambda run_ids, label: calls.update(ticked=(run_ids, label)) or {"ok": True})
    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert calls["handled"] == ("run-1", "a", ("BUILT",))
    assert calls["ticked"] == ({"run-1"}, "kicker")  # timeout payload 也照常触发 tick

def test_scan_overdue_timeouts_only_over_budget(tmp_path, monkeypatch):
    """防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。"""
    calls = []
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built: calls.append(sid))
    # claimed_at 在过去（相对真时钟必已超 300s+60s 余量）→ 处置
    built = _timeout_built(tmp_path / "over", claimed_at="2026-08-13T00:00:00Z")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == ["a"]
    # claimed_at 在未来（elapsed 为负，等价「未到期」）→ 不碰
    calls.clear()
    built = _timeout_built(tmp_path / "fresh", claimed_at="2099-01-01T00:00:00Z")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == []
    # 无 claimed_at（旧数据/未 claim）→ 不碰（无起算点不臆断）
    built = _timeout_built(tmp_path / "nocl")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == []
