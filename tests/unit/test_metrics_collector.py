"""
Unit tests for MetricsCollector.

Tests the new schema (v2.0.0) where:
- record_step() accepts NO token parameters
- steps[] array contains only timing/interaction fields
- Token fields in steps[] raise ValueError (fail-fast validation)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.orchestrator.metrics_collector import MetricsCollector


@pytest.fixture
def mock_dependencies():
    """Mock MetricsConfig and CostCalculator dependencies."""
    with patch('src.orchestrator.metrics_collector.get_metrics_config') as mock_config, \
         patch('src.orchestrator.metrics_collector.CostCalculator') as mock_calculator:
        
        # Mock metrics config
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        
        # Mock cost calculator
        mock_calc_instance = MagicMock()
        mock_calc_instance.calculate_cost.return_value = {
            'total_cost': 0.0,
            'input_cost': 0.0,
            'output_cost': 0.0,
            'cached_input_cost': 0.0
        }
        mock_calculator.return_value = mock_calc_instance
        
        yield mock_config, mock_calculator


class TestMetricsCollector:
    """Test suite for MetricsCollector with clean schema (no step-level tokens)."""
    
    def test_record_step_new_signature(self, mock_dependencies):
        """Test record_step() with new signature (no token parameters)."""
        collector = MetricsCollector(run_id="test_run_001")
        
        # Record step with new signature
        collector.record_step(
            step_num=1,
            duration_seconds=35.2,
            start_timestamp=1761523200,
            end_timestamp=1761523235,
            hitl_count=2,
            retry_count=0,
            success=True
        )
        
        metrics = collector.get_aggregate_metrics(
            crude_score=75,
            esr=0.95,
            mc=0.90,
            zdi=0
        )
        
        # Verify step was recorded
        assert len(metrics['steps']) == 1
        step = metrics['steps'][0]
        
        # Verify allowed fields
        assert step['step'] == 1
        assert step['duration_seconds'] == 35.2
        assert step['start_timestamp'] == 1761523200
        assert step['end_timestamp'] == 1761523235
        assert step['hitl_count'] == 2
        assert step['retry_count'] == 0
        assert step['success'] is True
        
        # CRITICAL: Verify NO token fields
        assert 'tokens_in' not in step
        assert 'tokens_out' not in step
        assert 'api_calls' not in step
        assert 'cached_tokens' not in step
    
    def test_multiple_steps_no_tokens(self, mock_dependencies):
        """Test recording multiple steps without token fields."""
        collector = MetricsCollector(run_id="test_run_002")
        
        # Record 3 steps
        for i in range(1, 4):
            collector.record_step(
                step_num=i,
                duration_seconds=float(i * 10),
                start_timestamp=1761523200 + (i-1) * 100,
                end_timestamp=1761523200 + i * 100,
                hitl_count=i,
                retry_count=0,
                success=True
            )
        
        metrics = collector.get_aggregate_metrics(
            crude_score=75,
            esr=0.95,
            mc=0.90,
            zdi=0
        )
        
        # Verify all steps have no token fields
        assert len(metrics['steps']) == 3
        for step in metrics['steps']:
            assert 'tokens_in' not in step
            assert 'tokens_out' not in step
            assert 'api_calls' not in step
            assert 'cached_tokens' not in step
    
    def test_aggregate_metrics_have_zero_tokens(self, mock_dependencies):
        """Test that aggregate_metrics initialize tokens to zero (reconciled post-run)."""
        collector = MetricsCollector(run_id="test_run_003")
        
        collector.record_step(
            step_num=1,
            duration_seconds=35.2,
            start_timestamp=1761523200,
            end_timestamp=1761523235,
            hitl_count=0,
            retry_count=0,
            success=True
        )
        
        metrics = collector.get_aggregate_metrics(
            crude_score=75,
            esr=0.95,
            mc=0.90,
            zdi=0
        )
        
        # Aggregate metrics should have zero tokens (reconciled later)
        assert metrics['aggregate_metrics']['TOK_IN'] == 0
        assert metrics['aggregate_metrics']['TOK_OUT'] == 0
        assert metrics['aggregate_metrics']['API_CALLS'] == 0
        assert metrics['aggregate_metrics']['CACHED_TOKENS'] == 0
    
    def test_save_metrics_schema_validation(self, mock_dependencies, tmp_path):
        """Test that save_metrics() validates clean schema (fail-fast)."""
        collector = MetricsCollector(run_id="test_run_004")
        
        # Record valid step
        collector.record_step(
            step_num=1,
            duration_seconds=35.2,
            start_timestamp=1761523200,
            end_timestamp=1761523235,
            hitl_count=0,
            retry_count=0,
            success=True
        )
        
        # Should save successfully (no token fields in steps)
        output_path = tmp_path / "metrics.json"
        collector.save_metrics(
            output_path=output_path,
            run_id="test_run_001",
            framework="baes",
            start_timestamp=1761523200,
            end_timestamp=1761523500
        )
        
        # Verify file was created and has clean schema
        assert output_path.exists()
        
        with open(output_path) as f:
            saved_metrics = json.load(f)
        
        # Verify steps have no token fields
        for step in saved_metrics['steps']:
            assert 'tokens_in' not in step
            assert 'tokens_out' not in step
            assert 'api_calls' not in step
            assert 'cached_tokens' not in step
    
    def test_save_metrics_rejects_token_fields(self, mock_dependencies, tmp_path):
        """Test that save_metrics() raises ValueError if steps contain token fields."""
        collector = MetricsCollector(run_id="test_run_005")
        
        # Manually inject forbidden token field into steps_data (simulates bug)
        collector.steps_data[1] = {
            'step': 1,
            'duration_seconds': 35.2,
            'tokens_in': 100,  # FORBIDDEN FIELD
            'success': True
        }
        
        output_path = tmp_path / "metrics.json"
        
        # Should raise ValueError (fail-fast validation)
        with pytest.raises(ValueError, match="tokens_in"):
            collector.save_metrics(
                output_path=output_path,
                run_id="test_run_001",
                framework="baes",
                start_timestamp=1761523200,
                end_timestamp=1761523500
            )
    
    def test_compute_efficiency_metrics_returns_zeros(self, mock_dependencies):
        """Test that compute_efficiency_metrics() returns zeros for tokens."""
        collector = MetricsCollector(run_id="test_run_006")
        
        collector.record_step(
            step_num=1,
            duration_seconds=35.2,
            start_timestamp=1761523200,
            end_timestamp=1761523235,
            hitl_count=0,
            retry_count=0,
            success=True
        )
        
        efficiency = collector.compute_efficiency_metrics()
        
        # Should return zeros (tokens reconciled post-run)
        assert efficiency['TOK_IN'] == 0
        assert efficiency['TOK_OUT'] == 0
        assert efficiency['API_CALLS'] == 0
        assert efficiency['CACHED_TOKENS'] == 0
