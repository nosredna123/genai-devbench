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
    
    def __init__(
        self,
        config: Dict[str, Any],
        run_id: str,
        workspace_path: str,
        sprint_num: int = 1,
        run_dir: Optional[Path] = None
    ):
        """
        Initialize adapter with configuration and run context.
        
        Args:
            config: Framework-specific settings from experiment.yaml
            run_id: Unique run identifier (UUID)
            workspace_path: Isolated directory for this run (legacy single-step runs)
            sprint_num: Current sprint number (1-indexed, default=1 for backward compatibility)
            run_dir: Run directory path (required for sprint-aware runs)
        """
        self.config = config
        self.run_id = run_id
        self.workspace_path = workspace_path
        self.current_step = 0
        self._step_start_time: Optional[float] = None  # Track step execution start time
        
        # Sprint-aware properties (US1: Sprint Architecture)
        self._sprint_num = sprint_num
        self._run_dir = Path(run_dir) if run_dir else None
    
    # =============================================================================
    # Sprint-Aware Properties (US1: Sprint Architecture)
    # =============================================================================
    
    @property
    def sprint_num(self) -> int:
        """Get current sprint number."""
        return self._sprint_num
    
    @property
    def run_dir(self) -> Optional[Path]:
        """Get run directory path."""
        return self._run_dir
    
    @property
    def previous_sprint_artifacts(self) -> Optional[Path]:
        """
        Get path to previous sprint's generated artifacts.
        
        Returns:
            Path to previous sprint's generated_artifacts/ directory, or None if:
            - This is the first sprint (sprint_num == 1)
            - Run directory is not set (legacy single-step runs)
            - Previous sprint doesn't exist
        """
        if not self._run_dir or self._sprint_num <= 1:
            return None
        
        # Import here to avoid circular dependency
        from src.utils.isolation import get_previous_sprint_artifacts
        return get_previous_sprint_artifacts(self._run_dir, self._sprint_num)
    
    @property
    def sprint_log_dir(self) -> Optional[Path]:
        """
        Get path to current sprint's logs directory.
        
        Returns:
            Path to sprint_NNN/logs/ directory, or None if run_dir not set
        """
        if not self._run_dir:
            return None
        
        # Use sprint_dir helper from isolation.py (DRY principle)
        from src.utils.isolation import sprint_dir
        sprint_path = sprint_dir(self._run_dir, self._sprint_num)
        return sprint_path / "logs"
    
    # =============================================================================
    # Token Metrics (Lazy Evaluation Pattern)
    # =============================================================================
    
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
    
    def get_shared_framework_path(self, framework_name: str) -> Path:
        """
        Get path to shared framework directory with backward compatibility.
        
        This method implements a fallback pattern to support both new (shared frameworks/)
        and old (workspace-local) directory structures, ensuring backward compatibility.
        
        Priority order:
        1. New location: <experiment_root>/frameworks/<framework_name>/
        2. Old location: <workspace>/workspace/<framework_name>_framework/ (deprecated)
        
        Args:
            framework_name: Framework identifier (baes, chatdev, ghspec)
            
        Returns:
            Path to framework directory (absolute)
            
        Raises:
            RuntimeError: If framework not found in either location
            
        Example:
            >>> adapter.get_shared_framework_path('baes')
            Path('/experiments/my-exp/frameworks/baes')
        """
        # Compute experiment root from workspace path
        # workspace_path: /exp-root/runs/framework/run-id/workspace
        # experiment_root: /exp-root (go up 4 levels)
        workspace = Path(self.workspace_path).resolve()
        experiment_root = workspace.parent.parent.parent.parent
        
        # Try new shared location first
        shared_path = experiment_root / 'frameworks' / framework_name
        if shared_path.exists() and shared_path.is_dir():
            logger.debug(
                f"Using shared framework: {shared_path}",
                extra={'run_id': self.run_id, 'framework': framework_name}
            )
            return shared_path
        
        # Fallback to old workspace location (deprecated)
        workspace_base = experiment_root / "workspace"
        old_path = workspace_base / f"{framework_name}_framework"
        if old_path.exists() and old_path.is_dir():
            logger.warning(
                f"Using deprecated workspace framework location: {old_path}. "
                f"Run setup_frameworks.py to migrate to shared location.",
                extra={'run_id': self.run_id, 'framework': framework_name}
            )
            return old_path.resolve()
        
        # Framework not found in either location
        error_msg = (
            f"Framework '{framework_name}' not found. Checked:\n"
            f"  - Shared location: {shared_path}\n"
            f"  - Old location: {old_path}\n"
            f"Run 'python templates/setup_frameworks.py' or './setup.sh' to set up frameworks."
        )
        logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
        raise RuntimeError(error_msg)
    
    def get_framework_python(self, framework_name: str) -> Path:
        """
        Get Python executable path from shared virtual environment.
        
        This method returns the Python interpreter from the framework's shared venv,
        which is created during setup and reused across all runs.
        
        Args:
            framework_name: Framework identifier (baes, chatdev, ghspec)
            
        Returns:
            Path to Python executable (absolute)
            
        Raises:
            RuntimeError: If venv doesn't exist or Python not executable
            
        Example:
            >>> adapter.get_framework_python('baes')
            Path('/experiments/my-exp/frameworks/baes/.venv/bin/python')
        """
        framework_path = self.get_shared_framework_path(framework_name)
        python_path = framework_path / '.venv' / 'bin' / 'python'
        
        # Validate Python executable exists
        if not python_path.exists():
            error_msg = (
                f"Python executable not found: {python_path}\n"
                f"Venv may not be set up. Run 'python templates/setup_frameworks.py'."
            )
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise RuntimeError(error_msg)
        
        # Validate it's a file (not directory or broken symlink)
        if not python_path.is_file():
            error_msg = f"Python path exists but is not a file: {python_path}"
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise RuntimeError(error_msg)
        
        # Validate it's executable
        if not os.access(python_path, os.X_OK):
            error_msg = f"Python executable lacks execute permission: {python_path}"
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise RuntimeError(error_msg)
        
        logger.debug(
            f"Using framework Python: {python_path}",
            extra={'run_id': self.run_id, 'framework': framework_name}
        )
        # Return the path WITHOUT resolving symlinks
        # Venv's python is a symlink, and we need to use it as-is
        # so Python can detect it's in a venv and use the correct site-packages
        return python_path
    
    def create_workspace_structure(self, subdirs: list[str], exist_ok: bool = True) -> Dict[str, Path]:
        """
        Create run-specific workspace subdirectories.
        
        This method creates isolated directories for run artifacts, ensuring each run
        writes to its own workspace without interfering with other runs.
        
        Args:
            subdirs: List of subdirectory names to create (e.g., ['managed_system', 'database'])
            exist_ok: If True, don't error if directories already exist (default: True)
            
        Returns:
            Dictionary mapping subdir names to absolute paths
            
        Raises:
            ValueError: If subdirs is empty or contains invalid names
            OSError: If directory creation fails
            PermissionError: If workspace not writable
            
        Example:
            >>> adapter.create_workspace_structure(['managed_system', 'database'])
            {
                'managed_system': Path('/runs/baes/uuid/workspace/managed_system'),
                'database': Path('/runs/baes/uuid/workspace/database')
            }
        """
        # Validate subdirs list
        if not subdirs:
            error_msg = "subdirs list cannot be empty"
            logger.error(error_msg, extra={'run_id': self.run_id})
            raise ValueError(error_msg)
        
        # Validate workspace path is writable
        workspace_path = Path(self.workspace_path)
        if not os.access(workspace_path, os.W_OK):
            error_msg = f"Workspace not writable: {workspace_path}"
            logger.error(error_msg, extra={'run_id': self.run_id})
            raise PermissionError(error_msg)
        
        result = {}
        for subdir in subdirs:
            # Validate subdir name (no path traversal)
            if '/' in subdir or '\\' in subdir or '..' in subdir:
                error_msg = f"Invalid subdirectory name (contains path separators): {subdir}"
                logger.error(error_msg, extra={'run_id': self.run_id})
                raise ValueError(error_msg)
            
            # Prevent framework names as subdirs (would break isolation)
            if subdir in ['baes', 'chatdev', 'ghspec'] or subdir.endswith('_framework'):
                error_msg = (
                    f"Invalid subdirectory name '{subdir}': cannot use framework names. "
                    f"Workspace should only contain artifacts, not framework copies."
                )
                logger.error(error_msg, extra={'run_id': self.run_id})
                raise ValueError(error_msg)
            
            # Create directory
            dir_path = workspace_path / subdir
            try:
                dir_path.mkdir(parents=True, exist_ok=exist_ok)
                logger.debug(
                    f"Created workspace directory: {dir_path}",
                    extra={'run_id': self.run_id, 'subdir': subdir}
                )
                result[subdir] = dir_path.resolve()
            except OSError as e:
                error_msg = f"Failed to create directory {dir_path}: {e}"
                logger.error(error_msg, extra={'run_id': self.run_id})
                raise OSError(error_msg) from e
        
        logger.info(
            f"Workspace structure created: {len(result)} directories",
            extra={'run_id': self.run_id, 'subdirs': list(result.keys())}
        )
        return result
    
    def validate_workspace_directory(self, dir_path: Path, dir_name: str = None) -> int:
        """
        Validate that a workspace directory contains files (DRY helper).
        
        This method checks if a workspace directory has any generated files
        and logs a warning if it's empty. Useful for frameworks that generate
        artifacts (code, configs, etc.) that should be captured.
        
        Args:
            dir_path: Path to the directory to validate
            dir_name: Optional name for logging (defaults to dir_path.name)
            
        Returns:
            Number of files found in the directory (recursively)
            
        Example:
            >>> file_count = adapter.validate_workspace_directory(
            ...     self.managed_system_dir,
            ...     "managed_system"
            ... )
            >>> if file_count == 0:
            ...     logger.warning("No files generated")
        """
        if not dir_path or not dir_path.exists():
            return 0
        
        dir_name = dir_name or dir_path.name
        file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
        
        if file_count == 0:
            logger.warning(
                f"⚠️  Workspace directory '{dir_name}' is empty - no files were generated",
                extra={
                    'run_id': self.run_id,
                    'metadata': {
                        'directory_path': str(dir_path),
                        'note': 'Framework may have failed to execute or generate artifacts'
                    }
                }
            )
        else:
            logger.debug(
                f"Workspace directory '{dir_name}' contains {file_count} files",
                extra={'run_id': self.run_id}
            )
        
        return file_count
    
    def setup_shared_venv(
        self,
        framework_name: str,
        requirements_file: Path,
        timeout: int = 300
    ) -> Path:
        """
        Create or verify shared virtual environment for a framework.
        
        This method is IDEMPOTENT: safe to call multiple times. If venv already exists
        and is valid, it returns immediately. Otherwise, it creates a fresh venv.
        
        This method is typically called by templates/setup_frameworks.py during
        experiment setup, not by adapters during runtime.
        
        Args:
            framework_name: Framework identifier (baes, chatdev, ghspec)
            requirements_file: Path to requirements.txt (relative to framework dir)
            timeout: Maximum seconds for venv creation (default: 300 = 5 minutes)
            
        Returns:
            Path to venv directory (absolute)
            
        Raises:
            RuntimeError: If framework directory doesn't exist
            RuntimeError: If requirements.txt not found
            TimeoutError: If venv creation exceeds timeout
            subprocess.CalledProcessError: If pip install fails
            OSError: If insufficient disk space
            
        Example:
            >>> adapter.setup_shared_venv('baes', Path('requirements.txt'), timeout=600)
            Path('/experiments/my-exp/frameworks/baes/.venv')
        """
        # Get framework directory
        try:
            framework_path = self.get_shared_framework_path(framework_name)
        except RuntimeError as e:
            error_msg = f"Cannot setup venv: {e}"
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise RuntimeError(error_msg) from e
        
        # Validate requirements file exists
        if not requirements_file.is_absolute():
            requirements_file = framework_path / requirements_file
        
        if not requirements_file.exists():
            error_msg = f"Requirements file not found: {requirements_file}"
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise RuntimeError(error_msg)
        
        venv_path = framework_path / '.venv'
        python_path = venv_path / 'bin' / 'python'
        
        # Check if venv already exists and is valid
        if python_path.exists() and os.access(python_path, os.X_OK):
            logger.info(
                f"Venv already exists for {framework_name}: {venv_path}",
                extra={'run_id': self.run_id, 'framework': framework_name}
            )
            return venv_path.resolve()
        
        # Create venv
        logger.info(
            f"Creating venv for {framework_name}: {venv_path}",
            extra={'run_id': self.run_id, 'framework': framework_name, 'timeout': timeout}
        )
        
        try:
            # Step 1: Create venv with --clear (remove if partially created)
            subprocess.run(
                ['python3', '-m', 'venv', str(venv_path), '--clear'],
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=60  # Venv creation is fast
            )
            logger.debug(
                f"Venv structure created: {venv_path}",
                extra={'run_id': self.run_id, 'framework': framework_name}
            )
            
            # Step 2: Install requirements with pip
            logger.info(
                f"Installing requirements from {requirements_file}",
                extra={'run_id': self.run_id, 'framework': framework_name}
            )
            pip_result = subprocess.run(
                [
                    str(python_path), '-m', 'pip', 'install',
                    '-r', str(requirements_file),
                    '--timeout', str(timeout)
                ],
                check=True,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=timeout
            )
            
            logger.info(
                f"Venv created successfully for {framework_name}",
                extra={
                    'run_id': self.run_id,
                    'framework': framework_name,
                    'venv_path': str(venv_path),
                    'requirements': str(requirements_file)
                }
            )
            return venv_path.resolve()
            
        except subprocess.TimeoutExpired as e:
            # Clean up partial venv
            if venv_path.exists():
                shutil.rmtree(venv_path, ignore_errors=True)
            
            error_msg = f"Venv creation timeout after {timeout}s for {framework_name}"
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise TimeoutError(error_msg) from e
            
        except subprocess.CalledProcessError as e:
            # Clean up partial venv
            if venv_path.exists():
                shutil.rmtree(venv_path, ignore_errors=True)
            
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            error_msg = f"Failed to install requirements for {framework_name}: {stderr}"
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise subprocess.CalledProcessError(e.returncode, e.cmd, e.output, stderr) from e
            
        except OSError as e:
            # Clean up partial venv
            if venv_path.exists():
                shutil.rmtree(venv_path, ignore_errors=True)
            
            error_msg = f"OS error creating venv for {framework_name}: {e}"
            logger.error(error_msg, extra={'run_id': self.run_id, 'framework': framework_name})
            raise OSError(error_msg) from e
    
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
    
    def _format_validation_error(
        self,
        workspace_dir: Path,
        framework_name: str,
        last_execution_error: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        DRY helper to format user-friendly validation error messages.
        
        Extracts root cause from last_execution_error and formats a consistent
        error message across all framework adapters.
        
        Args:
            workspace_dir: Path to the workspace directory
            framework_name: Name of the framework (e.g., "BAEs", "ChatDev", "GHSpec")
            last_execution_error: Optional dict containing error details with keys:
                - 'stderr': Standard error output
                - 'stdout': Standard output
                - 'error': Error message
                - 'exception_type': Type of exception
        
        Returns:
            Formatted error message with root cause and next steps
        """
        error_details = ""
        
        if last_execution_error:
            # Try to extract meaningful error from stderr (BAeS, ChatDev)
            stderr = last_execution_error.get('stderr', '')
            if stderr and 'ERROR:' in stderr:
                # Find first ERROR line for concise output
                for line in stderr.split('\n'):
                    if 'ERROR:' in line:
                        error_details = f"\n\n📋 Root Cause:\n{line.strip()}"
                        break
            # Fallback to last non-empty stderr line (ChatDev pattern)
            elif stderr:
                error_lines = [line.strip() for line in stderr.split('\n') if line.strip()]
                if error_lines:
                    error_details = f"\n\n📋 Root Cause:\n{error_lines[-1]}"
            # Try exception-based errors (GHSpec pattern)
            elif 'error' in last_execution_error:
                error_msg = last_execution_error.get('error', '')
                error_type = last_execution_error.get('exception_type', '')
                if error_msg:
                    error_details = f"\n\n📋 Root Cause:\n{error_type}: {error_msg}"
        
        return (
            f"❌ Validation Failed: No Python files generated in workspace\n\n"
            f"📁 Expected location: {workspace_dir}\n"
            f"🔍 Issue: {framework_name} framework executed but failed to generate code files"
            f"{error_details}\n\n"
            f"💡 Next Steps:\n"
            f"   1. Check adapter logs: runs/<run_id>/logs/step_*/adapter.log\n"
            f"   2. Review the root cause error above\n"
            f"   3. Fix the issue in the {framework_name} framework if needed"
        )
    
    def _copy_directory_contents(
        self,
        source_dir: Path,
        dest_dir: Path,
        step_num: int,
        recursive: bool = True
    ) -> int:
        """
        DRY helper to copy directory contents to destination.
        
        Shared by ChatDev and GHSpec adapters for copying generated artifacts
        to workspace directory where validation expects them.
        
        Args:
            source_dir: Source directory containing files to copy
            dest_dir: Destination directory (typically workspace root)
            step_num: Current step number for logging
            recursive: If True, use rglob for recursive copy; else use iterdir
            
        Returns:
            Number of files copied
            
        Raises:
            Exception: If copy operation fails
        """
        if not source_dir.exists():
            logger.warning(
                f"Source directory not found - no artifacts to copy: {source_dir}",
                extra={'run_id': self.run_id, 'step': step_num}
            )
            return 0
        
        copied_count = 0
        
        try:
            # Choose iteration method based on recursive flag
            items = source_dir.rglob('*') if recursive else source_dir.iterdir()
            
            for item in items:
                if item.is_file():
                    # Calculate relative path from source_dir
                    rel_path = item.relative_to(source_dir)
                    dest = dest_dir / rel_path
                    
                    # Create parent directories if needed
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(item, dest)
                    copied_count += 1
                    
                    logger.debug(f"Copied artifact: {rel_path}",
                               extra={'run_id': self.run_id, 'step': step_num})
            
            logger.info(f"Copied {copied_count} artifacts to workspace",
                       extra={'run_id': self.run_id, 'step': step_num,
                             'metadata': {
                                 'source': str(source_dir),
                                 'dest': str(dest_dir),
                                 'files_copied': copied_count
                             }})
            
            return copied_count
            
        except Exception as e:
            logger.error("Failed to copy artifacts",
                       extra={'run_id': self.run_id, 'step': step_num,
                             'metadata': {
                                 'error': str(e),
                                 'source': str(source_dir),
                                 'dest': str(dest_dir)
                             }})
            raise
    
    @abstractmethod
    def validate_run_artifacts(self) -> tuple[bool, str]:
        """
        Validate that the framework generated expected artifacts in the workspace.
        
        This method should be called during the validation phase to ensure that
        the framework execution actually produced the expected output files.
        An empty workspace directory indicates a framework execution failure.
        
        Returns:
            tuple[bool, str]: (success, error_message)
                - success: True if artifacts are valid, False otherwise
                - error_message: Empty string if success, descriptive error if failure
                
        Example:
            success, error = adapter.validate_run_artifacts()
            if not success:
                logger.error(f"Artifact validation failed: {error}")
        """
        pass
