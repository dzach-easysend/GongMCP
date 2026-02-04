"""
Participant lookup tool for cross-MCP join validation.
"""

from datetime import datetime

from ..gong_client import GongClient


async def get_call_participants(
    call_ids: list[str],
) -> dict:
    """
    Get participant info for multiple calls.

    This is a lightweight alternative to fetching full transcripts.
    Useful for validating cross-MCP joins before running analysis.

    Args:
        call_ids: List of Gong call IDs.

    Returns:
        Dict mapping call_id to participant info.
    """
    if not call_ids:
        return {"error": "No call IDs provided", "participants_by_call": {}}

    async with GongClient() as client:
        # Fetch all calls (we need to search to get participant data)
        from_datetime = "2020-01-01T00:00:00Z"
        to_datetime = datetime.now().strftime("%Y-%m-%dT23:59:59Z")

        all_calls = await client.get_all_calls(from_datetime, to_datetime)

        # Build lookup
        call_lookup = {call.get("id"): call for call in all_calls}

        # Extract participants for requested calls
        participants_by_call = {}
        found_calls = []
        not_found_calls = []

        for call_id in call_ids:
            if call_id in call_lookup:
                call = call_lookup[call_id]
                participants_by_call[call_id] = client.extract_participants(call)
                found_calls.append(call_id)
            else:
                not_found_calls.append(call_id)

    return {
        "participants_by_call": participants_by_call,
        "found_count": len(found_calls),
        "not_found_count": len(not_found_calls),
        "not_found_call_ids": not_found_calls if not_found_calls else None,
    }
