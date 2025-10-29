# Research Notes: Camera-Ready Paper Generation

**Feature**: 010-paper-generation  
**Date**: 2025-10-28  
**Status**: Phase 0 Complete

## Research Tasks

### Task 1: Pandoc Version Requirements and LaTeX Conversion Best Practices

**Unknown from Technical Context**: "Pandoc (external system tool - Markdown→LaTeX conversion, NEEDS CLARIFICATION: version requirements)"

**Research Question**: What Pandoc version is required for reliable Markdown→LaTeX conversion with mathematical notation preservation?

**Decision**: Require Pandoc ≥2.0 (released 2017)

**Rationale**:
- Pandoc 2.0+ has stable CommonMark parser with improved math support
- LaTeX math mode preservation works reliably in 2.x series
- Version 2.0 is widely available in package managers (Ubuntu 20.04+, macOS Homebrew, Windows Chocolatey)
- Older versions (1.x) had issues with complex math expressions and table formatting

**Alternatives Considered**:
1. **Pandoc 3.x only** (latest): Rejected - too new, not available in older LTS distributions
2. **Pandoc 1.x**: Rejected - unstable math rendering, missing features for academic papers
3. **No version requirement**: Rejected - violates fail-fast principle, would lead to silent math rendering bugs

**Implementation Notes**:
- Check version via `pandoc --version` in PandocConverter initialization
- Fail-fast with error message if version <2.0 detected
- Provide OS-specific installation commands in error message

---

### Task 2: AI Prose Generation Approaches for Scientific Papers

**Unknown from Technical Context**: How to generate ≥800 words of coherent scientific prose per section (6 sections = 4800+ words total)?

**Research Question**: What prompt engineering strategy produces publication-quality scientific prose from experiment data?

**Decision**: Use **structured multi-turn prompts** with OpenAI GPT-5 models (default: gpt-5-mini) via OpenAI API **for paper generation only**

**Scope**: This AI configuration is **ONLY** for generating paper prose. Experiment execution and framework interactions use their own model configurations (unchanged).

**Rationale**:
- **Structured prompts** prevent hallucinations by grounding generation in experiment data
- **Multi-turn approach**: First turn generates outline, second turn expands each point into full prose
- **Model flexibility**: Default to cost-effective gpt-5-mini, allow upgrade to gpt-5 or other models via --model flag
- **Explicit constraints**: Prompts specify "no citations" for related work to enforce placeholder-only strategy

**Prompt Strategy**:

```python
# Example for Results section
RESULTS_PROMPT_TEMPLATE = """
You are a computer science researcher writing the Results section of a conference paper.

EXPERIMENT DATA:
{statistical_tables}
{metric_comparisons}
{effect_sizes}

TASK: Write the Results section (≥800 words) following this structure:
1. Overview of findings (1-2 paragraphs)
2. Detailed metric analysis (3-4 paragraphs, one per metric category)
3. Statistical significance summary (1 paragraph)

REQUIREMENTS:
- Use formal academic tone
- Cite specific numbers from the data (p-values, effect sizes, means)
- Do NOT make causal claims beyond what statistics support
- Do NOT invent or hallucinate any data not provided above
- Mark any interpretations as "this suggests..." or "this indicates..."

Generate ONLY the prose content. Do not include section heading.
"""
```

**Alternatives Considered**:
1. **Template-based generation** (fill-in-the-blanks): Rejected - too rigid, doesn't adapt to varied experiment results
2. **GPT-4o-mini**: Rejected - gpt-5-mini provides better quality with latest improvements
3. **Fine-tuned model**: Rejected - violates "no AI model customization" non-goal, requires training infrastructure

**Implementation Notes**:
- Store prompts as constants in `prose_engine.py`
- Use `requests` library to call OpenAI API (existing dependency)
- Implement retry logic for API failures (exponential backoff)
- Log all API calls with token usage for cost tracking

---

### Task 3: Citation Placeholder Strategy

**Unknown from Technical Context**: How to insert citation placeholders without hallucinating references?

**Research Question**: What placeholder format is both human-readable and LaTeX-safe?

**Decision**: Use format `[CITE: descriptive text]` in Markdown, render as `\textbf{[CITE: ...]}` in LaTeX

**Rationale**:
- **Markdown format** `[CITE: description]` is clear and search-friendly
- **LaTeX bold rendering** `\textbf{}` makes placeholders visually distinct in PDF
- **Descriptive text** helps researcher identify which paper to cite (e.g., "[CITE: AutoGPT original paper]")
- **No automatic expansion** prevents hallucination - researcher must manually add real citation keys

**Citation Detection Strategy**:
1. **Framework names**: AutoGPT, ChatDev, MetaGPT → auto-insert "[CITE: {framework} original paper]"
2. **Research claims**: "Recent studies show..." → insert "[CITE: relevant prior work]"
3. **Benchmark references**: "Previous benchmarks..." → insert "[CITE: framework comparison studies]"

**Alternatives Considered**:
1. **BibTeX key placeholders** (`\cite{PLACEHOLDER}`): Rejected - looks like broken citation, confusing
2. **HTML comments** (`<!-- CITE: ... -->`): Rejected - invisible in PDF, easy to miss during review
3. **Empty cite commands** (`\cite{}`): Rejected - breaks LaTeX compilation
4. **Generate real citations from database**: Rejected - high hallucination risk, violates spec requirement

**Implementation Notes**:
- Implement in `citation_handler.py` with regex patterns
- Run after prose generation but before LaTeX conversion
- Maintain list of detected frameworks from experiment config

---

### Task 4: ACM SIGSOFT Template Integration

**Unknown from Technical Context**: Which ACM template files are required and where to source them?

**Research Question**: What is the minimal ACM SIGSOFT template bundle for reproducible paper generation?

**Decision**: Bundle ACM `sigconf` template (v1.90 as of 2025) with the following files

**Required Files**:
```
templates/acm_sigsoft/
├── sigconf.cls           # Document class (2-column ACM format)
├── ACM-Reference-Format.bst  # Bibliography style
├── acmart.pdf            # Template documentation
└── VERSION               # Version tracking file (contains "1.90")
```

**Rationale**:
- **sigconf.cls**: ACM SIGSOFT uses "sigconf" mode (conference proceedings format)
- **ACM-Reference-Format.bst**: Standard ACM bibliography style
- **acmart.pdf**: User documentation for template usage
- **VERSION file**: Track template version for reproducibility (fail-fast if missing/mismatched)

**Source**: ACM official template repository (https://www.acm.org/publications/proceedings-template)

**Alternatives Considered**:
1. **Download on-demand**: Rejected - requires network, fails in offline environments
2. **Full acmart package** (all document classes): Rejected - bloat, only need sigconf
3. **User-provided template**: Rejected - violates "bundle required files" requirement (FR-010)

**Implementation Notes**:
- Check in template files to `templates/acm_sigsoft/` directory
- Verify VERSION file in `template_bundle.py` initialization
- Copy templates to generated paper output directory during generation

---

### Task 5: Figure Generation for Publication Quality

**Unknown from Technical Context**: How to generate Matplotlib figures meeting publication standards (≥300 DPI, vector formats)?

**Research Question**: What Matplotlib settings ensure publication-quality figure export?

**Decision**: Use dual export strategy - PDF (vector) + PNG (300 DPI raster)

**Matplotlib Configuration**:
```python
import matplotlib
matplotlib.use('Agg')  # Headless backend (no X11 display needed)

import matplotlib.pyplot as plt

# Publication-quality settings
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,        # High-resolution raster
    'savefig.dpi': 300,       # Export DPI
    'savefig.format': 'pdf',  # Default vector format
    'savefig.bbox': 'tight',  # Remove whitespace
})

# Dual export
fig.savefig('figure.pdf', format='pdf')  # Vector
fig.savefig('figure.png', format='png', dpi=300)  # Raster
```

**Rationale**:
- **PDF**: Scalable, preferred by publishers, small file size for simple plots
- **PNG 300 DPI**: Fallback for complex plots, compatible with all systems
- **Headless backend (`Agg`)**: Works in server environments without display
- **Times New Roman**: Matches ACM SIGSOFT paper body font
- **Tight bounding box**: Professional appearance, no wasted whitespace

**Alternatives Considered**:
1. **SVG only**: Rejected - not universally supported by LaTeX compilers
2. **PNG only**: Rejected - not scalable, looks pixelated when zoomed
3. **EPS format**: Rejected - deprecated, larger file sizes than PDF
4. **Interactive backend**: Rejected - requires X11, fails in headless environments

**Implementation Notes**:
- Set Matplotlib backend in `figure_exporter.py` module initialization
- Implement dual export in `export_figure()` method
- Verify file sizes <10MB per figure (fail-fast if exceeded)

---

### Task 6: README Enhancement for Reproducibility Documentation

**Unknown from Technical Context**: What sections should be added to generated experiment README.md?

**Research Question**: What information enables independent reproduction in ≤30 minutes?

**Decision**: Add comprehensive "Reproduction" section with 5 subsections

**README Structure**:
```markdown
# [Existing experiment README content]

## Reproduction

This section provides complete instructions for reproducing this experiment and regenerating analysis reports.

### Environment Requirements
- Python 3.11+ (exact version: 3.11.5 used in original run)
- Operating System: Linux (Ubuntu 22.04), macOS (13+), or Windows 10+
- Required system tools: git, pandoc ≥2.0, pdflatex (TeX Live 2023)
- Memory: ≥4GB RAM
- Disk space: ≥2GB free

### Dependency Installation
```bash
# Clone this repository (if from archive)
git clone <url> experiment-reproduction
cd experiment-reproduction

# Install Python dependencies
pip install -r requirements.txt

# Verify Pandoc (optional, for paper regeneration)
pandoc --version  # Should show ≥2.0
```

### Running the Experiment
```bash
# Execute experiment run (reproduces original data collection)
python run_experiment.py --config config/experiment.yaml

# Expected runtime: 30-45 minutes for 50 runs across 3 frameworks
# Output: runs/<framework>/<run-id>/ directories with logs and metrics
```

### Regenerating Analysis Reports
```bash
# Generate statistical reports and figures
python scripts/generate_reports.py --experiment-dir .

# Output files:
#   - analysis/statistical_report.md
#   - analysis/figures/*.png
#   - analysis/figures/*.pdf
```

### Expected Outputs
After successful reproduction, you should have:
- `runs/` directory with per-framework run data
- `analysis/statistical_report.md` with metric comparisons
- `analysis/figures/` with metric plots (PDF + PNG)
- `paper/main.pdf` (camera-ready paper, if generated)

If any step fails, see `docs/troubleshooting.md` or file an issue.
```

**Rationale**:
- **Environment Requirements**: Prevents "works on my machine" issues
- **Exact versions**: Python 3.11.5 specificity enables bit-identical reproduction
- **Step-by-step commands**: Copy-paste workflow, no guessing
- **Expected outputs**: Verification checklist for successful reproduction
- **Troubleshooting reference**: Reduces support burden

**Alternatives Considered**:
1. **Minimal README** (just "run run_experiment.sh"): Rejected - insufficient for independent reproduction
2. **Docker-only approach**: Rejected - spec explicitly chose "enhanced README" over Docker package
3. **Video tutorial**: Rejected - not text-searchable, harder to maintain

**Implementation Notes**:
- Template stored in `templates/readme_reproduction_section.md`
- Inject experiment-specific values (Python version, framework list, runtime estimates)
- Append to existing experiment README during paper generation

---

## Best Practices Identified

### LaTeX Best Practices for Scientific Papers
- Use `booktabs` package for publication-quality tables (no vertical lines)
- Escape special characters: `%`, `$`, `&`, `#`, `_`, `{`, `}`, `~`, `^`, `\`
- Math mode delimiters: inline `$...$`, display `$$...$$` or `\[...\]`
- Figure placement: use `[htbp]` for flexible positioning
- Caption formatting: `\caption{Description}` before `\label{fig:key}`

### OpenAI API Best Practices
- Default model: `gpt-5-mini` (cost-effective, latest generation quality)
- Allow model override via `--model` flag (e.g., `gpt-5`, `gpt-4o`, `gpt-4-turbo`)
- Set `temperature=0.3` (low but not zero - allows slight variation while staying factual)
- Implement exponential backoff retry (3 attempts with 1s, 2s, 4s delays)
- Log token usage for cost tracking and debugging
- Cache API responses during development (avoid redundant calls)

### Pandoc Conversion Best Practices
- Use `--standalone` flag for complete LaTeX documents
- Specify input format explicitly: `--from=markdown+tex_math_dollars`
- Preserve math: `--mathjax` or `--katex` flags (KaTeX recommended for speed)
- Template variable syntax: `$if(title)$ $title$ $endif$`
- Validate output with `pdflatex -interaction=nonstopmode` (catch errors)

### Error Handling Best Practices
- Detect missing tools before generation starts (fail-fast)
- Provide OS-specific installation commands in error messages
- Use absolute paths in error messages (aid debugging)
- Log full command output for subprocess failures
- Distinguish user errors (missing input) from system errors (API failure)

---

## Technology Integration Patterns

### Pattern 1: Pandoc Wrapper with Fail-Fast Detection

```python
class PandocConverter:
    """Wrapper around Pandoc CLI for Markdown→LaTeX conversion."""
    
    MIN_VERSION = (2, 0)
    
    def __init__(self):
        """Initialize and verify Pandoc availability."""
        self._verify_pandoc()
    
    def _verify_pandoc(self):
        """Detect Pandoc and check version. Fail-fast if missing or too old."""
        try:
            result = subprocess.run(
                ['pandoc', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse version from first line: "pandoc 2.19.2"
            version_line = result.stdout.split('\n')[0]
            version_str = version_line.split()[1]
            version = tuple(map(int, version_str.split('.')[:2]))
            
            if version < self.MIN_VERSION:
                raise PandocVersionError(version, self.MIN_VERSION)
        
        except FileNotFoundError:
            raise PandocMissingError()
    
    def convert(self, markdown_path: str, output_path: str):
        """Convert Markdown to LaTeX using ACM template."""
        cmd = [
            'pandoc',
            '--from=markdown+tex_math_dollars',
            '--to=latex',
            '--standalone',
            '--template=templates/acm_sigsoft/template.tex',
            '-o', output_path,
            markdown_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Fail-fast with full error output
            raise PandocConversionError(markdown_path, e.stderr.decode())
```

### Pattern 2: AI Prose Generation with Structured Prompts

```python
class ProseEngine:
    """AI-powered text generation for scientific paper sections."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_section(
        self, 
        section_name: str, 
        context_data: dict, 
        min_words: int = 800,
        model: str = "gpt-5-mini"
    ) -> str:
        """Generate prose for a paper section using OpenAI API."""
        
        prompt = self._build_prompt(section_name, context_data, min_words)
        
        # Call OpenAI API with retry logic
        for attempt in range(3):
            try:
                response = requests.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,  # Configurable model (default: gpt-5-mini)
                        "messages": [
                            {"role": "system", "content": "You are an expert CS researcher."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=60
                )
                response.raise_for_status()
                
                prose = response.json()['choices'][0]['message']['content']
                
                # Validate length
                word_count = len(prose.split())
                if word_count < min_words:
                    raise ProseTooShortError(section_name, word_count, min_words)
                
                return prose
            
            except requests.exceptions.RequestException as e:
                if attempt == 2:  # Last attempt
                    raise ProseGenerationError(section_name, str(e))
                time.sleep(2 ** attempt)  # Exponential backoff
```

### Pattern 3: Citation Placeholder Insertion

```python
class CitationHandler:
    """Insert citation placeholders to avoid hallucinated references."""
    
    FRAMEWORK_NAMES = ['AutoGPT', 'ChatDev', 'MetaGPT', 'GPT-Engineer']
    
    CLAIM_PATTERNS = [
        (r'(Recent studies|Prior work|Previous research)\s+show', r'\1 [CITE: relevant studies] show'),
        (r'(benchmark|evaluation)\s+demonstrates', r'\1 [CITE: benchmark studies] demonstrates'),
        (r'(has been shown|have been shown)', r'[CITE: prior work] \1'),
    ]
    
    def insert_placeholders(self, prose: str, experiment_frameworks: list) -> str:
        """Insert citation placeholders where references are needed."""
        
        # Framework-specific citations
        for framework in experiment_frameworks:
            if framework in self.FRAMEWORK_NAMES:
                pattern = rf'\b({framework})\b'
                replacement = rf'\1 [CITE: {framework} original paper]'
                prose = re.sub(pattern, replacement, prose)
        
        # Generic research claim citations
        for pattern, replacement in self.CLAIM_PATTERNS:
            prose = re.sub(pattern, replacement, prose, flags=re.IGNORECASE)
        
        return prose
    
    def render_latex(self, prose: str) -> str:
        """Convert [CITE: ...] placeholders to bold LaTeX."""
        return re.sub(
            r'\[CITE: ([^\]]+)\]',
            r'\\textbf{[CITE: \1]}',
            prose
        )
```

---

## Open Questions for Phase 1

1. **Data model for paper configuration**: How should users specify section selection, metric filtering, prose detail level? (Addressed in data-model.md)

2. **API contract for figure export**: Should it return file paths, bytes, or both? (Addressed in contracts/)

3. **Error recovery strategy**: Should partial paper generation be allowed (e.g., skip figures if matplotlib fails), or fail-fast? (Answer: Fail-fast per Constitution XIII)

4. **Template customization**: Should users be able to override ACM template with custom LaTeX templates in v1? (Answer: No, per non-goal "Multi-Format Support")

---

## Phase 0 Summary

All unknowns from Technical Context resolved:
- ✅ Pandoc version requirements determined (≥2.0)
- ✅ AI prose generation approach selected (gpt-5-mini default with --model override)
- ✅ Citation placeholder strategy defined ([CITE: description] format)
- ✅ ACM template bundle identified (sigconf v1.90)
- ✅ Figure quality settings specified (PDF vector + PNG 300 DPI)
- ✅ README enhancement structure designed (5-subsection Reproduction guide)

Proceeding to Phase 1: Data Model and API Contracts.
