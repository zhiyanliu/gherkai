"""RunStore 写入口的对拍测试（ADR 0034 机制三/机制四、ADR 0054 决策五、ADR 0030 决定四）：create_run / update_job_state / try_claim_job /
project_state / try_finalize。

**local（fcntl 文件锁）与 ddb（moto，条件表达式）运行同一批断言**（parametrize）——保两 adapter 语义一致。
moto 的条件写行为与真 DDB 可能有别（绿≠对边界）→ 真 DDB 复验单列在文件末（integration 标记，需真凭证才运行；
地基实测见 ADR 0034）。

覆盖三机制的正确性核心：
- 机制四 CAS：pending→running 只成功一次，并发认领只一个成功。
- 机制三 HWM：stale（更小 hwm）投影写被挡、不覆盖已推进态。
- 机制三 finalize 单调：已终态不被重复 finalize / 不被刷回。
- 机制三②的写入开销：无效果的 pending 项 DDB 不发写，两侧落库结果仍等于投影前库中值（DDB 侧另断言写入次数）。
- run 级状态只进不退：认领与前台 `update_job_state` 写下 running 时 run 级为 running、已收尾的 run 上认领被挡且
  运行态不变、前台的执行中写在已收尾的 run 上写不成（ADR 0034 机制三「run 级状态只进不退」条③）、全 pending 的旧投影不把 run 级
  改回 pending（DDB 侧另断言 `update_job_state` 只发一次写）。
- 建 run 只在 run 不存在时成立：对已有的 run 再建抛 FileExistsError、不改任何东西（ADR 0054 决策五）。
- `update_job_state` 只写 running（写别的状态是参数错误）；返回 run 在这次写时是否仍未结束（ADR 0054 决策五，加 ADR 0034 机制三
  「run 级状态只进不退」条③）：run 级为 pending 或 running 时 True、已是终态时 False 且运行态不变；DDB 侧因 STATE 不存在被挡之后并发建出的新记录不收到这次写。job 已是终态或不在运行态里时不写、
  返回值照样只看 run，两侧对拍在 test_ending_and_commit_writes.py。
- 投影不改写库中已是终态的 job，同一等级的终态之间也不以投影为准。
- 认领计数：建 run 为 0，认领成功加一、失败与其它写入口不变，缺键读作 0（ADR 0034 机制三「run 级状态只进不退」条①）；收尾写可带期望的计数。
- 运行态记录顶层的附加键（不属于 RunState 模型的键或属性）经各个写入口原样保留（ADR 0030 决定四「local 的顶层附加键整体保留」）。
结束写 `end_run` 与带结果的 job 终态写 `commit_job_states` 的语义对拍在 test_ending_and_commit_writes.py。
本机写入口在文件锁内互斥的结论靠真实进程核对，见 test_local_run_store_lock.py。
"""
from __future__ import annotations

import itertools

import pytest

from gherkai_core.model import JobState, RunMeta, RunState, Status


def _meta(run_id: str = "run-1", *scope_ids: str) -> RunMeta:
    from gherkai_core.model import Job, Scenario, Step
    ids = scope_ids or ("a", "b")
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="novaact",
            scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),), timeout_s=300.0)
        for s in ids
    )
    return RunMeta(run_id=run_id, created_at="2026-07-19T00:00:00Z", jobs=jobs, deadline_at="2026-01-01T01:00:00+00:00")


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
    # 第二次认领同一个 → 失败（严格并发闸：不会重复 RunTask）
    assert run_store.try_claim_job("run-1", "a") is False


def test_claim_nonexistent_job_fails(run_store):
    """claim 不在 definition 里的 scope → False（不臆造 job），run 级不变（仍为 pending）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    before = run_store.load_run_state("run-1")
    assert run_store.try_claim_job("run-1", "ghost") is False
    assert run_store.load_run_state("run-1") == before


def test_claim_two_different_jobs_both_succeed(run_store):
    """认领两个不同 pending job 各自成功（互不干扰）；run 级已是 running 时再认领另一个 pending job 照样成功。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a") is True
    assert run_store.load_run_state("run-1").status == Status.RUNNING
    assert run_store.try_claim_job("run-1", "b") is True
    assert run_store.load_run_state("run-1").status == Status.RUNNING


# ---------- run 级状态只进不退（ADR 0034 机制三「run 级状态只进不退」条）----------

def test_claim_advances_run_status_in_the_same_write(run_store):
    """认领成功后 run 级即为 running（条①：认领与 run 级同一条条件写），HWM 不变，另一个 job 不受影响。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=4))
    assert run_store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    got = run_store.load_run_state("run-1")
    assert got.status == Status.RUNNING
    assert got.high_water_mark == 4
    assert got.jobs["b"] == JobState("b", Status.PENDING)


def test_claim_rejected_on_finalized_run_leaves_state_unchanged(run_store):
    """已收尾（error、job 仍 pending）的 run 上认领返回 False，整份运行态不变：run 级、ended_at、message、job 态与 claimed_at
    （run 已收尾后不再接受新认领；推进器在 definition 不可用时带着 pending 的 job 收尾为 error，不能被认领复活）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    assert run_store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    assert run_store.try_finalize("run-1", Status.ERROR, "2026-08-13T02:00:00Z", message="原因") is True
    before = run_store.load_run_state("run-1")
    assert (before.status, before.jobs["b"].status) == (Status.ERROR, Status.PENDING), "前提：带着 pending 的 job 收尾"
    assert run_store.try_claim_job("run-1", "b", claimed_at="2026-08-13T03:00:00Z") is False
    got = run_store.load_run_state("run-1")
    assert got == before
    assert (got.status, got.ended_at, got.message) == (Status.ERROR, "2026-08-13T02:00:00Z", "原因")
    assert got.jobs["a"] == JobState("a", Status.RUNNING, claimed_at="2026-08-13T01:02:03Z")
    assert got.jobs["b"] == JobState("b", Status.PENDING)


def test_finalize_with_pending_jobs_succeeds(run_store):
    """收尾不要求 job 全为终态：run 级 pending（零认领）与 running（已认领一个）两种起点上，带着 pending 的 job 都能收尾，
    job 态原样保留。"""
    meta = _meta("run-1")
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_finalize("run-1", Status.ERROR, "t1") is True
    got = run_store.load_run_state("run-1")
    assert got.status == Status.ERROR and {js.status for js in got.jobs.values()} == {Status.PENDING}

    meta2 = _meta("run-2")
    run_store.create_run(meta2, _initial(meta2))
    assert run_store.try_claim_job("run-2", "a") is True
    assert run_store.try_finalize("run-2", Status.ERROR, "t1") is True
    got = run_store.load_run_state("run-2")
    assert got.status == Status.ERROR
    assert (got.jobs["a"].status, got.jobs["b"].status) == (Status.RUNNING, Status.PENDING)


@pytest.mark.parametrize("hwm", [0, 3], ids=["same_hwm", "higher_hwm"])
def test_all_pending_projection_after_claim_keeps_run_running(run_store, hwm):
    """认领之后，拿着认领之前 baseline 的全 pending 投影（同 HWM 或更高 HWM，都过得了 HWM 守卫）不把 run 级改回 pending，
    HWM 按条件前进，已认领的 job 仍为 running（条②：全 pending 的投影不写 run 级）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    assert run_store.try_claim_job("run-1", "a") is True
    assert run_store.project_state("run-1", _initial(meta, hwm=hwm)) is True
    got = run_store.load_run_state("run-1")
    assert got.status == Status.RUNNING
    assert got.high_water_mark == hwm
    assert got.jobs["a"].status == Status.RUNNING


def test_job_write_of_running_advances_run_status(run_store):
    """前台的执行中写把 job 记为 running 时 run 级随之为 running（取法：有 job 离开 pending、未全部结束；ADR 0034 机制三「run 级
    状态只进不退」条③）；另一个 job 不受影响。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="sess-a")) is True
    got = run_store.load_run_state("run-1")
    assert got.status == Status.RUNNING
    assert got.jobs["a"] == JobState("a", Status.RUNNING, session_id="sess-a")
    assert got.jobs["b"] == JobState("b", Status.PENDING)


@pytest.mark.parametrize("job_status", [Status.PENDING, Status.PASSED, Status.FAILED, Status.ERROR, Status.SKIPPED,
                                        Status.ABORTED])
def test_job_write_of_a_state_other_than_running_is_rejected(run_store, job_status):
    """执行中的写只记 running：写 pending 或终态是参数错误，抛 ValueError、运行态不变（终态由终态写与结束写写下）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    before = run_store.load_run_state("run-1")
    with pytest.raises(ValueError):
        run_store.update_job_state("run-1", JobState("a", job_status, session_id="sess-a"))
    assert run_store.load_run_state("run-1") == before


def test_job_write_on_finalized_run_changes_nothing(run_store):
    """已收尾、留有未结束 job 的 run 上写 job：写不成，运行态整份不变（run 到终态之后不再接受任何写，ADR 0054 决策五；ADR 0034
    机制三「run 级状态只进不退」条③）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", message="原因") is True
    before = run_store.load_run_state("run-1")
    assert before.jobs["a"].status == Status.PENDING, "前提：run 已结束而 job 未结束"
    assert run_store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="sess-a")) is False
    assert run_store.load_run_state("run-1") == before


def test_job_write_before_create_raises(run_store):
    """运行态不存在时 update_job_state 抛 FileNotFoundError（须先 create_run）。"""
    with pytest.raises(FileNotFoundError):
        run_store.update_job_state("nope", JobState("a", Status.RUNNING))


def test_job_write_reports_the_run_still_open(run_store):
    """update_job_state 返回 run 在这次写时是否仍未结束（ADR 0054 决策五）：run 级为 pending 与为 running 时都返回 True；落库
    结果与不看返回值时相同，running 的 job 再写一次取这次的会话。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.update_job_state("run-1", JobState("a", Status.RUNNING)) is True  # run 级 pending
    assert run_store.try_claim_job("run-1", "b") is True  # run 级 running
    assert run_store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="sess-a")) is True
    got = run_store.load_run_state("run-1")
    assert got.status == Status.RUNNING
    assert got.jobs["a"] == JobState("a", Status.RUNNING, session_id="sess-a")


def test_job_write_on_a_finalized_run_reports_it_ended(run_store):
    """run 级已是终态时 update_job_state 返回 False、不写：job、run 级、ended_at、message 与认领计数都不变（前台执行者据此得知
    run 已被别处记为已结束）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a", claimed_at="2026-11-15T08:00:00+00:00") is True
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", message="已超过允许运行的时间（已记为已结束）") is True
    before = run_store.load_run_state("run-1")
    written = JobState("a", Status.RUNNING, session_id="sess-a", claimed_at="2026-11-15T08:00:00+00:00")
    assert run_store.update_job_state("run-1", written) is False
    assert run_store.load_run_state("run-1") == before


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


@pytest.mark.parametrize("hwm", [3, 4], ids=["same_hwm", "higher_hwm"])
def test_projection_does_not_rewrite_a_terminal_job(run_store, hwm):
    """库中已是终态的 job 不被投影改写，同一等级的终态之间也不以投影为准（终态只写一次，ADR 0031 决定一·补）：之后的投影把它算成
    另一个终态、带另一个会话，HWM 相同或更高，库中仍是先写下的那一份；同一次投影里未结束的 job 照常推进。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    first = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=3,
                     jobs={"a": JobState("a", Status.PASSED, session_id="s1"), "b": JobState("b", Status.PENDING)})
    assert run_store.project_state("run-1", first) is True
    later = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=hwm,
                     jobs={"a": JobState("a", Status.ERROR, session_id="s2"), "b": JobState("b", Status.RUNNING)})
    assert run_store.project_state("run-1", later) is True
    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.PASSED, session_id="s1")
    assert got.jobs["b"].status == Status.RUNNING


def test_claimed_running_not_regressed_to_pending_same_hwm(run_store):
    """机制四护栏：已认领的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。"""
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


def test_projection_writes_only_hwm_run_status_and_jobs(run_store):
    """投影写只写 HWM、run 级与 jobs：投影带来的 started_at、ended_at、message 一律不用，库中值原样保留；HWM 为 None 时按 0 落库。
    两个 adapter 落库结果逐项相等（ADR 0034 机制三「两端对拍口径」）。"""
    from dataclasses import replace

    meta = _meta()
    run_store.create_run(meta, replace(_initial(meta), message="库中消息"))
    carried = RunState(run_id="run-1", status=Status.RUNNING,
                       jobs={"a": JobState("a", Status.RUNNING, session_id="s1"), "b": JobState("b", Status.PENDING)},
                       started_at="2099-01-01T00:00:00Z", ended_at="2099-01-02T00:00:00Z", message="投影消息")
    assert run_store.project_state("run-1", carried) is True
    got = run_store.load_run_state("run-1")
    assert (got.started_at, got.ended_at, got.message) == ("2026-07-19T00:00:00Z", None, "库中消息")
    assert got.high_water_mark == 0
    assert got.status == Status.RUNNING and got.jobs["a"] == JobState("a", Status.RUNNING, session_id="s1")


def test_finalize_without_message_keeps_stored_message(run_store):
    """try_finalize 不给 message 时不动库中值，给了才覆盖：两个 adapter 同一语义。"""
    from dataclasses import replace

    meta = _meta()
    run_store.create_run(meta, replace(_initial(meta), message="库中消息"))
    assert run_store.try_finalize("run-1", Status.PASSED, "t1") is True
    got = run_store.load_run_state("run-1")
    assert (got.status, got.ended_at, got.message) == (Status.PASSED, "t1", "库中消息")

    meta2 = _meta("run-2", "a")
    run_store.create_run(meta2, replace(_initial(meta2), message="库中消息"))
    assert run_store.try_finalize("run-2", Status.ERROR, "t1", message="收尾消息") is True
    assert run_store.load_run_state("run-2").message == "收尾消息"


def test_projection_keeps_pending_while_no_job_started(run_store):
    """喂**真 project() 产物**（非手搓 RunState）验 run 级 status 钳制的 pending 半边：全 pending 的投影不写 run 级，库中
    还没有 job 被认领时 run 级仍是 `create_run` 落的 **pending**（status 如实反映「未启动」，ADR 0034 机制三「run 级状态只进
    不退」条②）。project 的 run 级 status 此时也是 pending（取法：全部 job 为 pending，ADR 0031 决定三），但落库取值只按 job 态定，
    不依赖它。
    """
    from gherkai_core.project import project

    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    projected = project(meta, [])  # 零事件、全 job pending
    assert projected.status == Status.PENDING
    assert run_store.project_state("run-1", projected) is True
    got = run_store.load_run_state("run-1")
    assert got.status == Status.PENDING  # 不虚报 running
    assert run_store.try_finalize("run-1", Status.PASSED, "2026-07-19T02:00:00Z") is True


def test_projection_clamps_the_terminal_run_status_from_project(run_store):
    """喂**真 project() 产物**验钳制仍承重：两个 job 都已结束时 project 的 run 级 status 按取法已是终态 passed，投影写必须钳成
    running；否则紧接的终态写会读到 run 已结束（ALREADY_ENDED），run 的终态与报告不再由收尾写下。钳住之后，收尾的终态写使 run
    成为终态（ENDED_RUN），已由投影写下终态的 job 不被改写。"""
    from gherkai_core.model import ScenarioDone, ScopeDone, ScopeStarted
    from gherkai_core.project import EventRecord, TaskExited, project
    from gherkai_core.run_status import CommitOutcome

    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    recs = []
    for sid in ("a", "b"):
        evs = [ScopeStarted(scope_id=sid, session_id=f"sess-{sid}"), ScenarioDone(scenario_id=f"{sid}:1", status=Status.PASSED),
               ScopeDone(scope_id=sid)]
        recs += [EventRecord(scope_id=sid, kind="event", seq=i + 1, event=ev, emit_ts=0.0) for i, ev in enumerate(evs)]
        recs.append(EventRecord(scope_id=sid, kind="exit", exited=TaskExited(scope_id=sid, exit_code=0)))
    projected = project(meta, recs)
    assert (projected.jobs["a"].status, projected.jobs["b"].status) == (Status.PASSED, Status.PASSED)
    assert projected.status == Status.PASSED, "前提：全部 job 都结束，取法给出终态"
    assert run_store.project_state("run-1", projected) is True
    assert run_store.load_run_state("run-1").status == Status.RUNNING
    outcome = run_store.commit_job_states("run-1", [JobState("a", Status.PASSED), JobState("b", Status.PASSED)],
                                          ended_at="2026-07-19T02:00:00Z")
    assert outcome is CommitOutcome.ENDED_RUN
    got = run_store.load_run_state("run-1")
    assert (got.status, got.ended_at) == (Status.PASSED, "2026-07-19T02:00:00Z")
    assert got.jobs["a"] == JobState("a", Status.PASSED, session_id="sess-a")


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
    """全 job 已终态（传入的 run 级为终态）时投影仍只落 running——run 级终态只随记下最后一个 job 终态的写或结束写写下：若投影提前
    落终态，紧接的终态写会被它挡成 ALREADY_ENDED。"""
    from gherkai_core.run_status import CommitOutcome

    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    all_done = RunState(run_id="run-1", status=Status.FAILED,  # 手搓：传入的 run 级是终态
                        jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.FAILED)},
                        high_water_mark=9)
    assert run_store.project_state("run-1", all_done) is True
    assert run_store.load_run_state("run-1").status == Status.RUNNING  # 不是 passed/failed
    assert run_store.commit_job_states("run-1", [JobState("b", Status.FAILED)], ended_at="t1") is CommitOutcome.ENDED_RUN
    assert run_store.load_run_state("run-1").status == Status.FAILED


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
    local 跳过、DDB 的条件（库中这个 job 为 pending 或 running）不成立、走 CCF 跳过（曾整 entry SET 会补建，改逐属性后父路径
    不存在会 ValidationException 穿出、整 tick 失败——收敛成同一语义并锁定）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    projected = RunState(run_id="run-1", status=Status.RUNNING,
                         jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.PENDING),
                               "ghost": JobState("ghost", Status.PASSED)},
                         started_at="2026-07-19T00:00:00Z", high_water_mark=1)
    assert run_store.project_state("run-1", projected) is True
    got = run_store.load_run_state("run-1")
    assert set(got.jobs) == {"a", "b"} and got.jobs["a"].status == Status.PASSED


def test_bare_pending_projection_leaves_stored_job_unchanged(run_store):
    """投影里的 job 为 pending 且无会话、无认领时刻时，库中该 job 原为 pending、已 claim 的 running、终态还是不在 Map 里，
    落库结果都等于投影前库中该 job 的值（不在 Map 里时仍不在）。DDB 对这类 job 不发写、local 照常合并（ADR 0034 机制三
    「逐 job 写跳过无效果的 pending 项」段），两 adapter 对拍。"""
    meta = _meta("run-1", "p", "r", "t")
    run_store.create_run(meta, _initial(meta, hwm=0))
    seeded = RunState(run_id="run-1", status=Status.RUNNING,
                      jobs={"p": JobState("p", Status.PENDING), "r": JobState("r", Status.PENDING),
                            "t": JobState("t", Status.PASSED, session_id="sess-t")},
                      high_water_mark=1)
    assert run_store.project_state("run-1", seeded) is True
    assert run_store.try_claim_job("run-1", "r", claimed_at="2026-08-13T01:02:03Z") is True
    before = run_store.load_run_state("run-1").jobs
    assert {sid: js.status for sid, js in before.items()} == {
        "p": Status.PENDING, "r": Status.RUNNING, "t": Status.PASSED}, "前提：库中三个 job 分处三个等级"

    bare = RunState(run_id="run-1", status=Status.PENDING,
                    jobs={sid: JobState(sid, Status.PENDING) for sid in ("p", "r", "t", "ghost")},
                    high_water_mark=2)
    assert run_store.project_state("run-1", bare) is True
    got = run_store.load_run_state("run-1")
    assert got.high_water_mark == 2  # 标量写成功，跳过的只是逐 job 写
    assert got.jobs == before  # 各 job 逐字段等于投影前的值（含 r 的 claimed_at、t 的 session_id），ghost 仍不在


def _ddb_store_counting_updates(aws, monkeypatch):
    """DDB store 加 update_item 计数：返回 (store, calls)，calls 依次记下每次 update_item 的参数。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    table = aws["ddb"].Table(aws["table_name"])
    calls: list[dict] = []
    real_update_item = table.update_item

    def counting_update_item(**kwargs):
        calls.append(kwargs)
        return real_update_item(**kwargs)

    monkeypatch.setattr(table, "update_item", counting_update_item)
    return DynamoDBRunStore(table), calls


def test_ddb_projection_writes_scalar_once_plus_unskipped_jobs(aws, monkeypatch):
    """DDB 侧写入次数（ADR 0034 机制三「逐 job 写跳过无效果的 pending 项」段），前提是标量写成功：一次 project_state 发出的
    update_item 为标量写一次加未跳过的 job 数。只跳过 status 为 pending、session_id 与 claimed_at 都为空的 job；
    带认领时刻或带会话的 pending、running、终态照常发写。"""
    store, calls = _ddb_store_counting_updates(aws, monkeypatch)
    meta = _meta("run-1", "p1", "p2", "pc", "ps", "r", "t")
    store.create_run(meta, _initial(meta, hwm=0))
    calls.clear()
    projected = RunState(run_id="run-1", status=Status.RUNNING, jobs={
        "p1": JobState("p1", Status.PENDING),
        "p2": JobState("p2", Status.PENDING),
        "pc": JobState("pc", Status.PENDING, claimed_at="2026-08-13T01:02:03Z"),
        "ps": JobState("ps", Status.PENDING, session_id="sess-ps"),
        "r": JobState("r", Status.RUNNING, session_id="sess-r"),
        "t": JobState("t", Status.PASSED),
    }, high_water_mark=1)
    assert store.project_state("run-1", projected) is True
    assert "#sid" not in calls[0]["ExpressionAttributeNames"], "首次 update_item 应是标量写"
    assert len(calls) == 1 + 4
    assert sorted(c["ExpressionAttributeNames"]["#sid"] for c in calls[1:]) == ["pc", "ps", "r", "t"]


def test_ddb_claim_is_one_write_setting_job_and_run_status(aws, monkeypatch):
    """DDB 侧认领只发一次 update_item，同一条更新表达式里同时置 job 与 run 级（连同状态分组，ADR 0030 决定六）并把认领计数加一，
    条件同时判 job 仍 pending 与 run 未收尾（ADR 0034 机制三「run 级状态只进不退」条①）。只看调用结束后的
    运行态分不出「一次写」与「先写 job、再写 run 级与计数」。"""
    store, calls = _ddb_store_counting_updates(aws, monkeypatch)
    meta = _meta()
    store.create_run(meta, _initial(meta))
    calls.clear()
    assert store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    assert len(calls) == 1
    update = calls[0]["UpdateExpression"].replace(" ", "")
    values, attr_names = calls[0]["ExpressionAttributeValues"], calls[0]["ExpressionAttributeNames"]
    assert "jobs.#sid.#st=:running" in update and ",#st=:rst" in update and values[":rst"] == "running"
    assert "#sg=:rsg" in update and attr_names["#sg"] == "status_group" and values[":rsg"] == "live"
    assert "#cc=if_not_exists(#cc,:zero)+:one" in update and attr_names["#cc"] == "claim_count"
    assert (values[":zero"], values[":one"]) == (0, 1)
    condition = calls[0]["ConditionExpression"].replace(" ", "")
    assert "jobs.#sid.#st=:pending" in condition and "#stIN(:pending,:running)" in condition


def test_ddb_finalize_with_expected_claim_count_is_one_conditional_write(aws, monkeypatch):
    """DDB 侧带期望认领计数的收尾只发一次 update_item，计数的判定在条件表达式里，不是先读再写；
    不给期望计数时条件里不提计数。"""
    store, calls = _ddb_store_counting_updates(aws, monkeypatch)
    meta = _meta()
    store.create_run(meta, _initial(meta))
    assert store.try_claim_job("run-1", "a") is True
    calls.clear()
    assert store.try_finalize("run-1", Status.ERROR, "t1", expected_claim_count=2) is False
    assert store.try_finalize("run-1", Status.ERROR, "t1", expected_claim_count=1) is True
    assert len(calls) == 2
    for call in calls:
        condition = call["ConditionExpression"].replace(" ", "")
        assert "#cc=:ecc" in condition and call["ExpressionAttributeNames"]["#cc"] == "claim_count"
    assert [c["ExpressionAttributeValues"][":ecc"] for c in calls] == [2, 1]

    meta2 = _meta("run-2")
    store.create_run(meta2, _initial(meta2))
    calls.clear()
    assert store.try_finalize("run-2", Status.PASSED, "t1") is True
    assert "claim_count" not in calls[0]["ExpressionAttributeNames"].values()


def test_ddb_job_write_update_item_counts(aws, monkeypatch):
    """DDB 侧 `update_job_state` 恒只发一次 update_item（ADR 0034 机制三「run 级状态只进不退」条③与「两端对拍口径」条；ADR 0054
    决策五）：run 未结束时写成；库中这个 job 已是终态、不在 Map 里时这一次被挡下，不再写；run 已结束时（job 未结束或已结束）这一次被
    挡下、返回 False，没有只写 job 的第二次写；STATE 不存在时一次之后报错。参数错误不发写。被挡下的原因由这次写带回的条目分辨，
    不另读。"""
    from gherkai_core.run_status import CommitOutcome

    store, calls = _ddb_store_counting_updates(aws, monkeypatch)
    meta = _meta()
    store.create_run(meta, _initial(meta))
    assert store.commit_job_states("run-1", [JobState("b", Status.PASSED)], ended_at="t0") is CommitOutcome.OPEN
    for js, still_open in ((JobState("a", Status.RUNNING), True), (JobState("a", Status.RUNNING, session_id="s"), True),
                           (JobState("b", Status.RUNNING), True), (JobState("ghost", Status.RUNNING), True)):
        calls.clear()
        assert store.update_job_state("run-1", js) is still_open
        assert len(calls) == 1
    got = store.load_run_state("run-1")
    assert (got.jobs["a"], got.jobs["b"].status, set(got.jobs)) == (
        JobState("a", Status.RUNNING, session_id="s"), Status.PASSED, {"a", "b"})

    assert store.try_finalize("run-1", Status.FAILED, "t1") is True
    for js in (JobState("a", Status.RUNNING), JobState("b", Status.RUNNING)):  # a 未结束、b 已结束
        calls.clear()
        assert store.update_job_state("run-1", js) is False
        assert len(calls) == 1
    assert store.load_run_state("run-1").jobs["a"] == JobState("a", Status.RUNNING, session_id="s")

    calls.clear()
    with pytest.raises(FileNotFoundError):
        store.update_job_state("nope", JobState("a", Status.RUNNING))
    assert len(calls) == 1
    calls.clear()
    with pytest.raises(ValueError):
        store.update_job_state("run-1", JobState("a", Status.PASSED))
    assert calls == []


def test_ddb_job_write_reports_a_missing_state_even_if_the_run_is_created_after_the_rejection(aws, monkeypatch):
    """DDB 侧的那一次写因 STATE 不存在被挡下时即报 STATE 不存在（ADR 0034 机制三「run 级状态只进不退」条③）：原因取自这次写带回的
    条目（条件判断那一刻没有条目），被挡之后并发建出全 pending 的 run 也不改变它，job 不落进新记录，也不会报告一个仍为 pending 的
    run 已结束；与本机「运行态不存在即报错」一致。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    table = aws["ddb"].Table(aws["table_name"])
    store = DynamoDBRunStore(table)
    ccf = table.meta.client.exceptions.ConditionalCheckFailedException
    meta = _meta("run-race")
    real_update_item = table.update_item
    created = []

    def update_item_creating_the_run_after_the_first_rejection(**kwargs):
        try:
            return real_update_item(**kwargs)
        except ccf:
            if not created:  # 第一次写被挡之后，另一个写入方建出这个 run
                created.append(True)
                DynamoDBRunStore(table).create_run(meta, _initial(meta))
            raise

    monkeypatch.setattr(table, "update_item", update_item_creating_the_run_after_the_first_rejection)
    with pytest.raises(FileNotFoundError):
        store.update_job_state("run-race", JobState("a", Status.RUNNING))
    assert created == [True]
    got = store.load_run_state("run-race")
    assert got.status == Status.PENDING
    assert got.jobs["a"] == JobState("a", Status.PENDING)


def test_ddb_rejected_scalar_write_issues_no_job_writes(aws, monkeypatch):
    """标量写条件不成立（更小 HWM）时 project_state 直接返回 False、不发逐 job 写：update_item 只有标量写那一次。"""
    store, calls = _ddb_store_counting_updates(aws, monkeypatch)
    meta = _meta()
    store.create_run(meta, _initial(meta, hwm=0))
    fresh = RunState(run_id="run-1", status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.RUNNING)},
                     high_water_mark=10)
    assert store.project_state("run-1", fresh) is True
    calls.clear()
    stale = RunState(run_id="run-1", status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.RUNNING)},
                     high_water_mark=5)  # 两个 job 都不属于跳过项：标量写被挡后若仍发逐 job 写，调用次数会多出两次
    assert store.project_state("run-1", stale) is False
    assert len(calls) == 1


# ---------- 真 DDB 复验（integration 标记，默认 deselect；需真表 + 真凭证）----------
# moto 的条件表达式是模拟实现——认领的排他性与 job 级单调条件写是**机制三/四的承重面**（ADR 0034），
# 绿≠对：这两条在真 DDB 上复验同一语义，只挑「moto 失真就会静默放过」的那两个断言，不复刻全部对拍。
# 运行：`uv run pytest core/tests -m integration`（真表/真桶名经 AWS_DDB_TABLE / AWS_S3_BUCKET 传，见 tests/README.md）。

_real_counter = itertools.count(1)  # 单进程内递增，给真表上的 run_id 去重（无随机源）


def _real_store(real_aws):
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    return DynamoDBRunStore(real_aws["ddb"].Table(real_aws["table_name"]))


def _real_run_id(real_aws, tag: str) -> str:
    """真表上本次运行专属的 run_id，并登记自清理（多次执行不撞名、不留垃圾）。"""
    rid = f"it-cw-{tag}-{next(_real_counter)}"
    real_aws["cleanup_run_id"](rid)
    return rid


@pytest.mark.integration
def test_claim_is_exclusive_on_real_ddb(real_aws):
    """真 DDB 的机制四 CAS：两个推进器认领同一个 pending job，**恰一个**成功（另一个见条件失败）。

    两个 store 实例对应两个推进器各持自己的表句柄（对位 per-run 进程与 `status --wait` 接力者同时在推同一 run）。
    赢家是谁不重要、「只有一个」才是承重的：若真 DDB 的条件写放过第二次，就会重复 RunTask、同一 scope 执行两遍。
    """
    rid = _real_run_id(real_aws, "claim")
    store_a, store_b = _real_store(real_aws), _real_store(real_aws)
    meta = _meta(rid)
    store_a.create_run(meta, _initial(meta))

    claims = [store_a.try_claim_job(rid, "a"), store_b.try_claim_job(rid, "a")]
    assert claims.count(True) == 1, f"CAS 不排他：{claims}"
    state = store_a.load_run_state(rid)
    assert state.jobs["a"].status == Status.RUNNING
    assert state.jobs["b"].status == Status.PENDING  # 另一个 job 不受污染


@pytest.mark.integration
def test_stale_projection_never_regresses_terminal_job_on_real_ddb(real_aws):
    """真 DDB 的机制三②：终态 job 不被 stale 投影刷回 running——两道闸各验一遍。

    - 同 HWM（task_exited 无数值 seq，两投影 HWM 相等）→ run 级 HWM 闸挡不住，靠 job 级单调条件写挡；
    - 更小 HWM → run 级 HWM 闸直接挡下整次投影（返回 False）。
    刷回的后果是永久错态（run=passed 而 job 恒 running），故这两道闸的真 DDB 行为必须实证、不能只信 moto。
    """
    rid = _real_run_id(real_aws, "stale")
    store = _real_store(real_aws)
    meta = _meta(rid)
    store.create_run(meta, _initial(meta, hwm=0))

    fresh = RunState(run_id=rid, status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.RUNNING)},
                     high_water_mark=3)
    assert store.project_state(rid, fresh) is True

    same_hwm = RunState(run_id=rid, status=Status.RUNNING,
                        jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.RUNNING)},
                        high_water_mark=3)
    store.project_state(rid, same_hwm)  # 整体返回值不限（HWM 相等本就允许写）——看的是终态有没有被刷回
    assert store.load_run_state(rid).jobs["a"].status == Status.PASSED

    older = RunState(run_id=rid, status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.PENDING)},
                     high_water_mark=2)
    assert store.project_state(rid, older) is False  # 更小 HWM：整次投影被挡
    got = store.load_run_state(rid)
    assert got.jobs["a"].status == Status.PASSED and got.high_water_mark == 3


def test_finalize_message_lands_with_terminal_status_and_is_absent_otherwise(run_store):
    """run 级消息：随 try_finalize 同一次写入、读回原文；不给时读回 None（不写键）；已终态的 run 再带消息 finalize
    被挡，库里的消息不变。两 adapter 同语义。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.load_run_state("run-1").message is None
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", message="提交记录不能由本后端执行：结构版本 2") is True
    state = run_store.load_run_state("run-1")
    assert state.status == Status.ERROR and state.message == "提交记录不能由本后端执行：结构版本 2"
    assert run_store.try_finalize("run-1", Status.PASSED, "t2", message="别人") is False
    assert run_store.load_run_state("run-1").message == "提交记录不能由本后端执行：结构版本 2"

    meta2 = _meta("run-2", "a")
    run_store.create_run(meta2, _initial(meta2))
    assert run_store.try_finalize("run-2", Status.PASSED, "t1") is True
    assert run_store.load_run_state("run-2").message is None


def test_finalized_run_keeps_message_against_later_projection_and_claim(run_store):
    """run 级消息的边界护栏：已带消息终结的 run，再来更高 HWM 的投影被挡（status、ended_at、message 全不变）；job 认领也不抹掉消息
    （local 的读改写与 DDB 的逐属性 SET 对拍）。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", message="原因") is True
    later = RunState(run_id="run-1", status=Status.RUNNING,
                     jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.PENDING)}, high_water_mark=5)
    assert run_store.project_state("run-1", later) is False
    state = run_store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.ERROR, "t1", "原因")
    run_store.try_claim_job("run-1", "a", claimed_at="c1")
    assert run_store.load_run_state("run-1").message == "原因"


# ---------- 建 run 只在 run 不存在时成立（ADR 0054 决策五）----------

def test_create_run_on_an_existing_run_fails_and_changes_nothing(run_store):
    """对已有的 run 再建抛 FileExistsError：definition 与运行态都不变——不论再建时给的 definition、初始运行态是否不同，
    也不论这个 run 已推进到哪一步（这里已认领、已收尾）。没有整份重写运行态的入口，终态不会被一次建 run 改回 pending。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", message="原因") is True
    meta_before, state_before = run_store.load_run_meta("run-1"), run_store.load_run_state("run-1")

    other = _meta("run-1", "x")
    with pytest.raises(FileExistsError):
        run_store.create_run(other, _initial(other))
    assert run_store.load_run_meta("run-1") == meta_before
    assert run_store.load_run_state("run-1") == state_before


# ---------- 认领计数 ----------

def test_claim_count_starts_at_zero_and_counts_successful_claims_only(run_store):
    """建 run 时为 0；每次认领成功加一；三种认领失败（已非 pending、job 不存在、run 已收尾）都不改它
    （ADR 0034 机制三「run 级状态只进不退」条①）。"""
    meta = _meta("run-1", "a", "b", "c")
    run_store.create_run(meta, _initial(meta))
    assert run_store.load_run_state("run-1").claim_count == 0
    assert run_store.try_claim_job("run-1", "a") is True
    assert run_store.try_claim_job("run-1", "b") is True
    assert run_store.load_run_state("run-1").claim_count == 2
    assert run_store.try_claim_job("run-1", "a") is False  # 已非 pending
    assert run_store.try_claim_job("run-1", "ghost") is False  # 不在 definition 里
    assert run_store.load_run_state("run-1").claim_count == 2
    assert run_store.try_finalize("run-1", Status.ERROR, "t1") is True
    assert run_store.try_claim_job("run-1", "c") is False  # run 已收尾
    assert run_store.load_run_state("run-1").claim_count == 2


def test_claim_count_is_left_alone_by_the_other_write_entries(run_store):
    """执行中的写、终态写、投影写（传入的运行态带着别的计数）与结束写都不改认领计数：它只由认领写。"""
    meta = _meta()
    run_store.create_run(meta, _initial(meta, hwm=0))
    from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome

    assert run_store.try_claim_job("run-1", "a") is True
    assert run_store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="sess-a")) is True
    assert run_store.commit_job_states("run-1", [JobState("b", Status.PASSED)], ended_at="t0") is CommitOutcome.OPEN
    carried = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=3, claim_count=99,
                       jobs={"a": JobState("a", Status.PASSED), "b": JobState("b", Status.PASSED)})
    assert run_store.project_state("run-1", carried) is True
    assert run_store.load_run_state("run-1").claim_count == 1
    assert run_store.commit_job_states("run-1", [JobState("a", Status.PASSED)], ended_at="t1") is CommitOutcome.ENDED_RUN
    assert run_store.load_run_state("run-1").claim_count == 1

    meta2 = _meta("run-2")
    run_store.create_run(meta2, _initial(meta2, hwm=0))
    assert run_store.try_claim_job("run-2", "a") is True
    assert run_store.end_run("run-2", RUN_ENDINGS["settle-advancer-exited"], ended_at="t1") is True
    assert run_store.load_run_state("run-2").claim_count == 1


@pytest.fixture
def raw_run_store(request, tmp_path, aws):
    """对拍用的 adapter，连同改写库中原始记录的两个手段（附加键、删掉认领计数），两端各一套。

    产出 (store, set_extra(run_id, key, value), get_extra(run_id, key), drop_claim_count(run_id))。本机直接改 run_state.json 的
    顶层键，云端直接改 STATE item 的顶层属性：附加键只能这样造（模型里没有它），缺认领计数的记录同样只能这样造（写端恒写）。
    """
    import json

    if request.param == "local":
        from gherkai_core.adapters.run_store.local import LocalRunStore

        def path(run_id):
            return tmp_path / run_id / "run_state.json"

        def edit(run_id, change):
            d = json.loads(path(run_id).read_text(encoding="utf-8"))
            change(d)
            path(run_id).write_text(json.dumps(d), encoding="utf-8")

        return (LocalRunStore(tmp_path),
                lambda run_id, key, value: edit(run_id, lambda d: d.__setitem__(key, value)),
                lambda run_id, key: json.loads(path(run_id).read_text(encoding="utf-8")).get(key),
                lambda run_id: edit(run_id, lambda d: d.pop("claim_count")))
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    table = aws["ddb"].Table(aws["table_name"])

    def key_of(run_id):
        return {"run_id": run_id, "item_type": "STATE"}

    return (DynamoDBRunStore(table),
            lambda run_id, key, value: table.update_item(Key=key_of(run_id), UpdateExpression="SET #k = :v",
                                                         ExpressionAttributeNames={"#k": key},
                                                         ExpressionAttributeValues={":v": value}),
            lambda run_id, key: table.get_item(Key=key_of(run_id), ConsistentRead=True)["Item"].get(key),
            lambda run_id: table.update_item(Key=key_of(run_id), UpdateExpression="REMOVE claim_count"))


_both = pytest.mark.parametrize("raw_run_store", ["local", "ddb"], indirect=True)


@_both
def test_missing_claim_count_reads_as_zero_and_claims_count_from_it(raw_run_store):
    """缺认领计数的记录读作 0，认领从 0 起算得 1；期望计数为 0 的收尾写在缺键的记录上成立（两端同一口径）。"""
    store, _set, get_extra, drop_claim_count = raw_run_store
    meta = _meta()
    store.create_run(meta, _initial(meta))
    assert get_extra("run-1", "claim_count") == 0, "前提：写端恒写认领计数"
    drop_claim_count("run-1")
    assert get_extra("run-1", "claim_count") is None
    assert store.load_run_state("run-1").claim_count == 0
    assert store.try_claim_job("run-1", "a") is True
    assert store.load_run_state("run-1").claim_count == 1

    meta2 = _meta("run-2")
    store.create_run(meta2, _initial(meta2))
    drop_claim_count("run-2")
    assert store.try_finalize("run-2", Status.ERROR, "t1", expected_claim_count=1) is False
    assert store.try_finalize("run-2", Status.ERROR, "t1", expected_claim_count=0) is True


def test_finalize_with_expected_claim_count_lands_only_on_an_equal_count(run_store):
    """收尾写带期望的认领计数时，只在库中计数等于它时写成；不等时不写、运行态整份不变。不给时不判计数，与原行为相同。
    run 已收尾时即使计数相等也写不成。"""
    meta = _meta("run-1", "a", "b", "c")
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a") is True
    before = run_store.load_run_state("run-1")
    assert before.claim_count == 1
    for stale in (0, 2):
        assert run_store.try_finalize("run-1", Status.ERROR, "t1", message="m", expected_claim_count=stale) is False
        assert run_store.load_run_state("run-1") == before
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", message="m", expected_claim_count=1) is True
    got = run_store.load_run_state("run-1")
    assert (got.status, got.ended_at, got.message, got.claim_count) == (Status.ERROR, "t1", "m", 1)
    assert run_store.try_finalize("run-1", Status.PASSED, "t2", expected_claim_count=1) is False

    meta2 = _meta("run-2")
    run_store.create_run(meta2, _initial(meta2))
    assert run_store.try_claim_job("run-2", "a") is True
    assert run_store.try_claim_job("run-2", "b") is True
    assert run_store.try_finalize("run-2", Status.PASSED, "t1") is True  # 不给期望计数：计数为 2 也照常写成


def test_finalize_conditioned_on_the_read_count_is_blocked_by_a_claim_landing_after_the_read(run_store):
    """到期收尾的竞态：一方读到运行态（计数 n）之后另一方的认领落下，前者以 n 为条件的收尾
    被挡、run 不结束，新认领的 job 仍是 running；以新读到的计数重试才写成。"""
    meta = _meta("run-1", "a", "b")
    run_store.create_run(meta, _initial(meta))
    assert run_store.try_claim_job("run-1", "a") is True
    seen = run_store.load_run_state("run-1")
    assert run_store.try_claim_job("run-1", "b", claimed_at="2026-08-13T01:02:03Z") is True  # 另一方的认领落在读之后
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", expected_claim_count=seen.claim_count) is False
    got = run_store.load_run_state("run-1")
    assert got.status == Status.RUNNING and got.jobs["b"] == JobState("b", Status.RUNNING, claimed_at="2026-08-13T01:02:03Z")
    assert run_store.try_finalize("run-1", Status.ERROR, "t1", expected_claim_count=got.claim_count) is True


# ---------- 顶层附加键整体保留（ADR 0030 决定四「local 的顶层附加键整体保留」）----------

_LAUNCHER = {"pid_namespace": "ns-1", "pid": 4242, "start_time": "123456", "host": "dev-box"}


def _job_write(store):
    store.update_job_state("run-1", JobState("a", Status.RUNNING, session_id="sess-a"))
    assert store.load_run_state("run-1").jobs["a"].session_id == "sess-a"


def _claim(store):
    assert store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True


def _project(store):
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=2,
                         jobs={"a": JobState("a", Status.RUNNING, session_id="sess-a"), "b": JobState("b", Status.PENDING)})
    assert store.project_state("run-1", projected) is True


def _finalize(store):
    assert store.try_finalize("run-1", Status.ERROR, "t1", message="原因") is True


def _commit(store):
    from gherkai_core.run_status import CommitOutcome
    assert store.try_claim_job("run-1", "a", claimed_at="2026-08-13T01:02:03Z") is True
    assert store.commit_job_states("run-1", [JobState("a", Status.PASSED, claimed_at="2026-08-13T01:02:03Z")],
                                   ended_at="t1") is CommitOutcome.OPEN


def _end(store):
    from gherkai_core.run_status import RUN_ENDINGS
    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="t1") is True


@_both
@pytest.mark.parametrize("write", [_job_write, _claim, _project, _finalize, _commit, _end],
                         ids=["update_job_state", "try_claim_job", "project_state", "try_finalize", "commit_job_states",
                              "end_run"])
def test_each_write_entry_keeps_top_level_extras(raw_run_store, write):
    """运行态记录顶层不属于 RunState 模型的键（这里是一个发起进程标识形态的对象与后台执行标记）经每个写入口原样保留：
    本机在锁内读到的文件里整体带回，云端 update_item 本来就不碰未提及的属性。每个写入口都确认写成，免得保留是因为没写。"""
    store, set_extra, get_extra, _drop = raw_run_store
    meta = _meta()
    store.create_run(meta, _initial(meta, hwm=0))
    set_extra("run-1", "launcher", _LAUNCHER)
    set_extra("run-1", "detached", True)
    write(store)
    assert get_extra("run-1", "launcher") == _LAUNCHER
    assert get_extra("run-1", "detached") is True
    assert not hasattr(store.load_run_state("run-1"), "launcher")  # 附加键不进模型
