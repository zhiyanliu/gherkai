"""Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler _run_ids_from_stream。

主体测**事件格式解析**（最易错、最该测的纯逻辑）——用实际运行抓到的 ECS STOPPED event / DDB Stream event 形状；
另有一组走 moto 内存表运行真 handler（末尾「只推进 detached run」——组合根侧分流是行为契约，解析测不出来）。
真 Stream 触发 / 真 Fargate / 真 EventBridge 投递仍是 moto 之外的真实运行边界（绿≠对的证据边界）。

handler 源与本测试同住 provider 包（`gherkai_deploy_aws/lambdas/`，AWS 专属胶水，ADR 0037 决策 6）——测试不寄居
上游 runtime（ADR 0016 当年抽包的理由之一就是「handler 测试无处安身」）。经 sys.path 加那个目录——**摊平 import
是真实形态**：Lambda asset 把它们摊在 zip 根、作平级顶层模块（`exit_observer` 里 `from reconciler import …`
依赖此形态），故这里也按顶层模块 import、不走包路径。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 包内的 handler 源目录（tests/ 与 gherkai_deploy_aws/ 是兄弟目录）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gherkai_deploy_aws" / "lambdas"))

import exit_observer  # noqa: E402
import reconciler  # noqa: E402


# ---------- 退出观察者 _extract（从 STOPPED event detail 拿 run_id/scope_id/exit_code）----------

def _stopped_detail(run_id, scope_id, exit_code):
    """构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，已由实际运行抓到的事件证实）。"""
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
    run_id, scope_id, exit_code, timed_out, reason, _at = exit_observer._extract(_stopped_detail("run-1", "a", 0))
    assert run_id == "run-1" and scope_id == "a" and exit_code == 0
    assert timed_out is False  # 普通退出（无超时哨兵）不误标
    assert reason is None  # 带码的退出不带平台归因（worker 自己的日志才是归因源）


def test_extract_nonzero_exit():
    _r, _s, exit_code, _t, _reason, _at = exit_observer._extract(_stopped_detail("run-1", "a", 137))
    assert exit_code == 137


def test_extract_missing_exitcode_becomes_platform_sentinel_with_reason():
    """container 缺 exitCode 表示容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 + `stopCode: stoppedReason`
    归因（ADR 0034 机制二「退出码缺失」条）。曾写 None 当宽限态等下轮补——STOPPED 事件只来一次，run 会永久 wedge。"""
    from gherkai_core.project import PLATFORM_FAILED_EXIT
    detail = _stopped_detail("run-1", "a", 0)
    detail["containers"] = [{"name": "novaact-worker"}]  # 无 exitCode
    detail["stopCode"] = "TaskFailedToStart"
    detail["stoppedReason"] = "CannotPullContainerError: ref pull has been retried 1 time(s): not found"
    _r, _s, exit_code, timed_out, reason, _at = exit_observer._extract(detail)
    assert exit_code == PLATFORM_FAILED_EXIT and timed_out is False
    assert reason == "TaskFailedToStart: CannotPullContainerError: ref pull has been retried 1 time(s): not found"


def test_extract_missing_exitcode_without_any_reason_still_gets_sentinel():
    """连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。"""
    from gherkai_core.project import PLATFORM_FAILED_EXIT
    detail = _stopped_detail("run-1", "a", 0)
    detail["containers"] = []
    _r, _s, exit_code, _t, reason, _at = exit_observer._extract(detail)
    assert exit_code == PLATFORM_FAILED_EXIT and reason


def test_extract_missing_env_returns_none():
    """非 gherkai 起的 task（env 无 RUN_ID/SCOPE_ID）→ (None, None, ...)，handler 会跳过。"""
    detail = {"overrides": {"containerOverrides": [{"environment": []}]}, "containers": []}
    run_id, scope_id, _e, _t, _reason, _at = exit_observer._extract(detail)
    assert run_id is None and scope_id is None


def test_extract_timed_out_from_stopped_reason_sentinel():
    """stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True
    （ADR 0034「job timeout」节归因链：exit_observer 据此写 task_exited(timed_out=True)）。"""
    detail = _stopped_detail("run-1", "a", 143)
    detail["stoppedReason"] = f"{reconciler.TIMEOUT_STOP_SENTINEL}: scope exceeded 300s budget"
    _r, _s, exit_code, timed_out, _reason, _at = exit_observer._extract(detail)
    assert exit_code == 143 and timed_out is True
    # reason 不含哨兵的 StopTask（如人工停止）→ False
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


def test_run_ids_skips_ttl_remove_records():
    """events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，不为它推进一次
    （推进方本次读到终态即返回）。"""
    removed = dict(_stream_record("run-1#a"), eventName="REMOVE")
    assert reconciler._run_ids_from_stream({"Records": [removed]}) == set()
    # 混批：同批里的正常写入照常推进（别退化成「整批丢弃」）
    kept = dict(_stream_record("run-2#a"), eventName="INSERT")
    assert reconciler._run_ids_from_stream({"Records": [removed, kept]}) == {"run-2"}


def test_run_ids_keeps_modify_and_records_without_event_name():
    """只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的
    观察者以真退出码/归因重写）在 Stream 上是 MODIFY，白名单会把这类携带新归因的写入静默滤掉；缺 eventName
    的记录形状同样照收。"""
    modified = dict(_stream_record("run-1#a"), eventName="MODIFY")
    assert reconciler._run_ids_from_stream({"Records": [modified]}) == {"run-1"}
    assert reconciler._run_ids_from_stream({"Records": [_stream_record("run-1#a")]}) == {"run-1"}


def test_run_ids_scope_with_colon_not_hash():
    """scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。"""
    event = {"Records": [_stream_record("20260719T04Z-abc#features/deterministic_step.feature:7")]}
    assert reconciler._run_ids_from_stream(event) == {"20260719T04Z-abc"}


# ---------- 启动器 _run_ids_from_runs_stream（两种 event 源，ADR 0034「重议闸门」首条）----------

def _runs_stream_record(run_id):
    return {"dynamodb": {"Keys": {"run_id": {"S": run_id}, "item_type": {"S": "META"}}}}


def test_starter_run_ids_from_runs_stream():
    """① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。"""
    event = {"Records": [_runs_stream_record("run-1"), _runs_stream_record("run-2")]}
    assert reconciler._run_ids_from_runs_stream(event) == {"run-1", "run-2"}


def test_starter_run_ids_from_direct_kick():
    """② 直接 invoke 触发一次 kickoff（status --wait 接力）：payload {"run_id": ...}——实际运行中抓到的 bug：
    原启动器只认 Stream records、忽略此格式 → status --wait invoke 空转救不了卡 pending 的 run。"""
    assert reconciler._run_ids_from_runs_stream({"run_id": "run-x"}) == {"run-x"}


def test_starter_run_ids_both_sources():
    """Stream records + 直接 run_id 并存时都提取（健壮）。"""
    event = {"Records": [_runs_stream_record("run-1")], "run_id": "run-2"}
    assert reconciler._run_ids_from_runs_stream(event) == {"run-1", "run-2"}


def test_starter_run_ids_empty_when_neither():
    """既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。"""
    assert reconciler._run_ids_from_runs_stream({"test": "kick"}) == set()


# ---------- job timeout（ADR 0034「job timeout」节的云端后端一侧）----------

import datetime as _dt  # noqa: E402

import pytest  # noqa: E402

from gherkai_core.adapters.event_log import SqliteEventLog  # noqa: E402
from gherkai_core.adapters.run_store.local import LocalRunStore  # noqa: E402
from gherkai_core.model import (Job, JobState, RunMeta, RunState, Scenario, Status, Step,  # noqa: E402
                                StepArgument)


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
    watch.arm("run-1", "features/x.feature:7", _dt.datetime(2026, 11, 8, 10, 5, tzinfo=_dt.timezone.utc))
    assert len(client.calls) == 1
    kw = client.calls[0]
    assert kw["Name"].startswith("gherkai-job-timeout-") and len(kw["Name"]) <= 64  # 哈希名（scope_id 可含非法字符）
    assert kw["ScheduleExpression"].startswith("at(")
    assert kw["ActionAfterCompletion"] == "DELETE"  # 到点自动删（idle 零成本）
    assert kw["FlexibleTimeWindow"] == {"Mode": "OFF"}
    import json as _json
    payload = _json.loads(kw["Target"]["Input"])
    assert payload == {"run_id": "run-1", "timeout_scope": "features/x.feature:7"}


def test_timeout_watch_at_is_the_given_cutoff():
    """at 取 core 传来的截止时刻本身，带秒、不取整到分钟（ADR 0034「job timeout」节「到点不早于 deadline」条①）：触发器不再自己
    由预算推算，arm 晚于认领不推后到点。at() 只收到秒，小数秒截去，差的那不到一秒由到点处置的复查补足；截止时刻带别的时区偏移时
    换算回 UTC（at() 不带时区后缀、按 UTC 解释）。"""
    client = _FakeSchedulerClient()
    watch = reconciler.EventBridgeTimeoutWatch(client, kicker_arn="arn:k", role_arn="arn:r", prefix="gherkai-")
    watch.arm("run-1", "a", _dt.datetime.fromisoformat("2026-11-08T10:05:07.800000+00:00"))
    watch.arm("run-1", "b", _dt.datetime.fromisoformat("2026-11-08T18:01:37+08:00"))
    assert [c["ScheduleExpression"] for c in client.calls] == [
        "at(2026-11-08T10:05:07)", "at(2026-11-08T10:01:37)"]


def test_job_timeout_schedule_is_armed_at_the_cutoff_capped_by_the_run_deadline(tmp_path):
    """推进步骤认领时算出的截止时刻经 CloudLauncher 原样定为一次性定时触发的时刻（ADR 0054 决策二后台推进条「截止时刻与说明」）：
    认领时刻加预算早于运行期限时取前者，晚于期限时以期限封顶。真 tick、真 CloudLauncher、真触发器，只替换 Scheduler 客户端与
    起 task 的引擎；时刻带秒、小数秒截去。判定存储是临时目录里的本机文件存储（这一轮只认领、不存明细）。"""
    from gherkai_core.adapters.cloud_launcher import CloudLauncher
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.reconcile import tick

    claimed = _dt.datetime(2026, 11, 8, 10, 0, 0, 500000, tzinfo=_dt.timezone.utc)

    class _Engine:
        def start_scope(self, job):
            pass

    def armed_at(sub: str, deadline_at: str) -> str:
        job = Job(scope_id="a", scope_name="a", engine="novaact", timeout_s=300.0,
                  scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),))
        meta = RunMeta(run_id="run-1", created_at="t0", jobs=(job,), deadline_at=deadline_at)
        store = LocalRunStore(tmp_path / sub)
        store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)},
                                        started_at="t0", high_water_mark=0))
        client = _FakeSchedulerClient()
        watch = reconciler.EventBridgeTimeoutWatch(client, kicker_arn="arn:k", role_arn="arn:r", prefix="gherkai-")
        launcher = CloudLauncher(lambda _name: _Engine(), run_id="run-1", timeout_watch=watch)
        tick("run-1", meta, SqliteEventLog(tmp_path / sub / "events.db"), store, launcher, 1, clock=lambda: claimed,
             result_store=LocalResultStore(tmp_path / sub))
        assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING
        [call] = client.calls
        return call["ScheduleExpression"]

    assert armed_at("budget", "2026-11-08T11:00:00+00:00") == "at(2026-11-08T10:05:00)"    # 认领时刻加 300 秒
    assert armed_at("deadline", "2026-11-08T10:03:20+00:00") == "at(2026-11-08T10:03:20)"  # 期限更早：以期限封顶


def test_timeout_watch_name_is_exactly_64_chars_at_prefix_limit():
    # prefix 取上限 32 个字符（stack 合成期校验的边界）时，schedule 名恰为 EventBridge Scheduler 的 64 字符上限。
    prefix = "a" * 31 + "-"
    watch = reconciler.EventBridgeTimeoutWatch(
        _FakeSchedulerClient(), kicker_arn="arn:k", role_arn="arn:r", prefix=prefix)
    name = watch.schedule_name("run-1", "features/x.feature:7")
    assert name.startswith(f"{prefix}job-timeout-")
    assert len(name) == 64


def test_timeout_watch_conflict_is_idempotent():
    """同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。"""
    watch = reconciler.EventBridgeTimeoutWatch(
        _FakeSchedulerClient(conflict=True), kicker_arn="arn:k", role_arn="arn:r", prefix="gherkai-")
    watch.arm("run-1", "a", _dt.datetime(2026, 11, 8, 10, 1, tzinfo=_dt.timezone.utc))  # 不抛即过


def _timeout_built(tmp_path, *, status=Status.RUNNING, claimed_at=None, with_exit=False,
                   deadline_at="2999-01-01T00:00:00+00:00"):
    """构造 _handle_timeout 需要的 built 元组（真 LocalRunStore + SqliteEventLog，meta 带 300 秒的 timeout 预算；运行期限缺省远在
    任何时刻之后、不起作用）。"""
    job = Job(scope_id="a", scope_name="a", engine="novaact", timeout_s=300.0,
              scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),))
    meta = RunMeta(run_id="run-1", created_at="t0", jobs=(job,), deadline_at=deadline_at)
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
    """list_tasks/describe_tasks/stop_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的 task 描述
    （dict：arn / lastStatus / desiredStatus / exitCode? / stoppedReason? / stopCode? / executionStoppedAt? / stoppedAt? /
    scope_id?——后者缺省用
    构造时的 `scope_id`，给多 task 场景造出「只有一个匹配目标」）。list_tasks 按 desiredStatus 过滤
    （ECS 语义：正在停止/已停止的不在 RUNNING 列表里）；describe 返回带 SCOPE_ID env 的 overrides。

    **两条真 ECS 上限照搬**（单页 100 与 tasks 硬上限 100，实现必须翻页 + 分批才过得去）：list_tasks 一页最多
    `PAGE` 条、给了 `maxResults` 则按它（仍夹在 `PAGE` 以内，同真 API）、还有下页就带 `nextToken`（本替身里
    就是页内偏移）；describe_tasks 收到超过 `PAGE` 个 ARN 直接抛，真 AWS 那边是 `InvalidParameterException`。
    每批 ARN 记进 `described` 供断言分批与「找到即停」。"""

    PAGE = 100

    def __init__(self, task_arns=(), scope_id="a", tasks=()):
        self._tasks = [{"arn": a, "lastStatus": "RUNNING", "desiredStatus": "RUNNING"} for a in task_arns] + list(tasks)
        self._scope_id = scope_id
        self.stopped: list[dict] = []
        self.described: list[list[str]] = []

    def list_tasks(self, **kw):
        want = kw.get("desiredStatus", "RUNNING")
        arns = [t["arn"] for t in self._tasks if t.get("desiredStatus", "RUNNING") == want]
        start = int(kw.get("nextToken") or 0)
        # 页长按调用方给的 `maxResults` 走、夹到真上限：调小了就该翻更多页，替身照搬这条才测得出翻页逻辑
        # （当前实现不传它、靠真 ECS 默认 100，这里先把行为对齐，别让将来调小页长时偏差无声通过）。
        size = min(int(kw.get("maxResults") or self.PAGE), self.PAGE)
        page = arns[start:start + size]
        resp = {"taskArns": page}
        if start + size < len(arns):
            resp["nextToken"] = str(start + size)
        return resp

    def describe_tasks(self, **kw):
        if len(kw["tasks"]) > self.PAGE:
            raise AssertionError(f"DescribeTasks 一次最多 {self.PAGE} 个 ARN，收到 {len(kw['tasks'])} 个")
        self.described.append(list(kw["tasks"]))
        out = []
        for t in self._tasks:
            if t["arn"] not in kw["tasks"]:
                continue
            container = {"name": "novaact-worker"}
            if t.get("exitCode") is not None:
                container["exitCode"] = t["exitCode"]
            scope_id = t.get("scope_id", self._scope_id)
            d = {"taskArn": t["arn"], "lastStatus": t.get("lastStatus", "RUNNING"),
                 "desiredStatus": t.get("desiredStatus", "RUNNING"), "containers": [container],
                 "overrides": {"containerOverrides": [{"environment": [{"name": "SCOPE_ID", "value": scope_id}]}]}}
            for k in ("stoppedReason", "stopCode", "executionStoppedAt", "stoppedAt"):
                if t.get(k):
                    d[k] = t[k]
            out.append(d)
        return {"tasks": out}

    def stop_task(self, **kw):
        self.stopped.append(kw)
        return {}


def _stopped_filler(n, *, exit_code=0):
    """n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。"""
    return [{"arn": f"arn:task/stopped-{i}", "lastStatus": "STOPPED", "desiredStatus": "STOPPED",
             "exitCode": exit_code, "scope_id": f"other-{i}"} for i in range(n)]


def test_handle_timeout_stops_matching_task(tmp_path, monkeypatch):
    """仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer 既有链收敛（单一真源）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path), ecs_client=ecs)
    assert r == "stopped"
    assert len(ecs.stopped) == 1
    assert reconciler.TIMEOUT_STOP_SENTINEL in ecs.stopped[0]["reason"]
    assert ecs.stopped[0]["task"] == "arn:task/1"


def test_handle_timeout_noop_when_job_terminal(tmp_path, monkeypatch):
    """到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。"""
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
    """task 无踪且无退出记录（STOPPED 事件丢投等）→ 补写一条判为超时的未知退出收敛：退出码未知、带超时标志、没有可观察的退出
    时刻（对位 local 接力恢复；「到点 invoke 顺带兜事件丢投」的落点）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    built = _timeout_built(tmp_path, claimed_at="2026-08-13T00:00:00Z")
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=_FakeEcs(task_arns=[]))
    assert r == "converged-directly"
    exits = [rec for rec in built[1].records() if rec.kind == "exit"]
    assert len(exits) == 1
    assert (exits[0].exited.exit_code, exits[0].exited.timed_out, exits[0].exited.exited_at) == (None, True, None)


def test_handle_timeout_pages_task_lists_and_batches_describe(tmp_path, monkeypatch):
    """STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。

    ECS 保留已停止的 task 约 1 小时，故一个大 run 的 STOPPED 列表轻易超过单页 100 条；只取首页会把仍在运行的
    目标判成「无踪」，把一个正常运行的 job 误判成超时。
    """
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"], tasks=_stopped_filler(120))
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path), ecs_client=ecs)
    assert r == "stopped"
    assert ecs.stopped and ecs.stopped[0]["task"] == "arn:task/1"
    assert all(len(batch) <= _FakeEcs.PAGE for batch in ecs.described)
    assert len(ecs.described) == 1  # 目标在首批就命中 → 不再往下 describe


def test_handle_timeout_finds_stopped_target_on_second_page(tmp_path, monkeypatch):
    """目标落在 STOPPED 列表第二页、且没有退出记录 → 仍按 DescribeTasks 落它的真退出码，不臆造超时。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    target = {"arn": "arn:task/target", "lastStatus": "STOPPED", "desiredStatus": "STOPPED", "exitCode": 7}
    ecs = _FakeEcs(tasks=_stopped_filler(100) + [target])
    built = _timeout_built(tmp_path)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs)
    assert r == "converged-from-describe"
    exits = [rec for rec in built[1].records() if rec.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.exit_code == 7 and exits[0].exited.timed_out is False
    assert all(len(batch) <= _FakeEcs.PAGE for batch in ecs.described)


# ---------- 到点处置先复查 deadline（ADR 0034「job timeout」节「到点不早于 deadline」条②）----------
# Scheduler 只承诺 60 秒精度，带秒的 at() 可能在 deadline 所在那一分钟的开头触发。下面几条的 job 在 10:00:00 被
# claim、预算 300 秒（`_timeout_built`），截止时刻是 10:05:00（运行期限远在其后）；时钟与等待经 now_fn / sleep_fn 注入。

_CLAIMED = "2026-11-08T10:00:00+00:00"


class _Clock:
    """注入 `_handle_timeout` 的时钟与等待：sleep 推进时钟、记下每次等了多久，可选在等待期间执行一个动作。rewind_s 依次给出每次
    等待期间系统时钟被回拨的秒数（缺省不回拨）；advance=False 时墙钟不随等待前进（出故障的系统时钟）。等待次数超过
    `MAX_SLEEPS` 即断言失败：被测的等待循环不收敛时测试报错，而不是一直等下去。"""

    MAX_SLEEPS = 1000

    def __init__(self, now: str, during_sleep=None, rewind_s=(), advance=True):
        self.t = _dt.datetime.fromisoformat(now)
        self.slept: list[float] = []
        self._during_sleep = during_sleep
        self._rewind_s = list(rewind_s)
        self._advance = advance

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.slept.append(seconds)
        if len(self.slept) > self.MAX_SLEEPS:
            raise AssertionError(f"等待了 {len(self.slept)} 次仍未返回，等待循环不收敛")
        if self._advance:
            self.t += _dt.timedelta(seconds=seconds)
        if self._rewind_s:
            self.t -= _dt.timedelta(seconds=self._rewind_s.pop(0))
        if self._during_sleep is not None:
            self._during_sleep()


def test_handle_timeout_waits_until_deadline_when_triggered_early(tmp_path, monkeypatch):
    """触发早于 deadline、剩余不超过 60 秒 → 先等到 deadline、重读状态，再停 task；等待期间尚未动 ECS。等满剩余的 45 秒醒来时读到的
    恰好是截止时刻本身，还不算已到（已到指严格晚于），再等一个固定的短时长，读到晚于截止时刻才停 task。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    stopped_during_wait: list[list] = []
    clock = _Clock("2026-11-08T10:04:15+00:00", during_sleep=lambda: stopped_during_wait.append(list(ecs.stopped)))
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1
    assert clock.slept == [45.0, reconciler._TIMEOUT_TIE_WAIT_S]  # 等到 deadline，恰好读到 deadline 时再等一次
    assert stopped_during_wait == [[], []]                         # 停 task 发生在两次等待都完成之后
    assert clock.now() > _dt.datetime.fromisoformat("2026-11-08T10:05:00+00:00")


@pytest.mark.parametrize("now, slept", [
    ("2026-11-08T10:05:00+00:00", [reconciler._TIMEOUT_TIE_WAIT_S]),
    ("2026-11-08T10:05:00.000001+00:00", []),
], ids=["exactly-at-the-cutoff", "one-microsecond-after"])
def test_handle_timeout_stops_only_after_reading_a_time_strictly_later_than_the_cutoff(tmp_path, monkeypatch, now, slept):
    """已到指读到的墙钟严格晚于截止时刻，与本机启动器的检查、投影比较退出时刻的取法相同（ADR 0054 决策二「已过」的定义）。触发时
    读到的恰好是截止时刻 10:05:00：不停 task，再等一个固定的短时长，醒来读到晚于截止时刻才停；晚 1 微秒即已到，不等待、直接停。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    stopped_during_wait: list[list] = []
    clock = _Clock(now, during_sleep=lambda: stopped_during_wait.append(list(ecs.stopped)))
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1
    assert clock.slept == slept
    assert stopped_during_wait == [[] for _ in slept]  # 等待期间没有停 task


def test_handle_timeout_does_not_loop_forever_when_the_clock_stays_at_the_cutoff(tmp_path, monkeypatch, capsys):
    """墙钟停在截止时刻、等待之后不前进（出故障的系统时钟）：每次醒来读到的都恰好是截止时刻、都不算已到。各次等待计入同一份等待额度
    （60 秒），额度用完即不停 task、不写退出记录，返回 skip-early 并打一行诊断，不在循环里一直等下去。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = _timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock("2026-11-08T10:05:00+00:00", advance=False)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early"
    assert ecs.stopped == [] and ecs.described == [] and built[1].has_exit("a") is False
    assert sum(clock.slept) <= reconciler._TIMEOUT_EARLY_WAIT_MAX_S
    assert clock.slept == [reconciler._TIMEOUT_TIE_WAIT_S] * int(
        reconciler._TIMEOUT_EARLY_WAIT_MAX_S // reconciler._TIMEOUT_TIE_WAIT_S)
    out = capsys.readouterr().out
    assert "timeout-skip: run=run-1 scope=a 读到的时刻恰好是截止时刻" in out and "已等过 60 秒仍未到" in out


@pytest.mark.parametrize("stuck_at", ["2026-11-08T10:04:59.999999+00:00", "2026-11-08T10:04:59.999000+00:00",
                                      "2026-11-08T10:04:59.500000+00:00"])
def test_handle_timeout_wait_count_is_bounded_wherever_the_clock_is_stuck(tmp_path, monkeypatch, stuck_at):
    """墙钟停在截止时刻之前不到一秒的位置：每次等待至少是固定量，等待次数不超过额度除以固定量，用完即不停 task、返回 skip-early。
    按剩余时长等待的话，剩余越小循环次数越多，每次醒来都要重读 job 状态与退出记录。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = _timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock(stuck_at, advance=False)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early"
    assert ecs.stopped == [] and built[1].has_exit("a") is False
    assert all(s >= reconciler._TIMEOUT_TIE_WAIT_S for s in clock.slept)
    assert len(clock.slept) <= reconciler._TIMEOUT_EARLY_WAIT_MAX_S / reconciler._TIMEOUT_TIE_WAIT_S
    assert sum(clock.slept) <= reconciler._TIMEOUT_EARLY_WAIT_MAX_S


def test_handle_timeout_disposes_at_once_when_deadline_passed(tmp_path, monkeypatch):
    """触发时 deadline 已过（Scheduler 在那一分钟内偏晚）→ 不等待、直接处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:05:20+00:00")
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1 and clock.slept == []


def test_handle_timeout_skips_when_triggered_more_than_a_minute_early(tmp_path, monkeypatch, capsys):
    """剩余超过 60 秒（早于 Scheduler 的文档精度）→ 不等待、不处置、不碰 ECS，打一行诊断；宁可不处置也不提前处置，
    保护交给防御扫与 status --wait。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = _timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock("2026-11-08T10:03:30+00:00")
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early"
    assert ecs.stopped == [] and ecs.described == [] and clock.slept == []
    assert built[1].has_exit("a") is False
    out = capsys.readouterr().out
    assert "timeout-skip: run=run-1 scope=a" in out and "90 秒" in out


def test_handle_timeout_skips_when_the_invocation_cannot_wait_long_enough(tmp_path, monkeypatch):
    """剩余虽在 60 秒内、却超过本次调用可等的秒数（kicker 按 Lambda 剩余时间给出）→ 同样不处置：等不到 deadline 就动手
    即是提前处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:04:20+00:00")
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   wait_budget_fn=lambda: 20.0, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early" and ecs.stopped == [] and clock.slept == []


def test_handle_timeout_samples_the_wait_budget_after_the_state_reads(tmp_path, monkeypatch):
    """等待额度临睡前才采样：复查前的读取慢时，已花掉的时间不再算进可等的额度。Lambda 剩余 70 秒、离 deadline 50 秒、
    一次读取 25 秒——提前采样会批准再等 25 秒、等完只剩 20 秒（低于处置预留）；临睡采样得到 15 秒的额度，等不到 deadline 即不处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = _timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock("2026-11-08T10:04:10+00:00")
    start = clock.now()
    store = built[2]
    real_load = store.load_run_state

    def slow_load(run_id):
        clock.t += _dt.timedelta(seconds=25)  # 慢读取：DDB 读取本身消耗本次调用的时间
        return real_load(run_id)

    monkeypatch.setattr(store, "load_run_state", slow_load)
    budget = lambda: 70.0 - (clock.now() - start).total_seconds() - reconciler._TIMEOUT_HANDLING_RESERVE_S
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs,
                                   wait_budget_fn=budget, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early" and ecs.stopped == [] and clock.slept == []


def test_handle_timeout_noop_when_job_finishes_during_wait(tmp_path, monkeypatch):
    """等待期间 job 自行结束（观察者写下退出记录）→ 等完重读即 no-op，不停 task、不改写那条真退出记录。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = _timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock("2026-11-08T10:04:30+00:00", during_sleep=lambda: built[1].record_exit("a", 0))
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "noop-exit-in-flight" and ecs.stopped == [] and clock.slept == [30.0]
    exits = {x.scope_id: x.exited for x in built[1].records() if x.kind == "exit"}
    assert exits["a"].exit_code == 0 and exits["a"].timed_out is False


def test_handle_timeout_waits_again_when_the_clock_is_turned_back_during_the_wait(tmp_path, monkeypatch):
    """等待期间系统时钟被回拨：10:04:15 触发、等 45 秒，醒来读到的是 10:04:50，还没到截止时刻 10:05:00；在这次调用的等待额度
    （60 秒）之内接着等 10 秒，醒来恰好读到截止时刻本身，仍不算已到，再等一个固定的短时长，读到晚于截止时刻才停 task。发出停止之前
    必须有一次读到已过截止时刻（ADR 0054 决策二后台推进条「截止时刻与说明」）：醒来只重查状态与退出记录、不重读时钟时，会在截止时刻
    之前 10 秒停 task。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    stopped_during_wait: list[list] = []
    clock = _Clock("2026-11-08T10:04:15+00:00", during_sleep=lambda: stopped_during_wait.append(list(ecs.stopped)),
                   rewind_s=[10.0])
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1
    assert clock.slept == [45.0, 10.0, reconciler._TIMEOUT_TIE_WAIT_S]
    assert stopped_during_wait == [[], [], []]  # 三次等待期间都没有停 task
    assert clock.now() > _dt.datetime.fromisoformat("2026-11-08T10:05:00+00:00")


def test_handle_timeout_does_not_stop_when_the_wait_quota_runs_out_before_the_cutoff(tmp_path, monkeypatch, capsys):
    """回拨之后在这次调用的等待额度之内等不到截止时刻：额度在第一次临睡前定下（60 秒与本次调用还能等的秒数取小），各次等待之和
    不超过它。只受 60 秒约束时回拨 30 秒，还要再等 30 秒，合计 75 秒；本次调用只能等 50 秒时回拨 10 秒，合计 55 秒。两种都超过额度：
    不再等待、不停 task、不写退出记录，返回 skip-early 并打一行诊断，交给之后的推进检查。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    for name, budget, rewind in (("cap", None, 30.0), ("budget", 50.0, 10.0)):
        ecs = _FakeEcs(task_arns=["arn:task/1"])
        built = _timeout_built(tmp_path / name, claimed_at=_CLAIMED)
        clock = _Clock("2026-11-08T10:04:15+00:00", rewind_s=[rewind])
        wait_budget_fn = (lambda b=budget: b) if budget is not None else None
        r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, wait_budget_fn=wait_budget_fn,
                                       now_fn=clock.now, sleep_fn=clock.sleep)
        assert r == "skip-early", name
        assert ecs.stopped == [] and ecs.described == [] and clock.slept == [45.0], name
        assert built[1].has_exit("a") is False, name
        out = capsys.readouterr().out
        assert "timeout-skip: run=run-1 scope=a" in out and "已等过 45 秒仍未到" in out, name


def test_handle_timeout_without_claimed_at_counts_as_reached(tmp_path, monkeypatch):
    """JobState 缺 claimed_at 时无从复查 → 按已到处理：不等待、照常处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:00:00+00:00")
    r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and clock.slept == []


def test_handle_timeout_treats_an_unreadable_claim_time_as_reached(tmp_path, monkeypatch):
    """认领时刻读不出或不带时区（不是本系统写出的值）时与缺认领时刻同一分支：无从复查，按已到处理，不抛到调用方。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    for i, claimed in enumerate(("2026-11-08T10:00:00", "not-a-time")):
        ecs = _FakeEcs(task_arns=["arn:task/1"])
        clock = _Clock("2026-11-08T10:00:00+00:00")
        r = reconciler._handle_timeout("run-1", "a", _timeout_built(tmp_path / str(i), claimed_at=claimed), ecs_client=ecs,
                                       now_fn=clock.now, sleep_fn=clock.sleep)
        assert r == "stopped" and clock.slept == [], claimed


# ---------- 截止时刻以运行期限封顶（ADR 0054 决策二第 2 条、后台推进条「截止时刻与说明」）----------
# job 在 10:00:00 被认领、预算 300 秒；运行期限 10:02:00 早于认领时刻加预算，截止时刻因此是 10:02:00。

_EARLY_DEADLINE = "2026-11-08T10:02:00+00:00"


def test_handle_timeout_rechecks_against_the_cutoff_capped_by_the_run_deadline(tmp_path, monkeypatch):
    """到点复查按封顶后的截止时刻：10:01:30 触发时离期限 30 秒，等过期限即停 task（只按预算算会离 10:05:00 还有 210 秒、判成过早
    而不处置；等满 30 秒恰好读到期限本身时再等一个固定的短时长）。停 task 的 reason 带哨兵串并说明是 run 的期限到了，观察者据哨兵串
    归因为超时。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:01:30+00:00")
    built = _timeout_built(tmp_path, claimed_at=_CLAIMED, deadline_at=_EARLY_DEADLINE)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and clock.slept == [30.0, reconciler._TIMEOUT_TIE_WAIT_S]
    reason = ecs.stopped[0]["reason"]
    assert reason == f"{reconciler.TIMEOUT_STOP_SENTINEL}: run deadline 2026-11-08T10:02:00+00:00 reached"
    assert reconciler.exit_from_task({"containers": [{"exitCode": 143}], "stoppedReason": reason}) == (143, True, None, None)


def test_stop_reason_names_the_cutoff_that_took_effect(tmp_path, monkeypatch):
    """停 task 的 reason 按起作用的截止时刻分别写：job 自己的预算到点仍是原有的写法，期限封顶时说明是 run 的期限；认领时刻缺失、
    无从重算时只说到了时间上限。三种都以哨兵串开头。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    reasons = {}
    for name, claimed, deadline_at in (("budget", _CLAIMED, "2999-01-01T00:00:00+00:00"),
                                       ("deadline", _CLAIMED, _EARLY_DEADLINE),
                                       ("unknown", None, _EARLY_DEADLINE)):
        ecs = _FakeEcs(task_arns=["arn:task/1"])
        clock = _Clock("2026-11-08T10:06:00+00:00")
        built = _timeout_built(tmp_path / name, claimed_at=claimed, deadline_at=deadline_at)
        assert reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now,
                                          sleep_fn=clock.sleep) == "stopped"
        reasons[name] = ecs.stopped[0]["reason"]
    sentinel = reconciler.TIMEOUT_STOP_SENTINEL
    assert reasons == {"budget": f"{sentinel}: scope exceeded 300s budget",
                       "deadline": f"{sentinel}: run deadline 2026-11-08T10:02:00+00:00 reached",
                       "unknown": f"{sentinel}: scope reached its time limit"}


def test_scan_overdue_timeouts_uses_the_cutoff_capped_by_the_run_deadline(tmp_path, monkeypatch):
    """防御扫按封顶后的截止时刻判断：认领 200 秒、预算 300 秒，只按预算算离截止还有 100 秒；运行期限已过去 150 秒，超过余量
    120 秒，于是进处置。期限只过去 100 秒时仍在余量之内，不碰。"""
    from gherkai_core.serialize import instant_to_iso
    from gherkai_runtime import compose

    calls = []
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built: calls.append(sid))
    now = compose.now()
    claimed = instant_to_iso(now - _dt.timedelta(seconds=200))
    for sub, past_s, expected in (("over", 150, ["a"]), ("within", 100, [])):
        calls.clear()
        built = _timeout_built(tmp_path / sub, claimed_at=claimed,
                               deadline_at=instant_to_iso(now - _dt.timedelta(seconds=past_s)))
        reconciler._scan_overdue_timeouts("run-1", built)
        assert calls == expected, sub


def test_kicker_bounds_the_timeout_wait_by_the_remaining_invocation_time(monkeypatch):
    """kicker 把 Lambda 剩余时间减去处置与 tick 的余裕作为可等待的上界交给处置；拿不到 context 时不加这层约束。"""
    seen: list = []
    monkeypatch.setattr(reconciler, "_build", lambda rid: ("BUILT",))
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built, **kw: seen.append(kw["wait_budget_fn"]()))
    monkeypatch.setattr(reconciler, "_tick_runs", lambda run_ids, label, prebuilt=None: {"ok": True})

    class _Ctx:
        def get_remaining_time_in_millis(self):
            return 100_000

    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, _Ctx())
    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert seen == [100.0 - reconciler._TIMEOUT_HANDLING_RESERVE_S, None]


def test_kicker_routes_timeout_scope_payload(monkeypatch):
    """Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick bonus）。"""
    calls = {}
    monkeypatch.setattr(reconciler, "_build", lambda rid: ("BUILT",))
    monkeypatch.setattr(reconciler, "_handle_timeout",
                        lambda rid, sid, built, **_kw: calls.update(handled=(rid, sid, built)))
    monkeypatch.setattr(reconciler, "_tick_runs",
                        lambda run_ids, label, prebuilt=None: calls.update(ticked=(run_ids, label, prebuilt)) or {"ok": True})
    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert calls["handled"] == ("run-1", "a", ("BUILT",))
    # timeout payload 也照常触发 tick，且把处置用的组合根经 prebuilt 交下去（同一 run 只装配一次）
    assert calls["ticked"] == ({"run-1"}, "kicker", {"run-1": ("BUILT",)})


def test_kicker_timeout_path_builds_once(monkeypatch):
    """超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文），
    处置与随后的 tick 复用同一个。tick 只 stub 掉 gherkai_core.reconcile.tick，_tick_runs 走真实实现取 prebuilt。"""
    builds = []
    monkeypatch.setattr(reconciler, "_build", lambda rid: builds.append(rid) or ("BUILT",) * 7)
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built, **_kw: "stopped")
    import gherkai_core.reconcile as _cr
    monkeypatch.setattr(_cr, "tick", lambda *a, **kw: _cr.TickOutcome.CONTINUE)
    monkeypatch.setattr(reconciler, "_scan_overdue_timeouts", lambda rid, built: None)
    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert builds == ["run-1"]


def test_kicker_timeout_path_skips_tick_when_not_detached(monkeypatch):
    """_build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。"""
    builds = []
    monkeypatch.setattr(reconciler, "_build", lambda rid: builds.append(rid) or None)
    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert builds == ["run-1"]


def test_scan_overdue_timeouts_only_over_budget(tmp_path, monkeypatch):
    """防御扫（claimed_at ②）只处置「过了截止时刻加余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at/认领时刻读不出的不碰。"""
    calls = []
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built: calls.append(sid))
    # claimed_at 在过去（相对真时钟必已超 300s 预算加余量）→ 处置
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
    # 认领时刻不带时区（不是本系统写出的值）→ 同「无起算点」，不碰、不抛
    built = _timeout_built(tmp_path / "naive", claimed_at="2026-08-13T00:00:00")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == []


def test_tick_runs_isolates_defensive_scan_failure(monkeypatch, capsys):
    """防御性超时扫抛异常不影响其它 run：本次调用仍成功返回，同一批里其它 run 照常推进（同 revision 解析失败的逐 run 隔离）。"""
    ticked = []
    monkeypatch.setattr(reconciler, "_build", lambda rid: ("BUILT",) * 7)
    import gherkai_core.reconcile as _cr
    monkeypatch.setattr(_cr, "tick", lambda run_id, *a, **kw: ticked.append(run_id) or _cr.TickOutcome.CONTINUE)

    def _boom(run_id, built):
        raise RuntimeError("DescribeTable 超时")

    monkeypatch.setattr(reconciler, "_scan_overdue_timeouts", _boom)
    result = reconciler._tick_runs({"run-1", "run-2"}, "reconciler")
    assert result["ok"] is True and sorted(result["runs"]) == ["run-1", "run-2"]
    assert sorted(ticked) == ["run-1", "run-2"]  # 一个 run 的扫失败不挡另一个 run 的推进
    assert "超时兜底检查未完成" in capsys.readouterr().out


def _stub_tick_runs_host(monkeypatch, outcome):
    """把 _tick_runs 的三个外部动作换成记录：tick 返回给定结果，记下报告生成与防御性超时扫是否被调。"""
    import gherkai_core.reconcile as _cr

    calls: list[str] = []
    monkeypatch.setattr(reconciler, "_build", lambda rid: ("BUILT",) * 7)
    monkeypatch.setattr(_cr, "tick", lambda *a, **kw: outcome)
    monkeypatch.setattr(_cr, "write_report_from_record", lambda *a, **kw: calls.append("report"))
    monkeypatch.setattr(reconciler, "_scan_overdue_timeouts", lambda rid, built: calls.append("scan"))
    return calls


class _StateStub:
    def load_run_state(self, run_id):
        return None


def test_tick_runs_branches_on_tick_outcome(monkeypatch):
    """_tick_runs 按 tick 的三种结果分支（ADR 0034 机制三「run 级状态只进不退」条④）。"""
    import gherkai_core.reconcile as _cr

    cases = [
        (_cr.TickOutcome.COMMITTED, ["report"]),  # 这一方的写使 run 成为终态：生成报告、不做超时扫
        (_cr.TickOutcome.ENDED, []),              # run 已结束而不是这一方使它结束：既不写报告、也不做超时扫
        (_cr.TickOutcome.CONTINUE, ["scan"]),     # 继续推进：只做防御性超时扫
    ]
    assert {outcome for outcome, _ in cases} == set(_cr.TickOutcome)  # 每一种结果都有一条
    for outcome, expected in cases:
        outcome_name = outcome.name
        calls = _stub_tick_runs_host(monkeypatch, outcome)
        built = ("META", "LOG", _StateStub(), "LAUNCHER", 1, "RSTORE", "PSTORE")
        result = reconciler._tick_runs({"run-1"}, "reconciler", prebuilt={"run-1": built})
        assert result == {"ok": True, "runs": ["run-1"]}, outcome_name
        assert calls == expected, outcome_name


def test_tick_runs_writes_the_report_from_the_record_when_its_tick_commits(monkeypatch):
    """这一方的写使 run 成为终态时，报告由这一方从记录生成（ADR 0034 机制三「run 级状态只进不退」条④ K2，ADR 0027「ReportStore
    接口：整 run 一次写」节）：_tick_runs 把这个 run 的运行定义、RunStore、判定存储与报告落点交给从记录生成报告的入口，tick 不交回
    明细；状态由入口读运行态取得，各 job 的明细由入口按运行态里点名的标识从判定存储读回，不另读事件重算；生成的时刻取组合根的
    墙钟。实参按入口的真实签名对位核对，传错位置即红。"""
    import inspect

    import gherkai_core.reconcile as _cr
    from gherkai_core.serialize import instant_from_iso

    real_signature = inspect.signature(_cr.write_report_from_record)
    meta = RunMeta(run_id="run-1", created_at="t0", jobs=(), deadline_at="2999-01-01T00:00:00+00:00")
    run_store = _StateStub()
    reports: list = []
    monkeypatch.setattr(_cr, "tick", lambda *a, **kw: _cr.TickOutcome.COMMITTED)
    monkeypatch.setattr(_cr, "write_report_from_record",
                        lambda *a, **kw: reports.append(real_signature.bind(*a, **kw).arguments))
    monkeypatch.setattr(reconciler, "_scan_overdue_timeouts",
                        lambda rid, built: pytest.fail("这一方使 run 成为终态时不做防御性超时扫"))
    built = (meta, "LOG", run_store, "LAUNCHER", 1, "RSTORE", "PSTORE")
    reconciler._tick_runs({"run-1"}, "reconciler", prebuilt={"run-1": built})
    [arguments] = reports
    assert set(arguments) == {"meta", "run_store", "result_store", "report_store", "created_at"}
    assert arguments["meta"] is meta and arguments["run_store"] is run_store
    assert (arguments["result_store"], arguments["report_store"]) == ("RSTORE", "PSTORE")
    instant_from_iso(arguments["created_at"])  # 记录写法的时刻（带时区），解析不了即抛


# ---------- 只推进 detached run（handler 侧分流）----------
# 同步 `run --backend cloud` 与 detached 共用同一张 events 表、同一个 cluster，而 events item / STOPPED 事件里
# 没有 detached 标记（标记只在 runs 表 STATE item 上）→ Stream/rule 层滤不掉，两个 handler 必须自己判。
# 这组用 moto 内存表运行真 handler（含真 tick/真 CAS），**正负两面都验**：非 detached 零动作、detached 照常推进
# （只验前者会放过「is_detached 恒 False」这种把整条链废掉的假绿）。

from moto import mock_aws  # noqa: E402

from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore  # noqa: E402

_RUNS_TABLE = "gherkai-runs"
_EVENTS_TABLE = "gherkai-events"
_BUCKET = "gherkai-artifacts"


@pytest.fixture
def cloud_env(monkeypatch):
    """moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。"""
    import boto3

    for k, v in {"AWS_ACCESS_KEY_ID": "testing", "AWS_SECRET_ACCESS_KEY": "testing",
                 "AWS_SESSION_TOKEN": "testing", "AWS_DEFAULT_REGION": "us-east-1"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        runs = ddb.create_table(
            TableName=_RUNS_TABLE,
            KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"},
                       {"AttributeName": "item_type", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"},
                                  {"AttributeName": "item_type", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST")
        events = ddb.create_table(
            TableName=_EVENTS_TABLE,
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"},
                       {"AttributeName": "seq", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"},
                                  {"AttributeName": "seq", "AttributeType": "N"}],
            BillingMode="PAY_PER_REQUEST")
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=_BUCKET)
        for k, v in {"REGION": "us-east-1", "RUNS_TABLE": _RUNS_TABLE, "EVENTS_TABLE": _EVENTS_TABLE,
                     "ARTIFACTS_BUCKET": _BUCKET, "CLUSTER": "gherkai-cluster", "PREFIX": "gherkai-",
                     "SUBNETS": "subnet-1", "SECURITY_GROUPS": "sg-1",
                     # 部署侧 per-run cap（IaC 现值，ADR 0034 机制四）；单 job 的用例照样只起 1 个
                     "MAX_CONCURRENCY": "4"}.items():
            monkeypatch.setenv(k, v)
        yield {"runs": runs, "events": events}


# 提交侧 preflight 解析出的 novaact worker revision ARN（ADR 0038）——**显式 revision、非 family 名**。
# 绝大多数用例只关心「推进器认不认 definition 里的这一份」，故 _seed_run 默认带上它（即打通后的正常形态）；
# 缺该字段的情形（定义违约：标 error、不解析默认指针）由下面专门那组用例显式置 None 来验。
_WORKER_REV = "arn:aws:ecs:us-east-1:000000000000:task-definition/gherkai-novaact-worker:7"
_SENTINEL = object()


def _seed_run(runs_table, *, detached: bool, max_concurrency: int | None = None,
              worker_task_defs=_SENTINEL, extra_http_headers=None, session_warmup_url=None) -> DynamoDBRunStore:
    """建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run 形态。
    `extra_http_headers` / `session_warmup_url` 是隧道模式随 definition 走的两个值（ADR 0035 决策 4、ADR 0051 决策 13）。"""
    store = DynamoDBRunStore(runs_table, detached=detached)
    job = Job(scope_id="a", scope_name="a", engine="novaact",
              scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
    if worker_task_defs is _SENTINEL:
        worker_task_defs = {"novaact": _WORKER_REV}
    store.create_run(
        RunMeta(run_id="run-1", created_at="t0", jobs=(job,), max_concurrency=max_concurrency,
                worker_variant="base" if worker_task_defs else None,
                worker_task_defs=worker_task_defs,
                extra_http_headers=tuple(extra_http_headers.items()) if extra_http_headers else None,
                session_warmup_url=session_warmup_url, deadline_at="2999-01-01T00:00:00+00:00"),
        RunState(run_id="run-1", status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)},
                 started_at="t0"))
    return store


def test_reconciler_noop_for_non_detached_run(cloud_env):
    """同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零终态写（否则与进程内 schedule 双开）。"""
    store = _seed_run(cloud_env["runs"], detached=False)
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    state = store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.PENDING   # 零认领
    assert state.status == Status.PENDING             # 零投影写、零终态写（仍是 create_run 的初态）
    # 零 launch：launch 真被调过则 tick 的失败补偿会往 events 表写一条 exit 记录（moto 无 task-def，RunTask 必失败）
    assert cloud_env["events"].scan()["Count"] == 0


def test_reconciler_ticks_detached_run(cloud_env):
    """对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、认领到那个 pending job。"""
    store = _seed_run(cloud_env["runs"], detached=True)
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING


def test_build_wires_arg_offloader_so_step_argument_bodies_read_back(cloud_env):
    """`_build` 装的 RunStore 必带 arg_offloader（ADR 0030 决定七）：META 里只留 S3 指针的 docString 正文要读得回。

    漏挂则 load_run_meta 对含指针的 META 直接 fail-loud 抛，云端推进器整条链停在装配上。写端按 submit 侧形态
    造（同桶、同 REPORT_DIR 前缀——fixture 不设 REPORT_DIR，Lambda 侧默认 `reports`）。
    """
    import boto3
    from gherkai_core.adapters.run_store.arg_offload import S3StepArgumentOffloader

    body = "第一行\n第二行"
    offloader = S3StepArgumentOffloader(boto3.client("s3", region_name="us-east-1"), _BUCKET, "reports/")
    store = DynamoDBRunStore(cloud_env["runs"], arg_offloader=offloader, detached=True)
    job = Job(scope_id="a", scope_name="a", engine="novaact",
              scenarios=(Scenario(id="a:1", name="s",
                                  steps=(Step(0, "Given", "x",
                                              argument=StepArgument(kind="docString", content=body)),)),), timeout_s=300.0)
    store.create_run(
        RunMeta(run_id="run-1", created_at="t0", jobs=(job,), worker_variant="base",
                worker_task_defs={"novaact": _WORKER_REV}, deadline_at="2999-01-01T00:00:00+00:00"),
        RunState(run_id="run-1", status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)},
                 started_at="t0"))

    built = reconciler._build("run-1")
    assert built is not None
    meta = built[0]
    assert meta.jobs[0].scenarios[0].steps[0].argument.content == body


def test_build_reuses_its_own_handles_and_builds_no_new_client(cloud_env, monkeypatch):
    """`_build` 的三层 store 全用它自己已建的那批句柄装配——compose 里建句柄的两个钩子在此一次都不该执行。

    这条同时是「region 不必传给 `build_cloud_stores`」的前提：region 在那边的唯一消费者就是这两个钩子。
    退回手工重造装配、或漏掉句柄注入，本用例即红（钩子被叫到就抛）。
    """
    from gherkai_runtime import compose

    def _boom(*a, **kw):
        raise AssertionError("句柄已注入，装配不该再建 client")

    monkeypatch.setattr(compose, "_make_ddb_table", _boom)
    monkeypatch.setattr(compose, "_make_s3_client", _boom)
    _seed_run(cloud_env["runs"], detached=True)

    built = reconciler._build("run-1")

    assert built is not None
    assert built[0].run_id == "run-1"   # META 真读回来了（装配可用，不是「钩子没执行因为整条路都没走」）


# ---------- 已收尾的 run 再被触发时 handler 整体 no-op（判定真值销毁的第二道闸）----------

# 预置的那一份判定明细的标识（形态同 named_details.new_result_id：16 个小写十六进制字符）
_SEEDED_RESULT_ID = "5eed5eed5eed5eed"


def _seed_finished_run(cloud_env, *, status=Status.PASSED):
    """造「run 已收尾 + events 表只剩永不过期的退出记录」的形态，即 worker 事件被 TTL 删掉约 7 天后的真实样子，
    并预置那时已在 S3 的一份判定明细（键只由标识构成）与报告；job 已是终态时它的终态点名这一份，仍在执行时不点名。返回 (store, s3 client)。"""
    import boto3
    from gherkai_core.adapters.event_log import DdbEventLog
    from gherkai_core.model import TERMINAL_STATUSES

    store = DynamoDBRunStore(cloud_env["runs"], detached=True)
    job = Job(scope_id="a", scope_name="a", engine="novaact",
              scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
    named = _SEEDED_RESULT_ID if status in TERMINAL_STATUSES else None
    store.create_run(
        RunMeta(run_id="run-1", created_at="t0", jobs=(job,), worker_task_defs={"novaact": _WORKER_REV}, deadline_at="2999-01-01T00:00:00+00:00"),
        RunState(run_id="run-1", status=status,
                 jobs={"a": JobState("a", status, claimed_at="2026-09-01T00:00:00+00:00", result_id=named)},
                 started_at="2026-09-01T00:00:00+00:00", ended_at="2026-09-01T00:03:00+00:00"))
    DdbEventLog(cloud_env["events"], "run-1", ["a"]).record_exit("a", 0)  # 不带 expires_at：退出记录永不过期
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket=_BUCKET, Key=f"reports/run-1/jobs/{_SEEDED_RESULT_ID}.json", Body=b'{"status": "passed"}')
    s3.put_object(Bucket=_BUCKET, Key="reports/run-1/index.html", Body=b"<html>passed</html>")
    return store, s3


def _report_bytes(s3) -> dict[str, bytes]:
    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=_BUCKET, Prefix="reports/run-1/").get("Contents", [])]
    return {k: s3.get_object(Bucket=_BUCKET, Key=k)["Body"].read() for k in keys}


def test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(cloud_env):
    """已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体
    no-op：判定真值 jobs/*.json 与报告 index.html **字节不变**。

    已收尾的 run 被重放推演的后果（那时 events 表只剩退出记录）见 ADR 0034 端到端流程 cloud 一节「已收尾的 run 不再推演」条。
    """
    store, s3 = _seed_finished_run(cloud_env)
    before = _report_bytes(s3)
    assert before, "预置报告没落进桶，断言会空转"

    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    reconciler.kicker_handler({"run_id": "run-1"}, None)

    assert _report_bytes(s3) == before          # 判定真值与报告一个字节没动
    assert store.load_run_state("run-1").status == Status.PASSED
    assert cloud_env["events"].scan()["Count"] == 1  # 零补偿写（launch 没被调过）


def test_finished_run_gate_keys_on_the_committed_run_status_only(cloud_env):
    """对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物）
    但 run 级仍 running（提交点还没落）时照常推进到收尾，说明挡住的是「已提交」而不是「有终态 job」。"""
    store, s3 = _seed_finished_run(cloud_env, status=Status.RUNNING)
    before = _report_bytes(s3)
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    assert store.load_run_state("run-1").status == Status.ERROR  # 本 tick 真实运行到终态写（exit=0 无 scope_done → error）
    assert _report_bytes(s3) != before                           # 判定真值与报告由本 tick 写出


def test_timeout_payload_on_a_finished_run_is_a_noop(cloud_env):
    """超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写
    （ADR 0034「job timeout」节「到点时 job 已终态 → tick no-op」）。"""
    _store, s3 = _seed_finished_run(cloud_env)
    before = _report_bytes(s3)
    out = reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert out["ok"] and _report_bytes(s3) == before


# ---------- 终态写之后为生成报告而读记录，失败不许击穿已到终态的 run（ADR 0030 决定三 / 0034 收尾）----------

def test_handler_returns_normally_when_the_record_read_for_the_report_fails(cloud_env, monkeypatch):
    """报告从记录组装，为生成而读 RunState 的那一次在这一方的终态写**之后**——那次强一致读抛（DDB 限流 / 瞬时 5xx）不许冒泡：
    终态写之后的失败无人重试，且在云端会让 events Stream 本批重试耗尽后整批丢弃，同批其它 run 的事件随之丢失（ADR 0034
    「端到端流程」cloud 第 ④ 步）。断言 handler 正常返回；判定明细与终态已落；读不到记录就不生成报告。
    """
    import boto3

    # 让 run 一 tick 就 done：job 已 CAS 成 running、events 表已有它的退出记录 → 本 tick 推成终态 → 终态写
    store = DynamoDBRunStore(cloud_env["runs"], detached=True)
    job = Job(scope_id="a", scope_name="a", engine="novaact",
              scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
    store.create_run(
        RunMeta(run_id="run-1", created_at="t0", jobs=(job,), worker_task_defs={"novaact": _WORKER_REV}, deadline_at="2999-01-01T00:00:00+00:00"),
        RunState(run_id="run-1", status=Status.RUNNING,
                 jobs={"a": JobState("a", Status.RUNNING, claimed_at="2026-09-01T00:00:00+00:00")},
                 started_at="2026-09-01T00:00:00+00:00"))
    from gherkai_core.adapters.event_log import DdbEventLog
    DdbEventLog(cloud_env["events"], "run-1", ["a"]).record_exit("a", 0)

    # 只让终态写**之后**的那次读抛（终态写之前的读是 tick 的正常输入，抛了就不是本用例要验的路径）
    real_load, real_commit = DynamoDBRunStore.load_run_state, DynamoDBRunStore.commit_job_states
    committed: list = []
    raised: list[str] = []

    def load(self, run_id):
        if committed:
            raised.append(run_id)
            raise RuntimeError("DDB 限流")
        return real_load(self, run_id)

    def commit_job_states(self, *a, **kw):
        out = real_commit(self, *a, **kw)
        committed.append(out)
        return out

    monkeypatch.setattr(DynamoDBRunStore, "load_run_state", load)
    monkeypatch.setattr(DynamoDBRunStore, "commit_job_states", commit_job_states)

    out = reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)

    assert out == {"ok": True, "runs": ["run-1"]}       # 不抛 → Stream 本批不重试、不整批丢弃
    assert len(committed) == 1, "run 没有走到终态写，断言会空转"
    assert raised == ["run-1"]                          # 失败确实落在为生成报告而读的那一次上
    recorded = real_load(store, "run-1")
    assert recorded.status == Status.ERROR  # 终态已落（exit=0 无 scope_done → error）
    s3 = boto3.client("s3", region_name="us-east-1")
    result_id = recorded.jobs["a"].result_id  # 终态点名的那一份判定明细在终态写之前已落，键只由标识构成
    assert result_id is not None
    assert s3.get_object(Bucket=_BUCKET, Key=f"reports/run-1/jobs/{result_id}.json")["Body"].read()
    listed = s3.list_objects_v2(Bucket=_BUCKET, Prefix="reports/run-1/index.html").get("Contents", [])
    assert listed == []                                 # 读不到记录就不生成报告


# ---------- 并发上限取 min(meta, 部署侧 cap)（ADR 0034 机制四）----------

def test_build_takes_meta_max_concurrency_under_cap(cloud_env):
    """definition 声明 ≤ cap → 按 definition 走（打通前云端后端静默忽略提交侧声明，是可用性缺陷）。"""
    _seed_run(cloud_env["runs"], detached=True, max_concurrency=2)  # cap=4（fixture env）
    assert reconciler._build("run-1")[4] == 2


def test_build_clamps_meta_max_concurrency_to_cap(cloud_env, monkeypatch):
    """definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。"""
    monkeypatch.setenv("MAX_CONCURRENCY", "2")
    _seed_run(cloud_env["runs"], detached=True, max_concurrency=9)
    assert reconciler._build("run-1")[4] == 2


def test_build_defaults_to_one_when_meta_missing(cloud_env):
    """meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。"""
    _seed_run(cloud_env["runs"], detached=True, max_concurrency=None)
    assert reconciler._build("run-1")[4] == 1


def test_build_cap_defaults_to_one_when_env_absent(cloud_env, monkeypatch):
    """cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。

    **meta 必须声明 >1** 才验得动这条：meta 无值时 min(1, cap) 恒 1，缺省是 1 还是 4 都绿（非判别性断言）；
    声明 9 时 min 完全由缺省决定——回 1 则 1、若哪天缺省又被写成部署值 4 则 4，断言才真兜住。
    """
    monkeypatch.delenv("MAX_CONCURRENCY", raising=False)
    _seed_run(cloud_env["runs"], detached=True, max_concurrency=9)
    assert reconciler._build("run-1")[4] == 1


def test_exit_observer_skips_non_detached_run(cloud_env):
    """同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。"""
    _seed_run(cloud_env["runs"], detached=False)
    r = exit_observer.handler({"detail": _stopped_detail("run-1", "a", 0)}, None)
    assert r.get("skipped") is True
    assert cloud_env["events"].scan()["Count"] == 0


def test_exit_observer_records_exit_for_detached_run(cloud_env):
    """对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。"""
    _seed_run(cloud_env["runs"], detached=True)
    r = exit_observer.handler({"detail": _stopped_detail("run-1", "a", 0)}, None)
    assert r.get("ok") is True
    items = cloud_env["events"].scan()["Items"]
    assert len(items) == 1 and items[0]["item_type"] == "exit"


def test_reconciler_writes_timestamps_in_compose_clock_format(cloud_env):
    """推进器 Lambda 落库的时间戳格式是 `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。

    曾在本文件自带 `_now_iso`（`strftime` 的 `…Z`），与 submit 侧 `compose.now_iso`（`isoformat` 的 `+00:00`）
    并存 → 同一份 RunState 内 started_at 与 claimed_at 格式不同、`status --json` 机读消费者要兼容两种。
    """
    from gherkai_core.serialize import instant_from_iso

    store = _seed_run(cloud_env["runs"], detached=True)
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    claimed_at = store.load_run_state("run-1").jobs["a"].claimed_at
    assert claimed_at, "tick 没写 claimed_at，断言会空转"
    # 逐字比对「解析回来再 isoformat 是否原样」——退回 `…Z` 写法即失败
    assert claimed_at == instant_from_iso(claimed_at).isoformat()


# ---------- worker task-def revision：只来自 definition，缺即定义违约标 error（ADR 0038、0037 决策 7）----------
# 不变量「运行时只用 definition 里的显式 revision，永不用 family 取最新」的 handler 侧落点。**正负两面都验**：
# 正面验原样用 definition、不看 SSM 默认指针；反面验缺字段不回落默认指针而是标 error。
# 真 RunTask 吃这个 ARN 起得来要真账号，是 moto 之外的边界（ADR 0038「实测项」）。

def _seed_worker_ssm(*, version: str = "1.4.0", variant: str = "base", engine: str = "novaact",
                     revision_arn: str = "arn:compat-rev:1"):
    """把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。"""
    import json

    import boto3
    from gherkai_runtime import names

    ssm = boto3.client("ssm", region_name="us-east-1")
    ssm.put_parameter(Name=names.ssm_path("gherkai-", "version"), Value=version,
                      Type="String", Overwrite=True)
    ssm.put_parameter(Name=names.ssm_path("gherkai-", names.WORKER_DEFAULT_KEY), Value=variant,
                      Type="String", Overwrite=True)
    ssm.put_parameter(
        Name=names.ssm_path("gherkai-", names.worker_image_key(engine, names.image_tag(version, variant))),
        Value=json.dumps({"template_arn": "arn:tpl:1", "revision_arn": revision_arn,
                          "digest": "sha256:" + "a" * 64, "pushed_at": "2026-09-08T00:00:00Z"}),
        Type="String", Overwrite=True)
    return revision_arn


def test_build_uses_definition_worker_task_defs_verbatim(cloud_env):
    """definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。

    SSM 里故意放一个**不同**的 revision：若实现悄悄走了兼容路径，断言会立刻抓到。
    """
    _seed_worker_ssm(revision_arn="arn:should-not-be-used:1")
    _seed_run(cloud_env["runs"], detached=True)
    engines = reconciler._build("run-1")[3]._resolver("novaact")
    assert engines._task_def == _WORKER_REV


def test_build_hands_the_deployed_fargate_config_to_the_worker_task(cloud_env, monkeypatch):
    """推进器是起 worker task 的唯一装配方（ADR 0016 决策 C）：IaC 注入的 cluster、events 表、桶、报告前缀、子网、安全组、
    assignPublicIp 与 region 经 `_build` 原样到达 RunTask 与 worker 的环境变量，job 对象落在 RunTask 指给 worker 的位置。

    经 launcher 起一次 job、看 RunTask 收到什么（ECS 换成记录调用的假 client，S3 用 moto）。子网给两个，顺带验逗号拆分；
    ASSIGN_PUBLIC_IP 与 REPORT_DIR 给出不同于缺省的值，漏读环境变量即红。"""
    import json

    import boto3

    class _RecordingEcs:
        def __init__(self) -> None:
            self.run_task_calls: list[dict] = []

        def run_task(self, **kw):
            self.run_task_calls.append(kw)
            return {"tasks": [{"taskArn": "arn:aws:ecs:us-east-1:000000000000:task/gherkai-cluster/t1"}], "failures": []}

    ecs = _RecordingEcs()
    ecs_regions: list = []
    real_client = boto3.client

    def _client(service, *a, **kw):
        if service == "ecs":
            ecs_regions.append(kw.get("region_name"))
            return ecs
        return real_client(service, *a, **kw)

    monkeypatch.setattr(boto3, "client", _client)
    monkeypatch.setenv("SUBNETS", "subnet-1,subnet-2")
    monkeypatch.setenv("ASSIGN_PUBLIC_IP", "DISABLED")
    monkeypatch.setenv("REPORT_DIR", "team/reports")
    _seed_run(cloud_env["runs"], detached=True)

    built = reconciler._build("run-1")
    meta, launcher = built[0], built[3]
    launcher.launch(meta.jobs[0], cutoff_at=_dt.datetime(2999, 1, 1, tzinfo=_dt.timezone.utc))

    assert ecs_regions == ["us-east-1"]
    (call,) = ecs.run_task_calls
    assert call["cluster"] == "gherkai-cluster"
    assert call["taskDefinition"] == _WORKER_REV
    assert call["networkConfiguration"] == {"awsvpcConfiguration": {
        "subnets": ["subnet-1", "subnet-2"], "securityGroups": ["sg-1"], "assignPublicIp": "DISABLED"}}
    (override,) = call["overrides"]["containerOverrides"]
    env = {e["name"]: e["value"] for e in override["environment"]}
    assert env["EVENTS_DDB_TABLE"] == _EVENTS_TABLE
    assert env["RUN_ID"] == "run-1" and env["SCOPE_ID"] == "a"
    assert env["AWS_REGION"] == "us-east-1"
    assert (env["ARTIFACT_S3_BUCKET"], env["ARTIFACT_S3_PREFIX"]) == (_BUCKET, "team/reports/run-1/")
    assert env["JOB_S3_URI"] == f"s3://{_BUCKET}/team/reports/run-1/jobs-in/a.json"
    # RunTask 指给 worker 的 job 对象确实写在那里（worker 只按这个地址读）
    body = real_client("s3", region_name="us-east-1").get_object(
        Bucket=_BUCKET, Key="team/reports/run-1/jobs-in/a.json")["Body"].read().decode("utf-8")
    assert json.loads(body)["scope"]["id"] == "a"


def test_build_reads_session_warmup_url_back_into_worker_env(cloud_env):
    """云端推进器从 definition 读回预热地址（ADR 0051 决策 13）：与额外请求头一起进 FargateEngine 的附加 env、经 RunTask overrides
    到容器——容器不继承任何宿主 env，漏接这一处 worker 就按 definition 完整性判 precheck_failed，而本机单测里没有别的东西能暴露它。"""
    import json as _json

    url = "https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "a" * 32
    _seed_run(cloud_env["runs"], detached=True, extra_http_headers={"ngrok-skip-browser-warning": "1"}, session_warmup_url=url)
    env = reconciler._build("run-1")[3]._resolver("novaact")._extra_env
    assert env["GHERKAI_SESSION_WARMUP_URL"] == url
    assert _json.loads(env["GHERKAI_EXTRA_HTTP_HEADERS"]) == {"ngrok-skip-browser-warning": "1"}


def test_build_without_tunnel_injects_no_warmup_env(cloud_env):
    """对偶：不经隧道的 run 不出现预热地址与额外请求头两个键（worker 以「有请求头没预热地址」判 definition 不完整，所以两键必须同在同缺）。"""
    _seed_run(cloud_env["runs"], detached=True)
    env = reconciler._build("run-1")[3]._resolver("novaact")._extra_env
    assert "GHERKAI_SESSION_WARMUP_URL" not in env and "GHERKAI_EXTRA_HTTP_HEADERS" not in env


@pytest.mark.parametrize("claimed", [False, True], ids=["pending-job", "running-job"])
def test_build_ends_the_run_with_the_error_ending_when_definition_lacks_worker_task_defs(cloud_env, capsys, claimed):
    """云端 definition 缺 worker_task_defs 是定义违约（ADR 0037 决策 7 不留兼容分支）：不按默认指针解析、不推进，记诊断，以结束写的
    error 变体结束 run（ADR 0031 决定三「结束写」小节「运行定义不可用时」条）：没有启动的与执行中的 job 都记 error，run 级与 job 级
    说明都是同一句原因，与本机后台推进进程同一句；这一写不生成报告。"""
    import boto3
    from gherkai_core.run_status import NO_WORKER_IMAGES_REASON

    _seed_worker_ssm(variant="login", revision_arn="arn:must-not-be-used:9")
    store = _seed_run(cloud_env["runs"], detached=True, worker_task_defs=None)
    if claimed:
        assert store.try_claim_job("run-1", "a", claimed_at="2026-09-01T00:00:00+00:00") is True
    assert reconciler._build("run-1") is None
    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.ERROR, NO_WORKER_IMAGES_REASON)
    assert (state.jobs["a"].status, state.jobs["a"].message) == (Status.ERROR, NO_WORKER_IMAGES_REASON)
    assert state.ended_at is not None
    out = capsys.readouterr().out
    assert "不推进、标为 error" in out and "worker-compat" not in out
    listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(Bucket=_BUCKET, Prefix="reports/run-1/")
    assert listed.get("Contents", []) == []  # 不存明细、不生成报告


def test_load_definition_ends_the_run_on_schema_or_contract_violation_and_passes_good_ones(capsys):
    """结构版本不是本后端认的、定义形态违约、缺 worker_task_defs：以结束写的 error 变体结束 run（`end_run` 收到运行定义不可用的变体，
    原因是 run_status 里的那一句）、记诊断、返回 None；正常 definition 原样返回；不存在的 run 忽略、不写。"""
    from gherkai_core.errors import DefinitionContractError, UnsupportedDefinitionSchema
    from gherkai_core.model import RunMeta
    from gherkai_core.run_status import DEFINITION_CONTRACT_REASON, NO_WORKER_IMAGES_REASON, schema_mismatch_reason
    from gherkai_core.serialize import instant_from_iso

    class _Store:
        def __init__(self, *, exc=None, meta=None, state_exists=True):
            self.exc, self.meta, self.ended, self.state_exists = exc, meta, [], state_exists

        def load_run_meta(self, run_id):
            if self.exc is not None:
                raise self.exc
            return self.meta

        def end_run(self, run_id, ending, *, ended_at):
            instant_from_iso(ended_at)  # 记录写法的时刻，解析不了即抛
            if not self.state_exists:
                return False  # 运行态不在（或 run 已结束）：结束写不成立
            self.ended.append((run_id, ending.definition_unavailable, ending.ends_running_jobs))
            self.message = ending.run_message
            return True

    unavailable = [("r", True, True)]
    s = _Store(exc=UnsupportedDefinitionSchema(2, 1, cli_version="9.9.0"))
    assert reconciler._load_definition(s, "r") is None and s.ended == unavailable
    out = capsys.readouterr().out
    assert "9.9.0" in out and out.startswith("reject: run r ")  # 诊断行按事件种类起前缀，与 skip: / timeout-stop: 同一风格
    # run 级说明随终态写入、status 可见：产品语言整句（谁写的、两边各第几版、怎么办），不是异常原文
    assert s.message == schema_mismatch_reason(2, 1, "9.9.0")
    assert s.message.startswith("提交记录由更新版本的 gherkai 9.9.0 写出") and "第 2 版" in s.message and "重新提交" in s.message
    s2 = _Store(exc=DefinitionContractError("definition 里的 job 缺键 target"))
    assert reconciler._load_definition(s2, "r") is None and s2.ended == unavailable
    assert s2.message == DEFINITION_CONTRACT_REASON and "缺键 target" not in s2.message  # 契约异常的原文只进诊断行
    assert "缺键 target" in capsys.readouterr().out
    s_old = _Store(exc=UnsupportedDefinitionSchema(0, 1, cli_version="1.4.9"))
    assert reconciler._load_definition(s_old, "r") is None and s_old.message.startswith("提交记录由更早版本的 gherkai 1.4.9 写出")
    # 写端版本来自提交记录、不受信：损坏成超长文本也不能把说明撑大（ADR 0037 决策 7「有界」）
    s_long = _Store(exc=UnsupportedDefinitionSchema(2, 1, cli_version="v" * 5000))
    reconciler._load_definition(s_long, "r")
    assert len(s_long.message) < 300 and "v" * 41 not in s_long.message and "v" * 40 in s_long.message
    s3 = _Store(meta=RunMeta(run_id="r", created_at="t", jobs=(), deadline_at="2999-01-01T00:00:00+00:00"))
    assert reconciler._load_definition(s3, "r") is None and s3.ended == unavailable
    assert s3.message == NO_WORKER_IMAGES_REASON
    ok = RunMeta(run_id="r", created_at="t", jobs=(), worker_task_defs={"novaact": "arn:rev:1"}, deadline_at="2999-01-01T00:00:00+00:00")
    s4 = _Store(meta=ok)
    assert reconciler._load_definition(s4, "r") is ok and s4.ended == []
    # 提交记录不在而运行态在（记录被删去）：与形态违约同样以 error 结束，原因用同一句
    capsys.readouterr()
    s5 = _Store(meta=None)
    assert reconciler._load_definition(s5, "r") is None and s5.ended == unavailable
    assert s5.message == DEFINITION_CONTRACT_REASON
    assert capsys.readouterr().out.startswith("reject: run r ")
    # 运行态也不在（不属于这张表的 run、已被清理的 run）：结束写不成立，什么都不做、不打诊断行
    s6 = _Store(meta=None, state_exists=False)
    assert reconciler._load_definition(s6, "r") is None and s6.ended == [] and capsys.readouterr().out == ""


def test_kicker_uses_definition_worker_task_defs(cloud_env):
    """kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。"""
    _seed_worker_ssm(revision_arn="arn:should-not-be-used:1")
    store = _seed_run(cloud_env["runs"], detached=True)
    reconciler.kicker_handler({"run_id": "run-1"}, None)
    assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING  # 真 tick 运行到认领


def test_run_ids_scope_id_containing_hash_is_split_from_the_left():
    """scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条
    events Stream 会被抽成错的 run_id、reconciler 静默 no-op（主推进链断）。"""
    event = {"Records": [_stream_record("20260909T000000Z-a3f9c1#checkout#step-2")]}
    assert reconciler._run_ids_from_stream(event) == {"20260909T000000Z-a3f9c1"}


def test_handle_timeout_leaves_a_stopping_task_to_the_observer(tmp_path, monkeypatch):
    """task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING 列表里，但**不是**无踪：不动、
    不直写，等观察者的真退出记录（ADR 0034「job timeout」节）。曾按 RUNNING 列表判「无踪」直写 timed_out，与几秒后
    到达的真退出记录同键互覆——恰在预算点运行结束的 passed job 可被终判成 timeout。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(tasks=[{"arn": "arn:task/1", "lastStatus": "DEPROVISIONING", "desiredStatus": "STOPPED"}])
    built = _timeout_built(tmp_path)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs)
    assert r == "noop-stopping" and ecs.stopped == []
    assert built[1].has_exit("a") is False  # 没直写


def test_handle_timeout_converges_from_describe_when_task_already_stopped(tmp_path, monkeypatch):
    """task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录
    （exit 0、非 timed_out、带 task 的执行停止时刻），不臆造 timeout；迟到的观察者写同内容同键、幂等。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    stopped_at = _dt.datetime(2026, 11, 8, 10, 4, 59, tzinfo=_dt.timezone.utc)
    ecs = _FakeEcs(tasks=[{"arn": "arn:task/1", "lastStatus": "STOPPED", "desiredStatus": "STOPPED",
                           "exitCode": 0, "stoppedReason": "Essential container in task exited",
                           "executionStoppedAt": stopped_at}])
    built = _timeout_built(tmp_path)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs)
    assert r == "converged-from-describe" and ecs.stopped == []
    exits = {x.scope_id: x.exited for x in built[1].records() if x.kind == "exit"}
    assert exits["a"].exit_code == 0 and exits["a"].timed_out is False and exits["a"].reason is None
    assert exits["a"].exited_at == stopped_at


def test_handle_timeout_converges_from_describe_keeps_timeout_attribution_of_own_stop(tmp_path, monkeypatch):
    """上一轮已 StopTask（stoppedReason 带哨兵）、事件丢投、本轮再扫到它已 STOPPED → 落记录仍归因 timeout。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(tasks=[{"arn": "arn:task/1", "lastStatus": "STOPPED", "desiredStatus": "STOPPED",
                           "exitCode": 143, "stoppedReason": f"{reconciler.TIMEOUT_STOP_SENTINEL}: scope exceeded 300s budget"}])
    built = _timeout_built(tmp_path)
    assert reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs) == "converged-from-describe"
    exits = {x.scope_id: x.exited for x in built[1].records() if x.kind == "exit"}
    assert exits["a"].exit_code == 143 and exits["a"].timed_out is True


def test_exit_from_task_is_shared_by_observer_and_timeout_handler():
    """同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out, reason, exited_at)——同键幂等的前提。
    容器没能开始运行的 task 没有执行停止时刻，退出时刻取 ECS 记下 task 已停止的时刻。"""
    detail = _stopped_detail("run-1", "a", 0)
    detail["containers"] = [{"name": "novaact-worker"}]
    detail["stopCode"] = "TaskFailedToStart"
    detail["stoppedReason"] = "CannotPullContainerError: not found"
    detail["stoppedAt"] = "2026-11-08T10:05:03.100Z"
    _r, _s, ec, to, reason, at = exit_observer._extract(detail)
    assert (ec, to, reason, at) == reconciler.exit_from_task(detail)
    assert reason == "TaskFailedToStart: CannotPullContainerError: not found"
    assert at == _ECS_STOPPED


# ---------- 退出时刻（ADR 0054 决策二后台推进条「截止时刻与说明」、实测项 10 到 12）----------
# 退出记录带 task 的执行停止时刻，是否已过截止时刻由投影判断。同一个时刻在两种来源里形态不同：STOPPED 事件的 detail 里是 ISO 串，
# DescribeTasks 的应答经 botocore 解析之后是带本机时区的 datetime（ECS 的 JSON 协议里传的是纪元秒）。下面几条的 job 在 10:00:00 被
# 认领、预算 300 秒，截止时刻是 10:05:00。

_EXEC_STOPPED = _dt.datetime(2026, 11, 8, 10, 5, 1, 473000, tzinfo=_dt.timezone.utc)  # 容器实际停下的时刻
_ECS_STOPPED = _dt.datetime(2026, 11, 8, 10, 5, 3, 100000, tzinfo=_dt.timezone.utc)  # ECS 记下 task 已停止的时刻


def _iso_z(t: _dt.datetime) -> str:
    """STOPPED 事件 detail 里时刻的写法：UTC、毫秒、以 Z 结尾。"""
    return t.astimezone(_dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _detail_with_times(exit_code, *, execution_stopped=_EXEC_STOPPED, stopped=_ECS_STOPPED):
    detail = _stopped_detail("run-1", "a", exit_code)
    if execution_stopped is not None:
        detail["executionStoppedAt"] = _iso_z(execution_stopped)
    if stopped is not None:
        detail["stoppedAt"] = _iso_z(stopped)
    return detail


def _described(detail: dict) -> dict:
    """同一个 task 经 DescribeTasks 取回的形态：把 detail 按 ECS 的 JSON 协议编码（时刻写成纪元秒），再交给 botocore 的应答解析器。"""
    import json

    import botocore.session
    from botocore import parsers

    task = dict(detail)
    for key in ("executionStoppedAt", "stoppedAt"):
        if key in task:
            task[key] = _dt.datetime.fromisoformat(task[key]).timestamp()
    model = botocore.session.get_session().get_service_model("ecs")
    parsed = parsers.create_parser(model.metadata["protocol"]).parse(
        {"status_code": 200, "headers": {}, "body": json.dumps({"tasks": [task]}).encode()},
        model.operation_model("DescribeTasks").output_shape)
    return parsed["tasks"][0]


def test_exit_from_task_reads_one_exit_time_from_the_event_and_from_describe_tasks():
    """实测项 10 的本地一半：同一个已停止的 task，从 STOPPED 事件与从 DescribeTasks 取到同一个退出时刻（执行停止时刻），写进记录的
    ISO 串也相同。不带时区的 datetime（SDK 返回的对象）按 UTC；没有执行停止时刻时取 ECS 记下停止的时刻；都没有或读不出时不带退出时刻。"""
    from gherkai_core.serialize import instant_to_iso

    detail = _detail_with_times(3)
    described = _described(detail)
    assert isinstance(described["executionStoppedAt"], _dt.datetime)  # 查询形态确实是 datetime，不是串
    from_event, from_query = reconciler.exit_from_task(detail), reconciler.exit_from_task(described)
    assert from_event == from_query == (3, False, None, _EXEC_STOPPED)
    assert instant_to_iso(from_event[3]) == instant_to_iso(from_query[3]) == "2026-11-08T10:05:01.473000+00:00"
    naive = dict(described, executionStoppedAt=_EXEC_STOPPED.replace(tzinfo=None))
    assert reconciler.exit_from_task(naive)[3] == _EXEC_STOPPED
    assert reconciler.exit_from_task(_detail_with_times(3, execution_stopped=None))[3] == _ECS_STOPPED
    assert reconciler.exit_from_task(dict(detail, executionStoppedAt="不是时刻"))[3] == _ECS_STOPPED
    assert reconciler.exit_from_task(_detail_with_times(3, execution_stopped=None, stopped=None))[3] is None


def test_exit_from_task_skips_a_time_string_without_a_time_zone():
    """时刻串与记录里的时刻经同一处严格解析（`serialize.instant_from_iso`）：不带时区的串当作这个字段没有值，按次序取下一个字段，
    不补成 UTC（串里没写时区，补哪个时区都是猜）。两个字段都只有不带时区的串时不带退出时刻。"""
    naive_exec = _EXEC_STOPPED.replace(tzinfo=None).isoformat()  # "2026-11-08T10:05:01.473000"
    detail = dict(_detail_with_times(3), executionStoppedAt=naive_exec)
    assert reconciler.exit_from_task(detail)[3] == _ECS_STOPPED
    both_naive = dict(detail, stoppedAt=_ECS_STOPPED.replace(tzinfo=None).isoformat())
    assert reconciler.exit_from_task(both_naive)[3] is None


def _claimed_detached_run(cloud_env):
    """moto 上的后台 run：job a 已在 10:00:00 被认领。"""
    store = _seed_run(cloud_env["runs"], detached=True)
    assert store.try_claim_job("run-1", "a", claimed_at=_CLAIMED) is True
    return store


def _exit_item(cloud_env) -> dict:
    from gherkai_core.adapters.fargate_engine import EXIT_SK, events_pk

    return cloud_env["events"].get_item(Key={"pk": events_pk("run-1", "a"), "seq": EXIT_SK})["Item"]


def test_late_observer_rewrites_the_exit_record_from_describe_tasks_unchanged(cloud_env):
    """实测项 10 的本地一半（moto）：STOPPED 事件迟到时，超时处置先从 DescribeTasks 的 task 对象写下退出记录，观察者随后从事件写同一
    条记录，写入前后内容相同（含退出时刻）。"""
    _claimed_detached_run(cloud_env)
    detail = _detail_with_times(3)
    described = _described(detail)
    ecs = _FakeEcs(tasks=[{"arn": detail["taskArn"], "lastStatus": "STOPPED", "desiredStatus": "STOPPED", "exitCode": 3,
                           "executionStoppedAt": described["executionStoppedAt"], "stoppedAt": described["stoppedAt"]}])
    clock = _Clock("2026-11-08T10:06:00+00:00")
    built = reconciler._build("run-1")
    assert reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now,
                                      sleep_fn=clock.sleep) == "converged-from-describe"
    from_describe = _exit_item(cloud_env)
    assert from_describe["exited_at"] == "2026-11-08T10:05:01.473000+00:00"
    out = exit_observer.handler({"detail": detail}, None)
    assert out["ok"] is True and out["exited_at"] == "2026-11-08T10:05:01.473000+00:00"
    assert _exit_item(cloud_env) == from_describe


_JUDGED_TIMEOUT = ("error", "timeout", "job 超时（预算 300s，已中止）")
_JUDGED_ENGINE_ERROR = ("error", "engine_error", "worker 非正常退出（退出码 3；事件流里没有失败原因——详见 worker 日志）")


@pytest.mark.parametrize("execution_stopped, stopped, expected", [
    ("2026-11-08T10:05:01.000Z", _iso_z(_ECS_STOPPED), _JUDGED_TIMEOUT),
    ("2026-11-08T10:04:59.000Z", _iso_z(_ECS_STOPPED), _JUDGED_ENGINE_ERROR),
    # 执行停止时刻是不带时区的串：当作没有值，取 ECS 记下停止的时刻 10:05:01，晚于截止时刻，判为超时；把它补成 UTC 的
    # 10:04:59 会早于截止时刻、按退出码判成 engine_error
    ("2026-11-08T10:04:59", "2026-11-08T10:05:01Z", _JUDGED_TIMEOUT),
], ids=["after-the-cutoff", "before-the-cutoff", "naive-execution-time-falls-back-to-stopped-at"])
def test_task_exiting_on_its_own_is_judged_by_its_exit_time_through_the_real_tick(cloud_env, execution_stopped, stopped,
                                                                                  expected):
    """实测项 11 的本地一半（moto，真实的观察者与推进 Lambda）：task 在截止时刻之后、停止请求发出之前自己以 3 退出，STOPPED 事件里
    没有超时哨兵，观察者只记退出码与执行停止时刻；投影按退出时刻晚于截止时刻判为超时，说明是预算那一句，与前台同一情形相同。
    在截止时刻之前这样退出时按退出码归因。执行停止时刻读不出（不带时区）时按 ECS 记下停止的时刻判断。"""
    import json
    import time

    import boto3
    from gherkai_core.adapters.fargate_engine import events_pk

    store = _claimed_detached_run(cloud_env)
    cloud_env["events"].put_item(Item={"pk": events_pk("run-1", "a"), "seq": 1,
                                       "body": '{"type":"scope_started","scopeId":"a","sessionId":"s"}',
                                       "expires_at": int(time.time()) + 7 * 24 * 3600})
    detail = dict(_stopped_detail("run-1", "a", 3), executionStoppedAt=execution_stopped, stoppedAt=stopped)
    observed = exit_observer.handler({"detail": detail}, None)
    assert (observed["exit_code"], observed["timed_out"]) == (3, False)  # 观察者不判超时
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)

    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status) == (Status.ERROR, Status.ERROR)
    s3 = boto3.client("s3", region_name="us-east-1")
    # 读终态点名的那一份（键只由标识构成）
    key = f"reports/run-1/jobs/{state.jobs['a'].result_id}.json"
    jr = json.loads(s3.get_object(Bucket=_BUCKET, Key=key)["Body"].read())
    assert (jr["status"], jr["error_type"], jr["message"]) == expected


def test_timeout_handling_keeps_an_exit_record_written_while_it_lists_tasks(cloud_env):
    """实测项 12（moto）：超时处置点查过「还没有退出记录」之后、补写之前，观察者写下了真实的退出记录（这里在列 task
    期间写下，两个列表里都已找不到这个 task）。补写是条件写、不成立，留下的是真实的那一条，处置按退出记录已在返回。"""
    _claimed_detached_run(cloud_env)
    detail = _detail_with_times(3)

    class _ObserverLandsWhileListing(_FakeEcs):
        landed = False

        def list_tasks(self, **kw):
            if not self.landed:
                self.landed = True
                assert exit_observer.handler({"detail": detail}, None)["ok"] is True
            return super().list_tasks(**kw)

    built = reconciler._build("run-1")
    clock = _Clock("2026-11-08T10:06:00+00:00")
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=_ObserverLandsWhileListing(), now_fn=clock.now,
                                   sleep_fn=clock.sleep)
    assert r == "noop-exit-in-flight"
    [exit_rec] = [x.exited for x in built[1].records() if x.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.exited_at) == (3, False, _EXEC_STOPPED)
