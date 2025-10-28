"""
ChatDev framework adapter implementation.

Integrates with ChatDev framework for experiment execution.

OpenAI API Compatibility Strategy
----------------------------------
ChatDev's codebase lags behind OpenAI's API evolution. We apply runtime patches to add:

1. **API Field Compatibility** (_patch_openai_compatibility):
   - 'refusal' field (Aug 2024): ✅ Already in commit 52edb89
   - 'audio' field (Sep 2024): ✅ Already in commit 52edb89  
   - 'annotations' field (Oct 2024): ⚠️ Patched by us at runtime

2. **New Model Support** (_patch_o1_model_support):
   - o1-preview: ⚠️ Patched at runtime ($15/$60 per 1M tokens)
   - o1-mini: ⚠️ Patched at runtime ($3/$12 per 1M tokens)
   - gpt-5-mini: ⚠️ Patched at runtime ($0.25/$2.00 per 1M tokens)

See .copilot/FINAL_CHATDEV_SOLUTION.md for full details.
"""

import os
import subprocess
import sys
import time
import shutil
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
import requests
from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__, component="adapter")


class ChatDevAdapter(BaseAdapter):
    """Adapter for ChatDev framework."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        run_id: str,
        workspace_path: str,
        sprint_num: int = 1,
        run_dir: Optional[Path] = None
    ):
        """
        Initialize ChatDev adapter.
        
        Args:
            config: Framework configuration from experiment.yaml
            run_id: Unique run identifier
            workspace_path: Isolated workspace directory
            sprint_num: Current sprint number (1-indexed)
            run_dir: Run directory path (required for sprint-aware runs)
        """
        super().__init__(config, run_id, workspace_path, sprint_num, run_dir)
        self.process = None
        self.framework_dir = None
        self.hitl_text = None
        self.python_path = None  # Path to virtual environment Python
        self.venv_path = None    # Path to virtual environment directory
        self.last_execution_error = None  # Track last framework execution error for debugging
        
    def start(self) -> None:
        """
        Initialize ChatDev framework environment with shared resources.
        
        Uses shared framework directory and venv (created during setup).
        Patches are already applied during setup_frameworks.py.
        """
        logger.info("Starting ChatDev framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        try:
            # Get shared framework path (read-only reference)
            self.framework_dir = self.get_shared_framework_path('chatdev')
            logger.info(f"Using shared framework: {self.framework_dir}",
                       extra={'run_id': self.run_id})
            
            # Get shared Python executable from venv
            self.python_path = self.get_framework_python('chatdev')
            self.venv_path = self.framework_dir / '.venv'  # For compatibility
            logger.info(f"Using framework Python: {self.python_path}",
                       extra={'run_id': self.run_id})
            
            # Initialize directory attributes (will be set properly in sprint loop)
            # In sprint architecture, directories are created per-sprint, not during framework initialization
            self.warehouse_dir = None
            
            # NOTE: Patches (_patch_openai_compatibility, _patch_o1_model_support) 
            # are now applied during setup_frameworks.py, NOT per-run.
            # This avoids race conditions when multiple runs execute concurrently.
            
            # Verify ChatDev entry point exists
            run_py = self.framework_dir / "run.py"
            if not run_py.exists():
                raise RuntimeError(f"ChatDev entry point not found: {run_py}")
            
            # Validate API key configuration (FR-011)
            self.validate_api_key()
            logger.info("ChatDev API key validated",
                       extra={'run_id': self.run_id})
            
            logger.info("ChatDev framework ready",
                       extra={
                           'run_id': self.run_id,
                           'framework_dir': str(self.framework_dir),
                           'python': str(self.python_path),
                           'workspace': str(Path(self.workspace_path))
                       })
            
        except RuntimeError as e:
            logger.error("Failed to initialize ChatDev",
                        extra={'run_id': self.run_id, 'metadata': {'error': str(e)}})
            raise RuntimeError("ChatDev initialization failed") from e
    
    def _copy_artifacts(self, step_num: int, project_name: str) -> None:
        """
        Copy ChatDev's WareHouse output to workspace directory.
        
        This ensures validation can find the generated code.
        Aligns with BAeS pattern of writing directly to workspace.
        
        Args:
            step_num: Step number that was executed
            project_name: Name of the ChatDev project (e.g., BAEs_Step1_xxx)
        """
        warehouse_path = self.framework_dir / "WareHouse"
        
        if not warehouse_path.exists():
            logger.warning("WareHouse directory not found - no artifacts to copy",
                         extra={'run_id': self.run_id, 'step': step_num,
                               'metadata': {'expected_path': str(warehouse_path)}})
            return
        
        # Find the project directory (ChatDev may add timestamp suffix)
        project_dirs = list(warehouse_path.glob(f"{project_name}*"))
        
        if not project_dirs:
            logger.warning("No matching project directory found in WareHouse",
                         extra={'run_id': self.run_id, 'step': step_num,
                               'metadata': {'project_pattern': f"{project_name}*",
                                          'warehouse_path': str(warehouse_path)}})
            return
        
        # Copy to workspace directory (where validation expects files)
        workspace_dir = Path(self.workspace_path)
        
        # Copy each matching project directory
        for project_dir in project_dirs:
            try:
                # Copy contents of project_dir into workspace
                # (not the project_dir itself, to avoid nested structure)
                for item in project_dir.iterdir():
                    dest = workspace_dir / item.name
                    if item.is_file():
                        shutil.copy2(item, dest)
                    elif item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                
                file_count = len(list(workspace_dir.rglob('*')))
                logger.info("Copied ChatDev artifacts to workspace",
                          extra={'run_id': self.run_id, 'step': step_num,
                                'metadata': {
                                    'source': str(project_dir),
                                    'destination': str(workspace_dir),
                                    'files_copied': file_count
                                }})
            except Exception as e:
                logger.error("Failed to copy ChatDev artifacts",
                           extra={'run_id': self.run_id, 'step': step_num,
                                 'metadata': {
                                     'error': str(e),
                                     'source': str(project_dir),
                                     'destination': str(workspace_dir)
                                 }})
            
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
        
        # Record step start time for Usage API query (Unix timestamp)
        self._step_start_time = int(time.time())
        start_time = time.time()  # For duration calculation
        
        logger.info("Executing step",
                   extra={'run_id': self.run_id, 'step': step_num, 
                         'event': 'step_start', 
                         'metadata': {'framework': 'chatdev', 'task': command_text[:100]}})
        
        # Get API key from environment - REQUIRED
        api_key_env = self.config.get('api_key_env', 'OPENAI_API_KEY_CHATDEV')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise RuntimeError(
                f"API key not found in environment: {api_key_env}. "
                "Each framework must use a dedicated API key for accurate token tracking."
            )
        
        logger.info("API key retrieved", extra={'run_id': self.run_id, 
                   'metadata': {'env_var': api_key_env, 
                               'key_length': len(api_key)}})
        
        # Generate unique project name per step
        project_name = f"BAEs_Step{step_num}_{self.run_id[:8]}"
        
        # Get model from global config (injected into framework config by config_loader)
        # All frameworks must use the same model for fair comparison
        model = self.config.get('model', 'gpt-4o-mini')
        # Convert to ChatDev's model enum format (e.g., gpt-4o-mini -> GPT_4O_MINI)
        chatdev_model = model.replace('-', '_').upper()
        
        # Verify pydantic version before execution (debugging)
        verify_cmd = [str(self.python_path), "-c", "import pydantic; print(f'Pydantic: {pydantic.__version__}')"]
        verify_result = subprocess.run(verify_cmd, capture_output=True, stdin=subprocess.DEVNULL, text=True, cwd=self.framework_dir)
        logger.info("Pre-execution environment check",
                   extra={'run_id': self.run_id,
                         'metadata': {'pydantic_check': verify_result.stdout.strip(),
                                     'check_stderr': verify_result.stderr[:200] if verify_result.stderr else ''}})
        
        # Determine if we should use incremental development
        # For sprint > 1, use ChatDev's built-in incremental mode with --path to previous code
        use_incremental = self.sprint_num > 1
        config_mode = "Incremental" if use_incremental else "Default"
        
        # Construct ChatDev command
        cmd = [
            str(self.python_path),
            "run.py",
            "--task", command_text,
            "--name", project_name,
            "--org", "BAEs_Experiment",
            "--config", config_mode,
            "--model", chatdev_model
        ]
        
        # Add --path parameter for incremental development
        # ChatDev's incremental mode requires the path to previous sprint's source code
        if use_incremental:
            prev_artifacts = self.previous_sprint_artifacts
            if prev_artifacts and prev_artifacts.exists():
                cmd.extend(["--path", str(prev_artifacts)])
                logger.info("Using incremental development mode",
                           extra={'run_id': self.run_id, 'step': step_num,
                                 'metadata': {
                                     'sprint': self.sprint_num,
                                     'prev_sprint': self.sprint_num - 1,
                                     'source_path': str(prev_artifacts),
                                     'config': config_mode
                                 }})
            else:
                logger.warning("Previous sprint artifacts not found - falling back to Default mode",
                             extra={'run_id': self.run_id, 'step': step_num,
                                   'metadata': {
                                       'sprint': self.sprint_num,
                                       'expected_path': str(prev_artifacts) if prev_artifacts else 'None'
                                   }})
                # Fallback to Default mode if previous sprint not found
                cmd[cmd.index("Incremental")] = "Default"
                config_mode = "Default"
        
        logger.info("Invoking ChatDev",
                   extra={'run_id': self.run_id, 'step': step_num,
                         'metadata': {
                             'project': project_name,
                             'model': chatdev_model,
                             'config': config_mode,
                             'sprint': self.sprint_num,
                             'incremental': use_incremental
                         }})
        
        # Execute ChatDev with timeout
        # IMPORTANT: ChatDev expects OPENAI_API_KEY (not our custom name)
        env = os.environ.copy()
        
        # Clean Python-related environment variables to ensure venv isolation
        # Remove system Python paths that could interfere with venv
        for key in ['PYTHONHOME', '__PYVENV_LAUNCHER__']:
            env.pop(key, None)
        
        # Set virtual environment variables
        env['VIRTUAL_ENV'] = str(self.venv_path)
        env['PATH'] = f"{self.venv_path / 'bin'}:{env.get('PATH', '')}"
        env['OPENAI_API_KEY'] = api_key  # Set standard OpenAI key name
        
        # Add ChatDev directory to PYTHONPATH for relative imports
        # ChatDev's code uses absolute imports like "from utils import ..." 
        # which require the framework directory to be in sys.path
        # IMPORTANT: When using venv's Python, it automatically adds venv/lib/pythonX.Y/site-packages
        # We just need to add the framework directory for ChatDev's own modules
        env['PYTHONPATH'] = str(self.framework_dir)
        
        logger.info("Environment setup for subprocess", extra={'run_id': self.run_id,
                   'metadata': {'OPENAI_API_KEY_set': 'OPENAI_API_KEY' in env,
                               'OPENAI_API_KEY_length': len(env.get('OPENAI_API_KEY', '')),
                               'VIRTUAL_ENV': env.get('VIRTUAL_ENV', ''),
                               'PYTHONPATH': env.get('PYTHONPATH', ''),
                               'total_env_vars': len(env)}})
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.framework_dir,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=600,  # 10 minutes per step
                env=env
            )
            
            success = result.returncode == 0
            duration = time.time() - start_time
            end_timestamp = int(time.time())
            
            # Log stderr if execution failed
            if not success:
                # Store error for validation reporting
                self.last_execution_error = {
                    'type': 'EXECUTION_FAILURE',
                    'exit_code': result.returncode,
                    'stderr': result.stderr,
                    'stdout': result.stdout
                }
                logger.error("ChatDev execution failed",
                           extra={'run_id': self.run_id, 'step': step_num,
                                 'metadata': {
                                     'exit_code': result.returncode,
                                     'stderr': result.stderr[:1000] if result.stderr else '',
                                     'stdout_preview': result.stdout[:500] if result.stdout else ''
                                 }})
            
            # BREAKING CHANGE (v2.0.0): Token metrics removed from step execution
            # Tokens are now reconciled post-run via UsageReconciler (eliminates zero-token bug)
            
            # T068: Detect HITL events (should be 0 with Default config)
            hitl_count = self._detect_hitl_events(result.stdout)
            
            # Copy ChatDev's WareHouse output to permanent storage
            # This preserves generated code for reproducibility and debugging
            if success:
                self._copy_artifacts(step_num, project_name)
            
            logger.info("ChatDev execution complete",
                       extra={'run_id': self.run_id, 'step': step_num,
                             'metadata': {
                                 'success': success,
                                 'duration': duration,
                                 'hitl_count': hitl_count,
                                 'exit_code': result.returncode,
                                 'note': 'Tokens will be reconciled post-run'
                             }})
            
            return {
                'success': success,
                'duration_seconds': duration,
                'start_timestamp': self._step_start_time,
                'end_timestamp': end_timestamp,
                'hitl_count': hitl_count,
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
                'start_timestamp': self._step_start_time,
                'end_timestamp': int(time.time()),
                'hitl_count': 0,
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
                'start_timestamp': self._step_start_time if hasattr(self, '_step_start_time') else int(time.time()),
                'end_timestamp': int(time.time()),
                'hitl_count': 0,
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
            True if healthy
            
        Raises:
            RuntimeError: If health check fails with details
        """
        # Verify run.py exists
        run_py = self.framework_dir / "run.py"
        if not run_py.exists():
            raise RuntimeError(f"ChatDev entry point not found: {run_py}")
        
        # Verify Python environment is accessible
        if not self.python_path or not Path(self.python_path).exists():
            raise RuntimeError(
                f"ChatDev Python environment not accessible: {self.python_path}"
            )
        
        # Quick Python version check
        result = subprocess.run(
            [str(self.python_path), "--version"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=5
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"ChatDev Python check failed with exit code {result.returncode}: "
                f"{result.stderr.decode() if result.stderr else 'No error output'}"
            )
        
        return True
            
    def handle_hitl(self, query: str) -> str:
        """
        Return fixed HITL response for deterministic execution.
        
        Args:
            query: Framework's clarification question
            
        Returns:
            Fixed clarification text from config/hitl/expanded_spec.txt
            
        Raises:
            RuntimeError: If HITL file is missing or empty
        """
        if self.hitl_text is None:
            # Load HITL text from config (should be done once)
            hitl_path = Path("config/hitl/expanded_spec.txt")
            if not hitl_path.exists():
                raise RuntimeError(
                    f"HITL specification file not found: {hitl_path}. "
                    "This file is required for deterministic HITL responses."
                )
            
            with open(hitl_path, 'r', encoding='utf-8') as f:
                self.hitl_text = f.read().strip()
            
            if not self.hitl_text:
                raise RuntimeError(
                    f"HITL specification file is empty: {hitl_path}. "
                    "File must contain clarification text."
                )
                
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
    
    def validate_run_artifacts(self) -> tuple[bool, str]:
        """Validate that ChatDev generated code artifacts in workspace directory.
        
        Checks that the workspace directory contains expected files:
        - At least one Python file (.py)
        - Main entry point file (main.py)
        
        Returns:
            tuple[bool, str]: (success, error_message)
                - success: True if artifacts are valid, False otherwise
                - error_message: Empty string if success, descriptive error if failure
        """
        workspace_dir = Path(self.workspace_path)
        if not workspace_dir.exists():
            return False, (
                f"Workspace directory does not exist: {workspace_dir}. "
                "ChatDev framework failed to create workspace directory."
            )
        
        # Use DRY helper from BaseAdapter for language-agnostic validation
        if not self.validate_artifacts_generated(workspace_dir, "ChatDev"):
            error_msg = self._format_validation_error(
                workspace_dir=workspace_dir,
                framework_name="ChatDev",
                last_execution_error=self.last_execution_error
            )
            return False, error_msg
        
        # Check for main.py (typical ChatDev entry point)
        main_file = workspace_dir / "main.py"
        if not main_file.exists():
            logger.warning(
                f"No main.py found in workspace directory: {workspace_dir}",
                extra={'run_id': self.run_id}
            )
        
        return True, ""
