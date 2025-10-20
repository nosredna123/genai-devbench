# Asynchronous Usage API Design

## Problem Statement

The OpenAI Usage API has an unpredictable reporting delay (5-15 minutes to hours), making real-time token counting during test execution unreliable. Currently, we query the Usage API immediately after step execution, which consistently returns 0 tokens due to this delay.

**Requirements:**
1. Token data MUST come from OpenAI Usage API (official source of truth)
2. Token counts MUST be accurate and framework-specific
3. Metrics file MUST eventually contain final token counts
4. System MUST handle API reporting delays gracefully

## Current Architecture Analysis

### Data Flow (Current)

```
Framework Execution
  ↓
Adapter.execute_step()
  ↓ (immediately after)
Adapter.fetch_usage_from_openai()  ← Returns 0 (too soon!)
  ↓
MetricsCollector.record_step(tokens_in=0, tokens_out=0)
  ↓
metrics.json saved with 0 tokens
  ↓
Archive created
```

### Key Components

1. **ChatDevAdapter** (`src/adapters/chatdev_adapter.py`):
   - Records `_step_start_time` before execution
   - Calls `fetch_usage_from_openai()` after execution
   - Passes token counts to MetricsCollector

2. **MetricsCollector** (`src/orchestrator/metrics_collector.py`):
   - `record_step()`: Stores per-step metrics
   - `get_aggregate_metrics()`: Computes final metrics
   - No update mechanism after initial save

3. **OrchestratorRunner** (`src/orchestrator/runner.py`):
   - Line 371: Saves `metrics.json` once
   - Line 378: Creates archive
   - No mechanism to update metrics later

4. **Archiver** (`src/orchestrator/archiver.py`):
   - Creates `run.tar.gz` with workspace + metrics
   - Computes SHA-256 hash
   - Archive is immutable after creation

### Critical Observations

1. ✅ **Time windows are recorded**: `start_timestamp` and `end_timestamp` are stored in metrics
2. ✅ **Framework attribution works**: Sequential execution + time windows
3. ❌ **No update mechanism**: metrics.json written once, never updated
4. ❌ **Archive is immutable**: Changing metrics.json invalidates SHA-256 hash
5. ✅ **Constitution requires**: "Compare local token counts against OpenAI Usage API" (post-run validation)

## Design Approaches

### Approach 1: Post-Run Update Script (Recommended)

**Concept**: Separate background process that updates metrics after API data becomes available.

#### Architecture

```
┌─────────────────┐
│  Run Complete   │
│  metrics.json   │
│  (tokens=0)     │
└────────┬────────┘
         │
         │ 5-60 minutes later...
         │
         ▼
┌─────────────────────────┐
│  Usage Reconciliation   │
│  (Background Process)   │
├─────────────────────────┤
│ 1. Read metrics.json    │
│ 2. Query Usage API      │
│    (use time windows)   │
│ 3. Update token counts  │
│ 4. Save updated file    │
│ 5. Log reconciliation   │
└─────────────────────────┘
```

#### Implementation

**New Component**: `src/orchestrator/usage_reconciler.py`

```python
class UsageReconciler:
    """Updates metrics with Usage API data after reporting delay."""
    
    def __init__(self, runs_dir: Path = Path("runs")):
        self.runs_dir = runs_dir
    
    def reconcile_run(self, run_id: str, framework: str) -> Dict[str, Any]:
        """
        Update a single run's metrics with Usage API data.
        
        Args:
            run_id: Run identifier
            framework: Framework name (baes, chatdev, ghspec)
            
        Returns:
            Reconciliation report with updated counts
        """
        # 1. Load existing metrics.json
        metrics_file = self.runs_dir / framework / run_id / "metrics.json"
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        # 2. Extract time windows from steps
        reconciliation_report = {
            'run_id': run_id,
            'framework': framework,
            'reconciled_at': datetime.utcnow().isoformat() + 'Z',
            'steps_updated': []
        }
        
        for step in metrics['steps']:
            # Skip if already has tokens
            if step.get('tokens_in', 0) > 0 or step.get('tokens_out', 0) > 0:
                continue
            
            # Get time window from step metadata
            # (Need to add this to step recording!)
            start_time = step.get('start_timestamp')
            end_time = step.get('end_timestamp')
            
            if not start_time or not end_time:
                logger.warning(f"Step {step['step_number']} missing timestamps")
                continue
            
            # 3. Query Usage API for this time window
            tokens_in, tokens_out = self._fetch_usage(
                start_timestamp=start_time,
                end_timestamp=end_time
            )
            
            # 4. Update step
            step['tokens_in'] = tokens_in
            step['tokens_out'] = tokens_out
            step['reconciled'] = True
            
            reconciliation_report['steps_updated'].append({
                'step': step['step_number'],
                'tokens_in': tokens_in,
                'tokens_out': tokens_out
            })
        
        # 5. Recompute aggregate metrics
        total_in = sum(s['tokens_in'] for s in metrics['steps'])
        total_out = sum(s['tokens_out'] for s in metrics['steps'])
        
        metrics['aggregate_metrics']['TOK_IN'] = total_in
        metrics['aggregate_metrics']['TOK_OUT'] = total_out
        
        # Recompute AEI (depends on tokens)
        autr = metrics['aggregate_metrics']['AUTR']
        aei = autr / math.log(1 + total_in) if total_in > 0 else 0.0
        metrics['aggregate_metrics']['AEI'] = aei
        
        # 6. Mark as reconciled
        metrics['usage_api_reconciliation'] = reconciliation_report
        
        # 7. Save updated metrics
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Reconciled {run_id}: {total_in:,} input, {total_out:,} output tokens")
        
        return reconciliation_report
    
    def reconcile_all_pending(self, max_age_minutes: int = 60) -> List[Dict]:
        """
        Find and reconcile all runs with missing token data.
        
        Args:
            max_age_minutes: Only reconcile runs older than this
            
        Returns:
            List of reconciliation reports
        """
        results = []
        cutoff_time = time.time() - (max_age_minutes * 60)
        
        for framework_dir in self.runs_dir.iterdir():
            if not framework_dir.is_dir():
                continue
            
            framework = framework_dir.name
            
            for run_dir in framework_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                
                metrics_file = run_dir / "metrics.json"
                if not metrics_file.exists():
                    continue
                
                # Check if run is old enough
                if metrics_file.stat().st_mtime > cutoff_time:
                    continue
                
                # Check if needs reconciliation
                with open(metrics_file) as f:
                    metrics = json.load(f)
                
                if metrics.get('usage_api_reconciliation'):
                    continue  # Already reconciled
                
                # Check if has zero tokens
                total_tokens = metrics.get('aggregate_metrics', {}).get('TOK_IN', 0)
                if total_tokens > 0:
                    continue  # Already has token data
                
                # Reconcile this run
                try:
                    report = self.reconcile_run(run_dir.name, framework)
                    results.append(report)
                except Exception as e:
                    logger.error(f"Failed to reconcile {framework}/{run_dir.name}: {e}")
        
        return results
```

**New Script**: `runners/reconcile_usage.sh`

```bash
#!/bin/bash
# Reconcile token usage data from OpenAI Usage API
# Run this periodically (e.g., hourly cron job) to update runs with missing token data

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

source .venv/bin/activate
set -a
source .env
set +a

export PYTHONPATH="$PROJECT_ROOT"

python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.utils.logger import get_logger

logger = get_logger(__name__)

reconciler = UsageReconciler()

# Reconcile runs older than 30 minutes
results = reconciler.reconcile_all_pending(max_age_minutes=30)

if results:
    logger.info(f"Reconciled {len(results)} runs")
    for report in results:
        steps_updated = len(report['steps_updated'])
        logger.info(f"  {report['framework']}/{report['run_id']}: {steps_updated} steps updated")
else:
    logger.info("No runs need reconciliation")
EOF
```

**Cron Job** (optional):

```cron
# Update token usage every hour
0 * * * * cd /path/to/genai-devbench && ./runners/reconcile_usage.sh >> logs/reconciliation.log 2>&1
```

#### Pros
- ✅ Doesn't block run completion
- ✅ Simple, independent process
- ✅ Can retry failed reconciliations
- ✅ No changes to archive/hash (metrics.json not in archive yet)
- ✅ Works with any delay duration
- ✅ Easy to test and debug
- ✅ Can run manually or automated (cron)

#### Cons
- ⚠️ Metrics initially incomplete (shows 0 tokens)
- ⚠️ Requires separate execution step
- ⚠️ Need to track which runs are reconciled

---

### Approach 2: Delayed Save with Retry

**Concept**: Don't save metrics immediately; wait and retry until tokens are available.

#### Implementation

```python
def execute_single_run(self) -> Dict[str, Any]:
    # ... existing code ...
    
    # End metrics collection
    self.metrics_collector.end_run()
    
    # Try to fetch usage with retries
    MAX_RETRIES = 3
    RETRY_DELAYS = [5 * 60, 15 * 60, 30 * 60]  # 5min, 15min, 30min
    
    for attempt, delay in enumerate(RETRY_DELAYS, 1):
        logger.info(f"Attempt {attempt}/{MAX_RETRIES} to fetch usage data")
        
        # Update all step token counts
        for step_num in range(1, 7):
            step_data = self.metrics_collector.steps_data.get(step_num)
            if not step_data:
                continue
            
            tokens_in, tokens_out = self.adapter.fetch_usage_from_openai(
                start_timestamp=step_data['start_timestamp'],
                end_timestamp=step_data['end_timestamp']
            )
            
            if tokens_in > 0 or tokens_out > 0:
                step_data['tokens_in'] = tokens_in
                step_data['tokens_out'] = tokens_out
        
        # Check if we got data
        total_tokens = sum(s.get('tokens_in', 0) for s in self.metrics_collector.steps_data.values())
        
        if total_tokens > 0:
            logger.info("Usage data received!")
            break
        
        if attempt < MAX_RETRIES:
            logger.info(f"No usage data yet, waiting {delay}s before retry...")
            time.sleep(delay)
    
    # Continue with metrics saving...
```

#### Pros
- ✅ Metrics file complete when saved
- ✅ No separate process needed
- ✅ Simple linear flow

#### Cons
- ❌ Blocks run completion for 5-50 minutes
- ❌ May still get 0 tokens if delay > 30 min
- ❌ Wastes compute resources waiting
- ❌ Bad UX (appears hung)
- ❌ Complicates error handling

---

### Approach 3: Dual Metrics Files

**Concept**: Save preliminary metrics immediately, then save final metrics after reconciliation.

#### Implementation

```
runs/chatdev/run-abc123/
├── metrics_preliminary.json    # Saved immediately (tokens=0)
├── metrics.json                 # Saved after reconciliation (tokens=actual)
├── reconciliation.json          # Reconciliation report
└── run.tar.gz                   # Archive with preliminary metrics
```

#### Pros
- ✅ Run completes immediately
- ✅ Clear distinction between preliminary/final
- ✅ Analysis can check for final metrics first

#### Cons
- ⚠️ Two source of truth files
- ⚠️ Analysis needs to handle both cases
- ⚠️ More complex file structure

---

### Approach 4: Async Background Thread (During Run)

**Concept**: Start background thread during run that waits and updates metrics.

#### Implementation

```python
import threading

class AsyncUsageUpdater(threading.Thread):
    def __init__(self, metrics_file, steps_data, adapter):
        super().__init__(daemon=True)
        self.metrics_file = metrics_file
        self.steps_data = steps_data
        self.adapter = adapter
    
    def run(self):
        # Wait 30 minutes
        time.sleep(30 * 60)
        
        # Update metrics
        # ... (similar to Approach 1)
```

#### Pros
- ✅ Automatic, no manual trigger
- ✅ Metrics eventually updated

#### Cons
- ❌ Complex lifecycle management
- ❌ Thread outlives test process
- ❌ Hard to test
- ❌ Resource leaks if process crashes

---

## Recommendation: Approach 1 (Post-Run Update Script)

### Why?

1. **Aligns with Constitution**: "Compare local token counts against OpenAI Usage API" suggests post-run validation
2. **Non-blocking**: Doesn't delay experiment completion
3. **Reliable**: Works regardless of API delay duration
4. **Testable**: Can test reconciliation independently
5. **Simple**: Clean separation of concerns
6. **Flexible**: Run manually or automated

### Implementation Plan

1. **Phase 1: Add timestamps to step data** (Required for reconciliation)
   - Modify `MetricsCollector.record_step()` to accept start/end timestamps
   - Update adapters to pass timestamps

2. **Phase 2: Create UsageReconciler**
   - Implement `src/orchestrator/usage_reconciler.py`
   - Add reconciliation logic
   - Handle edge cases (missing data, API errors)

3. **Phase 3: Create reconciliation script**
   - Implement `runners/reconcile_usage.sh`
   - Add CLI options (framework filter, run-id, etc.)

4. **Phase 4: Documentation & Testing**
   - Document reconciliation workflow
   - Add tests for reconciler
   - Update quickstart guide

5. **Phase 5: Automation (Optional)**
   - Add cron job example
   - Consider GitHub Actions workflow
   - Add reconciliation status to analysis

### Required Changes

#### 1. MetricsCollector Enhancement

```python
# src/orchestrator/metrics_collector.py

def record_step(
    self,
    step_num: int,
    command: str,
    duration_seconds: float,
    success: bool,
    retry_count: int,
    hitl_count: int,
    tokens_in: int,
    tokens_out: int,
    start_timestamp: int,  # NEW
    end_timestamp: int      # NEW
) -> None:
    """Record metrics for a single step."""
    self.steps_data[step_num] = {
        'step_number': step_num,
        'command': command,
        'duration_seconds': duration_seconds,
        'success': success,
        'retry_count': retry_count,
        'hitl_count': hitl_count,
        'tokens_in': tokens_in,
        'tokens_out': tokens_out,
        'start_timestamp': start_timestamp,  # NEW
        'end_timestamp': end_timestamp        # NEW
    }
```

#### 2. Adapter Update

```python
# src/adapters/chatdev_adapter.py

# In execute_step():
start_timestamp = self._step_start_time
end_timestamp = int(time.time())

# Pass to metrics collector
metrics_collector.record_step(
    step_num=step_num,
    command=task,
    duration_seconds=duration,
    success=True,
    retry_count=0,
    hitl_count=hitl_count,
    tokens_in=tokens_in,  # Will be 0 initially
    tokens_out=tokens_out,  # Will be 0 initially
    start_timestamp=start_timestamp,  # NEW
    end_timestamp=end_timestamp        # NEW
)
```

#### 3. Metrics Schema Update

```json
{
  "run_id": "abc-123",
  "steps": [
    {
      "step_number": 1,
      "command": "Create...",
      "duration_seconds": 432.69,
      "success": true,
      "retry_count": 0,
      "hitl_count": 0,
      "tokens_in": 0,           // Initially 0
      "tokens_out": 0,          // Initially 0
      "start_timestamp": 1760015386,  // NEW
      "end_timestamp": 1760015878      // NEW
    }
  ],
  "usage_api_reconciliation": {  // Added after reconciliation
    "reconciled_at": "2025-10-09T14:00:00Z",
    "steps_updated": [
      {
        "step": 1,
        "tokens_in": 84604,
        "tokens_out": 23275
      }
    ]
  }
}
```

### Usage Workflow

```bash
# Run experiment
./runners/run_experiment.sh chatdev

# Metrics saved with tokens=0
# metrics.json: {"TOK_IN": 0, "TOK_OUT": 0}

# Wait 30-60 minutes for Usage API to update

# Reconcile token counts
./runners/reconcile_usage.sh

# Metrics now updated
# metrics.json: {"TOK_IN": 84604, "TOK_OUT": 23275, "usage_api_reconciliation": {...}}

# Run analysis (uses updated metrics)
./runners/analyze_results.sh
```

## Alternative: Quick Win Approach

If you want a simpler immediate solution:

**Add a retry loop with longer delays:**

```python
# Wait longer before querying Usage API
USAGE_API_DELAY = 10 * 60  # 10 minutes

logger.info(f"Waiting {USAGE_API_DELAY}s for Usage API to update...")
time.sleep(USAGE_API_DELAY)

# Then query
tokens_in, tokens_out = self.fetch_usage_from_openai(...)
```

**Pros**: Simple, one-line change
**Cons**: Blocks for 10 minutes, may still fail

## Conclusion

**Recommended**: Implement Approach 1 (Post-Run Update Script) for production use.

This provides:
- ✅ Reliable token data from OpenAI API
- ✅ Non-blocking workflow
- ✅ Framework-specific attribution
- ✅ Clean separation of concerns
- ✅ Easy to test and maintain

The reconciliation process runs asynchronously and updates metrics files after the Usage API data becomes available, ensuring accurate token counts while not blocking experiment execution.
