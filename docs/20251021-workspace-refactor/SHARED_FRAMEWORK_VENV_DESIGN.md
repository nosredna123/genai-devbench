# Shared Framework & Virtual Environment Design (DRY Architecture)

**Date**: October 21, 2025  
**Status**: Design Phase  
**Related Issue**: Framework copying waste (622MB per run)

## Problem Statement

Current implementation wastes massive resources:
- **Framework code** (~3.6MB): Copied to every run workspace - unnecessary duplication
- **Virtual environments** (~619MB): Created fresh for every run - 5+ minutes installation time
- **Total waste**: ~622MB disk + 5min per run

### Root Causes
1. Each adapter duplicates venv creation logic
2. Frameworks copied to workspace even though they're read-only
3. No distinction between shared resources vs. run-specific artifacts

## Proposed Architecture

### Directory Structure

```
<experiment>/
├── frameworks/                    # Shared, read-only resources
│   ├── baes/
│   │   ├── .venv/                # SHARED venv (created once by setup.sh)
│   │   ├── baes/                 # Framework source code
│   │   ├── requirements.txt
│   │   └── ...
│   ├── chatdev/
│   │   ├── .venv/                # SHARED venv (created once by setup.sh)
│   │   ├── ChatDev/              # Framework source code
│   │   └── ...
│   └── ghspec/
│       ├── ... (no venv, runs with system Node.js)
│
└── runs/
    └── <framework>/
        └── <run_id>/
            ├── workspace/
            │   └── managed_system/    # ONLY generated artifacts (writable)
            │       ├── app.py
            │       ├── models/
            │       └── ...
            ├── database/              # Run-specific state
            ├── outputs/               # Framework-specific outputs
            ├── run.log
            └── metrics.json
```

## Design Principles (DRY)

### BaseAdapter Responsibilities

**New generic methods in `base_adapter.py`:**

1. **`setup_shared_venv(framework_name, requirements_file, timeout)`**
   - Check if `frameworks/<name>/.venv/` exists
   - If not, create it and install requirements
   - Return path to shared venv
   - Used by: BAEs, ChatDev

2. **`get_framework_python(framework_name)`**
   - Return path to `frameworks/<name>/.venv/bin/python`
   - Validates venv exists and Python is executable
   - Used by: Any adapter with `use_venv: true`

3. **`create_workspace_structure(subdirs)`**
   - Create only necessary run-specific directories
   - Examples: `managed_system/`, `database/`, `outputs/`
   - Skip creating framework directory copies

4. **`get_shared_framework_path(framework_name)`**
   - Return path to `frameworks/<name>/`
   - Used for reading framework code without copying

### Adapter-Specific Responsibilities

Each adapter (BAEs, ChatDev, GHSpec) only implements:
- Framework-specific execution logic
- Custom patches/configurations
- Prompt handling
- Result parsing

**What adapters should NOT do anymore:**
- ❌ Clone/copy framework code to workspace
- ❌ Create virtual environments
- ❌ Install packages

## Implementation Plan

### Phase 1: Update BaseAdapter (Generic Logic)

**File**: `src/adapters/base_adapter.py`

```python
def setup_shared_venv(
    self,
    framework_name: str,
    requirements_file: Optional[Path] = None,
    python_version: str = "python3",
    timeout_install: int = 300
) -> Path:
    """
    Set up or reuse shared virtual environment for framework.
    
    This method is called by adapters during initialization if use_venv=true.
    The venv is created in frameworks/<name>/.venv/ and shared across all runs.
    
    Args:
        framework_name: Name of framework (e.g., 'baes', 'chatdev')
        requirements_file: Path to requirements.txt (defaults to frameworks/<name>/requirements.txt)
        python_version: Python executable to use
        timeout_install: Timeout for pip install (seconds)
        
    Returns:
        Path to shared venv directory
        
    Raises:
        RuntimeError: If venv creation or package installation fails
    """
    # Implementation...
    pass

def get_framework_python(self, framework_name: str) -> Path:
    """Get path to Python interpreter in shared venv."""
    pass

def create_workspace_structure(self, subdirs: List[str]) -> Dict[str, Path]:
    """Create only run-specific directories in workspace."""
    pass

def get_shared_framework_path(self, framework_name: str) -> Path:
    """Get path to shared framework directory."""
    pass
```

### Phase 2: Update templates/setup.sh

**Add venv setup for frameworks that need it:**

```bash
# After cloning each framework
if [ -f "frameworks/$FRAMEWORK/requirements.txt" ]; then
  echo "Setting up shared virtual environment for $FRAMEWORK..."
  python3 -m venv "frameworks/$FRAMEWORK/.venv"
  "frameworks/$FRAMEWORK/.venv/bin/pip" install -r "frameworks/$FRAMEWORK/requirements.txt"
  echo "✓ $FRAMEWORK venv ready"
fi
```

### Phase 3: Update BAeSAdapter

**File**: `src/adapters/baes_adapter.py`

**Before** (50+ lines):
```python
def start(self) -> None:
    self.framework_dir = Path(self.workspace_path) / "baes_framework"
    self.managed_system_dir = Path(self.workspace_path) / "managed_system"
    
    # Clone/copy framework (wasteful)
    self.setup_framework_from_repo(...)
    
    # Create venv in workspace (wasteful!)
    self._setup_virtual_environment()  # 619MB + 5 minutes
```

**After** (~10 lines):
```python
def start(self) -> None:
    # Get shared framework path (no copying!)
    self.framework_dir = self.get_shared_framework_path('baes')
    
    # Get shared venv (already created by setup.sh)
    self.venv_path = self.framework_dir / ".venv"
    self.python_path = self.get_framework_python('baes')
    
    # Create only run-specific directories
    workspace_dirs = self.create_workspace_structure([
        'managed_system',
        'database'
    ])
    self.managed_system_dir = workspace_dirs['managed_system']
    self.database_dir = workspace_dirs['database']
    
    # Set environment variables
    os.environ['BAE_CONTEXT_STORE_PATH'] = str(self.database_dir / "context_store.json")
    os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
    # ... rest of env setup
```

**Remove entirely**:
- `_setup_virtual_environment()` method (50+ lines)
- All venv creation and pip install logic

### Phase 4: Update ChatDevAdapter

**File**: `src/adapters/chatdev_adapter.py`

Similar changes:
- Use `get_shared_framework_path('chatdev')`
- Use `get_framework_python('chatdev')`
- Remove `_setup_virtual_environment()` method
- Create only `workspace/WareHouse/` for generated projects

### Phase 5: Update GHSpecAdapter

**File**: `src/adapters/ghspec_adapter.py`

Minimal changes (no venv needed):
- Use `get_shared_framework_path('ghspec')`
- Remove framework copying logic

### Phase 6: Update experiment.yaml

Add `use_venv` flag to all frameworks:

```yaml
frameworks:
  baes:
    use_venv: true
    # ...
    
  chatdev:
    use_venv: true  # ADD THIS
    # ...
    
  ghspec:
    use_venv: false  # Node.js-based, no Python venv
    # ...
```

## Benefits

### Performance
- **Disk savings**: 622MB → ~1MB per run (99.8% reduction)
- **Time savings**: 5min venv creation → 0s (instant)
- **Setup time**: One-time cost in setup.sh vs. per-run cost

### Code Quality (DRY)
- **Lines of code**: Remove ~150 lines of duplicate venv logic
- **Maintainability**: Single source of truth for venv setup
- **Consistency**: All adapters use same venv strategy

### Clarity
- **Separation of concerns**: 
  - `frameworks/`: Shared, read-only resources
  - `runs/<id>/workspace/`: Run-specific, writable artifacts
- **Debugging**: Generated code isolated in workspace
- **Reproducibility**: Same framework + venv = identical environment

## Migration Path

1. ✅ **Design** (this document)
2. ⏳ **Implement BaseAdapter methods**
3. ⏳ **Update setup.sh template**
4. ⏳ **Refactor BAeSAdapter** (remove venv creation)
5. ⏳ **Refactor ChatDevAdapter** (remove venv creation)
6. ⏳ **Refactor GHSpecAdapter** (remove framework copying)
7. ⏳ **Update experiment.yaml** (add use_venv flags)
8. ⏳ **Test with fresh experiment**
9. ⏳ **Update documentation**

## Testing Strategy

1. **Create test experiment**: `python scripts/new_experiment.py --name test-shared-venv --frameworks baes,chatdev --runs 1`
2. **Verify setup.sh**: Check frameworks/*/. venv created only once
3. **Run experiment**: Verify no venv creation in workspace
4. **Check disk usage**: Confirm workspace has only artifacts
5. **Verify all adapters**: BAEs, ChatDev, GHSpec all work
6. **Performance comparison**: Measure time savings

## Expected Disk Usage After Implementation

**Per 6-run experiment with 3 frameworks:**

Before:
- Framework copies: 3 × 6 × 3.6MB = 64.8MB
- Venvs: 2 × 6 × 619MB = 7,428MB
- **Total**: ~7.5GB per experiment ❌

After:
- Shared frameworks: 3 × 3.6MB = 10.8MB
- Shared venvs: 2 × 619MB = 1,238MB
- Run artifacts: 6 × ~1MB = 6MB
- **Total**: ~1.25GB per experiment ✅

**Savings**: 83% disk reduction + instant run startup

## Questions for Implementation

1. **Venv isolation**: Should we symlink or use same venv? → Same venv (same commit = same packages)
2. **Framework modifications**: What if adapter needs to patch framework code? → Patch in shared location during setup
3. **Concurrent runs**: Can multiple runs share same venv safely? → Yes, Python packages are read-only
4. **Cleanup strategy**: When to delete shared venvs? → Only on new setup.sh run or manual cleanup

## Related Documents
- `docs/DRY_REFACTORING_COMPLETE.md`: Previous DRY work on framework setup
- `config/experiment.yaml`: Framework configuration
- `templates/setup.sh`: Initial framework setup script
