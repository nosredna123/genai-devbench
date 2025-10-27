# Quickstart Guide

Get up and running with the BAEs Experiment Framework in minutes.

## Prerequisites

### Required Software

- **Python 3.11+**: Core runtime environment
- **Git**: Version control for framework repositories
- **Bash**: Shell scripting support (Linux/macOS)

### Optional Software

- **Docker**: For containerized framework isolation (recommended)
- **Virtual Environment**: `venv` or `conda` for Python dependency isolation

### API Keys

You'll need API keys for the frameworks you want to test:

- **BAEs Framework**: OpenAI API key
- **ChatDev Framework**: OpenAI API key
- **GitHub Spec-kit**: GitHub token (optional, for rate limiting)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/gesad-lab/genai-devbench.git
cd genai-devbench
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```bash
BAES_API_KEY=sk-your-openai-key-here
CHATDEV_API_KEY=sk-your-openai-key-here
GHSPEC_API_KEY=ghp_your-github-token-here  # Optional
```

### 5. Verify Configuration

Check that your configuration is valid:

```bash
python3 -m src.orchestrator --help
```

You should see the CLI usage information.

## First Run

### Run a Single Framework Test

Execute a single run with the BAEs framework:

```bash
./runners/run_experiment.sh baes
```

**What happens:**
1. Creates an isolated workspace in `runs/baes/<run-id>/`
2. Clones the BAEs framework repository
3. Executes all 6 CRUD evolution steps
4. Validates outputs at each step
5. Collects 16 metrics (AUTR, Q*, TOK_IN, etc.)
6. Archives results with SHA-256 hash
7. Logs all events to `event_log.jsonl`

**Expected duration:** 15-30 minutes (depending on framework and API latency)

### View Results

After the run completes, check the outputs:

```bash
# View metrics
cat runs/baes/<run-id>/metrics.json

# View event log
cat runs/baes/<run-id>/event_log.jsonl

# View HITL events (for reproducibility)
cat runs/baes/<run-id>/hitl_events.jsonl

# View archive
ls -lh runs/baes/<run-id>/archive.tar.gz
```

### Run Multi-Framework Comparison

To compare multiple frameworks until convergence:

```bash
./runners/run_experiment.sh --multi baes chatdev ghspec
```

**What happens:**
1. Runs all 3 frameworks in parallel (default: 5 runs minimum)
2. Checks convergence after each run using bootstrap CI
3. Stops when 95% CI half-width < 10% of mean
4. Maximum 25 runs per framework
5. Results saved in `runs/<framework>/<run-id>/`

**Expected duration:** 1-3 hours (depending on convergence rate)

## Analyze Results

After collecting run data, generate analysis and visualizations:

```bash
./runners/analyze_results.sh ./analysis_output
```

**Outputs:**
- `radar_chart.svg`: Multi-framework comparison across 6 metrics
- `pareto_plot.svg`: Quality vs cost trade-off visualization
- `timeline_chart.svg`: CRUD coverage evolution over steps
- `report.md`: Comprehensive statistical report with:
  - Aggregate statistics (mean, median, 95% CI)
  - Kruskal-Wallis tests
  - Pairwise comparisons with Cliff's delta
  - Outlier detection

**View the report:**

```bash
cat analysis_output/report.md
```

**View visualizations:**

Open the SVG files in a web browser or image viewer:

```bash
firefox analysis_output/radar_chart.svg  # Or your preferred browser
```

## Advanced Configuration

### GHSpec Template Configuration (T046)

The GHSpec adapter supports two template modes for reproducibility and upstream tracking:

#### Static Templates (Default)

Use curated, version-controlled templates from `docs/ghspec/prompts/`:

```yaml
# config_sets/default/experiment.yaml
framework_config:
  template_source: static  # Default mode
```

**Pros:**
- **Reproducible**: Templates versioned with experiment code
- **Stable**: Changes require explicit version control
- **Documented**: Templates include inline documentation

**Use when:** Running production experiments, comparing across time periods

#### Dynamic Templates

Use templates directly from cloned GHSpec-Kit repository at `frameworks/ghspec/`:

```yaml
# config_sets/default/experiment.yaml
framework_config:
  template_source: dynamic  # Upstream tracking mode
```

**Pros:**
- **Latest features**: Automatically uses upstream improvements
- **Development**: Test new template versions without manual sync
- **Commit tracking**: Framework commit hash logged in experiment metadata

**Use when:** Development, testing new GHSpec-Kit releases, tracking upstream changes

#### Template Synchronization Workflow (T048)

When using dynamic templates, the framework commit hash is automatically logged:

```json
{
  "template_source": "dynamic",
  "ghspec_commit": "a1b2c3d4e5f67890abcdef1234567890abcdef12",
  "ghspec_commit_short": "a1b2c3d"
}
```

**To update dynamic templates:**

```bash
cd frameworks/ghspec
git pull origin main
cd ../..
# Next run will use updated templates
```

**To sync static templates from dynamic:**

```bash
# Copy templates from framework to static location
cp frameworks/ghspec/.specify/templates/commands/*.md docs/ghspec/prompts/
# Commit changes to version control
git add docs/ghspec/prompts/
git commit -m "Sync templates from GHSpec-Kit vX.Y.Z"
```

### Constitution Configuration

Define coding standards that guide all 5 GHSpec phases:

```yaml
# config_sets/default/experiment.yaml
framework_config:
  # Option 1: External file (recommended)
  constitution_file: config_sets/default/constitution/project_constitution.md
  
  # Option 2: Inline (for small constitutions)
  constitution_text: |
    - Always write unit tests with 80%+ coverage
    - Follow PEP 8 style guide for Python
    - Use type hints for all function signatures
```

**Default fallback:** If no constitution provided, uses `config_sets/default/constitution/default_principles.md`

### Technology Stack Constraints

Enforce specific tech choices for consistent comparisons:

```yaml
# config_sets/default/experiment.yaml
framework_config:
  tech_stack_constraints: |
    - Language: Python 3.11+
    - Web Framework: FastAPI 0.104+
    - Database: PostgreSQL 14+
    - ORM: SQLAlchemy 2.0+
    - Testing: pytest with pytest-asyncio
```

**Sprint consistency:** When `sprint_num > 1`, tech stack is automatically validated against previous sprint

## Expected Outputs

### Metrics File (`metrics.json`)

```json
{
  "AUTR": 0.85,
  "Q*": 0.72,
  "AEI": 0.043,
  "TOK_IN": 12500,
  "TOK_OUT": 3200,
  "T_WALL": 1847.5,
  "T_USER": 245.3,
  "T_CPU": 12.8,
  "CRUDe": 10,
  "ESR": 0.83,
  "MC": 0.15,
  "ZDI": 0,
  "RTE": 0.08,
  "MCI": 0,
  "ITR": 3,
  "DPL": 1
}
```

### Event Log (`event_log.jsonl`)

Each line is a JSON event:

```json
{"timestamp": "2025-10-08T14:23:15.123456Z", "level": "INFO", "message": "Starting BAEs run", "run_id": "baes-20251008-142315-abc123"}
{"timestamp": "2025-10-08T14:23:18.456789Z", "level": "INFO", "message": "Executing step 1", "step": 1, "prompt": "..."}
```

### HITL Events (`hitl_events.jsonl`)

SHA-1 hashed HITL clarifications for reproducibility:

```json
{"timestamp": "2025-10-08T14:25:30.123456Z", "step": 2, "hitl_response": "Use PostgreSQL 14 with JSON support", "sha1": "a1b2c3d4e5f6..."}
```

### Archive (`archive.tar.gz`)

Compressed tarball with SHA-256 checksum containing:
- All source code generated by framework
- Logs and intermediate outputs
- Configuration snapshots

## Next Steps

- **Reproducibility**: See [Reproducibility Guide](./reproducibility.md) for deterministic runs
- **Configuration**: See [Configuration Guide](./configuration.md) for advanced options
- **Metrics**: See [Metrics Guide](./metrics.md) for detailed metric definitions
- **Architecture**: See [Architecture Guide](./architecture.md) for system design
- **Troubleshooting**: See [Troubleshooting Guide](./troubleshooting.md) for common issues

## Troubleshooting (T058)

### Constitution Not Loading

**Symptom:** Error: "No constitution found. Checked: project_constitution.md, experiment.yaml constitution_text, default_principles.md"

**Causes:**
1. Missing default constitution file
2. Incorrect file path
3. File permission issues

**Solutions:**

```bash
# Check if default constitution exists
ls -la config_sets/default/constitution/default_principles.md

# If missing, verify you're in project root
pwd  # Should end with genai-devbench

# Check file permissions
chmod 644 config_sets/default/constitution/default_principles.md

# Verify constitution content is not empty
cat config_sets/default/constitution/default_principles.md | wc -l  # Should be > 0
```

**Alternative:** Provide inline constitution in experiment.yaml:

```yaml
framework_config:
  constitution_text: |
    - Use Python 3.11+
    - Follow PEP 8 style guide
    - Write comprehensive docstrings
```

### Template Missing Error

**Symptom:** Error: "Template not found for phase: specify"

**Causes:**
1. `template_source` misconfigured (invalid value)
2. Static templates missing from `docs/ghspec/prompts/`
3. Dynamic templates missing from `frameworks/ghspec/`

**Solutions:**

```bash
# Check template_source configuration
grep -r "template_source" config_sets/default/experiment.yaml

# Verify static templates exist
ls -la docs/ghspec/prompts/
# Should contain: specify_template.md, plan_template.md, tasks_template.md,
#                 implement_template.md, bugfix_template.md

# If using dynamic mode, check framework clone
ls -la frameworks/ghspec/.specify/templates/commands/

# If framework not cloned, clone it manually
git clone https://github.com/ghspec/ghspec-kit.git frameworks/ghspec

# Switch to static mode as workaround
# Edit config_sets/default/experiment.yaml:
framework_config:
  template_source: static  # Safe default
```

**Template validation:** Ensure templates contain required sections:
- `## System Prompt`
- `## User Prompt Template`

### API Rate Limits

**Symptom:** Error: "Rate limit exceeded for API key"

**Causes:**
1. Free-tier OpenAI API key (limited to 3 requests/minute)
2. High request volume from multiple experiments
3. Shared API key across team

**Solutions:**

```bash
# Option 1: Add delays between API calls
# Edit config_sets/default/experiment.yaml:
timeout_seconds: 3600
api_rate_limit_delay: 20  # Wait 20 seconds between calls

# Option 2: Upgrade to paid OpenAI API key
# Visit: https://platform.openai.com/account/billing

# Option 3: Use different API keys for admin vs. user operations
# Set separate keys in .env:
OPEN_AI_KEY_USR=sk-user-key-here     # For framework operations
OPEN_AI_KEY_ADM=sk-admin-key-here    # For usage API queries
```

**Rate limit monitoring:**

```bash
# Check recent API usage
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Bugfix Cycle Not Converging

**Symptom:** Warning: "Bugfix cycle reached max iterations (3) with N errors remaining"

**Causes:**
1. Complex syntax errors AI cannot fix
2. Missing imports/dependencies
3. Constitution conflicts with code generation

**Solutions:**

```bash
# Check error types in logs
grep "Error classification summary" runs/<framework>/<run-id>/event_log.jsonl

# If syntax errors dominate, check constitution for conflicting rules
cat config_sets/default/constitution/project_constitution.md

# If import errors persist, add dependency constraints
# Edit experiment.yaml:
framework_config:
  tech_stack_constraints: |
    - Install dependencies: fastapi, sqlalchemy, pytest
    - Use only standard library for utilities
```

**Manual intervention:**

```bash
# After bugfix cycle fails, inspect generated code
cat runs/<framework>/<run-id>/workspace/src/api.py

# Fix manually and re-run validation
python -m py_compile runs/<framework>/<run-id>/workspace/src/api.py
```

### Single-Threaded Execution (T064)

**Important Constraint:** The GHSpec adapter does NOT support concurrent experiment runs.

**Why:** The adapter maintains instance-level state (cached constitution, templates, phase context) that is not thread-safe.

**Symptoms of concurrent execution:**
- Race conditions in cached templates
- Constitution content from wrong experiment
- Corrupted workspace state

**Solutions:**

```bash
# CORRECT: Run experiments sequentially
./runners/run_experiment.sh baes
./runners/run_experiment.sh chatdev
./runners/run_experiment.sh ghspec

# WRONG: Parallel execution (will cause issues)
./runners/run_experiment.sh baes &
./runners/run_experiment.sh chatdev &  # DO NOT DO THIS
./runners/run_experiment.sh ghspec &

# For multi-framework comparisons, use sequential mode
./runners/run_experiment.sh --multi --sequential baes chatdev ghspec
```

**Architecture note:** Each experiment run creates an isolated workspace, but adapter state is shared within a single process. Future versions may add process-level isolation for parallel execution.

### Large Constitution Performance

**Symptom:** Long delays when loading constitution, high memory usage

**Causes:**
1. Constitution file > 100 KB
2. Many nested sections
3. Inefficient chunking strategy

**Solutions:**

```bash
# Check constitution size
ls -lh config_sets/default/constitution/project_constitution.md

# If > 100 KB, adapter automatically chunks to first 30% + last 10%
# To verify chunking, check logs:
grep "Constitution chunked" runs/<framework>/<run-id>/event_log.jsonl

# Optimize constitution:
# 1. Remove redundant sections
# 2. Use concise language
# 3. Focus on high-impact rules

# Alternative: Use constitution excerpting per phase
# (Future enhancement - not yet implemented)
```

## Common Issues

### API Rate Limits

If you encounter rate limit errors:

1. Add delays between steps in `config/experiment.yaml`:
   ```yaml
   timeout_seconds: 3600
   retry_attempts: 3
   retry_delay: 60  # Wait 60 seconds between retries
   ```

2. Use a paid OpenAI API key with higher rate limits

### Framework Clone Failures

If Git clone fails:

1. Check internet connectivity
2. Verify framework repository URL in `config/experiment.yaml`
3. Ensure Git is installed and accessible

### Disk Space

Each run consumes ~100-500 MB. Ensure sufficient disk space:

```bash
df -h .  # Check available space
```

Clean old runs if needed:

```bash
rm -rf runs/*/  # WARNING: Deletes all run data
```

## Support

For additional help:

- **Issues**: [GitHub Issues](https://github.com/gesad-lab/genai-devbench/issues)
- **Documentation**: Browse the `docs/` directory
- **Logs**: Check `event_log.jsonl` for detailed execution traces
