# Quick Start Guide

Get started with the BAEs multi-experiment system in 5 minutes!

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.11+ installed
- ✅ Git repository cloned
- ✅ Virtual environment set up: `python -m venv .venv && source .venv/bin/activate`
- ✅ Dependencies installed: `pip install -r requirements.txt`
- ✅ `.env` file configured with OpenAI API keys

Need help? See [Full Setup Guide](../README.md#installation)

---

## Your First Experiment (5 Minutes)

###  Step 1: Create an Experiment (30 seconds)

```bash
python scripts/new_experiment.py \\
    --name my_first_experiment \\
    --model gpt-4o \\
    --frameworks baes \\
    --runs 10
```

**What this does:**
- Creates `experiments/my_first_experiment/` directory
- Generates configuration file
- Sets up directory structure
- Registers experiment in global registry

**Expected output:**
```
Experiment 'my_first_experiment' created successfully!

Directory: experiments/my_first_experiment/
Config hash: a1b2c3d4e5f6...
```

---

### 2️⃣ Step 2: Run the Experiment (varies)

```bash
python scripts/run_experiment.py my_first_experiment
```

**What happens:**
- Runs BAEs framework 10 times
- Each run is isolated in its own workspace
- Metrics collected automatically
- Progress displayed in terminal

**Duration:** Depends on task complexity (typically 5-30 minutes per run)

**Expected output:**
```
Starting run 1/10 for framework: baes
✓ Run completed: baes_run_20251020_140523
...
✓ All runs completed!
```

**Tip:** Start with `--runs 1` to test quickly, then increase for real experiments.

---

### 3️⃣ Step 3: Analyze Results (30 seconds)

```bash
./runners/analyze_results.sh my_first_experiment
```

**What this does:**
- Generates statistical analysis
- Creates visualizations
- Produces comprehensive report
- Saves to `experiments/my_first_experiment/analysis/`

**Expected output:**
```
Loading run data...
✓ Loaded 10 VERIFIED runs
Generating analysis...
✓ Report saved to: experiments/my_first_experiment/analysis/report.md
```

---

### 4️⃣ Step 4: View Results

```bash
cat experiments/my_first_experiment/analysis/report.md
```

Or open in your favorite Markdown viewer!

**Report includes:**
- Summary statistics
- Confidence intervals
- Statistical tests
- Visualizations
- Recommendations

---

## What You Just Did 🎉

Congratulations! You've just:

✅ Created your first experiment  
✅ Run it with proper isolation  
✅ Generated statistical analysis  
✅ Produced a comprehensive report  

---

## Directory Structure Created

```
experiments/my_first_experiment/
├── config.yaml              # Experiment configuration
├── README.md                # Auto-generated documentation
├── runs/                    # Run outputs
│   ├── manifest.json        # Run tracking
│   └── baes/               # Framework-specific runs
│       └── baes_run_*/     # Individual run directories
│           ├── metrics.json
│           ├── metadata.json
│           └── workspace/  # Isolated workspace
├── analysis/               # Analysis outputs ⭐
│   ├── report.md          # Statistical report
│   └── visualizations/    # Charts and graphs
└── .meta/                  # Metadata
    └── config.hash        # Config validation
```

---

## Next Steps

### Learn More Workflows

See [WORKFLOWS.md](WORKFLOWS.md) for:
- Running multiple frameworks
- Comparing experiments
- Advanced configurations
- Troubleshooting

### Compare Two Experiments

```bash
# Create variant experiment
python scripts/new_experiment.py \\
    --name variant1 \\
    --model gpt-4o-mini \\
    --frameworks baes \\
    --runs 10

# Run it
python scripts/run_experiment.py variant1

# Analyze both
./runners/analyze_results.sh my_first_experiment
./runners/analyze_results.sh variant1

# Compare
diff experiments/my_first_experiment/analysis/report.md \\
     experiments/variant1/analysis/report.md
```

See [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) for detailed comparison techniques.

### Best Practices

- **Naming:** Use descriptive names (e.g., `baseline_gpt4o`, `variant_gpt4mini`)
- **Runs:** Start with 5-10 runs, increase if needed for statistical power
- **Versioning:** Commit experiments to git for reproducibility
- **Documentation:** Update experiment README.md with findings

See [BEST_PRACTICES.md](BEST_PRACTICES.md) for more tips.

---

## Common Commands Cheat Sheet

```bash
# Create experiment
python scripts/new_experiment.py --name <name> --model <model> --frameworks <fw> --runs <n>

# Run experiment
python scripts/run_experiment.py <experiment_name> [framework]

# Analyze results
./runners/analyze_results.sh <experiment_name>

# Reconcile usage (after 30+ minutes)
./runners/reconcile_usage.sh <experiment_name> --list
./runners/reconcile_usage.sh <experiment_name>

# List all experiments
python -c "from src.utils.experiment_registry import get_registry; \\
    r = get_registry(); \\
    [print(f'{name}: {info[\"status\"]} ({info[\"total_runs\"]}/{info[\"max_runs\"]})') \\
     for name, info in r.list_experiments().items()]"
```

---

## Troubleshooting

### "Experiment not found"

Make sure you're using the exact experiment name:
```bash
ls experiments/  # List all experiments
```

### "No runs found"

Runs are only counted after they complete successfully:
```bash
python scripts/run_experiment.py <experiment_name>  # Run it first
```

### "Config hash mismatch"

Don't edit `config.yaml` after creating the experiment. Create a new experiment instead:
```bash
python scripts/new_experiment.py --name <new_name> ...
```

### Need more help?

- See [WORKFLOWS.md](WORKFLOWS.md) for detailed examples
- See [troubleshooting.md](troubleshooting.md) for common issues
- Check logs in experiment directory

---

## Key Concepts

### Experiment
A named configuration for running comparative tests. Each experiment:
- Has its own `config.yaml`
- Tracks runs independently
- Produces separate analysis
- Enables easy comparison

### Run
A single execution of a framework. Each run:
- Uses isolated workspace
- Generates metrics
- Tracked in manifest
- Reproducible via config hash

### Framework
An AI software development system (baes, chatdev, ghspec) being evaluated.

### Stopping Rule
Automatic stopping when statistical confidence is achieved or max runs reached.

---

## What Makes This System Powerful?

✅ **Isolation:** Each experiment is completely independent  
✅ **Reproducibility:** Config hash prevents mid-experiment changes  
✅ **Organization:** All outputs grouped by experiment  
✅ **Comparison:** Easy to compare multiple configurations  
✅ **Tracking:** Global registry knows all experiments  
✅ **Statistics:** Built-in statistical analysis with confidence intervals  

---

## Ready for More?

- 📖 [Complete Workflows](WORKFLOWS.md) - Detailed usage patterns
- 📊 [Comparison Guide](COMPARISON_GUIDE.md) - How to compare experiments
- 🎯 [Best Practices](BEST_PRACTICES.md) - Tips and recommendations
- 🏗️ [Architecture](architecture.md) - System design details

---

**Happy Experimenting!** 🚀

Questions? Check the [README](../README.md) or open an issue.
