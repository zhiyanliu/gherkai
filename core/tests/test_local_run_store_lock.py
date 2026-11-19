"""LocalRunStore 写入口的互斥与条件建 run（ADR 0030 决定三、ADR 0054 决策五），真起子进程、不 mock。

本机的写入口（create_run、update_job_state、try_claim_job、project_state、commit_job_states、end_run）都在 run 目录下
同一把 fcntl 文件锁内读改写，除 create_run 之外都经同一个锁内读改写的路径（`LocalRunStore._locked_rmw`）。锁跨进程是否真的互斥、读改写之间是否真的没有别的写插进来，是 mock 之外的真实行为（绿≠对），所以并发的结论用多个真实
进程核对：各进程先就绪、再同时放行，各自按角色反复写，结束后检查没有任何一次写丢失、终态没有被改回，并核对这次确实形成了
交错（否则用例空转）。把锁换成空操作时，三个并发用例在本机每次都失败，失败的形态有：job 写与认领丢失、终态被一次读在终态之前的
job 写改回 running、同一个 run 被几个进程都建成。
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.run_status import RUN_ENDINGS

_TIMEOUT_S = 120

# 子进程：先写就绪文件，再等放行文件出现，然后按角色写。只用 ASCII，参数经一个 JSON 串传入
_WORKER = r"""
import json, sys, time, pathlib
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
a = json.loads(sys.argv[1])
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
        except FileExistsError:
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


# ---------- 建 run 只在 run 目录里还没有运行态时成立 ----------

def test_create_run_on_an_existing_run_leaves_both_files_byte_identical(tmp_path: Path):
    """再建同一个 run 抛 FileExistsError，run_meta.json 与 run_state.json 逐字节不变（再建时给的 definition 与初始运行态都不同，
    被重写就一定看得出来）；后台执行标记也不因再建的实例带 detached 而出现或消失。"""
    store = LocalRunStore(tmp_path / "runs")
    store.create_run(_meta("r", ["a"]), _pending("r", ["a"]))
    assert store.try_claim_job("r", "a") is True
    run_dir = tmp_path / "runs" / "r"
    before = {name: (run_dir / name).read_bytes() for name in ("run_meta.json", "run_state.json")}

    for again in (LocalRunStore(tmp_path / "runs"), LocalRunStore(tmp_path / "runs", detached=True)):
        try:
            again.create_run(_meta("r", ["x", "y"], created_at="2099-01-01T00:00:00Z"), _pending("r", ["x", "y"]))
        except FileExistsError:
            pass
        else:
            raise AssertionError("对已有的 run 再建应当失败")
        assert {name: (run_dir / name).read_bytes() for name in before} == before


def test_create_run_proceeds_while_the_run_directory_has_no_run_state(tmp_path: Path):
    """判据只看运行态文件：目录里只有 definition（上一次建 run 在两次写之间中断）或只有别的产物时照常建成，definition 被这次的
    内容替换。"""
    store = LocalRunStore(tmp_path / "runs")
    store.create_run(_meta("r", ["a"]), _pending("r", ["a"]))
    (tmp_path / "runs" / "r" / "run_state.json").unlink()
    store.create_run(_meta("r", ["b"]), _pending("r", ["b"]))
    assert [j.scope_id for j in store.load_run_meta("r").jobs] == ["b"]
    assert set(store.load_run_state("r").jobs) == {"b"}

    (tmp_path / "runs" / "other").mkdir()
    (tmp_path / "runs" / "other" / "worker.log").write_text("x", encoding="utf-8")
    store.create_run(_meta("other", ["a"]), _pending("other", ["a"]))
    assert store.load_run_state("other").claim_count == 0


def test_concurrent_creates_of_one_run_in_separate_processes_have_exactly_one_winner(tmp_path: Path):
    """多个进程同时依次建同一批 run：每个 run 恰有一个进程建成，其余得到「已存在」；落盘的 definition 与运行态出自同一个进程
    （建成者的标记）。一批多个 run 是为了让竞争反复发生。"""
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


# ---------- 写入口在文件锁内互斥 ----------

def test_concurrent_job_writes_and_claims_in_separate_processes_lose_no_update(tmp_path: Path):
    """几个进程各自反复写自己的 job、另一个进程逐个认领其余 job，全部同时进行：结束后每个 job 都是它最后一次写的值，每个认领都在
    （running、带认领时刻），认领计数等于认领次数，建 run 时写下的附加键仍在。前台 job 写与认领若不互斥，一方的读改写会用旧文件
    覆盖另一方刚写下的结果。"""
    updated = [f"u{i}" for i in range(3)]
    claimed = [f"c{i}" for i in range(40)]
    times = 150
    store = LocalRunStore(tmp_path / "runs", detached=True)
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
    assert store.is_detached("r") is True


def test_terminal_status_survives_job_writes_racing_an_end_write_in_another_process(tmp_path: Path):
    """另一个进程在前台 job 写持续进行时以结束写把 run 记为已结束：结束后运行态仍是那次结束写写下的结果（run 级终态、ended_at 与
    说明，执行中的 job 记 aborted、还没写过的 job 记 skipped，各带那一行的说明），没有被一次读在终态之前、写在终态之后的 job 写改回
    running；结束之后的 job 写不再落下，各 job 的会话停在结束写写成时的那一次。

    每次 job 写的返回值（run 级在这次写时是否仍未结束，ADR 0054 决策五）与锁内的次序一致：每个写入进程先得到若干 True、之后一直是
    False，不会在 False 之后又得到 True；结束写写成之后才读到的那次 job 写之后的写都是 False；至少有一个写入进程两种都得到过。"""
    updated = [f"u{i}" for i in range(3)]
    times = 300
    route = "settle-advancer-exited"
    ending = RUN_ENDINGS[route]
    store = LocalRunStore(tmp_path / "runs")
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
