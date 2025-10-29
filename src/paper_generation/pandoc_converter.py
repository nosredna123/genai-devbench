"""Pandoc detection and Markdown→LaTeX conversion.

This module handles detection of Pandoc availability, version checking,
and conversion of Markdown to LaTeX for paper generation. Follows fail-fast
philosophy with OS-specific installation instructions.

Constitution Principle VII: Fail-Fast Philosophy - immediate error with remediation
Constitution Principle II: Clarity & Transparency - explicit installation guidance
"""

import subprocess
import platform
from pathlib import Path
from typing import Optional

from .exceptions import DependencyMissingError, LatexConversionError


class PandocConverter:
    """Handles Pandoc-based Markdown to LaTeX conversion.
    
    Detects Pandoc installation, validates version requirements,
    and performs conversions with error handling.
    """
    
    # Minimum required Pandoc version
    MIN_VERSION = (2, 0)
    
    def __init__(self):
        """Initialize Pandoc converter with version detection.
        
        Raises:
            DependencyMissingError: Pandoc not found or version too old
        """
        self._validate_pandoc()
    
    def _validate_pandoc(self) -> None:
        """Validate Pandoc is installed with sufficient version.
        
        Raises:
            DependencyMissingError: Pandoc not installed or version < 2.0
        """
        # Check if Pandoc is available
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
        except FileNotFoundError:
            self._raise_pandoc_not_found()
        except subprocess.CalledProcessError as e:
            raise DependencyMissingError(
                "Pandoc",
                f"Failed to check Pandoc version: {e}\n\n{self._get_install_command()}"
            ) from e
        
        # Parse version from output
        # Expected format: "pandoc 2.19.2\n..."
        version_line = result.stdout.split('\n')[0]
        try:
            version_str = version_line.split()[1]
            version_parts = version_str.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            version = (major, minor)
        except (IndexError, ValueError):
            raise DependencyMissingError(
                "Pandoc",
                f"Failed to parse Pandoc version from: {version_line}\n\n{self._get_install_command()}"
            )
        
        # Check minimum version
        if version < self.MIN_VERSION:
            raise DependencyMissingError(
                "Pandoc",
                f"Pandoc version {version[0]}.{version[1]} is too old. "
                f"Minimum required: {self.MIN_VERSION[0]}.{self.MIN_VERSION[1]}\n\n"
                f"{self._get_install_command()}"
            )
    
    def _raise_pandoc_not_found(self) -> None:
        """Raise DependencyMissingError with OS-specific installation instructions.
        
        Raises:
            DependencyMissingError: Always raised with installation command
        """
        raise DependencyMissingError(
            "Pandoc",
            "Pandoc is required to convert Markdown to LaTeX for paper generation.\n\n"
            f"{self._get_install_command()}"
        )
    
    def _get_install_command(self) -> str:
        """Get OS-specific Pandoc installation command.
        
        Returns:
            Shell command to install Pandoc
        """
        os_name = platform.system()
        
        if os_name == "Linux":
            # Detect Linux distribution
            try:
                with open("/etc/os-release", encoding="utf-8") as f:
                    os_release = f.read().lower()
                
                if "ubuntu" in os_release or "debian" in os_release:
                    return "sudo apt-get update && sudo apt-get install -y pandoc"
                elif "fedora" in os_release or "rhel" in os_release or "centos" in os_release:
                    return "sudo dnf install -y pandoc"
                elif "arch" in os_release:
                    return "sudo pacman -S pandoc"
            except FileNotFoundError:
                pass
            
            # Generic Linux fallback
            return (
                "Install Pandoc using your package manager:\n"
                "  Debian/Ubuntu: sudo apt-get install pandoc\n"
                "  Fedora/RHEL: sudo dnf install pandoc\n"
                "  Arch: sudo pacman -S pandoc\n"
                "Or download from: https://pandoc.org/installing.html"
            )
        
        elif os_name == "Darwin":  # macOS
            return "brew install pandoc"
        
        elif os_name == "Windows":
            return (
                "Download installer from: https://pandoc.org/installing.html\n"
                "Or use Chocolatey: choco install pandoc"
            )
        
        else:
            return "Download from: https://pandoc.org/installing.html"
    
    def convert_to_latex(
        self,
        markdown_path: Path,
        latex_path: Path,
        template: Optional[Path] = None
    ) -> None:
        """Convert Markdown file to LaTeX using Pandoc.
        
        Args:
            markdown_path: Input Markdown file
            latex_path: Output LaTeX file
            template: Optional Pandoc LaTeX template
        
        Raises:
            LatexConversionError: Pandoc conversion failed
            FileNotFoundError: Input file doesn't exist
        """
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        # Build Pandoc command
        cmd = [
            "pandoc",
            str(markdown_path),
            "-o", str(latex_path),
            "--standalone",
            "--from", "markdown",
            "--to", "latex"
        ]
        
        if template:
            cmd.extend(["--template", str(template)])
        
        # Run conversion
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise LatexConversionError(
                f"Pandoc conversion failed for {markdown_path}",
                pandoc_output=e.stderr
            ) from e
        
        # Verify output was created
        if not latex_path.exists():
            raise LatexConversionError(
                f"Pandoc completed but output file was not created: {latex_path}. "
                "This may indicate insufficient disk space or permissions.",
                pandoc_output=result.stderr
            )
    
    def get_version(self) -> str:
        """Get installed Pandoc version string.
        
        Returns:
            Version string (e.g., "2.19.2")
        """
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_line = result.stdout.split('\n')[0]
        return version_line.split()[1]
