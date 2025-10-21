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
├── reconcile_usage.sh   # Usage API reconciliation
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

## Usage Reconciliation

The OpenAI Usage API has a 5-60 minute reporting delay. During experiment runs, 
token counts are estimated. After the delay, use the reconciliation script to 
update with accurate data from the Usage API.

### Workflow

1. **Run experiment**
   ```bash
   ./run.sh
   ```

2. **Wait 30-60 minutes** for Usage API data propagation

3. **Check what needs reconciliation**
   ```bash
   ./reconcile_usage.sh --list
   ```

4. **Reconcile token counts**
   ```bash
   ./reconcile_usage.sh
   ```

5. **Verify reconciliation**
   ```bash
   ./reconcile_usage.sh --list --verbose
   ```

### Commands

```bash
# List runs needing reconciliation
./reconcile_usage.sh --list

# See detailed status of all runs
./reconcile_usage.sh --list --verbose

# Reconcile all pending runs
./reconcile_usage.sh

# Reconcile specific framework
./reconcile_usage.sh baes

# Reconcile specific run
./reconcile_usage.sh baes abc123-run-id

# Show help
./reconcile_usage.sh --help
```

### API Key Requirements

The reconciliation script requires an API key with `api.usage.read` scope.
Set `OPEN_AI_KEY_ADM` in your `.env` file. You can use the same key as one
of your frameworks, or create a dedicated key.

## Analysis

After running, experiment results are saved to:
- `runs/<framework>/<run_id>/` - Individual run outputs
- `analysis/` - Analysis results and visualizations

Generate analysis report:

```bash
source venv/bin/activate
python -m src.analysis.report_generator
```

**Important:** For accurate cost and token metrics, reconcile usage data 
before generating analysis reports.

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
4. For reconciliation, ensure `OPEN_AI_KEY_ADM` has `api.usage.read` scope

### Reconciliation Issues

**No runs listed for reconciliation:**
- Runs may be too recent (< 30 minutes old) - wait and try again
- Runs may already be verified - use `--list --verbose` to see all runs
- Check that runs actually completed successfully

**Reconciliation returns 0 tokens:**
- Usage API delay may be longer than expected - wait and retry
- API key may lack `api.usage.read` scope - check permissions
- Verify the API key in `OPEN_AI_KEY_ADM` is correct

**Permission denied error:**
```bash
chmod +x reconcile_usage.sh
```

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

# Usage Reconciliation API Key
# This key is used to query the OpenAI Usage API for token reconciliation
# It requires 'api.usage.read' scope
# You can use the same key as one of the frameworks above, or a dedicated key
OPEN_AI_KEY_ADM=sk-your-admin-api-key-here

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
    
    def generate_reconcile_usage_script(self) -> str:
        """
        Generate reconcile_usage.sh script for standalone experiment.
        
        Returns:
            Shell script content
        """
        script = f"""#!/bin/bash
# Reconcile token usage data from OpenAI Usage API
# 
# The OpenAI Usage API has a 5-60 minute reporting delay. This script updates
# metrics.json files with accurate token counts after that delay.
#
# Usage:
#   ./reconcile_usage.sh              # Reconcile all pending runs
#   ./reconcile_usage.sh --list       # List runs needing reconciliation
#   ./reconcile_usage.sh --help       # Show detailed help
#   ./reconcile_usage.sh <framework>  # Reconcile specific framework
#   ./reconcile_usage.sh <framework> <run-id>  # Reconcile specific run

set -e

# Check if setup was run
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first!"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Check for required API key (for Usage API access)
# Note: Uses OPEN_AI_KEY_ADM or falls back to first framework key
if [ -z "${{OPEN_AI_KEY_ADM}}" ]; then
    # Try to use first available framework key
    FIRST_KEY=""
{self._generate_fallback_key_logic()}
    if [ -z "$FIRST_KEY" ]; then
        echo "⚠️  Warning: No OPEN_AI_KEY_ADM found in .env"
        echo "   Usage reconciliation requires an API key with usage read permissions"
        echo "   The script will attempt to use framework keys, but may fail"
    else
        export OPEN_AI_KEY_ADM="$FIRST_KEY"
    fi
fi

export PYTHONPATH="$(pwd)"

# Parse arguments
case "${{1:-}}" in
    --help|-h)
        cat << 'HELP_EOF'
Reconcile Usage - Update token counts from OpenAI Usage API

USAGE:
    ./reconcile_usage.sh [OPTIONS] [FRAMEWORK] [RUN_ID]

OPTIONS:
    --help, -h          Show this help message
    --list              List all runs needing reconciliation
    --list --verbose    Show detailed status of all runs

EXAMPLES:
    # List runs needing reconciliation
    ./reconcile_usage.sh --list

    # See detailed status of all runs
    ./reconcile_usage.sh --list --verbose

    # Reconcile all pending runs (recommended)
    ./reconcile_usage.sh

    # Reconcile specific framework
    ./reconcile_usage.sh baes
    ./reconcile_usage.sh chatdev

    # Reconcile specific run
    ./reconcile_usage.sh baes abc123-run-id

WORKFLOW:
    1. Run experiment: ./run.sh
    2. Wait 30-60 minutes for Usage API data propagation
    3. List pending: ./reconcile_usage.sh --list
    4. Reconcile: ./reconcile_usage.sh
    5. Verify: Check metrics.json files or run analysis

NOTES:
    - OpenAI Usage API has 5-60 minute reporting delay
    - Script will skip runs younger than 30 minutes
    - Runs are verified after multiple stable checks
    - Requires API key with 'api.usage.read' scope

For more information, see the documentation.
HELP_EOF
        exit 0
        ;;
    
    --list)
        VERBOSE=""
        if [ "${{2:-}}" = "--verbose" ]; then
            VERBOSE="--verbose"
        fi
        
        python3 << EOF
import sys
import json
import os
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.utils.logger import get_logger
import time

logger = get_logger(__name__)
reconciler = UsageReconciler()

# Load manifest directly from standalone experiment path
manifest_path = Path("runs/manifest.json")
if not manifest_path.exists():
    print("No runs found in this experiment.")
    sys.exit(0)

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

all_runs = manifest.get("runs", [])

if not all_runs:
    print("No runs found in this experiment.")
    sys.exit(0)

# Categorize runs
verified_runs = []
pending_runs = []
too_recent_runs = []
no_data_runs = []

current_time = time.time()
# Read minimum age from environment variable (same as reconciliation uses)
min_age_minutes = int(os.getenv('RECONCILIATION_VERIFICATION_INTERVAL_MIN', '0'))
min_age_seconds = min_age_minutes * 60

for run_entry in all_runs:
    run_id = run_entry['run_id']
    framework = run_entry['framework']
    
    # Load metrics to check status
    metrics_file = Path('runs') / framework / run_id / 'metrics.json'
    if not metrics_file.exists():
        no_data_runs.append((framework, run_id))
        continue
    
    with open(metrics_file) as f:
        metrics = json.load(f)
    
    # Check verification status
    reconciliation = metrics.get('usage_api_reconciliation', {{}})
    status = reconciliation.get('verification_status', 'pending')
    
    if status == 'verified':
        verified_runs.append((framework, run_id, metrics, reconciliation))
    else:
        # Check age - parse ISO timestamp from manifest
        start_time_str = run_entry.get('start_time')
        if start_time_str:
            # Parse ISO format: "2025-10-20T21:45:07.765641Z"
            start_time_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            start_timestamp = start_time_dt.timestamp()
            run_age = current_time - start_timestamp
            
            if run_age < min_age_seconds:
                wait_minutes = (min_age_seconds - run_age) / 60
                too_recent_runs.append((framework, run_id, wait_minutes, metrics))
            else:
                pending_runs.append((framework, run_id, run_age / 3600, metrics, reconciliation))
        else:
            # No timestamp - add to pending with 0 age
            pending_runs.append((framework, run_id, 0, metrics, reconciliation))

verbose = "$VERBOSE" == "--verbose"

if verbose:
    # Verbose mode: show everything
    print("=" * 70)
    print("RECONCILIATION STATUS - ALL RUNS")
    print("=" * 70)
    print()
    print(f"Total runs: {{len(all_runs)}}")
    print(f"  ✅ Verified: {{len(verified_runs)}}")
    print(f"  ⏳ Pending verification: {{len(pending_runs)}}")
    print(f"  🕐 Too recent: {{len(too_recent_runs)}}")
    print(f"  ❓ No reconciliation data: {{len(no_data_runs)}}")
    print()
    
    if verified_runs:
        print("─" * 70)
        print("✅ VERIFIED RUNS")
        print("─" * 70)
        for fw, rid, metrics, recon in verified_runs:
            short_id = rid[:8] if len(rid) > 8 else rid
            attempts = recon.get('attempts', [])
            if attempts:
                last = attempts[-1]
                tokens_in = last.get('total_tokens_in', 0)
                tokens_out = last.get('total_tokens_out', 0)
                print(f"  ✅ {{fw}}/{{short_id}}...")
                print(f"     Tokens: {{tokens_in:,}} in / {{tokens_out:,}} out")
                print(f"     Verified at: {{recon.get('verified_at', 'N/A')}}")
        print()
    
    if pending_runs:
        print("─" * 70)
        print("⏳ PENDING VERIFICATION")
        print("─" * 70)
        for fw, rid, age_hours, metrics, recon in pending_runs:
            short_id = rid[:8] if len(rid) > 8 else rid
            attempts = recon.get('attempts', [])
            attempt_count = len(attempts)
            print(f"  ⏳ {{fw}}/{{short_id}}...")
            print(f"     Status: {{recon.get('verification_status', 'pending')}} (attempt {{attempt_count}})")
            print(f"     Age: {{age_hours:.1f}} hours")
            if attempts:
                last = attempts[-1]
                tokens_in = last.get('total_tokens_in', 0)
                tokens_out = last.get('total_tokens_out', 0)
                print(f"     Tokens: {{tokens_in:,}} in / {{tokens_out:,}} out")
        print()
    
    if too_recent_runs:
        print("─" * 70)
        print("🕐 TOO RECENT FOR RECONCILIATION")
        print("─" * 70)
        for fw, rid, wait_min, metrics in too_recent_runs:
            short_id = rid[:8] if len(rid) > 8 else rid
            agg = metrics.get('aggregate_metrics', {{}})
            tokens_in = agg.get('TOK_IN', 0)
            tokens_out = agg.get('TOK_OUT', 0)
            print(f"  🕐 {{fw}}/{{short_id}}...")
            print(f"     Tokens: {{tokens_in:,}} in / {{tokens_out:,}} out")
            print(f"     Wait {{wait_min:.1f}} more minutes")
        print()
    
    if no_data_runs:
        print("─" * 70)
        print("❓ NO RECONCILIATION DATA")
        print("─" * 70)
        for fw, rid in no_data_runs:
            short_id = rid[:8] if len(rid) > 8 else rid
            print(f"  ❓ {{fw}}/{{short_id}}...")
        print()
    
else:
    # Normal mode: only show pending
    if not pending_runs:
        print("✅ No runs need reconciliation")
        print()
        if verified_runs:
            print(f"   {{len(verified_runs)}} run(s) already verified")
        if too_recent_runs:
            print(f"   {{len(too_recent_runs)}} run(s) too recent (wait 30+ minutes)")
        print()
        print("💡 Tip: Use '--list --verbose' to see ALL runs and their status")
    else:
        print(f"Found {{len(pending_runs)}} run(s) pending verification:")
        print()
        for fw, rid, age_hours, metrics, recon in pending_runs:
            short_id = rid[:8] if len(rid) > 8 else rid
            attempts = recon.get('attempts', [])
            attempt_count = len(attempts)
            print(f"  ⏳ {{fw}}/{{short_id}}...")
            print(f"     Status: {{recon.get('verification_status', 'pending')}} (attempt {{attempt_count}})")
            print(f"     Age: {{age_hours:.1f}} hours")
            msg = recon.get('verification_message', 'Not yet reconciled')
            print(f"     Message: {{msg}}")
            print()
        
        print("💡 Tip: Use '--list --verbose' to see ALL runs and their status")

EOF
        exit 0
        ;;
    
    *)
        # Reconcile mode
        FRAMEWORK="${{1:-}}"
        RUN_ID="${{2:-}}"
        
        if [ -n "$RUN_ID" ]; then
            # Reconcile specific run
            echo "Reconciling specific run: $FRAMEWORK/$RUN_ID"
            echo ""
            
            python3 << EOF
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.utils.logger import get_logger

logger = get_logger(__name__)
reconciler = UsageReconciler()

try:
    report = reconciler.reconcile_run("$RUN_ID", "$FRAMEWORK")
    
    print(f"✅ Reconciliation complete")
    print()
    print(f"Status: {{report['status']}}")
    print(f"Input tokens: {{report['total_tokens_in']:,}}")
    print(f"Output tokens: {{report['total_tokens_out']:,}}")
    print(f"Steps with tokens: {{report['steps_with_tokens']}}/{{report['total_steps']}}")
    print(f"Message: {{report['verification_message']}}")
    print()
    
    if report['status'] == 'verified':
        print("🎉 Data verified and stable!")
    elif report['status'] == 'pending':
        print("⏳ Verification pending - run again later to confirm stability")
    
except Exception as e:
    print(f"❌ Error: {{e}}")
    sys.exit(1)
EOF
            
        elif [ -n "$FRAMEWORK" ]; then
            # Reconcile specific framework
            echo "Reconciling framework: $FRAMEWORK"
            echo ""
            
            python3 << EOF
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.utils.logger import get_logger

logger = get_logger(__name__)
reconciler = UsageReconciler()

try:
    results = reconciler.reconcile_all_pending(framework="$FRAMEWORK")
    
    if not results:
        print("✅ No runs need reconciliation for $FRAMEWORK")
    else:
        print(f"Processed {{len(results)}} run(s):")
        print()
        
        for report in results:
            status_icon = "✅" if report['status'] == 'verified' else "⏳"
            print(f"{{status_icon}} {{report['framework']}}/{{report['run_id'][:8]}}...")
            print(f"   Tokens: {{report['total_tokens_in']:,}} in / {{report['total_tokens_out']:,}} out")
            print(f"   Status: {{report['status']}}")
            print()
            
except Exception as e:
    print(f"❌ Error: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
            
        else
            # Reconcile all pending
            echo "Reconciling all pending runs..."
            echo ""
            
            python3 << EOF
import sys
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.utils.logger import get_logger

logger = get_logger(__name__)
reconciler = UsageReconciler()

def format_age(seconds):
    # Format age in a human-readable way
    if seconds < 3600:
        return f"{{seconds/60:.0f}}m"
    elif seconds < 86400:
        return f"{{seconds/3600:.1f}}h"
    else:
        days = seconds / 86400
        return f"{{days:.1f}}d"

def get_run_age(run_id, framework):
    # Get age of run from manifest
    try:
        manifest_path = Path("runs/manifest.json")
        if not manifest_path.exists():
            return None
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        for run_entry in manifest.get("runs", []):
            if run_entry['run_id'] == run_id and run_entry['framework'] == framework:
                start_time_str = run_entry.get('start_time')
                if start_time_str:
                    start_time_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    start_timestamp = start_time_dt.timestamp()
                    return time.time() - start_timestamp
        return None
    except Exception:
        return None

try:
    # First, get list of pending runs to show total count
    manifest_path = Path("runs/manifest.json")
    if not manifest_path.exists():
        print("✅ No runs found in this experiment.")
        sys.exit(0)
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    all_runs = manifest.get("runs", [])
    if not all_runs:
        print("✅ No runs found in this experiment.")
        sys.exit(0)
    
    # Filter runs that need reconciliation
    pending_runs = []
    for run_entry in all_runs:
        run_id = run_entry['run_id']
        framework = run_entry['framework']
        
        # Check metrics to see if already verified
        metrics_file = Path('runs') / framework / run_id / 'metrics.json'
        if metrics_file.exists():
            with open(metrics_file) as f:
                metrics = json.load(f)
            
            reconciliation = metrics.get('usage_api_reconciliation', {{}})
            status = reconciliation.get('verification_status', 'pending')
            
            if status != 'verified':
                pending_runs.append((framework, run_id, run_entry))
    
    if not pending_runs:
        print("✅ No runs need reconciliation")
        print()
        print(f"Checked {{len(all_runs)}} run(s):")
        print()
        print("All runs are either:")
        print("  - Already verified ✅")
        print("  - Too recent (< 30 minutes old) 🕐")
        print("  - Outside reconciliation window ⏰")
        print()
        print("💡 Tips:")
        print("   - Use './reconcile_usage.sh --list --verbose' to see all runs")
        print("   - Wait 30-60 minutes after run completion for Usage API data")
        sys.exit(0)
    
    # Process each run and show progress in real-time
    print(f"Processing {{len(pending_runs)}} run(s)...")
    print()
    
    verified_count = 0
    pending_count = 0
    data_not_available_count = 0
    
    for idx, (framework, run_id, run_entry) in enumerate(pending_runs, 1):
        short_id = run_id[:8] if len(run_id) > 8 else run_id
        
        # Get age
        start_time_str = run_entry.get('start_time')
        age_seconds = None
        if start_time_str:
            start_time_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            start_timestamp = start_time_dt.timestamp()
            age_seconds = time.time() - start_timestamp
        age_str = format_age(age_seconds) if age_seconds else "?"
        
        # Show what we're processing
        print(f"[{{idx}}/{{len(pending_runs)}}] Processing {{framework}}/{{short_id}}... (age: {{age_str}})")
        
        # Reconcile this specific run
        try:
            report = reconciler.reconcile_run(run_id, framework)
            
            status = report['status']
            
            # Status icon and counter
            if status == 'verified':
                status_icon = "✅"
                verified_count += 1
            elif status == 'data_not_available':
                status_icon = "⏳"
                data_not_available_count += 1
            else:
                status_icon = "⏳"
                pending_count += 1
            
            # Show result
            print(f"   {{status_icon}} Tokens: {{report['total_tokens_in']:,}} in / {{report['total_tokens_out']:,}} out")
            print(f"   Status: {{status}}")
            
            msg = report.get('verification_message', '')
            if msg:
                print(f"   {{msg}}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {{e}}")
            print()
    
    print("─" * 60)
    print(f"Summary: {{verified_count}} verified, {{pending_count}} pending")
    if data_not_available_count > 0:
        print(f"         {{data_not_available_count}} waiting for Usage API data")
    print()
    
    if pending_count > 0 or data_not_available_count > 0:
        print("⏳ Some runs are pending verification.")
        print("   Run this script again later to confirm data stability.")
        if data_not_available_count > 0:
            print()
            print("💡 Tip: Usage API data typically available after 30-60 minutes")
    
except Exception as e:
    print(f"❌ Error: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
        fi
        ;;
esac

echo ""
echo "✅ Reconciliation complete!"
echo ""
"""
        return script
    
    def _generate_fallback_key_logic(self) -> str:
        """Generate bash code to find first available API key."""
        checks = []
        for fw in self.enabled_frameworks:
            key_var = f"OPENAI_API_KEY_{fw.upper()}"
            checks.append(f'''    if [ -z "$FIRST_KEY" ] && [ -n "${{{key_var}}}" ]; then
        FIRST_KEY="${{{key_var}}}"
    fi''')
        return '\n'.join(checks)
