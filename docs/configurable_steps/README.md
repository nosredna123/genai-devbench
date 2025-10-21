# Config Sets + Configurable Steps - Documentation Index

## 📋 Overview

Complete planning and design documentation for the integrated **Config Sets + Configurable Steps** system, which enables curated experiment templates and flexible step configuration.

**Feature ID:** FEAT-001-CONFIG-SETS-CONFIGURABLE-STEPS  
**Version:** 1.0.0  
**Status:** ✅ Planning Complete - Ready for Implementation  
**Estimated Effort:** 12-16 hours

---

## 🏗️ Architecture Insight

The system operates in **two distinct stages**:

1. **Generator Stage** (genai-devbench repo): Curated config sets as templates
2. **Generated Experiment Stage** (separate directory): Independent, fully flexible workspace

**Key Decision:** Generator always copies ALL steps/prompts/HITL. Researchers customize post-generation by editing `config.yaml`.

---

## 📚 Documentation Structure

```
docs/configurable_steps/
├── README.md                           ← You are here
├── FINAL-IMPLEMENTATION-PLAN.md        ← 🎯 MASTER PLAN (START HERE)
├── feature-spec.md                     ← Feature specification
├── research.md                         ← Phase 0: Research & analysis
├── data-model.md                       ← Phase 1: Data model
├── quickstart.md                       ← Quick start guide
├── contracts/
│   └── api-contracts.md                ← API contracts
└── archive/                            ← Historical discussion artifacts
    ├── clarification-questions*.md
    ├── config-set-management.md
    └── implementation-plan.md (old)
```

---

## 🎯 Quick Start

### 1️⃣ Read the Master Plan First
**[FINAL-IMPLEMENTATION-PLAN.md](FINAL-IMPLEMENTATION-PLAN.md)** - Complete implementation guide with:
- Architecture overview
- All design decisions
- 5 implementation phases
- Code examples
- Testing strategy

### 2️⃣ For Developers Implementing
1. **[FINAL-IMPLEMENTATION-PLAN.md](FINAL-IMPLEMENTATION-PLAN.md)** - Follow the checklist
2. **[Data Model](data-model.md)** - Understand entities
3. **[API Contracts](contracts/api-contracts.md)** - Review function signatures
4. **[Research Document](research.md)** - Background decisions

### 3️⃣ For Users (Post-Implementation)
1. **[Quickstart Guide](quickstart.md)** - Usage examples
2. **[Feature Specification](feature-spec.md)** - User stories

---

## 📖 Document Summaries

### 🎯 FINAL-IMPLEMENTATION-PLAN.md (Master Document)
**Status:** Ready for implementation  
**Length:** ~2,100 lines  
**Contents:**
- Complete architecture with diagrams
- All 15 design decisions validated
- 5 detailed implementation phases (12-16 hours)
- Full code examples for all components
- Testing strategy with coverage matrix
- Success criteria and acceptance tests

**Start here for implementation.**

---

### feature-spec.md
**Purpose:** Original requirements and user stories  
**Contents:**
- 5 user stories
- 6 functional requirements
- Non-functional requirements
- Acceptance criteria

**Note:** Some requirements evolved during clarification (e.g., backwards compatibility removed).

---

### research.md
**Purpose:** Phase 0 unknowns resolution  
**Contents:**
- 9 research tasks completed
- Technology choices
- Best practices analysis
- Alternatives considered

---

### data-model.md
**Purpose:** Entity definitions  
**Contents:**
- StepConfig entity
- StepsCollection entity
- EnabledStepInfo entity

**Note:** ConfigSet entity added in FINAL plan.

---

### contracts/api-contracts.md
**Purpose:** API specifications  
**Contents:**
- 9 API functions
- 35+ test cases
- Input/output schemas

**Note:** ConfigSetLoader APIs added in FINAL plan.

---

### quickstart.md
**Purpose:** User guide for using the feature  
**Contents:**
- Usage examples
- Common workflows
- Configuration patterns

**Note:** Needs update for two-stage architecture post-implementation.

---

## 🎨 Feature Overview

### What It Does
Provides a **two-stage architecture** for flexible experiment configuration:

**Stage 1 - Generator (genai-devbench):**
```bash
# Select from curated templates
python scripts/new_experiment.py \
    --name my_test \
    --config-set default \
    --frameworks chatdev metagpt
```

**Stage 2 - Generated Experiment (my_test/):**
```yaml
# Researcher edits config.yaml freely
steps:
  - id: 1
    enabled: true    # ✅ Execute
    name: "Student CRUD"
    
  - id: 2
    enabled: false   # ❌ Skip (researcher disabled)
    name: "Course CRUD"
```

### Why It Matters
- ✅ **Curated Templates:** Project maintains quality-controlled scenarios
- ✅ **Full Flexibility:** Researchers customize experiments post-generation
- ✅ **Self-Contained:** Generated experiments are completely independent
- ✅ **Reproducibility:** All files copied, no external dependencies
- ✅ **Simple Generator:** No complex filtering logic, always copies everything

### Key Design Decisions
1. **Two-Stage Architecture:** Curated templates → Independent experiments
2. **No --steps Flag:** Generator always copies all (simplified)
3. **Declaration Order:** YAML order = execution order (intuitive)
4. **Fail-Fast:** Validation errors stop execution immediately
5. **Original IDs:** Metrics preserve step IDs from config
6. **Full Amnesia:** Generated experiments have no knowledge of origin

---

## 🏗️ Implementation Status

### Planning Phase ✅ COMPLETE
- [x] Feature specification (5 user stories)
- [x] Research & analysis (9 research tasks)
- [x] Data model design (4 entities)
- [x] API contracts (9+ functions)
- [x] Clarification rounds (27 design decisions validated)
- [x] Final implementation plan (2,100 lines, 5 phases)

### Implementation Phase ⏳ READY
- [ ] Phase 0: Preparation (1 hour)
- [ ] Phase 1: Data Model & Core Services (3 hours)
- [ ] Phase 2: Generator Integration (4 hours)
- [ ] Phase 3: Runner Integration (3 hours)
- [ ] Phase 4: Documentation & Examples (2 hours)
- [ ] Phase 5: Testing & Validation (2-3 hours)

**Total Estimate:** 12-16 hours

---

## 📊 Key Metrics

### Documentation Produced
- **Planning Documents:** 6 core + 4 archived
- **Total Lines:** ~6,000+
- **Design Decisions Validated:** 27
- **Implementation Hours Estimated:** 12-16

### Implementation Scope
- **New Entities:** ConfigSet, StepMetadata, ConfigSetLoader
- **Updated Entities:** StepConfig, StepsCollection
- **New Files:** ~8 (models, loader, exceptions, tests)
- **Modified Files:** ~5 (generator, runner, CLI)
- **Config Sets Created:** 2 (default, minimal)

### Test Coverage
- **Unit Tests:** 25+ test cases
- **Integration Tests:** 10+ scenarios
- **Manual Tests:** 5 critical workflows

---

## 🔄 Evolution History

This feature evolved significantly through systematic clarification:

1. **Initial Request:** "Allow configuring which steps are enabled"
2. **Discovery:** Config sets (prompts + HITL) are hardcoded
3. **Integration:** Config Sets + Configurable Steps must work together
4. **Architecture Insight:** Two-stage system (generator → experiment)
5. **Simplification:** Remove --steps flag, always copy all
6. **Final Design:** All 27 decisions validated and documented

See `archive/` for the complete clarification journey.

---

## 🎯 Success Criteria

### Functional Requirements (5)
- ✅ FR-1: Config Set Management (list, load, validate)
- ✅ FR-2: Generator Integration (--config-set, copy all)
- ✅ FR-3: Post-Generation Flexibility (edit config.yaml)
- ✅ FR-4: Runner Execution (declaration order, fail-fast)
- ✅ FR-5: Complete Independence (self-contained experiments)

### Non-Functional Requirements (3)
- ✅ NFR-1: Usability (clear errors, helpful CLI)
- ✅ NFR-2: Reliability (fail-fast, strict validation)
- ✅ NFR-3: Maintainability (clean code, easy to extend)

---

## 📞 Support

For implementation questions:
1. Read **[FINAL-IMPLEMENTATION-PLAN.md](FINAL-IMPLEMENTATION-PLAN.md)** (master document)
2. Check `archive/clarification-questions-round2-ANSWERS.md` (all decisions)
3. Review research.md for background decisions

---

## � Archive

The `archive/` directory contains interim discussion artifacts:
- **clarification-questions*.md** - Design clarification rounds
- **config-set-management.md** - Original config set design (merged into FINAL)
- **implementation-plan.md** - Old plan (superseded by FINAL)

These documents show the evolution of the design but are not needed for implementation.
```
config_loader (Task 2.1)
    ↓
    ├→ runner (Task 2.2)
    ├→ generator (Task 2.3)
    └→ unit tests (Task 3.1)
         ↓
         └→ integration tests (Task 3.2)
              ↓
              └→ documentation (Task 4.1-4.3)

metrics_collector (Task 2.4) [parallel]
```

---

## 🚀 Next Steps

### Immediate (Start Implementation)
1. Review all planning documents
2. Start Task 2.1: Config Loader Updates
3. Write unit tests as you implement
4. Commit frequently with clear messages

### Short Term (This Week)
1. Complete Phase 2: Implementation
2. Complete Phase 3: Testing
3. Complete Phase 4: Documentation

### Medium Term (Next Week)
1. Code review
2. Integration testing
3. User acceptance testing
4. Deployment

---

## 📞 Support

- **Planning Documents:** This directory (`docs/configurable_steps/`)
- **Issues:** GitHub Issues
- **Questions:** Team chat / email

---

## 🏆 Design Highlights

### ✅ Strengths
1. **Self-Documenting:** Config includes names and descriptions
2. **Backwards Compatible:** No breaking changes
3. **Extensible:** Easy to add features (timeouts, dependencies)
4. **Fair Comparison:** All frameworks use same steps
5. **Clear Errors:** Actionable error messages with examples
6. **Well Tested:** 35+ test cases planned

### 🎯 Trade-offs
1. **Verbose Config:** More YAML lines vs simple list
   - *Justified:* Self-documentation worth the verbosity
2. **No Framework Override:** Can't customize per framework
   - *Justified:* Ensures fair comparison
3. **Step ID Limit:** Only steps 1-6 supported
   - *Justified:* Current prompt infrastructure

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-21 | Initial planning complete |

---

## 🙏 Acknowledgments

**Planning Method:** Spec-kit planning process  
**Design Pattern:** Configuration-driven architecture  
**Best Practices:** Fail-fast validation, explicit over implicit

---

**Status:** ✅ Planning Complete - Ready for Implementation  
**Next Action:** Begin Task 2.1 (Config Loader Updates)  
**Estimated Time to Completion:** 10 hours
