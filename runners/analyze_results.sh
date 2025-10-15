#!/bin/bash
# Analysis entry point for BAEs experiment results
# 
# Usage:
#   ./runners/analyze_results.sh [output_dir]
#
# Arguments:
#   output_dir: Directory to save analysis outputs (default: ./analysis_output)
#
# This script:
# 1. Loads metrics from all framework runs in runs/ directory
# 2. Computes aggregate statistics with bootstrap CI
# 3. Runs statistical tests (Kruskal-Wallis, pairwise comparisons)
# 4. Generates visualizations (radar, Pareto, timeline charts)
# 5. Produces comprehensive statistical report (report.md)

set -euo pipefail

# Configuration
RUNS_DIR="./runs"
OUTPUT_DIR="${1:-./analysis_output}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
log_info "Validating environment..."

if [ ! -d "$RUNS_DIR" ]; then
    log_error "Runs directory not found: $RUNS_DIR"
    log_error "Please run experiments first using ./runners/run_experiment.sh"
    exit 1
fi

# Check Python availability
if ! command -v python3 &> /dev/null; then
    log_error "python3 not found. Please install Python 3.11+"
    exit 1
fi

# Check dependencies
log_info "Checking dependencies..."
python3 -c "import matplotlib" 2>/dev/null || {
    log_warn "matplotlib not installed. Installing dependencies..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
}

# Create output directory
log_info "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Export environment variables for Python script
export PROJECT_ROOT
export RUNS_DIR
export OUTPUT_DIR

# Run analysis script
log_info "Running analysis..."

python3 - <<'EOF'
import os
import sys
import json
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(os.environ['PROJECT_ROOT'])
sys.path.insert(0, str(project_root))

from src.analysis.statistics import (
    bootstrap_aggregate_metrics,
    kruskal_wallis_test,
    pairwise_comparisons,
    compute_composite_scores,
    generate_statistical_report
)
from src.analysis.visualizations import (
    radar_chart,
    pareto_plot,
    timeline_chart
)
from src.utils.logger import get_logger
from src.orchestrator.manifest_manager import get_manifest, find_runs

logger = get_logger(__name__)

# Configuration
RUNS_DIR = Path(os.environ['RUNS_DIR'])
OUTPUT_DIR = Path(os.environ['OUTPUT_DIR'])

# Step 1: Load all run data from manifest
logger.info("Loading run data from manifest...")
frameworks_data = defaultdict(list)
timeline_data = defaultdict(dict)

# Get manifest
try:
    manifest = get_manifest()
    logger.info("Manifest loaded: %d total runs across %d frameworks", 
                manifest['total_runs'], len(manifest['frameworks']))
except FileNotFoundError:
    logger.error("Manifest file not found. Run experiments first or rebuild manifest.")
    sys.exit(1)
except Exception as e:
    logger.error("Failed to load manifest: %s", e)
    sys.exit(1)

# Query all runs from manifest
all_runs = find_runs()

if not all_runs:
    logger.error("No runs found in manifest")
    sys.exit(1)

logger.info("Found %d runs in manifest", len(all_runs))

# Load metrics for each run
for run_entry in all_runs:
    framework_name = run_entry['framework']
    run_id = run_entry['run_id']
    
    # Build path to metrics file
    run_dir = RUNS_DIR / framework_name / run_id
    metrics_file = run_dir / "metrics.json"
    
    if not metrics_file.exists():
        logger.warning("Metrics file not found for run %s: %s", run_id, metrics_file)
        continue
    
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
        
        # Extract aggregate metrics for analysis (only numeric metrics)
        if 'aggregate_metrics' in metrics:
            frameworks_data[framework_name].append(metrics['aggregate_metrics'])
        else:
            logger.warning("No aggregate_metrics found in run %s", run_id)
        
        # Load step-by-step data for timeline chart
        # Check if step_metrics.json exists (optional)
        step_metrics_file = run_dir / "step_metrics.json"
        if step_metrics_file.exists():
            with open(step_metrics_file, 'r', encoding='utf-8') as f:
                step_metrics = json.load(f)
            
            for step_num, step_data in step_metrics.items():
                step_int = int(step_num)
                if step_int not in timeline_data[framework_name]:
                    timeline_data[framework_name][step_int] = {
                        'CRUDe': step_data.get('CRUDe', 0),
                        'ZDI': step_data.get('ZDI', 0)
                    }
    
    except json.JSONDecodeError as e:
        logger.error("Failed to parse %s: %s", metrics_file, e)
        continue
    except Exception as e:
        logger.error("Error loading %s: %s", metrics_file, e)
        continue

if not frameworks_data:
    logger.error("No valid metrics loaded from manifest runs")
    sys.exit(1)

logger.info("Loaded data for %d frameworks", len(frameworks_data))
for fw, runs in frameworks_data.items():
    logger.info("  %s: %d runs", fw, len(runs))

# Step 2: Compute aggregate metrics
logger.info("Computing aggregate metrics...")
aggregated_data = {}

for framework, runs in frameworks_data.items():
    aggregated = bootstrap_aggregate_metrics(runs)
    aggregated_data[framework] = {
        metric: stats['mean']
        for metric, stats in aggregated.items()
    }
    
    # Add composite scores
    try:
        composite = compute_composite_scores(aggregated_data[framework])
        aggregated_data[framework].update(composite)
    except ValueError as e:
        logger.warning("Could not compute composite scores for %s: %s", framework, e)

# Step 3: Generate visualizations
logger.info("Generating visualizations...")

# Radar chart (6 key metrics)
try:
    radar_metrics = ['AUTR', 'TOK_IN', 'T_WALL', 'CRUDe', 'ESR', 'MC']
    radar_data = {
        fw: {m: aggregated_data[fw][m] for m in radar_metrics if m in aggregated_data[fw]}
        for fw in aggregated_data
    }
    
    radar_chart(
        radar_data,
        str(OUTPUT_DIR / "radar_chart.svg"),
        metrics=radar_metrics,
        title="Framework Comparison - 6 Key Metrics"
    )
    logger.info("✓ Radar chart saved")
except Exception as e:
    logger.error("Failed to generate radar chart: %s", e)

# Pareto plot (Q* vs TOK_IN)
try:
    pareto_data = {
        fw: {'Q*': data['Q*'], 'TOK_IN': data['TOK_IN']}
        for fw, data in aggregated_data.items()
        if 'Q*' in data and 'TOK_IN' in data
    }
    
    if pareto_data:
        pareto_plot(
            pareto_data,
            str(OUTPUT_DIR / "pareto_plot.svg"),
            title="Quality vs Cost Trade-off"
        )
        logger.info("✓ Pareto plot saved")
    else:
        logger.warning("Insufficient data for Pareto plot")
except Exception as e:
    logger.error("Failed to generate Pareto plot: %s", e)

# Timeline chart (CRUD coverage + downtime over steps)
try:
    if timeline_data:
        timeline_chart(
            dict(timeline_data),
            str(OUTPUT_DIR / "timeline_chart.svg"),
            title="Evolution Timeline: CRUD Coverage & Downtime"
        )
        logger.info("✓ Timeline chart saved")
    else:
        logger.warning("No step-by-step data for timeline chart")
except Exception as e:
    logger.error("Failed to generate timeline chart: %s", e)

# Step 4: Generate statistical report
logger.info("Generating statistical report...")

try:
    generate_statistical_report(
        dict(frameworks_data),
        str(OUTPUT_DIR / "report.md")
    )
    logger.info("✓ Statistical report saved")
except Exception as e:
    logger.error("Failed to generate report: %s", e)

# Step 5: Summary
logger.info("=" * 60)
logger.info("Analysis complete!")
logger.info("Output directory: %s", OUTPUT_DIR)
logger.info("Files generated:")
logger.info("  - radar_chart.svg")
logger.info("  - pareto_plot.svg")
logger.info("  - timeline_chart.svg (if step data available)")
logger.info("  - report.md")
logger.info("=" * 60)

EOF

# Completion message
log_info "Analysis complete! Results saved to: $OUTPUT_DIR"
log_info ""
log_info "Generated files:"
log_info "  - radar_chart.svg       : Multi-framework radar comparison"
log_info "  - pareto_plot.svg       : Quality vs cost trade-off"
log_info "  - timeline_chart.svg    : CRUD evolution timeline"
log_info "  - report.md             : Comprehensive statistical report"
log_info ""
log_info "To view the report:"
log_info "  cat $OUTPUT_DIR/report.md"
log_info ""
log_info "To view visualizations:"
log_info "  Open SVG files in a web browser or image viewer"
