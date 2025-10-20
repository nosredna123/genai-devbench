# Architecture Guide

Comprehensive overview of the BAEs Experiment Framework architecture.

## System Overview

The BAEs Experiment Framework is a **research infrastructure** for empirically comparing AI-powered software development frameworks. It orchestrates multi-framework experiments, collects standardized metrics, and performs statistical analysis.

### Design Principles

1. **Reproducibility First**: Deterministic seeds, commit hashing, HITL logging
2. **Framework Agnostic**: Adapter pattern for easy framework integration
3. **Isolated Execution**: Each run in separate workspace with cleanup
4. **Observable**: Comprehensive logging and event tracking
5. **Statistically Sound**: Non-parametric tests, bootstrap CI, convergence detection

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                                                                  │
│  ┌────────────────┐              ┌──────────────────┐          │
│  │ run_experiment │              │ analyze_results  │          │
│  │     .sh        │              │      .sh         │          │
│  └────────┬───────┘              └────────┬─────────┘          │
└───────────┼──────────────────────────────┼────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────────┐   ┌──────────────────────────────┐
│   Orchestrator Module     │   │    Analysis Module           │
│                           │   │                              │
│  ┌─────────────────────┐ │   │  ┌────────────────────────┐ │
│  │ OrchestratorRunner  │ │   │  │  Statistical Tests     │ │
│  │  - run_single()     │ │   │  │  - Kruskal-Wallis      │ │
│  │  - run_multi()      │ │   │  │  - Pairwise compare    │ │
│  └──────────┬──────────┘ │   │  │  - Cliff's delta       │ │
│             │             │   │  └────────────────────────┘ │
│  ┌──────────▼──────────┐ │   │  ┌────────────────────────┐ │
│  │ MetricsCollector    │ │   │  │  Visualizations        │ │
│  │ Validator           │ │   │  │  - Radar charts        │ │
│  │ Archiver            │ │   │  │  - Pareto plots        │ │
│  └─────────────────────┘ │   │  │  - Timeline charts     │ │
└───────────┬───────────────┘   │  └────────────────────────┘ │
            │                   │  ┌────────────────────────┐ │
            │                   │  │  Stopping Rule         │ │
            │                   │  │  - Bootstrap CI        │ │
            │                   │  │  - Convergence check   │ │
            │                   │  └────────────────────────┘ │
            ▼                   └──────────────────────────────┘
┌───────────────────────────┐
│    Adapter Pattern        │
│                           │
│  ┌─────────────────────┐ │
│  │   BaseAdapter       │ │
│  │   (Abstract)        │ │
│  └──────────┬──────────┘ │
│             │             │
│  ┌──────────┼──────────┐ │
│  ▼          ▼          ▼ │
│ BAeS    ChatDev   GHSpec │
│ Adapter  Adapter  Adapter│
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│   Utility Modules         │
│                           │
│  - Logger (JSON)          │
│  - ConfigLoader           │
│  - Isolation (workspace)  │
│  - APIClient              │
└───────────────────────────┘
```

## Core Components

### 1. Orchestrator Module (`src/orchestrator/`)

**Purpose**: Coordinates experiment execution across frameworks.

#### OrchestratorRunner

Main execution engine with two modes:

**Single Run Mode:**
```python
runner = OrchestratorRunner(config)
results = runner.run_single(
    framework_name="baes",
    prompts=prompts,
    run_id="baes-20251008-..."
)
```

**Multi-Framework Mode:**
```python
results = runner.run_multi_framework(
    framework_names=["baes", "chatdev", "ghspec"],
    prompts=prompts
)
# Runs until convergence (min 5, max 25 runs each)
```

**Key Responsibilities:**
- Initializes isolated workspaces
- Invokes framework adapters for each step
- Enforces timeouts and retry logic
- Logs HITL events with SHA-1 hashing
- Coordinates validation and archival

#### MetricsCollector

Computes 16 standardized metrics from run outputs:

**Metric Categories:**
1. **Quality Metrics**: AUTR, Q*, ESR, CRUDe, MC
2. **Efficiency Metrics**: TOK_IN, TOK_OUT, T_WALL, T_USER, T_CPU, AEI
3. **Reliability Metrics**: ZDI, RTE, MCI
4. **Process Metrics**: ITR, DPL

**Collection Process:**
```python
collector = MetricsCollector(workspace_dir)
metrics = collector.collect_metrics(
    adapter_results,    # Framework outputs
    validation_results, # CRUD testing results
    wall_time=1847.5,
    api_usage={"input": 12500, "output": 3200}
)
```

#### Validator

Validates framework outputs at each step:

**Validation Types:**
1. **CRUD Operations**: Tests Create/Read/Update/Delete functionality
2. **UI Testing**: Verifies user interface correctness
3. **Downtime Monitoring**: Detects zero-downtime violations

**Interface:**
```python
validator = Validator(workspace_dir)
results = validator.validate_step(step_num=3)
# Returns: {"crud_coverage": 10/12, "ui_valid": True, "downtime": 0}
```

#### Archiver

Archives run outputs with integrity verification:

**Archive Contents:**
- Generated source code
- Configuration snapshots
- Logs and events
- Validation results

**Process:**
```python
archiver = Archiver(workspace_dir)
archive_path, sha256 = archiver.create_archive()
# Creates: archive.tar.gz + SHA-256 checksum
```

### 2. Adapter Pattern (`src/adapters/`)

**Purpose**: Abstracts framework-specific invocation details.

#### BaseAdapter (Abstract)

Defines the contract all framework adapters must implement:

```python
class BaseAdapter(ABC):
    @abstractmethod
    def setup(self, workspace_dir: str) -> None:
        """Clone and configure framework repository."""
        pass
    
    @abstractmethod
    def execute_step(
        self,
        step_num: int,
        prompt: str,
        hitl_response: Optional[str]
    ) -> Dict[str, Any]:
        """Execute one evolution step."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass
    
    @abstractmethod
    def get_output_dir(self) -> str:
        """Return directory with generated code."""
        pass
    
    @abstractmethod
    def get_logs(self) -> List[str]:
        """Return framework execution logs."""
        pass
```

#### Concrete Adapters

**BAeSAdapter:**
- Invokes BAEs CLI with JSON prompts
- Handles multi-file CRUD scenarios
- Extracts token usage from OpenAI API

**ChatDevAdapter:**
- Runs ChatDev phases (design → code → test)
- Manages agent conversations
- Monitors role-based outputs

**GHSpecAdapter:**
- Integrates GitHub Spec-kit workflow
- Handles specification evolution
- Tracks issue-based development

### 3. Analysis Module (`src/analysis/`)

**Purpose**: Statistical analysis and visualization of experiment results.

#### Statistical Tests (`statistics.py`)

**Non-Parametric Tests:**
```python
# Kruskal-Wallis H-test (3+ groups)
result = kruskal_wallis_test({
    "baes": [0.85, 0.88, 0.82],
    "chatdev": [0.72, 0.75, 0.70],
    "ghspec": [0.68, 0.65, 0.70]
})
# Returns: H statistic, p-value, significance

# Pairwise comparisons with Dunn-Šidák correction
comparisons = pairwise_comparisons(groups, alpha=0.05)
# Returns: [(group1, group2, p_value, cliff_delta, effect_size), ...]
```

**Effect Sizes:**
```python
# Cliff's delta (non-parametric effect size)
delta = cliffs_delta([0.85, 0.88], [0.72, 0.75])
# Returns: -1 to 1 (magnitude: negligible/small/medium/large)
```

**Bootstrap Confidence Intervals:**
```python
aggregated = bootstrap_aggregate_metrics(runs, n_bootstrap=10000)
# Returns: mean, median, std, ci_lower, ci_upper for each metric
```

#### Stopping Rule (`stopping_rule.py`)

Determines when to stop collecting runs:

**Convergence Criterion:**
- Bootstrap 95% CI half-width < 10% of mean
- Minimum 5 runs per framework
- Maximum 25 runs per framework

```python
converged = check_convergence(
    values=[0.85, 0.88, 0.82, 0.86, 0.84],
    threshold=0.10,  # 10% threshold
    n_bootstrap=10000
)
# Returns: True if converged, False otherwise
```

#### Visualizations (`visualizations.py`)

**Publication-Quality Charts:**

1. **Radar Chart**: 6 metrics comparison (polar projection)
2. **Pareto Plot**: Q* vs TOK_IN scatter with frontier
3. **Timeline Chart**: CRUD coverage + downtime evolution

All exported as SVG (scalable, publication-ready).

### 4. Utility Modules (`src/utils/`)

#### Logger (`logger.py`)

Structured JSON logging with metadata:

```python
logger = get_logger(__name__)
log_event("run_started", run_id="baes-123", framework="baes")
# Output: {"timestamp": "...", "level": "INFO", "message": "...", "run_id": "..."}
```

#### ConfigLoader (`config_loader.py`)

YAML configuration with validation:

```python
config = load_config("config/experiment.yaml")
# Validates schema, sets deterministic seeds
```

#### Isolation (`isolation.py`)

Workspace management:

```python
run_id = generate_run_id("baes")  # baes-20251008-142315-abc123
workspace = create_isolated_workspace("runs", "baes", run_id)
# Creates: runs/baes/baes-20251008-142315-abc123/
```

#### APIClient (`api_client.py`)

OpenAI Usage API verification:

```python
client = OpenAIAPIClient(api_key)
usage = client.verify_token_usage(run_id)
# Returns: {"input_tokens": 12500, "output_tokens": 3200}
```

## Data Flow

### Single Run Execution

```
1. User invokes run_experiment.sh
   ↓
2. OrchestratorRunner.run_single()
   ↓
3. generate_run_id() → "baes-20251008-142315-abc123"
   ↓
4. create_isolated_workspace() → runs/baes/<run-id>/
   ↓
5. BAeSAdapter.setup() → Clone framework repo
   ↓
6. For each step (1-6):
   │
   ├─ BAeSAdapter.execute_step(step_num, prompt, hitl)
   │  ├─ Invoke framework CLI
   │  ├─ Wait for completion (timeout: 3600s)
   │  └─ Return outputs
   │
   ├─ Validator.validate_step(step_num)
   │  ├─ Run CRUD tests
   │  ├─ Check UI validity
   │  └─ Monitor downtime
   │
   └─ log_hitl_event() → hitl_events.jsonl (with SHA-1)
   ↓
7. MetricsCollector.collect_metrics()
   ↓
8. Archiver.create_archive() → archive.tar.gz + SHA-256
   ↓
9. Save metrics.json, event_log.jsonl
   ↓
10. cleanup_workspace() (optional)
```

### Multi-Framework Execution

```
1. User invokes run_experiment.sh --multi baes chatdev ghspec
   ↓
2. OrchestratorRunner.run_multi_framework()
   ↓
3. Initialize convergence tracker for each framework
   ↓
4. Loop (min 5 runs, max 25 runs):
   │
   ├─ For each framework in parallel:
   │  ├─ run_single(framework)
   │  └─ Collect metrics
   │
   ├─ check_convergence() for each metric
   │  ├─ Bootstrap 95% CI
   │  └─ Half-width < 10% of mean?
   │
   └─ If all frameworks converged → STOP
   ↓
5. Return aggregated results
```

### Analysis Pipeline

```
1. User invokes analyze_results.sh
   ↓
2. Load all metrics.json from runs/*/
   ↓
3. bootstrap_aggregate_metrics()
   ├─ Compute mean, median, CI for each metric
   └─ Group by framework
   ↓
4. kruskal_wallis_test() for each metric
   ├─ Test for significant differences
   └─ Report H statistic, p-value
   ↓
5. pairwise_comparisons()
   ├─ Dunn-Šidák correction
   ├─ Cliff's delta effect sizes
   └─ Identify significant pairs
   ↓
6. Generate visualizations:
   ├─ radar_chart() → radar_chart.svg
   ├─ pareto_plot() → pareto_plot.svg
   └─ timeline_chart() → timeline_chart.svg
   ↓
7. generate_statistical_report() → report.md
```

## Directory Structure

```
genai-devbench/
├── config/                      # Configuration files
│   ├── experiment.yaml          # Main config (frameworks, timeouts, seeds)
│   ├── prompts/                 # CRUD evolution prompts (6 steps)
│   │   ├── step_1.txt
│   │   ├── step_2.txt
│   │   ...
│   │   └── step_6.txt
│   └── hitl/                    # HITL clarification templates
│       └── expanded_spec.txt
│
├── src/                         # Source code
│   ├── orchestrator/            # Execution coordination
│   │   ├── __main__.py          # CLI entry point
│   │   ├── runner.py            # OrchestratorRunner
│   │   ├── metrics_collector.py # MetricsCollector
│   │   ├── validator.py         # Validator
│   │   ├── archiver.py          # Archiver
│   │   └── config_loader.py     # ConfigLoader
│   │
│   ├── adapters/                # Framework integrations
│   │   ├── base_adapter.py      # BaseAdapter (abstract)
│   │   ├── baes_adapter.py      # BAeSAdapter
│   │   ├── chatdev_adapter.py   # ChatDevAdapter
│   │   └── ghspec_adapter.py    # GHSpecAdapter
│   │
│   ├── analysis/                # Statistical analysis
│   │   ├── statistics.py        # Tests, effect sizes, reports
│   │   ├── stopping_rule.py     # Convergence detection
│   │   └── visualizations.py    # Charts (radar, Pareto, timeline)
│   │
│   └── utils/                   # Utilities
│       ├── logger.py            # JSON logging
│       ├── config_loader.py     # YAML parsing
│       ├── isolation.py         # Workspace management
│       └── api_client.py        # OpenAI API verification
│
├── runners/                     # Executable scripts
│   ├── run_experiment.sh        # Main experiment runner
│   └── analyze_results.sh       # Analysis pipeline
│
├── runs/                        # Experiment outputs (gitignored)
│   └── <framework>/
│       └── <run-id>/
│           ├── metrics.json
│           ├── event_log.jsonl
│           ├── hitl_events.jsonl
│           ├── archive.tar.gz
│           └── checksum.sha256
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── contract/                # Contract tests
│
├── docs/                        # Documentation
│   ├── quickstart.md
│   ├── architecture.md          # This file
│   ├── metrics.md
│   └── troubleshooting.md
│
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git exclusions
└── README.md                    # Project overview
```

## Key Design Patterns

### 1. Adapter Pattern

**Problem**: Different frameworks have different CLIs, configurations, and output formats.

**Solution**: Define `BaseAdapter` interface, implement concrete adapters for each framework.

**Benefits**:
- Easy to add new frameworks (just implement BaseAdapter)
- Uniform interface for orchestrator
- Framework-specific logic isolated

### 2. Isolated Workspaces

**Problem**: Frameworks may conflict with each other (dependencies, ports, files).

**Solution**: Each run gets its own directory with cleanup.

**Benefits**:
- No cross-contamination
- Reproducible environments
- Parallel execution possible

### 3. Event Sourcing (Logs)

**Problem**: Need audit trail for debugging and reproducibility.

**Solution**: All operations logged to `event_log.jsonl` in append-only format.

**Benefits**:
- Full execution history
- Easy to replay/debug
- Machine-readable logs

### 4. Statistical Rigor

**Problem**: Need valid conclusions from empirical comparisons.

**Solution**: Non-parametric tests, effect sizes, bootstrap CI, convergence detection.

**Benefits**:
- No distribution assumptions
- Quantified effect magnitudes
- Efficient data collection (stop early if converged)

## Extension Points

### Adding a New Framework

1. Create `src/adapters/myframework_adapter.py`
2. Implement `BaseAdapter` interface
3. Add configuration to `config/experiment.yaml`:
   ```yaml
   frameworks:
     myframework:
       repo_url: https://github.com/org/myframework
       commit_hash: abc123...
       api_key_env: MYFRAMEWORK_API_KEY
   ```
4. Test with `./runners/run_experiment.sh myframework`

### Adding a New Metric

1. Update `src/orchestrator/metrics_collector.py`:
   ```python
   def compute_my_metric(self, data: Dict) -> float:
       # Computation logic
       return value
   ```
2. Add to `collect_metrics()` return dict
3. Update `docs/metrics.md` with definition

### Adding a New Visualization

1. Update `src/analysis/visualizations.py`:
   ```python
   def my_chart(data: Dict, output_path: str) -> None:
       # Chart generation logic
       plt.savefig(output_path, format='svg')
   ```
2. Call from `runners/analyze_results.sh`

## Performance Considerations

### Timeouts

Each step has a configurable timeout (default: 3600s). Adjust in `experiment.yaml`:

```yaml
timeout_seconds: 7200  # 2 hours for complex steps
```

### Parallelization

Multi-framework mode runs frameworks in parallel. Control with:

```yaml
max_parallel_runs: 3  # Limit concurrent framework executions
```

### Disk Space

Each run consumes ~100-500 MB. Monitor with `df -h` and clean old runs periodically.

### API Rate Limits

If hitting OpenAI rate limits:
- Use paid API tier
- Add delays between steps
- Reduce max parallel runs

## Security Considerations

### API Key Management

- Store keys in `.env` (gitignored)
- Never commit `.env` to version control
- Use environment variables only (no hardcoding)

### Framework Sandboxing

- Frameworks run in isolated workspaces
- Consider Docker containers for additional isolation
- Review framework code before execution

### Data Privacy

- No user data collected by default
- Experiment outputs contain only generated code
- HITL responses logged with SHA-1 (one-way hash)

## Further Reading

- **[Quickstart Guide](./quickstart.md)**: Get started quickly
- **[Metrics Guide](./metrics.md)**: Detailed metric definitions
- **[Troubleshooting Guide](./troubleshooting.md)**: Common issues and solutions
- **[Configuration Guide](./configuration.md)**: Advanced configuration options
