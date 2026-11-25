"""Lambda handler 测试（ADR 0034；后端各入口共用的闸与清扫见 ADR 0054 决策九）：退出观察者 _extract、两条流的记录解析与 kicker 的
载荷分派、job 到点停止、闸、清扫与一批记录里各 run 的失败隔离。

事件格式解析用实际运行抓到的 ECS STOPPED event / DDB Stream event 形状；闸与清扫另有一组走 moto 内存表运行真 handler（各入口在
运行态不存在、已结束、读不出、提交记录不可用时的处理是行为契约，解析测不出来），ECS 用记录调用的替身。
真 Stream 触发 / 真 Fargate / 真 EventBridge 投递仍是 moto 之外的真实运行边界（绿≠对的证据边界）。

handler 源与本测试同住 provider 包（`gherkai_deploy_aws/lambdas/`，AWS 专属胶水，ADR 0037 决策 6）——测试不寄居
上游 runtime（ADR 0016 当年抽包的理由之一就是「handler 测试无处安身」）。经 sys.path 加那个目录——**摊平 import
是真实形态**：Lambda asset 把它们摊在 zip 根、作平级顶层模块（`exit_observer` 里 `from reconciler import …`
依赖此形态），故这里也按顶层模块 import、不走包路径。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

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


# ---------- kicker 对 runs 表流记录的分辨（ADR 0054 决策九第 1 条：按记录的种类，不按读到的状态）----------

def _runs_stream_record(run_id, *, event_name="INSERT", item_type="STATE", status_group="live"):
    """runs 表流记录的真实形状（NEW_IMAGE：Keys 与新映像，新映像带键属性）。status_group 为 None 时新映像不带这个属性。"""
    image = {"run_id": {"S": run_id}, "item_type": {"S": item_type}, "status": {"S": "pending"}}
    if status_group is not None:
        image["status_group"] = {"S": status_group}
    return {"eventName": event_name,
            "dynamodb": {"Keys": {"run_id": {"S": run_id}, "item_type": {"S": item_type}}, "NewImage": image}}


def _terminal_modify(run_id, status_group="passed"):
    """使 run 成为终态的那次写在流上的记录：STATE 条目的修改，新映像的状态分组不是 live。"""
    return _runs_stream_record(run_id, event_name="MODIFY", status_group=status_group)


def test_kicker_tells_the_state_insert_from_the_ending_write_by_the_record_kind():
    """kicker 按流记录的种类分辨两种写（ADR 0054 决策九第 1 条，ADR 0033 资源清单 13.）：STATE 条目的新建是新 run，STATE 条目的修改
    且新映像的状态分组不是 live 是使 run 成为终态的那次写；每种终态的分组值都算。"""
    event = {"Records": [_runs_stream_record("run-1"), _terminal_modify("run-2"), _terminal_modify("run-3", "error")]}
    assert reconciler._runs_from_runs_stream(event) == {
        "run-1": reconciler._NEW_RUN, "run-2": reconciler._RUN_ENDED, "run-3": reconciler._RUN_ENDED}


@pytest.mark.parametrize("order", ["insert-first", "modify-first"])
def test_kicker_takes_each_run_once_per_batch_and_the_new_run_kind_wins(order):
    """同一批里按 run 去重（ADR 0054 决策九第 2 条）：一个 run 的新建与终态写同在一批时只处理一次，按新建处理（新建一支同样先过闸，
    读到已结束即只清扫）。与两条记录的先后无关。"""
    records = [_runs_stream_record("run-1"), _terminal_modify("run-1")]
    if order == "modify-first":
        records.reverse()
    assert reconciler._runs_from_runs_stream({"Records": records}) == {"run-1": reconciler._NEW_RUN}


@pytest.mark.parametrize("record", [
    pytest.param(_runs_stream_record("run-1", item_type="META"), id="meta-insert"),
    pytest.param(_runs_stream_record("run-1", event_name="MODIFY"), id="live-modify"),
    pytest.param(_runs_stream_record("run-1", event_name="MODIFY", status_group=None), id="modify-without-group"),
    pytest.param(_runs_stream_record("run-1", event_name="MODIFY", item_type="META", status_group="passed"),
                 id="meta-modify"),
    pytest.param({"eventName": "REMOVE", "dynamodb": {"Keys": {"run_id": {"S": "run-1"}, "item_type": {"S": "STATE"}}}},
                 id="remove"),
    pytest.param({"eventName": "INSERT", "dynamodb": {"Keys": {}}}, id="no-run-id"),
    pytest.param("不是记录", id="not-a-dict"),
])
def test_kicker_skips_and_logs_a_stream_record_it_does_not_recognise(record, capsys):
    """认不出的流记录（两条过滤本不放过的：META 的新建与修改、状态分组仍是 live 的修改、REMOVE、形态不对的）记一行日志、跳过，同一批里
    认得出的照常；不推进、不算失败。"""
    event = {"Records": [record, _runs_stream_record("run-2")]}
    assert reconciler._runs_from_runs_stream(event) == {"run-2": reconciler._NEW_RUN}
    assert "跳过一条认不出的运行状态表流记录" in capsys.readouterr().out


@pytest.mark.parametrize("payload", [
    pytest.param({"run_id": "run-x"}, id="run-id-only"),
    pytest.param({"test": "kick"}, id="unknown-keys"),
    pytest.param({"run_id": "run-x", "timeout_scope": ""}, id="empty-scope"),
    pytest.param({"run_id": 7, "timeout_scope": "a"}, id="run-id-not-a-string"),
    pytest.param(["run-x"], id="not-a-dict"),
])
def test_kicker_logs_and_ignores_a_payload_it_does_not_recognise(payload, monkeypatch, capsys):
    """kicker 只认流记录与 job 到点的 `{run_id, timeout_scope}`（ADR 0034「推进器与触发源」第 2 条）：其余载荷（含只带 run 标识的）
    记一行日志、正常返回，不推进、不抛出——抛出会让异步调用重试一个没有意义的载荷。连组合根都不装配。"""
    monkeypatch.setattr(reconciler, "_backend", lambda: pytest.fail("认不出的载荷不该装配任何东西"))
    assert reconciler.kicker_handler(payload, None) == {"ok": True, "runs": []}
    assert "认不出的调用载荷" in capsys.readouterr().out


# ---------- job timeout（ADR 0034「job timeout」节的云端后端一侧）----------

import datetime as _dt  # noqa: E402

from gherkai_core.adapters.event_log import SqliteEventLog  # noqa: E402
from gherkai_core.adapters.run_store.local import LocalRunStore  # noqa: E402
from gherkai_core.model import (Job, JobState, RunMeta, RunState, Scenario, Status, Step,  # noqa: E402
                                StepArgument)


@pytest.fixture(autouse=True)
def _host_independent_filesystem_type(monkeypatch):
    """建 run 时的边界检查不依赖宿主的文件系统：把取文件系统类型的那一步换成本平台清单的第一项。这里测的是处理器的逻辑，
    报告目录落在哪种文件系统上由 core 的用例覆盖。"""
    from gherkai_core.adapters.run_store import run_dir

    allowed = run_dir.ALLOWED_FILESYSTEMS.get(sys.platform)
    if allowed:
        monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: allowed[0])


class _ReleaseAtOnce:
    """建 run 用的锁持有者：收到持生命期锁的描述符即关闭（ADR 0030 决定四「持锁的描述符交给注入的持有者」条）。这里的用例只要
    `create_run` 写下的记录，本机的生命期锁不在测试范围内，所以不留着它，用例结束之后也没有打开的描述符。边界检查经上面的自动
    夹具取本平台清单的第一项。"""

    def hold(self, fd: int) -> None:
        os.close(fd)


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


def test_timeout_watch_creates_one_time_schedule_in_the_schedule_group():
    """job 到点停止的触发建在专用 schedule group 里，名字不带 prefix（ADR 0033 资源清单 15.）：表达式 at()、FlexibleTimeWindow OFF、
    触发之后自动删除、目标是 kicker 加执行角色，载荷 `{run_id, timeout_scope}`；RetryPolicy 不传，取 Scheduler 的缺省。"""
    from gherkai_runtime import names

    client = _FakeSchedulerClient()
    kicker = "arn:aws:lambda:us-east-1:000000000000:function:gherkai-kicker"
    role = "arn:aws:iam::000000000000:role/gherkai-timeout-scheduler"
    watch = reconciler.EventBridgeTimeoutWatch(client, kicker_arn=kicker, role_arn=role, group_name="gherkai-schedules")
    watch.arm("run-1", "features/x.feature:7", _dt.datetime(2026, 11, 8, 10, 5, tzinfo=_dt.timezone.utc))
    assert len(client.calls) == 1
    kw = client.calls[0]
    assert kw["GroupName"] == "gherkai-schedules"
    assert kw["Name"] == names.job_timeout_schedule_name("run-1", "features/x.feature:7")  # 哈希名（scope_id 可含非法字符）
    assert kw["Name"].startswith("job-timeout-") and not kw["Name"].startswith("gherkai-")
    assert kw["ScheduleExpression"] == "at(2026-11-08T10:05:00)"
    assert kw["ActionAfterCompletion"] == "DELETE"  # 到点自动删（idle 零成本）
    assert kw["FlexibleTimeWindow"] == {"Mode": "OFF"}
    assert "RetryPolicy" not in kw
    import json as _json
    assert {k: v for k, v in kw["Target"].items() if k != "Input"} == {"Arn": kicker, "RoleArn": role}
    payload = _json.loads(kw["Target"]["Input"])
    assert payload == {"run_id": "run-1", "timeout_scope": "features/x.feature:7"}


def test_timeout_watch_at_is_the_given_cutoff():
    """at 取 core 传来的截止时刻本身，带秒、不取整到分钟（ADR 0034「job timeout」节「到点不早于 deadline」条①）：触发器不再自己
    由预算推算，arm 晚于认领不推后到点。at() 只收到秒，小数秒截去，差的那不到一秒由到点处置的复查补足；截止时刻带别的时区偏移时
    换算回 UTC（at() 不带时区后缀、按 UTC 解释）。"""
    client = _FakeSchedulerClient()
    watch = reconciler.EventBridgeTimeoutWatch(client, kicker_arn="arn:k", role_arn="arn:r", group_name="gherkai-schedules")
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
        store = LocalRunStore(tmp_path / sub, lock_holder=_ReleaseAtOnce())
        store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)},
                                        started_at="t0", high_water_mark=0))
        client = _FakeSchedulerClient()
        watch = reconciler.EventBridgeTimeoutWatch(client, kicker_arn="arn:k", role_arn="arn:r", group_name="gherkai-schedules")
        launcher = CloudLauncher(lambda _name: _Engine(), run_id="run-1", timeout_watch=watch)
        tick("run-1", meta, SqliteEventLog(tmp_path / sub / "events.db"), store, launcher, 1, clock=lambda: claimed,
             result_store=LocalResultStore(tmp_path / sub))
        assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING
        [call] = client.calls
        return call["ScheduleExpression"]

    assert armed_at("budget", "2026-11-08T11:00:00+00:00") == "at(2026-11-08T10:05:00)"    # 认领时刻加 300 秒
    assert armed_at("deadline", "2026-11-08T10:03:20+00:00") == "at(2026-11-08T10:03:20)"  # 期限更早：以期限封顶


def test_timeout_watch_name_does_not_depend_on_the_prefix_or_the_scope_text():
    """触发名不带 prefix、长度固定：prefix 取上限 47 个字符时 group 名随之变长，触发名不变；scope_id 是很长的用户文本时名字仍是
    32 个字符、只含 schedule 名允许的字符（EventBridge Scheduler 的名字至多 64 个字符）。"""
    long_prefix = "a" * 46 + "-"
    long_scope = "features/很长的目录/" + "x" * 300 + ".feature:7"
    named = []
    for group in (f"{long_prefix}schedules", "gherkai-schedules"):
        client = _FakeSchedulerClient()
        reconciler.EventBridgeTimeoutWatch(client, kicker_arn="arn:k", role_arn="arn:r", group_name=group).arm(
            "run-1", long_scope, _dt.datetime(2026, 11, 8, 10, 1, tzinfo=_dt.timezone.utc))
        [call] = client.calls
        assert call["GroupName"] == group
        named.append(call["Name"])
    assert named[0] == named[1]
    assert len(named[0]) == 32 <= 64
    assert re.fullmatch(r"job-timeout-[0-9a-f]{20}", named[0])


def test_timeout_watch_conflict_is_idempotent():
    """同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。"""
    watch = reconciler.EventBridgeTimeoutWatch(
        _FakeSchedulerClient(conflict=True), kicker_arn="arn:k", role_arn="arn:r", group_name="gherkai-schedules")
    watch.arm("run-1", "a", _dt.datetime(2026, 11, 8, 10, 1, tzinfo=_dt.timezone.utc))  # 不抛即过


@pytest.fixture
def timeout_built(monkeypatch):
    """构造 _handle_timeout 需要的 built 元组的函数：给定目录里的真 LocalRunStore，加 moto 内存表上的真 DdbEventLog（生产里云端超时
    处置用的正是它，见 `reconciler._assemble`）；meta 带 300 秒的 timeout 预算，运行期限缺省远在任何时刻之后、不起作用。每次构造建一张
    新的 events 表，同一条用例里的几次构造互不串扰。先盖假凭证、再 mock，绝不连真 AWS。"""
    import itertools

    import boto3
    from moto import mock_aws

    from gherkai_core.adapters.event_log import DdbEventLog

    for k, v in {"AWS_ACCESS_KEY_ID": "testing", "AWS_SECRET_ACCESS_KEY": "testing",
                 "AWS_SESSION_TOKEN": "testing", "AWS_DEFAULT_REGION": "us-east-1"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        tables = itertools.count()

        def build(root, *, status=Status.RUNNING, claimed_at=None, with_exit=False,
                  deadline_at="2999-01-01T00:00:00+00:00"):
            job = Job(scope_id="a", scope_name="a", engine="novaact", timeout_s=300.0,
                      scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),))
            meta = RunMeta(run_id="run-1", created_at="t0", jobs=(job,), deadline_at=deadline_at)
            store = LocalRunStore(root, lock_holder=_ReleaseAtOnce())
            store.create_run(meta, RunState(
                run_id="run-1", status=Status.RUNNING,
                jobs={"a": JobState("a", status, claimed_at=claimed_at)},
                started_at="t0", high_water_mark=0))
            events = ddb.create_table(
                TableName=f"gherkai-events-{next(tables)}",
                KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"},
                           {"AttributeName": "seq", "KeyType": "RANGE"}],
                AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"},
                                      {"AttributeName": "seq", "AttributeType": "N"}],
                BillingMode="PAY_PER_REQUEST")
            log = DdbEventLog(events, "run-1", ["a"])
            if with_exit:
                log.record_exit("a", 137)
            return meta, log, store, None, 1, None, None

        yield build


class _FakeEcs:
    """list_tasks/describe_tasks/stop_task/run_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的 task 描述
    （dict：arn / lastStatus / desiredStatus / exitCode? / stoppedReason? / stopCode? / executionStoppedAt? / stoppedAt? /
    scope_id? / started_by?——scope_id 缺省用构造时的 `scope_id`，给多 task 场景造出「只有一个匹配目标」；started_by 缺省是 run-1）。
    list_tasks 按 desiredStatus 与 startedBy 过滤（ECS 语义：正在停止/已停止的不在 RUNNING 列表里），每次调用的参数记进 `listed`；
    describe 返回带 SCOPE_ID env 的 overrides。stop_task 之后这个 task 的期望状态即为已停止，按「运行中」再列不出它（与真实的 ECS
    相同，ADR 0054 实测项 27）；对已停止的 task 照常成功返回。run_task 记下请求、返回一个新的 task。

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
        self.listed: list[dict] = []
        self.run_tasks: list[dict] = []

    def add(self, arn, *, started_by="run-1", desired="RUNNING", last="RUNNING"):
        """加一个 task（缺省是 run-1 起的、运行中的）。"""
        self._tasks.append({"arn": arn, "started_by": started_by, "desiredStatus": desired, "lastStatus": last})

    def list_tasks(self, **kw):
        self.listed.append(dict(kw))
        want = kw.get("desiredStatus", "RUNNING")
        by = kw.get("startedBy")
        arns = [t["arn"] for t in self._tasks
                if t.get("desiredStatus", "RUNNING") == want and (by is None or t.get("started_by", "run-1") == by)]
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
        for t in self._tasks:
            if t["arn"] == kw["task"]:
                t["desiredStatus"] = "STOPPED"
        return {}

    def run_task(self, **kw):
        self.run_tasks.append(kw)
        arn = f"arn:task/started-{len(self.run_tasks)}"
        self.add(arn, started_by=kw.get("startedBy"))
        return {"tasks": [{"taskArn": arn}], "failures": []}


def _stopped_filler(n, *, exit_code=0):
    """n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。"""
    return [{"arn": f"arn:task/stopped-{i}", "lastStatus": "STOPPED", "desiredStatus": "STOPPED",
             "exitCode": exit_code, "scope_id": f"other-{i}"} for i in range(n)]


def test_handle_timeout_stops_matching_task(timeout_built, tmp_path, monkeypatch):
    """仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer 既有链收敛（单一真源）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path), ecs_client=ecs)
    assert r == "stopped"
    assert len(ecs.stopped) == 1
    assert reconciler.TIMEOUT_STOP_SENTINEL in ecs.stopped[0]["reason"]
    assert ecs.stopped[0]["task"] == "arn:task/1"


def test_handle_timeout_noop_when_job_terminal(timeout_built, tmp_path, monkeypatch):
    """到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path, status=Status.PASSED), ecs_client=ecs)
    assert r == "noop-not-running" and ecs.stopped == []


def test_handle_timeout_noop_when_exit_in_flight(timeout_built, tmp_path, monkeypatch):
    """退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path, with_exit=True), ecs_client=ecs)
    assert r == "noop-exit-in-flight" and ecs.stopped == []


def test_handle_timeout_converges_directly_when_task_gone(timeout_built, tmp_path, monkeypatch):
    """task 无踪且无退出记录（STOPPED 事件丢投等）→ 补写一条判为超时的未知退出收敛：退出码未知、带超时标志、没有可观察的退出
    时刻（「到点 invoke 顺带兜事件丢投」的落点）。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    built = timeout_built(tmp_path, claimed_at="2026-08-13T00:00:00Z")
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=_FakeEcs(task_arns=[]))
    assert r == "converged-directly"
    exits = [rec for rec in built[1].records() if rec.kind == "exit"]
    assert len(exits) == 1
    assert (exits[0].exited.exit_code, exits[0].exited.timed_out, exits[0].exited.exited_at) == (None, True, None)


def test_handle_timeout_pages_task_lists_and_batches_describe(timeout_built, tmp_path, monkeypatch):
    """STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。

    ECS 保留已停止的 task 约 1 小时，故一个大 run 的 STOPPED 列表轻易超过单页 100 条；只取首页会把仍在运行的
    目标判成「无踪」，把一个正常运行的 job 误判成超时。
    """
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"], tasks=_stopped_filler(120))
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path), ecs_client=ecs)
    assert r == "stopped"
    assert ecs.stopped and ecs.stopped[0]["task"] == "arn:task/1"
    assert all(len(batch) <= _FakeEcs.PAGE for batch in ecs.described)
    assert len(ecs.described) == 1  # 目标在首批就命中 → 不再往下 describe


def test_handle_timeout_finds_stopped_target_on_second_page(timeout_built, tmp_path, monkeypatch):
    """目标落在 STOPPED 列表第二页、且没有退出记录 → 仍按 DescribeTasks 落它的真退出码，不臆造超时。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    target = {"arn": "arn:task/target", "lastStatus": "STOPPED", "desiredStatus": "STOPPED", "exitCode": 7}
    ecs = _FakeEcs(tasks=_stopped_filler(100) + [target])
    built = timeout_built(tmp_path)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs)
    assert r == "converged-from-describe"
    exits = [rec for rec in built[1].records() if rec.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.exit_code == 7 and exits[0].exited.timed_out is False
    assert all(len(batch) <= _FakeEcs.PAGE for batch in ecs.described)


# ---------- 到点处置先复查 deadline（ADR 0034「job timeout」节「到点不早于 deadline」条②）----------
# Scheduler 只承诺 60 秒精度，带秒的 at() 可能在 deadline 所在那一分钟的开头触发。下面几条的 job 在 10:00:00 被
# claim、预算 300 秒（`timeout_built`），截止时刻是 10:05:00（运行期限远在其后）；时钟与等待经 now_fn / sleep_fn 注入。

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


def test_handle_timeout_waits_until_deadline_when_triggered_early(timeout_built, tmp_path, monkeypatch):
    """触发早于 deadline、剩余不超过 60 秒 → 先等到 deadline、重读状态，再停 task；等待期间尚未动 ECS。等满剩余的 45 秒醒来时读到的
    恰好是截止时刻本身，还不算已到（已到指严格晚于），再等一个固定的短时长，读到晚于截止时刻才停 task。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    stopped_during_wait: list[list] = []
    clock = _Clock("2026-11-08T10:04:15+00:00", during_sleep=lambda: stopped_during_wait.append(list(ecs.stopped)))
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1
    assert clock.slept == [45.0, reconciler._TIMEOUT_TIE_WAIT_S]  # 等到 deadline，恰好读到 deadline 时再等一次
    assert stopped_during_wait == [[], []]                         # 停 task 发生在两次等待都完成之后
    assert clock.now() > _dt.datetime.fromisoformat("2026-11-08T10:05:00+00:00")


@pytest.mark.parametrize("now, slept", [
    ("2026-11-08T10:05:00+00:00", [reconciler._TIMEOUT_TIE_WAIT_S]),
    ("2026-11-08T10:05:00.000001+00:00", []),
], ids=["exactly-at-the-cutoff", "one-microsecond-after"])
def test_handle_timeout_stops_only_after_reading_a_time_strictly_later_than_the_cutoff(timeout_built, tmp_path, monkeypatch, now, slept):
    """已到指读到的墙钟严格晚于截止时刻，与本机启动器的检查、投影比较退出时刻的取法相同（ADR 0054 决策二「已过」的定义）。触发时
    读到的恰好是截止时刻 10:05:00：不停 task，再等一个固定的短时长，醒来读到晚于截止时刻才停；晚 1 微秒即已到，不等待、直接停。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    stopped_during_wait: list[list] = []
    clock = _Clock(now, during_sleep=lambda: stopped_during_wait.append(list(ecs.stopped)))
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1
    assert clock.slept == slept
    assert stopped_during_wait == [[] for _ in slept]  # 等待期间没有停 task


def test_handle_timeout_does_not_loop_forever_when_the_clock_stays_at_the_cutoff(timeout_built, tmp_path, monkeypatch, capsys):
    """墙钟停在截止时刻、等待之后不前进（出故障的系统时钟）：每次醒来读到的都恰好是截止时刻、都不算已到。各次等待计入同一份等待额度
    （60 秒），额度用完即不停 task、不写退出记录，返回 skip-early 并打一行诊断，不在循环里一直等下去。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = timeout_built(tmp_path, claimed_at=_CLAIMED)
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
def test_handle_timeout_wait_count_is_bounded_wherever_the_clock_is_stuck(timeout_built, tmp_path, monkeypatch, stuck_at):
    """墙钟停在截止时刻之前不到一秒的位置：每次等待至少是固定量，等待次数不超过额度除以固定量，用完即不停 task、返回 skip-early。
    按剩余时长等待的话，剩余越小循环次数越多，每次醒来都要重读 job 状态与退出记录。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock(stuck_at, advance=False)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early"
    assert ecs.stopped == [] and built[1].has_exit("a") is False
    assert all(s >= reconciler._TIMEOUT_TIE_WAIT_S for s in clock.slept)
    assert len(clock.slept) <= reconciler._TIMEOUT_EARLY_WAIT_MAX_S / reconciler._TIMEOUT_TIE_WAIT_S
    assert sum(clock.slept) <= reconciler._TIMEOUT_EARLY_WAIT_MAX_S


def test_handle_timeout_disposes_at_once_when_deadline_passed(timeout_built, tmp_path, monkeypatch):
    """触发时 deadline 已过（Scheduler 在那一分钟内偏晚）→ 不等待、直接处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:05:20+00:00")
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1 and clock.slept == []


def test_handle_timeout_skips_when_triggered_more_than_a_minute_early(timeout_built, tmp_path, monkeypatch, capsys):
    """剩余超过 60 秒（早于 Scheduler 的文档精度）→ 不等待、不处置、不碰 ECS，打一行诊断；宁可不处置也不提前处置，
    保护交给防御扫与之后的推进。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock("2026-11-08T10:03:30+00:00")
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early"
    assert ecs.stopped == [] and ecs.described == [] and clock.slept == []
    assert built[1].has_exit("a") is False
    out = capsys.readouterr().out
    assert "timeout-skip: run=run-1 scope=a" in out and "90 秒" in out


def test_handle_timeout_skips_when_the_invocation_cannot_wait_long_enough(timeout_built, tmp_path, monkeypatch):
    """剩余虽在 60 秒内、却超过本次调用可等的秒数（kicker 按 Lambda 剩余时间给出）→ 同样不处置：等不到 deadline 就动手
    即是提前处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:04:20+00:00")
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   wait_budget_fn=lambda: 20.0, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "skip-early" and ecs.stopped == [] and clock.slept == []


def test_handle_timeout_samples_the_wait_budget_after_the_state_reads(timeout_built, tmp_path, monkeypatch):
    """等待额度临睡前才采样：复查前的读取慢时，已花掉的时间不再算进可等的额度。Lambda 剩余 70 秒、离 deadline 50 秒、
    一次读取 25 秒——提前采样会批准再等 25 秒、等完只剩 20 秒（低于处置预留）；临睡采样得到 15 秒的额度，等不到 deadline 即不处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = timeout_built(tmp_path, claimed_at=_CLAIMED)
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


def test_handle_timeout_noop_when_job_finishes_during_wait(timeout_built, tmp_path, monkeypatch):
    """等待期间 job 自行结束（观察者写下退出记录）→ 等完重读即 no-op，不停 task、不改写那条真退出记录。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    built = timeout_built(tmp_path, claimed_at=_CLAIMED)
    clock = _Clock("2026-11-08T10:04:30+00:00", during_sleep=lambda: built[1].record_exit("a", 0))
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "noop-exit-in-flight" and ecs.stopped == [] and clock.slept == [30.0]
    exits = {x.scope_id: x.exited for x in built[1].records() if x.kind == "exit"}
    assert exits["a"].exit_code == 0 and exits["a"].timed_out is False


def test_handle_timeout_waits_again_when_the_clock_is_turned_back_during_the_wait(timeout_built, tmp_path, monkeypatch):
    """等待期间系统时钟被回拨：10:04:15 触发、等 45 秒，醒来读到的是 10:04:50，还没到截止时刻 10:05:00；在这次调用的等待额度
    （60 秒）之内接着等 10 秒，醒来恰好读到截止时刻本身，仍不算已到，再等一个固定的短时长，读到晚于截止时刻才停 task。发出停止之前
    必须有一次读到已过截止时刻（ADR 0054 决策二后台推进条「截止时刻与说明」）：醒来只重查状态与退出记录、不重读时钟时，会在截止时刻
    之前 10 秒停 task。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    stopped_during_wait: list[list] = []
    clock = _Clock("2026-11-08T10:04:15+00:00", during_sleep=lambda: stopped_during_wait.append(list(ecs.stopped)),
                   rewind_s=[10.0])
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path, claimed_at=_CLAIMED), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and len(ecs.stopped) == 1
    assert clock.slept == [45.0, 10.0, reconciler._TIMEOUT_TIE_WAIT_S]
    assert stopped_during_wait == [[], [], []]  # 三次等待期间都没有停 task
    assert clock.now() > _dt.datetime.fromisoformat("2026-11-08T10:05:00+00:00")


def test_handle_timeout_does_not_stop_when_the_wait_quota_runs_out_before_the_cutoff(timeout_built, tmp_path, monkeypatch, capsys):
    """回拨之后在这次调用的等待额度之内等不到截止时刻：额度在第一次临睡前定下（60 秒与本次调用还能等的秒数取小），各次等待之和
    不超过它。只受 60 秒约束时回拨 30 秒，还要再等 30 秒，合计 75 秒；本次调用只能等 50 秒时回拨 10 秒，合计 55 秒。两种都超过额度：
    不再等待、不停 task、不写退出记录，返回 skip-early 并打一行诊断，交给之后的推进检查。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    for name, budget, rewind in (("cap", None, 30.0), ("budget", 50.0, 10.0)):
        ecs = _FakeEcs(task_arns=["arn:task/1"])
        built = timeout_built(tmp_path / name, claimed_at=_CLAIMED)
        clock = _Clock("2026-11-08T10:04:15+00:00", rewind_s=[rewind])
        wait_budget_fn = (lambda b=budget: b) if budget is not None else None
        r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, wait_budget_fn=wait_budget_fn,
                                       now_fn=clock.now, sleep_fn=clock.sleep)
        assert r == "skip-early", name
        assert ecs.stopped == [] and ecs.described == [] and clock.slept == [45.0], name
        assert built[1].has_exit("a") is False, name
        out = capsys.readouterr().out
        assert "timeout-skip: run=run-1 scope=a" in out and "已等过 45 秒仍未到" in out, name


def test_handle_timeout_without_claimed_at_counts_as_reached(timeout_built, tmp_path, monkeypatch):
    """JobState 缺 claimed_at 时无从复查 → 按已到处理：不等待、照常处置。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:00:00+00:00")
    r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path), ecs_client=ecs,
                                   now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and clock.slept == []


def test_handle_timeout_treats_an_unreadable_claim_time_as_reached(timeout_built, tmp_path, monkeypatch):
    """认领时刻读不出或不带时区（不是本系统写出的值）时与缺认领时刻同一分支：无从复查，按已到处理，不抛到调用方。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    for i, claimed in enumerate(("2026-11-08T10:00:00", "not-a-time")):
        ecs = _FakeEcs(task_arns=["arn:task/1"])
        clock = _Clock("2026-11-08T10:00:00+00:00")
        r = reconciler._handle_timeout("run-1", "a", timeout_built(tmp_path / str(i), claimed_at=claimed), ecs_client=ecs,
                                       now_fn=clock.now, sleep_fn=clock.sleep)
        assert r == "stopped" and clock.slept == [], claimed


# ---------- 截止时刻以运行期限封顶（ADR 0054 决策二第 2 条、后台推进条「截止时刻与说明」）----------
# job 在 10:00:00 被认领、预算 300 秒；运行期限 10:02:00 早于认领时刻加预算，截止时刻因此是 10:02:00。

_EARLY_DEADLINE = "2026-11-08T10:02:00+00:00"


def test_handle_timeout_rechecks_against_the_cutoff_capped_by_the_run_deadline(timeout_built, tmp_path, monkeypatch):
    """到点复查按封顶后的截止时刻：10:01:30 触发时离期限 30 秒，等过期限即停 task（只按预算算会离 10:05:00 还有 210 秒、判成过早
    而不处置；等满 30 秒恰好读到期限本身时再等一个固定的短时长）。停 task 的 reason 带哨兵串并说明是 run 的期限到了，观察者据哨兵串
    归因为超时。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(task_arns=["arn:task/1"])
    clock = _Clock("2026-11-08T10:01:30+00:00")
    built = timeout_built(tmp_path, claimed_at=_CLAIMED, deadline_at=_EARLY_DEADLINE)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now, sleep_fn=clock.sleep)
    assert r == "stopped" and clock.slept == [30.0, reconciler._TIMEOUT_TIE_WAIT_S]
    reason = ecs.stopped[0]["reason"]
    assert reason == f"{reconciler.TIMEOUT_STOP_SENTINEL}: run deadline 2026-11-08T10:02:00+00:00 reached"
    assert reconciler.exit_from_task({"containers": [{"exitCode": 143}], "stoppedReason": reason}) == (143, True, None, None)


def test_stop_reason_names_the_cutoff_that_took_effect(timeout_built, tmp_path, monkeypatch):
    """停 task 的 reason 按起作用的截止时刻分别写：job 自己的预算到点仍是原有的写法，期限封顶时说明是 run 的期限；认领时刻缺失、
    无从重算时只说到了时间上限。三种都以哨兵串开头。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    reasons = {}
    for name, claimed, deadline_at in (("budget", _CLAIMED, "2999-01-01T00:00:00+00:00"),
                                       ("deadline", _CLAIMED, _EARLY_DEADLINE),
                                       ("unknown", None, _EARLY_DEADLINE)):
        ecs = _FakeEcs(task_arns=["arn:task/1"])
        clock = _Clock("2026-11-08T10:06:00+00:00")
        built = timeout_built(tmp_path / name, claimed_at=claimed, deadline_at=deadline_at)
        assert reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs, now_fn=clock.now,
                                          sleep_fn=clock.sleep) == "stopped"
        reasons[name] = ecs.stopped[0]["reason"]
    sentinel = reconciler.TIMEOUT_STOP_SENTINEL
    assert reasons == {"budget": f"{sentinel}: scope exceeded 300s budget",
                       "deadline": f"{sentinel}: run deadline 2026-11-08T10:02:00+00:00 reached",
                       "unknown": f"{sentinel}: scope reached its time limit"}


def test_scan_overdue_timeouts_uses_the_cutoff_capped_by_the_run_deadline(timeout_built, tmp_path, monkeypatch):
    """防御扫按封顶后的截止时刻判断：认领 200 秒、预算 300 秒，只按预算算离截止还有 100 秒；运行期限已过去 150 秒，超过余量
    120 秒，于是进处置。期限只过去 100 秒时仍在余量之内，不碰。"""
    from gherkai_core.serialize import instant_to_iso
    from gherkai_runtime import compose

    calls = []
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built, **kw: calls.append(sid))
    now = compose.now()
    claimed = instant_to_iso(now - _dt.timedelta(seconds=200))
    for sub, past_s, expected in (("over", 150, ["a"]), ("within", 100, [])):
        calls.clear()
        built = timeout_built(tmp_path / sub, claimed_at=claimed,
                               deadline_at=instant_to_iso(now - _dt.timedelta(seconds=past_s)))
        reconciler._scan_overdue_timeouts("run-1", built)
        assert calls == expected, sub


class _StubBackend:
    """只给分派一层的用例用：闸、装配与推进一步都换成记录，组合根里只有 ECS client 会被读到。"""

    ecs = "ECS"


def _stub_kicker_steps(monkeypatch, gate):
    """把 kicker 到点路径上的各步换成记录：闸给出 gate（`_Gate`），装配返回 "BUILT"。"""
    calls: list[tuple] = []
    monkeypatch.setattr(reconciler, "_backend", lambda: _StubBackend())
    monkeypatch.setattr(reconciler, "_gate",
                        lambda rid, backend: calls.append(("gate", rid)) or reconciler._GateResult(gate, "META"))
    monkeypatch.setattr(reconciler, "_assemble",
                        lambda rid, meta, backend: calls.append(("assemble", rid, meta)) or "BUILT")
    monkeypatch.setattr(reconciler, "_handle_timeout",
                        lambda rid, sid, built, **kw: calls.append(("timeout", rid, sid, built, kw["ecs_client"])))
    monkeypatch.setattr(reconciler, "_advance",
                        lambda rid, built, backend, label: calls.append(("advance", rid, built, label)))
    return calls


def test_kicker_job_timeout_passes_the_gate_before_stopping_then_advances(monkeypatch):
    """job 到点停止的触发（payload {"run_id","timeout_scope"}）：先过闸（先看 run、再看 job，ADR 0054 决策九「落实时」一段），装配一次，
    再做 job 到点停止（用组合根里那一个 ECS client），然后照常推进一步（到点 invoke 本身即一次强制推进，ADR 0034「job timeout」节）。"""
    calls = _stub_kicker_steps(monkeypatch, reconciler._Gate.ADMITTED)
    out = reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert out == {"ok": True, "runs": ["run-1"]}
    assert calls == [("gate", "run-1"), ("assemble", "run-1", "META"), ("timeout", "run-1", "a", "BUILT", "ECS"),
                     ("advance", "run-1", "BUILT", "kicker")]


@pytest.mark.parametrize("gate", [reconciler._Gate.SWEPT, reconciler._Gate.UNREADABLE])
def test_kicker_job_timeout_does_nothing_else_when_the_gate_does_not_admit(monkeypatch, gate):
    """闸不放行（运行态不存在或已结束时闸已清扫、读不出时闸只记了日志）：不做 job 到点停止、不装配、不推进。"""
    calls = _stub_kicker_steps(monkeypatch, gate)
    assert reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None) == {"ok": True, "runs": ["run-1"]}
    assert calls == [("gate", "run-1")]


def test_kicker_job_timeout_failure_fails_the_invocation(monkeypatch):
    """定时触发的调用只带一个 run：job 到点停止里的失败让这次调用失败，由 AWS 的重试再调用（ADR 0054 决策九第 2 条「失败与批的
    隔离」末句）。"""
    _stub_kicker_steps(monkeypatch, reconciler._Gate.ADMITTED)

    def _boom(rid, sid, built, **kw):
        raise RuntimeError("ListTasks 被限流")

    monkeypatch.setattr(reconciler, "_handle_timeout", _boom)
    with pytest.raises(reconciler._RunsNotDone) as exc:
        reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert exc.value.failed == ["run-1"]


def test_kicker_bounds_the_timeout_wait_by_the_remaining_invocation_time(monkeypatch):
    """kicker 把 Lambda 剩余时间减去处置与 tick 的余裕作为可等待的上界交给处置；拿不到 context 时不加这层约束。"""
    seen: list = []
    _stub_kicker_steps(monkeypatch, reconciler._Gate.ADMITTED)
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built, **kw: seen.append(kw["wait_budget_fn"]()))

    class _Ctx:
        def get_remaining_time_in_millis(self):
            return 100_000

    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, _Ctx())
    reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)
    assert seen == [100.0 - reconciler._TIMEOUT_HANDLING_RESERVE_S, None]


def test_scan_overdue_timeouts_only_over_budget(timeout_built, tmp_path, monkeypatch):
    """防御扫（claimed_at ②）只处置「过了截止时刻加余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at/认领时刻读不出的不碰。"""
    calls = []
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda rid, sid, built, **kw: calls.append(sid))
    # claimed_at 在过去（相对真时钟必已超 300s 预算加余量）→ 处置
    built = timeout_built(tmp_path / "over", claimed_at="2026-08-13T00:00:00Z")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == ["a"]
    # claimed_at 在未来（elapsed 为负，等价「未到期」）→ 不碰
    calls.clear()
    built = timeout_built(tmp_path / "fresh", claimed_at="2099-01-01T00:00:00Z")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == []
    # 无 claimed_at（旧数据/未 claim）→ 不碰（无起算点不臆断）
    built = timeout_built(tmp_path / "nocl")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == []
    # 认领时刻不带时区（不是本系统写出的值）→ 同「无起算点」，不碰、不抛
    built = timeout_built(tmp_path / "naive", claimed_at="2026-08-13T00:00:00")
    reconciler._scan_overdue_timeouts("run-1", built)
    assert calls == []


def _stub_advance_host(monkeypatch, outcome):
    """把 `_advance` 的外部动作换成记录：tick 返回给定结果，记下报告生成、防御性超时扫与清扫的先后。"""
    import gherkai_core.reconcile as _cr

    calls: list[str] = []
    monkeypatch.setattr(_cr, "tick", lambda *a, **kw: outcome)
    monkeypatch.setattr(_cr, "write_report_from_record", lambda *a, **kw: calls.append("report"))
    monkeypatch.setattr(reconciler, "_scan_overdue_timeouts", lambda rid, built, **kw: calls.append("scan"))
    monkeypatch.setattr(reconciler, "_sweep", lambda rid, backend: calls.append("sweep"))
    return calls


class _StateStub:
    def load_run_state(self, run_id):
        return None


_STUB_BUILT = reconciler._Assembled("META", "LOG", _StateStub(), "LAUNCHER", 1, "RSTORE", "PSTORE")


def test_advance_branches_on_tick_outcome(monkeypatch):
    """`_advance` 按 tick 的三种结果分支（ADR 0034 机制三「run 级状态只进不退」条④）：这一方的写使 run 成为终态时先生成报告、再清扫
    （ADR 0054 决策九第 2 条③「生成报告之后」）；run 已结束而不是这一方使它结束时只清扫；继续推进时只做防御性超时扫。"""
    import gherkai_core.reconcile as _cr

    cases = [
        (_cr.TickOutcome.COMMITTED, ["report", "sweep"]),
        (_cr.TickOutcome.ENDED, ["sweep"]),
        (_cr.TickOutcome.CONTINUE, ["scan"]),
    ]
    assert {outcome for outcome, _ in cases} == set(_cr.TickOutcome)  # 每一种结果都有一条
    for outcome, expected in cases:
        calls = _stub_advance_host(monkeypatch, outcome)
        reconciler._advance("run-1", _STUB_BUILT, _StubBackend(), "reconciler")
        assert calls == expected, outcome.name


def test_advance_writes_the_report_from_the_record_when_its_tick_commits(monkeypatch):
    """这一方的写使 run 成为终态时，报告由这一方从记录生成（ADR 0034 机制三「run 级状态只进不退」条④ K2，ADR 0027「ReportStore
    接口：整 run 一次写」节）：`_advance` 把这个 run 的运行定义、RunStore、判定存储与报告落点交给从记录生成报告的入口，tick 不交回
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
                        lambda rid, built, **kw: pytest.fail("这一方使 run 成为终态时不做防御性超时扫"))
    monkeypatch.setattr(reconciler, "_sweep", lambda rid, backend: None)
    built = reconciler._Assembled(meta, "LOG", run_store, "LAUNCHER", 1, "RSTORE", "PSTORE")
    reconciler._advance("run-1", built, _StubBackend(), "reconciler")
    [arguments] = reports
    assert set(arguments) == {"meta", "run_store", "result_store", "report_store", "created_at"}
    assert arguments["meta"] is meta and arguments["run_store"] is run_store
    assert (arguments["result_store"], arguments["report_store"]) == ("RSTORE", "PSTORE")
    instant_from_iso(arguments["created_at"])  # 记录写法的时刻（带时区），解析不了即抛


def test_advance_isolates_a_defensive_scan_failure(monkeypatch, capsys):
    """防御性超时扫的失败隔离在调用之内（ADR 0054 决策九第 2 条「失败与批的隔离」）：`_advance` 照常返回，不算这条记录的失败。"""
    import gherkai_core.reconcile as _cr

    _stub_advance_host(monkeypatch, _cr.TickOutcome.CONTINUE)

    def _boom(run_id, built, **kw):
        raise RuntimeError("DescribeTable 超时")

    monkeypatch.setattr(reconciler, "_scan_overdue_timeouts", _boom)
    reconciler._advance("run-1", _STUB_BUILT, _StubBackend(), "reconciler")
    assert "超时兜底检查未完成" in capsys.readouterr().out


@pytest.mark.parametrize("outcome", ["COMMITTED", "ENDED"])
def test_advance_raises_a_sweep_failure(monkeypatch, outcome):
    """清扫的失败记为这条记录的失败（同一条）：原样抛出，交给 `_each_run` 汇总。"""
    import gherkai_core.reconcile as _cr

    _stub_advance_host(monkeypatch, _cr.TickOutcome[outcome])

    def _boom(run_id, backend):
        raise RuntimeError("StopTask 被拒")

    monkeypatch.setattr(reconciler, "_sweep", _boom)
    with pytest.raises(RuntimeError, match="StopTask 被拒"):
        reconciler._advance("run-1", _STUB_BUILT, _StubBackend(), "reconciler")


def test_sweep_pages_through_every_running_task_of_the_run_and_can_repeat():
    """清扫（ADR 0054 决策九第 2 条）：按启动标识与期望状态「运行中」在部署的 cluster 里列出这个 run 的 task，翻页取全、逐个停掉；别的
    run 的 task 与已在停止的不在列表里。不写 runs 表，可以重复执行：再清扫一次列不出已停的，什么都不停。"""
    import types

    ecs = _FakeEcs()
    running = [f"arn:task/{i}" for i in range(_FakeEcs.PAGE * 2 + 5)]
    for arn in running:
        ecs.add(arn)
    ecs.add("arn:task/stopping", desired="STOPPED", last="DEPROVISIONING")
    ecs.add("arn:task/of-another-run", started_by="run-2")
    backend = types.SimpleNamespace(ecs=ecs, cluster="gherkai-cluster")

    assert reconciler._sweep("run-1", backend) == len(running)
    assert [c["task"] for c in ecs.stopped] == running
    assert len(ecs.listed) == 3  # 三页
    assert all((kw["cluster"], kw["startedBy"], kw["desiredStatus"]) == ("gherkai-cluster", "run-1", "RUNNING")
               for kw in ecs.listed)
    assert reconciler._sweep("run-1", backend) == 0 and len(ecs.stopped) == len(running)


def test_each_run_isolates_a_failing_run_and_fails_the_invocation_after_all(capsys):
    """失败与批的隔离（ADR 0054 决策九第 2 条）：每个 run 各自处理，一个的失败不打断同批排在它后面的；全部处理完之后有失败即抛出，让
    这次调用失败、由流重试（被拒方案「一批流记录遇错即抛」）。日志里留下失败那一个的回溯。"""
    done: list[str] = []

    def _fail():
        raise RuntimeError("读运行态被限流")

    work = [("run-1", _fail), ("run-2", lambda: done.append("run-2")), ("run-3", _fail), ("run-4", lambda: done.append("run-4"))]
    with pytest.raises(reconciler._RunsNotDone) as exc:
        reconciler._each_run("reconciler", work)
    assert done == ["run-2", "run-4"]
    assert exc.value.failed == ["run-1", "run-3"]
    out = capsys.readouterr().out
    assert out.count("RuntimeError: 读运行态被限流") == 2 and "Traceback" in out


def test_each_run_returns_normally_when_every_run_succeeds():
    assert reconciler._each_run("kicker", [("run-1", lambda: None), ("run-2", lambda: None)]) == {
        "ok": True, "runs": ["run-1", "run-2"]}


# ---------- moto 内存表上执行真 handler：闸、清扫、推进（含真 tick / 真 CAS）----------
# 后台执行标记只作描述、不参与任何判断（ADR 0034 端到端 cloud 1b）：带不带它的 run 推进相同。退出观察者不读 runs 表、对任何 run 都写
# 退出记录，见下面 test_exit_observer_records_every_exit_without_reading_the_runs_table。ECS 有两种：不需要看停了哪些 task 的用例用
# moto（夹具里建了 cluster，列 task 得到空表；RunTask 因没有任务定义而失败，由推进步骤的启动失败补偿收尾）；要看清扫的用例经
# `fake_ecs` 把组合根里那一个 ECS client 换成 `_FakeEcs`。

from moto import mock_aws  # noqa: E402

from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore  # noqa: E402

_RUNS_TABLE = "gherkai-runs"
_EVENTS_TABLE = "gherkai-events"
_BUCKET = "gherkai-artifacts"


def _jobs_objects():
    """提交一侧装配的 jobs 对象存取（同一个产物桶、命名真源的定义前缀，同 submit 经 compose 装配的那一份）。须在 cloud_env 之内调用。"""
    import boto3
    from gherkai_core.adapters.run_store.jobs_object import S3JobsObjects
    from gherkai_runtime import names

    return S3JobsObjects(boto3.client("s3", region_name="us-east-1"), _BUCKET, names.DEFINITIONS_PREFIX)


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
        boto3.client("ecs", region_name="us-east-1").create_cluster(clusterName="gherkai-cluster")
        for k, v in {"REGION": "us-east-1", "RUNS_TABLE": _RUNS_TABLE, "EVENTS_TABLE": _EVENTS_TABLE,
                     "ARTIFACTS_BUCKET": _BUCKET, "CLUSTER": "gherkai-cluster", "PREFIX": "gherkai-",
                     "SUBNETS": "subnet-1", "SECURITY_GROUPS": "sg-1",
                     # 部署侧 per-run cap（IaC 现值，ADR 0034 机制四）；单 job 的用例照样只起 1 个
                     "MAX_CONCURRENCY": "4"}.items():
            monkeypatch.setenv(k, v)
        yield {"runs": runs, "events": events}


@pytest.fixture
def fake_ecs(cloud_env, monkeypatch):
    """把组合根里那一个 ECS client 换成 `_FakeEcs`（清扫、job 到点停止与起 task 共用它），其余句柄照旧是 moto。"""
    import dataclasses

    ecs = _FakeEcs()
    real = reconciler._backend
    monkeypatch.setattr(reconciler, "_backend", lambda: dataclasses.replace(real(), ecs=ecs))
    return ecs


def _build(run_id: str):
    """过闸、装配，返回装配结果；闸不放行时返回 None。测试用的组合：生产里各入口各自调闸与装配。"""
    backend = reconciler._backend()
    result = reconciler._gate(run_id, backend)
    return reconciler._assemble(run_id, result.meta, backend) if result.gate is reconciler._Gate.ADMITTED else None


# 提交侧 preflight 解析出的 novaact worker revision ARN（ADR 0038）——**显式 revision、非 family 名**。
# 绝大多数用例只关心「推进器认不认 definition 里的这一份」，故 _seed_run 默认带上它（即打通后的正常形态）；
# 缺该字段的情形（定义违约：标 error、不解析默认指针）由下面专门那组用例显式置 None 来验。
_WORKER_REV = "arn:aws:ecs:us-east-1:000000000000:task-definition/gherkai-novaact-worker:7"
_SENTINEL = object()


def _seed_run(runs_table, *, detached: bool = True, max_concurrency: int | None = None,
              worker_task_defs=_SENTINEL, extra_http_headers=None, session_warmup_url=None,
              run_id: str = "run-1") -> DynamoDBRunStore:
    """建一个单 job、全 pending 的 run（后台执行标记按参数）——同 submit 的 create_run 形态。
    `extra_http_headers` / `session_warmup_url` 是隧道模式随 definition 走的两个值（ADR 0035 决策 4、ADR 0051 决策 13）。"""
    store = DynamoDBRunStore(runs_table, jobs_objects=_jobs_objects(), detached=detached)
    job = Job(scope_id="a", scope_name="a", engine="novaact",
              scenarios=(Scenario(id="a:1", name="s", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
    if worker_task_defs is _SENTINEL:
        worker_task_defs = {"novaact": _WORKER_REV}
    store.create_run(
        RunMeta(run_id=run_id, created_at="t0", jobs=(job,), max_concurrency=max_concurrency,
                worker_variant="base" if worker_task_defs else None,
                worker_task_defs=worker_task_defs,
                extra_http_headers=tuple(extra_http_headers.items()) if extra_http_headers else None,
                session_warmup_url=session_warmup_url, deadline_at="2999-01-01T00:00:00+00:00"),
        RunState(run_id=run_id, status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)},
                 started_at="t0"))
    return store


def test_reconciler_advances_a_run_without_the_background_flag(cloud_env):
    """后台执行标记不参与任何判断（ADR 0034 端到端 cloud 1b「触发过滤不看后台执行标记」）：不带它的 run 同样被推进、认领到那个 pending
    job。各入口按标记分流时这里失败。"""
    store = _seed_run(cloud_env["runs"], detached=False)
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING


def test_reconciler_ticks_detached_run(cloud_env):
    """对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、认领到那个 pending job。"""
    store = _seed_run(cloud_env["runs"], detached=True)
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING


def test_build_wires_jobs_objects_so_the_full_definition_reads_back(cloud_env):
    """`_build` 装的 RunStore 带 jobs 对象的存取（ADR 0030 决定六「云端提交记录」条的「装配」一项）：提交一侧写进定义前缀的 jobs
    对象读得回，DocString 正文原样。漏装则 load_run_meta 对每个 run 都抛装配缺失。"""
    body = "第一行\n第二行"
    store = DynamoDBRunStore(cloud_env["runs"], jobs_objects=_jobs_objects(), detached=True)
    job = Job(scope_id="a", scope_name="a", engine="novaact",
              scenarios=(Scenario(id="a:1", name="s",
                                  steps=(Step(0, "Given", "x",
                                              argument=StepArgument(kind="docString", content=body)),)),), timeout_s=300.0)
    store.create_run(
        RunMeta(run_id="run-1", created_at="t0", jobs=(job,), worker_variant="base",
                worker_task_defs={"novaact": _WORKER_REV}, deadline_at="2999-01-01T00:00:00+00:00"),
        RunState(run_id="run-1", status=Status.PENDING, jobs={"a": JobState("a", Status.PENDING)},
                 started_at="t0"))

    built = _build("run-1")
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

    built = _build("run-1")

    assert built is not None
    assert built[0].run_id == "run-1"   # META 真读回来了（装配可用，不是「钩子没执行因为整条路都没走」）


@pytest.mark.parametrize("prefix", ["gherkai-", "prod-"])
def test_build_arms_job_timeouts_in_the_schedule_group_of_the_deployed_prefix(cloud_env, monkeypatch, prefix):
    """`_build` 交给到点触发器的 group 名由部署前缀（env PREFIX）经命名真源推出，与 IaC 建 group、授 IAM 资源域同一个函数
    （ADR 0033 资源清单 15.）；目标与执行角色取 IaC 注入的 KICKER_ARN / SCHEDULER_ROLE_ARN。"""
    from gherkai_runtime import names

    monkeypatch.setenv("PREFIX", prefix)
    monkeypatch.setenv("KICKER_ARN", "arn:aws:lambda:us-east-1:000000000000:function:k")
    monkeypatch.setenv("SCHEDULER_ROLE_ARN", "arn:aws:iam::000000000000:role/r")
    seen: list[dict] = []
    real = reconciler.EventBridgeTimeoutWatch

    def _capture(client, **kw):
        seen.append(kw)
        return real(client, **kw)

    monkeypatch.setattr(reconciler, "EventBridgeTimeoutWatch", _capture)
    _seed_run(cloud_env["runs"], detached=True)

    assert _build("run-1") is not None
    assert seen == [{"kicker_arn": "arn:aws:lambda:us-east-1:000000000000:function:k",
                     "role_arn": "arn:aws:iam::000000000000:role/r",
                     "group_name": names.schedule_group_name(prefix)}]
    assert seen[0]["group_name"] == f"{prefix}schedules"


# ---------- 已收尾的 run 再被触发时各入口只清扫（判定真值销毁的第二道闸）----------

# 预置的那一份判定明细的标识（形态同 named_details.new_result_id：16 个小写十六进制字符）
_SEEDED_RESULT_ID = "5eed5eed5eed5eed"


def _seed_finished_run(cloud_env, *, status=Status.PASSED):
    """造「run 已收尾 + events 表只剩永不过期的退出记录」的形态，即 worker 事件被 TTL 删掉约 7 天后的真实样子，
    并预置那时已在 S3 的一份判定明细（键只由标识构成）与报告；job 已是终态时它的终态点名这一份，仍在执行时不点名。返回 (store, s3 client)。"""
    import boto3
    from gherkai_core.adapters.event_log import DdbEventLog
    from gherkai_core.model import TERMINAL_STATUSES

    store = DynamoDBRunStore(cloud_env["runs"], jobs_objects=_jobs_objects(), detached=True)
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


# 后端的各个入口（ADR 0054 决策九「落实时，后端各入口先过同一道闸」）：reconciler 处理 events 表流的记录，kicker 处理 runs 表流的两种
# 记录与 job 到点停止的触发。同一种情形在各入口得到同一种处理，下面几组用例对每个入口都核。
_ENTRIES = {
    "events-stream": lambda: reconciler.handler({"Records": [_stream_record("run-1#a")]}, None),
    "state-insert": lambda: reconciler.kicker_handler({"Records": [_runs_stream_record("run-1")]}, None),
    "ending-write": lambda: reconciler.kicker_handler({"Records": [_terminal_modify("run-1")]}, None),
    "job-timeout": lambda: reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None),
}


def _forbid_advancing(monkeypatch):
    """闸不放行的用例里，推进一步、job 到点停止与装配都不该发生。"""
    import gherkai_core.reconcile as _cr

    monkeypatch.setattr(_cr, "tick", lambda *a, **kw: pytest.fail("闸没有放行，不该推进"))
    monkeypatch.setattr(reconciler, "_handle_timeout", lambda *a, **kw: pytest.fail("闸没有放行，不该做 job 到点停止"))
    monkeypatch.setattr(reconciler, "_assemble", lambda *a, **kw: pytest.fail("闸没有放行，不该装配起 task 用的部分"))


def _runs_items(cloud_env) -> list[dict]:
    """runs 表里的全部条目（每个 run 的 META 与 STATE），按键排序：清扫前后比对它，核清扫不写 runs 表。"""
    items = cloud_env["runs"].scan(ConsistentRead=True)["Items"]
    return sorted(items, key=lambda i: (i["run_id"], i["item_type"]))


def _assert_swept_once(fake_ecs, *, stopped):
    """这次调用恰好清扫一次：按 run-1 的启动标识、期望状态「运行中」在部署的 cluster 里列 task，停掉的正是 stopped，StopTask 的说明不含
    超时哨兵（退出观察者据此不把这次退出记成超时）。"""
    assert fake_ecs.listed == [{"cluster": "gherkai-cluster", "startedBy": "run-1", "desiredStatus": "RUNNING"}]
    assert [c["task"] for c in fake_ecs.stopped] == stopped
    for call in fake_ecs.stopped:
        assert call["cluster"] == "gherkai-cluster"
        assert reconciler.TIMEOUT_STOP_SENTINEL not in call["reason"] and len(call["reason"]) <= 1024
        assert reconciler.exit_from_task({"stoppedReason": call["reason"], "containers": [{"exitCode": 143}]})[1] is False


@pytest.mark.parametrize("entry", sorted(_ENTRIES))
def test_finished_run_is_only_swept_by_a_late_or_replayed_trigger(cloud_env, fake_ecs, monkeypatch, entry):
    """已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒 / 到点时已结束）→ 各入口过闸读到已结束即
    清扫（ADR 0054 决策九第 2 条③「闸读到已结束」），不推演、不做 job 到点停止、不读提交记录的头：判定真值 jobs/*.json 与报告
    index.html **字节不变**，停掉的只有这个 run 仍在执行的 task。清扫不写 runs 表（同一条）：META 与 STATE 的每个属性都不变——已结束
    的 run 上一次改变了内容的写会产生状态分组不是 live 的 STATE 修改记录、再次唤醒 kicker，形成「清扫引出写、写再引出清扫」的回路。

    已收尾的 run 被重放推演的后果（那时 events 表只剩退出记录）见 ADR 0034 端到端流程 cloud 一节「已收尾的 run 不再推演」条。
    """
    store, s3 = _seed_finished_run(cloud_env)
    before = _report_bytes(s3)
    assert before, "预置报告没落进桶，断言会空转"
    fake_ecs.add("arn:task/started-after-the-end")
    fake_ecs.add("arn:task/of-another-run", started_by="run-2")
    _forbid_advancing(monkeypatch)
    monkeypatch.setattr(DynamoDBRunStore, "read_head", lambda self, rid: pytest.fail("已结束的 run 不读提交记录的头"))
    runs_before = _runs_items(cloud_env)

    assert _ENTRIES[entry]()["ok"] is True

    _assert_swept_once(fake_ecs, stopped=["arn:task/started-after-the-end"])
    assert _runs_items(cloud_env) == runs_before  # 清扫不写 runs 表
    assert _report_bytes(s3) == before          # 判定真值与报告一个字节没动
    assert store.load_run_state("run-1").status == Status.PASSED
    assert cloud_env["events"].scan()["Count"] == 1  # 零补偿写（launch 没被调过）


@pytest.mark.parametrize("entry", sorted(_ENTRIES))
def test_a_run_without_its_run_state_is_only_swept(cloud_env, fake_ecs, monkeypatch, entry):
    """运行态不存在即清扫（ADR 0054 决策九第 2 条①）：run 标识带随机尾、不会复用，没有要保护的记录；不读提交记录、不写。STATE 被删去
    的 run 的 task 由之后带到它的调用停下，各入口都走到这一条。"""
    import boto3

    _seed_run(cloud_env["runs"])
    cloud_env["runs"].delete_item(Key={"run_id": "run-1", "item_type": "STATE"})
    fake_ecs.add("arn:task/1")
    _forbid_advancing(monkeypatch)
    monkeypatch.setattr(DynamoDBRunStore, "read_head", lambda self, rid: pytest.fail("运行态不存在时不读提交记录"))
    head_before = cloud_env["runs"].scan()["Items"]

    assert _ENTRIES[entry]()["ok"] is True

    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])
    assert cloud_env["runs"].scan()["Items"] == head_before  # 没有任何写
    listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(Bucket=_BUCKET, Prefix="reports/")
    assert listed.get("Contents", []) == []


def _corrupt_state(cloud_env, run_id: str = "run-1", **attrs) -> dict:
    """把 STATE 条目的几个属性改成给定的值（模拟人为改动或环境损坏），返回改动之后的整个条目。"""
    item = cloud_env["runs"].get_item(Key={"run_id": run_id, "item_type": "STATE"}, ConsistentRead=True)["Item"]
    item.update(attrs)
    cloud_env["runs"].put_item(Item=item)
    return item


@pytest.mark.parametrize("entry", sorted(_ENTRIES))
def test_a_run_whose_common_part_is_unreadable_is_left_alone(cloud_env, fake_ecs, monkeypatch, capsys, entry):
    """运行态的公共部分读不出（ADR 0054 决策九「落实时」第一步）：只记一行日志，不写、不推进、不清扫，不读提交记录；不算这条记录的
    失败，调用照常返回（被拒方案「运行态读不出时各入口一律清扫」：分不清 run 是否已结束，清扫可能停掉仍在执行的 task）。"""
    _seed_run(cloud_env["runs"])
    corrupted = _corrupt_state(cloud_env, status="unknown-status")
    fake_ecs.add("arn:task/1")
    _forbid_advancing(monkeypatch)
    monkeypatch.setattr(DynamoDBRunStore, "read_head", lambda self, rid: pytest.fail("运行态读不出时不读提交记录"))

    assert _ENTRIES[entry]()["ok"] is True

    assert fake_ecs.listed == [] and fake_ecs.stopped == []
    assert cloud_env["runs"].get_item(Key={"run_id": "run-1", "item_type": "STATE"}, ConsistentRead=True)["Item"] == corrupted
    assert "运行状态记录读不出" in capsys.readouterr().out


def test_an_unreadable_run_does_not_hold_up_the_rest_of_the_batch(cloud_env, fake_ecs):
    """同批别的 run 照常（同一条）：一个 run 的运行态读不出，同一批里另一个 run 照常推进，调用照常返回。"""
    _seed_run(cloud_env["runs"], run_id="run-1")
    other = _seed_run(cloud_env["runs"], run_id="run-2")
    _corrupt_state(cloud_env, "run-1", jobs="不是 Map")
    out = reconciler.handler({"Records": [_stream_record("run-1#a"), _stream_record("run-2#a")]}, None)
    assert out == {"ok": True, "runs": ["run-1", "run-2"]}
    assert other.load_run_state("run-2").jobs["a"].status == Status.RUNNING
    assert len(fake_ecs.run_tasks) == 1 and fake_ecs.stopped == []


@pytest.mark.parametrize("entry", sorted(_ENTRIES))
def test_a_run_whose_remaining_attributes_are_unreadable_is_left_alone(cloud_env, fake_ecs, monkeypatch, capsys, entry):
    """头里的记录格式版本是后端的，按后端的格式读运行态的其余部分读不出（同一段第二步末项）：与公共部分读不出同样只记日志，不取
    jobs 对象、不写、不推进、不清扫，调用照常返回。各入口相同。"""
    from gherkai_core.adapters.run_store.jobs_object import S3JobsObjects

    _seed_run(cloud_env["runs"])
    corrupted = _corrupt_state(cloud_env, claim_count="许多")  # 公共部分之外的属性，本格式按整数读
    fake_ecs.add("arn:task/1")
    _forbid_advancing(monkeypatch)
    monkeypatch.setattr(S3JobsObjects, "get", lambda *a, **kw: pytest.fail("其余部分读不出时不取 jobs 对象"))

    assert _ENTRIES[entry]()["ok"] is True

    assert fake_ecs.listed == [] and fake_ecs.stopped == []
    assert cloud_env["runs"].get_item(Key={"run_id": "run-1", "item_type": "STATE"}, ConsistentRead=True)["Item"] == corrupted
    assert "运行状态记录读不出" in capsys.readouterr().out


def _head(cloud_env, run_id="run-1") -> dict:
    return cloud_env["runs"].get_item(Key={"run_id": run_id, "item_type": "META"}, ConsistentRead=True)["Item"]


def _record_jobs_object_reads(monkeypatch) -> list:
    from gherkai_core.adapters.run_store.jobs_object import S3JobsObjects

    reads: list = []
    real = S3JobsObjects.get
    monkeypatch.setattr(S3JobsObjects, "get", lambda self, *a, **kw: reads.append(a) or real(self, *a, **kw))
    return reads


def _change_head(cloud_env, case: str) -> None:
    """按 case 改写或删去提交记录的头（META）。记录格式版本不合的两种另把顶层的写出版本写成 `_WRITER_VERSION`：原因句要写出它。"""
    import json
    from decimal import Decimal

    head = _head(cloud_env)
    if case == "head-missing":
        cloud_env["runs"].delete_item(Key={"run_id": "run-1", "item_type": "META"})
        return
    if case == "version-not-an-integer":
        head["schema_version"] = Decimal("2.5")
    elif case == "version-a-string":
        head["schema_version"] = "2"
    elif case == "version-newer":
        head["schema_version"] = 3
        head["cli_version"] = _WRITER_VERSION
    elif case == "version-absent":
        del head["schema_version"]
        head["cli_version"] = _WRITER_VERSION
    elif case == "copy-disagrees":
        meta = json.loads(head["meta_json"])
        meta["schema_version"] = 3
        head["meta_json"] = json.dumps(meta, ensure_ascii=False)
    elif case == "meta-json-broken":
        head["meta_json"] = "{不是 JSON"
    elif case == "max-concurrency-a-string":
        meta = json.loads(head["meta_json"])
        meta["max_concurrency"] = "2"
        head["meta_json"] = json.dumps(meta, ensure_ascii=False)
    elif case == "headers-a-list":
        meta = json.loads(head["meta_json"])
        meta["extra_http_headers"] = ["x"]
        head["meta_json"] = json.dumps(meta, ensure_ascii=False)
    else:
        raise AssertionError(case)
    cloud_env["runs"].put_item(Item=head)


# 记录格式版本不合的两种用例里头上的写出版本：种子 run 不带写出版本（读作「版本未知」），用一个具体的值才照得出原因句漏传了它
_WRITER_VERSION = "9.9.0"


def _expected_reason(case: str) -> str:
    from gherkai_core.run_status import DEFINITION_CONTRACT_REASON, schema_mismatch_reason
    from gherkai_core.serialize import DEFINITION_SCHEMA_VERSION

    if case == "version-newer":
        return schema_mismatch_reason(3, DEFINITION_SCHEMA_VERSION, _WRITER_VERSION)
    if case == "version-absent":
        return schema_mismatch_reason(0, DEFINITION_SCHEMA_VERSION, _WRITER_VERSION)
    return DEFINITION_CONTRACT_REASON


@pytest.mark.parametrize("case", [
    "head-missing",            # 头不在
    "version-not-an-integer",  # 头里的记录格式版本不是整数
    "version-a-string",
    "version-newer",           # 不是后端的：不取 jobs 对象
    "version-absent",          # 缺这个属性读作 0，同样不是后端的
    "copy-disagrees",          # 顶层是后端的、meta_json 里的副本不是：两处本该恒同，按形态不对
    "meta-json-broken",        # 定义违约：契约异常的原文只进诊断行
    "headers-a-list",          # 定义违约，取回 jobs 对象之后拼回运行定义时才认出：不漏成读取失败、一再重试
    "max-concurrency-a-string",  # 同上：这个值到装配与认领时才用到，不在读定义时拒绝的话闸会放行、之后每次都以类型错误失败
])
@pytest.mark.parametrize("entry", sorted(_ENTRIES))
def test_an_unusable_submission_record_ends_the_run_with_the_error_ending_and_sweeps(cloud_env, fake_ecs, monkeypatch,
                                                                                       capsys, case, entry):
    """闸的第二步（ADR 0054 决策九「落实时」一段）：头不在、头里的记录格式版本不是整数或不是后端的、运行定义违约，都以结束写的 error
    变体结束这个 run（未结束的 job 与 run 都记 error，原因取 `run_status` 里那一句，ADR 0031 决定三「结束写」小节说明表下；记录格式
    版本不合的那一句写出取自头的写出版本），结束时刻是记录写法的时刻；之后清扫；不推进、不生成报告。记录格式版本不合的不取 jobs
    对象。各入口相同。"""
    import boto3
    from gherkai_core.serialize import instant_from_iso

    store = _seed_run(cloud_env["runs"])
    _change_head(cloud_env, case)
    fake_ecs.add("arn:task/1")
    _forbid_advancing(monkeypatch)
    reads = _record_jobs_object_reads(monkeypatch)

    assert _ENTRIES[entry]()["ok"] is True

    state = store.load_run_state("run-1")
    reason = _expected_reason(case)
    assert (state.status, state.message) == (Status.ERROR, reason)
    assert (state.jobs["a"].status, state.jobs["a"].message) == (Status.ERROR, reason)
    if case in ("version-newer", "version-absent"):
        assert _WRITER_VERSION in state.message
    instant_from_iso(state.ended_at)  # 带时区的记录写法，读不出即抛
    out = capsys.readouterr().out
    assert "不推进、标为 error" in out
    if case == "meta-json-broken":
        assert "不是合法的 JSON" in out and "不是合法的 JSON" not in state.message
    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])
    # 头与运行定义里的形态问题都在取 jobs 对象之前认出；拼回运行定义时才认出的，jobs 对象恰好取了一次
    assert len(reads) == (1 if case in ("headers-a-list", "max-concurrency-a-string") else 0)
    listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(Bucket=_BUCKET, Prefix="reports/run-1/")
    assert listed.get("Contents", []) == []  # error 变体之后不生成报告


def test_a_run_written_in_another_format_is_ended_without_reading_the_rest_of_its_state(cloud_env, fake_ecs):
    """头里的记录格式版本不是后端的：不按后端的格式读运行态的其余部分（同一段第二步）——这里其余部分按后端的格式读不出，run 照样以 error
    变体结束、被清扫；error 变体只写公共部分，公共部分之外的属性原样留下。"""
    store = _seed_run(cloud_env["runs"])
    _change_head(cloud_env, "version-newer")
    _corrupt_state(cloud_env, claim_count="许多")
    fake_ecs.add("arn:task/1")

    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)

    item = cloud_env["runs"].get_item(Key={"run_id": "run-1", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert (item["status"], item["jobs"]["a"]["status"], item["claim_count"]) == ("error", "error", "许多")
    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])
    del store


def test_the_error_ending_that_finds_the_run_already_ended_still_sweeps(cloud_env, fake_ecs, monkeypatch, capsys):
    """error 变体没写成、它重读到 run 已结束（别的写方先使 run 成为终态）时同样当场清扫（ADR 0054 决策九第 2 条③）；记录保持先结束它的
    那一方的结果。交错用钩子固定：闸读过运行态（未结束）之后、error 变体写之前，处置方以结束写结束了这个 run。"""
    from gherkai_core.run_status import RUN_ENDINGS

    store = _seed_run(cloud_env["runs"])
    cloud_env["runs"].delete_item(Key={"run_id": "run-1", "item_type": "META"})  # 头不在 → 走 error 变体
    fake_ecs.add("arn:task/1")
    real_read_head = DynamoDBRunStore.read_head

    def read_head_then_another_writer_ends_the_run(self, run_id):
        head = real_read_head(self, run_id)
        assert store.end_run(run_id, RUN_ENDINGS["settle-past-deadline"], ended_at="2026-11-26T00:00:00+00:00") is True
        return head

    monkeypatch.setattr(DynamoDBRunStore, "read_head", read_head_then_another_writer_ends_the_run)

    assert reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)["ok"] is True

    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.ABORTED, RUN_ENDINGS["settle-past-deadline"].run_message)
    assert "不推进、标为 error" not in capsys.readouterr().out
    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])


def test_the_error_ending_that_finds_the_run_state_unreadable_only_logs(cloud_env, fake_ecs, monkeypatch, capsys):
    """error 变体重读到的运行态公共部分读不出（它不写）：与闸里的「读不出」同样只记一行日志、不清扫、不算失败。交错用钩子固定：闸读过
    运行态之后、error 变体写之前，记录被改成读不出。"""
    _seed_run(cloud_env["runs"])
    cloud_env["runs"].delete_item(Key={"run_id": "run-1", "item_type": "META"})
    fake_ecs.add("arn:task/1")
    real_read_head = DynamoDBRunStore.read_head

    def read_head_then_the_state_is_corrupted(self, run_id):
        head = real_read_head(self, run_id)
        _corrupt_state(cloud_env, status="unknown-status")
        return head

    monkeypatch.setattr(DynamoDBRunStore, "read_head", read_head_then_the_state_is_corrupted)

    assert reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)["ok"] is True

    assert fake_ecs.listed == [] and fake_ecs.stopped == []
    out = capsys.readouterr().out
    assert "运行状态记录读不出" in out and "不推进、标为 error" not in out


def test_a_failed_error_ending_is_logged_and_fails_the_record(cloud_env, fake_ecs, monkeypatch, capsys):
    """结束写本身的失败原样抛出（同一段第二步末项），记为这条记录的失败、让这次调用失败；抛出之前记一行，带上原因与契约异常的原文，并说明
    标为 error 的写没有写成：这次写可能每次都写不成，日志里不能只剩回溯。没有写成就不清扫。"""
    from gherkai_core.run_status import DEFINITION_CONTRACT_REASON

    _seed_run(cloud_env["runs"])
    _change_head(cloud_env, "meta-json-broken")
    fake_ecs.add("arn:task/1")

    def _boom(self, run_id, reason, *, ended_at):
        raise RuntimeError("写不进运行状态")

    monkeypatch.setattr(DynamoDBRunStore, "end_run_as_error", _boom)

    with pytest.raises(reconciler._RunsNotDone):
        reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)

    lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("reject: run run-1 ")]
    assert len(lines) == 1 and DEFINITION_CONTRACT_REASON in lines[0] and "不是合法的 JSON" in lines[0]
    assert lines[0].endswith("把它标为 error 的写没有写成")
    assert fake_ecs.stopped == []


def _throttled_on(fault: str):
    """（AWS 调用的操作名, 参数）→ 是否让这一次调用被限流：只对 run-1 的那一种读生效。"""
    from gherkai_runtime import names

    def hit(operation_name: str, api_params: dict) -> bool:
        if fault in ("state-read", "head-read"):
            want = "STATE" if fault == "state-read" else "META"
            return operation_name == "GetItem" and api_params.get("Key") == {"run_id": "run-1", "item_type": want}
        return operation_name == "GetObject" and api_params.get("Key", "").startswith(f"{names.DEFINITIONS_PREFIX}run-1/")

    return hit


@pytest.mark.parametrize("fault", ["state-read", "head-read", "jobs-object-read"])
def test_a_read_failure_fails_only_its_own_record(cloud_env, fake_ecs, monkeypatch, fault):
    """闸里读取本身的错误原样抛出，记为这条记录的失败（ADR 0054 决策九「落实时」第一、二步）：读运行态、读提交记录的头、取 jobs
    对象被限流时，这个 run 不写、不清扫、不推进，同一批里另一个 run 照常推进，全部处理完之后这次调用失败、由流重试（同一决策第 2 条
    「失败与批的隔离」）。故障放在 AWS 调用这一层，经过 adapter 里的真实读法：读法把错误吞成「不存在」时，第一步会按运行态不存在清扫
    一个仍在执行的 run，第二步会以 error 变体结束一个正常的 run。"""
    import botocore.client
    from botocore.exceptions import ClientError

    _seed_run(cloud_env["runs"], run_id="run-1")
    other = _seed_run(cloud_env["runs"], run_id="run-2")
    fake_ecs.add("arn:task/1")
    runs_before = [i for i in _runs_items(cloud_env) if i["run_id"] == "run-1"]
    hit = _throttled_on(fault)
    real_call = botocore.client.BaseClient._make_api_call
    hits: list[str] = []

    def _make_api_call(self, operation_name, api_params):
        if hit(operation_name, api_params):
            hits.append(operation_name)
            code = "SlowDown" if operation_name == "GetObject" else "ProvisionedThroughputExceededException"
            raise ClientError({"Error": {"Code": code, "Message": "slow down"},
                               "ResponseMetadata": {"HTTPStatusCode": 503 if code == "SlowDown" else 400}}, operation_name)
        return real_call(self, operation_name, api_params)

    monkeypatch.setattr(botocore.client.BaseClient, "_make_api_call", _make_api_call)

    with pytest.raises(reconciler._RunsNotDone) as exc:
        reconciler.handler({"Records": [_stream_record("run-1#a"), _stream_record("run-2#a")]}, None)

    # 之后的读（Scan 与 run-2 的 GetItem）不落在故障上，替换不必撤回
    assert len(hits) == 1, "故障没有落在要核的那一次读上，断言会空转"
    assert exc.value.failed == ["run-1"]
    assert [i for i in _runs_items(cloud_env) if i["run_id"] == "run-1"] == runs_before  # 没有 error 变体，也没有别的写
    assert fake_ecs.stopped == [] and all(c["startedBy"] != "run-1" for c in fake_ecs.listed)  # 没有清扫
    assert other.load_run_state("run-2").jobs["a"].status == Status.RUNNING


def test_a_sweep_failure_fails_its_record_after_the_rest_of_the_batch(cloud_env, fake_ecs):
    """清扫的失败记为这条记录的失败（同一条）：已结束的 run-1 清扫失败，同一批里的 run-2 照常推进，这次调用最后失败。"""
    _seed_finished_run(cloud_env)
    other = _seed_run(cloud_env["runs"], run_id="run-2")
    real_list = fake_ecs.list_tasks

    def list_tasks(**kw):
        if kw.get("startedBy") == "run-1":
            raise RuntimeError("ListTasks 被限流")
        return real_list(**kw)

    fake_ecs.list_tasks = list_tasks

    with pytest.raises(reconciler._RunsNotDone) as exc:
        reconciler.kicker_handler({"Records": [_terminal_modify("run-1"), _runs_stream_record("run-2")]}, None)

    assert exc.value.failed == ["run-1"]
    assert other.load_run_state("run-2").jobs["a"].status == Status.RUNNING


def test_a_sweep_failure_on_a_job_timeout_trigger_fails_the_invocation(cloud_env, fake_ecs):
    """定时触发的调用只带一个 run：清扫的失败让这次调用失败，由 AWS 的重试再调用（同一条末句）。"""
    _seed_finished_run(cloud_env)

    def list_tasks(**kw):
        raise RuntimeError("ListTasks 被限流")

    fake_ecs.list_tasks = list_tasks
    with pytest.raises(reconciler._RunsNotDone):
        reconciler.kicker_handler({"run_id": "run-1", "timeout_scope": "a"}, None)


def test_a_stop_task_failure_fails_its_record_after_stopping_the_rest(cloud_env, fake_ecs):
    """清扫里 StopTask 的失败同样记为这条记录的失败（ADR 0054 决策九第 2 条「失败与批的隔离」）：同一个 run 列出的别的 task 照常停掉，
    同一批里的 run-2 照常推进，这次调用最后失败；重试时那个 task 仍列得出、被停下。"""
    _seed_finished_run(cloud_env)
    other = _seed_run(cloud_env["runs"], run_id="run-2")
    fake_ecs.add("arn:task/refused-once")
    fake_ecs.add("arn:task/stoppable")
    real_stop = fake_ecs.stop_task
    refused: list[str] = []

    def stop_task(**kw):
        if kw["task"] == "arn:task/refused-once" and not refused:
            refused.append(kw["task"])
            raise RuntimeError("StopTask 被限流")
        return real_stop(**kw)

    fake_ecs.stop_task = stop_task

    with pytest.raises(reconciler._RunsNotDone) as exc:
        reconciler.kicker_handler({"Records": [_terminal_modify("run-1"), _runs_stream_record("run-2")]}, None)

    assert exc.value.failed == ["run-1"]
    assert refused == ["arn:task/refused-once"]
    assert [c["task"] for c in fake_ecs.stopped] == ["arn:task/stoppable"]
    assert other.load_run_state("run-2").jobs["a"].status == Status.RUNNING

    # 流重试这一条：没有停掉的那个 task 仍列得出（期望状态仍是运行中），这一次停下
    assert reconciler.kicker_handler({"Records": [_terminal_modify("run-1")]}, None)["ok"] is True
    assert [c["task"] for c in fake_ecs.stopped] == ["arn:task/stoppable", "arn:task/refused-once"]


def test_a_batch_with_both_records_of_a_finished_run_passes_the_gate_once(cloud_env, fake_ecs, monkeypatch):
    """同一批里按 run 去重（ADR 0054 决策九第 2 条）：同一个 run 在同一批里既有 STATE 的新建又有终态写（流积压之后一次投递）时，真实的
    handler 只过一次闸、只清扫一次；run 已结束，不推进。"""
    _seed_finished_run(cloud_env)
    fake_ecs.add("arn:task/1")
    _forbid_advancing(monkeypatch)
    gates: list[str] = []
    real_gate = reconciler._gate
    monkeypatch.setattr(reconciler, "_gate", lambda rid, backend: gates.append(rid) or real_gate(rid, backend))

    out = reconciler.kicker_handler({"Records": [_runs_stream_record("run-1"), _terminal_modify("run-1")]}, None)

    assert out == {"ok": True, "runs": ["run-1"]}
    assert gates == ["run-1"]
    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])


@pytest.mark.parametrize("hook", ["after-head-read", "after-assemble"])
@pytest.mark.parametrize("entry", sorted(set(_ENTRIES) - {"ending-write"}))
def test_a_run_ended_between_the_gate_and_the_advance_is_only_swept(cloud_env, fake_ecs, monkeypatch, entry, hook):
    """闸是先读后判、不是原子的（`reconciler._gate`）：闸第一步读到未结束之后，别的写方结束了这个 run——落在读头之后（第二步仍按第一步
    读到的条目解读、放行），或落在放行与装配之后、推进步骤读运行态之前。推进步骤读到终态即停止推演（ADR 0034 机制三「run 级状态只进
    不退」条④），宿主只清扫（ADR 0054 决策九第 2 条③「推进步骤返回 run 已结束」）：不起 task、不生成报告，job 到点停止读到 job 已结束
    即不动手，记录保持另一方的结果。交错用钩子固定：在真实的读头或装配之后，处置方以结束写结束这个 run。终态写那一个入口过闸之后不推进，
    不在此列。"""
    import boto3
    from gherkai_core.run_status import RUN_ENDINGS

    store = _seed_run(cloud_env["runs"])
    fake_ecs.add("arn:task/1")
    after_the_other_writer: list[list[dict]] = []

    def another_writer_ends_the_run(run_id):
        assert store.end_run(run_id, RUN_ENDINGS["settle-past-deadline"], ended_at="2026-11-26T00:00:00+00:00") is True
        after_the_other_writer.append(_runs_items(cloud_env))

    if hook == "after-head-read":
        real_read_head = DynamoDBRunStore.read_head

        def read_head_then_the_run_ends(self, run_id):
            head = real_read_head(self, run_id)
            another_writer_ends_the_run(run_id)
            return head

        monkeypatch.setattr(DynamoDBRunStore, "read_head", read_head_then_the_run_ends)
    else:
        real_assemble = reconciler._assemble

        def assemble_then_the_run_ends(run_id, meta, backend):
            built = real_assemble(run_id, meta, backend)
            another_writer_ends_the_run(run_id)
            return built

        monkeypatch.setattr(reconciler, "_assemble", assemble_then_the_run_ends)

    assert _ENTRIES[entry]()["ok"] is True

    assert len(after_the_other_writer) == 1, "钩子没有走到，断言会空转"
    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])
    assert fake_ecs.run_tasks == []
    assert _runs_items(cloud_env) == after_the_other_writer[0]  # 记录保持处置方写下的结果
    assert store.load_run_state("run-1").status == Status.ABORTED
    listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(Bucket=_BUCKET, Prefix="reports/")
    assert listed.get("Contents", []) == []


def test_the_state_insert_starts_the_first_jobs_and_the_ending_write_only_sweeps(cloud_env, fake_ecs, monkeypatch):
    """kicker 按流记录的种类分派（ADR 0054 决策九第 1、2 条）：STATE 条目的新建过闸之后做首轮推进、认领并起首批 job；使 run 成为终态的
    那次写只过闸、清扫，不推进，也不写 runs 表（再写一次会再命中终态写的过滤、再次唤醒 kicker）。"""
    import gherkai_core.reconcile as _cr

    store = _seed_run(cloud_env["runs"])
    assert reconciler.kicker_handler({"Records": [_runs_stream_record("run-1")]}, None)["ok"] is True
    assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING
    assert len(fake_ecs.run_tasks) == 1 and fake_ecs.listed == []

    _seed_finished_run_from(cloud_env, store)
    monkeypatch.setattr(_cr, "tick", lambda *a, **kw: pytest.fail("终态写那一条只清扫，不推进"))
    runs_before = _runs_items(cloud_env)
    assert reconciler.kicker_handler({"Records": [_terminal_modify("run-1")]}, None)["ok"] is True
    _assert_swept_once(fake_ecs, stopped=["arn:task/started-1"])
    assert _runs_items(cloud_env) == runs_before


def _seed_finished_run_from(cloud_env, store) -> None:
    """把 run-1 以处置的结束写结束（使 run 成为终态的那次写），起过的 task 仍在执行。"""
    from gherkai_core.run_status import RUN_ENDINGS

    assert store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at="2026-11-26T00:00:00+00:00") is True


def test_the_ending_write_of_a_run_read_as_still_open_does_not_advance(cloud_env, fake_ecs, monkeypatch, capsys):
    """使 run 成为终态的那次写之后运行态不再变（ADR 0054 决策五），读到仍未结束只会出自记录被改动：终态写那一支过了闸也不推进、不清扫，
    记一行日志。"""
    import gherkai_core.reconcile as _cr

    _seed_run(cloud_env["runs"])
    monkeypatch.setattr(_cr, "tick", lambda *a, **kw: pytest.fail("终态写那一条只清扫，不推进"))
    assert reconciler.kicker_handler({"Records": [_terminal_modify("run-1")]}, None)["ok"] is True
    assert fake_ecs.listed == [] and "仍未结束" in capsys.readouterr().out


def test_the_committing_advance_writes_the_report_before_it_sweeps(cloud_env, fake_ecs):
    """推进步骤这一次写成了终态：先生成报告、再清扫（ADR 0054 决策九第 2 条③）。清扫列 task 的那一刻报告已在桶里。"""
    import boto3
    from gherkai_core.adapters.event_log import DdbEventLog

    store = _seed_run(cloud_env["runs"])
    assert store.try_claim_job("run-1", "a", claimed_at="2026-09-01T00:00:00+00:00") is True
    DdbEventLog(cloud_env["events"], "run-1", ["a"]).record_exit("a", 0)
    fake_ecs.add("arn:task/1")
    seen_report: list[bool] = []
    real_list = fake_ecs.list_tasks

    def list_tasks(**kw):
        listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(
            Bucket=_BUCKET, Prefix="reports/run-1/index.html").get("Contents", [])
        seen_report.append(bool(listed))
        return real_list(**kw)

    fake_ecs.list_tasks = list_tasks

    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)

    assert store.load_run_state("run-1").status == Status.ERROR  # exit=0 无 scope_done → error：这一方的终态写使 run 成为终态
    assert seen_report == [True]
    assert [c["task"] for c in fake_ecs.stopped] == ["arn:task/1"]


def test_finished_run_gate_keys_on_the_committed_run_status_only(cloud_env):
    """对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物）
    但 run 级仍 running（提交点还没落）时照常推进到收尾，说明挡住的是「已提交」而不是「有终态 job」。"""
    store, s3 = _seed_finished_run(cloud_env, status=Status.RUNNING)
    before = _report_bytes(s3)
    reconciler.handler({"Records": [_stream_record("run-1#a")]}, None)
    assert store.load_run_state("run-1").status == Status.ERROR  # 本 tick 真实运行到终态写（exit=0 无 scope_done → error）
    assert _report_bytes(s3) != before                           # 判定真值与报告由本 tick 写出


# ---------- 终态写之后为生成报告而读记录，失败不许击穿已到终态的 run（ADR 0030 决定三 / 0034 收尾）----------

def test_handler_returns_normally_when_the_record_read_for_the_report_fails(cloud_env, monkeypatch):
    """报告从记录组装，为生成而读 RunState 的那一次在这一方的终态写**之后**——那次强一致读抛（DDB 限流 / 瞬时 5xx）不许冒泡：
    终态写之后的失败无人重试，且在云端会让 events Stream 本批重试耗尽后整批丢弃，同批其它 run 的事件随之丢失（ADR 0034
    「端到端流程」cloud 第 ④ 步）。断言 handler 正常返回；判定明细与终态已落；读不到记录就不生成报告。
    """
    import boto3

    # 让 run 一 tick 就 done：job 已 CAS 成 running、events 表已有它的退出记录 → 本 tick 推成终态 → 终态写
    store = DynamoDBRunStore(cloud_env["runs"], jobs_objects=_jobs_objects(), detached=True)
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
    assert _build("run-1")[4] == 2


def test_build_clamps_meta_max_concurrency_to_cap(cloud_env, monkeypatch):
    """definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。"""
    monkeypatch.setenv("MAX_CONCURRENCY", "2")
    _seed_run(cloud_env["runs"], detached=True, max_concurrency=9)
    assert _build("run-1")[4] == 2


def test_build_defaults_to_one_when_meta_missing(cloud_env):
    """meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。"""
    _seed_run(cloud_env["runs"], detached=True, max_concurrency=None)
    assert _build("run-1")[4] == 1


def test_build_cap_defaults_to_one_when_env_absent(cloud_env, monkeypatch):
    """cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。

    **meta 必须声明 >1** 才验得动这条：meta 无值时 min(1, cap) 恒 1，缺省是 1 还是 4 都绿（非判别性断言）；
    声明 9 时 min 完全由缺省决定——回 1 则 1、若哪天缺省又被写成部署值 4 则 4，断言才真兜住。
    """
    monkeypatch.delenv("MAX_CONCURRENCY", raising=False)
    _seed_run(cloud_env["runs"], detached=True, max_concurrency=9)
    assert _build("run-1")[4] == 1


@pytest.mark.parametrize("seed", ["detached", "not-detached", "absent"])
def test_exit_observer_records_every_exit_without_reading_the_runs_table(cloud_env, monkeypatch, seed, tmp_path):
    """退出观察者不读 runs 表、不按后台执行标记分流（ADR 0033 资源清单 10.、ADR 0034 端到端流程 cloud 1b）：凡带 run 与 scope 标识
    的 task 停止都写退出记录，run 带不带后台执行标记、runs 表里有没有这个 run 都一样。runs 表在调用前删掉，推进器才有的几项环境变量
    （runs 表名、桶、cluster 等）也删去，任何一次读 runs 表、或依赖这几项之一都会让这里失败。区域只能从 REGION 取到：区域类环境变量删掉，
    AWS 配置文件与 profile 也指向不存在的位置，执行测试的机器上的配置不能替它补上区域。"""
    if seed != "absent":
        _seed_run(cloud_env["runs"], detached=(seed == "detached"))
    cloud_env["runs"].delete()
    for key in ("RUNS_TABLE", "ARTIFACTS_BUCKET", "CLUSTER", "PREFIX", "SUBNETS", "SECURITY_GROUPS", "MAX_CONCURRENCY",
                "AWS_DEFAULT_REGION", "AWS_REGION", "AWS_PROFILE", "AWS_DEFAULT_PROFILE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "no-config"))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(tmp_path / "no-credentials"))
    # boto3 的缺省 session 在夹具建 moto 表时已经建立、读过当时的配置文件并缓存下来；不换成新的，上面改的配置文件位置对 handler
    # 不起作用，机器上配置文件里的区域仍会替它补上
    import boto3
    monkeypatch.setattr(boto3, "DEFAULT_SESSION", None)
    assert {k for k in os.environ if k in ("EVENTS_TABLE", "REGION")} == {"EVENTS_TABLE", "REGION"}

    r = exit_observer.handler({"detail": _stopped_detail("run-1", "a", 0)}, None)

    assert r.get("ok") is True and "skipped" not in r
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
    engines = _build("run-1")[3]._resolver("novaact")
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

    built = _build("run-1")
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
    env = _build("run-1")[3]._resolver("novaact")._extra_env
    assert env["GHERKAI_SESSION_WARMUP_URL"] == url
    assert _json.loads(env["GHERKAI_EXTRA_HTTP_HEADERS"]) == {"ngrok-skip-browser-warning": "1"}


def test_build_without_tunnel_injects_no_warmup_env(cloud_env):
    """对偶：不经隧道的 run 不出现预热地址与额外请求头两个键（worker 以「有请求头没预热地址」判 definition 不完整，所以两键必须同在同缺）。"""
    _seed_run(cloud_env["runs"], detached=True)
    env = _build("run-1")[3]._resolver("novaact")._extra_env
    assert "GHERKAI_SESSION_WARMUP_URL" not in env and "GHERKAI_EXTRA_HTTP_HEADERS" not in env


def _jobs_object_keys_of(run_id: str) -> list[str]:
    import boto3
    from gherkai_runtime import names

    listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(
        Bucket=_BUCKET, Prefix=f"{names.DEFINITIONS_PREFIX}{run_id}/")
    return [o["Key"] for o in listed.get("Contents", [])]


@pytest.mark.parametrize("claimed", [False, True], ids=["pending-job", "running-job"])
def test_build_ends_the_run_with_the_error_ending_when_the_jobs_object_is_gone(cloud_env, fake_ecs, capsys, claimed):
    """提交记录的头还在、jobs 对象已被删去：推进 Lambda 取它得到「键不存在」，按运行定义不可用以结束写的 error 变体结束 run（ADR 0030
    决定六「jobs 对象取不到时」的后端一项）：未结束的 job 与 run 都记 error，说明是「提交记录不完整或形态不对」那一句；不推进、不生成
    报告，诊断行带上取不到的那个地址；之后清扫（ADR 0054 决策九第 2 条③）。"""
    import boto3
    from gherkai_core.run_status import DEFINITION_CONTRACT_REASON
    from gherkai_core.serialize import instant_from_iso

    store = _seed_run(cloud_env["runs"], detached=True)
    if claimed:
        assert store.try_claim_job("run-1", "a", claimed_at="2026-09-01T00:00:00+00:00") is True
    [key] = _jobs_object_keys_of("run-1")
    boto3.client("s3", region_name="us-east-1").delete_object(Bucket=_BUCKET, Key=key)
    fake_ecs.add("arn:task/1")

    assert _build("run-1") is None
    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])
    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.ERROR, DEFINITION_CONTRACT_REASON)
    assert (state.jobs["a"].status, state.jobs["a"].message) == (Status.ERROR, DEFINITION_CONTRACT_REASON)
    instant_from_iso(state.ended_at)  # 带时区的记录写法，读不出即抛
    out = capsys.readouterr().out
    assert "不推进、标为 error" in out and key in out
    listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(Bucket=_BUCKET, Prefix="reports/run-1/")
    assert listed.get("Contents", []) == []
    assert cloud_env["events"].scan()["Count"] == 0  # 没有推进（没有起 task 的失败补偿记录）


@pytest.mark.parametrize("case", ["access_denied", "no_such_bucket"])
def test_build_raises_other_jobs_object_errors_and_leaves_the_record(cloud_env, monkeypatch, case):
    """取 jobs 对象得到「键不存在」之外的错误（拒绝访问、桶不存在）：原样抛出、本次调用失败，由之后的触发再读；运行态不改，不记
    error。拒绝访问由替换后的 API 调用给出（替身上做不出缺权限的角色），桶不存在由头里改写的地址在替身上真实得到。"""
    import botocore.client
    from botocore.exceptions import ClientError

    from gherkai_core.adapters.run_store.jobs_object import JobsObjectFailure, JobsObjectUnreadable

    store = _seed_run(cloud_env["runs"], detached=True)
    head = cloud_env["runs"].get_item(Key={"run_id": "run-1", "item_type": "META"}, ConsistentRead=True)["Item"]
    if case == "access_denied":
        real_call = botocore.client.BaseClient._make_api_call

        def _make_api_call(self, operation_name, api_params):
            if operation_name == "GetObject":
                raise ClientError({"Error": {"Code": "AccessDenied", "Message": "Access Denied"},
                                   "ResponseMetadata": {"HTTPStatusCode": 403}}, operation_name)
            return real_call(self, operation_name, api_params)

        monkeypatch.setattr(botocore.client.BaseClient, "_make_api_call", _make_api_call)
        want = (JobsObjectFailure.ACCESS_DENIED, "AccessDenied")
    else:
        cloud_env["runs"].put_item(Item={**head, "jobs_ref": head["jobs_ref"].replace(_BUCKET, "no-such-bucket-gherkai-x", 1)})
        want = (JobsObjectFailure.OTHER, "NoSuchBucket")
    before = store.load_run_state("run-1")

    with pytest.raises(JobsObjectUnreadable) as exc:
        _build("run-1")
    assert (exc.value.failure, exc.value.error_code) == want
    monkeypatch.undo()
    assert store.load_run_state("run-1") == before
    assert before.status == Status.PENDING


@pytest.mark.parametrize("claimed", [False, True], ids=["pending-job", "running-job"])
def test_build_ends_the_run_with_the_error_ending_when_definition_lacks_worker_task_defs(cloud_env, fake_ecs, capsys,
                                                                                         claimed):
    """云端 definition 缺 worker_task_defs 是定义违约（ADR 0037 决策 7 不留兼容分支）：不按默认指针解析、不推进，记诊断，以结束写的
    error 变体结束 run（ADR 0031 决定三「结束写」小节「运行定义不可用、或 run 由别的格式写出时」条）：没有启动的与执行中的 job 都记
    error，run 级与 job 级说明都是同一句原因；这一写不生成报告，之后清扫。"""
    import boto3
    from gherkai_core.run_status import NO_WORKER_IMAGES_REASON
    from gherkai_core.serialize import instant_from_iso

    _seed_worker_ssm(variant="login", revision_arn="arn:must-not-be-used:9")
    store = _seed_run(cloud_env["runs"], detached=True, worker_task_defs=None)
    if claimed:
        assert store.try_claim_job("run-1", "a", claimed_at="2026-09-01T00:00:00+00:00") is True
    fake_ecs.add("arn:task/1")
    assert _build("run-1") is None
    _assert_swept_once(fake_ecs, stopped=["arn:task/1"])
    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.ERROR, NO_WORKER_IMAGES_REASON)
    assert (state.jobs["a"].status, state.jobs["a"].message) == (Status.ERROR, NO_WORKER_IMAGES_REASON)
    instant_from_iso(state.ended_at)  # 带时区的记录写法，读不出即抛
    out = capsys.readouterr().out
    assert "不推进、标为 error" in out and "worker-compat" not in out
    listed = boto3.client("s3", region_name="us-east-1").list_objects_v2(Bucket=_BUCKET, Prefix="reports/run-1/")
    assert listed.get("Contents", []) == []  # 不存明细、不生成报告


def test_kicker_uses_definition_worker_task_defs(cloud_env):
    """kicker 与 reconciler 共用闸与装配 → 同一条解析（不在 kicker 侧另起一套）：STATE 条目的新建过闸之后首轮推进。"""
    _seed_worker_ssm(revision_arn="arn:should-not-be-used:1")
    store = _seed_run(cloud_env["runs"], detached=True)
    reconciler.kicker_handler({"Records": [_runs_stream_record("run-1")]}, None)
    assert store.load_run_state("run-1").jobs["a"].status == Status.RUNNING  # 真 tick 运行到认领


def test_run_ids_scope_id_containing_hash_is_split_from_the_left():
    """scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条
    events Stream 会被抽成错的 run_id、reconciler 静默 no-op（主推进链断）。"""
    event = {"Records": [_stream_record("20260909T000000Z-a3f9c1#checkout#step-2")]}
    assert reconciler._run_ids_from_stream(event) == {"20260909T000000Z-a3f9c1"}


def test_handle_timeout_leaves_a_stopping_task_to_the_observer(timeout_built, tmp_path, monkeypatch):
    """task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING 列表里，但**不是**无踪：不动、
    不直写，等观察者的真退出记录（ADR 0034「job timeout」节）。曾按 RUNNING 列表判「无踪」直写 timed_out，与几秒后
    到达的真退出记录同键互覆——恰在预算点运行结束的 passed job 可被终判成 timeout。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(tasks=[{"arn": "arn:task/1", "lastStatus": "DEPROVISIONING", "desiredStatus": "STOPPED"}])
    built = timeout_built(tmp_path)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs)
    assert r == "noop-stopping" and ecs.stopped == []
    assert built[1].has_exit("a") is False  # 没直写


def test_handle_timeout_converges_from_describe_when_task_already_stopped(timeout_built, tmp_path, monkeypatch):
    """task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录
    （exit 0、非 timed_out、带 task 的执行停止时刻），不臆造 timeout；迟到的观察者写同内容同键、幂等。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    stopped_at = _dt.datetime(2026, 11, 8, 10, 4, 59, tzinfo=_dt.timezone.utc)
    ecs = _FakeEcs(tasks=[{"arn": "arn:task/1", "lastStatus": "STOPPED", "desiredStatus": "STOPPED",
                           "exitCode": 0, "stoppedReason": "Essential container in task exited",
                           "executionStoppedAt": stopped_at}])
    built = timeout_built(tmp_path)
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=ecs)
    assert r == "converged-from-describe" and ecs.stopped == []
    exits = {x.scope_id: x.exited for x in built[1].records() if x.kind == "exit"}
    assert exits["a"].exit_code == 0 and exits["a"].timed_out is False and exits["a"].reason is None
    assert exits["a"].exited_at == stopped_at


def test_handle_timeout_converges_from_describe_keeps_timeout_attribution_of_own_stop(timeout_built, tmp_path, monkeypatch):
    """上一轮已 StopTask（stoppedReason 带哨兵）、事件丢投、本轮再扫到它已 STOPPED → 落记录仍归因 timeout。"""
    monkeypatch.setenv("CLUSTER", "test-cluster")
    ecs = _FakeEcs(tasks=[{"arn": "arn:task/1", "lastStatus": "STOPPED", "desiredStatus": "STOPPED",
                           "exitCode": 143, "stoppedReason": f"{reconciler.TIMEOUT_STOP_SENTINEL}: scope exceeded 300s budget"}])
    built = timeout_built(tmp_path)
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
    built = _build("run-1")
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

    built = _build("run-1")
    clock = _Clock("2026-11-08T10:06:00+00:00")
    r = reconciler._handle_timeout("run-1", "a", built, ecs_client=_ObserverLandsWhileListing(), now_fn=clock.now,
                                   sleep_fn=clock.sleep)
    assert r == "noop-exit-in-flight"
    [exit_rec] = [x.exited for x in built[1].records() if x.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.exited_at) == (3, False, _EXEC_STOPPED)
