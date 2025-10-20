# Documentation Review: Simplified Verification Approach

**Date**: October 20, 2025  
**Purpose**: Review existing documentation before implementing simplified verification approach

## Current System Analysis

### Current Hardcoded Value
**Location**: `src/orchestrator/usage_reconciler.py`, lines 398-480  
**Hardcoded behavior**: Requires exactly **2 consecutive stable verifications** (implicit in the logic)

**Current logic**:
```python
if len(attempts) == 0:
    # First attempt
    return {'status': 'pending', 'message': 'First reconciliation attempt successful, awaiting verification'}

# Get previous attempt (this is attempt 2, 3, 4, etc.)
previous_attempt = attempts[-1]

# Compare current vs previous
if data_identical and time_diff_minutes >= 60:
    if all_steps_have_tokens:
        return {'status': 'verified', ...}  # ✅ Verified after 2nd matching attempt
```

**Issue**: The "2" is implicit - it compares current attempt with previous attempt. No way to require 3+ stable verifications.

## Documentation Review

### 1. VERIFICATION_RULES.md ✅
**Status**: Well-documented but needs update  
**Current content**:
- Explains double-check verification (2 attempts)
- States: "At least 2 reconciliation attempts have been made"
- States: "steps_with_tokens MUST equal total_steps" ← **This is the problematic rule**

**Required changes**:
1. Update to mention configurable number of stable verifications
2. **Remove or soften** the strict "MUST equal total_steps" rule
3. Add section on framework efficiency (zero-token steps as feature)

### 2. usage_reconciliation_guide.md ✅
**Status**: Good quick reference, minimal changes needed  
**Current content**:
- Explains 5-60 minute delay
- Shows workflow: run → wait → reconcile → verify
- Documents command-line usage

**Required changes**:
1. Mention new `RECONCILIATION_MIN_STABLE_VERIFICATIONS` parameter
2. Add example of adjusting verification confidence level

### 3. double_check_verification.md ✅
**Status**: Detailed explanation, needs significant update  
**Current content**:
- Explains "double-check" concept (2 attempts)
- States: "Data is marked 'verified' only when TWO consecutive reconciliation attempts..."
- Documents 60-minute interval configuration

**Required changes**:
1. **Rename concept**: "Double-Check" → "Multi-Check" or "N-Check" verification
2. Update all references to "2 attempts" → "N attempts (configurable)"
3. Add table showing recommended N values:
   - Development: N=1 (fast feedback)
   - Testing: N=2 (current behavior)
   - Production: N=3 (high confidence)
   - Research: N=4 (maximum certainty)

### 4. BAES_ZERO_TOKEN_ANALYSIS.md ✅
**Status**: Recently created, excellent analysis  
**Current content**:
- Documents that BAeS generates code without LLM calls (zero tokens)
- Explains this is efficiency, not a bug
- Recommends treating zero-token steps as acceptable

**Required changes**:
1. Add note that simplified approach **solves this issue**
2. Explain: If tokens stabilize at 3/6 steps after N verifications, accept as complete
3. Update recommendations to reference new verification parameter

## Proposed Changes Summary

### Core Change: Make "2" Configurable

#### Environment Variable (.env)
```bash
# NEW PARAMETER
RECONCILIATION_MIN_STABLE_VERIFICATIONS=2

# Minimum stable verifications before marking as 'verified'
# - Development/Testing: 1-2 (fast feedback)
# - Production: 2-3 (high confidence)  
# - Research/Publication: 3-4 (maximum certainty)
# 
# A "stable verification" means token counts are identical to previous attempt
# with at least RECONCILIATION_VERIFICATION_INTERVAL_MIN between attempts.
```

#### Code Change (usage_reconciler.py)
```python
# At top of file with other defaults
DEFAULT_MIN_STABLE_VERIFICATIONS = int(os.getenv('RECONCILIATION_MIN_STABLE_VERIFICATIONS', '2'))

# In _check_verification_status():
def _check_verification_status(self, run_id: str, current_attempt: dict, metrics: dict) -> dict:
    reconciliation = metrics.get('usage_api_reconciliation', {})
    attempts = reconciliation.get('attempts', [])
    
    # Count consecutive stable attempts
    stable_count = self._count_stable_verifications(attempts, current_attempt)
    
    if stable_count >= DEFAULT_MIN_STABLE_VERIFICATIONS:
        # Check step completeness (but don't require 100%)
        steps_with_tokens = current_attempt.get('steps_with_tokens', 0)
        total_steps = current_attempt.get('total_steps', 0)
        coverage_rate = steps_with_tokens / total_steps if total_steps > 0 else 0
        
        if coverage_rate == 1.0:
            return {
                'status': 'verified',
                'message': f'✅ Complete verification: {stable_count} stable checks, all {total_steps} steps with tokens'
            }
        else:
            return {
                'status': 'verified',
                'message': f'✅ Verified after {stable_count} stable checks ({steps_with_tokens}/{total_steps} steps used LLM, {coverage_rate:.0%} coverage)'
            }
    else:
        return {
            'status': 'pending',
            'message': f'⏳ Awaiting verification: {stable_count}/{DEFAULT_MIN_STABLE_VERIFICATIONS} stable checks completed'
        }

def _count_stable_verifications(self, attempts: list, current_attempt: dict) -> int:
    """Count consecutive stable verifications (identical token counts with sufficient time gap)."""
    if len(attempts) == 0:
        return 0  # First attempt, no stability yet
    
    stable_count = 0
    prev = current_attempt
    
    # Walk backwards through attempts
    for attempt in reversed(attempts):
        # Check time gap
        current_time = datetime.fromisoformat(prev['timestamp'])
        prev_time = datetime.fromisoformat(attempt['timestamp'])
        time_diff = (current_time - prev_time).total_seconds() / 60
        
        if time_diff < DEFAULT_VERIFICATION_INTERVAL_MIN:
            break  # Gap too small, stop counting
        
        # Check if identical
        if (prev['total_tokens_in'] == attempt['total_tokens_in'] and
            prev['total_tokens_out'] == attempt['total_tokens_out']):
            stable_count += 1
            prev = attempt
        else:
            break  # Not identical, stop counting
    
    return stable_count
```

## Documentation Update Plan

### Phase 1: Update Core Verification Docs (High Priority)

**Files to update**:
1. `VERIFICATION_RULES.md` - Remove strict "steps_with_tokens == total_steps" rule
2. `double_check_verification.md` - Update to N-check verification
3. `.env` - Add new parameter with explanation

**Estimated time**: 1-2 hours

### Phase 2: Update Reference Docs (Medium Priority)

**Files to update**:
1. `usage_reconciliation_guide.md` - Mention new parameter
2. `configuration_reference.md` - Document new parameter
3. `quickstart.md` - Update verification explanation if mentioned

**Estimated time**: 30 minutes

### Phase 3: Update Analysis Docs (Low Priority)

**Files to update**:
1. `BAES_ZERO_TOKEN_ANALYSIS.md` - Add resolution note
2. Archive old comprehensive plans:
   - Move `VERIFICATION_UPDATE_PLAN.md` to `docs/archived/`
   - Move `VERIFICATION_UPDATE_CHECKLIST.md` to `docs/archived/`
   - Move `VERIFICATION_UPDATE_SUMMARY.md` to `docs/archived/`

**Estimated time**: 15 minutes

## Key Insights from Documentation Review

### 1. The "2" is Actually Well-Documented
Current docs consistently state "2 attempts" and explain the double-check concept clearly. Making this configurable is a natural evolution.

### 2. The Real Problem is "all_steps_have_tokens" Check
The strict requirement `steps_with_tokens == total_steps` is **the actual issue**, not the number of verification attempts.

### 3. Your Simplified Approach Solves BOTH Problems
By making N configurable AND accepting stable data even with partial token coverage, we solve:
- **Problem 1**: BAeS zero-token steps (solved by accepting <100% coverage)
- **Problem 2**: Confidence level tuning (solved by configurable N)

### 4. "Double-Check" Terminology Needs Update
If N can be 1, 2, 3, or 4, calling it "double-check" is misleading. Better terms:
- "Multi-check verification"
- "N-check verification"
- "Stability verification"
- "Consecutive verification"

## Recommended Implementation Order

### Step 1: Code Changes (1-2 hours)
1. Add `RECONCILIATION_MIN_STABLE_VERIFICATIONS` to `.env`
2. Implement `_count_stable_verifications()` method
3. Update `_check_verification_status()` to use N checks
4. **Remove strict** `all_steps_have_tokens` requirement for verification
5. Add informative messages showing coverage rate

### Step 2: Test Implementation (30 minutes)
1. Test with N=1 (should verify after 2nd attempt if stable)
2. Test with N=2 (should verify after 3rd attempt if stable)
3. Test with N=3 (should verify after 4th attempt if stable)
4. Test with BAeS run (3/6 tokens should verify after N stable checks)

### Step 3: Update Documentation (2 hours)
1. Update `VERIFICATION_RULES.md` - new rules
2. Update `double_check_verification.md` - N-check concept
3. Update `usage_reconciliation_guide.md` - new parameter
4. Add note to `BAES_ZERO_TOKEN_ANALYSIS.md` - issue resolved

### Step 4: Cleanup (15 minutes)
1. Archive comprehensive plans that are now obsolete
2. Update README if verification mentioned
3. Commit with clear message

## Potential Issues & Mitigations

### Issue 1: Backward Compatibility
**Risk**: Existing runs have only 2 attempts recorded  
**Mitigation**: Default N=2 preserves current behavior

### Issue 2: N=1 Might Be Too Permissive
**Risk**: Single check might catch unstable data  
**Mitigation**: Document that N=1 is for development only, require N≥2 for production

### Issue 3: Documentation Consistency
**Risk**: Multiple docs reference "double-check"  
**Mitigation**: Update all docs in same commit, grep for "double-check" to find all

### Issue 4: Analysis Scripts
**Risk**: Scripts might assume status='verified' means 100% coverage  
**Mitigation**: Review analysis scripts, add coverage rate filtering if needed

## Success Criteria

✅ **Simplified approach successfully implemented when:**
1. `RECONCILIATION_MIN_STABLE_VERIFICATIONS` parameter exists and works
2. BAeS run with 3/6 tokens gets `verified` status after N stable checks
3. Documentation consistently explains N-check verification
4. No references to hardcoded "2" remain in code
5. Verification messages show coverage rate (e.g., "50% coverage")

## Conclusion

**Your simplified approach is the right solution.** The documentation review confirms:

1. ✅ Current system is well-documented (easy to update consistently)
2. ✅ Making "2" configurable is a natural evolution
3. ✅ Removing strict "all steps must have tokens" rule fixes BAeS issue
4. ✅ Implementation is straightforward (~4 hours total including docs)

**Recommendation**: Proceed with simplified approach. Archive the comprehensive plans (they served their purpose as analysis but are now obsolete).

---

**Next Action**: Shall I implement the simplified approach?
- Add `RECONCILIATION_MIN_STABLE_VERIFICATIONS` parameter
- Implement `_count_stable_verifications()` logic
- Update verification to accept <100% token coverage
- Update documentation to match
