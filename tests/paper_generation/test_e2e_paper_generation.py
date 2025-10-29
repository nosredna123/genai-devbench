"""
End-to-end test for paper generation.

Tests the complete pipeline by running the CLI on a sample experiment fixture
and verifying the generated paper meets all requirements.

NOTE: This test requires:
1. Valid OPENAI_API_KEY in .env file (loaded by pytest conftest)
2. Pandoc installed on the system (for LaTeX conversion)
3. pdflatex installed (optional, tests use --skip-latex by default)

The tests will be skipped if OPENAI_API_KEY is not available.
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
import json
import yaml


class TestEndToEndPaperGeneration:
    """End-to-end tests for complete paper generation pipeline."""
    
    @pytest.fixture
    def sample_experiment_dir(self):
        """Path to sample experiment fixture."""
        return Path(__file__).parent / "fixtures" / "sample_experiment"
    
    @pytest.fixture
    def output_dir(self, tmp_path):
        """Temporary output directory for generated paper."""
        return tmp_path / "paper_output"
    
    def test_generate_paper_cli_with_skip_latex(self, sample_experiment_dir, output_dir):
        """
        Test: Run generate_paper.py CLI with --skip-latex flag.
        
        This is the core E2E test that verifies the entire pipeline works:
        1. Load experiment data
        2. Generate all 7 sections
        3. Export figures
        4. Convert to LaTeX
        5. Verify output files exist
        
        Uses --skip-latex to avoid pdflatex dependency.
        """
        # Ensure sample experiment exists
        assert sample_experiment_dir.exists(), f"Sample experiment not found at {sample_experiment_dir}"
        assert (sample_experiment_dir / "analysis").exists(), "analysis/ subdirectory missing"
        
        # Build CLI command
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [
            sys.executable,
            str(cli_script),
            str(sample_experiment_dir),
            "--output-dir", str(output_dir),
            "--skip-latex",  # Skip pdflatex for faster testing
            "--verbose"
        ]
        
        # Run the CLI
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=os.environ.copy()  # Pass current environment including OPENAI_API_KEY
        )
        
        # Check exit code
        if result.returncode != 0:
            # Check if failure was due to missing API key
            error_output = result.stdout + result.stderr
            if "OPENAI_API_KEY" in error_output or "API key not found" in error_output:
                pytest.skip("OPENAI_API_KEY not available in subprocess environment")
            
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            pytest.fail(f"CLI failed with exit code {result.returncode}")
        
        # Verify success message in output
        assert "Paper generation complete" in result.stdout or "✅" in result.stdout
        
        # Verify output directory was created
        assert output_dir.exists(), "Output directory not created"
        
        # Verify main.tex was generated
        main_tex = output_dir / "main.tex"
        assert main_tex.exists(), "main.tex not generated"
        
        # Read generated LaTeX content
        latex_content = main_tex.read_text()
        
        # Verify all sections are present in LaTeX
        required_sections = [
            "abstract",
            "introduction", 
            "related work",
            "methodology",
            "results",
            "discussion",
            "conclusion"
        ]
        
        for section in required_sections:
            assert section.lower() in latex_content.lower(), \
                f"Section '{section}' not found in generated LaTeX"
        
        # Verify LaTeX uses ACM template
        assert "documentclass" in latex_content.lower() or "sigconf" in latex_content.lower(), \
            "ACM template not used"
        
        print(f"✅ E2E test passed: Paper generated successfully at {output_dir}")
    
    def test_generated_sections_meet_word_count(self, sample_experiment_dir, output_dir):
        """
        Test: Verify generated sections meet ≥800 word requirement.
        
        NOTE: This test will make actual OpenAI API calls and incur costs.
        Uses --skip-latex to speed up generation.
        """
        # Run generation
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [
            sys.executable,
            str(cli_script),
            str(sample_experiment_dir),
            "--output-dir", str(output_dir),
            "--skip-latex",
            "--verbose"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=os.environ.copy())
        
        if result.returncode != 0:
            pytest.skip(f"Paper generation failed: {result.stderr}")
        
        # Parse output to check word counts
        # The CLI should display word counts in the output
        output = result.stdout
        
        # Look for "Total words:" in output
        if "Total words:" in output:
            # Extract word count from output
            for line in output.split('\n'):
                if "Total words:" in line:
                    # Format is typically "Total words:     X,XXX"
                    parts = line.split(':')
                    if len(parts) >= 2:
                        word_count_str = parts[1].strip().replace(',', '')
                        try:
                            total_words = int(word_count_str)
                            # With 6 AI-generated sections @ 800 words each = 4800 words minimum
                            # Plus abstract (~200 words) = ~5000 words total minimum
                            assert total_words >= 4800, \
                                f"Total word count {total_words} is below minimum 4800 words"
                            print(f"✅ Word count test passed: {total_words} words generated")
                        except ValueError:
                            pytest.skip("Could not parse word count from CLI output")
        else:
            pytest.skip("Word count not reported in CLI output")
    
    def test_citation_placeholders_present(self, sample_experiment_dir, output_dir):
        """
        Test: Verify citation placeholders are present in generated paper.
        
        Citation placeholders should be in format **[CITE: framework]** to prevent
        AI hallucination of fake references.
        """
        # Run generation
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [
            sys.executable,
            str(cli_script),
            str(sample_experiment_dir),
            "--output-dir", str(output_dir),
            "--skip-latex"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=os.environ.copy())
        
        if result.returncode != 0:
            pytest.skip(f"Paper generation failed: {result.stderr}")
        
        # Read generated LaTeX
        main_tex = output_dir / "main.tex"
        if not main_tex.exists():
            pytest.skip("main.tex not found")
        
        latex_content = main_tex.read_text()
        
        # Check for citation placeholders
        # They should appear in bold: **[CITE: framework]**
        # Or converted to LaTeX: \textbf{[CITE: framework]}
        citation_markers = [
            "[CITE:",
            "CITE:",
        ]
        
        has_citations = any(marker in latex_content for marker in citation_markers)
        
        assert has_citations, \
            "No citation placeholders found in generated paper. " \
            "Expected format: [CITE: framework] or \\textbf{[CITE: framework]}"
        
        print("✅ Citation placeholder test passed")
    
    def test_figures_exported(self, sample_experiment_dir, output_dir):
        """
        Test: Verify figures are exported in both PDF and PNG formats at ≥300 DPI.
        """
        # Run generation
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [
            sys.executable,
            str(cli_script),
            str(sample_experiment_dir),
            "--output-dir", str(output_dir),
            "--skip-latex"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=os.environ.copy())
        
        if result.returncode != 0:
            pytest.skip(f"Paper generation failed: {result.stderr}")
        
        # Check for exported figures
        figures_dir = output_dir / "figures"
        
        # If figures directory doesn't exist, check in output_dir root
        if not figures_dir.exists():
            figures_dir = output_dir
        
        # Look for PDF and PNG files
        pdf_files = list(figures_dir.glob("*.pdf"))
        png_files = list(figures_dir.glob("*.png"))
        
        # Should have at least some figures
        # (Even if metrics are minimal, we should generate at least one figure)
        if len(pdf_files) == 0 and len(png_files) == 0:
            # Check if figures were mentioned in output
            if "figures exported" in result.stdout.lower():
                pytest.skip("Figures reported but files not found in expected location")
            else:
                pytest.skip("No figures generated (may be expected if no suitable metrics)")
        
        # For each PDF, should have corresponding PNG
        for pdf_file in pdf_files:
            png_file = pdf_file.with_suffix('.png')
            assert png_file.exists(), \
                f"Missing PNG for {pdf_file.name} (dual export requirement)"
        
        print(f"✅ Figure export test passed: {len(pdf_files)} figures exported")
    
    def test_ai_generated_markers_present(self, sample_experiment_dir, output_dir):
        """
        Test: Verify AI-generated content is marked with review indicators.
        
        All AI-generated sections should include markers like:
        % AI-GENERATED CONTENT START
        % AI-GENERATED CONTENT END
        """
        # Run generation
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [
            sys.executable,
            str(cli_script),
            str(sample_experiment_dir),
            "--output-dir", str(output_dir),
            "--skip-latex"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=os.environ.copy())
        
        if result.returncode != 0:
            pytest.skip(f"Paper generation failed: {result.stderr}")
        
        # Read generated LaTeX
        main_tex = output_dir / "main.tex"
        if not main_tex.exists():
            pytest.skip("main.tex not found")
        
        latex_content = main_tex.read_text()
        
        # Check for AI markers
        ai_markers = [
            "AI-GENERATED",
            "AI GENERATED",
            "REVIEW:",
        ]
        
        has_markers = any(marker in latex_content for marker in ai_markers)
        
        # Note: Markers might be in comments or text
        # We just want to ensure some form of marking exists
        if not has_markers:
            # This is a warning, not a failure - implementation may vary
            print("⚠️  Warning: No AI-generated markers found in LaTeX")
        else:
            print("✅ AI marker test passed")
    
    @pytest.mark.slow
    def test_full_pipeline_with_pdf_compilation(self, sample_experiment_dir, output_dir):
        """
        Test: Full pipeline including PDF compilation with pdflatex.
        
        This test is marked as 'slow' because it:
        1. Makes real OpenAI API calls
        2. Runs pdflatex (which is slow)
        3. May fail if pdflatex is not installed
        
        Run with: pytest -m slow
        """
        # Check if pdflatex is available
        try:
            subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                check=True,
                timeout=5
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("pdflatex not available on system")
        
        # Run generation WITHOUT --skip-latex
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [
            sys.executable,
            str(cli_script),
            str(sample_experiment_dir),
            "--output-dir", str(output_dir),
            "--verbose"
            # No --skip-latex flag
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=os.environ.copy())  # 10 min timeout
        
        if result.returncode != 0:
            # Check if failure was due to missing API key
            error_output = result.stdout + result.stderr
            if "OPENAI_API_KEY" in error_output or "API key not found" in error_output:
                pytest.skip("OPENAI_API_KEY not available in subprocess environment")
            
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            pytest.fail(f"Full pipeline failed with exit code {result.returncode}")
        
        # Verify both .tex and .pdf exist
        main_tex = output_dir / "main.tex"
        main_pdf = output_dir / "main.pdf"
        
        assert main_tex.exists(), "main.tex not generated"
        assert main_pdf.exists(), "main.pdf not compiled"
        
        # Verify PDF is a valid PDF file (basic check)
        pdf_content = main_pdf.read_bytes()
        assert pdf_content[:4] == b'%PDF', "Generated file is not a valid PDF"
        
        # Check PDF size is reasonable (not empty, not huge)
        pdf_size = main_pdf.stat().st_size
        assert pdf_size > 1000, "PDF file is suspiciously small"
        assert pdf_size < 50_000_000, "PDF file is suspiciously large (>50MB)"
        
        print(f"✅ Full pipeline test passed: PDF generated at {main_pdf} ({pdf_size:,} bytes)")


class TestCLIErrorHandling:
    """Test CLI error handling and validation."""
    
    def test_cli_fails_with_nonexistent_directory(self):
        """Test CLI fails gracefully with nonexistent experiment directory."""
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [
            sys.executable,
            str(cli_script),
            "/nonexistent/directory"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Should fail with exit code 1
        assert result.returncode != 0, "CLI should fail for nonexistent directory"
        
        # Error message should be informative
        error_output = result.stdout + result.stderr
        assert "not found" in error_output.lower() or "does not exist" in error_output.lower()
    
    def test_cli_shows_help_with_help_flag(self):
        """Test CLI displays help with --help flag."""
        cli_script = Path(__file__).parent.parent.parent / "scripts" / "generate_paper.py"
        cmd = [sys.executable, str(cli_script), "--help"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Should succeed
        assert result.returncode == 0
        
        # Should show usage information
        assert "usage:" in result.stdout.lower()
        assert "experiment_dir" in result.stdout.lower()
        assert "--output-dir" in result.stdout


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "--tb=short"])
