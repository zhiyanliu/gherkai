# 云端后端：分工、交付清单、variant 镜像与升级

本文给 agent 在云端后端要知道的事。资源清单、费用、VPC 三种取值的细节与权限清单以用户指南的云端后端页为准：
https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md 。

## 1 分工

| 谁 | 做什么 | agent 的角色 |
|---|---|---|
| 部署方 | `gherkai deploy` 建 / 改后端，`gherkai deploy push-worker` 推送并注册 worker 镜像，`gherkai destroy` 拆，管 IAM 与网络 | `deploy` / `destroy` **不自己运行**：用 `doctor` 判缺什么，把命令与前置清单交给人；`push-worker` 不改 IAM，可以运行 |
| 测试开发 | 写确定性 step，构建定制 worker 镜像，交部署方推送；一人兼任两个角色时自己用 `push-worker` 推送 | 可以运行 |
| QA / CI | 依次执行 `submit --backend cloud`、`status --wait`、`explain` | 直接运行 |

## 2 交给部署方的清单

前置：`uv tool install 'gherkai[deploy-aws]'`；Node ≥ 22 在 PATH；容器引擎 docker 可用（要拉官方 worker 基础镜像并推进 ECR）；凭证有云端写权限（CloudFormation、DynamoDB、S3、ECS、ECR、Lambda、EventBridge、VPC、日志组、IAM 建角色与 PassRole、SSM 读写 `/<prefix>backend/*`、Device Farm 在 us-west-2 的 `ListProjects` / `GetProject` / `CreateProject`（找到已有的设备项目或新建一个）、`sts:GetCallerIdentity`）；region 已定。缺 Device Farm 这三项时部署照常完成并给出警告：后端已记录项目时沿用记录；没有记录，或记录的项目已被删除且无法找回或新建时，这套后端不启用设备支持，带设备目标的云端 run 提交时以退出码 2 结束。

```bash
gherkai deploy --bootstrap                                  # 每个 account+region 首次一次
gherkai deploy --diff --vpc default --prefix gherkai-       # 先看变更集（尤其网络 / IAM），每次 deploy 前
gherkai deploy --vpc default --prefix gherkai-              # 真部署 / 更新，幂等
gherkai deploy --synth-only ./out --vpc default             # 只导模板给自己的审批流水线，不碰账户
gherkai destroy --vpc default --prefix gherkai- --yes       # 拆栈；表 / 桶 / 镜像仓库与 Device Farm 项目保留
```

- `--vpc` **必给、无隐式默认**（只有 `--bootstrap` 不需要）：`default`（账户默认 VPC）/ `new`（新建，2 可用区、零 NAT）/ `vpc-<id>`。生效的取值记在后端，下次给错会以退出码 2 结束；确认要换网络时加 `--allow-vpc-change` 放行一次。
- `--prefix`（默认 `gherkai-`）是全部云资源的命名空间，**必须与 `run` / `submit` / `status` / `list-runs` / `explain` 的 `--prefix` 一致**。换 prefix 就是换一套独立环境（`prod-` / `stage-`），闲置成本近零。
- 其它：`--require-approval never|any-change|broadening`（IAM 变更要不要人过目）、`--stop-timeout N`（worker 容器停止宽限秒；默认值与上限见 `--help`，上限是平台限制、更大的值在命令期就被拒；云端对应本机 `run --grace`）、`--container-engine 名`（默认 docker）、`--refresh-context`、`--region` / `--profile`。
- 退出码：0 成功；2 前置 / 校验失败（Node 缺失、VPC 取值不符、容器引擎名不认、`push-worker` 架构或版本不符；读不到后端记录的 Device Farm 项目、记录不是合法的项目 ARN、Device Farm 里有不止一个名为 `<prefix>devices` 的项目，这几种都在动账户之前拦下；`--diff` 核对记录的项目时遇到限流、网络或服务端故障也以 2 结束、不输出变更集）；1 账户可能已被改动，三种来源——cdk 自身失败（它自己的退出码多为 1、原样透传，处置看 cdk 输出），cdk 已成功而 worker 镜像步骤失败（重新运行 `gherkai deploy` 幂等收敛），或部署 stack 之前找回或建立 Device Farm 项目时遇到权限以外的错误（限流、网络、服务端故障；stack 没有改动、项目可能已建立，重新运行 `gherkai deploy` 会按名称找回、不会重复建立）；`destroy` 没有镜像步骤，它的 1 只来自 cdk；其余原样透传 cdk。

建出来的东西：DynamoDB 两张表（run 状态、事件）、S3 桶（判定结果、报告、引擎产物）、ECS 集群与每引擎一个 Fargate task 定义、每引擎一个 ECR 仓库、三个 Lambda 与调度规则（让 `submit` 的 run 在云上自我推进）、按 `--vpc` 取值的子网与安全组、每引擎最小权限角色、SSM 参数（版本戳、VPC 取值、worker 镜像映射与默认指针、启用设备支持时的 Device Farm 项目 ARN）。stack 之外，deploy 还会在部署 stack 之前在 us-west-2 找回或新建 Device Farm 项目 `<prefix>devices`，供带设备目标的云端 run 建立远程访问会话；它不属于 stack，destroy 时保留（见第 6 节）。`submit --backend cloud` 提交的一个 run，并行 job 数为 min(提交时 `--max-concurrency`, 部署侧上限 20)：超过上限时 `submit` 打印一行提示、本 run 按上限并行。`run --backend cloud` 的并行度就是 `--max-concurrency`，不受这个上限约束。

## 3 使用方一条线

```bash
gherkai doctor --backend cloud --prefix gherkai-                    # 凭证、后端版本、资源、variant 能否解析、设备支持
gherkai plan features/x.feature                                     # 本机用例预检；确定性标注只代表本机 steps
RUN_ID=$(gherkai submit features/x.feature --backend cloud --prefix gherkai-)
gherkai status "$RUN_ID" --backend cloud --prefix gherkai- --wait   # 退出码即判定
gherkai explain "$RUN_ID" --backend cloud --prefix gherkai-         # 失败证据；截图是 S3 地址
```

`status` / `explain` 的 `--backend` / `--report-dir` / `--prefix` 与 `submit` 逐字一致，否则以退出码 2 结束、说找不到 run（`--report-dir` 在 cloud 后端下是云端的报告前缀，默认 `reports`）。`--region` / `--profile` 与本机命令同名同义。

没记下 run_id 时，`gherkai list-runs --backend cloud --prefix gherkai-` 列出这个后端里的 run（不读报告，不看 `--report-dir`）：只读，机器只需读权限，另要运行记录表索引上的 `dynamodb:Query` 与表上的 `dynamodb:BatchGetItem`，缺了交人补。清单为空多半是 `--prefix` / `--region` 与提交时不一致，提示行点名了它查的前缀、region 与表名。

## 4 variant 与 `push-worker`：本机 steps 怎么进云端

| 概念 | 是什么 | 谁写 |
|---|---|---|
| 基础镜像 | 官方镜像 `ghcr.io/zhiyanliu/gherkai-worker-<engine>:X.Y.Z`，零使用方内容 | 官方发布；`gherkai deploy` 同步成 `<版本>-base` |
| variant | 一套具名的确定性 step 集就是一个定制镜像，ECR tag `<CLI 版本>-<variant 名>`，对应一个 task 定义 revision（按 digest 引用） | 你的 `push-worker` |
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
gherkai deploy push-worker acme-novaact:common --engine novaact --variant common --set-default        # 同时改默认指针
gherkai deploy list-workers --prefix gherkai-                      # 看有哪些 variant、默认指针；--json 机读
gherkai submit features/x.feature --backend cloud --prefix gherkai- --worker-variant login
```

- arm Mac 上不带 `--platform linux/amd64` 会 build 出 arm64，容器启动期才报 exec format error；`push-worker` 会在推之前查架构与版本，不符则以退出码 2 结束。
- 提交时 `--worker-variant` 被解析成本 run 各引擎的精确 revision 写进提交记录：一个 run 内镜像固定，别人重推同名 variant 不影响正在运行的 run。某引擎缺该 variant 即以退出码 2 结束、不回落默认。
- **测试开发到 QA / CI 的交接**：本机新写或改了确定性 step，`plan` 的标注会变，但云端不会，直到重新 build + `push-worker`。cloud 后端「改了 steps 不推镜像等于没改」，且没有任何显式失败提醒。
- `gherkai deploy delete-worker` 尚未提供（命令存在、会说明）。

## 5 升级顺序

后端记一个版本戳，cloud 命令动资源前比对：CLI 比后端新就以退出码 2 结束、无放行开关；比后端旧只警告。所以升级是三步，顺序不能反：

1. 部署方 `uv tool upgrade gherkai`。
2. 立刻 `gherkai deploy --vpc <同一取值> --prefix <同前缀>`：新模板 + 新版本基础镜像进 ECR + 已有 variant 按新模板重派生。中间窗口里提交会以退出码 2 结束，这是预期。
3. 有自定义 variant 的：从新版本基础镜像重新 build、`push-worker`。其他人再升自己的 CLI。

不想动本机安装的部署方可用 `uvx --from 'gherkai[deploy-aws]==X.Y.Z' gherkai deploy` 先升后端。

升级到带 `list-runs` 清单索引的版本（1.5 起）时，第 2 步给运行记录表加索引，AWS 在部署后为已有的 run 补齐索引、`gherkai deploy` 不等它：这段时间 `list-runs --backend cloud` 以退出码 2 结束、说索引还在建立，稍后重试即可，其它命令不受影响。补齐之前这张表不能再被更新，别让人为此重新部署；建索引期间部署失败回滚时索引不会随之删除，须由人手动删掉再部署（命令见用户指南云端后端页的「版本与升级」）。

## 6 多环境与清理

- 多环境靠 `--prefix`：`prod-` / `stage-` 各一套后端，互不影响；所有 cloud 命令带同一个 prefix。
- `gherkai destroy` 之后两张 DynamoDB 表、S3 桶、两个 ECR 仓库**保留、需手动删**（防误删数据）。不手动删则同 prefix 重新 deploy 会因资源已存在而冲突。worker 镜像映射与默认指针也不随 destroy 删，ECR 留着则重建后照样能用。部署时在 us-west-2 建立的 Device Farm 项目 `<prefix>devices` 不属于 stack，也随 destroy 保留（连同其中的远程访问会话记录与录像；记着项目 ARN 的 SSM 参数随 stack 删除）；它留着时同 prefix 重新 deploy 会按名称找回并沿用、不冲突；不再需要时手动删除（删除会一并删掉会话记录与录像，旧 run 报告里指向这些会话的控制台链接随之失效）。命令样例见用户指南云端后端页（https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md ）的「拆除与清理」节。

## 7 `--expose-local` 在 cloud 后端的例外

`submit --backend cloud --expose-local <原始 origin>` 时隧道由**本机**的守护进程持有，本机须保持开机联网到 run 终态，这是「提交后关机也会运行到结束」的唯一例外。`--tunnel-ttl S` 是守护进程的兜底 TTL（默认为这个 run 各 job 预算之和加启动余量与每个 job 的余量，是按任务量估算的上限、不是保证），到点无条件拆隧道，调小可能在 run 未完时断隧道。
