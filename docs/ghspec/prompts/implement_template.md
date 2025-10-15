# GHSpec Implement Phase Prompt Template

**Purpose**: Generate/update code for a specific task with full context

**Based on**: spec-kit's `templates/commands/implement.md` + Enhanced Hybrid approach

---

## System Prompt

```
You are a Copilot-style code assistant implementing features based on specifications and technical plans. Your role is to write clean, tested, idiomatic code for ONE file at a time.

**Critical Guidelines**:
- Modify EXACTLY ONE file per task
- Preserve existing code style and patterns
- Write complete, production-quality code
- Include proper error handling
- Add inline comments for complex logic
- Ensure code is testable
- If anything is unclear, make reasonable assumptions

**Output Format**: Complete file content only (no explanations, no markdown code fences unless file is markdown)
```

## User Prompt Template (Per Task)

```
Implement this task:

---
TASK: {task_description}
FILE: {file_path}
GOAL: {task_goal}

SPECIFICATION (relevant excerpt):
{spec_excerpt}

TECHNICAL PLAN (relevant excerpt):
{plan_excerpt}

CURRENT FILE CONTENT:
```
{current_file_content or "# File does not exist yet - create from scratch"}
```
---

**Instructions**:
1. Implement the task goal in the specified file
2. Follow the technical plan's architecture and patterns
3. Ensure implementation satisfies specification requirements
4. Preserve existing code style if file exists
5. Include proper error handling and validation
6. Add tests if this is a test file
7. Make reasonable assumptions for any unclear details

**Output ONLY the complete final content of {file_path}**

DO NOT include:
- Explanations or commentary
- Markdown code fences (unless the file itself is markdown)
- "Here's the implementation" or similar text
- Partial code or placeholders

Output must be ready to write directly to {file_path}.
```

---

## Example Usage Scenarios

### Scenario 1: Creating New Model File

**Input**:
```
TASK: Create User model with authentication fields
FILE: backend/models/user.py
GOAL: Implement User entity from data model

SPECIFICATION (excerpt):
- Users must have email and password
- Email must be unique and validated
- Passwords must be hashed, never stored plain

TECHNICAL PLAN (excerpt):
- Use SQLAlchemy ORM
- bcrypt for password hashing
- Email validation with regex

CURRENT FILE CONTENT:
# File does not exist yet
```

**Expected Output** (complete file):
```python
"""User model for authentication."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
import re

Base = declarative_base()

class User(Base):
    """User entity with authentication."""
    
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def set_password(self, password: str) -> None:
        """Hash and store password."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)
```

### Scenario 2: Updating Existing File

**Input**:
```
TASK: Add password reset functionality
FILE: backend/models/user.py
GOAL: Add reset token generation to User model

SPECIFICATION (excerpt):
- Users can request password reset via email
- Reset tokens expire after 1 hour
- Tokens are single-use

CURRENT FILE CONTENT:
[existing User model from above]
```

**Expected Output**: Updated file with reset token methods added

---

## Context Extraction

Before calling this template, extract relevant sections:

```python
def _extract_relevant_section(self, document: str, task: Dict) -> str:
    """
    Extract section of spec/plan relevant to current task.
    
    Uses task labels and description to find relevant content.
    """
    # Simple approach: extract sections containing task keywords
    task_keywords = self._extract_keywords(task['description'])
    
    sections = self._split_into_sections(document)
    relevant = []
    
    for section in sections:
        if any(keyword.lower() in section.lower() for keyword in task_keywords):
            relevant.append(section)
    
    # Join and truncate if needed
    result = '\n\n'.join(relevant)
    return self._truncate(result, max_chars=5000)

def _extract_keywords(self, text: str) -> List[str]:
    """Extract important nouns/verbs from task description."""
    # Remove common words, extract meaningful terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    words = text.lower().split()
    return [w for w in words if w not in stop_words and len(w) > 3]
```

---

## Usage in Adapter

```python
def _build_task_prompt(
    self,
    task: Dict,
    spec_content: str,
    plan_content: str,
    file_path: str
) -> List[Dict]:
    """Build prompt for code implementation."""
    
    # Read current file if exists
    current_content = ""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            current_content = f.read()
    else:
        current_content = "# File does not exist yet - create from scratch"
    
    # Extract relevant sections
    spec_excerpt = self._extract_relevant_section(spec_content, task)
    plan_excerpt = self._extract_relevant_section(plan_content, task)
    
    # Build prompts
    system = """You are a Copilot-style code assistant...
    [system prompt from above]
    """
    
    user = f"""Implement this task:

---
TASK: {task['description']}
FILE: {file_path}
GOAL: {task['goal']}

SPECIFICATION (relevant excerpt):
{self._truncate(spec_excerpt, 5000)}

TECHNICAL PLAN (relevant excerpt):
{self._truncate(plan_excerpt, 3000)}

CURRENT FILE CONTENT:
```
{current_content}
```
---

**Instructions**:
[instructions from template]

**Output ONLY the complete final content of {file_path}**
"""
    
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

## Output Extraction

```python
def _extract_file_content(self, api_response: str) -> str:
    """
    Extract clean file content from API response.
    
    Handles cases where model adds explanations or code fences.
    """
    content = api_response.strip()
    
    # Remove markdown code fences if present
    if content.startswith('```'):
        lines = content.split('\n')
        # Remove first line (```python or similar)
        if lines[0].startswith('```'):
            lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        content = '\n'.join(lines)
    
    # Remove common prefixes the model might add
    prefixes_to_remove = [
        "Here's the implementation:",
        "Here is the code:",
        "The updated file:",
    ]
    
    for prefix in prefixes_to_remove:
        if content.startswith(prefix):
            content = content[len(prefix):].strip()
    
    return content
```
