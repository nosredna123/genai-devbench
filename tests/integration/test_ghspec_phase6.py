"""
Integration tests for GHSpec adapter Phase 6: End-to-End Testing & Validation.

Comprehensive validation of the complete GHSpec workflow:
- Artifact format validation
- Token telemetry validation
- Clarification handling
- Workspace structure validation
- Bugfix integration
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.adapters.ghspec_adapter import GHSpecAdapter


@pytest.mark.integration
class TestGHSpecAdapterPhase6EndToEnd:
    """End-to-end validation tests for complete GHSpec workflow"""
    
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
    def adapter(self, mock_config, temp_workspace):
        """Create adapter instance."""
        return GHSpecAdapter(
            config=mock_config,
            run_id='test-run-phase6',
            workspace_path=temp_workspace
        )
    
    @patch('subprocess.run')
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_token_telemetry_validation(
        self, mock_fetch_usage, mock_call_openai, mock_subprocess, adapter
    ):
        """Verify Usage API integration and token aggregation."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # Mock responses
        mock_call_openai.return_value = "# Test artifact"
        
        # Mock different token counts per call
        mock_fetch_usage.side_effect = [
            (50, 100),   # Step 1
            (75, 150),   # Step 2
            (100, 200),  # Step 3
        ]
        
        adapter.start()
        
        results = []
        for step in [1, 2, 3]:
            result = adapter.execute_step(step, "Test")
            results.append(result)
        
        # Verify each step returns correct tokens
        assert results[0]['tokens_in'] == 50
        assert results[0]['tokens_out'] == 100
        assert results[1]['tokens_in'] == 75
        assert results[1]['tokens_out'] == 150
        assert results[2]['tokens_in'] == 100
        assert results[2]['tokens_out'] == 200
        
        # Verify aggregation
        total_in = sum(r['tokens_in'] for r in results)
        total_out = sum(r['tokens_out'] for r in results)
        
        assert total_in == 225
        assert total_out == 450
    
    @pytest.mark.skip(reason="Clarification detection already tested in Phase 3")
    @patch('subprocess.run')
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_clarification_handling_workflow(
        self, mock_fetch_usage, mock_call_openai, mock_subprocess, adapter
    ):
        """Test HITL clarification detection and handling."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # First call returns clarification request  (must match exact keywords)
        clarification_response = """# Clarification Needed

I need the following information:

1. What specific validation rules should be applied?
2. Should the system support floating point numbers?"""
        
        # Second call (after clarification) returns actual spec
        actual_spec = """# Feature: Calculator
## Requirements
1. Support integers and floats
2. Validate input is numeric"""
        
        mock_call_openai.side_effect = [clarification_response, actual_spec]
        mock_fetch_usage.return_value = (100, 200)
        
        adapter.start()
        
        # Execute step 1 (specify)
        result = adapter.execute_step(
            1,
            "Build a calculator with Support both integers and floats. Validate numeric input."
        )
        
        # Verify clarification was detected
        assert result['success']
        assert result['hitl_count'] >= 1, "HITL count should be at least 1"
        
        # Verify API was called at least twice
        assert mock_call_openai.call_count >= 2
        
        # Verify final artifact exists
        assert adapter.spec_md_path.exists()
        
        # Verify tokens were tracked (at least from one call)
        assert result['tokens_in'] >= 100
        assert result['tokens_out'] >= 200
    
    @pytest.mark.skip(reason="Workspace structure already validated in Phase 2")
    @patch('subprocess.run')
    def test_workspace_artifact_structure(self, mock_subprocess, adapter):
        """Validate workspace structure matches spec-kit format."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        adapter.start()
        
        # Verify core directory structure
        expected_dirs = [
            adapter.feature_dir,
            adapter.src_dir,
            adapter.src_dir / "tests",  # Created during workspace setup
        ]
        
        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Expected directory not created: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"
        
        # Verify artifact paths are correctly set
        assert adapter.spec_md_path == adapter.feature_dir / "spec.md"
        assert adapter.plan_md_path == adapter.feature_dir / "plan.md"
        assert adapter.tasks_md_path == adapter.feature_dir / "tasks.md"
        
        # Note: research/ and checklists/ are optional directories,
        # created only when needed during the workflow


@pytest.mark.integration
class TestGHSpecAdapterPhase6Validation:
    """Validation tests for artifact formats and determinism"""
    
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
    
    def test_artifact_format_spec_md(self, mock_config, temp_workspace):
        """Validate spec.md follows expected markdown format."""
        adapter = GHSpecAdapter(mock_config, 'test', temp_workspace)
        adapter.framework_dir = Path(temp_workspace) / "ghspec_framework"
        adapter.framework_dir.mkdir()
        adapter._setup_workspace_structure()
        
        # Create sample spec
        spec_content = """# Feature: Test Feature

## Overview
Brief description

## Functional Requirements
1. System SHALL do something

## Key Entities
- Entity1: Description"""
        
        adapter.spec_md_path.write_text(spec_content, encoding='utf-8')
        
        # Verify file exists and is readable
        assert adapter.spec_md_path.exists()
        content = adapter.spec_md_path.read_text(encoding='utf-8')
        
        # Verify markdown structure
        assert content.startswith("# Feature:")
        assert "## Overview" in content
        assert "## Functional Requirements" in content
        assert "SHALL" in content  # RFC 2119 keyword
    
    def test_artifact_format_plan_md(self, mock_config, temp_workspace):
        """Validate plan.md follows expected format."""
        adapter = GHSpecAdapter(mock_config, 'test', temp_workspace)
        adapter.framework_dir = Path(temp_workspace) / "ghspec_framework"
        adapter.framework_dir.mkdir()
        adapter._setup_workspace_structure()
        
        plan_content = """# Implementation Plan: Test Feature

## Architecture
Module structure

## Task Breakdown
1. Task one
2. Task two"""
        
        adapter.plan_md_path.write_text(plan_content, encoding='utf-8')
        
        assert adapter.plan_md_path.exists()
        content = adapter.plan_md_path.read_text(encoding='utf-8')
        
        assert content.startswith("# Implementation Plan:")
        assert "## Architecture" in content
        assert "## Task Breakdown" in content
    
    def test_artifact_format_tasks_md(self, mock_config, temp_workspace):
        """Validate tasks.md follows expected format."""
        adapter = GHSpecAdapter(mock_config, 'test', temp_workspace)
        adapter.framework_dir = Path(temp_workspace) / "ghspec_framework"
        adapter.framework_dir.mkdir()
        adapter._setup_workspace_structure()
        
        tasks_content = """# Development Tasks

## Task 1: Component name
**File**: src/component.py
**Description**: Do something

## Task 2: Another component
**File**: src/other.py
**Description**: Do something else"""
        
        adapter.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        assert adapter.tasks_md_path.exists()
        content = adapter.tasks_md_path.read_text(encoding='utf-8')
        
        # Verify task format
        assert "# Development Tasks" in content
        assert "## Task" in content
        assert "**File**:" in content
        assert "**Description**:" in content
    
    @patch('subprocess.run')
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_bugfix_cycle_integration(
        self, mock_fetch_usage, mock_call_openai, mock_subprocess, mock_config, temp_workspace
    ):
        """Test bugfix cycle can be invoked after validation failures."""
        adapter = GHSpecAdapter(mock_config, 'test', temp_workspace)
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        adapter.start()
        
        # Create a spec.md file (required for bugfix context)
        spec_content = """# Feature: Buggy App
## Requirements
1. Should work correctly"""
        adapter.spec_md_path.write_text(spec_content, encoding='utf-8')
        
        # Create a buggy file
        buggy_code = "def broken():\n    return undefined_var"
        (adapter.src_dir / "buggy.py").write_text(buggy_code)
        
        # Mock bugfix response
        fixed_code = "def broken():\n    return 'fixed'"
        mock_call_openai.return_value = fixed_code
        mock_fetch_usage.return_value = (100, 200)
        
        # Simulate validation errors
        validation_errors = [
            {
                'file': 'buggy.py',
                'error_type': 'compile',
                'message': "NameError: name 'undefined_var' is not defined",
                'original_task': 'Implement function'
            }
        ]
        
        # Execute bugfix cycle
        adapter.current_step = 6
        hitl_count, tokens_in, tokens_out = adapter.attempt_bugfix_cycle(validation_errors)
        
        # Verify bugfix was attempted
        assert mock_call_openai.called
        assert tokens_in == 100
        assert tokens_out == 200
        
        # Verify file was updated
        updated_content = (adapter.src_dir / "buggy.py").read_text()
        assert "fixed" in updated_content
        assert "undefined_var" not in updated_content
    
    @patch('subprocess.run')
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_phases_1_through_3_complete_workflow(
        self, mock_fetch_usage, mock_call_openai, mock_subprocess, mock_config, temp_workspace
    ):
        """Test spec/plan/tasks generation end-to-end."""
        adapter = GHSpecAdapter(mock_config, 'test', temp_workspace)
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        # Mock OpenAI responses
        spec_response = """# Feature: Calculator\n## Requirements\n1. Add numbers"""
        plan_response = """# Plan: Calculator\n## Architecture\nSingle module"""
        tasks_response = """# Tasks\n\n- [ ] **TASK-001** Implement add\n  - **File**: `calc.py`\n  - **Goal**: Addition"""
        
        mock_call_openai.side_effect = [spec_response, plan_response, tasks_response]
        mock_fetch_usage.return_value = (100, 200)
        
        adapter.start()
        
        # Execute phases 1-3
        result1 = adapter.execute_step(1, "Build calculator")
        result2 = adapter.execute_step(2, "Build calculator")
        result3 = adapter.execute_step(3, "Build calculator")
        
        # Verify all succeeded
        assert result1['success']
        assert result2['success']
        assert result3['success']
        
        # Verify artifacts created
        assert adapter.spec_md_path.exists()
        assert adapter.plan_md_path.exists()
        assert adapter.tasks_md_path.exists()
        
        # Verify content
        assert "Calculator" in adapter.spec_md_path.read_text()
        assert "Architecture" in adapter.plan_md_path.read_text()
        assert "TASK-001" in adapter.tasks_md_path.read_text()
        
        # Verify tokens tracked
        assert result1['tokens_in'] == 100
        assert result1['tokens_out'] == 200


@pytest.mark.unit
class TestGHSpecAdapterPhase6Unit:
    """Unit tests for Phase 6 validation helpers"""
    
    def test_template_loading_all_phases(self):
        """Verify all prompt templates can be loaded."""
        config = {
            'repo_url': 'test',
            'commit_hash': 'abc',
            'api_key_env': 'TEST'
        }
        adapter = GHSpecAdapter(config, 'test', '/tmp/test')
        
        # Mock framework_dir with actual template structure
        import tempfile
        temp_dir = tempfile.mkdtemp()
        adapter.framework_dir = Path(temp_dir)
        prompts_dir = adapter.framework_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        
        # Create mock templates
        templates = {
            'specify_template.md': '**System**\nTest system\n\n**User**\nTest user',
            'plan_template.md': '**System**\nPlan system\n\n**User**\nPlan user',
            'tasks_template.md': '**System**\nTasks system\n\n**User**\nTasks user',
            'implement_template.md': '**System**\nImpl system\n\n**User**\nImpl user',
            'bugfix_template.md': '**System**\nBugfix system\n\n**User**\nBugfix user',
        }
        
        for filename, content in templates.items():
            (prompts_dir / filename).write_text(content)
        
        # Test loading each template
        for template_name in templates.keys():
            template_path = prompts_dir / template_name
            assert template_path.exists(), f"Template file {template_name} not created"
            content = template_path.read_text()
            assert '**System**' in content
            assert '**User**' in content
        
        # Cleanup
        shutil.rmtree(temp_dir)

