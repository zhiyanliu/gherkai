"""Fargate 执行 adapter（ADR 0024「远程传输演进」节；ADR 0034「Engine port 演进」节）：在 ECS Fargate 上起一个讲 ADR 0024 协议的
worker task。

云端后端只有后台推进路径（ADR 0016 决策 A），本 adapter 因此只有 `start_scope`：上传 job、发 RunTask、返回 task ARN，不返回事件迭代器、
不轮询，也不实装 `Engine` port。推进器 Lambda 经 `CloudLauncher` 在认领成功之后调它；worker 自己把事件写进 DDB events 表，退出码由
平台侧的退出观察者写成退出记录，推进器从表里重放（ADR 0034 机制一、机制二）。

与子进程 adapter 相比，各条 I/O 边缘换成的传输（对应 ADR 0024「远程传输演进」节的通道表）：

| 边缘 | 子进程 | Fargate |
|---|---|---|
| job 入口 | 写 worker stdin | 本 adapter `PutObject` 整个 job 到 S3，RunTask overrides 经 env 只传小指针 `JOB_S3_URI`（overrides 有 8192 字符上限，含 feature 的 job 放不下） |
| 事件出口 | 读 `EVENTS_FD` 的 fd | worker `PutItem` 到 DDB events 表；读端是推进器的全量重放与 `explain`，经 `DdbEventLog` 读，不经本 adapter |
| 停 / 退出码 | SIGTERM→grace→SIGKILL；`proc.wait()` | 停 task 由推进器调 `StopTask`；退出码由退出观察者从 ECS 的 STOPPED 事件读出（ADR 0024「控制面不走 events 表」条） |

**红线**：boto3 client 由组合根注入、adapter 不自建（`require_boto3` 首行守卫，ADR 0016）；线格式与 wire 不改，job 行复用
`wire.job_to_line`（ADR 0024「远程传输演进」节①）。

**PK 由 run_id 与 scope_id 复合**（防重复运行同一 feature 撞键：scope_id 只在 feature 内稳定、不含 run_id，见 ADR 0024「DynamoDB 作
events-out 传输」节「表键设计」条）：run_id 由推进器一侧的组合根 `compose.build_fargate_engines` 在构造时注入，经 RunTask overrides 交给
worker 拼 PK。

**证据边界**：moto 能验 RunTask 的参数、env 注入、job 对象的键与 tag；task 能否真起来（放置、拉镜像）只有真部署之后的云端 submit 能证。
"""
from __future__ import annotations

from urllib.parse import quote

from gherkai_core.adapters._boto import require_boto3
from gherkai_core.model import Job
from gherkai_core.wire import job_to_line

# events 表 schema 的**单一事实源**（ADR 0024「DynamoDB 作 events-out 传输」节 + ADR 0034 机制一）：PK=run_id#scope_id、
# SK=scope 内单调 seq。**读写两侧共用**——`DdbEventLog`（退出观察者与推进器都经它读写）import 这批常量，别在别处再抄一份
# （抄一份即两处漂移）。
PK_ATTR = "pk"
SK_ATTR = "seq"
BODY_ATTR = "body"  # 0024 事件的 JSON line 原样（DDB 不解析 body）

# 平台侧退出观察者写的 `task_exited` 的**独立键空间**（ADR 0034 机制一）：DDB SK 是 NUMBER、字符串前缀结构上
# 不可行，故用保留高位数值 SK（worker seq 从 1 递增、永不到它）+ `item_type` 属性承载，退出记录不入 worker 段。
# **该 item 没有 body**：读 worker 事件的一方须按 `item_type` 分流，否则读到它 → KeyError('body')。
# 取值 10^18 是远超任何真实 scope 事件数的大数（DDB Number 精度内；虽超 JSON 安全整数，但 DDB 线上存字符串数值故 OK）。
EXIT_SK = 10 ** 18
ITEM_TYPE_ATTR = "item_type"
EXIT_ITEM_TYPE = "exit"     # item_type 取值：退出记录（worker 事件 item 不带此属性）
EXIT_CODE_ATTR = "exit_code"


def events_pk(run_id: str, scope_id: str) -> str:
    """events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker 与读端各自本地拼、须逐字一致。"""
    return f"{run_id}#{scope_id}"


class FargateEngine:
    """在 Fargate 上起 worker task 的 adapter（推进器一侧的组合根注入 boto3 client 与 run 级配置）。

    推进器 Lambda 的组合根经 `compose.build_fargate_engines` 为每个 run 装配一份（ADR 0016 决策 C；ADR 0033「组合根接线（非 IaC）」节）：
    - ecs/s3 client：boto3 句柄（adapter 不自建，ADR 0016）。
    - run_id：拼 events 表 PK 用，经 RunTask overrides 注入 worker（每 run 一个 engine 实例）。
    - cluster / network_config：**真值由后端 stack（`gherkai-deploy-aws`，ADR 0033）产出**、经推进器 Lambda 的环境变量到组合根；本
      adapter 只认字段、不知真 ARN（moto 测用假值验接线）。
    - task_definition：**显式 revision ARN、不是 family 名**（ADR 0038 不变量「运行时只用 definition 里的显式 revision，永不用 family
      取最新」）：family 名下 ECS 取该 family 最新 ACTIVE revision，多 variant 并存时任何一次 `push-worker` 都会劫持正在运行的 run
      （中途换 step 集）。选哪个 revision 由提交时写进 definition（`worker_task_defs`），推进器的组合根照它传入，本 adapter 原样交给
      RunTask、不做任何名字推导。
    - job_s3：(bucket, prefix) job 对象落点；events_table_name：events 表名（worker PutItem 目标）。
    - region：部署所在区域，由推进器的组合根取得（IaC 注入推进器 Lambda 的 `REGION`；ADR 0016 决策 C「region」条，ADR 0033「组合根接线
      （非 IaC）」节「Fargate 配置参数」条）。非 None 时经 RunTask overrides 注入 worker 的 `AWS_REGION`，使 worker 建 boto3/aws-sdk
      client（EventSink DDB / JobSource S3 / ArtifactUploader）拿到与推进器 store 句柄同一个 region。Fargate 容器不继承宿主 env、也不吃
      profile config（AgentCore `validate_region` 要显式字符串），故须显式注入（否则 worker `region_name=None` → NoRegionError /
      AgentCore InvalidRegionError）。
      **不接收 profile**（正确的非对称，ADR 0016 决策 C「profile」条）：Fargate 容器无 `~/.aws`、用 task role 凭证链——注入一个容器内
      不存在的 profile 名会让 boto3 在 client 创建期 `ProfileNotFound` 崩、且盖过 task role。
    """

    def __init__(
        self,
        *,
        ecs_client,
        s3_client,
        run_id: str,
        cluster: str,
        task_definition: str,  # **显式 revision ARN**（`…:task-definition/{family}:{N}`），绝不 family 名——ADR 0038 不变量
        network_config: dict,      # {"subnets":[...], "securityGroups":[...], "assignPublicIp":"ENABLED"/"DISABLED"}
        job_s3: tuple[str, str],   # (bucket, prefix)：job 对象落 s3://bucket/prefix<scope_id>.json
        events_table_name: str,    # 注入 worker 的 events 表名（worker PutItem 目标）
        container_name: str,       # RunTask overrides 要指定往哪个 container 注 env
        # 下面两个产物落点参数**必给关键字、无缺省**：cloud 下两者必注，漏传即静默丢产物（实际运行暴露过一次），
        # 与 ADR 0038 的显式 revision 判法一致——漏传即在装配点报错，不做成「忘了传就静默破」。
        artifact_s3: tuple[str, str] | None,  # (bucket, prefix)：worker 产物上传落点（ADR 0029）——注入 worker 的
                                   # ARTIFACT_S3_BUCKET/PREFIX，否则容器盘停即销毁、产物必丢（ADR 0029「cloud 下注入不是可选」）。None 表示显式不上传
        sdk_artifact_dir_env: dict,  # 按引擎的 SDK 产物落点 env（如 {"NOVA_LOGS_DIR": "/容器内/…/nova-trajectories"}）——
                                   # worker ArtifactUploader 用其父级算 run_dir/相对 key。**缺它 uploader run_dir=None→no-op 报 file://→产物丢**
                                   # （实际运行暴露：只注 ARTIFACT_S3_* 不够，SDK 落点 env 也必注）。引擎无关：由组合根按引擎算好、本 adapter 只转发。
        extra_env: dict | None = None,  # 通用附加 env（组合根算好，如 GHERKAI_EXTRA_HTTP_HEADERS，ADR 0035）——逐条注 RunTask overrides
        region: str | None = None, # 注入 worker 的 AWS_REGION（部署所在区域，ADR 0016 决策 C）；None 表示真无 region、worker fail-loud
    ) -> None:
        require_boto3("FargateEngine")
        self._ecs = ecs_client
        self._s3 = s3_client
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

    def start_scope(self, job: Job) -> str:
        """起一个 Fargate task 执行 job（上传 job、发 RunTask），返回 task_arn（ADR 0034「Engine port 演进」节）。

        不返回事件迭代器、不轮询：worker 自己把事件 PutItem 进 DDB events 表，退出观察者 Lambda 补写 task_exited，推进器从表里重放。
        `CloudLauncher` 在推进器认领成功之后调它。RunTask 的放置失败抛 RuntimeError（带 ECS 给的 reason 与 detail），由调用方按起
        worker 失败处理。
        """
        return self._put_job_and_run_task(job)

    def _put_job_and_run_task(self, job: Job) -> str:
        # ① job-in 走 S3（ADR 0024「远程传输演进」节通道表的 job 入口一行）：整 job 序列化（复用 wire.job_to_line）PutObject，env 只传小指针 JOB_S3_URI。
        # scope_id 用 quote(safe='')：/ 也编码成 %2F——否则 scope_id 里的 `/`（如 feature 路径）在 job_prefix 下
        # 造 S3 假子前缀（jobs-in/features%2F… 被拆成多级"目录"）。job-in 落 **独立前缀 jobs-in/**（组合根
        # build_fargate_engines 注入、与判定明细的 jobs/ 前缀分开）；worker 经 JOB_S3_URI 全指针
        # GetObject 读、不 list/unquote 枚举，故 quote 的唯一作用是避假子前缀（不透明标识符作键里的一段时的通行编码，判定明细的键对
        # 它的标识用同一种编码）。
        job_key = f"{self._job_prefix}{quote(job.scope_id, safe='')}.json"
        # 打 tag `gherkai=job-in`：job-in 是喂 worker 的一次性输入（worker GetObject 读完即无用），桶按此 tag
        # 挂 S3 lifecycle 过期清理（ADR 0033「job-in S3 对象生命周期」条）。**用 tag 而非 key 前缀过滤**——job-in 落 `<prefix><run_id>/jobs-in/`，
        # run_id 在中间，lifecycle 的纯前缀 filter 框不住它、且不能误伤同前缀下的判定明细(jobs/)/报告；tag 精确只框 job-in。
        # Tagging 是 URL-encoded 查询串格式（`k=v`）。**打 tag 的是推进器 Lambda**（本 put_object 在推进器组合根注入的 s3_client 上执行、
        # 用 Lambda 执行角色的凭证），非 worker task role（后者只 GetObject 读 job-in），故无需给 task role 加 PutObjectTagging。
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
        # 用其父级算 run_dir/相对 key——**缺它 uploader run_dir=None→no-op→产物丢**（实际运行暴露；只注 ARTIFACT_S3_* 不够）。
        for name, value in self._sdk_artifact_dir_env.items():
            env.append({"name": name, "value": value})
        for name, value in self._extra_env.items():  # 通用附加 env（如 GHERKAI_EXTRA_HTTP_HEADERS，ADR 0035）
            env.append({"name": name, "value": value})
        # region 与推进器 store 句柄同源注入（ADR 0016 决策 C）：Fargate 容器不继承宿主 env、也不吃 profile config，非 None 时
        # 显式传，否则 worker region_name=None → NoRegionError/AgentCore InvalidRegionError。
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
        return tasks[0]["taskArn"]
