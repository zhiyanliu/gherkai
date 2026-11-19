"""RunStore 上 run 状态只由 job 终态算出的两个写入口（ADR 0031 决定三、ADR 0030 决定四）：结束写 `end_run` 与带结果的 job 终态写
`commit_job_states`。

本机（fcntl 文件锁内读改写）与云端（moto）运行同一批断言，保两个 adapter 的语义一致。覆盖：
- 结束写：run 未结束时 pending 记 skipped、running 记 aborted，各带说明表里的一句，会话与认领时刻保留，已是终态的 job 不变；run 状态
  按取法成为终态，run 级说明与结束时刻同一次写下；运行定义不可用的变体把未结束的 job 都记 error；不结束执行中 job 的来路（说明表里
  aborted 一格不出现）在有 running 的 job 时不写；run 已结束、记录不存在时返回 False、不改任何东西；同一个 run 两次结束写只有第一次写成。
- 终态写：三种返回值各自的情形，一次写记多个 job，已是终态的 job 不被改写，run 已结束时写不成、运行态不变，使 run 成为终态的那次写
  带上结束时刻，参数不合要求时不写；给出的 job 与库中的条目按字段合并（会话、认领时刻、job 级说明各自的规则）。
- 终态只写一次：执行中的写（update_job_state）不改写已结束的 job，run 未结束与已由结束写结束两种情形都是；投影不改写终态写与结束写
  记下的终态，云端在投影的标量一步与逐 job 写之间落下结束写时同样如此。执行中的写也不臆造运行态里没有的 job。
- 没有记录的执行在内存里算出的运行态（`run_status.state_without_record`）与两个写入口按同一组执行事实写下的记录相同。
- 先后：在调用方读运行态与它的写之间插入另一方的写（认领、执行中的写、投影、处置的结束写、另一方的终态写），按固定次序构造，不靠
  线程竞争。
- job 级说明：投影与认领保留库中的说明。
本机写入口在同一把文件锁内互斥的结论靠真实进程核对，见 test_local_run_store_lock.py；这里的两个写入口与其余写入口共用同一个锁内
读改写的路径。云端的写入序号、插在 adapter 自己的读与写之间的写、写入次数与重读的次数上限见 test_ddb_write_seq.py。
"""
from __future__ import annotations

import pytest

from gherkai_core.model import Job, JobResult, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome, definition_unavailable_ending, state_without_record

_T0 = "2026-11-19T00:00:00Z"
_CLAIMED = "2026-11-19T00:01:00Z"
_ENDED = "2026-11-19T02:00:00Z"


def _meta(run_id: str, scope_ids: tuple[str, ...]) -> RunMeta:
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="novaact", timeout_s=300.0,
            scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
        for s in scope_ids)
    return RunMeta(run_id=run_id, created_at=_T0, jobs=jobs, deadline_at="2026-11-19T01:00:00+00:00")


def _create(store, scope_ids=("a", "b", "c"), *, run_id="run-1", hwm=None, messages=None) -> None:
    """建一个全 pending 的 run。messages 给出时，对应的 job 在初始运行态里就带 job 级说明（只为核对别的写保留它）。"""
    messages = messages or {}
    meta = _meta(run_id, scope_ids)
    store.create_run(meta, RunState(
        run_id=run_id, status=Status.PENDING, started_at=_T0, high_water_mark=hwm,
        jobs={s: JobState(s, Status.PENDING, message=messages.get(s)) for s in scope_ids}))


def _claim(store, scope_id, *, session=None, run_id="run-1") -> None:
    """认领一个 job（带认领时刻）；给出 session 时再以执行中的写带上会话。"""
    assert store.try_claim_job(run_id, scope_id, claimed_at=_CLAIMED) is True
    if session is not None:
        store.update_job_state(run_id, JobState(scope_id, Status.RUNNING, session_id=session, claimed_at=_CLAIMED))


def _done(scope_id, status, *, session=None) -> JobState:
    """由执行结果结束的 job 的终态（调用方带上会话与认领时刻）。"""
    return JobState(scope_id, status, session_id=session, claimed_at=_CLAIMED)


@pytest.fixture(params=["local", "ddb"])
def run_store(request, tmp_path):
    """两个 adapter 各来一遍（对拍）。本机用 tmp_path；云端用 moto 建好的表。"""
    if request.param == "local":
        from gherkai_core.adapters.run_store.local import LocalRunStore
        return LocalRunStore(tmp_path)
    return request.getfixturevalue("ddb_run_store")


# ---------- 结束写 end_run ----------

def test_end_run_marks_pending_skipped_running_aborted_and_leaves_terminal_jobs(run_store):
    """处置（锁拿到了）的结束写：pending 记 skipped、running 记 aborted，各带这一行的说明，会话与认领时刻保留；已是终态的 job 原样；
    run 状态按取法（passed、skipped、aborted 并存）为 aborted，run 级说明与结束时刻同一次写下；认领计数、HWM 与开始时刻不变。"""
    _create(run_store, hwm=3)
    _claim(run_store, "b", session="sess-b")
    _claim(run_store, "c", session="sess-c")
    assert run_store.commit_job_states("run-1", [_done("c", Status.PASSED, session="sess-c")],
                                       ended_at="never") is CommitOutcome.OPEN
    before = run_store.load_run_state("run-1")
    ending = RUN_ENDINGS["settle-advancer-exited"]

    assert run_store.end_run("run-1", ending, ended_at=_ENDED) is True

    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.SKIPPED, message=ending.skipped_message)
    assert got.jobs["b"] == JobState("b", Status.ABORTED, session_id="sess-b", claimed_at=_CLAIMED,
                                     message=ending.aborted_message)
    assert got.jobs["c"] == before.jobs["c"]
    assert (got.status, got.message, got.ended_at) == (Status.ABORTED, ending.run_message, _ENDED)
    assert (got.claim_count, got.high_water_mark, got.started_at) == (2, 3, _T0)


@pytest.mark.parametrize("route, setup, expected_jobs, expected_run", [
    # 执行方自己到期：全部没有启动
    ("deadline", {}, {"a": Status.SKIPPED, "b": Status.SKIPPED}, Status.ABORTED),
    # fail-fast：一个 job 出错，余下没有启动，run 是 error 而不是 aborted
    ("fail-fast", {"a": Status.ERROR}, {"a": Status.ERROR, "b": Status.SKIPPED}, Status.ERROR),
    # 使用方中断：已执行的 job 通过，余下没有启动，run 没有执行完
    ("interrupt", {"a": Status.PASSED}, {"a": Status.PASSED, "b": Status.SKIPPED}, Status.ABORTED),
    # 处置（已过期限加 300 秒）：一个 job 断言没过，一个已认领而没有结果
    ("settle-past-deadline", {"a": Status.FAILED, "b": Status.RUNNING}, {"a": Status.FAILED, "b": Status.ABORTED},
     Status.FAILED),
])
def test_end_run_takes_the_run_status_from_the_job_statuses(run_store, route, setup, expected_jobs, expected_run):
    """各条来路的结束写之后，未结束的 job 按运行态里的状态记成终态，run 状态由各 job 的终态按取法算出，run 级说明取这一行。"""
    _create(run_store, ("a", "b"))
    for sid, status in setup.items():
        _claim(run_store, sid)
        if status != Status.RUNNING:
            assert run_store.commit_job_states("run-1", [_done(sid, status)], ended_at="never") is CommitOutcome.OPEN
    ending = RUN_ENDINGS[route]

    assert run_store.end_run("run-1", ending, ended_at=_ENDED) is True

    got = run_store.load_run_state("run-1")
    assert {sid: js.status for sid, js in got.jobs.items()} == expected_jobs
    assert (got.status, got.message, got.ended_at) == (expected_run, ending.run_message, _ENDED)
    for sid, status in expected_jobs.items():
        expected_message = {Status.SKIPPED: ending.skipped_message, Status.ABORTED: ending.aborted_message}.get(status)
        assert got.jobs[sid].message == expected_message


def test_end_run_definition_unavailable_marks_every_unfinished_job_error(run_store):
    """运行定义不可用的变体：pending 与 running 的 job 都记 error，说明同 run 级；已是终态的 job 不变；run 为 error。"""
    _create(run_store)
    _claim(run_store, "b", session="sess-b")
    _claim(run_store, "c")
    run_store.commit_job_states("run-1", [_done("c", Status.PASSED)], ended_at="never")
    reason = "提交记录不完整或形态不对，后端不能执行它；请用与后端同版本的 gherkai 重新提交"

    assert run_store.end_run("run-1", definition_unavailable_ending(reason), ended_at=_ENDED) is True

    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.ERROR, message=reason)
    assert got.jobs["b"] == JobState("b", Status.ERROR, session_id="sess-b", claimed_at=_CLAIMED, message=reason)
    assert got.jobs["c"].status == Status.PASSED and got.jobs["c"].message is None
    assert (got.status, got.message, got.ended_at) == (Status.ERROR, reason, _ENDED)


@pytest.mark.parametrize("route", ["deadline", "fail-fast", "interrupt"])
def test_end_run_of_a_route_that_does_not_end_running_jobs_leaves_a_run_with_a_running_job(run_store, route):
    """不结束执行中 job 的来路（ends_running_jobs 为 False）：运行态里有 running 的 job 时结束写不成立，返回 False，运行态整份不变。"""
    _create(run_store)
    _claim(run_store, "a")
    before = run_store.load_run_state("run-1")

    assert run_store.end_run("run-1", RUN_ENDINGS[route], ended_at=_ENDED) is False
    assert run_store.load_run_state("run-1") == before


def test_end_run_on_an_ended_run_changes_nothing(run_store):
    """run 已结束（这里由最后一个 job 的终态写结束）时结束写返回 False，运行态整份不变。"""
    _create(run_store, ("a",))
    _claim(run_store, "a")
    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.ENDED_RUN
    before = run_store.load_run_state("run-1")

    assert run_store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at="later") is False
    assert run_store.load_run_state("run-1") == before


def test_end_run_without_a_record_returns_false(run_store):
    """run 的记录不存在时结束写返回 False，不建出记录。"""
    assert run_store.end_run("ghost", RUN_ENDINGS["deadline"], ended_at=_ENDED) is False
    assert run_store.load_run_state("ghost") is None


def test_only_the_first_of_two_end_runs_lands(run_store):
    """同一个 run 两次结束写（两个处置方，或处置与执行方自己到期）：第一次写成，第二次返回 False，记录是第一次写下的。"""
    _create(run_store)
    _claim(run_store, "a")
    assert run_store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True
    first = run_store.load_run_state("run-1")

    assert run_store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at="later") is False
    assert run_store.load_run_state("run-1") == first


def test_end_run_by_deadline_does_not_overtake_a_claim_landing_after_the_read(run_store):
    """执行方读到运行态（没有执行中的 job、余下的都没有启动）之后另一方的认领落下：到期的结束写不成立、run 不结束，新认领的 job
    仍是 running；那个 job 记下终态之后再做结束写才写成，余下没有启动的记 skipped。"""
    _create(run_store, ("a", "b"))
    seen = run_store.load_run_state("run-1")
    assert all(js.status == Status.PENDING for js in seen.jobs.values()), "前提：读到的运行态里没有执行中的 job"
    _claim(run_store, "b")  # 另一方的认领落在读之后

    assert run_store.end_run("run-1", RUN_ENDINGS["deadline"], ended_at=_ENDED) is False
    got = run_store.load_run_state("run-1")
    assert got.status == Status.RUNNING and got.jobs["b"].status == Status.RUNNING

    assert run_store.commit_job_states("run-1", [_done("b", Status.PASSED)], ended_at="never") is CommitOutcome.OPEN
    assert run_store.end_run("run-1", RUN_ENDINGS["deadline"], ended_at=_ENDED) is True
    got = run_store.load_run_state("run-1")
    assert (got.jobs["a"].status, got.jobs["b"].status, got.status) == (Status.SKIPPED, Status.PASSED, Status.ABORTED)


def test_end_run_by_deadline_lands_when_a_claim_after_the_read_already_has_its_result(run_store):
    """执行方读到运行态（两个 job 都没有启动）之后，另一方认领 b、起 task 失败、以启动失败的补偿记下 b 的终态，然后执行方才做到期的
    结束写：结束写按写下时的运行态判断，这时没有 running 的 job，写成；a 记 skipped，b 保留它的 error、不带说明，run 随之为 error。
    「读之后出现了新的认领」本身不使结束写不成立，不成立的只是写下时仍有执行中 job 的情形。"""
    _create(run_store, ("a", "b"))
    seen = run_store.load_run_state("run-1")
    assert all(js.status == Status.PENDING for js in seen.jobs.values()), "前提：读到的运行态里没有执行中的 job"
    _claim(run_store, "b")  # 另一方的认领与补偿写都落在读之后
    assert run_store.commit_job_states("run-1", [_done("b", Status.ERROR)], ended_at="never") is CommitOutcome.OPEN
    ending = RUN_ENDINGS["deadline"]

    assert run_store.end_run("run-1", ending, ended_at=_ENDED) is True

    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.SKIPPED, message=ending.skipped_message)
    assert got.jobs["b"] == _done("b", Status.ERROR)
    assert (got.status, got.message, got.ended_at) == (Status.ERROR, ending.run_message, _ENDED)


# ---------- 带结果的 job 终态写 commit_job_states ----------

def test_commit_returns_open_while_other_jobs_are_unfinished(run_store):
    """还有 job 未结束时终态写写成、返回 OPEN：job 记为给出的终态，run 状态按取法为 running，不写结束时刻。"""
    _create(run_store, ("a", "b"), hwm=2)
    _claim(run_store, "a", session="sess-a")
    _claim(run_store, "b")

    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED, session="sess-a")],
                                       ended_at=_ENDED) is CommitOutcome.OPEN

    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == _done("a", Status.PASSED, session="sess-a")
    assert got.jobs["b"].status == Status.RUNNING
    assert (got.status, got.ended_at, got.message) == (Status.RUNNING, None, None)
    assert (got.claim_count, got.high_water_mark, got.started_at) == (2, 2, _T0)


def test_commit_of_the_last_unfinished_job_ends_the_run_with_its_ended_at(run_store):
    """记下最后一个未结束 job 的终态写返回 ENDED_RUN：run 状态按取法成为终态，同一次写下调用方给的结束时刻；run 级说明不写。"""
    _create(run_store, ("a", "b"))
    _claim(run_store, "a")
    _claim(run_store, "b")
    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="not-this") is CommitOutcome.OPEN

    assert run_store.commit_job_states("run-1", [_done("b", Status.FAILED)], ended_at=_ENDED) is CommitOutcome.ENDED_RUN

    got = run_store.load_run_state("run-1")
    assert (got.status, got.ended_at, got.message) == (Status.FAILED, _ENDED, None)


def test_one_commit_records_several_jobs(run_store):
    """一次终态写记多个 job：没有记到的 job 仍未结束时为 OPEN；一次记下全部未结束的 job 时为 ENDED_RUN，run 状态按取法取 error。"""
    _create(run_store)
    for sid in ("a", "b", "c"):
        _claim(run_store, sid)
    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED), _done("b", Status.FAILED)],
                                       ended_at="not-this") is CommitOutcome.OPEN
    mid = run_store.load_run_state("run-1")
    assert {sid: js.status for sid, js in mid.jobs.items()} == {
        "a": Status.PASSED, "b": Status.FAILED, "c": Status.RUNNING}

    _create(run_store, ("x", "y"), run_id="run-2")
    _claim(run_store, "x", run_id="run-2")
    _claim(run_store, "y", run_id="run-2")
    assert run_store.commit_job_states("run-2", [_done("x", Status.ERROR), _done("y", Status.PASSED)],
                                       ended_at=_ENDED) is CommitOutcome.ENDED_RUN
    got = run_store.load_run_state("run-2")
    assert (got.jobs["x"].status, got.jobs["y"].status, got.status, got.ended_at) == (
        Status.ERROR, Status.PASSED, Status.ERROR, _ENDED)


def test_commit_does_not_rewrite_a_job_that_is_already_terminal(run_store):
    """job 的终态只写一次：库中已是终态的 job 不被后来的终态写改写。只带这个 job 的写返回 OPEN、运行态不变；与别的 job 一起写时只记
    别的 job，run 状态按库中保留的终态算。"""
    _create(run_store, ("a", "b"))
    _claim(run_store, "a", session="sess-a")
    _claim(run_store, "b")
    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED, session="sess-a")],
                                       ended_at="never") is CommitOutcome.OPEN
    before = run_store.load_run_state("run-1")

    assert run_store.commit_job_states("run-1", [_done("a", Status.ERROR, session="other")],
                                       ended_at="never") is CommitOutcome.OPEN
    assert run_store.load_run_state("run-1") == before

    assert run_store.commit_job_states("run-1", [_done("a", Status.ERROR), _done("b", Status.PASSED)],
                                       ended_at=_ENDED) is CommitOutcome.ENDED_RUN
    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == before.jobs["a"]
    assert (got.jobs["b"].status, got.status) == (Status.PASSED, Status.PASSED)


def test_commit_on_an_ended_run_does_not_land(run_store):
    """run 已结束（这里由处置的结束写结束）时终态写返回 ALREADY_ENDED，运行态整份不变：结束写记下的 aborted 不被真实结果改写。"""
    _create(run_store, ("a",))
    _claim(run_store, "a")
    assert run_store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at=_ENDED) is True
    before = run_store.load_run_state("run-1")

    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED)],
                                       ended_at="later") is CommitOutcome.ALREADY_ENDED
    assert run_store.load_run_state("run-1") == before


def test_commit_after_an_end_run_inserted_between_read_and_write_does_not_land(run_store):
    """调用方读到运行态（job 执行中）之后、写下终态之前，处置的结束写落下：这次终态写返回 ALREADY_ENDED，记录是结束写写下的。"""
    _create(run_store, ("a", "b"))
    _claim(run_store, "a")
    _claim(run_store, "b")
    seen = run_store.load_run_state("run-1")
    assert seen.status == Status.RUNNING, "前提：调用方读到的 run 未结束"
    assert run_store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True  # 插在读与写之间
    ended = run_store.load_run_state("run-1")

    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED)],
                                       ended_at="later") is CommitOutcome.ALREADY_ENDED
    assert run_store.load_run_state("run-1") == ended


def test_only_one_of_two_writers_gets_ended_run(run_store):
    """两个写入方各持一个 job 的结果、都读到另一个 job 未结束：先写的一方得 OPEN，后写的一方的写使 run 成为终态、得 ENDED_RUN；
    先写的一方再写一次得 ALREADY_ENDED。返回 ENDED_RUN 的只有一方，生成报告的也就只有一方。"""
    _create(run_store, ("a", "b"))
    _claim(run_store, "a")
    _claim(run_store, "b")
    seen = run_store.load_run_state("run-1")
    assert seen.jobs["a"].status == seen.jobs["b"].status == Status.RUNNING, "前提：两方读到的都是两个 job 执行中"

    assert run_store.commit_job_states("run-1", [_done("b", Status.PASSED)], ended_at="t-b") is CommitOutcome.OPEN
    assert run_store.commit_job_states("run-1", [_done("a", Status.PASSED)], ended_at="t-a") is CommitOutcome.ENDED_RUN
    assert run_store.commit_job_states("run-1", [_done("b", Status.PASSED)],
                                       ended_at="t-b2") is CommitOutcome.ALREADY_ENDED
    got = run_store.load_run_state("run-1")
    assert (got.status, got.ended_at) == (Status.PASSED, "t-a")


def test_end_run_after_the_last_commit_ended_the_run_does_not_land(run_store):
    """最后一个 job 的终态写已使 run 成为终态之后，处置的结束写返回 False：run 成为终态只发生一次。"""
    _create(run_store, ("a",))
    _claim(run_store, "a")
    assert run_store.commit_job_states("run-1", [_done("a", Status.ERROR)], ended_at=_ENDED) is CommitOutcome.ENDED_RUN
    assert run_store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="later") is False
    got = run_store.load_run_state("run-1")
    assert (got.status, got.ended_at, got.message, got.jobs["a"].message) == (Status.ERROR, _ENDED, None, None)


@pytest.mark.parametrize("job_states, match", [
    ([], "至少"),
    ([_done("a", Status.PASSED), _done("a", Status.FAILED)], "不止一次"),
    ([_done("a", Status.RUNNING)], "只记终态"),
    ([_done("a", Status.PENDING)], "只记终态"),
    ([_done("ghost", Status.PASSED)], "不在"),
])
def test_commit_rejects_bad_arguments_without_writing(run_store, job_states, match):
    """参数不合要求（空、scope_id 重复、不是终态、不在这个 run 里）抛 ValueError，运行态整份不变。"""
    _create(run_store, ("a", "b"))
    _claim(run_store, "a")
    before = run_store.load_run_state("run-1")

    with pytest.raises(ValueError, match=match):
        run_store.commit_job_states("run-1", job_states, ended_at=_ENDED)
    assert run_store.load_run_state("run-1") == before


def test_commit_without_a_record_raises_file_not_found(run_store):
    """run 的记录不存在时终态写抛 FileNotFoundError（须先 create_run），不建出记录。"""
    with pytest.raises(FileNotFoundError):
        run_store.commit_job_states("ghost", [_done("a", Status.PASSED)], ended_at=_ENDED)
    assert run_store.load_run_state("ghost") is None


# ---------- 终态写的字段合并 ----------

def _session_by_job_write(store):
    """另一方认领 a，再以执行中的写给它写下会话。"""
    _claim(store, "a", session="sess-new")


def _session_by_projection(store):
    """另一方认领 a，再由投影给它写下会话（投影不带认领时刻）。"""
    _claim(store, "a")
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=1, jobs={
        "a": JobState("a", Status.RUNNING, session_id="sess-new"), "b": JobState("b", Status.PENDING)})
    assert store.project_state("run-1", projected) is True


@pytest.mark.parametrize(("own_session", "kept_session"), [(None, "sess-new"), ("sess-result", "sess-result")],
                         ids=["no-session-given", "own-session-given"])
@pytest.mark.parametrize("other_write", [_session_by_job_write, _session_by_projection],
                         ids=["update_job_state", "project_state"])
def test_commit_merges_the_session_and_claim_time_written_after_the_caller_prepared_it(run_store, other_write,
                                                                                       own_session, kept_session):
    """调用方读到 a 仍 pending、按读到的条目准备好终态参数（没有认领时刻；会话为空，或是产出这个结果的那次执行的会话）之后，另一方
    认领 a（写下认领时刻）并写下会话；终态写之后 a 是给出的终态，认领时刻是另一方写下的。会话在参数没有会话时是另一方写下的、不被
    空值覆盖，参数带了会话时取参数的。"""
    _create(run_store, ("a", "b"), hwm=0)
    seen = run_store.load_run_state("run-1").jobs["a"]
    assert (seen.session_id, seen.claimed_at) == (None, None), "前提：参数按读到的 pending 条目准备"
    prepared = JobState("a", Status.PASSED, session_id=own_session, claimed_at=seen.claimed_at)
    other_write(run_store)  # 落在准备参数之后、终态写之前

    assert run_store.commit_job_states("run-1", [prepared], ended_at="never") is CommitOutcome.OPEN
    assert run_store.load_run_state("run-1").jobs["a"] == JobState(
        "a", Status.PASSED, session_id=kept_session, claimed_at=_CLAIMED)


def test_commit_takes_the_given_session_and_the_recorded_claim_time(run_store):
    """库中与给出的都有值时，会话取给出的（产出这个结果的那次执行的会话），认领时刻取库中的（认领写下的）；库中没有认领时刻时取给出的。
    给出的 job 级说明不写下。"""
    _create(run_store, ("a", "b", "c"))
    _claim(run_store, "a", session="sess-recorded")
    given_claim = "2026-11-19T00:09:00Z"

    assert run_store.commit_job_states("run-1", [
        JobState("a", Status.FAILED, session_id="sess-result", claimed_at=given_claim, message="给出的说明"),
        JobState("b", Status.ERROR, claimed_at=given_claim),
    ], ended_at="never") is CommitOutcome.OPEN

    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.FAILED, session_id="sess-result", claimed_at=_CLAIMED)
    assert got.jobs["b"] == JobState("b", Status.ERROR, claimed_at=given_claim)


# ---------- 终态只写一次：执行中的写不重开已结束的 job ----------

def test_a_late_running_write_does_not_reopen_a_committed_job(run_store):
    """run 未结束时，a 的终态记下之后，迟到的执行中写（running、另一个会话与认领时刻）返回 True（run 仍未结束），a 不变；此后再给 a 记
    终态同样不改动它；b 记下终态之后，run 按 a 的第一个终态与 b 的终态为 passed。"""
    _create(run_store, ("a", "b"))
    _claim(run_store, "a")
    _claim(run_store, "b")
    first = JobState("a", Status.PASSED, session_id="first", claimed_at=_CLAIMED)
    assert run_store.commit_job_states("run-1", [first], ended_at="never") is CommitOutcome.OPEN

    late = JobState("a", Status.RUNNING, session_id="late", claimed_at="2026-11-19T00:05:00Z")
    assert run_store.update_job_state("run-1", late) is True
    got = run_store.load_run_state("run-1")
    assert (got.jobs["a"], got.status) == (first, Status.RUNNING)

    second = JobState("a", Status.ERROR, session_id="second", claimed_at="2026-11-19T00:06:00Z")
    assert run_store.commit_job_states("run-1", [second], ended_at="never") is CommitOutcome.OPEN
    assert run_store.load_run_state("run-1").jobs["a"] == first

    assert run_store.commit_job_states("run-1", [_done("b", Status.PASSED)], ended_at=_ENDED) is CommitOutcome.ENDED_RUN
    got = run_store.load_run_state("run-1")
    assert (got.jobs["a"], got.status, got.ended_at) == (first, Status.PASSED, _ENDED)


@pytest.mark.parametrize("scope_id", ["a", "b", "ghost"], ids=["aborted", "skipped", "outside-the-run"])
def test_a_job_write_after_an_end_run_changes_nothing(run_store, scope_id):
    """run 由处置的结束写结束之后（a 记 aborted、b 记 skipped，各带说明），迟到的执行中写返回 False（run 已结束），运行态整份不变；
    写的是运行态里没有的 job 时同样如此（返回值只看 run）。"""
    _create(run_store, ("a", "b"))
    _claim(run_store, "a", session="sess-a")
    assert run_store.end_run("run-1", RUN_ENDINGS["settle-past-deadline"], ended_at=_ENDED) is True
    before = run_store.load_run_state("run-1")

    late = JobState(scope_id, Status.RUNNING, session_id="late", claimed_at=_CLAIMED)
    assert run_store.update_job_state("run-1", late) is False
    assert run_store.load_run_state("run-1") == before


@pytest.mark.parametrize("claimed", [False, True], ids=["run-pending", "run-running"])
def test_a_job_write_for_a_job_outside_the_run_writes_nothing(run_store, claimed):
    """执行中的写不臆造 job：运行态里没有的 scope 不写，运行态整份不变（运行定义以外的 running 项会让 run 永远到不了终态）；run 仍未
    结束，返回 True。"""
    _create(run_store, ("a", "b"))
    if claimed:
        _claim(run_store, "a")
    before = run_store.load_run_state("run-1")
    assert run_store.update_job_state("run-1", JobState("ghost", Status.RUNNING, session_id="s")) is True
    assert run_store.load_run_state("run-1") == before


# ---------- 终态只写一次：投影不改写终态写与结束写记下的终态 ----------

@pytest.mark.parametrize("hwm", [1, 2], ids=["same_hwm", "higher_hwm"])
def test_projection_does_not_rewrite_a_terminal_job_written_by_a_commit(run_store, hwm):
    """run 未结束时 a 的终态由终态写记下之后，投影把 a 算成另一个终态（同级、另一个会话），HWM 相同或更高也不改写它；同一次投影里
    执行中的 b 照常写下新的会话。"""
    _create(run_store, ("a", "b"), hwm=0)
    _claim(run_store, "a")
    _claim(run_store, "b")
    first = _done("a", Status.PASSED, session="first")
    assert run_store.commit_job_states("run-1", [first], ended_at="never") is CommitOutcome.OPEN
    seeded = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=1,
                      jobs={"a": JobState("a", Status.PASSED, session_id="first"), "b": JobState("b", Status.RUNNING)})
    assert run_store.project_state("run-1", seeded) is True

    later = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=hwm,
                     jobs={"a": JobState("a", Status.ERROR, session_id="other"),
                           "b": JobState("b", Status.RUNNING, session_id="sess-b")})
    assert run_store.project_state("run-1", later) is True
    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == first
    assert got.jobs["b"] == JobState("b", Status.RUNNING, session_id="sess-b", claimed_at=_CLAIMED)
    assert got.status == Status.RUNNING


def test_projection_does_not_rewrite_jobs_ended_by_an_end_run_landing_after_its_scalar_step(aws, monkeypatch):
    """云端的投影分两步：标量一步写成之后、逐 job 写发出之前，另一方以处置的结束写结束这个 run（a、b 都还是 running，记 aborted 并带
    说明）。余下的逐 job 写——把 a 写成终态、给 b 写新会话——都以 run 未结束、库中 job 未结束为条件，写不成；记录保持那次结束写的结果。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    table = aws["ddb"].Table(aws["table_name"])
    store, other = DynamoDBRunStore(table), DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))
    _create(store, ("a", "b"), hwm=0)
    _claim(store, "a", session="sess-a")
    _claim(store, "b", session="sess-b")
    real_update = table.update_item
    calls: list[dict] = []
    ended = None

    def update_item(**kwargs):
        nonlocal ended
        calls.append(kwargs)  # 记下发出的每一次写，被条件挡下的也算
        resp = real_update(**kwargs)
        if len(calls) == 1:  # 标量一步写成之后、逐 job 写发出之前
            assert other.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at=_ENDED) is True
            ended = other.load_run_state("run-1")
        return resp

    monkeypatch.setattr(table, "update_item", update_item)
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=5,
                         jobs={"a": JobState("a", Status.PASSED, session_id="sess-a"),
                               "b": JobState("b", Status.RUNNING, session_id="sess-new")})
    assert store.project_state("run-1", projected) is True
    assert len(calls) == 3, "前提：标量一步之后两个 job 各发了一次逐 job 写"
    got = store.load_run_state("run-1")
    assert ended is not None and got.jobs == ended.jobs
    ending = RUN_ENDINGS["settle-advancer-exited"]
    assert got.jobs["a"] == JobState("a", Status.ABORTED, session_id="sess-a", claimed_at=_CLAIMED,
                                     message=ending.aborted_message)
    assert got.jobs["b"] == JobState("b", Status.ABORTED, session_id="sess-b", claimed_at=_CLAIMED,
                                     message=ending.aborted_message)
    assert (got.status, got.message, got.ended_at) == (Status.ABORTED, ending.run_message, _ENDED)


# ---------- 没有记录的执行：内存里算出的运行态与记录相同 ----------

@pytest.mark.parametrize("route, first", [("deadline", Status.PASSED), ("fail-fast", Status.ERROR),
                                          ("interrupt", Status.ABORTED)])
def test_state_without_record_matches_the_record_written_by_the_two_entries(run_store, route, first):
    """同一组执行事实（a 判出结果，b、c 没有启动，余下的 job 不再启动的来源是 route）：有记录时经终态写与结束写写下的运行态，与没有
    记录时在内存里算出的相同（两边都没有开始时刻与认领写）。"""
    meta = _meta("run-1", ("a", "b", "c"))
    run_store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                        jobs={j.scope_id: JobState(j.scope_id, Status.PENDING) for j in meta.jobs}))
    assert run_store.commit_job_states("run-1", [JobState("a", first, session_id="s-a")],
                                       ended_at=_ENDED) is CommitOutcome.OPEN
    assert run_store.end_run("run-1", RUN_ENDINGS[route], ended_at=_ENDED) is True
    results = [JobResult(job=meta.jobs[0], status=first, session_id="s-a")]
    assert state_without_record(meta, results, route, ended_at=_ENDED) == run_store.load_run_state("run-1")


# ---------- job 级说明：别的写原样保留 ----------

def test_projection_and_claim_keep_the_job_message(run_store):
    """库中 job 带说明时，状态投影把它推进为 running、认领把 pending 的它置为 running，说明都原样保留。说明只由结束写写下，结束写又
    使 run 成为终态，这里借初始运行态造出 run 未结束而 job 带说明的记录。"""
    _create(run_store, ("a", "b"), hwm=0, messages={"a": "说明 a", "b": "说明 b"})
    projected = RunState(run_id="run-1", status=Status.RUNNING, high_water_mark=1,
                         jobs={"a": JobState("a", Status.RUNNING, session_id="sess-a"), "b": JobState("b", Status.PENDING)})
    assert run_store.project_state("run-1", projected) is True
    assert run_store.try_claim_job("run-1", "b", claimed_at=_CLAIMED) is True

    got = run_store.load_run_state("run-1")
    assert got.jobs["a"] == JobState("a", Status.RUNNING, session_id="sess-a", message="说明 a")
    assert got.jobs["b"] == JobState("b", Status.RUNNING, claimed_at=_CLAIMED, message="说明 b")
