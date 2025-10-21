"""
Abstract base adapter for LLM framework integrations.

Defines the contract that all framework adapters must implement.
"""

from abc import ABC, abstractmethod
import subprocess
import time
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
from datetime import datetime, timezone
from src.utils.logger import get_logger

logger = get_logger(__name__, component="adapter")


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
    ) -> Tuple[int, int, int, int]:
        """
        Lazy evaluation stub for token usage collection.
        
        LAZY EVALUATION PATTERN:
        This method intentionally returns (0, 0, 0, 0) during step execution.
        Token metrics are collected later by the reconciliation script, which:
        1. Waits for OpenAI Usage API propagation delay (5-15 minutes)
        2. Queries usage data for the entire run window
        3. Attributes tokens to individual steps based on timestamps
        4. Updates metrics.json with verified counts
        
        This approach:
        - Avoids silent failures from API propagation delays
        - Centralizes data collection in one place (DRY principle)
        - Ensures all metrics go through the same verification process
        - Prevents blocking step execution on Usage API availability
        
        Args:
            api_key_env_var: Environment variable name containing the OpenAI API key (unused)
            start_timestamp: Unix timestamp (seconds) when step execution started (unused)
            end_timestamp: Unix timestamp (seconds) when step execution ended (unused)
            model: Optional model filter (unused)
            
        Returns:
            Tuple of (0, 0, 0, 0) - indicating metrics need reconciliation
            
        Note:
            All adapters (BAeS, ChatDev, GHSpec) use this method for consistency.
            The reconciliation script (scripts/reconcile_usage.sh) backfills actual data.
        """
        # LAZY EVALUATION: Return zeros immediately
        # Token metrics will be collected by reconciliation script after Usage API propagation
        logger.debug(
            "Lazy evaluation: returning zero metrics (reconciliation required)",
            extra={
                'run_id': self.run_id,
                'step': self.current_step,
                'metadata': {
                    'start_timestamp': start_timestamp,
                    'end_timestamp': end_timestamp or int(time.time()),
                    'window_seconds': (end_timestamp or int(time.time())) - start_timestamp,
                    'note': 'Metrics will be backfilled by reconciliation script'
                }
            }
        )
        
        return 0, 0, 0, 0
    
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
    
    def setup_framework_from_repo(
        self, 
        framework_name: str,
        target_dir: Path,
        repo_url: str,
        commit_hash: str,
        timeout_clone: int = 300,
        timeout_checkout: int = 60
    ) -> None:
        """
        Setup framework repository from shared directory or clone from URL.
        
        DRY PRINCIPLE: Centralizes framework setup logic used by all adapters.
        This method implements a performance optimization by reusing frameworks
        cloned during setup.sh instead of cloning for every run.
        
        Behavior:
        1. Check if shared framework exists in frameworks/<name>/
        2. If yes: Copy from shared directory (fast, ~1 second)
        3. If no: Clone from repo_url (slow, ~30 seconds)
        4. Checkout specified commit hash
        5. Verify commit hash matches expected value
        
        Performance Impact:
        - Before: ~90 seconds cloning for 3 frameworks per run
        - After: ~3 seconds copying from shared directories
        - Savings: ~87 seconds per run, ~522 seconds per 6-run experiment!
        
        Args:
            framework_name: Framework name (baes, chatdev, ghspec)
            target_dir: Destination directory for framework (run workspace)
            repo_url: Git repository URL or file:// path
            commit_hash: Specific commit to checkout
            timeout_clone: Timeout for git clone operation (seconds)
            timeout_checkout: Timeout for git checkout operation (seconds)
            
        Raises:
            RuntimeError: If setup fails at any stage
        """
        # Check if framework was already cloned in shared frameworks/ directory
        shared_framework_dir = Path('frameworks') / framework_name
        
        try:
            if shared_framework_dir.exists() and (shared_framework_dir / '.git').exists():
                # FAST PATH: Copy from shared directory
                logger.info(
                    f"Reusing shared {framework_name} repository from {shared_framework_dir}",
                    extra={'run_id': self.run_id, 'event': 'framework_reuse'}
                )
                shutil.copytree(shared_framework_dir, target_dir, symlinks=False)
                
            elif repo_url.startswith('file://'):
                # LOCAL PATH: Copy from local repository
                local_path = repo_url[7:]  # Strip 'file://' prefix
                logger.info(
                    f"Copying local {framework_name} repository from {local_path}",
                    extra={'run_id': self.run_id}
                )
                shutil.copytree(local_path, target_dir, symlinks=False)
                
            else:
                # SLOW PATH: Clone from remote URL
                logger.info(
                    f"Cloning {framework_name} repository from {repo_url}",
                    extra={'run_id': self.run_id, 'event': 'framework_clone'}
                )
                subprocess.run(
                    ['git', 'clone', repo_url, str(target_dir)],
                    check=True,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                    timeout=timeout_clone
                )
            
            # Checkout specific commit (needed for all paths)
            if commit_hash != 'HEAD':
                logger.info(
                    f"Checking out commit {commit_hash}",
                    extra={'run_id': self.run_id}
                )
                subprocess.run(
                    ['git', 'checkout', commit_hash],
                    cwd=target_dir,
                    check=True,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                    timeout=timeout_checkout
                )
            
            # Verify commit hash matches configuration
            self.verify_commit_hash(target_dir, commit_hash)
            
            logger.info(
                f"{framework_name} repository setup complete",
                extra={
                    'run_id': self.run_id,
                    'metadata': {
                        'commit': commit_hash,
                        'source': 'shared' if shared_framework_dir.exists() else 'clone'
                    }
                }
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to setup {framework_name} repository: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg, extra={'run_id': self.run_id})
            raise RuntimeError(error_msg) from e
        except subprocess.TimeoutExpired as e:
            error_msg = f"{framework_name} repository setup timed out"
            logger.error(error_msg, extra={'run_id': self.run_id})
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error setting up {framework_name}: {e}"
            logger.error(error_msg, extra={'run_id': self.run_id})
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
                    'tokens_out': int,
                    'start_timestamp': int,  # Unix timestamp when API calls started
                    'end_timestamp': int     # Unix timestamp when API calls ended
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
