"""Unit tests for PandocConverter.

Tests Pandoc version detection, fail-fast behavior, and conversion mocking.
"""

import subprocess
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
from src.paper_generation.pandoc_converter import PandocConverter
from src.paper_generation.exceptions import DependencyMissingError, LatexConversionError


class TestPandocConverter:
    """Test Pandoc detection and conversion."""
    
    def test_pandoc_detection_success(self):
        """Test successful Pandoc detection."""
        # This test will only pass if Pandoc ≥2.0 is installed
        try:
            converter = PandocConverter()
            version = converter.get_version()
            assert version  # Should return version string
        except DependencyMissingError:
            pytest.skip("Pandoc not installed on test system")
    
    def test_pandoc_not_found(self):
        """Test error when Pandoc is not found."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with pytest.raises(DependencyMissingError, match="Pandoc"):
                PandocConverter()
    
    def test_pandoc_too_old(self):
        """Test error when Pandoc version < 2.0."""
        # Mock old Pandoc version
        mock_result = MagicMock()
        mock_result.stdout = "pandoc 1.19.2\nCompiled with...\n"
        
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(DependencyMissingError, match="too old"):
                PandocConverter()
    
    def test_pandoc_version_2_0_accepted(self):
        """Test Pandoc 2.0 is accepted."""
        mock_result = MagicMock()
        mock_result.stdout = "pandoc 2.0\nCompiled with...\n"
        
        with patch('subprocess.run', return_value=mock_result):
            converter = PandocConverter()
            assert converter is not None
    
    def test_pandoc_version_parsing(self):
        """Test version parsing from Pandoc output."""
        mock_result = MagicMock()
        mock_result.stdout = "pandoc 2.19.2\nCompiled with pandoc-types 1.22.2.1\n"
        
        with patch('subprocess.run', return_value=mock_result):
            converter = PandocConverter()
            version = converter.get_version()
            assert version == "2.19.2"
    
    def test_install_command_linux(self):
        """Test Linux installation command."""
        with patch('platform.system', return_value='Linux'):
            with patch('subprocess.run', side_effect=FileNotFoundError):
                try:
                    PandocConverter()
                except DependencyMissingError as e:
                    # Check that install instructions are provided
                    assert "apt-get" in str(e) or "dnf" in str(e) or "pacman" in str(e)
    
    def test_install_command_macos(self):
        """Test macOS installation command."""
        with patch('platform.system', return_value='Darwin'):
            with patch('subprocess.run', side_effect=FileNotFoundError):
                try:
                    PandocConverter()
                except DependencyMissingError as e:
                    assert "brew install pandoc" in str(e)
    
    def test_install_command_windows(self):
        """Test Windows installation command."""
        with patch('platform.system', return_value='Windows'):
            with patch('subprocess.run', side_effect=FileNotFoundError):
                try:
                    PandocConverter()
                except DependencyMissingError as e:
                    assert "pandoc.org" in str(e) or "choco" in str(e)
    
    def test_convert_success(self, tmp_path):
        """Test successful Markdown to LaTeX conversion."""
        # Create test files
        md_file = tmp_path / "input.md"
        latex_file = tmp_path / "output.tex"
        md_file.write_text("# Test\n\nContent")
        
        # Mock Pandoc installed and successful conversion
        mock_version = MagicMock()
        mock_version.stdout = "pandoc 2.19.2\n"
        
        mock_convert = MagicMock()
        mock_convert.returncode = 0
        mock_convert.stderr = ""
        
        def run_side_effect(*args, **kwargs):
            if "--version" in args[0]:
                return mock_version
            else:
                # Simulate file creation
                latex_file.write_text("\\section{Test}\n\nContent")
                return mock_convert
        
        with patch('subprocess.run', side_effect=run_side_effect):
            converter = PandocConverter()
            converter.convert_to_latex(md_file, latex_file)
            
            assert latex_file.exists()
    
    def test_convert_missing_input(self, tmp_path):
        """Test error when input file doesn't exist."""
        # Mock Pandoc installed
        mock_result = MagicMock()
        mock_result.stdout = "pandoc 2.19.2\n"
        
        with patch('subprocess.run', return_value=mock_result):
            converter = PandocConverter()
            
            with pytest.raises(FileNotFoundError):
                converter.convert_to_latex(
                    tmp_path / "nonexistent.md",
                    tmp_path / "output.tex"
                )
    
    def test_convert_pandoc_error(self, tmp_path):
        """Test error when Pandoc conversion fails."""
        md_file = tmp_path / "input.md"
        md_file.write_text("# Test")
        
        # Mock Pandoc installed
        mock_version = MagicMock()
        mock_version.stdout = "pandoc 2.19.2\n"
        
        # Mock conversion failure
        mock_convert = MagicMock()
        mock_convert.stderr = "Error at line 5: unclosed code block"
        
        def run_side_effect(*args, **kwargs):
            if "--version" in args[0]:
                return mock_version
            else:
                raise subprocess.CalledProcessError(1, args[0], stderr="Error at line 5")
        
        with patch('subprocess.run', side_effect=run_side_effect):
            converter = PandocConverter()
            
            with pytest.raises(LatexConversionError):
                converter.convert_to_latex(md_file, tmp_path / "output.tex")
