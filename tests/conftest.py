"""
Pytest configuration and shared fixtures for Gong MCP Server tests.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from httpx import Response


# ============================================================================
# Environment and Configuration Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def _gong_config_for_tests(monkeypatch):
    """Set dummy Gong credentials so tools pass check_gong_config() unless a test explicitly unsets them."""
    monkeypatch.setenv("GONG_ACCESS_KEY", "test_access_key")
    monkeypatch.setenv("GONG_ACCESS_KEY_SECRET", "test_secret")


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GONG_ACCESS_KEY", "test_access_key")
    monkeypatch.setenv("GONG_ACCESS_KEY_SECRET", "test_secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
    monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K tokens
    yield
    # Cleanup handled by monkeypatch


@pytest.fixture
def temp_jobs_dir(tmp_path, monkeypatch):
    """Create a temporary directory for job files."""
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()
    monkeypatch.setenv("GONG_MCP_JOBS_DIR", str(jobs_dir))
    return jobs_dir


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_call_data():
    """Sample call data from Gong API."""
    return {
        "metaData": {
            "id": "call_12345",  # ID is inside metaData per Gong API
            "title": "Sales Call with Acme Corp",
            "started": "2024-01-15T10:30:00Z",
            "duration": 1800,  # 30 minutes
            "primaryUserId": "user_123",
        },
        "parties": [
            {
                "name": "John Doe",
                "emailAddress": "john@example.com",
                "affiliation": "internal",
                "speakerId": "speaker_1",
            },
            {
                "name": "Jane Smith",
                "emailAddress": "jane@acme.com",
                "affiliation": "external",
                "speakerId": "speaker_2",
            },
        ],
    }


@pytest.fixture
def sample_transcript_data():
    """Sample transcript data from Gong API."""
    return {
        "callId": "call_12345",
        "transcript": [
            {
                "speakerId": "speaker_1",
                "sentences": [
                    {
                        "start": 0,
                        "text": "Hello, thanks for joining the call today.",
                    },
                    {
                        "start": 3000,
                        "text": "Let's discuss your requirements.",
                    },
                ],
            },
            {
                "speakerId": "speaker_2",
                "sentences": [
                    {
                        "start": 5000,
                        "text": "Thanks for reaching out. We're looking for a solution.",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_calls_list(sample_call_data):
    """List of sample calls for pagination testing."""
    import copy
    calls = []
    for i in range(5):
        call = copy.deepcopy(sample_call_data)  # Deep copy to avoid shared references
        call["metaData"]["id"] = f"call_{i}"  # ID is inside metaData
        call["metaData"]["title"] = f"Call {i}"
        calls.append(call)
    return calls


# ============================================================================
# Mock HTTP Client Fixtures
# ============================================================================

@pytest.fixture
def mock_httpx_client(httpx_mock):
    """Mock httpx requests using pytest-httpx.
    
    This fixture properly intercepts all HTTP calls made by httpx.AsyncClient.
    Tests should add their own mock responses using httpx_mock.add_response().
    """
    # Configure to allow unused responses (some tests may not use all mocked responses)
    httpx_mock.reset()
    # Allow responses to be registered but not necessarily used
    # This is useful when tests conditionally make API calls
    return httpx_mock


@pytest.fixture
def mock_gong_responses(sample_call_data, sample_transcript_data):
    """Mock Gong API responses."""
    return {
        "calls_extensive": {
            "calls": [sample_call_data],
            "records": {
                "cursor": None,
                "currentPageSize": 1,
            },
        },
        "transcript": {
            "callTranscripts": [sample_transcript_data],
        },
        "empty_calls": {
            "calls": [],
            "records": {
                "cursor": None,
                "currentPageSize": 0,
            },
        },
    }


# ============================================================================
# Job Management Fixtures
# ============================================================================

@pytest.fixture
def sample_job_status():
    """Sample job status for testing."""
    return {
        "job_id": "job_20240115_103000",
        "status": "running",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:35:00",
        "call_count": 10,
        "estimated_batches": 2,
        "estimated_minutes": 3,
        "prompt": "Analyze these calls",
        "current_batch": 1,
        "total_batches": 2,
        "progress_percent": 50,
        "cost_so_far": 0.05,
        "message": "Processing batch 1/2",
    }


@pytest.fixture
def sample_job_results():
    """Sample job results for testing."""
    return {
        "job_id": "job_20240115_103000",
        "total_calls": 10,
        "total_batches": 2,
        "total_cost": 0.10,
        "prompt_used": "Analyze these calls",
        "batch_results": [
            {
                "batch_num": 1,
                "calls_count": 5,
                "analysis": "Analysis results for batch 1",
            },
            {
                "batch_num": 2,
                "calls_count": 5,
                "analysis": "Analysis results for batch 2",
            },
        ],
    }


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_jobs(temp_jobs_dir):
    """Clean up job files after each test."""
    yield
    # Cleanup handled by tmp_path fixture


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_response(status_code: int, json_data: dict = None) -> Response:
    """Create a mock HTTP response."""
    return Response(
        status_code=status_code,
        json=json_data or {},
        request=MagicMock(),
    )


def load_fixture(filename: str) -> dict:
    """Load a JSON fixture file."""
    fixture_path = Path(__file__).parent / "fixtures" / filename
    if fixture_path.exists():
        with open(fixture_path) as f:
            return json.load(f)
    return {}
