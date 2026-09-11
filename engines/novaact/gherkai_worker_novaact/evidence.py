"""step 级机读证据（evidence，ADR 0042 决策一）：把本 step 各 act 的 Nova trajectory 裁成 gherkai 自有 schema。

为什么在 worker：引擎知识只住 worker（ADR 0022/0027），而 step 结束那一刻 worker 手里才有全部材料
（各正常返回的 act 刚写盘的 `_trajectory.json` + 本步的判定/费用/指令）。CLI 事后解析 SDK 产物是被拒方案。

SDK 耦合被关在本模块（ADR 0042 决策六防线 1/2）：
- **只读映射表列出的少数字段、每个字段当可选**，读不到给 null / 空数组、**绝不抛**——`schema` 只承诺键名与类型。
- **判别按值、不按 SDK 的布尔标志**：真产物里 `is_tool` / `is_return` 对所有 call 都是 False，按它判会静默取空；
  故 think / return / 动作三者一律按 call 的 `name` 分。
- **trajectory 按普通 dict 用 `.get` 链读**：SDK 写出它的 pydantic 模型在私有 `impl/`，仅作阅读指针、不 import、
  不 `model_validate`（其字段无默认值，一处漂移就整份 ValidationError，与「逐字段容缺」相悖）。
- **prompt 用 worker 自己构造的指令串**，不取 json 的 `prompt`——`act_get` 时 SDK 在尾部追加了
  `, format output with jsonschema: {...}`。
- 真产物裁成的 fixture 钉住映射（`tests/fixtures/nova_*_traj.json`），SDK 升版漂移在跑测试时变红。

error act 的契约（ADR 0042 决策一）：act 抛错 → `error` 非空、`prompt` 与 `time_worked_s` 仍填、`frames == []`
（SDK 只在 act 正常返回时写 json，异常对象的 `metadata.trajectory_file_path` 照给路径但文件不存在）。
这是 SDK 事实、不是抽取失败，消费端别把空 frames 当 bug。

本模块只产文件、不上传、不发事件：`evidence.json` 的 ref 由调用方经 uploader 即时上传拿到；截图 URI 由注入的
`ref_for` 确定性算出（字节由调用方在 `step_done` emit 之后交给 uploader 的后台队列，不把 K×票数 次 PutObject
压在判定临界路径上，ADR 0042 决策一「上传时机分两类」）——故 `write_step_evidence` **回传它写下的截图路径**，
调用方拿去入队。调用方负责 best-effort 兜底（ADR 0042 决策二）。
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

SCHEMA_VERSION = 1          # 消费端据此判「认不认这个版本」（ADR 0042 决策六防线 3）
ENGINE = "novaact"

# 截图上界（ADR 0042 决策一「截图策略（有上界）」）：单 act 帧数由 SDK 默认步数上限封顶（30）、再乘票数，
# 不设界时单个 failed Then 可达 10 MB 量级。**只有 screenshot 受限**——frames 的 thought/actions/url 全留（文本很小）。
MAX_SHOTS_PER_ACT = 3       # K：failed/error 档每 act 最多几张
MAX_SHOTS_PER_STEP = 12     # M：每 step 总数上界

_THINK = "think"
_RETURN = "return"

_FAILING = ("failed", "error")

# 目录名安全集：其余（`/` `:` 空格 中文等）一律折成 `-`，再尾附短哈希防二次撞名（见 scenario_key）
_KEY_UNSAFE = re.compile(r"[^0-9A-Za-z._-]+")
_KEY_SLUG_MAX = 80          # 目录名长度上界（scenario_id 可以很长；哈希才是唯一性来源）
_KEY_HASH_LEN = 8

_DATA_URL = re.compile(r"^data:image/[A-Za-z0-9.+-]+;base64,")


@dataclass(frozen=True)
class WrittenEvidence:
    """`write_step_evidence` 的产出：evidence.json 的本地路径 + 它写下的截图本地路径。

    两者去向不同（ADR 0042 决策一「上传时机分两类」）：json 由调用方即时上传换 ref 挂进 `step_done`；
    截图路径在 emit 之后交给上传器的后台队列（本模块不上传、不认识队列）。
    """

    json_path: str
    screenshots: list[str]


@dataclass(frozen=True)
class ActRecord:
    """一次 AI 调用（`act` / `act_get`）的 worker 侧材料：evidence 的 act = 本记录 + 该 act 的 trajectory。

    `vote`：本次调用计入判定的那一票；None = 本 act 不投票（When/Given 的动作）。票源表达式与 `step_done`
    同一个（`bool(matches_schema and parsed_response)`）——**不从 `result` 反推**：模型回非 JSON 或不过 schema 时
    该票记 no，而 return call 的 kwargs 里仍留着看似为真的原文（ADR 0042 决策一映射表）。
    `trajectory_path`：`metadata.trajectory_file_path`（**不用**公开属性 `ActResult.trajectory_file_path`——
    未开 replayable 时它返 None 并喷 SDK 警告，`act_get` 更是恒 None）。抛错的 act 该文件通常不存在。
    """

    index: int
    prompt: str | None = None
    vote: bool | None = None
    error: str | None = None
    time_worked_s: float | None = None
    trajectory_path: str | None = None


def read_trajectory(path: str | None) -> dict | None:
    """读 act 的 `_trajectory.json` → 普通 dict；无路径 / 缺文件 / 坏 json / 非 dict → None（**不抛**）。

    缺文件是**常态而非故障**：SDK 的写盘闸门是「传了 logs_directory 且 act 有 step」，act 抛错时只落 `.html`
    （ADR 0042 决策一 error act 契约）→ 调用方据 None 得 `frames: []`、不报抽取失败。
    """
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):     # 缺文件/无权限/坏 json：证据缺一块，不影响判定
        return None
    return data if isinstance(data, dict) else None


def _kwargs(call: dict) -> dict:
    kw = call.get("kwargs")
    return kw if isinstance(kw, dict) else {}


def _calls(frame: dict) -> list[dict]:
    """`steps[i].program.calls` → call 列表（任一层缺/类型不对 → 空）。"""
    program = frame.get("program")
    calls = program.get("calls") if isinstance(program, dict) else None
    if not isinstance(calls, list):
        return []
    return [c for c in calls if isinstance(c, dict)]


def _thought(calls: Sequence[dict]) -> str | None:
    """模型逐步推理原文 = `name == "think"` 的 call 的 `kwargs.value`；多个换行拼接，无则 None。"""
    values = [
        str(_kwargs(c)["value"])
        for c in calls
        if c.get("name") == _THINK and _kwargs(c).get("value") is not None
    ]
    return "\n".join(values) if values else None


def _actions(calls: Sequence[dict]) -> list[dict]:
    """引擎动作 = `name` 不为 think / return 的 call（如 agentType / waitForPageToSettle / takeObservation）。

    `args` 是 SDK 原样透传的对象、内部键随 SDK 版本漂——不属本 schema 的契约面（消费端不许下钻）。
    """
    return [
        {"name": c.get("name"), "args": _kwargs(c)}
        for c in calls
        if c.get("name") not in (_THINK, _RETURN)
    ]


def act_evidence(record: ActRecord, trajectory: dict | None) -> dict:
    """一个 act 的 evidence（纯映射，无 IO）：frames / url / result 取自 trajectory，其余取自 record。

    `frames` 与 `steps` **逐位对齐**（非 dict 的 step 也占一格、当空 frame）：截图文件名 `act-<i>-frame-<j>.jpg`
    的 j 就是这个位序，错位会让 evidence 指向别的帧。`screenshot` 一律先置 None，由 `select_screenshots` 选中者补。
    """
    steps = trajectory.get("steps") if isinstance(trajectory, dict) else None
    steps = steps if isinstance(steps, list) else []
    frames: list[dict] = []
    result: Any = None
    for raw in steps:
        frame = raw if isinstance(raw, dict) else {}
        calls = _calls(frame)
        frames.append({
            "url": frame.get("active_url"),
            "thought": _thought(calls),
            "actions": _actions(calls),
            "screenshot": None,
        })
        for c in calls:
            if c.get("name") == _RETURN:
                result = _kwargs(c)   # 正常只有末帧一个 return；多个取末个（终止那次）
    tw = record.time_worked_s
    if tw is None:
        # 容缺回落：同一 act 的 json 里也有这个量（`metadata.time_worked_s`），worker 侧没拿到时读它
        md = trajectory.get("metadata") if isinstance(trajectory, dict) else None
        tw = md.get("time_worked_s") if isinstance(md, dict) else None
    return {
        "index": record.index,
        "prompt": record.prompt,
        "vote": record.vote,
        "url": frames[-1]["url"] if frames else None,   # 调用结束时的页面 = 末 frame 的 active_url
        "frames": frames,
        "result": result,
        "error": record.error,
        "time_worked_s": tw,
    }


def step_evidence(
    *,
    scope_id: str | None,
    scenario_id: str | None,
    step_index: int,
    keyword: str | None,
    text: str | None,
    status: str | None,
    message: str | None = None,
    acts: Sequence[ActRecord],
    trajectories: Sequence[dict | None],
) -> dict:
    """整份 evidence 文档（纯映射，无 IO）。`trajectories` 与 `acts` 按位对应（缺 → None → frames []）。

    `status` / `message` 冗余自本步 step_done（文件自包含，ADR 0042 决策一），故调用方应直接从要 emit 的
    事件里取、别另算一份（两份会漂）。
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "engine": ENGINE,
        "scope_id": scope_id,
        "scenario_id": scenario_id,
        "step_index": step_index,
        "step": {"keyword": keyword, "text": text},
        "status": status,
        "message": message,
        "acts": [
            act_evidence(a, trajectories[i] if i < len(trajectories) else None)
            for i, a in enumerate(acts)
        ],
    }


def select_screenshots(doc: dict) -> list[tuple[int, int]]:
    """选出要落盘的截图 `(act 位序, frame 位序)`，带上界（ADR 0042 决策一 截图策略）。

    - failed / error：每 act 候选 = 末帧、首个含 thought 的帧，去重后取前 K；每 step 总数再封 M。
      ADR 那组候选的第三项「出错帧」在 Nova 侧**无对应物**——抛错的 act 根本没有 json（frames 为空），
      frame 自身也不带错误标记；K 仍按 3 留着上界不动。
    - passed：每 act 只留末帧一张。
    M 对 passed 档实际不可达（每 act 一张、票数远小于 M），仍统一施加，免出现第二条计数路径。
    """
    per_act = MAX_SHOTS_PER_ACT if doc.get("status") in _FAILING else 1
    picks: list[tuple[int, int]] = []
    for i, act in enumerate(doc.get("acts") or []):
        frames = act.get("frames") or []
        if not frames:
            continue
        candidates = [len(frames) - 1]                      # 末帧（判否理由通常落在最后一次观察）
        if per_act > 1:
            first_thought = next((j for j, f in enumerate(frames) if f.get("thought")), None)
            if first_thought is not None:
                candidates.append(first_thought)
        chosen: list[int] = []
        for j in candidates:
            if j not in chosen:                             # 去重（单帧 act 的末帧就是首个含 thought 帧）
                chosen.append(j)
        for j in chosen[:per_act]:
            if len(picks) >= MAX_SHOTS_PER_STEP:
                return picks
            picks.append((i, j))
    return picks


def _decode_data_url(image: Any) -> bytes | None:
    """`steps[i].image`（data URL base64 jpeg）→ 字节；非 data URL / 解不开 / 空 → None（截图给 null）。"""
    if not isinstance(image, str):
        return None
    m = _DATA_URL.match(image)
    if not m:
        return None
    try:
        raw = base64.b64decode(image[m.end():], validate=True)
    except (binascii.Error, ValueError):
        return None
    return raw or None


def scenario_key(scenario_id: str | None) -> str:
    """`<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。

    **必须确定性且不二次撞名**：产物目录按 run 共享、S3 key 镜像相对路径，同一 run 内所有 scope 共用这一命名
    空间；撞名的表现是两条 scenario 的 evidence 静默互相覆盖、读到的 thought 属于另一条且无从察觉。转义会把
    `a/b.feature:1` 与 `a-b.feature-1` 压成同一串，哈希把它们分开。
    **不用显示名**：标题不唯一（同文件重名只靠 id 区分、`@scope` 又允许跨文件合并成一个 job）。
    """
    sid = scenario_id or ""
    slug = _KEY_UNSAFE.sub("-", sid).strip("-.")[:_KEY_SLUG_MAX].strip("-.")
    digest = hashlib.sha256(sid.encode("utf-8")).hexdigest()[:_KEY_HASH_LEN]
    return f"{slug}-{digest}" if slug else digest


def step_dir(base_dir: str | Path, scenario_id: str | None, step_index: int) -> Path:
    """本 step 的 evidence 目录：`<NOVA_LOGS_DIR>/evidence/<scenario 键>/step-<n>/`。

    落在引擎自己的产物目录内（ADR 0042 决策一）：两引擎上传器的 S3 key 都相对各自 run 目录算，复用既有上传器
    （key 计算、幂等去重、scope 末整目录递归 flush）而不引入新的注入 env 与上传根。
    """
    return Path(base_dir) / "evidence" / scenario_key(scenario_id) / f"step-{step_index}"


def write_step_evidence(
    *,
    base_dir: str | Path,
    scope_id: str | None,
    scenario_id: str | None,
    step_index: int,
    keyword: str | None,
    text: str | None,
    status: str | None,
    message: str | None,
    acts: Sequence[ActRecord],
    ref_for: Callable[[str], str],
) -> WrittenEvidence:
    """落 `evidence.json` + 选中的截图，回传两者的本地路径（去向不同，见 `WrittenEvidence`）。

    `ref_for`：本地路径 → 该文件**将来**的 ref（`file://` / `s3://`），只算不传——截图字节由调用方在
    `step_done` emit 之后交给上传器的后台队列（ADR 0042 决策一）。**回传的截图路径正是入队清单**：只含真写下
    的那些（解不开的图留 null、不落盘、也不入队），故队列里不会有幻影文件。
    单张截图解不开就留 null、不打断整份 evidence（逐字段容缺）。
    """
    trajectories = [read_trajectory(a.trajectory_path) for a in acts]
    doc = step_evidence(
        scope_id=scope_id, scenario_id=scenario_id, step_index=step_index,
        keyword=keyword, text=text, status=status, message=message,
        acts=acts, trajectories=trajectories,
    )
    out = step_dir(base_dir, scenario_id, step_index)
    out.mkdir(parents=True, exist_ok=True)
    shots: list[str] = []
    for i, j in select_screenshots(doc):
        steps = (trajectories[i] or {}).get("steps") or []
        raw = _decode_data_url(steps[j].get("image") if j < len(steps) and isinstance(steps[j], dict) else None)
        if raw is None:
            continue
        shot = out / f"act-{doc['acts'][i].get('index', i)}-frame-{j}.jpg"
        shot.write_bytes(raw)
        doc["acts"][i]["frames"][j]["screenshot"] = ref_for(str(shot))
        shots.append(str(shot))
    path = out / "evidence.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return WrittenEvidence(json_path=str(path), screenshots=shots)
