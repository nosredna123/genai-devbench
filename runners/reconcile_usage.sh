#!/bin/bash
# Reconcile token usage data from OpenAI Usage API
#
# Supports both legacy mode (./runs) and multi-experiment mode (experiments/<name>/runs)
#
# Multi-Experiment Mode (NEW):
#   ./runners/reconcile_usage.sh <experiment>                  # Reconcile all pending runs
#   ./runners/reconcile_usage.sh <experiment> <framework>      # Reconcile specific framework
#   ./runners/reconcile_usage.sh <experiment> <framework> <run># Reconcile specific run
#   ./runners/reconcile_usage.sh <experiment> --list           # List pending runs
#
# Legacy Mode (backward compatible, uses ./runs):
#   ./runners/reconcile_usage.sh                               # Reconcile all pending runs
#   ./runners/reconcile_usage.sh <framework>                   # Reconcile specific framework
#   ./runners/reconcile_usage.sh <framework> <run-id>          # Reconcile specific run
#   ./runners/reconcile_usage.sh --list                        # List pending runs
#
# Options:
#   --help, -h              Show help message

set -e

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTO-DETECT MODE: Multi-Experiment vs Legacy
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXPERIMENT_NAME=""
MODE="legacy"

# Check if first argument is an experiment directory
if [ -d "experiments/${1:-}" ]; then
    EXPERIMENT_NAME="$1"
    MODE="multi-experiment"
    shift  # Remove experiment name from arguments
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
if [ "$MODE" = "multi-experiment" ]; then
    echo "Usage API Reconciliation: $EXPERIMENT_NAME"
else
    echo "Usage API Reconciliation (Legacy Mode)"
fi
echo "========================================"
echo ""

# Handle command line arguments
case "${1:-}" in
  --help|-h)
    echo "Reconcile token usage data from OpenAI Usage API with double-check verification"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "MULTI-EXPERIMENT MODE (Recommended)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Usage:"
    echo "  $0 <experiment>                     # Reconcile all pending runs"
    echo "  $0 <experiment> <framework>         # Reconcile specific framework"
    echo "  $0 <experiment> <framework> <run>   # Reconcile specific run"
    echo "  $0 <experiment> --list              # List pending runs"
    echo ""
    echo "Examples:"
    echo "  $0 baseline                         # Reconcile all in baseline experiment"
    echo "  $0 baseline --list                  # Show what needs verification"
    echo "  $0 baseline baes                    # Reconcile BAEs runs only"
    echo "  $0 baseline baes test_run_001       # Reconcile specific run"
    echo "  $0 baseline --list --verbose        # Show all runs with details"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "LEGACY MODE (Backward Compatible, uses ./runs)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Usage:"
    echo "  $0                                  # Reconcile all pending (>30 min old)"
    echo "  $0 <framework>                      # Reconcile specific framework"
    echo "  $0 <framework> <run-id>             # Reconcile specific run"
    echo "  $0 --list                           # List pending runs"
    echo ""
    echo "Examples:"
    echo "  $0                                  # Reconcile all pending"
    echo "  $0 chatdev                          # Reconcile ChatDev runs"
    echo "  $0 chatdev test_run_123             # Reconcile specific run"
    echo "  $0 --list                           # Show what needs verification"
    echo "  $0 --list --verbose                 # Show all runs with details"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "OPTIONS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  --min-age MINUTES       # Only reconcile runs older than this (default: 30)"
    echo "  --max-age HOURS         # Don't reconcile runs older than this (default: 24)"
    echo "  --force                 # Force reconciliation even if already verified"
    echo "  --verbose               # Show detailed information (use with --list)"
    echo "  --help, -h              # Show this help message"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "DOUBLE-CHECK VERIFICATION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Runs are marked 'verified' only when TWO consecutive reconciliation"
    echo "  attempts return identical token counts with at least 60 minutes between them."
    echo "  This ensures Usage API data has fully stabilized."
    echo ""
    echo "  Status progression:"
    echo "    🕐 data_not_available → ⏳ pending → ✅ verified"
    echo ""
    echo "  Configure interval: RECONCILIATION_VERIFICATION_INTERVAL_MIN=60 in .env"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "ENVIRONMENT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  OPEN_AI_KEY_ADM must be set in .env file"
    echo "  This key requires api.usage.read scope"
    echo "  RECONCILIATION_VERIFICATION_INTERVAL_MIN (default: 60)"
    echo ""
    exit 0
    ;;
    
  --list)
    # Check for --verbose flag
    VERBOSE=false
    if [ "${2:-}" = "--verbose" ]; then
      VERBOSE=true
    fi
    
    if [ "$VERBOSE" = "true" ]; then
      echo "Scanning ALL runs with detailed status..."
      VERBOSE_PYTHON="True"
    else
      echo "Scanning for pending reconciliations..."
      VERBOSE_PYTHON="False"
    fi
    echo ""
    
    python3 << EOF
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.usage_reconciler import UsageReconciler
from src.orchestrator.manifest_manager import find_runs
import json
from datetime import datetime, timezone
import time

# Multi-experiment mode support
experiment_name = "${EXPERIMENT_NAME}" if "${EXPERIMENT_NAME}" else None

if experiment_name:
    from src.utils.experiment_paths import ExperimentPaths
    ep = ExperimentPaths(experiment_name)
    reconciler = UsageReconciler(runs_dir=ep.runs_dir)
    all_runs = find_runs(experiment_name=experiment_name)
else:
    # Legacy mode
    reconciler = UsageReconciler()
    all_runs = find_runs()

verbose = $VERBOSE_PYTHON

if verbose:
    # Show ALL runs grouped by status
    all_runs = find_runs()
    
    # Categorize runs
    verified_runs = []
    pending_runs = []
    too_recent_runs = []
    no_reconciliation_runs = []
    
    current_time = time.time()
    min_age_seconds = 30 * 60  # 30 minutes
    
    for run_entry in all_runs:
        run_id = run_entry['run_id']
        framework = run_entry['framework']
        
        # Load metrics
        run_dir = reconciler.runs_dir / framework / run_id
        metrics_file = run_dir / "metrics.json"
        
        if not metrics_file.exists():
            continue
            
        file_mtime = metrics_file.stat().st_mtime
        age_minutes = (current_time - file_mtime) / 60
        
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            
            reconciliation = metrics.get('usage_api_reconciliation', {})
            verification_status = reconciliation.get('verification_status', 'unknown')
            attempts = reconciliation.get('attempts', [])
            message = reconciliation.get('verification_message', 'Not yet reconciled')
            
            tokens_in = metrics.get('aggregate_metrics', {}).get('TOK_IN', 0)
            tokens_out = metrics.get('aggregate_metrics', {}).get('TOK_OUT', 0)
            
            run_info = {
                'run_id': run_id,
                'framework': framework,
                'age_minutes': age_minutes,
                'status': verification_status,
                'attempts': len(attempts),
                'message': message,
                'tokens_in': tokens_in,
                'tokens_out': tokens_out,
                'end_time': run_entry.get('end_time', 'Unknown')
            }
            
            if verification_status == 'verified':
                verified_runs.append(run_info)
            elif file_mtime > (current_time - min_age_seconds):
                too_recent_runs.append(run_info)
            elif verification_status in ['pending', 'data_not_available', 'warning']:
                pending_runs.append(run_info)
            else:
                no_reconciliation_runs.append(run_info)
                
        except Exception as e:
            print(f"⚠️  Error reading {framework}/{run_id}: {e}")
    
    # Print summary
    total = len(verified_runs) + len(pending_runs) + len(too_recent_runs) + len(no_reconciliation_runs)
    print(f"📊 SUMMARY: {total} total runs")
    print(f"   ✅ Verified: {len(verified_runs)}")
    print(f"   ⏳ Pending verification: {len(pending_runs)}")
    print(f"   🕐 Too recent (<30 min): {len(too_recent_runs)}")
    if no_reconciliation_runs:
        print(f"   ❓ No reconciliation data: {len(no_reconciliation_runs)}")
    print("")
    print("=" * 70)
    print("")
    
    # Print verified runs
    if verified_runs:
        print(f"✅ VERIFIED RUNS ({len(verified_runs)})")
        print(f"   Data confirmed stable across multiple checks")
        print("")
        for run in sorted(verified_runs, key=lambda x: x['end_time'], reverse=True):
            print(f"  {run['framework']}/{run['run_id'][:8]}...")
            print(f"    Tokens: {run['tokens_in']:,} in / {run['tokens_out']:,} out")
            print(f"    Age: {run['age_minutes']:.0f} minutes")
            print(f"    Message: {run['message']}")
            print("")
    
    # Print pending runs
    if pending_runs:
        print(f"⏳ PENDING VERIFICATION ({len(pending_runs)})")
        print(f"   Ready for reconciliation (>30 min old)")
        print("")
        for run in sorted(pending_runs, key=lambda x: x['age_minutes'], reverse=True):
            status_icon = {
                'pending': '⏳',
                'data_not_available': '🕐',
                'warning': '⚠️'
            }.get(run['status'], '❓')
            
            print(f"  {status_icon} {run['framework']}/{run['run_id'][:8]}...")
            print(f"    Status: {run['status']} (attempt {run['attempts']})")
            print(f"    Tokens: {run['tokens_in']:,} in / {run['tokens_out']:,} out")
            print(f"    Age: {run['age_minutes']:.0f} minutes")
            print(f"    Message: {run['message']}")
            print("")
    
    # Print too recent runs
    if too_recent_runs:
        print(f"🕐 TOO RECENT FOR RECONCILIATION ({len(too_recent_runs)})")
        print(f"   Waiting for 30-minute delay before attempting reconciliation")
        print("")
        for run in sorted(too_recent_runs, key=lambda x: x['age_minutes']):
            wait_minutes = max(0, 30 - run['age_minutes'])
            print(f"  🕐 {run['framework']}/{run['run_id'][:8]}...")
            print(f"    Tokens: {run['tokens_in']:,} in / {run['tokens_out']:,} out")
            print(f"    Age: {run['age_minutes']:.1f} minutes (wait {wait_minutes:.1f} more)")
            print("")
    
    # Print no reconciliation runs
    if no_reconciliation_runs:
        print(f"❓ NO RECONCILIATION DATA ({len(no_reconciliation_runs)})")
        print("")
        for run in no_reconciliation_runs:
            print(f"  ❓ {run['framework']}/{run['run_id'][:8]}...")
            print(f"    Tokens: {run['tokens_in']:,} in / {run['tokens_out']:,} out")
            print(f"    Age: {run['age_minutes']:.0f} minutes")
            print("")

else:
    # Normal mode: show only pending runs
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
        print("")
        print("💡 Tip: Use '--list --verbose' to see ALL runs and their status")
    else:
        print("✅ No runs need reconciliation right now!")
        print("")
        print("Possible reasons:")
        print("  • Too recent (< 30 minutes old) - wait for data propagation")
        print("  • Already verified (double-check complete)")
        print("  • Too old (> 24 hours) - outside reconciliation window")
        print("")
        print("💡 Tip: Use '--list --verbose' to see ALL runs with their status")
EOF
    ;;
    
  *)
    # Parse options
    MIN_AGE=30
    MAX_AGE=99999 # effectively no limit as default
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

# Multi-experiment mode support
experiment_name = "${EXPERIMENT_NAME}" if "${EXPERIMENT_NAME}" else None

if experiment_name:
    from src.utils.experiment_paths import ExperimentPaths
    ep = ExperimentPaths(experiment_name)
    reconciler = UsageReconciler(runs_dir=ep.runs_dir)
else:
    # Legacy mode
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

# Multi-experiment mode support
experiment_name = "${EXPERIMENT_NAME}" if "${EXPERIMENT_NAME}" else None

if experiment_name:
    from src.utils.experiment_paths import ExperimentPaths
    ep = ExperimentPaths(experiment_name)
    reconciler = UsageReconciler(runs_dir=ep.runs_dir)
else:
    # Legacy mode
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
