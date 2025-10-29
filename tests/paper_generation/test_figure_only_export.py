"""
Integration tests for figure-only export functionality.

Tests the export_figures.py CLI and verifies output directory structure,
PDF+PNG pairs, and metadata.
"""

import pytest
import subprocess
import json
from pathlib import Path


class TestFigureOnlyExport:
    """Integration tests for standalone figure export."""
    
    def test_export_figures_cli_creates_output_directory(self, tmp_path):
        """Test that export_figures.py creates output directory structure."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "figures_output"
        project_root = Path(__file__).parent.parent.parent
        
        # Act
        result = subprocess.run(
            [
                str(project_root / ".venv" / "bin" / "python"),
                "scripts/export_figures.py",
                str(experiment_dir),
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Assert
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_dir.exists(), "Output directory should be created"
        assert (output_dir / "figures").exists(), "Figures subdirectory should be created"
    
    def test_export_figures_creates_pdf_png_pairs(self, tmp_path):
        """Test that each figure is exported in both PDF and PNG formats."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "figures_output"
        project_root = Path(__file__).parent.parent.parent
        
        # Act
        result = subprocess.run(
            [
                str(project_root / ".venv" / "bin" / "python"),
                "scripts/export_figures.py",
                str(experiment_dir),
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Assert
        assert result.returncode == 0
        
        figures_dir = output_dir / "figures"
        pdf_files = list(figures_dir.glob("*.pdf"))
        png_files = list(figures_dir.glob("*.png"))
        
        assert len(pdf_files) > 0, "Should generate at least one PDF figure"
        assert len(pdf_files) == len(png_files), "Each PDF should have corresponding PNG"
        
        # Check each PDF has matching PNG
        for pdf_file in pdf_files:
            png_file = pdf_file.with_suffix('.png')
            assert png_file.exists(), f"Missing PNG for {pdf_file.name}"
    
    def test_export_figures_respects_output_dir_flag(self, tmp_path):
        """Test that --output-dir flag is respected."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        custom_output = tmp_path / "custom_output_location"
        project_root = Path(__file__).parent.parent.parent
        
        # Act
        result = subprocess.run(
            [
                str(project_root / ".venv" / "bin" / "python"),
                "scripts/export_figures.py",
                str(experiment_dir),
                "--output-dir", str(custom_output)
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Assert
        assert result.returncode == 0
        assert custom_output.exists()
        assert (custom_output / "figures").exists()
    
    def test_export_figures_lists_exported_files(self, tmp_path):
        """Test that CLI displays list of exported files."""
        # Arrange
        experiment_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "figures_output"
        project_root = Path(__file__).parent.parent.parent
        
        # Act
        result = subprocess.run(
            [
                str(project_root / ".venv" / "bin" / "python"),
                "scripts/export_figures.py",
                str(experiment_dir),
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Assert
        assert result.returncode == 0
        # Check that output mentions exported files
        assert "exported" in result.stdout.lower() or "figure" in result.stdout.lower()
        assert ".pdf" in result.stdout or ".png" in result.stdout
    
    def test_export_figures_handles_missing_experiment_dir(self, tmp_path):
        """Test that CLI handles missing experiment directory gracefully."""
        # Arrange
        nonexistent_dir = tmp_path / "nonexistent"
        output_dir = tmp_path / "output"
        project_root = Path(__file__).parent.parent.parent
        
        # Act
        result = subprocess.run(
            [
                str(project_root / ".venv" / "bin" / "python"),
                "scripts/export_figures.py",
                str(nonexistent_dir),
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Assert
        assert result.returncode != 0, "Should fail with non-existent directory"
        assert "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower()
