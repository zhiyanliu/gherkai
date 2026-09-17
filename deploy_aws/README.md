# gherkai-deploy-aws

gherkai 的 AWS 后端供给包：一条命令在你自己的 AWS 账户里建齐 `gherkai --backend cloud` 所需的资源——运行状态表、事件表、产物桶、Fargate 集群、镜像仓库、让 run 在云端自动推进的后台组件、网络与最小权限角色——并把官方 worker 基底镜像同步进你账号的镜像仓库、登记成名为 `base` 的默认镜像（自己 build 的定制镜像用 `gherkai deploy push-worker` 推）。

装上它，`gherkai deploy` 与 `gherkai destroy` 才能真正执行，并带上 `--vpc`、`--stop-timeout`、`--container-engine` 等部署选项；没装时这两条命令仍在帮助里，运行会提示先装 `gherkai[deploy-aws]` 并以退出码 2 结束。只有部署方需要装，团队里只提交 run 的人不必装。

## 安装

```bash
uv tool install 'gherkai[deploy-aws]'   # 随命令行的 extra 安装，需 Python ≥ 3.13
```

部署机上还需要 Node ≥ 22 在 PATH 上（底层用 AWS CDK）与容器引擎 docker（拉取官方 worker 基底镜像并推送到你账号的 ECR）。

## 最小用法

```bash
gherkai deploy --vpc default --prefix gherkai-      # 建或更新云端后端
gherkai destroy --vpc default --prefix gherkai-     # 拆掉后端；数据类资源保留
```

`destroy` 不删数据类资源：两张 DynamoDB 表、产物桶与镜像仓库都保留，防止误删历史与镜像。它们需要手动清理，用同一前缀重新部署前尤其要注意。

`--vpc` 与 `--prefix` 必给，`--prefix` 须与提交侧 `gherkai run` / `submit` 的 `--prefix` 一致。三档 VPC 取值、某个 account 与 region 第一次要跑的 `gherkai deploy --bootstrap`、用 `gherkai deploy --diff` 预览将要改动哪些资源、以及拆除后的手动清理步骤，见云端后端文档：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md 。

## 文档

- 部署、升级、worker 镜像与清理的完整流程：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/cloud-backend.md
- 环境变量与选项总表：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/configuration.md
- 报错了先看哪：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/troubleshooting.md
- 每版变更：https://github.com/zhiyanliu/gherkai/blob/HEAD/CHANGELOG.md

项目主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme
