# Research & Technical Decisions

**Feature**: BAEs Experiment Framework  
**Phase**: 0 (Research & Resolution)  
**Date**: 2025-10-08

## Overview

This document consolidates research findings and technical decisions for implementing the BAEs experiment orchestrator. All "NEEDS CLARIFICATION" items from Technical Context have been resolved through analysis of requirements, constitutional constraints, and best practices.

---

## 1. Minimal Dependency Strategy

**Decision**: Use Python standard library for 95% of functionality. Limit external dependencies to: PyYAML (config parsing), requests (HTTP/API calls), pytest (testing).

**Rationale**:
- Constitution Principle IV (Minimal Dependencies) requires portability and longevity
- Standard library modules are stable across Python versions and OS platforms
- Reduces security surface area and installation complexity
- Enables running experiments in restricted environments (e.g., air-gapped systems)

**Implementation**:
```python
# Core modules (standard library)
import subprocess  # Framework process management
import json        # Structured logging and metrics
import pathlib     # Cross-platform path handling
import uuid        # Run ID generation
import hashlib     # SHA-256 for artifact verification
import datetime    # ISO 8601 timestamps
import time        # Sleep for health checks
import tarfile     # Artifact compression
import shutil      # Directory operations
import os          # Environment variables

# External dependencies (minimal)
import yaml        # Config parsing (PyYAML)
import requests    # OpenAI Usage API, health checks
import pytest      # Testing framework
```

**Alternatives Considered**:
- **Rich CLI frameworks** (Click, Typer): Rejected—simple argparse sufficient for single entry point
- **Logging libraries** (loguru, structlog): Rejected—standard `logging` module meets needs
- **HTTP libraries** (httpx, aiohttp): Rejected—requests is simpler, no async needed (sequential runs)
- **Configuration libraries** (pydantic, marshmallow): Rejected—manual YAML parsing with dict access is clearer

---

## 2. Framework Adapter Architecture

**Decision**: Abstract base class (`BaseAdapter`) with framework-specific implementations. Each adapter translates standard CLI commands (start, command, health, stop) to framework-specific invocations.

**Rationale**:
- Enables adding new frameworks without modifying orchestrator core
- Provides contract testing surface (all adapters must implement base interface)
- Isolates framework-specific quirks from deterministic orchestration logic

**Interface Design**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    """Abstract interface for LLM framework adapters."""
    
    def __init__(self, config: Dict[str, Any], run_id: str, workspace_path: str):
        self.config = config  # Framework-specific settings from experiment.yaml
        self.run_id = run_id  # Unique run identifier
        self.workspace_path = workspace_path  # Isolated directory for this run
    
    @abstractmethod
    def start(self) -> None:
        """Initialize framework environment (clone repo, setup venv, install deps)."""
        pass
    
    @abstractmethod
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """Send natural language command to framework, wait for completion.
        Returns: {success: bool, duration_seconds: float, hitl_count: int}
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if framework API/UI are responding (HTTP 200).
        Returns: True if healthy, False otherwise.
        """
        pass
    
    @abstractmethod
    def handle_hitl(self, query: str) -> str:
        """Respond to framework clarification request with fixed expanded_spec.txt.
        Returns: Deterministic clarification text.
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Gracefully shutdown framework processes, cleanup temporary files."""
        pass
```

**Alternatives Considered**:
- **Plugin system** (importlib/entry points): Rejected—three known frameworks, no need for dynamic discovery
- **Configuration-driven** (YAML describes commands): Rejected—Python code is more maintainable than complex YAML DSL
- **Monolithic adapter** (if/else per framework): Rejected—violates open/closed principle, harder to test

---

## 3. Deterministic HITL Implementation

**Decision**: Store fixed clarification text in `config/hitl/expanded_spec.txt`. All frameworks receive identical response regardless of query content. Log every HITL event with SHA-1 hash of response for verification.

**Rationale**:
- Constitution Principle V (Deterministic HITL) requires identical guidance across frameworks
- Hashing clarification text enables detecting accidental modifications between runs
- HITL count becomes a measurable autonomy metric (fewer clarifications = higher autonomy)

**Implementation**:
```python
import hashlib

def handle_hitl(self, query: str) -> str:
    """Return fixed clarification from config/hitl/expanded_spec.txt."""
    clarification_path = self.config['hitl_path']  # From experiment.yaml
    with open(clarification_path, 'r') as f:
        response = f.read().strip()
    
    # Log HITL event with hash
    response_hash = hashlib.sha1(response.encode()).hexdigest()
    self.log_hitl_event({
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'step': self.current_step,
        'query': query,
        'response_hash': response_hash,
        'run_id': self.run_id
    })
    
    return response
```

**Alternatives Considered**:
- **LLM-generated clarifications**: Rejected—introduces non-determinism (GPT outputs vary)
- **Interactive prompts**: Rejected—violates automation-first philosophy
- **Per-framework clarifications**: Rejected—breaks experimental control (frameworks must receive identical guidance)

---

## 4. Metrics Collection & Verification

**Decision**: Collect metrics locally during run, then verify token counts against OpenAI Usage API after completion. Store all metrics in structured JSON with ISO 8601 timestamps.

**Rationale**:
- Constitution Principle VI (Reproducible Metrics) requires API-verified token counts
- Local collection provides immediate feedback if API call fails
- JSON storage enables schema validation and programmatic analysis

**Metrics Schema**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "framework": "baes",
  "start_timestamp": "2025-10-08T14:30:00.000Z",
  "end_timestamp": "2025-10-08T15:15:00.000Z",
  "steps": [
    {
      "step_number": 1,
      "command": "Create a Python FastAPI app...",
      "duration_seconds": 120.5,
      "success": true,
      "retry_count": 0,
      "hitl_count": 1,
      "tokens_in": 1500,
      "tokens_out": 3200
    }
  ],
  "aggregate_metrics": {
    "UTT": 12,
    "HIT": 3,
    "AUTR": 0.5,
    "HEU": 9,
    "TOK_IN": 9000,
    "TOK_OUT": 18000,
    "T_WALL_seconds": 2700,
    "CRUDe": 10,
    "ESR": 0.83,
    "MC": 1.0,
    "ZDI": 0,
    "Q_star": 0.79,
    "AEI": 0.055
  },
  "usage_api_verification": {
    "tokens_match": true,
    "discrepancy": 0
  }
}
```

**Alternatives Considered**:
- **Database storage** (SQLite, PostgreSQL): Rejected—JSON files are simpler, self-contained, version-controllable
- **CSV format**: Rejected—not hierarchical, requires separate files for steps vs. aggregates
- **Binary formats** (pickle, msgpack): Rejected—not human-readable, harder to debug

---

## 5. Isolation Strategy

**Decision**: Each run gets unique UUID, isolated workspace directory (`runs/{framework}/{run-id}/`), and fresh Docker container. Delete workspace after successful archival to conserve disk space.

**Rationale**:
- Constitution Principle IX (Failure Isolation) requires no shared state between runs
- UUID run IDs prevent accidental collisions (1 in 10^36 probability)
- Docker containers ensure framework environment isolation (no host contamination)
- Archival with SHA-256 hash enables integrity verification

**Directory Lifecycle**:
```python
# 1. Create isolated workspace
run_id = str(uuid.uuid4())
workspace = pathlib.Path(f"runs/{framework}/{run_id}/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# 2. Execute run in isolated environment
# ... (framework execution happens here)

# 3. Archive workspace
archive_path = pathlib.Path(f"runs/{framework}/{run_id}/run.tar.gz")
with tarfile.open(archive_path, "w:gz") as tar:
    tar.add(workspace, arcname="workspace")
    tar.add(f"runs/{framework}/{run_id}/metrics.json", arcname="metrics.json")
    # ... (add all logs and metadata)

# 4. Compute SHA-256 hash
with open(archive_path, 'rb') as f:
    archive_hash = hashlib.sha256(f.read()).hexdigest()
    
# 5. Store hash in metadata
metadata = {
    'run_id': run_id,
    'archive_hash': archive_hash,
    'archive_size_bytes': archive_path.stat().st_size
}
with open(f"runs/{framework}/{run_id}/metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

# 6. Delete workspace (keep archive only)
shutil.rmtree(workspace)
```

**Alternatives Considered**:
- **Persistent workspace**: Rejected—wastes disk space (~10GB/run × 75 runs = 750GB)
- **Shared Docker volumes**: Rejected—risk of cross-contamination between runs
- **ZIP compression**: Rejected—tar.gz is standard on Linux, better compression ratio

---

## 6. Statistical Analysis Approach

**Decision**: Use scipy.stats for non-parametric tests (Kruskal-Wallis, Dunn-Šidák post-hoc), implement Cliff's δ manually, bootstrap confidence intervals with 10,000 resamples.

**Rationale**:
- Non-parametric tests don't assume normal distribution (common in software metrics)
- Cliff's δ provides effect size interpretation independent of sample size
- Bootstrap CI is distribution-free and robust to outliers

**Implementation Note**:
```python
# scipy is allowed as analysis dependency (not core orchestrator)
# Analysis runs after data collection, not during experiments
from scipy import stats
import numpy as np

def kruskal_wallis_test(groups):
    """Non-parametric alternative to ANOVA for comparing 3+ groups."""
    return stats.kruskal(*groups)

def dunn_sidak_posthoc(groups, alpha=0.05):
    """Pairwise comparisons with family-wise error rate correction."""
    # Implementation based on Dunn 1964 + Šidák correction
    pass

def cliffs_delta(group1, group2):
    """Effect size: proportion of pairs where group1 > group2."""
    n1, n2 = len(group1), len(group2)
    comparisons = sum(x > y for x in group1 for y in group2)
    return (comparisons / (n1 * n2)) * 2 - 1  # Scale to [-1, 1]
```

**Alternatives Considered**:
- **Parametric tests** (t-test, ANOVA): Rejected—assumes normality, fragile to outliers
- **Permutation tests**: Rejected—computationally expensive, bootstrap is faster
- **Cohen's d**: Rejected—assumes equal variances, Cliff's δ is distribution-free

---

## 7. Timeout & Retry Strategy

**Decision**: 10-minute timeout per step (configurable in experiment.yaml), 2 automatic retries on failure (r=2), exponential backoff for API calls (3 retries: 1s, 2s, 4s).

**Rationale**:
- 10 minutes is generous for simple CRUD operations but prevents infinite hangs
- 2 retries balance robustness vs. experimental purity (more retries dilute failure signal)
- Exponential backoff standard for handling transient API errors

**Implementation**:
```python
import signal
import time

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Step exceeded timeout")

def execute_step_with_timeout(step_func, timeout_seconds=600):
    """Execute step with timeout enforcement."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = step_func()
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError:
        # Log timeout, mark run as failed
        return {'success': False, 'error': 'timeout'}

def api_call_with_retry(url, max_retries=3):
    """Exponential backoff retry for API calls."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
            else:
                raise
```

**Alternatives Considered**:
- **Adaptive timeouts** (3× median): Rejected—adds complexity, 10 minutes is sufficient
- **Unlimited retries**: Rejected—can mask systemic failures
- **Fixed retry delay**: Rejected—exponential backoff is standard best practice

---

## 8. Visualization Libraries

**Decision**: Use matplotlib for all visualizations (radar charts, Pareto plots, timeline charts). Export to SVG for publication quality.

**Rationale**:
- matplotlib is de facto standard for scientific plotting in Python
- SVG output is vector-based (scales without quality loss)
- Extensive customization options for publication-ready figures

**Note**: matplotlib is analysis dependency only (not core orchestrator).

```python
import matplotlib.pyplot as plt
import numpy as np

def generate_radar_chart(metrics_dict, output_path):
    """Create radar chart for 6 metrics: AUTR, TOK_IN, T_WALL, CRUDe, ESR, MC."""
    labels = list(metrics_dict.keys())
    values = list(metrics_dict.values())
    
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]  # Close the polygon
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_title("Framework Performance Metrics", pad=20)
    
    plt.savefig(output_path, format='svg', bbox_inches='tight')
```

**Alternatives Considered**:
- **Plotly** (interactive charts): Rejected—overkill for static publication figures
- **seaborn** (statistical plots): Rejected—matplotlib sufficient, reduces dependencies
- **PNG output**: Rejected—SVG is resolution-independent (better for papers)

---

## 9. Configuration Schema

**Decision**: YAML configuration with nested structure: frameworks, prompts, hitl, api_keys, stopping_rule, timeouts. Validate on load with explicit error messages.

**Example**: config/experiment.yaml
```yaml
# BAEs Experiment Configuration
# Version: 1.0.0

random_seed: 42  # Fixed for deterministic execution

frameworks:
  baes:
    repo_url: "https://github.com/gesad-lab/baes.git"
    commit_hash: "a1b2c3d4e5f6g7h8i9j0"
    api_port: 8000
    ui_port: 3000
    api_key_env: "OPENAI_API_KEY_BAES"
    
  chatdev:
    repo_url: "https://github.com/OpenBMB/ChatDev.git"
    commit_hash: "k1l2m3n4o5p6q7r8s9t0"
    api_port: 8001
    ui_port: 3001
    api_key_env: "OPENAI_API_KEY_CHATDEV"
    
  ghspec:
    repo_url: "https://github.com/github/spec-kit.git"
    commit_hash: "u1v2w3x4y5z6a7b8c9d0"
    api_port: 8002
    ui_port: 3002
    api_key_env: "OPENAI_API_KEY_GHSPEC"

prompts_dir: "config/prompts"
hitl_path: "config/hitl/expanded_spec.txt"

stopping_rule:
  min_runs: 5
  max_runs: 25
  confidence_level: 0.95
  max_half_width_pct: 10  # Stop when CI half-width ≤10% of mean
  metrics:
    - AUTR
    - TOK_IN
    - T_WALL
    - CRUDe
    - ESR
    - MC

timeouts:
  step_timeout_seconds: 600  # 10 minutes per step
  health_check_interval_seconds: 5
  api_retry_attempts: 3
```

**Validation Logic**:
```python
def validate_config(config: dict) -> None:
    """Validate experiment.yaml schema."""
    required_keys = ['random_seed', 'frameworks', 'prompts_dir', 'hitl_path', 'stopping_rule', 'timeouts']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    for fw_name, fw_config in config['frameworks'].items():
        required_fw_keys = ['repo_url', 'commit_hash', 'api_port', 'ui_port', 'api_key_env']
        for key in required_fw_keys:
            if key not in fw_config:
                raise ValueError(f"Framework {fw_name} missing required key: {key}")
```

---

## 10. Logging Strategy

**Decision**: Structured JSON logging with consistent schema across all modules. Log levels: DEBUG (verbose), INFO (milestones), WARNING (retries), ERROR (failures). Separate log files per concern: orchestrator.log, stdout.log, stderr.log.

**Log Schema**:
```json
{
  "timestamp": "2025-10-08T14:30:15.123Z",
  "level": "INFO",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "framework": "baes",
  "step": 3,
  "event": "step_completed",
  "message": "Step 3 completed successfully",
  "metadata": {
    "duration_seconds": 120.5,
    "hitl_count": 1,
    "tokens_in": 1500,
    "tokens_out": 3200
  }
}
```

**Implementation**:
```python
import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage()
        }
        
        # Add custom fields from record
        if hasattr(record, 'run_id'):
            log_entry['run_id'] = record.run_id
        if hasattr(record, 'framework'):
            log_entry['framework'] = record.framework
        if hasattr(record, 'step'):
            log_entry['step'] = record.step
        if hasattr(record, 'metadata'):
            log_entry['metadata'] = record.metadata
            
        return json.dumps(log_entry)
```

**Alternatives Considered**:
- **Plain text logs**: Rejected—harder to parse programmatically
- **Single log file**: Rejected—mixing orchestrator/framework output complicates debugging
- **Database logging**: Rejected—files are simpler, self-contained

---

## Summary

All technical decisions align with constitutional principles (minimal dependencies, reproducibility, transparency, isolation). Implementation will proceed with:

- **Core**: Python 3.11 standard library
- **Config**: PyYAML for experiment.yaml parsing
- **HTTP**: requests for API calls and health checks
- **Testing**: pytest for unit/integration/contract tests
- **Analysis**: scipy + matplotlib (separate from core orchestrator)
- **Architecture**: Abstract adapter pattern with concrete implementations per framework
- **Storage**: JSON for metrics/logs, tar.gz for archives, YAML for configuration

No NEEDS CLARIFICATION items remain. Ready to proceed to Phase 1 (Design & Contracts).
