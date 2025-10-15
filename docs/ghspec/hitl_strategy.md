# GHSpec HITL Strategy

## Overview

This document explains why GHSpec uses a different HITL (Human-in-the-Loop) approach than ChatDev and BAEs adapters.

## The Problem

All frameworks in this experiment need deterministic HITL responses for reproducibility. However, they differ in **when** and **what** they need clarification about:

### ChatDev & BAEs: Specification Consumers
- **Input**: Complete feature specification (e.g., "Build a course management system")
- **HITL Trigger**: When implementation details are unclear
- **HITL Content**: Concrete specification details (`config/hitl/expanded_spec.txt`)
- **Example**: "What validation rules for email addresses?" → "RFC 5322 format"

### GHSpec: Specification Generator
- **Input**: High-level user story or feature request
- **HITL Trigger**: When requirements are ambiguous **during specification generation**
- **HITL Content**: Meta-guidelines for requirement handling (`config/hitl/ghspec_clarification_guidelines.txt`)
- **Example**: "How detailed should security requirements be?" → "Include auth, input validation, rate limiting; assume JWT tokens"

## The Solution

### File Structure
```
config/hitl/
├── expanded_spec.txt                      # ChatDev/BAEs: Concrete specification
└── ghspec_clarification_guidelines.txt    # GHSpec: Meta-guidelines
```

### Why Two Files?

**`expanded_spec.txt`** (ChatDev/BAEs):
- Contains a **complete, concrete specification** for a specific feature
- Example content: "Student: {id: int, name: str, email: str (unique)}"
- Used when: Framework asks "What should the data model look like?"
- Purpose: Provide implementation details

**`ghspec_clarification_guidelines.txt`** (GHSpec):
- Contains **general guidelines** for handling ANY unclear requirement
- Example content: "Assume JWT authentication, 80% test coverage, GDPR compliance"
- Used when: Framework asks "How should I handle unclear security requirements?"
- Purpose: Guide specification generation process

## Workflow Comparison

### ChatDev/BAEs Workflow
```
User Request
    ↓
[HITL: expanded_spec.txt] → Complete Specification
    ↓
Implementation → Testing → Delivery
```

### GHSpec Workflow
```
User Request
    ↓
Specify Phase → [HITL: ghspec_clarification_guidelines.txt] → spec.md
    ↓
Plan Phase → [HITL: ghspec_clarification_guidelines.txt] → plan.md
    ↓
Tasks Phase → tasks.md
    ↓
Implement Phase → Code files
    ↓
Bugfix Phase → Refined code
```

## Design Rationale

### Why Not Use The Same File?

1. **Different Abstraction Levels**:
   - ChatDev/BAEs need **what to build** (feature specification)
   - GHSpec needs **how to specify** (meta-guidelines)

2. **Different Timing**:
   - ChatDev/BAEs: HITL happens during implementation
   - GHSpec: HITL happens during specification generation

3. **Different Content**:
   - ChatDev/BAEs: "The student entity has these fields..."
   - GHSpec: "When unclear, assume standard security practices..."

### Why Not Generate Specifications Dynamically?

We considered having GHSpec use `expanded_spec.txt` as its output target, but this would:
- Break reproducibility (non-deterministic specification generation)
- Make it impossible to compare frameworks fairly
- Lose the ability to study how different frameworks interpret the same requirements

## Scientific Validity

This dual-HITL approach maintains experimental validity because:

1. **Reproducibility**: Both files are fixed and version-controlled
2. **Fairness**: Each framework gets HITL content appropriate to its workflow
3. **Comparability**: We can still measure:
   - Token usage (all frameworks make API calls)
   - HITL count (all frameworks encounter ambiguities)
   - Output quality (all frameworks produce working code)
   - Time to completion

## Implementation

### GHSpec Adapter
```python
def handle_hitl(self, query: str) -> str:
    """Use meta-guidelines for specification generation."""
    if self.hitl_text is None:
        hitl_path = Path("config/hitl/ghspec_clarification_guidelines.txt")
        with open(hitl_path, 'r', encoding='utf-8') as f:
            self.hitl_text = f.read().strip()
    return self.hitl_text
```

### ChatDev/BAEs Adapters
```python
def handle_hitl(self, query: str) -> str:
    """Use concrete specification."""
    if self.hitl_text is None:
        hitl_path = Path("config/hitl/expanded_spec.txt")
        with open(hitl_path, 'r', encoding='utf-8') as f:
            self.hitl_text = f.read().strip()
    return self.hitl_text
```

## Validation

To verify this approach maintains scientific rigor:

1. **HITL Count**: Track how many times each framework requests clarification
2. **HITL Content**: Log what each framework asked (for post-hoc analysis)
3. **Output Equivalence**: Verify all frameworks produce functionally equivalent code
4. **Determinism**: Re-run experiments and verify identical HITL responses

## Future Considerations

If we add more frameworks:

- **Specification Generators** (like GHSpec): Use `ghspec_clarification_guidelines.txt` or similar meta-guidelines
- **Specification Consumers** (like ChatDev/BAEs): Use `expanded_spec.txt` with concrete details
- **Hybrid Frameworks**: May need custom HITL content depending on their workflow

## References

- Implementation Plan: `docs/ghspec/implementation_plan.md`
- Decision Analysis: `docs/ghspec/decision_analysis.md`
- Clarification Guidelines: `config/hitl/ghspec_clarification_guidelines.txt`
- Concrete Specification: `config/hitl/expanded_spec.txt`
