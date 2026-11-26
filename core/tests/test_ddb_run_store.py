"""DynamoDBRunStore 对拍测试（ADR 0030 决定六）：与 LocalRunStore 同一批行为断言，moto mock、不产生真实 AWS 费用。

对拍的是**后端无关的行为契约**（create/load round-trip、实时写生命周期、Map 单元素刷、未 create 报错、
omit-null 时间戳）——即 test_stores.py 里 LocalRunStore 那批。物理落点断言（文件存在/JSON 是 list）是
Local 专属、不在此。复用 test_stores 的 _sample_run/_initial_state 造数据。DDB 一侧才有的：云端提交记录的头加 jobs 对象（ADR 0030
决定六「云端提交记录」条：形态、读整份定义、取不到时的类别、装配缺失、建 run 的三次条件写与各步留下的），jobs Map 条目里点名标识的
键，以及终态写被写入序号挡下、重读再算时点名的仍是同一个标识。
"""
from __future__ import annotations

import json

import pytest

from gherkai_core.errors import RunAlreadyExists
from gherkai_core.model import JobState, Status
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from tests.test_stores import _initial_state, _sample_run


# ---- create/load round-trip（对拍 test_run_store_create_load）----
def test_create_load_round_trip(ddb_run_store):
    r = _sample_run("run-1")
    ddb_run_store.create_run(r.run_meta, r.state)

    # definition 读回
    meta = ddb_run_store.load_run_meta("run-1")
    assert meta is not None and meta.run_id == "run-1" and meta.created_at == "2026-06-29T00:00:00Z"
    assert len(meta.jobs) == 2 and meta.jobs[0].scope_id == "features/wiki.feature:6"
    # definition 深树完整重建（含 assertion_votes 非默认值）
    assert meta.jobs[0].scenarios[0].steps[1].text == "搜索 OpenAI"
    assert meta.jobs[0].assertion_votes == 3

    # 运行态读回（jobs 是 Map，按 scope_id 取）
    state = ddb_run_store.load_run_state("run-1")
    assert state is not None and state.status == Status.FAILED
    j0 = state.jobs["features/wiki.feature:6"]
    j1 = state.jobs["登录场景"]
    assert j0.status == Status.PASSED and j0.session_id == "sess-1"
    assert j1.status == Status.FAILED


def test_load_missing_returns_none(ddb_run_store):
    assert ddb_run_store.load_run_meta("nope") is None
    assert ddb_run_store.load_run_state("nope") is None


def _deep_meta(run_id: str):
    """step 参数齐全的运行定义：DataTable 含空 cell，一个 scenario 里有两段多行 DocString，scope 标识含中文。用它核的是 step 参数
    整份内联进 jobs 对象之后原样往返、头里不带 step 正文；正文的具体取值不承担别的检查。"""
    from gherkai_core.model import Job, RunMeta, RunState, Scenario, Step, StepArgument, Status

    job = Job(scope_id="features/表单.feature:3", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="features/表单.feature:3", name="sc", steps=(
            Step(0, "When", "填表", StepArgument(kind="dataTable", rows=(("k", "v"), ("", "空cell")))),
            Step(1, "Then", "看结果", StepArgument(kind="docString", content="第一段正文\n多行\n内容")),
            Step(2, "Then", "再看", StepArgument(kind="docString", content="同一 scenario 的第二段正文")),
        )),
    ), timeout_s=300.0)
    meta = RunMeta(run_id=run_id, created_at="t", jobs=(job,), deadline_at="2026-01-01T01:00:00+00:00")
    return meta, RunState(run_id=run_id, status=Status.PENDING, jobs={job.scope_id: JobState(job.scope_id, Status.PENDING)})


def _jobs_object_keys(aws, run_id: str) -> list[str]:
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix=f"definitions/{run_id}/")
    return sorted(o["Key"] for o in listed.get("Contents", []))


def test_run_meta_deep_argument_round_trip_through_the_jobs_object(aws, ddb_run_store):
    """运行定义经 jobs 对象往返：读回的与写入的相同（空 cell、多行正文原样）；jobs 对象的内容就是
    `run_meta_to_dict` 产出的 jobs，step 参数原样内联其中；头的 meta_json 里没有 jobs。"""
    from gherkai_core.serialize import run_meta_to_dict

    meta, state = _deep_meta("deep")
    ddb_run_store.create_run(meta, state)

    assert ddb_run_store.load_run_meta("deep") == meta
    [key] = _jobs_object_keys(aws, "deep")
    body = aws["s3"].get_object(Bucket=aws["bucket"], Key=key)["Body"].read()
    assert json.loads(body) == run_meta_to_dict(meta)["jobs"]
    head = aws["ddb"].Table(aws["table_name"]).get_item(Key={"run_id": "deep", "item_type": "META"})["Item"]
    assert "jobs" not in json.loads(head["meta_json"])
    assert "填表" not in head["meta_json"] and "空cell" not in head["meta_json"]


def test_head_carries_the_top_level_attributes_and_does_not_grow_with_jobs(aws, ddb_run_store):
    """头的顶层属性恰是键属性、三个副本、jobs_ref 与 meta_json；jobs_ref 指向 definitions/<run_id>/ 下的 jobs 对象；job 数从 1 到 200，
    头的大小不变。"""
    import dataclasses
    import re

    from gherkai_core.model import Job, Scenario, Step

    table = aws["ddb"].Table(aws["table_name"])

    def head_of(run_id: str, n_jobs: int) -> dict:
        jobs = tuple(Job(scope_id=f"f.feature:{i}", scope_name="s", engine="novaact", timeout_s=300.0, scenarios=(
            Scenario(id=f"f.feature:{i}", name="sc", steps=(Step(0, "Given", "一步" * 20),)),)) for i in range(n_jobs))
        meta = dataclasses.replace(_deep_meta(run_id)[0], jobs=jobs)
        ddb_run_store.create_run(meta, _initial_state(run_id, [j.scope_id for j in jobs]))
        return table.get_item(Key={"run_id": run_id, "item_type": "META"})["Item"]

    small, large = head_of("h-1", 1), head_of("h-200", 200)
    assert set(small) == {"run_id", "item_type", "schema_version", "cli_version", "deadline_at", "jobs_ref", "meta_json"}
    assert re.fullmatch(r"s3://gherkai-artifacts/definitions/h-1/[0-9a-f]{32}\.json", small["jobs_ref"])
    assert small["jobs_ref"] == f"s3://{aws['bucket']}/{_jobs_object_keys(aws, 'h-1')[0]}"
    assert len(small["meta_json"]) == len(large["meta_json"].replace("h-200", "h-1"))


# ---- 实时写生命周期（对拍 test_realtime_write_lifecycle）----
def test_realtime_write_lifecycle(ddb_run_store):
    meta = _sample_run("rt-run").run_meta
    scope_ids = ["features/wiki.feature:6", "登录场景"]

    # 1) 开始：全 pending
    ddb_run_store.create_run(meta, _initial_state("rt-run", scope_ids))
    s0 = ddb_run_store.load_run_state("rt-run")
    assert s0 is not None and s0.status == Status.PENDING
    assert all(js.status == Status.PENDING for js in s0.jobs.values())
    assert ddb_run_store.load_run_meta("rt-run") is not None  # definition 也落了

    # 2) 一个 job 开始运行 → running（带血缘）；中途读到部分完成态（Map 单元素刷不互相污染）
    ddb_run_store.update_job_state("rt-run", JobState("features/wiki.feature:6", Status.RUNNING, session_id="sess-1"))
    mid = ddb_run_store.load_run_state("rt-run")
    assert mid.jobs["features/wiki.feature:6"].status == Status.RUNNING
    assert mid.jobs["features/wiki.feature:6"].session_id == "sess-1"
    assert mid.jobs["登录场景"].status == Status.PENDING   # 另一个没动
    assert mid.status == Status.RUNNING                      # job 记为 running 时 run 级随之为 running

    # 3) 第一个 job 完成：终态写记下它，run 仍 running、没有结束时刻
    assert ddb_run_store.commit_job_states(
        "rt-run", [JobState("features/wiki.feature:6", Status.PASSED, session_id="sess-1")],
        ended_at="2026-07-01T00:04:00Z") is CommitOutcome.OPEN
    s2 = ddb_run_store.load_run_state("rt-run")
    assert s2.jobs["features/wiki.feature:6"].status == Status.PASSED
    assert (s2.status, s2.ended_at) == (Status.RUNNING, None)

    # 4) 最后一个 job 完成：这次终态写使 run 成为终态，run 状态按取法写下，同一次写下结束时刻；各 job 态保留
    assert ddb_run_store.commit_job_states("rt-run", [JobState("登录场景", Status.FAILED)],
                                           ended_at="2026-07-01T00:05:00Z") is CommitOutcome.ENDED_RUN
    final = ddb_run_store.load_run_state("rt-run")
    assert final.status == Status.FAILED
    assert final.ended_at == "2026-07-01T00:05:00Z"
    assert final.started_at == "2026-07-01T00:00:00Z"  # create_run 填的起点保留
    assert final.jobs["features/wiki.feature:6"] == JobState("features/wiki.feature:6", Status.PASSED, session_id="sess-1")
    assert final.jobs["登录场景"].status == Status.FAILED


def test_writes_before_create_raise_or_write_nothing(ddb_run_store):
    # 未 create_run 就写 → 执行中的写与终态写报错（对拍 local：条件不成立且带回的条目为空 → FileNotFoundError）；结束写写不成；
    # 都不臆造 STATE
    with pytest.raises(FileNotFoundError):
        ddb_run_store.update_job_state("nope", JobState("s", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        ddb_run_store.commit_job_states("nope", [JobState("s", Status.PASSED)], ended_at="t")
    assert ddb_run_store.end_run("nope", RUN_ENDINGS["deadline"], ended_at="t") is False
    assert ddb_run_store.load_run_state("nope") is None


def test_session_id_none_omitted_and_roundtrips(ddb_run_store):
    # session_id=None：omit-when-None（不写该键），读回仍 None（对拍 local/serialize 语义）
    meta = _sample_run("s-run").run_meta
    ddb_run_store.create_run(meta, _initial_state("s-run", ["features/wiki.feature:6", "登录场景"]))
    assert ddb_run_store.update_job_state("s-run", JobState("登录场景", Status.RUNNING, session_id=None)) is True
    js = ddb_run_store.load_run_state("s-run").jobs["登录场景"]
    assert js.status == Status.RUNNING and js.session_id is None


def test_started_ended_omit_when_none_round_trip(ddb_run_store):
    # 起止为 None 时不写、读回仍 None；非 None 时完整保留（对拍 test_run_state_omits/timestamps）
    meta = _sample_run("ts-run").run_meta
    # 初始态 started 填、ended 缺
    ddb_run_store.create_run(meta, _initial_state("ts-run", ["s"]))
    got = ddb_run_store.load_run_state("ts-run")
    assert got.started_at == "2026-07-01T00:00:00Z" and got.ended_at is None
    # 使 run 成为终态的那次写之后 ended 出现
    assert ddb_run_store.commit_job_states("ts-run", [JobState("s", Status.PASSED)],
                                           ended_at="2026-07-01T01:00:00Z") is CommitOutcome.ENDED_RUN
    got2 = ddb_run_store.load_run_state("ts-run")
    assert got2.ended_at == "2026-07-01T01:00:00Z"


def test_detached_flag_on_state_item(aws, jobs_objects):
    """detached 组合根的 create_run 在 STATE item 落 detached=true 标记;默认不落。标记只作描述（`list-runs --json` 的 `detached`
    键），触发过滤与云端后端各入口都不看它（ADR 0034 端到端 cloud 1b「触发过滤不看后台执行标记」）。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

    def _mk(run_id):
        job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=(
            Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
        meta = RunMeta(run_id=run_id, created_at="t", jobs=(job,), deadline_at="2026-01-01T01:00:00+00:00")
        state = RunState(run_id=run_id, status=Status.PENDING,
                         jobs={"s": JobState("s", Status.PENDING)}, started_at="t")
        return meta, state

    table = aws["ddb"].Table(aws["table_name"])
    meta, state = _mk("det-1")
    DynamoDBRunStore(table, jobs_objects=jobs_objects, detached=True).create_run(meta, state)
    item = table.get_item(Key={"run_id": "det-1", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item.get("detached") is True

    meta, state = _mk("sync-1")
    DynamoDBRunStore(table, jobs_objects=jobs_objects).create_run(meta, state)  # 默认不带
    item = table.get_item(Key={"run_id": "sync-1", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert "detached" not in item

    # 只读访问器:读同一个标记,未知 run 判 False
    reader = DynamoDBRunStore(table)
    assert reader.is_detached("det-1") is True
    assert reader.is_detached("sync-1") is False
    assert reader.is_detached("没这个 run") is False


def test_worker_task_def_arns_on_state_item(aws, jobs_objects):
    """create_run 把 definition 的 worker revision ARN 摊平成 STATE 顶层属性（ADR 0038 清理 pass 的运行中 run 引用检查）。

    为什么必须摊平：同一批 ARN 也在 definition 里，但那在 META 的 `meta_json` 字符串内、DDB 查不动；清理 pass
    要按 `status` GSI Query 非终态 run + `contains` 过滤引用，只有顶层属性做得到（沿用 `detached` 顶层标记先例）。
    未设 → 属性缺席（`contains` 对缺属性天然不匹配，语义即「未引用」）——不落空 list。
    """
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

    # 属性名写死在此（**不 import `gherkai_runtime.names`**：core 是窄腰下层，其测试也不该反向依赖组合根
    # 共享层）。与读端命名真源 `names.STATE_WORKER_TASK_DEF_ARNS_ATTR` 的逐字一致由 runtime 侧的对拍测试
    # `runtime/tests/test_names_worker.py` 守——那里能同时看见两边。
    ATTR = "worker_task_def_arns"

    def _mk(run_id, worker_task_defs=None):
        job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=(
            Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
        meta = RunMeta(run_id=run_id, created_at="t", jobs=(job,),
                       worker_task_defs=worker_task_defs, deadline_at="2026-01-01T01:00:00+00:00")
        state = RunState(run_id=run_id, status=Status.PENDING,
                         jobs={"s": JobState("s", Status.PENDING)}, started_at="t")
        return meta, state

    table = aws["ddb"].Table(aws["table_name"])
    nova = "arn:aws:ecs:us-east-1:1:task-definition/gherkai-novaact-worker:7"
    mid = "arn:aws:ecs:us-east-1:1:task-definition/gherkai-midscene-worker:3"
    meta, state = _mk("wk-1", {"novaact": nova, "midscene": mid})
    DynamoDBRunStore(table, jobs_objects=jobs_objects).create_run(meta, state)
    item = table.get_item(Key={"run_id": "wk-1", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item[ATTR] == sorted([nova, mid])  # list of ARN、稳定排序（item 可比对）

    # 两引擎共用同一 revision（同一 variant 名跨引擎、极端下 ARN 相同）→ 去重，不留重复项
    meta, state = _mk("wk-dup", {"novaact": nova, "midscene": nova})
    DynamoDBRunStore(table, jobs_objects=jobs_objects).create_run(meta, state)
    item = table.get_item(Key={"run_id": "wk-dup", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item[ATTR] == [nova]

    # 旧 definition / 本机后端（无该字段）→ 属性缺席
    meta, state = _mk("wk-none")
    DynamoDBRunStore(table, jobs_objects=jobs_objects).create_run(meta, state)
    item = table.get_item(Key={"run_id": "wk-none", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert ATTR not in item


# ---- definition 结构版本摊成 META 顶层属性 + 轻量读头（ADR 0037 决策 7）----
def test_meta_item_carries_schema_header_top_level_and_peek_reads_only_it(ddb_run_store):
    import dataclasses

    from gherkai_core.errors import UnsupportedDefinitionSchema
    r = _sample_run("hdr")
    ddb_run_store.create_run(dataclasses.replace(r.run_meta, cli_version="1.5.0"), r.state)
    assert ddb_run_store.peek_definition_header("hdr") == (2, "1.5.0")
    assert ddb_run_store.peek_definition_header("nope") is None
    raw = ddb_run_store._table.get_item(Key={"run_id": "hdr", "item_type": "META"})["Item"]
    assert int(raw["schema_version"]) == 2 and raw["cli_version"] == "1.5.0"   # 顶层属性与 meta_json 同值
    # 运行期限同样摊成顶层属性（ADR 0054 决策二），值与 meta_json 里的同名键恒同，读回的 definition 也带着它
    assert raw["deadline_at"] == json.loads(raw["meta_json"])["deadline_at"] == r.run_meta.deadline_at
    assert ddb_run_store.load_run_meta("hdr").deadline_at == r.run_meta.deadline_at
    # 没有顶层属性的 META（早于结构版本号的写端）：读头得 (0, None)，整读按版本不符拒绝
    ddb_run_store._table.put_item(Item={"run_id": "old", "item_type": "META",
                                        "meta_json": '{"run_id": "old", "created_at": "", "jobs": []}'})
    assert ddb_run_store.peek_definition_header("old") == (0, None)
    with pytest.raises(UnsupportedDefinitionSchema):
        ddb_run_store.load_run_meta("old")


@pytest.mark.parametrize("bad", ["1", True], ids=["string", "bool"])
def test_peek_rejects_non_integer_schema_attribute(ddb_run_store, bad):
    from gherkai_core.errors import DefinitionContractError

    ddb_run_store._table.put_item(Item={"run_id": "weird", "item_type": "META", "schema_version": bad, "meta_json": "{}"})
    with pytest.raises(DefinitionContractError, match="schema_version 须为整数"):
        ddb_run_store.peek_definition_header("weird")


def test_peek_rejects_fractional_and_accepts_integral_decimal(ddb_run_store):
    from decimal import Decimal

    from gherkai_core.errors import DefinitionContractError

    ddb_run_store._table.put_item(Item={"run_id": "frac", "item_type": "META", "schema_version": Decimal("1.9"), "meta_json": "{}"})
    with pytest.raises(DefinitionContractError):
        ddb_run_store.peek_definition_header("frac")
    ddb_run_store._table.put_item(Item={"run_id": "whole", "item_type": "META", "schema_version": Decimal("1"), "cli_version": "1.5.0", "meta_json": "{}"})
    assert ddb_run_store.peek_definition_header("whole") == (1, "1.5.0")


# ---- 云端后端各入口共用的闸用到的两种读（ADR 0054 决策九「落实时，后端各入口先过同一道闸」）----
def _pending_run(run_id: str):
    from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=(
        Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
    return (RunMeta(run_id=run_id, created_at="t", jobs=(job,), deadline_at="2026-01-01T01:00:00+00:00"),
            RunState(run_id=run_id, status=Status.PENDING, jobs={"s": JobState("s", Status.PENDING)}, started_at="t"))


def _state_item(store, run_id: str) -> dict:
    return store._table.get_item(Key={"run_id": run_id, "item_type": "STATE"}, ConsistentRead=True)["Item"]


def test_read_state_common_gives_the_four_outcomes_from_one_strongly_consistent_read(ddb_run_store, monkeypatch):
    """闸的第一步只读一次 STATE（强一致），按公共部分分出四种：不存在为 None；公共部分读不出抛 RunStateUnreadable（判据与 error 变体
    同一处）；读得出时已结束与未结束由 `ended` 分开（只看 run 级状态，状态分组缺席不算读不出）。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable

    reads: list[dict] = []
    real = ddb_run_store._table.get_item
    monkeypatch.setattr(ddb_run_store._table, "get_item", lambda **kw: reads.append(kw) or real(**kw))

    assert ddb_run_store.read_state_common("nope") is None
    meta, state = _pending_run("open")
    ddb_run_store.create_run(meta, state)
    reads.clear()
    common = ddb_run_store.read_state_common("open")
    assert (common.status, common.ended) == ("pending", False)
    assert len(reads) == 1 and reads[0]["ConsistentRead"] is True and reads[0]["Key"]["item_type"] == "STATE"
    item = _state_item(ddb_run_store, "open")
    assert common.item == item

    item.pop("status_group")
    ddb_run_store._table.put_item(Item={**item, "status": "passed", "jobs": {"s": {"status": "passed"}}})
    assert ddb_run_store.read_state_common("open").ended is True

    for broken in ({"status": "unknown-status"}, {"jobs": "不是 Map"}, {"jobs": {"s": {"status": "?"}}},
                   {"write_seq": "x"}):
        ddb_run_store._table.put_item(Item={**item, **broken})
        with pytest.raises(RunStateUnreadable):
            ddb_run_store.read_state_common("open")


def test_state_from_common_reads_the_rest_from_the_same_item_and_reports_it_unreadable(ddb_run_store, monkeypatch):
    """闸的第二步按本格式读运行态的其余部分：解析第一步读到的同一个条目、不另读；公共部分读得出而其余部分按本格式读不出时抛
    RunStateUnreadable。"""
    from gherkai_core.adapters.run_store.ddb import RunStateUnreadable

    meta, state = _pending_run("r")
    ddb_run_store.create_run(meta, state)
    common = ddb_run_store.read_state_common("r")
    monkeypatch.setattr(ddb_run_store._table, "get_item", lambda **kw: pytest.fail("不另读"))
    assert ddb_run_store.state_from_common(common) == state
    monkeypatch.undo()

    ddb_run_store._table.put_item(Item={**_state_item(ddb_run_store, "r"), "claim_count": "许多"})
    with pytest.raises(RunStateUnreadable):
        ddb_run_store.state_from_common(ddb_run_store.read_state_common("r"))


def test_read_head_reads_the_head_once_without_the_jobs_object(aws, ddb_run_store, monkeypatch):
    """闸的第二步先只读头（强一致、整个 META 条目，不取 jobs 对象），看头里的记录格式版本；是本格式的再由同一份头拼回整份运行定义，
    头不另读、jobs 对象只取一次。`load_run_meta` 是这两步的合成，结果相同，读头同样强一致。

    强一致只能在调用参数上核：替身不模拟最终一致。真实的表上退回最终一致时，kicker 由 STATE 的新建触发、META 只早一次写，可能读到
    「头不在」，闸会以 error 变体结束一个刚提交的正常 run。"""
    from decimal import Decimal

    from gherkai_core.errors import DefinitionContractError

    meta, state = _deep_meta("h")
    ddb_run_store.create_run(meta, state)
    fetched = _recording_get_object(aws, monkeypatch)
    real = ddb_run_store._table.get_item
    reads: list[dict] = []
    monkeypatch.setattr(ddb_run_store._table, "get_item", lambda **kw: reads.append(kw) or real(**kw))
    assert ddb_run_store.read_head("nope") is None
    head = ddb_run_store.read_head("h")
    assert (head.schema_version(), head.cli_version) == (2, meta.cli_version)
    assert fetched == []
    meta_reads = [{"Key": {"run_id": rid, "item_type": "META"}, "ConsistentRead": True} for rid in ("nope", "h")]
    assert reads == meta_reads
    monkeypatch.setattr(ddb_run_store._table, "get_item", lambda **kw: pytest.fail("头不另读"))
    assert ddb_run_store.meta_from_head(head) == meta
    assert len(fetched) == 1
    reads.clear()
    monkeypatch.setattr(ddb_run_store._table, "get_item", lambda **kw: reads.append(kw) or real(**kw))
    assert ddb_run_store.load_run_meta("h") == meta
    assert reads == meta_reads[1:]
    monkeypatch.setattr(ddb_run_store._table, "get_item", real)

    raw = _head(aws, "h")
    for value, want in ((None, 0), ("2", DefinitionContractError), (Decimal("2.5"), DefinitionContractError),
                        (True, DefinitionContractError)):
        item = {k: v for k, v in raw.items() if k != "schema_version"}
        if value is not None:
            item["schema_version"] = value
        ddb_run_store._table.put_item(Item=item)
        head = ddb_run_store.read_head("h")
        if want is DefinitionContractError:
            with pytest.raises(DefinitionContractError):
                head.schema_version()
        else:
            assert head.schema_version() == want


def test_the_head_carries_the_deadline_without_the_jobs_object(aws, ddb_run_store, monkeypatch):
    """头顶层的运行期限（ADR 0054 决策二「落点是运行定义」一段）随读头带回：运行态读不出时后端到期结束只读头里的记录格式版本与期限，
    不取 jobs 对象、不拼回运行定义（ADR 0054 决策九「落实时」一段第一步）。与运行定义里的期限是同一个时刻；缺失、不是字符串、不带时区或
    读不出的都是定义违约。"""
    from decimal import Decimal

    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.run_deadline import deadline_of

    meta, state = _pending_run("d")
    ddb_run_store.create_run(meta, state)
    fetched = _recording_get_object(aws, monkeypatch)
    assert ddb_run_store.read_head("d").deadline() == deadline_of(meta)
    assert fetched == []

    raw = _head(aws, "d")
    for value in (None, Decimal(7), "2026-11-08T10:00:00", "不是时刻"):
        item = {k: v for k, v in raw.items() if k != "deadline_at"}
        if value is not None:
            item["deadline_at"] = value
        ddb_run_store._table.put_item(Item=item)
        with pytest.raises(DefinitionContractError, match="deadline_at"):
            ddb_run_store.read_head("d").deadline()


@pytest.mark.parametrize("meta_json", [None, 7], ids=["absent", "not-a-string"])
def test_meta_from_head_reports_a_head_without_meta_json_as_a_contract_error(aws, ddb_run_store, meta_json):
    """头缺 meta_json 或它不是字符串：定义违约（推进器据此以 error 变体结束），不是别的异常。"""
    from gherkai_core.errors import DefinitionContractError

    meta, state = _pending_run("m")
    ddb_run_store.create_run(meta, state)
    item = {k: v for k, v in _head(aws, "m").items() if k != "meta_json"}
    if meta_json is not None:
        item["meta_json"] = meta_json
    ddb_run_store._table.put_item(Item=item)
    with pytest.raises(DefinitionContractError, match="meta_json"):
        ddb_run_store.meta_from_head(ddb_run_store.read_head("m"))


@pytest.mark.parametrize("read", ["read_state_common", "read_head"])
def test_the_gate_reads_raise_a_failed_get_item_as_it_is(ddb_run_store, monkeypatch, read):
    """闸的两种读，读取本身的错误原样抛出（ADR 0054 决策九「落实时」第一、二步），不吞成「不存在」：吞掉的话，一次限流在第一步会被当成
    运行态不存在而清扫一个仍在执行的 run，在第二步会被当成头不在而以 error 变体结束一个正常的 run。"""
    from botocore.exceptions import ClientError

    meta, state = _pending_run("t")
    ddb_run_store.create_run(meta, state)
    throttled = ClientError({"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "slow down"}}, "GetItem")

    def get_item(**kw):
        raise throttled

    monkeypatch.setattr(ddb_run_store._table, "get_item", get_item)
    with pytest.raises(ClientError) as exc:
        getattr(ddb_run_store, read)("t")
    assert exc.value is throttled


# ---- 读整份运行定义（ADR 0030 决定六「云端提交记录」条的「读整份定义」「jobs 对象取不到时」两项）----
def _head(aws, run_id: str) -> dict:
    return aws["ddb"].Table(aws["table_name"]).get_item(Key={"run_id": run_id, "item_type": "META"},
                                                        ConsistentRead=True)["Item"]


def _recording_get_object(aws, monkeypatch) -> list[dict]:
    """包住共享 s3 client 的 get_object，记下每次调用的参数。"""
    calls: list[dict] = []
    real = aws["s3"].get_object

    def get_object(**kwargs):
        calls.append(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(aws["s3"], "get_object", get_object)
    return calls


def test_load_run_meta_checks_the_schema_before_fetching_the_jobs_object(aws, ddb_run_store, monkeypatch):
    """结构版本不是本读端认的：抛 UnsupportedDefinitionSchema，不取 jobs 对象。同一条记录换回本版本的号即照常取（一次 GetObject），
    说明前面没有取是因为版本、不是因为替身没接上。"""
    from gherkai_core.errors import UnsupportedDefinitionSchema

    meta, state = _deep_meta("future")
    ddb_run_store.create_run(meta, state)
    head = _head(aws, "future")
    later = json.loads(head["meta_json"]) | {"schema_version": 3}
    ddb_run_store._table.put_item(Item={**head, "schema_version": 3, "meta_json": json.dumps(later)})
    fetched = _recording_get_object(aws, monkeypatch)

    with pytest.raises(UnsupportedDefinitionSchema):
        ddb_run_store.load_run_meta("future")
    assert fetched == []
    ddb_run_store._table.put_item(Item=head)
    assert ddb_run_store.load_run_meta("future") == meta
    assert [c["Key"] for c in fetched] == _jobs_object_keys(aws, "future")


@pytest.mark.parametrize("corrupt", ["no_ref", "ref_not_s3", "ref_without_key", "ref_not_text", "jobs_in_head",
                                     "body_not_json", "body_not_array", "headers_a_list", "task_defs_a_string",
                                     "task_defs_a_list", "scenarios_null"])
def test_load_run_meta_reports_malformed_records_as_contract_errors(aws, ddb_run_store, corrupt):
    """头缺 jobs_ref、地址不是 s3://<桶>/<键>、meta_json 里另有 jobs、jobs 对象的内容不是 JSON 数组，以及拼回运行定义时字段的形态不对
    （额外请求头是数组、worker 修订表是字符串或数组、job 的 scenarios 为 null）：都是定义违约，不漏成 KeyError、TypeError、ValueError
    或 AttributeError。漏出去的话，云端推进器把它当成读取失败、对这条记录一再重试，这个 run 永远结束不了。"""
    from decimal import Decimal

    from gherkai_core.errors import DefinitionContractError

    meta, state = _deep_meta("bad")
    ddb_run_store.create_run(meta, state)
    head = _head(aws, "bad")
    [key] = _jobs_object_keys(aws, "bad")
    table = ddb_run_store._table
    in_meta_json = {"headers_a_list": ("extra_http_headers", ["x"]), "task_defs_a_string": ("worker_task_defs", "abc"),
                    "task_defs_a_list": ("worker_task_defs", [1])}
    if corrupt in in_meta_json:
        name, value = in_meta_json[corrupt]
        table.put_item(Item={**head, "meta_json": json.dumps(json.loads(head["meta_json"]) | {name: value})})
    elif corrupt == "scenarios_null":
        jobs = json.loads(aws["s3"].get_object(Bucket=aws["bucket"], Key=key)["Body"].read())
        jobs[0]["scenarios"] = None
        aws["s3"].put_object(Bucket=aws["bucket"], Key=key, Body=json.dumps(jobs).encode())
    elif corrupt == "no_ref":
        table.put_item(Item={k: v for k, v in head.items() if k != "jobs_ref"})
    elif corrupt == "ref_not_s3":
        table.put_item(Item={**head, "jobs_ref": f"https://{aws['bucket']}/{key}"})
    elif corrupt == "ref_without_key":
        table.put_item(Item={**head, "jobs_ref": f"s3://{aws['bucket']}"})
    elif corrupt == "ref_not_text":
        table.put_item(Item={**head, "jobs_ref": Decimal(1)})
    elif corrupt == "jobs_in_head":
        table.put_item(Item={**head, "meta_json": json.dumps(json.loads(head["meta_json"]) | {"jobs": []})})
    else:
        body = b"{not json" if corrupt == "body_not_json" else b'{"jobs": []}'
        aws["s3"].put_object(Bucket=aws["bucket"], Key=key, Body=body)
    with pytest.raises(DefinitionContractError):
        ddb_run_store.load_run_meta("bad")


def _client_error(code: str, status: int):
    from botocore.exceptions import ClientError

    return ClientError({"Error": {"Code": code, "Message": code}, "ResponseMetadata": {"HTTPStatusCode": status}}, "GetObject")


@pytest.mark.parametrize("case", ["missing", "access_denied", "no_such_bucket", "no_response", "body_read"])
def test_load_run_meta_marks_jobs_object_read_failures_with_their_kind(aws, ddb_run_store, monkeypatch, case):
    """取 jobs 对象的那一次读失败：抛 JobsObjectUnreadable，类别区分键不存在、拒绝访问与别的错误（错误码另带，没有收到响应时为
    None），原异常在 __cause__；它不落在「内容不合法」的口径里，调用方不会把它当成定义违约。缺键在替身上真实删去对象，拒绝访问与
    没有响应由替换后的 get_object 抛出（替身在没有列举权限时取缺键的行为不等价，真实的表上另核）。"""
    from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError, ReadTimeoutError

    from gherkai_core.adapters.run_store.jobs_object import JobsObjectFailure, JobsObjectUnreadable
    from gherkai_core.serialize import UNREADABLE_RECORD_ERRORS

    meta, state = _deep_meta("gone")
    ddb_run_store.create_run(meta, state)
    [key] = _jobs_object_keys(aws, "gone")
    ref = _head(aws, "gone")["jobs_ref"]
    real_get = aws["s3"].get_object
    if case == "missing":
        aws["s3"].delete_object(Bucket=aws["bucket"], Key=key)
        want = (JobsObjectFailure.MISSING, "NoSuchKey", ClientError)
    elif case == "access_denied":
        monkeypatch.setattr(aws["s3"], "get_object", lambda **kw: (_ for _ in ()).throw(_client_error("AccessDenied", 403)))
        want = (JobsObjectFailure.ACCESS_DENIED, "AccessDenied", ClientError)
    elif case == "no_such_bucket":
        ref = "s3://no-such-bucket-gherkai-x/" + key
        ddb_run_store._table.put_item(Item={**_head(aws, "gone"), "jobs_ref": ref})
        want = (JobsObjectFailure.OTHER, "NoSuchBucket", ClientError)
    elif case == "no_response":
        monkeypatch.setattr(aws["s3"], "get_object",
                            lambda **kw: (_ for _ in ()).throw(EndpointConnectionError(endpoint_url="https://s3")))
        want = (JobsObjectFailure.OTHER, None, BotoCoreError)
    else:
        class _Body:
            def read(self):
                raise ReadTimeoutError(endpoint_url="https://s3")

        monkeypatch.setattr(aws["s3"], "get_object", lambda **kw: {**real_get(**kw), "Body": _Body()})
        want = (JobsObjectFailure.OTHER, None, BotoCoreError)

    with pytest.raises(JobsObjectUnreadable) as ei:
        ddb_run_store.load_run_meta("gone")
    failure, code, cause_type = want
    assert (ei.value.failure, ei.value.error_code, ei.value.run_id, ei.value.ref) == (failure, code, "gone", ref)
    assert isinstance(ei.value.__cause__, cause_type)
    assert not isinstance(ei.value, UNREADABLE_RECORD_ERRORS)
    assert "gone" in str(ei.value) and ref in str(ei.value)


def test_load_run_meta_lets_non_s3_errors_through_unwrapped(aws, ddb_run_store, monkeypatch):
    """S3 之外的异常（注入的句柄不对一类的装配错误）不包成 JobsObjectUnreadable：那不是这次读的结果。"""
    from gherkai_core.adapters.run_store.jobs_object import JobsObjectUnreadable

    meta, state = _deep_meta("wired")
    ddb_run_store.create_run(meta, state)
    monkeypatch.setattr(aws["s3"], "get_object", lambda **kw: (_ for _ in ()).throw(AttributeError("not an s3 client")))
    with pytest.raises(AttributeError) as ei:
        ddb_run_store.load_run_meta("wired")
    assert not isinstance(ei.value, JobsObjectUnreadable)


def test_tunnel_headers_and_warmup_url_stay_in_the_head(aws, ddb_run_store):
    """会话预热地址（带隧道令牌）与额外请求头留在头的 meta_json 里，jobs 对象里没有它们（ADR 0030 决定六「令牌与额外请求头留在头里」）。"""
    import dataclasses

    meta, state = _deep_meta("tun")
    meta = dataclasses.replace(meta, extra_http_headers=(("x-gherkai-tunnel", "secret-header-value"),),
                               session_warmup_url="https://edge.example/warmup?token=secret-token-value")
    ddb_run_store.create_run(meta, state)
    [key] = _jobs_object_keys(aws, "tun")
    body = aws["s3"].get_object(Bucket=aws["bucket"], Key=key)["Body"].read().decode("utf-8")
    assert "secret-header-value" not in body and "secret-token-value" not in body
    head_json = _head(aws, "tun")["meta_json"]
    assert "secret-header-value" in head_json and "secret-token-value" in head_json
    assert ddb_run_store.load_run_meta("tun") == meta


def test_header_only_reads_never_fetch_the_jobs_object(aws, jobs_objects, monkeypatch):
    """只读头的各处不取 jobs 对象（ADR 0030 决定六「读整份定义」一项），注入了 jobs 对象存取的 store 也一样：读头、读运行态、判断
    是否 detached 与列举都不发 GetObject。最后读一次整份定义（一次 GetObject），说明记录调用的替身接上了。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from tests.conftest import STATUS_GROUP_INDEX

    store = DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]), jobs_objects=jobs_objects,
                             list_index_name=STATUS_GROUP_INDEX)
    meta, state = _deep_meta("hdr-only")
    store.create_run(meta, state)
    fetched = _recording_get_object(aws, monkeypatch)

    assert store.peek_definition_header("hdr-only") == (2, None)
    assert store.load_run_state("hdr-only").status == Status.PENDING
    assert store.is_detached("hdr-only") is False
    [row] = store.list_runs([Status.PENDING], limit=None)
    assert row.run_id == "hdr-only"
    assert fetched == []
    assert store.load_run_meta("hdr-only") == meta
    assert [c["Key"] for c in fetched] == _jobs_object_keys(aws, "hdr-only")


# ---- 没有注入 jobs 对象的存取（ADR 0030 决定六「云端提交记录」条的「装配」一项）----
def test_store_without_jobs_objects_refuses_create_and_full_read_for_every_run(aws, ddb_run_store, monkeypatch):
    """没有注入 jobs 对象存取的 DynamoDBRunStore：建 run 与读整份运行定义一律报装配缺失，不带多行参数的 run 同样报，没有 job 的运行
    定义也先报装配缺失；报之前不发任何读写。只读头的读照常。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import RunMeta, RunState

    plain = _sample_run("plain")  # step 没有参数
    ddb_run_store.create_run(plain.run_meta, _initial_state("plain", [j.scope_id for j in plain.run_meta.jobs]))
    table = aws["ddb"].Table(aws["table_name"])
    bare = DynamoDBRunStore(table)
    calls: list[str] = []
    for name in ("get_item", "put_item", "update_item"):
        monkeypatch.setattr(table, name, lambda _n=name, **kw: calls.append(_n))
    for name in ("get_object", "put_object"):
        monkeypatch.setattr(aws["s3"], name, lambda _n=name, **kw: calls.append(_n))

    other = _sample_run("other").run_meta
    empty = RunMeta(run_id="empty", created_at="t", jobs=(), deadline_at="2026-01-01T01:00:00+00:00")
    for create in (lambda: bare.create_run(other, _initial_state("other", [j.scope_id for j in other.jobs])),
                   lambda: bare.create_run(empty, RunState(run_id="empty", status=Status.PENDING, jobs={}))):
        with pytest.raises(RuntimeError, match="jobs_objects"):
            create()
    for run_id in ("plain", "nope"):
        with pytest.raises(RuntimeError, match="jobs_objects"):
            bare.load_run_meta(run_id)
    assert calls == []

    monkeypatch.undo()
    assert bare.peek_definition_header("plain") == (2, None)
    assert bare.load_run_state("plain").status == Status.PENDING
    assert bare.is_detached("plain") is False
    assert table.get_item(Key={"run_id": "other", "item_type": "META"}).get("Item") is None
    assert _jobs_object_keys(aws, "other") == [] and _jobs_object_keys(aws, "empty") == []


# ---- 建 run 是条件写（ADR 0030 决定六「建 run 是条件写」条与「建 run 的次序与失败时留下的」一项，ADR 0054 决策五）----
def _doc_meta(run_id: str, content: str, *, extra_scope: bool = False):
    """带 docString 的 definition。同一 run_id 下换 content 再建，jobs 对象若被重写，正文就会变；extra_scope 再多一个 scope，运行态
    若被重写会多出一个条目。"""
    from gherkai_core.model import Job, RunMeta, RunState, Scenario, Step, StepArgument

    def job(scope_id):
        return Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", timeout_s=300.0, scenarios=(
            Scenario(id=f"{scope_id}:1", name="sc", steps=(
                Step(0, "Then", "看结果", StepArgument(kind="docString", content=content)),)),))
    jobs = (job("s"), job("t")) if extra_scope else (job("s"),)
    meta = RunMeta(run_id=run_id, created_at="t", jobs=jobs, deadline_at="2026-01-01T01:00:00+00:00")
    state = RunState(run_id=run_id, status=Status.PENDING, started_at="t",
                     jobs={j.scope_id: JobState(j.scope_id, Status.PENDING) for j in jobs})
    return meta, state


def _snapshot(aws, run_id: str) -> tuple[dict | None, dict | None, dict[str, bytes]]:
    """库中原样：META item、STATE item 与桶里全部对象（key → 正文）。"""
    table = aws["ddb"].Table(aws["table_name"])
    items = tuple(table.get_item(Key={"run_id": run_id, "item_type": t}, ConsistentRead=True).get("Item")
                  for t in ("META", "STATE"))
    s3 = aws["s3"]
    objects = {o["Key"]: s3.get_object(Bucket=aws["bucket"], Key=o["Key"])["Body"].read()
               for o in s3.list_objects_v2(Bucket=aws["bucket"]).get("Contents", [])}
    return items[0], items[1], objects


def _first_content(body: bytes) -> str:
    return json.loads(body)[0]["scenarios"][0]["steps"][0]["argument"]["content"]


def test_create_run_writes_the_jobs_object_then_head_then_state_without_reading_first(aws, ddb_run_store, monkeypatch):
    """次序：带「键不存在才写」条件的 jobs 对象写在前，两次带「条目不存在」条件的 put 在后（头先于运行态）；建 run 之前不读表。jobs
    对象不带 tag。"""
    order: list[str] = []
    table = ddb_run_store._table
    real_get, real_put, real_s3_put = table.get_item, table.put_item, aws["s3"].put_object

    def get_item(**kwargs):
        order.append("get")
        return real_get(**kwargs)

    def put_item(**kwargs):
        order.append(f"put {kwargs['Item']['item_type']} if {kwargs.get('ConditionExpression')}")
        return real_put(**kwargs)

    def put_object(**kwargs):
        order.append(f"s3 put if-none-match={kwargs.get('IfNoneMatch')} tagged={'Tagging' in kwargs}")
        return real_s3_put(**kwargs)

    monkeypatch.setattr(table, "get_item", get_item)
    monkeypatch.setattr(table, "put_item", put_item)
    monkeypatch.setattr(aws["s3"], "put_object", put_object)
    ddb_run_store.create_run(*_doc_meta("ord", "正文"))
    assert order == ["s3 put if-none-match=* tagged=False",
                     "put META if attribute_not_exists(run_id)",
                     "put STATE if attribute_not_exists(run_id)"]
    [key] = _jobs_object_keys(aws, "ord")
    assert aws["s3"].get_object_tagging(Bucket=aws["bucket"], Key=key)["TagSet"] == []


def test_create_run_twice_writes_jobs_objects_under_different_keys(aws, ddb_run_store):
    """同一个 run 标识的两次建 run 各写一个新键：键形态是 definitions/<run_id>/<32 个十六进制字符>.json，两次的键不同。"""
    import re

    ddb_run_store.create_run(*_doc_meta("twice", "第一版正文"))
    with pytest.raises(RunAlreadyExists):
        ddb_run_store.create_run(*_doc_meta("twice", "第二版正文"))
    keys = _jobs_object_keys(aws, "twice")
    assert len(keys) == 2 and all(re.fullmatch(r"definitions/twice/[0-9a-f]{32}\.json", k) for k in keys)


def test_create_run_on_existing_run_leaves_records_and_adds_only_an_unreferenced_jobs_object(aws, ddb_run_store):
    """对已有的 run 再建（jobs 对象的键不同）：抛 RunAlreadyExists，头、运行态与先前的 jobs 对象都不变，只多出一个没有记录指向的
    jobs 对象（正文是这次的）。读回的仍是先建的那份运行定义。"""
    meta, state = _doc_meta("dup", "第一版正文")
    ddb_run_store.create_run(meta, state)
    assert ddb_run_store.try_claim_job("dup", "s") is True
    before = _snapshot(aws, "dup")

    with pytest.raises(RunAlreadyExists):
        ddb_run_store.create_run(*_doc_meta("dup", "第二版正文", extra_scope=True))
    after = _snapshot(aws, "dup")
    assert after[:2] == before[:2]
    assert {k: after[2][k] for k in before[2]} == before[2]
    [orphan] = set(after[2]) - set(before[2])
    assert after[0]["jobs_ref"] != f"s3://{aws['bucket']}/{orphan}" and _first_content(after[2][orphan]) == "第二版正文"
    assert ddb_run_store.load_run_meta("dup") == meta


def test_create_run_with_the_same_jobs_object_key_is_stopped_by_the_conditional_put(aws, ddb_run_store, monkeypatch):
    """让第二次建 run 取到与第一次相同的 jobs 对象键（替换随机段的来源）：jobs 对象的写得到 412，抛 RunAlreadyExists，不再写头与
    运行态；先前的 jobs 对象、头与运行态都不变，也不多出对象。"""
    from botocore.exceptions import ClientError

    from gherkai_core.adapters.run_store import jobs_object

    monkeypatch.setattr(jobs_object, "_new_segment", lambda: "0" * 32)
    meta, state = _doc_meta("same", "第一版正文")
    ddb_run_store.create_run(meta, state)
    assert ddb_run_store.try_claim_job("same", "s") is True
    before = _snapshot(aws, "same")
    puts: list[str] = []
    real_put = ddb_run_store._table.put_item
    monkeypatch.setattr(ddb_run_store._table, "put_item", lambda **kw: puts.append(kw["Item"]["item_type"]) or real_put(**kw))

    with pytest.raises(RunAlreadyExists) as ei:
        ddb_run_store.create_run(*_doc_meta("same", "第二版正文", extra_scope=True))
    assert isinstance(ei.value.__cause__, ClientError)
    assert ei.value.__cause__.response["Error"]["Code"] == "PreconditionFailed"
    assert puts == []
    assert _snapshot(aws, "same") == before


def test_create_run_head_put_is_conditional_when_another_writer_lands_after_the_jobs_object(aws, ddb_run_store, monkeypatch):
    """本方写成 jobs 对象之后、写头之前，另一方完整地建了同一个 run 标识（键不同）：头的条件写挡下本方，抛 RunAlreadyExists；头与
    运行态是另一方的，头指向另一方的 jobs 对象，本方的 jobs 对象留在桶里、没有记录指向。另一方用自己的 s3 client，先后靠包住本方
    client 的 put_object 固定。"""
    import boto3

    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.adapters.run_store.jobs_object import S3JobsObjects
    from tests.conftest import DEFINITIONS_PREFIX

    other = DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]),
                             jobs_objects=S3JobsObjects(boto3.client("s3", region_name="us-east-1"), aws["bucket"],
                                                        DEFINITIONS_PREFIX))
    other_meta, other_state = _doc_meta("race", "另一方的正文", extra_scope=True)
    real_put = aws["s3"].put_object
    log: list[str] = []

    def put_object(**kwargs):
        resp = real_put(**kwargs)
        log.append(kwargs["Key"])
        other.create_run(other_meta, other_state)  # 插在本方的 jobs 对象与头之间
        return resp

    monkeypatch.setattr(aws["s3"], "put_object", put_object)
    with pytest.raises(RunAlreadyExists):
        ddb_run_store.create_run(*_doc_meta("race", "本方的正文"))
    monkeypatch.undo()

    [mine] = log
    head, state, objects = _snapshot(aws, "race")
    assert head["jobs_ref"] != f"s3://{aws['bucket']}/{mine}"
    assert set(state["jobs"]) == {"s", "t"}
    assert sorted(objects) == _jobs_object_keys(aws, "race") and len(objects) == 2
    assert _first_content(objects[mine]) == "本方的正文"
    assert ddb_run_store.load_run_meta("race") == other_meta


def test_create_run_stopped_at_the_head_when_only_the_head_exists(aws, ddb_run_store):
    """只有头在（运行态被绕过端口删去）：再建在头的条件写被挡下，抛 RunAlreadyExists；头不变、运行态仍不在，只多出一个没有记录指向
    的 jobs 对象。"""
    ddb_run_store.create_run(*_doc_meta("half", "正文"))
    ddb_run_store._table.delete_item(Key={"run_id": "half", "item_type": "STATE"})
    before = _snapshot(aws, "half")

    with pytest.raises(RunAlreadyExists):
        ddb_run_store.create_run(*_doc_meta("half", "另一份正文"))
    head, state, objects = _snapshot(aws, "half")
    assert (head, state) == (before[0], None)
    assert len(objects) == len(before[2]) + 1


def test_create_run_state_put_is_conditional_on_its_own(aws, ddb_run_store, monkeypatch):
    """STATE 那一次写自己带「条目不存在」的条件：头不在（被绕过端口删去）而运行态在时，再建写成新的 jobs 对象与头，到运行态被已有的
    STATE 挡下，抛 RunAlreadyExists，STATE 仍是原来的内容（含已有的认领）。建 run 之前不读，所以走得到这一次写。写成的头与 jobs 对象
    留在原处、不补偿：头指向这次新写的 jobs 对象，桶里只多出这一个对象。"""
    ddb_run_store.create_run(*_doc_meta("race2", "先到的正文"))
    assert ddb_run_store.try_claim_job("race2", "s") is True
    table = aws["ddb"].Table(aws["table_name"])
    table.delete_item(Key={"run_id": "race2", "item_type": "META"})
    state_before = table.get_item(Key={"run_id": "race2", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    _, _, objects_before = _snapshot(aws, "race2")

    puts: list[str] = []
    real_put = ddb_run_store._table.put_item
    with monkeypatch.context() as mp:
        mp.setattr(ddb_run_store._table, "put_item", lambda **kw: puts.append(kw["Item"]["item_type"]) or real_put(**kw))
        with pytest.raises(RunAlreadyExists):
            ddb_run_store.create_run(*_doc_meta("race2", "后到的正文", extra_scope=True))
    assert puts == ["META", "STATE"]
    head, state, objects = _snapshot(aws, "race2")
    assert state == state_before
    assert {k: objects[k] for k in objects_before} == objects_before
    [new_key] = set(objects) - set(objects_before)
    assert head is not None and head["jobs_ref"] == f"s3://{aws['bucket']}/{new_key}"
    assert _first_content(objects[new_key]) == "后到的正文"


@pytest.mark.parametrize("step", ["jobs_object", "META", "STATE"])
def test_create_run_failure_at_a_step_propagates_and_leaves_earlier_writes(aws, ddb_run_store, monkeypatch, step):
    """某一步以条件之外的错误失败（拒绝访问、限流一类）：原样抛出那个错误、不报成 run 已存在；前面各步写下的原样留下、不补偿
    （ADR 0030 决定六「建 run 的次序与失败时留下的」）。jobs 对象那一步失败，什么都没写下；头那一步失败，只留下一个没有记录指向的
    jobs 对象；运行态那一步失败，头与它指向的 jobs 对象都在，没有运行态。"""
    from botocore.exceptions import ClientError

    if step == "jobs_object":
        boom = ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}}, "PutObject")
    else:
        boom = ClientError({"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "slow down"}}, "PutItem")
    real_s3_put, real_put = aws["s3"].put_object, ddb_run_store._table.put_item

    def put_object(**kw):
        if step == "jobs_object":
            raise boom
        return real_s3_put(**kw)

    def put_item(**kw):
        if kw["Item"]["item_type"] == step:
            raise boom
        return real_put(**kw)

    with monkeypatch.context() as mp:
        mp.setattr(aws["s3"], "put_object", put_object)
        mp.setattr(ddb_run_store._table, "put_item", put_item)
        with pytest.raises(ClientError) as ei:
            ddb_run_store.create_run(*_doc_meta("fail", "正文"))
    assert ei.value is boom

    head, state, _ = _snapshot(aws, "fail")
    keys = _jobs_object_keys(aws, "fail")
    assert state is None
    if step == "jobs_object":
        assert (head, keys) == (None, [])
    elif step == "META":
        assert head is None and len(keys) == 1
    else:
        assert len(keys) == 1 and head is not None and head["jobs_ref"] == f"s3://{aws['bucket']}/{keys[0]}"


def test_create_run_writes_claim_count_zero_on_the_state_item(aws, ddb_run_store):
    """STATE item 写下认领计数 0（写端恒写，数值属性）。"""
    meta, state = _doc_meta("cc", "正文")
    ddb_run_store.create_run(meta, state)
    item = aws["ddb"].Table(aws["table_name"]).get_item(Key={"run_id": "cc", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item["claim_count"] == 0


# ---- 点名的标识（ADR 0030 决定三「点名」条）：jobs Map 条目里的键，与重读再算时的沿用 ----
def test_job_entries_carry_result_id_only_when_named(aws, ddb_run_store):
    """STATE 的 jobs Map 里，被点名的 job 的条目带 `result_id`，没被点名的（未结束、由结束写结束）省键；读回与写下的标识相同。读原始
    STATE，不经 load_run_state。"""
    meta = _sample_run("rid-run").run_meta
    sid0, sid1 = (j.scope_id for j in meta.jobs)
    ddb_run_store.create_run(meta, _initial_state("rid-run", [sid0, sid1]))
    assert ddb_run_store.try_claim_job("rid-run", sid0, claimed_at="2026-07-01T00:01:00Z") is True
    assert ddb_run_store.commit_job_states("rid-run", [JobState(sid0, Status.PASSED, result_id="0123456789abcdef")],
                                           ended_at="never") is CommitOutcome.OPEN
    assert ddb_run_store.end_run("rid-run", RUN_ENDINGS["deadline"], ended_at="2026-07-01T00:05:00Z") is True

    raw = aws["ddb"].Table(aws["table_name"]).get_item(Key={"run_id": "rid-run", "item_type": "STATE"})["Item"]["jobs"]
    assert raw[sid0]["result_id"] == "0123456789abcdef"
    assert "result_id" not in raw[sid1]
    got = ddb_run_store.load_run_state("rid-run")
    assert (got.jobs[sid0].result_id, got.jobs[sid1].result_id) == ("0123456789abcdef", None)


def test_commit_rejected_by_the_write_seq_names_the_same_id_after_rereading(aws, jobs_objects, monkeypatch):
    """终态写读到 STATE 之后、发出写之前，另一个写入方认领了 b：整体替换被写入序号的条件挡下，重读再算之后写成，a 点名的仍是调用方给出
    的那个标识（重读再算用的是同一组 JobState，不另生成标识），b 的认领也留下。先后靠包住被测表对象的 update_item 固定。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    table = aws["ddb"].Table(aws["table_name"])
    store, other = DynamoDBRunStore(table, jobs_objects=jobs_objects), DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))
    meta = _sample_run("seq-run").run_meta
    sid_a, sid_b = (j.scope_id for j in meta.jobs)
    store.create_run(meta, _initial_state("seq-run", [sid_a, sid_b]))
    assert store.try_claim_job("seq-run", sid_a, claimed_at="2026-07-01T00:01:00Z") is True

    ccf = table.meta.client.exceptions.ConditionalCheckFailedException
    real_update = table.update_item
    log: list[str] = []

    def update_item(**kwargs):
        if not log:
            assert other.try_claim_job("seq-run", sid_b, claimed_at="2026-07-01T00:02:00Z") is True  # 插在读与写之间
            log.append("other")
        try:
            resp = real_update(**kwargs)
        except ccf:
            log.append("write-rejected")
            raise
        log.append("write-ok")
        return resp

    monkeypatch.setattr(table, "update_item", update_item)
    given = JobState(sid_a, Status.PASSED, session_id="sess-a", result_id="00000000000000a1")
    assert store.commit_job_states("seq-run", [given], ended_at="never") is CommitOutcome.OPEN

    assert log == ["other", "write-rejected", "write-ok"]
    got = store.load_run_state("seq-run")
    assert got.jobs[sid_a] == JobState(sid_a, Status.PASSED, session_id="sess-a", claimed_at="2026-07-01T00:01:00Z",
                                       result_id="00000000000000a1")
    assert got.jobs[sid_b] == JobState(sid_b, Status.RUNNING, claimed_at="2026-07-01T00:02:00Z")
