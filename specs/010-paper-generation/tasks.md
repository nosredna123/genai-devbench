# Tasks: Camera-Ready Paper Generation from Experiment Results

**Input**: Design documents from `/specs/010-paper-generation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: Test tasks are included per Constitution requirement for ≥80% test coverage

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
All paths relative to repository root (`/home/amg/projects/uece/baes/genai-devbench/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, ACM template bundling, and basic structure

- [x] T001 Create `src/paper_generation/` module structure with `__init__.py`
- [x] T002 Create `src/paper_generation/sections/` subdirectory with `__init__.py`
- [x] T003 [P] Download and bundle ACM SIGSOFT template files to `templates/acm_sigsoft/` (sigconf.cls, ACM-Reference-Format.bst, acmart.pdf, VERSION file with "1.90")
- [x] T004 [P] Create `scripts/generate_paper.py` CLI entry point skeleton
- [x] T005 [P] Create `scripts/export_figures.py` CLI entry point skeleton
- [x] T006 [P] Create `tests/paper_generation/` directory structure
- [x] T007 [P] Create `tests/paper_generation/fixtures/` for test experiment data

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 Implement `src/paper_generation/exceptions.py` with all error types (PaperGenerationError, ConfigValidationError, DependencyMissingError, ExperimentDataError, ProseGenerationError, FigureExportError, LatexConversionError, PdfCompilationError)
- [x] T009 Implement `src/paper_generation/models.py` with data classes (PaperConfig with __post_init__ validation, PaperStructure, Figure with file validation, Table, SectionContext, PaperResult)
- [x] T010 [P] Implement `src/paper_generation/template_bundle.py` (TemplateBundle class: verify ACM template VERSION, copy templates to output, validate template integrity)
- [x] T011 [P] Implement `src/paper_generation/pandoc_converter.py` (PandocConverter class: detect Pandoc ≥2.0, fail-fast with OS-specific installation instructions, convert Markdown→LaTeX)
- [x] T012 [P] Implement `src/paper_generation/citation_handler.py` (CitationHandler class: insert_placeholders() with framework detection and claim patterns, render_latex() for bold formatting)
- [x] T013 [P] Implement `src/paper_generation/document_formatter.py` (DocumentFormatter class: escape LaTeX special characters, format_latex() with ACM template integration, handle math mode)
- [x] T014 Write unit tests for exceptions in `tests/paper_generation/test_exceptions.py` (test each exception type, verify error messages include remediation)
- [x] T015 [P] Write unit tests for models in `tests/paper_generation/test_models.py` (test PaperConfig validation, Figure file checks, Table structure validation)
- [x] T016 [P] Write unit tests for TemplateBundle in `tests/paper_generation/test_template_bundle.py` (test VERSION validation, template file existence)
- [x] T017 [P] Write unit tests for PandocConverter in `tests/paper_generation/test_pandoc_converter.py` (test version detection, fail-fast behavior, mock Pandoc calls)
- [x] T018 [P] Write unit tests for CitationHandler in `tests/paper_generation/test_citation_handler.py` (test placeholder insertion patterns, LaTeX rendering)
- [x] T019 [P] Write unit tests for DocumentFormatter in `tests/paper_generation/test_document_formatter.py` (test special character escaping, math mode preservation)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Researcher Generates Publication Draft (Priority: P1) 🎯 MVP

**Goal**: Generate complete camera-ready paper with AI-generated prose for all sections, statistical tables, embedded figures, and citation placeholders, compiling to ACM SIGSOFT PDF

**Independent Test**: Run complete experiment with 3+ frameworks, execute `python scripts/generate_paper.py <experiment_dir>`, verify: (1) all sections present with ≥800 words each, (2) statistical tables formatted correctly, (3) figures embedded, (4) main.pdf compiles matching ACM format, (5) citation placeholders present without hallucinated refs

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [P] [US1] Create test fixture: sample experiment data in `tests/paper_generation/fixtures/sample_experiment/` (analysis/statistical_report.md, analysis/metrics.json, config/experiment.yaml with 3 frameworks)
- [x] T021 [P] [US1] Integration test for full paper generation in `tests/paper_generation/test_paper_generator_integration.py` (test complete pipeline: load experiment → generate sections → export figures → convert to LaTeX → verify PDF exists)
- [x] T022 [P] [US1] Contract test for ProseEngine API in `tests/paper_generation/test_prose_engine_contract.py` (test generate_prose() with mock OpenAI responses, verify ≥800 words, verify AI-generated markers)
- [x] T023 [P] [US1] Contract test for FigureExporter API in `tests/paper_generation/test_figure_exporter_contract.py` (test export_figures() returns Figure objects with valid paths, verify PDF+PNG dual export, verify ≥300 DPI)

### Implementation for User Story 1

- [x] T024 [P] [US1] Implement `src/paper_generation/prose_engine.py` (ProseEngine class: generate_prose() with OpenAI API calls, structured prompts from research.md, exponential backoff retry, token usage logging, validate ≥800 words)
- [x] T025 [P] [US1] Implement `src/paper_generation/figure_exporter.py` (FigureExporter class: configure Matplotlib headless backend, export_figures() with dual PDF+PNG export at 300 DPI, verify file sizes <10MB, generate Figure objects with captions)
- [x] T026 [P] [US1] Implement `src/paper_generation/section_generator.py` (BaseSectionGenerator abstract class with generate() method, context loading, prose generation orchestration, AI marker insertion)
- [x] T027 [P] [US1] Implement `src/paper_generation/sections/abstract_generator.py` (AbstractGenerator extending BaseSectionGenerator: extract experiment summary, frameworks, key findings)
- [x] T028 [P] [US1] Implement `src/paper_generation/sections/introduction_generator.py` (IntroductionGenerator: research motivation, problem statement, key contributions, paper organization - comprehensive prose ≥800 words)
- [x] T029 [P] [US1] Implement `src/paper_generation/sections/related_work_generator.py` (RelatedWorkGenerator: generate prose on framework landscape, insert citation placeholders for frameworks and prior work, avoid hallucinations - ≥800 words)
- [x] T030 [P] [US1] Implement `src/paper_generation/sections/methodology_generator.py` (MethodologyGenerator: experimental design, task specification, metrics definitions, statistical methods - comprehensive prose ≥800 words)
- [x] T031 [P] [US1] Implement `src/paper_generation/sections/results_generator.py` (ResultsGenerator: descriptive statistics tables, comparative analysis with effect sizes, AI-generated interpretations embedded with p-values/confidence intervals - ≥800 words)
- [x] T032 [P] [US1] Implement `src/paper_generation/sections/discussion_generator.py` (DiscussionGenerator: interpretation of results, implications for practitioners, threats to validity - ≥800 words)
- [x] T033 [P] [US1] Implement `src/paper_generation/sections/conclusion_generator.py` (ConclusionGenerator: summary of contributions, key findings, limitations, future work - ≥800 words)
- [x] T034 [US1] Implement `src/paper_generation/paper_generator.py` (PaperGenerator class: orchestrate entire pipeline - depends on T024-T033)
  - validate experiment directory (has analysis/ subdirectory)
  - detect Pandoc availability (fail-fast if missing)
  - load experiment data
  - generate all sections (call all section generators)
  - export figures
  - assemble PaperStructure
  - insert citation placeholders
  - convert to LaTeX via DocumentFormatter
  - invoke Pandoc for Markdown→LaTeX
  - invoke pdflatex for PDF compilation
  - return PaperResult with file paths, word count, timing, token usage
- [x] T035 [US1] Implement CLI in `scripts/generate_paper.py` (argparse for experiment_dir, --output-dir, --sections, --prose-level, --skip-latex, --model, --temperature; call PaperGenerator; handle errors with exit codes; display results)
- [x] T036 [US1] Write unit test for ProseEngine in `tests/paper_generation/test_prose_engine.py` (mock OpenAI API, test prompt generation, test retry logic, test word count validation)
- [x] T037 [P] [US1] Write unit test for FigureExporter in `tests/paper_generation/test_figure_exporter.py` (mock Matplotlib, test dual export, test DPI settings, test file size validation)
- [x] T038 [P] [US1] Write unit tests for each section generator in `tests/paper_generation/test_section_generators.py` (test each generator's context parsing, prose generation call, ≥800 word validation)
- [x] T039 [P] [US1] Write unit test for PaperGenerator orchestration in `tests/paper_generation/test_paper_generator.py` (test pipeline stages, test error propagation, test PaperResult structure)
- [x] T040 [US1] End-to-end test: run `python scripts/generate_paper.py` on fixture experiment, verify main.pdf exists and compiles, verify all sections present, verify word counts ≥800, verify citation placeholders present

**Checkpoint**: At this point, User Story 1 should be fully functional - researchers can generate complete camera-ready papers with AI prose, figures, and ACM formatting

---

## Phase 4: User Story 2 - Researcher Customizes Paper Output (Priority: P2)

**Goal**: Enable researchers to control section selection, metric filtering, and prose detail level via CLI flags and PaperConfig options

**Independent Test**: Generate paper with `--sections=methodology,results`, verify only those sections have full prose while others have outlines; filter metrics with `--metrics-filter=efficiency,cost`, verify only those categories appear; set `--prose-level=minimal`, verify prose focuses on observations without causal claims

### Tests for User Story 2

- [x] T041 [P] [US2] Integration test for section selection in `tests/paper_generation/test_customization_sections.py` (test --sections flag filters correctly, test outline generation for non-selected sections)
- [x] T042 [P] [US2] Integration test for metric filtering in `tests/paper_generation/test_customization_metrics.py` (test --metrics-filter affects tables and prose, test filtered metrics exclude others)
- [x] T043 [P] [US2] Integration test for prose levels in `tests/paper_generation/test_customization_prose.py` (test minimal vs standard vs comprehensive prose differences, verify minimal avoids causal claims)

### Implementation for User Story 2

- [x] T044 [US2] Extend PaperConfig in `src/paper_generation/models.py` with validation for sections list and prose_level enum (validate section names against valid set, validate prose_level in ["minimal", "standard", "comprehensive"])
- [x] T045 [US2] Extend PaperGenerator in `src/paper_generation/paper_generator.py` to respect config.sections (skip full prose for non-selected sections, generate structural outlines instead)
- [x] T046 [US2] Extend ProseEngine in `src/paper_generation/prose_engine.py` to support prose_level parameter (minimal: observations only, standard: balanced, comprehensive: deep analysis; adjust prompt templates accordingly)
- [x] T047 [US2] Implement metric filtering in ResultsGenerator (`src/paper_generation/sections/results_generator.py`): filter statistical tables and prose to config.metrics_filter categories if specified
- [x] T048 [US2] Extend CLI in `scripts/generate_paper.py` to parse --sections, --metrics-filter, --prose-level flags and populate PaperConfig
- [x] T049 [P] [US2] Write unit test for section filtering logic in `tests/paper_generation/test_section_filtering.py`
- [x] T050 [P] [US2] Write unit test for prose level variations in `tests/paper_generation/test_prose_level.py` (verify prompt differences, verify output characteristics)
- [x] T051 [P] [US2] Write unit test for metric filtering in `tests/paper_generation/test_metric_filtering.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - researchers can generate default papers OR customized papers with section/metric/prose control

---

## Phase 5: User Story 3 - Researcher Exports Publication Figures (Priority: P2)

**Goal**: Enable figure-only export for researchers who need high-quality visualizations without regenerating entire paper, supporting both CLI and programmatic access

**Independent Test**: Run `python scripts/export_figures.py <experiment_dir>`, verify all figures exported in PDF+PNG formats, verify ≥300 DPI, verify scalable vector PDFs; alternatively use `--figures-only` flag with generate_paper.py

### Tests for User Story 3

- [x] T052 [P] [US3] Integration test for figure-only export in `tests/paper_generation/test_figure_only_export.py` (test export_figures.py CLI, verify output directory structure, verify PDF+PNG pairs, verify metadata)
- [x] T053 [P] [US3] Contract test for FigureExporter standalone usage in `tests/paper_generation/test_figure_exporter_standalone.py` (test calling export_figures() directly without PaperGenerator, verify independent operation)

### Implementation for User Story 3

- [x] T054 [US3] Extend FigureExporter in `src/paper_generation/figure_exporter.py` to support standalone operation (add method to load experiment data independently, extract statistical results, generate all figure types)
- [x] T055 [US3] Implement CLI in `scripts/export_figures.py` (argparse for experiment_dir, --output-dir, --formats, --dpi; call FigureExporter.export_figures(); handle errors; display exported file list)
- [x] T056 [US3] Extend `scripts/generate_paper.py` to support --figures-only flag (skip prose generation, only export figures, exit after figure export)
- [ ] T057 [P] [US3] Write unit test for figures-only mode in `tests/paper_generation/test_paper_generator.py`
- [ ] T058 [US3] End-to-end test: run `python scripts/export_figures.py` on fixture experiment, verify all expected figures present, verify file properties (DPI, format, size)

**Checkpoint**: All user stories 1-3 should now be independently functional - researchers can generate full papers, customize output, OR export just figures

---

## Phase 6: User Story 4 - Researcher Uses Enhanced Documentation (Priority: P2)

**Goal**: Enhance generated experiment project's README.md with comprehensive Reproduction section enabling independent researchers to reproduce experiment in ≤30 minutes

**Independent Test**: Follow generated README.md Reproduction section on fresh system, verify all steps work without external help, verify successful experiment rerun and report regeneration

### Tests for User Story 4

- [ ] T059 [P] [US4] Integration test for README enhancement in `tests/paper_generation/test_readme_enhancement.py` (test README template rendering, verify all required sections present, verify experiment-specific values injected)
- [ ] T060 [P] [US4] Validation test for README instructions in `tests/paper_generation/test_readme_validation.py` (parse README commands, verify they are syntactically correct for target shells)

### Implementation for User Story 4

- [x] T061 [P] [US4] Create README reproduction template in `templates/readme_reproduction_section.md` (5 subsections: Environment Requirements, Dependency Installation, Running the Experiment, Regenerating Analysis Reports, Expected Outputs - use placeholders for experiment-specific values)
- [x] T062 [US4] Implement `src/paper_generation/readme_enhancer.py` (ReadmeEnhancer class: load template, inject experiment-specific values [Python version, framework list, runtime estimates], append to existing experiment README.md)
- [x] T063 [US4] Integrate ReadmeEnhancer into PaperGenerator in `src/paper_generation/paper_generator.py` (call after paper generation, enhance experiment's README.md, log README path in PaperResult warnings)
- [ ] T064 [P] [US4] Write unit test for ReadmeEnhancer in `tests/paper_generation/test_readme_enhancer.py` (test template loading, test value injection, test README appending)
- [ ] T065 [US4] End-to-end test: generate paper, verify experiment README.md contains Reproduction section, manually verify instructions are clear and complete

**Checkpoint**: All 4 user stories should now be fully implemented and independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, edge case handling, performance optimization

- [ ] T066 [P] Add comprehensive docstrings to all modules following PEP 257 (Constitution Principle II: Clarity & Transparency)
- [ ] T067 [P] Add logging throughout paper generation pipeline using JSON structured logging (timestamp, step, message, metadata)
- [ ] T068 [P] Implement performance optimization: cache API responses during development mode (avoid redundant OpenAI calls for same section+context)
- [x] T069 Handle edge case: experiments with only 1 framework (modify ResultsGenerator to skip comparative statistics, focus on descriptive analysis)
- [x] T070 Handle edge case: missing figures during LaTeX compilation (add placeholder text in document_formatter.py)
- [x] T071 Handle edge case: corrupted ACM template files (implement template integrity check in template_bundle.py with re-download from bundled backup)
- [x] T072 [P] Add CLI --help documentation with comprehensive usage examples in both scripts/generate_paper.py and scripts/export_figures.py
- [ ] T073 [P] Create user documentation in `docs/paper_generation_guide.md` (usage examples, troubleshooting guide, AI review checklist)
- [x] T074 [P] Update main README.md with paper generation feature description and quick start example
- [ ] T075 Performance test: measure paper generation time for experiment with 50 runs, 3 frameworks, verify completes in ≤3 minutes (Success Criterion SC-008)
- [ ] T076 [P] Validate all AI-generated prose is marked with review indicators (audit all section generators)
- [ ] T077 [P] Validate all citation placeholders are in correct format and visually distinct in PDF (SC-004, SC-010)
- [ ] T078 Final integration test: run all 4 user stories in sequence on same experiment, verify no conflicts or shared state issues
- [x] T079 [P] Code quality: run `ruff check .` and fix any linting issues (Constitution requirement)
- [ ] T080 [P] Code quality: verify test coverage ≥80% for paper_generation module using pytest-cov

---

## Dependencies

### User Story Dependencies
```
Setup (Phase 1) → Foundational (Phase 2)
                        ↓
        ┌───────────────┼───────────────┬───────────────┐
        ↓               ↓               ↓               ↓
    US1 (P1)        US2 (P2)        US3 (P2)        US4 (P2)
    Generate        Customize        Export          Enhance
    Paper           Output           Figures         Docs
        ↓               ↓               ↓               ↓
        └───────────────┼───────────────┴───────────────┘
                        ↓
                  Polish & Cross-Cutting
```

**Independence**: 
- US1 is fully independent (MVP scope)
- US2 depends on US1 (extends PaperGenerator and ProseEngine)
- US3 is mostly independent (can run standalone), but shares FigureExporter with US1
- US4 is fully independent (operates on experiment README, not generated paper)

### Task Dependencies Within Phases

**Phase 2 (Foundational)**:
- T014-T019 (tests) can run in parallel, independent of each other
- T008-T013 (implementations) can run in parallel, all are independent modules

**Phase 3 (US1)**:
- T020-T023 (tests) can run in parallel
- T024-T033 (section implementations) can run in parallel - all extend BaseSectionGenerator independently
- T034 (PaperGenerator) DEPENDS ON T024-T033 completing
- T035 (CLI) DEPENDS ON T034
- T036-T039 (unit tests) can run in parallel
- T040 (E2E test) DEPENDS ON T035

**Phase 4 (US2)**:
- T041-T043 (tests) can run in parallel
- T044-T048 (implementations) are sequential (extend existing modules)
- T049-T051 (unit tests) can run in parallel

**Phase 5 (US3)**:
- T052-T053 (tests) can run in parallel
- T054-T056 (implementations) are sequential
- T057-T058 (tests) can run in parallel

**Phase 6 (US4)**:
- T059-T060 (tests) can run in parallel
- T061 (template creation) is independent
- T062-T063 (implementations) are sequential
- T064-T065 (tests) can run in parallel

**Phase 7 (Polish)**:
- Most tasks can run in parallel except T078 (final integration test) which must be last

---

## Parallel Execution Opportunities

### Within Foundational Phase (Phase 2)
```bash
# All implementations can happen in parallel
parallel --jobs 6 ::: \
  "implement exceptions.py" \
  "implement models.py" \
  "implement template_bundle.py" \
  "implement pandoc_converter.py" \
  "implement citation_handler.py" \
  "implement document_formatter.py"

# All tests can happen in parallel after implementations
parallel --jobs 6 ::: \
  "test exceptions" \
  "test models" \
  "test template_bundle" \
  "test pandoc_converter" \
  "test citation_handler" \
  "test document_formatter"
```

### Within User Story 1 (Phase 3)
```bash
# All section generators can be implemented in parallel
parallel --jobs 7 ::: \
  "implement abstract_generator.py" \
  "implement introduction_generator.py" \
  "implement related_work_generator.py" \
  "implement methodology_generator.py" \
  "implement results_generator.py" \
  "implement discussion_generator.py" \
  "implement conclusion_generator.py"

# ProseEngine and FigureExporter can happen in parallel
parallel --jobs 2 ::: \
  "implement prose_engine.py" \
  "implement figure_exporter.py"
```

### Across User Stories (after US1 complete)
```bash
# US2, US3, US4 can happen in parallel teams
Team A: Implement US2 (Customization)
Team B: Implement US3 (Figure Export)
Team C: Implement US4 (README Enhancement)
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)
**Deliver**: User Story 1 only (Phases 1-3)
- **Outcome**: Researchers can generate complete camera-ready papers with AI prose, figures, ACM formatting
- **Validation**: End-to-end test (T040) passes
- **Timeline**: ~2-3 weeks (foundational + US1)

### Incremental Delivery
1. **Sprint 1** (Week 1): Foundational infrastructure (Phase 1-2)
   - Deliverable: All base classes, error handling, data models tested
   - Checkpoint: T019 complete

2. **Sprint 2-3** (Weeks 2-3): User Story 1 - Core paper generation (Phase 3)
   - Deliverable: Full paper generation working end-to-end
   - Checkpoint: T040 complete, MVP delivered

3. **Sprint 4** (Week 4): User Stories 2-4 in parallel (Phases 4-6)
   - Team A: US2 (Customization)
   - Team B: US3 (Figure Export) 
   - Team C: US4 (README Enhancement)
   - Deliverable: All customization and export features working
   - Checkpoint: T058, T065 complete

4. **Sprint 5** (Week 5): Polish and hardening (Phase 7)
   - Deliverable: Production-ready with documentation, edge cases handled, performance verified
   - Checkpoint: T080 complete

### Testing Strategy
- **TDD Approach**: Tests written FIRST for each user story (T020-T023, T041-T043, T052-T053, T059-T060)
- **Test Pyramid**: 
  - Unit tests (60%): Test individual modules in isolation
  - Integration tests (30%): Test component interactions
  - End-to-end tests (10%): Test complete user journeys
- **Coverage Target**: ≥80% (Constitution requirement, verified in T080)

---

## Task Summary

**Total Tasks**: 80

**Task Count by User Story**:
- Setup (Phase 1): 7 tasks
- Foundational (Phase 2): 12 tasks
- User Story 1 - Generate Paper (P1): 21 tasks (T020-T040)
- User Story 2 - Customize Output (P2): 11 tasks (T041-T051)
- User Story 3 - Export Figures (P2): 7 tasks (T052-T058)
- User Story 4 - Enhance Docs (P2): 7 tasks (T059-T065)
- Polish & Cross-Cutting: 15 tasks (T066-T080)

**Parallel Opportunities**: ~45 tasks marked [P] can run in parallel within their phase

**Independent Test Criteria**:
- US1: Run generate_paper.py on 3-framework experiment → verify PDF compiles, all sections ≥800 words, citation placeholders present
- US2: Run with customization flags → verify section filtering, metric filtering, prose level changes
- US3: Run export_figures.py → verify all figures exported in PDF+PNG at 300+ DPI
- US4: Follow generated README Reproduction section → successfully rerun experiment

**Suggested MVP Scope**: Phases 1-3 (Tasks T001-T040) = User Story 1 only

**Estimated Timeline**: 4-5 weeks with full team
- MVP (US1): 2-3 weeks
- Full feature (US1-4 + Polish): 4-5 weeks
