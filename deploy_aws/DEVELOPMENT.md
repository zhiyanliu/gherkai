# gherkai-deploy-aws — contributor 手册

> 同目录 [`README.md`](./README.md) 是本包的入口页（它**逐字**作为 `gherkai-deploy-aws` 的 PyPI 长描述发布，只保留定位 / 安装方式 / 最小用法与外链）；部署方的操作流程在 [`docs/user-guide/cloud-backend.md`](../docs/user-guide/cloud-backend.md)。本文件面向 contributor：包内布局、设计约束、本地验证，以及几条实测得来的约束。**权威在 ADR + code**，本文件只做导航，并说明改动时须守住的约束。

## 包定位与发现面

- 发行名 `gherkai-deploy-aws` · import 名 `gherkai_deploy_aws`（ADR [0037](../docs/adr/0037-distribution-and-packaging.md) 决策 2a/6）；随 CLI 的 `[deploy-aws]` extra 装，只有部署方需要（决策 2c）。
- 经 entry point group `gherkai.deploy` 的 `aws` 项被 CLI 发现（`gherkai_deploy_aws.cli:Provider`）：装了一个 provider 时无需 `--provider`。
- **「clone repo + 直接 `cdk deploy`」不再是部署形态**（ADR 0037 决策 6）：该形态要求本地持有源码树、以相对路径拼装 Lambda asset，且把 vpc context 的易错点外露给每个使用者。现在 IaC 随 wheel 分发，`gherkai deploy` 在临时工作目录生成 `cdk.json`（`app` 指向 `<当前解释器> -m gherkai_deploy_aws.app`，取 `sys.executable`、而非写死 `python`）后调 cdk CLI。查看模板用 `gherkai deploy --synth-only DIR`；**不经 `gherkai deploy` 生成的 `cdk.json` 手工运行 `python -m gherkai_deploy_aws.app` 不是支持的用法**，它缺 `-c version=` 会 fail-fast，这是有意的。

## 模块布局

| 文件 | 职责 |
|---|---|
| `cli.py` | `Provider`：命令面 flag、context 拼装、`cdk.json` 生成、cdk CLI 调用（`deploy` / `destroy` / `diff` / `--synth-only` / `--bootstrap`）、VPC 档比对（四种判定）、工具链前置检查（Node ≥ 22 + cdk 可定位）、`gherkai doctor` 的部署方段（node / cdk / 容器引擎三项只读自检，全 `required=False`）、worker 镜像子动词分派 |
| `stack.py` | `BackendStack`：全部云资源（含 `_reconcile_lambdas` 事件链、`_build_lambda_asset`、`_worker_subnet_ids`） |
| `app.py` | cdk app 入口（`cdk.json` 的 `app` 指向它），按 context 建 stack |
| `names.py` | 命名契约：**直接 re-export** `runtime/gherkai_runtime/names.py`（见下「命名真源」）+ provider 特有的 `stack_name`、`ssm_*` 路径 helper、`LAMBDA_ASSET_DIR_ENV`（命令进程 → cdk 起的 app 进程之间传 asset 落点的 env） |
| `workers.py` / `container.py` | worker 镜像族命令的实现 / 容器引擎抽象 |
| `lambdas/reconciler.py`、`lambdas/exit_observer.py` | 三个 Lambda 的 handler 源（打包时平铺在 asset zip 根，故平级 import 成立） |
| `tests/` | 见下「本地验证」 |

包根 `__init__.py` 是空文件；`lambdas/` **有意不带 `__init__.py`**：handler 源在 asset zip 根是平级顶层模块，做成子包后，包内相对 import 在 Lambda 中不成立。

**唯一接缝的硬约束**：**CLI 前端绝不 import `aws_cdk`**（jsii 绑定，import 即起 node 子进程，ADR 0037 决策 6）。故 `cli.py` 自身也只 import 标准库 + `gherkai_runtime` + 本包 `names`（零 `aws_cdk`）；`stack.py` / `app.py` 只经 cdk CLI 起的子进程触达。改动时须确保 `aws_cdk` 不进入 `cli.py` 的 import 面：`gherkai --help` 的启动代价取决于这条约束。

**`--require-approval` / `--allow-vpc-change` 是有意的两层声明**：CLI 前端先声明 provider 中立版（provider 缺席时 `deploy --help` 不残缺），`Provider.add_arguments` 再声明带 AWS 语义的版本（前者以 `choices` 校验 cdk 三档、后者的措辞明确指向 VPC 档三态）；前端的 subparser 开 `conflict_handler="resolve"`，同名以后声明的为准。两层不是重复真源，而是「中立占位 + provider 精确化」。两层都只声明在 `deploy` 上：`destroy` 不消费它们（不做 VPC 档三态比对、`cdk destroy` 也无 `--require-approval`），若声明在 `destroy` 上，只会让 `destroy --help` 出现两个恒无效的旋钮。`Provider` 另经 `getattr` 容忍它们彻底缺席（其它前端）：缺 `--allow-vpc-change` 即一律不放行（fail-closed）。

## 命名真源

`names.py` 直接 re-export `runtime/gherkai_runtime/names.py`：此前曾因「CDK 独立工程、不能 import cli」复刻过一份、须两处同步修改，共享层抽为平级产品本体包后复刻消除（ADR [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)「演进」节 / [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）。stack 名的推导（`names.stack_name`，`BackendStack-<prefix 去尾横线>`）同样单一真源：`app.py` 建 stack 用它，`cli.py` 做 VPC 档三态比对时 `DescribeStacks` 用同一个名。

## 事件驱动推进（无状态跑批）

`submit` 提交完成即返回、进程不驻留，run 的推进由云上事件链自我驱动（`stack._reconcile_lambdas`，ADR [0034](../docs/adr/0034-detached-batch-reconciler.md)）。同步 `run` 路径不消费 Stream、仍走 Query 轮询，与此链解耦（ADR [0024](../docs/adr/0024-worker-core-protocol.md)）。

- **三个 Lambda**（同一份打包 asset，`handler` 入口不同）：
  - `{prefix}kicker`（踢启器）：`{prefix}runs` 表 Stream 的 **INSERT** 触发（`submit` 的 `create_run` 写 definition）→ 冷启动时启动首批 task；也由 cli `status --wait` 直接 invoke 以执行 kickoff。handler=`reconciler.kicker_handler`。
  - `{prefix}reconciler`：`{prefix}events` 表 Stream 触发（worker `PutItem` 执行事件 / 退出观察者写 `task_exited`）→ `reconcile.tick` 推进 + finalize 聚合。handler=`reconciler.handler`。
  - `{prefix}exit-observer`（退出观察者）：ECS Task `STOPPED` 事件触发 → 写 `task_exited` 事件（薄；只 events 表 `PutItem`）。handler=`exit_observer.handler`。
  - kicker/reconciler 共享起 task 的全套权限与装配（同一个 `_advancer_function`：2 分钟超时、256 MB；`ecs:RunTask`（family 全部 revision）+ `ecs:DescribeTasks`/`StopTask`/`ListTasks` + `iam:PassRole`（execution role 与各 task role、Scheduler 执行 role）+ `scheduler:CreateSchedule`/`DeleteSchedule` + runs 表读写 / events 表只读 / 桶读写，env `SUBNETS` / `SECURITY_GROUPS` / `MAX_CONCURRENCY`，另加 `ssm:GetParameter` + `ssm:GetParametersByPath` 于 `/{prefix}backend/*`）。kicker 负责让 run 从零启动（runs 表 INSERT、`status --wait` 的主动调起、超时闹钟到点），reconciler 负责在执行事件到达时推进一步并聚合收尾；两者运行同一份 `reconcile.tick` 代码。env `MAX_CONCURRENCY` 取 `stack.BackendStack.DEPLOY_SIDE_MAX_CONCURRENCY`，**两个推进器必须同值**：同值由「两者共用一份 `advancer_env` dict」的结构保证，不依赖人工对齐；这道部署侧 cap 与提交侧声明的关系、local 档为何无 cap，见 [`docs/internals/execution-and-reconciliation.md`](../docs/internals/execution-and-reconciliation.md)。
- 两个推进器起 task 用 **definition 里解析好的显式 task-def revision**（不是 family 最新 ACTIVE：取最新会让任意一次 `push-worker` 把在跑 run 的镜像换成他人推送的 variant）。没有该字段的旧 definition（升级窗口内在跑的 run / 旧 CLI 提交的 run）走**兼容回落**：读 SSM `worker-default` + `worker-image/<engine>/<后端版本>-<默认 variant>` 解析 revision，这也是它们需要 SSM 读权限的原因。**不回落模板 revision**：模板的镜像栏是 `latest` 占位，全新 prefix 上无法拉取（ADR [0038](../docs/adr/0038-worker-image-delivery.md) 列为被拒方案）。
- **EventBridge rule `{prefix}ecs-stopped`**：按 `source=aws.ecs` + `ECS Task State Change` + `lastStatus=STOPPED` + 本 cluster 的 `clusterArn` 过滤（不误触其它负载）→ 路由到 `{prefix}exit-observer`。
- **Event source mappings**（两侧都带 filter）：`{prefix}events` 表 Stream → reconciler，**filter `eventName != REMOVE`**：events 表开了 TTL（`expires_at`），过期删除同样进 Stream，不过滤会让 reconciler 以「此刻尚存的事件」对早已收尾的 run 重算并覆盖判定真值；用 `anything-but REMOVE` 而非 `INSERT` 白名单，是因为同键重写（迟到的退出观察者以真退出码重写超时处置写下的记录）在 Stream 上是 `MODIFY`。`{prefix}runs` 表 Stream → kicker，**filter `eventName=INSERT` ∧ `NewImage.detached=true`**，只让 detached 的 `create_run` 触发冷启动；reconciler 之后写 runs 表的 `MODIFY` 不会自触发放大（ADR 0034 把「无 filter」列为被拒方案）。两个 mapping 都以 `LATEST` 为起点、`retry_attempts=2`。
- **job timeout 到点触发器**（ADR 0034「job timeout」节）：IAM role `{prefix}timeout-scheduler`（`scheduler.amazonaws.com` assume、仅允许 invoke kicker；授权写**确定性 kicker ARN 串**而非资源引用，以避免 role↔function 互引成环）+ EventBridge Scheduler 的 one-time schedule 名字空间 `{prefix}job-timeout-*`（default group，`ActionAfterCompletion=DELETE` 到点自删、idle 零成本）+ 注给推进器的 `KICKER_ARN` / `SCHEDULER_ROLE_ARN` env。改 prefix 时这两个名字随之变化。

## Lambda 打包（`stack._build_lambda_asset`）

三个 Lambda 共用一个 asset：本包 `gherkai_deploy_aws/lambdas/` 的两个 handler 源平铺在 **zip 根**（故 `exit_observer` 里 `from reconciler import …` 这条平级 import 成立；也因此 handler 源不做成本包的子包）+ 从**当前 venv 已安装位置**复制的 `gherkai_runtime` / `gherkai_core` / `gherkin` / `packaging` / `typing_extensions`（清单 = `stack.BackendStack.LAMBDA_ASSET_PACKAGES`，逐项经 `find_spec` 定位；单文件模块按原名置于根）。**不打包 `gherkai_cli`**（Lambda 侧不需要 argparse/render，ADR 0016「演进」节）；**boto3 由 Lambda runtime 自带、不打包**。

两条硬约束：

- **来源必须是「已安装包」，不是仓库相对路径、也不是联网 `pip install`**（ADR 0037 决策 6）。相对路径只在 monorepo 里成立，wheel 用户的 site-packages 不具备该布局；联网安装在离线环境下不可用，且装到的是 PyPI 上的某个版本而非**运行中这一份**：dev 版不在 PyPI 上，contributor 部署自己的 dev 版会直接失败。
- **清单是手写的，因此须有一条真 import 的测试作护栏**：`typing_extensions` 是 `gherkin-official>=42` 的传递依赖（`gherkin/parser_types.py` 无条件 import 它），旧的 `pip install --target` 会一并安装该依赖，改为「按名复制」后被漏掉：单测全绿，而真 synth 出的 asset 在 import 时即 `ModuleNotFoundError`。现在 `tests/test_lambda_asset.py::test_asset_imports_with_only_stdlib_beside_it` 在**剥离 site-packages 的子进程**里真 import asset，新增或更换依赖时它是判据。

asset 落在 `gherkai deploy` 的临时工作目录（`GHERKAI_LAMBDA_ASSET_DIR`，命令结束即删除），不再写进仓库或包目录。

## 资源侧的硬约束（改动前必读）

以下每条都不会在单测中直接失败：违约通常要到部署期、RunTask 或回收时才暴露，改动前须先确认约束仍成立。

- **DDB `{prefix}runs` 的稀疏 GSI `status-index`**：只有 STATE item 有顶层 `status`，投影含 `worker_task_def_arns`，供 worker revision 清理的「在跑 run 安全阀」`Query`（ADR 0038）。
- **S3 lifecycle `expire-job-in` 按对象 tag `gherkai=job-in`**（7 天）而非 key 前缀：job-in 的 key 里 `run_id` 在中间，纯前缀 filter 无法精确匹配，且会误删判定真值与报告。tag 由编排进程打（worker task role 因此不需要 `s3:PutObjectTagging`，ADR 0033）。
- **ECR 不设任何 lifecycle 规则**：重推同名 variant 会使旧 tag 变为 untagged，而在跑 run 的旧 task-def revision 仍按 digest 引用该镜像层，untagged 过期规则会静默删除它（ADR 0038 护栏；代价是永久留一层 untagged，回收与 `delete-worker` 同批设计）。
- **SSM 部署戳是 stack 资源**、不是命令事后 `put_parameter`：随部署事务一起提交或回滚，回滚后不留错值（ADR 0037 决策 6）。参数族（都在 `/{prefix}backend/*`）：`version`（后端版本戳，供提交侧的版本 skew 比对，决策 7）、`vpc`（生效 VPC 档，供档比对）、`subnets` / `security-groups`（cli 读）、`worker-template/<engine>`（stack 写的模板 revision ARN，`Ref` 返回带 revision）、`worker-image/<engine>/<版本>-<variant>`（JSON：`template_arn` / `revision_arn` / `digest` / `pushed_at`，`push-worker` 写）、`worker-default`（默认 variant 名）。**退休时刻与血缘不进 SSM**，以 task-def 的 tags 承载（随 revision 一同建立与消失，清理对账只看一处）。`vpc` 对 `new` 档记成 `new:<所建 vpc-id>`（带出所建 id 以便回溯核对）；部署戳与档**有意不 RETAIN**：保留只会让下次 deploy 读到已消失环境的档与版本。
- **`_worker_subnet_ids` 是「优先公有子网、无则回落私有」的唯一落点**：三个消费者（SSM `subnets`、reconciler 与 kicker 的 `SUBNETS` env）最终写入同一个 `awsvpcConfiguration`，此前曾有三份复刻：单侧改动会使 cli 与 Lambda 起的 task 落进不同子网，且只在 RunTask 时暴露；合成测试比对三者恒等作护栏。真私有隔离（NAT / VPC endpoint）留 backlog，改动时须同步 `_worker_subnet_ids` 与 cli 的 `assignPublicIp`（跨组件联动）。
- **worker task role 的模型权限不 pin 具体 model-id**（`stack._grant_task_role`，IAM 表在 ADR [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）：Midscene 侧 `bedrock:InvokeModel` 的资源共三条：`arn:aws:bedrock:*::foundation-model/*`（account 段按 AWS 惯例为空）、本账户 `inference-profile/*`（GPT 系经跨区 inference profile 调用，须同时放行 profile 与它路由到的模型 ARN）、本账户 `project/default`（OpenAI 系模型在 bedrock-runtime 端点上按模型卡还要求它，IAM 模拟器实证前两条覆盖不到）。模型是运行期选择（改镜像 ENV 即换，ADR [0044](../docs/adr/0044-engine-model-selection-and-override.md)），pin 具体 ARN 会让换模型变成重部署。Nova 侧收窄到本账户/region 的 `nova-act:workflow-definition/*` 与其 `workflow-run/*`（definition 名段放开：名字定义在 worker code 中，不应进入 IaC）。两引擎共享的 AgentCore 浏览器权限分为两条 statement：一条把 `StartBrowserSession` / `StopBrowserSession` / `GetBrowserProfile` 收窄到系统默认 browser（ARN **account 段是字面量 `aws`**、不是客户账户）与本账户 `browser-profile/*` 这两个资源；另一条覆盖四个 SAR 无资源类型的动作、保留 `*`，这是结构性的，不是待收窄项。Nova 侧另单授一条 `SaveBrowserSessionProfile`，资源与上述两个相同。
- **`--stop-timeout` 的 120s 上限是 Fargate 平台硬限**，>120 会在部署期被 ECS 拒绝，故命令/synth 期即 fail-fast 并明确说明这是平台限制（Nova 的 grace 下限 150s > 120s 这一冲突受限于这条硬上限，见 ADR [0032](../docs/adr/0032-fargate-execution-environment.md)）。

## worker 镜像命令族

`gherkai deploy` 的四步（全部幂等，重跑收敛，ADR 0038）：① 登记模板 revision ARN 到 SSM（随 cdk 事务）→ ② 从 GHCR 同步当前版本基底、推送为 `<版本>-base` → ③ 默认指针缺失则初始化为 `base`（已存在则保持不变）→ ④ 模板发生变化时用新模板 + 已记录的 digest 重派生既有 variant，末尾执行一次清理 pass。cdk 成功而后三步失败 → 退 1（不是 2：账户已被改动）。

`push-worker` 流程（细节与理由见 ADR 0038「push-worker 流程」）：版本 skew 前置（CLI **新于**后端 → 退 2，无放行入口）→ `inspect` 校验存在与架构 → ECR 登录 → tag + push → **推送后**再 `inspect` 取 digest（本地未推送的镜像没有 registry digest，`.Id` 是 config digest：注册可以通过，直到 RunTask 才报 `manifest unknown`）→ 按（模板 ARN、digest）查重 / 复用孤儿 / 否则从模板注册新 revision（血缘 tags：`gherkai:variant|version|digest|template`）→ 写 SSM 映射 → 旧 revision 打 `gherkai:retired-at` + 执行一次清理 pass。清理两道闸的判据见 [`docs/internals/cloud-backend-carriers.md`](../docs/internals/cloud-backend-carriers.md)（静默期数值以 `workers.RETIRE_QUIET_PERIOD` 常量为真源、文档不复写）；本包侧另有三条实现事实：仍被任何版本的 `worker-image` 映射引用的 revision 一律保留（与在跑 run 引用并列的安全阀），映射读取不完整时放弃本趟回收（读不全则无法判断哪些 revision 仍被引用），回收失败只输出警告、留给下次 pass。

- **`--container-engine` 为其它容器引擎预留**：当前只实装 `docker`（取值顺序 `--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`），其它名字退 2、不静默回落（`container.resolve_container_engine`）。名字不被识别 = 纯参数问题、绝不改动账户；已安装但不可用 / 未安装 = 只警告（且只对纯发行版警告：dev/post/本地段版本原本就不经过同步基底这一步，ADR 0038），退码语义归 cdk 之后的四步。容器引擎探活警告排在 `--vpc` 校验之后：缺 `--vpc` 会直接退 2，先输出两行警告会掩盖真正的失败原因。
- **`delete-worker` 是占位**：退 2 并说明推迟的是回收策略（旧版本 variant 的 ECR tag / untagged 层），重议条件见 ADR 0038。
- 子动词只声明在 `deploy` 上、不声明在 `destroy` 上（理由见 `cli.py._declares_worker_subverbs`）。

## 本地验证（不访问 AWS）

```bash
uv run pytest -q deploy_aws/tests   # stack 合成断言 + Provider + Lambda asset + Lambda handler + worker 镜像族 + 容器引擎 + skill 的 deploy/destroy 旋钮文案（test_skill_deploy_tokens.py）
```

默认档不访问 AWS、也不需要 docker，但需要 PATH 上有 Node ≥ 22：`tests/synth_fixture.py` 真调 cdk 合成，`aws_cdk` 是 jsii 绑定、构造 App 即起 node 子进程（缺 node 时报错落在 jsii 内部，难以看出真实原因）。真 docker 的三条（`tests/test_container.py` 末尾）在缺 docker daemon 或缺本地 `gherkai-worker-novaact:dev` 镜像时自动 skip，其余全绿。
本包是根 uv workspace 的成员，一次 `uv sync` 即装齐依赖；命令在仓库任意位置都可运行（`uv run gherkai …`）。

- `tests/synth_fixture.py`：真调 cdk 合成一次模板供多个测试共用（合成耗时，不在每个用例中各合成一次）。
- worker 镜像族分两层：`tests/test_workers.py` 用 moto（SSM/ECS/ECR/DDB）+ 假容器引擎验**编排**（步序、幂等查重、血缘 tags、清理两道闸）；`tests/test_container.py` 末尾三条用**真 docker** 验 mock 覆盖不到的引擎事实（本地未推送镜像 `RepoDigests` 为空、arm64 镜像被架构判据拒绝），无 docker 时自动 skip。
- **真 ECR push / RunTask 拉起已注册的 revision / VPC 档比对与 skew 比对的真账户一侧不在单测里**：按「绿≠对」，这些结论依赖被 mock 掉的真实行为，改动这些路径时按 CLAUDE.md「代码纪律」升级到真跑。

## 设计文档

- [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)：IaC 定位、资源清单、命名契约、preflight、IAM 最小权限表、RETAIN 语义。
- [0034](../docs/adr/0034-detached-batch-reconciler.md)：无状态跑批的事件链、并发 cap、job timeout。
- [0037](../docs/adr/0037-distribution-and-packaging.md)：包化与 `gherkai deploy` 命令面、版本单旋钮与 skew 检查（逐档判序见 [`cli/DEVELOPMENT.md`](../cli/DEVELOPMENT.md) 的版本 skew 一节）、Lambda asset 来源、CDK 查询缓存。
- [0038](../docs/adr/0038-worker-image-delivery.md)：基底 / variant / 默认指针、push-worker 流程、显式 revision、清理与权限增量。
- [0032](../docs/adr/0032-fargate-execution-environment.md)：Fargate 执行环境的中断/grace 韧性。

五个载体（stack / Lambda asset / 基底镜像 / variant 镜像 / SSM 参数）各自何时生效、一次改动要传播到哪几处，见 [`docs/internals/cloud-backend-carriers.md`](../docs/internals/cloud-backend-carriers.md)；参与开发的总入口（环境、测试、发布链、文档地图）见根 [`CONTRIBUTING.md`](../CONTRIBUTING.md)。
