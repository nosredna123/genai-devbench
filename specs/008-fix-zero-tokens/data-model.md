# Data Model: Fix Zero Tokens Issue

**Feature**: 008-fix-zero-tokens  
**Date**: 2025-10-27  
**Status**: Complete

## Overview

This document defines the data model changes for run-level token reconciliation. The primary change is removing token-related fields from the `steps` array in `metrics.json`, keeping them only at the `aggregate_metrics` level.

---

## Entity: Metrics

**Description**: Performance and cost metrics for a single framework run

**Storage**: JSON file at `runs/{framework}/{run_id}/metrics.json`

**Lifecycle**: 
1. Created during run execution with initial values
2. Updated post-run by reconciliation process
3. Immutable after verification reaches "verified" status

### Schema (Post-Fix)

```json
{
  "run_id": "string (UUID)",
  "framework": "string (baes|chatdev|ghspec)",
  "start_timestamp": "integer (Unix seconds)",
  "end_timestamp": "integer (Unix seconds)",
  "aggregate_metrics": {
    "TOK_IN": "integer (total input tokens)",
    "TOK_OUT": "integer (total output tokens)",
    "API_CALLS": "integer (total API calls)",
    "CACHED_TOKENS": "integer (total cached tokens)",
    "COST_USD": "float (total cost in USD)",
    "DUR": "float (total duration in seconds)",
    "UTT": "integer (total utterances/steps)",
    "HIT": "integer (total HITL interventions)"
  },
  "steps": [
    {
      "step": "integer (step number, 1-indexed)",
      "duration_seconds": "float",
      "start_timestamp": "integer (Unix seconds)",
      "end_timestamp": "integer (Unix seconds)",
      "hitl_count": "integer",
      "retry_count": "integer",
      "success": "boolean"
    }
  ],
  "usage_api_reconciliation": {
    "verification_status": "string (pending|verified|failed|data_not_available)",
    "attempts": [
      {
        "timestamp": "integer (Unix seconds)",
        "total_tokens_in": "integer",
        "total_tokens_out": "integer",
        "total_api_calls": "integer",
        "total_cached_tokens": "integer",
        "status": "string (pending|verified|failed)"
      }
    ],
    "last_attempt_timestamp": "integer (Unix seconds)",
    "verified_at": "integer|null (Unix seconds)"
  }
}
```

### Field Changes

**REMOVED from steps array** (BREAKING CHANGE):
- `tokens_in`: No longer stored at step level
- `tokens_out`: No longer stored at step level
- `api_calls`: No longer stored at step level
- `cached_tokens`: No longer stored at step level

**Rationale**: OpenAI Usage API bucket-based design makes per-step attribution unreliable. Removing these fields prevents false confidence in granular analysis.

**KEPT in steps array**:
- `step`: Step number (required for ordering)
- `duration_seconds`: Timing metric (synchronous, reliable)
- `start_timestamp` / `end_timestamp`: Time boundaries (for debugging)
- `hitl_count`: Human intervention count (synchronous, reliable)
- `retry_count`: Retry attempts (synchronous, reliable)
- `success`: Step completion status (synchronous, reliable)

**KEPT in aggregate_metrics** (unchanged):
- `TOK_IN`, `TOK_OUT`, `API_CALLS`, `CACHED_TOKENS`: Run-level totals (reconciled from Usage API)
- `COST_USD`: Computed from run-level token totals
- `DUR`, `UTT`, `HIT`: Aggregate timing and interaction metrics

---

## Entity: ReconciliationAttempt

**Description**: Single verification attempt for token reconciliation

**Storage**: Embedded in `metrics.json` → `usage_api_reconciliation.attempts[]`

**Lifecycle**: 
1. Created on first reconciliation attempt (typically 30+ minutes after run)
2. New attempts added until verification reaches stable state
3. Maximum attempts capped by age limit (default 24 hours)

### Fields

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `timestamp` | integer | When attempt occurred (Unix seconds) | Required, > run.end_timestamp |
| `total_tokens_in` | integer | Input tokens from Usage API | >= 0 |
| `total_tokens_out` | integer | Output tokens from Usage API | >= 0 |
| `total_api_calls` | integer | API calls from Usage API | >= 0 |
| `total_cached_tokens` | integer | Cached tokens from Usage API | >= 0 |
| `status` | string | Attempt status | Enum: pending, verified, failed, data_not_available |

### State Transitions

```
data_not_available → pending → verified
                   ↓
                 failed
```

**data_not_available**: Usage API returned no data (too soon after run)
**pending**: Data found, but not yet stable across N checks
**verified**: N consecutive checks with identical totals
**failed**: API error or timeout

---

## Entity: Run (Metadata Only)

**Description**: Metadata about a framework execution (not part of metrics.json)

**Storage**: Managed by `ManifestManager` (separate from metrics)

**Relationship**: One Run → One Metrics file

### Attributes (for reference)

- `run_id`: Unique identifier (UUID)
- `framework`: Framework name (baes, chatdev, ghspec)
- `start_timestamp`: Run start time (Unix seconds)
- `end_timestamp`: Run end time (Unix seconds)
- `verification_status`: Reconciliation status (from metrics.json)

---

## Validation Rules

### Metrics Validation

1. **Run-level token totals** (aggregate_metrics):
   - `TOK_IN >= 0`, `TOK_OUT >= 0`, `API_CALLS >= 0`, `CACHED_TOKENS >= 0`
   - `COST_USD >= 0`
   - All values are integers (except COST_USD which is float)

2. **Step-level data** (steps array):
   - NO token fields allowed (`tokens_in`, `tokens_out`, `api_calls`, `cached_tokens` must be absent)
   - `duration_seconds >= 0`
   - `start_timestamp < end_timestamp`
   - `hitl_count >= 0`, `retry_count >= 0`
   - `success` is boolean

3. **Reconciliation attempts**:
   - At least one attempt exists if verification_status != "pending"
   - Attempts ordered by timestamp (ascending)
   - Last attempt status matches overall verification_status

### Fail-Fast Behavior

Per Constitution Principle XIII (Fail-Fast Philosophy):

- **Missing required fields**: Raise `KeyError` immediately (no defaults)
- **Invalid field types**: Raise `TypeError` immediately (no coercion)
- **Negative token counts**: Raise `ValueError` immediately (data corruption)
- **Token fields in steps array**: Raise `ValueError` immediately (schema violation)

---

## API Key Configuration

### Environment Variables (New)

Required for API key filtering (FR-010):

```bash
# Execution keys (existing)
OPENAI_API_KEY_BAES="sk-proj-..."
OPENAI_API_KEY_CHATDEV="sk-proj-..."
OPENAI_API_KEY_GHSPEC="sk-proj-..."

# Admin key for Usage API queries (existing)
OPEN_AI_KEY_ADM="sk-proj-..."

# API Key IDs for filtering (NEW)
OPENAI_API_KEY_BAES_ID="key_XXXXXXXXXXXX"
OPENAI_API_KEY_CHATDEV_ID="key_XXXXXXXXXXXX"
OPENAI_API_KEY_GHSPEC_ID="key_XXXXXXXXXXXX"
```

### Validation (FR-011)

At adapter initialization:
1. Verify execution key exists (`OPENAI_API_KEY_{FRAMEWORK}`)
2. Verify key ID exists (`OPENAI_API_KEY_{FRAMEWORK}_ID`)
3. Verify key ID format matches `key_[A-Za-z0-9]{12,}`
4. Fail immediately if validation fails (no fallback)

---

## Example: Metrics.json (Before vs After)

### Before (Buggy Sprint-Level Tokens)

```json
{
  "run_id": "abc-123",
  "framework": "baes",
  "aggregate_metrics": {
    "TOK_IN": 25202,
    "TOK_OUT": 19812,
    "API_CALLS": 15,
    "CACHED_TOKENS": 1280,
    "COST_USD": 0.42
  },
  "steps": [
    {
      "step": 1,
      "tokens_in": 0,        // ❌ Zero (bug)
      "tokens_out": 0,       // ❌ Zero (bug)
      "api_calls": 0,        // ❌ Zero (bug)
      "duration_seconds": 35.2
    },
    {
      "step": 2,
      "tokens_in": 9874,     // ✅ Has data
      "tokens_out": 8234,
      "api_calls": 5,
      "duration_seconds": 38.1
    },
    {
      "step": 3,
      "tokens_in": 0,        // ❌ Zero (bug)
      "tokens_out": 0,
      "duration_seconds": 42.7
    }
  ]
}
```

### After (Clean Run-Level Tokens)

```json
{
  "run_id": "abc-123",
  "framework": "baes",
  "start_timestamp": 1761523200,
  "end_timestamp": 1761523530,
  "aggregate_metrics": {
    "TOK_IN": 25202,       // ✅ Accurate (from Usage API)
    "TOK_OUT": 19812,
    "API_CALLS": 15,
    "CACHED_TOKENS": 1280,
    "COST_USD": 0.42,
    "DUR": 330.0,
    "UTT": 5,
    "HIT": 0
  },
  "steps": [
    {
      "step": 1,
      "duration_seconds": 35.2,
      "start_timestamp": 1761523200,
      "end_timestamp": 1761523235,
      "hitl_count": 0,
      "retry_count": 0,
      "success": true
      // ✅ No token fields
    },
    {
      "step": 2,
      "duration_seconds": 38.1,
      "start_timestamp": 1761523235,
      "end_timestamp": 1761523273,
      "hitl_count": 0,
      "retry_count": 0,
      "success": true
      // ✅ No token fields
    }
  ],
  "usage_api_reconciliation": {
    "verification_status": "verified",
    "attempts": [
      {
        "timestamp": 1761525000,
        "total_tokens_in": 25202,
        "total_tokens_out": 19812,
        "total_api_calls": 15,
        "total_cached_tokens": 1280,
        "status": "pending"
      },
      {
        "timestamp": 1761526800,
        "total_tokens_in": 25202,
        "total_tokens_out": 19812,
        "total_api_calls": 15,
        "total_cached_tokens": 1280,
        "status": "verified"
      }
    ],
    "last_attempt_timestamp": 1761526800,
    "verified_at": 1761526800
  }
}
```

---

## Migration Strategy

**No migration needed** per Constitution Principle XII:
- Old experiments remain unchanged (independent git repositories)
- New experiments use clean schema from day one
- No backward compatibility code required

---

## Summary

**Key Changes**:
1. Remove `tokens_in`, `tokens_out`, `api_calls`, `cached_tokens` from `steps[]` (**BREAKING**)
2. Keep timing and interaction metrics in `steps[]` (duration, timestamps, HITL, retries)
3. All token/cost metrics remain in `aggregate_metrics` (no changes)
4. Add API key ID environment variables for filtering
5. Enforce fail-fast validation (no silent fallbacks)

**Impact**: Clean data model prevents misleading sprint-level analysis while maintaining accurate run-level metrics.
