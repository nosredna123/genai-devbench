# Standalone Experiment Generator Design

## Overview

Transform `new_experiment.py` to generate fully independent, self-contained experiment projects. Each experiment is a complete Python project that can be extracted, versioned, and run independently.

## Generated Project Structure

```
experiment_name/
├── .git/                          # Initialized git repository
├── .gitignore                     # Python + project-specific ignores
├── .env.example                   # Template for API keys
├── README.md                      # Standalone instructions
├── requirements.txt               # Minimal dependencies
├── setup.sh                       # One-command environment setup
├── run.sh                         # Main execution script
├── config.yaml                    # Experiment configuration
├── src/                           # Core source code (copied & adapted)
│   ├── __init__.py
│   ├── core/                      # Essential framework runners
│   │   ├── __init__.py
│   │   ├── baes_runner.py         # (if baes enabled)
│   │   ├── chatdev_runner.py      # (if chatdev enabled)
│   │   └── ghspec_runner.py       # (if ghspec enabled)
│   ├── metrics/                   # Metrics computation
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── functional_correctness.py
│   │   ├── design_quality.py
│   │   ├── code_maintainability.py
│   │   └── api_calls.py
│   ├── analysis/                  # Results analysis
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   └── report_generator.py
│   └── utils/                     # Utilities (copied & adapted)
│       ├── __init__.py
│       ├── logger.py
│       ├── config_loader.py
│       ├── file_utils.py
│       └── api_utils.py
├── runs/                          # Output directory structure
│   ├── baes/
│   ├── chatdev/
│   └── ghspec/
├── analysis/                      # Analysis outputs
│   └── visualizations/
└── prompts/                       # Framework-specific prompts
    ├── baes/
    ├── chatdev/
    └── ghspec/
```

## Key Features

### 1. Full Independence
- **No parent references:** All imports are relative or within project
- **Self-contained:** All needed code copied and adapted
- **Standalone execution:** `./setup.sh && ./run.sh`
- **Independent git repo:** Can be pushed to separate remote

### 2. Minimal Dependencies
- Only copy source files actually needed for enabled frameworks
- Generate `requirements.txt` with minimal dependencies:
  - Core: `pyyaml`, `requests`, `python-dotenv`
  - Framework-specific: Only what's needed
  - Metrics-specific: Only enabled metrics dependencies

### 3. Adapted Scripts
- **Import path rewriting:** `from src.utils.X` → `from src.utils.X` (works from experiment root)
- **Path resolution:** All paths relative to experiment root
- **Configuration:** Embedded in `config.yaml`, no external references
- **Runner scripts:** Simplified, experiment-specific

### 4. Framework Selectivity
- Only copy runners for enabled frameworks
- Only copy prompts for enabled frameworks
- Only copy metrics for enabled metrics
- Framework configs embedded in `config.yaml`

### 5. Easy Setup
```bash
# setup.sh does everything
./setup.sh

# Equivalent to:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "Edit .env with your API keys, then run: ./run.sh"
```

## Implementation Strategy

### Phase 1: Core Infrastructure

#### 1.1 Artifact Collector
```python
class ArtifactCollector:
    """Determine what needs to be copied based on experiment config."""
    
    def collect_source_files(self, frameworks: List[str], metrics: List[str]) -> Dict[str, List[Path]]:
        """
        Returns:
            {
                'core': [runner files for enabled frameworks],
                'metrics': [metric files for enabled metrics],
                'utils': [always needed utils],
                'analysis': [analysis files]
            }
        """
        
    def collect_config_files(self) -> List[Path]:
        """Prompts, hitl configs for enabled frameworks."""
        
    def collect_scripts(self) -> List[Path]:
        """Runner, setup, analysis scripts."""
```

#### 1.2 Import Path Rewriter
```python
class ImportRewriter:
    """Rewrite imports to work in standalone project."""
    
    def rewrite_file(self, source: Path, dest: Path, base_import_path: str):
        """
        Rewrite imports in source file and save to dest.
        
        Changes:
        - from src.utils.logger import X → from src.utils.logger import X (stays same)
        - Absolute paths → Relative to experiment root
        - Remove references to parent project
        """
```

#### 1.3 Script Generator
```python
class ScriptGenerator:
    """Generate standalone execution scripts."""
    
    def generate_setup_script(self, frameworks: List[str]) -> str:
        """Generate setup.sh with venv creation, deps install."""
        
    def generate_run_script(self, config: Dict) -> str:
        """Generate run.sh that executes experiment."""
        
    def generate_readme(self, config: Dict) -> str:
        """Generate standalone README with no parent references."""
```

#### 1.4 Dependency Analyzer
```python
class DependencyAnalyzer:
    """Determine minimal requirements.txt."""
    
    def analyze_dependencies(self, source_files: List[Path], frameworks: List[str]) -> List[str]:
        """
        Returns minimal list of packages needed.
        
        Core always: pyyaml, requests, python-dotenv, openai
        Add based on frameworks/metrics enabled
        """
```

### Phase 2: Generator Pipeline

```python
class StandaloneExperimentGenerator:
    """Main generator coordinating all components."""
    
    def generate(self, name: str, config: Dict, output_dir: Path):
        """
        1. Create directory structure
        2. Collect artifacts (files to copy)
        3. Copy and rewrite source files
        4. Generate scripts (setup.sh, run.sh)
        5. Generate configuration (config.yaml, .env.example)
        6. Generate documentation (README.md)
        7. Generate requirements.txt
        8. Initialize git repository
        9. Create initial commit
        """
```

### Phase 3: Integration

Update `new_experiment.py`:
```python
def create_experiment(...):
    """
    Existing logic +
    
    # Generate standalone project
    generator = StandaloneExperimentGenerator()
    generator.generate(name, config, exp_paths.experiment_dir)
    
    print(f"✅ Standalone project created: {exp_paths.experiment_dir}")
    print(f"📦 Ready to distribute - fully independent git repository")
    print(f"🚀 Get started: cd {exp_paths.experiment_dir} && ./setup.sh")
"""
```

## Generated Scripts

### setup.sh
```bash
#!/bin/bash
set -e

echo "Setting up experiment: {name}"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✅ .env already exists"
fi

# Initialize framework repositories (if needed)
python -m src.core.setup_frameworks

echo "✅ Setup complete!"
echo "Next: Edit .env with API keys, then run: ./run.sh"
```

### run.sh
```bash
#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

# Load environment
set -a
source .env
set +a

# Run experiment
python -m src.main

echo "✅ Experiment complete!"
echo "Results in: ./runs/"
echo "Analyze: python -m src.analysis.analyzer"
```

### .env.example
```bash
# OpenAI API Keys (framework-specific)
OPENAI_API_KEY_BAES=sk-...
OPENAI_API_KEY_CHATDEV=sk-...
OPENAI_API_KEY_GHSPEC=sk-...

# Optional: Custom configurations
# LOG_LEVEL=INFO
# RESULTS_DIR=./runs
```

## Benefits

1. **True Independence:** Each experiment is a complete, standalone project
2. **Easy Distribution:** Just `git clone` or extract and go
3. **No Parent Coupling:** Zero references to generator project
4. **Minimal Size:** Only includes what's needed
5. **Easy Setup:** Single command to get running
6. **Version Control Ready:** Git initialized, ready to push
7. **Transparent:** Full source code, easy to understand and modify
8. **Reproducible:** Config embedded, dependencies locked

## Migration Path

### For Existing Experiments
Provide conversion script:
```bash
python scripts/convert_to_standalone.py baseline
# Converts existing experiment to standalone format
```

### Backward Compatibility
Keep current experiment structure working:
- Registry still tracks experiments
- Can still use `run_experiment.sh <name>`
- Standalone is opt-in via flag: `--standalone`

## Future Enhancements

1. **Archive Generation:** Add `--package` flag to also create .tar.gz
2. **Docker Support:** Add `--docker` flag to generate Dockerfile
3. **GitHub Actions:** Generate CI/CD workflows for the standalone repo
4. **Experiment Templates:** Save successful experiments as templates
5. **Dependency Locking:** Use `requirements.lock` for reproducibility

## Questions for Implementation

1. Should we keep backward compatibility or fully replace current approach?
2. Should standalone generation be default or opt-in?
3. Should we convert existing experiments or only apply to new ones?
4. Should we keep the parent `.experiments.json` registry for tracking?
