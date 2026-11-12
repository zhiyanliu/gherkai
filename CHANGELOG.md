# 变更记录

本文件按发行版记录 gherkai 对使用者可见的变化：新增的命令与选项、行为与默认值的调整、修复的问题，以及升级时需要执行的动作。每个发行版在这里都有一节，GitHub Release 的正文取自对应的一节。每个版本的 Release 页（1.4.0 起）见 [GitHub Releases](https://github.com/zhiyanliu/gherkai/releases)。

全部发行包同号发布：命令行工具、两个引擎 worker 与云端后端须装同一个版本。命令与选项的完整说明见[用户指南](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/README.md)，环境变量总表见[配置](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/configuration.md)。

格式沿用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### 新增

- 引擎 worker 的能力自述带上支持的测试目标：`gherkai doctor` 多一行 `engines.targets.<引擎>`，显示该引擎支持的测试目标（Nova Act 只有桌面网页；Midscene 另有 Android 与 iOS 的网页与应用，这两个设备目标带 8880 秒的会话上限，`doctor` 把它换算成分钟附在目标后面，job 墙钟预算超过它的设备 scope 在执行前被拒绝）；`gherkai list-deterministic` 多一列「目标」，显示每条确定性 step 在该引擎上实际可用的目标，声明了该引擎不支持的目标时单独注明；`--json` 每项多 `targets`（worker 原样报出）与 `available_targets`（与引擎支持的目标求交后的结果）；worker 的能力自述缺「支持的测试目标」时，命令行工具按版本不一致拒绝。
- 用户指南新增[引擎能力矩阵](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/engines.md)一页：引擎 × 测试目标 × 确定性 step 的句柄 × 默认模型 × 计价公式。
- 确定性 step 可按句柄种类给多份实现：注册时第二个参数从单个函数换成按种类分键的对象（Midscene：`{ playwright, webdriver: [...] }`）或字典（Nova Act：`deterministic(pattern, {...}, description=…, example=…)`，字段名用下划线）；传单个函数仍等价于只有 `playwright`，已有的 `steps/` 不需要改。每个 `webdriver` 条目用 `uiKinds`（web / app）与 `devices`（android / ios）声明适用范围：条目适用于两个列表取值的全部组合，不写的列表取全部取值；可声明前提 `requires: ["web_context"]`。能力自述、`gherkai list-deterministic` 的「目标」列与 `gherkai plan` 的标注按条目推出每条 step 的目标（固定顺序：桌面、Android、iOS）。命中的 step 在当前目标上没有实现时改由 AI 执行，不会改用另一条也能匹配这段文本的 step，`gherkai plan` 对这类 step 不标「确定性」并在提示里说明原因。不认识的句柄种类或取值、带 `web_context` 的条目 `uiKinds` 不是恰好 `["web"]`、两个条目覆盖同一个（设备, 界面类型）组合，都在注册时被拒、worker 不启动并点名文件。Midscene 的 `webdriver` handler 拿到七个字段的上下文（`driver`、`device`、`uiKind`、`appId`、`app`、`log`、`withWebContext`）；Nova Act 没有设备路径，Python 侧的 `webdriver` 条目只进清单、不被调用。仓库模板 `features/steps/url_matches.mts` 改为两份实现。
- 设备 scope 用哪台设备要显式指定，不自动挑：按平台用 `--android-device-arn` / `--ios-device-arn`（环境变量 `GHERKAI_ANDROID_DEVICE_ARN` / `GHERKAI_IOS_DEVICE_ARN`）给设备 ARN，或在 `gherkai.toml` 的 `[devices.android]` / `[devices.ios]` 里给 `arn` 或 `os-version`（按系统版本族挑选，只能在配置文件里给）；计费方式 `billing-method` 与获取预算 `acquire-timeout-s` 在 `[devices]` 里给、平台子表可覆盖计费方式。有设备 scope 的平台没有任何来源指定设备时 `run` / `submit` 在提交前以退出码 2 结束，`plan` 只标注并警告。设备 ARN 与项目 ARN 只核对服务与资源类型段，贴错类型（如把项目 ARN 贴进设备 ARN）在提交前以退出码 2 结束并点名。本机后端另需 Device Farm 项目：`--device-farm-project-arn`、环境变量 `GHERKAI_DEVICE_FARM_PROJECT_ARN` 或 `[devices] project-arn`，项目所属账号与当前凭证不一致时警告不拦；云端后端用部署时建立的项目，部署没有建立项目时提交以退出码 2 结束、提示「部署未启用设备支持」。`plan` 的每个 job 行显示测试目标（如 `target=android/app:shop`，桌面 job 为 `target=desktop/web`），表头给出这次 run 要建立的远程访问会话数；`plan --json` 多 `device_session_count` 与 `devices` 两键，文本视图每个平台一行设备标注。
- `@app:<别名>` 的 scope 可以运行与提交：`run` / `submit` 把 `gherkai.toml` 的 `[apps.<别名>.<平台>]` 指向的安装包按内容哈希放进 S3 （键 `apps/<sha256>/<文件名>`，同一文件一个 run 只传一次），把位置写进提交记录；云端后端放进部署的产物桶、对象带标签 `gherkai=app`、按 14 天过期、已提交 run 引用的对象至少保留 7 天（复用时按对象年龄刷新）；本机后端放进 `--app-bucket`、环境变量 `GHERKAI_APP_BUCKET` 或 `[devices] app-bucket` 指定的桶，只复用不打标签不刷新。安装包不存在时 `plan` / `run` / `submit` 以退出码 2 结束；超过 500 MB 警告不拦。
- **Midscene 引擎在 Android 与 iOS 真机上执行设备目标的 scope**（Nova Act 仍只支持桌面网页）。每个设备 scope 在 AWS Device Farm（us-west-2）建立一个远程访问会话、经 Appium 执行：只标 `@device` 的 scope 测设备上的浏览器（Android 的 Chrome、iOS 的 Safari），再标 `@app` 的 scope 先把安装包装到设备上、启动被测应用再执行；同一 scope 的 scenario 之间不重启应用。AI step 的写法与桌面相同，确定性 step 调用它的 `webdriver` 实现。worker 在第一条 scenario 之前探测一次设备能力（是否提供网页上下文、坐标比例），设备不提供某条 step 需要的能力时这一步记 `capability_unavailable`、不交给 AI。scope 级的新错误类别：设备、安装包或驱动辅助程序的问题在执行任何 step 之前记 `precheck_failed`（没有符合条件的设备、安装包不在或不可读、应用启动后立即自行退出、设备拒绝安装驱动辅助程序等，消息分别给出处置）；在获取设备的等待时间（`acquire-timeout-s`）内没有拿到可用设备记 `acquire_timeout`；会话在执行中途结束或到达会话上限记 `session_lost`，本 scope 余下的 scenario 不执行。设备命令在等待时间内没有回应时这一步记 `engine_error`，消息说明这一步可能已执行也可能未执行，本 scenario 余下的 step 不执行。设备上 Midscene 的重规划上限缺省为 12，可用环境变量 `MIDSCENE_REPLANNING_CYCLE_LIMIT` 调整；取值不是正整数时 worker 在建立任何会话之前报错退出，桌面 run 同样核对这个值。
- 内建导航在设备目标上可用：网页目标打开地址（设备不提供网页上下文时交给设备的系统浏览器打开），应用目标把地址（任意 scheme）经 DeepLink 交给被测应用；iOS 上这一步只保证地址已送达、应用在前台，应用忽略这个链接时这一步照样通过，请紧跟一条落点核对；被测应用不处理该地址（Android）或这台设备不支持经系统打开地址（iOS）时，这一步记 `capability_unavailable`；Android 上地址里的 `;`、`'`、`(`、`)` 以及中文等地址中不允许出现的字符要先百分号编码，否则这一步记 `capability_unavailable`；任何目标上，地址里有未编码的空格时整句不算地址、这一步交给 AI，空格要写成 `%20`。`gherkai list-deterministic` 与 `gherkai plan` 里它的目标多出 Android 与 iOS 的网页和应用。仓库 `features/steps/` 多一个 Midscene 侧模板 `restart_app.mts`（`Given 重新启动应用`）：在应用目标上关闭并重新启动被测应用，并确认它没有在启动后自行退出，供需要干净起点的 scenario 写在 `Background` 里。
- 设备目标的 step 证据与诊断文件：设备上判为 failed / error 的确定性与导航 step 也产出证据（`acts` 为空），证据多出这一步的执行方式（`step_kind`）与 step 结束时的页面地址或取不到的原因（`url` / `url_missing`），判为 failed / error 的 step 另有控件摘要（`controls`）与原始控件树文件（`page_source`，写盘前脱敏，超过大小上限时截断并注明）。原始控件树在本机后端落在 `<report-dir>/<run_id>/midscene-run/device/` 下、按 scope 分目录，云端后端在产物桶的同一相对位置。每个设备 scope 另写一份诊断文件 `device-session.json`（能力探测结论、所用会话与设备、换台记录、从获取设备到释放各阶段的时刻、执行前失败的原因、释放时是否有会话未能确认停止），在判定记录里以 `device_session` 链接给出。这些采集按 step 累加计入 job 的墙钟预算。
- `gherkai deploy` 在部署 stack 之前找回或建立 Device Farm 项目 `<prefix>devices`（us-west-2），把项目 ARN 写进后端参数 `/<prefix>backend/device-farm-project`，并给 Midscene worker 授予在这个项目里使用设备所需的权限，供带设备目标的云端 run 建立会话使用。部署方的凭证需要 us-west-2 上的 `devicefarm:ListProjects`、`GetProject` 与 `CreateProject`；没有这些权限时部署照常完成并警告：后端仍记录着项目 ARN 时沿用该记录，否则这套后端不启用设备支持（记录的项目已被手动删除而又无法找回或新建时同样不启用）。同名项目不止一个时以退出码 2 结束并列出命中的项目 ARN，找回或建立项目时遇到限流、网络等其他错误以退出码 1 结束，两种情形都不部署 stack。`gherkai deploy --diff`、`--synth-only` 与 `gherkai destroy` 不建立项目，只读后端记录的项目 ARN；`--diff` 另核对记录的项目是否还在，项目已删时按未建立项目显示变更集，缺核对权限时只警告。读不到后端记录的项目 ARN 时（凭证不可用、缺 `ssm:GetParameter`、网络、限流），`gherkai deploy`、`--diff`、`--synth-only` 与 `gherkai destroy` 都以退出码 2 结束、不调用 cdk；后端记录的项目 ARN 被手工改成不合法的值时，这四个动作同样以退出码 2 结束、不调用 cdk，并给出查看项目 ARN 的命令；`--diff` 核对记录的项目时遇到限流、网络等权限以外的错误同样以退出码 2 结束、不输出变更集。唯一例外是 `--synth-only` 在完全没有 AWS 凭证时照常离线导出，模板按未启用设备支持生成、不含远程访问会话的授权，并警告它可能与已部署的 stack 不一致。
- `gherkai doctor --backend cloud` 多两行：`backend.devices.project` 显示这套后端是否启用了设备支持（部署建立的 Device Farm 项目 ARN），`backend.devices.sessions` 列出项目里还没结束的远程访问会话（含排队中的），每条带控制台链接与停止命令。两行都不影响退出码；列举会话需要 us-west-2 上对这个项目的 `devicefarm:ListRemoteAccessSessions` 权限，缺这项权限时这一行说明缺什么。
- 项目配置文件 `gherkai.toml`：把每个项目基本固定的选项写进文件、随 `.feature` 一起入库共享。`run` / `plan` / `submit` / `status` / `list-runs` / `explain` / `doctor` / `list-deterministic` 读它，按 `--config`、环境变量 `GHERKAI_CONFIG`、当前目录的 `gherkai.toml` 依次查找，不向上级目录查找；取值顺序是命令行选项、环境变量、配置文件、内建默认依次优先。`[common]` 与 `[cloud]` 的键与选项长名同词（`default-engine`、`steps-dir`、`prefix` 等；`[cloud]` 只在 `--backend cloud` 下生效），只影响本次调用的选项（`--scope`、`--tags`、`--json`、`--fail-fast` 等）不进文件；`[devices]` 给设备选择与计费方式，`[apps]` 给 `@app:<别名>` 对应的安装包与包名或 bundle id。路径类值（`steps-dir`、本机后端的 `report-dir`、`[apps]` 的 `file`）相对配置文件所在目录。不认识的节或键、取值不合法（含整数选项写成浮点，如 `max-concurrency = 4.7`）、`os-version` 写成数字都以退出码 2 结束并点名文件与位置。`gherkai doctor` 多一行 `config.file` 显示本次加载的配置文件。
- 判定记录带远程访问会话的字段：`run --json` 与 `explain --json` 的 job 可带 `sessions[]`（每个远程访问会话的名称、来源、是否确认停止、占用秒数）与 `device_observed_s` / `device_observed_missing` 两个计量键，run 级同样合计；两个计量键只出现在设备用例上，桌面用例的 `sessions[]` 见「变化」里浏览器会话的建立与停止一条。文本输出与报告页对设备 job 显示设备描述、Device Farm 控制台链接、设备占用时长，并列出未能确认停止的会话名；`explain` 对设备目标的证据显示这一步的执行方式、页面地址、控件摘要与控件树文件地址，设备上判为 failed / error 的 step 缺证据时按抽取失败提示。worker 在被测对象未就绪时报出的 scope 级错误会把未执行的 scenario 标为 `skipped`、旁注「未执行（scope 级错误，原因见 job 判定）」。
- 前台 `run` 支持使用方中断：按一次 Ctrl-C（或向命令进程发 SIGTERM）后，命令请求全部 worker 停止并等它们释放会话，再照常输出汇总与产物位置；退出码为 130（Ctrl-C）或 143（SIGTERM），不表示判定；有 job 被中止或跳过时，run 级判定记 `aborted`，被中止的 job 的判定消息写明「收到中断信号」。再按一次时，本机后端立即结束 worker，云端后端（`run --backend cloud`）只重发停止请求、不能缩短等待；两种情形下会话都可能来不及释放，命令会提示到控制台核对。说明见[运行测试与查看结果](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md)。
- 设备目标上多一个供 AI 使用的「收起键盘」动作：用例写「输入 … 后收起键盘」时，Android 由系统收起键盘，iOS 只点键盘上的 Done / 完成键或键盘上方工具栏里的 Done（Safari 给网页输入框配的那一条、应用自己加的工具栏），不按 Return 键、不点空白处；收不起时这一步以「键盘仍然显示」为由判出错并说明原因与改法，不再反复重试。写法与边界见[编写 .feature](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-features.md)「设备上的软键盘」一条。
- `gherkai explain` 对被中止或出错的 job 补取已执行 step 的记录与证据：worker 被中止时未执行完的 scenario 不进判定明细，此前这些 step 只显示「无记录」；现在从这个 run 的事件流补取（`--json` 里这些 step 的 `record_source` 为 `events`、所属 scenario 带 `unfinished`），文本形态在 step 行尾标「记录取自事件流」。为此本机前台 `run` 也把 worker 事件记录写到产物目录的 `events.db`（与 `submit` 同一文件），`--no-report` 不写；云端后端下 `explain` 对这类 job 另需 events 表的 `dynamodb:Query`，见[云端后端](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md)「团队成员需要的最小云端权限」。
- `gherkai list-runs` 列出一个后端里的 run，用来找回 run_id（换了终端、提交时没有记下、或要查看别人提交的 run）。定位选项（`--backend`、`--report-dir`、`--prefix`、`--region`、`--profile`、`--ddb-table`）与 `status` 相同，同样读 `gherkai.toml`；一次只列一个后端，云端后端下 `--report-dir` 给了也忽略。默认列出全部还没结束的 run 与最近创建的 20 条已结束的 run，新创建的在前；`--limit N` 改已结束部分的条数，`--status S`（可重复）只列这些状态。表格每行给出状态、开始与结束时刻（本机时区）、job 数、版本与提示：「版本」列给出写出这个 run 的 gherkai 版本，由当前版本写出的在版本后带 `*`，表格上方一行点明当前版本（当前版本取不到时没有这一行与 `*`）；运行状态读不出的行标「无法读取」并照样列出；还没结束、由前台 `run` 执行的 run 提示执行它的进程若已不在、它不会再到终态。清单为空时只打一行提示，点名所查的落点。`--json` 顶层给出所查的落点、当前 gherkai 版本与 `runs` 数组，每项带写出它的版本。命令只读，退出码 0 表示读到了清单（清单为空也是 0），2 表示参数不合法或读不到这个后端。云端后端需要运行记录表索引上的 `dynamodb:Query` 与表上的 `dynamodb:BatchGetItem`，后端要重新部署才有这个索引（见「升级须知」）。agent skill 同步教 agent 用它找回 run_id。说明见[运行测试与查看结果](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md)「找回 run_id」一节。

### 变化

- 两个引擎把失败原因压成一行时对同一段文本给出逐字相同的结果：只按 CR / LF 分行、按同一张空白字符表折叠，再脱敏、按字符数截断；含 U+2028、U+0085、U+000B 这类字符的文本不再在 Nova 侧被截掉后半段，只含这类空白的错误说明按空处理、改用异常本身的文本。
- 本机应用测试（`--expose-local`）的隧道改为「令牌换 cookie」：不再把 basic-auth 凭据内嵌在地址里。每次运行生成专用的访问令牌与会话 cookie 值，写进这次运行的 ngrok 流量策略（边缘节点拦截，不带 cookie 的请求到不了你的机器）；step 文本只替换成干净的隧道地址；引擎 worker 在第一个场景之前访问一次「会话预热地址」换到 cookie。同一套隧道对设备上的网页目标（Android 的 Chrome、iOS 的 Safari）同样可用；原生应用自己访问的后端地址打包在应用里、不经隧道替换，应用目标连本机或私网后端在本版本不受支持。预热被拒绝时，令牌被拒与会话 cookie 未通过校验给出不同的提示与处置。本机后端的 worker 不声明会话预热支持时在起隧道之前以退出码 2 拒绝。隧道地址在 step 文本里的识别带边界：`http://localhost:3000.evil/`、`http://localhost:30001/x` 不再被当成 `http://localhost:3000` 替换，`去 http://localhost:3000。`、`(see http://localhost:3000)` 照常替换。
- 脱敏规则从一条扩成三条：除地址里的 `用户:口令@` 外，`X-Amz-Signature` / `X-Amz-Security-Token` / `X-Amz-Credential` / `gherkai_tunnel_token` 这四个查询参数的值（含控件树里 `&amp;` 转义的形态）与 Device Farm 远程端点地址里的路径令牌也显示为 `***`；`X-Amz-Date`、`X-Amz-Expires` 等不是凭证的参数保留明文。两个引擎 worker 自己写出的诊断日志也在写出时脱敏，本机转发的与云端写进 CloudWatch 的都是如此，引擎 SDK 自己写出的内容除外。落盘的运行定义（`run_meta.json`）仍是明文，运行要读回它。
- Nova Act 引擎的 worker 自己管理云端浏览器会话的启动与停止：停止有超时预算，停止失败或超时时 job 记为 error（scenario 明细保留，退出码 1）；此前停止由 SDK 内部执行，部分失败不会反映在退出状态里。Nova Act 的 job 记录的会话 id 随之改为 AgentCore 浏览器会话 id（与 Midscene 同一种 id；此前是 Nova Act 服务侧的会话 id）；`nova-trajectories/` 下的子目录仍按 Nova Act 侧的会话 id 命名，不再等于 job 记录里的会话 id，worker 日志里有两者的对应行。
- `gherkai deploy push-worker` 的平台校验认得 containerd 镜像存储（Docker 29 起新装的缺省）下的多平台索引：本机有 linux/amd64 内容的镜像照常通过，没有时提示只构建 linux/amd64 一个平台；此前这类镜像被报成「平台是 ?/?」。
- `gherkai deploy push-worker` 与 `gherkai deploy` 不再沿用上次中断时留下的任务定义 revision：只有映射已指向用当前任务定义模板与同一镜像注册、且仍可用的 revision 时才跳过注册，其余情形一律注册新的 revision，中断留下的那个由之后的清理补记退休时刻、满 1 小时后回收（只多一条任务定义，镜像层共用）。映射指向的 revision 已被注销或删除时，用同一镜像再执行一次 `push-worker`（`base` 也可再执行一次 `gherkai deploy`）即注册新的 revision、替换映射。被替换的旧 revision 的退休时刻改为在映射替换之后记下，替换时没能记下的由之后的清理补记，回收一律从记下的时刻起满 1 小时才进行；清理在运行记录表的索引尚未就绪或查询失败时不回收任何 revision，并打印一行警告。`gherkai deploy list-workers` 的待清理条目只列不被任何版本的映射引用的 revision，`reason` 为 `retired` 表示已记下退休时刻、`orphan` 表示还没有记下、由后续清理在满足条件时补记。部署方的凭证需要补上 `ecs:UntagResource` 与运行记录表上的 `dynamodb:DescribeTable`；提交云端 run 的凭证需要补上 `ecs:ListTaskDefinitions`：读不到映射所指的任务定义 revision 时，提交前检查用它确认 revision 是否已被删除，确认已删除才提示重新推送，其余读取失败按凭证与权限问题报告。
- 提交记录（`run_meta.json`、云端运行状态表里的提交记录，以及 `run --json` 与 `plan --json` 里的 `run_meta` / `jobs[]`）带结构版本 `schema_version`（整数，本版本为 1）与写出它的 `cli_version`；键集固定、不适用的值写 `null` 而不再省键：`timeout_s` 不超时为 `null`，`target` 对桌面 job 也写出 `desktop` / `web`，`device_request` 非设备 job 为 `null`，`steps_dir`、`worker_variant`、`worker_task_defs`、`extra_http_headers` 无值为 `null`。`status` / `explain` 与本机接力读到结构版本不等于本机支持的记录以退出码 2 结束，并点名写出它的版本：更新的提示升级 gherkai，更早的提示用那个版本查看或重新提交。**同一报告目录不要混用 1.4 与 1.5 的命令行工具读写**：1.4 的命令行工具读 1.5 的记录会静默误判，1.5 读 1.4 的记录直接拒绝。云端后台读到不能执行的提交记录（结构版本与后端不一致、记录不完整、没有记 worker 镜像版本）时不执行、把 run 置为 `error`，原因写进运行状态：`status` 在状态行下多一行 `message`，`status --json` 多一个 `message` 键；正常收尾的 run 没有这一行与这个键。本机 `status` / `explain` / `status --wait` 接力读到不完整的提交记录以退出码 2 结束并说明。在云端推进后台 run 的 Lambda 函数不再读取 SSM 参数，部署时不再授予它们 SSM 读权限（已有部署重新 `gherkai deploy` 后生效）。
- 命令行工具发给引擎 worker 的 job 带格式版本（与 worker 能力自述的格式版本是同一个号，本版本为 2），worker 在建立任何会话之前核对它：版本不一致时这个 job 记 `error`、类别 `precheck_failed`，消息提示把两者装成同一版本。
- 带设备目标或使用 `--expose-local` 的 run 提交到没有版本戳的旧后端（1.4.0 之前部署、此后没有重新部署过）时以退出码 2 结束、提示先执行 `gherkai deploy` 升级部署；不使用 `--expose-local` 的桌面 run 维持只警告。
- `gherkai destroy` 保留部署建立的 Device Farm 项目，连同其中的远程访问会话记录与录像；记着项目 ARN 的后端参数随 stack 删除，同一前缀重新部署会按名称找回并沿用这个项目。不再需要时按[云端后端](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md)「拆除与清理」一节手动删除。
- 产物桶多一条按标签过期的规则：带 `gherkai=app` 标签的安装包对象 14 天后过期，不带这个标签的对象不受影响；已有部署重新运行 `gherkai deploy` 后生效。
- `.feature` 可以用 `@device:android` / `@device:ios` 与 `@app:<别名>` 声明 scope 的测试目标（声明、继承、冲突的规则与 `@engine` 相同）。设备目标只有 Midscene 支持（见上方「新增」里真机执行一条）：落到 Nova Act 的设备 scope 在 `plan` 与执行前预检中被拒绝并给出改法，不会建立任何会话。设备怎么指定、`@app` 的别名怎么绑定安装包见上方「新增」里「设备 scope 用哪台设备」与「项目配置文件」两条。
- `--default-job-timeout` 不给时按测试目标取缺省：桌面 scope 仍是 300 秒，设备 scope 为获取预算加 900 秒且不接受「不超时」（给 `<=0` 只让桌面 scope 不超时；给正值时设备 scope 不得低于获取预算加 180 秒，标在设备 scope 上的 `@timeout:<秒>` 同受这个下限约束，低于时在开始执行前以退出码 2 结束）；给 `nan` / `inf` 以退出码 2 结束。
- Midscene worker 的 SDK 从 `@midscene/web` 1.12.8 升到 1.15.1（Playwright 仍为 1.63.0）。对使用者的可见变化只有 Midscene 自己的报告页样式随新版改变；模型请求形态、证据与 `explain` 输出不变。
- **导航步的写法改为「`Given` / `When` 之后整句只是一个地址」**，加不加双引号都一样（`Given "https://example.com/"` 与 `Given https://example.com/` 都算）。此前「双引号内以 http(s) 开头就导航」的判法不再使用：`Given 打开 "https://…"` 这类句子里带地址的 step 不再导航，整句交给 AI 执行；升级后请把导航步改成整句地址。网页目标（桌面网页与设备上的浏览器）只接受 `http://` / `https://` 地址：整句是别的协议的地址时这一步记 `error`、不交给 AI。任何目标上，地址两侧的双引号不配对（只有一侧有）时不论地址末尾是不是标点同样记 `error`。此前这两种写法都交给 AI。导航现在是确定性 step 注册表里的一条，`gherkai plan` 对它的标注、`gherkai list-deterministic` 的清单与其它确定性 step 一致（Midscene 的说明比 Nova Act 多一句应用目标上经 DeepLink 的做法）。
- **引擎不再内建 `页面地址匹配 "<正则>"` 这条确定性 step**。要精确核对地址，把仓库 `features/steps/` 里的模板复制进项目的 `steps/`（两个引擎各一份）；用到它而没有带上这条 step 的现有用例，升级后这一步改由 AI 判定，`gherkai plan` 里这一步不再带确定性标注。
- 确定性 step 可以声明接受的关键字（`keywords`），内建导航只接受 `Given` / `When`：`Then` 后只写一个地址的 step 记 `error`、不交给 AI。`plan` 的文本视图用 ⚠ 标出这类 step，`--json` 的 `deterministic` 多一态 `keyword_mismatch`；`list-deterministic` 多一列「关键字」，`--json` 每项多 `keywords`。
- 确定性 step 带 DataTable / DocString 时这一步记 `error`；此前多行参数被静默忽略。
- **job 的最终判定由本机 `run` 与后台 `submit` 共用同一份规则**。对现有桌面用例的可见变化：worker 被强制结束（负退出码，如被系统 kill -9）此前按正常退出处理、现在按非正常退出处理（记 `error`；已被超时或 fail-fast 中止处置的 job 仍按那个处置记）；worker 正常退出却一条 scenario 判定都没报的 job 由 `passed` 改为 `error`（原因写「worker 未报告任何 scenario 判定」）；后台 `submit` 里 worker 崩溃或非零退出的 job 此前没有错误类别、现在记 `engine_error`，以网络故障退出码退出的记 `network_error`（与本机 `run` 一致）；超时与 fail-fast 中止同时成立的 job 按作出停止决定那一刻的事实归因（那一刻已超时记 `timeout`，否则记中止），此前本机 `run` 内部不同分支的判定顺序不一致；两条路径上超时的消息统一为「job 超时（预算 Ns，已中止）」；判定记录里的 `session_id` 以 worker 开始执行时报的会话为准，收尾时报的不再覆盖它。
- worker 已报完全部结果并最终正常退出、只是收尾超出了预算的 job，判定按已报出的结果给出、不记超时；本机 `run` 在这种情形下只向 worker 发出停止请求、等它结束收尾。收尾里非正常退出或一直不退出的仍记超时。
- 前台 `run` 在决定停止一个 job 之后继续读完 worker 的收尾事件，worker 在收尾里报出的事实（如会话已确认停止）不再丢失。worker 收尾完即结束等待，等待的上限按后端取：本机后端为停止宽限再加 5 秒；云端后端（`run --backend cloud`）为部署侧的容器停止宽限（`gherkai deploy --stop-timeout`，缺省 120 秒）再加 25 秒，这 25 秒包含 ECS 记下任务已停止所需的十几秒。
- 两个引擎的桌面 worker 都报出云端浏览器会话的建立与停止：`run --json` 与 `explain --json` 的 job 带 `sessions[]`，每个 AgentCore 浏览器会话一项（`session_id` 与 `name` 都是会话 id；结果未知的创建尝试也占一项，`origin` 为 `attempted`、`session_id` 为 `null`、`name` 为请求携带的会话名；`observed_s`、`provider_minutes` 与 `device` 恒为 `null`），没有会话记录的桌面 job 仍省略这个键。浏览器会话没能确认停止时——停止失败或超时，或者收到停止信号时建立会话的请求还没有返回——job 记 `error`、归因 `release_failed`、worker 以 1 退出，说明里列出会话名并提示到 Amazon Bedrock AgentCore 控制台核对；已报出的 scenario 结果照常保留。建立浏览器会话的请求带上按运行与 scope 生成的会话名（形如 `gherkai:<运行编号>:…`），结果未知的创建尝试在说明里以这个名字列出。
- **本机后端上 Midscene 的最小停止宽限由 31 秒变为 63.5 秒**（worker 按它的收尾超时算出）：只用 Midscene 的 run 不给 `--grace` 时，默认宽限随之变为 63.5 秒；显式给的 `--grace`（或 `gherkai.toml` 的 `grace`）小于 63.5 秒、且用到 Midscene 的 run 在开始执行前以退出码 2 结束，升级后请调大或删掉这个值。宽限只是中止时等待 worker 收尾的上限，worker 收尾完即退出，正常结束的 run 耗时不变。
- Midscene worker 的 npm 包新增五项运行时依赖：`@midscene/core` 1.15.1（与 `@midscene/web` 同版本、精确锁定）、`@aws-sdk/client-device-farm`、`@aws-sdk/s3-request-presigner`（为应用目标的安装包生成下载地址，与 `@aws-sdk/client-s3` 同属 AWS SDK，按版本范围安装）、`webdriverio` 10.0.2 与它的日志模块 `@wdio/logger` 10.0.0（两者同步精确锁定）。WebdriverIO、Device Farm SDK 与 `@aws-sdk/s3-request-presigner` 只在设备目标上加载，桌面 run 与能力自述不加载它们。Nova Act worker 把 `bedrock-agentcore` 列为直接依赖并精确锁定 1.22.0（此前经 `nova-act` 以范围版本间接安装），worker 用它自己启动与停止浏览器会话。
- agent skill 的云端参考：分工表恢复为 worker 镜像的推送与注册归部署方，一人兼任两个角色时可自己推送。
- agent skill 覆盖设备目标：`references/engines.md` 新增设备目标一节（`@device` / `@app` 的声明、设备选择与配置、费用、写法差异、证据字段与错误类别）；写用例规则里的导航步改为整句地址，导航后的落点核对按目标分写（桌面用确定性 step；Android 网页需要精确核对地址时用确定性 step，否则与 iOS 网页、应用目标一样用 AI 断言），地址核对改用仓库 `features/steps/` 的模板、不再引用内建 step。
- 本机后端的引擎 worker 在另一个进程组里运行，并自行监视命令进程是否还在：命令进程被强制结束（如 `kill -9`）后，worker 在几秒内察觉、释放会话并退出，不再留下继续计费的会话；云端 worker 不做这项检测。
- 两个桌面引擎建立 AgentCore 浏览器会话时，按 job 的墙钟预算加 120 秒设定会话的服务端存活上限（限定在 60 到 28800 秒之间，预算为「不超时」时保持服务默认的 1 小时）：worker 被强制结束而没来得及释放时，会话最晚到这个时限由服务端回收。
- 设备 scope 在获取设备期间会话丢失与墙钟预算到期同时成立时，判定记会话丢失这个更具体的原因，而不是获取超时。
- `explain --json` 的 `aborted_hint` 改为只在没能从事件流补取被中止 job 的记录时出现，并写明原因（没有事件流记录、events 表读不到或缺权限）；此前它在判定明细只有部分记录时就出现。
- `status --wait` 只对 `submit` 提交的 run 接力推进：对正在前台 `run` 的 run，它只等待那次运行结束再给判定并提示一句，不再接着推进（此前会与前台运行同时推进同一个 run）；云端后端同样不再对这样的 run 调起后台推进。等待或接力期间按 Ctrl-C 以退出码 130 停止并说明一句，不再打印异常栈。
- `gherkai status` 与 `gherkai list-runs` 里，只要有一个 job 不再是 `pending`（已被安排执行、正在执行或已有结果，包括被跳过），run 就显示为 `running`，到结束之前不再回到 `pending`：前台 `run` 正在执行的 run 此前在整个执行期间都显示 `pending`；`submit` 提交的 run 此前在 job 已不是 `pending`、worker 还没报出第一个事件的这段时间里也显示 `pending`，偶尔还会在显示 `running` 之后变回 `pending`。`list-runs --status running` 随之列出这些 run，`--status pending` 只列出全部 job 都还是 `pending` 的 run；`status --json` 与 `list-runs --json` 的 `status` 同样如此。
- 库层包 `gherkai-runtime`：`compose.build_engines` 新增必给的关键字参数 `run_id`，不传时调用即报 `TypeError`，传空值报 `ValueError`；传入的须与交给 `schedule` 的 `RunMeta.run_id` 是同一个值。本机 worker 用它给云端浏览器会话与远程访问会话命名，没有它会在建立会话之前以 1 退出。
- `submit --backend cloud --expose-local` 的隧道存活时间上限（`--tunnel-ttl`）默认值改为各 job 墙钟预算之和，加一次性的 900 秒，再加每个 job 210 秒；此前只加固定的 900 秒，并发为 1 且多个 job 用尽预算时，隧道可能在 run 结束前被拆除，剩下的 scenario 以导航失败告终。`submit` 打印的秒数随之变大，并注明这是按任务量估算的上限、不是保证；显式给出的 `--tunnel-ttl`（或 `gherkai.toml` 的 `tunnel-ttl`）不受影响。说明见[本机应用测试](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/local-app-testing.md)「存活时间上限」一节。
- `gherkai doctor` 把「未查」单列为一种结果：结果列多一种标记 `·`，表示这一行这次没有检查，原因写在说明列；有这样的行时，表格下方的结论行点明 `·` 的含义。此前未查的行按来由标 `✓` 或 `-`，看不出那一部分其实没有检查。未查的行有：未给云端参数时的 `aws.identity` 与 `backend.reachability`；region 或凭证先失败时的 `backend.reachability`；没有可比对的引擎时的 `backend.worker.grace`（没有解析到镜像的引擎，或解析到的引擎本机一个对应的 worker 都没有）；没装部署 extra、装了多个部署 provider 而未指名、或装上的 provider 不提供自检时 provider 段的那一行。`--json` 每项新增布尔键 `skipped`，为 true 时 `ok` 恒为 true、`required` 恒为 false。region 或凭证先失败时，`backend.reachability` 的 `ok` 由 false 改为 true（同时 `skipped` 为 true），只读单行 `ok` 来判断「查过且通过」的脚本要同时看 `skipped`；按「必修且未通过」挑阻塞项、或看顶层 `ok` 与退出码的不受影响，退出码规则不变。说明见[排错](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/troubleshooting.md)「先运行 gherkai doctor」一节。

### 修复

- `--expose-local` 的取值末尾带 `/`（如 `http://localhost:3000/`）时，feature 里以这个地址开头的 URL（如 `http://localhost:3000/login`）此前不能正确替换成隧道地址，scenario 以导航失败告终；现在末尾的一个 `/` 按不带斜杠处理。取值带路径、查询串、片段或用户信息，或者不以 `http://` / `https://` 开头时，`plan`、`run`、`submit` 改为以退出码 2 结束并给出正确写法（只写到端口为止），`run` 与 `submit` 不再起隧道。
- 运行中写入 job 状态失败时（如云端后端的运行状态表中途不可达），这个 job 此前被记成 `engine_error`、消息为「worker 异常：…」，run 照常继续；现在不给这个 job 记判定，而是停止这个 run 中仍在运行的 job 并原样报出这个错误，与写入 job 判定失败时的处理相同（云端后端以退出码 1 结束，提示运行期落库失败）。
- 云端后端的前台 `run`（`run --backend cloud`）里 worker 的任务没能启动（如拉不到镜像、缺少 secret）时，job 的判定消息给出退出码 255 与 ECS 报出的停止原因（如「TaskFailedToStart: CannotPullContainerError: …」），与 `submit` 下同一故障的判定一致；此前记为退出码 1 并提示查看 worker 日志，而容器没有启动时并没有 worker 日志。这种情形下判定也不再多等几秒。任务已停止却始终没有给出退出码的其他情形同样记为 255 并附上原因。
- Midscene worker 收到停止信号之后不再开始新的 step 与 scenario；此前在会话停止之前的几秒里，它仍会为下一个 step 调用模型、产生费用。停止期间除收尾本身的报告上传与排队中文件的上传之外，不再发起别的上传（step 与 scope 结束时的报告上传、诊断日志与 step 证据的上传、整目录上传剩余产物），也不再删除本地的运行目录；此前运行目录可能先被删除，收尾时的报告上传随之失败。worker 的退出码以停止收尾的结果为准。

### 升级须知

- 命令行工具、两个引擎 worker 与云端后端升到同一版本；同一报告目录不要混用 1.4 与 1.5 的命令行工具读写。
- 命令行工具与引擎 worker 之间的格式版本由 1 升为 2，1.5 的 worker 不再接受旧版命令行工具发来的确定性 step 查询。1.4 的命令行工具配 1.5 的 worker 时，`list-deterministic` 与本机后端的 `run`、`submit` 在读取 worker 能力自述这一步以退出码 2 结束（提示能力自述格式版本是 2、命令行工具认的是 1）；`plan` 同样以退出码 2 结束，转述 worker 的「命令行工具与 worker 的版本不一致，请把两者装成同一版本」（1.4 的命令行工具把这条消息冠以「使用方 steps 加载失败」，实际成因是版本不一致）。处置都是把两者装成同一版本。
- 反过来，1.5 的命令行工具配 1.4 的 worker 时，`list-deterministic`、本机后端的 `run`、`submit` 与 `plan` 都在读取 worker 能力自述这一步以退出码 2 结束，提示「引擎 … 的能力自述格式版本是 1，这个命令行工具认的是 2：命令行工具与 worker 的版本不一致，请把两者装成同一版本。」；1.4.3 之前的 worker 没有能力自述入口，这些命令同样以退出码 2 结束并转述 worker 自己的报错。`plan` 现在只在取不到 worker 的结果时（没装、起不来、超时、输出不是合法 JSON）降级为警告并继续；worker 自述不兼容（含版本不一致）与 `NOVA_ACT_TIMEOUT_S` 取值不合法改为以退出码 2 结束，不再降级。
- 把 `Given 打开 "https://…"` 这类导航步改成整句只写地址；用到 `页面地址匹配` 的项目把仓库 `features/steps/` 的模板复制进 `steps/`。
- 只用 Midscene 的本机 run 若显式给了小于 63.5 秒的 `--grace`（或 `gherkai.toml` 的 `grace`），调大或删掉它。
- 直接调用 `gherkai_runtime.compose.build_engines` 的程序传入 `run_id`，取与 `RunMeta.run_id` 相同的值（可用 `compose.new_run_id()` 生成）。
- 部署方重新执行 `gherkai deploy`：启用设备支持（建立 Device Farm 项目与 worker 授权；部署方的凭证要有 us-west-2 上的 `devicefarm:ListProjects`、`GetProject` 与 `CreateProject`，否则这套后端不启用设备支持）、加上安装包的过期规则、撤掉在云端推进后台 run 的 Lambda 函数的 SSM 读权限、给运行记录表加上 `list-runs` 用的清单索引。有自定义 worker 镜像 variant 的，从新版本基础镜像重新构建后用 `gherkai deploy push-worker` 推送一次，升级步骤见[云端后端](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md)「版本与升级」。
- 清单索引由 AWS 在部署后为表里已有的 run 补齐，`gherkai deploy` 不等补齐就结束：这段时间里 `list-runs --backend cloud` 以退出码 2 结束并提示索引还在建立，稍后重试，其它命令不受影响。补齐之前这张表不能再被更新，这期间再次部署要改运行记录表时会失败；建索引期间部署失败、stack 回滚时，已经开始建立的索引不会随回滚删除，须手动删掉再部署。命令与说明见[云端后端](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md)「版本与升级」。要用 `list-runs` 的团队成员，凭证补上运行记录表索引上的 `dynamodb:Query` 与表上的 `dynamodb:BatchGetItem`。

## [1.4.9] - 2026-10-12

### 变化

- agent skill 正文压缩约 7%，只删与参考文件重复的细则、不删规则：机读字段的读法以契约参考页为准，隧道的前置与排障细节只在环境与排障参考里保留一份，模式怎么写窄见确定性 step 参考；云端参考的分工表改正 `push-worker` 的归属，测试开发可以自己推送、不必交部署方。

### 新增

- agent skill 与用户指南的写用例规则补一条：导航步之后紧跟一条确定性落点核对（页面上有某按钮、标题包含，或内建的 `页面地址匹配`）。应用没有启动、启动的不是它或地址写错时，这一步在一秒内判否并写出页面内容，后面的 AI 步不再各花几秒与数千 token 去尝试。评测的两条写 feature 用例加了对应断言。

## [1.4.8] - 2026-09-30

### 变化

- 本机 `run` 里 worker 日志行前缀的颜色改为按 job 启动顺序分配，同一次运行内最多 8 个 scope 互不重色、同一 plan 下颜色稳定；调色板去掉红与绿，避免与判定汇总里的失败红、通过绿混读。颜色只用来区分来源 scope，不表示 out / err 或严重程度。`NO_COLOR` 现在也关闭这些前缀的颜色。
- 云端前置检查的提示改为书面表述：版本不一致、后端没有版本戳、跳过版本比对、worker 镜像 variant 解析失败这几条先说发生了什么，再说原因与处理方式；判据、退出码与命令都没有变化。

## [1.4.7] - 2026-09-30

### 变化

- 人读输出统一由 rich 渲染：多行同结构的清单改为带框线的表格（`deploy list-workers`、`list-engines`、`list-deterministic`、`status` 的 job 清单、`doctor`），层级结构改为带引导线的树（`run` 的判定汇总、`plan`、`explain`），判定与状态词按语义上色（通过绿、失败红、出错紫红、中止亮红、跳过淡显），标准输出不是终端或 `NO_COLOR` 为非空值时不带颜色，`FORCE_COLOR` 可强制带颜色；表格里的标识列（scope_id、示例、模式、tag、地址）不折断，说明类列只在终端过窄时折行，非终端输出每行保持一行。`list-workers` 的推送时间换算到 UTC、精确到分钟，默认 variant 以 `*` 标出。`--json` 的机读形态不变。命令行的依赖新增 `rich`。

## [1.4.6] - 2026-09-29

### 变化

- 隧道模式（`--expose-local`）下，gherkai 自己产出的文字不再带隧道凭据：确定性 step 的失败消息、AI 证据的 JSON、`explain` 输出、`run --json`、本机转发的 worker 日志里，地址中的凭据段显示为 `***`。落盘的运行定义（`run_meta.json`）与引擎的原生产物仍是明文，运行要读回前者、后者由引擎自己写。

## [1.4.5] - 2026-09-29

### 新增

- agent skill 写用例的规则补两条：期望值只来自需求，看被测应用只为定位元素与实现动作；写新的确定性 step 前先看两个引擎的清单，已有的复用、同义模式不重复注册。
- agent skill 的环境与排障参考把隧道模式（`--expose-local`）从「两条前置」扩成完整一节：选项值与 feature 书写逐字一致（前缀字符串匹配）、一个 run 只暴露一个地址、开发服务器要放行隧道域名、隧道的持有与拆除、排障入口与安全提醒，并给出用 `plan` 回显逐字对照的核对方法。
- agent skill 写用例的规则再补两条：需求给不出某条期望要的值、范围或清单时不猜、不从应用里补（应用里的取值不进用例、不进单测数据、也不当参照列进汇报），先做完不依赖缺口的部分再问人，非交互时把缺口单列进汇报；AI 动作步只描述这一步的动作、不写成目标（写「点击第 1 组」不写「选择第 1 组」，写成目标模型会做到底、越过这一步继续操作）。评测新增三条（需求缺规格、瞬态窗口本机过云端否、复用已有 step）与两套 fixture。
- agent skill 新增一份给测试开发的参考 `references/deterministic-steps.md`：确定性 step 该不该写（含成本与速度判据）、等待与判定（含瞬态窗口内的多个动作合成一次页面内调用）、失败消息带现场、判定逻辑与注册分离、本地用真浏览器单测、改一条在用的 step、症状速查。用户指南「编写确定性 step」同步补这几节与两侧完整示例。

### 变化

- `run` / `submit` 的 `--max-concurrency` 默认值从 1 改为 4，与设计一致：并发只改同时开几个浏览器会话，不改 job 数与总费用；20 个 job 的一次运行实测从约 29 分钟缩到约 7 分钟。云端 `submit` 仍受部署侧上限钳制，配额紧时手动调低。
- 云端后端 stack 的部署侧单 run 并发上限从 8 提到 20：提交侧默认仍是 4，上限只在提交者明确要更高并发时起作用；重新部署后生效。
- 用户指南与 skill 里 Midscene 侧的最小模板改为带等待的判定（此前示例直接读 `isVisible()` 的瞬时值，是确定性 step 假失败的常见来源）。

### 修复

- Midscene worker 给页面预置 `__name` 的恒等实现：使用方 `.mts` 里传给 `page.evaluate` / `waitForFunction` 的函数经加载器改写后在页面里引用 `__name` 而报 ReferenceError，本机单测不暴露、云端一运行全部记 error；现在 context 级初始化脚本与当前文档都补上这个定义。

## [1.4.4] - 2026-09-20

### 变化

- Midscene 引擎的默认模型改为 `us.openai.gpt-5.6-terra`（OpenAI GPT-5.6 Terra，经 Amazon Bedrock 调用）。在同一批用例上重复运行，它的判定稳定不抖动，并且比原默认模型 `qwen.qwen3-vl-235b-a22b` 快约三成、少用约四分之一 token；调用请求已按 Bedrock 对 GPT 系模型的要求调整。费用相应上升：一条 5 步左右的 scenario 约 5 美分，原默认模型约 2 美分（以你账户的 AWS 账单为准），量级与口径见[运行测试与查看结果](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md)。该模型经 Bedrock 跨区推理调用，Midscene 的 AI step 模型调用在美国境内三个 region（us-east-1 / us-east-2 / us-west-2）处理；浏览器会话与产物仍在你选的 region，Nova Act 引擎不变。
- Nova Act 引擎的默认模型改为固定的 `nova-act-v1.0`，不再使用跟随最新 GA 版本的别名。同一条断言在不同模型版本上可能翻转，固定版本让结果可复现；换模型只随 gherkai 发版，并在本文件里点明。
- 两个引擎的模型都可用环境变量覆盖：Nova Act 侧 `NOVA_MODEL_ID`；Midscene 侧 `MIDSCENE_MODEL_ID`，模型家族一般由模型 id 自动识别，识别不出时 worker 启动即报错并要求补 `MIDSCENE_MODEL_FAMILY`。本机 local 后端在 shell 里设置即生效；云端 cloud 后端把变量写进定制 worker 镜像。
- `gherkai doctor` 新增一行，显示本机各引擎 worker 实际会用的模型（`--json` 里是 `engines` 段的 `model.<engine>`），在 shell 里设过覆盖变量的机器可以直接核对；云端 worker 的模型写在定制镜像里，不在这一行显示。
- 云端 worker 现在可以调用 Bedrock 上的模型与你账户里的跨区推理入口，不再限定单一模型：换模型只需改定制 worker 镜像里的环境变量，不必重新部署后端。
- 两个引擎的第三方依赖改为固定精确版本：Midscene 侧 `@midscene/web` 升到 1.12.8、Playwright 1.63.0，Nova Act 侧 `nova-act` 3.4.187.0。此前声明的是版本范围，不同时间安装的机器会取到不同版本。
- Midscene 引擎的 token 用量改用引擎 SDK 公开的累计计数，元素定位时的区域搜索调用也计入。同一条用例的报告用量会比此前略高，是统计范围更全，不是模型消耗变多。
- `gherkai deploy` 结束时改为逐行说明默认 worker 镜像 variant 与 worker 运行配置的更新结果，例如「已保留默认 worker 镜像 variant `base`」「各 variant 的 worker 运行配置已是最新」。
- 仓库首页新增「判定由谁做出」一节，列出两个引擎各自使用的模型与服务、版本策略、查看与更换方式，以及费用来源。
- 文档重组：面向使用者的完整说明集中到 [`docs/user-guide/`](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/README.md)，新增[常见问题](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/faq.md)页；文档里的图改为统一风格的架构 / 流程 / 时序图，执行与推进全景、云端交付与 worker 身份两张大图另有可交互版本（https://zhiyanliu.github.io/gherkai/ ）；各发行包在 PyPI / npm 上的页面改为入口页，只留定位、装法、最小用法与指向用户指南的链接；本文件是新增的变更记录。
- 命令行的帮助、提示、警告、错误与 `gherkai deploy` 的步骤行统一了用词：口语的「跑」改为「运行」或「执行」；`--default-job-timeout` 的帮助改称「job 墙钟预算秒」；`gherkai skill` 各命令的帮助改称「agent skill」；`deploy` 里同步官方 worker 镜像的那一步改称「基础镜像同步」；`plan` 的输出表头改称「用例预检」。用户文档与随包发行的 agent skill 同批对齐了同一套用词：`plan` 一律称「用例预检」，前台与后台之别称「执行方式」、本机与云端之别称「执行后端」，两者的四种组合称「四种组合」；指一次运行时不再称「批」，统一称 `run` 或「本次运行」。`--vpc` 在帮助与用法行里的取值占位符改为 `取值`，`--require-approval` 的帮助改称「审批级别」，`gherkai deploy` 关于 VPC 的提示与报错统一说「VPC 取值」，与用户指南里的选项表用词一致。命令、选项、输出结构与退出码都没有变化。
- `gherkai --help` 不再列出 `_reconcile` 与 `_tunnel_watch`：它们是 `submit` 在后台启动的子进程入口，不供直接使用；此前二者以「==SUPPRESS==」出现在命令列表里。

- 命令行帮助、提示与两个引擎 worker 的日志继续统一措辞：不再用等号、箭头这类符号代替连词，「退 2」一律写成「退出码 2」；`gherkai status` 的几条帮助去掉了内部名词；两个引擎 worker 对同一种产物用同一个名字（「证据截图」）；产物上传失败的日志只说明什么没传成、不再承诺稍后重试；`gherkai deploy delete-worker` 的占位说明改为使用者语言。命令、选项、输出结构与退出码都没有变化。

### 修复

- Midscene 引擎每个 run 在日志里打出的一段 `Execution context was destroyed` 报错栈已消除（关闭了对云端浏览器无意义的一项 SDK 渲染开关）。
- 引擎无法回答能力查询时的提示改为先给出 worker 自己的报错原文，常见成因（版本不一致、模型配置不对）只在原文没有说明原因时补充。
- `gherkai deploy` 及其 `list-workers` / `push-worker` 子命令：给了不存在的 `--profile` 名、或配不出 region 时，现在以退出码 2 结束并说明「连不上 AWS」；此前会打印一段 Python 报错栈。
- 云端后端：一次 run 的 job 超过 100 个时，job 超时处置此前会失败，或把仍在运行的 task 误判为已不存在而直接记为超时；现在按页读取、分批查询。超时处置的兜底检查出错时，也不再影响同一批事件里其它 run 的推进。
- Midscene worker 收到停止信号时若正在释放浏览器会话，此前可能提前退出而漏掉释放、会话继续计费且退出码仍为 0；现在等释放完成再退出。
- `gherkai deploy` 同时给出只读选项（`--diff` / `--synth-only` / `--bootstrap`）与 worker 镜像子命令时的提示改为可执行的建议；此前对 `--bootstrap` 与 `--synth-only` 给出的建议命令无法运行。
- `gherkai run --json` 的帮助此前写「不打进度」，实际进度与诊断仍走标准错误、只有 `--quiet` 静音逐事件进度；帮助已改准，用户指南同步。
- 各 Python 发行包的源码包（sdist）不再包含测试目录，Nova Act worker 的源码包不再包含探针脚本；源码包内容改为显式白名单，不再受本机忽略规则影响。

### 升级须知

- 在本机 local 后端运行用例的机器上，把命令行工具与你的用例用到的引擎 worker 升到同一版本（`uv tool upgrade gherkai`；Midscene worker 另外执行 `npm i -g @gherkai/worker-midscene@<CLI 版本>`），新的默认模型随 worker 一起升级；版本不一致会在运行前检查时以退出码 2 结束。安装形态见[开始使用](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/getting-started.md)。
- 部署方须重新执行 `gherkai deploy`：新的默认模型在新版本的 worker 基础镜像里，放宽后的模型调用权限也随部署更新。有自定义 worker 镜像 variant 的团队，从新版本的基础镜像重新构建后用 `gherkai deploy push-worker` 推送一次。升级步骤见[云端后端](https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md)。
- 想继续用原来的 Midscene 模型：把 `MIDSCENE_MODEL_ID` 设为 `qwen.qwen3-vl-235b-a22b`（本机 local 后端设在 shell 里，云端 cloud 后端写进定制镜像的环境变量）。

## [1.4.3] - 2026-09-16

### 变化

- 停止 worker 的宽限秒数下限改由引擎 worker 自己报告：本机 local 后端不给 `--grace` 就按 run 里用到的各引擎报出的最短宽限取值，通常是分钟量级（只用 Midscene 引擎的 run 更短），给出小于该下限的值直接退 2。宽限过短会让正在进行的 AI 操作被强制杀掉、云端浏览器会话泄漏。
- `--backend cloud` 不再接受显式 `--grace`：云端 worker 的停止宽限由部署侧的 `gherkai deploy --stop-timeout` 决定，给了这个选项直接退 2，且不会产生任何云端调用。
- `gherkai doctor --backend cloud` 新增一行，把引擎 worker 报出的最短宽限与云端任务定义的停止宽限做比对；不足时提示可以调高部署侧的 `--stop-timeout`。
- 在本机运行之前，命令行工具会先向用到的每个引擎 worker 查询一次它的能力与最短宽限。worker 与命令行工具版本不一致时，命令几秒内退 2 并提示升级该引擎的 worker，不再等到超时。
- `gherkai explain --scenario <SEL> --step N` 点名的那一步一律展开证据，通过的 step 也展开，不必再加 `--all`。
- `gherkai deploy` 少给 `--vpc` 时的提示改为直接说明三档各是什么；后端记着上次部署用的档时，提示里直接给出沿用它的写法。

### 升级须知

- 在本机 local 后端运行用例的机器上，命令行工具与你的用例用到的引擎 worker 要升到同一版本；版本不一致会在运行前检查时退 2（没用到的引擎不受影响）。

## [1.4.2] - 2026-09-16

### 新增

- `gherkai explain <run_id>`：读出失败那一步的证据——AI 的推理、当时页面截图的位置、断言票数与页面地址。`--scenario` / `--step` 收窄范围，`--all` 连通过的 step 也展开，`--full` 逐段全文，`--json` 输出机读结构。
- `gherkai doctor`：一条命令自检环境——引擎是否装好、`steps/` 能否加载；加 `--backend cloud --prefix <前缀>` 连带查 AWS 凭证、region 与云端后端。
- `gherkai skill install`：把驾驭 gherkai 的 agent 技能装进项目（或用户级）的 agent 目录，`--agent` 支持 `claude-code` / `codex` / `all`。技能随命令行工具一起发行。
- 筛选与机读选项补齐：`plan` / `run` / `submit` 支持 `--scenario`（按 `<文件>:<行号>`、行号或标题片段选）与 `--scope`（按 scope_id 精确选整个 scope）；查询类命令都有 `--json`；`--quiet` 不打逐事件进度，本机 worker 日志改落 `<report-dir>/<run_id>/worker.log` 并只打一行位置。
- 判定明细与报告里每个 step 带一行原因（`message`）：说明它为什么不是 `passed`，通过的 step 为 null。

### 变化

- AI step 的截图改为运行期后台上传：每步完成即入队上传，不必等 scope 收尾；收尾时最多等待固定时长让剩余上传完成，失败重试一次。run 被中途停止时，已完成的 step 的截图仍会上传到产物桶，但不会进判定明细——`gherkai explain` 会在该 job 上提示这一点。
- `gherkai status` 在 run 到达终态时打出报告与判定明细的位置；建议加 `--wait` 继续等到终态的提示只在所有 job 都尚未开始运行时出现。
- `explain` 的文本输出统一用机读字段名作前缀（`message:` / `thought:` / `screenshot:` / `error:`），与 `--json` 的字段一致。
- `@scope` 的取值与另一个未标 `@scope` 的 scenario 自动生成的 scope_id 相同时，`plan` / `run` / `submit` 直接报错并给出位置，不再让两个 scope 使用同一个 scope_id。
- Nova Act 引擎在你账户里自动创建的 workflow definition 改名为 `gherkai-worker`；无需手动迁移，云端按新名自动建出。

### 移除

- `gherkai submit` 去掉 `--events-table` 与 `--cluster`：这两个资源名一律按 `--prefix` 推导。
- `gherkai destroy` 去掉 `--allow-vpc-change` 与 `--require-approval`：这条命令从不使用它们，此前给了会被静默忽略，现在直接退 2。

### 修复

- 本机 local 后端的判定明细与报告文件改为原子写入，运行期间读取不会读到写了一半的内容。
- `submit` 起了隧道、后台进程还没接管就失败时，隧道会被立即拆掉，不再残留。
- `explain` 在判定明细还没落地时的提示带上各后端定位 run 的选项。
- `gherkai skill install` 读到非 UTF-8 的目标文件时退 2 并说明真正的原因。

## [1.4.1] - 2026-09-10

### 变化

- 失败或超时的 AI step 同样报出它消耗的时间与用量，此前这部分统计整块丢失。
- 后台批量运行的报告带上 run 级总时长。
- 被测界面的语言支持范围写进文档：Midscene 引擎不限语言（中文界面上的操作与 AI 断言与英文同级可靠）；Nova Act 引擎的支持范围是英文界面——它在中文页面上能操作、能判页面级语义，但「正文里是否出现某个中文词」这类断言会稳定判否。非英文应用请用 `@engine:midscene` 路由。
- worker 镜像 variant 解析失败时的提示补上第二条出路：先用 `--worker-variant base` 运行。
- 各发行包在 PyPI / npm 上的说明页改为面向使用者，开发相关内容移到仓库内。

### 修复

- 云端 worker 未能启动时（例如拉不到镜像、缺少密钥），后台 run 会永久停在 `running`。现在会落到 `error` 终态，并在 `message` 里给出容器的停止原因。
- 云端 job 到达超时预算时的处置：正在停止中的任务不再被当作查不到而直接判超时，恰在预算点前运行结束的 job 也不会被误判为超时。
- 云端事件读取不再跳过短暂缺号的记录，判定明细不会因此少 step。
- 后台 run 收尾时先落判定明细再提交终态，run 的判定明细不会缺失。
- `gherkai status` 与后台推进进程并发读写运行状态文件时不再读到不完整内容（改为原子写入）。
- 后台 run 因超时被停止时，按该引擎的最短宽限等待 worker 退出，不再用极短宽限强制终止、导致云端浏览器会话泄漏。
- `gherkai deploy` 同时给出 `--diff` / `--synth-only` / `--bootstrap` 与 `push-worker` 等子命令时退 2，不再静默推送镜像。
- Midscene 引擎在 `--no-report` 下不再把引擎原生产物上传到 S3。
- `.feature` 路径指向目录、无读取权限或编码不对时退 2 并说明原因，不再打印调用栈。
- `--grace` 拒绝 `nan` / `inf` 这类取值（它们会让强制停止永不触发）。
- `@scope` 的名字里含 `#` 时，云端后台推进不再取错 run_id。
- 报告页与文本输出里，`skipped` / `aborted` 的原因会照原样显示。

## [1.4.0] - 2026-09-08

首个以发行包形式发布的版本；此前只能从仓库 checkout 运行。

### 新增

- 发行包：命令行工具 `gherkai`（PyPI）、本机 Nova Act worker `gherkai-worker-novaact`（随 `gherkai[local]` 装）、本机 Midscene worker `@gherkai/worker-midscene`（npm）、云端部署 provider `gherkai-deploy-aws`（随 `gherkai[deploy-aws]` 装）、库层 `gherkai-core` 与 `gherkai-runtime`；worker 基础镜像发布到 `ghcr.io/zhiyanliu/gherkai-worker-novaact` 与 `ghcr.io/zhiyanliu/gherkai-worker-midscene`。各包同号发布，`gherkai --version` 查看版本。
- `gherkai deploy` / `gherkai destroy`：一条命令建起或拆掉云端后端（运行状态表、产物桶、cluster、任务定义、Lambda 函数、VPC）。`--vpc` 三档（`default` / `new` / `vpc-<id>`）必给；`--diff` 只看变更集、`--synth-only` 只导出模板、`--bootstrap` 只做账户初始化；`--stop-timeout` 设 worker 容器的停止宽限。非交互场景用 `gherkai destroy --yes`。
- `gherkai deploy push-worker` / `list-workers`：把一套 `steps/` 构建成定制 worker 镜像、推成一个具名 variant，并查看各引擎当前的 variant、镜像 digest 与默认指针；提交时用 `--worker-variant` 选。
- 使用方自己的确定性 step 目录（`--steps-dir`，默认 `./steps` 存在即用）：本机 local 后端直接加载，云端 cloud 后端把它构建进定制 worker 镜像。
- 云端后台批量运行支持并发：`--max-concurrency` 在 cloud 后端同样生效，后端另有每个 run 最多 8 个 worker 的上限。

### 变化

- `--no-report` 改为真的不生成产物：不再注入报告落点，worker 也不生成、不上报产物。
- 命令行帮助、提示、警告、错误与 worker 日志改为直接说明发生了什么、怎么办，不再出现只有维护者能看懂的内部名称。

### 修复

- Nova Act worker 收到停止信号时可能因日志写入重入而崩溃，现已修正。

## [1.3.0] - 2026-08-17

发行重组之前的版本，没有独立发行包：只能从仓库 checkout 运行。
