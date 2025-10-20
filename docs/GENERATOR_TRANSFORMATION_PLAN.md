# Generator Transformation Implementation Plan

**Date:** October 20, 2025  
**Goal:** Transform genai-devbench into a pure experiment generator that creates fully standalone, self-contained experiment projects.

---

## Overview

Transform the current experiment execution framework into a **pure generator** that produces completely independent experiment projects. Each generated experiment will be a standalone git repository with no references to the parent generator.

### Key Principles
- ✅ Full independence - no parent references
- ✅ Minimal artifacts - only what's needed
- ✅ Self-contained execution - `./setup.sh && ./run.sh`
- ✅ Framework-selective - copy only enabled frameworks
- ✅ Clean slate - no backward compatibility concerns

---

## Phase 1: Generator Core Infrastructure

### Task 1.1: Create `generator/artifact_collector.py`
**Purpose:** Determine which files need to be copied based on experiment configuration.

**Implementation Details:**
```python
class ArtifactCollector:
    """Collects all artifacts needed for a standalone experiment."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled_frameworks = self._get_enabled_frameworks()
        self.enabled_metrics = self._get_enabled_metrics()
    
    def collect_source_files(self) -> Dict[str, List[Path]]:
        """
        Collect source files needed for experiment.
        
        Returns:
            {
                'adapters': [baes_adapter.py, chatdev_adapter.py, ...],
                'analysis': [all analysis files],
                'orchestrator': [runner.py, config_loader.py, ...],
                'utils': [logger.py, api_client.py, ...]
            }
        """
        
    def collect_config_files(self) -> List[Path]:
        """
        Collect configuration files.
        
        Returns:
            - config/prompts/<framework>/ for enabled frameworks
            - config/hitl/ files
        """
        
    def collect_dependencies(self) -> Set[str]:
        """
        Collect Python dependencies.
        
        Base dependencies (always):
            - pyyaml
            - requests
            - python-dotenv
            - openai
            
        Framework-specific:
            - Add based on enabled frameworks
            
        Metrics-specific:
            - Add based on enabled metrics
        """
```

**Specific Logic:**
- Parse `config['frameworks']` to find `enabled=True` frameworks
- For each enabled framework, include:
  - `src/adapters/{framework}_adapter.py`
  - `config/prompts/{framework}/` directory
- Parse `config['metrics']['enabled']` list
- Always include core files:
  - `src/orchestrator/runner.py`
  - `src/orchestrator/config_loader.py`
  - `src/orchestrator/metrics_collector.py`
  - `src/utils/logger.py`
  - `src/utils/api_client.py`
  - `src/utils/cost_calculator.py`
- Include analysis files:
  - `src/analysis/report_generator.py`
  - `src/analysis/stopping_rule.py`
  - `src/analysis/visualizations.py`

**Files to Create:**
- `generator/artifact_collector.py`

**Dependencies:**
- None (first component)

---

### Task 1.2: Create `generator/import_rewriter.py`
**Purpose:** Rewrite Python imports to work in standalone project structure.

**Implementation Details:**
```python
class ImportRewriter:
    """Rewrites imports in Python files for standalone operation."""
    
    def rewrite_file(self, source_path: Path, dest_path: Path) -> None:
        """
        Read source file, rewrite imports, write to destination.
        
        Transformations:
        1. No changes needed for most imports (already relative to src/)
        2. Remove any references to parent project paths
        3. Update __main__ entry points if needed
        """
        
    def _rewrite_imports(self, content: str) -> str:
        """
        Rewrite import statements.
        
        Generally imports like:
            from src.utils.logger import get_logger
        
        Will work as-is in standalone project since structure preserved.
        
        Only need to handle special cases:
        - Absolute paths to parent directories
        - References to 'experiments/' or 'runners/'
        """
        
    def _remove_parent_references(self, content: str) -> str:
        """
        Remove any hardcoded references to parent project.
        
        Examples:
        - Path('../experiments/') → Path('./runs/')
        - References to .experiments.json
        - References to parent registry
        """
```

**Specific Logic:**
- Parse Python AST to find import statements
- Most imports will work as-is (structure preserved)
- Main changes:
  - Remove registry references (experiment_registry.py usage)
  - Update ExperimentPaths to work from experiment root
  - Replace parent-relative paths with experiment-relative paths

**Files to Create:**
- `generator/import_rewriter.py`

**Dependencies:**
- Standard library: `ast`, `re`

---

### Task 1.3: Create `generator/script_generator.py`
**Purpose:** Generate standalone execution scripts for experiments.

**Implementation Details:**
```python
class ScriptGenerator:
    """Generates execution scripts for standalone experiments."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.experiment_name = config.get('experiment_name', 'experiment')
        self.enabled_frameworks = self._get_enabled_frameworks()
        
    def generate_setup_script(self) -> str:
        """
        Generate setup.sh script.
        
        Content:
        - Create Python virtual environment
        - Install dependencies from requirements.txt
        - Copy .env.example to .env (if not exists)
        - Initialize framework repositories (git clone)
        - Print next steps
        """
        
    def generate_run_script(self) -> str:
        """
        Generate run.sh script.
        
        Content:
        - Activate virtual environment
        - Load .env variables
        - Execute main orchestrator
        - Print completion message
        """
        
    def generate_readme(self) -> str:
        """
        Generate README.md for standalone experiment.
        
        Content:
        - Experiment overview (name, model, frameworks)
        - Quick start instructions
        - Configuration details
        - Directory structure
        - Usage examples
        - No references to parent generator
        """
        
    def generate_env_example(self) -> str:
        """
        Generate .env.example file.
        
        Content:
        - API keys for enabled frameworks
        - Optional configuration variables
        - Clear instructions
        """
        
    def generate_gitignore(self) -> str:
        """
        Generate .gitignore file.
        
        Content:
        - Python artifacts (__pycache__, *.pyc, venv/)
        - Environment files (.env)
        - Run outputs (runs/*)
        - Analysis outputs (analysis/*)
        - Framework checkouts (frameworks/)
        """
```

**Specific Scripts:**

**setup.sh Template:**
```bash
#!/bin/bash
set -e

echo "========================================="
echo "Setting up experiment: {name}"
echo "========================================="

# Check Python version
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Setup environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API keys!"
    echo "   Required keys for enabled frameworks:"
    {for framework in enabled_frameworks}
    echo "   - OPENAI_API_KEY_{FRAMEWORK.upper()}"
    {endfor}
else
    echo "✅ .env file already exists"
fi

# Clone framework repositories
echo "Setting up framework repositories..."
python -m src.setup_frameworks

echo ""
echo "========================================="
echo "✅ Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys"
echo "  2. Run experiment: ./run.sh"
echo ""
```

**run.sh Template:**
```bash
#!/bin/bash
set -e

# Check if setup was run
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first!"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Run ./setup.sh first!"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
set -a
source .env
set +a

echo "========================================="
echo "Running experiment: {name}"
echo "========================================="
echo ""

# Run experiment
python -m src.main

echo ""
echo "========================================="
echo "✅ Experiment complete!"
echo "========================================="
echo ""
echo "Results saved to: ./runs/"
echo ""
echo "Next steps:"
echo "  - View run outputs: ls -la runs/"
echo "  - Generate analysis: python -m src.analysis.report_generator"
echo ""
```

**Files to Create:**
- `generator/script_generator.py`

**Dependencies:**
- `generator/artifact_collector.py` (for framework info)

---

### Task 1.4: Create `generator/dependency_analyzer.py`
**Purpose:** Generate minimal requirements.txt for standalone experiments.

**Implementation Details:**
```python
class DependencyAnalyzer:
    """Analyzes and generates minimal dependency list."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled_frameworks = self._get_enabled_frameworks()
        self.enabled_metrics = self._get_enabled_metrics()
        
    def generate_requirements(self) -> List[str]:
        """
        Generate minimal requirements list.
        
        Base requirements (always):
            pyyaml>=6.0
            requests>=2.31.0
            python-dotenv>=1.0.0
            openai>=1.0.0
            
        Framework-specific:
            (none currently - frameworks are git clones)
            
        Metrics-specific:
            matplotlib>=3.7.0 (for visualizations)
            numpy>=1.24.0 (for statistics)
            pandas>=2.0.0 (for data analysis)
            
        Analysis-specific:
            scipy>=1.10.0 (for statistical tests)
        """
        
    def get_python_version_requirement(self) -> str:
        """Return required Python version (e.g., '>=3.9')."""
        return ">=3.9"
```

**Specific Dependencies:**
```
# Core (always)
pyyaml>=6.0
requests>=2.31.0
python-dotenv>=1.0.0
openai>=1.0.0

# Analysis and metrics
matplotlib>=3.7.0
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0

# Utilities
tqdm>=4.65.0  # Progress bars
colorlog>=6.7.0  # Colored logging
```

**Files to Create:**
- `generator/dependency_analyzer.py`

**Dependencies:**
- `generator/artifact_collector.py` (for framework/metrics info)

---

### Task 1.5: Create `generator/standalone_generator.py`
**Purpose:** Main orchestrator coordinating all generation components.

**Implementation Details:**
```python
class StandaloneGenerator:
    """Main generator creating standalone experiment projects."""
    
    def __init__(self):
        self.artifact_collector = None
        self.import_rewriter = ImportRewriter()
        self.script_generator = None
        self.dependency_analyzer = None
        
    def generate(
        self, 
        name: str, 
        config: Dict[str, Any], 
        output_dir: Path
    ) -> None:
        """
        Generate complete standalone experiment project.
        
        Steps:
        1. Initialize components with config
        2. Create directory structure
        3. Collect artifacts (files to copy)
        4. Copy and rewrite source files
        5. Copy configuration files (prompts, hitl)
        6. Generate scripts (setup.sh, run.sh)
        7. Generate configuration files (config.yaml, .env.example)
        8. Generate documentation (README.md)
        9. Generate requirements.txt
        10. Generate .gitignore
        11. Initialize git repository
        12. Create initial commit
        13. Validate generated project
        """
        
    def _create_directory_structure(self, output_dir: Path) -> None:
        """
        Create experiment directory structure.
        
        Structure:
        {output_dir}/
        ├── src/
        │   ├── adapters/
        │   ├── analysis/
        │   ├── orchestrator/
        │   └── utils/
        ├── config/
        │   ├── prompts/
        │   └── hitl/
        ├── runs/
        ├── analysis/
        └── frameworks/
        """
        
    def _copy_source_files(
        self, 
        artifacts: Dict[str, List[Path]], 
        output_dir: Path
    ) -> None:
        """
        Copy source files with import rewriting.
        
        For each file:
        1. Read from template/source
        2. Rewrite imports if needed
        3. Write to output directory
        4. Preserve file permissions
        """
        
    def _copy_config_files(
        self, 
        config_files: List[Path], 
        output_dir: Path
    ) -> None:
        """
        Copy configuration files.
        
        - Prompts for enabled frameworks
        - HITL configurations
        - No modification needed
        """
        
    def _generate_all_scripts(self, output_dir: Path) -> None:
        """Generate all execution scripts."""
        
    def _generate_config_yaml(
        self, 
        config: Dict[str, Any], 
        output_dir: Path
    ) -> None:
        """
        Generate standalone config.yaml.
        
        Modifications from original:
        - Update paths to be relative to experiment root
        - Remove parent project references
        - Embed all necessary configuration
        """
        
    def _initialize_git_repo(self, output_dir: Path) -> None:
        """
        Initialize git repository.
        
        Steps:
        1. git init
        2. git add .
        3. git commit -m "Initial commit: {name} experiment"
        """
        
    def _validate_generated_project(self, output_dir: Path) -> None:
        """
        Validate generated project.
        
        Checks:
        - All required files exist
        - Scripts are executable
        - No references to parent project
        - Valid Python syntax in all .py files
        - Valid YAML syntax in config.yaml
        """
```

**Files to Create:**
- `generator/standalone_generator.py`
- `generator/__init__.py`

**Dependencies:**
- All previous generator components

---

## Phase 2: Template Extraction

### Task 2.1: Create Framework Setup Module
**Purpose:** Generate `src/setup_frameworks.py` that clones framework repositories.

**Implementation Details:**
```python
# src/setup_frameworks.py (generated into experiments)
"""Setup framework repositories for experiment."""

import sys
import subprocess
from pathlib import Path
import yaml

def load_config():
    """Load experiment configuration."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def clone_framework(name: str, repo_url: str, commit_hash: str):
    """Clone and checkout framework repository."""
    frameworks_dir = Path('frameworks')
    frameworks_dir.mkdir(exist_ok=True)
    
    target_dir = frameworks_dir / name
    
    if target_dir.exists():
        print(f"✓ {name} already exists")
        return
        
    print(f"Cloning {name}...")
    subprocess.run(['git', 'clone', repo_url, str(target_dir)], check=True)
    subprocess.run(['git', 'checkout', commit_hash], cwd=target_dir, check=True)
    print(f"✓ {name} cloned")

def main():
    config = load_config()
    
    for name, fw_config in config['frameworks'].items():
        if fw_config.get('enabled', False):
            clone_framework(
                name,
                fw_config['repo_url'],
                fw_config['commit_hash']
            )
    
    print("\n✅ All frameworks ready!")

if __name__ == '__main__':
    main()
```

**Files to Create:**
- `templates/setup_frameworks.py` (template version)

**Note:** This will be copied into each generated experiment's `src/` directory.

---

### Task 2.2: Create Main Entry Point
**Purpose:** Generate `src/main.py` - the main experiment runner.

**Implementation Details:**
```python
# src/main.py (generated into experiments)
"""Main entry point for experiment execution."""

import sys
from pathlib import Path

from src.orchestrator.runner import ExperimentRunner
from src.orchestrator.config_loader import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """Execute experiment."""
    try:
        # Load configuration
        config_path = Path('config.yaml')
        config = load_config(config_path)
        
        logger.info(f"Starting experiment: {config.get('experiment_name', 'unnamed')}")
        
        # Create runner
        runner = ExperimentRunner(config)
        
        # Execute experiment
        results = runner.run()
        
        logger.info("Experiment completed successfully")
        logger.info(f"Results saved to: {Path('runs').absolute()}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Experiment interrupted by user")
        return 130
        
    except Exception as e:
        logger.exception("Experiment failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

**Files to Create:**
- `templates/main.py` (template version)

---

### Task 2.3: Adapt Existing Source Files
**Purpose:** Review and adapt existing src/ files to work standalone.

**Files to Adapt:**

1. **`src/orchestrator/runner.py`**
   - Remove registry dependencies
   - Update paths to work from experiment root
   - Remove parent project references

2. **`src/orchestrator/config_loader.py`**
   - Simplify to load from `./config.yaml`
   - Remove registry lookups
   - Remove parent path resolution

3. **`src/utils/experiment_paths.py`**
   - Adapt to work from experiment root (not parent/experiments/)
   - Remove registry dependencies
   - Simplify path resolution

4. **`src/utils/logger.py`**
   - Keep as-is (already standalone)

5. **`src/utils/api_client.py`**
   - Keep as-is (already standalone)

6. **`src/adapters/*.py`**
   - Keep framework adapters as-is
   - May need minor path updates

**Action Items:**
- Review each file
- Remove registry imports and usage
- Update ExperimentPaths initialization
- Test imports work standalone

---

## Phase 3: CLI Integration

### Task 3.1: Update `scripts/new_experiment.py`
**Purpose:** Integrate standalone generator into experiment creation CLI.

**Changes Required:**

1. **Remove Registry Logic**
   - Delete imports: `from src.utils.experiment_registry import get_registry, ExperimentAlreadyExistsError`
   - Remove registry checks and registration calls

2. **Add Generator Integration**
```python
from generator.standalone_generator import StandaloneGenerator

def create_experiment(...):
    """Create new standalone experiment."""
    
    # Validate inputs (keep existing)
    validate_experiment_name(name)
    validate_model(model)
    validate_frameworks(frameworks)
    
    # Generate configuration (keep existing)
    config = generate_config(model, frameworks, max_runs, template_config)
    config['experiment_name'] = name  # Add experiment name to config
    
    # Determine output directory
    if experiments_base_dir:
        output_dir = experiments_base_dir / name
    else:
        output_dir = Path('experiments') / name
        
    # Check if already exists
    if output_dir.exists():
        raise ExperimentCreationError(f"Experiment directory already exists: {output_dir}")
    
    # Generate standalone experiment
    logger.info(f"Generating standalone experiment: {name}")
    generator = StandaloneGenerator()
    generator.generate(name, config, output_dir)
    
    # Success message
    print()
    print("✅ Standalone experiment created successfully!")
    print()
    print(f"📁 Location: {output_dir.absolute()}")
    print(f"🎯 Type: Fully independent git repository")
    print()
    print("Quick start:")
    print(f"  cd {output_dir}")
    print(f"  ./setup.sh")
    print(f"  # Edit .env with your API keys")
    print(f"  ./run.sh")
    print()
```

3. **Update CLI Arguments**
   - Keep existing arguments
   - Remove `--template` for now (can add later)
   - Add `--output-dir` as alias for `--experiments-dir`

4. **Update Interactive Wizard**
   - Keep existing flow
   - Remove registry checks
   - Update success message

**Files to Modify:**
- `scripts/new_experiment.py`

**Files to Delete:**
- `src/utils/experiment_registry.py`

---

### Task 3.2: Create Generation Test Script
**Purpose:** Test script to validate generation pipeline.

**Implementation:**
```python
# scripts/test_generation.py
"""Test standalone experiment generation."""

import sys
import shutil
from pathlib import Path
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.standalone_generator import StandaloneGenerator

def test_generate_minimal():
    """Test generation with minimal configuration."""
    config = {
        'experiment_name': 'test_minimal',
        'model': 'gpt-4o-mini',
        'random_seed': 42,
        'frameworks': {
            'baes': {'enabled': True, 'repo_url': '...', 'commit_hash': '...'}
        },
        'stopping_rule': {'min_runs': 5, 'max_runs': 10},
        # ... rest of minimal config
    }
    
    output_dir = Path('test_output/test_minimal')
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    generator = StandaloneGenerator()
    generator.generate('test_minimal', config, output_dir)
    
    # Validation
    assert (output_dir / 'setup.sh').exists()
    assert (output_dir / 'run.sh').exists()
    assert (output_dir / 'README.md').exists()
    assert (output_dir / 'config.yaml').exists()
    assert (output_dir / '.gitignore').exists()
    assert (output_dir / '.git').exists()
    
    print("✅ Minimal generation test passed")

def test_validate_syntax():
    """Test that generated Python files have valid syntax."""
    output_dir = Path('test_output/test_minimal')
    
    for py_file in output_dir.rglob('*.py'):
        result = subprocess.run(
            ['python', '-m', 'py_compile', str(py_file)],
            capture_output=True
        )
        if result.returncode != 0:
            print(f"❌ Syntax error in {py_file}")
            print(result.stderr.decode())
            sys.exit(1)
    
    print("✅ Syntax validation passed")

if __name__ == '__main__':
    test_generate_minimal()
    test_validate_syntax()
    print("\n✅ All tests passed!")
```

**Files to Create:**
- `scripts/test_generation.py`

---

## Phase 4: Cleanup & Restructure

### Task 4.1: Delete Old Structures
**Purpose:** Remove all backward compatibility artifacts.

**Files/Directories to Delete:**
```
runners/
  - run_experiment.sh
  - analyze_results.sh
  - reconcile_usage.sh

experiments/
  - (entire directory, currently empty)

src/utils/
  - experiment_registry.py

Root files:
  - .experiments.json (if exists)
```

**Command:**
```bash
rm -rf runners/
rm -rf experiments/
rm -f src/utils/experiment_registry.py
rm -f .experiments.json
```

---

### Task 4.2: Update Project Structure
**Purpose:** Organize as generator-focused project.

**New Structure:**
```
genai-devbench/          # The Generator
├── generator/           # NEW: Generation logic
│   ├── __init__.py
│   ├── artifact_collector.py
│   ├── import_rewriter.py
│   ├── script_generator.py
│   ├── dependency_analyzer.py
│   └── standalone_generator.py
├── templates/           # NEW: Templates for generated projects
│   ├── main.py
│   └── setup_frameworks.py
├── src/                 # KEEP: Source code (templates)
│   ├── adapters/
│   ├── analysis/
│   ├── orchestrator/
│   └── utils/
├── config/              # KEEP: Config templates
│   ├── prompts/
│   └── hitl/
├── scripts/             # KEEP: Generator scripts
│   ├── new_experiment.py
│   └── test_generation.py
├── docs/                # KEEP: Documentation
├── tests/               # KEEP: Tests
├── requirements.txt     # KEEP: Generator dependencies
└── README.md            # UPDATE: Generator-focused
```

---

### Task 4.3: Update requirements.txt
**Purpose:** Update to reflect generator dependencies.

**New requirements.txt:**
```
# Core dependencies
pyyaml>=6.0
requests>=2.31.0
python-dotenv>=1.0.0

# Code analysis (for import rewriting)
ast-comments>=1.1.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Development
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0

# Note: Generated experiments will have their own requirements.txt
# with only what they need (openai, matplotlib, etc.)
```

---

## Phase 5: Documentation

### Task 5.1: Update Main README.md
**Purpose:** Rewrite README as generator documentation.

**New Structure:**
```markdown
# GenAI DevBench - Experiment Generator

A powerful generator for creating standalone GenAI framework evaluation experiments.

## What is This?

GenAI DevBench generates complete, self-contained experiment projects for evaluating 
AI-powered development frameworks (BAES, ChatDev, GitHub Copilot). Each generated 
experiment is a fully independent Git repository with everything needed to run.

## Features

- 🎯 **Fully Standalone** - Generated experiments have zero dependencies on this generator
- 📦 **Framework Selective** - Only includes what you need
- 🚀 **Quick Setup** - One command to generate, one to run
- 🔧 **Customizable** - Full control over configuration
- 📊 **Analysis Built-in** - Metrics and visualizations included

## Quick Start

### 1. Install Generator

```bash
git clone https://github.com/yourusername/genai-devbench.git
cd genai-devbench
pip install -r requirements.txt
```

### 2. Generate Experiment

```bash
# Interactive mode
python scripts/new_experiment.py

# Or CLI mode
python scripts/new_experiment.py \
  --name my_experiment \
  --model gpt-4o \
  --frameworks baes,chatdev \
  --runs 50
```

### 3. Run Experiment

```bash
cd experiments/my_experiment
./setup.sh
# Edit .env with your API keys
./run.sh
```

## Generated Project Structure

Each experiment is a complete, standalone project:

```
my_experiment/
├── .git/              # Independent git repository
├── setup.sh           # One-command setup
├── run.sh             # One-command execution
├── config.yaml        # Experiment configuration
├── src/               # Complete source code
└── README.md          # Standalone documentation
```

## Configuration Options

- **Model**: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-4, gpt-3.5-turbo
- **Frameworks**: BAES, ChatDev, GitHub Copilot
- **Runs**: Any number (determines statistical confidence)
- **Metrics**: Functional correctness, design quality, maintainability, API usage

## Architecture

This generator creates experiments using:

- **Artifact Collector** - Determines what to include
- **Import Rewriter** - Adapts code for standalone operation
- **Script Generator** - Creates setup and execution scripts
- **Dependency Analyzer** - Generates minimal requirements.txt

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

See [LICENSE](LICENSE)
```

---

### Task 5.2: Create Generator Documentation
**Purpose:** Document generator internals.

**Files to Create:**

1. **`docs/GENERATOR_ARCHITECTURE.md`**
   - Detailed architecture documentation
   - Component descriptions
   - Data flow diagrams
   - Extension points

2. **`docs/CREATING_EXPERIMENTS.md`**
   - User guide for generating experiments
   - Configuration options
   - Best practices
   - Troubleshooting

3. **`docs/GENERATED_EXPERIMENT_GUIDE.md`**
   - Guide for users of generated experiments
   - How to run experiments
   - How to analyze results
   - How to modify/extend experiments

---

### Task 5.3: Create Example Generated README
**Purpose:** Template for generated experiment README files.

**Location:** Used by `ScriptGenerator.generate_readme()`

**Content:**
```markdown
# Experiment: {name}

**Model:** {model}  
**Frameworks:** {frameworks}  
**Max Runs:** {max_runs}

## About This Experiment

This is a standalone experiment project for evaluating AI-powered development frameworks.
It was generated but is now completely independent and can be run anywhere.

## Quick Start

### 1. Setup Environment

```bash
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Setup configuration templates

### 2. Configure API Keys

Edit `.env` and add your OpenAI API keys:

```bash
OPENAI_API_KEY_BAES=sk-...
OPENAI_API_KEY_CHATDEV=sk-...
```

### 3. Run Experiment

```bash
./run.sh
```

Results will be saved to `./runs/`

## Project Structure

```
.
├── config.yaml          # Experiment configuration
├── src/                 # Source code
│   ├── adapters/       # Framework adapters
│   ├── orchestrator/   # Experiment runner
│   ├── analysis/       # Results analysis
│   └── utils/          # Utilities
├── config/             # Framework configurations
│   ├── prompts/        # Framework prompts
│   └── hitl/           # HITL specifications
├── runs/               # Experiment outputs
└── analysis/           # Analysis results
```

## Configuration

Edit `config.yaml` to customize:
- Number of runs
- Stopping criteria
- Timeouts
- Framework settings
- Metrics to collect

## Analysis

After running, generate analysis report:

```bash
source venv/bin/activate
python -m src.analysis.report_generator
```

## Troubleshooting

### Virtual Environment Issues
```bash
rm -rf venv
./setup.sh
```

### Framework Checkout Issues
```bash
rm -rf frameworks/
python -m src.setup_frameworks
```

### API Key Errors
Verify keys in `.env` are correct and have proper permissions.

## License

See [LICENSE](LICENSE)
```

---

## Phase 6: Testing & Validation

### Task 6.1: Generate Test Experiment
**Purpose:** Create a real test experiment and validate it works.

**Steps:**
```bash
# Generate test experiment
python scripts/new_experiment.py \
  --name test_standalone \
  --model gpt-4o-mini \
  --frameworks baes \
  --runs 5 \
  --output-dir ./test_output

# Navigate to experiment
cd test_output/test_standalone

# Validate structure
ls -la
cat README.md
cat setup.sh
cat run.sh

# Test setup (don't actually run, just validate)
cat setup.sh | bash -n  # Syntax check
cat run.sh | bash -n    # Syntax check

# Check Python syntax
find src -name "*.py" -exec python -m py_compile {} \;

# Validate no parent references
grep -r "genai-devbench" . || echo "✅ No parent references found"
grep -r "experiment_registry" src/ || echo "✅ No registry references"
grep -r "../.." src/ || echo "✅ No parent path references"

# Check git
git status
git log

# Return to generator
cd ../..
```

---

### Task 6.2: Validation Checklist
**Purpose:** Ensure generated experiments meet all requirements.

**Checklist:**

- [ ] Directory structure created correctly
- [ ] All source files copied
- [ ] Imports work (no parent references)
- [ ] Scripts are executable (`chmod +x`)
- [ ] Scripts have valid bash syntax
- [ ] Python files have valid syntax
- [ ] config.yaml is valid YAML
- [ ] requirements.txt is complete
- [ ] .gitignore includes necessary patterns
- [ ] README.md is complete and accurate
- [ ] .env.example includes all needed keys
- [ ] Git repository initialized
- [ ] Initial commit created
- [ ] No references to parent project
- [ ] Only enabled frameworks included
- [ ] Only enabled metrics included

---

### Task 6.3: Integration Tests
**Purpose:** Automated tests for generation pipeline.

**Test Cases:**

1. **Test: Minimal Configuration**
   - Single framework
   - Minimal runs
   - Verify all required files generated

2. **Test: All Frameworks**
   - All frameworks enabled
   - Verify all adapters copied
   - Verify all prompts copied

3. **Test: Import Validation**
   - Scan all generated Python files
   - Verify no imports fail
   - Verify no parent path references

4. **Test: Script Validation**
   - Parse bash scripts
   - Verify syntax
   - Verify executable permissions

5. **Test: Configuration Validation**
   - Load generated config.yaml
   - Verify all required keys present
   - Verify paths are relative

**Implementation:**
```python
# tests/test_generator.py
import pytest
from pathlib import Path
from generator.standalone_generator import StandaloneGenerator

def test_minimal_generation(tmp_path):
    """Test generation with minimal config."""
    config = {...}  # Minimal config
    generator = StandaloneGenerator()
    generator.generate('test', config, tmp_path / 'test')
    
    # Assertions
    assert (tmp_path / 'test' / 'setup.sh').exists()
    # ... more assertions

def test_all_frameworks(tmp_path):
    """Test generation with all frameworks."""
    # ... similar structure

# Run: pytest tests/test_generator.py
```

---

## Phase 7: Final Polish

### Task 7.1: Add Help Documentation
**Purpose:** Make generator easy to use.

**Additions:**

1. **scripts/new_experiment.py --help**
   - Improve help text
   - Add examples
   - Add troubleshooting tips

2. **Error Messages**
   - Improve error messages
   - Add suggested fixes
   - Add helpful context

3. **Progress Indicators**
   - Show generation progress
   - Estimate time remaining
   - Clear success/failure messages

---

### Task 7.2: Performance Optimization
**Purpose:** Make generation fast and efficient.

**Optimizations:**

1. **Parallel File Copying**
   - Use threading for large file operations
   - Progress bar during copy

2. **Lazy Loading**
   - Only load templates when needed
   - Cache processed templates

3. **Incremental Generation**
   - Skip files that haven't changed
   - Support regeneration with updates

---

### Task 7.3: Create CHANGELOG
**Purpose:** Document the transformation.

**Content:**
```markdown
# Changelog

## [2.0.0] - 2025-10-20

### BREAKING CHANGES
- Complete transformation to generator-only project
- Removed all experiment execution from parent project
- Removed `.experiments.json` registry
- Removed `runners/` directory
- Generated experiments are now fully standalone

### Added
- `generator/` module for experiment generation
- Standalone experiment generation pipeline
- Automatic import rewriting
- Script generation (setup.sh, run.sh)
- Git repository initialization for experiments
- Framework-selective copying
- Minimal dependency analysis

### Changed
- `scripts/new_experiment.py` now generates standalone projects
- Project structure reorganized as generator
- README updated to reflect generator purpose

### Removed
- `runners/` directory and scripts
- `src/utils/experiment_registry.py`
- `.experiments.json` registry
- Backward compatibility code

## [1.x.x] - Previous Versions
- Original experiment execution framework
```

---

## Success Criteria

### Generated Experiments Must:
- ✅ Run independently (no parent project references)
- ✅ Have complete documentation
- ✅ Have one-command setup
- ✅ Have one-command execution
- ✅ Be valid git repositories
- ✅ Include only necessary dependencies
- ✅ Include only enabled frameworks
- ✅ Have valid Python/Bash syntax
- ✅ Be distributable (can copy to another machine)

### Generator Must:
- ✅ Have clear CLI interface
- ✅ Have good error messages
- ✅ Be well documented
- ✅ Be tested
- ✅ Be maintainable
- ✅ Be extensible

---

## Timeline Estimate

- **Phase 1:** Generator Core Infrastructure - 8 hours
- **Phase 2:** Template Extraction - 4 hours
- **Phase 3:** CLI Integration - 2 hours
- **Phase 4:** Cleanup & Restructure - 1 hour
- **Phase 5:** Documentation - 3 hours
- **Phase 6:** Testing & Validation - 4 hours
- **Phase 7:** Final Polish - 2 hours

**Total: ~24 hours** (3 working days)

---

## Risk Mitigation

### Risk: Import rewriting breaks code
**Mitigation:** 
- Extensive testing
- Syntax validation
- Manual review of generated code

### Risk: Missing dependencies
**Mitigation:**
- Comprehensive dependency analysis
- Test installations
- Document optional dependencies

### Risk: Scripts don't work on all platforms
**Mitigation:**
- Test on Linux and macOS
- Use portable bash syntax
- Document platform requirements

### Risk: Generated experiments too large
**Mitigation:**
- Only copy needed files
- Measure generated size
- Optimize if needed

---

## Next Steps After Completion

1. **Test with real use cases**
   - Generate actual experiments
   - Run them end-to-end
   - Gather feedback

2. **Add advanced features**
   - Template system for custom experiments
   - Docker generation option
   - CI/CD workflow generation

3. **Community & Distribution**
   - Publish generator
   - Create tutorial videos
   - Accept contributions

4. **Iterate based on feedback**
   - Fix bugs
   - Add requested features
   - Improve documentation

---

## Notes

- Keep commits small and focused
- Test after each phase
- Document as you go
- Ask for review before major deletions
- Keep backup of current state before transformation

---

**Ready to implement? Let's start with Phase 1!**
