"""
Configuration loading and validation for BAEs experiment framework.

Loads experiment.yaml and validates schema compliance.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def load_config(config_path: str = "config/experiment.yaml") -> Dict[str, Any]:
    """
    Load and validate experiment configuration from YAML file.
    
    Args:
        config_path: Path to experiment.yaml file
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ConfigValidationError: If configuration is invalid
        FileNotFoundError: If config file doesn't exist
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    validate_config(config)
    logger.info(f"Configuration loaded and validated from {config_path}")
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate experiment configuration schema.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ConfigValidationError: If validation fails
    """
    # Check required top-level keys
    required_keys = ['random_seed', 'frameworks', 'prompts_dir', 'hitl_path', 
                     'stopping_rule', 'timeouts']
    
    for key in required_keys:
        if key not in config:
            raise ConfigValidationError(f"Missing required config key: {key}")
    
    # Validate frameworks section
    if not isinstance(config['frameworks'], dict):
        raise ConfigValidationError("'frameworks' must be a dictionary")
    
    if len(config['frameworks']) == 0:
        raise ConfigValidationError("At least one framework must be configured")
    
    # Validate each framework configuration
    for fw_name, fw_config in config['frameworks'].items():
        validate_framework_config(fw_name, fw_config)
    
    # Validate stopping rule
    validate_stopping_rule(config['stopping_rule'])
    
    # Validate timeouts
    validate_timeouts(config['timeouts'])
    
    # Validate paths exist
    validate_paths(config)


def validate_framework_config(name: str, config: Dict[str, Any]) -> None:
    """
    Validate individual framework configuration.
    
    Args:
        name: Framework name
        config: Framework configuration dictionary
        
    Raises:
        ConfigValidationError: If validation fails
    """
    required_fw_keys = ['repo_url', 'commit_hash', 'api_port', 'ui_port', 'api_key_env']
    
    for key in required_fw_keys:
        if key not in config:
            raise ConfigValidationError(
                f"Framework '{name}' missing required key: {key}"
            )
    
    # Validate port numbers
    if not isinstance(config['api_port'], int) or config['api_port'] <= 0:
        raise ConfigValidationError(
            f"Framework '{name}' api_port must be a positive integer"
        )
    
    if not isinstance(config['ui_port'], int) or config['ui_port'] <= 0:
        raise ConfigValidationError(
            f"Framework '{name}' ui_port must be a positive integer"
        )


def validate_stopping_rule(config: Dict[str, Any]) -> None:
    """
    Validate stopping rule configuration.
    
    Args:
        config: Stopping rule configuration dictionary
        
    Raises:
        ConfigValidationError: If validation fails
    """
    required_keys = ['min_runs', 'max_runs', 'confidence_level', 'max_half_width_pct', 'metrics']
    
    for key in required_keys:
        if key not in config:
            raise ConfigValidationError(
                f"Stopping rule missing required key: {key}"
            )
    
    # Validate numeric ranges
    if config['min_runs'] < 1:
        raise ConfigValidationError("min_runs must be at least 1")
    
    if config['max_runs'] < config['min_runs']:
        raise ConfigValidationError("max_runs must be >= min_runs")
    
    if not (0 < config['confidence_level'] < 1):
        raise ConfigValidationError("confidence_level must be between 0 and 1")
    
    if config['max_half_width_pct'] <= 0:
        raise ConfigValidationError("max_half_width_pct must be positive")
    
    # Validate metrics list
    if not isinstance(config['metrics'], list) or len(config['metrics']) == 0:
        raise ConfigValidationError("metrics must be a non-empty list")


def validate_timeouts(config: Dict[str, Any]) -> None:
    """
    Validate timeouts configuration.
    
    Args:
        config: Timeouts configuration dictionary
        
    Raises:
        ConfigValidationError: If validation fails
    """
    required_keys = ['step_timeout_seconds', 'health_check_interval_seconds', 
                     'api_retry_attempts']
    
    for key in required_keys:
        if key not in config:
            raise ConfigValidationError(
                f"Timeouts missing required key: {key}"
            )
        
        if not isinstance(config[key], int) or config[key] <= 0:
            raise ConfigValidationError(
                f"Timeout '{key}' must be a positive integer"
            )


def validate_paths(config: Dict[str, Any]) -> None:
    """
    Validate that required file paths exist.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ConfigValidationError: If paths don't exist
    """
    # Validate prompts directory
    prompts_dir = Path(config['prompts_dir'])
    if not prompts_dir.exists():
        raise ConfigValidationError(
            f"Prompts directory does not exist: {config['prompts_dir']}"
        )
    
    # Validate prompt files (step_1.txt through step_6.txt)
    for i in range(1, 7):
        prompt_file = prompts_dir / f"step_{i}.txt"
        if not prompt_file.exists():
            raise ConfigValidationError(
                f"Prompt file missing: {prompt_file}"
            )
    
    # Validate HITL path
    hitl_path = Path(config['hitl_path'])
    if not hitl_path.exists():
        raise ConfigValidationError(
            f"HITL file does not exist: {config['hitl_path']}"
        )


def get_framework_config(config: Dict[str, Any], framework: str) -> Dict[str, Any]:
    """
    Get configuration for a specific framework.
    
    Args:
        config: Full configuration dictionary
        framework: Framework name
        
    Returns:
        Framework-specific configuration
        
    Raises:
        KeyError: If framework not found in configuration
    """
    if framework not in config['frameworks']:
        raise KeyError(f"Framework '{framework}' not found in configuration")
    
    return config['frameworks'][framework]
