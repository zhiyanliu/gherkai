"""LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。

三层切分（ADR 0016）：RunStore 存**控制面**——`RunMeta`（definition：run_id/created_at/执行哪些 job，
执行前确定）+ `RunState`（运行态：总 status/各 job status/血缘，执行后产生）。**不存判定明细**
（那是数据面、由 ResultStore 持有，避免与 jobs/*.json 冗余真值）。

**跨文件读取契约（消解"信哪个"困惑）**：
- definition 唯一真值在 run_meta.json。jobs/*.json 内嵌的 job def 是其**自包含副本**——非独立维护的第二真值、
  不会漂移（两处都序列化同一次 plan 产出的同一个 Job 对象，共用 serialize.job_to_dict）。嵌它是为让 CI 读
  单 scope 不依赖 run_meta（上云对象存储按 key 取单 job 同理）。
- **判定真值的唯一权威是 jobs/*.json（数据面 ResultStore）**。run_state.json 的 status / 各 job status 是
  **控制面投影摘要**（供 exit-code / 未来的轮询式恢复执行 / WebUI 进度），与 jobs/*.json 同源（均从同一 RunResult
  投影，不双写漂移）。要权威判定读 jobs/*.json；要快速总览/轮询读 run_state.json。

**写入口全部在同一把 fcntl 文件锁内完成读改写**（ADR 0030 决定三、ADR 0054 决策五）：create_run、update_job_state、
try_claim_job、project_state、try_finalize、commit_job_states、end_run 互斥，跨进程与进程内多线程都成立；同一个 run 的各写入方
（前台执行者、后台推进进程、`status --wait` 接力）不靠调用方串行。读面（load_run_state、list_runs、`status`）不持锁，靠原子写看到完整文件。

**顶层附加键整体保留**（ADR 0030 决定四「local 的顶层附加键整体保留」）：run_state.json 里不属于 RunState 模型的顶层键（`serialize.RUN_STATE_KEYS` 之外，
如后台执行标记 `detached`）只在 create_run 时写下，之后每个写入口从锁内读到的文件里原样带回，不逐个补回。

**克制（ADR 0016）**：只忠实持久化已成形的 RunMeta/RunState（复用 serialize），**不发明 serialize 之外的字段**。
仍有意 defer：jobId、恢复执行/部分重新执行的 attempt 维度（ADR 0030「留口子」）——待真实需求逼出再加。
落点与 LocalReportStore 对齐（同 `<root>/<run_id>/`）：run_meta.json + run_state.json（锁文件 `.runstate.lock` 同目录）。
"""
from __future__ import annotations

import json
import stat
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

from gherkai_core.adapters._atomic import atomic_write_json
from gherkai_core.model import JobState, RunListing, RunMeta, RunState, Status
from gherkai_core.run_status import CommitOutcome, RunEnding, commit_applied, ending_applied
from gherkai_core.serialize import (
    RUN_STATE_KEYS,
    definition_schema_version,
    require_listing_header,
    require_listing_state,
    run_meta_from_dict,
    run_meta_to_dict,
    run_state_from_dict,
    run_state_to_dict,
)

_STATE_FILE = "run_state.json"
_META_FILE = "run_meta.json"
# 锁一个专用文件、不锁 json 本身：原子写是 tmp 加 rename，锁在被替换掉的 inode 上就护不住下一次读改写
_LOCK_FILE = ".runstate.lock"


def _atomic_write_json(path: Path, obj) -> None:
    """控制面文件（run_meta.json / run_state.json）的原子写。

    并发读者真实存在（ADR 0030 决定三）：写入方在文件锁内写 run_state.json 时，`gherkai status` / 接力进程**无锁**读
    同一文件（读面不持 `.runstate.lock`，只写面互斥）。原子性的实现与其余两面的读者见 `gherkai_core.adapters._atomic`。

    权限收在 0600：控制面只被本机同 uid 的进程消费（`status` / 接力 / 同步 run 自己），无跨用户/跨容器读需求——
    对外可读的是数据面 jobs/*.json 与报告产物，不是这两个文件。
    """
    atomic_write_json(path, obj, mode=0o600)


def _extras(raw: dict) -> dict:
    """run_state.json 顶层里不属于 RunState 模型的键（附加键），原样取出供写回时带上。"""
    return {k: v for k, v in raw.items() if k not in RUN_STATE_KEYS}


class LocalRunStore:
    """RunStore 的本地文件实现（组合根注入；DDB 实装见同包 `ddb.py`）。

    detached（ADR 0034）：本组合根是否「无状态批量运行的 submit」——True 则 create_run 写出的 run_state.json 带顶层
    `detached: true` 标记。标记是执行环境属性、不进 RunState 模型；之后的写回由「顶层附加键整体保留」承担（接力者与同步路径
    的实例不带 detached，它们的写不会丢掉标记，带 detached 的实例也不会给别的 run 补上标记）。读它只经 `is_detached`
    （对位 `DynamoDBRunStore.is_detached`）。
    """

    def __init__(self, root: str | Path, *, detached: bool = False) -> None:
        self._root = Path(root)
        self._detached = detached

    def _state_path(self, run_id: str) -> Path:
        return self._root / run_id / _STATE_FILE

    @staticmethod
    @contextmanager
    def _run_lock(run_dir: Path) -> Iterator[None]:
        """持 run 目录下锁文件的排他 fcntl 锁（跨进程互斥；同一进程里各自打开的描述符之间同样互斥）。run 目录须已存在。"""
        import fcntl

        with open(run_dir / _LOCK_FILE, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)

    @staticmethod
    def _read_raw(path: Path) -> dict | None:
        """读 run_state.json 原文为 dict；文件不存在（含 run 目录不在、同名的不是目录）返回 None。内容损坏照常抛出（写路径
        不吞错：读不出就不写，不会把损坏的文件当成「没有附加键」覆盖掉）。"""
        try:
            text = path.read_text(encoding="utf-8")
        except (FileNotFoundError, NotADirectoryError):
            return None
        return json.loads(text)

    @staticmethod
    def _write_state(path: Path, state: RunState, extras: dict) -> None:
        """写回 run_state.json：附加键在前、模型键在后（同名时模型键为准；附加键本来就不与模型键同名）。只在持锁时调用。"""
        _atomic_write_json(path, {**extras, **run_state_to_dict(state)})

    @staticmethod
    def _marker_in(path: Path) -> bool:
        if not path.exists():
            return False
        return json.loads(path.read_text(encoding="utf-8")).get("detached") is True

    def is_detached(self, run_id: str) -> bool:
        """run_state.json 上有没有 `detached` 标记（ADR 0034）：True 表示无状态批量运行的 submit 建的 run。

        **adapter-only 只读访问器、不在 RunStore port 上**（执行环境属性不进 core）。`status --wait` 据此分流：detached run
        才接力推进；同步 `run` 由进程内 schedule 推进，接力者碰它即双开推进器——与云端推进器「只碰 detached run」同一道闸。
        文件缺失、读不出或没有标记 → False（读路径保守：读不出标记就当不可接力）。
        """
        try:
            return self._marker_in(self._state_path(run_id))
        except (OSError, ValueError):
            return False

    # ---- 写入口：全部在文件锁内读改写 ----

    def _locked_rmw(self, run_id: str, mutate) -> bool | None:
        """在 run_state.json 上做跨进程原子读改写：持文件锁 → 读原文 → mutate(state) → (新 state | None) → 写回。

        返回 True 表示写成；False 表示 mutate 返回 None（条件不成立），不写；None 表示运行态不存在，不写。条件写入口把后两种
        都当作写不成，update_job_state 把 None 翻成 FileNotFoundError。写回时带上读到的附加键。"""
        path = self._state_path(run_id)
        if not path.exists():
            return None  # run 目录可能也不在：不为一次不存在的写建锁文件
        with self._run_lock(path.parent):
            raw = self._read_raw(path)
            if raw is None:
                return None
            new_state = mutate(run_state_from_dict(raw))
            if new_state is None:
                return False
            self._write_state(path, new_state, _extras(raw))
            return True

    def create_run(self, meta: RunMeta, initial_state: RunState) -> None:
        """run 开始：写 definition（run_meta.json）+ 初始运行态（run_state.json），只在 run 目录里还没有运行态时成立。

        判据与两个文件的写在同一把文件锁内（ADR 0054 决策五）：运行态已在 → 抛 FileExistsError，两个文件都不碰。只有
        run_meta.json、没有运行态的目录（建 run 在两次写之间中断）照常建。写序同云端：definition 在前、运行态在后，运行态一出现，
        definition 必已在。后台执行标记只在这里写下。"""
        run_dir = self._root / meta.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / _STATE_FILE
        with self._run_lock(run_dir):
            if path.exists():
                raise FileExistsError(f"run {meta.run_id} 已存在，不重新建立")
            _atomic_write_json(run_dir / _META_FILE, run_meta_to_dict(meta))
            self._write_state(path, initial_state, {"detached": True} if self._detached else {})

    def update_job_state(self, run_id: str, job_state: JobState) -> bool:
        """按 scope_id 刷单个 job 的运行态（Map upsert）。run_state.json 不存在则报错（须先 create_run）。

        写入的 job 态不是 pending 且 run 未收尾时，同一次读改写把 run 级置为 running（对拍 DDB 的带条件写与只写 job 的回退）；
        run 已收尾时 job 照写、run 级不变。写入 pending 时只写 job。
        读改写在文件锁内，与别的写入口互斥：已落下的终态不会被一次读在终态之前的写改回 running（ADR 0054 决策五）。
        返回 run 级在这次写时是否仍未结束：判据取锁内读到的 run 级，与写在同一次读改写里（ADR 0054 决策五）。"""
        open_at_write: list[bool] = []

        def mutate(state: RunState) -> RunState:
            jobs = dict(state.jobs)
            jobs[job_state.scope_id] = job_state  # Map 定位：各 scope 互不干扰
            status = state.status
            still_open = status in (Status.PENDING, Status.RUNNING)
            open_at_write.append(still_open)
            if job_state.status != Status.PENDING and still_open:
                status = Status.RUNNING
            return replace(state, status=status, jobs=jobs)  # 其余字段原样保留（含 run 级 message 与认领计数）
        if self._locked_rmw(run_id, mutate) is None:
            raise FileNotFoundError(f"update_job_state：run_state 不存在（须先 create_run）：{run_id}")
        return open_at_write[0]

    def load_run_meta(self, run_id: str) -> RunMeta | None:
        """读回 definition（RunMeta）；不存在返回 None。"""
        path = self._root / run_id / _META_FILE
        if not path.exists():
            return None
        return run_meta_from_dict(json.loads(path.read_text(encoding="utf-8")))

    def peek_definition_header(self, run_id: str) -> tuple[int, str | None] | None:
        """只读 definition 的结构版本与写端 CLI 版本（ADR 0037 决策 7）；run_meta.json 不存在返回 None。"""
        path = self._root / run_id / _META_FILE
        if not path.exists():
            return None
        d = json.loads(path.read_text(encoding="utf-8"))
        return definition_schema_version(d), d.get("cli_version")

    def load_run_state(self, run_id: str) -> RunState | None:
        """读回运行态（RunState）；不存在返回 None。"""
        raw = self._read_raw(self._state_path(run_id))
        return None if raw is None else run_state_from_dict(raw)

    def list_runs(self, statuses: Sequence[Status], *, limit: int | None) -> list[RunListing]:
        """列举（语义见 RunStore port；本机做法见 ADR 0041 决策七「本机实现」）：列报告落点下的子目录（目录名即 run_id），逐个读
        run_state.json，按读回的状态归入所请求的状态，每个状态按 run_id 降序取至多 `limit` 条。

        没有 run_state.json 的目录跳过（不是 run 目录，或在写下运行态之前就中断的执行）。读回解析不了的（JSON 损坏、形态违约、
        状态值本版本不认识、清单要输出的字段类型不对）以 `state=None` 列出、不参与归入与截取，不论请求了哪些状态。报告落点目录不存在
        时返回空列表（落点在第一次落盘时才建立，区分「目录不存在」与「目录下没有 run」是调用方的事）；目录、条目或文件不可读一类
        OSError 原样抛出，只有列出之后被删掉的条目跳过。不建索引文件：运行态的真值只在各 run 目录里，清单与 `status` 读到的永远一致。
        detached 与 `is_detached` 同一判据（run_state.json 顶层标记），取自同一次读回；提交记录头部只对入选的 run 读，读法同
        `peek_definition_header`，文件不存在或内容解析不了（含写端版本不是字符串）为 None。
        """
        wanted = list(dict.fromkeys(statuses))
        if limit is not None and limit < 1:
            raise ValueError(f"limit 须为正整数或 None，现为 {limit!r}")
        try:
            entries = list(self._root.iterdir())
        except FileNotFoundError:
            return []
        by_status: dict[Status, list[tuple[str, RunState, bool]]] = {s: [] for s in wanted}
        unreadable: list[tuple[str, bool]] = []
        for entry in entries:
            # 显式 stat 判目录、不用 Path.is_dir：Python 3.14 起 is_dir 把任何 OSError 都读作「不是目录」，权限错误会被吞成
            # 「目录下没有 run」。只有列出之后被删掉的条目（含目标不存在的符号链接）跳过
            try:
                mode = entry.stat().st_mode
            except FileNotFoundError:
                continue
            if not stat.S_ISDIR(mode):
                continue
            try:
                raw = (entry / _STATE_FILE).read_bytes()
            except (FileNotFoundError, IsADirectoryError):
                continue
            d = None
            try:
                d = json.loads(raw.decode("utf-8"))  # 解码放在这里：编码不对也是内容损坏，不是访问失败
                state = require_listing_state(run_state_from_dict(d))
            except (ValueError, KeyError, TypeError, AttributeError):  # JSON 损坏、形态违约、状态值不认识、字段类型不对
                state = None
            detached = isinstance(d, dict) and d.get("detached") is True
            if state is None:
                unreadable.append((entry.name, detached))
            elif state.status in by_status:
                by_status[state.status].append((entry.name, state, detached))
        rows = [RunListing(run_id=run_id, state=None, detached=detached, header=self._listing_header(run_id))
                for run_id, detached in unreadable]
        for bucket in by_status.values():
            bucket.sort(key=lambda row: row[0], reverse=True)
            for run_id, state, detached in bucket if limit is None else bucket[:limit]:
                rows.append(RunListing(run_id=run_id, state=state, detached=detached,
                                       header=self._listing_header(run_id)))
        rows.sort(key=lambda row: row.run_id, reverse=True)
        return rows

    def _listing_header(self, run_id: str) -> tuple[int, str | None] | None:
        """列举用的头部读取：与 `peek_definition_header` 同一读法，再经 `require_listing_header` 核类型；内容解析不了（JSON 损坏、
        不是对象、结构版本不是整数、写端版本不是字符串）读作 None，访问失败（OSError）照常抛出——权限一类问题不吞成「版本未知」
        （ADR 0041 决策七「写出版本的标记」）。"""
        try:
            header = self.peek_definition_header(run_id)
            return None if header is None else require_listing_header(header)
        except (ValueError, AttributeError):
            return None

    def preflight(self) -> None:
        """探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。"""

    # ---- 条件写（ADR 0034 机制三/四、ADR 0054 决策二/五）：同样走 _locked_rmw，cloud DDB 用条件表达式复刻同一语义 ----

    def try_claim_job(self, run_id: str, scope_id: str, *, claimed_at: str | None = None) -> bool:
        """CAS：仅当 jobs[scope_id] 当前 PENDING 且 run 未收尾才置 RUNNING（机制四）；随写 claimed_at（timeout 起算点）。

        同一次锁内写回把 run 级置为 RUNNING 并把认领计数加一（ADR 0034 机制三「run 级状态只进不退」条①）：
        run 已收尾后不再接受新认领，条件不成立（job 不存在、已非 pending、run 已收尾）一律返回 False、不写。HWM 不变。"""
        def mutate(state: RunState):
            if state.status not in (Status.PENDING, Status.RUNNING):
                return None  # run 已收尾：不再接受新认领
            js = state.jobs.get(scope_id)
            if js is None or js.status != Status.PENDING:
                return None  # 不存在 / 已非 pending（已被别人认领或已运行）→ 不改
            jobs = dict(state.jobs)
            jobs[scope_id] = replace(js, status=Status.RUNNING, claimed_at=claimed_at)  # 会话与 job 级说明原样保留
            # 其余字段原样保留（含 run 级 message），与 DDB 只 SET jobs.#sid、顶层 status 与认领计数对拍
            return replace(state, status=Status.RUNNING, jobs=jobs, claim_count=state.claim_count + 1)
        return self._locked_rmw(run_id, mutate) is True

    def project_state(self, run_id: str, state: RunState) -> bool:
        """HWM 条件写投影：仅当传入 hwm ≥ 库中 hwm 才写（机制三①，挡 stale 覆盖）。只写 HWM、run 级与 jobs，传入的
        started_at、ended_at、message、认领计数不用，库中值原样保留（与 DDB 的标量写只写 HWM 与 run 级对拍）。

        **run 级 status 只写 running、不落终态**（run 级终态是收尾的 commit point
        专属；若投影提前落终态，try_finalize 会被自己刚写的终态挡住）。取值规则见 `projected_run_status`
        （与 ddb adapter 共用一份）：它给出 pending（投影里全 job 仍 pending）时保留库中 run 级，认领或此前投影已写成的
        running 不被拿着旧 baseline 的投影改回 pending。
        已 finalize（库中 status 已终态）→ 挡。

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
                return None  # 已 finalize 终态：不被投影刷回
            # 逐 job 与库中现态取较推进者（同 rank 取新值——终态间以本次投影为准）
            jobs: dict[str, JobState] = dict(cur.jobs)  # 从库中现态出发：投影没带的 job 原样保留
            for sid, js in state.jobs.items():
                cur_js = cur.jobs.get(sid)
                if cur_js is None:
                    continue  # definition 外的 scope（不该发生：project 只吐 meta.jobs 的键）→ 不臆造，与 DDB 的 CCF 跳过对拍
                if _lifecycle_rank(cur_js.status) > _lifecycle_rank(js.status):
                    jobs[sid] = cur_js  # 库中更推进（已终态/已 claim）→ 保留，不回退
                else:
                    # 血缘/claim 时刻不丢：投影缺的字段回填库中值（claimed_at 只由 try_claim_job 落、
                    # 事件推演不出——正常经 project 的 baseline 带回，此处兜没带 baseline 的投影）。job 级说明只由结束写写下，
                    # 投影不带它，库中值原样保留
                    jobs[sid] = replace(
                        cur_js, status=js.status,
                        session_id=js.session_id or cur_js.session_id,
                        claimed_at=js.claimed_at or cur_js.claimed_at)
            # run 级 status 按投影里的 job 态定（全 pending → 保留库中值，否则 running）；传入的 run 级值在有 job
            # 出判定时即为终态聚合值，一律不用（规则与理由见 projected_run_status）。库中值此处必为 pending 或 running。
            status = Status.RUNNING if projected_run_status(state.jobs) == Status.RUNNING else cur.status
            # 只写 HWM、run 级与 jobs，其余字段（started_at、ended_at、message、认领计数）保留库中值，与 DDB 只 SET 这几项对拍；
            # HWM 为 None 时按 0 落库，同 DDB
            return replace(cur, status=status, jobs=jobs, high_water_mark=new_hwm)
        return self._locked_rmw(run_id, mutate) is True

    def try_finalize(self, run_id: str, status: Status, ended_at: str, *, message: str | None = None,
                     expected_claim_count: int | None = None) -> bool:
        """状态机单调条件写：仅当当前总 status 为非终态才写终态（commit 恰一次）。message 随终态同一次写入；
        为 None 时不动库中值（对拍 DDB 不提及该属性）。expected_claim_count 给出时另要求锁内重读到的认领计数等于它，
        为 None 时不判。"""
        def mutate(state: RunState):
            if state.status not in (Status.PENDING, Status.RUNNING):
                return None  # 已终态：别人已收尾 → 不覆盖
            if expected_claim_count is not None and state.claim_count != expected_claim_count:
                return None  # 读到运行态之后又有新的认领 → 放弃这次收尾
            return replace(state, status=status, ended_at=ended_at,
                           message=state.message if message is None else message)
        return self._locked_rmw(run_id, mutate) is True

    # ---- run 的状态只由 job 的终态算出（ADR 0031 决定三）：两个写入口的作用由 run_status 给出，这里只负责锁与落盘 ----

    def commit_job_states(self, run_id: str, job_states: Sequence[JobState], *, ended_at: str) -> CommitOutcome:
        """带结果的 job 终态写（语义见 RunStore port）：持文件锁读运行态，按 `run_status.commit_applied` 算出这次写的作用与结果，
        写成时原子写回，run 已结束时不写。判断用的是锁内读到的整份运行态（ADR 0034 机制三②），同一把锁挡住别的写入口插在读与写之间。
        运行态不存在抛 FileNotFoundError；参数不合要求时 commit_applied 抛 ValueError，文件不被改动。"""
        job_states = tuple(job_states)
        outcome: list[CommitOutcome] = []

        def mutate(state: RunState) -> RunState | None:
            new_state, result = commit_applied(state, job_states, ended_at=ended_at)
            outcome.append(result)
            return new_state
        if self._locked_rmw(run_id, mutate) is None:
            raise FileNotFoundError(f"commit_job_states：run_state 不存在（须先 create_run）：{run_id}")
        return outcome[0]

    def end_run(self, run_id: str, ending: RunEnding, *, ended_at: str) -> bool:
        """结束写（语义见 RunStore port）：持文件锁读运行态，按 `run_status.ending_applied` 算出要写下的运行态，成立时原子写回。
        run 已结束、条件不成立（不结束执行中 job 的来路，即 `ending.ends_running_jobs` 为 False，遇到 running 的 job）、运行态不存在，
        都返回 False、不写。"""
        return self._locked_rmw(run_id, lambda state: ending_applied(state, ending, ended_at=ended_at)) is True
