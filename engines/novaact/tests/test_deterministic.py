"""确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。

运行（从 repo 根）：uv run pytest -q engines/novaact/tests/test_deterministic.py
"""
import re
import pytest

from gherkai_worker_novaact import deterministic as d


@pytest.fixture(autouse=True)
def _isolate():
    # snapshot/restore（非 clear-only）：本文件测试用干净表，退出时还原真 step——避免同 pytest 进程内
    # 后续文件（若依赖脚手架真 step）撞「注册表被上游文件清空」的顺序性假绿/假红。
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
    """description/example 必填（ADR 0036：注册即暴露，缺元数据意味着能力不可发现，fail-loud）。"""
    with pytest.raises(TypeError):
        d.deterministic(r"x")  # 旧签名（无元数据）直接不成立
    with pytest.raises(ValueError, match="description/example"):
        d.deterministic(r"x", description="", example="y")


def test_list_registry_reflects_registrations():
    d.deterministic(r'页面地址匹配 "(?P<p>.+)"', description="断言 URL", example='Then 页面地址匹配 "/x"')(
        lambda ctx, p: None)
    got = d.list_registry()
    assert got == [{"pattern": r'页面地址匹配 "(?P<p>.+)"', "description": "断言 URL",
                    "example": 'Then 页面地址匹配 "/x"', "keywords": ["Given", "When", "Then"],  # 缺省接受全部关键字
                    "targets": [{"device": "desktop", "ui_kinds": ["web"]}]}]  # 只有 playwright 句柄 → 桌面网页（ADR 0050 决策 1）


def test_keywords_declaration_normalized_and_validated():
    """条目可声明适用关键字（ADR 0050 决策 1）：封闭集合、非空、不重复，自述按规范顺序给出。"""
    d.deterministic(r"仅 Then", description="x", example="y", keywords=("Then",))(lambda ctx: None)
    d.deterministic(r"先 When 后 Given", description="x", example="y", keywords=["When", "Given"])(lambda ctx: None)
    assert [e["keywords"] for e in d.list_registry()] == [["Then"], ["Given", "When"]]
    with pytest.raises(ValueError, match="不能为空"):
        d.deterministic(r"a", description="x", example="y", keywords=())
    with pytest.raises(ValueError, match="未知取值"):
        d.deterministic(r"b", description="x", example="y", keywords=("And",))
    with pytest.raises(ValueError, match="重复"):
        d.deterministic(r"c", description="x", example="y", keywords=("Then", "Then"))


def test_match_checks_keyword_after_hit():
    """命中模式但关键字不在条目声明里 → DeterministicKeywordMismatch（不转 AI、不顺延）；不传关键字则不核对（兼容）。"""
    d.deterministic(r"仅给定", description="x", example="y", keywords=("Given",))(lambda ctx: None)
    assert d.match("仅给定", "Given") is not None
    assert d.match("仅给定") is not None
    with pytest.raises(d.DeterministicKeywordMismatch) as ei:
        d.match("仅给定", "Then")
    assert "只在 Given 下有意义" in str(ei.value) and "当前关键字是 Then" in str(ei.value)
    assert ei.value.pattern == r"仅给定" and ei.value.keywords == ("Given",)


def test_registry_dump_via_capabilities_real_subprocess():
    """注册表清单经自述入口出去（ADR 0036「2.」/「5.」）真子进程：`--capabilities` 的 `deterministic_steps`
    键含脚手架真 step、每项元数据齐全（清单没有自己的 flag——加键不加入口，见「5.」）。"""
    import json as _json
    import subprocess
    import sys as _sys

    # 真子进程按**分发形态**拉起（ADR 0037 决策 3 定位链第二级 `python -m …`），不再指脚本路径——
    # 组合根 spawn 的就是这条 cmd，测的即生产拉起方式。
    import os as _os
    env = {k: v for k, v in _os.environ.items() if k != "GHERKAI_STEPS_DIR"}  # 只看脚手架自身的条目
    proc = subprocess.run([_sys.executable, "-m", "gherkai_worker_novaact", "--capabilities"],
                          capture_output=True, timeout=60, env=env)
    assert proc.returncode == 0, proc.stderr.decode()[-300:]
    entries = _json.loads(proc.stdout.decode("utf-8"))["deterministic_steps"]
    from gherkai_worker_novaact.deterministic_steps import ADDRESS_PATTERN
    # 脚手架差集：内建导航是唯一的内建条目（ADR 0020 第 2、3 条）——曾内置的「页面地址匹配」已退役，示范进 features/steps/。
    assert [e["pattern"] for e in entries] == [ADDRESS_PATTERN], entries
    assert entries[0]["keywords"] == ["Given", "When"], entries
    assert all(e.get("description") and e.get("example") for e in entries)


def test_address_pattern_cross_engine_fixture():
    """内建导航模式的跨语言对拍（ADR 0020 第 3 条）：同一组文本在两引擎上命中结果与 url 组一致，用例集只有一份
    （engines/fixtures/navigation-address-cases.json，Midscene 侧的 deterministic.test.mts 读同一个文件）。"""
    import json as _json
    from pathlib import Path

    from gherkai_worker_novaact.deterministic_steps import ADDRESS_PATTERN
    cases = _json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "navigation-address-cases.json")
                        .read_text(encoding="utf-8"))["cases"]
    assert len(cases) >= 10
    pat = re.compile(ADDRESS_PATTERN)
    for c in cases:
        m = pat.search(c["text"])
        assert (m is not None) == c["hit"], c
        if m:
            assert m.group("url") == c["url"], c


def test_registry_cross_engine_fixture():
    """注册表语义的跨语言对拍（ADR 0050 决策 1、0022 冲突规则）：同一组注册输入，两侧清单的 keywords 与 match_batch
    对探针的回答一致。用例集与上一条同一个文件的 registry 段，`<NAV>` 代入内建导航的 ADDRESS_PATTERN；
    其中一条是「使用方的宽模式也匹配裸地址 → 冲突、不做覆盖」。"""
    import json as _json
    from pathlib import Path

    from gherkai_worker_novaact.deterministic_steps import ADDRESS_PATTERN
    reg = _json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "navigation-address-cases.json")
                      .read_text(encoding="utf-8"))["registry"]

    def sub(v):
        if isinstance(v, str):
            return ADDRESS_PATTERN if v == "<NAV>" else v
        if isinstance(v, list):
            return [sub(x) for x in v]
        if isinstance(v, dict):
            return {k: sub(x) for k, x in v.items()}
        return v

    d.clear()
    for e in reg["entries"]:
        d.deterministic(sub(e["pattern"]), description=e["description"], example=e["example"],
                        keywords=e.get("keywords"))(lambda ctx, **groups: None)
    assert [x["keywords"] for x in d.list_registry()] == reg["expected_keywords"]
    for p in reg["probes"]:
        item = {"keyword": p["keyword"], "text": p["text"]} if "keyword" in p else p["text"]
        assert d.match_batch([item]) == [sub(p["expect"])], p


def test_match_batch_hit_miss_conflict():
    """match_batch（ADR 0036 决策 4）：命中/未命中/冲突结构化返回（冲突不抛——plan 是用例预检、不是执行）。"""
    d.deterministic(r'页面地址匹配 "(?P<p>[^"]+)"', description="断言 URL", example="Then …")(lambda ctx, p: None)
    d.deterministic(r"地址(?P<a>.+)", description="x", example="y")(lambda ctx, a: None)
    got = d.match_batch(['页面地址匹配 "x"', "无关文本", "地址什么的"])
    assert got[0] == {"conflict": [r'页面地址匹配 "(?P<p>[^"]+)"', r"地址(?P<a>.+)"]}  # 两条都命中 → 冲突
    assert got[1] is None
    assert got[2] == {"pattern": r"地址(?P<a>.+)", "description": "x"}


def test_match_batch_items_with_keyword():
    """match_batch 的每项可带关键字（{keyword, text}，ADR 0036 / 0050 决策 1）：命中但关键字不符 → keyword_mismatch。"""
    d.deterministic(r"仅给定", description="x", example="y", keywords=("Given",))(lambda ctx: None)
    got = d.match_batch([{"keyword": "Given", "text": "仅给定"}, {"keyword": "Then", "text": "仅给定"},
                         {"keyword": "Then", "text": "没命中"}, "仅给定"])
    assert got[0] == {"pattern": r"仅给定", "description": "x"}
    assert got[1] == {"keyword_mismatch": r"仅给定", "keywords": ["Given"]}
    assert got[2] is None
    assert got[3] == {"pattern": r"仅给定", "description": "x"}  # 裸字符串（旧版命令行工具）不核对关键字


def test_worker_match_steps_mode_real_subprocess():
    """--match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真 step 命中面与派发一致）。"""
    import json as _json
    import subprocess
    import sys as _sys

    payload = _json.dumps([{"keyword": "Given", "text": '"https://www.wikipedia.org/"'},
                           {"keyword": "Then", "text": "https://www.wikipedia.org/"},
                           {"keyword": "When", "text": '在输入框输入 "https://x.example/"'},
                           "https://bare.example/"]).encode("utf-8")
    proc = subprocess.run([_sys.executable, "-m", "gherkai_worker_novaact", "--match-steps"],
                          input=payload, capture_output=True, timeout=60)
    assert proc.returncode == 0, proc.stderr.decode()[-300:]
    got = _json.loads(proc.stdout.decode("utf-8"))
    assert got[0] is not None and "://" in got[0]["pattern"] and "内建导航" in got[0]["description"]
    assert got[1] == {"keyword_mismatch": got[0]["pattern"], "keywords": ["Given", "When"]}  # Then 后只有地址
    assert got[2] is None  # 句子里还有别的内容 → 不是导航、走 AI
    assert got[3] is not None and got[3]["pattern"] == got[0]["pattern"]  # 旧形态的裸字符串仍可用
