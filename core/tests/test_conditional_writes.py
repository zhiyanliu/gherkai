"""RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state / try_finalize。

**local（fcntl 文件锁）与 ddb（moto，条件表达式）跑同一批断言**（parametrize）——保两 adapter 语义一致。
moto 的条件写行为与真 DDB 可能有别（绿≠对边界）→ 真 DDB 复验单列（test 末 real_aws，需真凭证才跑）。

覆盖三机制的正确性核心：
- 机制四 CAS：pending→running 只成功一次，并发抢占只一个赢。
- 机制三 HWM：stale（更小 hwm）投影写被挡、不覆盖已推进态。
- 机制三 finalize 单调：已终态不被重复 finalize / 不被刷回。
"""
from __future__ import annotations

import pytest

from gherkai_core.model import JobState, RunMeta, RunState, Status


def _meta(run_id: str = "run-1", *scope_ids: str) -> RunMeta:
    from gherkai_core.model import Job, Scenario, Step
    ids = scope_ids or ("a", "b")
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="novaact",
            scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
        for s in ids
    )
    return RunMeta(run_id=run_id, created_at="2026-07-19T00:00:00Z", jobs=jobs)


def _initial(meta: RunMeta, hwm: int | None = None) -> RunState:
    return RunState(
        run_id=meta.run_id, status=Status.PENDING,
        jobs={j.scope_id: JobState(scope_id=j.scope_id, status=Status.PENDING) for j in meta.jobs},
        started_at="2026-07-19T00:00:00Z", high_water_mark=hwm,
    )


@pytest.fixture(params=["local", "ddb"])
def run_store(request, tmp_path, aws):
    """两个 adapter 各来一遍（对拍）。local 用 tmp_path；ddb 用 moto aws fixture。"""
    if request.param == "local":
        from gherkai_core.adapters.run_store.local import LocalRunStore
        return LocalRunStore(tmp_path)
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))


# ---------- 机制四：CAS try_claim_job ----------

def test_claim_pending_succeeds_once(run_store):
    """pending 的 job 首次 claim 成功、置 running；再 claim 同一个 → False（已非 pending）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a") is True
    state = run_store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.RUNNING
    # 第二次抢同一个 → 失败（严格并发闸：不会重复 RunTask）
    assert run_store.try_claim_job("run-1", "a") is False


def test_claim_nonexistent_job_fails(run_store):
    """claim 不在 definition 里的 scope → False（不臆造 job）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "ghost") is False


def test_claim_two_different_jobs_both_succeed(run_store):
    """抢两个不同 pending job 各自成功（互不干扰）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a") is True
    assert run_store.try_claim_job("run-1", "b") is True


def test_claim_writes_claimed_at(run_store):
    """claim 随写 claimed_at（timeout 起算点，ADR 0034「job timeout」节）；未 claim 的 job 无值。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    state = run_store.load_run_state("run-1")
    assert state.jobs["a"].claimed_at == "2026-08-13T01:02:03Z"
    assert state.jobs["b"].claimed_at is None


def test_projection_preserves_claimed_at(run_store):
    """投影的整 job 覆盖不抹 claimed_at：claimed_at 只由 claim 落库、事件推演不出——真实 tick 流里
    project() 经 baseline 带回（ADR 0034「job timeout」节），两 adapter 对拍。"""
    from gherkai_core.model import ScopeStarted
    from gherkai_core.project import EventRecord, project

    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    assert run_store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    baseline = run_store.load_run_state("run-1")
    recs = [EventRecord(scope_id="a", kind="event", seq=1,
                        event=ScopeStarted(scope_id="a", session_id="sess-1"), emit_ts=0.0)]
    projected = project(meta, recs, baseline)
    assert projected.jobs["a"].claimed_at == "2026-08-13T01:02:03Z"  # 投影经 baseline 带回
    assert run_store.project_state("run-1", projected) is True
    got = run_store.load_run_state("run-1")
    assert got.jobs["a"].claimed_at == "2026-08-13T01:02:03Z"  # 落库后仍在（整 job 覆盖没抹）
    assert got.jobs["a"].session_id == "sess-1"  # 血缘同机制带回


# ---------- 机制三：HWM project_state ----------

def test_project_advances_hwm(run_store):
    """hwm 递增的投影写成功。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    s = _initial(meta, hwm=5)
    s = RunState(run_id="run-1", status=Status.RUNNING, jobs=s.jobs, high_water_mark=5)
    assert run_store.project_state("run-1", s) is True
    assert run_store.load_run_state("run-1").high_water_mark == 5


def test_stale_projection_rejected(run_store):
    """关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    fresh = RunState(run_id="run-1", status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.PASSED)},
                     high_water_mark=10)
    assert run_store.project_state("run-1", fresh) is True
    stale = RunState(run_id="run-1", status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.PENDING)},
                     high_water_mark=5)
    assert run_store.project_state("run-1", stale) is False  # 被 HWM 挡
    # 库里仍是 fresh（hwm=10），未被 stale 覆盖
    got = run_store.load_run_state("run-1")
    assert got.high_water_mark == 10
    assert got.jobs["a"].status == Status.PASSED


def test_equal_hwm_projection_allowed(run_store):
    """同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    s = RunState(run_id="run-1", status=Status.RUNNING, jobs=_initial(meta).jobs, high_water_mark=7)
    assert run_store.project_state("run-1", s) is True
    assert run_store.project_state("run-1", s) is True  # 同 hwm 再写仍允许


def test_same_hwm_terminal_job_not_regressed(run_store):
    """关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。

    场景（对抗验证复现的永久错读模型）：实例 B 见 scope_done+task_exited 写 a=PASSED（hwm=3）；
    实例 A 对 a 视图旧（只见 scope_started）、对 b 视图新 → 同 hwm=3 投影 a=RUNNING——
    ① HWM 挡不住（3>=3），必须靠 job 级单调条件写挡。否则 a 被刷回 RUNNING 且若 run 已 finalize
    则永久错态（run=passed 而 jobs 恒 running）。
    """
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    fresh = RunState(run_id="run-1", status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.RUNNING)},
                     high_water_mark=3)
    assert run_store.project_state("run-1", fresh) is True
    stale = RunState(run_id="run-1", status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.RUNNING)},
                     high_water_mark=3)  # 同 HWM——① 不挡；靠 job 级 ② 挡
    run_store.project_state("run-1", stale)  # 整体返回值不限（local 合并写 True / 语义一致即可）
    got = run_store.load_run_state("run-1")
    assert got.jobs["a"].status == Status.PASSED  # 终态不回退（机制三② job 级）


def test_claimed_running_not_regressed_to_pending_same_hwm(run_store):
    """机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    assert run_store.try_claim_job("run-1", "a") is True  # a: pending→running
    stale = _initial(meta, hwm=0)  # 全 pending 视图、同 hwm=0
    run_store.project_state("run-1", stale)
    got = run_store.load_run_state("run-1")
    assert got.jobs["a"].status == Status.RUNNING  # claim 不被刷回


def test_projection_preserves_started_at(run_store):
    """投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    s = RunState(run_id="run-1", status=Status.RUNNING, jobs=_initial(meta).jobs,
                 high_water_mark=2)  # project() 产出的 RunState 不带 started_at
    assert run_store.project_state("run-1", s) is True
    got = run_store.load_run_state("run-1")
    assert got.started_at == "2026-07-19T00:00:00Z"  # create_run 落的起点仍在


def test_projection_keeps_pending_while_no_job_started(run_store):
    """喂**真 project() 产物**（非手搓 RunState）验 run 级 status 钳制的 pending 半边：project 的 run 级
    status 是终态聚合值——连「全 job 还 pending」的 run 它也吐 PASSED——投影写必须整个钳掉它；且此刻
    落库该是 **pending**（还没起过任何 job，status 如实反映「未启动」，ADR 0034 机制三）。
    """
    from gherkai_core.project import project

    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    projected = project(meta, [])  # 零事件、全 job pending
    assert projected.status == Status.PASSED, "前提：project 的 run 级 status 是终态聚合值（空 verdict 集→PASSED）"
    assert run_store.project_state("run-1", projected) is True
    got = run_store.load_run_state("run-1")
    assert got.status == Status.PENDING  # 钳掉聚合终态、且不虚报 running
    # 钳制到位的意义：commit point 仍可落（若投影落了 passed，这一步会被状态机单调条件写挡成 False）
    assert run_store.try_finalize("run-1", Status.PASSED, "2026-07-19T02:00:00Z") is True


def test_projection_lands_running_once_any_job_advanced(run_store):
    """钳制的 running 半边：任一 job 已推进（running / 终态）→ run 级落 running、不再 pending。"""
    from gherkai_core.model import ScopeStarted
    from gherkai_core.project import EventRecord, project

    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    recs = [EventRecord(scope_id="a", kind="event", seq=1,
                        event=ScopeStarted(scope_id="a", session_id="sess-1"), emit_ts=0.0)]
    projected = project(meta, recs)  # a=RUNNING、b=PENDING
    assert projected.jobs["a"].status == Status.RUNNING
    assert run_store.project_state("run-1", projected) is True
    assert run_store.load_run_state("run-1").status == Status.RUNNING


def test_projection_never_lands_terminal_run_status(run_store):
    """全 job 已终态（project 聚合出 PASSED）时投影仍只落 running——run 级终态是 try_finalize 的 commit
    point 专属（ADR 0030）：若投影提前落终态，紧接的 try_finalize 会被自己写的终态挡成 False。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    all_done = RunState(run_id="run-1", status=Status.PASSED,  # 手搓：模拟 project 的终态聚合值
                        jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.FAILED)},
                        high_water_mark=9)
    assert run_store.project_state("run-1", all_done) is True
    assert run_store.load_run_state("run-1").status == Status.RUNNING  # 不是 passed/failed
    assert run_store.try_finalize("run-1", Status.FAILED, "2026-07-19T02:00:00Z") is True


# ---------- 机制三：finalize 单调 ----------

def test_finalize_from_nonterminal_succeeds(run_store):
    """非终态（pending/running）→ finalize 成功写终态。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_finalize("run-1", Status.PASSED, "2026-07-19T01:00:00Z") is True
    state = run_store.load_run_state("run-1")
    assert state.status == Status.PASSED and state.ended_at == "2026-07-19T01:00:00Z"


def test_double_finalize_rejected(run_store):
    """关键（机制三）：已终态再 finalize → False（commit 恰一次、幂等），不刷回、不重复触发 report。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_finalize("run-1", Status.PASSED, "t1") is True
    # 第二个实例也见全终态、也想 finalize（如写 error）→ 被挡，库里仍是首次的 passed/t1
    assert run_store.try_finalize("run-1", Status.ERROR, "t2") is False
    state = run_store.load_run_state("run-1")
    assert state.status == Status.PASSED and state.ended_at == "t1"


def test_finalize_missing_run_fails(run_store):
    """未 create 的 run → finalize False（不崩、不臆造）。"""
    assert run_store.try_finalize("nope", Status.PASSED, "t") is False


def test_projection_without_baseline_keeps_stored_lineage(run_store):
    """**不带 baseline** 的投影（session_id 从事件来、claimed_at 事件推演不出 → None）落库后，库中的 claimed_at 仍在、
    session_id 已刷——两 adapter 对拍：local 靠「投影缺字段回填库中值」，DDB 靠逐属性 SET 不提及即保留
    （曾整 entry 覆盖，一次不带 baseline 的投影就把只由 claim 落库的 claimed_at 静默抹掉）。"""
    from gherkai_core.model import ScopeStarted
    from gherkai_core.project import EventRecord, project

    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    assert run_store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    recs = [EventRecord(scope_id="a", kind="event", seq=1,
                        event=ScopeStarted(scope_id="a", session_id="sess-1"), emit_ts=0.0)]
    projected = project(meta, recs)  # 无 baseline
    assert projected.jobs["a"].claimed_at is None  # 投影自己不知道 claimed_at
    assert run_store.project_state("run-1", projected) is True
    got = run_store.load_run_state("run-1")
    assert got.jobs["a"].claimed_at == "2026-08-13T01:02:03Z" and got.jobs["a"].session_id == "sess-1"
    assert got.jobs["a"].status == Status.RUNNING


def test_projection_with_unknown_scope_is_ignored_not_invented(run_store):
    """投影带一个 definition 外的 scope（不该发生：project 只吐 meta.jobs 的键）→ 两 adapter 都**不臆造** job、不抛：
    local 跳过、DDB 经 attribute_exists 走 CCF 跳过（曾整 entry SET 会补建，改逐属性后父路径不存在会 ValidationException
    穿出、整 tick 失败——收敛成同一语义并钉住）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    projected = RunState(run_id="run-1", status=Status.RUNNING,
                         jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.PENDING),
                               "ghost": JobState("ghost", Status.PASSED)},
                         started_at="2026-07-19T00:00:00Z", high_water_mark=1)
    assert run_store.project_state("run-1", projected) is True
    got = run_store.load_run_state("run-1")
    assert set(got.jobs) == {"a", "b"} and got.jobs["a"].status == Status.PASSED
