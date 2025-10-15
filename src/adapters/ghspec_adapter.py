"""
GitHub Spec-kit framework adapter implementation.

Integrates with GitHub Spec-kit (ghspec) framework for experiment execution.
"""

import subprocess
import time
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import requests
from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GHSpecAdapter(BaseAdapter):
    """Adapter for GitHub Spec-kit framework."""
    
    def __init__(self, config: Dict[str, Any], run_id: str, workspace_path: str):
        """
        Initialize GitHub Spec-kit adapter.
        
        Args:
            config: Framework configuration from experiment.yaml
            run_id: Unique run identifier
            workspace_path: Isolated workspace directory
        """
        super().__init__(config, run_id, workspace_path)
        self.framework_dir = None
        self.hitl_text = None
        
    def start(self) -> None:
        """
        Clone GitHub Spec-kit repository and setup workspace structure.
        
        Phase 2 Implementation:
        - Clone spec-kit repository from configured URL
        - Checkout and verify specific commit hash
        - Setup workspace directory structure for artifacts
        - Initialize feature directory (specs/001-baes-experiment/)
        - GHSpec is CLI-based (bash scripts), no services to start
        
        The workspace will have this structure:
            workspace_path/
                ghspec_framework/        # Cloned spec-kit repo
                specs/                   # Artifact storage
                    001-baes-experiment/ # Feature directory
                        spec.md          # Generated specification
                        plan.md          # Generated technical plan
                        tasks.md         # Generated task list
                        src/             # Generated code files
        """
        logger.info("Starting GitHub Spec-kit framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        repo_url = self.config['repo_url']
        commit_hash = self.config['commit_hash']
        
        # Create framework directory for cloned repo
        self.framework_dir = Path(self.workspace_path) / "ghspec_framework"
        
        try:
            # Clone repository
            logger.info("Cloning GitHub Spec-kit repository",
                       extra={'run_id': self.run_id,
                             'metadata': {'repo': repo_url, 'commit': commit_hash}})
            
            subprocess.run(
                ['git', 'clone', repo_url, str(self.framework_dir)],
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=120
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
            
            # Verify commit hash matches config (reproducibility requirement)
            self.verify_commit_hash(self.framework_dir, commit_hash)
            
            logger.info("GitHub Spec-kit repository cloned and verified",
                       extra={'run_id': self.run_id,
                             'metadata': {'commit': commit_hash}})
            
            # Setup workspace directory structure for artifacts
            self._setup_workspace_structure()
            
            # GHSpec is CLI-based (bash scripts + direct OpenAI API calls)
            # No virtual environment needed - we call OpenAI API directly
            # No persistent services to start - we invoke bash scripts per phase
            
            logger.info("GitHub Spec-kit framework ready",
                       extra={'run_id': self.run_id,
                             'metadata': {
                                 'framework_dir': str(self.framework_dir),
                                 'specs_dir': str(self.specs_dir),
                                 'feature_dir': str(self.feature_dir)
                             }})
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to initialize GitHub Spec-kit",
                        extra={'run_id': self.run_id,
                              'metadata': {'error': str(e),
                                         'stderr': e.stderr.decode() if e.stderr else ''}})
            raise RuntimeError("GitHub Spec-kit initialization failed") from e
        except subprocess.TimeoutExpired as e:
            logger.error("GitHub Spec-kit initialization timed out",
                        extra={'run_id': self.run_id})
            raise RuntimeError("GitHub Spec-kit initialization timed out") from e
    
    def _setup_workspace_structure(self) -> None:
        """
        Create workspace directory structure for GHSpec artifacts.
        
        Creates:
            workspace_path/
                specs/                      # Root for all feature specifications
                    001-baes-experiment/    # Feature directory (fixed name for experiment)
                        spec.md             # Will be generated in Phase 3
                        plan.md             # Will be generated in Phase 3
                        tasks.md            # Will be generated in Phase 3
                        src/                # Will contain generated code (Phase 4)
        
        The feature number and name follow spec-kit conventions:
        - NNN format for feature numbers (001, 002, etc.)
        - Kebab-case for feature names
        - For this experiment, we use "001-baes-experiment" consistently
        """
        # Create specs root directory
        self.specs_dir = Path(self.workspace_path) / "specs"
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create feature directory with fixed name for reproducibility
        # Using "baes-experiment" as the feature name for all runs
        self.feature_dir = self.specs_dir / "001-baes-experiment"
        self.feature_dir.mkdir(parents=True, exist_ok=True)
        
        # Create src directory for generated code (used in Phase 4)
        self.src_dir = self.feature_dir / "src"
        self.src_dir.mkdir(parents=True, exist_ok=True)
        
        # Store artifact paths for easy access in later phases
        self.spec_md_path = self.feature_dir / "spec.md"
        self.plan_md_path = self.feature_dir / "plan.md"
        self.tasks_md_path = self.feature_dir / "tasks.md"
        
        logger.info("Workspace structure created",
                   extra={'run_id': self.run_id,
                         'metadata': {
                             'specs_dir': str(self.specs_dir),
                             'feature_dir': str(self.feature_dir),
                             'src_dir': str(self.src_dir)
                         }})

            
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """
        Execute a step by generating spec/plan/tasks or implementing code.
        
        Phase 3 Implementation (steps 1-3):
        - Step 1: Generate specification (specify phase)
        - Step 2: Generate technical plan (plan phase)
        - Step 3: Generate task breakdown (tasks phase)
        
        Args:
            step_num: Step number (1-6)
            command_text: Natural language command (user's feature request)
            
        Returns:
            Dictionary with execution results including tokens and HITL count
        """
        self.current_step = step_num
        self._step_start_time = time.time()
        
        logger.info("Executing step",
                   extra={'run_id': self.run_id, 'step': step_num, 
                         'event': 'step_start', 
                         'metadata': {'framework': 'ghspec', 'command': command_text[:100]}})
        
        hitl_count = 0
        tokens_in = 0
        tokens_out = 0
        success = False
        
        try:
            # Phase 3: Spec/Plan/Tasks generation (steps 1-3)
            if step_num == 1:
                # Generate specification
                hitl_count, tokens_in, tokens_out = self._execute_phase('specify', command_text)
                success = self.spec_md_path.exists()
                
            elif step_num == 2:
                # Generate technical plan (requires spec.md)
                if not self.spec_md_path.exists():
                    raise RuntimeError("spec.md not found - run step 1 first")
                hitl_count, tokens_in, tokens_out = self._execute_phase('plan', command_text)
                success = self.plan_md_path.exists()
                
            elif step_num == 3:
                # Generate task breakdown (requires spec.md and plan.md)
                if not self.spec_md_path.exists() or not self.plan_md_path.exists():
                    raise RuntimeError("spec.md or plan.md not found - run steps 1-2 first")
                hitl_count, tokens_in, tokens_out = self._execute_phase('tasks', command_text)
                success = self.tasks_md_path.exists()
                
            # Phase 4: Task-by-task implementation (steps 4-5)
            elif step_num in [4, 5]:
                # TODO: Implement task-by-task code generation
                logger.warning("Phase 4 not yet implemented",
                             extra={'run_id': self.run_id, 'step': step_num})
                success = False
                
            # Phase 5: Bugfix cycle (step 6)
            elif step_num == 6:
                # TODO: Implement validation-driven bugfix
                logger.warning("Phase 5 not yet implemented",
                             extra={'run_id': self.run_id, 'step': step_num})
                success = False
                
            else:
                raise ValueError(f"Invalid step number: {step_num}")
                
        except Exception as e:
            logger.error("Step execution failed",
                        extra={'run_id': self.run_id, 'step': step_num,
                              'metadata': {'error': str(e)}})
            success = False
            # Re-raise to let orchestrator handle
            raise
        
        duration = time.time() - self._step_start_time
        
        logger.info("Step completed",
                   extra={'run_id': self.run_id, 'step': step_num,
                         'event': 'step_complete',
                         'metadata': {
                             'success': success,
                             'duration': duration,
                             'hitl_count': hitl_count,
                             'tokens_in': tokens_in,
                             'tokens_out': tokens_out
                         }})
        
        return {
            'success': success,
            'duration_seconds': duration,
            'hitl_count': hitl_count,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'retry_count': 0
        }
    
    def _execute_phase(self, phase: str, command_text: str) -> Tuple[int, int, int]:
        """
        Execute a single GHSpec phase (specify, plan, or tasks).
        
        Phase 3 Implementation:
        1. Load prompt template for this phase
        2. Build complete prompt with context
        3. Call OpenAI API (with timestamp tracking)
        4. Check for clarification requests
        5. Handle HITL if needed
        6. Save artifact to workspace
        7. Fetch token usage from OpenAI Usage API
        
        Args:
            phase: Phase name ('specify', 'plan', or 'tasks')
            command_text: User's feature request (used in specify phase)
            
        Returns:
            Tuple of (hitl_count, tokens_in, tokens_out)
        """
        logger.info(f"Executing {phase} phase",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {'phase': phase}})
        
        # Load prompt template
        template_path = Path(f"docs/ghspec/prompts/{phase}_template.md")
        system_prompt, user_prompt_template = self._load_prompt_template(template_path)
        
        # Build complete user prompt with context
        user_prompt = self._build_phase_prompt(phase, user_prompt_template, command_text)
        
        # Track start time for Usage API query
        api_call_start = int(time.time())
        
        # Call OpenAI API
        response_text = self._call_openai(system_prompt, user_prompt)
        
        # Check for clarification requests
        hitl_count = 0
        if self._needs_clarification(response_text):
            logger.info(f"Clarification needed in {phase} phase",
                       extra={'run_id': self.run_id, 'step': self.current_step})
            
            # Handle HITL by appending guidelines and regenerating
            clarification_text = self._handle_clarification(response_text)
            user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
            
            # Regenerate with clarification
            response_text = self._call_openai(system_prompt, user_prompt_with_hitl)
            hitl_count = 1
        
        # Save artifact
        output_path = {
            'specify': self.spec_md_path,
            'plan': self.plan_md_path,
            'tasks': self.tasks_md_path
        }[phase]
        
        self._save_artifact(output_path, response_text)
        
        # Fetch token usage from OpenAI Usage API
        api_call_end = int(time.time())
        tokens_in, tokens_out = self.fetch_usage_from_openai(
            api_key_env_var=self.config['api_key_env'],
            start_timestamp=api_call_start,
            end_timestamp=api_call_end,
            model='gpt-4o-mini'  # From experiment.yaml
        )
        
        logger.info(f"Phase {phase} completed",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'output_path': str(output_path),
                             'hitl_count': hitl_count,
                             'tokens_in': tokens_in,
                             'tokens_out': tokens_out
                         }})
        
        return hitl_count, tokens_in, tokens_out
    
    def _load_prompt_template(self, template_path: Path) -> Tuple[str, str]:
        """
        Load system and user prompt templates from markdown file.
        
        Expects template structure:
        ## System Prompt
        ```
        system prompt text
        ```
        
        ## User Prompt Template
        ```
        user prompt with {placeholders}
        ```
        
        Args:
            template_path: Path to prompt template markdown file
            
        Returns:
            Tuple of (system_prompt, user_prompt_template)
        """
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract system prompt (between ## System Prompt and next ##)
        system_match = re.search(
            r'## System Prompt\s*```\s*(.*?)\s*```',
            content,
            re.DOTALL
        )
        system_prompt = system_match.group(1).strip() if system_match else ""
        
        # Extract user prompt template
        user_match = re.search(
            r'## User Prompt Template\s*```\s*(.*?)\s*```',
            content,
            re.DOTALL
        )
        user_prompt_template = user_match.group(1).strip() if user_match else ""
        
        if not system_prompt or not user_prompt_template:
            raise ValueError(f"Invalid template format in {template_path}")
        
        return system_prompt, user_prompt_template
    
    def _build_phase_prompt(self, phase: str, template: str, command_text: str) -> str:
        """
        Build complete user prompt by filling template with context.
        
        Args:
            phase: Phase name ('specify', 'plan', or 'tasks')
            template: User prompt template with placeholders
            command_text: User's feature request
            
        Returns:
            Complete user prompt with all placeholders filled
        """
        if phase == 'specify':
            # Specify phase: just substitute user command
            return template.replace('{user_command}', command_text)
            
        elif phase == 'plan':
            # Plan phase: substitute spec content
            spec_content = self.spec_md_path.read_text(encoding='utf-8')
            return template.replace('{spec_content}', spec_content)
            
        elif phase == 'tasks':
            # Tasks phase: substitute spec + plan content
            spec_content = self.spec_md_path.read_text(encoding='utf-8')
            plan_content = self.plan_md_path.read_text(encoding='utf-8')
            return (template
                   .replace('{spec_content}', spec_content)
                   .replace('{plan_content}', plan_content))
        
        else:
            raise ValueError(f"Unknown phase: {phase}")
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call OpenAI API directly with chat completion.
        
        Uses configuration from experiment.yaml:
        - API key from environment variable (api_key_env)
        - Model: gpt-4o-mini (from model config)
        - Temperature: 0 (deterministic)
        
        Args:
            system_prompt: System role instructions
            user_prompt: User message/request
            
        Returns:
            Response text from assistant
        """
        api_key = os.getenv(self.config['api_key_env'])
        if not api_key:
            raise RuntimeError(f"API key not found in {self.config['api_key_env']}")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",  # From experiment.yaml
            "temperature": 0,  # Deterministic
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        logger.debug("Calling OpenAI API",
                    extra={'run_id': self.run_id, 'step': self.current_step,
                          'metadata': {
                              'model': 'gpt-4o-mini',
                              'system_prompt_length': len(system_prompt),
                              'user_prompt_length': len(user_prompt)
                          }})
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        assistant_message = result['choices'][0]['message']['content']
        
        return assistant_message
    
    def _needs_clarification(self, response_text: str) -> bool:
        """
        Detect if model response contains clarification requests.
        
        Looks for pattern: [NEEDS CLARIFICATION: ...]
        
        Args:
            response_text: Model's response
            
        Returns:
            True if clarification is needed, False otherwise
        """
        return '[NEEDS CLARIFICATION:' in response_text
    
    def _handle_clarification(self, response_text: str) -> str:
        """
        Return clarification guidelines from HITL file.
        
        This method is called when the model requests clarification.
        It loads the fixed clarification guidelines and returns them.
        
        Note: This delegates to handle_hitl() which manages the HITL text cache.
        
        Args:
            response_text: Model's response containing clarification request
            
        Returns:
            Fixed clarification guidelines text
        """
        # Extract the specific question (for logging)
        clarification_match = re.search(
            r'\[NEEDS CLARIFICATION: (.*?)\]',
            response_text,
            re.DOTALL
        )
        question = clarification_match.group(1).strip() if clarification_match else "unclear"
        
        # Get fixed HITL response
        return self.handle_hitl(question)
    
    def _save_artifact(self, output_path: Path, content: str) -> None:
        """
        Save generated artifact to workspace.
        
        Args:
            output_path: Path to save artifact
            content: Artifact content (markdown)
        """
        output_path.write_text(content, encoding='utf-8')
        
        logger.info("Artifact saved",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'path': str(output_path),
                             'size_bytes': len(content.encode('utf-8'))
                         }})
        
    def health_check(self) -> bool:
        """
        Check if GitHub Spec-kit framework is ready.
        
        GHSpec is CLI-based with no persistent services, so we just verify:
        - Framework directory exists
        - Workspace structure is set up
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.framework_dir or not self.framework_dir.exists():
            return False
        
        if not hasattr(self, 'specs_dir') or not self.specs_dir.exists():
            return False
            
        return True
            
    def handle_hitl(self, query: str) -> str:
        """
        Return fixed HITL response for deterministic execution.
        
        Note: GHSpec uses different HITL content than ChatDev/BAEs because it
        generates specifications incrementally. This returns meta-guidelines
        for handling ambiguous requirements, not a concrete specification.
        
        Args:
            query: Framework's clarification question
            
        Returns:
            Fixed clarification guidelines text
        """
        if self.hitl_text is None:
            # Load GHSpec-specific clarification guidelines
            hitl_path = Path("config/hitl/ghspec_clarification_guidelines.txt")
            with open(hitl_path, 'r', encoding='utf-8') as f:
                self.hitl_text = f.read().strip()
                
        logger.info("HITL intervention",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'event': 'hitl', 
                         'metadata': {'query_length': len(query), 'framework': 'ghspec'}})
                         
        return self.hitl_text
        
    def stop(self) -> None:
        """
        Gracefully shutdown GitHub Spec-kit framework.
        
        GHSpec is CLI-based with no persistent services, so cleanup is minimal:
        - Log shutdown event
        - Workspace artifacts are preserved (intentional)
        """
        logger.info("Stopping GitHub Spec-kit framework",
                   extra={'run_id': self.run_id, 'event': 'framework_stop'})
        
        # No services to terminate - GHSpec uses direct OpenAI API calls
        # Workspace and artifacts are intentionally preserved for analysis
        
        logger.info("GitHub Spec-kit framework stopped",
                   extra={'run_id': self.run_id, 'event': 'framework_stopped'})
