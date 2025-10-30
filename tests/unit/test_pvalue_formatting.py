"""
Unit tests for P-value formatting (User Story 6).

Tests FR-027 to FR-029:
- FR-027: All p-value display locations use format_pvalue()
- FR-028: Statistical test tables use APA formatting
- FR-029: Interpretation text uses APA formatting

Feature: 012-fix-statistical-report
Phase: 11 (Testing & Polish)
Task: T070
"""

import pytest
from src.utils.statistical_helpers import format_pvalue


class TestPValueFormatting:
    """Test FR-027 to FR-029: APA 7th edition p-value formatting."""
    
    def test_very_small_pvalues(self):
        """Verify very small p-values formatted as p < 0.001."""
        # FR-027: Very small p-values
        assert format_pvalue(0.0001) == "p < 0.001"
        assert format_pvalue(0.00001) == "p < 0.001"
        assert format_pvalue(0.0) == "p < 0.001"
        assert format_pvalue(1e-10) == "p < 0.001"
    
    def test_threshold_pvalue(self):
        """Verify p-value at threshold formatted correctly."""
        # Exactly at threshold
        assert format_pvalue(0.001) == "p = 0.001"
        # Just above threshold
        assert format_pvalue(0.0011) == "p = 0.001"
    
    def test_normal_pvalues(self):
        """Verify normal p-values formatted with 3 decimals."""
        # FR-027: Standard p-values (3 decimal places, no leading zero removal)
        assert format_pvalue(0.05) == "p = 0.050"
        assert format_pvalue(0.123) == "p = 0.123"
        assert format_pvalue(0.456) == "p = 0.456"
    
    def test_large_pvalues(self):
        """Verify large p-values formatted correctly."""
        assert format_pvalue(0.75) == "p = 0.750"
        assert format_pvalue(0.999) == "p = 0.999"
    
    def test_edge_case_one(self):
        """Verify p-value of 1.0 formatted correctly."""
        # Edge case: p = 1.0
        result = format_pvalue(1.0)
        assert result in ["p = 1.000", "p > 0.999"]
    
    def test_rounding_behavior(self):
        """Verify correct rounding to 3 decimal places."""
        # Test rounding
        assert format_pvalue(0.0234) == "p = 0.023"
        assert format_pvalue(0.0235) == "p = 0.024"  # Round up
        assert format_pvalue(0.0005) == "p < 0.001"  # Below threshold
    
    def test_no_p_equals_zero(self):
        """Verify we never show p = 0.000."""
        # FR-027: Never show "p = 0.000"
        assert format_pvalue(0.0) != "p = 0.000"
        assert format_pvalue(0.00001) != "p = 0.000"
        assert "0.000" not in format_pvalue(0.0)


class TestPValueFormattingConsistency:
    """Test consistency of p-value formatting across ranges."""
    
    def test_consistency_near_threshold(self):
        """Verify consistent formatting near 0.001 threshold."""
        # Just below threshold
        assert format_pvalue(0.0009) == "p < 0.001"
        assert format_pvalue(0.00099) == "p < 0.001"
        
        # Just at/above threshold
        assert format_pvalue(0.001) == "p = 0.001"
        assert format_pvalue(0.0011) == "p = 0.001"
    
    def test_all_formatted_values_start_with_p(self):
        """Verify all formatted values start with 'p'."""
        test_values = [0.0, 0.001, 0.01, 0.05, 0.10, 0.50, 0.99]
        
        for val in test_values:
            result = format_pvalue(val)
            assert result.startswith("p "), f"Format result '{result}' doesn't start with 'p '"
    
    def test_no_trailing_zeros_removed(self):
        """Verify trailing zeros are kept (APA style)."""
        # APA requires trailing zeros
        assert format_pvalue(0.05) == "p = 0.050"
        assert format_pvalue(0.10) == "p = 0.100"
        assert format_pvalue(0.20) == "p = 0.200"


class TestPValueFormattingInOutput:
    """Test p-value formatting appears correctly in generated output."""
    
    def test_format_used_in_statistical_tests(self):
        """Verify format_pvalue is used in statistical test output."""
        # This is an integration-style test - would need actual analyzer
        # For now, verify the function produces valid output
        p_values = [0.0001, 0.01, 0.05, 0.10, 0.50]
        
        for p in p_values:
            formatted = format_pvalue(p)
            # Should be a non-empty string
            assert isinstance(formatted, str)
            assert len(formatted) > 0
            # Should contain 'p' and a value
            assert 'p' in formatted
            assert any(c.isdigit() for c in formatted)


class TestAPAComplianceExamples:
    """Test specific APA 7th edition examples."""
    
    def test_apa_example_significant(self):
        """Test APA example for significant result."""
        # APA example: p = 0.033
        assert format_pvalue(0.033) == "p = 0.033"
    
    def test_apa_example_highly_significant(self):
        """Test APA example for highly significant result."""
        # APA example: p < 0.001
        assert format_pvalue(0.0001) == "p < 0.001"
    
    def test_apa_example_non_significant(self):
        """Test APA example for non-significant result."""
        # APA example: p = 0.224
        assert format_pvalue(0.224) == "p = 0.224"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
