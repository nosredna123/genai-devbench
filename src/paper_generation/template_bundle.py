"""ACM SIGSOFT template bundling and validation.

This module handles bundling, copying, and validating ACM SIGSOFT template files
for camera-ready paper generation. Templates are verified for version integrity
and copied to each output directory.

Constitution Principle II: Clarity & Transparency - explicit version checking
Constitution Principle VII: Fail-Fast Philosophy - immediate error on corruption
"""

from pathlib import Path
import shutil
import hashlib
import logging
from typing import Optional

from .exceptions import ConfigValidationError


logger = logging.getLogger(__name__)


class TemplateBundle:
    """Manages ACM SIGSOFT LaTeX template files for paper generation.
    
    The template bundle includes:
    - sigconf.cls: ACM document class (v1.90)
    - ACM-Reference-Format.bst: Bibliography style
    - acmart.pdf: Template documentation
    
    All template files are bundled at a specific version and validated
    for integrity before use.
    """
    
    # Expected template version
    EXPECTED_VERSION = "1.90"
    
    # Template file paths (relative to repository root)
    TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "acm_sigsoft"
    
    REQUIRED_FILES = [
        "sigconf.cls",
        "ACM-Reference-Format.bst",
        "acmart.pdf",
        "VERSION"
    ]
    
    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize template bundle with optional custom template directory.
        
        Args:
            template_dir: Custom template directory (defaults to bundled templates)
        
        Raises:
            ConfigValidationError: Template directory missing or corrupted
        """
        self.template_dir = template_dir or self.TEMPLATE_DIR
        self._validate_templates()
    
    def _validate_templates(self) -> None:
        """Validate template files exist and version is correct.
        
        Raises:
            ConfigValidationError: Missing files or version mismatch
        """
        # Check template directory exists
        if not self.template_dir.exists():
            raise ConfigValidationError(
                f"Template directory not found: {self.template_dir}. "
                "Templates should be bundled with this repository. "
                "If missing, re-download from: "
                "https://mirrors.ctan.org/macros/latex/contrib/acmart.zip"
            )
        
        # Check all required files exist
        missing_files = []
        for filename in self.REQUIRED_FILES:
            filepath = self.template_dir / filename
            if not filepath.exists():
                missing_files.append(filename)
        
        if missing_files:
            raise ConfigValidationError(
                f"Template files missing: {', '.join(missing_files)}. "
                f"Templates directory: {self.template_dir}. "
                f"Expected files: {', '.join(self.REQUIRED_FILES)}. "
                "Re-download ACM templates from CTAN if corrupted."
            )
        
        # Validate version
        version_file = self.template_dir / "VERSION"
        actual_version = version_file.read_text().strip()
        
        if actual_version != self.EXPECTED_VERSION:
            raise ConfigValidationError(
                f"Template version mismatch: expected {self.EXPECTED_VERSION}, "
                f"found {actual_version}. "
                "Template version has changed. Update EXPECTED_VERSION constant "
                "in template_bundle.py if intentional, or re-download correct version."
            )
    
    def copy_to_output(self, output_dir: Path) -> None:
        """Copy template files to output directory for paper compilation.
        
        Validates file integrity after copying to detect corruption.
        
        Args:
            output_dir: Destination directory for template files
        
        Raises:
            OSError: Failed to copy files (permissions, disk space, etc.)
            ConfigValidationError: Copied files are corrupted
        """
        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all template files except VERSION (not needed for LaTeX)
        for filename in self.REQUIRED_FILES:
            if filename == "VERSION":
                continue  # Internal metadata, not needed for compilation
            
            src = self.template_dir / filename
            dst = output_dir / filename
            
            try:
                shutil.copy2(src, dst)
                
                # Verify file was copied correctly (simple size check)
                if dst.stat().st_size != src.stat().st_size:
                    logger.warning(
                        "Template file size mismatch after copy: %s "
                        "(expected %d bytes, got %d bytes)",
                        filename,
                        src.stat().st_size,
                        dst.stat().st_size
                    )
                    # Retry copy once
                    shutil.copy2(src, dst)
                    if dst.stat().st_size != src.stat().st_size:
                        raise ConfigValidationError(
                            f"Template file {filename} corrupted during copy. "
                            "File size mismatch persists after retry."
                        )
                        
            except OSError as e:
                raise OSError(
                    f"Failed to copy template file {filename} to {output_dir}: {e}"
                ) from e
    
    def get_template_path(self, filename: str) -> Path:
        """Get path to a specific template file.
        
        Args:
            filename: Name of template file
        
        Returns:
            Absolute path to template file
        
        Raises:
            FileNotFoundError: Template file doesn't exist
        """
        filepath = self.template_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(
                f"Template file not found: {filename} "
                f"in directory {self.template_dir}"
            )
        return filepath
    
    def get_version(self) -> str:
        """Get template version string.
        
        Returns:
            Version string (e.g., "1.90")
        """
        version_file = self.template_dir / "VERSION"
        return version_file.read_text().strip()
