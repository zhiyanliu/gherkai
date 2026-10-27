> 类型: 进度总纲

# 移动真机支持（1.5）：实施进度总纲

分支 `feat/v1.5-mobile-devices`。设计已定稿为 ADR 0048 到 0053（2026-10-15），spike 与方案总稿两份 journey 随之删除；本文只记实施阶段的现场：做到哪、下一步、documenting 清单。实施完成后删除。

## 现场

- 2026-10-15：ADR 0048 到 0053 写成并通过复审；CONTEXT.md 词表加目标、界面类型、应用别名、远程访问会话、驱动适配器、能力探测、确定性 step SDK 七条，旧词条三条改写；ADR 0019 / 0035 / 0036 的 Status 头标部分取代，0022 / 0024 / 0034 / 0042 / 0044 加互链。spike 脚本 `engines/midscene/spikes/06-devicefarm-appium.mts` 保留为真机能力探测的雏形，实施时演化成 `tools/` 下的真机重新探测工具。
- 2026-10-15（续）：定稿后的专家复审与 Codex 同僚复核发现 0051 的事件契约与收尾顺序、预算分层、隧道令牌载体、scenario 间复位、evidence 衔接、Job 形态六处要改。修订方案经六轮同僚复核达成共识、定稿前实测（边缘契约、桌面与四台真机的预热闭环、导航路线、网页上下文身份、Midscene 中止行为、webdriver 超时语义、会话释放、IAM 策略模拟）全部完成，结论已内联进各 ADR 的实测依据。
- 2026-10-15（续二）：按修订方案改写 ADR 完成：0051 整篇重写（决策 1 到 14，新增设备解析与命令守卫、result-unknown、隧道令牌换 cookie）；0024 / 0028 / 0034 / 0031 / 0049 / 0037 就地改写被反转句并加 Status 反向链；0035 / 0052 / 0048 / 0050 / 0053 / 0042 / 0019 / 0033 / 0027 / 0025 按条改写；CONTEXT.md 加设备请求、设备解析、获取预算三条，改隧道暴露、远程访问会话、能力探测、step 证据四条；`docs/internals/cli-json-contract.md` 加法扩展（会话列表、设备计量、新错误类别、`run_meta` 的格式版本与会话预热地址、Job 的 `target` 与 `device_request`、evidence 的设备键、`list-deterministic` 的目标两键、doctor 的设备两项）。修订方案 journey 吸收后删除。
- 2026-10-16：IAM 真实角色闭环 spike 完成（跳板机一次性脚本，在 `/tmp/iam-spike/`）：按 0033 权限表建 worker、CLI、部署方三个角色逐动作正反面核对，31 项与表一致；会话 Get / Stop 必须同授会话前缀与项目 ARN，原表只授前者、策略模拟器判允许是假阳性，0033 与 0051 已改并内联证据。
- 2026-10-16（续）：实施规划完成，每批的改动面、先写的护栏测试、真跑核对与易错点在 journey 0015。规划者把 ADR 落到代码时提出的设计缺口经逐条复核，12 条成立的已补进 ADR：0049 顶层 targets 的唯一性；0025 / 0048 的别名核对位置与 target.app 两形态；0053 的键集差集映射表、排除名单判据与云端 report-dir；0042 判定行；0052 接缝加 scenario 前核对；0035 / 0051 脱敏规则三条（实测 Appium 端点凭据在路径里、没有查询参数）；0051 / 0037 的 SSM 值失效与读失败处置。
- 2026-10-16（续二）：Codex 同僚第十轮复核实施规划，判「暂不通过实施就绪」，成立项已处置：0052 存活探测失败的归因与接缝统一；scenario 前核对从第二条 scenario 起调用（`scope_started` 后紧跟第一个 `scenario_started` 的保证不变），0051 写明会话年龄在 step 中途与 scenario 之间到期的两种事件序列；0051 背景改正 Appium 端点凭据位置；IAM 实测的「一字符会话名放宽授权」是探针错误（STS 要求会话名至少两个字符，assume 失败后凭据为空串、回落到执行机角色），已从 0051 删去并写明探针须在 assume 后核对身份。次序调整为 core 事件先于目标与 Job，worker 自检并入后者；journey 0015 按新次序重排并补红线测试。
- **owner 已定策略（2026-10-16）**：应用目标上含网址的 step，能用这个链接把 App 带到某一页就走 `mobile: deepLink` 进被测应用；做不到就 fail-fast，step 记 error、提示换种写法，不转 AI、不重试。
- **deepLink spike 结论（2026-10-16，spike 06 的 `deeplink` 场景四轮，Android 15 维基百科客户端 / Chrome，iOS 15.8、18.6、26.3 用注册了自定义 scheme 的未签名示例包与 Safari，共 10 个会话）**：
  - 始终带 package / bundleId。Android 不带时系统交给 Chrome、离开被测应用；iOS 15.8 不带时命令挂住（4 次 120 秒客户端超时，481 秒）。
  - Android 指定 package：能处理的链接 1 秒内打开目标页，后台与冷启动同样；应用不处理的主机或路径时命令报 `Activity not started, unable to resolve Intent`，不离开被测应用；自定义 scheme 可靠。
  - Android 的 `mobile: deepLink` 经 `adb shell am start -d` 传地址，驱动的转义不完整：含 `; ' ( ) | < >` 的地址命令出错，且 `|` 与 `;` 会让命令被截断后部分执行（`l?x=a|b` 报错同时打开了 `l?x=a`）；`+ % [ ] { } & = # ! * $ , ~` 与已百分号编码的字符逐字送达（以 Chrome 回显页的 location.href 与标准化原值比对）。`mobile: startActivity` 同样经 shell、同样出错。单引号包裹地址会把驱动加的反斜杠留在地址里，不可用。规则：发命令前按 RFC 3986 字符集校验，含 `; ' ( )` 四个驱动传不过的子分隔符或任何非 URI 字符即 step 记 error，消息给出百分号编码的改法；不做静默改写（`%28` 与 `(` 对应用的链接匹配未必等价）。
  - iOS 18.6 与 26.3 指定 bundleId：已注册 scheme 的链接 0.3 秒到前台，后台与冷启动同样；地址不经 shell，含括号、引号、`;`、`&` 的地址原样送达（Safari 回显核对）；Device Farm 重签后 Info.plist 里注册的 scheme 保留。**应用不处理的地址（未注册 scheme、无关 https）命令照样成功、应用照样到前台**，系统只负责送达，应用是否跳转外部不可观测。Universal Links 未测（需受控域名的关联文件，重签可能去掉 associated-domains 授权）。
  - iOS 15.8 带 bundleId 时 2.4 秒报 WebDriverAgent「The current Xcode SDK does not support opening of URLs with given application」，首次调用即可识别为设备不支持；Device Farm 公共设备上系统「地图」被禁止启动，不能当被测对象。
  - 由此的实现规则：设备不支持按首次调用的该报错识别、记 `capability_unavailable` 并缓存结论（只缓存能力否定，地址被拒与超时不进缓存）；Android「应用未处理该地址」记 `capability_unavailable`（处置是改写 step、重试不会变；Codex 第十二轮同意，并指出不能据此把 `engine_error` 说成「暗示可重试」，0051 已用它表示禁止补发的结果未知）；命令成功后核对前台包名或 bundleId 是被测应用，允许短暂轮询，不是即记 error。
- **owner 已定（2026-10-16）**：① 接受 iOS 上网址 step 的成功契约为「地址已送达、应用在前台」，应用忽略链接时由紧跟的落点核对判 failed，写进用户文档；② 应用目标上识别引号内任意 `scheme://`。两项连同 spike 结论已写进 0048 决策 7 与被拒方案、0052 决策 4 / 5 / 6 与实测依据、0051 决策 4 类别表与实测依据，0020 第 3 条与 0024「worker 派发」段加注，Status 头反向链。Codex 第十二轮对 ② 持不同意见（出现 scheme 不等于导航意图），owner 按作者建议定，理由记在 0048 被拒方案。
- 2026-10-26：导航规则修订（由 DeepLink 讨论引出，owner 定稿）：导航判据改为「Given / When 后整句是一个地址」（加不加引号都一样），不再用动词或「引号里出现网址」；导航成为注册表里唯一的内建条目，plan 与 list-deterministic 对它的标注与其它确定性 step 一致，这取代了 0020 原来「误伤就整体退回全 AI」的退路；Then 后只有地址按注册表的关键字声明规则记 error；曾内置的「页面地址匹配」step 退役，示范改进文档与 `steps/` 模板；术语定为 DeepLink（词表立条，深层链接进 Avoid 与退役词表）。落在 0020 第 2、3 条、0018、0022、0024、0036、0048 决策 7、0050 决策 1 与 CONTEXT。实施作为第 0 批、排在能力自述之前，是 1.4 行为的不兼容变更，进 CHANGELOG。
- 2026-10-26：第 0 批（导航规则与注册面关键字声明）已落地、两引擎桌面真跑核过、双轨复核闭合（Codex 第二十轮总判定设计已落到位）。第 1 批（能力自述增键）已落地、兼容性真跑核过、双轨复核闭合（Codex 第二十三轮总判定设计已落到位）；第 2 批（core 侧会话事件与终结函数）已落地、跳板机真跑核过、十一轮复核处置已落（第七到十一轮只是护栏确定性）、跳板机真跑（fail-fast 与超时）核过、双轨复核闭合（Codex 第三十六轮总判定设计已落到位）；第 3 批（目标模型、CLI 侧、两个 worker 的自检）已落地、本机真子进程与跳板机桌面真跑核过、双轨复核闭合（Codex 第三十八轮总判定设计已落到位）。**恢复现场**：第 4 批（B3：项目配置文件与提交侧，底稿在 journey 0015 第 4 节）五个子批（①配置模块与取值顺序、②设备请求解析与 plan 标注、③a definition 结构版本与缺戳例外、③b 协议侧结构版本与 targets 必有、④应用上传、⑤文档）全部落地并提交，S3 标签与刷新在跳板机真实桶上核过；双轨复核第一轮（workflow 七路窄核对加 Codex 第三十九轮）与第二轮（Codex 第四十轮，加 owner 拍定的结构重构：`__main__` 拆出 settings / submission / console、共享前置返回 Prepared 数据类，以及运行态的 run 级 message）处置已落并提交；第三轮（Codex 第四十一轮加五路 workflow：配置整数校验、读头违约出口、推进器产品语言消息、offloader 异常范围、local adapter 不丢 message、删兼容回落死函数与 Lambda 的 SSM 读权限）处置已落并提交；第四轮（Codex 第四十二轮加三路核验 workflow：消息限长、offloader 两处形态校验、云端读头同源、数字选项不收文本、SSM 反向测试作用域、兼容回落残留清零）处置已落并提交；第五轮（Codex 第四十三轮只剩两条测试护栏缺口）已补，双轨复核闭合（Codex 第四十四轮总判定设计已落到位）。第 5 批（B4：确定性 step 多句柄注册，底稿在 0015 第 5 节）三条实现期决定已与 owner 对齐并落 ADR 0050，code 与文档已落地提交；双轨复核第一轮（workflow 四路加 Codex 第四十五轮）处置已落并提交（plan 按目标标注走 AI、null 同构、webdriverio 进依赖、多行参数护栏）；第二轮（Codex 第四十六轮三条小发现：plan 自述失败的显式降级、internals 两处文案）已落；第三轮（Codex 第四十七轮一条文案）已落，双轨复核闭合（Codex 第四十八轮总判定设计已落到位）。第 6 批（B7 隧道改令牌换 cookie，底稿在 0015 第 6 节）code 三笔、文档两笔已落地，跳板机真跑核过（真 ngrok 接受 code 生成的策略、16 项矩阵、两个桌面 worker 的预热与两条失败路径、本机 submit 接力）；双轨复核第一轮（workflow 五路窄核对加 Codex 第四十九轮）处置已落并提交：边缘脚本只把 401 判 DENIED、校验路径放行改空响应体、地址识别改前瞻式逐处带边界、令牌不进 repr；Nova 预热响应停止信号、预热失败后的释放异常不回建连重试域；Midscene 预热失败不被 cleanupFailed 吞掉；三份脱敏显式空白字符类与 ASCII 大小写折叠（规则 ① 保留正向字符集、ADR 0035 改写成与 code 一致）；消息「已尝试 N 次」并由夹具三方同源；补策略按 YAML 解析、四处接线、两个 worker 失败路径的测试；校验路径空响应体已在真 ngrok 与两个桌面 worker 上复核。云端推进链待 owner 重新部署后端后再核。下一步是第 6 批的第二轮复核（Codex 第五十轮，brief 已拟在本机 /tmp/codex-review/brief50.md，核对范围是 4686c9b 之后的提交），闭合后进第 7 批（B8 部署侧，底稿在 0015 第 7 节）。跳板机源码树已同步到本分支工作树（rsync），`GHERKAI_WORKER_MIDSCENE_CMD` 要指向 dev 树的 `dist/bin.mjs`（全局装的是 1.4.9 的旧 worker）。次序（各批的依赖、红线测试与易错点在 journey 0015）：⓪ 导航规则与注册面关键字声明（两个 worker 的派发与注册表、删内建 step、plan 标注、契约页、skill 与用户指南、CHANGELOG；桌面直接受影响，自己发）→ ① 能力自述增键（两个 worker 只声明桌面网页）→ ② core 的会话事件、scope 级 error 与终结函数（对桌面是修复：负退出码、零 scenario、超时与中止同时成立的仲裁三处判定改变，写进 CHANGELOG）→ ③ core 的目标与 Job 形态，与两个 worker 建会话前自检同批发布（第一个能产出非桌面 Job 的批次；设备模块完成前，非桌面目标由本机预检与云端 worker 自检拦住）→ ④ 配置文件与提交侧（前移定义 SSM 键名、保留期常量与预热字段）→ ⑤ 确定性 step 注册面 → ⑥ 隧道令牌换 cookie（桌面先行）→ ⑦ 部署侧 → ⑧ Midscene 设备模块 → 文档与 skill。⑦ 可与 ⑧ 的准备并行。

## documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）

新页：

- user guide：`engines.md`（引擎能力矩阵，差集测试守）；设备主题页（`@device` 与 `@app` 写法、应用别名、应用目标上含网址的 step 走DeepLink：Android 要带可被应用处理的地址且 `; ' ( )` 须百分号编码，iOS 只保证送达、要紧跟落点核对，老设备记为不支持；设备选择与 `gherkai.toml` 的 `[devices]`、费用含取设备开销与口径以账单为准、限制：国内消费级应用线上包自退、iOS 26 的 DOM、Compose 无标识、数据驻留 us-west-2 与 400 天）。
- docs/internals：设备会话与 Appium 适配的机理解读一篇（权威指回 0051 / 0052）；`docs/internals/README.md` 登记新篇。`cli-json-contract.md` 的加法扩展已随 ADR 改写完成，实施时按真渲染器样例核对、补护栏夹具。

既有用户文档的触点（按页列，每页都要补 1.5 的新内容，不只是新页）：

- `writing-features.md`：「一个 step 的三种执行路径」里导航写法改为「Given / When 后整句一个地址」，说明 Then 后只有地址与句中提及地址的处理；「三个有语义的 tag」改为五个，加 `@device` / `@app` 的写法、组合规则与缺省；`@timeout` 加「缺省按目标、设备 scope 有下限」；「按引擎选写法」旁加「按目标选写法」（导航后落点核对按 Android 网页 / iOS 网页 / 应用分写，设备上 scenario 之间不复位、需要干净起点时在 Background 写一条调用 `app.restart()` 的自写 step，模板给出）；「写完先自检」提 plan 对目标的标注。
- `running-and-results.md`：常用选项加 `--android-device-arn` / `--ios-device-arn` / `--device-farm-project-arn` / `--app-bucket` / `--config`，以及 `--default-job-timeout` 对设备 scope 的语义（非正值不等于不超时、低于下限被拒）；退出码加 definition 格式版本不匹配与设备缺项的 2；「结果在哪」加会话列表、设备占用时长与 `device_session` 链接；explain 节加设备证据（失败的确定性与导航 step 也有证据、控件摘要、原始控件树）；「费用量级」加设备分钟。
- `getting-started.md`：doctor 自检加 `targets.<engine>` / `devices.project` / `devices.sessions` 三行的读法；「AWS 前置」加 Device Farm（只在 us-west-2、首次 deploy 建项目、权限指 cloud-backend）。
- `troubleshooting.md`：「各行查什么」加上述三行；隧道节改为令牌换 cookie 的故障形态（预热失败的消息与处置）；新增设备节：会话类错误与五个新错误类别（`precheck_failed` / `acquire_timeout` / `session_lost` / `release_failed` 为 job 级，`capability_unavailable` 为 step 级）。
- `configuration.md`：「配置生效的四个位置」改为五个（加 `gherkai.toml`：路径基准、`--config`、与选项和环境变量的优先序）；环境变量表加 `GHERKAI_ANDROID_DEVICE_ARN` / `GHERKAI_IOS_DEVICE_ARN` / `GHERKAI_DEVICE_FARM_PROJECT_ARN` / `GHERKAI_APP_BUCKET`；「由 gherkai 注入的环境变量」加 `GHERKAI_SESSION_WARMUP_URL`；「跨命令通用选项」加 `--config`。
- `cloud-backend.md`：「后端包含什么」加 Device Farm 项目；「首次部署」加项目的找回或建立与部署方无权限时的降级；「团队成员需要的最小云端权限」加三方权限表（提交者、部署方、worker）；「拆除与清理」加项目保留与手动删除命令；「费用」加设备分钟；「退出码与常见错误」加「部署未启用设备支持」；「版本与升级」加两条不受支持的组合：同一 report 目录混用 1.4 与 1.5 CLI 读写、开发版本混搭（0037 决策 7）。
- `local-app-testing.md`：「工作方式」加 worker 预热一步；「安全」改为令牌换 cookie（含 cookie 会到达被测应用访问日志的残余）；「限制」加设备浏览器依赖服务商不弹警告页、免费层策略规则数；「常见故障」加预热失败的三个分支。
- `writing-deterministic-steps.md`：「内建的确定性 step」一节删去，改为「`steps/` 模板」一节（地址精确核对的写法示例，设备网页目标带 `requires`）；「注册一条 step」加 `targets`、`requires` 与 `keywords`；「handler 拿到什么」加 webdriver 句柄与上下文七字段（含 `app.restart()`）；「`steps/` 模板」一节给出地址精确核对与重启应用两条示范；「在本机核对」加 `list-deterministic` 的 `targets` / `available_targets`；「两侧对称地写」加设备目标的对称要求；材料规则与验收定位（0050 决策 4）。
- `faq.md`：改写「它在什么浏览器里运行？能测移动端视口，或换成 Firefox、Safari 吗？」（真机经 Device Farm，Safari 即 iOS 真机 Safari）；加「测真机要多少钱、必须用 AWS 吗」。
- `docs/user-guide/README.md`：索引登记 `engines.md` 与设备主题页。
- 包入口页：`engines/midscene/README.md` 加设备支持一段（Appium、Device Farm）；`deploy_aws/README.md` 加 Device Farm 项目与权限一句；`cli/README.md` 与根 `README.md` 门面各一句。
- CHANGELOG 与 1.5 的 Release 正文。

其它读者的文档：

- skill：导航写法改为整句地址，「导航步后紧跟确定性落点核对」改为「紧跟一条落点核对；要精确核对地址就自写确定性 step」，`references/deterministic-steps.md` 给地址核对的模板；路由表加设备；`references/` 加设备写法；确定性 step 参考按 0050 决策 4 改（期望来自需求、材料只定位置、来源平铺、agent 开会话须项目约定、长流程拆步）；评测集加设备用例（写 `@device` 用例、写一条 webdriver step、处置 precheck_failed）；不出现「先 AI 后硬化」类流程暗示。
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
