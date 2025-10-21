# Final Implementation Plan: Integrated Config Sets + Configurable Steps

**Date:** 2025-10-21  
**Status:** READY FOR IMPLEMENTATION  
**Estimated Effort:** 12-16 hours

---

## 🎯 Executive Summary

This document provides the complete implementation plan for the integrated **Config Sets + Configurable Steps** system. All design ambiguities have been resolved through two rounds of clarifications with the researcher.

### Key Architecture Insight

The system operates in **two distinct stages**:

1. **Generator Stage (genai-devbench repo)**: Contains curated config sets as templates
2. **Generated Experiment Stage (separate directory)**: Independent, fully flexible workspace

**Critical Design Decision:** No `--steps` flag at generation time. Generator **always copies all steps/prompts/HITL** from selected config set. Researchers edit `config.yaml` post-generation for customization.

---

## 📋 Table of Contents

1. [Design Decisions Summary](#design-decisions-summary)
2. [Architecture Overview](#architecture-overview)
3. [Data Model](#data-model)
4. [Implementation Phases](#implementation-phases)
5. [Testing Strategy](#testing-strategy)
6. [Migration & Rollout](#migration--rollout)

---

## 🎨 Design Decisions Summary

All decisions validated through Round 2 clarifications:

| Category | Decision | Rationale |
|----------|----------|-----------|
| **Generator Behavior** | Always copy ALL steps/prompts/HITL | Simple, researcher customizes post-generation |
| **Step Selection** | No `--steps` flag | Eliminates complexity, clear separation of concerns |
| **Default State** | All steps `enabled: true` | Researcher disables unwanted steps manually |
| **Copy Strategy** | Copy files, not reference | Complete independence, reproducibility |
| **Metadata Tracking** | Full amnesia (no source tracking) | Generated experiment is self-contained |
| **Execution Order** | By declaration order in YAML | Intuitive, easy to reorder |
| **Metrics Tracking** | Preserve original step IDs | Semantic meaning preserved |
| **Validation** | Fail-fast always | Prevents wasted runs, clear errors |
| **Discovery** | Distributed metadata (scan dirs) | Self-contained config sets, easy to add |
| **Config Set Location** | Local only (V1) | Simple, external support in V2 if needed |
| **Prompt Naming** | Numbered + semantic (01_name.txt) | Self-documenting, sortable |
| **Dependencies** | No step dependencies (V1) | Simple, researcher responsibility |
| **Initial Config Sets** | `default` + `minimal` | Compatibility + testing |
| **Validation Level** | Strict structure, basic content | High quality templates |
| **Implementation** | Big bang (V1 complete) | All features together, clean integration |

---

## 🏗️ Architecture Overview

### Two-Stage Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: GENERATOR (genai-devbench repo)         │
│                                                                       │
│  config_sets/                                                         │
│  ├── default/                  ┌──────────────────────────────────┐ │
│  │   ├── metadata.yaml         │ Curated Templates                │ │
│  │   ├── experiment_template.yaml │ - Fixed (project-maintained) │ │
│  │   ├── prompts/              │ - Quality controlled            │ │
│  │   │   ├── 01_student.txt    │ - Common scenarios             │ │
│  │   │   ├── 02_course.txt     └──────────────────────────────────┘ │
│  │   │   └── ...                                                    │
│  │   └── hitl/                                                      │
│  │       └── expanded_spec.txt                                      │
│  ├── minimal/                                                        │
│  │   └── ...                                                         │
│  └── microservices/ (future)                                        │
│                                                                       │
│  Generator Command:                                                  │
│  $ python scripts/new_experiment.py \                               │
│      --name my_test \                                               │
│      --config-set default \                                         │
│      --frameworks chatdev metagpt \                                 │
│      --model gpt-4o-mini                                            │
│                                                                       │
│  ▼ ALWAYS copies ALL steps/prompts/HITL                            │
└───────────────────────────────────────────────────────────┬─────────┘
                                                             │
                                                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              STAGE 2: GENERATED EXPERIMENT (my_test/)               │
│                                                                       │
│  my_test/                      ┌──────────────────────────────────┐ │
│  ├── config/                   │ Independent Workspace            │ │
│  │   ├── config.yaml           │ - Fully flexible                │ │
│  │   │   steps:                │ - Researcher edits freely       │ │
│  │   │     - id: 1             │ - No connection to generator    │ │
│  │   │       enabled: true     │ - Self-contained                │ │
│  │   │     - id: 2             └──────────────────────────────────┘ │
│  │   │       enabled: true (← researcher can set to false)          │
│  │   │     - id: 3                                                  │
│  │   │       enabled: true                                          │
│  │   ├── prompts/              (← All copied from config set)       │
│  │   │   ├── 01_student.txt                                         │
│  │   │   ├── 02_course.txt                                          │
│  │   │   └── ...                                                     │
│  │   └── hitl/                 (← Copied from config set)           │
│  │       └── expanded_spec.txt                                      │
│  └── runs/                     (← Generated during execution)       │
│                                                                       │
│  Post-Generation Editing:                                           │
│  $ vim my_test/config/config.yaml  # Disable step 2                │
│  $ vim my_test/config/prompts/01_student.txt  # Modify prompt       │
│                                                                       │
│  Run Experiment:                                                     │
│  $ python scripts/run_experiment.py my_test                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Properties

1. **Complete Independence**: Generated experiment has no knowledge of origin
2. **Full Flexibility**: Researcher can modify any file post-generation
3. **Simple Generator**: No filtering, no complex logic
4. **Reproducibility**: Self-contained experiments (all files copied)
5. **Clear Separation**: Curated templates vs. flexible experiments

---

## 📊 Data Model

### 1. ConfigSet (New Entity)

Represents a curated scenario template in the generator.

```python
@dataclass
class ConfigSet:
    """
    A curated experiment scenario template.
    
    Located at: config_sets/{name}/
    """
    name: str                          # e.g., "default", "microservices"
    description: str                   # Human-readable description
    available_steps: List[StepMetadata]  # Catalog of steps in this set
    template_path: Path                # Path to experiment_template.yaml
    prompts_dir: Path                  # Path to prompts/
    hitl_dir: Path                     # Path to hitl/
    
    @classmethod
    def load(cls, name: str) -> 'ConfigSet':
        """Load config set from config_sets/{name}/"""
        pass
    
    def validate(self) -> List[str]:
        """
        Validate config set structure.
        
        Returns list of validation errors (empty if valid).
        
        Checks:
        - metadata.yaml exists and is valid
        - experiment_template.yaml exists and is valid
        - All referenced prompt files exist
        - available_steps match prompt files
        - HITL directory exists
        - Step IDs are unique
        """
        pass


@dataclass
class StepMetadata:
    """Metadata about a step in a config set."""
    id: int                  # Step ID
    name: str                # Human-readable name
    prompt_file: str         # Relative path: "prompts/01_student.txt"
    description: str         # What this step does
```

### 2. StepConfig (Updated)

Represents a step configuration in generated experiment's `config.yaml`.

```python
@dataclass
class StepConfig:
    """
    Step configuration in generated experiment.
    
    Appears in: {experiment}/config/config.yaml
    """
    id: int                  # Unique step identifier
    enabled: bool            # Whether to execute this step (default: True)
    name: str                # Human-readable step name
    prompt_file: str         # Path to prompt (relative to config/)
    
    def validate(self, config_dir: Path) -> List[str]:
        """
        Validate step configuration.
        
        Fail-fast checks:
        - prompt_file exists
        - prompt_file is not empty
        - prompt_file is readable
        """
        pass


@dataclass
class StepsCollection:
    """
    Collection of steps from config.yaml.
    
    Loaded from: {experiment}/config/config.yaml
    """
    steps: List[StepConfig]
    
    def get_enabled_steps(self) -> List[StepConfig]:
        """
        Get enabled steps in declaration order.
        
        Returns steps where enabled=True, preserving YAML order.
        """
        return [s for s in self.steps if s.enabled]
    
    def validate(self, config_dir: Path) -> List[str]:
        """
        Validate entire collection.
        
        Checks:
        - No duplicate step IDs
        - All prompt files exist
        - At least one step enabled
        """
        pass
```

### 3. ConfigSetLoader (New)

Service for discovering and loading config sets.

```python
class ConfigSetLoader:
    """
    Service for managing config sets in generator.
    
    Discovery mechanism: Distributed metadata (scan directories)
    """
    
    def __init__(self, config_sets_dir: Path):
        """
        Initialize loader.
        
        Args:
            config_sets_dir: Path to config_sets/ directory
        """
        self.config_sets_dir = config_sets_dir
    
    def list_available(self) -> List[str]:
        """
        List all available config set names.
        
        Scans config_sets/ directory, returns names of valid config sets.
        """
        pass
    
    def load(self, name: str) -> ConfigSet:
        """
        Load and validate config set.
        
        Args:
            name: Config set name (e.g., "default")
            
        Returns:
            Validated ConfigSet object
            
        Raises:
            ConfigSetNotFoundError: If config set doesn't exist
            ConfigSetValidationError: If config set is invalid
        """
        pass
    
    def get_details(self, name: str) -> Dict[str, Any]:
        """
        Get config set details without full load.
        
        Returns:
            {
                "name": "default",
                "description": "...",
                "steps_count": 6,
                "steps": [
                    {"id": 1, "name": "Student CRUD", ...},
                    ...
                ]
            }
        """
        pass
```

---

## 🔧 Implementation Phases

### Phase 0: Preparation (1 hour)

**Goal:** Set up foundation and create config set structure.

#### Tasks:

1. **Create config_sets/ directory structure** (15 min)
   ```bash
   mkdir -p config_sets/{default,minimal}/{prompts,hitl}
   ```

2. **Move existing config/ to config_sets/default/** (30 min)
   - Move `config/prompts/` → `config_sets/default/prompts/`
   - Move `config/hitl/` → `config_sets/default/hitl/`
   - Rename prompt files to numbered format: `01_student_crud.txt`, `02_course_crud.txt`, etc.
   - Create `config_sets/default/metadata.yaml`
   - Create `config_sets/default/experiment_template.yaml` (extract from current config/experiment.yaml)

3. **Create minimal config set** (15 min)
   - Create hello world scenario
   - Single step: "Generate hello world API"
   - Use for testing and validation

**Output:**
```
config_sets/
├── default/
│   ├── metadata.yaml
│   ├── experiment_template.yaml
│   ├── prompts/
│   │   ├── 01_student_crud.txt
│   │   ├── 02_course_crud.txt
│   │   ├── 03_teacher_crud.txt
│   │   ├── 04_authentication.txt
│   │   ├── 05_relationships.txt
│   │   └── 06_testing.txt
│   └── hitl/
│       └── expanded_spec.txt
└── minimal/
    ├── metadata.yaml
    ├── experiment_template.yaml
    ├── prompts/
    │   └── 01_hello_world.txt
    └── hitl/
        └── simple_spec.txt
```

---

### Phase 1: Data Model & Core Services (3 hours)

**Goal:** Implement config set loading and validation.

#### 1.1: Config Set Metadata Schema (30 min)

**File:** `config_sets/default/metadata.yaml`

```yaml
# Config Set Metadata
# This file defines a curated experiment scenario template

name: "default"
version: "1.0.0"
description: "Traditional 6-step CRUD application (Student/Course/Teacher)"

# Catalog of available steps in this config set
available_steps:
  - id: 1
    name: "Student CRUD"
    prompt_file: "prompts/01_student_crud.txt"
    description: "Generate Student entity with CRUD operations"
  
  - id: 2
    name: "Course CRUD"
    prompt_file: "prompts/02_course_crud.txt"
    description: "Generate Course entity with CRUD operations"
  
  - id: 3
    name: "Teacher CRUD"
    prompt_file: "prompts/03_teacher_crud.txt"
    description: "Generate Teacher entity with CRUD operations"
  
  - id: 4
    name: "Authentication"
    prompt_file: "prompts/04_authentication.txt"
    description: "Add user authentication and authorization"
  
  - id: 5
    name: "Relationships"
    prompt_file: "prompts/05_relationships.txt"
    description: "Implement relationships between entities"
  
  - id: 6
    name: "Testing"
    prompt_file: "prompts/06_testing.txt"
    description: "Add unit and integration tests"

# Scenario-specific defaults (copied to generated config.yaml)
defaults:
  timeout:
    per_step: 600      # 10 minutes per step
    total: 7200        # 2 hours total
  
  metrics:
    weights:
      functionality: 0.4
      code_quality: 0.3
      documentation: 0.2
      test_coverage: 0.1
```

**File:** `config_sets/default/experiment_template.yaml`

```yaml
# Experiment Template for 'default' Config Set
# This file is used as the base for generated config.yaml

# Steps configuration (all enabled by default)
steps:
  - id: 1
    enabled: true
    name: "Student CRUD"
    prompt_file: "prompts/01_student_crud.txt"
  
  - id: 2
    enabled: true
    name: "Course CRUD"
    prompt_file: "prompts/02_course_crud.txt"
  
  - id: 3
    enabled: true
    name: "Teacher CRUD"
    prompt_file: "prompts/03_teacher_crud.txt"
  
  - id: 4
    enabled: true
    name: "Authentication"
    prompt_file: "prompts/04_authentication.txt"
  
  - id: 5
    enabled: true
    name: "Relationships"
    prompt_file: "prompts/05_relationships.txt"
  
  - id: 6
    enabled: true
    name: "Testing"
    prompt_file: "prompts/06_testing.txt"

# Timeouts (can be overridden by researcher post-generation)
timeout:
  per_step: 600
  total: 7200

# Metrics configuration
metrics:
  weights:
    functionality: 0.4
    code_quality: 0.3
    documentation: 0.2
    test_coverage: 0.1

# Stopping rule
stopping:
  confidence_level: 0.95
  min_runs: 10
  max_runs: 100
```

#### 1.2: Implement ConfigSet Entity (45 min)

**File:** `src/config_sets/models.py` (new file)

```python
"""
Data models for Config Set Management.

A Config Set is a curated experiment scenario template containing:
- Metadata (name, description, available steps)
- Experiment template (default config.yaml structure)
- Prompts directory (prompt files for each step)
- HITL directory (human-in-the-loop files)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
import yaml


@dataclass
class StepMetadata:
    """Metadata about a step in a config set."""
    id: int
    name: str
    prompt_file: str
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepMetadata':
        """Load from metadata.yaml entry."""
        return cls(
            id=data['id'],
            name=data['name'],
            prompt_file=data['prompt_file'],
            description=data['description']
        )


@dataclass
class ConfigSet:
    """A curated experiment scenario template."""
    
    name: str
    description: str
    version: str
    available_steps: List[StepMetadata]
    defaults: Dict[str, Any]
    
    # Paths
    base_path: Path
    template_path: Path
    prompts_dir: Path
    hitl_dir: Path
    
    @classmethod
    def load(cls, config_set_dir: Path) -> 'ConfigSet':
        """
        Load config set from directory.
        
        Args:
            config_set_dir: Path to config set (e.g., config_sets/default/)
            
        Returns:
            Loaded ConfigSet object
            
        Raises:
            FileNotFoundError: If metadata.yaml missing
            ValueError: If metadata is invalid
        """
        metadata_path = config_set_dir / "metadata.yaml"
        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.yaml not found in {config_set_dir}")
        
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        
        # Load available steps
        steps = [
            StepMetadata.from_dict(step_data)
            for step_data in metadata.get('available_steps', [])
        ]
        
        return cls(
            name=metadata['name'],
            description=metadata['description'],
            version=metadata.get('version', '1.0.0'),
            available_steps=steps,
            defaults=metadata.get('defaults', {}),
            base_path=config_set_dir,
            template_path=config_set_dir / "experiment_template.yaml",
            prompts_dir=config_set_dir / "prompts",
            hitl_dir=config_set_dir / "hitl"
        )
    
    def validate(self) -> List[str]:
        """
        Validate config set structure.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check template exists
        if not self.template_path.exists():
            errors.append(f"experiment_template.yaml not found at {self.template_path}")
        
        # Check directories exist
        if not self.prompts_dir.exists():
            errors.append(f"prompts/ directory not found at {self.prompts_dir}")
        if not self.hitl_dir.exists():
            errors.append(f"hitl/ directory not found at {self.hitl_dir}")
        
        # Check prompt files exist
        for step in self.available_steps:
            prompt_path = self.base_path / step.prompt_file
            if not prompt_path.exists():
                errors.append(f"Prompt file not found: {step.prompt_file}")
            elif prompt_path.stat().st_size == 0:
                errors.append(f"Prompt file is empty: {step.prompt_file}")
        
        # Check for duplicate step IDs
        step_ids = [s.id for s in self.available_steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Duplicate step IDs found in available_steps")
        
        return errors
    
    def get_step_count(self) -> int:
        """Get total number of steps in this config set."""
        return len(self.available_steps)
```

#### 1.3: Implement ConfigSetLoader Service (45 min)

**File:** `src/config_sets/loader.py` (new file)

```python
"""
Service for discovering and loading config sets.

Discovery mechanism: Distributed metadata (scan directories)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import ConfigSet
from .exceptions import ConfigSetNotFoundError, ConfigSetValidationError


class ConfigSetLoader:
    """Service for managing config sets in generator."""
    
    def __init__(self, config_sets_dir: Path):
        """
        Initialize loader.
        
        Args:
            config_sets_dir: Path to config_sets/ directory
        """
        self.config_sets_dir = Path(config_sets_dir)
        if not self.config_sets_dir.exists():
            raise FileNotFoundError(f"Config sets directory not found: {config_sets_dir}")
    
    def list_available(self) -> List[str]:
        """
        List all available config set names.
        
        Scans config_sets/ directory for subdirectories containing metadata.yaml
        
        Returns:
            List of config set names (e.g., ["default", "minimal"])
        """
        config_sets = []
        
        for item in self.config_sets_dir.iterdir():
            if item.is_dir():
                metadata_path = item / "metadata.yaml"
                if metadata_path.exists():
                    config_sets.append(item.name)
        
        return sorted(config_sets)
    
    def load(self, name: str) -> ConfigSet:
        """
        Load and validate config set.
        
        Args:
            name: Config set name (e.g., "default")
            
        Returns:
            Validated ConfigSet object
            
        Raises:
            ConfigSetNotFoundError: If config set doesn't exist
            ConfigSetValidationError: If config set is invalid (fail-fast)
        """
        config_set_dir = self.config_sets_dir / name
        
        # Check existence
        if not config_set_dir.exists():
            available = self.list_available()
            raise ConfigSetNotFoundError(
                f"Config set '{name}' not found. Available: {', '.join(available)}"
            )
        
        # Load config set
        try:
            config_set = ConfigSet.load(config_set_dir)
        except Exception as e:
            raise ConfigSetValidationError(f"Failed to load config set '{name}': {e}")
        
        # Validate (fail-fast)
        errors = config_set.validate()
        if errors:
            error_msg = f"Config set '{name}' validation failed:\n"
            error_msg += "\n".join(f"  - {err}" for err in errors)
            raise ConfigSetValidationError(error_msg)
        
        return config_set
    
    def get_details(self, name: str) -> Dict[str, Any]:
        """
        Get config set details without full validation.
        
        Args:
            name: Config set name
            
        Returns:
            Dictionary with config set information
            
        Example:
            {
                "name": "default",
                "description": "6-step CRUD application",
                "steps_count": 6,
                "steps": [
                    {"id": 1, "name": "Student CRUD", ...},
                    ...
                ]
            }
        """
        config_set = self.load(name)  # Will validate
        
        return {
            "name": config_set.name,
            "description": config_set.description,
            "version": config_set.version,
            "steps_count": config_set.get_step_count(),
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "prompt_file": step.prompt_file
                }
                for step in config_set.available_steps
            ]
        }
```

#### 1.4: Implement Exception Classes (15 min)

**File:** `src/config_sets/exceptions.py` (new file)

```python
"""Custom exceptions for config set management."""


class ConfigSetError(Exception):
    """Base exception for config set errors."""
    pass


class ConfigSetNotFoundError(ConfigSetError):
    """Raised when config set doesn't exist."""
    pass


class ConfigSetValidationError(ConfigSetError):
    """Raised when config set validation fails."""
    pass
```

#### 1.5: Update StepConfig for Generated Experiments (45 min)

**File:** `src/config/step_config.py` (update existing)

```python
"""
Step configuration for generated experiments.

This module handles loading and validating steps from config.yaml
in generated experiment directories.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
import yaml


@dataclass
class StepConfig:
    """
    Step configuration in generated experiment.
    
    Loaded from: {experiment}/config/config.yaml
    """
    id: int
    enabled: bool
    name: str
    prompt_file: str  # Relative to config/ directory
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepConfig':
        """Load from config.yaml step entry."""
        return cls(
            id=data['id'],
            enabled=data.get('enabled', True),  # Default: True
            name=data['name'],
            prompt_file=data['prompt_file']
        )
    
    def validate(self, config_dir: Path) -> List[str]:
        """
        Validate step configuration (fail-fast).
        
        Args:
            config_dir: Path to experiment's config/ directory
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check prompt file exists
        prompt_path = config_dir / self.prompt_file
        if not prompt_path.exists():
            errors.append(
                f"Step {self.id} ({self.name}): "
                f"Prompt file not found: {self.prompt_file}"
            )
        elif prompt_path.stat().st_size == 0:
            errors.append(
                f"Step {self.id} ({self.name}): "
                f"Prompt file is empty: {self.prompt_file}"
            )
        elif not prompt_path.is_file():
            errors.append(
                f"Step {self.id} ({self.name}): "
                f"Prompt file is not a regular file: {self.prompt_file}"
            )
        
        return errors


@dataclass
class StepsCollection:
    """
    Collection of steps from generated experiment's config.yaml.
    """
    steps: List[StepConfig]
    
    @classmethod
    def load(cls, config_yaml_path: Path) -> 'StepsCollection':
        """
        Load steps from config.yaml.
        
        Args:
            config_yaml_path: Path to config.yaml
            
        Returns:
            StepsCollection with all steps
        """
        with open(config_yaml_path) as f:
            config = yaml.safe_load(f)
        
        steps = [
            StepConfig.from_dict(step_data)
            for step_data in config.get('steps', [])
        ]
        
        return cls(steps=steps)
    
    def get_enabled_steps(self) -> List[StepConfig]:
        """
        Get enabled steps in declaration order.
        
        Returns steps where enabled=True, preserving YAML order.
        """
        return [s for s in self.steps if s.enabled]
    
    def validate(self, config_dir: Path) -> List[str]:
        """
        Validate entire collection (fail-fast).
        
        Args:
            config_dir: Path to experiment's config/ directory
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check for duplicate step IDs
        step_ids = [s.id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            duplicates = [sid for sid in step_ids if step_ids.count(sid) > 1]
            errors.append(f"Duplicate step IDs found: {set(duplicates)}")
        
        # Check at least one step enabled
        enabled_steps = self.get_enabled_steps()
        if not enabled_steps:
            errors.append("No enabled steps found. At least one step must be enabled.")
        
        # Validate each step
        for step in self.steps:
            errors.extend(step.validate(config_dir))
        
        return errors


def get_enabled_steps(config_yaml_path: Path) -> List[StepConfig]:
    """
    Helper function to load enabled steps from config.yaml.
    
    This is the main entry point for the runner to discover steps.
    
    Args:
        config_yaml_path: Path to experiment's config.yaml
        
    Returns:
        List of enabled steps in declaration order
        
    Raises:
        ValueError: If validation fails (fail-fast)
    """
    config_dir = config_yaml_path.parent
    
    # Load steps collection
    collection = StepsCollection.load(config_yaml_path)
    
    # Validate (fail-fast)
    errors = collection.validate(config_dir)
    if errors:
        error_msg = "Step configuration validation failed:\n"
        error_msg += "\n".join(f"  - {err}" for err in errors)
        raise ValueError(error_msg)
    
    # Return enabled steps in declaration order
    return collection.get_enabled_steps()
```

---

### Phase 2: Generator Integration (4 hours)

**Goal:** Update experiment generator to use config sets.

#### 2.1: Update CLI Arguments (30 min)

**File:** `scripts/new_experiment.py` (update)

```python
"""
Generate new experiment from config set.

Usage:
    python scripts/new_experiment.py \
        --name my_test \
        --config-set default \
        --frameworks chatdev metagpt \
        --model gpt-4o-mini \
        --max-runs 50
"""

import argparse
from pathlib import Path
from src.config_sets.loader import ConfigSetLoader
from src.generator.standalone_generator import StandaloneGenerator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate new experiment from config set"
    )
    
    # Required arguments
    parser.add_argument(
        "--name",
        required=True,
        help="Experiment name (directory will be created)"
    )
    
    parser.add_argument(
        "--config-set",
        required=True,
        help="Config set name (e.g., 'default', 'minimal')"
    )
    
    parser.add_argument(
        "--frameworks",
        nargs="+",
        required=True,
        help="Frameworks to test (e.g., chatdev metagpt)"
    )
    
    parser.add_argument(
        "--model",
        required=True,
        help="LLM model (e.g., gpt-4o-mini, o1-mini)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--max-runs",
        type=int,
        default=50,
        help="Maximum number of runs (default: 50)"
    )
    
    parser.add_argument(
        "--min-runs",
        type=int,
        default=10,
        help="Minimum number of runs (default: 10)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for LLM (default: 0.7)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--list-config-sets",
        action="store_true",
        help="List available config sets and exit"
    )
    
    return parser.parse_args()


def list_config_sets():
    """List all available config sets with details."""
    loader = ConfigSetLoader(Path("config_sets"))
    
    print("\n📦 Available Config Sets:\n")
    
    for name in loader.list_available():
        try:
            details = loader.get_details(name)
            print(f"  • {name}")
            print(f"    {details['description']}")
            print(f"    Steps: {details['steps_count']}")
            
            for step in details['steps']:
                print(f"      {step['id']}. {step['name']}")
            print()
            
        except Exception as e:
            print(f"  • {name} [ERROR: {e}]\n")


def main():
    args = parse_args()
    
    # Handle --list-config-sets
    if args.list_config_sets:
        list_config_sets()
        return
    
    # Initialize loader
    loader = ConfigSetLoader(Path("config_sets"))
    
    # Load config set (validates automatically)
    print(f"📦 Loading config set: {args.config_set}")
    try:
        config_set = loader.load(args.config_set)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nUse --list-config-sets to see available config sets")
        exit(1)
    
    print(f"   {config_set.description}")
    print(f"   Steps: {config_set.get_step_count()}")
    
    # Create output directory
    output_path = Path(args.name)
    if output_path.exists():
        print(f"❌ Error: Directory '{args.name}' already exists")
        exit(1)
    
    # Create generator
    generator = StandaloneGenerator(
        output_dir=output_path,
        config_set=config_set,
        frameworks=args.frameworks,
        model=args.model,
        max_runs=args.max_runs,
        min_runs=args.min_runs,
        temperature=args.temperature,
        seed=args.seed
    )
    
    # Generate experiment
    print(f"\n🚀 Generating experiment: {args.name}")
    generator.generate()
    
    print(f"\n✅ Experiment generated successfully!")
    print(f"\n📝 Next steps:")
    print(f"   1. Review config: vim {args.name}/config/config.yaml")
    print(f"   2. Customize prompts: vim {args.name}/config/prompts/*.txt")
    print(f"   3. Run experiment: python scripts/run_experiment.py {args.name}")


if __name__ == "__main__":
    main()
```

#### 2.2: Update StandaloneGenerator (2 hours)

**File:** `src/generator/standalone_generator.py` (update)

```python
"""
Standalone experiment generator.

Generates self-contained experiment directories from config sets.
Generator ALWAYS copies ALL steps/prompts/HITL from config set.
"""

import shutil
from pathlib import Path
from typing import List, Optional
import yaml
from src.config_sets.models import ConfigSet


class StandaloneGenerator:
    """
    Generator for creating standalone experiments.
    
    Key behavior: ALWAYS copies ALL steps/prompts/HITL from config set.
    Researcher customizes by editing config.yaml post-generation.
    """
    
    def __init__(
        self,
        output_dir: Path,
        config_set: ConfigSet,
        frameworks: List[str],
        model: str,
        max_runs: int = 50,
        min_runs: int = 10,
        temperature: float = 0.7,
        seed: Optional[int] = None
    ):
        """
        Initialize generator.
        
        Args:
            output_dir: Path where experiment will be created
            config_set: Validated ConfigSet object
            frameworks: List of frameworks to test
            model: LLM model name
            max_runs: Maximum number of runs
            min_runs: Minimum number of runs
            temperature: LLM temperature
            seed: Random seed for reproducibility
        """
        self.output_dir = Path(output_dir)
        self.config_set = config_set
        self.frameworks = frameworks
        self.model = model
        self.max_runs = max_runs
        self.min_runs = min_runs
        self.temperature = temperature
        self.seed = seed
    
    def generate(self):
        """
        Generate complete experiment structure.
        
        Process:
        1. Create directory structure
        2. Copy ALL prompts from config set
        3. Copy ALL HITL files from config set
        4. Generate config.yaml (all steps enabled: true)
        5. Create empty runs/ directory
        """
        print(f"   Creating directory structure...")
        self._create_structure()
        
        print(f"   Copying prompts...")
        self._copy_prompts()
        
        print(f"   Copying HITL files...")
        self._copy_hitl()
        
        print(f"   Generating config.yaml...")
        self._generate_config()
        
        print(f"   Creating runs directory...")
        self._create_runs_dir()
    
    def _create_structure(self):
        """Create experiment directory structure."""
        (self.output_dir / "config").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "config" / "prompts").mkdir(exist_ok=True)
        (self.output_dir / "config" / "hitl").mkdir(exist_ok=True)
    
    def _copy_prompts(self):
        """Copy ALL prompt files from config set."""
        # Copy all files from prompts directory
        for prompt_file in self.config_set.prompts_dir.iterdir():
            if prompt_file.is_file():
                dest = self.output_dir / "config" / "prompts" / prompt_file.name
                shutil.copy2(prompt_file, dest)
    
    def _copy_hitl(self):
        """Copy ALL HITL files from config set."""
        # Copy all files from hitl directory
        for hitl_file in self.config_set.hitl_dir.iterdir():
            if hitl_file.is_file():
                dest = self.output_dir / "config" / "hitl" / hitl_file.name
                shutil.copy2(hitl_file, dest)
    
    def _generate_config(self):
        """
        Generate config.yaml with ALL steps enabled.
        
        Strategy:
        1. Load experiment_template.yaml from config set
        2. Add user-specified settings (frameworks, model, runs)
        3. Keep all steps with enabled: true
        4. Write to {output_dir}/config/config.yaml
        """
        # Load template
        with open(self.config_set.template_path) as f:
            config = yaml.safe_load(f)
        
        # Override with user settings
        config['frameworks'] = self.frameworks
        config['model'] = self.model
        config['max_runs'] = self.max_runs
        config['min_runs'] = self.min_runs
        config['temperature'] = self.temperature
        
        if self.seed is not None:
            config['seed'] = self.seed
        
        # Ensure all steps are enabled: true (should already be in template)
        for step in config.get('steps', []):
            step['enabled'] = True
        
        # Write config.yaml
        config_path = self.output_dir / "config" / "config.yaml"
        with open(config_path, 'w') as f:
            # Add header comment
            f.write(self._get_config_header())
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def _get_config_header(self) -> str:
        """Generate informative header for config.yaml."""
        return f"""# Experiment Configuration
# Generated from config set: {self.config_set.name}
# 
# This is a self-contained experiment. You can freely modify this file:
# - Disable steps by setting 'enabled: false'
# - Reorder steps by moving entries (execution follows declaration order)
# - Modify prompt_file paths to point to custom prompts
# - Adjust timeouts, metrics, and other settings
#
# To run: python scripts/run_experiment.py {self.output_dir.name}

"""
    
    def _create_runs_dir(self):
        """Create empty runs/ directory for experiment results."""
        (self.output_dir / "runs").mkdir(exist_ok=True)
        
        # Create .gitkeep to preserve directory in git
        (self.output_dir / "runs" / ".gitkeep").touch()
```

#### 2.3: Add Config Set Listing Command (30 min)

**File:** `scripts/list_config_sets.py` (new file)

```python
"""
List available config sets with detailed information.

Usage:
    python scripts/list_config_sets.py
    python scripts/list_config_sets.py --verbose
"""

import argparse
from pathlib import Path
from src.config_sets.loader import ConfigSetLoader


def main():
    parser = argparse.ArgumentParser(description="List available config sets")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information including all steps"
    )
    args = parser.parse_args()
    
    loader = ConfigSetLoader(Path("config_sets"))
    
    print("\n📦 Available Config Sets:\n")
    
    for name in loader.list_available():
        try:
            details = loader.get_details(name)
            
            # Basic info
            print(f"  🎯 {name}")
            print(f"     {details['description']}")
            print(f"     Version: {details['version']}")
            print(f"     Steps: {details['steps_count']}")
            
            # Detailed step list if verbose
            if args.verbose:
                print(f"     Available steps:")
                for step in details['steps']:
                    print(f"       {step['id']}. {step['name']}")
                    print(f"          {step['description']}")
                    print(f"          File: {step['prompt_file']}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ {name} [ERROR: {e}]\n")


if __name__ == "__main__":
    main()
```

#### 2.4: Update Generator Tests (1 hour)

**File:** `tests/test_generator_with_config_sets.py` (new file)

Test scenarios:
1. Generate experiment from `default` config set
2. Generate experiment from `minimal` config set
3. Verify all prompts copied
4. Verify all HITL files copied
5. Verify config.yaml structure
6. Verify all steps enabled by default
7. Test with invalid config set name
8. Test with corrupted config set

---

### Phase 3: Runner Integration (3 hours)

**Goal:** Update runner to use declaration-order execution and fail-fast validation.

#### 3.1: Update Runner to Use get_enabled_steps() (1.5 hours)

**File:** `src/runner/experiment_runner.py` (update)

```python
"""
Experiment runner with configurable steps support.

Key behaviors:
- Execution order: By declaration order in config.yaml
- Validation: Fail-fast on any error
- Metrics: Preserve original step IDs
"""

from pathlib import Path
from typing import List, Dict, Any
from src.config.step_config import get_enabled_steps, StepConfig


class ExperimentRunner:
    """Runner for executing experiments with configurable steps."""
    
    def __init__(self, experiment_dir: Path):
        """
        Initialize runner.
        
        Args:
            experiment_dir: Path to experiment directory
        """
        self.experiment_dir = Path(experiment_dir)
        self.config_path = self.experiment_dir / "config" / "config.yaml"
        
        # Validate experiment structure
        if not self.config_path.exists():
            raise FileNotFoundError(f"config.yaml not found: {self.config_path}")
    
    def run(self):
        """
        Execute experiment with all enabled steps.
        
        Process:
        1. Load enabled steps (fail-fast validation)
        2. For each run iteration:
           a. Execute steps in declaration order
           b. Record metrics with original step IDs
           c. Check stopping criteria
        """
        # Load enabled steps (validates, fail-fast)
        print("📋 Loading experiment configuration...")
        try:
            enabled_steps = get_enabled_steps(self.config_path)
        except ValueError as e:
            print(f"❌ Configuration Error:\n{e}")
            exit(1)
        
        print(f"   ✓ Found {len(enabled_steps)} enabled steps")
        for i, step in enumerate(enabled_steps, 1):
            print(f"      {i}. Step {step.id}: {step.name}")
        
        # Execute runs
        run_number = 1
        while not self._should_stop():
            print(f"\n🚀 Run {run_number}/{self.max_runs}")
            
            try:
                self._execute_run(run_number, enabled_steps)
            except Exception as e:
                print(f"❌ Run {run_number} failed: {e}")
                exit(1)
            
            run_number += 1
        
        print(f"\n✅ Experiment completed: {run_number - 1} runs")
    
    def _execute_run(self, run_number: int, steps: List[StepConfig]):
        """
        Execute single run with all steps.
        
        Args:
            run_number: Current run number
            steps: List of enabled steps in declaration order
        """
        for step_index, step in enumerate(steps, 1):
            print(f"   Step {step.id}: {step.name}...", end=" ", flush=True)
            
            try:
                # Load prompt
                prompt = self._load_prompt(step.prompt_file)
                
                # Execute step
                result = self._execute_step(step, prompt)
                
                # Record metrics (preserve original step ID)
                self._record_metrics(
                    run_number=run_number,
                    step_id=step.id,  # Original ID, not sequential
                    step_name=step.name,
                    step_index=step_index,  # For ordering in reports
                    result=result
                )
                
                print(f"✓ [{result['duration']:.1f}s]")
                
            except Exception as e:
                print(f"✗ FAILED")
                # Fail-fast: stop entire run on first error
                raise RuntimeError(
                    f"Step {step.id} ({step.name}) failed: {e}"
                )
    
    def _load_prompt(self, prompt_file: str) -> str:
        """
        Load prompt file content.
        
        Args:
            prompt_file: Relative path from config/
            
        Returns:
            Prompt text
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist (fail-fast)
        """
        prompt_path = self.experiment_dir / "config" / prompt_file
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_path) as f:
            return f.read()
    
    def _record_metrics(
        self,
        run_number: int,
        step_id: int,
        step_name: str,
        step_index: int,
        result: Dict[str, Any]
    ):
        """
        Record metrics for step execution.
        
        Metrics include:
        - step_id: Original ID from config (may be non-sequential)
        - step_index: Execution order (1, 2, 3, ...)
        - step_name: Human-readable name
        - duration: Execution time
        - Other metrics...
        """
        metrics = {
            "run_number": run_number,
            "step_id": step_id,  # Preserve original ID
            "step_index": step_index,
            "step_name": step_name,
            "duration": result["duration"],
            # ... other metrics
        }
        
        # Save to database/file
        self._save_metrics(metrics)
```

#### 3.2: Update Metrics Collection (1 hour)

**File:** `src/metrics/collector.py` (update)

Ensure metrics preserve original step IDs:
- `step_id`: Original ID from config.yaml
- `step_index`: Execution order (for sequential reports)
- Both available for analysis

#### 3.3: Update Runner Tests (30 min)

**File:** `tests/test_runner_declaration_order.py` (new file)

Test scenarios:
1. Execute steps in declaration order (not sorted by ID)
2. Verify metrics preserve original step IDs
3. Test fail-fast on missing prompt file
4. Test fail-fast on invalid step config
5. Test with non-sequential step IDs (1, 5, 99)

---

### Phase 4: Documentation & Examples (2 hours)

**Goal:** Update documentation and create examples.

#### 4.1: Update Quickstart Guide (45 min)

**File:** `docs/configurable_steps/quickstart.md` (update)

Update with:
- Two-stage architecture explanation
- Config set selection
- Post-generation customization workflow
- Examples with `default` and `minimal` config sets

#### 4.2: Create Config Set Creation Guide (45 min)

**File:** `docs/config_sets/CREATING_CONFIG_SETS.md` (new file)

Guide for creating new config sets:
- Directory structure
- metadata.yaml schema
- experiment_template.yaml format
- Prompt file naming conventions
- Validation requirements
- Examples

#### 4.3: Update Main README (30 min)

**File:** `README.md` (update)

Add section on config sets and quickstart with new syntax:
```bash
python scripts/new_experiment.py \
    --name my_test \
    --config-set default \
    --frameworks chatdev metagpt \
    --model gpt-4o-mini
```

---

### Phase 5: Testing & Validation (2-3 hours)

**Goal:** Comprehensive testing of integrated system.

#### 5.1: Unit Tests (1 hour)

Test files to create/update:
- `tests/test_config_set_loader.py`
- `tests/test_config_set_validation.py`
- `tests/test_step_config.py`
- `tests/test_generator_config_sets.py`
- `tests/test_runner_declaration_order.py`

#### 5.2: Integration Tests (1 hour)

**File:** `tests/integration/test_end_to_end.py` (new file)

Test complete workflow:
1. List available config sets
2. Generate experiment from `default` config set
3. Verify all files copied
4. Modify config.yaml (disable step, reorder steps)
5. Run experiment
6. Verify metrics correctness

#### 5.3: Manual Testing (1 hour)

Test scenarios:
1. Generate from `default` → customize → run
2. Generate from `minimal` → run (simplest case)
3. Test error cases (invalid config set, missing prompt, etc.)
4. Verify fail-fast behavior
5. Verify declaration-order execution

---

## 🧪 Testing Strategy

### Test Coverage Goals

| Component | Unit Tests | Integration Tests | Manual Tests |
|-----------|------------|-------------------|--------------|
| ConfigSet loading | ✅ | ✅ | ✅ |
| ConfigSet validation | ✅ | ✅ | ✅ |
| Generator (copy all) | ✅ | ✅ | ✅ |
| Runner (declaration order) | ✅ | ✅ | ✅ |
| Fail-fast validation | ✅ | ✅ | ✅ |
| Metrics (original IDs) | ✅ | ✅ | ✅ |

### Critical Test Cases

1. **Config Set Discovery**
   - List available config sets
   - Load valid config set
   - Reject invalid config set (missing files, bad metadata)

2. **Generator Behavior**
   - Always copy ALL prompts
   - Always copy ALL HITL files
   - Generate config.yaml with all steps enabled
   - Verify self-contained experiment

3. **Runner Execution**
   - Execute in declaration order (not sorted by ID)
   - Fail-fast on missing prompt
   - Fail-fast on duplicate step IDs
   - Preserve original step IDs in metrics

4. **Post-Generation Customization**
   - Researcher disables step → not executed
   - Researcher reorders steps → new execution order
   - Researcher modifies prompt → new prompt used

---

## 📦 Migration & Rollout

### Migration from Current System

**Current state:**
- Single `config/` directory with hardcoded prompts/HITL
- `scripts/new_experiment.py` creates experiments

**Migration steps:**

1. **Create config_sets/ structure** (Phase 0)
   - Move existing config/ → config_sets/default/

2. **Update generator** (Phase 2)
   - Replace hardcoded paths with ConfigSetLoader

3. **Update runner** (Phase 3)
   - Use get_enabled_steps() instead of hardcoded list

4. **No backwards compatibility needed**
   - Clean break, no legacy experiments to support
   - All new experiments use config sets

### Rollout Strategy

**V1 Scope:**
- Config Sets: `default` and `minimal`
- All features integrated
- Big bang implementation (no phased rollout)

**Future Enhancements (V2+):**
- Additional config sets (microservices, ml_pipeline)
- External config set support (--config-set-path)
- Config set cloning tool (scripts/clone_config_set.py)
- Step dependencies validation

---

## 📋 Implementation Checklist

### Phase 0: Preparation ✓
- [ ] Create config_sets/ directory structure
- [ ] Move existing config/ to config_sets/default/
- [ ] Rename prompts to numbered format (01_*.txt)
- [ ] Create config_sets/default/metadata.yaml
- [ ] Create config_sets/default/experiment_template.yaml
- [ ] Create config_sets/minimal/ (hello world)

### Phase 1: Data Model ✓
- [ ] Implement ConfigSet entity (src/config_sets/models.py)
- [ ] Implement ConfigSetLoader (src/config_sets/loader.py)
- [ ] Implement exception classes (src/config_sets/exceptions.py)
- [ ] Update StepConfig for generated experiments
- [ ] Implement get_enabled_steps() helper
- [ ] Add unit tests for all entities

### Phase 2: Generator ✓
- [ ] Update new_experiment.py CLI (--config-set)
- [ ] Update StandaloneGenerator (always copy all)
- [ ] Add config set listing (scripts/list_config_sets.py)
- [ ] Add config.yaml header generation
- [ ] Add generator tests

### Phase 3: Runner ✓
- [ ] Update ExperimentRunner (use get_enabled_steps)
- [ ] Implement declaration-order execution
- [ ] Implement fail-fast validation
- [ ] Update metrics collection (preserve step IDs)
- [ ] Add runner tests

### Phase 4: Documentation ✓
- [ ] Update quickstart guide
- [ ] Create config set creation guide
- [ ] Update main README
- [ ] Add examples

### Phase 5: Testing ✓
- [ ] Unit tests (all components)
- [ ] Integration tests (end-to-end)
- [ ] Manual testing (scenarios)
- [ ] Validation tests (fail-fast)

---

## 🎯 Success Criteria

### Functional Requirements

✅ **FR-1: Config Set Management**
- [ ] Can list available config sets
- [ ] Can load config set with validation
- [ ] Validation fails on invalid structure

✅ **FR-2: Generator Integration**
- [ ] Generator accepts --config-set argument
- [ ] Generator ALWAYS copies ALL steps/prompts/HITL
- [ ] Generated config.yaml has all steps enabled: true

✅ **FR-3: Post-Generation Flexibility**
- [ ] Researcher can disable steps (enabled: false)
- [ ] Researcher can reorder steps (declaration order)
- [ ] Researcher can modify prompts

✅ **FR-4: Runner Execution**
- [ ] Executes steps in declaration order
- [ ] Skips disabled steps
- [ ] Fails fast on validation errors
- [ ] Preserves original step IDs in metrics

✅ **FR-5: Complete Independence**
- [ ] Generated experiment has all files (self-contained)
- [ ] No references to config sets
- [ ] Can be moved/archived without breaking

### Non-Functional Requirements

✅ **NFR-1: Usability**
- Clear error messages on validation failures
- Helpful CLI with --list-config-sets
- Informative config.yaml header

✅ **NFR-2: Reliability**
- Fail-fast validation (no silent failures)
- Strict config set validation
- No wasted runs

✅ **NFR-3: Maintainability**
- Clean separation of concerns
- Easy to add new config sets
- Well-documented APIs

---

## 📚 References

### Design Documents

- [Feature Spec](./feature-spec.md) - Original requirements
- [Research](./research.md) - Phase 0 unknowns resolution
- [Data Model](./data-model.md) - Entity definitions
- [API Contracts](./contracts/api-contracts.md) - API specifications
- [Config Set Management](./config-set-management.md) - Original config set design
- [Clarification Q&A](./clarification-questions-round2-ANSWERS.md) - All design decisions

### Key Decisions

- **Two-Stage Architecture**: Generator (templates) → Experiment (flexible)
- **No --steps Flag**: Always copy all, customize post-generation
- **Declaration Order**: YAML order = execution order
- **Fail-Fast**: Validation errors stop execution immediately
- **Full Amnesia**: Generated experiments are completely independent

---

## 📞 Contact & Support

For questions or issues during implementation:
- Review clarification answers: [clarification-questions-round2-ANSWERS.md](./clarification-questions-round2-ANSWERS.md)
- Check design documents in `docs/configurable_steps/`
- Refer to Phase 0 research: [research.md](./research.md)

---

**Last Updated:** 2025-10-21  
**Status:** READY FOR IMPLEMENTATION  
**Estimated Effort:** 12-16 hours  
**Priority:** HIGH
