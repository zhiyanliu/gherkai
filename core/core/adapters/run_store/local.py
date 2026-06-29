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

from core.model import RunMeta, RunState
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

    def save_run(self, meta: RunMeta, state: RunState) -> None:
        """落 <root>/<run_id>/{run_meta.json, run_state.json}（写面）。"""
        run_dir = self._root / meta.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run_meta.json").write_text(
            json.dumps(run_meta_to_dict(meta), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "run_state.json").write_text(
            json.dumps(run_state_to_dict(state), ensure_ascii=False, indent=2), encoding="utf-8"
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
