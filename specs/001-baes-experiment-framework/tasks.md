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

- [ ] T001 Create project directory structure: config/, src/{orchestrator,adapters,analysis,utils}/, tests/{unit,integration,contract}/, runners/, runs/
- [ ] T002 Initialize Python project with requirements.txt (PyYAML==6.0.1, requests==2.31.0, pytest==7.4.3)
- [ ] T003 [P] Create .env.example with template API key variables (OPENAI_API_KEY_BAES, OPENAI_API_KEY_CHATDEV, OPENAI_API_KEY_GHSPEC)
- [ ] T004 [P] Create .gitignore (runs/, .env, __pycache__, *.pyc, venv/)
- [ ] T005 [P] Create LICENSE file (CC BY 4.0)
- [ ] T006 [P] Create README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Implement structured JSON logger in src/utils/logger.py (JSONFormatter with timestamp, run_id, framework, step, event, metadata fields)
- [ ] T008 [P] Implement configuration loader in src/orchestrator/config_loader.py (load/validate experiment.yaml schema, validate all required keys)
- [ ] T009 [P] Create base adapter abstract class in src/adapters/base_adapter.py (@abstractmethod: start, execute_step, health_check, handle_hitl, stop)
- [ ] T010 [P] Implement workspace isolation utilities in src/utils/isolation.py (create_isolated_workspace, cleanup_workspace with UUID run_id)
- [ ] T011 Create experiment.yaml configuration template in config/experiment.yaml (frameworks: {baes, chatdev, ghspec} with repo_url, commit_hash, api_port, ui_port, api_key_env; stopping_rule; timeouts)
- [ ] T012 [P] Create six-step scenario prompt files in config/prompts/ (step_1.txt: "Create Student/Course/Teacher CRUD app", step_2.txt: "Add enrollment", step_3.txt: "Add teacher assignment", step_4.txt: "Add validation", step_5.txt: "Add pagination", step_6.txt: "Add comprehensive UI")
- [ ] T013 [P] Create fixed HITL clarification text in config/hitl/expanded_spec.txt (deterministic expanded specification for all frameworks)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Single Framework Run (Priority: P1) 🎯 MVP

**Goal**: Execute a complete six-step experiment run for one framework, collecting metrics and archiving artifacts

**Independent Test**: Run `./runners/run_experiment.sh baes` and verify all six steps complete with metrics.json, archived run.tar.gz, and health checks passed

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement metrics collector in src/orchestrator/metrics_collector.py (collect UTT, HIT, AUTR, HEU, TOK_IN, TOK_OUT, T_WALL with UTC timestamps)
- [ ] T015 [P] [US1] Implement API validator in src/orchestrator/validator.py (test_crud_endpoints for Student/Course/Teacher POST/GET/PATCH/DELETE, test_relational_endpoints for enroll/assign)
- [ ] T016 [P] [US1] Implement UI validator in src/orchestrator/validator.py (test_ui_pages for HTTP 200 checks and HTML content labels)
- [ ] T017 [P] [US1] Implement downtime probe in src/orchestrator/validator.py (health_check_loop with 5-second interval, increment ZDI on non-200)
- [ ] T018 [US1] Implement quality metrics calculator in src/orchestrator/metrics_collector.py (CRUDe 0-12 scale, ESR 0-1, MC 0-1, ZDI count, Q* composite, AEI composite)
- [ ] T019 [US1] Implement archiver in src/orchestrator/archiver.py (create run.tar.gz with workspace/metrics/logs, compute SHA-256 hash, store in metadata.json, delete workspace after archival)
- [ ] T020 [US1] Implement BAEs adapter in src/adapters/baes_adapter.py (inherits BaseAdapter, implements start: clone repo at commit_hash, execute_step: send command via API, health_check: HTTP GET api_port/health, handle_hitl: return fixed text from config, stop: graceful shutdown)
- [ ] T021 [US1] Implement timeout enforcement in src/orchestrator/runner.py (10-minute alarm per step, SIGTERM → wait 30s → SIGKILL on timeout, mark run as "timeout failure")
- [ ] T022 [US1] Implement retry logic in src/orchestrator/runner.py (r=2 automatic retries on step failure with exponential backoff, mark run as "failed" after retries exhausted)
- [ ] T023 [US1] Implement main run orchestration in src/orchestrator/runner.py (execute_single_run: initialize run_id, create workspace, load config, initialize adapter, execute 6 steps sequentially, collect metrics after each step, run validations, handle HITL, finalize and archive)
- [ ] T024 [US1] Create run_experiment.sh entry point in runners/run_experiment.sh (parse args: baes|chatdev|ghspec|all, setup venv, install deps, invoke orchestrator with framework arg, handle errors)
- [ ] T025 [US1] Implement OpenAI Usage API client in src/utils/api_client.py (verify_token_counts with exponential backoff retry, compare local vs API counts, log discrepancies)
- [ ] T026 [US1] Add usage API verification to run finalization in src/orchestrator/runner.py (call api_client after metrics collection, store results in usage_api.json)

**Checkpoint**: At this point, User Story 1 should be fully functional - can execute single framework run end-to-end

---

## Phase 4: User Story 2 - Compare Multiple Frameworks (Priority: P2)

**Goal**: Execute runs for all three frameworks with confidence-based stopping rule until statistical significance achieved

**Independent Test**: Run `./runners/run_experiment.sh all` and verify stopping rule terminates when CI ≤10% half-width for all metrics across all frameworks

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement ChatDev adapter in src/adapters/chatdev_adapter.py (inherits BaseAdapter, implements all abstract methods for ChatDev-specific CLI/API)
- [ ] T028 [P] [US2] Implement GitHub Spec-kit adapter in src/adapters/ghspec_adapter.py (inherits BaseAdapter, implements all abstract methods for Spec-kit-specific CLI/API)
- [ ] T029 [US2] Implement stopping rule in src/analysis/stopping_rule.py (compute 95% CI with bootstrap, check half-width ≤10% of mean for AUTR/TOK_IN/T_WALL/CRUDe/ESR/MC, min 5 runs, max 25 runs per framework)
- [ ] T030 [US2] Implement multi-framework orchestration in src/orchestrator/runner.py (execute_multi_framework: iterate through frameworks, run until stopping rule satisfied for each, collect aggregate metrics)
- [ ] T031 [US2] Implement Kruskal-Wallis test in src/analysis/statistics.py (non-parametric test for comparing 3+ groups using scipy.stats.kruskal)
- [ ] T032 [US2] Implement Dunn-Šidák post-hoc tests in src/analysis/statistics.py (pairwise comparisons with family-wise error correction)
- [ ] T033 [US2] Implement Cliff's delta effect size in src/analysis/statistics.py (proportion of pairs where group1 > group2, scaled to [-1, 1])
- [ ] T034 [US2] Implement bootstrap confidence intervals in src/analysis/statistics.py (10,000 resamples, percentile method for 95% CI)
- [ ] T035 [US2] Add multi-framework support to run_experiment.sh in runners/run_experiment.sh (when arg="all", execute for baes, chatdev, ghspec sequentially with stopping rule checks)
- [ ] T036 [US2] Implement aggregate metrics collector in src/analysis/statistics.py (compute mean/median/std/CI across runs for each framework, identify outliers)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - can execute multi-framework comparison with statistical stopping

---

## Phase 5: User Story 3 - Verify Reproducibility (Priority: P3)

**Goal**: Validate that experiments produce bit-identical results when re-run with identical configurations

**Independent Test**: Execute same run twice with identical config/experiment.yaml and verify metrics.json, hitl_events.jsonl, token counts match byte-for-byte

### Implementation for User Story 3

- [ ] T037 [US3] Implement deterministic seed enforcement in src/orchestrator/config_loader.py (validate random_seed in config, set Python/NumPy seeds before run execution)
- [ ] T038 [US3] Implement commit hash verification in src/adapters/base_adapter.py (verify cloned repo SHA matches config before run, fail fast if mismatch)
- [ ] T039 [US3] Implement HITL event logger with hashing in src/orchestrator/runner.py (log all HITL events with SHA-1 hash of response text to hitl_events.jsonl)
- [ ] T040 [US3] Add reproducibility validation script in tests/integration/test_reproducibility.py (execute run twice, compare metrics.json/hitl_events.jsonl/usage_api.json byte-for-byte)
- [ ] T041 [US3] Implement framework version recorder in src/orchestrator/archiver.py (write framework repo SHA to commit.txt in archive)
- [ ] T042 [US3] Add determinism checks to config validation in src/orchestrator/config_loader.py (verify temperature=0, top_p=1.0 in framework configs, validate prompts are immutable)

**Checkpoint**: All reproducibility mechanisms in place - experiments produce identical results on reruns

---

## Phase 6: User Story 4 - Analyze Metrics and Generate Reports (Priority: P3)

**Goal**: Generate publication-ready visualizations and statistical summaries from collected run data

**Independent Test**: Run analysis scripts on archived data and verify reports include all required statistical tests and vector visualizations

### Implementation for User Story 4

- [ ] T043 [P] [US4] Implement radar chart generator in src/analysis/visualizations.py (6 metrics: AUTR, TOK_IN, T_WALL, CRUDe, ESR, MC with matplotlib polar projection, export SVG)
- [ ] T044 [P] [US4] Implement Pareto plot generator in src/analysis/visualizations.py (Q* vs TOK_IN scatter with framework labels, export SVG)
- [ ] T045 [P] [US4] Implement timeline chart generator in src/analysis/visualizations.py (CRUD coverage and downtime events over 6 steps, dual-axis plot, export SVG)
- [ ] T046 [US4] Implement composite score calculator in src/analysis/statistics.py (Q* = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC, AEI = AUTR / log(1 + TOK_IN))
- [ ] T047 [US4] Implement statistical report generator in src/analysis/statistics.py (generate markdown report with tables: mean/median/CI for all metrics, Kruskal-Wallis results, pairwise comparisons with Cliff's δ)
- [ ] T048 [US4] Create analysis entry point script in runners/analyze_results.sh (load all runs from runs/{framework}/{run-id}/, compute aggregates, run statistical tests, generate visualizations, output report.md)
- [ ] T049 [US4] Implement outlier detection in src/analysis/statistics.py (identify runs >3 standard deviations from median, flag for manual review)

**Checkpoint**: All analysis and reporting capabilities complete - can generate publication-ready outputs

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Add comprehensive docstrings to all modules (orchestrator, adapters, analysis, utils) following Google style guide
- [ ] T051 [P] Create quickstart.md documentation in docs/quickstart.md (prerequisites: Python 3.11+/Docker/Git, installation steps, first run example, expected outputs)
- [ ] T052 [P] Create architecture.md documentation in docs/architecture.md (system diagram, adapter pattern explanation, data flow, directory structure)
- [ ] T053 [P] Create metrics.md documentation in docs/metrics.md (definitions for all 16 metrics, formulas, interpretation guidelines)
- [ ] T054 Add error handling improvements across all modules (specific exception types, helpful error messages with context)
- [ ] T055 Add logging coverage to all critical operations (run start/end, step execution, HITL events, validation failures, archival)
- [ ] T056 [P] Create troubleshooting guide in docs/troubleshooting.md (common failures: timeout, API quota, disk space, framework crashes with resolution steps)
- [ ] T057 Validate PEP 8 compliance across codebase (run flake8/black, fix style issues, add pre-commit hooks)
- [ ] T058 Add type hints to all function signatures (use Python 3.11+ typing, validate with mypy)
- [ ] T059 Create unit tests for critical utilities in tests/unit/ (test_logger.py, test_config_loader.py, test_isolation.py, test_metrics_collector.py)
- [ ] T060 Create integration tests in tests/integration/ (test_single_run.py: full end-to-end with mock framework, test_stopping_rule.py: convergence behavior)
- [ ] T061 Create contract tests in tests/contract/ (test_adapter_contract.py: verify all adapters implement BaseAdapter interface, test_config_schema.py: YAML validation)
- [ ] T062 Run full experiment cycle end-to-end validation (setup → single run → multi-framework → analysis → verify all outputs)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - Core functionality
- **User Story 2 (Phase 4)**: Depends on US1 completion - Builds on single-run capability
- **User Story 3 (Phase 5)**: Depends on US1 completion - Can run parallel with US2
- **User Story 4 (Phase 6)**: Depends on US1+US2 completion - Needs run data
- **Polish (Phase 7)**: Depends on all user stories - Final quality improvements

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
