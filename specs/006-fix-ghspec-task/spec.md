# Feature Specification: GHSpec Task Parser Regex Fix

**Feature Branch**: `006-fix-ghspec-task`  
**Created**: October 27, 2025  
**Status**: Draft  
**Input**: User description: "Fix GHSpec task parser regex to handle AI-generated file path format variations"

## Executive Summary

The GHSpec adapter's task parser currently fails to extract file paths from 92.3% of failed runs (12 out of 13 failures) due to a regex pattern that cannot handle format variations produced by the OpenAI API. This causes complete data loss for affected runs, including metrics, token usage, and execution records. The fix will enable the parser to handle both format variations, improving the success rate from 74% to ~98% and eliminating 8.7% data loss across experiments.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Task File Path Extraction from Format 1 (Priority: P1)

When the OpenAI API generates tasks.md files with file paths using Format 1 (colon inside bold markers like `**File**: path`), the system must successfully extract all file paths and process the tasks to completion.

**Why this priority**: This is the currently working format that accounts for 74% of successful runs. We must ensure the fix doesn't break existing functionality.

**Independent Test**: Can be fully tested by providing a tasks.md file with Format 1 paths and verifying that all tasks are extracted, files are generated, and metrics.json is created.

**Acceptance Scenarios**:

1. **Given** a tasks.md file with `- **File**: migrations/file.sql`  
   **When** the parser processes the file  
   **Then** it extracts "migrations/file.sql" as the file path

2. **Given** a tasks.md file with `**File**: api/students.js`  
   **When** the parser processes the file  
   **Then** it extracts "api/students.js" as the file path

3. **Given** a tasks.md file with `- **File path**: models/Student.js` (lowercase)  
   **When** the parser processes the file  
   **Then** it extracts "models/Student.js" as the file path

4. **Given** a tasks.md file with `  **File**: migrations/file.sql` (no backticks)  
   **When** the parser processes the file  
   **Then** it extracts "migrations/file.sql" as the file path

---

### User Story 2 - Task File Path Extraction from Format 2 (Priority: P1)

When the OpenAI API generates tasks.md files with file paths using Format 2 (colon outside bold markers like `**File Path:** path`), the system must successfully extract all file paths and process the tasks to completion.

**Why this priority**: This is the failing format that causes 92.3% of ghspec failures and 8.7% total data loss. This is the primary bug fix.

**Independent Test**: Can be fully tested by providing a tasks.md file with Format 2 paths (previously failing format) and verifying that all tasks are extracted, files are generated, and metrics.json is created.

**Acceptance Scenarios**:

1. **Given** a tasks.md file with `  **File Path:** \`/db/migrations/file.sql\``  
   **When** the parser processes the file  
   **Then** it extracts "/db/migrations/file.sql" as the file path

2. **Given** a tasks.md file with `  **File Path:** \`/models/student.js\``  
   **When** the parser processes the file  
   **Then** it extracts "/models/student.js" as the file path

3. **Given** a tasks.md file with `**File Path:** \`/src/components/Form.js\``  
   **When** the parser processes the file  
   **Then** it extracts "/src/components/Form.js" as the file path

4. **Given** a tasks.md file with `**File Path:** \`/tests/student.test.js\``  
   **When** the parser processes the file  
   **Then** it extracts "/tests/student.test.js" as the file path

---

### User Story 3 - Mixed Format Handling (Priority: P2)

When a tasks.md file contains both Format 1 and Format 2 file paths in different tasks, the system must successfully extract all file paths regardless of format variation.

**Why this priority**: While less common, AI output can be inconsistent within a single file. This ensures robustness.

**Independent Test**: Can be fully tested by providing a tasks.md file with mixed formats and verifying that all tasks are extracted correctly.

**Acceptance Scenarios**:

1. **Given** a tasks.md file with both `**File**: path1.js` and `**File Path:** \`path2.js\``  
   **When** the parser processes the file  
   **Then** both file paths are extracted correctly

2. **Given** 11 tasks with 6 in Format 1 and 5 in Format 2  
   **When** the parser processes the file  
   **Then** all 11 tasks are extracted with correct file paths

---

### User Story 4 - End-to-End Run Completion (Priority: P1)

When a ghspec run executes with a tasks.md file in Format 2 (previously failing), the run must complete successfully, generate all artifact files, save metrics.json, and update manifest.json.

**Why this priority**: This validates that the regex fix resolves the complete failure chain, not just the parsing step.

**Independent Test**: Can be fully tested by re-running a previously failed ghspec experiment and verifying complete run artifacts are created.

**Acceptance Scenarios**:

1. **Given** a ghspec run with Format 2 tasks.md  
   **When** the run executes  
   **Then** all task files are generated in src/ directory

2. **Given** a ghspec run with Format 2 tasks.md  
   **When** the run completes  
   **Then** metrics.json exists with token usage and execution time

3. **Given** a previously failed run (e.g., 4a922e67-4030-4c47-8dd9-eb2ea0244027)  
   **When** re-executed with the fix  
   **Then** run status changes from "failed" to "success"

4. **Given** a ghspec run with Format 2 tasks.md  
   **When** the run completes  
   **Then** manifest.json contains an entry for the run

---

### Edge Cases

- What happens when file paths contain spaces (e.g., `path/to/my file.js`)?
- What happens when file paths contain special characters (e.g., `path/to/file-v2.1.js`)?
- What happens when the file path line has extra whitespace or trailing characters?
- What happens when there's no file path found within the 10-line lookahead window?
- What happens when backticks are mismatched (e.g., opening backtick but no closing)?
- What happens with deeply nested paths (e.g., `/src/components/forms/inputs/text.js`)?
- What happens with file extensions that aren't typical (e.g., `.jsx`, `.tsx`, `.mjs`)?
- What happens when both "File" and "File Path" appear in the same task block?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Parser MUST extract file paths from Format 1 patterns where colon is inside bold markers (`**File**: path` or `**File Path**: path`)

- **FR-002**: Parser MUST extract file paths from Format 2 patterns where colon is outside bold markers (`**File Path:** path`)

- **FR-003**: Parser MUST handle file paths with or without backtick wrapping (e.g., both `` `path` `` and `path`)

- **FR-004**: Parser MUST handle both relative paths (e.g., `models/Student.js`) and absolute paths (e.g., `/models/Student.js`)

- **FR-005**: Parser MUST handle case variations in "File" and "Path" keywords (e.g., `file`, `File`, `path`, `Path`)

- **FR-006**: Parser MUST extract file paths with leading/trailing whitespace correctly (trim the path)

- **FR-007**: Parser MUST handle file paths with special characters (dashes, underscores, dots, numbers)

- **FR-008**: Parser MUST preserve the existing lookahead behavior (scan next 10 lines after task checkbox)

- **FR-009**: Parser MUST preserve the existing task extraction behavior (only tasks with both description and file path)

- **FR-010**: Parser MUST log which format pattern was matched for monitoring and debugging purposes

- **FR-011**: System MUST process all extracted tasks through the existing task implementation pipeline

- **FR-012**: System MUST generate src/ directory files for all successfully extracted tasks

- **FR-013**: System MUST save metrics.json for runs where tasks are successfully extracted and processed

- **FR-014**: System MUST update manifest.json for runs where tasks are successfully extracted and processed

### Key Entities

- **Task**: Represents a single work item extracted from tasks.md
  - Attributes: id (string), description (string), file (string path), goal (string)
  - Must have both description and file path to be included in task list

- **File Path Pattern**: The regex pattern used to match file path indicators in tasks.md
  - Two primary formats: Format 1 (colon inside bold), Format 2 (colon outside bold)
  - Variations: with/without backticks, relative/absolute paths, case variations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Parser successfully extracts file paths from 100% of Format 1 test cases (currently at 100%, must maintain)

- **SC-002**: Parser successfully extracts file paths from 100% of Format 2 test cases (currently at 0%, must reach 100%)

- **SC-003**: GHSpec run success rate improves from 74% (37/50) to at least 98% (49/50)

- **SC-004**: Data loss rate decreases from 8.7% (13/150 runs) to less than 1% (fewer than 2/150 runs)

- **SC-005**: All 7 documented test case variations (both formats + edge cases) pass validation

- **SC-006**: Previously failed runs (e.g., run ID 4a922e67) succeed when re-executed with identical inputs

- **SC-007**: No regression in existing successful runs (all 37 previously successful runs continue to succeed)

- **SC-008**: 100% of runs with valid tasks.md files generate metrics.json (no data loss from parsing failures)

## Assumptions

- The AI will continue to generate tasks.md files with one of the two identified format patterns
- The tasks.md structure (checkbox + task description + file path) will remain consistent
- File paths in tasks.md will always be on a line within 10 lines after the task checkbox
- The existing task execution pipeline (_execute_task_implementation, _save_code_file) works correctly once tasks are parsed
- The validation logic (validate_artifacts_generated) correctly checks for generated files
- Only two primary format variations exist (no evidence of additional patterns in the 150-run dataset)

## Out of Scope

- Modifying the AI prompt to enforce a specific format (this is a parser robustness fix, not an AI output constraint)
- Handling formats other than the two documented patterns (unless discovered during testing)
- Refactoring the task parsing algorithm beyond the regex fix
- Changes to the task execution pipeline or file generation logic
- Changes to metrics collection or manifest update logic
- Implementing partial metrics saving on failure (separate enhancement)
- Removing sprint-level metrics redundancy (separate cleanup task)
- Handling malformed tasks.md files with invalid structure beyond format variations

## Dependencies

- The GHSpec adapter must have access to the tasks.md file at self.tasks_md_path
- The Python `re` module must support the regex patterns used in the fix
- The existing logger instance must be available for format detection logging
- The _execute_task_implementation() method must function correctly with extracted tasks
- The validate_artifacts_generated() method must accurately check for generated files

## Risks & Mitigation

**Risk 1**: New regex patterns might incorrectly match non-file-path lines

- *Mitigation*: Use strict patterns with explicit markers (\*\*, :, backticks) and test with real tasks.md files
- *Verification*: Run unit tests with positive and negative test cases

**Risk 2**: Fix might introduce regressions in currently working Format 1 parsing

- *Mitigation*: Test all Format 1 variations before and after the fix; use two-pattern approach to isolate changes
- *Verification*: Re-run all 37 previously successful experiments to ensure no regressions

**Risk 3**: AI might generate new format variations not covered by the fix

- *Mitigation*: Implement logging to detect matched formats; monitor logs for unknown patterns
- *Verification*: Add telemetry to track which pattern matched and alert on parse failures

**Risk 4**: Backtick handling might fail with escaped or nested backticks

- *Mitigation*: Use simple backtick matching ([^`]+) that stops at first closing backtick
- *Verification*: Test with real-world examples from existing runs

## Technical Context

This issue affects the GHSpec adapter, which is one of several framework adapters used in the BAES (Benchmarking Agent-Enabled Software Engineering) system. The adapter orchestrates AI-driven software development tasks by:

1. Generating a specification (spec.md)
2. Creating a plan (plan.md)
3. Breaking down into tasks (tasks.md)
4. Implementing each task by calling the OpenAI API
5. Saving generated code files to src/
6. Collecting metrics (token usage, execution time, API calls)
7. Saving metrics.json and updating manifest.json

The bug occurs at step 4-5: when tasks.md cannot be parsed correctly, zero tasks are extracted, leading to zero files generated, which triggers a validation error and prevents metrics from being saved.

The fix must be implemented in `/home/amg/projects/uece/baes/genai-devbench/src/adapters/ghspec_adapter.py` in the `_parse_tasks()` method around line 1015.

## Validation & Testing Strategy

1. **Unit Testing**: Create test cases for all 7 documented format variations
2. **Integration Testing**: Test with real tasks.md files from failed runs
3. **Regression Testing**: Re-run all 37 previously successful experiments
4. **End-to-End Testing**: Execute a complete ghspec run and verify all artifacts
5. **Monitoring**: Add format detection logging to track pattern usage in production
