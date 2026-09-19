# 云端后端：分工、交付清单、variant 镜像与升级

本文给 agent 在云端后端要知道的事。资源清单、费用、VPC 三档细节与权限清单以用户指南的云端后端页为准：
https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md 。

## 1 分工

| 谁 | 做什么 | agent 的角色 |
|---|---|---|
| 部署方 | `gherkai deploy` 建 / 改后端，`gherkai deploy push-worker` 推 worker 镜像，`gherkai destroy` 拆，管 IAM 与网络 | **不自己运行**。用 `doctor` 判缺什么，把命令与前置清单交给人 |
| 测试开发 | 写确定性 step，构建定制 worker 镜像，交部署方推送 | 可以运行（不改 IAM） |
| QA / CI | `submit --backend cloud` → `status --wait` → `explain` | 直接运行 |

## 2 交给部署方的清单

前置：`uv tool install 'gherkai[deploy-aws]'`；Node ≥ 22 在 PATH；容器引擎 docker 可用（要拉官方 worker 基础镜像并推进 ECR）；凭证有云端写权限（CloudFormation、DynamoDB、S3、ECS、ECR、Lambda、EventBridge、VPC、日志组、IAM 建角色与 PassRole）；region 已定。

```bash
gherkai deploy --bootstrap                                  # 每个 account+region 首次一次
gherkai deploy --diff --vpc default --prefix gherkai-       # 先看变更集（尤其网络 / IAM），每次 deploy 前
gherkai deploy --vpc default --prefix gherkai-              # 真部署 / 更新，幂等
gherkai deploy --synth-only ./out --vpc default             # 只导模板给自己的审批流水线，不碰账户
gherkai destroy --vpc default --prefix gherkai- --yes       # 拆栈；表 / 桶 / 镜像仓库保留
```

- `--vpc` **必给、无隐式默认**（只有 `--bootstrap` 不需要）：`default`（账户默认 VPC）/ `new`（新建，2 可用区、零 NAT）/ `vpc-<id>`。生效的档记在后端，下次给错会退 2；确认要换网络时加 `--allow-vpc-change` 放行一次。
- `--prefix`（默认 `gherkai-`）是全部云资源的命名空间，**必须与 `run` / `submit` / `status` / `explain` 的 `--prefix` 一致**。换 prefix = 换一套独立环境（`prod-` / `stage-`），闲置成本近零。
- 其它：`--require-approval never|any-change|broadening`（IAM 变更要不要人过目）、`--stop-timeout N`（worker 容器停止宽限秒；默认值与上限见 `--help`，上限是平台限制、更大的值在命令期就被拒；云端对应本机 `run --grace`）、`--container-engine 名`（默认 docker）、`--refresh-context`、`--region` / `--profile`。
- 退出码：0 成功；2 前置 / 校验失败（Node 缺失、VPC 档不符、容器引擎名不认、`push-worker` 架构或版本不符）；1 账户可能已被改动，两种来源——cdk 自身失败（报错码多为 1、原样透传，处置看 cdk 输出），或 cdk 已成功而 worker 镜像步骤失败（重新运行 `gherkai deploy` 幂等收敛）；`destroy` 没有镜像步骤，它的 1 只来自 cdk；其余原样透传 cdk。

建出来的东西：DynamoDB 两张表（run 状态、事件）、S3 桶（判定结果、报告、引擎产物）、ECS 集群与每引擎一个 Fargate task 定义、每引擎一个 ECR 仓库、三个 Lambda 与调度规则（让 `submit` 的 run 在云上自我推进）、按 `--vpc` 档的子网与安全组、每引擎最小权限角色、SSM 参数（版本戳、VPC 档、worker 镜像映射与默认指针）。`submit --backend cloud` 提交的一个 run，并行 job 数 = min(提交时 `--max-concurrency`, 部署侧上限 8)：超过上限时 `submit` 打印一行提示、本 run 按上限并行。`run --backend cloud` 的并行度就是 `--max-concurrency`，不受这个上限约束。

## 3 使用方一条线

```bash
gherkai doctor --backend cloud --prefix gherkai-                    # 凭证、后端版本、资源、variant 能否解析
gherkai plan features/x.feature                                     # 本机用例预检；确定性标注只代表本机 steps
RUN_ID=$(gherkai submit features/x.feature --backend cloud --prefix gherkai-)
gherkai status "$RUN_ID" --backend cloud --prefix gherkai- --wait   # 退出码即判定
gherkai explain "$RUN_ID" --backend cloud --prefix gherkai-         # 失败证据；截图是 S3 地址
```

`status` / `explain` 的 `--backend` / `--report-dir` / `--prefix` 与 `submit` 逐字一致，否则退 2 说找不到 run（`--report-dir` 在 cloud 后端下是云端的报告前缀，默认 `reports`）。`--region` / `--profile` 与本机命令同名同义。

## 4 variant 与 `push-worker`：本机 steps 怎么进云端

| 概念 | 是什么 | 谁写 |
|---|---|---|
| 基础镜像 | 官方镜像 `ghcr.io/zhiyanliu/gherkai-worker-<engine>:X.Y.Z`，零使用方内容 | 官方发布；`gherkai deploy` 同步成 `<版本>-base` |
| variant | 一套具名的确定性 step 集 = 一个定制镜像，ECR tag `<CLI 版本>-<variant 名>`，对应一个 task 定义 revision（按 digest 引用） | 你的 `push-worker` |
| 默认指针 | 提交时不给 `--worker-variant` 用哪个（部署级一个） | `deploy` 初始化为 base；`push-worker --set-default` 改指 |

云端 worker 读不到本机 `steps/`，`--steps-dir` 在 `--backend cloud` 下只警告不生效。步骤要构建进镜像（构建不归 gherkai，三行 Dockerfile）：

```dockerfile
FROM ghcr.io/zhiyanliu/gherkai-worker-novaact:<你的 CLI 版本>   # 版本须与 gherkai --version 一致
COPY steps/ /app/steps
ENV GHERKAI_STEPS_DIR=/app/steps
```

```bash
docker build --platform linux/amd64 -t acme-novaact:login .        # 必须带 --platform，Fargate 是 X86_64
gherkai deploy push-worker acme-novaact:login --engine novaact --variant login --prefix gherkai-
gherkai deploy push-worker acme-midscene:login --engine midscene --variant login --prefix gherkai-   # 两引擎各推一次
gherkai deploy push-worker acme-novaact:common --engine novaact --variant common --set-default        # 顺手改默认指针
gherkai deploy list-workers --prefix gherkai-                      # 看有哪些 variant、默认指针；--json 机读
gherkai submit features/x.feature --backend cloud --prefix gherkai- --worker-variant login
```

- arm Mac 上不带 `--platform linux/amd64` 会 build 出 arm64，容器启动期才报 exec format error；`push-worker` 会在推之前查架构与版本、不符退 2。
- 提交时 `--worker-variant` 被解析成本 run 各引擎的精确 revision 写进提交记录：一个 run 内镜像固定，别人重推同名 variant 不影响正在运行的 run。某引擎缺该 variant 即退 2、不回落默认。
- **测试开发 → QA / CI 的交接**：本机新写或改了确定性 step，`plan` 的标注会变，但云端不会，直到重新 build + `push-worker`。cloud 后端「改了 steps 不推镜像等于没改」，且没有任何显式失败提醒。
- `gherkai deploy delete-worker` 尚未提供（命令存在、会说明）。

## 5 升级顺序

后端记一个版本戳，cloud 命令动资源前比对：CLI 比后端新 → 退 2、无放行开关；旧 → 警告。所以升级是三步，顺序不能反：

1. 部署方 `uv tool upgrade gherkai`。
2. 立刻 `gherkai deploy --vpc <同档> --prefix <同前缀>`：新模板 + 新版本基础镜像进 ECR + 已有 variant 按新模板重派生。中间窗口里提交退 2 是预期。
3. 有自定义 variant 的：从新版本基础镜像重新 build、`push-worker`。其他人再升自己的 CLI。

不想动本机安装的部署方可用 `uvx --from 'gherkai[deploy-aws]==X.Y.Z' gherkai deploy` 先升后端。

## 6 多环境与清理

- 多环境靠 `--prefix`：`prod-` / `stage-` 各一套后端，互不影响；所有 cloud 命令带同一个 prefix。
- `gherkai destroy` 之后两张 DynamoDB 表、S3 桶、两个 ECR 仓库**保留、需手动删**（防误删数据）。不手动删则同 prefix 重新 deploy 会因资源已存在而冲突。worker 镜像映射与默认指针也不随 destroy 删，ECR 留着则重建后照样能用。命令样例见部署方说明页「拆除与清理」节。

## 7 `--expose-local` 在 cloud 后端的例外

`submit --backend cloud --expose-local <原始 origin>` 时隧道由**本机**的守护进程持有，本机须保持开机联网到 run 终态，这是「提交后关机也会运行到结束」的唯一例外。`--tunnel-ttl S` 是守护进程的兜底 TTL（默认 = 本批各 job 预算之和 + 启动余量），到点无条件拆隧道，调小可能在 run 未完时断隧道。
