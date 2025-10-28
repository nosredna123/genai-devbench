# Feature Specification: Fix Zero Tokens Issue in Usage Reconciliation

**Feature Branch**: `008-fix-zero-tokens`  
**Created**: 2025-10-27  
**Status**: Draft  
**Input**: User description: "Fix zero tokens issue in sprint-level reconciliation by switching to run-level token tracking"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate Run-Level Token Counts (Priority: P1)

As a researcher analyzing LLM-based framework performance, I need accurate token usage data for each run so that I can compute reliable cost and efficiency metrics.

**Why this priority**: This is the most critical functionality. Without accurate run-level totals, all downstream analysis (cost computation, framework comparison, efficiency metrics) is unreliable. Currently, 36-50% of sprints show zero tokens, making sprint-level analysis impossible, but run-level totals are already correct.

**Independent Test**: Can be fully tested by running a single framework execution, waiting for Usage API reconciliation, and verifying that `runs/baes/{run_id}/metrics.json` contains accurate `aggregate_metrics.TOK_IN` and `aggregate_metrics.TOK_OUT` values that match the OpenAI Usage API dashboard.

**Acceptance Scenarios**:

1. **Given** a framework run has completed, **When** reconciliation executes with run-level querying, **Then** `metrics.json` shows accurate total tokens matching OpenAI dashboard
2. **Given** a run completed 30+ minutes ago, **When** reconciliation runs, **Then** verification status transitions from "pending" to "verified" after N stable checks
3. **Given** multiple runs from different frameworks on the same day, **When** reconciliation queries with run-level time windows, **Then** each run receives only its own tokens (no cross-contamination)

---

### User Story 2 - Remove Misleading Sprint-Level Token Attribution (Priority: P2)

As a researcher, I should not see misleading per-sprint token counts that create false confidence in granular analysis when the Usage API cannot reliably provide this level of detail.

**Why this priority**: Sprint-level token attribution is fundamentally unreliable due to OpenAI's bucket-based API design. Rather than fixing it (impossible without per-request tracking from OpenAI), we should remove the misleading data to prevent incorrect analysis.

**Independent Test**: After implementation, examine `runs/baes/{run_id}/metrics.json` to verify that the `steps` array no longer contains `tokens_in`, `tokens_out`, `api_calls`, or `cached_tokens` fields (these should only exist at run level in `aggregate_metrics`).

**Acceptance Scenarios**:

1. **Given** a run completes, **When** metrics are saved, **Then** step-level metrics contain timing data but NOT token counts
2. **Given** reconciliation completes, **When** examining metrics.json, **Then** only `aggregate_metrics` contains token/API call data
3. **Given** existing runs with sprint-level token data, **When** viewing analysis reports, **Then** deprecated data is ignored (backward compatibility)

---

### User Story 3 - Clear Reconciliation Status Reporting (Priority: P3)

As a developer monitoring reconciliation, I need clear status messages explaining whether data is verified, still pending, or encountered issues.

**Why this priority**: Good observability aids debugging and builds confidence, but the core functionality (accurate tokens) takes precedence.

**Independent Test**: Run reconciliation script and verify console output clearly indicates verification status, attempt number, and time remaining until next check.

**Acceptance Scenarios**:

1. **Given** first reconciliation attempt, **When** Usage API has no data yet, **Then** status shows "data_not_available" with helpful message
2. **Given** token counts are stable, **When** N consecutive checks pass, **Then** status shows "verified" with timestamp
3. **Given** token counts decrease between attempts, **When** reconciliation runs, **Then** status shows "warning" with anomaly details

---

### Edge Cases

- What happens when a run spans midnight (crosses bucket boundaries)? **Solution**: Run-level query returns all buckets in the time window, correctly aggregating across date boundaries.
- How does system handle API rate limits or temporary failures? **Solution**: Existing retry logic with exponential backoff handles transient failures; verification remains "pending" until successful.
- What if Usage API data never arrives (>24 hours old)? **Solution**: Age limit (default 24 hours) prevents indefinite reconciliation attempts on stale runs.
- How to handle runs with zero LLM calls (e.g., template-based generation)? **Solution**: Verification accepts zero tokens as valid if stable across N checks.
- What if multiple framework runs execute simultaneously? **Solution**: API key filtering ensures each run captures only its own framework's tokens, preventing cross-contamination in shared time buckets.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST query OpenAI Usage API once per run using run-level start/end timestamps (not per-sprint)
- **FR-002**: System MUST store token counts only at run level in `aggregate_metrics` section of `metrics.json`
- **FR-003**: System MUST remove `tokens_in`, `tokens_out`, `api_calls`, `cached_tokens` fields from `steps` array
- **FR-004**: System MUST maintain existing N-check verification logic (consecutive stable readings before marking "verified")
- **FR-005**: System MUST use bucket_width="1m" for minute-level granularity when querying Usage API
- **FR-006**: System MUST aggregate all buckets within run time window to compute total tokens
- **FR-007**: System MUST log reconciliation attempts with run_id, framework, status, and token totals
- **FR-008**: System MUST mark verification status as "verified" only after N consecutive stable checks with >= MIN_INTERVAL between attempts
- **FR-009**: System MUST skip runs older than MAX_AGE_HOURS to avoid reconciling stale data
- **FR-010**: System MUST filter Usage API queries by framework-specific api_key_id to prevent cross-contamination when multiple frameworks execute in overlapping time windows
- **FR-011**: System MUST validate that each framework uses a unique API key (enforced at adapter initialization)
- **FR-012**: System MUST extend query window to include buckets that overlap run boundaries (API returns buckets by start time, not end time)

### Key Entities *(include if feature involves data)*

- **Run**: A single execution of a framework generating code artifacts
  - Attributes: run_id, framework, start_timestamp, end_timestamp, verification_status
  - Relationships: Contains multiple steps/sprints, has one metrics.json

- **Metrics**: Token usage and performance data for a run
  - Attributes: aggregate_metrics (TOK_IN, TOK_OUT, API_CALLS, CACHED_TOKENS, COST_USD), steps (timing only)
  - Relationships: Belongs to one Run

- **ReconciliationAttempt**: Single query to Usage API for verification
  - Attributes: timestamp, total_tokens_in, total_tokens_out, total_api_calls, status
  - Relationships: Part of Run's verification history

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of reconciled runs show accurate run-level token counts matching OpenAI Usage API dashboard (eliminate 36-50% zero-token error rate)
- **SC-002**: Reconciliation completes successfully for runs aged 30-1440 minutes (Usage API reporting window)
- **SC-003**: No sprint/step in metrics.json contains token count fields after fresh runs (clean data model)
- **SC-004**: Verification achieves "verified" status within expected timeframe (N checks × MIN_INTERVAL, typically 2 checks × 30 minutes = 60 minutes for production settings)
- **SC-005**: No token leakage between consecutive runs with different API keys (verified by running two frameworks back-to-back and comparing totals to OpenAI dashboard per-key breakdowns)

## Assumptions *(optional)*

- OpenAI Usage API continues to attribute tokens by completion time (not request time) with 5-60 minute reporting delay
- **Our timestamp capture is correct**: We accurately record when subprocess.run() starts/ends, which reflects when our code sends/receives API requests
- **OpenAI's internal processing adds delay**: Tokens are attributed based on when OpenAI's backend completes processing (after we receive the HTTP response), which we cannot observe or control
- Run-level time windows provide sufficient isolation between runs (no overlapping execution across frameworks on same API key)
- Existing N-check verification logic is sufficient for data stability validation
- Minute-level bucket width (1m) provides adequate granularity for run-level aggregation
- ENV variables `RECONCILIATION_VERIFICATION_INTERVAL_MIN` and `RECONCILIATION_MIN_STABLE_VERIFICATIONS` remain configurable

## Dependencies *(optional)*

- OpenAI Usage API availability and access via `OPEN_AI_KEY_ADM` with `api.usage.read` permission
- Existing metrics.json schema with `aggregate_metrics`, `steps`, and `usage_api_reconciliation` sections
- Existing reconciliation infrastructure: `UsageReconciler` class, `reconcile_usage.py` script, manifest manager
- Python libraries: requests (API calls), json (data handling), datetime (timestamp parsing)

## Technical Constraints *(optional)*

- OpenAI Usage API limitations:
  - 5-60 minute reporting delay
  - Maximum 1440 buckets per query (24 hours at minute granularity)
  - Tokens attributed by completion time, not request time
  - No per-request attribution capability
- Must preserve existing double-check verification pattern (N consecutive stable checks)
- Must maintain existing logging infrastructure and log persistence

## Out of Scope *(optional)*

- Per-sprint token attribution (fundamentally impossible with current Usage API design)
- Real-time token tracking during run execution (reconciliation is post-run only)
- Alternative token tracking methods (e.g., tiktoken estimation, response header parsing)
- Retroactive correction of existing runs with zero-token sprints (old experiments remain unchanged)
- Migration script to clean up sprint-level token data from old runs (not needed - experiments are independent)
- Changes to Usage API query parameters beyond bucket_width and api_key_ids
- Sprint-level analysis or visualization features (these become run-level only)

## Open Questions *(if applicable)*

None - the root cause is well-understood and the solution is clear.

## Related Documentation

- `/home/amg/projects/uece/baes/test_1004/analysis/invalid_sprints-tokens_count_zero.csv` - Data showing 36-50% zero-token sprints
- `docs/async_usage_api_design.md` - Original reconciliation design
- `docs/usage_reconciliation_guide.md` - Quick reference for reconciliation behavior
- `docs/LAZY_EVALUATION_PATTERN.md` - Explains post-run reconciliation pattern
- Issue report: "Zero Tokens Issue - Root Cause Summary" (provided in user input)
