"""
Contract tests for FigureExporter standalone usage.

Tests calling export_figures() directly without PaperGenerator,
verifying independent operation.
"""

import pytest
from pathlib import Path

from src.paper_generation.figure_exporter import FigureExporter
from src.paper_generation.models import PaperConfig


class TestFigureExporterStandalone:
    """Test FigureExporter can operate independently."""
    
    def test_load_experiment_data_independently(self, tmp_path):
        """Test FigureExporter can load experiment data without PaperGenerator."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path,
            skip_latex=True,
            figures_only=True
        )
        exporter = FigureExporter(config)
        
        # Act
        context = exporter.load_experiment_data()
        
        # Assert
        assert context is not None
        assert len(context.frameworks) > 0, "Should load frameworks"
        assert context.metrics is not None, "Should load metrics"
        assert isinstance(context.frameworks, list)
    
    def test_export_figures_without_paper_generator(self, tmp_path):
        """Test FigureExporter.export_figures() works independently."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path,
            skip_latex=True,
            figures_only=True
        )
        exporter = FigureExporter(config)
        
        # Act
        context = exporter.load_experiment_data()
        figures = exporter.export_figures(context)
        
        # Assert
        assert len(figures) > 0, "Should export at least one figure"
        
        # Verify all figures have both PDF and PNG
        for fig in figures:
            assert fig.pdf_path.exists(), f"PDF missing: {fig.pdf_path}"
            assert fig.png_path.exists(), f"PNG missing: {fig.png_path}"
            assert fig.caption, "Figure should have caption"
    
    def test_standalone_export_creates_figures_directory(self, tmp_path):
        """Test standalone export creates figures subdirectory."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path,
            skip_latex=True,
            figures_only=True
        )
        
        # Act
        exporter = FigureExporter(config)
        
        # Assert
        assert (tmp_path / "figures").exists(), "Should create figures subdirectory"
    
    def test_standalone_export_all_metrics(self, tmp_path):
        """Test standalone export generates figure for each metric."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=tmp_path,
            skip_latex=True,
            figures_only=True
        )
        exporter = FigureExporter(config)
        
        # Act
        context = exporter.load_experiment_data()
        figures = exporter.export_figures(context)
        
        # Assert - should have one figure per metric
        if context.frameworks and context.metrics:
            first_framework = context.frameworks[0]
            num_metrics = len(context.metrics[first_framework])
            
            # At least one figure per metric (may have additional statistical plots)
            assert len(figures) >= num_metrics, \
                f"Should have at least {num_metrics} figures for {num_metrics} metrics"
    
    def test_load_experiment_data_handles_missing_metrics_file(self, tmp_path):
        """Test load_experiment_data raises error if metrics file missing."""
        # Arrange
        experiment_dir = tmp_path / "empty_experiment"
        experiment_dir.mkdir()
        (experiment_dir / "analysis").mkdir()  # Create analysis dir but no metrics.json
        
        output_dir = tmp_path / "output"
        config = PaperConfig(
            experiment_dir=experiment_dir,
            output_dir=output_dir,
            skip_latex=True,
            figures_only=True
        )
        output_dir.mkdir(exist_ok=True)
        
        exporter = FigureExporter(config)
        
        # Act & Assert
        from src.paper_generation.exceptions import FigureExportError
        with pytest.raises(FigureExportError) as exc_info:
            exporter.load_experiment_data()
        
        assert "not found" in str(exc_info.value).lower()
