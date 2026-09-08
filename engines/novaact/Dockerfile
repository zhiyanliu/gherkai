# syntax=docker/dockerfile:1
# Nova Act worker **基底镜像**（ADR 0037 决策 5「维护者 GHCR 基底 + 使用方定制层」；0024 Fargate 执行；0033「2 镜像」）。
# 内容 = 同版本 worker 包（`gherkai-worker-novaact`）+ SDK 运行时 + 协议层，**零使用方内容**——使用方的确定性
# step 由定制层（`FROM <基底>` + COPY steps/ + `GHERKAI_STEPS_DIR`）叠上去，模板与推送注册在 ADR 0038。
#
# **两态**（ADR 0037 决策 5）——同一份 Dockerfile，`--build-arg WORKER_SOURCE=` 选：
#   index（默认，CI 态）：按版本从 PyPI 装已发行的包。`--build-arg WORKER_VERSION=X.Y.Z`（release.yml 传 tag 版本；
#                        依赖随包元数据解析，本文件不复写下限——单一真源在 pyproject）。build context 任意（本态不 COPY）。
#   local（本地态）：    装 build context 里的 wheel（contributor 在发行前验镜像；容器内无 git 元数据、`pip install .`
#                        算不出版本，故先 `uv build` 再喂 wheel）：
#     uv build --package gherkai-worker-novaact --out-dir dist
#     docker build --platform linux/amd64 -f engines/novaact/Dockerfile \
#       --build-arg WORKER_SOURCE=local --build-arg WORKER_WHEEL=gherkai_worker_novaact-<ver>-py3-none-any.whl \
#       -t gherkai-worker-novaact:dev dist/          # ← context = 放 wheel 的目录
# **必须 `--platform linux/amd64`**：Fargate task-def 固定 X86_64（ARM64 是被拒方案，ADR 0038）；arm Mac 不加则 build 出
# arm64、Fargate 启动期 exec format error 挂死（ADR 0033）。
#
# Fargate 上跑 `python -m gherkai_worker_novaact`（包入口，ADR 0037 决策 3）：job 走 S3（JOB_S3_URI）、events 走 DDB
# （EVENTS_DDB_TABLE）、产物走 S3（ARTIFACT_S3_*）——全由 FargateEngine RunTask overrides 经 env 注入，worker from_env 判态。
ARG WORKER_SOURCE=index

FROM python:3.13-slim AS base
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
# /app 留给定制层放 steps/（基底不预置 GHERKAI_STEPS_DIR、不猜路径，ADR 0037 决策 4/5）
WORKDIR /app
RUN pip install --upgrade pip
# **不装 chromium 二进制**：worker 连的是 AgentCore 云浏览器（cdp_session→connectOverCDP，浏览器跑在云端），
# playwright 只作 CDP 客户端库、不 launch 本地 chromium——故只需 playwright 库（nova-act 依赖拉入），
# 不需 `playwright install chromium` 的二进制 + 系统库（省几百 MB）。真跑验证：connectOverCDP 连云浏览器不依赖本地二进制。

# ---- index 态：已发行包（CI / 使用方自建同版本基底）----
FROM base AS worker-index
ARG WORKER_VERSION
RUN test -n "${WORKER_VERSION}" || { echo "index 态需要 --build-arg WORKER_VERSION=<X.Y.Z>（或改 WORKER_SOURCE=local 喂 wheel）" >&2; exit 1; } \
 && pip install "gherkai-worker-novaact==${WORKER_VERSION}"

# ---- local 态：context 里的 wheel（发行前验镜像）----
FROM base AS worker-local
ARG WORKER_WHEEL
# 保留原文件名：pip 从 wheel 文件名解析发行名/版本/tag，改名（如 worker.whl）会被拒「Invalid wheel filename」（真 build 踩过）
COPY ${WORKER_WHEEL} /tmp/wheel/
RUN pip install /tmp/wheel/*.whl && rm -rf /tmp/wheel

FROM worker-${WORKER_SOURCE} AS final
# 三通道分离（ADR 0024）：事件走 DDB（EventSink DDB 态）、诊断走 stderr、SDK 噪声走 stdout——容器日志（awslogs）
# 抓 stdout/stderr 供调试，事件不依赖日志（走 DDB）。
# region/凭证不焊镜像：AWS_REGION 经 RunTask overrides 注入、凭证走 task role（ADR 0033 决策 C）。
# 入口 = 包的 `__main__`（**不加包装进程**：EVENTS_FD 经 pass_fds 继承，包装层会吞 fd3，ADR 0024/0037 决策 3）。
CMD ["python", "-m", "gherkai_worker_novaact"]
