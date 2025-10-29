"""
Integration tests for prose level customization.

Tests the --prose-level flag to ensure minimal/standard/comprehensive
variations generate appropriate language and claims.
"""

import subprocess
import sys
from pathlib import Path


class TestProseLevels:
    """Test prose level variations."""
    
    def test_minimal_prose_shorter_than_standard(self, tmp_path):
        """Test that minimal prose generates significantly shorter content."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        minimal_output = tmp_path / "minimal"
        standard_output = tmp_path / "standard"
        
        # Act - Generate both versions
        for output_dir, prose_level in [(minimal_output, "minimal"), 
                                         (standard_output, "standard")]:
            cmd = [
                sys.executable,
                "scripts/generate_paper.py",
                str(fixture_dir),
                "--output-dir", str(output_dir),
                "--prose-level", prose_level,
                "--skip-latex"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False
            )
            
            assert result.returncode == 0, f"Failed for {prose_level}: {result.stderr}"
        
        # Assert - Compare word counts
        minimal_tex = (minimal_output / "main.tex").read_text()
        standard_tex = (standard_output / "main.tex").read_text()
        
        minimal_words = len(minimal_tex.split())
        standard_words = len(standard_tex.split())
        
        # Minimal should be noticeably shorter (at least 30% shorter)
        assert minimal_words < standard_words * 0.7, \
            f"Minimal ({minimal_words} words) should be <70% of standard ({standard_words} words)"
    
    def test_minimal_avoids_causal_claims(self, tmp_path):
        """Test that minimal prose avoids causal language."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "minimal_paper"
        
        # Act
        cmd = [
            sys.executable,
            "scripts/generate_paper.py",
            str(fixture_dir),
            "--output-dir", str(output_dir),
            "--prose-level", "minimal",
            "--skip-latex"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )
        
        # Assert
        assert result.returncode == 0
        
        latex_content = (output_dir / "main.tex").read_text()
        
        # Discussion and results should avoid strong causal claims
        discussion_section = self._extract_section(latex_content, "Discussion")
        results_section = self._extract_section(latex_content, "Results")
        
        # These phrases indicate causal claims (should be rare/absent in minimal)
        causal_phrases = [
            "demonstrates that",
            "proves that",
            "shows that",
            "leads to",
            "causes",
            "results in",
            "due to",
            "because of"
        ]
        
        combined_content = (discussion_section + results_section).lower()
        
        causal_count = sum(
            combined_content.count(phrase) 
            for phrase in causal_phrases
        )
        
        # Minimal prose should have very few causal claims
        # (allow some as they may appear in citations or data descriptions)
        assert causal_count <= 3, \
            f"Minimal prose should avoid causal claims, found {causal_count} instances"
    
    def test_comprehensive_more_detailed_than_standard(self, tmp_path):
        """Test that comprehensive prose is more detailed than standard."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        standard_output = tmp_path / "standard"
        comprehensive_output = tmp_path / "comprehensive"
        
        # Act
        for output_dir, prose_level in [(standard_output, "standard"),
                                         (comprehensive_output, "comprehensive")]:
            cmd = [
                sys.executable,
                "scripts/generate_paper.py",
                str(fixture_dir),
                "--output-dir", str(output_dir),
                "--prose-level", prose_level,
                "--skip-latex"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False
            )
            
            assert result.returncode == 0
        
        # Assert - Comprehensive should be longer
        standard_tex = (standard_output / "main.tex").read_text()
        comprehensive_tex = (comprehensive_output / "main.tex").read_text()
        
        standard_words = len(standard_tex.split())
        comprehensive_words = len(comprehensive_tex.split())
        
        # Comprehensive should be at least 20% longer
        assert comprehensive_words > standard_words * 1.2, \
            f"Comprehensive ({comprehensive_words}) should be >120% of standard ({standard_words})"
    
    def test_standard_is_default_prose_level(self, tmp_path):
        """Test that standard prose level is the default."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        default_output = tmp_path / "default"
        explicit_standard_output = tmp_path / "explicit_standard"
        
        # Act - Generate with and without explicit --prose-level=standard
        for output_dir, extra_args in [(default_output, []),
                                        (explicit_standard_output, ["--prose-level", "standard"])]:
            cmd = [
                sys.executable,
                "scripts/generate_paper.py",
                str(fixture_dir),
                "--output-dir", str(output_dir),
                "--skip-latex"
            ] + extra_args
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False
            )
            
            assert result.returncode == 0
        
        # Assert - Should produce similar word counts (within 20%)
        default_tex = (default_output / "main.tex").read_text()
        explicit_tex = (explicit_standard_output / "main.tex").read_text()
        
        default_words = len(default_tex.split())
        explicit_words = len(explicit_tex.split())
        
        word_count_ratio = default_words / explicit_words
        assert 0.8 <= word_count_ratio <= 1.2, \
            f"Default and explicit standard should be similar (ratio: {word_count_ratio})"
    
    def test_invalid_prose_level_rejected(self, tmp_path):
        """Test that invalid prose levels are rejected."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "paper_output"
        
        # Act
        cmd = [
            sys.executable,
            "scripts/generate_paper.py",
            str(fixture_dir),
            "--output-dir", str(output_dir),
            "--prose-level", "invalid_level",
            "--skip-latex"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
        
        # Assert
        assert result.returncode != 0
        error_output = result.stdout + result.stderr
        assert "invalid_level" in error_output.lower()
        assert "minimal" in error_output.lower()
        assert "standard" in error_output.lower()
        assert "comprehensive" in error_output.lower()
    
    @staticmethod
    def _extract_section(latex_content: str, section_name: str) -> str:
        """Extract a specific section from LaTeX content."""
        section_start = latex_content.find(f"\\section{{{section_name}}}")
        if section_start == -1:
            return ""
        
        # Find the next section command
        next_section_start = latex_content.find(r"\section{", section_start + 1)
        if next_section_start == -1:
            next_section_start = len(latex_content)
        
        return latex_content[section_start:next_section_start]
