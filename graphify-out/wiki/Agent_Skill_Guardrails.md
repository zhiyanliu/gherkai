# Agent Skill Guardrails

> 21 nodes · cohesion 0.12

## Key Concepts

- **test_skill.py** (34 connections) — `cli/tests/test_skill.py`
- **skill_markdown_files()** (10 connections) — `cli/tests/_doc_rules.py`
- **_all_command_spans()** (5 connections) — `cli/tests/test_skill.py`
- **test_bare_flags_exist_somewhere()** (4 connections) — `cli/tests/test_skill.py`
- **_parser_nodes()** (3 connections) — `cli/tests/test_skill.py`
- **test_exclusive_claims_are_true()** (3 connections) — `cli/tests/test_skill.py`
- **test_scan_face_is_not_empty()** (3 connections) — `cli/tests/test_skill.py`
- **test_skill_mentions_commands_at_all()** (3 connections) — `cli/tests/test_skill.py`
- **_claimed_flags()** (2 connections) — `cli/tests/test_skill.py`
- **test_contract_copy_equals_transform_of_source()** (2 connections) — `cli/tests/test_skill.py`
- **test_rewrite_tables_are_all_used()** (2 connections) — `cli/tests/test_skill.py`
- **test_skill_directory_whitelist()** (2 connections) — `cli/tests/test_skill.py`
- **skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。** (1 connections) — `cli/tests/_doc_rules.py`
- **agent skill 的护栏（ADR 0043 决策六；fixture 三条见决策七）。 skill 是**产品面**：它随 wheel 发行、由…** (1 connections) — `cli/tests/test_skill.py`
- **扫描面为空即红：目录搬家 / 后缀写错不能让下面几条静默变绿。** (1 connections) — `cli/tests/test_skill.py`
- **成对比对的扫描面也不能空：一条 `gherkai …` 都抽不到，说明抽取器与写法脱节了。** (1 connections) — `cli/tests/test_skill.py`
- **散落的裸 `--flag`（不在 `gherkai …` 跨里的）只做弱断言：至少得是个真存在的 flag（打错字即红）。** (1 connections) — `cli/tests/test_skill.py`
- **副本必须逐字节等于 `transform(手写源)`：改了源没重跑生成器即红（副本不是第二事实源，是渲染产物）。** (1 connections) — `cli/tests/test_skill.py`
- **转换器的两张改写表（指针 / 禁词）里每条都得在源页命中：命中零次说明源页改了措辞、替换悄悄失效。 `transform`…** (1 connections) — `cli/tests/test_skill.py`
- **`SKILL.md` + `references/` +（按需）`scripts/`，别的一律红——挡评测资产悄悄长回发行树里…** (1 connections) — `cli/tests/test_skill.py`
- **子命令路径 → 该 parser 节点上声明的 `--flag` 集。`()` = 主 parser。** (1 connections) — `cli/tests/test_skill.py`

## Relationships

- [Skill Fixture Guardrails](Skill_Fixture_Guardrails.md) (9 shared connections)
- [Doc Command Scanning Rules](Doc_Command_Scanning_Rules.md) (7 shared connections)
- [Doc Flag Path Validation](Doc_Flag_Path_Validation.md) (5 shared connections)
- [Contract Key Documentation Check](Contract_Key_Documentation_Check.md) (3 shared connections)
- [Skill Frontmatter Validation](Skill_Frontmatter_Validation.md) (2 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (1 shared connections)
- [Deploy CLI Shell](Deploy_CLI_Shell.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (1 shared connections)

## Source Files

- `cli/tests/_doc_rules.py`
- `cli/tests/test_skill.py`

## Audit Trail

- EXTRACTED: 55 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*