# Round 2 Clarification: Deep Dive into Design Implications

## 🎯 Purpose
Based on your initial answers, this document explores the deeper implications and technical decisions needed to implement the integrated Config Sets + Configurable Steps system.

**Date:** 2025-10-21  
**Status:** ROUND 2 CLARIFICATION

---

## 📊 Analysis of Your Round 1 Answers

### ✅ What We Know So Far:

**A1.1 - Scenario Definition:** "All of the above (combination)"
- Config sets can mix: domain + tech stack + complexity + step count
- Researcher responsibility to choose appropriate config set
- Redundancy is acceptable if serving distinct experimental purposes

**A1.2 - Steps Flexibility:** "Option B - Flexible Steps"
- Steps configured directly in experiment config.yaml
- Can reorder, skip, or add custom steps
- Generated experiments should be minimal (only used steps/prompts)
- No knowledge of unused config set capabilities in generated experiment

---

## 📋 PART G: Flexible Steps - Deep Dive

### G1. Step ID Management with Flexibility

#### Q1.1: With flexible step IDs, how do we handle metrics and reporting?

**Your Choice:** Option B allows `id: 1`, then `id: 5`, then `id: 99`

**Scenario:** Researcher creates experiment:
```yaml
steps:
  - id: 1
    enabled: true
    name: "Service Design"
    prompt_file: "config/prompts/step_1.txt"
  - id: 5  # Skipped 2,3,4
    enabled: true
    name: "Communication"
    prompt_file: "config/prompts/step_5.txt"
  - id: 99  # Custom step
    enabled: true
    name: "Custom Security Audit"
    prompt_file: "my_prompts/security.txt"
```

**Question G1.1a:** Should metrics use:
- **Option A - Original IDs (1, 5, 99):** Preserves semantic meaning, but gaps in reports
- **Option B - Sequential (1, 2, 3):** Clean reports, but loses original step meaning
- **Option C - Dual tracking:** Track both original and execution order

**Your Preference:** _______________

---

#### Q1.2: How should step execution order be determined?

**Question G1.2a:** When steps are flexible, execution order is:

**Option A - By ID (ascending):**
```yaml
steps:
  - id: 5    # Runs SECOND
  - id: 1    # Runs FIRST  
  - id: 99   # Runs THIRD
```
Sorted automatically: 1 → 5 → 99

**Option B - By declaration order:**
```yaml
steps:
  - id: 5    # Runs FIRST (declared first)
  - id: 1    # Runs SECOND
  - id: 99   # Runs THIRD
```
Executes as written: 5 → 1 → 99

**Option C - Explicit order field:**
```yaml
steps:
  - id: 5
    order: 2
  - id: 1
    order: 1
  - id: 99
    order: 3
```
Requires explicit ordering

**Your Preference:** _______________

**Rationale:** _______________

---

#### Q1.3: Custom step validation - how strict?

**You said:** "Can add custom steps with custom prompt files"

**Question G1.3a:** Should custom prompt files be validated?

**Scenario:** User references `my_prompts/security.txt` but file doesn't exist

**Option A - Fail Fast (generation time):**
```bash
$ python scripts/new_experiment.py --config-set microservices
ERROR: Custom prompt file not found: my_prompts/security.txt
Experiment generation aborted.
```
- ✅ Catch errors early
- ❌ Can't generate experiment to edit later

**Option B - Fail at Runtime (execution time):**
```bash
$ python scripts/run_experiment.py my_experiment
✓ Step 1: Service Design [COMPLETED]
✓ Step 5: Communication [COMPLETED]
✗ Step 99: Custom Security Audit [ERROR: Prompt file not found]
```
- ✅ Allow generation with placeholders
- ❌ Fail during expensive experiment runs

**Option C - Lenient with Warning:**
```bash
$ python scripts/new_experiment.py --config-set microservices
WARNING: Custom prompt file not found: my_prompts/security.txt
         Create this file before running the experiment.
Experiment generated successfully.
```
- ✅ Flexible workflow
- ❌ Easy to forget

**Your Preference:** _______________

---

### G2. Minimal Generated Experiments

#### Q2.1: What exactly gets copied to generated experiment?

**You said:** "Just the steps and prompt files that are actually used should be included"

**Question G2.1a:** For this config:
```yaml
# Experiment uses steps 1, 5, 99
steps:
  - id: 1
    prompt_file: "config/prompts/step_1.txt"
  - id: 5
    prompt_file: "config/prompts/step_5.txt"
  - id: 99
    prompt_file: "my_prompts/security.txt"
```

**Should the generated experiment contain:**

**Option A - Only Used Prompts:**
```
my_experiment/
├── config/
│   ├── config.yaml
│   └── prompts/
│       ├── step_1.txt      # Copied from config set
│       └── step_5.txt      # Copied from config set
└── my_prompts/
    └── security.txt        # Custom (user provides)
```

**Option B - All Config Set Prompts (reference to unused):**
```
my_experiment/
├── config/
│   ├── config.yaml
│   └── prompts/            # All from config set
│       ├── step_1.txt      # Used
│       ├── step_2.txt      # Unused but present
│       ├── step_3.txt      # Unused but present
│       └── ...
└── my_prompts/
    └── security.txt
```

**Option C - Symlinks to Config Set:**
```
my_experiment/
├── config/
│   ├── config.yaml
│   └── prompts/ -> ../../config_sets/microservices/prompts/
└── my_prompts/
    └── security.txt
```

**Your Preference:** _______________

---

#### Q2.2: HITL files in generated experiment?

**Question G2.2a:** Following the "minimal experiment" principle:

**Option A - Always Copy HITL:**
```
my_experiment/
├── config/
│   ├── config.yaml
│   ├── prompts/
│   │   ├── step_1.txt
│   │   └── step_5.txt
│   └── hitl/
│       └── expanded_spec.txt  # Always included
```
- ✅ Self-contained
- ❌ Duplicates large files

**Option B - Reference HITL:**
```yaml
# my_experiment/config.yaml
hitl:
  expanded_spec: "../../config_sets/microservices/hitl/expanded_spec.txt"
```
- ✅ No duplication
- ❌ Breaks if config set moves

**Option C - Copy on Finalization:**
```bash
# During development - reference
python scripts/new_experiment.py --config-set microservices

# Before archiving - snapshot
python scripts/finalize_experiment.py my_experiment
# Now copies all referenced files
```
- ✅ Best of both worlds
- ❌ Requires explicit finalization step

**Your Preference:** _______________

---

### G3. Config Set Awareness in Generated Experiments

#### Q3.1: How much should generated experiment "know" about its source?

**You said:** "The generated experiment should not have knowledge of other possible steps or scenarios available in the generator's config sets"

**Question G3.1a:** Should the experiment track its source config set?

**Option A - Full Amnesia:**
```yaml
# my_experiment/config.yaml
steps:
  - id: 1
    enabled: true
    prompt_file: "config/prompts/step_1.txt"
# No mention of where this came from
```
- ✅ Pure minimal experiment
- ❌ Can't reproduce or trace origin

**Option B - Source Reference Only:**
```yaml
# my_experiment/config.yaml
_metadata:
  generated_from: "microservices"  # Just the name
  generated_at: "2025-10-21T15:30:00Z"

steps:
  - id: 1
    enabled: true
    prompt_file: "config/prompts/step_1.txt"
```
- ✅ Traceable
- ❌ Still references external system

**Option C - Immutable Snapshot:**
```yaml
# my_experiment/config.yaml
_metadata:
  source_config_set:
    name: "microservices"
    version: "1.0.0"
    snapshot_hash: "abc123..."
    # Full snapshot in separate file
    snapshot_path: "config_set_snapshot/"

steps:
  - id: 1
    enabled: true
    prompt_file: "config/prompts/step_1.txt"
```
- ✅ Fully reproducible
- ❌ Violates "minimal" principle

**Your Preference:** _______________

**Rationale:** _______________

---

## 📋 PART H: Config Set Structure Details

### H1. Config Set as "Step Pool"

#### Q1.1: How should config set define available steps?

**Based on your answers:**
- Config set provides step prompts
- User can use any/all/some/none + add custom
- Generated experiment is minimal

**Question H1.1a:** What is the "contract" of a config set?

**Option A - Config Set Defines Available Steps:**
```yaml
# config_sets/microservices/metadata.yaml
name: "microservices"
description: "8-step microservices architecture"
available_steps:
  1:
    name: "Service Design"
    prompt_file: "prompts/step_1.txt"
  2:
    name: "API Gateway"
    prompt_file: "prompts/step_2.txt"
  # ... up to 8
```
User picks from this menu

**Option B - Config Set is Just a Directory:**
```
config_sets/microservices/
├── metadata.yaml          # Basic info only
├── prompts/
│   ├── step_1.txt
│   ├── step_2.txt
│   └── ...
└── hitl/
    └── expanded_spec.txt
```
User manually specifies which prompt files to use

**Option C - Hybrid (Catalog + Flexibility):**
```yaml
# metadata.yaml - suggests steps but doesn't enforce
suggested_steps:
  - id: 1
    name: "Service Design"
    prompt_file: "prompts/step_1.txt"
  - id: 2
    name: "API Gateway"
    prompt_file: "prompts/step_2.txt"
# Users can deviate from suggestions
```

**Your Preference:** _______________

---

#### Q1.2: Should config sets support step dependencies?

**Question H1.2a:** If user enables step 5 but not steps 2-4, should we:

**Option A - No Dependencies (your current choice):**
```yaml
steps:
  - id: 1
    enabled: true
  - id: 5    # OK to skip 2,3,4
    enabled: true
```
User's responsibility to ensure logical flow

**Option B - Warn on Missing Dependencies:**
```yaml
# config_sets/microservices/metadata.yaml
available_steps:
  5:
    name: "Communication"
    dependencies: [2, 3, 4]  # Optional but recommended
```
Generator warns: "Step 5 usually requires steps 2-4. Continue? (y/N)"

**Option C - Enforce Dependencies:**
```yaml
available_steps:
  5:
    name: "Communication"
    required_dependencies: [2, 3]  # Must have
    optional_dependencies: [4]     # Recommended
```
Generator fails if required dependencies missing

**Your Preference:** _______________

---

### H2. experiment_template.yaml Content

#### Q2.1: With flexible steps, what goes in the template?

**Question H2.1a:** Should experiment_template.yaml include default steps?

**Option A - Template Has Default Steps:**
```yaml
# config_sets/microservices/experiment_template.yaml
steps:
  - id: 1
    enabled: true
    name: "Service Design"
    prompt_file: "config/prompts/step_1.txt"
  - id: 2
    enabled: true
    name: "API Gateway"
    prompt_file: "config/prompts/step_2.txt"
  # ... all 8 steps

# During generation:
"Use all 8 steps from template? (Y/n): n"
"Which steps? (1-8, comma-separated): 1,5,8"
# Generates experiment with only steps 1,5,8
```
- ✅ Easy for beginners (defaults provided)
- ❌ Template must change if steps change

**Option B - Template Has No Steps:**
```yaml
# config_sets/microservices/experiment_template.yaml
# No steps section

# During generation:
"Select steps from microservices config set:"
"  1. Service Design (prompts/step_1.txt)"
"  2. API Gateway (prompts/step_2.txt)"
"  ... (shows all available)"
"Which steps? (1-8, comma-separated): 1,5,8"
# Generator constructs steps section
```
- ✅ No duplication between metadata and template
- ❌ Requires interactive or explicit CLI flags

**Option C - Template References Metadata:**
```yaml
# experiment_template.yaml
steps: "use_all_from_metadata"  # Special value
# Or
steps: "prompt_user"  # Ask during generation
```

**Your Preference:** _______________

---

#### Q2.2: Other template configuration - scenario-specific or experiment-specific?

**Question H2.2a:** For each configuration item, mark Config Set Template vs. Experiment Creation:

| Configuration | Config Set Template | Experiment Creation | Both (override) |
|---------------|---------------------|---------------------|-----------------|
| Steps (default enabled/disabled) | ? | ? | ? |
| Step names | ? | ? | ? |
| Step timeout (max time per step) | ? | ? | ? |
| Total experiment timeout | ? | ? | ? |
| Metrics weights | ? | ? | ? |
| Stopping rule (confidence level) | ? | ? | ? |
| Max/Min runs | ? | ? | ? |
| Model (gpt-4o-mini, o1-mini) | ? | ? | ? |
| Frameworks to test | ? | ? | ? |
| Temperature | ? | ? | ? |
| Random seed | ? | ? | ? |
| Output directory | ? | ? | ? |

**Instructions:** Put X in one column per row

**Rationale for key decisions:** _______________

---

## 📋 PART I: Practical Workflow Scenarios

### I1. Researcher Workflows

#### Q1.1: Scenario walkthrough - validate the design

**Scenario 1: Standard Usage (use config set as-is)**

Researcher wants to test microservices scenario with all steps:

```bash
# What should this command do?
python scripts/new_experiment.py \
  --name my_microservices_test \
  --config-set microservices
```

**Question I1.1a:** Should this:

**Option A - Use All Steps by Default:**
```yaml
# Generated: my_microservices_test/config.yaml
steps:
  - id: 1
    enabled: true
    prompt_file: "config/prompts/step_1.txt"
  - id: 2
    enabled: true
    prompt_file: "config/prompts/step_2.txt"
  # ... all 8 steps enabled
```

**Option B - Prompt for Steps:**
```
$ python scripts/new_experiment.py --name test --config-set microservices
Config set 'microservices' has 8 steps. Which to enable?
  1) All (default)
  2) Custom selection
Choice [1]: _
```

**Option C - Require Explicit Step Selection:**
```bash
# Must specify:
python scripts/new_experiment.py \
  --name test \
  --config-set microservices \
  --steps all  # or --steps 1,2,3,4,5,6,7,8
```

**Your Preference:** _______________

---

**Scenario 2: Custom Step Subset**

Researcher wants to test only steps 1, 5, and 8:

```bash
python scripts/new_experiment.py \
  --name my_test \
  --config-set microservices \
  --steps 1,5,8
```

**Question I1.2a:** What gets generated?

```
my_test/
├── config/
│   ├── config.yaml
│   ├── prompts/
│   │   ├── step_1.txt     # Copied
│   │   ├── step_5.txt     # Copied
│   │   └── step_8.txt     # Copied
│   └── hitl/
│       └── expanded_spec.txt   # Always copied? Or referenced?
└── runs/
```

**config.yaml contains:**
```yaml
steps:
  - id: 1
    enabled: true
    name: "Service Design"
    prompt_file: "config/prompts/step_1.txt"
  - id: 5
    enabled: true
    name: "Communication"
    prompt_file: "config/prompts/step_5.txt"
  - id: 8
    enabled: true
    name: "Deployment"
    prompt_file: "config/prompts/step_8.txt"
```

**Is this correct?** (Y/N): _______________

**If N, describe what should be different:** _______________

---

**Scenario 3: Add Custom Step**

Researcher wants config set steps 1-3, plus custom security audit:

**Question I1.3a:** How should this be done?

**Option A - CLI Support:**
```bash
python scripts/new_experiment.py \
  --name test \
  --config-set microservices \
  --steps 1,2,3 \
  --custom-step id=99,prompt=my_prompts/security.txt,name="Security Audit"
```

**Option B - Manual Edit After Generation:**
```bash
# 1. Generate with base steps
python scripts/new_experiment.py \
  --name test \
  --config-set microservices \
  --steps 1,2,3

# 2. Manually edit test/config/config.yaml
# Add custom step:
steps:
  - id: 1
    ...
  - id: 2
    ...
  - id: 3
    ...
  - id: 99  # Manually added
    enabled: true
    name: "Security Audit"
    prompt_file: "my_prompts/security.txt"
```

**Option C - Interactive Wizard:**
```
$ python scripts/new_experiment.py --name test --config-set microservices
...
Add custom steps? (y/N): y
Custom step ID: 99
Custom step name: Security Audit
Custom step prompt file: my_prompts/security.txt
Add another? (y/N): n
```

**Your Preference:** _______________

**Rationale:** _______________

---

**Scenario 4: Reorder Steps**

Researcher wants to run step 3 before step 2:

**Question I1.4a:** Given your choice in G1.2 (execution order), how would user achieve this?

**If you chose "By ID (ascending)":**
- Can't reorder without changing IDs (problematic for metrics)

**If you chose "By declaration order":**
```yaml
steps:
  - id: 1
    enabled: true
  - id: 3     # Runs second
    enabled: true
  - id: 2     # Runs third
    enabled: true
```

**If you chose "Explicit order field":**
```yaml
steps:
  - id: 1
    order: 1
  - id: 3
    order: 2
  - id: 2
    order: 3
```

**Is this workflow acceptable for your research needs?** (Y/N): _______________

**If N, what would be better:** _______________

---

### I2. Config Set Creation Workflow

#### Q2.1: How do researchers create new config sets?

**Question I2.1a:** Should we provide tooling for config set creation?

**Option A - Manual (just documentation):**
```bash
# User manually creates:
mkdir -p config_sets/my_scenario/prompts
mkdir -p config_sets/my_scenario/hitl
# User creates metadata.yaml, experiment_template.yaml, etc.
```
- ✅ Simple, no tooling needed
- ❌ Error-prone, easy to get structure wrong

**Option B - Scaffolding CLI:**
```bash
python scripts/create_config_set.py \
  --name my_scenario \
  --description "My custom scenario" \
  --num-steps 5

# Creates skeleton:
config_sets/my_scenario/
├── metadata.yaml          # Pre-filled template
├── experiment_template.yaml
├── prompts/
│   ├── step_1.txt        # Placeholder
│   ├── step_2.txt
│   └── ...
└── hitl/
    └── expanded_spec.txt  # Placeholder
```
- ✅ Ensures correct structure
- ❌ Additional tooling to maintain

**Option C - Copy and Modify:**
```bash
python scripts/clone_config_set.py \
  --source default \
  --name my_scenario

# Copies default/, user modifies
```
- ✅ Easy for similar scenarios
- ❌ Might copy unwanted complexity

**Your Preference for V1:** _______________

**Your Preference for V2:** _______________

---

## 📋 PART J: Edge Cases and Error Handling

### J1. Validation and Error Scenarios

#### Q1.1: Step ID conflicts

**Question J1.1a:** User creates experiment with:
```yaml
steps:
  - id: 1
    prompt_file: "config/prompts/step_1.txt"
  - id: 1  # Duplicate ID!
    prompt_file: "my_prompts/alternative_step_1.txt"
```

**Should we:**
- [ ] **Reject:** Duplicate step IDs not allowed
- [ ] **Allow:** Last one wins (like dict keys)
- [ ] **Warn:** Allow but warn user

**Your Preference:** _______________

---

#### Q1.2: Missing prompt files during execution

**Question J1.2a:** Experiment starts running, step 5 prompt file is missing:

```bash
$ python scripts/run_experiment.py my_test
✓ Run 1/50 - Step 1: Service Design [COMPLETED - 45s]
✓ Run 1/50 - Step 5: Communication [ERROR: Prompt file not found]
```

**Should we:**

**Option A - Fail Entire Run:**
```
✗ Run 1/50 [FAILED]
Stopping experiment. Fix the issue and restart.
```

**Option B - Skip Step, Continue:**
```
⚠ Run 1/50 - Step 5: Skipped (prompt file not found)
✓ Run 1/50 - Step 8: Deployment [COMPLETED]
✓ Run 1/50 [COMPLETED with warnings]
```

**Option C - Prompt for Action:**
```
✗ Run 1/50 - Step 5: Prompt file not found

What would you like to do?
  1) Abort entire experiment
  2) Skip this step and continue
  3) Skip this step for all remaining runs
Choice [1]: _
```

**Your Preference:** _______________

---

#### Q1.3: Config set changes during experiment

**Question J1.3a:** Experiment is running, someone modifies the source config set:

```bash
# Terminal 1 - Running experiment (using microservices config set)
$ python scripts/run_experiment.py my_test
Running: Run 10/50...

# Terminal 2 - Someone modifies the config set
$ vim config_sets/microservices/prompts/step_1.txt
# Makes changes
```

**Should the running experiment:**

**Option A - Not affected (used copy):**
- Experiment copied prompts at generation time
- No impact from config set changes

**Option B - Picks up changes (used reference):**
- Experiment references config set
- Run 11/50 uses new prompt

**Option C - Detects change and warns:**
- Checksum validation detects change
- Prompts user about inconsistency

**Your Preference:** _______________

**How does this relate to your answer for C2.2 (copy vs reference)?** _______________

---

## 📋 PART K: Integration Specifics

### K1. StandaloneGenerator Changes

#### Q1.1: How should generator receive configuration?

**Question K1.1a:** Current generator is called like:
```python
generator = StandaloneGenerator(
    output_dir=output_path,
    base_spec=base_spec,
    # ... other params
)
```

**With config sets, should it be:**

**Option A - Config Set Name:**
```python
generator = StandaloneGenerator(
    output_dir=output_path,
    config_set="microservices",  # Looks up in registry
    enabled_steps=[1, 5, 8],
    # ... other params
)
```

**Option B - Config Set Path:**
```python
generator = StandaloneGenerator(
    output_dir=output_path,
    config_set_path="config_sets/microservices",
    enabled_steps=[1, 5, 8],
)
```

**Option C - Config Set Object:**
```python
config_set = ConfigSetLoader.load("microservices")
generator = StandaloneGenerator(
    output_dir=output_path,
    config_set=config_set,
    enabled_steps=[1, 5, 8],
)
```

**Your Preference:** _______________

**Rationale:** _______________

---

### K2. Runner Changes

#### Q2.1: How should runner discover steps?

**Question K2.1a:** Current runner has hardcoded `range(1, 7)`:

```python
# Current (hardcoded)
for step_num in range(1, 7):
    prompt = read_prompt(f"step_{step_num}.txt")
    run_step(step_num, prompt)
```

**With configurable steps, should it be:**

**Option A - Read from config.yaml:**
```python
# Load experiment config
config = load_config("config.yaml")

for step in config["steps"]:
    if step["enabled"]:
        step_id = step["id"]
        prompt_file = step["prompt_file"]
        prompt = read_prompt(prompt_file)
        run_step(step_id, prompt, step["name"])
```

**Option B - Use helper function:**
```python
enabled_steps = get_enabled_steps("config.yaml")
for step_info in enabled_steps:
    prompt = read_prompt(step_info.prompt_file)
    run_step(step_info.id, prompt, step_info.name)
```

**Option C - Iterator pattern:**
```python
step_runner = StepRunner(config_path="config.yaml")
for step in step_runner:
    step.execute()
```

**Your Preference:** _______________

---

## 📋 SUMMARY: Key Decisions Needed

Based on your initial answers, these are the critical questions that will shape implementation:

### 🔴 Critical (Must Answer):
1. **G1.2** - Execution order (by ID vs. declaration order vs. explicit)
2. **G2.1a** - What gets copied to generated experiment
3. **H1.1a** - How config set defines available steps
4. **H2.1a** - Whether template has default steps
5. **H2.2a** - What goes in template vs. experiment creation
6. **I1.1a** - Default behavior when using config set
7. **J1.3a** - Copy vs. reference prompts (impacts reproducibility)

### 🟡 Important (Should Answer):
8. **G1.1a** - Metric ID handling with gaps
9. **G1.3a** - Custom prompt validation strictness
10. **G3.1a** - How much source tracking in experiment
11. **H1.2a** - Step dependencies support
12. **I1.3a** - How to add custom steps
13. **J1.2a** - Error handling for missing prompts

### 🟢 Nice to Have (Can Decide Later):
14. **G2.2a** - HITL copy vs. reference
15. **I1.4a** - Step reordering workflow
16. **I2.1a** - Config set creation tooling
17. **J1.1a** - Duplicate step ID handling
18. **K1.1a** - Generator API design

---

## 📝 Next Steps

Please provide your answers to the questions above. Focus on:

1. **Critical decisions** (🔴) - These block implementation
2. **Workflow validation** (Part I) - Ensure the design works for your research
3. **Error handling philosophy** (Part J) - Determines system robustness

After your answers, I will:
1. Create consolidated design document
2. Update data models
3. Create detailed implementation plan
4. Show code examples for key components

---

## 💡 Reflection Questions (Optional but Helpful)

1. **What is the most common workflow you expect?**
   - Using config sets as-is? Customizing steps? Creating new config sets?

2. **What is more important?**
   - Flexibility (many options) vs. Simplicity (one clear way)

3. **Reproducibility concerns?**
   - Should experiments be 100% self-contained?
   - Or is referencing config sets acceptable?

4. **Timeline pressure?**
   - Need V1 quickly (simpler design)?
   - Or can take time for comprehensive solution?

**Your thoughts:** _______________

---

**Estimated Time to Answer Round 2:** 30-40 minutes  
**Impact:** This will finalize the implementation design! 🚀
