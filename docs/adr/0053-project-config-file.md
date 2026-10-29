# 0053. 项目配置文件 gherkai.toml

> **Status:** Accepted（2026-10-15）——项目级配置文件 `gherkai.toml` 的定位、取值顺序、节与键，以及设备选择的用户面规则。

## 背景与问题

1.4 之前，gherkai 的配置只有两层：命令行选项与环境变量，两者都没给就用内建默认。这对桌面网页目标够用：一个项目通常只需固定 `--default-engine`、`--steps-dir`、`--prefix` 少数几项，写进 shell 或 CI 的环境变量即可。

移动真机目标（[0048](./0048-test-targets-device-and-ui-kind.md)）带来三类新值，它们既不适合每次在命令行重复，也不适合塞进环境变量：

- **设备选择**：每个平台用哪台设备（设备 ARN，或平台加系统版本的筛选条件）、按哪种计费方式（`billingMethod`）、获取设备的预算。
- **应用清单**：`@app:<别名>` 里的别名要对应到一个本地安装包与它的包名或 bundle id，且同一别名在 Android 与 iOS 上是两个不同的文件。这是结构化数据，环境变量表达不了。
- **本机后端的设备资源**：本机后端驱动真机时没有部署产生的 SSM 参数可读，Device Farm 项目 ARN 与放安装包的 S3 桶要由使用方给出。

这些值属于**项目**（与 feature 文件一起入库、团队共享），而不是某一次调用。同时它们必须对所有启动 worker 的宿主一致：同步 `run`、本机无状态批量运行的 per-run 进程与 `status --wait` 接力者、云端 Fargate 与 detached Lambda（[0034](./0034-detached-batch-reconciler.md)）——后两者看不到使用方机器上的任何文件。

## 决策

### 1. 文件定位：只有运行侧 CLI 读它，读出的值解析成具体值随 Job 走

- 文件名 `gherkai.toml`。查找规则：`--config PATH`、环境变量 `GHERKAI_CONFIG`、当前目录下的 `gherkai.toml` 依次优先。缺省位置不存在不算错（等同于没有配置文件）；显式给出的路径不存在、或文件不是合法 TOML，以退出码 2 结束并点名文件与出错位置。
- **读它的只有运行侧 CLI 进程**：`run`、`plan`、`submit`、`status`、`explain`、`doctor`、`list-deterministic`。worker、云端后端（Fargate、Lambda）、部署命令（`deploy`、`destroy`、`deploy push-worker`、`deploy list-workers`）都不读。
- **解析发生在组合根，产物是具体值**：CLI 把配置文件、选项、环境变量合成后的结果写进 definition 与 Job（具名的设备请求：设备 ARN 或筛选条件、`billing_method`、获取预算、项目 ARN；应用条目的完整 S3 位置与包名或 bundle id，字段形态见 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 3）。所有启动 worker 的宿主一律从 definition 读回，不重新解析配置文件。这沿用 [0037](./0037-distribution-and-packaging.md) 决策 4 对 `steps_dir` 的同一惯例：只有随 definition 走，三个本机宿主（各自 CWD 不同）与云端宿主才对同一个 run 一致，提交之后修改配置文件也不会改变已提交 run 的判定条件。
- 解析用 Python 标准库 `tomllib`（CLI 要求 Python 3.13 起），零新增依赖；CLI 只读不写，不提供 `config set` 一类改写命令。
- `doctor` 显示本次加载的配置文件绝对路径，或「未使用配置文件」，便于排查「我改的配置为什么没生效」。

不做什么：不向上级目录逐层查找（monorepo 里在子目录执行时会静默拿到另一个项目的文件，且与 `./steps` 相对当前目录的既有约定不一致）；不合并多份文件（无用户级 `~/.config` 叠加层，见被拒方案）。

### 2. 取值顺序：选项、环境变量、配置文件、内建默认依次优先

- 对每个可配置项，按上述顺序取第一个给出的值。没有对应环境变量的项，跳过该层。
- 配置文件排在环境变量之后，是因为环境变量是「本次调用的临时覆盖」的惯用载体（CI 矩阵、单次排障），文件是项目的稳定基线；反过来排会让 CI 里的环境变量被入库文件静默覆盖。
- region 因此依次取 `--region`、`AWS_REGION`、`AWS_DEFAULT_REGION`、配置文件的 `region`、AWS profile 配置里的 region，前者优先；gherkai 仍不自行补默认 region。
- **`default-job-timeout` 的最后一层不是固定值**：选项或配置文件给出的值都算「显式给出」（本项没有环境变量层）；都没有给时由 plan 层按 scope 的目标补缺省（桌面 300 秒；设备 scope 为获取预算加执行余量，显式值另受下限校验，设备 scope 不存在「不超时」）。覆盖与校验顺序归 [0034](./0034-detached-batch-reconciler.md)「job timeout」节与 [0019](./0019-feature-tags-scope-and-engine.md) `@timeout` 节，缺省数值归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2。
- **路径类值相对配置文件所在目录解析**（`steps-dir`、`[apps]` 里的 `file`，以及本机后端下的 `report-dir`）。`steps-dir` 解析成绝对路径后写进 definition；`file` 解析成绝对路径后用于上传，definition 里记的是上传后的 S3 位置（[0048](./0048-test-targets-device-and-ui-kind.md) 决策 3）；本机后端的 `report-dir` 决定报告与判定明细的落点，不进 definition。选项与环境变量里的路径仍相对当前目录，与现有行为一致。这样无论在项目哪一级目录执行，同一份文件给出同一组路径。**云端后端下 `report-dir` 不是路径**：它是产物桶内的键前缀，原样使用、不做绝对化，并与推进器 Lambda 的 `REPORT_DIR` 核对一致（[0033](./0033-iac-aws-backend-and-composition-wiring.md)、[0034](./0034-detached-batch-reconciler.md)），与选项、环境变量给出时同一形态。

### 3. 节与键

```toml
[common]                       # 跨命令选项（个别只对本机后端起作用，见下），键名为选项长名去掉 "--"
default-engine = "midscene"
steps-dir = "steps"
assertion-votes = 3

[cloud]                        # 只在 --backend cloud 下起作用的选项
prefix = "stage-"
worker-variant = "with-steps"

[devices]
billing-method = "METERED"     # METERED / UNMETERED
acquire-timeout-s = 900        # 示意值；获取设备的预算，默认值见 0051 决策 2
project-arn = "arn:aws:devicefarm:us-west-2:…:project:…"   # 只供本机后端
app-bucket = "my-team-gherkai-apps"                         # 只供本机后端

[devices.android]
arn = "arn:aws:devicefarm:us-west-2::device:…"

[devices.ios]
os-version = "18.6"            # 筛选条件，挑选规则见决策 4

[apps.wiki]
android = { file = "build/app-release.apk", package = "org.wikipedia" }
ios     = { file = "build/Wikipedia.ipa", bundle-id = "org.wikimedia.wikipedia" }
```

- **`[common]` 与 `[cloud]` 的键与选项同词**：键名是选项长名去掉前导 `--`、连字符保留（`--default-engine` 对应 `default-engine`）。值经与 argparse 同一套类型与取值范围校验，按 TOML 的原生类型直接校验、不经字符串：整数选项只接受 TOML 整数（浮点不截断、与命令行上给 4.7 同拒），浮点选项与自定义校验接受 TOML 整数或浮点，数字选项不接受文本（TOML 里 `"4"` 是文本），布尔一律拒绝；非法值的报错形态与在命令行上给错一致，内建类型的失败给产品语言的理由。某个键对当前命令不适用（如 `grace` 之于 `plan`）时忽略，因为配置文件是项目级的、各命令只取自己有的那几项。`[devices]` 的键不受同词规则约束：命令行上设备选项平铺、要带平台或服务前缀，配置文件里有节层级、不需要前缀，对应关系见决策 4 与决策 6 的映射表。
- **可配置的只是「环境型」选项**：后端与资源名、引擎与 step 目录、投票与预算、并发、隧道、variant 一类每个项目基本固定的值。**按次选择型选项不进配置文件**：`--scope`、`--tags`、`--scenario`、`--step`、`--json`、`--quiet`、`--wait`、`explain` 的 `--all` 与 `--full`、`run` 的 `--fail-fast` 与 `--no-report`、`list-deterministic` 的 `--engine`、`--config` 本身以及位置参数。判据：只影响本次的范围、输出形态、中止方式、落盘取舍或查询对象的选项，都属按次选择型。把它们写进文件，会让某次调用的范围、输出或中止语义在不显眼处改变（如 `--fail-fast` 入库后其余 job 会被悄悄跳过，`--no-report` 入库后报告悄悄缺失），排查成本远高于每次多输入一个选项。`submit` 的 `--tunnel-ttl` 属环境型，与隧道一类同样可配置。
- **未知键以退出码 2 结束**，点名文件、节与键名。拼错的键若被静默忽略，表现是「配置没生效」，比直接报错更难发现（与 [0036](./0036-deterministic-capability-discovery.md) 对自述契约 fail-loud 同一取向）。
- **只对本机后端起作用的 `[common]` 键（如 `grace`）在 `--backend cloud` 下不生效、只提示一句**，与 `project-arn` / `app-bucket` 同一形态；命令行上显式给出仍按 [0024](./0024-worker-core-protocol.md) 拒绝。
- **`[devices]`**：每个平台一张子表 `[devices.android]` / `[devices.ios]`，二选一给出 `arn`（指定一台设备）或 `os-version`（平台加系统版本的族匹配，必须写成 TOML 字符串——写成数字会被解析成浮点，以退出码 2 结束并提示加引号），两者都给以退出码 2 结束。`billing-method` 内建默认 `METERED`，可在平台子表里覆盖（不计量槽位按平台购买）；月用量足够大时 `UNMETERED`（不计量槽位）更便宜，取舍见实测依据。`acquire-timeout-s` 的默认值与上界见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2，超出预算记 `acquire_timeout`（处置语义同在 0051）。
- **`project-arn` 与 `app-bucket` 只供本机后端**：云端后端的 Device Farm 项目由 `gherkai deploy` 建立、ARN 存 SSM，安装包放进现有产物桶（项目与 SSM 见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 10，产物桶见决策 9）。`--backend cloud` 下文件里给了这两项，提示一句「云端后端使用部署时建立的项目与产物桶，本项不生效」、不拦截，与 [0037](./0037-distribution-and-packaging.md) 决策 4 对云端 `--steps-dir` 的处理同一形态。两项是与账号、区域绑定的资源名，不是凭据：团队共用同一个账号时可以入库共享；项目要在多个账号或环境中执行时，改用 `GHERKAI_DEVICE_FARM_PROJECT_ARN` / `GHERKAI_APP_BUCKET` 按环境给出，入库值会被环境变量覆盖（决策 2）。本机后端下 `project-arn` 里的账号与当前凭证所属账号不一致时，CLI 在提交前警告并点名两个账号，不拦截。
- **`[apps]`**：每个别名一张子表，按平台各给一个条目：`file`（本地安装包，相对配置文件目录）加 `package`（Android）或 `bundle-id`（iOS），两者都必须显式给出（不靠 Appium 推断启动活动，理由见 [0051](./0051-device-session-lifecycle-and-app-distribution.md)）。`@app` 引用的别名不在 `[apps]` 里、或该别名缺少 scope 所在平台的条目，按 [0048](./0048-test-targets-device-and-ui-kind.md) 报 FeatureContractError；`plan` 同样报错，因为它只读本地文件、不违背零 AWS。安装包的上传（按内容哈希放进桶）发生在 `run` / `submit`，`plan` 只核对文件存在。

### 4. 设备选择要求显式，筛选的挑选规则确定

- **不自动挑设备**：run 里有某平台的设备 scope、而该平台既没有选项或环境变量给出的 ARN、配置文件里也没有 `[devices.<平台>]`，`run` / `submit` 在提交前以退出码 2 结束；`plan` 在输出里标出该平台未指定设备并在 stderr 警告，退出码仍为 0（缺的是执行环境，不是 feature 契约）。用户可见消息示例：

  > 这个 run 里有在 Android 设备上执行的 scope，但没有指定用哪台设备。请在 gherkai.toml 的 [devices.android] 里给出 arn 或 os-version，或用 --android-device-arn 指定。

- **选项与环境变量**：`--android-device-arn` / `--ios-device-arn`（环境变量 `GHERKAI_ANDROID_DEVICE_ARN` / `GHERKAI_IOS_DEVICE_ARN`）、`--device-farm-project-arn`（`GHERKAI_DEVICE_FARM_PROJECT_ARN`）、`--app-bucket`（`GHERKAI_APP_BUCKET`），按决策 2 的顺序覆盖配置文件。按平台分开命名，是因为一个 run 可以同时含 Android 与 iOS 的 scope，单个 `--device-arn` 无法表达。筛选条件只在配置文件里给，命令行只接受 ARN。
- **ARN 直接使用**：CLI 只核对 ARN 的服务与资源类型段（设备 ARN 形如 `arn:aws:devicefarm:<区域>::device:<id>`、项目 ARN 形如 `arn:aws:devicefarm:<区域>:<账号>:project:<id>`，零 AWS 调用；拦的是把项目 ARN 或设备池 ARN 贴进设备 ARN 这类最常见的错，提交前以退出码 2 结束并点名贴错的类型），之后 worker 以该 ARN 建立远程访问会话，不事先查可用性、不做静态过滤；该机型全部单元被占用时会话排队等待，与并发排队同处置，受获取预算约束；ARN 被同步拒绝（不存在、已下架、不支持远程访问）记 `precheck_failed`（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 3）。
- **筛选条件由 worker 在获取设备时解析**（不是 CLI 在提交时解析）：设备可用性随时间变化，detached 提交可能在数分钟后才真正启动 worker，提交时解析出的 ARN 到那时可能已不可用。本篇只定用户面语义，解析算法归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 3：
  - `os-version` 按点分段的族匹配——配置值按点切段，设备版本的前几段完全相等即命中（`18` 命中 `18.x.y`，`18.6` 命中 `18.6` 与 `18.6.2`、不命中 `18.60`，`18.1` 不命中 `18.10`），写全段即精确匹配；`plan` 对按系统版本挑选的平台一律注明命中范围，并提示「设备池新增版本时实际分到的版本可能改变，写全版本号可以固定」（`plan` 不调用 Device Farm，无从判断某个值是否已写全）。
  - 只取手机形态与支持远程访问的设备；零候选不进入繁忙等待，记 `precheck_failed`（再列举一次的判据见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 3），消息给出条件与最接近的可用版本。
  - 匹配候选中先排除繁忙与暂不可用的设备，再按版本号高、可用性高、ARN 字典序取第一台；全部繁忙才在获取预算内等待，预算用尽记 `acquire_timeout`，消息说明「符合条件的设备当前都忙」与所用的筛选条件。
- 排序确定，是为了同一份配置在设备池不变时总选中同一台设备、判定可复现；实际分到的机型与系统版本由 evidence 的 scope 表头记录（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8），设备池变化导致的换机因此可追溯。`plan` 不调用 Device Farm，只原样展示配置的 ARN 或筛选条件。

### 5. 与 ADR 0044 覆盖链的关系：worker 侧覆盖项不进配置文件

- 引擎模型（`NOVA_MODEL_ID`、`MIDSCENE_MODEL_ID`、`MIDSCENE_MODEL_FAMILY`）、`NOVA_ACT_TIMEOUT_S`、设备目标的重规划上限（[0052](./0052-appium-interface-adapter-and-platform-differences.md)）等 **worker 侧覆盖项**，继续走 [0044](./0044-engine-model-selection-and-override.md) 决策 2 的覆盖链：本机 shell 的环境变量、云端 variant 镜像的 `ENV`。配置文件不收这些键。
- 理由：配置文件只有 CLI 读（决策 1）。若让它承载 worker 侧覆盖项，CLI 就得把值注入本机 spawn、per-run 进程、`status --wait` 接力者、云端 RunTask 与 detached Lambda 各条路径，正是 [0044](./0044-engine-model-selection-and-override.md) 拒绝 run 级 `--model` 时指出的「四个注入面四处漂移」；配置文件不重新打开该决定。
- 配置文件也不收凭证与密钥：AWS 凭证走默认凭证链，`NGROK_AUTHTOKEN` 留在环境变量或 ngrok 自己的配置。`gherkai.toml` 预期入库，密钥进去即泄漏。

### 6. 护栏

- **键集差集**：测试从 argparse 定义推出各命令的长选项全集，断言它恰好等于「决策 3 的按次选择型排除名单 + `[common]` / `[cloud]` 的同词键 + 设备映射表」三者之和；新增选项时漏改任一侧即失败。排除名单与设备映射表都在测试里显式列出，新增选项必须有意识地归入其中一类。设备映射表：`--android-device-arn` 对 `[devices.android] arn`、`--ios-device-arn` 对 `[devices.ios] arn`、`--device-farm-project-arn` 对 `[devices] project-arn`、`--app-bucket` 对 `[devices] app-bucket`。这四项是环境型、在配置文件里有键，不能放进排除名单——那等于在测试里写一条「不可配置」的假事实。`[devices]` 里没有对应选项的键（`os-version`、`billing-method` 及其平台覆盖、`acquire-timeout-s`）由解析器的接受集与本 ADR 决策 3 的键表直接对照，表里多一键或少一键都失败。
- **云端 `report-dir` 不绝对化**：测试覆盖云端后端加配置文件 `report-dir` 的情形，断言交给前置检查与存储的值与文件里的原值逐字相同。
- **设备段的形态**：测试覆盖平台子表 `arn` 与 `os-version` 二选一（都给以退出码 2 结束；平台有设备 scope 而任何来源都没有给出选择时，`run` / `submit` 以退出码 2 结束、`plan` 只警告，见决策 4）、`os-version` 写成 TOML 数字时的退出码 2 与加引号提示、`billing-method` 的平台覆盖、以及本机后端下 `project-arn` 账号与当前凭证账号不一致的告警文本；解析结果断言为 Job 里的具名设备请求（[0048](./0048-test-targets-device-and-ui-kind.md) 决策 3）。
- **路径基准**：测试覆盖在子目录执行、`--config` 指向别处两种情形，断言 definition 里的路径以配置文件目录为基准。
- **宿主不读文件**：测试断言 worker 注入 env 与 Job 载荷由 definition 生成，`status --wait` 接力者在另一 CWD 下得到与提交时相同的设备与应用值。

## 实测依据

以下数字来自在 Device Farm（us-west-2）从美国出网的公共真机上对远程访问会话的逐项实测，支撑决策 3、4 的形态：

| 观察 | 数据 | 支撑的决策 |
|---|---|---|
| 同一账号远程访问并发 | 同机型连发 6 个会话请求，前 5 个进入 RUNNING，第 6 个进入 `PENDING_CONCURRENCY` 排队而不是报错；排队实测最长约 6 分钟；排队中撤回的会话返回体与 Get 都没有 `deviceMinutes` 字段，是否计费以账单为准 | 获取预算必须可配，且要覆盖排队时间 |
| 取设备开销 | 创建到 RUNNING：Android 51 到 92 秒、iOS 61 到 82 秒；加上 Appium 建连，创建到 Appium 可用约 1 到 2.5 分钟，计入 job 墙钟，并计入服务商回报的设备分钟 | `acquire-timeout-s` 的默认值不能低于分钟级 |
| 停止到 COMPLETED | Android 52 到 85 秒，iOS 超过 2 分钟（最长约 150 秒），只计入服务商回报的设备分钟、不占 job 墙钟 | 费用口径以账单为准、估算时不能漏掉收尾一段；与获取预算无关 |
| 计费方式的拐点 | 不计量槽位 250 美元每月除以计量单价 0.17 美元每分钟，约 1470 分钟每月每平台 | `billing-method` 必须可选，而不是内建固定 |
| 系统版本决定能力 | iOS 15.8 的 Safari 网页上下文完整可用，iOS 26.3 的网页上下文整体不可用 | 筛选条件以系统版本为必给项，而不是只按平台挑 |
| 设备忙 | 历次实测中未遇到机型被占满（BUSY）的情形；指定 ARN 而设备被占用时的会话状态在 API 状态枚举里是 `PENDING_DEVICE`（排队等设备），同机型 5 台并发都分到了不同单元 | 筛选时排除繁忙设备是保守选择（算法归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 3）；指定 ARN 时的等待由获取预算处理 |

## 被拒方案（护栏）

- **自动挑设备（未配置时按平台任选一台）**：设备分钟按会话计费，静默选机让使用方在不知情时付费；设备池变化会让同一份配置换到不同机型与系统版本，判定不可复现，而系统版本恰恰决定网页上下文是否可用。
- **云端后端或 worker 读配置文件**：云端宿主看不到使用方机器上的文件；即便随 definition 上传整份文件，也会让「值在哪一层被解析」出现第二处，且提交后改文件可能改变已提交 run 的行为。
- **CLI 在提交时把筛选条件解析成 ARN**：detached 提交到 worker 真正启动之间有时间差，提交时可用的设备到时可能已忙；同时让 `plan` / `submit` 需要 Device Farm 读权限，破坏 `plan` 的零 AWS。
- **配置文件优先于环境变量**：CI 与单次排障惯用环境变量做临时覆盖，被入库文件覆盖后表现为「设了不生效」。
- **用户级配置文件叠加（`~/.config/gherkai/…`）**：多份文件合并让同一个仓库在不同机器上得到不同值，排查时要同时看两处；1.5 的需求是项目级共享，单文件足够。
- **向上级目录逐层查找**：在 monorepo 子目录执行时可能拿到另一个项目的文件，且与 `./steps` 相对当前目录的既有约定冲突。
- **YAML 或 JSON**：YAML 需新增依赖且隐式类型转换易出错（`NO` 变布尔、版本号 `18.10` 变浮点）；JSON 不能写注释。TOML 由标准库直接读取，Python 使用方也熟悉 `pyproject.toml`。
- **配置文件承载引擎模型等 worker 侧覆盖项**：见决策 5，等于以另一种形态重新引入 [0044](./0044-engine-model-selection-and-override.md) 已拒的多注入面。
- **静默忽略未知键**：拼错的键表现为「配置没生效」，比报错更难排查。

## 边界与互链

- [0048](./0048-test-targets-device-and-ui-kind.md)：`@device` 与 `@app` tag 的语义、Job 里 target 与设备请求的形态、别名缺失时的 FeatureContractError；本 ADR 只定这些值从哪里来。
- [0049](./0049-worker-capabilities-targets-keys.md)：worker 能力自述的 `targets` 与 `max_session_s`；worker 自检据它记 `precheck_failed`，与配置文件无关。
- [0050](./0050-deterministic-step-handles-and-testing.md)：确定性 step 的多句柄注册；`steps-dir` 只是其目录的又一个取值来源。
- [0051](./0051-device-session-lifecycle-and-app-distribution.md)：设备解析的算法（列举、静态过滤、选择、零候选与繁忙等待）、获取预算的默认值与上界、超时类别、安装包的键布局、保留承诺与预签名、Device Farm 项目的建立与 SSM、权限（登记在 [0033](./0033-iac-aws-backend-and-composition-wiring.md)）、`billingMethod` 的费用模型。
- [0052](./0052-appium-interface-adapter-and-platform-differences.md)：重规划上限等驱动侧固定规则及其覆盖方式。
- [0044](./0044-engine-model-selection-and-override.md)：worker 侧覆盖项的覆盖链，本 ADR 不改变它。
- [0037](./0037-distribution-and-packaging.md) 决策 4：「解析在组合根、随 definition 持久化」的先例，本 ADR 把它推广到全部配置项。
- [0034](./0034-detached-batch-reconciler.md)：本机无状态批量运行的三个宿主与 detached 后端，决定了配置值必须随 definition 走。
