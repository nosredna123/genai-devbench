# API Contract: Paper Generation

**Version**: 1.0  
**Date**: 2025-10-28

## Overview

This document defines the programmatic interfaces for the paper generation system. All interfaces follow fail-fast principles with explicit error types.

---

## Core Interface: PaperGenerator

### generate_paper()

**Purpose**: Generate complete camera-ready paper from experiment results

**Signature**:
```python
def generate_paper(config: PaperConfig) -> PaperResult:
    """
    Generate camera-ready scientific paper from experiment results.
    
    Args:
        config: Paper generation configuration
    
    Returns:
        PaperResult containing paths to generated files
    
    Raises:
        ConfigValidationError: Invalid configuration
        DependencyMissingError: Required tool not found (Pandoc, LaTeX)
        ExperimentDataError: Experiment directory missing required files
        ProseGenerationError: AI API failure or content too short
        FigureExportError: Figure generation failed
        LatexConversionError: Pandoc conversion failed
        PdfCompilationError: pdflatex compilation failed
    """
```

**Request (PaperConfig)**:
```python
@dataclass
class PaperConfig:
    experiment_dir: Path          # Required: absolute path to experiment
    output_dir: Path              # Required: where to write generated paper
    
    # Optional customization
    sections: list[str] | None = None         # Sections for full prose
    metrics_filter: list[str] | None = None   # Metric categories
    prose_level: str = "standard"             # "minimal" | "standard" | "comprehensive"
    
    # AI configuration
    openai_api_key: str | None = None  # Falls back to env var
    model: str = "gpt-4"
    temperature: float = 0.3
    
    # Output control
    skip_latex: bool = False      # Generate Markdown only
    figures_only: bool = False    # Regenerate just figures
```

**Response (PaperResult)**:
```python
@dataclass
class PaperResult:
    """Result of paper generation operation."""
    
    # Output files
    markdown_path: Path | None    # Markdown source (always generated)
    latex_path: Path | None       # LaTeX source (if !skip_latex)
    pdf_path: Path | None         # Compiled PDF (if !skip_latex)
    
    # Figures
    figure_paths: list[Path]      # All generated figure files (PDF + PNG)
    
    # Metadata
    total_word_count: int         # Total prose word count
    generation_time_seconds: float
    ai_tokens_used: int           # OpenAI API token usage
    
    # Warnings (not errors)
    warnings: list[str] = field(default_factory=list)
```

**Example Usage**:
```python
from src.paper_generation import PaperGenerator, PaperConfig

config = PaperConfig(
    experiment_dir=Path("/path/to/experiment"),
    output_dir=Path("/path/to/output"),
    prose_level="comprehensive"
)

generator = PaperGenerator()
result = generator.generate_paper(config)

print(f"Paper generated: {result.pdf_path}")
print(f"Word count: {result.total_word_count}")
print(f"Figures: {len(result.figure_paths)}")
```

**Error Handling**:
```python
try:
    result = generator.generate_paper(config)
except DependencyMissingError as e:
    print(f"Missing dependency: {e}")
    print(f"Installation: {e.installation_command}")
except ProseGenerationError as e:
    print(f"AI generation failed for section '{e.section}': {e.reason}")
except PdfCompilationError as e:
    print(f"LaTeX compilation failed:\n{e.latex_log}")
```

---

## Interface: FigureExporter

### export_figures()

**Purpose**: Export publication-quality figures from experiment data

**Signature**:
```python
def export_figures(
    experiment_dir: Path,
    output_dir: Path,
    formats: list[str] = ["pdf", "png"],
    dpi: int = 300
) -> list[Figure]:
    """
    Export publication-quality figures from experiment results.
    
    Args:
        experiment_dir: Path to experiment with analysis data
        output_dir: Directory for exported figures
        formats: Output formats ("pdf", "png", or both)
        dpi: PNG resolution (default 300)
    
    Returns:
        List of Figure objects with file paths
    
    Raises:
        ExperimentDataError: Missing analysis data
        FigureExportError: Matplotlib rendering failed
        FileSizeError: Generated figure exceeds 10MB limit
    """
```

**Example**:
```python
from src.paper_generation import FigureExporter

exporter = FigureExporter()
figures = exporter.export_figures(
    experiment_dir=Path("/path/to/experiment"),
    output_dir=Path("/path/to/figures"),
    formats=["pdf", "png"],
    dpi=300
)

for fig in figures:
    print(f"{fig.id}: {fig.pdf_path}")
```

---

## Interface: ProseEngine

### generate_prose()

**Purpose**: Generate AI-powered scientific prose for a paper section

**Signature**:
```python
def generate_prose(
    section_name: str,
    context: SectionContext,
    api_key: str,
    model: str = "gpt-4",
    temperature: float = 0.3
) -> str:
    """
    Generate scientific prose for a specific section using AI.
    
    Args:
        section_name: Section identifier ("introduction", "results", etc.)
        context: Data context for generation
        api_key: OpenAI API key
        model: AI model to use (default "gpt-4")
        temperature: Creativity level 0-1 (default 0.3)
    
    Returns:
        Generated prose text (Markdown format)
    
    Raises:
        ProseGenerationError: API failure or content too short
        ApiKeyError: Invalid or missing API key
        RateLimitError: OpenAI rate limit exceeded
    """
```

**Example**:
```python
from src.paper_generation import ProseEngine, SectionContext

context = SectionContext(
    section_name="results",
    experiment_name="Framework Comparison",
    frameworks=["AutoGPT", "ChatDev"],
    task_description="Build a TODO app",
    statistical_tables={"metric_summary": [...] },
    min_words=800
)

engine = ProseEngine()
prose = engine.generate_prose(
    section_name="results",
    context=context,
    api_key=os.getenv("OPENAI_API_KEY")
)

print(f"Generated {len(prose.split())} words")
```

---

## Interface: CitationHandler

### insert_placeholders()

**Purpose**: Insert citation placeholders in prose to avoid hallucinations

**Signature**:
```python
def insert_placeholders(
    prose: str,
    experiment_frameworks: list[str]
) -> str:
    """
    Insert citation placeholders where references are needed.
    
    Args:
        prose: Generated prose text
        experiment_frameworks: List of frameworks used (for specific citations)
    
    Returns:
        Prose with [CITE: description] placeholders inserted
    """
```

**Example**:
```python
from src.paper_generation import CitationHandler

prose = "AutoGPT is a popular framework. Recent studies show improvements."

handler = CitationHandler()
updated = handler.insert_placeholders(
    prose=prose,
    experiment_frameworks=["AutoGPT", "ChatDev"]
)

# Result: "AutoGPT [CITE: AutoGPT original paper] is a popular framework. 
#          Recent studies [CITE: relevant studies] show improvements."
```

---

## Interface: DocumentFormatter

### format_latex()

**Purpose**: Apply ACM SIGSOFT formatting to paper content

**Signature**:
```python
def format_latex(
    paper: PaperStructure,
    output_path: Path,
    template_dir: Path
) -> Path:
    """
    Format paper content as ACM SIGSOFT LaTeX document.
    
    Args:
        paper: Complete paper structure
        output_path: Where to write LaTeX file
        template_dir: ACM template directory
    
    Returns:
        Path to generated LaTeX file
    
    Raises:
        TemplateError: Missing or corrupted template files
        FormattingError: Invalid content (e.g., unescaped special chars)
    """
```

---

## CLI Contract: generate_paper.py

### Command-Line Interface

**Usage**:
```bash
python scripts/generate_paper.py <experiment_dir> [OPTIONS]
```

**Arguments**:
```
Positional:
  experiment_dir           Path to experiment directory (required)

Options:
  --output-dir DIR         Output directory (default: ./paper_output)
  --sections SECTIONS      Comma-separated sections for full prose
                          (default: all sections)
  --metrics-filter METRICS Comma-separated metric categories
  --prose-level LEVEL      Detail level: minimal|standard|comprehensive
                          (default: standard)
  --skip-latex            Generate Markdown only (skip LaTeX/PDF)
  --figures-only          Regenerate just figures, no paper text
  --model MODEL           AI model (default: gpt-4)
  --temperature FLOAT     AI creativity 0-1 (default: 0.3)
  --help                  Show this help message
```

**Exit Codes**:
- `0`: Success
- `1`: Invalid arguments
- `2`: Missing dependency (Pandoc, LaTeX)
- `3`: Experiment data error
- `4`: AI generation error
- `5`: LaTeX compilation error

**Example**:
```bash
# Full paper generation
python scripts/generate_paper.py /path/to/experiment \
    --output-dir ./output \
    --prose-level comprehensive

# Figures only
python scripts/generate_paper.py /path/to/experiment \
    --figures-only \
    --output-dir ./figures

# Markdown only (skip LaTeX)
python scripts/generate_paper.py /path/to/experiment \
    --skip-latex
```

---

## Error Types

All custom exceptions inherit from `PaperGenerationError`:

```python
class PaperGenerationError(Exception):
    """Base exception for paper generation errors."""
    pass

class ConfigValidationError(PaperGenerationError):
    """Invalid configuration provided."""
    pass

class DependencyMissingError(PaperGenerationError):
    """Required system tool not found."""
    
    def __init__(self, tool: str, min_version: str, installation_cmd: str):
        self.tool = tool
        self.min_version = min_version
        self.installation_command = installation_cmd
        super().__init__(f"{tool} not found (require {min_version}). "
                        f"Install: {installation_cmd}")

class ExperimentDataError(PaperGenerationError):
    """Experiment directory missing required data."""
    pass

class ProseGenerationError(PaperGenerationError):
    """AI prose generation failed."""
    
    def __init__(self, section: str, reason: str):
        self.section = section
        self.reason = reason
        super().__init__(f"Prose generation failed for '{section}': {reason}")

class FigureExportError(PaperGenerationError):
    """Figure generation or export failed."""
    pass

class LatexConversionError(PaperGenerationError):
    """Pandoc conversion to LaTeX failed."""
    pass

class PdfCompilationError(PaperGenerationError):
    """pdflatex compilation failed."""
    
    def __init__(self, latex_log: str):
        self.latex_log = latex_log
        super().__init__(f"PDF compilation failed. See log:\n{latex_log}")
```

---

## Versioning

**API Version**: 1.0  
**Stability**: This is the initial API version. Breaking changes permitted in v2.0 (per Constitution XII).

**Compatibility Promise**: None (fail-fast design, no backward compatibility burden).

---

## Testing Contract

All public interfaces must have:
1. **Unit tests**: Test with mock data, verify fail-fast behavior
2. **Integration tests**: End-to-end paper generation from real experiment
3. **Error tests**: Verify each error type raised correctly

**Test Coverage Target**: ≥80% (per Constitution Technical Standards)
