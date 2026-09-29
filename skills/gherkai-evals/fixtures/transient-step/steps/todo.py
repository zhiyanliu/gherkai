# 待办清单的确定性 step（Nova Act 引擎）。判定逻辑在 _checks.py；与 todo.mts 成对。
from gherkai_worker_novaact.deterministic import deterministic

from . import _checks


@deterministic(r'删除 "(?P<text>[^"]+)" 后立刻撤销，条目仍在',
               description="删除给定条目后立刻点撤销，断言条目仍在列表里（精确判定，不走 AI）",
               example='When 删除 "买牛奶" 后立刻撤销，条目仍在')
def delete_then_undo(ctx, text):
    _checks.delete_then_undo_keeps_item(ctx.page, text)
