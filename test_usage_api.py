#!/usr/bin/env python3
"""
Test script for OpenAI Usage API token counting.

Tests the new fetch_usage_from_openai method to verify it correctly
retrieves token counts from the OpenAI Usage API.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.adapters.chatdev_adapter import ChatDevAdapter
from src.orchestrator.config_loader import load_config


def test_usage_api():
    """Test fetching usage from OpenAI Usage API."""
    print("="*80)
    print("Testing OpenAI Usage API Token Counting")
    print("="*80)
    
    # Load config
    config = load_config()
    chatdev_config = config['frameworks']['chatdev']
    chatdev_config['model'] = config.get('model')  # Add global model
    
    # Create adapter
    adapter = ChatDevAdapter(
        config=chatdev_config,
        run_id="test_usage_api",
        workspace_path="/tmp/test_usage_api"
    )
    
    # Test with a recent time window (last hour)
    end_time = int(time.time())
    start_time = end_time - 3600  # Last hour
    
    print(f"\nQuerying usage for last hour:")
    print(f"  Start: {start_time} ({time.ctime(start_time)})")
    print(f"  End:   {end_time} ({time.ctime(end_time)})")
    print(f"  Model: {chatdev_config.get('model')}")
    print(f"  API Key Env: OPEN_AI_KEY_ADM (admin key with org permissions)")
    
    # Fetch usage using admin key (OPEN_AI_KEY_ADM has org-level permissions for Usage API)
    tokens_in, tokens_out = adapter.fetch_usage_from_openai(
        api_key_env_var='OPEN_AI_KEY_ADM',
        start_timestamp=start_time,
        end_timestamp=end_time,
        model=chatdev_config.get('model')
    )
    
    print(f"\nResults:")
    print(f"  Input tokens:  {tokens_in:,}")
    print(f"  Output tokens: {tokens_out:,}")
    print(f"  Total tokens:  {tokens_in + tokens_out:,}")
    
    if tokens_in > 0 or tokens_out > 0:
        # Calculate cost (gpt-5-mini: $0.25/$2.00 per 1M tokens)
        cost_input = (tokens_in / 1_000_000) * 0.25
        cost_output = (tokens_out / 1_000_000) * 2.00
        total_cost = cost_input + cost_output
        print(f"\n  Estimated cost: ${total_cost:.4f}")
        print(f"    Input:  ${cost_input:.4f}")
        print(f"    Output: ${cost_output:.4f}")
        print("\n✅ SUCCESS: Token counting working!")
    else:
        print("\n⚠️  No tokens found in last hour (this may be expected)")
        print("   Try running a ChatDev test first, then run this script again")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_usage_api()
