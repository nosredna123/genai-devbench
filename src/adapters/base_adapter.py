"""
Abstract base adapter for LLM framework integrations.

Defines the contract that all framework adapters must implement.
"""

from abc import ABC, abstractmethod
import subprocess
import time
import os
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
from datetime import datetime, timezone
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAdapter(ABC):
    """Abstract interface for LLM framework adapters."""
    
    def __init__(self, config: Dict[str, Any], run_id: str, workspace_path: str):
        """
        Initialize adapter with configuration and run context.
        
        Args:
            config: Framework-specific settings from experiment.yaml
            run_id: Unique run identifier (UUID)
            workspace_path: Isolated directory for this run
        """
        self.config = config
        self.run_id = run_id
        self.workspace_path = workspace_path
        self.current_step = 0
        self._step_start_time: Optional[float] = None  # Track step execution start time
    
    def fetch_usage_from_openai(
        self,
        api_key_env_var: str,
        start_timestamp: int,
        end_timestamp: Optional[int] = None,
        model: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Fetch token usage from OpenAI Usage API.
        
        This is a general, DRY method that works for ALL frameworks (ChatDev, GHSpec, BAEs)
        by querying OpenAI's Usage API directly instead of parsing framework-specific logs.
        
        Args:
            api_key_env_var: Environment variable name containing the OpenAI API key
            start_timestamp: Unix timestamp (seconds) when step execution started
            end_timestamp: Unix timestamp (seconds) when step execution ended (defaults to now)
            model: Optional model filter (e.g., "gpt-4o-mini", "gpt-5-mini")
            
        Returns:
            Tuple of (tokens_in, tokens_out)
            
        Note:
            - Uses organization/usage/completions endpoint
            - Aggregates all API calls within the time window
            - Returns (0, 0) if API call fails or no usage found
        """
        try:
            import requests
            
            # Get API key from environment
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                logger.warning(
                    f"API key not found in environment variable: {api_key_env_var}",
                    extra={'run_id': self.run_id}
                )
                return 0, 0
            
            # Use current time if end_timestamp not provided
            if end_timestamp is None:
                end_timestamp = int(time.time())
            
            # Build API request
            url = "https://api.openai.com/v1/organization/usage/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "start_time": start_timestamp,
                "end_time": end_timestamp,
                "bucket_width": "1d",  # Use daily bucket
                "limit": 31  # Get last month of data
            }
            
            # Add model filter if specified
            if model:
                params["models"] = [model]
            
            logger.debug(
                "Querying OpenAI Usage API",
                extra={
                    'run_id': self.run_id,
                    'metadata': {
                        'start_time': start_timestamp,
                        'end_time': end_timestamp,
                        'start_dt': datetime.fromtimestamp(start_timestamp, tz=timezone.utc).isoformat(),
                        'end_dt': datetime.fromtimestamp(end_timestamp, tz=timezone.utc).isoformat(),
                        'model': model
                    }
                }
            )
            
            # Make API request
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Check for permission errors before raising
            if response.status_code == 401:
                error_data = response.json()
                if "api.usage.read" in error_data.get("error", {}).get("message", ""):
                    logger.error(
                        "API key lacks 'api.usage.read' scope for Usage API",
                        extra={
                            'run_id': self.run_id,
                            'metadata': {
                                'api_key_env_var': api_key_env_var,
                                'error': error_data.get("error", {}).get("message", ""),
                                'fix': 'Grant api.usage.read scope to the API key in OpenAI dashboard'
                            }
                        }
                    )
                    return 0, 0  # Return zeros instead of failing
            
            response.raise_for_status()
            usage_data = response.json()
            
            # Aggregate tokens from all buckets
            # Note: OpenAI Usage API uses n_context_tokens_total and n_generated_tokens_total
            total_input_tokens = 0
            total_output_tokens = 0
            
            for bucket in usage_data.get("data", []):
                for result in bucket.get("results", []):
                    total_input_tokens += result.get("n_context_tokens_total", 0)
                    total_output_tokens += result.get("n_generated_tokens_total", 0)
            
            logger.info(
                "Token usage fetched from OpenAI Usage API",
                extra={
                    'run_id': self.run_id,
                    'step': self.current_step,
                    'metadata': {
                        'tokens_in': total_input_tokens,
                        'tokens_out': total_output_tokens,
                        'buckets_count': len(usage_data.get("data", [])),
                        'model': model
                    }
                }
            )
            
            return total_input_tokens, total_output_tokens
            
        except Exception as e:
            logger.error(
                f"Failed to fetch usage from OpenAI API: {e}",
                extra={
                    'run_id': self.run_id,
                    'metadata': {
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                }
            )
            # Return 0, 0 on error - non-critical for test execution
            return 0, 0
    
    def verify_commit_hash(self, repo_path: Path, expected_hash: str) -> None:
        """
        Verify cloned repository is at expected commit hash.
        
        Ensures reproducibility by checking the framework version matches
        what's specified in the configuration. Fails fast if mismatch detected.
        
        Args:
            repo_path: Path to cloned repository
            expected_hash: Expected commit SHA from config
            
        Raises:
            RuntimeError: If commit hash doesn't match or check fails
        """
        try:
            # Get current HEAD commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            actual_hash = result.stdout.strip()
            
            # Compare hashes (allow short hash matching)
            if not actual_hash.startswith(expected_hash) and not expected_hash.startswith(actual_hash):
                error_msg = (
                    f"Commit hash mismatch! "
                    f"Expected: {expected_hash}, Got: {actual_hash}"
                )
                logger.error(
                    "Framework commit hash verification failed",
                    extra={
                        'run_id': self.run_id,
                        'metadata': {
                            'expected': expected_hash,
                            'actual': actual_hash,
                            'repo_path': str(repo_path)
                        }
                    }
                )
                raise RuntimeError(error_msg)
            
            logger.info(
                "Framework commit hash verified",
                extra={
                    'run_id': self.run_id,
                    'metadata': {
                        'commit_hash': actual_hash,
                        'repo_path': str(repo_path)
                    }
                }
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to verify commit hash: {e}"
            logger.error(
                "Commit hash verification command failed",
                extra={'run_id': self.run_id, 'metadata': {'error': str(e)}}
            )
            raise RuntimeError(error_msg) from e
        except subprocess.TimeoutExpired as e:
            error_msg = "Commit hash verification timed out"
            logger.error(
                error_msg,
                extra={'run_id': self.run_id}
            )
            raise RuntimeError(error_msg) from e
    
    @abstractmethod
    def start(self) -> None:
        """
        Initialize framework environment.
        
        This should:
        - Clone framework repository at specified commit hash
        - Set up virtual environment
        - Install dependencies
        - Start framework services (API, UI)
        
        Raises:
            RuntimeError: If initialization fails
        """
        pass
    
    @abstractmethod
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """
        Send natural language command to framework and wait for completion.
        
        Args:
            step_num: Step number (1-6)
            command_text: Natural language command from prompt file
            
        Returns:
            Dictionary with execution results:
                {
                    'success': bool,
                    'duration_seconds': float,
                    'hitl_count': int,
                    'tokens_in': int,
                    'tokens_out': int
                }
                
        Raises:
            TimeoutError: If step exceeds configured timeout
            RuntimeError: If execution fails
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if framework API/UI are responding.
        
        Returns:
            True if both API and UI return HTTP 200, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_hitl(self, query: str) -> str:
        """
        Respond to framework clarification request with fixed text.
        
        This ensures deterministic HITL responses across all runs.
        
        Args:
            query: Framework's clarification question
            
        Returns:
            Deterministic clarification text from config/hitl/expanded_spec.txt
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """
        Gracefully shutdown framework processes and cleanup.
        
        This should:
        - Stop framework services
        - Cleanup temporary files (keep workspace intact)
        - Remove Docker containers if used
        """
        pass
