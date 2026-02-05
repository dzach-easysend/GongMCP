"""Integration tests for call-related tools."""

import pytest

from gong_mcp.tools.calls import get_transcript, list_calls, search_calls


@pytest.mark.integration
@pytest.mark.asyncio
class TestListCalls:
    """Test list_calls tool."""

    async def test_list_calls_default_range(self, mock_httpx_client, sample_calls_list):
        """Test list_calls with default date range."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await list_calls()

        assert "calls" in result
        assert "total_count" in result
        assert "from_date" in result
        assert "to_date" in result
        assert result["total_count"] > 0

    async def test_list_calls_custom_date_range(self, mock_httpx_client, sample_calls_list):
        """Test list_calls with custom date range."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await list_calls(
            from_date="2024-01-01",
            to_date="2024-01-31",
            limit=10
        )

        assert result["from_date"] == "2024-01-01"
        assert result["to_date"] == "2024-01-31"
        assert len(result["calls"]) <= 10

    async def test_list_calls_returns_error_when_gong_keys_missing(self, monkeypatch):
        """When Gong credentials are missing, return informative error (no API call)."""
        monkeypatch.delenv("GONG_ACCESS_KEY", raising=False)
        monkeypatch.delenv("GONG_ACCESS_KEY_SECRET", raising=False)

        result = await list_calls(from_date="2024-01-01", to_date="2024-01-31")

        assert "error" in result
        assert "GONG_ACCESS_KEY" in result["error"]
        assert "calls" not in result

    async def test_list_calls_limit(self, mock_httpx_client, sample_calls_list):
        """Test that list_calls respects limit."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list * 2,
                "records": {"cursor": None, "currentPageSize": 10},
            },
        )

        result = await list_calls(limit=3)

        assert len(result["calls"]) == 3
        assert result["total_count"] == 3

    async def test_list_calls_participant_metadata(self, mock_httpx_client, sample_calls_list):
        """Test that list_calls includes participant metadata."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await list_calls()

        assert len(result["calls"]) > 0
        call = result["calls"][0]
        assert "participants" in call
        assert "internal" in call["participants"]
        assert "external" in call["participants"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetTranscript:
    """Test get_transcript tool."""

    async def test_get_transcript_returns_error_when_gong_keys_missing(self, monkeypatch):
        """When Gong credentials are missing, return informative error (no API call)."""
        monkeypatch.delenv("GONG_ACCESS_KEY", raising=False)
        monkeypatch.delenv("GONG_ACCESS_KEY_SECRET", raising=False)

        result = await get_transcript("call_12345")

        assert "error" in result
        assert "GONG_ACCESS_KEY" in result["error"]

    async def test_get_transcript_text_format(self, mock_httpx_client, sample_call_data, sample_transcript_data):
        """Test get_transcript with text format."""
        mock_httpx_client.reset()
        # Only mock transcript endpoint - no longer needs to list all calls first
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [sample_transcript_data]},
        )

        result = await get_transcript("call_12345", format="text")

        assert "call_id" in result
        assert "transcript" in result
        assert isinstance(result["transcript"], str)

    async def test_get_transcript_json_format(self, mock_httpx_client, sample_call_data, sample_transcript_data):
        """Test get_transcript with JSON format."""
        mock_httpx_client.reset()
        # Only mock transcript endpoint - no longer needs to list all calls first
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [sample_transcript_data]},
        )

        result = await get_transcript("call_12345", format="json")

        assert "metadata" in result
        assert "conversation" in result

    async def test_get_transcript_call_not_found(self, mock_httpx_client):
        """Test get_transcript when call not found."""
        mock_httpx_client.reset()
        # Mock transcript endpoint returning no transcripts
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": []},
        )

        result = await get_transcript("nonexistent_call")

        assert "error" in result

    async def test_get_transcript_fetches_directly_without_listing_all_calls(
        self, mock_httpx_client, sample_transcript_data
    ):
        """
        REGRESSION TEST: Verify get_transcript fetches transcript directly by call_id.
        
        This test would have caught the pagination bug where the old implementation:
        1. Fetched ALL calls from 2020 to present (hitting pagination limits)
        2. Searched through results to find the target call
        3. Failed when target call was beyond the 2000-call pagination limit
        
        The fix: Fetch transcript directly using the /calls/transcript endpoint
        which accepts call_id without needing to find the call first.
        """
        mock_httpx_client.reset()
        
        # IMPORTANT: We do NOT mock /calls/extensive - this verifies the code
        # no longer calls that endpoint. If it did, the test would fail with
        # an unexpected request error.
        
        # Only mock the transcript endpoint (the correct direct approach)
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [sample_transcript_data]},
        )

        result = await get_transcript("call_12345", format="text")

        # Should succeed by fetching transcript directly
        assert "error" not in result
        assert "transcript" in result
        assert result["call_id"] == "call_12345"

    async def test_get_transcript_handles_pagination_edge_case(
        self, mock_httpx_client, sample_transcript_data
    ):
        """
        REGRESSION TEST: Simulates the real-world scenario that caused the bug.
        
        Scenario: User has 3000+ calls in Gong. The target call exists but would
        be beyond page 20 (2000 calls limit) if we tried to list all calls first.
        
        Old behavior: Would return "Call not found" despite the call existing.
        New behavior: Fetches transcript directly, bypassing the listing entirely.
        """
        mock_httpx_client.reset()
        
        # Mock a call that exists in Gong but would be beyond pagination limits
        target_call_id = "5010460356281153960"  # Real call ID from production bug
        
        transcript_for_target = sample_transcript_data.copy()
        transcript_for_target["callId"] = target_call_id
        
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [transcript_for_target]},
        )

        result = await get_transcript(target_call_id, format="text")

        # Should succeed - the transcript endpoint works directly with call_id
        assert "error" not in result
        assert result["call_id"] == target_call_id
        assert "transcript" in result


@pytest.mark.integration
@pytest.mark.asyncio
class TestSearchCalls:
    """Test search_calls tool."""

    async def test_search_calls_returns_error_when_gong_keys_missing(self, monkeypatch):
        """When Gong credentials are missing, return informative error (no API call)."""
        monkeypatch.delenv("GONG_ACCESS_KEY", raising=False)
        monkeypatch.delenv("GONG_ACCESS_KEY_SECRET", raising=False)

        result = await search_calls(from_date="2024-01-01", to_date="2024-01-31")

        assert "error" in result
        assert "GONG_ACCESS_KEY" in result["error"]
        assert "calls" not in result

    async def test_search_calls_by_query(self, mock_httpx_client, sample_calls_list):
        """Test search_calls with text query."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await search_calls(query="Call")

        assert "calls" in result
        assert "filters_applied" in result
        assert result["filters_applied"]["query"] == "Call"

    async def test_search_calls_by_email(self, mock_httpx_client, sample_calls_list):
        """Test search_calls with email filter."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await search_calls(emails=["jane@acme.com"])

        assert "calls" in result
        assert "matched_emails" in result
        assert result["filters_applied"]["emails"] == ["jane@acme.com"]

    async def test_search_calls_by_domain(self, mock_httpx_client, sample_calls_list):
        """Test search_calls with domain filter."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await search_calls(domains=["acme.com"])

        assert "calls" in result
        assert result["filters_applied"]["domains"] == ["acme.com"]

    async def test_search_calls_combined_filters(self, mock_httpx_client, sample_calls_list):
        """Test search_calls with combined filters."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await search_calls(
            query="Call",
            emails=["jane@acme.com"],
            domains=["acme.com"],
            limit=5
        )

        assert "calls" in result
        assert result["filters_applied"]["query"] == "Call"
        assert result["filters_applied"]["emails"] == ["jane@acme.com"]
        assert result["filters_applied"]["domains"] == ["acme.com"]
        assert len(result["calls"]) <= 5

    async def test_search_calls_default_date_range(self, mock_httpx_client, sample_calls_list):
        """Test search_calls with default date range (30 days)."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        result = await search_calls()

        assert "from_date" in result
        assert "to_date" in result
