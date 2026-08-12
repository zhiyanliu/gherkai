"""core.project 纯投影测试（ADR 0034）：project(records)→RunState 的「两件都要」谓词 + HWM + plan_next。

纯逻辑、无 I/O、无 mock 外真实行为 → 绿即够（CLAUDE.md「绿≠对·别过度」：mock 内逻辑结论绿即足）。
reconciler 的执行编排（Stream 触发/CAS 真写/进程脱离）不在此测——那是 P2/P3/P4 的真跑边界。
"""
from __future__ import annotations

from core.model import (
    Job,
    RunMeta,
    Scenario,
    ScenarioDone,
    ScopeDone,
    ScopeStarted,
    Status,
    Step,
)
from core.project import Action, EventRecord, TaskExited, plan_next, project


def _job(scope_id: str, engine: str = "novaact") -> Job:
    sc = Scenario(id=f"{scope_id}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),))
    return Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=(sc,))


def _meta(*scope_ids: str) -> RunMeta:
    return RunMeta(run_id="run-1", created_at="2026-07-19T00:00:00Z",
                   jobs=tuple(_job(s) for s in scope_ids))


def _ev(scope_id: str, seq: int, event, ts: float = 0.0) -> EventRecord:
    return EventRecord(scope_id=scope_id, kind="event", seq=seq, event=event, emit_ts=ts)


def _exit(scope_id: str, code: int | None) -> EventRecord:
    return EventRecord(scope_id=scope_id, kind="exit", exited=TaskExited(scope_id=scope_id, exit_code=code))


# 一个「跑完 passed」的完整 worker 事件序列（scope_started→scenario_done(passed)→scope_done）
def _passed_events(scope_id: str, base_seq: int = 1):
    scen = f"{scope_id}:1"
    return [
        _ev(scope_id, base_seq, ScopeStarted(scope_id=scope_id, session_id="sess-x")),
        _ev(scope_id, base_seq + 1, ScenarioDone(scenario_id=scen, status=Status.PASSED)),
        _ev(scope_id, base_seq + 2, ScopeDone(scope_id=scope_id)),
    ]


# ---------- 「两件都要」谓词（机制二）----------

def test_no_records_job_is_pending():
    """definition 里的 job 没有任何 record → PENDING（还没起）。"""
    state = project(_meta("a"), [])
    assert state.jobs["a"].status == Status.PENDING
    assert state.status == Status.PASSED  # 全 pending 被 _NON_VERDICT 过滤，run 级空判定=passed


def test_scope_started_but_no_exit_is_running():
    """见了 scope_started、有 scope_done，但没 task_exit → RUNNING（进程未确认终止，两件缺一）。"""
    recs = _passed_events("a")  # 含 scope_done，但无 exit 记录
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.RUNNING
    assert state.jobs["a"].session_id == "sess-x"  # 血缘随 scope_started 落


def test_scope_started_running_without_exit():
    """会话已起（scope_started）、进程还没终止（无 task_exited）→ RUNNING（在跑）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s"))]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.RUNNING


def test_clean_exit_without_scope_done_is_error():
    """干净退出（exit=0）却没发完 scope_done（内容不完整）→ ERROR（矛盾态，不死循环，P3b crash 修正）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _exit("a", 0)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_crash_no_scope_done_nonzero_exit_is_error():
    """worker 崩溃（吐 scope_started 后非0退出、没 scope_done）→ ERROR（不等 scope_done，P3b 真跑复现的死循环修正）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a", session_id="s")), _exit("a", 3)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_network_exit_before_scope_started_is_error():
    """建连失败（退出码 80、scope_started 都没发）→ ERROR（进程终止即终态，不卡 pending）。"""
    recs = [_exit("a", 80)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_two_things_present_clean_exit_terminal_passed():
    """两件都要齐（scope_done ∧ exit=0）→ 终态取 scenario 归约（passed）。"""
    recs = _passed_events("a") + [_exit("a", 0)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.PASSED
    assert state.status == Status.PASSED


def test_nonzero_exit_overrides_content_to_error():
    """关键（机制二）：scope_done 说 passed，但 exit_code!=0 → 判 ERROR（防"发完 scope_done 又非0退出"误报）。"""
    recs = _passed_events("a") + [_exit("a", 1)]  # 内容 passed，进程非干净退出
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR
    assert state.status == Status.ERROR


def test_sigkill_137_is_error():
    """SIGKILL 截断 exit=137 → ERROR（实测 payload 带 137，机制二）。"""
    recs = _passed_events("a") + [_exit("a", 137)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.ERROR


def test_exit_code_none_is_conservative_running():
    """exit_code=None（宽限态未落值）→ 保守判 RUNNING、不轻易落终态（机制二兜底）。"""
    recs = _passed_events("a") + [_exit("a", None)]
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.RUNNING


# ---------- HWM（机制三）----------

def test_hwm_is_max_worker_seq():
    """high_water_mark = 所有 scope 的 worker 段 max seq（exit 记录无 seq、不参与）。"""
    recs = _passed_events("a", base_seq=1) + [_exit("a", 0)]  # worker seq 1,2,3
    state = project(_meta("a"), recs)
    assert state.high_water_mark == 3


def test_hwm_across_scopes():
    """多 scope：HWM 取跨 scope 的全局 max。"""
    recs = _passed_events("a", base_seq=1) + _passed_events("b", base_seq=1)
    recs += [_exit("a", 0), _exit("b", 0)]
    meta = _meta("a", "b")
    state = project(meta, recs)
    assert state.high_water_mark == 3  # 各 scope 独立 seq，max=3


def test_out_of_order_records_reduced_by_seq():
    """乱序 records（全量重放抗乱序，机制三前提）：project 内按 seq 升序归约，结果与顺序无关。"""
    recs = list(reversed(_passed_events("a"))) + [_exit("a", 0)]  # 倒序喂
    state = project(_meta("a"), recs)
    assert state.jobs["a"].status == Status.PASSED  # 仍正确归约


# ---------- plan_next（机制四）----------

def test_plan_next_starts_up_to_concurrency():
    """全 pending、max_concurrency=2 → 提议 start 前 2 个。"""
    state = project(_meta("a", "b", "c"), [])
    actions = plan_next(state, max_concurrency=2)
    starts = [a.scope_id for a in actions if a.kind == "start"]
    assert len(starts) == 2


def test_plan_next_respects_running_slots():
    """已有 1 个 running、max_concurrency=2 → 只补 1 个 pending。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a"))]  # a 在 running（scope_started 无 scope_done/exit）
    state = project(_meta("a", "b", "c"), recs)
    assert state.jobs["a"].status == Status.RUNNING
    actions = plan_next(state, max_concurrency=2)
    starts = [a.scope_id for a in actions if a.kind == "start"]
    assert len(starts) == 1  # 2-1=1 slot
    assert "a" not in starts  # 不重启 running 的


def test_plan_next_finalize_when_all_terminal():
    """所有 job 达终态（无 pending/running）→ 提议 finalize。"""
    recs = _passed_events("a") + [_exit("a", 0)]
    state = project(_meta("a"), recs)
    actions = plan_next(state, max_concurrency=2)
    assert actions == [Action(kind="finalize")]


def test_plan_next_not_finalize_while_running():
    """有 running 时不 finalize（即使有别的 pending 也优先补并发、不收尾）。"""
    recs = [_ev("a", 1, ScopeStarted(scope_id="a"))]
    state = project(_meta("a", "b"), recs)
    actions = plan_next(state, max_concurrency=2)
    assert not any(a.kind == "finalize" for a in actions)


# ---- exit-without-events 真值表（ADR 0034 机制二：task_exited 判定不设 saw_scope_started 前置）----


def test_clean_exit_without_any_event_is_error():
    """零事件 + exit==0（构造期 SIGTERM 干净退出，0024 设计内）→ ERROR，不得判 PENDING。

    若判 PENDING：与已 claim 的 RUNNING 基线单调合并 → 永停 RUNNING → plan_next 空 → run 永不收敛
    （对抗验证探针复现的死循环）。ERROR（内容不完整但进程说成功=矛盾）比死循环安全。
    """
    meta = _meta("a")
    state = project(meta, [_exit("a", 0)])
    assert state.jobs["a"].status == Status.ERROR


def test_clean_exit_without_events_converges_with_claimed_baseline():
    """同上,带「已 claim RUNNING」基线也必须收敛到 ERROR(终态 rank > running,单调合并不回退)。"""
    from core.model import JobState, RunState

    meta = _meta("a")
    baseline = RunState(run_id="run-1", status=Status.RUNNING,
                        jobs={"a": JobState("a", Status.RUNNING)}, high_water_mark=0)
    state = project(meta, [_exit("a", 0)], baseline)
    assert state.jobs["a"].status == Status.ERROR


def test_exit_none_without_events_is_running_grace():
    """零事件 + exit=None（TaskFailedToStart 的 STOPPED 无 exitCode）→ RUNNING 宽限（等观察者补），非 PENDING。

    判 PENDING 会让 plan_next 重复提议 start（与已 claim 基线合并后则永停）——宽限 RUNNING 是机制二兜底语义。
    """
    meta = _meta("a")
    state = project(meta, [_exit("a", None)])
    assert state.jobs["a"].status == Status.RUNNING
