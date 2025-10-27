# Default Project Constitution

**Version**: 1.0.0  
**Purpose**: Default coding standards and principles for GHSpec-Kit experiments  
**Scope**: Applied when no project-specific constitution is provided

---

## I. Code Quality Principles

### 1.1 Readability First
- Code should be self-documenting through clear naming conventions
- Complex logic must include explanatory comments
- Functions should do one thing and do it well (Single Responsibility Principle)
- Maximum function length: 50 lines (excluding docstrings)
- Maximum file length: 500 lines

### 1.2 Naming Conventions
- **Python**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **JavaScript/TypeScript**: camelCase for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Descriptive names**: Avoid abbreviations unless widely recognized (e.g., `url`, `http`, `api`)
- **Boolean variables**: Use positive predicates (`is_active`, `has_permission`, not `is_not_active`)

### 1.3 Documentation
- All public functions/methods must have docstrings explaining purpose, parameters, and return values
- All classes must have docstrings explaining purpose and main responsibilities
- README.md required for all projects explaining setup and usage
- Complex algorithms must include comments explaining the approach

---

## II. Testing Requirements

### 2.1 Test Coverage
- All new features must include automated tests
- Minimum test coverage target: 70% for business logic
- Critical paths (authentication, payment, data modification) require 90%+ coverage

### 2.2 Test Types
- **Unit tests**: Test individual functions/methods in isolation
- **Integration tests**: Test interactions between components
- **Contract tests**: Test API endpoints match specifications (for APIs)
- **End-to-end tests**: Optional for critical user journeys

### 2.3 Test Organization
- Tests should mirror source code structure (`src/services/user.py` → `tests/services/test_user.py`)
- Test files must be named with `test_` prefix for pytest discovery
- Use descriptive test names: `test_user_login_with_valid_credentials_succeeds()`

---

## III. Error Handling & Validation

### 3.1 Input Validation
- Validate all user inputs at system boundaries (API endpoints, CLI arguments)
- Fail fast: Reject invalid inputs immediately with clear error messages
- Use type hints (Python) or types (TypeScript) to catch errors early

### 3.2 Error Messages
- User-facing errors must be actionable (explain what went wrong and how to fix it)
- Include error codes for debugging (e.g., `E001: Invalid email format`)
- Never expose internal implementation details or stack traces to end users
- Log detailed error context for debugging (but never log sensitive data)

### 3.3 Exception Handling
- Don't catch exceptions you can't handle meaningfully
- Avoid bare `except:` clauses - catch specific exception types
- Always clean up resources (use context managers: `with` statement)

---

## IV. Security Principles

### 4.1 Data Protection
- Never log passwords, tokens, API keys, or PII (Personally Identifiable Information)
- Use environment variables for configuration secrets (never hardcode)
- Sanitize all user inputs to prevent injection attacks (SQL, XSS, command injection)

### 4.2 Authentication & Authorization
- Use established libraries for authentication (don't roll your own crypto)
- Implement principle of least privilege (users access only what they need)
- Session tokens must expire and be revocable

### 4.3 Dependency Security
- Keep dependencies up-to-date to avoid known vulnerabilities
- Pin dependency versions for reproducibility (`requirements.txt`, `package-lock.json`)
- Review dependency licenses for compatibility

---

## V. Performance Guidelines

### 5.1 Efficiency
- Avoid N+1 query problems (use joins or batch loading)
- Implement pagination for list endpoints (max 100 items per page)
- Cache expensive computations when appropriate
- Use async/await for I/O-bound operations

### 5.2 Scalability Awareness
- Design stateless services when possible
- Avoid hardcoding limits (use configuration)
- Consider database indexing for frequently queried fields

---

## VI. Code Organization

### 6.1 Project Structure
- **Python**: Standard layout with `src/`, `tests/`, `docs/`, `config/`
- **JavaScript/TypeScript**: Separate `src/` from `dist/` (compiled output)
- Configuration files at project root (`.env.example`, `README.md`)

### 6.2 Separation of Concerns
- Business logic separated from presentation layer
- Database access through repository/DAO pattern
- External API calls isolated in service layer

### 6.3 Dependency Management
- Minimize external dependencies (only include what you need)
- Prefer standard library over third-party for simple tasks
- Document why each major dependency is needed

---

## VII. Version Control Practices

### 7.1 Git Hygiene
- Commit messages should explain "why", not just "what"
- Small, atomic commits (one logical change per commit)
- Never commit sensitive data (passwords, keys, tokens)
- Use `.gitignore` to exclude build artifacts and virtual environments

### 7.2 Code Review Readiness
- Code should be self-explanatory to reviewers
- Include tests that demonstrate the feature works
- Update documentation alongside code changes

---

## VIII. API Design (if applicable)

### 8.1 RESTful Principles
- Use HTTP verbs correctly (GET for read, POST for create, PUT/PATCH for update, DELETE for delete)
- Use nouns for resource endpoints (`/users`, `/orders`, not `/getUsers`, `/createOrder`)
- Return appropriate status codes (200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Internal Error)

### 8.2 Request/Response Format
- Accept and return JSON by default
- Use consistent field naming (snake_case or camelCase, but be consistent)
- Include API versioning in URL (`/api/v1/users`) or headers

### 8.3 Error Responses
- Consistent error format: `{"error": {"code": "E001", "message": "...", "details": {}}}`
- Include request ID for tracing
- Provide helpful validation error details

---

## IX. Database Guidelines

### 9.1 Schema Design
- Use meaningful table and column names
- Define appropriate indexes for query performance
- Use foreign keys to enforce referential integrity
- Include `created_at` and `updated_at` timestamps

### 9.2 Migrations
- Always use migrations for schema changes (never manual SQL)
- Migrations must be reversible when possible
- Test migrations on a copy of production data

---

## X. Configuration Management

### 10.1 Environment-Specific Config
- Use environment variables for deployment-specific values
- Provide `.env.example` showing required configuration
- Document all configuration options
- Fail fast if required configuration is missing

### 10.2 Sensible Defaults
- Provide reasonable defaults for optional configuration
- Development environment should work with minimal setup

---

## XI. Logging & Monitoring

### 11.1 Structured Logging
- Use structured logging (JSON format) for easier parsing
- Include context: request ID, user ID (when applicable), timestamp
- Log levels: DEBUG (development), INFO (important events), WARNING (recoverable issues), ERROR (failures)

### 11.2 What to Log
- **DO log**: Request/response metadata, business events, errors with context
- **DON'T log**: Passwords, tokens, full credit card numbers, sensitive PII

---

## XII. Deployment Considerations

### 12.1 Production Readiness
- Application starts successfully with no manual intervention
- Health check endpoint available for monitoring
- Graceful shutdown (finish in-flight requests)
- Environment variables documented

### 12.2 Backward Compatibility
- API changes should be backward compatible or versioned
- Database migrations should not require downtime
- Deprecate features with warning period before removal

---

## XIII. Fail-Fast Philosophy

### 13.1 Early Detection
- Validate configuration at startup
- Detect errors as early as possible in the request lifecycle
- Use type checking and linting to catch errors before runtime

### 13.2 No Silent Failures
- Never swallow exceptions silently
- Log all errors with sufficient context for debugging
- If a operation cannot complete correctly, fail explicitly rather than returning partial/incorrect results

---

## Usage Notes

**Customization**: Projects with specific requirements should create a `project_constitution.md` that extends or overrides these defaults.

**Priority**: When conflicts arise between these principles, prioritize in this order:
1. Security
2. Correctness
3. Maintainability
4. Performance

**Enforcement**: These principles guide AI-generated code during GHSpec-Kit experiments. They are not enforced by tooling but should be verified during code review.
