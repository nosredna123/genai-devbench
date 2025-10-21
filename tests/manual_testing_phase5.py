"""
Manual testing script for Phase 5 - Config Sets & Configurable Steps

This script performs comprehensive manual testing of the implemented system.
"""

import sys
from pathlib import Path
import yaml
import shutil
import tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_sets.loader import ConfigSetLoader
from src.config import get_enabled_steps


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_1_list_config_sets():
    """Test 1: List available config sets."""
    print_section("TEST 1: List Available Config Sets")
    
    # Go up one level from tests/ to project root
    project_root = Path(__file__).parent.parent
    config_sets_dir = project_root / "config_sets"
    loader = ConfigSetLoader(config_sets_dir)
    
    names = loader.list_available()
    print(f"✓ Found {len(names)} config sets:")
    for name in names:
        print(f"  - {name}")
    
    assert len(names) >= 2, "Should have at least 'default' and 'minimal'"
    assert "default" in names, "Should have 'default' config set"
    assert "minimal" in names, "Should have 'minimal' config set"
    
    print("\n✅ TEST 1 PASSED")
    return True


def test_2_load_config_sets():
    """Test 2: Load and validate config sets."""
    print_section("TEST 2: Load and Validate Config Sets")
    
    project_root = Path(__file__).parent.parent
    config_sets_dir = project_root / "config_sets"
    loader = ConfigSetLoader(config_sets_dir)
    
    # Load default
    print("Loading 'default' config set...")
    default_cs = loader.load("default")
    print(f"✓ Name: {default_cs.name}")
    print(f"✓ Description: {default_cs.description}")
    print(f"✓ Version: {default_cs.version}")
    print(f"✓ Steps: {len(default_cs.available_steps)}")
    
    assert default_cs.name == "default"
    assert len(default_cs.available_steps) == 6
    
    # Load minimal
    print("\nLoading 'minimal' config set...")
    minimal_cs = loader.load("minimal")
    print(f"✓ Name: {minimal_cs.name}")
    print(f"✓ Description: {minimal_cs.description}")
    print(f"✓ Steps: {len(minimal_cs.available_steps)}")
    
    assert minimal_cs.name == "minimal"
    assert len(minimal_cs.available_steps) == 1
    
    print("\n✅ TEST 2 PASSED")
    return True


def test_3_declaration_order():
    """Test 3: Declaration order execution."""
    print_section("TEST 3: Declaration Order Execution")
    
    # Create temporary experiment with proper structure
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create config directory with prompts
        config_dir = temp_dir / "config" / "prompts"
        config_dir.mkdir(parents=True)
        
        # Create dummy prompt files
        for i in [1, 3, 5, 7]:
            (config_dir / f"0{i}.txt").write_text(f"Prompt {i}")
        
        # Create config with non-sequential IDs in custom order
        config = {
            "steps": [
                {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"},
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"},
                {"id": 7, "name": "Step 7", "enabled": True, "prompt_file": "config/prompts/07.txt"}
            ]
        }
        
        print("Config order (declaration):")
        for step in config["steps"]:
            print(f"  - Step {step['id']}: {step['name']}")
        
        # Get enabled steps
        enabled = get_enabled_steps(config, temp_dir)
        
        print("\nExecution order (should match declaration):")
        execution_ids = []
        for step in enabled:
            print(f"  - Step {step.id}: {step.name}")
            execution_ids.append(step.id)
        
        # Verify order matches declaration, not sorted by ID
        expected_order = [5, 1, 3, 7]
        assert execution_ids == expected_order, f"Expected {expected_order}, got {execution_ids}"
        
        print("\n✓ Execution order matches declaration order (not sorted by ID)")
        print("\n✅ TEST 3 PASSED")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_4_step_enable_disable():
    """Test 4: Enable/disable steps."""
    print_section("TEST 4: Enable/Disable Steps")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create config directory with prompts
        config_dir = temp_dir / "config" / "prompts"
        config_dir.mkdir(parents=True)
        
        # Create dummy prompt files
        for i in range(1, 6):
            (config_dir / f"0{i}.txt").write_text(f"Prompt {i}")
        
        # Create config with some disabled steps
        config = {
            "steps": [
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
                {"id": 2, "name": "Step 2", "enabled": False, "prompt_file": "config/prompts/02.txt"},  # Disabled
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"},
                {"id": 4, "name": "Step 4", "enabled": False, "prompt_file": "config/prompts/04.txt"},  # Disabled
                {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"}
            ]
        }
        
        print("All steps:")
        for step in config["steps"]:
            status = "✓ Enabled" if step["enabled"] else "✗ Disabled"
            print(f"  - Step {step['id']}: {step['name']} [{status}]")
        
        # Get enabled steps
        enabled = get_enabled_steps(config, temp_dir)
        
        print("\nSteps that will execute:")
        enabled_ids = []
        for step in enabled:
            print(f"  - Step {step.id}: {step.name}")
            enabled_ids.append(step.id)
        
        # Verify only enabled steps are included
        expected_ids = [1, 3, 5]
        assert enabled_ids == expected_ids, f"Expected {expected_ids}, got {enabled_ids}"
        
        print(f"\n✓ Only {len(enabled)} enabled steps will execute (skipped 2 disabled)")
        print("\n✅ TEST 4 PASSED")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_5_step_id_preservation():
    """Test 5: Original step IDs are preserved."""
    print_section("TEST 5: Step ID Preservation")
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create config directory with prompts
        config_dir = temp_dir / "config" / "prompts"
        config_dir.mkdir(parents=True)
        
        # Create dummy prompt files
        for i in [10, 25, 99]:
            (config_dir / f"{i}.txt").write_text(f"Prompt {i}")
        
        # Create config with gaps in IDs
        config = {
            "steps": [
                {"id": 10, "name": "Step 10", "enabled": True, "prompt_file": "config/prompts/10.txt"},
                {"id": 25, "name": "Step 25", "enabled": True, "prompt_file": "config/prompts/25.txt"},
                {"id": 99, "name": "Step 99", "enabled": True, "prompt_file": "config/prompts/99.txt"}
            ]
        }
        
        print("Original step IDs (non-sequential):")
        for step in config["steps"]:
            print(f"  - ID {step['id']}: {step['name']}")
        
        # Get enabled steps
        enabled = get_enabled_steps(config, temp_dir)
        
        print("\nStep IDs after loading:")
        actual_ids = []
        for step in enabled:
            print(f"  - ID {step.id}: {step.name}")
            actual_ids.append(step.id)
        
        # Verify IDs are preserved exactly
        expected_ids = [10, 25, 99]
        assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"
        
        print("\n✓ Original step IDs are preserved for metrics")
        print("\n✅ TEST 5 PASSED")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_6_config_set_files():
    """Test 6: Config set files structure."""
    print_section("TEST 6: Config Set Files Structure")
    
    project_root = Path(__file__).parent.parent
    config_sets_dir = project_root / "config_sets"
    
    # Check default config set
    print("Checking 'default' config set...")
    default_dir = config_sets_dir / "default"
    
    required_files = [
        "metadata.yaml",
        "experiment_template.yaml",
        "prompts",
        "hitl"
    ]
    
    for file_name in required_files:
        file_path = default_dir / file_name
        status = "✓" if file_path.exists() else "✗"
        print(f"  {status} {file_name}")
        assert file_path.exists(), f"Missing {file_name}"
    
    # Check prompts
    prompts_dir = default_dir / "prompts"
    prompt_files = sorted(prompts_dir.glob("*.txt"))
    print(f"\n  Found {len(prompt_files)} prompt files:")
    for pf in prompt_files:
        print(f"    - {pf.name}")
    
    assert len(prompt_files) == 6, "Default should have 6 prompts"
    
    # Check minimal config set
    print("\nChecking 'minimal' config set...")
    minimal_dir = config_sets_dir / "minimal"
    
    for file_name in required_files:
        file_path = minimal_dir / file_name
        status = "✓" if file_path.exists() else "✗"
        print(f"  {status} {file_name}")
        assert file_path.exists(), f"Missing {file_name}"
    
    prompts_dir = minimal_dir / "prompts"
    prompt_files = sorted(prompts_dir.glob("*.txt"))
    print(f"\n  Found {len(prompt_files)} prompt files:")
    for pf in prompt_files:
        print(f"    - {pf.name}")
    
    assert len(prompt_files) == 1, "Minimal should have 1 prompt"
    
    print("\n✅ TEST 6 PASSED")
    return True


def main():
    """Run all manual tests."""
    print("\n" + "="*70)
    print("  PHASE 5 MANUAL TESTING")
    print("  Config Sets + Configurable Steps")
    print("="*70)
    
    tests = [
        ("List Config Sets", test_1_list_config_sets),
        ("Load Config Sets", test_2_load_config_sets),
        ("Declaration Order", test_3_declaration_order),
        ("Enable/Disable Steps", test_4_step_enable_disable),
        ("Step ID Preservation", test_5_step_id_preservation),
        ("Config Set Files", test_6_config_set_files)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print_section("TESTING SUMMARY")
    print(f"✅ Passed: {passed}/{len(tests)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(tests)}")
    else:
        print("🎉 ALL TESTS PASSED!")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
