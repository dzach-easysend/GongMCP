"""
Gong API Client

Async client for Gong API v2 with email/participant filtering support.
Adapted from GongWebApp with cross-MCP synthesis enhancements.
"""

import os
from typing import Optional

import httpx


def check_gong_config() -> dict | None:
    """
    Return an error dict if Gong API credentials are missing.

    Use at the start of any tool that calls the Gong API so callers get
    a clear message instead of a failed request.

    Returns:
        Dict with "error" key and message if config is invalid, else None.
    """
    access_key = (os.getenv("GONG_ACCESS_KEY") or "").strip()
    secret = (os.getenv("GONG_ACCESS_KEY_SECRET") or "").strip()
    if not access_key or not secret:
        missing = []
        if not access_key:
            missing.append("GONG_ACCESS_KEY")
        if not secret:
            missing.append("GONG_ACCESS_KEY_SECRET")
        return {
            "error": (
                f"Gong API credentials not configured: {', '.join(missing)} must be set. "
                "Add them in your MCP client config or environment (see README)."
            )
        }
    return None


class GongClient:
    """Async client for Gong API v2."""

    def __init__(
        self,
        access_key: str | None = None,
        access_key_secret: str | None = None,
    ):
        self.access_key = access_key or os.getenv("GONG_ACCESS_KEY", "")
        self.access_key_secret = access_key_secret or os.getenv("GONG_ACCESS_KEY_SECRET", "")
        self.base_url = "https://api.gong.io/v2"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            auth=(self.access_key, self.access_key_secret),
            timeout=60.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with GongClient()' context.")
        return self._client

    async def search_calls(
        self,
        from_date: str,
        to_date: str,
        cursor: Optional[str] = None,
    ) -> dict:
        """
        Search for calls in date range with pagination.

        Args:
            from_date: ISO format datetime string
            to_date: ISO format datetime string
            cursor: Pagination cursor from previous response

        Returns:
            API response with calls and pagination info
        """
        url = f"{self.base_url}/calls/extensive"

        data = {
            "filter": {
                "fromDateTime": from_date,
                "toDateTime": to_date,
            },
            "contentSelector": {
                "exposedFields": {
                    "parties": True,
                }
            },
            "limit": 100,
        }

        if cursor:
            data["cursor"] = cursor

        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    async def get_all_calls(
        self,
        from_date: str,
        to_date: str,
        max_pages: int = 20,
    ) -> list[dict]:
        """
        Fetch all calls in date range with automatic pagination.

        Args:
            from_date: ISO format datetime string
            to_date: ISO format datetime string
            max_pages: Safety limit for pagination

        Returns:
            List of all calls in the date range
        """
        all_calls = []
        cursor = None

        for _ in range(max_pages):
            response = await self.search_calls(from_date, to_date, cursor)
            calls = response.get("calls", [])

            if not calls:
                break

            all_calls.extend(calls)

            records = response.get("records", {})
            cursor = records.get("cursor")
            current_page_size = records.get("currentPageSize", len(calls))

            if not cursor or current_page_size == 0:
                break

        # Sort by date descending (most recent first)
        all_calls.sort(
            key=lambda x: x.get("metaData", {}).get("started", ""),
            reverse=True,
        )

        return all_calls

    async def get_call_transcript(self, call_id: str) -> dict:
        """
        Get transcript for a specific call.

        Args:
            call_id: Gong call ID

        Returns:
            Transcript data or error dict
        """
        url = f"{self.base_url}/calls/transcript"

        data = {"filter": {"callIds": [call_id]}}

        response = await self.client.post(url, json=data)
        response.raise_for_status()
        result = response.json()

        if "callTranscripts" in result:
            transcripts = result["callTranscripts"]
            if transcripts and len(transcripts) > 0:
                return transcripts[0]
            return {"error": "No transcript found"}
        return {"error": "Unexpected response format"}

    async def get_multiple_transcripts(self, call_ids: list[str]) -> list[dict]:
        """
        Get transcripts for multiple calls.

        Args:
            call_ids: List of Gong call IDs

        Returns:
            List of transcript data
        """
        url = f"{self.base_url}/calls/transcript"

        data = {"filter": {"callIds": call_ids}}

        response = await self.client.post(url, json=data)
        response.raise_for_status()
        result = response.json()

        return result.get("callTranscripts", [])

    async def search_calls_by_emails(
        self,
        from_date: str,
        to_date: str,
        emails: list[str] | None = None,
        domains: list[str] | None = None,
    ) -> list[dict]:
        """
        Search calls filtered by participant emails or domains.

        Since Gong API doesn't support direct email filtering,
        we fetch all calls and filter client-side.

        Args:
            from_date: ISO format datetime string
            to_date: ISO format datetime string
            emails: List of email addresses to match
            domains: List of email domains to match (e.g., ['acme.com'])

        Returns:
            Filtered list of calls
        """
        all_calls = await self.get_all_calls(from_date, to_date)

        if not emails and not domains:
            return all_calls

        # Normalize for matching
        email_set = {e.lower() for e in (emails or [])}
        domain_set = {d.lower().lstrip("@") for d in (domains or [])}

        filtered = []
        for call in all_calls:
            parties = call.get("parties", [])
            for party in parties:
                email = party.get("emailAddress", "").lower()
                if not email:
                    continue

                # Match by exact email
                if email in email_set:
                    filtered.append(call)
                    break

                # Match by domain
                if "@" in email:
                    email_domain = email.split("@")[1]
                    if email_domain in domain_set:
                        filtered.append(call)
                        break

        return filtered

    def extract_participants(self, call: dict) -> dict:
        """
        Extract and categorize participants from a call.

        Args:
            call: Call data from Gong API

        Returns:
            Dict with 'internal' and 'external' participant lists
        """
        parties = call.get("parties", [])
        internal = []
        external = []

        for party in parties:
            name = party.get("name", party.get("emailAddress", "Unknown"))
            email = party.get("emailAddress", "")
            affiliation = party.get("affiliation", "").lower()

            # Skip noise
            if name in ["Merged Audio", "Fireflies.Ai Notetaker", "Fireflies.ai Notetaker"]:
                continue
            if "Fireflies" in name and "Notetaker" in name:
                continue

            participant = {"name": name, "email": email}

            if affiliation == "internal":
                internal.append(participant)
            else:
                external.append(participant)

        return {"internal": internal, "external": external}
