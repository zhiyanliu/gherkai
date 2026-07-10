"""iac_aws_backend Stack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。

一套 stack 建齐（可按 prefix 多实例化，多环境 prod-/stage-）：
- DynamoDB：{prefix}runs（控制面/RunStore）+ {prefix}events（events-out，开 expires_at TTL）
- S3：{prefix}artifacts（Result/Report/offload/job-in/artifact-upload，按 prefix key 分片）
- ECS：{prefix}cluster + 2 task-def（novaact/midscene，各自镜像/task role）
- ECR：2 repo（各承一镜像；镜像由 CI build&push，synth 不触发 docker build）
- IAM：每引擎一个 task role（最小权限）+ 共享 execution role
- VPC + SSM：subnet/sg ID 写进 /{prefix}backend/subnets|security-groups（cli 读）

命名走 names.py（与 cli compose 同源，ADR 0033 护栏）。prefix 从 CDK context 读（cdk deploy -c prefix=prod-）。
"""
from __future__ import annotations

from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_logs as logs,
)
from constructs import Construct

import names


class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.prefix = prefix

        vpc = self._network()
        self._storage()          # DDB ×2 + S3 ×1
        self._cluster(vpc)       # {prefix}cluster（RunTask 时 cli 按名指定，task-def 不绑 cluster）
        self._task_definitions()  # 2 引擎：ECR + task-def + task role
        self._ssm_network(vpc)   # 写 subnet/sg ID 供 cli 读

    # ---- DynamoDB ×2 + S3 ×1（ADR 0033 资源清单；schema 与 core/tests/conftest.py fixture 一致）----
    def _storage(self) -> None:
        # runs 表（控制面/RunStore）：PK=run_id(S) / SK=item_type(S，值 META/STATE）。
        dynamodb.Table(
            self, "RunsTable",
            table_name=names.default_name(self.prefix, names.BASE_RUNS_TABLE),
            partition_key=dynamodb.Attribute(name="run_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="item_type", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,  # 保留数据、防误删（stack 销毁不带走表）
        )
        # events 表（events-out）：PK=pk(S，run_id#scope_id) / SK=seq(N)；body 非键属性不声明。
        # 开 TTL：expires_at（worker 写 now+7d epoch 秒，ADR 0033/0024）自动过期旧事件。
        dynamodb.Table(
            self, "EventsTable",
            table_name=names.default_name(self.prefix, names.BASE_EVENTS_TABLE),
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="seq", type=dynamodb.AttributeType.NUMBER),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expires_at",  # DDB TTL（ADR 0033）
            removal_policy=RemovalPolicy.RETAIN,
        )
        # artifacts 桶：Result(jobs/) + Report(index/manifest) + offload(args/) + job-in + artifact-upload，
        # 全按 key 前缀 <report_dir>/<run_id>/ 分片。
        s3.Bucket(
            self, "ArtifactsBucket",
            bucket_name=names.default_name(self.prefix, names.BASE_BUCKET),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # 安全：私有桶
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
        )

    # ---- VPC（Fargate awsvpc 用）：三档 context 可指定（ADR 0033），默认建新 ----
    def _network(self) -> ec2.IVpc:
        # 优先级：-c vpc_id=xxx（用现有 VPC）> -c use_default_vpc=true（用账户默认 VPC）> 建新。
        # 三档都走**公有子网 + assignPublicIp=ENABLED** 出网连 AgentCore/Bedrock/S3/DDB（worker 只出不入），**零 NAT 成本**。
        vpc_id = self.node.try_get_context("vpc_id")
        if vpc_id:
            return ec2.Vpc.from_lookup(self, "BackendVpc", vpc_id=vpc_id)
        if str(self.node.try_get_context("use_default_vpc")).lower() == "true":
            return ec2.Vpc.from_lookup(self, "BackendVpc", is_default=True)
        # 建新：2-AZ、**零 NAT**（nat_gateways=0）。worker 落公有子网 + 公网 IP 出网，与 _ssm_network 的「公有子网优先」
        # 及 cli assignPublicIp=ENABLED 一致——不建常驻计费的 NAT。**真私有子网隔离（NAT/VPC endpoint 出网）留 backlog**：
        # 现三档均公有子网出网，若未来要私有隔离需同步 _ssm_network 选私有子网 + cli assignPublicIp=DISABLED（跨组件联动）。
        return ec2.Vpc(self, "BackendVpc", max_azs=2, nat_gateways=0)

    # ---- ECS cluster ----
    def _cluster(self, vpc: ec2.IVpc) -> ecs.Cluster:
        return ecs.Cluster(
            self, "BackendCluster",
            cluster_name=names.default_name(self.prefix, names.BASE_CLUSTER),
            vpc=vpc,
        )

    # ---- 2 引擎 task-def（ECR + task role 最小权限 + execution role）----
    def _task_definitions(self) -> None:
        # execution role（拉 ECR 镜像 + 写 CloudWatch 日志的平台角色，两引擎共享）——与 task role 职责分开（ADR 0033）。
        execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
            ],
        )
        for engine in names.ENGINES:
            self._one_task_def(engine, execution_role)

    def _one_task_def(self, engine: str, execution_role: iam.Role) -> None:
        # ECR repo（镜像由 CI build&push；synth 不触发 docker build——from_ecr_repository 只引用 repo）。
        repo = ecr.Repository(
            self, f"Ecr{engine.capitalize()}",
            repository_name=names.task_def_name(self.prefix, engine),  # repo 名复用 task-def family 名（同 prefix 心智）
            removal_policy=RemovalPolicy.RETAIN,
        )
        # task role（容器内 worker 凭证）——**最小权限、按引擎分立**（ADR 0033：一个引擎被攻破不波及另一个引擎模型权限）。
        task_role = iam.Role(
            self, f"TaskRole{engine.capitalize()}",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        self._grant_task_role(task_role, engine)

        # Nova 需更大 cpu/memory（playwright+chromium）；Midscene 亦跑 chromium。取 1vCPU/2GB 起步（真跑标定，
        # 属运维配置）。stopTimeout ≤120s（ADR 0024/0032；真容器 grace 校准 defer 0032）。
        task_def = ecs.FargateTaskDefinition(
            self, f"TaskDef{engine.capitalize()}",
            family=names.task_def_name(self.prefix, engine),
            cpu=1024, memory_limit_mib=2048,
            execution_role=execution_role,
            task_role=task_role,
        )
        task_def.add_container(
            names.container_name(engine),  # **container 名 = {engine}-worker（不带 prefix）**——cli RunTask 逐字匹配（ADR 0033 硬契约）
            image=ecs.ContainerImage.from_ecr_repository(repo, tag="latest"),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=engine,
                log_group=logs.LogGroup(
                    self, f"LogGroup{engine.capitalize()}",
                    log_group_name=f"/{self.prefix}worker/{engine}",
                    retention=logs.RetentionDays.TWO_WEEKS,
                    removal_policy=RemovalPolicy.DESTROY,  # 日志组可随 stack 销毁（非数据）
                ),
            ),
            # 不设 AWS_REGION/AWS_PROFILE（ADR 0033 决策 C）：region 每 run 经 RunTask overrides 注入、凭证靠 task role。
            stop_timeout=None,  # 用 task-def 默认；真容器 grace 校准 defer 0032（Nova 180s>120s 冲突）
        )

    def _grant_task_role(self, role: iam.Role, engine: str) -> None:
        """task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。"""
        acct, region = self.account, self.region
        pfx = self.prefix
        events_table = names.default_name(pfx, names.BASE_EVENTS_TABLE)
        bucket = names.default_name(pfx, names.BASE_BUCKET)

        # 两个引擎共享：events 表 PutItem（**只 events 表、不给 runs 表**——worker 绝不碰 RunState，ADR 0024/0030 单写者）
        role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:PutItem"],
            resources=[f"arn:aws:dynamodb:{region}:{acct}:table/{events_table}"],
        ))
        # 两个引擎共享：artifacts 桶 GetObject（job-in）+ PutObject（产物上传）+ AbortMultipartUpload。
        # **不给 DeleteObject**（worker 只 Put，ADR 0029）；但 **AbortMultipartUpload 必给**——Nova/Midscene worker 用
        # boto3/aws-sdk `upload_file`（TransferManager，multipart_threshold 默认 8MB），>8MB 产物（视频/大截图）走
        # 分段上传；某分段失败时 SDK 会调 AbortMultipartUpload 清理已传分段，缺此权限则 abort 报 AccessDenied、残留
        # 未完成分段在桶内持续计费（真跑用 example.com 小产物 <8MB 未触发 multipart，故此动作真跑未暴露——绿≠对）。
        role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject", "s3:AbortMultipartUpload"],
            resources=[f"arn:aws:s3:::{bucket}/*"],
        ))
        # 两个引擎共享：AgentCore 浏览器会话（Start/Stop）+ browser profile（Create/管理会话配置）。
        # CreateBrowserProfile 由真跑暴露（Nova SDK 起会话前 _resolve_or_create_profile 会建 profile）——grep 未及。
        role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock-agentcore:StartBrowserSession", "bedrock-agentcore:StopBrowserSession",
                # profile 解析 = List/Get 找已存在的、没有才 Create（真跑暴露：缺 List 会误走 Create → 已存在则 ConflictException）
                "bedrock-agentcore:ListBrowserProfiles", "bedrock-agentcore:GetBrowserProfile",
                "bedrock-agentcore:CreateBrowserProfile",
                # 连 CDP 自动化流的数据面权限（真跑暴露：connect_over_cdp 到 browser-streams WebSocket 403 Forbidden——
                # 控制面 Start/StopSession 之外还需数据面 stream 连接权限）。
                "bedrock-agentcore:ConnectBrowserAutomationStream",
                "bedrock-agentcore:ConnectBrowserLiveViewStream",
            ],
            resources=["*"],  # AgentCore browser/profile 资源 ARN 形态待真跑标定，先 *（属可收窄的运维加固项）
        ))
        # 各引擎特有模型权限
        if engine == "novaact":
            # Nova：nova-act workflow definition + run 生命周期（Create/Update）+ 模型推理。
            # UpdateWorkflowRun 由真跑暴露（Workflow __exit__ 更新 run 状态）——grep 未及。
            role.add_to_policy(iam.PolicyStatement(
                actions=[
                    "nova-act:GetWorkflowDefinition", "nova-act:CreateWorkflowDefinition",
                    "nova-act:CreateWorkflowRun", "nova-act:UpdateWorkflowRun",
                    "nova-act:CreateSession",  # 起 AgentCore 会话（真跑暴露；SDK NovaAct.start → CreateSession）
                    # AI act 生命周期（真跑 AI step 逐个暴露；确定性用例不触发）：Create→Update→Get→InvokeActStep（判定核心调用）。
                    "nova-act:CreateAct", "nova-act:UpdateAct", "nova-act:GetAct", "nova-act:InvokeActStep",
                ],
                resources=["*"],  # workflow definition ARN 形态待标定
            ))
            # AgentCore 保存会话 profile（真跑暴露：Nova 会话结束想存 profile 优化下次；缺它只 WARNING、非致命，
            # 但最小权限该有）。与上面 profile List/Get/Create 同族（profile 生命周期完整）。
            role.add_to_policy(iam.PolicyStatement(
                actions=["bedrock-agentcore:SaveBrowserSessionProfile"],
                resources=["*"],
            ))
        elif engine == "midscene":
            # Midscene：Bedrock InvokeModel（Qwen3-VL）
            role.add_to_policy(iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],  # 模型 ARN 待标定（qwen.qwen3-vl-235b-a22b）
            ))

    # ---- SSM：subnet/sg ID 写进含 prefix 路径（cli resolve_network 读，ADR 0033）----
    def _ssm_network(self, vpc: ec2.IVpc) -> None:
        # 优先公有子网（assignPublicIp=ENABLED 出网、零 NAT）；无公有则回落私有（需 NAT/VPC endpoint 出网）。
        # cli FargateEngine 的 assignPublicIp="ENABLED" 与公有子网配套（worker 只出不入连 AgentCore/Bedrock/S3/DDB）。
        subnets = vpc.public_subnets or vpc.private_subnets
        subnet_ids = [s.subnet_id for s in subnets]
        # Fargate 用的默认安全组（出站全开、入站无——worker 只出不入）。
        sg = ec2.SecurityGroup(
            self, "WorkerSg", vpc=vpc,
            description=f"{self.prefix}fargate worker sg (egress only)",
            allow_all_outbound=True,
        )
        ssm.StringListParameter(
            self, "SsmSubnets",
            parameter_name=names.ssm_subnets_path(self.prefix),
            string_list_value=subnet_ids,
        )
        ssm.StringListParameter(
            self, "SsmSecurityGroups",
            parameter_name=names.ssm_security_groups_path(self.prefix),
            string_list_value=[sg.security_group_id],
        )
        # 诊断输出（cdk deploy 后打印，便于人工核对 cli --prefix 一致）
        CfnOutput(self, "Prefix", value=self.prefix)
        CfnOutput(self, "SubnetsSsmPath", value=names.ssm_subnets_path(self.prefix))
