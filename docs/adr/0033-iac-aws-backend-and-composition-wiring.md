# iac_aws_backend：`--backend cloud` 的 AWS 资源 IaC（Python CDK）+ 组合根接 FargateEngine

> **Status:** Partially-superseded-by 0037/0038 —— 组合根接线（`build_fargate_engines` + `--backend cloud` 切执行）与 **CDK 工程本体（`iac_aws_backend/`）均已编码 + 真部署真跑验证**（两个引擎 ×（确定性+AI）跑通、产出物三处核对）。本 ADR 定 **IaC 工程定位/资源清单/命名契约/preflight** 与 **组合根把 `FargateEngine` 接进 `--backend cloud`** 的稳定决策。执行环境特有的中断/grace 韧性见 [0032](./0032-fargate-execution-environment.md)（Accepted，grace/stopTimeout + 中断韧性已真容器标定）；region/profile 贯通见 [0016](./0016-execution-architecture-core-lib-run-model.md) 决策 C；events-out/job-in 传输见 [0024](./0024-worker-core-protocol.md)；产物→S3 见 [0029](./0029-engine-artifacts-to-s3.md)。**被 [0037](./0037-distribution-and-packaging.md) 与 [0038](./0038-worker-image-delivery.md) 取代的部分（两者独立翻牌，状态各标）**——0037（Draft，决策已对齐、未实装）：`iac_aws_backend/` 独立工程 + 裸 `cdk deploy` → 包化进 `gherkai-deploy-aws`、经 `gherkai deploy` 执行（`prefix`/`vpc_id`/`use_default_vpc`/`stop_timeout` 四个 context 旋钮升为三个一等 flag，下「VPC 来源：三档」能力不减，但取消「默认建新」的隐式默认——`--vpc` 必给，本 ADR 正文三处「默认建新」（资源清单条、VPC 节标题与其「为何默认建新」句）在 0037 实装后失效，「默认建新对增量 deploy 是陷阱」的踩坑记述仍成立——另加 SSM 档三态比对）；Lambda asset 现场 copytree 仓库相对路径 + 联网装 gherkin → 从已安装包复制；下「留待」节 CI 条闭环；SSM 参数族加 `version`/`vpc`。0038（Draft，决策已对齐、未实装）：task-def 焊死 `tag="latest"` 且 RunTask 传 family → 每（引擎，variant）一个按 digest 引用的 revision、RunTask 传显式 revision；「必须 `--platform linux/amd64`」陷阱保留但 push-worker 推送前校验架构、提前 fail-loud；`tools/build_push_workers.py` → `gherkai deploy push-worker`；镜像交付改「维护者 GHCR 基底 + 使用方按 variant 推送的定制层」；runs 表 STATE 顶层加 `worker_task_def_arns` + 按 `status` 的稀疏 GSI、推进器 env 加模板 revision ARN；SSM 参数族加 `worker-template/*`、`worker-image/*`、`worker-default`；「资源清单」末段的编排机器权限清单按 0038「权限面增量」更新。资源清单/命名契约/container 名契约不动；preflight 加版本 skew 与 variant 解析两项。**本 ADR 正文仍描述当前实装态**，待两者实装后校准。

## 定位：一个 CDK 工程建齐「`--backend cloud` 需要的全部 AWS 资源」

`--backend cloud` 按 [0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A = **存储上云（DDB/S3）+ Fargate 执行**（单旋钮）。这两半的 AWS 资源此前一律「假定已存在、建表归 IaC」（[0030](./0030-realtime-persistence-seam.md) 决定六：adapter 不持 schema/建表权知识），生产侧从无建表建桶代码——只在 moto 单测 fixture（`core/tests/conftest.py`）里程序化建出。**本 ADR 决定把这些 fixture 里的建表建桶动作固化成真 CDK。**

**决策：新建顶层工程 `iac_aws_backend/`（Python CDK），与 `core/`/`cli/`/`engines/` 平级。**

- **命名**：`iac_` 前缀对齐「工程」定位；`aws_backend` 精确覆盖它建的东西 = 「`--backend cloud` 这个 backend 所需的 aws 资源」——含**存储**（DDB/S3）**与执行**（Fargate/ECR），不窄化成只有存储。（与决策 A「backend=存储+执行单旋钮」呼应。）
- **语言 = Python CDK**（aws-cdk-lib）。理由：与 core/cli 同语言（团队心智一致、CI 复用 uv 工具链）；不引入第二语言/Terraform HCL。
- **统一一个工程建齐、不拆散**：存储资源（含现在已有 adapter 的 RunStore 表 / S3 桶）也**收编进本 IaC**——此前它们「假定已存在」是收编前的遗留态，本 ADR 让「`--backend cloud` 的每一个 AWS 依赖」都有 IaC 出处、单一部署入口。

## 资源清单（CDK 建什么）

一套 CDK stack（可按 prefix 多实例化，见「两层命名」）建：

**DynamoDB（2 张表，均 `PAY_PER_REQUEST`；schema 权威源 = `core/tests/conftest.py` fixture，CDK 照抄）：**
1. `{prefix}runs`（控制面 / RunStore，已有 adapter，本 ADR 纳入统一 IaC）：PK=`run_id`(S)、SK=`item_type`(S，值 `META`/`STATE`）。
2. `{prefix}events`（events-out，本 ADR 新增）：PK=`pk`(S，值 `run_id#scope_id`)、SK=`seq`(N)；非键属性 `body`(S) 不进 AttributeDefinitions。**独立于 runs 表、绝不合表**（[0024](./0024-worker-core-protocol.md)：两种访问模式——runs 点读/单元素刷、events 大量追加+范围 Query；合表会踩 run_id 热分区、破 [0030](./0030-realtime-persistence-seam.md) 单写者不变量）。

**S3（1 个桶）：**
3. `{prefix}artifacts`：承 RunStore-offload（DDB 400KB 溢出，`args/`）+ ResultStore（判定真值，`jobs/<quote(scope_id)>.json`）+ ReportStore（`index/manifest`）+ **job-in（`jobs-in/<quote(scope_id)>.json`——独立前缀、非 `jobs/`）** + artifact-upload（trajectory/report/log），全部按 key 前缀 `<report_dir>/<run_id>/` 分片。（job 桶与 artifact 桶合一，权限按 prefix 分组。）**job-in 用 `jobs-in/` 而非 `jobs/`**（真跑暴露）：ResultStore 判定真值占 `jobs/` 且 `load_all` 用 `list jobs/ + unquote basename` 枚举，job-in 与 ResultStore 的 scope_id `quote` 编码相同、共用 `jobs/` 会撞 key（互相覆盖）+ 被 `load_all` 误读；故 job-in 独立前缀。scope_id 一律 `quote(safe='')`（`/`→`%2F`、`:`→`%3A`），不造 S3 假子前缀。

**ECS / Fargate：**
4. ECS cluster `{prefix}cluster`。
5. **每引擎一个 task definition + 一个容器镜像（2 个，见「2 镜像」节）**：task-def family = `{prefix}{engine}-worker`（`engine`=引擎规范名 `novaact`/`midscene`，即 `{prefix}novaact-worker` / `{prefix}midscene-worker`——须与 cli `compose.task_def_name` 逐字一致）。Fargate 兼容、`networkMode=awsvpc`。**`stopTimeout` 显式设为 120s（`stack._resolve_stop_timeout`，贴 Fargate ≤120s 平台上限）、可经 CDK context `-c stop_timeout=N` 覆盖**（synth 期对非整数/越界 `[1,120]` fail-fast）——做成可配是为 grace 真容器标定期迭代试不同值免改 code。**grace 预算解法归 [0032](./0032-fargate-execution-environment.md)、已真容器标定**（曾担心 Nova grace 下限 > 120s 硬上限的冲突，0032 结论 4 实测厘清：subprocess 侧压 margin 60→30 后下限 150 满足不变量、Fargate 侧对最坏长 act 结构性接受 SIGKILL+TTL 兜底；`ACT_TIMEOUT_S` 不动），**不是 stopTimeout 是否设值**（`FargateWorkerHandle.stop` 忽略运行期 grace 只发 StopTask，真实宽限由此 task-def 期 `stopTimeout` 决定）。**task-def 内 container 元素名 = `{engine}-worker`（不带 prefix，见下「container 名约定」）**。**task-def 不设 `AWS_REGION`/`AWS_PROFILE`**（见「task-def 不焊 region/凭证」）。
6. ECR 仓库（2 个，各承一镜像）。
7. VPC 网络：subnet(s) + security group(s)（`awsvpcConfiguration` 用；ID 走 SSM，见「subnet/sg 走 SSM」）。**VPC 来源三档可指定**（CDK context，见下「VPC 来源」）——默认建新，但支持复用现有/默认 VPC 避 NAT 成本。

**IAM：**
8. **task role**（容器内凭证链 `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` 解析目标）——**最小权限**（见「IAM 最小权限」）。
9. **task execution role**（拉 ECR 镜像 / 写 CloudWatch 日志的标准 Fargate execution role）。
10. **3 个 Lambda 执行角色**（随 12. 的各 Function 自动建、**与 task role/execution role 分立**）：exit-observer 只需 events 表写（`PutItem` 写 `task_exited`）+ **runs 表读**（写前判 run 是否 detached，见 13.）；reconciler / kicker 同款——起 worker task（`ecs:RunTask` 按引擎 task-def ARN + `iam:PassRole` 到 execution role 与各 task role）+ `ecs:DescribeTasks`/`StopTask`/`ListTasks`（退出码兜底、超时处置定位与停）+ runs 表读写 + events 表读 + 桶读写 + `scheduler:CreateSchedule`/`DeleteSchedule`（资源域见 15.）。**起 task 的能力集中在这三个角色上**，故 submit/status 机器无需任何 ECS 写/执行权限（[0034](./0034-detached-batch-reconciler.md) 最小权限卖点）。

**SSM：**
11. subnet/sg 的 ID 写进确定性路径的 SSM 参数（cli 读，见「subnet/sg 走 SSM」）。

**无状态跑批的事件驱动链（[0034](./0034-detached-batch-reconciler.md) 引入；机制/为什么归 0034，此处只列资源、命名与触发契约）：**
12. **3 个 Lambda Function**（同一份 code asset：`lambdas/` + `core/gherkai_core` + `runtime/gherkai_runtime`，pip 装 gherkin-official；boto3 用 runtime 自带）——`{prefix}kicker`（handler `reconciler.kicker_handler`）/ `{prefix}reconciler`（`reconciler.handler`）/ `{prefix}exit-observer`（`exit_observer.handler`）。名走 prefix 层默认名（基名 `kicker`/`reconciler`/`exit-observer` 在 `runtime/gherkai_runtime/names.py`），**cli 侧按同一 prefix 拼出同名**去 preflight 探活、`status --wait` 据此 invoke kicker → 与 task-def 同款「单一命名事实源、不漂移」。
13. **两表 DynamoDB Stream（`NEW_IMAGE`）+ 两个 event source mapping**：events 表 Stream → reconciler；runs 表 Stream → kicker，且**mapping 带 filter `eventName=INSERT ∧ NewImage.detached.BOOL=true`**（同步 `run --backend cloud` 的 create_run 同样 INSERT runs 表，靠 `detached` 标记在 Stream 层滤掉、零 Lambda 调用；标记由 submit 组合根写在 STATE item 上）。这两条触发关系（含 kicker 的 filter）与 container 名同属 CDK↔code 硬契约：filter 写漏 = 同步 run 被双开推进器。**events 表 Stream 这一条滤不了、只能在 handler 里判**：events item 上没有 `detached` 标记（标记只在 runs 表 STATE item 上），且同步 `run --backend cloud` 与 detached 共用同一张 events 表 —— 故 reconciler（与同 cluster 触发的 exit-observer，见 14.）在动手前自己查 run 是否 detached、非 detached 即 no-op（分流机制与不变量见 [0034](./0034-detached-batch-reconciler.md) 端到端 cloud 1b）。
14. **EventBridge rule `{prefix}ecs-stopped`** → exit-observer：本 cluster 的 `ECS Task State Change` ∧ `lastStatus=STOPPED`（event pattern 按 clusterArn 过滤，不误触账户里别的 ECS 负载）。
15. **job timeout 到点触发器的两件配套**（[0034](./0034-detached-batch-reconciler.md)「job timeout」节）：Scheduler 执行 role `{prefix}timeout-scheduler`（`scheduler.amazonaws.com` assume、只授 invoke kicker；用**确定性 kicker ARN 字符串**授权以避免 role↔function 互引成环）+ one-time schedule 的名字空间 `schedule/default/{prefix}job-timeout-*`（Lambda 的 Create/DeleteSchedule 资源域；schedule 本身运行期由推进器建、`ActionAfterCompletion=DELETE` 自动清，**非 CDK 建**）。名字空间前缀走 prefix 层默认名（基名 `job-timeout` 在 `runtime/gherkai_runtime/names.py`，`job_timeout_schedule_prefix()` 纯函数）——**IaC 的 IAM 资源域与推进器的建名同源推导**，同 Lambda 名那款「单一命名事实源」：单侧硬编码改名 → CreateSchedule 撞资源域 AccessDenied，而 arm 是 best-effort（只打日志），job timeout 会静默降级成只剩 tick 防御扫、纯静默 job 彻底失去超时保护。

**（编排进程角色**——跑 core/cli 的机器需：**同步 `run`**（进程内推进、直接起 task）`ecs:RunTask`/`StopTask`/`DescribeTasks` + `dynamodb:Query`/`PutItem` + store 读写 + `s3:PutObject`（job 上传）；**preflight 只读探活**（任何 `--backend cloud`）`dynamodb:DescribeTable` / `s3:HeadBucket` / `ecs:DescribeClusters` / `ecs:DescribeTaskDefinition`，detached `submit` 另需 `lambda:GetFunction`（探链上三 Lambda 存在性）；**`status --wait` 接力 kickoff** `lambda:InvokeFunction`（`{prefix}kicker`）；**读 subnet/sg** `ssm:GetParameter`（`/{prefix}backend/*`）。**detached `submit`/`status` 的机器只需「runs 表读写 + 上述只读探活 + `InvokeFunction`」、无任何 ECS 写/执行权限**（起 task 全走 Lambda 执行角色，见 10.——[0034](./0034-detached-batch-reconciler.md) 最小权限卖点）。若编排也在 AWS 上跑则一并建；本地跑则用本地凭证，不在本 stack 强制。）

**`RemovalPolicy.RETAIN` = 表/桶/ECR（防误删），其余随 stack 销毁**：2 张 DDB 表 + artifacts 桶设 `RETAIN`（承载 run 数据/产物，误删代价高）；**ECR repo 也设 `RETAIN`**（保住已 push 的镜像，且非空 repo `cdk destroy` 本就删不掉）。可随 stack 销毁的（cluster/task-def/SSM/日志组）用默认/`DESTROY`。**代价（运维须知）**：`cdk destroy` 后表/桶/ECR **残留、需手动删**（`aws dynamodb delete-table` / `aws s3 rb --force` / `aws ecr delete-repository --force`）；否则同 prefix 重新 deploy 会因资源已存在而处理为导入/冲突。清理 runbook 见 `iac_aws_backend/README`。

## 两层命名：`--prefix` 批量默认 + 单资源覆盖（正交、无特判）

**问题**：一个 AWS 账户下可能有**多套**环境（prod/stage）；逐个资源改名不可维护。

**决策：两层命名，正交组合。**

- **prefix 层**（`--prefix`，默认 `gherkai-`）：批量决定**所有名字类资源**的默认名——`{prefix}runs`/`{prefix}events`/`{prefix}artifacts`/`{prefix}cluster`/`{prefix}novaact-worker`/`{prefix}midscene-worker`/`{prefix}kicker`/`{prefix}reconciler`/`{prefix}exit-observer` 等（task-def 用引擎规范名 `novaact`，非 `nova`；三个 Lambda 名 cli 侧 preflight/接力也按此拼，见「资源清单」12.）。**CDK 部署吃同一 prefix**（`cdk deploy -c prefix=prod-`），故 CDK 建的名 = cli 推导的默认名 → **单一事实源、不漂移**。`--prefix prod-` 一键切整套。**命名真源的落位演进**：曾因「CDK 独立工程、不能 import `gherkai_cli`」在 `iac_aws_backend/names.py` **复刻**一份命名函数（双写、靠对拍测试防漂移）；组合根共享层抽为平级包（今 `runtime/gherkai_runtime`）后（[0016](./0016-execution-architecture-core-lib-run-model.md)「演进」节），命名纯函数移入零依赖的 `runtime/gherkai_runtime/names.py`，iac 直接 import（其 `pyproject.toml` 依赖 `gherkai-runtime`，path 源 `../runtime`）——复刻消除、护栏测试转为「真同源」的结构性保证。
- **单资源覆盖层**（`--ddb-table`/`--s3-bucket`/… 给完整终值）：直接用给定值。

**关键自洽点（无特判逻辑）**：覆盖时 prefix **自然不参与**——因为 prefix 只在「生成默认名」这条路径上拼，而覆盖 = 直接给完整 family name = 根本不走生成路径。两层在不同代码路径、正交解耦，不需要 `if override: strip_prefix` 之类的特判。

**护栏（双层方案的固有耦合点，必记）：**
- **CDK↔cli prefix 必须一致**：prefix 是 CDK 与 cli 的**共享约定**。若 `cdk deploy -c prefix=prod-` 但 cli 跑时用默认 `gherkai-`，cli 会拼出 `gherkai-events` 去连——那张表不存在。这不是缺陷，是双层方案的固有耦合；靠 preflight（见下）在启动时探出并**报错点名 prefix**，不静默跑到一半炸。
- **prefix 含分隔符、原样拼**：默认 `gherkai-` 自带连字符 → 名 `gherkai-runs`。用户给 `--prefix prod`（无连字符）会拼成 `prodruns`——**分隔符由用户负责**（对齐 [0016](./0016-execution-architecture-core-lib-run-model.md) S3 prefix 的粘连 key 先例：组合根不猜、不补，原样拼、文档写明）。
- **被拒方案：把 prefix 写进 SSM 让 cli「发现」**——否决。prefix 是 cli 定位资源的**钥匙**，不能又是它要去发现的输出：SSM 路径固定则多环境互相覆盖，路径含 prefix 则「要先知道 prefix 才能读 prefix」= 循环依赖。多环境的区分标识（prod/stage）本身就是 prefix，没有「先于 prefix」的东西定位它。故 prefix 只能是**输入**（`--prefix` / 默认）。

## VPC 来源：三档 context 可指定（默认建新，均公有子网出网、零 NAT）

Fargate awsvpc 模式要 VPC 的 subnet/sg。**VPC 从哪来是部署决策、不焊死**——三档（CDK context 优先级）：

- **复用现有**（`-c vpc_id=vpc-xxx`）：`Vpc.from_lookup(vpc_id=…)`——用账户已有 VPC。
- **用默认 VPC**（`-c use_default_vpc=true`）：`Vpc.from_lookup(is_default=True)`——账户 default VPC。
- **建新**（都不给，默认）：`Vpc(max_azs=2, nat_gateways=0)`——全新 VPC，**零 NAT**。

**三档统一走公有子网 + `assignPublicIp=ENABLED` 出网、零 NAT 成本**：worker **只出不入**（连 AgentCore/Bedrock/S3/DDB），公有子网 + 公网 IP 即够、无需 NAT Gateway（常驻计费 ~$32/月）。subnet 选取「优先 VPC 的公有子网、无则回落私有」**只有一处落点**（`BackendStack._worker_subnet_ids`）：三个消费者最终都喂同一个 `awsvpcConfiguration`——SSM `/{prefix}backend/subnets`（cli 读）+ reconciler / kicker Lambda 的 `SUBNETS` env（这两个起 worker task），故不各处内联（曾三份复刻；单侧改动 = cli 与 Lambda 起的 task 落进不同子网，且只在 RunTask 时才暴露，合成测试比对三者恒等作护栏）。`assignPublicIp` 由 cli `resolve_network` 默认 `ENABLED`，与公有子网配套。**为何默认建新而非默认复用**：建新自包含、无外部假设（不依赖账户已有 VPC 的存在/形态），且零 NAT 后无常驻成本代价。**「默认建新」对增量 deploy 是陷阱（实测踩过）**：CDK context 不进 stack state，后续每次 `diff`/`deploy` 都必须重带与首次部署相同的 vpc context——对以 `use_default_vpc=true`（或 `vpc_id`）档部署的环境漏给该 context，CDK 即按默认档合成「新建整套 VPC + WorkerSg 换 VpcId（replacement）」的变更集；护栏 = deploy 前先 `cdk diff`（带同一组 context），见到 VPC 级资源出现在 diff 里即停下查 context（iac README 的 deploy 段有同一警告）。

- **cli 读 SSM 空值 fail-fast（低频加固）**：`compose._read_ssm_list` 读到空列表（SSM 参数值空串 / 纯逗号，`split(",")` 过滤后 `[]`）时**就地报错、点名是哪个 SSM 路径空了**，不把空 subnet/sg 列表传到 `awsvpcConfiguration` 拖到 **RunTask 才炸**（那时错误不直观）。正常路径 CDK 一定写非空（subnet 取 `vpc.public_subnets or private_subnets`、sg 写默认 SG id），空值**几乎不可达**——只可能来自配置异常（参数被改空）；这条把不可达但代价高的静默失败挡在源头，与「preflight fail-fast 点名 prefix」同风格。

- **被拒（曾经的建新档）：`nat_gateways=1` + 私有子网出网**——曾想让建新档做「私有子网隔离」，但 `_worker_subnet_ids` 恒优先公有子网、cli `assignPublicIp` 恒 ENABLED，NAT 会被建却从不承载 worker 流量（空转计费 + 隔离承诺落空）。故建新档也走公有子网、零 NAT。**真私有隔离留 backlog**：需同步 `_worker_subnet_ids` 选私有子网 + cli `assignPublicIp=DISABLED`（跨组件联动），届时再作第四档或改建新档语义。

## subnet/sg 走 SSM（AWS 生成 ID，无字面默认）

subnet/sg 不是「名字」，是 **AWS 建 VPC 时生成的 ID**（`subnet-0abc…`/`sg-0def…`）——不可预测、无法写字面默认，是两层命名方案唯一套不上的资源。

**决策：CDK 把生成的 subnet/sg ID 写进含 prefix 的 SSM 参数路径（如 `/{prefix}backend/subnets`、`/{prefix}backend/security-groups`）；cli 的 `--subnet`/`--security-group` 未显式给时读该 SSM 路径，给了则用字面值覆盖。**

- **无循环**（与 prefix 不同）：读 SSM 的时机，prefix **已在手**（cli 已从 `--prefix`/默认解析出）→ 用它拼 SSM 路径去读 subnet/sg，正常的「IaC 输出 → 运行时读」模式。
- 这是标准 AWS 「IaC 产出、运行时消费」模式。代价：组合根需 `ssm:GetParameter`（只读、低风险 IAM）+ 一次 boto 调用（仅未显式给 subnet/sg 时触发）。
- 覆盖仍可给字面 ID（对称单资源覆盖层）。

## preflight fail-fast：用已解析 prefix 探全部资源存在性，错误点名 prefix

**目标**：别跑到一半才因「表/桶/cluster 不存在」炸；启动即探、报错要能指向 prefix 配错/CDK 没部署。

**决策：扩展现有 preflight**（`cli/gherkai_cli/__main__.py` 的 `persistence.begin()` 已对 store 探活失败退 2），**不引入 SSM 存 prefix**。

- cli 用**已解析的 prefix** 拼出 cloud 资源名，启动时探存在性（`DescribeTable`/`HeadBucket`/`DescribeClusters`）。
- 不存在 → fail-fast 退 2，**错误信息带上 prefix**：如「用 `--prefix=gherkai-` 拼出的表 `gherkai-events` 不存在——是 prefix 配错、还是 CDK（`iac_aws_backend`）未部署？」。
- **preflight 按轴分层探（report ⊥ 执行，见下「组合根接线」）**：执行必需资源（events 表 + cluster + 桶 + **本 run 用到引擎的 task-def**）**恒探**（只要 `--backend cloud`）；**runs 表仅落库需要**——`--no-report` 时不探（`runs_table=None`）。即 `--backend cloud --no-report` **仍探执行资源、仍 Fargate 跑**，只是不落库、不探 runs 表。
- **task-def 与 detached 链 Lambda 已纳入 preflight（原「暂不探」护栏兑现反转）**：task-def 即上条恒探档里那项（`DescribeTaskDefinition`，按本 run **实际用到**的引擎探、**不探全注册表**）——反转理由 = 原先该维度的 prefix 配错要漏到 RunTask 才炸（退 1、不点名 prefix）。detached `submit` 另探事件驱动链三 Lambda（kicker/reconciler/exit-observer，`GetFunction`）——链上任一缺，提交会成功但 run 永不推进/收敛（kicker 缺=卡 pending、reconciler 缺=起首批后无人推进、exit-observer 缺=退出信号断链），preflight 把它挡在提交前；同步 `run` 不探 Lambda（进程内 schedule 推进、不依赖链）。`status --wait` 对 kicker `ResourceNotFound` fail-fast 退 2 点名 prefix（接力对象不存在、轮询死等无意义；其他 AWS 错——限流/瞬时——仍吞、下轮再踢）。探针全为只读（Describe*/Get*/Head*），submit 机器权限面仍无任何写/执行权限（[0034] 最小权限卖点不破）。
- **产物前缀一致性（存在性之外唯一的语义探针，detached `submit` 专属）**：detached cloud 档的产物前缀有**两个独立来源**——提交侧 `--report-dir`（offloader 的 `args/` 按它落）与推进侧 Lambda 的 `REPORT_DIR` env（判定真值 `jobs/`、RunReport `index/manifest`、worker 产物、job-in 全按它落；IaC **有意不注入**、由 Lambda 内缺省 `reports` 供给，见「资源清单」）。两者不一致时提交成功、run 也跑得完，但**结果落在用户没指定的前缀下**（用户在自己给的前缀里找不到报告，提交侧 `args/` 还留下一批孤儿对象）——典型「不可达但代价高的静默失败」，与上条「cli 读 SSM 空值 fail-fast」同风格挡在源头。**实现即复用已有探针**：`lambda:GetFunction` 的返回体已含 `Configuration.Environment`，故零额外 AWS 调用/权限——比对**两个推进器**（kicker/reconciler；exit-observer 不读 `REPORT_DIR`、不比），env 缺该键视作 Lambda 侧缺省 `reports`，两侧过同一分隔符规范化再比（`reports` 与 `reports/` 不算冲突），不一致即退 2 并**点名两侧值 + 给两条修法**（改 `--report-dir` / 在 CDK 给推进器注入 `REPORT_DIR`）。**为何选「比对 fail-fast」而非「detached 档拒绝非默认值」**：`--report-dir` 在 local 档与同步 `run --backend cloud` 都端到端生效（[0016](./0016-execution-architecture-core-lib-run-model.md)「单 S3 桶 + `--report-dir` 复用为 key 前缀」），改成「此档只能用默认」会让同一 flag 三档三语义；比对放行则「两侧配一致就能换前缀」照旧可用。
- **job-in S3 对象生命周期（已定 + 已实现 + 真跑验证）**：`FargateEngine.run_scope` 每 scope `PutObject` 一个 `jobs-in/<quote(scope_id)>.json` 对象（因 RunTask overrides 8192 上限塞不下含 feature 的 job）——喂 worker 的一次性输入、worker `GetObject` 读完即无用，无清理会随 run 堆积。**决策：S3 lifecycle 自动过期（7 天），按对象 tag `gherkai=job-in` 过滤——不用 key 前缀**。
  - **为何 tag 而非前缀**：job-in 落 `<report_dir>/<run_id>/jobs-in/`（run_id 在 key 中间），S3 lifecycle 的 filter 是**纯前缀**、框不住中间的 run_id；且同 `<run_id>/` 前缀下还有判定真值 `jobs/` 与报告 `index/manifest`（长期保留、误删代价高），前缀规则会误伤。tag 精确只框 job-in——`FargateEngine.put_object` 打 `Tagging="gherkai=job-in"`、CDK 桶挂 `LifecycleRule(tag_filters={"gherkai":"job-in"}, expiration=7d)`。判定真值/报告不打此 tag、不受影响。
  - **7 天**：对齐 events 表 TTL 心智（输入/协调类脚手架，留窗口供事后调查失败 run，之后自动清）。
  - **打 tag 在编排进程、非 worker**：`put_object` 在 `FargateEngine`（组合根注入的 s3_client、运维凭证）上跑，worker 只 `GetObject` 读——故**无需给 worker task role 加 `s3:PutObjectTagging`**（避免为清理反而扩 task role 权限，与「IAM 最小权限」一致）。
  - **真跑验证**：cloud job 真跑后核实真 S3——job-in 对象带 `gherkai=job-in` tag、判定真值 `jobs/` 无 tag（lifecycle 精确不误伤）、桶 lifecycle rule 生效。护栏：core `test_run_scope_job_in_tagged_for_lifecycle` + iac `test_artifacts_bucket_job_in_lifecycle`（含「不得用 Prefix filter」负向护栏）。
  - **已知边界（历史遗留、可接受）**：部署此 lifecycle **之前**写的旧 job-in 对象无 tag、不被本规则清理，永久残留（就地几十个小 json、属历史）。要清需一次性手动删（`aws s3api list-objects-v2 ... jobs-in/ | delete`），非本规则职责。

## 2 镜像：Nova / Midscene 各一（依赖环境本质不同）

**决策：两个容器镜像 + 两个 task-def，不合并。** 两个引擎 worker 运行时依赖差异大、合并镜像既臃肿又耦合升级：

- **Nova 镜像**：Python 3.13 + `nova-act`（含 boto3 / bedrock-agentcore / **playwright 库**）。入口 `python worker/run_scope.py`。
- **Midscene 镜像**：Node ≥20（代码用 `AbortSignal.timeout`/`fs recursive`/`Dirent.parentPath`）+ `tsx` + `@midscene/web` + **playwright 库** + 全部 `@aws-sdk/*` + `openai`。入口 `node --import tsx worker/run-scope.ts`。
- **不装 chromium 二进制（真跑证实）**：两个引擎 worker 都用 `connect_over_cdp` 连 **AgentCore 云浏览器**（浏览器跑在云端），playwright 只作 **CDP 客户端库**、**不 launch 本地 chromium**——故只需 playwright 库（pip/npm 已装）、**不需 `playwright install chromium` 的二进制 + 系统库**（省几百 MB、build 快得多）。真跑核实：去掉二进制后 worker 走到 `connect_over_cdp` 那步（连 AgentCore WebSocket），从不报缺 chromium。
- **构建平台 `--platform linux/amd64`（必记坑）**：Fargate task-def 默认 `X86_64` runtime；arm Mac（M 系列）build 不加则出 arm64 镜像、Fargate 容器启动期 `exec format error` 挂死（错误在启动期、不易一眼看出是架构问题）。
  - **构建陷阱（必记）**：Midscene 把运行时真需要的 SDK（`@midscene/web`/playwright/bedrock-agentcore/signature-v4/openai）大多放在 **devDependencies**，只有 `client-dynamodb`/`client-s3` 在 dependencies。Dockerfile **不能用 `npm install --production`**（会漏装）——须装全部依赖，或构建前把它们提到 dependencies。

镜像入口 CMD = 现有 subprocess cmd 去掉 stdin/fd 传输（job 走 S3、events 走 DDB，[0024](./0024-worker-core-protocol.md)）——worker 引擎逻辑不因执行环境变（[0016](./0016-execution-architecture-core-lib-run-model.md)）。

## container 名约定：`{engine}-worker`（不带 prefix）—— CDK↔cli 硬契约

**CDK 建 task-def 时，其内部 container 元素名必须恰为 `{engine}-worker`（`novaact-worker` / `midscene-worker`，不带 prefix）。** 这是 cli 侧硬假定的契约（`compose.container_name`），CDK 侧必须兑现，否则 cloud 每个 run 都炸：

- **为什么不带 prefix**：container 是 **task-def 内部**名、随已带 prefix 的 task-def 走（task-def family 已是 `{prefix}{engine}-worker`），再叠 prefix 冗余。故 container 名只用引擎规范名 `{engine}-worker`。
- **为什么是硬契约**：cli 的 `FargateEngine` RunTask 用 `overrides.containerOverrides[].name = {engine}-worker` 把 `JOB_S3_URI`/`EVENTS_DDB_TABLE`/`RUN_ID`/`SCOPE_ID`/`AWS_REGION`/`ARTIFACT_S3_*` 注进容器。ECS 要求该 name 与 task-def 里的 container 元素名**逐字匹配**，否则 RunTask 报 `container ... does not exist in task definition`——env 注入全落空、worker 拿不到 job/events/落点。
- **单一事实源**：与 task-def family 名（`{prefix}{engine}-worker`）、prefix 一致护栏同理——CDK 作者读本 ADR、须照此建。

## task-def 不焊 region/凭证（决策 C 的非对称落到 IaC）

- **task-def 不设 `AWS_REGION`**：region 每 run 可能不同，由组合根经 **RunTask overrides 的 `containerOverrides.environment`** 注入（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 C：组合根 `resolve_region` 落实成具体字符串再注入；真无 region → 不注入、worker fail-loud）。
- **task-def 不设 `AWS_PROFILE`**：Fargate 容器用 **task role** 凭证链（`AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` 由平台自动注）；注入 profile 名会 `ProfileNotFound` 盖过 task role（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 C 的正确非对称——profile 只对 subprocess 有意义）。
- 凭证一律经 task role，不在镜像/task-def 里放任何 access key。

## IAM 最小权限（安全最佳实践）

**task role**（容器内 worker 的凭证）——按动作 × 目标资源收窄，不给通配：

| 动作 | 目标资源 | 引擎 |
|---|---|---|
| `dynamodb:PutItem` | events 表 ARN（`{prefix}events`）——**不给 runs 表**（worker 绝不碰 RunState，[0024](./0024-worker-core-protocol.md)/[0030](./0030-realtime-persistence-seam.md) 单写者）| 两个引擎 |
| `s3:GetObject` | artifacts 桶 job 前缀（`arn:…:{prefix}artifacts/*`）| 两个引擎 |
| `s3:PutObject` + `s3:AbortMultipartUpload` | artifacts 桶 产物前缀——**不给 DeleteObject**（worker 只上传+删本地，S3 侧只 Put，[0029](./0029-engine-artifacts-to-s3.md)）。`AbortMultipartUpload` 必给：`upload_file`（TransferManager，>8MB 走 multipart）分段失败时清理已传分段，缺则 abort AccessDenied + 孤儿分段计费 | 两个引擎 |
| `bedrock-agentcore:` `StartBrowserSession`/`StopBrowserSession`/`GetBrowserProfile` | 系统 browser `arn:…:{region}:aws:browser/aws.browser.v1`（**account 段字面量 `aws`**）+ `browser-profile/*`（profileId 运行期变量）| 两个引擎 |
| `bedrock-agentcore:` `ListBrowserProfiles`/`CreateBrowserProfile`/`ConnectBrowserAutomationStream`/`ConnectBrowserLiveViewStream` | `*`（SAR resource_types 为空，**结构上不支持 resource-level**：List 枚举 / Create 资源尚不存在 / Connect 数据面流无资源实体）| 两个引擎 |
| `bedrock-agentcore:SaveBrowserSessionProfile` | 系统 browser + `browser-profile/*`——**仅 Nova** task role 授（Midscene 不需要；code 在 novaact 分支单授）| Nova |
| `nova-act:` `GetWorkflowDefinition`/`CreateWorkflowDefinition`/`CreateWorkflowRun`/`UpdateWorkflowRun`/`CreateSession`/`CreateAct`/`UpdateAct`/`InvokeActStep` | `workflow-definition/*` + `.../workflow-run/*`（nova-act IAM 只到 definition/run 两级；session/act 非独立资源。**definition 名段 `*` 不 pin 具体名**——definition 名是 worker 运行期概念，不该泄进 IAM 让 IaC 耦合 worker 常量）| Nova |
| `bedrock:InvokeModel` | `arn:aws:bedrock:*::foundation-model/qwen.qwen3-vl-235b-a22b`（account 段空、region 通配 model-id pin；裸 modelId 直连 ON_DEMAND、不走 inference profile）| Midscene |

- **编排进程角色不在本表**（本表只列 task role，列此防漏）：`ssm:GetParameter`（`/{prefix}backend/*`，读 subnet/sg）连同 preflight 只读探活、`lambda:InvokeFunction` 接力 kickoff 等**属编排进程角色**——完整权限面单列一处，见「资源清单」末段，别在此重复。
- **两个引擎 task role 分立**（各给各真调的动作、最小权限、一个引擎被攻破不波及另一个引擎）——CDK 已按引擎分立。
- **上表动作集由真跑逐个暴露、非 grep 推全**（证据边界，绿≠对）：`UpdateWorkflowRun`/`CreateSession`/`CreateAct`/`UpdateAct`/`InvokeActStep`/`CreateBrowserProfile`/`List`/`Get`/`SaveBrowserSessionProfile`/`ConnectBrowserAutomationStream` 全是**真跑 cloud job 逐个报 AccessDenied 才补上**的（SDK 内部调用面远比 lib 里 grep 到的大——每加一个 redeploy+真跑一轮）。
- **资源 ARN 已收窄（动作 + 资源两维度都最小）**：依据 = AWS Service Authorization Reference 的 `resource_types` + IAM 策略模拟器对本账户实证 + **收窄后真部署真跑验证无 AccessDenied**（两引擎 ×（确定性+AI），Midscene Bedrock 1867 tokens / Nova act 全 passed、产物真上传 S3）。三处从 `*` 收窄，另留 4 个结构上只能 `*` 的（见上表）：
  - **`bedrock:InvokeModel`** → 单一 foundation-model ARN（收窄幅度最大）。
  - **`nova-act`（8 动作）** → 两条 ARN（`workflow-definition/*` + `.../workflow-run/*`）覆盖全部。**definition 名段用 `*`、不 pin 具体名**：definition 名是 worker 运行期概念（`engines/novaact/lib/constants.py` 的 `WORKFLOW_DEF`），若 pin 进 IAM 会让 IaC 跨工程耦合 worker 常量、靠"人肉注释保持一致"（改 worker 忘改 IaC → 静默 AccessDenied）。用 `*` 通配 definition 名换掉耦合——仍锁死 service/account/region，远窄于全 `*`。**顺带删了误授的 `nova-act:GetAct`**——AWS Service Reference v1.4 全动作集无此 action（此前多授一个不存在的动作，真跑删后照跑通）。
  - **`bedrock-agentcore` 可收窄的 4 个**（Start/Stop/GetProfile/Save）→ 系统 browser + `browser-profile/*`。**踩坑记录（copy-account 陷阱）**：系统默认 browser（`aws.browser.v1`）的 ARN **account 段是字面量 `aws`、不是客户账户**——AWS 官方人读文档（browser-profiles.html）误写成 `<account_id>`，实测 `get-browser` 返回 `aws`、模拟器验证填客户账户会 implicitDeny（下次部署必挂）。browser-profile 才是客户自建资源（account=客户账户、profileId 用 `*`）。两类 account 段方向相反，勿混。
  - **4 个只能 `*` 的**（List/CreateBrowserProfile/Connect×2）：SAR `resource_types` 为空，模拟器实证 scope 到任何具体 ARN 均 implicitDeny——**结构上不支持 resource-level**，诚实保留 `*`（非"待标定"）。
  - **风险收在两道**：`*` 只在这 4 个结构性动作的资源维度宽；**动作维度全最小 + 两引擎 task role 分立**（一引擎被攻破不波及另一个）。回归护栏见 `iac_aws_backend/tests/test_stack.py::test_task_role_resource_arns_narrowed`（钉死 ARN 形态 + account=aws 陷阱 + GetAct 已删）。
- **task execution role** 用 AWS 托管的 `AmazonECSTaskExecutionRolePolicy`（拉 ECR + 写日志）即可，与 task role 分开（execution role 是平台拉镜像用、task role 是容器内应用用，职责不同）。
- **无状态跑批链的 3 个 Lambda 执行角色**与上两者同样**分立**（各随 Function 建）：起 task（`ecs:RunTask` + `iam:PassRole`）、表桶读写、超时 schedule 的 `scheduler:Create|DeleteSchedule` 都收在这里，动作与资源域见「资源清单」10./15.——**worker 的 task role 一个都不含**（worker 绝不起 task、绝不碰 runs 表，[0030](./0030-realtime-persistence-seam.md) 单写者）。
- workflow definition：**已定 = CDK 不预建、worker 首跑 create-if-not-exists**（`workflow_setup.py`），故 Nova task role 授 `GetWorkflowDefinition` + `CreateWorkflowDefinition` 两者（见上表）。曾倾向「IaC 预建 + task role 收紧到只读 `Get`」（更干净、权限更小），但 CDK 落地时选了不预建（worker 自建闭环、无需 IaC 额外建 workflow definition 资源）——代价是 task role 保留 `Create`。若未来改为 IaC 预建，再把 task role 收紧到 `Get`-only。

## 组合根接线（非 IaC，已编码）

`runtime/gherkai_runtime/compose.py`（产品本体，曾居 `cli/`——[0016](./0016-execution-architecture-core-lib-run-model.md)「演进」节）的 `build_engines` 只产 `SubprocessEngine`（两个引擎，local 执行）。新增 `build_fargate_engines`，`--backend cloud` 用它替代：

- **`build_fargate_engines`（对称 `build_engines` 的 dict）**：按 `job.engine` 造 `FargateEngine`（`new_run_id()` 后把 run_id + cluster + 按引擎选的 task-def + network（读 SSM）+ events 表名 + container-name + job-s3 + artifact-s3 + **SDK 产物落点 env** + region 一起注入构造，对称已有 store 注入；**不传 profile**——决策 C 非对称）。
- **产物上传要注入两组 env、缺一不可（真跑暴露）**：worker `ArtifactUploader` 上传需要 ① `ARTIFACT_S3_BUCKET`/`PREFIX`（S3 落点）**和** ② SDK 产物本地落点 env（`NOVA_LOGS_DIR`/`MIDSCENE_RUN_DIR`，容器内路径，如 `/tmp/gherkai-run/<run_id>/{nova-trajectories,midscene-run}`）——uploader 用后者的父级算 `run_dir`/相对 key，**缺它 `run_dir=None` → uploader no-op → 报 `file://` → 产物写容器盘、STOPPED 后随盘销毁必丢**（ADR [0029](./0029-engine-artifacts-to-s3.md)）。subprocess 侧 `build_engines` 本就注入 SDK 落点 env，Fargate 侧曾漏（只注 S3 落点）——**只注 ①不注②等于没上传**。这两组按引擎不同（Nova `NOVA_LOGS_DIR` / Midscene `MIDSCENE_RUN_DIR`），组合根按引擎算好、`FargateEngine` 引擎无关地转发。
- **按引擎选 task-def**：`job.engine` → `{prefix}{engine}-worker`（对称 `EngineResolver` 按 engine 选 cmd）。
- **Fargate 配置参数**：`--prefix`/`--cluster`/`--subnet`/`--security-group`/`--events-table` 等走 CLI 参数、默认 = prefix 推导 / SSM 读、可覆盖（决策 C，[0016](./0016-execution-architecture-core-lib-run-model.md)）。
- **`--backend cloud` 切执行引擎**：决策 A 从设计落到 CLI 的动作点——cloud ⇒ FargateEngine 而非 SubprocessEngine。
- **report ⊥ 执行（关键，别耦合）**：`--backend` 定**执行环境**（cloud⇒Fargate）、`--no-report` 定**落不落库**，两轴正交。故组合根把「Fargate 执行配置解析 + 切 FargateEngine」放在 `do_report` **之外**（只看 `--backend cloud`）——`--backend cloud --no-report` = **Fargate 执行 + 不落库**（不是退回 subprocess）。`--no-report` 的逃生舱只跳过 store 落库（`persistence=None`），绝不改执行环境。（被拒的错误接线：把 FargateEngine 切换塞进 `if do_report` 分支——会让 `--no-report` 意外把执行退回 subprocess，违背决策 A 的「cloud=Fargate 与 report 无关」。）

## 已定的两项（原开放项，已编码）

- **Midscene region 全可配（修硬编码，不接受 east 固定）**：Midscene 的 AgentCore + Bedrock 模型连接此前用硬编码 `REGION="us-east-1"`（`engines/midscene/lib/agentcore-sigv4.mts` + `run-scope.ts` 的 `BedrockAgentCoreClient({region})`）——注入 `AWS_REGION=us-west-2` 时其 events/job/artifact 走 west、但浏览器会话+模型仍走 east（半贯通）。**决策：改成惰性读 `process.env.AWS_REGION`**（`getRegion()`/`getBaseUrl()`，与 I/O 边缘同源），使 region 真正全可配、与 Nova 侧一致（Nova 全程读同一 env、无此问题）。这样 Midscene task role 的 AgentCore/Bedrock 权限**不锁死 east**、跟注入的 region 走。（region=None 时的 fail-loud 语义随之统一，对齐 [0016](./0016-execution-architecture-core-lib-run-model.md) 决策 C。）
- **events 表开 TTL（worker 写时间戳）**：worker emit 时给每条 event item 多写一个 `expires_at`（epoch **秒**，= 写入时刻 + **7 天**），CDK 在该属性上开 DynamoDB TTL。**7 天的理由**：events 是协调/进度脚手架，权威数据在 RunReport/ResultStore（events 归约完即死重）——但留 7 天窗口供事后调查失败 run（如「worker 到底 emit 没 emit scope_done」），几天后仍可查、又自动清、免手工清理。属性名 `expires_at`（DDB TTL 惯例、epoch 秒）；两个引擎 worker 对称写（Nova put_item / Midscene PutItemCommand 的 `{N}`）。**FargateEngine 读端不受影响**——它只认 `pk`/`seq`/`body`（[0024](./0024-worker-core-protocol.md)），多一个属性无害、不进 Query 投影约束。TTL 是**最终清理、非精确**（DDB 可能延迟至 48h 才删过期项）——无碍，因为读端从不依赖过期项存在。

## 留待（defer）

- **镜像瘦身**：属施工，不在本 ADR 决策面。（真容器 grace/中断校准已完成，归 [0032](./0032-fargate-execution-environment.md) Accepted。）
- **build & push ECR 的自动化程度**：手动步骤已由 `tools/build_push_workers.py` 固化（ECR 登录 + 两引擎 `docker build --platform linux/amd64` + push 一条命令，`--platform` 硬编码防 arm64 Fargate 启动挂死）——消除手敲错，本地可真跑。**全自动 CI**（GitHub Actions + OIDC 免密钥 assume role、push/改 Dockerfile 触发）仍待建：需先定远端仓库托管 + CI 凭证方案（OIDC provider/role 又是一处 IaC + 需 org/repo 信息），非本地能闭环，故 defer 到有明确 CI 需求 + 仓库托管确定时。

## 重议

- 若多环境需求超出「prefix 切名」（如跨账户、跨 region 多活）→ prefix 单层不够，重议是否引入 CDK context/环境配置文件。
- 若编排进程也上云（WebUI 后端跑在 AWS）→ 编排进程角色需正式建，届时并入本 stack。
