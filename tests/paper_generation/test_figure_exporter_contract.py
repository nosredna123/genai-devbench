"""
Contract tests for FigureExporter API.

Tests the FigureExporter interface contract: export_figures() method should
accept experiment data, return Figure objects with valid PDF+PNG paths, 
verify ≥300 DPI quality.

Following TDD: These tests should FAIL initially since FigureExporter doesn't exist yet.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json

from src.paper_generation.models import Figure, PaperConfig, SectionContext
from src.paper_generation.exceptions import FigureExportError


@pytest.fixture
def metrics_data():
    """Create sample metrics data for figure generation."""
    return {
        "frameworks": {
            "ChatDev": {
                "execution_time": {"mean": 245.3, "std": 32.1, "min": 180.2, "max": 310.5},
                "total_cost_usd": {"mean": 0.42, "std": 0.08, "min": 0.25, "max": 0.58},
                "test_pass_rate": {"mean": 0.87, "std": 0.12, "min": 0.60, "max": 1.0},
                "code_quality_score": {"mean": 7.2, "std": 1.3, "min": 4.5, "max": 9.0}
            },
            "MetaGPT": {
                "execution_time": {"mean": 312.7, "std": 45.2, "min": 220.1, "max": 405.8},
                "total_cost_usd": {"mean": 0.53, "std": 0.11, "min": 0.30, "max": 0.75},
                "test_pass_rate": {"mean": 0.92, "std": 0.09, "min": 0.70, "max": 1.0},
                "code_quality_score": {"mean": 8.1, "std": 1.1, "min": 5.8, "max": 9.5}
            },
            "AutoGen": {
                "execution_time": {"mean": 198.4, "std": 28.5, "min": 140.3, "max": 260.7},
                "total_cost_usd": {"mean": 0.35, "std": 0.06, "min": 0.22, "max": 0.48},
                "test_pass_rate": {"mean": 0.83, "std": 0.14, "min": 0.55, "max": 1.0},
                "code_quality_score": {"mean": 6.9, "std": 1.5, "min": 4.0, "max": 8.8}
            }
        },
        "statistical_tests": {
            "kruskal_wallis": {
                "execution_time": {"p_value": 0.0001, "statistic": 42.3},
                "total_cost_usd": {"p_value": 0.0003, "statistic": 38.1}
            }
        }
    }


@pytest.fixture
def paper_config(tmp_path, monkeypatch):
    """Create a minimal PaperConfig for testing."""
    # Mock API key to avoid validation error
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
    
    # Create directories to pass validation
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    (exp_dir / "analysis").mkdir()  # Create analysis subdirectory
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    return PaperConfig(
        experiment_dir=exp_dir,
        output_dir=output_dir,
        model="gpt-3.5-turbo",
        temperature=0.7,
        prose_level="standard"
    )


@pytest.fixture
def section_context(metrics_data):
    """Create a SectionContext with metrics data."""
    return SectionContext(
        section_name="results",
        experiment_summary="Comparison of 3 agent frameworks",
        frameworks=["ChatDev", "MetaGPT", "AutoGen"],
        num_runs=50,
        metrics=metrics_data["frameworks"],
        statistical_results=metrics_data["statistical_tests"],
        key_findings=["AutoGen fastest", "MetaGPT highest quality"]
    )


class TestFigureExporterContract:
    """Contract tests for FigureExporter API - defines expected behavior."""
    
    def test_figure_exporter_exists(self):
        """Test that FigureExporter class can be imported.
        
        ✅ NOW PASSES - FigureExporter implemented!
        """
        from src.paper_generation.figure_exporter import FigureExporter
        assert FigureExporter is not None
    
    def test_figure_exporter_has_export_figures_method(self, paper_config):
        """Test that FigureExporter has export_figures() method.
        
        ✅ NOW PASSES - FigureExporter has export_figures() method!
        """
        from src.paper_generation.figure_exporter import FigureExporter
        
        exporter = FigureExporter(paper_config)
        assert hasattr(exporter, 'export_figures')
        assert callable(exporter.export_figures)
    
    @patch('matplotlib.pyplot.savefig')
    def test_export_figures_returns_list_of_figures(self, mock_savefig, section_context, paper_config):
        """Test that export_figures() returns list of Figure objects.
        
        Expected to FAIL until FigureExporter is implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # figures = exporter.export_figures(section_context)
        # 
        # assert isinstance(figures, list)
        # assert len(figures) > 0
        # assert all(isinstance(fig, Figure) for fig in figures)
    
    @patch('matplotlib.pyplot.savefig')
    def test_export_figures_creates_pdf_and_png(self, mock_savefig, section_context, paper_config):
        """Test that export_figures() creates both PDF and PNG files.
        
        This validates functional requirement FR-015 (dual format export).
        Expected to FAIL until dual export is implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # figures = exporter.export_figures(section_context)
        # 
        # for figure in figures:
        #     assert figure.pdf_path.exists(), f"PDF missing: {figure.pdf_path}"
        #     assert figure.png_path.exists(), f"PNG missing: {figure.png_path}"
        #     assert figure.pdf_path.suffix == '.pdf'
        #     assert figure.png_path.suffix == '.png'
    
    @patch('matplotlib.pyplot.savefig')
    def test_export_figures_minimum_dpi(self, mock_savefig, section_context, paper_config):
        """Test that exported figures meet ≥300 DPI requirement.
        
        This validates functional requirement FR-017 and Success Criterion SC-005.
        Expected to FAIL until DPI settings are implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # exporter.export_figures(section_context)
        # 
        # # Check that savefig was called with dpi >= 300
        # for call in mock_savefig.call_args_list:
        #     kwargs = call[1]
        #     if 'dpi' in kwargs:
        #         assert kwargs['dpi'] >= 300, f"DPI {kwargs['dpi']} < 300"
    
    @patch('matplotlib.pyplot.savefig')
    def test_export_figures_file_sizes_reasonable(self, mock_savefig, section_context, paper_config):
        """Test that exported figures have reasonable file sizes (<10MB).
        
        Expected to FAIL until file size validation is implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented (with real file creation, not mocked):
        # exporter = FigureExporter(paper_config)
        # figures = exporter.export_figures(section_context)
        # 
        # max_size_mb = 10
        # for figure in figures:
        #     pdf_size_mb = figure.pdf_path.stat().st_size / (1024 * 1024)
        #     png_size_mb = figure.png_path.stat().st_size / (1024 * 1024)
        #     
        #     assert pdf_size_mb <= max_size_mb, f"PDF too large: {pdf_size_mb:.1f}MB"
        #     assert png_size_mb <= max_size_mb, f"PNG too large: {png_size_mb:.1f}MB"
    
    @patch('matplotlib.pyplot.savefig')
    def test_export_figures_includes_captions(self, mock_savefig, section_context, paper_config):
        """Test that Figure objects include descriptive captions.
        
        Expected to FAIL until caption generation is implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # figures = exporter.export_figures(section_context)
        # 
        # for figure in figures:
        #     assert figure.caption is not None
        #     assert len(figure.caption) > 0
        #     # Caption should describe what the figure shows
        #     assert len(figure.caption.split()) >= 5


class TestFigureExporterHeadlessMode:
    """Test headless backend configuration for server environments."""
    
    @patch('matplotlib.use')
    def test_configures_headless_backend(self, mock_use, paper_config):
        """Test that FigureExporter configures Matplotlib for headless operation.
        
        This validates functional requirement FR-016 (headless backend).
        Expected to FAIL until backend configuration is implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # 
        # # Should have called matplotlib.use('Agg') before any plotting
        # mock_use.assert_called_with('Agg')
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    def test_does_not_display_figures(self, mock_savefig, mock_show, section_context, paper_config):
        """Test that FigureExporter never calls plt.show() (headless mode).
        
        Expected to FAIL until headless operation is confirmed.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # exporter.export_figures(section_context)
        # 
        # # Should never call show() in headless mode
        # mock_show.assert_not_called()


class TestFigureExporterFigureTypes:
    """Test that appropriate figure types are generated."""
    
    @patch('matplotlib.pyplot.savefig')
    def test_generates_comparison_bar_charts(self, mock_savefig, section_context, paper_config):
        """Test that exporter generates comparison charts for metrics across frameworks.
        
        Expected to FAIL until chart generation logic is implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # figures = exporter.export_figures(section_context)
        # 
        # # Should include comparison charts
        # figure_names = [fig.pdf_path.stem for fig in figures]
        # 
        # # Expected figures: execution_time_comparison, cost_comparison, quality_comparison
        # assert any('time' in name.lower() or 'execution' in name.lower() for name in figure_names)
        # assert any('cost' in name.lower() for name in figure_names)
        # assert any('quality' in name.lower() or 'test' in name.lower() for name in figure_names)
    
    @patch('matplotlib.pyplot.savefig')
    def test_generates_statistical_significance_plots(self, mock_savefig, section_context, paper_config):
        """Test that exporter includes statistical test visualizations.
        
        Expected to FAIL until statistical plotting is implemented.
        """
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # figures = exporter.export_figures(section_context)
        # 
        # # Should include at least 1 figure showing statistical significance
        # # (e.g., box plots, violin plots with significance markers)
        # assert len(figures) >= 1


class TestFigureExporterErrorHandling:
    """Test error handling in FigureExporter."""
    
    def test_export_figures_handles_invalid_metrics(self, paper_config):
        """Test that FigureExporter handles missing/invalid metrics gracefully.
        
        Expected to FAIL until error handling is implemented.
        """
        # Create context with empty metrics
        invalid_context = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["ChatDev"],
            num_runs=10,
            metrics={},  # Empty metrics
            statistical_results={},
            key_findings=[]
        )
        
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # 
        # with pytest.raises(FigureExportError, match="metrics data"):
        #     exporter.export_figures(invalid_context)
    
    @patch('matplotlib.pyplot.savefig')
    def test_export_figures_handles_matplotlib_errors(self, mock_savefig, section_context, paper_config):
        """Test that FigureExporter handles Matplotlib errors gracefully.
        
        Expected to FAIL until error handling is implemented.
        """
        # Simulate Matplotlib error
        mock_savefig.side_effect = Exception("Failed to save figure")
        
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # 
        # with pytest.raises(FigureExportError, match="export failed"):
        #     exporter.export_figures(section_context)
    
    def test_export_figures_validates_output_directory(self, section_context, paper_config):
        """Test that FigureExporter validates output directory exists.
        
        Expected to FAIL until directory validation is implemented.
        """
        # Point to non-existent output directory
        paper_config.output_dir = Path("/nonexistent/path")
        
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # 
        # with pytest.raises(FigureExportError, match="output directory"):
        #     exporter.export_figures(section_context)


class TestFigureExporterStandaloneUsage:
    """Test that FigureExporter can operate independently of PaperGenerator."""
    
    @patch('matplotlib.pyplot.savefig')
    def test_can_export_figures_without_paper_generator(self, mock_savefig, metrics_data, paper_config, tmp_path):
        """Test that FigureExporter can load experiment data and export independently.
        
        This validates User Story 3 requirement for standalone operation.
        Expected to FAIL until standalone data loading is implemented.
        """
        # Create experiment directory with metrics.json
        exp_dir = tmp_path / "standalone_experiment"
        exp_dir.mkdir()
        analysis_dir = exp_dir / "analysis"
        analysis_dir.mkdir()
        (analysis_dir / "metrics.json").write_text(json.dumps(metrics_data))
        
        paper_config.experiment_dir = exp_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.figure_exporter import FigureExporter
        
        # TODO: Once implemented:
        # exporter = FigureExporter(paper_config)
        # 
        # # Should be able to load data and export without PaperGenerator
        # context = exporter.load_experiment_data()
        # figures = exporter.export_figures(context)
        # 
        # assert len(figures) > 0
        # assert all(fig.pdf_path.exists() for fig in figures)
