# Git-Friendly Runs Implementation

**Implementation Date:** October 15, 2025  
**Commit:** a4c7b01

## Overview

The `runs/` directory is now **Git-tracked** in a selective manner that enables version control of experimental metrics while keeping the repository size small by ignoring large artifacts.

## Implementation Summary

### 1. Fresh Start ✅

All existing run data was deleted to start with a clean slate:

```bash
rm -rf runs/*
```

This ensured we could implement the new structure without legacy data conflicts.

### 2. Selective Git Tracking ✅

Modified `.gitignore` to implement **selective tracking**:

#### Tracked Files (Version Controlled)
- `runs_manifest.json` - Quick lookup index
- `*/*/metrics.json` - Token usage metrics
- `*/*/metadata.json` - Run configuration
- `*/*/commit.txt` - Git commit hash
- `*/*/*.md` - Analysis reports

**Size per run:** ~10 KB

#### Ignored Files (Local Only)
- `*/*/workspace/` - Source code workspace
- `*/*/artifacts/` - Generated artifacts
- `*/*/*.tar.gz` - Compressed archives
- `*/*/*.zip` - Compressed archives
- `*/*/*.log` - Log files

**Size per run:** ~500 MB

#### Size Comparison

| Aspect | Size |
|--------|------|
| **Tracked per run** | ~10 KB |
| **Ignored per run** | ~500 MB |
| **Ratio** | 1:50,000 |
| **100 runs (Git)** | ~1 MB |
| **100 runs (Disk)** | ~50 GB |

### 3. Manifest Manager ✅

Created `src/orchestrator/manifest_manager.py` for fast run lookups without file scanning.

#### Key Functions

```python
# Get current manifest
manifest = get_manifest()

# Add/update a run
update_manifest(run_data)

# Query runs
runs = find_runs(
    framework='chatdev',
    verification_status='verified',
    min_tokens=100000
)

# Rebuild from files
rebuild_manifest()

# Remove a run
remove_run(run_id)
```

#### Manifest Schema

```json
{
  "version": "1.0",
  "last_updated": "2025-10-15T10:30:00Z",
  "total_runs": 2,
  "frameworks": {
    "chatdev": 1,
    "baes": 1,
    "ghspec": 0
  },
  "runs": [
    {
      "run_id": "abc123...",
      "framework": "chatdev",
      "path": "chatdev/abc123...",
      "start_time": "2025-10-15T08:50:59Z",
      "end_time": "2025-10-15T09:25:22Z",
      "verification_status": "verified",
      "total_tokens_in": 287761,
      "total_tokens_out": 91329
    }
  ]
}
```

## Directory Structure

```
runs/
├── runs_manifest.json          ← Git tracked ✅
├── chatdev/
│   └── {run-id}/
│       ├── metrics.json        ← Git tracked ✅
│       ├── metadata.json       ← Git tracked ✅
│       ├── commit.txt          ← Git tracked ✅
│       ├── reconciliation_analysis.md  ← Git tracked ✅
│       ├── workspace/          ← Git ignored ❌
│       ├── artifacts/          ← Git ignored ❌
│       └── run.tar.gz          ← Git ignored ❌
├── baes/
└── ghspec/
```

## Benefits

### 1. Git Tracking
- ✅ View exact metric changes with `git diff`
- ✅ Track verification status progression over time
- ✅ Compare experiments across commits
- ✅ Rollback to previous experimental states
- ✅ Audit trail of all metric changes

### 2. Manifest Performance
- ✅ Instant lookups without file system scanning
- ✅ Quick filtering by framework/status
- ✅ Generate reports without loading all data
- ✅ Human-readable experiment overview

### 3. Repository Efficiency
- ✅ Keep repo small (~10 KB per run)
- ✅ Fast Git operations
- ✅ Large artifacts still available locally
- ✅ No risk of accidentally committing huge files

## Testing

Verified selective tracking works correctly:

```bash
# Create test run structure
mkdir -p runs/chatdev/test-abc-123/{workspace,artifacts}
echo '{"test": "metrics"}' > runs/chatdev/test-abc-123/metrics.json
echo '{"test": "metadata"}' > runs/chatdev/test-abc-123/metadata.json
echo 'abc123def' > runs/chatdev/test-abc-123/commit.txt
echo '# Analysis' > runs/chatdev/test-abc-123/reconciliation_analysis.md
echo 'workspace file' > runs/chatdev/test-abc-123/workspace/some_code.py
echo 'artifact file' > runs/chatdev/test-abc-123/artifacts/output.txt
echo 'large archive' > runs/chatdev/test-abc-123/run.tar.gz
echo 'log data' > runs/chatdev/test-abc-123/run.log

# Check what Git tracks
git add -A runs/
git status --short runs/
```

**Result:**
```
A  runs/chatdev/test-abc-123/commit.txt
A  runs/chatdev/test-abc-123/metadata.json
A  runs/chatdev/test-abc-123/metrics.json
A  runs/chatdev/test-abc-123/reconciliation_analysis.md
A  runs/runs_manifest.json
```

**Ignored:**
- `runs/chatdev/test-abc-123/workspace/`
- `runs/chatdev/test-abc-123/artifacts/`
- `runs/chatdev/test-abc-123/run.tar.gz`
- `runs/chatdev/test-abc-123/run.log`

✅ **Test Passed:** Only lightweight metadata tracked, large artifacts ignored.

## Usage Examples

### Query Verified Runs

```python
from src.orchestrator.manifest_manager import find_runs

# Find all verified ChatDev runs
verified_runs = find_runs(
    framework='chatdev',
    verification_status='verified'
)

for run in verified_runs:
    print(f"{run['run_id']}: {run['total_tokens_in'] + run['total_tokens_out']} tokens")
```

### Rebuild Manifest

If the manifest gets out of sync:

```python
from src.orchestrator.manifest_manager import rebuild_manifest

rebuild_manifest()
```

### View Git History

```bash
# See metric changes over time
git log -p runs/chatdev/abc123.../metrics.json

# Compare verification status between commits
git diff HEAD~1 HEAD runs/runs_manifest.json

# View all tracked run metrics
git ls-files runs/
```

## Integration Points

The manifest manager needs to be integrated into:

1. **Orchestrator** (`src/orchestrator/runner.py`)
   - Call `update_manifest()` after experiment completion
   - Update when reconciliation status changes

2. **Reconciler** (`src/orchestrator/usage_reconciler.py`)
   - Update manifest when verification status changes

3. **Analysis Scripts**
   - Use `find_runs()` instead of file system scanning
   - Query by framework, status, token counts

## Future Work

- [ ] Integrate manifest updates into orchestrator
- [ ] Add manifest queries to analysis scripts
- [ ] Implement automatic Git commits for completed runs
- [ ] Add CLI commands for manifest queries
- [ ] Create visualization of verification status progression

## Related Documentation

- [Double-Check Verification](./double_check_verification.md)
- [Run Artifacts Organization](./run_artifacts_organization.md)
- [Metrics Collection](./metrics.md)
