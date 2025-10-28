# API Contract: UsageReconciler

**Component**: `src/orchestrator/usage_reconciler.py`  
**Type**: Internal Python API  
**Consumer**: Reconciliation scripts, orchestrator

---

## Class: UsageReconciler

### Method: reconcile_run

**Purpose**: Reconcile tokens for a single run using OpenAI Usage API

**Signature**:
```python
def reconcile_run(
    self,
    run_id: str,
    framework: str,
    min_interval_minutes: int = DEFAULT_VERIFICATION_INTERVAL_MIN,
    min_stable_verifications: int = DEFAULT_MIN_STABLE_VERIFICATIONS
) -> bool:
    """
    Reconcile token usage for a completed run.
    
    Args:
        run_id: Unique run identifier
        framework: Framework name (baes, chatdev, ghspec)
        min_interval_minutes: Minimum minutes between verification attempts
        min_stable_verifications: Consecutive stable checks required
        
    Returns:
        bool: True if verification reached "verified" status, False otherwise
        
    Raises:
        ValueError: If run_id or framework is invalid
        FileNotFoundError: If metrics.json does not exist
        KeyError: If required environment variables missing (API keys)
        RuntimeError: If OpenAI API request fails with non-retryable error
    """
```

**Behavior**:
1. Load existing `metrics.json` for the run
2. Check if run is too old (> MAX_AGE_HOURS) → skip
3. Check if enough time has passed since last attempt (>= min_interval_minutes)
4. Query OpenAI Usage API with run-level time window
5. Aggregate all buckets in response
6. Compare with previous attempt (if exists)
7. Update `usage_api_reconciliation` section in `metrics.json`
8. Return verification status

**Contract**:
- MUST use `bucket_width="1m"` for minute-level granularity
- MUST filter by `api_key_ids` parameter using framework-specific key ID
- MUST aggregate ALL buckets returned (no filtering)
- MUST NOT modify `steps[]` array (no token fields)
- MUST update `aggregate_metrics` with reconciled totals
- MUST fail immediately on missing API key or invalid response (no silent fallbacks)

---

### Method: _fetch_usage_from_openai (Private)

**Purpose**: Query OpenAI Usage API for token counts

**Signature**:
```python
def _fetch_usage_from_openai(
    self,
    start_timestamp: int,
    end_timestamp: int,
    framework: str
) -> tuple[int, int, int, int]:
    """
    Fetch usage data from OpenAI Usage API.
    
    Args:
        start_timestamp: Unix timestamp (seconds) for query start
        end_timestamp: Unix timestamp (seconds) for query end
        framework: Framework name (for API key lookup)
        
    Returns:
        tuple: (input_tokens, output_tokens, api_calls, cached_tokens)
        
    Raises:
        KeyError: If OPEN_AI_KEY_ADM or framework API key ID not in environment
        requests.RequestException: If API request fails
        ValueError: If API response is malformed
    """
```

**Behavior**:
1. Get admin API key from `OPEN_AI_KEY_ADM` (for authorization)
2. Get framework API key ID from `OPENAI_API_KEY_{FRAMEWORK}_ID` (for filtering)
3. Construct query parameters:
   ```python
   {
       "start_time": start_timestamp,
       "end_time": end_timestamp,
       "bucket_width": "1m",
       "api_key_ids": [framework_api_key_id],
       "limit": 1440
   }
   ```
4. Make GET request to `https://api.openai.com/v1/organization/usage/completions`
5. Parse response and aggregate all buckets:
   ```python
   total_input = sum(bucket["input_tokens"] for bucket in response["data"])
   total_output = sum(bucket["output_tokens"] for bucket in response["data"])
   total_calls = sum(bucket["num_model_requests"] for bucket in response["data"])
   total_cached = sum(bucket.get("input_cached_tokens", 0) for bucket in response["data"])
   ```
6. Return tuple

**Contract**:
- MUST use admin key for authorization (`OPEN_AI_KEY_ADM`)
- MUST filter by framework-specific key ID (`api_key_ids` parameter)
- MUST use `bucket_width="1m"` (minute granularity)
- MUST aggregate ALL buckets (no partial sums)
- MUST handle empty response (return zeros if `data` array is empty)
- MUST raise on API errors (status code != 200)

---

## Environment Variables Contract

### Required

| Variable | Format | Purpose | Validation |
|----------|--------|---------|------------|
| `OPEN_AI_KEY_ADM` | `sk-proj-...` | Admin key with `api.usage.read` permission | Must exist, fail if missing |
| `OPENAI_API_KEY_{FRAMEWORK}_ID` | `key_XXXXXXXXXXXX` | API key ID for filtering (per framework) | Must exist, fail if missing |

### Optional

| Variable | Format | Default | Purpose |
|----------|--------|---------|---------|
| `RECONCILIATION_VERIFICATION_INTERVAL_MIN` | integer | `0` | Minutes between verification attempts |
| `RECONCILIATION_MIN_STABLE_VERIFICATIONS` | integer | `2` | Consecutive stable checks required |

---

## Error Handling Contract

**Fail-Fast Behavior** (per Constitution XIII):

```python
# Missing API key → FAIL immediately
if not os.getenv('OPEN_AI_KEY_ADM'):
    raise KeyError("OPEN_AI_KEY_ADM environment variable required")

# Invalid API response → FAIL immediately
if response.status_code != 200:
    raise RuntimeError(f"OpenAI API returned {response.status_code}: {response.text}")

# Token fields in steps → FAIL immediately
for step in metrics['steps']:
    if 'tokens_in' in step or 'tokens_out' in step:
        raise ValueError(f"Step {step['step']} contains forbidden token fields")
```

**No Silent Fallbacks**:
- Do NOT default to zero tokens if API fails
- Do NOT skip verification if API key missing
- Do NOT continue if response is malformed
- Do NOT ignore schema violations

---

## Example Usage

```python
from src.orchestrator.usage_reconciler import UsageReconciler
from pathlib import Path

reconciler = UsageReconciler(runs_dir=Path("runs"))

# Reconcile single run
success = reconciler.reconcile_run(
    run_id="run-abc-123",
    framework="baes",
    min_interval_minutes=30,
    min_stable_verifications=2
)

if success:
    print("✅ Run verified")
else:
    print("⏳ Verification pending (data not yet available or unstable)")
```

---

## Breaking Changes from Previous Version

1. **REMOVED**: `_reconcile_steps()` method (no longer needed)
2. **CHANGED**: `bucket_width` parameter from `"1d"` to `"1m"`
3. **ADDED**: `api_key_ids` parameter to OpenAI API query
4. **CHANGED**: Return value from `_fetch_usage_from_openai()` now expects framework parameter
5. **REMOVED**: Token fields from `metrics.json` → `steps[]` array

---

## Version

**Contract Version**: 2.0.0  
**Breaking**: Yes (schema change, method removal)  
**Compatible With**: metrics.json schema v2.0 (post-fix)
