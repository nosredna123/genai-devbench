# Usage API Reconciliation - Quick Reference

## Overview

The OpenAI Usage API has a reporting delay of **5-60 minutes**. To handle this:

1. **Run completes** → `metrics.json` saved with `tokens=0`
2. **Wait 30-60 minutes** → Usage API data becomes available  
3. **Run reconciliation** → `metrics.json` updated with actual tokens

## Quick Start

### 1. Run an experiment

```bash
./runners/run_experiment.sh chatdev
# Completes immediately, metrics.json has tokens=0
```

### 2. Wait for Usage API (30-60 minutes)

```bash
# Go get coffee ☕
```

### 3. Reconcile token counts

```bash
# Reconcile all pending runs
./runners/reconcile_usage.sh

# Or reconcile specific framework
./runners/reconcile_usage.sh chatdev

# Or reconcile specific run
./runners/reconcile_usage.sh chatdev run-abc123
```

### 4. Verify reconciliation

```bash
# Check metrics file
cat runs/chatdev/run-abc123/metrics.json | jq '.aggregate_metrics.TOK_IN'
# Should show actual token count (not 0)

# Check reconciliation status
cat runs/chatdev/run-abc123/metrics.json | jq '.usage_api_reconciliation'
```

## Commands

### List pending runs

```bash
./runners/reconcile_usage.sh --list
```

Output:
```
Found 3 runs pending reconciliation:

  chatdev/test_run_123
    Age: 1.2 hours
    File: runs/chatdev/test_run_123/metrics.json

  chatdev/test_run_456
    Age: 0.8 hours
    File: runs/chatdev/test_run_456/metrics.json
```

### Reconcile all pending

```bash
./runners/reconcile_usage.sh
```

Output:
```
Processed 3 runs:
  ✅ Success: 3
  ❌ Errors:  0

  chatdev/test_run_123
    Input:  84,604 tokens
    Output: 23,275 tokens
    Steps:  1/1 updated
```

### Reconcile with custom timing

```bash
# Wait only 15 minutes before reconciling
./runners/reconcile_usage.sh --min-age 15

# Process runs up to 48 hours old
./runners/reconcile_usage.sh --max-age 48
```

### Force re-reconciliation

```bash
# Re-reconcile even if already done
./runners/reconcile_usage.sh chatdev run-abc123 --force
```

## Automated Reconciliation

### Cron Job (Recommended)

Add to your crontab:

```cron
# Reconcile every hour
0 * * * * cd /path/to/genai-devbench && ./runners/reconcile_usage.sh >> logs/reconciliation.log 2>&1
```

### GitHub Actions (Optional)

```yaml
name: Reconcile Usage
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:      # Manual trigger

jobs:
  reconcile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Reconcile usage
        env:
          OPENAI_API_KEY_USAGE_TRACKING: ${{ secrets.OPENAI_API_KEY_USAGE_TRACKING }}
        run: ./runners/reconcile_usage.sh
```

## Metrics File Schema

### Before Reconciliation

```json
{
  "run_id": "test_run_123",
  "steps": [
    {
      "step_number": 1,
      "tokens_in": 0,
      "tokens_out": 0,
      "start_timestamp": 1760015386,
      "end_timestamp": 1760015878
    }
  ],
  "aggregate_metrics": {
    "TOK_IN": 0,
    "TOK_OUT": 0,
    "AEI": 0.0
  }
}
```

### After Reconciliation

```json
{
  "run_id": "test_run_123",
  "steps": [
    {
      "step_number": 1,
      "tokens_in": 84604,
      "tokens_out": 23275,
      "start_timestamp": 1760015386,
      "end_timestamp": 1760015878
    }
  ],
  "aggregate_metrics": {
    "TOK_IN": 84604,
    "TOK_OUT": 23275,
    "AEI": 0.0826
  },
  "usage_api_reconciliation": {
    "reconciled_at": "2025-10-09T14:30:00Z",
    "status": "success",
    "total_tokens_in": 84604,
    "total_tokens_out": 23275,
    "steps_with_tokens": 1,
    "total_steps": 1,
    "steps_updated": [
      {
        "step": 1,
        "status": "success",
        "tokens_in": 84604,
        "tokens_out": 23275
      }
    ]
  }
}
```

## Troubleshooting

### No runs listed

**Reasons**:
- Runs are too recent (< 30 minutes old)
- Runs already reconciled
- Runs already have token data
- Runs are too old (> 24 hours)

**Solutions**:
```bash
# Check run age
ls -lt runs/chatdev/

# Try different age filters
./runners/reconcile_usage.sh --min-age 15
./runners/reconcile_usage.sh --max-age 48
```

### Reconciliation returns 0 tokens

**Reasons**:
- Usage API delay longer than expected
- API key lacks `api.usage.read` scope
- Time window doesn't match actual API calls

**Solutions**:
```bash
# Wait longer and retry
sleep 1800  # 30 more minutes
./runners/reconcile_usage.sh chatdev run-abc123

# Check API key permissions
# Go to: https://platform.openai.com/settings/organization/api-keys
# Verify: api.usage.read scope is enabled

# Force re-reconcile
./runners/reconcile_usage.sh chatdev run-abc123 --force
```

### Permission denied error

```bash
# Make script executable
chmod +x runners/reconcile_usage.sh
```

### Import errors

```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Best Practices

### 1. Always wait before reconciling

```bash
# ❌ Don't reconcile immediately after run
./runners/run_experiment.sh chatdev
./runners/reconcile_usage.sh  # Will get 0 tokens!

# ✅ Wait 30-60 minutes
./runners/run_experiment.sh chatdev
# ... wait ...
./runners/reconcile_usage.sh
```

### 2. Run reconciliation before analysis

```bash
# Ensure all runs have token data
./runners/reconcile_usage.sh

# Then run analysis
./runners/analyze_results.sh
```

### 3. Check reconciliation status

```bash
# Before analysis, verify runs are reconciled
./runners/reconcile_usage.sh --list

# Should show: "No runs need reconciliation"
```

### 4. Use cron for automation

```cron
# Reconcile every hour (recommended)
0 * * * * cd /path/to/genai-devbench && ./runners/reconcile_usage.sh
```

## Architecture

```
┌─────────────────────┐
│   Run Experiment    │
│  ./run_experiment   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  metrics.json       │
│  (tokens = 0)       │
│  + timestamps       │
└──────────┬──────────┘
           │
           │ ⏰ Wait 30-60 minutes
           │    (Usage API delay)
           │
           ▼
┌─────────────────────┐
│  reconcile_usage.sh │
├─────────────────────┤
│ 1. Read metrics     │
│ 2. Get timestamps   │
│ 3. Query Usage API  │
│ 4. Update tokens    │
│ 5. Save metrics     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  metrics.json       │
│  (tokens = actual)  │
│  + reconciliation   │
└─────────────────────┘
```

## Related Documentation

- **Design**: `docs/async_usage_api_design.md` - Full design rationale
- **Token Counting**: `docs/token_counting_implementation.md` - Implementation details
- **API Keys**: `docs/API_KEY_PERMISSIONS_SETUP.md` - Required permissions
- **Metrics**: `docs/metrics.md` - Metrics reference

## FAQ

**Q: Why are tokens 0 after run completes?**  
A: OpenAI Usage API has 5-60 minute reporting delay. Run reconciliation after waiting.

**Q: How long should I wait before reconciling?**  
A: Minimum 30 minutes, maximum 24 hours. Default is 30 minutes.

**Q: Can I reconcile multiple times?**  
A: Yes. Already-reconciled runs are skipped unless you use `--force`.

**Q: Will reconciliation overwrite my metrics?**  
A: Yes, but only the token counts. All other metrics remain unchanged.

**Q: What if reconciliation fails?**  
A: Metrics stay at 0. Check logs and retry later. Token data is not critical for run completion.

**Q: Can I use framework-specific API keys?**  
A: No. Reconciliation requires `OPENAI_API_KEY_USAGE_TRACKING` with `api.usage.read` scope.

**Q: How does framework attribution work?**  
A: Time window isolation. Each step's start/end timestamps define the query window.

## Support

For issues or questions:
1. Check `logs/reconciliation.log` for errors
2. Verify API key has `api.usage.read` scope
3. Ensure runs are 30-60 minutes old
4. See troubleshooting section above
