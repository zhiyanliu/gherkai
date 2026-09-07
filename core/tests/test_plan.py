"""plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。"""
from __future__ import annotations

import logging

import pytest

from gherkai_core.scope import FeatureSource, PlanConfig, PlanError, plan

CFG = PlanConfig(default_engine="midscene")


def _plan(text: str, uri: str = "t.feature", cfg: PlanConfig = CFG):
    return plan([FeatureSource(uri, text)], cfg)


# ---- Background 前插每个 scenario ----
def test_background_prepended():
    jobs = _plan(
        """Feature: F
  Background:
    Given 打开 "https://x"
  Scenario: s1
    When "做事"
  Scenario: s2
    When "做别的"
"""
    )
    # 两个未标 scope 的 scenario → 各自单元素 job
    assert len(jobs) == 2
    for j in jobs:
        sc = j.scenarios[0]
        assert sc.steps[0].keyword == "Given"
        assert sc.steps[0].text == '打开 "https://x"'  # background 前插
        assert sc.steps[1].keyword == "When"


# ---- Scenario Outline 多行展开 + 占位符插值 + id/name 可区分 ----
def test_outline_expands_and_distinguishable():
    jobs = _plan(
        """Feature: F
  Scenario Outline: 登录 <role>
    When "以 <role> 登录"
    Then "欢迎 <role>"
    Examples:
      | role  |
      | admin |
      | user  |
"""
    )
    assert len(jobs) == 2  # 2 行 → 2 scenario → 2 job（未标 scope）
    names = sorted(j.scenarios[0].name for j in jobs)
    texts = sorted(j.scenarios[0].steps[0].text for j in jobs)
    ids = [j.scenarios[0].id for j in jobs]
    assert texts == ['"以 admin 登录"', '"以 user 登录"']  # 占位符已插值（引号是 step 自然语言写法的一部分）
    assert all("admin" in n or "user" in n for n in names)  # name 含 example 标识，可区分
    assert len(set(ids)) == 2  # id 各自不同（example 行号消歧）


# ---- Rule 嵌套场景：id 不塌成 :None、不撞名（ADR 0025，回归 parse._index_ast_lines 只遍历顶层的 bug）----
def test_rule_nested_scenarios_get_distinct_ids():
    # gherkin Compiler 把 Rule 下 scenario 完全展开成真 pickle（真 job）；其 astNodeIds 指向 Rule 内节点。
    # 曾 bug：_index_ast_lines 只遍历 feature 顶层、不下钻 rule → Rule 内 scenario 回查行号得 None →
    # id 塌成 "t.feature:None"、多个 Rule 场景静默撞名（ADR 0025 撞名=静默灾难）。此测护住递归下钻。
    jobs = _plan(
        """Feature: F
  Rule: R1
    Scenario: r1s1
      When "做事A"
  Rule: R2
    Scenario: r2s1
      When "做事B"
"""
    )
    assert len(jobs) == 2  # 两个 Rule 各一 scenario → 两个独立 job（未标 scope、不该塌成一个）
    ids = [j.scenarios[0].id for j in jobs]
    assert all(":None" not in i for i in ids), f"id 不该含 :None（行号回查失败），实际 {ids}"
    assert len(set(ids)) == 2, f"两个 Rule 场景 id 必须各异（不撞名），实际 {ids}"


def test_rule_nested_scenario_id_has_real_line():
    # 更强：Rule 内 scenario 的 id 尾部是真实行号（不是 None）
    jobs = _plan(
        """Feature: F
  Rule: R
    Scenario: rs
      When "做事"
""",
        uri="x.feature",
    )
    assert len(jobs) == 1
    sid = jobs[0].scenarios[0].id
    # 形如 x.feature:<行号>，行号是正整数
    prefix, _, line = sid.rpartition(":")
    assert prefix == "x.feature" and line.isdigit(), f"sid 应为 x.feature:<行号>，实际 {sid}"


# ---- DataTable / DocString 进 step argument ----
def test_datatable_and_docstring_argument():
    jobs = _plan(
        '''Feature: F
  Scenario: 表
    Given 一个表
      | h1 | h2 |
      | a  | b  |
  Scenario: 文档
    Given 一段文档
      """
      行1
      行2
      """
'''
    )
    tbl = next(j for j in jobs if j.scenarios[0].name == "表").scenarios[0]
    doc = next(j for j in jobs if j.scenarios[0].name == "文档").scenarios[0]
    assert tbl.steps[0].argument.kind == "dataTable"
    assert tbl.steps[0].argument.rows == (("h1", "h2"), ("a", "b"))
    assert doc.steps[0].argument.kind == "docString"
    assert doc.steps[0].argument.content == "行1\n行2"


# ---- 乱序 Given→Then→When→Then（保序、不重排）----
def test_out_of_order_steps_preserved():
    jobs = _plan(
        """Feature: F
  Scenario: 乱序
    Given 打开 "https://x"
    Then "没有错误"
    When "搜索"
    Then "进入页面"
"""
    )
    steps = jobs[0].scenarios[0].steps
    kws = [s.keyword for s in steps]
    assert kws == ["Given", "Then", "When", "Then"]  # 严格书写顺序，不重排
    assert [s.index for s in steps] == [0, 1, 2, 3]


# ---- 跨文件相同 @scope 合并（+ warning）----
def test_cross_file_scope_merge_warns(caplog):
    fa = FeatureSource("a.feature", "Feature: A\n  @scope:shared\n  Scenario: a1\n    When \"x\"\n")
    fb = FeatureSource("b.feature", "Feature: B\n  @scope:shared\n  Scenario: b1\n    When \"y\"\n")
    with caplog.at_level(logging.WARNING, logger="gherkai_core.scope"):
        jobs = plan([fa, fb], CFG)
    assert len(jobs) == 1  # 合并成一个 scope
    assert jobs[0].scope_id == "shared"
    assert len(jobs[0].scenarios) == 2
    assert any("跨" in r.message and "合并" in r.message for r in caplog.records)  # warning 打了


# ---- 重复 uri → 报错（接口违约，与上面跨文件 @scope 合并正交：那是 warning、这是 error）----
def test_duplicate_uri_errors():
    f = FeatureSource("dup.feature", "Feature: D\n  Scenario: s\n    When \"x\"\n")
    with pytest.raises(PlanError, match="重复 uri"):
        plan([f, f], CFG)  # 同一文件喂两遍 = 调用方 bug，fail-fast


def test_distinct_uri_ok():
    # 不同 uri（即便内容相同）→ 不报错（是两份独立 feature，不是重复传同一份）
    fa = FeatureSource("a.feature", "Feature: A\n  Scenario: s\n    When \"x\"\n")
    fb = FeatureSource("b.feature", "Feature: B\n  Scenario: s\n    When \"x\"\n")
    jobs = plan([fa, fb], CFG)
    assert len(jobs) == 2


# ---- @timeout tag（ADR 0019，与 @engine 同构）：tag 优先、缺省兜底、冲突/非法值报错 ----
def test_timeout_tag_sets_job_budget():
    jobs = _plan(
        """Feature: F
  @scope:x @timeout:60
  Scenario: a
    When "x"
"""
    )
    assert jobs[0].timeout_s == 60.0


def test_timeout_default_fills_untagged_tag_wins():
    cfg = PlanConfig(default_engine="midscene", default_job_timeout_s=120.0)
    jobs = _plan(
        """Feature: F
  @scope:x @timeout:60
  Scenario: a
    When "x"
  Scenario: b
    When "y"
""",
        cfg=cfg,
    )
    by_scope = {j.scope_id: j for j in jobs}
    assert by_scope["x"].timeout_s == 60.0  # tag 优先于缺省
    untagged = next(j for sid, j in by_scope.items() if sid != "x")
    assert untagged.timeout_s == 120.0  # 未标的走缺省


def test_timeout_absent_and_no_default_is_none():
    # 无 tag、无缺省（CFG 的 default_job_timeout_s=None）→ 不超时
    jobs = _plan('Feature: F\n  Scenario: s\n    When "x"\n')
    assert jobs[0].timeout_s is None


def test_timeout_conflict_errors():
    with pytest.raises(PlanError, match="多个 @timeout"):
        _plan(
            """Feature: F
  @scope:x @timeout:60
  Scenario: c1
    When "x"
  @scope:x @timeout:90
  Scenario: c2
    When "y"
"""
        )


def test_timeout_invalid_values_error():
    # 非数字 / 非正数都拒（「标了 tag 但想不超时」不成立——删 tag 走缺省）
    with pytest.raises(PlanError, match="不是数字"):
        _plan('Feature: F\n  @scope:x @timeout:abc\n  Scenario: a\n    When "x"\n')
    with pytest.raises(PlanError, match="正数"):
        _plan('Feature: F\n  @scope:x @timeout:0\n  Scenario: a\n    When "x"\n')


@pytest.mark.parametrize("raw", ["nan", "inf", "1e400"])  # 1e400 溢出成 inf
def test_timeout_non_finite_values_error(raw: str):
    # float() 收 nan/inf（不抛 ValueError）且都不满足 <=0 → 须显式拒：下游推进器一律用 `>` 比较 deadline，
    # nan/inf 会让超时保护静默失效（标了 tag 却永不超时，正是 ADR 0019 声明预算语义要拒的形态）。
    with pytest.raises(PlanError, match="正数"):
        _plan(f'Feature: F\n  @scope:x @timeout:{raw}\n  Scenario: a\n    When "x"\n')


# ---- 同一 scope 多个不同 engine → 报错 ----
def test_engine_conflict_errors():
    with pytest.raises(PlanError, match="多个 @engine"):
        _plan(
            """Feature: F
  @scope:x @engine:midscene
  Scenario: c1
    When "x"
  @scope:x @engine:novaact
  Scenario: c2
    When "y"
"""
        )


# ---- 一个 scenario 多个不同 @scope 值（feature 级传播 + scenario 级）→ 报错 ----
def test_multi_scope_errors():
    with pytest.raises(PlanError, match="多个 @scope"):
        _plan(
            """@scope:outer
Feature: F
  @scope:inner
  Scenario: d1
    When "x"
"""
        )


# ---- feature 级 @scope 传播（无冲突）→ 正常归一个 scope ----
def test_feature_level_scope_propagates():
    jobs = _plan(
        """@scope:whole
Feature: F
  Scenario: s1
    When "x"
  Scenario: s2
    When "y"
"""
    )
    assert len(jobs) == 1  # feature 级 @scope 让整个文件归一个 scope
    assert jobs[0].scope_id == "whole"
    assert len(jobs[0].scenarios) == 2


# ---- scope 缺省 engine → 用 defaultEngine ----
def test_engine_default():
    jobs = _plan("Feature: F\n  Scenario: s\n    When \"x\"\n")
    assert jobs[0].engine == "midscene"  # 缺省
    jobs2 = _plan("Feature: F\n  Scenario: s\n    When \"x\"\n", cfg=PlanConfig(default_engine="novaact"))
    assert jobs2[0].engine == "novaact"


# ---- 未标 scope 的 scenario → 各自独立成 job（含未标 scope 的 Outline → N 个 job 不撞 id）----
def test_unlabeled_scope_independent_jobs():
    jobs = _plan(
        """Feature: F
  Scenario Outline: o <n>
    When "做 <n>"
    Examples:
      | n |
      | 1 |
      | 2 |
"""
    )
    assert len(jobs) == 2  # 未标 scope 的 Outline 展开 → 2 个独立 job
    scope_ids = [j.scope_id for j in jobs]
    assert len(set(scope_ids)) == 2  # scope_id 不撞（继承 scenario_id 的 example 消歧）


# ---- engine 继承：scope 内任一 scenario 标了 → 全 scope 继承 ----
def test_engine_inherited_within_scope():
    jobs = _plan(
        """Feature: F
  @scope:s @engine:novaact
  Scenario: c1
    When "x"
  @scope:s
  Scenario: c2
    When "y"
"""
    )
    assert len(jobs) == 1
    assert jobs[0].engine == "novaact"  # c2 未标也继承


# ---- assertion_votes：PlanConfig 缺省贯穿进每个 Job（ADR 0014）----
def test_assertion_votes_default_is_one():
    jobs = _plan("Feature: F\n  Scenario: s\n    Then \"对吗\"\n")  # CFG 未设 → 默认 1
    assert jobs[0].assertion_votes == 1


def test_assertion_votes_from_config_propagates_to_all_jobs():
    cfg = PlanConfig(default_engine="midscene", default_assertion_votes=3)
    jobs = plan(
        [FeatureSource("t.feature", "Feature: F\n  Scenario: a\n    Then \"x\"\n  Scenario: b\n    Then \"y\"\n")],
        cfg,
    )
    assert len(jobs) == 2
    assert all(j.assertion_votes == 3 for j in jobs)  # 缺省值贯穿到每个 job


# ---- 步骤关键字判不出 → fail-fast（ADR 0025：keyword 只决定派发,判不出=拒绝猜）----


def test_star_step_keyword_fails_fast():
    """`*` 步骤 type='Unknown'（gherkin 实测）→ PlanError,不静默兜底成 Given（假绿方向的错标）。"""
    import pytest
    from gherkai_core.errors import PlanError
    from gherkai_core.parse import parse_feature

    with pytest.raises(PlanError, match="关键字无法判定"):
        parse_feature("x.feature", "Feature: t\n  Scenario: s\n    * 页面显示 OpenAI 词条\n")


def test_leading_and_keyword_fails_fast():
    """无前驱非连接词的首条 And 同判不出 → PlanError;有前驱的 And 正常继承不受影响。"""
    import pytest
    from gherkai_core.errors import PlanError
    from gherkai_core.parse import parse_feature

    with pytest.raises(PlanError, match="关键字无法判定"):
        parse_feature("y.feature", "Feature: t\n  Scenario: s\n    And 先看一眼\n")
    r = parse_feature("z.feature", "Feature: t\n  Scenario: s\n    Given 打开页面\n    And 再看一眼\n")
    assert [st.keyword for st in r[0].scenario.steps] == ["Given", "Given"]  # 继承前驱,照常
