# Data Model: Configurable Steps

## Version: 1.0.0
## Date: 2025-10-21

---

## Entities

### 1. StepConfig

**Description:** Configuration for a single development step

**Fields:**

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `id` | `int` | ✅ Yes | N/A | 1-6 | Step identifier (corresponds to prompt file number) |
| `enabled` | `bool` | ✅ Yes | N/A | true/false | Whether this step should be executed |
| `name` | `str` | ❌ No | `"Step {id}"` | 1-200 chars | Descriptive name for logs and reports |
| `prompt_file` | `str` | ❌ No | `"config/prompts/step_{id}.txt"` | Valid file path | Path to the prompt file for this step |

**Validation Rules:**
1. `id` must be unique within steps list
2. `id` must be in range [1, 6]
3. `enabled` must be boolean type
4. `name` if provided must be non-empty string
5. `prompt_file` must point to existing file
6. At least one step in collection must have `enabled: true`

**Example:**
```yaml
id: 1
enabled: true
name: "Initial CRUD Implementation"
prompt_file: "config/prompts/step_1.txt"
```

**State Transitions:**
```
CONFIGURED -> VALIDATED -> EXECUTING -> COMPLETED
                        -> SKIPPED (if enabled: false)
```

---

### 2. StepsCollection

**Description:** Collection of all step configurations for an experiment

**Fields:**

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `steps` | `List[StepConfig]` | ✅ Yes | Default 6 steps | 1-6 items | Ordered list of step configurations |

**Validation Rules:**
1. Must be a list
2. Must contain at least 1 item
3. Must contain at most 6 items
4. All step IDs must be unique
5. At least one step must be enabled
6. Steps should be defined in ascending ID order (warning if not)

**Derived Properties:**
- `enabled_steps`: List of steps where `enabled: true`
- `enabled_count`: Count of enabled steps
- `disabled_steps`: List of steps where `enabled: false`
- `step_ids`: List of all step IDs
- `enabled_step_ids`: List of enabled step IDs

**Default Configuration:**
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
    enabled: true
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
    enabled: true
    name: "User Interface"
    prompt_file: "config/prompts/step_6.txt"
```

---

### 3. EnabledStepInfo

**Description:** Runtime information about an enabled step during execution

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step_id` | `int` | ✅ | Original step ID (1-6) |
| `step_index` | `int` | ✅ | Sequential execution index (1-N where N=enabled count) |
| `step_name` | `str` | ✅ | Display name for this step |
| `prompt_text` | `str` | ✅ | Loaded prompt content |
| `prompt_file` | `str` | ✅ | Path to prompt file |
| `total_enabled` | `int` | ✅ | Total count of enabled steps |

**Usage Context:** Created at runtime in Runner for each enabled step

**Example:**
```python
EnabledStepInfo(
    step_id=4,           # Original step ID
    step_index=3,        # 3rd step to execute
    step_name="Validation & Error Handling",
    prompt_text="Implement comprehensive data validation...",
    prompt_file="config/prompts/step_4.txt",
    total_enabled=5      # 5 steps enabled total
)
```

**Display Format:**
```
⋯ Step 3/5 (#4: Validation & Error Handling) | 10:42:33
       ↑  ↑  ↑                               ↑
       │  │  │                               └─ Timestamp
       │  │  └─ Step Name
       │  └─ Original Step ID
       └─ Sequential Index / Total Enabled
```

---

## Relationships

### StepsCollection → StepConfig
- **Type:** One-to-Many
- **Cardinality:** 1 collection contains 1-6 step configs
- **Constraint:** Each StepConfig.id must be unique
- **Navigation:** `steps_collection.steps -> List[StepConfig]`

### ExperimentConfig → StepsCollection
- **Type:** One-to-One
- **Cardinality:** 1 experiment config has exactly 1 steps collection
- **Constraint:** Steps collection must be valid
- **Navigation:** `experiment_config['steps'] -> StepsCollection`

### Runner → EnabledStepInfo
- **Type:** One-to-Many (Temporal)
- **Cardinality:** 1 runner creates N enabled step infos during execution
- **Lifecycle:** Created at execution start, used during iteration
- **Navigation:** `runner.get_enabled_steps() -> List[EnabledStepInfo]`

---

## Data Flow

### 1. Configuration Loading
```
config.yaml
    ↓ (PyYAML load)
Dict[str, Any]
    ↓ (validate_steps_config)
StepsCollection (validated)
    ↓ (store in config)
config['steps']: List[Dict]
```

### 2. Execution Preparation
```
config['steps']: List[Dict]
    ↓ (filter enabled=true)
enabled_steps: List[Dict]
    ↓ (sort by id)
sorted_enabled: List[Dict]
    ↓ (create runtime info)
List[EnabledStepInfo]
```

### 3. Step Execution
```
for step_index, step_info in enumerate(enabled_steps_info, 1):
    ↓
Execute step_info.step_id
    ↓
Record metrics with step_info.step_id (original)
    ↓
Log with step_info.step_name
```

---

## Validation State Machine

```
┌─────────────┐
│   INITIAL   │
└──────┬──────┘
       │
       ↓ load config
┌─────────────┐
│ VALIDATING  │
└──────┬──────┘
       │
       ├─→ Missing 'steps' key ─→ Apply Defaults ─→ [VALID]
       │
       ├─→ Invalid type ─────────→ [ERROR: InvalidType]
       │
       ├─→ Empty list ───────────→ [ERROR: EmptySteps]
       │
       ├─→ Invalid step entry ───→ [ERROR: InvalidStepEntry]
       │
       ├─→ Duplicate IDs ────────→ [ERROR: DuplicateIds]
       │
       ├─→ No enabled steps ─────→ [ERROR: NoEnabledSteps]
       │
       ├─→ Missing prompt file ──→ [ERROR: MissingPromptFile]
       │
       └─→ All checks passed ────→ [VALID]
```

---

## Schema Definition

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StepsConfiguration",
  "type": "object",
  "properties": {
    "steps": {
      "type": "array",
      "minItems": 1,
      "maxItems": 6,
      "items": {
        "type": "object",
        "required": ["id", "enabled"],
        "properties": {
          "id": {
            "type": "integer",
            "minimum": 1,
            "maximum": 6,
            "description": "Step identifier (1-6)"
          },
          "enabled": {
            "type": "boolean",
            "description": "Whether to execute this step"
          },
          "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Descriptive name for logs and reports"
          },
          "prompt_file": {
            "type": "string",
            "pattern": "^.*\\.txt$",
            "description": "Path to prompt file"
          }
        },
        "additionalProperties": false
      }
    }
  },
  "required": ["steps"]
}
```

### Python TypedDict (for type hints)

```python
from typing import TypedDict, List, Optional

class StepConfig(TypedDict):
    id: int
    enabled: bool
    name: Optional[str]
    prompt_file: Optional[str]

class StepsCollection(TypedDict):
    steps: List[StepConfig]

class EnabledStepInfo(TypedDict):
    step_id: int
    step_index: int
    step_name: str
    prompt_text: str
    prompt_file: str
    total_enabled: int
```

---

## Constraints Summary

### Integrity Constraints
1. **Uniqueness:** All step IDs must be unique
2. **Range:** Step IDs must be 1-6 (inclusive)
3. **Minimum Enabled:** At least one step must be enabled
4. **File Existence:** Prompt files must exist
5. **Type Safety:** All fields must match declared types

### Business Rules
1. **Fair Comparison:** All frameworks execute same steps (no per-framework override)
2. **Sequential Order:** Enabled steps executed in ID order (sorted)
3. **Original ID Preservation:** Metrics recorded with original step ID
4. **Backwards Compatibility:** Missing steps config defaults to all enabled

### Referential Integrity
1. **Prompt File Reference:** `prompt_file` must reference existing file in filesystem
2. **Config Reference:** Steps config must be part of valid experiment config

---

## Migration Strategy

### Existing Configs (No Steps Section)
```yaml
# OLD CONFIG
frameworks:
  baes:
    enabled: true
# No steps section
```

**Auto-Migration:**
```python
def migrate_config(config: Dict) -> Dict:
    if 'steps' not in config:
        logger.info("No steps configuration found, applying defaults")
        config['steps'] = generate_default_steps_config()
    return config
```

### New Configs (With Steps Section)
```yaml
# NEW CONFIG
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD"
    # ... more steps

frameworks:
  baes:
    enabled: true
```

**No Migration Needed** - validated as-is

---

## Performance Considerations

### Memory
- **StepConfig:** ~200 bytes each
- **StepsCollection:** ~1.2 KB total (6 steps)
- **EnabledStepInfo:** ~500 bytes each (runtime)
- **Total Impact:** Negligible (<5 KB)

### Validation Time
- **Simple checks:** <1ms per step
- **File existence checks:** ~5ms per step (I/O)
- **Total validation:** <50ms for 6 steps
- **Impact:** Negligible (happens once at startup)

### Execution Impact
- **No additional overhead** during step execution
- **Same execution flow** as current implementation
- **Filtering overhead:** O(N) where N=6, ~microseconds

---

## Extension Points

### Future Enhancements (Out of Scope for V1)

1. **Per-Step Timeouts**
```yaml
- id: 1
  enabled: true
  timeout: 1800  # 30 minutes for this step
```

2. **Step Dependencies**
```yaml
- id: 4
  enabled: true
  depends_on: [1, 2, 3]  # Requires 1,2,3 to be enabled
```

3. **Conditional Execution**
```yaml
- id: 5
  enabled: true
  condition: "step_3.success"  # Only if step 3 succeeded
```

4. **Custom Step Ranges**
```yaml
- id: 7  # Beyond default 1-6
  enabled: true
  name: "Custom Step"
  prompt_file: "config/prompts/custom_step.txt"
```

5. **Step Parameters**
```yaml
- id: 1
  enabled: true
  parameters:
    temperature: 0.7
    max_tokens: 4000
```

---

## Summary

### Core Data Structure
```python
config = {
    'steps': [
        {'id': 1, 'enabled': True, 'name': '...', 'prompt_file': '...'},
        {'id': 2, 'enabled': True, 'name': '...', 'prompt_file': '...'},
        # ... more steps
    ]
}
```

### Key Properties
- ✅ Simple and explicit
- ✅ Self-documenting
- ✅ Extensible
- ✅ Type-safe
- ✅ Backwards compatible
- ✅ Easy to validate

### Validation Checklist
- [ ] Type: `steps` is a list
- [ ] Count: 1-6 items
- [ ] Required fields: `id`, `enabled`
- [ ] ID range: 1-6
- [ ] ID uniqueness: No duplicates
- [ ] Enabled count: At least one enabled
- [ ] Files: All prompt files exist
- [ ] Order: Warning if not ascending (optional)
