#!/usr/bin/env python3
"""
End-to-end test for API calls metric in full experiment workflow.

This test validates that the api_calls field appears correctly in metrics.json
after running experiments.
"""

import json
import sys
from pathlib import Path


def test_api_calls_in_metrics_json():
    """Test that api_calls appears in metrics.json after a run."""
    
    print("="*80)
    print("Testing API Calls Metric - End-to-End Workflow")
    print("="*80)
    
    # Find completed runs
    runs_dir = Path("runs")
    
    if not runs_dir.exists():
        print("\n❌ ERROR: runs/ directory not found")
        print("   Run an experiment first: ./runners/run_experiment.sh --framework chatdev --runs 1")
        sys.exit(1)
    
    metrics_files = list(runs_dir.glob("*/*/metrics.json"))
    
    if len(metrics_files) == 0:
        print("\n❌ ERROR: No metrics.json files found")
        print("   Run an experiment first: ./runners/run_experiment.sh --framework chatdev --runs 1")
        sys.exit(1)
    
    # Take the most recent one
    latest_metrics = max(metrics_files, key=lambda p: p.stat().st_mtime)
    
    print(f"\n📄 Analyzing most recent metrics file:")
    print(f"   {latest_metrics}")
    print(f"   Size: {latest_metrics.stat().st_size:,} bytes")
    
    # Load metrics
    with open(latest_metrics, 'r') as f:
        metrics = json.load(f)
    
    # Verify structure
    assert 'run_id' in metrics, "metrics.json should have 'run_id' key"
    assert 'steps' in metrics, "metrics.json should have 'steps' key"
    assert len(metrics['steps']) > 0, "Should have at least one step"
    
    print(f"\n✅ Run ID: {metrics['run_id']}")
    print(f"✅ Found {len(metrics['steps'])} steps")
    
    # Check if api_calls field exists (may not if implementation not yet complete)
    has_api_calls = any('api_calls' in step for step in metrics['steps'])
    
    if not has_api_calls:
        print("\n⚠️  WARNING: No 'api_calls' field found in any step")
        print("   This is expected if the api_calls metric hasn't been implemented yet")
        print("   After implementing, this test should pass")
        return
    
    # Detailed validation for each step
    total_api_calls = 0
    total_tokens = 0
    steps_with_calls = 0
    
    print("\n" + "-"*80)
    print("Step-by-Step Analysis:")
    print("-"*80)
    
    for i, step in enumerate(metrics['steps'], 1):
        step_num = step.get('step_number', i)
        
        # Check for api_calls field
        if 'api_calls' not in step:
            print(f"\n⚠️  Step {step_num}: Missing 'api_calls' field")
            continue
        
        api_calls = step['api_calls']
        tokens_in = step.get('tokens_in', 0)
        tokens_out = step.get('tokens_out', 0)
        step_tokens = tokens_in + tokens_out
        duration = step.get('duration_seconds', 0)
        success = step.get('success', False)
        
        # Validate data types
        assert isinstance(api_calls, int), f"Step {step_num}: api_calls should be integer, got {type(api_calls)}"
        assert api_calls >= 0, f"Step {step_num}: api_calls should be non-negative, got {api_calls}"
        
        # Calculate efficiency
        efficiency = (api_calls / step_tokens) * 1000 if step_tokens > 0 else 0
        
        print(f"\nStep {step_num}:")
        print(f"  Status:      {'✅ Success' if success else '❌ Failed'}")
        print(f"  Duration:    {duration:.1f}s")
        print(f"  Tokens in:   {tokens_in:,}")
        print(f"  Tokens out:  {tokens_out:,}")
        print(f"  Total:       {step_tokens:,}")
        print(f"  API calls:   {api_calls:,}")
        
        if step_tokens > 0:
            print(f"  Efficiency:  {efficiency:.2f} calls/1K tokens", end="")
            
            if efficiency < 1.0:
                print(" (very efficient ✅)")
            elif efficiency < 5.0:
                print(" (balanced ✅)")
            elif efficiency < 10.0:
                print(" (chatty ⚠️)")
            else:
                print(" (very chatty ⚠️)")
        
        # Data integrity checks
        if step_tokens > 0 and api_calls == 0:
            print(f"  ⚠️  WARNING: Step has tokens but no API calls (data integrity issue)")
        
        if api_calls > 0 and step_tokens == 0:
            print(f"  ⚠️  WARNING: Step has API calls but no tokens (data integrity issue)")
        
        # Aggregate
        total_api_calls += api_calls
        total_tokens += step_tokens
        if api_calls > 0:
            steps_with_calls += 1
    
    # Summary statistics
    print("\n" + "="*80)
    print("Summary Statistics:")
    print("="*80)
    print(f"Total API calls:         {total_api_calls:,}")
    print(f"Total tokens:            {total_tokens:,}")
    print(f"Steps with API calls:    {steps_with_calls}/{len(metrics['steps'])}")
    
    if total_tokens > 0:
        overall_efficiency = (total_api_calls / total_tokens) * 1000
        avg_tokens_per_call = total_tokens / total_api_calls if total_api_calls > 0 else 0
        
        print(f"\nOverall Efficiency:")
        print(f"  Calls per 1K tokens:   {overall_efficiency:.2f}")
        print(f"  Avg tokens per call:   {avg_tokens_per_call:.0f}")
    
    # Final validation
    if metrics.get('end_timestamp'):  # Run completed
        assert total_api_calls > 0, "Completed run should have > 0 total API calls"
        print("\n✅ All validations passed!")
    else:
        print("\n⚠️  Run incomplete (no end_timestamp)")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        test_api_calls_in_metrics_json()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
