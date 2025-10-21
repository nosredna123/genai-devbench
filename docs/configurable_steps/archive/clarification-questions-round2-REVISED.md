# Round 2 Clarification: Deep Dive into Design Implications (REVISED)

## 🎯 Purpose
Based on your initial answers and the **two-stage architecture** clarification, this document explores the design decisions needed to implement the integrated Config Sets + Configurable Steps system.

**Date:** 2025-10-21  
**Status:** ROUND 2 CLARIFICATION (REVISED)

---

## 🏗️ **CRITICAL ARCHITECTURE UNDERSTANDING**

### Two Distinct Stages:

#### **Stage 1: Generator (genai-devbench repo)**
- Contains `config_sets/` with **curated scenarios**
- Config sets are **relatively fixed** (maintained by project)
- Generator creates initial experiment structure
- **Purpose:** Template library for common scenarios

#### **Stage 2: Generated Experiment (separate directory/repo)**
- Has its **own config.yaml** (copied from generator)
- Researcher can **freely modify** this config.yaml post-generation
- Can add/remove/reorder steps
- Can point to custom prompts
- **Purpose:** Researcher's flexible workspace

### Key Insight:
> "The generator will be responsible for generating an initial config of the generated experiment based on pre-configured scenarios. After that, in the generated experiment repo scope, the researcher can change the config file according to their interests."

**This means:**
- ✅ Config sets in generator = Curated templates
- ✅ Generated experiment = Independent, fully flexible
- ✅ No tension between "fixed" and "flexible" - they're different stages!

---

## 📊 Analysis of Your Round 1 Answers

### ✅ What We Know So Far:

**A1.1 - Scenario Definition:** "All of the above (combination)"
- Config sets can mix: domain + tech stack + complexity + step count
- Researcher responsibility to choose appropriate config set
- Redundancy acceptable if serving distinct experimental purposes

**A1.2 - Steps Flexibility:** "Option B - Flexible Steps"
- **At generation time:** Select which steps from config set
- **Post-generation:** Researcher can freely modify config.yaml
- Generated experiments should be minimal (only selected steps/prompts copied)
- Generated experiment is self-contained and independent

---

## 📋 PART G: Generator Stage - Selection & Creation

### G1. Step Selection During Generation

#### Q1.1: Default behavior when using config set

**Question G1.1a:** When researcher runs:
```bash
python scripts/new_experiment.py \
  --name my_test \
  --config-set microservices
```

**Should this:**

**Option A - Use All Steps by Default:** ✅ **[MY GUESS]**
```yaml
# Generated: my_test/config.yaml
steps:
  - id: 1
    enabled: true
    name: "Service Design"
    prompt_file: "config/prompts/step_1.txt"
  - id: 2
    enabled: true
    name: "API Gateway"
    prompt_file: "config/prompts/step_2.txt"
  # ... all 8 steps from config set
```
- ✅ Simple, works for most cases
- ✅ User can edit config.yaml to remove steps later
- Reasoning: Most users want all steps initially, can customize post-generation

**Option B - Prompt for Steps:**
```
$ python scripts/new_experiment.py --name test --config-set microservices
Config set 'microservices' has 8 steps. Which to enable?
  1) All (default)
  2) Custom selection
Choice [1]: _
```
- More interactive, but slower workflow

**Option C - Require Explicit Step Selection:**
```bash
python scripts/new_experiment.py \
  --name test \
  --config-set microservices \
  --steps all  # Required flag
```
- More explicit, but verbose for common case

**Your Preference:** A - use all steps by default

---

#### Q1.2: Selecting step subset during generation

**Question G1.2a:** When researcher wants only specific steps:
```bash
python scripts/new_experiment.py \
  --name my_test \
  --config-set microservices \
  --steps 1,5,8
```

**What gets generated?** ✅ **[MY GUESS: Copy only selected steps]**

```
my_test/
├── config/
│   ├── config.yaml
│   ├── prompts/
│   │   ├── step_1.txt     # Copied from config set
│   │   ├── step_5.txt     # Copied from config set
│   │   └── step_8.txt     # Copied from config set
│   └── hitl/
│       └── expanded_spec.txt   # Copied (always needed)
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

**Is this correct?** No. let's make it simpler by defaulting all steps to enabled true. The generator will copy ALWAYS all steps/prompts from the config set. The researcher can then edit config.yaml in the generated experiment to disable/remove any steps they don't want.

---

#### Q1.3: How config set defines available steps

**Question G1.3a:** What is the "contract" of a config set?

**Option A - Config Set Defines Available Steps:** ✅ **[MY GUESS]**
```yaml
# config_sets/microservices/metadata.yaml
name: "microservices"
description: "8-step microservices architecture"
available_steps:
  1:
    name: "Service Design"
    prompt_file: "prompts/step_1.txt"
    description: "Design service boundaries and responsibilities"
  2:
    name: "API Gateway"
    prompt_file: "prompts/step_2.txt"
    description: "Implement API gateway pattern"
  # ... up to 8
```
- ✅ Explicit catalog of available steps
- ✅ Generator can show menu during creation
- ✅ Validates that requested steps exist
- Reasoning: Clear contract, enables validation and interactive selection

**Option B - Config Set is Just a Directory:**
```
config_sets/microservices/
├── metadata.yaml          # Basic info only
├── prompts/
│   ├── step_1.txt
│   └── ...
```
- Simpler but no validation

**Option C - Hybrid (Catalog + Flexibility):**
```yaml
suggested_steps:  # Optional suggestions
  - id: 1
    name: "Service Design"
```
- More complex

**Your Preference:** A 

---

### G2. What Gets Copied to Generated Experiment

#### Q2.1: Prompt files - copy strategy

**Question G2.1a:** Should prompts be copied or referenced?

**Option A - Copy Only Selected Prompts:** ✅ **[MY GUESS]**
```
my_experiment/
├── config/
│   ├── config.yaml
│   └── prompts/
│       ├── step_1.txt      # Copied from config set
│       └── step_5.txt      # Copied from config set (only selected ones)
```
- ✅ Self-contained experiment
- ✅ Independent from generator changes
- ✅ Can be moved/archived without breaking
- ✅ Aligns with "minimal experiment" principle
- Reasoning: Generated experiment should be completely independent

**Option B - Reference Config Set:**
```yaml
# config.yaml
prompts_source: "../../config_sets/microservices/prompts"
```
- Breaks if config set moves

**Option C - Symlinks:**
```
prompts/ -> ../../config_sets/microservices/prompts/
```
- Fragile

**Your Preference:** A (copy all steps/prompts from the selected config set)

**Follow-up:** If config set changes after experiment generation, experiment is NOT affected (has its own copy). **Agree?** Y. We don't need traceability back to config set after generation. once generated, the experiment is independent.

---

#### Q2.2: HITL files - copy or reference?

**Question G2.2a:** HITL files (expanded_spec.txt) are typically large and shared across frameworks.

**Option A - Always Copy HITL:** ✅ **[MY GUESS]**
```
my_experiment/
├── config/
│   ├── config.yaml
│   ├── prompts/
│   └── hitl/
│       └── expanded_spec.txt  # Copied from config set
```
- ✅ Self-contained (consistent with prompt copy strategy)
- ✅ Experiment is independent
- ❌ Duplicates large files (but ensures reproducibility)
- Reasoning: Consistency with copy strategy, ensures reproducibility

**Option B - Reference HITL:**
```yaml
hitl:
  expanded_spec: "../../config_sets/microservices/hitl/expanded_spec.txt"
```
- Breaks independence

**Option C - Copy on Finalization:**
- Extra complexity

**Your Preference:** A (always copy HITL from the base config set)
---

#### Q2.3: Metadata tracking in generated experiment

**Question G2.3a:** Should generated experiment track its source?

**Option B - Source Reference Only:** ✅ **[MY GUESS]**
```yaml
# my_experiment/config.yaml
_metadata:
  generated_from: "microservices"  # Config set name
  generated_at: "2025-10-21T15:30:00Z"
  generator_version: "1.0.0"

steps:
  - id: 1
    enabled: true
    prompt_file: "config/prompts/step_1.txt"
```
- ✅ Traceable (know where it came from)
- ✅ Still independent (has copied files)
- ✅ Minimal metadata
- Reasoning: Good for documentation/reproducibility without violating independence

**Option A - Full Amnesia:**
```yaml
# No metadata at all
steps:
  - id: 1
```
- Lose traceability

**Option C - Immutable Snapshot:**
```yaml
_metadata:
  source_config_set:
    name: "microservices"
    version: "1.0.0"
    snapshot_hash: "abc123..."
```
- Too verbose

**Your Preference:** B (Full Amnesia. The generated experiment has no knowledge of its origin beyond copied files.)

---

## 📋 PART H: Generated Experiment - Post-Generation Flexibility

### H1. Step Configuration Flexibility

#### Q1.1: Execution order in generated experiment

**Question H1.1a:** After generation, researcher edits config.yaml. How is execution order determined?

**Option B - By Declaration Order:** ✅ **[MY GUESS]**
```yaml
steps:
  - id: 5    # Runs FIRST (declared first)
    enabled: true
  - id: 1    # Runs SECOND
    enabled: true
  - id: 99   # Runs THIRD (custom step researcher added)
    enabled: true
```
Executes as written in config.yaml: 5 → 1 → 99

- ✅ Intuitive (what you see is what you get)
- ✅ Easy to reorder (just move lines in YAML)
- ✅ Allows flexibility for custom workflows
- Reasoning: Researchers can easily control execution order by editing file

**Option A - By ID (ascending):**
```yaml
steps:
  - id: 5    # Runs SECOND (sorted by ID)
  - id: 1    # Runs FIRST
  - id: 99   # Runs THIRD
```
- Harder to control execution order

**Option C - Explicit order field:**
```yaml
steps:
  - id: 5
    order: 1
  - id: 1
    order: 2
```
- More verbose

**Your Preference:** B (By Declaration Order)

---

#### Q1.2: Adding custom steps post-generation

**Question H1.2a:** Researcher wants to add custom step after generation. How?

**Option B - Manual Edit After Generation:** ✅ **[MY GUESS]**
```bash
# 1. Generate experiment normally
python scripts/new_experiment.py \
  --name test \
  --config-set microservices \
  --steps 1,2,3

# 2. Researcher manually edits test/config/config.yaml
# Add custom step:
steps:
  - id: 1
    enabled: true
    name: "Service Design"
    prompt_file: "config/prompts/step_1.txt"
  - id: 2
    enabled: true
    name: "API Gateway"
    prompt_file: "config/prompts/step_2.txt"
  - id: 3
    enabled: true
    name: "User Service"
    prompt_file: "config/prompts/step_3.txt"
  - id: 99  # Manually added
    enabled: true
    name: "Security Audit"
    prompt_file: "my_custom_prompts/security.txt"

# 3. Create custom prompt file
mkdir -p test/my_custom_prompts
vim test/my_custom_prompts/security.txt

# 4. Run experiment
python scripts/run_experiment.py test
```

- ✅ Simple, no special generator support needed
- ✅ Aligns with "post-generation flexibility" principle
- ✅ Researcher has full control
- Reasoning: Generated experiment is just YAML, easy to edit manually

**Option A - CLI Support:**
```bash
python scripts/new_experiment.py \
  --custom-step id=99,prompt=my_prompts/security.txt
```
- Complicates generator

**Option C - Interactive Wizard:**
- Complicates UX

**Your Preference:** B (Manual Edit After Generation. Remember: in the generation process, the user will NOT be prompted to add custom steps. They can only do so after generation by editing config.yaml manually. The generator should remain simple and always copy all steps/prompts from the selected config set.)

---

#### Q1.3: Step ID handling in metrics

**Question H1.3a:** If researcher has steps with IDs 1, 5, 99, how should metrics track them?

**Option C - Dual Tracking:** ✅ **[MY GUESS]**
```python
# In metrics/reports:
{
  "step_id": 1,           # Original ID from config
  "step_index": 1,        # Execution order (1st, 2nd, 3rd)
  "step_name": "Service Design",
  "duration": 45.2
}
{
  "step_id": 5,           # Original ID
  "step_index": 2,        # Second step executed
  "step_name": "Communication",
  "duration": 32.1
}
{
  "step_id": 99,          # Custom step ID
  "step_index": 3,        # Third step executed
  "step_name": "Security Audit",
  "duration": 28.5
}
```

- ✅ Preserves semantic meaning (original ID)
- ✅ Clean sequential reports (execution order)
- ✅ Both metrics available for analysis
- Reasoning: Best of both worlds, enables flexible analysis

**Option A - Original IDs only:**
- Reports have gaps (1, 5, 99)

**Option B - Sequential only:**
- Loses original step meaning

**Your Preference:** A (Preserve Original IDs Only. Metrics should reflect the actual step IDs as defined in config.yaml, even if non-sequential. Researchers can interpret gaps as needed.)

---

### H2. Validation and Error Handling

#### Q2.1: Missing prompt files during execution

**Question H2.1a:** Researcher edits config.yaml to add custom step but forgets to create prompt file:

```bash
$ python scripts/run_experiment.py my_test
✓ Run 1/50 - Step 1: Service Design [COMPLETED - 45s]
✓ Run 1/50 - Step 5: Communication [COMPLETED - 32s]
✗ Run 1/50 - Step 99: Security Audit [ERROR: Prompt file not found]
```

**Option A - Fail Entire Run:** ✅ **[MY GUESS]**
```
✗ Run 1/50 [FAILED]
ERROR: Prompt file not found: my_custom_prompts/security.txt
Stopping experiment. Fix the issue and restart.
```
- ✅ Catches errors immediately
- ✅ Prevents wasted computation
- ✅ Clear error message
- Reasoning: Fail fast to prevent confusion and wasted resources

**Option B - Skip Step, Continue:**
```
⚠ Run 1/50 - Step 99: Skipped (prompt file not found)
✓ Run 1/50 [COMPLETED with warnings]
```
- Silently continues, might miss issue

**Option C - Prompt for Action:**
- Complicates automation

**Your Preference:** A (Fail fast always! You must consider the "fail fast" as a core principle to avoid wasted runs and confusion.)
---

#### Q2.2: Duplicate step IDs

**Question H2.2a:** Researcher accidentally creates duplicate IDs:
```yaml
steps:
  - id: 1
    prompt_file: "config/prompts/step_1.txt"
  - id: 1  # Duplicate!
    prompt_file: "my_prompts/alternative_step_1.txt"
```

**Option: Reject** ✅ **[MY GUESS]**
```bash
$ python scripts/run_experiment.py my_test
ERROR: Duplicate step ID found: 1
Please ensure all step IDs are unique in config.yaml
```
- ✅ Clear error message
- ✅ Prevents ambiguity
- Reasoning: Duplicate IDs would cause confusion in metrics/reporting

**Your Preference:** Reject (fail fast on duplicates)

---

## 📋 PART I: Config Set Template Structure

### I1. experiment_template.yaml Content

#### Q1.1: What should be in the template?

**Question I1.1a:** Should experiment_template.yaml include default steps?

**Option A - Template Has Default Steps:** ✅ **[MY GUESS]**
```yaml
# config_sets/microservices/experiment_template.yaml

# Default steps configuration (all enabled by default)
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

# Other scenario-specific defaults
timeout:
  per_step: 600
  total: 7200

metrics:
  weights:
    correctness: 0.4
    performance: 0.3
    code_quality: 0.3
```

**During generation with --steps flag:**
```bash
python scripts/new_experiment.py \
  --name test \
  --config-set microservices \
  --steps 1,5,8
```
Generator filters template steps to include only 1,5,8 in generated config.yaml

- ✅ Provides good defaults
- ✅ Generator can filter based on --steps flag
- ✅ Easy for users to understand what's available
- Reasoning: Template shows full scenario, generator customizes on creation

**Option B - Template Has No Steps:**
- Template incomplete, harder to understand

**Option C - Template References Metadata:**
- Indirect, more complex

**Your Preference:** A (the generator will always copy all steps/prompts from the selected config set. The researcher can then edit config.yaml in the generated experiment to disable/remove any steps they don't want independently after generation.)
---

#### Q1.2: Configuration ownership

**Question I1.2a:** For each configuration item, mark where it should be defined:

| Configuration | Config Set Template | Experiment Creation | Both (template default, user can override) |
|---------------|---------------------|---------------------|-------------------------------------------|
| Steps (default enabled/disabled) | X | | ✅ **[MY GUESS]** |
| Step names | X | | |
| Step timeout (max time per step) | X | | ✅ **[MY GUESS]** |
| Total experiment timeout | X | | ✅ **[MY GUESS]** |
| Metrics weights | X | | ✅ **[MY GUESS]** |
| Stopping rule (confidence level) | X | | ✅ **[MY GUESS]** |
| Max/Min runs | | X | ✅ **[MY GUESS]** |
| Model (gpt-4o-mini, o1-mini) | | X | |
| Frameworks to test | | X | |
| Temperature | | X | ✅ **[MY GUESS]** |
| Random seed | | X | |
| Experiment name | | X | |
| Output directory | | X | |

**Rationale:** 
- Scenario-specific settings (timeouts, metrics weights) → Template defaults
- User-specific settings (model, frameworks, runs) → Experiment creation
- Most can be overridden post-generation by editing config.yaml

**Your Adjustments:** the generated experiment has no knowledge of its origin beyond copied files. it must know nothing about the config set after generation. Only the needed configuration items are copied over and duplicated in the generated experiment's config.yaml. The researcher can then modify freely.

---

### I2. Config Set Metadata Structure

#### Q2.1: Step naming convention in config set

**Question I2.1a:** Prompt file naming in config sets:

**Option C - Both (numbered + semantic):** ✅ **[MY GUESS]**
```
config_sets/microservices/prompts/
├── 01_service_design.txt
├── 02_api_gateway.txt
├── 03_user_service.txt
├── 04_order_service.txt
├── 05_communication.txt
├── 06_database_design.txt
├── 07_deployment.txt
└── 08_monitoring.txt
```

- ✅ Self-documenting (semantic names)
- ✅ Sortable (numeric prefix)
- ✅ Clear step order
- Reasoning: Best of both worlds - files naturally sort by step order and convey meaning

**Option A - Sequential only:**
```
step_1.txt, step_2.txt, ...
```
- Not self-documenting

**Option B - Semantic only:**
```
service_design.txt, api_gateway.txt, ...
```
- Harder to see natural order

**Your Preference:** C

---

#### Q2.2: Step dependencies in config set

**Question I2.2a:** Should config sets support step dependencies?

**Option A - No Dependencies:** ✅ **[MY GUESS]**
```yaml
# config_sets/microservices/metadata.yaml
available_steps:
  1:
    name: "Service Design"
  5:
    name: "Communication"
    # No dependency tracking
```

User's responsibility to ensure logical flow when selecting steps.

- ✅ Simple, no validation complexity
- ✅ Researchers know their requirements
- ✅ Maximum flexibility
- Reasoning: V1 should be simple, dependencies can be added in V2 if needed

**Option B - Warn on Dependencies:**
- More complex

**Option C - Enforce Dependencies:**
- Too restrictive

**Your Preference:** A

---

## 📋 PART J: Config Set Discovery & Management

### J1. Registry and Discovery

#### Q1.1: Registry structure

**Question J1.1a:** How should config sets be discovered?

**Option B - Distributed (per-config-set metadata):** ✅ **[MY GUESS]**
```
config_sets/
├── default/
│   ├── metadata.yaml          # Self-contained
│   ├── experiment_template.yaml
│   ├── prompts/
│   └── hitl/
├── microservices/
│   ├── metadata.yaml          # Self-contained
│   ├── experiment_template.yaml
│   ├── prompts/
│   └── hitl/
└── ml_pipeline/
    ├── metadata.yaml
    ├── experiment_template.yaml
    ├── prompts/
    └── hitl/
```

Generator scans config_sets/ directory, reads each metadata.yaml to discover available config sets.

- ✅ Self-contained (each config set has own metadata)
- ✅ Easy to add new config sets (just add directory)
- ✅ Easy for external contributions (copy directory)
- ✅ No central registry to keep in sync
- Reasoning: Simpler, more maintainable, easier for users to add custom config sets

**Option A - Centralized Registry:**
```
config_sets/
├── registry.yaml  # Must keep in sync
├── default/
└── microservices/
```
- Extra maintenance

**Option C - Hybrid:**
- More complex

**Your Preference:** B

---

#### Q1.2: External config sets

**Question J1.2a:** Should users be able to use config sets from outside genai-devbench directory?

**Option: Local only for V1, external in V2** ✅ **[MY GUESS]**

**V1 Behavior:**
```bash
# Only local config sets
python scripts/new_experiment.py \
  --name test \
  --config-set microservices  # Must exist in config_sets/
```

**V2 Future Enhancement:**
```bash
# Support external path
python scripts/new_experiment.py \
  --name test \
  --config-set-path /path/to/external/my_scenario
```

- ✅ V1 stays simple
- ✅ V2 can add external support if needed
- Reasoning: Start simple, add features based on user demand

**Your Preference:** Just local. Let's keep it simple for V1. External config sets can be a future enhancement if there's demand.

---

### J2. Config Set Creation

#### Q2.1: Tooling for creating new config sets

**Question J2.1a:** How should users create new config sets?

**V1 Preference: Option A - Manual** ✅ **[MY GUESS]**
```bash
# User manually creates structure:
mkdir -p config_sets/my_scenario/prompts
mkdir -p config_sets/my_scenario/hitl

# Copy example metadata.yaml and edit
cp config_sets/default/metadata.yaml config_sets/my_scenario/
vim config_sets/my_scenario/metadata.yaml

# Create prompts
vim config_sets/my_scenario/prompts/01_initial_step.txt
# ...
```

Provide good documentation and example config sets to copy from.

- ✅ Simple, no tooling to maintain
- ✅ Users have full control
- ✅ Can follow examples
- Reasoning: V1 focus on core features, tooling can come later

**V2 Preference: Option C - Copy and Modify**
```bash
python scripts/clone_config_set.py \
  --source default \
  --name my_scenario
```
- Easier for users in V2

**Your Preference V1:** A
**Your Preference V2:** C, in future versions we can add a CLI tool to clone and modify existing config sets to create new ones more easily. But for V1, let's keep it manual with good documentation. Let's focus on getting the core functionality right first.

---

## 📋 PART K: Integration & Implementation

### K1. Generator API Design

#### Q1.1: How should generator receive configuration?

**Question K1.1a:** Generator API design:

**Option C - Config Set Object:** ✅ **[MY GUESS]**
```python
# In new_experiment.py CLI:

# 1. Load config set
config_set = ConfigSetLoader.load("microservices")

# 2. Filter steps if specified
if args.steps:
    selected_steps = parse_steps(args.steps)  # "1,5,8" -> [1, 5, 8]
    config_set.filter_steps(selected_steps)

# 3. Create generator
generator = StandaloneGenerator(
    output_dir=output_path,
    config_set=config_set,  # Rich object with all config set data
    # Other params from CLI
)

# 4. Generate experiment
generator.generate()
```

- ✅ Clean separation of concerns
- ✅ ConfigSetLoader handles validation
- ✅ Generator receives validated object
- ✅ Testable (can mock ConfigSet)
- Reasoning: Clean architecture, easy to test and maintain

**Option A - Config Set Name:**
```python
generator = StandaloneGenerator(
    config_set="microservices",  # String lookup
)
```
- Generator does too much

**Option B - Config Set Path:**
```python
generator = StandaloneGenerator(
    config_set_path="config_sets/microservices",
)
```
- Less flexible

**Your Preference:** C

---

### K2. Runner Implementation

#### Q2.1: How should runner discover steps?

**Question K2.1a:** Runner implementation:

**Option B - Use helper function:** ✅ **[MY GUESS]**
```python
# In runner code:

# Load enabled steps from experiment's config.yaml
enabled_steps = get_enabled_steps("my_experiment/config/config.yaml")

# enabled_steps is list of StepInfo objects:
# [
#   StepInfo(id=1, name="Service Design", prompt_file="config/prompts/step_1.txt"),
#   StepInfo(id=5, name="Communication", prompt_file="config/prompts/step_5.txt"),
# ]

for step_info in enabled_steps:
    prompt = read_prompt(step_info.prompt_file)
    result = run_step(step_info.id, prompt, step_info.name)
    record_metrics(step_info.id, step_info.index, result)
```

- ✅ Clean, simple, testable
- ✅ Helper function handles complexity (parsing, filtering, ordering)
- ✅ Runner logic stays focused
- Reasoning: Clean separation, easy to test helper function independently

**Option A - Read directly:**
```python
config = load_config("config.yaml")
for step in config["steps"]:
    if step["enabled"]:
        ...
```
- More verbose in runner

**Option C - Iterator pattern:**
```python
step_runner = StepRunner(config_path="config.yaml")
for step in step_runner:
    step.execute()
```
- Over-engineered for V1

**Your Preference:** B 

---

## 📋 PART L: Testing & Validation

### L1. Initial Config Sets for V1

**Question L1.1:** Which config sets should we create for V1?

✅ **[MY GUESS: Priority ranking]**

1. **Priority 1 (Must Have):**
   - [X] `default` - Current CRUD scenario (6 steps: Student/Course/Teacher)
   - [X] `minimal` - 1 step hello world (for testing/validation)

2. **Priority 2 (Nice to Have for V1):**
   - [ ] `microservices` - 8 step microservices architecture
   - [ ] `api_only` - 4 steps, REST API without UI

3. **Priority 3 (V2):**
   - [ ] `ml_pipeline` - 5 steps, ML training pipeline
   - [ ] `crud_advanced` - 8+ steps with authentication, authorization

**Rationale:** 
- `default` is required for compatibility testing
- `minimal` is essential for validation and quick tests
- Others can be added incrementally based on research needs

**Your Priority Ranking:** 1. default and minimal first, others later as needed.

---

### L2. Validation Strictness

#### Q2.1: Config set validation level

**Question L2.1a:** How strict should config set validation be?

**Option A - Strict:** ✅ **[MY GUESS]**
```python
# Validation rules:
- metadata.yaml must exist and be valid
- experiment_template.yaml must exist and be valid
- All referenced prompt files must exist
- available_steps must match prompt files
- HITL directory must exist (can be empty)
- Step IDs must be unique
```

Generator rejects invalid config sets with clear error messages.

- ✅ Catches errors early
- ✅ Ensures quality
- ✅ Clear error messages guide users
- Reasoning: Config sets are curated templates, should be high quality

**Option B - Lenient:**
- Allows broken config sets

**Your Preference:** A 

---

#### Q2.2: Prompt file quality checks

**Question L2.2a:** Should we validate prompt content?

**Option: Basic checks only** ✅ **[MY GUESS]**
```python
# V1 validation:
- Prompt file exists
- Prompt file is not empty
- Prompt file is readable text

# NOT in V1:
- Grammar/spelling check
- Semantic analysis
- Required keywords
```

- ✅ Catches obvious errors
- ✅ Simple to implement
- ✅ Fast validation
- Reasoning: V1 should validate structure, not content quality

**Your Preference:** Basic checks only

---

## 📋 PART M: Implementation Strategy

### M1. Rollout Approach

#### Q1.1: Big bang or phased?

**Question M1.1a:** Implementation approach:

**Option A - Big Bang (V1 includes everything):** ✅ **[MY GUESS]**

**V1 Scope:**
- Config Set Management (directory structure, metadata, discovery)
- Configurable Steps (flexible step configuration)
- Generator integration (--config-set, --steps flags)
- Runner integration (read steps from config.yaml)
- Validation (config set and step validation)
- Documentation (how to create config sets, use steps)

**Timeline:** ~12-16 hours implementation

**Rationale:**
- Features are tightly coupled
- Clean break from old system (you said no backwards compatibility)
- Can test end-to-end immediately
- Simpler than coordinating phased releases

**Option B - Phased:**
- More complex coordination

**Your Preference:** A 

---

### M2. Migration Path

#### Q2.1: Migrating current experiments

**Question M2.1a:** What happens to current experiments?

✅ **[MY GUESS: Clean break]**

**Approach:**
1. Current experiments in `experiments/` stay as-is (can still run with old code if needed)
2. Create new `config_sets/default/` that replicates current scenario
3. All NEW experiments use new system
4. Document migration: "To recreate old experiment, use --config-set default --steps all"

**No migration tool needed** - You said "we will restart the experiment freshly"

**Your Preference:** Clean break. No worries about migrating old experiments. New experiments start fresh with the new config set system.

---

## 📋 SUMMARY: Key Decisions for Validation

### 🔴 Critical Decisions (Need Your Confirmation):

1. **G1.1a** - Default: Use all steps from config set ✅ **[Option A]**
2. **G2.1a** - Copy only selected prompts to experiment ✅ **[Option A]**
3. **G2.2a** - Always copy HITL files ✅ **[Option A]**
4. **G2.3a** - Track source with minimal metadata ✅ **[Option B]**
5. **H1.1a** - Execution order by declaration order ✅ **[Option B]**
6. **H1.2a** - Add custom steps via manual editing ✅ **[Option B]**
7. **H1.3a** - Dual tracking (ID + index) for metrics ✅ **[Option C]**
8. **I1.1a** - Template has default steps ✅ **[Option A]**
9. **I2.1a** - Numbered + semantic filenames ✅ **[Option C]**
10. **J1.1a** - Distributed metadata (no central registry) ✅ **[Option B]**
11. **K1.1a** - Generator receives ConfigSet object ✅ **[Option C]**
12. **K2.1a** - Runner uses helper function ✅ **[Option B]**
13. **M1.1a** - Big bang implementation ✅ **[Option A]**

### ✅ My Understanding:

**Two-Stage Architecture:**
- **Generator stage:** Select from curated config sets → Generate minimal experiment
- **Experiment stage:** Freely edit config.yaml → Full flexibility post-generation

**Copy Strategy:**
- Prompts: Copy only selected ones
- HITL: Copy (self-contained)
- Experiment is independent after generation

**Flexibility:**
- Declaration order determines execution
- Easy to add/remove/reorder steps by editing YAML
- Dual tracking for metrics (original ID + execution index)

**Simplicity:**
- No central registry (scan directories)
- No dependencies in V1
- Manual config set creation with good docs
- Basic validation only

---

## 📝 Your Action Items

Please review my guesses above and:

1. **Validate** decisions marked with ✅ **[MY GUESS]**
2. **Correct** any wrong assumptions
3. **Clarify** any ambiguities
4. **Add** any missing requirements

**Format:**
- ✅ Agree with G1.1a
- ❌ Change H1.2a to Option A because...
- ℹ️ Add requirement: ...

After validation, I will create:
1. Consolidated design document
2. Updated data models
3. Detailed implementation plan
4. Code examples

---

**Estimated Review Time:** 15-20 minutes  
**Impact:** Your validation will finalize the design! 🚀
