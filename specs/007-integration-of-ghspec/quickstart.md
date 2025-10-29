# Quick Start Guide: GHSpec-Kit Integration Enhancement

**Feature**: 007-integration-of-ghspec  
**Last Updated**: October 27, 2025  
**Audience**: Researchers and developers running genai-devbench experiments

## Overview

This guide explains how to configure and use the enhanced GHSpecAdapter with full 5-phase workflow support, constitution-based development guidance, and advanced clarification handling.

---

## Prerequisites

- genai-devbench installed and configured
- Python 3.11+ environment
- OpenAI API key configured (OPENAI_API_KEY_USAGE_TRACKING environment variable)
- GHSpec framework cloned to `frameworks/ghspec/` (via setup scripts)

---

## Configuration

### 1. Basic Experiment Setup

Edit `config/experiment.yaml` to include GHSpec runs:

```yaml
frameworks:
  - name: ghspec
    enabled: true
    api_key_env: OPENAI_API_KEY_USAGE_TRACKING
    model: gpt-4o-mini
    workspace_base: workspaces/ghspec
```

### 2. Constitution Configuration (Optional)

**Option A: Use Default Constitution**
No configuration needed. Adapter uses sensible defaults from `config/constitution/default_principles.md`.

**Option B: Provide Project-Specific Constitution**
Create `config/constitution/project_constitution.md`:

```markdown
# Project Constitution

## Coding Standards
- All code must include comprehensive docstrings
- Follow PEP 8 style guidelines
- Use type hints for all function signatures

## Testing Requirements
- Minimum 80% code coverage
- Unit tests for all public methods
- Integration tests for end-to-end workflows

## Quality Gates
- All code must pass ruff linting
- All code must pass mypy type checking
- All tests must pass before commit
```

**Option C: Inline Constitution Override**
Add to `config/experiment.yaml`:

```yaml
frameworks:
  - name: ghspec
    enabled: true
    constitution_text: |
      ## Core Principles
      - Write clean, maintainable code
      - Test all critical paths
      - Document all public APIs
```

**Priority**: project_constitution.md > inline constitution_text > default_principles.md

### 3. Technology Stack Constraints (Optional)

To ensure consistent tech stacks across experiments, add to `config/experiment.yaml`:

```yaml
frameworks:
  - name: ghspec
    enabled: true
    tech_stack_constraints: "Python 3.11+, FastAPI for web framework, PostgreSQL for database, pytest for testing"
```

If not specified, AI chooses appropriate technologies based on feature specification.

### 4. Template Source Configuration

**Static Mode (Default - Recommended for Reproducibility)**:
```yaml
frameworks:
  - name: ghspec
    enabled: true
    template_source: static  # Uses docs/ghspec/prompts/
```

**Dynamic Mode (Tracks Upstream Spec-Kit)**:
```yaml
frameworks:
  - name: ghspec
    enabled: true
    template_source: dynamic  # Uses frameworks/ghspec/.specify/templates/
```

⚠️ **Warning**: Dynamic mode may produce different results if Spec-Kit templates change. Use static mode for published experiments.

---

## Running Experiments

### Basic Run

```bash
./run_experiment.sh --framework ghspec --scenario hello-world
```

### With Custom Configuration

```bash
# Set API key
export OPENAI_API_KEY_USAGE_TRACKING="your-openai-api-key"

# Run experiment
python -m src.orchestrator \
    --framework ghspec \
    --scenario hello-world \
    --config config/experiment.yaml \
    --output runs/ghspec/run-$(date +%s)
```

### Multi-Sprint Incremental Development

```bash
# Sprint 1: Initial implementation
./run_experiment.sh --framework ghspec --scenario hello-world --sprint 1

# Sprint 2: Add authentication (builds on Sprint 1)
./run_experiment.sh --framework ghspec --scenario add-auth --sprint 2
```

Sprint 2 automatically loads Sprint 1 artifacts for incremental development.

---

## Workflow Phases

The enhanced GHSpecAdapter executes all 5 Spec-Kit phases automatically:

### Phase 1: Specify
- **Input**: Feature description from scenario
- **Output**: `spec.md` (business specification)
- **Duration**: ~2-3 minutes

### Phase 2: Plan
- **Input**: `spec.md` + constitution + tech constraints
- **Output**: `plan.md` (technical architecture)
- **Duration**: ~2-3 minutes

### Phase 3: Tasks
- **Input**: `spec.md` + `plan.md`
- **Output**: `tasks.md` (implementation task list)
- **Duration**: ~1-2 minutes

### Phase 4: Implement
- **Input**: `tasks.md` + spec/plan excerpts
- **Output**: Source code files in `src/`
- **Duration**: ~5-10 minutes (task-by-task generation)

### Phase 5: Bugfix (Automated)
- **Input**: Validation errors from Phase 4
- **Output**: Fixed code files
- **Duration**: ~1-3 minutes per iteration (max 3 iterations)

**Total Runtime**: Typically 12-18 minutes for medium complexity features.

---

## Output Artifacts

After successful run, find artifacts in workspace:

```
workspaces/ghspec/<run-id>/
├── specs/
│   └── 001-baes-experiment/
│       ├── spec.md           # Phase 1 output
│       ├── plan.md           # Phase 2 output
│       ├── tasks.md          # Phase 3 output
│       └── src/              # Phase 4 output
│           ├── models/
│           ├── services/
│           └── api/
├── spec.md                   # Copied to root for validation
├── plan.md
├── tasks.md
└── [generated code files]    # Copied to root for validation
```

---

## Clarification Handling

The adapter handles AI clarification requests automatically using pre-defined guidelines:

### How It Works

1. AI requests clarification (e.g., `[NEEDS CLARIFICATION: auth method?]`)
2. Adapter loads `config/hitl/ghspec_clarification_guidelines.txt`
3. Guidelines appended to prompt, AI regenerates response
4. Up to 3 clarification iterations per phase (then proceeds with best-effort)

### Customizing Clarifications

Edit `config/hitl/ghspec_clarification_guidelines.txt`:

```text
# Clarification Guidelines for GHSpec Experiments

## Authentication
Use OAuth 2.0 with JWT tokens for all authentication requirements.

## Database
Use PostgreSQL for all persistent storage needs.

## API Design
Follow REST principles with JSON payloads.

## Iteration 2 Guidance (if first clarification insufficient)
If still unclear, default to industry-standard patterns for the domain.

## Iteration 3 Guidance (final attempt)
Make best-effort interpretation based on specification context.
```

---

## Troubleshooting

### Constitution Not Loading

**Problem**: Adapter fails with "No constitution found"

**Solution**:
```bash
# Check file exists
ls -la config/constitution/default_principles.md

# Ensure proper permissions
chmod 644 config/constitution/default_principles.md

# Or provide inline override in experiment.yaml
```

### Template Files Missing

**Problem**: "Template file not found: specify_template.md"

**Solution**:
```bash
# Verify static templates exist
ls docs/ghspec/prompts/

# Or switch to dynamic mode (requires GHSpec cloned)
# Edit experiment.yaml: template_source: dynamic
```

### Bugfix Phase Not Executing

**Problem**: Phase 4 completes but bugfix phase skipped

**Expected Behavior**: Bugfix only runs if validation errors exist. Check logs:

```bash
grep "bugfix" runs/ghspec/<run-id>/orchestrator.log
```

If no errors in Phase 4, bugfix is correctly skipped.

### API Rate Limits

**Problem**: "Rate limit exceeded" error mid-workflow

**Behavior**: Experiment fails immediately (fail-fast design, no retries)

**Solution**:
- Wait for rate limit to reset (typically 1 minute for free tier)
- Upgrade to higher OpenAI tier if running frequent experiments
- Check token usage in logs to optimize prompt sizes

### Tech Stack Ignored

**Problem**: plan.md doesn't reflect configured tech_stack_constraints

**Validation**:
```bash
# Check constraints were loaded
grep "tech_stack_constraints" runs/ghspec/<run-id>/orchestrator.log

# Manually verify plan.md contains expected technologies
grep -i "fastapi\|postgresql" workspaces/ghspec/<run-id>/plan.md
```

**Solution**: Ensure constraints_text is non-empty, descriptive, and includes specific technology names.

---

## Advanced Usage

### Large Constitution Files

For constitutions >100KB:

```python
# Adapter automatically chunks large files
# First 30KB + last 10KB injected into prompts
# Full constitution logged but not fully transmitted to AI
```

No configuration needed - automatic handling per FR-011.

### Validating Token Metrics

Check token accuracy against OpenAI API:

```bash
# Extract run timestamps from logs
START_TIME=$(jq '.start_timestamp' runs/ghspec/<run-id>/metadata.json)
END_TIME=$(jq '.end_timestamp' runs/ghspec/<run-id>/metadata.json)

# Query OpenAI Usage API (requires admin key)
curl -H "Authorization: Bearer $OPENAI_API_KEY_USAGE_TRACKING" \
     "https://api.openai.com/v1/usage?start_time=$START_TIME&end_time=$END_TIME"

# Compare with logged metrics
jq '.metrics.tokens_in, .metrics.tokens_out' runs/ghspec/<run-id>/metadata.json
```

### Debugging Phase Failures

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
./run_experiment.sh --framework ghspec --scenario test-feature
```

Check phase-specific logs:

```bash
# Phase transitions
grep "phase_start\|phase_end" runs/ghspec/<run-id>/orchestrator.log

# API calls
grep "openai_api_call" runs/ghspec/<run-id>/orchestrator.log

# Clarifications
grep "hitl_interaction" runs/ghspec/<run-id>/orchestrator.log
```

---

## Best Practices

1. **Always Use Static Templates for Published Experiments**: Ensures reproducibility when sharing results.

2. **Document Constitution Rationale**: Add comments to project_constitution.md explaining why specific standards chosen.

3. **Test Clarification Guidelines**: Run simple experiments to verify HITL responses resolve ambiguities correctly.

4. **Monitor Bugfix Success Rate**: If <60% success (SC-003), review validation errors and improve spec clarity.

5. **Archive Complete Workspaces**: Save entire `workspaces/ghspec/<run-id>/` directory for replication studies.

6. **Pin Framework Versions**: Record GHSpec commit hash in experiment metadata for exact reproduction.

---

## Example Configurations

### Minimal Configuration (Defaults)
```yaml
frameworks:
  - name: ghspec
    enabled: true
    api_key_env: OPENAI_API_KEY_USAGE_TRACKING
```

### Research Configuration (Reproducibility Focus)
```yaml
frameworks:
  - name: ghspec
    enabled: true
    api_key_env: OPENAI_API_KEY_USAGE_TRACKING
    template_source: static
    tech_stack_constraints: "Python 3.11, FastAPI, PostgreSQL, pytest"
    constitution_text: |
      ## Research Standards
      - All code must be deterministic (fixed random seeds)
      - Document all non-obvious design decisions
      - Comprehensive logging for experiment analysis
```

### Development Configuration (Upstream Tracking)
```yaml
frameworks:
  - name: ghspec
    enabled: true
    api_key_env: OPENAI_API_KEY_USAGE_TRACKING
    template_source: dynamic
    # No tech constraints - let AI explore options
```

---

## Support

For issues or questions:
- Check experiment logs: `runs/ghspec/<run-id>/orchestrator.log`
- Review constitution compliance in output artifacts
- Consult `docs/ghspec/` for detailed Spec-Kit methodology
- See `src/adapters/ghspec_adapter.py` docstrings for implementation details

---

**Version**: 1.0.0 | **Feature**: 007-integration-of-ghspec | **Status**: Draft
