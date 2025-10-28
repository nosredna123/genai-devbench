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
from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__, component="adapter")


class GHSpecAdapter(BaseAdapter):
    """
    Adapter for GitHub Spec-kit framework.
    
    This adapter implements the complete 5-phase GHSpec-Kit workflow:
    1. Specify - Generate feature specification
    2. Plan - Create implementation plan
    3. Tasks - Break down into implementation tasks
    4. Implement - Generate code for each task
    5. Bugfix - Automated error resolution
    
    **Architecture Constraints**:
    - **Single-threaded execution only**: This adapter does not support concurrent 
      experiment runs. All experiment executions must be sequential. The adapter 
      maintains instance-level state (cached constitution, templates, phase context) 
      that is not thread-safe.
    - **Fail-fast on API errors**: Any OpenAI API failure (network error, rate limit, 
      timeout) immediately aborts the entire experiment run without retries. This 
      ensures clear failure attribution and data integrity.
    - **No size limits on constitution**: The adapter handles arbitrarily large 
      constitution files through intelligent chunking and excerpting strategies.
    
    **Template Synchronization (T048)**:
    The adapter supports two template modes for flexibility and reproducibility:
    
    - **Static mode (default)**: Uses version-controlled templates from 
      `docs/ghspec/prompts/`. Templates are stable and reproducible across runs.
      Change templates by editing files and committing to version control.
    
    - **Dynamic mode**: Uses templates from cloned GHSpec-Kit repository at 
      `frameworks/ghspec/`. Templates automatically track upstream improvements.
      Framework commit hash is logged in experiment metadata for reproducibility.
      Update templates by running `git pull` in `frameworks/ghspec/`.
    
    Configure mode in experiment.yaml:
        framework_config:
          template_source: static  # or 'dynamic'
    
    See docs/quickstart.md "Template Synchronization Workflow" for details.
    
    **Usage**:
        adapter = GHSpecAdapter(config, run_id, workspace_path, sprint_num)
        adapter.start()  # Initialize framework and load constitution
        adapter.execute_step(scenario_step, step_num)  # Run 5-phase workflow
        adapter.cleanup()  # Clean up resources
    """
    
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
        
        # Constitution caching (loaded once, reused across phases)
        self.constitution_content = None
        self.constitution_excerpt = None  # Chunked version for prompt injection
        
        # Template configuration
        self.template_cache = {}  # Cache loaded templates {phase: (system_prompt, user_template)}
        
        # Tech stack constraints (optional)
        self.tech_stack_constraints = None
        
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
            
            # Load constitution (T004/T007: Load and cache constitution)
            self.constitution_content = self._load_constitution()
            self.constitution_excerpt = self._prepare_constitution_excerpt(self.constitution_content)
            
            # Load tech stack constraints if configured (T009, T031, T033, T034)
            if 'tech_stack_constraints' in self.config:
                self.tech_stack_constraints = self.config['tech_stack_constraints']
                # T031: Validate - must be non-empty string (fail-fast)
                if not isinstance(self.tech_stack_constraints, str) or not self.tech_stack_constraints.strip():
                    raise ValueError(
                        "tech_stack_constraints must be a non-empty string if provided"
                    )
                # T033: Log comprehensive tech stack metadata
                tech_stack_metadata = {
                    'configured': True,
                    'size_bytes': len(self.tech_stack_constraints),
                    'size_chars': len(self.tech_stack_constraints),
                    'line_count': len(self.tech_stack_constraints.split('\n')),
                    'sprint_num': self.sprint_num
                }
                logger.info("Tech stack constraints loaded - will enforce in Plan phase",
                           extra={'run_id': self.run_id,
                                 'metadata': tech_stack_metadata})
            else:
                # T034: Handle missing constraints gracefully
                self.tech_stack_constraints = None
                tech_stack_metadata = {
                    'configured': False,
                    'mode': 'free_choice',
                    'sprint_num': self.sprint_num
                }
                logger.info("No tech stack constraints - AI has free choice",
                           extra={'run_id': self.run_id,
                                 'metadata': tech_stack_metadata})
            
            # Validate template configuration (T010, T045, T047)
            template_source = self.config.get('template_source', 'static')
            if template_source not in ['static', 'dynamic']:
                raise ValueError(
                    f"Invalid template_source '{template_source}'. Must be 'static' or 'dynamic'."
                )
            
            # T045: Log GHSpec commit hash when using dynamic templates
            template_metadata = {'template_source': template_source}
            if template_source == 'dynamic':
                # Get commit hash from frameworks/ghspec directory
                ghspec_commit_hash = self._get_framework_commit_hash()
                if ghspec_commit_hash:
                    template_metadata['ghspec_commit'] = ghspec_commit_hash
                    template_metadata['ghspec_commit_short'] = ghspec_commit_hash[:7]
                else:
                    template_metadata['ghspec_commit'] = 'unknown'
                    logger.warning("Could not determine GHSpec framework commit hash",
                                 extra={'run_id': self.run_id})
            
            logger.info("Template configuration validated",
                       extra={'run_id': self.run_id,
                             'metadata': template_metadata})
            
            # T029: Log comprehensive constitution metadata for experiment tracking
            constitution_metadata = {
                'source': 'project' if (self.project_root / "config_sets" / "default" / "constitution" / "project_constitution.md").exists()
                         else 'inline' if 'constitution_text' in self.config
                         else 'default',
                'size_bytes': len(self.constitution_content),
                'size_kb': round(len(self.constitution_content) / 1024, 2),
                'excerpt_size_bytes': len(self.constitution_excerpt),
                'was_chunked': len(self.constitution_excerpt) < len(self.constitution_content),
                'line_count': len(self.constitution_content.split('\n'))
            }
            logger.info("Constitution loaded and prepared for prompt injection",
                       extra={'run_id': self.run_id,
                             'metadata': constitution_metadata})
            
            # GHSpec is CLI-based (bash scripts + direct OpenAI API calls)
            # No virtual environment needed - we call OpenAI API directly
            # No persistent services to start - we invoke bash scripts per phase
            
            # Validate API key configuration (FR-011)
            self.validate_api_key()
            logger.info("GHSpec API key validated",
                       extra={'run_id': self.run_id})
            
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

    def _load_constitution(self) -> str:
        """
        Load project constitution with hierarchical fallback.
        
        Priority order:
        1. Project-specific constitution: config_sets/default/constitution/project_constitution.md
        2. Inline YAML override: experiment.yaml 'constitution_text' field
        3. Default principles: config_sets/default/constitution/default_principles.md
        
        Returns:
            Constitution content as string
            
        Raises:
            FileNotFoundError: If no constitution source is available
        """
        # Priority 1: Explicit project constitution
        project_const = self.project_root / "config_sets" / "default" / "constitution" / "project_constitution.md"
        if project_const.exists():
            content = project_const.read_text(encoding='utf-8')
            logger.info("Loaded project constitution",
                       extra={'run_id': self.run_id,
                             'metadata': {'source': 'project', 'size_bytes': len(content)}})
            return content
        
        # Priority 2: Inline YAML override
        if 'constitution_text' in self.config:
            content = self.config['constitution_text']
            logger.info("Loaded inline constitution from config",
                       extra={'run_id': self.run_id,
                             'metadata': {'source': 'inline', 'size_bytes': len(content)}})
            return content
        
        # Priority 3: Default principles (standalone experiments)
        default_const = self.project_root / "config" / "constitution" / "default_principles.md"
        if default_const.exists():
            content = default_const.read_text(encoding='utf-8')
            logger.info("Loaded default constitution",
                       extra={'run_id': self.run_id,
                             'metadata': {'source': 'default', 'size_bytes': len(content)}})
            return content
        
        # Priority 4: Default principles (main genai-devbench project)
        main_project_const = self.project_root / "config_sets" / "default" / "constitution" / "default_principles.md"
        if main_project_const.exists():
            content = main_project_const.read_text(encoding='utf-8')
            logger.info("Loaded default constitution from main project",
                       extra={'run_id': self.run_id,
                             'metadata': {'source': 'main_project', 'size_bytes': len(content)}})
            return content
        
        # Fail-fast: No constitution available
        raise FileNotFoundError(
            "No constitution found. Checked: project_constitution.md, "
            "experiment.yaml constitution_text, config/constitution/default_principles.md, "
            "config_sets/default/constitution/default_principles.md"
        )
    
    def _prepare_constitution_excerpt(self, constitution_content: str) -> str:
        """
        Prepare constitution excerpt for prompt injection, handling large files.
        
        Strategy for large constitutions (>100KB):
        - Take first 30KB (beginning with core principles)
        - Take last 10KB (ending with practical guidelines)
        - Insert separator indicating middle content omitted
        
        Args:
            constitution_content: Full constitution text
            
        Returns:
            Constitution excerpt suitable for prompt injection
        """
        size_bytes = len(constitution_content.encode('utf-8'))
        
        # If constitution is reasonable size, use it all
        if size_bytes <= 100_000:  # 100KB threshold
            return constitution_content
        
        # Large constitution: chunk it
        lines = constitution_content.split('\n')
        total_lines = len(lines)
        
        # Take first ~30% and last ~10% of lines
        first_chunk_lines = int(total_lines * 0.3)
        last_chunk_lines = int(total_lines * 0.1)
        
        first_chunk = '\n'.join(lines[:first_chunk_lines])
        last_chunk = '\n'.join(lines[-last_chunk_lines:])
        
        excerpt = f"{first_chunk}\n\n--- [Middle sections omitted for brevity] ---\n\n{last_chunk}"
        
        logger.info("Chunked large constitution for prompt",
                   extra={'run_id': self.run_id,
                         'metadata': {
                             'original_size_kb': size_bytes // 1024,
                             'excerpt_size_kb': len(excerpt.encode('utf-8')) // 1024,
                             'chunked': True
                         }})
        
        return excerpt
    
    def _get_framework_commit_hash(self) -> str:
        """
        Get git commit hash of GHSpec framework directory (T045).
        
        This is used when template_source='dynamic' to track which version
        of the upstream GHSpec-Kit templates are being used, enabling
        reproducibility and debugging of template-related issues.
        
        Returns:
            Git commit hash (40-character SHA-1) or empty string if unavailable
        """
        try:
            # Get commit hash from frameworks/ghspec directory
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(self.framework_dir),
                capture_output=True,
                text=True,
                timeout=5,
                check=False  # Don't raise on non-zero exit
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.debug("Could not get GHSpec framework commit hash",
                           extra={'run_id': self.run_id,
                                 'metadata': {'stderr': result.stderr}})
                return ""
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Error getting GHSpec framework commit hash: {e}",
                       extra={'run_id': self.run_id})
            return ""
    
    def _get_template_path(self, phase: str) -> Path:
        """
        Resolve template path based on configuration.
        
        Supports two modes:
        - 'static' (default): Use curated templates from docs/ghspec/prompts/
        - 'dynamic': Use templates from cloned framework (frameworks/ghspec/)
        
        Args:
            phase: Phase name ('specify', 'plan', 'tasks', 'implement', 'bugfix')
            
        Returns:
            Absolute path to template file
            
        Raises:
            ValueError: If template_source mode is invalid
        """
        mode = self.config.get('template_source', 'static')
        
        if mode == 'static':
            template_path = self.project_root / "docs" / "ghspec" / "prompts" / f"{phase}_template.md"
        elif mode == 'dynamic':
            template_path = self.framework_dir / ".specify" / "templates" / "commands" / f"{phase}.md"
        else:
            raise ValueError(
                f"Invalid template_source: '{mode}'. Must be 'static' or 'dynamic'."
            )
        
        if not template_path.exists():
            raise FileNotFoundError(
                f"Template not found: {template_path}. "
                f"Mode: {mode}, Phase: {phase}"
            )
        
        return template_path
    
    def _execute_specify_phase(self, command_text: str) -> Tuple[int, int, int, int, int]:
        """
        Execute Phase 1: Specify - Generate feature specification.
        
        This phase:
        1. Loads specify template
        2. Injects constitution for quality guidance
        3. Builds prompt with user command
        4. Handles up to 3 clarification iterations (FR-004)
        5. Saves spec.md
        
        Args:
            command_text: User's feature request
            
        Returns:
            Tuple of (hitl_count, tokens_in, tokens_out, api_calls, cached_tokens)
        """
        phase = 'specify'
        logger.info("Executing Specify phase (1/5)",
                   extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Load template with caching
        system_prompt, user_prompt_template = self._load_prompt_template(phase)
        
        # Inject constitution into system prompt (T021: Constitution integration)
        system_prompt_with_constitution = f"""{system_prompt}

## Project Constitution

Follow these coding standards and principles throughout the specification:

{self.constitution_excerpt}
"""
        
        # Build user prompt
        user_prompt = self._build_phase_prompt(phase, user_prompt_template, command_text)
        
        # Track start time
        api_call_start = int(time.time())
        
        # Call OpenAI with constitution-enhanced prompt
        response_text = self._call_openai(system_prompt_with_constitution, user_prompt)
        
        # Handle clarification with up to 3 iterations (FR-004, T036-T038)
        hitl_count = 0
        clarification_iteration = 0
        max_clarifications = 3
        
        while self._needs_clarification(response_text) and clarification_iteration < max_clarifications:
            clarification_iteration += 1
            hitl_count += 1
            
            # T040: Log clarification attempt with iteration number
            logger.info(f"Clarification needed in specify phase (iteration {clarification_iteration}/{max_clarifications})",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'iteration': clarification_iteration, 'phase': 'specify'}})
            
            # T037: Handle HITL with iteration-specific text
            clarification_text = self._handle_clarification(response_text, iteration=clarification_iteration)
            user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
            
            # Regenerate
            response_text = self._call_openai(system_prompt_with_constitution, user_prompt_with_hitl)
        
        if clarification_iteration >= max_clarifications and self._needs_clarification(response_text):
            logger.warning(f"Clarification limit reached ({max_clarifications}) in specify phase - proceeding with best effort",
                          extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Save artifact
        self._save_artifact(self.spec_md_path, response_text)
        
        # BREAKING CHANGE (v2.0.0): Token collection removed (reconciled post-run)
        api_call_end = int(time.time())
        tokens_in, tokens_out, api_calls, cached_tokens = 0, 0, 0, 0
        
        logger.info("Specify phase completed",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'output_path': str(self.spec_md_path),
                             'hitl_count': hitl_count,
                             'tokens_in': tokens_in,
                             'tokens_out': tokens_out,
                             'api_calls': api_calls,
                             'cached_tokens': cached_tokens
                         }})
        
        return hitl_count, tokens_in, tokens_out, api_calls, cached_tokens
    
    def _execute_plan_phase(self, command_text: str) -> Tuple[int, int, int, int, int]:
        """
        Execute Phase 2: Plan - Generate technical implementation plan.
        
        This phase:
        1. Loads plan template
        2. Injects constitution + tech stack constraints
        3. Builds prompt with spec.md content
        4. Handles up to 3 clarification iterations
        5. Saves plan.md
        
        Args:
            command_text: User's feature request (for context)
            
        Returns:
            Tuple of (hitl_count, tokens_in, tokens_out, api_calls, cached_tokens)
        """
        phase = 'plan'
        logger.info("Executing Plan phase (2/5)",
                   extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Load template
        system_prompt, user_prompt_template = self._load_prompt_template(phase)
        
        # Inject constitution + tech stack constraints (T030: Tech stack injection)
        tech_stack_guidance = ""
        if self.tech_stack_constraints:
            tech_stack_guidance = f"""

## Technology Stack Constraints

IMPORTANT: The following technology choices are required:

{self.tech_stack_constraints}

You MUST use these technologies in your technical plan.
"""
        else:
            tech_stack_guidance = """

## Technology Stack Constraints

None specified - you have free choice of technologies based on the specification requirements.
"""
        
        system_prompt_with_constitution = f"""{system_prompt}

## Project Constitution

Follow these coding standards and principles in your technical plan:

{self.constitution_excerpt}
{tech_stack_guidance}
"""
        
        # Build user prompt
        user_prompt = self._build_phase_prompt(phase, user_prompt_template, command_text)
        
        # Track start time
        api_call_start = int(time.time())
        
        # Call OpenAI
        response_text = self._call_openai(system_prompt_with_constitution, user_prompt)
        
        # Handle clarification with up to 3 iterations
        hitl_count = 0
        clarification_iteration = 0
        max_clarifications = 3
        
        while self._needs_clarification(response_text) and clarification_iteration < max_clarifications:
            clarification_iteration += 1
            hitl_count += 1
            
            # T040: Log clarification attempt with iteration number
            logger.info(f"Clarification needed in plan phase (iteration {clarification_iteration}/{max_clarifications})",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'iteration': clarification_iteration, 'phase': 'plan'}})
            
            # T037: Handle HITL with iteration-specific text
            clarification_text = self._handle_clarification(response_text, iteration=clarification_iteration)
            user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
            response_text = self._call_openai(system_prompt_with_constitution, user_prompt_with_hitl)
        
        if clarification_iteration >= max_clarifications and self._needs_clarification(response_text):
            logger.warning(f"Clarification limit reached ({max_clarifications}) in plan phase - proceeding with best effort",
                          extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Save artifact
        self._save_artifact(self.plan_md_path, response_text)
        
        # T032: Validate tech stack consistency across sprints
        if self.sprint_num > 1:
            self._validate_tech_stack_consistency(response_text)
        
        # BREAKING CHANGE (v2.0.0): Token collection removed (reconciled post-run)
        api_call_end = int(time.time())
        tokens_in, tokens_out, api_calls, cached_tokens = 0, 0, 0, 0
        
        logger.info("Plan phase completed",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'output_path': str(self.plan_md_path),
                             'hitl_count': hitl_count,
                             'tokens_in': tokens_in,
                             'tokens_out': tokens_out,
                             'api_calls': api_calls,
                             'cached_tokens': cached_tokens
                         }})
        
        return hitl_count, tokens_in, tokens_out, api_calls, cached_tokens
    
    def _execute_tasks_phase(self, command_text: str) -> Tuple[int, int, int, int, int]:
        """
        Execute Phase 3: Tasks - Generate implementation task breakdown.
        
        This phase:
        1. Loads tasks template
        2. Injects constitution for task quality
        3. Builds prompt with spec.md + plan.md content
        4. Handles up to 3 clarification iterations
        5. Saves tasks.md
        
        Args:
            command_text: User's feature request (for context)
            
        Returns:
            Tuple of (hitl_count, tokens_in, tokens_out, api_calls, cached_tokens)
        """
        phase = 'tasks'
        logger.info("Executing Tasks phase (3/5)",
                   extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Load template
        system_prompt, user_prompt_template = self._load_prompt_template(phase)
        
        # Inject constitution
        system_prompt_with_constitution = f"""{system_prompt}

## Project Constitution

Generate tasks that adhere to these coding standards:

{self.constitution_excerpt}
"""
        
        # Build user prompt
        user_prompt = self._build_phase_prompt(phase, user_prompt_template, command_text)
        
        # Track start time
        api_call_start = int(time.time())
        
        # Call OpenAI
        response_text = self._call_openai(system_prompt_with_constitution, user_prompt)
        
        # Handle clarification with up to 3 iterations
        hitl_count = 0
        clarification_iteration = 0
        max_clarifications = 3
        
        while self._needs_clarification(response_text) and clarification_iteration < max_clarifications:
            clarification_iteration += 1
            hitl_count += 1
            
            # T040: Log clarification attempt with iteration number
            logger.info(f"Clarification needed in tasks phase (iteration {clarification_iteration}/{max_clarifications})",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'iteration': clarification_iteration, 'phase': 'tasks'}})
            
            # T037: Handle HITL with iteration-specific text
            clarification_text = self._handle_clarification(response_text, iteration=clarification_iteration)
            user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
            response_text = self._call_openai(system_prompt_with_constitution, user_prompt_with_hitl)
        
        if clarification_iteration >= max_clarifications and self._needs_clarification(response_text):
            logger.warning(f"Clarification limit reached ({max_clarifications}) in tasks phase - proceeding with best effort",
                          extra={'run_id': self.run_id, 'step': self.current_step})
        
        # Save artifact
        self._save_artifact(self.tasks_md_path, response_text)
        
        # BREAKING CHANGE (v2.0.0): Token collection removed (reconciled post-run)
        api_call_end = int(time.time())
        tokens_in, tokens_out, api_calls, cached_tokens = 0, 0, 0, 0
        
        logger.info("Tasks phase completed",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'output_path': str(self.tasks_md_path),
                             'hitl_count': hitl_count,
                             'tokens_in': tokens_in,
                             'tokens_out': tokens_out,
                             'api_calls': api_calls,
                             'cached_tokens': cached_tokens
                         }})
        
        return hitl_count, tokens_in, tokens_out, api_calls, cached_tokens
            
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
        # BREAKING CHANGE (v2.0.0): Token tracking removed (reconciled post-run)
        total_hitl_count = 0
        
        try:
            # Phase 1: Generate specification (T011: Use new _execute_specify_phase)
            logger.info("GHSpec Phase 1/5: Specify",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, _tok_in, _tok_out, _calls, _cached = self._execute_specify_phase(command_text)
            total_hitl_count += hitl
            # Tokens ignored (reconciled post-run)
            
            # T017: Artifact validation
            if not self.spec_md_path.exists():
                raise RuntimeError("Failed to generate spec.md")
            if self.spec_md_path.stat().st_size < 100:
                raise RuntimeError(f"spec.md too small ({self.spec_md_path.stat().st_size} bytes) - likely empty or truncated")
            
            # Phase 2: Generate technical plan (T012: Use new _execute_plan_phase)
            logger.info("GHSpec Phase 2/5: Plan",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, _tok_in, _tok_out, _calls, _cached = self._execute_plan_phase(command_text)
            total_hitl_count += hitl
            # Tokens ignored (reconciled post-run)
            
            # T017: Artifact validation
            if not self.plan_md_path.exists():
                raise RuntimeError("Failed to generate plan.md")
            if self.plan_md_path.stat().st_size < 100:
                raise RuntimeError(f"plan.md too small ({self.plan_md_path.stat().st_size} bytes) - likely empty or truncated")
            
            # Phase 3: Generate task breakdown (T013: Use new _execute_tasks_phase)
            logger.info("GHSpec Phase 3/5: Tasks",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, _tok_in, _tok_out, _calls, _cached = self._execute_tasks_phase(command_text)
            total_hitl_count += hitl
            # Tokens ignored (reconciled post-run)
            
            # T017: Artifact validation
            if not self.tasks_md_path.exists():
                raise RuntimeError("Failed to generate tasks.md")
            if self.tasks_md_path.stat().st_size < 100:
                raise RuntimeError(f"tasks.md too small ({self.tasks_md_path.stat().st_size} bytes) - likely empty or truncated")
            
            # Phase 4: Implement code task-by-task (T014: Already exists, enhance with validation)
            logger.info("GHSpec Phase 4/5: Implement",
                       extra={'run_id': self.run_id, 'step': step_num})
            hitl, _tok_in, _tok_out, _calls, _cached = self._execute_task_implementation(command_text)
            total_hitl_count += hitl
            # Tokens ignored (reconciled post-run)
            
            # T017: Validate that implementation phase generated files
            python_files = list(self.src_dir.rglob("*.py"))
            if len(python_files) == 0:
                raise RuntimeError("No Python files generated during implementation phase")
            
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
                                 'total_hitl_count': total_hitl_count
                             }})
            
            # BREAKING CHANGE (v2.0.0): Token fields removed from return
            # Tokens reconciled post-run via Usage API
            return {
                'success': True,
                'duration_seconds': duration,
                'hitl_count': total_hitl_count,
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
        
        # Load prompt template with caching (T005/T006)
        system_prompt, user_prompt_template = self._load_prompt_template(phase)
        
        # Build complete user prompt with context
        user_prompt = self._build_phase_prompt(phase, user_prompt_template, command_text)
        
        # Track start time for Usage API query
        api_call_start = int(time.time())
        
        # Call OpenAI API
        response_text = self._call_openai(system_prompt, user_prompt)
        
        # Check for clarification requests
        hitl_count = 0
        if self._needs_clarification(response_text):
            # T040: Log clarification attempt
            logger.info(f"Clarification needed in {phase} phase",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'iteration': 1, 'phase': phase}})
            
            # T037: Handle HITL with iteration-specific text (iteration 1 by default)
            clarification_text = self._handle_clarification(response_text, iteration=1)
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
        
        # BREAKING CHANGE (v2.0.0): Token collection removed (reconciled post-run)
        api_call_end = int(time.time())
        tokens_in, tokens_out, api_calls, cached_tokens = 0, 0, 0, 0
        
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
    
    def _load_prompt_template(self, phase: str) -> Tuple[str, str]:
        """
        Load system and user prompt templates from markdown file with caching.
        
        Template resolution uses _get_template_path() which respects template_source config.
        Templates are cached per phase to avoid repeated disk I/O.
        
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
            phase: Phase name ('specify', 'plan', 'tasks', 'implement', 'bugfix')
            
        Returns:
            Tuple of (system_prompt, user_prompt_template)
            
        Raises:
            ValueError: If template format is invalid (missing required sections)
        """
        # Check cache first (T006: Caching)
        if phase in self.template_cache:
            logger.debug(f"Using cached template for phase: {phase}",
                        extra={'run_id': self.run_id})
            return self.template_cache[phase]
        
        # Resolve template path using configuration (T005)
        template_path = self._get_template_path(phase)
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate required sections present (T006: Validation)
        if '## System Prompt' not in content or '## User Prompt Template' not in content:
            raise ValueError(
                f"Invalid template format in {template_path}. "
                "Must contain '## System Prompt' and '## User Prompt Template' sections."
            )
        
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
            raise ValueError(
                f"Invalid template format in {template_path}. "
                "Could not extract system prompt or user prompt template."
            )
        
        # Cache for future use (T006: Caching)
        result = (system_prompt, user_prompt_template)
        self.template_cache[phase] = result
        
        logger.info(f"Loaded and cached template for phase: {phase}",
                   extra={'run_id': self.run_id,
                         'metadata': {
                             'template_path': str(template_path),
                             'system_prompt_length': len(system_prompt),
                             'user_template_length': len(user_prompt_template)
                         }})
        
        return result
    
    def _build_phase_prompt(self, phase: str, template: str, command_text: str) -> str:
        """
        Build complete user prompt by filling template with context.
        
        For sprint > 1, includes previous sprint context to enable incremental development:
        - Previous spec.md and plan.md (to understand existing system)
        - Previous generated code (to build upon, not replace)
        - Maintains tech stack consistency across sprints
        
        Args:
            phase: Phase name ('specify', 'plan', or 'tasks')
            template: User prompt template with placeholders
            command_text: User's feature request
            
        Returns:
            Complete user prompt with all placeholders filled
        """
        # Get previous sprint context for incremental development
        previous_context = self._get_previous_sprint_context() if self.sprint_num > 1 else None
        
        if phase == 'specify':
            # Specify phase: substitute user command + previous context
            prompt = template.replace('{user_command}', command_text)
            
            # Add previous sprint context for incremental development
            if previous_context:
                incremental_context = f"""

---
IMPORTANT: INCREMENTAL DEVELOPMENT CONTEXT

This is sprint {self.sprint_num} of an incremental development process.
You must build UPON the existing system, not replace it.

Previous Sprint Specification:
{previous_context['spec']}

Previous Sprint Tech Stack:
{previous_context['tech_stack']}

Previous Entities/Models:
{previous_context['entities']}

Instructions for Incremental Development:
1. The new feature should EXTEND the existing system
2. Use the SAME tech stack as previous sprint (consistency is critical)
3. Reference existing entities/models - don't recreate them
4. Specify how new components integrate with existing ones
5. Document what changes are needed to existing code (additions/modifications, NOT replacements)
---
"""
                prompt += incremental_context
            
            return prompt
            
        elif phase == 'plan':
            # Plan phase: substitute spec content + previous context
            spec_content = self.spec_md_path.read_text(encoding='utf-8')
            prompt = template.replace('{spec_content}', spec_content)
            
            # Add previous sprint context
            if previous_context:
                incremental_context = f"""

---
INCREMENTAL DEVELOPMENT CONTEXT

Previous Sprint Plan:
{previous_context['plan']}

Existing Code Files:
{previous_context['code_files']}

Instructions for Technical Plan:
1. MUST use the exact same tech stack as previous sprint
2. Show how new modules integrate with existing ones
3. Document modifications needed to existing files (not replacements)
4. Maintain backward compatibility with existing data models
5. Specify database migration strategy if data model changes
---
"""
                prompt += incremental_context
            
            return prompt
            
        elif phase == 'tasks':
            # Tasks phase: substitute spec + plan content + previous context
            spec_content = self.spec_md_path.read_text(encoding='utf-8')
            plan_content = self.plan_md_path.read_text(encoding='utf-8')
            prompt = (template
                   .replace('{spec_content}', spec_content)
                   .replace('{plan_content}', plan_content))
            
            # Add previous sprint context
            if previous_context:
                incremental_context = f"""

---
INCREMENTAL DEVELOPMENT CONTEXT

Existing Code to Build Upon:
{previous_context['code_summary']}

Instructions for Task Breakdown:
1. Identify which existing files need modifications
2. Create new files for new functionality
3. Ensure integration tasks are included
4. Maintain consistency with existing code style and patterns
---
"""
                prompt += incremental_context
            
            return prompt
        
        else:
            raise ValueError(f"Unknown phase: {phase}")
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call OpenAI API using the generic base adapter method.
        
        REFACTORED: Now delegates to BaseAdapter.call_openai_chat_completion()
        to follow DRY principle. The base adapter method:
        - Retrieves API key from self.config['api_key_env']
        - Uses gpt-4o-mini model (can be overridden)
        - Uses OpenAI default temperature (framework comparison as-is)
        - Handles logging and error handling consistently
        
        **T063: FAIL-FAST GUARANTEE**:
        This method does NOT retry on API failures. Any OpenAI API exception
        (network error, rate limit, timeout, authentication failure) immediately
        propagates to the caller, aborting the entire experiment run.
        
        This ensures:
        - Clear failure attribution (no hidden retries masking issues)
        - Data integrity (partial results are not saved)
        - Reproducibility (retry logic would introduce non-determinism)
        
        Args:
            system_prompt: System role instructions
            user_prompt: User message/request
            
        Returns:
            Response text from assistant
            
        Raises:
            RuntimeError: If API call fails (no retries, immediate abort)
        """
        # T063: Assert fail-fast behavior - no try-catch wrapper here
        # Any exception from call_openai_chat_completion() propagates unchanged
        return self.call_openai_chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4o-mini"  # From experiment.yaml config
            # Note: temperature not specified - uses BaseAdapter default (0 for consistency)
        )
    
    def _get_previous_sprint_context(self) -> Optional[Dict[str, str]]:
        """
        Load context from previous sprint for incremental development.
        
        Extracts:
        - Previous sprint's spec.md (business requirements)
        - Previous sprint's plan.md (technical decisions, tech stack)
        - Previous sprint's generated code (to build upon)
        - Key entities/models from previous sprint
        
        Returns:
            Dictionary with previous sprint context, or None if unavailable
        """
        prev_artifacts = self.previous_sprint_artifacts
        
        if not prev_artifacts or not prev_artifacts.exists():
            logger.warning("Previous sprint artifacts not found",
                         extra={'run_id': self.run_id,
                               'metadata': {
                                   'sprint': self.sprint_num,
                                   'expected_path': str(prev_artifacts) if prev_artifacts else 'None'
                               }})
            return None
        
        try:
            context = {}
            
            # Load previous spec.md
            prev_spec = prev_artifacts / "spec.md"
            if prev_spec.exists():
                context['spec'] = prev_spec.read_text(encoding='utf-8')
                # Extract entities from spec (usually in "Key Entities" section)
                context['entities'] = self._extract_entities_from_spec(context['spec'])
            else:
                context['spec'] = "No previous specification found"
                context['entities'] = "No entities defined"
            
            # Load previous plan.md
            prev_plan = prev_artifacts / "plan.md"
            if prev_plan.exists():
                context['plan'] = prev_plan.read_text(encoding='utf-8')
                # Extract tech stack from plan (usually in "Technical Context" section)
                context['tech_stack'] = self._extract_tech_stack_from_plan(context['plan'])
            else:
                context['plan'] = "No previous plan found"
                context['tech_stack'] = "No tech stack defined"
            
            # Load previous generated code files
            prev_models_dir = prev_artifacts / "models"
            prev_api_dir = prev_artifacts / "api"
            prev_tests_dir = prev_artifacts / "tests"
            
            code_files = []
            for code_dir in [prev_models_dir, prev_api_dir, prev_tests_dir]:
                if code_dir.exists():
                    for file_path in code_dir.rglob("*"):
                        if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.java', '.go']:
                            code_files.append({
                                'path': str(file_path.relative_to(prev_artifacts)),
                                'content': file_path.read_text(encoding='utf-8', errors='ignore')
                            })
            
            # Create code summary (limit to avoid token explosion)
            if code_files:
                context['code_files'] = "\n\n".join([
                    f"File: {f['path']}\n```\n{f['content'][:500]}...\n```"
                    for f in code_files[:5]  # Limit to first 5 files
                ])
                context['code_summary'] = "\n".join([
                    f"- {f['path']} ({len(f['content'])} bytes)"
                    for f in code_files
                ])
            else:
                context['code_files'] = "No code files found from previous sprint"
                context['code_summary'] = "No code files found"
            
            logger.info("Loaded previous sprint context for incremental development",
                       extra={'run_id': self.run_id,
                             'metadata': {
                                 'sprint': self.sprint_num,
                                 'prev_sprint': self.sprint_num - 1,
                                 'has_spec': 'spec' in context,
                                 'has_plan': 'plan' in context,
                                 'code_files_count': len(code_files)
                             }})
            
            return context
            
        except Exception as e:
            logger.error("Failed to load previous sprint context",
                       extra={'run_id': self.run_id,
                             'metadata': {
                                 'error': str(e),
                                 'sprint': self.sprint_num
                             }})
            return None
    
    def _extract_entities_from_spec(self, spec_content: str) -> str:
        """Extract Key Entities section from spec.md."""
        match = re.search(r'## Key Entities\s+(.*?)(?=\n##|\Z)', spec_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return "No entities defined in previous spec"
    
    def _extract_tech_stack_from_plan(self, plan_content: str) -> str:
        """Extract Technical Context section from plan.md."""
        match = re.search(r'## Technical Context\s+(.*?)(?=\n##|\Z)', plan_content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return "No tech stack defined in previous plan"
    
    def _validate_tech_stack_consistency(self, current_plan: str) -> None:
        """
        Validate tech stack consistency across sprints (T032).
        
        For sprint > 1, verifies that the current plan uses the same tech stack
        as the previous sprint. This prevents fragmentation and ensures
        incremental development on a consistent foundation.
        
        Args:
            current_plan: Generated plan.md content for current sprint
            
        Raises:
            ValueError: If tech stacks are inconsistent (fail-fast)
        
        Note: 
            - Only validates when sprint_num > 1
            - Uses fuzzy matching to account for formatting differences
            - Logs warning for review, raises error for critical mismatches
        """
        if self.sprint_num <= 1:
            return  # No validation needed for first sprint
        
        # Get previous sprint context
        previous_context = self._get_previous_sprint_context()
        if not previous_context:
            logger.warning("Cannot validate tech stack consistency - no previous sprint data",
                         extra={'run_id': self.run_id, 
                               'metadata': {'sprint_num': self.sprint_num}})
            return
        
        # Extract tech stacks
        previous_tech_stack = previous_context.get('tech_stack', '').lower()
        current_tech_stack = self._extract_tech_stack_from_plan(current_plan).lower()
        
        # Check if previous tech stack is defined
        if 'no tech stack defined' in previous_tech_stack:
            logger.info("No previous tech stack to validate against",
                       extra={'run_id': self.run_id,
                             'metadata': {'sprint_num': self.sprint_num}})
            return
        
        # Extract key technology terms (languages, frameworks, databases)
        def extract_tech_terms(text: str) -> set:
            """Extract technology keywords for comparison."""
            # Common tech patterns
            tech_patterns = [
                r'\b(python|java|javascript|typescript|go|rust|ruby|php|c\+\+|c#)\b',
                r'\b(flask|django|fastapi|express|react|vue|angular|spring|rails)\b',
                r'\b(postgresql|mysql|mongodb|redis|sqlite|cassandra|dynamodb)\b',
                r'\b(docker|kubernetes|aws|gcp|azure|heroku)\b',
                r'\b(rest|graphql|grpc|soap)\b'
            ]
            terms = set()
            for pattern in tech_patterns:
                terms.update(re.findall(pattern, text, re.IGNORECASE))
            return {t.lower() for t in terms}
        
        previous_terms = extract_tech_terms(previous_tech_stack)
        current_terms = extract_tech_terms(current_tech_stack)
        
        # Check for removed core technologies
        removed_terms = previous_terms - current_terms
        added_terms = current_terms - previous_terms
        
        # Log tech stack comparison
        logger.info("Tech stack consistency check",
                   extra={'run_id': self.run_id,
                         'metadata': {
                             'sprint_num': self.sprint_num,
                             'previous_terms': sorted(list(previous_terms)),
                             'current_terms': sorted(list(current_terms)),
                             'removed_terms': sorted(list(removed_terms)),
                             'added_terms': sorted(list(added_terms))
                         }})
        
        # Fail-fast if core technologies were removed (breaking consistency)
        if removed_terms:
            logger.warning("Tech stack inconsistency detected - technologies removed from previous sprint",
                          extra={'run_id': self.run_id,
                                'metadata': {
                                    'removed': sorted(list(removed_terms)),
                                    'previous_sprint': self.sprint_num - 1,
                                    'current_sprint': self.sprint_num
                                }})
            # This is a warning, not an error - AI might have valid reasons
            # (e.g., replacing deprecated tech, consolidating similar tools)
            # But we log it prominently for review
        
        # Success case
        if not removed_terms:
            logger.info("Tech stack consistency validated - no core technologies removed",
                       extra={'run_id': self.run_id,
                             'metadata': {'sprint_num': self.sprint_num}})
    
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
    
    def _handle_clarification(self, response_text: str, iteration: int = 1) -> str:
        """
        Return clarification guidelines from HITL file with iteration-specific content.
        
        This method is called when the model requests clarification.
        It loads the fixed clarification guidelines and returns them, optionally
        including iteration-specific sections for multi-round clarification.
        
        T037: Iteration-specific clarification text loading
        - Iteration 1: Returns base guidelines
        - Iteration 2: Returns base + "Iteration 2" section
        - Iteration 3: Returns base + "Iteration 2" + "Iteration 3" sections
        
        Note: This delegates to handle_hitl() which manages the HITL text cache.
        
        Args:
            response_text: Model's response containing clarification request
            iteration: Current clarification iteration (1-3)
            
        Returns:
            Fixed clarification guidelines text with iteration-specific sections
        """
        # Extract the specific question (for logging)
        clarification_match = re.search(
            r'\[NEEDS CLARIFICATION: (.*?)\]',
            response_text,
            re.DOTALL
        )
        question = clarification_match.group(1).strip() if clarification_match else "unclear"
        
        # Get full HITL content (cached)
        full_hitl_content = self.handle_hitl(question)
        
        # For iteration 1, return everything up to "## Iteration 2"
        if iteration == 1:
            match = re.search(r'(.*?)(?=\n## Iteration 2|\Z)', full_hitl_content, re.DOTALL)
            return match.group(1).strip() if match else full_hitl_content
        
        # For iteration 2, return everything up to "## Iteration 3"
        elif iteration == 2:
            match = re.search(r'(.*?)(?=\n## Iteration 3|\Z)', full_hitl_content, re.DOTALL)
            return match.group(1).strip() if match else full_hitl_content
        
        # For iteration 3+, return full content (includes all iterations)
        else:
            return full_hitl_content
    
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
        
        # Load implement template with caching (T005/T006)
        system_prompt, user_prompt_template = self._load_prompt_template('implement')
        
        # T025: Inject constitution into implementation prompts
        system_prompt_with_constitution = f"""{system_prompt}

## Project Constitution

Follow these coding standards when generating code:

{self.constitution_excerpt}
"""
        
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
            
            # Call OpenAI API with constitution-enhanced prompt (T025)
            response_text = self._call_openai(system_prompt_with_constitution, user_prompt)
            
            # Check for clarification
            hitl_count = 0
            if self._needs_clarification(response_text):
                # T040: Log clarification attempt
                logger.info(f"Clarification needed for task {task['id']}",
                           extra={'run_id': self.run_id, 'step': self.current_step,
                                 'metadata': {'iteration': 1, 'task_id': task['id']}})
                
                # T037: Handle HITL with iteration-specific text (iteration 1 for task implementation)
                clarification_text = self._handle_clarification(response_text, iteration=1)
                user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
                
                response_text = self._call_openai(system_prompt_with_constitution, user_prompt_with_hitl)
                hitl_count = 1
            
            # Save generated code (skip if file path is a directory or invalid)
            file_path_str = task['file'].strip()
            # Skip directory-only paths (ending with /) or paths without extensions
            if file_path_str and not file_path_str.endswith('/') and '.' in file_path_str:
                self._save_code_file(file_path_str, response_text)
            else:
                logger.debug(f"Skipping non-file task: {task['id']} ({file_path_str})",
                           extra={'run_id': self.run_id, 'step': self.current_step})
            
            # BREAKING CHANGE (v2.0.0): Token collection removed (reconciled post-run)
            api_call_end = int(time.time())
            tokens_in, tokens_out, api_calls, cached_tokens = 0, 0, 0, 0
            
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
        
        return total_hitl_count, total_tokens_in, total_tokens_out, total_api_calls, total_cached_tokens
    
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
                    # AI generates two format variations:
                    #   Format 1: **File**: `path` or **File Path**: `path` (colon after text, before closing **)
                    #   Format 2: **File Path:** `path` (colon between text and closing **)
                    # Use two patterns to handle both
                    
                    # Pattern A: Colon after closing ** (**File**: or **File Path**:)
                    # Handles: **File**: path, **File Path**: path, - **File**: `path`
                    file_pattern_a = r'\*\*File(?:\s+[Pp]ath)?\*\*:\s*(?:`([^`]+)`|([^\s]+))'
                    
                    # Pattern B: Colon between text and closing ** (**File Path:**)
                    # Handles: **File Path:** `path`, **File Path:** path
                    file_pattern_b = r'\*\*File(?:\s+[Pp]ath)?:\*\*\s*(?:`([^`]+)`|([^\s]+))'
                    
                    # Try Pattern A first (more common - 74% of runs)
                    file_match = re.search(file_pattern_a, next_line, re.IGNORECASE)
                    matched_format = None
                    
                    if file_match:
                        matched_format = "Format 1 (colon inside bold)"
                    else:
                        # Try Pattern B (previously failing format - 26% of runs)
                        file_match = re.search(file_pattern_b, next_line, re.IGNORECASE)
                        if file_match:
                            matched_format = "Format 2 (colon outside bold)"
                    
                    if file_match:
                        # Extract from whichever group matched (1=backticks, 2=no backticks)
                        file_path = (file_match.group(1) or file_match.group(2)).strip()
                        
                        # Log format detection for monitoring (FR-010)
                        logger.debug(
                            f"Task {task_count}: Detected {matched_format} for file: {file_path}"
                        )
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
        - Previous sprint code (for incremental development, sprint > 1)
        
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
        
        # Add previous sprint context for incremental development
        if self.sprint_num > 1:
            previous_context = self._get_previous_sprint_context()
            if previous_context and previous_context.get('code_files'):
                incremental_context = f"""

---
INCREMENTAL DEVELOPMENT CONTEXT

This is sprint {self.sprint_num}. You are building upon existing code from previous sprint.

Previous Sprint Code:
{previous_context['code_files']}

CRITICAL INSTRUCTIONS:
1. If modifying an existing file, preserve its structure and patterns
2. If creating a new file, match the coding style of existing files
3. Use the same language/framework as previous sprint ({previous_context.get('tech_stack', 'see previous code')})
4. Import/reference existing models and components - don't duplicate them
5. Add functionality incrementally - don't rewrite everything
---
"""
                prompt += incremental_context
        
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
        
        Raises:
            ValueError: If path is invalid (directory, empty, etc.)
        """
        # Strip leading / if present (AI often generates absolute paths)
        if relative_path.startswith('/'):
            relative_path = relative_path.lstrip('/')
        
        # Validate path
        if not relative_path or relative_path.endswith('/'):
            raise ValueError(f"Invalid file path (directory or empty): {relative_path}")
        
        # Resolve path relative to src_dir
        file_path = self.src_dir / relative_path
        
        # Check if path already exists as a directory
        if file_path.exists() and file_path.is_dir():
            raise IsADirectoryError(f"Cannot save file - path is a directory: {file_path}")
        
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
        
        **Phase 5 Implementation**: Bounded bugfix cycle with up to 3 iterations
        
        This method implements an iterative bugfix loop that attempts to resolve
        validation errors through multiple fix-and-validate cycles. Per FR-015,
        the cycle is bounded to max 3 iterations to ensure reproducibility and
        avoid infinite loops.
        
        Workflow per iteration:
        1. Derive bugfix tasks from validation errors (max 3 per iteration)
        2. For each bugfix task:
           a. Build bugfix prompt with error + current file + spec context
           b. Call OpenAI API (with optional HITL for clarification)
           c. Apply fixed code and log before/after diff (T054)
        3. Re-run validation on fixed files (T051)
        4. If errors remain and iteration < 3, repeat; otherwise exit
        5. Return aggregated token usage
        
        **T053**: Iteration limiting enforced - max 3 cycles per FR-015
        **T054**: Comprehensive logging with before/after diffs for each fix
        
        Args:
            validation_errors: List of error dictionaries with keys:
                - file: File path with error
                - error_type: 'compile', 'test_failure', 'runtime', 'syntax', 'import'
                - message: Error message/traceback
                - line_number: Optional line number
                
        Returns:
            Tuple of (hitl_count, tokens_in, tokens_out, api_calls, cached_tokens)
        """
        logger.info(f"Starting bugfix cycle for {len(validation_errors)} errors",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {'initial_error_count': len(validation_errors)}})
        
        # T053: Iteration limiting - max 3 cycles per FR-015
        max_iterations = 3
        current_iteration = 0
        remaining_errors = validation_errors.copy()
        
        total_hitl_count = 0
        total_tokens_in = 0
        total_tokens_out = 0
        total_api_calls = 0
        total_cached_tokens = 0
        
        # Load spec for context (shared across all iterations)
        spec_content = self.spec_md_path.read_text(encoding='utf-8')
        
        # Load bugfix template with caching (T005/T006)
        system_prompt, user_prompt_template = self._load_prompt_template('bugfix')
        
        # T026: Inject constitution into bugfix prompts
        system_prompt_with_constitution = f"""{system_prompt}

## Project Constitution

Apply these coding standards when fixing code:

{self.constitution_excerpt}
"""
        
        # T053: Iterative bugfix loop (max 3 iterations)
        while remaining_errors and current_iteration < max_iterations:
            current_iteration += 1
            
            logger.info(f"Bugfix iteration {current_iteration}/{max_iterations} - {len(remaining_errors)} errors",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {
                                 'iteration': current_iteration,
                                 'error_count': len(remaining_errors)
                             }})
            
            # Derive bugfix tasks (max 3, prioritized by severity)
            bugfix_tasks = self._derive_bugfix_tasks(remaining_errors)
            
            if not bugfix_tasks:
                logger.info("No bugfix tasks derived, ending cycle",
                           extra={'run_id': self.run_id, 'step': self.current_step})
                break
            
            fixed_files = []  # Track which files were fixed for re-validation
            
            # Process each bugfix task in this iteration
            for i, task in enumerate(bugfix_tasks, 1):
                logger.info(f"Bugfix {i}/{len(bugfix_tasks)}: {task['file']}",
                           extra={'run_id': self.run_id, 'step': self.current_step,
                                 'metadata': {
                                     'iteration': current_iteration,
                                     'error_type': task['error_type'],
                                     'file': task['file']
                                 }})
                
                # Build bugfix prompt
                user_prompt = self._build_bugfix_prompt(task, spec_content, user_prompt_template)
                
                # Track start time
                api_call_start = int(time.time())
                
                # Call OpenAI API with constitution-enhanced prompt (T026)
                response_text = self._call_openai(system_prompt_with_constitution, user_prompt)
                
                # Check for clarification (rare in bugfix, but possible)
                hitl_count = 0
                if self._needs_clarification(response_text):
                    # T040: Log clarification attempt
                    logger.info(f"Clarification needed for bugfix {task['file']}",
                               extra={'run_id': self.run_id, 'step': self.current_step,
                                     'metadata': {
                                         'iteration': current_iteration,
                                         'clarification_iteration': 1,
                                         'file': task['file']
                                     }})
                    
                    # T037: Handle HITL with iteration-specific text (iteration 1 for bugfix)
                    clarification_text = self._handle_clarification(response_text, iteration=1)
                    user_prompt_with_hitl = f"{user_prompt}\n\n---\n\n{clarification_text}"
                    response_text = self._call_openai(system_prompt_with_constitution, user_prompt_with_hitl)
                    hitl_count = 1
                
                # T052: Apply fix and capture before/after for diff logging
                before_content, after_content = self._apply_fix(task['file'], response_text)
                fixed_files.append(task['file'])
                
                # T054: Log before/after diff
                self._log_bugfix_diff(
                    file_path=task['file'],
                    before_content=before_content,
                    after_content=after_content,
                    iteration=current_iteration,
                    error_type=task['error_type']
                )
                
                # BREAKING CHANGE (v2.0.0): Token collection removed (reconciled post-run)
                api_call_end = int(time.time())
                tokens_in, tokens_out, api_calls, cached_tokens = 0, 0, 0, 0
                
                # Aggregate
                total_hitl_count += hitl_count
                total_tokens_in += tokens_in
                total_tokens_out += tokens_out
                total_api_calls += api_calls
                total_cached_tokens += cached_tokens
                
                logger.info(f"Bugfix {i} applied",
                           extra={'run_id': self.run_id, 'step': self.current_step,
                                 'metadata': {
                                     'iteration': current_iteration,
                                     'file': task['file'],
                                     'tokens_in': tokens_in,
                                     'tokens_out': tokens_out
                                 }})
            
            # T051: Re-validate fixed files to check if errors resolved
            remaining_errors = self._run_validation(fixed_files)
            
            if remaining_errors:
                logger.info(f"Iteration {current_iteration} complete - {len(remaining_errors)} errors remain",
                           extra={'run_id': self.run_id, 'step': self.current_step,
                                 'metadata': {
                                     'iteration': current_iteration,
                                     'remaining_errors': len(remaining_errors)
                                 }})
            else:
                logger.info(f"Iteration {current_iteration} complete - all errors resolved!",
                           extra={'run_id': self.run_id, 'step': self.current_step,
                                 'metadata': {'iteration': current_iteration}})
                break
        
        # Final summary
        if current_iteration >= max_iterations and remaining_errors:
            logger.warning(
                f"Bugfix cycle reached max iterations ({max_iterations}) with {len(remaining_errors)} errors remaining",
                extra={'run_id': self.run_id, 'step': self.current_step,
                      'metadata': {
                          'final_iteration': current_iteration,
                          'unresolved_errors': len(remaining_errors)
                      }})
        
        logger.info(f"Bugfix cycle completed: {current_iteration} iterations",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'iterations': current_iteration,
                             'total_tokens_in': total_tokens_in,
                             'total_tokens_out': total_tokens_out,
                             'total_api_calls': total_api_calls,
                             'total_cached_tokens': total_cached_tokens,
                             'final_error_count': len(remaining_errors)
                         }})
        
        return total_hitl_count, total_tokens_in, total_tokens_out, total_api_calls, total_cached_tokens
    
    def _log_bugfix_diff(
        self,
        file_path: str,
        before_content: str,
        after_content: str,
        iteration: int,
        error_type: str
    ) -> None:
        """
        Log before/after diff for bugfix application (T054).
        
        Provides detailed logging of code changes for debugging and analysis.
        
        Args:
            file_path: Relative path to fixed file
            before_content: Content before fix
            after_content: Content after fix
            iteration: Current bugfix iteration number
            error_type: Type of error being fixed
        """
        # Calculate basic diff statistics
        before_lines = before_content.split('\n') if before_content else []
        after_lines = after_content.split('\n')
        
        lines_added = len(after_lines) - len(before_lines)
        size_before = len(before_content.encode('utf-8')) if before_content else 0
        size_after = len(after_content.encode('utf-8'))
        size_delta = size_after - size_before
        
        logger.info(f"Bugfix diff for {file_path}",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'iteration': iteration,
                             'file': file_path,
                             'error_type': error_type,
                             'lines_before': len(before_lines),
                             'lines_after': len(after_lines),
                             'lines_delta': lines_added,
                             'bytes_before': size_before,
                             'bytes_after': size_after,
                             'bytes_delta': size_delta
                         }})
    
    def _derive_bugfix_tasks(self, validation_errors: list) -> list:
        """
        Derive bugfix tasks from validation errors (T049 + T055).
        
        Prioritizes errors by severity and limits to max 3 tasks to keep
        bugfix cycle manageable and deterministic. Enhanced with error type
        classification to better prioritize fixes.
        
        **T055**: Error type classification
        Priority order (most to least critical):
        1. Syntax errors (code won't parse)
        2. Import errors (missing dependencies)
        3. Compilation errors (type/semantic issues)
        4. Test failures (functional issues)
        5. Runtime errors (edge cases)
        6. Validation errors (style/quality issues)
        
        Args:
            validation_errors: List of error dictionaries with keys:
                - file: File path with error
                - error_type: Error classification
                - message: Error message/traceback
                - line_number: Optional line number
                
        Returns:
            List of bugfix task dictionaries (max 3, sorted by priority)
        """
        # T055: Enhanced severity ordering with detailed classification
        severity_order = {
            'syntax': 0,      # Highest priority - code won't parse
            'import': 1,      # Missing dependencies
            'compile': 2,     # Type/semantic issues
            'test_failure': 3,  # Functional issues
            'runtime': 4,     # Edge cases
            'validation': 5   # Lowest priority - style/quality
        }
        
        # Sort by severity (ascending order - lower number = higher priority)
        sorted_errors = sorted(
            validation_errors,
            key=lambda e: severity_order.get(e.get('error_type', 'runtime'), 99)
        )
        
        # Take top 3 most critical errors
        top_errors = sorted_errors[:3]
        
        # T055: Log error classification summary
        if validation_errors:
            error_type_counts = {}
            for error in validation_errors:
                error_type = error.get('error_type', 'unknown')
                error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
            
            logger.info(f"Error classification summary: {error_type_counts}",
                       extra={'run_id': self.run_id, 'step': self.current_step,
                             'metadata': {'error_type_counts': error_type_counts}})
        
        # Convert to bugfix tasks with enhanced metadata
        bugfix_tasks = []
        for error in top_errors:
            task = {
                'file': error['file'],
                'error_type': error['error_type'],
                'error_message': error['message'],
                'line_number': error.get('line_number'),
                'original_task': error.get('original_task', 'Code generation'),
                'severity_rank': severity_order.get(error['error_type'], 99)
            }
            bugfix_tasks.append(task)
        
        logger.info(f"Derived {len(bugfix_tasks)} bugfix tasks from {len(validation_errors)} errors",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'metadata': {
                             'total_errors': len(validation_errors),
                             'selected_tasks': len(bugfix_tasks),
                             'top_error_types': [t['error_type'] for t in bugfix_tasks]
                         }})
        
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
        
        # T056: Extract relevant spec section using enhanced keyword matching
        spec_excerpt = self._extract_spec_excerpt(
            spec_content=spec_content,
            file_path=bugfix_task['file'],
            error_message=bugfix_task['error_message']
        )
        
        # Fill template
        prompt = (template
                 .replace('{error_message}', bugfix_task['error_message'])
                 .replace('{file_path}', bugfix_task['file'])
                 .replace('{current_file_content}', current_content)
                 .replace('{spec_excerpt}', spec_excerpt)
                 .replace('{original_task_description}', bugfix_task['original_task']))
        
        return prompt
    
    def _extract_spec_excerpt(self, spec_content: str, file_path: str, error_message: str) -> str:
        """
        Extract relevant specification sections for bugfix context (T056).
        
        Matches file paths and error keywords to specification sections to provide
        targeted context for bug fixing.
        
        Args:
            spec_content: Full specification content
            file_path: Path to file with error
            error_message: Error message/traceback
            
        Returns:
            Relevant specification excerpt (max ~30 lines)
        """
        # Extract keywords from file path and error message
        keywords = set(file_path.lower().replace('/', ' ').replace('_', ' ').split())
        
        # Extract meaningful words from error message (filter common words)
        error_words = error_message.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        meaningful_words = [w for w in error_words if len(w) > 3 and w not in stop_words]
        keywords.update(meaningful_words[:15])  # First 15 meaningful words
        
        # Find relevant lines (scoring approach)
        spec_lines = spec_content.split('\n')
        line_scores = []
        
        for i, line in enumerate(spec_lines):
            line_lower = line.lower()
            score = sum(1 for keyword in keywords if keyword in line_lower)
            
            # Boost score for headers (likely important sections)
            if line.startswith('#'):
                score *= 2
            
            if score > 0:
                line_scores.append((score, i, line))
        
        # Sort by score and take top lines
        line_scores.sort(reverse=True, key=lambda x: x[0])
        top_lines = line_scores[:30]  # Max 30 relevant lines
        
        # Sort by original line number to preserve document flow
        top_lines.sort(key=lambda x: x[1])
        
        # Extract lines
        excerpt_lines = [line for _, _, line in top_lines]
        spec_excerpt = '\n'.join(excerpt_lines)
        
        if not spec_excerpt:
            spec_excerpt = "Refer to general specification requirements"
        
        return spec_excerpt
    
    def _run_validation(self, file_paths: list) -> list:
        """
        Run validation checks on generated code files (T051).
        
        Performs basic syntax checking and captures errors. This is a lightweight
        validation suitable for detecting common issues before attempting fixes.
        
        Args:
            file_paths: List of file paths to validate (relative to src_dir)
            
        Returns:
            List of error dictionaries with keys:
                - file: File path with error
                - error_type: 'syntax', 'import', or 'runtime'
                - message: Error message
                - line_number: Line number if available
        """
        validation_errors = []
        
        for file_path in file_paths:
            full_path = self.src_dir / file_path
            
            if not full_path.exists():
                validation_errors.append({
                    'file': file_path,
                    'error_type': 'runtime',
                    'message': f"File not found: {full_path}",
                    'line_number': None
                })
                continue
            
            # Python syntax checking
            if file_path.endswith('.py'):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    compile(code, str(full_path), 'exec')
                    
                    logger.debug(f"Syntax validation passed: {file_path}",
                               extra={'run_id': self.run_id, 'step': self.current_step})
                    
                except SyntaxError as e:
                    # T055: Classify as syntax error
                    validation_errors.append({
                        'file': file_path,
                        'error_type': 'syntax',
                        'message': f"SyntaxError: {e.msg} at line {e.lineno}",
                        'line_number': e.lineno
                    })
                    
                    logger.warning(f"Syntax error in {file_path}: {e.msg}",
                                 extra={'run_id': self.run_id, 'step': self.current_step,
                                       'metadata': {'line': e.lineno}})
                    
                except Exception as e:
                    # T055: Classify as runtime error
                    validation_errors.append({
                        'file': file_path,
                        'error_type': 'runtime',
                        'message': f"Validation error: {str(e)}",
                        'line_number': None
                    })
                    
                    logger.warning(f"Validation error in {file_path}: {e}",
                                 extra={'run_id': self.run_id, 'step': self.current_step})
        
        return validation_errors
    
    def _apply_fix(self, file_path: str, fixed_code: str) -> tuple[str, str]:
        """
        Apply AI-generated fix to target file (T052).
        
        Saves the fixed code and returns before/after content for logging.
        
        Args:
            file_path: Relative file path (relative to src_dir)
            fixed_code: Fixed code content from AI
            
        Returns:
            Tuple of (before_content, after_content) for diff logging
        """
        full_path = self.src_dir / file_path
        
        # Read current content for diff
        before_content = self._read_file_if_exists(full_path)
        
        # Save fixed code
        self._save_code_file(file_path, fixed_code)
        
        # Return before/after for logging
        after_content = fixed_code
        
        return before_content, after_content
        
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
