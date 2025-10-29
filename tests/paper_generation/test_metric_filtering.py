"""
Unit tests for metric filtering in ResultsGenerator.

Tests the _prepare_context override that filters metrics based on config.
"""

import pytest
from pathlib import Path
from dataclasses import replace

from src.paper_generation.sections.results_generator import ResultsGenerator
from src.paper_generation.models import PaperConfig, SectionContext
from src.paper_generation.prose_engine import ProseEngine


class TestMetricFiltering:
    """Test metric filtering logic in ResultsGenerator."""
    
    def test_no_filter_includes_all_metrics(self, tmp_path):
        """Test that when metrics_filter is None, all metrics are included."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            metrics_filter=None,  # No filtering
            skip_latex=True,
            figures_only=True
        )
        prose_engine = ProseEngine(config)
        generator = ResultsGenerator(config, prose_engine)
        
        # Metrics are indexed by framework, then metric name
        all_metrics = {
            "chatdev": {"executability": 0.85, "code_quality": 7.5, "cost": 0.50},
            "metagpt": {"executability": 0.90, "code_quality": 8.0, "cost": 0.45}
        }
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics=all_metrics,
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        filtered = generator._prepare_context(context, "results")
        
        # Assert
        assert filtered.metrics == all_metrics
        assert len(filtered.metrics["chatdev"]) == 3
        assert len(filtered.metrics["metagpt"]) == 3
        assert "executability" in filtered.metrics["chatdev"]
        assert "code_quality" in filtered.metrics["chatdev"]
        assert "cost" in filtered.metrics["chatdev"]
    
    def test_single_metric_filter(self, tmp_path):
        """Test filtering to a single metric."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            metrics_filter=["executability"],
            skip_latex=True,
            figures_only=True
        )
        prose_engine = ProseEngine(config)
        generator = ResultsGenerator(config, prose_engine)
        
        all_metrics = {
            "chatdev": {"executability": 0.85, "code_quality": 7.5, "cost": 0.50},
            "metagpt": {"executability": 0.90, "code_quality": 8.0, "cost": 0.45}
        }
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics=all_metrics,
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        filtered = generator._prepare_context(context, "results")
        
        # Assert
        assert len(filtered.metrics["chatdev"]) == 1
        assert len(filtered.metrics["metagpt"]) == 1
        assert "executability" in filtered.metrics["chatdev"]
        assert "executability" in filtered.metrics["metagpt"]
        assert "code_quality" not in filtered.metrics["chatdev"]
        assert "cost" not in filtered.metrics["chatdev"]
        assert filtered.metrics["chatdev"]["executability"] == 0.85
        assert filtered.metrics["metagpt"]["executability"] == 0.90
    
    def test_multiple_metric_filter(self, tmp_path):
        """Test filtering to multiple metrics."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            metrics_filter=["executability", "cost"],
            skip_latex=True,
            figures_only=True
        )
        prose_engine = ProseEngine(config)
        generator = ResultsGenerator(config, prose_engine)
        
        all_metrics = {
            "chatdev": {
                "executability": 0.85,
                "code_quality": 7.5,
                "cost": 0.50,
                "token_usage": 10000
            },
            "metagpt": {
                "executability": 0.90,
                "code_quality": 8.0,
                "cost": 0.45,
                "token_usage": 9500
            }
        }
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics=all_metrics,
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        filtered = generator._prepare_context(context, "results")
        
        # Assert
        assert len(filtered.metrics["chatdev"]) == 2
        assert len(filtered.metrics["metagpt"]) == 2
        assert "executability" in filtered.metrics["chatdev"]
        assert "cost" in filtered.metrics["chatdev"]
        assert "code_quality" not in filtered.metrics["chatdev"]
        assert "token_usage" not in filtered.metrics["chatdev"]
    
    def test_metric_filter_with_nonexistent_metric(self, tmp_path):
        """Test that filtering with non-existent metric names is handled gracefully."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            metrics_filter=["executability", "nonexistent_metric"],
            skip_latex=True,
            figures_only=True
        )
        prose_engine = ProseEngine(config)
        generator = ResultsGenerator(config, prose_engine)
        
        all_metrics = {
            "chatdev": {"executability": 0.85, "code_quality": 7.5},
            "metagpt": {"executability": 0.90, "code_quality": 8.0}
        }
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics=all_metrics,
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        filtered = generator._prepare_context(context, "results")
        
        # Assert - only existing metrics should be included
        assert len(filtered.metrics["chatdev"]) == 1
        assert "executability" in filtered.metrics["chatdev"]
        assert "nonexistent_metric" not in filtered.metrics["chatdev"]
    
    def test_empty_filter_list_includes_all(self, tmp_path):
        """Test that empty filter list behaves like None (includes all)."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            metrics_filter=[],  # Empty list
            skip_latex=True,
            figures_only=True
        )
        prose_engine = ProseEngine(config)
        generator = ResultsGenerator(config, prose_engine)
        
        all_metrics = {
            "chatdev": {"executability": 0.85, "code_quality": 7.5},
            "metagpt": {"executability": 0.90, "code_quality": 8.0}
        }
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics=all_metrics,
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        filtered = generator._prepare_context(context, "results")
        
        # Assert - empty list should filter out everything
        assert len(filtered.metrics["chatdev"]) == 0
        assert len(filtered.metrics["metagpt"]) == 0
    
    def test_filtered_context_preserves_other_fields(self, tmp_path):
        """Test that filtering only affects metrics, not other context fields."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            metrics_filter=["executability"],
            skip_latex=True,
            figures_only=True
        )
        prose_engine = ProseEngine(config)
        generator = ResultsGenerator(config, prose_engine)
        
        all_metrics = {
            "chatdev": {"executability": 0.85, "code_quality": 7.5},
            "metagpt": {"executability": 0.90, "code_quality": 8.0}
        }
        
        key_findings = [
            "ChatDev shows higher executability",
            "MetaGPT has better code quality"
        ]
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test experiment summary",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics=all_metrics,
            statistical_results={"p_value": 0.03},
            key_findings=key_findings
        )
        
        # Act
        filtered = generator._prepare_context(context, "results")
        
        # Assert - non-metric fields unchanged
        assert filtered.section_name == "results"
        assert filtered.experiment_summary == "Test experiment summary"
        assert filtered.frameworks == ["ChatDev", "MetaGPT"]
        assert filtered.num_runs == 50
        assert filtered.statistical_results == {"p_value": 0.03}
        assert filtered.key_findings == key_findings
        
        # But metrics should be filtered
        assert len(filtered.metrics["chatdev"]) == 1
        assert "executability" in filtered.metrics["chatdev"]
    
    def test_prepare_context_returns_new_instance(self, tmp_path):
        """Test that _prepare_context returns a new SectionContext instance."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            metrics_filter=["executability"],
            skip_latex=True,
            figures_only=True
        )
        prose_engine = ProseEngine(config)
        generator = ResultsGenerator(config, prose_engine)
        
        all_metrics = {
            "chatdev": {"executability": 0.85, "code_quality": 7.5},
            "metagpt": {"executability": 0.90, "code_quality": 8.0}
        }
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics=all_metrics,
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        filtered = generator._prepare_context(context, "results")
        
        # Assert - should be different instances
        assert filtered is not context
        # Original should be unchanged
        assert len(context.metrics["chatdev"]) == 2
        # Filtered should have only selected metric
        assert len(filtered.metrics["chatdev"]) == 1
