"""提交准备与 definition 填完（ADR 0048 决策 3、ADR 0053 决策 3、4、ADR 0051 决策 9、10）：run / submit 共享前置的产物与两个后端各自把
definition 填完整的次序，收在这一个模块里。

**次序是契约**（不是约定）：`Prepared` 是共享前置的产物——零 AWS、零副作用的解析结果；`complete_local_definition` 与
`complete_cloud_definition` 是本机 / 云端各自把 definition 填完的唯一入口，各自的次序排定：本机「账号比对（STS）→ 设备请求 → 安装包上传
→ 写前结构校验」，云端「读 SSM 取项目并填设备请求 → 安装包进产物桶 → 写前结构校验」；调用方只在正确的位置各调一次——本机在自己的选项校验之后、起隧道之前，云端在版本 skew 闸与资源 preflight 之后、落库之前。
此前这些步骤散在共享前置与两个云端分支里靠调用顺序维持，「先上传再被拒」的缺陷正出自那种形态。
纯解析（目标拒绝、设备选择、安装包定位）也住这里，plan 复用它们做标注与存在性核对。进度与诊断经 `console.progress` 打到 stderr。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

from gherkai_core.errors import DefinitionContractError
from gherkai_core.target import validate_job_definition
from gherkai_runtime import compose
from gherkai_runtime import names as _names

from gherkai_cli import config as _config
from gherkai_cli import device_selection as _devsel
from gherkai_cli import render
from gherkai_cli.console import progress
from gherkai_cli.settings import identity_layers


@dataclass
class Prepared:
    """run / submit 共享前置的产物：全部已解析、零 AWS 的输入。下游按字段取，不往 argparse 的 Namespace 上挂状态。"""

    jobs: list
    steps_dir: str | None
    device_selections: dict = field(default_factory=dict)        # 平台 → 设备选择（有设备 scope 的平台都有值，未指定在前置即拒）
    app_entries: dict = field(default_factory=dict)              # (别名, 平台) → 安装包路径（已核存在）
    local_project_arn: str | None = None                          # 本机后端：Device Farm 项目 ARN（已核形态）；云端 None（读 SSM）
    local_project_source: str | None = None                       # 它的来源说明（账号比对的警告点名用）
    local_app_bucket: str | None = None                           # 本机后端：放安装包的桶；云端 None（产物桶）


def target_rejections(jobs, caps: dict) -> list[str]:
    """按引擎能力自述核对各 job 的测试目标（ADR 0048 决策 4；0049 决策 4）：目标不在该引擎 worker 声明的 targets 里、或 job 墙钟预算超过
    该目标的会话上限，各给一条产品语言消息并指出改法。core 不内置引擎名到目标的对照，只看自述。"""
    supported = compose.worker_targets(caps)
    out: list[str] = []
    for j in jobs:
        t = j.target
        label = render.spaced(render.target_label(t.device, t.ui_kind))
        if not compose.target_supported(supported, t.device, t.ui_kind):
            first = j.scenarios[0].id if j.scenarios else j.scope_id
            out.append(
                f"场景 {first} 所在的 scope 要求在{label}上执行，但它使用的引擎 {j.engine} 不支持这个目标"
                f"（它支持：{render.targets_label(supported, with_requires=False)}）。请在这个 scope 的任一场景上加 @engine:<支持该目标的引擎>，"
                f"或用 --default-engine 更改默认引擎；各引擎支持的目标见 gherkai doctor。"
            )
            continue
        limit = compose.target_session_limit(supported, t.device)
        if limit is not None and j.timeout_s is not None and j.timeout_s > limit:
            out.append(
                f"scope {j.scope_id!r} 的 job 墙钟预算 {j.timeout_s:g} 秒超过了引擎 {j.engine} 在{label}上的会话上限 {limit:g} 秒："
                f"请调低这个 scope 的 @timeout 或 --default-job-timeout。"
            )
    return out


def validate_definition(jobs) -> int | None:
    """写 definition 之前的结构校验（ADR 0048 决策 3 的第一处；第二处在推进器读 definition 时）。返回 2 或 None。

    设备请求与应用条目的位置都已由前面的解析与上传填入，走到这里的 DefinitionContractError 只会由 plan 产出的畸形 job 或组合根漏填触发
    （内部错误、不因使用方输入发生），按契约型异常原样转述（ADR 0039 例外条）。
    """
    for j in jobs:
        try:
            validate_job_definition(j)
        except DefinitionContractError as e:
            progress(f"scope {j.scope_id!r} 的运行定义不符合要求，拒绝写入：{e}")
            return 2
    return None


def device_selections(args, jobs) -> "dict | int":
    """按 jobs 里出现的平台解析设备选择（选项 > 环境变量 > 配置文件，ADR 0053 决策 4）。ARN 形态不对以退出码 2 结束；
    未指定的平台值为 None，由调用方按命令处置（run / submit 拒绝、plan 标注并警告）。纯本地、零 AWS。"""
    cfg = getattr(args, "project_config", _config.NO_CONFIG)
    out: dict = {}
    for platform in sorted({j.target.device for j in jobs if not j.target.is_desktop}):
        try:
            out[platform] = _devsel.resolve_device_selection(
                platform, flag_arn=getattr(args, f"{platform}_device_arn", None), env=os.environ, config=cfg)
        except _devsel.DeviceSelectionError as e:
            progress(str(e))
            return 2
    return out


def require_device_selections(selections: dict) -> int | None:
    """run / submit：有设备 scope 的平台没有任何来源指定设备，在提交前以退出码 2 结束（ADR 0053 决策 4「不自动挑设备」）。"""
    missing = [p for p, sel in selections.items() if sel is None]
    for platform in missing:
        progress(_devsel.unspecified_message(platform))
    return 2 if missing else None


def local_project_arn_value(args, selections: dict) -> "tuple[str, str] | int | None":
    """本机后端的 Device Farm 项目 ARN 取值（ADR 0053 决策 3）：没有设备 scope 返回 None；有则按选项 > 环境变量 > 配置文件取，缺失或形态
    不对以退出码 2 结束。零 AWS；返回 (ARN, 来源说明)，来源供账号比对的警告点名。"""
    if not selections:
        return None
    cfg = getattr(args, "project_config", _config.NO_CONFIG)
    try:
        return _devsel.resolve_local_project_arn(flag_arn=getattr(args, "device_farm_project_arn", None), env=os.environ, config=cfg)
    except _devsel.DeviceSelectionError as e:
        progress(str(e))
        return 2


def warn_project_account(args, project_arn: str, source: str) -> None:
    """项目所属账号与当前凭证所属账号不一致只警告、不拦（两者都点名，ADR 0053 决策 3）；核对本身失败也只提示一句、继续。STS 一次。"""
    region, profile = compose.resolve_aws_identity(args.region, args.profile, **identity_layers(args))
    try:
        ident = compose.probe_aws_identity(region=region, profile=profile)
    except Exception as e:
        if not (isinstance(e, ImportError) or compose.is_botocore_error(e)):
            raise  # 别的异常是程序错误，不吞
        # 凭证不可用 / 未装 aws 依赖 / 网络：核对是辅助提示，不因它拦运行
        progress(f"未能核对 Device Farm 项目所属的账号（{e}），继续执行")
        return
    mine = ident.get("account")
    if mine and mine != _devsel.account_of(project_arn):
        progress(f"注意：Device Farm 项目 {project_arn}（来自 {source}）属于账号 {_devsel.account_of(project_arn)}，当前凭证属于账号 {mine}，"
                  "两者不一致——请确认用的是对的项目或凭证；继续执行")


def fill_device_requests(args, jobs, selections: dict, project_arn: str) -> list:
    """把设备选择、项目 ARN、计费方式与获取预算合成每个设备 job 的具名设备请求（ADR 0048 决策 3）；桌面 job 原样。"""
    cfg = getattr(args, "project_config", _config.NO_CONFIG)
    acquire_s = _devsel.acquire_timeout_for(cfg)
    out = []
    for j in jobs:
        if j.target.is_desktop:
            out.append(j)
            continue
        request = _devsel.build_device_request(selections[j.target.device], project_arn=project_arn,
                                               billing_method=_devsel.billing_method_for(j.target.device, cfg),
                                               acquire_timeout_s=acquire_s)
        out.append(replace(j, device_request=request))
    return out


def app_entries(args, jobs) -> "dict | int":
    """每个应用 job 的安装包（ADR 0053 决策 3 [apps]）：配置文件 [apps.<别名>.<平台>] 的 file（已按配置文件目录绝对化），不存在以退出码 2
    结束。plan 也调它、只核对存在（零 AWS）；上传在 run / submit。返回 {(别名, 平台): 路径}。"""
    cfg = getattr(args, "project_config", _config.NO_CONFIG)
    out: dict = {}
    for j in jobs:
        app = j.target.app
        if app is None:
            continue
        entry = cfg.apps.get(app.alias, {}).get(j.target.device)
        if entry is None:  # plan 层已按 FeatureContractError 拒绝，保险分支
            progress(f"scope {j.scope_id!r} 的 @app:{app.alias} 在配置文件里没有 {j.target.device} 平台的条目")
            return 2
        if not entry.file.is_file():
            progress(f"安装包不存在：{entry.file}（配置文件 [apps.{app.alias}.{j.target.device}] 的 file）")
            return 2
        out[(app.alias, j.target.device)] = entry.file
    return out


def local_app_bucket(args, entries: dict) -> "str | int | None":
    """本机后端放安装包的 S3 桶（ADR 0053 决策 3）：选项 > 环境变量 > 配置文件 [devices] app-bucket；没有应用 job 返回 None；有而缺失以退出码 2 结束。"""
    if not entries:
        return None
    cfg = getattr(args, "project_config", _config.NO_CONFIG)
    bucket = (getattr(args, "app_bucket", None) or os.environ.get(_devsel.APP_BUCKET_ENV)
              or (cfg.devices.app_bucket if cfg.devices is not None else None))
    if not bucket:
        progress("本机运行应用 scope 需要一个放安装包的 S3 桶，但没有指定：请在 gherkai.toml 的 [devices] 里给出 app-bucket，"
                  f"或用 {_devsel.APP_BUCKET_FLAG} / 环境变量 {_devsel.APP_BUCKET_ENV} 指定。")
        return 2
    return bucket


def fill_app_locations(args, jobs, entries: dict, *, bucket: str, managed: bool, region, profile) -> "list | int":
    """把每个应用 job 的安装包放进桶（按内容哈希，同一文件在一个 run 内只算一次哈希、只传一次）并把 bucket / key / sha256 填进应用条目
    （ADR 0051 决策 9、0048 决策 3）。失败以退出码 2 结束、不落下半成品 run。"""
    if not entries:
        return list(jobs)
    from datetime import datetime, timezone

    from gherkai_runtime import app_upload

    try:
        s3 = compose._make_s3_client(region=region, profile=profile)
    except ImportError as e:
        progress(f"上传安装包需要 boto3：{e}")
        return 2
    now = datetime.now(timezone.utc)
    done: dict = {}
    out = []
    for j in jobs:
        app = j.target.app
        if app is None:
            out.append(j)
            continue
        file = entries[(app.alias, j.target.device)]
        if (str(file), bucket) not in done:
            try:
                loc = app_upload.ensure_app_object(bucket, file, managed=managed, s3=s3, now=now, on_warn=progress)
            except app_upload.AppUploadError as e:
                progress(str(e))
                return 2
            except Exception as e:
                if compose.is_botocore_error(e):
                    progress(f"上传安装包 {file} 到 S3 桶 {bucket} 失败（凭证 / 权限 / 网络）：{e}")
                    return 2
                raise
            done[(str(file), bucket)] = loc
            progress(f"安装包 {file.name}：{'已上传到' if loc.uploaded else '复用'} s3://{bucket}/{loc.key}" + ("（已刷新保留期）" if loc.refreshed else ""))
            # 桶不在当前区域配置所指的区域：worker 按桶所在区域签发安装包地址，这里只提示（ADR 0051 决策 9；同一个桶只提示一次）
            if loc.bucket_region and region and loc.bucket_region != region and not any(k[1] == bucket for k in done if k != (str(file), bucket)):
                progress(f"注意：应用桶 {bucket} 在 {loc.bucket_region}，当前区域配置为 {region}；安装包按桶所在区域处理，不需要改配置")
        loc = done[(str(file), bucket)]
        out.append(replace(j, target=replace(j.target, app=replace(app, bucket=loc.bucket, key=loc.key, sha256=loc.sha256))))
    return out


def cloud_app_locations(args, target, prepared: "Prepared", jobs) -> "list | int":
    """云端后端：安装包进部署的产物桶、由本工具管理（打标签、按保留承诺刷新）；选项 / 环境变量 / 配置文件给的应用桶不生效、只提示（ADR 0053 决策 3）。"""
    entries = prepared.app_entries
    if not entries:
        return list(jobs)
    cfg = getattr(args, "project_config", _config.NO_CONFIG)
    if getattr(args, "app_bucket", None) or os.environ.get(_devsel.APP_BUCKET_ENV) or (cfg.devices is not None and cfg.devices.app_bucket):
        progress(f"注：云端后端把安装包放进部署的产物桶，{_devsel.APP_BUCKET_FLAG}、环境变量 {_devsel.APP_BUCKET_ENV} 与配置文件里的 app-bucket 不生效")
    return fill_app_locations(args, jobs, entries, bucket=target.bucket, managed=True, region=target.region, profile=target.profile)


def cloud_device_requests(args, target, prepared: "Prepared", jobs) -> "list | int":
    """云端后端的设备请求：项目 ARN 读部署写下的 SSM 参数（ADR 0051 决策 10、0048 决策 3），参数不在即「部署未启用设备支持」以退出码 2
    结束；选项、环境变量与配置文件给的项目 ARN 在云端不生效、只提示一句（ADR 0053 决策 3）。**调用位置在版本 skew 闸与资源 preflight
    之后**（读 SSM 是云端读，skew 先行；参数落在已授的 /{prefix}backend/* 内），之后由调用方做写前校验。没有设备 scope 时原样返回。"""
    selections = prepared.device_selections
    if not selections:
        return list(jobs)
    cfg = getattr(args, "project_config", _config.NO_CONFIG)
    if getattr(args, "device_farm_project_arn", None) or os.environ.get(_devsel.PROJECT_ARN_ENV) \
            or (cfg.devices is not None and cfg.devices.project_arn):
        progress(f"注：云端后端使用部署时建立的 Device Farm 项目，{_devsel.PROJECT_ARN_FLAG}、环境变量 {_devsel.PROJECT_ARN_ENV} 与"
                  "配置文件里的 project-arn 不生效")
    path = _names.ssm_path(target.prefix, _names.DEVICE_FARM_PROJECT_KEY)
    try:
        arn = compose.read_device_farm_project(prefix=target.prefix, region=target.region, profile=target.profile)
    except ImportError as e:
        progress(f"--backend cloud 需要 boto3：{e}")
        return 2
    except Exception as e:
        if compose.is_botocore_error(e):
            progress(f"--backend cloud 读取 Device Farm 项目参数失败（SSM 参数 {path}），请检查凭证、region 与权限：{e}")
            return 2
        raise
    if arn is None:
        progress("部署未启用设备支持：这个后端部署时没有建立 Device Farm 项目（部署版本早于本功能，或部署方没有 Device Farm 权限）。"
                  "请部署方用有 Device Farm 权限的凭证重新执行 gherkai deploy，再提交设备 scope。")
        return 2
    return fill_device_requests(args, jobs, selections, arn)

def complete_local_definition(args, prepared: "Prepared") -> "list | int":
    """本机后端填完 definition（ADR 0048 决策 3）：项目 ARN 所属账号的比对（STS，只警告）、设备请求填入、安装包上传（S3）并补齐位置，
    最后做写 definition 之前的结构校验。这是本机路径上**仅有的两步 AWS 操作**（账号比对与安装包上传），调用方把它排在全部零副作用校验（含 `run` 的
    `--grace`、`submit` 的 `--tunnel-ttl`）之后、起隧道与落库之前——配置错的 run 不该先上传几百 MB 再被拒。返回填完的 jobs 或退出码 2。"""
    jobs = list(prepared.jobs)
    if prepared.local_project_arn is not None:
        warn_project_account(args, prepared.local_project_arn, prepared.local_project_source or "配置")
        jobs = fill_device_requests(args, jobs, prepared.device_selections, prepared.local_project_arn)
    if prepared.local_app_bucket is not None:
        region, profile = compose.resolve_aws_identity(args.region, args.profile, **identity_layers(args))
        jobs = fill_app_locations(args, jobs, prepared.app_entries, bucket=prepared.local_app_bucket, managed=False, region=region, profile=profile)
        if isinstance(jobs, int):
            return jobs
    bad = validate_definition(jobs)
    if bad is not None:
        return bad
    return jobs


def complete_cloud_definition(args, target, prepared: Prepared, jobs) -> "list | int":
    """云端后端填完 definition：项目 ARN 读 SSM 填设备请求 → 安装包进产物桶并补齐位置 → 写 definition 之前的结构校验。
    调用方放在版本 skew 闸与资源 preflight 之后、落库之前（读 SSM 与写桶都是云端调用，skew 先行）。返回填完的 jobs 或退出码 2。"""
    filled = cloud_device_requests(args, target, prepared, jobs)
    if isinstance(filled, int):
        return filled
    filled = cloud_app_locations(args, target, prepared, filled)
    if isinstance(filled, int):
        return filled
    bad = validate_definition(filled)
    if bad is not None:
        return bad
    return filled
