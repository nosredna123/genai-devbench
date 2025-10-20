# Logging System

## Overview

The experiment framework uses a **per-run, per-step, component-separated logging system** to provide comprehensive observability for experiment execution, debugging, and analysis.

## Architecture

### Log Directory Structure

```
runs/<framework>/<run_id>/
├── logs/
│   ├── run.log                     # Pre-run setup, post-run cleanup
│   ├── reconciliation.log          # Token reconciliation attempts (cross-step)
│   └── step_001/                   # Step-specific logs
│       ├── orchestrator.log        # Step lifecycle, retries, timeouts
│       ├── adapter.log             # Framework API calls, process management
│       ├── metrics.log             # Token counting, API tracking
│       └── validator.log           # Health checks, downtime detection
│   └── step_002/
│       └── ... (same structure)
├── logs_summary.txt                # Git-tracked summary (human-readable)
├── metadata.json
├── metrics.json
└── run.tar.gz                      # Archive includes logs/
```

### Component Separation

Each component logs to its own file for clean separation of concerns:

| Component | File | Purpose |
|-----------|------|---------|
| **Orchestrator** | `orchestrator.log` (per-step) / `run.log` | Run lifecycle, step execution, retries, timeouts |
| **Adapter** | `adapter.log` (per-step) | Framework-specific operations, API calls, process management |
| **Metrics** | `metrics.log` (per-step) | Token counting, API call tracking, cost calculation |
| **Validator** | `validator.log` (per-step) | Health checks, downtime detection, service availability |
| **Reconciliation** | `reconciliation.log` (run-level) | Token reconciliation, verification attempts |

## Implementation

### LogContext Class

The `LogContext` singleton manages run and step context for all loggers:

```python
from src.utils.logger import LogContext

# At run start (in runner)
log_context = LogContext.get_instance()
log_context.set_run_context(
    run_id="abc123",
    framework="baes",
    logs_dir=Path("runs/baes/abc123/logs")
)

# Before each step
log_context.set_step_context(step_num=1)

# After each step
log_context.clear_step_context()
```

### Component Loggers

Each module creates a logger with its component name:

```python
from src.utils.logger import get_logger

# In adapters
logger = get_logger(__name__, component="adapter")

# In orchestrator/runner.py
logger = get_logger(__name__, component="orchestrator")

# In metrics_collector.py
logger = get_logger(__name__, component="metrics")

# In validator.py
logger = get_logger(__name__, component="validator")

# In usage_reconciler.py
logger = get_logger(__name__, component="reconciliation")
```

### Automatic Log File Creation

The logger automatically:
1. Creates step directories (`step_001/`, `step_002/`, etc.) as needed
2. Routes logs to appropriate files based on component and current step
3. Falls back to console-only logging if no context is set

## Log Formats

### JSON Structured Logging

All logs use JSON format for machine-readability:

```json
{
  "timestamp": "2025-10-20T14:23:45Z",
  "level": "INFO",
  "module": "runner",
  "message": "Step completed successfully",
  "run_id": "abc123",
  "step": 1,
  "event": "step_complete"
}
```

### Log Summary

The `logs_summary.txt` provides a human-readable overview:

```
================================================================================
EXPERIMENT RUN SUMMARY
================================================================================
Run ID: abc123
Framework: baes
Model: gpt-4o-2024-08-06
Started: 2025-10-20T14:23:45Z
Completed: 2025-10-20T14:45:12Z
Duration: 21m 27s

================================================================================
STEP EXECUTION SUMMARY
================================================================================
Step 001: SUCCESS (duration: 2m 34s, retries: 0)
  - API Calls: 12
  - Tokens (prompt/completion/total): 1234 / 567 / 1801
  - LLM Requests: 8
  
Step 003: SUCCESS (duration: 1m 45s, retries: 0)
  - API Calls: 0
  - Tokens (prompt/completion/total): 0 / 0 / 0
  - LLM Requests: 0
  - Note: Template-based generation (no LLM calls)
...
```

## Usage

### Debugging a Specific Step

```bash
# View all events for step 3
cat runs/baes/abc123/logs/step_003/orchestrator.log
cat runs/baes/abc123/logs/step_003/adapter.log

# Search for errors in step 3
jq 'select(.level == "ERROR")' runs/baes/abc123/logs/step_003/*.log
```

### Analyzing Token Usage

```bash
# Extract token metrics from all steps
for step in runs/baes/abc123/logs/step_*/; do
    echo "=== $(basename $step) ==="
    jq 'select(.message | contains("token"))' $step/metrics.log
done
```

### Tracking Reconciliation

```bash
# View all reconciliation attempts
cat runs/baes/abc123/logs/reconciliation.log | jq 'select(.event == "reconciliation_attempt")'
```

## Git Integration

### What's Tracked

✅ **Tracked in Git:**
- `logs_summary.txt` - Human-readable summary (~10KB)
- `metadata.json` - Run metadata
- `metrics.json` - Final metrics

❌ **Not Tracked (in .gitignore):**
- `logs/` - Full logs directory (archived in run.tar.gz)
- `run.tar.gz` - Compressed archive
- `workspace/` - Framework workspace
- `artifacts/` - Generated code

### Rationale

- **Summaries in git**: Easy to review in PRs, compare runs, track experiment evolution
- **Full logs in archives**: Deep debugging when needed, keeps repo lightweight
- **Best of both worlds**: Quick overview vs. comprehensive debugging data

## Archive Integration

All logs are included in the `run.tar.gz` archive for long-term preservation:

```bash
# Extract logs from archive
tar -xzf runs/baes/abc123/run.tar.gz logs/

# View logs from archive without extraction
tar -xzOf runs/baes/abc123/run.tar.gz logs/step_003/adapter.log | jq .
```

## Benefits

1. **Debugging Isolation**: Quickly identify which component failed
2. **Step-Level Analysis**: Focus on specific steps without noise
3. **Parallel Investigation**: Multiple researchers can analyze different aspects
4. **Automated Analysis**: Scripts can parse component-specific logs
5. **Historical Tracking**: Git summaries show experiment evolution
6. **Reproducibility**: Complete logs in archives for deep investigation

## Migration from Old System

### Before (Global Logs)

```python
logger = get_logger(__name__)  # Logs to console only
```

Logs were:
- Not saved per-run
- Mixed together (all components)
- Lost after run completion

### After (Per-Run, Per-Step)

```python
logger = get_logger(__name__, component="adapter")  # Logs to step file
```

Logs are now:
- Saved per-run under `runs/<framework>/<run_id>/logs/`
- Separated by component for clarity
- Organized by step in directories
- Archived in `run.tar.gz`
- Summarized in git-tracked `logs_summary.txt`

## See Also

- `src/utils/logger.py` - Logger implementation
- `src/utils/log_summary.py` - Summary generation
- `src/orchestrator/runner.py` - LogContext usage
- `docs/troubleshooting.md` - Debugging guide
