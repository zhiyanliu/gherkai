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
                     started_at=state.started_at, ended_at=state.ended_at,
                     high_water_mark=state.high_water_mark)  # 保留（同步路径恒 None；无状态路径不走此方法）
        )

    def finalize_run(self, run_id: str, status: Status, ended_at: str) -> None:
        """commit point：写总 status + ended_at（各 job 态此前已由 update_job_state 刷过）。"""
        state = self.load_run_state(run_id)
        if state is None:
            raise FileNotFoundError(f"finalize_run：run_state 不存在（须先 create_run）：{run_id}")
        # ended_at 直传（不写 `or None`）：签名是 str、finalize 语义就是落一个具体 ended_at；
        # 用 falsy 兜会把合法空串静默吞成 None（omit-when-None 后键消失，已 finalize 的 run 看似未 finalize）。
        self._write_state(
            RunState(run_id=state.run_id, status=status, jobs=state.jobs,
                     started_at=state.started_at, ended_at=ended_at,
                     high_water_mark=state.high_water_mark)  # 保留（同步路径恒 None）
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

    def preflight(self) -> None:
        """探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。"""

    # ---- 无状态跑批的条件写三方（ADR 0034）----
    # 与上面 update_job_state/finalize_run（同步 run 路径、依赖 RunPersistence 进程内锁）并存、职责不同：
    # 无状态跑批下多进程并发写（per-run 进程 + status --wait 接力），进程内锁跨不了进程边界，故这三方
    # 用 **fcntl 文件锁**（跨进程互斥）把「读 run_state.json → 判条件 → 写回」整段串成原子 RMW。
    # local 落地即校验条件写逻辑（P2 单测），cloud DDB 用条件表达式复刻同一语义（P4）。

    def _locked_rmw(self, run_id: str, mutate) -> bool:
        """在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→
        (新 state | None)；None=条件不满足不写、返回 False；否则写回、返回 True。state 不存在 → False。"""
        import fcntl

        path = self._root / run_id / "run_state.json"
        if not path.exists():
            return False
        # 锁一个专用 .lock 文件（不锁 json 本身，避免 truncate/rename 与锁交互的坑）；跨进程互斥。
        lock_path = self._root / run_id / ".runstate.lock"
        with open(lock_path, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                state = self.load_run_state(run_id)
                if state is None:
                    return False
                new_state = mutate(state)
                if new_state is None:
                    return False
                self._write_state(new_state)
                return True
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)

    def try_claim_job(self, run_id: str, scope_id: str) -> bool:
        """CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）。"""
        def mutate(state: RunState):
            js = state.jobs.get(scope_id)
            if js is None or js.status != Status.PENDING:
                return None  # 不存在 / 已非 pending（别人抢了或已跑）→ 不改
            jobs = dict(state.jobs)
            jobs[scope_id] = JobState(scope_id=scope_id, status=Status.RUNNING, session_id=js.session_id)
            return RunState(run_id=state.run_id, status=state.status, jobs=jobs,
                            started_at=state.started_at, ended_at=state.ended_at,
                            high_water_mark=state.high_water_mark)
        return self._locked_rmw(run_id, mutate)

    def project_state(self, run_id: str, state: RunState) -> bool:
        """HWM 条件写整个 RunState：仅当传入 hwm ≥ 库中 hwm 才写（机制三，挡 stale 覆盖）。"""
        def mutate(cur: RunState):
            cur_hwm = cur.high_water_mark or 0
            new_hwm = state.high_water_mark or 0
            if new_hwm < cur_hwm:
                return None  # stale：读到的 events 比库里记录的少 → 挡
            return state  # 整体覆盖（reconciler 全量重放算出的完整 state）
        return self._locked_rmw(run_id, mutate)

    def try_finalize(self, run_id: str, status: Status, ended_at: str) -> bool:
        """状态机单调条件写：仅当当前总 status 为非终态才写终态（机制三，commit 恰一次）。"""
        def mutate(state: RunState):
            if state.status not in (Status.PENDING, Status.RUNNING):
                return None  # 已终态：别人已 finalize → 幂等跳过
            return RunState(run_id=state.run_id, status=status, jobs=state.jobs,
                            started_at=state.started_at, ended_at=ended_at,
                            high_water_mark=state.high_water_mark)
        return self._locked_rmw(run_id, mutate)
