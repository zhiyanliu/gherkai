"""确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。

跑（从 repo 根）：uv run pytest -q engines/novaact/tests/test_deterministic.py
"""
import pytest

from gherkai_worker_novaact import deterministic as d


@pytest.fixture(autouse=True)
def _isolate():
    # snapshot/restore（非 clear-only）：本文件测试用干净表，退出时还原真锚点——避免同 pytest 进程内
    # 后续文件（若依赖脚手架真锚点）撞「注册表被上游文件清空」的顺序性假绿/假红。
    saved = list(d._REGISTRY)
    d.clear()
    yield
    d._REGISTRY[:] = saved


def test_register_and_match_with_named_groups():
    seen = []
    d.deterministic(r'页面地址匹配 "(?P<pattern>.+)"', description="测试", example="Then 测试")(lambda ctx, pattern: seen.append(pattern))
    hit = d.match('页面地址匹配 "/wiki/OpenAI"')
    assert hit is not None
    handler, groups = hit
    assert groups == {"pattern": "/wiki/OpenAI"}


def test_miss_returns_none():
    d.deterministic(r'页面地址匹配 "(?P<pattern>.+)"', description="测试", example="Then 测试")(lambda ctx, pattern: None)
    assert d.match("搜索 OpenAI") is None


def test_multiple_hits_raises_conflict():
    d.deterministic(r"地址(?P<a>.+)", description="测试", example="Then 测试")(lambda ctx, a: None)
    d.deterministic(r"(?P<b>地址.+)", description="测试", example="Then 测试")(lambda ctx, b: None)
    with pytest.raises(d.DeterministicConflict) as ei:
        d.match("地址匹配 x")
    # 冲突清单只经 message 传（派发侧只取 str(e) 落进 step_done.message）→ 撞上的两条模式串都得在 message 里，
    # 否则 QA 无法定位是哪两条撞了。要结构化清单走 match_batch 的 {"conflict": [...]}（ADR 0036），不挂异常字段。
    assert r"地址(?P<a>.+)" in str(ei.value) and r"(?P<b>地址.+)" in str(ei.value)


def test_handler_assertion_propagates():
    @d.deterministic(r"必假", description="测试", example="Then 测试")
    def _h(ctx):
        raise AssertionError("故意失败")

    hit = d.match("必假")
    assert hit is not None
    handler, groups = hit
    with pytest.raises(AssertionError, match="故意失败"):
        handler(object(), **groups)


def test_no_named_groups_empty_dict():
    d.deterministic(r"固定文本", description="测试", example="Then 测试")(lambda ctx: None)
    hit = d.match("固定文本")
    assert hit is not None
    _, groups = hit
    assert groups == {}


def test_missing_metadata_fails_loud():
    """description/example 必填（ADR 0036：注册即暴露，缺元数据 = 能力不可发现，fail-loud）。"""
    with pytest.raises(TypeError):
        d.deterministic(r"x")  # 旧签名（无元数据）直接不成立
    with pytest.raises(ValueError, match="description/example"):
        d.deterministic(r"x", description="", example="y")


def test_list_registry_reflects_registrations():
    d.deterministic(r'页面地址匹配 "(?P<p>.+)"', description="断言 URL", example='Then 页面地址匹配 "/x"')(
        lambda ctx, p: None)
    got = d.list_registry()
    assert got == [{"pattern": r'页面地址匹配 "(?P<p>.+)"', "description": "断言 URL",
                    "example": 'Then 页面地址匹配 "/x"'}]


def test_worker_dump_mode_real_subprocess():
    """--list-deterministic 自述模式（ADR 0036）真子进程：不读 stdin、输出 JSON、含脚手架真锚点。"""
    import json as _json
    import subprocess
    import sys as _sys

    # 真子进程按**分发形态**拉起（ADR 0037 决策 3 定位链第二级 `python -m …`），不再指脚本路径——
    # 组合根 spawn 的就是这条 cmd，测的即生产拉起方式。
    proc = subprocess.run([_sys.executable, "-m", "gherkai_worker_novaact", "--list-deterministic"],
                          capture_output=True, timeout=60)
    assert proc.returncode == 0, proc.stderr.decode()[-300:]
    entries = _json.loads(proc.stdout.decode("utf-8"))
    assert any("页面地址" in e["pattern"] for e in entries)
    assert all(e.get("description") and e.get("example") for e in entries)


def test_match_batch_hit_miss_conflict():
    """match_batch（ADR 0036 决策 4）：命中/未命中/冲突结构化返回（冲突不抛——plan 是预检不是执行）。"""
    d.deterministic(r'页面地址匹配 "(?P<p>[^"]+)"', description="断言 URL", example="Then …")(lambda ctx, p: None)
    d.deterministic(r"地址(?P<a>.+)", description="x", example="y")(lambda ctx, a: None)
    got = d.match_batch(['页面地址匹配 "x"', "无关文本", "地址什么的"])
    assert got[0] == {"conflict": [r'页面地址匹配 "(?P<p>[^"]+)"', r"地址(?P<a>.+)"]}  # 两条都命中 → 冲突
    assert got[1] is None
    assert got[2] == {"pattern": r"地址(?P<a>.+)", "description": "x"}


def test_worker_match_steps_mode_real_subprocess():
    """--match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真锚点命中面与派发一致）。"""
    import json as _json
    import subprocess
    import sys as _sys

    payload = _json.dumps(['页面地址匹配 "wikipedia"', "纯人话断言"]).encode("utf-8")
    proc = subprocess.run([_sys.executable, "-m", "gherkai_worker_novaact", "--match-steps"],
                          input=payload, capture_output=True, timeout=60)
    assert proc.returncode == 0, proc.stderr.decode()[-300:]
    got = _json.loads(proc.stdout.decode("utf-8"))
    assert got[0] is not None and "页面地址" in got[0]["pattern"]
    assert got[1] is None
