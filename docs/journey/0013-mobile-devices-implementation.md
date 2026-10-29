> 类型: 进度总纲

# 移动真机支持（1.5）：实施进度总纲

分支 `feat/v1.5-mobile-devices`。设计已定稿为 ADR 0048 到 0053（2026-10-15），spike 与方案总稿两份 journey 随之删除；本文只记实施阶段的现场：做到哪、下一步、documenting 清单。实施完成后删除。

## 恢复现场

第 0 到 6 批已闭合。下一步：第 7 批（B8 部署侧，底稿在 0015 第 7 节）。

云端验证已做（owner 部署了 dev 版本后端、两引擎 dev 镜像以 variant base 推上）：`doctor --backend cloud` 全绿、两引擎直连 cloud run passed（definition 结构版本 1、带 cli_version、无 run 级消息、会话 id 为 AgentCore 格式）、两引擎 `submit --backend cloud --expose-local` passed（推进器读回预热地址进 RunTask、Fargate worker 预热就绪、上游收到带 cookie 的请求、隧道终态即拆、无会话残留）；证据已内联进 ADR 0051 实测依据。应用上传的云端路径要等第 7 批（B8 部署侧的 Device Farm 项目与权限）才能在真云上走通，设备目标的执行还要等第 8 批（B6 设备模块）。

跳板机要点：源码树已同步到本分支工作树（rsync）；`GHERKAI_WORKER_MIDSCENE_CMD` 要指向 dev 树的 `dist/bin.mjs`（全局装的是 1.4.9 的旧 worker）。

## 现场

- 设计期结论已全部内联进 ADR 0048 到 0053、按条改写的既有 ADR（0018、0019、0020、0022、0024、0025、0027、0028、0031、0033 到 0037、0042、0044，Status 头带反向链）与 CONTEXT.md。
- 已闭合的批次（各批的复核过程在 commit 历史里）：
  - 第 0 批（B0：导航规则与注册面关键字声明）已落地、真跑核过、双轨复核闭合。
  - 第 1 批（B1：能力自述增键）已落地、真跑核过、双轨复核闭合。
  - 第 2 批（B5：core 侧会话事件与终结函数）已落地、真跑核过、双轨复核闭合。
  - 第 3 批（B2：目标模型、CLI 侧、两个 worker 的自检）已落地、真跑核过、双轨复核闭合。
  - 第 4 批（B3：项目配置文件与提交侧）已落地、真跑核过、双轨复核闭合。
  - 第 5 批（B4：确定性 step 多句柄注册）已落地、真 worker 读 `features/steps` 核过自述、双轨复核闭合。
  - 第 6 批（B7：隧道改令牌换 cookie）已落地、真跑核过、双轨复核闭合。
- 次序（各批的依赖、红线测试与易错点在 journey 0015）：⓪ 导航规则与注册面关键字声明（两个 worker 的派发与注册表、删内建 step、plan 标注、契约页、skill 与用户指南、CHANGELOG；桌面直接受影响，自己发）→ ① 能力自述增键（两个 worker 只声明桌面网页）→ ② core 的会话事件、scope 级 error 与终结函数（对桌面是修复：负退出码、零 scenario、超时与中止同时成立的仲裁三处判定改变，写进 CHANGELOG）→ ③ core 的目标与 Job 形态，与两个 worker 建会话前自检同批发布（第一个能产出非桌面 Job 的批次；设备模块完成前，非桌面目标由本机预检与云端 worker 自检拦住）→ ④ 配置文件与提交侧（前移定义 SSM 键名、保留期常量与预热字段）→ ⑤ 确定性 step 注册面 → ⑥ 隧道令牌换 cookie（桌面先行）→ ⑦ 部署侧 → ⑧ Midscene 设备模块 → 文档与 skill。⑦ 可与 ⑧ 的准备并行。

## 遗留项

- 两侧错误文本归一化的分行与空白规则不完全对称（Python 的 splitlines / split 认 U+2028 等 Unicode 行列分隔符与 Unicode 空白，Midscene 只按 CR / LF 分行、按 JS 的空白折叠），`A\u2028B` 一侧得 `A`、一侧得 `A B`。既有的低优先级差异，属 code 层、不必进 ADR，可交 code-health 复盘。
- 契约页护栏按全页扁平键名核对（`cli/tests/test_cli_json_contract.py` 的 `_leaf_keys`），删掉 list-deterministic 节的 keywords 说明仍能过（既有设计限制）。
- 评测集第 1 条（`skills/gherkai-evals/evals.json`）以「打开 https://example.com/ 看到大标题 Example Domain、点 More information」为需求，前提已与该页现状不符（页面已无「Example Domain」大标题）；评测只做 plan 不真跑、暂未改。
- 策略文件不删除的前提仍需真实核实：ngrok agent 在隧道存活期是否会重读策略文件（`runtime/gherkai_runtime/tunnel.py` 的 `NgrokTunnel.start` 注释已点明，只靠单测证明不了）。
- 待真跑核实：Midscene 桌面 worker 在 AgentCore 浏览器上预热后，被测应用用 history.pushState 不再抛 SecurityError；故意给错令牌时，run 的最终退出码与 explain 的呈现符合预期（READY、cookie 到达上游、错令牌归 precheck_failed、worker 退出码 0 已核）。
- 待真跑核实：同步 run 宿主下预热地址端到端到达 worker，且宿主 shell 里 export 的同名值不会越过 definition（本机 submit 的 per-run 进程与 status --wait 接力者、云端 submit 的推进链已核）。
- **ADR 0010 基准重测**：两个 spike 的动作指令措辞与计时边界不同、token 用量从未采集（owner 裁定补齐后重测，不冻结为历史快照）。做法：对齐 `engines/midscene/spikes/03-midscene-grounding.ts` 与 `engines/novaact/spikes/wikipedia_benchmark.py` 的提示词与计时范围、给两侧 metrics 补用量采集、在跳板机重测、替换 0010 的对比表并补成本行。时机：第 7 批 B8 闭合后、1.5 收尾（code-health 复盘）前；约一到两小时，不依赖部署。
- **演示材料随 1.5 升级与增补**（`docs/presentations/value-method/`）：1.5 收尾后按 `tools/presentations/production.md` 的流程改口播、重配音、更新 manifest（含口播稿与讲者备注的 SHA-256）。随下一版一并改的角色词：口播稿与讲者备注里「编程 agent」改「AI agent」、「QA，也就是测试工程师」改「QA」（ADR 0040 的正名；v12 的定稿原文按文档护栏的定稿豁免规则不回溯改写）。
- **评测 fixture 重录**：`skills/gherkai-evals/fixtures/` 下 wiki-search / job-failure / nova-zh 三个录制型 fixture 的 run_meta.json 缺 schema_version，当前 CLI 只认第 1 版；按 ADR 0043 决策七的流程用当前 CLI 重录并完整物化，不手工补键。
- **IAM 收窄的云端验证**：Nova 会话改为干净起步后，两个 task role 去掉了 browser profile 四个动作与 `browser-profile/*` 资源（ADR 0033 IAM 表），尚未经真部署验证。B8 部署后两引擎各真跑一条云端 run，确认无 AccessDenied；通过后把 0033「上表动作集由真跑逐个暴露」条里「尚未经真部署后的 task role 端到端验证」改为已验证的表述。
- **历史 browser profile 残留**：此前用过 Nova 的账户与 region 各有一个名为 default 的服务端 browser profile 存着历史状态；worker 已不再读写，task role 收窄后也无权删除。是否手动清理由 owner 决定；开发机上的本地缓存 `~/.nova-act/agentcore-profiles/default.json` 可直接删。
- **webdriverio 精确锁定**：第 8 批 B6 设备模块落地时把 `engines/midscene/package.json` 的 `webdriverio` 从范围版本改为精确版本、重算锁文件、改 `engines/midscene/DEVELOPMENT.md` 的锁定清单（ADR 0052 决策 7 已记此待办）。
- **可选的用户文档补句**：`docs/user-guide/running-and-results.md`、`docs/user-guide/cloud-backend.md`、skill 正文里「`--backend cloud` 给 `--grace` 以退出码 2 结束」仍成立，可各补一句「写在 gherkai.toml 里的 grace 在云端只提示、不生效」（配置页已写）。

## documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）

新页：

- user guide：`engines.md`（引擎能力矩阵，差集测试守；矩阵的句柄列随 Midscene 自述带设备目标时更新）；设备主题页（`@device` 与 `@app` 写法、应用别名、应用目标上含网址的 step 走DeepLink：Android 要带可被应用处理的地址且 `; ' ( )` 须百分号编码，iOS 只保证送达、要紧跟落点核对，老设备记为不支持；设备选择与 `gherkai.toml` 的 `[devices]`、费用含取设备开销与口径以账单为准、限制：国内消费级应用线上包自退、iOS 26 的 DOM、Compose 无标识、数据驻留 us-west-2 与 400 天）。
- docs/internals：设备会话与 Appium 适配的机理解读一篇（权威指回 0051 / 0052）；`docs/internals/README.md` 登记新篇。`cli-json-contract.md` 的加法扩展已随 ADR 改写完成，实施时按真渲染器样例核对、补护栏夹具。

既有用户文档的触点（按页列，每页都要补 1.5 的新内容，不只是新页）：

- `writing-features.md`：「一个 step 的三种执行路径」里导航写法改为「Given / When 后整句一个地址」，说明 Then 后只有地址与句中提及地址的处理；「三个有语义的 tag」改为五个，加 `@device` / `@app` 的写法、组合规则与缺省；`@timeout` 加「缺省按目标、设备 scope 有下限」；「按引擎选写法」旁加「按目标选写法」（导航后落点核对按 Android 网页 / iOS 网页 / 应用分写，设备上 scenario 之间不复位、需要干净起点时在 Background 写一条调用 `app.restart()` 的自写 step，模板给出）；「写完先自检」提 plan 对目标的标注。
- `running-and-results.md`：常用选项加 `--android-device-arn` / `--ios-device-arn` / `--device-farm-project-arn` / `--app-bucket` / `--config`，以及 `--default-job-timeout` 对设备 scope 的语义（非正值不等于不超时、低于下限被拒）；退出码加 definition 格式版本不匹配与设备缺项的 2；「结果在哪」加会话列表、设备占用时长与 `device_session` 链接；explain 节加设备证据（失败的确定性与导航 step 也有证据、控件摘要、原始控件树）；「费用量级」加设备分钟。
- `getting-started.md`：doctor 自检加 `targets.<engine>` / `devices.project` / `devices.sessions` 三行的读法；「AWS 前置」加 Device Farm（只在 us-west-2、首次 deploy 建项目、权限指 cloud-backend）。
- `troubleshooting.md`：「各行查什么」加上述三行；隧道节改为令牌换 cookie 的故障形态（预热失败的消息与处置）；新增设备节：会话类错误与五个新错误类别（`precheck_failed` / `acquire_timeout` / `session_lost` / `release_failed` 为 job 级，`capability_unavailable` 为 step 级）。
- `configuration.md`：「配置生效的四个位置」改为五个（加 `gherkai.toml`：路径基准、`--config`、与选项和环境变量的优先序）；环境变量表加 `GHERKAI_ANDROID_DEVICE_ARN` / `GHERKAI_IOS_DEVICE_ARN` / `GHERKAI_DEVICE_FARM_PROJECT_ARN` / `GHERKAI_APP_BUCKET`；「由 gherkai 注入的环境变量」加 `GHERKAI_SESSION_WARMUP_URL`；「跨命令通用选项」加 `--config`。
- `cloud-backend.md`：「后端包含什么」加 Device Farm 项目；「首次部署」加项目的找回或建立与部署方无权限时的降级；「团队成员需要的最小云端权限」加三方权限表（提交者、部署方、worker）；「拆除与清理」加项目保留与手动删除命令；「费用」加设备分钟；「退出码与常见错误」加「部署未启用设备支持」；「版本与升级」加两条不受支持的组合：同一 report 目录混用 1.4 与 1.5 CLI 读写、开发版本混搭（0037 决策 7）。
- `local-app-testing.md`：「工作方式」加 worker 预热一步；「安全」改为令牌换 cookie（含 cookie 会到达被测应用访问日志的残余）；「限制」加设备浏览器依赖服务商不弹警告页、免费层策略规则数；「常见故障」加预热失败的三个分支。
- `writing-deterministic-steps.md`：「内建的确定性 step」一节删去，改为「`steps/` 模板」一节（地址精确核对的写法示例，设备网页目标带 `requires`）；「注册一条 step」加 `targets`、`requires` 与 `keywords`；「handler 拿到什么」加 webdriver 句柄与上下文七字段（含 `app.restart()`）；「`steps/` 模板」一节给出地址精确核对与重启应用两条示范；「在本机核对」加 `list-deterministic` 的 `targets` / `available_targets`；「两侧对称地写」加设备目标的对称要求；材料规则与验收定位（0050 决策 4）；测试分层（离线 WebdriverIO 加 Chrome for Testing、缓存目录，0050 决策 3）与写作方法六条（0050 决策 4），设备路径真能运行后再写。
- `faq.md`：改写「它在什么浏览器里运行？能测移动端视口，或换成 Firefox、Safari 吗？」（真机经 Device Farm，Safari 即 iOS 真机 Safari）；加「测真机要多少钱、必须用 AWS 吗」。
- `docs/user-guide/README.md`：索引登记 `engines.md` 与设备主题页。
- 包入口页：`engines/midscene/README.md` 加设备支持一段（Appium、Device Farm）；`deploy_aws/README.md` 加 Device Farm 项目与权限一句；`cli/README.md` 与根 `README.md` 门面各一句。
- CHANGELOG 与 1.5 的 Release 正文。

其它读者的文档：

- skill：导航写法改为整句地址，「导航步后紧跟确定性落点核对」改为「紧跟一条落点核对；要精确核对地址就自写确定性 step」，`references/deterministic-steps.md` 给地址核对的模板；路由表加设备；`references/` 加设备写法；确定性 step 参考按 0050 决策 4 改（期望来自需求、材料只定位置、来源平铺、agent 开会话须项目约定、长流程拆步）；评测集加设备用例（写 `@device` 用例、写一条 webdriver step、处置 precheck_failed）；`--config` 与 `gherkai.toml` 的说明；不出现「先 AI 后硬化」类流程暗示。
- CONTRIBUTING：发版后验证项加真机验收矩阵；`tools/` 的真机重新探测工具使用方法。

## 实施期要核的点（ADR 已定、实施时顺手验证）

- 0051 决策 13 的边缘策略由 gherkai 的隧道实现生成后，在三种浏览器上各走一次（设计阶段已用手写策略文件验过）。
- 0051 决策 11 的脱敏：一次故意建连失败的真机执行，核报错文本里的签名与令牌已被盖住。
- 0049 决策 8 的差集测试在 CI 里如何取得两个 worker 的能力自述（直接调起 `--capabilities`，或各 worker 自测同步维护的快照）。
- 会话摘要投影的护栏测试（同步与推进器两条路径）：`attempted` 的 `session_opened` 不擦掉已记的真实 ARN；终结阶段交叠或重入时 `attempted` 只发一对、真实会话按 ARN 去重；`device_observed_s` 与 `device_observed_missing` 都不计 `attempted` 项，人读展示把它们标为「结果未知的创建尝试」。
- 0034 终结真值表的双路径对拍测试：事件矩阵在设计阶段的行之外加「先判 abort、收尾期间 deadline 才到仍为 abort」与「无 ARN 的未知 Create 加取消」两行。
- 0052 决策 6 命令守卫的实测：对缓存的元素句柄、提取出的方法与晚到回调的覆盖；旧执行的晚到命令与事件在下一 scenario 开始之后的表现。
- iOS 26 上「探测超时 → 恢复原生上下文 → deepLink → READY」整链路。
- 预热验收的三个失败分支实际触发：拒收 cookie、校验 401、请求失败。
- 计费：起点、排队是否计费、`deviceMinutes` 是否实时累计；claim 到进入设备解析的启动开销；真实设备 scope 的执行耗时分布（校准 0051 决策 2 的 900 秒与 180 秒）。
- 控件摘要与 page source 的采集耗时与字节量。
- Device Farm 接口形态：`ListDevices` 的 os 字段格式与 formFactor 取值；UNMETERED 无槽位时 Create 的行为；项目名唯一性与按名找回；`ListRemoteAccessSessions` 返回体是否带签名端点。
- S3 同键 CopyObject 刷新后过期是否重新计时。
- CloudTrail 的 RunTask 记录是否含 `containerOverrides`（0035 决策 5 的不脱敏清单依据）。
