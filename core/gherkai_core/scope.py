"""scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。

对外入口 plan(features, config) -> list[Job]：core 的窄腰第一步（解析→分组），
产出的 Job 正是 worker↔core 协议（ADR 0024）的输入形状。

语义（ADR 0025）：
- @scope 全局命名空间：相同值同 scope，跨文件合并（合并时 warning log）；未标各自单元素 scope。
- engine：scope 内缺省用 config.default_engine；任一 scenario 标了则全 scope 继承；多个不同值报错。
- timeout：scope 内缺省用 config.default_job_timeout_s（未给=不超时）；任一 scenario 标了 @timeout:N 则全 scope 继承；
  同 scope 多个不同值 / 非有限正数 → 报错（tag 语义权威在 ADR 0019）。
- 一个 scenario 多个不同 @scope 值（feature 级传播 + scenario 级）→ 报错（与 engine 冲突对称）。
- id 派生：有 @scope 用其值；无标用 scenario 的 id/标题。
"""
from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass

from gherkai_core.model import Job
from gherkai_core.errors import PlanError  # re-export（既有 `from gherkai_core.scope import PlanError` 不变）
from gherkai_core.parse import ParsedScenario, parse_feature

logger = logging.getLogger("gherkai_core.scope")

_SCOPE_PREFIX = "@scope:"
_ENGINE_PREFIX = "@engine:"
_TIMEOUT_PREFIX = "@timeout:"


@dataclass(frozen=True)
class FeatureSource:
    """plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。"""

    uri: str
    text: str


@dataclass(frozen=True)
class PlanConfig:
    default_engine: str
    # AI 断言投票次数缺省（ADR 0014）：无 per-scope 覆盖时所有 job 用它。默认 1（不抖动检测）。
    # 与 default_engine 对称——未来可由 @votes: tag per-scope 覆盖（留口子，现不实现）。
    default_assertion_votes: int = 1
    # job 墙钟预算秒缺省（ADR 0019 @timeout / ADR 0034「job timeout」节）：未标 @timeout: 的 scope 用它，
    # 与 default_engine 同构。None=不超时。
    default_job_timeout_s: float | None = None


def _values_with_prefix(tags: tuple[str, ...], prefix: str, where: str) -> list[str]:
    """从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where = 出错时的定位（scenario id，即 uri:line）。"""
    seen: list[str] = []
    for t in tags:
        if t.startswith(prefix):
            v = t[len(prefix):]
            if not v:
                # 空值 fail-fast（ADR 0025，与 @timeout 立场一致：标了 tag 就得给有效值、想走缺省就删 tag）。否则裸 @scope:
                # 会跨文件静默合并成一个空名 scope、裸 @engine: 会把 engine 置成空串顶掉缺省。
                raise PlanError(f"{where}：tag {t!r} 缺少值：标了 {prefix} 就得给值（想走缺省就删掉这个 tag）")
            if v not in seen:
                seen.append(v)
    return seen


def _scope_key(parsed: ParsedScenario) -> tuple[str | None, str]:
    """解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。

    多个不同 @scope 值 → PlanError（ADR 0025，与 engine 冲突对称）。
    """
    scope_values = _values_with_prefix(parsed.tags, _SCOPE_PREFIX, parsed.scenario.id)
    if len(scope_values) > 1:
        raise PlanError(
            f"scenario {parsed.scenario.id!r} 解析出多个 @scope 值 {scope_values}："
            f"一个 scenario 只能属一个 scope（会话边界）。"
            f"检查 feature 级 @scope 传播是否与 scenario 级 @scope 冲突。"
        )
    return (scope_values[0] if scope_values else None), parsed.scenario.id


def _resolve_engine(scope_id: str, members: list[ParsedScenario], default_engine: str) -> str:
    """解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。"""
    engines: list[str] = []
    for m in members:
        for v in _values_with_prefix(m.tags, _ENGINE_PREFIX, m.scenario.id):
            if v not in engines:
                engines.append(v)
    if len(engines) > 1:
        raise PlanError(
            f"scope {scope_id!r} 出现多个 @engine 值 {engines}："
            f"同一 scope 跨引擎 = 物理自相矛盾（共享会话又是两个不共享的会话），拒绝运行。"
        )
    return engines[0] if engines else default_engine


def _resolve_timeout(scope_id: str, members: list[ParsedScenario], default: float | None) -> float | None:
    """解析一个 scope 的 job 墙钟预算：与 _resolve_engine 同构（ADR 0019 @timeout）。

    缺省用 default；任一标了 @timeout:N 则全 scope 继承；多个不同值 → PlanError（同 scope 一个预算）。
    N 必须是**有限**正数（非数字 / <=0 / nan / inf → PlanError——「标了 tag 但想不超时」不成立，删 tag
    走缺省即可）。nan/inf 须显式拒：`float()` 收它们（`float("nan")`/`"inf"`/`"1e400"` 都不抛），而下游
    推进器一律用 `>` 比较 deadline，nan/inf 会让超时保护静默失效（标了 tag 却永不超时）。
    """
    raws: list[str] = []
    for m in members:
        for v in _values_with_prefix(m.tags, _TIMEOUT_PREFIX, m.scenario.id):
            if v not in raws:
                raws.append(v)
    if len(raws) > 1:
        raise PlanError(
            f"scope {scope_id!r} 出现多个 @timeout 值 {raws}："
            f"同一 scope（一个 job）只能有一个墙钟预算，拒绝运行。"
        )
    if not raws:
        return default
    raw = raws[0]
    try:
        n = float(raw)
    except ValueError:
        raise PlanError(f"scope {scope_id!r} 的 @timeout:{raw} 不是数字：须为正数秒。") from None
    if not math.isfinite(n) or n <= 0:
        raise PlanError(
            f"scope {scope_id!r} 的 @timeout:{raw} 须为正数秒；不想超时就删掉 tag 走缺省。"
        )
    return n


def plan(features: list[FeatureSource], config: PlanConfig, *,
         select: Callable[[ParsedScenario, str], bool] | None = None) -> list[Job]:
    """core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。

    select（ADR 0041 决策一）：scenario 筛选谓词，在 **scope 分组与 engine/timeout 解析之后、Job 组装之前**施加。
    不变量：筛选只减少「跑哪几条」——scope 的引擎、墙钟预算、会话身份一律按**全量**成员解析，与不筛时逐字一致（否则筛后
    跑的与全量跑的不是同一件事，迭代结论不可迁移）。整组被筛空的 scope 不进任何 job（且在解析 engine/timeout 之前跳过，
    它内部的 tag 冲突不拦本次迭代）；`_scope_key` 仍对全量成员校验（一个 scenario 多个 @scope 照样 fail-fast）。None = 不筛。
    谓词由调用方按 `--scope/--tags/--scenario` 组装，core 只收 `(ParsedScenario, scope_id) → bool`、不认 flag 语义
    （scope_id 一并传入：业务概念「scope」的筛选按分组键判，不逼调用方从 tags 反推）。筛后为空返回 []。

    严格契约：`features` 的 uri 必须互异（uri 是 scenarioId 前缀，重复会撞 id）。重复 → PlanError。
    这是**接口违约**校验，与「跨文件同 @scope 合并」（领域语义、warning、见下文 scope 分组）正交：
    前者防脏输入（同一文件喂两遍），后者是有意的跨文件会话共享。收集 feature 时的去重等便利逻辑
    由调用方（CLI/WebUI）负责，core 窄腰只接 uri 互异的列表（ADR 0025）。
    """
    # 0) 入口校验：uri 互异（接口违约则 fail-fast，不静默吞——ADR 0025）
    seen_uris: set[str] = set()
    for f in features:
        if f.uri in seen_uris:
            raise PlanError(
                f"features 含重复 uri {f.uri!r}：uri 是 scenarioId 前缀，重复会撞 id。"
                f"core 窄腰要求 uri 互异（调用方负责收集时去重）。"
            )
        seen_uris.add(f.uri)

    # 1) 解析所有 feature → ParsedScenario（带 tags）。select 不在此施加：分组与 engine/timeout 要看全量成员（ADR 0041 决策一）
    all_parsed: list[ParsedScenario] = []
    for f in features:
        all_parsed.extend(parse_feature(f.uri, f.text))

    # 2) 按 @scope 分组（全局命名空间）；未标的各自单元素 scope
    #    分组键：有 @scope → 用其值；无标 → 用 scenario_id（保证各自独立、不撞）
    groups: dict[str, list[ParsedScenario]] = {}
    group_is_named: dict[str, bool] = {}  # 该组是否来自显式 @scope（用于 warning + name 派生）
    for parsed in all_parsed:
        scope_value, scenario_id = _scope_key(parsed)  # 对全量成员校验：一个 scenario 多个 @scope 不因被筛掉而放过
        if scope_value is not None:
            key = scope_value
            group_is_named[key] = True
        else:
            key = scenario_id  # 未标 scope：自成单元素 scope，键 = scenario_id（ADR 0025）
            group_is_named[key] = False
        groups.setdefault(key, []).append(parsed)

    # 3) 每组：engine/timeout 按**全量**成员解析（不变量：筛选只减少跑哪几条，不改 scope 的引擎、预算、会话身份），
    #    再施加 select 取本次要跑的成员；整组筛空则不进任何 job——且在解析之前跳过，被筛掉的 scope 里的 @engine/@timeout
    #    冲突不拦本次迭代（ADR 0041 决策一）。
    jobs: list[Job] = []
    picked_uris: dict[str, set[str]] = {}  # 实际要跑的成员所在 uri（跨文件合并 warning 按它算，别报不会跑的文件）
    for key, members in groups.items():
        picked = members if select is None else [m for m in members if select(m, key)]
        if not picked:
            continue
        engine = _resolve_engine(key, members, config.default_engine)
        timeout_s = _resolve_timeout(key, members, config.default_job_timeout_s)
        named = group_is_named.get(key, False)
        if named:
            scope_id = key
            scope_name = key  # @scope 原值（人写名）
        else:
            # 未标 scope：scope_id = scenario_id；scope_name = scenario 标题（人写名，不复用机器键，ADR 0025）
            scope_id = key
            scope_name = picked[0].scenario.name
        jobs.append(
            Job(
                scope_id=scope_id,
                scope_name=scope_name,
                engine=engine,
                scenarios=tuple(m.scenario for m in picked),  # 丢弃 tags，Scenario 保持纯净
                assertion_votes=config.default_assertion_votes,  # per-scope 覆盖留口子（@votes:），现统一用缺省
                timeout_s=timeout_s,
            )
        )
        picked_uris[key] = {m.uri for m in picked}  # 权威 uri（parse 时已知），不从 id 有损反解

    # 4) 跨文件合并 warning（ADR 0025）：一个 named scope **要跑的**成员跨多个 uri
    for key, uris in picked_uris.items():
        if group_is_named.get(key) and len(uris) > 1:
            logger.warning(
                "scope %r 跨 %d 个 feature 文件合并（%s）：这些文件的 scenario 将串行共享同一会话。"
                "若非有意，检查是否 @scope 撞名。",
                key, len(uris), ", ".join(sorted(uris)),
            )
    return jobs
