"""_checks.py 的本地单测：真浏览器打开 app/index.html。运行：uv run pytest steps/test_checks.py"""
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

import _checks

APP = (Path(__file__).resolve().parent.parent / "app" / "index.html").as_uri()


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        yield pg
        browser.close()


def test_delete_then_undo_keeps_item(page):
    page.goto(APP)
    _checks.delete_then_undo_keeps_item(page, "买牛奶")
    assert page.locator("#todos li", has_text="买牛奶").count() == 1


def test_missing_item_reports_selector_and_url(page):
    page.goto(APP)
    with pytest.raises(AssertionError) as e:
        _checks.delete_then_undo_keeps_item(page, "不存在的条目")
    assert "#todos li" in str(e.value) and "file://" in str(e.value)
