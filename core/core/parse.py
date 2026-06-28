"""parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。

藏住第三方库 gherkin-official：Parser().parse() → Compiler().compile() → pickles（完全展开），
再映射成我们自己的 model.Scenario/Step。Background/Outline/DataTable/DocString 由 Compiler 展开。
core 其余部分只认 model.*，不见 pickle dict 形状。

实测要点（ADR 0025）：
- pickle step 不含字面 keyword，只有归一化 type（Context/Action/Outcome）→ 这里映射成 Given/When/Then。
- pickle 不带行号，只有 astNodeIds；行号需从 AST 节点 location.line 回查（id→node 索引）。
- argument 在 pickle 里是 {docString:{content}} / {dataTable:{rows:[{cells:[{value}]}]}}，这里重映射成 model.StepArgument。

版本：core 下限 gherkin-official>=31.0.0（实装 41.x）。本模块用顶层导出 `from gherkin import Parser, Compiler`
——该导出 ≥31.0.0 才有（<31 需走 gherkin.parser / gherkin.pickles.compiler 子模块路径），故下限锁 31。
"""
from __future__ import annotations

from dataclasses import dataclass

from gherkin import Compiler, Parser

from core.model import Scenario, Step, StepArgument


@dataclass(frozen=True)
class ParsedScenario:
    """parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。

    tags 是 scope 分组（按 @scope/@engine）的输入，属中间信息，不进最终领域模型 Scenario，
    故在这里独立承载，scope 分组后丢弃 tags、只把 .scenario 放进 Job（保持 Scenario 纯净）。
    """

    scenario: Scenario
    tags: tuple[str, ...]  # 已合并 feature 级 + scenario 级（gherkin Compiler 合并，ADR 0025）

# pickle step type → 我们的 keyword（And/But 已被 Compiler 折叠继承上一条非连接词的类型）
_TYPE_TO_KEYWORD = {"Context": "Given", "Action": "When", "Outcome": "Then"}


def _index_ast_lines(gherkin_document: dict) -> dict[str, int]:
    """建 AST 节点 id → location.line 的索引，供 pickle 的 astNodeIds 回查行号。

    遍历 feature.children 下的 background/scenario 及其 steps、scenario.examples 的 tableBody 行。
    """
    lines: dict[str, int] = {}

    def record(node: dict | None) -> None:
        if node and "id" in node and "location" in node:
            lines[node["id"]] = node["location"]["line"]

    feature = gherkin_document.get("feature")
    if not feature:
        return lines
    for child in feature.get("children", []):
        for key in ("background", "scenario"):
            node = child.get(key)
            if not node:
                continue
            record(node)
            for step in node.get("steps", []):
                record(step)
            # Scenario Outline 的 Examples 表行（pickle astNodeIds 末项指向它，用于区分展开后的多个 scenario）
            for ex in node.get("examples", []):
                for row in ex.get("tableBody", []):
                    record(row)
    return lines


def _map_argument(pickle_arg: dict | None) -> StepArgument | None:
    """pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子 dict）。"""
    if not pickle_arg:
        return None
    if "docString" in pickle_arg:
        return StepArgument(kind="docString", content=pickle_arg["docString"]["content"])
    if "dataTable" in pickle_arg:
        rows = tuple(
            tuple(cell["value"] for cell in row["cells"])
            for row in pickle_arg["dataTable"]["rows"]
        )
        return StepArgument(kind="dataTable", rows=rows)
    return None


def _scenario_line_and_example_line(
    ast_node_ids: list[str], ast_lines: dict[str, int]
) -> tuple[int | None, int | None]:
    """pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。

    普通 scenario: astNodeIds=[scenario_id] → (scenario_line, None)
    Outline 展开:  astNodeIds=[scenario_id, example_row_id] → (scenario_line, example_line)
    """
    if not ast_node_ids:
        return None, None
    scenario_line = ast_lines.get(ast_node_ids[0])
    example_line = ast_lines.get(ast_node_ids[1]) if len(ast_node_ids) > 1 else None
    return scenario_line, example_line


def parse_feature(uri: str, text: str) -> list[ParsedScenario]:
    """解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。

    uri 既是 id 前缀，也是 Compiler 的必填燃料（缺则 KeyError）。
    """
    gherkin_document = Parser().parse(text)
    gherkin_document["uri"] = uri
    ast_lines = _index_ast_lines(gherkin_document)
    pickles = Compiler().compile(gherkin_document)

    parsed: list[ParsedScenario] = []
    for pickle in pickles:
        scenario_line, example_line = _scenario_line_and_example_line(
            pickle.get("astNodeIds", []), ast_lines
        )
        # scenarioId：<uri>:<行号>[:<example行号>]（Outline 展开的多个靠 example 行号消歧，ADR 0025）
        sid = f"{uri}:{scenario_line}"
        name = pickle["name"]
        if example_line is not None:
            sid = f"{sid}:{example_line}"
            # Outline 展开后若标题模板不含占位符会重名 → 追加 Examples 行标识保证可区分（ADR 0025）
            name = f"{name} [@{example_line}]"

        steps = tuple(
            Step(
                index=i,
                keyword=_TYPE_TO_KEYWORD.get(s.get("type", ""), "Given"),
                text=s["text"],
                argument=_map_argument(s.get("argument")),
            )
            for i, s in enumerate(pickle["steps"])
        )
        parsed.append(
            ParsedScenario(
                scenario=Scenario(id=sid, name=name, steps=steps),
                tags=tuple(t["name"] for t in pickle.get("tags", [])),
            )
        )
    return parsed
