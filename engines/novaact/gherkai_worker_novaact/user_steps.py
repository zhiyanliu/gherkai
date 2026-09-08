"""加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。

**约定与解析不在这里**：`--steps-dir` flag > env > 默认 `./steps` 的解析、写进 definition、以及经
`GHERKAI_STEPS_DIR` 注给 worker，全在组合根（ADR 0037 决策 4：约定逻辑不进 worker，worker 保持薄，
ADR 0016 分层）。**worker 只认一个 env `GHERKAI_STEPS_DIR`**——没有 flag、不猜 `./steps`、不相对 worker
自身找任何东西（worker 的 CWD 在分发形态下就是用户的 CWD，猜就是漂移面）。

机制（与内建脚手架 `deterministic_steps` 的注册机制**完全同一**）：按排序递归遍历 `*.py`、逐个 import，
文件顶层 `from gherkai_worker_novaact.deterministic import deterministic` 后的 `@deterministic` 副作用
把 handler 登记进**同一张** `deterministic._REGISTRY`。Nova 侧不存在 midscene 那种「模块双实例把注册写进
一张永远不读的表」的风险（同进程、绝对包 import 命中同一 module 对象），故不需要 midscene 的「加载完某
文件若零注册即报错」兜底。

两条不变量（各有具体的坑作依据）：

- **steps 根不入 `sys.path`**：否则使用方目录里一个 `json.py` / `re.py` 就遮蔽标准库、症状离原因极远。
  故用 `importlib.util.spec_from_file_location` 按**文件路径**加载，模块名挂在合成命名空间
  `gherkai_user_steps.*` 下（不与任何真实可安装包撞名）。合成包的 `__path__` 指向 steps 目录本身，使
  step 文件之间的**相对** import（`from . import _helpers`）可用——这也是 `_*` 前缀被排除在自动加载之外
  的用途：它们是被显式 import 的辅助模块，不是 step 文件。
- **加载失败 fail-loud**（ADR 0037 决策 4）：任一文件 import 失败 → 带文件名与异常退出，**绝不静默跳过**。
  跳过等于把该文件里的确定性 step 静默换成 AI catch-all、run 可能「通过」——本项目最忌的静默降级。
  同理「给了目录但目录不存在」也是 fail-loud：使用方明确指了一个地方，那里没东西 = 配置错，不是「没定制」。

三个自述入口（`--list-deterministic` / `--match-steps`）与 job 模式**同样**先加载（调用点在
`run_scope.main()` 顶部），故 `list-deterministic` 与 plan 标注反映使用方定制（ADR 0036「真值单一」仍成立：
注册表 = 内建脚手架 + 加载的使用方模块）。
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

# 「还没开跑就被拒」的退出码。ADR 0024 只给了一个专用码（`EX_WORKER_NETWORK=80`，建连耗尽的 out-of-band
# 信号），装配/配置错没有专用码——用通用非 0 的 2，经 core 的 `raise_for_worker_exit` 落成 `RuntimeError`
# → job 记 error。**要的是「响亮」而非「可分类」**：steps 加载失败是使用方本机的配置错，人看 stderr 那行
# 诊断即知，不需要 core 侧按类型分支（真需要时再升专用码，别现在为它占码）。
EX_STEPS_LOAD = 2

# 合成命名空间根：使用方 step 文件被挂在这个名字下（`gherkai_user_steps.<相对路径转模块名>`）。
# 刻意不叫 `steps` / `user_steps` 这类可能真实存在于 PyPI 或使用方项目里的名字——`sys.modules` 撞名会让
# 「我的 import 拿到谁」变得不可预测。
_NS_ROOT = "gherkai_user_steps"


class UserStepsError(Exception):
    """使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。

    消息自带「哪个文件 + 什么异常」，调用点直接打给使用方看即可（诊断信息不靠调用点二次拼装）。
    """


def _module_name(root: Path, file: Path) -> str:
    """文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。

    用相对路径（而非仅 basename）是为了让不同子目录下的同名文件不互相覆盖 `sys.modules` 项——
    `a/login.py` 与 `b/login.py` 都要能加载、都要能注册。
    """
    rel = file.relative_to(root).with_suffix("")
    return f"{_NS_ROOT}." + ".".join(rel.parts)


def _ensure_ns_package(name: str, path: Path) -> None:
    """在 `sys.modules` 里备好一个合成命名空间壳，`__path__` 指向对应真实目录。

    `__path__` 让 step 文件里的相对 import 在 steps 树内解析；这**不是** `sys.path`——全局 import
    仍看不到 steps 目录，遮蔽风险不存在。
    """
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        mod.__doc__ = f"合成命名空间（gherkai worker 加载的使用方 steps）：{path}"
        mod.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = mod


def _is_step_file(file: Path) -> bool:
    """自动加载的筛选（ADR 0037 决策 4）：排除 `_*`（辅助模块，供相对 import）与 `test_*`（使用方自己的测试）。"""
    name = file.name
    return not name.startswith("_") and not name.startswith("test_")


def load_user_steps(root: str | None) -> list[Path]:
    """加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。

    `root` = env `GHERKAI_STEPS_DIR` 的值（由组合根注入）。None / 空串 → no-op（没定制，返回空表）。
    目录不存在、或任一文件 import 失败 → 抛 `UserStepsError`（fail-loud，见模块文档）。
    """
    if not root or not root.strip():
        return []  # 未注入 = 使用方没有定制 step，正常路径（不是错）

    base = Path(root).expanduser()
    if not base.is_dir():
        raise UserStepsError(
            f"steps 目录不存在或不是目录：{base}（GHERKAI_STEPS_DIR 指向它）"
        )
    base = base.resolve()

    # 排序遍历：保证注册顺序可复现 → ADR 0022/0036 的 conflict 清单也可复现（同一组文件永远给同一份清单）。
    # 按相对 posix 路径排序（而非 rglob 的文件系统顺序，那个跨平台/跨 fs 不稳）。
    files = sorted((f for f in base.rglob("*.py") if _is_step_file(f)),
                   key=lambda f: f.relative_to(base).as_posix())

    _ensure_ns_package(_NS_ROOT, base)
    loaded: list[Path] = []
    for file in files:
        name = _module_name(base, file)
        # 备好中间层命名空间（`a/b/login.py` → `gherkai_user_steps.a` / `.a.b`），使相对 import 有落点。
        parts = file.relative_to(base).parts[:-1]
        for i in range(len(parts)):
            _ensure_ns_package(f"{_NS_ROOT}." + ".".join(parts[: i + 1]), base.joinpath(*parts[: i + 1]))

        spec = importlib.util.spec_from_file_location(name, str(file))
        if spec is None or spec.loader is None:  # 理论上不会（路径存在且是 .py）；不静默当「没这文件」
            raise UserStepsError(f"steps 文件无法加载（拿不到 import spec）：{file}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module  # 先登记再 exec：自引用/dataclass 等按标准 import 语义需要它在表里
        try:
            spec.loader.exec_module(module)
        except Exception as e:  # noqa: BLE001  语法错/导入错/顶层任何异常一律 fail-loud（绝不跳过）
            sys.modules.pop(name, None)
            raise UserStepsError(f"steps 文件加载失败：{file}：{type(e).__name__}: {e}") from e
        loaded.append(file)
    return loaded
