"""
Integration tests for GHSpec adapter Phase 5: HITL & Bugfix loops.

Tests the validation-driven bugfix cycle implementation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.adapters.ghspec_adapter import GHSpecAdapter


@pytest.mark.integration
class TestGHSpecAdapterPhase5:
    """Integration tests for Phase 5: HITL & Bugfix Loops"""
    
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
    def adapter_with_code(self, mock_config, temp_workspace):
        """Create adapter with workspace and mock code files."""
        adapter = GHSpecAdapter(
            config=mock_config,
            run_id='test-run-phase5',
            workspace_path=temp_workspace
        )
        
        # Setup workspace structure
        adapter.framework_dir = Path(temp_workspace) / "ghspec_framework"
        adapter.framework_dir.mkdir(parents=True, exist_ok=True)
        adapter._setup_workspace_structure()
        
        # Create mock spec.md
        spec_content = """
# Feature: Calculator Application

## Functional Requirements
1. System SHALL support addition, subtraction, multiplication, division
2. System SHALL validate input is numeric
3. System SHALL handle division by zero gracefully

## Key Entities
- Calculator: Main class with arithmetic methods
"""
        adapter.spec_md_path.write_text(spec_content, encoding='utf-8')
        
        # Create mock code file with an error
        buggy_code = """
def add(a, b):
    return a + b

def divide(a, b):
    return a / b  # Bug: No division by zero check
"""
        code_file = adapter.src_dir / "calculator.py"
        code_file.parent.mkdir(parents=True, exist_ok=True)
        code_file.write_text(buggy_code, encoding='utf-8')
        
        return adapter
    
    def test_derive_bugfix_tasks_prioritization(self, adapter_with_code):
        """Test bugfix task derivation prioritizes by severity."""
        errors = [
            {
                'file': 'calculator.py',
                'error_type': 'runtime',
                'message': 'Division by zero',
                'line_number': 6
            },
            {
                'file': 'main.py',
                'error_type': 'compile',
                'message': 'SyntaxError: invalid syntax',
                'line_number': 10
            },
            {
                'file': 'test_calc.py',
                'error_type': 'test_failure',
                'message': 'AssertionError: Expected 5, got 6',
                'line_number': 15
            }
        ]
        
        bugfix_tasks = adapter_with_code._derive_bugfix_tasks(errors)
        
        # Should return all 3 (max 3)
        assert len(bugfix_tasks) == 3
        
        # Should be prioritized: compile first, test_failure second, runtime third
        assert bugfix_tasks[0]['error_type'] == 'compile'
        assert bugfix_tasks[1]['error_type'] == 'test_failure'
        assert bugfix_tasks[2]['error_type'] == 'runtime'
    
    def test_derive_bugfix_tasks_limits_to_three(self, adapter_with_code):
        """Test bugfix task derivation limits to max 3 tasks."""
        errors = [
            {'file': f'file{i}.py', 'error_type': 'runtime', 'message': f'Error {i}'}
            for i in range(10)
        ]
        
        bugfix_tasks = adapter_with_code._derive_bugfix_tasks(errors)
        
        # Should limit to 3
        assert len(bugfix_tasks) == 3
    
    def test_build_bugfix_prompt(self, adapter_with_code):
        """Test building bugfix prompt with error context."""
        bugfix_task = {
            'file': 'calculator.py',
            'error_type': 'runtime',
            'error_message': 'ZeroDivisionError: division by zero at line 6',
            'line_number': 6,
            'original_task': 'Implement division function'
        }
        
        spec_content = adapter_with_code.spec_md_path.read_text()
        
        template = """
ERROR: {error_message}
FILE: {file_path}
CODE: {current_file_content}
SPEC: {spec_excerpt}
TASK: {original_task_description}
"""
        
        prompt = adapter_with_code._build_bugfix_prompt(
            bugfix_task, spec_content, template
        )
        
        # Verify all placeholders filled
        assert 'ZeroDivisionError' in prompt
        assert 'calculator.py' in prompt
        assert 'def divide' in prompt  # Current code
        assert 'Implement division function' in prompt
        # Should include spec context (even if simplified)
        assert '{spec_excerpt}' not in prompt
    
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_attempt_bugfix_cycle_mocked(
        self, mock_fetch_usage, mock_call_openai, adapter_with_code
    ):
        """Test complete bugfix cycle (mocked)."""
        # Mock API response with fixed code
        fixed_code = """
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""
        mock_call_openai.return_value = fixed_code
        mock_fetch_usage.return_value = (100, 200)
        
        # Create validation errors
        errors = [
            {
                'file': 'calculator.py',
                'error_type': 'test_failure',
                'message': 'Test failed: divide(10, 0) should raise ValueError',
                'original_task': 'Implement division'
            }
        ]
        
        # Execute bugfix cycle
        adapter_with_code.current_step = 6
        hitl_count, tokens_in, tokens_out = adapter_with_code.attempt_bugfix_cycle(errors)
        
        # Verify API was called
        assert mock_call_openai.called
        
        # Verify tokens tracked
        assert tokens_in == 100
        assert tokens_out == 200
        assert hitl_count == 0
        
        # Verify file was updated
        updated_code = (adapter_with_code.src_dir / "calculator.py").read_text()
        assert 'if b == 0:' in updated_code
        assert 'Cannot divide by zero' in updated_code
    
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_attempt_bugfix_cycle_multiple_errors(
        self, mock_fetch_usage, mock_call_openai, adapter_with_code
    ):
        """Test bugfix cycle handles multiple errors."""
        # Mock responses for multiple files
        mock_call_openai.side_effect = [
            "# Fixed calculator.py",
            "# Fixed validator.py",
            "# Fixed main.py"
        ]
        mock_fetch_usage.return_value = (100, 200)
        
        # Create multiple validation errors
        errors = [
            {
                'file': 'calculator.py',
                'error_type': 'compile',
                'message': 'SyntaxError',
                'original_task': 'Calculator implementation'
            },
            {
                'file': 'validator.py',
                'error_type': 'test_failure',
                'message': 'Validation test failed',
                'original_task': 'Input validation'
            },
            {
                'file': 'main.py',
                'error_type': 'runtime',
                'message': 'IndexError',
                'original_task': 'Main entry point'
            }
        ]
        
        # Create the additional files
        (adapter_with_code.src_dir / "validator.py").write_text("# Buggy validator")
        (adapter_with_code.src_dir / "main.py").write_text("# Buggy main")
        
        adapter_with_code.current_step = 6
        hitl_count, tokens_in, tokens_out = adapter_with_code.attempt_bugfix_cycle(errors)
        
        # Should have called API 3 times
        assert mock_call_openai.call_count == 3
        
        # Tokens aggregated
        assert tokens_in == 300  # 100 * 3
        assert tokens_out == 600  # 200 * 3
    
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_attempt_bugfix_cycle_empty_errors(
        self, mock_fetch_usage, mock_call_openai, adapter_with_code
    ):
        """Test bugfix cycle handles no errors gracefully."""
        errors = []
        
        adapter_with_code.current_step = 6
        hitl_count, tokens_in, tokens_out = adapter_with_code.attempt_bugfix_cycle(errors)
        
        # Should not call API
        assert not mock_call_openai.called
        
        # Should return zero tokens
        assert hitl_count == 0
        assert tokens_in == 0
        assert tokens_out == 0


@pytest.mark.unit
class TestGHSpecAdapterPhase5Unit:
    """Unit tests for Phase 5 helper methods"""
    
    def test_derive_bugfix_tasks_handles_missing_fields(self):
        """Test bugfix task derivation handles missing optional fields."""
        errors = [
            {
                'file': 'test.py',
                'error_type': 'compile',
                'message': 'Syntax error'
                # Missing line_number and original_task
            }
        ]
        
        config = {'api_key_env': 'TEST', 'repo_url': 'test', 'commit_hash': 'abc'}
        adapter = GHSpecAdapter(config, 'test', '/tmp/test')
        
        bugfix_tasks = adapter._derive_bugfix_tasks(errors)
        
        assert len(bugfix_tasks) == 1
        assert bugfix_tasks[0]['file'] == 'test.py'
        assert bugfix_tasks[0]['line_number'] is None
        assert bugfix_tasks[0]['original_task'] == 'Code generation'  # Default
    
    def test_derive_bugfix_tasks_unknown_error_type(self):
        """Test bugfix tasks handles unknown error types."""
        errors = [
            {
                'file': 'test1.py',
                'error_type': 'unknown_type',
                'message': 'Unknown error'
            },
            {
                'file': 'test2.py',
                'error_type': 'compile',
                'message': 'Syntax error'
            }
        ]
        
        config = {'api_key_env': 'TEST', 'repo_url': 'test', 'commit_hash': 'abc'}
        adapter = GHSpecAdapter(config, 'test', '/tmp/test')
        
        bugfix_tasks = adapter._derive_bugfix_tasks(errors)
        
        # Should include both, with compile first (higher priority)
        assert len(bugfix_tasks) == 2
        assert bugfix_tasks[0]['error_type'] == 'compile'
        assert bugfix_tasks[1]['error_type'] == 'unknown_type'
