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
                stdin=subprocess.DEVNULL,
                timeout=300
            )
            
            # Checkout specific commit
            subprocess.run(
                ['git', 'checkout', commit_hash],
                cwd=self.framework_dir,
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=60
            )
            
            # Verify commit hash matches config (T038 - reproducibility)
            self.verify_commit_hash(self.framework_dir, commit_hash)
            
            logger.info("ChatDev repository cloned and verified",
                       extra={'run_id': self.run_id, 
                             'metadata': {'commit': commit_hash}})
            
            # T064: Set up virtual environment and install dependencies
            self._setup_virtual_environment()
            
            # Apply compatibility patches for OpenAI API changes
            self._patch_openai_compatibility()
            self._patch_o1_model_support()
            
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
                stdin=subprocess.DEVNULL,
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
                stdin=subprocess.DEVNULL,
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
                stdin=subprocess.DEVNULL,
                timeout=120,
                cwd=self.framework_dir
            )
            
            # CRITICAL FIX: Pin compatible versions BEFORE installing requirements
            # - pydantic<2: ChatDev uses pydantic 1.x dataclasses
            # - httpx<0.28: httpx 0.28+ removed 'proxies' parameter used by openai
            # - openai<1.40: Newer versions include 'annotations' field that ChatDev doesn't support
            logger.info("Pre-installing pydantic<2, httpx<0.28, openai<1.40",
                       extra={'run_id': self.run_id})
            
            result = subprocess.run(
                [str(pip_path), "install", "-v", "pydantic<2", "httpx<0.28", "openai<1.40"],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=120,
                cwd=self.framework_dir
            )
            
            if result.returncode != 0:
                logger.error("Pre-install failed", extra={'run_id': self.run_id,
                           'metadata': {'stderr': result.stderr[:1000]}})
                raise RuntimeError(f"Failed to pre-install compatible versions: {result.stderr}")
            
            logger.info("Pre-install successful",
                       extra={'run_id': self.run_id,
                             'metadata': {'stdout_tail': result.stdout[-500:] if result.stdout else ''}})
            
            # Now install requirements.txt with --no-deps to prevent upgrades
            # Then install missing dependencies separately
            logger.info("Installing requirements with --no-deps",
                       extra={'run_id': self.run_id})
            
            result = subprocess.run(
                [str(pip_path), "install", "--no-deps", "-r", "requirements.txt"],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=600,
                cwd=self.framework_dir
            )
            
            if result.returncode != 0:
                logger.error("No-deps install failed", extra={'run_id': self.run_id,
                           'metadata': {'stderr': result.stderr[:1000]}})
                raise RuntimeError(f"Failed to install requirements (no-deps): {result.stderr}")
            
            # Now install missing dependencies (but pydantic and httpx are already pinned)
            logger.info("Installing missing dependencies",
                       extra={'run_id': self.run_id})
            
            result = subprocess.run(
                [str(pip_path), "install", "-r", "requirements.txt"],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=600,
                cwd=self.framework_dir
            )
            
            if result.returncode != 0:
                logger.error("Dependencies install failed", extra={'run_id': self.run_id,
                           'metadata': {'stderr': result.stderr[:1000]}})
                raise RuntimeError(f"Failed to install dependencies: {result.stderr}")
            
            # Verify pydantic version (critical for ChatMessage compatibility)
            verify_result = subprocess.run(
                [str(pip_path), "show", "pydantic"],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=10,
                cwd=self.framework_dir
            )
            
            pydantic_version = "unknown"
            if verify_result.returncode == 0:
                for line in verify_result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        pydantic_version = line.split(':', 1)[1].strip()
                        break
            
            logger.info("ChatDev dependencies installed successfully",
                       extra={'run_id': self.run_id,
                             'event': 'dependency_install_complete',
                             'metadata': {'pydantic_version': pydantic_version}})
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Dependency installation timed out after 10 minutes")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Dependency installation failed: {e}") from e
    
    def _patch_openai_compatibility(self) -> None:
        """
        Apply compatibility patch for OpenAI API changes.
        
        OpenAI's API evolves faster than ChatDev's codebase. When new fields are added
        to API responses (like 'audio' and 'annotations'), ChatDev's dataclasses fail
        with "unexpected keyword argument" errors.
        
        This method applies the same fix pattern that ChatDev maintainers use
        (see commit 52edb89 for the 'audio' field fix). We add 'annotations' field
        following the same pattern.
        
        NOTE: This is a temporary compatibility layer. Ideally, ChatDev upstream
        should be updated to handle new API fields, or we should use a fork that
        already has these fixes.
        """
        chat_messages_file = self.framework_dir / "camel" / "messages" / "chat_messages.py"
        
        if not chat_messages_file.exists():
            logger.warning("chat_messages.py not found, skipping compatibility patch",
                          extra={'run_id': self.run_id,
                                'metadata': {'expected_path': str(chat_messages_file)}})
            return
        
        content = chat_messages_file.read_text()
        
        # Check if already patched
        if 'annotations: object = None' in content:
            logger.info("OpenAI compatibility patch already applied",
                       extra={'run_id': self.run_id})
            return
        
        # Add 'annotations' field after 'audio' field (following commit 52edb89 pattern)
        old_line = '    audio: object = None'
        new_lines = '    audio: object = None\n    annotations: object = None  # Compatibility patch for OpenAI API'
        
        if old_line in content:
            patched_content = content.replace(old_line, new_lines)
            occurrences = content.count(old_line)
            
            chat_messages_file.write_text(patched_content)
            
            logger.info("Applied OpenAI compatibility patch",
                       extra={'run_id': self.run_id,
                             'metadata': {'classes_patched': occurrences,
                                        'field_added': 'annotations',
                                        'file': str(chat_messages_file)}})
        else:
            logger.warning("Could not apply compatibility patch - 'audio' field not found",
                          extra={'run_id': self.run_id,
                                'metadata': {'file': str(chat_messages_file)}})
    
    def _patch_o1_model_support(self) -> None:
        """
        Add O1 and GPT-5 model support via runtime patching.
        
        ChatDev doesn't support these models yet. This method patches multiple files to add:
        1. Model types to camel/typing.py
        2. Token limits to model_backend.py and ecl/utils.py  
        3. Pricing info to chatdev/statistics.py
        4. CLI argument mapping in run.py
        
        Model Specifications:
        - o1-preview: 128k context, $15/1M input, $60/1M output
        - o1-mini: 128k context, $3/1M input, $12/1M output
        - gpt-5-mini: $0.25/1M input, $2.00/1M output (cached: $0.025/1M)
        
        Note: O1 models don't support streaming, system messages, or temperature
        """
        patches_applied = []
        
        # Patch 1: Add O1 and GPT-5 models to ModelType enum in camel/typing.py
        typing_file = self.framework_dir / "camel" / "typing.py"
        if typing_file.exists():
            content = typing_file.read_text()
            if 'O1_MINI' not in content:
                # Add after GPT_4O_MINI line
                old_line = '    GPT_4O_MINI = "gpt-4o-mini"'
                new_lines = '''    GPT_4O_MINI = "gpt-4o-mini"
    O1_PREVIEW = "o1-preview"  # O1 model patch
    O1_MINI = "o1-mini"  # O1 model patch
    GPT_5_MINI = "gpt-5-mini"  # GPT-5 model patch'''
                content = content.replace(old_line, new_lines)
                typing_file.write_text(content)
                patches_applied.append('camel/typing.py')
        
        # Patch 2: Add O1 and GPT-5 token limits to camel/model_backend.py
        model_backend_file = self.framework_dir / "camel" / "model_backend.py"
        if model_backend_file.exists():
            content = model_backend_file.read_text()
            if '"o1-mini"' not in content:
                # Add to both num_max_token_map occurrences
                old_map_entry = '"gpt-4o-mini": 16384, #100000'
                new_map_entry = '''"gpt-4o-mini": 16384, #100000
                "o1-preview": 128000,  # O1 model patch
                "o1-mini": 128000,  # O1 model patch
                "gpt-5-mini": 128000,  # GPT-5 model patch'''
                content = content.replace(old_map_entry, new_map_entry)
                model_backend_file.write_text(content)
                patches_applied.append('camel/model_backend.py')
        
        # Patch 3: Add O1 and GPT-5 token limits to ecl/utils.py  
        ecl_utils_file = self.framework_dir / "ecl" / "utils.py"
        if ecl_utils_file.exists():
            content = ecl_utils_file.read_text()
            if '"o1-mini"' not in content:
                old_map_entry = '"gpt-4o-mini": 16384, #100000'
                new_map_entry = '''"gpt-4o-mini": 16384, #100000
        "o1-preview": 128000,  # O1 model patch
        "o1-mini": 128000,  # O1 model patch
        "gpt-5-mini": 128000,  # GPT-5 model patch'''
                content = content.replace(old_map_entry, new_map_entry)
                ecl_utils_file.write_text(content)
                patches_applied.append('ecl/utils.py')
        
        # Patch 4: Add O1 and GPT-5 pricing to chatdev/statistics.py
        statistics_file = self.framework_dir / "chatdev" / "statistics.py"
        if statistics_file.exists():
            content = statistics_file.read_text()
            if '"o1-mini"' not in content:
                # Add to prompt_cost_map (input pricing per 1M tokens)
                old_input = '"gpt-4o-mini": 0.00015,'
                new_input = '''"gpt-4o-mini": 0.00015,
        "o1-preview": 0.015,  # O1 model patch: $15/1M input
        "o1-mini": 0.003,  # O1 model patch: $3/1M input
        "gpt-5-mini": 0.00025,  # GPT-5 model patch: $0.25/1M input'''
                content = content.replace(old_input, new_input)
                
                # Add to completion_cost_map (output pricing per 1M tokens)
                old_output = '"gpt-4o-mini": 0.0006,'
                new_output = '''"gpt-4o-mini": 0.0006,
        "o1-preview": 0.060,  # O1 model patch: $60/1M output
        "o1-mini": 0.012,  # O1 model patch: $12/1M output
        "gpt-5-mini": 0.002,  # GPT-5 model patch: $2.00/1M output'''
                content = content.replace(old_output, new_output)
                
                # Add to model type conversion
                old_conversion = '                model_type = "gpt-4o-mini"'
                new_conversion = '''                model_type = "gpt-4o-mini"
            elif model_type == "O1_PREVIEW":  # O1 model patch
                model_type = "o1-preview"
            elif model_type == "O1_MINI":  # O1 model patch
                model_type = "o1-mini"
            elif model_type == "GPT_5_MINI":  # GPT-5 model patch
                model_type = "gpt-5-mini"'''
                content = content.replace(old_conversion, new_conversion)
                
                statistics_file.write_text(content)
                patches_applied.append('chatdev/statistics.py')
        
        # Patch 5: Add O1 and GPT-5 to CLI argument mapping in run.py
        run_file = self.framework_dir / "run.py"
        if run_file.exists():
            content = run_file.read_text()
            if 'O1_MINI' not in content:
                # Add to args2type mapping (skip help text to avoid syntax issues)
                old_mapping = "            'GPT_4O_MINI': ModelType.GPT_4O_MINI,"
                new_mapping = '''            'GPT_4O_MINI': ModelType.GPT_4O_MINI,
            'O1_PREVIEW': ModelType.O1_PREVIEW,  # O1 model patch
            'O1_MINI': ModelType.O1_MINI,  # O1 model patch
            'GPT_5_MINI': ModelType.GPT_5_MINI,  # GPT-5 model patch'''
                content = content.replace(old_mapping, new_mapping)
                
                run_file.write_text(content)
                patches_applied.append('run.py')
        
        if patches_applied:
            logger.info("Applied O1/GPT-5 model support patches",
                       extra={'run_id': self.run_id,
                             'metadata': {'files_patched': patches_applied,
                                        'models_added': ['o1-preview', 'o1-mini', 'gpt-5-mini']}})
        else:
            logger.info("O1/GPT-5 model patches already applied or files not found",
                       extra={'run_id': self.run_id})
            
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
        
        # Get API key from environment
        api_key_env = self.config.get('api_key_env', 'OPENAI_API_KEY_CHATDEV')
        api_key = os.getenv(api_key_env)
        
        logger.info("API key retrieval", extra={'run_id': self.run_id, 
                   'metadata': {'env_var': api_key_env, 
                               'key_found': bool(api_key),
                               'key_length': len(api_key) if api_key else 0}})
        
        if not api_key:
            raise RuntimeError(f"API key not found in environment: {api_key_env}")
        
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
        
        # Construct ChatDev command
        # Using Default config for fully automated execution (no HITL)
        cmd = [
            str(self.python_path),
            "run.py",
            "--task", command_text,
            "--name", project_name,
            "--org", "BAEs_Experiment",
            "--config", "Default",  # Fully automated mode
            "--model", chatdev_model
        ]
        
        logger.info("Invoking ChatDev",
                   extra={'run_id': self.run_id, 'step': step_num,
                         'metadata': {'project': project_name, 'model': chatdev_model}})
        
        # Execute ChatDev with timeout
        # IMPORTANT: ChatDev expects OPENAI_API_KEY (not our custom name)
        env = os.environ.copy()
        
        # Clean Python-related environment variables to ensure venv isolation
        # Remove system Python paths that could interfere with venv
        for key in ['PYTHONPATH', 'PYTHONHOME', '__PYVENV_LAUNCHER__']:
            env.pop(key, None)
        
        # Set virtual environment variables
        env['VIRTUAL_ENV'] = str(self.venv_path)
        env['PATH'] = f"{self.venv_path / 'bin'}:{env.get('PATH', '')}"
        env['OPENAI_API_KEY'] = api_key  # Set standard OpenAI key name
        
        logger.info("Environment setup for subprocess", extra={'run_id': self.run_id,
                   'metadata': {'OPENAI_API_KEY_set': 'OPENAI_API_KEY' in env,
                               'OPENAI_API_KEY_length': len(env.get('OPENAI_API_KEY', '')),
                               'VIRTUAL_ENV': env.get('VIRTUAL_ENV', ''),
                               'PYTHONPATH_removed': 'PYTHONPATH' not in env,
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
                logger.error("ChatDev execution failed",
                           extra={'run_id': self.run_id, 'step': step_num,
                                 'metadata': {
                                     'exit_code': result.returncode,
                                     'stderr': result.stderr[:1000] if result.stderr else '',
                                     'stdout_preview': result.stdout[:500] if result.stdout else ''
                                 }})
            
            # Fetch token usage from OpenAI Usage API
            # This replaces framework-specific log parsing with a general DRY approach
            api_key_env = self.config.get('api_key_env', 'OPENAI_API_KEY_CHATDEV')
            model_config = self.config.get('model')  # From experiment.yaml
            
            logger.info(
                "Fetching token usage from OpenAI Usage API",
                extra={
                    'run_id': self.run_id,
                    'step': step_num,
                    'metadata': {
                        'start_timestamp': self._step_start_time,
                        'end_timestamp': end_timestamp,
                        'model': model_config
                    }
                }
            )
            
            tokens_in, tokens_out = self.fetch_usage_from_openai(
                api_key_env_var=api_key_env,
                start_timestamp=self._step_start_time,
                end_timestamp=end_timestamp,
                model=model_config
            )
            
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
                stdin=subprocess.DEVNULL,
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
