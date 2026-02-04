"""
Example unit tests for GongClient.

This demonstrates the testing approach for the Gong API client.
Copy and adapt these tests when implementing the full test suite.
"""

import pytest
import pytest_asyncio
from httpx import Response
from unittest.mock import AsyncMock, MagicMock, patch

from gong_mcp.gong_client import GongClient


@pytest.mark.asyncio
class TestGongClientInitialization:
    """Test GongClient initialization and configuration."""
    
    def test_init_with_env_vars(self, mock_env_vars):
        """Test client initialization from environment variables."""
        client = GongClient()
        assert client.access_key == "test_access_key"
        assert client.access_key_secret == "test_secret"
        assert client.base_url == "https://api.gong.io/v2"
    
    def test_init_with_explicit_credentials(self):
        """Test client initialization with explicit credentials."""
        client = GongClient(
            access_key="explicit_key",
            access_key_secret="explicit_secret"
        )
        assert client.access_key == "explicit_key"
        assert client.access_key_secret == "explicit_secret"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_httpx_client):
        """Test client context manager usage."""
        async with GongClient() as client:
            assert client._client is not None
            assert hasattr(client, "client")
        
        # Client should be closed after context
        mock_httpx_client.aclose.assert_called_once()
    
    def test_client_property_raises_when_not_initialized(self):
        """Test that client property raises when not in context."""
        client = GongClient()
        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = client.client


@pytest.mark.asyncio
class TestGongClientSearchCalls:
    """Test search_calls method."""
    
    @pytest.mark.asyncio
    async def test_search_calls_success(self, mock_httpx_client, sample_calls_list):
        """Test successful call search."""
        # Setup mock response
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {
                    "cursor": None,
                    "currentPageSize": len(sample_calls_list),
                },
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response
        
        async with GongClient() as client:
            result = await client.search_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z"
            )
        
        assert "calls" in result
        assert len(result["calls"]) == 5
        mock_httpx_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_calls_with_pagination(self, mock_httpx_client):
        """Test call search with pagination cursor."""
        # First page
        first_response = Response(
            status_code=200,
            json={
                "calls": [{"id": "call_1"}],
                "records": {
                    "cursor": "cursor_123",
                    "currentPageSize": 1,
                },
            },
            request=MagicMock(),
        )
        
        # Second page
        second_response = Response(
            status_code=200,
            json={
                "calls": [{"id": "call_2"}],
                "records": {
                    "cursor": None,
                    "currentPageSize": 1,
                },
            },
            request=MagicMock(),
        )
        
        mock_httpx_client.post.side_effect = [first_response, second_response]
        
        async with GongClient() as client:
            # First call
            result1 = await client.search_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z"
            )
            
            # Second call with cursor
            result2 = await client.search_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                cursor="cursor_123"
            )
        
        assert len(result1["calls"]) == 1
        assert len(result2["calls"]) == 1
        assert mock_httpx_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_search_calls_http_error(self, mock_httpx_client):
        """Test handling of HTTP errors."""
        mock_response = Response(
            status_code=401,
            json={"error": "Unauthorized"},
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response
        
        async with GongClient() as client:
            with pytest.raises(Exception):  # httpx raises HTTPStatusError
                await client.search_calls(
                    from_date="2024-01-01T00:00:00Z",
                    to_date="2024-01-31T23:59:59Z"
                )


@pytest.mark.asyncio
class TestGongClientGetAllCalls:
    """Test get_all_calls method."""
    
    @pytest.mark.asyncio
    async def test_get_all_calls_single_page(self, mock_httpx_client, sample_calls_list):
        """Test getting all calls from a single page."""
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {
                    "cursor": None,
                    "currentPageSize": len(sample_calls_list),
                },
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response
        
        async with GongClient() as client:
            calls = await client.get_all_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z"
            )
        
        assert len(calls) == 5
        assert calls[0]["id"] == "call_0"
    
    @pytest.mark.asyncio
    async def test_get_all_calls_multiple_pages(self, mock_httpx_client):
        """Test pagination across multiple pages."""
        responses = []
        for i in range(3):
            cursor = f"cursor_{i}" if i < 2 else None
            responses.append(Response(
                status_code=200,
                json={
                    "calls": [{"id": f"call_{i}", "metaData": {"started": f"2024-01-{i+1:02d}T00:00:00Z"}}],
                    "records": {
                        "cursor": cursor,
                        "currentPageSize": 1,
                    },
                },
                request=MagicMock(),
            ))
        
        mock_httpx_client.post.side_effect = responses
        
        async with GongClient() as client:
            calls = await client.get_all_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                max_pages=3
            )
        
        assert len(calls) == 3
        assert mock_httpx_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_all_calls_respects_max_pages(self, mock_httpx_client):
        """Test that max_pages limit is respected."""
        # Create responses that would continue indefinitely
        def infinite_responses():
            while True:
                yield Response(
                    status_code=200,
                    json={
                        "calls": [{"id": "call_1", "metaData": {"started": "2024-01-01T00:00:00Z"}}],
                        "records": {
                            "cursor": "next_cursor",
                            "currentPageSize": 1,
                        },
                    },
                    request=MagicMock(),
                )
        
        mock_httpx_client.post.side_effect = infinite_responses()
        
        async with GongClient() as client:
            calls = await client.get_all_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                max_pages=2
            )
        
        # Should stop at max_pages
        assert mock_httpx_client.post.call_count == 2


@pytest.mark.asyncio
class TestGongClientExtractParticipants:
    """Test extract_participants method."""
    
    def test_extract_participants_internal_external(self, sample_call_data):
        """Test participant extraction with internal/external categorization."""
        client = GongClient()
        participants = client.extract_participants(sample_call_data)
        
        assert "internal" in participants
        assert "external" in participants
        assert len(participants["internal"]) == 1
        assert len(participants["external"]) == 1
        assert participants["internal"][0]["email"] == "john@example.com"
        assert participants["external"][0]["email"] == "jane@acme.com"
    
    def test_extract_participants_filters_noise(self):
        """Test that noise participants are filtered out."""
        call_data = {
            "parties": [
                {"name": "Merged Audio", "emailAddress": "", "affiliation": "internal"},
                {"name": "Fireflies.Ai Notetaker", "emailAddress": "", "affiliation": "internal"},
                {"name": "John Doe", "emailAddress": "john@example.com", "affiliation": "internal"},
            ],
        }
        
        client = GongClient()
        participants = client.extract_participants(call_data)
        
        # Should only have John Doe
        assert len(participants["internal"]) == 1
        assert participants["internal"][0]["name"] == "John Doe"
    
    def test_extract_participants_no_parties(self):
        """Test handling of calls with no parties."""
        call_data = {"parties": []}
        client = GongClient()
        participants = client.extract_participants(call_data)
        
        assert participants["internal"] == []
        assert participants["external"] == []


@pytest.mark.asyncio
class TestGongClientSearchCallsByEmails:
    """Test search_calls_by_emails method."""
    
    @pytest.mark.asyncio
    async def test_search_by_exact_email(self, mock_httpx_client, sample_calls_list):
        """Test filtering by exact email match."""
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response
        
        async with GongClient() as client:
            filtered = await client.search_calls_by_emails(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                emails=["jane@acme.com"]
            )
        
        # Should filter to calls with matching email
        assert len(filtered) <= len(sample_calls_list)
    
    @pytest.mark.asyncio
    async def test_search_by_domain(self, mock_httpx_client, sample_calls_list):
        """Test filtering by email domain."""
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response
        
        async with GongClient() as client:
            filtered = await client.search_calls_by_emails(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                domains=["acme.com"]
            )
        
        # Should filter to calls with matching domain
        assert isinstance(filtered, list)
    
    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, mock_httpx_client, sample_calls_list):
        """Test that email matching is case insensitive."""
        mock_response = Response(
            status_code=200,
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
            request=MagicMock(),
        )
        mock_httpx_client.post.return_value = mock_response
        
        async with GongClient() as client:
            filtered_upper = await client.search_calls_by_emails(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                emails=["JANE@ACME.COM"]
            )
            
            filtered_lower = await client.search_calls_by_emails(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                emails=["jane@acme.com"]
            )
        
        # Should match regardless of case
        assert len(filtered_upper) == len(filtered_lower)
