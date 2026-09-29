"""待办清单页的判定逻辑（Nova Act 引擎用；与 _checks.mts 成对）。注册在 todo.py。"""
from playwright.sync_api import Page, expect

SEL_ITEM = "#todos li"
SEL_UNDO = "#undo"
TIMEOUT_MS = 3000


def _where(page: Page, selector: str) -> str:
    return f"页面 {page.url}，选择器 {selector}"


def delete_then_undo_keeps_item(page: Page, text: str) -> None:
    """删除给定条目后立刻点「撤销」，条目应仍在列表里。"""
    item = page.locator(SEL_ITEM, has_text=text)
    try:
        expect(item).to_have_count(1, timeout=TIMEOUT_MS)
    except AssertionError as e:
        raise AssertionError(f"要删除的条目 {text!r} 不在列表里（{_where(page, SEL_ITEM)}）") from e
    item.locator("button.del").click()
    undo = page.locator(SEL_UNDO)
    try:
        expect(undo).to_be_visible(timeout=TIMEOUT_MS)
    except AssertionError as e:
        raise AssertionError(f"删除后撤销按钮未出现（{_where(page, SEL_UNDO)}）") from e
    undo.click()
    try:
        expect(page.locator(SEL_ITEM, has_text=text)).to_have_count(1, timeout=TIMEOUT_MS)
    except AssertionError as e:
        raise AssertionError(f"撤销后条目 {text!r} 没有回到列表（{_where(page, SEL_ITEM)}）") from e
