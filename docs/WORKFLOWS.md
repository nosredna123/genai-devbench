# Experiment Workflows Guide

Comprehensive guide to common workflows and usage patterns in the BAEs multi-experiment system.

---

## Table of Contents

1. [Basic Workflows](#basic-workflows)
2. [Advanced Workflows](#advanced-workflows)
3. [Framework-Specific Workflows](#framework-specific-workflows)
4. [Analysis Workflows](#analysis-workflows)
5. [Troubleshooting](#troubleshooting)
6. [Real-World Scenarios](#real-world-scenarios)

---

## Basic Workflows

### Workflow 1: Single Experiment from Scratch

**Scenario:** Test BAEs with GPT-4o on 10 runs

```bash
# 1. Create experiment
python scripts/new_experiment.py \
    --name baseline_gpt4o \
    --model gpt-4o \
    --frameworks baes \
    --runs 10 \
    --description "Baseline performance with GPT-4o"

# 2. Run experiment
python scripts/run_experiment.py baseline_gpt4o

# 3. Analyze results
./runners/analyze_results.sh baseline_gpt4o

# 4. View report
cat experiments/baseline_gpt4o/analysis/report.md
```

**Duration:** ~1-3 hours (depending on task complexity)

**Output:**
- 10 isolated runs in `experiments/baseline_gpt4o/runs/baes/`
- Statistical report in `experiments/baseline_gpt4o/analysis/`
- Manifest tracking all runs

---

### Workflow 2: A/B Testing Two Models

**Scenario:** Compare GPT-4o vs GPT-4o-mini

```bash
# Create baseline (GPT-4o)
python scripts/new_experiment.py \
    --name baseline_gpt4o \
    --model gpt-4o \
    --frameworks baes \
    --runs 10

# Create variant (GPT-4o-mini)
python scripts/new_experiment.py \
    --name variant_gpt4omini \
    --model gpt-4o-mini \
    --frameworks baes \
    --runs 10

# Run both
python scripts/run_experiment.py baseline_gpt4o
python scripts/run_experiment.py variant_gpt4omini

# Analyze both
./runners/analyze_results.sh baseline_gpt4o
./runners/analyze_results.sh variant_gpt4omini

# Compare
diff -u experiments/baseline_gpt4o/analysis/report.md \
         experiments/variant_gpt4omini/analysis/report.md
```

**Tips:**
- Use consistent naming conventions (`baseline_*`, `variant_*`)
- Run experiments in parallel if you have quota
- See [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) for statistical comparison

---

### Workflow 3: Testing Multiple Frameworks

**Scenario:** Compare BAEs, ChatDev, and GHSpec

```bash
# Create multi-framework experiment
python scripts/new_experiment.py \
    --name multi_framework_test \
    --model gpt-4o \
    --frameworks baes chatdev ghspec \
    --runs 5

# Run all frameworks
python scripts/run_experiment.py multi_framework_test

# Or run one framework at a time
python scripts/run_experiment.py multi_framework_test baes
python scripts/run_experiment.py multi_framework_test chatdev
python scripts/run_experiment.py multi_framework_test ghspec

# Analyze
./runners/analyze_results.sh multi_framework_test
```

**Benefits:**
- Single config for all frameworks
- Easy cross-framework comparison
- Shared experiment directory

**Note:** Each framework's runs are isolated in separate subdirectories.

---

## Advanced Workflows

### Workflow 4: Incremental Runs with Stopping Rule

**Scenario:** Run until statistically significant, max 20 runs

```bash
# Create with stopping rule
python scripts/new_experiment.py \
    --name adaptive_experiment \
    --model gpt-4o \
    --frameworks baes \
    --runs 20  # Maximum runs
    # Stopping rule configured in config/experiment.yaml

# Run in batches
python scripts/run_experiment.py adaptive_experiment  # Runs batch 1

# Check if more runs needed
./runners/analyze_results.sh adaptive_experiment
# Check "Stopping Rule Status" in report

# Continue if needed
python scripts/run_experiment.py adaptive_experiment  # Continues from where it left off
```

**How it works:**
- System tracks completed runs in manifest
- `run_experiment.py` automatically continues from last run
- Analysis report shows stopping rule status
- Stops when confidence threshold met OR max runs reached

---

### Workflow 5: Reconciling API Usage

**Scenario:** Get accurate OpenAI cost data after runs complete

```bash
# Run experiment
python scripts/run_experiment.py my_experiment

# Wait 30+ minutes for OpenAI API usage data to be available

# Check which runs need reconciliation
./runners/reconcile_usage.sh my_experiment --list

# Reconcile all runs
./runners/reconcile_usage.sh my_experiment

# Regenerate analysis with accurate costs
./runners/analyze_results.sh my_experiment
```

**Why reconcile?**
- Initial metrics use estimated token counts
- OpenAI API provides exact usage after 30+ minutes
- Reconciliation replaces estimates with actual data
- Updates verification status to "reconciled"

**See:** [reconcile_usage_guide.md](reconcile_usage_guide.md) for details

---

### Workflow 6: Interactive Experiment Creation

**Scenario:** Create experiment with custom settings interactively

```bash
# Run without arguments for interactive mode
python scripts/new_experiment.py

# Follow prompts:
# - Experiment name: custom_timeout_test
# - Model: gpt-4o
# - Frameworks: baes
# - Max runs: 15
# - Task timeout: 1800 (30 minutes)
# - Analysis timeout: 600 (10 minutes)
# - Random seed: 42
# - Description: Testing with custom timeouts
```

**Interactive mode:**
- ✅ Validates all inputs
- ✅ Shows defaults
- ✅ Provides suggestions
- ✅ Creates complete configuration

**When to use:**
- First time users learning the system
- Complex configurations
- Want to see all available options

---

## Framework-Specific Workflows

### BAEs Framework

```bash
# Create BAEs experiment
python scripts/new_experiment.py \
    --name baes_deep_dive \
    --model gpt-4o \
    --frameworks baes \
    --runs 10

# Run
python scripts/run_experiment.py baes_deep_dive

# Check BAEs-specific metrics
cat experiments/baes_deep_dive/runs/baes/*/metrics.json | \
    jq '.aggregate_metrics.check_counts'
```

**BAEs-specific metrics:**
- `check_counts`: Number of verification attempts per type
- `double_check_rate`: Percentage using double-check strategy
- `n_check_distribution`: Distribution of N-check iterations

---

### ChatDev Framework

```bash
# Create ChatDev experiment
python scripts/new_experiment.py \
    --name chatdev_test \
    --model gpt-4o \
    --frameworks chatdev \
    --runs 5

# Run
python scripts/run_experiment.py chatdev_test

# Check ChatDev-specific outputs
ls experiments/chatdev_test/runs/chatdev/*/workspace/
```

**ChatDev notes:**
- Uses multi-agent conversation
- May take longer per run
- Check workspace for generated artifacts

---

### GHSpec Framework

```bash
# Create GHSpec experiment
python scripts/new_experiment.py \
    --name ghspec_test \
    --model gpt-4o \
    --frameworks ghspec \
    --runs 5

# Run
python scripts/run_experiment.py ghspec_test
```

**GHSpec notes:**
- Specification-driven approach
- Different metric structure than BAEs
- Check framework documentation for details

---

## Analysis Workflows

### Workflow 7: Generate Analysis Reports

```bash
# Basic analysis
./runners/analyze_results.sh my_experiment

# Analysis output location
ls experiments/my_experiment/analysis/
# - report.md          (comprehensive report)
# - visualizations/    (charts and graphs)
```

**Report sections:**
1. Executive Summary
2. Configuration Details
3. Run Summary
4. Quality Metrics
5. Performance Metrics
6. API Usage Metrics
7. Statistical Tests
8. Recommendations

---

### Workflow 8: Compare Multiple Experiments

**Scenario:** Compare 3 different model configurations

```bash
# Create and run experiments
for model in gpt-4o gpt-4o-mini gpt-3.5-turbo; do
    python scripts/new_experiment.py \
        --name "test_${model//./_}" \
        --model "$model" \
        --frameworks baes \
        --runs 10
    
    python scripts/run_experiment.py "test_${model//./_}"
    ./runners/analyze_results.sh "test_${model//./_}"
done

# Compare key metrics
for exp in test_gpt_4o test_gpt_4o_mini test_gpt_3_5_turbo; do
    echo "=== $exp ==="
    grep "Success Rate" experiments/$exp/analysis/report.md
    grep "Average Cost" experiments/$exp/analysis/report.md
    echo ""
done
```

**Better comparison:**
See [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) for statistical comparison techniques.

---

### Workflow 9: Filtering and Re-analysis

**Scenario:** Re-analyze after removing outlier runs

```bash
# Identify problematic run
cat experiments/my_experiment/runs/manifest.json | jq '.runs[] | select(.status == "error")'

# Remove from manifest (advanced - be careful!)
# Better: Note in documentation and include in analysis

# Regenerate analysis
./runners/analyze_results.sh my_experiment
```

**Note:** The system validates runs before analysis. Failed runs are excluded automatically.

---

## Troubleshooting

### Issue: "Experiment not found"

**Symptom:** Error when running `run_experiment.py` or `analyze_results.sh`

**Solution:**
```bash
# List all experiments
ls experiments/

# Check registry
python -c "from src.utils.experiment_registry import get_registry; \
    print(get_registry().list_experiments())"

# Verify exact name
python scripts/new_experiment.py --name my_experiment ...  # Note the exact name
python scripts/run_experiment.py my_experiment  # Use exact same name
```

---

### Issue: "Config hash mismatch"

**Symptom:** Error about configuration changing

**Cause:** Someone edited `config.yaml` after experiment creation

**Solution:**
```bash
# Don't edit config.yaml after creation!
# Instead, create new experiment with desired config:

python scripts/new_experiment.py \
    --name my_experiment_v2 \
    --model gpt-4o-mini \  # New setting
    --frameworks baes \
    --runs 10
```

**Why:** Config hash ensures reproducibility. Changing config mid-experiment invalidates results.

---

### Issue: "No runs found for analysis"

**Symptom:** Analysis fails because no runs exist

**Solution:**
```bash
# Check manifest
cat experiments/my_experiment/runs/manifest.json

# Run the experiment first
python scripts/run_experiment.py my_experiment

# Then analyze
./runners/analyze_results.sh my_experiment
```

---

### Issue: Run stuck or hanging

**Symptom:** `run_experiment.py` doesn't complete

**Possible causes:**
1. Task is complex (may take hours)
2. Framework hit timeout
3. API rate limit

**Solutions:**
```bash
# Check timeout settings in config
cat experiments/my_experiment/config.yaml | grep timeout

# Increase timeouts for next run (create new experiment):
python scripts/new_experiment.py \
    --name my_experiment_long \
    --model gpt-4o \
    --frameworks baes \
    --runs 10
    # Then edit config/experiment.yaml template before creation

# Check logs
tail -f experiments/my_experiment/runs/baes/*/workspace/log.txt
```

---

## Real-World Scenarios

### Scenario 1: PhD Research - Model Comparison Study

**Goal:** Compare 5 models across 3 tasks with 20 runs each

```bash
# Setup
models="gpt-4o gpt-4o-mini gpt-3.5-turbo claude-3-opus claude-3-sonnet"
tasks="task1 task2 task3"

# Create experiments (5 models × 3 tasks = 15 experiments)
for model in $models; do
    for task in $tasks; do
        exp_name="${task}_${model//./_}"
        python scripts/new_experiment.py \
            --name "$exp_name" \
            --model "$model" \
            --frameworks baes \
            --runs 20 \
            --description "Testing $model on $task"
    done
done

# Run all (can parallelize if quota allows)
for model in $models; do
    for task in $tasks; do
        exp_name="${task}_${model//./_}"
        python scripts/run_experiment.py "$exp_name" &
    done
    wait  # Wait for task batch to complete before next model
done

# Analyze all
for model in $models; do
    for task in $tasks; do
        exp_name="${task}_${model//./_}"
        ./runners/analyze_results.sh "$exp_name"
    done
done

# Aggregate results
for task in $tasks; do
    echo "=== $task ==="
    for model in $models; do
        exp_name="${task}_${model//./_}"
        echo "Model: $model"
        grep "Success Rate" experiments/$exp_name/analysis/report.md
    done
    echo ""
done
```

**Tips:**
- Use consistent naming: `{task}_{model}`
- Run in batches to avoid rate limits
- Commit after each model completes
- Use [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) for statistical analysis

---

### Scenario 2: Industry - Cost Optimization

**Goal:** Find cheapest model that meets quality threshold

```bash
# Create experiments from cheapest to most expensive
python scripts/new_experiment.py \
    --name cost_test_gpt35 \
    --model gpt-3.5-turbo \
    --frameworks baes \
    --runs 10

python scripts/new_experiment.py \
    --name cost_test_gpt4omini \
    --model gpt-4o-mini \
    --frameworks baes \
    --runs 10

python scripts/new_experiment.py \
    --name cost_test_gpt4o \
    --model gpt-4o \
    --frameworks baes \
    --runs 10

# Run in order
for exp in cost_test_gpt35 cost_test_gpt4omini cost_test_gpt4o; do
    python scripts/run_experiment.py "$exp"
    ./runners/reconcile_usage.sh "$exp"  # Get accurate costs
    ./runners/analyze_results.sh "$exp"
    
    # Check if meets quality threshold (e.g., 80% success rate)
    success_rate=$(grep "Success Rate" experiments/$exp/analysis/report.md | \
                   grep -oP '\d+\.\d+%')
    echo "$exp: $success_rate"
    
    # If meets threshold, use this model
    if (( $(echo "$success_rate > 80.0" | bc -l) )); then
        echo "✓ $exp meets threshold!"
        break
    fi
done
```

---

### Scenario 3: Reproducibility - Share Research

**Goal:** Package experiment for collaborators

```bash
# Run experiment
python scripts/new_experiment.py --name reproducible_study ...
python scripts/run_experiment.py reproducible_study
./runners/analyze_results.sh reproducible_study

# Commit to git
git add experiments/reproducible_study/
git add .experiment_registry.json
git commit -m "Add reproducible_study experiment"

# Collaborator can verify:
# 1. Config hash ensures same config
# 2. Can rerun and compare
# 3. Analysis is reproducible

# Share just the configuration:
tar -czf reproducible_study_config.tar.gz \
    experiments/reproducible_study/config.yaml \
    experiments/reproducible_study/README.md
```

**Collaborator workflow:**
```bash
# Extract config
tar -xzf reproducible_study_config.tar.gz

# Verify it exists
cat experiments/reproducible_study/config.yaml

# Rerun (creates new runs, but same config hash)
python scripts/run_experiment.py reproducible_study
./runners/analyze_results.sh reproducible_study

# Compare results
diff original_report.md experiments/reproducible_study/analysis/report.md
```

---

## Best Practices Summary

✅ **Naming:** Use descriptive, systematic names  
✅ **Versioning:** Commit experiments to git  
✅ **Documentation:** Update experiment README with findings  
✅ **Isolation:** One experiment per configuration  
✅ **Reconciliation:** Always reconcile before final analysis  
✅ **Comparison:** Use statistical methods (see COMPARISON_GUIDE.md)  
✅ **Reproducibility:** Never edit config.yaml after creation  

See [BEST_PRACTICES.md](BEST_PRACTICES.md) for detailed recommendations.

---

## Next Steps

- 📊 [Compare Experiments](COMPARISON_GUIDE.md) - Statistical comparison techniques
- 🎯 [Best Practices](BEST_PRACTICES.md) - Detailed recommendations
- 🏗️ [Architecture](architecture.md) - System design

---

**Questions?** Check [troubleshooting.md](troubleshooting.md) or open an issue.
