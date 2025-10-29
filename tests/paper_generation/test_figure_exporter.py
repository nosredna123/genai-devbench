"""
Unit tests for FigureExporter.

Tests FigureExporter implementation with mocked Matplotlib.
Validates dual export, DPI settings, file size validation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from src.paper_generation.figure_exporter import FigureExporter
from src.paper_generation.models import PaperConfig, Figure
from src.paper_generation.exceptions import FigureExportError


@pytest.fixture
def paper_config(tmp_path):
    """Create PaperConfig for testing."""
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    (exp_dir / "analysis").mkdir()
    
    return PaperConfig(
        experiment_dir=exp_dir,
        output_dir=tmp_path / "output"
    )


@pytest.fixture
def metrics_data():
    """Sample metrics data for figure generation."""
    return {
        "efficiency": {
            "ChatDev": {"mean": 120.5, "std": 15.2},
            "MetaGPT": {"mean": 135.8, "std": 18.3},
            "AutoGen": {"mean": 110.2, "std": 12.7}
        },
        "cost": {
            "ChatDev": {"mean": 0.45, "std": 0.08},
            "MetaGPT": {"mean": 0.52, "std": 0.09},
            "AutoGen": {"mean": 0.38, "std": 0.06}
        },
        "quality": {
            "ChatDev": {"mean": 85.3, "std": 5.2},
            "MetaGPT": {"mean": 88.7, "std": 4.8},
            "AutoGen": {"mean": 82.1, "std": 6.3}
        }
    }


class TestFigureExporterInitialization:
    """Test FigureExporter initialization."""
    
    @patch('matplotlib.pyplot.switch_backend')
    def test_initialization_sets_headless_backend(self, mock_switch_backend, paper_config):
        """Test initialization sets Matplotlib to headless mode."""
        exporter = FigureExporter(paper_config)
        
        mock_switch_backend.assert_called_once_with('Agg')
    
    def test_initialization_stores_config(self, paper_config):
        """Test initialization stores config."""
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
            assert exporter.config == paper_config


class TestFigureExporterDualExport:
    """Test dual PDF+PNG export functionality."""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_creates_both_pdf_and_png(self, mock_close, mock_figure, mock_savefig, 
                                      paper_config, metrics_data, tmp_path):
        """Test each figure is exported as both PDF and PNG."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        # Mock figure creation
        mock_fig = Mock()
        mock_figure.return_value = mock_fig
        
        # Create dummy files to satisfy validation
        for metric in metrics_data.keys():
            (output_dir / f"{metric}_comparison.pdf").write_text("dummy")
            (output_dir / f"{metric}_comparison.png").write_text("dummy")
        
        figures = exporter.export_figures(metrics_data, output_dir)
        
        # Should have called savefig twice per figure (PDF and PNG)
        # At least 3 metrics, so at least 6 calls
        assert mock_savefig.call_count >= 6
        
        # Check that both formats were used
        call_args_list = [str(call[0][0]) for call in mock_savefig.call_args_list]
        pdf_calls = [arg for arg in call_args_list if arg.endswith('.pdf')]
        png_calls = [arg for arg in call_args_list if arg.endswith('.png')]
        
        assert len(pdf_calls) >= 3
        assert len(png_calls) >= 3
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_png_export_uses_300_dpi(self, mock_close, mock_figure, mock_savefig,
                                     paper_config, metrics_data, tmp_path):
        """Test PNG export uses 300 DPI."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        mock_fig = Mock()
        mock_figure.return_value = mock_fig
        
        # Create dummy files
        for metric in metrics_data.keys():
            (output_dir / f"{metric}_comparison.pdf").write_text("dummy")
            (output_dir / f"{metric}_comparison.png").write_text("dummy")
        
        exporter.export_figures(metrics_data, output_dir)
        
        # Check PNG calls have dpi=300
        for call_item in mock_savefig.call_args_list:
            call_path = str(call_item[0][0])
            if call_path.endswith('.png'):
                assert 'dpi' in call_item[1]
                assert call_item[1]['dpi'] == 300


class TestFigureExporterFigureTypes:
    """Test different figure types generation."""
    
    @patch('matplotlib.pyplot.bar')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_creates_comparison_charts(self, mock_close, mock_figure, mock_savefig, 
                                       mock_bar, paper_config, metrics_data, tmp_path):
        """Test creates comparison bar charts for metrics."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        mock_fig = Mock()
        mock_figure.return_value = mock_fig
        
        # Create dummy files
        for metric in metrics_data.keys():
            (output_dir / f"{metric}_comparison.pdf").write_text("dummy")
            (output_dir / f"{metric}_comparison.png").write_text("dummy")
        
        figures = exporter.export_figures(metrics_data, output_dir)
        
        # Should have created comparison charts (bar charts)
        assert mock_bar.call_count >= 3  # One per metric category
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_figure_objects_have_correct_metadata(self, mock_close, mock_figure, 
                                                   mock_savefig, paper_config, 
                                                   metrics_data, tmp_path):
        """Test returned Figure objects have correct paths and captions."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        mock_fig = Mock()
        mock_figure.return_value = mock_fig
        
        # Create dummy files
        for metric in metrics_data.keys():
            (output_dir / f"{metric}_comparison.pdf").write_text("dummy")
            (output_dir / f"{metric}_comparison.png").write_text("dummy")
        
        figures = exporter.export_figures(metrics_data, output_dir)
        
        # Check Figure objects
        assert len(figures) >= 3
        
        for figure in figures:
            assert isinstance(figure, Figure)
            # Both PDF and PNG paths should be set
            assert figure.pdf_path is not None
            assert figure.png_path is not None
            # Caption should be non-empty
            assert len(figure.caption) > 0


class TestFigureExporterFileSizeValidation:
    """Test file size validation."""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_validate_figure_checks_file_existence(self, mock_close, mock_figure, 
                                                    mock_savefig, paper_config, tmp_path):
        """Test validation checks that files exist."""
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        pdf_path = tmp_path / "test.pdf"
        png_path = tmp_path / "test.png"
        
        # Files don't exist yet
        with pytest.raises(FigureExportError, match="not found"):
            exporter._validate_figure(pdf_path, png_path)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_validate_figure_checks_pdf_size_limit(self, mock_close, mock_figure,
                                                    mock_savefig, paper_config, tmp_path):
        """Test validation fails if PDF exceeds 10MB."""
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        pdf_path = tmp_path / "huge.pdf"
        png_path = tmp_path / "huge.png"
        
        # Create files
        png_path.write_bytes(b'x' * 1000)  # 1KB PNG (fine)
        pdf_path.write_bytes(b'x' * 11_000_000)  # 11MB PDF (too large)
        
        with pytest.raises(FigureExportError, match="exceeds 10MB"):
            exporter._validate_figure(pdf_path, png_path)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_validate_figure_passes_for_valid_files(self, mock_close, mock_figure,
                                                     mock_savefig, paper_config, tmp_path):
        """Test validation passes for valid files."""
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        pdf_path = tmp_path / "valid.pdf"
        png_path = tmp_path / "valid.png"
        
        # Create valid files
        pdf_path.write_bytes(b'x' * 1000)  # 1KB
        png_path.write_bytes(b'x' * 1000)  # 1KB
        
        # Should not raise
        exporter._validate_figure(pdf_path, png_path)


class TestFigureExporterErrorHandling:
    """Test error handling."""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_handles_matplotlib_errors(self, mock_figure, mock_savefig, 
                                       paper_config, metrics_data, tmp_path):
        """Test handles Matplotlib errors gracefully."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        # Make savefig raise an error
        mock_savefig.side_effect = Exception("Matplotlib error")
        
        with pytest.raises(FigureExportError):
            exporter.export_figures(metrics_data, output_dir)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_handles_invalid_metrics_data(self, mock_close, mock_figure, mock_savefig,
                                          paper_config, tmp_path):
        """Test handles invalid metrics data structure."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        # Invalid metrics structure
        invalid_metrics = {"bad": "data"}
        
        with pytest.raises(FigureExportError):
            exporter.export_figures(invalid_metrics, output_dir)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_validates_output_directory(self, mock_close, mock_figure, mock_savefig,
                                        paper_config, metrics_data, tmp_path):
        """Test validates output directory exists."""
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        nonexistent_dir = tmp_path / "nonexistent"
        
        with pytest.raises(FigureExportError, match="Output directory"):
            exporter.export_figures(metrics_data, nonexistent_dir)


class TestFigureExporterHeadlessMode:
    """Test headless operation (no display)."""
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.close')
    def test_does_not_call_show(self, mock_close, mock_figure, mock_savefig, 
                                mock_show, paper_config, metrics_data, tmp_path):
        """Test does not call plt.show() in headless mode."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        mock_fig = Mock()
        mock_figure.return_value = mock_fig
        
        # Create dummy files
        for metric in metrics_data.keys():
            (output_dir / f"{metric}_comparison.pdf").write_text("dummy")
            (output_dir / f"{metric}_comparison.png").write_text("dummy")
        
        exporter.export_figures(metrics_data, output_dir)
        
        # Should NOT have called show()
        mock_show.assert_not_called()
    
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_closes_figures_after_export(self, mock_figure, mock_savefig, 
                                        mock_close, paper_config, metrics_data, tmp_path):
        """Test closes figures after export to free memory."""
        output_dir = tmp_path / "figures"
        output_dir.mkdir()
        
        with patch('matplotlib.pyplot.switch_backend'):
            exporter = FigureExporter(paper_config)
        
        mock_fig = Mock()
        mock_figure.return_value = mock_fig
        
        # Create dummy files
        for metric in metrics_data.keys():
            (output_dir / f"{metric}_comparison.pdf").write_text("dummy")
            (output_dir / f"{metric}_comparison.png").write_text("dummy")
        
        exporter.export_figures(metrics_data, output_dir)
        
        # Should have closed figures
        assert mock_close.call_count >= 3
