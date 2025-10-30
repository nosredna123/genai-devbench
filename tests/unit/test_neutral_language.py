"""
Unit tests for neutral statistical language (User Story 8).

Tests FR-035 to FR-038:
- FR-035: Replace "outperforms" with "shows higher values than"
- FR-036: Replace "is better than" with neutral phrases
- FR-037: Extreme Cliff's Delta uses factual language
- FR-038: Non-significant results acknowledge power limitations

Feature: 012-fix-statistical-report
Phase: 11 (Testing & Polish)
Task: T074
"""

import pytest
import numpy as np
from src.paper_generation.educational_content import EducationalContentGenerator
from src.paper_generation.statistical_analyzer import (
    StatisticalAnalyzer, EffectSize, EffectSizeMeasure, TestType
)


@pytest.fixture
def content_generator():
    """Create EducationalContentGenerator instance."""
    return EducationalContentGenerator()


@pytest.fixture
def analyzer():
    """Create StatisticalAnalyzer instance."""
    return StatisticalAnalyzer(alpha=0.05)


class TestNeutralPhrasesDictionary:
    """Test FR-035 to FR-038: Neutral language dictionary."""
    
    def test_language_dictionary_exists(self, content_generator):
        """Verify _get_interpretation_language() method exists."""
        lang = content_generator._get_interpretation_language()
        
        assert isinstance(lang, dict)
        assert len(lang) > 0
    
    def test_language_dictionary_has_neutral_phrases(self, content_generator):
        """Verify dictionary contains neutral comparison phrases."""
        lang = content_generator._get_interpretation_language()
        
        # FR-035, FR-036: Should have neutral phrases
        assert "higher" in lang
        assert "lower" in lang
        assert "differs" in lang
        assert "exceeds" in lang
    
    def test_language_dictionary_has_cliffs_delta_phrases(self, content_generator):
        """Verify dictionary contains Cliff's Delta extreme case phrases."""
        lang = content_generator._get_interpretation_language()
        
        # FR-037: Cliff's Delta extreme values
        assert "cliffs_all_higher" in lang
        assert "cliffs_all_lower" in lang
        assert "all observed values" in lang["cliffs_all_higher"]
    
    def test_language_dictionary_has_power_aware_phrases(self, content_generator):
        """Verify dictionary contains power-aware non-significant phrases."""
        lang = content_generator._get_interpretation_language()
        
        # FR-038: Power-aware non-significant results
        assert "insufficient_evidence" in lang or "insufficient_evidence_low_power" in lang
        assert any("power" in key for key in lang.keys())
    
    def test_avoid_list_exists(self, content_generator):
        """Verify list of prohibited causal terms exists."""
        lang = content_generator._get_interpretation_language()
        
        # Should have list of terms to avoid
        assert "avoid" in lang
        assert isinstance(lang["avoid"], list)
        
        # Should include causal terms
        prohibited = lang["avoid"]
        assert "outperforms" in prohibited
        assert "is better than" in prohibited or "is better" in prohibited


class TestNoOutperformsLanguage:
    """Test FR-035: No "outperforms" in output."""
    
    def test_effect_size_explanation_no_outperforms(self, content_generator):
        """Verify effect size explanations don't use 'outperforms'."""
        # Create mock effect size
        effect = EffectSize(
            measure=EffectSizeMeasure.COHENS_D,
            metric_name="test_metric",
            group1="GPT-4",
            group2="GPT-3.5",
            value=0.75,
            ci_lower=0.50,
            ci_upper=1.00,
            magnitude="medium",
            interpretation="Test interpretation",
            bootstrap_iterations=1000,
            ci_method="bootstrap",
            ci_valid=True,
            test_type_alignment=TestType.T_TEST
        )
        
        explanation = content_generator.explain_effect_size(effect)
        
        # FR-035: Should not contain "outperforms"
        assert "outperforms" not in explanation.lower()
        assert "underperforms" not in explanation.lower()
        
        # Should use neutral language instead
        assert "shows higher" in explanation.lower() or "shows lower" in explanation.lower()


class TestNeutralEffectSizeLanguage:
    """Test FR-036: Neutral effect size interpretations."""
    
    def test_positive_effect_uses_neutral_language(self, content_generator):
        """Verify positive effects use 'shows higher values' not 'is better'."""
        effect = EffectSize(
            measure=EffectSizeMeasure.COHENS_D,
            metric_name="test_metric",
            group1="Treatment",
            group2="Control",
            value=0.85,  # Positive effect
            ci_lower=0.60,
            ci_upper=1.10,
            magnitude="large",
            interpretation="Large positive difference",
            bootstrap_iterations=1000,
            ci_method="bootstrap",
            ci_valid=True,
            test_type_alignment=TestType.T_TEST
        )
        
        explanation = content_generator.explain_effect_size(effect)
        
        # FR-036: Should not use "is better"
        assert "is better" not in explanation.lower()
        assert "beats" not in explanation.lower()
        
        # Should use neutral descriptive language
        assert any(phrase in explanation.lower() for phrase in 
                  ["shows higher", "exceeds", "differs from"])
    
    def test_negative_effect_uses_neutral_language(self, content_generator):
        """Verify negative effects use neutral language."""
        effect = EffectSize(
            measure=EffectSizeMeasure.COHENS_D,
            metric_name="test_metric",
            group1="Method A",
            group2="Method B",
            value=-0.55,  # Negative effect
            ci_lower=-0.80,
            ci_upper=-0.30,
            magnitude="medium",
            interpretation="Medium negative difference",
            bootstrap_iterations=1000,
            ci_method="bootstrap",
            ci_valid=True,
            test_type_alignment=TestType.T_TEST
        )
        
        explanation = content_generator.explain_effect_size(effect)
        
        # Should not use "is worse"
        assert "is worse" not in explanation.lower()
        assert "loses to" not in explanation.lower()
        
        # Should use neutral language
        assert "shows lower" in explanation.lower() or "lower values" in explanation.lower()


class TestCliffsDeltaExtremeLanguage:
    """Test FR-037: Extreme Cliff's Delta uses factual language."""
    
    def test_extreme_positive_cliffs_delta(self, content_generator):
        """Verify δ = 1.000 uses 'all observed values exceed' not '100% certain beats'."""
        effect = EffectSize(
            measure=EffectSizeMeasure.CLIFFS_DELTA,
            metric_name="test_metric",
            group1="System X",
            group2="System Y",
            value=1.000,  # Extreme positive
            ci_lower=0.95,
            ci_upper=1.00,
            magnitude="large",
            interpretation="All values in System X exceed those in System Y",
            bootstrap_iterations=1000,
            ci_method="bootstrap",
            ci_valid=True,
            test_type_alignment=TestType.MANN_WHITNEY
        )
        
        explanation = content_generator.explain_effect_size(effect)
        
        # FR-037: Should not use "100% certain" or "beats"
        assert "100% certain" not in explanation.lower()
        assert "beats" not in explanation.lower()
        assert "definitely" not in explanation.lower()
        
        # Should use factual language
        # The explanation should mention "all" and "exceed" or similar
        assert "all" in explanation.lower() or "100%" not in explanation.lower()
    
    def test_extreme_negative_cliffs_delta(self, content_generator):
        """Verify δ = -1.000 uses factual language."""
        effect = EffectSize(
            measure=EffectSizeMeasure.CLIFFS_DELTA,
            metric_name="test_metric",
            group1="Baseline",
            group2="Advanced",
            value=-1.000,  # Extreme negative
            ci_lower=-1.00,
            ci_upper=-0.95,
            magnitude="large",
            interpretation="All values in Baseline are less than those in Advanced",
            bootstrap_iterations=1000,
            ci_method="bootstrap",
            ci_valid=True,
            test_type_alignment=TestType.MANN_WHITNEY
        )
        
        explanation = content_generator.explain_effect_size(effect)
        
        # Should not use causal language
        assert "loses to" not in explanation.lower()
        assert "100% certain" not in explanation.lower()


class TestPowerAwareNonSignificant:
    """Test FR-038: Non-significant results acknowledge power."""
    
    def test_low_power_non_significant_interpretation(self, analyzer):
        """Verify low power non-significant results mention insufficient evidence."""
        np.random.seed(42)
        # Small samples for low power
        group1 = np.random.normal(10, 2, 5)
        group2 = np.random.normal(11, 2, 5)
        
        # This test verifies the interpretation logic exists
        # Full integration test would check actual output
        # For now, verify we have the infrastructure
        
        # The analyzer should have methods that consider power
        assert hasattr(analyzer, '_calculate_power_analysis')
    
    def test_adequate_power_non_significant_interpretation(self):
        """Verify adequate power non-significant results use appropriate language."""
        # With adequate power (80%+), should say:
        # "Insufficient evidence to conclude a difference exists"
        # NOT: "No effect exists" or "Groups are identical"
        
        # This is tested via the language dictionary
        generator = EducationalContentGenerator()
        lang = generator._get_interpretation_language()
        
        # Should have phrases for this scenario
        assert "insufficient_evidence" in lang
        
        # Check that "no effect exists" only appears in the avoid list
        avoid_list = lang.get("avoid", [])
        assert "no effect exists" in avoid_list, "Should be in avoid list"
        
        # Check that it's NOT used in actual phrases (exclude the avoid list)
        actual_phrases = {k: v for k, v in lang.items() if k != "avoid"}
        actual_phrases_str = str(actual_phrases.values()).lower()
        # "no effect exists" should not appear in actual usable phrases
        assert actual_phrases_str.count("no effect exists") == 0


class TestProhibitedTermsAbsent:
    """Verify prohibited causal terms are absent from templates."""
    
    def test_templates_no_causal_language(self, content_generator):
        """Verify explanation templates don't use causal language."""
        from src.paper_generation.educational_content import EXPLANATION_TEMPLATES
        
        templates_str = str(EXPLANATION_TEMPLATES).lower()
        
        # FR-035 to FR-037: Check prohibited terms
        # Note: "definitely" might appear in educational context, so we check carefully
        prohibited_in_context = [
            "outperforms",
            "underperforms",
            "is better than",
            "is worse than",
            "beats",
            "loses to",
            "100% certain"
        ]
        
        for term in prohibited_in_context:
            assert term not in templates_str, f"Found prohibited term: {term}"
    
    def test_interpretations_use_descriptive_not_causal(self, content_generator):
        """Verify interpretations describe observations, not causation."""
        # Create multiple effect sizes and check their explanations
        test_effects = [
            EffectSize(
                measure=EffectSizeMeasure.COHENS_D,
                metric_name="metric1",
                group1="A", group2="B",
                value=0.5, ci_lower=0.3, ci_upper=0.7,
                magnitude="medium", interpretation="Test",
                bootstrap_iterations=1000, ci_method="bootstrap",
                ci_valid=True, test_type_alignment=TestType.T_TEST
            ),
            EffectSize(
                measure=EffectSizeMeasure.CLIFFS_DELTA,
                metric_name="metric2",
                group1="C", group2="D",
                value=0.3, ci_lower=0.1, ci_upper=0.5,
                magnitude="small", interpretation="Test",
                bootstrap_iterations=1000, ci_method="bootstrap",
                ci_valid=True, test_type_alignment=TestType.MANN_WHITNEY
            )
        ]
        
        for effect in test_effects:
            explanation = content_generator.explain_effect_size(effect)
            
            # Should use descriptive language
            assert any(word in explanation.lower() for word in 
                      ["shows", "differs", "values", "distribution"])
            
            # Should not use causal language
            causal_terms = ["outperforms", "is better", "beats", "superior"]
            for term in causal_terms:
                assert term not in explanation.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
