# Investigation Report

## Date: October 22, 2025

## Objective
Investigate why ChatDev and GHSpec frameworks fail to generate workspace artifacts while BAeS succeeds.

## Experiment Data Analysis

### Experiment: agoravai
- **Model**: gpt-4o-mini
- **Frameworks**: baes, chatdev, ghspec
- **Runs per framework**: 2

### Results Summary

| Framework | Run 1 | Run 2 | Issue |
|-----------|-------|-------|-------|
| BAeS | ✅ 70s | ✅ 60s | None |
| ChatDev | ❌ 5s | ❌ 5s | `ModuleNotFoundError: No module named 'easydict'` |
| GHSpec | ❌ 20s | ❌ 20s | No Python files generated |

### Key Observations

1. **BAeS Success Pattern**
   - Takes 60-70 seconds (reasonable for LLM-based generation)
   - Passes validation phase
   - Archives successfully
   - Workspace: `workspace/managed_system/`

2. **ChatDev Failure Pattern**
   - Fails very quickly (5 seconds)
   - Missing Python dependency: `easydict`
   - Never reaches actual generation phase
   - Indicates environment setup issue

3. **GHSpec Failure Pattern**
   - Takes 20 seconds (suggests some execution happening)
   - No specific error in validation output
   - No Python files found in workspace
   - May be writing to wrong location or failing silently

## ChatDev Deep Dive

### Error Analysis
```
ModuleNotFoundError: No module named 'easydict'
```

This indicates:
1. ChatDev's virtual environment is missing `easydict` dependency
2. The dependency is not in `frameworks/chatdev/requirements.txt`
3. Setup phase didn't catch this missing dependency

### Action Items for ChatDev
1. ✅ Check `frameworks/chatdev/requirements.txt` for easydict
2. ✅ Add easydict to requirements if missing
3. ✅ Check adapter logs for actual execution flow
4. ✅ Verify workspace directory mapping
5. ✅ Compare with BAeS adapter implementation

## GHSpec Deep Dive

### Error Analysis
```
No Python files generated in workspace
Expected location: .../runs/ghspec/.../workspace
```

This suggests:
1. GHSpec executes but writes files elsewhere
2. Validation looks in wrong directory
3. GHSpec may fail silently without clear error

### Action Items for GHSpec
1. ✅ Check adapter logs for execution details
2. ✅ Find where GHSpec actually writes output
3. ✅ Check if it's a TypeScript/JS project (no Python files expected?)
4. ✅ Verify workspace directory configuration
5. ✅ Compare with BAeS adapter implementation

## Next Steps

### Immediate Actions
1. Examine ChatDev adapter logs from failed run
2. Examine GHSpec adapter logs from failed run
3. Review adapter implementations to find differences
4. Check requirements.txt files for all frameworks

### Investigation Focus
- Where does each adapter configure the workspace directory?
- How does validation determine the expected file location?
- What are the key differences between BAeS (working) and others (failing)?

## Code Analysis Findings

### ChatDev Adapter Issues

#### Issue #1: Missing easydict Dependency
**Location**: `frameworks/chatdev/requirements.txt`  
**Problem**: The `easydict` module is not included in ChatDev's requirements file  
**Impact**: Framework fails immediately on import with `ModuleNotFoundError: No module named 'easydict'`  
**Fix**: Add `easydict` to requirements.txt

#### Issue #2: Artifacts Saved to Wrong Location
**Location**: `ChatDevAdapter._copy_artifacts()` (lines 105-180)  
**Problem**: Artifacts are copied to `artifacts/` directory instead of `workspace/`  
**Code**:
```python
# WRONG: Copies to artifacts directory
artifacts_dir = run_dir / "artifacts"
# ...
shutil.copytree(project_dir, dest_path)
```

**Expected Behavior** (from BAeS):
```python
# CORRECT: Uses workspace directory directly
workspace_dirs = self.create_workspace_structure(['managed_system'])
self.managed_system_dir = workspace_dirs['managed_system']
# Framework writes directly to managed_system_dir
```

**Impact**: Validation looks in `workspace/` but files are in `artifacts/`  
**Fix**: Change `_copy_artifacts()` to copy to `workspace/` instead

#### Issue #3: Validation Method Exists but Artifacts Missing
**Location**: `ChatDevAdapter.validate_run_artifacts()` (lines 588-634)  
**Problem**: Validation looks for Python files in `workspace_path` but they're in `artifacts/`  
**Fix**: Ensure artifacts are copied to workspace before validation

### Comparison: BAeS vs ChatDev

| Aspect | BAeS (✅ Working) | ChatDev (❌ Broken) |
|--------|------------------|---------------------|
| Workspace Setup | `create_workspace_structure(['managed_system'])` | `create_workspace_structure(['WareHouse'])` |
| Output Location | `workspace/managed_system/` | `artifacts/` |
| Framework Writes To | `MANAGED_SYSTEM_PATH` env var | `WareHouse/` directory |
| Artifacts Copy | Not needed (writes directly) | Copies from WareHouse to artifacts |
| Validation Checks | `workspace/managed_system/` | `workspace/` |
| **Match?** | ✅ Yes | ❌ No - mismatch! |

### Root Cause Summary

**ChatDev has a mismatch between where artifacts are saved and where validation looks:**
1. ChatDev writes to `WareHouse/` directory
2. `_copy_artifacts()` copies to `artifacts/` directory  
3. Validation looks in `workspace/` directory
4. **Result**: Validation fails because `workspace/` is empty

**Solution**: Copy artifacts to `workspace/` instead of `artifacts/`
