# 环境就位与排障

本文管「装、查、卡住了怎么办」。每条命令的全部选项以 `gherkai <命令> --help` 为准；报错都带「怎么办」，先照它说的做。

## 1 装什么

| 角色 | 装法 | 得到 |
|---|---|---|
| 只提交云端 run（不在本机运行） | `uv tool install gherkai` | 只要 CLI 本体，两个 worker 都不用装（worker 运行在云端）；代价是 `plan` 会打「标注降级」 |
| 本机运行 Nova Act（推荐起点） | `uv tool install 'gherkai[local]'` | CLI 与 Nova worker 在同一环境 |
| 本机运行 Midscene | `uv tool install gherkai` + `npm i -g @gherkai/worker-midscene`（Node ≥ 22） | CLI + Midscene worker |
| 本机运行两个引擎 | `uv tool install 'gherkai[local]'` + `npm i -g @gherkai/worker-midscene`（Node ≥ 22） | CLI + 两个 worker |
| 部署方 | `uv tool install 'gherkai[deploy-aws]'`（另需 Node ≥ 22、docker） | 多出 `gherkai deploy` / `gherkai destroy` |

升级：`uv tool upgrade gherkai`（安装时带的 extras 沿用）；Midscene worker 另 `npm i -g @gherkai/worker-midscene@<CLI 版本>`。worker 与 CLI 版本同号锁定。

## 2 CLI 怎么找 worker

- **Nova Act**：① 环境变量 `GHERKAI_WORKER_NOVAACT_CMD`（+ 可选 `GHERKAI_WORKER_NOVAACT_CWD`）显式指定；② 与 CLI 同一个 Python 环境；③ PATH 上的 `gherkai-worker-novaact`；④ 三级都没有、CLI 是正式发行版、机器上有 uvx 时临时拉起同版本 worker。四级都没命中：local 后端的 `run` / `submit` 与 `list-deterministic` 以退出码 2 结束并打印装法（`submit` 也在提交前就拒）；`--backend cloud` 的 `run` / `submit` 不看本机 worker（它运行在云端容器里）；`plan` 不拦，只少了那个引擎的派发标注。
- **Midscene**：PATH 上的 `gherkai-worker-midscene`（`npm i -g` 的结果），或环境变量 `GHERKAI_WORKER_MIDSCENE_CMD`（+ 可选 `GHERKAI_WORKER_MIDSCENE_CWD`）显式覆写。**必须实际安装**，没有临时拉起的兜底。

`gherkai list-engines` 打出每个引擎的探测结果与来源，缺的那个原地给安装命令；`--json` 机读（`engine` / `available` / `cmd` / `cwd` / `source` / `hint`）。

## 3 `gherkai doctor` 怎么读

只读自检，不建会话、不调模型、不花钱。输出是一张表，每项一行（终端过窄时说明列在格内折行；要机读用 `--json`），第一列是结果：`✓` 过（「未查」的项也算过）、`✗` 必修项没过、`-` 可选能力缺失（如另一个引擎没装）。检查项按段分组：

| 段 | 查什么 | 何时查 |
|---|---|---|
| `cli.*` | CLI 版本与 Python | 总是 |
| `config.*` | 本次加载的项目配置文件；没有使用时列出查找顺序 | 总是 |
| `engines.*` | 每个引擎的 worker 能否定位、至少一个可用、本机 worker 各自自报的模型与支持的测试目标 | 总是 |
| `steps.*` | steps 目录是否存在、每个引擎加载 steps 是否成功、几条 | 总是（`--steps-dir` 可改目录） |
| `aws.*` | region、凭证身份 | 给了 `--backend cloud` 或 `--prefix` |
| `backend.*` | 后端版本与 CLI 比对、资源齐全、报告前缀一致、默认 variant 与逐引擎镜像能否解析、本机 worker 自报的收尾宽限与云端为它设的停止宽限的对比、设备支持是否已部署（`devices.project`）与项目里未结束的远程访问会话（`devices.sessions`，有残留时逐条给控制台链接与停止命令，停止前须确认没有 run 在使用它）。宽限比对与设备两行（`worker.grace`、`devices.project`、`devices.sessions`）没过时只标 `-`、不影响退出码 | 同上 |
| `provider.*` | Node、cdk、容器引擎（部署方工具链） | 装了部署 extra 时 |

退出码：全部通过为 0；有**必修项**失败为 2（非必修项失败只标出不影响退出码）。`--json` 每项给 `section` / `name` / `ok` / `required` / `detail`，脚本按 `required && !ok` 找阻塞项。

## 4 凭证与 region

- 走本机 AWS 默认凭证链：profile / 环境变量 / 实例角色皆可，`--profile` 或 `AWS_PROFILE` 选 profile。**不需要任何 API key**。
- **region 必须有出处**，按序解析：`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > `gherkai.toml` 里 `[common]` 的 `region` > `--profile`（或 `AWS_PROFILE`、或配置文件 `[common]` 里设的 profile）指的那个 profile 配置里的 region。五处都没有才报错；缺失时不会改用任何默认 region。
- 该 region 下账号要能用这些服务：Nova Act 引擎需要 Nova Act 服务与模型 nova-act-v1.0（默认锁定；环境变量 NOVA_MODEL_ID 可换，`doctor` 会显示实际模型）；Midscene 引擎需要 Bedrock 模型 us.openai.gpt-5.6-terra（默认；环境变量 MIDSCENE_MODEL_ID 可换，`doctor` 会显示实际模型）；两者都要 AgentCore Browser。`AccessDenied` / 模型不可用多半是 region 未开通模型或凭证缺这些权限。
- 本机 `run` / `submit` 也要 AWS 凭证（浏览器与模型在云端）；只有 `plan` / `list-engines` / `list-deterministic` / `doctor`（不带 cloud 参数）纯本地。

## 5 隧道（`--expose-local`）：前置、写法、排障

**前置两样**，缺哪样都是 `run` / `submit --expose-local` 在起隧道时以退出码 2 结束，且 `doctor` 两样都不查（它不碰隧道）：

- **ngrok 可执行文件**装好且在 PATH 上（`ngrok version` 能正常执行；下载 https://ngrok.com/download ）。没装的报错点名找不到 ngrok 可执行文件。
- **ngrok 账号的 authtoken**（免费账号即够）：`ngrok config add-authtoken <token>` 写进 ngrok 自己的配置文件，或环境变量 `NGROK_AUTHTOKEN`，任一处即可。排障别只看环境变量在不在——配置文件里配过就够。取值在 ngrok 控制台的 **Your Authtoken** 页；**API Keys** 页的值起不了隧道，两者都是长随机串、肉眼分不出，填错的表现是「隧道未就绪」、报错附带的 ngrok 日志会点明鉴权原因。

**写法三条**，都是导航失败的常见来源：

- **选项值与 feature 里书写的地址逐字一致**。`http://localhost:3000` 与 `http://127.0.0.1:3000` 互不匹配，大小写、端口都要一样；只替换「作为一个地址出现」的选项值（后面是路径、查询串、句末标点或正好结束），`http://localhost:30000`、`http://localhost:3000.evil/` 不会被改坏；没匹配上就不替换，云端浏览器照着原地址导航、第一步就失败，而被测应用的日志里一条请求都不会有。
- **核对方法，改完给人一并写出来**：

  ```bash
  gherkai plan features/<x>.feature --expose-local http://127.0.0.1:3000   # 「注：」行回显你给的值；把它与打印出的 step 文本逐字对照
  ```

  `plan` 不检查 feature 里有没有这个地址，地址不匹配它照样以退出码 0 结束，所以对照只能靠眼睛：大小写、端口、localhost 与 127.0.0.1 都要一致。
- **一个 run 只能暴露一个地址**：重复给 `--expose-local` 不报错，只有最后一个生效，前面的地址不被替换。多个本机地址先收敛到同一个入口。
- **被测应用收到的 Host 头是隧道分配的 ngrok 域名**，不是 localhost。校验 Host 的开发服务器会在框架层拒绝：Vite 的 `server.allowedHosts`、Django 的 `ALLOWED_HOSTS`、Rails 的 host authorization 都要放行隧道域名；域名每个 run 一换，用通配写法（如 `.ngrok-free.app`）改动最小。症状是请求到了应用却返回 400 或「Blocked request / host not allowed」，本机直连正常。

**隧道的持有与拆除**：`run` 由前台 CLI 进程持有，命令结束或 Ctrl-C 即拆；`submit` 由本机后台进程持有，run 到终态即拆；`submit --backend cloud` 由本机守护进程持有，到终态或 `--tunnel-ttl` 到点即拆。三种都要求**本机保持开机联网到 run 终态**。用 kill 命令结束 CLI 不会拆隧道，要到进程列表里结束 ngrok。隧道断了不自动重连，受影响的 scenario 以导航失败告终，修好后重新运行。

**排障入口**：CLI 打的「隧道已建立」那行给出原始地址与替换后的公网地址（Host 放行要用它的域名）；本机后端 `submit` 的隧道进程号记在 `<report-dir>/<run_id>/tunnel.json`；`submit --backend cloud` 的隧道守护进程日志在系统临时目录的 `gherkai-tunnel-watch-<run_id>.log`（提交时「隧道由守护进程持有」那一行给出完整路径）；起隧道的完整日志（ngrok 自己的日志）在系统临时目录里以 `gherkai-tunnel-` 开头、文件名不含 watch 的 `.log` 文件，按修改时间取最新；`submit` 若打出「隧道已拆除」，这个 run 已经不可用，别再等它的结果，修好报错后重新提交。

**向用户说明隧道的安全边界**：隧道存活期间被测应用可从公网访问，gherkai 为每次运行生成专用的访问令牌与会话 cookie、由 ngrok 在边缘校验，不带会话 cookie 的请求到不了本机；step 文本里只有干净的隧道地址；令牌出现在提交记录 `run_meta.json` 的预热地址里（明文，运行要读回），引擎的浏览器访问过预热地址、引擎原生产物里也可能记下它；gherkai 自己写的失败消息、`explain` 输出与 AI 证据里令牌与签名类参数显示为 `***`，引擎原生产物不脱敏，报告按内部资料对待；会话 cookie 会出现在被测应用的访问日志里；只把测试实例接上隧道。

**预热失败的四种消息**（都在 `status` 的 job 消息里，scope 没执行任何 step）：「隧道会话预热被拒绝：访问令牌或会话 cookie 不被边缘节点接受…」是令牌被拒（隧道已重建，或两侧隧道配置不一致），重新提交这次运行，仍出现时核对命令行工具与后端是否同版本；「隧道会话预热被拒绝：边缘节点没有收到有效的隧道会话 cookie…」是会话 cookie 未通过校验（浏览器没有保存或没有带上会话 cookie，或隧道在预热期间重建），确认隧道仍在、浏览器允许安全 cookie，必要时换浏览器或设备后重新提交；「隧道会话预热未能确认就绪（已尝试 3 次）…」是隧道已拆或浏览器到隧道入口的网络不通（预热的两个地址都由边缘直接响应，与本机应用是否在运行无关），确认隧道仍在后重新提交；「后端未传递会话预热地址，部署版本可能低于命令行工具…」是云端后端旧于命令行工具，请部署方 `gherkai deploy` 后重新提交。

## 6 版本不一致（`--backend cloud` 退出码 2）

部署时后端记下自己的版本，每条 cloud 命令动资源前先比对：

- **CLI 比后端新时拒绝，以退出码 2 结束，没有强行放行的开关。** 处理：部署方运行 `gherkai deploy` 把后端升级到同版本；或临时使用与后端同版本的 CLI：`uvx --from 'gherkai==<后端版本>' gherkai …`，不改动本机安装。
- CLI 比后端旧时只提示、不拦，用 `uv tool upgrade gherkai` 升级。
- 升级顺序：部署方先升 CLI、立刻 `gherkai deploy`，其他人再升自己的 CLI；中间窗口里提交被拒是预期。

## 7 症状与处置

| 你看到 | 多半是 | 怎么办 |
|---|---|---|
| 以退出码 2 结束，说某引擎 worker 未找到 | 没装或不在 PATH | 照打印的装法装；或设 `GHERKAI_WORKER_<ENGINE>_CMD` |
| `engine_error`，起 worker 失败 | worker 版本与 CLI 不一致 | 重装到同版本（第 1 节） |
| `release_failed`，说明里说会话未能确认停止并列出会话名 | worker 停止会话时失败或超时，或收到停止信号时建立会话的请求还没有返回；会话可能仍在计费 | 把会话名与说明里的核对位置原样转告用户：桌面目标的浏览器会话在 Amazon Bedrock AgentCore 控制台，设备目标的远程访问会话在 Device Farm 控制台（云端后端也可看 `doctor --backend cloud` 的 `devices.sessions` 行）；停止前须确认没有 run 在使用它。已报出的 scenario 结果照常可读，别靠重新运行掩盖残留会话 |
| `precheck_failed`，设备 scope 一条 step 都没执行 | 没有符合条件的设备、指定的设备 ARN 被拒、安装包不在或不可读、应用启动后立即自行退出、设备拒绝安装驱动辅助程序；重新运行不会变 | 按消息改设备选择、换测试包或换设备；应用启动即自退多半是应用带运行环境检测，要人提供关闭检测的测试包 |
| `acquire_timeout` | 在获取设备的等待时间内没拿到可用设备 | 稍后重新运行，或请人在 `gherkai.toml` 的 `[devices]` 调大 `acquire-timeout-s`；等待期间可能已产生设备分钟，别连续重试 |
| `session_lost` | 远程访问会话在执行中途结束（被人手动停止，或到达会话上限），本 scope 余下的 scenario 未执行 | 判定不完整，别当用例失败汇报；缩短 scope 后重新运行，或请人核对是否有人停止了会话；会话也可能在准备设备时就已结束（获取设备、启动应用或会话预热期间），这时本 scope 的 step 都没有执行，不必缩短 scope，请人核对是否有人停止了会话后重新运行 |
| step 记 `capability_unavailable` | 这台设备不提供这一步需要的能力（需要网页上下文的确定性 step、设备不支持经系统打开地址、Android 地址含没编码的 `;` `'` `(` `)` 或空格、非 ASCII 字符） | 改写为 AI 步、改地址或换设备；重新运行不会变 |
| 设备上 step 记 `engine_error`，消息说「这一步可能已执行也可能未执行」 | 设备命令在等待时间内没有回应，本 scenario 余下的 step 未执行 | 先用 `explain` 看这一步的证据核对设备状态（AI step 看截图，确定性与导航 step 看控件摘要与原始控件树），再收窄重新运行这一条 |
| 启动时报告未设置 region 的错误 | `--region` / `AWS_REGION` / `AWS_DEFAULT_REGION` / 配置文件的 `region` / profile 配置五处都没有 region | 任选一处设上（第 4 节）；缺失时不会改用任何默认 region |
| `AccessDenied` / 模型不可用 | region 未开通模型，或凭证缺 Bedrock / AgentCore 权限 | 换 region 或补权限（第 4 节） |
| Midscene 侧某个 step 文件里的 step 全走了 AI、`list-deterministic` 清单里也没有它，且没有任何报错 | 扩展名用了 `.ts` / `.js`（收集阶段按扩展名过滤，静默跳过、不 import） | 改成 `.mts` / `.mjs` |
| `plan` / `run` 以退出码 2 结束并点名某个 steps 文件 | 该文件加载失败 | 修那个文件，不是 feature |
| 明明写了 `steps/` 却全走 AI | 目录没被读到或正则不匹配 | `list-deterministic --steps-dir …` 核对；对照 `example` 改 step 文本 |
| `status` / `explain` 以退出码 2 结束、说找不到 run（提示只提 `submit`） | 三个参数与**产生这个 run 的那条命令**（`run` 或 `submit`）不一致 | 照那条命令逐字对齐 `--backend` / `--report-dir` / `--prefix` |
| `status` / `explain` 以退出码 2 结束、说提交记录由更新或更早版本写出 | 记录格式与本机 CLI 不一致 | 更新版本写出的就升级本机 CLI；更早版本写出的就按消息换用那个版本查看，或用当前版本重新提交 |
| `--expose-local` 起隧道失败 | 没装 ngrok、或 authtoken 没配（配置文件与环境变量都没有）、或填的是 API key、或本机没外网 | 第 5 节 |
| 隧道已建立，每条 scenario 第一步导航就失败，应用日志里没有请求 | 选项值与 feature 书写的地址不一致（localhost 对 `127.0.0.1`、端口、大小写），地址没被替换 | 第 5 节：`plan --expose-local` 回显与 step 文本逐字对照，改成一致 |
| 请求到了应用，页面返回 400 或「host not allowed」，本机直连正常 | 开发服务器校验 Host，拒绝了隧道域名 | 第 5 节：放行隧道域名（通配写法） |
| run 中途开始每条 scenario 都导航失败 | 隧道已拆：本机关机或断网，或 `--tunnel-ttl` 到点 | 保持开机联网；批量大时给更长的 `--tunnel-ttl` |
| 收窄参数以退出码 2 结束并列出候选 | `--scope` / `--scenario` / `--tags` 筛成空集 | 从列出的候选里挑正确的值 |
| cloud 命令以退出码 2 结束、说 CLI 新于后端 | 版本不一致 | 第 6 节 |
| cloud 提交以退出码 2 结束、说 variant 没推过 | 某引擎缺该 `--worker-variant` | `gherkai deploy list-workers` 看有哪些；推它或换名（`references/cloud-backend.md`） |
| Nova Act 引擎下非英文页面断言判否 | 引擎语言面 | `references/engines.md` 第 1 节 |
| `plan` 打「标注降级」 | 某引擎 worker 不可用，只影响标注 | 不阻塞 plan；要标注就把那个 worker 装上 |
