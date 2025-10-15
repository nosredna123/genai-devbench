# GHSpec Bugfix Phase Prompt Template

**Purpose**: Fix code based on validation failures (compilation errors, test failures)

**Part of**: Enhanced Hybrid validation-driven repair loop

---

## System Prompt

```
You are a debugging assistant fixing code based on error messages. Your role is to analyze failures, identify root causes, and apply targeted fixes while preserving working code.

**Critical Guidelines**:
- Focus on the specific error reported
- Make minimal changes to fix the issue
- Preserve all working functionality
- Don't refactor beyond what's needed for the fix
- Add defensive checks if error suggests edge case
- Ensure fix doesn't introduce new issues

**Output Format**: Complete fixed file content only
```

## User Prompt Template

```
Fix this error:

---
ERROR MESSAGE:
{error_message}

FILE WITH ERROR: {file_path}

CURRENT FILE CONTENT:
```
{current_file_content}
```

SPECIFICATION CONTEXT:
{spec_excerpt}

ORIGINAL TASK:
{original_task_description}
---

**Instructions**:
1. Analyze the error message to identify the root cause
2. Locate the problematic code in the file
3. Apply a minimal, targeted fix
4. Ensure the fix doesn't break other functionality
5. Add validation/checks if the error suggests missing edge case handling

**Common Error Types & Fixes**:

- **Import Error**: Add missing import or fix module path
- **Name Error**: Define missing variable or fix typo
- **Type Error**: Fix type mismatch or add type conversion
- **Attribute Error**: Fix method/property name or add attribute check
- **Syntax Error**: Fix malformed code (brackets, quotes, indentation)
- **Test Failure**: Fix logic to match expected behavior from spec
- **Runtime Error**: Add null checks, boundary checks, or error handling

**Output ONLY the complete corrected content of {file_path}**

Do not include explanations. Output must be ready to overwrite the file.
```

---

## Example Usage Scenarios

### Scenario 1: Import Error

**Input**:
```
ERROR MESSAGE:
Traceback (most recent call last):
  File "backend/api/auth.py", line 3, in <module>
    from models.user import User
ModuleNotFoundError: No module named 'models'

FILE: backend/api/auth.py

CURRENT CONTENT:
from fastapi import APIRouter
from models.user import User  # Wrong import path

router = APIRouter()
```

**Expected Fix**:
```python
from fastapi import APIRouter
from backend.models.user import User  # Fixed import path

router = APIRouter()
```

### Scenario 2: Test Failure

**Input**:
```
ERROR MESSAGE:
FAILED tests/test_auth.py::test_register_duplicate_email
Expected status 409, got 500

FILE: backend/services/auth.py

CURRENT CONTENT:
def register_user(email, password):
    user = User(email=email)
    user.set_password(password)
    db.save(user)  # Crashes if duplicate
    return user

SPECIFICATION CONTEXT:
- System SHALL reject duplicate email registration with 409 status
```

**Expected Fix**:
```python
def register_user(email, password):
    # Check for existing user
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        raise DuplicateEmailError(f"Email {email} already registered")
    
    user = User(email=email)
    user.set_password(password)
    db.save(user)
    return user
```

### Scenario 3: Missing Edge Case

**Input**:
```
ERROR MESSAGE:
FAILED tests/test_auth.py::test_empty_password
Expected ValueError, got User object

FILE: backend/models/user.py

CURRENT CONTENT:
def set_password(self, password: str) -> None:
    self.password_hash = generate_password_hash(password)

SPECIFICATION CONTEXT:
- Passwords must be at least 8 characters
```

**Expected Fix**:
```python
def set_password(self, password: str) -> None:
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    self.password_hash = generate_password_hash(password)
```

---

## Error Classification

```python
def _classify_error(self, error_message: str) -> str:
    """Determine error type from message."""
    error_types = {
        'ModuleNotFoundError': 'import',
        'ImportError': 'import',
        'NameError': 'undefined',
        'TypeError': 'type',
        'AttributeError': 'attribute',
        'SyntaxError': 'syntax',
        'IndentationError': 'syntax',
        'KeyError': 'missing_key',
        'ValueError': 'validation',
        'AssertionError': 'test_failure',
        'FAILED': 'test_failure'
    }
    
    for pattern, error_type in error_types.items():
        if pattern in error_message:
            return error_type
    
    return 'unknown'
```

---

## Bugfix Task Derivation

```python
def _derive_bugfix_tasks(self, validation_failures: List[Dict]) -> List[Dict]:
    """
    Create bugfix tasks from validation errors.
    
    Args:
        validation_failures: List of {
            'type': 'compile'|'test'|'lint',
            'file': 'path/to/file.py',
            'message': 'error message',
            'severity': 'error'|'warning'
        }
    
    Returns:
        List of bugfix task dicts (max 3)
    """
    # Group by file
    errors_by_file = {}
    for failure in validation_failures:
        if failure['severity'] != 'error':
            continue  # Skip warnings
        
        file_path = failure['file']
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []
        errors_by_file[file_path].append(failure)
    
    # Create tasks (prioritize by severity, limit to 3)
    bugfix_tasks = []
    for file_path, errors in list(errors_by_file.items())[:3]:
        # Combine error messages for this file
        combined_message = '\n\n'.join(e['message'] for e in errors)
        
        bugfix_tasks.append({
            'file_path': file_path,
            'error_type': self._classify_error(combined_message),
            'error': combined_message,
            'description': f"Fix errors in {file_path}"
        })
    
    return bugfix_tasks
```

---

## Usage in Adapter

```python
def _build_bugfix_prompt(
    self,
    task: Dict,
    spec_content: str,
    original_task: Dict
) -> List[Dict]:
    """Build prompt for bugfix."""
    
    file_path = task['file_path']
    
    # Read current (broken) file
    with open(file_path, 'r') as f:
        current_content = f.read()
    
    # Extract relevant spec
    spec_excerpt = self._extract_relevant_section(spec_content, original_task)
    
    system = """You are a debugging assistant...
    [system prompt from above]
    """
    
    user = f"""Fix this error:

---
ERROR MESSAGE:
{task['error']}

FILE WITH ERROR: {file_path}

CURRENT FILE CONTENT:
```
{current_content}
```

SPECIFICATION CONTEXT:
{self._truncate(spec_excerpt, 3000)}

ORIGINAL TASK:
{original_task.get('description', 'N/A')}
---

**Instructions**:
[instructions from template]

**Output ONLY the complete corrected content of {file_path}**
"""
    
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

## Bugfix Cycle Integration

```python
def _attempt_bugfix_cycle(self, validation_failures: List[Dict]) -> bool:
    """
    Attempt one round of bugfixes based on validation failures.
    
    Returns True if fixes were attempted, False if no fixable errors.
    """
    logger.info(
        "Validation failed - attempting bugfix cycle",
        extra={'run_id': self.run_id, 'failures': len(validation_failures)}
    )
    
    # Derive bugfix tasks (max 3)
    bugfix_tasks = self._derive_bugfix_tasks(validation_failures)
    
    if not bugfix_tasks:
        logger.warning("No fixable errors found")
        return False
    
    # Attempt fixes
    for task in bugfix_tasks:
        try:
            # Find original task this file belonged to
            original_task = self._find_original_task(task['file_path'])
            
            # Build bugfix prompt
            messages = self._build_bugfix_prompt(
                task,
                self._load_artifact('spec.md'),
                original_task
            )
            
            # Call API
            response = self._call_openai(messages)
            
            # Extract and save fix
            fixed_content = self._extract_file_content(response)
            self._save_file(task['file_path'], fixed_content)
            
            logger.info(
                f"Applied bugfix to {task['file_path']}",
                extra={'run_id': self.run_id, 'error_type': task['error_type']}
            )
            
        except Exception as e:
            logger.error(
                f"Bugfix failed for {task['file_path']}: {e}",
                extra={'run_id': self.run_id}
            )
    
    return True
```
