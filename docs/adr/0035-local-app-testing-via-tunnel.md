# 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器

> **Status:** Partially-superseded-by 0051 —— 决策 4 的「凭据内嵌地址」被 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13 改为「令牌换 cookie、worker 预热一次」（iOS Safari 不采用地址内嵌凭据，设备浏览器也没有注入请求头的通道，统一后桌面与设备一条路）；随之改写的还有决策 1 的 `TunnelInfo` 形态与服务商能力要求、决策 2 的匹配规则（由子串替换精化为带边界的识别）、决策 5 的脱敏规则与「明确不脱敏」清单、「边界与不变量」里「worker 对隧道无知」一条（worker 多做一次预热导航）并新增 definition 完整性不变量；其余决策不变。未被改写的部分设计与实现均已落地：`--expose-local` 在 run/plan/submit 三命令 + `runtime/gherkai_runtime/tunnel.py`（ngrok provider + URL 映射）与 `runtime/gherkai_runtime/tunnel_host.py`（宿主编排：起隧道/映射 definition/守护循环与其 TTL），四种「执行方式 × 执行后端」组合全支持（三形态隧道宿主 + 兜底拆除、额外请求头注入）。按 0051 决策 13 改写的部分尚未实现，代码仍是地址内嵌 basic-auth 凭据：决策 4 的令牌换 cookie 与 worker 预热、决策 1 的干净隧道地址与 `warmup_url`、决策 2 的带边界识别、决策 5 对签名类与令牌查询参数的脱敏、「边界与不变量」里的预热导航与 definition 完整性不变量。

## 背景与问题

浏览器跑在 AWS AgentCore（`aws.browser.v1`，CDP 驱动），此前隐含假设被测应用公网可达（wikipedia/example.com 级）。但本工具的主场景之一恰恰相反：**被测应用跑在开发者本机**——依赖只在本地环境齐备、开发到一半的东西不该为了测试走发布流程。矛盾固有：云端浏览器无法路由到开发机的 `localhost`。

## 调研结论（内联，自包含）

对四条候选路线做过源码级/文档级核查（Playwright 1.61 bundle、nova-act SDK 源码、AWS 文档与官方 samples、CDP 协议定义）：

**① CDP 请求拦截喂送**（worker 侧 `page.route()` 拦截远端浏览器请求、本地取内容、`Fetch.fulfillRequest` 喂回）——能力边界在协议层焊死：
- **WebSocket 不可拦截**：CDP Fetch 域对 ws upgrade 不产生 `requestPaused`，Network 域只有观测事件、无干预命令（devtools-protocol#147；Playwright `routeWebSocket` 是页面内 JS mock，真实连接仍从远端网络发起、够不到客户端 localhost）。
- **SSE/流式响应不支持**：`fulfillRequest` 的 body 是一次性 base64 全量；Playwright 流式 fulfill 至今是 open issue。
- Service Worker 发起的请求绕过 route（需 block SW）；redirect body 不可得；`https→http` 改写 URL 被禁（须同协议）。
- **性能税**：只要挂 route，Playwright 就强制 `Network.setCacheDisabled` 且 `Fetch.enable` 用 `urlPattern:'*'`——每个请求（含不拦的域）全量 pause 往返，body 以 base64（×1.33）过 WAN。实测参照：一个 4.9MB 静态站单次加载 ≈6.6MB 过 wss，且浏览器缓存全程失效。
- **Nova Act 侧执行模型脆**：SDK 自注册 `context.route("**")` 做 SSL 校验且从不 fallback（后注册先匹配 → 我们的 context 级 route 被静默遮蔽，只能用 page 级）；SDK 在 teardown/HITL 时 `unroute_all` 抹 context 级 route；Python sync route handler 跑在 greenlet 里、CDP 翻译在独立 node driver 子进程——被 pause 的请求要经「driver→stdio→greenlet 调度→stdio→driver」往返，而 greenlet 只在 worker 泵 Playwright 时被调度，**两次 act 之间的静默期请求会 stall**（与 [0024](./0024-worker-core-protocol.md) sync-over-greenlet 雷区同源）。

**② Playwright `exposeNetwork`**（官方 remote browser 访问客户端本地网络的方案，反向 SOCKS5）——机制：Playwright server 在浏览器同机起 SOCKS 代理、浏览器以 `--proxy-server=socks5://127.0.0.1:<port>` 启动、匹配规则的拨号经 client↔server 的 **Playwright 自有协议**连接 relay 回客户端进程执行。**对 AgentCore 三个环节全断**：托管浏览器启动 flags 不可配；浏览器同机没有我们的进程；relay 通道寄生在 Playwright protocol 上而我们只有 CDP 连接（`connectOverCDP` 无此 option）。

**③ AgentCore Browser VPC 模式**——自建 browser 资源支持 `networkMode=VPC`（2025-09 起，`vpcConfig{subnets,securityGroups}`，创建后不可改），可访问 VPC 内私有 IP（官方 sample 08 演示内网应用）。但**够不到开发者笔记本**：AWS Client VPN 对 IPv4 做 SNAT、VPC 侧无法反向寻址 client。它适配的是「被测应用本身跑在 VPC 内（云上开发机）」的场景——与本 ADR 的「本地应用」正交，留作口子（见被拒方案）。

**④ 出站隧道**（行业标准：BrowserStack Local / Sauce Connect / LambdaTest 全为此架构）——本机隧道 client 主动建 outbound 长连到服务商边缘，边缘分配公网 URL，浏览器流量经该长连回传、client 本地拨号。**本机零入站端口**；对浏览器而言被测应用就是普通公网 HTTPS 站点，故 HTTPS/WebSocket/cookie 天然全通、**双引擎零协议侵入**（不碰 Nova SDK 黑盒）、local/cloud 执行模式全通。Playwright `exposeNetwork` 本质是同构方案（relay 宿主不同）。AWS 原生无对应物（SSM 端口转发方向相反；IoT Secure Tunneling 两端 localproxy、不产 URL）。

**决策：走路线④。**

## 决策

### 1. `TunnelProvider` 可插拔口子（`gherkai-runtime` 组合根共享层），首个实现 = ngrok

- 协议形状：`start(local_origin, *, with_auth=True, timeout_s) -> TunnelInfo`（frozen dataclass `url` / `pid` / `local_origin`，`mapped_base` 是干净的隧道地址（不再内嵌凭据），另带本 run 的会话预热地址 `warmup_url`——鉴权契约见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13）+**模块级 `stop_tunnel(pid)`**。停止面按 **pid** 而非进程对象/实例方法：收尾者与起隧道者常不在同一进程（决策 3 三形态宿主），进程句柄传不过去，故 `TunnelInfo` 携带 pid、由收尾者 kill。就绪判据 = 轮询 agent 日志到 `started tunnel` 行（见下「拿公网 URL 走日志文件通道」条），**不做持续健康探活**——隧道断的失败形态已够清晰（导航失败，见「边界与不变量」），不值守护复杂度。住 `runtime/gherkai_runtime/`（组合根共享层——cli/未来 WebUI 复用；core 对隧道无知，worker 只做一次预热导航、不感知令牌与 cookie 的值，见「边界与不变量」）。
- 选择参数：`--tunnel <provider>`（默认 `ngrok`，当前唯一实现）——机制与 flag 同期落，将来加实现零接口变化。
- **首发只做 ngrok**：鉴权所需的边缘能力在免费层可用（流量策略：按路径、查询参数、cookie 精确值分支，返回带固定头的自定义响应——见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13），免费层的两条硬约束已实测：每个策略至多 5 条规则，`remove-headers` 是付费功能。不具备这两项边缘能力的服务商不能作为隧道实现，启动隧道时 fail-loud。
- **本项是对 [0009](./0009-maximize-aws-hard-constraint.md)「最大化用 AWS」的显式例外**（按 0009 要求登记）：ngrok 是 AWS 外的第三方 SaaS，但「开发机 → 云端浏览器」的入站通道在 AWS 内实查无等价物（SSM 端口转发方向相反；IoT Secure Tunneling 两端 localproxy、不产公网 URL；AgentCore Browser VPC 模式够不到开发者笔记本，已评估并缓——见调研结论③与被拒/被缓方案）。例外面压到最小：经 `TunnelProvider` 口子隔离、仅 `--expose-local` 显式启用、数据面只有被测应用自身流量（模型/浏览器/存储/编排仍全在 AWS 内）。
- **拿公网 URL 走日志文件通道**（`--log <file> --log-format json`，轮询 `msg:"started tunnel"` 行取 `url`）——本地 agent API 在 v3 下对 `ngrok http` 不可配端口（`--web-addr` 是配置文件项、非 flag，真跑暴露 unknown flag；注入需劫持用户 config，多 run 并存还撞默认 4040）。**稳定性权衡**：该日志消息文本严格说非 API 契约，但从 v2 到 v3.39 十余年未变、社区自动化广泛依赖；护栏 = 解析不到 URL 即 fail-loud（超时+日志尾部报错，不静默错），authtoken 配错等诊断天然同在此通道（真验中即靠它报出根因）。若未来真变，备选 =「`ngrok config check` 发现默认 config → `--config` 叠加临时 web_addr → agent API」，经 TunnelProvider 口子替换、不动调用方。**前置：用户需配 authtoken**（免费账号，`NGROK_AUTHTOKEN` 或 ngrok 配置文件）；免费层配额 1GB/月 + 2 万请求/月——页面资源全经隧道，重度使用可能碰顶，报错形态为 ngrok 侧 429/断流（文档预告）。

### 2. URL 映射：feature 写原始地址，组装 job 时替换

- feature 里自然书写本地地址（如 `http://localhost:3000`）——它是用例的**逻辑事实**，不感知隧道。
- CLI 加 `--expose-local <origin>`：组合根起隧道拿到公网 URL 后，**在 job 组装（job-in 之前）把 step 文本**及其 argument（docString 内容 / dataTable 各单元格——URL 可能出现在任一处）**中的该 origin 替换成干净的隧道地址**——映射对 worker/引擎/AI 透明（AI 看到的就是可导航的公网地址；鉴权由 worker 的一次预热导航完成，见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13，step 文本里不出现令牌）。flag 值须与 feature 中书写形式一致（`localhost` vs `127.0.0.1` 不互认，大小写也须一致，文档写明）。
- **识别带边界，不是子串替换**：URL 字符集按 RFC 3986（unreserved、reserved 与 `%`；全部非 ASCII、空白、引号、尖括号、反引号、竖线都不是 URL 字符）；左边界为串首或非 scheme 字符（`[A-Za-z0-9+.-]` 之外），所以 `next=http://localhost:3000/x` 这类嵌在别的地址查询里的写法照常映射、`xhttp://…` 不映射；右边界为 origin 之后最长的连续 URL 字符串 R 为空、或以 `/ ? #` 开头、或全部由尾随标点 `. , ; : ! ) ] '` 构成。钉死的用例：`http://localhost:3000.evil/` 与 `http://localhost:30001/x` 不命中；`去 http://localhost:3000。`、`Go to http://localhost:3000.`、`(see http://localhost:3000)`、`打开http://localhost:3000/a页面` 命中。step 正文、DocString、表格单元格各自独立套用，一段文本可以有多处命中。曾是裸子串替换：`http://localhost:3000` 会命中 `http://localhost:30001/x`，与本条「前缀」的本意不符。
- **origin 语义 =「跑 CLI 的机器可达」的任意地址，不限 localhost**：局域网/内网另一台机器上的应用（如 `http://192.168.1.50:3000`）同样支持——ngrok agent 本就是转发器，upstream 可为任意本机可达 host:port；目标机器**零配置**，唯一前提是 CLI 机器 → 目标地址网络可达（隧道宿主始终在 CLI 机器，含 cloud submit 的守护进程——CLI 机器关机即断，同边界）。flag 名中的 "local" 取「CLI 视角的本地网络」义。
- **`plan` 输出替换前的原始地址**：plan 是纯本地零副作用预检，隧道 URL 是运行时产物（每 run 一条、随机域名），plan 时起隧道既违背「不连外」也无意义。给了 `--expose-local` 时 plan 在输出中**标注**该 origin 将经隧道映射（可见性，零副作用）。

### 3. 四种「执行方式 × 执行后端」组合全支持；隧道生命周期按宿主分三形态

| 组合 | 隧道宿主 | 拆除时机 |
|---|---|---|
| 前台 `run`（local/cloud backend） | CLI 进程 | CLI 进程 `atexit` 拆——**有意选 atexit 而非 finally**：正常结束与 Ctrl-C 都收；SIGTERM 直杀的极端泄漏不兜（ngrok agent 是可见的独立进程，人能自行 kill） |
| local `submit` | per-run 推进进程 | `detached.drive_local_reconcile`（local 推进唯一入口）tick 到终态后拆；per-run 进程崩溃时由 `status --wait` 接力者走同一入口、据 `tunnel.json` 兜底拆 |
| cloud `submit` | **隧道守护进程**（setsid fork 脱离 CLI） | 轮询 run 终态即拆 + TTL 兜底自杀（防泄漏），TTL 按 definition 算——见下；**任何异常路径同样拆**（store 装配抛 / 轮询被中断）：守护进程是隧道唯一宿主，它带着异常死掉没人再拆——曾只在循环之后拆、装配段裸奔，装配一炸 ngrok 即永久留在公网（code-health 对抗验证发现） |

- 表外还有一处就地拆，**判据 = 交棒边界**：交棒发生在**后台宿主 fork 成功那一刻**（local=推进进程、cloud=隧道守护进程），由被调方回调通知调用方，故边界紧跟 `Popen`、不是提交函数收尾。此刻**之前**的任何失败——返回非 0（cloud 各道闸：版本 skew / 资源 preflight / variant 解析 / 落库时云端不可达）或抛异常（解析 profile、落库、建 events 库、开日志文件、fork 自身）——隧道都还没有宿主可交棒，由 CLI 当场拆；此刻**之后**即便收尾几行抛（stdout 是坏管道、Ctrl-C 恰落此窗）也**不拆**：宿主已在跑，拆了等于把隧道从活着的宿主底下抽掉，剩余 job 在被测应用不可达下跑成假失败——兜底机制反成失败源，还烧真钱。
  - **被接受的代价：「已落库但未交棒」这一格**（cloud 后端 `create_run` 已过而守护 fork 失败；local 后端 `create_run` 已过而推进进程 fork 失败）仍按未交棒拆——公网暴露此时没有任何收尾者，拆是对的；代价 = 这个 run 之后被云端链/接力者推进时必以导航失败告终（要访问的地址已随隧道失效），故 CLI 在拆的同时明示（「隧道已拆除、这一批别再往下推、先修问题再重新提交」），否则用户只看到一个非零退出、以为什么都没发生，而云端照跑照烧钱。
- **隧道 agent 进程自身也 setsid**（spawn 时 `start_new_session=True`）：agent 的存活该由**宿主**决定（上表三形态 + `stop_tunnel(pid)` 这唯一拆除面），不该由终端的信号转发决定。否则 agent 与 CLI 同进程组，`submit` 时 CLI 收到终端广播的 SIGINT/SIGHUP 会**连坐杀掉正要交棒给后台宿主的 agent**——两个后台宿主本身都 setsid、唯独被交棒的 agent 不，交棒链就断在这一环。**已真跑核实（真 spawn + 真 `killpg`，非 mock——进程组归属属「绿测试覆盖不到的真实行为」）**：同组时一发 SIGINT 广播必杀 agent；agent 自成进程组后存活，而前台 `run` 方式语义不变（Ctrl-C → `KeyboardInterrupt` → `atexit` 照常拆，见上表首行「有意选 atexit 而非 finally」）。
- **TTL 按 definition 算，不是一个常数**：`TTL = Σ(各 job 的 timeout_s；无预算者按一个明确上限记账) + 启动/级联余量`（`tunnel_host.compute_watch_ttl_s`；`submit` 算好显式传给守护进程并打印出来，`--tunnel-ttl` 是显式覆盖项）。
  - **为什么不能拍常数**：TTL 到点**无条件**拆隧道。TTL 短于 run 实际预算时，剩余 job 在被测应用不可达的情况下继续跑、以「AI 报导航失败」的形态**假失败**告终——兜底机制反过来成了失败源。（曾是恒定 1h 且没有任何生产写入者：默认 job 预算 300s 下约 12 个 job 起就超。）而运行预算在 definition 里本就是可算的。
  - **求和而非取 max**：并发 >1 时各 job 部分重叠、真实墙钟必 < 各预算之和，故串行总预算对**任何**并发取值都是保守上界（并发上限随 definition 走、cloud 再受部署侧 cap 钳制，见 [0034](./0034-detached-batch-reconciler.md) 机制四——TTL 计算不必知道它的取值，这正是取求和的好处）；高估无害——TTL 偏长=隧道多留一会儿（run 到终态照常提前拆），偏在安全的一侧。
  - **余量兜什么**：`submit` 只写 runs 表，之后还有 Stream INSERT 投递 → kicker 冷启动 → RunTask → 拉镜像/挂 ENI 才真开跑，job 之间又有云端事件链的固有尾延迟（[0034](./0034-detached-batch-reconciler.md) 实测每步 ~20-30s），末尾还有 finalize；而 job 预算从 claim 起算、不含这些。故余量是必需项、不是保险费。
  - 无预算的 job（`--default-job-timeout <=0` 且未标 `@timeout` = 执行侧不超时）按一个明确上限**记账**——TTL 必须有限，否则泄漏兜底整体失效。
- cloud submit 的语义澄清：「提交完就走」=不阻塞 CLI，**不等于关机**——机器继续开着时本地应用与隧道均可用，云端 Lambda 链驱动的浏览器经隧道访问本机应用完全成立。但**关机=隧道断=测试以导航失败告终**：submit 时打印明示（守护进程日志落点 + 生效的 TTL + 「本机需保持开机联网直到 run 终态」），把例外变成明示边界而非静默失败。

### 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式、仅桌面浏览器）

- ngrok 免费层对浏览器返回 interstitial 警告页（对自动化致命）；带任意值的 `ngrok-skip-browser-warning` 头即绕过。付费户带着无害（服务端忽略）→ 不做付费检测、隧道模式下恒注入。设备浏览器（Android Chrome、iOS Safari）没有注入请求头的通道；四台公共真机实测都没有出现警告页，若服务商改变行为则设备目标在隧道模式下要求付费层（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13）。
- 注入通道（通用形状「额外请求头」，全链路单一事实源在此）：组合根把 header 表填进 **`RunMeta.extra_http_headers`**（definition 层字段，tuple pairs；落盘为 dict、键序在写端排序规范化，空表与 `None` 同义均省键，随 META 落盘 DDB/文件）→ 推进器（per-run 进程 / reconciler Lambda）据它重建 engine → engine adapter 注 `GHERKAI_EXTRA_HTTP_HEADERS` env → worker 在 browser context 上 `setExtraHTTPHeaders`——纯 CDP 命令、无回调，**不触碰 Nova 的 route/greenlet 雷区**。两个 worker 各有一处注入点（URL 替换那半边才是 worker 零改动）。**载体为什么是 definition 而非只走 env**：cloud detached 下起隧道的 CLI 进程与重建 engine 的 Lambda 不同进程，env 传不过去，header 表必须随 META 持久化。`GHERKAI_EXTRA_HTTP_HEADERS` 与 `GHERKAI_SESSION_WARMUP_URL` 同属组合根拥有的 worker env，守同一条「有值显式注、无值显式清」的不变量（宿主继承的同名值不得越过 definition），清单与细则见 [0037](./0037-distribution-and-packaging.md) 决策 4。
- **隧道鉴权：默认开启，方案 = 令牌换 cookie、worker 预热一次**（契约全文在 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13，此处只记与本篇的接口）。组合根每 run 生成访问令牌与会话 cookie 值、写进流量策略文件（0600）；边缘只在预热路径凭令牌下发 `__Host-` 前缀的会话 cookie，其余路径只认 cookie 精确值，不带或不对即 401、请求到不了本机；worker 在被测对象就绪前导航预热地址一次并在页面标记上确认。安全面四件套不变：随机 URL + 每 run 一换的令牌与 cookie + 终态即拆 + 精确比对。**对本篇的影响**：step 文本里只有干净的隧道地址，`page.url()`、失败消息、AI 提示与引擎原生产物里不再出现凭据；原方案「文档地址带 userinfo 使被测应用用绝对地址调 `history.pushState` 时抛 SecurityError」这类隧道模式特有的假失败随之消失。
  **曾用方案（被取代，护栏）**：URL 内嵌 basic-auth 凭据（`https://user:pass@host`，经 ngrok 流量策略的 basic-auth 在边缘拦截，靠浏览器按域 auth cache 带后续请求）。它在桌面 Chromium 与 Android Chrome 成立，但 iOS Safari 不采用地址内嵌凭据、改弹系统级鉴权表单且网页上下文看不到；凭据还会进入 job 文本、AI 提示、引擎原生产物与 `page.url()`，并触发上述 `pushState` 假失败。
  被拒候选（防重复调研）：② extra headers 注 `Authorization`——**全域广播**给页面加载的所有第三方域，泄面严格大于 cookie，且设备浏览器没有注入请求头的通道；③ CDP Fetch 域 authChallenge——需开 Fetch 拦截、`authRequired` 事件同样要 handler 响应，撞 Nova 的 greenlet/node-driver 泵动问题（见上「调研结论①」）；④ 令牌作为查询参数写进 step 文本——映射器无法区分导航地址与地址断言的正则参数，令牌又会进入 AI 提示与设备录像（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 被拒方案）；⑤ 浏览器层 HTTP 认证（Playwright `httpCredentials`）——只有桌面 Playwright 上下文能用，Appium 驱动的设备浏览器没有对应通道，且要求边缘回到 basic-auth 质询；它想解决的地址带凭据与 `pushState` 假失败已由令牌换 cookie 消除，Nova Act 的浏览器启动面能否设置也未核实。

### 5. 工具自产文字里的凭据脱敏：剥 URL userinfo 与签名类查询参数，落盘的 run 定义不动

- **动机（演示项目云端真跑实测）**：确定性 step 的失败消息带 `page.url()`、AI 证据的 `url` / `prompt` / `thought`、`explain` 输出、`run --json`、本机转发的 worker 日志，都可能原样带着凭据（原方案里是 `https://用户:口令@主机`；现方案里是预热地址上的令牌参数，以及设备端点与预签名地址上的签名参数）。凭据虽是每 run 一换的短命物，但会随报告复制进工单与聊天、随 S3 产物留存、投屏时打在屏幕上；隧道或会话存活期间能看到这些文字的人就能访问被测机器上的应用或设备端点。
- **规则两条、三份同文实现**：① 把文本里每个 `scheme://userinfo@host` 的 userinfo 段替换成 `***`（`https://***@host`，沿用 pip / git 的显示惯例）。正则作用于 `://` 之后、`@` 之前不含 `/ ? # @ 空白 " \` 的一段，所以能直接作用在已序列化的 JSON 行上而不破坏结构。② 签名类查询参数与隧道令牌参数 `gherkai_tunnel_token` 的值替换成 `***`，并同时覆盖 XML 实体转义形态（控件树属性里 `&` 写成 `&amp;`；[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 11）。不做「拿本次凭据精确回替」：本次凭据分在不同持有者手里——隧道令牌随 definition 下发，设备端点与预签名地址由 worker 在运行时生成且不进任何事件（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 11），core 的 `wire.py` 与 CLI 的 `explain` 这些出口拿不到全部凭据，要回替就得把秘密再传一遍；按形态匹配不需要传递秘密，三份实现的行为也一致。实现三份（`gherkai_core/redact.py`、Nova worker `lib/redact.py`、Midscene worker `lib/redact.mts`）——Nova worker 零 core 依赖、Midscene 是另一种语言，三份文件头互指、测试用同一组用例。
- **收口在出口、不在产生点**：worker 两处（事件 `emit` 序列化后的整行、evidence.json 写盘前的整份），core 两处（`wire.py` 解码事件 `message` 时、`subprocess_engine` 转发 worker 日志每行时），CLI 两处（`explain` 的机读文档整份深度脱敏、`run --json` 输出整份深度脱敏）。放在出口是为了把 `steps/` 里使用方自写 handler 的消息、SDK 自己的 stdout 一并盖住，而不是逐个改消息模板。导航实参（`go_to_url` / `page.goto` 的参数）与 job 文本本身不经过这些出口，凭据照常生效。
- **明确不脱敏（执行依赖明文）**：`run_meta.json`（0600） / DDB META / S3 参数卸载对象 / Fargate job-in 里的 run 定义（推进器要读回会话预热地址注入 worker）、流量策略临时文件（0600）、worker 进程环境里的预热地址、云端 RunTask 的 `containerOverrides`。`jobs/*.json` 不在此列：它只被 `status` 与 `explain` 读取、不是执行输入，且现方案下 step 文本不含秘密，保持 0644 以便 CI 读取。另有一处**原样落库**：worker 发出的原始事件行（本机 detached 的 SQLite 事件库、云端的 DDB events 表）在解码前写入，两个官方 worker 已在 emit 处脱敏、故行内干净，第三方 worker 若不脱敏则行内有明文——core 的 `wire.py` 只盖住解码后的视图。也不改引擎原生产物（Nova 轨迹 html / json、Midscene 报告 html）、云端 CloudWatch 里的 SDK stdout 与 Device Farm 的录像、Appium 日志——它们由 SDK 或服务商写、不经我们的出口，仍按「短命凭据」对待，用户指南与 skill 的安全段照实说明。
- **已知残余**：模型在 thought 里复述地址时若去掉了 `scheme://` 只写 `用户:口令@主机`，规则抓不到；worker 把异常文本压成一行并截到 300 字时先脱敏再截断（否则截在 userinfo 中间会丢掉 `@`、规则失效）；纯 ASCII 逗号把地址与邮箱连写（`https://a.com,x@b.com`）仍会误吞到邮箱的 `@`；隧道 cookie 会到达被测应用的访问日志（剥离是服务商的付费功能）；云端 RunTask 的 `containerOverrides` 带预热地址，task 停止后约 1 小时内仍可经 `ecs:DescribeTasks` 读到，CloudTrail 是否记录该字段待实施期核实。

## 被拒/被缓方案（护栏）

- **CDP 请求拦截喂送**——拒。WS/SSE/SW 能力断崖对「开发中的全栈应用」是真实缺口；带宽税（缓存强制关闭+全请求 pause+base64）；Nova 侧 page 级 route + greenlet/node-driver 泵动的执行模型脆弱（stall 形态偶发、难排障）。静态站场景隧道同样覆盖，无需为其保留第二条路线。
- **Playwright `exposeNetwork`**——不可用而非不好：机制寄生在 Playwright 自有协议与浏览器启动权上，AgentCore 托管场景两者皆无。若未来浏览器宿主换成自管（如自起容器跑 Chromium），此路线值得重估。
- **cloudflared quick tunnel**——缓。零账号是其残留优势，但零认证、官方点名不支持 SSE、`*.trycloudflare.com` 被恶意软件滥用致企业网常见封锁。TunnelProvider 口子已留：ngrok 门槛（authtoken/配额）被用户反馈证明是问题时再加它作第二实现。
- **AgentCore Browser VPC 模式**——口子，非本 ADR 范围：它解决「应用在 VPC 内（云上开发机）」而非「应用在本地」，且需自建 browser 资源（IaC 新资源、创建后网络模式不可改）。真实需求出现时单独立项。

## 边界与不变量

- 隧道仅在 `--expose-local` 显式给出时起——默认路径零新依赖、零出网变化。
- core 对隧道无知（映射在组合根完成）；worker 只做一次预热导航并确认页面标记，不感知令牌与 cookie 的值（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13）。额外请求头与会话预热地址**不新增 worker↔core 协议事件**——definition 层各加一个 omit-when-None 字段（`RunMeta.extra_http_headers`、会话预热地址）+ 复用既有 env 注入面（`GHERKAI_EXTRA_HTTP_HEADERS`、`GHERKAI_SESSION_WARMUP_URL`），core 只搬运不解释语义。
- **definition 完整性不变量**：隧道模式下 definition 必带「额外请求头」与「会话预热地址」两项；worker 收到额外请求头却没有预热地址即记 `precheck_failed`「后端未传递会话预热地址，部署版本可能低于命令行工具，请重新部署」——两个既有事实绑成一个完整性判据，能抓到旧后端丢字段的部署残缺，不按文本猜测；它要防的开发版本混搭场景见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13。
- 本机关机/断网 = 隧道断 = run 以导航失败（AI 报错形态）告终——明示边界，submit 时提示，不做「断线重连恢复」（隧道进程崩溃同理；测试可重跑，不值守护复杂度）。
- **与设备目标的关系**：鉴权契约（预热页面的三种可见结果与归因、cookie 规格、边缘策略的规则数约束、导航路线由能力探测决定）、脱敏规则对查询串凭证的扩展，归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 11 与 13；本篇的地址映射与三形态宿主不变。
