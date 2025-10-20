# N-Check Verification for Token Usage Reconciliation

## Overview

The experiment framework implements a **configurable N-check verification** strategy for reconciling token usage data from the OpenAI Usage API. This ensures that reported token counts are stable before marking an experiment as "verified." The number of required stability checks is configurable (default: 2 for double-check verification).

## Problem Statement

The OpenAI Usage API has a **5-60 minute reporting delay** after API calls are made. Token data arrives incrementally and can take time to stabilize. A single reconciliation attempt might capture incomplete data, leading to:

- **Underreporting**: Early checks miss tokens still propagating through the API
- **Uncertainty**: No way to know if data is complete or still arriving
- **Research integrity issues**: Cannot cite token counts with confidence

## Solution: N-Check Verification

### Core Principle

**Data is marked "verified" only when N consecutive reconciliation attempts return identical token counts with at least 60 minutes between them.**

Where N is configurable via `RECONCILIATION_MIN_STABLE_VERIFICATIONS` (default: 2).

### Verification States

| Status | Icon | Meaning | Next Action |
|--------|------|---------|-------------|
| `data_not_available` | 🕐 | No token data from API yet | Wait 30-60 minutes, retry |
| `pending` | ⏳ | Data found, but not verified | Wait for second check |
| `verified` | ✅ | Data stable across 60+ min gap | Complete! |
| `warning` | ⚠️ | Token count decreased | Investigate API issue |

### Status Progression

```
🕐 data_not_available  →  ⏳ pending  →  ✅ verified
                                ↓
                        ⚠️ warning (if tokens decrease)
```

## Implementation Details

### Verification Criteria

A run is marked `verified` when ALL of the following conditions are met:

1. **At least N consecutive stable reconciliation attempts** (configurable via `RECONCILIATION_MIN_STABLE_VERIFICATIONS`, default: 2)
2. **Time gap ≥ 60 minutes** between each consecutive attempt (configurable via `RECONCILIATION_VERIFICATION_INTERVAL_MIN`)
3. **Identical token counts** across all N attempts:
   - `tokens_in` identical
   - `tokens_out` identical

### Anomaly Detection

The system detects and flags anomalies:

**Token Count Decrease** (⚠️ warning):
- If `current_tokens < previous_tokens`
- Indicates possible API issue or data loss
- Requires investigation before marking verified

**Data Still Arriving** (⏳ pending):
- If `current_tokens > previous_tokens`
- Normal behavior - API data still propagating
- Will continue to pending status

### Data Structure

```json
{
  "usage_api_reconciliation": {
    "verification_status": "verified",
    "verification_message": "✅ Data stable across 61 minute interval (287,761 in, 91,329 out)",
    "verified_at": "2025-10-15T10:19:18.522196+00:00",
    "attempts": [
      {
        "timestamp": "2025-10-15T09:15:00+00:00",
        "total_tokens_in": 287761,
        "total_tokens_out": 91329,
        "steps_with_tokens": 6,
        "total_steps": 6,
        "steps": [...]
      },
      {
        "timestamp": "2025-10-15T10:16:00+00:00",
        "total_tokens_in": 287761,
        "total_tokens_out": 91329,
        "steps_with_tokens": 6,
        "total_steps": 6,
        "steps": [...]
      }
    ]
  }
}
```

**Benefits of storing all attempts:**
- ✅ Full audit trail
- ✅ Can analyze convergence pattern
- ✅ Research-grade documentation
- ✅ Only ~500 bytes per run

## Configuration

### Environment Variables

```bash
# .env file
RECONCILIATION_VERIFICATION_INTERVAL_MIN=60  # Time between checks (default: 60 minutes)
RECONCILIATION_MIN_STABLE_VERIFICATIONS=2    # Number of stable checks required (default: 2)
```

### Recommended Settings

| Scenario | N Checks | Interval | Rationale |
|----------|----------|----------|-----------|
| **Development/Testing** | 1 | 0-30 min | Fast feedback, low confidence |
| **Production (Default)** | 2 | 60 min | Double-check, good confidence |
| **Research/Analysis** | 3 | 60 min | Triple-check, high confidence |
| **Publication/High-Stakes** | 4 | 60-90 min | Maximum certainty |

**Note**: Setting N=1 means data is verified after the second attempt (first + one stable check). This is acceptable for development but not recommended for production.

## Usage Examples

### List Pending Runs

```bash
./runners/reconcile_usage.sh --list
```

Output:
```
Found 1 runs pending verification:

  ⏳ chatdev/1f8c3fec-c970-45e0-b7e2-a73889e99586
    Status: pending (attempt 1)
    Age: 2.5 hours
    Message: First reconciliation attempt successful, awaiting verification
```

### Reconcile Specific Run

```bash
./runners/reconcile_usage.sh chatdev <run-id>
```

**First attempt:**
```
⏳ Reconciliation pending verification
   Input tokens:  287,761
   Output tokens: 91,329
   Attempt: 1
   Message: First reconciliation attempt successful, awaiting verification
```

**Second attempt (too soon):**
```
⏳ Reconciliation pending verification
   Input tokens:  287,761
   Output tokens: 91,329
   Attempt: 2
   Message: Data matches but interval too short (15m < 60m), wait 45m more
```

**Second attempt (after 60+ min):**
```
✅ Reconciliation VERIFIED!
   Data confirmed stable across multiple checks
   Input tokens:  287,761
   Output tokens: 91,329
   Verified at: 2025-10-15T10:19:18.522196+00:00
```

### Force Re-verification

```bash
./runners/reconcile_usage.sh chatdev <run-id> --force
```

## Best Practices

### Workflow Recommendation

1. **Immediate check** (T+0): Quick verification that experiment completed
2. **First reconciliation** (T+45min): Get initial token data
3. **Verification reconciliation** (T+90-120min): Confirm data stable

### Automated Workflow

```bash
# Run experiment
./runners/run_experiment.sh chatdev

# Wait 45 minutes
sleep 2700

# First reconciliation attempt
./runners/reconcile_usage.sh chatdev

# Wait 60 more minutes
sleep 3600

# Verification attempt
./runners/reconcile_usage.sh chatdev
```

### Scheduling with Cron

```cron
# Run first reconciliation 45 min after each hour
45 * * * * cd /path/to/baes && ./runners/reconcile_usage.sh

# Run verification reconciliation 45 min later
45 * * * * cd /path/to/baes && ./runners/reconcile_usage.sh
```

## Empirical Validation

### Proof of Concept (October 15, 2025)

**Experiment:** ChatDev run `1f8c3fec-c970-45e0-b7e2-a73889e99586`

| Check | Time | Tokens In | Tokens Out | Result |
|-------|------|-----------|------------|--------|
| First | T+37min | 287,761 | 91,329 | Complete |
| Second | T+80min | 287,761 | 91,329 | **Identical ✓** |
| Third | T+100min | 287,761 | 91,329 | **Identical ✓** |

**Conclusion:** Data stabilized by T+40min and remained unchanged for 60+ minutes.

**Verification:** ✅ Double-check strategy validated empirically

## Benefits

### For Research

- ✅ **Reproducibility**: Documented verification timestamps
- ✅ **Credibility**: Can cite exact token counts with confidence
- ✅ **Auditability**: Full history of reconciliation attempts
- ✅ **Transparency**: Clear status at every stage

### For Operations

- ✅ **Reliability**: No guessing if data is complete
- ✅ **Automation**: Unattended verification workflow
- ✅ **Error Detection**: Catches API anomalies automatically
- ✅ **Minimal Cost**: 6 extra API calls (~$0.0001)

## Trade-offs

| Aspect | Single-Check | Double-Check |
|--------|--------------|--------------|
| **Time to complete** | ~45 min | ~90-120 min |
| **Confidence level** | Assumption | Mathematical proof |
| **Research rigor** | Moderate | High |
| **Complexity** | Simple | Moderate |
| **API calls** | 6 calls/run | 12 calls/run |
| **Storage** | Minimal | ~1KB extra |

**Verdict:** For research use, benefits >>> costs

## Troubleshooting

### Run stuck in "pending"

**Symptoms:**
```
Status: pending (attempt 5)
Message: Data still arriving (+1234 in, +567 out tokens since last attempt)
```

**Diagnosis:** Token data still increasing between checks

**Solution:** Wait longer. This is normal for long experiments or API delays >60min

### Warning: Token count decreased

**Symptoms:**
```
⚠️ WARNING: ⚠️ Token count DECREASED (in: -1234, out: -567) - possible API issue!
```

**Diagnosis:** API returned fewer tokens than previous check

**Possible causes:**
1. OpenAI API issue
2. API key changed mid-experiment
3. Data corruption

**Solution:** 
1. Check OpenAI status page
2. Review API logs
3. Contact OpenAI support if persistent
4. Use `--force` to retry after issue resolved

### Data not available after hours

**Symptoms:**
```
🕐 Token data not available yet from OpenAI Usage API
```

**Diagnosis:** API hasn't received data yet

**Possible causes:**
1. Experiment used different API key
2. API key lacks `api.usage.read` scope
3. OpenAI API reporting delay >24 hours

**Solution:**
1. Verify correct API key in `.env`
2. Check API key permissions
3. Wait up to 24 hours (rare)

## Future Enhancements

Potential improvements (not yet implemented):

1. **Adaptive intervals**: Shorter intervals for small experiments
2. **Email notifications**: Alert when verification completes
3. **Slack integration**: Post verification status to channel
4. **Dashboard**: Web UI showing verification progress
5. **Confidence scoring**: Statistical confidence based on attempt history

## References

- [OpenAI Usage API Documentation](https://platform.openai.com/docs/api-reference/usage)
- [Usage API Permissions Setup](./API_KEY_PERMISSIONS_SETUP.md)
- [Usage Reconciliation Guide](./usage_reconciliation_guide.md)
