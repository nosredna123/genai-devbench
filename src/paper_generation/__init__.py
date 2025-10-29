"""
Camera-Ready Paper Generation from Experiment Results

This module generates publication-ready scientific papers in ACM SIGSOFT format
from completed experiment results. It includes AI-powered prose generation,
statistical analysis tables, high-quality figure export, and LaTeX/PDF compilation.

Main Components:
- PaperGenerator: Orchestrates the complete paper generation pipeline
- ProseEngine: AI-powered text generation using OpenAI models (gpt-5-mini default)
- FigureExporter: Publication-quality figure generation (PDF vector + PNG 300 DPI)
- SectionGenerators: Individual generators for each paper section

Usage:
    from paper_generation import PaperGenerator, PaperConfig
    
    config = PaperConfig(
        experiment_dir=Path("/path/to/experiment"),
        output_dir=Path("./paper_output")
    )
    
    result = PaperGenerator().generate_paper(config)
    print(f"Paper generated: {result.pdf_path}")

Note: AI model (gpt-5-mini) is used ONLY for paper prose generation,
NOT for experiment execution or framework interactions.
"""

__version__ = "0.1.0"
__author__ = "genai-devbench"

from .exceptions import (
    PaperGenerationError,
    ConfigValidationError,
    DependencyMissingError,
    ExperimentDataError,
    ProseGenerationError,
    FigureExportError,
    LatexConversionError,
    PdfCompilationError,
)

__all__ = [
    "PaperGenerationError",
    "ConfigValidationError",
    "DependencyMissingError",
    "ExperimentDataError",
    "ProseGenerationError",
    "FigureExportError",
    "LatexConversionError",
    "PdfCompilationError",
]
