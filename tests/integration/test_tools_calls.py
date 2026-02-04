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

    async def test_get_transcript_text_format(self, mock_httpx_client, sample_call_data, sample_transcript_data):
        """Test get_transcript with text format."""
        mock_httpx_client.reset()
        # Mock search calls response
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
        )
        # Mock transcript response
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [sample_transcript_data]},
        )

        result = await get_transcript("call_12345", format="text")

        assert "call_id" in result
        assert "transcript" in result
        assert isinstance(result["transcript"], str)
        assert "Sales Call" in result["transcript"]

    async def test_get_transcript_json_format(self, mock_httpx_client, sample_call_data, sample_transcript_data):
        """Test get_transcript with JSON format."""
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
            json={"callTranscripts": [sample_transcript_data]},
        )

        result = await get_transcript("call_12345", format="json")

        assert "metadata" in result
        assert "participants" in result
        assert "conversation" in result

    async def test_get_transcript_call_not_found(self, mock_httpx_client):
        """Test get_transcript when call not found."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={"calls": [], "records": {"cursor": None, "currentPageSize": 0}},
        )

        result = await get_transcript("nonexistent_call")

        assert "error" in result
        assert "not found" in result["error"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestSearchCalls:
    """Test search_calls tool."""

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
