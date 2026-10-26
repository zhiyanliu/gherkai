"""scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。

对外入口 plan(features, config) -> list[Job]：core 的窄腰第一步（解析→分组），
产出的 Job 正是 worker↔core 协议（ADR 0024）的输入形状。

语义（ADR 0025）：
- @scope 全局命名空间：相同值同 scope，跨文件合并（合并时 warning log）；未标各自单元素 scope。
- engine：scope 内缺省用 config.default_engine；任一 scenario 标了则全 scope 继承；多个不同值报错。
- device / app（ADR 0048 决策 2）：@device:android|ios 与 @app:<别名> 按 engine 同样的三条规则归约到 scope；不标即桌面网页；
  @device 取值不在 android / ios 之内、@app 用在桌面、别名不在 config.apps 里或缺本平台条目 → 报错。
- timeout（ADR 0034「job timeout」节、0051 决策 2）：任一 scenario 标了 @timeout:N 则全 scope 继承；否则用显式给出的
  config.default_job_timeout_s；都没有则按目标补缺省（桌面 default_desktop_job_timeout_s、设备 default_device_job_timeout_s）；
  显式非正值只让非设备 scope 不超时，设备 scope 落到设备缺省；设备 scope 的 tag 或显式正值低于 min_device_job_timeout_s → 报错；
  同 scope 多个不同值 / 非有限正数 → 报错（tag 语义权威在 ADR 0019）。
- 一个 scenario 多个不同 @scope 值（feature 级传播 + scenario 级）→ 报错（与 engine 冲突对称）。
- id 派生：有 @scope 用其值；无标用 scenario 的 id/标题；两者共用一个 scope_id 命名空间（下游主键），
  @scope 的值撞上某条未标 scenario 的 id → 报错（撞 id 意味着静默丢结果，与裸 `@scope:` 同立场）。
"""
from __future__ import annotations

import logging
import math
from collections.abc import Callable
from dataclasses import dataclass, field

from gherkai_core.model import DEFAULT_ACQUIRE_TIMEOUT_S, AppRef, Job, Target
from gherkai_core.errors import FeatureContractError  # re-export（既有 `from gherkai_core.scope import FeatureContractError` 不变）
from gherkai_core.parse import ParsedScenario, parse_feature

logger = logging.getLogger("gherkai_core.scope")

_SCOPE_PREFIX = "@scope:"
_ENGINE_PREFIX = "@engine:"
_TIMEOUT_PREFIX = "@timeout:"
_DEVICE_PREFIX = "@device:"
_APP_PREFIX = "@app:"
_DEVICES = ("android", "ios")  # @device 的合法取值（桌面不标，ADR 0048 决策 2）


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
    # 显式给出的 --default-job-timeout（ADR 0019 @timeout / ADR 0034「job timeout」节）：None 表示**未指定**（按目标补缺省），
    # 非正值表示「非设备 scope 不超时」（设备 scope 仍取设备缺省），正值对设备 scope 要过下限校验。
    default_job_timeout_s: float | None = None
    # 按目标的缺省与下限（ADR 0034「job timeout」节、0051 决策 2）：CLI 按获取预算算出传入；这里的缺省按内建获取预算推出，
    # 让直接构造 PlanConfig 的调用方（测试、工具）不必都传。目标缺省自身不过下限校验。
    default_desktop_job_timeout_s: float = 300.0
    default_device_job_timeout_s: float = DEFAULT_ACQUIRE_TIMEOUT_S + 900.0
    min_device_job_timeout_s: float = DEFAULT_ACQUIRE_TIMEOUT_S + 180.0
    # 应用别名表（ADR 0048 决策 2 / 0053 [apps]）：别名 → 平台 → 包名或 bundle id，纯数据、不带文件路径；core 据此核对 @app。
    apps: dict[str, dict[str, str]] = field(default_factory=dict)


def _values_with_prefix(tags: tuple[str, ...], prefix: str, where: str) -> list[str]:
    """从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即 uri:line）。"""
    seen: list[str] = []
    for t in tags:
        if t.startswith(prefix):
            v = t[len(prefix):]
            if not v:
                # 空值 fail-fast（ADR 0025，与 @timeout 立场一致：标了 tag 就得给有效值、想走缺省就删 tag）。否则裸 @scope:
                # 会跨文件静默合并成一个空名 scope、裸 @engine: 会把 engine 置成空串顶掉缺省。
                raise FeatureContractError(f"{where}：tag {t!r} 缺少值：标了 {prefix} 就得给值（想走缺省就删掉这个 tag）")
            if v not in seen:
                seen.append(v)
    return seen


def _scope_key(parsed: ParsedScenario) -> tuple[str | None, str]:
    """解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。

    多个不同 @scope 值 → FeatureContractError（ADR 0025，与 engine 冲突对称）。
    """
    scope_values = _values_with_prefix(parsed.tags, _SCOPE_PREFIX, parsed.scenario.id)
    if len(scope_values) > 1:
        raise FeatureContractError(
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
        raise FeatureContractError(
            f"scope {scope_id!r} 出现多个 @engine 值 {engines}："
            f"同一 scope 跨引擎在物理上自相矛盾（共享会话又是两个不共享的会话），拒绝运行。"
        )
    return engines[0] if engines else default_engine


def _resolve_target(scope_id: str, members: list[ParsedScenario], apps: dict[str, dict[str, str]]) -> Target:
    """解析一个 scope 的测试目标（ADR 0048 决策 2）：@device 与 @app 各按 engine 同样的三条规则归约（任一成员标了即整个 scope
    生效、feature 级由 scenario 继承、同一 scope 取值不一致即报错），两个维度分别判冲突。不标即桌面网页。

    另四种情形同样报 FeatureContractError：@device 取值不是 android / ios（显式写 @device:desktop 也不接受）；@app 出现在桌面
    scope；别名在 apps 里查不到；别名缺本平台的条目。apps 是组合根从项目配置读出的纯数据表（别名 → 平台 → 包名或 bundle id）。"""
    devices: list[str] = []
    aliases: list[str] = []
    for m in members:
        for v in _values_with_prefix(m.tags, _DEVICE_PREFIX, m.scenario.id):
            if v not in devices:
                devices.append(v)
        for v in _values_with_prefix(m.tags, _APP_PREFIX, m.scenario.id):
            if v not in aliases:
                aliases.append(v)
    if len(devices) > 1:
        raise FeatureContractError(
            f"scope {scope_id!r} 出现多个 @device 值 {devices}：同一 scope 共享一个会话，不能既在一种设备上又在另一种设备上执行，拒绝运行。"
        )
    if len(aliases) > 1:
        raise FeatureContractError(
            f"scope {scope_id!r} 出现多个 @app 值 {aliases}：同一 scope 共享一个会话，一个会话里只能是一个应用，拒绝运行。"
        )
    device = devices[0] if devices else "desktop"
    if devices and device not in _DEVICES:
        raise FeatureContractError(
            f"scope {scope_id!r} 的 @device:{device} 不是 android 或 ios（桌面网页不用标 @device，删掉这个 tag 即可）。"
        )
    if not aliases:
        return Target(device=device, ui_kind="web")
    alias = aliases[0]
    if device == "desktop":
        raise FeatureContractError(
            f"scope {scope_id!r} 标了 @app:{alias} 却没有标 @device：应用目标只在 Android 或 iOS 设备上，请加 @device:android 或 @device:ios。"
        )
    entry = apps.get(alias)
    if entry is None:
        raise FeatureContractError(
            f"scope {scope_id!r} 的 @app:{alias} 在项目配置的 [apps] 里查不到：请在 gherkai.toml 的 [apps.{alias}] 下给出该应用在各平台的安装包与包名。"
        )
    app_id = entry.get(device)
    if not isinstance(app_id, str) or not app_id:
        raise FeatureContractError(
            f"scope {scope_id!r} 的 @app:{alias} 在 [apps] 里没有 {device} 平台的条目：请在 gherkai.toml 的 [apps.{alias}.{device}] 下给出安装包与包名或 bundle id。"
        )
    return Target(device=device, ui_kind="app", app=AppRef(alias=alias, app_id=app_id))


def _resolve_timeout(scope_id: str, members: list[ParsedScenario], config: PlanConfig, target: Target) -> float | None:
    """解析一个 scope 的 job 墙钟预算（ADR 0019 @timeout；覆盖与校验顺序归 ADR 0034「job timeout」节、0051 决策 2）。

    ① 按来源取值：任一成员标了 @timeout:N 则全 scope 继承；否则用显式给出的 config.default_job_timeout_s；都没有则按目标补缺省
    （桌面 default_desktop_job_timeout_s，设备 default_device_job_timeout_s）。② 显式非正值只表示「非设备 scope 不超时」，设备
    scope 在这一步落到设备缺省、不报错（设备 scope 不存在不超时）。③ 下限只校验 tag 与显式正值：设备 scope 低于
    min_device_job_timeout_s 报错，消息说明可能还没拿到设备就被判超时；目标缺省自身不校验。
    多个不同 tag 值 → FeatureContractError（同 scope 一个预算）。N 必须是**有限**正数（非数字 / <=0 / nan / inf →
    FeatureContractError——「标了 tag 但想不超时」不成立，删 tag 走缺省即可）。nan/inf 须显式拒：`float()` 收它们
    （`float("nan")`/`"inf"`/`"1e400"` 都不抛），而下游推进器一律用 `>` 比较 deadline，nan/inf 会让超时保护静默失效。
    """
    raws: list[str] = []
    for m in members:
        for v in _values_with_prefix(m.tags, _TIMEOUT_PREFIX, m.scenario.id):
            if v not in raws:
                raws.append(v)
    if len(raws) > 1:
        raise FeatureContractError(
            f"scope {scope_id!r} 出现多个 @timeout 值 {raws}："
            f"同一 scope 只能有一个 job 墙钟预算，拒绝运行。"
        )
    is_device = not target.is_desktop
    if raws:
        raw = raws[0]
        try:
            n = float(raw)
        except ValueError:
            raise FeatureContractError(f"scope {scope_id!r} 的 @timeout:{raw} 不是数字：须为正数秒。") from None
        if not math.isfinite(n) or n <= 0:
            raise FeatureContractError(
                f"scope {scope_id!r} 的 @timeout:{raw} 须为正数秒；不想超时就删掉 tag 走缺省。"
            )
        source = f"@timeout:{raw}"
    else:
        explicit = config.default_job_timeout_s
        if explicit is None:
            return config.default_device_job_timeout_s if is_device else config.default_desktop_job_timeout_s
        if not math.isfinite(explicit):
            raise FeatureContractError(f"默认 job 墙钟预算须为有限数，收到 {explicit!r}。")
        if explicit <= 0:
            return config.default_device_job_timeout_s if is_device else None
        n = explicit
        source = f"默认 job 墙钟预算 {explicit:g} 秒"
    if is_device and n < config.min_device_job_timeout_s:
        raise FeatureContractError(
            f"scope {scope_id!r} 的 job 墙钟预算 {n:g} 秒（来自 {source}）低于设备目标的下限 {config.min_device_job_timeout_s:g} 秒："
            f"取设备就可能用掉大部分预算，还没开始执行就会被判超时。请调到至少 {config.min_device_job_timeout_s:g} 秒，"
            f"或删掉它走设备缺省（{config.default_device_job_timeout_s:g} 秒）。"
        )
    return n


def plan(features: list[FeatureSource], config: PlanConfig, *,
         select: Callable[[ParsedScenario, str], bool] | None = None) -> list[Job]:
    """core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。

    select（ADR 0041 决策一）：scenario 筛选谓词，在 **scope 分组与 engine/timeout 解析之后、Job 组装之前**施加。
    不变量：筛选只减少「运行哪几条」——scope 的引擎、job 墙钟预算、会话身份一律按**全量**成员解析，与不筛时逐字一致（否则筛后
    执行的与全量执行的不是同一件事，迭代结论不可迁移）。整组被筛空的 scope 不进任何 job（且在解析 engine/timeout 之前跳过，
    它内部的 tag 冲突不拦本次迭代）；`_scope_key` 仍对全量成员校验（一个 scenario 多个 @scope 照样 fail-fast）。None 表示不筛。
    谓词由调用方按 `--scope/--tags/--scenario` 组装，core 只收 `(ParsedScenario, scope_id) → bool`、不认 flag 语义
    （scope_id 一并传入：业务概念「scope」的筛选按分组键判，不逼调用方从 tags 反推）。筛后为空返回 []。

    严格契约：`features` 的 uri 必须互异（uri 是 scenarioId 前缀，重复会撞 id）。重复 → FeatureContractError。
    这是**接口违约**校验，与「跨文件同 @scope 合并」（领域语义、warning、见下文 scope 分组）正交：
    前者防脏输入（同一文件喂两遍），后者是有意的跨文件会话共享。收集 feature 时的去重等便利逻辑
    由调用方（CLI/WebUI）负责，core 窄腰只接 uri 互异的列表（ADR 0025）。
    """
    # 0) 入口校验：uri 互异（接口违约则 fail-fast，不静默吞——ADR 0025）
    seen_uris: set[str] = set()
    for f in features:
        if f.uri in seen_uris:
            raise FeatureContractError(
                f"同一个 .feature 给了两次：{f.uri!r}（重复会让两份的 scenario 编号撞在一起、结果错乱）。"
                f"每个文件只给一次。"
            )
        seen_uris.add(f.uri)

    # 1) 解析所有 feature → ParsedScenario（带 tags）。select 不在此施加：分组与 engine/timeout 要看全量成员（ADR 0041 决策一）
    all_parsed: list[ParsedScenario] = []
    for f in features:
        all_parsed.extend(parse_feature(f.uri, f.text))

    # 2) 按 @scope 分组（全局命名空间）；未标的各自单元素 scope
    #    分组键是 (是否来自显式 @scope, 键值) 二元组：有 @scope → 其值；无标 → scenario_id（ADR 0025）。
    #    「是否 named」进键、由结构承载——曾用一张 key→bool 边表，两类键撞上时被后写的成员覆盖，
    #    scope_name 与跨文件 warning 都随遍历顺序摆动（顺序依赖的静默错）。
    groups: dict[tuple[bool, str], list[ParsedScenario]] = {}
    for parsed in all_parsed:
        scope_value, scenario_id = _scope_key(parsed)  # 对全量成员校验：一个 scenario 多个 @scope 不因被筛掉而放过
        group_key = (True, scope_value) if scope_value is not None else (False, scenario_id)
        groups.setdefault(group_key, []).append(parsed)

    # 2.1) 两类键共用 scope_id 命名空间（scope_id 就是键值，ADR 0025「id 派生」）：@scope 的值若等于某条未标
    #      scenario 的 id，两个组会派生出同一个 scope_id，而 scope_id 是下游主键（RunState.jobs 的 key、每 job
    #      一个结果文件、claim 的键）→ 状态只剩一个、结果互相覆盖。撞名就是静默灾难，故 fail-fast（与裸 `@scope:`
    #      同立场）。判据用集合交、与遍历顺序无关；且只比**当了分组键**的 id，不误伤「那条 scenario 自己也标了
    #      别的 @scope」的无害输入（它的 id 根本不当键）。
    collided = sorted({k for named, k in groups if named} & {k for named, k in groups if not named})
    if collided:
        joined = "、".join(collided)
        raise FeatureContractError(
            f"@scope 的值和某条 scenario 的编号相同：{joined}。"
            f"没标 @scope 的 scenario 用自己的编号（文件:行号）当会话名，撞上会把两条 scenario 并进同一个会话、"
            f"运行结果互相覆盖。给这个 @scope 换个名字。"
        )

    # 3) 每组：engine/target/timeout 按**全量**成员解析（不变量：筛选只减少运行哪几条，不改 scope 的引擎、目标、预算、会话身份），
    #    再施加 select 取本次要运行的成员；整组筛空则不进任何 job——且在解析之前跳过，被筛掉的 scope 里的 @engine/@device/@timeout
    #    冲突不拦本次迭代（ADR 0041 决策一）。timeout 依赖目标（缺省与下限按目标给），故先解析目标。
    jobs: list[Job] = []
    picked_uris: dict[str, set[str]] = {}  # named scope 实际要运行的成员所在 uri（跨文件合并 warning 按它算，别报不会执行的文件）
    for (named, key), members in groups.items():
        picked = members if select is None else [m for m in members if select(m, key)]
        if not picked:
            continue
        engine = _resolve_engine(key, members, config.default_engine)
        target = _resolve_target(key, members, config.apps)
        timeout_s = _resolve_timeout(key, members, config, target)
        scope_id = key
        if named:
            scope_name = key  # @scope 原值（人写名）
        else:
            # 未标 scope：scope_id 取 scenario_id；scope_name 取 scenario 标题（人写名，不复用机器键，ADR 0025）
            scope_name = picked[0].scenario.name
        jobs.append(
            Job(
                scope_id=scope_id,
                scope_name=scope_name,
                engine=engine,
                scenarios=tuple(m.scenario for m in picked),  # 丢弃 tags，Scenario 保持纯净
                assertion_votes=config.default_assertion_votes,  # per-scope 覆盖留口子（@votes:），现统一用缺省
                timeout_s=timeout_s,
                target=target,  # plan 形态：device_request 留空，由 run / submit 的组合根填（ADR 0048 决策 3）
            )
        )
        if named:
            picked_uris[key] = {m.uri for m in picked}  # 权威 uri（parse 时已知），不从 id 有损反解

    # 4) 跨文件合并 warning（ADR 0025）：一个 named scope **要运行的**成员跨多个 uri
    for key, uris in picked_uris.items():
        if len(uris) > 1:
            logger.warning(
                "scope %r 跨 %d 个 feature 文件合并（%s）：这些文件的 scenario 将串行共享同一会话。"
                "若非有意，检查是否 @scope 撞名。",
                key, len(uris), ", ".join(sorted(uris)),
            )
    return jobs
