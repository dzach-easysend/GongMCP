# Test Suite

Comprehensive test suite for the Gong MCP Server.

## Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_filters.py
│   ├── test_formatters.py
│   ├── test_router.py
│   ├── test_gong_client.py
│   └── test_jobs.py
├── integration/             # Integration tests
│   ├── test_tools_calls.py
│   ├── test_tools_participants.py
│   └── test_tools_analysis.py
└── e2e/                     # End-to-end tests
    └── test_mcp_workflows.py
```

## Running Tests

### Install Test Dependencies

```bash
uv sync --extra test
# or
pip install -e ".[test]"
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# E2E tests only
pytest tests/e2e/ -m e2e
```

### Run with Coverage

```bash
pytest --cov=gong_mcp --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Test File

```bash
pytest tests/unit/test_filters.py
```

### Run Specific Test

```bash
pytest tests/unit/test_filters.py::TestFilterCallsByEmails::test_filter_by_exact_email
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

## Test Coverage

Current test coverage includes:

- **Unit Tests**: Filters, formatters, router, gong_client, jobs
- **Integration Tests**: All MCP tools (calls, participants, analysis)
- **E2E Tests**: Complete workflows and cross-MCP scenarios

## Writing New Tests

1. **Unit Tests**: Test individual functions/classes in isolation
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test complete user workflows

Use fixtures from `conftest.py` for common test data and mocks.

## Fixtures Available

- `mock_env_vars` - Environment variable mocking
- `temp_jobs_dir` - Temporary directory for job files
- `sample_call_data` - Sample call metadata
- `sample_transcript_data` - Sample transcript data
- `sample_calls_list` - List of sample calls
- `mock_httpx_client` - Mocked HTTP client
- `sample_job_status` - Sample job status
- `sample_job_results` - Sample job results

## Notes

- All async tests use `@pytest.mark.asyncio`
- Tests are marked with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.e2e`
- Use `mock_httpx_client` to mock Gong API calls
- Use `temp_jobs_dir` for job file tests
