# Feature Specification: Sprint-Based Directory Architecture

## Overview

Implement a sprint-based directory architecture for the GenAI-DevBench benchmarking framework to enable tracking of incremental code evolution across scenario steps. Each "sprint" represents a single scenario step execution, producing a complete, versioned system that builds incrementally on previous sprints.

## Problem Statement

**Current State:**
- All scenario steps (currently called "steps") write to the SAME `workspace/` directory
- Each step overwrites the previous step's output
- Only the final step's artifacts survive
- Cannot track code evolution across steps
- Cannot debug which step introduced bugs
- Cannot compare framework performance on incremental development
- Cannot analyze token efficiency per step

**Evidence from codebase:**
```python
# src/orchestrator/runner.py:333
for step_index, step_config in enumerate(enabled_steps, start=1):
    result = self._execute_step_with_retry(step_config.id, command_text)
    # All steps write to same workspace_path - artifacts overwritten!
```

## Terminology

**Change:** "Scenario Steps" → "**Sprints**"

**Rationale:** Sprints perfectly capture the agile development concept:
- Each sprint is an incremental development phase
- Each sprint builds on previous sprints
- Each sprint produces a complete, evolved version
- Failures stop the sprint sequence (like real agile)

## User Stories

### Priority 1: Framework Comparison Across Incremental Development
**As a researcher,**
I want to compare how BAeS, ChatDev, and GHSpec handle incremental code changes across multiple sprints,
So that I can evaluate which framework is better at evolutionary development.

**Acceptance Criteria:**
- Each sprint's artifacts are preserved in separate directories
- Can compare Sprint 1 vs Sprint 2 vs Sprint 3 outputs for same scenario
- Can measure tokens/time per sprint for each framework
- Can identify which framework gets more efficient over sprints

### Priority 2: Token Efficiency Analysis Per Sprint
**As a researcher,**
I want to see token usage breakdown by sprint,
So that I can identify which sprints are expensive and optimize prompts.

**Acceptance Criteria:**
- Per-sprint metrics show tokens_in, tokens_out, api_calls
- Cumulative metrics aggregate across all sprints
- Can calculate token efficiency trends (increasing/decreasing)
- Can identify token-heavy sprints for optimization

### Priority 3: Code Evolution Tracking
**As a researcher,**
I want to see how the codebase evolves from Sprint 1 → Sprint 2 → Sprint 3,
So that I can analyze code quality, refactoring, and incremental changes.

**Acceptance Criteria:**
- Can diff between sprint_001 and sprint_002 directories
- Can track LOC (lines of code) growth per sprint
- Can see which files were added/modified in each sprint
- Evolution report generated automatically

### Priority 4: Debugging Sprint Failures
**As a developer,**
When Sprint 2 fails, I want Sprint 1's artifacts preserved,
So that I can analyze the working state before failure.

**Acceptance Criteria:**
- Sprint 1 artifacts untouched when Sprint 2 fails
- Sprint 2 partial artifacts available for debugging
- Logs isolated per sprint
- Can retry just Sprint 2 without re-running Sprint 1

### Priority 5: Final System Access
**As a user,**
I want easy access to the final, complete system,
So that I can run and test it without navigating multiple sprint directories.

**Acceptance Criteria:**
- `final/` symlink points to last successful sprint
- README.md shows which sprint is final
- Quick start instructions work from final/ directory

## Functional Requirements

### FR1: Sprint-Based Directory Structure
Each run must create separate directories per sprint:

```
experiments/<experiment>/runs/<framework>/<run-id>/
├── README.md                    # Run overview with sprint summary
├── sprint_001/                  # First sprint
│   ├── generated_artifacts/
│   │   └── managed_system/
│   ├── logs/
│   ├── metadata.json
│   ├── metrics.json
│   └── validation.json
├── sprint_002/                  # Second sprint
│   ├── generated_artifacts/
│   ├── logs/
│   ├── metadata.json
│   ├── metrics.json
│   └── validation.json
├── sprint_003/                  # Third sprint
│   └── ... (same structure)
├── summary/                     # Aggregate data
│   ├── metrics_cumulative.json
│   ├── evolution_report.md
│   └── sprint_comparison.json
├── final -> sprint_003          # Symlink to final sprint
└── run.tar.gz                   # Archive (configurable)
```

**Sprint Numbering:** `sprint_NNN/` format (3 digits, zero-padded)
- Scales to 999 sprints
- Lexicographically sortable
- Self-documenting

### FR2: Incremental Context Preservation
Each sprint (except Sprint 1) must receive previous sprint's artifacts as context:

- **Sprint 1:** No previous context (start from scratch)
- **Sprint 2:** Receives Sprint 1's `generated_artifacts/` as input
- **Sprint 3:** Receives Sprint 2's `generated_artifacts/` as input

**Implementation:**
- `BaseAdapter` gains `previous_sprint_artifacts` property
- Frameworks use previous artifacts as context:
  - **BAeS:** Include previous code in prompt
  - **ChatDev:** Set WareHouse to previous sprint
  - **GHSpec:** Provide previous implementation to specify phase

**Adapter Attribute Updates Between Sprints:**

When transitioning from Sprint N to Sprint N+1, the adapter instance MUST:

1. **Preserve** framework state (initialized once in `start()`):
   - `framework_dir`, `python_path`, `venv_path`
   - Framework-specific installation paths

2. **Update** sprint context:
   - `workspace_path` → new sprint workspace directory
   - `_sprint_num` → current sprint number
   - `_run_dir` → run directory path

3. **Recreate** workspace subdirectories specific to framework type:

| Framework | Subdirectories to Recreate | Environment Variables to Update |
|-----------|---------------------------|--------------------------------|
| BAeS      | `managed_system/`, `database/` | `BAE_CONTEXT_STORE_PATH`, `MANAGED_SYSTEM_PATH` |
| ChatDev   | `WareHouse/`              | (none) |
| GHSpec    | `specs/<feature>/`, `specs/<feature>/src/` | (none) |

See [FR9: Adapter Lifecycle Management](#fr9-adapter-lifecycle-management) for detailed implementation requirements.

### FR3: Per-Sprint Metrics
Each sprint must track its own metrics independently:

**Per-Sprint (`sprint_NNN/metrics.json`):**
```json
{
  "sprint_number": 1,
  "step_id": 1,
  "tokens": {
    "input": 2000,
    "output": 800,
    "cached": 0,
    "total": 2800
  },
  "api_calls": 3,
  "execution_time_seconds": 45.3,
  "hitl_interactions": 0,
  "retry_count": 0,
  "validation": {
    "passed": true,
    "issues": []
  }
}
```

**Cumulative (`summary/metrics_cumulative.json`):**
```json
{
  "total_sprints": 3,
  "cumulative": {
    "tokens": {"total": 7900},
    "api_calls": 8,
    "execution_time_seconds": 125.7
  },
  "per_sprint": [
    {"sprint": 1, "tokens": {"total": 2800}},
    {"sprint": 2, "tokens": {"total": 2600}},
    {"sprint": 3, "tokens": {"total": 2500}}
  ],
  "sprint_efficiency": {
    "tokens_per_sprint_avg": 2633,
    "tokens_trend": "decreasing"
  }
}
```

**Tokens Trend Calculation:**

The `tokens_trend` field indicates whether token usage is increasing, decreasing, or stable across sprints:

**Algorithm:**
1. Split completed sprints into first half and second half
2. Calculate average total tokens per sprint for each half
3. Compare averages with 10% threshold:
   - If `second_half_avg < first_half_avg * 0.9`: **"decreasing"**
   - If `second_half_avg > first_half_avg * 1.1`: **"increasing"**
   - Otherwise: **"stable"**

**Example:** For 4 sprints with tokens `[3000, 2800, 2500, 2300]`:
- First half: sprints 1-2, average = (3000 + 2800) / 2 = **2900**
- Second half: sprints 3-4, average = (2500 + 2300) / 2 = **2400**
- Comparison: 2400 < 2900 * 0.9 (2610) → **"decreasing"**

**Edge Cases:**
- Single sprint: trend = "stable" (insufficient data)
- Two sprints: first half = sprint 1, second half = sprint 2

### FR4: Per-Sprint Validation
Each sprint's workspace must be validated independently:

- **Sprint 1:** Validate V1 of system (must be complete)
- **Sprint 2:** Validate V2 of system (must be complete with Sprint 2 additions)
- **Sprint 3:** Validate V3 of system (must be complete)

**Validation Results (`sprint_NNN/validation.json`):**
```json
{
  "sprint_number": 1,
  "validated_at": "2025-10-22T14:31:20Z",
  "overall_status": "passed",
  "checks": {
    "python_files_exist": true,
    "imports_valid": true,
    "syntax_valid": true,
    "requirements_exist": true
  },
  "issues": [],
  "completeness": 1.0
}
```

### FR5: Sprint Failure Handling
When a sprint fails, execution must stop and preserve all previous sprints:

**Behavior:**
- **Sprint 1 succeeds:** Artifacts saved, continue to Sprint 2
- **Sprint 2 fails:** Stop execution, preserve Sprint 1 and Sprint 2 (partial)
- **Sprint 3:** Not executed

**Failure State:**
```
runs/<framework>/<run-id>/
├── sprint_001/          ✅ Complete
├── sprint_002/          ❌ Failed (partial artifacts + error logs)
├── sprint_003/          ⏸️ Not created
├── summary/
│   └── metrics_cumulative.json  # Shows: completed=1, failed=2, planned=3
└── final -> sprint_001  # Points to last successful sprint
```

**Partial Artifacts Definition:**

"Partial artifacts" means any files written to `generated_artifacts/` before the failure occurred:
- Incomplete files are preserved as-is (not deleted)
- Corrupted or half-written files are preserved for debugging
- Minimum preservation: logs directory with full error information

**Error Logs Requirements:**

Each failed sprint MUST include error logs with:
- **Location:** `sprint_NNN/logs/error.log`
- **Content:** 
  - Full Python traceback (complete stack trace)
  - Error message and error type
  - Timestamp of failure (ISO 8601 format)
  - Context variables (run_id, sprint_num, framework name)
- **Format:** Plain text, UTF-8 encoding

**Stop Execution Behavior:**

When a sprint fails:
1. Catch exception in sprint loop
2. Break sprint loop immediately (no further sprint directories created)
3. Save partial `metadata.json` with `status="failed"` and error message
4. Ensure all log buffers are flushed to disk
5. Create `final/` symlink pointing to last successful sprint
6. Generate README with failure information
7. Exit gracefully (do not propagate exception to caller)

### FR6: README Generation
Each run must generate a README.md with sprint summary:

**Contents:**
- Run metadata (framework, model, date, status)
- Sprint summary table (status, tokens, time, validation)
- Total metrics
- Quick start instructions
- Directory structure explanation

### FR7: Final Symlink
Create `final/` symlink pointing to last successful sprint:
- If all sprints succeed: `final -> sprint_003`
- If Sprint 2 fails: `final -> sprint_001`

### FR8: Archive Strategy
Support configurable archiving:

**Configuration:**
```yaml
# config/experiment.yaml
archiving:
  mode: "final_only"  # or "all_sprints"
  compress_intermediate: true
```

**Modes:**
- `final_only`: Archive only final sprint + summary + README
- `all_sprints`: Archive all sprint directories

### FR9: Adapter Lifecycle Management
Adapter instances MUST be reused across all sprints within a run. Creating new adapter instances per sprint loses critical framework state initialized during `start()`.

**Adapter State Separation:**

Adapter state is divided into two categories:

**Framework State (initialized once in `start()`, persists across all sprints):**
- `framework_dir`: Path to shared framework installation (e.g., `~/.genai-devbench/frameworks/baes/`)
- `python_path`: Path to virtual environment Python executable (e.g., `~/.genai-devbench/frameworks/baes/venv/bin/python`)
- `venv_path`: Path to virtual environment directory
- Framework-specific paths:
  - **BAeS:** `kernel_wrapper_path` (location of kernel_wrapper.py)
  - **ChatDev:** Framework installation paths
  - **GHSpec:** Framework installation paths

**Sprint Context (updated at the start of each sprint):**
- `workspace_path`: Current sprint workspace directory (e.g., `runs/baes/run-123/sprint_002/generated_artifacts/`)
- `_sprint_num`: Current sprint number (1-indexed)
- `_run_dir`: Run directory path
- Framework-specific workspace subdirectories:
  - **BAeS:** `managed_system_dir`, `database_dir`
  - **ChatDev:** `warehouse_dir`
  - **GHSpec:** `specs_dir`, `feature_dir`, `src_dir`, `spec_md_path`, `plan_md_path`, `tasks_md_path`

**Update Strategy:**

For each sprint after the first:

1. Update `adapter.workspace_path` to new sprint workspace directory
2. Update `adapter._sprint_num` to current sprint number
3. Update `adapter._run_dir` to run directory path
4. Recreate framework-specific workspace subdirectories within new sprint workspace
5. Update framework-specific artifact paths (if applicable)
6. Update environment variables (if framework requires it)

**Framework-Specific Workspace Recreation:**

| Framework | Subdirectories to Recreate | Environment Variables to Update |
|-----------|---------------------------|--------------------------------|
| BAeS      | `managed_system/`, `database/` | `BAE_CONTEXT_STORE_PATH`, `MANAGED_SYSTEM_PATH` |
| ChatDev   | `WareHouse/`              | (none) |
| GHSpec    | `specs/<feature_dir>/`, `specs/<feature_dir>/src/` | (none) |

**Prohibited Pattern:**

```python
# ❌ WRONG: Creating new adapter instances loses framework state
for sprint_num in range(1, num_sprints + 1):
    sprint_workspace = run_dir / f"sprint_{sprint_num:03d}" / "generated_artifacts"
    
    # This creates a NEW adapter, losing python_path, framework_dir, etc.
    self.adapter = BAeSAdapter(
        config=self.config,
        workspace_path=str(sprint_workspace)
    )
    # python_path is now None! (only set during start())
```

**Required Pattern:**

```python
# ✅ CORRECT: Update existing adapter's sprint context
for sprint_num in range(1, num_sprints + 1):
    sprint_workspace = run_dir / f"sprint_{sprint_num:03d}" / "generated_artifacts"
    
    # Update sprint context on existing adapter
    self.adapter.workspace_path = str(sprint_workspace)
    self.adapter._sprint_num = sprint_num
    self.adapter._run_dir = str(run_dir)
    
    # Recreate framework-specific workspace subdirectories
    if isinstance(self.adapter, BAeSAdapter):
        workspace_dirs = self.adapter.create_workspace_structure(['managed_system', 'database'])
        self.adapter.managed_system_dir = workspace_dirs['managed_system']
        self.adapter.database_dir = workspace_dirs['database']
        os.environ['MANAGED_SYSTEM_PATH'] = str(self.adapter.managed_system_dir)
        os.environ['BAE_CONTEXT_STORE_PATH'] = str(self.adapter.database_dir)
    elif isinstance(self.adapter, ChatDevAdapter):
        workspace_dirs = self.adapter.create_workspace_structure(['WareHouse'])
        self.adapter.warehouse_dir = workspace_dirs['WareHouse']
    elif isinstance(self.adapter, GHSpecAdapter):
        # Recreate specs directory structure
        specs_dir = Path(sprint_workspace) / "specs"
        feature_dir = specs_dir / self.adapter.feature_name
        src_dir = feature_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Update artifact paths
        self.adapter.specs_dir = specs_dir
        self.adapter.feature_dir = feature_dir
        self.adapter.src_dir = src_dir
        self.adapter.spec_md_path = feature_dir / "spec.md"
        self.adapter.plan_md_path = feature_dir / "plan.md"
        self.adapter.tasks_md_path = feature_dir / "tasks.md"
    
    # python_path, framework_dir remain unchanged from start()
```

**Rationale:**

- **Efficiency:** Framework setup (virtualenv creation, dependency installation) is expensive and only needs to happen once
- **Correctness:** Framework state initialized in `start()` must persist (python_path, venv_path)
- **Isolation:** Sprint-specific artifacts are isolated by workspace_path changes
- **Flexibility:** Frameworks can evolve workspace needs per sprint without re-initialization

### FR10: Critical Variable Lifecycle
Critical timing and state variables MUST be initialized and captured at specific points in the execution flow to ensure correct metrics, README generation, and failure handling.

**Variable Initialization Order:**

**Before Sprint Loop (once per run):**
```python
run_start_time = datetime.utcnow()  # Capture before any sprint execution
last_successful_sprint = 0          # Initialize tracking variable
```

**During Sprint Loop (per sprint iteration):**
```python
sprint_start_time = datetime.utcnow()     # Capture at sprint iteration start
# ... execute sprint ...
sprint_end_time = datetime.utcnow()       # Capture after sprint execution completes
last_successful_sprint = sprint_num       # Update ONLY on successful sprint
```

**After Sprint Loop (immediately after loop exits):**
```python
run_end_time = datetime.utcnow()  # Capture BEFORE README generation or archiving
```

**Timing Constraints:**

1. `run_end_time` MUST be defined immediately after the sprint loop exits (whether by completion or failure)
2. `run_end_time` MUST be defined BEFORE calling `_generate_run_readme()`
3. `run_end_time` MUST be defined BEFORE validation/archiving steps that may use it
4. Variables MUST NOT be used before initialization (fail-fast principle)

**Rationale:**

The timing of `run_end_time` is critical:
- If captured too early (before loop), it's incorrect
- If captured too late (after README generation), it's used before definition
- If captured inside loop, it's overwritten each iteration
- Must be captured exactly once, immediately after loop exits

**Example Flow:**

```python
run_start_time = datetime.utcnow()
last_successful_sprint = 0

# Sprint loop
for sprint_num in range(1, num_sprints + 1):
    sprint_start_time = datetime.utcnow()
    
    try:
        # Execute sprint...
        sprint_end_time = datetime.utcnow()
        last_successful_sprint = sprint_num
    except Exception as e:
        # Handle failure...
        break  # Exit loop

# CRITICAL: Capture run_end_time immediately after loop
run_end_time = datetime.utcnow()

# Now safe to use run_end_time
_generate_run_readme(
    run_start_time=run_start_time,
    run_end_time=run_end_time,  # Guaranteed to be defined
    last_successful_sprint=last_successful_sprint
)
```

**Additional Requirements:**

- All timing variables MUST use `datetime.utcnow()` for consistency
- Timing variables MUST be in UTC timezone (not local time)
- Duration calculations MUST use `(end_time - start_time).total_seconds()`

## Non-Functional Requirements

### NFR1: No Backward Compatibility Burden
- Generated experiments are independent git repositories; breaking changes are
  permitted when they improve clarity or correctness.
- New runs use the sprint-based structure. There is NO requirement to provide
  automatic migration or compatibility layers.
  Tools that analyze historical runs MAY accept the previous single-`workspace/`
  format, but such support is optional and implemented as a separate analysis
  utility (not as an orchestrator fallback).

### NFR2: Performance
- Sprint directory creation: < 100ms
- Symlink creation: < 10ms
- README generation: < 500ms
- Total overhead per sprint: < 1s

### NFR3: Storage Efficiency
- Per-sprint overhead: ~100KB (metadata, logs, metrics)
- Compressed archives reduce by ~70%
- Option to delete intermediate sprints post-analysis

### NFR4: Maintainability
- DRY principles (no code duplication)
- Shared utilities in `BaseAdapter`
- Clear separation of concerns

### NFR5: Testability
- Unit tests for sprint workspace creation
- Integration tests for multi-sprint scenarios
- Test failure handling (Sprint 2 fails)
- Test metrics aggregation

## Technical Constraints

### TC1: Framework Integration
Must work with all three frameworks without modification to framework code:
- **BAeS:** Python-based, custom runner
- **ChatDev:** Python-based, WareHouse pattern
- **GHSpec:** Node.js-based, 5-phase workflow

**Solution:** Adapter pattern handles framework-specific context passing

### TC2: File System
- POSIX-compliant file systems (Linux, macOS)
- Symlinks supported
- No hardcoded paths
- Path separators handled correctly

### TC3: Concurrency
- Multiple runs can execute simultaneously (different run_ids)
- Sprint execution within a run is SEQUENTIAL (not parallel)
- File locking not required (isolated directories)

## Dependencies

### Existing Components
- `src/utils/isolation.py` - Workspace creation
- `src/adapters/base_adapter.py` - Adapter base class
- `src/orchestrator/runner.py` - Execution orchestration
- `src/orchestrator/metrics_collector.py` - Metrics tracking
- `src/orchestrator/validator.py` - Workspace validation
- `src/orchestrator/archiver.py` - Archive creation

### New Dependencies
- None (use existing Python stdlib)

## Out of Scope

### Not Included in This Feature
- Parallel sprint execution
- Sprint retry mechanism (future feature)
- Sprint rollback functionality
- Interactive sprint debugging UI
- Real-time sprint progress tracking
- Sprint-level test execution

### Explicitly Excluded
- Changes to framework internal code
- Changes to scenario YAML format
- Changes to validation schemas
- New metrics (use existing metrics)

## Success Metrics

### Quantitative
- **Sprint isolation:** 100% of sprints have separate directories
- **Artifact preservation:** 100% of previous sprint artifacts accessible to next sprint
- **Metrics accuracy:** 100% of sprint metrics match cumulative metrics sum
- **Failure handling:** 100% of failed sprints preserve previous sprint artifacts
- **Performance overhead:** < 5% total runtime increase

### Qualitative
- Researchers can easily compare framework sprint performance
- Debugging sprint failures is straightforward
- Code evolution analysis is automated
- Documentation is clear and complete

## Risks and Mitigations

### Risk 1: Storage Explosion
**Impact:** High storage usage for multi-sprint scenarios
**Likelihood:** High (3+ sprints = 3x storage)
**Mitigation:**
- Compress intermediate sprints
- Configurable archiving modes
- Option to delete intermediate sprints post-analysis
- Documentation on storage expectations

### Risk 2: Adapter Complexity
**Impact:** Increased complexity in adapters
**Likelihood:** Medium
**Mitigation:**
- Shared utilities in BaseAdapter (DRY)
- Clear documentation
- Comprehensive tests
- Incremental refactoring

### Risk 3: Backward Compatibility Concerns
**Impact:** Old runs may not be directly consumable by new analysis tools
**Likelihood:** Low — experiments are self-contained git repositories, minimizing
cross-contamination risk.
**Mitigation:**
- Provide a migration guide and a small, separate analysis utility to read legacy
  single-`workspace/` runs when needed.
- Do NOT implement runtime fallback behavior in the orchestrator. The system
  MUST fail fast on unrecognized run formats, emitting a clear error that the
  analysis tool or user must run the migration utility.

### Risk 4: Framework-Specific Context Issues
**Impact:** Previous sprint context not properly passed to frameworks
**Likelihood:** Medium (each framework handles context differently)
**Mitigation:**
- Thorough testing with all three frameworks
- Framework-specific adapter logic
- Clear documentation of context passing
- Debug logging for context flow

## Acceptance Criteria Summary

### Must Have (MVP)
- ✅ Sprint-based directory structure created
- ✅ Per-sprint metrics saved
- ✅ Per-sprint validation executed
- ✅ Previous sprint artifacts passed to next sprint
- ✅ Sprint failure stops execution, preserves artifacts
- ✅ Cumulative metrics calculated correctly
- ✅ Final symlink created
- ✅ README.md generated with sprint summary
- ✅ All three frameworks work with new architecture
- ✅ Tests pass (unit + integration)

### Should Have
- ✅ Evolution report generated
- ✅ Sprint comparison metrics
- ✅ Configurable archiving modes
- ✅ Storage optimization options

### Nice to Have (Future)
- ⏸️ Sprint retry mechanism
- ⏸️ Sprint rollback functionality
- ⏸️ Interactive debugging UI
- ⏸️ Real-time progress tracking

## References

- [Sprint Architecture Design](../../docs/workspace_generation_fix/SPRINT_ARCHITECTURE_DESIGN.md)
- [Current Runner Implementation](../../src/orchestrator/runner.py)
- [BaseAdapter](../../src/adapters/base_adapter.py)
- [Isolation Utilities](../../src/utils/isolation.py)
