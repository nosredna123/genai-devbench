"""Unit tests for paper generation exceptions.

Tests exception types and remediation messages for all error conditions.
"""

from src.paper_generation.exceptions import (
    PaperGenerationError,
    ConfigValidationError,
    DependencyMissingError,
    ExperimentDataError,
    ProseGenerationError,
    FigureExportError,
    LatexConversionError,
    PdfCompilationError
)


class TestPaperGenerationError:
    """Test base exception class."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        err = PaperGenerationError("Something went wrong")
        assert "Something went wrong" in str(err)
    
    def test_error_with_remediation(self):
        """Test error includes remediation guidance."""
        err = PaperGenerationError(
            "Something went wrong",
            remediation="Try fixing it this way"
        )
        assert "Something went wrong" in str(err)
        assert "How to fix:" in str(err)
        assert "Try fixing it this way" in str(err)


class TestConfigValidationError:
    """Test configuration validation errors."""
    
    def test_basic_config_error(self):
        """Test basic configuration error."""
        err = ConfigValidationError("Invalid configuration")
        assert "Invalid configuration" in str(err)
        assert "Check your PaperConfig" in str(err)
    
    def test_field_specific_error(self):
        """Test field-specific error includes field name."""
        err = ConfigValidationError("Invalid value", field="prose_level")
        assert "Invalid value" in str(err)
        assert "prose_level" in str(err)


class TestDependencyMissingError:
    """Test missing dependency errors."""
    
    def test_pandoc_missing(self):
        """Test Pandoc missing error includes installation instructions."""
        err = DependencyMissingError(
            "Pandoc",
            "sudo apt-get install pandoc"
        )
        assert "Pandoc" in str(err)
        assert "sudo apt-get install pandoc" in str(err)
        assert "Install Pandoc" in str(err)
    
    def test_latex_missing(self):
        """Test LaTeX missing error."""
        err = DependencyMissingError(
            "LaTeX",
            "sudo apt-get install texlive-full"
        )
        assert "LaTeX" in str(err)
        assert "texlive-full" in str(err)


class TestExperimentDataError:
    """Test experiment data errors."""
    
    def test_basic_data_error(self):
        """Test basic experiment data error."""
        err = ExperimentDataError("Missing required files")
        assert "Missing required files" in str(err)
        assert "analysis/statistical_report.md" in str(err)
    
    def test_missing_path_error(self):
        """Test error with specific missing path."""
        err = ExperimentDataError(
            "File not found",
            missing_path="/path/to/missing.json"
        )
        assert "File not found" in str(err)
        assert "/path/to/missing.json" in str(err)


class TestProseGenerationError:
    """Test prose generation errors."""
    
    def test_basic_prose_error(self):
        """Test basic prose generation error."""
        err = ProseGenerationError("AI generation failed")
        assert "AI generation failed" in str(err)
        assert "OpenAI API" in str(err)
    
    def test_section_specific_error(self):
        """Test error includes section name."""
        err = ProseGenerationError(
            "Too short",
            section="introduction"
        )
        assert "Too short" in str(err)
        assert "introduction" in str(err)
    
    def test_api_error_included(self):
        """Test error includes API error details."""
        err = ProseGenerationError(
            "Request failed",
            api_error="Rate limit exceeded"
        )
        assert "Request failed" in str(err)
        assert "Rate limit exceeded" in str(err)


class TestFigureExportError:
    """Test figure export errors."""
    
    def test_basic_figure_error(self):
        """Test basic figure export error."""
        err = FigureExportError("Export failed")
        assert "Export failed" in str(err)
        assert "Matplotlib" in str(err)
    
    def test_figure_name_included(self):
        """Test error includes figure name."""
        err = FigureExportError(
            "Rendering failed",
            figure_name="cost_comparison.pdf"
        )
        assert "Rendering failed" in str(err)
        assert "cost_comparison.pdf" in str(err)


class TestLatexConversionError:
    """Test LaTeX conversion errors."""
    
    def test_basic_conversion_error(self):
        """Test basic conversion error."""
        err = LatexConversionError("Conversion failed")
        assert "Conversion failed" in str(err)
        assert "Pandoc" in str(err)
    
    def test_pandoc_output_included(self):
        """Test error includes Pandoc output."""
        err = LatexConversionError(
            "Syntax error",
            pandoc_output="Error at line 42: unclosed code block"
        )
        assert "Syntax error" in str(err)
        assert "line 42" in str(err)
        assert "unclosed code block" in str(err)


class TestPdfCompilationError:
    """Test PDF compilation errors."""
    
    def test_basic_pdf_error(self):
        """Test basic PDF compilation error."""
        err = PdfCompilationError("Compilation failed")
        assert "Compilation failed" in str(err)
        assert "LaTeX distribution" in str(err)
    
    def test_latex_log_included(self):
        """Test error includes LaTeX log excerpt."""
        long_log = "\n".join([f"Line {i}" for i in range(100)])
        err = PdfCompilationError(
            "Missing package",
            latex_log=long_log
        )
        assert "Missing package" in str(err)
        # Should include last 20 lines
        assert "Line 99" in str(err)
        assert "Line 80" in str(err)
        # Should not include early lines
        assert "Line 1" not in str(err)
