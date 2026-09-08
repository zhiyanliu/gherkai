# gherkai-deploy-aws

`gherkai` 的 **AWS 后端供给** provider 包：Python CDK 定义 `--backend cloud` 所需的全部云资源（DDB / S3 / ECS / ECR / IAM / VPC + 无状态跑批的 Stream·Lambda·EventBridge，ADR [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)/[0034](../docs/adr/0034-detached-batch-reconciler.md)），以及 worker 镜像的推送与注册（ADR [0038](../docs/adr/0038-worker-image-delivery.md)）。

- 发行名 `gherkai-deploy-aws` · import 名 `gherkai_deploy_aws`（ADR [0037](../docs/adr/0037-distribution-and-packaging.md) 决策 2a/6）。
- **不单独安装**：随 CLI 的 extra 进来——`uv tool install 'gherkai[deploy-aws]'`；命令面是 `gherkai deploy` / `gherkai destroy`，本包经 entry point group `gherkai.deploy` 被发现（装一个 provider 时无需 `--provider`）。
- 只有**部署方**需要装它：改云端环境是云端写操作；只提交 run 的人不需要（ADR 0037 决策 2c）。
- **Node ≥ 22 必须在 PATH**：`aws-cdk-lib` 是 jsii 绑定（import 即起 node 子进程），cdk CLI 本身也是 npm 物。命令用 PATH 上的 `cdk`，没有则回落 `npx -y aws-cdk@2`。缺 Node 时命令报一句人话并退 2，不吐 jsii 堆栈。

> **「clone repo + 裸 `cdk deploy`」不再是部署形态**（ADR 0037 决策 6）：那条路要求源码树在手、相对路径拼 Lambda asset、且把 vpc context 的坑外露给每个使用者。现在 IaC 随 wheel 分发，`gherkai deploy` 在临时工作目录生成 `cdk.json`（`app` 指向 `python -m gherkai_deploy_aws.app`）后调 cdk CLI。contributor 想看模板走 `gherkai deploy --synth-only DIR`，别裸跑 `python -m gherkai_deploy_aws.app`（它缺 `-c version=` 会 fail-fast，这是有意的）。

## 建什么

一套 CloudFormation stack，stack 名 `BackendStack-<prefix 去尾横线>`（可按 prefix 多实例化，支持 prod-/stage- 多环境并存）：

- **DynamoDB**：`{prefix}runs`（控制面/RunStore）+ `{prefix}events`（events-out，开 `expires_at` TTL）——**两表均开 DynamoDB Stream（`NEW_IMAGE`）**，作为无状态跑批事件驱动链的触发源（见下「事件驱动推进」，ADR 0034）
- **S3**：`{prefix}artifacts`（判定结果 / 报告 / offload / job-in / 引擎产物，按 key 前缀分片）+ lifecycle 规则 `expire-job-in`（**按对象 tag `gherkai=job-in`** 7 天过期——job-in 的 key 里 `run_id` 在中间，纯前缀 filter 框不住且会误伤判定真值与报告）
- **ECS**：`{prefix}cluster` + 2 个 Fargate task-def（`{prefix}novaact-worker` / `{prefix}midscene-worker`）
- **ECR**：2 个 repo（repo 名复用 task-def family 名；镜像由部署方 build & push，CDK 只建 repo、synth 不触发 docker build）
- **IAM**：每引擎一个最小权限 task role + 共享 execution role + 3 个 Lambda 执行角色 + job timeout 的 Scheduler 执行 role `{prefix}timeout-scheduler`
- **VPC + SSM 网络**：worker 网络（subnet/sg）+ 把它们的 ID 写进 `/{prefix}backend/subnets`、`/{prefix}backend/security-groups`（cli 读）
- **SSM 部署戳**（都是 **stack 资源**、不是命令事后 `put_parameter`——与部署事务同生死、回滚不留错值，ADR 0037 决策 6）：
  - `/{prefix}backend/version`：后端版本戳，供提交侧 preflight 比对 CLI 版本（skew 三态，ADR 0037 决策 7）
  - `/{prefix}backend/vpc`：**生效的 VPC 档**，供下次 `gherkai deploy` 三态比对（见下「VPC 三档」）
  - `/{prefix}backend/worker-template/<engine>`：worker task-def 的**模板 revision ARN**（`Ref` 返回带 revision 的 ARN），`push-worker` 从它复制模板（ADR 0038 四步第 1 步）

### 事件驱动推进（无状态跑批，ADR 0034）

`submit` 提交完即走、进程不驻留，`run` 的推进改由云上事件链自我驱动（`stack._reconcile_lambdas`）。同步 `run` 路径不消费 Stream、仍走 Query 轮询，与此链解耦（ADR 0024）。

- **三个 Lambda**（同一份打包 asset，`handler` 入口不同——见下「Lambda 打包」）：
  - `{prefix}kicker`（踢启器）：`{prefix}runs` 表 Stream 的 **INSERT** 触发（`submit` 的 `create_run` 写 definition）→ 冷启动起首批 task；也被 cli `status --wait` 直接 invoke 做 kickoff。handler=`reconciler.kicker_handler`。
  - `{prefix}reconciler`：`{prefix}events` 表 Stream 触发（worker `PutItem` 执行事件 / 退出观察者写 `task_exited`）→ `reconcile.tick` 推进 + finalize 聚合。handler=`reconciler.handler`。
  - `{prefix}exit-observer`（退出观察者）：ECS Task `STOPPED` 事件触发 → 写 `task_exited` 事件（薄；只 events 表 `PutItem`）。handler=`exit_observer.handler`。
  - kicker/reconciler 共享起 task 的全套权限与装配（`RunTask` / `PassRole` / 表桶读写 + `SUBNETS` / `SECURITY_GROUPS` / `MAX_CONCURRENCY` / `WORKER_TEMPLATE_ARNS`）；分工 = kicker「让 run 动起来」、reconciler「推着走」。`MAX_CONCURRENCY`（当前 `8`，两侧须同值）是**部署侧 per-run 并发 cap**、不是真源——每个 run 并行几个 job 由提交侧的 `submit --max-concurrency` 随 definition 声明，kicker/reconciler 取 `min(声明, cap)`；cap 在此是因为 task 烧的是部署方账单，local 档无 cap（ADR 0034 机制四）。
  - `WORKER_TEMPLATE_ARNS`（`engine=arn` 逗号串）与 SSM `worker-template/<engine>` **同一份值同一个事务**，是 ADR 0038 读侧兼容口径的前向口子——当前 handler 尚未消费它（起 task 仍传 family），variant 解析随 0038 的 `push-worker` 批次落地。
- **EventBridge rule `{prefix}ecs-stopped`**：按 `source=aws.ecs` + `ECS Task State Change` + `lastStatus=STOPPED` + 本 cluster 的 `clusterArn` 过滤（不误触别的负载）→ 打到 `{prefix}exit-observer`。
- **Event source mappings**：`{prefix}events` 表 Stream → reconciler；`{prefix}runs` 表 Stream → kicker（**带 `eventName=INSERT` ∧ `detached=true` filter**，只让 detached 的 `create_run` 触发冷启动；reconciler 之后写 runs 表的 `MODIFY` 不自触发放大，见 ADR 0034 被拒方案）。
- **job timeout 到点触发器**（ADR 0034「job timeout」节）：IAM role `{prefix}timeout-scheduler`（`scheduler.amazonaws.com` assume、只准 invoke kicker——授权写**确定性 kicker ARN 串**而非资源引用，免 role↔function 互引成环）+ EventBridge Scheduler 的 one-time schedule 名字空间 `{prefix}job-timeout-*`（default group，`ActionAfterCompletion=DELETE` 到点自删、idle 零成本）+ 注给 reconciler/kicker 的 `KICKER_ARN` / `SCHEDULER_ROLE_ARN` env。改 prefix 时这两个名字随之变。

### Lambda 打包（`stack._build_lambda_asset`）

三个 Lambda 共用一个 asset：本包 `gherkai_deploy_aws/lambdas/` 的两个 handler 源摊在 **zip 根**（故 `exit_observer` 里 `from reconciler import …` 这条平级 import 成立；也因此 handler 源不做成本包的子包）+ 从**当前 venv 已安装位置**复制的 `gherkai_runtime` / `gherkai_core` / `gherkin` / `packaging` / `typing_extensions`。**不打 `gherkai_cli`**（Lambda 不背 argparse/render，ADR 0016「演进」节）；**boto3 由 Lambda runtime 自带、不打**。

两条踩出来的规矩：

- **来源必须是「已安装包」，不是仓库相对路径、也不是联网 `pip install`**（ADR 0037 决策 6）。相对路径只在 monorepo 里成立，wheel 用户的 site-packages 没那种布局；联网装会在离线环境断，且装到的是 PyPI 上的某个版本而非**运行中这一份**——dev 版根本不在 PyPI 上，contributor 部署自己的 dev 版会直接断。
- **清单是手写的，所以要有一条真 import 的测试守着**：`typing_extensions` 是 `gherkin-official>=42` 的传递依赖（`gherkin/parser_types.py` 无条件 import 它），旧的 `pip install --target` 顺带装上、改成「按名复制」后就漏了——单测全绿，真 synth 出的 asset 一 import 就 `ModuleNotFoundError`。现在 `tests/test_lambda_asset.py::test_asset_imports_with_only_stdlib_beside_it` 在**剥掉 site-packages 的子进程**里真 import 一遍 asset，加/换依赖时它是判据。

asset 落进 `gherkai deploy` 的临时工作目录（`GHERKAI_LAMBDA_ASSET_DIR`，命令用完即删），不再写进仓库或包目录。

## prefix 契约（关键）

`--prefix`（默认 `gherkai-`，也认 `AWS_RESOURCE_PREFIX`）**必须与 `gherkai run` / `submit` 的 `--prefix` 一致**——CDK 建的资源名 = cli 推导的默认名（`gherkai_deploy_aws/names.py` re-export 产品本体 `gherkai_runtime.names`，与 cli 同源）。不一致 → cli 连不上资源、preflight 报错点名 prefix。

命名规则**真同源**：`names.py` 直接 re-export `runtime/gherkai_runtime/names.py`（曾因「CDK 独立工程、不能 import cli」复刻一份、须两处同步改——组合根共享层抽为平级的产品本体包后复刻消除，ADR 0016「演进」节/0033）。stack 名的推导（`names.stack_name`）也是单一真源：`app.py` 建 stack 用它，命令做 VPC 档三态比对时 `DescribeStacks` 用同一个名。

## VPC 三档 + 档比对（踩过的坑，别放松）

`--vpc` **必给、无隐式默认**（deploy / `--diff` / `--synth-only` / destroy；`--bootstrap` 是账户级动作、不合成 stack、不需要它），三档：

| flag | 含义 | SSM `vpc` 里记成 |
|---|---|---|
| `--vpc default` | 用账户默认 VPC | `default` |
| `--vpc new` | 本 stack 新建（2-AZ、**零 NAT**） | `new:<所建 vpc-id>` |
| `--vpc vpc-xxxx` | 复用现有 VPC | `vpc-xxxx` |

三档都走**公有子网 + `assignPublicIp=ENABLED`** 出网连 AgentCore/Bedrock/S3/DDB（worker 只出不入），**零 NAT 成本**；真私有隔离（NAT / VPC endpoint）留 backlog，改它要同步 `_worker_subnet_ids` 与 cli 的 `assignPublicIp`（跨组件联动）。

> ⚠️ **为什么必给、还要比对**：vpc 的选择**不进 stack state**。裸 cdk 时代漏带 context 的后果是 diff 里出现「新建整套 VPC + 替换 WorkerSg」的危险变更集——**这是真踩过的坑**。只强制显式给值挡不住「第二次 deploy 敲错档」，故 stack 把生效档写成 SSM 参数，命令在调 cdk 前比对，三态齐全：
> - **stack 不存在** = 真首次部署 → 放行；
> - **参数缺失但 stack 已存在** = 这个部署早于档登记机制（本机制之前部署的环境都没有这个参数，而这恰是最危险的那一次 deploy）→ 退 2，要求先 `--diff` 核对变更集、再带 `--allow-vpc-change` 放行一次；
> - **参数存在**：与 `--vpc` 一致 → 放行；不一致 → 退 2（`--allow-vpc-change` 放行，且会打印两个档让你看清）。
>
> `--diff` **自己不做这个比对**——它正是三态让你去跑的那条核对手段，拦住它就无路可走。

## 用

本包是根 uv workspace 的成员，contributor 一次 `uv sync` 即装齐。下面的命令从仓库任意位置都可跑（`uv run gherkai …`）；已安装的用户直接 `gherkai …`。

```bash
# 首次在某 account+region 用 CDK：先 bootstrap（= cdk bootstrap aws://<account>/<region>；账户级，不需要 --vpc）
gherkai deploy --bootstrap

# 先看清这次会改什么（尤其网络/IAM）——每次 deploy 前的推荐动作
gherkai deploy --diff --vpc default --prefix gherkai-

# 真部署/更新
gherkai deploy --vpc default --prefix gherkai-
gherkai deploy --vpc new --require-approval broadening      # 新建整套 VPC；IAM 变更要人过目

# 逃生舱：只导模板到 DIR、不碰账户（交给自己的审批/发布流水线去 apply）
gherkai deploy --synth-only ./out --vpc default

# 拆栈（RETAIN 语义见下）
gherkai destroy --vpc default --prefix gherkai-
```

`--region` / `--profile` 与 `run`/`submit` 同名同义（region 解析链 `--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile config，ADR 0016 决策 C）。退出码：`0` 成功；`2` 前置/校验失败（Node 缺失、VPC 档不符、读后端失败）；其余为 cdk CLI 自己的返回码（原样透传）。

`--stop-timeout N` 标定 worker container 的 SIGTERM→SIGKILL 宽限（默认 120s）。**Fargate 硬上限就是 120s**，>120 会在部署期被 ECS 拒——命令/synth 期就 fail-fast、点名这是平台限制而非笔误（Nova 的 grace 下限 150s > 120s 这个冲突正卡在这条硬上限上，见 ADR [0032](../docs/adr/0032-fargate-execution-environment.md)）。

### 本地验证（不碰 AWS）

```bash
uv run pytest deploy_aws/tests -q   # stack 合成断言 + Provider + Lambda asset（纯本地）
```

## worker 镜像

CDK 只建 ECR repo、不 build 镜像。当前仍用 `tools/build_push_workers.py`（ECR 登录 + 两引擎 `docker build --platform linux/amd64` + push，一条命令）；ADR [0038](../docs/adr/0038-worker-image-delivery.md) 落地后由 `gherkai deploy push-worker` 取代，`tools/build_push_workers.py` 随之退役。

```bash
python tools/build_push_workers.py                     # 两引擎都 build&push（tag=latest, prefix=gherkai-）
python tools/build_push_workers.py --engine novaact --prefix prod-
python tools/build_push_workers.py --dry-run           # 只打印命令
```

> ⚠️ **必须 `--platform linux/amd64`**：Fargate task-def 默认 `X86_64`；arm Mac 上不加会 build 出 arm64，容器**启动期** `exec format error` 挂死——错误发生在启动期、不易一眼看出是架构问题。脚本已硬编码保证；手敲底层命令时别漏。（ADR 0038 让 `push-worker` 在推送前校验架构、提前 fail-loud。）

## 清理（destroy 之后还要手动删）

**数据类资源不随 destroy 删**（表/桶/ECR `RemovalPolicy.RETAIN`、防误删，ADR 0033）——`gherkai destroy` 之后 2 张 DDB 表 + artifacts 桶 + 2 个 ECR repo **残留、需手动删**：

```bash
aws dynamodb delete-table --table-name gherkai-runs
aws dynamodb delete-table --table-name gherkai-events
aws s3 rb s3://gherkai-artifacts --force                                      # 桶非空需 --force
aws ecr delete-repository --repository-name gherkai-novaact-worker --force
aws ecr delete-repository --repository-name gherkai-midscene-worker --force
```

不手动删则同 prefix 重新 deploy 会因资源已存在而冲突。cluster / task-def / SSM 参数（含版本戳与 VPC 档）/ 日志组随 stack 销毁、无需手动——部署戳有意**不** RETAIN：它是部署元数据，留着只会让下次 deploy 拿到已消失环境的档。
