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

## Adapter Implementation Strategy

**Critical Path Note**: Infrastructure (Phases 1-7) is complete. System cannot execute real experiments until framework adapters are fully implemented (Phase 8).

### Current Adapter Status

**Infrastructure**: ✅ Complete (67% of tasks)
- Orchestration, logging, metrics, archiving working
- Configuration system functional
- Statistical analysis and visualization ready

**Adapters**: ⚠️ Placeholders (30% complete)
- Can clone repositories and verify commit hashes
- **Cannot** install dependencies, execute commands, track tokens, or detect HITL
- All three adapters (BAEs, ChatDev, Spec-kit) have identical gaps

### Phased Adapter Implementation

**Approach**: Implement ChatDev first (template for others), then replicate pattern for BAEs and GitHub Spec-kit.

**Why ChatDev First**:
1. Most mature open-source LLM agent framework (35K+ GitHub stars)
2. Well-documented CLI interface and API patterns
3. Active community with integration examples
4. Reference implementation validates orchestrator before adapting to BAEs

**Phase 8 Breakdown** (30 new tasks, 80-135 hours):

#### Phase 8A: ChatDev Adapter (T063-T073, 30-45 hours)

1. **Research & Documentation** (T063, 2-4 hours)
   - Manual ChatDev exploration: Run standalone to understand I/O patterns
   - Document: CLI entry point, command arguments, output format, token logging
   - Identify: HITL detection signals, service architecture, dependencies
   - Deliverable: `docs/chatdev_integration.md` with integration specification

2. **Environment & Setup** (T064-T065, 6-12 hours)
   - Virtual environment creation and dependency installation
   - Service startup (if API-based) or CLI validation
   - Environment variable configuration (OPENAI_API_KEY)
   - Deliverable: Working `start()` method in `chatdev_adapter.py`

3. **Core Execution** (T066-T068, 12-20 hours)
   - Command execution via subprocess with proper timeout/error handling
   - Token extraction from ChatDev logs using framework-specific regex
   - HITL detection via stdout monitoring and response injection
   - Deliverable: Working `execute_step()` and `handle_hitl()` methods

4. **Lifecycle Management** (T069-T070, 3-5 hours)
   - Health check implementation (process or API endpoint)
   - Graceful shutdown with SIGTERM/SIGKILL sequence
   - Resource cleanup and logging
   - Deliverable: Complete adapter lifecycle

5. **Testing & Validation** (T071-T073, 6-11 hours)
   - Single-step test: Verify one command executes successfully
   - Six-step test: Complete end-to-end run with archival
   - Reproducibility test: Identical config produces identical results
   - Deliverable: Passing integration tests, validated adapter

#### Phase 8B: BAEs Adapter (T074-T082, 23-41 hours)

- Replicate ChatDev pattern for BAEs framework
- **Note**: BAEs is under development, may require framework modifications
- Document all BAEs changes separately from adapter wrapper code
- Follow same 9-step process (research → setup → execution → lifecycle → testing)

#### Phase 8C: GitHub Spec-kit Adapter (T083-T091, 23-41 hours)

- Replicate ChatDev pattern for GitHub Spec-kit
- Spec-kit likely has different interface (GitHub-native vs standalone CLI)
- May require GitHub API integration for issue/PR-based workflows
- Follow same 9-step process

#### Phase 8D: Multi-Framework Validation (T092, 4-8 hours)

- Execute `./runners/run_experiment.sh all`
- Verify stopping rule triggers correctly across all frameworks
- Generate comparative analysis and visualizations
- Validate statistical reports with real data

### Integration Requirements Per Framework

Each adapter MUST implement (per FR-002.1 through FR-002.4):

**1. Repository Setup**
- Clone at pinned commit hash
- Verify SHA matches configuration
- Create isolated virtual environment
- Install framework-specific dependencies

**2. Service Lifecycle**
- Start framework services (if API-based) on configured ports
- Validate CLI availability (if CLI-based)
- Maintain process handles for monitoring
- Implement framework-specific health checks

**3. Command Execution**
- Construct framework-specific command syntax
- Execute with proper environment variables and timeouts
- Capture stdout/stderr for metric extraction
- Handle framework-specific error codes

**4. Metric Extraction**
- Parse token usage from framework logs (regex patterns vary by framework)
- Fall back to OpenAI Usage API if no framework logging
- Detect success/failure from exit codes or output markers
- Extract timing information from orchestrator (framework-agnostic)

**5. HITL Integration**
- Monitor for clarification requests (keywords or specific prompts)
- Inject fixed response from `config/hitl/expanded_spec.txt`
- Log events with SHA-1 hash for reproducibility
- Enforce 2-clarification limit per step

**6. Graceful Shutdown**
- SIGTERM → wait 30 seconds → SIGKILL if needed
- Clean up virtual environments (optional)
- Save all logs before termination
- Verify no orphaned processes

### Risk Mitigation

**Risk 1**: Framework incompatibility (doesn't support 6-step iterative refinement)
- **Mitigation**: Manual pre-validation (FR-032) before adapter implementation
- **Fallback**: Document incompatibility, exclude from comparison, update spec

**Risk 2**: Frameworks don't log tokens consistently
- **Mitigation**: Rely on OpenAI Usage API verification (FR-009.2)
- **Acceptable**: Use API as source of truth if local parsing fails

**Risk 3**: HITL detection too brittle (false positives/negatives)
- **Mitigation**: Conservative detection (miss is better than false positive)
- **Logging**: All detection attempts logged for post-analysis

**Risk 4**: BAEs requires modifications for protocol compliance
- **Mitigation**: Separate adapter wrapper (read-only) from BAEs changes (versioned)
- **Documentation**: Maintain BAEs integration log with rationale for each change

### Success Criteria for Phase 8

**ChatDev Adapter Complete** when:
- ✅ Single-step test passes (T071)
- ✅ Six-step run generates complete archive with real metrics (T072)
- ✅ Two runs with identical config produce matching token counts (T073)

**All Adapters Complete** when:
- ✅ Multi-framework test executes all 3 frameworks successfully (T092)
- ✅ Stopping rule triggers for all frameworks
- ✅ Statistical analysis generates comparative reports
- ✅ No manual intervention required for any framework

**System Ready for Research** when:
- ✅ Can execute 75-run experiment (25 per framework) unattended
- ✅ All metrics collected with <5% discrepancy vs OpenAI API
- ✅ Reproducibility validated across all frameworks
- ✅ Analysis scripts generate publication-quality outputs

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: No violations. All constitutional requirements satisfied without exceptions.
