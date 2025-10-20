# Verification Rules for Token Metrics

## Overview

This document explains the strict verification rules that determine when experiment run metrics can be marked as "verified" and considered reliable for analysis.

## Verification Status Lifecycle

```
pending → warning (if incomplete) → verified
                ↓
        data_not_available (if API fails)
```

## Core Verification Rule

**A run can ONLY be marked as `verified` when ALL of the following conditions are met:**

### 1. Data Stability (Double-Check)
- At least 2 reconciliation attempts have been made
- The last 2 attempts show **identical** token counts (no changes)
- At least **60 minutes** between the last 2 attempts
- This ensures OpenAI Usage API data has fully stabilized

### 2. Data Completeness (Critical!)
- **`steps_with_tokens` MUST equal `total_steps`**
- Every step that executed successfully MUST have token data
- If `steps_with_tokens < total_steps`, status is set to `warning`

### 3. No Anomalies
- Token counts must never decrease between attempts
- If tokens decrease, status is set to `warning` with anomaly alert

## Status Definitions

### `verified` ✅
- All verification rules passed
- Data is stable and complete
- Safe to use for analysis and reports
- **Example**: 6/6 steps have tokens, stable for 60+ minutes

### `pending` ⏳
- Waiting for more time or data to arrive
- Normal status during reconciliation process
- **Examples**:
  - First reconciliation attempt
  - Data still changing (tokens increasing)
  - Time gap < 60 minutes between attempts

### `warning` ⚠️
- Data is stable BUT incomplete or anomalous
- **Should NOT be used for final analysis**
- **Examples**:
  - Only 3/6 steps have tokens (some steps failed/skipped)
  - Token counts decreased (API anomaly)

### `data_not_available` 🕐
- OpenAI Usage API returned zero tokens
- Run may be too recent (< 5-15 min old)
- Or API may be experiencing issues
- Will retry on next reconciliation

## Why Step Completeness Matters

### Scenario 1: Partial Step Success (Warning Status)
```json
{
  "total_steps": 6,
  "steps_with_tokens": 3,
  "steps": [
    {"step": 1, "tokens_in": 8389, "tokens_out": 2837},  // ✓ Has tokens
    {"step": 2, "tokens_in": 9819, "tokens_out": 3098},  // ✓ Has tokens
    {"step": 3, "tokens_in": 0, "tokens_out": 0},        // ✗ No tokens
    {"step": 4, "tokens_in": 3711, "tokens_out": 524},   // ✓ Has tokens
    {"step": 5, "tokens_in": 0, "tokens_out": 0},        // ✗ No tokens
    {"step": 6, "tokens_in": 0, "tokens_out": 0}         // ✗ No tokens
  ]
}
```

**Status**: `warning`  
**Reason**: Steps 3, 5, 6 have zero tokens - they either:
- Failed during execution
- Were skipped
- Didn't actually call the OpenAI API

**Impact**: Run can still be analyzed, but metrics are incomplete. Framework comparison may be unfair if other frameworks succeeded on all steps.

### Scenario 2: Complete Step Success (Can be Verified)
```json
{
  "total_steps": 6,
  "steps_with_tokens": 6,
  "steps": [
    {"step": 1, "tokens_in": 8389, "tokens_out": 2837},  // ✓
    {"step": 2, "tokens_in": 9819, "tokens_out": 3098},  // ✓
    {"step": 3, "tokens_in": 7245, "tokens_out": 2156},  // ✓
    {"step": 4, "tokens_in": 3711, "tokens_out": 524},   // ✓
    {"step": 5, "tokens_in": 5823, "tokens_out": 1890},  // ✓
    {"step": 6, "tokens_in": 4127, "tokens_out": 1456}   // ✓
  ]
}
```

**Status**: `verified` (after 60+ min double-check)  
**Reason**: All steps have tokens - complete data  
**Impact**: Safe to use for analysis and comparisons

## Implementation

The verification logic is implemented in:
- **File**: `src/orchestrator/usage_reconciler.py`
- **Method**: `_check_verification_status()`
- **Code location**: Lines ~390-490

### Key Code Snippet
```python
# Check if all steps that should have tokens actually have them
steps_with_tokens = current_attempt.get('steps_with_tokens', 0)
total_steps = current_attempt.get('total_steps', 0)
all_steps_have_tokens = (steps_with_tokens == total_steps)

if data_identical:
    if time_diff_minutes >= DEFAULT_VERIFICATION_INTERVAL_MIN:
        # Check completeness before marking as verified
        if not all_steps_have_tokens:
            return {
                'status': 'warning',
                'message': f'⚠️ Data stable but incomplete: only {steps_with_tokens}/{total_steps} steps have tokens'
            }
        # ✅ VERIFIED - all conditions met!
        return {
            'status': 'verified',
            'message': f'✅ Data stable across {time_diff_minutes:.0f} minute interval'
        }
```

## Monitoring Verification Status

### Check All Runs
```bash
./runners/reconcile_usage.sh --list --verbose
```

### Check Specific Run
```bash
./runners/reconcile_usage.sh <framework> <run-id>
```

### Status in metrics.json
```json
{
  "usage_api_reconciliation": {
    "verification_status": "warning",  // ← Check this field
    "verification_message": "⚠️ Data stable but incomplete: only 3/6 steps have tokens",
    "attempts": [...]
  }
}
```

### Status in runs_manifest.json
```json
{
  "runs": [
    {
      "run_id": "...",
      "verification_status": "warning",  // ← Also here
      "total_tokens_in": 21919,
      "total_tokens_out": 6459
    }
  ]
}
```

## Analysis Impact

### Report Generation
- Reports should **filter out** runs with `status != 'verified'`
- Or clearly mark incomplete runs in visualizations
- Example filter in analysis scripts:
  ```python
  verified_runs = [r for r in runs if r['verification_status'] == 'verified']
  ```

### Framework Comparison
- Only compare runs where ALL frameworks have `verified` status
- Comparing verified vs warning runs is unfair (different completeness levels)

### Statistical Analysis
- Use only `verified` runs for statistical tests
- Document any runs excluded due to incompleteness

## Troubleshooting

### Run Stuck in `pending`
- **Cause**: Token counts still changing OR time gap < 60 min
- **Solution**: Wait for Usage API to stabilize, then run reconciliation again

### Run Stuck in `warning` (Incomplete Steps)
- **Cause**: Some steps truly failed or didn't call API
- **Solution**: This is the correct status - run had partial failures
- **Action**: Investigate why those steps failed (check logs in run directory)

### Run Stuck in `data_not_available`
- **Cause**: OpenAI Usage API not returning data
- **Solution**: 
  1. Wait 15+ minutes after run end
  2. Check API key has `api.usage.read` scope
  3. Verify run end time is recent (< 24 hours)

## Related Documentation

- **Lazy Evaluation Pattern**: `docs/LAZY_EVALUATION_PATTERN.md`
- **Reconciliation Guide**: `docs/usage_reconciliation_guide.md`
- **Double-Check System**: `docs/double_check_verification.md`
- **Configuration**: `docs/configuration_reference.md`

## Summary

**The Golden Rule**: `verified` status requires **both** data stability (60+ min double-check) **and** data completeness (all steps have tokens). This ensures only high-quality, complete data is used for analysis and framework comparisons.
