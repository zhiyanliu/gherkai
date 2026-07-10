# Nova Act worker 容器镜像（ADR 0033「2 镜像」/ 0024 Fargate 执行）。
# Fargate 上跑 worker/run_scope.py：job 走 S3（JOB_S3_URI）、events 走 DDB（EVENTS_DDB_TABLE）、
# 产物走 S3（ARTIFACT_S3_*）——全由 FargateEngine RunTask overrides 经 env 注入，worker from_env 判态。
# 镜像由 CI/手动 build & push 到 ECR（{prefix}novaact-worker）；CDK 只建 ECR repo、不 build（ADR 0033）。
#
# 构建（从 engines/novaact/ 目录）——**必须 --platform linux/amd64**（Fargate task-def 默认 X86_64；arm Mac 不加
# 则 build 出 arm64、Fargate 启动期 exec format error 挂死，ADR 0033）：
#   docker build --platform linux/amd64 -t <ecr>/gherkai-novaact-worker:latest .
FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 装依赖（独立层、利用层缓存）。用 pip（容器内不必 uv；nova-act 拉 boto3/bedrock-agentcore/playwright 库）。
# 直接字面装 nova-act（不 COPY+读 pyproject/uv.lock——本 worker 运行时不解析它们，且下行 pip 不消费它们，
# COPY 进来是死层、只会因编辑 pyproject 无谓 bust 缓存）。版本下限须与 pyproject.toml 的 nova-act 约束一致（双端手动同步）。
RUN pip install --upgrade pip && pip install "nova-act>=3.4.187.0"

# **不装 chromium 二进制**：worker 连的是 AgentCore 云浏览器（cdp_session→connectOverCDP，浏览器跑在云端），
# playwright 只作 CDP 客户端库、不 launch 本地 chromium——故只需 playwright 库（上面 nova-act 已拉入），
# 不需 `playwright install chromium` 的二进制 + 系统库（省几百 MB）。真跑验证：connectOverCDP 连云浏览器不依赖本地二进制。

# worker 代码 + lib（event_sink/job_source/artifact_upload 的 DDB/S3 态）+ 确定性注册。
COPY lib/ ./lib/
COPY worker/ ./worker/

# 三通道分离（ADR 0024）：事件走 DDB（EventSink DDB 态）、诊断走 stderr、SDK 噪声走 stdout——容器日志（awslogs）
# 抓 stdout/stderr 供调试，事件不依赖日志（走 DDB）。
# region/凭证不焊镜像：AWS_REGION 经 RunTask overrides 注入、凭证走 task role（ADR 0033 决策 C）。
CMD ["python", "worker/run_scope.py"]
