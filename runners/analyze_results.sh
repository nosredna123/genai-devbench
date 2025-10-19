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
# 4. Generates visualizations (config-driven via VisualizationFactory)
# 5. Produces comprehensive statistical report (report.md)

set -euo pipefail

# Configuration
RUNS_DIR="./runs"
OUTPUT_DIR="${1:-./analysis_output}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/experiment.yaml"

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
python3 "$PROJECT_ROOT/scripts/generate_analysis.py" \
    --output-dir "$OUTPUT_DIR" \
    --config "$CONFIG_FILE" \
    --runs-dir "$RUNS_DIR"

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
