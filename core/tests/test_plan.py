"""plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。"""
from __future__ import annotations

import logging

import pytest

from core.scope import FeatureSource, PlanConfig, PlanError, plan

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
    assert texts == ['"以 admin 登录"', '"以 user 登录"']  # 占位符已插值（引号是 step 人话写法的一部分）
    assert all("admin" in n or "user" in n for n in names)  # name 含 example 标识，可区分
    assert len(set(ids)) == 2  # id 各自不同（example 行号消歧）


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
    with caplog.at_level(logging.WARNING, logger="core.scope"):
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
