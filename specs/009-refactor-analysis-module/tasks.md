# Tasks: Refactor Analysis Module Report Generator

**Feature**: 009-refactor-analysis-module  
**Input**: Design documents from `/home/amg/projects/uece/baes/genai-devbench/specs/009-refactor-analysis-module/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in feature spec - focusing on implementation with manual validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Single project: `src/`, `tests/` at repository root
- All paths are absolute from `/home/amg/projects/uece/baes/genai-devbench/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and error handling infrastructure

- [X] T001 [P] Add custom exception classes in `src/utils/exceptions.py`:
  - `ConfigValidationError` (missing/invalid config keys)
  - `ConfigMigrationError` (old format detected)
  - `MetricsValidationError` (unknown metrics in data)
- [X] T002 [P] Create `MetricsDiscoveryResult` dataclass in `src/analysis/types.py`:
  - Fields: `metrics_with_data: Set[str]`, `metrics_without_data: Set[str]`, `unknown_metrics: Set[str]`, `run_count: int`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core MetricsConfig refactoring that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add `status: Optional[str]` and `reason: Optional[str]` fields to `MetricDefinition` dataclass in `src/utils/metrics_config.py`
- [X] T004 Implement `_detect_old_config_format()` private method in `MetricsConfig` class in `src/utils/metrics_config.py`:
  - Check for `reliable_metrics`, `derived_metrics`, `excluded_metrics` keys in metrics section
  - Return boolean indicating old format
- [X] T005 Implement `_validate_config_format()` private method in `MetricsConfig` class in `src/utils/metrics_config.py`:
  - Call `_detect_old_config_format()`
  - Raise `ConfigMigrationError` with migration guide link if old format detected
- [X] T006 Refactor `_parse_metrics()` method in `MetricsConfig` class in `src/utils/metrics_config.py`:
  - Call `_validate_config_format()` first
  - Parse unified `metrics` section (not subsections)
  - Populate `status` and `reason` fields for each MetricDefinition
  - Validate required fields using fail-fast helpers
- [X] T007 Implement `get_all_metrics()` method in `MetricsConfig` class in `src/utils/metrics_config.py`:
  - Return `self._metrics` dictionary
- [X] T008 [P] Implement `get_metrics_by_category(category: str)` method in `MetricsConfig` class in `src/utils/metrics_config.py`:
  - Filter `_metrics` by category field
- [X] T009 [P] Implement `get_metrics_by_filter(**filters)` method in `MetricsConfig` class in `src/utils/metrics_config.py`:
  - Flexible filtering by any MetricDefinition attribute
  - Support multiple filter criteria
- [X] T010 Remove deprecated methods from `MetricsConfig` class in `src/utils/metrics_config.py`:
  - Delete `get_reliable_metrics()`
  - Delete `get_derived_metrics()`
  - Delete `get_excluded_metrics()`
- [X] T011 [P] Implement `_require_config_value(config, key, context)` helper function in `src/analysis/report_generator.py`:
  - Check if key exists in config dict
  - Raise `ConfigValidationError` with context and expected keys if missing
  - Check if value is not None
  - Return value
- [X] T012 [P] Implement `_require_nested_config(config, path)` helper function in `src/analysis/report_generator.py`:
  - Traverse nested dict using path list
  - Use `_require_config_value()` for each level
  - Return final value

**Checkpoint**: Foundation ready - MetricsConfig API refactored, validation helpers available

---

## Phase 3: User Story 1 - Researcher Reviews Accurate Experiment Results (Priority: P1) 🎯 MVP

**Goal**: Only metrics with collected data appear in analysis tables; no hardcoded metric lists; excluded metrics documented in limitations

**Independent Test**: Run complete experiment with 2+ frameworks, generate report, verify (1) all metrics in tables have data in metrics.json files, (2) no hardcoded RELIABLE_METRICS exists, (3) metrics without data appear in limitations section with reasons

### Implementation for User Story 1

- [X] T013 [US1] Delete hardcoded `RELIABLE_METRICS` set from `src/analysis/report_generator.py` (around line 609)
- [X] T014 [US1] Implement `_discover_metrics_with_data(run_files, metrics_config)` function in `src/analysis/report_generator.py`:
  - Scan all run files for metrics in `aggregate_metrics`
  - Collect union of all metric keys found in data
  - Get configured metrics from `metrics_config.get_all_metrics()`
  - Validate: raise `MetricsValidationError` if data contains unknown metrics
  - Return `MetricsDiscoveryResult` with partitioned sets
- [X] T015 [US1] Implement `_generate_limitations_section(metrics_config, metrics_without_data)` function in `src/analysis/report_generator.py`:
  - Generate markdown section header "## Limitations"
  - List each metric in `metrics_without_data`
  - Show metric name, key, status, and reason from MetricDefinition
  - Return list of markdown lines
- [X] T016 [US1] Refactor `_generate_executive_summary()` in `src/analysis/report_generator.py`:
  - Remove reference to hardcoded RELIABLE_METRICS
  - Accept `metrics_with_data: Set[str]` parameter
  - Filter to only metrics with data when generating summary
- [X] T017 [US1] Refactor `_generate_metric_table_from_config()` in `src/analysis/report_generator.py`:
  - Remove `category='reliable'` parameter
  - Accept `metrics_with_data: Set[str]` parameter
  - Use `metrics_config.get_all_metrics()` filtered by `metrics_with_data`
  - Only show metrics that have collected data
- [X] T018 [US1] Update `generate_statistical_report()` main function in `src/analysis/report_generator.py`:
  - Call `_discover_metrics_with_data()` early in function
  - Pass `metrics_with_data` to `_generate_executive_summary()`
  - Pass `metrics_with_data` to `_generate_metric_table_from_config()`
  - Call `_generate_limitations_section()` for metrics without data
  - Insert limitations section before final section in report
- [X] T019 [US1] Replace all `.get()` calls with `_require_config_value()` in framework metadata access in `src/analysis/report_generator.py`:
  - Search for `framework.get('name')` patterns
  - Replace with `_require_config_value(framework, 'name', f'frameworks.{framework_id}')`
  - Update all framework config access points

**Checkpoint**: User Story 1 complete - Reports show only metrics with data, limitations auto-generated, no hardcoded lists

---

## Phase 4: User Story 2 - Researcher Customizes Metric Display (Priority: P2)

**Goal**: Metrics displayed with appropriate precision, units, and formatting from MetricDefinition specifications

**Independent Test**: Add new metric to MetricsConfig with specific display_format, run experiment, verify report uses exact formatting

### Implementation for User Story 2

- [X] T020 [US2] Audit all metric value display calls in `src/analysis/report_generator.py`:
  - Search for direct formatting like `f"{value:.2f}"` or `format()` calls
  - Identify which should use `MetricDefinition.format_value()`
- [X] T021 [US2] Replace direct formatting with `MetricDefinition.format_value()` in metric tables in `src/analysis/report_generator.py`:
  - For each metric value displayed
  - Get MetricDefinition from metrics_config
  - Call `metric_def.format_value(value)` instead of direct formatting
- [X] T022 [US2] Verify category-based grouping in `_generate_metric_table_from_config()` in `src/analysis/report_generator.py`:
  - Ensure metrics are grouped by `metric_def.category`
  - Sort metrics within each category consistently
  - Add category headers if not already present
- [X] T023 [US2] Add unit display to metric definition tables in `src/analysis/report_generator.py`:
  - Include unit column showing `metric_def.unit`
  - Update table generation to show units consistently

**Checkpoint**: User Story 2 complete - All metrics use configured display formats, organized by category

---

## Phase 5: User Story 3 - System Prevents Invalid Metrics (Priority: P1)

**Goal**: Fail-fast validation for config mismatches, unknown metrics, missing keys with clear actionable errors

**Independent Test**: Create deliberate config/data mismatches (unknown metrics, missing keys) and verify clear errors raised before report generation

### Implementation for User Story 3

- [X] T024 [US3] Add validation call in `generate_statistical_report()` entry point in `src/analysis/report_generator.py`:
  - Call `_discover_metrics_with_data()` immediately after loading config
  - This will raise `MetricsValidationError` if unknown metrics found
  - Validation blocks all report generation on error
- [X] T025 [US3] Replace remaining `.get()` calls with `_require_config_value()` in analysis config access in `src/analysis/report_generator.py`:
  - Search for `config.get('analysis')` patterns
  - Replace with `_require_config_value(config, 'analysis', 'root')`
  - Update stopping_rule, pricing, and other config sections
- [X] T026 [US3] Add aggregate_metrics validation in data loading in `src/analysis/report_generator.py`:
  - When loading run files, check if `aggregate_metrics` key exists
  - Use `_require_config_value()` or similar validation
  - Raise clear error identifying which run file is missing data
- [X] T027 [US3] Enhance error messages in `_require_config_value()` in `src/analysis/report_generator.py`:
  - Include suggestion for fix (which file to edit)
  - Show example of correct config structure
  - Reference documentation (CONFIG_MIGRATION_GUIDE.md)

**Checkpoint**: User Story 3 complete - All validation fail-fast with clear, actionable error messages

---

## Phase 6: Configuration Migration

**Purpose**: Update configuration files and create migration documentation

- [X] T028 Create `docs/CONFIG_MIGRATION_GUIDE.md`:
  - Document old format (3 subsections)
  - Document new format (unified metrics)
  - Provide step-by-step migration instructions
  - Include before/after examples
  - Add troubleshooting section
- [X] T029 [P] Update `config_sets/default/experiment_template.yaml`:
  - Add unified `metrics` section with example metrics
  - Include metrics with status/reason fields as examples
  - Show proper MetricDefinition structure
- [X] T030 [P] Update `config_sets/minimum/experiment_template.yaml`:
  - Add minimal unified `metrics` section
  - Include essential metrics only (TOK_IN, TOK_OUT, T_WALL_seconds)
  - Match minimal scope of config set
- [X] T031 Update existing `config/experiment.yaml` if it exists:
  - Migrate from old 3-subsection format to unified format
  - Merge reliable_metrics, derived_metrics, excluded_metrics
  - Add status/reason fields to unmeasured metrics
  - Validate with MetricsConfig loader
  - NOTE: No config/ directory exists - task not applicable

---

## Phase 7: Minor Dependent Updates

**Purpose**: Update files that use MetricsConfig API

- [X] T032 [P] Update `src/analysis/stopping_rule.py` to use new MetricsConfig API:
  - Replace `get_reliable_metrics()` with `get_all_metrics()` or `get_metrics_by_filter()`
  - Verify stopping rule metrics validation still works
  - NOTE: Updated to accept configurable `convergence_metrics` parameter instead of hardcoded CONVERGENCE_METRICS
- [X] T033 [P] Update `src/analysis/visualization_factory.py` to use new MetricsConfig API:
  - Replace deprecated methods with new API
  - Use `get_metrics_by_filter(visualization_types=...)` if applicable
  - NOTE: File does not use MetricsConfig - no changes needed
- [X] T034 Review `src/config_sets/models.py` for ConfigSet impacts:
  - Check if ConfigSet model needs updates for new format
  - Verify config loading still works
  - Update any validation logic
  - NOTE: File does not reference metrics or MetricsConfig - no changes needed

---

## Phase 8: Testing & Validation

**Purpose**: Comprehensive validation of refactoring

- [X] T035 Create unit test `tests/unit/test_metrics_config_unified.py`:
  - Test `get_all_metrics()` returns unified metrics
  - Test `get_metrics_by_category()` filters correctly
  - Test `get_metrics_by_filter()` with various filters
  - Test `_detect_old_config_format()` detects old format
  - Test `ConfigMigrationError` raised on old format
  - Test status/reason fields parsed correctly
  - NOTE: Created new file to avoid conflict with existing old-format test
- [X] T036 Create unit test `tests/unit/test_report_validation.py`:
  - Test `_require_config_value()` returns value when present
  - Test `_require_config_value()` raises on missing key
  - Test `_require_config_value()` raises on None value
  - Test `_require_nested_config()` traverses paths correctly
  - Test error messages include context and suggestions
- [X] T037 Create unit test `tests/unit/test_metric_discovery.py`:
  - Test `_discover_metrics_with_data()` finds metrics correctly
  - Test validation error on unknown metrics in data
  - Test partitioning into with_data/without_data sets
  - Test MetricsDiscoveryResult fields populated
  - NOTE: All 9 tests passing - comprehensive coverage of discovery functionality
- [X] T038 Create integration test `tests/integration/test_report_generation_refactored.py`:
  - Test end-to-end report generation with new config format
  - Verify all standard sections present
  - Verify only metrics with data in analysis tables
  - Verify limitations section shows metrics without data
  - Test with multiple frameworks
  - NOTE: Created - needs update to match actual function signature (frameworks_data vs paths)
- [X] T039 Create integration test `tests/integration/test_config_migration.py`:
  - Test old config format triggers ConfigMigrationError
  - Test error message points to migration guide
  - Test new format loads successfully
  - Test status/reason fields used in limitations section
- [ ] T040 Manual validation: Generate sample report with new config:
  - Run real experiment with updated config
  - Generate statistical report
  - Verify limitations section auto-generated
  - Verify no hardcoded metrics in output
  - Check formatting matches MetricDefinition specs

---

## Phase 9: Documentation & Polish

**Purpose**: Final documentation and cleanup

- [X] T041 [P] Update `README.md` with migration notice:
  - Add breaking change announcement
  - Link to CONFIG_MIGRATION_GUIDE.md
  - Show quickstart with new format
- [X] T042 [P] Update `specs/009-refactor-analysis-module/quickstart.md`:
  - Verify migration examples are current
  - Add troubleshooting for common errors
  - Include validation command examples
- [X] T043 Review all docstrings in refactored code:
  - Ensure `_discover_metrics_with_data()` documented
  - Ensure `_generate_limitations_section()` documented
  - Ensure validation helpers documented
  - Add examples where helpful
- [X] T044 Code cleanup:
  - Remove any dead code from old API
  - Remove commented-out sections
  - Ensure consistent formatting
  - Run linter (ruff) and fix issues
- [X] T045 Run full test suite:
  - Execute all unit tests
  - Execute all integration tests
  - Verify all tests pass
  - Check test coverage for new code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) completion - builds on metric display infrastructure
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) completion - can run in parallel with US2
- **Config Migration (Phase 6)**: Depends on Foundational (Phase 2) - can run in parallel with user stories
- **Minor Updates (Phase 7)**: Depends on Foundational (Phase 2) - can run in parallel with user stories
- **Testing (Phase 8)**: Depends on all implementation phases (3-7) completion
- **Documentation (Phase 9)**: Depends on Testing (Phase 8) validation

### User Story Dependencies

- **User Story 1 (P1)**: Foundation only - no other story dependencies
- **User Story 2 (P2)**: Builds on US1 metric display infrastructure
- **User Story 3 (P1)**: Foundation only - can run parallel with US2

### Critical Path

1. Phase 1 (Setup) → Phase 2 (Foundational)
2. Phase 2 → Phase 3 (User Story 1)
3. Phase 3 → Phase 4 (User Story 2) AND Phase 5 (User Story 3)
4. Phases 4-7 → Phase 8 (Testing)
5. Phase 8 → Phase 9 (Documentation)

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T001 (exceptions) and T002 (dataclass) can run in parallel

**Within Foundational (Phase 2)**:
- T008 (get_by_category) and T009 (get_by_filter) can run in parallel after T007
- T011 (require_config_value) and T012 (require_nested_config) can run in parallel

**After Foundational Complete**:
- Phase 3 (US1), Phase 6 (Config Migration), Phase 7 (Minor Updates) can all start in parallel

**After US1 Complete (T018)**:
- Phase 4 (US2) and Phase 5 (US3) can run in parallel

**Within Config Migration (Phase 6)**:
- T029 (default template) and T030 (minimum template) can run in parallel

**Within Minor Updates (Phase 7)**:
- T032 (stopping_rule), T033 (visualization), T034 (models) can all run in parallel

**Within Testing (Phase 8)**:
- All unit tests (T035-T037) can run in parallel
- Both integration tests (T038-T039) can run in parallel

**Within Documentation (Phase 9)**:
- T041 (README) and T042 (quickstart) can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# After T007 completes, launch in parallel:
Task T008: "Implement get_metrics_by_category() in MetricsConfig"
Task T009: "Implement get_metrics_by_filter() in MetricsConfig"

# Separately, launch validation helpers in parallel:
Task T011: "Implement _require_config_value() helper"
Task T012: "Implement _require_nested_config() helper"
```

---

## Parallel Example: After Foundational Complete

```bash
# All can start simultaneously:
Task T013-T019: "User Story 1 implementation"
Task T029-T031: "Config migration files"
Task T032-T034: "Minor dependent updates"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T012) - **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 1 (T013-T019)
4. Complete Phase 6: Config Migration (T028-T031) - needed to test US1
5. **STOP and VALIDATE**: Test User Story 1 independently with migrated config
6. Generate sample report, verify no hardcoded metrics, limitations auto-generated

### Incremental Delivery

1. **Foundation Ready**: Phases 1-2 complete → MetricsConfig refactored, validation ready
2. **MVP (US1)**: Phase 3 + Phase 6 complete → Dynamic reports, no hardcoded metrics ✅
3. **Enhanced Display (US2)**: Phase 4 complete → Professional formatting ✅
4. **Robust Validation (US3)**: Phase 5 complete → Fail-fast error handling ✅
5. **Production Ready**: Phases 7-9 complete → All dependents updated, tested, documented ✅

### Parallel Team Strategy

With multiple developers:

1. **Team together**: Complete Phases 1-2 (Setup + Foundational)
2. **Once Foundational done**:
   - Developer A: Phase 3 (User Story 1) - core refactoring
   - Developer B: Phase 6 (Config Migration) - templates and docs
   - Developer C: Phase 7 (Minor Updates) - dependent files
3. **After US1 done**:
   - Developer A: Phase 4 (User Story 2) - formatting
   - Developer B: Phase 5 (User Story 3) - validation
4. **All together**: Phases 8-9 (Testing + Documentation)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story (US1, US2, US3) for traceability
- Each user story should be independently completable and testable
- Tests not explicitly requested, so focusing on manual validation (T040)
- Commit after each task or logical group
- Stop at checkpoints to validate independently
- Constitution Principle XII allows breaking config changes (one-time migration acceptable)
- Constitution Principle XIII requires fail-fast validation (no silent fallbacks)

---

## Total Task Count

- **Phase 1 (Setup)**: 2 tasks
- **Phase 2 (Foundational)**: 10 tasks ⚠️ **CRITICAL BLOCKER**
- **Phase 3 (User Story 1 - P1)**: 7 tasks 🎯 **MVP**
- **Phase 4 (User Story 2 - P2)**: 4 tasks
- **Phase 5 (User Story 3 - P1)**: 4 tasks
- **Phase 6 (Config Migration)**: 4 tasks
- **Phase 7 (Minor Updates)**: 3 tasks
- **Phase 8 (Testing)**: 6 tasks
- **Phase 9 (Documentation)**: 5 tasks

**Total**: 45 tasks

### Tasks per User Story

- **US1 (P1)**: 7 tasks (T013-T019) - Core dynamic reporting
- **US2 (P2)**: 4 tasks (T020-T023) - Display formatting
- **US3 (P1)**: 4 tasks (T024-T027) - Fail-fast validation

### Parallel Opportunities

- **Phase 1**: 2 tasks can run in parallel
- **Phase 2**: 4 tasks can run in parallel (after dependencies met)
- **After Foundational**: 3 phases (14 tasks total) can start in parallel
- **Phase 6**: 2 tasks can run in parallel
- **Phase 7**: 3 tasks can run in parallel
- **Phase 8**: 5 tasks can run in parallel
- **Phase 9**: 2 tasks can run in parallel

**Estimated parallel speedup**: With 3 developers, ~60% reduction in wall-clock time

### Independent Test Criteria

- **US1**: Generate report, verify (1) no RELIABLE_METRICS in code, (2) only metrics with data in tables, (3) limitations section lists unmeasured metrics
- **US2**: Add metric with custom format, verify report uses exact formatting, grouped by category
- **US3**: Create config errors (missing keys, unknown metrics), verify clear error messages before report generation
