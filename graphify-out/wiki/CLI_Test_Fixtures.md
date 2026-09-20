# CLI Test Fixtures

> 5 nodes · cohesion 0.40

## Key Concepts

- **gherkai_runtime/__init__.py** (13 connections) — `runtime/gherkai_runtime/__init__.py`
- **cli/tests/conftest.py** (3 connections) — `cli/tests/conftest.py`
- **_stub_engine_capabilities()** (2 connections) — `cli/tests/conftest.py`
- **cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…** (1 connections) — `cli/tests/conftest.py`
- **gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…** (1 connections) — `runtime/gherkai_runtime/__init__.py`

## Relationships

- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (1 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (1 shared connections)
- [JSON Field Contract Tests](JSON_Field_Contract_Tests.md) (1 shared connections)
- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (1 shared connections)
- [Submit & Tunnel CLI Wiring](Submit_%26_Tunnel_CLI_Wiring.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Tunnel Host TTL Watch](Tunnel_Host_TTL_Watch.md) (1 shared connections)
- [Worker Naming & Variants](Worker_Naming_%26_Variants.md) (1 shared connections)

## Source Files

- `cli/tests/conftest.py`
- `runtime/gherkai_runtime/__init__.py`

## Audit Trail

- EXTRACTED: 16 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*