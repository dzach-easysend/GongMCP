"""
Call-related MCP tools.

Provides list_calls, get_transcript, and search_calls functionality.
"""

from datetime import datetime, timedelta

from ..gong_client import GongClient, check_gong_config
from ..utils.filters import filter_calls_by_emails
from ..utils.formatters import build_transcript_json, build_transcript_text


async def list_calls(
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50,
) -> dict:
    """
    List Gong calls in a date range.

    Args:
        from_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        to_date: End date (YYYY-MM-DD). Defaults to today.
        limit: Maximum number of calls to return.

    Returns:
        Dict with calls list and metadata.
    """
    gong_error = check_gong_config()
    if gong_error:
        return gong_error

    # Default date range: last 7 days
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Convert to ISO format
    from_datetime = f"{from_date}T00:00:00Z"
    to_datetime = f"{to_date}T23:59:59Z"

    async with GongClient() as client:
        calls = await client.get_all_calls(from_datetime, to_datetime)

    # Limit results
    calls = calls[:limit]

    # Format output with participant metadata
    formatted_calls = []
    for call in calls:
        metadata = call.get("metaData", {})
        participants = client.extract_participants(call)

        formatted_calls.append({
            "call_id": metadata.get("id", ""),
            "title": metadata.get("title", "Untitled"),
            "date": metadata.get("started", ""),
            "duration_seconds": metadata.get("duration", 0),
            "participants": participants,
            "primary_user_id": metadata.get("primaryUserId", ""),
        })

    return {
        "calls": formatted_calls,
        "total_count": len(formatted_calls),
        "from_date": from_date,
        "to_date": to_date,
    }


async def get_transcript(
    call_id: str,
    format: str = "text",
) -> dict:
    """
    Get the full transcript for a specific call.

    Args:
        call_id: The Gong call ID.
        format: Output format - "text" or "json".

    Returns:
        Dict with transcript content.
    """
    gong_error = check_gong_config()
    if gong_error:
        return gong_error

    async with GongClient() as client:
        # Fetch transcript directly by call_id - no need to search through all calls
        transcript_data = await client.get_call_transcript(call_id)

        if "error" in transcript_data:
            return {"error": transcript_data["error"]}

        # Build minimal call_data for formatters (they need metaData structure)
        call_data = {
            "metaData": {"id": call_id},
            "parties": []
        }

        if format == "json":
            return build_transcript_json(call_data, transcript_data)
        else:
            return {
                "call_id": call_id,
                "transcript": build_transcript_text(call_data, transcript_data),
            }


async def search_calls(
    query: str | None = None,
    emails: list[str] | None = None,
    domains: list[str] | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50,
) -> dict:
    """
    Search for calls by text query OR participant emails/domains.

    This is critical for cross-MCP synthesis - use emails to find calls
    with specific leads from HubSpot, Salesforce, etc.

    Args:
        query: Text search query (searches title).
        emails: List of participant email addresses to match.
        domains: List of email domains to match (e.g., ['acme.com']).
        from_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
        to_date: End date (YYYY-MM-DD). Defaults to today.
        limit: Maximum number of calls to return.

    Returns:
        Dict with matching calls and metadata.
    """
    gong_error = check_gong_config()
    if gong_error:
        return gong_error

    # Default date range: last 30 days for search
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    from_datetime = f"{from_date}T00:00:00Z"
    to_datetime = f"{to_date}T23:59:59Z"

    async with GongClient() as client:
        all_calls = await client.get_all_calls(from_datetime, to_datetime)

    # Apply filters
    filtered_calls = all_calls
    matched_emails = []

    # Email/domain filtering (for cross-MCP joins)
    if emails or domains:
        filtered_calls, matched_emails = filter_calls_by_emails(
            filtered_calls, emails, domains
        )

    # Text query filtering
    if query:
        query_lower = query.lower()
        filtered_calls = [
            c for c in filtered_calls
            if query_lower in c.get("metaData", {}).get("title", "").lower()
        ]

    # Limit results
    filtered_calls = filtered_calls[:limit]

    # Format output with participant metadata
    formatted_calls = []
    for call in filtered_calls:
        metadata = call.get("metaData", {})
        participants = GongClient().extract_participants(call)

        formatted_calls.append({
            "call_id": metadata.get("id", ""),
            "title": metadata.get("title", "Untitled"),
            "date": metadata.get("started", ""),
            "duration_seconds": metadata.get("duration", 0),
            "participants": participants,
            "primary_user_id": metadata.get("primaryUserId", ""),
        })

    return {
        "calls": formatted_calls,
        "total_count": len(formatted_calls),
        "matched_emails": matched_emails,
        "from_date": from_date,
        "to_date": to_date,
        "filters_applied": {
            "query": query,
            "emails": emails,
            "domains": domains,
        },
    }
