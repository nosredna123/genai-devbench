# Troubleshooting Guide

Common issues and solutions for the BAEs Experiment Framework.

## Quick Diagnosis

Use this checklist to quickly identify issues:

```bash
# 1. Check Python version
python3 --version  # Should be 3.11+

# 2. Check dependencies
pip list | grep -E "PyYAML|requests|pytest|matplotlib"

# 3. Check configuration
python3 -m src.orchestrator --help

# 4. Check disk space
df -h .  # Need ~10 GB free

# 5. Check API connectivity
curl https://api.openai.com/v1/models -H "Authorization: Bearer $BAES_API_KEY"

# 6. Check logs
tail -50 runs/*/*/event_log.jsonl
```

---

## Common Issues

### 1. Timeout Errors

**Symptom:**
```
ERROR: Step 3 timed out after 3600 seconds
StepTimeoutError: Framework execution exceeded timeout
```

**Causes:**
- Framework taking too long to generate code
- Network latency to LLM APIs
- Complex prompts requiring many iterations
- Framework stuck in infinite loop

**Solutions:**

**A. Increase Timeout**

Edit `config/experiment.yaml`:

```yaml
timeout_seconds: 7200  # 2 hours instead of 1 hour
```

**B. Reduce Prompt Complexity**

Simplify prompts in `config/prompts/step_*.txt`:
- Remove detailed specifications
- Focus on core functionality
- Split complex steps into smaller increments

**C. Check Framework Logs**

```bash
# View framework execution logs
cat runs/<framework>/<run-id>/framework.log

# Look for:
# - Repeated API calls (stuck in loop)
# - Error messages (unhandled exceptions)
# - Long pauses (waiting for user input)
```

**D. Monitor Progress**

```bash
# Watch event log in real-time
tail -f runs/<framework>/<run-id>/event_log.jsonl
```

---

### 2. API Quota/Rate Limit Errors

**Symptom:**
```
ERROR: OpenAI API error 429: Rate limit exceeded
MCI metric shows >5 interruptions
```

**Causes:**
- Free tier rate limits (3 RPM, 200 RPD)
- Tier 1 limits (500 RPM, 200K TPD)
- Concurrent requests from multiple runs

**Solutions:**

**A. Upgrade API Tier**

Visit https://platform.openai.com/account/billing and upgrade to:
- **Tier 2**: 5,000 RPM, 450K TPD
- **Tier 3**: 10,000 RPM, 1M TPD

**B. Add Retry Delays**

Edit `config/experiment.yaml`:

```yaml
retry_attempts: 5
retry_delay: 120  # Wait 2 minutes between retries
```

**C. Reduce Parallel Runs**

```yaml
max_parallel_runs: 1  # Run frameworks sequentially
```

**D. Use Exponential Backoff**

The framework automatically implements exponential backoff, but you can tune it:

```python
# In src/utils/api_client.py, the retry logic uses:
# delay = retry_delay * (2 ** attempt)
# Increase base retry_delay in config to slow down retries
```

**E. Monitor Quota**

```bash
# Check current usage
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $BAES_API_KEY" | jq .
```

---

### 3. Disk Space Exhausted

**Symptom:**
```
ERROR: No space left on device
OSError: [Errno 28] No space left on device
```

**Causes:**
- Many run directories consuming space (~500 MB each)
- Large framework repositories
- Archive files (tar.gz) accumulating

**Solutions:**

**A. Check Disk Usage**

```bash
# Check available space
df -h .

# Find largest directories
du -sh runs/*/* | sort -rh | head -20
```

**B. Clean Old Runs**

```bash
# Remove specific framework runs
rm -rf runs/baes/baes-20251001-*

# Remove all runs older than 7 days
find runs -type d -mtime +7 -exec rm -rf {} +

# Remove only archives (keep metrics)
find runs -name "archive.tar.gz" -delete
```

**C. Enable Cleanup**

Edit run script to auto-cleanup:

```bash
# In runners/run_experiment.sh, add:
export AUTO_CLEANUP=true  # Deletes workspace after archiving
```

**D. Use External Storage**

Move runs directory to larger disk:

```bash
# Create symlink to external drive
mv runs /mnt/external/baes_runs
ln -s /mnt/external/baes_runs runs
```

**E. Compress Archives Better**

```bash
# Use xz compression instead of gz
tar -cJf archive.tar.xz workspace/  # Smaller but slower
```

---

### 4. Framework Clone/Checkout Failures

**Symptom:**
```
ERROR: Failed to clone repository
GitError: Repository not found or permission denied
```

**Causes:**
- Invalid repository URL
- Network connectivity issues
- Private repository without credentials
- Commit hash doesn't exist

**Solutions:**

**A. Verify Repository URL**

```bash
# Test manual clone
git clone https://github.com/org/baes-framework

# Check URL in config
grep repo_url config/experiment.yaml
```

**B. Check Commit Hash**

```yaml
# In config/experiment.yaml
frameworks:
  baes:
    repo_url: https://github.com/org/baes-framework
    commit_hash: abc123...  # Ensure this exists in repo
```

**Verify commit exists:**

```bash
git ls-remote https://github.com/org/baes-framework | grep abc123
```

**C. Use HTTPS with Token (Private Repos)**

```bash
# Set GitHub token in .env
GITHUB_TOKEN=ghp_your_token_here

# Update URL in config
repo_url: https://${GITHUB_TOKEN}@github.com/org/private-repo
```

**D. Check Network Connectivity**

```bash
# Test Git access
git ls-remote https://github.com/org/baes-framework

# Check DNS resolution
nslookup github.com

# Test HTTPS
curl -I https://github.com
```

**E. Use Local Repository**

For development/testing:

```yaml
frameworks:
  baes:
    repo_url: file:///home/user/local-baes-repo
    commit_hash: HEAD  # Use current HEAD
```

---

### 5. Framework Crashes

**Symptom:**
```
ERROR: Framework process exited with code 1
RTE metric shows >0.2 error rate
```

**Causes:**
- Framework bugs
- Incompatible dependencies
- Missing environment variables
- Out of memory

**Solutions:**

**A. Check Framework Logs**

```bash
# View stderr
cat runs/<framework>/<run-id>/framework_stderr.log

# View stdout
cat runs/<framework>/<run-id>/framework_stdout.log

# Look for:
# - ImportError (missing dependencies)
# - MemoryError (out of RAM)
# - UnboundLocalError (framework bugs)
```

**B. Verify Framework Dependencies**

```bash
# Check framework's requirements.txt
cat workspace/requirements.txt

# Install in isolated venv
python3 -m venv test_env
source test_env/bin/activate
pip install -r workspace/requirements.txt
```

**C. Increase Memory Limit**

```bash
# For Docker environments
docker run -m 8g ...  # 8 GB memory limit

# For systemd services
MemoryLimit=8G
```

**D. Check Environment Variables**

```bash
# Ensure all required vars set
env | grep -E "BAES|CHATDEV|GHSPEC"

# Source .env file
set -a; source .env; set +a
```

**E. Test Framework Manually**

```bash
# Run framework outside orchestrator
cd workspace
python -m baes.cli --prompt "Create a simple app"
```

---

### 6. Validation Failures

**Symptom:**
```
ERROR: CRUD validation failed
CRUDe metric shows <6 (incomplete)
```

**Causes:**
- Framework didn't generate expected endpoints
- Database migrations failed
- Incorrect test assumptions

**Solutions:**

**A. Check Validation Logs**

```bash
# View validation results
cat runs/<framework>/<run-id>/validation_results.json

# Example output:
{
  "step_3": {
    "crud_coverage": 8,  # Missing 4 operations
    "failed_tests": ["DELETE /tasks/:id", "DELETE /users/:id"]
  }
}
```

**B. Inspect Generated Code**

```bash
# Extract archive
tar -xzf runs/<framework>/<run-id>/archive.tar.gz

# Check routes/endpoints
grep -r "DELETE" workspace/src/routes/

# Check database models
cat workspace/src/models/*.py
```

**C. Relax Validation Criteria**

Edit `src/orchestrator/validator.py`:

```python
# Change minimum CRUD coverage
MIN_CRUD_COVERAGE = 6  # Accept 50% coverage instead of 100%
```

**D. Update Prompts**

Make CRUD requirements explicit in prompts:

```
Step 3: Implement DELETE operations
- DELETE /tasks/:id - Remove a task
- DELETE /users/:id - Remove a user
- DELETE /projects/:id - Remove a project

Ensure proper cascade deletion and foreign key handling.
```

---

### 7. HITL Reproducibility Issues

**Symptom:**
```
ERROR: HITL SHA-1 mismatch
Expected: a1b2c3d4e5f6...
Got: z9y8x7w6v5u4...
```

**Causes:**
- HITL response changed between runs
- Non-deterministic HITL generation
- Different HITL file loaded

**Solutions:**

**A. Use Fixed HITL Responses**

```bash
# Verify HITL file contents
cat config/hitl/expanded_spec.txt

# Check SHA-1 hash
sha1sum config/hitl/expanded_spec.txt
```

**B. Lock HITL Responses**

Edit `config/experiment.yaml`:

```yaml
hitl:
  use_deterministic: true
  response_file: config/hitl/expanded_spec.txt
  expected_sha1: a1b2c3d4e5f6...  # Lock to specific hash
```

**C. Verify Encoding**

```bash
# Check file encoding (must be UTF-8)
file -i config/hitl/expanded_spec.txt

# Convert if needed
iconv -f ISO-8859-1 -t UTF-8 expanded_spec.txt > expanded_spec_utf8.txt
```

---

### 8. Statistical Analysis Errors

**Symptom:**
```
ERROR: Not enough runs for convergence check
ValueError: Insufficient data for bootstrap CI
```

**Causes:**
- Fewer than 5 runs completed
- Missing metrics in some runs
- All values identical (zero variance)

**Solutions:**

**A. Check Run Count**

```bash
# Count completed runs per framework
ls -d runs/baes/* | wc -l

# Should be ≥5 for statistical analysis
```

**B. Complete More Runs**

```bash
# Run until convergence
./runners/run_experiment.sh --multi baes chatdev ghspec
```

**C. Check for Missing Metrics**

```bash
# Find runs with incomplete metrics
for dir in runs/*/*; do
  if ! jq -e '.AUTR' "$dir/metrics.json" &>/dev/null; then
    echo "Missing AUTR in $dir"
  fi
done
```

**D. Handle Zero Variance**

If all values identical:

```python
# In src/analysis/stopping_rule.py
# Bootstrap CI will return (mean, mean, mean) - this is expected
# Convergence check will still pass
```

---

### 9. Visualization Generation Failures

**Symptom:**
```
ERROR: Failed to generate radar chart
ModuleNotFoundError: No module named 'matplotlib'
```

**Causes:**
- matplotlib not installed
- NumPy version incompatibility
- Display not available (headless server)

**Solutions:**

**A. Install Dependencies**

```bash
pip install matplotlib==3.8.0 numpy
```

**B. Use Headless Backend**

For servers without display:

```python
# In src/analysis/visualizations.py, add at top:
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt
```

**C. Check Permissions**

```bash
# Ensure output directory writable
mkdir -p analysis_output
chmod 755 analysis_output
```

**D. Manual Generation**

```bash
# Generate charts individually
python3 -c "
from src.analysis.visualizations import radar_chart
radar_chart(data, 'output.svg')
"
```

---

### 10. Permission Errors

**Symptom:**
```
ERROR: Permission denied
PermissionError: [Errno 13] Permission denied: 'runs/baes/...'
```

**Causes:**
- Running as wrong user
- Directory ownership issues
- Filesystem permissions

**Solutions:**

**A. Check Ownership**

```bash
ls -la runs/
# Ensure you own the directories
```

**B. Fix Permissions**

```bash
# Recursive permission fix
chmod -R u+rwX runs/
chown -R $USER:$USER runs/
```

**C. Run with Correct User**

```bash
# Don't run as root
# Don't use sudo unless necessary
./runners/run_experiment.sh
```

**D. Check SELinux/AppArmor**

```bash
# Temporarily disable SELinux (CentOS/RHEL)
sudo setenforce 0

# Check AppArmor (Ubuntu)
sudo aa-status
```

---

## Advanced Troubleshooting

### Enable Debug Logging

Edit `src/utils/logger.py`:

```python
# Change log level
logging.basicConfig(level=logging.DEBUG)  # Was INFO
```

### Capture Framework Output

```bash
# Run with verbose output
./runners/run_experiment.sh baes 2>&1 | tee experiment.log
```

### Isolate Issues

Test components individually:

```bash
# Test adapter only
python3 -c "
from src.adapters.baes_adapter import BAeSAdapter
adapter = BAeSAdapter(config)
adapter.setup('test_workspace')
"

# Test metrics collection only
python3 -c "
from src.orchestrator.metrics_collector import MetricsCollector
collector = MetricsCollector('test_workspace')
metrics = collector.collect_metrics(...)
"
```

### Use Docker for Isolation

```bash
# Run in container to isolate environment issues
docker run -it python:3.11 bash
cd /app
pip install -r requirements.txt
./runners/run_experiment.sh
```

---

## Getting Help

If issues persist:

1. **Check Logs**: `runs/<framework>/<run-id>/event_log.jsonl`
2. **Search Issues**: [GitHub Issues](https://github.com/gesad-lab/baes_experiment/issues)
3. **Open New Issue**: Include logs, config, and error messages
4. **Community**: Discussions tab for questions

### Issue Template

When reporting issues, include:

```markdown
**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.5
- Framework: baes v1.0.0

**Configuration:**
```yaml
# Paste relevant config
```

**Error:**
```
# Paste error message and stack trace
```

**Logs:**
```json
# Paste last 10 lines of event_log.jsonl
```

**Steps to Reproduce:**
1. Run `./runners/run_experiment.sh baes`
2. Wait for step 3
3. Observe timeout error
```

---

## Preventive Measures

### Pre-Flight Checklist

Before starting experiments:

- [ ] Python 3.11+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] API keys configured in `.env`
- [ ] Sufficient disk space (>10 GB free)
- [ ] Network connectivity verified
- [ ] Framework repositories accessible
- [ ] Configuration validated (`python3 -m src.orchestrator --help`)

### Monitoring During Execution

```bash
# Monitor disk space
watch -n 60 df -h .

# Monitor API usage
watch -n 300 'curl -s https://api.openai.com/v1/usage -H "Authorization: Bearer $BAES_API_KEY" | jq .'

# Monitor event log
tail -f runs/<framework>/<run-id>/event_log.jsonl
```

### Post-Execution Validation

```bash
# Verify metrics collected
jq . runs/<framework>/<run-id>/metrics.json

# Check archive integrity
sha256sum -c runs/<framework>/<run-id>/checksum.sha256

# Verify reproducibility
python tests/integration/test_reproducibility.py runs/run1 runs/run2
```

---

## Further Reading

- **[Quickstart Guide](./quickstart.md)**: Basic usage patterns
- **[Architecture Guide](./architecture.md)**: System design and components
- **[Configuration Guide](./configuration.md)**: Advanced configuration options
