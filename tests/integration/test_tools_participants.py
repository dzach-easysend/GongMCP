"""Integration tests for participant tools."""

import pytest

from gong_mcp.tools.participants import get_call_participants


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetCallParticipants:
    """Test get_call_participants tool."""

    async def test_get_call_participants_single_call(self, mock_httpx_client, sample_call_data):
        """Test getting participants for a single call."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
        )

        result = await get_call_participants(["call_12345"])

        assert "participants_by_call" in result
        assert "call_12345" in result["participants_by_call"]
        assert result["found_count"] == 1
        assert result["not_found_count"] == 0

    async def test_get_call_participants_multiple_calls(self, mock_httpx_client, sample_call_data):
        """Test getting participants for multiple calls."""
        calls = [sample_call_data.copy() for _ in range(3)]
        for i, call in enumerate(calls):
            call["id"] = f"call_{i}"

        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": calls,
                "records": {"cursor": None, "currentPageSize": len(calls)},
            },
        )

        result = await get_call_participants(["call_0", "call_1", "call_2"])

        assert result["found_count"] == 3
        assert len(result["participants_by_call"]) == 3

    async def test_get_call_participants_not_found(self, mock_httpx_client):
        """Test getting participants for non-existent calls."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={"calls": [], "records": {"cursor": None, "currentPageSize": 0}},
        )

        result = await get_call_participants(["nonexistent_call"])

        assert result["found_count"] == 0
        assert result["not_found_count"] == 1
        assert "nonexistent_call" in result["not_found_call_ids"]

    async def test_get_call_participants_mixed(self, mock_httpx_client, sample_call_data):
        """Test getting participants for mix of found and not found calls."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
        )

        result = await get_call_participants(["call_12345", "nonexistent_call"])

        assert result["found_count"] == 1
        assert result["not_found_count"] == 1
        assert "call_12345" in result["participants_by_call"]
        assert "nonexistent_call" in result["not_found_call_ids"]

    async def test_get_call_participants_empty_list(self, mock_httpx_client):
        """Test getting participants with empty call IDs list."""
        result = await get_call_participants([])

        assert "error" in result
        assert result["participants_by_call"] == {}

    async def test_get_call_participants_structure(self, mock_httpx_client, sample_call_data):
        """Test that participant structure is correct."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [sample_call_data],
                "records": {"cursor": None, "currentPageSize": 1},
            },
        )

        result = await get_call_participants(["call_12345"])

        participants = result["participants_by_call"]["call_12345"]
        assert "internal" in participants
        assert "external" in participants
        assert isinstance(participants["internal"], list)
        assert isinstance(participants["external"], list)
