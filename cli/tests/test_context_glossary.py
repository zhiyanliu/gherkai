"""`CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。

词条 = `**规范术语 (english)**:` 一行 + 一段「是什么」（至多两句、至多一个「见 ADR」指针）+ 可选的 `_Avoid_:` 一行（只列词，
不成句）；六个 `###` 节固定。此前这些形态项每轮 doc-health 靠人查，这里机械判定；语义项（定义有无实现细节、Avoid 漏登旧名）仍归复盘。
"""
from __future__ import annotations

import re

from _doc_rules import REPO

CONTEXT = REPO / "CONTEXT.md"
SECTIONS = ["### 引擎与模型", "### 用例与断言", "### 角色与权限", "### 执行与推进", "### 结果与证据", "### 架构与交付"]
HEADER = re.compile(r"^\*\*(?P<term>[^*]+)\*\*:\s*$")


def _entries() -> list[dict]:
    lines = CONTEXT.read_text(encoding="utf-8").split("\n")
    out = []
    i = 0
    while i < len(lines):
        m = HEADER.match(lines[i])
        if not m:
            i += 1
            continue
        j = i + 1
        body = []
        while j < len(lines) and lines[j].strip() and not lines[j].startswith("_Avoid_"):
            body.append(lines[j])
            j += 1
        avoid = lines[j] if j < len(lines) and lines[j].startswith("_Avoid_") else None
        out.append({"line": i + 1, "term": m.group("term"), "body": body, "avoid": avoid})
        i = j
    return out


def test_sections_are_the_six_in_order():
    text = CONTEXT.read_text(encoding="utf-8")
    found = [line for line in text.splitlines() if line.startswith("### ")]
    assert found == SECTIONS, f"CONTEXT.md 的节不是固定的六个：{found}"


def test_glossary_has_entries():
    assert len(_entries()) >= 60, "CONTEXT.md 词条数异常，词条头形态是否变了？"


def test_each_entry_is_term_definition_and_avoid_words():
    bad = []
    for e in _entries():
        where = f"CONTEXT.md:{e['line']} {e['term']}"
        if len(e["body"]) != 1:
            bad.append(f"{where}：定义应是紧接词条头的一段（现 {len(e['body'])} 行）")
            continue
        definition = e["body"][0]
        if definition.count("。") > 2:
            bad.append(f"{where}：定义超过两句（{definition.count('。')} 句）——机制与理由搬回 ADR")
        if len(re.findall(r"见 ADR", definition)) > 1:
            bad.append(f"{where}：定义里多于一个 ADR 指针")
        if e["avoid"] is not None:
            if "。" in e["avoid"] or "见 ADR" in e["avoid"]:
                bad.append(f"{where}：_Avoid_ 只列词，不写句子与指针")
            if not e["avoid"].startswith("_Avoid_: "):
                bad.append(f"{where}：_Avoid_ 行形态应为 `_Avoid_: 词、词`")
    assert not bad, "\n".join(bad)
