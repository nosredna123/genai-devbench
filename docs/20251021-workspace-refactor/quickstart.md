# Quickstart: Workspace Refactor Developer Guide

**Date**: October 21, 2025  
**Audience**: Experiment users & adapter developers  
**Status**: Design Phase  
**Related**: [data-model.md](./data-model.md), [contracts/](./contracts/)

---

## Table of Contents

1. [For Experiment Users](#for-experiment-users)
2. [For Adapter Developers](#for-adapter-developers)
3. [Before & After Comparison](#before--after-comparison)
4. [Troubleshooting](#troubleshooting)
5. [FAQ](#faq)

---

## For Experiment Users

### What Changed?

**Before**: Every run created its own copy of the framework (622MB) and virtual environment (5 minutes).

**After**: Framework and venv are shared across all runs. Each run only stores its generated artifacts (~500KB).

**Benefits**:
- ✅ **99.8% disk reduction** per run (622MB → 0.5MB)
- ✅ **Instant startup** (no venv creation delay)
- ✅ **83% total savings** for 6-run experiments (3.7GB → 1.3GB)

### Updated Workflow

#### Step 1: Generate Experiment (Unchanged)

```bash
cd genai-devbench
python scripts/new_experiment.py \
    --name my-test-experiment \
    --frameworks baes chatdev \
    --prompts src/prompts/todo_app.yaml
```

**Creates**:
```
experiments/my-test-experiment/
├── config.yaml
├── main.py
└── (framework setup pending)
```

#### Step 2: Setup Frameworks (Now One-Time!)

```bash
cd experiments/my-test-experiment
python templates/setup_frameworks.py
```

**What happens**:
1. Clones framework repositories to `frameworks/`
2. Checks out correct commit hashes
3. **NEW**: Creates shared virtual environments (`.venv/`)
4. **NEW**: Applies framework patches (ChatDev only)

**Creates**:
```
frameworks/
├── baes/
│   ├── .venv/           ← Shared venv (619MB)
│   ├── baes/            ← Framework source (3MB)
│   └── requirements.txt
└── chatdev/
    ├── .venv/           ← Shared venv (646MB)
    ├── chatdev/         ← Framework source (4MB)
    └── requirements.txt
```

**Duration**: ~5 minutes (one-time setup)  
**Disk Usage**: ~1.3GB (shared across ALL runs)

#### Step 3: Run Experiment (Instant!)

```bash
python main.py
```

**What happens**:
1. Orchestrator reads `config.yaml`
2. For each run:
   - Creates run-specific workspace: `runs/<framework>/<run_id>/workspace/`
   - References shared framework: `frameworks/<framework>/`
   - Uses shared Python: `frameworks/<framework>/.venv/bin/python`
   - Executes framework with workspace for artifacts
   - Archives run artifacts

**Creates** (per run):
```
runs/baes/<run_id>/
└── workspace/
    ├── managed_system/  ← Generated code (500KB)
    └── database/        ← Run state (50KB)
```

**Duration**: ~2 minutes per run (no venv creation!)  
**Disk Usage**: ~550KB per run (only artifacts)

#### Step 4: View Results (Unchanged)

```bash
# Generate reports
python scripts/generate_reports.py --experiment my-test-experiment

# View artifacts
ls -lh runs/baes/<run_id>/workspace/managed_system/
```

### Directory Structure Overview

```
my-test-experiment/
│
├── frameworks/              ← SHARED (1.3GB, created once)
│   ├── baes/
│   │   ├── .venv/          ← Python venv (619MB)
│   │   └── baes/           ← Source code (3MB)
│   └── chatdev/
│       ├── .venv/          ← Python venv (646MB)
│       └── chatdev/        ← Source code (4MB)
│
├── runs/                    ← PER-RUN ARTIFACTS (~3MB for 6 runs)
│   ├── baes/
│   │   ├── run-001/
│   │   │   └── workspace/
│   │   │       ├── managed_system/  (500KB)
│   │   │       └── database/        (50KB)
│   │   └── run-002/
│   │       └── workspace/           (550KB)
│   └── chatdev/
│       ├── run-003/
│       │   └── workspace/
│       │       └── WareHouse/       (800KB)
│       └── run-004/
│           └── workspace/           (850KB)
│
├── config.yaml
├── main.py
└── logs/
```

**Total Disk Usage**:
- Old architecture: **3.7GB** (622MB × 6 runs)
- New architecture: **1.3GB** (1.3GB shared + 3MB runs)
- **Savings: 2.4GB (64%)**

---

## For Adapter Developers

### What Changed in Adapters?

**Before**: Each adapter copied framework to workspace and created venv per run.

**After**: Adapters reference shared framework and use base class methods.

### Migration Guide

#### Old Pattern (PRE-REFACTOR)

```python
class BAeSAdapter(BaseAdapter):
    def start(self):
        # ❌ OLD: Copy framework to workspace
        self.framework_dir = self.workspace_path / "baes_framework"
        self._copy_framework_to_workspace()
        
        # ❌ OLD: Create venv in workspace
        self._setup_virtual_environment()
        
        # Set paths
        self.python_path = self.framework_dir / ".venv" / "bin" / "python"
        self.managed_system_dir = self.workspace_path / "managed_system"
        self.database_dir = self.workspace_path / "database"
        
        # Create directories
        self.managed_system_dir.mkdir(parents=True)
        self.database_dir.mkdir(parents=True)
```

**Problems**:
- 622MB framework copy per run
- 5-minute venv creation per run
- ~150 lines of duplicate venv logic

#### New Pattern (POST-REFACTOR)

```python
class BAeSAdapter(BaseAdapter):
    def start(self):
        # ✅ NEW: Reference shared framework (read-only)
        self.framework_dir = self.get_shared_framework_path('baes')
        # Returns: frameworks/baes/
        
        # ✅ NEW: Use shared Python from venv
        self.python_path = self.get_framework_python('baes')
        # Returns: frameworks/baes/.venv/bin/python
        
        # ✅ NEW: Create only workspace directories
        workspace_dirs = self.create_workspace_structure([
            'managed_system',
            'database'
        ])
        self.managed_system_dir = workspace_dirs['managed_system']
        self.database_dir = workspace_dirs['database']
        
        # Set environment variables
        os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
        os.environ['BAE_CONTEXT_STORE_PATH'] = str(
            self.database_dir / "context_store.json"
        )
```

**Benefits**:
- Instant startup (no copying/venv creation)
- ~10 lines of code (vs. ~150)
- DRY: Base class handles common logic

### BaseAdapter Methods Reference

#### 1. `get_shared_framework_path(framework_name: str) -> Path`

**Purpose**: Get path to shared framework directory.

**Example**:
```python
self.framework_dir = self.get_shared_framework_path('baes')
# Returns: Path('/experiments/my-exp/frameworks/baes')
```

**Backward Compatibility**: Automatically falls back to old workspace location if needed.

**Raises**: `RuntimeError` if framework not found.

---

#### 2. `get_framework_python(framework_name: str) -> Path`

**Purpose**: Get Python executable from shared venv.

**Example**:
```python
self.python_path = self.get_framework_python('baes')
# Returns: Path('/experiments/my-exp/frameworks/baes/.venv/bin/python')
```

**Raises**: `RuntimeError` if venv not found or Python not executable.

---

#### 3. `create_workspace_structure(subdirs: list[str]) -> dict[str, Path]`

**Purpose**: Create run-specific workspace directories.

**Example**:
```python
workspace_dirs = self.create_workspace_structure([
    'managed_system',
    'database'
])
# Returns: {
#   'managed_system': Path('.../workspace/managed_system'),
#   'database': Path('.../workspace/database')
# }
```

**Validation**: Rejects framework names as subdirectories (prevents copying).

**Raises**: `ValueError` for invalid names, `OSError` for filesystem errors.

---

#### 4. `setup_shared_venv(framework_name: str, requirements_file: Path, timeout: int = 300) -> Path`

**Purpose**: Create or verify shared venv (used by `setup_frameworks.py`, not adapters).

**Example**:
```python
# In setup_frameworks.py
venv_path = adapter.setup_shared_venv(
    framework_name='baes',
    requirements_file=Path('frameworks/baes/requirements.txt'),
    timeout=300
)
# Creates: frameworks/baes/.venv/ with all packages
```

**Idempotent**: Safe to call multiple times (checks if venv exists).

**Raises**: `TimeoutError` if installation exceeds timeout, `RuntimeError` for other errors.

---

### Adapter-Specific Examples

#### Example 1: BAeSAdapter (Complete)

```python
class BAeSAdapter(BaseAdapter):
    def start(self):
        """Initialize BAEs adapter with shared resources."""
        # Get shared framework path
        self.framework_dir = self.get_shared_framework_path('baes')
        
        # Get shared Python executable
        self.python_path = self.get_framework_python('baes')
        
        # Create workspace directories
        workspace_dirs = self.create_workspace_structure([
            'managed_system',
            'database'
        ])
        self.managed_system_dir = workspace_dirs['managed_system']
        self.database_dir = workspace_dirs['database']
        
        # Set environment variables
        os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
        os.environ['BAE_CONTEXT_STORE_PATH'] = str(
            self.database_dir / "context_store.json"
        )
        
        logger.info(f"BAeSAdapter started with framework at {self.framework_dir}")
        logger.info(f"Python: {self.python_path}")
        logger.info(f"Workspace: {self.workspace_path}")
    
    def execute_step(self, step_config):
        """Execute BAEs step using shared framework."""
        cmd = [
            str(self.python_path),  # Use shared Python
            str(self.framework_dir / "baes" / "main.py"),  # Reference framework
            "--prompt", step_config['prompt'],
            "--output", str(self.managed_system_dir)  # Write to workspace
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
```

#### Example 2: ChatDevAdapter (Patching Removed)

```python
class ChatDevAdapter(BaseAdapter):
    def start(self):
        """Initialize ChatDev adapter with shared resources."""
        # Get shared framework path
        self.framework_dir = self.get_shared_framework_path('chatdev')
        
        # Get shared Python executable
        self.python_path = self.get_framework_python('chatdev')
        
        # Create workspace directories
        workspace_dirs = self.create_workspace_structure(['WareHouse'])
        self.warehouse_dir = workspace_dirs['WareHouse']
        
        # ❌ REMOVED: _patch_openai_compatibility() - now in setup_frameworks.py
        # ❌ REMOVED: _patch_o1_model_support() - now in setup_frameworks.py
        
        logger.info(f"ChatDevAdapter started with framework at {self.framework_dir}")
    
    def execute_step(self, step_config):
        """Execute ChatDev step using shared framework."""
        cmd = [
            str(self.python_path),
            str(self.framework_dir / "run.py"),  # Already patched!
            "--task", step_config['task'],
            "--name", step_config['project_name']
        ]
        
        # ChatDev writes to framework_dir/WareHouse, then copy to workspace
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.framework_dir)
        
        # Copy results to workspace
        self._copy_warehouse_to_workspace()
        
        return result
```

#### Example 3: GHSpecAdapter (No Venv)

```python
class GHSpecAdapter(BaseAdapter):
    def start(self):
        """Initialize GHSpec adapter (Node.js, no venv)."""
        # Get shared framework path
        self.framework_dir = self.get_shared_framework_path('ghspec')
        
        # ❌ NO get_framework_python() - GHSpec is Node.js
        
        # Create workspace (minimal, GHSpec outputs to stdout)
        self.create_workspace_structure([])  # Empty workspace
        
        logger.info(f"GHSpecAdapter started with framework at {self.framework_dir}")
    
    def execute_step(self, step_config):
        """Execute GHSpec using Node.js."""
        cmd = [
            "node",  # System Node.js (not venv)
            str(self.framework_dir / "src" / "index.js"),
            "--spec", step_config['spec']
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.framework_dir)
        return result
```

---

## Before & After Comparison

### Disk Usage

| Scenario | Old Architecture | New Architecture | Savings |
|----------|------------------|------------------|---------|
| 1 BAEs run | 622MB | 622MB (shared) + 0.5MB (run) = 622.5MB | 0MB (first run) |
| 2 BAEs runs | 1,244MB | 622MB (shared) + 1MB (runs) = 623MB | 621MB (50%) |
| 6 BAEs runs | 3,732MB | 622MB (shared) + 3MB (runs) = 625MB | 3,107MB (83%) |
| 1 experiment (3 frameworks, 6 runs) | 7,464MB | 1,322MB (shared) + 6MB (runs) = 1,328MB | 6,136MB (82%) |

### Startup Time

| Operation | Old Architecture | New Architecture | Improvement |
|-----------|------------------|------------------|-------------|
| Setup frameworks | ~5 min (per run!) | ~5 min (one-time) | 5× faster |
| Run startup | ~5 min (venv creation) | <1 sec (reference only) | 300× faster |
| Total for 6 runs | ~30 min | ~5 min setup + 6 sec runs = ~5 min | 6× faster |

### Code Complexity

| Adapter | Old LOC | New LOC | Reduction |
|---------|---------|---------|-----------|
| BAeSAdapter | ~180 lines | ~30 lines | 83% |
| ChatDevAdapter | ~250 lines | ~40 lines | 84% |
| GHSpecAdapter | ~120 lines | ~25 lines | 79% |
| **Total** | **~550 lines** | **~95 lines** | **83%** |

---

## Troubleshooting

### Issue 1: "Framework 'baes' not found"

**Symptom**:
```
RuntimeError: Framework 'baes' not found in frameworks/ or workspace/baes_framework/
```

**Cause**: Frameworks not set up.

**Solution**:
```bash
cd experiments/my-test-experiment
python templates/setup_frameworks.py
```

**Verify**:
```bash
ls -lh frameworks/
# Should show: baes/, chatdev/, ghspec/
```

---

### Issue 2: "Venv not found for framework 'baes'"

**Symptom**:
```
RuntimeError: Venv not found for framework 'baes'. Run setup_shared_venv first.
```

**Cause**: Virtual environment not created.

**Solution**:
```bash
# Re-run setup with verbose logging
python templates/setup_frameworks.py --verbose

# Manually check venv
ls -lh frameworks/baes/.venv/bin/python
```

**Verify**:
```bash
frameworks/baes/.venv/bin/python --version
# Should print: Python 3.11.x
```

---

### Issue 3: Workspace has old framework copy

**Symptom**: Disk usage still high, workspace contains `baes_framework/`.

**Cause**: Old experiment structure (pre-refactor).

**Solution**: Adapter automatically falls back to old location with warning. No action needed.

**Optional Migration**:
```bash
# Delete old framework copies (after verifying shared frameworks exist)
rm -rf runs/*/workspace/baes_framework
rm -rf runs/*/workspace/chatdev_framework
```

---

### Issue 4: Permission denied creating venv

**Symptom**:
```
OSError: [Errno 13] Permission denied: 'frameworks/baes/.venv'
```

**Cause**: Insufficient permissions on frameworks directory.

**Solution**:
```bash
# Fix permissions
chmod -R u+w frameworks/

# Re-run setup
python templates/setup_frameworks.py
```

---

### Issue 5: Venv creation timeout

**Symptom**:
```
TimeoutError: Venv creation timeout after 300s
```

**Cause**: Slow network or large requirements.txt.

**Solution**:
```python
# In templates/setup_frameworks.py, increase timeout
venv_path = adapter.setup_shared_venv(
    framework_name='baes',
    requirements_file=requirements_file,
    timeout=600  # Increase to 10 minutes
)
```

---

### Issue 6: "Workspace not writable"

**Symptom**:
```
PermissionError: Workspace not writable: runs/baes/<run_id>/workspace
```

**Cause**: Workspace directory permissions incorrect.

**Solution**:
```bash
# Fix workspace permissions
chmod -R u+w runs/

# Verify
touch runs/baes/<run_id>/workspace/test.txt && rm runs/baes/<run_id>/workspace/test.txt
```

---

## FAQ

### Q1: Do I need to re-run setup_frameworks.py for every experiment?

**A**: Yes, each experiment has its own `frameworks/` directory. Setup is one-time per experiment, but needed for each new experiment.

**Why**: Ensures reproducibility (each experiment has exact framework versions).

---

### Q2: Can I share frameworks/ across multiple experiments?

**A**: Not recommended. Each experiment should have isolated frameworks for reproducibility.

**Alternative**: Use symlinks (advanced users only):
```bash
ln -s ~/shared-frameworks/baes experiments/my-exp/frameworks/baes
```

---

### Q3: What if I need to update framework dependencies?

**A**: Delete venv and re-run setup:
```bash
rm -rf frameworks/baes/.venv
python templates/setup_frameworks.py
```

**Note**: This affects ALL future runs of the experiment.

---

### Q4: Can multiple runs execute concurrently?

**A**: Yes! Shared venv is read-only and safe for concurrent access.

**Verified**: Research Phase 0 confirmed Python venvs are concurrency-safe (see [research.md](./research.md)).

---

### Q5: How do I check disk usage?

**A**: Use du command:
```bash
# Total experiment size
du -sh experiments/my-test-experiment/

# Shared frameworks
du -sh experiments/my-test-experiment/frameworks/

# All runs
du -sh experiments/my-test-experiment/runs/

# Single run
du -sh experiments/my-test-experiment/runs/baes/<run_id>/
```

---

### Q6: Will old experiments break?

**A**: No. Adapters automatically fall back to old workspace structure.

**Details**: `get_shared_framework_path()` checks:
1. New location: `frameworks/baes/`
2. Old location: `workspace/baes_framework/` (fallback)

**Warning logged**: "Using deprecated workspace framework location"

---

### Q7: How do I verify everything is working?

**A**: Run this test:
```bash
cd experiments/my-test-experiment

# 1. Check frameworks exist
ls -lh frameworks/baes/.venv/bin/python
ls -lh frameworks/chatdev/.venv/bin/python

# 2. Test Python executables
frameworks/baes/.venv/bin/python --version
frameworks/chatdev/.venv/bin/python --version

# 3. Run experiment
python main.py

# 4. Verify workspace is small
du -sh runs/baes/*/workspace/
# Should show ~500KB per run (not 622MB!)

# 5. Verify frameworks unchanged
ls -lh frameworks/baes/  # Should still be 622MB
```

---

### Q8: What files can I delete to save space?

**Safe to delete**:
- `logs/` (experiment logs, regenerate anytime)
- Old run archives: `runs/*/*.tar.gz` (keep workspace dirs)

**Never delete**:
- `frameworks/` (breaks all future runs)
- `runs/*/workspace/` (lose experimental data)
- `config.yaml` (lose experiment configuration)

---

### Q9: Can I copy workspace/ to another machine?

**A**: Yes, but you'll need frameworks/ too.

**Steps**:
```bash
# On source machine
tar czf my-experiment.tar.gz frameworks/ runs/ config.yaml

# On destination machine
tar xzf my-experiment.tar.gz
cd my-experiment
python main.py  # Continue experiment
```

---

### Q10: How do I debug adapter issues?

**A**: Enable verbose logging:
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Run experiment
python main.py
```

**Check**:
- Framework paths: Look for "BAeSAdapter started with framework at..."
- Python executable: Look for "Python: frameworks/baes/.venv/bin/python"
- Workspace creation: Look for "Created workspace directory: ..."

---

## Next Steps

### For Experiment Users

1. ✅ Read this quickstart
2. ✅ Generate new experiment: `python scripts/new_experiment.py`
3. ✅ Run setup (one-time): `python templates/setup_frameworks.py`
4. ✅ Execute experiment: `python main.py`
5. ✅ Verify disk savings: `du -sh runs/` (should be <10MB for 6 runs)

### For Adapter Developers

1. ✅ Read [base_adapter_methods.yaml](./contracts/base_adapter_methods.yaml)
2. ✅ Review migration examples above
3. ✅ Update your adapter's `start()` method
4. ✅ Remove `_setup_virtual_environment()` method
5. ✅ Test with: `pytest tests/unit/test_<your>_adapter.py`
6. ✅ Verify disk usage improvement

### For Contributors

1. ✅ Read [data-model.md](./data-model.md) (entity definitions)
2. ✅ Read [research.md](./research.md) (design decisions)
3. ✅ Read [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) (full plan)
4. ✅ Review [contracts/](./contracts/) (API contracts)

---

## Summary

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Disk per run** | 622MB | 0.5MB | 99.8% reduction |
| **Setup time** | 5 min per run | 5 min one-time | 6× faster for 6 runs |
| **Code complexity** | ~550 LOC | ~95 LOC | 83% reduction |
| **Concurrency** | Not safe | Safe (read-only) | ✅ Concurrent runs |
| **Backward compat** | N/A | Automatic fallback | ✅ Old experiments work |

**Key Takeaway**: Shared frameworks + isolated workspaces = faster, leaner experiments with no downside.

---

**Questions?** Open an issue or check [research.md](./research.md) for technical details.
