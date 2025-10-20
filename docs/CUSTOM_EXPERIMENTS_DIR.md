# Custom Experiments Directory Support

## Overview

The framework now supports custom base directories for storing experiment data. By default, all experiments are stored in `./experiments/`, but you can specify a different location using the `--experiments-dir` flag.

## Use Cases

- **External Storage**: Store experiments on a different drive or network location
- **Organizational Separation**: Separate production experiments from test experiments
- **Shared Environments**: Multiple users can work with different experiment directories
- **Archive Management**: Move old experiments to archive directories while keeping active ones accessible

## Default Behavior

When no custom directory is specified, the framework uses the default pattern:

```
project_root/
├── experiments/
│   ├── experiment1/
│   │   ├── config.yaml
│   │   ├── runs/
│   │   ├── analysis/
│   │   └── .meta/
│   └── experiment2/
│       ├── config.yaml
│       ├── runs/
│       ├── analysis/
│       └── .meta/
```

## Custom Directory Usage

### Creating New Experiments

```bash
# Default location (./experiments/)
python scripts/new_experiment.py --name test1 --model gpt-4o --frameworks baes --runs 10

# Custom location
python scripts/new_experiment.py --name test1 --model gpt-4o --frameworks baes --runs 10 \
    --experiments-dir /data/my-experiments

# This creates:
# /data/my-experiments/test1/config.yaml
# /data/my-experiments/test1/runs/
# etc.
```

### Running Experiments

```bash
# Default location
python scripts/run_experiment.py test1

# Custom location
python scripts/run_experiment.py test1 --experiments-dir /data/my-experiments
```

### Generating Analysis

```bash
# Default location
python scripts/generate_analysis.py test1

# Custom location
python scripts/generate_analysis.py test1 --experiments-dir /data/my-experiments
```

## Implementation Details

### ExperimentPaths Class

The `ExperimentPaths` class now accepts an `experiments_base_dir` parameter:

```python
from pathlib import Path
from src.utils.experiment_paths import ExperimentPaths

# Default usage
paths = ExperimentPaths("my_experiment")

# Custom base directory
paths = ExperimentPaths(
    "my_experiment",
    experiments_base_dir=Path("/data/my-experiments")
)
```

### Script Support

All main scripts now support the `--experiments-dir` flag:

- `scripts/new_experiment.py`
- `scripts/run_experiment.py`
- `scripts/generate_analysis.py`

## Directory Structure Validation

The framework validates that:

1. The custom directory exists or can be created
2. Experiment subdirectories follow the standard structure
3. Required files (config.yaml) are present in the expected locations

## Backward Compatibility

This feature is fully backward compatible. All existing scripts and code will continue to work without modification, using the default `./experiments/` directory.

## Environment Variables (Future Enhancement)

Consider setting an environment variable for convenience:

```bash
# In your shell profile
export GENAI_EXPERIMENTS_DIR=/data/my-experiments

# Then use in scripts (requires implementation)
python scripts/run_experiment.py test1
```

*Note: Environment variable support is not yet implemented but can be added if needed.*

## Best Practices

1. **Consistent Path Usage**: Always use the same `--experiments-dir` flag for all operations on a given experiment
2. **Absolute Paths**: Use absolute paths for clarity, especially in scripts and CI/CD pipelines
3. **Documentation**: Document your custom paths in your project README or setup documentation
4. **Backup Strategy**: Ensure your backup strategy accounts for custom experiment locations
5. **Access Permissions**: Verify that the process has read/write permissions for custom directories

## Examples

### Scenario 1: External SSD for Performance

```bash
# Create experiments on fast SSD
python scripts/new_experiment.py --name speed_test --model gpt-4o \
    --frameworks baes,chatdev,ghspec --runs 50 \
    --experiments-dir /mnt/ssd/experiments

# Run experiment
python scripts/run_experiment.py speed_test --experiments-dir /mnt/ssd/experiments

# Analyze results
python scripts/generate_analysis.py speed_test --experiments-dir /mnt/ssd/experiments
```

### Scenario 2: Separate Test and Production

```bash
# Test experiments
python scripts/new_experiment.py --name test_run --model gpt-4o-mini \
    --frameworks baes --runs 2 \
    --experiments-dir ./test_experiments

# Production experiments (default location)
python scripts/new_experiment.py --name production_run --model gpt-4o \
    --frameworks baes,chatdev,ghspec --runs 50
```

### Scenario 3: Network Storage

```bash
# Store experiments on network share
python scripts/new_experiment.py --name shared_exp --model gpt-4o \
    --frameworks baes --runs 20 \
    --experiments-dir /mnt/network/shared/experiments

# Team members can access the same location
python scripts/run_experiment.py shared_exp --experiments-dir /mnt/network/shared/experiments
```

## Troubleshooting

### Error: Experiment not found

Make sure you're using the same `--experiments-dir` path that was used when creating the experiment.

```bash
# Wrong: Looking in default location
python scripts/run_experiment.py my_exp

# Correct: Specify custom location
python scripts/run_experiment.py my_exp --experiments-dir /data/my-experiments
```

### Error: Permission denied

Ensure the process has appropriate permissions:

```bash
# Check permissions
ls -la /data/my-experiments

# Fix if needed
chmod -R u+rwx /data/my-experiments
```

### Error: Directory not found

Create the base directory before running scripts:

```bash
mkdir -p /data/my-experiments
```

## Related Documentation

- [Experiment Path Management](./experiment_paths.md)
- [Multi-Experiment Support](./MULTI_EXPERIMENT_CLEAN_DESIGN.md)
- [Quickstart Guide](./quickstart.md)
