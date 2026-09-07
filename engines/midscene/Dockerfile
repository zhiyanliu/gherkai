# Midscene worker 基底镜像（ADR 0037 决策 5「维护者 GHCR 基底 + 使用方定制层」；0024 Fargate 执行）。
# 内容 = 同版本 worker 包 + SDK 运行时 + 协议层，**零使用方内容**——使用方的确定性 step 由定制层
# （`FROM <基底>` + COPY steps/）叠上去，模板与推送注册全在 ADR 0038。
#
# 容器里跑的入口与 npm bin 同一个：`dist/bin.mjs`（ADR 0037 决策 3）——进程内注册 tsx loader + 裸
# specifier 的 resolve hook 后调 worker main。**本进程即 worker**，不套包装进程（EVENTS_FD 经 fd 继承，
# 中间多一层就把 fd3 吞了，ADR 0024 三通道）。job 走 S3、events 走 DDB、产物走 S3——全由 FargateEngine
# RunTask overrides 经 env 注入，worker fromEnv 判态。
#
# 当前形态 = 从**源码** COPY + `npm run build`（contributor 本地即可造）。改成 ADR 0037 决策 5 的
# 「两态」（CI 态按版本装已发行的 `@gherkai/worker-midscene`；本地态经 `--build-arg` 指向 `npm pack`
# 出的 tarball）属基底镜像 CI 那一步，推送/注册机制见 ADR 0038。
#
# 构建（从 engines/midscene/ 目录）——**必须 --platform linux/amd64**（Fargate task-def 默认 X86_64；arm Mac 不加
# 则 build 出 arm64、Fargate 启动期 exec format error 挂死，ADR 0033/0038 固定单架构）：
#   docker build --platform linux/amd64 -t <ecr>/gherkai-midscene-worker:latest .
FROM node:22-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 先装依赖（层缓存）。`npm ci` 照锁文件装——**含 devDependencies**（typescript 是 build 期需要的）。
# 注：运行时真需要的 SDK（@midscene/web / @playwright/test / playwright / bedrock-agentcore /
# signature-v4 / credential-providers / tsx）如今全在 **dependencies**（ADR 0037 决策 3：作为被消费的
# npm 包只会装 dependencies，留在 devDependencies 即崩——ADR 0033 记的「不能 --production」陷阱在
# 包化后变成必然）。故这里也不需要 `--production` 之类的旋钮，装全部即对。
COPY package.json package-lock.json ./
RUN npm ci

# **不装 chromium 二进制**：worker 连的是 AgentCore 云浏览器（chromium.connectOverCDP(wsUrl)，浏览器跑在云端），
# playwright 只作 CDP 客户端库、不 launch 本地 chromium——故只需 playwright 库（npm ci 已装），
# 不需 `playwright install chromium` 的二进制 + 系统库（省几百 MB）。真跑验证：connectOverCDP 不依赖本地二进制。

# 源码 + 编译配置 → tsc 出 dist/*.mjs（ADR 0037 决策 3：发布形态统一 ESM + tsc 产物，
# tsconfig **入库**；早先「无 tsconfig、靠 tsx 运行期扩展名重写」的形态随包化退役）。
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# region 不焊镜像：AWS_REGION 经 RunTask overrides 注入（agentcore-sigv4 的 getRegion 读它、全可配，ADR 0033/0016 决策 C）；
# 凭证走 task role（fromNodeProviderChain 解析 AWS_CONTAINER_CREDENTIALS_RELATIVE_URI）。
# 使用方 steps 由定制层 COPY 进来 + 注 GHERKAI_STEPS_DIR（ADR 0037 决策 4；模板在 ADR 0038）。
CMD ["node", "dist/bin.mjs"]
