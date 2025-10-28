# Feature Specification: Camera-Ready Paper Generation from Experiment Results

**Feature Branch**: `010-paper-generation`  
**Created**: 2025-10-28  
**Status**: Draft  
**Depends On**: Feature 009-refactor-analysis-module (requires refactored MetricsConfig-driven report generator)  
**Input**: User description: "Generate camera-ready scientific papers in ACM SIGSOFT format from experiment results with AI-generated comprehensive prose, statistical analysis, auto-generated figures, and full reproducibility package"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Researcher Generates Publication Draft (Priority: P1)

A researcher completes a multi-framework comparison experiment and needs a camera-ready paper draft suitable for submission to top CS/SE conferences (ICSE, FSE, ASE, etc.) with minimal manual editing.

**Why this priority**: This is the core value proposition - automate 80% of paper writing effort, allowing researchers to focus on high-level insights and refinement rather than boilerplate content generation.

**Independent Test**: Can be fully tested by running a complete experiment with 3+ frameworks, generating the paper with `--generate-paper` flag, compiling the LaTeX output, and verifying: (1) all sections present (abstract through conclusion), (2) statistical tables formatted correctly, (3) figures embedded, (4) ACM template compiles without errors, (5) references section populated.

**Acceptance Scenarios**:

1. **Given** an experiment with complete statistical results, **When** paper generation is requested via `--generate-paper`, **Then** a complete LaTeX document is generated with abstract, introduction (full prose), related work (full prose with citation placeholders), detailed methodology (full prose), comprehensive results with statistics (full prose), discussion (full prose), and conclusion (full prose)
2. **Given** the experiment includes multiple metrics and statistical tests, **When** the results section is generated, **Then** it includes AI-generated prose descriptions of key findings with embedded statistical evidence (p-values, effect sizes, confidence intervals), all marked with [AI-GENERATED - REVIEW REQUIRED]
3. **Given** the paper is generated, **When** compiled with `pdflatex`, **Then** it produces a valid PDF matching ACM SIGSOFT format requirements
4. **Given** the related work section is generated, **When** examining the LaTeX source, **Then** all citations use placeholder format `[CITE: description]` without hallucinated references

---

### User Story 2 - Researcher Customizes Paper Output (Priority: P2)

A researcher wants control over which sections to generate, whether to include specific metrics, and how detailed the analysis prose should be.

**Why this priority**: Different venues have different requirements; researchers need flexibility to tailor output without editing LaTeX directly.

**Independent Test**: Can be tested by using various CLI flags (`--sections`, `--metrics-filter`, `--prose-level`) and verifying the generated paper respects the configuration.

**Acceptance Scenarios**:

1. **Given** a researcher specifies `--sections=methodology,results`, **When** the paper is generated, **Then** only methodology and results sections contain full prose (intro/discussion/conclusion are outlines)
2. **Given** a researcher uses `--metrics-filter="efficiency,cost"`, **When** the paper is generated, **Then** only efficiency and cost category metrics appear in tables and analysis
3. **Given** a researcher sets `--prose-level=minimal`, **When** results are generated, **Then** prose focuses on numerical observations without causal interpretations

---

### User Story 3 - Researcher Exports Publication Figures (Priority: P2)

A researcher needs high-quality vector graphics (PDF) and raster images (PNG) of all visualizations for inclusion in the paper and supplementary materials.

**Why this priority**: Figures must meet publication standards (300+ DPI, vector formats preferred, proper labeling).

**Independent Test**: Can be tested by running `--export-figures` and verifying all generated files are valid PDF/PNG, have correct dimensions, and can be embedded in LaTeX.

**Acceptance Scenarios**:

1. **Given** an experiment with statistical results, **When** `--export-figures` is used, **Then** all metric comparison plots, cost breakdowns, and distribution charts are exported as both PDF and PNG
2. **Given** figures are exported, **When** examining file metadata, **Then** PNG files have ≥300 DPI resolution and PDF files use vector graphics
3. **Given** figures are generated, **When** the LaTeX paper is compiled, **Then** all figures are correctly embedded with captions and labels

---

### User Story 4 - Researcher Uses Enhanced Documentation (Priority: P2)

A researcher needs clear, comprehensive documentation in the generated experiment project explaining how to reproduce the experiment and analysis results.

**Why this priority**: Reproducibility is critical for scientific validity, but the standalone generator already creates reproducible experiments - we just need better documentation explaining how to use them.

**Independent Test**: Can be tested by following the generated README.md reproduction section on a fresh system and verifying all steps work without external help.

**Acceptance Scenarios**:

1. **Given** paper generation is requested, **When** the experiment project is generated, **Then** the README.md includes a comprehensive "Reproduction" section with Python version, dependency installation, execution steps, and expected outputs
2. **Given** the README includes reproduction instructions, **When** a researcher follows them on a clean system, **Then** they can successfully run the experiment and regenerate analysis reports
3. **Given** the generated project includes analysis results, **When** examining the README, **Then** it documents which files contain statistical reports, figures, and raw data

---

### Edge Cases

- What happens when Pandoc is not installed? (fail with clear installation instructions, not silent degradation)
- How are missing figures handled during LaTeX compilation? (placeholder text indicating missing data)
- What if ACM template files are missing/corrupted? (re-download from bundled backup)
- How does the system handle experiments with only 1 framework? (skip comparative statistics, focus on descriptive analysis)
- What if the researcher wants to regenerate just figures without full paper? (support `--figures-only` flag)

## Requirements *(mandatory)*

### Functional Requirements

#### Paper Generation Core
- **FR-001**: System MUST provide CLI flag `--generate-paper` to trigger camera-ready paper generation
- **FR-002**: System MUST generate complete paper structure with full AI-generated prose for ALL sections: Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion, References (empty template)
- **FR-003**: System MUST generate comprehensive prose for Introduction section including: research motivation, problem statement, key contributions, and paper organization
- **FR-004**: System MUST generate comprehensive prose for Related Work section with citation placeholders in format `[CITE: description]` (e.g., `[CITE: AutoGPT original paper]`, `[CITE: framework comparison studies]`) to avoid hallucinated references
- **FR-005**: System MUST generate comprehensive prose for Methodology section describing: experimental design, task specification, framework selection rationale, metrics definitions, statistical methods (Kruskal-Wallis, Cliff's Delta, Dunn-Šidák correction)
- **FR-006**: System MUST generate comprehensive prose for Results section including: descriptive statistics tables, comparative analysis with effect sizes, key findings with statistical evidence (p-values, confidence intervals), AI-generated causal interpretations
- **FR-007**: System MUST generate comprehensive prose for Discussion section including: interpretation of results, implications for practitioners, threats to validity, comparison to related work
- **FR-008**: System MUST generate comprehensive prose for Conclusion section including: summary of contributions, key findings, limitations, and future work directions
- **FR-009**: System MUST mark ALL AI-generated prose (entire paper except tables/figures) with section-level or paragraph-level `[AI-GENERATED - REVIEW REQUIRED]` indicators to ensure researchers validate content before submission

#### LaTeX & Formatting
- **FR-010**: System MUST bundle ACM SIGSOFT LaTeX template files (.cls, .bst, logo files) in generated output
- **FR-011**: System MUST convert Markdown content to LaTeX format using Pandoc with ACM-specific formatting rules
- **FR-012**: System MUST format statistical tables using LaTeX booktabs package for publication-quality appearance
- **FR-013**: System MUST escape LaTeX special characters in generated prose (%, $, &, #, etc.)
- **FR-014**: System MUST generate valid LaTeX that compiles with `pdflatex` without errors (warnings acceptable)
- **FR-015**: System MUST preserve citation placeholders `[CITE: description]` in LaTeX output as `\textbf{[CITE: description]}` for easy identification

#### Figure Generation & Export
- **FR-016**: System MUST generate all visualization figures during paper generation (not on-demand)
- **FR-017**: System MUST export figures in both PDF (vector) and PNG (300+ DPI raster) formats
- **FR-018**: System MUST include figure captions with metric descriptions, sample sizes, and statistical test information
- **FR-019**: System MUST provide `--export-figures` flag to generate figures without full paper
- **FR-020**: System MUST provide `--figures-only` flag to regenerate just figures for existing paper

#### Pandoc Integration
- **FR-021**: System MUST detect Pandoc availability before attempting LaTeX conversion
- **FR-022**: System MUST fail with clear error message and installation instructions if Pandoc is missing (no auto-install)
- **FR-023**: System MUST provide error message with OS-specific Pandoc installation commands (apt/brew/choco)
- **FR-024**: System MUST support `--skip-latex` flag to generate Markdown only (skip Pandoc conversion)

#### Documentation Enhancement
- **FR-025**: System MUST enhance generated experiment project's README.md with comprehensive "Reproduction" section
- **FR-026**: System MUST document Python version requirement in README.md (matching generator's Python version)
- **FR-027**: System MUST document dependency installation steps in README.md (pip install -r requirements.txt)
- **FR-028**: System MUST document experiment execution steps in README.md (how to run the experiment)
- **FR-029**: System MUST document analysis execution steps in README.md (how to regenerate reports and figures)
- **FR-030**: System MUST document expected outputs in README.md (list of report files, figure files, data files)
- **FR-031**: System MUST document project structure in README.md (explanation of key directories and files)

#### CLI Architecture
- **FR-032**: System MUST implement paper generation as script in `scripts/` directory (e.g., `scripts/generate_paper.py`)
- **FR-033**: System MUST implement figure export as script in `scripts/` directory (e.g., `scripts/export_figures.py`)
- **FR-034**: Scripts MUST be importable and usable both as CLI tools and as library functions
- **FR-035**: CLI tools MUST accept experiment directory path as primary argument
- **FR-036**: CLI tools MUST support `--help` with comprehensive usage documentation

### Key Entities

- **PaperGenerator**: Main orchestrator that coordinates section generation, figure export, LaTeX conversion, and package assembly
- **SectionGenerator**: Component responsible for generating prose for individual sections (methodology, results, etc.)
- **ProseEngine**: AI-powered text generation using experiment data and statistical results to create comprehensive narratives
- **FigureExporter**: Component that renders matplotlib visualizations to PDF/PNG with publication-quality settings
- **PandocConverter**: Wrapper around Pandoc CLI for Markdown→LaTeX conversion with ACM template integration
- **ReproducibilityPackager**: Component that assembles Docker + requirements + scripts + data into reproducible artifact
- **ACMTemplateBundle**: Collection of ACM SIGSOFT template files (.cls, .bst) with version tracking

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Generated papers compile with `pdflatex` on first attempt with zero errors (warnings acceptable)
- **SC-002**: ALL sections (Introduction, Related Work, Methodology, Results, Discussion, Conclusion) contain ≥800 words of coherent AI-generated prose (not just tables)
- **SC-003**: All AI-generated prose is marked with `[AI-GENERATED - REVIEW REQUIRED]` tags at section or paragraph level
- **SC-004**: Related Work section contains zero actual citations, only placeholders in format `[CITE: description]` (no hallucinated references)
- **SC-005**: All exported figures are valid PDF (vector) and PNG (≥300 DPI)
- **SC-006**: Missing Pandoc dependency results in error message with OS-specific installation command (not crash or silent failure)
- **SC-007**: Generated README.md reproduction section enables independent researcher to reproduce experiment in ≤30 minutes (verified via user testing)
- **SC-008**: Paper generation completes in ≤3 minutes for experiments with 50 runs across 3 frameworks (increased from 2min due to full prose generation)
- **SC-009**: CLI tools display helpful error messages for invalid arguments (not Python stack traces)
- **SC-010**: Citation placeholders are visually distinct in compiled PDF (bold formatting) for easy identification during review

## Clarifications

### Session 2025-10-28 - Feature Scope Definition

- Q: Should paper generation be a separate feature from core report generator refactoring? → A: Yes, split into Feature 010 - Core refactoring (Feature 009) is substantial standalone work
- Q: What level of prose detail should be generated? → A: **FULL AI-generated prose for ALL sections** (Introduction, Related Work, Methodology, Results, Discussion, Conclusion) with manual review markers throughout
- Q: How should Related Work citations be handled? → A: **Citation placeholders** in format `[CITE: description]` to avoid hallucinated references - researcher fills in real citations during review
- Q: Should we target ACM format or generic LaTeX? → A: ACM SIGSOFT format - most SE venues require ACM compliance
- Q: Should Pandoc be auto-installed? → A: No - Detect and fail with clear instructions. Avoids sudo/permission issues.
- Q: Should figures be generated during paper creation or on-demand? → A: During paper creation for complete package, but also support `--figures-only` for regeneration
- Q: Where should CLI tools live? → A: `scripts/` directory as entry points wrapping library functions
- Q: What should reproducibility package include? → A: **Simplified approach** - No separate Docker package. Instead, enhance generated experiment's README.md with comprehensive reproduction instructions (Python version, dependencies, execution steps, expected outputs). Standalone generator already creates reproducible projects.

### Session 2025-10-28 - Risk Mitigation

- **AI-Generated Content Risk**: User will manually review all generated papers before submission. System marks ALL prose with `[AI-GENERATED - REVIEW REQUIRED]` to facilitate comprehensive review.
- **Citation Hallucination Risk**: Use placeholder format `[CITE: description]` instead of generating fake citations. Researcher fills real references during review.
- **LaTeX Compilation Risk**: Bundle known-good ACM template version to ensure reproducibility
- **Pandoc Availability Risk**: Fail-fast with instructions rather than silent degradation
- **Figure Quality Risk**: Export both vector (PDF) and raster (PNG 300+ DPI) to ensure venue compatibility
- **Scope Creep Risk**: Full prose generation for all sections is ambitious (≥800 words per section × 6 sections = ≥4800 words total). User acknowledges increased implementation time (4-5 weeks vs 3-4 weeks) and commits to careful manual review.

## Assumptions

- Feature 009 (refactored report generator with MetricsConfig) is complete and working
- Researchers have basic LaTeX knowledge for final refinement (not complete beginners)
- Pandoc is available as system command (not Python package) - user installs manually
- ACM SIGSOFT template is the target format (not IEEE, Springer, or others)
- Researchers will manually validate all AI-generated causal claims before submission
- Docker is available on systems generating reproducibility packages

## Dependencies

- **Feature 009**: Refactored report_generator.py with MetricsConfig-driven metrics, fail-fast validation
- **Pandoc**: System-level dependency for Markdown→LaTeX conversion (≥2.0)
- **LaTeX Distribution**: pdflatex, required packages (booktabs, graphicx, etc.) for compilation
- **Matplotlib**: For figure generation (already in requirements.txt)
- **ACM Template**: sigconf.cls, ACM-Reference-Format.bst (bundled with system)
- **OpenAI API** (or similar): For AI prose generation across all sections (Introduction, Related Work, Methodology, Results, Discussion, Conclusion)

## Non-Goals

- **Interactive Paper Editing**: No web UI or WYSIWYG editor (LaTeX source only)
- **Multi-Format Support**: Only ACM SIGSOFT (not IEEE, Springer, arXiv-specific formats) in v1
- **Automated Submission**: No integration with conference submission systems
- **Bibliography Management**: Researcher provides own .bib file and fills citation placeholders (not auto-generated)
- **Multi-Language Support**: English prose only
- **Real-time Generation**: Papers generated post-experiment, not during execution
- **AI Model Fine-tuning**: Use standard LLM APIs (no custom model training for prose generation)
- **Plagiarism Checking**: Researcher's responsibility to validate originality and uniqueness of AI-generated prose
- **Actual Citation Generation**: System generates citation placeholders only, not real bibliographic entries
- **Docker Reproducibility Package**: Simplified approach using enhanced README.md instead of full Docker packaging (standalone generator already creates reproducible projects)

## Technical Constraints

- Must maintain Python 3.11+ compatibility
- LaTeX output must compile with standard TeX Live distribution (no exotic packages)
- Pandoc conversion must preserve mathematical notation (KaTeX → LaTeX math)
- Figure generation must work in headless environments (no X11 display required)
- Total output size (paper + figures + reproducibility package) should be <100MB
- Paper generation should complete in ≤2 minutes for typical experiments (50 runs, 3 frameworks)
- Generated Docker images should be ≤2GB compressed

## Implementation Architecture

### Directory Structure (Generated Output)
```
<experiment_name>_paper_package/
├── paper/
│   ├── main.tex                    # Generated LaTeX source
│   ├── main.md                     # Intermediate Markdown
│   ├── acm_template/
│   │   ├── sigconf.cls
│   │   ├── ACM-Reference-Format.bst
│   │   └── acmart.pdf             # Template documentation
│   ├── figures/
│   │   ├── metric_comparison.pdf
│   │   ├── metric_comparison.png
│   │   ├── cost_breakdown.pdf
│   │   └── cost_breakdown.png
│   ├── references.bib              # Empty template for researcher
│   └── compile.sh                  # Helper script: pdflatex + bibtex
└── README.md                       # Overview with enhanced Reproduction section
```

### CLI Tools Architecture
```python
# scripts/generate_paper.py
def main():
    parser = argparse.ArgumentParser(description="Generate camera-ready paper from experiment results")
    parser.add_argument("experiment_dir", help="Path to experiment directory")
    parser.add_argument("--generate-paper", action="store_true", help="Generate full paper")
    parser.add_argument("--export-figures", action="store_true", help="Export figures only")
    parser.add_argument("--package-reproducibility", action="store_true", help="Create reproducibility package")
    parser.add_argument("--skip-latex", action="store_true", help="Generate Markdown only")
    parser.add_argument("--sections", help="Comma-separated sections for full prose")
    parser.add_argument("--prose-level", choices=["minimal", "standard", "comprehensive"])
    # ... more args

# scripts/export_figures.py  
def main():
    parser = argparse.ArgumentParser(description="Export publication-quality figures")
    parser.add_argument("experiment_dir", help="Path to experiment directory")
    parser.add_argument("--format", choices=["pdf", "png", "both"], default="both")
    parser.add_argument("--dpi", type=int, default=300, help="PNG resolution")
    # ... more args
```

### Pandoc Error Handling
```python
def _check_pandoc_available():
    """Detect Pandoc and provide installation instructions if missing."""
    try:
        result = subprocess.run(["pandoc", "--version"], capture_output=True)
        if result.returncode != 0:
            raise PandocMissingError()
    except FileNotFoundError:
        raise PandocMissingError()

class PandocMissingError(Exception):
    def __init__(self):
        msg = """
Pandoc not found. Required for LaTeX conversion.

Installation instructions:
  Ubuntu/Debian: sudo apt-get install pandoc
  macOS: brew install pandoc  
  Windows: choco install pandoc

Or visit: https://pandoc.org/installing.html

Alternatively, use --skip-latex to generate Markdown only.
"""
        super().__init__(msg)
```

### AI-Generated Content Marking & Citation Placeholders
```python
def _mark_ai_generated_section(section_name: str, prose: str) -> str:
    """Mark entire section as AI-generated for manual review."""
    header = f"% {section_name} - [AI-GENERATED - REVIEW REQUIRED]\n"
    header += "% This entire section was generated by AI. Carefully review for:\n"
    header += "%   - Factual accuracy\n"
    header += "%   - Scientific validity\n"
    header += "%   - Citation completeness (fill [CITE: ...] placeholders)\n"
    header += "%   - Logical coherence\n\n"
    return header + prose

def _insert_citation_placeholders(prose: str, context: str) -> str:
    """
    Insert citation placeholders instead of hallucinated references.
    
    Examples:
      "AutoGPT framework" → "AutoGPT framework [CITE: AutoGPT original paper]"
      "Recent studies show" → "Recent studies [CITE: framework comparison studies] show"
    """
    # Framework mentions need citations
    frameworks = ["AutoGPT", "ChatDev", "MetaGPT", "GPT-Engineer"]
    for fw in frameworks:
        prose = re.sub(
            f"({fw})",
            f"\\1 [CITE: {fw} original paper]",
            prose
        )
    
    # Generic research claims need citations
    claim_patterns = [
        (r"(Recent studies|Prior work|Previous research)", "[CITE: relevant studies]"),
        (r"(benchmarks? show|evaluation demonstrates)", "[CITE: benchmark studies]"),
    ]
    
    for pattern, citation in claim_patterns:
        prose = re.sub(pattern, f"\\1 {citation}", prose, flags=re.IGNORECASE)
    
    return prose
```

## Estimated Effort

- **Core Implementation**: 3-4 weeks
  - AI prose generation engine (all sections): 8 days
  - Citation placeholder system: 2 days
  - Paper generation logic: 5 days
  - Pandoc integration: 2 days
  - Figure export: 3 days
  - README enhancement: 2 days
  - CLI tools: 2 days
  
- **Testing & Validation**: 1 week
  - End-to-end paper generation tests
  - AI prose quality validation
  - LaTeX compilation across platforms
  - README reproduction testing
  
- **Documentation**: 3 days
  - User guide for paper generation
  - Example workflows
  - Troubleshooting guide
  - AI review checklist

**Total**: ~4-5 weeks (increased from 3-4 weeks due to full prose generation for all sections)

## Related Documentation

- Feature 009: Core report generator refactoring (prerequisite)
- `docs/METRICS_CONFIG_SCHEMA.md`: Metric definitions used in prose generation
- `docs/QUALITY_METRICS_SUMMARY.md`: Background on measured vs unmeasured metrics
- ACM SIGSOFT Author Guidelines: https://www.acm.org/publications/proceedings-template
- Pandoc User Guide: https://pandoc.org/MANUAL.html
