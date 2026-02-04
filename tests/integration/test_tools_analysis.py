"""Integration tests for analysis tools."""

import pytest
import pytest_asyncio
from httpx import Response
from unittest.mock import MagicMock, patch

from gong_mcp.tools.analysis import analyze_calls, get_job_results, get_job_status


@pytest.mark.integration
@pytest.mark.asyncio
class TestAnalyzeCalls:
    """Test analyze_calls tool."""

    async def test_analyze_calls_direct_mode(self, mock_httpx_client, sample_call_data, sample_transcript_data, monkeypatch):
        """Test analyze_calls with small dataset (direct mode)."""
        monkeypatch.setenv("DIRECT_TOKEN_THRESHOLD", "150000")
        
        # Mock search calls
        search_response = Response(
            status_code=200,
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
            request=MagicMock(),
        )
        # Mock transcript
        transcript_response = Response(
            status_code=200,
            json={"callTranscripts": [sample_transcript_data]},
            request=MagicMock(),
        )
        mock_httpx_client.post.side_effect = [search_response, transcript_response]

        result = await analyze_calls(
            from_date="2024-01-01",
            to_date="2024-01-31",
            prompt="Analyze these calls"
        )

        assert result["mode"] == "direct"
        assert "transcripts" in result
        assert "call_count" in result
        assert "total_tokens" in result

    async def test_analyze_calls_async_mode(self, mock_httpx_client, sample_call_data, sample_transcript_data, monkeypatch, temp_jobs_dir):
        """Test analyze_calls with large dataset (async mode)."""
        monkeypatch.setenv("DIRECT_TOKEN_THRESHOLD", "1000")  # Low threshold to force async
        
        # Create large transcript
        large_transcript = sample_transcript_data.copy()
        large_transcript["transcript"] = [
            {
                "speakerId": "speaker_1",
                "sentences": [{"start": i * 1000, "text": "x" * 1000} for i in range(100)]
            }
        ]
        
        # Mock search calls
        search_response = Response(
            status_code=200,
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
            request=MagicMock(),
        )
        # Mock transcript
        transcript_response = Response(
            status_code=200,
            json={"callTranscripts": [large_transcript]},
            request=MagicMock(),
        )
        mock_httpx_client.post.side_effect = [search_response, transcript_response]

        result = await analyze_calls(
            from_date="2024-01-01",
            to_date="2024-01-31",
            prompt="Analyze these calls"
        )

        assert result["mode"] == "async"
        assert "job_id" in result
        assert "estimated_batches" in result
        assert "estimated_minutes" in result

    async def test_analyze_calls_with_call_ids(self, mock_httpx_client, sample_call_data, sample_transcript_data, monkeypatch):
        """Test analyze_calls with specific call IDs."""
        monkeypatch.setenv("DIRECT_TOKEN_THRESHOLD", "150000")
        
        search_response = Response(
            status_code=200,
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
            request=MagicMock(),
        )
        transcript_response = Response(
            status_code=200,
            json={"callTranscripts": [sample_transcript_data]},
            request=MagicMock(),
        )
        mock_httpx_client.post.side_effect = [search_response, transcript_response]

        result = await analyze_calls(
            call_ids=["call_12345"],
            prompt="Analyze"
        )

        assert result["mode"] == "direct"
        assert result["call_count"] == 1

    async def test_analyze_calls_no_calls_found(self, mock_httpx_client):
        """Test analyze_calls when no calls match criteria."""
        mock_response = Response(
            status_code=200,
            json={"calls": [], "records": {"cursor": None, "currentPageSize": 0}},
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response

        result = await analyze_calls(
            from_date="2024-01-01",
            to_date="2024-01-31"
        )

        assert result["mode"] == "error"
        assert "error" in result
        assert "No calls found" in result["error"]


@pytest.mark.integration
class TestGetJobStatus:
    """Test get_job_status tool."""

    @pytest.mark.asyncio
    async def test_get_job_status_pending(self, temp_jobs_dir):
        """Test getting status for pending job."""
        from gong_mcp.analysis.jobs import create_job, generate_job_id
        
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )

        result = await get_job_status(job_id)

        assert result["job_id"] == job_id
        assert result["status"] == "pending"
        assert result["progress_percent"] == 0

    @pytest.mark.asyncio
    async def test_get_job_status_running(self, temp_jobs_dir):
        """Test getting status for running job."""
        from gong_mcp.analysis.jobs import create_job, generate_job_id, update_job_progress
        
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=4,
            estimated_minutes=5,
            prompt="Test",
        )
        update_job_progress(job_id, current_batch=2, total_batches=4, message="Processing...")

        result = await get_job_status(job_id)

        assert result["status"] == "running"
        assert result["progress_percent"] == 50
        assert result["current_batch"] == 2
        assert result["total_batches"] == 4

    @pytest.mark.asyncio
    async def test_get_job_status_complete(self, temp_jobs_dir):
        """Test getting status for completed job."""
        from gong_mcp.analysis.jobs import complete_job, create_job, generate_job_id
        
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )
        results = {"job_id": job_id, "total_calls": 10, "total_batches": 2, "total_cost": 0.10, "batch_results": []}
        complete_job(job_id, results, total_cost=0.10)

        result = await get_job_status(job_id)

        assert result["status"] == "complete"
        assert result["progress_percent"] == 100

    @pytest.mark.asyncio
    async def test_get_job_status_nonexistent(self, temp_jobs_dir):
        """Test getting status for non-existent job."""
        result = await get_job_status("nonexistent_job")

        assert "error" in result
        assert "not found" in result["error"].lower()


@pytest.mark.integration
class TestGetJobResults:
    """Test get_job_results tool."""

    @pytest.mark.asyncio
    async def test_get_job_results_complete(self, temp_jobs_dir):
        """Test getting results for completed job."""
        from gong_mcp.analysis.jobs import complete_job, create_job, generate_job_id
        
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )
        results = {
            "job_id": job_id,
            "total_calls": 10,
            "total_batches": 2,
            "total_cost": 0.10,
            "batch_results": [{"batch_num": 1, "analysis": "Test analysis"}],
        }
        complete_job(job_id, results, total_cost=0.10)

        result = await get_job_results(job_id)

        assert result["status"] == "complete"
        assert result["total_calls"] == 10
        assert result["total_batches"] == 2
        assert "batch_results" in result

    @pytest.mark.asyncio
    async def test_get_job_results_incomplete(self, temp_jobs_dir):
        """Test getting results for incomplete job."""
        from gong_mcp.analysis.jobs import create_job, generate_job_id
        
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )

        result = await get_job_results(job_id)

        assert "error" in result
        assert "not complete" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_job_results_nonexistent(self, temp_jobs_dir):
        """Test getting results for non-existent job."""
        result = await get_job_results("nonexistent_job")

        assert "error" in result
        assert "not found" in result["error"].lower()
