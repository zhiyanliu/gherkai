"""使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。

护住四条不变量（各自对应一个真实会静默出错的场景）：
- **排序递归加载 + 注册进同一张表**：注册顺序可复现 → ADR 0022/0036 的 conflict 清单可复现。
- **排除 `_` 开头的文件或目录 / `test_*`**：前者是供其它 step 文件 import 的辅助模块（`_helpers.py`、
  `_pages/` 整目录同性质）、后者是使用方自己的测试，误当 step 文件加载会把它们的顶层副作用/依赖拖进 worker。
- **fail-loud**：语法错/导入错/目录不存在都必须响亮失败——静默跳过等于把确定性 step 换成 AI catch-all、
  run 可能假「通过」（本项目最忌的静默降级）。
- **steps 根不入 `sys.path`**：否则使用方一个 `json.py` 就遮蔽标准库、症状离原因极远。

末尾的真子进程测试跨了「进程 + argv + env」这条边（`-m gherkai_worker_novaact --capabilities` 自述对象里的
`deterministic_steps` 清单、非 0 退出码、诊断行有无），in-process 断言覆盖不到。
"""
import json
import subprocess
import sys

import pytest

from gherkai_worker_novaact import deterministic as d
from gherkai_worker_novaact.user_steps import (
    EX_STEPS_LOAD,
    UserStepsError,
    load_user_steps,
)


@pytest.fixture(autouse=True)
def _isolate():
    """注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。"""
    saved = list(d._REGISTRY)
    yield
    d._REGISTRY[:] = saved
    for name in [n for n in sys.modules if n == "gherkai_user_steps" or n.startswith("gherkai_user_steps.")]:
        del sys.modules[name]


def _step_file(path, pattern: str) -> None:
    """写一个最小 step 文件：顶层 @deterministic 注册（与使用方真实写法逐字一致）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "from gherkai_worker_novaact.deterministic import deterministic\n"
        f"@deterministic({pattern!r}, description='d', example='e')\n"
        "def h(ctx):\n"
        "    pass\n",
        encoding="utf-8",
    )


# ---- (a) 递归 + 排序 + 真注册 ----
def test_loads_recursively_in_sorted_order_and_registers(tmp_path):
    _step_file(tmp_path / "b_second.py", "P-b")
    _step_file(tmp_path / "a_first.py", "P-a")
    _step_file(tmp_path / "sub" / "nested.py", "P-nested")

    before = len(d._REGISTRY)
    loaded = load_user_steps(str(tmp_path))

    assert [f.name for f in loaded] == ["a_first.py", "b_second.py", "nested.py"]  # 排序（子目录名 'sub' 在后）
    added = [e.raw for e in d._REGISTRY[before:]]
    assert added == ["P-a", "P-b", "P-nested"]  # 注册进同一张表、顺序即加载顺序
    # 自述入口看到的即这张表（ADR 0036 真值单一）
    assert "P-nested" in [e["pattern"] for e in d.list_registry()]


def test_same_basename_in_different_dirs_both_load(tmp_path):
    """不同子目录的同名文件都要加载（合成模块名用相对路径、不是 basename，否则后者覆盖前者）。"""
    _step_file(tmp_path / "a" / "login.py", "P-a-login")
    _step_file(tmp_path / "b" / "login.py", "P-b-login")
    before = len(d._REGISTRY)
    load_user_steps(str(tmp_path))
    assert sorted(e.raw for e in d._REGISTRY[before:]) == ["P-a-login", "P-b-login"]


# ---- (b) 排除规则 ----
def test_excludes_underscore_and_test_prefixed_files(tmp_path):
    _step_file(tmp_path / "real.py", "P-real")
    _step_file(tmp_path / "_helpers.py", "P-helper")
    _step_file(tmp_path / "test_real.py", "P-test")
    _step_file(tmp_path / "sub" / "_also_skipped.py", "P-sub-helper")

    before = len(d._REGISTRY)
    loaded = load_user_steps(str(tmp_path))

    assert [f.name for f in loaded] == ["real.py"]
    assert [e.raw for e in d._REGISTRY[before:]] == ["P-real"]


def test_excludes_files_under_underscore_dirs(tmp_path):
    """`_` 开头的**目录**整棵排除：段名判定（不只 basename），否则 `_pages/selectors.py` 会被当 step 文件加载。"""
    _step_file(tmp_path / "real.py", "P-real")
    _step_file(tmp_path / "_pages" / "selectors.py", "P-page-object")
    _step_file(tmp_path / "_pages" / "deep" / "more.py", "P-page-deep")
    _step_file(tmp_path / "sub" / "_fixtures" / "data.py", "P-sub-fixture")

    before = len(d._REGISTRY)
    loaded = load_user_steps(str(tmp_path))

    assert [f.name for f in loaded] == ["real.py"]
    assert [e.raw for e in d._REGISTRY[before:]] == ["P-real"]


def test_underscore_dir_still_importable_relatively(tmp_path):
    """`_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。"""
    (tmp_path / "_pages").mkdir()
    (tmp_path / "_pages" / "selectors.py").write_text("PATTERN = 'P-from-page-object'\n", encoding="utf-8")
    (tmp_path / "uses_page_object.py").write_text(
        "from gherkai_worker_novaact.deterministic import deterministic\n"
        "from ._pages import selectors\n"
        "@deterministic(selectors.PATTERN, description='d', example='e')\n"
        "def h(ctx):\n"
        "    pass\n",
        encoding="utf-8",
    )
    before = len(d._REGISTRY)
    load_user_steps(str(tmp_path))
    assert [e.raw for e in d._REGISTRY[before:]] == ["P-from-page-object"]


def test_underscore_helper_still_importable_relatively(tmp_path):
    """`_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。"""
    (tmp_path / "_shared.py").write_text("PATTERN = 'P-from-helper'\n", encoding="utf-8")
    (tmp_path / "uses_helper.py").write_text(
        "from gherkai_worker_novaact.deterministic import deterministic\n"
        "from . import _shared\n"
        "@deterministic(_shared.PATTERN, description='d', example='e')\n"
        "def h(ctx):\n"
        "    pass\n",
        encoding="utf-8",
    )
    before = len(d._REGISTRY)
    load_user_steps(str(tmp_path))
    assert [e.raw for e in d._REGISTRY[before:]] == ["P-from-helper"]


# ---- (c) fail-loud ----
def test_syntax_error_fails_loud_naming_the_file(tmp_path):
    (tmp_path / "broken.py").write_text("def h(:\n", encoding="utf-8")
    with pytest.raises(UserStepsError) as ei:
        load_user_steps(str(tmp_path))
    assert "broken.py" in str(ei.value) and "SyntaxError" in str(ei.value)


def test_import_error_fails_loud_naming_the_file(tmp_path):
    (tmp_path / "bad_import.py").write_text("import definitely_not_a_real_module_xyz\n", encoding="utf-8")
    with pytest.raises(UserStepsError) as ei:
        load_user_steps(str(tmp_path))
    assert "bad_import.py" in str(ei.value) and "ModuleNotFoundError" in str(ei.value)


def test_broken_file_does_not_leave_half_module_in_sys_modules(tmp_path):
    (tmp_path / "broken.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
    with pytest.raises(UserStepsError):
        load_user_steps(str(tmp_path))
    assert "gherkai_user_steps.broken" not in sys.modules  # 半成品模块不留在表里骗后续 import


def test_missing_dir_fails_loud(tmp_path):
    """给了目录但不存在就是配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。"""
    with pytest.raises(UserStepsError) as ei:
        load_user_steps(str(tmp_path / "nope"))
    assert "nope" in str(ei.value)


def test_file_instead_of_dir_fails_loud(tmp_path):
    f = tmp_path / "steps.py"
    f.write_text("", encoding="utf-8")
    with pytest.raises(UserStepsError):
        load_user_steps(str(f))


@pytest.mark.parametrize("root", [None, "", "   "])
def test_unset_env_is_noop(root):
    before = list(d._REGISTRY)
    assert load_user_steps(root) == []
    assert list(d._REGISTRY) == before


# ---- (d) steps 根不入 sys.path ----
def test_steps_root_not_added_to_sys_path(tmp_path):
    _step_file(tmp_path / "real.py", "P-real")
    before = list(sys.path)
    load_user_steps(str(tmp_path))
    assert list(sys.path) == before
    assert str(tmp_path) not in sys.path and str(tmp_path.resolve()) not in sys.path


def test_step_file_named_like_stdlib_does_not_shadow(tmp_path):
    """使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。"""
    (tmp_path / "json.py").write_text(
        "from gherkai_worker_novaact.deterministic import deterministic\n"
        "@deterministic('P-json', description='d', example='e')\n"
        "def h(ctx):\n"
        "    pass\n",
        encoding="utf-8",
    )
    load_user_steps(str(tmp_path))
    import json as reimported_json

    assert reimported_json.dumps({"a": 1}) == '{"a": 1}'  # 仍是标准库的 json
    assert sys.modules["json"] is reimported_json


# ---- (e) job 模式与两个非 job 入口都先加载：真子进程验 --capabilities 的清单含使用方 step ----
def test_capabilities_subprocess_includes_user_steps(tmp_path):
    """真子进程 + 真 env：`-m gherkai_worker_novaact --capabilities` 的 `deterministic_steps` 含使用方 step。

    跨了「进程 + env + argv」这条边（in-process 断言只证 registry，证不到自述入口先加载了 steps）。
    """
    _step_file(tmp_path / "mine.py", "P-user-visible")
    proc = subprocess.run(
        [sys.executable, "-m", "gherkai_worker_novaact", "--capabilities"],
        capture_output=True, timeout=60, env={**_clean_env(), "GHERKAI_STEPS_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    caps = json.loads(proc.stdout.decode("utf-8"))
    patterns = [e["pattern"] for e in caps["deterministic_steps"]]  # 清单是自述对象的一个键（ADR 0036「5.」）
    assert "P-user-visible" in patterns
    assert any("页面地址" in p for p in patterns)  # 内建脚手架仍在（叠加、不是替换）


def test_broken_steps_dir_makes_capabilities_exit_nonzero(tmp_path):
    """fail-loud 到进程边界：坏 step 文件 → 自述入口也非 0 退出、stderr 指名文件（不静默给出残缺清单）。"""
    (tmp_path / "broken.py").write_text("def h(:\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "gherkai_worker_novaact", "--capabilities"],
        capture_output=True, timeout=60, env={**_clean_env(), "GHERKAI_STEPS_DIR": str(tmp_path)},
    )
    assert proc.returncode == EX_STEPS_LOAD, (proc.returncode, proc.stderr.decode()[-500:])
    assert "broken.py" in proc.stderr.decode("utf-8")
    assert proc.stdout.decode("utf-8").strip() == ""  # 没吐半份清单


def test_loaded_count_line_on_stderr_subprocess(tmp_path):
    """加载成功也留一行 stderr（文件数 + 目录）：使用方据它分清「目录没被读到」与「pattern 没命中」。"""
    _step_file(tmp_path / "mine.py", "P-x")
    _step_file(tmp_path / "sub" / "other.py", "P-y")
    proc = subprocess.run(
        [sys.executable, "-m", "gherkai_worker_novaact", "--capabilities"],
        capture_output=True, timeout=60, env={**_clean_env(), "GHERKAI_STEPS_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    err = proc.stderr.decode("utf-8")
    assert "已加载使用方 steps 2 个文件" in err and str(tmp_path) in err


def test_no_loaded_line_when_nothing_injected(tmp_path):
    """未注入目录表示使用方没定制，正常路径不打这行（诊断行不许变成人人都看见的噪声）。"""
    proc = subprocess.run(
        [sys.executable, "-m", "gherkai_worker_novaact", "--capabilities"],
        capture_output=True, timeout=60, env=_clean_env(),
    )
    assert proc.returncode == 0, proc.stderr.decode()[-500:]
    assert "已加载使用方 steps" not in proc.stderr.decode("utf-8")


def _clean_env() -> dict:
    """子进程 env：保留 PATH/PYTHONPATH 等运行必需项，剥掉可能干扰的 GHERKAI_* / AWS 落点。"""
    import os

    keep = ("PATH", "PYTHONPATH", "PYTHONHOME", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "VIRTUAL_ENV")
    return {k: v for k, v in os.environ.items() if k in keep}
