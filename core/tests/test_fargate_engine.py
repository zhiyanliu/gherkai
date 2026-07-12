"""FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。

**证据边界分流（CLAUDE.md「绿≠对」；moto ECS 状态机失真已实测确认，见 conftest.fargate docstring）**：
- **moto 忠实、用 `fargate` fixture 测**：run_scope 调对 RunTask（env 注入 JOB_S3_URI/events 表/run_id/scope_id）+
  PutObject job 到 S3；Query 迭代器增量拉 + last_seq 游标 + scope_done 终止；stop→StopTask。
- **moto 失真（exitCode 恒 0、lastStatus 由 describe 次数驱动）→ 退出码语义用「构造 describe 响应 dict」的纯单测**测
  `_task_exit_code`/`_raise_for_exit`（不经 moto、可造任意 exitCode）；真实 ECS 时序标定见 ADR 0032 真容器校准。

对拍 test_subprocess_engine.py：同一 Engine port、同一 (WorkerHandle, Iterator[Event]) 形状。
"""
from __future__ import annotations

import json

import boto3
import pytest

from core.adapters.fargate_engine import FargateEngine, FargateWorkerHandle, events_pk
from core.errors import WorkerNetworkError
from core.model import Job, Scenario, Step, ScopeStarted, StepDone, ScopeDone, Status


_RUN_ID = "20260707T120000Z-abc123"


def _job(scope_id: str = "browse") -> Job:
    return Job(
        scope_id=scope_id, scope_name=scope_id, engine="novaact",
        scenarios=(Scenario(id="sc:0", name="s", steps=(Step(index=0, keyword="When", text='"做事"'),)),),
        assertion_votes=1,
    )


def _put_event(events_table, run_id: str, scope_id: str, seq: int, event: dict) -> None:
    """模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。"""
    events_table.put_item(Item={
        "pk": events_pk(run_id, scope_id),
        "seq": seq,
        "body": json.dumps(event, ensure_ascii=False),
    })


def _engine(fargate, run_id: str = _RUN_ID, region: str | None = None,
            artifact_s3: tuple[str, str] | None = None, sdk_artifact_dir_env: dict | None = None) -> FargateEngine:
    return FargateEngine(
        ecs_client=fargate["ecs"], s3_client=fargate["s3"], ddb_events_table=fargate["events_table"],
        run_id=run_id, cluster=fargate["cluster"], task_definition=fargate["task_def"],
        network_config=fargate["network_config"], job_s3=(fargate["bucket"], f"{run_id}/jobs/"),
        events_table_name=fargate["events_table_name"], container_name=fargate["container_name"],
        artifact_s3=artifact_s3, sdk_artifact_dir_env=sdk_artifact_dir_env, region=region,
        poll_interval_s=0.01,  # 测试快轮询（不接 profile——容器用 task role）
    )


def _spy_run_task_env(fargate, monkeypatch, eng) -> dict:
    """跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。"""
    real = fargate["ecs"].run_task
    captured = {}
    monkeypatch.setattr(fargate["ecs"], "run_task", lambda **kw: captured.update(kw) or real(**kw))
    eng.run_scope(_job("browse"))
    return {e["name"]: e["value"] for e in captured["overrides"]["containerOverrides"][0]["environment"]}


# ---- events_pk：复合键防重复跑撞（ADR 0024）----
def test_events_pk_composite_run_id_scope_id():
    assert events_pk("run-A", "browse") == "run-A#browse"
    # 同 feature 重复跑（scope_id 同、run_id 异）→ PK 不同、不撞
    assert events_pk("run-A", "browse") != events_pk("run-B", "browse")


# ---- run_scope：PutObject job + RunTask 注入 env（moto 忠实）----
def test_run_scope_puts_job_to_s3(fargate):
    eng = _engine(fargate)
    job = _job()
    # worker 尚未写事件；先只验 run_scope 的 job-in 侧（不消费迭代器、避免阻塞等 STOPPED）
    handle, _events = eng.run_scope(job)
    assert isinstance(handle, FargateWorkerHandle)
    # job 已 PutObject 到 s3://bucket/<run_id>/jobs/<scope_id>.json，内容 = job_to_line
    obj = fargate["s3"].get_object(Bucket=fargate["bucket"], Key=f"{_RUN_ID}/jobs/browse.json")
    body = obj["Body"].read().decode("utf-8").strip()
    assert json.loads(body)["scope"]["id"] == "browse"


def test_run_scope_job_key_quotes_scope_id(fargate):
    # scope_id 含 `/`:（如 feature 路径 features/x.feature:7）→ job key 用 quote(safe='')：/ 编码成 %2F、: 成 %3A，
    # 不造 S3 假子前缀、与 S3ResultStore（同 quote）一致（真跑暴露的一致性缺陷回归守卫）。
    from urllib.parse import quote
    eng = _engine(fargate)
    sid = "features/deterministic_anchor.feature:7"
    handle, _events = eng.run_scope(_job(sid))
    expected_key = f"{_RUN_ID}/jobs/{quote(sid, safe='')}.json"  # features%2Fdeterministic_anchor.feature%3A7.json
    obj = fargate["s3"].get_object(Bucket=fargate["bucket"], Key=expected_key)  # 能取到＝key 用了 quote
    assert json.loads(obj["Body"].read().decode("utf-8"))["scope"]["id"] == sid
    assert "%2F" in expected_key and "%3A" in expected_key  # 确认 / 和 : 都被编码（不造子前缀）


def test_run_scope_runtask_injects_env(fargate, monkeypatch):
    # 拦 ecs.run_task 记录 env 注入（验 JOB_S3_URI/EVENTS_DDB_TABLE/RUN_ID/SCOPE_ID 都传对）
    real_run_task = fargate["ecs"].run_task
    captured = {}

    def _spy(**kw):
        captured.update(kw)
        return real_run_task(**kw)

    monkeypatch.setattr(fargate["ecs"], "run_task", _spy)
    eng = _engine(fargate)
    eng.run_scope(_job("browse"))
    # env 注入在 containerOverrides
    env = {e["name"]: e["value"] for e in captured["overrides"]["containerOverrides"][0]["environment"]}
    assert env["RUN_ID"] == _RUN_ID
    assert env["SCOPE_ID"] == "browse"
    assert env["EVENTS_DDB_TABLE"] == fargate["events_table_name"]
    assert env["JOB_S3_URI"] == f"s3://{fargate['bucket']}/{_RUN_ID}/jobs/browse.json"
    assert captured["launchType"] == "FARGATE"
    assert captured["taskDefinition"] == fargate["task_def"]


def test_run_scope_injects_region_never_profile(fargate, monkeypatch):
    # region 非 None（组合根落实成具体字符串，ADR 0016 决策 C）→ overrides env 注入 AWS_REGION，与 core store 同源。
    # Fargate 容器不继承本地 env、不吃 profile config，不注入 region 则 worker → NoRegionError/AgentCore InvalidRegionError。
    # **AWS_PROFILE 绝不注入**（正确的非对称）：容器用 task role，注入 profile 名会 ProfileNotFound 盖过 task role。
    env = _spy_run_task_env(fargate, monkeypatch, _engine(fargate, region="us-west-2"))
    assert env["AWS_REGION"] == "us-west-2"
    assert "AWS_PROFILE" not in env  # FargateEngine 根本不接 profile 参数、绝不注入


def test_run_scope_omits_region_when_none(fargate, monkeypatch):
    # region=None（真无 region）→ 不注入（不硬写空值、留 fail-loud）。AWS_PROFILE 同样从不注入。
    env = _spy_run_task_env(fargate, monkeypatch, _engine(fargate, region=None))
    assert "AWS_REGION" not in env
    assert "AWS_PROFILE" not in env


def test_run_scope_injects_artifact_s3_env(fargate, monkeypatch):
    # artifact_s3 非 None（cloud 必注入，ADR 0029）→ overrides env 注入 ARTIFACT_S3_BUCKET/PREFIX，worker
    # ArtifactUploader 据此上传→报 s3://→删本地。**不注入则容器盘停即销毁、产物必丢**（ADR 0029/0032）——这条守卫防回归。
    env = _spy_run_task_env(fargate, monkeypatch, _engine(fargate, artifact_s3=("bkt", "reports/rid-1/")))
    assert env["ARTIFACT_S3_BUCKET"] == "bkt"
    assert env["ARTIFACT_S3_PREFIX"] == "reports/rid-1/"


def test_run_scope_omits_artifact_s3_when_none(fargate, monkeypatch):
    # artifact_s3=None（不上传，如无 report 落点）→ 不注入 ARTIFACT_S3_*（worker no-op 报 file://）。
    env = _spy_run_task_env(fargate, monkeypatch, _engine(fargate, artifact_s3=None))
    assert "ARTIFACT_S3_BUCKET" not in env
    assert "ARTIFACT_S3_PREFIX" not in env


def test_run_scope_injects_sdk_artifact_dir_env(fargate, monkeypatch):
    # SDK 产物落点 env（NOVA_LOGS_DIR 等）也须注入——**否则 worker ArtifactUploader run_dir=None→no-op→产物随容器盘销毁丢**
    # （真跑暴露：只注 ARTIFACT_S3_* 不够，uploader 还要 SDK 落点 env 算 run_dir/相对 key）。这条守卫防回归。
    env = _spy_run_task_env(fargate, monkeypatch,
                            _engine(fargate, sdk_artifact_dir_env={"NOVA_LOGS_DIR": "/tmp/gherkai-run/rid/nova-trajectories"}))
    assert env["NOVA_LOGS_DIR"] == "/tmp/gherkai-run/rid/nova-trajectories"


# ---- Query 迭代器：增量拉 + 保序 + scope_done 终止（moto DDB 忠实）----
def test_read_events_yields_in_seq_order_until_scope_done(fargate):
    eng = _engine(fargate)
    job = _job("browse")
    # 先把整个事件流写进 events 表（模拟 worker 已跑完、事件都落了）——含 scope_done 作终止
    _put_event(fargate["events_table"], _RUN_ID, "browse", 1, {"type": "scope_started", "scopeId": "browse", "sessionId": "s-1"})
    _put_event(fargate["events_table"], _RUN_ID, "browse", 2, {"type": "step_started", "scenarioId": "sc:0", "stepIndex": 0})
    _put_event(fargate["events_table"], _RUN_ID, "browse", 3, {"type": "step_done", "scenarioId": "sc:0", "stepIndex": 0, "status": "passed"})
    _put_event(fargate["events_table"], _RUN_ID, "browse", 4, {"type": "scope_done", "scopeId": "browse", "sessionId": "s-1"})
    _, events = eng.run_scope(job)
    got = list(events)  # scope_done 终止迭代（不必等 STOPPED）
    assert [type(e).__name__ for e in got] == ["ScopeStarted", "StepStarted", "StepDone", "ScopeDone"]
    assert isinstance(got[0], ScopeStarted) and got[0].session_id == "s-1"
    assert isinstance(got[2], StepDone) and got[2].status == Status.PASSED
    assert isinstance(got[-1], ScopeDone)


def test_read_events_only_this_scope_not_other(fargate):
    # 天然定向（ADR 0024 核心）：Query PK=run_id#scope_id 只返回本 scope，别的 scope 的事件不混入
    eng = _engine(fargate)
    # 写两个 scope 的事件到同一表
    _put_event(fargate["events_table"], _RUN_ID, "browse", 1, {"type": "scope_started", "scopeId": "browse"})
    _put_event(fargate["events_table"], _RUN_ID, "browse", 2, {"type": "scope_done", "scopeId": "browse"})
    _put_event(fargate["events_table"], _RUN_ID, "search", 1, {"type": "scope_started", "scopeId": "search"})
    _put_event(fargate["events_table"], _RUN_ID, "search", 2, {"type": "scope_done", "scopeId": "search"})
    _, events = eng.run_scope(_job("browse"))
    got = list(events)
    # 只拿到 browse 的（scope_started + scope_done 各一），无 search 的。强断言：每条 scope_id 都是 browse
    # （ScopeStarted/ScopeDone 都带 scope_id；直接断言值，不用 getattr 默认+hasattr 过滤那种自我豁免的弱断言）。
    assert len(got) == 2
    assert [e.scope_id for e in got] == ["browse", "browse"]  # 无 search 混入（天然定向）
    assert all(getattr(e, "scope_id", "browse") == "browse" for e in got if hasattr(e, "scope_id"))


def test_read_events_incremental_across_polls(fargate):
    # last_seq 游标：分批到达的事件按序拉全（模拟轮询间隙 worker 又写了新事件）
    eng = _engine(fargate)
    _put_event(fargate["events_table"], _RUN_ID, "browse", 1, {"type": "scope_started", "scopeId": "browse"})
    _, events = eng.run_scope(_job("browse"))
    it = iter(events)
    assert isinstance(next(it), ScopeStarted)  # 拿到第一批
    # 轮询间隙 worker 写了 scope_done
    _put_event(fargate["events_table"], _RUN_ID, "browse", 2, {"type": "scope_done", "scopeId": "browse"})
    assert isinstance(next(it), ScopeDone)  # 下一轮 Query SK>1 拿到它、终止
    with pytest.raises(StopIteration):
        next(it)


def test_read_events_midscene_lowlevel_marshalling_and_ascending_read(fargate):
    # 跨引擎编组同构 + 升序读（ADR 0024）：Midscene 那个引擎走**低层** PutItemCommand（attribute 显式 {N:String(seq)}/{S}），
    # Nova 那个引擎走 resource.put_item（原生 int）——两条不同 API 层，都须落成 core Query 能读的**同构** item。现有测试的
    # _put_event 走 resource（=Nova 形态），此处补 Midscene 低层形态：直接经低层 client 写 {N:"..."}。
    # **本测试真正锁住的（诚实边界，勿夸大）**：
    #   ① 跨层编组同构——低层 client 写的 {N}/{S} item，core 的 resource.Table Query 能读出（len==11、类型对）。
    #      若两个引擎编组不兼容（如 Midscene 误写 {S} 进 N-key），moto 直接 ClientError 拒；core 读不出则 len≠11。
    #   ② 升序读——引擎若误用 ScanIndexForward=False（降序）本测试会红（实测变异确认）。
    # **不锁的**：① 「漏 ScanIndexForward」不会红——moto 默认即按 sort-key 升序返回（本测试预写也是升序），故这条
    #   决策靠此测试守不住（记账诚实，别声称锁了跨 9/10 数值重排）；② 「seq 误存 String」不由本测试兜——它全程手写
    #   {N}、不调 EventSink，String-wire 回归由 event-sink 单测（seq.N 断言）+ events 表 N-key schema（moto 拒 {S} 入 N-key）兜。
    # moto 对 DDB 数据模型（N-key 编组/拒 {S}、sort-key 升序）保真（已探针证实），非「绿≠对」被 mock 掉的真实时序，可 moto 真验。
    # 真低层 client（同一 moto 后端）：dynamodb **resource** 的 .meta.client 挂了高层序列化 handler、会把 {S:..} 再编组成 M，
    # 故直接建低层 client 写原始 attribute-value，精确模拟 Midscene 的 PutItemCommand({N:String(seq)}) 线格式。
    low = boto3.client("dynamodb", region_name="us-east-1")
    pk = f"{_RUN_ID}#browse"
    # 写 seq 1..11（跨 9/10 边界），末条 scope_done 终止；全部用 Midscene 低层 attribute 形态
    for i in range(1, 11):
        low.put_item(TableName=fargate["events_table_name"], Item={
            "pk": {"S": pk}, "seq": {"N": str(i)},
            "body": {"S": json.dumps({"type": "step_done", "scenarioId": "sc:0", "stepIndex": i - 1, "status": "passed"})},
        })
    low.put_item(TableName=fargate["events_table_name"], Item={
        "pk": {"S": pk}, "seq": {"N": "11"},
        "body": {"S": json.dumps({"type": "scope_done", "scopeId": "browse"})},
    })
    eng = _engine(fargate)
    got = list(eng.run_scope(_job("browse"))[1])
    # 11 条全读出（低层写的 item core 能 Query＝跨层编组同构）、升序（step 0..9 依次——引擎误用降序读会红）
    assert len(got) == 11
    assert [type(e).__name__ for e in got] == ["StepDone"] * 10 + ["ScopeDone"]
    assert [e.step_index for e in got[:10]] == list(range(10))  # 升序读（跨 9/10 边界；moto 默认即升序，故此断言守降序误用、不守漏 ScanIndexForward）


# ---- STOPPED 兜底终止 + _final_drain（worker 崩溃没发 scope_done）----
# 这条兜底路径（DescribeTasks STOPPED → _final_drain 强一致补末尾 → _raise_for_exit）不依赖真实 ECS 时序、
# 全是确定性控制流 + 强一致 DDB Query（moto 可测），故**不在**真实 ECS 时序标定（ADR 0032 真容器校准）之列，须锁住「先 drain 后 raise」次序。
# moto fargate fixture 的 ecs 被 pin 成 lastStatus 恒不推进（见 conftest），故这里用可控假 ecs 造 RUNNING→STOPPED 时序。
def test_read_events_stopped_without_scope_done_drains_then_raises(fargate):
    """worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。"""
    eng = _engine(fargate)
    # 已落事件：seq 1（scope_started），**无 scope_done**（模拟 worker 中途崩）
    _put_event(fargate["events_table"], _RUN_ID, "browse", 1, {"type": "scope_started", "scopeId": "browse"})

    # 假 ecs：describe_tasks 首次调用（= 主循环第二轮 not items 后查退出码）才「变 STOPPED」，并在此刻补写一条
    # 末尾事件 seq 2（模拟：STOPPED 后强一致 drain 才看得到的、最终一致主循环漏掉的末尾 PutItem）。
    state = {"describe_calls": 0}

    class _StoppingEcs:
        def describe_tasks(self, **kw):
            state["describe_calls"] += 1
            # 第一次被查退出码时：补末尾事件（仅 _final_drain 的强一致读能拿到）+ 返回 STOPPED/exitCode=137
            _put_event(fargate["events_table"], _RUN_ID, "browse", 2,
                       {"type": "step_done", "scenarioId": "sc:0", "stepIndex": 0, "status": "error"})
            return {"tasks": [{"lastStatus": "STOPPED", "containers": [{"name": fargate["container_name"], "exitCode": 137}]}]}

    _, events = eng.run_scope(_job("browse"))  # run_scope 用真 moto ecs 发 RunTask
    eng._ecs = _StoppingEcs()  # 此后 _read_events 的 describe 走假 ecs（控 STOPPED 时序，moto 的 ecs 不推进 lastStatus）

    got = []
    with pytest.raises(RuntimeError, match="137"):
        for e in events:
            got.append(e)
    # 先 yield 出 scope_started（主循环）+ 末尾 step_done（_final_drain 强一致补），再抛 —— 次序不可颠倒、drain 不可漏
    assert [type(e).__name__ for e in got] == ["ScopeStarted", "StepDone"]
    assert state["describe_calls"] >= 1  # 确实走了 STOPPED 兜底、非 scope_done 主判


def test_final_drain_paginates_across_last_evaluated_key():
    """_final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环 ExclusiveStartKey 会丢事件。

    构造假 events table（query 按有无 ExclusiveStartKey 返回不同页）——moto 难造 >1MB 分页，此处精确验
    「首页带 LastEvaluatedKey → 续 ExclusiveStartKey 拉次页 → 拉全所有 item」的分页语义。
    """
    pk = f"{_RUN_ID}#browse"

    def _line(seq: int) -> str:
        return json.dumps({"type": "step_done", "scenarioId": "sc:0", "stepIndex": seq, "status": "passed"})

    class _PagingTable:
        def __init__(self):
            self.calls = []  # 记录每次 query 是否带 ExclusiveStartKey

        def query(self, **kw):
            self.calls.append(kw)
            if "ExclusiveStartKey" not in kw:
                # 首页：seq 2,3 + LastEvaluatedKey（模拟 1MB 单页截断）
                return {"Items": [{"seq": 2, "body": _line(2)}, {"seq": 3, "body": _line(3)}],
                        "LastEvaluatedKey": {"pk": pk, "seq": 3}}
            # 次页（带 ExclusiveStartKey）：seq 4,5，无 LastEvaluatedKey（末页）
            return {"Items": [{"seq": 4, "body": _line(4)}, {"seq": 5, "body": _line(5)}]}

    eng = FargateEngine.__new__(FargateEngine)
    eng._events = _PagingTable()
    got = list(eng._final_drain(pk, last_seq=1))
    # 两页全拉出（不因单次 query 只返首页而丢 seq 4,5）——分页守卫防回归
    assert [e.step_index for e in got] == [2, 3, 4, 5]
    assert len(eng._events.calls) == 2  # 翻了第二页
    assert eng._events.calls[1]["ExclusiveStartKey"] == {"pk": pk, "seq": 3}  # 用首页 LastEvaluatedKey 续读


def test_read_events_stopped_clean_exit_zero_terminates_without_raise(fargate):
    """worker 干净退出（exitCode 0）但没发 scope_done：drain 后正常终止、不抛。"""
    eng = _engine(fargate)
    _put_event(fargate["events_table"], _RUN_ID, "browse", 1, {"type": "scope_started", "scopeId": "browse"})

    class _StoppedCleanEcs:
        def describe_tasks(self, **kw):
            return {"tasks": [{"lastStatus": "STOPPED", "containers": [{"name": fargate["container_name"], "exitCode": 0}]}]}

    _, events = eng.run_scope(_job("browse"))
    eng._ecs = _StoppedCleanEcs()
    got = list(events)  # 不抛：exit 0 → _raise_for_exit 放行 → return
    assert [type(e).__name__ for e in got] == ["ScopeStarted"]


# ---- run_task 放置失败（failures 非空）→ 明确异常，非裸 IndexError ----
def test_run_scope_runtask_failure_raises_meaningful_error(fargate, monkeypatch):
    """RunTask 容量不足/子网无 IP 等 → HTTP 200 + 空 tasks + failures。须翻成带 reason 的明确异常，非 IndexError。"""
    monkeypatch.setattr(fargate["ecs"], "run_task",
                        lambda **kw: {"tasks": [], "failures": [{"reason": "RESOURCE:MEMORY", "detail": "no capacity"}]})
    eng = _engine(fargate)
    with pytest.raises(RuntimeError, match="RESOURCE:MEMORY"):
        eng.run_scope(_job("browse"))


# ---- stop → StopTask（moto 忠实）----
def test_handle_stop_calls_stop_task(fargate, monkeypatch):
    eng = _engine(fargate)
    handle, _ = eng.run_scope(_job())
    called = {}
    monkeypatch.setattr(fargate["ecs"], "stop_task", lambda **kw: called.update(kw) or {"task": {}})
    handle.stop(grace_period_s=30.0)  # grace 被忽略（Fargate stopTimeout 决定，ADR 0024）——只验发了 StopTask
    assert called["cluster"] == fargate["cluster"]
    assert "task" in called


# ---- 退出码解析 + 翻异常：moto exitCode 恒 0 失真 → 纯单测构造 describe 响应 dict ----
class _FakeEcs:
    """构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe 次数驱动，测不了退出码语义）。"""
    def __init__(self, describe_response):
        self._resp = describe_response
    def describe_tasks(self, **kw):
        return self._resp


def _engine_with_fake_ecs(describe_response, container_name="worker") -> FargateEngine:
    # 只测 _task_exit_code/_raise_for_exit，不跑 run_scope；其余注入 None（不触及）
    eng = FargateEngine.__new__(FargateEngine)
    eng._ecs = _FakeEcs(describe_response)
    eng._cluster = "c"
    eng._container = container_name
    return eng


def test_task_exit_code_none_when_not_stopped():
    # 未 STOPPED → None（继续轮询）
    eng = _engine_with_fake_ecs({"tasks": [{"lastStatus": "RUNNING", "containers": [{"name": "worker"}]}]})
    assert eng._task_exit_code("arn") is None


def test_task_exit_code_reads_stopped_exit_code():
    eng = _engine_with_fake_ecs({"tasks": [{"lastStatus": "STOPPED", "containers": [{"name": "worker", "exitCode": 0}]}]})
    assert eng._task_exit_code("arn") == 0
    eng2 = _engine_with_fake_ecs({"tasks": [{"lastStatus": "STOPPED", "containers": [{"name": "worker", "exitCode": 137}]}]})
    assert eng2._task_exit_code("arn") == 137


def test_task_exit_code_null_exitcode_treated_as_error():
    # STOPPED 但 exitCode=null（容器没正常报退出码）→ 当异常（1），不当成功
    eng = _engine_with_fake_ecs({"tasks": [{"lastStatus": "STOPPED", "containers": [{"name": "worker", "exitCode": None}]}]})
    assert eng._task_exit_code("arn") == 1


def test_raise_for_exit_maps_codes():
    eng = _engine_with_fake_ecs({})
    eng._raise_for_exit(0)  # 正常，不抛
    with pytest.raises(WorkerNetworkError):
        eng._raise_for_exit(80)  # 网络专用码（ADR 0028）
    with pytest.raises(RuntimeError):
        eng._raise_for_exit(1)   # 其余正非零
