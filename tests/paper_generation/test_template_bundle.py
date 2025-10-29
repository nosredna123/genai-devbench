"""Unit tests for TemplateBundle.

Tests ACM template version validation and file copying.
"""

import pytest
from pathlib import Path
from src.paper_generation.template_bundle import TemplateBundle
from src.paper_generation.exceptions import ConfigValidationError


class TestTemplateBundle:
    """Test template bundling and validation."""
    
    def test_default_template_dir(self):
        """Test default template directory is detected."""
        bundle = TemplateBundle()
        assert bundle.template_dir.exists()
        assert bundle.template_dir.name == "acm_sigsoft"
    
    def test_version_check(self):
        """Test VERSION file is checked."""
        bundle = TemplateBundle()
        version = bundle.get_version()
        assert version == "1.90"
    
    def test_required_files_exist(self):
        """Test all required template files exist."""
        bundle = TemplateBundle()
        
        for filename in TemplateBundle.REQUIRED_FILES:
            filepath = bundle.template_dir / filename
            assert filepath.exists(), f"Missing template file: {filename}"
    
    def test_get_template_path(self):
        """Test getting path to specific template file."""
        bundle = TemplateBundle()
        
        cls_path = bundle.get_template_path("sigconf.cls")
        assert cls_path.exists()
        assert cls_path.name == "sigconf.cls"
    
    def test_get_nonexistent_template(self):
        """Test error when requesting nonexistent template file."""
        bundle = TemplateBundle()
        
        with pytest.raises(FileNotFoundError):
            bundle.get_template_path("nonexistent.cls")
    
    def test_copy_to_output(self, tmp_path):
        """Test copying templates to output directory."""
        bundle = TemplateBundle()
        output_dir = tmp_path / "output"
        
        bundle.copy_to_output(output_dir)
        
        # Check files were copied (except VERSION)
        assert (output_dir / "sigconf.cls").exists()
        assert (output_dir / "ACM-Reference-Format.bst").exists()
        assert (output_dir / "acmart.pdf").exists()
        # VERSION should not be copied
        assert not (output_dir / "VERSION").exists()
    
    def test_copy_creates_output_dir(self, tmp_path):
        """Test output directory is created if missing."""
        bundle = TemplateBundle()
        output_dir = tmp_path / "nested" / "output"
        
        assert not output_dir.exists()
        bundle.copy_to_output(output_dir)
        assert output_dir.exists()
    
    def test_invalid_template_dir(self, tmp_path):
        """Test error when template directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        
        with pytest.raises(ConfigValidationError, match="Template directory not found"):
            TemplateBundle(template_dir=nonexistent)
    
    def test_missing_template_file(self, tmp_path):
        """Test error when template file is missing."""
        # Create incomplete template directory
        incomplete_dir = tmp_path / "incomplete"
        incomplete_dir.mkdir()
        
        # Create VERSION file only
        (incomplete_dir / "VERSION").write_text("1.90")
        
        with pytest.raises(ConfigValidationError, match="Template files missing"):
            TemplateBundle(template_dir=incomplete_dir)
    
    def test_wrong_version(self, tmp_path):
        """Test error when template version doesn't match."""
        wrong_version_dir = tmp_path / "wrong_version"
        wrong_version_dir.mkdir()
        
        # Create all files with wrong version
        (wrong_version_dir / "VERSION").write_text("2.00")
        (wrong_version_dir / "sigconf.cls").write_text("dummy")
        (wrong_version_dir / "ACM-Reference-Format.bst").write_text("dummy")
        (wrong_version_dir / "acmart.pdf").write_text("dummy")
        
        with pytest.raises(ConfigValidationError, match="Template version mismatch"):
            TemplateBundle(template_dir=wrong_version_dir)
