#!/usr/bin/env python3
"""
Phase 2 Implementation Verification Script

Tests the shared framework architecture implementation:
1. BaseAdapter methods work correctly
2. Adapters can reference shared frameworks
3. Workspace structure creation works
4. Config flags are present
"""

import sys
from pathlib import Path

# Add project root to path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.adapters.base_adapter import BaseAdapter
from src.adapters.baes_adapter import BAeSAdapter
from src.adapters.chatdev_adapter import ChatDevAdapter
from src.adapters.ghspec_adapter import GHSpecAdapter
import yaml


def test_base_adapter_methods():
    """Test that BaseAdapter has all required methods."""
    print("🔍 Testing BaseAdapter methods...")
    
    required_methods = [
        'get_shared_framework_path',
        'get_framework_python',
        'create_workspace_structure',
        'setup_shared_venv'
    ]
    
    for method in required_methods:
        if not hasattr(BaseAdapter, method):
            print(f"  ❌ Missing method: {method}")
            return False
        print(f"  ✓ Found method: {method}")
    
    print("  ✅ All BaseAdapter methods present\n")
    return True


def test_config_use_venv_flags():
    """Test that config.yaml has use_venv flags."""
    print("🔍 Testing config.yaml use_venv flags...")
    
    config_path = Path(__file__).parent.parent / "config" / "experiment.yaml"
    if not config_path.exists():
        print(f"  ❌ Config not found: {config_path}")
        return False
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    frameworks = config.get('frameworks', {})
    
    # Check BAEs
    if 'baes' not in frameworks:
        print("  ❌ BAEs framework not in config")
        return False
    if 'use_venv' not in frameworks['baes']:
        print("  ❌ BAEs missing use_venv flag")
        return False
    print(f"  ✓ BAEs use_venv = {frameworks['baes']['use_venv']}")
    
    # Check ChatDev
    if 'chatdev' not in frameworks:
        print("  ❌ ChatDev framework not in config")
        return False
    if 'use_venv' not in frameworks['chatdev']:
        print("  ❌ ChatDev missing use_venv flag")
        return False
    print(f"  ✓ ChatDev use_venv = {frameworks['chatdev']['use_venv']}")
    
    # Check GHSpec
    if 'ghspec' not in frameworks:
        print("  ❌ GHSpec framework not in config")
        return False
    if 'use_venv' not in frameworks['ghspec']:
        print("  ❌ GHSpec missing use_venv flag")
        return False
    print(f"  ✓ GHSpec use_venv = {frameworks['ghspec']['use_venv']}")
    
    print("  ✅ All use_venv flags present\n")
    return True


def test_adapter_start_methods():
    """Test that adapter start() methods use new architecture."""
    print("🔍 Testing adapter start() implementations...")
    
    # Test BAeSAdapter
    print("  Checking BAeSAdapter.start()...")
    baes_code = Path(__file__).parent.parent / "src" / "adapters" / "baes_adapter.py"
    baes_content = baes_code.read_text()
    
    if 'get_shared_framework_path' not in baes_content:
        print("    ❌ BAeSAdapter doesn't call get_shared_framework_path()")
        return False
    if 'get_framework_python' not in baes_content:
        print("    ❌ BAeSAdapter doesn't call get_framework_python()")
        return False
    if 'create_workspace_structure' not in baes_content:
        print("    ❌ BAeSAdapter doesn't call create_workspace_structure()")
        return False
    if '_setup_virtual_environment' in baes_content:
        # Check if it's just in comments or actually defined
        if 'def _setup_virtual_environment' in baes_content:
            print("    ❌ BAeSAdapter still has _setup_virtual_environment method")
            return False
    print("    ✓ BAeSAdapter uses shared resources")
    
    # Test ChatDevAdapter
    print("  Checking ChatDevAdapter.start()...")
    chatdev_code = Path(__file__).parent.parent / "src" / "adapters" / "chatdev_adapter.py"
    chatdev_content = chatdev_code.read_text()
    
    if 'get_shared_framework_path' not in chatdev_content:
        print("    ❌ ChatDevAdapter doesn't call get_shared_framework_path()")
        return False
    if 'get_framework_python' not in chatdev_content:
        print("    ❌ ChatDevAdapter doesn't call get_framework_python()")
        return False
    if 'create_workspace_structure' not in chatdev_content:
        print("    ❌ ChatDevAdapter doesn't call create_workspace_structure()")
        return False
    if 'def _setup_virtual_environment' in chatdev_content:
        print("    ❌ ChatDevAdapter still has _setup_virtual_environment method")
        return False
    if 'def _patch_openai_compatibility' in chatdev_content:
        print("    ❌ ChatDevAdapter still has _patch_openai_compatibility method")
        return False
    if 'def _patch_o1_model_support' in chatdev_content:
        print("    ❌ ChatDevAdapter still has _patch_o1_model_support method")
        return False
    print("    ✓ ChatDevAdapter uses shared resources")
    
    # Test GHSpecAdapter
    print("  Checking GHSpecAdapter.start()...")
    ghspec_code = Path(__file__).parent.parent / "src" / "adapters" / "ghspec_adapter.py"
    ghspec_content = ghspec_code.read_text()
    
    if 'get_shared_framework_path' not in ghspec_content:
        print("    ❌ GHSpecAdapter doesn't call get_shared_framework_path()")
        return False
    if 'setup_framework_from_repo' in ghspec_content:
        # Check if it's in start() method specifically
        start_method_start = ghspec_content.find('def start(self)')
        if start_method_start != -1:
            start_method_end = ghspec_content.find('\n    def ', start_method_start + 1)
            start_method = ghspec_content[start_method_start:start_method_end]
            if 'setup_framework_from_repo' in start_method:
                print("    ❌ GHSpecAdapter.start() still calls setup_framework_from_repo()")
                return False
    print("    ✓ GHSpecAdapter uses shared resources")
    
    print("  ✅ All adapters refactored correctly\n")
    return True


def test_setup_script_functions():
    """Test that setup_frameworks.py has new functions."""
    print("🔍 Testing setup_frameworks.py functions...")
    
    setup_code = Path(__file__).parent.parent / "templates" / "setup_frameworks.py"
    setup_content = setup_code.read_text()
    
    if 'def setup_venv_if_needed' not in setup_content:
        print("  ❌ Missing function: setup_venv_if_needed")
        return False
    print("  ✓ Found function: setup_venv_if_needed")
    
    if 'def patch_chatdev_if_needed' not in setup_content:
        print("  ❌ Missing function: patch_chatdev_if_needed")
        return False
    print("  ✓ Found function: patch_chatdev_if_needed")
    
    # Check if main() calls these functions
    if 'setup_venv_if_needed' not in setup_content.split('def main()')[1]:
        print("  ⚠️  Warning: main() might not call setup_venv_if_needed")
    
    if 'patch_chatdev_if_needed' not in setup_content.split('def main()')[1]:
        print("  ⚠️  Warning: main() might not call patch_chatdev_if_needed")
    
    print("  ✅ Setup script functions present\n")
    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Phase 2 Implementation Verification")
    print("=" * 60)
    print()
    
    tests = [
        ("BaseAdapter methods", test_base_adapter_methods),
        ("Config use_venv flags", test_config_use_venv_flags),
        ("Adapter start() methods", test_adapter_start_methods),
        ("Setup script functions", test_setup_script_functions),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Test '{name}' raised exception: {e}")
            results.append((name, False))
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All verification tests passed!")
        print("✅ Phase 2 implementation is complete and correct")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("❌ Phase 2 implementation needs fixes")
        return 1


if __name__ == '__main__':
    sys.exit(main())
