# Quickstart: Configurable Steps

## 🚀 Quick Start Guide

Get up and running with configurable steps in 5 minutes.

---

## What is Configurable Steps?

Configurable Steps allows you to **enable/disable individual development steps** in your experiment workflow, giving you flexibility to:
- ✅ Test partial workflows (e.g., only steps 1-3)
- ✅ Skip specific steps
- ✅ Reduce costs for iterative testing
- ✅ Debug specific steps in isolation

---

## Basic Example

### Default (All Steps Enabled)

By default, all 6 steps are enabled:

```yaml
# config.yaml (auto-generated)
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD Implementation"
    
  - id: 2
    enabled: true
    name: "Add Enrollment Relationship"
    
  # ... steps 3-6 all enabled: true
```

### Skip UI Step (Step 6)

Want to test backend-only? Just disable step 6:

```yaml
steps:
  - id: 6
    enabled: false  # ← Just change this!
    name: "User Interface"
```

### Test First 3 Steps Only

Testing early development phases:

```yaml
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD Implementation"
    
  - id: 2
    enabled: true
    name: "Add Enrollment Relationship"
    
  - id: 3
    enabled: true
    name: "Teacher Assignment"
    
  - id: 4
    enabled: false  # ← Disable steps 4-6
    
  - id: 5
    enabled: false
    
  - id: 6
    enabled: false
```

---

## Step-by-Step Tutorial

### 1. Generate New Experiment

```bash
python scripts/new_experiment.py \
  --name my_experiment \
  --model gpt-4o-mini \
  --frameworks baes,chatdev,ghspec \
  --runs 5
```

### 2. Edit config.yaml

Open `my_experiment/config.yaml` and find the `steps:` section:

```yaml
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD Implementation"
    prompt_file: "config/prompts/step_1.txt"
    
  - id: 2
    enabled: true
    name: "Add Enrollment Relationship"
    prompt_file: "config/prompts/step_2.txt"
  
  # ... more steps
```

### 3. Customize Steps

**Example:** Skip step 3 (Teacher Assignment):

```yaml
  - id: 3
    enabled: false  # ← Change true to false
    name: "Teacher Assignment"
    prompt_file: "config/prompts/step_3.txt"
```

### 4. Run Experiment

```bash
cd my_experiment
./run.sh
```

### 5. See Results

Terminal output will show:

```
[1/15] BAES - Run 1/5 | ID: run_20251021_103045 | 10:30:45
        ⋯ Step 1/5 (#1: Initial CRUD Implementation) | 10:30:46
        ⋯ Step 2/5 (#2: Add Enrollment Relationship) | 10:35:12
        ⋯ Step 3/5 (#4: Validation & Error Handling) | 10:42:33  ← Skipped #3!
        ⋯ Step 4/5 (#5: Pagination & Filtering) | 10:50:18
        ⋯ Step 5/5 (#6: User Interface) | 10:58:45
```

Notice:
- Shows "Step 1/5" (5 enabled steps, not 6)
- Shows original step IDs in parentheses (#4, not #3)
- Clearly skipped step 3

---

## Common Use Cases

### Use Case 1: Backend Testing Only

```yaml
# Disable UI step
steps:
  - id: 6
    enabled: false
```

**Why:** Test API development without UI complexity

---

### Use Case 2: Early Development Testing

```yaml
# Enable only steps 1-3
steps:
  - id: 4
    enabled: false
  - id: 5
    enabled: false
  - id: 6
    enabled: false
```

**Why:** Test basic CRUD before advanced features

---

### Use Case 3: Skip Problematic Step

```yaml
# Skip step that's causing issues
steps:
  - id: 3
    enabled: false
```

**Why:** Isolate and debug specific step issues

---

### Use Case 4: Minimal Test

```yaml
# Only step 1
steps:
  - id: 1
    enabled: true
  - id: 2
    enabled: false
  - id: 3
    enabled: false
  - id: 4
    enabled: false
  - id: 5
    enabled: false
  - id: 6
    enabled: false
```

**Why:** Quick smoke test, minimal cost

---

## Configuration Fields

### Required Fields

```yaml
- id: 1          # Step number (1-6)
  enabled: true  # true or false
```

### Optional Fields

```yaml
- id: 1
  enabled: true
  name: "Custom Step Name"                    # Optional: Descriptive name
  prompt_file: "config/prompts/custom.txt"    # Optional: Custom prompt file
```

---

## Step Descriptions

| Step | Name | Description |
|------|------|-------------|
| 1 | Initial CRUD | Create basic Student/Course/Teacher CRUD with FastAPI |
| 2 | Enrollment | Add Student-Course enrollment relationship |
| 3 | Teacher Assignment | Add Teacher-Course assignment relationship |
| 4 | Validation | Add input validation and error handling |
| 5 | Pagination | Add pagination and filtering to endpoints |
| 6 | User Interface | Create web UI for CRUD operations |

---

## Validation Rules

✅ **Valid Configurations:**
- At least 1 step enabled
- Step IDs between 1-6
- Unique step IDs
- Prompt files exist

❌ **Invalid Configurations:**
- All steps disabled → **Error:** "No steps enabled"
- Step ID 0 or 7+ → **Error:** "Step ID must be 1-6"
- Duplicate IDs → **Error:** "Duplicate step IDs"
- Missing prompt file → **Error:** "Prompt file not found"

---

## Troubleshooting

### Error: "No steps enabled"

**Problem:** All steps have `enabled: false`

**Solution:** Enable at least one step:
```yaml
- id: 1
  enabled: true  # ← Change to true
```

---

### Error: "Step ID must be 1-6"

**Problem:** Invalid step ID

**Solution:** Use valid IDs (1-6):
```yaml
- id: 10  # ❌ Invalid
  ↓
- id: 1   # ✅ Valid
```

---

### Error: "Prompt file not found"

**Problem:** Custom prompt file doesn't exist

**Solution:** 
1. Create the file, or
2. Remove `prompt_file` field (uses default):
```yaml
- id: 1
  enabled: true
  prompt_file: "nonexistent.txt"  # ❌ Doesn't exist
  ↓
- id: 1
  enabled: true
  # Uses default: config/prompts/step_1.txt ✅
```

---

### Warning: "Non-sequential steps"

**Problem:** Enabled steps not sequential (e.g., 1,3,5)

**Impact:** May work, but steps might have dependencies

**Solution:** If you see issues, enable missing steps:
```yaml
# Enabled: 1, 3, 5 (skipped 2, 4)
# → May cause issues if step 3 depends on step 2

# Better: Enable 1-5 or 1-3
```

---

## Best Practices

### ✅ DO:
- Start with all steps enabled (default)
- Disable steps one at a time
- Test incremental step subsets (1-2, then 1-3, etc.)
- Document why you disabled specific steps

### ❌ DON'T:
- Skip early steps (e.g., disable step 1)
- Enable only late steps (e.g., only step 6)
- Disable steps with unclear dependencies

---

## Examples

### Example 1: Complete Config

```yaml
steps:
  - id: 1
    enabled: true
    name: "Initial CRUD Implementation"
    prompt_file: "config/prompts/step_1.txt"
    
  - id: 2
    enabled: true
    name: "Add Enrollment Relationship"
    prompt_file: "config/prompts/step_2.txt"
    
  - id: 3
    enabled: false  # Skip teacher assignment
    name: "Teacher Assignment"
    prompt_file: "config/prompts/step_3.txt"
    
  - id: 4
    enabled: true
    name: "Validation & Error Handling"
    prompt_file: "config/prompts/step_4.txt"
    
  - id: 5
    enabled: true
    name: "Pagination & Filtering"
    prompt_file: "config/prompts/step_5.txt"
    
  - id: 6
    enabled: false  # Skip UI
    name: "User Interface"
    prompt_file: "config/prompts/step_6.txt"
```

**Result:** Executes steps 1, 2, 4, 5 (skips 3 and 6)

---

### Example 2: Minimal Config

```yaml
steps:
  - id: 1
    enabled: true
  - id: 2
    enabled: true
  - id: 3
    enabled: true
  - id: 4
    enabled: false
  - id: 5
    enabled: false
  - id: 6
    enabled: false
```

**Result:** Executes only steps 1-3 (uses default names/prompts)

---

### Example 3: Custom Prompts

```yaml
steps:
  - id: 1
    enabled: true
    name: "Custom CRUD Task"
    prompt_file: "config/prompts/custom_step_1.txt"  # Custom prompt!
```

**Result:** Executes step 1 with custom prompt file

---

## Next Steps

1. ✅ **Read:** [Feature Specification](feature-spec.md)
2. ✅ **Explore:** [Data Model](data-model.md)
3. ✅ **Review:** [API Contracts](contracts/api-contracts.md)
4. ✅ **Implement:** [Implementation Plan](implementation-plan.md)

---

## FAQ

### Q: Can I add custom steps beyond 1-6?
**A:** Not in v1.0. Current limit is steps 1-6 (based on existing prompts).

### Q: Can different frameworks run different steps?
**A:** No. All frameworks run the same steps to ensure fair comparison.

### Q: What happens to metrics for skipped steps?
**A:** No metrics recorded for skipped steps. Only executed steps appear in results.

### Q: Can I reorder steps?
**A:** No. Steps always execute in ID order (1 → 2 → 3... skipping disabled).

### Q: Do I need to regenerate my experiment?
**A:** No. Existing experiments auto-apply defaults (all 6 steps enabled).

### Q: Can I have multiple step configurations?
**A:** No. One global configuration per experiment (ensures fair comparison).

---

## Support

- **Documentation:** `docs/configurable_steps/`
- **Issues:** GitHub Issues
- **Examples:** `docs/configurable_steps/examples.md`

---

**Quick Reference:**

```yaml
# Minimal valid config
steps:
  - id: 1
    enabled: true
  # ... more steps

# Required fields: id, enabled
# Optional fields: name, prompt_file
# At least 1 step must be enabled
# Step IDs: 1-6 only
```

---

**Ready to start? Edit your `config.yaml` and run your experiment! 🚀**
