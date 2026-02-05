"""End-to-end tests for MCP workflows."""

import pytest

from gong_mcp.tools.analysis import analyze_calls, get_job_status
from gong_mcp.tools.calls import list_calls, search_calls


@pytest.mark.e2e
@pytest.mark.asyncio
class TestDiscoveryWorkflow:
    """Test discovery workflow: List -> Search -> Analyze."""

    async def test_list_then_search_workflow(self, mock_httpx_client, sample_calls_list):
        """Test workflow: list calls, then search for specific ones."""
        mock_httpx_client.reset()
        # Add responses for both calls
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        # Step 1: List calls
        listed = await list_calls(limit=5)
        assert len(listed["calls"]) > 0

        # Step 2: Search calls by email
        searched = await search_calls(emails=["jane@acme.com"])
        assert "calls" in searched

    async def test_search_then_analyze_workflow(self, mock_httpx_client, sample_call_data, sample_transcript_data, monkeypatch, temp_jobs_dir):
        """Test workflow: search calls, then analyze them."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K
        
        mock_httpx_client.reset()
        # Search response
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
        )
        # Analyze response (calls)
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
        )
        # Analyze response (transcript)
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [sample_transcript_data]},
        )

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
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "1")  # 1K - very low to trigger async
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")  # required for async path

        large_transcript = sample_transcript_data.copy()
        large_transcript["transcript"] = [
            {
                "speakerId": "speaker_1",
                "sentences": [{"start": i * 1000, "text": "x" * 1000} for i in range(100)]
            }
        ]
        
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
        )
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [large_transcript]},
        )
        # Async job runs in background and calls Anthropic API
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.anthropic.com/v1/messages",
            json={
                "content": [{"text": "E2E analysis result"}],
                "usage": {"input_tokens": 1000, "output_tokens": 50},
            },
        )

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


@pytest.mark.e2e
@pytest.mark.asyncio
class TestCrossMCPSimulation:
    """Test cross-MCP synthesis scenarios."""

    async def test_email_filter_workflow(self, mock_httpx_client, sample_calls_list):
        """Test workflow simulating cross-MCP join via email filtering."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        # Simulate: Get emails from HubSpot/Salesforce MCP
        lead_emails = ["jane@acme.com", "john@example.com"]

        # Use those emails to find matching calls
        matching_calls = await search_calls(emails=lead_emails)

        assert "calls" in matching_calls
        assert "matched_emails" in matching_calls

    async def test_domain_filter_workflow(self, mock_httpx_client, sample_calls_list):
        """Test workflow using domain filtering for cross-MCP joins."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        # Simulate: Get company domains from CRM
        company_domains = ["acme.com"]

        # Find all calls with participants from those domains
        matching_calls = await search_calls(domains=company_domains)

        assert "calls" in matching_calls
        assert matching_calls["filters_applied"]["domains"] == company_domains
