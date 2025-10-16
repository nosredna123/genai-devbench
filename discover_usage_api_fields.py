#!/usr/bin/env python3
"""
Query OpenAI Usage API to discover all available fields.
Run with: source .venv/bin/activate && source .env && python discover_usage_api_fields.py
"""
import os
import requests
import json
from datetime import datetime, timedelta

# Get the admin API key
api_key = os.getenv('OPEN_AI_KEY_ADM')
if not api_key:
    print("❌ OPEN_AI_KEY_ADM not found in environment")
    print("Run: source .env")
    exit(1)

print(f"✅ Using API key: {api_key[:15]}...")
print()

# Large timestamp range: last 60 days
end_time = int(datetime.now().timestamp())
start_time = int((datetime.now() - timedelta(days=60)).timestamp())

url = "https://api.openai.com/v1/organization/usage/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
params = {
    "start_time": start_time,
    "end_time": end_time,
    "bucket_width": "1d",
    "limit": 60
}

print("=" * 80)
print("🔍 OpenAI Usage API - Field Discovery")
print("=" * 80)
print(f"📅 Time range: Last 60 days")
print(f"   Start: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   End:   {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
print()

try:
    print("Querying API...")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code == 401:
        print("❌ 401 Unauthorized - API key lacks permissions")
        error_data = response.json()
        print(json.dumps(error_data, indent=2))
        exit(1)
    
    response.raise_for_status()
    data = response.json()
    
    total_buckets = len(data.get("data", []))
    print(f"✅ API call successful!")
    print(f"   Total buckets returned: {total_buckets}")
    print()
    
    # Find buckets with data
    buckets_with_data = []
    for bucket in data.get("data", []):
        if bucket.get("results"):
            buckets_with_data.append(bucket)
    
    print(f"   Buckets with data: {len(buckets_with_data)}/{total_buckets}")
    print()
    
    if buckets_with_data:
        # Analyze first bucket with data
        bucket = buckets_with_data[0]
        result = bucket["results"][0]
        
        print("=" * 80)
        print("📊 ACTUAL API RESPONSE STRUCTURE")
        print("=" * 80)
        print()
        print("🗓️  Sample Bucket:")
        print(f"   Start: {datetime.fromtimestamp(bucket['start_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   End:   {datetime.fromtimestamp(bucket['end_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("📋 Complete Result Object:")
        print(json.dumps(result, indent=2))
        print()
        
        print("=" * 80)
        print("🔑 ALL AVAILABLE FIELDS")
        print("=" * 80)
        print()
        
        all_fields = sorted(result.keys())
        
        print("✅ Currently USED (token counting):")
        for field in all_fields:
            if any(used in field for used in ["token", "context", "generated"]):
                value = result.get(field)
                print(f"   • {field:35s} = {value}")
        
        print()
        print("❌ Available but NOT USED:")
        for field in all_fields:
            if not any(used in field for used in ["token", "context", "generated", "object"]):
                value = result.get(field)
                print(f"   • {field:35s} = {value}")
        
        print()
        print("=" * 80)
        print("💡 HIGH-VALUE UNUSED FIELDS")
        print("=" * 80)
        print()
        
        if "num_model_requests" in result:
            print(f"1. num_model_requests = {result['num_model_requests']}")
            print("   → API call count (efficiency metric)")
            print("   → Use for: calls/token ratio, communication intensity")
            print()
        
        if "model" in result or "model_id" in result:
            model_val = result.get('model') or result.get('model_id', 'N/A')
            print(f"2. model = {model_val}")
            print("   → Actual model used")
            print("   → Use for: validation (ensure correct model)")
            print()
        
        if "input_cached_tokens" in result:
            print(f"3. input_cached_tokens = {result.get('input_cached_tokens', 0)}")
            print("   → Cached prompt tokens (prompt caching)")
            print("   → Use for: cost savings analysis")
            print()
        
        if "project_id" in result:
            print(f"4. project_id = {result.get('project_id', 'N/A')}")
            print("   → OpenAI project identifier")
            print("   → Use for: multi-project tracking")
            print()
        
        # List all other fields
        other_fields = [f for f in all_fields if f not in ["input_tokens", "output_tokens", 
                        "num_model_requests", "model", "model_id", "input_cached_tokens",
                        "project_id", "object", "n_context_tokens_total", "n_generated_tokens_total",
                        "n_input_tokens_total", "n_output_tokens_total", "n_context_tokens", "n_generated_tokens"]]
        
        if other_fields:
            print(f"5. Other fields found: {', '.join(other_fields)}")
            for field in other_fields:
                print(f"   • {field} = {result.get(field)}")
            print()
        
        # Aggregate statistics across all buckets
        print("=" * 80)
        print("📈 AGGREGATE STATISTICS (all buckets with data)")
        print("=" * 80)
        print()
        
        total_input = 0
        total_output = 0
        total_requests = 0
        total_cached = 0
        
        for bucket in buckets_with_data:
            for r in bucket.get("results", []):
                total_input += r.get("input_tokens", 0)
                total_output += r.get("output_tokens", 0)
                total_requests += r.get("num_model_requests", 0)
                total_cached += r.get("input_cached_tokens", 0)
        
        print(f"Total input tokens:        {total_input:,}")
        print(f"Total output tokens:       {total_output:,}")
        print(f"Total API requests:        {total_requests:,}")
        print(f"Total cached tokens:       {total_cached:,}")
        print()
        
        if total_input + total_output > 0:
            efficiency = (total_requests / (total_input + total_output)) * 1000
            cache_rate = (total_cached / total_input * 100) if total_input > 0 else 0
            avg_tokens_per_call = (total_input + total_output) / total_requests if total_requests > 0 else 0
            
            print(f"API Efficiency:            {efficiency:.2f} calls per 1K tokens")
            print(f"Cache hit rate:            {cache_rate:.1f}%")
            print(f"Avg tokens per API call:   {avg_tokens_per_call:.0f}")
        
    else:
        print("⚠️  No usage data found in last 60 days")
        print()
        print("Response structure:")
        print(json.dumps(data, indent=2)[:1000])
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request Error: {e}")
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        print(e.response.text[:500])
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
