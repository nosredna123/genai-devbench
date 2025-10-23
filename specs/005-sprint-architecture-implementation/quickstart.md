# Quickstart: Sprint-Based Architecture

## Basic Sprint Execution

```bash
# Run experiment with multi-sprint scenario
python run_experiment.py --config config/experiment.yaml
```

## Accessing Sprint Artifacts

```bash
# View specific sprint
ls experiments/my_exp/runs/baes/abc123/sprint_002/

# View final sprint (via symlink)
cd experiments/my_exp/runs/baes/abc123/final/generated_artifacts/managed_system/
```

## Analyzing Sprint Evolution

```bash
# Diff between sprints
diff -r sprint_001/generated_artifacts sprint_002/generated_artifacts

# View cumulative metrics
cat summary/metrics_cumulative.json | jq
```

## Debugging Failed Sprints

```bash
# Check logs for failed sprint
cat sprint_002/logs/execution_sprint_002.log

# View last successful sprint
cd final/generated_artifacts/managed_system/
```
