# Paper Generation Test Suite

This directory contains tests for the camera-ready paper generation feature.

## Structure

- `test_*.py`: Unit and integration tests
- `fixtures/`: Test experiment data for testing paper generation

## Running Tests

```bash
# Run all paper generation tests
pytest tests/paper_generation/

# Run with coverage
pytest tests/paper_generation/ --cov=src/paper_generation --cov-report=html

# Run specific test file
pytest tests/paper_generation/test_paper_generator.py
```

## Test Organization

Tests are organized by phase matching the tasks.md structure:
- Phase 2: Foundational tests (exceptions, models, utilities)
- Phase 3: User Story 1 tests (full paper generation)
- Phase 4: User Story 2 tests (customization)
- Phase 5: User Story 3 tests (figure export)
- Phase 6: User Story 4 tests (README enhancement)
