"""Unit tests for paper generation data models.

Tests PaperConfig validation, Figure file checks, and model validation.
"""

import os
from pathlib import Path
import pytest
from src.paper_generation.models import (
    PaperConfig,
    Figure,
    Table,
    SectionContext,
    PaperStructure,
    PaperResult
)


class TestPaperConfig:
    """Test PaperConfig validation."""
    
    def test_valid_config(self, tmp_path):
        """Test valid configuration passes validation."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        # Set API key for test
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        config = PaperConfig(
            experiment_dir=exp_dir,
            output_dir=tmp_path / "output"
        )
        
        assert config.experiment_dir == exp_dir
        assert config.prose_level == "standard"  # default
        assert config.model == "gpt-5-mini"  # default
    
    def test_missing_experiment_dir(self, tmp_path):
        """Test error when experiment directory doesn't exist."""
        with pytest.raises(ValueError, match="Experiment directory not found"):
            PaperConfig(
                experiment_dir=tmp_path / "nonexistent",
                output_dir=tmp_path / "output"
            )
    
    def test_invalid_prose_level(self, tmp_path):
        """Test error for invalid prose level."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        with pytest.raises(ValueError, match="Invalid prose_level"):
            PaperConfig(
                experiment_dir=exp_dir,
                output_dir=tmp_path / "output",
                prose_level="invalid"
            )
    
    def test_valid_prose_levels(self, tmp_path):
        """Test all valid prose levels."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        for level in ["minimal", "standard", "comprehensive"]:
            config = PaperConfig(
                experiment_dir=exp_dir,
                output_dir=tmp_path / "output",
                prose_level=level,
                openai_api_key="test-key"
            )
            assert config.prose_level == level
    
    def test_api_key_from_env(self, tmp_path):
        """Test API key loaded from environment."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        os.environ["OPENAI_API_KEY"] = "env-key"
        
        config = PaperConfig(
            experiment_dir=exp_dir,
            output_dir=tmp_path / "output"
        )
        
        assert config.openai_api_key == "env-key"
    
    def test_missing_api_key(self, tmp_path, monkeypatch):
        """Test error when API key not provided."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        # Remove env var
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="OpenAI API key not found"):
            PaperConfig(
                experiment_dir=exp_dir,
                output_dir=tmp_path / "output"
            )
    
    def test_invalid_sections(self, tmp_path):
        """Test error for invalid section names."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        with pytest.raises(ValueError, match="Invalid sections"):
            PaperConfig(
                experiment_dir=exp_dir,
                output_dir=tmp_path / "output",
                sections=["invalid_section"],
                openai_api_key="test-key"
            )


class TestFigure:
    """Test Figure model."""
    
    def test_valid_figure(self, tmp_path):
        """Test valid figure creation."""
        pdf_path = tmp_path / "figure.pdf"
        pdf_path.write_text("fake pdf")
        
        fig = Figure(
            name="test_figure",
            pdf_path=pdf_path,
            png_path=None,
            caption="Test figure caption"
        )
        
        assert fig.name == "test_figure"
        assert fig.pdf_path == pdf_path
        assert fig.caption == "Test figure caption"
    
    def test_missing_pdf_file(self, tmp_path):
        """Test error when PDF file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            Figure(
                name="test",
                pdf_path=tmp_path / "nonexistent.pdf",
                png_path=None,
                caption="Test"
            )
    
    def test_both_formats(self, tmp_path):
        """Test figure with both PDF and PNG."""
        pdf_path = tmp_path / "figure.pdf"
        png_path = tmp_path / "figure.png"
        pdf_path.write_text("pdf")
        png_path.write_text("png")
        
        fig = Figure(
            name="test",
            pdf_path=pdf_path,
            png_path=png_path,
            caption="Test"
        )
        
        assert fig.pdf_path.exists()
        assert fig.png_path.exists()


class TestTable:
    """Test Table model."""
    
    def test_valid_table(self):
        """Test valid table creation."""
        table = Table(
            caption="Test table",
            headers=["Col1", "Col2"],
            rows=[["A", "B"], ["C", "D"]]
        )
        
        assert table.caption == "Test table"
        assert len(table.headers) == 2
        assert len(table.rows) == 2
    
    def test_row_length_validation(self):
        """Test validation of row lengths matching headers."""
        with pytest.raises(ValueError, match="Row length mismatch"):
            Table(
                caption="Test",
                headers=["Col1", "Col2"],
                rows=[["A", "B", "C"]]  # Too many columns
            )


class TestSectionContext:
    """Test SectionContext model."""
    
    def test_basic_context(self):
        """Test basic section context creation."""
        context = SectionContext(
            section_name="introduction",
            experiment_summary="Test experiment",
            frameworks=["ChatDev", "MetaGPT"],
            metrics={}
        )
        
        assert context.section_name == "introduction"
        assert len(context.frameworks) == 2


class TestPaperStructure:
    """Test PaperStructure model."""
    
    def test_complete_structure(self):
        """Test complete paper structure."""
        structure = PaperStructure(
            title="Test Paper",
            authors=["Author One"],
            abstract="Test abstract",
            sections={
                "introduction": "Intro content",
                "methodology": "Method content"
            },
            figures=[],
            tables=[]
        )
        
        assert structure.title == "Test Paper"
        assert len(structure.sections) == 2


class TestPaperResult:
    """Test PaperResult model."""
    
    def test_successful_result(self, tmp_path):
        """Test successful paper generation result."""
        pdf_path = tmp_path / "paper.pdf"
        pdf_path.write_text("pdf")
        
        result = PaperResult(
            markdown_path=tmp_path / "paper.md",
            latex_path=tmp_path / "paper.tex",
            pdf_path=pdf_path,
            figure_paths=[],
            total_word_count=5000,
            generation_time_seconds=120.5,
            ai_tokens_used=10000
        )
        
        assert result.pdf_path == pdf_path
        assert result.total_word_count == 5000
        assert result.generation_time_seconds == 120.5
    
    def test_result_with_warnings(self, tmp_path):
        """Test result includes warnings."""
        result = PaperResult(
            markdown_path=tmp_path / "paper.md",
            latex_path=None,
            pdf_path=None,
            figure_paths=[],
            total_word_count=0,
            generation_time_seconds=0,
            ai_tokens_used=0,
            warnings=["Warning 1", "Warning 2"]
        )
        
        assert len(result.warnings) == 2
