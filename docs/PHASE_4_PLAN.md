# Phase 4 Implementation Plan: Runner Scripts Enhancement

**Date:** October 20, 2025  
**Status:** 🔄 In Progress

## Overview

Phase 4 focuses on enhancing the remaining runner scripts (`run_experiment.sh` and `reconcile_usage.sh`) to support the multi-experiment system while maintaining backward compatibility.

## Scripts to Update

### 1. `runners/run_experiment.sh` ⚠️ DEPRECATED

**Current Behavior:**
- Runs frameworks using `python3 -m src.orchestrator <framework>`
- Accepts framework name (baes, chatdev, ghspec, all)
- Supports `--rounds N` for multiple sequential runs
- Uses hardcoded `./runs` directory

**Recommendation:** ❌ **Mark as deprecated**

**Rationale:**
- We already have `scripts/run_experiment.py` which is experiment-aware
- Shell script adds no value over Python script (less validation, less features)
- Python script provides better error handling and registry integration
- Maintaining both creates confusion and duplicate logic

**Action:**
1. Add deprecation notice at top of script
2. Suggest using `scripts/run_experiment.py` instead
3. Keep script functional for backward compatibility
4. Document migration path

---

### 2. `runners/reconcile_usage.sh` ✅ UPDATE NEEDED

**Current Behavior:**
- Wraps Python reconciliation code
- Calls `UsageReconciler()` without experiment context
- Uses `find_runs()` without experiment filter
- Works only with legacy `./runs` directory

**Required Changes:**
1. Accept optional experiment name as first argument
2. Pass experiment_name to Python code
3. Auto-detect multi-experiment vs legacy mode
4. Update usage examples in help text

**Implementation:**
```bash
# Auto-detect mode
if [ -d "experiments/$1" ]; then
    EXPERIMENT_NAME="$1"
    # Use experiment-specific paths
else
    EXPERIMENT_NAME=""
    # Use legacy paths
fi

# Pass to Python
python3 << EOF
from src.utils.experiment_paths import ExperimentPaths

if experiment_name:
    ep = ExperimentPaths(experiment_name)
    reconciler = UsageReconciler(runs_dir=ep.runs_dir)
    runs = find_runs(experiment_name=experiment_name)
else:
    reconciler = UsageReconciler()  # Default to ./runs
    runs = find_runs()  # Default behavior
EOF
```

---

## Implementation Strategy

### Step 1: Deprecate `run_experiment.sh` ✅

Add prominent deprecation notice:
```bash
#!/bin/bash
# DEPRECATED: This script is deprecated in favor of scripts/run_experiment.py
# 
# Please use instead:
#   python scripts/run_experiment.py <experiment_name> [framework]
# 
# This script will continue to work for backward compatibility but receives
# no new features. It uses the legacy ./runs directory and does not support
# multi-experiment configurations.
#
# Migration guide: See docs/MIGRATION.md
```

### Step 2: Update `reconcile_usage.sh` ✅

**Changes:**
1. Add experiment name detection
2. Update help text with experiment examples
3. Pass experiment context to Python code
4. Maintain full backward compatibility

**New Usage:**
```bash
# Legacy mode (backward compatible)
./runners/reconcile_usage.sh                      # Reconcile all in ./runs
./runners/reconcile_usage.sh chatdev              # Reconcile framework in ./runs
./runners/reconcile_usage.sh chatdev run-123      # Reconcile specific run

# Multi-experiment mode (new)
./runners/reconcile_usage.sh baseline             # Reconcile baseline experiment
./runners/reconcile_usage.sh baseline chatdev     # Reconcile framework in baseline
./runners/reconcile_usage.sh baseline chatdev run-123  # Reconcile specific run
```

### Step 3: Testing ✅

**Test Cases:**
1. Legacy mode: `./runners/reconcile_usage.sh --list`
2. Multi-experiment mode: `./runners/reconcile_usage.sh baseline --list`
3. Specific framework: `./runners/reconcile_usage.sh baseline baes`
4. Help text: `./runners/reconcile_usage.sh --help`

### Step 4: Documentation ✅

**Updates Needed:**
- Add migration guide for `run_experiment.sh` → `run_experiment.py`
- Update `reconcile_usage.sh` usage examples
- Document multi-experiment reconciliation workflow
- Update README with new workflows

---

## Detailed Changes

### `runners/run_experiment.sh`

**Before:**
```bash
#!/bin/bash
# Run BAEs experiment framework
# Usage: ./run_experiment.sh {baes|chatdev|ghspec|all}
```

**After:**
```bash
#!/bin/bash
# ⚠️ DEPRECATED - Use scripts/run_experiment.py instead
#
# This script is maintained for backward compatibility only.
# 
# NEW WAY (recommended):
#   python scripts/run_experiment.py <experiment_name> [framework]
#
# OLD WAY (this script, legacy):
#   ./runners/run_experiment.sh {baes|chatdev|ghspec|all}
```

---

### `runners/reconcile_usage.sh`

#### Change 1: Argument Parsing

**Before:**
```bash
case "${1:-}" in
  --help|-h)
    # help text
    ;;
  --list)
    # list runs
    ;;
  *)
    FRAMEWORK="${1:-}"
    RUN_ID="${2:-}"
    ;;
esac
```

**After:**
```bash
# Detect if first arg is an experiment name
EXPERIMENT_NAME=""
if [ -d "experiments/${1:-}" ]; then
    EXPERIMENT_NAME="$1"
    shift  # Remove experiment name from args
fi

case "${1:-}" in
  --help|-h)
    # Updated help text with experiment examples
    ;;
  --list)
    # Pass experiment_name to list code
    ;;
  *)
    FRAMEWORK="${1:-}"
    RUN_ID="${2:-}"
    ;;
esac
```

#### Change 2: Help Text

**Add to help:**
```bash
echo "Multi-Experiment Mode (NEW):"
echo "  $0 <experiment> [options]   # Reconcile specific experiment"
echo ""
echo "Examples:"
echo "  $0 baseline --list          # List pending in baseline experiment"
echo "  $0 baseline                 # Reconcile all in baseline"
echo "  $0 baseline baes            # Reconcile baes in baseline"
echo ""
echo "Legacy Mode (backward compatible):"
echo "  $0 [options]                # Uses ./runs directory"
```

#### Change 3: Python Code Updates

**Before:**
```python
reconciler = UsageReconciler()
runs = find_runs()
```

**After:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

experiment_name = "${EXPERIMENT_NAME}" if "${EXPERIMENT_NAME}" else None

if experiment_name:
    from src.utils.experiment_paths import ExperimentPaths
    ep = ExperimentPaths(experiment_name)
    reconciler = UsageReconciler(runs_dir=ep.runs_dir)
    runs = find_runs(experiment_name=experiment_name)
else:
    # Legacy mode
    reconciler = UsageReconciler()
    runs = find_runs()
```

---

## Integration Points

### Phase 1 Integration ✅
- Uses `ExperimentPaths` to get runs_dir
- Validates experiment exists

### Phase 2 Integration ✅
- Uses `find_runs(experiment_name=...)` for experiment-specific runs
- `UsageReconciler` accepts custom runs_dir

### Phase 3 Integration ✅
- Works alongside analysis workflow
- Ensures runs are verified before analysis

---

## Backward Compatibility

### ✅ Legacy Mode Preserved

All existing commands continue to work:
```bash
./runners/run_experiment.sh baes --rounds 5
./runners/reconcile_usage.sh --list
./runners/reconcile_usage.sh chatdev
```

### ✅ Graceful Migration

Users can adopt multi-experiment mode gradually:
1. Keep using old scripts (they still work)
2. Try new experiment-based workflow
3. Migrate fully when ready

---

## Success Criteria

### Must Have ✅
- [ ] `run_experiment.sh` marked as deprecated with clear migration path
- [ ] `reconcile_usage.sh` supports experiment names
- [ ] Backward compatibility maintained 100%
- [ ] Help text updated with examples
- [ ] All existing functionality preserved

### Should Have ✅
- [ ] Auto-detection of experiment vs legacy mode
- [ ] Clear error messages for invalid experiments
- [ ] Performance: No degradation
- [ ] Documentation: Updated usage guides

### Nice to Have 🎯
- [ ] Colorized output for experiment mode
- [ ] Validation warnings for deprecated usage
- [ ] Migration helper script

---

## Timeline

1. **Deprecate run_experiment.sh** - 5 minutes
2. **Update reconcile_usage.sh** - 30 minutes
3. **Testing** - 15 minutes
4. **Documentation** - 15 minutes

**Total: ~65 minutes**

---

## Risks & Mitigations

### Risk 1: Breaking Changes
**Mitigation:** Maintain 100% backward compatibility, add new features only

### Risk 2: Confusion Between Scripts
**Mitigation:** Clear deprecation notices, updated documentation

### Risk 3: Python Code Complexity
**Mitigation:** Keep embedded Python simple, use existing utilities

---

## Next Steps After Phase 4

**Phase 5: Migration & Documentation**
1. Create migration script for old runs
2. Update all README files
3. Add workflow examples
4. Document comparison workflows

---

## Open Questions

1. ❓ Should we warn users when they use deprecated `run_experiment.sh`?
   - **Decision:** Yes, but only in script comments, not runtime (to avoid breaking scripts)

2. ❓ Should `reconcile_usage.sh` auto-detect experiment from current directory?
   - **Decision:** No, keep explicit for clarity

3. ❓ Should we add `--experiment` flag for explicitness?
   - **Decision:** No, positional argument is simpler and matches other scripts

---

## Completion Checklist

- [ ] `run_experiment.sh` deprecated
- [ ] `reconcile_usage.sh` updated
- [ ] Help texts updated
- [ ] Testing complete
- [ ] Documentation updated
- [ ] Phase 4 summary created

**Status:** Ready to implement
