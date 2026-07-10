# Midscene worker 容器镜像（ADR 0033「2 镜像」/ 0024 Fargate 执行）。
# Fargate 上跑 worker/run-scope.ts（node --import tsx）：job 走 S3、events 走 DDB、产物走 S3——
# 全由 FargateEngine RunTask overrides 经 env 注入，worker fromEnv 判态。
# 镜像由 CI/手动 build & push 到 ECR（{prefix}midscene-worker）；CDK 只建 ECR repo、不 build（ADR 0033）。
#
# 构建（从 engines/midscene/ 目录）——**必须 --platform linux/amd64**（Fargate task-def 默认 X86_64；arm Mac 不加
# 则 build 出 arm64、Fargate 启动期 exec format error 挂死，ADR 0033）：
#   docker build --platform linux/amd64 -t <ecr>/gherkai-midscene-worker:latest .
#
# **关键（ADR 0033 构建陷阱）**：运行时真需要的 SDK（@midscene/web / playwright / bedrock-agentcore /
# signature-v4 / credential-providers / tsx）大多在 devDependencies——**绝不能 npm install --production**
# （会漏装、worker import 即崩）。此处 `npm install` 装全部依赖。
FROM node:22-slim

ENV DEBIAN_FRONTEND=noninteractive \
    NODE_ENV=development

WORKDIR /app

# 先装依赖（层缓存）。装全部（含 devDeps 里的运行时依赖）——不加 --production。
COPY package.json package-lock.json* ./
RUN npm install

# **不装 chromium 二进制**：worker 连的是 AgentCore 云浏览器（chromium.connectOverCDP(wsUrl)，浏览器跑在云端），
# playwright 只作 CDP 客户端库、不 launch 本地 chromium——故只需 playwright 库（npm install 已装），
# 不需 `playwright install chromium` 的二进制 + 系统库（省几百 MB）。真跑验证：connectOverCDP 不依赖本地二进制。

# worker 代码 + lib（event-sink/job-source/artifact-upload 的 DDB/S3 态 + agentcore-sigv4）。
COPY lib/ ./lib/
COPY worker/ ./worker/
COPY tsconfig*.json ./

# region 不焊镜像：AWS_REGION 经 RunTask overrides 注入（agentcore-sigv4 的 getRegion 读它、全可配，ADR 0033/0016 决策 C）；
# 凭证走 task role（fromNodeProviderChain 解析 AWS_CONTAINER_CREDENTIALS_RELATIVE_URI）。
# 用 --import tsx（非 tsx 二进制、非子 node）：loader 加载进同一进程，保 fd/env 继承一致（与 subprocess 入口对称）。
CMD ["node", "--import", "tsx", "worker/run-scope.ts"]
