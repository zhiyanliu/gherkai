# syntax=docker/dockerfile:1
# Midscene worker **基底镜像**（ADR 0037 决策 5「维护者 GHCR 基底 + 使用方定制层」；0024 Fargate 执行；0033「2 镜像」）。
# 内容 = 同版本 worker 包（`@gherkai/worker-midscene`）+ SDK 运行时 + 协议层，**零使用方内容**——使用方的确定性
# step 由定制层（`FROM <基底>` + COPY steps/ + `GHERKAI_STEPS_DIR`）叠上去，模板与推送注册在 ADR 0038。
#
# **两态**（ADR 0037 决策 5）——同一份 Dockerfile，`--build-arg WORKER_SOURCE=` 选：
#   index（默认，CI 态）：按版本从 npm 装已发行的包（`npm install -g`，运行时依赖全在 dependencies——ADR 0037 决策 3）。
#                        `--build-arg WORKER_VERSION=X.Y.Z`（release.yml 传 tag 版本）。build context 任意（本态不 COPY）。
#   local（本地态）：    装 build context 里 `npm pack` 出的 tarball（contributor 在发行前验镜像）：
#     (cd engines/midscene && npm ci && npm run build && npm pack --pack-destination ../../dist)
#     docker build --platform linux/amd64 -f engines/midscene/Dockerfile \
#       --build-arg WORKER_SOURCE=local --build-arg WORKER_TARBALL=gherkai-worker-midscene-<ver>.tgz \
#       -t gherkai-worker-midscene:dev dist/         # ← context = 放 tarball 的目录
# **必须 `--platform linux/amd64`**：Fargate task-def 固定 X86_64（ARM64 是被拒方案，ADR 0038）；arm Mac 不加则 build 出
# arm64、Fargate 启动期 exec format error 挂死（ADR 0033）。
#
# 容器入口与 npm bin 同一个：`gherkai-worker-midscene`（→ `dist/bin.mjs`，ADR 0037 决策 3）——bin 是带 shebang 的
# 符号链接、内核直接 exec node，**本进程即 worker**、不套包装进程（EVENTS_FD 经 fd 继承，中间多一层就把 fd3 吞了，
# ADR 0024 三通道）。job 走 S3、events 走 DDB、产物走 S3——全由 FargateEngine RunTask overrides 经 env 注入，worker fromEnv 判态。
ARG WORKER_SOURCE=index

FROM node:22-slim AS base
ENV DEBIAN_FRONTEND=noninteractive
# /app 留给定制层放 steps/（基底不预置 GHERKAI_STEPS_DIR、不猜路径，ADR 0037 决策 4/5）
WORKDIR /app
# **不装 chromium 二进制**：worker 连的是 AgentCore 云浏览器（chromium.connectOverCDP(wsUrl)，浏览器跑在云端），
# playwright 只作 CDP 客户端库、不 launch 本地 chromium——不需 `playwright install chromium` 的二进制 + 系统库。

# ---- index 态：已发行包（CI / 使用方自建同版本基底）----
FROM base AS worker-index
ARG WORKER_VERSION
RUN test -n "${WORKER_VERSION}" || { echo "index 态需要 --build-arg WORKER_VERSION=<X.Y.Z>（或改 WORKER_SOURCE=local 喂 tarball）" >&2; exit 1; } \
 && npm install -g "@gherkai/worker-midscene@${WORKER_VERSION}" && npm cache clean --force

# ---- local 态：context 里的 tarball（发行前验镜像）----
FROM base AS worker-local
ARG WORKER_TARBALL
COPY ${WORKER_TARBALL} /tmp/worker.tgz
RUN npm install -g /tmp/worker.tgz && rm /tmp/worker.tgz && npm cache clean --force

FROM worker-${WORKER_SOURCE} AS final
# region 不焊镜像：AWS_REGION 经 RunTask overrides 注入（agentcore-sigv4 的 getRegion 读它、全可配，ADR 0033/0016 决策 C）；
# 凭证走 task role（fromNodeProviderChain 解析 AWS_CONTAINER_CREDENTIALS_RELATIVE_URI）。
CMD ["gherkai-worker-midscene"]
