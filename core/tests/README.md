# core 测试：单元测试 + 集成测试

两类测试，用 pytest marker 区分。**单测默认运行、绝不连真 AWS；集成测试连真 DDB/S3、须显式触发。**

| | 单元测试 | 集成测试 |
|---|---|---|
| 标记 | 无 | `@pytest.mark.integration` |
| 后端 | moto 内存 mock | **真** DDB / S3 |
| 凭证 | 假凭证硬隔离（autouse fixture） | 真凭证（default profile） |
| 默认 `uv run pytest` | ✅ 运行 | ❌ deselect（不运行） |
| 触发 | 裸命令即运行 | `-m integration` **且**设 `AWS_DDB_TABLE`/`AWS_S3_BUCKET` 环境变量 |
| 成本 | 0 | 极低（几个 DDB item + S3 小对象，<1 分钱；不碰引擎/AgentCore） |

## 单元测试（默认）

pytest 配置在**仓库根** `pyproject.toml`（全部 workspace 成员共用一份，ADR 0037 决策 2）；在根目录运行时收集各成员的 `tests/`，
在 `core/` 目录下运行只收集 core 的（cwd 决定收集范围）：

```bash
uv run pytest              # 仓库根：只运行单测；集成测试被 deselect（-m 'not integration'，见根 pyproject）
cd core && uv run pytest   # 只运行 core 的单测
uv run pytest -q           # 安静模式
```

单测全程 moto mock、假凭证硬隔离（`conftest.py` 的 `_fake_aws_creds` autouse + `mock_aws`），**机器上有没有真 AWS 凭证都不影响、绝不出网连真 AWS**。

### 本机 run 目录：持有者夹具与 `real_filesystem` 标记

本机建 run 要求构造 `LocalRunStore` 时注入锁的持有者（ADR 0030 决定四），并对报告目录做文件系统类型的边界检查（ADR 0054 决策四）。`conftest.py` 为此提供两样：

- `lock_holder` 夹具：要建 run 的 `LocalRunStore(..., lock_holder=lock_holder)` 传入它；它收下持锁的描述符，用例结束时关闭。只读的构造不必传。
- 文件系统类型的自动替身：把 `run_dir.filesystem_type` 换成本平台清单的第一项，结论不依赖宿主的文件系统。

带 `@pytest.mark.real_filesystem` 的用例不替换类型，用宿主真实的取法；起真实进程建 run 的用例都带这个标记（子进程里没有替换）。宿主的系统临时目录所在的类型取到了而不在清单里时这类用例跳过，判断不了时照常执行，取法本身出错就会失败。

## 集成测试（连真 DDB/S3，验证 moto 抓不到的真语义）

moto 是模拟实现，与真 DDB/S3 在若干边界可能不一致（DDB 空串 SET / 保留字 / 空 Map / `SET jobs.#sid`；S3 按标识存取判定明细的往返与取不存在的键；offload 真往返）。集成测试连接真实后端验证这些差异（`test_cloud_integration.py`）。DDB 条件写的真实语义另由 `test_conditional_writes.py` 里的两条集成测试（`test_claim_is_exclusive_on_real_ddb`、`test_stale_projection_never_regresses_terminal_job_on_real_ddb`）复验：两个推进器认领同一个 pending job 时恰有一个成功；终态 job 不会被过期投影改回 running。`test_cloud_integration.py` 另在真表上经产品代码核运行态的几种写法：执行中的写在 job 条目里逐属性 SET 与 REMOVE、不认识的属性留下；投影的逐 job 写只在内容与库中不同时写成；终态写与结束写整体替换 jobs 时并入不认识的属性、不写回省去的已知键；结束写的 error 变体原样复制条目、只改未结束的。

**最高价值的三条是 DDB 400KB item 上限**——moto **只在 `put_item` 校验 400KB、`update_item` 增量路径零校验**（实测写到近 1.5MB 仍全部 ACCEPT）；`update_item` 整个替换一个已有的顶层属性时，moto 反而按旧值加新值计大小（真实的表按写之后的条目计），三百 KB 左右的 STATE 整体替换 `jobs` 在 moto 上就被拒。故只有真 DDB 能证：

- STATE item 经反复 `SET jobs.#sid` 增量增长、越过 400KB 时抛 `ValidationException`（验证「控制面 jobs Map 没有上限保护」这一真实上限：STATE 从不 offload）。
- 含超过 400KB docString 的 RunMeta：不挂 offloader 时 `create_run` 因超过 400KB 上限而报错；挂上 offloader 后同一份 RunMeta 写入成功，META 只保留 `s3://` 指针——这条用例完整证明了 offloader 的存在理由（绕开 400KB 上限）。
- 按一个 run 的规模上限取最宽形态的运行态（500 个 job、scope 标识与会话标识都取 255 字节、20 个执行中、其余由执行结果结束并带齐会话、认领时刻与点名的标识）：处置的结束写与结束写的 error 变体都整条写成（`test_ddb_endings_of_the_widest_run_land_real`，ADR 0034 机制三②「条目大小」与「实测项」）。结束写给由它结束的 job 各添一句说明（error 变体的原因句最长），条目随之变大，而结束这类 run 必须写成的正是这一次；写不下时 DynamoDB 以 `ValidationException` 拒绝，adapter 原样抛出、不重读（这一路径的 moto 用例只能以替身造出这个错误）。

### 一次性：建真表 + 真桶

集成测试**假定表/桶已存在**（建表建桶归 IaC，adapter 不自建——ADR 0016/0030 决定六）。用你自己的测试账号建一次（us-east-1、default profile；名字自取，下面用示例名）。

```bash
# DDB 表：分区键 run_id (HASH, S) + 排序键 item_type (RANGE, S)，按量计费（省钱）
aws dynamodb create-table \
    --table-name ui-test-runs \
    --attribute-definitions AttributeName=run_id,AttributeType=S AttributeName=item_type,AttributeType=S \
    --key-schema AttributeName=run_id,KeyType=HASH AttributeName=item_type,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# S3 桶（桶名全局唯一，换成你自己的）
aws s3 mb s3://ui-test-artifacts-<你的后缀> --region us-east-1
```

> 建议专门建一对**测试专用**表/桶（勿复用生产表）——集成测试会写入并自清理，但用独立资源最可靠。

### 运行集成测试

```bash
# 仓库根（或 core/ 目录下，只收集 core）
export AWS_DDB_TABLE=ui-test-runs
export AWS_S3_BUCKET=ui-test-artifacts-<你的后缀>
# （凭证走 default profile；region 取 AWS_REGION/AWS_DEFAULT_REGION，默认 us-east-1）

uv run pytest -m integration            # 运行集成测试
uv run pytest -m integration -v         # 逐用例可见
uv run pytest                           # 仍只运行单测（集成默认 deselect，不受环境变量影响）
```

**没设 `AWS_DDB_TABLE`/`AWS_S3_BUCKET` 时**，集成测试**自动 skip**（不误连、不报错）——所以 `-m integration` 在没配环境的机器上是安全的空操作。

### 自清理

每个集成用例结束后，`real_aws` fixture 删掉本用例写进真表/真桶的数据（按 run_id 删 DDB 的 META/STATE item、按 key 前缀清 S3 对象），不留垃圾。清理尽力而为（逐个吞异常）——极端情况下如需手动清，按 `it-*` 前缀的 run_id / S3 key 找。

## 三重保险：`uv run pytest` 永远不连真 AWS

1. **根** `pyproject.toml` 的 `addopts = -m 'not integration' --timeout=60`：`-m 'not integration'` 默认命令 deselect 掉所有集成测试（`--timeout=60` 与连不连 AWS 无关，是防挂死的安全网：schedule 会一直等到 worker 的事件流结束，测试替身的事件流若始终不结束，又没有超时或停止请求把它截断，等待就不会结束；60 秒后由 pytest-timeout 报错，CI 不会一直挂起）。
2. `real_aws` fixture：没设 `AWS_DDB_TABLE`/`AWS_S3_BUCKET` 环境变量就 `skip`。
3. `_fake_aws_creds`（autouse）：对**非** integration 标记的测试盖假凭证——单测即便误发网络请求也连不上真 AWS。
