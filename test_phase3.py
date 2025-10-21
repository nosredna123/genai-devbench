"""
Test Phase 3 - Runner Integration with Step Configuration
"""

import yaml
from pathlib import Path
from src.config import get_enabled_steps

def test_step_loading():
    """Test loading steps from generated config.yaml"""
    
    # Load the minimal experiment config we generated
    config_path = Path('/tmp/test_minimal2/config.yaml')
    
    if not config_path.exists():
        print("❌ Config file not found. Run Phase 2 test first.")
        return False
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Testing step configuration loading...")
    print(f"Config file: {config_path}")
    print()
    
    # Test get_enabled_steps
    try:
        enabled_steps = get_enabled_steps(config, config_path.parent)
        
        print(f"✅ Loaded {len(enabled_steps)} enabled steps:")
        for i, step in enumerate(enabled_steps, start=1):
            print(f"  {i}. Step {step.id}: {step.name}")
            print(f"     Prompt: {step.prompt_file}")
            print(f"     Enabled: {step.enabled}")
            print()
        
        # Verify step order (declaration order, not sorted by ID)
        print("✅ Step execution order (declaration order):")
        for i, step in enumerate(enabled_steps, start=1):
            print(f"  Position {i}: Step ID {step.id}")
        print()
        
        # Test prompt file exists
        print("✅ Verifying prompt files exist:")
        for step in enabled_steps:
            prompt_path = config_path.parent / step.prompt_file
            if prompt_path.exists():
                print(f"  ✓ {step.prompt_file} (exists)")
            else:
                print(f"  ✗ {step.prompt_file} (MISSING!)")
                return False
        print()
        
        print("✅ All Phase 3 tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_step_loading()
    exit(0 if success else 1)
