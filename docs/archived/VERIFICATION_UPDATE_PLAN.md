# Verification System Update Plan
**Date**: October 20, 2025  
**Issue**: Current verification rule (`steps_with_tokens == total_steps`) is too strict and penalizes efficient frameworks  
**Goal**: Treat zero-token steps as efficiency feature, not data quality issue

## Problem Statement

The current verification rule requires ALL steps to have tokens to mark a run as "verified":
```python
all_steps_have_tokens = (steps_with_tokens == total_steps)
if not all_steps_have_tokens:
    return {'status': 'warning', 'message': '⚠️ Data stable but incomplete...'}
```

**Why this is wrong:**
- BAeS framework intelligently avoids unnecessary LLM calls using templates/rules
- Steps 3, 4, 6 in BAeS generate correct code WITHOUT calling OpenAI API
- Lower token usage = Lower cost = Better efficiency = Should be REWARDED, not penalized
- Current rule treats this as "incomplete data" when it's actually "smart optimization"

## Design Principles

1. **Efficiency is a feature**: Frameworks that minimize LLM calls while producing correct output should score BETTER
2. **Measure what matters**: Track BOTH execution completeness AND token usage separately
3. **Fair comparison**: Don't penalize frameworks for being smart about API usage
4. **Data quality first**: Still require stable, consistent metrics for statistical validity

## Solution Architecture

### 1. New Verification Status Model

Replace binary `all_steps_have_tokens` check with multi-dimensional verification:

```python
verification = {
    'execution_complete': True/False,    # All steps executed successfully
    'data_stable': True/False,           # Token counts unchanged across checks
    'token_coverage_rate': 0.0-1.0,      # Percentage of steps with tokens
    'verification_status': 'pending'|'verified'|'warning'|'failed'
}
```

**New Status Rules:**
- `verified`: execution_complete=True AND data_stable=True AND token_coverage_rate >= 0.5
- `warning`: execution_complete=True AND (data_stable=False OR token_coverage_rate < 0.5)
- `pending`: First reconciliation attempt, awaiting double-check
- `failed`: execution_complete=False

### 2. Framework-Specific Thresholds

Add configuration support for framework-specific verification rules:

```yaml
# In config/experiment.yaml
verification:
  global:
    min_token_coverage_rate: 0.5        # At least 50% steps must have tokens
    double_check_interval_minutes: 60   # Time between verification attempts
    max_double_check_attempts: 3        # Give up after 3 attempts
  
  framework_overrides:
    baes:
      min_token_coverage_rate: 0.5      # Allow template-based steps
      allow_zero_token_steps: true
      notes: "BAeS uses templates/rules for certain operations"
    
    chatdev:
      min_token_coverage_rate: 0.9      # Expect most steps to use LLM
      allow_zero_token_steps: false
      notes: "ChatDev typically calls LLM for all operations"
    
    ghspec:
      min_token_coverage_rate: 0.9      # Expect most steps to use LLM
      allow_zero_token_steps: false
      notes: "GHSpec typically calls LLM for all operations"
```

### 3. Enhanced Metrics Tracking

Track execution and token metrics separately:

```json
{
  "run_id": "23f46f6b-...",
  "execution": {
    "total_steps": 6,
    "steps_completed": 6,
    "steps_failed": 0,
    "completion_rate": 1.0
  },
  "token_usage": {
    "total_steps": 6,
    "steps_with_tokens": 3,
    "steps_with_zero_tokens": 3,
    "token_coverage_rate": 0.5,
    "total_tokens_in": 25156,
    "total_tokens_out": 6481,
    "total_api_calls": 15
  },
  "verification": {
    "status": "verified",
    "execution_complete": true,
    "data_stable": true,
    "token_coverage_sufficient": true,
    "attempts": 2,
    "message": "✓ All steps completed successfully. 3/6 steps used LLM, 3/6 used templates (expected for BAeS)."
  }
}
```

## Implementation Plan

### Phase 1: Update Data Model (Low Risk, Foundation)
**Time**: 2-3 hours  
**Files**: `src/orchestrator/usage_reconciler.py`, `src/orchestrator/experiment_orchestrator.py`

**Tasks:**
1. ✅ Add `execution` section to metrics.json schema
2. ✅ Add `token_coverage_rate` calculation
3. ✅ Track `steps_completed` separately from `steps_with_tokens`
4. ✅ Update manifest schema to include new fields

**Validation:**
- Run reconciliation on existing runs
- Verify new fields are populated correctly
- Ensure backward compatibility with existing metrics.json files

### Phase 2: Update Verification Logic (Medium Risk, Core Change)
**Time**: 3-4 hours  
**Files**: `src/orchestrator/usage_reconciler.py`

**Tasks:**
1. ✅ Modify `_check_verification_status()` to use new rules
2. ✅ Replace `all_steps_have_tokens` check with `token_coverage_rate` check
3. ✅ Add framework-aware threshold checking
4. ✅ Update status messages to reflect new model

**Code Changes:**
```python
def _check_verification_status(self, run_id: str, current_attempt: dict, 
                                previous_attempt: dict) -> dict:
    """Check if run can be marked as verified using new multi-dimensional model."""
    
    # Extract metrics
    steps_with_tokens = current_attempt.get('steps_with_tokens', 0)
    total_steps = current_attempt.get('total_steps', 0)
    steps_completed = current_attempt.get('steps_completed', total_steps)  # NEW
    
    # Calculate rates
    completion_rate = steps_completed / total_steps if total_steps > 0 else 0
    token_coverage_rate = steps_with_tokens / total_steps if total_steps > 0 else 0
    
    # Check execution completeness
    execution_complete = (completion_rate == 1.0)
    if not execution_complete:
        return {
            'status': 'failed',
            'message': f'⚠️ Only {steps_completed}/{total_steps} steps completed successfully'
        }
    
    # Check data stability
    if not previous_attempt:
        return {
            'status': 'pending',
            'message': '⏳ First reconciliation attempt successful, awaiting verification'
        }
    
    prev_tokens_in = previous_attempt.get('total_tokens_in', 0)
    curr_tokens_in = current_attempt.get('total_tokens_in', 0)
    data_stable = (prev_tokens_in == curr_tokens_in) and (prev_tokens_in > 0 or curr_tokens_in > 0)
    
    if not data_stable:
        return {
            'status': 'warning',
            'message': f'⚠️ Token counts still changing: {prev_tokens_in} → {curr_tokens_in}'
        }
    
    # Check token coverage (framework-aware)
    framework = current_attempt.get('framework', 'unknown')
    min_coverage = self._get_min_token_coverage(framework)
    token_coverage_sufficient = (token_coverage_rate >= min_coverage)
    
    if not token_coverage_sufficient:
        return {
            'status': 'warning',
            'message': (
                f'⚠️ Low token coverage: {steps_with_tokens}/{total_steps} steps '
                f'({token_coverage_rate:.0%}) have tokens. '
                f'Minimum required: {min_coverage:.0%}'
            )
        }
    
    # All checks passed - VERIFIED
    if steps_with_tokens == total_steps:
        message = f'✓ All steps completed and verified with complete token coverage'
    else:
        zero_token_steps = total_steps - steps_with_tokens
        message = (
            f'✓ All steps completed successfully. '
            f'{steps_with_tokens}/{total_steps} steps used LLM, '
            f'{zero_token_steps}/{total_steps} used templates/rules '
            f'(expected for {framework}).'
        )
    
    return {
        'status': 'verified',
        'message': message
    }

def _get_min_token_coverage(self, framework: str) -> float:
    """Get minimum token coverage threshold for framework."""
    # Load from config in Phase 3, hardcode for Phase 2
    thresholds = {
        'baes': 0.5,      # 50% - allows template-based steps
        'chatdev': 0.9,   # 90% - expects most steps to use LLM
        'ghspec': 0.9,    # 90% - expects most steps to use LLM
    }
    return thresholds.get(framework.lower(), 0.9)  # Default: require 90%
```

**Validation:**
- Test with run `23f46f6b-929e-429b-ba74-4b0d20abc1ed` (BAeS, 3/6 tokens)
- Should be marked as `verified` with appropriate message
- Test with ChatDev runs (should require higher coverage)

### Phase 3: Configuration Support (Low Risk, Enhancement)
**Time**: 2 hours  
**Files**: `config/experiment.yaml`, `src/orchestrator/usage_reconciler.py`

**Tasks:**
1. ✅ Add `verification` section to experiment.yaml
2. ✅ Load framework-specific thresholds from config
3. ✅ Update `_get_min_token_coverage()` to read from config
4. ✅ Add validation for config values

**Validation:**
- Modify thresholds in config
- Verify reconciliation respects new values
- Test with invalid values (should use defaults)

### Phase 4: Update Documentation (Low Risk, Required)
**Time**: 1-2 hours  
**Files**: `docs/VERIFICATION_RULES.md`, `docs/quickstart.md`, `README.md`

**Tasks:**
1. ✅ Update verification rules documentation
2. ✅ Add framework comparison section explaining efficiency differences
3. ✅ Update troubleshooting guide
4. ✅ Add examples of different verification scenarios

### Phase 5: Reconcile Existing Runs (Medium Risk, Data Migration)
**Time**: 1 hour + run time  
**Files**: New script `scripts/update_verification_status.py`

**Tasks:**
1. ✅ Create script to re-reconcile all existing runs
2. ✅ Update verification status using new rules
3. ✅ Preserve original metrics, add new fields
4. ✅ Update runs_manifest.json

**Script outline:**
```python
#!/usr/bin/env python3
"""Re-reconcile all runs using updated verification rules."""

import json
from pathlib import Path
from src.orchestrator.usage_reconciler import UsageReconciler

def update_all_runs():
    manifest_path = Path("runs/runs_manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    for framework, runs in manifest.items():
        print(f"\n=== Updating {framework} runs ===")
        for run_id, run_data in runs.items():
            if run_data.get('verification_status') in ['warning', 'verified']:
                print(f"Re-reconciling {run_id}...")
                # Re-run reconciliation with new rules
                # This will update verification status automatically
```

**Validation:**
- Backup manifest before running
- Compare before/after verification statuses
- Verify BAeS runs with 50%+ token coverage are marked as verified

### Phase 6: Update Analysis & Reporting (Low Risk, Enhancement)
**Time**: 2-3 hours  
**Files**: `src/analysis/report_generator.py`, `scripts/generate_analysis.py`

**Tasks:**
1. ✅ Update report templates to show execution vs token metrics separately
2. ✅ Add efficiency analysis section
3. ✅ Highlight frameworks that minimize API usage
4. ✅ Add cost efficiency metrics

**New report sections:**
```markdown
## Efficiency Analysis

### Token Usage Efficiency
- **BAeS**: 50% of steps used LLM (3/6), 50% used templates
  - Average tokens per LLM step: 8,385
  - Cost per feature: $0.XX
  - **Efficiency score**: High (minimizes unnecessary API calls)

- **ChatDev**: 100% of steps used LLM (6/6)
  - Average tokens per LLM step: 12,456
  - Cost per feature: $0.XX
  - **Efficiency score**: Standard (consistent LLM usage)

### Cost-Benefit Analysis
Framework | Total Cost | Features Delivered | Cost per Feature
----------|------------|-------------------|------------------
BAeS      | $0.XX      | 6                 | $0.XX
ChatDev   | $0.XX      | 6                 | $0.XX
GHSpec    | $0.XX      | 6                 | $0.XX
```

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_verification_logic.py
def test_baes_with_50_percent_coverage_is_verified():
    """BAeS runs with 50% token coverage should be verified."""
    metrics = {
        'framework': 'baes',
        'total_steps': 6,
        'steps_completed': 6,
        'steps_with_tokens': 3,
        'total_tokens_in': 25156
    }
    status = check_verification_status(metrics, previous=metrics)
    assert status['status'] == 'verified'

def test_chatdev_with_50_percent_coverage_is_warning():
    """ChatDev runs with 50% token coverage should be warning."""
    metrics = {
        'framework': 'chatdev',
        'total_steps': 6,
        'steps_completed': 6,
        'steps_with_tokens': 3,
        'total_tokens_in': 25156
    }
    status = check_verification_status(metrics, previous=metrics)
    assert status['status'] == 'warning'
```

### Integration Tests
- Run full experiment with BAeS (expect verified with 50%+ coverage)
- Run reconciliation on all frameworks
- Verify analysis report generates correctly

### Regression Tests
- Ensure existing verified runs remain verified
- Ensure metrics values unchanged (only status/messages updated)
- Ensure backward compatibility with old metrics.json format

## Rollout Plan

### Step 1: Development (Today)
1. Create feature branch: `git checkout -b feature/efficient-verification`
2. Implement Phase 1 (data model)
3. Implement Phase 2 (verification logic)
4. Write unit tests
5. Test manually with run `23f46f6b-929e-429b-ba74-4b0d20abc1ed`

### Step 2: Validation (Tomorrow)
1. Run full BAeS experiment
2. Verify new runs marked as verified with 50% coverage
3. Run reconciliation on existing runs
4. Compare before/after analysis reports

### Step 3: Deployment (After validation)
1. Merge to main branch
2. Update documentation
3. Re-reconcile all existing runs
4. Generate new analysis report
5. Archive old report for comparison

### Step 4: Monitoring (Ongoing)
1. Monitor verification rates across frameworks
2. Adjust thresholds if needed
3. Document any edge cases
4. Update documentation based on findings

## Success Metrics

### Quantitative
- ✅ BAeS runs with 50%+ token coverage marked as verified
- ✅ All existing verified runs remain verified (no false negatives)
- ✅ No runs incorrectly marked as verified (no false positives)
- ✅ Test coverage > 90% for new verification logic

### Qualitative
- ✅ Verification status messages are clear and actionable
- ✅ Documentation explains efficiency vs completeness trade-off
- ✅ Analysis report highlights framework efficiency differences
- ✅ Team understands new verification model

## Risk Mitigation

### Risk: Breaking existing analysis
**Mitigation**: 
- Preserve all original metrics
- Only ADD new fields, don't remove old ones
- Test report generation with before/after data

### Risk: Incorrect verification decisions
**Mitigation**:
- Conservative thresholds (50% for BAeS, 90% for others)
- Manual review of first 10 runs after deployment
- Easy rollback via git revert

### Risk: Framework misclassification
**Mitigation**:
- Framework name detection from run data
- Explicit configuration per framework
- Default to strict rules (90%) if framework unknown

## Open Questions

1. **Should we track WHICH steps have zero tokens?**
   - Pro: Could identify patterns (e.g., "validation steps never use LLM")
   - Con: Adds complexity, may not be actionable
   - **Decision**: Add in Phase 6 as optional enhancement

2. **Should we verify that zero-token steps actually generated code?**
   - Pro: Ensures steps weren't just skipped
   - Con: Requires code analysis, adds complexity
   - **Decision**: Out of scope for now, track as future work

3. **How to handle frameworks that improve efficiency over time?**
   - E.g., BAeS v2 might use LLM less than v1
   - **Decision**: Track framework version, allow per-version thresholds

## Related Documents
- [BAeS Zero Token Analysis](BAES_ZERO_TOKEN_ANALYSIS.md) - Root cause investigation
- [Verification Rules](VERIFICATION_RULES.md) - Current (outdated) rules
- [Metrics Configuration](METRICS_CONFIG_SCHEMA.md) - Metrics schema reference

## Appendix: Example Status Messages

### Verified (100% token coverage)
```
✓ All steps completed and verified with complete token coverage
```

### Verified (Partial token coverage, BAeS)
```
✓ All steps completed successfully. 3/6 steps used LLM, 3/6 used templates/rules (expected for baes).
```

### Warning (Low coverage, ChatDev)
```
⚠️ Low token coverage: 3/6 steps (50%) have tokens. Minimum required: 90%
```

### Warning (Data unstable)
```
⚠️ Token counts still changing: 23456 → 25156. Awaiting stabilization.
```

### Pending (First attempt)
```
⏳ First reconciliation attempt successful, awaiting verification
```

### Failed (Incomplete execution)
```
⚠️ Only 4/6 steps completed successfully
```
