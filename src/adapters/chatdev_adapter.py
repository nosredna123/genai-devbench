"""
ChatDev framework adapter implementation.

Integrates with ChatDev framework for experiment execution.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple
import requests
from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChatDevAdapter(BaseAdapter):
    """Adapter for ChatDev framework."""
    
    def __init__(self, config: Dict[str, Any], run_id: str, workspace_path: str):
        """
        Initialize ChatDev adapter.
        
        Args:
            config: Framework configuration from experiment.yaml
            run_id: Unique run identifier
            workspace_path: Isolated workspace directory
        """
        super().__init__(config, run_id, workspace_path)
        self.process = None
        self.framework_dir = None
        self.hitl_text = None
        self.python_path = None  # Path to virtual environment Python
        self.venv_path = None    # Path to virtual environment directory
        
    def start(self) -> None:
        """
        Initialize ChatDev framework environment.
        
        Clones repository, sets up environment, starts services.
        Implements T064: ChatDev Environment Setup.
        """
        logger.info("Starting ChatDev framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        # Clone repository
        repo_url = self.config['repo_url']
        commit_hash = self.config['commit_hash']
        self.framework_dir = Path(self.workspace_path) / "chatdev_framework"
        
        try:
            # Clone repository
            subprocess.run(
                ['git', 'clone', repo_url, str(self.framework_dir)],
                check=True,
                capture_output=True,
                timeout=300
            )
            
            # Checkout specific commit
            subprocess.run(
                ['git', 'checkout', commit_hash],
                cwd=self.framework_dir,
                check=True,
                capture_output=True,
                timeout=60
            )
            
            # Verify commit hash matches config (T038 - reproducibility)
            self.verify_commit_hash(self.framework_dir, commit_hash)
            
            logger.info("ChatDev repository cloned and verified",
                       extra={'run_id': self.run_id, 
                             'metadata': {'commit': commit_hash}})
            
            # T064: Set up virtual environment and install dependencies
            self._setup_virtual_environment()
            
            # T065: ChatDev is CLI-based (no persistent services to start)
            # Just verify that run.py exists
            run_py = self.framework_dir / "run.py"
            if not run_py.exists():
                raise RuntimeError(f"ChatDev entry point not found: {run_py}")
            
            logger.info("ChatDev framework ready",
                       extra={'run_id': self.run_id,
                             'metadata': {'venv': str(self.venv_path),
                                        'python': str(self.python_path)}})
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to initialize ChatDev",
                        extra={'run_id': self.run_id,
                              'metadata': {'error': str(e), 
                                         'stderr': e.stderr.decode() if e.stderr else ''}})
            raise RuntimeError("ChatDev initialization failed") from e
        except subprocess.TimeoutExpired as e:
            logger.error("ChatDev initialization timed out",
                        extra={'run_id': self.run_id})
            raise RuntimeError("ChatDev initialization timed out") from e
    
    def _setup_virtual_environment(self) -> None:
        """
        Create virtual environment and install ChatDev dependencies.
        
        Implements FR-002.1 steps 2-3: venv creation and dependency installation.
        """
        self.venv_path = self.framework_dir / ".venv"
        
        logger.info("Creating virtual environment",
                   extra={'run_id': self.run_id,
                         'metadata': {'path': str(self.venv_path)}})
        
        # Create virtual environment
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=True,
                timeout=120
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create virtual environment",
                        extra={'run_id': self.run_id,
                              'metadata': {'error': str(e)}})
            raise RuntimeError("Virtual environment creation failed") from e
        
        # Determine Python and pip paths (platform-independent)
        if sys.platform == "win32":
            self.python_path = self.venv_path / "Scripts" / "python.exe"
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:
            self.python_path = self.venv_path / "bin" / "python"
            pip_path = self.venv_path / "bin" / "pip"
        
        # Verify Python is accessible
        try:
            result = subprocess.run(
                [str(self.python_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            python_version = result.stdout.strip()
            logger.info("Virtual environment created",
                       extra={'run_id': self.run_id,
                             'metadata': {'python_version': python_version}})
        except Exception as e:
            raise RuntimeError(f"Virtual environment Python not accessible: {e}") from e
        
        # Install dependencies from requirements.txt
        logger.info("Installing ChatDev dependencies",
                   extra={'run_id': self.run_id,
                         'event': 'dependency_install_start'})
        
        requirements_file = self.framework_dir / "requirements.txt"
        if not requirements_file.exists():
            raise RuntimeError(f"Requirements file not found: {requirements_file}")
        
        try:
            # Upgrade pip first
            subprocess.run(
                [str(pip_path), "install", "--upgrade", "pip"],
                capture_output=True,
                timeout=120,
                cwd=self.framework_dir
            )
            
            # Install requirements
            result = subprocess.run(
                [str(pip_path), "install", "-r", "requirements.txt"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes for dependency installation
                cwd=self.framework_dir
            )
            
            if result.returncode != 0:
                logger.error("Dependency installation failed",
                           extra={'run_id': self.run_id,
                                 'metadata': {'stderr': result.stderr}})
                raise RuntimeError(f"pip install failed: {result.stderr}")
            
            logger.info("ChatDev dependencies installed successfully",
                       extra={'run_id': self.run_id,
                             'event': 'dependency_install_complete'})
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Dependency installation timed out after 10 minutes")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Dependency installation failed: {e}") from e
            
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """
        Execute a step by sending command to ChatDev framework.
        
        Implements T066: ChatDev Command Execution.
        
        Args:
            step_num: Step number (1-6)
            command_text: Natural language command
            
        Returns:
            Dictionary with execution results
        """
        self.current_step = step_num
        start_time = time.time()
        
        logger.info("Executing step",
                   extra={'run_id': self.run_id, 'step': step_num, 
                         'event': 'step_start', 
                         'metadata': {'framework': 'chatdev', 'task': command_text[:100]}})
        
        # Get API key from environment
        api_key_env = self.config.get('api_key_env', 'OPENAI_API_KEY_CHATDEV')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise RuntimeError(f"API key not found in environment: {api_key_env}")
        
        # Generate unique project name per step
        project_name = f"BAEs_Step{step_num}_{self.run_id[:8]}"
        
        # Construct ChatDev command
        # Using Default config for fully automated execution (no HITL)
        # Model: GPT_4O_MINI for cost efficiency
        cmd = [
            str(self.python_path),
            "run.py",
            "--task", command_text,
            "--name", project_name,
            "--org", "BAEs_Experiment",
            "--config", "Default",  # Fully automated mode
            "--model", "GPT_4O_MINI"
        ]
        
        logger.info("Invoking ChatDev",
                   extra={'run_id': self.run_id, 'step': step_num,
                         'metadata': {'project': project_name, 'model': 'GPT_4O_MINI'}})
        
        # Execute ChatDev with timeout
        try:
            result = subprocess.run(
                cmd,
                cwd=self.framework_dir,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes per step
                env={**os.environ, 'OPENAI_API_KEY': api_key}
            )
            
            success = result.returncode == 0
            duration = time.time() - start_time
            
            # T067: Parse token usage from output (likely returns 0, will use Usage API)
            tokens_in, tokens_out = self._parse_token_usage(result.stdout, result.stderr)
            
            # T068: Detect HITL events (should be 0 with Default config)
            hitl_count = self._detect_hitl_events(result.stdout)
            
            logger.info("ChatDev execution complete",
                       extra={'run_id': self.run_id, 'step': step_num,
                             'metadata': {
                                 'success': success,
                                 'duration': duration,
                                 'tokens_in': tokens_in,
                                 'tokens_out': tokens_out,
                                 'hitl_count': hitl_count,
                                 'exit_code': result.returncode
                             }})
            
            return {
                'success': success,
                'duration_seconds': duration,
                'hitl_count': hitl_count,
                'tokens_in': tokens_in,
                'tokens_out': tokens_out,
                'retry_count': 0
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error("ChatDev execution timeout",
                        extra={'run_id': self.run_id, 'step': step_num,
                              'metadata': {'duration': duration}})
            
            return {
                'success': False,
                'duration_seconds': duration,
                'hitl_count': 0,
                'tokens_in': 0,
                'tokens_out': 0,
                'retry_count': 0,
                'error': 'timeout'
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error("ChatDev execution failed",
                        extra={'run_id': self.run_id, 'step': step_num,
                              'metadata': {'error': str(e), 'duration': duration}})
            
            return {
                'success': False,
                'duration_seconds': duration,
                'hitl_count': 0,
                'tokens_in': 0,
                'tokens_out': 0,
                'retry_count': 0,
                'error': str(e)
            }
    
    def _parse_token_usage(self, stdout: str, stderr: str) -> Tuple[int, int]:
        """
        Parse token usage from ChatDev output.
        
        Implements T067: ChatDev Token Tracking.
        
        ChatDev does not directly log token counts in stdout/stderr.
        Returns (0, 0) to signal orchestrator to use OpenAI Usage API verification.
        
        Args:
            stdout: Standard output from ChatDev
            stderr: Standard error from ChatDev
            
        Returns:
            Tuple of (tokens_in, tokens_out). Returns (0, 0) if not found.
        """
        # ChatDev doesn't expose token counts in logs
        # Orchestrator will verify via OpenAI Usage API (already implemented)
        
        # Future: Could implement log parsing if ChatDev adds token logging
        # For now, rely on Usage API verification which is more reliable
        
        logger.debug("Token parsing skipped - relying on Usage API",
                    extra={'run_id': self.run_id, 'step': self.current_step})
        
        return 0, 0
    
    def _detect_hitl_events(self, output: str) -> int:
        """
        Detect Human-in-the-Loop events from ChatDev output.
        
        Implements T068: ChatDev HITL Detection.
        
        When using --config "Default", ChatDev runs fully automated.
        HITL only occurs with --config "Human" mode.
        
        Args:
            output: Standard output from ChatDev
            
        Returns:
            Number of HITL events detected (should be 0 with Default config)
        """
        import re
        
        # Check if we're using Human mode
        chatdev_config = self.config.get('chatdev_config', 'Default')
        
        if chatdev_config != 'Human':
            # No HITL expected in Default mode
            return 0
        
        # Patterns that indicate HITL request in Human mode
        hitl_patterns = [
            r"Human\s+Reviewer",
            r"Feedback\s+Needed",
            r"Please\s+review",
            r"Your\s+input:",
            r">\s+_"  # Prompt for input
        ]
        
        hitl_count = 0
        for pattern in hitl_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                hitl_count += len(matches)
                logger.info("HITL event detected",
                          extra={'run_id': self.run_id, 
                                'step': self.current_step,
                                'metadata': {'pattern': pattern, 
                                           'count': len(matches)}})
        
        return hitl_count
        
    def health_check(self) -> bool:
        """
        Check if ChatDev framework is ready for execution.
        
        Implements T069: ChatDev Health Checks.
        
        ChatDev is CLI-based (no persistent services), so health check verifies:
        1. run.py exists
        2. Python environment is accessible
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Verify run.py exists
            run_py = self.framework_dir / "run.py"
            if not run_py.exists():
                logger.warning("Health check failed: run.py not found",
                             extra={'run_id': self.run_id})
                return False
            
            # Verify Python environment is accessible
            if not self.python_path or not Path(self.python_path).exists():
                logger.warning("Health check failed: Python not accessible",
                             extra={'run_id': self.run_id})
                return False
            
            # Quick Python version check
            result = subprocess.run(
                [str(self.python_path), "--version"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning("Health check failed: Python check failed",
                             extra={'run_id': self.run_id})
                return False
            
            return True
            
        except Exception as e:
            logger.warning("Health check exception",
                         extra={'run_id': self.run_id,
                               'metadata': {'error': str(e)}})
            return False
            
    def handle_hitl(self, query: str) -> str:
        """
        Return fixed HITL response for deterministic execution.
        
        Args:
            query: Framework's clarification question
            
        Returns:
            Fixed clarification text
        """
        if self.hitl_text is None:
            # Load HITL text from config (should be done once)
            hitl_path = Path("config/hitl/expanded_spec.txt")
            with open(hitl_path, 'r', encoding='utf-8') as f:
                self.hitl_text = f.read().strip()
                
        logger.info("HITL intervention",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'event': 'hitl', 
                         'metadata': {'query_length': len(query), 'framework': 'chatdev'}})
                         
        return self.hitl_text
        
    def stop(self) -> None:
        """
        Gracefully shutdown ChatDev framework.
        
        Implements T070: ChatDev Graceful Shutdown.
        
        ChatDev is CLI-based, so cleanup involves:
        1. Terminating any running subprocess
        2. Cleanup handled by orchestrator (workspace archival)
        """
        logger.info("Stopping ChatDev framework",
                   extra={'run_id': self.run_id, 'event': 'framework_stop'})
        
        # If subprocess is still running, terminate it
        if hasattr(self, 'process') and self.process and self.process.poll() is None:
            logger.info("Terminating ChatDev process",
                       extra={'run_id': self.run_id})
            
            # Send SIGTERM for graceful shutdown
            self.process.terminate()
            
            try:
                # Wait up to 30 seconds for graceful termination
                self.process.wait(timeout=30)
                logger.info("ChatDev process terminated gracefully",
                           extra={'run_id': self.run_id})
            except subprocess.TimeoutExpired:
                # Force kill if still running
                logger.warning("ChatDev process did not terminate, forcing kill",
                             extra={'run_id': self.run_id})
                self.process.kill()
                self.process.wait()
                
        logger.info("ChatDev framework stopped",
                   extra={'run_id': self.run_id, 'event': 'framework_stopped'})
