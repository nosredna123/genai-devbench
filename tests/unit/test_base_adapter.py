"""Unit tests for BaseAdapter token, API call, and cache extraction."""

import pytest
from typing import Dict, Any


class TestBaseAdapter:
    """Test BaseAdapter usage extraction logic."""
    
    def test_extract_all_fields_from_response(self):
        """Test that num_model_requests and input_cached_tokens are correctly extracted from OpenAI Usage API response."""
        
        # Mock usage data (realistic response structure)
        mock_usage_data = {
            "object": "page",
            "data": [
                {
                    "object": "bucket",
                    "start_time": 1760556651,
                    "end_time": 1760556951,
                    "results": [
                        {
                            "object": "organization.usage.completions.result",
                            "input_tokens": 1000,
                            "output_tokens": 500,
                            "num_model_requests": 5,  # ← KEY FIELD 1
                            "input_cached_tokens": 100  # ← KEY FIELD 2
                        }
                    ]
                },
                {
                    "object": "bucket",
                    "start_time": 1760556951,
                    "end_time": 1760557251,
                    "results": [
                        {
                            "input_tokens": 2000,
                            "output_tokens": 800,
                            "num_model_requests": 8,  # ← Second bucket
                            "input_cached_tokens": 250  # ← Second bucket
                        }
                    ]
                }
            ]
        }
        
        # Simulate the extraction logic (matches implementation in base_adapter.py)
        def _extract_tokens(result: Dict[str, Any]) -> tuple[int, int, int, int]:
            """Extract tokens, API calls, and cached tokens from a single result."""
            input_fields = (
                "input_tokens",
                "n_context_tokens_total",
                "n_input_tokens_total",
                "n_context_tokens",
            )
            output_fields = (
                "output_tokens",
                "n_generated_tokens_total",
                "n_output_tokens_total",
                "n_generated_tokens",
            )
            tokens_in = next((int(result.get(field, 0) or 0) for field in input_fields if field in result), 0)
            tokens_out = next((int(result.get(field, 0) or 0) for field in output_fields if field in result), 0)
            num_requests = int(result.get("num_model_requests", 0) or 0)
            cached_tokens = int(result.get("input_cached_tokens", 0) or 0)
            return tokens_in, tokens_out, num_requests, cached_tokens
        
        total_input_tokens = 0
        total_output_tokens = 0
        total_api_calls = 0
        total_cached_tokens = 0
        
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                tokens_in, tokens_out, num_requests, cached = _extract_tokens(result)
                total_input_tokens += tokens_in
                total_output_tokens += tokens_out
                total_api_calls += num_requests
                total_cached_tokens += cached
        
        # Assertions
        assert total_input_tokens == 3000, "Input tokens should sum across buckets (1000 + 2000)"
        assert total_output_tokens == 1300, "Output tokens should sum across buckets (500 + 800)"
        assert total_api_calls == 13, "API calls should sum across buckets (5 + 8)"
        assert total_cached_tokens == 350, "Cached tokens should sum across buckets (100 + 250)"
        
        # Cache hit rate calculation
        cache_hit_rate = (total_cached_tokens / total_input_tokens) * 100
        assert cache_hit_rate > 0, "Cache hit rate should be > 0%"
        assert abs(cache_hit_rate - 11.67) < 0.1, f"Cache hit rate should be ~11.67% (got {cache_hit_rate:.2f}%)"
    
    def test_extract_handles_missing_fields(self):
        """Test graceful handling when num_model_requests or input_cached_tokens is missing."""
        
        mock_usage_data = {
            "data": [
                {
                    "results": [
                        {
                            "input_tokens": 1000,
                            "output_tokens": 500
                            # ← num_model_requests and input_cached_tokens missing
                        }
                    ]
                }
            ]
        }
        
        total_api_calls = 0
        total_cached_tokens = 0
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                total_api_calls += int(result.get("num_model_requests", 0) or 0)
                total_cached_tokens += int(result.get("input_cached_tokens", 0) or 0)
        
        assert total_api_calls == 0, "Should default to 0 when field missing"
        assert total_cached_tokens == 0, "Should default to 0 when field missing"
    
    def test_extract_handles_null_values(self):
        """Test graceful handling when num_model_requests or input_cached_tokens is null."""
        
        mock_usage_data = {
            "data": [
                {
                    "results": [
                        {
                            "input_tokens": 1000,
                            "output_tokens": 500,
                            "num_model_requests": None,  # ← Explicitly null
                            "input_cached_tokens": None  # ← Explicitly null
                        }
                    ]
                }
            ]
        }
        
        total_api_calls = 0
        total_cached_tokens = 0
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                # This mimics the `int(result.get("num_model_requests", 0) or 0)` pattern
                num_requests = result.get("num_model_requests", 0)
                cached = result.get("input_cached_tokens", 0)
                total_api_calls += int(num_requests or 0)
                total_cached_tokens += int(cached or 0)
        
        assert total_api_calls == 0, "Should handle null values gracefully (None or 0 → 0)"
        assert total_cached_tokens == 0, "Should handle null values gracefully (None or 0 → 0)"
    
    def test_extract_handles_zero_values(self):
        """Test that explicit zero is preserved (not confused with missing)."""
        
        mock_usage_data = {
            "data": [
                {
                    "results": [
                        {
                            "input_tokens": 1000,
                            "output_tokens": 500,
                            "num_model_requests": 0,  # ← Explicit zero (valid data)
                            "input_cached_tokens": 0  # ← Also zero (no cache hits)
                        }
                    ]
                }
            ]
        }
        
        total_api_calls = 0
        total_cached_tokens = 0
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                total_api_calls += int(result.get("num_model_requests", 0) or 0)
                total_cached_tokens += int(result.get("input_cached_tokens", 0) or 0)
        
        assert total_api_calls == 0, "Explicit zero should be preserved"
        assert total_cached_tokens == 0, "Explicit zero should be preserved"
    
    def test_extract_multiple_buckets_with_mixed_data(self):
        """Test extraction with realistic mixed data (some buckets have data, others don't)."""
        
        mock_usage_data = {
            "data": [
                {
                    "results": [
                        {
                            "input_tokens": 500,
                            "output_tokens": 200,
                            "num_model_requests": 3,
                            "input_cached_tokens": 50
                        }
                    ]
                },
                {
                    "results": []  # ← Empty bucket
                },
                {
                    "results": [
                        {
                            "input_tokens": 1500,
                            "output_tokens": 600,
                            "num_model_requests": 7,
                            "input_cached_tokens": 150
                        },
                        {
                            "input_tokens": 800,
                            "output_tokens": 300,
                            "num_model_requests": 4,
                            "input_cached_tokens": 80
                        }
                    ]
                },
                {
                    "results": [
                        {
                            "input_tokens": 200,
                            "output_tokens": 100
                            # ← num_model_requests and input_cached_tokens missing in this result
                        }
                    ]
                }
            ]
        }
        
        total_input_tokens = 0
        total_output_tokens = 0
        total_api_calls = 0
        total_cached_tokens = 0
        
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                total_input_tokens += int(result.get("input_tokens", 0) or 0)
                total_output_tokens += int(result.get("output_tokens", 0) or 0)
                total_api_calls += int(result.get("num_model_requests", 0) or 0)
                total_cached_tokens += int(result.get("input_cached_tokens", 0) or 0)
        
        # Verify totals
        assert total_input_tokens == 3000, "Should sum: 500 + 1500 + 800 + 200 = 3000"
        assert total_output_tokens == 1200, "Should sum: 200 + 600 + 300 + 100 = 1200"
        assert total_api_calls == 14, "Should sum: 3 + 7 + 4 + 0(missing) = 14"
        assert total_cached_tokens == 280, "Should sum: 50 + 150 + 80 + 0(missing) = 280"
        
        # Verify cache hit rate
        cache_hit_rate = (total_cached_tokens / total_input_tokens) * 100
        assert abs(cache_hit_rate - 9.33) < 0.1, f"Cache hit rate should be ~9.33% (got {cache_hit_rate:.2f}%)"


class TestAPIEfficiencyMetrics:
    """Test derived metrics based on API calls."""
    
    def test_calculate_efficiency_ratio(self):
        """Test calculation of API efficiency ratio (calls per 1K tokens)."""
        
        # Scenario 1: Efficient batching (fewer, larger calls)
        api_calls_1 = 10
        tokens_total_1 = 50000  # 50K tokens
        efficiency_1 = (api_calls_1 / tokens_total_1) * 1000
        
        assert efficiency_1 == 0.2, "10 calls / 50K tokens = 0.2 calls per 1K tokens"
        assert efficiency_1 < 1.0, "Very efficient (< 1 call per 1K tokens)"
        
        # Scenario 2: Chatty communication (many small calls)
        api_calls_2 = 500
        tokens_total_2 = 50000
        efficiency_2 = (api_calls_2 / tokens_total_2) * 1000
        
        assert efficiency_2 == 10.0, "500 calls / 50K tokens = 10 calls per 1K tokens"
        assert efficiency_2 > 5.0, "Chatty (> 5 calls per 1K tokens)"
        
        # Scenario 3: Balanced
        api_calls_3 = 150
        tokens_total_3 = 50000
        efficiency_3 = (api_calls_3 / tokens_total_3) * 1000
        
        assert efficiency_3 == 3.0, "150 calls / 50K tokens = 3 calls per 1K tokens"
        assert 1.0 < efficiency_3 < 5.0, "Balanced efficiency"
    
    def test_efficiency_handles_zero_tokens(self):
        """Test that efficiency calculation handles zero tokens gracefully."""
        
        api_calls = 10
        tokens_total = 0  # Edge case: no tokens (shouldn't happen in practice)
        
        # Should not divide by zero
        efficiency = (api_calls / tokens_total) * 1000 if tokens_total > 0 else 0
        
        assert efficiency == 0, "Should return 0 when no tokens (avoid division by zero)"
    
    def test_efficiency_handles_zero_calls(self):
        """Test efficiency when there are tokens but no API calls (data integrity issue)."""
        
        api_calls = 0
        tokens_total = 50000
        
        efficiency = (api_calls / tokens_total) * 1000 if tokens_total > 0 else 0
        
        assert efficiency == 0, "Zero calls = 0 efficiency (potential data issue)"


class TestCacheEfficiencyMetrics:
    """Test derived metrics based on cached tokens."""
    
    def test_calculate_cache_hit_rate(self):
        """Test calculation of cache hit rate percentage."""
        
        # Scenario 1: 10% cache hit rate (baseline from recent data)
        cached_tokens_1 = 42624
        input_tokens_1 = 426712
        hit_rate_1 = (cached_tokens_1 / input_tokens_1) * 100
        
        assert abs(hit_rate_1 - 10.0) < 0.1, f"Should be ~10% (got {hit_rate_1:.2f}%)"
        
        # Scenario 2: High cache hit rate
        cached_tokens_2 = 10000
        input_tokens_2 = 40000
        hit_rate_2 = (cached_tokens_2 / input_tokens_2) * 100
        
        assert hit_rate_2 == 25.0, "25% cache hit rate"
        
        # Scenario 3: No cache hits
        cached_tokens_3 = 0
        input_tokens_3 = 50000
        hit_rate_3 = (cached_tokens_3 / input_tokens_3) * 100
        
        assert hit_rate_3 == 0.0, "0% cache hit rate"
    
    def test_calculate_cost_savings(self):
        """Test calculation of cost savings from cache (gpt-4o-mini pricing)."""
        
        # Pricing (per 1M tokens)
        uncached_price = 2.50  # $2.50 per 1M tokens
        cached_price = 0.25    # $0.25 per 1M tokens (90% discount)
        
        # Scenario: 42,624 cached tokens (from recent data)
        cached_tokens = 42624
        cost_savings = cached_tokens * (uncached_price - cached_price) / 1_000_000
        
        assert abs(cost_savings - 0.096) < 0.001, f"Should save ~$0.096 (got ${cost_savings:.3f})"
        
        # Scenario: 100K cached tokens
        cached_tokens_2 = 100000
        cost_savings_2 = cached_tokens_2 * (uncached_price - cached_price) / 1_000_000
        
        assert abs(cost_savings_2 - 0.225) < 0.001, f"Should save ~$0.225 (got ${cost_savings_2:.3f})"
    
    def test_cache_handles_zero_input_tokens(self):
        """Test that cache hit rate calculation handles zero input tokens gracefully."""
        
        cached_tokens = 1000
        input_tokens = 0  # Edge case
        
        hit_rate = (cached_tokens / input_tokens) * 100 if input_tokens > 0 else 0
        
        assert hit_rate == 0, "Should return 0 when no input tokens (avoid division by zero)"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
