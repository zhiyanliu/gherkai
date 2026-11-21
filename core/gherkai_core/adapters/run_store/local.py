"""LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。

三层切分（ADR 0016）：RunStore 存**控制面**——`RunMeta`（definition：run_id/created_at/执行哪些 job，
执行前确定）+ `RunState`（运行态：总 status/各 job status/血缘/点名的标识，执行后产生）。**不存判定明细**
（那是数据面、由 ResultStore 持有，避免与 jobs/*.json 冗余真值）。

**跨文件读取契约（消解"信哪个"困惑）**：
- definition 唯一真值在 run_meta.json。jobs/*.json 内嵌的 job def 是其**自包含副本**——非独立维护的第二真值、
  不会漂移（两处都序列化同一次 plan 产出的同一个 Job 对象，共用 serialize.job_to_dict）。嵌它是为让读者按运行态里的标识取回
  一份明细之后，不再读 run_meta 也能还原它的 job 定义（云端对象存储按键取单份同理）。
- **run 与各 job 的状态以 run_state.json 为准**（ADR 0030 决定三「状态的权威是运行态」条）：退出码、`status` 与 run 的汇总都读它。
  jobs/*.json（数据面 ResultStore）是由执行结果结束的 job 的判定明细，对 scenario、step 与归因负责；每次保存一份、同一个 job 可能
  有多份，用哪一份由 run_state.json 里这个 job 的终态点名（`result_id`，ADR 0030 决定三「点名」条）；由结束写结束的 job 没有明细。

**建 run 经暂存目录与改名**（ADR 0030 决定四，做法在同包 `run_dir`）：create_run 先在报告目录里建暂存目录，在它上面取生命期锁
（ADR 0054 决策三），把 run_meta.json、run_state.json 写进去，写完才原子改名成 run 标识，持锁的描述符交给构造时注入的持有者。
暂存目录里的两个文件没有写序的约束：两个都写完才改名，按标识的读与列举不认以点开头的名字。建 run 不取运行态的短锁，「已存在」
只由改名给出。

**建 run 之后的各写入口在同一把 fcntl 短锁内完成读改写**（ADR 0030 决定三、ADR 0054 决策五）：update_job_state、try_claim_job、
project_state、commit_job_states、end_run 互斥，跨进程与进程内多线程都成立；同一个 run 的各写入方（前台执行者、后台推进进程、
`status --wait` 接力）不靠调用方串行。短锁的锁文件 `.runstate.lock` 在第一次读改写时建出。它与生命期锁是两个对象（目录里的一个
文件、目录本身），互不阻挡。读面（load_run_state、list_runs、`status`）不持锁，靠原子写看到完整文件。

**名字规则**（`run_dir.is_run_name`）：run 标识即 run 目录的名字，不以点开头、不含路径分隔符、非空、按文件系统编码不超过
255 字节。create_run 拒绝不合规则的标识；按标识读写的各入口收到这样的标识按 run 不存在处理；list_runs 跳过名字不合规则的目录
（含暂存目录与别的隐藏目录）。

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
from gherkai_core.adapters.run_store import run_dir
from gherkai_core.model import TERMINAL_STATUSES, JobState, RunListing, RunMeta, RunState, Status
from gherkai_core.run_status import (
    CommitOutcome,
    RunEnding,
    check_new_run,
    check_running_write,
    commit_applied,
    ending_applied,
    run_status_of,
)
from gherkai_core.serialize import (
    RUN_STATE_KEYS,
    definition_from_json,
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

    lock_holder（ADR 0030 决定四「持锁的描述符交给注入的持有者」条）：create_run 建成之后把持生命期锁的描述符交给它。只有推进
    这个 run 的进程（前台 `run`、本机后台推进进程）构造带持有者的 store；不带持有者的 store 调 create_run 即 RuntimeError，
    只读命令与接力的 store 因此不能建 run。
    """

    def __init__(self, root: str | Path, *, detached: bool = False,
                 lock_holder: run_dir.LockHolder | None = None) -> None:
        self._root = Path(root)
        self._detached = detached
        self._lock_holder = lock_holder

    def _run_dir(self, run_id: str) -> Path | None:
        """run 标识对应的 run 目录；标识不合名字规则（`run_dir.is_run_name`）即 None，调用方一律按 run 不存在处理。"""
        return self._root / run_id if run_dir.is_run_name(run_id) else None

    def _state_path(self, run_id: str) -> Path | None:
        d = self._run_dir(run_id)
        return None if d is None else d / _STATE_FILE

    def _meta_path(self, run_id: str) -> Path | None:
        d = self._run_dir(run_id)
        return None if d is None else d / _META_FILE

    @staticmethod
    @contextmanager
    def _run_lock(directory: Path) -> Iterator[None]:
        """持 run 目录下锁文件的排他 fcntl 锁（跨进程互斥；同一进程里各自打开的描述符之间同样互斥）。run 目录须已存在。"""
        import fcntl

        with open(directory / _LOCK_FILE, "w") as lf:
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
        """写回 run_state.json：附加键在前、模型键在后（同名时模型键为准；附加键本来就不与模型键同名）。建 run 时写进暂存目录，此后只在持短锁时调用。"""
        _atomic_write_json(path, {**extras, **run_state_to_dict(state)})

    @staticmethod
    def _marker_in(path: Path | None) -> bool:
        if path is None or not path.exists():
            return False
        return json.loads(path.read_text(encoding="utf-8")).get("detached") is True

    def is_detached(self, run_id: str) -> bool:
        """run_state.json 上有没有 `detached` 标记（ADR 0034）：True 表示无状态批量运行的 submit 建的 run。

        **adapter-only 只读访问器、不在 RunStore port 上**（执行环境属性不进 core）。`status --wait` 据此分流：detached run
        才接力推进；同步 `run` 由进程内 schedule 推进，接力者碰它即双开推进器——与云端推进器「只碰 detached run」同一道闸。
        文件缺失、读不出、没有标记或标识不合名字规则时返回 False（读路径保守：读不出标记就当不可接力）。
        """
        try:
            return self._marker_in(self._state_path(run_id))
        except (OSError, ValueError):
            return False

    # ---- 写入口：建 run 经暂存目录与改名，之后的各写入口在文件锁内读改写 ----

    def _locked_rmw(self, run_id: str, mutate) -> bool | None:
        """在 run_state.json 上做跨进程原子读改写：持文件锁 → 读原文 → mutate(state) → (新 state | None) → 写回。

        返回 True 表示写成；False 表示 mutate 返回 None（条件不成立），不写；None 表示运行态不存在（含标识不合名字规则），不写。
        条件写入口把后两种都当作写不成，update_job_state 把 None 翻成 FileNotFoundError。写回时带上读到的附加键。锁文件在
        这里第一次用到时建出（建 run 不取这把锁）。"""
        path = self._state_path(run_id)
        if path is None or not path.exists():
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
        """run 开始：写 definition（run_meta.json）+ 初始运行态（run_state.json），只在以 run 标识命名的位置还没有非空目录时成立
        （ADR 0054 决策五、ADR 0030 决定四）。

        次序：没有 job 的运行定义即 ValueError（`run_status.check_new_run`）；没有注入持有者即 RuntimeError（编程错误）；run 标识
        不合名字规则即 ValueError。三者都什么都不建。之后经 `run_dir.create_run_dir`：边界检查，在暂存目录上取锁，把两个文件写进
        暂存目录，原子改名成 run 标识，描述符交给持有者。后台执行标记只在这里写下。

        失败的类型（调用方据它分别说明）：报告目录不合要求 `run_dir.RunDirRejected`；取锁出错 `run_dir.LifetimeLockUnavailable`
        （OSError 的子类）；暂存目录连续被占用 `run_dir.StagingContended`；目标已是非空目录 `errors.RunAlreadyExists`，什么都没改；其余
        OSError（写两个文件失败，与 run 同名的位置被文件、符号链接或挂载点占着，建报告目录失败，建暂存目录或打开它失败）是写记录失败，原样抛出，不是
        `RunAlreadyExists`。"""
        check_new_run(meta)  # 没有 job 的运行定义不建（先于建目录，不留空目录）
        if self._lock_holder is None:
            raise RuntimeError("这个 LocalRunStore 没有注入锁的持有者，不能建 run：只有推进 run 的进程构造带持有者的 store")
        if not run_dir.is_run_name(meta.run_id):
            raise ValueError(f"run 标识 {meta.run_id!r} 不能用作本机 run 目录的名字：不能为空、不能以点开头、不能含路径分隔符、"
                             f"按文件系统编码不能超过 {run_dir.RUN_NAME_MAX_BYTES} 字节")
        extras = {"detached": True} if self._detached else {}

        def write(staging: Path) -> None:
            _atomic_write_json(staging / _META_FILE, run_meta_to_dict(meta))
            self._write_state(staging / _STATE_FILE, initial_state, extras)
        run_dir.create_run_dir(self._root, meta.run_id, write, holder=self._lock_holder)

    def update_job_state(self, run_id: str, job_state: JobState) -> bool:
        """执行中的写（语义见 RunStore port）：按 scope_id 整项替换单个 job 的条目。run_state.json 不存在则报错（须先 create_run）；
        写入的不是 running、或带点名的标识，即抛 ValueError（`run_status.check_running_write`），文件不被改动。

        锁内读到 run 已结束、这个 job 不在 Map 里或已是终态时都不写：run 到终态之后不再接受任何写（ADR 0054 决策五），不臆造 job，
        终态只写一次（ADR 0031 决定一·补）。写成时 run 状态按锁内读到的整份运行态经取法算出（ADR 0031 决定三），与 job 在同一次读改写里
        写下（ADR 0034 机制三「run 级状态只进不退」条③）。读改写在文件锁内，与别的写入口互斥：已落下的终态不会被一次读在终态之前的写
        改回 running（ADR 0054 决策五）。
        返回 run 在这次写时是否仍未结束：判据取锁内读到的 run 状态，与写在同一次读改写里（ADR 0054 决策五）；job 不在 Map 里或已是终态
        而没有写时同样按它给出。"""
        check_running_write(job_state)
        open_at_write: list[bool] = []

        def mutate(state: RunState) -> RunState | None:
            still_open = state.status not in TERMINAL_STATUSES
            open_at_write.append(still_open)
            if not still_open:
                return None  # run 已结束：不再接受写
            current = state.jobs.get(job_state.scope_id)
            if current is None or current.status in TERMINAL_STATUSES:
                return None  # 不在运行态里的 job 不臆造；已结束的 job 不被执行中的写改写
            jobs = {**state.jobs, job_state.scope_id: job_state}  # Map 定位：各 scope 互不干扰
            # run 状态按取法写下；其余字段原样保留（含 run 级 message 与认领计数）
            return replace(state, status=run_status_of(js.status for js in jobs.values()), jobs=jobs)
        if self._locked_rmw(run_id, mutate) is None:
            raise FileNotFoundError(f"update_job_state：run_state 不存在（须先 create_run）：{run_id}")
        return open_at_write[0]

    def load_run_meta(self, run_id: str) -> RunMeta | None:
        """读回 definition（RunMeta）；不存在（含标识不合名字规则）返回 None。"""
        path = self._meta_path(run_id)
        if path is None or not path.exists():
            return None
        return run_meta_from_dict(definition_from_json(path.read_text(encoding="utf-8")))

    def peek_definition_header(self, run_id: str) -> tuple[int, str | None] | None:
        """只读 definition 的结构版本与写端 CLI 版本（ADR 0037 决策 7）；run_meta.json 不存在（含标识不合名字规则）返回 None。"""
        path = self._meta_path(run_id)
        if path is None or not path.exists():
            return None
        d = definition_from_json(path.read_text(encoding="utf-8"))
        return definition_schema_version(d), d.get("cli_version")

    def load_run_state(self, run_id: str) -> RunState | None:
        """读回运行态（RunState）；不存在（含标识不合名字规则）返回 None。"""
        path = self._state_path(run_id)
        raw = None if path is None else self._read_raw(path)
        return None if raw is None else run_state_from_dict(raw)

    def list_runs(self, statuses: Sequence[Status], *, limit: int | None) -> list[RunListing]:
        """列举（语义见 RunStore port；本机做法见 ADR 0041 决策七「本机实现」）：列报告落点下的子目录（目录名即 run_id），逐个读
        run_state.json，按读回的状态归入所请求的状态，每个状态按 run_id 降序取至多 `limit` 条。

        名字不合名字规则的（以点开头，含建 run 用的暂存目录与别的隐藏目录）先于读文件跳过：暂存目录在改名成 run 标识之前里面已有
        运行态。没有 run_state.json 的目录跳过（不是 run 目录）。读回解析不了的（JSON 损坏、形态违约、
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
            if not run_dir.is_run_name(entry.name):
                continue
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

    # ---- 条件写（ADR 0034 机制三/四、ADR 0054 决策五）：同样走 _locked_rmw，cloud DDB 用条件表达式复刻同一语义 ----

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
        """投影写（语义见 RunStore port）：在文件锁内一次读改写。传入 HWM 小于库中 HWM（机制三①，挡 stale 覆盖）或库中 run 已结束时
        不写；否则只写 HWM、各 job 态，以及按下段规则写 run 状态，传入的 run 级 status、started_at、ended_at、message、认领计数不用，
        库中值原样保留（与 DDB 只 SET HWM、job 属性与 run 状态对拍）。

        **job 态不越过 running**：投影里已有结果的 job 按 running 写，它的终态只由终态写记下（ADR 0034 机制三「② 的 job 级半边落地
        形态」段）。各 job 态与库中现态按生命周期序逐 job 单调合并（机制三②的 job 级半边）：task_exited 走独立键空间、不带数值 seq，
        「被 scope_done 触发」与「被 task_exited 触发」的投影可携带相同 HWM，① 挡不住 stale 实例把已推进的 job 改回旧态（并发实例对
        某 scope 视图旧、对另一 scope 视图新时 HWM 相等）。逐 job 取较推进者：库中已是终态的 job 不被改动（终态只写一次，ADR 0031
        决定一·补），running 不被 pending 覆盖（防已认领的 job 被改回 pending 而重复启动，机制四）。

        **run 状态只写 running、不写终态**（ADR 0034 机制三「投影写的 run 状态按 0031 决定三的取法给出」段，并见 ADR 0030 决定三）：
        这次写把某个 job 写成 running（库中这个 job 是 pending 或 running）时 run 状态随之写成 running，否则保留库中的 run 状态。与 DDB
        在把 job 写成 running 的那次逐 job 写里同时写 run 状态对拍。不按取法对整份 jobs 重算：零个 job 时取法给出 passed，投影会写下
        没有结束时刻的终态；run 的终态只随记下最后一个 job 终态的写或结束写写下。"""
        from gherkai_core.project import _lifecycle_rank

        def mutate(cur: RunState):
            cur_hwm = cur.high_water_mark or 0
            new_hwm = state.high_water_mark or 0
            if new_hwm < cur_hwm:
                return None  # stale：读到的事件比库中记录的少，不写（机制三①）
            if cur.status in TERMINAL_STATUSES:
                return None  # run 已结束：运行态不再接受写（ADR 0054 决策五）
            # 逐 job 与库中现态取较推进者，写下的 job 态不越过 running；库中已是终态的不改，同为 running 时取本次投影的值
            # （ADR 0034 机制三「② 的 job 级半边落地形态」段）
            jobs: dict[str, JobState] = dict(cur.jobs)  # 从库中现态出发：投影没带的 job 原样保留
            wrote_running = False
            for sid, js in state.jobs.items():
                cur_js = cur.jobs.get(sid)
                if cur_js is None:
                    continue  # definition 外的 scope（不该发生：project 只给出 meta.jobs 的键）：不臆造，与 DDB 的 CCF 跳过对拍
                target = Status.RUNNING if js.status in TERMINAL_STATUSES else js.status  # 投影不越过 running
                if _lifecycle_rank(cur_js.status) > _lifecycle_rank(target):
                    continue  # 库中已结束或更推进（已认领）：保留库中值，不回退
                # 血缘与认领时刻不丢：投影缺的字段回填库中值（claimed_at 只由 try_claim_job 写下、事件推演不出，正常经 project 的
                # baseline 带回，这里为没带 baseline 的投影兜底）。job 级说明只由结束写写下，投影不带它，库中值原样保留
                jobs[sid] = replace(
                    cur_js, status=target,
                    session_id=js.session_id or cur_js.session_id,
                    claimed_at=js.claimed_at or cur_js.claimed_at)
                wrote_running = wrote_running or target == Status.RUNNING
            # run 状态只随把 job 写成 running 的这次写写成 running，否则保留库中值（此处必为 pending 或 running）
            status = Status.RUNNING if wrote_running else cur.status
            # 只写 HWM、run 状态与 jobs，其余字段（started_at、ended_at、message、认领计数）保留库中值，与 DDB 只 SET 这几项对拍；
            # HWM 为 None 时按 0 落库，同 DDB
            return replace(cur, status=status, jobs=jobs, high_water_mark=new_hwm)
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
