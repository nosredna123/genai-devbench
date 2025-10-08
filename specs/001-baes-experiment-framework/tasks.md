---
description: "Implementation tasks for BAEs Experiment Framework"
---

# Tasks: BAEs Experiment Framework

**Input**: Design documents from `/specs/001-baes-experiment-framework/`
**Prerequisites**: plan.md (tech stack), spec.md (user stories), research.md (technical decisions)

**Tests**: Not explicitly requested in feature specification - focusing on implementation tasks only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure: config/, src/{orchestrator,adapters,analysis,utils}/, tests/{unit,integration,contract}/, runners/, runs/
- [x] T002 Initialize Python project with requirements.txt (PyYAML==6.0.1, requests==2.31.0, pytest==7.4.3)
- [x] T003 [P] Create .env.example with template API key variables (OPENAI_API_KEY_BAES, OPENAI_API_KEY_CHATDEV, OPENAI_API_KEY_GHSPEC)
- [x] T004 [P] Create .gitignore (runs/, .env, __pycache__, *.pyc, venv/)
- [x] T005 [P] Create LICENSE file (CC BY 4.0)
- [x] T006 [P] Create README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Implement structured JSON logger in src/utils/logger.py (JSONFormatter with timestamp, run_id, framework, step, event, metadata fields)
- [x] T008 [P] Implement configuration loader in src/orchestrator/config_loader.py (load/validate experiment.yaml schema, validate all required keys)
- [x] T009 [P] Create base adapter abstract class in src/adapters/base_adapter.py (@abstractmethod: start, execute_step, health_check, handle_hitl, stop)
- [x] T010 [P] Implement workspace isolation utilities in src/utils/isolation.py (create_isolated_workspace, cleanup_workspace with UUID run_id)
- [x] T011 Create experiment.yaml configuration template in config/experiment.yaml (frameworks: {baes, chatdev, ghspec} with repo_url, commit_hash, api_port, ui_port, api_key_env; stopping_rule; timeouts)
- [x] T012 [P] Create six-step scenario prompt files in config/prompts/ (step_1.txt: "Create Student/Course/Teacher CRUD app", step_2.txt: "Add enrollment", step_3.txt: "Add teacher assignment", step_4.txt: "Add validation", step_5.txt: "Add pagination", step_6.txt: "Add comprehensive UI")
- [x] T013 [P] Create fixed HITL clarification text in config/hitl/expanded_spec.txt (deterministic expanded specification for all frameworks)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Single Framework Run (Priority: P1) 🎯 MVP

**Goal**: Execute a complete six-step experiment run for one framework, collecting metrics and archiving artifacts

**Independent Test**: Run `./runners/run_experiment.sh baes` and verify all six steps complete with metrics.json, archived run.tar.gz, and health checks passed

### Implementation for User Story 1

- [x] T014 [P] [US1] Implement metrics collector in src/orchestrator/metrics_collector.py (collect UTT, HIT, AUTR, HEU, TOK_IN, TOK_OUT, T_WALL with UTC timestamps)
- [x] T015 [P] [US1] Implement API validator in src/orchestrator/validator.py (test_crud_endpoints for Student/Course/Teacher POST/GET/PATCH/DELETE, test_relational_endpoints for enroll/assign)
- [x] T016 [P] [US1] Implement UI validator in src/orchestrator/validator.py (test_ui_pages for HTTP 200 checks and HTML content labels)
- [x] T017 [P] [US1] Implement downtime probe in src/orchestrator/validator.py (health_check_loop with 5-second interval, increment ZDI on non-200)
- [x] T018 [US1] Implement quality metrics calculator in src/orchestrator/metrics_collector.py (CRUDe 0-12 scale, ESR 0-1, MC 0-1, ZDI count, Q* composite, AEI composite)
- [x] T019 [US1] Implement archiver in src/orchestrator/archiver.py (create run.tar.gz with workspace/metrics/logs, compute SHA-256 hash, store in metadata.json, delete workspace after archival)
- [ ] T020 [US1] ⚠️ INCOMPLETE - Implement BAEs adapter in src/adapters/baes_adapter.py - **STATUS**: Placeholder only (30% complete - clone/checkout working, needs full integration per FR-002.1 through FR-002.4). See Phase 8 for detailed subtasks.
- [x] T021 [US1] Implement timeout enforcement in src/orchestrator/runner.py (10-minute alarm per step, SIGTERM → wait 30s → SIGKILL on timeout, mark run as "timeout failure")
- [x] T022 [US1] Implement retry logic in src/orchestrator/runner.py (r=2 automatic retries on step failure with exponential backoff, mark run as "failed" after retries exhausted)
- [x] T023 [US1] Implement main run orchestration in src/orchestrator/runner.py (execute_single_run: initialize run_id, create workspace, load config, initialize adapter, execute 6 steps sequentially, collect metrics after each step, run validations, handle HITL, finalize and archive)
- [x] T024 [US1] Create run_experiment.sh entry point in runners/run_experiment.sh (parse args: baes|chatdev|ghspec|all, setup venv, install deps, invoke orchestrator with framework arg, handle errors)
- [x] T025 [US1] Implement OpenAI Usage API client in src/utils/api_client.py (verify_token_counts with exponential backoff retry, compare local vs API counts, log discrepancies)
- [x] T026 [US1] Add usage API verification to run finalization in src/orchestrator/runner.py (call api_client after metrics collection, store results in usage_api.json)

**Checkpoint**: ⚠️ User Story 1 is PARTIALLY FUNCTIONAL - infrastructure works but framework adapters cannot execute real steps. See Phase 8 for completion.

---

## Phase 4: User Story 2 - Compare Multiple Frameworks (Priority: P2)

**Goal**: Execute runs for all three frameworks with confidence-based stopping rule until statistical significance achieved

**Independent Test**: Run `./runners/run_experiment.sh all` and verify stopping rule terminates when CI ≤10% half-width for all metrics across all frameworks

### Implementation for User Story 2

- [ ] T027 [P] [US2] ⚠️ INCOMPLETE - Implement ChatDev adapter in src/adapters/chatdev_adapter.py - **STATUS**: Placeholder only (30% complete - clone/checkout working, needs full integration per FR-002.1 through FR-002.4). See Phase 8 for detailed subtasks.
- [ ] T028 [P] [US2] ⚠️ INCOMPLETE - Implement GitHub Spec-kit adapter in src/adapters/ghspec_adapter.py - **STATUS**: Placeholder only (30% complete - clone/checkout working, needs full integration per FR-002.1 through FR-002.4). See Phase 8 for detailed subtasks.
- [x] T029 [US2] Implement stopping rule in src/analysis/stopping_rule.py (compute 95% CI with bootstrap, check half-width ≤10% of mean for AUTR/TOK_IN/T_WALL/CRUDe/ESR/MC, min 5 runs, max 25 runs per framework)
- [x] T030 [US2] Implement multi-framework orchestration in src/orchestrator/runner.py (execute_multi_framework: iterate through frameworks, run until stopping rule satisfied for each, collect aggregate metrics)
- [x] T031 [US2] Implement Kruskal-Wallis test in src/analysis/statistics.py (non-parametric test for comparing 3+ groups using scipy.stats.kruskal)
- [x] T032 [US2] Implement Dunn-Šidák post-hoc tests in src/analysis/statistics.py (pairwise comparisons with family-wise error correction)
- [x] T033 [US2] Implement Cliff's delta effect size in src/analysis/statistics.py (proportion of pairs where group1 > group2, scaled to [-1, 1])
- [x] T034 [US2] Implement bootstrap confidence intervals in src/analysis/statistics.py (10,000 resamples, percentile method for 95% CI)
- [x] T035 [US2] Add multi-framework support to run_experiment.sh in runners/run_experiment.sh (when arg="all", execute for baes, chatdev, ghspec sequentially with stopping rule checks)
- [x] T036 [US2] Implement aggregate metrics collector in src/analysis/statistics.py (compute mean/median/std/CI across runs for each framework, identify outliers)

**Checkpoint**: ⚠️ User Story 2 infrastructure complete but CANNOT RUN - framework adapters need completion (Phase 8)

---

## Phase 5: User Story 3 - Verify Reproducibility (Priority: P3)

**Goal**: Validate that experiments produce bit-identical results when re-run with identical configurations

**Independent Test**: Execute same run twice with identical config/experiment.yaml and verify metrics.json, hitl_events.jsonl, token counts match byte-for-byte

### Implementation for User Story 3

- [x] T037 [US3] Implement deterministic seed enforcement in src/orchestrator/config_loader.py (validate random_seed in config, set Python/NumPy seeds before run execution)
- [x] T038 [US3] Implement commit hash verification in src/adapters/base_adapter.py (verify cloned repo SHA matches config before run, fail fast if mismatch)
- [x] T039 [US3] Implement HITL event logger with hashing in src/orchestrator/runner.py (log all HITL events with SHA-1 hash of response text to hitl_events.jsonl)
- [x] T040 [US3] Add reproducibility validation script in tests/integration/test_reproducibility.py (execute run twice, compare metrics.json/hitl_events.jsonl/usage_api.json byte-for-byte)
- [x] T041 [US3] Implement framework version recorder in src/orchestrator/archiver.py (write framework repo SHA to commit.txt in archive)
- [x] T042 [US3] Add determinism checks to config validation in src/orchestrator/config_loader.py (verify temperature=0, top_p=1.0 in framework configs, validate prompts are immutable)

**Checkpoint**: ⚠️ All reproducibility mechanisms in place but UNTESTED - cannot validate without working adapters (Phase 8)

---

## Phase 6: User Story 4 - Analyze Metrics and Generate Reports (Priority: P3)

**Goal**: Generate publication-ready visualizations and statistical summaries from collected run data

**Independent Test**: Run analysis scripts on archived data and verify reports include all required statistical tests and vector visualizations

### Implementation for User Story 4

- [x] T043 [P] [US4] Implement radar chart generator in src/analysis/visualizations.py (6 metrics: AUTR, TOK_IN, T_WALL, CRUDe, ESR, MC with matplotlib polar projection, export SVG)
- [x] T044 [P] [US4] Implement Pareto plot generator in src/analysis/visualizations.py (Q* vs TOK_IN scatter with framework labels, export SVG)
- [x] T045 [P] [US4] Implement timeline chart generator in src/analysis/visualizations.py (CRUD coverage and downtime events over 6 steps, dual-axis plot, export SVG)
- [x] T046 [US4] Implement composite score calculator in src/analysis/statistics.py (Q* = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC, AEI = AUTR / log(1 + TOK_IN))
- [x] T047 [US4] Implement statistical report generator in src/analysis/statistics.py (generate markdown report with tables: mean/median/CI for all metrics, Kruskal-Wallis results, pairwise comparisons with Cliff's δ)
- [x] T048 [US4] Create analysis entry point script in runners/analyze_results.sh (load all runs from runs/{framework}/{run-id}/, compute aggregates, run statistical tests, generate visualizations, output report.md)
- [x] T049 [US4] Implement outlier detection in src/analysis/statistics.py (identify runs >3 standard deviations from median, flag for manual review)

**Checkpoint**: ✅ All analysis and reporting capabilities complete - ready to process data once adapters generate real run results

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T050 [P] Add comprehensive docstrings to all modules (orchestrator, adapters, analysis, utils) following Google style guide
- [x] T051 [P] Create quickstart.md documentation in docs/quickstart.md (prerequisites: Python 3.11+/Docker/Git, installation steps, first run example, expected outputs)
- [x] T052 [P] Create architecture.md documentation in docs/architecture.md (system diagram, adapter pattern explanation, data flow, directory structure)
- [x] T053 [P] Create metrics.md documentation in docs/metrics.md (definitions for all 16 metrics, formulas, interpretation guidelines)
- [x] T054 Add error handling improvements across all modules (specific exception types, helpful error messages with context)
- [x] T055 Add logging coverage to all critical operations (run start/end, step execution, HITL events, validation failures, archival)
- [x] T056 [P] Create troubleshooting guide in docs/troubleshooting.md (common failures: timeout, API quota, disk space, framework crashes with resolution steps)
- [ ] T057 Validate PEP 8 compliance across codebase (run flake8/black, fix style issues, add pre-commit hooks)
- [ ] T058 Add type hints to all function signatures (use Python 3.11+ typing, validate with mypy)
- [ ] T059 Create unit tests for critical utilities in tests/unit/ (test_logger.py, test_config_loader.py, test_isolation.py, test_metrics_collector.py)
- [ ] T060 Create integration tests in tests/integration/ (test_single_run.py: full end-to-end with mock framework, test_stopping_rule.py: convergence behavior)
- [ ] T061 Create contract tests in tests/contract/ (test_adapter_contract.py: verify all adapters implement BaseAdapter interface, test_config_schema.py: YAML validation)
- [ ] T062 Run full experiment cycle end-to-end validation (setup → single run → multi-framework → analysis → verify all outputs)

---

## Phase 8: Framework Adapter Implementation (CRITICAL - REQUIRED FOR REAL EXPERIMENTS)

**Purpose**: Complete framework adapter implementations to enable real experiment execution

**Context**: Tasks T020, T027, T028 are placeholders. This phase provides detailed breakdown to make them functional.

**Status**: ❌ NOT STARTED - This phase is REQUIRED before any real experiments can run

**Recommended Approach**: Complete ChatDev adapter first (most mature, best documented), then replicate pattern for BAEs and GitHub Spec-kit.

### ChatDev Adapter Complete Implementation (Replaces T027)

- [x] T063 [US2] **Research ChatDev Integration** - Run ChatDev standalone manually, document: CLI entry point (run.py or main.py), command-line arguments for task execution, console output format, token logging patterns, HITL detection signals, service architecture (CLI vs API-based), Python/dependency requirements. Create research notes in docs/chatdev_integration.md (Estimated: 2-4 hours)

- [x] T064 [US2] **ChatDev Environment Setup** - Implement in src/adapters/chatdev_adapter.py start() method: Create Python virtual environment at workspace/.venv using subprocess.run([sys.executable, "-m", "venv"]), install ChatDev dependencies from requirements.txt using pip install, verify Python version compatibility, set OPENAI_API_KEY environment variable from config (Estimated: 2-4 hours, implements FR-002.1 step 2-3)

- [x] T065 [US2] **ChatDev Service Management** - Implement service startup (if ChatDev uses persistent API) or validate CLI availability: If API-based, start server process with subprocess.Popen, wait for health check to pass; If CLI-based, verify entry point script exists and is executable. Store process handle in self.process for lifecycle management (Estimated: 4-8 hours, implements FR-002.1 step 4, FR-002.3)

- [x] T066 [US2] **ChatDev Command Execution** - Implement execute_step() method: Construct command with framework entry point, task argument, and configuration; Execute via subprocess.run() with capture_output=True, timeout=STEP_TIMEOUT; Capture stdout/stderr for parsing; Return success boolean based on exit code (Estimated: 4-8 hours, implements FR-002.1 step 5, FR-002.2a)

- [x] T067 [US2] **ChatDev Token Tracking** - Implement _parse_token_usage() method: Scan ChatDev stdout/stderr for token usage patterns using regex (e.g., r'prompt_tokens:\s*(\d+)', r'completion_tokens:\s*(\d+)'); Sum tokens across all API calls in step; If no tokens found in logs, return 0 and rely on OpenAI Usage API verification; Log parsing failures for debugging (Estimated: 4-6 hours, implements FR-002.1 step 6, FR-009.1a)

- [x] T068 [US2] **ChatDev HITL Detection and Injection** - Implement _detect_hitl_events() and handle_hitl() methods: Monitor stdout for HITL patterns (keywords: "clarification", "unclear", "please specify", question marks + pause); On detection, inject fixed response from config/hitl/expanded_spec.txt via stdin or command restart; Compute SHA-1 hash of response; Log HITL event to hitl_events.jsonl; Enforce 2-clarification limit per step (Estimated: 4-6 hours, implements FR-002.1 step 7, FR-004.1, FR-004.2)

- [x] T069 [US2] **ChatDev Health Checks** - Implement health_check() method: If CLI-based, verify entry point script exists and Python process is responsive; If API-based, make HTTP GET to health endpoint; Return boolean; Handle timeouts and connection errors gracefully (Estimated: 2-3 hours, implements FR-002.1 step 8, FR-002.3)

- [x] T070 [US2] **ChatDev Graceful Shutdown** - Implement stop() method: Send SIGTERM to framework process if running; Wait up to 30 seconds for graceful termination; Send SIGKILL if still running; Clean up virtual environment if configured; Log shutdown events (Estimated: 1-2 hours, implements FR-002.1 step 9, FR-002.3)

- [ ] T071 [US2] **ChatDev Single-Step Test** - Create test script tests/integration/test_chatdev_single_step.py: Execute one step with ChatDev adapter; Verify metrics.json created with token counts > 0; Verify workspace contains generated code; Verify no crashes or timeouts (Estimated: 2-4 hours, validates FR-031 steps 1-7)

- [ ] T072 [US2] **ChatDev Six-Step Integration Test** - Execute full six-step run: Run ./runners/run_experiment.sh chatdev; Verify all 6 steps complete; Verify run.tar.gz archive created; Verify metrics cover all steps; Check for HITL events if triggered (Estimated: 2-4 hours, validates FR-031 step 8, User Story 1 acceptance)

- [ ] T073 [US2] **ChatDev Reproducibility Validation** - Run ChatDev twice with identical config: Compare metrics.json for identical token counts; Compare HITL events for identical hashes; Verify archive hashes match if framework is fully deterministic (Estimated: 2-3 hours, validates User Story 3)

**ChatDev Adapter Checkpoint**: ✅ ChatDev adapter fully functional - can execute real experiments

### BAEs Adapter Complete Implementation (Replaces T020)

- [ ] T074 [US1] **Research BAEs Integration** - Analyze BAEs framework structure, document integration requirements same as T063 for ChatDev (Estimated: 2-4 hours)

- [ ] T075 [US1] **BAEs Environment Setup** - Implement same as T064 for BAEs-specific requirements (Estimated: 2-4 hours)

- [ ] T076 [US1] **BAEs Service Management** - Implement same as T065 for BAEs API/CLI pattern (Estimated: 4-8 hours)

- [ ] T077 [US1] **BAEs Command Execution** - Implement same as T066 for BAEs-specific commands (Estimated: 4-8 hours)

- [ ] T078 [US1] **BAEs Token Tracking** - Implement same as T067 with BAEs token logging patterns (Estimated: 4-6 hours)

- [ ] T079 [US1] **BAEs HITL Detection** - Implement same as T068 for BAEs HITL patterns (Estimated: 4-6 hours)

- [ ] T080 [US1] **BAEs Health Checks** - Implement same as T069 for BAEs health monitoring (Estimated: 2-3 hours)

- [ ] T081 [US1] **BAEs Graceful Shutdown** - Implement same as T070 for BAEs cleanup (Estimated: 1-2 hours)

- [ ] T082 [US1] **BAEs Integration Testing** - Execute tests same as T071-T073 for BAEs (Estimated: 6-11 hours)

**BAEs Adapter Checkpoint**: ✅ BAEs adapter fully functional

### GitHub Spec-kit Adapter Complete Implementation (Replaces T028)

- [ ] T083 [US2] **Research GitHub Spec-kit Integration** - Same as T063 for Spec-kit (Estimated: 2-4 hours)

- [ ] T084 [US2] **Spec-kit Environment Setup** - Same as T064 for Spec-kit (Estimated: 2-4 hours)

- [ ] T085 [US2] **Spec-kit Service Management** - Same as T065 for Spec-kit (Estimated: 4-8 hours)

- [ ] T086 [US2] **Spec-kit Command Execution** - Same as T066 for Spec-kit (Estimated: 4-8 hours)

- [ ] T087 [US2] **Spec-kit Token Tracking** - Same as T067 for Spec-kit (Estimated: 4-6 hours)

- [ ] T088 [US2] **Spec-kit HITL Detection** - Same as T068 for Spec-kit (Estimated: 4-6 hours)

- [ ] T089 [US2] **Spec-kit Health Checks** - Same as T069 for Spec-kit (Estimated: 2-3 hours)

- [ ] T090 [US2] **Spec-kit Graceful Shutdown** - Same as T070 for Spec-kit (Estimated: 1-2 hours)

- [ ] T091 [US2] **Spec-kit Integration Testing** - Same as T071-T073 for Spec-kit (Estimated: 6-11 hours)

**GitHub Spec-kit Adapter Checkpoint**: ✅ All three framework adapters functional

### Final Validation

- [ ] T092 **Multi-Framework End-to-End Test** - Execute ./runners/run_experiment.sh all; Verify all three frameworks complete 5+ runs each; Verify stopping rule triggers correctly; Generate analysis with ./runners/analyze_results.sh; Verify statistical reports and visualizations generated (Estimated: 4-8 hours, validates User Stories 2 and 4)

**Phase 8 Complete Checkpoint**: ✅ **SYSTEM FULLY FUNCTIONAL** - Can execute real experiments across all three frameworks

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately ✅ COMPLETE
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories ✅ COMPLETE
- **User Story 1 (Phase 3)**: Depends on Foundational completion - Core functionality ⚠️ INFRASTRUCTURE COMPLETE, ADAPTERS INCOMPLETE
- **User Story 2 (Phase 4)**: Depends on US1 completion - Builds on single-run capability ⚠️ INFRASTRUCTURE COMPLETE, ADAPTERS INCOMPLETE
- **User Story 3 (Phase 5)**: Depends on US1 completion - Can run parallel with US2 ⚠️ INFRASTRUCTURE COMPLETE, UNTESTED
- **User Story 4 (Phase 6)**: Depends on US1+US2 completion - Needs run data ✅ COMPLETE, READY FOR DATA
- **Polish (Phase 7)**: Depends on all user stories - Final quality improvements ⚠️ DOCUMENTATION COMPLETE, TESTS PENDING
- **Adapter Implementation (Phase 8)**: ❌ CRITICAL - REQUIRED TO MAKE SYSTEM FUNCTIONAL - Currently blocks all real experiment execution

### Critical Path to Working System

**Current Status**: 62/92 tasks complete (67%), but system cannot execute real experiments

**Required Next Steps** (in order):

1. **IMMEDIATE**: Complete Phase 8 ChatDev adapter (T063-T073) - 11 tasks, 30-45 hours
   - This enables first working end-to-end experiment
   - Validates infrastructure with real framework integration
   - Provides template for other adapters

2. **SHORT-TERM**: Complete Phase 8 BAEs adapter (T074-T082) - 9 tasks, 23-41 hours
   - Enables BAEs framework testing
   - May require BAEs framework modifications (document carefully)

3. **MEDIUM-TERM**: Complete Phase 8 GitHub Spec-kit adapter (T083-T091) - 9 tasks, 23-41 hours
   - Completes three-framework comparison capability

4. **VALIDATION**: Execute Phase 8 final validation (T092) - 1 task, 4-8 hours
   - Validates entire system end-to-end
   - Confirms multi-framework comparison works

**Total Remaining Work**: 30 tasks, 80-135 hours to full functionality

### Task Execution Strategy

**Parallel Opportunities** (marked with [P]):
- Within each adapter, research can happen in parallel
- Environment setup for different frameworks can overlap
- Documentation tasks can run alongside implementation

**Sequential Requirements**:
- ChatDev adapter MUST complete before BAEs/Spec-kit (provides pattern)
- Each adapter's steps MUST follow order T.1→T.2→T.3...→T.9 (T.10-T.11 validate)
- Multi-framework test (T092) MUST wait for all three adapters

**Recommended Sprint Plan**:
- **Sprint 1** (40-50 hours): ChatDev adapter complete (T063-T073)
- **Sprint 2** (25-45 hours): BAEs adapter complete (T074-T082)
- **Sprint 3** (25-45 hours): Spec-kit adapter complete (T083-T091)
- **Sprint 4** (4-8 hours): Final validation (T092) + remaining Phase 7 tasks

**Alternative: Mock Adapter Path** (not in current tasks):
- If real adapter implementation too resource-intensive
- Create MockAdapter that generates synthetic realistic data
- Allows testing entire pipeline (8-14 hours)
- Validates infrastructure before committing to full adapter work

### User Story Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← CRITICAL: Blocks everything
    ↓
    ├─→ Phase 3 (US1: Single Run) ← MVP Functionality
    │       ↓
    │       ├─→ Phase 4 (US2: Multi-Framework) ← Builds on US1
    │       │
    │       └─→ Phase 5 (US3: Reproducibility) ← Independent of US2
    │
    └─→ (US1 + US2 complete)
            ↓
        Phase 6 (US4: Analysis) ← Needs data from US1+US2
            ↓
        Phase 7 (Polish)
```

### Within Each User Story

- **US1**: Foundation → Metrics/Validation → Adapter → Orchestration → Entry Point → Verification
- **US2**: Additional Adapters → Statistical Analysis → Multi-Framework Logic → Stopping Rule
- **US3**: Determinism Enforcement → Verification → Logging
- **US4**: Visualizations → Statistics → Reporting

### Parallel Opportunities

**Phase 1 (Setup)**: Tasks T003, T004, T005, T006 can run in parallel (different files)

**Phase 2 (Foundational)**: Tasks T008, T009, T010, T012, T013 can run in parallel (different modules)

**Phase 3 (US1)**: 
- T014, T015, T016, T017 can run in parallel (different validation modules)
- T020 (adapter) can start after T009 (base adapter) completes

**Phase 4 (US2)**:
- T027, T028 can run in parallel (different adapters)
- T031, T032, T033, T034 can run in parallel (different statistical methods)

**Phase 6 (US4)**:
- T043, T044, T045 can run in parallel (different visualizations)

**Phase 7 (Polish)**:
- T050, T051, T052, T053, T056 can run in parallel (different documentation files)
- T059, T060, T061 can run in parallel (different test suites)

---

## Parallel Example: Foundational Phase

```bash
# Launch all foundational components together after T007 (logger) completes:
Task T008: "Implement config loader in src/orchestrator/config_loader.py"
Task T009: "Create base adapter in src/adapters/base_adapter.py"
Task T010: "Implement workspace isolation in src/utils/isolation.py"
Task T012: "Create prompt files in config/prompts/"
Task T013: "Create HITL text in config/hitl/expanded_spec.txt"

# T011 (experiment.yaml) depends on T008 completing
# Then US1 can start once all Phase 2 tasks complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. **Complete Phase 1: Setup** (T001-T006) - 1 day
2. **Complete Phase 2: Foundational** (T007-T013) - 2-3 days (CRITICAL PATH)
3. **Complete Phase 3: User Story 1** (T014-T026) - 5-7 days
4. **STOP and VALIDATE**: Execute `./runners/run_experiment.sh baes` end-to-end
5. **Deploy/Demo**: Working single-framework experiment system

**Total MVP Timeline**: ~2 weeks

### Incremental Delivery

1. **Foundation Ready** (Phase 1+2) → ~4 days
2. **Add US1 (Single Run)** → Test independently → **MVP Release** 🎯
3. **Add US2 (Multi-Framework)** → Test independently → **v0.2 Release**
4. **Add US3 (Reproducibility)** → Test independently → **v0.3 Release**
5. **Add US4 (Analysis)** → Test independently → **v1.0 Release**
6. **Polish** → **v1.1 Production Release**

Each story adds value without breaking previous functionality.

### Parallel Team Strategy

With 3 developers after Foundational phase completes:

- **Developer A**: Phase 3 (US1) - Core orchestration
- **Developer B**: Phase 4 (US2) - Multi-framework support (starts after US1 adapters ready)
- **Developer C**: Phase 5 (US3) - Reproducibility mechanisms (parallel with US2)

Developer B+C join US4 after their phases complete.

---

## Task Count Summary

- **Total Tasks**: 62
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 7 tasks ← CRITICAL PATH
- **Phase 3 (US1)**: 13 tasks ← MVP
- **Phase 4 (US2)**: 10 tasks
- **Phase 5 (US3)**: 6 tasks
- **Phase 6 (US4)**: 7 tasks
- **Phase 7 (Polish)**: 13 tasks

**Parallelizable Tasks**: 23 tasks marked [P] (~37% can run in parallel with proper coordination)

**Critical Path**: Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US2) → Phase 6 (US4)

**Suggested MVP Scope**: Phases 1+2+3 (26 tasks) = Single-framework experiment capability

---

## Notes

- **[P] tasks**: Different files, no dependencies - safe to parallelize
- **[Story] labels**: Map each task to specific user story for traceability and independent testing
- **MVP Focus**: Phase 3 (US1) delivers end-to-end single-run capability - highest value
- **Foundational Phase**: Must complete 100% before any user story work begins
- **Tests Optional**: No explicit test tasks per feature spec - can add later if needed
- **Validation Strategy**: Each phase ends with checkpoint to verify story works independently
- **Commit Frequency**: Commit after each task or logical group for atomic progress
- **Constitutional Compliance**: All tasks align with 10 constitutional principles (see plan.md Constitution Check)
