"""LocalRunStore 写面的原子性（ADR 0030 决定四 / 0034）：per-run 推进进程写 run_state.json 的同时，
`gherkai status` / 接力进程无锁读它——写必须 tmp+rename，读者绝不能看到半截/空 JSON。

真起子进程读、不 mock（绿≠对：进程间文件可见性是 mock 之外的真实行为）。对照实验（同一读者 + `write_text`
写法）在本机能稳定观测到 torn read，故本用例对「回退成 write_text」有判别力。
"""
from __future__ import annotations

import json
import subprocess
import sys

from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import JobState, RunState, Status

_READER = r"""
import json, sys, pathlib
p = pathlib.Path(sys.argv[1]); stop = pathlib.Path(sys.argv[2])
reads = torn = 0
while not stop.exists():
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        continue
    reads += 1
    try:
        json.loads(raw)
    except ValueError:
        torn += 1
print(json.dumps({"reads": reads, "torn": torn}))
"""


def _big_state(run_id: str, n_jobs: int, tick: int) -> RunState:
    jobs = {f"features/f{i}.feature:{tick}": JobState(scope_id=f"features/f{i}.feature:{tick}", status=Status.RUNNING,
                                                       session_id=f"s-{tick}-{i}", claimed_at="2026-01-01T00:00:00Z")
            for i in range(n_jobs)}
    return RunState(run_id=run_id, status=Status.RUNNING, jobs=jobs,
                    started_at="2026-01-01T00:00:00Z", ended_at=None, high_water_mark=None)


def test_concurrent_reader_never_sees_torn_run_state(tmp_path):
    store = LocalRunStore(tmp_path)
    run_id = "run-atomic"
    store._write_state(_big_state(run_id, 2000, 0))  # 先落一份，让读者从第一拍就有文件可读
    state_path = tmp_path / run_id / "run_state.json"
    stop = tmp_path / "stop"
    reader = subprocess.Popen([sys.executable, "-c", _READER, str(state_path), str(stop)],
                              stdout=subprocess.PIPE, text=True)
    try:
        for tick in range(1, 200):
            store._write_state(_big_state(run_id, 2000, tick))  # ~200KB/次，给读者足够多的撞窗机会
    finally:
        stop.touch()
        out, _ = reader.communicate(timeout=30)
    stats = json.loads(out)
    assert stats["reads"] >= 10, stats  # 读者确实在写的期间反复读到了（否则本用例空转）
    assert stats["torn"] == 0, stats
    # 读回是最后一次写的完整态、且目录里无 tmp 残留
    assert store.load_run_state(run_id).jobs["features/f0.feature:199"].session_id == "s-199-0"
    assert not list((tmp_path / run_id).glob("*.tmp"))
