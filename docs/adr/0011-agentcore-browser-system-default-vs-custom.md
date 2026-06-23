# AgentCore 浏览器层：spike 用系统默认，接内网真实系统时切自建 custom browser

AgentCore Browser 有两类，选哪类取决于被测系统在公网还是内网。

**两类（2026-06 本账号实查确认）**：
- **系统默认 `aws.browser.v1`**：AWS 内建沙箱，`status: READY`，开箱即用、零配置。`list-browsers` 返回空 `[]` 是正常的——它是系统级的，不计入"你创建的" browser。本会话已实测可 `start-browser-session` 起停。
- **自建 custom browser（`create-browser`）**：可定制 `--network-configuration`（必填，如放进 VPC 走私网）、`--recording`（会话录像存 S3）、`--certificates`（自定义证书，测私有 HTTPS）、`--enterprise-policies`、`--execution-role-arn`、`--browser-signing`。

**决定**：
- **spike 与公网用例用系统默认 `aws.browser.v1`**——维基百科等公网站点用不上任何自建能力，自建只会徒增 `network-configuration` 必填项的负担。
- **接入真实被测系统时，若系统在内网/VPC 或需自定义证书/审计录像，则切到自建 custom browser**，重点是 `--network-configuration`（VPC 私网可达）与可能的 `--certificates`。

**何时重议（留作未来需求的指针）**：一旦讨论"框架要测我们自己的内网系统"，回到本 ADR——大概率要从 `aws.browser.v1` 切到自建 browser 配 VPC，那时再定具体网络配置，另立或更新 ADR。与 [0007](./0007-programmatic-login-hitl-as-escape-hatch.md)（认证）一样，都属"接真实系统"阶段才落地的事。
