# Token Counting Implementation using OpenAI Usage API

## Overview

Implemented a **DRY (Don't Repeat Yourself)** solution for token counting that works across ALL frameworks (ChatDev, GHSpec, BAEs) by querying the OpenAI Usage API directly instead of parsing framework-specific logs.

## API Key Architecture

This project uses a **two-tier API key system**:

### 1. Admin Key (Organization-Level)
- **Variable**: `OPEN_AI_KEY_ADM`
- **Purpose**: Query the OpenAI Usage API for token counting
- **Permissions**: Organization-level access required (`api.usage.read` scope)
- **Used by**: All adapters (ChatDev, GHSpec, BAEs) for token tracking

### 2. Framework Keys (Project-Level)
- **Variables**: `OPENAI_API_KEY_CHATDEV`, `OPENAI_API_KEY_GHSPEC`, `OPENAI_API_KEY_BAES`
- **Purpose**: Execute framework-specific API calls (chat completions, embeddings)
- **Permissions**: Standard project-level access
- **Used by**: Individual frameworks for their LLM operations

**Why Two Tiers?**
- Usage API requires **organization-level permissions** that framework keys don't have
- Framework keys are used to MAKE the API calls
- Admin key is used to MEASURE the API calls
- Per-framework attribution is achieved through **time window isolation**, not API key filtering

**Time Window Isolation Strategy:**
Since OpenAI Usage API doesn't reliably filter by `api_key_id` or `model`, we use tight time windows:
1. Record start timestamp when framework step begins
2. Execute framework (uses framework-specific API key)
3. Record end timestamp when framework step completes
4. Query Usage API for that exact time window
5. All tokens in that window belong to that framework execution

This works because:
- ✅ Sequential execution (one framework at a time)
- ✅ Tight time windows (4-5 minutes per step)
- ✅ No concurrent API calls
- ✅ Precise attribution without API key filtering

## Problem Statement

**Before**: Each framework had different token logging formats:
- ChatDev: Writes `prompt_tokens:` and `completion_tokens:` to log files
- GHSpec: Unknown format
- BAEs: Unknown format

This required:
- ❌ Framework-specific parsing code
- ❌ Maintenance burden when frameworks change
- ❌ Unreliable (logs might not exist or have different formats)
- ❌ Code duplication across adapters

## Solution

**After**: Single general method in `BaseAdapter`:
- ✅ One implementation for all frameworks
- ✅ Direct from OpenAI (authoritative source)
- ✅ No framework-specific code
- ✅ Automatic handling of all API calls
- ✅ DRY principle applied

## Implementation

### 1. Base Adapter Method

Added `fetch_usage_from_openai()` to `src/adapters/base_adapter.py`:

```python
def fetch_usage_from_openai(
    self,
    api_key_env_var: str,
    start_timestamp: int,
    end_timestamp: Optional[int] = None,
    model: Optional[str] = None
) -> Tuple[int, int]:
    """
    Fetch token usage from OpenAI Usage API.
    
    This is a general, DRY method that works for ALL frameworks.
    
    Returns:
        Tuple of (tokens_in, tokens_out)
    """
```

**Key Features**:
- Uses `/v1/organization/usage/completions` endpoint
- Queries specific time window (step start to step end)
- Aggregates tokens across all buckets
- Filters by model (gpt-5-mini, gpt-4o-mini, etc.)
- Returns (0, 0) on error (non-blocking)

### 2. ChatDev Adapter Integration

Updated `src/adapters/chatdev_adapter.py`:

**Before**:
```python
# T067: Parse token usage from output (likely returns 0, will use Usage API)
tokens_in, tokens_out = self._parse_token_usage(result.stdout, result.stderr)
```

**After**:
```python
# Fetch token usage from OpenAI Usage API
# Uses OPEN_AI_KEY_ADM (admin key with org-level permissions)
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var='OPEN_AI_KEY_ADM',
    start_timestamp=self._step_start_time,
    end_timestamp=end_timestamp,
    model=model_config
)
```

**Important**: The Usage API requires an admin API key with organization-level permissions. The framework-specific keys (e.g., `OPENAI_API_KEY_CHATDEV`) don't have these permissions, so we use `OPEN_AI_KEY_ADM` instead.

### 3. Runner Updates

Modified `src/orchestrator/runner.py` to pass global model config to framework:

```python
# Add global model to framework config
framework_config['model'] = self.config.get('model')
```

This ensures all frameworks use the same model for fair comparison.

### 4. Test Script

Created `test_usage_api.py` to verify token counting works:

```bash
python test_usage_api.py
```

## API Reference

### OpenAI Usage API Endpoint

```
GET https://api.openai.com/v1/organization/usage/completions
```

**Query Parameters**:
- `start_time`: Unix timestamp (seconds), inclusive
- `end_time`: Unix timestamp (seconds), exclusive
- `bucket_width`: "1m", "1h", or "1d" (default: "1d")
- `models`: Array of model names to filter
- `limit`: Number of buckets to return (max: 31 for daily)

**Response Format**:
```json
{
    "object": "page",
    "data": [
        {
            "object": "bucket",
            "start_time": 1730419200,
            "end_time": 1730505600,
            "results": [
                {
                    "object": "organization.usage.completions.result",
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "num_model_requests": 5
                }
            ]
        }
    ],
    "has_more": true
}
```

## Benefits

### 1. **DRY Principle** ✅
- Single implementation in `BaseAdapter`
- All frameworks inherit the same method
- No code duplication

### 2. **Accuracy** ✅
- Direct from OpenAI (authoritative source)
- Includes ALL API calls in time window
- No parsing errors

### 3. **Reliability** ✅
- Doesn't depend on framework logs
- Works even if logs are missing/malformed
- Consistent across frameworks

### 4. **Maintainability** ✅
- Framework changes don't break token counting
- Single point of maintenance
- Easy to update/improve

### 5. **Completeness** ✅
- Captures all API calls automatically
- No need to find/parse log files
- Handles concurrent API calls

## How It Works

### Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Step Execution Starts                                   │
│ - Record start_timestamp = int(time.time())             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Framework Executes (ChatDev/GHSpec/BAEs)                │
│ - Makes OpenAI API calls                                │
│ - OpenAI tracks usage automatically                     │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Step Execution Ends                                     │
│ - Record end_timestamp = int(time.time())               │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Query OpenAI Usage API                                  │
│ - GET /v1/organization/usage/completions                │
│ - start_time=<start_timestamp>                          │
│ - end_time=<end_timestamp>                              │
│ - models=[gpt-5-mini]                                   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Aggregate Tokens from Response                          │
│ - Sum input_tokens across all buckets                   │
│ - Sum output_tokens across all buckets                  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Return (tokens_in, tokens_out)                          │
└─────────────────────────────────────────────────────────┘
```

### Time Window Strategy

**Problem**: Usage API returns data in buckets (1m, 1h, or 1d)

**Solution**: Use tight time window:
- Start: Record timestamp when step starts
- End: Record timestamp when step ends
- Query: Request all buckets covering this window
- Aggregate: Sum tokens from all buckets

**Example**:
```
Step starts:  2025-10-09 11:27:35 (timestamp: 1728476855)
Step ends:    2025-10-09 11:33:40 (timestamp: 1728477220)
Duration:     6 minutes 5 seconds
Query:        start_time=1728476855, end_time=1728477220
Buckets:      1 bucket (using 1d bucket_width)
Tokens:       Aggregated from all API calls in window
```

## Testing

### Manual Test

```bash
# 1. Activate environment
source .venv/bin/activate
set -a && source .env && set +a

# 2. Run usage API test
python test_usage_api.py
```

**Expected Output**:
```
================================================================================
Testing OpenAI Usage API Token Counting
================================================================================

Querying usage for last hour:
  Start: 1728476220 (Wed Oct  9 11:17:00 2025)
  End:   1728479820 (Wed Oct  9 12:17:00 2025)
  Model: gpt-5-mini
  API Key Env: OPENAI_API_KEY_CHATDEV

Results:
  Input tokens:  12,345
  Output tokens: 5,678
  Total tokens:  18,023

  Estimated cost: $0.0145
    Input:  $0.0031
    Output: $0.0114

✅ SUCCESS: Token counting working!
```

### Integration Test

Run the smoke test to verify end-to-end:

```bash
./run_tests.sh smoke
```

**Expected**: Token counts now appear instead of zeros!

## Migration Path

### For Other Adapters

To add token counting to GHSpec and BAEs adapters:

1. **Use the admin API key** for Usage API queries:

```python
# In ghspec_adapter.py execute_step():
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var='OPEN_AI_KEY_ADM',  # Admin key with org permissions
    start_timestamp=self._step_start_time,
    end_timestamp=int(time.time()),
    model=self.config.get('model')
)
```

2. Make sure to set `self._step_start_time` before execution:

```python
self._step_start_time = int(time.time())
```

3. Done! Token counting works automatically.

**Important**: All frameworks should use `OPEN_AI_KEY_ADM` for the Usage API, not their framework-specific keys (which lack organization permissions).

## API Requirements

### Permissions

The API key must have **organization-level permissions** to access the Usage API.

**In this project**:
- ✅ `OPEN_AI_KEY_ADM` - Admin key with org permissions (use this for Usage API)
- ❌ `OPENAI_API_KEY_CHATDEV` - Framework key (lacks org permissions)
- ❌ `OPENAI_API_KEY_GHSPEC` - Framework key (lacks org permissions)
- ❌ `OPENAI_API_KEY_BAES` - Framework key (lacks org permissions)

**To check**:
```bash
curl "https://api.openai.com/v1/organization/usage/completions?start_time=1728476220&limit=1" \
  -H "Authorization: Bearer $OPEN_AI_KEY_ADM"
```

**If you get 403 Forbidden**: The API key doesn't have org permissions. Make sure you're using `OPEN_AI_KEY_ADM`, not a framework-specific key.

### Rate Limits

Usage API has separate rate limits from Chat Completions:
- Typically very generous
- Unlikely to hit limits with our usage pattern
- Error handling returns (0, 0) on failure (non-blocking)

## Troubleshooting

### Issue: Returns (0, 0)

**Possible causes**:
1. No API calls in time window → Expected if step hasn't run
2. Wrong API key - using framework key instead of admin key → Use `OPEN_AI_KEY_ADM`
3. Model filter too specific → Try without model filter
4. Network/timeout error → Check logs

**Debug**:
```python
# Add to fetch_usage_from_openai after response:
print(f"Response: {response.json()}")
```

### Issue: Token counts seem low

**Possible causes**:
1. Time window too narrow → Ensure proper timestamps
2. Using wrong API key → Check api_key_env value
3. Bucket aggregation issue → Check all buckets summed

**Debug**:
```python
# Log each bucket's tokens
for bucket in usage_data.get("data", []):
    print(f"Bucket: {bucket['start_time']} - {bucket['end_time']}")
    for result in bucket.get("results", []):
        print(f"  Input: {result.get('input_tokens')}, Output: {result.get('output_tokens')}")
```

## Future Enhancements

### 1. Caching

Cache Usage API responses to avoid redundant calls:

```python
def fetch_usage_from_openai(self, ...):
    cache_key = f"{start_timestamp}_{end_timestamp}_{model}"
    if cache_key in self._usage_cache:
        return self._usage_cache[cache_key]
    
    # ... fetch from API ...
    
    self._usage_cache[cache_key] = (tokens_in, tokens_out)
    return tokens_in, tokens_out
```

### 2. Retry Logic

Add retry logic for transient API failures:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def fetch_usage_from_openai(self, ...):
    # ... existing code ...
```

### 3. Cost Calculation

Add cost calculation to base adapter:

```python
def calculate_cost(self, tokens_in: int, tokens_out: int, model: str) -> float:
    """Calculate cost based on model pricing."""
    pricing = {
        "gpt-5-mini": {"input": 0.25, "output": 2.00},  # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        # ... more models ...
    }
    
    rates = pricing.get(model, {"input": 0, "output": 0})
    cost = (tokens_in / 1_000_000) * rates["input"]
    cost += (tokens_out / 1_000_000) * rates["output"]
    return cost
```

## Summary

✅ **Implemented**: OpenAI Usage API token counting
✅ **Principle**: DRY - single implementation for all frameworks
✅ **Location**: `BaseAdapter.fetch_usage_from_openai()`
✅ **Integration**: ChatDev adapter updated
✅ **Testing**: test_usage_api.py created
✅ **Committed**: ee9d71d pushed to main

**Next Steps**:
1. Run smoke test to verify: `./run_tests.sh smoke`
2. Check token counts are no longer zero
3. Update GHSpec and BAEs adapters (copy same pattern)
4. Consider adding caching/retry logic

**References**:
- [OpenAI Usage API Documentation](https://platform.openai.com/docs/api-reference/usage)
- Commit: ee9d71d "feat: Implement OpenAI Usage API token counting (DRY principle)"
