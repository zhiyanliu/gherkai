"""BackendStack 合成断言测试（ADR 0033）：纯本地 synth、不碰 AWS。

用 CDK assertions.Template 断言关键契约——尤其**与 cli 侧命名/schema 的单一事实源对齐点**（ADR 0033 护栏）：
表/桶/task-def 名、events TTL 属性、container 名不带 prefix、SSM 路径。防未来改 stack 时漂移。
跑：uv run pytest。
"""
from __future__ import annotations

import json

import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
import pytest

from stack import BackendStack


def _template(prefix: str = "gherkai-", context: dict | None = None) -> Template:
    app = cdk.App(context=context)
    stack = BackendStack(app, "T", prefix=prefix,
                         env=cdk.Environment(account="000000000000", region="us-east-1"))
    return Template.from_stack(stack)


def test_two_dynamodb_tables_with_correct_schema():
    t = _template()
    t.resource_count_is("AWS::DynamoDB::Table", 2)
    # runs 表：PK=run_id / SK=item_type
    t.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "gherkai-runs",
        "KeySchema": [
            {"AttributeName": "run_id", "KeyType": "HASH"},
            {"AttributeName": "item_type", "KeyType": "RANGE"},
        ],
    })
    # events 表：PK=pk / SK=seq + TTL expires_at（ADR 0033/0024）
    t.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "gherkai-events",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "seq", "KeyType": "RANGE"},
        ],
        "TimeToLiveSpecification": {"AttributeName": "expires_at", "Enabled": True},
    })


def test_events_table_seq_is_number_type():
    # seq 必须 Number（N）——core FargateEngine Query gt(int) 依赖数值比较、保序（非字符串序）
    t = _template()
    t.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "gherkai-events",
        "AttributeDefinitions": Match.array_with([
            {"AttributeName": "seq", "AttributeType": "N"},
        ]),
    })


def test_artifacts_bucket_private():
    t = _template()
    t.resource_count_is("AWS::S3::Bucket", 1)
    t.has_resource_properties("AWS::S3::Bucket", {
        "BucketName": "gherkai-artifacts",
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True, "BlockPublicPolicy": True,
            "IgnorePublicAcls": True, "RestrictPublicBuckets": True,
        },
    })


def test_artifacts_bucket_job_in_lifecycle():
    # job-in 对象生命周期（ADR 0033）：桶按 tag gherkai=job-in 过期（7 天），非 key 前缀（run_id 在 key 中间、
    # 前缀 filter 框不住且会误伤 jobs/reports）。回归守卫：防误删规则 / 改成前缀过滤（会误删判定真值）/ 漏 tag filter。
    t = _template()
    t.has_resource_properties("AWS::S3::Bucket", {
        "LifecycleConfiguration": {
            "Rules": Match.array_with([
                Match.object_like({
                    "Status": "Enabled",
                    "ExpirationInDays": 7,
                    "TagFilters": [{"Key": "gherkai", "Value": "job-in"}],
                }),
            ]),
        },
    })
    # 负向护栏：该规则**不得**用 Prefix filter（前缀会误删同 <run_id>/ 下的判定真值 jobs/ 与报告 reports/）。
    for bkt in t.find_resources("AWS::S3::Bucket").values():
        for rule in bkt["Properties"].get("LifecycleConfiguration", {}).get("Rules", []):
            if rule.get("Id") == "expire-job-in":
                assert "Prefix" not in rule, f"job-in 过期规则不应用 Prefix（会误删 jobs/reports）：{rule}"


def test_two_task_defs_container_name_without_prefix():
    # **container 名 = {engine}-worker（不带 prefix）**——cli RunTask containerOverrides[].name 逐字匹配（ADR 0033 硬契约）。
    t = _template()
    t.resource_count_is("AWS::ECS::TaskDefinition", 2)
    for engine in ("novaact", "midscene"):
        t.has_resource_properties("AWS::ECS::TaskDefinition", {
            "Family": f"gherkai-{engine}-worker",                       # family 带 prefix
            "ContainerDefinitions": Match.array_with([
                Match.object_like({"Name": f"{engine}-worker"}),        # container 名不带 prefix
            ]),
        })


def test_two_ecr_repos():
    t = _template()
    t.resource_count_is("AWS::ECR::Repository", 2)
    for engine in ("novaact", "midscene"):
        t.has_resource_properties("AWS::ECR::Repository", {"RepositoryName": f"gherkai-{engine}-worker"})


def test_ssm_params_with_prefix_path():
    t = _template()
    t.has_resource_properties("AWS::SSM::Parameter", {
        "Name": "/gherkai-backend/subnets", "Type": "StringList",
    })
    t.has_resource_properties("AWS::SSM::Parameter", {
        "Name": "/gherkai-backend/security-groups", "Type": "StringList",
    })


def test_task_role_has_events_putitem_not_runs():
    # task role 最小权限：events 表 PutItem，**不给 runs 表**（worker 绝不碰 RunState，ADR 0024/0030 单写者）。
    t = _template()
    # events 表 PutItem 出现在某个 policy（两个引擎 task role 都有）
    t.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": Match.array_with([
                Match.object_like({
                    "Action": "dynamodb:PutItem",
                    "Resource": Match.string_like_regexp(r".*gherkai-events.*"),
                }),
            ]),
        },
    })
    # **负向护栏（契约的关键一半）**：没有任何 policy statement 的 Resource 指向 runs 表——worker 绝不碰 RunState
    # （单写者，ADR 0024/0030）。遍历所有 IAM policy 的所有 statement，断言无一 Resource 命中 gherkai-runs。
    # （光验 events PutItem「存在」是假护栏：误加 runs 表写权限时子集匹配仍绿。）
    for policy in t.find_resources("AWS::IAM::Policy").values():
        for stmt in policy["Properties"]["PolicyDocument"]["Statement"]:
            res = json.dumps(stmt.get("Resource", ""))  # Resource 可能是 str / dict(Fn::Join) / list，统一序列化后搜
            assert "gherkai-runs" not in res, f"task role 不应含指向 runs 表的权限：{stmt}"


def test_task_role_resource_arns_narrowed():
    """IAM 资源 ARN 已收窄（ADR 0033）——回归护栏：防将来改回 * 或踩 account=aws 陷阱。

    收窄依据 = AWS SAR resource_types + IAM 策略模拟器实证。此测试钉死 CDK 生成的 ARN 形态。
    """
    t = _template()
    # 收集所有 IAM policy 的所有 statement（Resource 统一序列化后搜，容 str/list/Fn::Join）
    stmts = []
    for policy in t.find_resources("AWS::IAM::Policy").values():
        for st in policy["Properties"]["PolicyDocument"]["Statement"]:
            acts = st.get("Action")
            acts = acts if isinstance(acts, list) else [acts]
            stmts.append((acts, json.dumps(st.get("Resource", ""), ensure_ascii=False)))

    def res_for(action_substr: str) -> list[str]:
        return [res for acts, res in stmts if any(action_substr in a for a in acts)]

    # ① bedrock InvokeModel → 单一 foundation-model ARN（region 通配、model-id pin；account 段空）。不得是裸 *。
    invoke = res_for("bedrock:InvokeModel")
    assert invoke, "缺 bedrock:InvokeModel 权限"
    for r in invoke:
        assert "foundation-model/qwen.qwen3-vl-235b-a22b" in r, f"InvokeModel 未收窄到 Qwen 模型 ARN：{r}"
        assert r != '"*"', "InvokeModel 不应是裸 *"

    # ② nova-act → 收窄到 workflow-definition/* 通配（definition 名段 *，不 pin 具体名——避免 IaC 跨工程耦合
    #    worker 运行期常量）；仍锁死 service/account/region，不得是裸 *。且 **不含 GetAct**（非真实 action，已删）。
    nova = res_for("nova-act:")
    assert nova, "缺 nova-act 权限"
    for r in nova:
        assert "nova-act" in r and "workflow-definition" in r, f"nova-act 未收窄到 workflow-definition ARN：{r}"
        assert r != '"*"', "nova-act 不应是裸 *"
        # 不该 pin 具体 definition 名（那是 worker 运行期概念、不该泄进 IAM）
        assert "spike-wikipedia-benchmark" not in r, f"nova-act 不应 pin 具体 definition 名（应用 * 通配）：{r}"
    all_nova_actions = {a for acts, _ in stmts for a in acts if a.startswith("nova-act:")}
    assert "nova-act:GetAct" not in all_nova_actions, "GetAct 非真实 IAM action，应已删除"

    # ③ bedrock-agentcore Start/Stop/Get/Save → 具体 ARN（含系统 browser 的 account=aws 陷阱段）。
    #    系统 browser ARN 的 account 段必须是字面量 aws（非客户账户——模拟器实证填客户账户会 implicitDeny）。
    sys_browser_seen = any("browser/aws.browser.v1" in res for _, res in stmts)
    assert sys_browser_seen, "缺系统 browser ARN"
    for acts, res in stmts:
        if any(a in ("bedrock-agentcore:StartBrowserSession", "bedrock-agentcore:StopBrowserSession",
                     "bedrock-agentcore:GetBrowserProfile", "bedrock-agentcore:SaveBrowserSessionProfile") for a in acts):
            assert res != '"*"', f"agentcore 可收窄动作不应是裸 *：{acts}"
            if "browser/aws.browser.v1" in res:
                # 系统 browser 段的 account 必须是 aws、绝不是客户账户（copy-account 陷阱护栏）
                assert ":aws:browser/aws.browser.v1" in res, f"系统 browser account 段应为字面量 aws：{res}"
                assert "000000000000:browser/aws.browser.v1" not in res, "踩了 copy-account 陷阱（系统 browser 用了客户账户）"  # 000…0=本测试 synth env 的账号（第 21 行）——断言必须用它才抓得到陷阱（曾误用真实账号字面量、synth 产物里不可能出现、断言永真失效）
    # ④ List/Create/Connect×2 结构上不支持 resource-level，诚实保留 *（不因收窄而误删这条 * statement）
    for action in ("bedrock-agentcore:ListBrowserProfiles", "bedrock-agentcore:CreateBrowserProfile",
                   "bedrock-agentcore:ConnectBrowserAutomationStream", "bedrock-agentcore:ConnectBrowserLiveViewStream"):
        rs = res_for(action)
        assert rs and all(r == '"*"' for r in rs), f"{action} 应保留 *（SAR 不支持 resource-level）：{rs}"


def test_prefix_switches_whole_set():
    # 两层命名核心：-c prefix=prod- 切整套名，container 名仍不带 prefix。
    t = _template(prefix="prod-")
    t.has_resource_properties("AWS::DynamoDB::Table", {"TableName": "prod-runs"})
    t.has_resource_properties("AWS::DynamoDB::Table", {"TableName": "prod-events"})
    t.has_resource_properties("AWS::S3::Bucket", {"BucketName": "prod-artifacts"})
    t.has_resource_properties("AWS::ECS::TaskDefinition", {
        "Family": "prod-novaact-worker",
        "ContainerDefinitions": Match.array_with([Match.object_like({"Name": "novaact-worker"})]),  # 仍不带 prefix
    })
    t.has_resource_properties("AWS::SSM::Parameter", {"Name": "/prod-backend/subnets"})


def test_timeout_scheduler_role_and_lambda_perms():
    # job timeout 配套（ADR 0034「job timeout」节）：
    # ① Scheduler 执行 role：scheduler.amazonaws.com 可 assume、能 invoke kicker（按确定性 ARN 串授权）。
    # ② reconciler/kicker：scheduler:CreateSchedule+DeleteSchedule（ActionAfterCompletion=DELETE 前置）
    #    框在 default group 的 {prefix}job-timeout-* 名字空间；ecs:ListTasks（startedBy=run_id 定位 task）。
    t = _template()
    t.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": Match.object_like({
            "Statement": Match.array_with([Match.object_like({
                "Principal": {"Service": "scheduler.amazonaws.com"},
            })]),
        }),
    })
    t.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": Match.object_like({
            "Statement": Match.array_with([Match.object_like({
                "Action": ["scheduler:CreateSchedule", "scheduler:DeleteSchedule"],
                "Resource": Match.string_like_regexp(r".*schedule/default/gherkai-job-timeout-\*"),
            })]),
        }),
    })


def test_execution_role_and_two_task_roles():
    # 7 role：1 execution role（共享）+ 2 task role（每引擎分立，最小权限，ADR 0033）
    #        + 3 Lambda 执行角色（退出观察者 + reconciler + kicker，CDK 自动建，ADR 0034）
    #        + 1 job timeout 的 Scheduler 执行角色（Scheduler 服务 assume 它 invoke kicker，ADR 0034「job timeout」节）。
    t = _template()
    t.resource_count_is("AWS::IAM::Role", 7)


# ---- stopTimeout（grace 真容器校准入口，ADR 0032）----
def test_stop_timeout_defaults_to_120s():
    # 默认 stopTimeout = 120s（贴 Fargate 上限），两个 task-def 的 container 都带（SIGTERM→SIGKILL 宽限）。
    t = _template()
    for engine in ("novaact", "midscene"):
        t.has_resource_properties("AWS::ECS::TaskDefinition", {
            "Family": f"gherkai-{engine}-worker",
            "ContainerDefinitions": Match.array_with([
                Match.object_like({"Name": f"{engine}-worker", "StopTimeout": 120}),
            ]),
        })


def test_stop_timeout_context_override():
    # -c stop_timeout=90 覆盖默认，落到 container StopTimeout（grace 真容器校准迭代试值免改 code，ADR 0032）。
    # 用 str "90"（非 int 90）——真实 CDK `-c stop_timeout=90` 恒传字符串，测真实路径（避免测试与 CLI 分叉）。
    t = _template(context={"stop_timeout": "90"})
    t.has_resource_properties("AWS::ECS::TaskDefinition", {
        "ContainerDefinitions": Match.array_with([Match.object_like({"StopTimeout": 90})]),
    })


def test_stop_timeout_accepts_upper_boundary_120():
    # **上界含 120**（=Fargate 硬上限、=默认值）：走**校验路径**（显式 context "120"，非默认路径的 raw is None 短路）
    # 才真正锁住 `<= 120` 的「等于」一侧——off-by-one 改成 `< 120` 时本测试会红（默认路径测不到）。
    t = _template(context={"stop_timeout": "120"})
    t.has_resource_properties("AWS::ECS::TaskDefinition", {
        "ContainerDefinitions": Match.array_with([Match.object_like({"StopTimeout": 120})]),
    })


def test_stop_timeout_accepts_lower_boundary_1():
    # 下界含 1：锁 `1 <=` 的「等于」一侧（改成 `1 <` 时本测试红）。
    t = _template(context={"stop_timeout": "1"})
    t.has_resource_properties("AWS::ECS::TaskDefinition", {
        "ContainerDefinitions": Match.array_with([Match.object_like({"StopTimeout": 1})]),
    })


def test_stop_timeout_rejects_just_over_cap_121():
    # **刚越上界 121** fail-fast：钉死上限 = 120（区分 <=120 / <=119 / <=130——180 太远、区分不了边界）。
    with pytest.raises(ValueError, match="Fargate"):
        _template(context={"stop_timeout": "121"})


def test_stop_timeout_rejects_over_fargate_cap():
    # 远越界（180 > grace 下限 150 > 120 硬上限）也拒——错误信息点名 Fargate 硬上限 + ADR 0032 冲突。
    with pytest.raises(ValueError, match="Fargate"):
        _template(context={"stop_timeout": "180"})


def test_stop_timeout_rejects_zero_and_negative():
    # 下界外（0 / 负数）fail-fast——stopTimeout 须 ≥1。
    for bad in ("0", "-1"):
        with pytest.raises(ValueError, match="Fargate"):
            _template(context={"stop_timeout": bad})


def test_stop_timeout_rejects_non_integer():
    # 非整数 context 值 fail-fast（笔误如 -c stop_timeout=abc）。
    with pytest.raises(ValueError, match="整数秒"):
        _template(context={"stop_timeout": "abc"})


def test_stop_timeout_rejects_bool_and_float_typed_context():
    # cdk.json/编程式 context 可给原生 bool/float（非 CLI str）：True→int 子类、90.5→截断会绕过「须整数秒」意图。
    # 收紧后经 str() 归一，二者均 fail-fast（与 CLI str 路径同行为，见 _resolve_stop_timeout 注释）。
    for bad in (True, 90.5):
        with pytest.raises(ValueError, match="整数秒"):
            _template(context={"stop_timeout": bad})


# ---- 无状态跑批事件驱动链（ADR 0034 P4c）----
def test_reconcile_lambdas_present():
    # 3 Lambda：退出观察者（ECS STOPPED→task_exited）+ reconciler（events Stream→推进+finalize）
    #          + kicker（runs Stream INSERT→冷启动起首批，ADR 0034）。
    t = _template()
    t.resource_count_is("AWS::Lambda::Function", 3)


def test_events_table_has_stream():
    # events 表开 Stream（NEW_IMAGE）触发 reconciler（ADR 0034）。runs 表不开（无需）。
    t = _template()
    t.has_resource_properties("AWS::DynamoDB::Table", {
        "StreamSpecification": {"StreamViewType": "NEW_IMAGE"},
    })


def test_ecs_stopped_eventbridge_rule():
    # EventBridge rule 捕本 cluster 的 ECS Task STOPPED（退出观察者触发源，机制二）。
    t = _template()
    t.has_resource_properties("AWS::Events::Rule", {
        "EventPattern": {
            "source": ["aws.ecs"],
            "detail-type": ["ECS Task State Change"],
            "detail": {"lastStatus": ["STOPPED"]},
        },
    })


def test_stream_event_source_mapping_to_reconciler():
    # 2 event source mapping：events Stream→reconciler（推进主链）+ runs Stream INSERT→kicker（冷启动，ADR 0034）。
    t = _template()
    t.resource_count_is("AWS::Lambda::EventSourceMapping", 2)


def test_reconciler_can_runtask_and_passrole():
    # reconciler 权限含 ecs:RunTask + iam:PassRole（起 worker task + 传 execution/task role）。
    t = _template()
    # 找带 RunTask 的 policy（reconciler 起 worker）
    t.has_resource_properties("AWS::IAM::Policy", Match.object_like({
        "PolicyDocument": {
            "Statement": Match.array_with([
                Match.object_like({"Action": "ecs:RunTask"}),
                Match.object_like({"Action": "iam:PassRole"}),
            ]),
        },
    }))


def test_runs_table_has_stream_for_kicker():
    # runs 表开 Stream（冷启动：submit create_run INSERT → kicker，ADR 0034）。两表都开 Stream。
    t = _template()
    t.resource_count_is("AWS::DynamoDB::Table", 2)
    # 至少一张表（runs）的 Stream 供kicker；events 表 Stream 供 reconciler（前面 test 已验其一）——此处验两张都开
    streams = [tbl for tbl in t.find_resources("AWS::DynamoDB::Table").values()
               if tbl["Properties"].get("StreamSpecification", {}).get("StreamViewType") == "NEW_IMAGE"]
    assert len(streams) == 2, f"runs+events 两表都应开 Stream，实际 {len(streams)}"


def test_kicker_mapping_insert_filter():
    # kicker的 event source mapping 带 INSERT-only filter（防 reconciler 写 runs 表 MODIFY 自触发放大，ADR 0034）。
    t = _template()
    mappings = t.find_resources("AWS::Lambda::EventSourceMapping")
    insert_filtered = []
    for m in mappings.values():
        crit = m["Properties"].get("FilterCriteria", {})
        for f in crit.get("Filters", []):
            if "INSERT" in f.get("Pattern", ""):
                insert_filtered.append(m)
    assert len(insert_filtered) == 1, f"应恰有 1 个 INSERT-filter mapping（kicker），实际 {len(insert_filtered)}"
