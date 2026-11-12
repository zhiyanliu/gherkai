# 部署与维护云端后端

**部署方**按以下内容在自己的 AWS 账户里建齐 `--backend cloud` 所需的资源、维护 worker 镜像、升级与拆除。怎么提交 run、看判定与退出码见 [`running-and-results.md`](./running-and-results.md)；环境变量总表见 [`configuration.md`](./configuration.md)；后端由哪几个部分拼成、一次改动传播到哪里见 [`../internals/cloud-backend-carriers.md`](../internals/cloud-backend-carriers.md)。

云端后端只需部署方装与维护。团队里只提交 run 的成员不装部署包，用[下面的最小权限](#团队成员需要的最小云端权限)即可。

## 前置要求

CLI 与两个引擎 worker 的安装形态、AWS 凭证与 region 的配置见 [`getting-started.md`](./getting-started.md)，本节只讲部署方额外要准备的东西。

```bash
uv tool install 'gherkai[deploy-aws]'      # 部署包随 CLI 的 extra 一起装，不单独装
```

`deploy` 与 `destroy` 两条命令一直列在 `gherkai --help` 里，装上这个 extra 后它们才能实际运行；没装时执行会提示先装 `gherkai[deploy-aws]` 并以退出码 2 结束。另需：

| 前置 | 说明 |
|---|---|
| Node ≥ 22 在 PATH 上 | 底层用 AWS CDK。优先用 PATH 上的 `cdk`，没有则回落 `npx -y aws-cdk@2`。缺 Node 时命令报一句说明并以退出码 2 结束 |
| 容器引擎（docker） | 部署时要拉官方 worker 基础镜像并推送到你的 ECR 仓库；`push-worker` 也用它 |
| AWS 凭证与 region | 凭证走 `--profile` / `AWS_PROFILE`；region 取 `--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile 配置 |
| 每个 account + region 初始化一次 | `gherkai deploy --bootstrap`（账户级动作，不需要 `--vpc`）。未初始化就部署会报错并指回这个选项 |

部署机的凭证要能做云端写操作，范围比只提交 run 的成员大得多：CloudFormation 建改删并读取本 stack；建改删 DynamoDB 表、S3 桶、ECS 集群与任务定义、ECR 仓库、Lambda 与其事件源、EventBridge 规则与调度、VPC / 子网 / 安全组、CloudWatch 日志组；IAM 建角色与策略并 `PassRole`；SSM 读写 `/<prefix>backend/*`；ECR 登录与推送、列出、查看、注册、注销与删除任务定义 revision 并打上与去掉标签、读取运行记录表的状态并查询它的 `status-index` 索引；Device Farm 在 us-west-2 的 `ListProjects`、`GetProject` 与 `CreateProject`（找到已有的设备项目或新建一个）；`sts:GetCallerIdentity`（`--bootstrap` 取账户号）。缺 Device Farm 这三项权限时部署照常完成并给出警告（`--diff` 同样只警告）：后端仍记录着项目 ARN 且未确认项目已被删除时沿用该记录；没有记录，或已确认项目被删除且无法找回或新建时，这套后端不启用设备支持，带设备目标的云端 run 在提交前以退出码 2 结束。用 `gherkai doctor` 可先检查 Node、cdk 与容器引擎三项。

## 后端包含什么

一套 CloudFormation stack，名字随 `--prefix` 走（前缀 `gherkai-` 对应 stack `BackendStack-gherkai`），因此同一账户可按前缀并存多套环境，例如 `prod-` 与 `stage-`：

- **DynamoDB**：`<prefix>runs`（run 状态，带一个供 `gherkai list-runs` 按状态列出 run 的索引 `status-run_id-index`）与 `<prefix>events`（执行事件，带 TTL 自动过期），两张表按请求计费。
- **S3**：`<prefix>artifacts`（判定结果、报告、引擎产物，以及设备目标的安装包；派给 worker 的输入对象 7 天自动过期，`apps/` 下的安装包 14 天自动过期，复用与保留规则见 [`configuration.md`](./configuration.md)）。
- **ECS 与 ECR**：`<prefix>cluster`、每个引擎一个 Fargate 任务定义（1 vCPU / 2 GB）与一个镜像仓库 `<prefix><engine>-worker`。
- **Lambda 三个 + EventBridge 规则与到点调度**：让 `gherkai submit` 提交完即返回的 run 在云端自行推进与收敛，提交者的机器不必在线。
- **网络与 IAM**：按 `--vpc` 取值给 worker 的子网与安全组（优先用公有子网加公网 IP 出网，不建 NAT 网关），每个引擎一个最小权限角色，后端的三个 Lambda 各有自己的角色。
- **SSM 参数**（`/<prefix>backend/*`）：后端版本戳、生效的 VPC 取值、每个引擎的 worker 任务定义模板、worker 镜像映射与默认指针、子网与安全组 ID，以及 Device Farm 项目 ARN（启用设备支持时才有），供 `run` / `submit` 读取。

stack 之外，`gherkai deploy` 还会在部署 stack 之前找到已有的或新建一个 Device Farm 项目 `<prefix>devices`，供带设备目标的云端 run 在其中建立远程访问会话。项目固定在 us-west-2（Device Farm 只在这个区域提供），不属于 stack，destroy 时保留，见[拆除与清理](#拆除与清理)。

前缀原样接在每个资源名前面，分隔符要写进前缀里：`--prefix prod-` 得到 `prod-runs`，`--prefix prod` 得到 `prodruns`。前缀至多 32 个字符，更长的前缀在生成部署模板时即被拒绝，原因见下文「deploy 与 destroy 的选项」。

团队成员查结果时同样按前缀找到这套后端：`status`、`list-runs` 与 `explain` 的 `--backend`、`--report-dir`、`--prefix` 必须与产生这个 run 的 `run` 或 `submit` 一致（前台运行与后台提交都算），云端后端下 `--region` 也要指向同一个 region，否则查不到这个 run。云端后端的 `list-runs` 不读报告，不看 `--report-dir`。查询命令的用法见 [`running-and-results.md`](./running-and-results.md)。

云端两种执行方式的差别都源自「谁拉起 worker 任务」：`submit` 的任务由后端拉起；`run --backend cloud` 的任务由你自己的 CLI 进程拉起并等到运行结束。下面的并发上限与[团队成员的最小权限](#团队成员需要的最小云端权限)两处都由这一条决定。

`submit --backend cloud` 提交的一个 run，并行 job 数为 `min(提交时 --max-concurrency 的值, 部署侧上限 20)`；给的值超过上限时提交命令打印一行提示，并按 20 并行。`run --backend cloud` 的并行度就是 `--max-concurrency`，不受这个上限约束。

## 首次部署

```bash
gherkai deploy --bootstrap --profile <profile> --region <region>       # 该 account+region 首次用 CDK
gherkai deploy --diff --vpc default --prefix gherkai-                  # 先看会改动哪些资源，尤其网络与 IAM
gherkai deploy --vpc default --prefix gherkai-                         # 真部署
```

增量部署就是重复第三条命令：同一组选项重新运行即幂等收敛。中断后再次运行会接着收敛，中断留下的多余任务定义 revision 由后续部署或 `push-worker` 顺带回收。每次部署前建议先执行一次 `--diff`。

`--diff`、`--synth-only DIR`、`--bootstrap` 三者互斥，各自把默认动作换成一个只读或准备动作；都不给就是真部署。`--synth-only DIR` 只把 CloudFormation 模板导出到 `DIR`、不改动账户里的任何资源，适合交给你自己的审批流水线；`--vpc default` 与 `--vpc vpc-<id>` 仍要向账户查一次网络信息，因此这两个取值也需要可用凭证。有可用凭证时，`--diff` 与 `--synth-only` 执行前还会在后端所在区域读取 SSM 里记录的 Device Farm 项目 ARN，使变更集或模板与已部署的 stack 一致；读不到（凭证或 region 不可用、缺 `ssm:GetParameter` 权限、网络、限流）就以退出码 2 结束。后端还没有项目记录时，`--diff` 提示用于计算变更集的模板不含设备支持相关的授权与项目 ARN 参数，用有 Device Farm 权限的凭证实际部署会多出这两部分。记录的项目已被手动删除时，`--diff` 给出警告，同样用不含这些授权与参数的模板计算变更集，已部署的模板含它们时变更集会显示移除；用有 Device Farm 权限的凭证执行 `gherkai deploy` 时会按名称找回或新建项目。完全没有凭证时 `--synth-only` 照常离线导出，但模板按未启用设备支持生成、不含远程访问会话的授权，可能与已部署的 stack 不一致，命令会给出警告；需要与已部署一致的模板时，配好凭证后重新导出。

`--vpc default` 与 `--vpc vpc-<id>` 要向账户查 VPC、子网与可用区。结果按前缀缓存在 `$XDG_CACHE_HOME`（缺省 `~/.cache`）下的 `gherkai/cdk-context/`。首次查询某个前缀时会出现一条含 `Template validation found issues` 的告警，这是 CDK 在查询结果就绪前先用占位网络合成一遍所致；之后改用缓存的查询结果，不再出现。默认 VPC 的子网确实变了、或除这条警告之外真出现「新建或替换子网」的变更时，先 `--refresh-context` 再 `--diff`。

## VPC 的三种取值

`--vpc` 必给，没有隐式默认（`deploy`、`--diff`、`--synth-only`、`destroy` 都要给；`--bootstrap` 不需要）：

| 取值 | 含义 |
|---|---|
| `default` | 用账户的默认 VPC |
| `new` | 本 stack 新建一套（2 个可用区，不建 NAT 网关） |
| `vpc-<id>` | 复用现有的某个 VPC。worker 运行在该 VPC 的公有子网；该 VPC 没有公有子网时 worker 运行在私有子网，没有出网路径，此时须自备 NAT 网关或 VPC 端点，否则 worker 连不上模型与浏览器服务 |

生效的取值记录在后端，每次部署前比对，结果分四种：取值一致则放行；**不一致**则以退出码 2 结束并打印两个取值，确认要换就带 `--allow-vpc-change` 放行一次；**后端没有这条记录而 stack 已存在**（早于取值记录机制的环境）则以退出码 2 结束，先用 `gherkai deploy --diff --vpc <取值>` 核对变更集，再带 `--allow-vpc-change` 放行一次登记；stack 不存在（真首次部署）则放行。

`--vpc` 没有默认值、且每次部署都与后端记录比对，原因是 VPC 的选择不记录在 stack 状态里：若 `--vpc` 有默认值，第二次部署漏给时会静默改用默认取值；显式给值也可能给错。取值一旦与上次生效的取值不同，变更集里就可能出现新建 VPC、删除本 stack 所建的 VPC、替换 worker 安全组这类高风险变更。`--diff` 自身不做比对，它是用来核对变更集的手段。变更集里出现 VPC 级资源时，先确认取值再继续。

## deploy 与 destroy 的选项

| 选项 | 作用 |
|---|---|
| `--prefix P` | 资源名前缀（默认 `gherkai-`，也可用 `AWS_RESOURCE_PREFIX`），至多 32 个字符：job 超时保护所用定时计划的名称由前缀加固定后缀组成，不能超过 AWS 规定的 64 个字符，更长的前缀在生成部署模板时即报错，stack 不会被改动，但 Device Farm 项目可能已经建立（部署命令在生成模板之前找回或新建 `<prefix>devices` 项目），destroy 时保留，见[拆除与清理](#拆除与清理)。**须与 `run` / `submit` 的 `--prefix` 一致**，包括 `gherkai.toml` 里 `[cloud]` 节的 `prefix`：建出来的资源名就是提交侧推导的默认名，不一致时提交前检查会报错并点名前缀。部署命令不读 `gherkai.toml`，项目在配置文件里指定了前缀时，部署时要用 `--prefix` 或 `AWS_RESOURCE_PREFIX` 给出同一值 |
| `--vpc` 取值 | 见上「VPC 的三种取值」，必给 |
| `--allow-vpc-change` | 放行一次 VPC 取值变更或首次登记（仅 `deploy`） |
| `--require-approval {never,any-change,broadening}` | 透传 CDK 的 IAM 变更审批级别（仅 `deploy`；不给则用 CDK 自己的默认值） |
| `--refresh-context` | 丢弃本机缓存的环境查询结果重新查询；默认复用缓存 |
| `--stop-timeout N` | worker 容器从收到停止信号到被强制终止的宽限秒数（默认 120）。Fargate 的上限是 120 秒，更大的值在生成部署模板时即报错，stack 不会被改动，但 Device Farm 项目可能已经建立（部署命令在生成模板之前找回或新建 `<prefix>devices` 项目），destroy 时保留，见[拆除与清理](#拆除与清理)。云端运行时的停止宽限由这个值决定；提交侧的 `--grace` 只对本机运行有效，`--backend cloud` 带了它会直接报错并以退出码 2 结束，写在 `gherkai.toml` 里的 `grace` 在云端只提示一句、不生效 |
| `--container-engine 名` | 用哪个容器引擎（默认 `docker`，也可用 `GHERKAI_CONTAINER_ENGINE`）；当前只支持 `docker`，别的名字以退出码 2 结束、不静默回落 |
| `--provider NAME` | 用哪个部署 provider；装了一个时不必给 |
| `--region R` / `--profile P` | 与 `run` / `submit` 同名同义 |
| `--yes` | 不再询问确认（仅 `destroy`）；非交互终端与脚本里必须给 |

`destroy` 收下 `--prefix`、`--vpc`、`--refresh-context`、`--stop-timeout`、`--region`、`--profile`、`--provider` 与 `--yes`。`--allow-vpc-change`、`--require-approval`、`--container-engine` 只属 `deploy`，给了 `destroy` 会被拒并以退出码 2 结束。

## worker 镜像 variant

| 概念 | 是什么 | 谁写 |
|---|---|---|
| **基础镜像** | `ghcr.io/zhiyanliu/gherkai-worker-<engine>:<版本>`，linux/amd64，不含任何使用方内容 | 官方发布 |
| **variant** | 一套具名的确定性 step 集构建成的定制镜像，推送到 ECR 时打上标签 `<CLI 版本>-<variant 名>`，对应一个任务定义 revision（镜像按 digest 引用） | 你的 `push-worker` |
| **默认指针** | 提交时不给 `--worker-variant` 时用哪个 variant（一个部署一个） | `gherkai deploy` 初始化为 `base`；`push-worker --set-default` 改指 |

云端运行哪套确定性 step 由镜像决定，不由提交侧的 `--steps-dir` 决定。怎么写这些 step 见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)。

镜像构建不由 gherkai 负责，三行即可：

```dockerfile
FROM ghcr.io/zhiyanliu/gherkai-worker-novaact:<你的 CLI 版本>
COPY steps/ /app/steps
ENV GHERKAI_STEPS_DIR=/app/steps
```

**构建时必须带 `--platform linux/amd64`**：`docker build --platform linux/amd64 -t acme-novaact:login .`。云端 worker 任务固定 X86_64，在 arm 机器上漏掉这个参数会构建出 arm64 镜像，容器要到启动期才报 `exec format error`。`push-worker` 在推送前校验架构，不匹配即以退出码 2 结束。

```bash
# 推一个本地镜像，注册为某引擎的一个 variant（一次一个引擎，两个引擎分两次执行）
gherkai deploy push-worker acme-novaact:login --engine novaact --variant login --prefix gherkai-
gherkai deploy push-worker acme-midscene:login --engine midscene --variant login
# 顺带把默认指针指过去（该 variant 在另一个引擎还没有时只警告、不阻止）
gherkai deploy push-worker acme-novaact:common --engine novaact --variant common --set-default
gherkai deploy list-workers                    # 当前版本有哪些 variant、默认是谁、哪些 revision 待清理；加 --json 输出机读格式
gherkai submit features/login.feature --backend cloud --worker-variant login   # 提交时选 variant，缺省用默认指针
```

- **重推同名 variant 直接放行**，只打印原 digest 到新 digest 的变化。正在运行的 run 手里的 revision 按 digest 指着旧镜像层，不受影响。
- **variant 按版本隔离**：标签含 CLI 版本，旧版本的 variant 留在 ECR 作历史、不参与当前版本的解析。升级不重置默认指针。
- **退休的旧 revision 顺带回收**：`push-worker` 与 `deploy` 末尾各回收一次，退休满 1 小时且没有未结束的 run 引用才真删，否则留到下一次。例外是 `run --backend cloud --no-report`：它不写运行记录，回收时看不到它正在使用的 revision；这样的 run 可能执行超过 1 小时时，执行期间不要重推它使用的 variant，也不要重新部署后端。滞留不影响使用，`list-workers` 看得到。`delete-worker` 尚未提供（执行会以退出码 2 结束并说明），旧版本 variant 的 ECR 标签目前请按需自行清理。

## 部署输出怎么读

CDK 成功完成资源部署之后，命令继续执行 worker 镜像的三步，最后清理一次旧 revision。输出依次如下：

1. `== 基础镜像同步 novaact：ghcr.io/zhiyanliu/gherkai-worker-novaact:<版本> ==` —— 把当前版本的官方基础镜像拉下来、推成你 ECR 里的 `<版本>-base`。两个引擎各一段。
2. `已保留默认 worker 镜像 variant common（部署不改动已有的默认设置）` —— 默认指针已存在，部署不动它，它记录的是团队的选择。首次部署这里是 `默认 worker 镜像 variant 初始化为 base（官方基础镜像，未定制）`。
3. `<engine>/<variant> 的 worker 运行配置已按本次部署更新为 <family>:<n>（旧配置 <family>:<m> 已标记待清理）` —— 本次部署改了任务定义模板（如 `--stop-timeout`），已有 variant 按记录的镜像重新派生一份 revision；旧配置已不可用（已注销或已删除）时不带括号里这一句。模板没变、且各 variant 的 revision 仍可用时，这里是 `各 variant 的 worker 运行配置已是最新，无需更新`；模板没变而某个 variant 的 revision 已不可用时，这一行说明它已按记录的镜像重新注册。
4. `清理：回收 N 个 revision（…）` —— 顺带回收了已退休且无人引用的旧 revision，没有可回收的就不打印。

## 版本与升级

后端记一个版本戳，提交前检查拿它比对 CLI 版本。**CLI 比后端新时拒绝执行并以退出码 2 结束**（新 CLI 写的任务定义旧后端读不懂，没有放行选项）；CLI 比后端旧时只打印一行提示、照常提交，所以团队成员可以晚一步再升。任一侧不是发行版本时跳过比对。后端还没有版本戳（这套后端在 1.4.0 之前部署、此后没有重新部署过）时，没有使用 `--expose-local` 的桌面 run 只提示、照常提交；带设备目标或使用 `--expose-local` 的 run 以退出码 2 结束，需要先升级部署。CLI 与后端保持同版本，因此升级是三步：

1. 部署方 `uv tool upgrade gherkai`（安装时带的 extra 沿用）。
2. 部署方立刻 `gherkai deploy --vpc <与上次相同的取值> --prefix <同前缀>`：新模板、新版本基础镜像同步进 ECR、对本版本已有的 variant 重新派生。
3. 有自定义 variant 的，由测试开发从新版本基础镜像重新构建，交部署方用 `gherkai deploy push-worker` 推一遍。三步完成后，团队其他成员再升级自己的 CLI。

三步之间有两段窗口，被拒的人不同：

![升级三步（部署方先升级本机、再部署后端、最后重推自定义 variant，其他成员在三步完成后升级）之间的两段降级窗口，以及每段里谁被拒、谁照常](../diagrams/cloud-backend-upgrade-windows.svg)

图注：窗口一里被拦下的只有刚升级的那台部署机——它的提交、查结果、列出 run（`list-runs`）与读证据（`explain`）、推送镜像与列出镜像都会被拒绝；其他成员的 CLI 仍与后端同版本，提交前检查直接放行、不受影响。`deploy` 本身不做这项版本比对，所以第 2 步照常执行。窗口二里被拦下的是已升到新版本的提交者——自定义 variant 在新版本下还没有镜像，止于第 3 步重推完成；这段里还没升级的成员，CLI 旧于后端只被打一行提示、不拦（提交记录格式不变的升级里如此；格式变化的升级里，旧版本 CLI 提交的 run 会被后端置为 `error`，要先升级 CLI 再重新提交，见下段），而镜像标签由**提交者本机的 CLI 版本**拼出（对应上面「variant 按版本隔离」），他解析到的仍是自己那一版的镜像。窗口二只出现在默认指针指的是自定义 variant（或提交时显式选了自定义 variant）的情形——指针是 `base` 且不显式指定时，第 2 步已经把新版本的基础镜像备好了。图上只画这两段窗口的起止。

升级 CLI 之后，本机读到格式与本机 CLI 不一致的提交记录时怎么处理，见 [`running-and-results.md`](./running-and-results.md)「命令」一节末尾的提交记录格式版本说明。云端后台自己读到不能执行的提交记录（格式与后端不一致、记录不完整）时不执行，把这个 run 置为 `error`，原因显示在 `status` 的 `message` 行里；按原因升级后端或重新提交。

两段窗口里被拒的命令都以退出码 2 结束。窗口一在第 2 步执行完后即恢复，不想动本机安装的部署方可以用 `uvx --from 'gherkai[deploy-aws]==X.Y.Z' gherkai deploy` 先把后端升上来；窗口二里可让提交者临时用 `--worker-variant base`。顺序不能倒过来：后端由 CLI 的部署包部署，版本戳的值就是发起该次部署的 CLI 的版本。第 3 步也不能提前到第 2 步之前：镜像标签含 CLI 版本，提前推等于推到一个后端还不识别的版本标签下，`push-worker` 与 `list-workers` 会拒绝并以退出码 2 结束。

**升级后清单索引要先建好**：已部署的后端升级到带 `list-runs` 清单索引的版本（1.5 起）时，第 2 步的 `gherkai deploy` 给运行记录表 `<prefix>runs` 加上索引 `status-run_id-index`，AWS 随后在后台为表里已有的 run 补齐索引。`gherkai deploy` 不等补齐就结束，所以部署完成后的一段时间里 `gherkai list-runs --backend cloud` 以退出码 2 结束并提示索引还在建立，稍后重试即可；`submit`、`status`、`explain` 等命令不用这个索引，不受影响。加索引的这次升级还要承担 [AWS::DynamoDB::Table](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-dynamodb-table.html) 文档写明的三条限制：

- 索引补齐之前这张表不能再被更新：这段时间里再次执行 `gherkai deploy`，只要这次部署要改运行记录表就会失败，等补齐后再部署。补齐与否可用 `aws dynamodb describe-table --table-name <prefix>runs` 查看这个索引的 `IndexStatus`，变为 `ACTIVE` 即已补齐。
- 建索引期间 stack 更新失败而回滚时，已经开始建立的索引不会随回滚删除，须先手动删掉再重新部署：`aws dynamodb update-table --table-name <prefix>runs --global-secondary-index-updates '[{"Delete":{"IndexName":"status-run_id-index"}}]'`。索引刚开始建立、还在分配资源的一小段时间里删不了，稍后重试。
- AWS 建议加索引的那次更新不改其它资源，而 `gherkai deploy` 的升级是整个 stack 一次更新，无法把加索引单独拆成一次；所以这次升级前更要先用 `--diff` 核对变更集。

## 团队成员需要的最小云端权限

同一套后端可以给团队成员两级不同大小的权限，凭证越少的那一级越适合 CI 与低权限机器。执行方式与执行后端四种组合的对照见 [`running-and-results.md`](./running-and-results.md)，这里只说云端两级的差别：

- **`submit` + `status`**：运行记录表读写、提交前对表、桶、集群、任务定义与后端 Lambda 的只读检查、调用 `<prefix>kicker` Lambda、读 `/<prefix>backend/*` 参数、产物桶 `s3:PutObject`（用例含多行参数时才触发），以及 variant 解析要的只读 `ecr:DescribeImages`、`ecs:DescribeTaskDefinition` 与 `ecs:ListTaskDefinitions`（读不到任务定义 revision 时用它确认 revision 是否已被删除）。**不需要任何 ECS 写权限**，worker 任务由后端的 Lambda 拉起。
- **`run --backend cloud`**：运行记录表读写、events 表（`<prefix>events`）的 `dynamodb:Query`（逐 scope 读取执行事件）、同样的只读检查、读 `/<prefix>backend/*` 参数、variant 解析的只读权限（同上），再加起停与查询 Fargate 任务的权限、把 worker 的任务角色与执行角色传给 ECS 的权限（`iam:PassRole`）、以及上传 job 到产物桶的权限——起任务的是你自己的进程（见上「后端包含什么」），因此不需要调用 Lambda 的权限。

无论哪一级，提交带设备目标或 `@app` 的 scope 时，都另需读 `/<prefix>backend/device-farm-project` 参数（已含在上面的参数读权限里），以及产物桶 `apps/` 前缀的读、写、分段上传中止与打标签，和该前缀的列举。

两级都用 `explain` 读证据：除判定明细与证据对象的读权限外，对被中止的 job 补取已执行 step 的记录时需要 events 表（`<prefix>events`）的 `dynamodb:Query`（`run --backend cloud` 这一级已含，`submit` + `status` 这一级要另加）；缺它时 `explain` 照常输出，只在那个 job 下说明没能补取的原因。events 表的记录只保留 7 天，过期后同样补不到、同样说明原因；判定明细与证据不受这个期限影响。

两级都用 `gherkai list-runs --backend cloud` 列出 run 时，另需运行记录表索引上的 `dynamodb:Query`，资源要写成索引 ARN `arn:aws:dynamodb:<区域>:<账号>:table/<prefix>runs/index/status-run_id-index`（表 ARN 上的 `Query` 授权覆盖不到索引），以及表 ARN 上的 `dynamodb:BatchGetItem`（按 run_id 读回运行状态）；它读表结构用的 `dynamodb:DescribeTable` 与读版本戳用的参数读权限已含在上面两级里。`list-runs` 只读、不需要任何写权限，不用这个命令的成员可以不给这两项。

无论哪一级，用 `gherkai doctor --backend cloud` 自检设备支持时，另需 us-west-2 上的 `devicefarm:ListRemoteAccessSessions`，资源为部署建立的 Device Farm 项目 ARN（即 `/<prefix>backend/device-farm-project` 参数的值），用来列出项目里还没结束的远程访问会话；缺这一项时 doctor 的 `backend.devices.sessions` 行只说明缺什么、不影响退出码，不测设备的团队可以不给。停止会话需要的 `devicefarm:StopRemoteAccessSession` 不在这两级里，请有这项权限的人执行。

## 拆除与清理

```bash
gherkai destroy --vpc default --prefix gherkai-          # 交互终端下会再问一次确认
gherkai destroy --vpc default --prefix gherkai- --yes    # 脚本或非交互终端
```

集群、日志组、stack 建的那份任务定义模板、以及 SSM 里的版本戳与 VPC 取值随 stack 销毁，不用管。`push-worker` 与 `deploy` 派生的各 variant 任务定义 revision 不由 stack 管理，destroy 之后留在账户里，不产生费用，可以不清理。**数据类资源不随 destroy 删除**，这是为了防误删。下面这些需要手动清理（把 `gherkai-` 换成你的前缀）：

```bash
aws dynamodb delete-table --table-name gherkai-runs
aws dynamodb delete-table --table-name gherkai-events
aws s3 rb s3://gherkai-artifacts --force                                    # 桶非空需要 --force
aws ecr delete-repository --repository-name gherkai-novaact-worker --force
aws ecr delete-repository --repository-name gherkai-midscene-worker --force
```

不清理的话，用同一前缀重新部署会因资源已存在而冲突。

worker 镜像映射与默认 variant 指针这两族 SSM 参数也不随 destroy 删除：同前缀重建后它们还记着上一套环境里的 variant。ECR 仓库还在的话，重新 `gherkai deploy` 会把这些 variant 按原镜像重新登记、照样可用；ECR 仓库也删了的话，这些 variant 变成有记录、没镜像，提交时以退出码 2 结束并提示找不到镜像，重推同名 variant 即恢复。想彻底清空，用 `aws ssm get-parameters-by-path --path /gherkai-backend/worker-image --recursive --query 'Parameters[].Name' --output text` 列出后逐条 `aws ssm delete-parameter --name …`，再删 `/gherkai-backend/worker-default`。

部署时建立的 Device Farm 项目 `gherkai-devices` 也不随 destroy 删除：它由 `gherkai deploy` 在部署 stack 之前建立、不属于 stack，项目连同其中的远程访问会话记录与录像一起保留（会话录像与日志由 AWS 保留 400 天，到期自动删除，见 [Device Farm 的数据保留](https://docs.aws.amazon.com/devicefarm/latest/developerguide/data-protection.html)），SSM 里记着项目 ARN 的 `/gherkai-backend/device-farm-project` 参数则随 stack 删除。项目留着时，同一前缀重新部署会按名称找回并沿用它，不会冲突。不再需要时手动删除：

```bash
aws devicefarm list-projects --region us-west-2 --query "projects[?name=='gherkai-devices'].arn" --output text   # 查出项目 ARN
aws devicefarm delete-project --region us-west-2 --arn <项目 ARN>
```

Device Farm 只在 us-west-2 提供，这两条命令的区域与后端所在区域无关。删除项目会一并删掉其中的会话记录与录像，之前 run 报告里指向这些会话的控制台链接随之失效。

## 费用

后端闲置时的成本接近零：不建 NAT 网关，两张表按请求计费，S3 与日志按量。ECR 镜像存储按量计费：仓库不设自动过期，重推同名 variant 会留下旧镜像层，需要时按上面 worker 镜像一节的说明自行清理。费用主要产生在执行 run 时：Fargate 任务按运行时长计费，另有 AI step 调用模型的费用、云端浏览器会话的费用，以及设备目标的 Device Farm 远程访问会话费用（按设备分钟计费）。量级见 [`running-and-results.md`](./running-and-results.md)，实际数字以你账户的 AWS 账单为准。

## 退出码与常见错误

- `0`：成功。
- `2`：前置或校验失败，都可由你修正。缺 Node、找不到 cdk、容器引擎名无法识别、取不到 gherkai 自身的版本号（gherkai 未以发行包形式安装；`deploy`、`--diff`、`--synth-only`、`destroy`、`push-worker` 与 `list-workers` 都要用这个版本号）、读不到后端里的 Device Farm 项目记录（凭证或 region 不可用、缺 `ssm:GetParameter`、网络、限流）、记录不是合法的项目 ARN（被手工改过），都在改动账户之前拦下；`--diff` 核对后端记录的项目时遇到限流、网络或服务端故障，同样以 `2` 结束、不输出变更集，稍后重试即可。例外：`push-worker` 推送途中的 AWS 调用失败也以 `2` 结束，但这时镜像与 revision 可能已写入账户。
- `1`：账户可能已被改动，来源有三种：
  - CDK 自身失败：CDK 的退出码原样透传（多为 `1`），原因看上方 cdk 输出；
  - CDK 已成功、随后的 worker 镜像步骤失败：带同一组选项重新运行 `gherkai deploy` 幂等收敛；
  - 部署 stack 之前找回或建立 Device Farm 项目时遇到权限以外的错误（限流、网络、服务端故障）：这时 stack 没有改动，项目可能已经建立，重新运行 `gherkai deploy` 会按名称找回它、不会重复建立。

  `gherkai destroy` 没有 worker 镜像步骤，它的 `1` 只会来自 CDK。
- 其余退出码：cdk 命令自己的返回值，原样透传。

| 现象 | 处置 |
|---|---|
| 找不到 node | 装 Node ≥ 22 后重新运行 |
| 找不到 cdk 也找不到 npx | 装 Node ≥ 22（自带 npx），或 `npm i -g aws-cdk`，之后重新运行 |
| 提示 `取不到 gherkai 自身的版本号：gherkai 未以发行包形式安装（例如直接从源码运行）` | 把 gherkai 装成包（`uv tool install 'gherkai[deploy-aws]'`，或在工作区执行 `uv sync`）后重新运行 |
| 缺 `--vpc` | 补上三个取值之一。环境已存在时提示里会给出上次部署用的那个取值 |
| `--vpc` 取值不合法 | 只能是 `default`、`new`、`vpc-<id>` 三种形态 |
| VPC 取值与后端记录不符，或后端没有取值记录 | 先 `gherkai deploy --diff`（带同一组选项）核对变更集，确认无误再带 `--allow-vpc-change` 放行一次 |
| cdk deploy 失败且报错提到 bootstrap | 先 `gherkai deploy --bootstrap`（同 `--profile` / `--region`） |
| 找不到容器引擎或连不上其守护进程 | 装好 docker 并让守护进程运行。stack 仍会照常部署，随后的基础镜像同步以退出码 1 结束，带同一组选项重新运行 `gherkai deploy` 幂等收敛 |
| `push-worker` 说架构不对 | 带 `--platform linux/amd64` 重新构建 |
| `deploy` 以退出码 2 结束，提示 Device Farm 里有多个名为 `<prefix>devices` 的项目 | 部署不替你选用其中哪一个，消息里列出了命中的全部项目 ARN，本次没有改动后端。用 `aws devicefarm delete-project --region us-west-2 --arn <项目 ARN>` 删掉多余的、只留一个（删除会一并删掉其中的会话记录与录像），再重新运行 `gherkai deploy` |
| `deploy` 或 `deploy --diff` 警告当前凭证没有 Device Farm 权限 | 命令照常完成：之前的部署记录过项目就沿用它，设备支持保持不变（`--diff` 按记录的项目计算变更集，项目若恰好已被手动删除，变更集会与下一次部署不同）；记录的项目已被手动删除而又无法找回或新建时，本次按未启用设备支持部署、撤掉设备授权；没有记录就跳过设备支持。后两种情形下带设备目标的云端 run 在提交时以退出码 2 结束并提示「部署未启用设备支持」。要启用，给部署用的凭证加上 us-west-2 的 `devicefarm:ListProjects`、`GetProject` 与 `CreateProject`（见[前置要求](#前置要求)），再重新运行 `gherkai deploy`；不测设备的团队可以忽略这条警告 |

提交侧遇到的症状（CLI 与后端版本不一致、variant 解析不到、后端没有默认 variant 指针、读不到后端版本戳、云端 job 判 `error`）以及更多按症状分类的处置见 [`troubleshooting.md`](./troubleshooting.md)。`gherkai deploy --help` 与 `gherkai deploy push-worker --help` 列出全部选项。
