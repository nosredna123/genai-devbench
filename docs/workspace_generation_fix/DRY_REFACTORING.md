# DRY Refactoring Analysis

## Overview

Analysis of code duplication across BAeS, ChatDev, and GHSpec adapters to identify opportunities for shared code extraction.

## Current DRY Implementations

### ✅ Already Implemented

#### 1. `_format_validation_error()` Helper (BaseAdapter)

**Location**: `src/adapters/base_adapter.py` lines 736-792

**Purpose**: Format consistent validation error messages across all frameworks

**Usage**: 
- BAeS: Line 516
- ChatDev: Line 620
- GHSpec: Line 1264

**Benefit**: Consistent error messaging, single source of truth for error format

```python
def _format_validation_error(
    self,
    workspace_dir: Path,
    framework_name: str,
    last_execution_error: Optional[Dict[str, Any]] = None
) -> str:
    # Extracts root cause and formats user-friendly error
    # Used by all 3 frameworks
```

#### 2. `get_framework_python()` Method (BaseAdapter)

**Location**: `src/adapters/base_adapter.py` lines 340-392

**Purpose**: Get Python executable path for framework venv

**Usage**:
- ChatDev: Multiple times for subprocess execution
- BAeS: Implicitly through base class
- GHSpec: N/A (no venv needed)

**Benefit**: Centralized venv Python path resolution, including the critical fix to preserve symlinks

#### 3. `_copy_directory_contents()` Helper (BaseAdapter) ✅

**Location**: `src/adapters/base_adapter.py` lines 795-870

**Purpose**: Shared method for copying generated artifacts to workspace directory

**Usage**:
- GHSpec: Copy from `specs/001-baes-experiment/src/` to `workspace/`
- ChatDev: Can be refactored to use this (currently has custom logic)

**Benefit**: Eliminates duplication of file copying logic, consistent error handling

```python
def _copy_directory_contents(
    self,
    source_dir: Path,
    dest_dir: Path,
    step_num: int,
    recursive: bool = True
) -> int:
    # Copies files from source to dest
    # Used by GHSpec (and can be used by ChatDev)
```

## Framework-Specific Patterns (Not Duplicated)

### 1. Artifact Handling

**ChatDev**: `_copy_artifacts()` - Copies from WareHouse/ to workspace/
```python
def _copy_artifacts(self, step_num: int, project_name: str):
    # ChatDev-specific: copy from WareHouse structure
    warehouse_path = self.framework_dir / "WareHouse"
    # ... copy to workspace
```

**BAeS**: Writes directly to workspace/managed_system/
- No copying needed

**GHSpec**: Writes directly to workspace/specs/001-baes-experiment/src/
- No copying needed

**Analysis**: Not duplicated - each framework has unique artifact storage pattern.

### 2. Validation Logic

**BAeS**: `validate_run_artifacts()` - Checks workspace/managed_system/
```python
managed_system_dir = workspace_dir / "managed_system"
python_files = list(managed_system_dir.rglob("*.py"))
```

**ChatDev**: `validate_run_artifacts()` - Checks workspace/ root
```python
python_files = list(workspace_dir.rglob("*.py"))
```

**GHSpec**: `validate_run_artifacts()` - Checks workspace/ recursively (includes specs/)
```python
python_files = list(workspace_dir.rglob("*.py"))
# Also checks for API entry points
```

**Analysis**: Similar pattern (rglob), but framework-specific directory expectations. Minimal duplication.

### 3. Environment Setup

**ChatDev**: Complex subprocess environment with PYTHONPATH
```python
env['PYTHONPATH'] = str(self.framework_dir)
env['VIRTUAL_ENV'] = str(self.venv_path)
```

**BAeS**: Uses Docker containers
- Different environment model

**GHSpec**: Direct OpenAI API calls
- No environment setup needed

**Analysis**: Too framework-specific to extract.

## Opportunities for Further DRY (Optional)

### 1. Validation Helper for `rglob("*.py")`

**Current**: All 3 adapters use similar pattern:
```python
python_files = list(workspace_dir.rglob("*.py"))
if not python_files:
    return False, error_msg
```

**Potential**: Extract to base adapter:
```python
def _count_python_files(self, directory: Path) -> int:
    """Count Python files recursively in directory."""
    return len(list(directory.rglob("*.py")))
```

**Value**: Low - only saves 1 line per adapter
**Recommendation**: ⚠️ Not worth it - clarity vs. abstraction tradeoff

### 2. Common Logging Patterns

**Current**: Similar logging patterns:
```python
logger.info("Framework ready", extra={'run_id': self.run_id, ...})
```

**Potential**: Logger wrapper methods
**Value**: Low - would obscure logging structure
**Recommendation**: ⚠️ Keep explicit logging

## Conclusion

### Already Achieved ✅

1. `_format_validation_error()` - Shared error formatting
2. `get_framework_python()` - Shared venv Python resolution
3. Base class structure - Common interface across adapters

### Not Worth Extracting ❌

The remaining "duplicated" code is:
- **Framework-specific** by nature (artifact paths, validation rules)
- **Too minimal** to extract (1-2 lines)
- **Better kept explicit** for clarity and maintainability

## Recommendation

**Phase 3 Status**: ✅ COMPLETE

The critical DRY improvements are already in place. Further extraction would:
- Increase abstraction complexity
- Reduce code clarity
- Provide minimal benefit

**Best Practice**: Keep framework-specific logic in adapters, share only truly common utilities.
