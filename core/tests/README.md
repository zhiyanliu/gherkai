# core 测试：单元测试 + 集成测试

两类测试，用 pytest marker 区分。**单测默认跑、绝不连真 AWS；集成测试连真 DDB/S3、须显式触发。**

| | 单元测试 | 集成测试 |
|---|---|---|
| 标记 | 无 | `@pytest.mark.integration` |
| 后端 | moto 内存 mock | **真** DDB / S3 |
| 凭证 | 假凭证硬隔离（autouse fixture） | 真凭证（default profile） |
| 默认 `uv run pytest` | ✅ 跑 | ❌ deselect（不跑） |
| 触发 | 裸命令即跑 | `-m integration` **且**设 `AWS_DDB_TABLE`/`AWS_S3_BUCKET` 环境变量 |
| 成本 | 0 | 极低（几个 DDB item + S3 小对象，<1 分钱；不碰引擎/AgentCore） |

## 单元测试（默认）

pytest 配置在**仓库根** `pyproject.toml`（uv workspace 三成员共用一份，ADR 0037 决策 2）；根目录跑收集三成员的 `tests/`，
在 `core/` 目录下跑只收集 core 的（cwd 决定收集范围）：

```bash
uv run pytest              # 仓库根：只跑单测；集成测试被 deselect（-m 'not integration'，见根 pyproject）
cd core && uv run pytest   # 只跑 core 的单测
uv run pytest -q           # 安静模式
```

单测全程 moto mock、假凭证硬隔离（`conftest.py` 的 `_fake_aws_creds` autouse + `mock_aws`），**机器上有没有真 AWS 凭证都不影响、绝不出网连真 AWS**。

## 集成测试（连真 DDB/S3，验证 moto 抓不到的真语义）

moto 是模拟实现，与真 DDB/S3 在若干边界可能不一致（DDB 空串 SET / 保留字 / 空 Map / `SET jobs.#sid`；S3 中文·斜杠 key 编码 / `load_all` 全量；offload 真往返）。集成测试连真后端钉这些差异（`test_cloud_integration.py`）。

**最高价值的两条是 DDB 400KB item 上限**——moto **只在 `put_item` 校验 400KB、`update_item` 增量路径零校验**（实测刷近 1.5MB 全 ACCEPT），故只有真 DDB 能证：

- STATE item 经反复 `SET jobs.#sid` 增量长大越过 400KB → `ValidationException`（钉「控制面 jobs Map 无上限保护」这个真实天花板，STATE 从不 offload）。
- 含 >400KB docString 的 RunMeta：不挂 offloader 时 `create_run` 撞限抛错、挂 offloader 时成功且 META 只留 `s3://` 指针 —— **offloader 存在理由（解 400KB 限）的因果闭环**。

### 一次性：建真表 + 真桶

集成测试**假定表/桶已存在**（建表建桶归 IaC，adapter 不自建——ADR 0016/0030 决定六）。用你自己的测试账号建一次（us-east-1、default profile；名字自取，下面用示例名）。可在会话里用 `!` 前缀直接跑：

```bash
# DDB 表：分区键 run_id (HASH, S) + 排序键 item_type (RANGE, S)，按量计费（省钱）
! aws dynamodb create-table \
    --table-name ui-test-runs \
    --attribute-definitions AttributeName=run_id,AttributeType=S AttributeName=item_type,AttributeType=S \
    --key-schema AttributeName=run_id,KeyType=HASH AttributeName=item_type,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# S3 桶（桶名全局唯一，换成你自己的）
! aws s3 mb s3://ui-test-artifacts-<你的后缀> --region us-east-1
```

> 建议专门建一对**测试专用**表/桶（勿复用生产表）——集成测试会写入并自清理，但用独立资源最稳。

### 跑集成测试

```bash
# 仓库根（或 core/ 目录下，只收集 core）
export AWS_DDB_TABLE=ui-test-runs
export AWS_S3_BUCKET=ui-test-artifacts-<你的后缀>
# （凭证走 default profile；region 取 AWS_REGION/AWS_DEFAULT_REGION，默认 us-east-1）

uv run pytest -m integration            # 跑集成测试
uv run pytest -m integration -v         # 逐用例可见
uv run pytest                           # 仍只跑单测（集成默认 deselect，不受环境变量影响）
```

**没设 `AWS_DDB_TABLE`/`AWS_S3_BUCKET` 时**，集成测试**自动 skip**（不误连、不报错）——所以 `-m integration` 在没配环境的机器上是安全的空跑。

### 自清理

每个集成用例结束后，`real_aws` fixture 删掉本用例写进真表/真桶的数据（按 run_id 删 DDB 的 META/STATE item、按 key 前缀清 S3 对象），不留垃圾。清理尽力而为（逐个吞异常）——极端情况下如需手动清，按 `it-*` 前缀的 run_id / S3 key 找。

## 三重保险：`uv run pytest` 永远不连真 AWS

1. **根** `pyproject.toml` 的 `addopts = -m 'not integration' --timeout=60`：`-m 'not integration'` 默认命令 deselect 掉所有集成测试（`--timeout=60` 与连不连 AWS 无关，是挂死安全网——FargateEngine 等-STOPPED 轮询若测试忘换假 ecs 会无限轮询，60s 后 pytest-timeout 报错而非 CI 无限挂）。
2. `real_aws` fixture：没设 `AWS_DDB_TABLE`/`AWS_S3_BUCKET` 环境变量就 `skip`。
3. `_fake_aws_creds`（autouse）：对**非** integration 标记的测试盖假凭证——单测即便误发网络请求也连不上真 AWS。
