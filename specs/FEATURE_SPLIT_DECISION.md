# Feature Split Decision: 009 + 010

**Date**: 2025-10-28  
**Decision**: Split refactoring and paper generation into two sequential features

## Context

Initial feature request was to "refactor analysis module to update/fix final analysis report generator." During clarification, user introduced requirement for camera-ready paper generation with ACM format, comprehensive AI prose, figure export, and reproducibility packaging.

## Decision Rationale

### Why Split?

1. **Scope Management**: Core refactoring (removing hardcoded metrics, config-driven design) is substantial standalone work (1-2 weeks)
2. **Faster Delivery**: Get improved statistical reports working in days, paper generation follows
3. **Clearer Testing**: Each feature has focused test scenarios and success criteria
4. **Reduced Risk**: If paper generation hits issues, doesn't block core improvements
5. **Better Git History**: Separate PRs enable focused code review

### Feature 009: Refactor Analysis Module Report Generator
**Estimated Effort**: 1-2 weeks  
**Scope**: Technical refactoring only
- Remove hardcoded `RELIABLE_METRICS` set
- Implement unified MetricsConfig with single metrics section
- Add fail-fast validation (no silent fallbacks)
- Dynamic metric partitioning (measured vs unmeasured)
- Configuration migration (old → new format)

**Deliverables**:
- Refactored `src/analysis/report_generator.py`
- Updated `src/utils/metrics_config.py` API
- New configuration format in `config/experiment.yaml`
- Migration guide for existing experiments
- Markdown statistical reports (improved, config-driven)

### Feature 010: Camera-Ready Paper Generation
**Estimated Effort**: 4-5 weeks (increased from 3-4 due to full prose generation)  
**Scope**: Publication automation
- ACM SIGSOFT LaTeX template integration
- **Full AI-generated prose for ALL sections** (Introduction, Related Work, Methodology, Results, Discussion, Conclusion)
- Citation placeholders `[CITE: description]` to avoid hallucinations
- Pandoc-based Markdown→LaTeX conversion
- Publication-quality figure export (PDF + PNG 300 DPI)
- Enhanced README.md with reproduction instructions (no separate Docker package)
- CLI tools in `scripts/` directory

**Deliverables**:
- `scripts/generate_paper.py` CLI tool
- `scripts/export_figures.py` CLI tool
- AI prose generation engine for all paper sections
- Citation placeholder system
- Bundled ACM template files
- Enhanced README.md generator
- Comprehensive user documentation

## Key Decisions Recorded

### Decision 1: AI-Generated Interpretations
**Choice**: Option A - Full causal reasoning with manual review  
**Implementation**: **ALL sections** (Introduction, Related Work, Methodology, Results, Discussion, Conclusion) get full AI-generated prose marked with `[AI-GENERATED - REVIEW REQUIRED]`  
**Rationale**: User will carefully review each generated paper before submission. Maximizes automation of writing effort.

### Decision 1b: Related Work Citations
**Choice**: Option A - Citation placeholders (safest)  
**Implementation**: Use `[CITE: description]` format (e.g., `[CITE: AutoGPT original paper]`) instead of hallucinated references  
**Rationale**: Prevents AI from inventing fake citations; researcher fills real references during review

### Decision 2: Pandoc Installation
**Choice**: Option A - Detection + clear instructions only  
**Implementation**: Fail-fast with OS-specific install commands, support `--skip-latex` flag  
**Rationale**: Avoids sudo/permission issues, simpler cross-platform support

### Decision 3: Feature Scope
**Choice**: Option A - Split into 009 (refactor) + 010 (paper)  
**Implementation**: Sequential features with 010 depending on 009  
**Rationale**: Faster delivery, clearer scope, reduced risk

### Decision 4: CLI Architecture
**Choice**: Option C - Scripts entry point wrapping both tools  
**Implementation**: `scripts/generate_paper.py` and `scripts/export_figures.py`  
**Rationale**: Clean separation, discoverability, dual-use (CLI + library)

### Decision 5: Report Output Control
**Choice**: Generate paper only when explicitly requested via `--generate-paper` flag  
**Implementation**: Default behavior generates Markdown stats only  
**Rationale**: Prevents unwanted overhead, enables iteration

### Decision 6: ACM Template Integration
**Choice**: Bundle ACM template files in generated output  
**Implementation**: Include `.cls`, `.bst`, logo files in `paper/acm_template/`  
**Rationale**: Ensures reproducibility, reduces researcher friction

### Decision 7: Figure Generation Workflow
**Choice**: Generate during report creation + support `--figures-only` flag  
**Implementation**: Default creates complete package, separate flag for regeneration  
**Rationale**: Complete package by default, flexibility for debugging

### Decision 8: Reproducibility Package
**Choice**: Simplified approach - No Docker package  
**Implementation**: Enhance generated experiment's README.md with comprehensive reproduction section (Python version, dependencies, execution steps, expected outputs)  
**Rationale**: Standalone generator already creates reproducible projects; Docker packaging is unnecessary overhead. Better documentation is sufficient.

## Dependencies

- **Feature 010 depends on Feature 009**: Paper generator uses refactored MetricsConfig API
- **No backward dependency**: Feature 009 is completely independent

## Migration Path

1. **Implement Feature 009**: Refactor core report generator (~1-2 weeks)
2. **Test & validate**: Ensure statistical reports work with new config format
3. **Migrate existing configs**: Update experiment.yaml files to new unified metrics section
4. **Implement Feature 010**: Build paper generation on top of refactored base (~3-4 weeks)
5. **Integration testing**: Verify end-to-end workflow from experiment → stats → paper

## Success Metrics

### Feature 009 Success
- ✅ Zero hardcoded metric lists in `report_generator.py`
- ✅ All metrics loaded from unified config section
- ✅ Fail-fast validation with clear error messages
- ✅ Statistical reports generate successfully with new config

### Feature 010 Success
- ✅ Papers compile with `pdflatex` on first attempt
- ✅ All figures exported as PDF (vector) + PNG (300 DPI)
- ✅ Reproducibility Docker container rebuilds successfully
- ✅ REPRODUCTION.md enables independent reproduction in ≤30 minutes

## Next Steps

1. **Finalize Feature 009 spec**: Review with user, invoke `/speckit.plan`
2. **Implement Feature 009**: Core refactoring work
3. **Test & validate Feature 009**: Ensure statistical reports work perfectly
4. **Review Feature 010 spec**: Detailed review before implementation
5. **Implement Feature 010**: Paper generation on refactored foundation
