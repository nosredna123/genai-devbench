# Best Practices Guide

Recommendations and guidelines for effective use of the BAEs multi-experiment system.

---

## Table of Contents

1. [Experiment Design](#experiment-design)
2. [Naming Conventions](#naming-conventions)
3. [Configuration Management](#configuration-management)
4. [Running Experiments](#running-experiments)
5. [Data Quality](#data-quality)
6. [Analysis and Reporting](#analysis-and-reporting)
7. [Reproducibility](#reproducibility)
8. [Collaboration](#collaboration)
9. [Performance Optimization](#performance-optimization)
10. [Common Pitfalls](#common-pitfalls)

---

## Experiment Design

### Plan Before You Run

**Do:**
- ✅ Define clear hypothesis before starting
- ✅ Determine minimum sample size (power analysis)
- ✅ Set success criteria upfront
- ✅ Document expected outcomes

**Don't:**
- ❌ Run experiments without clear goals
- ❌ Change success criteria after seeing results
- ❌ Use arbitrary sample sizes

**Example:**

```markdown
# Experiment Plan: baseline_gpt4o

## Hypothesis
GPT-4o will achieve >80% success rate with <$3/run cost

## Sample Size
- Minimum: 10 runs (power=0.80 for 20% effect)
- Maximum: 20 runs (stopping rule)

## Success Criteria
- Success rate ≥ 80% (lower CI bound)
- Cost ≤ $3.00 (mean)
- Completion time ≤ 60 minutes (mean)

## Decision
If all criteria met → Use GPT-4o for production
If not → Test GPT-4o-mini variant
```

---

### Start Small, Scale Up

**Recommended approach:**

```bash
# 1. Pilot run (1 run)
python scripts/new_experiment.py \
    --name pilot_test \
    --model gpt-4o \
    --frameworks baes \
    --runs 1

python scripts/run_experiment.py pilot_test

# Verify it works, check outputs

# 2. Small batch (5 runs)
python scripts/new_experiment.py \
    --name small_batch_test \
    --model gpt-4o \
    --frameworks baes \
    --runs 5

python scripts/run_experiment.py small_batch_test
./runners/analyze_results.sh small_batch_test

# Check variance, estimate time/cost

# 3. Full experiment (15-20 runs)
python scripts/new_experiment.py \
    --name full_experiment \
    --model gpt-4o \
    --frameworks baes \
    --runs 20
```

**Benefits:**
- Catch configuration issues early
- Estimate total time and cost
- Refine settings before committing resources

---

### Use Appropriate Sample Sizes

**Rule of thumb:**

| Goal | Minimum Runs | Recommended Runs |
|------|--------------|------------------|
| Quick test | 1-3 | 5 |
| Initial exploration | 5-10 | 10 |
| Robust statistics | 10-15 | 15 |
| Publication-quality | 20+ | 30 |
| A/B testing | 10 per variant | 15 per variant |

**Power analysis:**
See [statistical_power_analysis.md](statistical_power_analysis.md) for calculators.

**Stopping rule:**
Use maximum runs with confidence-based stopping for efficiency.

---

## Naming Conventions

### Systematic Naming

**Pattern:** `{purpose}_{model}_{variant}_{date}`

**Examples:**

```bash
# Purpose-based
baseline_gpt4o
variant_gpt4omini
ablation_no_doublecheck

# Model comparison
compare_gpt4o_v1
compare_gpt4omini_v1
compare_claude3opus_v1

# Feature testing
test_timeout1800_gpt4o
test_timeout3600_gpt4o

# Date-stamped (for iterative work)
baseline_gpt4o_20251020
baseline_gpt4o_20251027  # Re-run with updated prompt
```

**Benefits:**
- Easy to find related experiments
- Clear purpose from name
- Sortable and groupable

---

### Naming Rules

**Do:**
- ✅ Use lowercase
- ✅ Use underscores (not spaces or hyphens)
- ✅ Be descriptive (not `test1`, `test2`)
- ✅ Include key differentiator in name
- ✅ Use consistent prefixes (`baseline_`, `variant_`, `ablation_`)

**Don't:**
- ❌ Use generic names (`experiment`, `test`)
- ❌ Use spaces or special characters
- ❌ Make names too long (>50 chars)
- ❌ Include version numbers that will change

**Bad names:**
- `test`
- `my experiment`
- `final-version-really-final-v3`
- `baseline_gpt4o_with_custom_prompt_and_increased_timeout_testing_v2`

**Good names:**
- `baseline_gpt4o`
- `variant_gpt4omini_long_timeout`
- `ablation_no_ncheck`
- `compare_models_task1`

---

## Configuration Management

### Never Edit config.yaml After Creation

**Why:** Config hash ensures reproducibility. Changing config invalidates experiment.

**Wrong:**
```bash
# Create experiment
python scripts/new_experiment.py --name my_exp --model gpt-4o ...

# Run some iterations
python scripts/run_experiment.py my_exp

# ❌ WRONG: Edit config
nano experiments/my_exp/config.yaml  # Change model to gpt-4o-mini

# ❌ This will fail with config hash mismatch!
python scripts/run_experiment.py my_exp
```

**Right:**
```bash
# Create new experiment with desired config
python scripts/new_experiment.py \
    --name my_exp_v2 \
    --model gpt-4o-mini \
    --frameworks baes \
    --runs 10

# Run the new experiment
python scripts/run_experiment.py my_exp_v2
```

---

### Version Control Experiments

**Git workflow:**

```bash
# Create and run experiment
python scripts/new_experiment.py --name baseline_gpt4o ...
python scripts/run_experiment.py baseline_gpt4o

# Commit experiment configuration
git add experiments/baseline_gpt4o/config.yaml
git add experiments/baseline_gpt4o/README.md
git add experiments/baseline_gpt4o/.meta/
git add .experiment_registry.json
git commit -m "Add baseline_gpt4o experiment configuration"

# After runs complete
git add experiments/baseline_gpt4o/runs/manifest.json
git commit -m "Complete baseline_gpt4o: 10 runs"

# After analysis
git add experiments/baseline_gpt4o/analysis/
git commit -m "Add baseline_gpt4o analysis report"
```

**Benefits:**
- Track experiment history
- Share configurations with team
- Revert if needed
- Document evolution

**Tip:** Use `.gitignore` to exclude large workspace directories if needed:

```gitignore
# .gitignore
experiments/*/runs/*/workspace/  # Exclude large workspace artifacts
!experiments/*/runs/manifest.json  # But keep manifests
```

---

### Document Your Experiments

**Update experiment README:**

```bash
# After running experiment
cat >> experiments/baseline_gpt4o/README.md << 'EOF'

## Results Summary

- Runs completed: 10/10
- Success rate: 85% ± 7%
- Average cost: $2.45 ± $0.32
- Date: 2025-10-20

## Key Findings

- GPT-4o performs well on this task
- Occasional timeout issues (1/10 runs)
- Cost within acceptable range

## Decision

Approved for production deployment with monitoring.

## Follow-up

- Test GPT-4o-mini for cost comparison (variant_gpt4omini)
- Investigate timeout in run 7
EOF
```

---

## Running Experiments

### Monitor Progress

**Use tmux/screen for long runs:**

```bash
# Start tmux session
tmux new -s experiment

# Run experiment
python scripts/run_experiment.py long_running_test

# Detach: Ctrl+B, then D

# Reattach later
tmux attach -t experiment
```

**Check logs:**

```bash
# Latest run log
tail -f experiments/my_exp/runs/baes/*/workspace/log.txt

# All run logs
ls -lt experiments/my_exp/runs/baes/*/workspace/log.txt
```

---

### Handle Failures Gracefully

**What to do when a run fails:**

```bash
# 1. Check the error
cat experiments/my_exp/runs/baes/baes_run_*/workspace/log.txt | grep -i error

# 2. Determine cause
# - Timeout? Increase timeout setting
# - API error? Check API status
# - Code bug? Fix and create new experiment

# 3. Continue or restart
# System automatically skips failed runs in analysis
# Just continue running:
python scripts/run_experiment.py my_exp  # Continues from last successful run
```

**Don't:**
- ❌ Manually delete failed runs from manifest
- ❌ Edit metrics.json to "fix" failures
- ❌ Restart experiment from scratch (continue instead)

---

### Parallel Experiments

**When safe to parallelize:**

```bash
# Different experiments on different models (watch API quota!)
python scripts/run_experiment.py baseline_gpt4o &
python scripts/run_experiment.py variant_gpt35turbo &
wait

# Different frameworks (less API contention)
python scripts/run_experiment.py multi_fw_test baes &
python scripts/run_experiment.py multi_fw_test chatdev &
python scripts/run_experiment.py multi_fw_test ghspec &
wait
```

**When NOT to parallelize:**
- ❌ Same experiment (single experiment runs sequentially by design)
- ❌ Limited API quota
- ❌ Shared resources (file locks, etc.)

---

## Data Quality

### Reconcile API Usage

**Always reconcile before final analysis:**

```bash
# Run experiment
python scripts/run_experiment.py my_exp

# Wait 30+ minutes for OpenAI usage data

# Reconcile
./runners/reconcile_usage.sh my_exp

# Regenerate analysis with accurate data
./runners/analyze_results.sh my_exp
```

**Why:**
- Initial metrics use estimated token counts
- Reconciliation provides exact API usage
- Affects cost calculations and usage metrics

**Check reconciliation status:**

```bash
# List reconciliation status
./runners/reconcile_usage.sh my_exp --list

# Look for RECONCILED status in manifest
cat experiments/my_exp/runs/manifest.json | jq '.runs[].verification_status'
```

---

### Validate Runs

**Automated validation:**
The system automatically validates:
- ✅ Config hash matches
- ✅ Metrics schema is correct
- ✅ Required fields present
- ✅ Run completed successfully

**Manual spot checks:**

```bash
# Check a few runs manually
for run in experiments/my_exp/runs/baes/baes_run_*/; do
    echo "=== $run ==="
    cat $run/metrics.json | jq '.aggregate_metrics.quality_metrics'
    echo ""
done
```

---

### Handle Outliers

**Identify outliers:**

```bash
# Look for extreme values in analysis report
cat experiments/my_exp/analysis/report.md | grep -A 5 "Outliers"

# Or calculate manually
python3 << 'EOF'
import json
from pathlib import Path
import statistics

runs_dir = Path("experiments/my_exp/runs/baes")
costs = []
for run_dir in runs_dir.glob("*"):
    metrics_file = run_dir / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            data = json.load(f)
            costs.append(data['aggregate_metrics']['api_usage']['total_cost'])

mean = statistics.mean(costs)
stdev = statistics.stdev(costs)
outliers = [c for c in costs if abs(c - mean) > 2*stdev]

print(f"Mean: ${mean:.2f}")
print(f"Std Dev: ${stdev:.2f}")
print(f"Outliers (>2σ): {outliers}")
EOF
```

**What to do:**
- **Don't remove outliers automatically** - they may be real
- **Investigate** - Check logs for cause
- **Document** - Note in experiment README
- **Report both** - With and without outliers if significant

---

## Analysis and Reporting

### Generate Complete Reports

**Standard workflow:**

```bash
# 1. Run experiment
python scripts/run_experiment.py my_exp

# 2. Reconcile (after 30+ min)
./runners/reconcile_usage.sh my_exp

# 3. Analyze
./runners/analyze_results.sh my_exp

# 4. Review report
cat experiments/my_exp/analysis/report.md

# 5. Archive/commit
git add experiments/my_exp/
git commit -m "Complete my_exp with analysis"
```

---

### Interpret Results Carefully

**Check these sections in report:**

1. **Sample Size**
   - Enough runs for statistical power?
   - Check power analysis section

2. **Confidence Intervals**
   - Wide CIs indicate high variance (need more runs)
   - Narrow CIs indicate consistent performance

3. **Verification Status**
   - All runs VERIFIED or RECONCILED?
   - Any ERROR or PENDING?

4. **Stopping Rule**
   - Was confidence threshold reached?
   - Or stopped at max runs?

5. **Outliers**
   - Any extreme values?
   - Investigated?

---

### Compare Experiments Properly

**Use statistical methods:**

See [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) for details.

**Quick checklist:**
- [ ] Both experiments use same task
- [ ] Both have ≥10 runs
- [ ] Both reconciled
- [ ] Confidence intervals checked
- [ ] Practical significance considered

---

## Reproducibility

### Document Everything

**Minimum documentation:**

```markdown
# experiments/my_exp/README.md

## Purpose
Test GPT-4o baseline performance on task X

## Configuration
- Model: gpt-4o
- Framework: baes
- Runs: 10
- Task timeout: 1800s

## Environment
- Date: 2025-10-20
- Python: 3.11.5
- Dependencies: requirements.txt (commit abc123)
- OS: Ubuntu 22.04

## Results
See analysis/report.md

## Reproducibility
Config hash: a1b2c3d4e5f6...
Random seed: 42
```

---

### Use Config Hashes

**Config hash ensures:**
- Exact same configuration
- Detects any changes
- Enables verification

**Check hash:**

```bash
cat experiments/my_exp/.meta/config.hash
```

**Verify reproducibility:**

```bash
# Re-run same experiment (new runs, same config)
python scripts/run_experiment.py my_exp

# Config hash prevents accidental changes
# If config edited, system will error
```

---

### Version Dependencies

**Document Python environment:**

```bash
# After creating experiment
pip freeze > experiments/my_exp/requirements_frozen.txt
git add experiments/my_exp/requirements_frozen.txt
git commit -m "Add frozen requirements for my_exp"
```

**Recreate environment later:**

```bash
# Exact same environment
pip install -r experiments/my_exp/requirements_frozen.txt
```

---

## Collaboration

### Share Experiments

**Share configuration (minimal):**

```bash
# Package just the config
tar -czf my_exp_config.tar.gz \
    experiments/my_exp/config.yaml \
    experiments/my_exp/README.md \
    experiments/my_exp/.meta/

# Share file
# Collaborator extracts and runs:
# python scripts/run_experiment.py my_exp
```

**Share complete results:**

```bash
# Package everything
tar -czf my_exp_complete.tar.gz \
    experiments/my_exp/ \
    --exclude='workspace'  # Exclude large files

# Share file
```

---

### Use Consistent Standards

**Team conventions:**

```markdown
# team_conventions.md

## Naming
- Baseline experiments: `baseline_{model}_{date}`
- Variants: `variant_{feature}_{model}_{date}`
- Ablations: `ablation_{removed_feature}_{model}_{date}`

## Sample Sizes
- Minimum: 10 runs
- Standard: 15 runs
- Publication: 30 runs

## Documentation
- Update README.md after completion
- Include hypothesis, results, decision
- Link to related experiments

## Git
- Commit config after creation
- Commit analysis after completion
- Use descriptive commit messages
```

---

## Performance Optimization

### Optimize API Usage

**Reduce costs:**

```bash
# 1. Test with smaller models first
python scripts/new_experiment.py --name test_gpt35 --model gpt-3.5-turbo ...

# 2. Use minimal runs for testing
--runs 3  # For initial tests

# 3. Increase only if needed
--runs 15  # For robust statistics

# 4. Monitor costs
./runners/reconcile_usage.sh my_exp
cat experiments/my_exp/analysis/report.md | grep "Total Cost"
```

---

### Parallel Framework Testing

**Efficient multi-framework testing:**

```bash
# Create single experiment
python scripts/new_experiment.py \
    --name multi_fw \
    --model gpt-4o \
    --frameworks baes chatdev ghspec \
    --runs 5

# Run frameworks in parallel
python scripts/run_experiment.py multi_fw baes &
python scripts/run_experiment.py multi_fw chatdev &
python scripts/run_experiment.py multi_fw ghspec &
wait

# Single analysis for all
./runners/analyze_results.sh multi_fw
```

---

### Timeout Tuning

**Set appropriate timeouts:**

```yaml
# config/experiment.yaml (before creating experiment)
timeouts:
  task_execution: 1800  # 30 minutes (default)
  analysis: 600  # 10 minutes (default)
```

**Guidelines:**
- **Too short:** Runs timeout prematurely
- **Too long:** Waste time on stuck runs
- **Recommended:** 1.5x expected time

**Find optimal timeout:**

```bash
# Run with default (1800s)
python scripts/new_experiment.py --name test_timeout_default --model gpt-4o --frameworks baes --runs 5
python scripts/run_experiment.py test_timeout_default

# Check actual times
cat experiments/test_timeout_default/runs/baes/*/metrics.json | \
    jq '.aggregate_metrics.performance_metrics.total_time'

# If all runs complete well under timeout, can reduce
# If some timeout, increase for next experiment
```

---

## Common Pitfalls

### Pitfall 1: Editing Config Mid-Experiment

**Problem:**
```bash
# Create and run
python scripts/new_experiment.py --name my_exp --model gpt-4o ...
python scripts/run_experiment.py my_exp  # Run 5 times

# ❌ Edit config
nano experiments/my_exp/config.yaml  # Change model

# ❌ Continue running - FAILS with hash mismatch
python scripts/run_experiment.py my_exp
```

**Solution:**
Create new experiment instead of editing.

---

### Pitfall 2: Not Reconciling Before Analysis

**Problem:**
```bash
python scripts/run_experiment.py my_exp
./runners/analyze_results.sh my_exp  # ❌ Using estimated costs

# Later realize costs were wrong
```

**Solution:**
Always reconcile first:

```bash
python scripts/run_experiment.py my_exp
# Wait 30+ minutes
./runners/reconcile_usage.sh my_exp  # ✅ Get actual costs
./runners/analyze_results.sh my_exp  # ✅ Accurate analysis
```

---

### Pitfall 3: Insufficient Sample Size

**Problem:**
```bash
# Run only 3 times
python scripts/new_experiment.py --name tiny_exp --model gpt-4o --frameworks baes --runs 3
python scripts/run_experiment.py tiny_exp
./runners/analyze_results.sh tiny_exp

# ⚠️ Report shows:
# "Warning: Sample size too small for reliable statistics"
# Wide confidence intervals
```

**Solution:**
Use ≥10 runs for meaningful statistics.

---

### Pitfall 4: Comparing Without Statistical Rigor

**Problem:**
```bash
# Experiment A: 85% success (1 run)
# Experiment B: 80% success (1 run)
# Conclusion: A is better ❌
```

**Solution:**
See [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) for proper comparison.

---

### Pitfall 5: Ignoring Variance

**Problem:**
```bash
# Both experiments: 85% mean success rate
# Experiment A: ±2% (consistent)
# Experiment B: ±15% (high variance)
# Treat as equivalent ❌
```

**Solution:**
Consider variance. Low variance = more reliable.

---

### Pitfall 6: Cherry-Picking Results

**Problem:**
- Run 20 experiments
- Report only the 2 that support hypothesis
- Ignore other 18

**Solution:**
- Pre-register hypotheses
- Report all experiments
- Use appropriate multiple testing corrections

---

## Quick Reference Checklist

### Before Creating Experiment

- [ ] Clear hypothesis defined
- [ ] Sample size determined (power analysis)
- [ ] Success criteria established
- [ ] Naming convention decided

### Creating Experiment

- [ ] Descriptive name used
- [ ] Appropriate model selected
- [ ] Sufficient runs planned (≥10)
- [ ] Timeouts configured if needed
- [ ] Random seed set for reproducibility

### Running Experiment

- [ ] Monitoring progress (tmux/screen if long)
- [ ] Checking logs for errors
- [ ] API quota sufficient
- [ ] Not editing config during run

### After Runs Complete

- [ ] Wait 30+ minutes
- [ ] Reconcile API usage
- [ ] Generate analysis
- [ ] Review report thoroughly
- [ ] Check for outliers

### Analysis and Documentation

- [ ] Confidence intervals checked
- [ ] Statistical power verified
- [ ] Practical significance considered
- [ ] Experiment README updated
- [ ] Results documented
- [ ] Decision recorded

### Reproducibility

- [ ] Config hash recorded
- [ ] Dependencies versioned
- [ ] Environment documented
- [ ] Committed to git
- [ ] Shareable with team

---

## Resources

- 📖 [Quick Start](QUICKSTART.md) - Get started in 5 minutes
- 📖 [Workflows](WORKFLOWS.md) - Common usage patterns
- 📊 [Comparison Guide](COMPARISON_GUIDE.md) - Statistical comparison
- 🏗️ [Architecture](architecture.md) - System design
- 📈 [Statistical Power Analysis](statistical_power_analysis.md) - Sample size calculations

---

## Summary

**Top 10 Best Practices:**

1. **Plan first** - Define hypothesis, sample size, success criteria
2. **Name systematically** - Use clear, consistent naming conventions
3. **Never edit config.yaml** - Create new experiment instead
4. **Start small** - Pilot → Small batch → Full experiment
5. **Use sufficient runs** - Minimum 10, recommended 15+
6. **Always reconcile** - Before final analysis (after 30+ min)
7. **Version control** - Commit configs and results to git
8. **Document thoroughly** - Update READMEs, record decisions
9. **Compare properly** - Use statistics, check CIs, consider variance
10. **Ensure reproducibility** - Config hash, frozen deps, documentation

**Remember:** The goal is **reliable, reproducible, statistically valid** research.

---

**Happy Experimenting!** 🎯

Questions? See [troubleshooting.md](troubleshooting.md) or open an issue.
