#!/bin/bash
# Analysis entry point for BAEs experiment results
# 
# Usage:
#   # Legacy mode (backward compatible)
#   ./runners/analyze_results.sh [output_dir]
#
#   # Multi-experiment mode
#   ./runners/analyze_results.sh EXPERIMENT_NAME
#
# Arguments:
#   experiment_name or output_dir: 
#     - If matches experiment in experiments/, uses multi-experiment mode
#     - Otherwise treats as output directory (legacy mode)
#
# This script:
# 1. Loads metrics from all framework runs in runs/ directory
# 2. Computes aggregate statistics with bootstrap CI
# 3. Runs statistical tests (Kruskal-Wallis, pairwise comparisons)
# 4. Generates visualizations (config-driven via VisualizationFactory)
# 5. Produces comprehensive statistical report (report.md)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# Determine mode (multi-experiment or legacy)
if [ $# -ge 1 ]; then
    ARG1="$1"
    # Check if argument is an experiment name
    if [ -d "$PROJECT_ROOT/experiments/$ARG1" ]; then
        # Multi-experiment mode
        EXPERIMENT_NAME="$ARG1"
        RUNS_DIR="$PROJECT_ROOT/experiments/$EXPERIMENT_NAME/runs"
        OUTPUT_DIR="$PROJECT_ROOT/experiments/$EXPERIMENT_NAME/analysis"
        CONFIG_FILE="$PROJECT_ROOT/experiments/$EXPERIMENT_NAME/config.yaml"
        MODE="multi-experiment"
        
        log_info "Multi-experiment mode: $EXPERIMENT_NAME"
    else
        # Legacy mode - treat argument as output directory
        RUNS_DIR="$PROJECT_ROOT/runs"
        OUTPUT_DIR="$ARG1"
        CONFIG_FILE="$PROJECT_ROOT/config/experiment.yaml"
        MODE="legacy"
        EXPERIMENT_NAME=""
        
        log_info "Legacy mode: custom output directory"
    fi
else
    # Default legacy mode
    RUNS_DIR="$PROJECT_ROOT/runs"
    OUTPUT_DIR="$PROJECT_ROOT/analysis_output"
    CONFIG_FILE="$PROJECT_ROOT/config/experiment.yaml"
    MODE="legacy"
    EXPERIMENT_NAME=""
    
    log_info "Legacy mode: default output directory"
fi

# Validate environment
log_info "Validating environment..."

if [ ! -d "$RUNS_DIR" ]; then
    log_error "Runs directory not found: $RUNS_DIR"
    if [ "$MODE" = "multi-experiment" ]; then
        log_error "Please run experiment first: python scripts/run_experiment.py $EXPERIMENT_NAME"
    else
        log_error "Please run experiments first using ./runners/run_experiment.sh"
    fi
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    log_error "Config file not found: $CONFIG_FILE"
    exit 1
fi

# Check Python and dependencies
log_info "Checking dependencies..."
python3 -c "import matplotlib" 2>/dev/null || {
    log_warn "matplotlib not installed. Installing dependencies..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
}

# Create output directory
log_info "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Run the new Python analysis script
log_info "Running analysis with VisualizationFactory..."

if [ "$MODE" = "multi-experiment" ]; then
    # Multi-experiment mode: pass experiment name as positional argument
    python3 "$PROJECT_ROOT/scripts/generate_analysis.py" "$EXPERIMENT_NAME"
else
    # Legacy mode: pass paths as options
    python3 "$PROJECT_ROOT/scripts/generate_analysis.py" \
        --output-dir "$OUTPUT_DIR" \
        --config "$CONFIG_FILE" \
        --runs-dir "$RUNS_DIR"
fi

# Check exit code
if [ $? -eq 0 ]; then
    log_info ""
    log_info "Analysis complete! Results saved to: $OUTPUT_DIR"
    log_info ""
    log_info "To view the report:"
    log_info "  cat $OUTPUT_DIR/report.md"
    log_info ""
    log_info "To view visualizations:"
    log_info "  Open PNG/SVG files in $OUTPUT_DIR with a web browser or image viewer"
else
    log_error "Analysis failed. Check logs above for details."
    exit 1
fi
