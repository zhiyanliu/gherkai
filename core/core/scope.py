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
from dataclasses import dataclass

from core.model import Job
from core.parse import ParsedScenario, parse_feature

logger = logging.getLogger("core.scope")

_SCOPE_PREFIX = "@scope:"
_ENGINE_PREFIX = "@engine:"


class PlanError(ValueError):
    """配置矛盾，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值等。"""


@dataclass(frozen=True)
class FeatureSource:
    """plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。"""

    uri: str
    text: str


@dataclass(frozen=True)
class PlanConfig:
    default_engine: str


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


def plan(features: list[FeatureSource], config: PlanConfig) -> list[Job]:
    """core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。"""
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
        group_uris.setdefault(key, set()).add(_uri_of(scenario_id))

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
            )
        )
    return jobs


def _uri_of(scenario_id: str) -> str:
    """从 scenario_id（<uri>:<line>[:<example>]）取回 uri 部分。

    uri 本身可能含冒号（如 URL），故从右侧剥 1~2 段纯数字行号。
    """
    parts = scenario_id.split(":")
    # 从右往左剥掉连续的纯数字段（行号 / example 行号）
    while len(parts) > 1 and parts[-1].isdigit():
        parts.pop()
    return ":".join(parts)
