"""资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。

**零依赖**（不 import core/boto3）——`gherkai-deploy-aws`（`gherkai_deploy_aws.names`）直接 import 本模块拿命名，依赖面最小
（曾因「CDK 独立工程、不能 import 当时的 `cli` 包（今 `gherkai_cli`）」在 iac 侧复刻一份、靠对拍测试防漂移，抽入本模块后复刻消除、真同源）。
"""
from __future__ import annotations

import hashlib
import re

DEFAULT_PREFIX = "gherkai-"

# 各资源的「基名」（prefix 之后的固定部分）——CDK 与 cli 共享的约定（CDK 侧须用同名，否则 preflight 报 prefix 不一致）。
BASE_RUNS_TABLE = "runs"
BASE_EVENTS_TABLE = "events"
BASE_BUCKET = "artifacts"
BASE_CLUSTER = "cluster"
# 无状态批量运行 kicker（踢启器）Lambda 基名：CDK 建 `{prefix}kicker`（stack.py 用同名），cli status
# --wait 据 --prefix 推理出它、检测到推进停住时 invoke 它触发继续推进（Lambda 名单一真源、cli↔IaC 同源）。
BASE_KICKER_LAMBDA = "kicker"
BASE_RECONCILER_LAMBDA = "reconciler"
BASE_EXIT_OBSERVER_LAMBDA = "exit-observer"
# 一次性定时触发（ADR 0033 资源清单 15.）：IaC 建专用 schedule group `{prefix}schedules`，推进器运行期把两族一次性触发建在里面
# ——job 到点停止的一族与 run 级的一族（每个 run 在期限与期限加 300 秒各一次）。group 内的名字不带 prefix，由基名加摘要构成、
# 长度固定，见 job_timeout_schedule_name 与 run_timer_schedule_name。IaC 的 IAM 资源域按 group 授权（`schedule/<group 名>/*`），
# 与推进器建触发时给的 group 名同由 schedule_group_name 推出：任一侧单独改名，CreateSchedule 即被拒。
BASE_SCHEDULE_GROUP = "schedules"
BASE_JOB_TIMEOUT_SCHEDULE = "job-timeout"
BASE_RUN_TIMER_SCHEDULE = "run-timer"
# run 级一族的两种：期限那一次（deadline）与期限加 300 秒那一次（overdue），ADR 0054 决策九第 1 条。取值同时是名字里摘要的输入与
# 载荷 `{run_id, run_timer}` 里 run_timer 的值：推进器建触发与 kicker 认载荷引同一对常量。
RUN_TIMER_DEADLINE = "deadline"
RUN_TIMER_OVERDUE = "overdue"
RUN_TIMER_KINDS = (RUN_TIMER_DEADLINE, RUN_TIMER_OVERDUE)
# 两族名字里摘要的位数（sha1 的十六进制前缀，80 bit）：同一 group 内碰撞概率可忽略，名字长度因此固定、不随 prefix 变化。
SCHEDULE_NAME_DIGEST_LEN = 20
# 一次性触发的执行角色（EventBridge Scheduler 服务以它调用 kicker）：IaC 建 `{prefix}timeout-scheduler`，名字见
# timeout_scheduler_role_name。带 prefix 的资源名里它最长，IAM 角色名的上限因此决定 prefix 的长度上限（prefix_max_len）。
BASE_TIMEOUT_SCHEDULER_ROLE = "timeout-scheduler"
IAM_ROLE_NAME_MAX_LEN = 64  # AWS IAM 对角色名的长度上限
# task-def / container：按 job.engine 拼 `{prefix}{engine}-worker`（对称 EngineResolver 按 engine 选）。
ENGINES = ("novaact", "midscene")

# 后端 SSM 参数的相对键（全路径为 `ssm_path(prefix, 键)`；参数全集与各自的写者见 ADR 0038「SSM 参数与命名真源」）。
# 调用点一律引常量、不写裸字面量——推送方/解析方/IaC/Lambda 拼的必须是同一个键。
BACKEND_VERSION_KEY = "version"        # 后端版本戳（stack 资源随部署事务写；提交侧 skew 比对读）
DEVICE_FARM_PROJECT_KEY = "device-farm-project"  # 云端 Device Farm 项目 ARN（deploy 找回或建立后写，ADR 0051 决策 10；提交侧填设备请求时读）
VPC_KEY = "vpc"                      # 生效的 VPC 取值（部署方三态比对读，ADR 0037 决策 6）
WORKER_IMAGE_ROOT_KEY = "worker-image"  # `worker-image/<engine>/<tag>` 映射族的根（按路径列举时用；单条键走 worker_image_key）

# 产物桶里专放云端提交记录 jobs 对象的定义前缀（ADR 0030 决定六「云端提交记录」条、ADR 0033「资源清单」3.）：在桶根下、不随报告
# 前缀变化，不设过期规则。键为 `<本前缀><run_id>/<随机段>.json`，由组合根注入 core 的 jobs 对象存取（core 不 import 本模块）。
# 用到这个前缀名的地方都引这个常量，不写裸字面量。
DEFINITIONS_PREFIX = "definitions/"

# 安装包在产物桶里的布局与保留承诺（ADR 0051 决策 9）：键前缀、对象标签（部署侧按它配生命周期规则）、过期天数 E 与「已提交 run 引用的对象
# 至少保留」天数 R；上传侧的复用窗口是 E 减 R。IaC 与上传侧共用这一处定义，改一处两侧同变。
APP_OBJECT_PREFIX = "apps/"
APP_OBJECT_TAG = "gherkai=app"       # S3 Tagging 的查询串写法（k=v）
APP_OBJECT_EXPIRE_DAYS = 14
APP_OBJECT_RETAIN_DAYS = 7

# 云端 Device Farm 项目（ADR 0051 决策 10、ADR 0033 资源清单第 11 条）：deploy 按项目名找回或建立，stack 校验 context 里的 ARN 并
# 按它给 Midscene task role 授权，提交侧与 doctor 读 DEVICE_FARM_PROJECT_KEY。几处都引这里的常量与函数，调用点不写裸字面量。
BASE_DEVICE_FARM_PROJECT = "devices"   # 项目名 default_name(prefix, 本基名)，即 `{prefix}devices`
# Device Farm 只在这一个区域提供：Python 侧的 Device Farm 客户端与 task role 里全部 devicefarm ARN 的区域段都用它、不跟后端区域走
# （ADR 0033「region 全可配」的唯一例外）。
DEVICE_FARM_REGION = "us-west-2"
# 「待建立」占位值：命令手里没有可用的项目 ARN 时经 context 传它（哪些情形用占位见 ADR 0051 决策 10），stack 对它与缺省同样处理：
# 不写 SSM 参数、不授 Device Farm 权限，也不报错（ADR 0037 决策 6）。值必须过不了 validate_device_farm_project_arn。
DEVICE_FARM_PROJECT_PENDING = "pending"
# 项目 ARN 的完整形态：分区 aws、区域 DEVICE_FARM_REGION、12 位账户、资源类型 project。项目 id 只含字母、数字与连字符：含 `/` `:`
# 会让会话前缀错位，含 `*` `?` 会让授权扩到别的项目。只有部署侧这样严格校验；提交侧对使用方给的 ARN 只核服务与资源类型段
# （ADR 0053 决策 4）。
_DEVICE_FARM_PROJECT_ARN_RE = re.compile(
    rf"arn:aws:devicefarm:{re.escape(DEVICE_FARM_REGION)}:(?P<account>[0-9]{{12}}):project:"
    r"(?P<project_id>[A-Za-z0-9-]+)")

# 引擎原生产物在 run 树下的子目录名（ADR 0029「S3 key 镜像本地 run 树」的前提）：同步 run / local per-run / cloud 容器内
# 三宿主拼的必须是同一个名字，故单点；键为引擎名（ENGINES）。改名即改 S3 key 布局，须同时考虑已落产物的可读性。
ARTIFACT_SUBDIR = {"novaact": "nova-trajectories", "midscene": "midscene-run"}


def default_name(prefix: str, base: str) -> str:
    """prefix + 基名（原样拼，prefix 含分隔符由部署方负责）。CDK 与 cli 共用此推导 → 单一事实源。"""
    return f"{prefix}{base}"


def task_def_name(prefix: str, engine: str) -> str:
    """引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称 EngineResolver）。"""
    return f"{prefix}{engine}-worker"


def container_name(engine: str) -> str:
    """task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带 prefix——container 是
    task-def 内部名、随 task-def 走（task-def 已带 prefix），再叠 prefix 冗余。固定 `{engine}-worker`。"""
    return f"{engine}-worker"


def schedule_group_name(prefix: str) -> str:
    """专用 schedule group 的名字 `{prefix}schedules`（ADR 0033 资源清单 15.）。IaC 用它建 group、拼 IAM 资源域
    `schedule/<本名>/*`，推进器建一次性触发时用它作 GroupName，三处同源。"""
    return default_name(prefix, BASE_SCHEDULE_GROUP)


def _schedule_name(base: str, digest_input: str) -> str:
    """group 内一次性触发的名字：基名、连字符与 `digest_input` 的 sha1 十六进制前 SCHEDULE_NAME_DIGEST_LEN 位。

    取摘要而不直接拼：job 到点停止要区分 scope，而 scope_id 是用户文本，字符集与长度都可能超出 schedule 名所允许的；两族同取
    摘要，名字形态一致、长度固定。名字由输入确定，重复建得到 ConflictException，调用方视为已建。"""
    digest = hashlib.sha1(digest_input.encode("utf-8")).hexdigest()[:SCHEDULE_NAME_DIGEST_LEN]
    return f"{base}-{digest}"


def job_timeout_schedule_name(run_id: str, scope_id: str) -> str:
    """job 到点停止的触发名 `job-timeout-<sha1(run_id#scope_id) 前 20 位>`，不带 prefix（所在 group 已带），长度恒为 32。"""
    return _schedule_name(BASE_JOB_TIMEOUT_SCHEDULE, f"{run_id}#{scope_id}")


def run_timer_schedule_name(run_id: str, kind: str) -> str:
    """run 级定时触发的名字 `run-timer-<sha1(run_id#kind) 前 20 位>`，不带 prefix，长度恒为 30；`kind` 须是 RUN_TIMER_KINDS
    之一，否则抛 `ValueError`。基名与 job 到点停止的不同，摘要的输入互不相撞：scope_id 是用户文本，不与种类共用名字空间。"""
    if kind not in RUN_TIMER_KINDS:
        raise ValueError(f"run 级定时触发的种类须是 {RUN_TIMER_KINDS} 之一，现在是 {kind!r}")
    return _schedule_name(BASE_RUN_TIMER_SCHEDULE, f"{run_id}#{kind}")


def timeout_scheduler_role_name(prefix: str) -> str:
    """一次性触发的执行角色名 `{prefix}timeout-scheduler`：IaC 建角色时用它；已建的触发按角色 ARN 投递，改名会让在途的触发
    失去执行角色。"""
    return default_name(prefix, BASE_TIMEOUT_SCHEDULER_ROLE)


def prefix_max_len() -> int:
    """prefix 的长度上限：带 prefix 的资源名里最紧的一条推出，即执行角色 `{prefix}timeout-scheduler` 不超过 IAM 角色名的上限。

    其余带 prefix 的名字都更宽，上限较紧的几个：Lambda `{prefix}exit-observer` 容 51、EventBridge 规则 `{prefix}ecs-stopped`
    容 53、桶 `{prefix}artifacts` 容 54、schedule group `{prefix}schedules` 按 64 个字符计容 55（ADR 0033「命名」节护栏）；部署
    模板里全部带 prefix 的名字与各自的上限由部署包的合成测试逐个核对。一次性触发的名字不带 prefix、长度固定，不参与这条上限。
    上限由公式推出、不写死，基名改动时随之变化；stack 在合成期据此校验 prefix，部署命令的 `--prefix` 帮助文字也引用它。
    """
    return IAM_ROLE_NAME_MAX_LEN - len(BASE_TIMEOUT_SCHEDULER_ROLE)


def ssm_path(prefix: str, key: str) -> str:
    """`/{prefix}backend/<key>`：本部署**全部** SSM 参数的路径构造单点（version/vpc、device-farm-project、
    worker-template/worker-image/worker-default 皆经此；IAM 资源域按同一形态拼 `*`；参数全集见 ADR 0038「SSM 参数与命名真源」）。
    cli 已知 prefix 直接拼路径读、无循环依赖（ADR 0033）。"""
    return f"/{prefix}backend/{key}"


def validate_device_farm_project_arn(arn: str) -> str:
    """项目 ARN 形态校验：须是 `arn:aws:devicefarm:us-west-2:<12 位账户>:project:<项目 id>`，合格原样返回，否则抛 `ValueError`。

    stack 在合成期用它拦经 context 传入的值（ADR 0037 决策 6）：形态不对的 ARN 拼出的会话前缀只会在运行期表现为 AccessDenied。
    消息给使用方看（cdk 合成失败时打到终端），只说收到了什么、应是什么形态。
    """
    _match_device_farm_project_arn(arn)
    return arn


def _match_device_farm_project_arn(arn: str) -> re.Match[str]:
    m = _DEVICE_FARM_PROJECT_ARN_RE.fullmatch(arn)   # fullmatch：`$` 会放过末尾换行
    if m is None:
        raise ValueError(
            f"Device Farm 项目 ARN 形态不对：须形如 arn:aws:devicefarm:{DEVICE_FARM_REGION}:<12 位账号>:project:<项目 id>，"
            f"现在是 {arn!r}"
        )
    return m


def device_farm_session_arn_prefix(project_arn: str) -> str:
    """本项目全部远程访问会话的 ARN 通配：`arn:aws:devicefarm:us-west-2:<账户>:session:<项目 id>/*`。形态不对抛 `ValueError`。

    会话 ARN 形如 `…:session:<项目 id>/<会话 id>/<序号>`，账户段与项目 id 段都取自项目 ARN 本身，区域段恒为 DEVICE_FARM_REGION。
    task role 的会话查询与停止要把它与项目 ARN 列在同一条 statement 里，只授其一即被真实角色拒绝（ADR 0033 task role 权限表）。
    """
    m = _match_device_farm_project_arn(project_arn)
    return f"arn:aws:devicefarm:{DEVICE_FARM_REGION}:{m.group('account')}:session:{m.group('project_id')}/*"


def device_farm_interactive_endpoint_resource(project_arn: str) -> str:
    """Device Farm 交互端点（远程访问会话的 Appium 入口）做授权检查时用的资源 ARN：`arn:aws:devicefarm:us-west-2:<账户>:project:session`。

    这是服务端固定的字面量，不是哪个项目或会话的 ARN，所以收窄不到项目：真实 task role 经该端点建 Appium 会话时被拒，拒绝消息点名
    `devicefarm:GetRemoteAccessSession on resource: …:project:session`（2026-11-01 部署后实测）；策略模拟器对这个字面量判 implicitDeny、
    对真实会话 ARN 判允许，与实测一致。控制面的 Get / Stop 仍按会话前缀与项目 ARN 授权，这一条只给 Get（ADR 0033 task role 权限表）。
    账户段取自项目 ARN，形态不对抛 `ValueError`。
    """
    m = _match_device_farm_project_arn(project_arn)
    return f"arn:aws:devicefarm:{DEVICE_FARM_REGION}:{m.group('account')}:project:session"


def ecr_repo_name(prefix: str, engine: str) -> str:
    """引擎 worker 镜像的 ECR 仓库名 —— **恒等于 `task_def_name(prefix, engine)`**（ADR 0038「tag 命名」节）。

    「ECR repo 名复用 task-def family 名」是一条约定（同 prefix 心智、一个引擎一套资源同名），曾以注释 +
    内联副本散在 IaC 侧与推送脚本里；收在此处后**改名只改一处**，两侧不会漂。
    单独立函数而非让调用方直接用 `task_def_name`：调用点意图是「取 ECR 仓库」，语义名让「将来若要拆开」有落点。
    """
    return task_def_name(prefix, engine)


# worker 镜像 tag / SSM 键（ADR 0038）。
# ---- tag 字符集（docker/OCI 与 ECR 共同约束）：首字符 `[A-Za-z0-9_]`，其后 `[A-Za-z0-9_.-]`，总长 ≤128 ----
_TAG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")
# variant 名（tag 的后半段）：同字符集但不设长度上限（总长由 _TAG_RE 兜）。单独校验是为了把
# 「variant 名本身不合法」与「拼出来的 tag 超长/首字符非法」两类错误分开报。
_VARIANT_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")

# 默认 variant 指针（部署级一个；deploy 初始化为 `base`，`push-worker --set-default` 改写）。
WORKER_DEFAULT_KEY = "worker-default"

# task-def revision 上记血缘与退休时刻的 tag 键（ADR 0038：退休时刻与血缘**不进 SSM**、随 revision 同生死）。
TAG_VARIANT = "gherkai:variant"
TAG_VERSION = "gherkai:version"
TAG_DIGEST = "gherkai:digest"
TAG_TEMPLATE = "gherkai:template"
TAG_RETIRED_AT = "gherkai:retired-at"

# runs 表 STATE item 的顶层属性名：本 run 用到的 worker task-def revision ARN 列表（清理 pass 的运行中 run
# 引用检查按它判定，沿用 ADR 0034 `detached` 顶层标记先例）。
STATE_WORKER_TASK_DEF_ARNS_ATTR = "worker_task_def_arns"
# runs 表 STATE item 的顶层属性名：由 run 级 `status` 派生的状态分组（非终态取 STATUS_GROUP_LIVE，终态取该终态的状态值；
# 写端与派生函数在 `gherkai_core.adapters.run_store.ddb.status_group`，ADR 0030 决定六）。
STATE_STATUS_GROUP_ATTR = "status_group"
STATUS_GROUP_LIVE = "live"
# runs 表的排序键属性名与运行态条目的取值（一个 run 落提交记录的头 META 与运行态 STATE 两个条目，ADR 0030 决定六）：kicker 的流过滤
# 按 STATE 条目匹配、kicker 按流记录的新映像分辨记录种类（ADR 0033 资源清单 13.），两者与状态分组同属跨版本不变的约定（ADR 0037
# 决策 7）。写端在 `gherkai_core.adapters.run_store.ddb`，字面量两处各有，理由与漂移护栏同上两条。
RUNS_ITEM_TYPE_ATTR = "item_type"
RUNS_STATE_ITEM = "STATE"
# runs 表按状态分组分区、`run_id` 排序的稀疏 GSI 名（只有 STATE item 带分组属性，投影 INCLUDE `worker_task_def_arns`）：
# worker revision 清理的引用检查读 live 分组，`list-runs` 读 live 分组与各终态分组，两者共用（ADR 0030 决定六、
# ADR 0038「不变量」清理 pass 条、ADR 0041 决策七）。
RUNS_STATUS_GROUP_GSI = "status_group-run_id-index"


def image_tag(version: str, variant: str) -> str:
    """worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。

    PEP 440 的 `+`（本地段）与 `!`（epoch）不在 docker/ECR 的 tag 字符集内（`1.4.0.post3.dev0+28c1684` 直接
    `docker tag` 即 `invalid reference format`，实测），故两者归一化为 `.`；返回前按字符集正则校验，不匹配即
    `ValueError`——推送方与解析方（提交侧 preflight）拼的是同一个函数，键不会两边算法不同而对不上。
    """
    if not _VARIANT_RE.match(variant):
        raise ValueError(
            f"variant 名不合法：{variant!r}——须匹配 {_VARIANT_RE.pattern}"
            "（字母数字下划线开头，其后可含 `.` `-`）"
        )
    tag = f"{version.replace('+', '.').replace('!', '.')}-{variant}"
    if not _TAG_RE.match(tag):
        raise ValueError(
            f"镜像 tag 不合法：{tag!r}（由版本 {version!r} + variant {variant!r} 拼出）"
            f"——须匹配 {_TAG_RE.pattern}"
        )
    return tag


def worker_template_key(engine: str) -> str:
    """模板 revision ARN 的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。写者是 stack 资源。"""
    return f"worker-template/{engine}"


def short_digest(digest: str | None, keep: int = 12) -> str:
    """镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight 打印都用它，
    同一个 digest 在两处长相一致，人对照「是不是刚推上去那个」不用换算。机器要全串看 definition / SSM。"""
    if not digest:
        return "-"
    algo, _, hexpart = digest.partition(":")
    return f"{algo}:{hexpart[:keep]}" if hexpart else digest[:keep]


def worker_image_key(engine: str, tag: str) -> str:
    """（引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。

    值是 JSON：`template_arn` / `revision_arn` / `digest` / `pushed_at`（ISO 8601 UTC）。键含版本，因此 variant
    **按版本隔离**：旧版本的 variant 留作历史、不参与当前版本解析。
    """
    return f"{WORKER_IMAGE_ROOT_KEY}/{engine}/{tag}"
