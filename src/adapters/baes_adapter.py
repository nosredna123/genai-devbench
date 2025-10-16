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
from typing import Any, Dict, List, Tuple

from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BAeSAdapter(BaseAdapter):
    """Adapter for Business Autonomous Entities (BAEs) framework."""
    
    COMMAND_MAPPING = {
        "Create a Student/Course/Teacher CRUD application":
            ["add student entity", "add course entity", "add teacher entity"],
        "Add enrollment relationship between Student and Course":
            ["add course to student entity"],
        "Add teacher assignment relationship to Course":
            ["add teacher to course entity"],
        "Implement comprehensive data validation":
            ["add validation to all entities"],
        "Enhance UI with filtering and sorting":
            ["enhance ui with filtering and sorting"],
        "Add automated testing":
            ["add automated tests"]
    }
    
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
        commit_hash = self.config.get('commit_hash', 'HEAD')
        
        try:
            if repo_url.startswith('file://'):
                local_path = repo_url[7:]
                logger.info(f"Copying local BAEs repository from {local_path}",
                           extra={'run_id': self.run_id})
                shutil.copytree(local_path, self.framework_dir, symlinks=False)
            else:
                logger.info(f"Cloning BAEs repository from {repo_url}",
                           extra={'run_id': self.run_id})
                subprocess.run(
                    ['git', 'clone', repo_url, str(self.framework_dir)],
                    check=True,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                    timeout=300
                )
            
            if commit_hash != 'HEAD':
                logger.info(f"Checking out commit {commit_hash}",
                           extra={'run_id': self.run_id})
                subprocess.run(
                    ['git', 'checkout', commit_hash],
                    cwd=self.framework_dir,
                    check=True,
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                    timeout=60
                )
            
            self.verify_commit_hash(self.framework_dir, commit_hash)
            
            logger.info("Setting up isolated virtual environment",
                       extra={'run_id': self.run_id, 'event': 'venv_setup_start'})
            self._setup_virtual_environment()
            
            os.environ['BAE_CONTEXT_STORE_PATH'] = str(self.database_dir / "context_store.json")
            os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
            os.environ['API_PORT'] = str(self.config.get('api_port', 8100))
            os.environ['UI_PORT'] = str(self.config.get('ui_port', 8600))
            os.environ['BAE_MAX_RETRIES'] = str(self.config.get('max_retries', 3))
            
            baes_api_key = os.getenv('OPENAI_API_KEY_BAES')
            if baes_api_key:
                os.environ['OPENAI_API_KEY'] = baes_api_key
                logger.info("BAEs API key configured for token tracking",
                           extra={'run_id': self.run_id})
            else:
                logger.warning("OPENAI_API_KEY_BAES not set - using default key",
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
        """Execute a BAEs kernel request using the wrapper script in the venv.
        
        Args:
            request: Natural language request
            start_servers: Whether to start API/UI servers
            
        Returns:
            Dictionary with 'success' and 'result' or 'error'
        """
        wrapper_script = Path(__file__).parent / "baes_kernel_wrapper.py"
        context_store_path = str(self.database_dir / "context_store.json")
        venv_python = self.venv_path / "bin" / "python"
        
        cmd = [
            str(venv_python),
            str(wrapper_script),
            str(self.framework_dir),
            context_store_path,
            request,
            str(start_servers).lower()
        ]
        
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
                return {
                    'success': False,
                    'error': f"Wrapper script failed: {result.stderr}"
                }
            
            # Parse JSON output
            import json
            return json.loads(result.stdout)
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Request execution timed out after 5 minutes'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Failed to parse wrapper output: {e}\nOutput: {result.stdout}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {e}'
            }
    
    def execute_step(self, step_num: int, command_text: str) -> Tuple[bool, float, int, int, float, float]:
        start_timestamp = time.time()
        self.current_step = step_num
        
        logger.info("Executing BAEs step",
                   extra={'run_id': self.run_id, 'step': step_num, 'event': 'step_start'})
        
        try:
            requests_list = self._translate_command_to_requests(command_text)
            
            if not requests_list:
                logger.warning(f"No BAEs requests mapped for command: {command_text}",
                             extra={'run_id': self.run_id, 'step': step_num})
                requests_list = [command_text]
            
            all_success = True
            for idx, request in enumerate(requests_list):
                logger.info(f"Executing BAEs request {idx+1}/{len(requests_list)}: {request}",
                           extra={'run_id': self.run_id, 'step': step_num})
                
                start_servers = (step_num == 1 and idx == 0)
                
                result = self._execute_kernel_request(
                    request=request,
                    start_servers=start_servers
                )
                
                if not result.get('success', False):
                    all_success = False
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"BAEs request failed: {request}",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'metadata': {'error': error_msg}})
                    break
                
                logger.info(f"BAEs request {idx+1}/{len(requests_list)} completed successfully",
                           extra={'run_id': self.run_id, 'step': step_num})
            
            end_timestamp = time.time()
            duration = end_timestamp - start_timestamp
            
            tokens_in = 0
            tokens_out = 0
            
            logger.info("BAEs step completed",
                       extra={'run_id': self.run_id, 'step': step_num, 'event': 'step_complete'})
            
            return {
                'success': all_success,
                'duration_seconds': duration,
                'hitl_count': 0,
                'tokens_in': tokens_in,
                'tokens_out': tokens_out,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
                'retry_count': 0
            }
            
        except Exception as e:
            end_timestamp = time.time()
            logger.error(f"BAEs step failed with exception: {e}",
                        extra={'run_id': self.run_id, 'step': step_num})
            return {
                'success': False,
                'duration_seconds': end_timestamp - start_timestamp,
                'hitl_count': 0,
                'tokens_in': 0,
                'tokens_out': 0,
                'start_timestamp': start_timestamp,
                'end_timestamp': end_timestamp,
                'retry_count': 0
            }
    
    def _translate_command_to_requests(self, command_text: str) -> List[str]:
        if command_text in self.COMMAND_MAPPING:
            return self.COMMAND_MAPPING[command_text]
        
        command_lower = command_text.lower()
        for key, value in self.COMMAND_MAPPING.items():
            if key.lower() in command_lower or command_lower in key.lower():
                return value
        
        return []
    
    def stop(self) -> None:
        logger.info("Stopping BAEs framework", extra={'run_id': self.run_id})
        
        if hasattr(self, '_kernel') and self._kernel:
            try:
                if hasattr(self._kernel, '_managed_system_manager'):
                    mgr = self._kernel._managed_system_manager
                    if mgr and hasattr(mgr, 'stop_servers'):
                        mgr.stop_servers()
            except Exception as e:
                logger.warning(f"Error stopping servers via kernel: {e}",
                             extra={'run_id': self.run_id})
        
        self._ensure_servers_stopped()
        self._archive_managed_system()
        
        logger.info("BAEs framework stopped", extra={'run_id': self.run_id})
    
    def _ensure_servers_stopped(self) -> None:
        api_port = self.config.get('api_port', 8100)
        ui_port = self.config.get('ui_port', 8600)
        
        for port in [api_port, ui_port]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    if sock.connect_ex(("localhost", port)) == 0:
                        subprocess.run(
                            f"lsof -ti:{port} | xargs kill -9",
                            shell=True,
                            timeout=10,
                            stderr=subprocess.DEVNULL,
                            check=False
                        )
                        time.sleep(1)
            except Exception:
                pass
    
    def _archive_managed_system(self) -> None:
        if self.managed_system_dir and self.managed_system_dir.exists():
            archive_path = Path(self.workspace_path) / "managed_system.tar.gz"
            
            try:
                with tarfile.open(archive_path, "w:gz") as tar:
                    tar.add(self.managed_system_dir, arcname="managed_system")
                
                logger.info(f"Archived managed system to {archive_path}", extra={'run_id': self.run_id})
            except Exception as e:
                logger.warning(f"Failed to archive managed system: {e}", extra={'run_id': self.run_id})
    
    def health_check(self) -> bool:
        try:
            if not hasattr(self, '_kernel') or not self._kernel:
                return False
            
            context_store = self._kernel.context_store
            if not context_store:
                return False
            
            supported_entities = self._kernel.bae_registry.get_supported_entities()
            if not supported_entities:
                return False
            
            if self._should_check_endpoints():
                if not self._check_http_endpoints():
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _should_check_endpoints(self) -> bool:
        return (hasattr(self, 'current_step') and 
                self.current_step >= 2 and
                self.managed_system_dir and
                self.managed_system_dir.exists())
    
    def _check_http_endpoints(self) -> bool:
        import requests
        
        api_port = self.config.get('api_port', 8100)
        ui_port = self.config.get('ui_port', 8600)
        
        try:
            response = requests.get(f"http://localhost:{api_port}/docs", timeout=5)
            if response.status_code != 200:
                return False
        except requests.RequestException:
            return False
        
        try:
            response = requests.get(f"http://localhost:{ui_port}/", timeout=5)
            if response.status_code != 200:
                return False
        except requests.RequestException:
            return False
        
        return True
    
    def handle_hitl(self, query: str) -> str:
        if self.hitl_text is None:
            hitl_path = Path("config/hitl/expanded_spec.txt")
            if hitl_path.exists():
                with open(hitl_path, 'r', encoding='utf-8') as f:
                    self.hitl_text = f.read().strip()
            else:
                self.hitl_text = """Create a complete CRUD system with:
- Student entity: name, email, enrollment_date
- Course entity: code, title, credits
- Teacher entity: name, email, department
- Full CRUD operations for all entities
- FastAPI backend, Streamlit UI, SQLite database""".strip()
        
        logger.info("HITL intervention", extra={'run_id': self.run_id, 'step': self.current_step})
        
        return self.hitl_text
