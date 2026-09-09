# gherkai-deploy-aws

`gherkai` 的 **AWS 后端供给**包：一条命令在你自己的 AWS 账户里建齐 `gherkai --backend cloud` 所需的全部资源（状态表、产物桶、Fargate 集群、镜像仓库、让 run 在云上自我推进的事件链、网络与最小权限角色），并把 worker 镜像推上去、登记成可提交的版本。装上它，`gherkai` 就多出 `gherkai deploy` / `gherkai destroy` 两条命令。

只有**部署方**需要装：改云端环境是云端写操作，团队里只提交 run 的人不需要。

## 安装与前置

```bash
uv tool install 'gherkai[deploy-aws]'   # 本包随 CLI 的 extra 进来，不单独安装
```

- **Node ≥ 22 在 PATH 上**：底层用 AWS CDK（Node 程序），优先用 PATH 上的 `cdk`、没有则回落 `npx -y aws-cdk@2`；缺 Node 时报一句人话并退 2，不吐堆栈。
- **部署机上要有容器引擎（docker）**：`gherkai deploy` 要拉官方 worker 基底镜像、推进你的 ECR。
- **AWS 凭证与 region**：`--profile` / `AWS_PROFILE`；region 取 `--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile 配置。
- **每个 account+region 首次用 CDK 要初始化一次**：`gherkai deploy --bootstrap`（账户级动作，不需要 `--vpc`）；没初始化就 deploy 会报错并指回这个 flag。

## 建什么

一套 CloudFormation stack，名字随 `--prefix` 走，故同一账户可按 prefix 并存多套环境（`prod-` / `stage-`）：

- **DynamoDB**：`{prefix}runs`（run 状态）+ `{prefix}events`（执行事件，带 TTL 自动过期）
- **S3**：`{prefix}artifacts`（判定结果、报告、引擎产物；派给 worker 的输入对象 7 天自动过期）
- **ECS + ECR**：`{prefix}cluster`、每引擎一个 Fargate task 定义、每引擎一个镜像仓库（放你 push 的 worker 镜像）
- **Lambda ×3 + EventBridge 规则 + 到点调度**：让 `gherkai submit` 提交完即走的 run 在云上自我推进、自我收敛，不需要你的机器在线
- **网络与 IAM**：按 `--vpc` 档给 worker 的子网与安全组（三档都是公有子网 + 公网 IP 出网、**零 NAT 常驻成本**）+ 每引擎一个最小权限角色与推进链各自的角色
- **SSM 参数**（`/{prefix}backend/*`）：版本戳、生效的 VPC 档、worker 镜像映射与默认指针、子网/安全组 ID（供 `run` / `submit` 读）

云端每个 run 的并行 job 数 = `min(提交时 --max-concurrency 声明的值, 部署侧上限 8)`。

## 用

```bash
gherkai deploy --bootstrap                                  # 某 account+region 首次用 CDK
gherkai deploy --diff --vpc default --prefix gherkai-       # 先看清这次会改什么（尤其网络/IAM），每次 deploy 前推荐
gherkai deploy --vpc default --prefix gherkai-              # 真部署/更新
gherkai deploy --vpc new --require-approval broadening      # 新建整套 VPC；IAM 变更要人过目
gherkai deploy --synth-only ./out --vpc default             # 只导模板到 DIR、不碰账户（交给自己的审批流水线）
gherkai destroy --vpc default --prefix gherkai- [--yes]     # 拆栈；交互终端下会再问一次，脚本/非 TTY 加 --yes
```

`--diff` / `--synth-only DIR` / `--bootstrap` 三者互斥，各把默认动作换成一个只读/准备动作；都不给 = 真部署。`destroy` 收下表除 `--container-engine` 外的同一组旋钮，另有 `--yes`。

| flag | 作用 |
|---|---|
| `--prefix P` | 资源名前缀（默认 `gherkai-`，兜底 `AWS_RESOURCE_PREFIX`）；**必须与 `gherkai run` / `submit` 的 `--prefix` 一致**——建出来的资源名就是提交侧推导的默认名，不一致则提交侧连不上、preflight 报错点名 prefix。多环境切换靠它 |
| `--vpc 档` | `default` / `new` / `vpc-<id>`，**必给**；见下「VPC 三档」 |
| `--allow-vpc-change` | 放行一次 VPC 档变更或首次登记 |
| `--require-approval` | 透传 cdk 的 IAM 变更审批档（`never` / `any-change` / `broadening`） |
| `--refresh-context` | 丢弃本机缓存的环境查询结果（VPC/子网/AZ）重新查询；默认复用缓存 |
| `--stop-timeout N` | worker container 的 SIGTERM→SIGKILL 宽限秒数（默认 120；**Fargate 硬上限就是 120**，更大的值在命令期就被拒——这是平台限制、不是笔误） |
| `--container-engine 名` | 用哪个容器引擎（默认 `docker`，兜底 `GHERKAI_CONTAINER_ENGINE`）；当前只实装 `docker`，别的名字退 2、不静默回落 |
| `--region R` / `--profile P` | 与 `run` / `submit` 同名同义 |

**关于环境查询缓存**：`--vpc default` / `--vpc vpc-<id>` 要向账户查 VPC/子网/AZ，结果按 prefix 缓存在 `$XDG_CACHE_HOME`（缺省 `~/.cache`）`/gherkai/cdk-context/`。**首次**查询某 prefix 时会出现一次 `[Warning] Template validation found issues…`（cdk 为缺失查询值先用占位网络预合成一遍所致，属误报），之后走缓存即消失。默认 VPC 的子网真变了、或除这条 warning 之外真出现「新建/替换子网」的变更集时，先 `--refresh-context` 再 `--diff`。

## VPC 三档

`--vpc` **必给、无隐式默认**（`deploy` / `--diff` / `--synth-only` / `destroy`；`--bootstrap` 不需要）：`default`（用账户默认 VPC）/ `new`（本 stack 新建，2-AZ、零 NAT）/ `vpc-xxxx`（复用现有 VPC）。

> ⚠️ **为什么必给、还要比对（真踩过的坑）**：VPC 的选择不进 stack 状态，第二次 deploy 漏带或敲错档，变更集里就会出现「**新建整套 VPC + 替换 worker 安全组**」这种危险变更——这是真踩过的。所以生效的档记在后端，每次 deploy 前比对四态：**一致** → 放行；**不一致** → 退 2 并打印两个档让你看清，确认要换就带 `--allow-vpc-change` 放行一次；**后端没有这条记录但 stack 已存在**（本机制之前部署的旧环境，恰是最危险的那一次 deploy）→ 退 2，请先 `gherkai deploy --diff --vpc <档>` 核对变更集、再带 `--allow-vpc-change` 放行一次登记；**stack 不存在**（真首次部署）→ 放行。
>
> `--diff` 自己不做这个比对——它正是让你去核对的那条手段，拦住它就无路可走。看到 VPC 级资源出现在 diff 里，停下来查档。

## 版本与升级

后端记一个版本戳，提交侧 preflight 拿它比对 CLI 版本、不一致即拦。CLI 与后端钉在同一版本，故**升级是三步**：

1. `uv tool upgrade gherkai` —— 升 CLI（安装时带的 `[deploy-aws]` extra 会沿用）。
2. `gherkai deploy` —— 新模板 + 新版本基底镜像同步进 ECR + 对新版本已有的 variant 重派生。（1→2 中间的窗口里提交会退 2，这是预期。）
3. 有自定义 variant 的：从**新版本基底**重新 build 各引擎镜像，`gherkai deploy push-worker` 推上去。

不想动本机安装的部署方可以 `uvx --from 'gherkai[deploy-aws]==X.Y.Z' gherkai deploy` 先升后端。团队里只提交 run 的人，等部署方做完三步再升自己的 CLI。

## worker 镜像：基底 / variant / 默认指针

| 概念 | 是什么 | 谁写 |
|---|---|---|
| **基底** | `ghcr.io/zhiyanliu/gherkai-worker-<engine>:X.Y.Z`，linux/amd64，零使用方内容 | 官方发布 |
| **variant** | 一套具名的确定性 step 集 = 一个定制镜像，落 ECR tag `<CLI 版本>-<variant>`，并对应一个 task 定义 revision（镜像按 digest 引用） | 你的 `push-worker` |
| **默认指针** | 提交时不给 `--worker-variant` 用哪个 variant（部署级一个） | `gherkai deploy` 初始化为 `base`；`push-worker --set-default` 改指 |

`gherkai deploy` 自己会：把当前版本的基底同步成 `<版本>-base`、默认指针缺失时初始化为 `base`（**已存在则不动**，它记的是团队意图）、task 定义模板变了就用已记录的镜像重派生既有 variant。全部幂等，重跑收敛。

定制镜像三行搞定（构建不归 gherkai）：

```dockerfile
FROM ghcr.io/zhiyanliu/gherkai-worker-novaact:<你的 CLI 版本>   # 版本须与 gherkai --version 一致
COPY steps/ /app/steps
ENV GHERKAI_STEPS_DIR=/app/steps
```

> ⚠️ **build 时必须带 `--platform linux/amd64`**（`docker build --platform linux/amd64 -t acme-novaact:login .`）：Fargate task 定义固定 X86_64，arm Mac 上不加会 build 出 arm64，容器**启动期**才 `exec format error` 挂死、不易一眼看出是架构问题。`push-worker` 会在推送前校验架构、不匹配即退 2，把这个坑提前到推送前。

```bash
# 推一个本地镜像成某引擎的一个 variant（一次一个引擎；两个引擎跑两次）
gherkai deploy push-worker acme-novaact:login --engine novaact --variant login --prefix gherkai-
gherkai deploy push-worker acme-midscene:login --engine midscene --variant login
# 顺手把默认指针指过去（该 variant 在另一引擎还没有 → 只警告不拦）
gherkai deploy push-worker acme-novaact:common --engine novaact --variant common --set-default
gherkai deploy list-workers                       # 当前版本有哪些 variant、默认是谁、哪些 revision 待清理
gherkai submit features/ --backend cloud --worker-variant login    # 提交时选 variant（缺省 = 默认指针）
```

- **重推同名 variant 直接放行**，只打印「原 digest → 新 digest」；在跑的 run 手里的旧 revision 按 digest 指着旧镜像层、不受影响。
- **variant 按版本隔离**（tag 含 CLI 版本），旧版本的留在 ECR 作历史、不参与当前版本解析；升级不重置默认指针——若默认是 `common` 而新版本的 `common` 还没推，提交会退 2 并提示让部署方把它推上去，推上去即恢复；急着跑可以自己临时 `--worker-variant base`（`gherkai deploy` 已把当前版本的基底同步成 `base`）。
- **退休的旧 revision 机会式清理**（挂在 `push-worker` / `deploy` 末尾，无定时任务）：退休满 1 小时且无未结束的 run 引用才真删，否则留到下次；滞留无害，`list-workers` 看得到。**`delete-worker` 尚未提供**（退 2 并说明原因），旧版本 variant 的 ECR tag 目前请自行按需清理。

## 清理

**数据类资源不随 destroy 删**（防误删）——`gherkai destroy` 之后 2 张 DynamoDB 表 + artifacts 桶 + 2 个 ECR 仓库**残留、需手动删**（把 `gherkai-` 换成你的 prefix）：

```bash
aws dynamodb delete-table --table-name gherkai-runs
aws dynamodb delete-table --table-name gherkai-events
aws s3 rb s3://gherkai-artifacts --force                                      # 桶非空需 --force
aws ecr delete-repository --repository-name gherkai-novaact-worker --force
aws ecr delete-repository --repository-name gherkai-midscene-worker --force
```

不手动删则同 prefix 重新 deploy 会因资源已存在而冲突。cluster / task 定义 / SSM 参数（含版本戳与 VPC 档）/ 日志组随 stack 销毁、无需手动。

## 部署机需要的权限

部署机的凭证要能做云端写操作（比只提交 run 的人大得多）：**CloudFormation** 建/改/删本 stack + 读 stack（VPC 档比对）；**建改删** DynamoDB 表、S3 桶、ECS 集群与 task 定义、ECR 仓库、Lambda 与其事件源、EventBridge 规则与调度、VPC/子网/安全组、CloudWatch 日志组；**IAM** 建角色与策略 + `PassRole`（把 task / Lambda 角色交给 ECS 与 Lambda）；**SSM** 读写 `/{prefix}backend/*`；**worker 镜像**——ECR 登录与推送、ECS 注册/注销 task 定义 revision 并打 tag、`Query` runs 表及其 `status-index`（清理前确认没有在跑的 run 引用旧 revision）；**`sts:GetCallerIdentity`**（`--bootstrap` 取账户号，对任何主体恒可用）。

## 退出码与常见错误

`0` 成功 · `2` 前置/校验失败（Node 缺失、VPC 档不符或无记录、读后端失败、容器引擎名不认、`push-worker` 的架构或版本不符——都是你可修的）· `1` **cdk 已成功、而 worker 镜像步骤失败**（账户已被改动，重跑 `gherkai deploy` 幂等收敛）· 其余 = cdk CLI 自己的返回码（原样透传）。

常见的几条：**找不到 node** → 装 Node ≥ 22；**VPC 档报错** → 见上「VPC 三档」；**`push-worker` 说架构不对** → 带 `--platform linux/amd64` 重 build；**`push-worker` 说 CLI 新于后端** → 先 `gherkai deploy`；**deploy 只警告「容器引擎不可用」、没同步基底** → 修好 docker 后重跑 `gherkai deploy`。

## 帮助

`gherkai deploy --help` / `gherkai deploy push-worker --help` 列全部 flag；项目说明与上手见 https://github.com/zhiyanliu/gherkai#readme ，问题反馈见 https://github.com/zhiyanliu/gherkai/issues 。

设计文档（架构决策记录）见 https://github.com/zhiyanliu/gherkai/tree/HEAD/docs/adr 。
