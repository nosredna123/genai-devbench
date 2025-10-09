# Test Logs Directory

This directory contains test execution logs generated during development and testing.

## Log Files

### Smoke Test Logs
- `smoke_test_YYYYMMDD_HHMMSS.log` - Smoke test execution logs
- Created by: `./run_tests.sh smoke 2>&1 | tee logs/smoke_test_$(date +%Y%m%d_%H%M%S).log`

### Experiment Logs
- `experiment_output.log` - Full experiment run logs
- Created by: Experiment orchestrator during full runs

## Usage

When running tests manually and you want to save the output:

```bash
# Smoke test with logging
./run_tests.sh smoke 2>&1 | tee logs/smoke_test_$(date +%Y%m%d_%H%M%S).log

# Full integration test with logging  
./run_tests.sh full 2>&1 | tee logs/integration_$(date +%Y%m%d_%H%M%S).log

# Unit tests with logging
./run_tests.sh unit 2>&1 | tee logs/unit_$(date +%Y%m%d_%H%M%S).log
```

## Cleanup

Log files are automatically ignored by `.gitignore` and should not be committed to version control.

To clean up old logs:

```bash
# Remove logs older than 7 days
find logs/ -name "*.log" -mtime +7 -delete

# Remove all logs
rm logs/*.log
```

## Best Practices

1. **Don't commit logs**: All `*.log` files are in `.gitignore`
2. **Use timestamps**: Include date/time in log filenames for easy identification
3. **Regular cleanup**: Remove old logs to save disk space
4. **CI/CD logs**: Consider using test artifacts in CI/CD instead of local logs
