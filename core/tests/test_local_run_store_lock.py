"""LocalRunStore 的条件建 run 与写入口的互斥（ADR 0030 决定三、四，ADR 0054 决策五），真起子进程、不 mock。

建 run 经暂存目录与改名（`run_dir.create_run_dir`）：「已存在」只由改名给出，以 run 标识命名的位置已是非空目录即失败、什么都不改；
那个位置被文件或符号链接占着是写记录失败。建 run 之后的写入口（update_job_state、try_claim_job、project_state、commit_job_states、
end_run）在 run 目录下同一把 fcntl 短锁内读改写，都经同一个锁内读改写的路径（`LocalRunStore._locked_rmw`）。锁跨进程是否真的
互斥、读改写之间是否真的没有别的写插进来、改名在几个进程同时进行时是否只有一个成功，是 mock 之外的真实行为（绿≠对），所以并发的
结论用多个真实进程核对：各进程先就绪、再同时放行，各自按角色反复写，结束后检查没有任何一次写丢失、终态没有被改回，并核对这次确实
形成了交错（否则用例空转）。把短锁换成空操作时，两个并发写的用例都失败，失败的形态有：job 写与认领丢失、终态被一次读在终态之前的
job 写改回 running。

建 run 的子进程用宿主真实的文件系统类型做边界检查（子进程里没有替换），这样的用例带 `real_filesystem` 标记。
"""
from __future__ import annotations

import errno
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from gherkai_core.adapters.run_store import run_dir
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.errors import RunAlreadyExists
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.run_status import RUN_ENDINGS

_TIMEOUT_S = 120

# 子进程：先写就绪文件，再等放行文件出现，然后按角色写。只用 ASCII，参数经一个 JSON 串传入。建 run 的角色与前台 run、后台推进
# 进程一样持锁到进程退出，所以显式构造生产用的持有者
_WORKER = r"""
import json, sys, time, pathlib
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.errors import RunAlreadyExists
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
a = json.loads(sys.argv[1])
if a["role"] == "create":
    from gherkai_core.adapters.run_store.run_dir import HoldUntilExit
    store = LocalRunStore(a["root"], lock_holder=HoldUntilExit())
else:
    store = LocalRunStore(a["root"])
pathlib.Path(a["ready"]).touch()
go = pathlib.Path(a["go"])
while not go.exists():
    time.sleep(0.001)
run_id, role = a["run_id"], a["role"]
if role == "update":
    returns = []
    for k in range(a["times"]):
        returns.append(store.update_job_state(run_id, JobState(scope_id=a["scope_id"], status=Status.RUNNING,
                                                               session_id="%s-%d" % (a["scope_id"], k))))
    print(json.dumps(returns))
elif role == "claim":
    results, seen = [], []
    for sid in a["scope_ids"]:
        results.append(store.try_claim_job(run_id, sid, claimed_at="2026-11-15T00:00:00Z"))
        seen.append({k: js.session_id for k, js in store.load_run_state(run_id).jobs.items()})
    print(json.dumps({"results": results, "first": seen[0], "last": seen[-1]}))
elif role == "end":
    from gherkai_core.run_status import RUN_ENDINGS
    time.sleep(a["delay"])
    ok = store.end_run(run_id, RUN_ENDINGS[a["route"]], ended_at="2026-11-15T01:00:00Z")
    print(json.dumps({"ok": ok, "seen": {k: js.session_id for k, js in store.load_run_state(run_id).jobs.items()}}))
elif role == "create":
    job = Job(scope_id="s", scope_name="s", engine="midscene", timeout_s=300.0,
              scenarios=(Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),))
    outcomes = []
    for rid in a["run_ids"]:
        meta = RunMeta(run_id=rid, created_at=a["marker"], jobs=(job,), deadline_at="2026-01-01T01:00:00+00:00")
        state = RunState(run_id=rid, status=Status.PENDING, jobs={"s": JobState("s", Status.PENDING)},
                         started_at=a["marker"])
        try:
            store.create_run(meta, state)
            outcomes.append("created")
        except RunAlreadyExists:
            outcomes.append("exists")
    print(json.dumps(outcomes))
"""


def _run_together(tmp_path: Path, roles: list[dict]) -> list[str]:
    """起与 roles 等数的子进程，全部就绪后同时放行；返回各进程 stdout 的最后一行（次序同 roles），任一进程非零退出即失败。"""
    sync = tmp_path / "sync"
    sync.mkdir(exist_ok=True)
    go = sync / f"go-{time.monotonic_ns()}"
    procs = []
    for i, role in enumerate(roles):
        args = {"root": str(tmp_path / "runs"), "ready": str(sync / f"{go.name}-ready-{i}"), "go": str(go), **role}
        procs.append(subprocess.Popen([sys.executable, "-c", _WORKER, json.dumps(args)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    deadline = time.monotonic() + _TIMEOUT_S
    while not all((sync / f"{go.name}-ready-{i}").exists() for i in range(len(roles))):
        assert time.monotonic() < deadline, "子进程没有在时限内就绪"
        assert all(p.poll() is None for p in procs), [p.communicate() for p in procs if p.poll() is not None]
        time.sleep(0.01)
    go.touch()
    outs = []
    for p in procs:
        out, err = p.communicate(timeout=_TIMEOUT_S)
        assert p.returncode == 0, err
        outs.append(out.strip().splitlines()[-1])
    return outs


def _meta(run_id: str, scope_ids: list[str], created_at: str = "2026-11-15T00:00:00Z") -> RunMeta:
    jobs = tuple(Job(scope_id=s, scope_name=s, engine="midscene", timeout_s=300.0,
                     scenarios=(Scenario(id=f"{s}:1", name="sc", steps=(Step(0, "Given", "x"),)),)) for s in scope_ids)
    return RunMeta(run_id=run_id, created_at=created_at, jobs=jobs, deadline_at="2026-01-01T01:00:00+00:00")


def _pending(run_id: str, scope_ids: list[str]) -> RunState:
    return RunState(run_id=run_id, status=Status.PENDING, started_at="2026-11-15T00:00:00Z",
                    jobs={s: JobState(s, Status.PENDING) for s in scope_ids})


# ---------- 建 run 只在以 run 标识命名的位置还没有非空目录时成立 ----------

def _snapshot(path: Path) -> dict[str, object]:
    """path 本身与它之下每个名字的内容：文件记字节，符号链接记它指向的路径，目录记为 None。"""
    def one(p: Path):
        if p.is_symlink():
            return ("symlink", os.readlink(p))
        return None if p.is_dir() else p.read_bytes()
    out = {".": one(path)}
    if path.is_dir() and not path.is_symlink():
        out.update({str(p.relative_to(path)): one(p) for p in sorted(path.rglob("*"))})
    return out


def test_create_run_on_an_existing_run_leaves_both_files_byte_identical(tmp_path: Path, lock_holder):
    """再建同一个 run 抛 `RunAlreadyExists`，run_meta.json 与 run_state.json 逐字节不变（再建时给的 definition 与初始运行态都不同，
    被重写就一定看得出来）；后台执行标记也不因再建的实例带 detached 而出现或消失。"""
    store = LocalRunStore(tmp_path / "runs", lock_holder=lock_holder)
    store.create_run(_meta("r", ["a"]), _pending("r", ["a"]))
    assert store.try_claim_job("r", "a") is True
    run_dir_path = tmp_path / "runs" / "r"
    before = {name: (run_dir_path / name).read_bytes() for name in ("run_meta.json", "run_state.json")}

    for again in (LocalRunStore(tmp_path / "runs", lock_holder=lock_holder),
                  LocalRunStore(tmp_path / "runs", detached=True, lock_holder=lock_holder)):
        try:
            again.create_run(_meta("r", ["x", "y"], created_at="2099-01-01T00:00:00Z"), _pending("r", ["x", "y"]))
        except RunAlreadyExists:
            pass
        else:
            raise AssertionError("对已有的 run 再建应当失败")
        assert {name: (run_dir_path / name).read_bytes() for name in before} == before
    assert os.listdir(tmp_path / "runs") == ["r"]  # 两次再建的暂存目录都已删去


@pytest.mark.parametrize("contents", ["definition-only", "other-file-only", "complete-run"])
def test_create_run_onto_a_non_empty_directory_of_that_name_is_already_exists_and_changes_nothing(
        tmp_path: Path, lock_holder, contents: str):
    """以 run 标识命名的位置已是非空目录，不论里面是什么（只有运行定义、只有别的产物、完整的 run）：抛 `RunAlreadyExists`，那个
    目录逐字节不变，报告目录里没有留下暂存目录，持有者什么都没收到。"""
    runs = tmp_path / "runs"
    spot = runs / "r"
    spot.mkdir(parents=True)
    if contents == "definition-only":
        (spot / "run_meta.json").write_text('{"run_id": "r"}', encoding="utf-8")
    elif contents == "other-file-only":
        (spot / "worker.log").write_text("x", encoding="utf-8")
    else:
        other_holder = type(lock_holder)()
        try:
            LocalRunStore(tmp_path / "elsewhere", lock_holder=other_holder).create_run(_meta("r", ["a"]), _pending("r", ["a"]))
        finally:
            other_holder.close_all()
        spot.rmdir()
        (tmp_path / "elsewhere" / "r").rename(spot)
    before = _snapshot(spot)
    with pytest.raises(RunAlreadyExists) as exc:
        LocalRunStore(runs, lock_holder=lock_holder).create_run(_meta("r", ["b"]), _pending("r", ["b"]))
    assert exc.value.run_id == "r"
    assert _snapshot(spot) == before
    assert os.listdir(runs) == ["r"]
    assert lock_holder.fds == []


@pytest.mark.parametrize("occupant", ["file", "dangling-symlink", "symlink-to-directory"])
def test_create_run_reports_a_non_directory_in_place_of_the_run_as_a_write_failure(tmp_path: Path, lock_holder, occupant: str):
    """报告目录里与 run 同名的不是目录（普通文件、悬空的符号链接、指向目录的符号链接）：改名失败，抛的不是 `RunAlreadyExists` 而是
    带 run 目录路径的普通 OSError（目标不是目录），那是写记录失败，不是 run 已存在（调用方按类型分开报）。占位的那一项与符号链接
    指向的目录原样留着，暂存目录已删去，没有写下任何记录。"""
    runs = tmp_path / "runs"
    runs.mkdir()
    spot = runs / "r"
    target = tmp_path / "target"
    if occupant == "file":
        spot.write_text("不是 run 目录", encoding="utf-8")
    elif occupant == "dangling-symlink":
        spot.symlink_to(tmp_path / "nowhere")
    else:
        target.mkdir()
        (target / "keep.txt").write_text("k", encoding="utf-8")
        spot.symlink_to(target)
    before, target_before = _snapshot(spot), _snapshot(target) if target.exists() else None
    with pytest.raises(OSError) as exc:
        LocalRunStore(runs, lock_holder=lock_holder).create_run(_meta("r", ["a"]), _pending("r", ["a"]))
    assert not isinstance(exc.value, RunAlreadyExists)
    assert isinstance(exc.value, NotADirectoryError) and exc.value.filename == str(spot)
    assert _snapshot(spot) == before
    assert (_snapshot(target) if target.exists() else None) == target_before
    assert not (tmp_path / "nowhere").exists()
    assert os.listdir(runs) == ["r"]
    assert lock_holder.fds == []


def test_create_run_replaces_an_empty_directory_of_that_name(tmp_path: Path, lock_holder):
    """以 run 标识命名的位置是空目录：改名替换它（POSIX rename 的语义；空目录不带记录），照常建成。"""
    runs = tmp_path / "runs"
    (runs / "r").mkdir(parents=True)
    empty_ino = os.stat(runs / "r").st_ino
    store = LocalRunStore(runs, lock_holder=lock_holder)
    store.create_run(_meta("r", ["a"]), _pending("r", ["a"]))
    assert os.listdir(runs) == ["r"] and os.stat(runs / "r").st_ino != empty_ino
    assert set(store.load_run_state("r").jobs) == {"a"}


@pytest.mark.parametrize("run_id", [".x", ".gherkai-creating-0123456789abcdef", "a/b", "", "a" * 256])
def test_create_run_refuses_an_identifier_that_cannot_name_a_run_directory(tmp_path: Path, lock_holder, run_id: str):
    """run 标识不能用作 run 目录的名字（以点开头、含路径分隔符、空、按文件系统编码超过 255 字节）：ValueError，什么都不建，报告目录
    也不建。"""
    with pytest.raises(ValueError):
        LocalRunStore(tmp_path / "runs", lock_holder=lock_holder).create_run(_meta(run_id, ["a"]), _pending(run_id, ["a"]))
    assert os.listdir(tmp_path) == []
    assert lock_holder.fds == []


def test_create_run_without_a_lock_holder_is_a_programming_error_and_creates_nothing(tmp_path: Path):
    """不带持有者的 store（只读命令、处置方）不能建 run：RuntimeError，什么都不建。"""
    with pytest.raises(RuntimeError):
        LocalRunStore(tmp_path / "runs").create_run(_meta("r", ["a"]), _pending("r", ["a"]))
    assert os.listdir(tmp_path) == []


@pytest.mark.parametrize("name", [".gherkai-creating-0123456789abcdef", ".hidden", "nested/r"])
def test_entries_by_identifier_treat_a_name_outside_the_rule_as_no_run(tmp_path: Path, name: str):
    """名字不合规则的目录里放着合法的运行定义与带后台执行标记的运行态（如改名之前的暂存目录）：按标识读的入口都按 run 不存在
    处理，试拿得到「这个名字下已没有 run」，写入口都写不成，文件逐字节不变。"""
    root = tmp_path / "runs"
    d = root / name
    d.mkdir(parents=True)
    meta, state = _meta("r", ["a"]), _pending("r", ["a"])
    from gherkai_core.serialize import run_meta_to_dict, run_state_to_dict
    (d / "run_meta.json").write_text(json.dumps(run_meta_to_dict(meta)), encoding="utf-8")
    (d / "run_state.json").write_text(json.dumps({"detached": True, **run_state_to_dict(state)}), encoding="utf-8")
    before = _snapshot(root)
    store = LocalRunStore(root)
    assert store.load_run_state(name) is None
    assert store.load_run_meta(name) is None
    assert store.peek_definition_header(name) is None
    with pytest.raises(run_dir.RunDirGone):
        with store.probe_run_dir(name):
            pass
    with pytest.raises(FileNotFoundError):
        store.update_job_state(name, JobState("a", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        store.commit_job_states(name, [JobState("a", Status.PASSED)], ended_at="t")
    assert store.try_claim_job(name, "a") is False
    assert store.project_state(name, state) is False
    assert store.end_run(name, RUN_ENDINGS["deadline"], ended_at="t") is False
    assert _snapshot(root) == before


@pytest.mark.parametrize("name", ["a" * 256, "é" * 300], ids=["ascii", "multibyte"])
def test_entries_by_identifier_treat_a_name_too_long_for_a_directory_as_no_run(tmp_path: Path, name: str):
    """标识按文件系统编码超过 255 字节（长到不能作一层目录名）：按标识读的入口都按 run 不存在处理、写入口都写不成，不以「文件名
    太长」的 OSError 失败；报告目录里什么都不多出来。"""
    root = tmp_path / "runs"
    root.mkdir()
    store = LocalRunStore(root)
    assert store.load_run_state(name) is None
    assert store.load_run_meta(name) is None
    assert store.peek_definition_header(name) is None
    with pytest.raises(run_dir.RunDirGone):
        with store.probe_run_dir(name):
            pass
    with pytest.raises(FileNotFoundError):
        store.update_job_state(name, JobState("a", Status.RUNNING))
    assert store.try_claim_job(name, "a") is False
    assert store.end_run(name, RUN_ENDINGS["deadline"], ended_at="t") is False
    assert os.listdir(root) == []


@pytest.mark.real_filesystem
def test_concurrent_creates_of_one_run_in_separate_processes_have_exactly_one_winner(tmp_path: Path):
    """多个进程同时依次建同一批 run：每个 run 恰有一个进程建成，其余得到「已存在」；落盘的 definition 与运行态出自同一个进程
    （建成者的标记）；结束之后报告目录里只有这批 run 的目录，没有暂存目录。一批多个 run 是为了让改名的竞争反复发生。"""
    run_ids = [f"r{i:02d}" for i in range(30)]
    roles = [{"role": "create", "run_id": "", "run_ids": run_ids, "marker": f"proc-{i}"} for i in range(8)]
    outcomes = [json.loads(out) for out in _run_together(tmp_path, roles)]
    store = LocalRunStore(tmp_path / "runs")
    for k, run_id in enumerate(run_ids):
        per_run = [o[k] for o in outcomes]
        assert sorted(per_run) == ["created"] + ["exists"] * (len(roles) - 1), (run_id, per_run)
        winner = roles[per_run.index("created")]["marker"]
        assert store.load_run_meta(run_id).created_at == winner
        assert store.load_run_state(run_id).started_at == winner
    assert sorted(os.listdir(tmp_path / "runs")) == run_ids
    assert not any(n.startswith(run_dir.STAGING_PREFIX) for n in os.listdir(tmp_path / "runs"))


# ---------- 建 run 之后的写入口在文件锁内互斥 ----------

def test_concurrent_job_writes_and_claims_in_separate_processes_lose_no_update(tmp_path: Path, lock_holder):
    """几个进程各自反复写自己的 job、另一个进程逐个认领其余 job，全部同时进行：结束后每个 job 都是它最后一次写的值，每个认领都在
    （running、带认领时刻），认领计数等于认领次数，建 run 时写下的附加键仍在。前台 job 写与认领若不互斥，一方的读改写会用旧文件
    覆盖另一方刚写下的结果。"""
    updated = [f"u{i}" for i in range(3)]
    claimed = [f"c{i}" for i in range(40)]
    times = 150
    store = LocalRunStore(tmp_path / "runs", detached=True, lock_holder=lock_holder)
    store.create_run(_meta("r", updated + claimed), _pending("r", updated + claimed))

    outs = _run_together(tmp_path, [{"role": "update", "run_id": "r", "scope_id": sid, "times": times} for sid in updated]
                         + [{"role": "claim", "run_id": "r", "scope_ids": claimed}])
    claims = json.loads(outs[-1])
    assert claims["results"] == [True] * len(claimed)
    # 用例确实形成了交错：第一次与最后一次认领之后看到的 job 写不同，说明认领期间 job 写在持续落下
    assert any(claims["first"][sid] != claims["last"][sid] for sid in updated), claims
    state = store.load_run_state("r")
    for sid in updated:
        assert state.jobs[sid] == JobState(sid, Status.RUNNING, session_id=f"{sid}-{times - 1}"), state.jobs[sid]
    for sid in claimed:
        assert state.jobs[sid] == JobState(sid, Status.RUNNING, claimed_at="2026-11-15T00:00:00Z"), state.jobs[sid]
    assert state.claim_count == len(claimed)
    assert json.loads((tmp_path / "runs" / "r" / "run_state.json").read_text(encoding="utf-8"))["detached"] is True


def test_terminal_status_survives_job_writes_racing_an_end_write_in_another_process(tmp_path: Path, lock_holder):
    """另一个进程在前台 job 写持续进行时以结束写把 run 记为已结束：结束后运行态仍是那次结束写写下的结果（run 级终态、ended_at 与
    说明，执行中的 job 记 aborted、还没写过的 job 记 skipped，各带那一行的说明），没有被一次读在终态之前、写在终态之后的 job 写改回
    running；结束之后的 job 写不再落下，各 job 的会话停在结束写写成时的那一次。

    每次 job 写的返回值（run 级在这次写时是否仍未结束，ADR 0054 决策五）与锁内的次序一致：每个写入进程先得到若干 True、之后一直是
    False，不会在 False 之后又得到 True；结束写写成之后才读到的那次 job 写之后的写都是 False；至少有一个写入进程两种都得到过。"""
    updated = [f"u{i}" for i in range(3)]
    times = 300
    route = "settle-advancer-exited"
    ending = RUN_ENDINGS[route]
    store = LocalRunStore(tmp_path / "runs", lock_holder=lock_holder)
    store.create_run(_meta("r", updated), _pending("r", updated))

    outs = _run_together(tmp_path, [{"role": "update", "run_id": "r", "scope_id": sid, "times": times} for sid in updated]
                         + [{"role": "end", "run_id": "r", "delay": 0.05, "route": route}])
    ended = json.loads(outs[-1])
    assert ended["ok"] is True
    # 用例确实形成了交错：结束写写成的那一刻还有 job 写没有落完
    assert any(ended["seen"][sid] != f"{sid}-{times - 1}" for sid in updated), ended
    state = store.load_run_state("r")
    assert (state.status, state.ended_at, state.message) == (Status.ABORTED, "2026-11-15T01:00:00Z", ending.run_message)
    for sid in updated:
        seen = ended["seen"][sid]
        expected = (Status.ABORTED, ending.aborted_message) if seen is not None else (Status.SKIPPED, ending.skipped_message)
        assert (state.jobs[sid].status, state.jobs[sid].message) == expected, state.jobs[sid]
        assert state.jobs[sid].session_id == seen

    returns = {sid: json.loads(out) for sid, out in zip(updated, outs[:-1])}
    for sid, got in returns.items():
        assert len(got) == times
        still_open = got.index(False) if False in got else times
        assert got == [True] * still_open + [False] * (times - still_open), (sid, got)
        seen = ended["seen"][sid]  # 结束写写成之后读到的这个 job 的最后一次写；之后的写都落在结束写之后
        after = 0 if seen is None else int(seen.rsplit("-", 1)[1]) + 1
        assert all(r is False for r in got[after:]), (sid, seen, got)
    assert any(True in got and False in got for got in returns.values()), returns


# ---------- 读到「不存在」即这个 run 不存在（ADR 0030 决定四「local 读到『不存在』即这个 run 不存在」条） ----------

class _CloseAtOnce:
    """建 run 用的持有者：收到持锁的描述符即关闭。这里的用例只要记录，不要生命期锁，几百个 run 也不占着描述符。"""

    def hold(self, fd: int) -> None:
        os.close(fd)


@pytest.mark.parametrize("occupant", ["deleted", "file"])
def test_entries_by_identifier_read_a_vanished_run_directory_as_no_run(tmp_path: Path, occupant: str):
    """run 目录已被删去、或同名的换成了一个文件：读运行定义、版本头与运行态都返回 None，条件写入口都写不成，执行中的写与带结果的终态写照
    「运行态不存在」报错；不抛「不存在」之外的错误，报告目录里什么都不多出来（不为不存在的 run 建锁文件），占位的文件逐字节不变。"""
    root = tmp_path / "runs"
    store = LocalRunStore(root, lock_holder=_CloseAtOnce())
    meta, state = _meta("r", ["a"]), _pending("r", ["a"])
    store.create_run(meta, state)
    import shutil
    shutil.rmtree(root / "r")
    if occupant == "file":
        (root / "r").write_bytes(b"not a run")
    before = _snapshot(root)
    assert store.load_run_meta("r") is None
    assert store.peek_definition_header("r") is None
    assert store.load_run_state("r") is None
    assert store.try_claim_job("r", "a") is False
    assert store.project_state("r", state) is False
    assert store.end_run("r", RUN_ENDINGS["settle-advancer-exited"], ended_at="t") is False
    with pytest.raises(FileNotFoundError):
        store.update_job_state("r", JobState("a", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        store.commit_job_states("r", [JobState("a", Status.PASSED)], ended_at="t")
    assert store.list_runs([Status.PENDING, Status.RUNNING], limit=None) == []
    assert _snapshot(root) == before


def test_reading_runs_while_they_are_being_deleted_never_fails_on_a_vanished_run(tmp_path: Path):
    """一个线程逐个删去 run 目录，同时另一个线程反复列举、对列出的每个 run 读运行定义、版本头与运行态：列举与按标识的读遇到列举之后
    被删去的 run 都读作不存在（略过、None），不抛出。用例确实形成了交错：至少有一次列出的 run 在随后的读里已不在。先查是否存在再打开
    的读法在这里会偶发以 FileNotFoundError 失败（查与开之间目录被删去）。"""
    import shutil
    import threading

    root = tmp_path / "runs"
    store = LocalRunStore(root, lock_holder=_CloseAtOnce())
    vanished_after_listing = 0
    for round_ in range(20):
        ids = [f"r{round_:02d}-{i:03d}" for i in range(120)]
        for run_id in ids:
            store.create_run(_meta(run_id, ["a"]), _pending(run_id, ["a"]))
        deleter = threading.Thread(target=lambda: [shutil.rmtree(root / run_id) for run_id in ids])
        deleter.start()
        try:
            while True:
                rows = store.list_runs([Status.PENDING, Status.RUNNING], limit=None)
                for row in rows:
                    meta = store.load_run_meta(row.run_id)
                    header = store.peek_definition_header(row.run_id)
                    state = store.load_run_state(row.run_id)
                    if meta is None or header is None or state is None:
                        vanished_after_listing += 1
                if not rows and not deleter.is_alive():
                    break
        finally:
            deleter.join(timeout=_TIMEOUT_S)
        assert os.listdir(root) == []
    assert vanished_after_listing > 0


def test_a_write_entry_meeting_a_directory_that_is_being_removed_reads_it_as_no_run(tmp_path: Path):
    """另一个线程反复建出同名的 run 目录（里面是一份已结束的运行态）、再删去，同时反复做结束写与认领：打开短锁的锁文件那一步、锁内
    读运行态那一步遇到正被删去的目录时都读作 run 不存在，写不成，不抛出（macOS 的 APFS 上建出锁文件的那次打开可能得到 EINVAL 而不是
    ENOENT，见 `LocalRunStore._open_lock_file`）。运行态已结束，所以两个写入口在读到它时也不写：这里只核打开与读。先查运行态是否存在
    再打开、或把 EINVAL 原样抛出，在这里都会偶发失败。"""
    import shutil
    import threading

    from gherkai_core.serialize import run_state_to_dict

    root = tmp_path / "runs"
    root.mkdir()
    store = LocalRunStore(root)
    ended = json.dumps(run_state_to_dict(RunState(run_id="r", status=Status.PASSED, jobs={"a": JobState("a", Status.PASSED)},
                                                  started_at="t0", ended_at="t1")))
    stop = threading.Event()

    def churn():
        # 先在别的名字下备好完整的目录，再改名到位：读的一方看不到写了一半的运行态
        while not stop.is_set():
            shutil.rmtree(root / ".prep", ignore_errors=True)
            try:
                os.mkdir(root / ".prep")
                (root / ".prep" / "run_state.json").write_text(ended, encoding="utf-8")
                os.rename(root / ".prep", root / "r")
            except OSError:
                pass
            shutil.rmtree(root / "r", ignore_errors=True)

    churner = threading.Thread(target=churn)
    churner.start()
    try:
        for _ in range(20000):
            assert store.end_run("r", RUN_ENDINGS["settle-advancer-exited"], ended_at="t") is False
            assert store.try_claim_job("r", "a", claimed_at="t") is False
    finally:
        stop.set()
        churner.join(timeout=_TIMEOUT_S)


def test_an_end_write_overlapping_the_removal_of_its_run_directory_reads_as_no_run(tmp_path: Path):
    """同上一条的布置，但运行态没有结束：结束写真的会写（建临时文件、改名），这两步与另一个线程删去 run 目录真实重叠。每一次结束写
    的结果只有三种：写成；读到 run 不存在而写不成；写的中途目录已不在，以「不存在」抛出。macOS 的 APFS 上这两步在正被删去的目录里
    可能得到 EINVAL（见 `_atomic.hit_vanished_dir`），原样抛出的话处置方会把「run 已被删去」当成读写记录失败。"""
    import shutil
    import threading

    from gherkai_core.serialize import run_state_to_dict

    root = tmp_path / "runs"
    root.mkdir()
    store = LocalRunStore(root)
    running = json.dumps(run_state_to_dict(RunState(run_id="r", status=Status.RUNNING, jobs={"a": JobState("a", Status.RUNNING)},
                                                    started_at="t0")))
    stop = threading.Event()

    def churn():
        while not stop.is_set():
            shutil.rmtree(root / ".prep", ignore_errors=True)
            try:
                os.mkdir(root / ".prep")
                (root / ".prep" / "run_state.json").write_text(running, encoding="utf-8")
                os.rename(root / ".prep", root / "r")
            except OSError:
                pass
            shutil.rmtree(root / "r", ignore_errors=True)

    outcomes = {"written": 0, "no-run": 0, "vanished": 0}
    churner = threading.Thread(target=churn)
    churner.start()
    try:
        for _ in range(20000):
            try:
                wrote = store.end_run("r", RUN_ENDINGS["settle-advancer-exited"], ended_at="t")
            except (FileNotFoundError, NotADirectoryError):
                outcomes["vanished"] += 1
            else:
                outcomes["written" if wrote else "no-run"] += 1
    finally:
        stop.set()
        churner.join(timeout=_TIMEOUT_S)
    assert outcomes["written"] > 0 and outcomes["no-run"] > 0, outcomes


@pytest.mark.parametrize("case", ["removed-then-real-open", "removed-then-einval", "still-there-einval"])
def test_a_run_directory_removed_right_before_the_lock_file_is_opened_reads_as_no_run(tmp_path: Path, monkeypatch, case: str):
    """建 run 之后的写入口打开短锁的锁文件那一刻 run 目录已被删去：真实的打开得到「不存在」，或（macOS 的 APFS 上可能的）EINVAL，都读作
    run 不存在：结束写与认领写不成，执行中的写照「运行态不存在」报错，什么都不建出。目录还在而打开以 EINVAL 失败时原样抛出，不吞成
    「不存在」，运行态逐字节不变。注入只换那一次打开：按 case 先真的删去 run 目录，再照常打开或以同步的系统错误失败。"""
    import builtins
    import shutil

    from gherkai_core.adapters.run_store import local as local_mod

    root = tmp_path / "runs"
    store = LocalRunStore(root, lock_holder=_CloseAtOnce())
    real_open = builtins.open

    def open_(path, *args, **kwargs):
        if os.fspath(path).endswith(".runstate.lock"):
            if case != "still-there-einval":
                shutil.rmtree(root / "r")
            if case != "removed-then-real-open":
                raise OSError(errno.EINVAL, os.strerror(errno.EINVAL), os.fspath(path))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(local_mod, "open", open_, raising=False)
    writes = [lambda: store.end_run("r", RUN_ENDINGS["settle-advancer-exited"], ended_at="t"),
              lambda: store.try_claim_job("r", "a", claimed_at="t"),
              lambda: store.update_job_state("r", JobState("a", Status.RUNNING))]
    for write in writes:
        store.create_run(_meta("r", ["a"]), _pending("r", ["a"]))
        before = (root / "r" / "run_state.json").read_bytes()
        if case == "still-there-einval":
            with pytest.raises(OSError) as exc:
                write()
            assert exc.value.errno == errno.EINVAL
            assert (root / "r" / "run_state.json").read_bytes() == before
            shutil.rmtree(root / "r")
        elif write is writes[2]:
            with pytest.raises(FileNotFoundError):
                write()
        else:
            assert write() is False
        assert os.listdir(root) == []


@pytest.mark.parametrize("reader", ["load_run_meta", "peek_definition_header", "load_run_state", "list_runs-state",
                                    "list_runs-header"])
def test_a_run_directory_removed_right_before_a_record_is_read_reads_as_no_run(tmp_path: Path, monkeypatch, reader: str):
    """读记录文件的那一刻 run 目录已被删去：读运行定义、版本头与运行态都返回 None；列举时读运行态得到「不存在」即略过这一项，读版本头
    得到「不存在」时这一项照列、头部为空（与没有 run_meta.json 的 run 同一读法，ADR 0041 决策七「读不到为空」），别的 run 照常列出；
    都不抛出。注入只换文件读取这一步：先真的删去 run 目录，再照常读。"""
    import shutil

    root = tmp_path / "runs"
    store = LocalRunStore(root, lock_holder=_CloseAtOnce())
    for run_id in ("r", "s"):
        store.create_run(_meta(run_id, ["a"]), _pending(run_id, ["a"]))
    target = "run_state.json" if reader in ("load_run_state", "list_runs-state") else "run_meta.json"
    real_read_text, real_read_bytes = Path.read_text, Path.read_bytes
    armed = [True]

    def remove_first(path: Path) -> None:
        if armed[0] and path.name == target and path.parent == root / "r":
            armed[0] = False
            shutil.rmtree(root / "r")

    def read_text(self, *args, **kwargs):
        remove_first(self)
        return real_read_text(self, *args, **kwargs)

    def read_bytes(self):
        remove_first(self)
        return real_read_bytes(self)

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    if reader.startswith("list_runs"):
        rows = {row.run_id: row for row in store.list_runs([Status.PENDING, Status.RUNNING], limit=None)}
        if reader == "list_runs-state":
            assert list(rows) == ["s"]
        else:
            assert sorted(rows) == ["r", "s"] and rows["r"].header is None and rows["r"].state == _pending("r", ["a"])
        assert rows["s"].header is not None
    else:
        assert getattr(store, reader)("r") is None
    assert armed == [False]  # 注入确实发生了
    assert os.listdir(root) == ["s"]
