# Testing Guide for PM Analysis Tool

This document provides comprehensive information about the testing suite and quality assurance processes for the PM Analysis Tool.

## Overview

The PM Analysis Tool uses a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and end-to-end workflows
- **Performance Tests**: Ensure the tool can handle large files efficiently
- **Code Quality Checks**: Maintain consistent code style and quality

## Test Structure

```
tests/
├── conftest.py                 # Pytest fixtures and configuration
├── test_*.py                   # Unit test files (mirror source structure)
├── test_*_integration.py       # Integration test files
└── test_performance.py         # Performance and load tests
```

## Running Tests

### Quick Start

```bash
# Run all fast tests (excludes performance tests)
python scripts/run_tests.py --fast

# Run all tests including performance tests
python scripts/run_tests.py --all

# Run with coverage reporting
python scripts/run_tests.py --fast --coverage
```

### Test Categories

#### Unit Tests
Test individual components in isolation:
```bash
python scripts/run_tests.py --unit
```

#### Integration Tests
Test component interactions and workflows:
```bash
python scripts/run_tests.py --integration
```

#### Performance Tests
Test performance with large datasets:
```bash
python scripts/run_tests.py --performance
```

### Direct pytest Usage

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=utils --cov-report=html

# Run specific test file
pytest tests/test_engine.py

# Run tests with specific marker
pytest -m "not slow"

# Run in verbose mode
pytest -v

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Markers

The test suite uses pytest markers to categorize tests:

- `unit`: Unit tests (default for most tests)
- `integration`: Integration tests that test multiple components
- `slow`: Performance tests that may take longer to run
- `performance`: Alias for slow tests

## Code Coverage

The project maintains high code coverage standards:

- **Target**: 80% minimum coverage
- **Current**: 87% coverage
- **Reports**: Generated in `htmlcov/` directory

### Coverage Configuration

Coverage is configured in `pytest.ini`:
```ini
--cov=core
--cov=utils
--cov=processors
--cov=extractors
--cov=file_handlers
--cov=reporters
--cov-report=term-missing
--cov-report=html:htmlcov
--cov-fail-under=80
```

## Performance Testing

Performance tests ensure the tool can handle realistic workloads:

### Test Scenarios

1. **Large Excel Files**: 10,000+ rows
2. **Large Markdown Files**: 1,000+ sections
3. **Multiple Files**: Processing 5+ files simultaneously
4. **End-to-End**: Complete project analysis
5. **Memory Usage**: Memory efficiency checks

### Performance Thresholds

- Large Excel file processing: < 30 seconds
- Large Markdown file processing: < 15 seconds
- Multiple file processing: < 45 seconds
- End-to-end analysis: < 60 seconds
- Memory growth: < 500MB for large datasets

## Code Quality

### Tools Used

1. **Black**: Code formatting
2. **Flake8**: Linting and style checking
3. **isort**: Import sorting
4. **MyPy**: Type checking (optional)

### Running Quality Checks

```bash
# Check code quality
python scripts/quality_check.py

# Auto-format code
python scripts/format_code.py
```

### Configuration Files

- `pyproject.toml`: Black and isort configuration
- `.flake8`: Flake8 configuration
- `pytest.ini`: Pytest and coverage configuration

## Writing Tests

### Test File Structure

Each source module should have a corresponding test file:

```
core/engine.py          → tests/test_engine.py
utils/validators.py     → tests/test_validators.py
processors/status.py    → tests/test_status.py
```

### Test Class Structure

```python
class TestClassName:
    """Test cases for ClassName."""
    
    def test_method_name_scenario(self, fixture_name):
        """Test method_name with specific scenario."""
        # Arrange
        # Act
        # Assert
```

### Using Fixtures

Common fixtures are defined in `conftest.py`:

```python
def test_example(self, sample_risk, sample_config):
    """Test using predefined fixtures."""
    # Use sample_risk and sample_config in test
```

### Performance Test Guidelines

```python
@pytest.mark.slow
def test_performance_scenario(self):
    """Test performance with large dataset."""
    start_time = time.time()
    
    # Perform operation
    result = process_large_dataset()
    
    processing_time = time.time() - start_time
    
    # Assert performance threshold
    assert processing_time < 30.0
    assert result.success
```

## Continuous Integration

### Pre-commit Checks

Before committing code, run:

```bash
# Format code
python scripts/format_code.py

# Run quality checks
python scripts/quality_check.py

# Run fast tests
python scripts/run_tests.py --fast --coverage
```

### CI Pipeline

The CI pipeline should run:

1. Code quality checks
2. Unit tests with coverage
3. Integration tests
4. Performance tests (on schedule)

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the project root
cd "PM Assistant"

# Install dependencies
pip install -r requirements.txt
```

#### Coverage Issues
```bash
# Clear coverage cache
rm -rf .coverage htmlcov/

# Run tests with coverage
pytest --cov=core --cov-report=html
```

#### Performance Test Failures
```bash
# Run performance tests in isolation
pytest -m slow -v

# Check system resources
# Performance tests may fail on resource-constrained systems
```

### Test Data

Test data is managed through:
- Fixtures in `conftest.py`
- Temporary files created during tests
- Sample data in `tests/test_data/`

## Best Practices

1. **Test Naming**: Use descriptive test names that explain the scenario
2. **Test Independence**: Each test should be independent and not rely on others
3. **Fixtures**: Use fixtures for common test data and setup
4. **Assertions**: Use specific assertions with clear error messages
5. **Performance**: Mark slow tests appropriately
6. **Documentation**: Document complex test scenarios
7. **Cleanup**: Ensure tests clean up temporary resources

## Metrics and Reporting

### Test Metrics
- Total tests: 635+
- Test coverage: 87%
- Performance tests: 10+
- Average test execution time: < 10 seconds

### Reports Generated
- Coverage report: `htmlcov/index.html`
- Test results: Console output
- Performance metrics: Logged during performance tests

## Future Enhancements

Planned improvements to the testing suite:

1. **Mutation Testing**: Verify test quality
2. **Property-Based Testing**: Generate test cases automatically
3. **Load Testing**: Test with concurrent users
4. **Security Testing**: Validate input sanitization
5. **Compatibility Testing**: Test across Python versions