"""
Unit tests for prose level variations in ProseEngine.

Tests the prompt generation differences for minimal/standard/comprehensive levels.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.paper_generation.prose_engine import ProseEngine
from src.paper_generation.models import PaperConfig, SectionContext


class TestProseLevelVariations:
    """Test prose level impacts on generation."""
    
    def test_minimal_prose_level_word_count_target(self, tmp_path):
        """Test that minimal prose level has lower word count target."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="minimal",
            skip_latex=True,
            figures_only=True  # Skip API key requirement
        )
        engine = ProseEngine(config)
        
        # Act
        word_count = engine._get_word_count_target()
        
        # Assert
        assert word_count == 400, "Minimal should target 400 words"
    
    def test_standard_prose_level_word_count_target(self, tmp_path):
        """Test that standard prose level has medium word count target."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="standard",
            skip_latex=True,
            figures_only=True
        )
        engine = ProseEngine(config)
        
        # Act
        word_count = engine._get_word_count_target()
        
        # Assert
        assert word_count == 800, "Standard should target 800 words"
    
    def test_comprehensive_prose_level_word_count_target(self, tmp_path):
        """Test that comprehensive prose level has higher word count target."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="comprehensive",
            skip_latex=True,
            figures_only=True
        )
        engine = ProseEngine(config)
        
        # Act
        word_count = engine._get_word_count_target()
        
        # Assert
        assert word_count == 1200, "Comprehensive should target 1200 words"
    
    def test_minimal_prose_level_instruction(self, tmp_path):
        """Test that minimal level emphasizes observations over interpretation."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="minimal",
            skip_latex=True,
            figures_only=True
        )
        engine = ProseEngine(config)
        
        # Act
        instruction = engine._get_prose_level_instruction()
        
        # Assert
        assert "concise" in instruction.lower()
        assert "observation" in instruction.lower()
        assert "causal" in instruction.lower()  # Should mention avoiding causal claims
        assert "data shows" in instruction.lower() or "we observe" in instruction.lower()
    
    def test_standard_prose_level_instruction(self, tmp_path):
        """Test that standard level balances observation and interpretation."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="standard",
            skip_latex=True,
            figures_only=True
        )
        engine = ProseEngine(config)
        
        # Act
        instruction = engine._get_prose_level_instruction()
        
        # Assert
        assert "balanced" in instruction.lower()
        assert "observation" in instruction.lower() or "factual" in instruction.lower()
        assert "interpretation" in instruction.lower() or "inference" in instruction.lower()
    
    def test_comprehensive_prose_level_instruction(self, tmp_path):
        """Test that comprehensive level encourages deep analysis."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="comprehensive",
            skip_latex=True,
            figures_only=True
        )
        engine = ProseEngine(config)
        
        # Act
        instruction = engine._get_prose_level_instruction()
        
        # Assert
        assert "thorough" in instruction.lower() or "detailed" in instruction.lower()
        assert "deep" in instruction.lower() or "comprehensive" in instruction.lower()
        assert "implication" in instruction.lower() or "theoretical" in instruction.lower()
    
    def test_prompt_includes_word_count_target(self, tmp_path):
        """Test that generated prompt includes the prose level word count target."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="minimal",
            skip_latex=True,
            figures_only=True
        )
        engine = ProseEngine(config)
        
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
        prompt = engine._build_prompt(context)
        
        # Assert
        assert "400" in prompt, "Minimal level should mention 400 word target"
        assert "AT LEAST" in prompt, "Should emphasize minimum word count"
    
    def test_prompt_includes_prose_level_instruction(self, tmp_path):
        """Test that generated prompt includes prose level specific guidance."""
        # Arrange
        config = PaperConfig(
            experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
            output_dir=tmp_path,
            prose_level="comprehensive",
            skip_latex=True,
            figures_only=True
        )
        engine = ProseEngine(config)
        
        context = SectionContext(
            section_name="methodology",
            experiment_summary="Test experiment",
            frameworks=["ChatDev"],
            num_runs=50,
            metrics={},
            statistical_results={},
            key_findings=[]
        )
        
        # Act
        prompt = engine._build_prompt(context)
        
        # Assert
        assert "thorough" in prompt.lower() or "detailed" in prompt.lower()
        assert "1200" in prompt, "Comprehensive level should mention 1200 word target"
    
    def test_different_prose_levels_generate_different_prompts(self, tmp_path):
        """Test that different prose levels produce different prompts."""
        # Arrange
        context = SectionContext(
            section_name="results",
            experiment_summary="Test experiment",
            frameworks=["ChatDev"],
            num_runs=50,
            metrics={},
            statistical_results={},
            key_findings=[]
        )
        
        configs = {
            "minimal": PaperConfig(
                experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
                output_dir=tmp_path / "minimal",
                prose_level="minimal",
                skip_latex=True,
                figures_only=True
            ),
            "standard": PaperConfig(
                experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
                output_dir=tmp_path / "standard",
                prose_level="standard",
                skip_latex=True,
                figures_only=True
            ),
            "comprehensive": PaperConfig(
                experiment_dir=Path(__file__).parent / "fixtures" / "sample_experiment",
                output_dir=tmp_path / "comprehensive",
                prose_level="comprehensive",
                skip_latex=True,
                figures_only=True
            )
        }
        
        # Act
        prompts = {}
        for level, config in configs.items():
            engine = ProseEngine(config)
            prompts[level] = engine._build_prompt(context)
        
        # Assert - all prompts should be different
        assert prompts["minimal"] != prompts["standard"]
        assert prompts["standard"] != prompts["comprehensive"]
        assert prompts["minimal"] != prompts["comprehensive"]
        
        # Verify word count targets differ
        assert "400" in prompts["minimal"]
        assert "800" in prompts["standard"]
        assert "1200" in prompts["comprehensive"]
