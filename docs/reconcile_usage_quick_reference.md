# Reconcile Usage Quick Reference

## Common Commands

### Check what needs reconciliation
```bash
./runners/reconcile_usage.sh --list
```
Shows only runs that are ready to be reconciled (>30 min old, not verified).

### See complete system status
```bash
./runners/reconcile_usage.sh --list --verbose
```
Shows ALL runs with detailed breakdown by status category.

### Reconcile all pending runs
```bash
./runners/reconcile_usage.sh
```
Automatically reconciles all runs that are ready (>30 min old).

### Reconcile specific framework
```bash
./runners/reconcile_usage.sh baes
./runners/reconcile_usage.sh chatdev
./runners/reconcile_usage.sh ghspec
```

### Reconcile specific run
```bash
./runners/reconcile_usage.sh baes 0a7e4445-ddf2-4e34-98c6-486690697fe5
```

### Get help
```bash
./runners/reconcile_usage.sh --help
```

## Status Icons Guide

| Icon | Status | Meaning |
|------|--------|---------|
| ✅ | Verified | Data confirmed stable, no action needed |
| ⏳ | Pending | Awaiting verification check |
| 🕐 | Too Recent | Waiting for 30-min threshold |
| ⚠️ | Warning | Inconsistencies detected |
| ❓ | Unknown | No reconciliation data |

## Typical Workflow

### After running experiments:

1. **Immediate check** (right after experiments complete):
   ```bash
   ./runners/reconcile_usage.sh --list --verbose
   ```
   Expected: Most runs show as "Too recent"

2. **Wait 30+ minutes** for OpenAI API data propagation

3. **Check again**:
   ```bash
   ./runners/reconcile_usage.sh --list
   ```
   Expected: Runs now show as "Pending verification"

4. **Reconcile**:
   ```bash
   ./runners/reconcile_usage.sh
   ```
   Expected: First reconciliation attempt, status → "pending"

5. **Wait 60+ minutes** for verification interval

6. **Reconcile again**:
   ```bash
   ./runners/reconcile_usage.sh
   ```
   Expected: Second check confirms data stability, status → "verified"

7. **Verify all done**:
   ```bash
   ./runners/reconcile_usage.sh --list --verbose
   ```
   Expected: All runs show as "Verified"

## Understanding Wait Times

### 30-minute minimum age
- **Why?** OpenAI Usage API has 5-60 minute data propagation delay
- **What?** Script won't attempt reconciliation until run is 30+ minutes old
- **When shown?** In "Too recent" section of verbose output

### 60-minute verification interval
- **Why?** Ensures data has fully stabilized in OpenAI's systems
- **What?** Second reconciliation must be 60+ minutes after first
- **When shown?** In verification messages

## Troubleshooting

### "No runs need reconciliation"
✅ **Normal if:**
- Runs are < 30 minutes old
- All runs already verified
- No new experiments run recently

💡 **Check:** Use `--list --verbose` to see all runs

### Run shows "0 tokens in/out"
❓ **Possible causes:**
- Experiment failed before making API calls
- No LLM interactions in that run
- Metrics not captured properly

💡 **Check:** Review run's `metrics.json` and logs

### Run stuck in "pending" status
⏳ **Possible causes:**
- Not yet 60 minutes since first reconciliation
- API data still changing (rare)

💡 **Action:** Wait longer, then reconcile again

### "Data not available" status
🕐 **Causes:**
- OpenAI API delay longer than usual
- API temporary issue

💡 **Action:** Wait and retry later (automatic retry will happen)

## Advanced Options

### Custom minimum age
```bash
./runners/reconcile_usage.sh --min-age 60
```
Wait 60 minutes instead of 30 before reconciling.

### Custom maximum age
```bash
./runners/reconcile_usage.sh --max-age 48
```
Reconcile runs up to 48 hours old (default: 24).

### Force re-verification
```bash
./runners/reconcile_usage.sh baes <run-id> --force
```
Re-verify even if already marked as verified.

## Output Interpretation

### Normal mode output
```
Found 1 runs pending verification:

  ⏳ baes/0a7e4445-ddf2-4e34-98c6-486690697fe5
    Status: pending (attempt 0)
    Age: 0.9 hours
    Message: Not yet reconciled
```

**Meaning:**
- 1 run is ready for reconciliation
- Status is "pending" (never reconciled or awaiting verification)
- "attempt 0" means never reconciled yet
- Run is 54 minutes old (0.9 hours)

### Verbose mode summary
```
📊 SUMMARY: 13 total runs
   ✅ Verified: 3
   ⏳ Pending verification: 0
   🕐 Too recent (<30 min): 9
   ❓ No reconciliation data: 1
```

**Meaning:**
- Total 13 runs in system
- 3 fully verified (no action needed)
- 0 ready for reconciliation right now
- 9 too recent (wait ~30 min)
- 1 never reconciled (may have zero tokens)

### Wait time indication
```
🕐 chatdev/aa0e24f6...
  Tokens: 237,487 in / 84,634 out
  Age: 28.9 minutes (wait 1.1 more)
```

**Meaning:**
- Run is 28.9 minutes old
- Need to wait 1.1 more minutes to reach 30-min threshold
- Will automatically be eligible for reconciliation after that

## Best Practices

1. **Use verbose mode** when you want the full picture
2. **Use normal mode** for quick "what needs attention?" checks
3. **Wait for verification** - don't force unless necessary
4. **Check after batches** to ensure all runs processed
5. **Monitor "Too recent"** section to know when to come back
6. **Investigate zero-token runs** - they might indicate issues

## Configuration

Edit `.env` file to customize:

```bash
# Minimum interval between verification attempts (minutes)
RECONCILIATION_VERIFICATION_INTERVAL_MIN=60

# Your OpenAI API key with usage.read scope
OPEN_AI_KEY_ADM=sk-proj-...
```
