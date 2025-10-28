# OpenAI Usage API Query Analysis

## Current Query Parameters

From `src/orchestrator/usage_reconciler.py` lines 90-93:

```python
params = {
    "start_time": int(start_timestamp),
    "end_time": int(end_timestamp),
    "bucket_width": "1d",  # ← ISSUE: Daily buckets!
    "limit": 31
}
```

## The Problem

### Issue 1: Bucket Width is "1d" (Daily) ❌

**Current behavior:**
- Query for Sprint 1 (21:41:05 - 21:41:41) returns **ALL tokens from entire day (Oct 15)**
- Query for Sprint 2 (21:41:42 - 21:42:13) returns **same daily total**
- All sprints get identical values = daily aggregate

**From issue report:**
> "The reconciliation script queries the OpenAI Usage API with bucket_width='1d', which means the API returns token usage aggregated by DAY, not by minute or hour."

### Issue 2: Query Filtering

**What happens with bucket_width="1d":**

```
Sprint 1 query:
  start_time: 1697399465 (2024-10-15 21:41:05)
  end_time:   1697399501 (2024-10-15 21:41:41)
  bucket_width: "1d"
  
Response:
  {
    "data": [
      {
        "bucket_start_time": 1697328000,  // 2024-10-15 00:00:00 (midnight)
        "results": [
          {
            "input_tokens": 75000,  // ALL tokens from entire day
            "output_tokens": 25000,
            ...
          }
        ]
      }
    ]
  }
```

The API returns ONE bucket per day, containing ALL usage for that day, regardless of the specific `start_time`/`end_time` window!

## The Fix Needed

### Change bucket_width to "1m" (Minute-level)

```python
params = {
    "start_time": int(start_timestamp),
    "end_time": int(end_timestamp),
    "bucket_width": "1m",  # ✅ Minute-level granularity
    "limit": 1440  # 24 hours × 60 minutes
}
```

**With bucket_width="1m":**

```
Sprint 1 query:
  start_time: 1697399465 (2024-10-15 21:41:05)
  end_time:   1697399501 (2024-10-15 21:41:41)
  bucket_width: "1m"
  
Response:
  {
    "data": [
      {
        "bucket_start_time": 1697399460,  // 21:41:00
        "results": [{"input_tokens": 0, "output_tokens": 0}]  // Sprint 1's tokens went to 21:42:00
      },
      {
        "bucket_start_time": 1697399520,  // 21:42:00
        "results": [{"input_tokens": 4937, "output_tokens": 1589}]  // Sprint 1's tokens HERE
      }
    ]
  }
```

## Verification from Issue Report

The issue report explicitly states:

> "For sprint-level attribution, need bucket_width='1m' (minute-level granularity)"

And confirms the current code uses:
> "bucket_width='1d'" 

This is **already documented as the root cause!**

## Impact

With `bucket_width="1d"`:
- ❌ All sprints from same run get identical token counts
- ❌ Cannot distinguish between sprints
- ❌ Explains why reconciliation doesn't fix the zero-token issue

With `bucket_width="1m"`:
- ✅ Each minute bucket shows separate token counts
- ✅ Can aggregate buckets within run window
- ⚠️ Still subject to bucket misalignment (tokens attributed to next bucket)
- ✅ But run-level totals will be accurate (sum all buckets in range)

## Recommendation

1. **Immediate fix**: Change `bucket_width` from "1d" to "1m"
2. **Architectural fix**: Switch to run-level reconciliation (not per-sprint)
3. **Remove misleading data**: Don't store sprint-level token counts

The spec correctly addresses this in FR-005:
> "System MUST use bucket_width='1m' for minute-level granularity when querying Usage API"
