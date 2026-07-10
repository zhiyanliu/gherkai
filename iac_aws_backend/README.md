# iac_aws_backend

`--backend cloud` 需要的全部 AWS 资源的 IaC（Python CDK）。设计决策见 [ADR 0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)。

## 建什么

一套 CloudFormation stack（可按 prefix 多实例化，支持 prod-/stage- 多环境并存）：

- **DynamoDB**：`{prefix}runs`（控制面/RunStore）+ `{prefix}events`（events-out，开 `expires_at` TTL）
- **S3**：`{prefix}artifacts`（判定结果 / 报告 / offload / job-in / 引擎产物，按 key 前缀分片）
- **ECS**：`{prefix}cluster` + 2 个 Fargate task-def（`{prefix}novaact-worker` / `{prefix}midscene-worker`）
- **ECR**：2 个 repo（各承一个 worker 镜像；镜像由 CI/手动 build & push，CDK 只建 repo）
- **IAM**：每引擎一个最小权限 task role + 共享 execution role
- **VPC + SSM**：worker 网络（subnet/sg）+ 把它们的 ID 写进 `/{prefix}backend/subnets`、`/{prefix}backend/security-groups`（cli 读）。**VPC 来源三档**（context）：`-c vpc_id=vpc-xxx` 复用现有 / `-c use_default_vpc=true` 用默认 VPC / 都不给则建新——**三档均走公有子网 + 零 NAT**（worker 只出不入，公有子网 + 公网 IP 出网即够；真私有隔离留 backlog，见 ADR 0033）。

## prefix 契约（关键）

`--prefix`（CDK context `-c prefix=`，默认 `gherkai-`）**必须与 cli 的 `--prefix` 一致**——CDK 建的资源名 = cli 推导的默认名（`names.py` 复刻 cli `compose.py` 的命名规则）。不一致 → cli 连不上资源、preflight 报错点名 prefix。

命名规则的**单一事实源**分两处、须同步改：CDK 的 `names.py` ↔ cli 的 `cli/cli/compose.py`。

## 用

```bash
uv sync                                    # 建 venv、装 CDK

# 合成 CloudFormation 模板（纯本地、不碰 AWS）——CI/改动后的验证边界
CDK_DEFAULT_ACCOUNT=<acct> CDK_DEFAULT_REGION=us-east-1 uv run cdk synth

uv run pytest                              # stack 断言测试（命名/schema/TTL/container 名/prefix 切换）

# 部署（碰真 AWS、按 prefix；首次需先 cdk bootstrap）
uv run cdk deploy -c prefix=gherkai-
uv run cdk deploy -c prefix=prod-          # 另一套环境
```

镜像构建（CDK 不做，见各引擎 Dockerfile）：

```bash
# 从 engines/novaact/ 或 engines/midscene/
# **必须 --platform linux/amd64**：Fargate task-def 默认 X86_64 runtime；arm Mac（M 系列）不加则 build 出
# arm64 镜像、Fargate 容器启动期 `exec format error` 挂死（且错误在启动期、不易一眼看出是架构问题）。
docker build --platform linux/amd64 -t <ecr-repo>:latest .
docker push <ecr-repo>:latest              # repo 名 = {prefix}{engine}-worker
```

登录 ECR（push 前）：
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS \
  --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
```

## 待做（真部署时）

- `cdk bootstrap`（首次）、真 `deploy`、镜像 build & push ECR、CI 流水线。
- 真容器 grace/中断校准见 [ADR 0032](../docs/adr/0032-fargate-execution-environment.md)。
- task role 的 `bedrock-agentcore`/`nova-act`/`bedrock` 资源 ARN 当前用 `*`，真跑标定后收窄。
