"""
Cost calculator for OpenAI API usage.

Calculates USD costs based on token consumption with proper handling
of cached tokens (50% discount) and model-specific pricing.
"""

from typing import Dict
from src.utils.metrics_config import get_metrics_config


class CostCalculator:
    """
    Calculate USD costs for OpenAI API usage with cache discount.
    
    Implements the COST_USD metric calculation:
    - Uncached input tokens: full price
    - Cached input tokens: 50% discount
    - Output tokens: full price (no discount)
    
    Pricing is loaded from the centralized configuration.
    """
    
    def __init__(self, model: str):
        """
        Initialize cost calculator for a specific model.
        
        Args:
            model: OpenAI model name (e.g., 'gpt-4o-mini', 'o1-mini')
            
        Raises:
            ValueError: If model pricing not found in configuration
        """
        self.model = model
        self.config = get_metrics_config()
        
        # Load pricing for this model
        self.pricing = self.config.get_pricing_config(model)
        if self.pricing is None:
            raise ValueError(
                f"Pricing not found for model '{model}'. "
                f"Available models: {self._get_available_models()}"
            )
        
        # Extract pricing components (per million tokens)
        self.input_price = self.pricing['input_price']
        self.cached_price = self.pricing['cached_price']
        self.output_price = self.pricing['output_price']
    
    def _get_available_models(self) -> list:
        """Get list of models with pricing configured."""
        # Get all model names by trying to get pricing for each
        models = ['gpt-4o-mini', 'gpt-4o', 'o1-mini', 'o1-preview']
        available = []
        for model in models:
            if self.config.get_pricing_config(model) is not None:
                available.append(model)
        return available if available else ['gpt-4o-mini']  # Fallback
    
    def calculate_cost(
        self,
        tokens_in: int,
        tokens_out: int,
        cached_tokens: int = 0
    ) -> Dict[str, float]:
        """
        Calculate USD cost for token usage with cache discount.
        
        Formula:
            uncached_input_cost = (tokens_in - cached_tokens) * (input_price / 1M)
            cached_input_cost = cached_tokens * (cached_price / 1M)
            output_cost = tokens_out * (output_price / 1M)
            total_cost = uncached_input_cost + cached_input_cost + output_cost
            cache_savings = cached_tokens * (input_price - cached_price) / 1M
        
        Args:
            tokens_in: Total input tokens (prompt tokens)
            tokens_out: Total output tokens (completion tokens)
            cached_tokens: Input tokens served from cache (default: 0)
            
        Returns:
            Dictionary with cost breakdown:
            {
                'uncached_input_cost': float,  # Cost of non-cached input tokens
                'cached_input_cost': float,    # Cost of cached input tokens
                'output_cost': float,          # Cost of output tokens
                'total_cost': float,           # Total USD cost
                'cache_savings': float,        # USD saved by cache
                'model': str,                  # Model name
                'tokens_in': int,              # Input tokens (for reference)
                'tokens_out': int,             # Output tokens (for reference)
                'cached_tokens': int           # Cached tokens (for reference)
            }
            
        Raises:
            ValueError: If cached_tokens > tokens_in or any value is negative
            
        Examples:
            >>> calc = CostCalculator('gpt-4o-mini')
            >>> result = calc.calculate_cost(
            ...     tokens_in=100000,
            ...     tokens_out=50000,
            ...     cached_tokens=20000
            ... )
            >>> print(f"${result['total_cost']:.4f}")
            $0.0432
        """
        # Validate inputs
        if tokens_in < 0 or tokens_out < 0 or cached_tokens < 0:
            raise ValueError("Token counts cannot be negative")
        
        if cached_tokens > tokens_in:
            raise ValueError(
                f"Cached tokens ({cached_tokens}) cannot exceed "
                f"total input tokens ({tokens_in})"
            )
        
        # Calculate uncached input tokens
        uncached_tokens = tokens_in - cached_tokens
        
        # Calculate costs (pricing is per million tokens)
        uncached_input_cost = (uncached_tokens * self.input_price) / 1_000_000
        cached_input_cost = (cached_tokens * self.cached_price) / 1_000_000
        output_cost = (tokens_out * self.output_price) / 1_000_000
        
        # Total cost
        total_cost = uncached_input_cost + cached_input_cost + output_cost
        
        # Calculate savings from cache (what we would have paid at full price)
        cache_savings = (cached_tokens * (self.input_price - self.cached_price)) / 1_000_000
        
        return {
            'uncached_input_cost': uncached_input_cost,
            'cached_input_cost': cached_input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'cache_savings': cache_savings,
            'model': self.model,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'cached_tokens': cached_tokens
        }
    
    def calculate_step_cost(
        self,
        tokens_in: int,
        tokens_out: int,
        cached_tokens: int = 0
    ) -> float:
        """
        Calculate total cost for a single step (convenience method).
        
        Args:
            tokens_in: Input tokens for this step
            tokens_out: Output tokens for this step
            cached_tokens: Cached input tokens for this step
            
        Returns:
            Total USD cost for this step
        """
        result = self.calculate_cost(tokens_in, tokens_out, cached_tokens)
        return result['total_cost']
    
    def get_model_pricing(self) -> Dict[str, float]:
        """
        Get pricing details for the current model.
        
        Returns:
            Dictionary with input_price, cached_price, output_price
        """
        return {
            'model': self.model,
            'input_price': self.input_price,
            'cached_price': self.cached_price,
            'output_price': self.output_price
        }
    
    def format_cost(self, cost: float) -> str:
        """
        Format cost value for display.
        
        Args:
            cost: Cost in USD
            
        Returns:
            Formatted string (e.g., "$0.1234")
        """
        return f"${cost:.4f}"
    
    def __repr__(self) -> str:
        """String representation of the calculator."""
        return (
            f"CostCalculator(model='{self.model}', "
            f"input=${self.input_price:.3f}/1M, "
            f"cached=${self.cached_price:.3f}/1M, "
            f"output=${self.output_price:.3f}/1M)"
        )
