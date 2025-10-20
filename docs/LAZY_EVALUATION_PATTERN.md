# Lazy Evaluation Pattern for Token Metrics

## Overview

The experiment framework uses a **lazy evaluation pattern** for collecting token usage metrics from the OpenAI Usage API. This design centralizes all metrics collection in the reconciliation script, avoiding issues with API propagation delays during experiment execution.

## Architecture

### During Experiment Execution

When a step executes:

1. **Adapter calls OpenAI API** (e.g., `gpt-4o-mini` for code generation)
2. **Step completes** and duration is recorded
3. **Token metrics are set to 0** via `BaseAdapter.fetch_usage_from_openai()`:
   ```python
   tokens_in = 0
   tokens_out = 0
   api_calls = 0
   cached_tokens = 0
   ```
4. **Metrics saved to `metrics.json`** with `verification_status: 'pending'`

### After Experiment Completion

The reconciliation script (`runners/reconcile_usage.sh`) runs separately:

1. **Waits for API propagation** (5-15 minutes after run completes)
2. **Queries OpenAI Usage API** for the entire run time window
3. **Attributes tokens to individual steps** based on timestamps
4. **Updates `metrics.json`** with actual token counts
5. **Sets `verification_status: 'verified'`** upon success

## Why Lazy Evaluation?

### Problems with Immediate Collection

**Before (Immediate Collection):**
- Short steps (<1 min): Usage API returns empty data → silent failure → zeros recorded
- Long steps (>4 min): Usage API has data → success
- Inconsistent results across steps
- Silent failures masked as valid data

**Example from metrics.json:**
```json
{
  "step_number": 1,
  "duration_seconds": 15.05,
  "tokens_in": 0,        // ❌ API not propagated yet
  "tokens_out": 0,
  "api_calls": 0
},
{
  "step_number": 4,
  "duration_seconds": 249.69,
  "tokens_in": 46130,    // ✓ API had time to propagate
  "tokens_out": 18304,
  "api_calls": 52
}
```

### Benefits of Lazy Evaluation

✅ **Consistency**: All steps processed the same way  
✅ **Reliability**: Waits for API propagation before querying  
✅ **DRY Principle**: Single source of truth (reconciliation script)  
✅ **Simplicity**: Adapters don't need Usage API logic  
✅ **Transparency**: `verification_status` clearly indicates data state  

## Implementation Details

### Base Adapter (DRY)

All adapters inherit from `BaseAdapter`, which provides:

```python
def fetch_usage_from_openai(self, ...) -> Tuple[int, int, int, int]:
    """
    Lazy evaluation stub - always returns zeros.
    Actual data collected by reconciliation script.
    """
    logger.debug("Lazy evaluation: returning zero metrics")
    return 0, 0, 0, 0
```

**Adapters using this method:**
- `BAeSAdapter`
- `ChatDevAdapter`
- `GHSpecAdapter`

### Metrics Collector

```python
def record_step(self, step_num, ..., tokens_in=0, tokens_out=0, ...):
    """
    Records step with verification_status='pending'.
    Accepts zeros without validation errors.
    """
    self.steps_data[step_num] = {
        ...
        'tokens_in': tokens_in,  # Will be 0 initially
        'tokens_out': tokens_out,
        'verification_status': 'pending'
    }
```

### Orchestrator Runner

```python
# Skip Usage API verification during execution
metrics['verification_status'] = 'pending'
metrics['usage_api_verification'] = {
    'verified': False,
    'error': 'Lazy evaluation - use reconciliation script'
}
```

## Usage Guide

### Running Experiments

```bash
# Run experiment as normal
./runners/run_experiment.sh baes

# Metrics will be saved with zeros and verification_status='pending'
```

### Reconciling Metrics

```bash
# Wait 5-15 minutes after run completes, then reconcile
./runners/reconcile_usage.sh

# Or reconcile specific framework/run
./runners/reconcile_usage.sh chatdev
./runners/reconcile_usage.sh chatdev abc-123-def
```

### Re-running Reconciliation

If you need to re-collect token data:

```bash
# Reset verification status to 'pending'
python scripts/reset_metrics_for_reconciliation.py

# Re-run reconciliation
./runners/reconcile_usage.sh
```

## Verification Status States

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `pending` | Metrics need reconciliation | Run `reconcile_usage.sh` |
| `verified` | Metrics verified by reconciliation | None - data is complete |
| `failed` | Reconciliation encountered errors | Check logs, retry reconciliation |

## File Structure

```
runs/
├── baes/
│   └── {run-id}/
│       └── metrics.json          # verification_status: 'pending'
└── chatdev/
    └── {run-id}/
        └── metrics.json

# After reconciliation:
runs/
├── baes/
│   └── {run-id}/
│       └── metrics.json          # verification_status: 'verified'
│                                 # tokens_in/out: actual values
```

## Metrics JSON Structure

### Before Reconciliation (Fresh Run)

```json
{
  "run_id": "abc-123",
  "verification_status": "pending",
  "steps": [
    {
      "step_number": 1,
      "tokens_in": 0,
      "tokens_out": 0,
      "api_calls": 0,
      "cached_tokens": 0,
      "verification_status": "pending",
      "start_timestamp": 1760883669,
      "end_timestamp": 1760883684
    }
  ],
  "aggregate_metrics": {
    "TOK_IN": 0,
    "TOK_OUT": 0,
    "API_CALLS": 0,
    "COST_USD": 0.0
  },
  "usage_api_verification": {
    "verified": false,
    "error": "Lazy evaluation - use reconciliation script"
  }
}
```

### After Reconciliation

```json
{
  "run_id": "abc-123",
  "verification_status": "verified",
  "steps": [
    {
      "step_number": 1,
      "tokens_in": 12453,
      "tokens_out": 5234,
      "api_calls": 15,
      "cached_tokens": 1200,
      "verification_status": "verified",
      "start_timestamp": 1760883669,
      "end_timestamp": 1760883684
    }
  ],
  "aggregate_metrics": {
    "TOK_IN": 76164,
    "TOK_OUT": 30903,
    "API_CALLS": 86,
    "COST_USD": 0.0234
  },
  "usage_api_reconciliation": {
    "verification_status": "verified",
    "attempts": [...]
  }
}
```

## Design Principles

1. **Separation of Concerns**: Execution ≠ Metrics Collection
2. **DRY**: Single method in base class used by all adapters
3. **Fail-Safe**: Better to have zeros + pending status than incorrect data
4. **Observable**: Clear status indicators at step and run levels
5. **Recoverable**: Can always re-run reconciliation

## Migration Notes

When migrating existing runs to lazy evaluation:

1. Run `scripts/reset_metrics_for_reconciliation.py` to set status to 'pending'
2. Run `runners/reconcile_usage.sh` to collect actual data
3. Verify `verification_status` changed to 'verified'

## Related Documentation

- [Reconciliation Quick Reference](reconcile_usage_quick_reference.md)
- [Usage Reconciliation Guide](usage_reconciliation_guide.md)
- [Metrics Documentation](metrics.md)
