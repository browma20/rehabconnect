# RehabConnect Backend Tests

This directory contains comprehensive unit tests for the RehabConnect backend application.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_models.py          # Model unit tests
├── test_services.py        # Service layer unit tests
├── test_compliance_engines.py  # Compliance engine unit tests
├── test_risk_engine.py     # Risk engine unit tests
├── __init__.py
├── pytest.ini             # Pytest configuration
├── requirements-test.txt  # Test dependencies
└── run_tests.py          # Test runner script
```

## Test Coverage

### Models (`test_models.py`)
- **Patient**: Creation, validation, relationships, constraints
- **TherapySession**: Session creation, relationships, optional fields
- **PhysicianEvaluation**: Evaluation creation, compliance tracking

### Services (`test_services.py`)
- **PatientService**: CRUD operations, validation, error handling
- **TherapyMinutesService**: Session recording, daily calculations
- **PhysicianEvaluationService**: Evaluation creation, compliance checking

### Compliance Engines (`test_compliance_engines.py`)
- **Three Hour Rule Engine**: Daily minutes, 7-day rolling intensity, missed minutes documentation
- **First Day Engine**: Physician evaluation within 24 hours
- **IDT Engine**: Weekly interdisciplinary team meetings
- **Functional Improvement Engine**: Regular functional assessments

### Risk Engine (`test_risk_engine.py`)
- **Risk Scoring**: Composite risk calculation, category classification
- **Risk Utils**: Status conversion, documentation completeness, survey readiness

## Running Tests

### Prerequisites
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test Types
```bash
# Unit tests only
python run_tests.py unit

# Models only
python run_tests.py models

# Services only
python run_tests.py services

# Engines only
python run_tests.py engines
```

### Run with Coverage
```bash
python run_tests.py --coverage
```

### Using pytest Directly
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_models.py::TestPatient

# Run specific test method
pytest tests/test_models.py::TestPatient::test_patient_creation

# Run with coverage
pytest --cov=app --cov-report=html
```

## Test Database

Tests use an in-memory SQLite database for isolation and speed. The `conftest.py` file provides:

- `engine`: SQLAlchemy engine for in-memory database
- `tables`: Database schema creation
- `db_session`: Database session fixture
- `sample_patient_data`: Sample patient data
- `sample_patient`: Pre-created patient instance
- `sample_therapy_session`: Pre-created therapy session

## Test Conventions

- **Naming**: `test_*` for functions, `Test*` for classes
- **Structure**: Arrange-Act-Assert pattern
- **Isolation**: Each test is independent with fresh database
- **Fixtures**: Use pytest fixtures for common setup
- **Assertions**: Clear, descriptive assertions
- **Coverage**: Aim for high coverage of business logic

## Adding New Tests

1. **For Models**: Add test class in `test_models.py`
2. **For Services**: Add test class in `test_services.py`
3. **For Engines**: Add test class in `test_compliance_engines.py` or `test_risk_engine.py`
4. **Fixtures**: Add to `conftest.py` if reusable across tests
5. **Dependencies**: Add to `requirements-test.txt` if needed

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd backend
    pip install -r requirements-test.txt
    python run_tests.py --coverage
```

## Test Quality Metrics

- **Coverage**: Target >90% for business logic
- **Performance**: Tests should complete in <30 seconds
- **Reliability**: No flaky tests, deterministic results
- **Maintainability**: Clear test names and documentation