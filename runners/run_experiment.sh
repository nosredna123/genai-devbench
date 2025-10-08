#!/bin/bash

# Run BAEs experiment framework
# Usage: ./run_experiment.sh {baes|chatdev|ghspec|all}

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}BAEs Experiment Framework${NC}"
echo "======================================"

# Check arguments
if [ $# -ne 1 ]; then
    echo -e "${RED}Error: Missing framework argument${NC}"
    echo "Usage: $0 {baes|chatdev|ghspec|all}"
    exit 1
fi

FRAMEWORK="$1"

# Validate framework choice
if [[ ! "$FRAMEWORK" =~ ^(baes|chatdev|ghspec|all)$ ]]; then
    echo -e "${RED}Error: Invalid framework '$FRAMEWORK'${NC}"
    echo "Valid options: baes, chatdev, ghspec, all"
    exit 1
fi

echo "Framework: $FRAMEWORK"
echo "Project root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}Error: Python 3.11+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install/upgrade dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"

# Check for .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Copy .env.example to .env and configure API keys"
    if [ ! -f "$PROJECT_ROOT/.env.example" ]; then
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Create runs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/runs"

# Run the experiment
echo ""
echo -e "${GREEN}Starting experiment...${NC}"
echo "======================================"

export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

if [ "$FRAMEWORK" == "all" ]; then
    # Run all frameworks sequentially
    for fw in baes chatdev ghspec; do
        echo ""
        echo -e "${YELLOW}Running framework: $fw${NC}"
        python3 -m src.orchestrator.runner "$fw" || {
            echo -e "${RED}✗ Framework $fw failed${NC}"
            exit 1
        }
        echo -e "${GREEN}✓ Framework $fw completed${NC}"
    done
else
    # Run single framework
    python3 -m src.orchestrator.runner "$FRAMEWORK" || {
        echo -e "${RED}✗ Experiment failed${NC}"
        exit 1
    }
fi

echo ""
echo -e "${GREEN}======================================"
echo "Experiment completed successfully!"
echo "=====================================${NC}"
echo ""
echo "Results available in: $PROJECT_ROOT/runs/"
