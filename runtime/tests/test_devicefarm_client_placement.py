"""差集护栏：Python 侧的 Device Farm 客户端只在 `gherkai_runtime.devicefarm` 构造（ADR 0051 决策 10「调用归属」）。

执行期调用 Device Farm 的只有 worker 的设备模块（TS 侧，断言在 Midscene 包里）；Python 侧只有部署与诊断这一个模块承担 deploy 找回或
建立项目、doctor 列会话。core 不认识 Device Farm，推进器（云端 Lambda）不调它。客户端区域写死为 `names.DEVICE_FARM_REGION`：跟着
后端区域走的客户端在 us-east-1 等区域找不到服务端点，部署与 doctor 会把「服务不在这个区域」误报成别的故障。

扫描面是仓库里全部受版本管理与未忽略的 Python 生产源码（测试目录除外：测试不面向使用者，也不在执行路径上）。用 AST 而不是文本匹配，
换行、关键字传参与引号风格都不影响判定。
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULE = "runtime/gherkai_runtime/devicefarm.py"
LAMBDAS = "deploy_aws/gherkai_deploy_aws/lambdas/"


def _python_sources() -> list[str]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.py"],
                         capture_output=True, check=True).stdout.decode()
    paths = sorted({p for p in out.split("\0") if p and (REPO / p).is_file()})
    assert MODULE in paths, f"扫描面失效：{MODULE} 不在文件清单里（模块搬家了？请同步更新本护栏，别让它静默空扫）"
    return paths


def _is_devicefarm_client_call(node: ast.AST) -> bool:
    """`<任意>.client("devicefarm", …)`、`client(service_name="devicefarm")`、botocore 会话的 `create_client("devicefarm", …)` 等构造形态。"""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    fname = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
    if fname not in ("client", "create_client"):
        return False
    args = [a.value for a in node.args[:1] if isinstance(a, ast.Constant)]
    args += [k.value.value for k in node.keywords if k.arg == "service_name" and isinstance(k.value, ast.Constant)]
    return "devicefarm" in args


def _imports_devicefarm_module(node: ast.AST) -> bool:
    if isinstance(node, ast.Import):
        return any(a.name == "gherkai_runtime.devicefarm" for a in node.names)
    if isinstance(node, ast.ImportFrom):
        return (node.module == "gherkai_runtime.devicefarm"
                or (node.module == "gherkai_runtime" and any(a.name == "devicefarm" for a in node.names)))
    return False


def _trees() -> dict[str, ast.Module]:
    return {p: ast.parse((REPO / p).read_text(encoding="utf-8"), filename=p) for p in _python_sources()}


def _production(path: str) -> bool:
    return "tests" not in Path(path).parts


def test_devicefarm_client_is_constructed_only_in_the_runtime_module():
    sites = {p for p, tree in _trees().items() if _production(p) and any(_is_devicefarm_client_call(n) for n in ast.walk(tree))}
    assert sites == {MODULE}, (
        f"Device Farm 客户端的构造点应只有 {MODULE}，实际为 {sorted(sites)}。新的调用方请改为调用该模块的函数。")


def test_core_and_lambdas_never_touch_device_farm():
    """core（含其测试）与推进器 Lambda 源码里既不构造 Device Farm 客户端，也不 import 部署与诊断模块。"""
    hits = []
    for p, tree in _trees().items():
        if not (p.startswith("core/") or p.startswith(LAMBDAS)):
            continue
        for n in ast.walk(tree):
            if _is_devicefarm_client_call(n) or _imports_devicefarm_module(n):
                hits.append(f"{p}:{n.lineno}")
    assert not hits, f"core 与推进器 Lambda 不调用 Device Farm，命中：{hits}"


def test_scan_covers_core_and_lambdas():
    """差集的另一半：扫描面确实包含 core 与 Lambda 源码，否则上一条会因空扫而恒绿。"""
    paths = _python_sources()
    assert any(p.startswith("core/gherkai_core/") for p in paths)
    assert any(p.startswith(LAMBDAS) for p in paths)


def test_client_region_is_the_device_farm_region_constant():
    """模块里唯一的构造点显式传 `region_name=<names>.DEVICE_FARM_REGION`，不写字面量、不取后端区域。"""
    tree = ast.parse((REPO / MODULE).read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if _is_devicefarm_client_call(n)]
    assert len(calls) == 1, f"{MODULE} 里应只有一个客户端构造点，实际 {len(calls)} 个"
    region = [k.value for k in calls[0].keywords if k.arg == "region_name"]
    assert len(region) == 1, "构造客户端时须显式传 region_name"
    value = region[0]
    name = value.attr if isinstance(value, ast.Attribute) else value.id if isinstance(value, ast.Name) else None
    assert name == "DEVICE_FARM_REGION", f"region_name 须引用 names.DEVICE_FARM_REGION，实际为 {ast.unparse(value)}"


def test_import_does_not_pull_boto3():
    """boto3 与 botocore 在函数内延迟导入：CLI 与 deploy 的 `--help` 不该为这个模块拉起 AWS SDK。

    在子进程里往 `sys.modules` 塞毒（值为 None 时 import 立即失败），而不是事后断言「不在 sys.modules 里」——本会话的其他测试早已
    import 过 boto3；放在子进程里也免得重新 import 出第二份模块对象、让别的测试按旧对象打的桩落空。
    """
    code = ("import sys\n"
            "for m in ('boto3', 'botocore', 'botocore.exceptions'):\n"
            "    sys.modules[m] = None\n"
            "import gherkai_runtime.devicefarm\n")
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stderr
