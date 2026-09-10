"""Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024 协议的 worker。

对称 `subprocess_engine.py`（同一 `Engine` port、同一 `(WorkerHandle, Iterator[Event])` 形状），只把「进程世界」换成
「ECS/DDB 世界」——四条 I/O 边缘各自换传输（ADR 0024 远程传输演进表）：

| 边缘 | subprocess | Fargate（本 adapter） |
|---|---|---|
| job-in | 写 worker stdin | `PutObject` 整 job 到 S3、RunTask overrides 经 env 传 `JOB_S3_URI` 小指针（RunTask overrides 8192 上限塞不下含 feature 的 job） |
| events-out | 读 `EVENTS_FD` fd 逐行 | worker `PutItem` 到 DDB events 表；本 adapter `Query PK=run_id#scope_id AND last_seq<SK<EXIT_SK`（只读 worker seq 段，退出观察者的 `task_exited` 旁挂保留高位 SK、不入流）轮询增量拉 → `event_from_line` → yield（events-out=DDB，非 SQS/MSK，见 ADR 0024「DynamoDB 作 events-out」+ 三方案被拒护栏） |
| stop | SIGTERM→grace→SIGKILL | `StopTask`（grace 由 task-def 期 `stopTimeout` 决定、≤120s、不逐次传——Nova 下限 150s>120s，真容器标定后 Fargate 侧对最坏长 act 接受 SIGKILL，ADR 0032 结论 4） |
| 退出码 | `proc.wait()` returncode | `DescribeTasks` 轮询到 `lastStatus==STOPPED` → `containers[0].exitCode`（STOPPED 前常 null）→ 交 `wire.raise_for_worker_exit`（与 subprocess 共用同一份码→异常翻译） |

**红线（ADR 0016/0024/0026）**：boto3 client 由组合根注入、adapter 不自建（`require_boto3` 首行守卫）；schedule 仍纯归约、
对 ECS/DDB 无知（存活/退出码判定藏在本 adapter 的迭代器/handle 内，非 schedule）；port 签名/线格式/wire 一行不改（复用 `event_from_line`/`job_to_line`）。

**PK 由 run_id + scope_id 复合**（防重复跑同一 feature 撞键——scope_id 只在 feature 内稳定、不含 run_id，见 ADR 0024）：
run_id 组合根构造期注入本 adapter（对称已有 artifact_s3 落点注入，__main__ 在 new_run_id 后才 build_engines）。

**证据边界（CLAUDE.md「绿≠对」）**：moto 能验接线/RunTask 调对/Query 增量/退出码翻异常；但 moto 对 ECS `lastStatus`
状态机（STOPPED 前 exitCode=null 时序）、DDB 最终一致读的真实时序**保真度存疑**——轮询节奏/STOPPED 滞后/终读一致性的
真行为已由真容器校准厘清（见 ADR 0032 真容器校准结论）。
"""
from __future__ import annotations

import logging
import time
from typing import Iterator, NamedTuple
from urllib.parse import quote

from gherkai_core.adapters._boto import require_boto3
from gherkai_core.model import Event, Job, ScopeDone
from gherkai_core.wire import event_from_line, job_to_line, raise_for_worker_exit

# events 表 schema 的**单一事实源**（ADR 0024「DynamoDB 作 events-out」+ ADR 0034 机制一）：PK=run_id#scope_id、
# SK=scope 内单调 seq。**读写两侧共用**——`DdbEventLog` import 这批常量，别在别处再抄一份（抄一份 = 两处漂移）。
PK_ATTR = "pk"
SK_ATTR = "seq"
BODY_ATTR = "body"  # 0024 事件的 JSON line 原样（DDB 不解析 body）
# 平台侧退出观察者写的 `task_exited` 的**独立键空间**（ADR 0034 机制一）：DDB SK 是 NUMBER、字符串前缀结构上
# 不可行，故用保留高位数值 SK（worker seq 从 1 递增、永不到它）+ `item_type` 属性承载，退出记录不入 worker 段。
# **该 item 没有 body**：读 worker 段的 Query 必须把 SK 上界收在 `EXIT_SK - 1`，否则读到它 → KeyError('body')。
# 取值 10^18 = 远超任何真实 scope 事件数的大数（DDB Number 精度内；虽超 JSON 安全整数，但 DDB 线上存字符串数值故 OK）。
logger = logging.getLogger("gherkai_core.adapters.fargate_engine")

# 流式期最终一致读的断号宽限秒数（ADR 0024「读一致性」）：游标只越过连续前缀，页内断号处停住、下轮 re-query 补齐；
# 断号持续超过此宽限 = 写者侧真洞（worker PutItem 失败但 seq 已耗——SDK 关重试、单次墙钟封顶）→ 记警告越过，别让流式读
# 无界停摆（schedule 的静默兜底会把停摆误判成 worker 卡死）。EC 滞后通常 <1s，5s 留足余量；构造期可覆盖（测试）。
EC_GAP_GRACE_S = 5.0

EXIT_SK = 10 ** 18
ITEM_TYPE_ATTR = "item_type"
EXIT_ITEM_TYPE = "exit"     # item_type 取值：退出记录（worker 事件 item 不带此属性）
EXIT_CODE_ATTR = "exit_code"

class TaskProbe(NamedTuple):
    """一次 DescribeTasks 探测的结果——**两个正交事实各自命名**（ADR 0024「exitCode 落值延迟」）：

    - `stopped`：task 是否已到 STOPPED 终态。
    - `exit_code`：container 的 exitCode；`None` = 尚未落值。

    **关键：`stopped` 与 `exit_code` 非原子**——DescribeTasks 的 `lastStatus==STOPPED` 翻转与 `containers[].exitCode`
    落值可分两次可见，STOPPED 瞬间 exit_code 可能短暂 `None`（AWS 有记录的时序）。故三种有意义组合：
    `(False, None)`=未 STOPPED（继续轮询）；`(True, None)`=已 STOPPED 但码尚未落值（有界多等几拍，别当异常）；
    `(True, int)`=已 STOPPED 且落值。用命名字段表达，避免把"到没到终态"与"码落没落值"挤进一个过载返回值。"""
    stopped: bool
    exit_code: int | None


def events_pk(run_id: str, scope_id: str) -> str:
    """events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。"""
    return f"{run_id}#{scope_id}"


class FargateWorkerHandle:
    """一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称 SubprocessWorkerHandle）。"""

    def __init__(self, ecs_client, cluster: str, task_arn: str) -> None:
        self._ecs = ecs_client
        self._cluster = cluster
        self._task_arn = task_arn

    def stop(self, grace_period_s: float) -> None:
        """请求优雅停止 = StopTask。

        **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器 SIGTERM→SIGKILL 的宽限由 task-def 期
        常量 `stopTimeout`（≤120s）决定、StopTask 不收运行期 grace 参数。故此处忽略入参、只发 StopTask——
        Nova grace 下限 150s > stopTimeout 上限 120s：真容器标定（ADR 0032 结论 4）已厘清——subprocess 侧
        150 满足不变量、Fargate 侧对最坏长 act（跑满 act_timeout）结构性接受 SIGKILL + AgentCore TTL 兜底。
        参数保留是为 port 对称。
        """
        self._ecs.stop_task(cluster=self._cluster, task=self._task_arn, reason="core requested stop")


class FargateEngine:
    """Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。

    组合根构造期注入（对称 __main__ 在 new_run_id 后 build_engines 注入 artifact_s3 落点）：
    - ecs/s3/ddb client：boto3 句柄（adapter 不自建，ADR 0016）。
    - run_id：拼 events 表 PK 用（每 run 一个 engine 实例，run_id 构造期已生成）。
    - task_config：cluster / task_definition / network（subnet/security-group/assign-public-ip）——**真值由后端 stack（`gherkai-deploy-aws`）
      （ADR 0033）产出、组合根注入**；本 adapter 只认字段、不知真 ARN（moto 测用假值验接线）。
      **`task_definition` 是一个显式 revision ARN、不是 family 名**（ADR 0038 不变量「运行时只用 definition 里的
      显式 revision，永不用 family 取最新」）：family 名下 ECS 取该 family 最新 ACTIVE revision，多 variant 并存时
      任何一次 `push-worker` 都会劫持在跑的 run（中途换 step 集）。选哪个 revision 是组合根的事（`compose` 按
      definition 的 `worker_variant` 解析），本 adapter 原样传给 RunTask、不做任何名字推导。
    - job_s3：(bucket, prefix) job 对象落点；events_table_name：events 表名（worker PutItem 目标）。
    - region：组合根**落实成具体字符串**的 AWS region（`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile config，
      ADR 0016 决策 C）——非 None 时经 RunTask overrides 注入 worker 的 `AWS_REGION`，使 worker 建 boto3/aws-sdk client
      （EventSink DDB / JobSource S3 / ArtifactUploader）拿到与 core store 侧**同源**的 region。Fargate 容器不继承本地 env、
      也不吃 profile config（AgentCore `validate_region` 要显式字符串），故必须由组合根落实后显式注入（否则 worker
      `region_name=None` → NoRegionError / AgentCore InvalidRegionError）。**与 subprocess 的 `build_engines` 注入同源**。
      **不接收 profile**（正确的非对称，ADR 0016 决策 C）：Fargate 容器无 `~/.aws`、用 task role 凭证链——注入一个容器内
      不存在的 profile 名会让 boto3 在 client 创建期 `ProfileNotFound` 崩、且盖过 task role。profile 只对 subprocess
      有意义（继承本机 `~/.aws`），故只 `build_engines` 注入、本 adapter 绝不碰。
    - poll_interval_s：Query 轮询间隔（延迟 vs 读放大权衡，ADR 0024，待真跑标定；默认 0.5s）。
    """

    def __init__(
        self,
        *,
        ecs_client,
        s3_client,
        ddb_events_table,          # boto3 dynamodb.Table 资源（events 表；建表责任 IaC）
        run_id: str,
        cluster: str,
        task_definition: str,  # **显式 revision ARN**（`…:task-definition/{family}:{N}`），绝不 family 名——ADR 0038 不变量
        network_config: dict,      # {"subnets":[...], "securityGroups":[...], "assignPublicIp":"ENABLED"/"DISABLED"}
        job_s3: tuple[str, str],   # (bucket, prefix)：job 对象落 s3://bucket/prefix<scope_id>.json
        events_table_name: str,    # 注入 worker 的 events 表名（worker PutItem 目标）
        container_name: str,       # RunTask overrides 要指定往哪个 container 注 env
        artifact_s3: tuple[str, str] | None = None,  # (bucket, prefix)：worker 产物上传落点（ADR 0029）——注入 worker 的
                                   # ARTIFACT_S3_BUCKET/PREFIX，否则容器盘停即销毁、产物必丢（ADR 0029「cloud 下注入不是可选」）。None=不上传
        extra_env: dict | None = None,  # 通用附加 env（组合根算好，如 GHERKAI_EXTRA_HTTP_HEADERS，ADR 0035）——逐条注 RunTask overrides
        sdk_artifact_dir_env: dict | None = None,  # 按引擎的 SDK 产物落点 env（如 {"NOVA_LOGS_DIR": "/容器内/…/nova-trajectories"}）——
                                   # worker ArtifactUploader 用其父级算 run_dir/相对 key。**缺它 uploader run_dir=None→no-op 报 file://→产物丢**
                                   # （真跑暴露：只注 ARTIFACT_S3_* 不够，SDK 落点 env 也必注）。引擎无关：由组合根按引擎算好、本 adapter 只转发。
        region: str | None = None, # 注入 worker 的 AWS_REGION（组合根已落实成具体字符串，ADR 0016 决策 C）；None＝真无 region、worker fail-loud
        poll_interval_s: float = 0.5,
        gap_grace_s: float = EC_GAP_GRACE_S,  # 流式期断号宽限（ADR 0024「读一致性」，见模块常量注释）
        null_exit_grace_polls: int = 5,  # STOPPED 但 exitCode 尚 null 时的有界宽限拍数（ADR 0024「exitCode 落值延迟」）——
                                   # 多等这么多拍等落值，超限才落定异常码 1（防把落值延迟误报 error）。5×0.5s≈2.5s，远大于落值瞬时窗口。
    ) -> None:
        require_boto3("FargateEngine")
        self._ecs = ecs_client
        self._s3 = s3_client
        self._events = ddb_events_table
        self._run_id = run_id
        self._cluster = cluster
        self._task_def = task_definition
        self._network = network_config
        self._job_bucket, self._job_prefix = job_s3
        self._events_table_name = events_table_name
        self._container = container_name
        self._artifact_s3 = artifact_s3  # (bucket, prefix) or None——注入 worker 产物上传落点（ADR 0029）
        self._sdk_artifact_dir_env = sdk_artifact_dir_env or {}  # 按引擎 SDK 落点 env（NOVA_LOGS_DIR/MIDSCENE_RUN_DIR）
        self._extra_env = extra_env or {}  # 通用附加 env（ADR 0035 extra headers 等；组合根注入、worker 消费）
        self._region = region
        # 不存 profile：Fargate 用 task role，注入 profile 名会 ProfileNotFound 盖过 task role（ADR 0016 决策 C 的非对称）。
        self._poll = poll_interval_s
        self._gap_grace_s = gap_grace_s
        self._null_exit_grace_polls = null_exit_grace_polls

    def start_scope(self, job: Job) -> str:
        """fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine 增出形状）。

        = run_scope 的前半（PutObject job + RunTask），**不返回事件迭代器、不轮询**——cloud 无状态路径下 worker
        自 PutItem events 到 DDB、退出观察者 Lambda 补 task_exited、reconciler Lambda 从表重放，没有「调用方持续
        迭代」（对照 run_scope 的 pull 式，同步 run 路径用）。CloudLauncher 在 reconciler CAS 抢占成功后调它。
        run_scope 现 delegate 到本方法拿 task_arn，再加事件迭代器（同步路径），保两路径起 task 逻辑单一真源。
        """
        return self._put_job_and_run_task(job)

    def _put_job_and_run_task(self, job: Job) -> str:
        # ① job-in 走 S3（ADR 0024 A3）：整 job 序列化（复用 wire.job_to_line）PutObject，env 只传小指针 JOB_S3_URI。
        # scope_id 用 quote(safe='')：/ 也编码成 %2F——否则 scope_id 里的 `/`（如 feature 路径）在 job_prefix 下
        # 造 S3 假子前缀（jobs-in/features%2F… 被拆成多级"目录"）。job-in 落 **独立前缀 jobs-in/**（组合根
        # build_fargate_engines 注入、与 ResultStore 的 jobs/ 物理隔离、不撞 key）；worker 经 JOB_S3_URI 全指针
        # GetObject 读、不 list/unquote 枚举，故 quote 的唯一作用是避假子前缀（编码沿用 ResultStore 的 quote(safe='') 惯例）。
        job_key = f"{self._job_prefix}{quote(job.scope_id, safe='')}.json"
        # 打 tag `gherkai=job-in`：job-in 是喂 worker 的一次性输入（worker GetObject 读完即无用），桶按此 tag
        # 挂 S3 lifecycle 过期清理（ADR 0033）。**用 tag 而非 key 前缀过滤**——job-in 落 `<prefix><run_id>/jobs-in/`，
        # run_id 在中间，lifecycle 的纯前缀 filter 框不住它、且不能误伤同前缀下的判定真值(jobs/)/报告；tag 精确只框 job-in。
        # Tagging 是 URL-encoded 查询串格式（`k=v`）。**打 tag 的是编排进程**（本 put_object 在 FargateEngine=组合根注入的
        # s3_client 上跑、用运维凭证），非 worker task role（后者只 GetObject 读 job-in），故无需给 task role 加 PutObjectTagging。
        self._s3.put_object(
            Bucket=self._job_bucket, Key=job_key,
            Body=(job_to_line(job) + "\n").encode("utf-8"),
            Tagging="gherkai=job-in",
        )
        job_s3_uri = f"s3://{self._job_bucket}/{job_key}"

        # ② RunTask：env 注入 worker 的 I/O 边缘落点（JOB_S3_URI / events 表 / run_id / scope_id）——worker 的
        # JobSource 读 JOB_S3_URI GetObject、EventSink 拼 PK=run_id#scope_id PutItem 到 events 表。run_id 组合根期已注入本 engine。
        env = [
            {"name": "JOB_S3_URI", "value": job_s3_uri},
            {"name": "EVENTS_DDB_TABLE", "value": self._events_table_name},
            {"name": "RUN_ID", "value": self._run_id},
            {"name": "SCOPE_ID", "value": job.scope_id},
        ]
        # 产物上传落点（ADR 0029）：非 None 时注入 ARTIFACT_S3_BUCKET/PREFIX，worker ArtifactUploader 据此上传→报 s3://→删本地。
        # **cloud 下必注入**——否则 worker no-op 报 file://、产物写容器临时盘、STOPPED 后盘销毁必丢（ADR 0029「cloud 注入不是可选」/0032）。
        if self._artifact_s3 is not None:
            env.append({"name": "ARTIFACT_S3_BUCKET", "value": self._artifact_s3[0]})
            env.append({"name": "ARTIFACT_S3_PREFIX", "value": self._artifact_s3[1]})
        # SDK 产物落点 env（NOVA_LOGS_DIR/MIDSCENE_RUN_DIR，组合根按引擎算好的容器内路径）：worker ArtifactUploader
        # 用其父级算 run_dir/相对 key——**缺它 uploader run_dir=None→no-op→产物丢**（真跑暴露；只注 ARTIFACT_S3_* 不够）。
        for name, value in self._sdk_artifact_dir_env.items():
            env.append({"name": name, "value": value})
        for name, value in self._extra_env.items():  # 通用附加 env（如 GHERKAI_EXTRA_HTTP_HEADERS，ADR 0035）
            env.append({"name": name, "value": value})
        # region 与 core store 同源注入（ADR 0016 决策 C）：Fargate 容器不继承本地 env、也不吃 profile config，非 None 时
        # 显式传（组合根已落实成具体字符串），否则 worker region_name=None → NoRegionError/AgentCore InvalidRegionError。
        # **不注入 AWS_PROFILE**：容器用 task role，注入 profile 名会 ProfileNotFound 盖过 task role（正确的非对称）。
        if self._region is not None:
            env.append({"name": "AWS_REGION", "value": self._region})
        resp = self._ecs.run_task(
            cluster=self._cluster,
            taskDefinition=self._task_def,
            launchType="FARGATE",
            networkConfiguration={"awsvpcConfiguration": self._network},
            overrides={"containerOverrides": [{"name": self._container, "environment": env}]},
            count=1,
            # startedBy=run_id（ADR 0034「job timeout」节）：超时处置用 ListTasks(startedBy=run_id) 定位本 run
            # 的 task（≤36 字符约束：run_id 形如 20260629T141207Z-a3f9c1 共 23 字符，恒满足）。
            startedBy=self._run_id,
        )
        # RunTask 的放置失败（容量不足/子网无 IP/资源约束/task-def 校验）是**正常契约**：HTTP 200 + 空 tasks + 填 failures
        # （reason/detail），非抛异常。不检查就直接 resp["tasks"][0] 会抛无信息的裸 IndexError、丢掉 ECS 给的可归因原因。
        tasks = resp.get("tasks", [])
        if not tasks:
            failures = resp.get("failures", [])
            reason = failures[0].get("reason", "unknown") if failures else "no reason given"
            detail = failures[0].get("detail", "") if failures else ""
            raise RuntimeError(f"RunTask 未起 task（放置失败）：reason={reason} detail={detail}")
        task_arn = tasks[0]["taskArn"]
        return task_arn

    def run_scope(self, job: Job) -> tuple[FargateWorkerHandle, Iterator[Event]]:
        """起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称 SubprocessEngine.run_scope。

        同步 run 路径用（schedule pull 式迭代）。delegate 到 _put_job_and_run_task 起 task（与 start_scope
        单一真源），再包 handle + 事件迭代器。cloud 无状态路径不用它、用 start_scope（fire-and-forget）。
        """
        task_arn = self._put_job_and_run_task(job)
        handle = FargateWorkerHandle(self._ecs, self._cluster, task_arn)
        return handle, self._read_events(job.scope_id, task_arn)

    def _read_events(self, scope_id: str, task_arn: str) -> Iterator[Event]:
        """Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。

        **天然定向 + 天然幂等**（ADR 0024，DDB 相对 SQS 的核心简化）：Query PK=run_id#scope_id 只返回本 run 本 scope
        的事件（查询即分流、无 dispatcher）；Query 是非破坏性读、last_seq 是本地游标（非删除），重读同一 seq 无副作用（无去重表）。

        **纯事件流、不掺心跳**（Engine port 铁律）：静默时本迭代器阻塞在轮询上，schedule 的 _heartbeat_wrap 兜底唤醒查超时。

        **终止 = 内容完整 + 进程终止两件事、都要**（ADR 0024「事件流结束信号」，与 subprocess「fd EOF + 无条件
        proc.wait()」严格同构）：① 内容完整判据 = 读到本 scope 的 scope_done（最大 seq、最后一条），或 worker 崩溃没发；
        ② **无论哪种，都等 DescribeTasks STOPPED 读 exitCode 再翻异常**——scope_done 非终态，worker 可发完它又在会话
        释放阶段非 0 退出（Midscene cleanupFailed→exit 1），"读到 scope_done 即 break、不读码"会吞掉它、job 误报
        PASSED（违「会话释放失败可观测」不变量）。代价 = 每 scope 收尾等 ~11s（ECS 记录 executionStoppedAt 平台滞后，
        ADR 0032 结论 2）；一次性、事件早经 Query yield、不影响流式期进度。
        """
        from boto3.dynamodb.conditions import Key

        last_seq = 0  # 已消费的**连续前缀**末 seq（不是页内最大 seq）
        gap_since: float | None = None  # 首次撞见当前断号的时刻；None = 当前无断号
        pk = events_pk(self._run_id, scope_id)
        while True:
            # 增量 Query：本 scope 的 **worker 段**、last_seq<SK<EXIT_SK、SK 升序（保序）。最终一致读（默认）——
            # 漏读靠「游标只越过连续前缀」补齐（见下断号分支）。**上界必须收在 EXIT_SK-1**：退出观察者的 task_exited
            # item 挂同 PK 的保留高位 SK 且无 body（ADR 0034 机制一），读进 worker 段即 KeyError；ADR 0024 亦定「单调/断号只跑 worker 段」。
            resp = self._events.query(
                KeyConditionExpression=Key(PK_ATTR).eq(pk) & Key(SK_ATTR).between(last_seq + 1, EXIT_SK - 1),
                ScanIndexForward=True,
            )
            items = resp.get("Items", [])
            saw_scope_done = False
            consumed = 0
            for it in items:
                seq = int(it[SK_ATTR])
                if seq != last_seq + 1:
                    # 断号（ADR 0024「读一致性」）：最终一致读可能先看到后写的 item。游标**不越过洞**——在此停住，
                    # 下轮从 last_seq+1 re-query 补齐（Query 非破坏、重读无副作用）。曾直接把游标推到页内最大 seq，
                    # 洞被永久越过（step/scenario 结果静默缺失）。
                    now = time.monotonic()
                    if gap_since is None:
                        gap_since = now
                    if now - gap_since < self._gap_grace_s:
                        break  # 宽限内：等下轮
                    # 宽限已过 = 写者侧真洞（worker PutItem 失败但 seq 已耗）→ 记警告、越过继续，别让流式读无界停摆
                    # （schedule 的静默兜底会把停摆误判成 worker 卡死）。
                    logger.warning("events 断号：scope %s 的 seq %d..%d 在 %.0fs 内未出现，视为写者侧丢失、越过继续",
                                   scope_id, last_seq + 1, seq - 1, self._gap_grace_s)
                gap_since = None
                last_seq = seq
                consumed += 1
                event = event_from_line(it[BODY_ATTR])
                yield event  # 解析失败抛 ValueError，schedule 记 error（同 subprocess）
                if isinstance(event, ScopeDone):  # 终止判据：scope_done 是最后一条（复用已解析 event、不重复解析 body）
                    saw_scope_done = True
            if saw_scope_done:
                # 内容完整（scope_done 是最后一条）；但终止仍须等 STOPPED 读 exitCode——与 subprocess「fd EOF 后无条件
                # proc.wait()」同构：捕获「worker 发完 scope_done 又会话释放失败非 0 退出」（Midscene cleanupFailed→exit 1）。
                # exit>0 抛（schedule 记 error、泄漏可观测）、exit==0 正常终止（ADR 0024「事件流结束信号」）。
                # 不 _final_drain：scope_done 是最大 seq、已读到，SK>last_seq 必空（drain 只为「靠 STOPPED 兜底」路径补最终一致漏读）。
                raise_for_worker_exit(self._await_exit_code(task_arn), code_label="exitCode")
                return

            # 本轮无进展（无新事件，或停在断号处等补齐）且未见 scope_done：查 task 是否已 STOPPED（兜底：worker 崩溃没发 scope_done）
            if consumed == 0:
                if self._probe_task(task_arn).stopped:  # 已 STOPPED（exitCode 是否落值不影响"该终结了"）——别再拉事件
                    # task 已 STOPPED。终读强一致 Query 从 last_seq+1 读全（含停在断号处未消费的部分；补最终一致还没看到的
                    # 末尾 PutItem，ADR 0024 读一致性条）——终读里的断号即真洞、只记警告。
                    yield from self._final_drain(pk, last_seq)
                    # 拿确定退出码：_await_exit_code 处理「exitCode 尚 null」的有界宽限（ADR 0024「exitCode 落值延迟」）——
                    # 与 scope_done 路径复用同一读码逻辑（此刻已 STOPPED、几乎立即返回，除非撞落值延迟窗口）。
                    raise_for_worker_exit(self._await_exit_code(task_arn), code_label="exitCode")
                    return
                time.sleep(self._poll)  # task 还在跑、暂无新事件 → 等一个轮询周期再拉（延迟 vs 读放大，ADR 0024）

    def _final_drain(self, pk: str, last_seq: int) -> Iterator[Event]:
        """task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。

        **必须翻页**（与主循环不同）：主循环靠逐轮 `SK>last_seq` re-query 天然跨 1MB 单页上限；但终读是
        「最后一次、之后 `raise_for_worker_exit`+return、不再 query」，单次 query 遇上 >1MB 尾部（DDB Query 单页
        上限）会返回 `LastEvaluatedKey` 并把余下 item 留在下一页——不循环 `ExclusiveStartKey` 就静默丢弃，
        与本函数「反映所有在先成功写」的强一致承诺相悖。故 while 循环拉全所有页。
        """
        from boto3.dynamodb.conditions import Key

        kwargs = {
            # 与主循环同一段界：只读 worker 段（上界 EXIT_SK-1 排除无 body 的 task_exited item，ADR 0034 机制一）。
            "KeyConditionExpression": Key(PK_ATTR).eq(pk) & Key(SK_ATTR).between(last_seq + 1, EXIT_SK - 1),
            "ScanIndexForward": True,
            "ConsistentRead": True,  # 强一致：反映所有在先成功写（2× RRU，成本忽略；防永久漏最后几条）
        }
        expected = last_seq + 1
        while True:
            resp = self._events.query(**kwargs)
            for it in resp.get("Items", []):
                seq = int(it[SK_ATTR])
                if seq != expected:
                    # 强一致读里的断号 = 写者侧真洞（worker PutItem 失败但 seq 已耗），无从补、只记警告（ADR 0024 读一致性）
                    logger.warning("events 终读断号：%s 的 seq %d..%d 缺失（强一致读、写者侧丢失）", pk, expected, seq - 1)
                expected = seq + 1
                yield event_from_line(it[BODY_ATTR])
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break  # 无更多页 → 拉全
            kwargs["ExclusiveStartKey"] = last_key  # 续下一页（>1MB 尾部才触发）

    def _probe_task(self, task_arn: str) -> TaskProbe:
        """DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR 0024「exitCode 落值延迟」）。

        未 STOPPED → (False, None)；已 STOPPED 但 exitCode 尚 null（缺 container 亦然）→ (True, None)；
        已 STOPPED 且落值 → (True, int)。stopped 与 exit_code 非原子（见 TaskProbe），故分开返回、不揉进单值。
        """
        resp = self._ecs.describe_tasks(cluster=self._cluster, tasks=[task_arn])
        tasks = resp.get("tasks", [])
        if not tasks or tasks[0].get("lastStatus") != "STOPPED":
            return TaskProbe(stopped=False, exit_code=None)  # 未 STOPPED
        containers = tasks[0].get("containers", [])
        # 已 STOPPED。找本 worker container 的 exitCode；缺 container / exitCode 尚 null → (True, None)（落值延迟，非"当异常"）。
        c = next((c for c in containers if c.get("name") == self._container), containers[0] if containers else None)
        return TaskProbe(stopped=True, exit_code=(c.get("exitCode") if c else None))

    def _await_exit_code(self, task_arn: str) -> int:
        """轮询 DescribeTasks 直到拿到确定的 exitCode——scope_done 后读退出码用（ADR 0024「事件流结束信号」）。

        scope_done 只表示事件流内容完整、非进程终态；等 STOPPED 读码才能捕获「worker 发完 scope_done 又会话释放失败
        非 0 退出」（Midscene cleanupFailed→exit 1），与 subprocess 无条件 proc.wait() 同构。阻塞期 = worker 会话释放
        + ECS 记录 executionStoppedAt 平台滞后（~11s，ADR 0032 结论 2）；轮询静默时由 schedule _heartbeat_wrap/deadline
        兜底唤醒（同主循环兜底路径的 sleep 轮询，不会真无限——worker 已在退出路径、很快 STOPPED）。

        **STOPPED 但 exitCode 尚 null**（ADR 0024「exitCode 落值延迟」）：不立即当异常（否则把干净退出误报 error），
        **有界**多等 `_null_exit_grace_polls` 拍等落值；超限仍 null 才落定为 1（容器真被强杀/没报码，非落值延迟）。
        """
        pending_polls = 0
        while True:
            probe = self._probe_task(task_arn)
            if not probe.stopped:  # 未 STOPPED → 继续轮询等终态
                time.sleep(self._poll)
                continue
            if probe.exit_code is None:  # 已 STOPPED 但 exitCode 尚 null：有界多等几拍等落值
                if pending_polls >= self._null_exit_grace_polls:
                    return 1  # 超宽限仍 null → 落定异常（容器没报码，非落值延迟）
                pending_polls += 1
                time.sleep(self._poll)
                continue
            return probe.exit_code  # STOPPED 且落值
