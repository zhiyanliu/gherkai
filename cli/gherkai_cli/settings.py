"""项目配置文件合成进命令行选项（ADR 0053 决策 2、3、6）：七个运行侧命令在 parse_args 之后、分派之前经 `apply_project_config` 把 gherkai.toml
的值按「选项 > 环境变量 > 配置文件 > 内建默认」合成进 args；有环境变量层的项不写进 args，经 `identity_layers` / `config_layers` 交给
compose 的解析链放在环境变量之后。[common] / [cloud] 接受的键由 argparse 的选项面差集推出（单一真源在 argparse，三份名单只做归类）。
读文件与形态校验在 `config`；本模块不知道命令的语义，只知道选项面。
"""
from __future__ import annotations

import argparse

from gherkai_cli import config as _config
from gherkai_cli.console import progress


# run / submit 的并发默认值（ADR 0026「并发上限」定为 4）：并发只改同时开几个浏览器会话，不改 job 数与总费用；
# status --wait 与 reconcile 的同名 flag 只是提交记录缺值时的回落，取同一常量避免漂移。
DEFAULT_MAX_CONCURRENCY = 4

# ---- 项目配置文件 gherkai.toml（ADR 0053）：七个运行侧命令读它，合成进「选项 > 环境变量 > 配置文件 > 内建默认」----
CONFIG_COMMANDS = ("run", "plan", "submit", "status", "explain", "doctor", "list-deterministic")
# 按次选择型选项（ADR 0053 决策 3 的排除名单，用 argparse 的 dest 名）：只影响本次的范围、输出形态、中止方式、落盘取舍或
# 查询对象，不进配置文件——写进文件会让某次调用的范围或中止语义在不显眼处改变。护栏 test_project_config 从 argparse 差集
# 核对：七个命令的全部长选项恰好由本名单、CLOUD_OPTIONS、DEVICE_OPTIONS 与 [common] 同词键四者拼成，新增选项漏归类即失败。
PER_CALL_OPTIONS = frozenset({"scope", "tags", "scenario", "step", "json", "quiet", "wait", "all", "full",
                               "fail_fast", "no_report", "engine", "config"})
# 只在 --backend cloud 下起作用的选项 → [cloud] 节；本机后端下 [cloud] 整节静默不生效（ADR 0053 决策 3）
CLOUD_OPTIONS = frozenset({"prefix", "ddb_table", "s3_bucket", "events_table", "cluster", "subnet", "security_group",
                            "worker_variant"})
# 有环境变量层的选项：配置值**不写进 args**（否则配置越过环境变量，正是决策 2 要避免的），而是经各解析链的 config_* 形参
# 插在环境变量之后（prefix / ddb-table / s3-bucket 在 compose.resolve_cloud_target，region / profile 在 resolve_aws_identity，
# steps-dir 在 _steps_dir_or_error）
ENV_LAYER_OPTIONS = frozenset({"prefix", "ddb_table", "s3_bucket", "region", "profile", "steps_dir"})
# 设备专用选项 → [devices] 的键（ADR 0053 决策 6 映射表）：命令行平铺带平台前缀、配置文件有节层级；它们有环境变量层
# （GHERKAI_*），解析在设备请求解析那一步、不经本节的同词规则
DEVICE_OPTIONS = {"android_device_arn": ("devices.android", "arn"), "ios_device_arn": ("devices.ios", "arn"),
                   "device_farm_project_arn": ("devices", "project-arn"), "app_bucket": ("devices", "app-bucket")}
# 只对本机后端起作用的 [common] 键 → --backend cloud 下不写进 args、不做校验，只在 run / submit 上提示一句（ADR 0053 决策 3，
# 与 project-arn / app-bucket 同一形态：同一份项目文件要同时服务本机与云端，用不到的值不拦）。命令行上显式给出的值不受影响、
# 仍由入口拒绝（ADR 0024「引擎自报下限」条）。值是提示里的理由（产品语言）。steps-dir 同属本机专用，但有环境变量层，
# 它的提示在 steps 目录解析那一步。
LOCAL_ONLY_OPTIONS = {"grace": "grace 只对本机运行起作用，云端 worker 的停止宽限由部署时的 gherkai deploy --stop-timeout 决定"}
LOCAL_ONLY_NOTICE_COMMANDS = ("run", "submit")
# 内建默认：argparse 侧这些选项改成 None 哨兵（分得出「使用方没给」），配置合成之后在这里补
BUILTIN_DEFAULTS = {"default_engine": "novaact", "assertion_votes": 1, "max_concurrency": DEFAULT_MAX_CONCURRENCY,
                     "report_dir": "reports", "backend": "local", "tunnel": "ngrok"}


# argparse 没有公开的反射接口：取子命令、列选项、判「可重复给」只能走它的私有属性。三处私有访问全部集中在下面三个小函数里，
# 其余代码只认它们；argparse 的这几个名字十多年未变，真变时只改这里。单一真源的理由见 configurable_keys。
def subparser(parser: argparse.ArgumentParser, name: str) -> argparse.ArgumentParser:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices[name]
    raise KeyError(name)


def option_actions(parser: argparse.ArgumentParser, name: str) -> list:
    """某子命令的全部选项定义（不含位置参数与 --help）。"""
    return [a for a in subparser(parser, name)._actions if a.option_strings and a.dest != "help"]


def _is_repeatable(action) -> bool:
    """可重复给的选项（action="append"）：配置文件里对应写成文本列表。"""
    return isinstance(action, argparse._AppendAction)


def configurable_keys(parser: argparse.ArgumentParser) -> dict[str, set[str]]:
    """从 argparse 推出 [common] / [cloud] 两节接受的键（选项长名去掉 `--`，ADR 0053 决策 3 的同词规则）：七个读配置命令的全部
    长选项，减去按次选择型与设备专用选项，再按是否只在云端生效分到两节。单一真源在 argparse：新增选项自动进入接受集，归类由
    三份名单决定。"""
    common: set[str] = set()
    cloud: set[str] = set()
    for name in CONFIG_COMMANDS:
        for action in option_actions(parser, name):
            dest = action.dest
            if dest in PER_CALL_OPTIONS or dest in DEVICE_OPTIONS:
                continue
            (cloud if dest in CLOUD_OPTIONS else common).add(dest.replace("_", "-"))
    return {"common": common, "cloud": cloud}


_BUILTIN_TYPE_REASONS = {int: "应为整数", float: "应为数字"}


def convert_config_value(action, raw, *, section: str, key: str, path):
    """配置值经与 argparse 同一套类型与取值范围校验（ADR 0053 决策 3）：非法值的报错形态与命令行上给错一致。
    按 TOML 的原生类型直接校验、不经字符串：整数选项只接受 TOML 整数（浮点不截断——命令行上给 4.7 同样被拒），浮点选项与自定义
    校验函数接受 TOML 整数或浮点（拿到数字本身），数字选项不接受文本（TOML 里 "4" 是文本、不是数字）；没有 type 的选项要求文本；
    布尔一律拒绝；可重复给的选项接受文本列表，其余只接受单个值。失败理由是产品语言（不把解释器的英文原文带给使用方），自定义校验
    函数自己写的消息原样保留；取值回显限长，别让一个超长的值撑爆一行提示。"""
    def fail(reason: str):
        shown = repr(raw) if len(repr(raw)) <= 80 else repr(raw)[:77] + "…"
        raise _config.ConfigError(f"配置文件 {path} 的 [{section}] {key} 取值 {shown} 无效：{reason}（要求与命令行选项 --{key} 相同）")

    repeat = _is_repeatable(action)
    if isinstance(raw, list) and not repeat:
        fail("这个选项只接受一个值，不接受列表")
    out = []
    for item in (raw if isinstance(raw, list) else [raw]):
        if isinstance(item, bool):
            fail("不接受布尔值")
        if callable(action.type):
            reason = _BUILTIN_TYPE_REASONS.get(action.type, "应为数字")
            if not isinstance(item, (int, float)) or (action.type is int and isinstance(item, float)):
                fail(reason)
            try:
                value = action.type(item)
            except argparse.ArgumentTypeError as e:  # 自定义校验函数自己的消息（已是产品语言）
                fail(str(e))
            except (ValueError, TypeError, OverflowError):  # 内建类型或自定义校验吞不下这个数（如超出浮点范围）
                fail(reason if action.type in _BUILTIN_TYPE_REASONS else "不是可接受的数字")
        else:
            if not isinstance(item, str):
                fail("应为文本")
            value = item
        if action.choices is not None and value not in action.choices:
            fail(f"只能是 {'、'.join(str(c) for c in action.choices)} 之一")
        out.append(value)
    return out if repeat else out[0]


def apply_project_config(args, parser: argparse.ArgumentParser) -> int | None:
    """parse_args 之后、分派之前：读项目配置文件并合成取值顺序（ADR 0053 决策 1、2、3）。返回 2（配置文件不可用）或 None。

    只对七个读配置的命令做；`_reconcile` / `_tunnel_watch`（宿主不读文件：值已在 definition 里，或由提交侧按解析后的值经
    argv 传入）、`deploy` / `destroy` / `skill` / `list-engines` 不读。
    三类选项三种去向：①没有环境变量层的 → 配置值填进仍为 None 的 args 字段（选项已给则不动），最后补内建默认；
    ②有环境变量层的（ENV_LAYER_OPTIONS）→ 只做类型校验、存进 `args.config_values`，由各解析链经 config_* 形参放在环境变量
    之后；③ [cloud] 整节只在 --backend cloud 下生效，backend 自身先按「选项 > [common] > 内建」定下来；只对本机后端起作用的
    [common] 键（LOCAL_ONLY_OPTIONS）在 --backend cloud 下跳过、不写进 args，run / submit 上各提示一句。
    [common] 里对当前命令不存在的键忽略（配置文件是项目级的，各命令只取自己有的那几项）。
    路径类值相对配置文件所在目录（决策 2）：steps-dir 恒绝对化；report-dir 只在本机后端下绝对化（云端是桶内键前缀、原样）。
    """
    if getattr(args, "command", None) not in CONFIG_COMMANDS:
        return None
    keys = configurable_keys(parser)
    try:
        path, origin = _config.locate_config(getattr(args, "config", None))
        cfg = _config.load_project_config(path, common_keys=keys["common"], cloud_keys=keys["cloud"])
    except _config.ConfigError as e:
        progress(str(e))
        return 2
    args.project_config = cfg
    args.config_origin = origin
    args.config_values = {}    # 有环境变量层的选项：dest → 已校验的配置值（解析链经 config_* 形参取用）
    args.config_filled = set()  # 由配置填进 args 的 dest（提示语按来源分流时用）
    actions = {a.dest: a for a in option_actions(parser, args.command)}
    try:
        if "backend" in actions and args.backend is None and "backend" in cfg.common:
            args.backend = convert_config_value(actions["backend"], cfg.common["backend"], section="common", key="backend", path=cfg.path)
            args.config_filled.add("backend")
        if "backend" in actions and args.backend is None:
            args.backend = BUILTIN_DEFAULTS["backend"]
        # doctor 只给 --prefix 也做云端检查（_cmd_doctor 的判据），[cloud] 节与「report-dir 是键前缀、不绝对化」同样按云端处理
        use_cloud = getattr(args, "backend", None) == "cloud" or (args.command == "doctor" and getattr(args, "prefix", None) is not None)
        for dest, action in actions.items():
            if dest == "backend" or dest in PER_CALL_OPTIONS or dest in DEVICE_OPTIONS:
                continue
            section = "cloud" if dest in CLOUD_OPTIONS else "common"
            if (section == "cloud" and not use_cloud) or (use_cloud and dest in LOCAL_ONLY_OPTIONS):
                continue
            key = dest.replace("_", "-")
            source = cfg.cloud if section == "cloud" else cfg.common
            if key not in source:
                continue
            value = convert_config_value(action, source[key], section=section, key=key, path=cfg.path)
            if dest in ENV_LAYER_OPTIONS:
                args.config_values[dest] = cfg.resolve_path(value) if dest == "steps_dir" else value
                continue
            if getattr(args, dest) is not None:
                continue
            if dest == "report_dir" and not use_cloud:
                value = cfg.resolve_path(value)
            setattr(args, dest, value)
            args.config_filled.add(dest)
        # 有环境变量层的资源名与身份（prefix / ddb-table / s3-bucket / region / profile）被解析链用到的命令，不一定都有对应选项
        # （explain 没有 --s3-bucket、doctor 连 --ddb-table 也没有，却照样读 AWS_S3_BUCKET / AWS_DDB_TABLE 并用到桶与表）：
        # 配置层对它们同样要生效，否则同一份文件让 submit 写进一个桶、explain 去另一个桶读。按节取值、经任一命令的同名选项转换。
        for dest in sorted(ENV_LAYER_OPTIONS):
            if dest in args.config_values or dest == "steps_dir":
                continue
            section = "cloud" if dest in CLOUD_OPTIONS else "common"
            if section == "cloud" and not use_cloud:
                continue
            key = dest.replace("_", "-")
            source = cfg.cloud if section == "cloud" else cfg.common
            if key not in source:
                continue
            action = find_option_action(parser, dest)
            if action is None:
                continue
            args.config_values[dest] = convert_config_value(action, source[key], section=section, key=key, path=cfg.path)
    except _config.ConfigError as e:
        progress(str(e))
        return 2
    # 提示按命令而不按选项面：submit 没有 --grace，云端提交照样要说清文件里那一项为什么没用上
    if use_cloud and args.command in LOCAL_ONLY_NOTICE_COMMANDS:
        for dest, reason in LOCAL_ONLY_OPTIONS.items():
            key = dest.replace("_", "-")
            if key in cfg.common:
                progress(f"注：配置文件 {cfg.path} 的 [common] {key} 本次未生效：{reason}")
    for dest, default in BUILTIN_DEFAULTS.items():
        if dest in actions and getattr(args, dest) is None:
            setattr(args, dest, default)
    return None


def find_option_action(parser: argparse.ArgumentParser, dest: str):
    """在七个读配置的命令里找某个 dest 的选项定义（任一命令的那份即可：同名选项各命令类型一致），供配置值转换。"""
    for name in CONFIG_COMMANDS:
        for action in option_actions(parser, name):
            if action.dest == dest:
                return action
    return None


def option_origin(args, dest: str) -> str:
    """一个选项值的来源说明（产品语言）：配置文件填的点名文件、节与键，否则是命令行选项本身。错误消息按它指路。"""
    if dest in getattr(args, "config_filled", set()):
        cfg = getattr(args, "project_config", _config.NO_CONFIG)
        section = "cloud" if dest in CLOUD_OPTIONS else "common"
        return f"配置文件 {cfg.path} 的 [{section}] {dest.replace('_', '-')}"
    return "--" + dest.replace("_", "-")


def identity_layers(args) -> dict:
    """`compose.resolve_aws_identity` 的配置文件层（region / profile 排在环境变量之后，ADR 0053 决策 2）。"""
    vals = getattr(args, "config_values", {})
    return {"config_region": vals.get("region"), "config_profile": vals.get("profile")}


def config_layers(args) -> dict:
    """`compose.resolve_cloud_target` 的配置文件层：身份两项加 prefix / ddb-table / s3-bucket（都有环境变量层，排在它之后）。
    events-table / cluster 没有环境变量层，配置值已由 `apply_project_config` 直接填进 args、按选项值传入。"""
    vals = getattr(args, "config_values", {})
    return {**identity_layers(args), "config_prefix": vals.get("prefix"),
            "config_runs_table": vals.get("ddb_table"), "config_bucket": vals.get("s3_bucket")}
