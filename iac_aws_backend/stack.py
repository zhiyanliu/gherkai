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
    Duration,
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
    # Fargate 平台对 container stopTimeout 的硬上限（SIGTERM→SIGKILL 宽限）。ECS 部署期会拒 >120s（对 EC2 launch
    # type 无此限、对 Fargate 有）；此常量供 synth 期 fail-fast，别等 deploy 才炸（Nova grace 下限 150s>120s 冲突的根源，见 ADR 0032）。
    FARGATE_STOP_TIMEOUT_MAX_S = 120
    DEFAULT_STOP_TIMEOUT_S = 120  # 默认贴 Fargate 上限：尽量给 worker 会话释放+抢传预算（grace 真容器校准见 ADR 0032），可 -c stop_timeout= 覆盖

    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.prefix = prefix
        self.stop_timeout_s = self._resolve_stop_timeout()

        vpc = self._network()
        self._storage()          # DDB ×2 + S3 ×1
        self._cluster(vpc)       # {prefix}cluster（RunTask 时 cli 按名指定，task-def 不绑 cluster）
        self._task_definitions()  # 2 引擎：ECR + task-def + task role
        self._ssm_network(vpc)   # 写 subnet/sg ID 供 cli 读

    # ---- stopTimeout 解析（grace 真容器校准落点，ADR 0032）----
    def _resolve_stop_timeout(self) -> int:
        """container stopTimeout（秒）：`-c stop_timeout=N` 覆盖，默认 120s。

        grace 真容器校准的**唯一落点**（`FargateWorkerHandle.stop` 忽略运行期 grace 参数，真实宽限由 task-def
        期这个常量决定，见 ADR 0024/0032）。做成 context 可配是为迭代试不同 grace 值免改 code。
        **synth 期 fail-fast**：Fargate 硬上限 120s，>120 部署期必被 ECS 拒——早报错、点明是 Fargate 限制而非笔误。
        （Nova grace 下限 150s>120s 的冲突正卡在这条硬上限上，解法见 ADR 0032 grace 预算条。）
        """
        raw = self.node.try_get_context("stop_timeout")
        if raw is None:
            return self.DEFAULT_STOP_TIMEOUT_S
        # 显式收紧类型再转：CLI `-c stop_timeout=` 恒给 str，但 cdk.json / 编程式 context 可给原生 bool/float——
        # 直接 int(raw) 会静默把 True→1、90.5→90（bool 是 int 子类、float 截断），绕过「须为整数秒」意图。故先经
        # str() 归一：str(True)='True' / str(90.5)='90.5' 都会让 int() 抛 ValueError，与 CLI str 路径行为一致。
        try:
            seconds = int(str(raw))
        except (TypeError, ValueError):
            raise ValueError(f"stop_timeout context 须为整数秒，得到 {raw!r}")
        if not 1 <= seconds <= self.FARGATE_STOP_TIMEOUT_MAX_S:
            raise ValueError(
                f"stop_timeout={seconds}s 越界：Fargate 要求 1..{self.FARGATE_STOP_TIMEOUT_MAX_S}s"
                f"（>120s 部署期会被 ECS 拒；这正是 Nova grace 下限>120s 冲突的硬上限，见 ADR 0032）"
            )
        return seconds

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
            # job-in 对象生命周期（ADR 0033）：FargateEngine 写的 job-in 是喂 worker 的一次性输入（读完即无用），
            # 无清理会随 run 堆积。**按对象 tag `gherkai=job-in` 过期、非 key 前缀**——job-in 落 `<prefix><run_id>/jobs-in/`
            # （run_id 在中间），lifecycle 纯前缀 filter 框不住、且会误伤同前缀下的判定真值(jobs/)/报告；tag 精确只框 job-in。
            # 7 天：对齐 events 表 TTL 心智（协调/输入类脚手架，留窗口供事后调查失败 run，之后自动清）。判定真值(jobs/)、
            # 报告(reports/)不打此 tag、不受影响（长期保留，误删代价高，同 RETAIN 精神）。
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="expire-job-in",
                    enabled=True,
                    tag_filters={"gherkai": "job-in"},
                    expiration=Duration.days(7),
                ),
            ],
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
        # 属运维配置）。stopTimeout（SIGTERM→SIGKILL 宽限）= self.stop_timeout_s（默认 120s、-c stop_timeout= 覆盖，
        # Fargate ≤120s 硬上限——grace 真容器校准见 _resolve_stop_timeout / ADR 0032）。
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
            stop_timeout=Duration.seconds(self.stop_timeout_s),  # grace 真容器校准（ADR 0032），默认 120s、-c stop_timeout= 覆盖（见 _resolve_stop_timeout）
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
        # 两个引擎共享：AgentCore 浏览器会话（Start/Stop）+ browser profile。资源 ARN 已按 SAR resource_types
        # 收窄（ADR 0033；SAR + IAM 策略模拟器对本账户实证）——拆两条 statement：
        # 系统默认 browser（aws.browser.v1，非自建 custom，ADR 0011）的 ARN **account 段是字面量 `aws`**（非客户账户！
        # 官方人读文档误写成 <account_id>，实测 get-browser 返回 aws、模拟器验证填客户账户会 implicitDeny——copy-account 陷阱）。
        # browser-profile 是客户自建资源（account=客户账户，profileId 运行期生成 → * 通配）。
        _sys_browser = f"arn:aws:bedrock-agentcore:{region}:aws:browser/aws.browser.v1"
        _browser_profiles = f"arn:aws:bedrock-agentcore:{region}:{acct}:browser-profile/*"
        role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock-agentcore:StartBrowserSession",  # 触及 browser + profile
                "bedrock-agentcore:StopBrowserSession",   # 只触及 browser（SAR 无 profile 资源类型）
                "bedrock-agentcore:GetBrowserProfile",    # 只触及 profile
            ],
            resources=[_sys_browser, _browser_profiles],
        ))
        # 以下 4 个动作 SAR resource_types 为空、不支持 resource-level（模拟器实证：scope 到任何具体 ARN 均 implicitDeny，
        # 只在 Resource:"*" 下才授权），诚实保留 *（非"待标定"，是**结构上只能** *）：
        # - List/CreateBrowserProfile：控制面 List 枚举 / Write create（资源尚不存在，无 ARN 可 scope）。
        #   List 真跑暴露（缺它误走 Create→已存在则 ConflictException）；Create 真跑暴露（SDK _resolve_or_create_profile）。
        # - Connect{Automation,LiveView}Stream：数据面 CDP/live-view 流连接（无资源实体、无 data-event CloudTrail）。
        #   真跑暴露（connect_over_cdp 到 browser-streams WebSocket 403 Forbidden 定位）。
        role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock-agentcore:ListBrowserProfiles",
                "bedrock-agentcore:CreateBrowserProfile",
                "bedrock-agentcore:ConnectBrowserAutomationStream",
                "bedrock-agentcore:ConnectBrowserLiveViewStream",
            ],
            resources=["*"],  # SAR resource_types 为空——结构上不支持 resource-level（非可收窄项）
        ))
        # 各引擎特有模型权限
        if engine == "novaact":
            # Nova：nova-act workflow definition + run 生命周期 + 会话/act。资源 ARN 已收窄（ADR 0033；AWS Service
            # Reference v1.4 权威列 resource_types）——nova-act 只有 workflow-definition / workflow-run 两个 IAM 资源类型，
            # session/act 非独立资源（IAM 鉴权只到 workflow-run 层）。
            # **definition 名段用 `*`（不 pin 具体名）**：definition 名（worker create-if-not-exists 的那个）是 worker
            # 运行期概念、住在 worker code（engines/novaact/lib/constants.py），**不该泄进 IAM 层让 IaC 跨工程耦合它**。
            # 用「锁死 service+account+region、放开 definition 名段」换掉耦合——仍远窄于全 *（只该账户/region 的 nova-act
            # workflow-definition 资源）。两条 ARN 覆盖全部动作：① definition 层（Get/Create/CreateWorkflowRun 只认父）；
            # ② run 通配（Update{WorkflowRun}/CreateSession/Create/UpdateAct/InvokeActStep，runId 亦运行期变量）。
            _wf = f"arn:aws:nova-act:{region}:{acct}:workflow-definition"
            role.add_to_policy(iam.PolicyStatement(
                actions=[
                    "nova-act:GetWorkflowDefinition", "nova-act:CreateWorkflowDefinition",
                    "nova-act:CreateWorkflowRun", "nova-act:UpdateWorkflowRun",
                    "nova-act:CreateSession",  # 起 AgentCore 会话（真跑暴露；SDK NovaAct.start → CreateSession）
                    # AI act 生命周期（真跑 AI step 逐个暴露；确定性用例不触发）。**删 GetAct**——AWS Service Reference
                    # v1.4 全动作集无 GetAct（此前误授一个不存在的 action，非资源维度问题）；实调是 Create→Update→InvokeActStep。
                    "nova-act:CreateAct", "nova-act:UpdateAct", "nova-act:InvokeActStep",
                ],
                resources=[f"{_wf}/*", f"{_wf}/*/workflow-run/*"],
            ))
            # AgentCore 保存会话 profile（真跑暴露：Nova 会话结束想存 profile 优化下次；缺它只 WARNING、非致命，
            # 但最小权限该有）。SAR resource_types = browser + browser-profile：触及来源系统 browser（account=aws）+ 目标 profile。
            role.add_to_policy(iam.PolicyStatement(
                actions=["bedrock-agentcore:SaveBrowserSessionProfile"],
                resources=[_sys_browser, _browser_profiles],
            ))
        elif engine == "midscene":
            # Midscene：Bedrock InvokeModel（Qwen3-VL）。收窄到该 foundation-model 单一 ARN（ADR 0033；文档格式 +
            # CloudTrail 样本 + code 实际 modelId 三方对上）。foundation-model ARN 的 **account 段为空**（AWS 惯例）；
            # region 段用 `*`——region 是 code 可配运行期变量（AWS_REGION 注入，ADR 0016 决策 C），model-id 才是稳定段，
            # 故 pin model-id、通配 region（无跨区 inference profile：裸 modelId 直连 ON_DEMAND，该模型不支持 profile）。
            role.add_to_policy(iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[f"arn:aws:bedrock:*::foundation-model/{names.QWEN_MODEL_ID}"],
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
