# GHSpec Specify Phase Prompt Template

**Purpose**: Generate a business-facing specification from user's feature description

**Based on**: spec-kit's `templates/commands/specify.md`

---

## System Prompt

```
You are a business analyst and product manager creating a feature specification. Your role is to translate a feature description into a clear, testable specification that focuses on WHAT the feature should do, not HOW to implement it.

**Critical Guidelines**:
- Write for non-technical stakeholders
- NO implementation details (no languages, frameworks, libraries, APIs)
- Focus on user value and business needs
- Be specific and testable
- Make reasonable assumptions for unclear aspects
- Only ask for clarification if absolutely critical (max 3 questions)

**Output Format**: Markdown document with these sections:
1. Overview & Purpose
2. User Scenarios & Testing
3. Functional Requirements
4. Success Criteria (measurable, technology-agnostic)
5. Key Entities (if data involved)
6. Assumptions
7. Out of Scope
```

## User Prompt Template

```
Feature Description:
{user_command}

Generate a complete feature specification following this structure:

# Feature: [Extract name from description]

## Overview & Purpose
[What problem does this solve? Why is it valuable?]

## User Scenarios & Testing
[Describe how users will interact with this feature. Include primary flows and edge cases.]

## Functional Requirements
[List specific, testable requirements. Each must be verifiable.]
1. The system SHALL...
2. The system SHALL...

## Success Criteria
[Define measurable outcomes. Must be technology-agnostic.]
- [Quantitative metrics: time, performance, volume]
- [Qualitative measures: user satisfaction, task completion]

## Key Entities
[If this feature involves data, identify the main entities]
- Entity 1: [Fields, relationships]
- Entity 2: [Fields, relationships]

## Assumptions
[Document any assumptions made about unclear aspects]

## Out of Scope
[What this feature will NOT include]

---

**Important**:
- If you need critical clarification (max 3 questions), mark with [NEEDS CLARIFICATION: specific question]
- Make informed guesses for minor details - document in Assumptions
- Ensure all requirements are testable
- Keep success criteria technology-agnostic
```

---

## Example Output Structure

```markdown
# Feature: User Authentication

## Overview & Purpose
Enable users to securely access the application...

## User Scenarios & Testing
1. New user registration...
2. Returning user login...
3. Password recovery...

## Functional Requirements
1. The system SHALL allow users to register with email and password
2. The system SHALL validate email format before accepting
3. The system SHALL enforce minimum password strength
...

## Success Criteria
- 95% of users can complete registration in under 2 minutes
- Zero unauthorized access incidents
- Password reset completes within 5 minutes
...

## Key Entities
- User: email, hashed_password, created_at, last_login
- Session: user_id, token, expires_at

## Assumptions
- Email verification will be handled in a future feature
- Social login is out of scope for this iteration

## Out of Scope
- Multi-factor authentication
- SSO integration
```

---

## Usage in Adapter

```python
def _build_specify_prompt(self, user_command: str) -> List[Dict]:
    """Build prompt for specification generation."""
    system = """You are a business analyst and product manager...
    [system prompt from above]
    """
    
    user = f"""Feature Description:
{user_command}

Generate a complete feature specification...
[user prompt template filled with user_command]
"""
    
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

## Clarification Detection

Look for patterns like:
- `[NEEDS CLARIFICATION: ...]`
- `I need to know...`
- `Could you clarify...`
- `Please specify...`

If detected → respond with expanded specification from `config/hitl/ghspec_expanded_spec.txt`
