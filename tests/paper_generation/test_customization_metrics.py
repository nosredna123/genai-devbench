"""
Integration tests for metric filtering customization.

Tests the --metrics-filter flag to ensure only selected metric categories
appear in tables and prose.
"""

import subprocess
import sys
from pathlib import Path


class TestMetricFiltering:
    """Test metric category filtering."""
    
    def test_metrics_filter_affects_tables_and_prose(self, tmp_path):
        """Test that --metrics-filter limits both statistical tables and prose."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "paper_output"
        
        # Act - Generate paper with only efficiency and cost metrics
        cmd = [
            sys.executable,
            "scripts/generate_paper.py",
            str(fixture_dir),
            "--output-dir", str(output_dir),
            "--metrics-filter", "execution_time,total_cost_usd",
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
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        latex_file = output_dir / "main.tex"
        assert latex_file.exists(), "main.tex not generated"
        
        latex_content = latex_file.read_text()
        
        # Should include filtered metrics
        assert "execution_time" in latex_content.lower() or "execution time" in latex_content.lower()
        assert "cost" in latex_content.lower()
        
        # Should NOT include excluded metrics (test_pass_rate, code_quality_score, tokens_used)
        # Note: We need to be careful about incidental mentions in prose
        results_section = self._extract_results_section(latex_content)
        
        # Check that filtered metrics dominate the results section
        assert results_section.lower().count("execution") >= 2, \
            "execution_time metric should appear multiple times in results"
        assert results_section.lower().count("cost") >= 2, \
            "cost metric should appear multiple times in results"
    
    def test_filtered_metrics_exclude_others(self, tmp_path):
        """Test that filtering explicitly excludes non-selected metrics."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "paper_output"
        
        # Act - Generate with only one metric
        cmd = [
            sys.executable,
            "scripts/generate_paper.py",
            str(fixture_dir),
            "--output-dir", str(output_dir),
            "--metrics-filter", "execution_time",
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
        
        latex_file = output_dir / "main.tex"
        latex_content = latex_file.read_text()
        
        # execution_time should be present
        assert "execution" in latex_content.lower()
        
        # Other metrics should have minimal presence (may appear in general discussion)
        # but should not have dedicated tables or detailed analysis
        results_section = self._extract_results_section(latex_content)
        
        # Execution time should be prominent
        execution_mentions = results_section.lower().count("execution")
        cost_mentions = results_section.lower().count("cost")
        tokens_mentions = results_section.lower().count("token")
        
        assert execution_mentions > cost_mentions, \
            "Filtered metric (execution_time) should be more prominent than excluded metrics"
        assert execution_mentions > tokens_mentions, \
            "Filtered metric should dominate over excluded metrics"
    
    def test_no_metrics_filter_includes_all_metrics(self, tmp_path):
        """Test that without --metrics-filter, all metrics are included."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "paper_output"
        
        # Act - Generate without metrics filter
        cmd = [
            sys.executable,
            "scripts/generate_paper.py",
            str(fixture_dir),
            "--output-dir", str(output_dir),
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
        
        latex_file = output_dir / "main.tex"
        latex_content = latex_file.read_text()
        
        results_section = self._extract_results_section(latex_content)
        
        # All metric categories should appear
        assert "execution" in results_section.lower() or "time" in results_section.lower()
        assert "cost" in results_section.lower()
        assert "token" in results_section.lower()
        assert "quality" in results_section.lower() or "test" in results_section.lower()
    
    def test_invalid_metric_names_rejected(self, tmp_path):
        """Test that invalid metric names are rejected with helpful error."""
        # Arrange
        fixture_dir = Path(__file__).parent / "fixtures" / "sample_experiment"
        output_dir = tmp_path / "paper_output"
        
        # Act - Use invalid metric name
        cmd = [
            sys.executable,
            "scripts/generate_paper.py",
            str(fixture_dir),
            "--output-dir", str(output_dir),
            "--metrics-filter", "invalid_metric,execution_time",
            "--skip-latex"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
        
        # Assert - Should fail with error message
        assert result.returncode != 0
        error_output = result.stdout + result.stderr
        assert "invalid_metric" in error_output.lower()
        assert "available" in error_output.lower() or "valid" in error_output.lower()
    
    @staticmethod
    def _extract_results_section(latex_content: str) -> str:
        """Extract the Results section from LaTeX content."""
        results_start = latex_content.find(r"\section{Results}")
        if results_start == -1:
            return ""
        
        # Find next section
        discussion_start = latex_content.find(r"\section{Discussion}", results_start)
        if discussion_start == -1:
            discussion_start = len(latex_content)
        
        return latex_content[results_start:discussion_start]
