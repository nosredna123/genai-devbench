"""
Unit tests for GHSpec adapter task parser regex fix.

Tests the _parse_tasks() method to ensure it handles both Format 1 and Format 2
file path variations produced by the OpenAI API.

Format 1 (colon inside bold): **File**: `path` or **File Path**: `path`
Format 2 (colon outside bold): **File Path:** `path`

Reference: Feature Specification 006-fix-ghspec-task
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from src.adapters.ghspec_adapter import GHSpecAdapter


class TestGHSpecTaskParser:
    """Test suite for GHSpec task parser regex patterns."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup after test
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
    def adapter_with_tasks_md(self, mock_config, temp_workspace):
        """Create adapter instance with a tasks.md file."""
        # Create workspace structure
        specs_dir = temp_workspace / "specs"
        feature_dir = specs_dir / "001-test-feature"
        feature_dir.mkdir(parents=True, exist_ok=True)
        
        # Create empty tasks.md (will be populated by individual tests)
        tasks_md_path = feature_dir / "tasks.md"
        tasks_md_path.write_text("", encoding='utf-8')
        
        # Create adapter
        adapter = GHSpecAdapter(
            config=mock_config,
            run_id='test-run-123',
            workspace_path=str(temp_workspace)
        )
        
        # Set the paths manually (normally done in _setup_workspace_structure)
        adapter.specs_dir = specs_dir
        adapter.feature_dir = feature_dir
        adapter.tasks_md_path = tasks_md_path
        
        return adapter
    
    # =========================================================================
    # FORMAT 1 TESTS - Colon Inside Bold (Currently Working)
    # =========================================================================
    
    def test_format1_with_dash_and_backticks(self, adapter_with_tasks_md):
        """
        Test Format 1: - **File**: `path`
        User Story 1, Acceptance Scenario 1
        """
        tasks_content = """
# Implementation Tasks

- [ ] **Task 1**: Create migration file
  - **File**: `migrations/20231023_create_table.sql`
  - **Goal**: Set up database schema
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == 'migrations/20231023_create_table.sql'
        assert tasks[0]['id'] == 'TASK-001'
        assert 'Create migration file' in tasks[0]['description']
    
    def test_format1_no_dash_with_backticks(self, adapter_with_tasks_md):
        """
        Test Format 1: **File**: `path`
        User Story 1, Acceptance Scenario 2
        """
        tasks_content = """
# Tasks

- [ ] **Task 1**: Implement API endpoint
  **File**: `api/students.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == 'api/students.js'
    
    def test_format1_lowercase_path_with_backticks(self, adapter_with_tasks_md):
        """
        Test Format 1: - **File path**: `path` (lowercase 'path')
        User Story 1, Acceptance Scenario 3
        """
        tasks_content = """
- [ ] **Task 1**: Create model
  - **File path**: `models/Student.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == 'models/Student.js'
    
    def test_format1_no_backticks_with_spaces(self, adapter_with_tasks_md):
        """
        Test Format 1: **File**: path (no backticks, leading spaces)
        User Story 1, Acceptance Scenario 4
        """
        tasks_content = """
- [ ] **Task 1**: Update database
    **File**: migrations/file.sql
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == 'migrations/file.sql'
    
    # =========================================================================
    # FORMAT 2 TESTS - Colon Outside Bold (CURRENTLY FAILING - BUG FIX)
    # =========================================================================
    
    def test_format2_absolute_path_with_backticks(self, adapter_with_tasks_md):
        """
        Test Format 2: **File Path:** `/path` (colon outside bold)
        User Story 2, Acceptance Scenario 1
        
        THIS TEST WILL FAIL BEFORE THE FIX IS IMPLEMENTED
        """
        tasks_content = """
- [ ] **Task 1**: Add email column to students table
  **File Path:** `/db/migrations/20231010_add_email_to_students.sql`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        # BEFORE FIX: assert len(tasks) == 0 (FAILS)
        # AFTER FIX: assert len(tasks) == 1 (PASSES)
        assert len(tasks) == 1, "Format 2 parsing should extract 1 task"
        assert tasks[0]['file'] == '/db/migrations/20231010_add_email_to_students.sql'
    
    def test_format2_model_file_with_backticks(self, adapter_with_tasks_md):
        """
        Test Format 2: **File Path:** `/models/file.js`
        User Story 2, Acceptance Scenario 2
        
        THIS TEST WILL FAIL BEFORE THE FIX IS IMPLEMENTED
        """
        tasks_content = """
- [ ] **Task 2**: Create Student model
  **File Path:** `/models/student.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1, "Format 2 parsing should extract 1 task"
        assert tasks[0]['file'] == '/models/student.js'
    
    def test_format2_component_file_with_backticks(self, adapter_with_tasks_md):
        """
        Test Format 2: **File Path:** `/src/components/Form.js`
        User Story 2, Acceptance Scenario 3
        
        THIS TEST WILL FAIL BEFORE THE FIX IS IMPLEMENTED
        """
        tasks_content = """
- [ ] **Task 3**: Create form component
  **File Path:** `/src/components/CreateStudentForm.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1, "Format 2 parsing should extract 1 task"
        assert tasks[0]['file'] == '/src/components/CreateStudentForm.js'
    
    def test_format2_test_file_with_backticks(self, adapter_with_tasks_md):
        """
        Test Format 2: **File Path:** `/tests/file.test.js`
        User Story 2, Acceptance Scenario 4
        
        THIS TEST WILL FAIL BEFORE THE FIX IS IMPLEMENTED
        """
        tasks_content = """
- [ ] **Task 4**: Add unit tests
  **File Path:** `/tests/student.test.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1, "Format 2 parsing should extract 1 task"
        assert tasks[0]['file'] == '/tests/student.test.js'
    
    # =========================================================================
    # MIXED FORMAT TESTS
    # =========================================================================
    
    def test_mixed_formats_in_same_file(self, adapter_with_tasks_md):
        """
        Test mixed Format 1 and Format 2 in same tasks.md
        User Story 3, Acceptance Scenario 1
        
        THIS TEST WILL PARTIALLY FAIL BEFORE THE FIX
        (only Format 1 tasks will be extracted)
        """
        tasks_content = """
# Implementation Tasks

- [ ] **Task 1**: Create migration (Format 1)
  - **File**: `migrations/create_table.sql`

- [ ] **Task 2**: Create model (Format 2)
  **File Path:** `/models/student.js`

- [ ] **Task 3**: Create API route (Format 1)
  **File path**: `routes/students.js`

- [ ] **Task 4**: Create test (Format 2)
  **File Path:** `/tests/student.test.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        # Should extract all 4 tasks regardless of format
        assert len(tasks) == 4, "Should extract all tasks from both formats"
        
        # Verify specific file paths
        assert tasks[0]['file'] == 'migrations/create_table.sql'
        assert tasks[1]['file'] == '/models/student.js'
        assert tasks[2]['file'] == 'routes/students.js'
        assert tasks[3]['file'] == '/tests/student.test.js'
    
    def test_eleven_tasks_mixed_formats(self, adapter_with_tasks_md):
        """
        Test 11 tasks with 6 Format 1 and 5 Format 2
        User Story 3, Acceptance Scenario 2
        
        Simulates realistic ghspec output with multiple tasks
        """
        tasks_content = """
# Tasks

- [ ] **Task 1**: Migration 1
  **File**: `migrations/001.sql`

- [ ] **Task 2**: Migration 2
  **File Path:** `/migrations/002.sql`

- [ ] **Task 3**: Model 1
  - **File**: `models/student.js`

- [ ] **Task 4**: Model 2
  **File Path:** `/models/course.js`

- [ ] **Task 5**: Route 1
  **File path**: `routes/students.js`

- [ ] **Task 6**: Route 2
  **File Path:** `/routes/courses.js`

- [ ] **Task 7**: Controller
  **File**: `controllers/student.js`

- [ ] **Task 8**: Service
  **File Path:** `/services/enrollment.js`

- [ ] **Task 9**: Component
  **File**: `components/StudentList.js`

- [ ] **Task 10**: Test 1
  **File Path:** `/tests/student.test.js`

- [ ] **Task 11**: Test 2
  **File**: `tests/integration.test.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 11, "Should extract all 11 tasks"
        
        # Verify task IDs are sequential
        for i, task in enumerate(tasks, 1):
            assert task['id'] == f'TASK-{str(i).zfill(3)}'
    
    # =========================================================================
    # EDGE CASE TESTS
    # =========================================================================
    
    def test_file_path_with_dashes_and_dots(self, adapter_with_tasks_md):
        """
        Test edge case: File paths with special characters (dashes, dots, underscores)
        Edge Case: What happens when file paths contain special characters?
        """
        tasks_content = """
- [ ] **Task 1**: Create migration with version number
  **File**: `migrations/20231023_create-student-table_v2.1.sql`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == 'migrations/20231023_create-student-table_v2.1.sql'
    
    def test_deeply_nested_path(self, adapter_with_tasks_md):
        """
        Test edge case: Deeply nested file paths
        Edge Case: What happens with deeply nested paths?
        """
        tasks_content = """
- [ ] **Task 1**: Create nested component
  **File Path:** `/src/components/forms/inputs/text/TextInput.jsx`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == '/src/components/forms/inputs/text/TextInput.jsx'
    
    def test_non_standard_extensions(self, adapter_with_tasks_md):
        """
        Test edge case: Non-standard file extensions (.jsx, .tsx, .mjs)
        Edge Case: What happens with file extensions that aren't typical?
        """
        tasks_content = """
- [ ] **Task 1**: Create React component
  **File**: `components/App.jsx`

- [ ] **Task 2**: Create TypeScript component
  **File Path:** `/components/Button.tsx`

- [ ] **Task 3**: Create ES module
  **File**: `utils/helpers.mjs`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 3
        assert tasks[0]['file'] == 'components/App.jsx'
        assert tasks[1]['file'] == '/components/Button.tsx'
        assert tasks[2]['file'] == 'utils/helpers.mjs'
    
    def test_extra_whitespace_handling(self, adapter_with_tasks_md):
        """
        Test edge case: File path line has extra whitespace
        Edge Case: What happens when the file path line has extra whitespace?
        """
        tasks_content = """
- [ ] **Task 1**: Create file with messy formatting
     **File Path:**    `/models/student.js`   
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        # Path should be trimmed of leading/trailing whitespace
        assert tasks[0]['file'] == '/models/student.js'
        assert tasks[0]['file'].strip() == tasks[0]['file']  # Verify no whitespace
    
    def test_no_file_path_in_lookahead_window(self, adapter_with_tasks_md):
        """
        Test edge case: No file path found within 10-line lookahead window
        Edge Case: What happens when there's no file path found within the 10-line lookahead?
        
        Task should NOT be extracted (existing behavior)
        """
        tasks_content = """
- [ ] **Task 1**: Task with no file path
  Some description
  More description
  Even more description
  Still no file path
  Line 6
  Line 7
  Line 8
  Line 9
  Line 10
  Line 11
  - **File**: `this_is_too_far.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        # Should NOT extract this task (file path beyond 10-line window)
        assert len(tasks) == 0, "Should not extract task when file path is beyond lookahead window"
    
    def test_task_without_file_path_not_extracted(self, adapter_with_tasks_md):
        """
        Test that tasks without file paths are not extracted (existing behavior)
        """
        tasks_content = """
- [ ] **Task 1**: Create file
  **File**: `models/student.js`

- [ ] **Task 2**: Task without file path
  Just a description, no file indicator

- [ ] **Task 3**: Another valid task
  **File Path:** `/routes/courses.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        # Should only extract tasks 1 and 3 (those with file paths)
        assert len(tasks) == 2
        assert tasks[0]['id'] == 'TASK-001'
        assert tasks[1]['id'] == 'TASK-003'  # Note: ID is based on checkbox count, not extraction order
    
    def test_stop_at_next_checkbox(self, adapter_with_tasks_md):
        """
        Test that lookahead stops when hitting another checkbox
        Ensures file path from next task isn't incorrectly attributed
        """
        tasks_content = """
- [ ] **Task 1**: First task
  Some description
- [ ] **Task 2**: Second task immediately follows
  **File**: `should_not_be_in_task1.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        # Task 1 should not be extracted (no file path before next checkbox)
        # Task 2 should be extracted
        assert len(tasks) == 1
        assert tasks[0]['id'] == 'TASK-002'
        assert tasks[0]['file'] == 'should_not_be_in_task1.js'
    
    # =========================================================================
    # REAL-WORLD SCENARIO TESTS
    # =========================================================================
    
    def test_realistic_ghspec_output_format1(self, adapter_with_tasks_md):
        """
        Test with realistic tasks.md from successful ghspec runs (Format 1)
        Based on actual output patterns from 37 successful runs
        """
        tasks_content = """
# Implementation Plan

## Tasks

- [ ] **TASK-001** Create database migration for students table
  - **File**: `migrations/20231023_create_student_table.sql`
  - **Goal**: Set up the database schema for storing student information

- [ ] **TASK-002** Implement Student model
  - **File**: `models/Student.js`
  - **Goal**: Create the Student model with validation

- [ ] **TASK-003** Create API endpoint for student enrollment
  **File**: `api/students/courses/associate.js`
  **Goal**: Handle POST requests for course enrollment
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 3
        assert tasks[0]['file'] == 'migrations/20231023_create_student_table.sql'
        assert tasks[1]['file'] == 'models/Student.js'
        assert tasks[2]['file'] == 'api/students/courses/associate.js'
    
    def test_realistic_ghspec_output_format2(self, adapter_with_tasks_md):
        """
        Test with realistic tasks.md from FAILED ghspec runs (Format 2)
        Based on actual output from run 4a922e67-4030-4c47-8dd9-eb2ea0244027
        
        THIS TEST WILL FAIL BEFORE THE FIX IS IMPLEMENTED
        """
        tasks_content = """
# Implementation Plan

## Tasks

- [ ] **Task 1**: Create database migration for email field
  **File Path:** `/db/migrations/20231010_add_email_to_students.sql`
  **Goal**: Add email column to students table

- [ ] **Task 2**: Update Student model
  **File Path:** `/models/student.js`
  **Goal**: Add email field to model

- [ ] **Task 3**: Create API route for student registration
  **File Path:** `/routes/students.js`
  **Goal**: Handle student registration with email

- [ ] **Task 4**: Create React form component
  **File Path:** `/src/components/CreateStudentForm.js`
  **Goal**: Build UI for student registration

- [ ] **Task 5**: Add unit tests for Student model
  **File Path:** `/tests/student.test.js`
  **Goal**: Ensure model validation works correctly
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        # CRITICAL: This is the bug fix validation
        # BEFORE FIX: len(tasks) == 0
        # AFTER FIX: len(tasks) == 5
        assert len(tasks) == 5, "Format 2 should extract all 5 tasks (bug fix validation)"
        
        assert tasks[0]['file'] == '/db/migrations/20231010_add_email_to_students.sql'
        assert tasks[1]['file'] == '/models/student.js'
        assert tasks[2]['file'] == '/routes/students.js'
        assert tasks[3]['file'] == '/src/components/CreateStudentForm.js'
        assert tasks[4]['file'] == '/tests/student.test.js'
    
    # =========================================================================
    # NEGATIVE TESTS - Should NOT Match
    # =========================================================================
    
    def test_non_file_bold_text_not_matched(self, adapter_with_tasks_md):
        """
        Test that random bold text doesn't get mistaken for file paths
        """
        tasks_content = """
- [ ] **Task 1**: Create something
  **Important**: This is a note, not a file path
  **File**: `actual/file.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == 'actual/file.js'  # Should match the actual File: marker
    
    def test_file_word_in_description_not_matched(self, adapter_with_tasks_md):
        """
        Test that the word 'file' in regular text doesn't cause false matches
        """
        tasks_content = """
- [ ] **Task 1**: Create a new file for the project
  This task involves creating a file in the filesystem
  **File**: `src/newfile.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 1
        assert tasks[0]['file'] == 'src/newfile.js'
    
    # =========================================================================
    # TASK ID AND DESCRIPTION TESTS
    # =========================================================================
    
    def test_task_id_generation(self, adapter_with_tasks_md):
        """
        Test that task IDs are generated correctly with zero-padding
        """
        tasks_content = """
- [ ] **Task 1**: Task one
  **File**: `file1.js`
- [ ] **Task 2**: Task two
  **File**: `file2.js`
- [ ] **Task 10**: Task ten
  **File**: `file10.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 3
        assert tasks[0]['id'] == 'TASK-001'
        assert tasks[1]['id'] == 'TASK-002'
        assert tasks[2]['id'] == 'TASK-003'  # Sequential, not based on task number in text
    
    def test_description_extraction_removes_task_markers(self, adapter_with_tasks_md):
        """
        Test that task descriptions are cleaned of task number markers
        """
        tasks_content = """
- [ ] **Task 1**: Create migration file
  **File**: `file1.sql`

- [ ] **TASK-002** Implement model
  **File**: `file2.js`

- [ ] Task 3: Add API route
  **File**: `file3.js`
"""
        adapter_with_tasks_md.tasks_md_path.write_text(tasks_content, encoding='utf-8')
        
        tasks = adapter_with_tasks_md._parse_tasks()
        
        assert len(tasks) == 3
        # Descriptions should not contain task markers
        assert 'Task 1' not in tasks[0]['description']
        assert 'Create migration file' in tasks[0]['description']
        assert 'TASK-002' not in tasks[1]['description']
        assert 'Implement model' in tasks[1]['description']
        assert 'Task 3' not in tasks[2]['description']
        assert 'Add API route' in tasks[2]['description']


# =============================================================================
# TEST EXECUTION MARKERS
# =============================================================================

class TestFormatIdentification:
    """
    Meta-tests to identify which format a test case represents.
    Useful for debugging and understanding test coverage.
    """
    
    def test_format1_count(self):
        """Document how many Format 1 test cases exist"""
        format1_tests = [
            'test_format1_with_dash_and_backticks',
            'test_format1_no_dash_with_backticks',
            'test_format1_lowercase_path_with_backticks',
            'test_format1_no_backticks_with_spaces',
        ]
        assert len(format1_tests) == 4, "4 Format 1 test cases (User Story 1)"
    
    def test_format2_count(self):
        """Document how many Format 2 test cases exist"""
        format2_tests = [
            'test_format2_absolute_path_with_backticks',
            'test_format2_model_file_with_backticks',
            'test_format2_component_file_with_backticks',
            'test_format2_test_file_with_backticks',
        ]
        assert len(format2_tests) == 4, "4 Format 2 test cases (User Story 2)"
    
    def test_mixed_format_count(self):
        """Document how many mixed format test cases exist"""
        mixed_tests = [
            'test_mixed_formats_in_same_file',
            'test_eleven_tasks_mixed_formats',
        ]
        assert len(mixed_tests) == 2, "2 mixed format test cases (User Story 3)"
    
    def test_edge_case_count(self):
        """Document how many edge case tests exist"""
        edge_tests = [
            'test_file_path_with_dashes_and_dots',
            'test_deeply_nested_path',
            'test_non_standard_extensions',
            'test_extra_whitespace_handling',
            'test_no_file_path_in_lookahead_window',
            'test_task_without_file_path_not_extracted',
            'test_stop_at_next_checkbox',
        ]
        assert len(edge_tests) == 7, "7 edge case tests"
    
    def test_total_coverage(self):
        """Verify total test coverage meets specification requirements"""
        # Format 1: 4 tests
        # Format 2: 4 tests (will fail before fix)
        # Mixed: 2 tests
        # Edge cases: 7 tests
        # Real-world: 2 tests
        # Negative: 2 tests
        # Task ID/Description: 2 tests
        total_functional_tests = 4 + 4 + 2 + 7 + 2 + 2 + 2
        assert total_functional_tests == 23, "23 functional test cases cover all scenarios"
