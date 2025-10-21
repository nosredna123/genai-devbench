# Quickstart: Config Sets + Configurable Steps

**Last Updated**: 2024-10-21  
**Version**: 1.0  
**Implementation Status**: Complete ✅

---

## 🚀 5-Minute Quick Start

Get started with config sets and configurable steps in 5 minutes.

---

## What Are Config Sets?

Config Sets are **curated experiment templates** that provide pre-configured prompts, steps, and HITL files for common scenarios:

- 📦 **default**: 6-step CRUD application (Student/Course/Teacher)
- 📦 **minimal**: 1-step Hello World API (testing/learning)
- 📦 **microservices** (coming soon): Multi-service architecture
- 📦 **ml_pipeline** (coming soon): ML model development

Each config set includes:
- ✅ Step configurations
- ✅ Prompt files
- ✅ HITL specifications
- ✅ Default settings

---

## Two-Stage Architecture

```
┌─────────────────────────────────────────────┐
│ STAGE 1: Generator (genai-devbench repo)   │
│                                             │
│ config_sets/                                │
│ ├── default/      ← Curated templates      │
│ │   ├── metadata.yaml                      │
│ │   ├── experiment_template.yaml           │
│ │   ├── prompts/  (6 steps)                │
│ │   └── hitl/                              │
│ └── minimal/      ← Testing template       │
│     └── ...       (1 step)                 │
└─────────────────────────────────────────────┘
                     │
                     ▼ Generate
┌─────────────────────────────────────────────┐
│ STAGE 2: Generated Experiment (my_test/)   │
│                                             │
│ my_test/                                    │
│ ├── config/                                 │
│ │   ├── config.yaml  ← Customize here!     │
│ │   ├── prompts/     ← All steps copied    │
│ │   └── hitl/        ← HITL copied         │
│ └── runs/            ← Results stored      │
└─────────────────────────────────────────────┘
```

**Key Insight**: 
- Generator copies **ALL files** from config set
- You customize **after generation** by editing config.yaml
- Experiment is **self-contained** (no dependency on generator)

---

## Quick Start Examples

### Example 1: Default Config Set (6 Steps)

```bash
# 1. List available config sets
python scripts/new_experiment.py --list-config-sets

# Output:
# 📦 Available Config Sets:
#   • default (6 steps): Traditional 6-step CRUD application
#   • minimal (1 step): Hello World API for testing

# 2. Generate experiment
python scripts/new_experiment.py \
  --name my_crud_test \
  --config-set default \
  --model gpt-4o-mini \
  --frameworks baes \
  --runs 5

# Output:
# 🚀 Generating standalone experiment: my_crud_test
# 📦 Config set: default (6 steps)
# ✅ Generation complete!

# 3. Customize (optional)
vim my_crud_test/config.yaml
# → Disable step 6 (UI)
# → Reorder steps
# → Adjust timeouts

# 4. Run experiment
cd my_crud_test
./run.sh
```

### Example 2: Minimal Config Set (1 Step)

```bash
# Quick test with minimal config
python scripts/new_experiment.py \
  --name hello_test \
  --config-set minimal \
  --model gpt-4o-mini \
  --frameworks baes \
  --runs 1

# Generated config.yaml will have:
# steps:
#   - id: 1
#     enabled: true
#     name: "Hello World API"
#     prompt_file: "config/prompts/01_hello_world.txt"
```

---

## Step-by-Step Tutorial

### Step 1: Choose a Config Set

```bash
# See what's available
python scripts/new_experiment.py --list-config-sets
```

**Output:**
```
📦 Available Config Sets:

  • default (v1.0.0)
    6 steps: Traditional 6-step CRUD application (Student/Course/Teacher)
    Steps:
      1. Student CRUD
      2. Course CRUD
      3. Teacher CRUD
      4. Authentication
      5. Relationships
      6. Testing

  • minimal (v1.0.0)
    1 step: Hello World API for testing and learning
    Steps:
      1. Hello World API
```

### Step 2: Generate Experiment

```bash
python scripts/new_experiment.py \
  --name my_experiment \
  --config-set default \
  --model gpt-4o-mini \
  --frameworks baes chatdev \
  --runs 10
```

**What happens:**
- ✅ Creates `my_experiment/` directory
- ✅ Copies **ALL** prompts from config set
- ✅ Copies **ALL** HITL files
- ✅ Generates `config.yaml` with **all steps enabled**
- ✅ Creates standalone git repository

### Step 3: Review Generated Config

```bash
cat my_experiment/config.yaml
```

**Generated config.yaml:**
```yaml
# Experiment Configuration
# Generated from config set: default
# 
# This is a self-contained experiment. You can freely modify this file:
# - Disable steps by setting 'enabled: false'
# - Reorder steps by moving entries (execution follows declaration order)
# - Modify prompt_file paths to point to custom prompts
# - Adjust timeouts, metrics, and other settings

experiment_name: my_experiment
model: gpt-4o-mini
random_seed: 42

# Steps execute in DECLARATION ORDER (not sorted by ID)
steps:
  - id: 1
    enabled: true
    name: "Student CRUD"
    prompt_file: "config/prompts/01_student_crud.txt"
  
  - id: 2
    enabled: true
    name: "Course CRUD"
    prompt_file: "config/prompts/02_course_crud.txt"
  
  - id: 3
    enabled: true
    name: "Teacher CRUD"
    prompt_file: "config/prompts/03_teacher_crud.txt"
  
  - id: 4
    enabled: true
    name: "Authentication"
    prompt_file: "config/prompts/04_authentication.txt"
  
  - id: 5
    enabled: true
    name: "Relationships"
    prompt_file: "config/prompts/05_relationships.txt"
  
  - id: 6
    enabled: true
    name: "Testing"
    prompt_file: "config/prompts/06_testing.txt"

timeouts:
  step_timeout_seconds: 600
  total_timeout_seconds: 7200

# ... more settings
```

### Step 4: Customize Steps (Optional)

Edit `my_experiment/config.yaml` to customize:

#### Disable Steps

```yaml
steps:
  - id: 6
    enabled: false  # Skip testing step
    name: "Testing"
    prompt_file: "config/prompts/06_testing.txt"
```

#### Reorder Steps

```yaml
# Execute in this order: 3 → 1 → 2
steps:
  - id: 3
    enabled: true
    name: "Teacher CRUD"
  
  - id: 1
    enabled: true
    name: "Student CRUD"
  
  - id: 2
    enabled: true
    name: "Course CRUD"
```

**Result**: Steps execute in declaration order (3, 1, 2), but metrics preserve original IDs.

#### Use Custom Prompts

```yaml
steps:
  - id: 1
    enabled: true
    name: "Custom Student CRUD"
    prompt_file: "config/prompts/custom_student.txt"  # Point to your file
```

### Step 5: Run Experiment

```bash
cd my_experiment
./run.sh
```

**Console Output:**
```
📋 Loading experiment configuration...
   ✓ Found 5 enabled steps
      1. Step 1: Student CRUD
      2. Step 2: Course CRUD
      3. Step 3: Teacher CRUD
      4. Step 4: Authentication
      5. Step 5: Relationships

🚀 Run 1/10

Framework: baes
   Step 1 (Student CRUD) | 1/5... ✓ (45s)
   Step 2 (Course CRUD) | 2/5... ✓ (38s)
   Step 3 (Teacher CRUD) | 3/5... ✓ (42s)
   Step 4 (Authentication) | 4/5... ✓ (51s)
   Step 5 (Relationships) | 5/5... ✓ (47s)
```

---

## Common Use Cases

### Use Case 1: Testing with Minimal Set

**Goal**: Quick smoke test before full run

```bash
python scripts/new_experiment.py \
  --name smoke_test \
  --config-set minimal \
  --model gpt-4o-mini \
  --frameworks baes \
  --runs 1
```

**Why**: Single step, fast execution, minimal cost

---

### Use Case 2: Backend-Only Testing

**Goal**: Test API without UI

```bash
# 1. Generate with default config set
python scripts/new_experiment.py \
  --name backend_test \
  --config-set default \
  --model gpt-4o-mini \
  --frameworks baes chatdev \
  --runs 5

# 2. Disable step 6 (if it's UI)
vim backend_test/config.yaml
# Set step 6 enabled: false

# 3. Run
cd backend_test
./run.sh
```

---

### Use Case 3: Incremental Testing

**Goal**: Test steps 1-3, then 1-5, then all

```bash
# Round 1: Steps 1-3
python scripts/new_experiment.py \
  --name test_round1 \
  --config-set default \
  --model gpt-4o-mini \
  --frameworks baes \
  --runs 3

vim test_round1/config.yaml
# Disable steps 4-6

# Round 2: Steps 1-5 (copy and modify)
cp -r test_round1 test_round2
vim test_round2/config.yaml
# Enable steps 4-5, keep 6 disabled

# Round 3: All steps
cp -r test_round1 test_round3
vim test_round3/config.yaml
# Enable all steps
```

---

### Use Case 4: Custom Step Order

**Goal**: Test relationships before authentication

```yaml
steps:
  - id: 5
    enabled: true
    name: "Relationships"
  
  - id: 4
    enabled: true
    name: "Authentication"
  
  # ... other steps
```

**Result**: Executes step 5 first, then 4, preserving IDs in metrics

---

## Declaration Order Execution

**Key Feature**: Steps execute in the order they appear in config.yaml, **NOT** sorted by ID.

### Example: Non-Sequential Execution

```yaml
steps:
  - id: 3
    enabled: true
  
  - id: 1
    enabled: true
  
  - id: 5
    enabled: true
```

**Execution Order**: 3 → 1 → 5

**Metrics Record**: Step IDs preserved (3, 1, 5)

**Console Output**:
```
Step 3 (Teacher CRUD) | 1/3... ✓
Step 1 (Student CRUD) | 2/3... ✓
Step 5 (Relationships) | 3/3... ✓
```

---

## Available Config Sets

### default (6 steps)

**Description**: Traditional CRUD application with authentication and testing

**Steps**:
1. Student CRUD - Basic Student entity operations
2. Course CRUD - Basic Course entity operations
3. Teacher CRUD - Basic Teacher entity operations
4. Authentication - User auth and authorization
5. Relationships - Student-Course, Teacher-Course relationships
6. Testing - Unit and integration tests

**Use For**:
- ✅ Full-featured API testing
- ✅ Framework comparison
- ✅ Production-like scenarios

---

### minimal (1 step)

**Description**: Simple Hello World API

**Steps**:
1. Hello World API - Basic endpoint returning "Hello World"

**Use For**:
- ✅ Quick testing
- ✅ Learning the system
- ✅ Debugging framework issues
- ✅ Minimal cost experiments

---

## Validation & Error Handling

### Automatic Validation

The system validates:
- ✅ At least one step enabled
- ✅ No duplicate step IDs
- ✅ All prompt files exist
- ✅ Prompt files not empty

### Fail-Fast Behavior

**Invalid config.yaml** → Immediate error before execution

```bash
❌ Configuration Error:
  - Step 1 (Student CRUD): Prompt file not found: config/prompts/missing.txt
  - No enabled steps found. At least one step must be enabled.
```

### Common Errors

#### Error: "No enabled steps"

**Cause**: All steps have `enabled: false`

**Fix**:
```yaml
steps:
  - id: 1
    enabled: true  # ← Enable at least one step
```

#### Error: "Prompt file not found"

**Cause**: Referenced prompt file doesn't exist

**Fix**:
```yaml
steps:
  - id: 1
    enabled: true
    prompt_file: "config/prompts/01_student_crud.txt"  # ← Use correct path
```

#### Error: "Duplicate step IDs"

**Cause**: Same ID appears multiple times

**Fix**:
```yaml
steps:
  - id: 1  # ✅ Unique
  - id: 2  # ✅ Unique
  # Not: id: 1 again ❌
```

---

## Best Practices

### ✅ DO:

1. **Start with existing config sets**
   ```bash
   python scripts/new_experiment.py --config-set default ...
   ```

2. **Customize after generation**
   ```bash
   vim my_experiment/config.yaml
   ```

3. **Test incrementally**
   - First: 1-3 steps
   - Then: 1-5 steps
   - Finally: All steps

4. **Document customizations**
   ```yaml
   steps:
     - id: 6
       enabled: false  # Disabled: UI not needed for API testing
   ```

5. **Use meaningful names**
   ```yaml
   - id: 1
     name: "Student CRUD with Validation"  # Clear intent
   ```

### ❌ DON'T:

1. **Don't modify generator's config_sets/**
   - Config sets are curated templates
   - Customize in generated experiments only

2. **Don't skip early steps if later steps depend on them**
   ```yaml
   # Bad: Step 5 might need steps 1-4
   - id: 5
     enabled: true
   - id: 1
     enabled: false  # ❌ May break step 5
   ```

3. **Don't create circular dependencies**
   - Steps are independent by design
   - No dependency validation (yet)

4. **Don't edit prompts in generator**
   - Edit in generated experiment only
   - Keeps config sets clean

---

## CLI Reference

### Generate Experiment

```bash
python scripts/new_experiment.py \
  --name <experiment_name> \
  --config-set <config_set_name> \
  --model <model_name> \
  --frameworks <framework1> <framework2> ... \
  --runs <num_runs>
```

**Required Arguments**:
- `--name`: Experiment directory name
- `--config-set`: Config set to use (default, minimal)
- `--model`: LLM model (gpt-4o-mini, gpt-4o, etc.)
- `--frameworks`: Frameworks to test (baes, chatdev, ghspec)
- `--runs`: Number of runs per framework

**Optional Arguments**:
- `--seed`: Random seed for reproducibility
- `--experiments-dir`: Where to create experiment (default: current dir)

### List Config Sets

```bash
python scripts/new_experiment.py --list-config-sets
```

**Output**:
```
📦 Available Config Sets:
  • default (v1.0.0) - 6 steps
  • minimal (v1.0.0) - 1 step
```

---

## Files Generated

When you generate an experiment, you get:

```
my_experiment/
├── config/
│   ├── config.yaml          ← Main configuration
│   ├── prompts/
│   │   ├── 01_student_crud.txt   ← All prompts copied
│   │   ├── 02_course_crud.txt
│   │   └── ...
│   └── hitl/
│       └── expanded_spec.txt     ← HITL files copied
├── src/                     ← Framework code
├── runs/                    ← Results (created during execution)
├── setup.sh                 ← Setup script
├── run.sh                   ← Execution script
├── .env.example             ← API key template
└── README.md                ← Experiment docs
```

**Self-Contained**: No dependencies on generator after creation!

---

## Troubleshooting

### Issue: "Config set not found"

**Solution**:
```bash
# List available config sets
python scripts/new_experiment.py --list-config-sets

# Use exact name
python scripts/new_experiment.py --config-set default ...
```

### Issue: Steps not executing in expected order

**Check**: Declaration order in config.yaml
```yaml
# This order:
steps:
  - id: 2
  - id: 1

# Executes: 2 → 1 (not 1 → 2!)
```

### Issue: "No module named 'src.config_sets'"

**Solution**: Run from repository root
```bash
cd /path/to/genai-devbench
python scripts/new_experiment.py ...
```

---

## Next Steps

### Learn More
- 📖 [Creating Config Sets](CREATING_CONFIG_SETS.md) - Build your own config sets
- 📖 [Implementation Guide](FINAL-IMPLEMENTATION-PLAN.md) - Technical details
- 📖 [Feature Spec](feature-spec.md) - Complete feature documentation

### Try It Out
1. Generate a minimal experiment
2. Customize config.yaml
3. Run and observe results
4. Iterate and refine

---

## FAQ

**Q: Can I create custom config sets?**  
A: Yes! See [Creating Config Sets](CREATING_CONFIG_SETS.md) for a guide.

**Q: What happens to skipped steps?**  
A: They're not executed. No metrics, no logs, no API calls.

**Q: Can I change steps after starting a run?**  
A: No. Config is frozen per experiment. Create a new experiment for different configuration.

**Q: Do all frameworks run the same steps?**  
A: Yes. Same configuration ensures fair comparison.

**Q: Can I mix steps from different config sets?**  
A: Not directly. Choose one config set, then customize prompts manually.

**Q: What's the difference between step ID and position?**  
A: 
- **ID**: Original step number (preserved in metrics)
- **Position**: Execution order (1/5, 2/5, etc.)

**Q: Is the `minimal` config set just for testing?**  
A: Yes, primarily. But you can use it as a template for simple experiments.

---

## Summary

**Key Takeaways**:
1. 📦 Config sets provide curated templates
2. 🔧 Generator copies ALL files
3. ✏️ Customize after generation
4. 🎯 Declaration order = execution order
5. 📊 Step IDs preserved in metrics
6. ✅ Fail-fast validation prevents issues

**Ready to start?**
```bash
python scripts/new_experiment.py --list-config-sets
```

🚀 **Happy experimenting!**
