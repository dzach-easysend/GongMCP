"""Unit tests for GongClient."""

import pytest
from httpx import HTTPStatusError

from gong_mcp.gong_client import GongClient, check_gong_config


@pytest.mark.unit
class TestCheckGongConfig:
    """Test check_gong_config helper."""

    def test_returns_none_when_both_keys_set(self, monkeypatch):
        """When both credentials are set, return None."""
        monkeypatch.setenv("GONG_ACCESS_KEY", "key")
        monkeypatch.setenv("GONG_ACCESS_KEY_SECRET", "secret")
        assert check_gong_config() is None

    def test_returns_error_when_access_key_missing(self, monkeypatch):
        """When GONG_ACCESS_KEY is missing, return error dict."""
        monkeypatch.delenv("GONG_ACCESS_KEY", raising=False)
        monkeypatch.setenv("GONG_ACCESS_KEY_SECRET", "secret")
        result = check_gong_config()
        assert result is not None
        assert "error" in result
        assert "GONG_ACCESS_KEY" in result["error"]

    def test_returns_error_when_secret_missing(self, monkeypatch):
        """When GONG_ACCESS_KEY_SECRET is missing, return error dict."""
        monkeypatch.setenv("GONG_ACCESS_KEY", "key")
        monkeypatch.delenv("GONG_ACCESS_KEY_SECRET", raising=False)
        result = check_gong_config()
        assert result is not None
        assert "error" in result
        assert "GONG_ACCESS_KEY_SECRET" in result["error"]

    def test_returns_error_when_both_missing(self, monkeypatch):
        """When both are missing, return error dict naming both."""
        monkeypatch.delenv("GONG_ACCESS_KEY", raising=False)
        monkeypatch.delenv("GONG_ACCESS_KEY_SECRET", raising=False)
        result = check_gong_config()
        assert result is not None
        assert "error" in result
        assert "GONG_ACCESS_KEY" in result["error"]
        assert "GONG_ACCESS_KEY_SECRET" in result["error"]

    def test_returns_error_when_keys_empty_or_whitespace(self, monkeypatch):
        """When keys are empty or whitespace, treat as missing."""
        monkeypatch.setenv("GONG_ACCESS_KEY", "  ")
        monkeypatch.setenv("GONG_ACCESS_KEY_SECRET", "")
        result = check_gong_config()
        assert result is not None
        assert "error" in result


@pytest.mark.unit
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
        # Context manager exits cleanly

    def test_client_property_raises_when_not_initialized(self):
        """Test that client property raises when not in context."""
        client = GongClient()
        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = client.client


@pytest.mark.unit
class TestGongClientSearchCalls:
    """Test search_calls method."""

    @pytest.mark.asyncio
    async def test_search_calls_success(self, mock_httpx_client, sample_calls_list):
        """Test successful call search."""
        # Reset and add custom response
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {
                    "cursor": None,
                    "currentPageSize": len(sample_calls_list),
                },
            },
        )

        async with GongClient() as client:
            result = await client.search_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z"
            )

        assert "calls" in result
        assert len(result["calls"]) == 5

    @pytest.mark.asyncio
    async def test_search_calls_with_pagination(self, mock_httpx_client):
        """Test call search with pagination cursor."""
        mock_httpx_client.reset()
        
        # First page
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [{"id": "call_1"}],
                "records": {
                    "cursor": "cursor_123",
                    "currentPageSize": 1,
                },
            },
        )
        
        # Second page
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": [{"id": "call_2"}],
                "records": {
                    "cursor": None,
                    "currentPageSize": 1,
                },
            },
        )

        async with GongClient() as client:
            result1 = await client.search_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z"
            )

            result2 = await client.search_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                cursor="cursor_123"
            )

        assert len(result1["calls"]) == 1
        assert len(result2["calls"]) == 1

    @pytest.mark.asyncio
    async def test_search_calls_http_error(self, mock_httpx_client):
        """Test handling of HTTP errors."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        async with GongClient() as client:
            with pytest.raises(HTTPStatusError):
                await client.search_calls(
                    from_date="2024-01-01T00:00:00Z",
                    to_date="2024-01-31T23:59:59Z"
                )


@pytest.mark.unit
class TestGongClientGetAllCalls:
    """Test get_all_calls method."""

    @pytest.mark.asyncio
    async def test_get_all_calls_single_page(self, mock_httpx_client, sample_calls_list):
        """Test getting all calls from a single page."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {
                    "cursor": None,
                    "currentPageSize": len(sample_calls_list),
                },
            },
        )

        async with GongClient() as client:
            calls = await client.get_all_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z"
            )

        assert len(calls) == 5

    @pytest.mark.asyncio
    async def test_get_all_calls_multiple_pages(self, mock_httpx_client):
        """Test pagination across multiple pages."""
        mock_httpx_client.reset()
        
        for i in range(3):
            cursor = f"cursor_{i}" if i < 2 else None
            mock_httpx_client.add_response(
                method="POST",
                url="https://api.gong.io/v2/calls/extensive",
                json={
                    "calls": [{"id": f"call_{i}", "metaData": {"started": f"2024-01-{i+1:02d}T00:00:00Z"}}],
                    "records": {
                        "cursor": cursor,
                        "currentPageSize": 1,
                    },
                },
            )

        async with GongClient() as client:
            calls = await client.get_all_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                max_pages=3
            )

        assert len(calls) == 3

    @pytest.mark.asyncio
    async def test_get_all_calls_respects_max_pages(self, mock_httpx_client):
        """Test that max_pages limit is respected."""
        mock_httpx_client.reset()
        
        # Add exactly max_pages responses (2)
        for i in range(2):
            mock_httpx_client.add_response(
                method="POST",
                url="https://api.gong.io/v2/calls/extensive",
                json={
                    "calls": [{"id": f"call_{i}", "metaData": {"started": "2024-01-01T00:00:00Z"}}],
                    "records": {
                        "cursor": "next_cursor" if i < 1 else None,  # Last one has no cursor
                        "currentPageSize": 1,
                    },
                },
            )

        async with GongClient() as client:
            calls = await client.get_all_calls(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                max_pages=2
            )

        # Should stop at max_pages
        assert len(calls) == 2


@pytest.mark.unit
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

        assert len(participants["internal"]) == 1
        assert participants["internal"][0]["name"] == "John Doe"

    def test_extract_participants_no_parties(self):
        """Test handling of calls with no parties."""
        call_data = {"parties": []}
        client = GongClient()
        participants = client.extract_participants(call_data)

        assert participants["internal"] == []
        assert participants["external"] == []


@pytest.mark.unit
class TestGongClientSearchCallsByEmails:
    """Test search_calls_by_emails method."""

    @pytest.mark.asyncio
    async def test_search_by_exact_email(self, mock_httpx_client, sample_calls_list):
        """Test filtering by exact email match."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        async with GongClient() as client:
            filtered = await client.search_calls_by_emails(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                emails=["jane@acme.com"]
            )

        assert isinstance(filtered, list)

    @pytest.mark.asyncio
    async def test_search_by_domain(self, mock_httpx_client, sample_calls_list):
        """Test filtering by email domain."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        async with GongClient() as client:
            filtered = await client.search_calls_by_emails(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z",
                domains=["acme.com"]
            )

        assert isinstance(filtered, list)

    @pytest.mark.asyncio
    async def test_search_no_emails_or_domains(self, mock_httpx_client, sample_calls_list):
        """Test that no filtering occurs when no emails/domains provided."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/extensive",
            json={
                "calls": sample_calls_list,
                "records": {"cursor": None, "currentPageSize": len(sample_calls_list)},
            },
        )

        async with GongClient() as client:
            filtered = await client.search_calls_by_emails(
                from_date="2024-01-01T00:00:00Z",
                to_date="2024-01-31T23:59:59Z"
            )

        assert len(filtered) == len(sample_calls_list)


@pytest.mark.unit
class TestGongClientGetCallTranscript:
    """Test get_call_transcript method."""

    @pytest.mark.asyncio
    async def test_get_call_transcript_success(self, mock_httpx_client, sample_transcript_data):
        """Test successful transcript retrieval."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [sample_transcript_data]},
        )

        async with GongClient() as client:
            transcript = await client.get_call_transcript("call_12345")

        assert transcript["callId"] == "call_12345"
        assert "transcript" in transcript

    @pytest.mark.asyncio
    async def test_get_call_transcript_no_transcript(self, mock_httpx_client):
        """Test handling when no transcript found."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": []},
        )

        async with GongClient() as client:
            transcript = await client.get_call_transcript("call_12345")

        assert "error" in transcript
        assert transcript["error"] == "No transcript found"

    @pytest.mark.asyncio
    async def test_get_multiple_transcripts(self, mock_httpx_client, sample_transcript_data):
        """Test getting multiple transcripts."""
        mock_httpx_client.reset()
        mock_httpx_client.add_response(
            method="POST",
            url="https://api.gong.io/v2/calls/transcript",
            json={"callTranscripts": [sample_transcript_data, sample_transcript_data]},
        )

        async with GongClient() as client:
            transcripts = await client.get_multiple_transcripts(["call_1", "call_2"])

        assert len(transcripts) == 2
