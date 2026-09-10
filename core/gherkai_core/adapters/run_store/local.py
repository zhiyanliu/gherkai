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

**克制（ADR 0016）**：只忠实持久化已成形的 RunMeta/RunState（复用 serialize），**不发明 serialize 之外的字段**。
已落地（ADR 0030 决定四/六）：起止时刻（started_at/ended_at）、实时写三段（create_run / update_job_state /
finalize_run）+ 读回面（load_run_state，`status` 与 tick 的 baseline 都靠它）、DDB 实装（同包 `ddb.py`）。
仍有意 defer：jobId、续跑/部分重跑的 attempt 维度（ADR 0030「留口子」）——待真实需求逼出再加。
落点与 LocalReportStore 对齐（同 `<root>/<run_id>/`）：run_meta.json + run_state.json。
"""
from __future__ import annotations

import json
import tempfile
import os
import contextlib
from pathlib import Path

from gherkai_core.model import JobState, RunMeta, RunState, Status
from gherkai_core.serialize import (
    run_meta_from_dict,
    run_meta_to_dict,
    run_state_from_dict,
    run_state_to_dict,
)



def _atomic_write_json(path: Path, obj) -> None:
    """同目录 tmp + `os.replace`：读者要么看到旧文件、要么看到新文件，绝不看到半截/空 JSON。

    并发读者真实存在（ADR 0030 决定四/0034）：per-run 推进进程在 `_locked_rmw` 里写 run_state.json 时，
    `gherkai status` / 接力进程**无锁**读同一文件（读面不持 `.runstate.lock`，只写面互斥）；`write_text` 是
    truncate 再写，两步之间的读者会拿到空文件或前半截、json.loads 直接炸。tmp 与目标同目录保证 rename 同分区原子。
    """
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False, indent=2))
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise

class LocalRunStore:
    """RunStore 的本地文件实现（组合根注入；DDB 实装见同包 `ddb.py`）。"""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _write_state(self, state: RunState) -> None:
        run_dir = self._root / state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(run_dir / "run_state.json", run_state_to_dict(state))

    def save_run(self, meta: RunMeta, state: RunState) -> None:
        """落 <root>/<run_id>/{run_meta.json, run_state.json}（一次性写完整态，写面）。"""
        run_dir = self._root / meta.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(run_dir / "run_meta.json", run_meta_to_dict(meta))
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
    # local 落地即校验条件写逻辑（单测），cloud DDB 用条件表达式复刻同一语义。

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

    def try_claim_job(self, run_id: str, scope_id: str, *, claimed_at: str | None = None) -> bool:
        """CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）；随写 claimed_at（timeout 起算点）。"""
        def mutate(state: RunState):
            js = state.jobs.get(scope_id)
            if js is None or js.status != Status.PENDING:
                return None  # 不存在 / 已非 pending（别人抢了或已跑）→ 不改
            jobs = dict(state.jobs)
            jobs[scope_id] = JobState(scope_id=scope_id, status=Status.RUNNING, session_id=js.session_id,
                                      claimed_at=claimed_at)
            return RunState(run_id=state.run_id, status=state.status, jobs=jobs,
                            started_at=state.started_at, ended_at=state.ended_at,
                            high_water_mark=state.high_water_mark)
        return self._locked_rmw(run_id, mutate)

    def project_state(self, run_id: str, state: RunState) -> bool:
        """HWM 条件写 RunState：仅当传入 hwm ≥ 库中 hwm 才写（机制三①，挡 stale 覆盖）。

        **run 级 status 钳为 pending/running、不落终态**（ADR 0030：run 级终态是 finalize 的 commit point
        专属；若投影提前落终态，try_finalize 会被自己刚写的终态挡住）。取值规则见 `projected_run_status`
        （与 ddb adapter 共用一份）。已 finalize（库中 status 已终态）→ 挡。

        **各 job 态与库中现态按生命周期序逐 job 单调合并（机制三②的 job 级半边）**：task_exited 走独立
        键空间、不带数值 seq，「被 scope_done 触发」与「被 task_exited 触发」的投影可携带相同 HWM——
        ① 挡不住 stale 实例把已终态的 job 刷回 running（并发实例对某 scope 视图旧、对另一 scope 视图新时
        HWM 相等）。逐 job 取较推进者：终态不被 running/pending 覆盖、running 不被 pending 覆盖（防已
        claim 被刷回 → 重复 launch，机制四）。"""
        from gherkai_core.project import _lifecycle_rank, projected_run_status

        def mutate(cur: RunState):
            cur_hwm = cur.high_water_mark or 0
            new_hwm = state.high_water_mark or 0
            if new_hwm < cur_hwm:
                return None  # stale：读到的 events 比库里记录的少 → 挡（机制三①）
            if cur.status not in (Status.PENDING, Status.RUNNING):
                return None  # 已 finalize 终态：不被投影刷回（机制三 finalize 单调的对偶保护）
            # 机制三② job 级：逐 job 与库中现态取较推进者（同 rank 取新值——终态间以本次投影为准）
            jobs: dict[str, JobState] = dict(cur.jobs)  # 从库中现态出发：投影没带的 job 原样保留
            for sid, js in state.jobs.items():
                cur_js = cur.jobs.get(sid)
                if cur_js is None:
                    continue  # definition 外的 scope（不该发生：project 只吐 meta.jobs 的键）→ 不臆造，与 DDB 的 CCF 跳过对拍
                if _lifecycle_rank(cur_js.status) > _lifecycle_rank(js.status):
                    jobs[sid] = cur_js  # 库中更推进（已终态/已 claim）→ 保留，不回退
                else:
                    # 血缘/claim 时刻不丢：投影缺的字段回填库中值（claimed_at 只由 try_claim_job 落、
                    # 事件推演不出——正常经 project 的 baseline 带回，此处兜没带 baseline 的投影）
                    jobs[sid] = JobState(
                        scope_id=sid, status=js.status,
                        session_id=js.session_id or cur_js.session_id,
                        claimed_at=js.claimed_at or cur_js.claimed_at)
            # run 级 status 按投影里的 job 态定（全 pending → pending，否则 running）；传入的 run 级值是
            # 终态聚合值、一律不用（规则与理由见 projected_run_status）。
            return RunState(run_id=state.run_id, status=projected_run_status(state.jobs), jobs=jobs,
                            started_at=state.started_at or cur.started_at,
                            ended_at=state.ended_at, high_water_mark=state.high_water_mark)
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
