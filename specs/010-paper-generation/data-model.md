# Data Model: Camera-Ready Paper Generation

**Feature**: 010-paper-generation  
**Date**: 2025-10-28  
**Status**: Phase 1

## Overview

This document defines the data structures and entities used in the paper generation system. All entities are designed for fail-fast validation and clear error messages.

---

## Core Entities

### PaperConfig

**Purpose**: Configuration for paper generation request

**Fields**:
```python
@dataclass
class PaperConfig:
    """Configuration for camera-ready paper generation."""
    
    # Required fields
    experiment_dir: Path          # Absolute path to experiment directory
    output_dir: Path              # Where to write generated paper
    
    # Optional customization
    sections: list[str] = None    # Sections for full prose (None = all)
    metrics_filter: list[str] = None  # Metric categories to include
    prose_level: str = "standard"     # "minimal" | "standard" | "comprehensive"
    
    # AI configuration (for paper prose generation only, NOT for experiment execution)
    openai_api_key: str = None    # Falls back to OPENAI_API_KEY env var
    model: str = "gpt-5-mini"     # AI model for prose generation (paper only)
    temperature: float = 0.3      # Creativity level (0-1)
    
    # Output format control
    skip_latex: bool = False      # Generate Markdown only (skip Pandoc)
    figures_only: bool = False    # Regenerate just figures, no paper
    
    def __post_init__(self):
        """Validate configuration. Fail-fast on invalid values."""
        # Validate paths exist
        if not self.experiment_dir.exists():
            raise ValueError(f"Experiment directory not found: {self.experiment_dir}")
        
        # Validate prose level
        valid_levels = ["minimal", "standard", "comprehensive"]
        if self.prose_level not in valid_levels:
            raise ValueError(f"Invalid prose_level: {self.prose_level}. "
                           f"Must be one of {valid_levels}")
        
        # Validate API key
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY "
                               "environment variable or pass via config.")
        
        # Validate sections if specified
        if self.sections is not None:
            valid_sections = [
                "abstract", "introduction", "related_work",
                "methodology", "results", "discussion", "conclusion"
            ]
            invalid = set(self.sections) - set(valid_sections)
            if invalid:
                raise ValueError(f"Invalid sections: {invalid}. "
                               f"Valid: {valid_sections}")
```

**Validation Rules**:
- `experiment_dir` must exist and contain `analysis/` subdirectory
- `prose_level` must be one of: "minimal", "standard", "comprehensive"
- `openai_api_key` required (from config or env var)
- `sections` if specified must be valid section names
- `output_dir` created automatically if missing

**Usage Example**:
```python
config = PaperConfig(
    experiment_dir=Path("/path/to/experiment"),
    output_dir=Path("/path/to/output"),
    sections=["methodology", "results"],
    prose_level="comprehensive"
)
```

---

### PaperStructure

**Purpose**: Complete paper content organized by section

**Fields**:
```python
@dataclass
class PaperStructure:
    """Generated paper content organized by section."""
    
    # Metadata
    title: str
    authors: list[str]
    abstract: str
    
    # Main sections (prose content)
    introduction: str
    related_work: str
    methodology: str
    results: str
    discussion: str
    conclusion: str
    
    # Supporting content
    acknowledgments: str = ""
    references_template: str = ""  # Empty BibTeX template
    
    # Figures
    figures: list['Figure'] = field(default_factory=list)
    
    # Tables
    tables: list['Table'] = field(default_factory=list)
    
    # Generation metadata
    generated_at: datetime = field(default_factory=datetime.now)
    ai_model: str = "gpt-5-mini"
    total_word_count: int = 0
    
    def __post_init__(self):
        """Calculate total word count."""
        sections = [
            self.introduction,
            self.related_work,
            self.methodology,
            self.results,
            self.discussion,
            self.conclusion
        ]
        self.total_word_count = sum(len(s.split()) for s in sections)
    
    def to_markdown(self) -> str:
        """Export full paper as Markdown."""
        md = f"# {self.title}\n\n"
        md += f"**Authors**: {', '.join(self.authors)}\n\n"
        md += f"## Abstract\n\n{self.abstract}\n\n"
        md += f"## Introduction\n\n{self.introduction}\n\n"
        md += f"## Related Work\n\n{self.related_work}\n\n"
        md += f"## Methodology\n\n{self.methodology}\n\n"
        md += f"## Results\n\n{self.results}\n\n"
        md += f"## Discussion\n\n{self.discussion}\n\n"
        md += f"## Conclusion\n\n{self.conclusion}\n\n"
        if self.acknowledgments:
            md += f"## Acknowledgments\n\n{self.acknowledgments}\n\n"
        md += "## References\n\n[Researcher to provide bibliography]\n"
        return md
```

**Validation Rules**:
- Each section must contain ≥100 words (fail-fast if AI generation too short)
- Total word count must be ≥4800 words (800 × 6 sections)
- Title and authors required (extracted from experiment config)

---

### Figure

**Purpose**: Publication-quality figure with metadata

**Fields**:
```python
@dataclass
class Figure:
    """Publication-quality figure with dual format export."""
    
    # Identification
    id: str                    # e.g., "metric_comparison"
    caption: str               # Figure caption text
    label: str                 # LaTeX label (e.g., "fig:metric_comparison")
    
    # File paths
    pdf_path: Path             # Vector format
    png_path: Path             # Raster format (300 DPI)
    
    # Metadata
    width_inches: float = 6.5  # ACM 2-column width
    height_inches: float = 4.0 # Aspect ratio ~1.6:1
    dpi: int = 300             # PNG resolution
    
    # Source data reference
    data_source: str = ""      # Description of data used
    
    def __post_init__(self):
        """Validate figure files exist."""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF figure not found: {self.pdf_path}")
        if not self.png_path.exists():
            raise FileNotFoundError(f"PNG figure not found: {self.png_path}")
        
        # Verify file sizes (fail-fast if too large)
        pdf_size_mb = self.pdf_path.stat().st_size / 1_000_000
        png_size_mb = self.png_path.stat().st_size / 1_000_000
        
        if pdf_size_mb > 10:
            raise ValueError(f"PDF too large ({pdf_size_mb:.1f}MB > 10MB): {self.pdf_path}")
        if png_size_mb > 10:
            raise ValueError(f"PNG too large ({png_size_mb:.1f}MB > 10MB): {self.png_path}")
    
    def to_latex(self) -> str:
        """Generate LaTeX figure environment."""
        return f"""
\\begin{{figure}}[htbp]
  \\centering
  \\includegraphics[width=\\columnwidth]{{{self.pdf_path.name}}}
  \\caption{{{self.caption}}}
  \\label{{{self.label}}}
\\end{{figure}}
"""
```

**Validation Rules**:
- PDF and PNG files must exist
- File sizes must be <10MB each
- Width must fit ACM 2-column layout (≤6.5 inches)
- DPI must be ≥300 for PNG

---

### Table

**Purpose**: Statistical table with publication formatting

**Fields**:
```python
@dataclass
class Table:
    """Statistical table with booktabs formatting."""
    
    # Identification
    id: str                    # e.g., "metric_summary"
    caption: str               # Table caption text
    label: str                 # LaTeX label (e.g., "tab:metric_summary")
    
    # Data
    headers: list[str]         # Column headers
    rows: list[list[str]]      # Table data (pre-formatted strings)
    
    # Formatting
    alignment: str = "lrrrr"   # LaTeX column alignment (l=left, r=right, c=center)
    
    def __post_init__(self):
        """Validate table structure."""
        # Check all rows have same length
        expected_cols = len(self.headers)
        for i, row in enumerate(self.rows):
            if len(row) != expected_cols:
                raise ValueError(f"Row {i} has {len(row)} columns, expected {expected_cols}")
        
        # Check alignment matches column count
        if len(self.alignment) != expected_cols:
            raise ValueError(f"Alignment string has {len(self.alignment)} chars, "
                           f"expected {expected_cols}")
    
    def to_latex(self) -> str:
        """Generate LaTeX table with booktabs formatting."""
        lines = [
            "\\begin{table}[htbp]",
            "  \\centering",
            f"  \\caption{{{self.caption}}}",
            f"  \\label{{{self.label}}}",
            f"  \\begin{{tabular}}{{{self.alignment}}}",
            "    \\toprule"
        ]
        
        # Headers
        lines.append(f"    {' & '.join(self.headers)} \\\\")
        lines.append("    \\midrule")
        
        # Data rows
        for row in self.rows:
            lines.append(f"    {' & '.join(row)} \\\\")
        
        lines.extend([
            "    \\bottomrule",
            "  \\end{tabular}",
            "\\end{table}"
        ])
        
        return "\n".join(lines)
```

**Validation Rules**:
- All rows must have same number of columns as headers
- Alignment string length must match column count
- Headers and data must not contain unescaped LaTeX special characters

---

### SectionContext

**Purpose**: Data context for AI prose generation

**Fields**:
```python
@dataclass
class SectionContext:
    """Context data for generating a specific paper section."""
    
    section_name: str          # "introduction", "results", etc.
    
    # Experiment metadata
    experiment_name: str
    frameworks: list[str]
    task_description: str
    
    # Statistical data (for Results section)
    statistical_tables: dict = field(default_factory=dict)
    metric_comparisons: dict = field(default_factory=dict)
    effect_sizes: dict = field(default_factory=dict)
    p_values: dict = field(default_factory=dict)
    
    # Configuration
    min_words: int = 800       # Minimum prose length
    prose_level: str = "standard"  # Detail level
    
    def to_prompt_dict(self) -> dict:
        """Convert to structured data for AI prompt."""
        return {
            "section": self.section_name,
            "experiment": self.experiment_name,
            "frameworks": self.frameworks,
            "task": self.task_description,
            "statistics": {
                "tables": self.statistical_tables,
                "comparisons": self.metric_comparisons,
                "effect_sizes": self.effect_sizes,
                "p_values": self.p_values
            },
            "requirements": {
                "min_words": self.min_words,
                "detail_level": self.prose_level
            }
        }
```

**Usage**: Passed to ProseEngine to generate section-specific content

---

## Relationships

```
PaperConfig
    ↓ (input to)
PaperGenerator
    ↓ (creates)
PaperStructure
    ↓ (contains)
├── Section prose (str)
├── Figure[] (list)
└── Table[] (list)
```

**Flow**:
1. User creates `PaperConfig` with experiment directory
2. `PaperGenerator` loads experiment data
3. For each section, create `SectionContext` with relevant data
4. `ProseEngine` generates prose from `SectionContext`
5. `FigureExporter` creates `Figure` objects
6. `PaperStructure` assembles all content
7. `DocumentFormatter` converts to LaTeX/PDF

---

## State Transitions

### Paper Generation Lifecycle

```
[Config Created]
    ↓
[Validation] → FAIL (invalid config) → ERROR
    ↓ PASS
[Dependency Check] → FAIL (Pandoc missing) → ERROR
    ↓ PASS
[Load Experiment Data]
    ↓
[Generate Sections] (6 sections in parallel)
    ↓
[Export Figures]
    ↓
[Assemble Paper]
    ↓
[Convert to LaTeX] (if !skip_latex)
    ↓
[Compile PDF]
    ↓
[SUCCESS]
```

**Failure Points** (fail-fast):
- Config validation: Invalid paths, missing API key
- Dependency check: Pandoc not found or version <2.0
- Data loading: Experiment directory missing analysis results
- Prose generation: API failure, content too short
- Figure export: Matplotlib error, file size exceeded
- LaTeX conversion: Pandoc error, malformed math
- PDF compilation: pdflatex error, missing template files

---

## Validation Summary

All entities implement fail-fast validation:
- **PaperConfig**: Validates on initialization (\_\_post_init\_\_)
- **Figure**: Checks file existence and sizes
- **Table**: Validates row structure
- **PaperStructure**: Verifies minimum word counts

Error messages include:
- Absolute file paths (for debugging)
- Expected vs actual values
- Clear remediation steps (e.g., "Install Pandoc ≥2.0")

This aligns with Constitution Principle XIII (Fail-Fast Philosophy).
