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
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

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
    
    def __init__(self, config: Dict[str, Any], run_id: str, workspace_path: str):
        super().__init__(config, run_id, workspace_path)
        self.framework_dir = None
        self.managed_system_dir = None
        self.database_dir = None
        self.venv_path = None
        self.python_path = None
        self._kernel = None
        self.hitl_text = None
        self.current_step = 0
        
    def start(self) -> None:
        logger.info("Starting BAEs framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        self.framework_dir = Path(self.workspace_path) / "baes_framework"
        self.managed_system_dir = Path(self.workspace_path) / "managed_system"
        self.database_dir = Path(self.workspace_path) / "database"
        
        repo_url = self.config['repo_url']
        commit_hash = self.config['commit_hash']  # Required for reproducibility
        
        # Use centralized framework setup method (DRY principle)
        self.setup_framework_from_repo(
            framework_name='baes',
            target_dir=self.framework_dir,
            repo_url=repo_url,
            commit_hash=commit_hash
        )
        
        try:
            logger.info("Setting up isolated virtual environment",
                       extra={'run_id': self.run_id, 'event': 'venv_setup_start'})
            self._setup_virtual_environment()
            
            os.environ['BAE_CONTEXT_STORE_PATH'] = str(self.database_dir / "context_store.json")
            os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
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
            
            logger.info("BAEs framework ready", extra={'run_id': self.run_id})
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to initialize BAEs framework", extra={'run_id': self.run_id})
            raise RuntimeError(f"BAEs initialization failed: {e}") from e
        except subprocess.TimeoutExpired as e:
            logger.error("BAEs initialization timed out", extra={'run_id': self.run_id})
            raise RuntimeError("BAEs initialization timed out") from e
    
    def _setup_virtual_environment(self) -> None:
        self.venv_path = self.framework_dir / ".venv"
        
        logger.info("Creating virtual environment for BAEs",
                   extra={'run_id': self.run_id})
        
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=120
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to create virtual environment", extra={'run_id': self.run_id})
            raise RuntimeError(f"Virtual environment creation failed: {e}") from e
        
        if sys.platform == "win32":
            self.python_path = self.venv_path / "Scripts" / "python.exe"
            pip_path = self.venv_path / "Scripts" / "pip.exe"
        else:
            self.python_path = self.venv_path / "bin" / "python"
            pip_path = self.venv_path / "bin" / "pip"
        
        self.python_path = self.python_path.absolute()
        pip_path = pip_path.absolute()
        
        requirements_file = (self.framework_dir / "requirements.txt").absolute()
        if not requirements_file.exists():
            raise RuntimeError(f"Requirements file not found: {requirements_file}")
        
        try:
            subprocess.run(
                [str(pip_path), "install", "--upgrade", "pip", "setuptools>=67.0.0", "wheel"],
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=120,
                cwd=self.framework_dir
            )
            
            subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=300,
                cwd=self.framework_dir
            )
            
            logger.info("BAEs dependencies installed successfully", extra={'run_id': self.run_id})
            
        except subprocess.CalledProcessError as e:
            stderr_output = e.stderr.decode() if e.stderr else 'No stderr output'
            logger.error("Failed to install BAEs dependencies",
                        extra={'run_id': self.run_id,
                              'metadata': {
                                  'error': str(e),
                                  'stderr': stderr_output[:1000]  # First 1000 chars
                              }})
            raise RuntimeError(f"BAEs dependency installation failed: {e}\nStderr: {stderr_output[:500]}") from e
        except subprocess.TimeoutExpired as exc:
            logger.error("BAEs dependency installation timed out", extra={'run_id': self.run_id})
            raise RuntimeError("BAEs dependency installation timed out") from exc
    
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
                # Try to parse error from JSON output
                try:
                    error_data = json.loads(result.stdout)
                    return {
                        'success': False,
                        'error': error_data.get('error', result.stderr or 'Unknown error')
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': f"CLI execution failed: {result.stderr or result.stdout}"
                    }
            
            # Parse JSON output from CLI
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'Failed to parse CLI output: {e}\nOutput: {result.stdout}'
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
            
            # Fetch usage from OpenAI Usage API
            tokens_in, tokens_out, api_calls, cached_tokens = self.fetch_usage_from_openai(
                api_key_env_var='OPEN_AI_KEY_ADM',  # Admin key with usage.read scope
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                model=None  # Don't filter by model - time window is sufficient
            )
            
            # Log warning if step completed but has no API calls (may indicate an issue)
            if all_success and api_calls == 0:
                logger.warning(
                    f"⚠️ Step {step_num} completed successfully but recorded 0 API calls!",
                    extra={
                        'run_id': self.run_id,
                        'step': step_num,
                        'event': 'zero_api_calls',
                        'metadata': {
                            'duration': duration,
                            'request': command_text,
                            'note': 'BAeS framework may not have called OpenAI API, or calls happened outside time window'
                        }
                    }
                )
            
            logger.info("BAEs step completed",
                       extra={'run_id': self.run_id, 'step': step_num, 'event': 'step_complete',
                              'metadata': {'tokens_in': tokens_in, 'tokens_out': tokens_out,
                                         'api_calls': api_calls, 'cached_tokens': cached_tokens}})
            
            return {
                'success': all_success,
                'duration_seconds': duration,
                'hitl_count': 0,
                'tokens_in': tokens_in,
                'tokens_out': tokens_out,
                'api_calls': api_calls,
                'cached_tokens': cached_tokens,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
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
                'hitl_count': 0,
                'tokens_in': 0,
                'tokens_out': 0,
                'api_calls': 0,
                'cached_tokens': 0,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
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
            archive_path = Path(self.workspace_path) / "managed_system.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(self.managed_system_dir, arcname="managed_system")
            
            logger.info(f"Archived managed system to {archive_path}", extra={'run_id': self.run_id})
    
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
