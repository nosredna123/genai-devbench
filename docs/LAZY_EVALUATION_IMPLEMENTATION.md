# Lazy Evaluation Implementation Summary

**Date:** October 20, 2025  
**Implementation:** Option 3 - Lazy Evaluation Approach

## Changes Made

### 1. Base Adapter (`src/adapters/base_adapter.py`)

**Changed:** `fetch_usage_from_openai()` method

**Before:**
- Queried OpenAI Usage API during step execution
- Returned actual token counts or (0, 0, 0, 0) on errors
- Silent failures from API propagation delays

**After:**
- Immediately returns (0, 0, 0, 0) - lazy evaluation stub
- Logs debug message indicating reconciliation is needed
- No API calls during execution

**Code:**
```python
def fetch_usage_from_openai(self, ...) -> Tuple[int, int, int, int]:
    """
    Lazy evaluation stub for token usage collection.
    Returns (0, 0, 0, 0) - metrics backfilled by reconciliation script.
    """
    logger.debug("Lazy evaluation: returning zero metrics (reconciliation required)")
    return 0, 0, 0, 0
```

**Impact:** All 3 adapters (BAeS, ChatDev, GHSpec) automatically inherit this behavior.

---

### 2. Metrics Collector (`src/orchestrator/metrics_collector.py`)

**Changed:** `record_step()` method

**Before:**
- Validated that successful steps had tokens > 0 and api_calls >= 1
- Raised ValueError on impossible metric combinations

**After:**
- Accepts zeros without validation during execution
- Adds `verification_status: 'pending'` to each step
- Validation delegated to reconciliation script

**Code:**
```python
def record_step(self, step_num, ..., tokens_in=0, tokens_out=0, ...):
    """
    LAZY EVALUATION PATTERN:
    Token metrics will be 0 initially, backfilled by reconciliation.
    """
    self.steps_data[step_num] = {
        ...
        'verification_status': 'pending'  # Added
    }
```

---

### 3. Orchestrator Runner (`src/orchestrator/runner.py`)

**Changed:** Usage API verification logic

**Before:**
- Called `OpenAIAPIClient.verify_token_counts()` after run completion
- Attempted to verify token counts immediately

**After:**
- Skips Usage API verification during execution
- Sets `verification_status: 'pending'` at run level
- Sets `usage_api_verification.error` with clear message

**Code:**
```python
# LAZY EVALUATION: Skip Usage API verification during execution
logger.info("Skipping Usage API verification (lazy evaluation)")
metrics['verification_status'] = 'pending'
metrics['usage_api_verification'] = {
    'verified': False,
    'error': 'Lazy evaluation - use reconciliation script'
}
```

**Also changed:** Manifest update to use aggregate_metrics properly:
```python
'total_tokens_in': metrics['aggregate_metrics'].get('TOK_IN', 0),
'total_tokens_out': metrics['aggregate_metrics'].get('TOK_OUT', 0)
```

---

### 4. Reset Script (`scripts/reset_metrics_for_reconciliation.py`)

**Created:** New utility to reset verification status

**Purpose:**
- Marks existing runs as needing reconciliation
- Sets `verification_status: 'pending'`
- Removes `usage_api_reconciliation` data to allow fresh reconciliation

**Usage:**
```bash
# Reset all runs
python scripts/reset_metrics_for_reconciliation.py

# Reset specific framework
python scripts/reset_metrics_for_reconciliation.py chatdev

# Reset specific run
python scripts/reset_metrics_for_reconciliation.py chatdev run-id

# Dry run
python scripts/reset_metrics_for_reconciliation.py --dry-run
```

---

### 5. Documentation (`docs/LAZY_EVALUATION_PATTERN.md`)

**Created:** Comprehensive documentation covering:
- Architecture and design rationale
- Before/after comparison
- Implementation details
- Usage guide
- Verification status states
- Migration notes

---

## DRY Principle Adherence

✅ **Single Implementation:** `BaseAdapter.fetch_usage_from_openai()`  
✅ **All Adapters Inherit:** BAeS, ChatDev, GHSpec use same method  
✅ **No Duplication:** Token collection logic exists only in reconciliation script  
✅ **Consistent Behavior:** All steps processed identically  

---

## Benefits Achieved

### 1. Consistency
- All steps have the same workflow
- No special cases for short vs. long steps
- Predictable behavior across frameworks

### 2. Reliability
- No silent failures from API propagation delays
- Clear indication when data needs verification (`verification_status: 'pending'`)
- Reconciliation script handles all API timing issues

### 3. Simplicity
- Adapters don't need Usage API credentials
- No error handling for API failures during execution
- Centralized metrics collection logic

### 4. Transparency
- `verification_status` clearly shows data state
- Logs explain lazy evaluation pattern
- Users know when to run reconciliation

---

## Migration Path for Existing Runs

For the example run `c420e4fe-354d-4db2-a374-5a381c96e08b`:

```bash
# Step 1: Reset to pending status
python scripts/reset_metrics_for_reconciliation.py ghspec c420e4fe-354d-4db2-a374-5a381c96e08b

# Step 2: Run reconciliation (will backfill all token data)
./runners/reconcile_usage.sh ghspec c420e4fe-354d-4db2-a374-5a381c96e08b
```

**Result:**
- Steps 1, 2, 3, 6 will get correct token counts
- `verification_status` changes from `'pending'` → `'verified'`
- `usage_api_reconciliation` section added with attempt history

---

## Testing Recommendations

### 1. New Runs
```bash
# Run experiment
./runners/run_experiment.sh baes

# Verify metrics.json has:
# - verification_status: 'pending'
# - All token metrics: 0
# - All steps have verification_status: 'pending'

# Run reconciliation
./runners/reconcile_usage.sh

# Verify metrics.json updated with:
# - verification_status: 'verified'
# - Actual token counts
# - usage_api_reconciliation section
```

### 2. Existing Runs
```bash
# Reset status
python scripts/reset_metrics_for_reconciliation.py --dry-run  # Preview
python scripts/reset_metrics_for_reconciliation.py            # Apply

# Reconcile
./runners/reconcile_usage.sh
```

### 3. Validation
```bash
# Check all runs are verified
grep -r "verification_status" runs/*/*/metrics.json | grep -v "verified"

# Should return empty if all runs reconciled successfully
```

---

## Files Modified

1. `src/adapters/base_adapter.py` - Lazy evaluation stub
2. `src/orchestrator/metrics_collector.py` - Accept zeros, add verification_status
3. `src/orchestrator/runner.py` - Skip immediate verification
4. `scripts/reset_metrics_for_reconciliation.py` - New reset utility (created)
5. `docs/LAZY_EVALUATION_PATTERN.md` - Documentation (created)

---

## Rollback Plan (If Needed)

If you need to revert these changes:

1. Restore `base_adapter.py` to query Usage API
2. Restore `metrics_collector.py` validation logic
3. Restore `runner.py` verification calls
4. Delete reset script and documentation

**Note:** Existing metrics.json files with `verification_status: 'pending'` will still work - reconciliation script will process them correctly.

---

## Next Steps

1. ✅ Test with a new experimental run
2. ✅ Run reset script on existing runs
3. ✅ Execute reconciliation script
4. ✅ Verify all metrics have `verification_status: 'verified'`
5. Document any issues or edge cases discovered

---

## Questions & Answers

**Q: Will old runs still work?**  
A: Yes. Use the reset script to mark them as `'pending'`, then run reconciliation.

**Q: What if reconciliation fails?**  
A: Metrics remain at `verification_status: 'pending'`. Check logs, fix issues, re-run reconciliation.

**Q: Can I run reconciliation multiple times?**  
A: Yes. Use reset script to clear previous reconciliation data, then re-run.

**Q: Do I need to wait 15 minutes before reconciliation?**  
A: Reconciliation script handles this automatically - it will wait if needed.

---

**Implementation Complete** ✓
