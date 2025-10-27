# Example Project Constitution

**Version**: 1.0.0  
**Purpose**: Template for project-specific coding standards and principles  
**Usage**: Copy to `project_constitution.md` and customize for your project

---

## Overview

This constitution defines coding standards, architectural patterns, and quality requirements that guide all phases of the GHSpec-Kit workflow (Specify → Plan → Tasks → Implement → Bugfix).

**When to use this:**
- Creating new projects with specific quality standards
- Enforcing team coding conventions
- Ensuring consistency across framework comparisons
- Documenting technical decisions

**How it works:**
- Loaded once at experiment start
- Injected into all 5 phase prompts as system context
- Guides AI decisions throughout workflow
- Hierarchical fallback: project → inline → default

---

## 1. Language and Version Requirements

**Primary Language**: Python 3.11+

**Rationale**: Python 3.11 offers improved type hints, error messages, and performance optimizations.

**Standards**:
- Use type hints for all function signatures
- Leverage dataclasses for structured data
- Use f-strings for string formatting
- Follow PEP 484 (Type Hints) and PEP 585 (Generic Types)

**Example**:
```python
from typing import Optional
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
    age: Optional[int] = None

def create_user(name: str, email: str) -> User:
    """Create a new user with validated email."""
    return User(id=generate_id(), name=name, email=email)
```

---

## 2. Code Style and Formatting

**Style Guide**: PEP 8 (Python Enhancement Proposal 8)

**Formatter**: Black (line length: 100 characters)

**Linter**: Pylint (minimum score: 8.0/10)

**Standards**:
- Consistent indentation (4 spaces)
- Maximum line length: 100 characters
- Maximum function length: 50 lines
- Maximum cyclomatic complexity: 10
- Snake_case for functions and variables
- PascalCase for classes
- UPPER_CASE for constants

**Example**:
```python
# Good: Clear, concise, follows PEP 8
def calculate_total_price(items: list[Item], tax_rate: float = 0.08) -> float:
    """Calculate total price including tax."""
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)

# Bad: Long lines, unclear names, poor structure
def calc(i, t=0.08):
    return sum([x.price for x in i]) * (1 + t)  # Missing docstring, unclear variable names
```

---

## 3. Testing Requirements

**Framework**: pytest with pytest-asyncio

**Coverage Target**: Minimum 80% code coverage

**Standards**:
- Write unit tests for all public functions
- Write integration tests for API endpoints
- Use fixtures for test data setup
- Mock external dependencies
- Test edge cases and error conditions

**Test Structure**:
```python
import pytest
from myapp.models import User

@pytest.fixture
def sample_user():
    """Fixture providing a sample user for tests."""
    return User(id=1, name="Test User", email="test@example.com")

def test_user_creation(sample_user):
    """Test that user is created with correct attributes."""
    assert sample_user.id == 1
    assert sample_user.name == "Test User"
    assert sample_user.email == "test@example.com"

def test_email_validation():
    """Test that invalid email raises ValueError."""
    with pytest.raises(ValueError, match="Invalid email format"):
        User(id=2, name="Bad User", email="not-an-email")
```

---

## 4. Documentation Standards

**Docstring Style**: Google-style docstrings

**Standards**:
- All public functions, classes, and modules must have docstrings
- Docstrings must describe purpose, parameters, return values, and exceptions
- Use type hints in conjunction with docstrings (not in docstring)
- Include usage examples for complex functions

**Example**:
```python
def fetch_user_by_id(user_id: int, include_deleted: bool = False) -> Optional[User]:
    """
    Fetch a user by their ID from the database.
    
    Args:
        user_id: The unique identifier of the user.
        include_deleted: Whether to include soft-deleted users in search.
    
    Returns:
        The User object if found, None otherwise.
    
    Raises:
        DatabaseError: If database connection fails.
        ValueError: If user_id is negative.
    
    Example:
        >>> user = fetch_user_by_id(42)
        >>> print(user.name)
        'John Doe'
    """
    if user_id < 0:
        raise ValueError("User ID must be non-negative")
    
    # Implementation...
```

---

## 5. Error Handling

**Strategy**: Explicit error handling with custom exceptions

**Standards**:
- Use custom exception classes for domain-specific errors
- Catch specific exceptions, not generic `Exception`
- Log errors with contextual information
- Provide meaningful error messages
- Use type guards to prevent errors

**Example**:
```python
class UserNotFoundError(Exception):
    """Raised when a user cannot be found in the database."""
    pass

class InvalidEmailError(ValueError):
    """Raised when email format is invalid."""
    pass

def get_user(user_id: int) -> User:
    """
    Retrieve a user by ID.
    
    Raises:
        UserNotFoundError: If user does not exist.
        DatabaseError: If database query fails.
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
    except DatabaseError as e:
        logger.error(f"Database query failed for user_id={user_id}: {e}")
        raise
    
    if user is None:
        raise UserNotFoundError(f"User with id={user_id} not found")
    
    return user
```

---

## 6. API Design

**Framework**: FastAPI 0.104+

**Standards**:
- RESTful endpoint naming
- Use HTTP status codes correctly (200, 201, 400, 404, 500)
- Validate request bodies with Pydantic models
- Return structured JSON responses
- Include API versioning (/api/v1/)
- Provide OpenAPI documentation

**Example**:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI(title="My API", version="1.0.0")

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate) -> UserResponse:
    """
    Create a new user.
    
    Returns:
        201 Created: User successfully created.
        400 Bad Request: Invalid input data.
        409 Conflict: Email already exists.
    """
    # Implementation...
```

---

## 7. Database Interaction

**ORM**: SQLAlchemy 2.0+

**Database**: PostgreSQL 14+

**Standards**:
- Use async SQLAlchemy for non-blocking I/O
- Define models with proper relationships
- Use migrations for schema changes (Alembic)
- Index foreign keys and frequently queried columns
- Use connection pooling
- Avoid N+1 queries (use eager loading)

**Example**:
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    posts = relationship("Post", back_populates="author", lazy="selectin")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    author = relationship("User", back_populates="posts")
```

---

## 8. Security Requirements

**Standards**:
- Validate all user inputs
- Use parameterized queries (prevent SQL injection)
- Hash passwords with bcrypt (cost factor: 12)
- Implement rate limiting on API endpoints
- Use HTTPS in production
- Sanitize outputs (prevent XSS)
- Use environment variables for secrets

**Example**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hashed version."""
    return pwd_context.verify(plain_password, hashed_password)
```

---

## 9. Logging Standards

**Library**: Python standard library `logging`

**Standards**:
- Use structured logging (JSON format)
- Include context (user_id, request_id, timestamp)
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Log all API requests and responses
- Never log sensitive data (passwords, tokens)

**Example**:
```python
import logging
import json

logger = logging.getLogger(__name__)

def process_payment(user_id: int, amount: float) -> bool:
    """Process payment for user."""
    logger.info(
        "Payment processing started",
        extra={"user_id": user_id, "amount": amount, "currency": "USD"}
    )
    
    try:
        result = payment_gateway.charge(user_id, amount)
        logger.info(
            "Payment successful",
            extra={"user_id": user_id, "transaction_id": result.id}
        )
        return True
    except PaymentError as e:
        logger.error(
            "Payment failed",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        return False
```

---

## 10. Performance Guidelines

**Standards**:
- Use async/await for I/O-bound operations
- Implement caching for frequently accessed data (Redis)
- Use database query optimization (EXPLAIN ANALYZE)
- Profile code to identify bottlenecks
- Set reasonable timeouts (API: 30s, DB: 10s)
- Use pagination for large result sets

**Example**:
```python
from fastapi import Query
from redis import asyncio as aioredis

redis = aioredis.from_url("redis://localhost")

@app.get("/api/v1/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> dict:
    """
    List users with pagination.
    
    Performance: Cached for 5 minutes, paginated to limit result size.
    """
    cache_key = f"users:page:{page}:size:{page_size}"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query database
    offset = (page - 1) * page_size
    users = await db.query(User).limit(page_size).offset(offset).all()
    
    result = {"users": [user.to_dict() for user in users], "page": page}
    
    # Cache result
    await redis.setex(cache_key, 300, json.dumps(result))
    
    return result
```

---

## 11. Dependency Management

**Tool**: pip + requirements.txt (or Poetry for advanced projects)

**Standards**:
- Pin exact versions in production (e.g., `fastapi==0.104.1`)
- Use version ranges in development (e.g., `fastapi>=0.104.0,<0.105.0`)
- Separate requirements: `requirements.txt`, `requirements-dev.txt`, `requirements-test.txt`
- Keep dependencies minimal (avoid bloat)
- Regularly update dependencies (security patches)

**Example**:
```txt
# requirements.txt
fastapi==0.104.1
sqlalchemy[asyncio]==2.0.23
pydantic==2.5.0
uvicorn[standard]==0.24.0
redis==5.0.1

# requirements-dev.txt
-r requirements.txt
black==23.11.0
pylint==3.0.2
mypy==1.7.1

# requirements-test.txt
-r requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2  # For FastAPI test client
```

---

## 12. Git Workflow

**Branching Strategy**: Feature branches + main branch

**Standards**:
- Create feature branches from main: `feature/add-user-authentication`
- Write descriptive commit messages (50-char summary + detailed body)
- Squash commits before merging to main
- Use Pull Requests for code review
- Require at least 1 approval before merging
- Delete branches after merging

**Commit Message Format**:
```
Add user authentication with JWT tokens

- Implement JWT token generation and validation
- Add /login and /logout endpoints
- Write unit tests for authentication logic
- Update API documentation

Closes #42
```

---

## 13. Configuration Management

**Tool**: Environment variables + YAML config files

**Standards**:
- Use `.env` files for local development (never commit!)
- Use environment variables in production
- Provide `.env.example` with placeholder values
- Validate configuration on startup
- Use Pydantic Settings for type-safe config

**Example**:
```python
from pydantic import BaseSettings, PostgresDsn

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    app_name: str = "My API"
    debug: bool = False
    database_url: PostgresDsn
    redis_url: str = "redis://localhost:6379"
    secret_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## Customization Guide

**To create a project-specific constitution:**

1. Copy this file to `project_constitution.md`:
   ```bash
   cp example_constitution.md project_constitution.md
   ```

2. Customize sections relevant to your project:
   - Remove sections you don't need
   - Add project-specific requirements
   - Update version numbers
   - Adjust standards to match team preferences

3. Test with a small experiment:
   ```bash
   ./runners/run_experiment.sh ghspec --sprint 1
   ```

4. Review generated code for constitution compliance

5. Iterate and refine constitution based on results

**Recommended sections for minimal constitution:**
- Language and Version Requirements (Section 1)
- Code Style and Formatting (Section 2)
- Testing Requirements (Section 3)
- Error Handling (Section 5)

**Optional sections (add as needed):**
- API Design (Section 6) - If building web APIs
- Database Interaction (Section 7) - If using databases
- Security Requirements (Section 8) - For production systems
- Performance Guidelines (Section 10) - For high-traffic systems

---

## References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
