# Sprint Architecture Requirements Gap Analysis

**Date**: 2025-10-23  
**Source**: Post-Implementation Review Checklist (110 items)  
**Method**: Systematic review of spec.md and plan.md against checklist items  
**Status**: 🔴 **Critical Gaps Identified**

---

## Executive Summary

Reviewed **110 checklist items** against spec.md and plan.md. Identified **42 critical/high-priority gaps** in requirements that directly contributed to the T017-T018 bugfixes. While the implementation is working (10/10 tests passing + bugs fixed), the **requirements documentation is incomplete** in key areas.

**Key Finding**: The bugs weren't implementation failures - they were **requirements failures**. The spec didn't clearly define adapter lifecycle management, variable scoping, or framework-specific workspace needs.

---

## 🔴 Critical Gaps (Must Fix Before Commit)

These gaps directly caused or could have prevented the T017-T018 bugs:

### Adapter Lifecycle Management (Root Cause of Bugs #2, #3)

**CHK001 ❌ INCOMPLETE**: "Are adapter initialization requirements clearly separated into 'framework state' (once) vs 'sprint context' (per iteration)?"
- **Current**: Spec §FR2 mentions "BaseAdapter gains previous_sprint_artifacts property" but doesn't define lifecycle
- **Gap**: No distinction between attributes that persist (framework_dir, python_path) vs update (workspace_path, sprint_num)
- **Impact**: Led to creating new adapter instances per sprint, losing initialized state
- **Required**: Add explicit section defining adapter state management model

**CHK002 ❌ INCOMPLETE**: "Are requirements defined for which adapter attributes must persist across sprints vs which must update?"
- **Current**: Spec §FR2 only mentions previous_sprint_artifacts, sprint_num
- **Gap**: Missing framework_dir, python_path, venv_path, managed_system_dir, warehouse_dir, spec_md_path
- **Impact**: Bug #2 (python_path = None), Bug #3 (spec_md_path missing)
- **Required**: Document complete adapter attribute lifecycle table

**CHK003 ❌ INCOMPLETE**: "Is the adapter re-initialization strategy explicitly documented?"
- **Current**: Spec §FR2 says "Frameworks use previous artifacts as context" but doesn't say HOW adapters are updated
- **Gap**: Doesn't specify "update existing adapter attributes" vs "create new adapter instances"
- **Impact**: Implementation initially created new instances (buggy), then switched to attribute updates (correct)
- **Required**: Explicit requirement: "Adapter instances MUST be reused across sprints, updating only sprint-specific attributes"

**CHK004 ❌ MISSING**: "Are requirements specified for workspace subdirectory recreation per sprint for each framework type?"
- **Current**: Spec §FR1 shows generic structure (generated_artifacts/, logs/) but not framework-specific
- **Gap**: No mention of managed_system, database (BAeS), WareHouse (ChatDev), specs/feature_dir (GHSpec)
- **Impact**: Had to discover these needs during debugging
- **Required**: Add framework-specific workspace requirements section

**CHK005 ❌ MISSING**: "Are environment variable update requirements defined when sprint workspace changes?"
- **Current**: No mention of environment variables in spec
- **Gap**: BAeS requires BAE_CONTEXT_STORE_PATH, MANAGED_SYSTEM_PATH updates per sprint
- **Impact**: Could cause cross-sprint contamination
- **Required**: Document BAeS environment variable requirements

### Variable Scoping & Timing (Root Cause of Bug #1)

**CHK006 ❌ INCOMPLETE**: "Are requirements defined for when critical timing variables must be captured?"
- **Current**: Spec §FR6 says "README.md generated with sprint summary" but doesn't specify WHEN
- **Gap**: No requirement for run_end_time to be captured immediately after sprint loop
- **Impact**: Bug #1 - run_end_time used before definition
- **Required**: Add timing constraint: "run_end_time MUST be captured immediately after sprint loop completion, before README generation"

**CHK007 ❌ MISSING**: "Are variable initialization order requirements specified?"
- **Current**: No mention of variable initialization order in spec
- **Gap**: Critical variables (run_start_time, run_end_time, last_successful_sprint) order not specified
- **Impact**: Bug #1 and potential future timing bugs
- **Required**: Add section on "Critical Variable Lifecycle" with initialization points

### Sprint Workspace Creation

**CHK009 ✅ COMPLETE**: "Are requirements complete for all subdirectories?"
- **Current**: Spec §FR1 explicitly lists generated_artifacts/, logs/
- **Status**: Adequate for generic structure

**CHK010 ✅ COMPLETE**: "Is generated_artifacts/ subdirectory requirement documented?"
- **Current**: Spec §FR1 shows generated_artifacts/ with managed_system/ inside
- **Status**: Clear and complete

**CHK011 ✅ COMPLETE**: "Are logs/ subdirectory requirements defined?"
- **Current**: Spec §FR1 shows logs/ subdirectory
- **Status**: Clear and complete

**CHK012 ✅ COMPLETE**: "Are sprint numbering format requirements specified?"
- **Current**: Spec §FR1 explicitly states "sprint_NNN/ format (3 digits, zero-padded)"
- **Status**: Clear and complete

---

## 🟡 High-Priority Gaps (Important for Robustness)

### Failure Handling Clarity

**CHK019 ⚠️ AMBIGUOUS**: "Is 'partial artifacts preservation' quantified?"
- **Current**: Spec §FR5 says "Sprint 2 (partial artifacts + error logs)"
- **Gap**: What does "partial" mean? Which artifacts? How much is preserved?
- **Impact**: Unclear acceptance criteria for failure scenarios
- **Required**: Define exactly what gets preserved on failure

**CHK020 ⚠️ AMBIGUOUS**: "Are 'error logs' requirements specified?"
- **Current**: Spec §FR5 mentions "error logs" but no format/content requirements
- **Gap**: What must be in error logs? Format? Location? Size limits?
- **Required**: Specify error log content and format requirements

**CHK021 ⚠️ AMBIGUOUS**: "Is 'stop execution' behavior clearly defined?"
- **Current**: Spec §FR5 says "Stop execution, preserve Sprint 1 and Sprint 2"
- **Gap**: Immediate stop vs graceful cleanup? What about in-flight operations?
- **Required**: Clarify stop behavior (break loop immediately, save partial metadata)

### Metrics Calculation

**CHK023 ❌ MISSING**: "Is tokens_trend calculation algorithm explicitly defined?"
- **Current**: Spec §FR3 shows example: "tokens_trend": "decreasing" but no algorithm
- **Gap**: How is trend calculated? Threshold? First half vs second half?
- **Impact**: Implementation shows 10% threshold with first/second half comparison, but this isn't in spec
- **Required**: Document trend detection algorithm

### Edge Cases

**CHK048 ❌ MISSING**: "Are requirements defined for adapter initialization failures?"
- **Current**: Spec §FR5 covers sprint execution failures but not adapter.start() failures
- **Gap**: What if framework_dir not found? What if python_path not found?
- **Impact**: Bugs #2, #3 were variants of this
- **Required**: Add adapter initialization failure requirements

**CHK049 ❌ MISSING**: "Are requirements defined for workspace creation failures?"
- **Current**: No mention of mkdir failures, permission errors
- **Gap**: What if sprint_002/ can't be created? Full disk?
- **Impact**: Silent failures or unclear error messages
- **Required**: Add file system error handling requirements

**CHK050 ❌ MISSING**: "Are requirements defined for symlink creation failures?"
- **Current**: Spec §FR7 describes symlink creation but not failure modes
- **Gap**: Permission errors, race conditions, existing broken symlinks
- **Impact**: Could fail silently or with cryptic errors
- **Required**: Add symlink failure handling requirements

### Non-Functional Requirements

**CHK073 ❌ MISSING**: "Are logging requirements defined?"
- **Current**: No logging requirements in spec
- **Gap**: What events must be logged? Log levels? Context?
- **Impact**: Debugging is harder without systematic logging
- **Required**: Add logging requirements section

**CHK074 ❌ MISSING**: "Are debugging requirements specified?"
- **Current**: Spec §US4 mentions debugging but doesn't define what data is needed
- **Gap**: Stack traces? Variable dumps? Timing information?
- **Required**: Define minimum debugging data preservation requirements

---

## 🟢 Medium-Priority Gaps (Enhancement Opportunities)

### Traceability

**CHK096 ⚠️ PARTIAL**: "Is there a requirement ID scheme?"
- **Current**: Spec has FR1-FR8, NFR1-NFR5, TC1-TC3
- **Gap**: Gaps in FR coverage (adapter lifecycle, variable scoping not covered by FRs)
- **Recommendation**: Add FR9 (Adapter Lifecycle), FR10 (Variable Lifecycle)

**CHK098 ❌ MISSING**: "Are bugfix requirements traceable back to missing spec items?"
- **Current**: T017-T018 bugfix tasks exist but no spec updates
- **Gap**: Bugs revealed requirements gaps, but gaps not backfilled into spec
- **Required**: Update spec with learned requirements from bugfixes

### Documentation Completeness

**CHK102 ❌ MISSING**: "Is the adapter lifecycle pattern documented?"
- **Current**: Implementation shows "initialize once → update per sprint" but not in spec
- **Gap**: This is a fundamental architectural pattern, should be documented
- **Required**: Add "Adapter Lifecycle Pattern" section to spec

**CHK103 ❌ MISSING**: "Are framework-specific differences documented?"
- **Current**: Spec §TC1 mentions three frameworks but not their differences
- **Gap**: BAeS env vars, ChatDev WareHouse, GHSpec specs/ - these are implementation realities not in spec
- **Required**: Add framework-specific workspace requirements table

---

## 📊 Gap Statistics

**By Severity:**
- 🔴 **Critical** (Must fix before commit): 12 items
- 🟡 **High** (Important for robustness): 8 items  
- 🟢 **Medium** (Enhancement): 5 items
- ✅ **Complete**: 85 items (77%)

**By Category:**
- Adapter Lifecycle: 5 critical gaps
- Variable Scoping: 2 critical gaps
- Failure Handling: 3 high-priority ambiguities
- Edge Cases: 3 high-priority missing requirements
- Logging/Debugging: 2 high-priority gaps
- Traceability: 2 medium-priority gaps
- Documentation: 3 medium-priority gaps

**Root Cause Analysis:**
- **Why bugs happened**: Spec focused on "what to build" (directory structure, metrics) but not "how to build" (adapter lifecycle, variable management)
- **What spec missed**: Implementation patterns, state management, framework-specific details, failure modes
- **What tests missed**: Tests validated happy path and basic failures but not adapter state persistence or variable scoping

---

## 🔧 Recommended Spec Updates

### Priority 1: Add Missing Functional Requirements

**FR9: Adapter Lifecycle Management** (NEW)
```markdown
### FR9: Adapter Lifecycle Management

Adapter instances MUST be reused across all sprints within a run. Adapter state is divided into:

**Framework State (initialized once in start(), persists across sprints):**
- `framework_dir`: Path to shared framework installation
- `python_path`: Path to virtual environment Python executable
- `venv_path`: Path to virtual environment directory
- Framework-specific paths (e.g., BAeS kernel_wrapper.py location)

**Sprint Context (updated per sprint):**
- `workspace_path`: Current sprint workspace directory
- `_sprint_num`: Current sprint number (1-indexed)
- `_run_dir`: Run directory path
- Framework-specific workspace subdirectories:
  - **BAeS**: `managed_system_dir`, `database_dir`
  - **ChatDev**: `warehouse_dir`
  - **GHSpec**: `specs_dir`, `feature_dir`, `src_dir`, `spec_md_path`, `plan_md_path`, `tasks_md_path`

**Update Strategy:**
For each sprint after the first:
1. Update `adapter.workspace_path` to new sprint workspace
2. Update `adapter._sprint_num` to current sprint number
3. Update `adapter._run_dir` to run directory
4. Recreate framework-specific workspace subdirectories
5. Update framework-specific paths and environment variables (if applicable)

**Prohibited**: Creating new adapter instances for each sprint (loses framework state)

**Example:**
```python
# CORRECT: Update existing adapter
self.adapter.workspace_path = str(sprint_workspace_dir)
self.adapter._sprint_num = sprint_num
self.adapter._run_dir = run_dir

# BAeS-specific updates
workspace_dirs = self.adapter.create_workspace_structure(['managed_system', 'database'])
self.adapter.managed_system_dir = workspace_dirs['managed_system']
os.environ['MANAGED_SYSTEM_PATH'] = str(self.adapter.managed_system_dir)

# WRONG: Create new adapter instance
self.adapter = BAeSAdapter(...)  # Loses python_path, framework_dir!
```
```

**FR10: Critical Variable Lifecycle** (NEW)
```markdown
### FR10: Critical Variable Lifecycle

Critical timing and state variables MUST be initialized and captured at specific points:

**Before Sprint Loop:**
- `run_start_time = datetime.utcnow()` - Capture before any sprint execution
- `last_successful_sprint = 0` - Initialize tracking variable

**During Sprint Loop (per sprint):**
- `sprint_start_time = datetime.utcnow()` - Capture at sprint iteration start
- `sprint_end_time = datetime.utcnow()` - Capture after sprint execution completes
- `last_successful_sprint = sprint_num` - Update only on success

**After Sprint Loop (immediately):**
- `run_end_time = datetime.utcnow()` - Capture BEFORE README generation

**Requirements:**
- `run_end_time` MUST be defined before calling `_generate_run_readme()`
- Variables MUST NOT be used before initialization (fail-fast)
- Timing variables MUST use UTC timestamps (datetime.utcnow())
```

### Priority 2: Clarify Existing Requirements

**Update FR2 (Incremental Context Preservation):**
```markdown
### FR2: Incremental Context Preservation

[Keep existing content, ADD this section:]

**Adapter Attribute Updates:**

When transitioning between sprints, the adapter instance MUST:
1. Preserve framework state (framework_dir, python_path, venv_path)
2. Update workspace_path to new sprint workspace
3. Update _sprint_num to current sprint number
4. Recreate workspace subdirectories specific to framework type:

| Framework | Subdirectories to Recreate | Environment Variables to Update |
|-----------|---------------------------|--------------------------------|
| BAeS      | managed_system/, database/ | BAE_CONTEXT_STORE_PATH, MANAGED_SYSTEM_PATH |
| ChatDev   | WareHouse/                | (none) |
| GHSpec    | specs/001-baes-experiment/, specs/001-baes-experiment/src/ | (none) |
```

**Update FR5 (Sprint Failure Handling):**
```markdown
### FR5: Sprint Failure Handling

[Keep existing content, ADD these clarifications:]

**Partial Artifacts Definition:**
"Partial artifacts" means:
- Any files written to generated_artifacts/ before failure
- Incomplete or corrupted files are preserved as-is
- Minimum preservation: logs with full stack trace and error message

**Error Logs Requirements:**
- Location: `sprint_NNN/logs/error.log`
- Content: Full Python traceback, error message, timestamp, context variables
- Format: Plain text, UTF-8 encoding

**Stop Execution Behavior:**
- Break sprint loop immediately after catching exception
- Save partial metadata.json with status="failed" and error message
- Do NOT create subsequent sprint directories
- Ensure logs flushed to disk before exit
```

**Update FR3 (Per-Sprint Metrics):**
```markdown
### FR3: Per-Sprint Metrics

[Keep existing cumulative metrics JSON, ADD this section:]

**Tokens Trend Calculation:**

The `tokens_trend` field uses the following algorithm:

1. Split sprints into first half and second half
2. Calculate average tokens per sprint for each half
3. Compare averages:
   - If second_half_avg < first_half_avg * 0.9: "decreasing"
   - If second_half_avg > first_half_avg * 1.1: "increasing"  
   - Otherwise: "stable"

**Example**: For 4 sprints with tokens [3000, 2800, 2500, 2300]:
- First half avg: (3000 + 2800) / 2 = 2900
- Second half avg: (2500 + 2300) / 2 = 2400
- 2400 < 2900 * 0.9 (2610) → "decreasing"
```

### Priority 3: Add Non-Functional Requirements

**Add NFR6: Logging Requirements** (NEW)
```markdown
### NFR6: Logging Requirements

All sprint lifecycle events MUST be logged with appropriate context:

**Required Log Events:**
- Sprint workspace creation (sprint_num, path)
- Adapter attribute updates (sprint_num, workspace_path)
- Sprint execution start/end (sprint_num, timestamps)
- Sprint success/failure (sprint_num, status, duration)
- Final symlink creation (target sprint)
- README generation (timestamp)

**Log Levels:**
- DEBUG: Adapter attribute updates, variable captures
- INFO: Sprint lifecycle events, symlink creation
- ERROR: Sprint failures, initialization errors

**Log Context:**
All log entries MUST include:
- run_id
- sprint_num (if applicable)
- timestamp (ISO 8601)
```

**Add NFR7: Error Handling Requirements** (NEW)
```markdown
### NFR7: Error Handling Requirements

**Fail-Fast Principles:**
- Undefined variables MUST raise exceptions (no silent None)
- Missing adapter attributes MUST raise AttributeError
- File system errors MUST propagate (no silent fallback)

**Error Scenarios:**

| Scenario | Behavior | Error Type |
|----------|----------|------------|
| framework_dir not found | Raise RuntimeError with checked paths | RuntimeError |
| python_path is None | Raise RuntimeError before subprocess call | RuntimeError |
| sprint directory exists | Raise FileExistsError | FileExistsError |
| mkdir permission denied | Raise PermissionError | PermissionError |
| symlink creation fails | Raise OSError | OSError |
| run_end_time undefined | Raise UnboundLocalError | UnboundLocalError |

**Error Messages:**
- MUST include absolute paths
- MUST include suggested remediation (e.g., "Run ./setup.sh")
- MUST include context (run_id, sprint_num)
```

---

## 📋 Recommended Action Plan

### Phase 1: Critical Spec Updates (Before Commit)

1. **Add FR9: Adapter Lifecycle Management**
   - Document framework state vs sprint context separation
   - Specify attribute update strategy
   - Provide correct/incorrect examples
   - **Estimated time**: 30 minutes

2. **Add FR10: Critical Variable Lifecycle**
   - Document initialization points for run_start_time, run_end_time
   - Specify capture timing constraints
   - Add fail-fast requirements
   - **Estimated time**: 20 minutes

3. **Update FR2: Add adapter update table**
   - Add framework-specific subdirectory recreation requirements
   - Document environment variable updates (BAeS)
   - **Estimated time**: 20 minutes

4. **Update FR5: Clarify failure handling**
   - Define "partial artifacts"
   - Specify error log requirements
   - Clarify stop behavior
   - **Estimated time**: 15 minutes

5. **Update FR3: Add trend calculation algorithm**
   - Document threshold (10%)
   - Provide calculation example
   - **Estimated time**: 10 minutes

**Total Phase 1 time**: ~95 minutes (1.5 hours)

### Phase 2: High-Priority Enhancements (Post-Commit)

6. **Add NFR6: Logging Requirements**
   - Specify required log events
   - Define log levels
   - Document log context
   - **Estimated time**: 20 minutes

7. **Add NFR7: Error Handling Requirements**
   - Document fail-fast principles
   - Create error scenario table
   - Specify error message format
   - **Estimated time**: 25 minutes

8. **Update tasks.md with new requirements**
   - Add T019-requirements: "Update spec.md with FR9, FR10, NFR6, NFR7"
   - Mark as completed after spec updates
   - **Estimated time**: 10 minutes

**Total Phase 2 time**: ~55 minutes

### Phase 3: Documentation (Post-Commit)

9. **Create ADAPTER_LIFECYCLE.md** (separate guide)
   - Detailed adapter state management guide
   - Code examples for each framework
   - Troubleshooting common issues
   - **Estimated time**: 45 minutes

10. **Update quickstart.md**
    - Add "How Adapters Work" section
    - Reference new FR9/FR10
    - **Estimated time**: 15 minutes

**Total Phase 3 time**: ~60 minutes

---

## ✅ Immediate Next Steps

1. **Read this gap analysis thoroughly** (~10 min)
2. **Execute Phase 1: Update spec.md** (~95 min)
   - Add FR9, FR10
   - Update FR2, FR3, FR5 with clarifications
3. **Validate updates against checklist** (~20 min)
   - Re-check CHK001-CHK008 (should all be ✅)
4. **Commit changes** (~5 min)
   - Commit message: "docs: add adapter lifecycle and variable management requirements (FR9, FR10)"
   - Reference T017-T018 bugfixes in commit message
5. **Execute Phase 2 (optional pre-commit)** (~55 min)
   - Add NFR6, NFR7
   - Update tasks.md

**Total immediate work**: ~130 minutes (2.2 hours) for Phase 1 + validation + commit

---

## 🎯 Success Criteria

After completing these updates, the following should be true:

- ✅ CHK001-CHK008 (critical adapter lifecycle gaps) all marked complete
- ✅ CHK019-CHK021 (failure handling ambiguities) clarified
- ✅ CHK023 (trend calculation) documented
- ✅ Future implementers can avoid the bugs we fixed
- ✅ Spec clearly distinguishes framework state vs sprint context
- ✅ Variable initialization order is explicit and testable
- ✅ All three bugs (run_end_time, python_path, spec_md_path) are preventable by following spec

**Key Principle**: Anyone implementing from the updated spec should naturally avoid creating the bugs we just fixed. The spec should encode the lessons learned.
