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
    echo "Reconcile token usage data from OpenAI Usage API with double-check verification"
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
    echo "  --force                 # Force reconciliation even if already verified"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Reconcile all pending"
    echo "  $0 chatdev                            # Reconcile ChatDev runs"
    echo "  $0 chatdev test_run_123               # Reconcile specific run"
    echo "  $0 --list                             # Show what needs verification"
    echo "  $0 --min-age 60                       # Wait 60 minutes before reconciling"
    echo ""
    echo "Double-Check Verification:"
    echo "  Runs are marked 'verified' only when TWO consecutive reconciliation"
    echo "  attempts return identical token counts with at least 60 minutes between them."
    echo "  This ensures Usage API data has fully stabilized."
    echo ""
    echo "  Status progression:"
    echo "    🕐 data_not_available → ⏳ pending → ✅ verified"
    echo ""
    echo "  Configure interval: RECONCILIATION_VERIFICATION_INTERVAL_MIN=60 in .env"
    echo ""
    echo "Environment:"
    echo "  OPEN_AI_KEY_ADM must be set in .env file"
    echo "  This key requires api.usage.read scope"
    echo "  RECONCILIATION_VERIFICATION_INTERVAL_MIN (default: 60)"
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
    print(f"Found {len(pending)} runs pending verification:")
    print("")
    for run in pending:
        age_hours = run['age_minutes'] / 60
        status = run.get('verification_status', 'unknown')
        attempts = run.get('attempts', 0)
        message = run.get('message', 'No message')
        
        # Status emoji
        status_icon = {
            'pending': '⏳',
            'data_not_available': '🕐',
            'warning': '⚠️',
            'verified': '✅'
        }.get(status, '❓')
        
        print(f"  {status_icon} {run['framework']}/{run['run_id']}")
        print(f"    Status: {status} (attempt {attempts})")
        print(f"    Age: {age_hours:.1f} hours")
        print(f"    Message: {message}")
        print("")
else:
    print("✅ No runs need reconciliation - all verified!")
    print("")
    print("Reasons a run might not be listed:")
    print("  - Too recent (< 30 minutes old)")
    print("  - Already verified (double-check complete)")
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
    
    status = report['status']
    
    # Status-specific output
    if status == 'verified':
        print(f"✅ Reconciliation VERIFIED!")
        print(f"   Data confirmed stable across multiple checks")
        print(f"   Input tokens:  {report['total_tokens_in']:,}")
        print(f"   Output tokens: {report['total_tokens_out']:,}")
        print(f"   Verified at: {report.get('verified_at', 'N/A')}")
        
    elif status == 'pending':
        print(f"⏳ Reconciliation pending verification")
        print(f"   Input tokens:  {report['total_tokens_in']:,}")
        print(f"   Output tokens: {report['total_tokens_out']:,}")
        print(f"   Attempt: {report.get('attempt_number', 'N/A')}")
        print(f"   Message: {report.get('verification_message', 'N/A')}")
        
    elif status == 'warning':
        print(f"⚠️  WARNING: {report.get('verification_message', 'Unknown issue')}")
        print(f"   Input tokens:  {report['total_tokens_in']:,}")
        print(f"   Output tokens: {report['total_tokens_out']:,}")
        print(f"   This may indicate an API issue - investigate!")
        
    elif status == 'already_verified':
        print(f"✅ Run already verified at {report.get('verified_at', 'N/A')}")
        print(f"   Use --force to re-verify")
        
    elif status == 'data_not_available':
        print(f"🕐 Token data not available yet from OpenAI Usage API")
        print(f"   This is normal - Usage API has a 5-60 minute reporting delay")
        print(f"   Run will remain pending for automatic retry")
        print(f"   Try again in 30-60 minutes")
        
    else:
        print(f"❓ Reconciliation completed with status: {status}")
        if 'verification_message' in report:
            print(f"   Message: {report['verification_message']}")
            
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
    # Count by status
    verified_count = sum(1 for r in results if r['status'] == 'verified')
    pending_count = sum(1 for r in results if r['status'] == 'pending')
    deferred_count = sum(1 for r in results if r['status'] == 'data_not_available')
    warning_count = sum(1 for r in results if r['status'] == 'warning')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"Processed {len(results)} runs:")
    if verified_count > 0:
        print(f"  ✅ Verified:   {verified_count}")
    if pending_count > 0:
        print(f"  ⏳ Pending:    {pending_count}")
    if deferred_count > 0:
        print(f"  🕐 Deferred:   {deferred_count} (data not available yet)")
    if warning_count > 0:
        print(f"  ⚠️  Warnings:   {warning_count}")
    if error_count > 0:
        print(f"  ❌ Errors:     {error_count}")
    print("")
    
    for report in results:
        status = report['status']
        framework = report['framework']
        run_id = report['run_id']
        tokens_in = report.get('total_tokens_in', 0)
        tokens_out = report.get('total_tokens_out', 0)
        message = report.get('verification_message', '')
        
        if status == 'verified':
            print(f"  ✅ {framework}/{run_id} - VERIFIED")
            print(f"    Input:  {tokens_in:,} tokens")
            print(f"    Output: {tokens_out:,} tokens")
            print(f"    {message}")
            print("")
            
        elif status == 'pending':
            print(f"  ⏳ {framework}/{run_id} - Pending")
            print(f"    Input:  {tokens_in:,} tokens")
            print(f"    Output: {tokens_out:,} tokens")
            print(f"    {message}")
            print("")
            
        elif status == 'warning':
            print(f"  ⚠️  {framework}/{run_id} - WARNING")
            print(f"    {message}")
            print("")
            
        elif status == 'data_not_available':
            print(f"  🕐 {framework}/{run_id} - Data not available yet (will retry)")
            print("")
            
        elif status == 'error':
            print(f"  ❌ {framework}/{run_id}: {report.get('error', 'Unknown error')}")
            print("")
else:
    print("✅ No runs need reconciliation - all verified!")
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
