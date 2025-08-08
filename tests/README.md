# Test Suite Documentation

This directory contains the comprehensive test suite for the Math Buddy Backend application.

## Test Organization

The test suite is organized into the following modules:

### `test_database.py`
- **Purpose**: Tests database connectivity and connection methods
- **Covers**: SQLAlchemy connections, direct psycopg connections, SSL configurations, hostname resolution
- **Original files**: `test_db_connection.py`, `test_connection_methods.py`, `test_psycopg_direct.py`

### `test_auth.py`
- **Purpose**: Tests authentication and OAuth2 functionality
- **Covers**: OAuth2 token endpoints, JSON login, protected endpoints, FastAPI docs integration
- **Original files**: `test_oauth2_auth.py`

### `test_imports.py`
- **Purpose**: Tests module imports and dependency loading
- **Covers**: All app modules, third-party packages, environment variables
- **Original files**: `test_imports.py`

### `test_db_init.py`
- **Purpose**: Tests database initialization and schema setup
- **Covers**: Table creation, schema integrity, foreign keys, constraints
- **Original files**: `test_init_db.py`

## Running Tests

### Prerequisites
Install test dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage
```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_database.py

# Run specific test class
python -m pytest tests/test_database.py::TestDatabaseConnection

# Run specific test method
python -m pytest tests/test_database.py::TestDatabaseConnection::test_sqlalchemy_connection
```

### Using the Test Runner Script
```bash
# Run all tests
python run_tests.py

# Run only unit tests (fast)
python run_tests.py --type unit

# Run integration tests (requires running server)
python run_tests.py --type integration

# Run database tests only
python run_tests.py --type database

# Run authentication tests only
python run_tests.py --type auth

# Install dependencies and run tests
python run_tests.py --install
```

### Test Markers

Tests are organized with markers for selective running:

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (require running server)
- `@pytest.mark.database` - Database connection tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.slow` - Slow running tests

Run tests by marker:
```bash
# Run only unit tests
python -m pytest -m "unit"

# Run tests except slow ones
python -m pytest -m "not slow"

# Run database and auth tests
python -m pytest -m "database or auth"
```

## Test Configuration

### Environment Variables
Tests require the following environment variables (usually in `.env` file):
- `DATABASE_URL` - Database connection string

### Test Data
- Tests use fixture-based test data defined in `conftest.py`
- Default test user credentials: `test@example.com` / `testpassword`
- Tests will skip if required data is not available

### Test Database
- Tests use the same database as the application
- Tests are designed to be non-destructive
- Some tests may skip if database schema is not set up

## Continuous Integration

The test suite is designed to work in CI environments:

```bash
# CI-friendly test run
python -m pytest --tb=short --disable-warnings
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and the app modules are importable
2. **Database Connection**: Check that `DATABASE_URL` is set and the database is accessible
3. **Authentication Tests**: Require either a running server or test user in database
4. **Skipped Tests**: Many tests will skip gracefully if prerequisites are not met

### Test Dependencies
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `httpx` - HTTP client for FastAPI testing
- `requests` - HTTP client for integration tests
- `python-dotenv` - Environment variable loading

## Migration from Old Tests

The original test files have been consolidated:
- `test_db_connection.py` → `tests/test_database.py`
- `test_connection_methods.py` → `tests/test_database.py`  
- `test_psycopg_direct.py` → `tests/test_database.py`
- `test_oauth2_auth.py` → `tests/test_auth.py`
- `test_imports.py` → `tests/test_imports.py` (enhanced)
- `test_init_db.py` → `tests/test_db_init.py` (enhanced)
- `test_sqlalchemy.py` → `tests/test_database.py` (was empty)

You can safely remove the old test files after verifying the new test suite works correctly.
