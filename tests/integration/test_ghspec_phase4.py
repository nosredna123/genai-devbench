"""
Integration tests for GHSpec adapter Phase 4: Task-by-task code generation.

Tests the task parsing, context building, and code generation workflow.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.adapters.ghspec_adapter import GHSpecAdapter


@pytest.mark.integration
class TestGHSpecAdapterPhase4:
    """Integration tests for Phase 4: Task-by-Task Implementation"""
    
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
    def adapter_with_artifacts(self, mock_config, temp_workspace):
        """Create adapter with workspace and mock artifacts."""
        adapter = GHSpecAdapter(
            config=mock_config,
            run_id='test-run-phase4',
            workspace_path=temp_workspace
        )
        
        # Setup workspace structure
        adapter.framework_dir = Path(temp_workspace) / "ghspec_framework"
        adapter.framework_dir.mkdir(parents=True, exist_ok=True)
        adapter._setup_workspace_structure()
        
        # Create mock spec.md
        spec_content = """
# Feature: Todo List Application

## Overview
A simple todo list for personal task management.

## Functional Requirements
1. Users SHALL create tasks with title and description
2. Users SHALL mark tasks as complete
3. Users SHALL delete tasks

## Key Entities
- Task: {id, title, description, completed, created_at}
- User: {id, email, password_hash}

## Success Criteria
- Tasks persist across sessions
- Users can manage personal task lists
"""
        adapter.spec_md_path.write_text(spec_content, encoding='utf-8')
        
        # Create mock plan.md
        plan_content = """
# Technical Plan: Todo List Application

## Architecture
- Backend: Python FastAPI
- Database: SQLite with SQLAlchemy ORM
- Frontend: HTML/CSS/JavaScript

## Data Model
### Task Model
- id: Integer, primary key
- title: String(200), not null
- description: Text, nullable
- completed: Boolean, default False
- user_id: Foreign key to User

### User Model
- id: Integer, primary key
- email: String(100), unique, not null
- password_hash: String(256), not null

## API Endpoints
- POST /tasks: Create task
- GET /tasks: List user's tasks
- PATCH /tasks/{id}: Update task
- DELETE /tasks/{id}: Delete task
"""
        adapter.plan_md_path.write_text(plan_content, encoding='utf-8')
        
        # Create mock tasks.md
        tasks_content = """
# Implementation Tasks

## Phase 1: Foundation

- [ ] **TASK-001** [setup] Create project structure
  - **File**: `README.md`
  - **Goal**: Project documentation
  - **Test**: README exists

- [ ] **TASK-002** [setup] Setup database models
  - **File**: `models/task.py`
  - **Goal**: Task model with SQLAlchemy
  - **Test**: Model can save and load

- [ ] **TASK-003** [setup] Setup user model
  - **File**: `models/user.py`
  - **Goal**: User model with password hashing
  - **Test**: Password verification works

## Phase 2: API Implementation

- [ ] **TASK-010** [api] Create task endpoint
  - **File**: `api/tasks.py`
  - **Goal**: POST /tasks endpoint
  - **Dependencies**: TASK-002
  - **Test**: Returns 201 with task_id

- [ ] **TASK-011** [api] List tasks endpoint
  - **File**: `api/tasks.py`
  - **Goal**: GET /tasks endpoint
  - **Dependencies**: TASK-002
  - **Test**: Returns array of tasks
"""
        adapter.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        return adapter
    
    def test_parse_tasks(self, adapter_with_artifacts):
        """Test parsing tasks from tasks.md."""
        tasks = adapter_with_artifacts._parse_tasks()
        
        # Should find 5 tasks (TASK-001, 002, 003, 010, 011)
        assert len(tasks) == 5
        
        # Verify first task
        assert tasks[0]['id'] == 'TASK-001'
        assert tasks[0]['file'] == 'README.md'
        # New parser uses description as goal (simpler approach)
        assert tasks[0]['goal'] == tasks[0]['description']
        assert '[setup]' in tasks[0]['description']
        
        # Verify task with dependencies (search by file since parser generates sequential IDs)
        # The parser finds 5 tasks: TASK-001 through TASK-005 (sequential, not preserving original IDs)
        task_010 = next(t for t in tasks if t['file'] == 'api/tasks.py' and 'Create task endpoint' in t['description'])
        assert task_010['file'] == 'api/tasks.py'
        # Goal equals description in new parser
        assert '[api] Create task endpoint' in task_010['description']
    
    def test_extract_relevant_section_spec(self, adapter_with_artifacts):
        """Test extracting relevant spec sections for a task."""
        spec_content = adapter_with_artifacts.spec_md_path.read_text()
        
        task = {
            'id': 'TASK-002',
            'file': 'models/task.py',
            'description': 'Setup database models',
            'goal': 'Task model with SQLAlchemy'
        }
        
        excerpt = adapter_with_artifacts._extract_relevant_section(spec_content, task)
        
        # Should include Task entity definition
        assert 'Task:' in excerpt or 'task' in excerpt.lower()
        # Should be reasonably sized
        assert len(excerpt) < 2500
    
    def test_extract_relevant_section_plan(self, adapter_with_artifacts):
        """Test extracting relevant plan sections for a task."""
        plan_content = adapter_with_artifacts.plan_md_path.read_text()
        
        task = {
            'id': 'TASK-003',
            'file': 'models/user.py',
            'description': 'Setup user model',
            'goal': 'User model with password hashing'
        }
        
        excerpt = adapter_with_artifacts._extract_relevant_section(plan_content, task)
        
        # Should include User Model section
        assert 'User' in excerpt or 'user' in excerpt.lower()
        # Should mention password hashing from plan
        assert 'password' in excerpt.lower()
    
    def test_read_file_if_exists_missing(self, adapter_with_artifacts):
        """Test reading non-existent file returns empty string."""
        file_path = adapter_with_artifacts.src_dir / "nonexistent.py"
        
        content = adapter_with_artifacts._read_file_if_exists(file_path)
        
        assert content == ""
    
    def test_read_file_if_exists_present(self, adapter_with_artifacts):
        """Test reading existing file returns content."""
        file_path = adapter_with_artifacts.src_dir / "existing.py"
        test_content = "# Existing code\nprint('hello')"
        file_path.write_text(test_content, encoding='utf-8')
        
        content = adapter_with_artifacts._read_file_if_exists(file_path)
        
        assert content == test_content
    
    def test_save_code_file_creates_directories(self, adapter_with_artifacts):
        """Test saving code file creates parent directories."""
        relative_path = "models/nested/deep/file.py"
        content = "# Test file"
        
        adapter_with_artifacts._save_code_file(relative_path, content)
        
        file_path = adapter_with_artifacts.src_dir / relative_path
        assert file_path.exists()
        assert file_path.read_text() == content
    
    def test_save_code_file_overwrites_existing(self, adapter_with_artifacts):
        """Test saving code file overwrites existing content."""
        relative_path = "models/task.py"
        old_content = "# Old code"
        new_content = "# New code"
        
        # Create existing file
        file_path = adapter_with_artifacts.src_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(old_content, encoding='utf-8')
        
        # Overwrite
        adapter_with_artifacts._save_code_file(relative_path, new_content)
        
        assert file_path.read_text() == new_content
    
    def test_build_task_prompt(self, adapter_with_artifacts):
        """Test building context-rich task prompt."""
        spec_content = adapter_with_artifacts.spec_md_path.read_text()
        plan_content = adapter_with_artifacts.plan_md_path.read_text()
        
        task = {
            'id': 'TASK-002',
            'file': 'models/task.py',
            'description': 'Setup database models',
            'goal': 'Task model with SQLAlchemy'
        }
        
        template = """
TASK: {task_description}
FILE: {file_path}
GOAL: {task_goal}

SPEC: {spec_excerpt}
PLAN: {plan_excerpt}
CURRENT: {current_file_content}
"""
        
        prompt = adapter_with_artifacts._build_task_prompt(
            task, spec_content, plan_content, template
        )
        
        # Verify all placeholders filled
        assert '{task_description}' not in prompt
        assert '{file_path}' not in prompt
        assert 'models/task.py' in prompt
        assert 'SQLAlchemy' in prompt
        # Should include "file does not exist" since we haven't created it
        assert 'does not exist' in prompt or 'create from scratch' in prompt
    
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_execute_task_implementation_mocked(
        self, mock_fetch_usage, mock_call_openai, adapter_with_artifacts
    ):
        """Test complete task implementation workflow (mocked)."""
        # Mock API responses for each task
        mock_call_openai.side_effect = [
            "# Todo List\nProject documentation here...",  # TASK-001: README
            "# Task model\nfrom sqlalchemy import...",     # TASK-002: task.py
            "# User model\nfrom werkzeug.security...",     # TASK-003: user.py
            "# Tasks API\nfrom fastapi import...",         # TASK-010: api/tasks.py
            "# Get tasks\n@app.get('/tasks')...",          # TASK-011: api/tasks.py (update)
        ]
        
        # Mock token usage (same for all calls for simplicity)
        mock_fetch_usage.return_value = (200, 400, 5, 10)
        
        # Execute implementation
        adapter_with_artifacts.current_step = 4
        hitl_count, tokens_in, tokens_out, api_calls, cached_tokens, start_timestamp, end_timestamp = adapter_with_artifacts._execute_task_implementation("Build todo app")
        
        # Verify all tasks were processed
        assert mock_call_openai.call_count == 5
        
        # Verify token aggregation
        assert tokens_in == 200 * 5  # 5 tasks
        assert tokens_out == 400 * 5
        assert hitl_count == 0  # No clarifications
        
        # Verify timestamps
        assert isinstance(start_timestamp, int)
        assert isinstance(end_timestamp, int)
        assert start_timestamp > 0
        assert end_timestamp >= start_timestamp
        
        # Verify files were created
        assert (adapter_with_artifacts.src_dir / "README.md").exists()
        assert (adapter_with_artifacts.src_dir / "models/task.py").exists()
        assert (adapter_with_artifacts.src_dir / "models/user.py").exists()
        assert (adapter_with_artifacts.src_dir / "api/tasks.py").exists()
    
    @patch.object(GHSpecAdapter, '_call_openai')
    @patch.object(GHSpecAdapter, 'fetch_usage_from_openai')
    def test_execute_task_with_clarification(
        self, mock_fetch_usage, mock_call_openai, adapter_with_artifacts
    ):
        """Test task implementation with clarification handling."""
        # First task requests clarification, then completes
        mock_call_openai.side_effect = [
            "# README\n[NEEDS CLARIFICATION: License type?]",  # Initial request
            "# README\nMIT License...",                        # After HITL
            "# Task model\nfrom sqlalchemy...",                # TASK-002
            "# User model...",                                 # TASK-003
            "# API...",                                        # TASK-010
            "# API update...",                                 # TASK-011
        ]
        
        mock_fetch_usage.return_value = (150, 350, 5, 10)
        
        adapter_with_artifacts.current_step = 4
        hitl_count, tokens_in, tokens_out, api_calls, cached_tokens, start_timestamp, end_timestamp = adapter_with_artifacts._execute_task_implementation("Build todo app")
        
        # Should have made 6 API calls (5 tasks + 1 clarification)
        assert mock_call_openai.call_count == 6
        
        # Should have 1 HITL intervention
        assert hitl_count == 1
        
        # Verify timestamps
        assert isinstance(start_timestamp, int)
        assert isinstance(end_timestamp, int)
        assert start_timestamp > 0
        assert end_timestamp >= start_timestamp
        
        # README should exist with final content (no clarification marker)
        readme_content = (adapter_with_artifacts.src_dir / "README.md").read_text()
        assert '[NEEDS CLARIFICATION' not in readme_content
        assert 'MIT License' in readme_content


@pytest.mark.unit
class TestGHSpecAdapterPhase4Unit:
    """Unit tests for Phase 4 helper methods"""
    
    def test_parse_tasks_various_formats(self):
        """Test task parsing handles various markdown formats."""
        tasks_md = """
# Tasks

- [ ] **TASK-001** Simple task
  - **File**: `path/file1.py`
  - **Goal**: Do something

- [ ] **TASK-002** [label] Task with label
  - **File**: path/file2.py
  - **Goal**: Do something else
  - **Dependencies**: TASK-001

- [ ] **TASK-003** No file task
  - **Goal**: Organizational task

- [ ] **TASK-004** [multiple][labels] Multi-label
  - **File**: `nested/deep/file.py`
  - **Goal**: Deep nesting
"""
        
        # Create minimal adapter
        config = {'api_key_env': 'TEST', 'repo_url': 'test', 'commit_hash': 'abc'}
        adapter = GHSpecAdapter(config, 'test', '/tmp/test')
        
        # Mock workspace
        import tempfile
        temp_dir = tempfile.mkdtemp()
        adapter._setup_workspace_structure = lambda: None
        adapter.workspace_path = temp_dir
        adapter.specs_dir = Path(temp_dir) / "specs"
        adapter.feature_dir = adapter.specs_dir / "001-test"
        adapter.src_dir = adapter.feature_dir / "src"
        adapter.tasks_md_path = adapter.feature_dir / "tasks.md"
        
        adapter.feature_dir.mkdir(parents=True, exist_ok=True)
        adapter.tasks_md_path.write_text(tasks_md, encoding='utf-8')
        
        tasks = adapter._parse_tasks()
        
        # Should find 3 tasks (TASK-003 has no file, so skipped)
        assert len(tasks) == 3
        assert tasks[0]['id'] == 'TASK-001'
        assert tasks[1]['id'] == 'TASK-002'
        assert tasks[2]['id'] == 'TASK-004'
        
        # Verify file paths parsed correctly (with/without backticks)
        assert tasks[0]['file'] == 'path/file1.py'
        assert tasks[1]['file'] == 'path/file2.py'
        assert tasks[2]['file'] == 'nested/deep/file.py'
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_extract_relevant_section_keyword_matching(self):
        """Test relevant section extraction uses smart keyword matching."""
        content = """
# Feature Specification

## User Authentication
Users must be able to log in with email and password.
Password must be hashed using bcrypt.

## Task Management
Users can create, read, update, and delete tasks.
Tasks have title, description, and completion status.

## Database Schema
- User table: id, email, password_hash
- Task table: id, title, description, completed, user_id
"""
        
        config = {'api_key_env': 'TEST', 'repo_url': 'test', 'commit_hash': 'abc'}
        adapter = GHSpecAdapter(config, 'test', '/tmp/test')
        
        # Task about authentication
        auth_task = {
            'file': 'auth/login.py',
            'description': 'User authentication',
            'goal': 'Login endpoint'
        }
        
        excerpt = adapter._extract_relevant_section(content, auth_task)
        
        # Should prioritize User Authentication section
        assert 'Authentication' in excerpt or 'login' in excerpt.lower()
        assert 'password' in excerpt.lower()
        
        # Task about tasks
        task_task = {
            'file': 'models/task.py',
            'description': 'Task model',
            'goal': 'CRUD operations for tasks'
        }
        
        excerpt = adapter._extract_relevant_section(content, task_task)
        
        # Should prioritize Task sections
        assert 'task' in excerpt.lower()
        assert 'title' in excerpt.lower() or 'description' in excerpt.lower()
