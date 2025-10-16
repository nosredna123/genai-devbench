"""
Pytest configuration and fixtures.

This file is automatically loaded by pytest before running tests.
It ensures proper environment setup including loading .env files.
"""

import os
import sys
from pathlib import Path
import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """
    Pytest hook called after command line options have been parsed.
    This is the best place to load environment variables.
    """
    # Load environment variables from .env file if it exists
    env_file = PROJECT_ROOT / ".env"
    
    if env_file.exists():
        print(f"\n✅ Loading environment variables from {env_file}")
        load_env_file(env_file)
    else:
        print(f"\n⚠️  No .env file found at {env_file}")
        print(f"   Using .env.example as template (API calls will be mocked)")
        # Optionally load .env.example for testing
        env_example = PROJECT_ROOT / ".env.example"
        if env_example.exists():
            load_env_file(env_example)


def load_env_file(env_path: Path):
    """
    Load environment variables from a file.
    
    Args:
        env_path: Path to the .env file
    """
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Only set if not already in environment (allow override)
                if key not in os.environ:
                    os.environ[key] = value


@pytest.fixture(scope="session")
def project_root():
    """Provide the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        'project_root': PROJECT_ROOT,
        'env_loaded': (PROJECT_ROOT / ".env").exists(),
        'mock_mode': not (PROJECT_ROOT / ".env").exists(),
    }


def pytest_report_header(config):
    """Add custom header information to pytest output."""
    env_status = "✅ Loaded" if (PROJECT_ROOT / ".env").exists() else "⚠️  Missing (using mocks)"
    return [
        f"Project root: {PROJECT_ROOT}",
        f"Environment file: {env_status}",
        f"Python path includes project root: {str(PROJECT_ROOT) in sys.path}",
    ]
