# Test Suite Implementation Guide

This guide provides step-by-step instructions for implementing the test suite for the Gong MCP Server.

## Prerequisites

1. **Python 3.10+** (required for the project)
2. **pytest** and related testing packages
3. **Understanding of async testing** in Python

## Step 1: Setup Test Dependencies

Add test dependencies to `pyproject.toml`:

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-httpx>=0.27.0",  # For mocking HTTP requests
    "freezegun>=1.4.0",  # For time-based testing
]
```

Install test dependencies:

```bash
uv sync --extra test
# or
pip install -e ".[test]"
```

## Step 2: Create Test Directory Structure

```bash
mkdir -p tests/{unit,integration,e2e,fixtures}
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py
touch tests/fixtures/__init__.py
```

## Step 3: Configure Pytest

Add pytest configuration to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = [
    "--strict-markers",
    "--cov=gong_mcp",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "-v",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow-running tests",
]
```

## Step 4: Implement Shared Fixtures

Copy `tests/conftest.py.example` to `tests/conftest.py` and customize:

1. **Review and adapt fixtures** for your specific needs
2. **Add more sample data** as needed
3. **Enhance mock responses** to match real API structures

Key fixtures to implement:
- `mock_env_vars` - Environment variable mocking
- `temp_jobs_dir` - Temporary job storage
- `sample_call_data` - Realistic call metadata
- `sample_transcript_data` - Transcript structures
- `mock_httpx_client` - HTTP client mocking

## Step 5: Implement Unit Tests

### Priority Order:

1. **Utils First** (easiest, no external dependencies)
   - `test_filters.py` - Email/domain filtering logic
   - `test_formatters.py` - Formatting functions
   - `test_router.py` - Routing decision logic

2. **Client Tests** (core functionality)
   - `test_gong_client.py` - API client (use example as template)

3. **Job Management** (file I/O)
   - `test_jobs.py` - Job state management

### Example: Starting with `test_filters.py`

```python
"""Test filtering utilities."""
import pytest
from gong_mcp.utils.filters import (
    filter_calls_by_emails,
    extract_external_emails,
    get_matching_call_ids,
)

@pytest.mark.unit
class TestFilterCallsByEmails:
    """Test filter_calls_by_emails function."""
    
    def test_filter_by_exact_email(self, sample_calls_list):
        """Test filtering by exact email match."""
        emails = ["jane@acme.com"]
        filtered, matched = filter_calls_by_emails(sample_calls_list, emails=emails)
        
        assert len(filtered) > 0
        assert "jane@acme.com" in matched
    
    # Add more test cases...
```

## Step 6: Implement Integration Tests

Integration tests verify that components work together:

1. **`test_tools_calls.py`** - Test call-related tools end-to-end
2. **`test_tools_participants.py`** - Test participant tools
3. **`test_tools_analysis.py`** - Test analysis workflow
4. **`test_server.py`** - Test MCP server integration

### Mocking Strategy for Integration Tests

- **Mock Gong API** at the HTTP level (use `pytest-httpx` or `responses`)
- **Mock Claude API** for analysis tests
- **Use real file I/O** for job management (with temp directories)

Example integration test structure:

```python
"""Integration tests for call tools."""
import pytest
from gong_mcp.tools.calls import list_calls, get_transcript, search_calls

@pytest.mark.integration
@pytest.mark.asyncio
class TestCallTools:
    """Test call-related MCP tools."""
    
    async def test_list_calls_default_range(self, mock_gong_api):
        """Test list_calls with default date range."""
        result = await list_calls()
        
        assert "calls" in result
        assert "total_count" in result
        assert "from_date" in result
        assert "to_date" in result
```

## Step 7: Implement End-to-End Tests

E2E tests simulate real user workflows:

1. **Discovery workflow**: List → Search → Get Transcript
2. **Analysis workflow**: Analyze → Poll Status → Get Results
3. **Cross-MCP simulation**: Email filtering → Batch analysis

These tests should:
- Use more realistic data
- Test error scenarios
- Verify complete workflows
- Be marked as `@pytest.mark.slow` if they take time

## Step 8: Add Test Markers

Use markers to organize and run specific test suites:

```python
@pytest.mark.unit
def test_something():
    """Unit test."""
    pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration():
    """Integration test."""
    pass

@pytest.mark.e2e
@pytest.mark.slow
async def test_workflow():
    """Slow E2E test."""
    pass
```

Run specific test suites:

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Step 9: Set Up CI/CD

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -e ".[test]"
      
      - name: Run tests
        run: |
          pytest --cov=gong_mcp --cov-report=xml
        env:
          GONG_ACCESS_KEY: test_key
          GONG_ACCESS_KEY_SECRET: test_secret
          ANTHROPIC_API_KEY: test_key
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Step 10: Test Coverage Goals

Aim for:
- **90%+ unit test coverage**
- **80%+ integration test coverage**
- **100% coverage** on critical paths:
  - Error handling
  - Authentication
  - Routing decisions
  - Job state transitions

Check coverage:

```bash
pytest --cov=gong_mcp --cov-report=html
# Open htmlcov/index.html in browser
```

## Step 11: Continuous Improvement

### Regular Tasks:

1. **Update tests when adding features**
   - Add tests for new functionality
   - Update existing tests if behavior changes

2. **Review coverage reports**
   - Identify untested code paths
   - Add tests for edge cases

3. **Refactor tests for clarity**
   - Keep tests readable and maintainable
   - Extract common patterns into fixtures

4. **Keep test data realistic**
   - Update sample data to match API changes
   - Test with various data shapes

## Common Testing Patterns

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

### Testing HTTP Requests

```python
import pytest_httpx

@pytest.mark.asyncio
async def test_api_call(httpx_mock):
    """Test API call with mocked HTTP."""
    httpx_mock.add_response(
        method="POST",
        url="https://api.gong.io/v2/calls/extensive",
        json={"calls": []},
    )
    
    async with GongClient() as client:
        result = await client.search_calls(...)
    
    assert result is not None
```

### Testing File I/O

```python
def test_file_operations(tmp_path):
    """Test file operations with temporary directory."""
    test_file = tmp_path / "test.json"
    test_file.write_text('{"key": "value"}')
    
    # Test your file operations
    data = json.loads(test_file.read_text())
    assert data["key"] == "value"
```

### Testing Time-Dependent Code

```python
from freezegun import freeze_time

@freeze_time("2024-01-15")
def test_time_dependent_function():
    """Test function that depends on current time."""
    result = function_that_uses_datetime_now()
    assert "2024-01-15" in result
```

## Troubleshooting

### Common Issues:

1. **Async test warnings**
   - Ensure `asyncio_mode = "auto"` in pytest config
   - Use `@pytest.mark.asyncio` decorator

2. **Import errors**
   - Check that `src/` is in Python path
   - Use `pip install -e .` for editable install

3. **Mock not working**
   - Verify mock is set up before the code runs
   - Check that you're mocking the right object

4. **Fixture not found**
   - Ensure fixtures are in `conftest.py`
   - Check fixture scope (function, class, module, session)

## Next Steps

1. Start with unit tests for utilities (filters, formatters)
2. Add client tests using the example as a template
3. Build up integration tests
4. Add E2E tests for critical workflows
5. Set up CI/CD
6. Monitor and improve coverage

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-httpx documentation](https://pytest-httpx.readthedocs.io/)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)
