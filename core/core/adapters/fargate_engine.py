"""Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024 协议的 worker。

对称 `subprocess_engine.py`（同一 `Engine` port、同一 `(WorkerHandle, Iterator[Event])` 形状），只把「进程世界」换成
「ECS/DDB 世界」——四条 I/O 边缘各自换传输（ADR 0024 远程传输演进表）：

| 边缘 | subprocess | Fargate（本 adapter） |
|---|---|---|
| job-in | 写 worker stdin | `PutObject` 整 job 到 S3、RunTask overrides 经 env 传 `JOB_S3_URI` 小指针（RunTask overrides 8192 上限塞不下含 feature 的 job） |
| events-out | 读 `EVENTS_FD` fd 逐行 | worker `PutItem` 到 DDB events 表；本 adapter `Query PK=run_id#scope_id AND SK>last_seq` 轮询增量拉 → `event_from_line` → yield（events-out=DDB，非 SQS/MSK，见 ADR 0024「DynamoDB 作 events-out」+ 三方案被拒护栏） |
| stop | SIGTERM→grace→SIGKILL | `StopTask`（grace 由 task-def 期 `stopTimeout` 决定、≤120s、不逐次传——Nova 180s>120s 真冲突 defer WP3-B） |
| 退出码 | `proc.wait()` returncode | `DescribeTasks` 轮询到 `lastStatus==STOPPED` → `containers[0].exitCode`（STOPPED 前常 null）→ 同 subprocess 翻异常 |

**红线（ADR 0016/0024/0026）**：boto3 client 由组合根注入、adapter 不自建（`require_boto3` 首行守卫）；schedule 仍纯归约、
对 ECS/DDB 无知（存活/退出码判定藏在本 adapter 的迭代器/handle 内，非 schedule）；port 签名/线格式/wire 一行不改（复用 `event_from_line`/`job_to_line`）。

**PK 由 run_id + scope_id 复合**（防重复跑同一 feature 撞键——scope_id 只在 feature 内稳定、不含 run_id，见 ADR 0024）：
run_id 组合根构造期注入本 adapter（对称已有 artifact_s3 落点注入，__main__ 在 new_run_id 后才 build_engines）。

**证据边界（CLAUDE.md「绿≠对」）**：moto 能验接线/RunTask 调对/Query 增量/退出码翻异常；但 moto 对 ECS `lastStatus`
状态机（STOPPED 前 exitCode=null 时序）、DDB 最终一致读的真实时序**保真度存疑**——轮询节奏/STOPPED 滞后/终读一致性的
真行为须真容器标定（defer WP3-B）。
"""
from __future__ import annotations

import json
import time
from typing import Iterator

from core.adapters._boto import require_boto3
from core.errors import WorkerNetworkError
from core.model import Event, Job
from core.wire import event_from_line, job_to_line

# worker 网络专用退出码（ADR 0028）：与 subprocess_engine.py 同值（两引擎 worker 硬编码 80）。
EX_WORKER_NETWORK = 80

# events 表键字段名（ADR 0024「DynamoDB 作 events-out」）：PK=run_id#scope_id、SK=scope 内单调 seq。
_PK_ATTR = "pk"
_SK_ATTR = "seq"
_BODY_ATTR = "body"  # 0024 事件的 JSON line 原样（DDB 不解析 body）


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
        Nova grace 下限 180s > stopTimeout 上限 120s 的真冲突 defer WP3-B（真容器标定）。参数保留是为 port 对称。
        """
        self._ecs.stop_task(cluster=self._cluster, task=self._task_arn, reason="core requested stop")


class FargateEngine:
    """Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。

    组合根构造期注入（对称 __main__ 在 new_run_id 后 build_engines 注入 artifact_s3 落点）：
    - ecs/s3/ddb client：boto3 句柄（adapter 不自建，ADR 0016）。
    - run_id：拼 events 表 PK 用（每 run 一个 engine 实例，run_id 构造期已生成）。
    - task_config：cluster / task_definition / network（subnet/security-group/assign-public-ip）——**真值由 WP2
      IaC 产出、组合根注入**；本 adapter 只认字段、不知真 ARN（moto 测用假值验接线）。
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
        task_definition: str,
        network_config: dict,      # {"subnets":[...], "securityGroups":[...], "assignPublicIp":"ENABLED"/"DISABLED"}
        job_s3: tuple[str, str],   # (bucket, prefix)：job 对象落 s3://bucket/prefix<scope_id>.json
        events_table_name: str,    # 注入 worker 的 events 表名（worker PutItem 目标）
        container_name: str,       # RunTask overrides 要指定往哪个 container 注 env
        artifact_s3: tuple[str, str] | None = None,  # (bucket, prefix)：worker 产物上传落点（ADR 0029）——注入 worker 的
                                   # ARTIFACT_S3_BUCKET/PREFIX，否则容器盘停即销毁、产物必丢（ADR 0029「cloud 下注入不是可选」）。None=不上传
        region: str | None = None, # 注入 worker 的 AWS_REGION（组合根已落实成具体字符串，ADR 0016 决策 C）；None＝真无 region、worker fail-loud
        poll_interval_s: float = 0.5,
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
        self._region = region
        # 不存 profile：Fargate 用 task role，注入 profile 名会 ProfileNotFound 盖过 task role（ADR 0016 决策 C 的非对称）。
        self._poll = poll_interval_s

    def run_scope(self, job: Job) -> tuple[FargateWorkerHandle, Iterator[Event]]:
        """起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称 SubprocessEngine.run_scope。"""
        # ① job-in 走 S3（ADR 0024 A3）：整 job 序列化（复用 wire.job_to_line）PutObject，env 只传小指针 JOB_S3_URI。
        job_key = f"{self._job_prefix}{job.scope_id}.json"
        self._s3.put_object(Bucket=self._job_bucket, Key=job_key, Body=(job_to_line(job) + "\n").encode("utf-8"))
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

        handle = FargateWorkerHandle(self._ecs, self._cluster, task_arn)
        return handle, self._read_events(job.scope_id, task_arn)

    def _read_events(self, scope_id: str, task_arn: str) -> Iterator[Event]:
        """Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。

        **天然定向 + 天然幂等**（ADR 0024，DDB 相对 SQS 的核心简化）：Query PK=run_id#scope_id 只返回本 run 本 scope
        的事件（查询即分流、无 dispatcher）；Query 是非破坏性读、last_seq 是本地游标（非删除），重读同一 seq 无副作用（无去重表）。

        **纯事件流、不掺心跳**（Engine port 铁律）：静默时本迭代器阻塞在轮询上，schedule 的 _heartbeat_wrap 兜底唤醒查超时。

        **终止信号**（ADR 0024）：主判 = 读到本 scope 的 scope_done（最大 seq、最后一条）；兜底 = DescribeTasks STOPPED
        （worker 崩溃没发 scope_done）。SQS 长轮询靠空 receive+STOPPED，DDB 靠 Query 空+STOPPED，同构。
        """
        from boto3.dynamodb.conditions import Key

        last_seq = 0
        pk = events_pk(self._run_id, scope_id)
        while True:
            # 增量 Query：本 scope、SK>last_seq、SK 升序（保序）。最终一致读（默认）——流式期漏读无害，下轮补齐。
            resp = self._events.query(
                KeyConditionExpression=Key(_PK_ATTR).eq(pk) & Key(_SK_ATTR).gt(last_seq),
                ScanIndexForward=True,
            )
            items = resp.get("Items", [])
            saw_scope_done = False
            for it in items:
                last_seq = int(it[_SK_ATTR])
                event = event_from_line(it[_BODY_ATTR])
                yield event  # 解析失败抛 ValueError，schedule 记 error（同 subprocess）
                if _is_scope_done(it[_BODY_ATTR]):
                    saw_scope_done = True
            if saw_scope_done:
                break  # 主判：scope_done 是最后一条，正常终止

            # 无新事件（或未见 scope_done）：查 task 是否已 STOPPED（兜底：worker 崩溃没发 scope_done）
            if not items:
                exit_code = self._task_exit_code(task_arn)
                if exit_code is not None:
                    # task 已 STOPPED。终读一次强一致 Query 补末尾（防最终一致还没看到最后几条 PutItem，ADR 0024 读一致性条）。
                    yield from self._final_drain(pk, last_seq)
                    self._raise_for_exit(exit_code)
                    return
                time.sleep(self._poll)  # task 还在跑、暂无新事件 → 等一个轮询周期再拉（延迟 vs 读放大，ADR 0024）

    def _final_drain(self, pk: str, last_seq: int) -> Iterator[Event]:
        """task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。"""
        from boto3.dynamodb.conditions import Key

        resp = self._events.query(
            KeyConditionExpression=Key(_PK_ATTR).eq(pk) & Key(_SK_ATTR).gt(last_seq),
            ScanIndexForward=True,
            ConsistentRead=True,  # 强一致：反映所有在先成功写（2× RRU，成本忽略；防永久漏最后几条）
        )
        for it in resp.get("Items", []):
            yield event_from_line(it[_BODY_ATTR])

    def _task_exit_code(self, task_arn: str) -> int | None:
        """DescribeTasks 查退出码：lastStatus==STOPPED 才有 exitCode（STOPPED 前常 null）。未 STOPPED → None（继续轮询）。"""
        resp = self._ecs.describe_tasks(cluster=self._cluster, tasks=[task_arn])
        tasks = resp.get("tasks", [])
        if not tasks or tasks[0].get("lastStatus") != "STOPPED":
            return None
        containers = tasks[0].get("containers", [])
        # 找本 worker container 的 exitCode；缺省当异常（0 才是正常，见 _raise_for_exit）。
        for c in containers:
            if c.get("name") == self._container:
                return c.get("exitCode", 1) if c.get("exitCode") is not None else 1
        return containers[0].get("exitCode", 1) if containers else 1

    def _raise_for_exit(self, rc: int) -> None:
        """退出码翻异常（复刻 subprocess_engine._read_events:116-127）：80→网络错、>0→RuntimeError、0→正常。"""
        if rc == EX_WORKER_NETWORK:
            raise WorkerNetworkError(f"worker 建连失败（网络/SSL 瞬时故障），退出码 {rc}")
        if rc > 0:
            raise RuntimeError(f"worker 异常退出 exitCode={rc}")


def _is_scope_done(body: str) -> bool:
    """peek 事件 body 的 type 是否 scope_done（终止判据）——只读 type、不重复 event_from_line 的完整解析。"""
    try:
        return json.loads(body).get("type") == "scope_done"
    except (ValueError, AttributeError):
        return False
