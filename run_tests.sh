#!/bin/bash
# Quick test runner with environment setup
# Usage: ./run_tests.sh {unit|smoke|full|all}

set -e

# Get project root (script is in project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project root
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
    echo "Please create .env with your OPENAI_API_KEY_CHATDEV"
    exit 1
fi

set -a
source .env
set +a

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT"

# Print environment info
echo "=================================="
echo "BAEs Experiment Test Runner"
echo "=================================="
echo "Project Root: $PROJECT_ROOT"
echo "Python: $(python --version)"
echo "Pytest: $(pytest --version | head -1)"
echo ""

# Run tests based on argument
case "${1:-smoke}" in
  unit)
    echo "🧪 Running unit tests (fast)..."
    echo "----------------------------------"
    pytest tests/unit/ -v
    echo ""
    echo "✅ Unit tests completed in $(pytest tests/unit/ -v --co -q | grep -c 'test_') tests"
    ;;
    
  smoke)
    echo "💨 Running smoke test (3-5 minutes)..."
    echo "----------------------------------"
    pytest -m smoke -v -s
    echo ""
    echo "✅ Smoke test completed"
    ;;
    
  full)
    echo "🐌 Running full integration test (30+ minutes)..."
    echo "----------------------------------"
    echo "WARNING: This will take 30+ minutes and cost ~$0.50 in API calls"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
    pytest -m slow -v -s
    echo ""
    echo "✅ Full integration test completed"
    ;;
    
  integration)
    echo "🔗 Running all integration tests (smoke + full)..."
    echo "----------------------------------"
    pytest tests/integration/ -v -s
    ;;
    
  all)
    echo "🚀 Running all tests..."
    echo "----------------------------------"
    echo "1/3: Unit tests..."
    pytest tests/unit/ -v
    echo ""
    echo "2/3: Smoke test..."
    pytest -m smoke -v -s
    echo ""
    echo "3/3: Full integration test..."
    read -p "Run full integration test (30 min, $0.50)? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pytest -m slow -v -s
    else
        echo "Skipping full integration test"
    fi
    echo ""
    echo "✅ All requested tests completed"
    ;;
    
  quick)
    echo "⚡ Quick validation (unit + smoke)..."
    echo "----------------------------------"
    echo "1/2: Unit tests (0.36s)..."
    pytest tests/unit/ -v || exit 1
    echo ""
    echo "2/2: Smoke test (3-5 min)..."
    pytest -m smoke -v -s || exit 1
    echo ""
    echo "✅ Quick validation PASSED"
    echo "   Your changes are ready to commit!"
    ;;
    
  list)
    echo "📋 Available tests:"
    echo "----------------------------------"
    echo "Unit tests:"
    pytest tests/unit/ --co -q
    echo ""
    echo "Integration tests:"
    pytest tests/integration/ --co -q
    ;;
    
  *)
    echo "Usage: $0 {unit|smoke|full|integration|all|quick|list}"
    echo ""
    echo "Test Levels:"
    echo "  unit        - Run unit tests (0.36s, $0)"
    echo "  smoke       - Run smoke test (5 min, ~$0.08)"
    echo "  full        - Run full integration test (30 min, ~$0.50)"
    echo "  integration - Run all integration tests (smoke + full)"
    echo "  all         - Run everything (unit + smoke + full)"
    echo "  quick       - Pre-commit check (unit + smoke, ~5 min)"
    echo "  list        - List all available tests"
    echo ""
    echo "Recommended:"
    echo "  During development:  ./run_tests.sh quick"
    echo "  Before commit:       ./run_tests.sh quick"
    echo "  Before release:      ./run_tests.sh all"
    echo ""
    exit 1
    ;;
esac

echo ""
echo "=================================="
echo "Test run completed!"
echo "=================================="
