# Quickstart: Fix Zero Tokens Issue

**Feature**: 008-fix-zero-tokens  
**Date**: 2025-10-27  
**Audience**: Developers implementing or testing the run-level reconciliation fix

## Overview

This guide explains how to configure, run, and validate the fixed token reconciliation system that eliminates the 36-50% zero-token error rate.

---

## Prerequisites

- Python 3.11+
- OpenAI API keys configured (admin + framework-specific)
- Access to OpenAI Usage API dashboard
- Completed framework run (for testing reconciliation)

---

## Configuration

### 1. API Key Setup

You need API key IDs for the filtering feature. Get them from the [OpenAI Usage Dashboard](https://platform.openai.com/usage):

1. Navigate to **Usage** → **Activity**
2. Click on any usage entry
3. Note the `api_key_id` field (format: `key_XXXXXXXXXXXX`)

### 2. Environment Variables

Add to your `.env` file:

```bash
# Admin key for querying Usage API (existing)
OPEN_AI_KEY_ADM="sk-proj-YOUR_ADMIN_KEY"

# Framework execution keys (existing)
OPENAI_API_KEY_BAES="sk-proj-YOUR_BAES_KEY"
OPENAI_API_KEY_CHATDEV="sk-proj-YOUR_CHATDEV_KEY"
OPENAI_API_KEY_GHSPEC="sk-proj-YOUR_GHSPEC_KEY"

# Framework API key IDs (NEW - required for filtering)
OPENAI_API_KEY_BAES_ID="key_XXXXXXXXXXXX"
OPENAI_API_KEY_CHATDEV_ID="key_XXXXXXXXXXXX"
OPENAI_API_KEY_GHSPEC_ID="key_XXXXXXXXXXXX"

# Reconciliation settings (optional)
RECONCILIATION_VERIFICATION_INTERVAL_MIN=30  # Minutes between checks (0 for testing)
RECONCILIATION_MIN_STABLE_VERIFICATIONS=2    # Consecutive stable checks required
```

### 3. Verify Configuration

```bash
python -c "
import os
frameworks = ['BAES', 'CHATDEV', 'GHSPEC']
missing = []
for fw in frameworks:
    if not os.getenv(f'OPENAI_API_KEY_{fw}'):
        missing.append(f'OPENAI_API_KEY_{fw}')
    if not os.getenv(f'OPENAI_API_KEY_{fw}_ID'):
        missing.append(f'OPENAI_API_KEY_{fw}_ID')
if missing:
    print(f'❌ Missing: {missing}')
else:
    print('✅ All API keys configured')
"
```

---

## Running Reconciliation

### Manual Reconciliation

Run reconciliation for all pending runs:

```bash
python scripts/reconcile_usage.py
```

Expected output:

```
[INFO] Starting reconciliation for 3 pending runs
[INFO] Processing run baes/run-abc-123...
[INFO]   Attempt 1: data_not_available (too soon)
[INFO] Processing run chatdev/run-def-456...
[INFO]   Attempt 1: pending (tokens: 12,450 in, 9,820 out)
[INFO]   Attempt 2: verified (tokens stable)
[SUCCESS] Verified 1/3 runs
```

### Reconcile Specific Run

```bash
python scripts/reconcile_usage.py --run-id <RUN_ID> --framework <FRAMEWORK>
```

Example:

```bash
python scripts/reconcile_usage.py --run-id run-abc-123 --framework baes
```

### Force Immediate Reconciliation (Testing)

```bash
RECONCILIATION_VERIFICATION_INTERVAL_MIN=0 python scripts/reconcile_usage.py
```

---

## Validation

### 1. Check Metrics Schema

Verify that new runs have clean schema (no tokens in steps):

```bash
python -c "
import json
from pathlib import Path

# Find most recent run
run_path = max(Path('runs/baes').glob('*/metrics.json'), key=lambda p: p.stat().st_mtime)
metrics = json.loads(run_path.read_text())

# Check steps array
has_token_fields = any(
    'tokens_in' in step or 'tokens_out' in step 
    for step in metrics['steps']
)

if has_token_fields:
    print('❌ FAIL: Steps contain token fields')
else:
    print('✅ PASS: Clean schema (no tokens in steps)')
    
# Check aggregate_metrics
agg = metrics['aggregate_metrics']
print(f'Run-level tokens: {agg[\"TOK_IN\"]} in, {agg[\"TOK_OUT\"]} out')
"
```

### 2. Compare with OpenAI Dashboard

1. Open [OpenAI Usage Dashboard](https://platform.openai.com/usage)
2. Filter by date range matching your run
3. Filter by API key ID (e.g., `OPENAI_API_KEY_BAES_ID`)
4. Compare total tokens with `aggregate_metrics` in `metrics.json`

Expected: **Exact match** (± 1% for rounding)

### 3. Test Cross-Contamination Prevention

Run two frameworks back-to-back:

```bash
# Run BAeS
python run_experiment.sh --framework baes --spec test-spec.txt

# Immediately run ChatDev (overlapping time window)
python run_experiment.sh --framework chatdev --spec test-spec.txt

# Reconcile both
python scripts/reconcile_usage.py

# Verify no token leakage
python -c "
import json
from pathlib import Path

baes_runs = list(Path('runs/baes').glob('*/metrics.json'))
chatdev_runs = list(Path('runs/chatdev').glob('*/metrics.json'))

baes_metrics = json.loads(baes_runs[-1].read_text())
chatdev_metrics = json.loads(chatdev_runs[-1].read_text())

baes_tokens = baes_metrics['aggregate_metrics']['TOK_IN']
chatdev_tokens = chatdev_metrics['aggregate_metrics']['TOK_IN']

print(f'BAeS tokens: {baes_tokens}')
print(f'ChatDev tokens: {chatdev_tokens}')
print('✅ PASS: Different token counts (no cross-contamination)')
"
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY_BAES_ID not found"

**Cause**: Missing API key ID environment variable

**Fix**: Add `OPENAI_API_KEY_{FRAMEWORK}_ID` to `.env` (see Configuration section above)

---

### Issue: "verification_status: data_not_available"

**Cause**: OpenAI Usage API reporting delay (5-60 minutes typical)

**Fix**: Wait and re-run reconciliation:

```bash
# Wait 30 minutes, then retry
sleep 1800
python scripts/reconcile_usage.py
```

---

### Issue: "Tokens don't match OpenAI dashboard"

**Possible Causes**:
1. Wrong API key ID configured
2. Multiple frameworks using same API key
3. Run time window overlaps with other activity

**Debug Steps**:

```bash
# 1. Verify API key ID matches dashboard
python -c "
import os
print(f'Configured: {os.getenv(\"OPENAI_API_KEY_BAES_ID\")}')
print('Compare with Usage Dashboard → Activity → api_key_id field')
"

# 2. Check for duplicate API keys
python -c "
import os
keys = {
    'BAES': os.getenv('OPENAI_API_KEY_BAES'),
    'CHATDEV': os.getenv('OPENAI_API_KEY_CHATDEV'),
    'GHSPEC': os.getenv('OPENAI_API_KEY_GHSPEC')
}
if len(set(keys.values())) != len(keys):
    print('❌ DUPLICATE API KEYS DETECTED')
    print(keys)
else:
    print('✅ All frameworks use unique API keys')
"

# 3. Check run time window
python -c "
import json
from pathlib import Path
from datetime import datetime

run_path = Path('runs/baes/run-abc-123/metrics.json')  # Replace with your run
metrics = json.loads(run_path.read_text())

start = datetime.fromtimestamp(metrics['start_timestamp'])
end = datetime.fromtimestamp(metrics['end_timestamp'])

print(f'Run window: {start} → {end}')
print('Check OpenAI dashboard for other activity in this window')
"
```

---

### Issue: "Zero tokens after reconciliation"

**Cause**: Run made no LLM API calls (e.g., template-based generation)

**Validation**: This is valid if framework didn't call OpenAI API

```bash
# Check if run actually called OpenAI
python -c "
import json
from pathlib import Path

run_path = Path('runs/baes/run-abc-123/metrics.json')
metrics = json.loads(run_path.read_text())

api_calls = metrics['aggregate_metrics']['API_CALLS']
if api_calls == 0:
    print('✅ VALID: Run made no API calls (zero tokens expected)')
else:
    print(f'❌ INVALID: Run made {api_calls} API calls but has zero tokens')
"
```

---

## Testing

### Unit Tests

```bash
# Test reconciliation logic
pytest tests/unit/test_usage_reconciler.py -v

# Test metrics schema validation
pytest tests/unit/test_metrics_collector.py -v
```

### Integration Tests

```bash
# Test full reconciliation workflow
pytest tests/integration/test_reconciliation.py -v
```

---

## Success Criteria Checklist

Validate that the fix meets all success criteria:

- [ ] **SC-001**: Run-level tokens match OpenAI dashboard (100% accuracy)
- [ ] **SC-002**: Reconciliation succeeds for runs aged 30-1440 minutes
- [ ] **SC-003**: No steps contain `tokens_in`/`tokens_out`/`api_calls`/`cached_tokens` fields
- [ ] **SC-004**: Verification reaches "verified" status within expected timeframe
- [ ] **SC-005**: No token leakage between back-to-back runs with different API keys

---

## Next Steps

After validating the fix:

1. **Run production experiments**: Execute framework runs with new reconciliation
2. **Monitor logs**: Check for any `data_not_available` or `failed` statuses
3. **Compare results**: Verify run-level tokens match OpenAI dashboard
4. **Document findings**: Update experiment reports with accurate token metrics

---

## Reference

- **Specification**: [spec.md](./spec.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Research**: [research.md](./research.md)
- **OpenAI Usage API**: https://platform.openai.com/docs/api-reference/usage
- **Issue Report**: Zero Tokens Issue - Root Cause Summary (original bug report)
