# Phase 0: Research & Analysis

## Feature: Configurable Steps Configuration

**Date:** 2025-10-21  
**Status:** Complete

---

## Research Tasks

### RT-1: Existing Step Execution Flow

#### Current Implementation Analysis

**Location:** `src/orchestrator/runner.py:317`

```python
# Execute 6 steps sequentially
# TODO: #3 The number of steps must be loaded from config
for step_num in range(1, 7):
    log_context.set_step_context(step_num)
    
    # Load step prompt
    prompt_path = Path(f"config/prompts/step_{step_num}.txt")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        command_text = f.read().strip()
```

**Key Findings:**
1. Hardcoded range(1, 7) - needs to be dynamic
2. Step prompts loaded from `config/prompts/step_{N}.txt`
3. Step context set in logging for tracking
4. Progress display shows "Step N/6" - needs to show enabled count
5. Metrics recorded per step with step_num

**Decision:** Replace hardcoded range with dynamic list from config

---

### RT-2: Configuration Schema Patterns

#### YAML List vs Object Comparison

**Option A: Simple List**
```yaml
steps: [1, 2, 3, 4, 5, 6]
```
- ✅ Concise
- ❌ No metadata (names, custom prompts)
- ❌ Not self-documenting

**Option B: Detailed Objects** (SELECTED)
```yaml
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD"
    prompt_file: "config/prompts/step_1.txt"
```
- ✅ Self-documenting
- ✅ Flexible (metadata, custom prompts)
- ✅ Explicit enable/disable
- ❌ More verbose

**Decision:** Option B provides better UX and maintainability

**Rationale:**
- Self-documenting configuration aligns with project goals
- Explicit flags reduce user error
- Extensible for future features (timeouts per step, dependencies)
- Clear mapping between config and execution

---

### RT-3: Step Data Model

#### Required Fields
- `id` (int): Step number 1-6
- `enabled` (bool): Whether to execute this step

#### Optional Fields
- `name` (str): Descriptive name for logs/reports
- `prompt_file` (str): Path to prompt file (default: `config/prompts/step_{id}.txt`)

#### Future Extensions
- `timeout` (int): Per-step timeout override
- `retries` (int): Per-step retry override
- `depends_on` (List[int]): Step dependency declaration

**Decision:** Start with required + 2 optional fields

---

### RT-4: Validation Rules

#### Critical Validations (Must Error)
1. `steps` must be a list
2. At least one step enabled
3. Step IDs must be 1-6 (current constraint)
4. Step IDs must be unique
5. Prompt files must exist
6. `id` and `enabled` fields required
7. `enabled` must be boolean

#### Warning Validations (Should Warn)
1. Non-sequential enabled steps (e.g., 1,3,5)
2. All steps disabled
3. Missing step names (use defaults)

#### Defaults
- `prompt_file`: `config/prompts/step_{id}.txt`
- `name`: Generate from first line of prompt file or "Step {id}"

**Decision:** Strict validation to prevent runtime errors

---

### RT-5: Backwards Compatibility Strategy

#### Scenarios

**Scenario 1:** Existing config without `steps` section
```yaml
# No steps section
frameworks:
  baes:
    enabled: true
```

**Handling:** Auto-generate default steps config
```python
if 'steps' not in config:
    config['steps'] = [
        {'id': i, 'enabled': True, 'name': f'Step {i}', 
         'prompt_file': f'config/prompts/step_{i}.txt'}
        for i in range(1, 7)
    ]
```

**Scenario 2:** Invalid steps config

**Handling:** Clear error message with example:
```
ConfigValidationError: Invalid 'steps' configuration.

Expected format:
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD"
    prompt_file: "config/prompts/step_1.txt"
```

**Decision:** Seamless backwards compatibility with helpful errors

---

### RT-6: Progress Display Format

#### Current Format
```
⋯ Step 1/6 | 10:30:45
⋯ Step 2/6 | 10:35:12
```

#### Proposed Format (with names)
```
⋯ Step 1/4 (#1: Initial CRUD) | 10:30:45
⋯ Step 2/4 (#2: Add Enrollment) | 10:35:12
⋯ Step 3/4 (#4: Validation & Error Handling) | 10:42:33
⋯ Step 4/4 (#5: Pagination & Filtering) | 10:50:18
```

**Format Breakdown:**
- `Step 1/4`: Current step / Total enabled steps
- `#1`: Original step ID (for metrics traceability)
- `Initial CRUD`: Step name from config
- `10:30:45`: Timestamp

**Decision:** Show both sequential count and original ID

**Rationale:**
- Sequential count shows progress (1/4 = 25%)
- Original ID maintains traceability in logs
- Name provides context without checking prompts

---

### RT-7: Metrics Recording Strategy

#### Options Considered

**Option A: Sequential IDs**
- Record steps as 1, 2, 3, 4 (ignoring original IDs)
- ❌ Loses traceability
- ❌ Can't compare runs with different configs

**Option B: Original IDs** (SELECTED)
- Record steps with original IDs (1, 2, 4, 5)
- ✅ Maintains traceability
- ✅ Enables comparison across configs
- ✅ Clear gaps show skipped steps

**Option C: Dual Recording**
- Record both sequential and original
- ❌ Overcomplicated
- ❌ Storage overhead

**Decision:** Record with original step IDs

**Implementation:**
```python
# Metrics collection
for step_index, step_config in enumerate(enabled_steps, start=1):
    step_id = step_config['id']
    
    # Execute step
    result = self._execute_step_with_retry(step_id, command_text)
    
    # Record with ORIGINAL step_id
    self.metrics_collector.record_step(
        step_num=step_id,  # Original: 1, 2, 4, 5 (not 1, 2, 3, 4)
        step_name=step_config.get('name', f'Step {step_id}'),
        ...
    )
```

---

### RT-8: Configuration Generation

#### Generator Updates Required

**File:** `generator/standalone_generator.py`

**Current Behavior:**
- Copies prompt files to experiment directory
- Generates basic config.yaml

**Required Changes:**
1. Generate default steps configuration
2. Add explanatory comments for steps section
3. Include step descriptions in header

**Template:**
```python
def _generate_default_steps_config(self) -> List[Dict]:
    """Generate default steps configuration."""
    step_descriptions = {
        1: "Initial CRUD Implementation",
        2: "Add Enrollment Relationship", 
        3: "Teacher Assignment",
        4: "Validation & Error Handling",
        5: "Pagination & Filtering",
        6: "User Interface"
    }
    
    return [
        {
            'id': i,
            'enabled': True,
            'name': step_descriptions[i],
            'prompt_file': f'config/prompts/step_{i}.txt'
        }
        for i in range(1, 7)
    ]
```

**Header Comment Template:**
```yaml
# ============================================================
# Steps Configuration
# ============================================================
# Define which development steps to execute in the workflow.
# Each step can be individually enabled/disabled for testing
# different development patterns.
#
# Fields:
#   - id: Step number (1-6)
#   - enabled: Whether to execute this step (true/false)
#   - name: Descriptive name (optional, for logs/reports)
#   - prompt_file: Path to prompt file (optional, defaults to config/prompts/step_{id}.txt)
#
# Note: All frameworks execute the same steps to ensure fair comparison.
#
# Step Descriptions:
#   1. Initial CRUD - Create basic Student/Course/Teacher CRUD with FastAPI
#   2. Enrollment - Add Student-Course enrollment relationship
#   3. Teacher Assignment - Add Teacher-Course assignment relationship  
#   4. Validation - Add input validation and error handling
#   5. Pagination - Add pagination and filtering to list endpoints
#   6. User Interface - Create web UI for CRUD operations
# ============================================================
```

---

### RT-9: Error Message Design

#### Error Categories

**E1: Invalid Steps Structure**
```python
if not isinstance(config.get('steps'), list):
    raise ConfigValidationError(
        "Invalid 'steps' configuration: must be a list.\n\n"
        "Expected format:\n"
        "steps:\n"
        "  - id: 1\n"
        "    enabled: true\n"
        "    name: 'Initial CRUD'\n"
    )
```

**E2: No Steps Enabled**
```python
if not any(s['enabled'] for s in steps):
    raise ConfigValidationError(
        "No steps enabled. At least one step must be enabled.\n"
        "Set 'enabled: true' for at least one step."
    )
```

**E3: Invalid Step ID**
```python
if step['id'] not in range(1, 7):
    raise ConfigValidationError(
        f"Invalid step ID: {step['id']}. "
        f"Step IDs must be between 1 and 6.\n"
        f"Available steps: 1, 2, 3, 4, 5, 6"
    )
```

**E4: Missing Prompt File**
```python
if not prompt_path.exists():
    raise ConfigValidationError(
        f"Prompt file not found: {prompt_path}\n"
        f"For step {step['id']}, expected file at:\n"
        f"  {prompt_path.absolute()}\n"
        f"Create the file or update 'prompt_file' in config."
    )
```

**E5: Duplicate Step IDs**
```python
if len(step_ids) != len(set(step_ids)):
    duplicates = [id for id in step_ids if step_ids.count(id) > 1]
    raise ConfigValidationError(
        f"Duplicate step IDs found: {duplicates}\n"
        f"Each step ID must be unique."
    )
```

**Decision:** Clear, actionable error messages with examples

---

## Technology Stack

### Existing Dependencies
- **PyYAML** (3.13): YAML parsing
- **Python 3.11+**: Type hints, pathlib
- **Pydantic** (optional): Could use for validation

### No New Dependencies Required
- Standard library sufficient for validation
- Existing YAML infrastructure works

---

## Best Practices Applied

### BP-1: Configuration Design
- **Explicit over Implicit**: Require `enabled` flag (not inferred)
- **Self-Documenting**: Include names and comments
- **Fail Fast**: Validate at load time, not runtime
- **Defaults**: Sensible defaults for optional fields

### BP-2: Validation Pattern
```python
def validate_config(config: Dict) -> None:
    """Validate entire config"""
    validate_steps_config(config)
    # ... other validations

def validate_steps_config(config: Dict) -> None:
    """Validate steps section"""
    _validate_steps_structure(config['steps'])
    for step in config['steps']:
        _validate_step_entry(step)
    _validate_steps_integrity(config['steps'])

def _validate_step_entry(step: Dict) -> None:
    """Validate single step"""
    _check_required_fields(step)
    _check_field_types(step)
    _check_field_values(step)
```

### BP-3: Error Handling
- Specific exception types
- Helpful error messages
- Examples in errors
- Path information in file errors

### BP-4: Testing Strategy
- Unit tests for validation functions
- Integration tests for execution flow
- Edge case coverage (empty, invalid, missing)
- Backwards compatibility tests

---

## Implementation Dependencies

### Files to Modify
1. `src/orchestrator/config_loader.py` - Validation logic
2. `src/orchestrator/runner.py` - Execution logic
3. `generator/standalone_generator.py` - Config generation
4. `templates/main.py` - Template updates (if needed)

### Files to Create
1. `tests/unit/test_steps_config.py` - Unit tests
2. `tests/integration/test_steps_execution.py` - Integration tests

### Order of Implementation
1. Config loader validation (isolated, testable)
2. Runner execution updates (depends on #1)
3. Generator updates (depends on #1)
4. Integration testing (depends on #1-3)
5. Documentation updates (final)

---

## Alternatives Considered

### Alternative 1: Framework-Specific Steps
```yaml
frameworks:
  baes:
    steps: [1, 2, 3, 4, 5]  # No UI
  chatdev:
    steps: [1, 2, 3, 4, 5, 6]  # Full workflow
```

**Rejected Reason:** Violates fairness requirement - all frameworks must run same steps for valid comparison

### Alternative 2: Simple List Format
```yaml
steps: [1, 2, 4, 5]  # Skip steps 3 and 6
```

**Rejected Reason:** Not self-documenting, can't add metadata, harder to understand

### Alternative 3: Step Range Notation
```yaml
steps: "1-4,6"  # Steps 1,2,3,4,6
```

**Rejected Reason:** Less explicit, harder to parse, no metadata support

---

## Open Questions

### Q1: Should we validate step dependencies?
**Question:** If step 4 depends on step 1, should we error if 1 is disabled?  
**Answer:** NO - keep validation simple, let frameworks fail naturally if dependencies missing  
**Rationale:** Dependency detection is complex and may vary by framework

### Q2: Should we support custom step IDs beyond 1-6?
**Question:** Allow step IDs like 7, 8, 9 for custom steps?  
**Answer:** NO - out of scope for v1, can extend later  
**Rationale:** Current prompt infrastructure assumes 1-6

### Q3: Should step names be required?
**Question:** Make `name` field mandatory?  
**Answer:** NO - optional with sensible default  
**Rationale:** Reduces verbosity, can default to prompt summary

---

## Risk Analysis

### Risk: Non-Sequential Steps Causing Failures
**Probability:** MEDIUM  
**Impact:** HIGH  
**Mitigation:** 
- Log warning for non-sequential steps
- Document step dependencies in config comments
- Include troubleshooting guide

### Risk: Metrics Comparison Across Different Configs
**Probability:** LOW  
**Impact:** MEDIUM  
**Mitigation:**
- Include enabled steps in run manifest
- Add filter in analysis to compare same-step runs
- Document in analysis reports

### Risk: User Error in Configuration
**Probability:** HIGH  
**Impact:** LOW  
**Mitigation:**
- Comprehensive validation
- Clear error messages
- Examples in documentation
- Generated configs have all steps enabled by default

---

## Conclusion

**Ready for Implementation:** ✅ YES

All unknowns resolved:
- ✅ Configuration schema defined (Option B)
- ✅ Validation rules specified
- ✅ Execution flow mapped
- ✅ Progress display format designed
- ✅ Metrics strategy decided
- ✅ Backwards compatibility ensured
- ✅ Error handling designed
- ✅ No new dependencies needed

**Proceed to Phase 1: Design & Contracts**
