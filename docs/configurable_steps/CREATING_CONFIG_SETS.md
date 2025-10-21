# Creating Custom Config Sets

**Last Updated**: 2024-10-21  
**Version**: 1.0  
**Difficulty**: Intermediate

---

## 📋 Overview

This guide shows you how to create custom config sets for the genai-devbench system. Config sets are curated experiment templates that define steps, prompts, and HITL files for specific scenarios.

---

## 🎯 When to Create a Config Set

Create a custom config set when you want to:

- ✅ **Reuse a scenario** across multiple experiments
- ✅ **Share a template** with other researchers
- ✅ **Standardize testing** for a specific domain
- ✅ **Curate prompts** for a common use case

**Examples**:
- `microservices`: Multi-service architecture with service mesh
- `ml_pipeline`: Data processing → Training → Deployment
- `graphql_api`: GraphQL API with subscriptions
- `blockchain`: Smart contract development

---

## 📁 Config Set Structure

A config set is a directory with this structure:

```
config_sets/
└── your_config_set/
    ├── metadata.yaml              # ← Config set info
    ├── experiment_template.yaml   # ← Default config.yaml template
    ├── prompts/                   # ← Prompt files
    │   ├── 01_step_one.txt
    │   ├── 02_step_two.txt
    │   └── ...
    └── hitl/                      # ← HITL files
        └── expanded_spec.txt
```

---

## 🛠️ Step-by-Step Guide

### Step 1: Create Directory Structure

```bash
cd config_sets/
mkdir -p your_config_set/{prompts,hitl}
cd your_config_set/
```

### Step 2: Create metadata.yaml

This file defines your config set's identity and catalog of steps.

**Template**:
```yaml
# Config Set Metadata
name: "your_config_set"
version: "1.0.0"
description: "Brief description of what this config set does"

# Catalog of available steps
available_steps:
  - id: 1
    name: "Step Name"
    prompt_file: "prompts/01_step_name.txt"
    description: "What this step does"
  
  - id: 2
    name: "Another Step"
    prompt_file: "prompts/02_another_step.txt"
    description: "What this step does"

# Scenario-specific defaults
defaults:
  timeout:
    per_step: 600
    total: 3600
  
  metrics:
    weights:
      functionality: 0.4
      code_quality: 0.3
      documentation: 0.2
      test_coverage: 0.1
```

**Example** (microservices config set):
```yaml
name: "microservices"
version: "1.0.0"
description: "Multi-service architecture with API gateway and service mesh"

available_steps:
  - id: 1
    name: "User Service"
    prompt_file: "prompts/01_user_service.txt"
    description: "Create user management microservice with database"
  
  - id: 2
    name: "Product Service"
    prompt_file: "prompts/02_product_service.txt"
    description: "Create product catalog microservice"
  
  - id: 3
    name: "API Gateway"
    prompt_file: "prompts/03_api_gateway.txt"
    description: "Implement API gateway with routing and auth"
  
  - id: 4
    name: "Service Mesh"
    prompt_file: "prompts/04_service_mesh.txt"
    description: "Add service mesh with Istio for observability"

defaults:
  timeout:
    per_step: 900  # 15 minutes (complex steps)
    total: 7200    # 2 hours total
  
  metrics:
    weights:
      functionality: 0.3
      code_quality: 0.3
      documentation: 0.2
      architecture: 0.2
```

### Step 3: Create experiment_template.yaml

This file becomes the base `config.yaml` for generated experiments.

**Template**:
```yaml
# Experiment Template for 'your_config_set' Config Set
# This file is used as the base for generated config.yaml

# Steps configuration (all enabled by default)
steps:
  - id: 1
    enabled: true
    name: "Step Name"
    prompt_file: "config/prompts/01_step_name.txt"
  
  - id: 2
    enabled: true
    name: "Another Step"
    prompt_file: "config/prompts/02_another_step.txt"

# Timeouts
timeouts:
  step_timeout_seconds: 600
  total_timeout_seconds: 3600

# Metrics configuration
metrics:
  weights:
    functionality: 0.4
    code_quality: 0.3
    documentation: 0.2
    test_coverage: 0.1

# Stopping rule
stopping:
  confidence_level: 0.95
  min_runs: 10
  max_runs: 100
```

**Important**: Prompt file paths use `config/prompts/` (relative to generated experiment root).

### Step 4: Create Prompt Files

Create one prompt file per step in the `prompts/` directory.

**Naming Convention**: `{id:02d}_{name}.txt`
- `01_step_name.txt`
- `02_another_step.txt`
- `03_third_step.txt`

**Example** (`prompts/01_user_service.txt`):
```
You are building a microservices-based e-commerce system.

TASK: Create a User Management Microservice

Requirements:
1. User entity with fields:
   - id (UUID)
   - email (unique)
   - password (hashed)
   - created_at, updated_at

2. REST API endpoints:
   - POST /users - Create user
   - GET /users/{id} - Get user by ID
   - PUT /users/{id} - Update user
   - DELETE /users/{id} - Delete user
   - GET /users - List users (paginated)

3. Technical requirements:
   - Use FastAPI framework
   - PostgreSQL database
   - SQLAlchemy ORM
   - Password hashing with bcrypt
   - Input validation with Pydantic
   - Docker containerization

4. Code quality:
   - Type hints
   - Docstrings
   - Error handling
   - Logging

DELIVERABLES:
- src/services/user_service/
  - main.py (FastAPI app)
  - models.py (SQLAlchemy models)
  - schemas.py (Pydantic schemas)
  - database.py (DB connection)
  - Dockerfile
  - requirements.txt
- tests/
  - test_user_service.py

Generate complete, working code that can be run with Docker.
```

**Tips for Good Prompts**:
- ✅ Be specific about requirements
- ✅ Include technical constraints (framework, database, etc.)
- ✅ Specify deliverables clearly
- ✅ Mention code quality expectations
- ✅ Include examples if helpful

### Step 5: Create HITL Files

Create files in the `hitl/` directory for human-in-the-loop interactions.

**Typical HITL Files**:
- `expanded_spec.txt` - Detailed specification for reference
- `clarifications.txt` - Common clarifications
- `examples.txt` - Example code/patterns

**Example** (`hitl/expanded_spec.txt`):
```
# Microservices E-Commerce System Specification

## Architecture Overview

This system consists of 4 microservices:
1. User Service - User authentication and management
2. Product Service - Product catalog management
3. API Gateway - Request routing and authentication
4. Service Mesh - Inter-service communication and observability

## Service Dependencies

User Service:
- Database: PostgreSQL
- External: None

Product Service:
- Database: PostgreSQL
- External: None

API Gateway:
- External: User Service, Product Service

Service Mesh:
- All services for observability

## API Contracts

### User Service API

POST /users
Request:
{
  "email": "user@example.com",
  "password": "securepassword"
}
Response (201):
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2024-10-21T10:00:00Z"
}

... (more endpoints)

## Infrastructure

- Docker Compose for local development
- PostgreSQL 15
- Istio service mesh (optional for advanced setup)
```

### Step 6: Validate Your Config Set

Run validation to check for errors:

```bash
cd /path/to/genai-devbench

# Test loading your config set
python -c "
from pathlib import Path
from src.config_sets.loader import ConfigSetLoader

loader = ConfigSetLoader(Path('config_sets'))
config_set = loader.load('your_config_set')
print(f'✅ Config set valid: {config_set.name}')
print(f'   Steps: {config_set.get_step_count()}')
"
```

### Step 7: Test Generation

Generate an experiment using your config set:

```bash
python scripts/new_experiment.py \
  --name test_your_config \
  --config-set your_config_set \
  --model gpt-4o-mini \
  --frameworks baes \
  --runs 1
```

**Verify**:
1. ✅ All prompt files copied to `test_your_config/config/prompts/`
2. ✅ All HITL files copied to `test_your_config/config/hitl/`
3. ✅ `config.yaml` has all steps enabled
4. ✅ Prompt file paths correct (`config/prompts/...`)

### Step 8: Test Execution

Run the generated experiment:

```bash
cd test_your_config
./run.sh
```

**Watch for**:
- ✅ Steps execute in correct order
- ✅ Prompts load correctly
- ✅ No file not found errors
- ✅ Results recorded properly

---

## 📏 Validation Rules

Your config set must pass these validation rules:

### Required Files

```
your_config_set/
├── metadata.yaml              ✅ Required
├── experiment_template.yaml   ✅ Required
├── prompts/                   ✅ Required (at least 1 file)
└── hitl/                      ✅ Required (at least 1 file)
```

### metadata.yaml Requirements

- ✅ `name` field matches directory name
- ✅ `version` follows semver (e.g., "1.0.0")
- ✅ `description` is present and non-empty
- ✅ `available_steps` has at least one step
- ✅ Step IDs are unique
- ✅ All `prompt_file` paths exist

### experiment_template.yaml Requirements

- ✅ Has `steps` array
- ✅ Each step has `id`, `enabled`, `name`, `prompt_file`
- ✅ Step IDs match `metadata.yaml`
- ✅ Prompt paths use `config/prompts/` prefix
- ✅ Has `timeouts` section
- ✅ Has `metrics` section

### Prompt File Requirements

- ✅ Files named with pattern: `{id:02d}_{name}.txt`
- ✅ All files referenced in metadata exist
- ✅ Files are non-empty
- ✅ Files use UTF-8 encoding

---

## 🎨 Design Patterns

### Pattern 1: Sequential Steps

Steps build on each other (common pattern):

```yaml
available_steps:
  - id: 1
    name: "Foundation"
    description: "Set up basic structure"
  
  - id: 2
    name: "Core Features"
    description: "Build on foundation"
  
  - id: 3
    name: "Advanced Features"
    description: "Add complexity"
```

**Example**: CRUD → Relationships → Auth → UI

### Pattern 2: Independent Steps

Steps can run in any order (flexible pattern):

```yaml
available_steps:
  - id: 1
    name: "User Service"
    description: "Independent microservice"
  
  - id: 2
    name: "Product Service"
    description: "Independent microservice"
```

**Example**: Microservices, where services are independent

### Pattern 3: Minimal Steps

Single step for simple scenarios:

```yaml
available_steps:
  - id: 1
    name: "Complete Application"
    description: "Build entire app in one step"
```

**Example**: Hello World, Simple API, Minimal viable product

---

## 💡 Best Practices

### Naming

✅ **DO**:
- Use lowercase with underscores: `ml_pipeline`, `graphql_api`
- Be descriptive: `microservices_ecommerce` not `ms`
- Use domain-specific terms: `blockchain_dapp` not `bc`

❌ **DON'T**:
- Use spaces: `my config` → `my_config`
- Use hyphens: `my-config` → `my_config`
- Be vague: `test`, `example`, `misc`

### Step Design

✅ **DO**:
- Keep steps focused (one clear goal)
- Make steps reusable
- Provide clear context in prompts
- Include technical constraints
- Specify deliverables

❌ **DON'T**:
- Make steps too large (split into sub-steps)
- Assume prior knowledge
- Leave requirements ambiguous
- Skip quality requirements

### Prompt Writing

✅ **DO**:
```
TASK: Create user authentication

Requirements:
1. JWT-based authentication
2. Password hashing with bcrypt
3. Endpoints: /login, /register, /logout

Technical Stack:
- FastAPI
- PostgreSQL
- SQLAlchemy

Deliverables:
- auth.py (authentication logic)
- test_auth.py (unit tests)
```

❌ **DON'T**:
```
Build authentication
```

### Versioning

- Use semantic versioning: `1.0.0`, `1.1.0`, `2.0.0`
- Increment:
  - **Major**: Breaking changes (incompatible)
  - **Minor**: New features (compatible)
  - **Patch**: Bug fixes (compatible)

---

## 📊 Example Config Sets

### Example 1: Machine Learning Pipeline

```
config_sets/ml_pipeline/
├── metadata.yaml
├── experiment_template.yaml
├── prompts/
│   ├── 01_data_collection.txt
│   ├── 02_data_preprocessing.txt
│   ├── 03_feature_engineering.txt
│   ├── 04_model_training.txt
│   ├── 05_model_evaluation.txt
│   └── 06_model_deployment.txt
└── hitl/
    └── expanded_spec.txt
```

### Example 2: GraphQL API

```
config_sets/graphql_api/
├── metadata.yaml
├── experiment_template.yaml
├── prompts/
│   ├── 01_schema_definition.txt
│   ├── 02_queries.txt
│   ├── 03_mutations.txt
│   └── 04_subscriptions.txt
└── hitl/
    └── expanded_spec.txt
```

### Example 3: Blockchain DApp

```
config_sets/blockchain_dapp/
├── metadata.yaml
├── experiment_template.yaml
├── prompts/
│   ├── 01_smart_contract.txt
│   ├── 02_contract_testing.txt
│   ├── 03_frontend_web3.txt
│   └── 04_deployment.txt
└── hitl/
    └── expanded_spec.txt
```

---

## 🧪 Testing Checklist

Before sharing your config set:

- [ ] All validation passes
- [ ] Generate experiment successfully
- [ ] All prompts load correctly
- [ ] Steps execute in correct order
- [ ] Results recorded properly
- [ ] HITL files accessible
- [ ] Documentation clear
- [ ] Example experiment works
- [ ] Edge cases handled
- [ ] Error messages helpful

---

## 🤝 Sharing Config Sets

### Internal Use

Just add to `config_sets/` directory:

```bash
git add config_sets/your_config_set/
git commit -m "Add your_config_set config set"
```

### External Sharing (Future)

V2 will support external config sets:

```bash
# Install from URL
python scripts/install_config_set.py \
  --url https://github.com/user/config-set-repo

# Use external config set
python scripts/new_experiment.py \
  --config-set-path /path/to/external/config_set \
  --name my_test
```

---

## 🐛 Troubleshooting

### Error: "metadata.yaml not found"

**Cause**: Missing metadata file

**Fix**:
```bash
cd config_sets/your_config_set/
touch metadata.yaml
# Add required content
```

### Error: "Prompt file not found"

**Cause**: Path mismatch between metadata and actual file

**Fix**: Check metadata.yaml references match actual files:
```yaml
# metadata.yaml
prompt_file: "prompts/01_step.txt"

# Must match actual file:
# config_sets/your_config_set/prompts/01_step.txt
```

### Error: "Duplicate step IDs"

**Cause**: Same ID used multiple times

**Fix**: Ensure unique IDs:
```yaml
available_steps:
  - id: 1  # ✅
  - id: 2  # ✅
  # Not: id: 1 again ❌
```

### Error: "Invalid prompt path in template"

**Cause**: Template uses wrong path prefix

**Fix**: Use `config/prompts/` in experiment_template.yaml:
```yaml
# ❌ Wrong
prompt_file: "prompts/01_step.txt"

# ✅ Correct
prompt_file: "config/prompts/01_step.txt"
```

---

## 📚 Reference

### metadata.yaml Schema

```yaml
name: string (required)
version: string (required, semver)
description: string (required)

available_steps: array (required)
  - id: integer (required, unique)
    name: string (required)
    prompt_file: string (required, path exists)
    description: string (required)

defaults: object (optional)
  timeout: object
    per_step: integer (seconds)
    total: integer (seconds)
  metrics: object
    weights: object
      [metric_name]: float (0-1)
```

### experiment_template.yaml Schema

```yaml
steps: array (required)
  - id: integer (required)
    enabled: boolean (required)
    name: string (required)
    prompt_file: string (required, starts with "config/prompts/")

timeouts: object (required)
  step_timeout_seconds: integer
  total_timeout_seconds: integer

metrics: object (required)
  weights: object
    [metric_name]: float (0-1)

stopping: object (required)
  confidence_level: float (0-1)
  min_runs: integer
  max_runs: integer
```

---

## 🎯 Summary

**Key Steps**:
1. Create directory structure
2. Write metadata.yaml
3. Write experiment_template.yaml
4. Create prompt files
5. Create HITL files
6. Validate
7. Test generation
8. Test execution

**Remember**:
- ✅ Use consistent naming
- ✅ Validate before sharing
- ✅ Test thoroughly
- ✅ Document clearly
- ✅ Follow best practices

**Questions?**
- Review existing config sets: `config_sets/default/`, `config_sets/minimal/`
- Check [QUICKSTART_CONFIG_SETS.md](QUICKSTART_CONFIG_SETS.md)
- See [FINAL-IMPLEMENTATION-PLAN.md](FINAL-IMPLEMENTATION-PLAN.md)

---

🚀 **Ready to create your first config set? Start with the directory structure and work through each step!**
