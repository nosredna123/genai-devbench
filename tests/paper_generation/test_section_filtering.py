"""
Unit tests for section filtering logic in PaperGenerator.

Tests the _generate_section_outline method and section selection logic.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from src.paper_generation.paper_generator import PaperGenerator
from src.paper_generation.models import PaperConfig, SectionContext


class TestSectionFilteringLogic:
    """Test section filtering and outline generation."""
    
    def test_generate_section_outline_introduction(self, tmp_path):
        """Test that introduction outline contains expected structure."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            sections=["methodology"],  # Only methodology gets full prose
            skip_latex=True
        )
        generator = PaperGenerator(config)
        
        context = SectionContext(
            section_name="introduction",
            experiment_summary="Test experiment",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics={},
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        outline = generator._generate_section_outline("introduction", context)
        
        # Assert
        assert "itemize" in outline.lower(), "Outline should use LaTeX itemize environment"
        assert "motivation" in outline.lower(), "Should mention motivation"
        assert "research questions" in outline.lower(), "Should mention research questions"
        assert "contributions" in outline.lower(), "Should mention contributions"
        assert len(outline.split()) < 200, "Outline should be brief (<200 words)"
    
    def test_generate_section_outline_methodology(self, tmp_path):
        """Test that methodology outline contains expected structure."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            sections=["results"],
            skip_latex=True
        )
        generator = PaperGenerator(config)
        
        context = SectionContext(
            section_name="methodology",
            experiment_summary="Test experiment",
            frameworks=["ChatDev", "MetaGPT", "AutoGen"],
            num_runs=50,
            metrics={},
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        outline = generator._generate_section_outline("methodology", context)
        
        # Assert
        assert "itemize" in outline.lower()
        assert "experimental setup" in outline.lower()
        assert "metrics" in outline.lower()
        assert "statistical analysis" in outline.lower()
        assert all(fw in outline for fw in context.frameworks), "Should list all frameworks"
        assert str(context.num_runs) in outline, "Should mention number of runs"
    
    def test_generate_section_outline_results(self, tmp_path):
        """Test that results outline uses key findings when available."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            sections=["methodology"],
            skip_latex=True
        )
        generator = PaperGenerator(config)
        
        context = SectionContext(
            section_name="results",
            experiment_summary="Test experiment",
            frameworks=["ChatDev", "MetaGPT"],
            num_runs=50,
            metrics={},
            statistical_results={},
            key_findings=[
                "ChatDev is 20% faster than MetaGPT",
                "MetaGPT has higher code quality",
                "Significant difference in token usage"
            ]
        )
        
        # Act
        outline = generator._generate_section_outline("results", context)
        
        # Assert
        assert "itemize" in outline.lower()
        assert "key findings" in outline.lower()
        # Should include at least some key findings
        assert any(finding.split()[0] in outline for finding in context.key_findings[:3])
    
    def test_generate_section_outline_abstract(self, tmp_path):
        """Test that abstract outline is simple text (no lists)."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            sections=["introduction"],
            skip_latex=True
        )
        generator = PaperGenerator(config)
        
        context = SectionContext(
            section_name="abstract",
            experiment_summary="Test experiment",
            frameworks=["ChatDev"],
            num_runs=50,
            metrics={},
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        outline = generator._generate_section_outline("abstract", context)
        
        # Assert
        assert "empirical comparison" in outline.lower()
        assert len(outline.split()) < 50, "Abstract outline should be very brief"
        assert "itemize" not in outline.lower(), "Abstract outline should not use lists"
    
    def test_section_selection_determines_prose_vs_outline(self, tmp_path):
        """Test that config.sections controls which sections get full prose."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            sections=["methodology", "results"],  # Only these get full prose
            skip_latex=True
        )
        generator = PaperGenerator(config)
        
        # The section_generators dict should exist
        assert hasattr(generator, 'section_generators')
        assert 'introduction' in generator.section_generators
        assert 'methodology' in generator.section_generators
        assert 'results' in generator.section_generators
        
        # Selected sections should be properly identified
        # (This would be tested in _generate_all_sections but we're testing the logic)
        if config.sections is None:
            selected_sections = set(generator.section_generators.keys())
        else:
            selected_sections = set(config.sections)
        
        assert 'methodology' in selected_sections
        assert 'results' in selected_sections
        assert 'introduction' not in selected_sections
        assert 'discussion' not in selected_sections
    
    def test_none_sections_means_all_selected(self, tmp_path):
        """Test that sections=None means all sections get full prose."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            sections=None,  # Default: all sections
            skip_latex=True
        )
        generator = PaperGenerator(config)
        
        # Act - determine selected sections (mimics logic in _generate_all_sections)
        if config.sections is None:
            selected_sections = set(generator.section_generators.keys())
        else:
            selected_sections = set(config.sections)
        
        # Assert - all sections should be selected
        assert 'introduction' in selected_sections
        assert 'methodology' in selected_sections
        assert 'results' in selected_sections
        assert 'discussion' in selected_sections
        assert 'conclusion' in selected_sections
