"""End-to-end tests for MCP workflows."""

import pytest
import pytest_asyncio
from httpx import Response
from unittest.mock import MagicMock

from gong_mcp.tools.analysis import analyze_calls, get_job_status
from gong_mcp.tools.calls import list_calls, search_calls


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDiscoveryWorkflow:
    """Test discovery workflow: List -> Search -> Analyze."""

    async def test_list_then_search_workflow(self, mock_httpx_client, sample_calls_list):
        """Test workflow: list calls, then search for specific ones."""
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response

        # Step 1: List calls
        listed = await list_calls(limit=5)
        assert len(listed["calls"]) > 0

        # Step 2: Search calls by email
        call_ids = [call["call_id"] for call in listed["calls"][:2]]
        searched = await search_calls(emails=["jane@acme.com"])
        assert "calls" in searched

    async def test_search_then_analyze_workflow(self, mock_httpx_client, sample_call_data, sample_transcript_data, monkeypatch, temp_jobs_dir):
        """Test workflow: search calls, then analyze them."""
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

        # Step 1: Search calls
        searched = await search_calls(emails=["jane@acme.com"])
        assert len(searched["calls"]) > 0

        # Step 2: Analyze the found calls
        call_ids = [call["call_id"] for call in searched["calls"]]
        analyzed = await analyze_calls(call_ids=call_ids, prompt="Analyze these calls")
        assert analyzed["mode"] == "direct" or analyzed["mode"] == "async"


@pytest.mark.e2e
@pytest.mark.asyncio
class TestAnalysisWorkflow:
    """Test analysis workflow: Analyze -> Poll Status -> Get Results."""

    async def test_async_analysis_workflow(self, mock_httpx_client, sample_call_data, sample_transcript_data, monkeypatch, temp_jobs_dir):
        """Test complete async analysis workflow."""
        monkeypatch.setenv("DIRECT_TOKEN_THRESHOLD", "1000")  # Force async mode
        
        # Create large transcript
        large_transcript = sample_transcript_data.copy()
        large_transcript["transcript"] = [
            {
                "speakerId": "speaker_1",
                "sentences": [{"start": i * 1000, "text": "x" * 1000} for i in range(100)]
            }
        ]
        
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
            json={"callTranscripts": [large_transcript]},
            request=MagicMock(),
        )
        mock_httpx_client.post.side_effect = [search_response, transcript_response]

        # Step 1: Start analysis (should return async mode)
        result = await analyze_calls(
            from_date="2024-01-01",
            to_date="2024-01-31",
            prompt="Analyze these calls"
        )

        assert result["mode"] == "async"
        job_id = result["job_id"]

        # Step 2: Check job status
        status = await get_job_status(job_id)
        assert status["job_id"] == job_id
        assert "status" in status

        # Note: In a real scenario, we would wait for completion and get results
        # For testing, we just verify the workflow structure


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCrossMCPSimulation:
    """Test cross-MCP synthesis scenarios."""

    async def test_email_filter_workflow(self, mock_httpx_client, sample_calls_list):
        """Test workflow simulating cross-MCP join via email filtering."""
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response

        # Simulate: Get emails from HubSpot/Salesforce MCP
        lead_emails = ["jane@acme.com", "john@example.com"]

        # Use those emails to find matching calls
        matching_calls = await search_calls(emails=lead_emails)

        assert "calls" in matching_calls
        assert "matched_emails" in matching_calls
        assert len(matching_calls["matched_emails"]) > 0

    async def test_domain_filter_workflow(self, mock_httpx_client, sample_calls_list):
        """Test workflow using domain filtering for cross-MCP joins."""
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response

        # Simulate: Get company domains from CRM
        company_domains = ["acme.com"]

        # Find all calls with participants from those domains
        matching_calls = await search_calls(domains=company_domains)

        assert "calls" in matching_calls
        assert matching_calls["filters_applied"]["domains"] == company_domains
