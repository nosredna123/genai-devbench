"""
Data Models for Camera-Ready Paper Generation

All models implement fail-fast validation with clear error messages.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .exceptions import ConfigValidationError


@dataclass
class PaperConfig:
    """Configuration for camera-ready paper generation."""
    
    # Required fields
    experiment_dir: Path          # Absolute path to experiment directory
    output_dir: Path              # Where to write generated paper
    
    # Optional customization
    sections: list[str] | None = None    # Sections for full prose (None = all)
    metrics_filter: list[str] | None = None  # Metric categories to include
    prose_level: str = "standard"     # "minimal" | "standard" | "comprehensive"
    
    # AI configuration (for paper prose generation only, NOT for experiment execution)
    openai_api_key: str | None = None    # Falls back to OPENAI_API_KEY env var
    model: str = "gpt-5-mini"     # AI model for prose generation (paper only)
    temperature: float = 0.3      # Creativity level (0-1)
    
    # Output format control
    skip_latex: bool = False      # Generate Markdown only (skip Pandoc)
    figures_only: bool = False    # Regenerate just figures, no paper
    
    def __post_init__(self):
        """Validate configuration. Fail-fast on invalid values."""
        # Validate paths exist
        if not self.experiment_dir.exists():
            raise ConfigValidationError(
                f"Experiment directory not found: {self.experiment_dir}",
                field="experiment_dir"
            )
        
        # Validate experiment has runs directory (required for analysis)
        runs_dir = self.experiment_dir / "runs"
        if not runs_dir.exists():
            raise ConfigValidationError(
                f"Experiment directory missing 'runs/' subdirectory: {self.experiment_dir}",
                field="experiment_dir"
            )
        
        # Validate prose level
        valid_levels = ["minimal", "standard", "comprehensive"]
        if self.prose_level not in valid_levels:
            raise ConfigValidationError(
                f"Invalid prose_level: {self.prose_level}. Must be one of {valid_levels}",
                field="prose_level"
            )
        
        # Validate API key (only if not figures_only mode)
        if not self.figures_only:
            if self.openai_api_key is None:
                self.openai_api_key = os.getenv("OPENAI_API_KEY")
                if not self.openai_api_key:
                    raise ConfigValidationError(
                        "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                        "or pass via config.openai_api_key",
                        field="openai_api_key"
                    )
        
        # Validate sections if specified
        if self.sections is not None:
            valid_sections = [
                "abstract", "introduction", "related_work",
                "methodology", "results", "discussion", "conclusion"
            ]
            invalid = set(self.sections) - set(valid_sections)
            if invalid:
                raise ConfigValidationError(
                    f"Invalid sections: {invalid}. Valid sections: {valid_sections}",
                    field="sections"
                )
        
        # Note: metrics_filter validation happens later in validate_metrics_filter()
        # after experiment data is loaded (since available metrics depend on data)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_metrics_filter(self, available_metrics: set[str]) -> None:
        """
        Validate metrics_filter against available metrics from experiment data.
        
        Should be called after loading experiment data.
        
        Args:
            available_metrics: Set of metric names from experiment data
            
        Raises:
            ConfigValidationError: If metrics_filter contains invalid metric names
        """
        if self.metrics_filter is not None:
            invalid = set(self.metrics_filter) - available_metrics
            if invalid:
                raise ConfigValidationError(
                    f"Invalid metrics: {invalid}. Available metrics: {sorted(available_metrics)}",
                    field="metrics_filter"
                )


@dataclass
class Figure:
    """Publication-quality figure with dual format export."""
    
    # File paths (required)
    pdf_path: Path             # Vector format
    png_path: Path             # Raster format (300 DPI)
    caption: str               # Figure caption text
    
    # Identification (optional)
    id: str = ""                    # e.g., "metric_comparison"
    label: str = ""                 # LaTeX label (e.g., "fig:metric_comparison")
    
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
        return f"""\\begin{{figure}}[htbp]
  \\centering
  \\includegraphics[width=\\columnwidth]{{{self.pdf_path.name}}}
  \\caption{{{self.caption}}}
  \\label{{{self.label}}}
\\end{{figure}}"""


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


@dataclass
class SectionContext:
    """Context data for generating a specific paper section."""
    
    section_name: str          # "introduction", "results", etc.
    
    # Experiment metadata
    experiment_summary: str    # High-level description of the experiment
    frameworks: List[str]      # List of frameworks being compared
    num_runs: int              # Number of runs per framework
    
    # Experimental data
    metrics: Dict[str, Any] = field(default_factory=dict)  # Metrics data by framework
    statistical_results: Dict[str, Any] = field(default_factory=dict)  # Statistical test results
    key_findings: List[str] = field(default_factory=list)  # Key findings from analysis
    
    # Legacy fields (for backwards compatibility)
    experiment_name: str = ""
    task_description: str = ""
    
    # Statistical data (for Results section - legacy)
    statistical_tables: Dict = field(default_factory=dict)
    metric_comparisons: Dict = field(default_factory=dict)
    effect_sizes: Dict = field(default_factory=dict)
    p_values: Dict = field(default_factory=dict)
    
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
    figures: list[Figure] = field(default_factory=list)
    
    # Tables
    tables: list[Table] = field(default_factory=list)
    
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
        self.total_word_count = sum(len(s.split()) for s in sections if s)
    
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


@dataclass
class PaperResult:
    """Result of paper generation operation."""
    
    # Output files (required, can be None)
    markdown_path: Path | None
    latex_path: Path | None
    pdf_path: Path | None
    
    # Figures (with default)
    figure_paths: list[Path] = field(default_factory=list)  # All generated figure files (PDF + PNG)
    
    # Metadata (with defaults)
    total_word_count: int = 0         # Total prose word count
    generation_time_seconds: float = 0.0
    ai_tokens_used: int = 0           # OpenAI API token usage
    success: bool = True              # Overall success status
    
    # Warnings (with default)
    warnings: list[str] = field(default_factory=list)
    
    @property
    def figures_generated(self) -> int:
        """Return count of unique figures (PDF+PNG pairs count as 1)."""
        # Count unique figure base names (excluding extensions)
        unique_figures = set()
        for path in self.figure_paths:
            # Remove extension and add to set
            base_name = path.stem
            unique_figures.add(base_name)
        return len(unique_figures)
    
    @property
    def latex_file(self) -> Path | None:
        """Alias for latex_path for backward compatibility."""
        return self.latex_path
    
    @property
    def pdf_file(self) -> Path | None:
        """Alias for pdf_path for backward compatibility."""
        return self.pdf_path
