# Integrated Design Clarification: Config Sets + Configurable Steps

## 🎯 Purpose
Systematic clarification questions to ensure the integrated design meets your research needs.

**Date:** 2025-10-21  
**Status:** CLARIFICATION PHASE

---

## 📋 PART A: Config Set Architecture

### A1. Config Set Scope & Granularity

#### Q1.1: What exactly defines a unique "scenario"?
**Options:**
- [ ] **Problem Domain** (CRUD vs. Microservices vs. ML Pipeline)
- [ ] **Technology Stack** (FastAPI vs. Flask, SQLite vs. PostgreSQL)
- [ ] **Complexity Level** (Simple vs. Advanced)
- [ ] **Step Count** (3 steps vs. 6 steps vs. 10 steps)
- [X] **All of the above** (combination)

**Example Decision Impact:**
- If "technology stack" is part of scenario → Need config sets like `crud_fastapi`, `crud_flask`, `crud_django`
- If "complexity level" is part of scenario → Need config sets like `crud_simple`, `crud_advanced`

**Your Answer:** All of the above (combination). I think it's important to have config sets that can reflect different combinations of these factors to allow for comprehensive testing across various scenarios. It will be responsibility of the researchers to choose the appropriate config set that aligns with their experimental goals. You don't be afraid about redundancy in config sets as long as they serve distinct experimental purposes. It will be user's responsibility to choose the right config set for their experiments.

---

#### Q1.2: Should steps within a config set be fixed or flexible?
**Scenario:** `microservices` config set has 8 step prompts defined

**Option A - Fixed Steps:**
```yaml
# Config set defines exactly 8 steps, no more, no less
# Users can only enable/disable these 8
steps:
  - id: 1  # Must be step 1
  - id: 2  # Must be step 2
  # ... up to 8
```

**Option B - Flexible Steps:**
```yaml
# Config set provides step prompts, but users can:
# - Reorder steps
# - Add custom steps
# - Use only some steps
steps:
  - id: 1
    prompt_file: "config/prompts/step_1_service_design.txt"
  - id: 5  # User skips 2,3,4
    prompt_file: "config/prompts/step_5_communication.txt"
  - id: 99  # Custom step
    prompt_file: "my_custom_prompts/special_step.txt"
```

**Your Preference:** I liked the idea of flexible steps described directly in the experiment config yaml file. This allows researchers to tailor the workflow to their specific needs while still leveraging the predefined prompts in the config set. It provides the necessary flexibility for diverse experimental setups. So I prefer Option B - Flexible Steps. It's necessary highlight that this flexibility should be well-documented to avoid confusion among users. Another important point is in the generated experiment, just the steps and prompt files that are actually used should be included to keep things clean. In true, each generated experiment must deal with only its own scenario, so no need to include unused steps from the config set. The generated experiment should be as minimal as possible, containing only what is necessary for that specific run. The generated experiment should not have knowledge of other possible steps or scenarios available in the generator's config sets.

---

#### Q1.3: Config set step numbering - sequential or semantic?

**Option A - Sequential (1,2,3,...):**
```
microservices/prompts/
├── step_1.txt    # Service design
├── step_2.txt    # API gateway
├── step_3.txt    # User service
```
- ✅ Simple, consistent with current implementation
- ❌ Doesn't convey meaning

**Option B - Semantic (descriptive names):**
```
microservices/prompts/
├── step_1_service_design.txt
├── step_2_api_gateway.txt
├── step_3_user_service.txt
```
- ✅ Self-documenting
- ❌ Longer filenames

**Option C - Both (numbered + semantic):**
```
microservices/prompts/
├── 01_service_design.txt
├── 02_api_gateway.txt
├── 03_user_service.txt
```
- ✅ Sortable and descriptive
- ❌ Different from current pattern

**Your Preference:** _______________

---

### A2. Config Set Discovery & Management

#### Q2.1: Registry location - centralized or distributed?

**Option A - Centralized Registry:**
```
config_sets/
├── registry.yaml              # Single source of truth
├── default/
├── microservices/
└── ml_pipeline/
```
- ✅ Single source of truth
- ❌ Harder for external contributions

**Option B - Distributed (per-config-set metadata):**
```
config_sets/
├── default/
│   └── metadata.yaml          # Self-contained
├── microservices/
│   └── metadata.yaml
└── ml_pipeline/
    └── metadata.yaml
```
- ✅ Self-contained, easier for external config sets
- ❌ Need to scan all directories

**Option C - Hybrid (registry + metadata):**
```
config_sets/
├── registry.yaml              # Index only
├── default/
│   └── metadata.yaml          # Full details
```
- ✅ Best of both
- ❌ Duplication risk

**Your Preference:** _______________

---

#### Q2.2: External config sets - support or not?

**Question:** Should researchers be able to use config sets from outside the genai-devbench directory?

**Use Case 1:** Researcher has config sets in separate git repo
```bash
python scripts/new_experiment.py \
  --name my_exp \
  --config-set-path /path/to/external/microservices_v2
```

**Use Case 2:** Config set registry points to external locations
```yaml
# config_sets/registry.yaml
external_config_sets:
  microservices_v2:
    source: "git"
    url: "https://github.com/researcher/config-sets.git"
    path: "microservices_v2"
```

**Your Decision:**
- [ ] Support external config sets from V1
- [ ] Local only for V1, external in V2
- [ ] Never support external (security/complexity)

**Your Answer:** _______________

---

### A3. Config Set Content & Structure

#### Q3.1: What goes in experiment_template.yaml?

**Question:** Which configuration should be in the config set template vs. specified at experiment creation?

**Config Set Template (Fixed per scenario):**
- [ ] Steps configuration (enabled/disabled, names)
- [ ] Timeout values (step timeout, total timeout)
- [ ] Metrics configuration (weights, thresholds)
- [ ] Stopping rule defaults (confidence level, min/max runs)
- [ ] Framework-specific settings
- [ ] Pricing configuration

**Experiment Creation (User-specified):**
- [ ] Experiment name
- [ ] Model (gpt-4o-mini, o1-mini, etc.)
- [ ] Framework selection (which frameworks to test)
- [ ] Number of runs
- [ ] Random seed

**Your Assignment:** Mark which goes where above

---

#### Q3.2: HITL files - single or multiple per config set?

**Current:** Single `expanded_spec.txt` file

**Option A - Single HITL file:**
```
default/hitl/
└── expanded_spec.txt
```
- ✅ Simple
- ❌ Can't have different clarifications per framework

**Option B - Multiple HITL files:**
```
default/hitl/
├── expanded_spec.txt              # Default/global
├── baes_clarification.txt         # BAES-specific
├── chatdev_clarification.txt      # ChatDev-specific
└── ghspec_clarification.txt       # GHSpec-specific
```
- ✅ Framework-specific clarifications
- ❌ More complex

**Option C - Flexible (either):**
```yaml
# experiment_template.yaml
hitl:
  default: "config/hitl/expanded_spec.txt"
  framework_specific:
    baes: "config/hitl/baes_clarification.txt"
    ghspec: "config/hitl/ghspec_clarification.txt"
```

**Your Preference:** _______________

---

#### Q3.3: Should config sets include framework-specific prompts?

**Question:** Some frameworks might need different prompts for the same step

**Example:** Step 1 "Initial CRUD"
- BAES might need: "Create FastAPI CRUD with specific patterns"
- ChatDev might need: "Create CRUD application following ChatDev workflow"

**Option A - Shared prompts (current):**
```
default/prompts/
├── step_1.txt    # Same for all frameworks
├── step_2.txt
└── ...
```

**Option B - Framework-specific prompts:**
```
default/prompts/
├── shared/
│   ├── step_1.txt    # Default
│   └── step_2.txt
└── framework_overrides/
    ├── baes/
    │   └── step_1.txt    # BAES-specific override
    └── chatdev/
        └── step_1.txt    # ChatDev-specific override
```

**Option C - Separate config sets per framework:**
```
config_sets/
├── default_for_baes/
├── default_for_chatdev/
└── default_for_ghspec/
```

**Your Preference:** _______________

---

## 📋 PART B: Configurable Steps Integration

### B1. Step Configuration Source

#### Q1.1: Where do steps get configured - config set or experiment?

**Option A - Steps in Config Set (Template-driven):**
```yaml
# config_sets/default/experiment_template.yaml
steps:
  - id: 1
    enabled: true    # Config set decides defaults
    name: "Initial CRUD"
  - id: 2
    enabled: true
  # ...
```
Generated experiment inherits these, can override

**Option B - Steps in Experiment Only (User-driven):**
```yaml
# config_sets/default/experiment_template.yaml
# No steps section - just prompts available

# my_experiment/config.yaml
steps:
  - id: 1
    enabled: true    # User configures everything
  - id: 2
    enabled: false   # User decides
```

**Option C - Hybrid (Template + Override):**
```yaml
# Config set provides defaults
# Experiment can override per-step

# During generation:
"Do you want to use default step configuration? (Y/n)"
"Which steps do you want to enable? (1,2,3,4,5,6)"
```

**Your Preference:** _______________

---

#### Q1.2: Can users add custom steps beyond config set?

**Scenario:** Config set has 6 steps, user wants to add a 7th custom step

**Option A - Forbidden:**
- Config set defines all possible steps
- Users can only enable/disable

**Option B - Allowed:**
```yaml
steps:
  - id: 1
    enabled: true
    prompt_file: "config/prompts/step_1.txt"  # From config set
  - id: 7
    enabled: true
    prompt_file: "my_custom_prompts/custom_step.txt"  # Custom
```

**Your Preference:** _______________

---

### B2. Step Metadata & Naming

#### Q2.1: Step names - required or optional?

**Current Plan:** Optional (defaults to "Step {id}")

**Question:** Should step names be required in config sets?

**Option A - Required in Config Set:**
```yaml
# metadata.yaml
steps:
  1:
    name: "Initial CRUD Implementation"  # REQUIRED
    description: "Create basic entities..."
  2:
    name: "Add Enrollment"  # REQUIRED
```

**Option B - Optional Everywhere:**
```yaml
# Can omit names, use defaults
steps:
  - id: 1
    enabled: true
    # name defaults to "Step 1"
```

**Your Preference:** _______________

---

#### Q2.2: Step descriptions - needed?

**Question:** Besides name, do we need longer descriptions?

```yaml
# metadata.yaml
steps:
  1:
    name: "Initial CRUD"
    description: |
      Create a Student/Course/Teacher CRUD application 
      with Python, FastAPI, and SQLite. Include all 
      basic CRUD operations for each entity.
    estimated_duration: 300  # seconds
    complexity: "simple"
```

**Your Preference:**
- [ ] Just name (short)
- [ ] Name + description
- [ ] Name + description + metadata (duration, complexity, etc.)

**Your Answer:** _______________

---

## 📋 PART C: Experiment Generation Workflow

### C1. User Experience

#### Q1.1: Experiment generation - interactive or CLI-only?

**Current:** Supports both (wizard or CLI flags)

**Question:** For config set selection, which UX?

**Option A - Interactive Wizard:**
```
$ python scripts/new_experiment.py

Welcome to genai-devbench experiment generator!

Step 1: Select config set
  1. default - Student/Course/Teacher CRUD (6 steps)
  2. microservices - Microservices architecture (8 steps)
  3. ml_pipeline - ML training pipeline (5 steps)
  
Select config set [1]: 2

Step 2: Configure steps
Current config set has 8 steps:
  1. Service Design [enabled]
  2. API Gateway [enabled]
  3. User Service [enabled]
  ...
  
Keep all steps enabled? (Y/n): n
Which steps to enable? (1-8, comma-separated): 1,2,3,4,5

Step 3: Select frameworks...
```

**Option B - CLI Flags Only:**
```bash
python scripts/new_experiment.py \
  --name my_exp \
  --config-set microservices \
  --steps 1,2,3,4,5 \
  --frameworks baes,chatdev \
  --runs 50
```

**Option C - Both (support both workflows):**

**Your Preference:** _______________

---

#### Q1.2: Step configuration during generation - explicit or inherit?

**Question:** When creating experiment, how should steps be configured?

**Option A - Explicit (always ask/specify):**
```bash
python scripts/new_experiment.py \
  --config-set microservices \
  --enable-steps 1,2,3,4,5 \  # MUST specify
  --disable-steps 6,7,8
```

**Option B - Inherit with optional override:**
```bash
# Use all steps from config set (default)
python scripts/new_experiment.py --config-set microservices

# Override if needed
python scripts/new_experiment.py \
  --config-set microservices \
  --enable-steps 1,2,3,4,5
```

**Your Preference:** _______________

---

### C2. Generated Experiment Structure

#### Q2.1: Config set reference in generated experiment - how much info?

**Question:** What should be tracked about the source config set?

**Option A - Minimal (just name):**
```yaml
# my_experiment/config.yaml
config_set: "microservices"
```

**Option B - Full tracking:**
```yaml
# my_experiment/config.yaml
config_set:
  name: "microservices"
  version: "1.0.0"
  source_path: "../config_sets/microservices"
  generated_at: "2025-10-21T10:30:00Z"
  prompt_checksums:
    step_1: "abc123..."
    step_2: "def456..."
```

**Option C - Embedded (copy everything):**
```
my_experiment/
├── config.yaml
├── config_set_snapshot/      # Copy of entire config set
│   ├── metadata.yaml
│   ├── prompts/
│   └── hitl/
```

**Your Preference:** _______________

---

#### Q2.2: Prompts in generated experiment - copy or reference?

**Question:** Should prompts be copied to experiment or referenced from config set?

**Option A - Copy (self-contained):**
```
my_experiment/
├── config/
│   ├── prompts/
│   │   ├── step_1.txt    # Copied from config set
│   │   └── ...
```
- ✅ Self-contained, reproducible
- ❌ Uses more space, harder to update

**Option B - Reference (link to config set):**
```yaml
# my_experiment/config.yaml
prompts_source: "../config_sets/microservices/prompts"
```
- ✅ Space efficient, easy to update config set
- ❌ Not self-contained, breaks if config set moves

**Option C - Hybrid (reference with snapshot):**
- Reference config set during development
- Snapshot on finalization/archiving

**Your Preference:** _______________

---

## 📋 PART D: Multi-Config Set Experiments

### D1. Comparing Across Config Sets

#### Q1.1: Should we support comparing experiments with different config sets?

**Use Case:** Compare how frameworks perform on CRUD vs. Microservices

**Option A - Separate experiments:**
```
experiments/
├── crud_comparison/         # Config set: default
│   └── runs/
├── microservices_comparison/ # Config set: microservices
│   └── runs/
```
Manual comparison across experiments

**Option B - Multi-config-set experiment:**
```
experiments/
├── cross_scenario_comparison/
│   ├── config_sets_used/
│   │   ├── default/
│   │   └── microservices/
│   └── runs/
│       ├── baes_default_run1/
│       ├── baes_microservices_run1/
│       └── ...
```
Single experiment tests multiple scenarios

**Your Preference:** _______________

---

### D2. Config Set Evolution

#### Q1.1: Can experiments update their config set reference?

**Scenario:** Config set gets updated (improved prompts), should experiments pick up changes?

**Option A - Frozen at creation:**
- Experiment snapshots config set
- Never updates

**Option B - Can update manually:**
```bash
cd my_experiment
python scripts/update_config_set.py --config-set microservices
```

**Option C - Auto-update (dangerous):**
- Experiment always uses latest config set
- Could break reproducibility

**Your Preference:** _______________

---

## 📋 PART E: Implementation Strategy

### E1. Migration & Rollout

#### Q1.1: Big bang or phased rollout?

**Option A - Big Bang (V1 includes everything):**
- Config Set Management + Configurable Steps together
- Break current experiments, start fresh
- ~10-12 hours implementation

**Option B - Phased:**
- Phase 1: Config Set Management only (6 hours)
- Phase 2: Integrate Configurable Steps (4 hours)
- Allow testing between phases

**Your Preference:** _______________

---

#### Q1.2: Testing strategy - what config sets for initial release?

**Question:** Which config sets should we create for V1?

- [ ] `default` (current CRUD, 6 steps) - **MUST HAVE**
- [ ] `minimal` (1 step hello world) - **MUST HAVE** (for testing)
- [ ] `microservices` (8 steps) - Research scenario
- [ ] `ml_pipeline` (5 steps) - Research scenario
- [ ] `api_only` (4 steps, no UI) - Variation
- [ ] Other: _______________

**Your Priority (1=highest):** _______________

---

### E2. Validation & Quality

#### Q2.1: Validation strictness level?

**Question:** How strict should config set validation be?

**Option A - Strict:**
- All metadata fields required
- Prompt files must match naming pattern
- experiment_template.yaml must validate against schema
- Reject invalid config sets

**Option B - Lenient:**
- Only validate critical fields
- Allow flexible naming
- Warn but don't reject

**Your Preference:** _______________

---

#### Q2.2: Config set quality checks?

**Question:** Should we validate prompt file quality?

```python
# Example checks:
- Min/max prompt length (100 < chars < 5000)
- Required keywords (e.g., must mention "Python", "FastAPI")
- Semantic similarity across steps
- Grammar/spelling check
```

**Your Preference:**
- [ ] No quality checks (trust users)
- [ ] Basic checks (length, required fields)
- [ ] Advanced checks (grammar, semantic)

**Your Answer:** _______________

---

## 📋 PART F: Advanced Features (V1 or V2?)

### F1. Feature Prioritization

#### Q1.1: Which features for V1 vs. V2?

**Features:**

| Feature | V1 | V2 | Never |
|---------|----|----|-------|
| Basic config set system | ✅ | | |
| Configurable steps | ✅ | | |
| Registry-based discovery | ? | ? | ? |
| External config sets | ? | ? | ? |
| Config set versioning | ? | ? | ? |
| Config set inheritance | ? | ? | ? |
| Framework-specific prompts | ? | ? | ? |
| Multi-config-set experiments | ? | ? | ? |
| Config set marketplace/sharing | ? | ? | ? |
| GUI for config set creation | ? | ? | ? |
| Config set validation CLI | ? | ? | ? |

**Your V1/V2/Never assignments:** Fill in the table above

---

## 📋 SUMMARY: Action Items

After you answer these questions, I will:

1. **Consolidate answers** into a unified design document
2. **Create integrated implementation plan** (Config Sets + Configurable Steps)
3. **Define clear data models** for both features
4. **Specify API contracts** for all components
5. **Provide detailed subtasks** with code examples
6. **Create test plan** covering all scenarios
7. **Document migration path** from current system

---

## 📝 Your Answers

Please answer the questions above by:
1. Filling in blanks (_______________) 
2. Checking boxes ([x])
3. Selecting options (A, B, C, etc.)
4. Providing free-form text where indicated

**Estimated Time to Answer:** 20-30 minutes  
**Impact:** This will determine the entire implementation approach!

---

## 🎯 Priority Questions (if short on time, answer these first)

If you're short on time, prioritize answering:

1. **A1.1** - What defines a scenario? (Critical for architecture)
2. **A1.2** - Fixed or flexible steps? (Affects data model)
3. **A3.1** - What goes in template vs. experiment? (Core design)
4. **B1.1** - Steps in config set or experiment? (Integration point)
5. **C1.1** - Interactive or CLI-only? (UX design)
6. **C2.2** - Copy or reference prompts? (Storage strategy)
7. **E1.1** - Big bang or phased? (Implementation strategy)

Answer these 7, and I can make informed decisions on the rest! 🚀
