# Research: Fix Zero Tokens Issue

**Feature**: 008-fix-zero-tokens  
**Date**: 2025-10-27  
**Status**: Complete

## Overview

This document consolidates research findings for switching from sprint-level to run-level token reconciliation in the BAeS experiment orchestrator.

## Research Questions

### 1. OpenAI Usage API Behavior

**Question**: How does the OpenAI Usage API attribute tokens to time buckets, and what are the query parameter constraints?

**Findings**:
- **Token Attribution**: Tokens are attributed by completion time (when OpenAI's backend finishes processing), NOT request time (when our code sends HTTP request)
- **Reporting Delay**: 5-60 minutes typical delay between API call completion and Usage API data availability
- **Bucket Granularity**: 
  - `bucket_width="1m"` → minute-level buckets (max 1440 per query = 24 hours)
  - `bucket_width="1h"` → hour-level buckets (max 168 per query = 7 days)
  - `bucket_width="1d"` → day-level buckets (max 31 per query = 1 month)
- **API Key Filtering**: `api_key_ids` parameter filters results to specific API keys (prevents cross-contamination when multiple frameworks run simultaneously)

**Decision**: Use `bucket_width="1m"` for maximum granularity (currently using "1d" which is causing the bug)

**Rationale**: Minute-level buckets provide best accuracy for run-level aggregation (runs are 3-6 minutes). Daily buckets aggregate all runs on the same day, making attribution impossible.

**Alternatives Considered**:
- Hour-level buckets (`bucket_width="1h"`): Too coarse for 3-6 minute runs (multiple runs per hour)
- Keep daily buckets: Would not fix the zero-token issue (all sprints see same daily total)

**Sources**:
- OpenAI API Documentation: https://platform.openai.com/docs/api-reference/usage
- Real CSV export: `/home/amg/Downloads/completions_usage_2025-10-27_2025-10-27.csv` (validated bucket structure)
- Issue report: 130+ sprints with zero tokens across 50+ runs (36-50% error rate)

---

### 2. API Key ID Resolution

**Question**: How do we map framework environment variables (OPENAI_API_KEY_BAES) to OpenAI's api_key_id format for the api_key_ids filter parameter?

**Findings**:
- OpenAI API keys are prefixed: `sk-proj-...` (project keys) or `sk-...` (user keys)
- API key IDs in Usage API responses use format: `key_XXXXXXXXXXXX` (e.g., `key_3QRCYbJRFQ0G4ycm`)
- There is NO public API to convert API key → API key ID
- **Solution**: Must store api_key_id mapping in environment variables or config

**Decision**: Add new environment variables for API key IDs:
- `OPENAI_API_KEY_BAES_ID` → Maps to `OPENAI_API_KEY_BAES`
- `OPENAI_API_KEY_CHATDEV_ID` → Maps to `OPENAI_API_KEY_CHATDEV`
- `OPENAI_API_KEY_GHSPEC_ID` → Maps to `OPENAI_API_KEY_GHSPEC`

**Rationale**: Explicit mapping is most reliable. Attempting to derive key ID from key string would require undocumented OpenAI internals.

**Alternatives Considered**:
- Extract from API responses: Requires making a Usage API query first (chicken-and-egg problem)
- Parse from OpenAI dashboard: Manual process, not automatable
- Don't use api_key_ids filter: Would cause cross-contamination when multiple frameworks run simultaneously (rejected for accuracy)

**Implementation Note**: Add validation in adapter initialization to ensure both key and key_id are configured.

---

### 3. Metrics Schema Changes

**Question**: Can we make breaking changes to the metrics.json schema?

**Findings**:
- Constitution Principle XII: "Each experiment is independent git repository with no cross-dependencies"
- Old experiments remain reproducible by checking out their git commits
- New experiments will use the new schema (clean data model)
- No migration needed (experiments are isolated)

**Decision**: **BREAKING CHANGE** - Remove token fields from steps array entirely

**Rationale**: 
- Each experiment run is independent (no cross-contamination)
- Old experiments remain intact and reproducible
- Clean schema prevents misleading sprint-level analysis going forward
- Simpler implementation (no backward compatibility code)

**New Schema**:
```json
{
  "aggregate_metrics": {"TOK_IN": 25202, "TOK_OUT": 19812, ...},
  "steps": [
    {"step": 1, "duration_seconds": 35.2, "start_timestamp": 1761523200, ...},  // No token fields
    {"step": 2, "duration_seconds": 38.1, "start_timestamp": 1761523235, ...}
  ]
}
```

**Alternatives Considered**:
- Maintain backward compatibility: Unnecessary complexity (violates Constitution XII)
- Migration script: Not needed (old experiments are independent)

---

### 4. Verification Logic Preservation

**Question**: Should we keep the N-check verification logic or simplify to single-check?

**Findings**:
- Current logic: Requires N consecutive stable readings (default N=2) with MIN_INTERVAL between checks
- Rationale for N-check: OpenAI Usage API data can change as delayed reports arrive
- Observation: Run-level aggregation is LESS sensitive to bucket changes than sprint-level (more stable)

**Decision**: **Keep N-check verification logic** (FR-004, FR-009)

**Rationale**: 
- Conservative approach ensures data quality
- Existing ENV variables (`RECONCILIATION_MIN_STABLE_VERIFICATIONS`, `RECONCILIATION_VERIFICATION_INTERVAL_MIN`) already provide configurability
- Minimal code impact (logic already exists)
- Better safe than sorry for research data accuracy

**Alternatives Considered**:
- Single-check verification: Faster but less reliable; small risk of capturing incomplete data
- Increase N to 3+: Slower verification, not justified by current error patterns

---

### 5. Bucket Boundary Handling

**Question**: How do we ensure tokens from API calls near sprint boundaries are captured correctly?

**Findings**:
- Scenario: Sprint ends at 10:05:30, API call completes at 10:05:15 but OpenAI processes it at 10:05:45
- Bucket assignment: Tokens land in 10:05:00-10:06:00 bucket (based on 10:05:45 completion)
- Current bug: Sprint-level query with exact timestamps misses this bucket
- Run-level solution: Query returns ALL buckets that intersect [run_start, run_end], naturally capturing boundary tokens

**Decision**: Use run-level time window WITHOUT manual extension (FR-013 clarified as "natural" bucket overlap, not artificial padding)

**Rationale**: OpenAI Usage API already returns buckets by bucket start time. A query for [10:00:00, 10:05:30] returns buckets: 10:00-10:01, 10:01-10:02, ..., 10:05-10:06. The 10:05-10:06 bucket naturally captures late-arriving tokens.

**Alternatives Considered**:
- Add 60-second padding to end_timestamp: Unnecessary; API already handles this
- Query with broader window (e.g., +5 minutes): Could capture tokens from next run (rejected for accuracy)

**Implementation Note**: No code changes needed beyond switching to run-level queries. The bucket aggregation algorithm already sums all returned buckets.

---

## Technology Best Practices

### OpenAI Usage API Integration

**Best Practice**: Always use `api_key_ids` filter when multiple API keys share an organization

**Rationale**: Prevents cross-contamination in shared time buckets (validated by CSV export showing multiple keys in same bucket)

**Best Practice**: Implement exponential backoff for API rate limits

**Rationale**: OpenAI Usage API has standard rate limits; retries ensure reliable data collection

**Best Practice**: Log all reconciliation attempts with timestamps and token deltas

**Rationale**: Enables debugging of verification failures and audit trails for research reproducibility

---

### Metrics Data Model Design

**Best Practice**: Store metrics at the coarsest reliable granularity (run-level, not sprint-level)

**Rationale**: Finer granularity requires more complex reconciliation logic and is more fragile to API timing issues

**Best Practice**: Separate timing metrics (step-level) from cost metrics (run-level)

**Rationale**: Different reconciliation strategies; timing is synchronous, tokens are asynchronous (API delay)

**Best Practice**: Use JSON schema validation for metrics files

**Rationale**: Catches schema drift early, prevents silent data corruption

---

## Risks & Mitigations

### Risk: API Key ID Mapping Errors

**Impact**: Token attribution to wrong framework (cross-contamination)

**Likelihood**: Medium (manual configuration)

**Mitigation**: 
- FR-011: Validate unique API keys at adapter initialization
- Add integration test that runs two frameworks simultaneously and verifies no cross-contamination
- Document API key ID setup in quickstart guide

---

### Risk: Delayed Token Reporting Beyond 24 Hours

**Impact**: Reconciliation gives up before data arrives (missed tokens)

**Likelihood**: Low (typically 5-60 minutes)

**Mitigation**:
- FR-009: MAX_AGE_HOURS configurable (default 24 hours)
- Log warnings when reconciliation times out
- Manual re-run of reconciliation script supported

---

### Risk: Breaking Change Impacts Existing Analysis

**Impact**: Analysis scripts expecting sprint-level tokens will fail

**Likelihood**: Medium (unknown downstream consumers)

**Mitigation**:
- Document schema change prominently in CHANGELOG and quickstart
- Each experiment is independent (old experiments unaffected)
- New experiments use clean schema from day one

---

## Implementation Priorities

1. **Phase 1** (Critical): Fix bucket_width bug in usage_reconciler.py (FR-005)
2. **Phase 1** (Critical): Add api_key_ids filtering (FR-010, FR-011)
3. **Phase 1** (High): Remove token fields from steps array in metrics_collector.py (FR-002, FR-003)
4. **Phase 1** (High): Update adapter execute_step() to not return tokens (cleanup)
5. **Phase 2** (Medium): Integration tests for run-level reconciliation
6. **Phase 2** (Low): Documentation updates (quickstart, troubleshooting)

---

## Conclusion

All technical unknowns resolved. Key decisions:
- Use `bucket_width="1m"` for minute-level granularity
- Add api_key_ids environment variables for framework isolation
- **BREAKING CHANGE**: Remove token fields from steps array (no backward compatibility needed per Constitution XII)
- Preserve N-check verification logic
- No artificial bucket boundary extensions needed

Ready to proceed to **Phase 1: Data Model & Contracts**.
