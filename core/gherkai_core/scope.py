"""scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine 校验 → Job[]。

对外入口 plan(features, config) -> list[Job]：core 的窄腰第一步（解析→分组），
产出的 Job 正是 worker↔core 协议（ADR 0024）的输入形状。

语义（ADR 0025）：
- @scope 全局命名空间：相同值同 scope，跨文件合并（合并时 warning log）；未标各自单元素 scope。
- engine：scope 内缺省用 config.default_engine；任一 scenario 标了则全 scope 继承；多个不同值报错。
- 一个 scenario 多个不同 @scope 值（feature 级传播 + scenario 级）→ 报错（与 engine 冲突对称）。
- id 派生：有 @scope 用其值；无标用 scenario 的 id/标题。
"""
from __future__ import annotations

import logging
import math
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


def _values_with_prefix(tags: tuple[str, ...], prefix: str) -> list[str]:
    """从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。"""
    seen: list[str] = []
    for t in tags:
        if t.startswith(prefix):
            v = t[len(prefix):]
            if v not in seen:
                seen.append(v)
    return seen


def _scope_key(parsed: ParsedScenario) -> tuple[str | None, str]:
    """解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。

    多个不同 @scope 值 → PlanError（ADR 0025，与 engine 冲突对称）。
    """
    scope_values = _values_with_prefix(parsed.tags, _SCOPE_PREFIX)
    if len(scope_values) > 1:
        raise PlanError(
            f"scenario {parsed.scenario.id!r} 解析出多个 @scope 值 {scope_values}："
            f"一个 scenario 只能属一个 scope（会话边界）。"
            f"检查 feature 级 @scope 传播是否与 scenario 级 @scope 冲突（ADR 0025）。"
        )
    return (scope_values[0] if scope_values else None), parsed.scenario.id


def _resolve_engine(scope_id: str, members: list[ParsedScenario], default_engine: str) -> str:
    """解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。"""
    engines: list[str] = []
    for m in members:
        for v in _values_with_prefix(m.tags, _ENGINE_PREFIX):
            if v not in engines:
                engines.append(v)
    if len(engines) > 1:
        raise PlanError(
            f"scope {scope_id!r} 出现多个 @engine 值 {engines}："
            f"同一 scope 跨引擎 = 物理自相矛盾（共享会话又是两个不共享的会话），拒绝运行（ADR 0019）。"
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
        for v in _values_with_prefix(m.tags, _TIMEOUT_PREFIX):
            if v not in raws:
                raws.append(v)
    if len(raws) > 1:
        raise PlanError(
            f"scope {scope_id!r} 出现多个 @timeout 值 {raws}："
            f"同一 scope（一个 job）只能有一个墙钟预算，拒绝运行（ADR 0019）。"
        )
    if not raws:
        return default
    raw = raws[0]
    try:
        n = float(raw)
    except ValueError:
        raise PlanError(f"scope {scope_id!r} 的 @timeout:{raw} 不是数字：须为正数秒（ADR 0019）。") from None
    if not math.isfinite(n) or n <= 0:
        raise PlanError(
            f"scope {scope_id!r} 的 @timeout:{raw} 须为正数秒（ADR 0019）；不想超时就删掉 tag 走缺省。"
        )
    return n


def plan(features: list[FeatureSource], config: PlanConfig) -> list[Job]:
    """core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。

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

    # 1) 解析所有 feature → ParsedScenario（带 tags）
    all_parsed: list[ParsedScenario] = []
    for f in features:
        all_parsed.extend(parse_feature(f.uri, f.text))

    # 2) 按 @scope 分组（全局命名空间）；未标的各自单元素 scope
    #    分组键：有 @scope → 用其值；无标 → 用 scenario_id（保证各自独立、不撞）
    groups: dict[str, list[ParsedScenario]] = {}
    group_is_named: dict[str, bool] = {}  # 该组是否来自显式 @scope（用于 warning + name 派生）
    group_uris: dict[str, set[str]] = {}  # 该 scope 出现在哪些 uri（检测跨文件合并）

    for parsed in all_parsed:
        scope_value, scenario_id = _scope_key(parsed)
        if scope_value is not None:
            key = scope_value
            group_is_named[key] = True
        else:
            key = scenario_id  # 未标 scope：自成单元素 scope，键 = scenario_id（ADR 0025）
            group_is_named[key] = False
        groups.setdefault(key, []).append(parsed)
        group_uris.setdefault(key, set()).add(parsed.uri)  # 权威 uri（parse 时已知），不从 id 有损反解

    # 3) 跨文件合并 warning（ADR 0025）：一个 named scope 跨多个 uri
    for key, uris in group_uris.items():
        if group_is_named.get(key) and len(uris) > 1:
            logger.warning(
                "scope %r 跨 %d 个 feature 文件合并（%s）：这些文件的 scenario 将串行共享同一会话。"
                "若非有意，检查是否 @scope 撞名（ADR 0025）。",
                key, len(uris), ", ".join(sorted(uris)),
            )

    # 4) 每组解析 engine + 派生 scope 名 → 组装 Job
    jobs: list[Job] = []
    for key, members in groups.items():
        engine = _resolve_engine(key, members, config.default_engine)
        timeout_s = _resolve_timeout(key, members, config.default_job_timeout_s)
        named = group_is_named.get(key, False)
        if named:
            scope_id = key
            scope_name = key  # @scope 原值（人写名）
        else:
            # 未标 scope：scope_id = scenario_id；scope_name = scenario 标题（人写名，不复用机器键，ADR 0025）
            scope_id = key
            scope_name = members[0].scenario.name
        jobs.append(
            Job(
                scope_id=scope_id,
                scope_name=scope_name,
                engine=engine,
                scenarios=tuple(m.scenario for m in members),  # 丢弃 tags，Scenario 保持纯净
                assertion_votes=config.default_assertion_votes,  # per-scope 覆盖留口子（@votes:），现统一用缺省
                timeout_s=timeout_s,
            )
        )
    return jobs
