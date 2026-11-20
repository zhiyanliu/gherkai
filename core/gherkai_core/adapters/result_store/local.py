"""LocalResultStore（ADR 0016 数据面）：由执行结果结束的 job 的判定明细，每次保存一个 JSON 文件。

落点：`<root>/<run_id>/jobs/<result_id>.json`。每次保存一个文件，文件名只由写入方给出的标识构成（ADR 0030 决定三「点名」条，以及
「local 三个写面一律原子写」框里「本机判定明细的落点」一段）：同一个 job 可以有多份、互不覆盖，用哪一份由运行态里这个 job 的终态点名，读者按标识取、不列举目录。文件名与
scope_id 无关，长度因此有界，含中文的长 scope_id 不会使保存因文件名过长而失败。与 RunStore（控制面：run_meta.json + run_state.json）
互补；单份明细自包含（嵌完整 Job def）。

写入方有两个，都在记下 job 终态的那次写之前保存（ADR 0030 决定三）：前台 `persist.RunPersistence.on_job_complete` 每个 job 完成即存；
后台 `reconcile.tick` 从这一轮的同一份事件快照为每个已有结果的 job 各存一份。两者都不等整个 run 结束。本机推进器的组合根在本类外面套
保存失败的退避重试（同包 `retrying.py`），本类自身不重试。

**克制（ADR 0016）**：只忠实落已成形的 `JobResult`（复用 serialize.job_result_to_dict / job_result_from_dict），
不发明 ADR 有意 defer 的数据面新字段；标识不写进文件内容，文件名本身就是标识。

标识按不透明标识符的惯例编码成文件名里的一段（`quote(safe="")`，把 `/` 等也编码）：生成的十六进制标识编码后不变，被手改过的运行态
里的值也只会落在 `jobs/` 之下的一段里，本类因此不校验标识的形态。
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from gherkai_core.adapters._atomic import atomic_write_json
from gherkai_core.model import JobResult
from gherkai_core.serialize import job_result_from_dict, job_result_to_dict


class LocalResultStore:
    """ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。"""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _path(self, run_id: str, result_id: str) -> Path:
        return self._root / run_id / "jobs" / (quote(result_id, safe="") + ".json")

    def save_job_result(self, run_id: str, result_id: str, job: JobResult) -> None:
        """把一份明细存成 `<root>/<run_id>/jobs/<result_id>.json`，权限 0644（消费者含 CI 与人）。

        **原子写**（同目录 tmp 加 rename，见 `gherkai_core.adapters._atomic`）：读者是另一个进程（run 执行中读已结束 job 的 `explain`，
        ADR 0042 决策四），要么读不到这个文件，要么读到完整的一份，不会撞上 truncate 窗口拿到空的或半截的 JSON。同一个标识再存一次即
        原样覆盖，只发生在同一次保存的重试上（内容相同）。不带条件，写面没有跨进程锁（文件锁只护 run_state.json）。
        """
        path = self._path(run_id, result_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(path, job_result_to_dict(job))

    def load_job_result(self, run_id: str, result_id: str) -> JobResult | None:
        """按标识读回那一份；这个标识下没有文件时返回 None。

        直接打开文件、接住 FileNotFoundError，不先探测存在再读：两步之间文件被删会冒出未归类的异常。别的读取失败（权限等 OSError）
        照常抛出；内容损坏不兜（`JSONDecodeError` 原样抛出，写面原子写，读到的只会是完整文件，ADR 0042 决策四「数据来源」段）。"""
        try:
            text = self._path(run_id, result_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        return job_result_from_dict(json.loads(text))

    def preflight(self) -> None:
        """探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。"""
