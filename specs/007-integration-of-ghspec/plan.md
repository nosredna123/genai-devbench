# Implementation Plan: GHSpec-Kit Integration Enhancement

**Branch**: `007-integration-of-ghspec` | **Date**: October 27, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-integration-of-ghspec/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This enhancement implements five critical improvements to the GHSpecAdapter to achieve full Spec-Kit methodology compliance and research parity. The primary requirements are: (1) Complete 5-phase workflow execution (Specify → Plan → Tasks → Implement → Bugfix) with proper artifact generation and validation, (2) Constitution-based development guidance for consistent code quality, (3) Technology stack constraint injection for controlled experiments, (4) Enhanced multi-iteration clarification handling, and (5) Dynamic prompt template loading with reproducibility controls. The technical approach leverages existing BaseAdapter infrastructure while adding constitution loading, template management, and robust bugfix automation to fulfill Spec-Kit's complete development lifecycle.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: PyYAML (config), requests (OpenAI API), pathlib (file handling), existing BaseAdapter infrastructure  
**Storage**: File-based (constitution files in config/, prompt templates in docs/ghspec/prompts/ or frameworks/ghspec/, HITL guidelines in config/hitl/)  
**Testing**: pytest with existing test infrastructure (test_phase*.py), integration tests for 5-phase workflow  
**Target Platform**: Linux server (genai-devbench experiment orchestrator environment)  
**Project Type**: Single project (adapter enhancement within existing src/adapters/)  
**Performance Goals**: Complete 5-phase workflow in under 15 minutes for typical features, support arbitrarily large constitution files through chunking  
**Constraints**: Fail-fast on API errors (no retries), single-threaded execution (no concurrent experiments), 95% automated success rate  
**Scale/Scope**: Enhance 1 adapter class (GHSpecAdapter), add 3-5 new methods, modify 5-10 existing methods, maintain compatibility with BaseAdapter interface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with BAEs Experiment Constitution v1.2.0:

- [x] **Scientific Reproducibility**: Fixed random seeds not applicable (deterministic API calls), framework versions already pinned in setup
- [x] **Clarity & Transparency**: Adapter methods have docstrings, structured JSON logging via BaseAdapter already implemented
- [x] **Open Science**: CC BY 4.0 licensed, no new proprietary dependencies (using existing OpenAI API)
- [x] **Minimal Dependencies**: Using standard library (pathlib, re, time) + existing PyYAML/requests from BaseAdapter
- [x] **Deterministic HITL**: Already implemented via config/hitl/ghspec_clarification_guidelines.txt with fixed responses
- [x] **Reproducible Metrics**: Token usage fetched from OpenAI Usage API via BaseAdapter.fetch_usage_from_openai()
- [x] **Version Control Integrity**: GHSpec framework commit hash pinned in experiment.yaml, no new repos added
- [x] **Automation-First**: All enhancements integrate with existing run_experiment.sh, no manual steps
- [x] **Failure Isolation**: Each run uses isolated workspace_path with unique run_id (BaseAdapter pattern)
- [x] **Educational Accessibility**: Code follows PEP 8, docstrings explain Spec-Kit phase mapping
- [x] **DRY Principle**: Inherits from BaseAdapter, shares constitution loading logic, reuses template loading patterns
- [x] **No Backward Compatibility Burden**: Each experiment run is independent, breaking changes to constitution loading acceptable
- [x] **Fail-Fast Philosophy**: Implements fail-fast on API errors per FR-016, no silent fallbacks or retries

**Constitution Compliance**: ✅ PASS - All 13 principles satisfied. Enhancement follows existing architecture patterns.

**Post-Design Re-Check**: ✅ CONFIRMED - Design decisions (research.md, data-model.md) maintain compliance:
- File-based storage aligns with Minimal Dependencies
- Fail-fast error handling per Principle XIII
- DRY via BaseAdapter inheritance maintained
- No backward compatibility burden (independent experiment runs)
- Educational accessibility via comprehensive quickstart.md documentation

## Project Structure

### Documentation (this feature)

```
specs/007-integration-of-ghspec/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (see below)
├── data-model.md        # Phase 1 output (see below)
├── quickstart.md        # Phase 1 output (see below)
├── contracts/           # Phase 1 output (not applicable - no new APIs)
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/adapters/
├── base_adapter.py      # Existing - provides shared infrastructure
├── ghspec_adapter.py    # MODIFY - add constitution, bugfix, template management
└── __init__.py

config/
├── hitl/
│   └── ghspec_clarification_guidelines.txt  # Existing - deterministic HITL responses
├── constitution/
│   └── default_principles.md  # NEW - default constitution when none provided
└── experiment.yaml      # Existing - experiment configuration

docs/ghspec/prompts/
├── specify_template.md  # Existing - static prompt templates
├── plan_template.md
├── tasks_template.md
├── implement_template.md
└── bugfix_template.md   # Existing - needs integration into adapter

tests/
├── test_phase1.py       # Existing - modify to test constitution loading
├── test_phase3.py       # Existing - modify to test 5-phase workflow
└── test_ghspec_bugfix.py  # NEW - test bugfix loop automation
```

**Structure Decision**: Single project structure (Option 1) is appropriate. This is an adapter enhancement, not a new standalone system. All modifications integrate into existing src/adapters/ghspec_adapter.py. No new top-level directories needed - leverage existing config/, docs/, and tests/ structure for consistency with other adapters.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No violations detected.** All enhancements comply with constitution principles.
