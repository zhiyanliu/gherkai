# gherkai-deploy-aws — contributor 手册

> 使用者文档是同目录 [`README.md`](./README.md)（它**逐字**作为 `gherkai-deploy-aws` 的 PyPI 长描述发出去，只讲装/用）。本文件给 contributor：包内布局、设计约束、本地验证、以及几条真踩出来的规矩。**权威在 ADR + code**，本文件只做导航与「怎么改不踩雷」。

## 包定位与发现面

- 发行名 `gherkai-deploy-aws` · import 名 `gherkai_deploy_aws`（ADR [0037](../docs/adr/0037-distribution-and-packaging.md) 决策 2a/6）；随 CLI 的 `[deploy-aws]` extra 装，只有部署方需要（决策 2c）。
- 经 entry point group `gherkai.deploy` 的 `aws` 项被 CLI 发现（`gherkai_deploy_aws.cli:Provider`）：装了一个 provider 时无需 `--provider`。
- **「clone repo + 裸 `cdk deploy`」不再是部署形态**（ADR 0037 决策 6）：那条路要求源码树在手、相对路径拼 Lambda asset、且把 vpc context 的坑外露给每个使用者。现在 IaC 随 wheel 分发，`gherkai deploy` 在临时工作目录生成 `cdk.json`（`app` 指向 `python -m gherkai_deploy_aws.app`）后调 cdk CLI。想看模板走 `gherkai deploy --synth-only DIR`，**别裸跑 `python -m gherkai_deploy_aws.app`**——它缺 `-c version=` 会 fail-fast，这是有意的。

## 模块布局

| 文件 | 职责 |
|---|---|
| `cli.py` | `Provider`：命令面 flag、context 拼装、`cdk.json` 生成、cdk CLI 调用、VPC 档三态比对、Node 前置检查、worker 镜像子动词分派 |
| `stack.py` | `BackendStack`：全部云资源（含 `_reconcile_lambdas` 事件链、`_build_lambda_asset`、`_worker_subnet_ids`） |
| `app.py` | cdk app 入口（`cdk.json` 的 `app` 指向它），按 context 建 stack |
| `names.py` | 命名契约，**直接 re-export** `runtime/gherkai_runtime/names.py`（见下「命名真源」） |
| `workers.py` / `container.py` | worker 镜像族命令的实现 / 容器引擎抽象 |
| `lambdas/reconciler.py`、`lambdas/exit_observer.py` | 三个 Lambda 的 handler 源（打包时摊在 asset zip 根，故平级 import 成立） |
| `tests/` | 见下「本地验证」 |

**唯一接缝的硬约束**：**CLI 皮绝不 import `aws_cdk`**（jsii 绑定，import 即起 node 子进程，ADR 0037 决策 6）。故 `cli.py` 自身也只 import 标准库 + `gherkai_runtime` + 本包 `names`（零 `aws_cdk`）；`stack.py` / `app.py` 只经 cdk CLI 起的子进程触达。改动时别把 `aws_cdk` 漏进 `cli.py` 的 import 面——`gherkai --help` 的启动代价挂在这条上。

**`--require-approval` / `--allow-vpc-change` 是有意的两层声明**：CLI 皮先声明 provider 中立版（provider 缺席时 `deploy --help` 不残缺），`Provider.add_arguments` 再声明带 AWS 语义的版本（前者能 `choices` 校验 cdk 三档、后者措辞点名 VPC 档三态）；皮的 subparser 开 `conflict_handler="resolve"`，同名以后贴的为准。两层不是重复真源，是「中立占位 + provider 精确化」。`Provider` 另经 `getattr` 容忍它们彻底缺席（别的皮）：缺 `--allow-vpc-change` = 一律不放行（fail-closed）。

## 命名真源

`names.py` 直接 re-export `runtime/gherkai_runtime/names.py`——曾因「CDK 独立工程、不能 import cli」复刻过一份、须两处同步改，共享层抽为平级产品本体包后复刻消除（ADR [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)「演进」节 / [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）。stack 名的推导（`names.stack_name`，`BackendStack-<prefix 去尾横线>`）同样单一真源：`app.py` 建 stack 用它，`cli.py` 做 VPC 档三态比对时 `DescribeStacks` 用同一个名。

## 事件驱动推进（无状态跑批）

`submit` 提交完即走、进程不驻留，run 的推进由云上事件链自我驱动（`stack._reconcile_lambdas`，ADR [0034](../docs/adr/0034-detached-batch-reconciler.md)）。同步 `run` 路径不消费 Stream、仍走 Query 轮询，与此链解耦（ADR [0024](../docs/adr/0024-worker-core-protocol.md)）。

- **三个 Lambda**（同一份打包 asset，`handler` 入口不同）：
  - `{prefix}kicker`（踢启器）：`{prefix}runs` 表 Stream 的 **INSERT** 触发（`submit` 的 `create_run` 写 definition）→ 冷启动起首批 task；也被 cli `status --wait` 直接 invoke 做 kickoff。handler=`reconciler.kicker_handler`。
  - `{prefix}reconciler`：`{prefix}events` 表 Stream 触发（worker `PutItem` 执行事件 / 退出观察者写 `task_exited`）→ `reconcile.tick` 推进 + finalize 聚合。handler=`reconciler.handler`。
  - `{prefix}exit-observer`（退出观察者）：ECS Task `STOPPED` 事件触发 → 写 `task_exited` 事件（薄；只 events 表 `PutItem`）。handler=`exit_observer.handler`。
  - kicker/reconciler 共享起 task 的全套权限与装配（`RunTask` / `PassRole` / 表桶读写 + `SUBNETS` / `SECURITY_GROUPS` / `MAX_CONCURRENCY`，另加 `ssm:GetParameter*` 于 `/{prefix}backend/*`）；分工 = kicker「让 run 动起来」、reconciler「推着走」。`MAX_CONCURRENCY`（当前 `8`，**两侧须同值**）是部署侧 per-run 并发 cap、不是真源——每个 run 并行几个 job 由提交侧 `submit --max-concurrency` 随 definition 声明，推进器取 `min(声明, cap)`；cap 在此是因为 task 计入的是部署方账单，local 档无 cap（ADR 0034 机制四）。
- 两个推进器起 task 用 **definition 里解析好的显式 task-def revision**（不是 family 最新 ACTIVE——那会让任何一次 push 劫持别人的 variant）。没有该字段的旧 definition（升级窗口内在跑的 run / 旧 CLI 提交的 run）走**兼容回落**：读 SSM `worker-default` + `worker-image/<engine>/<后端版本>-<默认 variant>` 解析 revision——这就是它们要 SSM 读权限的原因。**不回落模板 revision**：模板的镜像栏是 `latest` 占位，全新 prefix 上根本拉不到（ADR [0038](../docs/adr/0038-worker-image-delivery.md) 列为被拒方案）。
- **EventBridge rule `{prefix}ecs-stopped`**：按 `source=aws.ecs` + `ECS Task State Change` + `lastStatus=STOPPED` + 本 cluster 的 `clusterArn` 过滤（不误触别的负载）→ 打到 `{prefix}exit-observer`。
- **Event source mappings**：`{prefix}events` 表 Stream → reconciler；`{prefix}runs` 表 Stream → kicker（**带 `eventName=INSERT` ∧ `detached=true` filter**，只让 detached 的 `create_run` 触发冷启动；reconciler 之后写 runs 表的 `MODIFY` 不自触发放大，ADR 0034 把「无 filter」列为被拒方案）。
- **job timeout 到点触发器**（ADR 0034「job timeout」节）：IAM role `{prefix}timeout-scheduler`（`scheduler.amazonaws.com` assume、只准 invoke kicker——授权写**确定性 kicker ARN 串**而非资源引用，免 role↔function 互引成环）+ EventBridge Scheduler 的 one-time schedule 名字空间 `{prefix}job-timeout-*`（default group，`ActionAfterCompletion=DELETE` 到点自删、idle 零成本）+ 注给推进器的 `KICKER_ARN` / `SCHEDULER_ROLE_ARN` env。改 prefix 时这两个名字随之变。

## Lambda 打包（`stack._build_lambda_asset`）

三个 Lambda 共用一个 asset：本包 `gherkai_deploy_aws/lambdas/` 的两个 handler 源摊在 **zip 根**（故 `exit_observer` 里 `from reconciler import …` 这条平级 import 成立；也因此 handler 源不做成本包的子包）+ 从**当前 venv 已安装位置**复制的 `gherkai_runtime` / `gherkai_core` / `gherkin` / `packaging` / `typing_extensions`。**不打 `gherkai_cli`**（Lambda 不背 argparse/render，ADR 0016「演进」节）；**boto3 由 Lambda runtime 自带、不打**。

两条踩出来的规矩：

- **来源必须是「已安装包」，不是仓库相对路径、也不是联网 `pip install`**（ADR 0037 决策 6）。相对路径只在 monorepo 里成立，wheel 用户的 site-packages 没那种布局；联网装会在离线环境断，且装到的是 PyPI 上的某个版本而非**运行中这一份**——dev 版根本不在 PyPI 上，contributor 部署自己的 dev 版会直接断。
- **清单是手写的，所以要有一条真 import 的测试守着**：`typing_extensions` 是 `gherkin-official>=42` 的传递依赖（`gherkin/parser_types.py` 无条件 import 它），旧的 `pip install --target` 顺带装上、改成「按名复制」后就漏了——单测全绿，真 synth 出的 asset 一 import 就 `ModuleNotFoundError`。现在 `tests/test_lambda_asset.py::test_asset_imports_with_only_stdlib_beside_it` 在**剥掉 site-packages 的子进程**里真 import 一遍 asset，加/换依赖时它是判据。

asset 落进 `gherkai deploy` 的临时工作目录（`GHERKAI_LAMBDA_ASSET_DIR`，命令用完即删），不再写进仓库或包目录。

## 资源侧几处不能放松的

- **DDB `{prefix}runs` 的稀疏 GSI `status-index`**：只有 STATE item 有顶层 `status`，投影含 `worker_task_def_arns`，供 worker revision 清理的「在跑 run 安全阀」`Query`（ADR 0038）。
- **S3 lifecycle `expire-job-in` 按对象 tag `gherkai=job-in`**（7 天）而非 key 前缀：job-in 的 key 里 `run_id` 在中间，纯前缀 filter 框不住且会误伤判定真值与报告。打 tag 在编排进程做（worker task role 因此不需要 `s3:PutObjectTagging`，ADR 0033）。
- **ECR 不设任何 lifecycle 规则**：重推同名 variant 会把旧 tag 顶成 untagged，而在跑 run 的旧 task-def revision 正按 digest 指着那一层，untagged 过期规则会静默删掉它（ADR 0038 护栏；代价是永久留一层 untagged，回收与 `delete-worker` 同批设计）。
- **SSM 部署戳是 stack 资源**、不是命令事后 `put_parameter`——与部署事务同生死、回滚不留错值（ADR 0037 决策 6）。参数族（都在 `/{prefix}backend/*`）：`version`（后端版本戳，供 skew 三态比对，决策 7）、`vpc`（生效 VPC 档，供档比对）、`subnets` / `security-groups`（cli 读）、`worker-template/<engine>`（stack 写的模板 revision ARN，`Ref` 返回带 revision）、`worker-image/<engine>/<版本>-<variant>`（JSON：`template_arn` / `revision_arn` / `digest` / `pushed_at`，`push-worker` 写）、`worker-default`（默认 variant 名）。**退休时刻与血缘不进 SSM**，以 task-def 的 tags 承载（与 revision 同生死、清理对账只看一处）。 `vpc` 对 `new` 档记成 `new:<所建 vpc-id>`（带出所建 id 以便回溯核对）；部署戳与档**有意不 RETAIN**——留着只会让下次 deploy 拿到已消失环境的档/版本。
- **`_worker_subnet_ids` 是「优先公有子网、无则回落私有」的唯一落点**：三个消费者（SSM `subnets`、reconciler 与 kicker 的 `SUBNETS` env）最终喂同一个 `awsvpcConfiguration`，曾三份复刻——单侧改动 = cli 与 Lambda 起的 task 落进不同子网，且只在 RunTask 时才暴露；合成测试比对三者恒等作护栏。真私有隔离（NAT / VPC endpoint）留 backlog，改它要同步 `_worker_subnet_ids` 与 cli 的 `assignPublicIp`（跨组件联动）。
- **`--stop-timeout` 的 120s 上限是 Fargate 平台硬限**，>120 会在部署期被 ECS 拒，故命令/synth 期就 fail-fast 并点名这是平台限制（Nova 的 grace 下限 150s > 120s 这个冲突正卡在这条硬上限上，见 ADR [0032](../docs/adr/0032-fargate-execution-environment.md)）。

## worker 镜像命令族

`gherkai deploy` 的四步（全部幂等，重跑收敛，ADR 0038）：① 登记模板 revision ARN 到 SSM（随 cdk 事务）→ ② 从 GHCR 同步当前版本基底、推成 `<版本>-base` → ③ 默认指针缺失则初始化为 `base`（已存在则不动）→ ④ 模板变了就用新模板 + 已记录的 digest 重派生既有 variant，末尾跑一次清理 pass。cdk 成功而后三步失败 → 退 1（不是 2：账户已被改动）。

`push-worker` 流程（细节与理由见 ADR 0038「push-worker 流程」）：版本 skew 前置（CLI **新于**后端 → 退 2，无放行口）→ `inspect` 校验存在与架构 → ECR 登录 → tag + push → **推送后**再 `inspect` 取 digest（本地未推送的镜像没有 registry digest，`.Id` 是 config digest、注册能过而 RunTask 才 `manifest unknown`）→ 按（模板 ARN、digest）查重 / 复用孤儿 / 否则从模板注册新 revision（血缘 tags：`gherkai:variant|version|digest|template`）→ 写 SSM 映射 → 旧 revision 打 `gherkai:retired-at` + 跑一次清理 pass。

- **`--container-engine` 是留的口子**：这一期只实装 `docker`，别的名字退 2、不静默回落（`container.resolve_container_engine`）。名字不认 = 纯参数问题、绝不动账户；装了但不可用 / 没装 = 只警告，退码语义归 cdk 之后的四步。探活警告有意排在 `--vpc` 校验之后——缺 `--vpc` 会直接退 2，先打两行 docker 警告只会盖住真因。
- **`delete-worker` 是占位**：退 2 并说明押后的是回收策略（旧版本 variant 的 ECR tag / untagged 层），重议条件见 ADR 0038。
- 子动词只挂 `deploy`、不挂 `destroy`（理由见 `cli.py._declares_worker_subverbs`）。

## 本地验证（不碰 AWS）

```bash
uv run pytest deploy_aws/tests -q   # stack 合成断言 + Provider + Lambda asset + Lambda handler + worker 镜像族
```

本包是根 uv workspace 的成员，一次 `uv sync` 即装齐；命令从仓库任意位置都可跑（`uv run gherkai …`）。

- `tests/synth_fixture.py`：真调 cdk 合成一次模板供多个测试共用（合成慢，别在每个用例里各合一遍）。
- worker 镜像族分两层：`tests/test_workers.py` 用 moto（SSM/ECS/ECR/DDB）+ 假容器引擎验**编排**（步序、幂等查重、血缘 tags、清理两道闸）；`tests/test_container.py` 末尾三条用**真 docker** 验 mock 不出来的引擎事实（本地未推送镜像 `RepoDigests` 为空、arm64 镜像被架构判据拒），无 docker 时自动 skip。
- **真 ECR push / RunTask 拉起注册出来的 revision / VPC 档三态与 skew 三态的真账户半边不在单测里**——「绿≠对」：这些结论依赖被 mock 掉的真实行为，改动这些路径时按 CLAUDE.md「代码纪律」升级到真跑。

## 设计文档

- [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)：IaC 定位、资源清单、命名契约、preflight、IAM 最小权限表、RETAIN 语义。
- [0034](../docs/adr/0034-detached-batch-reconciler.md)：无状态跑批的事件链、并发 cap、job timeout。
- [0037](../docs/adr/0037-distribution-and-packaging.md)：包化与 `gherkai deploy` 命令面、版本单旋钮与 skew 三态、Lambda asset 来源、CDK 查询缓存。
- [0038](../docs/adr/0038-worker-image-delivery.md)：基底 / variant / 默认指针、push-worker 流程、显式 revision、清理与权限增量。
- [0032](../docs/adr/0032-fargate-execution-environment.md)：Fargate 执行环境的中断/grace 韧性。
