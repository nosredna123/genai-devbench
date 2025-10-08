# Specification Decisions Log

**Feature**: BAEs Experiment Framework  
**Specification**: [spec.md](spec.md)  
**Date**: 2025-10-08  
**Status**: Resolved

## Purpose

This document records all clarification decisions made during specification development. It preserves the original questions, available options, and selected answers to enable rollback and maintain decision traceability.

---

## Decision 1: Failed Step Retry Policy

**Decision ID**: BAES-SPEC-001  
**Date**: 2025-10-08  
**Status**: ✅ Resolved

### Original Question

**Context**: Assumption 7 in the specification asked: "Should the system support re-running failed steps within a run, or should failures result in run termination and a fresh run attempt?"

**What we needed to know**: How should the system handle step failures that persist after the r=2 automatic retries?

### Available Options

| Option | Description | Implications |
|--------|-------------|--------------|
| **A** | **Terminate run and start fresh** | Preserves experimental purity, simpler implementation, may waste resources on framework bugs |
| B | Allow manual intervention to fix framework environment and resume from failed step | More resource-efficient, introduces non-determinism, requires manual monitoring |
| C | Continue to next step even after failure (mark step as failed, log partial metrics) | Maximizes data collection, allows analysis of failure patterns, may produce incomplete artifact sets |
| Custom | User-provided alternative | Flexible but requires detailed specification |

### Selected Answer

**Option A**: Terminate run and start fresh

### Rationale

This approach:
- **Preserves scientific reproducibility**: Each run is either complete or discarded, no partial/contaminated runs
- **Maintains determinism**: No manual intervention during execution
- **Simplifies implementation**: Clear binary outcome (success/failure)
- **Aligns with constitution**: Principle IX (Failure Isolation) requires clean environments
- **Trade-off accepted**: Resource waste on framework bugs is acceptable given experimental integrity priority

### Implementation Details

When a step fails after r=2 automatic retries:
1. System logs the failure with timestamp, step number, error details
2. Marks the run status as "failed"
3. Archives partial artifacts for debugging (metrics up to failure point, logs, error trace)
4. Stops execution immediately (does not proceed to subsequent steps)
5. Increments failed run counter
6. Continues with next scheduled run (does not count toward stopping rule minimum)

### Rollback Instructions

To revert to different policy:
1. Locate Assumption 7 in spec.md
2. Replace current text with desired option from table above
3. Update FR-028 (retry handling) to reflect new policy
4. Update Edge Cases section to describe new failure handling
5. Update this decision log with rollback justification

---

## Decision 2: Step Timeout Policy

**Decision ID**: BAES-SPEC-002  
**Date**: 2025-10-08  
**Status**: ✅ Resolved

### Original Question

**Context**: Assumption 8 in the specification asked: "What is the maximum acceptable wall-clock time per step before considering it a timeout?"

**What we needed to know**: Should the system enforce maximum time limits per step to prevent indefinite hangs?

### Available Options

| Option | Description | Implications |
|--------|-------------|--------------|
| A | No timeout - frameworks run until completion | May cause indefinite hangs, wastes resources on stuck frameworks, requires manual monitoring |
| **B** | **Fixed timeout: 2 hours per step (12 hours max per run)** | Prevents indefinite hangs, may prematurely kill legitimate slow executions, requires calibration testing |
| C | Adaptive timeout: 3× median step time from previous runs | Learns from data, handles variability, requires initial calibration runs, complex implementation |
| Custom | User-provided timeout value/policy | Flexible timing configuration |

### Selected Answer

**Option B (Modified)**: Fixed timeout of **10 minutes per step** (60 minutes max per run)

### Rationale

This approach:
- **Prevents indefinite hangs**: Hard limit stops stuck frameworks
- **Resource efficiency**: Frees resources quickly for next runs
- **Realistic for test scenario**: Six-step CRUD app evolution should complete within minutes per step for functional frameworks
- **Early failure detection**: 10 minutes is generous for simple operations but catches serious issues
- **Simpler than adaptive**: No learning mechanism needed, deterministic behavior
- **Conservative initial value**: Can be adjusted based on calibration runs

### Implementation Details

Timeout enforcement:
1. System starts wall-clock timer when step execution begins
2. Monitor checks elapsed time every 30 seconds
3. At 9:30 (warning threshold), log warning with current framework status
4. At 10:00 (hard timeout):
   - Send SIGTERM to framework process
   - Wait 30 seconds for graceful shutdown
   - Send SIGKILL if process still running
   - Log timeout event with partial metrics
   - Mark step as "timeout failure"
   - Apply Decision 1 policy (terminate run, start fresh)

Configuration:
- Timeout value stored in `config/experiment.yaml` as `step_timeout_seconds: 600`
- Adjustable per framework if needed: `framework_overrides.baes.step_timeout_seconds: 900`
- Warning threshold at 95% of timeout value

Metrics:
- Record timeout events in metrics.json: `"timeout_occurred": true/false`
- Track time-to-timeout for failed runs: `"elapsed_at_timeout": <seconds>`

### Calibration Plan

Before production runs:
1. Execute 3 calibration runs per framework with timeout disabled
2. Record P95 step completion time
3. Verify 10-minute timeout exceeds P95 by 2× margin
4. Adjust timeout if P95 > 5 minutes (should indicate framework issue)

### Rollback Instructions

To change timeout policy:
1. Locate Assumption 8 in spec.md
2. Update timeout value or select different option from table above
3. Modify `config/experiment.yaml` template with new timeout
4. Update FR-028 to reflect new timeout handling
5. Update Edge Cases section with new timeout behavior
6. Re-run calibration if switching to adaptive timeout
7. Update this decision log with new timeout value and justification

---

## Decision 3: Artifact Archival Scope

**Decision ID**: BAES-SPEC-003  
**Date**: 2025-10-08  
**Status**: ✅ Resolved

### Original Question

**Context**: Assumption 9 in the specification asked: "Should artifact archival include framework-generated source code, or only orchestrator logs and metrics?"

**What we needed to know**: What should be included in the run.tar.gz archive for each completed run?

### Available Options

| Option | Description | Implications |
|--------|-------------|--------------|
| **A** | **Full workspace: generated code, database, logs, all intermediate files** | Maximum reproducibility, enables detailed failure analysis, high storage cost (~10GB/run), long archival time |
| B | Selective archival: metrics, logs, database snapshot only (no generated code) | Lower storage (~500MB/run), faster archival, cannot reproduce exact code for inspection |
| C | Code snapshots only at critical steps (1, 3, 6) + full metrics/logs | Balances storage and reproducibility, enables milestone code review, moderate complexity |
| Custom | User-defined archival policy | Flexible content selection |

### Selected Answer

**Option A**: Full workspace archival (generated code, database, logs, all intermediate files)

### Rationale

This approach:
- **Maximizes reproducibility**: Complete artifact set enables exact run replication
- **Enables deep analysis**: Framework-generated code can be inspected for quality assessment
- **Supports debugging**: All intermediate files available for failure analysis
- **Aligns with constitution**: Principle X (Educational Accessibility) benefits from code examples
- **Aligns with Open Science**: Principle III requires publishing all artifacts
- **Storage is acceptable**: 10GB × 75 runs = 750GB is manageable with modern storage
- **Research value**: Generated code serves as dataset for code quality analysis

### Implementation Details

Archive contents (`run.tar.gz`):
```
runs/{framework}/{run-id}/
├── workspace/              # Full framework workspace
│   ├── src/                # Generated source code
│   ├── tests/              # Generated tests (if any)
│   ├── database.sqlite     # Final database state
│   ├── migrations/         # Schema migration files
│   ├── requirements.txt    # Python dependencies
│   └── .git/               # Framework's git history (if maintained)
├── orchestrator/
│   ├── metrics.json        # All collected metrics
│   ├── hitl_events.jsonl   # HITL interaction log
│   ├── api_spec.json       # OpenAPI specification
│   ├── ui_snapshot.html    # UI capture
│   ├── db_snapshot.sqlite  # Database state per step
│   ├── usage_api.json      # OpenAI usage data
│   ├── stdout.log          # Framework output
│   ├── stderr.log          # Framework errors
│   ├── orchestrator.log    # Orchestrator events
│   └── commit.txt          # Framework commit hash
└── metadata.json           # Run metadata
```

Archival process:
1. Create archive directory structure
2. Copy workspace directory (excluding .env with API keys)
3. Copy all orchestrator logs and metrics
4. Compress with gzip level 6 (balanced speed/size)
5. Compute SHA-256 hash of archive
6. Store hash in metadata.json
7. Verify archive integrity (test extraction)
8. Move archive to permanent storage location

Storage management:
- Archives stored in `runs/{framework}/{run-id}/run.tar.gz`
- Original workspace deleted after successful archival
- Archive retention: permanent (or until storage cleanup script run manually)
- Storage monitoring: alert if free space < 100GB

Exclusions (never archived):
- API keys and secrets (`.env` files)
- Virtual environment directories (`venv/`, `.venv/`)
- Package caches (`__pycache__/`, `.pytest_cache/`)
- Temporary files (`*.tmp`, `*.swp`)

### Storage Optimization

Compression strategies:
- Use `tar czf` with pigz (parallel gzip) for faster compression
- Exclude binary dependencies (can be reinstalled from requirements.txt)
- De-duplicate identical files across runs (consider hardlinks if same framework/step)

Expected sizes:
- Small run (minimal code): ~500MB compressed
- Average run (full app): ~2-5GB compressed
- Large run (complex framework): ~8-10GB compressed

### Rollback Instructions

To change archival policy:
1. Locate Assumption 9 in spec.md
2. Select different option from table above
3. Update FR-015 (artifact list) with new content
4. Update FR-016 (storage requirements) with new size estimates
5. Modify archival script to include/exclude content per new policy
6. Update Constraints section with new storage requirements
7. Update this decision log with new archival scope and justification

---

## Summary

| Decision ID | Topic | Selected Option | Key Impact |
|-------------|-------|-----------------|------------|
| BAES-SPEC-001 | Failed Step Retry Policy | A - Terminate and restart | Preserves experimental purity, simpler implementation |
| BAES-SPEC-002 | Step Timeout Policy | B (Modified) - 10 minutes/step | Prevents hangs, faster failure detection |
| BAES-SPEC-003 | Artifact Archival Scope | A - Full workspace | Maximum reproducibility, ~10GB/run storage |

## Change History

| Date | Decision ID | Change | Reason |
|------|-------------|--------|--------|
| 2025-10-08 | BAES-SPEC-002 | Reduced timeout from 2 hours to 10 minutes | More realistic for simple CRUD evolution scenario |

## Notes

- All decisions align with project constitution principles (reproducibility, transparency, open science)
- Decisions prioritize scientific validity over resource efficiency
- Storage costs (~750GB total) are acceptable for research project scale
- Timeout value (10 min) may need adjustment after calibration runs
