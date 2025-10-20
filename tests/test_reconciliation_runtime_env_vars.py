"""
Test that reconciliation reads environment variables at runtime, not module load time.

This ensures that changes to .env files are respected without restarting Python processes.
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest import mock

from src.orchestrator.usage_reconciler import UsageReconciler


def test_count_stable_verifications_reads_interval_at_runtime():
    """Test that _count_stable_verifications reads RECONCILIATION_VERIFICATION_INTERVAL_MIN at runtime."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        reconciler = UsageReconciler(runs_dir=runs_dir)
        
        # Create two attempts with 5-minute gap
        now = datetime.now(timezone.utc)
        earlier = now.replace(hour=now.hour-1) if now.hour > 0 else now
        
        attempt1 = {
            'timestamp': earlier.isoformat(),
            'total_tokens_in': 1000,
            'total_tokens_out': 500
        }
        
        attempt2 = {
            'timestamp': now.isoformat(),
            'total_tokens_in': 1000,  # Same tokens
            'total_tokens_out': 500
        }
        
        # Test with INTERVAL_MIN=0 (should count as stable)
        with mock.patch.dict(os.environ, {'RECONCILIATION_VERIFICATION_INTERVAL_MIN': '0'}):
            stable_count = reconciler._count_stable_verifications([attempt1], attempt2)
            assert stable_count == 1, "With INTERVAL_MIN=0, 5-minute gap should count as stable"
        
        # Test with INTERVAL_MIN=120 (2 hours, should NOT count as stable since gap is ~1 hour)
        with mock.patch.dict(os.environ, {'RECONCILIATION_VERIFICATION_INTERVAL_MIN': '120'}):
            stable_count = reconciler._count_stable_verifications([attempt1], attempt2)
            assert stable_count == 0, "With INTERVAL_MIN=120, 1-hour gap should NOT count as stable"


def test_check_verification_status_reads_min_verifications_at_runtime():
    """Test that _check_verification_status reads RECONCILIATION_MIN_STABLE_VERIFICATIONS at runtime."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        # Create a mock run directory
        framework = "baes"
        run_id = "test123"
        run_dir = runs_dir / framework / run_id
        run_dir.mkdir(parents=True)
        
        reconciler = UsageReconciler(runs_dir=runs_dir)
        
        # Create metrics with one previous attempt
        now = datetime.now(timezone.utc)
        earlier = now.replace(hour=now.hour-1) if now.hour > 0 else now
        
        attempt1 = {
            'timestamp': earlier.isoformat(),
            'total_tokens_in': 1000,
            'total_tokens_out': 500,
            'steps_with_tokens': 6,
            'total_steps': 6
        }
        
        current_attempt = {
            'timestamp': now.isoformat(),
            'total_tokens_in': 1000,  # Same tokens - stable!
            'total_tokens_out': 500,
            'steps_with_tokens': 6,
            'total_steps': 6
        }
        
        metrics = {
            'usage_api_reconciliation': {
                'verification_status': 'pending',
                'attempts': [attempt1]
            }
        }
        
        # Test with MIN_STABLE_VERIFICATIONS=1 (should verify after 1 stable check)
        with mock.patch.dict(os.environ, {
            'RECONCILIATION_VERIFICATION_INTERVAL_MIN': '0',
            'RECONCILIATION_MIN_STABLE_VERIFICATIONS': '1'
        }):
            result = reconciler._check_verification_status(metrics, current_attempt, framework, run_id)
            assert result['status'] == 'verified', \
                "With MIN_STABLE_VERIFICATIONS=1, should verify after 1 stable check"
            assert '1 stable checks' in result['message']
        
        # Test with MIN_STABLE_VERIFICATIONS=2 (should still be pending, need more checks)
        with mock.patch.dict(os.environ, {
            'RECONCILIATION_VERIFICATION_INTERVAL_MIN': '0',
            'RECONCILIATION_MIN_STABLE_VERIFICATIONS': '2'
        }):
            result = reconciler._check_verification_status(metrics, current_attempt, framework, run_id)
            assert result['status'] == 'pending', \
                "With MIN_STABLE_VERIFICATIONS=2, should be pending after only 1 stable check"
            assert '1/2 stable checks' in result['message']


def test_runtime_env_vars_respected_immediately():
    """Test that changing environment variables takes effect immediately (no restart needed)."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = Path(tmpdir) / "runs"
        runs_dir.mkdir()
        
        reconciler = UsageReconciler(runs_dir=runs_dir)
        
        # Create attempts with 5-minute gap
        now = datetime.now(timezone.utc)
        earlier = now.replace(minute=now.minute-5) if now.minute >= 5 else now.replace(hour=now.hour-1, minute=55)
        
        attempt1 = {
            'timestamp': earlier.isoformat(),
            'total_tokens_in': 1000,
            'total_tokens_out': 500
        }
        
        attempt2 = {
            'timestamp': now.isoformat(),
            'total_tokens_in': 1000,
            'total_tokens_out': 500
        }
        
        # First call: INTERVAL_MIN=0, should count as stable
        with mock.patch.dict(os.environ, {'RECONCILIATION_VERIFICATION_INTERVAL_MIN': '0'}):
            stable_count1 = reconciler._count_stable_verifications([attempt1], attempt2)
        
        # Second call: INTERVAL_MIN=10 (10 minutes), should NOT count (gap is only 5 min)
        with mock.patch.dict(os.environ, {'RECONCILIATION_VERIFICATION_INTERVAL_MIN': '10'}):
            stable_count2 = reconciler._count_stable_verifications([attempt1], attempt2)
        
        assert stable_count1 == 1, "First call with INTERVAL_MIN=0 should count as stable"
        assert stable_count2 == 0, "Second call with INTERVAL_MIN=10 should NOT count (gap too small)"


if __name__ == "__main__":
    # Run tests
    print("Testing runtime environment variable reading...")
    
    print("\n1. Testing _count_stable_verifications reads INTERVAL_MIN at runtime...")
    test_count_stable_verifications_reads_interval_at_runtime()
    print("✓ PASS")
    
    print("\n2. Testing _check_verification_status reads MIN_VERIFICATIONS at runtime...")
    test_check_verification_status_reads_min_verifications_at_runtime()
    print("✓ PASS")
    
    print("\n3. Testing env vars are respected immediately...")
    test_runtime_env_vars_respected_immediately()
    print("✓ PASS")
    
    print("\n✅ All tests passed!")
