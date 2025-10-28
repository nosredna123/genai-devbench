"""
BAEs framework adapter implementation.

Integrates the Business Autonomous Entities (BAEs) framework into the experiment orchestrator.
Uses domain entity-focused architecture with SWEA agent coordination.

Repository: https://github.com/gesad-lab/baes_demo
Commit: a34b207 (Phase 1 Complete)
"""

import os
import subprocess
import sys
import time
import shutil
import tarfile
import socket
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger
from src.utils.text import parse_json_from_output

logger = get_logger(__name__, component="adapter")


class BAeSAdapter(BaseAdapter):
    """Adapter for Business Autonomous Entities (BAEs) framework.
    
    Uses the BAEs non-interactive CLI (bae_noninteractive.py) to execute
    natural language requests. This approach:
    - Avoids hardcoded command mappings
    - Uses the official BAEs CLI interface
    - Handles any natural language request dynamically
    - Future-proof against internal API changes
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        run_id: str,
        workspace_path: str,
        sprint_num: int = 1,
        run_dir: Optional[Path] = None
    ):
        super().__init__(config, run_id, workspace_path, sprint_num, run_dir)
        self.framework_dir = None
        self.managed_system_dir = None
        self.database_dir = None
        self.venv_path = None
        self.python_path = None
        self._kernel = None
        self.hitl_text = None
        self.current_step = 0
        self.last_execution_error = None  # Track last framework execution error for debugging
        
    def start(self) -> None:
        """Initialize BAEs adapter with shared framework resources."""
        logger.info("Starting BAEs framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        try:
            # Get shared framework path (read-only reference)
            self.framework_dir = self.get_shared_framework_path('baes')
            logger.info(f"Using shared framework: {self.framework_dir}",
                       extra={'run_id': self.run_id})
            
            # Get shared Python executable from venv
            self.python_path = self.get_framework_python('baes')
            self.venv_path = self.framework_dir / '.venv'  # Set venv_path for _execute_kernel_request
            logger.info(f"Using framework Python: {self.python_path}",
                       extra={'run_id': self.run_id})
            
            # Initialize directory attributes (will be set properly in sprint loop)
            # In sprint architecture, directories are created per-sprint, not during framework initialization
            self.managed_system_dir = None
            self.database_dir = None
            
            # Set framework-level environment variables (sprint-specific paths set in sprint loop)
            os.environ['API_PORT'] = str(self.config.get('api_port', 8100))
            os.environ['UI_PORT'] = str(self.config.get('ui_port', 8600))
            os.environ['BAE_MAX_RETRIES'] = str(self.config.get('max_retries', 3))
            
            # REQUIRED: BAEs must have dedicated API key for proper token attribution
            baes_api_key = os.getenv('OPENAI_API_KEY_BAES')
            if not baes_api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY_BAES environment variable is required. "
                    "Each framework must use a dedicated API key for accurate token tracking."
                )
            
            os.environ['OPENAI_API_KEY'] = baes_api_key
            logger.info("BAEs API key configured for token tracking",
                       extra={'run_id': self.run_id})
            
            # Validate API key configuration (FR-011)
            self.validate_api_key()
            logger.info("BAeS API key validated",
                       extra={'run_id': self.run_id})
            
            logger.info("BAEs framework ready",
                       extra={
                           'run_id': self.run_id,
                           'framework_dir': str(self.framework_dir),
                           'python': str(self.python_path),
                           'workspace': str(Path(self.workspace_path))
                       })
            
        except RuntimeError as e:
            logger.error("Failed to initialize BAEs framework", extra={'run_id': self.run_id})
            raise RuntimeError(f"BAEs initialization failed: {e}") from e
    
    @property
    def kernel(self):
        """Property to access kernel - kept for API compatibility but not actually used.
        
        Actual kernel execution happens via subprocess in the venv.
        """
        # Deprecated - kernel execution moved to subprocess wrapper
        return None
    
    def _execute_kernel_request(self, request: str, start_servers: bool = False) -> dict:
        """Execute a BAEs kernel request using the non-interactive CLI.
        
        Args:
            request: Natural language request
            start_servers: Whether to start API/UI servers
            
        Returns:
            Dictionary with 'success' and 'result' or 'error'
        """
        cli_script = self.framework_dir / "bae_noninteractive.py"
        context_store_path = str(self.database_dir / "context_store.json")
        venv_python = (self.venv_path / "bin" / "python").absolute()
        
        # Build command for non-interactive CLI
        cmd = [
            str(venv_python),
            str(cli_script.absolute()),
            "--request", request,
            "--context-store", context_store_path,
            "--output-json",
            "--quiet"  # Suppress progress messages, only output JSON
        ]
        
        if start_servers:
            cmd.append("--start-servers")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per request
                cwd=str(self.framework_dir),
                env=os.environ.copy()
            )
            
            if result.returncode != 0:
                # Try to parse error from JSON output (with ANSI stripping)
                error_data, parse_error = parse_json_from_output(result.stdout or "")
                if error_data:
                    error_msg = error_data.get('error', result.stderr or 'Unknown error')
                    logger.error(
                        f"BAeS CLI returned error (exit code {result.returncode})",
                        extra={
                            'run_id': self.run_id,
                            'metadata': {
                                'error': error_msg,
                                'stdout': result.stdout[:500] if result.stdout else None,
                                'stderr': result.stderr[:500] if result.stderr else None
                            }
                        }
                    )
                    return {
                        'success': False,
                        'error': error_msg
                    }
                else:
                    error_msg = f"CLI execution failed: {result.stderr or result.stdout}"
                    # Store error for validation reporting
                    self.last_execution_error = {
                        'type': 'CLI_EXECUTION_FAILURE',
                        'exit_code': result.returncode,
                        'stderr': result.stderr,
                        'stdout': result.stdout
                    }
                    logger.error(
                        f"BAeS CLI failed with non-JSON output (exit code {result.returncode})",
                        extra={
                            'run_id': self.run_id,
                            'metadata': {
                                'stdout': result.stdout[:500] if result.stdout else None,
                                'stderr': result.stderr[:500] if result.stderr else None,
                                'parse_error': parse_error
                            }
                        }
                    )
                    return {
                        'success': False,
                        'error': error_msg
                    }
            
            # Parse JSON output from CLI (with robust ANSI stripping and JSON extraction)
            output, parse_error = parse_json_from_output(result.stdout or "")
            if output:
                return output
            else:
                logger.error(
                    "Failed to parse CLI output after ANSI cleaning and JSON extraction",
                    extra={
                        'run_id': self.run_id,
                        'step': self.current_step,
                        'metadata': {
                            'parse_error': parse_error,
                            'raw_stdout_snippet': (result.stdout[:1000] + '...') if len(result.stdout) > 1000 else result.stdout
                        }
                    }
                )
                return {
                    'success': False,
                    'error': f'Failed to parse CLI output after cleaning: {parse_error}'
                }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Request execution timed out after 5 minutes'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {e}'
            }
    
    def execute_step(self, step_num: int, command_text: str) -> Tuple[bool, float, int, int, float, float]:
        start_time = time.time()  # Float for precise duration calculation
        start_timestamp = int(time.time())  # Integer for API queries
        self.current_step = step_num
        
        logger.info("Executing BAEs step",
                   extra={'run_id': self.run_id, 'step': step_num, 'event': 'step_start'})
        
        try:
            # Execute the natural language request directly via CLI
            # No need for command mapping - BAEs handles any request
            logger.info(
                f"Executing BAEs request for step {step_num}: {command_text}",
                extra={
                    'run_id': self.run_id,
                    'step': step_num,
                    'event': 'step_request_start',
                    'metadata': {
                        'request': command_text[:200]  # Log first 200 chars
                    }
                }
            )
            
            # For step 1, start servers; for subsequent steps, assume servers are running
            start_servers = (step_num == 1)
            
            result = self._execute_kernel_request(
                request=command_text,
                start_servers=start_servers
            )
            
            all_success = result.get('success', False)
            
            if not all_success:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"BAEs request failed: {command_text[:100]}",
                           extra={'run_id': self.run_id, 'step': step_num,
                                 'metadata': {'error': error_msg}})
            else:
                logger.info(f"BAEs request completed successfully",
                           extra={'run_id': self.run_id, 'step': step_num})
            
            duration = time.time() - start_time  # Precise duration as float
            end_timestamp = int(time.time())  # Integer timestamp for API queries
            
            # BREAKING CHANGE (v2.0.0): Token metrics removed from step execution
            # Tokens are now reconciled post-run via UsageReconciler (eliminates zero-token bug)
            
            logger.info("BAEs step completed",
                       extra={'run_id': self.run_id, 'step': step_num, 'event': 'step_complete',
                              'metadata': {
                                  'duration': duration,
                                  'note': 'Tokens will be reconciled post-run'
                              }})
            
            return {
                'success': all_success,
                'duration_seconds': duration,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
                'hitl_count': 0,
                'retry_count': 0
            }
            
        except Exception as e:
            duration = time.time() - start_time  # Precise duration as float
            end_timestamp = int(time.time())  # Integer timestamp for API queries
            logger.error(f"BAEs step failed with exception: {e}",
                        extra={'run_id': self.run_id, 'step': step_num})
            return {
                'success': False,
                'duration_seconds': duration,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
                'hitl_count': 0,
                'retry_count': 0
            }
    
    def stop(self) -> None:
        logger.info("Stopping BAEs framework", extra={'run_id': self.run_id})
        
        # Deprecated kernel cleanup (kept for compatibility but not used with CLI)
        if hasattr(self, '_kernel') and self._kernel:
            if hasattr(self._kernel, '_managed_system_manager'):
                mgr = self._kernel._managed_system_manager
                if mgr and hasattr(mgr, 'stop_servers'):
                    mgr.stop_servers()
        
        self._ensure_servers_stopped()
        self._archive_managed_system()
        
        logger.info("BAEs framework stopped", extra={'run_id': self.run_id})
    
    def _ensure_servers_stopped(self) -> None:
        """Force kill any processes on BAEs ports.
        
        Uses lsof + kill to ensure ports are freed. May raise if commands fail.
        """
        api_port = self.config.get('api_port', 8100)
        ui_port = self.config.get('ui_port', 8600)
        
        for port in [api_port, ui_port]:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("localhost", port)) == 0:
                    # Port is in use - kill the process
                    result = subprocess.run(
                        f"lsof -ti:{port} | xargs kill -9",
                        shell=True,
                        timeout=10,
                        stderr=subprocess.PIPE,
                        check=False  # Don't raise if no process found
                    )
                    if result.returncode != 0 and result.stderr:
                        logger.warning(
                            f"Failed to kill process on port {port}: {result.stderr.decode()}",
                            extra={'run_id': self.run_id}
                        )
                    time.sleep(1)
    
    def _archive_managed_system(self) -> None:
        """Archive managed system directory for reproducibility.
        
        Raises:
            RuntimeError: If archiving fails
        """
        if self.managed_system_dir and self.managed_system_dir.exists():
            # Use DRY helper from BaseAdapter to validate directory contents
            file_count = self.validate_workspace_directory(
                self.managed_system_dir,
                "managed_system"
            )
            
            archive_path = Path(self.workspace_path) / "managed_system.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(self.managed_system_dir, arcname="managed_system")
            
            logger.info(
                f"Archived managed system to {archive_path}",
                extra={
                    'run_id': self.run_id,
                    'metadata': {'file_count': file_count}
                }
            )
    
    def health_check(self) -> bool:
        """Check BAEs framework health.
        
        Returns:
            True if healthy
            
        Raises:
            RuntimeError: If health check fails with details
        """
        if not hasattr(self, '_kernel') or not self._kernel:
            raise RuntimeError("BAEs kernel not initialized")
        
        context_store = self._kernel.context_store
        if not context_store:
            raise RuntimeError("BAEs context store not available")
        
        supported_entities = self._kernel.bae_registry.get_supported_entities()
        if not supported_entities:
            raise RuntimeError("BAEs registry has no supported entities")
        
        if self._should_check_endpoints():
            self._check_http_endpoints()  # Will raise if endpoints fail
        
        return True
    
    def _should_check_endpoints(self) -> bool:
        return (hasattr(self, 'current_step') and 
                self.current_step >= 2 and
                self.managed_system_dir and
                self.managed_system_dir.exists())
    
    def _check_http_endpoints(self) -> bool:
        """Check if BAEs API and UI endpoints are responding.
        
        Returns:
            True if both endpoints are healthy
            
        Raises:
            RuntimeError: If endpoints are not responding
        """
        import requests
        
        api_port = self.config.get('api_port', 8100)
        ui_port = self.config.get('ui_port', 8600)
        
        # Check API endpoint
        try:
            response = requests.get(f"http://localhost:{api_port}/docs", timeout=5)
            if response.status_code != 200:
                raise RuntimeError(
                    f"BAEs API endpoint returned status {response.status_code} "
                    f"(expected 200) at http://localhost:{api_port}/docs"
                )
        except requests.RequestException as e:
            raise RuntimeError(f"BAEs API endpoint not responding at http://localhost:{api_port}/docs: {e}") from e
        
        # Check UI endpoint
        try:
            response = requests.get(f"http://localhost:{ui_port}/", timeout=5)
            if response.status_code != 200:
                raise RuntimeError(
                    f"BAEs UI endpoint returned status {response.status_code} "
                    f"(expected 200) at http://localhost:{ui_port}/"
                )
        except requests.RequestException as e:
            raise RuntimeError(f"BAEs UI endpoint not responding at http://localhost:{ui_port}/: {e}") from e
        
        return True
    
    def handle_hitl(self, query: str) -> str:
        """Return HITL response for deterministic execution.
        
        Args:
            query: Framework's clarification question
            
        Returns:
            Clarification text from config/hitl/expanded_spec.txt
            
        Raises:
            RuntimeError: If HITL file is missing
        """
        if self.hitl_text is None:
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
        
        logger.info("HITL intervention", extra={'run_id': self.run_id, 'step': self.current_step})
        
        return self.hitl_text
    
    def validate_run_artifacts(self) -> tuple[bool, str]:
        """Validate that BAEs generated code artifacts in managed_system directory.
        
        Checks that the managed_system directory contains expected files:
        - At least one Python file (.py)
        - A requirements.txt file (for dependencies)
        
        Returns:
            tuple[bool, str]: (success, error_message)
                - success: True if artifacts are valid, False otherwise
                - error_message: Empty string if success, descriptive error if failure
        """
        if not self.managed_system_dir or not self.managed_system_dir.exists():
            return False, (
                f"Managed system directory does not exist: {self.managed_system_dir}. "
                "BAEs framework failed to create workspace directory."
            )
        
        # Use DRY helper from BaseAdapter for language-agnostic validation
        if not self.validate_artifacts_generated(self.managed_system_dir, "BAEs"):
            error_msg = self._format_validation_error(
                workspace_dir=self.managed_system_dir,
                framework_name="BAEs",
                last_execution_error=self.last_execution_error
            )
            return False, error_msg
        
        # Check for requirements.txt (common dependency file)
        requirements_file = self.managed_system_dir / "requirements.txt"
        if not requirements_file.exists():
            logger.warning(
                f"No requirements.txt found in managed_system directory: {self.managed_system_dir}",
                extra={'run_id': self.run_id}
            )
        
        return True, ""
