"""LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。

数据面（追加为主）：一次 run 的每个 JobResult 落 `<root>/<run_id>/jobs/<encoded_scope_id>.json`，
供 CI 读单 scope 判定真值。与 RunStore（控制面：run_meta.json + run_state.json）互补——数据面按 job 追加，
未来可流式（worker 跑完一个 job 即落），不必等整 run 结束。单 job 文件自包含（嵌完整 Job def）。

**克制（ADR 0016）**：只忠实落已成形的 `JobResult`（复用 serialize.job_to_dict/from_dict），
不发明 ADR 有意 defer 的数据面新字段。

scope_id 是**不透明标识符**（可含 `/`:`空格/中文，ADR 0025）——落文件名时做**可逆 urlencode**
（safe=""，把 `/` 等也编码），保唯一、不撞名、不当路径解析（消费层安全字符编码由该层做，ADR 0025）。
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from core.model import JobResult
from core.serialize import job_result_from_dict, job_result_to_dict


class LocalResultStore:
    """ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。"""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def save_job_result(self, run_id: str, job: JobResult) -> None:
        """把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。"""
        jobs_dir = self._root / run_id / "jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        fname = quote(job.scope_id, safe="") + ".json"  # 可逆编码，scope_id 任意字符都安全成文件名
        (jobs_dir / fname).write_text(
            json.dumps(job_result_to_dict(job), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load_job_result(self, run_id: str, scope_id: str) -> JobResult | None:
        """读回单个 JobResult（读回面）；不存在返回 None。"""
        path = self._root / run_id / "jobs" / (quote(scope_id, safe="") + ".json")
        if not path.exists():
            return None
        return job_result_from_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_all(self, run_id: str) -> list[JobResult]:
        """读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。"""
        jobs_dir = self._root / run_id / "jobs"
        if not jobs_dir.is_dir():
            return []
        return [job_result_from_dict(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(jobs_dir.glob("*.json"))]

    def preflight(self) -> None:
        """探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。"""
