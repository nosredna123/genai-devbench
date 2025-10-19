"""Tests for visualization format inference functionality.

This test module validates the format inference helper that was added
to fix the bug where SVG files were being saved with .png extensions.
"""

from src.analysis.visualizations import _infer_format_from_path


class TestFormatInference:
    """Test format inference from file paths."""
    
    def test_infer_png_format(self):
        """Test PNG format inference."""
        assert _infer_format_from_path('chart.png') == 'png'
        assert _infer_format_from_path('/path/to/chart.png') == 'png'
        assert _infer_format_from_path('analysis_output/timeline.png') == 'png'
    
    def test_infer_svg_format(self):
        """Test SVG format inference."""
        assert _infer_format_from_path('chart.svg') == 'svg'
        assert _infer_format_from_path('/path/to/chart.svg') == 'svg'
    
    def test_infer_pdf_format(self):
        """Test PDF format inference."""
        assert _infer_format_from_path('chart.pdf') == 'pdf'
        assert _infer_format_from_path('/path/to/chart.pdf') == 'pdf'
    
    def test_infer_jpeg_format(self):
        """Test JPEG format inference."""
        assert _infer_format_from_path('chart.jpg') == 'jpeg'
        assert _infer_format_from_path('chart.jpeg') == 'jpeg'
    
    def test_case_insensitive(self):
        """Test that format inference is case-insensitive."""
        assert _infer_format_from_path('chart.PNG') == 'png'
        assert _infer_format_from_path('chart.Svg') == 'svg'
        assert _infer_format_from_path('chart.PDF') == 'pdf'
    
    def test_unknown_extension_defaults_to_png(self):
        """Test that unknown extensions default to PNG."""
        assert _infer_format_from_path('chart.xyz') == 'png'
        assert _infer_format_from_path('chart.unknown') == 'png'
        assert _infer_format_from_path('chart') == 'png'  # No extension
    
    def test_no_extension(self):
        """Test file with no extension defaults to PNG."""
        assert _infer_format_from_path('chart') == 'png'
        assert _infer_format_from_path('/path/to/chart') == 'png'
