"""
Integration tests for complete paper generation pipeline.

Tests the full end-to-end flow: load experiment → generate sections → 
export figures → convert to LaTeX → verify PDF compilation.

Following TDD: These tests should FAIL initially since implementations don't exist yet.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import json
import yaml

from src.paper_generation.models import PaperConfig, PaperResult
from src.paper_generation.exceptions import (
    ExperimentDataError,
    DependencyMissingError,
    PdfCompilationError
)


@pytest.fixture
def sample_experiment_dir(tmp_path):
    """Create a minimal valid experiment directory structure."""
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    
    # Create config directory with experiment.yaml
    config_dir = exp_dir / "config"
    config_dir.mkdir()
    config_yaml = {
        "frameworks": ["ChatDev", "MetaGPT", "AutoGen"],
        "num_runs": 50,
        "metrics": {
            "categories": ["efficiency", "cost", "quality"]
        }
    }
    (config_dir / "experiment.yaml").write_text(yaml.dump(config_yaml))
    
    # Create analysis directory with metrics.json
    analysis_dir = exp_dir / "analysis"
    analysis_dir.mkdir()
    metrics_data = {
        "frameworks": {
            "ChatDev": {
                "execution_time": {"mean": 245.3, "std": 32.1},
                "total_cost_usd": {"mean": 0.42, "std": 0.08}
            },
            "MetaGPT": {
                "execution_time": {"mean": 312.7, "std": 45.2},
                "total_cost_usd": {"mean": 0.53, "std": 0.11}
            },
            "AutoGen": {
                "execution_time": {"mean": 198.4, "std": 28.5},
                "total_cost_usd": {"mean": 0.35, "std": 0.06}
            }
        },
        "statistical_tests": {
            "kruskal_wallis": {"p_value": 0.0001, "statistic": 42.3}
        }
    }
    (analysis_dir / "metrics.json").write_text(json.dumps(metrics_data, indent=2))
    
    # Create statistical_report.md
    report_md = """# Statistical Analysis Report

## Descriptive Statistics

| Framework | Execution Time (s) | Cost (USD) |
|-----------|-------------------|------------|
| ChatDev   | 245.3 ± 32.1      | $0.42 ± 0.08 |
| MetaGPT   | 312.7 ± 45.2      | $0.53 ± 0.11 |
| AutoGen   | 198.4 ± 28.5      | $0.35 ± 0.06 |

## Inferential Statistics

Kruskal-Wallis test: p < 0.001, indicating significant differences.
"""
    (analysis_dir / "statistical_report.md").write_text(report_md)
    
    return exp_dir


@pytest.fixture
def paper_config(tmp_path, monkeypatch):
    """Create a minimal PaperConfig for testing."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Mock API key to avoid validation error
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
    
    # Create experiment directory to pass validation
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir(exist_ok=True)  # Allow existing directory
    
    return PaperConfig(
        experiment_dir=exp_dir,
        output_dir=output_dir,
        model="gpt-3.5-turbo",  # Use cheaper model for tests
        temperature=0.7,
        prose_level="standard"
    )


class TestPaperGeneratorIntegration:
    """Integration tests for PaperGenerator orchestration."""
    
    def test_complete_pipeline_success(self, sample_experiment_dir, paper_config, tmp_path):
        """Test complete pipeline: load → generate → export → convert → verify PDF.
        
        This is the MAIN integration test - verifies entire workflow.
        Expected to FAIL until PaperGenerator is implemented.
        """
        # Import will fail until module exists
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented, this test should:
        # 1. Create PaperGenerator instance
        # 2. Call generate() method
        # 3. Verify PaperResult is returned
        # 4. Check all sections were generated
        # 5. Verify figures were exported
        # 6. Confirm LaTeX files exist
        # 7. Validate PDF was compiled (if pdflatex available)
        
    def test_pipeline_validates_experiment_directory(self, paper_config, tmp_path):
        """Test that pipeline fails fast if experiment directory is invalid.
        
        Expected to FAIL until PaperGenerator validation is implemented.
        """
        # Point to non-existent directory
        paper_config.experiment_dir = tmp_path / "nonexistent"
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented, should raise ExperimentDataError
        # generator = PaperGenerator(paper_config)
        # with pytest.raises(ExperimentDataError, match="experiment directory does not exist"):
        #     generator.generate()
    
    def test_pipeline_validates_analysis_subdirectory(self, sample_experiment_dir, paper_config, tmp_path):
        """Test that pipeline fails if analysis/ subdirectory is missing.
        
        Expected to FAIL until PaperGenerator validation is implemented.
        """
        # Remove analysis directory
        import shutil
        analysis_dir = sample_experiment_dir / "analysis"
        if analysis_dir.exists():
            shutil.rmtree(analysis_dir)
        
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented, should raise ExperimentDataError
        # generator = PaperGenerator(paper_config)
        # with pytest.raises(ExperimentDataError, match="analysis subdirectory not found"):
        #     generator.generate()
    
    def test_pipeline_detects_pandoc_availability(self, sample_experiment_dir, paper_config):
        """Test that pipeline checks for Pandoc and fails fast if missing.
        
        Expected to FAIL until PaperGenerator Pandoc detection is implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented, mock subprocess to simulate missing Pandoc
        # with patch('subprocess.run', side_effect=FileNotFoundError):
        #     generator = PaperGenerator(paper_config)
        #     with pytest.raises(DependencyMissingError, match="Pandoc"):
        #         generator.generate()
    
    @patch('subprocess.run')
    def test_pipeline_handles_pdflatex_failure(self, mock_run, sample_experiment_dir, paper_config):
        """Test that pipeline handles pdflatex compilation errors gracefully.
        
        Expected to FAIL until PaperGenerator error handling is implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented, mock pdflatex failure
        # mock_run.return_value = Mock(returncode=1, stderr="LaTeX Error: Missing \\begin{document}")
        # generator = PaperGenerator(paper_config)
        # with pytest.raises(PdfCompilationError, match="LaTeX compilation failed"):
        #     generator.generate()
    
    def test_pipeline_returns_paper_result(self, sample_experiment_dir, paper_config):
        """Test that successful pipeline returns PaperResult with all fields.
        
        Expected to FAIL until PaperGenerator is fully implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # result = generator.generate()
        # 
        # assert isinstance(result, PaperResult)
        # assert result.output_dir.exists()
        # assert result.latex_file.exists()
        # assert result.pdf_file is None or result.pdf_file.exists()
        # assert result.total_words >= 800 * 7  # 7 sections minimum
        # assert result.generation_time_seconds > 0
        # assert result.total_tokens_used > 0
    
    def test_pipeline_generates_all_sections(self, sample_experiment_dir, paper_config):
        """Test that pipeline generates all required sections.
        
        Expected to FAIL until all section generators are implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # result = generator.generate()
        # 
        # expected_sections = [
        #     "abstract", "introduction", "related_work", 
        #     "methodology", "results", "discussion", "conclusion"
        # ]
        # 
        # for section in expected_sections:
        #     assert section in result.paper_structure.sections
        #     assert len(result.paper_structure.sections[section]) >= 800
    
    def test_pipeline_exports_figures(self, sample_experiment_dir, paper_config):
        """Test that pipeline exports figures in both PDF and PNG formats.
        
        Expected to FAIL until FigureExporter integration is complete.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # result = generator.generate()
        # 
        # assert len(result.paper_structure.figures) > 0
        # 
        # for figure in result.paper_structure.figures:
        #     assert figure.pdf_path.exists()
        #     assert figure.png_path.exists()
        #     assert figure.pdf_path.stat().st_size > 0
        #     assert figure.png_path.stat().st_size > 0
    
    def test_pipeline_inserts_citation_placeholders(self, sample_experiment_dir, paper_config):
        """Test that pipeline inserts citation placeholders for frameworks and claims.
        
        Expected to FAIL until CitationHandler integration is complete.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # result = generator.generate()
        # 
        # # Read generated LaTeX
        # latex_content = result.latex_file.read_text()
        # 
        # # Should contain citation placeholders for frameworks
        # assert "\\textbf{[CITE:" in latex_content
        # assert "ChatDev" in latex_content or "MetaGPT" in latex_content
    
    def test_pipeline_respects_skip_latex_flag(self, sample_experiment_dir, paper_config):
        """Test that pipeline can skip LaTeX/PDF compilation when requested.
        
        Expected to FAIL until PaperGenerator skip_latex logic is implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        paper_config.skip_latex = True
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # result = generator.generate()
        # 
        # # Should generate markdown sections but not LaTeX/PDF
        # assert result.pdf_file is None
        # assert result.total_words > 0  # Prose was still generated


class TestPaperGeneratorLoadExperiment:
    """Test experiment data loading functionality."""
    
    def test_load_experiment_reads_config_yaml(self, sample_experiment_dir, paper_config):
        """Test that experiment config is loaded correctly.
        
        Expected to FAIL until data loading is implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # context = generator._load_experiment_data()
        # 
        # assert "ChatDev" in context.frameworks
        # assert "MetaGPT" in context.frameworks
        # assert "AutoGen" in context.frameworks
        # assert context.num_runs == 50
    
    def test_load_experiment_reads_metrics_json(self, sample_experiment_dir, paper_config):
        """Test that metrics.json is parsed correctly.
        
        Expected to FAIL until data loading is implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # context = generator._load_experiment_data()
        # 
        # assert "execution_time" in context.metrics
        # assert context.metrics["execution_time"]["ChatDev"]["mean"] == 245.3
    
    def test_load_experiment_reads_statistical_report(self, sample_experiment_dir, paper_config):
        """Test that statistical report markdown is loaded.
        
        Expected to FAIL until data loading is implemented.
        """
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # context = generator._load_experiment_data()
        # 
        # assert context.statistical_report is not None
        # assert "Kruskal-Wallis" in context.statistical_report


class TestPaperGeneratorTiming:
    """Test performance requirements."""
    
    def test_pipeline_completes_within_time_limit(self, sample_experiment_dir, paper_config):
        """Test that paper generation completes in ≤3 minutes for typical experiment.
        
        This validates Success Criterion SC-008.
        Expected to FAIL until performance is optimized.
        """
        import time
        
        paper_config.experiment_dir = sample_experiment_dir
        
        with pytest.raises(ImportError):
            from src.paper_generation.paper_generator import PaperGenerator
        
        # TODO: Once implemented:
        # generator = PaperGenerator(paper_config)
        # 
        # start_time = time.time()
        # result = generator.generate()
        # elapsed = time.time() - start_time
        # 
        # # SC-008: Generate paper in ≤3 minutes
        # assert elapsed <= 180, f"Generation took {elapsed:.1f}s, expected ≤180s"
        # assert result.generation_time_seconds <= 180
