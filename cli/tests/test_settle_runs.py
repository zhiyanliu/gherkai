"""run 处置的两个入口在命令行一侧的测试：`settle-runs`（含清理暂存目录）与等待中的 `status --wait`（ADR 0054 决策六到八，退出码见
ADR 0031 决定五）。判定与动作在 runtime 的 settle 模块，它自己的用例在 runtime/tests；这里核的是两个入口怎样调用它、中断在哪些
检查点被看到、输出、说明的整句与退出码。

证据边界：run 目录、生命期锁、运行态与报告都是真实的文件与真实的 `flock`（`LocalRunStore` 建 run，持有者是测试里能放开的那一种，
放开即等于管它的进程已退出；同一进程另一次打开同样被挡，所以测试进程里持着的锁对处置方就是「已被持有」）。文件系统类型经 conftest 的
替身取本平台清单的第一项，只在要拒绝的用例里换成清单之外的类型；带 `real_filesystem` 标记、起真实子进程的用例取宿主真实的类型。
故障注入只换边界上的原语（`fcntl.flock`、文件权限、`signal.raise_signal` 落在真实的写里、输出）。真实进程的用例核信号、进程退出与
锁的释放：两种推进器被 SIGKILL 之后等待中的 `status --wait` 下一次轮询即处置，`settle-runs` 在处置期间与开始输出之前收到的真实
SIGINT 只被记下，这次处置与输出照常做完，启动时 SIGINT 已被忽略的 `status --wait` 收到 SIGINT 接着等待。标准输出写不进时收到的
信号见 `test_output_under_interrupts`。
"""
from __future__ import annotations

import builtins
import errno
import json
import os
import shlex
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import gherkai_cli.__main__ as m
from gherkai_core.adapters.run_store import run_dir
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.run_status import run_status_of
from gherkai_core.serialize import DEFINITION_SCHEMA_VERSION, instant_to_iso
from gherkai_runtime import compose, handoff

FUTURE = datetime(2100, 1, 1, tzinfo=timezone.utc)
PAST = datetime(2001, 1, 1, tzinfo=timezone.utc)
NOT_YET = "还没有到可以记为已结束的时刻（允许运行的时间之后再过 5 分钟）"
HELD_BY_SOMEONE = "执行它的 gherkai 进程还在，或另一个 gherkai 命令正在处理它"
UNREADABLE_REMEDY = "settle-runs 与 status --wait 不改动这个 run 的记录，确认不需要之后可以手工移走这个 run 目录"
STAGING_HEADER = "暂存目录（建立 run 时中断留下的）"


class Holder:
    """测试用的锁持有者：收下建 run 交来的描述符，`release` 关掉它——锁随之放开，等于管这个 run 的进程已退出。"""

    def __init__(self) -> None:
        self.fds: list[int] = []

    def hold(self, fd: int) -> None:
        self.fds.append(fd)

    def release(self) -> None:
        while self.fds:
            os.close(self.fds.pop())


@pytest.fixture
def holders():
    made: list[Holder] = []
    yield made
    for h in made:
        h.release()


def _jobs(n: int) -> tuple[Job, ...]:
    return tuple(Job(scope_id=f"f.feature:{i}", scope_name=f"s{i}", engine="novaact", timeout_s=300.0,
                     scenarios=(Scenario(id=f"f.feature:{i}", name=f"s{i}", steps=(Step(index=0, keyword="Given", text="x"),)),))
                 for i in range(n))


def _create(root: Path, run_id: str, holders: list, *, deadline: datetime = FUTURE,
            statuses=(Status.RUNNING, Status.PENDING)) -> Holder:
    """用真实的 LocalRunStore 建一个 run（暂存、取锁、改名），把锁交给返回的持有者；运行态的 job 状态取 statuses（running 的带认领时刻）。"""
    holder = Holder()
    holders.append(holder)
    jobs = _jobs(len(statuses))
    meta = RunMeta(run_id=run_id, created_at="2030-01-01T00:00:00+00:00", jobs=jobs, deadline_at=instant_to_iso(deadline))
    run_status = run_status_of(statuses)  # run 的状态只由 job 的状态算出（与写入口同一处取法）
    state = RunState(run_id=run_id, status=run_status, started_at="2030-01-01T00:00:00+00:00",
                     jobs={j.scope_id: JobState(j.scope_id, s, claimed_at="2030-01-01T00:00:01+00:00" if s is Status.RUNNING else None)
                           for j, s in zip(jobs, statuses)})
    LocalRunStore(root, lock_holder=holder).create_run(meta, state)
    return holder


def _bytes(root: Path, run_id: str) -> dict[str, bytes]:
    d = root / run_id
    return {name: (d / name).read_bytes() for name in sorted(os.listdir(d)) if (d / name).is_file()}


def _state(root: Path, run_id: str) -> RunState:
    return LocalRunStore(root).load_run_state(run_id)


def _row(out: str, key: str) -> list[str]:
    """人读表格里含 key 的那一行的各格（去掉框线与两侧空白）。"""
    line = next(ln for ln in out.splitlines() if key in ln)
    return [c.strip() for c in line.split("│")[1:-1]]


def _lock_state(path: Path) -> run_dir.LockState:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        return run_dir.try_lock(fd).state
    finally:
        os.close(fd)


def _staging(root: Path, tail: str) -> Path:
    path = root / f"{run_dir.STAGING_PREFIX}{tail}"
    path.mkdir(parents=True)
    return path


def _hold_dir(path: Path) -> int:
    """在 path 上另开一次、取排他锁并一直开着（像正在建 run 的一方或另一个清理方那样持有它）；返回描述符，由调用方关闭。"""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    assert run_dir.try_lock(fd).state is run_dir.LockState.ACQUIRED
    return fd


def _settle(capsys, *argv) -> tuple[int, str, str]:
    rc = m.main(["settle-runs", *argv])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def _run_endings(root: Path, run_id: str) -> tuple:
    st = _state(root, run_id)
    return st.status, st.message, sorted((js.scope_id, js.status, js.message) for js in st.jobs.values())


# ---- settle-runs：每一种 reason 的人读与机读输出、退出码 ----

def test_settle_runs_lists_every_local_reason_in_the_table_and_in_json(tmp_path, capsys, holders, monkeypatch):
    """一个报告目录里：执行它的进程已退出的、还在的、被暂停且已过期限加 300 秒的、运行态损坏的、提交记录由别的版本写出的、run 目录在
    清单之外的文件系统上的，另有两个暂存目录（一个没人持有、一个被持有）。人读表格与 --json 的每一项、退出码 0；被处置的两个按说明表
    结束（末尾加「（已记为已结束）」）并生成了报告，跳过的记录字节不变；暂存目录一个删去、一个留下。"""
    root = tmp_path / "reports"
    exited, alive, paused, broken, other, nfs = (f"2030010{i}T000000Z-aaaaaa" for i in range(6, 0, -1))
    _create(root, exited, holders).release()
    _create(root, alive, holders)
    _create(root, paused, holders, deadline=PAST)
    _create(root, broken, holders).release()
    (root / broken / "run_state.json").write_text("{broken", encoding="utf-8")
    _create(root, other, holders).release()
    meta = json.loads((root / other / "run_meta.json").read_text(encoding="utf-8"))
    meta.update(schema_version=DEFINITION_SCHEMA_VERSION + 1, cli_version="9.9.0")
    (root / other / "run_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    _create(root, nfs, holders).release()
    nfs_ino = os.stat(root / nfs).st_ino
    allowed = run_dir.ALLOWED_FILESYSTEMS[sys.platform][0]
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs" if os.fstat(fd).st_ino == nfs_ino else allowed)
    leftover = _staging(root, "0123456789abcdef")
    busy = _staging(root, "fedcba9876543210")
    busy_fd = _hold_dir(busy)
    try:
        before = {rid: _bytes(root, rid) for rid in (alive, broken, other, nfs)}
        try:
            json.loads("{broken")
        except ValueError as e:
            broken_error = str(e)

        rc, out, err = _settle(capsys, "--report-dir", str(root))
        assert (rc, err) == (0, "")
        assert _row(out, exited) == [exited, "已记为已结束", "执行它的 gherkai 进程已退出"]
        assert _row(out, alive) == [alive, "跳过", f"{HELD_BY_SOMEONE}；{NOT_YET}"]
        assert _row(out, paused) == [paused, "已记为已结束", "已超过允许运行的时间"]
        assert _row(out, broken) == [broken, "跳过", f"运行状态记录读不出（{broken_error}）：{UNREADABLE_REMEDY}"]
        assert _row(out, other) == [other, "跳过", f"提交记录由 gherkai 9.9.0 写出（记录是第 {DEFINITION_SCHEMA_VERSION + 1} 版，"
                                                   f"本版本只认第 {DEFINITION_SCHEMA_VERSION} 版）：本版本不处理它，请用写出它的版本处理"]
        assert _row(out, nfs) == [nfs, "跳过", "run 目录所在的文件系统是 nfs，本机后端不支持，无法确认执行它的进程是否还在"]
        assert _row(out, STAGING_HEADER) == [STAGING_HEADER, "处置", "原因"]
        assert _row(out, leftover.name) == [leftover.name, "已删除", "-"]
        assert _row(out, busy.name) == [busy.name, "跳过", "另一个 gherkai 进程正在使用它（正在建立 run，或另一个 settle-runs 正在处理）"]
        # run 表按 run_id 降序（列举次序）
        assert [_row(ln, "aaaaaa")[0] for ln in out.splitlines() if "aaaaaa" in ln] == [exited, alive, paused, broken, other, nfs]

        exited_rows = [("f.feature:0", Status.ABORTED, "执行这个 run 的 gherkai 进程已退出，job 没有结果（已记为已结束）"),
                       ("f.feature:1", Status.SKIPPED, "执行这个 run 的 gherkai 进程已退出，job 没有启动（已记为已结束）")]
        assert _run_endings(root, exited) == (Status.ABORTED, "执行这个 run 的 gherkai 进程已退出（已记为已结束）", exited_rows)
        assert _run_endings(root, paused) == (
            Status.ABORTED, "已超过允许运行的时间（已记为已结束）",
            [("f.feature:0", Status.ABORTED, "这个 run 已超过允许运行的时间，job 没有结果（已记为已结束）"),
             ("f.feature:1", Status.SKIPPED, "这个 run 已超过允许运行的时间，job 没有启动（已记为已结束）")])
        assert (root / exited / "index.html").is_file() and (root / paused / "index.html").is_file()
        assert {rid: _bytes(root, rid) for rid in before} == before
        assert not leftover.exists() and busy.is_dir()
        assert _lock_state(root / alive) is run_dir.LockState.HELD  # 跳过的那一个：处置方没有留着锁，持有者照旧

        # 同一个报告目录再执行一次 --json：已处置的两个不再出现（不再是未结束的 run），跳过的照旧跳过
        rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
        assert (rc, err) == (0, "")
        doc = json.loads(out)
        assert doc == {
            "backend": "local", "report_dir": str(root.resolve()), "dry_run": False,
            "runs": [{"run_id": alive, "outcome": "skipped", "reason": "lock_held"},
                     {"run_id": broken, "outcome": "skipped", "reason": "unreadable"},
                     {"run_id": other, "outcome": "skipped", "reason": "other_version"},
                     {"run_id": nfs, "outcome": "skipped", "reason": "unsupported_filesystem"}],
            "staging_dirs": [{"name": busy.name, "outcome": "skipped", "reason": "held"}]}
    finally:
        os.close(busy_fd)


def test_settle_runs_json_reports_settled_runs_with_report_written(tmp_path, capsys, holders):
    """--json 的 settled 项带 report_written：生成了报告为 true；提交记录不存在的 run 只凭锁处置、没有报告，为 false，原因作为诊断写在
    标准错误（不打回溯）。人读输出在「处置」一栏说明，见下一条。"""
    root = tmp_path / "reports"
    _create(root, "20300102T000000Z-aaaaaa", holders).release()
    _create(root, "20300101T000000Z-aaaaaa", holders).release()
    (root / "20300101T000000Z-aaaaaa" / "run_meta.json").unlink()
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json", "--dry-run")
    assert rc == 0 and [r["outcome"] for r in json.loads(out)["runs"]] == ["would_settle", "would_settle"]
    assert all("report_written" not in r for r in json.loads(out)["runs"])  # 只看不写的结果不带这个键
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert rc == 0 and err.splitlines() == [
        "本命令已把 run 20300101T000000Z-aaaaaa 记为已结束，报告没有生成：这个 run 的提交记录不存在，报告要按提交记录列出各个 job。"]
    assert json.loads(out)["runs"] == [
        {"run_id": "20300102T000000Z-aaaaaa", "outcome": "settled", "reason": "advancer_exited", "report_written": True},
        {"run_id": "20300101T000000Z-aaaaaa", "outcome": "settled", "reason": "advancer_exited", "report_written": False}]
    assert (root / "20300102T000000Z-aaaaaa" / "index.html").is_file()
    assert not (root / "20300101T000000Z-aaaaaa" / "index.html").exists()
    assert _state(root, "20300101T000000Z-aaaaaa").status is Status.ABORTED


def test_settle_runs_without_a_report_says_so_in_the_outcome_column(tmp_path, capsys, holders):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    (root / run_id / "run_meta.json").unlink()
    rc, out, err = _settle(capsys, run_id, "--report-dir", str(root))
    assert (rc, err) == (0, "")
    assert _row(out, run_id) == [run_id, "已记为已结束，报告没有生成：这个 run 的提交记录不存在，报告要按提交记录列出各个 job",
                                 "执行它的 gherkai 进程已退出"]


def test_settle_runs_dry_run_changes_nothing_and_releases_what_it_tried(tmp_path, capsys, holders):
    """--dry-run 只判断、不写：会被处置的给 would_settle，记录字节不变、没有报告，拿到的锁随即放开（另开一次即拿得到）；会删除的暂存目录
    给 would_remove、仍在。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    leftover = _staging(root, "0123456789abcdef")
    before = _bytes(root, run_id)
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--dry-run")
    assert (rc, err) == (0, "")
    assert _row(out, run_id) == [run_id, "会记为已结束（--dry-run，没有改动）", "执行它的 gherkai 进程已退出"]
    assert _row(out, leftover.name) == [leftover.name, "会删除（--dry-run，没有改动）", "-"]
    assert _bytes(root, run_id) == before and leftover.is_dir()
    assert _lock_state(root / run_id) is run_dir.LockState.ACQUIRED and _lock_state(leftover) is run_dir.LockState.ACQUIRED
    rc, out, _ = _settle(capsys, "--report-dir", str(root), "--dry-run", "--json")
    assert json.loads(out)["staging_dirs"] == [{"name": leftover.name, "outcome": "would_remove", "reason": None}]


def test_settle_runs_names_a_lock_that_cannot_be_taken(tmp_path, capsys, holders, monkeypatch):
    """试拿锁出错且不是「已被持有」（这里把不阻塞的 flock 换成得到 ENOLCK 的替身，阻塞的短锁照常）：期限没到即 undetermined，说明里带
    原错误；暂存目录记 lock_unavailable。已过期限加 300 秒的照常按期限处置。"""
    import fcntl

    real_flock = fcntl.flock

    def flock(fd, op):
        if op & fcntl.LOCK_NB:
            raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))
        return real_flock(fd, op)

    root = tmp_path / "reports"
    _create(root, "20300102T000000Z-aaaaaa", holders)
    _create(root, "20300101T000000Z-aaaaaa", holders, deadline=PAST)
    leftover = _staging(root, "0123456789abcdef")
    monkeypatch.setattr(fcntl, "flock", flock)
    rc, out, err = _settle(capsys, "--report-dir", str(root))
    assert (rc, err) == (0, "")
    assert _row(out, "20300102T000000Z-aaaaaa") == [
        "20300102T000000Z-aaaaaa", "跳过",
        f"无法确认执行它的进程是否还在（在 run 目录上加锁失败：{os.strerror(errno.ENOLCK)}），也{NOT_YET}"]
    assert _row(out, "20300101T000000Z-aaaaaa") == ["20300101T000000Z-aaaaaa", "已记为已结束", "已超过允许运行的时间"]
    assert _row(out, leftover.name) == [leftover.name, "跳过", f"加锁失败：{os.strerror(errno.ENOLCK)}"]
    assert leftover.is_dir()
    rc, out, _ = _settle(capsys, "--report-dir", str(root), "--json")
    doc = json.loads(out)
    assert doc["runs"] == [{"run_id": "20300102T000000Z-aaaaaa", "outcome": "skipped", "reason": "undetermined"}]
    assert doc["staging_dirs"] == [{"name": leftover.name, "outcome": "skipped", "reason": "lock_unavailable"}]


def test_settle_runs_lock_held_without_a_readable_definition(tmp_path, capsys, holders):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders)
    (root / run_id / "run_meta.json").write_text("{", encoding="utf-8")
    rc, out, _ = _settle(capsys, run_id, "--report-dir", str(root))
    assert rc == 0
    assert _row(out, run_id) == [run_id, "跳过", f"{HELD_BY_SOMEONE}；提交记录不完整或形态不对，不知道它允许运行到什么时候"]


def test_settle_runs_leaves_out_a_run_removed_after_listing_and_goes_on(tmp_path, capsys, holders, monkeypatch):
    """列举之后、处置之前被删去的 run 略过：不出现在结果里，也不中止其余的处理（其余的照常处置，暂存目录照常清理），退出码 0。"""
    import shutil

    from gherkai_runtime import settle

    root = tmp_path / "reports"
    first, removed, last = "20300103T000000Z-aaaaaa", "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    for rid in (first, removed, last):
        _create(root, rid, holders).release()
    leftover = _staging(root, "0123456789abcdef")
    real_listing = settle.unfinished_run_ids

    def listing_then_remove(target):
        ids = real_listing(target)
        shutil.rmtree(root / removed)
        return ids

    monkeypatch.setattr(settle, "unfinished_run_ids", listing_then_remove)
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert (rc, err) == (0, "")
    assert json.loads(out)["runs"] == [
        {"run_id": first, "outcome": "settled", "reason": "advancer_exited", "report_written": True},
        {"run_id": last, "outcome": "settled", "reason": "advancer_exited", "report_written": True}]
    assert json.loads(out)["staging_dirs"] == [{"name": leftover.name, "outcome": "removed", "reason": None}]
    assert not (root / removed).exists() and not leftover.exists()


def test_settle_runs_cleans_only_staging_directories_in_name_order(tmp_path, capsys, holders):
    """清理只认暂存目录：按名字升序逐个处理；以暂存目录的形态命名的文件、以前缀起名而形态不符的目录不出现在结果里、原样留着，run 目录
    不当作暂存目录。只看不删的一次给出「会删除」、什么都不删，随后真删的一次照样拿得到锁、删去。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders, statuses=(Status.PASSED,)).release()
    later = _staging(root, "fedcba9876543210")
    earlier = _staging(root, "0123456789abcdef")
    (root / f"{run_dir.STAGING_PREFIX}{'1' * 16}").write_text("x", encoding="utf-8")
    user_named = _staging(root, "user-named")
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--dry-run", "--json")
    assert (rc, err) == (0, "")
    assert json.loads(out)["staging_dirs"] == [{"name": earlier.name, "outcome": "would_remove", "reason": None},
                                               {"name": later.name, "outcome": "would_remove", "reason": None}]
    assert earlier.is_dir() and later.is_dir()
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert (rc, err) == (0, "")
    assert json.loads(out)["staging_dirs"] == [{"name": earlier.name, "outcome": "removed", "reason": None},
                                               {"name": later.name, "outcome": "removed", "reason": None}]
    assert sorted(os.listdir(root)) == sorted([run_id, f"{run_dir.STAGING_PREFIX}{'1' * 16}", user_named.name])
    assert (root / f"{run_dir.STAGING_PREFIX}{'1' * 16}").read_text(encoding="utf-8") == "x" and user_named.is_dir()


def test_settle_runs_given_a_finished_run_skips_it_as_already_finished(tmp_path, capsys, holders):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders, statuses=(Status.PASSED,)).release()
    before = _bytes(root, run_id)
    rc, out, _ = _settle(capsys, run_id, "--report-dir", str(root), "--json")
    assert rc == 0 and json.loads(out) == {"backend": "local", "report_dir": str(root.resolve()), "dry_run": False,
                                           "runs": [{"run_id": run_id, "outcome": "skipped", "reason": "already_finished"}]}
    rc, out, _ = _settle(capsys, run_id, "--report-dir", str(root))
    assert _row(out, run_id) == [run_id, "跳过", "已结束"] and STAGING_HEADER not in out  # 给了标识不清理暂存目录
    assert _bytes(root, run_id) == before




@pytest.mark.parametrize("entry", ["settle-runs", "status-wait", "status-wait-json"])
def test_a_report_that_cannot_be_written_is_said_once_without_a_traceback(entry, tmp_path, capsys, holders):
    """处置写成之后报告写不进（报告的落点被一个目录占着）：处置照样算写成，两个入口都说明已记为已结束、报告没有生成及原因，不打回溯，
    status --wait 不给报告那一行；status --wait --json 照常给出 JSON 文档，报告没有生成及其原因是诊断、写到标准错误；--json 的
    report_written 为 false。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    (root / run_id / "manifest.json").mkdir()
    head = "已记为已结束，报告没有生成：读写这个 run 的记录或报告失败："
    if entry == "settle-runs":
        rc, out, err = _settle(capsys, "--report-dir", str(root))
        assert (rc, err) == (0, "")
        outcome = _row(out, run_id)[1]
        assert outcome.startswith(head) and "manifest.json" in outcome
    elif entry == "status-wait-json":
        rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait", "--json")
        assert rc == 1 and json.loads(out)["status"] == "aborted" and "Traceback" not in err
        [line] = err.splitlines()
        assert line.startswith(f"本命令已把 run {run_id} 记为已结束，报告没有生成：读写这个 run 的记录或报告失败：")
    else:
        rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
        assert rc == 1 and "Traceback" not in err
        lines = err.splitlines()
        assert lines[0].startswith(f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出；报告没有生成："
                                   "读写这个 run 的记录或报告失败：")
        assert not any(ln.startswith("报告:") for ln in lines) and "判定明细:" in err
    assert _state(root, run_id).status is Status.ABORTED and not (root / run_id / "index.html").exists()


# ---- settle-runs：以 2 结束的几种、报告目录不存在 ----

def test_settle_runs_cloud_backend_is_refused_before_any_cloud_access(tmp_path, capsys, monkeypatch):
    def no_cloud(*a, **k):
        raise AssertionError("不该访问云端")

    monkeypatch.setattr(compose, "resolve_cloud_target", no_cloud)
    monkeypatch.setattr(compose, "check_backend_skew", no_cloud)
    rc, out, err = _settle(capsys, "--backend", "cloud", "--prefix", "p-", "--json")
    assert (rc, out) == (2, "")
    assert err.splitlines() == ["这个版本的 gherkai settle-runs 只处理本机后端（--backend local）的 run，还不能处理云端后端的 run。"]


@pytest.mark.parametrize("name", ["20300101T000000Z-nonexist", ".gherkai-creating-0123456789abcdef", "", "a/b"],
                         ids=["missing", "staging-name", "empty", "with-slash"])
def test_settle_runs_given_a_run_that_does_not_exist_exits_2(name, tmp_path, capsys, holders):
    """给出的 run 不存在（含暂存目录的名字与不合名字规则的标识）：「未找到 run」那一句、退出码 2、标准输出为空，什么都不动。"""
    root = tmp_path / "reports"
    _create(root, "20300101T000000Z-aaaaaa", holders).release()
    staging = _staging(root, "0123456789abcdef")
    rc, out, err = _settle(capsys, name, "--report-dir", str(root), "--json")
    assert (rc, out) == (2, "")
    assert err.splitlines() == [f"未找到 run：{name}（--report-dir 是否与产生这个 run 的 run 或 submit 一致？）"]
    assert staging.is_dir() and _state(root, "20300101T000000Z-aaaaaa").status is Status.RUNNING


def test_settle_runs_on_a_report_dir_that_does_not_exist(tmp_path, capsys):
    """报告目录不存在：不给标识时照常结束（人读一句、--json 是空的两个数组），给了标识按 run 不存在以 2 结束；都不建出这个目录。"""
    root = tmp_path / "nowhere" / "reports"
    rc, out, err = _settle(capsys, "--report-dir", str(root))
    assert (rc, out, err) == (0, f"报告目录 {root} 不存在，这里还没有 run。\n", "")
    rc, out, _ = _settle(capsys, "--report-dir", str(root), "--json")
    assert rc == 0 and json.loads(out) == {"backend": "local", "report_dir": str(root), "dry_run": False, "runs": [],
                                           "staging_dirs": []}
    rc, out, err = _settle(capsys, "20300101T000000Z-aaaaaa", "--report-dir", str(root))
    assert (rc, out) == (2, "") and err.startswith("未找到 run：20300101T000000Z-aaaaaa")
    assert not (tmp_path / "nowhere").exists()


def test_settle_runs_on_an_empty_report_dir_says_there_is_no_unfinished_run(tmp_path, capsys, holders):
    root = tmp_path / "reports"
    _create(root, "20300101T000000Z-aaaaaa", holders, statuses=(Status.PASSED,)).release()
    rc, out, err = _settle(capsys, "--report-dir", str(root))
    assert (rc, out, err) == (0, f"报告目录 {root} 里没有未结束的 run。\n", "")


def test_settle_runs_refuses_a_report_dir_outside_the_supported_filesystems(tmp_path, capsys, holders, monkeypatch):
    root = tmp_path / "reports"
    _create(root, "20300101T000000Z-aaaaaa", holders).release()
    before = _bytes(root, "20300101T000000Z-aaaaaa")
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs")
    rc, out, err = _settle(capsys, "--report-dir", str(root))
    assert (rc, out) == (2, "")
    platform = {"darwin": "macOS", "linux": "Linux"}
    listing = "；".join(f"{platform[p]} 支持 {'、'.join(t)}" for p, t in run_dir.ALLOWED_FILESYSTEMS.items())
    assert err.splitlines() == [
        f"报告目录 {root} 所在的文件系统是 nfs，本机后端不支持：在这样的目录上无法确认执行 run 的 gherkai 进程是否还在，没有处理其中的 run。"
        f"请把报告目录（--report-dir 选项，或配置文件里的 report-dir）换到本机磁盘上的目录（{listing}）；多台机器共用运行记录请用云端后端。"]
    assert _bytes(root, "20300101T000000Z-aaaaaa") == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root 不受目录权限限制")
def test_settle_runs_stops_at_a_record_it_cannot_read_and_keeps_what_it_did(tmp_path, capsys, holders):
    """打开 run 目录得到「不存在」之外的失败（目录权限 0o300，运行态照样读得出）是读写记录失败：就此停止，先输出已处理的部分，再说明，
    退出码 2；出错的那个与其余的没有改动，暂存目录不清理。"""
    root = tmp_path / "reports"
    done, stuck, rest = "20300103T000000Z-aaaaaa", "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    for rid in (done, stuck, rest):
        _create(root, rid, holders).release()
    leftover = _staging(root, "0123456789abcdef")
    before = {rid: _bytes(root, rid) for rid in (stuck, rest)}
    (root / stuck).chmod(0o300)
    try:
        rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    finally:
        (root / stuck).chmod(0o755)
    assert rc == 2
    assert json.loads(out)["runs"] == [{"run_id": done, "outcome": "settled", "reason": "advancer_exited", "report_written": True}]
    assert json.loads(out)["staging_dirs"] == []
    assert err.splitlines() == [
        f"读写报告目录 {root} 里的记录失败：[Errno {errno.EACCES}] {os.strerror(errno.EACCES)}: '{root / stuck}'。"
        "上面列出的已处理完，出错的那个与其余的没有改动；请检查这个目录的读写权限与所在磁盘，再执行一次同一条命令。"]
    assert {rid: _bytes(root, rid) for rid in before} == before and leftover.is_dir()


@pytest.mark.skipif(os.geteuid() == 0, reason="root 不受文件权限限制")
def test_settle_runs_that_cannot_list_does_not_say_there_is_nothing(tmp_path, capsys, holders):
    """列举本身失败（某个 run 的运行态读不了）：以 2 结束、一个都不处理，人读输出不说「没有未结束的 run」。"""
    root = tmp_path / "reports"
    _create(root, "20300101T000000Z-aaaaaa", holders).release()
    state_file = root / "20300101T000000Z-aaaaaa" / "run_state.json"
    state_file.chmod(0o000)
    try:
        rc, out, err = _settle(capsys, "--report-dir", str(root))
    finally:
        state_file.chmod(0o644)
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"读写报告目录 {root} 里的记录失败：[Errno {errno.EACCES}] {os.strerror(errno.EACCES)}: '{state_file}'。"
        "没有改动任何记录；请检查这个目录的读写权限与所在磁盘，再执行一次同一条命令。"]
    assert _state(root, "20300101T000000Z-aaaaaa").status is Status.RUNNING


@pytest.mark.skipif(os.geteuid() == 0, reason="root 不受目录权限限制")
@pytest.mark.parametrize("given", [False, True], ids=["all", "given-run-id"])
def test_settle_runs_that_stops_before_settling_any_listed_run_does_not_say_there_is_nothing(given, tmp_path, capsys,
                                                                                            holders):
    """列举完成、却在第一个 run 上就因读写记录失败停下（最新那个 run 的目录权限 0o300：运行态读得出，打开 run 目录失败）：一个都没有
    处理完，人读标准输出为空、不说「没有未结束的 run」，标准错误是读写失败那一句，退出码 2；给了 run 标识（就是这个 run）时同样不说。
    两个 run 的记录都没有改动。"""
    root = tmp_path / "reports"
    newest, older = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    for rid in (newest, older):
        _create(root, rid, holders).release()
    before = {rid: _bytes(root, rid) for rid in (newest, older)}
    (root / newest).chmod(0o300)
    try:
        rc, out, err = _settle(capsys, *([newest] if given else []), "--report-dir", str(root))
    finally:
        (root / newest).chmod(0o755)
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"读写报告目录 {root} 里的记录失败：[Errno {errno.EACCES}] {os.strerror(errno.EACCES)}: '{root / newest}'。"
        "没有改动任何记录；请检查这个目录的读写权限与所在磁盘，再执行一次同一条命令。"]
    assert {rid: _bytes(root, rid) for rid in before} == before


# ---- settle-runs：中断 ----
# 列举之前装上只记标志的处理器：Ctrl-C 只记下、不打断正在做的一项，每一项之前（于是列举之后与每一项之后）看一次，输出只做一次（ADR 0054
# 决策八「中断」）。信号是真实的：`signal.raise_signal` 在主线程里发给本进程，命令装的处理器照常收到。

def _signal_inside_end_run(monkeypatch, *, times: int = 1, signum: int = signal.SIGINT, at: "int | None" = None) -> list:
    """在真实的结束写里给本进程发一次真实的信号（之后照常写）：处理器只记下，不打断这次结束写。前 times 次结束写里各发一次；给了 at 时
    只在第 at 次里发。返回记下各次结束写的列表。"""
    real_end_run = LocalRunStore.end_run
    calls: list = []

    def end_run(self, run_id, ending, *, ended_at):
        calls.append(run_id)
        if (len(calls) == at) if at is not None else (len(calls) <= times):
            signal.raise_signal(signum)
        return real_end_run(self, run_id, ending, ended_at=ended_at)

    monkeypatch.setattr(LocalRunStore, "end_run", end_run)
    return calls


@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_ctrl_c_during_a_settle_is_handled_after_it_and_the_rest_is_left(machine, tmp_path, capsys, holders, monkeypatch):
    """处置中途（结束写里）按下的 Ctrl-C 不打断这次处置（结束写写成、报告生成）：它出现在输出里，其余的 run 与暂存目录没有处理；先输出
    已处理的部分（--json 下是单个对象），再说明，以 130 结束、不打回溯，命令结束之后信号的处置恢复原状。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    leftover = _staging(root, "0123456789abcdef")
    before = _bytes(root, second)
    calls = _signal_inside_end_run(monkeypatch)
    rc, out, err = _settle(capsys, "--report-dir", str(root), *(["--json"] if machine else []))
    assert rc == 130 and calls == [first] and "Traceback" not in err
    assert err.splitlines() == ["已停止：上面列出的已处理完，其余的没有处理；可以再执行同一条命令。"]
    if machine:
        assert json.loads(out) == {
            "backend": "local", "report_dir": str(root.resolve()), "dry_run": False, "staging_dirs": [],
            "runs": [{"run_id": first, "outcome": "settled", "reason": "advancer_exited", "report_written": True}]}
    else:
        assert _row(out, first) == [first, "已记为已结束", "执行它的 gherkai 进程已退出"] and second not in out
    assert _state(root, first).status is Status.ABORTED and (root / first / "index.html").is_file()
    assert _bytes(root, second) == before and leftover.is_dir()
    assert signal.getsignal(signal.SIGINT) is signal.default_int_handler


def _signal_inside_sweep(monkeypatch, *, at: int = 1) -> list:
    """在第 at 次真实的清理暂存目录里给本进程发一次真实的 SIGINT（之后照常清理）。返回记下各次清理的列表。"""
    real_sweep = LocalRunStore.sweep_staging_dir
    calls: list = []

    def sweep(self, name, *, dry_run):
        calls.append(name)
        if len(calls) == at:
            signal.raise_signal(signal.SIGINT)
        return real_sweep(self, name, dry_run=dry_run)

    monkeypatch.setattr(LocalRunStore, "sweep_staging_dir", sweep)
    return calls


@pytest.mark.parametrize("last", ["given-run-id", "last-run", "last-staging-dir"])
@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_ctrl_c_during_the_last_item_does_not_change_the_result(last, machine, tmp_path, capsys, holders, monkeypatch):
    """最后一项期间才收到的中断（这里在最后一项真实的结束写或清理里发出真实的 SIGINT）没有让命令少做事：每一项都处理完、出现在输出里，
    没有停止的说明，退出码与没有中断时相同（0）。三种最后一项：给了 run 标识时那唯一的一次处置；不给时没有暂存目录、最后一个 run 的
    处置；最后一个暂存目录的清理。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    given = [first] if last == "given-run-id" else []
    staging = [_staging(root, "0123456789abcdef"), _staging(root, "fedcba9876543210")] if last == "last-staging-dir" else []
    if last == "last-staging-dir":
        calls = _signal_inside_sweep(monkeypatch, at=2)
    else:
        calls = _signal_inside_end_run(monkeypatch, at=1 if given else 2)
    rc, out, err = _settle(capsys, *given, "--report-dir", str(root), *(["--json"] if machine else []))
    assert (rc, err) == (0, "")
    settled = [first] if given else [first, second]
    assert calls == ([s.name for s in staging] if staging else settled)
    if machine:
        doc = json.loads(out)
        assert [(r["run_id"], r["outcome"]) for r in doc["runs"]] == [(rid, "settled") for rid in settled]
        assert doc.get("staging_dirs") == (None if given else [{"name": s.name, "outcome": "removed", "reason": None}
                                                              for s in staging])
    else:
        assert all(_row(out, rid)[1] == "已记为已结束" for rid in settled)
        assert all(_row(out, s.name)[1] == "已删除" for s in staging)
    assert all(_state(root, rid).status is Status.ABORTED for rid in settled)
    assert not any(s.exists() for s in staging)
    assert signal.getsignal(signal.SIGINT) is signal.default_int_handler


@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_ctrl_c_before_the_settle_of_a_given_run_changes_nothing(machine, tmp_path, capsys, holders, monkeypatch):
    """给了 run 标识时，那一次处置之前同样看一次标志：装上处理器之后、处置之前收到的 Ctrl-C（这里在报告目录的边界检查里发出真实的
    SIGINT）使它不处置，说明没有改动任何记录，以 130 结束；人读输出为空，--json 是 runs 为空数组的那一个对象；记录字节不变。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    before = _bytes(root, run_id)
    real_check = run_dir.check_existing_dir

    def check_existing_dir(path):
        signal.raise_signal(signal.SIGINT)
        return real_check(path)

    monkeypatch.setattr(run_dir, "check_existing_dir", check_existing_dir)
    settles = _count_settles(monkeypatch)
    rc, out, err = _settle(capsys, run_id, "--report-dir", str(root), *(["--json"] if machine else []))
    assert rc == 130 and settles == [] and "Traceback" not in err
    assert err.splitlines() == ["已停止，没有改动任何记录；可以再执行同一条命令。"]
    if machine:
        assert json.loads(out) == {"backend": "local", "report_dir": str(root.resolve()), "dry_run": False, "runs": []}
    else:
        assert out == ""
    assert _bytes(root, run_id) == before


def test_sigterm_during_a_settle_is_handled_like_ctrl_c_and_exits_143(tmp_path, capsys, holders, monkeypatch):
    """SIGTERM 由同一个处理器记下：这次处置照样做完，其余的没有处理，说明相同，退出码按信号取 143；SIGTERM 的处置随后恢复原状。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    before = signal.getsignal(signal.SIGTERM)
    _signal_inside_end_run(monkeypatch, signum=signal.SIGTERM)
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert rc == 143 and [r["run_id"] for r in json.loads(out)["runs"]] == [first]
    assert err.splitlines() == ["已停止：上面列出的已处理完，其余的没有处理；可以再执行同一条命令。"]
    assert _state(root, second).status is Status.RUNNING and signal.getsignal(signal.SIGTERM) is before


def test_ctrl_c_while_cleaning_a_staging_dir_is_handled_after_that_one(tmp_path, capsys, holders, monkeypatch):
    """清理暂存目录时按下的 Ctrl-C（这里在真实的清理里给本进程发一次真实的 SIGINT）不打断这一项：它已删去、出现在输出里，下一个
    暂存目录没有处理；先输出已处理的部分，再说明，以 130 结束。"""
    root = tmp_path / "reports"
    first, second = _staging(root, "0123456789abcdef"), _staging(root, "fedcba9876543210")
    calls = _signal_inside_sweep(monkeypatch)
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert rc == 130 and calls == [first.name]
    assert json.loads(out)["staging_dirs"] == [{"name": first.name, "outcome": "removed", "reason": None}]
    assert err.splitlines() == ["已停止：上面列出的已处理完，其余的没有处理；可以再执行同一条命令。"]
    assert not first.exists() and second.is_dir()


def _signal_after_listing(monkeypatch, *, during: bool) -> None:
    """列举 run 时给本进程发一次真实的 SIGINT：during 为真时在列举里面（读运行态的那一步），为假时在列举返回之后、第一项之前。列举照常
    完成、返回真实的结果。"""
    from gherkai_runtime import settle

    if during:
        real_list_runs = LocalRunStore.list_runs

        def list_runs(self, statuses, *, limit):
            signal.raise_signal(signal.SIGINT)
            return real_list_runs(self, statuses, limit=limit)

        monkeypatch.setattr(LocalRunStore, "list_runs", list_runs)
        return
    real_listing = settle.unfinished_run_ids

    def listing(target):
        ids = real_listing(target)
        signal.raise_signal(signal.SIGINT)
        return ids

    monkeypatch.setattr(settle, "unfinished_run_ids", listing)


@pytest.mark.parametrize("during", [True, False], ids=["while-listing", "after-listing"])
def test_ctrl_c_before_the_first_settle_does_not_say_there_is_nothing(during, tmp_path, capsys, holders, monkeypatch):
    """列举期间或列举之后、第一项之前按下的 Ctrl-C：列举完成，第一项之前看到标志，一个都不处理；列出的 run 一个都没有处理完，人读输出
    为空、不说「没有未结束的 run」，--json 是空的两个数组；说明没有改动任何记录，以 130 结束，记录字节不变、暂存目录不动。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    leftover = _staging(root, "0123456789abcdef")
    before = _bytes(root, run_id)
    _signal_after_listing(monkeypatch, during=during)
    rc, out, err = _settle(capsys, "--report-dir", str(root))
    assert (rc, out) == (130, "") and err.splitlines() == ["已停止，没有改动任何记录；可以再执行同一条命令。"]
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert rc == 130 and json.loads(out)["runs"] == [] and json.loads(out)["staging_dirs"] == []
    assert err.splitlines() == ["已停止，没有改动任何记录；可以再执行同一条命令。"]
    assert _bytes(root, run_id) == before and leftover.is_dir()


@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_ctrl_c_just_before_the_output_still_prints_what_was_done(machine, tmp_path, capsys, holders, monkeypatch):
    """处理完全部各项之后、开始输出之前按下的 Ctrl-C（这里在进入输出的那一步发出真实的 SIGINT）：输出照常做一次，已处理的两个 run 与
    删去的暂存目录都在里面（人读表格；--json 下是一个完整的对象）；这个中断没有让命令少做事，没有停止的说明，以 0 结束。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    leftover = _staging(root, "0123456789abcdef")
    real_emit = m._emit_settle_runs

    def emit(*a, **k):
        signal.raise_signal(signal.SIGINT)
        return real_emit(*a, **k)

    monkeypatch.setattr(m, "_emit_settle_runs", emit)
    rc, out, err = _settle(capsys, "--report-dir", str(root), *(["--json"] if machine else []))
    assert (rc, err) == (0, "")
    if machine:
        doc = json.loads(out)
        assert [(r["run_id"], r["outcome"]) for r in doc["runs"]] == [(first, "settled"), (second, "settled")]
        assert doc["staging_dirs"] == [{"name": leftover.name, "outcome": "removed", "reason": None}]
    else:
        assert _row(out, first)[1] == "已记为已结束" and _row(out, second)[1] == "已记为已结束"
        assert _row(out, leftover.name)[1] == "已删除"
    assert not leftover.exists()


def test_ctrl_c_while_printing_the_result_lets_the_output_finish_once(tmp_path, capsys, holders, monkeypatch):
    """输出期间按下的 Ctrl-C 不打断输出：标准输出恰是一个完整的 JSON 对象（没有第二次输出）；它没有让命令少做事，没有停止的说明，以 0
    结束。"""
    root = tmp_path / "reports"
    _create(root, "20300101T000000Z-aaaaaa", holders).release()
    real_print = builtins.print
    printed: list = []

    def print_(*a, **k):
        if k.get("file") is None:  # 只数写到标准输出的那几次；说明经同一个 print 写到标准错误
            printed.append(a)
            if a and str(a[0]).lstrip().startswith("{"):
                signal.raise_signal(signal.SIGINT)
        return real_print(*a, **k)

    monkeypatch.setattr(builtins, "print", print_)
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert (rc, err) == (0, "") and len(printed) == 1
    assert json.loads(out)["runs"] == [{"run_id": "20300101T000000Z-aaaaaa", "outcome": "settled",
                                        "reason": "advancer_exited", "report_written": True}]


def test_a_record_failure_that_comes_with_an_interrupt_ends_as_the_failure(tmp_path, capsys, holders, monkeypatch):
    """列举时收到 Ctrl-C、列举本身又以读写失败结束：停下的原因是读写失败，按它说明、以 2 结束，不另给中断的那一句；什么都没有处理。"""
    root = tmp_path / "reports"
    _create(root, "20300101T000000Z-aaaaaa", holders).release()
    denied = PermissionError(errno.EACCES, os.strerror(errno.EACCES), str(root / "20300101T000000Z-aaaaaa" / "run_state.json"))

    def list_runs(self, statuses, *, limit):
        signal.raise_signal(signal.SIGINT)
        raise denied

    monkeypatch.setattr(LocalRunStore, "list_runs", list_runs)
    rc, out, err = _settle(capsys, "--report-dir", str(root))
    assert (rc, out) == (2, "")
    assert err.splitlines() == [f"读写报告目录 {root} 里的记录失败：{denied}。没有改动任何记录；请检查这个目录的读写权限与所在磁盘，"
                                "再执行一次同一条命令。"]


# ---- 等待中的 status --wait（本机） ----

def _status(capsys, *argv) -> tuple[int, str, str]:
    rc = m.main(["status", *argv])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def _polls(monkeypatch, on_poll) -> list:
    """把等待间隔里的 sleep 换成不真等的函数：每一小段都不超过 0.2 秒，凑满一个轮询间隔记一次（记下这个间隔的长度），第 n 个间隔凑满时
    执行 on_poll(n)。"""
    polls: list = []
    slices: list = []

    def sleep(s):
        assert 0 < s <= 0.2, s
        slices.append(s)
        if round(sum(slices), 6) >= m._LOCAL_WAIT_POLL_S:
            polls.append(round(sum(slices), 6))
            slices.clear()
            on_poll(len(polls))

    monkeypatch.setattr(time, "sleep", sleep)
    return polls


def test_status_wait_settles_once_the_holder_is_gone_and_renders_the_terminal_state(tmp_path, capsys, holders, monkeypatch):
    """锁被持有、期限没到：继续等待且不说明；持有者放开之后的下一次轮询即处置（锁拿到了那一行），标准错误说一句本命令已把它记为已结束，
    标准输出照不带 --wait 的规则渲染终态，退出码 1；报告生成了，所以报告那一行在。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    holder = _create(root, run_id, holders)
    polls = _polls(monkeypatch, lambda n: holder.release() if n == 3 else None)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert rc == 1 and polls == [1.0, 1.0, 1.0]
    lines = err.splitlines()
    assert lines[0] == f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出。"
    assert f"报告: {(root / run_id / 'index.html').resolve().as_uri()}" in lines
    assert out.splitlines()[0] == f"run {run_id}: aborted"
    assert "message=执行这个 run 的 gherkai 进程已退出（已记为已结束）" in out


def test_status_wait_json_says_nothing_and_shows_the_settled_run_in_the_document(tmp_path, capsys, holders, monkeypatch):
    """--json 下「已把它记为已结束」不给，报告生成了也就没有诊断：标准错误为空，本命令处置了它由 JSON 文档里的状态与结束原因体现，
    退出码 1。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    holder = _create(root, run_id, holders)
    _polls(monkeypatch, lambda n: holder.release() if n == 2 else None)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait", "--json")
    doc = json.loads(out)
    assert (rc, err) == (1, "")
    assert (doc["status"], doc["message"]) == ("aborted", "执行这个 run 的 gherkai 进程已退出（已记为已结束）")
    assert doc["artifacts"]["report_index"] == (root.resolve() / run_id / "index.html").as_uri()


def test_status_wait_json_merges_settling_into_the_line_it_exits_2_with(tmp_path, capsys, holders, monkeypatch):
    """--json 下等待中的说明不给（这里是会说明「不知道允许运行到什么时候」的那一种）；本命令处置了它而随后显示不了、没有 JSON 文档时，
    「已把它记为已结束」只出现在以 2 结束的那一句诊断里。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    holder = _create(root, run_id, holders)
    (root / run_id / "run_meta.json").write_text("{", encoding="utf-8")
    _polls(monkeypatch, lambda n: holder.release() if n == 2 else None)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait", "--json")
    # 提交记录不完整：处置之后显示时与不带 --wait 的 status 一样以 2 结束、没有 JSON 文档；--json 下标准错误只有诊断，已把它记为已结束
    # 这件事（连同报告没有生成）并进以 2 结束的那一句
    assert (rc, out) == (2, "")
    try:
        json.loads("{")
    except ValueError as e:
        why = str(e)
    assert err.splitlines() == [
        f"本命令已把 run {run_id} 记为已结束（报告没有生成：这个 run 的提交记录不完整或形态不对，报告要按提交记录列出各个 job），"
        f"但显示不了它：这个 run 的提交记录不完整或形态不对，本机不能读取它：definition 不是合法的 JSON（{why}）"
        "（用写出它的那个版本查看，或重新提交）"]
    assert _state(root, run_id).status is Status.ABORTED


@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_status_wait_that_settles_and_then_cannot_show_says_it_settled_once(machine, tmp_path, capsys, holders, monkeypatch):
    """处置写成（报告也生成了）之后显示时读记录失败、以 2 结束：--json 下标准输出为空，「已把它记为已结束」并进那一句诊断；人读方式下
    这件事在处置之后那一句里已经说过，诊断里不重复。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()

    def unreadable_header(self, rid):
        raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), str(root / rid / "run_meta.json"))

    monkeypatch.setattr(LocalRunStore, "peek_definition_header", unreadable_header)  # 只有显示的一步读头，处置读整份提交记录
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait", *(["--json"] if machine else []))
    failure = (f"读取 run {run_id} 的记录失败：[Errno {errno.EACCES}] {os.strerror(errno.EACCES)}: "
               f"'{root / run_id / 'run_meta.json'}'。请检查报告目录 {root.resolve()} 的读权限后重新执行。")
    assert (rc, out) == (2, "")
    if machine:
        assert err.splitlines() == [f"本命令已把 run {run_id} 记为已结束，但显示不了它：{failure}"]
    else:
        assert err.splitlines() == [f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出。", failure]
    assert _state(root, run_id).status is Status.ABORTED and (root / run_id / "index.html").is_file()


def test_status_wait_on_a_malformed_definition_tells_once_then_settles_and_shows_like_status(tmp_path, capsys, holders,
                                                                                           monkeypatch):
    """提交记录不完整（不是别的版本）：期限读不出、只凭锁；等待中说明一次（之后的轮询不重复），持有者放开即处置，先说已记为已结束、报告
    没有生成，再按不带 --wait 的 status 的显示规则以 2 结束。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    holder = _create(root, run_id, holders)
    (root / run_id / "run_meta.json").write_text("{", encoding="utf-8")
    _polls(monkeypatch, lambda n: holder.release() if n == 3 else None)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    lines = err.splitlines()
    assert (rc, out) == (2, "")
    assert lines[0] == (f"run {run_id} 的提交记录不完整或形态不对，不知道它允许运行到什么时候：本命令只在执行它的 gherkai 进程退出之后"
                        "把它记为已结束；可按 Ctrl-C 停止等待。")
    assert lines[1] == (f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出；报告没有生成：这个 run 的提交记录不完整或形态"
                        "不对，报告要按提交记录列出各个 job。")
    assert lines[2].startswith("这个 run 的提交记录不完整或形态不对，本机不能读取它：") and len(lines) == 3


@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_status_wait_on_an_unreadable_state_exits_2_like_status_without_waiting(machine, tmp_path, capsys, holders,
                                                                                 monkeypatch):
    """运行态读不出：本命令不处置它，也不等待（读不出是持续的状态，等不出结果），以退出码 2 结束；说明与不带 --wait 的 status 是同一句
    （--json 下同样给出，它是以 2 结束的原因），记录字节不变。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    (root / run_id / "run_state.json").write_text("{broken", encoding="utf-8")
    before = _bytes(root, run_id)
    monkeypatch.setattr(time, "sleep", lambda s: pytest.fail("运行态读不出时不等待"))
    json_flag = ["--json"] if machine else []
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait", *json_flag)
    assert (rc, out) == (2, "")
    assert (2, "", err) == _status(capsys, run_id, "--report-dir", str(root), *json_flag)
    try:
        json.loads("{broken")
    except ValueError as e:
        why = str(e)
    assert err.splitlines() == [
        f"run {run_id} 的运行状态记录读不出（{why}），本命令不能显示它：settle-runs 与 status --wait 不改动这个 run 的记录，"
        f"确认不需要之后可以手工移走 run 目录 {root.resolve() / run_id}。"]
    assert _bytes(root, run_id) == before


@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_status_wait_with_an_unavailable_lock_and_no_deadline_exits_2_without_waiting(machine, tmp_path, capsys, holders,
                                                                                       monkeypatch):
    """锁不可用（这里把不阻塞的 flock 换成得到 ENOLCK 的替身）而提交记录也读不出：既不能凭锁判断，也没有可以等到的时刻，所以不等待，
    以退出码 2 结束；说明写出加锁失败的原因、读不到允许运行到什么时候、为什么不等与怎么办（--json 下同样给出），记录字节不变。"""
    import fcntl

    real_flock = fcntl.flock

    def flock(fd, op):
        if op & fcntl.LOCK_NB:
            raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))
        return real_flock(fd, op)

    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    (root / run_id / "run_meta.json").unlink()
    before = _bytes(root, run_id)
    monkeypatch.setattr(fcntl, "flock", flock)
    monkeypatch.setattr(time, "sleep", lambda s: pytest.fail("锁不可用而期限也读不出时不等待"))
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait", *(["--json"] if machine else []))
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"无法确认执行 run {run_id} 的 gherkai 进程是否还在（在 run 目录上加锁失败：{os.strerror(errno.ENOLCK)}），它的提交记录也不存在，"
        "不知道它允许运行到什么时候。本命令既不能凭锁判断执行它的进程是否已退出，也不知道该等到什么时刻，所以不等待，也没有改动它的记录。"
        f"请检查 run 目录 {root.resolve() / run_id} 所在的文件系统与访问权限后重新执行；只查看它现在的状态可用 "
        f"gherkai status {run_id} --report-dir {root.resolve()}。"]
    assert _bytes(root, run_id) == before


def test_status_wait_with_an_unavailable_lock_tells_when_it_will_settle_and_settles_past_the_deadline(
        tmp_path, capsys, holders, monkeypatch):
    """锁不可用、期限读得到：说明一次原因与本命令按期限处置的本地时刻；墙钟过了期限加 300 秒的那次轮询按期限处置。"""
    import fcntl

    real_flock = fcntl.flock

    def flock(fd, op):
        if op & fcntl.LOCK_NB:
            raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))
        return real_flock(fd, op)

    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    deadline = datetime(2030, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    _create(root, run_id, holders, deadline=deadline)
    clock = {"now": deadline}
    monkeypatch.setattr(compose, "now", lambda: clock["now"])
    monkeypatch.setattr(fcntl, "flock", flock)
    _polls(monkeypatch, lambda n: clock.update(now=deadline + timedelta(seconds=300, microseconds=1)) if n == 2 else None)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    local = (deadline + timedelta(seconds=300)).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    assert rc == 1
    assert err.splitlines()[:2] == [
        f"无法确认执行 run {run_id} 的 gherkai 进程是否还在（在 run 目录上加锁失败：{os.strerror(errno.ENOLCK)}）。到 {local} 仍没有"
        "结束时，本命令把它记为已超过允许运行的时间；可按 Ctrl-C 停止等待。",
        f"本命令已把 run {run_id} 记为已结束：已超过允许运行的时间。"]
    assert _state(root, run_id).message == "已超过允许运行的时间（已记为已结束）"


def _count_settles(monkeypatch) -> list:
    """记下等待中的 status --wait 做了几次处置（真实的 `settle.settle_run` 照常执行）。"""
    from gherkai_runtime import settle

    real_settle = settle.settle_run
    calls: list = []

    def settle_run(*a, **k):
        calls.append(a[1])
        return real_settle(*a, **k)

    monkeypatch.setattr(settle, "settle_run", settle_run)
    return calls


def test_status_wait_ctrl_c_before_settling_changes_nothing(tmp_path, capsys, holders, monkeypatch):
    """等待的间隔里按下的 Ctrl-C（在第一个间隔凑满时发出真实的 SIGINT）：不再做下一次处置，说明没有改动，130，不打回溯；记录字节不变，
    命令结束之后信号的处置恢复原状。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders)
    before = _bytes(root, run_id)
    settles = _count_settles(monkeypatch)
    polls = _polls(monkeypatch, lambda n: signal.raise_signal(signal.SIGINT))
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert (rc, out) == (130, "") and "Traceback" not in err
    assert err.splitlines() == [f"已停止等待，本命令没有改动 run {run_id} 的记录；可以再执行同一条命令接着等待。"]
    assert polls == [1.0] and settles == [run_id]
    assert _bytes(root, run_id) == before and signal.getsignal(signal.SIGINT) is signal.default_int_handler


def test_status_wait_ctrl_c_while_waiting_stops_within_one_slice(tmp_path, capsys, holders, monkeypatch):
    """等待的间隔分成不超过 0.2 秒的小段、每段之前看一次标志：在第一小段里按下的 Ctrl-C，这一小段睡完即停止等待，不再睡余下的部分、不再
    处置；说明没有改动，130。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders)
    settles = _count_settles(monkeypatch)
    slept: list = []

    def sleep(s):
        slept.append(s)
        signal.raise_signal(signal.SIGINT)

    monkeypatch.setattr(time, "sleep", sleep)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert (rc, out) == (130, "") and slept == [0.2] and settles == [run_id]
    assert err.splitlines() == [f"已停止等待，本命令没有改动 run {run_id} 的记录；可以再执行同一条命令接着等待。"]


@pytest.mark.parametrize(("signum", "rc"), [(signal.SIGINT, 130), (signal.SIGTERM, 143)], ids=["SIGINT", "SIGTERM"])
def test_status_wait_ctrl_c_during_the_settle_is_handled_after_it(signum, rc, tmp_path, capsys, holders, monkeypatch):
    """处置中途（结束写里）收到的中断不打断这次处置：记录已结束、报告已生成；处置之后看到标志，不再显示，说明已把它记为已结束并给出
    查看的命令，退出码按信号取（SIGINT 130、SIGTERM 143）。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    _signal_inside_end_run(monkeypatch, signum=signum)
    got, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert (got, out) == (rc, "")
    assert err.splitlines() == [f"已停止：本命令已把 run {run_id} 记为已结束，可用 gherkai status {run_id} --report-dir {root} 查看。"]
    assert _state(root, run_id).status is Status.ABORTED and (root / run_id / "index.html").is_file()


def test_status_wait_tells_again_when_the_lock_error_code_changes_and_once_per_code(tmp_path, capsys, holders, monkeypatch):
    """等待中的说明按结构化的原因与错误码去重：加锁失败的错误码不变时连续多轮只说明一次，错误码变了（ENOLCK 变为 EOPNOTSUPP）再说明
    一次；期限读得出，墙钟过了期限加 300 秒的那一轮按期限处置。不阻塞的 flock 换成按轮次给出错误码的替身（错误的归类是我们的逻辑）。"""
    import fcntl

    real_flock = fcntl.flock
    tries: list = []

    def flock(fd, op):
        if op & fcntl.LOCK_NB:
            tries.append(op)
            code = errno.ENOLCK if len(tries) <= 3 else errno.EOPNOTSUPP
            raise OSError(code, os.strerror(code))
        return real_flock(fd, op)

    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    deadline = datetime(2030, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    _create(root, run_id, holders, deadline=deadline)
    clock = {"now": deadline}
    monkeypatch.setattr(compose, "now", lambda: clock["now"])
    monkeypatch.setattr(fcntl, "flock", flock)
    _polls(monkeypatch, lambda n: clock.update(now=deadline + timedelta(seconds=300, microseconds=1)) if n == 6 else None)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    local = (deadline + timedelta(seconds=300)).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    tail = f"）。到 {local} 仍没有结束时，本命令把它记为已超过允许运行的时间；可按 Ctrl-C 停止等待。"
    head = f"无法确认执行 run {run_id} 的 gherkai 进程是否还在（在 run 目录上加锁失败："
    assert rc == 1 and len(tries) == 7
    assert err.splitlines()[:3] == [f"{head}{os.strerror(errno.ENOLCK)}{tail}", f"{head}{os.strerror(errno.EOPNOTSUPP)}{tail}",
                                    f"本命令已把 run {run_id} 记为已结束：已超过允许运行的时间。"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root 不受目录权限限制")
def test_status_wait_record_failure_that_comes_with_an_interrupt_ends_as_the_failure(tmp_path, capsys, holders, monkeypatch):
    """处置期间收到 Ctrl-C、这次处置又以读写记录失败结束（run 目录权限 0o300，打开它失败）：按读写失败那一句以 2 结束，不另给中断的那一句；
    记录字节不变。"""
    from gherkai_runtime import settle

    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    before = _bytes(root, run_id)
    real_settle = settle.settle_run

    def settle_run(*a, **k):
        signal.raise_signal(signal.SIGINT)
        return real_settle(*a, **k)

    monkeypatch.setattr(settle, "settle_run", settle_run)
    (root / run_id).chmod(0o300)
    try:
        rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    finally:
        (root / run_id).chmod(0o755)
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"读写 run {run_id} 的记录失败：[Errno {errno.EACCES}] {os.strerror(errno.EACCES)}: '{root.resolve() / run_id}'。"
        f"本命令没有把它记为已结束；请检查报告目录 {root.resolve()} 的读写权限后重新执行。"]
    assert _bytes(root, run_id) == before


@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_status_wait_ctrl_c_while_showing_the_run_does_not_change_the_result(machine, tmp_path, capsys, holders, monkeypatch):
    """处置之后、显示期间才收到的 Ctrl-C（这里在生成显示内容的那一步发出真实的 SIGINT）没有让命令少做事：照常显示，按 run 的状态给退出码
    （aborted 为 1），没有停止等待的说明。"""
    from gherkai_core import serialize

    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    real_text, real_doc = m.render.render_run_state, serialize.run_state_to_dict

    def text(state):
        signal.raise_signal(signal.SIGINT)
        return real_text(state)

    def doc(state):
        signal.raise_signal(signal.SIGINT)
        return real_doc(state)

    monkeypatch.setattr(m.render, "render_run_state", text)
    monkeypatch.setattr(serialize, "run_state_to_dict", doc)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait", *(["--json"] if machine else []))
    assert rc == 1 and "已停止" not in err and "Traceback" not in err
    if machine:
        assert (json.loads(out)["status"], err) == ("aborted", "")
    else:
        assert out.splitlines()[0] == f"run {run_id}: aborted"
        assert err.splitlines()[0] == f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出。"


# ---- 进入命令时已被忽略的信号；恢复处理器的次序 ----
# 进入命令时已被设为忽略的信号不装处理器、保持忽略（非交互 shell 的后台作业即是如此）；恢复时先 SIGTERM、后 SIGINT，恢复 SIGINT 之后
# 才到的 SIGINT 不会使 SIGTERM 留在只记标志的处理器上（ADR 0054 决策八「中断」）。信号都是真实的（`signal.raise_signal`）。

@pytest.fixture
def sigint_ignored():
    """在用例期间把 SIGINT 设为忽略，像非交互 shell 起的后台作业那样；用例结束时恢复。"""
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, previous)


def test_settle_runs_keeps_an_ignored_sigint_ignored(tmp_path, capsys, holders, monkeypatch, sigint_ignored):
    """SIGINT 进入命令时已被忽略：第一个 run 的结束写里收到的 SIGINT 不被记下，两个 run 都处理完，以 0 结束、没有停止的说明；命令结束之后
    SIGINT 仍是忽略。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    calls = _signal_inside_end_run(monkeypatch)
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert (rc, err) == (0, "") and calls == [first, second]
    assert [(r["run_id"], r["outcome"]) for r in json.loads(out)["runs"]] == [(first, "settled"), (second, "settled")]
    assert signal.getsignal(signal.SIGINT) is signal.SIG_IGN


def test_settle_runs_with_sigint_ignored_still_records_sigterm(tmp_path, capsys, holders, monkeypatch, sigint_ignored):
    """只有被忽略的那一个保持忽略：SIGINT 被忽略、SIGTERM 没有，第一个 run 的结束写里收到的 SIGTERM 照常被记下，第二个 run 没有处理，
    以 143 结束；命令结束之后 SIGINT 仍是忽略，SIGTERM 恢复原状。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    before = signal.getsignal(signal.SIGTERM)
    _signal_inside_end_run(monkeypatch, signum=signal.SIGTERM)
    rc, out, err = _settle(capsys, "--report-dir", str(root), "--json")
    assert rc == 143 and [r["run_id"] for r in json.loads(out)["runs"]] == [first]
    assert err.splitlines() == ["已停止：上面列出的已处理完，其余的没有处理；可以再执行同一条命令。"]
    assert _state(root, second).status is Status.RUNNING
    assert signal.getsignal(signal.SIGINT) is signal.SIG_IGN and signal.getsignal(signal.SIGTERM) is before


def test_status_wait_keeps_an_ignored_sigint_ignored(tmp_path, capsys, holders, monkeypatch, sigint_ignored):
    """SIGINT 进入命令时已被忽略：等待的间隔里收到的 SIGINT 不使它停止等待；持有者放开之后的那次轮询照常处置并显示，退出码按 run 的
    状态（1）；命令结束之后 SIGINT 仍是忽略。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    holder = _create(root, run_id, holders)

    def on_poll(n):
        signal.raise_signal(signal.SIGINT)
        if n == 2:
            holder.release()

    polls = _polls(monkeypatch, on_poll)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert rc == 1 and polls == [1.0, 1.0] and "已停止" not in err
    assert err.splitlines()[0] == f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出。"
    assert out.splitlines()[0] == f"run {run_id}: aborted"
    assert signal.getsignal(signal.SIGINT) is signal.SIG_IGN


def _sigint_right_after_restoring_it(monkeypatch) -> list:
    """命令恢复 SIGINT 的那一次设置处置刚完成，就给本进程发一次真实的 SIGINT（信号恰在此刻到达）：原处置是缺省的处理器，它随即抛出
    KeyboardInterrupt。只认装上只记标志的处理器之后、把 SIGINT 换回别的处理器的第一次（之后用例收尾时恢复处置的那一次不算）；返回
    记下各次注入的列表。"""
    real_signal = signal.signal
    injected: list = []
    armed: list = []

    def set_disposition(signum, handler):
        old = real_signal(signum, handler)
        if signum == signal.SIGINT:
            if isinstance(getattr(handler, "__self__", None), m._InterruptState):
                armed.append(True)
            elif armed and not injected:
                injected.append(handler)
                signal.raise_signal(signal.SIGINT)
        return old

    monkeypatch.setattr(signal, "signal", set_disposition)
    return injected


def test_status_wait_interrupted_right_after_restoring_says_what_it_did(tmp_path, capsys, holders, monkeypatch):
    """本命令已把 run 记为已结束并显示之后，恢复处理器时恰在恢复 SIGINT 之后收到 SIGINT：两个信号的处置都已复原（先恢复 SIGTERM，
    它不会留在只记标志的处理器上）；接住这个中断时的说明与刚显示的状态一致，说已把它记为已结束，不说没有改动记录；130。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    before = signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)
    injected = _sigint_right_after_restoring_it(monkeypatch)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert injected == [before[0]]
    assert (signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)) == before
    assert rc == 130 and out.splitlines()[0] == f"run {run_id}: aborted"
    assert err.splitlines()[-1] == f"已停止：本命令已把 run {run_id} 记为已结束，可用 gherkai status {run_id} --report-dir {root} 查看。"
    assert "没有改动" not in err and _state(root, run_id).status is Status.ABORTED


def test_settle_runs_interrupted_right_after_restoring_leaves_no_handler_behind(tmp_path, capsys, holders, monkeypatch):
    """`settle-runs` 处理完、恢复处理器时恰在恢复 SIGINT 之后收到 SIGINT：这个中断落在命令的处理之外，以 KeyboardInterrupt 冒出 main；
    两个信号的处置都已复原，SIGTERM 不留在只记标志的处理器上；输出在恢复之前已经写完。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    before = signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)
    _sigint_right_after_restoring_it(monkeypatch)
    with pytest.raises(KeyboardInterrupt):
        m.main(["settle-runs", "--report-dir", str(root), "--json"])
    assert (signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)) == before
    assert [r["run_id"] for r in json.loads(capsys.readouterr().out)["runs"]] == [run_id]


def test_status_wait_on_a_finished_run_neither_checks_the_filesystem_nor_tries_the_lock(tmp_path, capsys, holders, monkeypatch):
    """已结束的 run：直接渲染、按终态给退出码，不做边界检查、不碰锁（取文件系统类型一调用即失败，照样渲染）。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders, statuses=(Status.FAILED,))

    def no_check(fd):
        raise AssertionError("已结束的 run 不做边界检查")

    monkeypatch.setattr(run_dir, "filesystem_type", no_check)
    monkeypatch.setattr(time, "sleep", lambda s: pytest.fail("已结束的 run 不等待"))
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert rc == 1 and out.splitlines()[0] == f"run {run_id}: failed" and "本命令已把" not in err


def test_status_wait_refuses_a_run_dir_outside_the_supported_filesystems(tmp_path, capsys, holders, monkeypatch):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    before = _bytes(root, run_id)
    monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: "nfs")
    monkeypatch.setattr(time, "sleep", lambda s: pytest.fail("run 目录不过边界检查时不等待"))
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    platform = {"darwin": "macOS", "linux": "Linux"}
    listing = "；".join(f"{platform[p]} 支持 {'、'.join(t)}" for p, t in run_dir.ALLOWED_FILESYSTEMS.items())
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"run 目录 {root.resolve() / run_id} 所在的文件系统是 nfs，本机后端不支持：在这样的目录上无法确认执行 run 的 gherkai 进程是否还在，"
        f"本命令不等待它，也没有改动它的记录。请把报告目录（--report-dir 选项，或配置文件里的 report-dir）换到本机磁盘上的目录（{listing}）"
        "；多台机器共用运行记录请用云端后端。"]
    assert _bytes(root, run_id) == before


def test_status_wait_on_a_run_written_by_another_version_exits_2_before_waiting(tmp_path, capsys, holders, monkeypatch):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    meta = json.loads((root / run_id / "run_meta.json").read_text(encoding="utf-8"))
    meta.update(schema_version=DEFINITION_SCHEMA_VERSION + 1, cli_version="9.9.0")
    (root / run_id / "run_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    before = _bytes(root, run_id)
    monkeypatch.setattr(time, "sleep", lambda s: pytest.fail("别的版本写出的 run 不进入等待"))
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"这个 run 的提交记录由更新版本的 gherkai 9.9.0 写出，本机的 gherkai 读不懂它的记录格式（记录是第 {DEFINITION_SCHEMA_VERSION + 1} "
        f"版，本机支持第 {DEFINITION_SCHEMA_VERSION} 版）。请升级本机的 gherkai：uv tool upgrade gherkai"]
    assert _bytes(root, run_id) == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root 不受目录权限限制")
def test_status_wait_exits_2_when_the_record_cannot_be_read_or_written(tmp_path, capsys, holders, monkeypatch):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    before = _bytes(root, run_id)
    (root / run_id).chmod(0o300)
    try:
        rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    finally:
        (root / run_id).chmod(0o755)
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"读写 run {run_id} 的记录失败：[Errno {errno.EACCES}] {os.strerror(errno.EACCES)}: '{root.resolve() / run_id}'。"
        f"本命令没有把它记为已结束；请检查报告目录 {root.resolve()} 的读写权限后重新执行。"]
    assert _bytes(root, run_id) == before


def test_status_wait_exits_2_when_the_run_is_deleted_while_waiting(tmp_path, capsys, holders, monkeypatch):
    import shutil

    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders)
    _polls(monkeypatch, lambda n: shutil.rmtree(root / run_id) if n == 2 else None)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), "--wait")
    assert (rc, out) == (2, "")
    assert err.splitlines() == [f"未找到 run：{run_id}（--report-dir 是否与产生这个 run 的 run 或 submit 一致？）"]


# ---- 不带 --wait 的 status（本机） ----

def test_status_without_wait_on_an_unreadable_state_exits_2_with_what_to_do(tmp_path, capsys, holders):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    (root / run_id / "run_state.json").write_text("{broken", encoding="utf-8")
    try:
        json.loads("{broken")
    except ValueError as e:
        why = str(e)
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root))
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"run {run_id} 的运行状态记录读不出（{why}），本命令不能显示它：settle-runs 与 status --wait 不改动这个 run 的记录，"
        f"确认不需要之后可以手工移走 run 目录 {root.resolve() / run_id}。"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root 不受文件权限限制")
def test_status_without_wait_exits_2_when_the_record_cannot_be_read(tmp_path, capsys, holders):
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    state_file = root / run_id / "run_state.json"
    state_file.chmod(0o000)
    try:
        rc, out, err = _status(capsys, run_id, "--report-dir", str(root))
    finally:
        state_file.chmod(0o644)
    assert (rc, out) == (2, "")
    assert err.splitlines() == [
        f"读取 run {run_id} 的记录失败：[Errno {errno.EACCES}] {os.strerror(errno.EACCES)}: '{root.resolve() / run_id / 'run_state.json'}'。"
        f"请检查报告目录 {root.resolve()} 的读权限后重新执行。"]


@pytest.mark.parametrize("detached", [False, True])
def test_status_without_wait_on_a_pending_run_gives_no_hint(detached, tmp_path, capsys, holders):
    """本机不带 --wait 的 status 对全部 job 仍 pending 的 run 不给提示（不论是不是 submit 提交的）：它只读记录、不碰锁。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders, statuses=(Status.PENDING,))
    if detached:
        path = root / run_id / "run_state.json"
        path.write_text(json.dumps({**json.loads(path.read_text(encoding="utf-8")), "detached": True}), encoding="utf-8")
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root))
    assert (rc, err) == (0, "") and out.splitlines()[0] == f"run {run_id}: pending"


def test_status_no_longer_accepts_max_concurrency(capsys):
    with pytest.raises(SystemExit) as e:
        m.main(["status", "20300101T000000Z-aaaaaa", "--max-concurrency", "2"])
    assert e.value.code == 2 and "--max-concurrency" in capsys.readouterr().err


@pytest.mark.parametrize("wait", [False, True])
def test_local_status_does_not_resolve_the_aws_identity(wait, tmp_path, capsys, holders, monkeypatch):
    """本机 status（含 --wait）不解析 AWS 身份：AWS_PROFILE 指向不存在的 profile 时照常工作。"""
    monkeypatch.setenv("AWS_PROFILE", "gherkai-test-no-such-profile")
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders).release()
    rc, out, err = _status(capsys, run_id, "--report-dir", str(root), *(["--wait"] if wait else []))
    assert rc == (1 if wait else 0) and "AWS 身份不可用" not in err
    assert out.splitlines()[0] == f"run {run_id}: {'aborted' if wait else 'running'}"


# ---- 说法：可以按期限记为已结束的时刻 ----

def test_the_time_a_run_can_be_settled_is_said_the_same_way_in_both_helps_and_in_the_reasons(tmp_path, capsys, holders,
                                                                                            monkeypatch):
    """期限之后、期限加 300 秒之前的 run 已超过允许运行的时间、还不能按期限处置：锁被持有时的原因说「还没有到可以记为已结束的时刻（允许运行
    的时间之后再过 5 分钟）」，不说「还没有超过」；settle-runs 与 status --wait 的帮助用同一种说法。5 分钟由那 300 秒换算。"""
    import argparse

    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    deadline = datetime(2030, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    _create(root, run_id, holders, deadline=deadline)
    monkeypatch.setattr(compose, "now", lambda: deadline + timedelta(seconds=299))
    rc, out, _ = _settle(capsys, run_id, "--report-dir", str(root))
    reason = _row(out, run_id)[2]
    assert rc == 0 and reason == f"{HELD_BY_SOMEONE}；{NOT_YET}" and "还没有超过" not in reason
    sub = next(a for a in m._build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    phrase = "允许运行的时间之后再过 5 分钟"
    assert phrase in next(a.help for a in sub.choices["status"]._actions if a.dest == "wait")
    assert phrase in next(a.help for a in sub._choices_actions if a.dest == "settle-runs")


def test_settle_runs_is_a_public_command_in_the_help(capsys):
    with pytest.raises(SystemExit) as e:
        m.main(["--help"])
    assert e.value.code == 0 and "settle-runs" in capsys.readouterr().out
    with pytest.raises(SystemExit) as e:
        m.main(["settle-runs", "--help"])
    out = capsys.readouterr().out
    assert e.value.code == 0 and "--dry-run" in out and "--report-dir" in out


# ---- 真实进程：两种推进器被强杀、等待中的 status --wait 处置；settle-runs 处置期间的真实 SIGINT ----

# 假 worker：能力自述与匹配查询照 `_fake_worker` 的值作答；被当作 job 执行时在 GHERKAI_TEST_WORKER_DIR 里留一个名为自己进程号的
# 文件，然后等到它的所属进程不在（所属进程号查不到、或自己的父进程变了），至多 60 秒。只用 ASCII
_WAITING_WORKER = """\
import json, os, sys, time
caps = sys.argv[1]
flag = sys.argv[2] if len(sys.argv) > 2 else None
if flag == "--capabilities":
    print(open(caps, encoding="utf-8").read())
    sys.exit(0)
if flag == "--match-steps":
    print(json.dumps([None for _ in json.load(sys.stdin)]))
    sys.exit(0)
if flag is not None:
    sys.exit(3)
open(os.path.join(os.environ["GHERKAI_TEST_WORKER_DIR"], "worker-%d" % os.getpid()), "w").close()
owner = int(os.environ.get("GHERKAI_PARENT_PID", "0"))
parent = os.getppid()
deadline = time.monotonic() + 60
while time.monotonic() < deadline and os.getppid() == parent:
    try:
        os.kill(owner, 0)
    except OSError:
        break
    time.sleep(0.05)
"""


def _child_env(tmp_path: Path) -> dict[str, str]:
    """真实子进程的环境：两个引擎的 worker 换成 `_WAITING_WORKER`，不读配置文件与 steps 目录的环境变量；AWS 用假凭证、端点指向本机
    一个不监听的端口。"""
    from _fake_worker import FAKE_DETERMINISTIC_STEPS, FAKE_MIN_GRACE_S, FAKE_MODEL_ID
    from gherkai_core.wire import PROTOCOL_SCHEMA_VERSION

    worker = tmp_path / "waiting_worker.py"
    worker.write_text(_WAITING_WORKER, encoding="utf-8")
    workers = tmp_path / "workers"
    workers.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items()
           if k not in ("NGROK_AUTHTOKEN", "GHERKAI_CONFIG", "GHERKAI_STEPS_DIR", "AWS_PROFILE")}
    for engine, grace in FAKE_MIN_GRACE_S.items():
        caps = tmp_path / f"caps-{engine}.json"
        caps.write_text(json.dumps({
            "schema_version": PROTOCOL_SCHEMA_VERSION, "engine": engine, "min_grace_s": grace,
            "targets": [{"device": "desktop", "ui_kinds": ["web"]}], "deterministic_steps": FAKE_DETERMINISTIC_STEPS,
            "model_id": FAKE_MODEL_ID[engine], compose.SESSION_WARMUP_KEY: True}), encoding="utf-8")
        env[f"GHERKAI_WORKER_{engine.upper()}_CMD"] = shlex.join([sys.executable, str(worker), str(caps)])
        env.pop(f"GHERKAI_WORKER_{engine.upper()}_CWD", None)
    env.update(AWS_ENDPOINT_URL="http://127.0.0.1:9", AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing",
               AWS_EC2_METADATA_DISABLED="true", AWS_REGION="us-east-1", GHERKAI_TEST_WORKER_DIR=str(workers))
    return env


def _wait_until(predicate, proc: "subprocess.Popen | None", what: str, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if proc is not None:
            assert proc.poll() is None, proc.communicate()
        assert time.monotonic() < deadline, f"没有在时限内{what}"
        time.sleep(0.02)


def _run_dirs(root: Path) -> list[str]:
    return [n for n in os.listdir(root) if run_dir.is_run_name(n)] if root.exists() else []


def _cli(*argv) -> list[str]:
    return [sys.executable, "-P", "-m", "gherkai_cli", *argv]


def _kill_and_reap(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.kill()
    proc.communicate(timeout=60)


def _start_foreground_run(tmp_path: Path, env: dict, root: Path) -> subprocess.Popen:
    feature = tmp_path / "t.feature"
    feature.write_text('Feature: t\n  Scenario: s\n    When "打开首页"\n', encoding="utf-8")
    return subprocess.Popen(_cli("run", str(feature), "--report-dir", str(root)), cwd=tmp_path, env=env,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _start_background_advancer(tmp_path: Path, env: dict, root: Path) -> tuple[subprocess.Popen, int, int]:
    """以 `_reconcile` 入口启动本机后台推进进程（以新会话、`-P`），测试一侧充当 submit：经标准输入交出输入、读回报管道（标准输入的写端
    一直开着）。返回 (进程, 标准输入的写端, 回报管道的读端)。"""
    job = Job(scope_id="s", scope_name="s", engine="novaact", timeout_s=300.0,
              scenarios=(Scenario(id="t.feature:2", name="s", steps=(Step(0, "When", "打开首页"),)),))
    line = handoff.encode_advancer_input(handoff.AdvancerInput(
        jobs=(job,), steps_dir=None, max_concurrency=1, per_job_tail_s=310.0, expose_local=None,
        tunnel_provider="ngrok", region="us-east-1", profile=None, report_dir=str(root)))
    report_r, report_w = os.pipe()
    stdin_r, stdin_w = os.pipe()
    try:
        proc = subprocess.Popen(_cli("_reconcile", "--report-fd", str(report_w)), stdin=stdin_r, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, pass_fds=(report_w,), start_new_session=True, cwd=tmp_path, env=env)
    finally:
        os.close(report_w)
        os.close(stdin_r)
    assert handoff.write_all(stdin_w, line)
    return proc, stdin_w, report_r


@pytest.mark.real_filesystem
@pytest.mark.parametrize("advancer", ["foreground", "background"])
def test_status_wait_settles_a_run_whose_advancer_was_killed_on_its_next_poll(advancer, tmp_path):
    """真实进程、真实锁：两种推进器各执行一个 job（假 worker 一直在等），推进器还在时等待中的 `status --wait` 在 2 秒内不返回、收到真实的
    SIGINT 以 130 结束并说明没有改动；推进器被 SIGKILL 之后，再执行一次即在下一次轮询处置：退出码 1，标准错误有本命令已把它记为已结束
    的那一句，运行态按说明表「锁拿到了」一行结束（执行中的 job 记 aborted），报告生成。worker 在推进器不在之后自行退出。"""
    root = tmp_path / "reports"
    env = _child_env(tmp_path)
    workers = Path(env["GHERKAI_TEST_WORKER_DIR"])
    extra: list[int] = []
    if advancer == "foreground":
        proc = _start_foreground_run(tmp_path, env, root)
    else:
        proc, stdin_w, report_r = _start_background_advancer(tmp_path, env, root)
        extra += [stdin_w, report_r]
    try:
        _wait_until(lambda: os.listdir(workers), proc, "起 worker")
        [run_id] = _run_dirs(root)
        assert _state(root, run_id).status is Status.RUNNING
        before = _bytes(root, run_id)

        waiting = subprocess.Popen(_cli("status", run_id, "--report-dir", str(root), "--wait"), cwd=tmp_path, env=env,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            time.sleep(2.0)
            assert waiting.poll() is None, waiting.communicate()
            waiting.send_signal(signal.SIGINT)
            out, err = waiting.communicate(timeout=30)
        finally:
            _kill_and_reap(waiting) if waiting.poll() is None else None
        assert (waiting.returncode, out, "Traceback" in err) == (130, "", False), err
        assert err.splitlines()[-1] == f"已停止等待，本命令没有改动 run {run_id} 的记录；可以再执行同一条命令接着等待。"
        assert _bytes(root, run_id) == before

        proc.kill()
        proc.communicate(timeout=60)
        done = subprocess.run(_cli("status", run_id, "--report-dir", str(root), "--wait"), cwd=tmp_path, env=env,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        assert done.returncode == 1, done.stderr
        assert done.stderr.splitlines()[0] == f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出。"
        assert done.stdout.splitlines()[0] == f"run {run_id}: aborted"
        state = _state(root, run_id)
        assert [(js.status, js.message) for js in state.jobs.values()] == [
            (Status.ABORTED, "执行这个 run 的 gherkai 进程已退出，job 没有结果（已记为已结束）")]
        assert (root / run_id / "index.html").is_file()
    finally:
        if proc.poll() is None:
            _kill_and_reap(proc)
        for fd in extra:
            os.close(fd)
    _wait_until(lambda: all(not _alive(int(n.split("-")[1])) for n in os.listdir(workers)), None, "等 worker 自行退出", 30)


@pytest.mark.real_filesystem
def test_status_wait_started_with_sigint_ignored_keeps_waiting_through_sigint(tmp_path, holders):
    """真实进程、真实信号：像非交互 shell 起的后台作业那样，启动时 SIGINT 已被设为忽略（由启动它的一方设下、经 exec 继承）。等待中的
    `status --wait` 收到 SIGINT 不停止、接着等待；收到没有被忽略的 SIGTERM 才停止，说明没有改动，以 143 结束。"""
    root = tmp_path / "reports"
    run_id = "20300101T000000Z-aaaaaa"
    _create(root, run_id, holders)  # 测试进程持着锁：有进程在管这个 run，命令一直等待
    before = _bytes(root, run_id)
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        waiting = subprocess.Popen(_cli("status", run_id, "--report-dir", str(root), "--wait"), cwd=tmp_path,
                                   env=_child_env(tmp_path), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
    finally:
        signal.signal(signal.SIGINT, previous)
    try:
        time.sleep(2.0)
        assert waiting.poll() is None, waiting.communicate()
        waiting.send_signal(signal.SIGINT)
        time.sleep(1.0)
        assert waiting.poll() is None, "被忽略的 SIGINT 停止了等待"
        waiting.send_signal(signal.SIGTERM)
        out, err = waiting.communicate(timeout=30)
    finally:
        if waiting.poll() is None:
            _kill_and_reap(waiting)
    assert (waiting.returncode, out, "Traceback" in err) == (143, "", False), err
    assert err.splitlines()[-1] == f"已停止等待，本命令没有改动 run {run_id} 的记录；可以再执行同一条命令接着等待。"
    assert _bytes(root, run_id) == before


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:  # 已退出、还没有被回收的进程 kill(0) 也成功：读它的状态排除僵尸
        out = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except OSError:
        return True
    return bool(out.stdout.strip()) and not out.stdout.strip().startswith("Z")


# 在 settle-runs 的子进程里打补丁的 sitecustomize：GHERKAI_TEST_PAUSE_AT 为 end_run 时停在真实的结束写之前，为 output 时停在开始输出的
# 那一步（人读表格与 --json 对象的生成）之前；停下时在 PAUSE 目录里放一个 paused 文件，等到 release 文件出现再接着执行。只用 ASCII
_PAUSE_IN_SETTLE_RUNS = r"""
import os, time
_dir = os.environ.get("GHERKAI_TEST_PAUSE_DIR")
_at = os.environ.get("GHERKAI_TEST_PAUSE_AT")

def _pause():
    open(os.path.join(_dir, "paused"), "w").close()
    deadline = time.monotonic() + 60
    while not os.path.exists(os.path.join(_dir, "release")) and time.monotonic() < deadline:
        time.sleep(0.01)

if _dir and _at == "end_run":
    from gherkai_core.adapters.run_store.local import LocalRunStore
    _real = LocalRunStore.end_run

    def _end_run(self, run_id, ending, *, ended_at):
        _pause()
        return _real(self, run_id, ending, ended_at=ended_at)

    LocalRunStore.end_run = _end_run
if _dir and _at == "output":
    from gherkai_cli import render
    _real_dict, _real_text = render.settle_runs_to_dict, render.render_settle_runs

    def _to_dict(*a, **k):
        _pause()
        return _real_dict(*a, **k)

    def _to_text(*a, **k):
        _pause()
        return _real_text(*a, **k)

    render.settle_runs_to_dict, render.render_settle_runs = _to_dict, _to_text
"""


def _start_paused_settle_runs(tmp_path: Path, root: Path, at: str, *flags: str) -> tuple[subprocess.Popen, Path]:
    hook, pause = tmp_path / "hook", tmp_path / "pause"
    hook.mkdir()
    pause.mkdir()
    (hook / "sitecustomize.py").write_text(_PAUSE_IN_SETTLE_RUNS, encoding="utf-8")
    env = _child_env(tmp_path)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(hook), env.get("PYTHONPATH")) if p)
    env.update(GHERKAI_TEST_PAUSE_DIR=str(pause), GHERKAI_TEST_PAUSE_AT=at)
    proc = subprocess.Popen(_cli("settle-runs", "--report-dir", str(root), *flags), cwd=tmp_path, env=env,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc, pause


def _signal_the_paused(proc: subprocess.Popen, pause: Path, what: str) -> tuple[str, str]:
    """等子进程停下，对它发 SIGINT，核对它没有因此退出（处理器只记下、不打断这一步），再放行、收下输出。"""
    try:
        _wait_until(lambda: (pause / "paused").exists(), proc, what)
        proc.send_signal(signal.SIGINT)
        time.sleep(0.5)
        assert proc.poll() is None, "收到的 SIGINT 打断了正在做的一步"
        (pause / "release").touch()
        return proc.communicate(timeout=60)
    finally:
        if proc.poll() is None:
            _kill_and_reap(proc)


@pytest.mark.real_filesystem
def test_a_real_sigint_during_a_settle_waits_for_that_settle(tmp_path, holders):
    """真实进程、真实信号：`settle-runs --json` 停在第一个 run 的结束写之前时收到 SIGINT。处理器只记下：它不在这时退出；放行之后这次处置
    做完（结束写写成、报告生成），随后以 130 结束，标准输出是只含它的单个 JSON 对象，另一个 run 没有处理，说明是已处理完的那一句。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    before = _bytes(root, second)
    proc, pause = _start_paused_settle_runs(tmp_path, root, "end_run", "--json")
    out, err = _signal_the_paused(proc, pause, "停到结束写之前")
    assert (proc.returncode, "Traceback" in err) == (130, False), err
    assert json.loads(out)["runs"] == [{"run_id": first, "outcome": "settled", "reason": "advancer_exited",
                                        "report_written": True}]
    assert err.splitlines() == ["已停止：上面列出的已处理完，其余的没有处理；可以再执行同一条命令。"]
    assert _state(root, first).status is Status.ABORTED and (root / first / "index.html").is_file()
    assert _bytes(root, second) == before


@pytest.mark.real_filesystem
@pytest.mark.parametrize("machine", [False, True], ids=["text", "json"])
def test_a_real_sigint_just_before_the_output_still_prints_what_was_done(machine, tmp_path, holders):
    """真实进程、真实信号：`settle-runs` 处理完两个 run 与一个暂存目录、停在开始输出之前时收到 SIGINT。它不在这时退出；放行之后输出照常
    做一次（人读表格里有两个 run 与那个暂存目录；--json 下是含它们的单个对象）；这个中断没有让命令少做事，没有停止的说明，以 0 结束、
    不打回溯。"""
    root = tmp_path / "reports"
    first, second = "20300102T000000Z-aaaaaa", "20300101T000000Z-aaaaaa"
    _create(root, first, holders).release()
    _create(root, second, holders).release()
    leftover = _staging(root, "0123456789abcdef")
    proc, pause = _start_paused_settle_runs(tmp_path, root, "output", *(["--json"] if machine else []))
    out, err = _signal_the_paused(proc, pause, "停到开始输出之前")
    assert (proc.returncode, err) == (0, ""), err
    if machine:
        doc = json.loads(out)
        assert [(r["run_id"], r["outcome"]) for r in doc["runs"]] == [(first, "settled"), (second, "settled")]
        assert doc["staging_dirs"] == [{"name": leftover.name, "outcome": "removed", "reason": None}]
    else:
        assert _row(out, first)[1] == "已记为已结束" and _row(out, second)[1] == "已记为已结束"
        assert _row(out, leftover.name)[1] == "已删除"
    assert _state(root, first).status is Status.ABORTED and _state(root, second).status is Status.ABORTED
    assert not leftover.exists()
