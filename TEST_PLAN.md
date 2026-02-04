# Gong MCP Server - Test Suite Plan

## Overview

This document outlines a comprehensive test suite for the Gong MCP Server, covering unit tests, integration tests, and end-to-end tests. The test suite follows Python best practices using pytest with async support.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/
│   ├── __init__.py
│   ├── test_gong_client.py
│   ├── test_filters.py
│   ├── test_formatters.py
│   ├── test_router.py
│   └── test_jobs.py
├── integration/
│   ├── __init__.py
│   ├── test_tools_calls.py
│   ├── test_tools_participants.py
│   ├── test_tools_analysis.py
│   └── test_server.py
├── e2e/
│   ├── __init__.py
│   └── test_mcp_workflows.py
└── fixtures/
    ├── __init__.py
    ├── gong_responses.py    # Mock Gong API responses
    └── sample_data.py       # Sample call/transcript data
```

## Test Categories

### 1. Unit Tests

#### 1.1 Gong Client (`test_gong_client.py`)
- **Authentication**
  - Client initialization with env vars
  - Client initialization with explicit credentials
  - Missing credentials handling
  - Context manager usage (`async with`)

- **API Methods**
  - `search_calls()` - Date range queries, pagination cursor handling
  - `get_all_calls()` - Pagination across multiple pages, max_pages limit
  - `get_call_transcript()` - Single call transcript retrieval
  - `get_multiple_transcripts()` - Batch transcript retrieval
  - `search_calls_by_emails()` - Email matching, domain matching, combined filters
  - `extract_participants()` - Internal/external categorization, noise filtering

- **Error Handling**
  - HTTP errors (4xx, 5xx)
  - Network timeouts
  - Invalid API responses
  - Missing data fields

#### 1.2 Filters (`test_filters.py`)
- **Email/Domain Filtering**
  - `filter_calls_by_emails()` - Exact email matching, domain matching, case insensitivity
  - `extract_external_emails()` - External participant extraction, deduplication
  - `get_matching_call_ids()` - ID extraction from filtered calls

- **Edge Cases**
  - Empty email/domain lists
  - Calls with no participants
  - Malformed email addresses
  - Domain matching with/without @ prefix

#### 1.3 Formatters (`test_formatters.py`)
- **Duration Formatting**
  - `format_duration()` - Hours, minutes, seconds formatting, zero/negative handling

- **Timestamp Formatting**
  - `format_timestamp()` - MM:SS and HH:MM:SS formats

- **Date Formatting**
  - `format_iso_date()` - ISO string parsing, timezone handling, invalid format handling

- **Transcript Building**
  - `build_transcript_text()` - Text format with/without timestamps, speaker mapping
  - `build_transcript_json()` - JSON structure, metadata extraction, conversation ordering

#### 1.4 Router (`test_router.py`)
- **Token Estimation**
  - `estimate_tokens()` - Character-to-token conversion
  - `estimate_transcripts_tokens()` - Multiple transcript aggregation

- **Routing Decision**
  - `should_use_direct_mode()` - Threshold comparison, configurable threshold
  - `get_routing_decision()` - Direct mode decision, async mode decision, metadata generation

- **Batch Estimation**
  - `estimate_batch_count()` - Token-based batch calculation
  - `estimate_processing_time()` - Time estimation from batch count

#### 1.5 Jobs (`test_jobs.py`)
- **Job Management**
  - `generate_job_id()` - Unique ID generation
  - `create_job()` - Initial status creation
  - `save_job_status()` / `load_job_status()` - File persistence
  - `update_job_progress()` - Progress calculation, status updates
  - `complete_job()` - Completion marking, results saving
  - `fail_job()` - Error state handling

- **Job Results**
  - `get_job_results()` - Results file loading
  - `list_jobs()` - Job listing, sorting, filtering

- **Background Tasks**
  - `run_job_in_background()` - Task registration
  - `is_job_running()` - Running state tracking

### 2. Integration Tests

#### 2.1 Call Tools (`test_tools_calls.py`)
- **list_calls**
  - Default date range (7 days)
  - Custom date ranges
  - Limit enforcement
  - Participant metadata extraction
  - Empty result handling

- **get_transcript**
  - Text format output
  - JSON format output
  - Call not found handling
  - Missing transcript handling
  - Wide date range search for call lookup

- **search_calls**
  - Text query filtering
  - Email filtering
  - Domain filtering
  - Combined filters
  - Default date range (30 days)
  - Matched emails tracking

#### 2.2 Participant Tools (`test_tools_participants.py`)
- **get_call_participants**
  - Multiple call IDs
  - Participant extraction
  - Found/not found tracking
  - Empty input handling

#### 2.3 Analysis Tools (`test_tools_analysis.py`)
- **analyze_calls**
  - Direct mode (small dataset)
  - Async mode (large dataset)
  - Call ID filtering
  - Email/domain filtering
  - Date range filtering
  - No calls found handling
  - Routing decision integration

- **get_job_status**
  - Pending status
  - Running status with progress
  - Complete status
  - Error status
  - Non-existent job handling

- **get_job_results**
  - Completed job results
  - Incomplete job handling
  - Missing results file handling

#### 2.4 Server (`test_server.py`)
- **Tool Registration**
  - All tools registered
  - Correct tool schemas
  - Tool descriptions

- **Tool Handling**
  - Correct tool routing
  - Argument parsing
  - Error handling and formatting
  - JSON response format

### 3. End-to-End Tests

#### 3.1 MCP Workflows (`test_mcp_workflows.py`)
- **Discovery Workflow**
  - List calls → Get transcript → Analyze
  - Search by email → Get participants → Analyze filtered set

- **Cross-MCP Simulation**
  - Email list input → Search calls → Filter analysis
  - Domain filtering → Batch analysis

- **Analysis Workflow**
  - Small dataset → Direct mode → Inline analysis
  - Large dataset → Async mode → Job polling → Results retrieval

- **Error Recovery**
  - API failures → Retry logic
  - Job failures → Error state handling

## Test Fixtures and Mocks

### Fixtures (`conftest.py`)
- **Gong API Mock**
  - `mock_gong_client` - Mocked httpx.AsyncClient
  - `mock_gong_responses` - Sample API responses
  - `mock_gong_error_responses` - Error scenarios

- **Sample Data**
  - `sample_call_data` - Realistic call metadata
  - `sample_transcript_data` - Transcript structures
  - `sample_participants` - Participant lists

- **Job Management**
  - `temp_jobs_dir` - Temporary directory for job files
  - `sample_job_status` - Job status examples

- **Environment**
  - `mock_env_vars` - Environment variable mocking
  - `cleanup_jobs` - Test cleanup fixture

### Mock Responses (`fixtures/gong_responses.py`)
- Paginated call lists
- Single call metadata
- Transcript data (various formats)
- Error responses (400, 401, 429, 500, 529)
- Empty results

## Testing Tools and Dependencies

### Required Packages
```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "httpx>=0.27.0",  # For mocking HTTP requests
    "freezegun>=1.4.0",  # For time-based testing
]
```

### Configuration (`pytest.ini` or `pyproject.toml`)
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
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow-running tests",
]
```

## Test Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: 80%+ coverage
- **Critical Paths**: 100% coverage
  - Error handling
  - Authentication
  - Routing decisions
  - Job state transitions

## Test Execution

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage
pytest --cov=gong_mcp --cov-report=html

# Specific test file
pytest tests/unit/test_gong_client.py

# Specific test
pytest tests/unit/test_gong_client.py::test_search_calls_pagination
```

### CI/CD Integration
- Run tests on every PR
- Require 85%+ coverage
- Run slow tests only on main branch
- Parallel test execution

## Mock Strategy

### Gong API Mocking
- Use `httpx.AsyncClient` with `responses` library or `pytest-httpx`
- Mock all external API calls
- Provide realistic response structures
- Test error scenarios (rate limits, timeouts, errors)

### Claude API Mocking
- Mock Anthropic API calls in analysis runner
- Simulate rate limiting (429, 529)
- Test retry logic
- Verify cost calculations

### File System
- Use temporary directories for job files
- Cleanup after tests
- Test file permission scenarios

## Special Test Scenarios

### 1. Rate Limiting
- Test 429 response handling
- Test retry-after header parsing
- Test exponential backoff

### 2. Large Datasets
- Test pagination with 100+ calls
- Test token estimation accuracy
- Test batch creation logic

### 3. Edge Cases
- Empty date ranges
- Invalid date formats
- Missing optional fields
- Unicode in transcripts
- Very long transcripts

### 4. Concurrent Operations
- Multiple simultaneous job requests
- Concurrent API calls
- Job status polling during execution

## Performance Tests (Optional)

- API call latency
- Batch processing throughput
- Memory usage with large datasets
- Job file I/O performance

## Documentation Tests

- Docstring examples (doctest)
- README code examples
- API documentation accuracy

## Test Data Management

- Use fixtures for consistent test data
- Generate realistic but synthetic data
- Avoid hardcoding real API keys
- Use environment variable mocking

## Maintenance

- Update tests when adding features
- Review coverage reports regularly
- Refactor tests for clarity
- Keep test data up to date with API changes
