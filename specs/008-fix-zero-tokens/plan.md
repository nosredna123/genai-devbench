# Implementation Plan: Fix Zero Tokens Issue in Usage Reconciliation

**Branch**: `008-fix-zero-tokens` | **Date**: 2025-10-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-fix-zero-tokens/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Fix systematic zero-token issue affecting 36-50% of BAeS sprints by switching from sprint-level to run-level token reconciliation. The OpenAI Usage API attributes tokens by completion time (not request time) and uses bucket-based aggregation, making per-sprint attribution unreliable. Solution: Query once per run with bucket_width="1m", aggregate all buckets in the time window, and store tokens only at run level in aggregate_metrics. Remove misleading sprint-level token fields from steps array to prevent false confidence in granular analysis.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: requests (OpenAI API calls), PyYAML (config), pytest (testing)  
**Storage**: JSON files (runs/{framework}/{run_id}/metrics.json)  
**Testing**: pytest with integration tests for reconciliation workflow  
**Target Platform**: Linux server (Ubuntu/Debian)  
**Project Type**: Single project (orchestrator with framework adapters)  
**Performance Goals**: Reconciliation completes within 24 hours for runs aged 30-1440 minutes  
**Constraints**: 
  - OpenAI Usage API 5-60 minute reporting delay
  - Maximum 1440 minute-buckets per query (24 hours)
  - Tokens attributed by completion time (not request time)
  - Must preserve backward compatibility with existing metrics.json files
**Scale/Scope**: 
  - 50+ runs across 3 frameworks (BAeS, ChatDev, GHSpec)
  - 130+ sprints with zero-token issue (36-50% error rate)
  - Run duration: 3-6 minutes with 30-40 second sprints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**INITIAL CHECK** (Before Phase 0): ✅ PASS  
**FINAL CHECK** (After Phase 1): ✅ PASS

Verify compliance with BAEs Experiment Constitution v1.2.0:

- [x] **Scientific Reproducibility**: Fixed random seeds N/A (no randomness in reconciliation); Framework versions already pinned in existing code
- [x] **Clarity & Transparency**: All modules documented; Logs already use structured JSON format; API contracts defined in contracts/
- [x] **Open Science**: Code licensed CC BY 4.0 (existing); No new proprietary dependencies
- [x] **Minimal Dependencies**: Using standard library + requests (already required); No new dependencies
- [x] **Deterministic HITL**: N/A (reconciliation is post-run, no HITL)
- [x] **Reproducible Metrics**: Feature ENHANCES metric reproducibility by fixing zero-token bug; Metrics verified against OpenAI Usage API (FR-001); Data model documented in data-model.md
- [x] **Version Control Integrity**: N/A (no framework version changes)
- [x] **Automation-First**: Reconciliation already automated via reconcile_usage.py script; No manual steps; Quickstart provides automation guidance
- [x] **Failure Isolation**: Each run already in isolated workspace with unique run_id; No changes to isolation
- [x] **Educational Accessibility**: Quickstart.md provides beginner-friendly setup guide; Research.md explains bucket-based API design; Code follows PEP 8
- [x] **DRY Principle**: Reuses existing UsageReconciler class; No code duplication; API contracts enforce single source of truth
- [x] **No Backward Compatibility Burden**: Each experiment is independent git repository; Breaking changes are acceptable (old experiments remain reproducible by checking out their commits); Clean schema going forward
- [x] **Fail-Fast Philosophy**: Removes silent fallbacks (sprint-level tokens are misleading); Fails immediately on API errors; Contracts specify fail-fast behavior for validation errors

**Constitution Compliance**: ✅ PASS - All principles satisfied after Phase 1 design. Data model, contracts, and quickstart documentation complete.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── orchestrator/
│   ├── usage_reconciler.py       # MODIFY: Change bucket_width, add API key filtering, remove _reconcile_steps()
│   ├── metrics_collector.py      # MODIFY: Remove token fields from record_step(), keep in aggregate only
│   └── manifest_manager.py       # READ-ONLY: Uses existing find_runs() for reconciliation
├── adapters/
│   ├── base_adapter.py           # MODIFY: Remove fetch_usage_from_openai() (deprecated)
│   ├── baes_adapter.py           # MODIFY: Remove step-level token calls, validate unique API key
│   ├── chatdev_adapter.py        # MODIFY: Same as baes_adapter
│   └── ghspec_adapter.py         # MODIFY: Same as baes_adapter
└── utils/
    └── logger.py                 # READ-ONLY: Existing structured logging

tests/
├── integration/
│   └── test_reconciliation.py    # NEW: Integration tests for run-level reconciliation
├── unit/
│   └── test_usage_reconciler.py  # MODIFY: Update tests for new bucket_width and API key filtering
└── conftest.py                   # READ-ONLY: Existing test fixtures

scripts/
└── reconcile_usage.py            # READ-ONLY: Entry point for reconciliation (uses UsageReconciler)

runs/
└── {framework}/
    └── {run_id}/
        └── metrics.json          # MODIFIED SCHEMA: Remove tokens from steps[], keep in aggregate_metrics only
```

**Structure Decision**: Single project structure (existing). This is a bug fix to the orchestrator's reconciliation logic, not a new service or application. All changes are within the existing src/orchestrator/ and src/adapters/ directories.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No violations** - All constitution principles satisfied. Breaking changes are acceptable per principle XII (each experiment is independent).
