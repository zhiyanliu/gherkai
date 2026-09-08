"""Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。

护的是**来源与内容清单**这条契约：handler 源在包内、依赖从**当前 venv 已安装位置**复制、`__pycache__`/`tests`
不进包、落点在临时目录而**非仓库/包目录**。漏一项的后果都要等到 Lambda 真跑才炸
（ImportError / zip 臃肿 / 往只读的 site-packages 写）。

**证据边界（绿≠对）**：多数用例用**假**复制源验「摆放规则」；`test_asset_imports_with_only_stdlib_beside_it`
则用真依赖 + 剥掉 site-packages 的**子进程**真 import 一遍——这一条才验「清单是否完整」（漏传递依赖只有真
import 才看得见，本项目就是这么抓到 gherkin-official 的 `typing_extensions` 漏项的）。
仍在边界之外：真 zip 打包、Lambda runtime 自带的 boto3、真 handler 被 AWS 调起。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import gherkai_deploy_aws
from gherkai_deploy_aws import names
from gherkai_deploy_aws.stack import BackendStack
from synth_fixture import make_stack

# 假源里故意做成**单文件模块**的那一项（真实世界里 typing_extensions 就是 `typing_extensions.py`）——
# 「包 = 目录」一刀切会把它判成「找不到」，这是踩过的坑，故两种形态都要有用例覆盖。
SINGLE_FILE_MODULE = "typing_extensions"


def _fake_installed_sources(root: Path) -> None:
    """造假「已安装依赖」：除 `SINGLE_FILE_MODULE` 外都是包目录，各带一个应被排除的 `__pycache__` 与 `tests`。"""
    root.mkdir(parents=True, exist_ok=True)
    for pkg in BackendStack.LAMBDA_ASSET_PACKAGES:
        if pkg == SINGLE_FILE_MODULE:
            (root / f"{pkg}.py").write_text(f"# {pkg}\n", encoding="utf-8")
            continue
        d = root / pkg
        (d / "__pycache__").mkdir(parents=True)
        (d / "__pycache__" / "stale.pyc").write_bytes(b"")
        (d / "tests").mkdir()
        (d / "tests" / "test_inner.py").write_text("", encoding="utf-8")
        (d / "__init__.py").write_text(f"# {pkg}\n", encoding="utf-8")


def _patch_sources(monkeypatch, root: Path) -> None:
    def fake(import_name: str) -> str:
        single = root / f"{import_name}.py"
        return str(single if single.is_file() else root / import_name)

    monkeypatch.setattr(BackendStack, "_installed_import_source", staticmethod(fake))


@pytest.fixture
def asset_dir(tmp_path, monkeypatch) -> Path:
    """synth 一次 stack，返回摊好的 asset 目录（复制源换成假的，免得断言随真包演进而漂）。"""
    src = tmp_path / "site-packages"
    _fake_installed_sources(src)
    _patch_sources(monkeypatch, src)
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv(names.LAMBDA_ASSET_DIR_ENV, str(work))
    make_stack()  # __init__ 里 _reconcile_lambdas → _build_lambda_asset
    return work / "lambda-asset"


def test_handler_sources_land_at_asset_root(asset_dir):
    """两个 handler 摊在 asset **根**、是平级顶层模块——Lambda 的 `handler="reconciler.handler"`
    与 `exit_observer` 里 `from reconciler import …` 都依赖这个形态（故 handler 源不做成本包子包）。"""
    assert (asset_dir / "reconciler.py").is_file()
    assert (asset_dir / "exit_observer.py").is_file()


def test_declared_dependencies_land_in_the_right_shape(asset_dir):
    """内容清单（ADR 0037 决策 6）+ 两种形态各自摆对：包 → 同名目录；单文件模块 → 同名 `.py`。"""
    assert set(BackendStack.LAMBDA_ASSET_PACKAGES) == {
        "gherkai_runtime", "gherkai_core", "gherkin", "packaging", "typing_extensions"}
    for pkg in BackendStack.LAMBDA_ASSET_PACKAGES:
        if pkg == SINGLE_FILE_MODULE:
            assert (asset_dir / f"{pkg}.py").is_file(), f"{pkg} 单文件模块没进 asset"
        else:
            assert (asset_dir / pkg / "__init__.py").is_file(), f"{pkg} 没进 asset"
    # boto3 由 Lambda runtime 自带、**不打**（省包体，ADR 0037 决策 6）
    assert "boto3" not in BackendStack.LAMBDA_ASSET_PACKAGES
    assert not (asset_dir / "boto3").exists()


def test_pycache_and_tests_excluded(asset_dir):
    # 负向护栏：__pycache__（跨平台 pyc 无用且撑包体）与 tests（不该进生产 zip）一律不进。
    for pkg in BackendStack.LAMBDA_ASSET_PACKAGES:
        if pkg == SINGLE_FILE_MODULE:
            continue
        assert not (asset_dir / pkg / "__pycache__").exists(), f"{pkg} 的 __pycache__ 漏进 asset"
        assert not (asset_dir / pkg / "tests").exists(), f"{pkg} 的 tests 漏进 asset"
    assert not (asset_dir / ".gitignore").exists(), "handler 目录的 .gitignore 漏进 asset"


def test_asset_not_written_into_the_installed_package(asset_dir):
    """落点在命令给的临时工作目录，**不在包目录内**——旧实现落 `iac_aws_backend/.lambda_build/`，
    那要求源码树可写；wheel 装的包目录既可能只读、也不该被写。"""
    assert Path(gherkai_deploy_aws.__file__).parent not in asset_dir.parents


def test_falls_back_to_tempdir_without_env(tmp_path, monkeypatch):
    """没有命令给的工作目录（裸跑 cdk synth）→ 自建 mkdtemp，仍不写仓库。"""
    src = tmp_path / "site-packages"
    _fake_installed_sources(src)
    _patch_sources(monkeypatch, src)
    monkeypatch.delenv(names.LAMBDA_ASSET_DIR_ENV, raising=False)
    built = Path(make_stack()._build_lambda_asset())
    assert built.is_dir() and (built / "reconciler.py").is_file()
    assert Path(__file__).parent.parent not in built.parents, f"asset 落进了仓库：{built}"


# ---- 复制源定位（find_spec）----

def test_missing_dependency_fails_loud_naming_it():
    """漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。"""
    with pytest.raises(RuntimeError, match="no_such_import_package_xyz"):
        BackendStack._installed_import_source("no_such_import_package_xyz")


def test_source_lookup_handles_both_packages_and_single_file_modules():
    """`find_spec` 对两种形态都要给出可复制的路径；editable 安装（contributor 的 workspace）也命中源码目录——
    这是「从已安装包复制」能替掉「仓库相对路径」的前提（dev 版不在 PyPI 上，联网装那条路对 contributor 是断的）。"""
    for pkg in BackendStack.LAMBDA_ASSET_PACKAGES:
        source = Path(BackendStack._installed_import_source(pkg))
        if pkg == SINGLE_FILE_MODULE:
            assert source.is_file() and source.suffix == ".py", f"{pkg} 应定位到单文件模块：{source}"
        else:
            assert (source / "__init__.py").is_file(), f"{pkg} 定位到的不是包目录：{source}"


# ---- 清单完整性（真依赖 + 真 import，跨 mock 边界）----

def test_asset_imports_with_only_stdlib_beside_it(tmp_path, monkeypatch):
    """把**真** asset 摊出来，在**剥掉 site-packages** 的子进程里 import 一遍。

    这是清单完整性的唯一有效判据：`LAMBDA_ASSET_PACKAGES` 是手写清单，漏掉某个**传递依赖**时上面所有
    「摆放规则」用例照样绿——只有真 import 才炸（`gherkin-official>=42` 的 `typing_extensions` 就是这么抓到的）。
    子进程 + 剥 site-packages 是关键：留着 site-packages 会让漏项从开发机的 venv 里悄悄补上、假绿。

    只 import 不需要 boto3 的那几个模块（boto3 由 Lambda runtime 自带、有意不打进 asset，故本地无从提供）；
    `gherkai_core.parse` 是必测的一个——它是 gherkin → typing_extensions 那条链的入口。
    """
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv(names.LAMBDA_ASSET_DIR_ENV, str(work))
    asset = Path(make_stack()._build_lambda_asset())  # 真复制源（不打桩）

    probe = "\n".join([
        "import sys",
        f"sys.path = [{str(asset)!r}] + [p for p in sys.path if 'site-packages' not in p]",
        "import reconciler, exit_observer",
        "import gherkai_core.parse, gherkai_core.reconcile, gherkai_runtime.names",
        "import gherkin, packaging.version, typing_extensions",
        "assert reconciler.TIMEOUT_STOP_SENTINEL",
        f"assert gherkai_core.parse.__file__.startswith({str(asset)!r}), gherkai_core.parse.__file__",
        "print('OK')",
    ])
    done = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert done.returncode == 0, f"asset 自身 import 不通（清单漏项？）：\n{done.stderr}"
    assert done.stdout.strip().endswith("OK")
