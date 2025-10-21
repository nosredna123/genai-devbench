# Data Model: Workspace Refactor Directory Structure

**Date**: October 21, 2025  
**Status**: Design Phase  
**Related**: [research.md](./research.md), [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)

## Overview

This document defines the entities, relationships, and state transitions for the workspace refactor architecture. The design separates **shared, read-only framework resources** from **run-specific, writable artifacts**.

---

## Entity Definitions

### Entity 1: SharedFramework

**Purpose**: Centralized framework installation shared across all runs of an experiment.

**Location Pattern**: `<experiment_root>/frameworks/<framework_name>/`

**Attributes**:

| Attribute | Type | Description | Mutability |
|-----------|------|-------------|------------|
| `framework_name` | string | Framework identifier (baes, chatdev, ghspec) | Immutable |
| `source_code` | directory | Cloned git repository | Read-only after setup |
| `commit_hash` | string | Git commit SHA for reproducibility | Immutable |
| `venv_dir` | directory | `.venv/` virtual environment (optional) | Read-only after setup |
| `requirements_file` | file | `requirements.txt` for dependencies | Read-only |
| `use_venv` | boolean | Whether framework requires Python venv | Immutable |
| `patches_applied` | boolean | Whether source patches have been applied | Set once during setup |

**Storage Structure**:
```
frameworks/<framework_name>/
├── .git/                    # Git repository metadata
├── .venv/                   # Virtual environment (if use_venv=true)
│   ├── bin/python          # Python interpreter
│   ├── lib/pythonX.Y/      # Installed packages
│   └── pyvenv.cfg          # Venv configuration
├── requirements.txt         # Python dependencies
├── <framework_files>        # Framework source code
└── README.md               # Framework documentation
```

**Size Estimates**:
- BAEs: ~622MB (3MB source + 619MB venv)
- ChatDev: ~650MB (est. 4MB source + 646MB venv)
- GHSpec: ~50MB (Node.js project, no venv)

**Lifecycle**:
1. **Created**: During `setup_frameworks.py` execution
2. **Patched**: Framework-specific patches applied (e.g., ChatDev)
3. **Read-only**: Never modified during runs
4. **Destroyed**: Manually or when re-running setup

**Ownership**: `BaseAdapter` (via `get_shared_framework_path()`)

**Validation Rules**:
- MUST exist before any run starts
- MUST be on correct `commit_hash` (verified during setup)
- If `use_venv=true`, `.venv/bin/python` MUST exist and be executable
- Source code MUST NOT be modified during runs

---

### Entity 2: RunWorkspace

**Purpose**: Isolated directory for run-specific writable data and generated artifacts.

**Location Pattern**: `<experiment_root>/runs/<framework_name>/<run_id>/workspace/`

**Attributes**:

| Attribute | Type | Description | Mutability |
|-----------|------|-------------|------------|
| `run_id` | UUID | Unique identifier for this run | Immutable |
| `framework_name` | string | Framework that created this workspace | Immutable |
| `subdirectories` | list[directory] | Run-specific writable directories | Mutable |
| `created_at` | timestamp | When workspace was created | Immutable |
| `size_bytes` | integer | Total disk usage of workspace | Increases during run |

**Storage Structure (per framework)**:

**BAEs Workspace**:
```
workspace/
├── managed_system/          # Generated application code
│   ├── app.py              # Main application
│   ├── models/             # Data models
│   └── tests/              # Generated tests
└── database/               # Run-specific state
    └── context_store.json  # Execution context
```

**ChatDev Workspace**:
```
workspace/
└── WareHouse/              # Generated project artifacts
    └── ProjectName_*/      # Timestamped project directories
        ├── main.py
        ├── manual.md
        └── ...
```

**GHSpec Workspace**:
```
workspace/
# (Currently no subdirectories - GHSpec outputs to stdout/files)
```

**Size Estimates**:
- Per run: < 1MB (only generated artifacts)
- Per 6-run experiment: ~6MB total

**Lifecycle**:
1. **Created**: During `adapter.start()` via `create_workspace_structure()`
2. **Populated**: During run execution (framework writes artifacts)
3. **Archived**: After run completion (optional tar.gz)
4. **Retained**: Permanently for reproducibility

**Ownership**: Adapter-specific (BAeSAdapter, ChatDevAdapter, GHSpecAdapter)

**Validation Rules**:
- MUST be unique per run (enforced by UUID in path)
- MUST be writable by adapter process
- MUST NOT contain framework source code
- MUST be isolated (runs cannot access each other's workspaces)

---

### Entity 3: ExperimentRoot

**Purpose**: Top-level directory containing all experiment resources.

**Location Pattern**: `<experiments_dir>/<experiment_name>/`

**Attributes**:

| Attribute | Type | Description | Mutability |
|-----------|------|-------------|------------|
| `experiment_name` | string | Human-readable experiment identifier | Immutable |
| `config` | file | `config.yaml` experiment configuration | Read-only during runs |
| `frameworks_dir` | directory | `frameworks/` with shared resources | Read-only during runs |
| `runs_dir` | directory | `runs/` with per-run workspaces | Writable |
| `logs_dir` | directory | `logs/` with experiment-wide logs | Writable |

**Storage Structure**:
```
<experiment_name>/
├── config.yaml              # Experiment configuration
├── main.py                  # Execution entry point
├── frameworks/              # Shared framework resources
│   ├── baes/
│   ├── chatdev/
│   └── ghspec/
├── runs/                    # Per-run workspaces
│   ├── baes/
│   │   ├── <run_id_1>/
│   │   └── <run_id_2>/
│   ├── chatdev/
│   └── ghspec/
└── logs/                    # Experiment-wide logs
    └── experiment.log
```

**Lifecycle**:
1. **Generated**: By `scripts/new_experiment.py`
2. **Setup**: By `python templates/setup_frameworks.py`
3. **Executed**: By `python main.py`
4. **Archived**: Manually or via CI/CD

**Ownership**: Orchestrator (main.py)

---

## Relationships

### Relationship 1: ExperimentRoot → SharedFramework

- **Type**: One-to-Many (1 experiment : N frameworks)
- **Cardinality**: 1..3 (current: baes, chatdev, ghspec)
- **Direction**: ExperimentRoot contains SharedFramework
- **Implementation**: Directory hierarchy (`frameworks/<name>/`)
- **Lifecycle**: Created during setup, never modified during runs

**Invariants**:
- Each framework appears exactly once in `frameworks/`
- All enabled frameworks in `config.yaml` MUST have corresponding `frameworks/<name>/`

### Relationship 2: ExperimentRoot → RunWorkspace

- **Type**: One-to-Many (1 experiment : N runs)
- **Cardinality**: 0..* (unbounded, limited by max_runs config)
- **Direction**: ExperimentRoot contains RunWorkspace
- **Implementation**: Directory hierarchy (`runs/<framework>/<run_id>/workspace/`)
- **Lifecycle**: Created per run, accumulated over experiment

**Invariants**:
- Each `run_id` is unique across entire experiment
- Run directories never deleted (for reproducibility)

### Relationship 3: RunWorkspace → SharedFramework

- **Type**: Many-to-One (N workspaces : 1 framework)
- **Cardinality**: N..1 (many runs share one framework)
- **Direction**: RunWorkspace references SharedFramework
- **Implementation**: Path reference (no copying, no symlinks)
- **Access Pattern**: Read-only reference via `get_shared_framework_path()`

**Invariants**:
- Workspace NEVER contains framework copy
- All runs of same framework reference same SharedFramework
- SharedFramework MUST exist before creating workspace

**Concurrency**:
- Multiple workspaces can reference same framework simultaneously
- Framework read access is concurrent-safe (proven in research.md)
- No locking required

---

## State Transitions

### State Machine: SharedFramework Lifecycle

```
[NOT_EXISTS] 
    |
    | setup_frameworks.py: clone repo
    v
[CLONED]
    |
    | git checkout <commit_hash>
    v
[CHECKED_OUT]
    |
    | apply_patches (if framework=chatdev)
    v
[PATCHED]
    |
    | setup_venv_if_needed (if use_venv=true)
    v
[READY] ←────────────────┐
    |                     │
    | adapter.start()     │ (concurrent reads OK)
    v                     │
[IN_USE] ─────────────────┘
    |
    | (optional: manual cleanup)
    v
[DESTROYED]
```

**State Descriptions**:
- **NOT_EXISTS**: Framework directory doesn't exist
- **CLONED**: Git repository cloned to `frameworks/<name>/`
- **CHECKED_OUT**: On correct commit hash
- **PATCHED**: Framework-specific patches applied (ChatDev only)
- **READY**: Venv created and dependencies installed (if needed)
- **IN_USE**: Being referenced by one or more active runs (read-only)
- **DESTROYED**: Deleted manually or by re-running setup

**Valid Transitions**:
- NOT_EXISTS → CLONED (setup_frameworks.py)
- CLONED → CHECKED_OUT (git checkout)
- CHECKED_OUT → PATCHED (apply_patches)
- PATCHED → READY (setup_venv_if_needed)
- READY ↔ IN_USE (concurrent read access)
- * → DESTROYED (manual rm -rf or setup re-run)

**Invalid Transitions**:
- IN_USE → PATCHED (cannot modify while in use)
- IN_USE → DESTROYED (unsafe - would break active runs)

### State Machine: RunWorkspace Lifecycle

```
[NOT_EXISTS]
    |
    | adapter.start(): create_workspace_structure()
    v
[CREATED]
    |
    | os.environ['MANAGED_SYSTEM_PATH'] = workspace/managed_system
    v
[CONFIGURED]
    |
    | adapter.execute_step(): framework writes artifacts
    v
[POPULATING] ←───────────┐
    |                     │
    | (during execution)  │
    └─────────────────────┘
    |
    | adapter.stop(): archive workspace
    v
[COMPLETED]
    |
    | (retained for reproducibility)
    v
[ARCHIVED]
```

**State Descriptions**:
- **NOT_EXISTS**: Workspace directory doesn't exist yet
- **CREATED**: Subdirectories created via `create_workspace_structure()`
- **CONFIGURED**: Environment variables set to point to workspace
- **POPULATING**: Framework actively writing artifacts
- **COMPLETED**: Run finished, all artifacts written
- **ARCHIVED**: Workspace packaged into tar.gz (optional)

**Valid Transitions**:
- NOT_EXISTS → CREATED (create_workspace_structure)
- CREATED → CONFIGURED (set environment variables)
- CONFIGURED → POPULATING (framework execution)
- POPULATING → POPULATING (iterative writing)
- POPULATING → COMPLETED (execution finished)
- COMPLETED → ARCHIVED (optional archiving)

**Invalid Transitions**:
- POPULATING → CREATED (cannot reset during execution)
- ARCHIVED → POPULATING (workspace is read-only after archiving)

---

## Data Flow

### Setup Phase: Framework Preparation

```
┌─────────────────────┐
│ setup_frameworks.py │
└──────────┬──────────┘
           │
           ├─→ Clone repos to frameworks/
           │
           ├─→ Checkout commit hashes
           │
           ├─→ Apply patches (ChatDev)
           │
           └─→ Create venvs (if use_venv=true)
                    │
                    v
           ┌─────────────────┐
           │ SharedFramework │ (read-only)
           │     READY       │
           └─────────────────┘
```

### Execution Phase: Run Workflow

```
┌──────────────┐
│ adapter.start()│
└──────┬────────┘
       │
       ├─→ get_shared_framework_path('baes')
       │        │
       │        v
       │   frameworks/baes/ (reference only)
       │
       ├─→ get_framework_python('baes')
       │        │
       │        v
       │   frameworks/baes/.venv/bin/python
       │
       └─→ create_workspace_structure(['managed_system', 'database'])
                │
                v
       ┌─────────────────┐
       │  RunWorkspace   │ (writable)
       │   workspace/    │
       │   ├─managed_    │
       │   └─database/   │
       └─────────────────┘
                │
                v
       adapter.execute_step()
                │
                v
       Framework writes artifacts
       to workspace/managed_system/
```

---

## Constraints & Invariants

### Global Constraints

1. **No Framework Duplication**
   - Rule: Framework source MUST NOT exist in workspace
   - Enforcement: `create_workspace_structure()` validates subdirs list
   - Violation: RuntimeError raised

2. **Shared Venv Isolation**
   - Rule: `frameworks/<name>/.venv/` MUST be read-only during runs
   - Enforcement: File system permissions + adapter code review
   - Validation: No write operations in adapter code

3. **Run Artifact Isolation**
   - Rule: Each run writes only to its own `workspace/<run_id>/`
   - Enforcement: `workspace_path` contains unique run_id
   - Validation: Path validation in BaseAdapter.__init__

4. **Reproducibility**
   - Rule: Same `commit_hash` + same prompts = identical results
   - Enforcement: Git checkout verification, config immutability
   - Validation: Commit hash verification in setup_frameworks.py

### Entity-Specific Invariants

**SharedFramework**:
- Size MUST be stable after setup (no growth during runs)
- `.venv/bin/python` MUST exist if `use_venv=true`
- Patches MUST be idempotent (re-running has no effect)

**RunWorkspace**:
- Size MUST be < 10MB per run (warning if exceeded)
- Subdirectories MUST be created before framework execution
- Path MUST contain run_id for uniqueness

**ExperimentRoot**:
- `config.yaml` MUST be immutable once runs begin
- `frameworks/` MUST contain all enabled frameworks
- `runs/` MUST only contain completed run directories

---

## Usage Examples

### Example 1: BAEs Adapter Initialization

```python
class BAeSAdapter:
    def start(self):
        # Get shared framework (read-only reference)
        self.framework_dir = self.get_shared_framework_path('baes')
        # Returns: Path('/experiments/my-exp/frameworks/baes')
        
        # Get shared Python (from venv)
        self.python_path = self.get_framework_python('baes')
        # Returns: Path('/experiments/my-exp/frameworks/baes/.venv/bin/python')
        
        # Create workspace directories (writable)
        workspace_dirs = self.create_workspace_structure([
            'managed_system',
            'database'
        ])
        # Returns: {
        #   'managed_system': Path('.../workspace/managed_system'),
        #   'database': Path('.../workspace/database')
        # }
        
        self.managed_system_dir = workspace_dirs['managed_system']
        self.database_dir = workspace_dirs['database']
        
        # Set environment variables
        os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
        os.environ['BAE_CONTEXT_STORE_PATH'] = str(
            self.database_dir / "context_store.json"
        )
```

### Example 2: Concurrent Runs

```
Experiment: my-test
├── frameworks/
│   └── baes/            ← Shared (619MB venv)
│       └── .venv/
│
└── runs/
    └── baes/
        ├── run-001/     ← References frameworks/baes/
        │   └── workspace/
        │       ├── managed_system/ (500KB artifacts)
        │       └── database/ (50KB state)
        │
        └── run-002/     ← Also references frameworks/baes/
            └── workspace/
                ├── managed_system/ (600KB artifacts)
                └── database/ (45KB state)

Disk Usage:
- Shared framework: 619MB (one copy)
- Run 001 artifacts: 550KB
- Run 002 artifacts: 645KB
- Total: 620MB (vs 1240MB if copied)
- Savings: 50%
```

---

## Migration Notes

### Backward Compatibility

**Old Structure** (pre-refactor):
```
runs/baes/<run_id>/workspace/
├── baes_framework/      ← Framework copy (622MB)
│   ├── .venv/
│   └── baes/
├── managed_system/
└── database/
```

**New Structure** (post-refactor):
```
frameworks/baes/         ← Shared framework (622MB)
├── .venv/
└── baes/

runs/baes/<run_id>/workspace/
├── managed_system/      ← Only artifacts
└── database/
```

**Adapter Fallback Logic**:
```python
def get_shared_framework_path(self, name):
    # Try new location first
    shared = self.experiment_root / "frameworks" / name
    if shared.exists():
        return shared
    
    # Fallback to old workspace location
    old = Path(self.workspace_path) / f"{name}_framework"
    if old.exists():
        logger.warning("Using deprecated workspace framework")
        return old
    
    raise RuntimeError(f"Framework '{name}' not found")
```

---

## Summary

| Entity | Purpose | Size | Mutability | Lifetime |
|--------|---------|------|------------|----------|
| SharedFramework | Shared framework code + venv | ~622MB | Read-only | Experiment |
| RunWorkspace | Per-run artifacts | <1MB | Writable | Permanent |
| ExperimentRoot | Container for all resources | ~1.25GB | Mixed | Experiment |

**Key Benefits**:
- 99.8% disk reduction per run (622MB → 1MB)
- Instant run startup (no venv creation)
- Clear separation of concerns (shared vs. run-specific)
- Concurrent access safety (proven read-only)
