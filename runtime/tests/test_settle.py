"""run 处置（`gherkai_runtime.settle`，ADR 0054 决策六到八）。

判定只在 `settle_run` 一处，两个入口共用；它依赖的锁、改名与条件写都是 mock 之外的真实行为（绿≠对），所以断言都落在真实文件与真实
内核上：

- **真实进程**：推进器是一个用生产代码建 run、持锁到进程退出的子进程（`_CHILD` 的 advancer），存活、被暂停、被强杀各一种；两个处置方
  同时处置、处置与推进器最后一次终态写交错，都由真实子进程在同一个文件出现时同时开始。这类用例带 `real_filesystem` 标记（子进程里没有
  替换文件系统类型）。
- **同一进程里的真实锁**：锁按打开的文件描述计，同一进程另一次打开同样被挡，所以测试进程用 `lock_holder` 持着建 run 时的描述符即是
  「锁被持有」，关掉它即是「锁拿到了」。各种状态组合的表驱动用例这样布置，期望的 reason 与 outcome 照 ADR 0054 决策八手写。
- **替身只换边界上的原语**：锁不可用把 `fcntl.flock` 的非阻塞一次换成抛 ENOLCK；边界检查沿用 conftest 对 `run_dir.filesystem_type`
  的替换；run 目录在某一步之间被删、被改，由包在真实试拿外面的一层在那一步做真实的文件操作。
"""
from __future__ import annotations

import errno
import json
import os
import shutil
import signal
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from gherkai_core.adapters.run_store import run_dir
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.errors import UnsupportedDefinitionSchema
from gherkai_core.model import Job, JobState, RunMeta, Scenario, Status, Step
from gherkai_core.persist import initial_run_state
from gherkai_core.run_status import RUN_ENDINGS
from gherkai_core.serialize import instant_to_iso
from gherkai_runtime import compose, settle
from gherkai_runtime.settle import DefinitionRead, Outcome, Reason, ReportMissing

_TIMEOUT_S = 30
_NOW = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)
_FAR = _NOW + timedelta(days=1)            # 期限远在之后
_WITHIN = _NOW - timedelta(seconds=100)    # 已过期限、还没过期限加 300 秒
_PAST = _NOW - timedelta(seconds=301)      # 已过期限加 300 秒
_RID = "20261121T120000Z-a1b2c3"

# 结束写说明表里处置的两行（ADR 0031 决定三「结束写」小节），照 ADR 原文手写，句末加「（已记为已结束）」
_EXITED = {"run": "执行这个 run 的 gherkai 进程已退出（已记为已结束）",
           "skipped": "执行这个 run 的 gherkai 进程已退出，job 没有启动（已记为已结束）",
           "aborted": "执行这个 run 的 gherkai 进程已退出，job 没有结果（已记为已结束）"}
_OVERDUE = {"run": "已超过允许运行的时间（已记为已结束）",
            "skipped": "这个 run 已超过允许运行的时间，job 没有启动（已记为已结束）",
            "aborted": "这个 run 已超过允许运行的时间，job 没有结果（已记为已结束）"}
_RUN_MESSAGE = {Reason.ADVANCER_EXITED: _EXITED["run"], Reason.PAST_DEADLINE: _OVERDUE["run"]}


def _job(sid: str) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="midscene", timeout_s=300.0,
               scenarios=(Scenario(id=f"{sid}:1", name="sc", steps=(Step(0, "Given", "x"),)),))


def _make_run(root: Path, holder, run_id: str = _RID, *, deadline: datetime = _FAR, scopes=("a", "b"),
              claim=("a",)) -> LocalRunStore:
    """用生产的建 run 入口建一个 run，holder 收下持锁的描述符；claim 里的 job 认领成 running。"""
    meta = RunMeta(run_id=run_id, created_at=instant_to_iso(_NOW - timedelta(hours=2)),
                   jobs=tuple(_job(s) for s in scopes), deadline_at=instant_to_iso(deadline))
    store = LocalRunStore(root, lock_holder=holder)
    store.create_run(meta, initial_run_state(meta, started_at=meta.created_at))
    for sid in claim:
        assert store.try_claim_job(run_id, sid, claimed_at=meta.created_at) is True
    return store


def _state_bytes(root: Path, run_id: str = _RID) -> bytes:
    return (root / run_id / "run_state.json").read_bytes()


def _fixed_clock(*readings: datetime):
    """依次给出 readings 的墙钟；多读一次即失败。"""
    left = list(readings)

    def clock() -> datetime:
        assert left, "墙钟被多读了一次"
        return left.pop(0)

    return clock


class _Holder:
    """单独一个 run 的持有者：用例里要放开其中一个 run 的锁、其余照旧持有时用。"""

    def __init__(self) -> None:
        self.fds: list[int] = []

    def hold(self, fd: int) -> None:
        self.fds.append(fd)

    def close(self) -> None:
        while self.fds:
            os.close(self.fds.pop())


def _set_definition(root: Path, kind: str, run_id: str = _RID) -> None:
    """把这个 run 的提交记录改成 kind：missing 删去、malformed 写坏、bad_deadline 期限不是时刻、other_version 结构版本改成别的版本的。"""
    path = root / run_id / "run_meta.json"
    if kind == "missing":
        path.unlink()
    elif kind == "malformed":
        path.write_text("{写坏了", encoding="utf-8")
    elif kind in ("bad_deadline", "other_version"):
        d = json.loads(path.read_text(encoding="utf-8"))
        if kind == "bad_deadline":
            d["deadline_at"] = "快到了"
        else:
            d["schema_version"], d["cli_version"] = 99, "9.9.9"
        path.write_text(json.dumps(d), encoding="utf-8")
    else:
        assert kind == "readable", kind


def _lock_unavailable(monkeypatch) -> None:
    """不阻塞的取锁一律得到 ENOLCK（取锁出错、且不是「已被持有」）；运行态短锁的阻塞取锁照旧。"""
    import fcntl

    real = fcntl.flock

    def flock(fd, op):
        if op & fcntl.LOCK_NB:
            raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))
        return real(fd, op)

    monkeypatch.setattr(fcntl, "flock", flock)


# ---------- decide：锁与期限决定的五个 reason（纯函数，期望照 ADR 0054 决策八手写）----------

_EXACT = _NOW - timedelta(seconds=300)                     # now 恰是期限加 300 秒：还不算过
_JUST_PAST = _NOW - timedelta(seconds=300, microseconds=1)  # 晚一微秒：已过
_AHEAD = _NOW + timedelta(hours=1)
_A, _H, _U = run_dir.LockState.ACQUIRED, run_dir.LockState.HELD, run_dir.LockState.UNAVAILABLE


@pytest.mark.parametrize("lock, deadline, expected", [
    (_A, None, Reason.ADVANCER_EXITED), (_A, _AHEAD, Reason.ADVANCER_EXITED),
    (_A, _EXACT, Reason.ADVANCER_EXITED), (_A, _JUST_PAST, Reason.ADVANCER_EXITED),
    (_H, None, Reason.LOCK_HELD), (_H, _AHEAD, Reason.LOCK_HELD),
    (_H, _EXACT, Reason.LOCK_HELD), (_H, _JUST_PAST, Reason.PAST_DEADLINE),
    (_U, None, Reason.UNDETERMINED), (_U, _AHEAD, Reason.UNDETERMINED),
    (_U, _EXACT, Reason.UNDETERMINED), (_U, _JUST_PAST, Reason.PAST_DEADLINE),
    (None, None, Reason.UNDETERMINED), (None, _AHEAD, Reason.WITHIN_DEADLINE),
    (None, _EXACT, Reason.WITHIN_DEADLINE), (None, _JUST_PAST, Reason.PAST_DEADLINE),
])
def test_decide_takes_the_first_reason_that_holds(lock, deadline, expected):
    assert settle.decide(lock=lock, deadline=deadline, now=_NOW) is expected


# ---------- 各种状态组合（真实文件、同一进程里的真实锁）----------

_SETTLED, _WOULD, _SKIPPED = Outcome.SETTLED, Outcome.WOULD_SETTLE, Outcome.SKIPPED

# (编号, 运行态, 提交记录, 边界检查, 锁, 期限, dry_run, 期望的 outcome, 期望的 reason)
_COMBINATIONS = [
    ("exited", "running", "readable", "inside", "free", _FAR, False, _SETTLED, Reason.ADVANCER_EXITED),
    ("exited-and-overdue", "running", "readable", "inside", "free", _PAST, False, _SETTLED, Reason.ADVANCER_EXITED),
    ("exited-all-pending", "pending", "readable", "inside", "free", _FAR, False, _SETTLED, Reason.ADVANCER_EXITED),
    ("held", "running", "readable", "inside", "held", _FAR, False, _SKIPPED, Reason.LOCK_HELD),
    ("held-past-deadline-within-margin", "running", "readable", "inside", "held", _WITHIN, False, _SKIPPED,
     Reason.LOCK_HELD),
    ("held-overdue", "running", "readable", "inside", "held", _PAST, False, _SETTLED, Reason.PAST_DEADLINE),
    ("unavailable", "running", "readable", "inside", "unavailable", _FAR, False, _SKIPPED, Reason.UNDETERMINED),
    ("unavailable-overdue", "running", "readable", "inside", "unavailable", _PAST, False, _SETTLED,
     Reason.PAST_DEADLINE),
    ("exited-definition-missing", "running", "missing", "inside", "free", _PAST, False, _SETTLED,
     Reason.ADVANCER_EXITED),
    ("exited-definition-malformed", "running", "malformed", "inside", "free", _FAR, False, _SETTLED,
     Reason.ADVANCER_EXITED),
    ("held-definition-missing", "running", "missing", "inside", "held", _PAST, False, _SKIPPED, Reason.LOCK_HELD),
    ("held-definition-malformed", "running", "malformed", "inside", "held", _PAST, False, _SKIPPED, Reason.LOCK_HELD),
    ("unavailable-bad-deadline", "running", "bad_deadline", "inside", "unavailable", _PAST, False, _SKIPPED,
     Reason.UNDETERMINED),
    ("unavailable-definition-missing", "running", "missing", "inside", "unavailable", _PAST, False, _SKIPPED,
     Reason.UNDETERMINED),
    ("other-version", "running", "other_version", "inside", "free", _PAST, False, _SKIPPED, Reason.OTHER_VERSION),
    ("other-version-before-unreadable", "unreadable", "other_version", "inside", "free", _FAR, False, _SKIPPED,
     Reason.OTHER_VERSION),
    ("other-version-before-finished", "finished", "other_version", "inside", "free", _FAR, False, _SKIPPED,
     Reason.OTHER_VERSION),
    ("unreadable", "unreadable", "readable", "inside", "free", _PAST, False, _SKIPPED, Reason.UNREADABLE),
    ("unreadable-before-boundary", "unreadable", "readable", "outside", "free", _FAR, False, _SKIPPED,
     Reason.UNREADABLE),
    ("finished", "finished", "readable", "inside", "free", _FAR, False, _SKIPPED, Reason.ALREADY_FINISHED),
    ("finished-before-boundary", "finished", "readable", "outside", "held", _PAST, False, _SKIPPED,
     Reason.ALREADY_FINISHED),
    ("outside", "running", "readable", "outside", "free", _PAST, False, _SKIPPED, Reason.UNSUPPORTED_FILESYSTEM),
    ("unknown-filesystem", "running", "readable", "unknown", "free", _FAR, False, _SKIPPED,
     Reason.UNSUPPORTED_FILESYSTEM),
    ("dry-exited", "running", "readable", "inside", "free", _FAR, True, _WOULD, Reason.ADVANCER_EXITED),
    ("dry-held-overdue", "running", "readable", "inside", "held", _PAST, True, _WOULD, Reason.PAST_DEADLINE),
    ("dry-held", "running", "readable", "inside", "held", _FAR, True, _SKIPPED, Reason.LOCK_HELD),
]


@pytest.mark.parametrize("state, definition, boundary, lock, deadline, dry_run, outcome, reason",
                         [c[1:] for c in _COMBINATIONS], ids=[c[0] for c in _COMBINATIONS])
def test_each_combination_gets_its_reason_and_only_the_settled_ones_write(
        tmp_path, monkeypatch, lock_holder, state, definition, boundary, lock, deadline, dry_run, outcome, reason):
    """每种组合的 reason 与 outcome（ADR 0054 决策八「settle-runs」一条的次序）。只有 SETTLED 改记录：它的运行态按说明表写成终态、
    run 级说明对应它的 reason；其余的 run_state.json 逐字节不变，也不生成报告。提交记录读得出时期限记在结果里，读不出时为 None；写成
    的那一种提交记录读得出才有报告。"""
    root = tmp_path / "reports"
    store = _make_run(root, lock_holder, deadline=deadline, claim=() if state in ("pending", "finished") else ("a",))
    if state == "finished":
        assert store.end_run(_RID, RUN_ENDINGS["interrupt"], ended_at=instant_to_iso(_NOW)) is True
    elif state == "unreadable":
        (root / _RID / "run_state.json").write_text('{"run_id": ', encoding="utf-8")
    _set_definition(root, definition)
    if boundary == "outside":
        monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs4")
    elif boundary == "unknown":
        def unknown(fd):
            raise run_dir.FilesystemUnknown("挂载信息里找不到这个目录所在的挂载")
        monkeypatch.setattr(run_dir, "filesystem_type", unknown)
    if lock == "free":
        lock_holder.close_all()
    elif lock == "unavailable":
        lock_holder.close_all()
        _lock_unavailable(monkeypatch)
    before = _state_bytes(root)

    r = settle.settle_run(settle.local_target(root), _RID, clock=_fixed_clock(_NOW, _NOW + timedelta(seconds=1)),
                          dry_run=dry_run)

    assert (r.run_id, r.outcome, r.reason) == (_RID, outcome, reason)
    expected_read = {"readable": DefinitionRead.READABLE, "missing": DefinitionRead.MISSING,
                     "malformed": DefinitionRead.MALFORMED, "bad_deadline": DefinitionRead.MALFORMED,
                     "other_version": DefinitionRead.OTHER_VERSION}[definition]
    assert r.definition is expected_read
    assert r.deadline == (deadline if definition == "readable" else None)
    if outcome is not _SETTLED:
        assert _state_bytes(root) == before
        assert not (root / _RID / "index.html").exists() and r.report_written is None
        return
    after = LocalRunStore(root).load_run_state(_RID)
    assert after.status is Status.ABORTED and after.message == _RUN_MESSAGE[reason]
    assert after.ended_at == instant_to_iso(_NOW)  # 判定与结束时刻共用一个读数
    rows = _EXITED if reason is Reason.ADVANCER_EXITED else _OVERDUE
    for sid, js in after.jobs.items():
        kind = "skipped" if js.status is Status.SKIPPED else "aborted"
        assert js.message == rows[kind], sid
    assert r.report_written is (definition == "readable")
    assert (root / _RID / "index.html").exists() is (definition == "readable")
    if definition != "readable":
        assert r.report_missing.kind is ReportMissing.DEFINITION_UNREADABLE


def test_the_result_carries_what_the_decision_used(tmp_path, monkeypatch, lock_holder):
    """结果里带判定用到的结构化字段：别的版本写出时是读端的原异常（带两边的结构版本与写出它的版本），运行态读不出时是解析的原异常，
    文件系统不在清单里时是边界检查的结论与类型，锁不可用时是取锁的原错误。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder, run_id="20261121T120001Z-000001")
    _make_run(root, lock_holder, run_id="20261121T120002Z-000002")
    _make_run(root, lock_holder, run_id="20261121T120003Z-000003")
    _make_run(root, lock_holder, run_id="20261121T120004Z-000004")
    lock_holder.close_all()
    _set_definition(root, "other_version", "20261121T120001Z-000001")
    (root / "20261121T120002Z-000002" / "run_state.json").write_text("[]", encoding="utf-8")
    target = settle.local_target(root)

    other = settle.settle_run(target, "20261121T120001Z-000001", clock=_fixed_clock(), dry_run=False)
    assert isinstance(other.definition_error, UnsupportedDefinitionSchema)
    assert (other.definition_error.found, other.definition_error.supported, other.definition_error.cli_version) == (
        99, 2, "9.9.9")
    unreadable = settle.settle_run(target, "20261121T120002Z-000002", clock=_fixed_clock(), dry_run=False)
    assert unreadable.reason is Reason.UNREADABLE and unreadable.state_error is not None

    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs4")
    outside = settle.settle_run(target, "20261121T120003Z-000003", clock=_fixed_clock(), dry_run=False)
    assert outside.reason is Reason.UNSUPPORTED_FILESYSTEM
    assert (outside.boundary.verdict, outside.boundary.fs_type, outside.lock) == (run_dir.Boundary.OUTSIDE, "nfs4", None)

    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: run_dir.ALLOWED_FILESYSTEMS[sys.platform][0])
    _lock_unavailable(monkeypatch)
    unavailable = settle.settle_run(target, "20261121T120004Z-000004", clock=_fixed_clock(_NOW), dry_run=False)
    assert (unavailable.reason, unavailable.lock) == (Reason.UNDETERMINED, run_dir.LockState.UNAVAILABLE)
    assert unavailable.lock_error.errno == errno.ENOLCK


def test_without_a_lock_only_the_deadline_decides(tmp_path, lock_holder):
    """没有锁的处置目标（云端的形态，`run_dirs` 为 None）：不打开 run 目录、不试拿，只比期限。锁这时其实被持有：走了试拿就会是
    lock_held，这里给出的是 within_deadline；期限读不出即 undetermined；过了期限加 300 秒即按期限处置。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder, run_id="20261121T120001Z-000001", deadline=_FAR)
    _make_run(root, lock_holder, run_id="20261121T120002Z-000002", deadline=_FAR)
    _make_run(root, lock_holder, run_id="20261121T120003Z-000003", deadline=_PAST)
    _set_definition(root, "malformed", "20261121T120002Z-000002")
    target = replace(settle.local_target(root), run_dirs=None)

    def one(run_id):
        r = settle.settle_run(target, run_id, clock=_fixed_clock(_NOW, _NOW), dry_run=False)
        return r.outcome, r.reason, r.boundary, r.lock

    assert one("20261121T120001Z-000001") == (_SKIPPED, Reason.WITHIN_DEADLINE, None, None)
    assert one("20261121T120002Z-000002") == (_SKIPPED, Reason.UNDETERMINED, None, None)
    assert one("20261121T120003Z-000003") == (_SETTLED, Reason.PAST_DEADLINE, None, None)


# ---------- 这个名字下已没有 run：读运行态之后任一步遇到「不存在」（ADR 0054 决策八「处置的次序」）----------


class _InterposedDirs:
    """包在真实的本机 run 目录入口外面：试拿之前（before）或真实试拿已打开 run 目录之后（inside）对文件系统做一次真实的改动。"""

    def __init__(self, real, *, before=None, inside=None) -> None:
        self._real, self._before, self._inside = real, before, inside
        self.probed = 0

    @contextmanager
    def probe_run_dir(self, run_id):
        self.probed += 1
        if self._before:
            self._before()
        with self._real.probe_run_dir(run_id) as probe:
            if self._inside:
                self._inside()
            yield probe

    def staging_names(self):
        return self._real.staging_names()

    def sweep_staging_dir(self, name, *, dry_run):
        return self._real.sweep_staging_dir(name, dry_run=dry_run)


def _replace_with_file(path: Path) -> None:
    shutil.rmtree(path)
    path.write_text("不是目录", encoding="utf-8")


@pytest.mark.parametrize("when", ["before-probe", "after-probe", "replaced-by-a-file-after-probe"])
def test_a_run_dir_removed_after_the_state_was_read_is_gone(tmp_path, lock_holder, when):
    """run 目录在读运行态之后被删去（打开 run 目录时已不在；或打开之后、结束写之前被删去、被换成文件）：按这个名字下已没有 run 处理，
    抛 `RunGone`，结束写什么都没有建出（目录没有被重新建出，短锁的锁文件也没有）。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder)
    lock_holder.close_all()
    path = root / _RID
    hooks = {"before-probe": {"before": lambda: shutil.rmtree(path)},
             "after-probe": {"inside": lambda: shutil.rmtree(path)},
             "replaced-by-a-file-after-probe": {"inside": lambda: _replace_with_file(path)}}[when]
    target = settle.local_target(root)
    target = replace(target, run_dirs=_InterposedDirs(target.run_dirs, **hooks))

    with pytest.raises(settle.RunGone):
        settle.settle_run(target, _RID, clock=_fixed_clock(_NOW), dry_run=False)
    assert os.listdir(root) == ([] if when != "replaced-by-a-file-after-probe" else [_RID])
    assert not path.is_dir()


def test_a_run_dir_removed_in_the_middle_of_the_end_write_is_gone(tmp_path, monkeypatch, lock_holder):
    """run 目录在结束写的中途被删去（已在短锁内读到运行态、正要建出原子写的临时文件时）：写以「不存在」失败，按这个名字下已没有 run
    处理（`RunGone`），什么都没有建出。删除经建临时文件的那个系统原语之前的一次真实的删除做出。"""
    import tempfile

    root = tmp_path / "reports"
    _make_run(root, lock_holder)
    lock_holder.close_all()
    real_mkstemp = tempfile.mkstemp

    def mkstemp(*args, **kwargs):
        if Path(kwargs.get("dir", "")) == root / _RID:
            shutil.rmtree(root / _RID)
        return real_mkstemp(*args, **kwargs)

    monkeypatch.setattr(tempfile, "mkstemp", mkstemp)
    with pytest.raises(settle.RunGone):
        settle.settle_run(settle.local_target(root), _RID, clock=_fixed_clock(_NOW), dry_run=False)
    assert os.listdir(root) == []


@pytest.mark.parametrize("run_id", ["20261121T000000Z-000000", ".gherkai-creating-0123456789abcdef", "", "a/b"])
def test_a_name_that_is_not_a_run_is_gone(tmp_path, lock_holder, run_id):
    """没有这个 run、或名字不合 run 标识的规则（暂存目录的名字、空的、含路径分隔符的）都是 `RunGone`；暂存目录里即便有完整的两个
    文件也不认它，什么都不改。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder, run_id="20261121T120000Z-ffffff")
    lock_holder.close_all()
    staging = root / ".gherkai-creating-0123456789abcdef"
    shutil.copytree(root / "20261121T120000Z-ffffff", staging)
    before = sorted(p.relative_to(root) for p in root.rglob("*"))

    with pytest.raises(settle.RunGone):
        settle.settle_run(settle.local_target(root), run_id, clock=_fixed_clock(_NOW), dry_run=False)
    assert sorted(p.relative_to(root) for p in root.rglob("*")) == before


def test_a_state_damaged_between_the_read_and_the_end_write_is_unreadable(tmp_path, lock_holder):
    """读运行态时读得出、结束写在短锁内读到的已解析不了：记为 unreadable，带解析的原异常，文件保持损坏之后的字节、不被覆盖。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder)
    lock_holder.close_all()
    state_file = root / _RID / "run_state.json"
    target = settle.local_target(root)
    target = replace(target, run_dirs=_InterposedDirs(target.run_dirs,
                                                      inside=lambda: state_file.write_bytes(b'{"jobs": ')))

    r = settle.settle_run(target, _RID, clock=_fixed_clock(_NOW), dry_run=False)
    assert (r.outcome, r.reason, r.lock) == (_SKIPPED, Reason.UNREADABLE, run_dir.LockState.ACQUIRED)
    assert isinstance(r.state_error, ValueError)
    assert state_file.read_bytes() == b'{"jobs": '


def test_a_run_ended_elsewhere_between_the_read_and_the_end_write_is_already_finished(tmp_path, lock_holder):
    """读运行态之后、结束写之前另一方先结束了它：结束写写不成，重读到终态即 already_finished；记录是先写成的那一方的，这一方不生成
    报告。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder, claim=())
    lock_holder.close_all()
    target = settle.local_target(root)

    def end_elsewhere():
        assert LocalRunStore(root).end_run(_RID, RUN_ENDINGS["interrupt"], ended_at="elsewhere") is True

    target = replace(target, run_dirs=_InterposedDirs(target.run_dirs, inside=end_elsewhere))
    r = settle.settle_run(target, _RID, clock=_fixed_clock(_NOW), dry_run=False)
    assert (r.outcome, r.reason, r.report_written) == (_SKIPPED, Reason.ALREADY_FINISHED, None)
    state = LocalRunStore(root).load_run_state(_RID)
    assert (state.ended_at, state.message) == ("elsewhere", RUN_ENDINGS["interrupt"].run_message)
    assert not (root / _RID / "index.html").exists()


def test_finished_and_unreadable_runs_are_decided_without_opening_the_run_dir(tmp_path, lock_holder):
    """已结束、运行态读不出、提交记录由别的版本写出的 run 不打开 run 目录、不做边界检查、不试拿（ADR 0054 决策八「处置的次序」）。"""
    root = tmp_path / "reports"
    store = _make_run(root, lock_holder, run_id="20261121T120001Z-000001", claim=())
    assert store.end_run("20261121T120001Z-000001", RUN_ENDINGS["interrupt"], ended_at="t") is True
    _make_run(root, lock_holder, run_id="20261121T120002Z-000002")
    (root / "20261121T120002Z-000002" / "run_state.json").write_text("{", encoding="utf-8")
    _make_run(root, lock_holder, run_id="20261121T120003Z-000003")
    _set_definition(root, "other_version", "20261121T120003Z-000003")
    target = settle.local_target(root)
    dirs = _InterposedDirs(target.run_dirs)
    target = replace(target, run_dirs=dirs)

    reasons = [settle.settle_run(target, rid, clock=_fixed_clock(), dry_run=False).reason
               for rid in ("20261121T120001Z-000001", "20261121T120002Z-000002", "20261121T120003Z-000003")]
    assert reasons == [Reason.ALREADY_FINISHED, Reason.UNREADABLE, Reason.OTHER_VERSION]
    assert dirs.probed == 0


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 不受目录权限限制")
def test_a_run_dir_that_cannot_be_opened_is_a_record_access_failure(tmp_path, lock_holder):
    """run 目录打开得到「不存在」之外的失败（这里是没有读权限，运行态照样读得出）：原样抛出 OSError，不当作锁不可用、不按期限写，
    记录逐字节不变（ADR 0054 决策三「结果的判读」）。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder, deadline=_PAST)
    lock_holder.close_all()
    before = _state_bytes(root)
    os.chmod(root / _RID, 0o300)
    try:
        with pytest.raises(PermissionError):
            settle.settle_run(settle.local_target(root), _RID, clock=_fixed_clock(_NOW), dry_run=False)
    finally:
        os.chmod(root / _RID, 0o700)
    assert _state_bytes(root) == before


# ---------- 报告：写成之后按被处置的标识生成，失败隔离在处置之内（ADR 0054 决策七「报告」）----------


def test_the_report_is_written_while_the_lock_is_still_held_and_from_two_clock_readings(tmp_path, lock_holder):
    """锁持有到报告生成之后：写报告的那一刻，同一进程另开一次 run 目录试拿得到「已被持有」（处置方的那次打开还在）；处置返回之后即拿得到。
    墙钟读两次：结束时刻是第一次的读数，报告的生成时刻是第二次的。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder)
    lock_holder.close_all()
    target = settle.local_target(root)
    seen: list = []

    class _ProbingReports:
        def write(self, run_id, result, *, created_at):
            with run_dir.probe_run_dir(root / run_id) as probe:
                seen.append(probe.lock.state)
            return target.report_store.write(run_id, result, created_at=created_at)

    t1, t2 = _NOW, _NOW + timedelta(seconds=7)
    r = settle.settle_run(replace(target, report_store=_ProbingReports()), _RID, clock=_fixed_clock(t1, t2),
                          dry_run=False)
    assert (r.outcome, r.report_written) == (_SETTLED, True)
    assert seen == [run_dir.LockState.HELD]
    with run_dir.probe_run_dir(root / _RID) as probe:
        assert probe.lock.state is run_dir.LockState.ACQUIRED
    assert LocalRunStore(root).load_run_state(_RID).ended_at == instant_to_iso(t1)
    assert json.loads((root / _RID / "manifest.json").read_text(encoding="utf-8"))["created_at"] == instant_to_iso(t2)


def test_a_copied_run_dir_is_reported_under_its_own_name(tmp_path, lock_holder):
    """复制出来的 run 目录里提交记录的标识是原来那个：报告按被处置的那个标识（目录名）读写，原来那个 run 不受影响。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder, run_id="20261121T120000Z-000001")
    lock_holder.close_all()
    shutil.copytree(root / "20261121T120000Z-000001", root / "20261121T120000Z-000002")
    original = _state_bytes(root, "20261121T120000Z-000001")

    r = settle.settle_run(settle.local_target(root), "20261121T120000Z-000002", clock=_fixed_clock(_NOW, _NOW),
                          dry_run=False)
    assert (r.outcome, r.report_written) == (_SETTLED, True)
    manifest = json.loads((root / "20261121T120000Z-000002" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "20261121T120000Z-000002"
    assert _state_bytes(root, "20261121T120000Z-000001") == original
    assert not (root / "20261121T120000Z-000001" / "manifest.json").exists()


def test_a_report_that_cannot_be_written_is_a_fact_in_the_result_and_nothing_is_logged(tmp_path, lock_holder, capsys,
                                                                                     caplog):
    """写报告失败（manifest.json 的位置被一个目录占着，原子写的改名失败）：处置照样写成，结果里报告没有生成、类别是读写失败、带原
    异常；不记日志，标准错误上什么都没有（CLI 进程没有配置日志，记下的警告会连同回溯落到终端）。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder)
    lock_holder.close_all()
    (root / _RID / "manifest.json").mkdir()

    with caplog.at_level("DEBUG"):
        r = settle.settle_run(settle.local_target(root), _RID, clock=_fixed_clock(_NOW, _NOW), dry_run=False)
    assert (r.outcome, r.reason, r.report_written) == (_SETTLED, Reason.ADVANCER_EXITED, False)
    assert r.report_missing.kind is ReportMissing.ACCESS_FAILED and isinstance(r.report_missing.error, OSError)
    assert r.report_missing.detail
    assert LocalRunStore(root).load_run_state(_RID).status is Status.ABORTED
    assert not (root / _RID / "index.html").exists()
    assert caplog.records == [] and capsys.readouterr().err == ""


def test_a_definition_that_does_not_match_the_state_leaves_the_run_settled_without_a_report(tmp_path, lock_holder):
    """提交记录读得出、却列着运行态里没有的 job（记录被改动过）：处置照样写成，报告组装不出，类别是记录读不出、带原异常。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder)
    lock_holder.close_all()
    path = root / _RID / "run_meta.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d["jobs"].append({**d["jobs"][0], "scope_id": "c", "scope_name": "c"})
    path.write_text(json.dumps(d), encoding="utf-8")

    r = settle.settle_run(settle.local_target(root), _RID, clock=_fixed_clock(_NOW, _NOW), dry_run=False)
    assert (r.outcome, r.report_written, r.report_missing.kind) == (_SETTLED, False, ReportMissing.RECORD_UNREADABLE)
    assert isinstance(r.report_missing.error, ValueError)
    assert LocalRunStore(root).load_run_state(_RID).status is Status.ABORTED
    assert not (root / _RID / "index.html").exists()


def test_any_other_failure_while_writing_the_report_is_isolated_too(tmp_path, lock_holder):
    """写报告时抛出别的异常（报告存储这一边界上的替身抛 RuntimeError）：同样隔离在处置之内，类别是别的异常，处置照样写成。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder)
    lock_holder.close_all()

    class _Broken:
        def write(self, run_id, result, *, created_at):
            raise RuntimeError("报告模板坏了")

    target = replace(settle.local_target(root), report_store=_Broken())
    r = settle.settle_run(target, _RID, clock=_fixed_clock(_NOW, _NOW), dry_run=False)
    assert (r.outcome, r.report_written, r.report_missing.kind) == (_SETTLED, False, ReportMissing.OTHER)
    assert "报告模板坏了" in r.report_missing.detail
    assert LocalRunStore(root).load_run_state(_RID).status is Status.ABORTED


def test_a_named_detail_that_cannot_be_read_leaves_the_run_settled_without_a_report(tmp_path, lock_holder):
    """运行态点名了一份不在存放处的判定明细：处置写成，报告没有生成，类别是明细缺失，说明是读端给使用者的那一句。"""
    root = tmp_path / "reports"
    store = _make_run(root, lock_holder)
    store.commit_job_states(_RID, [JobState("a", Status.PASSED, result_id="0123456789abcdef")], ended_at="t")
    lock_holder.close_all()

    r = settle.settle_run(settle.local_target(root), _RID, clock=_fixed_clock(_NOW, _NOW), dry_run=False)
    assert (r.outcome, r.report_written, r.report_missing.kind) == (_SETTLED, False, ReportMissing.DETAIL_MISSING)
    assert r.report_missing.detail == str(r.report_missing.error)
    state = LocalRunStore(root).load_run_state(_RID)
    assert (state.jobs["a"].status, state.jobs["b"].status) == (Status.PASSED, Status.SKIPPED)


# ---------- 不给 run 标识时处理哪些 run ----------


def _batch_root(tmp_path, lock_holder) -> Path:
    """五个 run：持锁的、管它的进程已不在的、已结束的、运行态读不出的、提交记录由别的版本写出的。"""
    root = tmp_path / "reports"
    _make_run(root, lock_holder, run_id="20261121T120005Z-000005")
    gone = _Holder()
    _make_run(root, gone, run_id="20261121T120004Z-000004")
    gone.close()
    finished = _make_run(root, lock_holder, run_id="20261121T120003Z-000003", claim=())
    assert finished.end_run("20261121T120003Z-000003", RUN_ENDINGS["interrupt"], ended_at="t") is True
    _make_run(root, lock_holder, run_id="20261121T120002Z-000002")
    (root / "20261121T120002Z-000002" / "run_state.json").write_text("{", encoding="utf-8")
    _make_run(root, lock_holder, run_id="20261121T120001Z-000001")
    _set_definition(root, "other_version", "20261121T120001Z-000001")
    return root


def test_the_runs_to_settle_are_the_unfinished_and_unreadable_ones_in_descending_order(tmp_path, lock_holder):
    """要处置的是未结束与运行态读不出的 run（已结束的不在其中，提交记录由别的版本写出的也在其中、由处置给出 other_version），按 run
    标识降序；只列举、不处置，记录逐字节不变。"""
    root = _batch_root(tmp_path, lock_holder)
    before = {rid: _state_bytes(root, rid) for rid in os.listdir(root)}
    assert settle.unfinished_run_ids(settle.local_target(root)) == [
        "20261121T120005Z-000005", "20261121T120004Z-000004", "20261121T120002Z-000002", "20261121T120001Z-000001"]
    assert {rid: _state_bytes(root, rid) for rid in os.listdir(root)} == before


# ---------- 真实进程：推进器存活、被暂停、被强杀；两个处置方同时；处置与推进器的写交错 ----------

# 子进程只用 ASCII，参数经一个 JSON 串传入。advancer 用生产的建 run 入口建 run、持锁到进程退出，然后按标准输入里的每一行命令写；
# settler 经 `settle.local_target` 处置。带 go 的命令先回一行 waiting，等那个文件出现（再等 delay 秒）才动手，几个子进程由此同时开始
_CHILD = r"""
import json, pathlib, sys, time
a = json.loads(sys.argv[1])
if a["role"] == "advancer":
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.adapters.run_store.run_dir import HoldUntilExit
    from gherkai_core.model import Job, JobState, RunMeta, Scenario, Status, Step
    from gherkai_core.persist import initial_run_state
    store = LocalRunStore(a["root"], lock_holder=HoldUntilExit())
    for r in a["runs"]:
        jobs = tuple(Job(scope_id=s, scope_name=s, engine="midscene", timeout_s=300.0,
                         scenarios=(Scenario(id=s + ":1", name="sc", steps=(Step(0, "Given", "x"),)),)) for s in r["scopes"])
        meta = RunMeta(run_id=r["run_id"], created_at=a["at"], jobs=jobs, deadline_at=r["deadline_at"])
        store.create_run(meta, initial_run_state(meta, started_at=a["at"]))
        for sid in r["claim"]:
            assert store.try_claim_job(r["run_id"], sid, claimed_at=a["at"])
else:
    from gherkai_core.adapters.run_store import run_dir
    from gherkai_runtime import compose, settle
    target = settle.local_target(a["root"])
print("ready", flush=True)
for line in sys.stdin:
    c = json.loads(line)
    if "go" in c:
        print(json.dumps("waiting"), flush=True)
        go = pathlib.Path(c["go"])
        while not go.exists():
            time.sleep(0.0002)
        time.sleep(c.get("delay", 0))
    op, rid = c["op"], c["run_id"]
    if op == "claim":
        out = store.try_claim_job(rid, c["scope"], claimed_at=a["at"])
    elif op == "update":
        out = store.update_job_state(rid, JobState(c["scope"], Status.RUNNING, session_id="s"))
    elif op == "commit":
        out = store.commit_job_states(rid, [JobState(c["scope"], Status.PASSED)], ended_at=a["at"]).value
    elif op == "settle":
        try:
            r = settle.settle_run(target, rid, clock=compose.now, dry_run=c["dry_run"])
            out = [r.outcome.value, r.reason.value]
        except settle.RunGone:
            out = "gone"
    else:
        with run_dir.probe_run_dir(pathlib.Path(a["root"]) / rid) as p:
            out = p.lock.state.value
    print(json.dumps(out), flush=True)
"""


class _Child:
    def __init__(self, args: dict) -> None:
        self.proc = subprocess.Popen([sys.executable, "-c", _CHILD, json.dumps(args)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert self.reply() == "ready"

    def reply(self):
        line = self.proc.stdout.readline()
        if not line:
            self.proc.wait(timeout=_TIMEOUT_S)
            pytest.fail(f"子进程提前退出：{self.proc.stderr.read()}")
        return line.strip() if line.strip() == "ready" else json.loads(line)

    def send(self, **cmd) -> None:
        self.proc.stdin.write(json.dumps(cmd) + "\n")
        self.proc.stdin.flush()

    def ask(self, **cmd):
        self.send(**cmd)
        return self.reply()

    def kill(self) -> None:
        self.proc.kill()
        self.proc.wait(timeout=_TIMEOUT_S)


@pytest.fixture
def children():
    """起真实子进程的工厂；用例结束时还在的一律强杀并回收。"""
    started: list[_Child] = []

    def advancer(root: Path, runs: list[dict]) -> _Child:
        started.append(_Child({"role": "advancer", "root": str(root), "runs": runs,
                               "at": instant_to_iso(compose.now() - timedelta(hours=2))}))
        return started[-1]

    def settler(root: Path) -> _Child:
        started.append(_Child({"role": "settler", "root": str(root)}))
        return started[-1]

    yield advancer, settler
    for c in started:
        if c.proc.poll() is None:
            c.proc.kill()
        c.proc.wait(timeout=_TIMEOUT_S)
        for stream in (c.proc.stdin, c.proc.stdout, c.proc.stderr):
            stream.close()


def _run(run_id: str = _RID, *, deadline: datetime, scopes=("a", "b"), claim=("a",)) -> dict:
    return {"run_id": run_id, "deadline_at": instant_to_iso(deadline), "scopes": list(scopes), "claim": list(claim)}


def _together(tmp_path: Path, name: str, *pairs) -> list:
    """把 (子进程, 命令) 逐个发出，等它们都回了 waiting，再让同一个文件出现；返回各自的结果。"""
    go = tmp_path / f"go-{name}"
    for child, cmd in pairs:
        child.send(go=str(go), **cmd)
    for child, _cmd in pairs:
        assert child.reply() == "waiting"
    go.touch()
    return [child.reply() for child, _cmd in pairs]


@pytest.mark.real_filesystem
def test_a_live_or_paused_advancer_keeps_its_run_untouched(tmp_path, children):
    """推进器进程还在（含被 SIGSTOP 暂停）时锁被持有：期限未到即 lock_held，run_state.json 逐字节不变，run 目录里什么都没有多出来。"""
    advancer, _ = children
    root = tmp_path / "reports"
    adv = advancer(root, [_run(deadline=compose.now() + timedelta(days=1))])
    target = settle.local_target(root)
    before, names = _state_bytes(root), sorted(os.listdir(root / _RID))
    try:
        for pause in (False, True):
            if pause:
                adv.proc.send_signal(signal.SIGSTOP)
            r = settle.settle_run(target, _RID, clock=compose.now, dry_run=False)
            assert (r.outcome, r.reason, r.lock) == (_SKIPPED, Reason.LOCK_HELD, run_dir.LockState.HELD)
            assert _state_bytes(root) == before and sorted(os.listdir(root / _RID)) == names
    finally:
        adv.proc.send_signal(signal.SIGCONT)


@pytest.mark.real_filesystem
def test_a_killed_advancer_is_settled_once_and_the_lock_is_free_afterwards(tmp_path, children):
    """推进器被 SIGKILL 之后锁拿得到：记为已结束（锁拿到了那一行），执行中的 job 记 aborted、未启动的记 skipped，报告生成；再处置一次
    即 already_finished、记录不变；处置返回之后锁已放开。"""
    advancer, _ = children
    root = tmp_path / "reports"
    adv = advancer(root, [_run(deadline=compose.now() + timedelta(days=1))])
    adv.kill()
    target = settle.local_target(root)

    r = settle.settle_run(target, _RID, clock=compose.now, dry_run=False)
    assert (r.outcome, r.reason, r.lock, r.report_written) == (
        _SETTLED, Reason.ADVANCER_EXITED, run_dir.LockState.ACQUIRED, True)
    state = LocalRunStore(root).load_run_state(_RID)
    assert (state.status, state.message) == (Status.ABORTED, _EXITED["run"])
    assert (state.jobs["a"].status, state.jobs["a"].message) == (Status.ABORTED, _EXITED["aborted"])
    assert (state.jobs["b"].status, state.jobs["b"].message) == (Status.SKIPPED, _EXITED["skipped"])
    assert (root / _RID / "index.html").exists() and (root / _RID / "manifest.json").exists()

    after = _state_bytes(root)
    again = settle.settle_run(target, _RID, clock=compose.now, dry_run=False)
    assert (again.outcome, again.reason) == (_SKIPPED, Reason.ALREADY_FINISHED)
    assert _state_bytes(root) == after
    with run_dir.probe_run_dir(root / _RID) as probe:
        assert probe.lock.state is run_dir.LockState.ACQUIRED


@pytest.mark.real_filesystem
def test_a_dry_run_writes_nothing_and_another_process_gets_the_lock_at_once(tmp_path, children):
    """只看不写：给出 would_settle，run 目录里什么都没有改、没有多出来（运行态的短锁文件也没有建出）；返回之后另一个进程立即拿得到锁。"""
    advancer, settler = children
    root = tmp_path / "reports"
    adv = advancer(root, [_run(deadline=compose.now() + timedelta(days=1))])
    adv.kill()
    other = settler(root)
    before, names = _state_bytes(root), sorted(os.listdir(root / _RID))

    r = settle.settle_run(settle.local_target(root), _RID, clock=compose.now, dry_run=True)
    assert (r.outcome, r.reason, r.report_written) == (_WOULD, Reason.ADVANCER_EXITED, None)
    assert _state_bytes(root) == before and sorted(os.listdir(root / _RID)) == names
    assert other.ask(op="probe", run_id=_RID) == "acquired"


@pytest.mark.real_filesystem
def test_a_paused_advancer_past_the_overdue_time_is_settled_and_its_writes_fail_after_resuming(tmp_path, children):
    """推进器被暂停、已过期限加 300 秒：锁被持有，按期限那一行记为已结束；SIGCONT 之后它的认领、执行中的写与终态写都写不成，记录
    不变（ADR 0054 决策五）。"""
    advancer, _ = children
    root = tmp_path / "reports"
    adv = advancer(root, [_run(deadline=compose.now() - timedelta(hours=1))])
    adv.proc.send_signal(signal.SIGSTOP)
    try:
        r = settle.settle_run(settle.local_target(root), _RID, clock=compose.now, dry_run=False)
    finally:
        adv.proc.send_signal(signal.SIGCONT)
    assert (r.outcome, r.reason, r.lock, r.report_written) == (
        _SETTLED, Reason.PAST_DEADLINE, run_dir.LockState.HELD, True)
    state = LocalRunStore(root).load_run_state(_RID)
    assert (state.status, state.message) == (Status.ABORTED, _OVERDUE["run"])
    assert (state.jobs["a"].message, state.jobs["b"].message) == (_OVERDUE["aborted"], _OVERDUE["skipped"])

    after = _state_bytes(root)
    assert adv.ask(op="claim", run_id=_RID, scope="b") is False
    assert adv.ask(op="update", run_id=_RID, scope="a") is False
    assert adv.ask(op="commit", run_id=_RID, scope="a") == "already_ended"
    assert _state_bytes(root) == after


@pytest.mark.real_filesystem
@pytest.mark.parametrize("overdue", [False, True], ids=["within-deadline", "past-overdue"])
def test_two_settlers_at_once_write_once(tmp_path, children, overdue):
    """两个处置方在同一时刻开始处置同一个 run（推进器已被强杀），各做多轮：每轮恰好一方写成，另一方给出它那一刻的判定（期限未到时
    锁被另一方持有即 lock_held，或读到已结束）；run 级说明对应写成的那一方的 reason（两行都是真实情形，ADR 0054 决策八）。"""
    advancer, settler = children
    root = tmp_path / "reports"
    deadline = compose.now() + (timedelta(hours=-1) if overdue else timedelta(days=1))
    rounds = [f"20261121T1200{k:02d}Z-00000{k % 10}" for k in range(8)]
    adv = advancer(root, [_run(rid, deadline=deadline, scopes=("a",)) for rid in rounds])
    adv.kill()
    first, second = settler(root), settler(root)
    losers = {("skipped", "already_finished")} | (set() if overdue else {("skipped", "lock_held")})
    seen = set()
    for rid in rounds:
        out = [tuple(o) for o in _together(tmp_path, rid, (first, {"op": "settle", "run_id": rid, "dry_run": False}),
                                           (second, {"op": "settle", "run_id": rid, "dry_run": False}))]
        winners = [o for o in out if o[0] == "settled"]
        assert len(winners) == 1, out
        [loser] = [o for o in out if o[0] != "settled"]
        assert loser in losers, out
        seen.add(loser)
        assert winners[0][1] in ({"advancer_exited", "past_deadline"} if overdue else {"advancer_exited"}), out
        message = LocalRunStore(root).load_run_state(rid).message
        assert message == _RUN_MESSAGE[Reason(winners[0][1])], (out, message)
    if not overdue:
        assert ("skipped", "lock_held") in seen, "两个处置方没有一次真正交错：另一方从没有遇到被持有的锁"


@pytest.mark.real_filesystem
def test_a_settler_and_the_advancers_last_commit_write_once(tmp_path, children):
    """处置方（已过期限加 300 秒、锁被推进器持有）与推进器最后一个 job 的终态写同时开始，各做多轮：每轮恰好一方写成，记录与写成的
    那一方一致：终态写先成时 run 通过、处置方读到已结束；处置先成时 run 按期限那一行结束、终态写得到 run 已结束。终态写比处置的几步
    快，同时开始时多是它先成，所以后几轮让终态写晚一点开始，两种先后都要出现。"""
    advancer, settler = children
    root = tmp_path / "reports"
    delays = [0, 0, 0, 0.0002, 0.0005, 0.001, 0.05, 0.2]
    rounds = [f"20261121T1200{k:02d}Z-00000{k % 10}" for k in range(len(delays))]
    adv = advancer(root, [_run(rid, deadline=compose.now() - timedelta(hours=1), scopes=("a",)) for rid in rounds])
    other = settler(root)
    firsts = set()
    for rid, delay in zip(rounds, delays):
        commit, settled = _together(tmp_path, rid, (adv, {"op": "commit", "run_id": rid, "scope": "a", "delay": delay}),
                                    (other, {"op": "settle", "run_id": rid, "dry_run": False}))
        state = LocalRunStore(root).load_run_state(rid)
        if commit == "ended_run":
            assert settled == ["skipped", "already_finished"]
            assert (state.status, state.message) == (Status.PASSED, None)
            firsts.add("commit")
        else:
            assert (commit, settled) == ("already_ended", ["settled", "past_deadline"])
            assert (state.status, state.message) == (Status.ABORTED, _OVERDUE["run"])
            firsts.add("settle")
    assert firsts == {"commit", "settle"}, firsts
