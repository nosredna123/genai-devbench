# API Contracts: Configurable Steps

## Version: 1.0.0
## Date: 2025-10-21

---

## 1. Configuration Loader API

### 1.1 `validate_steps_config(config: Dict[str, Any]) -> None`

**Module:** `src/orchestrator/config_loader.py`

**Purpose:** Validate the steps section of experiment configuration

**Parameters:**
- `config` (Dict[str, Any]): Complete experiment configuration dictionary

**Returns:** `None`

**Raises:**
- `ConfigValidationError`: If steps configuration is invalid

**Behavior:**
1. Check if 'steps' key exists (apply defaults if missing)
2. Validate steps structure (must be list)
3. Validate each step entry
4. Check integrity constraints (uniqueness, at least one enabled)
5. Validate prompt file existence

**Pre-conditions:**
- `config` is a valid dictionary
- Config loader initialized

**Post-conditions:**
- `config['steps']` is valid or error raised
- All prompt files verified to exist

**Example:**
```python
from src.orchestrator.config_loader import validate_steps_config

config = {
    'steps': [
        {'id': 1, 'enabled': True, 'name': 'CRUD', 'prompt_file': 'config/prompts/step_1.txt'},
        {'id': 2, 'enabled': False, 'name': 'Enrollment', 'prompt_file': 'config/prompts/step_2.txt'}
    ]
}

validate_steps_config(config)  # Validates or raises ConfigValidationError
```

**Error Cases:**

| Error | Condition | Message |
|-------|-----------|---------|
| `InvalidType` | `steps` is not a list | "Invalid 'steps' configuration: must be a list" |
| `EmptySteps` | `steps` list is empty | "Steps list cannot be empty" |
| `NoEnabledSteps` | All steps have `enabled: false` | "No steps enabled. At least one step must be enabled" |
| `InvalidStepEntry` | Step missing required fields | "Step at index {i}: missing required field '{field}'" |
| `DuplicateStepIds` | Multiple steps with same ID | "Duplicate step IDs found: {ids}" |
| `MissingPromptFile` | Prompt file doesn't exist | "Prompt file not found: {path}" |

---

### 1.2 `get_enabled_steps(config: Dict[str, Any]) -> List[Dict[str, Any]]`

**Module:** `src/orchestrator/config_loader.py`

**Purpose:** Get list of enabled steps in execution order

**Parameters:**
- `config` (Dict[str, Any]): Validated experiment configuration

**Returns:** `List[Dict[str, Any]]` - List of enabled step configurations, sorted by ID

**Raises:** None (assumes pre-validated config)

**Behavior:**
1. Filter steps where `enabled: true`
2. Sort filtered steps by `id` (ascending)
3. Return sorted list

**Pre-conditions:**
- `config` has been validated
- `config['steps']` exists and is valid

**Post-conditions:**
- Returns only enabled steps
- Steps ordered by ID

**Example:**
```python
from src.orchestrator.config_loader import get_enabled_steps

config = {
    'steps': [
        {'id': 1, 'enabled': True, 'name': 'CRUD'},
        {'id': 2, 'enabled': False, 'name': 'Enrollment'},
        {'id': 3, 'enabled': True, 'name': 'Teacher'}
    ]
}

enabled = get_enabled_steps(config)
# Returns: [
#   {'id': 1, 'enabled': True, 'name': 'CRUD'},
#   {'id': 3, 'enabled': True, 'name': 'Teacher'}
# ]
```

---

### 1.3 `_validate_step_entry(step: Dict[str, Any], index: int) -> None`

**Module:** `src/orchestrator/config_loader.py` (private)

**Purpose:** Validate a single step configuration entry

**Parameters:**
- `step` (Dict[str, Any]): Single step configuration
- `index` (int): Position in steps list (for error messages)

**Returns:** `None`

**Raises:**
- `ConfigValidationError`: If step entry is invalid

**Behavior:**
1. Check required fields (`id`, `enabled`)
2. Validate field types
3. Validate field values (ID range, name length)
4. Set defaults for optional fields

**Validation Rules:**

| Field | Check | Error Message |
|-------|-------|---------------|
| `id` | Required | "Step at index {i}: missing required field 'id'" |
| `id` | Type int | "Step at index {i}: 'id' must be an integer" |
| `id` | Range 1-6 | "Step at index {i}: 'id' must be between 1 and 6, got {id}" |
| `enabled` | Required | "Step at index {i}: missing required field 'enabled'" |
| `enabled` | Type bool | "Step at index {i}: 'enabled' must be a boolean" |
| `name` | Type str (if present) | "Step at index {i}: 'name' must be a string" |
| `name` | Length 1-200 | "Step at index {i}: 'name' must be 1-200 characters" |
| `prompt_file` | Type str (if present) | "Step at index {i}: 'prompt_file' must be a string" |

**Example:**
```python
from src.orchestrator.config_loader import _validate_step_entry

step = {'id': 1, 'enabled': True, 'name': 'CRUD'}
_validate_step_entry(step, 0)  # OK

step = {'id': 10, 'enabled': True}
_validate_step_entry(step, 1)  # Raises: ID must be between 1 and 6
```

---

### 1.4 `apply_steps_defaults(config: Dict[str, Any]) -> None`

**Module:** `src/orchestrator/config_loader.py`

**Purpose:** Apply default steps configuration if missing

**Parameters:**
- `config` (Dict[str, Any]): Experiment configuration (modified in-place)

**Returns:** `None`

**Side Effects:** Modifies `config` by adding `steps` key if missing

**Behavior:**
1. Check if 'steps' key exists
2. If missing, generate default configuration (all 6 steps enabled)
3. Log that defaults were applied

**Default Configuration:**
```python
[
    {'id': 1, 'enabled': True, 'name': 'Initial CRUD Implementation', 
     'prompt_file': 'config/prompts/step_1.txt'},
    {'id': 2, 'enabled': True, 'name': 'Add Enrollment Relationship',
     'prompt_file': 'config/prompts/step_2.txt'},
    {'id': 3, 'enabled': True, 'name': 'Teacher Assignment',
     'prompt_file': 'config/prompts/step_3.txt'},
    {'id': 4, 'enabled': True, 'name': 'Validation & Error Handling',
     'prompt_file': 'config/prompts/step_4.txt'},
    {'id': 5, 'enabled': True, 'name': 'Pagination & Filtering',
     'prompt_file': 'config/prompts/step_5.txt'},
    {'id': 6, 'enabled': True, 'name': 'User Interface',
     'prompt_file': 'config/prompts/step_6.txt'}
]
```

**Example:**
```python
from src.orchestrator.config_loader import apply_steps_defaults

config = {'frameworks': {'baes': {'enabled': True}}}
apply_steps_defaults(config)
# config now includes 'steps' with default configuration
```

---

## 2. Runner API

### 2.1 `_get_enabled_steps_info(self) -> List[EnabledStepInfo]`

**Module:** `src/orchestrator/runner.py` (private method)

**Purpose:** Prepare runtime information for enabled steps

**Parameters:** None (uses `self.config`)

**Returns:** `List[Dict]` - List of enabled step info with runtime metadata

**Behavior:**
1. Get enabled steps from config
2. For each enabled step:
   - Load prompt text from file
   - Create EnabledStepInfo with runtime data
3. Return list of step info objects

**EnabledStepInfo Structure:**
```python
{
    'step_id': int,          # Original step ID (1-6)
    'step_index': int,       # Sequential index (1-N)
    'step_name': str,        # Display name
    'prompt_text': str,      # Loaded prompt content
    'prompt_file': str,      # Path to prompt file
    'total_enabled': int     # Total enabled steps count
}
```

**Example:**
```python
# Inside Runner class
enabled_steps_info = self._get_enabled_steps_info()
# Returns: [
#   {'step_id': 1, 'step_index': 1, 'step_name': 'CRUD', ...},
#   {'step_id': 3, 'step_index': 2, 'step_name': 'Teacher', ...}
# ]
```

---

### 2.2 `execute_single_run(self) -> Dict[str, Any]`

**Module:** `src/orchestrator/runner.py`

**Purpose:** Execute single framework run with configurable steps (MODIFIED)

**Changes from Current:**
- Replace `for step_num in range(1, 7)` with dynamic enabled steps iteration
- Update progress display to show correct total and step info
- Preserve original step IDs in metrics

**Algorithm:**
```python
def execute_single_run(self) -> Dict[str, Any]:
    # ... setup code ...
    
    # Get enabled steps with runtime info
    enabled_steps_info = self._get_enabled_steps_info()
    
    # Execute enabled steps
    for step_info in enabled_steps_info:
        step_id = step_info['step_id']
        step_index = step_info['step_index']
        step_name = step_info['step_name']
        total_enabled = step_info['total_enabled']
        command_text = step_info['prompt_text']
        
        # Set logging context with original step ID
        log_context.set_step_context(step_id)
        
        # Display progress
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"        ⋯ Step {step_index}/{total_enabled} "
              f"(#{step_id}: {step_name}) | {timestamp}", flush=True)
        
        # Execute step with retry
        result = self._execute_step_with_retry(step_id, command_text)
        
        # Record metrics with ORIGINAL step_id
        self.metrics_collector.record_step(
            step_num=step_id,
            step_name=step_name,
            command=command_text,
            duration_seconds=result.get('duration_seconds', 0),
            # ... other metrics
        )
```

**Pre-conditions:**
- Config validated
- Steps configuration loaded
- Prompt files exist

**Post-conditions:**
- Only enabled steps executed
- Metrics recorded with original step IDs
- Progress display accurate

---

## 3. Generator API

### 3.1 `_generate_steps_config(self) -> List[Dict[str, Any]]`

**Module:** `generator/standalone_generator.py`

**Purpose:** Generate default steps configuration for new experiments

**Parameters:** None

**Returns:** `List[Dict]` - Default steps configuration

**Behavior:**
1. Create step configuration for each of 6 steps
2. Set all steps as enabled by default
3. Assign descriptive names
4. Set default prompt file paths

**Output:**
```python
[
    {
        'id': 1,
        'enabled': True,
        'name': 'Initial CRUD Implementation',
        'prompt_file': 'config/prompts/step_1.txt'
    },
    # ... steps 2-6
]
```

---

### 3.2 `_generate_config_yaml(self, config: Dict, output_dir: Path) -> None`

**Module:** `generator/standalone_generator.py` (MODIFIED)

**Purpose:** Generate config.yaml with steps section

**Changes from Current:**
- Add steps configuration to full_config
- Include steps documentation in header comments

**Header Addition:**
```yaml
# ============================================================
# Steps Configuration
# ============================================================
# Define which development steps to execute in the workflow.
# Each step can be individually enabled/disabled.
#
# Fields:
#   - id: Step number (1-6)
#   - enabled: Whether to execute this step (true/false)
#   - name: Descriptive name (optional)
#   - prompt_file: Path to prompt (optional, defaults to config/prompts/step_{id}.txt)
#
# Note: All frameworks execute the same steps for fair comparison.
# ============================================================
```

---

## 4. Metrics Collector API

### 4.1 `record_step(..., step_name: str = None, ...) -> None`

**Module:** `src/orchestrator/metrics_collector.py` (MODIFIED)

**Purpose:** Record step metrics with optional step name

**New Parameter:**
- `step_name` (str, optional): Descriptive name for the step

**Changes from Current:**
- Add `step_name` parameter to record_step method
- Include step_name in metrics output

**Example:**
```python
metrics_collector.record_step(
    step_num=4,  # Original step ID
    step_name="Validation & Error Handling",  # NEW
    command=command_text,
    duration_seconds=120.5,
    # ... other params
)
```

**Metrics Output:**
```json
{
  "step": 4,
  "step_name": "Validation & Error Handling",
  "duration": 120.5,
  ...
}
```

---

## 5. Type Definitions

### 5.1 Type Aliases (for clarity)

```python
# Add to src/orchestrator/config_loader.py or new types.py

from typing import TypedDict, List, Optional

class StepConfig(TypedDict):
    """Configuration for a single step"""
    id: int
    enabled: bool
    name: Optional[str]
    prompt_file: Optional[str]

class EnabledStepInfo(TypedDict):
    """Runtime information for an enabled step"""
    step_id: int
    step_index: int
    step_name: str
    prompt_text: str
    prompt_file: str
    total_enabled: int

StepsConfig = List[StepConfig]
```

---

## 6. Error Contracts

### 6.1 ConfigValidationError

**Module:** `src/orchestrator/config_loader.py`

**Purpose:** Raised when configuration validation fails

**Attributes:**
- `message` (str): Detailed error message with context
- `field` (str, optional): Field name that caused error
- `value` (Any, optional): Invalid value

**Examples:**

```python
# Invalid type
raise ConfigValidationError(
    "Invalid 'steps' configuration: must be a list.\n\n"
    "Expected format:\n"
    "steps:\n"
    "  - id: 1\n"
    "    enabled: true\n"
)

# No enabled steps
raise ConfigValidationError(
    "No steps enabled. At least one step must be enabled.\n"
    "Set 'enabled: true' for at least one step."
)

# Missing prompt file
raise ConfigValidationError(
    f"Prompt file not found: {prompt_path}\n"
    f"For step {step_id}, expected file at:\n"
    f"  {prompt_path.absolute()}\n"
    f"Create the file or update 'prompt_file' in config."
)
```

---

## 7. Integration Points

### 7.1 Config Loading Flow

```
main.py
  ↓ calls
load_config(config_path)
  ↓ calls
apply_steps_defaults(config)  # Add defaults if missing
  ↓ calls
validate_config(config)
  ↓ calls
validate_steps_config(config)  # Validate steps section
  ↓ returns
Validated config dict
```

### 7.2 Execution Flow

```
Runner.execute_single_run()
  ↓ calls
get_enabled_steps(config)
  ↓ returns
List of enabled steps
  ↓ for each
_execute_step_with_retry(step_id, prompt_text)
  ↓ after
metrics_collector.record_step(step_num=step_id, step_name=name)
```

---

## 8. Backwards Compatibility

### 8.1 Config without Steps Section

**Input:**
```yaml
frameworks:
  baes:
    enabled: true
# No 'steps' section
```

**Behavior:**
1. `apply_steps_defaults()` detects missing 'steps'
2. Adds default configuration (all 6 steps enabled)
3. Logs: "No steps configuration found, applying defaults"
4. Continues normal execution

**Result:** No breaking changes

---

### 8.2 Existing Generated Experiments

**Scenario:** User has existing experiment with old config format

**Solution:** On first run, config loader applies defaults automatically

**Migration:**
- **Automatic:** No user action required
- **Optional:** User can regenerate experiment to get new config format
- **Manual:** User can add steps section to existing config.yaml

---

## 9. Testing Contracts

### 9.1 Unit Test Requirements

**Test Module:** `tests/unit/test_steps_config.py`

**Test Cases:**

| Test | Input | Expected Output |
|------|-------|-----------------|
| `test_valid_steps_config` | Valid steps config | No error |
| `test_missing_steps_applies_defaults` | Config without steps | Defaults applied |
| `test_invalid_steps_type` | steps as dict | ConfigValidationError |
| `test_empty_steps_list` | steps: [] | ConfigValidationError |
| `test_no_enabled_steps` | All enabled: false | ConfigValidationError |
| `test_invalid_step_id` | id: 10 | ConfigValidationError |
| `test_duplicate_step_ids` | Two steps with id: 1 | ConfigValidationError |
| `test_missing_required_field` | Step without 'enabled' | ConfigValidationError |
| `test_invalid_field_type` | enabled: "yes" | ConfigValidationError |
| `test_missing_prompt_file` | prompt_file: "nonexistent.txt" | ConfigValidationError |
| `test_get_enabled_steps` | Mixed enabled/disabled | Only enabled returned |
| `test_enabled_steps_sorted` | Steps [3,1,2] | Returns [1,2,3] |
| `test_step_name_defaults` | Step without name | Uses default name |
| `test_prompt_file_defaults` | Step without prompt_file | Uses default path |

### 9.2 Integration Test Requirements

**Test Module:** `tests/integration/test_steps_execution.py`

**Test Cases:**

| Test | Scenario | Expected Behavior |
|------|----------|-------------------|
| `test_execute_all_steps` | All 6 steps enabled | Executes 1-6 in order |
| `test_execute_subset_steps` | Only steps 1,2,3 enabled | Executes only 1,2,3 |
| `test_skip_middle_step` | Steps 1,2,4,5,6 enabled | Skips step 3 |
| `test_progress_display` | 3 steps enabled | Shows "1/3", "2/3", "3/3" |
| `test_metrics_original_ids` | Steps 1,3,5 enabled | Metrics recorded as 1,3,5 |
| `test_custom_step_names` | Custom names provided | Names in logs/reports |
| `test_custom_prompt_files` | Custom prompt paths | Loads from custom paths |

---

## 10. API Summary

### Public APIs

| Function | Module | Purpose |
|----------|--------|---------|
| `validate_steps_config(config)` | config_loader | Validate steps section |
| `get_enabled_steps(config)` | config_loader | Get enabled steps list |
| `apply_steps_defaults(config)` | config_loader | Apply default config |

### Private APIs

| Function | Module | Purpose |
|----------|--------|---------|
| `_validate_step_entry(step, index)` | config_loader | Validate single step |
| `_get_enabled_steps_info()` | runner | Prepare runtime step info |
| `_generate_steps_config()` | generator | Generate default steps |

### Modified APIs

| Function | Module | Change |
|----------|--------|--------|
| `execute_single_run()` | runner | Use dynamic enabled steps |
| `record_step()` | metrics_collector | Add step_name parameter |
| `_generate_config_yaml()` | generator | Include steps section |

---

## 11. Configuration Schema

### Complete YAML Schema

```yaml
# config.yaml
steps:
  - id: 1                                    # Required: int (1-6)
    enabled: true                            # Required: bool
    name: "Initial CRUD Implementation"      # Optional: str
    prompt_file: "config/prompts/step_1.txt" # Optional: str
    
  - id: 2
    enabled: true
    name: "Add Enrollment Relationship"
    prompt_file: "config/prompts/step_2.txt"
    
  # ... steps 3-6
```

### Minimal Valid Config

```yaml
steps:
  - id: 1
    enabled: true
```

### Complete Valid Config

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
    enabled: false
    name: "Teacher Assignment"
    prompt_file: "config/prompts/step_3.txt"
    
  - id: 4
    enabled: true
    name: "Validation & Error Handling"
    prompt_file: "config/prompts/step_4.txt"
    
  - id: 5
    enabled: true
    name: "Pagination & Filtering"
    prompt_file: "config/prompts/step_5.txt"
    
  - id: 6
    enabled: false
    name: "User Interface"
    prompt_file: "config/prompts/step_6.txt"
```

---

## Contract Verification Checklist

- [ ] All public APIs documented
- [ ] All parameters specified
- [ ] All return types defined
- [ ] All exceptions documented
- [ ] Pre/post-conditions specified
- [ ] Example usage provided
- [ ] Error cases enumerated
- [ ] Type hints defined
- [ ] Integration points mapped
- [ ] Backwards compatibility verified
- [ ] Test contracts specified
