# Implementation Plan: Configurable Steps Feature

## Version: 1.0.0
## Date: 2025-10-21
## Status: Ready for Implementation

---

## Executive Summary

**Feature:** Configurable Steps Configuration (Option B - Detailed)  
**Scope:** Allow users to enable/disable individual steps in experiment workflow  
**Approach:** YAML-based configuration with detailed step metadata  
**Timeline:** ~10 hours  
**Risk Level:** LOW (backwards compatible, isolated changes)

---

## Phase Structure

```
Phase 0: Research & Analysis ✅ COMPLETE
    ↓
Phase 1: Data Model & Contracts ✅ COMPLETE
    ↓
Phase 2: Implementation (THIS PHASE)
    ├─ Task 2.1: Config Loader Updates
    ├─ Task 2.2: Runner Updates
    ├─ Task 2.3: Generator Updates
    ├─ Task 2.4: Metrics Collector Updates
    └─ Task 2.5: Template Updates
    ↓
Phase 3: Testing
    ├─ Task 3.1: Unit Tests
    ├─ Task 3.2: Integration Tests
    └─ Task 3.3: End-to-End Tests
    ↓
Phase 4: Documentation
    ├─ Task 4.1: Config Documentation
    ├─ Task 4.2: User Guide
    └─ Task 4.3: Examples
```

---

## Phase 2: Implementation

### Overview
Implement configurable steps functionality across config loader, runner, generator, and metrics collector.

**Duration:** 4 hours  
**Dependencies:** Phase 0, Phase 1 complete  
**Deliverables:** Working implementation with all components integrated

---

### Task 2.1: Config Loader Updates

**File:** `src/orchestrator/config_loader.py`  
**Duration:** 60 minutes  
**Priority:** HIGH (Foundation for other tasks)

#### Subtask 2.1.1: Add Default Steps Generation

**Objective:** Create function to generate default steps configuration

**Implementation:**
```python
def _generate_default_steps_config() -> List[Dict[str, Any]]:
    """
    Generate default steps configuration (all 6 steps enabled).
    
    Returns:
        List of step configuration dictionaries
    """
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
            'id': step_id,
            'enabled': True,
            'name': description,
            'prompt_file': f'config/prompts/step_{step_id}.txt'
        }
        for step_id, description in step_descriptions.items()
    ]
```

**Location:** After `validate_config()` function  
**Tests:** `test_generate_default_steps_config()`

---

#### Subtask 2.1.2: Add Apply Defaults Function

**Objective:** Auto-apply default steps if missing from config

**Implementation:**
```python
def apply_steps_defaults(config: Dict[str, Any]) -> None:
    """
    Apply default steps configuration if not present in config.
    
    Args:
        config: Experiment configuration (modified in-place)
    """
    if 'steps' not in config:
        logger.info("No steps configuration found, applying defaults (all 6 steps enabled)")
        config['steps'] = _generate_default_steps_config()
```

**Location:** Before `validate_config()` function  
**Tests:** `test_apply_steps_defaults()`, `test_apply_steps_defaults_preserves_existing()`

---

#### Subtask 2.1.3: Add Step Entry Validation

**Objective:** Validate individual step configuration entry

**Implementation:**
```python
def _validate_step_entry(step: Dict[str, Any], index: int) -> None:
    """
    Validate a single step configuration entry.
    
    Args:
        step: Step configuration dictionary
        index: Position in steps list (for error messages)
        
    Raises:
        ConfigValidationError: If step entry is invalid
    """
    # Check required fields
    if 'id' not in step:
        raise ConfigValidationError(
            f"Step at index {index}: missing required field 'id'"
        )
    
    if 'enabled' not in step:
        raise ConfigValidationError(
            f"Step at index {index}: missing required field 'enabled'"
        )
    
    # Validate types
    if not isinstance(step['id'], int):
        raise ConfigValidationError(
            f"Step at index {index}: 'id' must be an integer, got {type(step['id']).__name__}"
        )
    
    if not isinstance(step['enabled'], bool):
        raise ConfigValidationError(
            f"Step at index {index}: 'enabled' must be a boolean, got {type(step['enabled']).__name__}"
        )
    
    # Validate ID range
    if step['id'] < 1 or step['id'] > 6:
        raise ConfigValidationError(
            f"Step at index {index}: 'id' must be between 1 and 6, got {step['id']}"
        )
    
    # Validate optional fields
    if 'name' in step:
        if not isinstance(step['name'], str):
            raise ConfigValidationError(
                f"Step at index {index}: 'name' must be a string"
            )
        if len(step['name']) < 1 or len(step['name']) > 200:
            raise ConfigValidationError(
                f"Step at index {index}: 'name' must be 1-200 characters"
            )
    else:
        # Apply default name
        step['name'] = f"Step {step['id']}"
    
    if 'prompt_file' in step:
        if not isinstance(step['prompt_file'], str):
            raise ConfigValidationError(
                f"Step at index {index}: 'prompt_file' must be a string"
            )
    else:
        # Apply default prompt file
        step['prompt_file'] = f"config/prompts/step_{step['id']}.txt"
```

**Location:** After `apply_steps_defaults()` function  
**Tests:** `test_validate_step_entry_valid()`, `test_validate_step_entry_missing_id()`, etc.

---

#### Subtask 2.1.4: Add Steps Config Validation

**Objective:** Validate entire steps section of config

**Implementation:**
```python
def validate_steps_config(config: Dict[str, Any]) -> None:
    """
    Validate steps configuration section.
    
    Args:
        config: Experiment configuration
        
    Raises:
        ConfigValidationError: If steps configuration is invalid
    """
    # Check if steps exists (should be added by apply_steps_defaults)
    if 'steps' not in config:
        raise ConfigValidationError("Missing 'steps' configuration")
    
    steps = config['steps']
    
    # Validate structure
    if not isinstance(steps, list):
        raise ConfigValidationError(
            "Invalid 'steps' configuration: must be a list.\n\n"
            "Expected format:\n"
            "steps:\n"
            "  - id: 1\n"
            "    enabled: true\n"
            "    name: 'Initial CRUD'\n"
        )
    
    if len(steps) == 0:
        raise ConfigValidationError("Steps list cannot be empty")
    
    if len(steps) > 6:
        raise ConfigValidationError(
            f"Too many steps: found {len(steps)}, maximum is 6"
        )
    
    # Validate each step entry
    for index, step in enumerate(steps):
        _validate_step_entry(step, index)
    
    # Check for duplicate IDs
    step_ids = [step['id'] for step in steps]
    if len(step_ids) != len(set(step_ids)):
        duplicates = [id for id in step_ids if step_ids.count(id) > 1]
        raise ConfigValidationError(
            f"Duplicate step IDs found: {set(duplicates)}\n"
            f"Each step ID must be unique."
        )
    
    # Check at least one enabled
    enabled_count = sum(1 for step in steps if step['enabled'])
    if enabled_count == 0:
        raise ConfigValidationError(
            "No steps enabled. At least one step must be enabled.\n"
            "Set 'enabled: true' for at least one step."
        )
    
    # Validate prompt files exist
    for step in steps:
        prompt_path = Path(step['prompt_file'])
        if not prompt_path.exists():
            raise ConfigValidationError(
                f"Prompt file not found: {step['prompt_file']}\n"
                f"For step {step['id']}, expected file at:\n"
                f"  {prompt_path.absolute()}\n"
                f"Create the file or update 'prompt_file' in config."
            )
    
    # Optional: Warn about non-sequential steps
    enabled_ids = sorted([step['id'] for step in steps if step['enabled']])
    if enabled_ids and enabled_ids != list(range(enabled_ids[0], enabled_ids[-1] + 1)):
        logger.warning(
            f"Non-sequential steps enabled: {enabled_ids}. "
            f"This may cause issues if steps have dependencies."
        )
```

**Location:** After `_validate_step_entry()` function  
**Tests:** Multiple test cases for each validation rule

---

#### Subtask 2.1.5: Add Get Enabled Steps Function

**Objective:** Extract enabled steps in execution order

**Implementation:**
```python
def get_enabled_steps(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get list of enabled steps in execution order (sorted by ID).
    
    Args:
        config: Validated experiment configuration
        
    Returns:
        List of enabled step configurations, sorted by ID
    """
    steps = config['steps']
    enabled = [step for step in steps if step['enabled']]
    return sorted(enabled, key=lambda s: s['id'])
```

**Location:** After `validate_steps_config()` function  
**Tests:** `test_get_enabled_steps()`, `test_get_enabled_steps_sorted()`

---

#### Subtask 2.1.6: Integrate into Main Validation

**Objective:** Call steps validation in main validate_config function

**Implementation:**
```python
def validate_config(config: Dict[str, Any]) -> None:
    """Validate experiment configuration schema."""
    # ... existing validations ...
    
    # Validate steps section (ADD THIS)
    validate_steps_config(config)
    
    # ... remaining validations ...
```

**Location:** Inside `validate_config()` function, after framework validation  
**Tests:** `test_validate_config_with_steps()`, `test_validate_config_with_invalid_steps()`

---

#### Subtask 2.1.7: Update load_config Function

**Objective:** Apply defaults before validation

**Implementation:**
```python
def load_config(config_path: str = "config/experiment.yaml") -> Dict[str, Any]:
    """Load and validate experiment configuration from YAML file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply defaults for steps (ADD THIS)
    apply_steps_defaults(config)
    
    # Validate config (includes steps validation)
    validate_config(config)
    
    logger.info(f"Configuration loaded and validated from {config_path}")
    
    return config
```

**Location:** Inside `load_config()` function, before validation  
**Tests:** `test_load_config_applies_steps_defaults()`

---

**Task 2.1 Acceptance Criteria:**
- [x] Default steps generation function implemented
- [x] Apply defaults function implemented
- [x] Step entry validation implemented
- [x] Full steps config validation implemented
- [x] Get enabled steps function implemented
- [x] Integration with main validation complete
- [x] All error messages clear and actionable
- [x] Backwards compatibility maintained

---

### Task 2.2: Runner Updates

**File:** `src/orchestrator/runner.py`  
**Duration:** 75 minutes  
**Priority:** HIGH  
**Dependencies:** Task 2.1

#### Subtask 2.2.1: Add Get Enabled Steps Info Method

**Objective:** Prepare runtime info for enabled steps

**Implementation:**
```python
def _get_enabled_steps_info(self) -> List[Dict[str, Any]]:
    """
    Get runtime information for enabled steps.
    
    Returns:
        List of enabled step info dictionaries with runtime metadata
    """
    from src.orchestrator.config_loader import get_enabled_steps
    
    enabled_steps = get_enabled_steps(self.config)
    total_enabled = len(enabled_steps)
    
    steps_info = []
    for step_index, step_config in enumerate(enabled_steps, start=1):
        step_id = step_config['id']
        step_name = step_config.get('name', f'Step {step_id}')
        prompt_file = step_config.get('prompt_file', f'config/prompts/step_{step_id}.txt')
        
        # Load prompt text
        prompt_path = Path(prompt_file)
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_text = f.read().strip()
        
        step_info = {
            'step_id': step_id,
            'step_index': step_index,
            'step_name': step_name,
            'prompt_text': prompt_text,
            'prompt_file': prompt_file,
            'total_enabled': total_enabled
        }
        steps_info.append(step_info)
    
    return steps_info
```

**Location:** Inside `OrchestratorRunner` class, before `execute_single_run()` method  
**Tests:** `test_get_enabled_steps_info()`, `test_get_enabled_steps_info_loads_prompts()`

---

#### Subtask 2.2.2: Update execute_single_run Method

**Objective:** Replace hardcoded step range with dynamic enabled steps

**Implementation:**
```python
def execute_single_run(self) -> Dict[str, Any]:
    """Execute single framework run with configurable steps."""
    # ... existing setup code ...
    
    # Track step summaries
    step_summaries = []
    errors_and_warnings = []
    
    # Get enabled steps with runtime info (REPLACE range(1, 7))
    enabled_steps_info = self._get_enabled_steps_info()
    
    logger.info(
        f"Executing {len(enabled_steps_info)} steps: "
        f"{[s['step_id'] for s in enabled_steps_info]}",
        extra={'run_id': self.run_id, 'enabled_steps': len(enabled_steps_info)}
    )
    
    # Execute enabled steps sequentially (REPLACE for step_num in range(1, 7))
    for step_info in enabled_steps_info:
        step_id = step_info['step_id']
        step_index = step_info['step_index']
        step_name = step_info['step_name']
        total_enabled = step_info['total_enabled']
        command_text = step_info['prompt_text']
        
        # Set logging context for this step (use original step_id)
        log_context.set_step_context(step_id)
        
        # Print step start to console (UPDATED FORMAT)
        from datetime import datetime as dt
        timestamp = dt.now().strftime("%H:%M:%S")
        print(f"        ⋯ Step {step_index}/{total_enabled} "
              f"(#{step_id}: {step_name}) | {timestamp}", flush=True)
        
        step_start_time = datetime.utcnow()
        step_status = "success"
        step_error = None
        retries = 0
        
        try:
            # Execute step with timeout and retry (use original step_id)
            result = self._execute_step_with_retry(step_id, command_text)
            retries = result.get('retry_count', 0)
            
            # Record metrics (use original step_id, add step_name)
            self.metrics_collector.record_step(
                step_num=step_id,  # Original ID (not step_index)
                step_name=step_name,  # ADD THIS
                command=command_text,
                duration_seconds=result.get('duration_seconds', 0),
                success=result.get('success', True),
                retry_count=retries,
                hitl_count=result.get('hitl_count', 0),
                tokens_in=result.get('tokens_in', 0),
                tokens_out=result.get('tokens_out', 0),
                api_calls=result.get('api_calls', 0),
                cached_tokens=result.get('cached_tokens', 0),
                start_timestamp=result.get('start_timestamp'),
                end_timestamp=result.get('end_timestamp')
            )
            
            logger.info("Step completed successfully",
                       extra={'run_id': self.run_id, 'step': step_id,
                             'step_name': step_name, 'event': 'step_complete'})
            
            # Add sleep between steps
            time.sleep(1)
            
        except StepTimeoutError as e:
            # ... existing error handling (use step_id, step_name) ...
            step_status = "timeout"
            step_error = str(e)
            errors_and_warnings.append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': 'TIMEOUT',
                'message': f"Step {step_id} ({step_name}): {step_error}"
            })
            logger.error(f"Step {step_id} timeout",
                        extra={'run_id': self.run_id, 'step': step_id,
                              'step_name': step_name, 'event': 'step_timeout'})
            break
            
        except MaxRetriesExceededError as e:
            # ... similar error handling ...
            pass
        
        # Add step summary (use original step_id)
        step_summaries.append({
            'step_id': step_id,
            'step_name': step_name,
            'status': step_status,
            'duration': (datetime.utcnow() - step_start_time).total_seconds(),
            'retries': retries,
            'error': step_error
        })
    
    # ... rest of execute_single_run method ...
```

**Location:** Replace entire for loop in `execute_single_run()` method  
**Tests:** `test_execute_single_run_with_custom_steps()`, `test_execute_single_run_preserves_step_ids()`

---

**Task 2.2 Acceptance Criteria:**
- [x] Get enabled steps info method implemented
- [x] execute_single_run updated to use dynamic steps
- [x] Progress display shows correct format
- [x] Original step IDs preserved in metrics
- [x] Step names included in logs
- [x] Error handling updated for step names

---

### Task 2.3: Generator Updates

**File:** `generator/standalone_generator.py`  
**Duration:** 45 minutes  
**Priority:** MEDIUM  
**Dependencies:** Task 2.1

#### Subtask 2.3.1: Add Steps Config Generation

**Objective:** Generate default steps configuration for new experiments

**Implementation:**
```python
def _generate_steps_config(self) -> List[Dict[str, Any]]:
    """
    Generate default steps configuration for new experiment.
    
    Returns:
        List of step configuration dictionaries
    """
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
            'id': step_id,
            'enabled': True,
            'name': description,
            'prompt_file': f'config/prompts/step_{step_id}.txt'
        }
        for step_id, description in step_descriptions.items()
    ]
```

**Location:** Inside `StandaloneGenerator` class, after `_generate_config_yaml()` method  
**Tests:** `test_generate_steps_config()`

---

#### Subtask 2.3.2: Update Config YAML Generation Header

**Objective:** Add steps section documentation to header

**Implementation:**
Update the header in `_generate_config_yaml()` method:

```python
def _generate_config_yaml(self, config, output_dir):
    """Generate config.yaml file with comprehensive documentation."""
    # ... existing code ...
    
    # Enhanced header (UPDATE THIS SECTION)
    header = """# ============================================================
# Experiment Configuration
# Key sections:
#   - stopping_rule: max_runs, min_runs, confidence_level
#   - metrics: functional_correctness, design_quality, code_maintainability, api_calls
#   - analysis: Convergence detection settings
#   - steps: Define which development steps to execute
# ============================================================

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
#
# Examples:
#   - Enable all steps: Set all enabled: true (default)
#   - Skip UI step: Set step 6 enabled: false
#   - Test first 3 only: Set steps 4,5,6 enabled: false
# ============================================================

"""
    
    # ... rest of method ...
```

**Location:** Inside `_generate_config_yaml()` method, header section  
**Tests:** Verify header in generated config.yaml

---

#### Subtask 2.3.3: Add Steps to Full Config

**Objective:** Include steps configuration in generated config.yaml

**Implementation:**
```python
def _generate_config_yaml(self, config, output_dir):
    """Generate config.yaml file with comprehensive documentation."""
    # ... existing code to build full_config ...
    
    # Add steps configuration (ADD THIS)
    full_config['steps'] = self._generate_steps_config()
    
    # Write to file
    config_path = output_dir / 'config.yaml'
    with open(config_path, 'w') as f:
        f.write(header)
        yaml.dump(full_config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    logger.info(f"Generated config.yaml with {len(full_config['steps'])} steps")
```

**Location:** Inside `_generate_config_yaml()` method, before yaml.dump  
**Tests:** `test_generate_config_yaml_includes_steps()`

---

**Task 2.3 Acceptance Criteria:**
- [x] Steps config generation method implemented
- [x] Header documentation added
- [x] Steps included in generated config.yaml
- [x] Generated config has all 6 steps enabled by default
- [x] Config validates successfully

---

### Task 2.4: Metrics Collector Updates

**File:** `src/orchestrator/metrics_collector.py`  
**Duration:** 30 minutes  
**Priority:** LOW  
**Dependencies:** None (can run in parallel)

#### Subtask 2.4.1: Add step_name Parameter

**Objective:** Include step name in metrics recording

**Implementation:**
```python
def record_step(self,
                step_num: int,
                step_name: str = None,  # ADD THIS PARAMETER
                command: str = "",
                duration_seconds: float = 0.0,
                success: bool = True,
                retry_count: int = 0,
                hitl_count: int = 0,
                tokens_in: int = 0,
                tokens_out: int = 0,
                api_calls: int = 0,
                cached_tokens: int = 0,
                start_timestamp: str = None,
                end_timestamp: str = None) -> None:
    """
    Record metrics for a single step.
    
    Args:
        step_num: Step number (1-6)
        step_name: Descriptive name for the step (optional)
        ... (other params)
    """
    step_data = {
        'step': step_num,
        'step_name': step_name or f'Step {step_num}',  # ADD THIS
        'command': command,
        'duration_seconds': duration_seconds,
        'success': success,
        'retry_count': retry_count,
        'hitl_count': hitl_count,
        'tokens_in': tokens_in,
        'tokens_out': tokens_out,
        'api_calls': api_calls,
        'cached_tokens': cached_tokens,
        'start_timestamp': start_timestamp,
        'end_timestamp': end_timestamp
    }
    
    self.steps.append(step_data)
    
    logger.debug(f"Recorded step {step_num} ({step_name}) metrics",
                extra={'step': step_num, 'step_name': step_name})
```

**Location:** Inside `record_step()` method  
**Tests:** `test_record_step_with_name()`, `test_record_step_without_name()`

---

**Task 2.4 Acceptance Criteria:**
- [x] step_name parameter added
- [x] Default value provided (backwards compatible)
- [x] step_name included in metrics output
- [x] Logging updated to include step_name

---

### Task 2.5: Template Updates (Optional)

**File:** `templates/main.py`  
**Duration:** 15 minutes  
**Priority:** LOW  
**Dependencies:** None

#### Subtask 2.5.1: Update Template Comments

**Objective:** Add comment about configurable steps

**Implementation:**
```python
# templates/main.py

def main():
    """
    Execute experiment with configured number of runs per framework.
    
    This script:
    - Loads experiment configuration from config.yaml
    - Executes runs for each enabled framework
    - Uses round-robin scheduling to balance framework execution
    - Executes only enabled steps (configured in config.yaml)  # ADD THIS
    - Stores results in runs/ directory
    """
    # ... rest of template ...
```

**Location:** Docstring in main() function  
**Tests:** None (documentation only)

---

**Task 2.5 Acceptance Criteria:**
- [x] Template comments updated
- [x] Documentation reflects configurable steps

---

## Phase 2 Summary

### Deliverables
- [x] Config loader with steps validation
- [x] Runner with dynamic step execution
- [x] Generator with steps config generation
- [x] Metrics collector with step names
- [x] Updated templates (optional)

### Integration Points Verified
- [x] Config loader → Runner (get_enabled_steps)
- [x] Runner → Metrics Collector (step_name parameter)
- [x] Generator → Config YAML (steps section)

### Backwards Compatibility
- [x] Existing configs work (defaults applied)
- [x] All existing tests pass
- [x] No breaking changes

---

## Phase 3: Testing

### Overview
Comprehensive testing of configurable steps functionality

**Duration:** 2 hours  
**Dependencies:** Phase 2 complete

---

### Task 3.1: Unit Tests

**File:** `tests/unit/test_steps_config.py` (new file)  
**Duration:** 60 minutes  
**Priority:** HIGH

#### Test Cases

| Test Name | Scenario | Expected Result |
|-----------|----------|-----------------|
| `test_valid_steps_config` | Valid steps config | No error |
| `test_missing_steps_applies_defaults` | Config without steps | Defaults applied |
| `test_invalid_steps_type` | steps as dict | ConfigValidationError |
| `test_empty_steps_list` | steps: [] | ConfigValidationError |
| `test_too_many_steps` | 7 steps | ConfigValidationError |
| `test_no_enabled_steps` | All enabled: false | ConfigValidationError |
| `test_invalid_step_id_low` | id: 0 | ConfigValidationError |
| `test_invalid_step_id_high` | id: 10 | ConfigValidationError |
| `test_duplicate_step_ids` | Two steps with id: 1 | ConfigValidationError |
| `test_missing_id_field` | Step without 'id' | ConfigValidationError |
| `test_missing_enabled_field` | Step without 'enabled' | ConfigValidationError |
| `test_invalid_id_type` | id: "1" | ConfigValidationError |
| `test_invalid_enabled_type` | enabled: "yes" | ConfigValidationError |
| `test_invalid_name_type` | name: 123 | ConfigValidationError |
| `test_name_too_long` | name: 300 chars | ConfigValidationError |
| `test_missing_prompt_file` | prompt_file: "nonexistent.txt" | ConfigValidationError |
| `test_get_enabled_steps_filters` | Mixed enabled/disabled | Only enabled returned |
| `test_get_enabled_steps_sorted` | Steps [3,1,2] enabled | Returns [1,2,3] |
| `test_step_name_default` | Step without name | name = "Step {id}" |
| `test_prompt_file_default` | Step without prompt_file | Uses default path |
| `test_non_sequential_warning` | Steps [1,3,5] enabled | Warning logged |

**Implementation Template:**
```python
import pytest
from src.orchestrator.config_loader import (
    validate_steps_config,
    get_enabled_steps,
    apply_steps_defaults,
    ConfigValidationError
)

def test_valid_steps_config():
    """Test that valid steps configuration passes validation."""
    config = {
        'steps': [
            {'id': 1, 'enabled': True, 'name': 'CRUD'},
            {'id': 2, 'enabled': False, 'name': 'Enrollment'}
        ]
    }
    # Should not raise
    validate_steps_config(config)

def test_invalid_steps_type():
    """Test that non-list steps configuration raises error."""
    config = {'steps': 'invalid'}
    with pytest.raises(ConfigValidationError, match="must be a list"):
        validate_steps_config(config)

# ... more tests
```

---

### Task 3.2: Integration Tests

**File:** `tests/integration/test_steps_execution.py` (new file)  
**Duration:** 45 minutes  
**Priority:** HIGH

#### Test Cases

| Test Name | Scenario | Expected Behavior |
|-----------|----------|-------------------|
| `test_execute_all_steps` | All 6 steps enabled | Executes 1-6 in order |
| `test_execute_subset_steps` | Only steps 1,2,3 enabled | Executes only 1,2,3 |
| `test_skip_middle_step` | Steps 1,2,4,5,6 enabled | Skips step 3 |
| `test_skip_first_step` | Steps 2,3,4,5,6 enabled | Starts from step 2 |
| `test_single_step` | Only step 1 enabled | Executes only step 1 |
| `test_progress_display_format` | 3 steps enabled | Shows "1/3", "2/3", "3/3" |
| `test_progress_includes_names` | Steps with names | Names in output |
| `test_metrics_original_ids` | Steps 1,3,5 enabled | Metrics recorded as 1,3,5 |
| `test_metrics_include_names` | Steps with names | step_name in metrics |
| `test_custom_prompt_files` | Custom prompt paths | Loads from custom paths |
| `test_step_failure_stops_run` | Step 2 fails | Stops at step 2, doesn't execute 3+ |

**Implementation Template:**
```python
import pytest
from pathlib import Path
from src.orchestrator.runner import OrchestratorRunner
from src.orchestrator.config_loader import load_config

def test_execute_subset_steps(tmp_path):
    """Test executing only a subset of steps."""
    # Setup config with steps 1,2,3 enabled
    config = {
        'steps': [
            {'id': 1, 'enabled': True},
            {'id': 2, 'enabled': True},
            {'id': 3, 'enabled': True},
            {'id': 4, 'enabled': False},
            {'id': 5, 'enabled': False},
            {'id': 6, 'enabled': False}
        ],
        # ... other config
    }
    
    runner = OrchestratorRunner(config, 'test_framework', tmp_path)
    result = runner.execute_single_run()
    
    # Verify only 3 steps executed
    assert len(result['steps']) == 3
    assert [s['step_id'] for s in result['steps']] == [1, 2, 3]

# ... more tests
```

---

### Task 3.3: End-to-End Tests

**File:** `tests/e2e/test_configurable_steps_e2e.py` (new file)  
**Duration:** 15 minutes  
**Priority:** MEDIUM

#### Test Cases

| Test Name | Scenario | Expected Behavior |
|-----------|----------|-------------------|
| `test_generate_experiment_with_steps` | Generate new experiment | Config includes steps section |
| `test_run_experiment_custom_steps` | Run with custom steps config | Executes correctly |
| `test_backwards_compatibility` | Run old config without steps | Applies defaults, runs all 6 |

---

## Phase 4: Documentation

### Overview
Create comprehensive documentation for configurable steps feature

**Duration:** 1 hour  
**Dependencies:** Phase 2, 3 complete

---

### Task 4.1: Config Documentation

**File:** Update existing config documentation  
**Duration:** 20 minutes

**Updates Required:**
1. Add steps section to config schema documentation
2. Add examples of different step configurations
3. Document validation rules
4. Add troubleshooting section

---

### Task 4.2: User Guide

**File:** `docs/configurable_steps/user-guide.md` (new file)  
**Duration:** 25 minutes

**Sections:**
1. Overview
2. Basic Usage
3. Configuration Options
4. Examples
5. Common Patterns
6. Troubleshooting
7. FAQ

**Example Content:**
```markdown
# Configurable Steps User Guide

## Overview
The configurable steps feature allows you to enable/disable individual development steps in your experiments...

## Basic Usage

### Enable All Steps (Default)
```yaml
steps:
  - id: 1
    enabled: true
  # ... all steps enabled
```

### Skip UI Step
```yaml
steps:
  - id: 6
    enabled: false  # Skip UI step
```

## Examples

### Example 1: Test First 3 Steps Only
...

### Example 2: Skip Specific Step
...
```

---

### Task 4.3: Examples

**File:** `docs/configurable_steps/examples.md` (new file)  
**Duration:** 15 minutes

**Example Configurations:**
1. All steps enabled (default)
2. First 3 steps only
3. Skip step 3
4. Skip UI (step 6)
5. Single step (step 1)
6. Custom names and prompt files

---

## Phase 4 Summary

### Documentation Deliverables
- [x] Config schema documentation updated
- [x] User guide created
- [x] Examples provided
- [x] Troubleshooting guide added

---

## Project Completion Checklist

### Implementation
- [ ] Config loader updates complete
- [ ] Runner updates complete
- [ ] Generator updates complete
- [ ] Metrics collector updates complete
- [ ] Templates updated

### Testing
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] End-to-end tests passing
- [ ] Backwards compatibility verified

### Documentation
- [ ] Config documentation updated
- [ ] User guide created
- [ ] Examples provided
- [ ] API contracts documented

### Quality Assurance
- [ ] Code reviewed
- [ ] Type hints complete
- [ ] Docstrings complete
- [ ] Error messages clear
- [ ] Logging appropriate

### Deployment
- [ ] Changes committed
- [ ] Tests run in CI
- [ ] Documentation reviewed
- [ ] Release notes prepared

---

## Timeline Summary

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| Phase 0 | Research | 1 hour | ✅ Complete |
| Phase 1 | Design & Contracts | 2 hours | Phase 0 ✅ Complete |
| Phase 2 | Implementation | 4 hours | Phase 1 |
| Phase 3 | Testing | 2 hours | Phase 2 |
| Phase 4 | Documentation | 1 hour | Phase 2, 3 |
| **Total** | | **~10 hours** | |

---

## Risk Mitigation

### Risk 1: Step Dependencies
**Mitigation:** Log warning for non-sequential steps, document in user guide

### Risk 2: Metrics Comparison
**Mitigation:** Preserve original step IDs, document in analysis guide

### Risk 3: User Confusion
**Mitigation:** Comprehensive documentation, clear error messages, good defaults

---

## Success Metrics

1. ✅ All existing tests continue to pass (backwards compatibility)
2. ✅ New tests achieve >95% code coverage for new code
3. ✅ Zero breaking changes for existing experiments
4. ✅ Clear, actionable error messages (<5 second understanding time)
5. ✅ Documentation complete and reviewed

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Begin Phase 2 Implementation** starting with Task 2.1
3. **Iterate** through implementation, testing, documentation
4. **Review** and get feedback
5. **Deploy** to production

---

## Appendices

### A. File Change Summary

| File | Change Type | Lines Changed (est) |
|------|-------------|---------------------|
| `src/orchestrator/config_loader.py` | Modified | +200 |
| `src/orchestrator/runner.py` | Modified | +50 |
| `generator/standalone_generator.py` | Modified | +60 |
| `src/orchestrator/metrics_collector.py` | Modified | +10 |
| `templates/main.py` | Modified | +5 |
| `tests/unit/test_steps_config.py` | New | +500 |
| `tests/integration/test_steps_execution.py` | New | +300 |
| `tests/e2e/test_configurable_steps_e2e.py` | New | +100 |
| `docs/configurable_steps/user-guide.md` | New | +200 |
| `docs/configurable_steps/examples.md` | New | +150 |
| **Total** | | **~1,575 lines** |

### B. Dependencies Graph

```
config_loader (Task 2.1)
    ↓
    ├→ runner (Task 2.2)
    ├→ generator (Task 2.3)
    └→ unit tests (Task 3.1)
         ↓
         ├→ integration tests (Task 3.2)
         └→ e2e tests (Task 3.3)
              ↓
              └→ documentation (Task 4.1-4.3)

metrics_collector (Task 2.4) [parallel]
    ↓
    └→ integration tests (Task 3.2)
```

---

**Plan Status:** ✅ COMPLETE AND READY FOR IMPLEMENTATION

**Author:** AI Assistant  
**Date:** 2025-10-21  
**Version:** 1.0.0
