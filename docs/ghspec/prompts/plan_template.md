# GHSpec Plan Phase Prompt Template

**Purpose**: Generate technical architecture and implementation plan from specification

**Based on**: spec-kit's `templates/commands/plan.md`

---

## System Prompt

```
You are a lead architect and technical planner. Your role is to translate a business specification into a concrete technical plan that defines the architecture, tech stack, and implementation approach.

**Critical Guidelines**:
- Base decisions on the specification requirements
- Choose appropriate, modern technologies
- Define clear module boundaries and responsibilities
- Specify data models and API contracts
- Consider scalability, security, and maintainability
- Document technical trade-offs and decisions

**Output Format**: Markdown document with technical design
```

## User Prompt Template

```
I need you to create a technical implementation plan based on this specification:

---
SPECIFICATION:
{spec_content}
---

Generate a complete implementation plan following this structure:

# Implementation Plan: [Feature Name]

## Technical Context
- **Target Platform**: [Web/Mobile/Desktop/Backend]
- **Primary Language**: [Language choice with rationale]
- **Framework**: [Framework choice with rationale]
- **Database**: [If data persistence needed]
- **Key Libraries**: [Essential dependencies]

## Architecture Overview
[High-level architecture diagram description]
- Component 1: Responsibilities
- Component 2: Responsibilities
- Interactions and data flow

## Data Model
[Based on Key Entities from spec]

### Entity: [Name]
```
Fields:
- field1: type, constraints
- field2: type, constraints

Relationships:
- relates_to: Entity2 (one-to-many/many-to-many)

Validation Rules:
- Rule from requirements
```

## API Contracts
[For each user interaction or integration point]

### Endpoint: [Name]
- **Purpose**: [From functional requirement]
- **Method**: GET/POST/PUT/DELETE
- **Request**: `{ schema }`
- **Response**: `{ schema }`
- **Validation**: [Rules from spec]

## Module Structure
```
project/
├── module1/
│   ├── component1.ext
│   └── component2.ext
├── module2/
└── tests/
```

## Implementation Phases
1. **Phase 1: Foundation** - Core data models and basic operations
2. **Phase 2: Core Features** - Primary user scenarios
3. **Phase 3: Polish** - Edge cases, error handling, optimization

## Technical Decisions
[Document key choices]
- **Decision**: [What was chosen]
- **Rationale**: [Why chosen]
- **Alternatives Considered**: [What else evaluated]
- **Trade-offs**: [Pros/cons]

## Testing Strategy
- Unit tests: [What to test]
- Integration tests: [What to test]
- Acceptance criteria: [From spec success criteria]

## Security Considerations
[If applicable based on spec]

## Performance Requirements
[Based on spec success criteria]

## Dependencies
[External libraries/services needed]

---

**Important**:
- All decisions must trace back to specification requirements
- Be specific about technologies and versions
- Define clear boundaries between modules
- Ensure plan enables all success criteria from spec
```

---

## Example Output Structure

```markdown
# Implementation Plan: User Authentication

## Technical Context
- **Target Platform**: Web Application
- **Primary Language**: Python 3.11 (mature ecosystem, excellent security libraries)
- **Framework**: FastAPI (async, automatic API docs, type hints)
- **Database**: PostgreSQL (ACID compliance for user data)
- **Key Libraries**: bcrypt (password hashing), PyJWT (tokens), pydantic (validation)

## Architecture Overview
- **API Layer**: FastAPI endpoints for auth operations
- **Service Layer**: Business logic for registration, login, validation
- **Data Layer**: User repository with database operations
- **Security Layer**: Password hashing, token generation/validation

## Data Model

### Entity: User
```
Fields:
- id: UUID, primary key
- email: string, unique, validated format
- password_hash: string, bcrypt hashed
- created_at: timestamp
- last_login: timestamp, nullable

Validation Rules:
- Email must match RFC 5322 format
- Password must be 8+ chars, include uppercase, lowercase, number
```

### Entity: Session
```
Fields:
- id: UUID, primary key
- user_id: UUID, foreign key
- token: string, JWT
- expires_at: timestamp
```

## API Contracts

### POST /auth/register
- **Purpose**: Create new user account
- **Request**: `{ "email": "user@example.com", "password": "SecurePass123" }`
- **Response**: `{ "user_id": "uuid", "created_at": "timestamp" }`
- **Validation**: Email format, password strength, duplicate check

### POST /auth/login
- **Purpose**: Authenticate user and create session
- **Request**: `{ "email": "user@example.com", "password": "SecurePass123" }`
- **Response**: `{ "token": "jwt", "expires_at": "timestamp" }`
- **Validation**: Credentials match, account active

...
```

---

## Usage in Adapter

```python
def _build_plan_prompt(self, spec_content: str) -> List[Dict]:
    """Build prompt for technical planning."""
    system = """You are a lead architect and technical planner...
    [system prompt from above]
    """
    
    user = f"""I need you to create a technical implementation plan based on this specification:

---
SPECIFICATION:
{spec_content}
---

Generate a complete implementation plan...
[user prompt template filled with spec]
"""
    
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```
