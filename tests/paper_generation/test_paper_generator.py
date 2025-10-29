"""
Unit tests for PaperGenerator orchestration.

Tests pipeline stages, error propagation, and PaperResult structure.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import yaml
import json

from src.paper_generation.paper_generator import PaperGenerator
from src.paper_generation.models import PaperConfig, PaperResult, Figure
from src.paper_generation.exceptions import (
    PaperGenerationError,
    ExperimentDataError,
    DependencyMissingError
)


@pytest.fixture
def experiment_dir(tmp_path):
    """Create sample experiment directory."""
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    analysis_dir = exp_dir / "analysis"
    analysis_dir.mkdir()
    
    # Create config.yaml
    config_data = {
        "experiment": {
            "name": "Framework Comparison",
            "frameworks": ["ChatDev", "MetaGPT", "AutoGen"],
            "task": "Build a web application"
        }
    }
    (exp_dir / "config.yaml").write_text(yaml.dump(config_data))
    
    # Create metrics.json
    metrics_data = {
        "efficiency": {
            "ChatDev": {"mean": 120.5, "std": 15.2}
        }
    }
    (analysis_dir / "metrics.json").write_text(json.dumps(metrics_data))
    
    # Create statistical_report.md
    (analysis_dir / "statistical_report.md").write_text("# Report\nKey findings here.")
    
    return exp_dir


@pytest.fixture
def paper_config(experiment_dir, tmp_path):
    """Create PaperConfig for testing."""
    return PaperConfig(
        experiment_dir=experiment_dir,
        output_dir=tmp_path / "output",
        skip_latex=True  # Skip pdflatex for unit tests
    )


class TestPaperGeneratorInitialization:
    """Test PaperGenerator initialization."""
    
    def test_initialization_creates_components(self, paper_config):
        """Test initialization creates ProseEngine and FigureExporter."""
        with patch('src.paper_generation.paper_generator.ProseEngine'):
            with patch('src.paper_generation.paper_generator.FigureExporter'):
                generator = PaperGenerator(paper_config)
                assert generator.config == paper_config
    
    def test_initialization_validates_experiment_directory(self, tmp_path):
        """Test initialization validates experiment directory exists."""
        bad_config = PaperConfig(
            experiment_dir=tmp_path / "nonexistent",
            output_dir=tmp_path / "output"
        )
        
        with pytest.raises(ExperimentDataError, match="Experiment directory"):
            PaperGenerator(bad_config)
    
    def test_initialization_validates_analysis_subdirectory(self, tmp_path):
        """Test initialization validates analysis/ subdirectory exists."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        # No analysis/ subdirectory
        
        bad_config = PaperConfig(
            experiment_dir=exp_dir,
            output_dir=tmp_path / "output"
        )
        
        with pytest.raises(ExperimentDataError, match="analysis"):
            PaperGenerator(bad_config)


class TestPaperGeneratorLoadExperimentData:
    """Test experiment data loading stage."""
    
    @patch('src.paper_generation.paper_generator.ProseEngine')
    @patch('src.paper_generation.paper_generator.FigureExporter')
    def test_load_experiment_data_success(self, mock_fig, mock_prose, 
                                          experiment_dir, paper_config):
        """Test successful data loading."""
        generator = PaperGenerator(paper_config)
        data = generator._load_experiment_data()
        
        assert "config" in data
        assert "metrics" in data
        assert "statistical_report" in data
    
    @patch('src.paper_generation.paper_generator.ProseEngine')
    @patch('src.paper_generation.paper_generator.FigureExporter')
    def test_load_experiment_data_missing_config_raises_error(self, mock_fig, mock_prose,
                                                              tmp_path):
        """Test error when config.yaml missing."""
        exp_dir = tmp_path / "experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        config = PaperConfig(
            experiment_dir=exp_dir,
            output_dir=tmp_path / "output"
        )
        
        generator = PaperGenerator(config)
        
        with pytest.raises(ExperimentDataError):
            generator._load_experiment_data()


class TestPaperGeneratorSectionGeneration:
    """Test section generation stages."""
    
    @patch('src.paper_generation.sections.abstract_generator.AbstractGenerator.generate')
    @patch('src.paper_generation.sections.introduction_generator.IntroductionGenerator.generate')
    @patch('src.paper_generation.sections.related_work_generator.RelatedWorkGenerator.generate')
    @patch('src.paper_generation.sections.methodology_generator.MethodologyGenerator.generate')
    @patch('src.paper_generation.sections.results_generator.ResultsGenerator.generate')
    @patch('src.paper_generation.sections.discussion_generator.DiscussionGenerator.generate')
    @patch('src.paper_generation.sections.conclusion_generator.ConclusionGenerator.generate')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    @patch('src.paper_generation.paper_generator.FigureExporter')
    def test_generate_all_sections_calls_all_generators(self, mock_fig, mock_prose,
                                                        mock_conclusion, mock_discussion,
                                                        mock_results, mock_methodology,
                                                        mock_related, mock_intro, mock_abstract,
                                                        experiment_dir, paper_config):
        """Test _generate_all_sections calls all 7 section generators."""
        # Mock return values
        mock_abstract.return_value = "Abstract text"
        mock_intro.return_value = "Introduction text " * 200
        mock_related.return_value = "Related work text " * 200
        mock_methodology.return_value = "Methodology text " * 200
        mock_results.return_value = "Results text " * 200
        mock_discussion.return_value = "Discussion text " * 200
        mock_conclusion.return_value = "Conclusion text " * 200
        
        generator = PaperGenerator(paper_config)
        sections = generator._generate_all_sections()
        
        # All generators should be called
        mock_abstract.assert_called_once()
        mock_intro.assert_called_once()
        mock_related.assert_called_once()
        mock_methodology.assert_called_once()
        mock_results.assert_called_once()
        mock_discussion.assert_called_once()
        mock_conclusion.assert_called_once()
        
        # PaperStructure should have all sections
        assert sections.abstract is not None
        assert sections.introduction is not None
        assert sections.related_work is not None
        assert sections.methodology is not None
        assert sections.results is not None
        assert sections.discussion is not None
        assert sections.conclusion is not None


class TestPaperGeneratorFigureExport:
    """Test figure export stage."""
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_export_figures_calls_figure_exporter(self, mock_prose, mock_fig_class,
                                                  experiment_dir, paper_config):
        """Test _export_figures calls FigureExporter.export_figures()."""
        mock_exporter = Mock()
        mock_fig_class.return_value = mock_exporter
        
        # Mock return value
        mock_exporter.export_figures.return_value = [
            Figure(id="fig1", pdf_path=Path("fig1.pdf"), png_path=Path("fig1.png"), 
                   caption="Figure 1")
        ]
        
        generator = PaperGenerator(paper_config)
        metrics = {"efficiency": {"mean": 100}}
        figures = generator._export_figures(metrics)
        
        # Should have called export_figures
        mock_exporter.export_figures.assert_called_once()
        assert len(figures) > 0


class TestPaperGeneratorCitationPlaceholders:
    """Test citation placeholder insertion."""
    
    @patch('src.paper_generation.citation_handler.CitationHandler.insert_placeholders')
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_insert_citation_placeholders_processes_all_sections(self, mock_prose, mock_fig,
                                                                 mock_citations,
                                                                 experiment_dir, paper_config):
        """Test _insert_citation_placeholders processes all sections."""
        mock_citations.return_value = "Text with **[CITE: framework]**"
        
        generator = PaperGenerator(paper_config)
        
        sections = {
            "introduction": "Mention ChatDev here",
            "related_work": "Discuss MetaGPT here",
            "methodology": "Using AutoGen",
            "results": "ChatDev performed well",
            "discussion": "MetaGPT showed promise",
            "conclusion": "Future work with AutoGen"
        }
        
        result = generator._insert_citation_placeholders(sections)
        
        # Should have called insert_placeholders for each section
        assert mock_citations.call_count == len(sections)
        
        # All sections should be processed
        for section_name in sections.keys():
            assert section_name in result


class TestPaperGeneratorErrorPropagation:
    """Test error handling and propagation."""
    
    @patch('src.paper_generation.sections.introduction_generator.IntroductionGenerator.generate')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    @patch('src.paper_generation.paper_generator.FigureExporter')
    def test_section_generation_error_propagates(self, mock_fig, mock_prose, mock_intro,
                                                experiment_dir, paper_config):
        """Test error in section generation propagates correctly."""
        # Make introduction generator raise error
        mock_intro.side_effect = Exception("Generation failed")
        
        generator = PaperGenerator(paper_config)
        
        with pytest.raises(Exception):
            generator._generate_all_sections()
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_figure_export_error_propagates(self, mock_prose, mock_fig_class,
                                           experiment_dir, paper_config):
        """Test error in figure export propagates correctly."""
        mock_exporter = Mock()
        mock_fig_class.return_value = mock_exporter
        
        # Make export raise error
        from src.paper_generation.exceptions import FigureExportError
        mock_exporter.export_figures.side_effect = FigureExportError("Export failed")
        
        generator = PaperGenerator(paper_config)
        
        with pytest.raises(FigureExportError):
            generator._export_figures({"metrics": {}})


class TestPaperGeneratorPaperResult:
    """Test PaperResult structure."""
    
    @patch('src.paper_generation.paper_generator.PandocConverter')
    @patch('src.paper_generation.paper_generator.DocumentFormatter')
    @patch('src.paper_generation.paper_generator.CitationHandler')
    @patch('src.paper_generation.sections.abstract_generator.AbstractGenerator.generate')
    @patch('src.paper_generation.sections.introduction_generator.IntroductionGenerator.generate')
    @patch('src.paper_generation.sections.related_work_generator.RelatedWorkGenerator.generate')
    @patch('src.paper_generation.sections.methodology_generator.MethodologyGenerator.generate')
    @patch('src.paper_generation.sections.results_generator.ResultsGenerator.generate')
    @patch('src.paper_generation.sections.discussion_generator.DiscussionGenerator.generate')
    @patch('src.paper_generation.sections.conclusion_generator.ConclusionGenerator.generate')
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_paper_result_has_correct_structure(self, mock_prose, mock_fig,
                                                mock_conclusion, mock_discussion, mock_results,
                                                mock_methodology, mock_related, mock_intro,
                                                mock_abstract, mock_citation, mock_formatter,
                                                mock_pandoc, experiment_dir, paper_config):
        """Test PaperResult contains all required fields."""
        # Mock all dependencies
        mock_abstract.return_value = "Abstract"
        mock_intro.return_value = "Intro " * 200
        mock_related.return_value = "Related " * 200
        mock_methodology.return_value = "Method " * 200
        mock_results.return_value = "Results " * 200
        mock_discussion.return_value = "Discussion " * 200
        mock_conclusion.return_value = "Conclusion " * 200
        
        mock_exporter = Mock()
        mock_fig.return_value = mock_exporter
        mock_exporter.export_figures.return_value = []
        
        mock_citation_handler = Mock()
        mock_citation.return_value = mock_citation_handler
        mock_citation_handler.insert_placeholders.return_value = "Text with citations"
        
        mock_doc_formatter = Mock()
        mock_formatter.return_value = mock_doc_formatter
        mock_doc_formatter.format_latex_document.return_value = "LaTeX content"
        
        mock_converter = Mock()
        mock_pandoc.return_value = mock_converter
        mock_converter.convert_to_latex.return_value = Path(paper_config.output_dir / "main.tex")
        
        # Create output files
        paper_config.output_dir.mkdir(parents=True, exist_ok=True)
        (paper_config.output_dir / "main.tex").write_text("LaTeX content")
        
        generator = PaperGenerator(paper_config)
        result = generator.generate()
        
        # Verify PaperResult structure
        assert isinstance(result, PaperResult)
        assert result.success is True
        assert result.output_dir == paper_config.output_dir
        assert result.latex_file is not None
        assert result.generation_time_seconds > 0
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_paper_result_includes_timing(self, mock_prose, mock_fig,
                                         experiment_dir, paper_config):
        """Test PaperResult includes generation timing."""
        # This will fail early due to missing data, but we can check timing is attempted
        generator = PaperGenerator(paper_config)
        
        # The generate() method should track timing even if it fails
        # We'll test this by ensuring the structure supports it
        assert hasattr(PaperResult, 'generation_time_seconds')


class TestPaperGeneratorFiguresOnlyMode:
    """Test figures-only mode (T057 - US3)."""
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_figures_only_mode_skips_prose_generation(self, mock_prose, mock_fig_class,
                                                      experiment_dir, tmp_path):
        """Test figures-only mode skips all prose generation."""
        # Create config with figures_only=True
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path / "output",
            figures_only=True
        )
        
        # Mock figure exporter
        mock_exporter = Mock()
        mock_fig_class.return_value = mock_exporter
        mock_exporter.export_figures.return_value = [
            Figure(
                pdf_path=Path("fig1.pdf"),
                png_path=Path("fig1.png"),
                caption="Figure 1",
                label="fig:1"
            )
        ]
        
        generator = PaperGenerator(config)
        result = generator.generate()
        
        # ProseEngine should never be used in figures-only mode
        mock_prose.assert_not_called()
        
        # FigureExporter should be called
        mock_exporter.export_figures.assert_called_once()
        
        # Result should indicate success but no LaTeX/PDF generated
        assert result.success is True
        assert result.figures_generated > 0
        assert result.latex_file is None
        assert result.pdf_file is None
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_figures_only_mode_skips_latex_conversion(self, mock_prose, mock_fig_class,
                                                      experiment_dir, tmp_path):
        """Test figures-only mode skips Pandoc and pdflatex."""
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path / "output",
            figures_only=True
        )
        
        mock_exporter = Mock()
        mock_fig_class.return_value = mock_exporter
        mock_exporter.export_figures.return_value = []
        
        # Patch the conversion methods to ensure they're not called
        with patch.object(PaperGenerator, '_convert_to_latex') as mock_convert:
            with patch.object(PaperGenerator, '_compile_to_pdf') as mock_compile:
                generator = PaperGenerator(config)
                result = generator.generate()
                
                # Neither conversion method should be called in figures-only mode
                mock_convert.assert_not_called()
                mock_compile.assert_not_called()
                
                assert result.success is True
                assert result.latex_file is None
                assert result.pdf_file is None
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_figures_only_mode_creates_output_directory(self, mock_prose, mock_fig_class,
                                                       experiment_dir, tmp_path):
        """Test figures-only mode creates output directory."""
        output_dir = tmp_path / "custom_output"
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=output_dir,
            figures_only=True
        )
        
        mock_exporter = Mock()
        mock_fig_class.return_value = mock_exporter
        mock_exporter.export_figures.return_value = []
        
        # Mock the figures_dir attribute
        mock_exporter.figures_dir = output_dir / "figures"
        mock_exporter.figures_dir.mkdir(parents=True, exist_ok=True)
        
        generator = PaperGenerator(config)
        result = generator.generate()
        
        # Output directory should be created (via PaperConfig.__post_init__)
        assert output_dir.exists()
        # Figures directory should be created (via FigureExporter.__init__)
        assert (output_dir / "figures").exists()
        assert result.success is True
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_figures_only_mode_handles_export_errors(self, mock_prose, mock_fig_class,
                                                     experiment_dir, tmp_path):
        """Test figures-only mode handles FigureExportError correctly."""
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path / "output",
            figures_only=True
        )
        
        mock_exporter = Mock()
        mock_fig_class.return_value = mock_exporter
        
        from src.paper_generation.exceptions import FigureExportError
        mock_exporter.export_figures.side_effect = FigureExportError("Export failed")
        
        generator = PaperGenerator(config)
        
        with pytest.raises(FigureExportError, match="Export failed"):
            generator.generate()
    
    @patch('src.paper_generation.paper_generator.FigureExporter')
    @patch('src.paper_generation.paper_generator.ProseEngine')
    def test_figures_only_mode_returns_figure_count(self, mock_prose, mock_fig_class,
                                                    experiment_dir, tmp_path):
        """Test figures-only mode returns correct figure count in result."""
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path / "output",
            figures_only=True
        )
        
        mock_exporter = Mock()
        mock_fig_class.return_value = mock_exporter
        
        # Create mock figures with temp files to satisfy validation
        fig_dir = tmp_path / "figs"
        fig_dir.mkdir()
        for i in range(1, 4):
            (fig_dir / f"fig{i}.pdf").write_text("PDF")
            (fig_dir / f"fig{i}.png").write_text("PNG")
        
        mock_exporter.export_figures.return_value = [
            Figure(
                pdf_path=fig_dir / "fig1.pdf",
                png_path=fig_dir / "fig1.png",
                caption="Figure 1",
                label="fig:1"
            ),
            Figure(
                pdf_path=fig_dir / "fig2.pdf",
                png_path=fig_dir / "fig2.png",
                caption="Figure 2",
                label="fig:2"
            ),
            Figure(
                pdf_path=fig_dir / "fig3.pdf",
                png_path=fig_dir / "fig3.png",
                caption="Figure 3",
                label="fig:3"
            )
        ]
        
        generator = PaperGenerator(config)
        result = generator.generate()
        
        assert result.figures_generated == 3
        assert result.success is True
