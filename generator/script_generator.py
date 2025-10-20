"""
Script Generator

Generates standalone execution scripts and documentation for experiment projects.
Creates setup.sh, run.sh, README.md, .env.example, and .gitignore.
"""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class ScriptGenerator:
    """Generates execution scripts for standalone experiments."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize script generator.
        
        Args:
            config: Experiment configuration dictionary
        """
        self.config = config
        self.experiment_name = config.get('experiment_name', 'experiment')
        self.model = config.get('model', 'gpt-4o')
        self.enabled_frameworks = self._get_enabled_frameworks()
        self.max_runs = config.get('stopping_rule', {}).get('max_runs', 50)
    
    def _get_enabled_frameworks(self) -> List[str]:
        """Get list of enabled framework names."""
        frameworks = self.config.get('frameworks', {})
        return [
            name for name, fw_config in frameworks.items()
            if fw_config.get('enabled', False)
        ]
    
    def generate_setup_script(self) -> str:
        """
        Generate setup.sh script for experiment setup.
        
        Returns:
            Shell script content
        """
        frameworks_list = '\n'.join([
            f'    echo "   - OPENAI_API_KEY_{fw.upper()}"'
            for fw in self.enabled_frameworks
        ])
        
        script = f"""#!/bin/bash
set -e

echo "========================================="
echo "Setting up experiment: {self.experiment_name}"
echo "========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{{sys.version_info.major}}.{{sys.version_info.minor}}")')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo "✓ Dependencies installed"

# Setup environment file
echo ""
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API keys!"
    echo ""
    echo "   Required keys for enabled frameworks:"
{frameworks_list}
    echo ""
    echo "   Edit with: nano .env  (or your preferred editor)"
else
    echo "✅ .env file already exists"
fi

# Clone framework repositories
echo ""
echo "Setting up framework repositories..."
python -m src.setup_frameworks

echo ""
echo "========================================="
echo "✅ Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys: nano .env"
echo "  2. Run experiment: ./run.sh"
echo ""
"""
        return script
    
    def generate_run_script(self) -> str:
        """
        Generate run.sh script for experiment execution.
        
        Returns:
            Shell script content
        """
        script = f"""#!/bin/bash
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

# Verify API keys are set
MISSING_KEYS=false
{self._generate_api_key_checks()}

if [ "$MISSING_KEYS" = true ]; then
    echo ""
    echo "❌ Please set all required API keys in .env file"
    echo "   Edit with: nano .env"
    exit 1
fi

echo "========================================="
echo "Running experiment: {self.experiment_name}"
echo "========================================="
echo ""
echo "Configuration:"
echo "  Model: {self.model}"
echo "  Frameworks: {', '.join(self.enabled_frameworks)}"
echo "  Max runs per framework: {self.max_runs}"
echo ""
echo "This may take a while..."
echo ""

# Run experiment
python -m src.main

EXIT_CODE=$?

echo ""
echo "========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Experiment completed successfully!"
else
    echo "❌ Experiment failed with exit code: $EXIT_CODE"
fi
echo "========================================="
echo ""
echo "Results saved to: ./runs/"
echo ""
echo "Next steps:"
echo "  - View run outputs: ls -la runs/"
echo "  - Generate analysis: python -m src.analysis.report_generator"
echo ""

exit $EXIT_CODE
"""
        return script
    
    def _generate_api_key_checks(self) -> str:
        """Generate bash code to check API keys."""
        checks = []
        for fw in self.enabled_frameworks:
            key_var = f"OPENAI_API_KEY_{fw.upper()}"
            checks.append(f'''if [ -z "${{{key_var}}}" ]; then
    echo "⚠️  Missing: {key_var}"
    MISSING_KEYS=true
fi''')
        return '\n'.join(checks)
    
    def generate_readme(self) -> str:
        """
        Generate README.md for standalone experiment.
        
        Returns:
            Markdown content
        """
        frameworks_str = ', '.join(self.enabled_frameworks)
        total_runs = self.max_runs * len(self.enabled_frameworks)
        
        readme = f"""# Experiment: {self.experiment_name}

**Created:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  
**Model:** `{self.model}`  
**Frameworks:** {frameworks_str}  
**Max Runs:** {self.max_runs} per framework ({total_runs} total)

## About This Experiment

This is a standalone experiment project for evaluating AI-powered software development frameworks.
It is completely independent and can be run anywhere with Python 3.9+ installed.

## Quick Start

### 1. Setup Environment

```bash
./setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Setup `.env` configuration template
- Clone framework repositories

### 2. Configure API Keys

Edit `.env` and add your OpenAI API keys:

```bash
nano .env  # or use your preferred editor
```

Required keys:
{self._generate_api_key_list()}

### 3. Run Experiment

```bash
./run.sh
```

Results will be saved to `./runs/`

## Project Structure

```
{self.experiment_name}/
├── config.yaml          # Experiment configuration
├── setup.sh             # One-command setup
├── run.sh               # One-command execution
├── .env                 # Environment variables (API keys)
├── .gitignore           # Git ignore patterns
├── requirements.txt     # Python dependencies
├── src/                 # Source code
│   ├── adapters/       # Framework adapters
│   ├── analysis/       # Results analysis
│   ├── orchestrator/   # Experiment runner
│   ├── utils/          # Utilities
│   ├── setup_frameworks.py  # Framework setup
│   └── main.py         # Entry point
├── config/             # Framework configurations
│   ├── prompts/        # Framework-specific prompts
│   └── hitl/           # HITL specifications
├── runs/               # Experiment outputs (generated)
├── analysis/           # Analysis results (generated)
└── frameworks/         # Framework repositories (generated)
```

## Configuration

The experiment is configured via `config.yaml`. Key settings:

- **model**: OpenAI model to use
- **frameworks**: Framework configurations and settings
- **stopping_rule**: When to stop collecting data
- **metrics**: Which metrics to collect
- **timeouts**: Timeout configurations

You can edit `config.yaml` to customize the experiment.

## Running

### Full Experiment

```bash
./run.sh
```

### Individual Components

```bash
# Activate virtual environment first
source venv/bin/activate

# Setup frameworks only
python -m src.setup_frameworks

# Run main experiment
python -m src.main

# Generate analysis report
python -m src.analysis.report_generator
```

## Analysis

After running, experiment results are saved to:
- `runs/<framework>/<run_id>/` - Individual run outputs
- `analysis/` - Analysis results and visualizations

Generate analysis report:

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

1. Verify keys in `.env` are correct (start with `sk-`)
2. Check API key permissions on OpenAI platform
3. Verify different keys are used for each framework (if required)

### Import Errors

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Frameworks

This experiment evaluates the following frameworks:

{self._generate_framework_descriptions()}

## Metrics Collected

{self._generate_metrics_list()}

## License

See [LICENSE](LICENSE) file.

## Support

For issues or questions, please refer to the documentation in the `docs/` directory
or check the source code comments.
"""
        return readme
    
    def _generate_api_key_list(self) -> str:
        """Generate markdown list of required API keys."""
        return '\n'.join([
            f'- `OPENAI_API_KEY_{fw.upper()}` - For {fw.upper()} framework'
            for fw in self.enabled_frameworks
        ])
    
    def _generate_framework_descriptions(self) -> str:
        """Generate framework descriptions."""
        descriptions = {
            'baes': '**BAES** - Behavior-driven Agile Engineering System',
            'chatdev': '**ChatDev** - Communicative agents for software development',
            'ghspec': '**GitHub Copilot** - AI pair programmer',
        }
        
        return '\n'.join([
            f'- {descriptions.get(fw, fw.upper())}'
            for fw in self.enabled_frameworks
        ])
    
    def _generate_metrics_list(self) -> str:
        """Generate list of collected metrics."""
        metrics = self.config.get('metrics', {}).get('enabled', [])
        if not metrics:
            return '- Standard metrics (tokens, cost, time)'
        
        metric_descriptions = {
            'functional_correctness': '**Functional Correctness** - Does the code work?',
            'design_quality': '**Design Quality** - Architecture and design patterns',
            'code_maintainability': '**Code Maintainability** - Readability and maintainability',
            'api_calls': '**API Calls** - OpenAI API usage and costs',
        }
        
        return '\n'.join([
            f'- {metric_descriptions.get(m, m)}'
            for m in metrics
        ])
    
    def generate_env_example(self) -> str:
        """
        Generate .env.example file.
        
        Returns:
            Environment file content
        """
        api_keys = '\n'.join([
            f'OPENAI_API_KEY_{fw.upper()}=sk-your-api-key-here'
            for fw in self.enabled_frameworks
        ])
        
        env = f"""# OpenAI API Keys
# Get your API keys from: https://platform.openai.com/api-keys
#
# IMPORTANT: Use different API keys for each framework to track usage separately
# All keys must have access to the model: {self.model}

{api_keys}

# Usage Reconciliation Configuration
# How often to check for stable reconciliation (in minutes)
RECONCILIATION_VERIFICATION_INTERVAL_MIN=2

# Number of consecutive stable checks required to consider reconciliation complete
RECONCILIATION_MIN_STABLE_VERIFICATIONS=3

# Optional: Logging configuration
# LOG_LEVEL=INFO

# Optional: Custom results directory
# RESULTS_DIR=./runs
"""
        return env
    
    def generate_gitignore(self) -> str:
        """
        Generate .gitignore file.
        
        Returns:
            .gitignore content
        """
        gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local

# Experiment Outputs
runs/
analysis/
*.log

# Framework Checkouts
frameworks/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Temporary Files
tmp/
temp/
*.tmp

# Coverage Reports
.coverage
htmlcov/
.pytest_cache/
"""
        return gitignore
