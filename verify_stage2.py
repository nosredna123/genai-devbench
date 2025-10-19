#!/usr/bin/env python3
"""
Stage 2 Integration Verification

Verifies that CostCalculator is properly integrated into MetricsCollector
and that costs are calculated correctly.
"""

import sys
from src.utils.cost_calculator import CostCalculator
from src.orchestrator.metrics_collector import MetricsCollector

def test_cost_calculator():
    """Test CostCalculator directly"""
    print("=" * 60)
    print("Testing CostCalculator")
    print("=" * 60)
    
    # Test with gpt-4o-mini
    calc = CostCalculator(model='gpt-4o-mini')
    
    # Test case: 10k input (5k cached), 2k output
    result = calc.calculate_cost(
        tokens_in=10000,
        tokens_out=2000,
        cached_tokens=5000
    )
    
    print(f"✓ Model: {calc.model}")
    print("✓ Input tokens: 10,000")
    print("✓ Cached tokens: 5,000 (50% cache hit rate)")
    print("✓ Output tokens: 2,000")
    print(f"✓ Total cost: ${result['total_cost']:.6f}")
    print("✓ Breakdown:")
    print(f"  - Uncached input: ${result['uncached_input_cost']:.6f}")
    print(f"  - Cached input: ${result['cached_input_cost']:.6f}")
    print(f"  - Output: ${result['output_cost']:.6f}")
    print(f"  - Cache savings: ${result['cache_savings']:.6f}")
    
    # Expected calculation:
    # Uncached input: (10k - 5k) * $0.150/1M = 5000 * 0.00000015 = $0.00075
    # Cached input: 5k * $0.075/1M = 5000 * 0.000000075 = $0.000375
    # Output: 2k * $0.600/1M = 2000 * 0.0000006 = $0.0012
    # Total: $0.00075 + $0.000375 + $0.0012 = $0.002625
    # Savings: (5k * $0.150/1M) - (5k * $0.075/1M) = $0.000375
    
    expected_total = 0.002625
    # BUT WAIT - there's a bug! The savings are counted in total_cost
    # total_cost should be uncached + cached + output, not including savings again
    # Let's recalculate: 0.00075 + 0.000375 + 0.0012 = 0.002325
    expected_total = 0.002325
    if abs(result['total_cost'] - expected_total) < 0.000001:
        print(f"✓ Cost calculation CORRECT (expected ${expected_total:.6f})")
        return True
    else:
        print(f"✗ Cost calculation ERROR (expected ${expected_total:.6f})")
        return False

def test_metrics_collector_integration():
    """Test MetricsCollector integration"""
    print("\n" + "=" * 60)
    print("Testing MetricsCollector Integration")
    print("=" * 60)
    
    # Create collector with gpt-4o model
    collector = MetricsCollector(run_id="test_verify", model="gpt-4o")
    
    print(f"✓ MetricsCollector created with model: {collector.model}")
    print(f"✓ CostCalculator initialized: {collector.cost_calculator is not None}")
    
    # Add test step data
    test_tok_in = 50000
    test_tok_out = 10000
    test_cached = 20000
    
    collector.record_step(
        step_num=1,
        command="Test command",
        duration_seconds=60.0,
        success=True,
        retry_count=0,
        hitl_count=0,
        tokens_in=test_tok_in,
        tokens_out=test_tok_out,
        api_calls=5,
        cached_tokens=test_cached,
        start_timestamp=1234567890.0,
        end_timestamp=1234567950.0
    )
    
    # Test compute_cost_metrics method
    result = collector.compute_cost_metrics()
    
    print("✓ Test usage:")
    print(f"  - Input tokens: {test_tok_in:,}")
    print(f"  - Cached tokens: {test_cached:,}")
    print(f"  - Output tokens: {test_tok_out:,}")
    print(f"✓ Computed cost: ${result['COST_USD']:.6f}")
    print(f"✓ Cost breakdown available: {result.get('COST_BREAKDOWN') is not None}")
    
    if result.get('COST_BREAKDOWN'):
        breakdown = result['COST_BREAKDOWN']
        print(f"  - Uncached input cost: ${breakdown['uncached_input_cost']:.6f}")
        print(f"  - Cached input cost: ${breakdown['cached_input_cost']:.6f}")
        print(f"  - Output cost: ${breakdown['output_cost']:.6f}")
        print(f"  - Cache savings: ${breakdown['cache_savings']:.6f}")
    print(f"✓ Computed cost: ${result['COST_USD']:.6f}")
    print(f"✓ Cost breakdown available: {result.get('cost_breakdown') is not None}")
    
    if result.get('cost_breakdown'):
        breakdown = result['cost_breakdown']
        print(f"  - Input cost: ${breakdown['input_cost']:.6f}")
        print(f"  - Cached cost: ${breakdown['cached_cost']:.6f}")
        print(f"  - Output cost: ${breakdown['output_cost']:.6f}")
        print(f"  - Cache savings: ${breakdown['cache_savings']:.6f}")
    
    # Expected calculation for gpt-4o:
    # Regular input: (50k - 20k) * $2.500/1M = 30000 * 0.0000025 = $0.075
    # Cached input: 20k * $1.250/1M = 20000 * 0.00000125 = $0.025
    # Output: 10k * $10.000/1M = 10000 * 0.00001 = $0.1
    # Total: $0.075 + $0.025 + $0.1 = $0.2
    
    expected_total = 0.2
    if abs(result['COST_USD'] - expected_total) < 0.000001:
        print(f"✓ Integration cost calculation CORRECT (expected ${expected_total:.6f})")
        return True
    else:
        print(f"✗ Integration cost calculation ERROR (expected ${expected_total:.6f})")
        return False

def main():
    """Run all verification tests"""
    print("\n" + "=" * 60)
    print("Stage 2: Cost Calculation Integration Verification")
    print("=" * 60 + "\n")
    
    success = True
    
    # Test 1: CostCalculator
    try:
        if not test_cost_calculator():
            success = False
    except (ValueError, TypeError, KeyError) as e:
        print(f"✗ CostCalculator test FAILED: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # Test 2: MetricsCollector integration
    try:
        if not test_metrics_collector_integration():
            success = False
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        print(f"✗ MetricsCollector integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ All verification tests PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ Some verification tests FAILED")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
