# 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器

> **Status:** Accepted —— 设计已定（v1.3 主特性）；实现随本分支推进。

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

### 1. `TunnelProvider` 可插拔口子（gherkai 组合根层），首个实现 = ngrok

- 协议形状：`start(local_origin) -> public_url` / `stop()`（+健康探活）。住 `gherkai/`（组合根共享层——cli/未来 WebUI 复用；worker/core 对隧道无知）。
- 选择参数：`--tunnel <provider>`（默认 `ngrok`，当前唯一实现）——机制与 flag 同期落，将来加实现零接口变化。
- **首发只做 ngrok**：认证能力免费（Traffic Policy basic-auth，本期默认开启——见决策 4）、付费可去 interstitial。
- **拿公网 URL 走日志文件通道**（`--log <file> --log-format json`，轮询 `msg:"started tunnel"` 行取 `url`）——本地 agent API 在 v3 下对 `ngrok http` 不可配端口（`--web-addr` 是配置文件项、非 flag，真跑暴露 unknown flag；注入需劫持用户 config，多 run 并存还撞默认 4040）。**稳定性权衡**：该日志消息文本严格说非 API 契约，但从 v2 到 v3.39 十余年未变、社区自动化广泛依赖；护栏 = 解析不到 URL 即 fail-loud（超时+日志尾部报错，不静默错），authtoken 配错等诊断天然同在此通道（真验中即靠它报出根因）。若未来真变，备选 =「`ngrok config check` 发现默认 config → `--config` 叠加临时 web_addr → agent API」，经 TunnelProvider 口子替换、不动调用方。**前置：用户需配 authtoken**（免费账号，`NGROK_AUTHTOKEN` 或 ngrok 配置文件）；免费层配额 1GB/月 + 2 万请求/月——页面资源全经隧道，重度使用可能碰顶，报错形态为 ngrok 侧 429/断流（文档预告）。

### 2. URL 映射：feature 写原始地址，组装 job 时替换

- feature 里自然书写本地地址（如 `http://localhost:3000`）——它是用例的**逻辑事实**，不感知隧道。
- CLI 加 `--expose-local <origin>`：组合根起隧道拿到公网 URL 后，**在 job 组装（job-in 之前）把 step 文本中的该 origin 前缀替换成隧道 URL**——对 worker/引擎/AI 完全透明（AI 看到的就是可导航的公网地址）。匹配是前缀字符串级：flag 值须与 feature 中书写形式一致（`localhost` vs `127.0.0.1` 不互认，文档写明）。
- **origin 语义 =「跑 CLI 的机器可达」的任意地址，不限 localhost**：局域网/内网另一台机器上的应用（如 `http://192.168.1.50:3000`）同样支持——ngrok agent 本就是转发器，upstream 可为任意本机可达 host:port；目标机器**零配置**，唯一前提是 CLI 机器 → 目标地址网络可达（隧道宿主始终在 CLI 机器，含 cloud submit 的守护进程——CLI 机器关机即断，同边界）。flag 名中的 "local" 取「CLI 视角的本地网络」义。
- **`plan` 输出替换前的原始地址**：plan 是纯本地零副作用预检，隧道 URL 是运行时产物（每 run 一条、随机域名），plan 时起隧道既违背「不连外」也无意义。给了 `--expose-local` 时 plan 在输出中**标注**该 origin 将经隧道映射（可见性，零副作用）。

### 3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态

| 组合 | 隧道宿主 | 拆除时机 |
|---|---|---|
| 前台 `run`（local/cloud backend） | CLI 进程 | run 结束 finally 拆 |
| local `submit` | per-run 推进进程 | `run_reconcile_loop` 终态后拆 |
| cloud `submit` | **隧道守护进程**（setsid fork 脱离 CLI） | 轮询 run 终态即拆 + TTL 兜底自杀（防泄漏） |

- cloud submit 的语义澄清：「提交完就走」=不阻塞 CLI，**不等于关机**——机器继续开着时本地应用与隧道均可用，云端 Lambda 链驱动的浏览器经隧道访问本机应用完全成立。但**关机=隧道断=测试以导航失败告终**：submit 时打印明示（「隧道已起（守护 pid N）：本机需保持开机联网直到 run 终态」），把例外变成明示边界而非静默失败。

### 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）

- ngrok 免费层对浏览器返回 interstitial 警告页（对自动化致命）；带任意值的 `ngrok-skip-browser-warning` 头即绕过。付费户带着无害（服务端忽略）→ 不做付费检测、隧道模式下恒注入。
- 注入通道：组合根经 worker env 传「额外请求头」（通用形状），worker 在 browser context 上 `setExtraHTTPHeaders`——纯 CDP 命令、无回调，**不触碰 Nova 的 route/greenlet 雷区**。两 worker 各几行改动（URL 替换那半边才是 worker 零改动）。
- **隧道认证（basic-auth）：本期做、默认开启，方案 = URL 内嵌凭据**。框架每 run 生成随机凭据（纯字母数字，规避 URL-encode），经 ngrok Traffic Policy `basic-auth` 在**边缘节点拦截**（不带凭据的请求到不了本机）；URL 替换时嵌成 `https://user:pass@host` 形态——首次导航后凭据进浏览器**按域 auth cache**，同域后续请求（子资源/AI 点击/XHR）自动带，且只发隧道域。安全面从三件套升为四件套：随机 URL + 随机凭据 + 每 run 一换 + 终态即拆。
  已知软性代价（接受）：凭据出现在 job 文本/AI prompt/引擎原生产物（报告里的导航 URL）——皆为短命物，隧道拆除即失效，留存的是死凭据；浏览器的 Referer/地址栏显示会剥离 userinfo，不经这两面外泄。已知小概率分支：AI 重写 URL 时剥掉 `user:pass@` → auth cache 兜底；若首次导航即剥则 401、失败形态清晰（AI 报断言失败）。
  被拒候选（防重复调研）：② extra headers 注 `Authorization`——**全域广播**给页面加载的所有第三方域，泄面严格大于①；③ CDP Fetch 域 authChallenge——需开 Fetch 拦截、`authRequired` 事件同样要 handler 响应，撞 Nova 的 greenlet/node-driver 泵动问题（见上「调研结论①」）。

## 被拒/被缓方案（护栏）

- **CDP 请求拦截喂送**——拒。WS/SSE/SW 能力断崖对「开发中的全栈应用」是真实缺口；带宽税（缓存强制关闭+全请求 pause+base64）；Nova 侧 page 级 route + greenlet/node-driver 泵动的执行模型脆弱（stall 形态偶发、难排障）。静态站场景隧道同样覆盖，无需为其保留第二条路线。
- **Playwright `exposeNetwork`**——不可用而非不好：机制寄生在 Playwright 自有协议与浏览器启动权上，AgentCore 托管场景两者皆无。若未来浏览器宿主换成自管（如自起容器跑 Chromium），此路线值得重估。
- **cloudflared quick tunnel**——缓。零账号是其残留优势，但零认证、官方点名不支持 SSE、`*.trycloudflare.com` 被恶意软件滥用致企业网常见封锁。TunnelProvider 口子已留：ngrok 门槛（authtoken/配额）被用户反馈证明是问题时再加它作第二实现。
- **AgentCore Browser VPC 模式**——口子，非本 ADR 范围：它解决「应用在 VPC 内（云上开发机）」而非「应用在本地」，且需自建 browser 资源（IaC 新资源、创建后网络模式不可改）。真实需求出现时单独立项。

## 边界与不变量

- 隧道仅在 `--expose-local` 显式给出时起——默认路径零新依赖、零出网变化。
- worker/core 对隧道无知（映射在组合根完成）；额外请求头经既有 env 注入面走，不新增协议事件。
- 本机关机/断网 = 隧道断 = run 以导航失败（AI 报错形态）告终——明示边界，submit 时提示，不做「断线重连恢复」（隧道进程崩溃同理；测试可重跑，不值守护复杂度）。
