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

**A run can be marked as `verified` when ALL of the following conditions are met:**

### 1. Data Stability (N-Check Verification)
- At least **N consecutive stable verifications** (configurable via `RECONCILIATION_MIN_STABLE_VERIFICATIONS`, default: 2)
- Each verification shows **identical** token counts to the previous attempt
- At least **60 minutes** between each verification attempt (configurable via `RECONCILIATION_VERIFICATION_INTERVAL_MIN`)
- This ensures OpenAI Usage API data has fully stabilized

**Configuration**:
- `RECONCILIATION_MIN_STABLE_VERIFICATIONS=1`: Development/Testing (fast feedback)
- `RECONCILIATION_MIN_STABLE_VERIFICATIONS=2`: Production (default, double-check)
- `RECONCILIATION_MIN_STABLE_VERIFICATIONS=3`: Research (high confidence)
- `RECONCILIATION_MIN_STABLE_VERIFICATIONS=4`: Publication (maximum certainty)

### 2. No Anomalies
- Token counts must never decrease between attempts
- If tokens decrease, status is set to `warning` with anomaly alert

### 3. Token Coverage (Framework Efficiency)
**Note:** The system NO LONGER requires all steps to have tokens. Some frameworks (like BAeS) intelligently avoid unnecessary LLM calls by using templates or rules for certain operations. This is treated as **efficiency**, not incomplete data.

- Runs are verified regardless of token coverage percentage
- Verification message shows coverage rate (e.g., "3/6 steps used LLM, 50% coverage")
- Zero-token steps are acceptable when data has stabilized across N checks
- This allows fair comparison of frameworks with different efficiency strategies

## Status Definitions

### `verified` ✅
- All verification rules passed
- Data is stable across N consecutive checks
- Safe to use for analysis and reports
- **Examples**: 
  - "Verified after 2 stable checks: all 6 steps used LLM" (100% coverage)
  - "Verified after 2 stable checks: 3/6 steps used LLM, 50% coverage" (partial coverage, acceptable)

### `pending` ⏳
- Waiting for more time, data, or verification checks
- Normal status during reconciliation process
- **Examples**:
  - First reconciliation attempt
  - Data still changing (tokens increasing)
  - Time gap < 60 minutes between attempts
  - Only 1/2 stable checks completed (need more verifications)

### `warning` ⚠️
- Token count anomaly detected
- **Should be investigated before using for analysis**
- **Examples**:
  - Token counts decreased (API anomaly or data loss)

### `data_not_available` 🕐
- OpenAI Usage API returned zero tokens
- Run may be too recent (< 5-15 min old)
- Or API may be experiencing issues
- Will retry on next reconciliation

## Understanding Token Coverage

### Scenario 1: Full LLM Usage (100% Coverage)
```json
{
  "total_steps": 6,
  "steps_with_tokens": 6,
  "steps": [
    {"step": 1, "tokens_in": 8389, "tokens_out": 2837},  // ✓ Used LLM
    {"step": 2, "tokens_in": 9819, "tokens_out": 3098},  // ✓ Used LLM
    {"step": 3, "tokens_in": 7245, "tokens_out": 2156},  // ✓ Used LLM
    {"step": 4, "tokens_in": 3711, "tokens_out": 524},   // ✓ Used LLM
    {"step": 5, "tokens_in": 5823, "tokens_out": 1890},  // ✓ Used LLM
    {"step": 6, "tokens_in": 4127, "tokens_out": 1456}   // ✓ Used LLM
  ]
}
```

**Status**: `verified` (after N stable checks)  
**Message**: "Verified after 2 stable checks: all 6 steps used LLM"  
**Framework Strategy**: Traditional approach - calls LLM for every operation  
**Impact**: Higher token usage, but consistent behavior across all steps

### Scenario 2: Partial LLM Usage (50% Coverage - Efficiency Strategy)
```json
{
  "total_steps": 6,
  "steps_with_tokens": 3,
  "steps": [
    {"step": 1, "tokens_in": 8389, "tokens_out": 2837},  // ✓ Used LLM (new entities)
    {"step": 2, "tokens_in": 9819, "tokens_out": 3098},  // ✓ Used LLM (relationships)
    {"step": 3, "tokens_in": 0, "tokens_out": 0},        // ✓ Used template (field addition)
    {"step": 4, "tokens_in": 0, "tokens_out": 0},        // ✓ Used rules (validation)
    {"step": 5, "tokens_in": 5823, "tokens_out": 1890},  // ✓ Used LLM (complex feature)
    {"step": 6, "tokens_in": 0, "tokens_out": 0}         // ✓ Used template (UI generation)
  ]
}
```

**Status**: `verified` (after N stable checks)  
**Message**: "Verified after 2 stable checks: 3/6 steps used LLM, 50% coverage"  
**Framework Strategy**: Intelligent optimization - uses templates/rules when possible  
**Impact**: Lower token usage = lower cost = higher efficiency. Common in BAeS framework.  
**Note**: This is NOT incomplete data - the framework chose not to call LLM for certain operations

## Implementation

The verification logic is implemented in:
- **File**: `src/orchestrator/usage_reconciler.py`
- **Method**: `_check_verification_status()`
- **Code location**: Lines ~390-490

### Key Code Snippet
```python
# Count consecutive stable verifications
stable_count = self._count_stable_verifications(attempts, current_attempt)

# Check if we have enough stable verifications
if stable_count >= DEFAULT_MIN_STABLE_VERIFICATIONS:
    # Calculate token coverage rate
    coverage_rate = steps_with_tokens / total_steps if total_steps > 0 else 0
    
    # ✅ VERIFIED - data is stable after N checks
    if coverage_rate == 1.0:
        # Perfect: all steps used LLM
        return {
            'status': 'verified',
            'message': f'✅ Verified after {stable_count} stable checks: all {total_steps} steps used LLM'
        }
    else:
        # Partial: some steps didn't use LLM (acceptable for efficient frameworks)
        return {
            'status': 'verified',
            'message': f'✅ Verified after {stable_count} stable checks: {steps_with_tokens}/{total_steps} steps used LLM, {coverage_rate:.0%} coverage'
        }
else:
    # Need more stable verifications
    return {
        'status': 'pending',
        'message': f'⏳ Awaiting verification: {stable_count}/{DEFAULT_MIN_STABLE_VERIFICATIONS} stable checks completed'
    }
```

### Configuration
```bash
# In .env file
RECONCILIATION_MIN_STABLE_VERIFICATIONS=2  # Require 2 consecutive stable checks (default)
RECONCILIATION_VERIFICATION_INTERVAL_MIN=60  # 60 minutes between checks
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

**The Golden Rule**: `verified` status requires **data stability** across N consecutive checks (configurable, default: 2), with sufficient time between each check (60+ minutes in production). Token coverage percentage is **informational** - frameworks that intelligently minimize LLM usage are not penalized. This ensures fair comparison of frameworks with different efficiency strategies while maintaining data quality standards.
