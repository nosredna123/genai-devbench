---
description: "Implementation tasks for GHSpec-Kit Integration Enhancement"
---

# Tasks: GHSpec-Kit Integration Enhancement

**Feature Branch**: `007-integration-of-ghspec`
**Input**: Design documents from `/specs/007-integration-of-ghspec/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in specification - focusing on implementation tasks

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create default constitution file at `config/constitution/default_principles.md` with sensible coding standards
- [ ] T002 [P] Verify existing HITL guidelines at `config/hitl/ghspec_clarification_guidelines.txt` support multi-iteration clarification
- [ ] T003 [P] Document single-threaded execution requirement in `src/adapters/ghspec_adapter.py` class docstring

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `_load_constitution()` method in `src/adapters/ghspec_adapter.py` with hierarchical fallback (project → inline → default)
- [ ] T005 Implement `_get_template_path()` method in `src/adapters/ghspec_adapter.py` to resolve static vs. dynamic template sources
- [ ] T006 Implement `_load_prompt_template()` method in `src/adapters/ghspec_adapter.py` with caching and validation
- [ ] T007 Add constitution content caching in `GHSpecAdapter.__init__()` to avoid repeated file I/O
- [ ] T008 Implement chunking logic for large constitutions (>100KB) in `_prepare_constitution_excerpt()` helper method
- [ ] T009 Update `GHSpecAdapter.start()` to load tech stack constraints from `experiment.yaml` if present
- [ ] T010 Add template configuration loading in `GHSpecAdapter.start()` (read `template_source` key, validate mode)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Complete 5-Phase Workflow Execution (Priority: P1) 🎯 MVP

**Goal**: Execute all five GHSpec-Kit phases (Specify, Plan, Tasks, Implement, Bugfix) in sequence for each scenario step, generating all expected artifacts

**Independent Test**: Run experiment with single feature request "Build Hello World API" and verify all five artifacts (spec.md, plan.md, tasks.md, source code files, bugfix logs) are generated

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `_execute_specify_phase()` method in `src/adapters/ghspec_adapter.py` - load specify_template, inject constitution, handle clarifications, save spec.md
- [ ] T012 [P] [US1] Implement `_execute_plan_phase()` method in `src/adapters/ghspec_adapter.py` - load plan_template, inject spec.md + constitution + tech stack, save plan.md
- [ ] T013 [P] [US1] Implement `_execute_tasks_phase()` method in `src/adapters/ghspec_adapter.py` - load tasks_template, inject spec.md + plan.md, save tasks.md
- [ ] T014 [US1] Refactor existing `_execute_task_implementation()` in `src/adapters/ghspec_adapter.py` to become Phase 4 (Implement) - inject tasks.md + spec/plan excerpts
- [ ] T015 [US1] Implement `_execute_bugfix_phase()` method in `src/adapters/ghspec_adapter.py` - validation loop, derive bugfix tasks, apply fixes
- [ ] T016 [US1] Implement orchestrator method `execute_step()` that sequences all 5 phases: Specify → Plan → Tasks → Implement → Bugfix
- [ ] T017 [US1] Add artifact validation after each phase in `execute_step()` - check file existence and minimum size
- [ ] T018 [US1] Implement phase context passing: each phase receives outputs from previous phases
- [ ] T019 [US1] Add token/API call aggregation across all phases in `execute_step()` for final metrics return
- [ ] T020 [US1] Update existing `execute_step()` return signature to include tokens_in, tokens_out, api_calls from all 5 phases

**Checkpoint**: At this point, User Story 1 should be fully functional - complete 5-phase workflow generates all artifacts

---

## Phase 4: User Story 2 - Project Constitution and Principles (Priority: P1)

**Goal**: Define and apply project-level principles (constitution) that guide all GHSpec-Kit phases, ensuring code adheres to consistent quality standards

**Independent Test**: Configure constitution with specific rules ("always write unit tests", "follow PEP8"), run experiment, verify generated code adheres to principles

### Implementation for User Story 2

- [ ] T021 [US2] Implement constitution injection in `_build_phase_prompt()` helper method - add constitution section to system prompts
- [ ] T022 [US2] Update `_execute_specify_phase()` to inject constitution into specify_template system prompt
- [ ] T023 [US2] Update `_execute_plan_phase()` to inject constitution into plan_template system prompt
- [ ] T024 [US2] Update `_execute_tasks_phase()` to inject constitution into tasks_template system prompt
- [ ] T025 [US2] Update `_execute_task_implementation()` to inject constitution into implement_template system prompt
- [ ] T026 [US2] Update `_execute_bugfix_phase()` to inject constitution into bugfix_template system prompt
- [ ] T027 [US2] Add constitution source logging in `GHSpecAdapter.start()` - log whether using project/inline/default constitution
- [ ] T028 [US2] Implement constitution validation: content must be non-empty, fail-fast if all sources missing
- [ ] T029 [US2] Add constitution metadata to experiment logs (source_type, size_bytes, chunked flag)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - 5-phase workflow with constitution guidance

---

## Phase 5: User Story 3 - Technology Stack Guidance (Priority: P2)

**Goal**: Specify or constrain technology stack choices for Plan phase to ensure consistency across framework comparisons

**Independent Test**: Configure tech stack preference ("Python 3 + FastAPI + PostgreSQL"), run Plan phase, verify plan.md reflects those choices

### Implementation for User Story 3

- [ ] T030 [US3] Implement tech stack constraint injection in `_execute_plan_phase()` - add constraints to user prompt
- [ ] T031 [US3] Add tech stack validation: if configured, constraints_text must be non-empty string
- [ ] T032 [US3] Implement sprint consistency check: if sprint_num > 1, compare tech stack with previous sprint's plan.md
- [ ] T033 [US3] Add tech stack configuration documentation to experiment metadata logs
- [ ] T034 [US3] Handle missing tech stack constraints: inject "None specified - AI free choice" message in prompts

**Checkpoint**: All P1 and P2 priority stories complete - 5-phase workflow with constitution and tech stack control

---

## Phase 6: User Story 4 - Enhanced Clarification Handling (Priority: P2)

**Goal**: Handle multiple rounds of AI clarification requests (up to 3 iterations per phase) so ambiguous feature descriptions are fully resolved

**Independent Test**: Provide intentionally ambiguous feature description, observe clarification handling, verify adapter attempts up to 3 cycles before proceeding

### Implementation for User Story 4

- [ ] T035 [US4] Add `clarification_count` tracking to Phase Execution Context (initialize to 0 per phase)
- [ ] T036 [US4] Update `_handle_clarification()` to increment counter and check iteration limit (max 3)
- [ ] T037 [US4] Implement iteration-specific clarification text loading: append "Iteration 2: ..." sections from HITL guidelines
- [ ] T038 [US4] Add warning log when clarification limit reached: "Proceeding with best-effort interpretation after 3 iterations"
- [ ] T039 [US4] Update `_needs_clarification()` detection logic to handle multi-iteration responses
- [ ] T040 [US4] Add clarification attempt logging: log iteration number, question, response for each cycle
- [ ] T041 [US4] Test multi-iteration flow: verify that each phase can handle 1-3 clarification cycles

**Checkpoint**: All P1 and P2 stories complete with robust clarification handling

---

## Phase 7: User Story 5 - Prompt Template Synchronization (Priority: P3)

**Goal**: Support both static templates (reproducibility) and dynamic templates from cloned GHSpec-Kit repository (track upstream improvements)

**Independent Test**: Configure adapter to use templates from frameworks/ghspec, update those templates, verify adapter uses new versions in next run

### Implementation for User Story 5

- [ ] T042 [P] [US5] Implement dynamic template path resolution in `_get_template_path()` - check frameworks/ghspec/.specify/templates/commands/
- [ ] T043 [P] [US5] Add template validation in `_load_prompt_template()` - check for "System Prompt" and "User Prompt Template" sections
- [ ] T044 [US5] Implement template caching per phase: lazy load on first access, cache for run duration
- [ ] T045 [US5] Add Spec-Kit commit hash logging when using dynamic templates - document version in experiment metadata
- [ ] T046 [US5] Update quickstart.md with template source configuration instructions (static vs. dynamic mode)
- [ ] T047 [US5] Validate template_source config value: must be "static" or "dynamic", fail-fast on invalid values
- [ ] T048 [US5] Add development note in `src/adapters/ghspec_adapter.py` about template synchronization workflow

**Checkpoint**: All user stories (P1, P2, P3) complete - full feature implementation

---

## Phase 8: Bugfix Phase Implementation (Cross-Story Infrastructure)

**Purpose**: Automated bugfix loop infrastructure that supports User Story 1

- [ ] T049 [P] Implement `_derive_bugfix_tasks()` method in `src/adapters/ghspec_adapter.py` - parse validation errors, create up to 3 BugfixTask entities
- [ ] T050 [P] Implement `_build_bugfix_prompt()` method in `src/adapters/ghspec_adapter.py` - load template, inject error context + spec excerpts
- [ ] T051 Implement `_run_validation()` helper method in `src/adapters/ghspec_adapter.py` - run tests/linters, capture errors
- [ ] T052 Implement `_apply_fix()` method in `src/adapters/ghspec_adapter.py` - write AI-generated fixes to target files
- [ ] T053 Add bugfix iteration limiting in `_execute_bugfix_phase()` - max 3 iterations per FR-015
- [ ] T054 Implement bugfix logging: before/after diffs, error messages, iteration count
- [ ] T055 Add error type classification in `_derive_bugfix_tasks()` - syntax, import, runtime, validation
- [ ] T056 Implement spec excerpt extraction for bugfix context - match file paths to relevant spec sections

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057 [P] Update `docs/quickstart.md` with complete configuration examples (constitution, tech stack, templates)
- [ ] T058 [P] Add troubleshooting section to quickstart.md (constitution not loading, template missing, API rate limits)
- [ ] T059 Add comprehensive docstrings to all new methods in `src/adapters/ghspec_adapter.py`
- [ ] T060 [P] Update existing tests in `tests/test_phase1.py` to cover constitution loading scenarios
- [ ] T061 [P] Update existing tests in `tests/test_phase3.py` to cover complete 5-phase workflow
- [ ] T062 [P] Create new test file `tests/test_ghspec_bugfix.py` for bugfix loop testing
- [ ] T063 Add fail-fast assertions: verify OpenAI API exceptions propagate unchanged (no retry logic)
- [ ] T064 Document single-threaded execution in quickstart.md - clarify no concurrent experiment support
- [ ] T065 [P] Add example constitution file to `config/constitution/example_constitution.md` for reference
- [ ] T066 Validate all success criteria from spec.md: 95% success rate target, artifact format compliance, bugfix resolution rate
- [ ] T067 Run complete integration test: full experiment with all 5 phases + constitution + tech stack + bugfix

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (Phase 3): Can start after Foundational - No dependencies on other stories
  - User Story 2 (Phase 4): Can start after Foundational - Integrates with US1 but independently testable
  - User Story 3 (Phase 5): Can start after Foundational - Integrates with US1/US2
  - User Story 4 (Phase 6): Can start after Foundational - Enhances US1 phases
  - User Story 5 (Phase 7): Can start after Foundational - Independent infrastructure improvement
- **Bugfix Phase (Phase 8)**: Required by User Story 1, can be developed in parallel with other stories
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Core 5-phase workflow, no dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Constitution integration affects all phases from US1
- **User Story 3 (P2)**: Depends on US1 Phase 2 (Plan) implementation - Enhances plan phase specifically
- **User Story 4 (P2)**: Depends on US1 phase methods - Enhances clarification handling across all phases
- **User Story 5 (P3)**: Can start after Foundational - Independent template loading infrastructure

### Within Each User Story

**User Story 1 (5-Phase Workflow)**:
- T011, T012, T013 can run in parallel (different phase methods)
- T014 refactors existing code (prerequisite for T016)
- T015 depends on T049-T056 (bugfix infrastructure)
- T016 depends on T011-T015 (orchestration needs all phases)
- T017-T020 enhance T016 (sequential refinements)

**User Story 2 (Constitution)**:
- T021 creates shared helper (prerequisite for T022-T026)
- T022-T026 can run in parallel after T021 (different phase updates)
- T027-T029 can run in parallel (logging/validation enhancements)

**User Story 3 (Tech Stack)**:
- T030-T034 are sequential (each builds on previous validation/logic)

**User Story 4 (Clarification)**:
- T035-T041 are mostly sequential (each enhances previous clarification logic)

**User Story 5 (Templates)**:
- T042-T043 can run in parallel (different aspects of template loading)
- T044-T048 are sequential refinements

**Bugfix Phase (Phase 8)**:
- T049-T050 can run in parallel (different helper methods)
- T051-T056 depend on T049-T050 (use helper methods)

### Parallel Opportunities

- **Phase 1 (Setup)**: T002 and T003 can run in parallel (different files)
- **Phase 2 (Foundational)**: T004-T010 are mostly sequential due to shared state, but T009-T010 can run in parallel
- **Phase 3 (US1)**: T011, T012, T013 can run in parallel (different phase implementations)
- **Phase 4 (US2)**: T022-T026 can run in parallel after T021 (different phase method updates)
- **Phase 8 (Bugfix)**: T049-T050 can run in parallel, T051-T052 can run in parallel
- **Phase 9 (Polish)**: T057-T058, T060-T062, T065 can all run in parallel (different files)

---

## Parallel Example: User Story 1 Core Phases

```bash
# After foundational phase complete, launch phase implementations in parallel:
Task T011: "Implement _execute_specify_phase() in src/adapters/ghspec_adapter.py"
Task T012: "Implement _execute_plan_phase() in src/adapters/ghspec_adapter.py"
Task T013: "Implement _execute_tasks_phase() in src/adapters/ghspec_adapter.py"

# Then integrate sequentially:
Task T014: "Refactor _execute_task_implementation() for Phase 4"
Task T015: "Implement _execute_bugfix_phase()"
Task T016: "Implement orchestrator execute_step() sequencing all 5 phases"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. **Complete Phase 1**: Setup (T001-T003)
2. **Complete Phase 2**: Foundational (T004-T010) - CRITICAL, blocks all stories
3. **Complete Phase 3**: User Story 1 - 5-Phase Workflow (T011-T020)
4. **Complete Phase 4**: User Story 2 - Constitution Integration (T021-T029)
5. **Complete Phase 8**: Bugfix Infrastructure (T049-T056) - Required by US1
6. **STOP and VALIDATE**: Test 5-phase workflow with constitution guidance
7. Deploy/demo if ready - this satisfies both P1 user stories

### Incremental Delivery

1. **Foundation**: Setup + Foundational → Infrastructure ready
2. **MVP**: Add User Story 1 + User Story 2 → Test independently → Deploy/Demo (Core capability!)
3. **Enhanced**: Add User Story 3 → Test tech stack constraints → Deploy/Demo
4. **Robust**: Add User Story 4 → Test multi-iteration clarifications → Deploy/Demo
5. **Complete**: Add User Story 5 → Test template synchronization → Deploy/Demo
6. **Polish**: Complete Phase 9 → Final testing and documentation

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

1. **Developer A**: User Story 1 (T011-T020) + Bugfix infrastructure (T049-T056)
2. **Developer B**: User Story 2 (T021-T029) + User Story 3 (T030-T034)
3. **Developer C**: User Story 4 (T035-T041) + User Story 5 (T042-T048)
4. **All team**: Phase 9 Polish tasks in parallel

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 7 tasks
- **Phase 3 (User Story 1)**: 10 tasks
- **Phase 4 (User Story 2)**: 9 tasks
- **Phase 5 (User Story 3)**: 5 tasks
- **Phase 6 (User Story 4)**: 7 tasks
- **Phase 7 (User Story 5)**: 7 tasks
- **Phase 8 (Bugfix Infrastructure)**: 8 tasks
- **Phase 9 (Polish)**: 11 tasks

**Total**: 67 tasks

### Tasks per User Story

- **User Story 1 (P1)**: 10 tasks (Phase 3) + 8 tasks (Phase 8 Bugfix) = 18 tasks
- **User Story 2 (P1)**: 9 tasks (Phase 4)
- **User Story 3 (P2)**: 5 tasks (Phase 5)
- **User Story 4 (P2)**: 7 tasks (Phase 6)
- **User Story 5 (P3)**: 7 tasks (Phase 7)
- **Infrastructure**: 10 tasks (Phase 1-2)
- **Polish**: 11 tasks (Phase 9)

### Parallel Opportunities Identified

- **14 tasks** marked with [P] indicating parallelizable work
- **5 parallel groups** where multiple user stories can proceed simultaneously after foundational phase
- **MVP deliverable** after approximately 37 tasks (Setup + Foundational + US1 + US2 + Bugfix)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Focus on fail-fast behavior: no retry logic, immediate propagation of API errors
- Single-threaded execution enforced through documentation and runtime assertions
- Constitution must handle arbitrarily large files through chunking/excerpting strategies
