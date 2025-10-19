"""Tests for timeline data aggregation in generate_analysis.py.

This test module validates the new aggregation functionality added in Stage 5 Task 5.1
to fix the bug where timeline data was being overwritten instead of aggregated.
"""

import pytest
from scripts.generate_analysis import aggregate_timeline_data


class TestTimelineAggregation:
    """Test timeline data aggregation across multiple runs."""
    
    def test_aggregate_mean(self):
        """Test mean aggregation of timeline data."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [5, 7, 6]},  # mean = 6.0
                2: {'API_CALLS': [10, 12, 11]}  # mean = 11.0
            },
            'chatdev': {
                1: {'API_CALLS': [8, 10]},  # mean = 9.0
                2: {'API_CALLS': [15, 17]}  # mean = 16.0
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'mean')
        
        assert result['baes'][1]['API_CALLS'] == 6.0
        assert result['baes'][2]['API_CALLS'] == 11.0
        assert result['chatdev'][1]['API_CALLS'] == 9.0
        assert result['chatdev'][2]['API_CALLS'] == 16.0
    
    def test_aggregate_median_odd_count(self):
        """Test median aggregation with odd number of values."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [5, 7, 9]},  # median = 7
                2: {'API_CALLS': [10, 15, 20]}  # median = 15
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'median')
        
        assert result['baes'][1]['API_CALLS'] == 7
        assert result['baes'][2]['API_CALLS'] == 15
    
    def test_aggregate_median_even_count(self):
        """Test median aggregation with even number of values."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [5, 7, 9, 11]},  # median = (7+9)/2 = 8.0
                2: {'API_CALLS': [10, 20]}  # median = (10+20)/2 = 15.0
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'median')
        
        assert result['baes'][1]['API_CALLS'] == 8.0
        assert result['baes'][2]['API_CALLS'] == 15.0
    
    def test_aggregate_last(self):
        """Test 'last' aggregation (uses last run's value)."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [5, 7, 9]},  # last = 9
                2: {'API_CALLS': [10, 15, 20]}  # last = 20
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'last')
        
        assert result['baes'][1]['API_CALLS'] == 9
        assert result['baes'][2]['API_CALLS'] == 20
    
    def test_aggregate_multiple_metrics(self):
        """Test aggregation with multiple metrics per step."""
        timeline_data = {
            'baes': {
                1: {
                    'API_CALLS': [5, 7, 6],
                    'TOK_IN': [1000, 1100, 1050],
                    'TOK_OUT': [500, 550, 525]
                }
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'mean')
        
        assert result['baes'][1]['API_CALLS'] == 6.0
        assert result['baes'][1]['TOK_IN'] == 1050.0
        assert result['baes'][1]['TOK_OUT'] == 525.0
    
    def test_aggregate_empty_values(self):
        """Test aggregation with empty value lists."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': []},  # empty list
                2: {'API_CALLS': [10]}  # single value
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'mean')
        
        assert result['baes'][1]['API_CALLS'] == 0  # empty -> 0
        assert result['baes'][2]['API_CALLS'] == 10.0
    
    def test_aggregate_single_value(self):
        """Test aggregation with single value (all methods should give same result)."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [42]}
            }
        }
        
        for method in ['mean', 'median', 'last']:
            result = aggregate_timeline_data(timeline_data, method)
            assert result['baes'][1]['API_CALLS'] == 42
    
    def test_aggregate_default_to_mean(self):
        """Test that invalid aggregation method defaults to mean."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [5, 7, 9]}  # mean = 7.0
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'invalid_method')
        
        # Should default to mean
        assert result['baes'][1]['API_CALLS'] == 7.0
    
    def test_aggregate_preserves_structure(self):
        """Test that aggregation preserves framework and step structure."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [5]},
                2: {'API_CALLS': [10]},
                3: {'API_CALLS': [15]}
            },
            'chatdev': {
                1: {'API_CALLS': [8]},
                2: {'API_CALLS': [12]}
            },
            'ghspec': {
                1: {'API_CALLS': [6]}
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'mean')
        
        # Check all frameworks present
        assert set(result.keys()) == {'baes', 'chatdev', 'ghspec'}
        
        # Check steps for each framework
        assert set(result['baes'].keys()) == {1, 2, 3}
        assert set(result['chatdev'].keys()) == {1, 2}
        assert set(result['ghspec'].keys()) == {1}
    
    def test_aggregate_real_world_scenario(self):
        """Test with realistic multi-run, multi-framework data."""
        # Simulate 3 runs for baes, 2 runs for chatdev
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [5, 6, 5], 'TOK_IN': [1000, 1100, 1050]},
                2: {'API_CALLS': [8, 9, 7], 'TOK_IN': [1500, 1600, 1550]},
                3: {'API_CALLS': [12, 13, 11], 'TOK_IN': [2000, 2100, 2050]}
            },
            'chatdev': {
                1: {'API_CALLS': [10, 11], 'TOK_IN': [2000, 2200]},
                2: {'API_CALLS': [15, 16], 'TOK_IN': [3000, 3200]},
                3: {'API_CALLS': [20, 21], 'TOK_IN': [4000, 4200]}
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'mean')
        
        # Verify BAEs averages
        assert result['baes'][1]['API_CALLS'] == pytest.approx(5.33, abs=0.01)
        assert result['baes'][1]['TOK_IN'] == pytest.approx(1050.0)
        assert result['baes'][2]['API_CALLS'] == 8.0
        assert result['baes'][3]['API_CALLS'] == 12.0
        
        # Verify ChatDev averages
        assert result['chatdev'][1]['API_CALLS'] == 10.5
        assert result['chatdev'][1]['TOK_IN'] == 2100.0
        assert result['chatdev'][2]['API_CALLS'] == 15.5
        assert result['chatdev'][3]['API_CALLS'] == 20.5
    
    def test_aggregate_handles_float_values(self):
        """Test aggregation with float values (e.g., duration_seconds)."""
        timeline_data = {
            'baes': {
                1: {'duration_seconds': [10.5, 11.2, 10.8]}  # mean = 10.83...
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'mean')
        
        assert result['baes'][1]['duration_seconds'] == pytest.approx(10.83, abs=0.01)
    
    def test_aggregate_median_unsorted_values(self):
        """Test that median correctly sorts values before finding middle."""
        timeline_data = {
            'baes': {
                1: {'API_CALLS': [9, 5, 7]}  # sorted: [5, 7, 9], median = 7
            }
        }
        
        result = aggregate_timeline_data(timeline_data, 'median')
        
        assert result['baes'][1]['API_CALLS'] == 7
