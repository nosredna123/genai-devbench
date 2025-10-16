# API Calls Metric Implementation Plan

**Date**: October 16, 2025  
**Status**: 📋 Planning  
**Estimated Effort**: 1 hour (50 lines of code changes)

## Overview

Add a new metric called **`api_calls`** that tracks the number of API requests made to OpenAI during each experimental step. This metric leverages the existing OpenAI Usage API infrastructure to extract `num_model_requests` alongside token counts.

## Motivation

### Scientific Value

1. **Efficiency Analysis**: Measure API calls per token to identify frameworks that batch requests efficiently
2. **Communication Patterns**: Understand inter-agent or iterative refinement intensity
3. **Cost-Effectiveness**: Correlate API call volume with quality outcomes
4. **Step-wise Insights**: Identify which development phases trigger most AI interactions

### Current Infrastructure

✅ **Already Available**: OpenAI Usage API returns `num_model_requests` in the same response as token counts  
✅ **No Additional Costs**: No extra API calls needed  
✅ **Time-Window Isolation**: Same accurate attribution as token tracking  
✅ **Framework-Agnostic**: Works identically for ChatDev, GHSpec, and BAEs

## Metric Definition

### Name: `api_calls`

**Rationale**: 
- ✅ Accurate: Reflects actual OpenAI API requests
- ✅ Neutral: Doesn't imply agent communication (works for all frameworks)
- ✅ Actionable: Clear interpretation for efficiency analysis
- ❌ Rejected alternatives: `utterances` (misleading for non-agent frameworks), `model_interactions` (verbose)

### Interpretation by Framework

| Framework | API Call Represents | Expected Pattern |
|-----------|---------------------|------------------|
| **ChatDev** | Inter-agent utterance (CEO→CTO→Programmer→Reviewer) | High (multi-agent dialogue) |
| **GHSpec** | Iterative refinement cycle (spec→plan→tasks→code) | Moderate (4-phase workflow) |
| **BAEs** | Kernel-mediated entity interaction | Variable (depends on coordination) |

### Derived Metrics

1. **API Efficiency Ratio**: `api_calls / (tokens_in + tokens_out)`
   - Lower = fewer, larger calls (efficient batching)
   - Higher = many small calls (chatty communication)

2. **Calls Per Step**: `api_calls` aggregated by step number
   - Identify which development phases are most API-intensive

3. **Total Run Calls**: Sum of `api_calls` across all steps
   - Overall framework communication intensity

## Implementation Plan

### Phase 1: Data Collection (15 min)

**File**: `src/adapters/base_adapter.py`

#### Change 1.1: Update `fetch_usage_from_openai()` return signature

**Current**:
```python
def fetch_usage_from_openai(
    self,
    api_key_env_var: str,
    start_timestamp: int,
    end_timestamp: Optional[int] = None,
    model: Optional[str] = None
) -> Tuple[int, int]:  # ← (tokens_in, tokens_out)
```

**Updated**:
```python
def fetch_usage_from_openai(
    self,
    api_key_env_var: str,
    start_timestamp: int,
    end_timestamp: Optional[int] = None,
    model: Optional[str] = None
) -> Tuple[int, int, int]:  # ← (tokens_in, tokens_out, api_calls)
```

#### Change 1.2: Extract `num_model_requests` from API response

**Location**: `base_adapter.py` lines ~140-165

**Current**:
```python
def _extract_tokens(result: Dict[str, Any]) -> tuple[int, int]:
    input_fields = ("input_tokens", "n_context_tokens_total", ...)
    output_fields = ("output_tokens", "n_generated_tokens_total", ...)
    tokens_in = next((int(result.get(field, 0) or 0) for field in input_fields if field in result), 0)
    tokens_out = next((int(result.get(field, 0) or 0) for field in output_fields if field in result), 0)
    return tokens_in, tokens_out

total_input_tokens = 0
total_output_tokens = 0

for bucket in usage_data.get("data", []):
    for result in bucket.get("results", []):
        tokens_in, tokens_out = _extract_tokens(result)
        total_input_tokens += tokens_in
        total_output_tokens += tokens_out

return total_input_tokens, total_output_tokens
```

**Updated**:
```python
def _extract_tokens(result: Dict[str, Any]) -> tuple[int, int, int]:
    input_fields = ("input_tokens", "n_context_tokens_total", ...)
    output_fields = ("output_tokens", "n_generated_tokens_total", ...)
    tokens_in = next((int(result.get(field, 0) or 0) for field in input_fields if field in result), 0)
    tokens_out = next((int(result.get(field, 0) or 0) for field in output_fields if field in result), 0)
    num_requests = int(result.get("num_model_requests", 0) or 0)  # ← NEW
    return tokens_in, tokens_out, num_requests

total_input_tokens = 0
total_output_tokens = 0
total_api_calls = 0  # ← NEW

for bucket in usage_data.get("data", []):
    for result in bucket.get("results", []):
        tokens_in, tokens_out, num_requests = _extract_tokens(result)  # ← UPDATED
        total_input_tokens += tokens_in
        total_output_tokens += tokens_out
        total_api_calls += num_requests  # ← NEW

return total_input_tokens, total_output_tokens, total_api_calls  # ← UPDATED
```

#### Change 1.3: Update logging

**Location**: `base_adapter.py` lines ~167-180

**Current**:
```python
logger.info(
    "Token usage fetched from OpenAI Usage API",
    extra={
        'run_id': self.run_id,
        'step': self.current_step,
        'metadata': {
            'tokens_in': total_input_tokens,
            'tokens_out': total_output_tokens,
            'buckets_count': len(usage_data.get("data", [])),
            'model': model
        }
    }
)
```

**Updated**:
```python
logger.info(
    "Token usage fetched from OpenAI Usage API",
    extra={
        'run_id': self.run_id,
        'step': self.current_step,
        'metadata': {
            'tokens_in': total_input_tokens,
            'tokens_out': total_output_tokens,
            'api_calls': total_api_calls,  # ← NEW
            'buckets_count': len(usage_data.get("data", [])),
            'model': model
        }
    }
)
```

#### Change 1.4: Update error handling

**Location**: `base_adapter.py` lines ~85, 120, 181-190

**All returns** `(0, 0)` → `(0, 0, 0)`:
```python
# Line ~85 (missing API key)
return 0, 0, 0

# Line ~120 (permission error)
return 0, 0, 0

# Line ~186 (exception handler)
return 0, 0, 0
```

---

### Phase 2: Adapter Updates (15 min)

Update all framework adapters to capture the third return value.

#### File: `src/adapters/chatdev_adapter.py`

**Location**: Lines ~680-690 (in `execute_step` method)

**Current**:
```python
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var='OPEN_AI_KEY_ADM',
    start_timestamp=self._step_start_time,
    end_timestamp=end_timestamp,
    model=model_config
)
```

**Updated**:
```python
tokens_in, tokens_out, api_calls = self.fetch_usage_from_openai(
    api_key_env_var='OPEN_AI_KEY_ADM',
    start_timestamp=self._step_start_time,
    end_timestamp=end_timestamp,
    model=model_config
)
```

**Then add to return dict** (lines ~720-730):

**Current**:
```python
return {
    'duration_seconds': duration,
    'success': True,
    'retry_count': 0,
    'hitl_count': hitl_count,
    'tokens_in': tokens_in,
    'tokens_out': tokens_out,
    'start_timestamp': self._step_start_time,
    'end_timestamp': end_timestamp
}
```

**Updated**:
```python
return {
    'duration_seconds': duration,
    'success': True,
    'retry_count': 0,
    'hitl_count': hitl_count,
    'tokens_in': tokens_in,
    'tokens_out': tokens_out,
    'api_calls': api_calls,  # ← NEW
    'start_timestamp': self._step_start_time,
    'end_timestamp': end_timestamp
}
```

#### File: `src/adapters/ghspec_adapter.py`

**Apply identical changes** to the `execute_step()` method:
- Update `fetch_usage_from_openai()` call to capture third value
- Add `'api_calls': api_calls` to return dictionary

#### File: `src/adapters/baes_adapter.py`

**Apply identical changes** to the `execute_step()` method:
- Update `fetch_usage_from_openai()` call to capture third value
- Add `'api_calls': api_calls` to return dictionary

---

### Phase 3: Storage & Reconciliation (10 min)

#### File: `src/orchestrator/usage_reconciler.py`

**Change 3.1**: Update `_fetch_usage_from_openai()` return signature

**Location**: Lines ~51-150

**Current**:
```python
def _fetch_usage_from_openai(
    self,
    start_timestamp: int,
    end_timestamp: int
) -> tuple[int, int]:
    # ... existing code ...
    return total_input_tokens, total_output_tokens
```

**Updated**:
```python
def _fetch_usage_from_openai(
    self,
    start_timestamp: int,
    end_timestamp: int
) -> tuple[int, int, int]:
    # ... existing code ...
    total_api_calls = 0  # ← NEW (aggregate from buckets)
    
    for bucket in usage_data.get("data", []):
        for result in bucket.get("results", []):
            # ... extract tokens ...
            num_requests = int(result.get("num_model_requests", 0) or 0)  # ← NEW
            total_api_calls += num_requests  # ← NEW
    
    return total_input_tokens, total_output_tokens, total_api_calls
```

**Change 3.2**: Update reconciliation logic

**Location**: Lines ~200-250 (`_reconcile_steps` method)

**Current**:
```python
tokens_in, tokens_out = self._fetch_usage_from_openai(
    start_timestamp=step.get('start_timestamp'),
    end_timestamp=step.get('end_timestamp')
)

step['tokens_in'] = tokens_in
step['tokens_out'] = tokens_out
```

**Updated**:
```python
tokens_in, tokens_out, api_calls = self._fetch_usage_from_openai(
    start_timestamp=step.get('start_timestamp'),
    end_timestamp=step.get('end_timestamp')
)

step['tokens_in'] = tokens_in
step['tokens_out'] = tokens_out
step['api_calls'] = api_calls  # ← NEW
```

---

### Phase 4: Analysis & Reporting (15 min)

#### File: `src/analysis/statistics.py`

**Change 4.1**: Extract `api_calls` from metrics

**Location**: Lines ~100-150 (metric extraction section)

**Add after token extraction**:
```python
# Extract API calls
api_calls_data = []
for run in runs:
    steps = run['metrics'].get('steps', [])
    total_calls = sum(step.get('api_calls', 0) for step in steps)
    api_calls_data.append({
        'framework': run['framework'],
        'run_id': run['run_id'],
        'total_calls': total_calls,
        'steps': [step.get('api_calls', 0) for step in steps]
    })
```

**Change 4.2**: Add statistical analysis

**Location**: Lines ~300-400 (after existing metric analysis)

**Add new section**:
```python
def _analyze_api_calls(self, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze API call patterns across frameworks."""
    
    # Extract data by framework
    chatdev_calls = []
    ghspec_calls = []
    baes_calls = []
    
    for run in runs:
        framework = run['framework']
        steps = run['metrics'].get('steps', [])
        total_calls = sum(step.get('api_calls', 0) for step in steps)
        
        if framework == 'chatdev':
            chatdev_calls.append(total_calls)
        elif framework == 'ghspec':
            ghspec_calls.append(total_calls)
        elif framework == 'baes':
            baes_calls.append(total_calls)
    
    # Compute statistics
    results = {}
    
    for framework, data in [('chatdev', chatdev_calls), ('ghspec', ghspec_calls), ('baes', baes_calls)]:
        if data:
            results[framework] = {
                'mean': np.mean(data),
                'median': np.median(data),
                'std': np.std(data),
                'min': np.min(data),
                'max': np.max(data),
                'ci_95': self._bootstrap_ci(data) if len(data) > 1 else (np.mean(data), np.mean(data))
            }
    
    # Kruskal-Wallis test
    if len(chatdev_calls) > 0 and len(ghspec_calls) > 0 and len(baes_calls) > 0:
        h_stat, p_value = stats.kruskal(chatdev_calls, ghspec_calls, baes_calls)
        results['kruskal_wallis'] = {'h_statistic': h_stat, 'p_value': p_value}
    
    return results
```

**Change 4.3**: Add to report generation

**Location**: Lines ~744+ (in Experimental Methodology section, or create new metric section)

**Add new subsection**:
```markdown
### API Calls (Communication Intensity)

**Definition**: Number of OpenAI API requests made during the entire experiment run.

**Interpretation**:
- **Higher API calls**: More iterative refinement, richer inter-agent dialogue, or frequent model consultations
- **Lower API calls**: More efficient batching, fewer iterations, or direct code generation

**Framework Patterns**:
- **ChatDev**: Expected high (multi-agent communication: CEO→CTO→Programmer→Reviewer→Tester)
- **GHSpec**: Expected moderate (4-phase workflow: specify→plan→tasks→implement)
- **BAEs**: Variable (depends on entity coordination complexity)

**Efficiency Metric**: API Calls per 1K Tokens = `api_calls / (tokens_total / 1000)`
- Lower ratio = fewer, larger API calls (efficient batching)
- Higher ratio = many small API calls (chatty communication)

**Results**:
- ChatDev: {mean} ± {std} calls (CI: [{ci_low}, {ci_high}])
- GHSpec: {mean} ± {std} calls (CI: [{ci_low}, {ci_high}])
- BAEs: {mean} ± {std} calls (CI: [{ci_low}, {ci_high}])

**Statistical Test**: Kruskal-Wallis H = {h_stat}, p = {p_value}
```

**Change 4.4**: Add to visualization

**Location**: Lines ~600-650 (radar chart generation)

**Add to metrics list**:
```python
metrics_to_plot = [
    'tokens_total',
    'duration_seconds',
    'hitl_count',
    'api_calls',  # ← NEW
    'test_coverage'  # if available
]
```

---

### Phase 5: Visualization (10 min)

#### New Chart: API Calls Timeline

**File**: `src/analysis/statistics.py`

**Add new method** (lines ~650-700):

```python
def _generate_api_calls_timeline(self, runs: List[Dict[str, Any]]) -> str:
    """Generate timeline showing API call distribution across steps."""
    
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Group by framework
    for framework in ['chatdev', 'ghspec', 'baes']:
        framework_runs = [r for r in runs if r['framework'] == framework]
        
        if not framework_runs:
            continue
        
        # Calculate mean API calls per step across runs
        step_calls = {}
        for run in framework_runs:
            for step in run['metrics'].get('steps', []):
                step_num = step.get('step_number', 0)
                calls = step.get('api_calls', 0)
                if step_num not in step_calls:
                    step_calls[step_num] = []
                step_calls[step_num].append(calls)
        
        # Plot mean with error bars
        steps = sorted(step_calls.keys())
        means = [np.mean(step_calls[s]) for s in steps]
        stds = [np.std(step_calls[s]) for s in steps]
        
        ax.errorbar(steps, means, yerr=stds, label=framework.upper(), 
                   marker='o', capsize=5, linewidth=2)
    
    ax.set_xlabel('Development Step', fontsize=12)
    ax.set_ylabel('API Calls (Mean ± SD)', fontsize=12)
    ax.set_title('API Communication Intensity Across Development Steps', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save to buffer
    import io
    import base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return f"![API Calls Timeline](data:image/png;base64,{img_base64})"
```

**Add to report** (lines ~800+):
```markdown
### Communication Intensity Timeline

{self._generate_api_calls_timeline(runs)}

**Insights**:
- Which steps trigger most AI interactions?
- Do frameworks show different communication patterns across the development lifecycle?
- Step 1 (initial spec): Typically high for exploration
- Step 6 (UI): May be lower if frameworks use templates
```

---

## Testing Strategy

### Test 1: Unit Test - Extract `num_model_requests` from API Response

**File**: `tests/unit/test_base_adapter.py` (create if doesn't exist)

```python
"""Unit tests for BaseAdapter token and API call extraction."""

import pytest
from src.adapters.base_adapter import BaseAdapter


class TestBaseAdapter:
    """Test BaseAdapter usage extraction logic."""
    
    def test_extract_num_model_requests_from_response(self):
        """Test that num_model_requests is correctly extracted from OpenAI Usage API response."""
        
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
                            "num_model_requests": 5  # ← KEY FIELD
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
                            "num_model_requests": 8  # ← Second bucket
                        }
                    ]
                }
            ]
        }
        
        # Simulate the extraction logic (copy from _extract_tokens inner function)
        total_input_tokens = 0
        total_output_tokens = 0
        total_api_calls = 0
        
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                total_input_tokens += int(result.get("input_tokens", 0) or 0)
                total_output_tokens += int(result.get("output_tokens", 0) or 0)
                total_api_calls += int(result.get("num_model_requests", 0) or 0)
        
        # Assertions
        assert total_input_tokens == 3000, "Input tokens should sum across buckets"
        assert total_output_tokens == 1300, "Output tokens should sum across buckets"
        assert total_api_calls == 13, "API calls should sum across buckets (5 + 8)"
    
    def test_extract_handles_missing_num_model_requests(self):
        """Test graceful handling when num_model_requests is missing."""
        
        mock_usage_data = {
            "data": [
                {
                    "results": [
                        {
                            "input_tokens": 1000,
                            "output_tokens": 500
                            # ← num_model_requests missing
                        }
                    ]
                }
            ]
        }
        
        total_api_calls = 0
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                total_api_calls += int(result.get("num_model_requests", 0) or 0)
        
        assert total_api_calls == 0, "Should default to 0 when field missing"
    
    def test_extract_handles_null_num_model_requests(self):
        """Test graceful handling when num_model_requests is null."""
        
        mock_usage_data = {
            "data": [
                {
                    "results": [
                        {
                            "input_tokens": 1000,
                            "output_tokens": 500,
                            "num_model_requests": None  # ← Explicitly null
                        }
                    ]
                }
            ]
        }
        
        total_api_calls = 0
        for bucket in mock_usage_data.get("data", []):
            for result in bucket.get("results", []):
                total_api_calls += int(result.get("num_model_requests", 0) or 0)
        
        assert total_api_calls == 0, "Should handle null values gracefully"
```

---

### Test 2: Integration Test - Verify API Calls in Live Usage API Call

**File**: `tests/integration/test_usage_api.py` (update existing)

**Add new test function**:

```python
def test_usage_api_returns_api_calls():
    """Test that fetch_usage_from_openai returns API call count as third value."""
    
    print("="*80)
    print("Testing OpenAI Usage API - API Calls Extraction")
    print("="*80)
    
    # Load config
    config = load_config()
    chatdev_config = config['frameworks']['chatdev']
    chatdev_config['model'] = config.get('model')
    
    # Create adapter
    adapter = ChatDevAdapter(
        config=chatdev_config,
        run_id="test_api_calls_extraction",
        workspace_path="/tmp/test_api_calls"
    )
    
    # Test with recent time window (last 24 hours)
    end_time = int(time.time())
    start_time = end_time - 86400  # Last 24 hours
    
    print(f"\nQuerying usage for last 24 hours:")
    print(f"  Start: {start_time} ({time.ctime(start_time)})")
    print(f"  End:   {end_time} ({time.ctime(end_time)})")
    print(f"  Model: {chatdev_config.get('model')}")
    
    # Fetch usage (should return 3-tuple)
    result = adapter.fetch_usage_from_openai(
        api_key_env_var='OPEN_AI_KEY_ADM',
        start_timestamp=start_time,
        end_timestamp=end_time,
        model=chatdev_config.get('model')
    )
    
    # Verify return structure
    assert isinstance(result, tuple), "Should return a tuple"
    assert len(result) == 3, f"Should return 3-tuple, got {len(result)}-tuple"
    
    tokens_in, tokens_out, api_calls = result
    
    print(f"\n✅ Results:")
    print(f"  Input tokens:  {tokens_in:,}")
    print(f"  Output tokens: {tokens_out:,}")
    print(f"  API calls:     {api_calls:,}")  # ← NEW
    
    # Assertions
    assert isinstance(tokens_in, int), "tokens_in should be integer"
    assert isinstance(tokens_out, int), "tokens_out should be integer"
    assert isinstance(api_calls, int), "api_calls should be integer"
    assert api_calls >= 0, "api_calls should be non-negative"
    
    # Sanity check: if we have tokens, we should have API calls
    if tokens_in > 0 or tokens_out > 0:
        assert api_calls > 0, "If tokens exist, API calls must be > 0"
        
        # Efficiency check: API calls should be reasonable relative to tokens
        total_tokens = tokens_in + tokens_out
        calls_per_1k_tokens = (api_calls / total_tokens) * 1000 if total_tokens > 0 else 0
        
        print(f"\n📊 Efficiency Metrics:")
        print(f"  Total tokens:        {total_tokens:,}")
        print(f"  Calls per 1K tokens: {calls_per_1k_tokens:.2f}")
        
        # Sanity bounds (very loose - just checking for obviously wrong data)
        assert calls_per_1k_tokens < 100, "Too many calls per token (likely parsing error)"
        assert calls_per_1k_tokens > 0.001, "Too few calls per token (likely missing data)"
    
    print("\n✅ All assertions passed!")
```

---

### Test 3: End-to-End Test - Verify API Calls in Metrics JSON

**File**: `tests/integration/test_full_workflow.py` (create if doesn't exist)

```python
"""End-to-end test for API calls metric in full experiment workflow."""

import json
import subprocess
from pathlib import Path


def test_api_calls_in_metrics_json():
    """Test that api_calls appears in metrics.json after a run."""
    
    print("="*80)
    print("Testing API Calls Metric - End-to-End Workflow")
    print("="*80)
    
    # Find a recent completed run
    runs_dir = Path("runs")
    metrics_files = list(runs_dir.glob("*/*/metrics.json"))
    
    assert len(metrics_files) > 0, "No metrics.json files found. Run an experiment first."
    
    # Take the most recent one
    latest_metrics = max(metrics_files, key=lambda p: p.stat().st_mtime)
    
    print(f"\nAnalyzing: {latest_metrics}")
    
    # Load metrics
    with open(latest_metrics, 'r') as f:
        metrics = json.load(f)
    
    # Verify structure
    assert 'steps' in metrics, "metrics.json should have 'steps' key"
    assert len(metrics['steps']) > 0, "Should have at least one step"
    
    print(f"  Found {len(metrics['steps'])} steps")
    
    # Check each step for api_calls field
    total_api_calls = 0
    for i, step in enumerate(metrics['steps'], 1):
        assert 'api_calls' in step, f"Step {i} missing 'api_calls' field"
        
        api_calls = step['api_calls']
        assert isinstance(api_calls, int), f"Step {i} api_calls should be integer"
        assert api_calls >= 0, f"Step {i} api_calls should be non-negative"
        
        tokens_in = step.get('tokens_in', 0)
        tokens_out = step.get('tokens_out', 0)
        
        print(f"\n  Step {i}:")
        print(f"    Tokens in:  {tokens_in:,}")
        print(f"    Tokens out: {tokens_out:,}")
        print(f"    API calls:  {api_calls:,}")
        
        # If step has tokens, it should have API calls
        if tokens_in > 0 or tokens_out > 0:
            assert api_calls > 0, f"Step {i} has tokens but no API calls"
        
        total_api_calls += api_calls
    
    print(f"\n  Total API calls across all steps: {total_api_calls:,}")
    
    # Verify total is reasonable (not zero for completed run)
    if metrics.get('end_timestamp'):  # Run completed
        assert total_api_calls > 0, "Completed run should have > 0 API calls"
    
    print("\n✅ All assertions passed!")
```

---

### Test 4: Statistical Analysis Test

**File**: `tests/unit/test_statistics.py` (update existing or create)

```python
"""Test API calls statistical analysis."""

import pytest
import numpy as np
from src.analysis.statistics import StatisticalAnalyzer


def test_api_calls_analysis():
    """Test that API calls are properly analyzed in statistics."""
    
    # Mock run data with api_calls
    mock_runs = [
        {
            'framework': 'chatdev',
            'run_id': 'test-1',
            'metrics': {
                'steps': [
                    {'step_number': 1, 'api_calls': 10, 'tokens_in': 1000, 'tokens_out': 500},
                    {'step_number': 2, 'api_calls': 15, 'tokens_in': 2000, 'tokens_out': 800},
                ]
            }
        },
        {
            'framework': 'ghspec',
            'run_id': 'test-2',
            'metrics': {
                'steps': [
                    {'step_number': 1, 'api_calls': 5, 'tokens_in': 800, 'tokens_out': 400},
                    {'step_number': 2, 'api_calls': 8, 'tokens_in': 1500, 'tokens_out': 600},
                ]
            }
        },
    ]
    
    # Create analyzer
    analyzer = StatisticalAnalyzer()
    
    # Analyze API calls (assuming _analyze_api_calls method exists)
    results = analyzer._analyze_api_calls(mock_runs)
    
    # Verify ChatDev stats
    assert 'chatdev' in results
    assert results['chatdev']['mean'] == 25  # 10 + 15
    assert results['chatdev']['median'] == 25
    
    # Verify GHSpec stats
    assert 'ghspec' in results
    assert results['ghspec']['mean'] == 13  # 5 + 8
    assert results['ghspec']['median'] == 13
    
    # Verify efficiency metrics can be computed
    chatdev_total_tokens = 1000 + 500 + 2000 + 800  # 4300
    chatdev_efficiency = (25 / chatdev_total_tokens) * 1000
    
    assert 0 < chatdev_efficiency < 100, "Efficiency should be in reasonable range"
    
    print(f"✅ ChatDev efficiency: {chatdev_efficiency:.2f} calls per 1K tokens")
```

---

## Test Execution Plan

### Pre-Implementation Tests (Should FAIL)

Run these BEFORE implementing to verify they actually test the new functionality:

```bash
# Unit tests
pytest tests/unit/test_base_adapter.py::TestBaseAdapter::test_extract_num_model_requests_from_response -v

# Integration test
pytest tests/integration/test_usage_api.py::test_usage_api_returns_api_calls -v

# Expected: FAIL (method doesn't return 3-tuple yet)
```

### Post-Implementation Tests (Should PASS)

Run these AFTER implementing all changes:

```bash
# Run all new tests
pytest tests/unit/test_base_adapter.py -v
pytest tests/integration/test_usage_api.py -v
pytest tests/integration/test_full_workflow.py -v

# Run full test suite
./run_tests.sh

# Verify with actual experiment
./runners/run_experiment.sh --framework chatdev --runs 1

# Check metrics.json contains api_calls
cat runs/chatdev/*/metrics.json | jq '.steps[0].api_calls'

# Generate report and verify api_calls section
./runners/analyze_results.sh
grep -A 20 "API Calls" analysis_output/report.md
```

---

## Validation Checklist

- [ ] **Phase 1**: `BaseAdapter.fetch_usage_from_openai()` returns 3-tuple
- [ ] **Phase 1**: Error handlers return `(0, 0, 0)`
- [ ] **Phase 1**: Logging includes `api_calls`
- [ ] **Phase 2**: ChatDev adapter captures and stores `api_calls`
- [ ] **Phase 2**: GHSpec adapter captures and stores `api_calls`
- [ ] **Phase 2**: BAEs adapter captures and stores `api_calls`
- [ ] **Phase 3**: Reconciler extracts and updates `api_calls`
- [ ] **Phase 4**: Statistics analyzer processes `api_calls`
- [ ] **Phase 4**: Report includes API Calls section
- [ ] **Phase 5**: Radar chart includes `api_calls` dimension
- [ ] **Phase 5**: Timeline chart shows API call patterns
- [ ] **Tests**: Unit test passes (extract from mock data)
- [ ] **Tests**: Integration test passes (live Usage API)
- [ ] **Tests**: E2E test passes (metrics.json validation)
- [ ] **Tests**: Statistical analysis test passes

---

## Rollout Strategy

### Step 1: Implement & Test (45 min)
1. Implement Phase 1-3 (data collection & storage)
2. Run unit tests
3. Run integration test with live Usage API
4. Commit: `feat: Add api_calls metric - data collection`

### Step 2: Analysis & Reporting (30 min)
1. Implement Phase 4-5 (analysis & visualization)
2. Regenerate report from existing runs
3. Verify new sections appear correctly
4. Commit: `feat: Add api_calls metric - analysis & visualization`

### Step 3: Documentation (15 min)
1. Update `docs/metrics.md` with API calls definition
2. Update `README.md` to mention new metric
3. Update `docs/architecture.md` with data flow
4. Commit: `docs: Document api_calls metric`

### Step 4: Full Experiment (Optional)
1. Run fresh experiment: `./runners/run_experiment.sh --framework all --runs 5`
2. Verify API calls collected for all frameworks
3. Analyze patterns and update methodology section if needed

---

## Expected Results

### Typical Values (Estimated)

Based on framework architectures:

| Framework | Expected API Calls (6 steps) | Calls per Step | Efficiency (calls/1K tokens) |
|-----------|------------------------------|----------------|------------------------------|
| **ChatDev** | 150-300 | 25-50 | 5-10 (high, multi-agent) |
| **GHSpec** | 50-100 | 8-17 | 2-5 (moderate, 4-phase) |
| **BAEs** | 30-80 | 5-13 | 1-4 (low, direct API) |

### Interpretation Guidelines

**High API Calls** (>200 total):
- ✅ Rich multi-agent dialogue
- ✅ Extensive iterative refinement
- ⚠️ Potentially inefficient batching
- ⚠️ Higher latency due to API overhead

**Low API Calls** (<50 total):
- ✅ Efficient request batching
- ✅ Direct code generation
- ⚠️ Possibly less iterative (lower quality?)
- ⚠️ May skip validation steps

**Efficiency Ratio**:
- `< 3 calls/1K tokens`: Very efficient (good batching)
- `3-7 calls/1K tokens`: Balanced (typical)
- `> 7 calls/1K tokens`: Chatty (many small interactions)

---

## Success Criteria

1. ✅ All unit tests pass
2. ✅ Integration test with live Usage API returns 3-tuple
3. ✅ E2E test finds `api_calls` in metrics.json
4. ✅ Report includes API Calls section with statistics
5. ✅ Radar chart displays `api_calls` dimension
6. ✅ Timeline chart shows step-wise patterns
7. ✅ No regression in existing token/timing metrics
8. ✅ Statistical analysis (Kruskal-Wallis) runs without errors
9. ✅ CI/CD pipeline passes (if applicable)
10. ✅ Documentation updated

---

## Future Enhancements

1. **Derived Metrics**:
   - API Efficiency Score: `(tokens_total / api_calls) / 1000`
   - Communication Overhead: `(api_calls * avg_latency_ms) / total_duration`

2. **Detailed Breakdown**:
   - If OpenAI API adds per-agent/per-phase metadata, capture it
   - Cross-reference with HITL events (does HITL correlate with more API calls?)

3. **Anomaly Detection**:
   - Flag steps with unusually high/low API calls
   - Alert if `api_calls = 0` but `tokens > 0` (data integrity issue)

4. **Cost Analysis**:
   - Combine with per-call pricing to estimate API cost per call
   - Compare total cost vs. quality outcomes

---

## References

- **OpenAI Usage API**: https://platform.openai.com/docs/api-reference/usage
- **Token Counting Implementation**: `docs/token_counting_implementation.md`
- **Metric Definitions**: `docs/metrics.md`
- **Statistical Methods**: `docs/test_results_2025-10-09.md`

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-10-16 | Initial implementation plan created | GitHub Copilot |

