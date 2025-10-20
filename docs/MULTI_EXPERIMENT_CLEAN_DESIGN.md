# Multi-Experiment Management: Clean Design (No Backward Compatibility)

**Date:** October 20, 2025  
**Status:** Proposed Clean-Slate Design  
**Constraint:** No backward compatibility required

---

## 🎯 Design Philosophy

**Simple. Clean. Explicit.**

No legacy modes, no fallbacks, no complexity. Every experiment is:
1. **Self-contained**: All config + outputs in one directory
2. **Explicit**: Config defines everything (no defaults, no assumptions)
3. **Validated**: Hash-checked before every run
4. **Organized**: Standardized structure across all experiments

---

## 📂 Directory Structure

### Project Root
```
genai-devbench/
├── experiments/                      # ALL experiments live here
│   ├── baseline_gpt4o_mini/
│   ├── baes_deep_dive_gpt5/
│   └── quick_test_o1_mini/
│
├── config/                           # TEMPLATES ONLY (not used directly)
│   ├── experiment.template.yaml     # Template for new experiments
│   └── prompts/                     # Shared prompt files
│
├── src/                              # Source code (unchanged)
├── scripts/                          # Experiment management tools
│   ├── new_experiment.py            # Create new experiment
│   ├── run_experiment.py            # Run experiment (replaces shell script)
│   ├── analyze_experiment.py        # Analyze experiment
│   └── list_experiments.py          # List all experiments
│
└── .experiments.json                # Global experiment registry
```

### Individual Experiment Structure
```
experiments/baseline_gpt4o_mini/
├── config.yaml                       # Complete experiment config (SINGLE SOURCE OF TRUTH)
│
├── runs/                             # Run artifacts
│   ├── manifest.json                 # Run registry
│   ├── baes/
│   │   ├── <run_id_1>/
│   │   │   ├── workspace/            # Generated code
│   │   │   ├── logs/                 # Execution logs
│   │   │   ├── metrics.json          # Aggregate metrics
│   │   │   └── step_metrics.json     # Per-step metrics
│   │   └── <run_id_2>/
│   ├── chatdev/
│   └── ghspec/
│
├── analysis/                         # Analysis outputs
│   ├── report.md                     # Statistical report
│   └── visualizations/               # Charts
│       ├── radar_framework_profile.png
│       ├── scatter_token_efficiency.png
│       └── ...
│
├── .meta/                            # Experiment metadata (auto-generated)
│   ├── config_hash.txt               # SHA-256 of canonical config
│   ├── created_at.txt                # ISO timestamp
│   ├── updated_at.txt                # Last run timestamp
│   └── status.txt                    # in_progress | completed | failed
│
└── README.md                         # Auto-generated experiment summary
```

---

## 📝 Configuration Schema

### experiments/<name>/config.yaml

```yaml
# =============================================================================
# EXPERIMENT METADATA
# =============================================================================
experiment:
  name: "baseline_gpt4o_mini"
  description: "Baseline comparison of 3 frameworks using GPT-4o-mini"
  created_at: "2025-10-20T14:30:00Z"
  created_by: "researcher_name"
  tags:
    - baseline
    - gpt4o-mini
    - three-way-comparison

# =============================================================================
# EXECUTION CONFIGURATION
# =============================================================================
random_seed: 42

model: "gpt-4o-mini"

frameworks:
  baes:
    enabled: true
    repo_url: "https://github.com/gesad-lab/baes_demo"
    commit_hash: "1dd573633a98b8baa636c200bc1684cec7a8179f"
    api_port: 8100
    ui_port: 8600
    max_retries: 3
    auto_restart_servers: false
    use_venv: true
    api_key_env: "OPENAI_API_KEY_BAES"
    
  chatdev:
    enabled: true
    repo_url: "https://github.com/OpenBMB/ChatDev.git"
    commit_hash: "52edb89997b4312ad27d8c54584d0a6c59940135"
    api_port: 8001
    ui_port: 3001
    api_key_env: "OPENAI_API_KEY_CHATDEV"
    
  ghspec:
    enabled: true
    repo_url: "https://github.com/github/spec-kit.git"
    commit_hash: "89f4b0b38a42996376c0f083d47281a4c9196761"
    api_port: 8002
    ui_port: 3002
    api_key_env: "OPENAI_API_KEY_GHSPEC"

# Prompts directory (relative to project root, NOT experiment dir)
prompts_dir: "config/prompts"

# HITL path (relative to project root)
hitl_path: "config/hitl/expanded_spec.txt"

stopping_rule:
  min_runs: 5
  max_runs: 50
  confidence_level: 0.95
  max_half_width_pct: 10
  metrics:
    - TOK_IN
    - T_WALL_seconds
    - COST_USD

timeouts:
  step_timeout_seconds: 600
  health_check_interval_seconds: 5
  api_retry_attempts: 3

analysis:
  bootstrap_samples: 10000
  significance_level: 0.05
  confidence_level: 0.95
  effect_size_thresholds:
    negligible: 0.147
    small: 0.330
    medium: 0.474

# =============================================================================
# METRICS, PRICING, VISUALIZATIONS, REPORT
# =============================================================================
# (Same as current experiment.yaml - no changes needed)

metrics:
  # ... (keep existing metrics config)

pricing:
  # ... (keep existing pricing config)

visualizations:
  # ... (keep existing visualizations config)

report:
  # ... (keep existing report config)
```

---

## 🛠️ Core Utilities

### 1. Experiment Path Manager

**File**: `src/utils/experiment_paths.py` (REPLACES path_resolver.py)

```python
"""
Experiment path management.

All paths are derived from experiment directory. No legacy modes.
"""

from pathlib import Path
from typing import Optional
import hashlib
import json
import yaml


class ExperimentPaths:
    """Manages all paths for an experiment."""
    
    def __init__(self, experiment_name: str, project_root: Optional[Path] = None):
        """
        Initialize experiment paths.
        
        Args:
            experiment_name: Name of the experiment
            project_root: Project root directory (auto-detected if not provided)
        """
        if project_root is None:
            # Auto-detect project root (where .git or experiments/ exists)
            current = Path.cwd()
            while current != current.parent:
                if (current / "experiments").exists() or (current / ".git").exists():
                    project_root = current
                    break
                current = current.parent
            else:
                raise ValueError("Could not detect project root")
        
        self.project_root = Path(project_root)
        self.experiment_name = experiment_name
        self.experiment_dir = self.project_root / "experiments" / experiment_name
        
        # Validate experiment exists
        if not self.experiment_dir.exists():
            raise ValueError(
                f"Experiment '{experiment_name}' not found.\n"
                f"Expected: {self.experiment_dir}\n"
                f"Use: python scripts/new_experiment.py to create it."
            )
        
        # Load config
        self.config_path = self.experiment_dir / "config.yaml"
        if not self.config_path.exists():
            raise ValueError(f"Config not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    # Directory paths
    @property
    def runs_dir(self) -> Path:
        """Get runs directory."""
        return self.experiment_dir / "runs"
    
    @property
    def analysis_dir(self) -> Path:
        """Get analysis directory."""
        return self.experiment_dir / "analysis"
    
    @property
    def visualizations_dir(self) -> Path:
        """Get visualizations directory."""
        return self.analysis_dir / "visualizations"
    
    @property
    def meta_dir(self) -> Path:
        """Get metadata directory."""
        return self.experiment_dir / ".meta"
    
    # File paths
    @property
    def manifest_path(self) -> Path:
        """Get manifest file path."""
        return self.runs_dir / "manifest.json"
    
    @property
    def config_hash_path(self) -> Path:
        """Get config hash file path."""
        return self.meta_dir / "config_hash.txt"
    
    @property
    def status_path(self) -> Path:
        """Get status file path."""
        return self.meta_dir / "status.txt"
    
    @property
    def report_path(self) -> Path:
        """Get report file path."""
        return self.analysis_dir / "report.md"
    
    # Shared resource paths (in project root)
    @property
    def prompts_dir(self) -> Path:
        """Get prompts directory (shared across experiments)."""
        return self.project_root / self.config.get('prompts_dir', 'config/prompts')
    
    @property
    def hitl_path(self) -> Path:
        """Get HITL file path (shared across experiments)."""
        return self.project_root / self.config.get('hitl_path', 'config/hitl/expanded_spec.txt')
    
    # Config hash
    def compute_config_hash(self) -> str:
        """
        Compute SHA-256 hash of canonical config fields.
        
        Only hashes fields that affect experimental validity.
        """
        # Fields that invalidate results if changed
        canonical_fields = {
            'model': self.config.get('model'),
            'frameworks': {
                k: v for k, v in self.config.get('frameworks', {}).items()
                if v.get('enabled', False)
            },
            'stopping_rule': self.config.get('stopping_rule'),
            'metrics': {
                'reliable_metrics': self.config.get('metrics', {}).get('reliable_metrics'),
                'derived_metrics': self.config.get('metrics', {}).get('derived_metrics'),
            },
            'pricing': self.config.get('pricing'),
            'random_seed': self.config.get('random_seed'),
        }
        
        config_str = json.dumps(canonical_fields, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def validate_config_hash(self) -> None:
        """
        Validate that config hasn't changed since experiment started.
        
        Raises:
            ValueError: If hash mismatch detected
        """
        if not self.config_hash_path.exists():
            # First run - save hash
            self.meta_dir.mkdir(parents=True, exist_ok=True)
            current_hash = self.compute_config_hash()
            self.config_hash_path.write_text(current_hash)
            return
        
        # Compare hashes
        stored_hash = self.config_hash_path.read_text().strip()
        current_hash = self.compute_config_hash()
        
        if stored_hash != current_hash:
            raise ValueError(
                f"❌ Configuration has changed since experiment started!\n\n"
                f"Experiment: {self.experiment_name}\n"
                f"Stored hash:  {stored_hash[:16]}...\n"
                f"Current hash: {current_hash[:16]}...\n\n"
                f"This could invalidate your results.\n"
                f"Options:\n"
                f"  1. Revert config changes\n"
                f"  2. Create a new experiment with the new config\n"
                f"  3. Force update hash (not recommended):\n"
                f"     rm {self.config_hash_path}"
            )
    
    def ensure_structure(self) -> None:
        """Create experiment directory structure if missing."""
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.visualizations_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
    
    def get_run_dir(self, framework: str, run_id: str) -> Path:
        """Get path for specific run."""
        return self.runs_dir / framework / run_id
    
    def __repr__(self) -> str:
        return f"ExperimentPaths('{self.experiment_name}')"


def get_experiment_paths(experiment_name: str) -> ExperimentPaths:
    """
    Get ExperimentPaths instance for an experiment.
    
    Args:
        experiment_name: Name of the experiment
        
    Returns:
        ExperimentPaths instance
    """
    return ExperimentPaths(experiment_name)
```

---

## 🚀 New Workflow

### 1. Create Experiment

```bash
# Interactive wizard
python scripts/new_experiment.py

# Or with arguments
python scripts/new_experiment.py \
  --name "baseline_gpt4o_mini" \
  --model "gpt-4o-mini" \
  --frameworks "baes,chatdev,ghspec" \
  --max-runs 50 \
  --description "Baseline 3-way comparison for paper"
```

**Output:**
```
✓ Created experiment: experiments/baseline_gpt4o_mini/
✓ Config: experiments/baseline_gpt4o_mini/config.yaml
✓ Structure: runs/, analysis/, .meta/
✓ README: experiments/baseline_gpt4o_mini/README.md

Next steps:
  1. Review config: cat experiments/baseline_gpt4o_mini/config.yaml
  2. Run experiment: python scripts/run_experiment.py baseline_gpt4o_mini
```

### 2. Run Experiment

```bash
# Run all enabled frameworks
python scripts/run_experiment.py baseline_gpt4o_mini

# Run specific framework
python scripts/run_experiment.py baseline_gpt4o_mini --framework baes

# Run multiple rounds
python scripts/run_experiment.py baseline_gpt4o_mini --rounds 10
```

**Auto-validates config hash before every run!**

### 3. Analyze Results

```bash
# Analyze experiment
python scripts/analyze_experiment.py baseline_gpt4o_mini

# Output:
#   experiments/baseline_gpt4o_mini/analysis/report.md
#   experiments/baseline_gpt4o_mini/analysis/visualizations/*.png
```

### 4. List Experiments

```bash
# List all experiments
python scripts/list_experiments.py

# Output:
# Experiments:
#   1. baseline_gpt4o_mini (in_progress, 47/150 runs)
#   2. baes_deep_dive_gpt5 (pending, 0/100 runs)
#   3. quick_test_o1 (completed, 15/15 runs)
```

### 5. Compare Experiments

```bash
# Compare multiple experiments
python scripts/compare_experiments.py \
  baseline_gpt4o_mini \
  baes_deep_dive_gpt5 \
  --output comparison_report.md
```

---

## 🗂️ Global Experiment Registry

**File**: `.experiments.json` (in project root)

```json
{
  "version": "1.0",
  "experiments": {
    "baseline_gpt4o_mini": {
      "path": "experiments/baseline_gpt4o_mini",
      "config_hash": "a7f3c9b2d4e5f6a8c9d0e1f2a3b4c5d6",
      "created_at": "2025-10-20T14:30:00Z",
      "updated_at": "2025-10-20T16:45:00Z",
      "status": "in_progress",
      "model": "gpt-4o-mini",
      "frameworks": {
        "baes": {"enabled": true, "runs": 47},
        "chatdev": {"enabled": true, "runs": 50},
        "ghspec": {"enabled": true, "runs": 50}
      },
      "total_runs": 147,
      "max_runs": 150,
      "stopping_rule_met": false
    },
    "baes_deep_dive_gpt5": {
      "path": "experiments/baes_deep_dive_gpt5",
      "config_hash": "b8c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0",
      "created_at": "2025-10-21T09:00:00Z",
      "updated_at": "2025-10-21T09:00:00Z",
      "status": "pending",
      "model": "gpt-5",
      "frameworks": {
        "baes": {"enabled": true, "runs": 0}
      },
      "total_runs": 0,
      "max_runs": 100,
      "stopping_rule_met": false
    }
  }
}
```

**Auto-updated on every run!**

---

## 🔧 Code Changes Required

### Files to Create

1. ✅ `src/utils/experiment_paths.py` - Path management
2. ✅ `scripts/new_experiment.py` - Create experiments
3. ✅ `scripts/run_experiment.py` - Run experiments (replaces shell script)
4. ✅ `scripts/analyze_experiment.py` - Analyze experiments
5. ✅ `scripts/list_experiments.py` - List experiments
6. ✅ `scripts/compare_experiments.py` - Compare experiments
7. ✅ `src/utils/experiment_registry.py` - Registry management

### Files to Update

1. 🔄 `src/orchestrator/runner.py` - Use ExperimentPaths
2. 🔄 `src/orchestrator/manifest_manager.py` - Use experiment-specific manifest
3. 🔄 `src/utils/isolation.py` - Use experiment-specific runs_dir
4. 🔄 `src/analysis/report_generator.py` - Use experiment-specific analysis_dir
5. 🔄 `src/analysis/visualization_factory.py` - Use experiment-specific viz dir

### Files to Remove

1. ❌ `runners/run_experiment.sh` - Replaced by Python script
2. ❌ `runners/analyze_results.sh` - Replaced by Python script
3. ❌ `runs/` directory - Moved into experiments/
4. ❌ `analysis_output/` directory - Moved into experiments/

---

## 📦 Migration Plan

### Step 1: Create experiments/ directory

```bash
mkdir -p experiments
```

### Step 2: Move existing runs to experiment (if any)

```bash
python scripts/migrate_to_experiments.py \
  --from ./runs \
  --to experiments/legacy_baseline \
  --name "legacy_baseline" \
  --model "gpt-4o-mini"
```

### Step 3: Remove old structure

```bash
# Backup first!
tar -czf backup_old_structure_$(date +%Y%m%d).tar.gz runs/ analysis_output/

# Remove
rm -rf runs/
rm -rf analysis_output/
rm runners/run_experiment.sh
rm runners/analyze_results.sh
```

### Step 4: Update all code

```bash
# Run migration script that updates all imports and paths
python scripts/migrate_codebase.py
```

---

## ✨ Benefits of Clean Design

### 1. **Simplicity**
- No legacy modes to maintain
- No fallback logic
- One way to do things

### 2. **Clarity**
- Everything explicit in config
- No hidden defaults
- Clear experiment boundaries

### 3. **Safety**
- Config hash validated every run
- Can't mix runs from different configs
- Clear error messages

### 4. **Organization**
- All experiments in one place
- Standardized structure
- Self-documenting

### 5. **Scalability**
- Easy to add new experiments
- Easy to compare experiments
- Easy to archive/share experiments

---

## 🎯 Your Use Case Example

### Day 1: Baseline Comparison

```bash
python scripts/new_experiment.py \
  --name "baseline_gpt4o_mini" \
  --model "gpt-4o-mini" \
  --frameworks "baes,chatdev,ghspec" \
  --max-runs 50

python scripts/run_experiment.py baseline_gpt4o_mini --rounds 10
```

**Result**: `experiments/baseline_gpt4o_mini/` with 150 runs (50×3)

### Day 2: BAEs Deep Dive

```bash
python scripts/new_experiment.py \
  --name "baes_deep_dive_gpt5" \
  --model "gpt-5" \
  --frameworks "baes" \
  --max-runs 100

python scripts/run_experiment.py baes_deep_dive_gpt5 --rounds 20
```

**Result**: `experiments/baes_deep_dive_gpt5/` with 100 runs

### Day 3: Quick Test

```bash
python scripts/new_experiment.py \
  --name "quick_test_o1_mini" \
  --model "o1-mini" \
  --frameworks "chatdev" \
  --max-runs 5

python scripts/run_experiment.py quick_test_o1_mini
```

**Result**: `experiments/quick_test_o1_mini/` with 5 runs

### Day 4: Compare All

```bash
python scripts/compare_experiments.py \
  baseline_gpt4o_mini \
  baes_deep_dive_gpt5 \
  quick_test_o1_mini \
  --output experiments/comparison_report.md
```

---

## 📋 Implementation Estimate

| Task | Time | Priority |
|------|------|----------|
| Create ExperimentPaths utility | 2h | HIGH |
| Create new_experiment.py script | 2h | HIGH |
| Update runner.py | 1h | HIGH |
| Update manifest_manager.py | 1h | HIGH |
| Create run_experiment.py | 2h | MEDIUM |
| Create analyze_experiment.py | 1h | MEDIUM |
| Create list_experiments.py | 1h | LOW |
| Create compare_experiments.py | 3h | LOW |
| Create migration script | 2h | MEDIUM |
| Update all imports/paths | 2h | HIGH |
| Testing | 3h | HIGH |

**Total: ~20 hours** (2.5 days of focused work)

---

## 🚀 Ready to Implement?

This clean design gives you:
- ✅ Multiple experiments managed cleanly
- ✅ Config-driven output organization
- ✅ Automatic validation
- ✅ Simple, explicit workflow
- ✅ Easy comparison across experiments

**No legacy baggage. Just clean, simple, effective.**

Want me to start implementing? Which part first?

1. **ExperimentPaths utility** (foundation)
2. **new_experiment.py script** (create experiments)
3. **Update core modules** (runner, manifest)
4. **Migration script** (move existing data)
