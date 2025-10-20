# Experiment Comparison Guide

Learn how to statistically compare experiments and interpret results.

---

## Table of Contents

1. [Quick Comparison](#quick-comparison)
2. [Statistical Comparison](#statistical-comparison)
3. [Metric-by-Metric Analysis](#metric-by-metric-analysis)
4. [Visualizations](#visualizations)
5. [Interpretation Guidelines](#interpretation-guidelines)
6. [Common Patterns](#common-patterns)

---

## Quick Comparison

### Side-by-Side Report Comparison

**Scenario:** Compare two experiments quickly

```bash
# Generate both reports
./runners/analyze_results.sh baseline_gpt4o
./runners/analyze_results.sh variant_gpt4omini

# View side by side
diff -y experiments/baseline_gpt4o/analysis/report.md \
         experiments/variant_gpt4omini/analysis/report.md | less
```

**Look for:**
- Success Rate differences
- Cost per run differences
- API call counts
- Confidence intervals overlap

---

### Key Metrics Summary

```bash
# Extract key metrics from both experiments
for exp in baseline_gpt4o variant_gpt4omini; do
    echo "=== $exp ==="
    grep -A 3 "Success Rate" experiments/$exp/analysis/report.md
    grep -A 3 "Average Cost" experiments/$exp/analysis/report.md
    grep -A 3 "Total API Calls" experiments/$exp/analysis/report.md
    echo ""
done
```

**Example output:**
```
=== baseline_gpt4o ===
Success Rate: 85.0% ± 7.14%
95% CI: [70.72%, 99.28%]

Average Cost: $2.45 ± $0.32
95% CI: [$1.81, $3.09]

Total API Calls: 125 ± 15
95% CI: [95, 155]

=== variant_gpt4omini ===
Success Rate: 80.0% ± 8.00%
95% CI: [64.00%, 96.00%]

Average Cost: $0.85 ± $0.12
95% CI: [$0.61, $1.09]

Total API Calls: 130 ± 18
95% CI: [94, 166]
```

**Quick interpretation:**
- ✅ GPT-4o has 5% higher success rate (but CIs overlap)
- ✅ GPT-4o-mini is ~65% cheaper
- ✅ Similar API call counts

---

## Statistical Comparison

### Understanding Confidence Intervals

**Key concept:** If 95% confidence intervals (CI) overlap, differences may not be statistically significant.

**Example 1: Significant difference**
```
Experiment A: 85.0% ± 3.0%  [82.0%, 88.0%]
Experiment B: 70.0% ± 3.0%  [67.0%, 73.0%]
```
✅ **No overlap** → Significant difference (A > B)

**Example 2: Not significant**
```
Experiment A: 85.0% ± 7.0%  [78.0%, 92.0%]
Experiment B: 80.0% ± 8.0%  [72.0%, 88.0%]
```
⚠️ **Overlap** → Difference may be due to chance

---

### Statistical Power Analysis

**How many runs needed for reliable comparison?**

The system automatically calculates statistical power in the analysis report. Look for:

```markdown
## Statistical Power Analysis

Current sample size: 10 runs
Power to detect 10% difference: 0.45 (needs 20 runs for 0.80)
Power to detect 20% difference: 0.82 ✓
```

**Interpretation:**
- Power < 0.80: Need more runs
- Power ≥ 0.80: Sufficient for detecting meaningful differences

**See:** [statistical_power_analysis.md](statistical_power_analysis.md) for details

---

### Comparing Distributions

**Use when:** You want to compare entire distributions, not just means

```bash
# Extract all success rates
python3 << 'EOF'
import json
from pathlib import Path

def get_success_rates(exp_name):
    runs_dir = Path(f"experiments/{exp_name}/runs/baes")
    rates = []
    for run_dir in runs_dir.glob("*"):
        metrics_file = run_dir / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                data = json.load(f)
                rates.append(data['aggregate_metrics']['quality_metrics']['success_rate'])
    return rates

baseline = get_success_rates("baseline_gpt4o")
variant = get_success_rates("variant_gpt4omini")

print("Baseline:", baseline)
print("Variant:", variant)
print()
print("Baseline mean:", sum(baseline)/len(baseline))
print("Variant mean:", sum(variant)/len(variant))
EOF
```

**Statistical tests:**
- **t-test:** Compare means (assumes normal distribution)
- **Mann-Whitney U:** Compare distributions (non-parametric)
- **Bootstrap:** Estimate confidence intervals

The analysis report includes these automatically!

---

## Metric-by-Metric Analysis

### Quality Metrics Comparison

**Metrics to compare:**

| Metric | Description | Higher is better? |
|--------|-------------|-------------------|
| Success Rate | Percentage of passing tests | ✅ Yes |
| Code Quality | Correctness, completeness | ✅ Yes |
| Error Rate | Frequency of failures | ❌ No (lower is better) |

**Example analysis:**

```bash
# Compare quality metrics
for metric in success_rate code_quality_score error_rate; do
    echo "=== $metric ==="
    for exp in baseline_gpt4o variant_gpt4omini; do
        python3 << EOF
import json
from pathlib import Path

runs_dir = Path("experiments/$exp/runs/baes")
values = []
for run_dir in runs_dir.glob("*"):
    metrics_file = run_dir / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            data = json.load(f)
            values.append(data['aggregate_metrics']['quality_metrics']['$metric'])

print(f"$exp: {sum(values)/len(values):.2f} ± {(max(values)-min(values))/2:.2f}")
EOF
    done
    echo ""
done
```

---

### Performance Metrics Comparison

**Metrics to compare:**

| Metric | Description | Lower is better? |
|--------|-------------|------------------|
| Total Time | Wall-clock time | ✅ Yes |
| API Calls | Number of API requests | ✅ Yes (efficiency) |
| Tokens Used | Total tokens consumed | ✅ Yes (efficiency) |

**Example:**

```bash
# Compare performance
grep -h "Total Time" experiments/baseline_gpt4o/analysis/report.md \
                       experiments/variant_gpt4omini/analysis/report.md

grep -h "Total API Calls" experiments/baseline_gpt4o/analysis/report.md \
                           experiments/variant_gpt4omini/analysis/report.md
```

**Interpretation:**
- **Faster + accurate:** Clear winner
- **Faster but less accurate:** Trade-off decision
- **Slower but more accurate:** May be worth it for critical tasks

---

### Cost Metrics Comparison

**Key question:** What's the cost per successful run?

```python
# Calculate cost per success
import json
from pathlib import Path

def cost_per_success(exp_name):
    runs_dir = Path(f"experiments/{exp_name}/runs/baes")
    total_cost = 0
    successes = 0
    
    for run_dir in runs_dir.glob("*"):
        metrics_file = run_dir / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                data = json.load(f)
                total_cost += data['aggregate_metrics']['api_usage']['total_cost']
                if data['aggregate_metrics']['quality_metrics']['success_rate'] > 0.8:
                    successes += 1
    
    if successes == 0:
        return float('inf')
    return total_cost / successes

baseline_cps = cost_per_success("baseline_gpt4o")
variant_cps = cost_per_success("variant_gpt4omini")

print(f"Baseline cost per success: ${baseline_cps:.2f}")
print(f"Variant cost per success: ${variant_cps:.2f}")
print(f"Savings: {(1 - variant_cps/baseline_cps)*100:.1f}%")
```

---

## Visualizations

### Using Experiment Reports

Each experiment's `analysis/report.md` includes:

1. **Summary Statistics Table**
   - Mean, median, std dev for all metrics
   - Confidence intervals
   - Sample size

2. **Distribution Plots** (if generated)
   - Histograms
   - Box plots
   - Scatter plots

3. **Time Series** (if applicable)
   - Metrics over time
   - Trends

**Location:** `experiments/<name>/analysis/visualizations/`

---

### Creating Custom Visualizations

**Example: Success Rate Comparison Chart**

```python
import json
import matplotlib.pyplot as plt
from pathlib import Path

def get_metric(exp_name, metric_path):
    """Extract metric from all runs"""
    runs_dir = Path(f"experiments/{exp_name}/runs/baes")
    values = []
    for run_dir in runs_dir.glob("*"):
        metrics_file = run_dir / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                data = json.load(f)
                # Navigate metric_path: e.g., "aggregate_metrics.quality_metrics.success_rate"
                parts = metric_path.split('.')
                value = data
                for part in parts:
                    value = value[part]
                values.append(value)
    return values

# Compare experiments
experiments = ["baseline_gpt4o", "variant_gpt4omini"]
success_rates = [get_metric(exp, "aggregate_metrics.quality_metrics.success_rate") 
                 for exp in experiments]

# Create box plot
plt.figure(figsize=(10, 6))
plt.boxplot(success_rates, labels=experiments)
plt.ylabel("Success Rate")
plt.title("Success Rate Comparison")
plt.grid(True, alpha=0.3)
plt.savefig("comparison_success_rate.png")
plt.show()
```

---

## Interpretation Guidelines

### Decision Matrix

| Success Rate Δ | Cost Δ | Decision |
|---------------|--------|----------|
| +10%, CI no overlap | -50% | ✅ Clear winner (variant) |
| +5%, CI overlap | -50% | ⚠️ Need more runs or accept cost savings |
| +5%, CI no overlap | +10% | 💡 Trade-off: quality vs cost |
| -5%, CI overlap | -50% | 🤔 Depends on quality requirements |
| -10%, CI no overlap | -70% | ❌ Not worth the quality loss |

**Δ = Difference** (+ means variant is better/higher)

---

### Statistical Significance Checklist

Before concluding one experiment is better:

- ✅ Confidence intervals don't overlap (for key metrics)
- ✅ Statistical power ≥ 0.80 for expected effect size
- ✅ Sample size ≥ 10 runs per experiment
- ✅ Difference is practically significant (not just statistically)
- ✅ Results are reproducible (re-run a subset to verify)

**Warning signs:**
- ⚠️ High variance (large confidence intervals)
- ⚠️ Small sample size (< 10 runs)
- ⚠️ Outliers dominating results
- ⚠️ Inconsistent trends across metrics

---

### Practical Significance

**Statistical significance ≠ Practical significance**

**Example:**
- Experiment A: 85.0% success rate, $2.00/run
- Experiment B: 85.5% success rate, $3.00/run

**Analysis:**
- Difference: +0.5% success rate, +$1.00/run
- Statistical significance: Possibly yes (with enough runs)
- Practical significance: **No** - 0.5% improvement not worth 50% cost increase

**Consider:**
- Business impact of metric changes
- Cost constraints
- Time constraints
- Risk tolerance

---

## Common Patterns

### Pattern 1: Model Size Trade-off

**Typical finding:**

```
Large Model (GPT-4o):
- Success Rate: 90% ± 5%
- Cost: $3.50/run
- Time: 45 min/run

Small Model (GPT-4o-mini):
- Success Rate: 75% ± 8%
- Cost: $0.80/run
- Time: 30 min/run
```

**When to choose large model:**
- Critical applications
- Accuracy > cost
- Budget allows

**When to choose small model:**
- Rapid prototyping
- Cost-sensitive
- Acceptable quality threshold

---

### Pattern 2: Diminishing Returns

**Scenario:** Testing 4 model sizes

```
Model     Success Rate  Cost/run  Cost per 1% improvement
XL        92%          $5.00     -
Large     90%          $3.50     $0.75
Medium    85%          $1.50     $0.40
Small     75%          $0.80     $0.07
```

**Insight:** Medium model offers best value (highest success/$)

**Graph mentally:**
- X-axis: Cost
- Y-axis: Success Rate
- Look for "knee" in curve (inflection point)

---

### Pattern 3: Variance Matters

**Scenario A: Consistent performance**
```
Experiment A: 85% ± 2%  [83%, 87%]
```

**Scenario B: High variance**
```
Experiment B: 85% ± 15%  [70%, 100%]
```

**Even though means are equal:**
- A is more reliable (predictable outcomes)
- B is risky (some runs may fail completely)

**Prefer low variance** for production systems.

---

### Pattern 4: Multi-Objective Optimization

**Scenario:** Need to balance 3 metrics

| Experiment | Success Rate | Cost | Time |
|------------|--------------|------|------|
| A          | 90%         | $3   | 60m  |
| B          | 85%         | $1   | 30m  |
| C          | 95%         | $5   | 90m  |

**Pareto optimal:** A and C
- A: Good balance
- C: Best quality (if cost/time not critical)
- B: Not optimal (dominated by A)

**Use case dependent:**
- Research: Choose C (best quality)
- Production: Choose A (balanced)
- Prototyping: Choose B (fast & cheap)

---

## Advanced Techniques

### Bayesian Comparison

**When:** Small sample sizes, want to incorporate prior knowledge

```python
# Pseudo-code (requires pymc3 or similar)
import pymc3 as pm

with pm.Model() as model:
    # Priors
    mu_baseline = pm.Normal('mu_baseline', mu=0.8, sd=0.1)
    mu_variant = pm.Normal('mu_variant', mu=0.8, sd=0.1)
    
    # Likelihood
    baseline_obs = pm.Normal('baseline_obs', mu=mu_baseline, sd=0.05, 
                             observed=baseline_data)
    variant_obs = pm.Normal('variant_obs', mu=mu_variant, sd=0.05, 
                           observed=variant_data)
    
    # Difference
    diff = pm.Deterministic('diff', mu_variant - mu_baseline)
    
    # Sample
    trace = pm.sample(2000)

# Probability variant is better
prob_better = (trace['diff'] > 0).mean()
print(f"Probability variant > baseline: {prob_better:.2%}")
```

---

### Sequential Testing

**Use case:** Stop experiment early if clear winner emerges

**Concept:**
- Run in batches (e.g., 5 runs at a time)
- Check after each batch
- Stop if significant difference detected

**Caution:** Requires adjustment for multiple testing

---

### Meta-Analysis

**When:** Combining results from multiple experiment pairs

**Example:** 3 tasks × 2 models = 6 experiments

```python
# Calculate effect sizes for each task
effect_sizes = []
for task in tasks:
    baseline_mean = get_mean(f"{task}_baseline")
    variant_mean = get_mean(f"{task}_variant")
    pooled_std = calculate_pooled_std(f"{task}_baseline", f"{task}_variant")
    
    effect_size = (variant_mean - baseline_mean) / pooled_std
    effect_sizes.append(effect_size)

# Average effect size across tasks
meta_effect = sum(effect_sizes) / len(effect_sizes)
print(f"Average effect size: {meta_effect:.2f}")
```

---

## Checklist for Robust Comparisons

### Before Running

- [ ] Same task for both experiments
- [ ] Same evaluation criteria
- [ ] Same random seed (if comparing deterministic aspects)
- [ ] Sufficient runs planned (power analysis)
- [ ] Clear hypothesis about expected difference

### During Running

- [ ] Monitor for anomalies
- [ ] Check both experiments running similarly
- [ ] Note any external factors (API issues, timeouts)

### After Running

- [ ] Reconcile API usage for both
- [ ] Generate analysis reports
- [ ] Check confidence intervals
- [ ] Verify statistical power
- [ ] Look for outliers
- [ ] Consider practical significance
- [ ] Document findings

---

## Tools and Scripts

### Quick Comparison Script

```bash
#!/bin/bash
# compare_experiments.sh

EXP1=$1
EXP2=$2

echo "Comparing $EXP1 vs $EXP2"
echo ""

echo "Success Rates:"
grep "Success Rate" experiments/$EXP1/analysis/report.md
grep "Success Rate" experiments/$EXP2/analysis/report.md
echo ""

echo "Costs:"
grep "Average Cost" experiments/$EXP1/analysis/report.md
grep "Average Cost" experiments/$EXP2/analysis/report.md
echo ""

echo "API Calls:"
grep "Total API Calls" experiments/$EXP1/analysis/report.md
grep "Total API Calls" experiments/$EXP2/analysis/report.md
```

**Usage:**
```bash
chmod +x compare_experiments.sh
./compare_experiments.sh baseline_gpt4o variant_gpt4omini
```

---

## Real-World Example

### Complete Comparison Workflow

```bash
# 1. Create experiments
python scripts/new_experiment.py --name baseline_gpt4o --model gpt-4o --frameworks baes --runs 15
python scripts/new_experiment.py --name variant_gpt4omini --model gpt-4o-mini --frameworks baes --runs 15

# 2. Run experiments
python scripts/run_experiment.py baseline_gpt4o
python scripts/run_experiment.py variant_gpt4omini

# 3. Reconcile (wait 30+ minutes after completion)
./runners/reconcile_usage.sh baseline_gpt4o
./runners/reconcile_usage.sh variant_gpt4omini

# 4. Analyze
./runners/analyze_results.sh baseline_gpt4o
./runners/analyze_results.sh variant_gpt4omini

# 5. Compare
diff -y experiments/baseline_gpt4o/analysis/report.md \
         experiments/variant_gpt4omini/analysis/report.md | less

# 6. Extract key findings
echo "=== Baseline (GPT-4o) ==="
grep -A 2 "Success Rate\|Average Cost\|Total API Calls" \
    experiments/baseline_gpt4o/analysis/report.md

echo ""
echo "=== Variant (GPT-4o-mini) ==="
grep -A 2 "Success Rate\|Average Cost\|Total API Calls" \
    experiments/variant_gpt4omini/analysis/report.md

# 7. Document decision
cat > comparison_decision.md << 'EOF'
# Comparison Decision: GPT-4o vs GPT-4o-mini

## Results
- GPT-4o: 87% success, $2.80/run
- GPT-4o-mini: 82% success, $0.90/run

## Analysis
- 5% quality difference (CIs overlap)
- 68% cost reduction
- Similar API call counts

## Decision
Use GPT-4o-mini for:
- Non-critical tasks
- Prototyping
- Budget constraints

Use GPT-4o for:
- Production deployments
- Critical applications
- When 5% quality matters
EOF
```

---

## Summary

**Key takeaways:**

1. **Always use confidence intervals** - Don't just compare means
2. **Check statistical power** - Ensure enough runs for reliable comparison
3. **Consider practical significance** - 1% improvement may not matter
4. **Balance multiple objectives** - Quality, cost, time
5. **Document your reasoning** - Why you chose one over the other

**Next steps:**

- 📖 [Workflows Guide](WORKFLOWS.md) - How to run comparisons
- 🎯 [Best Practices](BEST_PRACTICES.md) - Comparison best practices
- 📊 [Statistical Power Analysis](statistical_power_analysis.md) - Detailed stats

---

**Happy Comparing!** 📊

Questions? See [troubleshooting.md](troubleshooting.md) or open an issue.
