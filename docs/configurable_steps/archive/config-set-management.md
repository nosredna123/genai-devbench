# Config Set Management: Multi-Scenario Experiment Design

## 📋 Executive Summary

**Problem:** The current implementation hardcodes a single config set (prompts + HITL + experiment template), limiting genai-devbench's ability to support different experimental scenarios.

**Solution:** Implement a **Config Set** system that allows researchers to define and reuse different experimental configurations (prompt collections, HITL strategies, experiment templates).

**Impact:** Enables comparative research across different:
- Problem domains (CRUD apps, ML pipelines, microservices, etc.)
- Specification styles (detailed vs. high-level)
- HITL strategies (different clarification approaches)
- Step configurations (3 steps vs. 6 steps, different sequences)

---

## 🎯 Core Concept: Config Set

A **Config Set** is a named collection of:
1. **Prompts** - Step-by-step development instructions
2. **HITL Files** - Human-in-the-loop clarification content
3. **Experiment Template** - Base experiment.yaml configuration
4. **Metadata** - Description, version, author, tags

### Config Set Structure

```
config_sets/
├── default/                           # Default CRUD app scenario
│   ├── metadata.yaml                  # Config set metadata
│   ├── experiment_template.yaml       # Base experiment config
│   ├── prompts/
│   │   ├── step_1.txt
│   │   ├── step_2.txt
│   │   └── ... (up to N steps)
│   └── hitl/
│       ├── expanded_spec.txt
│       └── ghspec_clarification_guidelines.txt
│
├── microservices/                     # Microservices scenario
│   ├── metadata.yaml
│   ├── experiment_template.yaml
│   ├── prompts/
│   │   ├── step_1_service_design.txt
│   │   ├── step_2_api_gateway.txt
│   │   └── ... (8 steps)
│   └── hitl/
│       └── microservices_clarification.txt
│
├── ml_pipeline/                       # ML pipeline scenario
│   ├── metadata.yaml
│   ├── experiment_template.yaml
│   ├── prompts/
│   │   ├── step_1_data_ingestion.txt
│   │   ├── step_2_preprocessing.txt
│   │   └── ... (5 steps)
│   └── hitl/
│       └── ml_clarification.txt
│
└── minimal/                           # Minimal test scenario
    ├── metadata.yaml
    ├── experiment_template.yaml
    ├── prompts/
    │   └── step_1_hello_world.txt
    └── hitl/
        └── minimal_spec.txt
```

---

## 📐 Design Proposal

### Option 1: Config Set Registry (Recommended)

**Concept:** Centralized registry of config sets with metadata-driven discovery

#### Directory Structure

```
genai-devbench/
├── config_sets/                       # All config sets
│   ├── registry.yaml                  # Global registry
│   ├── default/                       # Default config set
│   │   ├── metadata.yaml
│   │   ├── experiment_template.yaml
│   │   ├── prompts/
│   │   └── hitl/
│   ├── microservices/
│   └── ml_pipeline/
│
├── config/                            # Symlink to default config set
│   ├── experiment.yaml -> ../config_sets/default/experiment_template.yaml
│   ├── prompts/ -> ../config_sets/default/prompts/
│   └── hitl/ -> ../config_sets/default/hitl/
│
└── scripts/
    ├── new_experiment.py              # Modified to accept --config-set
    └── list_config_sets.py            # New: List available config sets
```

#### Registry Structure (registry.yaml)

```yaml
# config_sets/registry.yaml
version: "1.0.0"

config_sets:
  default:
    path: "default"
    description: "Student/Course/Teacher CRUD application with FastAPI"
    steps: 6
    tags: [crud, fastapi, sqlite, baseline]
    author: "genai-devbench team"
    created: "2025-01-01"
    
  microservices:
    path: "microservices"
    description: "Microservices architecture with API gateway and service mesh"
    steps: 8
    tags: [microservices, kubernetes, grpc]
    author: "researcher@university.edu"
    created: "2025-02-15"
    
  ml_pipeline:
    path: "ml_pipeline"
    description: "ML training pipeline with data preprocessing and model serving"
    steps: 5
    tags: [ml, pipeline, tensorflow]
    author: "researcher@university.edu"
    created: "2025-03-01"
    
  minimal:
    path: "minimal"
    description: "Minimal single-step test scenario"
    steps: 1
    tags: [test, minimal, debug]
    author: "genai-devbench team"
    created: "2025-01-15"
```

#### Metadata Structure (metadata.yaml)

```yaml
# config_sets/default/metadata.yaml
name: "default"
version: "1.0.0"
description: "Student/Course/Teacher CRUD application with FastAPI"

author:
  name: "genai-devbench team"
  email: "support@genai-devbench.org"

created: "2025-01-01"
updated: "2025-10-21"

tags:
  - crud
  - fastapi
  - sqlite
  - baseline

# Step configuration
steps:
  count: 6
  descriptions:
    1: "Initial CRUD Implementation"
    2: "Add Enrollment Relationship"
    3: "Teacher Assignment"
    4: "Validation & Error Handling"
    5: "Pagination & Filtering"
    6: "User Interface"

# HITL configuration
hitl:
  strategy: "expanded_spec"
  files:
    - "expanded_spec.txt"
    - "ghspec_clarification_guidelines.txt"

# Experiment defaults
experiment_defaults:
  model: "gpt-4o-mini"
  max_runs: 50
  min_runs: 30
  confidence_level: 0.95
  
# Validation constraints
constraints:
  min_steps: 1
  max_steps: 6
  required_frameworks: []
  recommended_frameworks: ["baes", "chatdev", "ghspec"]

# Documentation
documentation:
  readme: "README.md"
  examples: "examples/"
  references:
    - "https://example.com/fastapi-guide"
```

#### Experiment Template (experiment_template.yaml)

```yaml
# config_sets/default/experiment_template.yaml
# This is a TEMPLATE - values will be merged with user inputs during generation

# Base configuration that applies to all experiments using this config set
experiment_name: "${EXPERIMENT_NAME}"  # Replaced during generation
model: "${MODEL}"                      # Replaced during generation

# Fixed random seed for deterministic execution
random_seed: 42

# Config set reference (injected automatically)
config_set:
  name: "default"
  version: "1.0.0"
  source: "config_sets/default"

# Steps configuration (default for this config set)
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD Implementation"
    prompt_file: "config/prompts/step_1.txt"
  - id: 2
    enabled: true
    name: "Add Enrollment Relationship"
    prompt_file: "config/prompts/step_2.txt"
  # ... more steps

# HITL paths relative to config set
prompts_dir: "config/prompts"
hitl_path: "config/hitl/expanded_spec.txt"

# Stopping rule (can be overridden during generation)
stopping_rule:
  max_runs: 50
  min_runs: 30
  confidence_level: 0.95
  metrics:
    - functional_correctness
    - design_quality

# Framework configurations (merged with user selection)
frameworks:
  baes:
    enabled: false  # Will be set during generation
    repo_url: "https://github.com/gesad-lab/baes_demo"
    # ... framework-specific config
    
  chatdev:
    enabled: false
    repo_url: "https://github.com/OpenBMB/ChatDev.git"
    # ... framework-specific config

# Timeouts (config set specific)
timeouts:
  step: 1800
  total_run: 10800
  setup: 600

# Metrics configuration (config set specific)
metrics:
  reliable_metrics:
    functional_correctness:
      weight: 0.35
      # ... metric config
    design_quality:
      weight: 0.25
      # ... metric config
```

---

### Usage Flow

#### 1. List Available Config Sets

```bash
$ python scripts/list_config_sets.py

Available Config Sets:
======================

1. default (v1.0.0) ⭐ [default]
   Description: Student/Course/Teacher CRUD application with FastAPI
   Steps: 6
   Tags: crud, fastapi, sqlite, baseline
   Created: 2025-01-01

2. microservices (v1.0.0)
   Description: Microservices architecture with API gateway and service mesh
   Steps: 8
   Tags: microservices, kubernetes, grpc
   Created: 2025-02-15

3. ml_pipeline (v1.0.0)
   Description: ML training pipeline with data preprocessing
   Steps: 5
   Tags: ml, pipeline, tensorflow
   Created: 2025-03-01

4. minimal (v1.0.0)
   Description: Minimal single-step test scenario
   Steps: 1
   Tags: test, minimal, debug
   Created: 2025-01-15

Use --config-set <name> to specify a config set when creating an experiment.
```

#### 2. Create Experiment with Config Set

```bash
# Use default config set (implicit)
$ python scripts/new_experiment.py \
    --name crud_experiment \
    --model gpt-4o-mini \
    --frameworks baes,chatdev,ghspec \
    --runs 50

# Use specific config set (explicit)
$ python scripts/new_experiment.py \
    --name microservices_experiment \
    --model gpt-4o-mini \
    --frameworks baes,chatdev \
    --runs 30 \
    --config-set microservices

# Use custom config set (from path)
$ python scripts/new_experiment.py \
    --name custom_experiment \
    --model gpt-4o-mini \
    --frameworks baes \
    --runs 20 \
    --config-set-path /path/to/my_config_set
```

#### 3. Generated Experiment Structure

```
crud_experiment/
├── config.yaml                        # Merged config
│   └── config_set:                    # Tracks source config set
│         name: "default"
│         version: "1.0.0"
│         source: "config_sets/default"
│
├── config/
│   ├── prompts/                       # Copied from config set
│   │   ├── step_1.txt
│   │   └── ...
│   └── hitl/                          # Copied from config set
│       └── expanded_spec.txt
│
├── src/                               # Standard experiment code
├── runs/                              # Results (empty initially)
└── docs/                              # Documentation
```

---

## 🔧 Implementation Plan

### Phase 1: Config Set Infrastructure (2 hours)

#### Task 1.1: Create Config Set Registry
- Create `config_sets/` directory
- Create `registry.yaml`
- Create `config_sets/default/metadata.yaml`
- Move current `config/` contents to `config_sets/default/`

#### Task 1.2: Config Set Loader
```python
# New file: src/utils/config_set_loader.py

class ConfigSetLoader:
    def __init__(self, registry_path: Path = Path("config_sets/registry.yaml")):
        self.registry_path = registry_path
        self.registry = self._load_registry()
    
    def list_config_sets(self) -> List[Dict]:
        """List all available config sets."""
        pass
    
    def get_config_set(self, name: str) -> ConfigSet:
        """Load a specific config set."""
        pass
    
    def validate_config_set(self, path: Path) -> bool:
        """Validate config set structure."""
        pass

class ConfigSet:
    def __init__(self, path: Path):
        self.path = path
        self.metadata = self._load_metadata()
        self.experiment_template = self._load_template()
    
    def get_prompts_dir(self) -> Path:
        """Get prompts directory path."""
        return self.path / "prompts"
    
    def get_hitl_dir(self) -> Path:
        """Get HITL directory path."""
        return self.path / "hitl"
    
    def get_steps_config(self) -> List[Dict]:
        """Get steps configuration from template."""
        pass
```

#### Task 1.3: Update Generator
```python
# Modify: generator/standalone_generator.py

class StandaloneGenerator:
    def __init__(
        self,
        project_root: Path,
        config_set_name: str = "default",  # NEW PARAMETER
        config_set_path: Optional[Path] = None  # NEW PARAMETER
    ):
        self.project_root = project_root
        self.config_set = self._load_config_set(
            config_set_name, 
            config_set_path
        )
    
    def _load_config_set(
        self, 
        name: str, 
        custom_path: Optional[Path]
    ) -> ConfigSet:
        """Load config set from registry or custom path."""
        if custom_path:
            # Load from custom path
            return ConfigSet(custom_path)
        else:
            # Load from registry
            loader = ConfigSetLoader()
            return loader.get_config_set(name)
    
    def generate(self, config: Dict, output_dir: Path) -> Path:
        """Generate experiment using config set."""
        # Copy prompts from config set
        self._copy_config_set_files(output_dir)
        
        # Merge experiment template with user config
        merged_config = self._merge_config(config)
        
        # ... rest of generation
```

---

### Phase 2: CLI Integration (1 hour)

#### Task 2.1: Update new_experiment.py

```python
# Modify: scripts/new_experiment.py

def parse_args():
    parser = argparse.ArgumentParser(...)
    
    # ADD NEW ARGUMENTS
    parser.add_argument(
        '--config-set',
        default='default',
        help='Config set to use (default: default)'
    )
    
    parser.add_argument(
        '--config-set-path',
        type=Path,
        help='Custom config set path (overrides --config-set)'
    )
    
    parser.add_argument(
        '--list-config-sets',
        action='store_true',
        help='List available config sets and exit'
    )
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Handle list config sets
    if args.list_config_sets:
        list_config_sets()
        return 0
    
    # Create generator with config set
    generator = StandaloneGenerator(
        project_root=Path.cwd(),
        config_set_name=args.config_set,
        config_set_path=args.config_set_path
    )
    
    # ... rest of generation
```

#### Task 2.2: Create list_config_sets.py

```python
# New file: scripts/list_config_sets.py

def main():
    loader = ConfigSetLoader()
    config_sets = loader.list_config_sets()
    
    print("\nAvailable Config Sets:")
    print("=" * 50)
    
    for cs in config_sets:
        marker = "⭐ [default]" if cs['name'] == 'default' else ""
        print(f"\n{cs['name']} (v{cs['version']}) {marker}")
        print(f"  Description: {cs['description']}")
        print(f"  Steps: {cs['steps']}")
        print(f"  Tags: {', '.join(cs['tags'])}")
    
    print("\nUse --config-set <name> to specify a config set.")
```

---

### Phase 3: Config Set Examples (2 hours)

#### Task 3.1: Create Microservices Config Set

```
config_sets/microservices/
├── metadata.yaml
├── experiment_template.yaml
├── prompts/
│   ├── step_1_service_design.txt     # Design service boundaries
│   ├── step_2_api_gateway.txt        # Implement API gateway
│   ├── step_3_user_service.txt       # User management service
│   ├── step_4_order_service.txt      # Order management service
│   ├── step_5_communication.txt      # Inter-service communication
│   ├── step_6_database.txt           # Database per service
│   ├── step_7_deployment.txt         # Docker/K8s deployment
│   └── step_8_monitoring.txt         # Observability
└── hitl/
    └── microservices_clarification.txt
```

#### Task 3.2: Create ML Pipeline Config Set

```
config_sets/ml_pipeline/
├── metadata.yaml
├── experiment_template.yaml
├── prompts/
│   ├── step_1_data_ingestion.txt     # Data loading pipeline
│   ├── step_2_preprocessing.txt      # Feature engineering
│   ├── step_3_training.txt           # Model training
│   ├── step_4_evaluation.txt         # Model evaluation
│   └── step_5_serving.txt            # Model serving API
└── hitl/
    └── ml_clarification.txt
```

#### Task 3.3: Create Minimal Config Set

```
config_sets/minimal/
├── metadata.yaml
├── experiment_template.yaml
├── prompts/
│   └── step_1_hello_world.txt        # Simple hello world app
└── hitl/
    └── minimal_spec.txt
```

---

### Phase 4: Documentation (1 hour)

#### Task 4.1: Create Config Set Guide

```markdown
# docs/config_sets_guide.md

## Creating Custom Config Sets

### Structure
- metadata.yaml - Config set metadata
- experiment_template.yaml - Base experiment config
- prompts/ - Step prompt files
- hitl/ - HITL clarification files

### Example: Creating a REST API Config Set
...
```

#### Task 4.2: Update Quickstart

```markdown
# docs/quickstart.md

## Using Different Config Sets

genai-devbench supports multiple config sets for different
experimental scenarios...
```

---

## 🎯 Benefits

### 1. Research Flexibility
- ✅ Compare frameworks across different problem domains
- ✅ Test different prompt strategies
- ✅ Evaluate HITL effectiveness
- ✅ Standardize experimental scenarios

### 2. Reusability
- ✅ Share config sets between researchers
- ✅ Version control experimental setups
- ✅ Reproduce experiments exactly
- ✅ Build library of scenarios

### 3. Extensibility
- ✅ Easy to add new scenarios
- ✅ No code changes needed
- ✅ Community contributions
- ✅ Domain-specific experiments

### 4. Maintainability
- ✅ Centralized config management
- ✅ Clear separation of concerns
- ✅ Easier testing
- ✅ Better documentation

---

## 🔄 Integration with Configurable Steps

Config Sets and Configurable Steps work together:

1. **Config Set** defines the **available steps** (prompts, metadata)
2. **Configurable Steps** lets you **enable/disable** those steps

**Example:**
```yaml
# microservices config set has 8 steps defined
# User can enable only first 5 for their experiment

steps:
  - id: 1
    enabled: true    # Use step from config set
  - id: 2
    enabled: true
  - id: 3
    enabled: true
  - id: 4
    enabled: true
  - id: 5
    enabled: true
  - id: 6
    enabled: false   # Skip this step
  - id: 7
    enabled: false
  - id: 8
    enabled: false
```

---

## 📊 Migration Strategy

### Backwards Compatibility

**Current Setup (Before):**
```
genai-devbench/
├── config/
│   ├── experiment.yaml
│   ├── prompts/
│   └── hitl/
```

**New Setup (After):**
```
genai-devbench/
├── config_sets/
│   ├── registry.yaml
│   └── default/              # Old config/ moved here
│       ├── metadata.yaml
│       ├── experiment_template.yaml
│       ├── prompts/
│       └── hitl/
├── config/                   # Symlink to default OR deprecated
```

**Migration Steps:**
1. Create `config_sets/default/` directory
2. Move `config/*` to `config_sets/default/`
3. Create `metadata.yaml` and `experiment_template.yaml`
4. Update generator to use config sets
5. Keep `config/` as symlink for backwards compatibility (optional)

**No Breaking Changes:**
- Existing experiments continue to work
- `config/` can remain as symlink to default config set
- CLI without `--config-set` uses "default"

---

## 🚀 Timeline Summary

| Phase | Description | Duration | Dependencies |
|-------|-------------|----------|--------------|
| Phase 1 | Config Set Infrastructure | 2 hours | None |
| Phase 2 | CLI Integration | 1 hour | Phase 1 |
| Phase 3 | Example Config Sets | 2 hours | Phase 1 |
| Phase 4 | Documentation | 1 hour | Phase 1-3 |
| **Total** | | **6 hours** | |

---

## 🤔 Discussion Points

### 1. Config Set Validation
**Question:** How strict should validation be?
- Require all fields in metadata.yaml?
- Validate prompt file naming (step_N.txt)?
- Check experiment_template.yaml schema?

**Recommendation:** Strict validation with clear errors

### 2. Config Set Versioning
**Question:** How to handle config set updates?
- Semantic versioning?
- Experiment tracks config set version?
- Allow experiments to update config set?

**Recommendation:** Track version in generated experiment, allow manual updates

### 3. Custom Config Set Discovery
**Question:** Should we support config sets from external locations?
- Environment variable (GENAI_DEVBENCH_CONFIG_SETS)?
- Multiple registry files?
- Remote config sets (git repositories)?

**Recommendation:** Start with local only, add remote later

### 4. Config Set Inheritance
**Question:** Should config sets support inheritance?
```yaml
# microservices_advanced config set
inherits: "microservices"
steps:
  9: "step_9_service_mesh.txt"  # Add new step
```

**Recommendation:** V2 feature, not V1

---

## ✅ Next Steps

1. **Review this proposal** with team
2. **Discuss design decisions** above
3. **Validate config set structure** with real use cases
4. **Start Phase 1 implementation** (Config Set Infrastructure)
5. **Migrate default config** to config set
6. **Test with multiple scenarios**

---

## 📚 Related Documents

- [Configurable Steps Feature Spec](feature-spec.md)
- [Configurable Steps Implementation Plan](implementation-plan.md)
- [Data Model](data-model.md)
- [API Contracts](contracts/api-contracts.md)

---

**Status:** 📝 Design Proposal - Awaiting Review  
**Author:** AI Assistant  
**Date:** 2025-10-21  
**Version:** 1.0.0
