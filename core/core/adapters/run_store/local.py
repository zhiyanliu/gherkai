"""LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。

三层切分（ADR 0016）：RunStore 存**控制面**——`RunMeta`（definition：run_id/created_at/跑哪些 job，
执行前确定）+ `RunState`（运行态：总 status/各 job status/血缘，执行后产生）。**不存判定明细**
（那是数据面、由 ResultStore 持有，避免与 jobs/*.json 冗余真值）。

**跨文件读取契约（消解"信哪个"困惑）**：
- definition 唯一真值在 run_meta.json。jobs/*.json 内嵌的 job def 是其**自包含副本**——非独立维护的第二真值、
  不会漂移（两处都序列化同一次 plan 产出的同一个 Job 对象，共用 serialize.job_to_dict）。嵌它是为让 CI 读
  单 scope 不依赖 run_meta（上云对象存储按 key 取单 job 同理）。
- **判定真值唯一权威 = jobs/*.json（数据面 ResultStore）**。run_state.json 的 status / 各 job status 是
  **控制面投影摘要**（供 exit-code / 未来轮询续跑 / WebUI 进度），与 jobs/*.json 同源（均从同一 RunResult
  投影，不双写漂移）。要权威判定读 jobs/*.json；要快速总览/轮询读 run_state.json。

**克制（ADR 0016）**：只忠实持久化已成形的 RunMeta/RunState（复用 serialize），**不发明** jobId/起止
时刻/DDB 表/执行中实时更新读取面那些有意 defer 的字段——待真实续跑/轮询/WebUI 需求逼出再加。
落点与 LocalReportStore 对齐（同 `<root>/<run_id>/`）：run_meta.json + run_state.json。
"""
from __future__ import annotations

import json
from pathlib import Path

from core.model import JobState, RunMeta, RunState, Status
from core.serialize import (
    run_meta_from_dict,
    run_meta_to_dict,
    run_state_from_dict,
    run_state_to_dict,
)


class LocalRunStore:
    """RunStore 的本地文件实现（组合根注入；未来 DDB 版换落点/读写）。"""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _write_state(self, state: RunState) -> None:
        run_dir = self._root / state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run_state.json").write_text(
            json.dumps(run_state_to_dict(state), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def save_run(self, meta: RunMeta, state: RunState) -> None:
        """落 <root>/<run_id>/{run_meta.json, run_state.json}（一次性写完整态，写面）。"""
        run_dir = self._root / meta.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run_meta.json").write_text(
            json.dumps(run_meta_to_dict(meta), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._write_state(state)

    # ---- 实时写三段（ADR 0030）----
    # 注：update_job_state / finalize_run 是「读 run_state.json → 改 → 写回」的 read-modify-write，
    # **非自身线程安全**——依赖调用方串行（RunPersistence 的单一 store 锁，ADR 0030 决定三）。本地小文件，RMW 开销可忽略。

    def create_run(self, meta: RunMeta, initial_state: RunState) -> None:
        """run 开始：写 definition（run_meta.json）+ 初始运行态（run_state.json，各 job 一般为 pending）。
        语义同 save_run，但意图是「生命周期起点」（与 finalize_run 配对）。"""
        self.save_run(meta, initial_state)

    def update_job_state(self, run_id: str, job_state: JobState) -> None:
        """按 scope_id 刷单个 job 的运行态（Map upsert）。run_state.json 不存在则报错（须先 create_run）。"""
        state = self.load_run_state(run_id)
        if state is None:
            raise FileNotFoundError(f"update_job_state：run_state 不存在（须先 create_run）：{run_id}")
        jobs = dict(state.jobs)
        jobs[job_state.scope_id] = job_state  # Map 定位：各 scope 互不干扰
        self._write_state(
            RunState(run_id=state.run_id, status=state.status, jobs=jobs,
                     started_at=state.started_at, ended_at=state.ended_at)
        )

    def finalize_run(self, run_id: str, status: Status, ended_at: str) -> None:
        """commit point：写总 status + ended_at（各 job 态此前已由 update_job_state 刷过）。"""
        state = self.load_run_state(run_id)
        if state is None:
            raise FileNotFoundError(f"finalize_run：run_state 不存在（须先 create_run）：{run_id}")
        self._write_state(
            RunState(run_id=state.run_id, status=status, jobs=state.jobs,
                     started_at=state.started_at, ended_at=ended_at or None)
        )

    def load_run_meta(self, run_id: str) -> RunMeta | None:
        """读回 definition（RunMeta）；不存在返回 None。"""
        path = self._root / run_id / "run_meta.json"
        if not path.exists():
            return None
        return run_meta_from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_run_state(self, run_id: str) -> RunState | None:
        """读回运行态（RunState）；不存在返回 None。"""
        path = self._root / run_id / "run_state.json"
        if not path.exists():
            return None
        return run_state_from_dict(json.loads(path.read_text(encoding="utf-8")))
