# API Contract: MetricsCollector

**Component**: `src/orchestrator/metrics_collector.py`  
**Type**: Internal Python API  
**Consumer**: Framework adapters, orchestrator

---

## Class: MetricsCollector

### Method: record_step

**Purpose**: Record metrics for a completed step/sprint

**Signature**:
```python
def record_step(
    self,
    step_num: int,
    duration_seconds: float,
    start_timestamp: int,
    end_timestamp: int,
    hitl_count: int = 0,
    retry_count: int = 0,
    success: bool = True
) -> None:
    """
    Record step-level metrics (timing and interactions only, NO tokens).
    
    Args:
        step_num: Step number (1-indexed)
        duration_seconds: Step execution time in seconds
        start_timestamp: Unix timestamp when step started
        end_timestamp: Unix timestamp when step ended
        hitl_count: Number of human interventions
        retry_count: Number of retry attempts
        success: Whether step completed successfully
        
    Raises:
        ValueError: If step_num <= 0, duration < 0, or end < start
        TypeError: If parameters have wrong types
    """
```

**Behavior**:
1. Validate inputs (fail-fast on invalid data)
2. Create step record with timing and interaction metrics
3. Store in `self.steps_data` dictionary
4. Do NOT accept or store token counts

**Contract**:
- MUST accept only timing and interaction metrics (duration, timestamps, HITL, retries)
- MUST NOT accept `tokens_in`, `tokens_out`, `api_calls`, `cached_tokens` parameters
- MUST fail immediately on invalid inputs (negative duration, etc.)
- MUST store step number, timestamps, and success status

**Breaking Change**: Removed parameters:
- `tokens_in` (no longer accepted)
- `tokens_out` (no longer accepted)
- `api_calls` (no longer accepted)
- `cached_tokens` (no longer accepted)

---

### Method: get_aggregate_metrics

**Purpose**: Compute aggregate metrics for the run

**Signature**:
```python
def get_aggregate_metrics(self) -> Dict[str, Any]:
    """
    Compute aggregate metrics from step data.
    
    Returns:
        dict: Metrics dictionary with run-level aggregates
        
    Structure:
        {
            'steps': [  # Timing and interaction data only
                {
                    'step': int,
                    'duration_seconds': float,
                    'start_timestamp': int,
                    'end_timestamp': int,
                    'hitl_count': int,
                    'retry_count': int,
                    'success': bool
                }
            ],
            'aggregate_metrics': {
                'TOK_IN': 0,      # Placeholder (reconciled post-run)
                'TOK_OUT': 0,     # Placeholder (reconciled post-run)
                'API_CALLS': 0,   # Placeholder (reconciled post-run)
                'CACHED_TOKENS': 0,  # Placeholder (reconciled post-run)
                'COST_USD': 0.0,  # Placeholder (reconciled post-run)
                'DUR': float,     # Sum of step durations
                'UTT': int,       # Number of steps
                'HIT': int        # Sum of hitl_count
            }
        }
    """
```

**Behavior**:
1. Aggregate timing metrics from `self.steps_data`
2. Set token/cost metrics to zero (placeholders for reconciliation)
3. Return structured dictionary

**Contract**:
- `steps[]` array MUST NOT contain token fields
- `aggregate_metrics` token fields initialized to zero (reconciled later)
- `DUR`, `UTT`, `HIT` computed from step data (accurate immediately)
- Return value matches metrics.json schema v2.0

---

### Method: save_metrics

**Purpose**: Save metrics to JSON file

**Signature**:
```python
def save_metrics(
    self,
    output_path: Path,
    run_id: str,
    framework: str,
    start_timestamp: int,
    end_timestamp: int
) -> None:
    """
    Save metrics to JSON file.
    
    Args:
        output_path: Path to metrics.json
        run_id: Unique run identifier
        framework: Framework name (baes, chatdev, ghspec)
        start_timestamp: Run start time (Unix seconds)
        end_timestamp: Run end time (Unix seconds)
        
    Raises:
        OSError: If file write fails
        ValueError: If metrics contain invalid data
    """
```

**Behavior**:
1. Get aggregate metrics via `get_aggregate_metrics()`
2. Add run metadata (run_id, framework, timestamps)
3. Add reconciliation section (initialized to "pending")
4. Validate schema (fail if steps contain token fields)
5. Write to JSON file

**Contract**:
- MUST validate that `steps[]` contains no token fields before writing
- MUST initialize `usage_api_reconciliation.verification_status = "pending"`
- MUST fail immediately if validation fails (no partial writes)

---

## Schema Validation Contract

**Enforced Constraints**:

```python
# Steps array validation
for step in metrics['steps']:
    forbidden_fields = {'tokens_in', 'tokens_out', 'api_calls', 'cached_tokens'}
    if any(field in step for field in forbidden_fields):
        raise ValueError(
            f"Step {step['step']} contains forbidden fields: "
            f"{forbidden_fields & step.keys()}"
        )
```

**Required Fields in steps[]**:
- `step`: integer >= 1
- `duration_seconds`: float >= 0
- `start_timestamp`: integer > 0
- `end_timestamp`: integer > start_timestamp
- `hitl_count`: integer >= 0
- `retry_count`: integer >= 0
- `success`: boolean

**Forbidden Fields in steps[]**:
- `tokens_in`
- `tokens_out`
- `api_calls`
- `cached_tokens`

---

## Example Usage

```python
from src.orchestrator.metrics_collector import MetricsCollector
from pathlib import Path

collector = MetricsCollector()

# Record steps (NO token parameters)
collector.record_step(
    step_num=1,
    duration_seconds=35.2,
    start_timestamp=1761523200,
    end_timestamp=1761523235,
    hitl_count=0,
    retry_count=0,
    success=True
)

collector.record_step(
    step_num=2,
    duration_seconds=38.1,
    start_timestamp=1761523235,
    end_timestamp=1761523273,
    hitl_count=1,
    retry_count=0,
    success=True
)

# Save metrics (tokens will be reconciled post-run)
collector.save_metrics(
    output_path=Path("runs/baes/run-abc-123/metrics.json"),
    run_id="run-abc-123",
    framework="baes",
    start_timestamp=1761523200,
    end_timestamp=1761523530
)
```

**Generated metrics.json**:
```json
{
  "run_id": "run-abc-123",
  "framework": "baes",
  "start_timestamp": 1761523200,
  "end_timestamp": 1761523530,
  "aggregate_metrics": {
    "TOK_IN": 0,
    "TOK_OUT": 0,
    "API_CALLS": 0,
    "CACHED_TOKENS": 0,
    "COST_USD": 0.0,
    "DUR": 73.3,
    "UTT": 2,
    "HIT": 1
  },
  "steps": [
    {
      "step": 1,
      "duration_seconds": 35.2,
      "start_timestamp": 1761523200,
      "end_timestamp": 1761523235,
      "hitl_count": 0,
      "retry_count": 0,
      "success": true
    },
    {
      "step": 2,
      "duration_seconds": 38.1,
      "start_timestamp": 1761523235,
      "end_timestamp": 1761523273,
      "hitl_count": 1,
      "retry_count": 0,
      "success": true
    }
  ],
  "usage_api_reconciliation": {
    "verification_status": "pending",
    "attempts": [],
    "last_attempt_timestamp": null,
    "verified_at": null
  }
}
```

---

## Breaking Changes from Previous Version

1. **REMOVED**: `tokens_in`, `tokens_out`, `api_calls`, `cached_tokens` parameters from `record_step()`
2. **CHANGED**: `get_aggregate_metrics()` returns steps without token fields
3. **ADDED**: Schema validation in `save_metrics()` to enforce clean data model
4. **CHANGED**: Aggregate token metrics initialized to zero (not summed from steps)

---

## Migration Guide

**Old Code** (Buggy):
```python
collector.record_step(
    step_num=1,
    duration_seconds=35.2,
    tokens_in=9874,      # ❌ No longer accepted
    tokens_out=8234,     # ❌ No longer accepted
    api_calls=5,         # ❌ No longer accepted
    cached_tokens=1280   # ❌ No longer accepted
)
```

**New Code** (Fixed):
```python
collector.record_step(
    step_num=1,
    duration_seconds=35.2,
    start_timestamp=1761523200,
    end_timestamp=1761523235,
    hitl_count=0,
    retry_count=0,
    success=True
    # ✅ No token parameters
)

# Tokens reconciled post-run via UsageReconciler
```

---

## Version

**Contract Version**: 2.0.0  
**Breaking**: Yes (parameter removal, schema change)  
**Compatible With**: metrics.json schema v2.0 (post-fix)
