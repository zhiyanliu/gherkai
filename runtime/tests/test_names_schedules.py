"""`gherkai_runtime.names` 的一次性定时触发命名（ADR 0033 资源清单 15.「专用 schedule group」「group 内的名字不带 prefix」与「命名」节
的 prefix 长度上限）。

group 名、group 内两族触发的名字与执行角色名是 IaC 与推进器之间的硬契约：IaC 按 group 名建 group、授 IAM 资源域，推进器按同一
group 名与名字建触发，任一侧单独改算法，CreateSchedule 即被拒。故断言落在形态、长度与「同一入参恒得同一串」上。
"""
from __future__ import annotations

import hashlib
import re

import pytest

from gherkai_runtime import names


def test_schedule_group_name_carries_the_prefix():
    assert names.schedule_group_name("gherkai-") == "gherkai-schedules"
    assert names.schedule_group_name("prod-") == "prod-schedules"


def test_job_timeout_schedule_name_is_the_base_and_a_fixed_length_digest_without_prefix():
    """`job-timeout-` 加 `sha1(run_id#scope_id)` 的前 20 位，不带 prefix、长度恒为 32；scope_id 是用户文本，字符集与长度不影响名字。"""
    for scope in ("a", "features/x.feature:7", "目录/" + "很长" * 200 + ".feature:9", "a#b"):
        name = names.job_timeout_schedule_name("20261126T0100Z-ab12", scope)
        expected = hashlib.sha1(f"20261126T0100Z-ab12#{scope}".encode()).hexdigest()[:20]
        assert name == f"job-timeout-{expected}"
        assert len(name) == 32
        assert re.fullmatch(r"[0-9a-z-]+", name)
    assert names.job_timeout_schedule_name("run-1", "a") != names.job_timeout_schedule_name("run-1", "b")
    assert names.job_timeout_schedule_name("run-1", "a") != names.job_timeout_schedule_name("run-2", "a")


@pytest.mark.parametrize("kind", ["deadline", "overdue"])
def test_run_timer_schedule_name_is_the_base_and_a_fixed_length_digest_without_prefix(kind):
    """`run-timer-` 加 `sha1(run_id#kind)` 的前 20 位，不带 prefix、长度恒为 30。"""
    name = names.run_timer_schedule_name("run-1", kind)
    assert name == "run-timer-" + hashlib.sha1(f"run-1#{kind}".encode()).hexdigest()[:20]
    assert len(name) == 30


def test_run_timer_kinds_are_exactly_deadline_and_overdue_and_others_are_rejected():
    """两种取值也是载荷里 run_timer 的值：推进器建触发与 kicker 认载荷引同一对常量，取值属已建触发的载荷形态、不随意改。"""
    assert names.RUN_TIMER_KINDS == ("deadline", "overdue")
    assert (names.RUN_TIMER_DEADLINE, names.RUN_TIMER_OVERDUE) == names.RUN_TIMER_KINDS
    assert names.run_timer_schedule_name("run-1", "deadline") != names.run_timer_schedule_name("run-1", "overdue")
    with pytest.raises(ValueError, match="种类"):
        names.run_timer_schedule_name("run-1", "expiry")


def test_the_two_families_do_not_share_a_name_space():
    """两族基名不同：scope_id 恰好写成某个种类时，两族的名字仍不相同（scope_id 是用户文本，不与种类共用名字空间）。"""
    for kind in names.RUN_TIMER_KINDS:
        assert names.job_timeout_schedule_name("run-1", kind) != names.run_timer_schedule_name("run-1", kind)


def test_timeout_scheduler_role_name_and_the_prefix_limit_it_sets():
    """执行角色 `{prefix}timeout-scheduler` 是带 prefix 的名字里最长的一个，IAM 角色名至多 64 个字符，prefix 上限由它推出：今为 47。"""
    assert names.timeout_scheduler_role_name("gherkai-") == "gherkai-timeout-scheduler"
    assert names.prefix_max_len() == names.IAM_ROLE_NAME_MAX_LEN - len(names.BASE_TIMEOUT_SCHEDULER_ROLE) == 47
    at_limit = "p" * (names.prefix_max_len() - 1) + "-"
    assert len(names.timeout_scheduler_role_name(at_limit)) == names.IAM_ROLE_NAME_MAX_LEN
    # 其余带 prefix 的名字在上限处都更短，起约束的确实是角色名
    for base in (names.BASE_EXIT_OBSERVER_LAMBDA, names.BASE_BUCKET, names.BASE_SCHEDULE_GROUP):
        assert len(names.default_name(at_limit, base)) < names.IAM_ROLE_NAME_MAX_LEN
