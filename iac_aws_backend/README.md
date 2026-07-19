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

镜像构建（CDK 不做、只建 ECR repo，见各引擎 Dockerfile）——**用 `tools/build_push_workers.py` 固化**
（ECR 登录 + 两引擎 `docker build --platform linux/amd64` + push，一条命令；`--platform` 已硬编码保证、
免手敲漏它致 arm64 Fargate 启动挂死）：

```bash
# 从仓库根：
python tools/build_push_workers.py                     # 两引擎都 build&push（tag=latest, prefix=gherkai-）
python tools/build_push_workers.py --engine novaact    # 只一个
python tools/build_push_workers.py --tag v2 --prefix prod-
python tools/build_push_workers.py --dry-run           # 只打印命令、不真跑
```

底层命令（脚本封装的，供参考/排障）——repo 名 = `{prefix}{engine}-worker`，build context = `engines/{engine}/`：
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS \
  --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com   # 登录（push 前）
# **必须 --platform linux/amd64**：Fargate task-def 默认 X86_64；arm Mac 不加则 build 出 arm64、
# 容器启动期 `exec format error` 挂死（错误在启动期、不易一眼看出是架构问题）。
docker build --platform linux/amd64 -t <account>.dkr.ecr.us-east-1.amazonaws.com/<prefix><engine>-worker:latest .
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/<prefix><engine>-worker:latest
```

## 清理（destroy）

```bash
uv run cdk destroy -c use_default_vpc=true          # 或与 deploy 时相同的 -c prefix=/vpc 档
```

**数据资源不随 destroy 删**（表/桶 `RemovalPolicy.RETAIN`、防误删，见 ADR 0033）——`cdk destroy` 后 2 张 DDB 表 + artifacts 桶**残留、需手动删**：

```bash
aws dynamodb delete-table --table-name gherkai-runs
aws dynamodb delete-table --table-name gherkai-events
aws s3 rb s3://gherkai-artifacts --force            # 桶非空需 --force
aws ecr delete-repository --repository-name gherkai-novaact-worker --force   # ECR 也 RETAIN
aws ecr delete-repository --repository-name gherkai-midscene-worker --force
```

不手动删则同 prefix 重新 deploy 会因资源已存在而冲突。（cluster/task-def/SSM/日志组随 stack 销毁、无需手动。）

## 待做（真部署时）

- `cdk bootstrap`（首次）。
- **CI build & push ECR 流水线**：手动步骤已由 `tools/build_push_workers.py` 固化（本地一条命令）；**全自动 CI**（GitHub Actions + OIDC 免密钥 assume role、push/改 Dockerfile 时触发）仍待建——需先定远端仓库托管 + 凭证方案（ADR 0033 记为待做）。
- ~~真容器 grace/中断校准~~ **已完成**（4 次真跑标定，见 [ADR 0032](../docs/adr/0032-fargate-execution-environment.md) 真容器校准结论）。
- ~~task role 的 `bedrock-agentcore`/`nova-act`/`bedrock` 资源 ARN 用 `*`~~ **已收窄**（动作+资源两维度都最小）：三处从 `*` 收到具体 ARN（bedrock 单 foundation-model / nova-act definition+run/* / agentcore 系统 browser+profile/*），另 4 个结构上只能 `*` 的诚实保留；收窄后真部署真跑验证无 AccessDenied。依据/踩坑（copy-account 陷阱）/回归护栏见 [ADR 0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) IAM 表 + `tests/test_stack.py::test_task_role_resource_arns_narrowed`。
