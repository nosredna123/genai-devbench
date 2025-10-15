"""
Integration tests for GHSpec adapter Phase 3: Spec/Plan/Tasks generation.

These tests verify the complete workflow of specification generation through
OpenAI API calls. They require:
- OPENAI_API_KEY_GHSPEC environment variable set
- Internet connection to access OpenAI API
- Valid prompt templates in docs/ghspec/prompts/

Note: These are integration tests that make real API calls and will consume tokens.
Mark as slow and skip in fast test runs.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.adapters.ghspec_adapter import GHSpecAdapter


@pytest.mark.integration
@pytest.mark.slow
class TestGHSpecAdapterPhase3Integration:
    """Integration tests for Phase 3: Spec/Plan/Tasks generation"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for GHSpec."""
        return {
            'repo_url': 'https://github.com/github/spec-kit.git',
            'commit_hash': '89f4b0b38a42996376c0f083d47281a4c9196761',
            'api_port': 8002,
            'ui_port': 3002,
            'api_key_env': 'OPENAI_API_KEY_GHSPEC'
        }
    
    @pytest.fixture
    def adapter_with_workspace(self, mock_config, temp_workspace):
        """Create adapter instance with workspace structure initialized."""
        adapter = GHSpecAdapter(
            config=mock_config,
            run_id='test-run-phase3',
            workspace_path=temp_workspace
        )
        
        # Setup workspace structure (skip repo cloning for tests)
        adapter.framework_dir = Path(temp_workspace) / "ghspec_framework"
        adapter.framework_dir.mkdir(parents=True, exist_ok=True)
        adapter._setup_workspace_structure()
        
        return adapter
    
    def test_load_prompt_template(self, adapter_with_workspace):
        """Test loading system and user prompts from template file."""
        template_path = Path("docs/ghspec/prompts/specify_template.md")
        
        system_prompt, user_prompt_template = adapter_with_workspace._load_prompt_template(template_path)
        
        # Verify prompts were extracted
        assert len(system_prompt) > 100, "System prompt should be substantial"
        assert len(user_prompt_template) > 100, "User prompt template should be substantial"
        assert '{user_command}' in user_prompt_template, "User prompt should have placeholder"
        assert 'business analyst' in system_prompt.lower(), "System prompt should define role"
    
    def test_build_phase_prompt_specify(self, adapter_with_workspace):
        """Test building specify phase prompt with user command."""
        template = "Feature: {user_command}\n\nGenerate specification..."
        command = "Build a todo list application"
        
        prompt = adapter_with_workspace._build_phase_prompt('specify', template, command)
        
        assert 'Build a todo list application' in prompt
        assert '{user_command}' not in prompt
    
    def test_build_phase_prompt_plan(self, adapter_with_workspace):
        """Test building plan phase prompt with spec content."""
        # Create mock spec.md
        spec_content = "# Feature Specification\n\nBuild a calculator..."
        adapter_with_workspace.spec_md_path.write_text(spec_content, encoding='utf-8')
        
        template = "Specification:\n{spec_content}\n\nGenerate plan..."
        
        prompt = adapter_with_workspace._build_phase_prompt('plan', template, "")
        
        assert 'Build a calculator' in prompt
        assert '{spec_content}' not in prompt
    
    def test_build_phase_prompt_tasks(self, adapter_with_workspace):
        """Test building tasks phase prompt with spec + plan content."""
        # Create mock artifacts
        spec_content = "# Feature: Calculator"
        plan_content = "## Architecture\nUse Python FastAPI..."
        adapter_with_workspace.spec_md_path.write_text(spec_content, encoding='utf-8')
        adapter_with_workspace.plan_md_path.write_text(plan_content, encoding='utf-8')
        
        template = "Spec:\n{spec_content}\n\nPlan:\n{plan_content}\n\nGenerate tasks..."
        
        prompt = adapter_with_workspace._build_phase_prompt('tasks', template, "")
        
        assert 'Feature: Calculator' in prompt
        assert 'Python FastAPI' in prompt
        assert '{spec_content}' not in prompt
        assert '{plan_content}' not in prompt
    
    def test_needs_clarification_detection(self, adapter_with_workspace):
        """Test detection of clarification requests in model responses."""
        # Response with clarification
        response_with_clarification = """
        # Feature Specification
        
        [NEEDS CLARIFICATION: What authentication method should we use?]
        
        The system will...
        """
        
        # Response without clarification
        response_without_clarification = """
        # Feature Specification
        
        The system will provide user authentication...
        """
        
        assert adapter_with_workspace._needs_clarification(response_with_clarification) is True
        assert adapter_with_workspace._needs_clarification(response_without_clarification) is False
    
    def test_save_artifact(self, adapter_with_workspace):
        """Test saving generated artifact to workspace."""
        content = "# Feature Specification\n\nThis is a test specification."
        output_path = adapter_with_workspace.spec_md_path
        
        adapter_with_workspace._save_artifact(output_path, content)
        
        assert output_path.exists()
        assert output_path.read_text(encoding='utf-8') == content
    
    @pytest.mark.skipif(
        not os.getenv('OPENAI_API_KEY_GHSPEC'),
        reason="OPENAI_API_KEY_GHSPEC not set"
    )
    def test_call_openai_real_api(self, adapter_with_workspace):
        """
        Test real OpenAI API call (requires API key).
        
        WARNING: This test makes a real API call and consumes tokens.
        """
        system_prompt = "You are a helpful assistant."
        user_prompt = "Say 'Hello, World!' and nothing else."
        
        response = adapter_with_workspace._call_openai(system_prompt, user_prompt)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert 'Hello' in response or 'hello' in response
    
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_execute_phase_specify_mocked(self, mock_fetch_usage, mock_call_openai, adapter_with_workspace):
        """Test specify phase execution with mocked API."""
        # Mock API response
        mock_call_openai.return_value = """
# Feature: Todo List Application

## Overview
A simple todo list application for task management.

## Functional Requirements
1. Users SHALL be able to create tasks
2. Users SHALL be able to mark tasks as complete
3. Users SHALL be able to delete tasks

## Success Criteria
- Users can manage personal todo lists
- Tasks persist across sessions
"""
        
        # Mock token usage
        mock_fetch_usage.return_value = (150, 350)
        
        # Execute specify phase
        hitl_count, tokens_in, tokens_out, start_timestamp, end_timestamp = adapter_with_workspace._execute_phase(
            'specify',
            'Build a todo list application'
        )
        
        # Verify API was called
        assert mock_call_openai.called
        assert mock_fetch_usage.called
        
        # Verify results
        assert hitl_count == 0  # No clarification needed
        assert tokens_in == 150
        assert tokens_out == 350
        
        # Verify timestamps are valid Unix timestamps
        assert isinstance(start_timestamp, int)
        assert isinstance(end_timestamp, int)
        assert start_timestamp > 0
        assert end_timestamp >= start_timestamp
        assert tokens_out == 350
        
        # Verify artifact was saved
        assert adapter_with_workspace.spec_md_path.exists()
        spec_content = adapter_with_workspace.spec_md_path.read_text()
        assert 'Todo List Application' in spec_content
    
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_execute_phase_with_clarification_mocked(self, mock_fetch_usage, mock_call_openai, adapter_with_workspace):
        """Test phase execution with clarification handling (mocked)."""
        # First call: Request clarification
        # Second call: Complete response after HITL
        mock_call_openai.side_effect = [
            """
# Feature: Authentication System

[NEEDS CLARIFICATION: What authentication method should be used?]

## Overview
User authentication system...
""",
            """
# Feature: Authentication System

## Overview
User authentication system using JWT tokens.

## Functional Requirements
1. Users SHALL authenticate via JWT tokens
2. Tokens SHALL expire after 24 hours
"""
        ]
        
        # Mock token usage (called twice)
        mock_fetch_usage.return_value = (200, 400)
        
        # Execute phase
        hitl_count, tokens_in, tokens_out, start_timestamp, end_timestamp = adapter_with_workspace._execute_phase(
            'specify',
            'Build an authentication system'
        )
        
        # Verify HITL handling
        assert hitl_count == 1  # One clarification
        assert mock_call_openai.call_count == 2  # Called twice (initial + after HITL)
        
        # Verify timestamps
        assert isinstance(start_timestamp, int)
        assert isinstance(end_timestamp, int)
        assert start_timestamp > 0
        assert end_timestamp >= start_timestamp
        
        # Verify final artifact doesn't have clarification marker
        spec_content = adapter_with_workspace.spec_md_path.read_text()
        assert '[NEEDS CLARIFICATION' not in spec_content
        assert 'JWT tokens' in spec_content


@pytest.mark.unit
class TestGHSpecAdapterPhase3Unit:
    """Unit tests for Phase 3 helper methods"""
    
    @pytest.fixture
    def adapter(self):
        """Create minimal adapter instance for unit tests."""
        config = {
            'api_key_env': 'OPENAI_API_KEY_GHSPEC',
            'repo_url': 'https://github.com/github/spec-kit.git',
            'commit_hash': 'abc123'
        }
        return GHSpecAdapter(config, 'test-run', '/tmp/test')
    
    def test_needs_clarification_edge_cases(self, adapter):
        """Test clarification detection with edge cases."""
        # Multiple clarifications
        multi_clarification = """
        [NEEDS CLARIFICATION: Question 1]
        Some text
        [NEEDS CLARIFICATION: Question 2]
        """
        assert adapter._needs_clarification(multi_clarification) is True
        
        # Case sensitivity
        lowercase = "[needs clarification: something]"
        assert adapter._needs_clarification(lowercase) is False
        
        # Partial match
        partial = "This needs clarification but not marked"
        assert adapter._needs_clarification(partial) is False
        
        # Empty string
        assert adapter._needs_clarification("") is False
