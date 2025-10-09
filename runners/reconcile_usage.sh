#!/bin/bash
# Reconcile token usage data from OpenAI Usage API
#
# Usage:
#   ./runners/reconcile_usage.sh                    # Reconcile all pending runs
#   ./runners/reconcile_usage.sh chatdev            # Reconcile specific framework
#   ./runners/reconcile_usage.sh chatdev run-abc123 # Reconcile specific run
#   ./runners/reconcile_usage.sh --list             # List pending runs
#   ./runners/reconcile_usage.sh --help             # Show help

set -e

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found (.venv)"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source .venv/bin/activate

# Load environment variables
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please create .env with your OPEN_AI_KEY_ADM"
    exit 1
fi

set -a
source .env
set +a

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT"

# Print header
echo "========================================"
echo "Usage API Reconciliation"
echo "========================================"
echo ""

# Handle command line arguments
case "${1:-}" in
  --help|-h)
    echo "Reconcile token usage data from OpenAI Usage API"
    echo ""
    echo "Usage:"
    echo "  $0                      # Reconcile all pending runs (>30 min old)"
    echo "  $0 <framework>          # Reconcile specific framework"
    echo "  $0 <framework> <run-id> # Reconcile specific run"
    echo "  $0 --list               # List pending runs"
    echo "  $0 --help               # Show this help"
    echo ""
    echo "Options:"
    echo "  --min-age MINUTES       # Only reconcile runs older than this (default: 30)"
    echo "  --max-age HOURS         # Don't reconcile runs older than this (default: 24)"
    echo "  --force                 # Force reconciliation even if already done"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Reconcile all pending"
    echo "  $0 chatdev                            # Reconcile ChatDev runs"
    echo "  $0 chatdev test_run_123               # Reconcile specific run"
    echo "  $0 --list                             # Show what needs reconciliation"
    echo "  $0 --min-age 60                       # Wait 60 minutes before reconciling"
    echo ""
    echo "Environment:"
    echo "  OPEN_AI_KEY_ADM must be set in .env file"
    echo "  This key requires api.usage.read scope"
    echo ""
    exit 0
    ;;
    
  --list)
    echo "Scanning for pending reconciliations..."
    echo ""
    python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler

reconciler = UsageReconciler()
pending = reconciler.get_pending_runs(min_age_minutes=30)

if pending:
    print(f"Found {len(pending)} runs pending reconciliation:")
    print("")
    for run in pending:
        age_hours = run['age_minutes'] / 60
        print(f"  {run['framework']}/{run['run_id']}")
        print(f"    Age: {age_hours:.1f} hours")
        print(f"    File: {run['metrics_file']}")
        print("")
else:
    print("No runs need reconciliation")
    print("")
    print("Reasons a run might not be listed:")
    print("  - Too recent (< 30 minutes old)")
    print("  - Already reconciled")
    print("  - Already has token data")
    print("  - Too old (> 24 hours)")
EOF
    ;;
    
  *)
    # Parse options
    MIN_AGE=30
    MAX_AGE=24
    FORCE=false
    FRAMEWORK=""
    RUN_ID=""
    
    while [[ $# -gt 0 ]]; do
      case $1 in
        --min-age)
          MIN_AGE="$2"
          shift 2
          ;;
        --max-age)
          MAX_AGE="$2"
          shift 2
          ;;
        --force)
          FORCE=true
          shift
          ;;
        *)
          if [ -z "$FRAMEWORK" ]; then
            FRAMEWORK="$1"
          elif [ -z "$RUN_ID" ]; then
            RUN_ID="$1"
          fi
          shift
          ;;
      esac
    done
    
    # Run reconciliation
    if [ -n "$RUN_ID" ]; then
      # Reconcile specific run
      echo "Reconciling specific run: $FRAMEWORK/$RUN_ID"
      echo ""
      
      # Convert bash boolean to Python boolean
      FORCE_PYTHON=$([ "$FORCE" = "true" ] && echo "True" || echo "False")
      
      python3 << EOF
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.utils.logger import get_logger

logger = get_logger(__name__)
reconciler = UsageReconciler()

try:
    report = reconciler.reconcile_run(
        run_id="$RUN_ID",
        framework="$FRAMEWORK",
        force=$FORCE_PYTHON
    )
    
    if report['status'] == 'success':
        print(f"✅ Reconciliation successful!")
        print(f"   Input tokens:  {report['total_tokens_in']:,}")
        print(f"   Output tokens: {report['total_tokens_out']:,}")
        print(f"   Steps updated: {report['steps_with_tokens']}/{report['total_steps']}")
    elif report['status'] == 'already_reconciled':
        print(f"ℹ️  Run already reconciled at {report['reconciled_at']}")
    else:
        print(f"⚠️  Reconciliation completed with status: {report['status']}")
except Exception as e:
    logger.error(f"Reconciliation failed: {e}")
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF
      
    else
      # Reconcile all pending or specific framework
      if [ -n "$FRAMEWORK" ]; then
        echo "Reconciling framework: $FRAMEWORK"
      else
        echo "Reconciling all pending runs"
      fi
      echo "  Min age: $MIN_AGE minutes"
      echo "  Max age: $MAX_AGE hours"
      echo ""
      
      python3 << EOF
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.utils.logger import get_logger

logger = get_logger(__name__)
reconciler = UsageReconciler()

framework = "$FRAMEWORK" if "$FRAMEWORK" else None

results = reconciler.reconcile_all_pending(
    framework=framework,
    min_age_minutes=$MIN_AGE,
    max_age_hours=$MAX_AGE
)

if results:
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"Processed {len(results)} runs:")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Errors:  {error_count}")
    print("")
    
    for report in results:
        if report['status'] == 'success':
            framework = report['framework']
            run_id = report['run_id']
            tokens_in = report.get('total_tokens_in', 0)
            tokens_out = report.get('total_tokens_out', 0)
            steps = report.get('steps_with_tokens', 0)
            total_steps = report.get('total_steps', 0)
            
            print(f"  {framework}/{run_id}")
            print(f"    Input:  {tokens_in:,} tokens")
            print(f"    Output: {tokens_out:,} tokens")
            print(f"    Steps:  {steps}/{total_steps} updated")
            print("")
        elif report['status'] == 'error':
            print(f"  ❌ {report['framework']}/{report['run_id']}: {report.get('error', 'Unknown error')}")
            print("")
else:
    print("No runs need reconciliation")
    print("")
    print("To see what runs exist, use: $0 --list")
EOF
    fi
    ;;
esac

echo ""
echo "========================================"
echo "Reconciliation complete!"
echo "========================================"
