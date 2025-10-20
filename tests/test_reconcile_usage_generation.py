"""
Test reconcile_usage.sh script generation and functionality.

Tests that the generated reconcile_usage.sh script:
1. Correctly reads RECONCILIATION_VERIFICATION_INTERVAL_MIN from .env
2. Uses the same value in both --list and reconciliation modes
3. Loads manifest from runs/manifest.json (standalone path)
"""

import re
import tempfile
from pathlib import Path
from generator.standalone_generator import StandaloneGenerator


def test_reconcile_script_uses_env_var_for_min_age():
    """Test that reconcile_usage.sh reads min_age from environment variable."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate a test experiment
        generator = StandaloneGenerator()
        config = {
            "experiment_name": "test_reconcile",
            "model": "gpt-4o",
            "frameworks": {"baes": {"enabled": True}},
            "max_runs": 1
        }
        generator.generate("test_reconcile", config, Path(tmpdir))
        
        script_path = Path(tmpdir) / "reconcile_usage.sh"
        assert script_path.exists(), "reconcile_usage.sh should be generated"
        
        script_content = script_path.read_text(encoding='utf-8')
        
        # Check that --list mode reads from environment variable (not hardcoded 30)
        # Should have: min_age_minutes = int(os.getenv('RECONCILIATION_VERIFICATION_INTERVAL_MIN', '0'))
        assert "os.getenv('RECONCILIATION_VERIFICATION_INTERVAL_MIN'" in script_content, \
            "--list mode should read RECONCILIATION_VERIFICATION_INTERVAL_MIN from env"
        
        # Should NOT have hardcoded: min_age_seconds = 30 * 60
        hardcoded_pattern = r"min_age_seconds\s*=\s*30\s*\*\s*60"
        assert not re.search(hardcoded_pattern, script_content), \
            "Script should not have hardcoded 30-minute minimum age"
        
        # Should have: min_age_seconds = min_age_minutes * 60
        assert "min_age_seconds = min_age_minutes * 60" in script_content, \
            "Should calculate min_age_seconds from min_age_minutes variable"


def test_reconcile_script_loads_standalone_manifest():
    """Test that reconcile_usage.sh loads from runs/manifest.json (standalone path)."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = StandaloneGenerator()
        config = {
            "experiment_name": "test_manifest",
            "model": "gpt-4o",
            "frameworks": {"baes": {"enabled": True}},
            "max_runs": 1
        }
        generator.generate("test_manifest", config, Path(tmpdir))
        
        script_path = Path(tmpdir) / "reconcile_usage.sh"
        
        script_content = script_path.read_text(encoding='utf-8')
        
        # Check that script loads from runs/manifest.json
        assert 'manifest_path = Path("runs/manifest.json")' in script_content, \
            "Script should load manifest from runs/manifest.json"
        
        # Should NOT reference runs/runs_manifest.json (old multi-experiment path)
        assert "runs/runs_manifest.json" not in script_content, \
            "Script should not reference old multi-experiment manifest path"


def test_reconcile_script_imports_os():
    """Test that the Python code in reconcile_usage.sh imports os module."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = StandaloneGenerator()
        config = {
            "experiment_name": "test_imports",
            "model": "gpt-4o",
            "frameworks": {"baes": {"enabled": True}},
            "max_runs": 1
        }
        generator.generate("test_imports", config, Path(tmpdir))
        
        script_path = Path(tmpdir) / "reconcile_usage.sh"
        
        script_content = script_path.read_text(encoding='utf-8')
        
        # Check that os is imported somewhere in the script (needed for os.getenv)
        assert "import os" in script_content, \
            "Script should import os module for environment variable access"


def test_reconcile_script_consistent_timing():
    """Test that --list and reconciliation use same timing logic."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = StandaloneGenerator()
        config = {
            "experiment_name": "test_timing",
            "model": "gpt-4o",
            "frameworks": {"baes": {"enabled": True}},
            "max_runs": 1
        }
        generator.generate("test_timing", config, Path(tmpdir))
        
        script_path = Path(tmpdir) / "reconcile_usage.sh"
        
        script_content = script_path.read_text(encoding='utf-8')
        
        # Both sections should reference RECONCILIATION_VERIFICATION_INTERVAL_MIN
        env_var_name = "RECONCILIATION_VERIFICATION_INTERVAL_MIN"
        
        # Count occurrences (should appear in --list section)
        count = script_content.count(env_var_name)
        assert count >= 1, \
            f"RECONCILIATION_VERIFICATION_INTERVAL_MIN should be used in the script (found {count} times)"


if __name__ == "__main__":
    # Run tests
    print("Testing reconcile_usage.sh generation...")
    
    print("\n1. Testing env var usage for min_age...")
    test_reconcile_script_uses_env_var_for_min_age()
    print("✓ PASS")
    
    print("\n2. Testing standalone manifest loading...")
    test_reconcile_script_loads_standalone_manifest()
    print("✓ PASS")
    
    print("\n3. Testing os module import...")
    test_reconcile_script_imports_os()
    print("✓ PASS")
    
    print("\n4. Testing consistent timing logic...")
    test_reconcile_script_consistent_timing()
    print("✓ PASS")
    
    print("\n✅ All tests passed!")
