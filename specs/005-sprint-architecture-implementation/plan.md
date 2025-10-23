````markdown
# Implementation Plan: Sprint-Based Directory Architecture

**Branch**: `005-sprint-architecture-implementation` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-sprint-architecture-implementation/spec.md`

**Note**: This plan follows the SpecKit planning workflow for implementing the sprint-based directory architecture.

## Summary

Implement a sprint-based directory architecture that creates isolated directories for each scenario step (sprint), enabling tracking of incremental code evolution, per-sprint metrics, independent validation, and proper failure isolation. Each sprint builds on the previous sprint's artifacts, creating a complete versioned system. This enables researchers to compare framework performance across incremental development cycles, debug sprint-specific failures, analyze code evolution, and measure token efficiency per sprint.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: PyYAML (existing), pathlib (stdlib), json (stdlib), shutil (stdlib)  
**Storage**: File system (POSIX-compliant with symlink support), JSON files for metadata/metrics  
**Testing**: pytest (existing test suite)  
**Target Platform**: Linux/macOS servers (POSIX file systems)  
**Project Type**: Single Python project - extending existing orchestration system  
**Performance Goals**: 
- Sprint directory creation: < 100ms per sprint
- Symlink creation: < 10ms
- README generation: < 500ms
- Total overhead per sprint: < 1 second

**Constraints**: 
- Must not modify framework internals (BAeS/ChatDev/GHSpec)
- Must support concurrent runs (different run_ids)
- Sequential sprint execution only (no parallel sprints within same run)
**Constraints**: 
- Must not modify framework internals (BAeS/ChatDev/GHSpec)
- No backward compatibility burden: new runs use the sprint-based structure and the
    orchestrator will NOT implement runtime compatibility fallbacks. Historical run
    analysis is provided via separate migration/analysis utilities where required.
- Must support concurrent runs (different run_ids)
- Sequential sprint execution only (no parallel sprints within same run)

**Scale/Scope**: 
- Up to 999 sprints per run (3-digit numbering)
- 3 frameworks × multiple experiments × multiple runs
- Typical scenario: 2-5 sprints per run
- Storage: ~500KB-2MB per sprint (depending on generated code size)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with BAEs Experiment Constitution v1.2.0:

- [x] **Scientific Reproducibility**: Yes - Sprint execution is deterministic; all sprints use same seeds/config as existing system. No new randomness introduced.
- [x] **Clarity & Transparency**: Yes - All sprint metadata uses structured JSON. Code will be thoroughly documented. Clear directory naming (sprint_NNN).
- [x] **Open Science**: Yes - No new dependencies. All code CC BY 4.0. Public artifacts.
- [x] **Minimal Dependencies**: Yes - Uses only stdlib (pathlib, json, shutil) + existing PyYAML. No new external dependencies.
- [x] **Deterministic HITL**: Yes - No changes to HITL system. Existing deterministic behavior preserved.
- [x] **Reproducible Metrics**: Yes - Per-sprint metrics use same calculation as existing. Cumulative metrics are simple sums. OpenAI API verification unchanged.
- [x] **Version Control Integrity**: Yes - No changes to framework pinning. Sprint architecture is orchestrator-level only.
- [x] **Automation-First**: Yes - `run_experiment.sh` unchanged. Sprint creation fully automated. No manual steps.
- [x] **Failure Isolation**: Yes - Enhanced! Each sprint gets isolated directory. Failed sprints don't contaminate successful ones.
- [x] **Educational Accessibility**: Yes - Clear documentation will be provided. Sprint concept is intuitive (agile terminology). README generation aids understanding.
- [x] **DRY Principle**: Yes - Shared utilities in `BaseAdapter` and `isolation.py`. No code duplication. Previous fixes (see DRY_REFACTORING.md) extracted common patterns. New sprint code follows same DRY approach.
- [x] **No Backward Compatibility Burden**: Yes - Sprint architecture is additive change. Old single-workspace experiments can be reproduced by checking out commits before this feature. No migration required since each experiment is independent git repository.
- [x] **Fail-Fast Philosophy**: Yes - Missing sprint directories raise exceptions. Invalid metadata JSON aborts run. No silent fallbacks or default values. Clear error messages with absolute paths.

**Gate Status**: ✅ PASS - No constitution violations. All 13 principles satisfied.

## Project Structure

### Documentation (this feature)

```
specs/005-sprint-architecture-implementation/
├── plan.md              # This file - implementation plan
├── spec.md              # Feature specification
├── research.md          # Phase 0: Research findings (to be generated)
├── data-model.md        # Phase 1: Data structures (to be generated)
├── quickstart.md        # Phase 1: Usage guide (to be generated)
├── contracts/           # Phase 1: API contracts (to be generated)
│   ├── sprint_metadata_schema.json
│   ├── sprint_metrics_schema.json
│   └── cumulative_metrics_schema.json
└── tasks.md             # Phase 2: Implementation tasks (via /speckit.tasks)
```

### Source Code (repository root)

```
src/
├── utils/
│   ├── isolation.py                 # MODIFY: Add sprint workspace creation functions
│   │                                #   - create_sprint_workspace()
│   │                                #   - get_previous_sprint_artifacts()
│   └── experiment_paths.py          # NO CHANGE: Uses existing run_dir logic
│
├── adapters/
│   ├── base_adapter.py              # MODIFY: Add sprint awareness
│   │                                #   - Add sprint_num parameter
│   │                                #   - Add previous_sprint_artifacts property
│   │                                #   - Add sprint_log_dir property
│   ├── baes_adapter.py              # MODIFY: Update __init__ signature
│   ├── chatdev_adapter.py           # MODIFY: Update __init__ signature  
│   └── ghspec_adapter.py            # MODIFY: Update __init__ signature
│
├── orchestrator/
│   ├── runner.py                    # MAJOR MODIFY: Sprint execution loop
│   │                                #   - Replace single workspace with sprint loop
│   │                                #   - Add sprint metadata/metrics saving
│   │                                #   - Add failure handling logic
│   │                                #   - Add cumulative metrics calculation
│   │                                #   - Add README generation
│   │                                #   - Add final symlink creation
│   ├── metrics_collector.py         # NO CHANGE: Existing per-step metrics work
│   ├── validator.py                 # NO CHANGE: Existing validation works per sprint
│   └── archiver.py                  # MODIFY: Support sprint-based archiving modes
│
└── config/
    └── experiment.yaml              # MODIFY: Add archiving configuration options

tests/
├── unit/
│   ├── test_sprint_workspace.py     # NEW: Test sprint directory creation
│   ├── test_sprint_context.py       # NEW: Test previous artifact passing
│   └── test_cumulative_metrics.py   # NEW: Test metrics aggregation
│
└── integration/
    ├── test_multi_sprint_run.py     # NEW: End-to-end multi-sprint test
    └── test_sprint_failure.py       # NEW: Test failure handling

docs/workspace_generation_fix/
└── SPRINT_ARCHITECTURE_DESIGN.md   # EXISTING: Design reference document
```

**Structure Decision**: Single Python project extension. Core changes in `src/utils/isolation.py` (sprint workspace creation), `src/adapters/base_adapter.py` (sprint awareness), and `src/orchestrator/runner.py` (sprint execution loop). All three frameworks updated consistently. Tests cover unit (individual functions) and integration (full sprint runs).

## Complexity Tracking

*No constitution violations - this section intentionally left minimal.*

This feature actually **reduces** complexity by:
- Improving failure isolation (each sprint independent)
- Eliminating artifact overwriting bug
- Making debugging simpler (clear sprint boundaries)
- Following existing patterns (uses current workspace isolation model)

No complexity trade-offs required - this is a natural extension of existing architecture.

---

## Phase 0: Research & Analysis

### Research Questions

1. **Current Implementation Analysis**
   - How does `runner.py` currently execute steps?
   - Where is workspace_path set and passed to adapters?
   - How are metrics currently collected per step?
   - How does validation currently work?

2. **Framework Context Passing**
   - How does BAeS handle incremental prompts?
   - How does ChatDev's WareHouse pattern work?
   - How does GHSpec pass context between phases?

3. **File System Best Practices**
   - Symlink handling across platforms
   - Directory structure conventions
   - JSON schema best practices for metadata

4. **Storage Optimization**
   - Typical generated code sizes per framework
   - Compression ratios for intermediate sprints
   - Archive strategy trade-offs

### Research Tasks

| Task ID | Research Area | Output Location |
|---------|--------------|-----------------|
| R1 | Analyze `runner.py` step execution loop | `research.md` §1 |
| R2 | Document current adapter initialization | `research.md` §2 |
| R3 | Study framework-specific context mechanisms | `research.md` §3 |
| R4 | Research POSIX symlink best practices | `research.md` §4 |
| R5 | Measure existing run artifact sizes | `research.md` §5 |
| R6 | Review JSON schema standards for metrics | `research.md` §6 |

**Output**: `research.md` with all findings documented

---

## Phase 1: Design & Contracts

### Data Model

**Entities to define in `data-model.md`:**

1. **SprintMetadata**
   - Fields: sprint_number, step_id, step_name, description, framework, started_at, completed_at, status, error (optional)
   - Relationships: Part of Run
   - Validation: sprint_number > 0, status in [success, failed, timeout]

2. **SprintMetrics**
   - Fields: sprint_number, step_id, tokens (input/output/cached/total), api_calls, execution_time_seconds, hitl_interactions, retry_count
   - Relationships: Belongs to Sprint
   - Validation: All numeric fields >= 0

3. **SprintValidation**
   - Fields: sprint_number, validated_at, overall_status, checks (dict), issues (list), completeness
   - Relationships: Belongs to Sprint
   - Validation: overall_status in [passed, failed], completeness in [0.0, 1.0]

4. **CumulativeMetrics**
   - Fields: total_sprints, cumulative (tokens/api_calls/time), per_sprint (array), sprint_efficiency (stats)
   - Relationships: Aggregates Sprint Metrics
   - Validation: cumulative values = sum of per_sprint values

5. **RunSummary**
   - Fields: total_sprints_planned, completed_sprints, failed_sprint (optional), sprint_results (array)
   - Relationships: Contains multiple Sprint results
   - Validation: completed_sprints <= total_sprints_planned

### API Contracts

**Define in `contracts/` directory:**

1. **`sprint_metadata_schema.json`**
   - JSON schema for `sprint_NNN/metadata.json`
   - Required fields, type constraints, validation rules

2. **`sprint_metrics_schema.json`**
   - JSON schema for `sprint_NNN/metrics.json`
   - Numeric constraints, nested structure for tokens

3. **`sprint_validation_schema.json`**
   - JSON schema for `sprint_NNN/validation.json`
   - Status enums, checks structure

4. **`cumulative_metrics_schema.json`**
   - JSON schema for `summary/metrics_cumulative.json`
   - Per-sprint array structure, efficiency calculations

5. **`run_summary_schema.json`**
   - JSON schema for run-level summary
   - Sprint results array, failure tracking

### Quickstart Guide

**Generate `quickstart.md` covering:**

1. **Basic Sprint Execution**
   ```bash
   # Run experiment with 3-sprint scenario
   python run_experiment.py --config config/experiment.yaml
   ```

2. **Accessing Sprint Artifacts**
   ```bash
   # View specific sprint
   ls experiments/my_exp/runs/baes/abc123/sprint_002/

   # View final sprint (via symlink)
   cd experiments/my_exp/runs/baes/abc123/final/generated_artifacts/managed_system/
   ```

3. **Analyzing Sprint Evolution**
   ```bash
   # Diff between sprints
   diff -r sprint_001/generated_artifacts sprint_002/generated_artifacts

   # View cumulative metrics
   cat summary/metrics_cumulative.json | jq
   ```

4. **Debugging Failed Sprints**
   ```bash
   # Check logs for failed sprint
   cat sprint_002/logs/execution_sprint_002.log

   # View last successful sprint
   cd final/generated_artifacts/managed_system/
   ```

---

## Phase 2: Implementation Phases

### Phase 2A: Core Sprint Infrastructure (3-4 hours)

**Module: `src/utils/isolation.py`**

Tasks:
1. Add `create_sprint_workspace(framework, run_id, sprint_num, experiment_name)` function
   - Create `sprint_NNN/` directory
   - Create `generated_artifacts/` subdirectory
   - Create `logs/` subdirectory
   - Return (sprint_dir, artifacts_dir) tuple

2. Add `get_previous_sprint_artifacts(run_dir, current_sprint_num)` function
   - Return None if sprint_num == 1
   - Find `sprint_{N-1:03d}/generated_artifacts/`
   - Return Path or None

3. Add `create_final_symlink(run_dir, final_sprint_num)` function
   - Create `final` symlink pointing to `sprint_{N:03d}`
   - Handle existing symlink (remove and recreate)
   - Cross-platform symlink creation

**Module: `src/adapters/base_adapter.py`**

Tasks:
4. Update `__init__` signature to accept `sprint_num` and `run_dir`
5. Add `self.sprint_num` property
6. Add `self.run_dir` property
7. Add `self.previous_sprint_artifacts` property (use `get_previous_sprint_artifacts`)
8. Add `self.sprint_log_dir` property
9. Update docstrings explaining sprint awareness

**Modules: Framework Adapters**

Tasks:
10. Update `BAeSAdapter.__init__` to pass sprint_num and run_dir to super()
11. Update `ChatDevAdapter.__init__` similarly
12. Update `GHSpecAdapter.__init__` similarly
13. Document how each framework uses `previous_sprint_artifacts`

**Tests:**
14. Write `tests/unit/test_sprint_workspace.py`
    - Test create_sprint_workspace creates correct structure
    - Test get_previous_sprint_artifacts returns correct path
    - Test get_previous_sprint_artifacts returns None for sprint 1

15. Write `tests/unit/test_sprint_context.py`
    - Test BaseAdapter initializes with sprint awareness
    - Test previous_sprint_artifacts is None for sprint 1
    - Test previous_sprint_artifacts is set for sprint 2+

### Phase 2B: Sprint Execution Loop (4-5 hours)

**Module: `src/orchestrator/runner.py`**

Tasks:
16. **Refactor step execution into sprint loop**
    - Replace single workspace creation with sprint loop
    - For each step_config, create sprint workspace
    - Initialize adapter with sprint_num and run_dir

17. **Add sprint metadata saving**
    - Create `_save_sprint_metadata(sprint_dir, sprint_num, step_config, result)` method
    - Write to `sprint_NNN/metadata.json`
    - Include started_at, completed_at, status, error

18. **Add sprint metrics saving**
    - Create `_save_sprint_metrics(sprint_dir, result)` method
    - Write to `sprint_NNN/metrics.json`
    - Validate against schema

19. **Add sprint validation saving**
    - Create `_save_sprint_validation(sprint_dir, validation_result)` method
    - Write to `sprint_NNN/validation.json`
    - Include all validation checks

20. **Implement failure handling**
    - On sprint failure: log error, save partial metadata, break loop
    - Track `completed_sprints` and `failed_sprint` variables
    - Do not execute remaining sprints after failure

21. **Add cumulative metrics calculation**
    - Create `_create_cumulative_metrics(summary_dir, sprint_results)` method
    - Aggregate tokens, api_calls, time across all sprints
    - Calculate efficiency trends
    - Write to `summary/metrics_cumulative.json`

22. **Add README generation**
    - Create `_generate_run_readme(run_dir, sprint_results)` method
    - Include sprint summary table
    - Add quick start instructions
    - Explain directory structure
    - Write to run_dir/README.md

23. **Add final symlink creation**
    - Call `create_final_symlink(run_dir, completed_sprints)` after sprint loop
    - Points to last successful sprint

**Tests:**
24. Write `tests/integration/test_multi_sprint_run.py`
    - Test 3-sprint scenario executes all sprints
    - Verify all sprint directories created
    - Verify final symlink points to sprint_003
    - Verify cumulative metrics correct

25. Write `tests/integration/test_sprint_failure.py`
    - Force sprint 2 to fail (mock execution)
    - Verify sprint 1 preserved
    - Verify sprint 2 has failure metadata
    - Verify sprint 3 not executed
    - Verify final points to sprint_001

### Phase 2C: Enhanced Features (2-3 hours)

**Module: `src/orchestrator/archiver.py`**

Tasks:
26. Add archiving mode configuration support
    - Read `config.experiment.yaml` for archiving.mode
    - Support "final_only" mode (archive only final/ + summary/)
    - Support "all_sprints" mode (archive all sprint_NNN/)

27. Add compression for intermediate sprints
    - If compress_intermediate: true, compress sprint_001, sprint_002, etc.
    - Leave final sprint uncompressed

**Module: `config/experiment.yaml`**

Tasks:
28. Add archiving configuration section
    ```yaml
    archiving:
      mode: "final_only"  # or "all_sprints"
      compress_intermediate: true
    ```

**Summary Generation:**

Tasks:
29. Create `_generate_evolution_report(summary_dir, run_dir)` method
    - Analyze code growth per sprint (LOC, files added)
    - Diff summary between consecutive sprints
    - Write to `summary/evolution_report.md`

30. Create `_generate_sprint_comparison(summary_dir, sprint_results)` method
    - Compare sprint metrics (tokens, time, efficiency)
    - Identify trends
    - Write to `summary/sprint_comparison.json`

**Tests:**
31. Write `tests/unit/test_cumulative_metrics.py`
    - Test metrics aggregation is correct sum
    - Test efficiency calculations
    - Test trend detection (increasing/decreasing)

32. Write `tests/unit/test_readme_generation.py`
    - Test README contains all required sections
    - Test sprint table formatting
    - Test quick start commands

### Phase 2D: Documentation & Testing (2-3 hours)

Tasks:
33. Update `docs/workspace_generation_fix/SPRINT_ARCHITECTURE_DESIGN.md`
    - Mark as implemented
    - Add "See implementation in specs/005-sprint-architecture-implementation/"

34. Create `docs/SPRINT_MIGRATION_GUIDE.md`
    - Explain new directory structure
        - Explain new directory structure
        - Document that runtime backward-compatibility fallbacks are NOT provided;
            instead provide a separate migration/analysis utility and troubleshooting tips

35. Update main `README.md`
    - Add sprint architecture section
    - Link to design and implementation docs

36. **Run full integration test suite**
    - Test all three frameworks (BAeS, ChatDev, GHSpec)
    - Verify 2-sprint scenarios work
    - Verify 3-sprint scenarios work
    - Verify failure handling works
    - Verify metrics are accurate

37. **Performance testing**
    - Measure overhead per sprint (should be < 1s)
    - Verify symlink creation is fast (< 10ms)
    - Verify README generation is fast (< 500ms)

38. **Storage analysis**
    - Measure disk usage for 3-sprint runs
    - Verify compression works
    - Document storage expectations in README

---

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 0: Research** | 2-3 hours | `research.md` with all findings |
| **Phase 1: Design & Contracts** | 2-3 hours | `data-model.md`, `contracts/`, `quickstart.md` |
| **Phase 2A: Core Infrastructure** | 3-4 hours | Sprint workspace creation, adapter updates, tests |
| **Phase 2B: Sprint Execution** | 4-5 hours | Runner refactor, metrics/metadata saving, failure handling |
| **Phase 2C: Enhanced Features** | 2-3 hours | Archiving modes, evolution reports, comparison |
| **Phase 2D: Documentation & Testing** | 2-3 hours | Docs, integration tests, performance validation |
| **Total** | **15-21 hours** | Complete sprint-based architecture |

---

## Risk Management

### Risk 1: Framework Context Passing Issues
**Mitigation**: Test with all three frameworks early. Document adapter-specific logic clearly. If `previous_sprint_artifacts` is missing or incompatible, the orchestrator MUST fail with a clear error; any "no context" handling should be implemented as an explicit, opt-in analysis utility, not as a silent runtime fallback.

### Risk 2: Storage Explosion
**Mitigation**: Implement compression. Provide clear documentation on storage expectations. Make archiving modes configurable.

### Risk 3: Performance Overhead
**Mitigation**: Optimize file operations. Use fast JSON library. Benchmark early and iterate.

### Risk 4: Backward Compatibility Breaks
**Mitigation**: Provide version detection in analysis utilities and a separate migration tool. The orchestrator MUST NOT attempt runtime compatibility fallbacks; instead emit clear errors directing users to run the migration utility.

---

## Success Criteria

### Must Have (MVP)
- [ ] Sprint directories created for each step
- [ ] Per-sprint metrics saved correctly
- [ ] Per-sprint validation executed
- [ ] Previous sprint artifacts passed to next sprint
- [ ] Sprint failures stop execution and preserve artifacts
- [ ] Cumulative metrics calculated correctly
- [ ] Final symlink created
- [ ] README.md generated with sprint summary
- [ ] All three frameworks work
- [ ] Integration tests pass

### Should Have
- [ ] Evolution report generated
- [ ] Sprint comparison metrics
- [ ] Configurable archiving modes
- [ ] Compression for intermediate sprints

### Quality Gates
- [ ] Constitution check passes (Phase 0 and Phase 1)
- [ ] Unit test coverage > 80%
- [ ] Integration tests for multi-sprint scenarios pass
- [ ] Performance overhead < 5% total runtime
- [ ] Documentation complete and clear

---

## Next Steps

1. **Phase 0**: Generate `research.md` by analyzing current implementation
2. **Phase 1**: Generate `data-model.md` and `contracts/` schemas
3. **Phase 2**: Begin implementation following task order above
4. **Testing**: Run integration tests with all frameworks
5. **Documentation**: Complete migration guide and update README
6. **Review**: Constitution re-check after Phase 1
7. **Deployment**: Merge to main branch after all tests pass

---

**Status**: Ready for Phase 0 execution ✅

````
