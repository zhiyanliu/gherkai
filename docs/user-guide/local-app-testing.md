# 测本机或内网里的被测应用

浏览器跑在云端，访问不到 `http://localhost:3000`。本机 local 与云端 cloud 两个后端在这一点上相同：local 只是把 worker 进程放在你的机器上，浏览器始终在云端，所以两个后端测本机应用都要用 `--expose-local`。

本页讲 `--expose-local` 的前置、行为、隧道的持有进程、存活时间上限与限制。四种跑法的选择、结果读法与退出码见 [`running-and-results.md`](./running-and-results.md)；选项与环境变量总表见 [`configuration.md`](./configuration.md)；按症状排障见 [`troubleshooting.md`](./troubleshooting.md)。

## 工作方式

`--expose-local <ORIGIN>` 让 gherkai 在本机起一条出站隧道，并在组装任务时把 feature 文本里的 `ORIGIN` 替换成隧道分配的公网地址。feature、引擎与 AI 都不感知隧道。

![云端浏览器经隧道服务商边缘回到本机的隧道进程，再由它转发给被测应用；第三方域资源由浏览器直连、不经隧道，公网上不带凭据的访问者被拦在边缘](../diagrams/local-app-testing-tunnel-topology.svg)

图注（隧道拓扑）：浏览器 → 边缘 → 隧道进程 → 被测应用这条实线链是请求方向，响应沿同一路径返回；隧道是本机发起的出站长连，你的机器不开入站端口；命令行到隧道进程那条边只表示起进程。隧道服务商、凭据与请求头的具体形态见下文各节。

`ORIGIN` 是「跑 CLI 的这台机器可达」的任意地址，不限 `localhost`：局域网另一台机器上的应用（如 `http://192.168.1.50:3000`）同样可以，目标机器不需要任何配置。

隧道模式下，云端浏览器发出的请求恒带一个固定请求头 `ngrok-skip-browser-warning: 1`，用于跳过 ngrok 对浏览器返回的警告页（被测应用的访问日志里会看到它）；机读输出里对应 `extra_http_headers` 字段，应用侧不需要为它做任何处理。

## 前置：ngrok 与 authtoken

两项都要，缺任一项都会在起隧道时失败并退出码 2；`gherkai doctor` 不检查这两项。

1. 安装 ngrok 并让它在 PATH 上（`ngrok version` 能跑）。下载地址：https://ngrok.com/download
2. 配置 authtoken（免费账号即够），下面两种方式任选一种：

```bash
ngrok config add-authtoken <token>   # 写进 ngrok 自己的配置文件
export NGROK_AUTHTOKEN=<token>       # 或者用环境变量
```

`<token>` 在 ngrok dashboard（https://dashboard.ngrok.com/ ）的 **Your Authtoken** 页取。不要用 **API Keys** 页上的值：API key 只能调 ngrok 的管理接口，拿它起不了隧道。两类值都是长随机串、肉眼分不出，按页面取值。填错时会以「隧道未就绪」失败，报错附带的 ngrok 日志会点明鉴权原因。

## 用法

feature 里照写原始地址，不要写隧道地址：

```bash
# 前台跑：命令结束即拆隧道
gherkai run my_app.feature --expose-local http://localhost:3000

# 提交到本机后台跑
RUN_ID=$(gherkai submit my_app.feature --expose-local http://localhost:3000)

# 提交到云端后端跑
RUN_ID=$(gherkai submit my_app.feature --backend cloud --prefix gherkai- \
  --expose-local http://localhost:3000)

# 预检：plan 不起隧道，按原文打印每个 step，并回显你给的取值
gherkai plan my_app.feature --expose-local http://localhost:3000
```

选项值必须与 feature 中书写的形式完全一致：替换是前缀字符串匹配，`http://localhost:3000` 与 `http://127.0.0.1:3000` 两者不会互相匹配。替换覆盖 step 文本以及它挂的 DocString 与 DataTable 单元格。

替换按纯字符串命中，不做端口边界判断：同一批 feature 里若还有以选项值为前缀的地址（如 `http://localhost:30000`），会被一并改坏，这种情况先把端口写法区分开。

`plan` 的「注：」行只是把你给的取值原样回显，不检查 feature 里有没有这个地址——地址写错时 `plan` 同样不报异常。把这一行的地址与 `plan` 打印出的 step 文本逐字符对照（大小写、端口、`localhost` 与 `127.0.0.1` 都要一致），即可确认能替换上。

隧道建立后 CLI 打印一行「隧道已建立：<原始地址> → <公网地址>」。`--tunnel` 选择隧道服务，当前只有 `ngrok` 一个取值，默认即它。

## 隧道的持有进程与拆除时机

隧道进程的位置见「工作方式」的隧道拓扑图；下表列各跑法由谁持有隧道、何时拆。

| 跑法 | 持有隧道的进程 | 拆除时机 |
|---|---|---|
| `run`（`--backend local` 或 `cloud`） | 前台的 CLI 进程 | 命令正常结束或 Ctrl-C 时拆 |
| `submit`（默认 `--backend local`） | 本机的后台进程（隧道进程号记在 `<report-dir>/<run_id>/tunnel.json`） | run 到终态即拆；该后台进程异常退出时，由 `gherkai status <run_id> --wait` 接力拆 |
| `submit --backend cloud` | 本机的隧道守护进程（日志落系统临时目录的 `gherkai-tunnel-watch-<run_id>.log`） | run 到终态即拆；到存活时间上限也拆 |

因此：**用了 `--expose-local`，本机要保持开机联网直到 run 达终态**。隧道拓扑图上从边缘回到被测应用那一段全在你的机器这一侧，关机或断网等于隧道断，剩下的 scenario 会以导航失败告终。云端后端平时可以提交完就关机，用了 `--expose-local` 时不行——这是那条便利的唯一例外。

提交后用 `gherkai status <run_id> --wait` 等到 run 达终态：这条命令会一直等到 run 结束再返回。本机后端用过非默认 `--report-dir` 时要带上同一个值，否则查不到这个 run；云端后端还要带 `--backend cloud --prefix <前缀>`。两档的定位参数都与 `submit` 时一致，照抄 `submit` 打出的那行提示即可。

## 存活时间上限：`--tunnel-ttl S`

只有 `submit --backend cloud` 配 `--expose-local` 时用得上，作用是防止 run 卡住时隧道长期留在公网。

- 默认值按这一批任务算：各 job 的墙钟预算之和，再加 900 秒固定余量（云端排队、拉镜像与收尾的时间）。job 预算来自 `@timeout` 标签或 `--default-job-timeout`（默认 300 秒）；把 `--default-job-timeout` 设成 0 或负数（不超时）时，算这个上限仍要给每个 job 记一个预算，按 3600 秒计。
- `submit` 会把生效的秒数打印出来，不用自己算。
- 到点**无条件**拆隧道。调小有风险：短于 run 实际耗时时，剩下的 scenario 在被测应用不可达的情况下继续跑，以导航失败告终。
- 值须为有限正数，否则退出码 2。
- run 提前到终态时隧道也提前拆，不会等满这个时间。

## 安全

- 隧道存活期间，被测应用可从公网访问。gherkai 默认开启 basic-auth：凭据随机生成、每个 run 换一次，由 ngrok 在边缘节点校验，不带凭据的请求到不了你的机器（隧道拓扑图上被拦在边缘的那条支路）。
- 凭据内嵌在替换后的地址里，因此会出现在提交的任务文本、发给模型的提示以及报告中的导航地址里。隧道一拆凭据即失效，但报告与日志仍应按内部资料对待。
- 只把测试环境的实例接上隧道，不要暴露带生产数据或生产凭证的服务。
- 隧道进程是本机上一个可见的独立进程。命令正常结束与 Ctrl-C 都会拆隧道；用 `kill` 结束 CLI 进程不会拆（SIGTERM 与 `kill -9` 都不会），此时在进程列表里找到 `ngrok` 结束它即可。

## 限制

- 一个 run 只能暴露一个地址。重复给 `--expose-local` 不会报错，只有最后一个取值生效——前面给的地址不会被替换，用到它的 scenario 会导航失败。被测应用依赖多个本机地址时，先让它们收敛到同一个入口再测。
- 只替换与选项值完全相同的前缀，且按纯字符串命中（见上「用法」）。
- 被测应用收到的 `Host` 头是隧道分配的 ngrok 域名，不是 `localhost`——「工作方式」的隧道拓扑图上，浏览器导航的是边缘分配的公网地址。校验 Host 的开发服务器要先放行这个域名（Vite 设 `server.allowedHosts`、Django 加 `ALLOWED_HOSTS`、Rails 放宽 host authorization），否则应用会在框架层拒绝请求。域名每个 run 一换，用通配写法（如 `.ngrok-free.app`）改动最小。
- 隧道转发 HTTP、HTTPS 与 WebSocket 流量。被测应用自身域下的请求（HTML、脚本、样式、图片、接口）全部经隧道，吞吐与延迟受隧道链路影响，也都计入 ngrok 配额；页面引用的第三方域资源由云端浏览器直接访问，不经隧道（隧道拓扑图上通向第三方域资源的那条虚线）。
- ngrok 免费层有配额（量级为每月 1 GB 流量与 2 万次请求，以 ngrok 的定价页为准），重度使用可能超出配额，表现为 429 或断流。
- 隧道断了不会自动重连。受影响的 scenario 以导航失败告终，修好后重跑即可。

## 常见故障

ngrok 没装、authtoken 没配这两类报错见[排错](./troubleshooting.md)的隧道节。下表只列隧道特有的症状。

| 症状 | 原因 | 处置 |
|---|---|---|
| 隧道起来了，但每个 scenario 都在第一步导航失败 | 选项值与 feature 里书写的地址不一致；或被测应用没在监听该地址 | 跑 `gherkai plan my_app.feature --expose-local <ORIGIN>`，把回显的取值与打印出的 step 文本逐字符对照；再在本机直接访问一次该地址，确认应用在跑 |
| 页面返回「Host 不被允许」一类的提示或 400，但 `plan` 对照无误、本机直连也正常 | 被测应用只接受自己配置的域名，拒绝了隧道域名 | 在应用的允许域名列表里加上隧道域名（地址见「隧道已建立」那一行），或临时放开该校验后重跑 |
| run 跑到中途开始，之后每个 scenario 都导航失败 | 隧道已拆：本机关机或断网，或存活时间上限到点 | 保持本机开机联网；批量很大时用 `--tunnel-ttl` 显式给一个更长的值 |
| 加载变慢、间歇 429 | 碰到免费层的配额或带宽限制 | 减少一次跑的 scenario 数，或升级 ngrok 套餐 |
| `submit` 打印「隧道已拆除（本机的被测应用不再对外暴露）」 | 提交过程中出错，接手隧道的后台进程没起来 | 先修同时打出的那条报错，再重新提交。如果上面已经打出提交成功（拿到了 run_id），这一批已经不可用：不要再等它的结果，它要访问的地址已随隧道失效，只会以导航失败告终 |

起隧道失败时，报错只附 ngrok 日志的尾部。完整日志是系统临时目录下的 `gherkai-tunnel-*.log`，每起一次隧道一个文件，按修改时间取最新的那个。

feature 的写法与断言规范见 [`writing-features.md`](./writing-features.md)，示例 feature 在 [`features/`](../../features/)。
