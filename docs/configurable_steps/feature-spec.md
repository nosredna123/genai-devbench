# Feature Specification: Configurable Steps

## Feature ID
`FEAT-001-CONFIGURABLE-STEPS`

## Version
1.0.0

## Status
Planning

---

## Overview

### Problem Statement
Currently, the experiment framework executes a fixed sequence of 6 development steps for all runs. This limits flexibility for:
- Testing partial workflows (e.g., only steps 1-3)
- Skipping specific steps that may not be relevant for certain experiments
- Comparing framework performance at different complexity levels
- Debugging specific steps in isolation
- Reducing cost/time for iterative development

### Solution Summary
Implement a configuration system that allows users to:
1. Define which steps are enabled/disabled in `config.yaml`
2. Provide descriptive names for each step
3. Customize prompt files per step
4. Ensure all frameworks execute the same step configuration (for fair comparison)

### Design Choice: Option B (Detailed Steps Configuration)
The most flexible and explicit approach that provides:
- Complete control over each step
- Self-documenting configuration with descriptive names
- Per-step prompt file customization
- Clear enable/disable flags per step
- Maintains fairness by ensuring all frameworks use same steps

---

## User Stories

### US-1: Configure Step Subset
**As a** researcher  
**I want to** enable only steps 1-4  
**So that** I can test framework performance on simpler requirements without UI complexity

**Acceptance Criteria:**
- Can set `enabled: false` for steps 5 and 6 in config.yaml
- Runner executes only enabled steps
- Metrics collection respects enabled steps
- Terminal output shows "Step 1/4" instead of "Step 1/6"

### US-2: Skip Specific Step
**As a** researcher  
**I want to** skip step 3 (teacher assignment)  
**So that** I can test how frameworks handle the workflow without that relationship

**Acceptance Criteria:**
- Can set step 3 `enabled: false` in config.yaml
- Runner skips step 3 entirely
- Step numbering preserved in logs (step 2 → step 4)
- Metrics recorded with original step IDs

### US-3: Custom Step Names
**As a** user  
**I want to** see descriptive step names in output  
**So that** I understand what each step does without checking prompt files

**Acceptance Criteria:**
- Config includes optional `name` field per step
- Terminal output shows: "⋯ Step 1/6 (Initial CRUD) | 10:30:45"
- Log files include step names
- Names displayed in reports

### US-4: Custom Prompt Files
**As a** researcher  
**I want to** specify custom prompt files per step  
**So that** I can test variations of the same step

**Acceptance Criteria:**
- Config allows custom `prompt_file` path per step
- Runner loads prompts from specified paths
- Validation ensures prompt files exist

### US-5: Validation and Errors
**As a** user  
**I want to** receive clear error messages for invalid configurations  
**So that** I can fix issues before running experiments

**Acceptance Criteria:**
- Error if no steps enabled
- Error if step IDs invalid (not 1-6)
- Error if prompt files don't exist
- Error if duplicate step IDs

---

## Functional Requirements

### FR-1: Configuration Schema
**Priority:** MUST  
**Description:** Define YAML schema for step configuration

```yaml
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD Implementation"
    prompt_file: "config/prompts/step_1.txt"
    
  - id: 2
    enabled: true
    name: "Add Enrollment Relationship"
    prompt_file: "config/prompts/step_2.txt"
    
  - id: 3
    enabled: false  # Skip this step
    name: "Teacher Assignment"
    prompt_file: "config/prompts/step_3.txt"
```

**Validation Rules:**
- `steps` must be a list
- Each step must have `id` (integer, 1-6)
- Each step must have `enabled` (boolean)
- `name` is optional (string)
- `prompt_file` is optional (defaults to `config/prompts/step_{id}.txt`)
- At least one step must be enabled
- Step IDs must be unique
- Prompt files must exist

### FR-2: Config Loading and Validation
**Priority:** MUST  
**Description:** Load and validate steps configuration in `config_loader.py`

**Functions:**
- `validate_steps_config(config: Dict) -> None`
- `get_enabled_steps(config: Dict) -> List[StepConfig]`
- `_validate_step_entry(step: Dict) -> None`

### FR-3: Runner Execution
**Priority:** MUST  
**Description:** Execute only enabled steps in order

**Behavior:**
- Get list of enabled steps from config
- Iterate through enabled steps only
- Display progress as "Step N/M" where M = total enabled steps
- Preserve original step IDs in metrics/logs

### FR-4: Progress Display
**Priority:** MUST  
**Description:** Show step progress with names

**Format:**
```
⋯ Step 1/4 (#1: Initial CRUD) | 10:30:45
⋯ Step 2/4 (#2: Add Enrollment) | 10:35:12
⋯ Step 3/4 (#4: Validation) | 10:42:33  # Note: skipped #3
⋯ Step 4/4 (#5: Pagination) | 10:50:18
```

### FR-5: Metrics Recording
**Priority:** MUST  
**Description:** Record metrics with original step IDs

**Behavior:**
- Metrics use original step ID (1-6)
- Metrics include `step_name` field
- Reports indicate which steps were enabled
- Comparison metrics handle different step configs

### FR-6: Backwards Compatibility
**Priority:** MUST  
**Description:** Support existing configs without steps section

**Behavior:**
- If `steps` not in config, default to all 6 steps enabled
- Generate default step names from prompt file content
- No breaking changes to existing experiments

---

## Non-Functional Requirements

### NFR-1: Performance
- Config validation < 100ms
- No performance impact on step execution

### NFR-2: Usability
- Clear error messages with examples
- Self-documenting configuration
- Comprehensive header comments in generated config.yaml

### NFR-3: Maintainability
- Step configuration logic isolated in config_loader
- Easy to extend to more steps in future
- Type hints and docstrings for all functions

### NFR-4: Testability
- Unit tests for config validation
- Integration tests for partial step execution
- Test cases for all edge cases

---

## Technical Constraints

### TC-1: Framework Fairness
**Constraint:** All frameworks MUST execute the same steps  
**Rationale:** Ensure fair comparison across frameworks  
**Implementation:** Single global steps config (no framework-specific overrides)

### TC-2: Step ID Range
**Constraint:** Step IDs must be 1-6 (current prompt files)  
**Rationale:** Existing prompt infrastructure  
**Future:** Extend to support custom step ranges

### TC-3: Sequential Execution
**Constraint:** Steps must execute in ID order  
**Rationale:** Steps have dependencies (e.g., step 2 depends on step 1)  
**Implementation:** Sort enabled steps by ID before execution

---

## Dependencies

### Internal
- `src/orchestrator/config_loader.py` - Config validation
- `src/orchestrator/runner.py` - Step execution
- `generator/standalone_generator.py` - Config generation
- `templates/main.py` - Main execution template

### External
- PyYAML - Configuration parsing
- Existing prompt files in `config/prompts/`

---

## Risks and Mitigations

### Risk 1: Invalid Step Sequences
**Risk:** User enables step 4 but not step 1-3, causing failures  
**Severity:** HIGH  
**Mitigation:** Add validation warnings for non-sequential steps (not errors, since some sequences may work)

### Risk 2: Metrics Comparison
**Risk:** Comparing experiments with different enabled steps  
**Severity:** MEDIUM  
**Mitigation:** Include enabled steps in run manifest; add filter in analysis

### Risk 3: Prompt File Management
**Risk:** Custom prompt files not tracked in version control  
**Severity:** LOW  
**Mitigation:** Document best practices; validate files exist on load

---

## Out of Scope

- Framework-specific step configurations (enforcing fairness)
- Conditional step execution (if-then logic)
- Dynamic step generation
- Step dependencies graph
- Custom step IDs beyond 1-6
- Parallel step execution

---

## Success Criteria

1. ✅ User can enable/disable steps in config.yaml
2. ✅ Runner executes only enabled steps
3. ✅ Progress display shows correct step count
4. ✅ Metrics recorded with original step IDs
5. ✅ All existing experiments continue to work (backwards compatible)
6. ✅ Clear validation errors for invalid configs
7. ✅ Documentation and examples provided
8. ✅ All unit tests passing

---

## Timeline Estimate

- Phase 0 (Research): 1 hour
- Phase 1 (Design & Contracts): 2 hours
- Phase 2 (Implementation): 4 hours
- Phase 3 (Testing): 2 hours
- Phase 4 (Documentation): 1 hour

**Total:** ~10 hours
