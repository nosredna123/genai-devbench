"""
Unit tests for section generators.

Tests each section generator's context parsing, prose generation calls,
and word count validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import yaml
import json

from src.paper_generation.sections.abstract_generator import AbstractGenerator
from src.paper_generation.sections.introduction_generator import IntroductionGenerator
from src.paper_generation.sections.related_work_generator import RelatedWorkGenerator
from src.paper_generation.sections.methodology_generator import MethodologyGenerator
from src.paper_generation.sections.results_generator import ResultsGenerator
from src.paper_generation.sections.discussion_generator import DiscussionGenerator
from src.paper_generation.sections.conclusion_generator import ConclusionGenerator
from src.paper_generation.models import PaperConfig
from src.paper_generation.exceptions import ExperimentDataError


@pytest.fixture
def experiment_dir(tmp_path):
    """Create sample experiment directory with data files."""
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    analysis_dir = exp_dir / "analysis"
    analysis_dir.mkdir()
    
    # Create config.yaml
    config_data = {
        "experiment": {
            "name": "Framework Comparison",
            "frameworks": ["ChatDev", "MetaGPT", "AutoGen"],
            "task": "Build a web application"
        }
    }
    (exp_dir / "config.yaml").write_text(yaml.dump(config_data))
    
    # Create metrics.json
    metrics_data = {
        "efficiency": {
            "ChatDev": {"mean": 120.5, "std": 15.2},
            "MetaGPT": {"mean": 135.8, "std": 18.3},
            "AutoGen": {"mean": 110.2, "std": 12.7}
        },
        "statistical_tests": {
            "kruskal_wallis_p": 0.023,
            "effect_sizes": {"ChatDev_vs_MetaGPT": 0.45}
        }
    }
    (analysis_dir / "metrics.json").write_text(json.dumps(metrics_data))
    
    # Create statistical_report.md
    report = """# Statistical Analysis Report

## Key Findings
- Framework A showed significant improvement
- Effect size was moderate (d=0.45)
"""
    (analysis_dir / "statistical_report.md").write_text(report)
    
    return exp_dir


@pytest.fixture
def paper_config(experiment_dir, tmp_path):
    """Create PaperConfig for testing."""
    return PaperConfig(
        experiment_dir=experiment_dir,
        output_dir=tmp_path / "output",
        prose_level="standard"
    )


class TestAbstractGenerator:
    """Test AbstractGenerator."""
    
    def test_generate_returns_string(self, experiment_dir, paper_config):
        """Test generate returns a string."""
        generator = AbstractGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_abstract_includes_frameworks(self, experiment_dir, paper_config):
        """Test abstract includes framework names."""
        generator = AbstractGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        assert "ChatDev" in result or "MetaGPT" in result or "AutoGen" in result
    
    def test_abstract_is_concise(self, experiment_dir, paper_config):
        """Test abstract is reasonably concise (~200 words)."""
        generator = AbstractGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        word_count = len(result.split())
        # Abstract should be under 300 words (not 800 like other sections)
        assert word_count < 300


class TestIntroductionGenerator:
    """Test IntroductionGenerator."""
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_calls_prose_engine(self, mock_generate, experiment_dir, paper_config):
        """Test calls ProseEngine.generate_prose()."""
        mock_generate.return_value = "Generated introduction prose. " * 200
        
        generator = IntroductionGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        mock_generate.assert_called_once()
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_section_context_has_correct_name(self, mock_generate, experiment_dir, paper_config):
        """Test SectionContext has section_name='introduction'."""
        mock_generate.return_value = "Generated prose. " * 200
        
        generator = IntroductionGenerator()
        generator.generate(experiment_dir, paper_config)
        
        call_args = mock_generate.call_args[0]
        context = call_args[0]
        assert context.section_name == "introduction"
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_section_context_has_min_words_800(self, mock_generate, experiment_dir, paper_config):
        """Test SectionContext requires ≥800 words."""
        mock_generate.return_value = "Generated prose. " * 200
        
        generator = IntroductionGenerator()
        generator.generate(experiment_dir, paper_config)
        
        call_args = mock_generate.call_args[0]
        context = call_args[0]
        assert context.min_words >= 800


class TestRelatedWorkGenerator:
    """Test RelatedWorkGenerator."""
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_calls_prose_engine(self, mock_generate, experiment_dir, paper_config):
        """Test calls ProseEngine.generate_prose()."""
        mock_generate.return_value = "Related work prose. " * 200
        
        generator = RelatedWorkGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        mock_generate.assert_called_once()
    
    @patch('src.paper_generation.citation_handler.CitationHandler.insert_placeholders')
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_inserts_citation_placeholders(self, mock_generate, mock_citations, 
                                          experiment_dir, paper_config):
        """Test inserts citation placeholders for frameworks."""
        mock_generate.return_value = "Discussion of ChatDev and MetaGPT. " * 100
        mock_citations.return_value = "Discussion of **[CITE: ChatDev]** and **[CITE: MetaGPT]**. " * 100
        
        generator = RelatedWorkGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        # Should have called citation handler
        mock_citations.assert_called_once()
        # Result should include citation placeholders
        assert "[CITE:" in result


class TestMethodologyGenerator:
    """Test MethodologyGenerator."""
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_calls_prose_engine(self, mock_generate, experiment_dir, paper_config):
        """Test calls ProseEngine.generate_prose()."""
        mock_generate.return_value = "Methodology prose. " * 200
        
        generator = MethodologyGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        mock_generate.assert_called_once()
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_includes_task_description(self, mock_generate, experiment_dir, paper_config):
        """Test SectionContext includes task description."""
        mock_generate.return_value = "Methodology prose. " * 200
        
        generator = MethodologyGenerator()
        generator.generate(experiment_dir, paper_config)
        
        call_args = mock_generate.call_args[0]
        context = call_args[0]
        assert len(context.task_description) > 0


class TestResultsGenerator:
    """Test ResultsGenerator."""
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_calls_prose_engine(self, mock_generate, experiment_dir, paper_config):
        """Test calls ProseEngine.generate_prose()."""
        mock_generate.return_value = "Results prose. " * 200
        
        generator = ResultsGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        mock_generate.assert_called_once()
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_includes_statistical_results(self, mock_generate, experiment_dir, paper_config):
        """Test SectionContext includes statistical results."""
        mock_generate.return_value = "Results prose. " * 200
        
        generator = ResultsGenerator()
        generator.generate(experiment_dir, paper_config)
        
        call_args = mock_generate.call_args[0]
        context = call_args[0]
        assert context.statistical_results is not None
        assert len(context.statistical_results) > 0
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_includes_metrics_data(self, mock_generate, experiment_dir, paper_config):
        """Test SectionContext includes metrics data."""
        mock_generate.return_value = "Results prose. " * 200
        
        generator = ResultsGenerator()
        generator.generate(experiment_dir, paper_config)
        
        call_args = mock_generate.call_args[0]
        context = call_args[0]
        assert context.metrics is not None
        assert len(context.metrics) > 0


class TestDiscussionGenerator:
    """Test DiscussionGenerator."""
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_calls_prose_engine(self, mock_generate, experiment_dir, paper_config):
        """Test calls ProseEngine.generate_prose()."""
        mock_generate.return_value = "Discussion prose. " * 200
        
        generator = DiscussionGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        mock_generate.assert_called_once()
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_section_name_is_discussion(self, mock_generate, experiment_dir, paper_config):
        """Test SectionContext has section_name='discussion'."""
        mock_generate.return_value = "Discussion prose. " * 200
        
        generator = DiscussionGenerator()
        generator.generate(experiment_dir, paper_config)
        
        call_args = mock_generate.call_args[0]
        context = call_args[0]
        assert context.section_name == "discussion"


class TestConclusionGenerator:
    """Test ConclusionGenerator."""
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_calls_prose_engine(self, mock_generate, experiment_dir, paper_config):
        """Test calls ProseEngine.generate_prose()."""
        mock_generate.return_value = "Conclusion prose. " * 200
        
        generator = ConclusionGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        mock_generate.assert_called_once()
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_includes_key_findings(self, mock_generate, experiment_dir, paper_config):
        """Test SectionContext includes key findings."""
        mock_generate.return_value = "Conclusion prose. " * 200
        
        generator = ConclusionGenerator()
        generator.generate(experiment_dir, paper_config)
        
        call_args = mock_generate.call_args[0]
        context = call_args[0]
        # Key findings should be extracted from statistical report
        assert context.key_findings is not None


class TestBaseSectionGeneratorWordCountValidation:
    """Test word count validation in BaseSectionGenerator."""
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_validate_word_count_sufficient(self, mock_generate, experiment_dir, paper_config):
        """Test validation passes for sufficient words."""
        mock_generate.return_value = "Word " * 850  # 850 words
        
        generator = IntroductionGenerator()
        result = generator.generate(experiment_dir, paper_config)
        
        # Should not raise - 850 >= 800
        word_count = len(result.split())
        assert word_count >= 800
    
    @patch('src.paper_generation.prose_engine.ProseEngine.generate_prose')
    def test_validate_word_count_insufficient_raises_error(self, mock_generate, 
                                                          experiment_dir, paper_config):
        """Test validation fails for insufficient words."""
        mock_generate.return_value = "Word " * 700  # 700 words (insufficient)
        
        generator = IntroductionGenerator()
        
        # ProseEngine should raise error internally
        # But if it doesn't, our generator should catch it
        with pytest.raises(Exception):  # Could be ProseGenerationError or ExperimentDataError
            generator.generate(experiment_dir, paper_config)


class TestSectionGeneratorExperimentDataLoading:
    """Test experiment data loading."""
    
    def test_load_experiment_data_missing_config(self, tmp_path, paper_config):
        """Test error when config.yaml missing."""
        exp_dir = tmp_path / "bad_experiment"
        exp_dir.mkdir()
        (exp_dir / "analysis").mkdir()
        
        generator = AbstractGenerator()
        
        with pytest.raises(ExperimentDataError):
            generator._load_experiment_data(exp_dir)
    
    def test_load_experiment_data_missing_metrics(self, tmp_path, paper_config):
        """Test error when metrics.json missing."""
        exp_dir = tmp_path / "bad_experiment"
        exp_dir.mkdir()
        analysis_dir = exp_dir / "analysis"
        analysis_dir.mkdir()
        
        # Has config but no metrics
        (exp_dir / "config.yaml").write_text("experiment: {name: test}")
        
        generator = AbstractGenerator()
        
        with pytest.raises(ExperimentDataError):
            generator._load_experiment_data(exp_dir)
    
    def test_load_experiment_data_success(self, experiment_dir):
        """Test successful data loading."""
        generator = AbstractGenerator()
        data = generator._load_experiment_data(experiment_dir)
        
        assert "config" in data
        assert "metrics" in data
        assert "statistical_report" in data
