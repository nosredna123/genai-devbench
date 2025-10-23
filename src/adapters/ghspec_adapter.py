"""
GitHub Spec-kit framework adapter implementation.

Integrates with GitHub Spec-kit (ghspec) framework for experiment execution.
"""

import subprocess
import time
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import requests
from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__, component="adapter")


class GHSpecAdapter(BaseAdapter):
    """Adapter for GitHub Spec-kit framework."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        run_id: str,
        workspace_path: str,
        sprint_num: int = 1,
        run_dir: Optional[Path] = None
    ):
        """
        Initialize GitHub Spec-kit adapter.
        
        Args:
            config: Framework configuration from experiment.yaml
            run_id: Unique run identifier
            workspace_path: Isolated workspace directory
            sprint_num: Current sprint number (1-indexed)
            run_dir: Run directory path (required for sprint-aware runs)
        """
        super().__init__(config, run_id, workspace_path, sprint_num, run_dir)
        self.framework_dir = None
        self.hitl_text = None
        # Get project root for resolving template paths
        self.project_root = Path(__file__).parent.parent.parent
        self.last_execution_error = None  # Track last framework execution error for debugging
        
    def start(self) -> None:
        """
        Initialize GitHub Spec-kit framework and setup workspace structure.
        
        REFACTORED: Uses shared framework instead of per-run clone.
        - References shared frameworks/ghspec/ directory (read-only)
        - Creates per-run workspace structure for artifacts
        - Initialize feature directory (specs/001-baes-experiment/)
        - GHSpec is CLI-based (bash scripts), no services to start
        
        The workspace will have this structure:
            frameworks/ghspec/           # Shared framework (read-only)
            workspace_path/
                specs/                   # Artifact storage (per-run)
                    001-baes-experiment/ # Feature directory
                        spec.md          # Generated specification
                        plan.md          # Generated technical plan
                        tasks.md         # Generated task list
                        src/             # Generated code files
        """
        logger.info("Starting GitHub Spec-kit framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        try:
            # Reference shared framework (read-only) - NOT per-run clone
            # setup_frameworks.py already cloned ghspec into frameworks/ghspec/
            self.framework_dir = self.get_shared_framework_path('ghspec')
            
            # Validate framework exists
            if not self.framework_dir.exists():
                raise RuntimeError(
                    f"Shared ghspec framework not found at {self.framework_dir}. "
                    "Run setup_frameworks.py first."
                )
            
            logger.info("Using shared GitHub Spec-kit framework",
                       extra={'run_id': self.run_id,
                             'metadata': {'framework_dir': str(self.framework_dir)}})
            
            # Create per-run workspace structure for artifacts
            # This is writable and isolated per run
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
            
        except RuntimeError as e:
            logger.error("Failed to initialize GitHub Spec-kit",
                        extra={'run_id': self.run_id,
                              'metadata': {'error': str(e)}})
            raise RuntimeError("GitHub Spec-kit initialization failed") from e
    
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
        # Create directory structure
        self.specs_dir = Path(self.workspace_path) / "specs"
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        
        self.feature_dir = self.specs_dir / "001-baes-experiment"
        self.feature_dir.mkdir(parents=True, exist_ok=True)
        
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
        Execute a complete GHSpec workflow for one scenario step.
        
        IMPORTANT: GHSpec's internal 5-phase workflow is DIFFERENT from scenario steps:
        - **Scenario Step** (this method): User's business requirement (e.g., "Build Hello World API")
        - **GHSpec Internal Phases**: Framework's process to fulfill that requirement
        
        GHSpec Workflow (executes ALL phases in ONE scenario step):
        1. Phase 1 (Specify): Generate specification from command_text
        2. Phase 2 (Plan): Generate technical plan from spec
        3. Phase 3 (Tasks): Generate task breakdown from spec + plan
        4. Phase 4 (Implement): Generate code task-by-task
        5. Phase 5 (Bugfix): Optional error correction (stub for now)
        
        This matches how BAeS and ChatDev work - ONE execute_step() call generates
        a complete working system.
        
        Args:
            step_num: Scenario step number (e.g., 1 for "Build Hello World API")
            command_text: Natural language command (user's feature request)
            
        Returns:
            Dictionary with execution results including tokens and HITL count
        """
        self.current_step = step_num
        self._step_start_time = time.time()
        overall_start_timestamp = int(time.time())
        
        logger.info("Executing GHSpec complete workflow",
                   extra={'run_id': self.run_id, 'step': step_num, 
                         'event': 'step_start', 
                         'metadata': {'framework': 'ghspec', 'command': command_text[:100],
                                    'note': 'Running all 5 GHSpec internal phases'}})
        
        # Aggregate metrics across all phases
        total_hitl_count = 0
        total_tokens_in = 0
        total_tokens_out = 0
        total_api_calls = 0
        total_cached_tokens = 0
        
        try:
            # Phase 1: Generate specification
            logger.info("GHSpec Phase 1/5: Specify",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, tok_in, tok_out, calls, cached, start_ts, end_ts = self._execute_phase('specify', command_text)
            total_hitl_count += hitl
            total_tokens_in += tok_in
            total_tokens_out += tok_out
            total_api_calls += calls
            total_cached_tokens += cached
            
            if not self.spec_md_path.exists():
                raise RuntimeError("Failed to generate spec.md")
            
            # Phase 2: Generate technical plan
            logger.info("GHSpec Phase 2/5: Plan",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, tok_in, tok_out, calls, cached, start_ts, end_ts = self._execute_phase('plan', command_text)
            total_hitl_count += hitl
            total_tokens_in += tok_in
            total_tokens_out += tok_out
            total_api_calls += calls
            total_cached_tokens += cached
            
            if not self.plan_md_path.exists():
                raise RuntimeError("Failed to generate plan.md")
            
            # Phase 3: Generate task breakdown
            logger.info("GHSpec Phase 3/5: Tasks",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, tok_in, tok_out, calls, cached, start_ts, end_ts = self._execute_phase('tasks', command_text)
            total_hitl_count += hitl
            total_tokens_in += tok_in
            total_tokens_out += tok_out
            total_api_calls += calls
            total_cached_tokens += cached
            
            if not self.tasks_md_path.exists():
                raise RuntimeError("Failed to generate tasks.md")
            
            # Phase 4: Implement code task-by-task
            logger.info("GHSpec Phase 4/5: Implement",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, tok_in, tok_out, calls, cached, start_ts, end_ts = self._execute_task_implementation(command_text)
            total_hitl_count += hitl
            total_tokens_in += tok_in
            total_tokens_out += tok_out
            total_api_calls += calls
            total_cached_tokens += cached
            
            # Check if code was generated
            created_files = list(self.src_dir.rglob('*.py')) + list(self.src_dir.rglob('*.md'))
            if len(created_files) == 0:
                raise RuntimeError("No code files generated during implementation")
            
            # Phase 5: Bugfix cycle (stub - orchestrator handles validation)
            logger.info("GHSpec Phase 5/5: Bugfix (skipped - orchestrator handles)",
                       extra={'run_id': self.run_id, 'step': step_num})
            # Bugfix would go here, but orchestrator handles validation retry logic
            
            # Copy all artifacts to workspace root for validation
            self._copy_phase3_artifacts(step_num)  # Copy spec/plan/tasks
            self._copy_artifacts(step_num)         # Copy generated code
            
            success = True
            overall_end_timestamp = int(time.time())
            duration = time.time() - self._step_start_time
            
            logger.info("GHSpec complete workflow finished",
                       extra={'run_id': self.run_id, 'step': step_num,
                             'event': 'step_complete',
                             'metadata': {
                                 'success': True,
                                 'duration_seconds': duration,
                                 'total_hitl_count': total_hitl_count,
                                 'total_tokens_in': total_tokens_in,
                                 'total_tokens_out': total_tokens_out,
                                 'total_api_calls': total_api_calls,
                                 'total_cached_tokens': total_cached_tokens,
                                 'files_generated': len(created_files)
                             }})
            
            return {
                'success': True,
                'duration_seconds': duration,
                'hitl_count': total_hitl_count,
                'tokens_in': total_tokens_in,
                'tokens_out': total_tokens_out,
                'api_calls': total_api_calls,
                'cached_tokens': total_cached_tokens,
                'start_timestamp': overall_start_timestamp,
                'end_timestamp': overall_end_timestamp,
                'retry_count': 0
            }
                
        except Exception as e:
            # Store error for validation reporting
            self.last_execution_error = {
                'type': 'EXECUTION_EXCEPTION',
                'error': str(e),
                'exception_type': type(e).__name__
            }
            logger.error("GHSpec workflow execution failed",
                        extra={'run_id': self.run_id, 'step': step_num,
                              'metadata': {'error': str(e), 'exception_type': type(e).__name__}})
            # Re-raise to let orchestrator handle
            raise
    
    def _copy_artifacts(self, step_num: int) -> None:
        """
        Copy GHSpec's generated code from specs/001-baes-experiment/src/ to workspace root.
        
        This ensures validation can find the generated code in a standard location,
        aligning with BAeS and ChatDev patterns.
        
        Args:
            step_num: Step number that was executed
        """
        # Use DRY helper from BaseAdapter
        copied_count = self._copy_directory_contents(
            source_dir=self.src_dir,
            dest_dir=Path(self.workspace_path),
            step_num=step_num,
            recursive=True
        )
    
    def _copy_phase3_artifacts(self, step_num: int) -> None:
        """
        Copy GHSpec's Phase 3 artifacts (spec.md, plan.md, tasks.md) to workspace root.
        
        Phase 3 generates specification documents in specs/001-baes-experiment/:
        - spec.md: Feature specification
        - plan.md: Technical implementation plan
        - tasks.md: Breakdown of implementation tasks
        
        These files are copied to workspace root for:
        1. Consistent validation (same location as BAeS/ChatDev artifacts)
        2. Easy access for analysis and reporting
        3. Archive packaging (all artifacts in one place)
        
        Args:
            step_num: Step number that was executed (1, 2, or 3)
        """
        workspace_root = Path(self.workspace_path)
        
        # Map of artifacts to copy
        artifacts = {
            'spec.md': self.spec_md_path,
            'plan.md': self.plan_md_path,
            'tasks.md': self.tasks_md_path
        }
        
        copied_count = 0
        for filename, source_path in artifacts.items():
            if source_path.exists():
                dest_path = workspace_root / filename
                try:
                    dest_path.write_text(source_path.read_text(), encoding='utf-8')
                    copied_count += 1
                    logger.info(f"Copied Phase 3 artifact: {filename}",
                               extra={'run_id': self.run_id, 'step': step_num})
                except Exception as e:
                    logger.warning(f"Failed to copy {filename}: {e}",
                                  extra={'run_id': self.run_id, 'step': step_num})
        
        if copied_count > 0:
            logger.info(f"Copied {copied_count} Phase 3 artifacts to workspace root",
                       extra={'run_id': self.run_id, 'step': step_num})

    
    def _execute_phase(self, phase: str, command_text: str) -> Tuple[int, int, int, int, int]:
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
            Tuple of (hitl_count, tokens_in, tokens_out, start_timestamp, end_timestamp)
        """
        logger.info(f"Executing {phase} phase",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {'phase': phase}})
        
        # Load prompt template (resolve relative to project root)
        template_path = self.project_root / "docs" / "ghspec" / "prompts" / f"{phase}_template.md"
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
        tokens_in, tokens_out, api_calls, cached_tokens = self.fetch_usage_from_openai(
            api_key_env_var='OPEN_AI_KEY_ADM',  # Admin key for Usage API
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
                             'tokens_out': tokens_out,
                             'api_calls': api_calls,
                             'cached_tokens': cached_tokens
                         }})
        
        return hitl_count, tokens_in, tokens_out, api_calls, cached_tokens, api_call_start, api_call_end
    
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
        
        # Split by ## headers to isolate sections
        lines = content.split('\n')
        
        system_prompt = ""
        user_prompt_template = ""
        current_section = None
        in_code_block = False
        code_block_content = []
        
        for line in lines:
            # Detect section headers
            if line.strip().startswith('## System Prompt'):
                current_section = 'system'
                in_code_block = False
                code_block_content = []
            elif line.strip().startswith('## User Prompt Template'):
                current_section = 'user'
                in_code_block = False
                code_block_content = []
            elif line.strip().startswith('##') and line.strip() != '##':
                # Different section, stop capturing
                if current_section and in_code_block and code_block_content:
                    # Save what we captured
                    if current_section == 'system':
                        system_prompt = '\n'.join(code_block_content).strip()
                    elif current_section == 'user':
                        user_prompt_template = '\n'.join(code_block_content).strip()
                current_section = None
                in_code_block = False
                code_block_content = []
            elif current_section:
                # Handle code blocks
                if line.strip().startswith('```'):
                    if not in_code_block:
                        # Starting code block
                        in_code_block = True
                        code_block_content = []
                    else:
                        # Ending code block - save content
                        if current_section == 'system' and not system_prompt:
                            system_prompt = '\n'.join(code_block_content).strip()
                        elif current_section == 'user' and not user_prompt_template:
                            user_prompt_template = '\n'.join(code_block_content).strip()
                        in_code_block = False
                elif in_code_block:
                    code_block_content.append(line)
        
        # Handle case where file ends while in code block
        if in_code_block and code_block_content:
            if current_section == 'user' and not user_prompt_template:
                user_prompt_template = '\n'.join(code_block_content).strip()
        
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
    
    def _execute_task_implementation(self, command_text: str) -> Tuple[int, int, int, int, int]:
        """
        Execute task-by-task code generation (Phase 4).
        
        Workflow:
        1. Parse tasks.md into structured task list
        2. For each task:
           a. Build context-rich prompt (spec excerpt + plan excerpt + current file)
           b. Call OpenAI API
           c. Handle clarifications if needed
           d. Save generated code to file
        3. Aggregate token usage across all tasks
        
        Args:
            command_text: User's original feature request (for logging)
            
        Returns:
            Tuple of (total_hitl_count, total_tokens_in, total_tokens_out, 
                     overall_start_timestamp, overall_end_timestamp)
        """
        logger.info("Starting task-by-task implementation",
                   extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Parse tasks from tasks.md
        tasks = self._parse_tasks()
        
        logger.info(f"Found {len(tasks)} tasks to implement",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {'task_count': len(tasks)}})
        
        # Load spec and plan content once (for excerpting)
        spec_content = self.spec_md_path.read_text(encoding='utf-8')
        plan_content = self.plan_md_path.read_text(encoding='utf-8')
        
        # Load implement template (resolve relative to project root)
        template_path = self.project_root / "docs" / "ghspec" / "prompts" / "implement_template.md"
        system_prompt, user_prompt_template = self._load_prompt_template(template_path)
        
        total_hitl_count = 0
        total_tokens_in = 0
        total_tokens_out = 0
        total_api_calls = 0
        total_cached_tokens = 0
        
        # Track overall start time (before first task)
        overall_start_timestamp = int(time.time())
        
        # Process each task
        for i, task in enumerate(tasks, 1):
            logger.info(f"Processing task {i}/{len(tasks)}: {task['id']}",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'task_id': task['id'], 'file': task['file']}})
            
            # Build task-specific prompt
            user_prompt = self._build_task_prompt(
                task, spec_content, plan_content, user_prompt_template
            )
            
            # Track start time for Usage API
            api_call_start = int(time.time())
            
            # Call OpenAI API
            response_text = self._call_openai(system_prompt, user_prompt)
            
            # Check for clarification
            hitl_count = 0
            if self._needs_clarification(response_text):
                logger.info(f"Clarification needed for task {task['id']}",
                           extra={'run_id': self.run_id, 'step': self.current_step})
                
                clarification_text = self._handle_clarification(response_text)
                user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
                
                response_text = self._call_openai(system_prompt, user_prompt_with_hitl)
                hitl_count = 1
            
            # Save generated code
            self._save_code_file(task['file'], response_text)
            
            # Fetch token usage
            api_call_end = int(time.time())
            tokens_in, tokens_out, api_calls, cached_tokens = self.fetch_usage_from_openai(
                api_key_env_var='OPEN_AI_KEY_ADM',  # Admin key for Usage API
                start_timestamp=api_call_start,
                end_timestamp=api_call_end,
                model='gpt-4o-mini'
            )
            
            # Aggregate totals
            total_hitl_count += hitl_count
            total_tokens_in += tokens_in
            total_tokens_out += tokens_out
            total_api_calls += api_calls
            total_cached_tokens += cached_tokens
            
            logger.info(f"Task {task['id']} completed",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {
                                 'file': task['file'],
                                 'tokens_in': tokens_in,
                                 'tokens_out': tokens_out,
                                 'hitl': hitl_count
                             }})
        
        logger.info("Task implementation completed",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'tasks_completed': len(tasks),
                             'total_hitl': total_hitl_count,
                             'total_tokens_in': total_tokens_in,
                             'total_tokens_out': total_tokens_out,
                             'total_api_calls': total_api_calls,
                             'total_cached_tokens': total_cached_tokens
                         }})
        
        # Track overall end time (after last task)
        overall_end_timestamp = int(time.time())
        
        return total_hitl_count, total_tokens_in, total_tokens_out, total_api_calls, total_cached_tokens, overall_start_timestamp, overall_end_timestamp
    
    def _parse_tasks(self) -> list:
        """
        Parse tasks.md into structured task list using a robust two-pass approach.
        
        Strategy:
        1. First pass: Find all checkbox lines with task markers (- [ ] **Task...)
        2. Second pass: Extract file path from lines following each task marker
        
        Handles various AI-generated formats:
        - [ ] **TASK-001** Description
        - [ ] **Task 1**: Description  
        - [ ] **Task 1.1**: Description (nested)
        - [ ] Task 1: Description (no bold)
        
        File path formats supported:
        - **File**: /path/to/file.ext
        - **File Path**: /path/to/file.ext
        - - **File**: /path/to/file.ext (bullet point)
        
        Returns:
            List of task dictionaries with keys: id, description, file, goal
        """
        tasks_content = self.tasks_md_path.read_text(encoding='utf-8')
        tasks = []
        lines = tasks_content.split('\n')
        
        # Two-pass approach for robustness
        task_count = 0
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Pass 1: Detect checkbox task line
            # Pattern: - [ ] followed by some task indicator
            if line.startswith('- [ ]'):
                task_count += 1
                
                # Extract task description (everything after checkbox)
                # Remove checkbox and clean up
                desc_text = line[5:].strip()  # Remove '- [ ]'
                
                # Remove bold markers and extract core description
                # Handle: **Task N**: desc, **TASK-NNN** desc, Task N: desc
                desc_text = re.sub(r'\*\*Task \d+(\.\d+)?\*\*:?\s*', '', desc_text, flags=re.IGNORECASE)
                desc_text = re.sub(r'\*\*TASK-\d+\*\*:?\s*', '', desc_text, flags=re.IGNORECASE)
                desc_text = re.sub(r'Task \d+(\.\d+)?:?\s*', '', desc_text, flags=re.IGNORECASE)
                desc_text = desc_text.strip()
                
                # Pass 2: Look ahead for file path (within next 10 lines)
                file_path = None
                for j in range(i + 1, min(i + 11, len(lines))):
                    next_line = lines[j].strip()
                    
                    # Stop if we hit another task
                    if next_line.startswith('- [ ]'):
                        break
                    
                    # Look for file indicators
                    # Pattern: **File**: path or **File Path**: path or - **File**: path
                    file_match = re.search(
                        r'\*\*File(?:\s+Path)?\*\*:\s*`?([^\s`\n]+)',
                        next_line,
                        re.IGNORECASE
                    )
                    
                    if file_match:
                        file_path = file_match.group(1).strip()
                        break
                
                # Only add tasks with file paths
                if file_path and desc_text:
                    # Generate consistent task ID
                    task_id = f"TASK-{str(task_count).zfill(3)}"
                    
                    tasks.append({
                        'id': task_id,
                        'description': desc_text,
                        'file': file_path,
                        'goal': desc_text  # Use description as goal
                    })
            
            i += 1
        
        return tasks
    
    def _build_task_prompt(
        self, 
        task: dict, 
        spec_content: str, 
        plan_content: str,
        template: str
    ) -> str:
        """
        Build context-rich prompt for a specific task.
        
        Context includes:
        - Task details (id, description, goal, file)
        - Relevant spec excerpt (extracted via keywords)
        - Relevant plan excerpt (extracted via keywords)
        - Current file content (if file exists)
        
        Args:
            task: Task dictionary from _parse_tasks()
            spec_content: Full specification text
            plan_content: Full technical plan text
            template: User prompt template from implement_template.md
            
        Returns:
            Complete user prompt with all context filled in
        """
        # Extract relevant sections from spec and plan
        spec_excerpt = self._extract_relevant_section(spec_content, task)
        plan_excerpt = self._extract_relevant_section(plan_content, task)
        
        # Read current file content if it exists
        file_full_path = self.src_dir / task['file']
        current_file_content = self._read_file_if_exists(file_full_path)
        
        if not current_file_content:
            current_file_content = "# File does not exist yet - create from scratch"
        
        # Fill template with context
        prompt = (template
                 .replace('{task_description}', task['description'])
                 .replace('{file_path}', task['file'])
                 .replace('{task_goal}', task['goal'])
                 .replace('{spec_excerpt}', spec_excerpt)
                 .replace('{plan_excerpt}', plan_excerpt)
                 .replace('{current_file_content}', current_file_content))
        
        return prompt
    
    def _extract_relevant_section(self, full_content: str, task: dict) -> str:
        """
        Extract relevant excerpt from spec/plan for this specific task.
        
        Uses keyword matching to find sections related to:
        - File name/path keywords (e.g., "user", "auth", "model")
        - Task description keywords
        - Task goal keywords
        
        Strategy:
        1. Split document into sections (by ## headers)
        2. Score each section based on keyword matches
        3. Return top 2-3 sections concatenated
        4. Limit to ~500 words to manage context window
        
        Args:
            full_content: Complete spec.md or plan.md content
            task: Task dictionary with description, file, goal
            
        Returns:
            Relevant excerpt (truncated if needed)
        """
        # Extract keywords from task
        keywords = set()
        
        # From file path: "backend/models/user.py" → ["user", "model"]
        file_parts = task['file'].lower().replace('/', ' ').replace('.', ' ').split()
        keywords.update(file_parts)
        
        # From description and goal
        desc_words = task['description'].lower().split()
        goal_words = task['goal'].lower().split()
        keywords.update(w for w in desc_words if len(w) > 3)
        keywords.update(w for w in goal_words if len(w) > 3)
        
        # Split content into sections by headers
        sections = re.split(r'\n##+ ', full_content)
        
        # Score each section
        scored_sections = []
        for section in sections:
            section_lower = section.lower()
            score = sum(1 for keyword in keywords if keyword in section_lower)
            if score > 0:
                scored_sections.append((score, section))
        
        # Sort by score and take top 3
        scored_sections.sort(reverse=True, key=lambda x: x[0])
        top_sections = [s[1] for s in scored_sections[:3]]
        
        # Concatenate and truncate
        excerpt = '\n\n## '.join(top_sections)
        
        # Limit to ~2000 characters (~500 words)
        if len(excerpt) > 2000:
            excerpt = excerpt[:2000] + "\n\n[... excerpt truncated ...]"
        
        return excerpt if excerpt else "No relevant sections found - use general context"
    
    def _read_file_if_exists(self, file_path: Path) -> str:
        """
        Read file content if it exists in workspace.
        
        Args:
            file_path: Absolute path to file
            
        Returns:
            File content as string, or empty string if doesn't exist
        """
        if file_path.exists():
            try:
                return file_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}",
                             extra={'run_id': self.run_id, 'step': self.current_step})
                return ""
        return ""
    
    def _save_code_file(self, relative_path: str, content: str) -> None:
        """
        Save generated code to workspace file.
        
        Creates parent directories if needed.
        Handles both absolute paths and relative paths from src/.
        
        Args:
            relative_path: Path relative to src_dir (e.g., "backend/models/user.py")
                          Can start with / which will be stripped
            content: File content to write
        """
        # Strip leading / if present (AI often generates absolute paths)
        if relative_path.startswith('/'):
            relative_path = relative_path.lstrip('/')
        
        # Resolve path relative to src_dir
        file_path = self.src_dir / relative_path
        
        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        file_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Code file saved: {relative_path}",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'path': str(file_path),
                             'size_bytes': len(content.encode('utf-8'))
                         }})
    
    def attempt_bugfix_cycle(self, validation_errors: list) -> Tuple[int, int, int, int, int]:
        """
        Attempt to fix code based on validation failures.
        
        **Phase 5 Implementation**: Bounded bugfix cycle
        
        This method would be called by the experiment orchestrator after
        validation failures are detected. It implements a single-pass bugfix
        cycle to maintain reproducibility.
        
        Workflow:
        1. Derive bugfix tasks from validation errors (max 3)
        2. For each bugfix task:
           a. Build bugfix prompt with error + current file + spec context
           b. Call OpenAI API
           c. Save fixed code
        3. Return aggregated token usage
        
        **Important**: Bounded to 1 cycle to avoid infinite loops and ensure
        reproducibility. This matches ChatDev/BAEs iteration behavior.
        
        Args:
            validation_errors: List of error dictionaries with keys:
                - file: File path with error
                - error_type: 'compile', 'test_failure', 'runtime'
                - message: Error message/traceback
                - line_number: Optional line number
                
        Returns:
            Tuple of (hitl_count, tokens_in, tokens_out)
        """
        logger.info(f"Starting bugfix cycle for {len(validation_errors)} errors",
                   extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Derive bugfix tasks (max 3, prioritized by severity)
        bugfix_tasks = self._derive_bugfix_tasks(validation_errors)
        
        if not bugfix_tasks:
            logger.info("No bugfix tasks derived",
                       extra={'run_id': self.run_id, 'step': self.current_step})
            return 0, 0, 0, 0, 0
        
        # Load spec for context
        spec_content = self.spec_md_path.read_text(encoding='utf-8')
        
        # Load bugfix template (resolve relative to project root)
        template_path = self.project_root / "docs" / "ghspec" / "prompts" / "bugfix_template.md"
        system_prompt, user_prompt_template = self._load_prompt_template(template_path)
        
        total_hitl_count = 0
        total_tokens_in = 0
        total_tokens_out = 0
        total_api_calls = 0
        total_cached_tokens = 0
        
        # Process each bugfix task
        for i, task in enumerate(bugfix_tasks, 1):
            logger.info(f"Bugfix {i}/{len(bugfix_tasks)}: {task['file']}",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'error_type': task['error_type']}})
            
            # Build bugfix prompt
            user_prompt = self._build_bugfix_prompt(task, spec_content, user_prompt_template)
            
            # Track start time
            api_call_start = int(time.time())
            
            # Call OpenAI API
            response_text = self._call_openai(system_prompt, user_prompt)
            
            # Check for clarification (rare in bugfix, but possible)
            hitl_count = 0
            if self._needs_clarification(response_text):
                clarification_text = self._handle_clarification(response_text)
                user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
                response_text = self._call_openai(system_prompt, user_prompt_with_hitl)
                hitl_count = 1
            
            # Save fixed code
            self._save_code_file(task['file'], response_text)
            
            # Fetch token usage
            api_call_end = int(time.time())
            tokens_in, tokens_out, api_calls, cached_tokens = self.fetch_usage_from_openai(
                api_key_env_var='OPEN_AI_KEY_ADM',  # Admin key for Usage API
                start_timestamp=api_call_start,
                end_timestamp=api_call_end,
                model='gpt-4o-mini'
            )
            
            # Aggregate
            total_hitl_count += hitl_count
            total_tokens_in += tokens_in
            total_tokens_out += tokens_out
            total_api_calls += api_calls
            total_cached_tokens += cached_tokens
            
            logger.info(f"Bugfix {i} applied",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'file': task['file']}})
        
        logger.info(f"Bugfix cycle completed: {len(bugfix_tasks)} fixes applied",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'total_tokens_in': total_tokens_in,
                             'total_tokens_out': total_tokens_out,
                             'total_api_calls': total_api_calls,
                             'total_cached_tokens': total_cached_tokens
                         }})
        
        return total_hitl_count, total_tokens_in, total_tokens_out, total_api_calls, total_cached_tokens
    
    def _derive_bugfix_tasks(self, validation_errors: list) -> list:
        """
        Derive bugfix tasks from validation errors.
        
        Prioritizes errors by severity and limits to max 3 tasks to keep
        bugfix cycle manageable and deterministic.
        
        Priority order:
        1. Compilation errors (block execution)
        2. Test failures (functional issues)
        3. Runtime errors (edge cases)
        
        Args:
            validation_errors: List of error dictionaries
            
        Returns:
            List of bugfix task dictionaries (max 3)
        """
        # Sort by severity
        severity_order = {'compile': 0, 'test_failure': 1, 'runtime': 2}
        sorted_errors = sorted(
            validation_errors,
            key=lambda e: severity_order.get(e.get('error_type', 'runtime'), 99)
        )
        
        # Take top 3
        top_errors = sorted_errors[:3]
        
        # Convert to bugfix tasks
        bugfix_tasks = []
        for error in top_errors:
            task = {
                'file': error['file'],
                'error_type': error['error_type'],
                'error_message': error['message'],
                'line_number': error.get('line_number'),
                'original_task': error.get('original_task', 'Code generation')
            }
            bugfix_tasks.append(task)
        
        return bugfix_tasks
    
    def _build_bugfix_prompt(
        self,
        bugfix_task: dict,
        spec_content: str,
        template: str
    ) -> str:
        """
        Build bugfix prompt with error context.
        
        Args:
            bugfix_task: Bugfix task dictionary from _derive_bugfix_tasks()
            spec_content: Full specification content
            template: User prompt template from bugfix_template.md
            
        Returns:
            Complete user prompt for bugfix
        """
        # Read current file content
        file_path = self.src_dir / bugfix_task['file']
        current_content = self._read_file_if_exists(file_path)
        
        if not current_content:
            current_content = "# File not found or empty"
        
        # Extract relevant spec section (similar to task implementation)
        # Use file path and error message as keywords
        keywords = set(bugfix_task['file'].lower().replace('/', ' ').split())
        keywords.update(bugfix_task['error_message'].lower().split()[:10])  # First 10 words
        
        # Simple excerpt: find sections mentioning keywords
        spec_lines = spec_content.split('\n')
        relevant_lines = [
            line for line in spec_lines
            if any(keyword in line.lower() for keyword in keywords if len(keyword) > 3)
        ]
        spec_excerpt = '\n'.join(relevant_lines[:20])  # Max 20 lines
        
        if not spec_excerpt:
            spec_excerpt = "Refer to general specification requirements"
        
        # Fill template
        prompt = (template
                 .replace('{error_message}', bugfix_task['error_message'])
                 .replace('{file_path}', bugfix_task['file'])
                 .replace('{current_file_content}', current_content)
                 .replace('{spec_excerpt}', spec_excerpt)
                 .replace('{original_task_description}', bugfix_task['original_task']))
        
        return prompt
        
    def health_check(self) -> bool:
        """
        Check if GitHub Spec-kit framework is ready.
        
        GHSpec is CLI-based with no persistent services, so we just verify:
        - Framework directory exists
        - Workspace structure is set up
        
        Returns:
            True if healthy
            
        Raises:
            RuntimeError: If health check fails with details
        """
        if not self.framework_dir or not self.framework_dir.exists():
            raise RuntimeError(
                f"GHSpec framework directory not found or not initialized: {self.framework_dir}"
            )
        
        if not hasattr(self, 'specs_dir') or not self.specs_dir.exists():
            raise RuntimeError(
                f"GHSpec workspace structure not set up: specs_dir missing or not found"
            )
            
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
            
        Raises:
            RuntimeError: If HITL file is missing or empty
        """
        if self.hitl_text is None:
            # Load GHSpec-specific clarification guidelines
            hitl_path = Path("config/hitl/ghspec_clarification_guidelines.txt")
            if not hitl_path.exists():
                raise RuntimeError(
                    f"GHSpec HITL guidelines file not found: {hitl_path}. "
                    "This file is required for deterministic HITL responses."
                )
            
            with open(hitl_path, 'r', encoding='utf-8') as f:
                self.hitl_text = f.read().strip()
            
            if not self.hitl_text:
                raise RuntimeError(
                    f"GHSpec HITL guidelines file is empty: {hitl_path}. "
                    "File must contain clarification guidelines."
                )
                
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
    
    def validate_run_artifacts(self) -> tuple[bool, str]:
        """Validate that GHSpec generated expected artifacts based on completed phases.
        
        GHSpec is multi-phase:
        - Phase 3 (Steps 1-3): Generate spec.md, plan.md, tasks.md
        - Phase 4 (Steps 4-5): Generate Python code files
        
        Validation checks for artifacts appropriate to the completed phase.
        If only specification phases were run, validates spec/plan/tasks files.
        If implementation phases were run, validates Python code files.
        
        Returns:
            tuple[bool, str]: (success, error_message)
                - success: True if artifacts are valid, False otherwise
                - error_message: Empty string if success, descriptive error if failure
        """
        workspace_dir = Path(self.workspace_path)
        if not workspace_dir.exists():
            return False, (
                f"Workspace directory does not exist: {workspace_dir}. "
                "GHSpec framework failed to create workspace directory."
            )
        
        # Check what phase was completed by looking at generated files
        has_spec = self.spec_md_path.exists()
        has_plan = self.plan_md_path.exists()
        has_tasks = self.tasks_md_path.exists()
        python_files = list(workspace_dir.rglob("*.py"))
        has_code = len(python_files) > 0
        
        # Determine validation expectations based on artifacts present
        if has_code:
            # Phase 4 (implementation) completed - validate code artifacts
            logger.info("Validating Phase 4 artifacts (implementation)",
                       extra={'run_id': self.run_id,
                             'metadata': {'python_files': len(python_files)}})
            
            # Check for typical API entry point files
            api_files = ["api.py", "routes.py", "main.py", "app.py"]
            has_api_file = any((workspace_dir / f).exists() for f in api_files)
            if not has_api_file:
                logger.warning(
                    f"No typical API entry point file found in workspace directory: {workspace_dir}",
                    extra={'run_id': self.run_id}
                )
            
            # Success - log summary
            file_count = len(list(workspace_dir.rglob("*")))
            logger.info(
                f"Artifact validation passed: {len(python_files)} Python files, "
                f"{file_count} total files in workspace",
                extra={'run_id': self.run_id}
            )
            return True, ""
            
        elif has_spec or has_plan or has_tasks:
            # Phase 3 (specification) completed - validate spec/plan/tasks artifacts
            phase_files = []
            if has_spec:
                phase_files.append("spec.md")
            if has_plan:
                phase_files.append("plan.md")
            if has_tasks:
                phase_files.append("tasks.md")
            
            logger.info("Validating Phase 3 artifacts (specification)",
                       extra={'run_id': self.run_id,
                             'metadata': {'files': phase_files}})
            
            logger.info(
                f"Artifact validation passed: Phase 3 complete with {', '.join(phase_files)}",
                extra={'run_id': self.run_id}
            )
            return True, ""
            
        else:
            # No artifacts generated at all - this is a failure
            error_msg = self._format_validation_error(
                workspace_dir=workspace_dir,
                framework_name="GHSpec",
                last_execution_error=self.last_execution_error
            )
            return False, error_msg
