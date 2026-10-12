# Worker Job Source Input

> 70 nodes · cohesion 0.05

## Key Concepts

- **ValueError** (25 connections)
- **video.py** (15 connections) — `tools/presentations/video.py`
- **refresh()** (12 connections) — `tools/presentations/video.py`
- **minimax_narration.py** (11 connections) — `tools/presentations/minimax_narration.py`
- **web_captions()** (11 connections) — `tools/presentations/video.py`
- **JobSource** (9 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **test_job_source.py** (9 connections) — `engines/novaact/tests/test_job_source.py`
- **subtitles()** (9 connections) — `tools/presentations/video.py`
- **main()** (7 connections) — `tools/presentations/minimax_narration.py`
- **link_chapter_title_track()** (7 connections) — `tools/presentations/video.py`
- **write_json()** (6 connections) — `tools/presentations/video.py`
- **main()** (5 connections) — `.github/scripts/release_notes.py`
- **section()** (5 connections) — `.github/scripts/release_notes.py`
- **probe()** (5 connections) — `tools/presentations/video.py`
- **protected_state()** (5 connections) — `tools/presentations/video.py`
- **run()** (5 connections) — `tools/presentations/video.py`
- **job_source.py** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **._read_s3()** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- **release_notes.py** (4 connections) — `.github/scripts/release_notes.py`
- **_read_ssm_list()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **gemini_image.py** (4 connections) — `tools/presentations/gemini_image.py`
- **APIError** (4 connections) — `tools/presentations/minimax_narration.py`
- **download_subtitles()** (4 connections) — `tools/presentations/minimax_narration.py`
- **NoRedirect** (4 connections) — `tools/presentations/minimax_narration.py`
- **post()** (4 connections) — `tools/presentations/minimax_narration.py`
- *... and 45 more nodes in this community*

## Relationships

- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (3 shared connections)
- [Worker Event Sink & Redaction](Worker_Event_Sink_%26_Redaction.md) (2 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (2 shared connections)
- [Backend CDK Stack Constructs](Backend_CDK_Stack_Constructs.md) (2 shared connections)
- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (2 shared connections)
- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (1 shared connections)
- [Documentation Guardrail Rules](Documentation_Guardrail_Rules.md) (1 shared connections)
- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (1 shared connections)
- [Cloud Backend CLI Wiring Tests](Cloud_Backend_CLI_Wiring_Tests.md) (1 shared connections)
- [Schedule Module Tests](Schedule_Module_Tests.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)
- [Deploy Provider Commands](Deploy_Provider_Commands.md) (1 shared connections)

## Source Files

- `.github/scripts/release_notes.py`
- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- `engines/novaact/tests/test_job_source.py`
- `runtime/gherkai_runtime/compose.py`
- `tools/presentations/README.md`
- `tools/presentations/gemini_image.py`
- `tools/presentations/minimax_narration.py`
- `tools/presentations/production.md`
- `tools/presentations/video.py`

## Audit Trail

- EXTRACTED: 119 (82%)
- INFERRED: 26 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*