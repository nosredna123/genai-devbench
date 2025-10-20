# Run Artifacts Organization

## Problem

Based on the current implementation, when ChatDev executes, it creates artifacts in multiple locations:

### Current Structure (Temporary Workspace)
```
/tmp/chatdev_xxx/               # Temporary workspace per run
├── chatdev_framework/          # Cloned ChatDev repository
│   ├── .venv/                  # Virtual environment
│   ├── WareHouse/              # ⚠️ ChatDev's output (generated code)
│   │   └── BAEs_Step1_xxx_BAEs_Experiment_20251009111220/
│   │       ├── main.py
│   │       ├── manual.md
│   │       └── ...             # All generated project files
│   └── CompanyConfig/          # ChatDev internal configs
```

### Current Permanent Storage
```
runs/
└── chatdev/
    └── <run-id>/               # e.g., reconciliation_test_20251009_142201
        └── metrics.json        # ⚠️ Only metrics, no generated code!
```

## Issues

1. **Missing Artifacts**: Generated code (WareHouse/) is in temp directory and gets deleted after cleanup
2. **No Reproducibility**: Can't inspect the actual code ChatDev generated for a specific run
3. **Incomplete Archive**: Only metrics.json is saved, but not the actual deliverable
4. **Debugging Difficulty**: Can't examine ChatDev's output after the fact

## Proposed Solution

### Option 1: Copy WareHouse to runs/ (Recommended)
```
runs/
└── chatdev/
    └── <run-id>/
        ├── metrics.json              # Experiment metrics
        ├── artifacts/                # NEW: Generated code
        │   └── BAEs_Step1_xxx_*/     # ChatDev's WareHouse project
        │       ├── main.py
        │       ├── manual.md
        │       └── ...
        └── framework_info.json       # NEW: Framework metadata (commit, venv packages, etc.)
```

**Pros:**
- Complete artifact preservation
- Easy to inspect generated code
- Supports reproducibility validation
- Clean separation: runs/ has everything permanent

**Cons:**
- Slightly more disk space (but code is usually small)
- Need to copy WareHouse after each step

### Option 2: Symlink from runs/ to temp
```
runs/
└── chatdev/
    └── <run-id>/
        ├── metrics.json
        └── artifacts -> /tmp/chatdev_xxx/chatdev_framework/WareHouse/
```

**Pros:**
- No disk duplication
- Instant access

**Cons:**
- ⚠️ Breaks after cleanup (temp dir is deleted)
- Not suitable for long-term storage

### Option 3: Archive WareHouse as tar.gz
```
runs/
└── chatdev/
    └── <run-id>/
        ├── metrics.json
        └── artifacts.tar.gz          # Compressed WareHouse
```

**Pros:**
- Minimal disk space
- Complete preservation

**Cons:**
- Need to extract to inspect
- Extra compression/decompression overhead

## Recommendation

**Go with Option 1** because:

1. **Reproducibility**: Essential for T073 (ChatDev Reproducibility Validation)
2. **Debugging**: Can examine what ChatDev actually generated
3. **Archival**: Aligns with the archiver's purpose (complete run preservation)
4. **Analysis**: Can compare generated code across runs
5. **Transparency**: Full visibility into framework behavior

## Implementation

Update `ChatDevAdapter.execute_step()` to:

```python
def execute_step(self, step_num, prompt, previous_output):
    # ... existing execution code ...
    
    # After successful execution, copy WareHouse to run directory
    warehouse_path = self.framework_dir / "WareHouse"
    if warehouse_path.exists():
        artifacts_dir = Path(self.output_dir) / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        # Copy the specific project directory
        for project_dir in warehouse_path.glob(f"BAEs_Step{step_num}_*"):
            shutil.copytree(
                project_dir,
                artifacts_dir / project_dir.name,
                dirs_exist_ok=True
            )
    
    return result
```

## Directory Structure After Implementation

```
genai-devbench/
├── runs/
│   ├── chatdev/
│   │   ├── run_20251009_142201/
│   │   │   ├── metrics.json                    # Experiment metrics
│   │   │   └── artifacts/                      # Generated code
│   │   │       ├── BAEs_Step1_xxx_*/          # Step 1 output
│   │   │       ├── BAEs_Step2_xxx_*/          # Step 2 output (if 6-step)
│   │   │       └── ...
│   │   └── run_20251009_143045/
│   │       ├── metrics.json
│   │       └── artifacts/
│   ├── baes/
│   │   └── ...                                # Similar structure
│   └── ghspec/
│       └── ...                                # Similar structure
├── logs/
│   └── ...                                    # Execution logs
└── src/
    └── ...                                    # Source code
```

## Benefits

1. **Complete Run Data**: Everything in one place (runs/<framework>/<run-id>/)
2. **Git-Friendly**: Can .gitignore runs/*/artifacts/ if too large
3. **Reconciliation-Ready**: Metrics + artifacts for full analysis
4. **Reproducibility**: Can compare artifacts between runs
5. **Debugging**: Inspect generated code without running again

## Migration Notes

- Existing runs won't have artifacts/ (that's okay - they're pre-reconciliation test runs)
- New runs will automatically include artifacts/
- .gitignore should exclude `runs/*/artifacts/` if artifacts are large
- Archive tool should include artifacts/ in the zip
