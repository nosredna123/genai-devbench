"""
Unit tests for CostCalculator class.

Tests cost calculation with OpenAI pricing and cache discounts.
"""

import pytest
from src.utils.cost_calculator import CostCalculator


class TestCostCalculatorInitialization:
    """Tests for CostCalculator initialization."""
    
    def test_init_with_valid_model(self):
        """Test initialization with a valid model."""
        calc = CostCalculator('gpt-4o-mini')
        assert calc.model == 'gpt-4o-mini'
        assert calc.input_price == 0.150
        assert calc.cached_price == 0.075
        assert calc.output_price == 0.600
    
    def test_init_with_gpt4o(self):
        """Test initialization with gpt-4o model."""
        calc = CostCalculator('gpt-4o')
        assert calc.model == 'gpt-4o'
        assert calc.input_price == 2.500
        assert calc.cached_price == 1.250
        assert calc.output_price == 10.000
    
    def test_init_with_o1_mini(self):
        """Test initialization with o1-mini model."""
        calc = CostCalculator('o1-mini')
        assert calc.model == 'o1-mini'
        assert calc.input_price == 3.000
        assert calc.cached_price == 1.500
        assert calc.output_price == 12.000
    
    def test_init_with_o1_preview(self):
        """Test initialization with o1-preview model."""
        calc = CostCalculator('o1-preview')
        assert calc.model == 'o1-preview'
        assert calc.input_price == 15.000
        assert calc.cached_price == 7.500
        assert calc.output_price == 60.000
    
    def test_init_with_invalid_model(self):
        """Test initialization with nonexistent model raises error."""
        with pytest.raises(ValueError, match="Pricing not found"):
            CostCalculator('nonexistent-model')


class TestCostCalculation:
    """Tests for cost calculation methods."""
    
    def test_calculate_cost_no_cache(self):
        """Test cost calculation without any cache."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=50000,
            cached_tokens=0
        )
        
        # Verify structure
        assert 'uncached_input_cost' in result
        assert 'cached_input_cost' in result
        assert 'output_cost' in result
        assert 'total_cost' in result
        assert 'cache_savings' in result
        
        # Verify values
        # Input: 100,000 * $0.150 / 1M = $0.015
        assert result['uncached_input_cost'] == pytest.approx(0.015, abs=1e-6)
        # Cached: 0 * $0.075 / 1M = $0.000
        assert result['cached_input_cost'] == pytest.approx(0.000, abs=1e-6)
        # Output: 50,000 * $0.600 / 1M = $0.030
        assert result['output_cost'] == pytest.approx(0.030, abs=1e-6)
        # Total: $0.015 + $0.000 + $0.030 = $0.045
        assert result['total_cost'] == pytest.approx(0.045, abs=1e-6)
        # Savings: 0
        assert result['cache_savings'] == pytest.approx(0.000, abs=1e-6)
    
    def test_calculate_cost_with_cache(self):
        """Test cost calculation with cached tokens."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=50000,
            cached_tokens=20000
        )
        
        # Uncached: 80,000 * $0.150 / 1M = $0.012
        assert result['uncached_input_cost'] == pytest.approx(0.012, abs=1e-6)
        # Cached: 20,000 * $0.075 / 1M = $0.0015
        assert result['cached_input_cost'] == pytest.approx(0.0015, abs=1e-6)
        # Output: 50,000 * $0.600 / 1M = $0.030
        assert result['output_cost'] == pytest.approx(0.030, abs=1e-6)
        # Total: $0.012 + $0.0015 + $0.030 = $0.0435
        assert result['total_cost'] == pytest.approx(0.0435, abs=1e-6)
        # Savings: 20,000 * ($0.150 - $0.075) / 1M = $0.0015
        assert result['cache_savings'] == pytest.approx(0.0015, abs=1e-6)
    
    def test_calculate_cost_all_cached(self):
        """Test cost calculation when all input tokens from cache."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=50000,
            cached_tokens=100000
        )
        
        # Uncached: 0 * $0.150 / 1M = $0.000
        assert result['uncached_input_cost'] == pytest.approx(0.000, abs=1e-6)
        # Cached: 100,000 * $0.075 / 1M = $0.0075
        assert result['cached_input_cost'] == pytest.approx(0.0075, abs=1e-6)
        # Output: 50,000 * $0.600 / 1M = $0.030
        assert result['output_cost'] == pytest.approx(0.030, abs=1e-6)
        # Total: $0.000 + $0.0075 + $0.030 = $0.0375
        assert result['total_cost'] == pytest.approx(0.0375, abs=1e-6)
        # Savings: 100,000 * ($0.150 - $0.075) / 1M = $0.0075
        assert result['cache_savings'] == pytest.approx(0.0075, abs=1e-6)
    
    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=0,
            tokens_out=0,
            cached_tokens=0
        )
        
        assert result['uncached_input_cost'] == 0.0
        assert result['cached_input_cost'] == 0.0
        assert result['output_cost'] == 0.0
        assert result['total_cost'] == 0.0
        assert result['cache_savings'] == 0.0
    
    def test_calculate_cost_large_values(self):
        """Test cost calculation with large token counts."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=10_000_000,  # 10 million
            tokens_out=5_000_000,   # 5 million
            cached_tokens=2_000_000  # 2 million
        )
        
        # Uncached: 8M * $0.150 / 1M = $1.200
        assert result['uncached_input_cost'] == pytest.approx(1.200, abs=1e-6)
        # Cached: 2M * $0.075 / 1M = $0.150
        assert result['cached_input_cost'] == pytest.approx(0.150, abs=1e-6)
        # Output: 5M * $0.600 / 1M = $3.000
        assert result['output_cost'] == pytest.approx(3.000, abs=1e-6)
        # Total: $4.350
        assert result['total_cost'] == pytest.approx(4.350, abs=1e-6)
        # Savings: 2M * $0.075 / 1M = $0.150
        assert result['cache_savings'] == pytest.approx(0.150, abs=1e-6)
    
    def test_calculate_cost_different_model(self):
        """Test cost calculation with more expensive model."""
        calc = CostCalculator('o1-preview')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=50000,
            cached_tokens=20000
        )
        
        # Uncached: 80,000 * $15.000 / 1M = $1.200
        assert result['uncached_input_cost'] == pytest.approx(1.200, abs=1e-6)
        # Cached: 20,000 * $7.500 / 1M = $0.150
        assert result['cached_input_cost'] == pytest.approx(0.150, abs=1e-6)
        # Output: 50,000 * $60.000 / 1M = $3.000
        assert result['output_cost'] == pytest.approx(3.000, abs=1e-6)
        # Total: $4.350
        assert result['total_cost'] == pytest.approx(4.350, abs=1e-6)
        # Savings: 20,000 * ($15.000 - $7.500) / 1M = $0.150
        assert result['cache_savings'] == pytest.approx(0.150, abs=1e-6)
    
    def test_calculate_cost_metadata(self):
        """Test that result includes metadata fields."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=50000,
            cached_tokens=20000
        )
        
        assert result['model'] == 'gpt-4o-mini'
        assert result['tokens_in'] == 100000
        assert result['tokens_out'] == 50000
        assert result['cached_tokens'] == 20000


class TestCostCalculationValidation:
    """Tests for input validation."""
    
    def test_negative_tokens_in(self):
        """Test that negative input tokens raises error."""
        calc = CostCalculator('gpt-4o-mini')
        with pytest.raises(ValueError, match="cannot be negative"):
            calc.calculate_cost(tokens_in=-100, tokens_out=50)
    
    def test_negative_tokens_out(self):
        """Test that negative output tokens raises error."""
        calc = CostCalculator('gpt-4o-mini')
        with pytest.raises(ValueError, match="cannot be negative"):
            calc.calculate_cost(tokens_in=100, tokens_out=-50)
    
    def test_negative_cached_tokens(self):
        """Test that negative cached tokens raises error."""
        calc = CostCalculator('gpt-4o-mini')
        with pytest.raises(ValueError, match="cannot be negative"):
            calc.calculate_cost(tokens_in=100, tokens_out=50, cached_tokens=-20)
    
    def test_cached_exceeds_input(self):
        """Test that cached > input raises error."""
        calc = CostCalculator('gpt-4o-mini')
        with pytest.raises(ValueError, match="cannot exceed"):
            calc.calculate_cost(tokens_in=100, tokens_out=50, cached_tokens=200)


class TestConvenienceMethods:
    """Tests for convenience methods."""
    
    def test_calculate_step_cost(self):
        """Test calculate_step_cost convenience method."""
        calc = CostCalculator('gpt-4o-mini')
        cost = calc.calculate_step_cost(
            tokens_in=100000,
            tokens_out=50000,
            cached_tokens=20000
        )
        
        # Should return just the total cost
        assert cost == pytest.approx(0.0435, abs=1e-6)
    
    def test_get_model_pricing(self):
        """Test get_model_pricing returns pricing details."""
        calc = CostCalculator('gpt-4o-mini')
        pricing = calc.get_model_pricing()
        
        assert pricing['model'] == 'gpt-4o-mini'
        assert pricing['input_price'] == 0.150
        assert pricing['cached_price'] == 0.075
        assert pricing['output_price'] == 0.600
    
    def test_format_cost(self):
        """Test cost formatting."""
        calc = CostCalculator('gpt-4o-mini')
        
        assert calc.format_cost(0.1234) == '$0.1234'
        assert calc.format_cost(1.2345) == '$1.2345'
        assert calc.format_cost(0.0001) == '$0.0001'
    
    def test_repr(self):
        """Test string representation."""
        calc = CostCalculator('gpt-4o-mini')
        repr_str = repr(calc)
        
        assert 'CostCalculator' in repr_str
        assert 'gpt-4o-mini' in repr_str
        assert '0.150' in repr_str
        assert '0.075' in repr_str
        assert '0.600' in repr_str


class TestCacheDiscountCalculation:
    """Tests specifically for cache discount logic."""
    
    def test_cache_discount_is_50_percent(self):
        """Verify cache discount is exactly 50%."""
        calc = CostCalculator('gpt-4o-mini')
        
        # Cache price should be exactly 50% of input price
        assert calc.cached_price == calc.input_price * 0.5
    
    def test_cache_savings_calculation(self):
        """Test cache savings calculation logic."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=0,
            cached_tokens=50000
        )
        
        # Savings should be: cached * (full_price - discount_price) / 1M
        expected_savings = 50000 * (0.150 - 0.075) / 1_000_000
        assert result['cache_savings'] == pytest.approx(expected_savings, abs=1e-6)
    
    def test_no_cache_no_savings(self):
        """Test that no cache means no savings."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=50000,
            cached_tokens=0
        )
        
        assert result['cache_savings'] == 0.0
    
    def test_100_percent_cache_maximum_savings(self):
        """Test maximum savings when all tokens cached."""
        calc = CostCalculator('gpt-4o-mini')
        result = calc.calculate_cost(
            tokens_in=100000,
            tokens_out=0,
            cached_tokens=100000
        )
        
        # Maximum savings: all tokens at 50% discount
        expected_savings = 100000 * (0.150 - 0.075) / 1_000_000
        assert result['cache_savings'] == pytest.approx(expected_savings, abs=1e-6)
