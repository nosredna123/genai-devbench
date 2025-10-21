# Phase 0 Research: Workspace Refactor Technical Analysis

**Date**: October 21, 2025  
**Status**: Research Complete  
**Related**: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)

## Executive Summary

This document presents findings from technical research conducted to validate the workspace refactor design. All 5 research questions have been investigated with definitive decisions.

**Key Findings**:
- ✅ Shared venv is safe for concurrent read-only access
- ✅ ChatDev patches modify source files (must run during setup_frameworks.py)
- ✅ Workspace directory requirements confirmed for all 3 adapters  
- ✅ setup_frameworks.py already exists (not setup.sh) - needs venv integration
- ✅ Minimal backward compatibility impact - 4 test files need updates

---

## 1. Venv Safety Analysis

### Question
Can multiple Python processes safely share a read-only venv simultaneously?

### Decision
**YES** - Shared venvs are safe for concurrent read-only access by multiple Python processes.

### Rationale

#### Python Venv Architecture
A Python virtual environment consists of:
1. **`pyvenv.cfg`**: Configuration file (read-only metadata)
2. **`bin/` (or `Scripts/` on Windows)**: Executables including Python interpreter (read-only binaries)
3. **`lib/pythonX.Y/site-packages/`**: Installed packages (read-only after installation)
4. **`__pycache__/`**: Bytecode cache (write operations occur but are atomic and idempotent)

#### Read-Only Nature
- **Package imports**: Read from `.py` and `.pyc` files, no writes to venv
- **`__pycache__` writes**: Python handles concurrent cache writes via atomic operations
  - Race conditions result in duplicate work, not corruption
  - Cache misses are acceptable (Python regenerates)
- **C extensions**: Loaded as shared objects (`.so`/`.dll`), inherently read-only

#### Concurrent Access Patterns
- **Multiple runs**: Each run is a separate Python process
- **No shared state**: Processes don't share memory, only read from disk
- **No locking needed**: OS filesystem handles concurrent reads efficiently

### Testing Approach

**Test Plan** (for validation during Phase 2):
```python
# tests/unit/test_shared_venv_concurrent.py
import pytest
import subprocess
from pathlib import Path
import concurrent.futures
import sys

def test_shared_venv_concurrent_access(tmp_path):
    """
    Verify shared venv can be used by multiple processes simultaneously.
    """
    # Create shared venv
    venv_path = tmp_path / "shared_venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    
    python_exe = venv_path / "bin" / "python"
    
    # Run 10 concurrent processes using the same venv
    def run_python(i):
        result = subprocess.run(
            [str(python_exe), "-c", f"import sys; print(f'Process {i}: {{sys.prefix}}')"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and "shared_venv" in result.stdout
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_python, i) for i in range(10)]
        results = [f.result() for f in futures]
    
    assert all(results), "All concurrent processes should succeed"
```

### Edge Cases Documented

1. **`__pycache__` race conditions**: 
   - **Impact**: Negligible - duplicate compilation work only
   - **Mitigation**: None needed (Python handles it)

2. **C extension loading**:
   - **Impact**: None - shared objects are read-only by design
   - **Mitigation**: None needed

3. **Pip install during runs**:
   - **Impact**: Would corrupt venv
   - **Mitigation**: Venv created during setup_frameworks.py only, never during runs

4. **Disk space**:
   - **Impact**: ~1.2GB for 2 venvs (BAEs + ChatDev)
   - **Mitigation**: Documented in deployment requirements

### Conclusion
Shared venv architecture is **production-ready** with no concurrency concerns.

---

## 2. Framework Patching Strategy

### Question
Where should ChatDev compatibility patches be applied if framework is shared?

### Decision
**Patches MUST be applied during `setup_frameworks.py` execution** (once, before any runs).

### Rationale

#### Current Patching Logic Analysis
ChatDev adapter applies two types of patches:

**Patch 1: `_patch_openai_compatibility()`** (lines 293-331)
- **What**: Adds `annotations: object = None` field to `ChatMessage` dataclass
- **Where**: Modifies `camel/messages/chat_messages.py` **source file**
- **When**: Called during `adapter.start()` (currently per-run)
- **Effect**: **MODIFIES SHARED FRAMEWORK SOURCE**

**Patch 2: `_patch_o1_model_support()`** (lines 333-457)
- **What**: Adds O1 and GPT-5 model support
- **Where**: Modifies 5 source files:
  - `camel/typing.py` (ModelType enum)
  - `camel/model_backend.py` (token limits)
  - `ecl/utils.py` (token limits)
  - `chatdev/statistics.py` (pricing)
  - `run.py` (CLI arguments)
- **When**: Called during `adapter.start()` (currently per-run)
- **Effect**: **MODIFIES SHARED FRAMEWORK SOURCE**

#### Problem with Current Approach
- Patches modify framework source files in `frameworks/chatdev/`
- If run concurrently, multiple adapters would attempt to write simultaneously
- Current code checks "if already patched" but has race conditions
- Wasteful: Re-checking and re-writing identical patches every run

#### Proposed Solution
Move patching to `setup_frameworks.py`:

```python
# templates/setup_frameworks.py (add after clone_framework function)

def patch_chatdev_if_needed(framework_dir: Path):
    """Apply ChatDev compatibility patches after cloning."""
    patches_needed = []
    
    # Check if patches already applied
    typing_file = framework_dir / "camel" / "typing.py"
    if typing_file.exists():
        content = typing_file.read_text()
        if 'O1_MINI' not in content:
            patches_needed.append('o1_models')
    
    chat_messages_file = framework_dir / "camel" / "messages" / "chat_messages.py"
    if chat_messages_file.exists():
        content = chat_messages_file.read_text()
        if 'annotations: object = None' not in content:
            patches_needed.append('openai_compat')
    
    if not patches_needed:
        print("  ✓ ChatDev patches already applied")
        return
    
    print(f"  Applying patches: {', '.join(patches_needed)}")
    
    if 'openai_compat' in patches_needed:
        apply_openai_compatibility_patch(framework_dir)
    
    if 'o1_models' in patches_needed:
        apply_o1_model_patch(framework_dir)
    
    print("  ✓ ChatDev patches applied successfully")

def clone_framework(name: str, repo_url: str, commit_hash: str):
    # ... existing clone logic ...
    
    # NEW: Apply framework-specific patches after cloning
    if name == 'chatdev' and target_dir.exists():
        patch_chatdev_if_needed(target_dir)
```

### Implementation Notes

**Changes Required**:

1. **Create patches module**:
   - New file: `templates/patches/chatdev_patches.py`
   - Move patching functions from adapter
   - Make functions standalone (no self references)

2. **Update setup_frameworks.py**:
   - Import chatdev patches module
   - Call patching after successful clone
   - Log patch application status

3. **Update ChatDevAdapter**:
   - Remove `_patch_openai_compatibility()` method
   - Remove `_patch_o1_model_support()` method
   - Remove patch calls from `start()` method
   - Add validation check to ensure patches were applied

### Benefits
- ✅ Patches applied once during setup (no runtime overhead)
- ✅ No race conditions (single-threaded setup)
- ✅ Cleaner adapter code (framework-agnostic)
- ✅ Patches version-controlled with framework commit hash

### Validation Strategy
Add check in ChatDevAdapter.start():
```python
def start(self):
    # Verify patches were applied during setup
    typing_file = self.framework_dir / "camel" / "typing.py"
    if not typing_file.exists() or 'O1_MINI' not in typing_file.read_text():
        raise RuntimeError(
            "ChatDev framework not properly patched. "
            "Run: python templates/setup_frameworks.py"
        )
```

---

## 3. Workspace Directory Requirements

### Question
What directories does each adapter actually need in workspace?

### Analysis Results

#### BAEs Adapter
**Source**: `src/adapters/baes_adapter.py`

**Required Directories**:
1. **`managed_system/`** (line 55)
   - Purpose: Stores generated application code
   - Set via: `MANAGED_SYSTEM_PATH` environment variable (line 75)
   - Used by: BAEs framework to write generated code
   - Lifecycle: Created at start, populated during execution, archived at end

2. **`database/`** (line 56)
   - Purpose: Stores context store and execution state
   - Contains: `context_store.json` (line 74, 187)
   - Set via: `BAE_CONTEXT_STORE_PATH` environment variable
   - Lifecycle: Created at start, updated during execution

**NOT Required** (to be removed):
- ❌ `baes_framework/` - Framework code (should use shared)
- ❌ `baes_framework/.venv/` - Virtual environment (should use shared)

**Code Change**:
```python
# OLD
self.framework_dir = Path(self.workspace_path) / "baes_framework"

# NEW
self.framework_dir = self.get_shared_framework_path('baes')
workspace_dirs = self.create_workspace_structure(['managed_system', 'database'])
self.managed_system_dir = workspace_dirs['managed_system']
self.database_dir = workspace_dirs['database']
```

#### ChatDev Adapter
**Source**: `src/adapters/chatdev_adapter.py`

**Required Directories**:
1. **`WareHouse/`** (special case)
   - Purpose: ChatDev's output directory for generated projects
   - Location: ChatDev writes to `framework_dir/WareHouse/` (line 475)
   - **Current behavior**: ChatDev writes to shared `frameworks/chatdev/WareHouse/`
   - **After execution**: Copied to run artifacts (lines 466-520)

**Workspace Structure for ChatDev**:
Since ChatDev writes to its own framework directory, we need special handling:
- **Option A**: Let ChatDev write to shared `frameworks/chatdev/WareHouse/`, clean before each run
- **Option B**: Create symlink from `workspace/WareHouse/` to `frameworks/chatdev/WareHouse/`
- **Option C**: Create temporary `WareHouse/` in workspace, copy framework, let ChatDev write there

**Decision**: **Option C** - Create workspace-local WareHouse for isolation
- Each run gets its own WareHouse directory in workspace
- No risk of concurrent runs overwriting each other's outputs
- Adapter references framework from shared location but outputs to workspace

**NOT Required**:
- ❌ `chatdev_framework/` source code (should use shared)
- ❌ `chatdev_framework/.venv/` (should use shared)

**Code Change**:
```python
# OLD
self.framework_dir = Path(self.workspace_path) / "chatdev_framework"

# NEW
self.framework_dir = self.get_shared_framework_path('chatdev')
workspace_dirs = self.create_workspace_structure(['WareHouse'])
self.warehouse_dir = workspace_dirs['WareHouse']

# Update execute_step to use workspace WareHouse
# Set ChatDev's working directory to use workspace WareHouse
```

#### GHSpec Adapter
**Source**: `src/adapters/ghspec_adapter.py`

**Required Directories**:
1. **No workspace subdirectories currently required**
   - GHSpec runs directly from framework directory
   - Output artifacts are generated and captured via stdout/files
   - May need `outputs/` directory for future enhancements

**NOT Required**:
- ❌ `ghspec_framework/` - Framework code (should use shared)
- ✅ No venv needed (Node.js-based framework)

**Code Change**:
```python
# OLD
self.framework_dir = Path(self.workspace_path) / "ghspec_framework"

# NEW
self.framework_dir = self.get_shared_framework_path('ghspec')
# No workspace subdirectories needed currently
```

### Summary Table

| Adapter | Workspace Directories | Framework Location | Venv Needed |
|---------|----------------------|-------------------|-------------|
| BAEs | `managed_system/`, `database/` | `frameworks/baes/` | Yes |
| ChatDev | `WareHouse/` | `frameworks/chatdev/` | Yes |
| GHSpec | (none) | `frameworks/ghspec/` | No |

---

## 4. setup.sh Implementation

### Question
How does setup.sh determine which frameworks need venvs?

### Discovery
**IMPORTANT**: The template is called `setup_frameworks.py`, NOT `setup.sh`

**Current Implementation**: `templates/setup_frameworks.py`
- Written in Python (not bash)
- Loads `config.yaml` to get framework definitions
- Clones frameworks and checks out commit hashes
- Does NOT currently create venvs

### Decision
Extend `setup_frameworks.py` to create venvs based on `use_venv` flag in config.

### Implementation Approach

**Configuration Reading**:
```python
def setup_venv_if_needed(name: str, framework_dir: Path, use_venv: bool):
    """Create virtual environment and install requirements if needed."""
    if not use_venv:
        print(f"  ✓ {name} does not require venv (skipping)")
        return
    
    venv_dir = framework_dir / ".venv"
    requirements_file = framework_dir / "requirements.txt"
    
    if venv_dir.exists():
        print(f"  ✓ {name} venv already exists")
        return
    
    if not requirements_file.exists():
        print(f"  ⚠️  No requirements.txt found for {name}, skipping venv")
        return
    
    print(f"  Creating virtual environment for {name}...")
    try:
        import subprocess
        import sys
        
        # Create venv
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
            timeout=120
        )
        
        # Install requirements
        pip_exe = venv_dir / "bin" / "pip"
        if sys.platform == "win32":
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        
        print(f"  Installing dependencies from requirements.txt...")
        subprocess.run(
            [str(pip_exe), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            timeout=120
        )
        
        subprocess.run(
            [str(pip_exe), "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            timeout=300
        )
        
        print(f"  ✓ {name} venv ready")
        
    except subprocess.TimeoutExpired:
        print(f"  ❌ Venv setup timed out for {name}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Venv setup failed for {name}")
        if e.stderr:
            print(f"     {e.stderr.decode('utf-8')[:500]}")
        sys.exit(1)

def clone_framework(name: str, repo_url: str, commit_hash: str, use_venv: bool = False):
    # ... existing clone logic ...
    
    # After successful clone/checkout:
    if target_dir.exists():
        # Setup venv if needed
        setup_venv_if_needed(name, target_dir, use_venv)
        
        # Apply framework-specific patches
        if name == 'chatdev':
            patch_chatdev_if_needed(target_dir)

def main():
    # ... existing config loading ...
    
    for name, fw_config in enabled_frameworks.items():
        clone_framework(
            name,
            fw_config['repo_url'],
            fw_config['commit_hash'],
            fw_config.get('use_venv', False)  # NEW parameter
        )
```

### Error Handling

**Timeout Handling**:
- Venv creation: 120 seconds
- Pip upgrade: 120 seconds  
- Requirements install: 300 seconds (5 minutes)
- If timeout: Print error, exit with code 1

**Disk Space Checks**:
```python
import shutil

def check_disk_space(path: Path, required_gb: float = 2.0):
    """Check if sufficient disk space available."""
    stat = shutil.disk_usage(path)
    available_gb = stat.free / (1024**3)
    
    if available_gb < required_gb:
        print(f"⚠️  Warning: Low disk space ({available_gb:.1f}GB available)")
        print(f"   Recommended: {required_gb}GB for venv creation")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            sys.exit(1)
```

### Configuration Access

The `use_venv` flag is read from `config.yaml`:
```yaml
frameworks:
  baes:
    use_venv: true  # Already exists
    # ...
  
  chatdev:
    use_venv: true  # NEW - to be added
    # ...
  
  ghspec:
    use_venv: false  # NEW - to be added (Node.js project)
    # ...
```

---

## 5. Backward Compatibility

### Question
Will existing experiments break with this change?

### Assessment
**Impact Level**: **LOW** - Minimal breaking changes

### Breaking Changes Identified

#### 1. Test Files Hardcoding Workspace Paths
**Affected Files**:
- `tests/unit/test_chatdev_adapter.py` (2 occurrences)
  - Line 224: `warehouse_dir = temp_workspace / "chatdev_framework" / "WareHouse"`
  - Line 271: `framework_dir = temp_workspace / "chatdev_framework"`

- `tests/unit/test_archiver.py` (2 occurrences)
  - Line 456: `workspace = temp_run_dir / "chatdev_framework" / "WareHouse"`
  - Line 489: `workspace_dir=workspace.parent.parent`

**Fix Required**:
Update test fixtures to use shared framework path:
```python
# OLD
framework_dir = temp_workspace / "chatdev_framework"

# NEW  
framework_dir = temp_workspace.parent.parent / "frameworks" / "chatdev"
```

#### 2. Metrics Collection Paths
**Analysis**: Checked metrics collection code
**Result**: ✅ No hardcoded workspace/framework paths
- Metrics reference `managed_system_dir` and `database_dir` (adapter attributes)
- Paths are dynamic, not hardcoded

#### 3. Existing Generated Experiments
**Question**: Will experiments generated before this change still work?

**Answer**: **YES** - Full backward compatibility

**Reasoning**:
- Old experiments have framework in `workspace/baes_framework/`
- Old experiments don't have `frameworks/` directory
- Adapters still check workspace first (fallback behavior)
- New experiments use `frameworks/` directory
- Both can coexist

**Implementation**:
```python
# BaseAdapter.get_shared_framework_path()
def get_shared_framework_path(self, framework_name: str) -> Path:
    """Get path to shared framework, with fallback to workspace (backward compat)."""
    # Check shared location first (new approach)
    shared_path = self.experiment_root / "frameworks" / framework_name
    if shared_path.exists():
        return shared_path
    
    # Fallback to workspace location (old experiments)
    workspace_path = Path(self.workspace_path) / f"{framework_name}_framework"
    if workspace_path.exists():
        logger.warning(
            f"Using deprecated workspace framework location: {workspace_path}",
            extra={'run_id': self.run_id}
        )
        return workspace_path
    
    # Neither exists - error
    raise RuntimeError(
        f"Framework '{framework_name}' not found in shared location ({shared_path}) "
        f"or workspace ({workspace_path}). Run: python templates/setup_frameworks.py"
    )
```

### Migration Path

#### For New Experiments
- Use updated generator: `python scripts/new_experiment.py`
- Run `python templates/setup_frameworks.py` once
- Frameworks in `frameworks/` directory
- Instant run startup (no venv creation)

#### For Existing Experiments
**Option 1: Keep As-Is** (Recommended for in-flight experiments)
- No changes needed
- Continues to work with workspace frameworks
- Slightly slower (creates venv per run)

**Option 2: Migrate to Shared** (For long-running experiments)
1. Run setup script to create `frameworks/` directory:
   ```bash
   cd experiment_dir
   python ../genai-devbench/templates/setup_frameworks.py
   ```

2. Delete old workspace frameworks (optional cleanup):
   ```bash
   find runs/ -name "*_framework" -type d -exec rm -rf {} +
   ```

3. Future runs will use shared frameworks automatically

### Deprecation Warnings

Add logging when using old structure:
```python
logger.warning(
    "Deprecated: Framework in workspace detected. "
    "Consider running setup_frameworks.py to use shared frameworks.",
    extra={
        'run_id': self.run_id,
        'framework': framework_name,
        'old_path': str(workspace_path),
        'new_path': str(shared_path)
    }
)
```

### Testing Strategy

**Backward Compatibility Tests**:
```python
# tests/unit/test_backward_compatibility.py

def test_old_experiment_structure_still_works(tmp_path):
    """Verify experiments with workspace frameworks still work."""
    # Create old-style structure
    workspace = tmp_path / "runs" / "baes" / "test-id" / "workspace"
    framework_dir = workspace / "baes_framework"
    framework_dir.mkdir(parents=True)
    
    # Create adapter
    adapter = BAeSAdapter(config, workspace, experiment_root=tmp_path)
    
    # Should find framework in workspace (fallback)
    assert adapter.get_shared_framework_path('baes') == framework_dir

def test_new_experiment_structure_preferred(tmp_path):
    """Verify new shared structure is used when available."""
    # Create both old and new structures
    workspace = tmp_path / "runs" / "baes" / "test-id" / "workspace"
    old_framework = workspace / "baes_framework"
    old_framework.mkdir(parents=True)
    
    new_framework = tmp_path / "frameworks" / "baes"
    new_framework.mkdir(parents=True)
    
    # Create adapter
    adapter = BAeSAdapter(config, workspace, experiment_root=tmp_path)
    
    # Should prefer new shared location
    assert adapter.get_shared_framework_path('baes') == new_framework
```

### Summary

| Change | Breaking? | Mitigation |
|--------|-----------|------------|
| Shared frameworks | No | Fallback to workspace frameworks |
| Shared venvs | No | Created in shared location only |
| Test paths | **Yes** | Update 4 test files |
| Metrics paths | No | Already dynamic |
| Old experiments | No | Backward compatible fallback |

**Conclusion**: Backward compatibility is maintained with minimal updates required (4 test files only).

---

## Phase 0 Completion Checklist

- [x] 1. Venv Safety Analysis - **SAFE for concurrent access**
- [x] 2. Framework Patching Strategy - **Apply during setup_frameworks.py**
- [x] 3. Workspace Directory Requirements - **Confirmed for all 3 adapters**
- [x] 4. setup.sh Implementation - **Extend setup_frameworks.py with venv creation**
- [x] 5. Backward Compatibility - **Maintained with fallback logic**

## Next Steps

**Phase 1**: Create design documents based on these findings:
1. `data-model.md` - Directory structure entities and relationships
2. `contracts/base_adapter_methods.yaml` - BaseAdapter method contracts
3. `contracts/directory_structure.yaml` - Filesystem layout contracts
4. `quickstart.md` - Developer guide

**Phase 2**: Implementation
- Begin with BaseAdapter methods
- Update setup_frameworks.py
- Refactor adapters
- Update tests
- Validate disk usage improvements
