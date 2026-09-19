"""LocalResultStore 写面的原子性（ADR 0042 决策四 / 0034）：`explain` 被允许在 run 运行到一半时读
jobs/<scope>.json（另一个进程），而写者可能正在重写同一文件——同步 run 逐 job 写，无状态批量运行下两个推进者
（per-run 进程 + `status --wait` 接力）又会各写一遍全部 jobs/*.json，写面无跨进程锁。写必须 tmp+rename，
读者绝不能看到空/半截 JSON（撞上就是 explain 的裸 traceback）。

真起子进程读、不 mock（绿≠对：进程间文件可见性是 mock 之外的真实行为）。对照实验（同一读者 + `write_text`
写法）在本机能稳定观测到读到空文件，故本用例对「回退成 write_text」有判别力。
"""
from __future__ import annotations

import json
import subprocess
import sys

from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.model import Job, JobResult, ReportRef, ScenarioResult, Status, StepResult

_READER = r"""
import json, sys, pathlib
p = pathlib.Path(sys.argv[1]); stop = pathlib.Path(sys.argv[2])
reads = empty = unparsable = 0
while not stop.exists():
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        continue
    reads += 1
    if raw == "":
        empty += 1
        continue
    try:
        json.loads(raw)
    except ValueError:
        unparsable += 1
print(json.dumps({"reads": reads, "empty": empty, "unparsable": unparsable}))
"""

_SCOPE = "features/checkout.feature:12"


def _big_job_result(tick: int) -> JobResult:
    """~几十 KB 的 JobResult（6 scenario × 8 step + 每 step 的 evidence ref 与失败原文），给读者足够撞窗机会。"""
    job = Job(scope_id=_SCOPE, scope_name="结账", engine="novaact", scenarios=())
    scenarios = [
        ScenarioResult(
            scenario_id=f"下单-{si}",
            status=Status.FAILED,
            duration_ms=1234.5,
            steps=[
                StepResult(
                    index=k,
                    status=Status.FAILED,
                    duration_ms=float(k),
                    error_type="assertion_failed",
                    message=f"tick={tick} 第 {si}/{k} 步断言未过：" + "证据原文 " * 40,
                    report_refs=(
                        ReportRef(kind="evidence", ref=f"file:///tmp/ev-{si}-{k}.json", label="步骤证据"),
                        ReportRef(kind="trajectory", ref=f"file:///tmp/tr-{si}-{k}.html", label="轨迹"),
                    ),
                )
                for k in range(8)
            ],
        )
        for si in range(6)
    ]
    return JobResult(job=job, status=Status.FAILED, scenarios=scenarios, session_id=f"s-{tick}",
                     total_time_worked_s=12.5, duration_ms=99999.0, error_type=None, message=None)


def test_concurrent_reader_never_sees_torn_job_result(tmp_path):
    store = LocalResultStore(tmp_path / "runs")
    run_id = "run-result-atomic"
    store.save_job_result(run_id, _big_job_result(0))  # 先落一份，让读者从第一拍就有文件可读
    jobs_dir = tmp_path / "runs" / run_id / "jobs"
    path = next(iter(jobs_dir.glob("*.json")))
    assert path.stat().st_size > 20_000, path.stat().st_size  # 单文件够大才有撞窗机会（否则用例无判别力）
    stop = tmp_path / "stop"
    reader = subprocess.Popen([sys.executable, "-c", _READER, str(path), str(stop)],
                              stdout=subprocess.PIPE, text=True)
    try:
        for tick in range(1, 300):
            store.save_job_result(run_id, _big_job_result(tick))
    finally:
        stop.touch()
        out, _ = reader.communicate(timeout=30)
    stats = json.loads(out)
    assert stats["reads"] >= 10, stats  # 读者确实在写的期间反复读到了（否则本用例空转）
    assert stats["empty"] == 0, stats       # truncate 窗口：write_text 写法在此处会计出非 0
    assert stats["unparsable"] == 0, stats  # 半截 JSON
    # 读回是最后一次写的完整态；目录里无 tmp 残留、读回面不把 tmp 当 job
    assert store.load_job_result(run_id, _SCOPE).session_id == "s-299"
    assert not list(jobs_dir.glob("*.tmp"))
    assert len(store.load_all(run_id)) == 1
    assert [p.name for p in sorted(jobs_dir.iterdir())] == [path.name]


def test_job_result_file_stays_readable_by_others(tmp_path):
    """判定真值的消费者是 CI/人（ADR 0034 表）：原子写用的临时文件是 0600，落盘后必须仍是可被别的用户读的权限。"""
    store = LocalResultStore(tmp_path / "runs")
    store.save_job_result("run-perm", _big_job_result(0))
    path = next(iter((tmp_path / "runs" / "run-perm" / "jobs").glob("*.json")))
    mode = path.stat().st_mode & 0o777
    assert mode & 0o044, oct(mode)  # group/other 可读（别被 mkstemp 的 0600 悄悄收窄）
