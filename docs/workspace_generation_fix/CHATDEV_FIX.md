# ChatDev Framework Fix

## Date: October 22, 2025

## Problem Summary

ChatDev framework fails with two issues:
1. **Missing Dependency**: `ModuleNotFoundError: No module named 'easydict'`
2. **Artifacts Location Mismatch**: Files saved to `artifacts/` but validation looks in `workspace/`

## Solution Overview

### Fix #1: Add easydict Dependency
**File**: Check if needs to be added to setup scripts  
**Change**: Ensure `easydict` is installed in ChatDev's venv

### Fix #2: Copy Artifacts to Workspace
**File**: `src/adapters/chatdev_adapter.py`  
**Method**: `_copy_artifacts()`  
**Change**: Copy files to `workspace/` instead of `artifacts/`

## Implementation Details

### Change #1: Fix _copy_artifacts() Method

**Current Code** (Lines 105-165):
```python
def _copy_artifacts(self, step_num: int, project_name: str) -> None:
    warehouse_path = self.framework_dir / "WareHouse"
    
    # PROBLEM: Copies to artifacts directory
    run_dir = Path(self.workspace_path).parent
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    # Copy to artifacts/
    dest_path = artifacts_dir / project_dir.name
    shutil.copytree(project_dir, dest_path)
```

**New Code** (DRY principle - align with BAeS pattern):
```python
def _copy_artifacts(self, step_num: int, project_name: str) -> None:
    """
    Copy ChatDev's WareHouse output to workspace directory.
    
    This ensures validation can find the generated code.
    Similar to how BAeS writes directly to workspace/managed_system.
    """
    warehouse_path = self.framework_dir / "WareHouse"
    
    if not warehouse_path.exists():
        logger.warning("WareHouse directory not found - no artifacts to copy",
                     extra={'run_id': self.run_id, 'step': step_num,
                           'metadata': {'expected_path': str(warehouse_path)}})
        return
    
    # Find the project directory
    project_dirs = list(warehouse_path.glob(f"{project_name}*"))
    
    if not project_dirs:
        logger.warning("No matching project directory found in WareHouse",
                     extra={'run_id': self.run_id, 'step': step_num,
                           'metadata': {'project_pattern': f"{project_name}*",
                                      'warehouse_path': str(warehouse_path)}})
        return
    
    # Copy to workspace directory (where validation expects it)
    workspace_dir = Path(self.workspace_path)
    
    for project_dir in project_dirs:
        try:
            # Copy contents of project_dir into workspace
            # (not the project_dir itself, to avoid nested structure)
            for item in project_dir.iterdir():
                dest = workspace_dir / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
            
            logger.info("Copied ChatDev artifacts to workspace",
                      extra={'run_id': self.run_id, 'step': step_num,
                            'metadata': {
                                'source': str(project_dir),
                                'destination': str(workspace_dir),
                                'files_copied': len(list(workspace_dir.rglob('*')))
                            }})
        except Exception as e:
            logger.error("Failed to copy ChatDev artifacts",
                       extra={'run_id': self.run_id, 'step': step_num,
                             'metadata': {
                                 'error': str(e),
                                 'source': str(project_dir),
                                 'destination': str(workspace_dir)
                             }})
```

### Change #2: Fix easydict Dependency

**Check**: Verify if `easydict` needs to be added to requirements

The error suggests it's missing from the ChatDev venv. Need to check:
1. `frameworks/chatdev/requirements.txt` in the experiment
2. ChatDev's original `requirements.txt` in the repository

**Most likely**: The issue is that we're using Python 3.11 for ChatDev (for compatibility) but `easydict` might not be installed. Check the setup script.

## Testing Plan

1. **Create test experiment**:
```bash
cd /home/amg/projects/uece/baes/genai-devbench
python scripts/new_experiment.py
# Name: test_chatdev_fix
# Model: gpt-4o-mini  
# Frameworks: baes,chatdev,ghspec
# Runs: 2
```

2. **Apply fixes**:
   - Update `_copy_artifacts()` method
   - Verify easydict is in requirements

3. **Run experiment**:
```bash
cd ../test_chatdev_fix
./setup.sh
./run.sh
```

4. **Validate results**:
   - [ ] ChatDev run 1 completes without errors
   - [ ] ChatDev run 2 completes without errors  
   - [ ] Python files exist in `workspace/`
   - [ ] Validation phase passes
   - [ ] No easydict import errors

## Success Criteria

✅ All tests pass  
✅ ChatDev generates files in `workspace/`  
✅ Validation finds and validates files  
✅ Both runs succeed consistently  
✅ BAeS and GHSpec still work (no regression)

## Next Steps After ChatDev Fix

1. Move to GHSpec investigation and fix
2. Extract common patterns to base adapter (DRY refactoring)
3. Document all changes
4. Final integration test with all frameworks
