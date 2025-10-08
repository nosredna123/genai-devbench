# Implementation Plan: BAEs Experiment Framework

**Branch**: `001-baes-experiment-framework` | **Date**: 2025-10-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-baes-experiment-framework/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an automated experiment orchestrator that executes a six-step academic CRUD evolution scenario across three LLM-driven framework systems (BAEs, ChatDev, GitHub Spec-kit). The system provides deterministic execution with reproducible metrics (autonomy, efficiency, quality), statistical analysis with confidence-based stopping rules, and complete artifact archival. Core technical approach: Python 3.11 standard library with minimal dependencies (PyYAML for config, requests for API verification), isolated per-run environments, and structured JSON logging for all events.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: 
- **Core**: Python standard library (subprocess, json, pathlib, uuid, hashlib, datetime, time)
- **Configuration**: PyYAML (YAML parsing for config/experiment.yaml)
- **HTTP/API**: requests (OpenAI Usage API verification, framework health checks)
- **Testing**: pytest (unit/integration test framework)
- **Containerization**: Docker (framework isolation)

**Storage**: 
- **Configuration**: YAML files (config/experiment.yaml, config/hitl/expanded_spec.txt)
- **Prompts**: Text files (config/prompts/step_1.txt through step_6.txt)
- **Metrics**: JSON files (metrics.json, hitl_events.jsonl, usage_api.json)
- **Artifacts**: Tar.gz archives (run.tar.gz per run with SHA-256 checksums)
- **Logs**: Structured JSON logs (stdout.log, stderr.log, orchestrator.log)

**Testing**: pytest with coverage reporting, contract tests for adapters, integration tests for end-to-end runs  
**Target Platform**: Ubuntu 22.04 LTS (Linux server environment)  
**Project Type**: Single CLI application with modular adapter architecture  
**Performance Goals**: 
- Single run completion: <60 minutes (10 min/step × 6 steps)
- Health check interval: 5 seconds
- API retry: 3 attempts with exponential backoff
- Step timeout: 10 minutes (configurable)

**Constraints**: 
- **Dependencies**: Minimal external libraries (standard library preferred)
- **Determinism**: No random behavior (fixed seeds, deterministic HITL)
- **Isolation**: No shared state between runs
- **Storage**: <10GB per run archive
- **Reproducibility**: Bit-identical metrics on reruns with same framework versions

**Scale/Scope**: 
- 3 frameworks (BAEs, ChatDev, GitHub Spec-kit)
- 6 steps per scenario
- 5-25 runs per framework (confidence-based stopping rule)
- ~75 total runs maximum (25 runs × 3 frameworks)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with BAEs Experiment Constitution v1.0.0:

- [x] **Scientific Reproducibility**: Random seeds fixed in config/experiment.yaml. Framework versions pinned to commit hashes. Prompts version-controlled and immutable during runs.
- [x] **Clarity & Transparency**: All modules will have docstrings. Configuration uses self-documenting YAML. Adapter mappings documented. Orchestrator logs use structured JSON (timestamp, run ID, step, event type). Metrics calculations include formula comments.
- [x] **Open Science**: Code licensed CC BY 4.0. Run artifacts published. No API keys hard-coded (use .env). All frameworks are open-source/publicly accessible.
- [x] **Minimal Dependencies**: Core orchestrator uses Python 3.11 standard library. Only external deps: PyYAML, requests, pytest. No framework-specific SDKs in orchestrator. Docker uses official Python base images. Dependencies pinned in requirements.txt.
- [x] **Deterministic HITL**: Clarifications automated via config/hitl/expanded_spec.txt (fixed text, version-controlled). HITL logged with query/response/timestamp. No interactive prompts. Adapter HITL methods deterministic.
- [x] **Reproducible Metrics**: Token counts verified against OpenAI Usage API. Runtime in UTC timestamps (ISO 8601). CRUD accuracy uses standardized test suite. Downtime measured as non-200 health check responses. Metrics stored in JSON with schema validation.
- [x] **Version Control Integrity**: Frameworks cloned at specific commit SHAs. Commit hashes in config/experiment.yaml. No manual patches/uncommitted changes. Docker images tag framework versions. Orchestrator verifies commit hashes before runs.
- [x] **Automation-First**: run_experiment.sh provisions environments, runs all steps, collects metrics. Configuration read from config/experiment.yaml. No interactive confirmations. Error recovery automated (retries/fail-fast).
- [x] **Failure Isolation**: Each run uses unique run ID and isolated workspace (runs/{framework}/{run-id}/). Docker containers removed after runs. Temporary files cleaned up. Database state reset between runs. Log files isolated per run ID.
- [x] **Educational Accessibility**: Documentation includes step-by-step setup for beginners. Code follows PEP 8 with descriptive names. Complex algorithms have explanatory comments/citations. Example runs provided with expected outputs. Troubleshooting guide for common failures.

**Status**: ✅ All constitutional requirements satisfied by design. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
baes_experiment/
├── config/
│   ├── experiment.yaml          # Framework configurations, commit hashes, API keys, random seeds
│   ├── hitl/
│   │   └── expanded_spec.txt    # Fixed HITL clarification text
│   └── prompts/
│       ├── step_1.txt           # "Create Student/Course/Teacher CRUD app with Python/FastAPI/SQLite"
│       ├── step_2.txt           # "Add enrollment relationship (Student-Course)"
│       ├── step_3.txt           # "Add teacher assignment (Teacher-Course)"
│       ├── step_4.txt           # "Implement data validation and error handling"
│       ├── step_5.txt           # "Add pagination and filtering to list endpoints"
│       └── step_6.txt           # "Add comprehensive UI for all operations"
│
├── src/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── runner.py            # Main run orchestration logic
│   │   ├── config_loader.py     # YAML config parsing and validation
│   │   ├── metrics_collector.py # Token/time/quality metric collection
│   │   ├── validator.py         # API/UI/downtime validation tests
│   │   └── archiver.py          # Artifact compression and hashing
│   │
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base_adapter.py      # Abstract adapter interface (start, command, health, stop)
│   │   ├── baes_adapter.py      # BAEs framework adapter
│   │   ├── chatdev_adapter.py   # ChatDev framework adapter
│   │   └── ghspec_adapter.py    # GitHub Spec-kit adapter
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── statistics.py        # Kruskal-Wallis, Dunn-Šidák, Cliff's δ
│   │   ├── stopping_rule.py     # Confidence interval convergence check
│   │   └── visualizations.py    # Radar charts, Pareto plots, timelines
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py            # Structured JSON logging
│       ├── isolation.py         # Workspace/environment isolation helpers
│       └── api_client.py        # OpenAI Usage API verification
│
├── tests/
│   ├── unit/
│   │   ├── test_orchestrator.py
│   │   ├── test_adapters.py
│   │   ├── test_metrics.py
│   │   └── test_validators.py
│   ├── integration/
│   │   ├── test_single_run.py
│   │   └── test_multi_framework.py
│   └── contract/
│       ├── test_adapter_contract.py  # Ensure all adapters implement base interface
│       └── test_config_schema.py     # YAML schema validation
│
├── runners/
│   └── run_experiment.sh        # Main entry point (accepts: baes, chatdev, ghspec, all)
│
├── runs/                         # Run artifacts (gitignored)
│   └── {framework}/
│       └── {run-id}/
│           ├── workspace/        # Framework-generated code
│           ├── metrics.json
│           ├── hitl_events.jsonl
│           ├── usage_api.json
│           ├── *.log
│           ├── commit.txt
│           └── run.tar.gz
│
├── requirements.txt              # PyYAML==6.0.1, requests==2.31.0, pytest==7.4.3
├── .env.example                  # Template for API keys (not committed)
├── .gitignore
├── README.md
└── LICENSE                       # CC BY 4.0
```

**Structure Decision**: Single CLI application structure (Option 1). No frontend/backend split needed—this is a research automation tool with CLI-only interface. All orchestration logic in `src/orchestrator/`, framework-specific adapters in `src/adapters/`, and analysis tools in `src/analysis/`. Clear separation between core logic, adapters, and utilities enables independent testing and future framework additions.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: No violations. All constitutional requirements satisfied without exceptions.
