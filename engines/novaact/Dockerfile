# Nova Act worker 容器镜像（ADR 0033「2 镜像」/ 0024 Fargate 执行）。
# Fargate 上跑 `python -m gherkai_worker_novaact`（包入口，ADR 0037 决策 3）：job 走 S3（JOB_S3_URI）、
# events 走 DDB（EVENTS_DDB_TABLE）、产物走 S3（ARTIFACT_S3_*）——全由 FargateEngine RunTask overrides
# 经 env 注入，worker from_env 判态。
# 镜像由 CI/手动 build & push 到 ECR（{prefix}novaact-worker）；CDK 只建 ECR repo、不 build（ADR 0033）。
#
# **本文件是「源码直 COPY」形态**（当前唯一可行形态）：包版本由 uv-dynamic-versioning 从 git tag 算，
# 容器内没有 git 元数据 → 在镜像里 `pip install .` 必失败。基于 wheel 的两态 Dockerfile（CI 态按版本从
# PyPI 装 / 本地态经 --build-arg 指向本地 `uv build` 产物）属基底镜像交付，两态设计见 ADR 0037 决策 5、推送/注册见 ADR 0038。
#
# 构建（从 engines/novaact/ 目录）——**必须 --platform linux/amd64**（Fargate task-def 默认 X86_64；arm Mac 不加
# 则 build 出 arm64、Fargate 启动期 exec format error 挂死，ADR 0033）：
#   docker build --platform linux/amd64 -t <ecr>/gherkai-novaact-worker:latest .
FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 装依赖（独立层、利用层缓存）。用 pip（容器内不必 uv）。**两个依赖都字面写在这里**：不 COPY+读
# pyproject/uv.lock——本 worker 运行时不解析它们，且下行 pip 不消费它们，COPY 进来是死层、只会因编辑
# pyproject 无谓 bust 缓存。**版本下限须与 pyproject.toml 的 dependencies 一致（双端手动同步）**。
# boto3 显式装：worker 自己直接 import 它（event_sink/job_source/artifact_upload/workflow_setup 的 AWS 态），
# 不靠 nova-act 传递依赖捎带（ADR 0037 决策 2c：直接 import 就直接声明）。
RUN pip install --upgrade pip && pip install "nova-act>=3.4.187.0" "boto3>=1.34"

# **不装 chromium 二进制**：worker 连的是 AgentCore 云浏览器（cdp_session→connectOverCDP，浏览器跑在云端），
# playwright 只作 CDP 客户端库、不 launch 本地 chromium——故只需 playwright 库（上面 nova-act 已拉入），
# 不需 `playwright install chromium` 的二进制 + 系统库（省几百 MB）。真跑验证：connectOverCDP 连云浏览器不依赖本地二进制。

# worker 包整体 COPY（协议/派发 + lib 的 DDB/S3 两态 + 确定性注册表与内建脚手架）。
# **零使用方内容**（ADR 0037 决策 5：这是基底镜像的定义）：使用方的 `steps/` 由定制层 COPY 进来、
# 并置 `GHERKAI_STEPS_DIR` 指向它（模板见 ADR 0038）；基底不预置该 env、不猜路径。
COPY gherkai_worker_novaact/ ./gherkai_worker_novaact/

# 包按 import 名住在 /app 下、未经 pip 安装 → PYTHONPATH 让 `python -m gherkai_worker_novaact` 找得到它。
ENV PYTHONPATH=/app

# 三通道分离（ADR 0024）：事件走 DDB（EventSink DDB 态）、诊断走 stderr、SDK 噪声走 stdout——容器日志（awslogs）
# 抓 stdout/stderr 供调试，事件不依赖日志（走 DDB）。
# region/凭证不焊镜像：AWS_REGION 经 RunTask overrides 注入、凭证走 task role（ADR 0033 决策 C）。
# 入口 = 包的 `__main__`（**不加包装进程**：EVENTS_FD 经 pass_fds 继承，包装层会吞 fd3，ADR 0024/0037 决策 3）。
CMD ["python", "-m", "gherkai_worker_novaact"]
