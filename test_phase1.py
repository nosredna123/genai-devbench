"""
Basic test to verify Phase 1 implementation.
"""

import yaml
from pathlib import Path
from src.config_sets import ConfigSetLoader
from src.config import get_enabled_steps


def test_config_sets():
    """Test config set loading and validation."""
    print("Testing config sets...")
    
    loader = ConfigSetLoader(Path('config_sets'))
    
    # List available config sets
    available = loader.list_available()
    print(f"Available config sets: {available}")
    assert 'default' in available
    assert 'minimal' in available
    
    # Load default config set
    default_set = loader.load('default')
    print(f"\nDefault config set:")
    print(f"  Name: {default_set.name}")
    print(f"  Version: {default_set.version}")
    print(f"  Steps: {len(default_set.available_steps)}")
    
    assert default_set.name == 'default'
    assert len(default_set.available_steps) == 6
    
    # Load minimal config set
    minimal_set = loader.load('minimal')
    print(f"\nMinimal config set:")
    print(f"  Name: {minimal_set.name}")
    print(f"  Version: {minimal_set.version}")
    print(f"  Steps: {len(minimal_set.available_steps)}")
    
    assert minimal_set.name == 'minimal'
    assert len(minimal_set.available_steps) == 1
    
    print("\n✅ Config set loading tests passed!")


def test_step_config():
    """Test step configuration loading."""
    print("\nTesting step configuration...")
    
    # Load the default template
    template_path = Path('config_sets/default/experiment_template.yaml')
    config = yaml.safe_load(template_path.read_text())
    
    # Get enabled steps
    enabled_steps = get_enabled_steps(config, Path('config_sets/default'))
    
    print(f"Enabled steps: {len(enabled_steps)}")
    for step in enabled_steps:
        print(f"  Step {step.id}: {step.name} ({step.prompt_file})")
    
    assert len(enabled_steps) == 6
    assert enabled_steps[0].id == 1
    assert enabled_steps[0].name == "Student CRUD"
    
    print("\n✅ Step configuration tests passed!")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Phase 1 Implementation Test")
    print("=" * 70)
    
    try:
        test_config_sets()
        test_step_config()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Phase 1 Implementation Complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == '__main__':
    main()
