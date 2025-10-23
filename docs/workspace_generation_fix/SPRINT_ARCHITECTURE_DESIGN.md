# Sprint-Based Directory Architecture Design

## 🎯 Executive Summary

**Terminology Change:** "Scenario Steps" → "**Sprints**"

This perfectly captures the concept:
- Each sprint is an **incremental development phase**
- Each sprint **builds on previous sprints**
- Each sprint produces a **complete, evolved version** of the system
- Failures stop the sprint sequence (like real agile development!)

## 📊 Current Implementation Analysis

### What Currently Happens (Question D Answer)

Looking at `src/orchestrator/runner.py:300-400`, the current behavior is:

```python
# Line 328-330: Get enabled steps (sprints)
enabled_steps = get_enabled_steps(self.config, Path.cwd())

# Line 333: Execute steps SEQUENTIALLY
for step_index, step_config in enumerate(enabled_steps, start=1):
    # Line 360: Execute each step
    result = self._execute_step_with_retry(step_config.id, command_text)
    
    # Line 364-378: Record metrics for this step
    self.metrics_collector.record_step(
        step_num=step_config.id,
        command=command_text,
        duration_seconds=...,
        tokens_in=...,
        tokens_out=...,
        ...
    )
```

**Current Problem:** 
All sprints write to the **SAME** `workspace/` directory, so:
- ❌ Sprint 1 output gets **overwritten** by Sprint 2
- ❌ Sprint 2 output gets **overwritten** by Sprint 3
- ❌ Only **final sprint** artifacts survive
- ❌ Cannot debug "which sprint introduced the bug"
- ❌ Cannot analyze code evolution
- ❌ Cannot compare framework performance across sprints

## 🏗️ Proposed Sprint-Based Architecture

### Directory Structure

```
experiments/baseline_gpt4o_mini/runs/baes/abc123/
├── README.md                           # Run overview with sprint summary
│
├── sprint_001/                         # First sprint execution
│   ├── generated_artifacts/            # Sprint 1 artifacts
│   │   ├── managed_system/             # V1: User CRUD only
│   │   │   ├── main.py
│   │   │   ├── requirements.txt
│   │   │   ├── models/
│   │   │   │   └── user.py
│   │   │   └── routes/
│   │   │       └── user_routes.py
│   │   └── database/                   # BAeS-specific (if applicable)
│   │       └── schema.sql
│   ├── logs/
│   │   └── execution_sprint_001.log    # Sprint 1 logs
│   ├── metadata.json                   # Sprint 1 metadata
│   ├── metrics.json                    # Sprint 1 metrics
│   └── validation.json                 # Sprint 1 validation results
│
├── sprint_002/                         # Second sprint execution
│   ├── generated_artifacts/
│   │   ├── managed_system/             # V2: User + Product CRUD (incremental)
│   │   │   ├── main.py                 # Updated
│   │   │   ├── requirements.txt        # Updated
│   │   │   ├── models/
│   │   │   │   ├── user.py             # Preserved from Sprint 1
│   │   │   │   └── product.py          # NEW in Sprint 2
│   │   │   └── routes/
│   │   │       ├── user_routes.py      # Preserved from Sprint 1
│   │   │       └── product_routes.py   # NEW in Sprint 2
│   │   └── database/
│   │       └── schema.sql              # Updated with Product table
│   ├── logs/
│   │   └── execution_sprint_002.log
│   ├── metadata.json
│   ├── metrics.json
│   └── validation.json
│
├── sprint_003/                         # Third sprint execution
│   ├── generated_artifacts/
│   │   └── managed_system/             # V3: Full system with auth
│   │       ├── main.py                 # Updated
│   │       ├── requirements.txt        # Updated
│   │       ├── models/
│   │       │   ├── user.py
│   │       │   └── product.py
│   │       ├── routes/
│   │       │   ├── user_routes.py
│   │       │   └── product_routes.py
│   │       └── middleware/             # NEW in Sprint 3
│   │           └── auth.py
│   ├── logs/
│   ├── metadata.json
│   ├── metrics.json
│   └── validation.json
│
├── summary/                            # Aggregate data for entire run
│   ├── metrics_cumulative.json         # Cumulative + per-sprint metrics
│   ├── evolution_report.md             # Code evolution analysis
│   └── sprint_comparison.json          # Compare sprints
│
├── final -> sprint_003                 # Symlink to final sprint
└── run.tar.gz                          # Archive (optional: all sprints or final only)
```

### Key Design Decisions

#### 1. **Sprint Numbering: `sprint_NNN/`**

**Format:** `sprint_001`, `sprint_002`, `sprint_003`, ...

**Rationale:**
- ✅ Self-documenting (clear they're agile sprints)
- ✅ Sortable (lexicographic order matches execution order)
- ✅ Consistent with user's mental model
- ✅ Scales to 999 sprints (3 digits)

**Metadata Connection:**
```json
// sprint_001/metadata.json
{
  "sprint_number": 1,
  "step_id": 1,  // Original step ID from config
  "step_name": "Create User CRUD",
  "description": "Implement user model with CRUD operations",
  "framework": "baes",
  "started_at": "2025-10-22T14:30:22Z",
  "completed_at": "2025-10-22T14:31:15Z"
}
```

#### 2. **Incremental Context Preservation**

**How Sprint 2 Sees Sprint 1:**

```python
# In BaseAdapter.__init__()
def __init__(self, workspace_path: Path, sprint_num: int, run_dir: Path, ...):
    self.workspace_path = workspace_path  # Current sprint workspace
    self.sprint_num = sprint_num
    self.run_dir = run_dir
    
    # NEW: Get previous sprint's artifacts for context
    self.previous_sprint_path = None
    if sprint_num > 1:
        prev_sprint = f"sprint_{sprint_num-1:03d}"
        self.previous_sprint_path = run_dir / prev_sprint / "generated_artifacts"
```

**Framework Execution:**

```python
# Sprint 1: Start from scratch
adapter.execute_step(
    step_num=1,
    command="Create User CRUD",
    previous_artifacts=None  # No previous sprint
)

# Sprint 2: Build on Sprint 1
adapter.execute_step(
    step_num=2,
    command="Add Product CRUD",
    previous_artifacts=sprint_001/generated_artifacts/  # Pass Sprint 1 code
)
```

**Framework's Perspective:**
- BAeS: Receives previous code in prompt context
- ChatDev: Sets WareHouse to previous sprint artifacts
- GHSpec: Provides previous implementation to specify phase

#### 3. **Metrics: Per-Sprint + Cumulative**

**Per-Sprint Metrics (`sprint_NNN/metrics.json`):**
```json
{
  "sprint_number": 1,
  "step_id": 1,
  "tokens": {
    "input": 2000,
    "output": 800,
    "cached": 0,
    "total": 2800
  },
  "api_calls": 3,
  "execution_time_seconds": 45.3,
  "hitl_interactions": 0,
  "retry_count": 0,
  "validation": {
    "passed": true,
    "issues": []
  }
}
```

**Cumulative Metrics (`summary/metrics_cumulative.json`):**
```json
{
  "total_sprints": 3,
  "cumulative": {
    "tokens": {
      "input": 5300,
      "output": 2100,
      "cached": 500,
      "total": 7900
    },
    "api_calls": 8,
    "execution_time_seconds": 125.7,
    "hitl_interactions": 0
  },
  "per_sprint": [
    {
      "sprint": 1,
      "tokens": {"total": 2800},
      "api_calls": 3,
      "execution_time": 45.3
    },
    {
      "sprint": 2,
      "tokens": {"total": 2600},
      "api_calls": 3,
      "execution_time": 40.2
    },
    {
      "sprint": 3,
      "tokens": {"total": 2500},
      "api_calls": 2,
      "execution_time": 40.2
    }
  ],
  "sprint_efficiency": {
    "tokens_per_sprint_avg": 2633,
    "tokens_trend": "decreasing",  // Good: getting more efficient
    "time_per_sprint_avg": 41.9
  }
}
```

#### 4. **Validation: Per-Sprint**

**Each sprint gets validated independently:**

```python
# After Sprint 1 completes
validator.validate_workspace(sprint_001/generated_artifacts/)
# Must be valid: Complete User CRUD app

# After Sprint 2 completes
validator.validate_workspace(sprint_002/generated_artifacts/)
# Must be valid: Complete User + Product CRUD app

# After Sprint 3 completes
validator.validate_workspace(sprint_003/generated_artifacts/)
# Must be valid: Complete app with auth
```

**Validation Results (`sprint_NNN/validation.json`):**
```json
{
  "sprint_number": 1,
  "validated_at": "2025-10-22T14:31:20Z",
  "overall_status": "passed",
  "checks": {
    "python_files_exist": true,
    "imports_valid": true,
    "syntax_valid": true,
    "requirements_exist": true
  },
  "issues": [],
  "completeness": 1.0
}
```

#### 5. **Failure Handling: Stop and Preserve**

**If Sprint 2 fails:**

```
experiments/.../runs/baes/abc123/
├── sprint_001/                 ✅ Complete and validated
│   ├── generated_artifacts/
│   ├── metrics.json
│   └── validation.json
│
├── sprint_002/                 ❌ Failed
│   ├── generated_artifacts/    ⚠️ Partial/incomplete
│   ├── logs/
│   │   └── execution.log       📝 Contains error details
│   ├── metadata.json           
│   │   ├── "status": "failed"
│   │   └── "error": "Timeout after 600s"
│   ├── metrics.json            📊 Metrics up to failure point
│   └── validation.json         
│       └── "status": "failed"
│
├── sprint_003/                 ⏸️ Not executed (stopped at Sprint 2)
│   └── [DOES NOT EXIST]
│
├── summary/
│   └── metrics_cumulative.json
│       ├── "completed_sprints": 1
│       ├── "failed_sprint": 2
│       └── "total_planned_sprints": 3
│
└── final -> sprint_001         🔗 Symlink to last successful sprint
```

**Benefit for Debugging:**
- ✅ Sprint 1 artifacts preserved (can be analyzed)
- ✅ Sprint 2 partial artifacts available (can see what was generated before failure)
- ✅ Logs show exactly where Sprint 2 failed
- ✅ Can retry just Sprint 2 (future feature)

#### 6. **Archiving Strategy**

**Option A: Archive Final Sprint Only (Recommended)**
```bash
run.tar.gz contains:
  - final/ (symlink target: sprint_003/)
  - summary/
  - README.md
```

**Option B: Archive All Sprints (Research Mode)**
```bash
run.tar.gz contains:
  - sprint_001/
  - sprint_002/
  - sprint_003/
  - summary/
  - README.md
```

**Configurable:**
```yaml
# config/experiment.yaml
archiving:
  mode: "final_only"  # or "all_sprints"
  compress_intermediate: true  # Compress sprint_001, sprint_002
```

#### 7. **README.md Generation**

**Run-Level README (`README.md`):**
```markdown
# Run: abc123 - BAeS Framework

**Experiment:** baseline_gpt4o_mini  
**Framework:** BAeS  
**Model:** gpt-4o-mini  
**Started:** 2025-10-22 14:30:22  
**Completed:** 2025-10-22 14:32:15  
**Status:** ✅ Success (3/3 sprints completed)

## Scenario
Build a user management system with incremental features.

## Sprint Summary

| Sprint | Description | Status | Tokens | Time | Validation |
|--------|-------------|--------|--------|------|------------|
| 1 | Create User CRUD | ✅ Success | 2,800 | 45.3s | ✅ Pass |
| 2 | Add Product CRUD | ✅ Success | 2,600 | 40.2s | ✅ Pass |
| 3 | Add Auth Middleware | ✅ Success | 2,500 | 40.2s | ✅ Pass |

**Total:** 7,900 tokens, 125.7s, 8 API calls

## Final Application

The complete application is in: **`sprint_003/generated_artifacts/managed_system/`**

Or use the convenience symlink: **`final/generated_artifacts/managed_system/`**

### Quick Start
```bash
cd sprint_003/generated_artifacts/managed_system/
# or: cd final/generated_artifacts/managed_system/
pip install -r requirements.txt
python main.py
```

## Sprint Evolution

- **Sprint 1:** Basic User CRUD (user.py, user_routes.py)
- **Sprint 2:** Added Product CRUD (product.py, product_routes.py)
- **Sprint 3:** Added Authentication (middleware/auth.py)

## Detailed Metrics

See `summary/metrics_cumulative.json` for complete breakdown.

## Directory Structure

```
abc123/
├── sprint_001/     # First increment: User CRUD
├── sprint_002/     # Second increment: + Product CRUD
├── sprint_003/     # Third increment: + Auth
├── summary/        # Aggregated data
└── final/          # → sprint_003 (convenience symlink)
```
```

## 🔧 Implementation Plan

### Phase 4A: Sprint-Based Directory Structure

#### Step 1: Update `isolation.py` (Create Sprint Workspaces)

```python
# src/utils/isolation.py

def create_sprint_workspace(
    framework: str,
    run_id: str,
    sprint_num: int,
    experiment_name: Optional[str] = None
) -> Tuple[Path, Path]:
    """
    Create isolated workspace for a specific sprint.
    
    Args:
        framework: Framework name (baes, chatdev, ghspec)
        run_id: Unique run identifier
        sprint_num: Sprint number (1, 2, 3, ...)
        experiment_name: Name of experiment
        
    Returns:
        Tuple of (sprint_dir, artifacts_dir) Path objects
        
    Example:
        sprint_dir: runs/baes/abc123/sprint_001/
        artifacts_dir: runs/baes/abc123/sprint_001/generated_artifacts/
    """
    # Get run directory
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        run_dir = exp_paths.get_run_dir(framework, run_id)
    else:
        run_dir = Path("runs") / framework / run_id
    
    # Create sprint directory
    sprint_dir = run_dir / f"sprint_{sprint_num:03d}"
    artifacts_dir = sprint_dir / "generated_artifacts"
    
    # Create directories
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (sprint_dir / "logs").mkdir(exist_ok=True)
    
    logger.info(
        f"Created sprint workspace: {artifacts_dir}",
        extra={'run_id': run_id, 'framework': framework, 'sprint': sprint_num}
    )
    
    return sprint_dir, artifacts_dir


def get_previous_sprint_artifacts(
    run_dir: Path,
    current_sprint_num: int
) -> Optional[Path]:
    """
    Get previous sprint's artifacts directory for incremental context.
    
    Args:
        run_dir: Run directory path
        current_sprint_num: Current sprint number
        
    Returns:
        Path to previous sprint's artifacts, or None if sprint 1
    """
    if current_sprint_num <= 1:
        return None
    
    prev_sprint_num = current_sprint_num - 1
    prev_sprint_dir = run_dir / f"sprint_{prev_sprint_num:03d}"
    prev_artifacts = prev_sprint_dir / "generated_artifacts"
    
    if prev_artifacts.exists():
        return prev_artifacts
    
    return None
```

#### Step 2: Update `BaseAdapter` (Sprint-Aware)

```python
# src/adapters/base_adapter.py

class BaseAdapter(ABC):
    def __init__(
        self,
        workspace_path: Path,
        sprint_num: int,
        run_dir: Path,
        config: Dict[str, Any],
        run_id: str,
        scenario_description: str,
        **kwargs
    ):
        """
        Initialize base adapter with sprint awareness.
        
        Args:
            workspace_path: Current sprint's workspace path
            sprint_num: Current sprint number (1, 2, 3, ...)
            run_dir: Run directory (contains all sprints)
            config: Framework configuration
            run_id: Unique run identifier
            scenario_description: Scenario description
        """
        self.workspace_path = workspace_path
        self.sprint_num = sprint_num
        self.run_dir = run_dir
        self.config = config
        self.run_id = run_id
        self.scenario_description = scenario_description
        
        # Get previous sprint for context
        self.previous_sprint_artifacts = get_previous_sprint_artifacts(
            run_dir, sprint_num
        )
        
        # Sprint-specific logs
        sprint_dir = workspace_path.parent
        self.sprint_log_dir = sprint_dir / "logs"
        self.sprint_log_dir.mkdir(exist_ok=True)
        
        logger.info(
            f"Initialized adapter for sprint {sprint_num}",
            extra={
                'run_id': run_id,
                'sprint': sprint_num,
                'has_previous': self.previous_sprint_artifacts is not None
            }
        )
```

#### Step 3: Update `OrchestratorRunner` (Execute Sprints)

```python
# src/orchestrator/runner.py

def run(self) -> Dict[str, Any]:
    """Execute framework run with sprint-based isolation."""
    
    # ... (setup code unchanged) ...
    
    # Track sprint results
    sprint_results = []
    completed_sprints = 0
    failed_sprint = None
    
    # Execute sprints sequentially
    for step_index, step_config in enumerate(enabled_steps, start=1):
        sprint_num = step_index
        
        # Create sprint workspace
        sprint_dir, artifacts_dir = create_sprint_workspace(
            framework=self.framework_name,
            run_id=self.run_id,
            sprint_num=sprint_num,
            experiment_name=self.experiment_name
        )
        
        # Initialize adapter for this sprint
        if self.framework_name == "baes":
            self.adapter = BAeSAdapter(
                workspace_path=artifacts_dir,
                sprint_num=sprint_num,
                run_dir=run_dir,
                config=framework_config,
                run_id=self.run_id,
                scenario_description=self.config['scenario']['description']
            )
        # ... (ChatDev, GHSpec similar) ...
        
        # Execute sprint
        try:
            result = self._execute_sprint(sprint_num, step_config, sprint_dir)
            
            # Validate sprint
            validation_result = self.validator.validate_workspace(artifacts_dir)
            
            if not validation_result['passed']:
                raise ValidationError(f"Sprint {sprint_num} validation failed")
            
            # Save sprint metadata
            self._save_sprint_metadata(sprint_dir, sprint_num, step_config, result)
            self._save_sprint_metrics(sprint_dir, result)
            self._save_sprint_validation(sprint_dir, validation_result)
            
            sprint_results.append({
                'sprint': sprint_num,
                'status': 'success',
                'metrics': result
            })
            completed_sprints += 1
            
        except Exception as e:
            # Sprint failed - stop execution
            logger.error(f"Sprint {sprint_num} failed: {e}")
            
            failed_sprint = sprint_num
            sprint_results.append({
                'sprint': sprint_num,
                'status': 'failed',
                'error': str(e)
            })
            
            # Save failure metadata
            self._save_sprint_metadata(
                sprint_dir, sprint_num, step_config,
                {'status': 'failed', 'error': str(e)}
            )
            
            break  # STOP: Don't execute remaining sprints
    
    # Create summary
    summary_dir = run_dir / "summary"
    summary_dir.mkdir(exist_ok=True)
    
    self._create_cumulative_metrics(summary_dir, sprint_results)
    self._create_final_symlink(run_dir, completed_sprints)
    self._generate_run_readme(run_dir, sprint_results)
    
    return {
        'total_sprints_planned': len(enabled_steps),
        'completed_sprints': completed_sprints,
        'failed_sprint': failed_sprint,
        'status': 'success' if failed_sprint is None else 'failed'
    }
```

## 📈 Benefits Analysis

### For Your Priority #1: Compare Framework Performance Across Sprints

**Before (Current):**
- ❌ Can't compare how BAeS vs ChatDev vs GHSpec handle incremental changes
- ❌ Only see final output

**After (Sprint-Based):**
- ✅ See which framework is better at Sprint 1 (initial creation)
- ✅ See which framework is better at Sprint 2 (adding features to existing code)
- ✅ See which framework is better at Sprint 3 (complex integration)
- ✅ Measure "incremental efficiency" (tokens per sprint, time per sprint)

**Example Analysis:**
```
Sprint Efficiency Report:

Framework: BAeS
- Sprint 1: 2800 tokens, 45s (baseline)
- Sprint 2: 2600 tokens, 40s (7% faster, learned context)
- Sprint 3: 2500 tokens, 40s (11% faster than baseline)

Framework: ChatDev
- Sprint 1: 3200 tokens, 55s (baseline)
- Sprint 2: 3400 tokens, 58s (6% slower, struggled with context)
- Sprint 3: 3600 tokens, 62s (12% slower than baseline)

Winner: BAeS (gets more efficient with each sprint)
```

### For Priority #2: Token Efficiency Per Sprint

- ✅ See exactly which sprints are expensive
- ✅ Identify token-heavy sprints (opportunities for optimization)
- ✅ Track token trends (increasing? decreasing?)

### For Priority #3: Code Evolution Analysis

- ✅ `git diff sprint_001 sprint_002` to see what changed
- ✅ Track LOC growth per sprint
- ✅ See how frameworks handle refactoring
- ✅ Analyze code quality degradation over sprints

### For Priority #4: Debug Step Failures

- ✅ Sprint 2 failed? Check Sprint 1 artifacts (still there!)
- ✅ See exact state before failure
- ✅ Compare Sprint 1 (working) vs Sprint 2 (broken)
- ✅ Logs isolated per sprint

## 🎯 Recommendation

**✅ STRONGLY RECOMMEND** implementing sprint-based architecture because:

1. **Essential for your goals** (priorities #1, #2, #4)
2. **Clean mental model** (sprints = agile development)
3. **Enables powerful analysis** (framework comparison across increments)
4. **Better debugging** (isolate failures to specific sprints)
5. **Incremental validation** (each sprint must be valid)

**Complexity is justified** because:
- This is a **benchmarking research tool**, not a simple demo
- Understanding incremental development is **core to the research question**
- The implementation is **well-scoped** and **architecturally sound**

## 🚀 Implementation Timeline

1. **Phase 4A: Sprint Directory Structure** (3-4 hours)
   - Update `isolation.py` with sprint workspace creation
   - Update `BaseAdapter` with sprint awareness
   - Update `OrchestratorRunner` with sprint execution loop

2. **Phase 4B: Sprint Metadata & Metrics** (2-3 hours)
   - Per-sprint metadata/metrics saving
   - Cumulative metrics aggregation
   - Sprint validation tracking

3. **Phase 4C: Documentation & Symlinks** (1-2 hours)
   - README.md generation
   - Final symlink creation
   - Evolution report generation

4. **Phase 4D: Testing** (2-3 hours)
   - Test with multi-sprint scenarios
   - Verify failure handling
   - Validate metrics aggregation

**Total: 8-12 hours** (justified by research value!)

---

**Question for you:** Shall we proceed with this sprint-based architecture? I'm ready to implement it! 🚀
