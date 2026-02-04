"""
Formatting utilities for transcripts and call data.
Ported from GongWebApp with enhancements.
"""

from datetime import datetime, timezone
from typing import Any


def format_duration(seconds: int | float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "1h 23m 45s" or "5m 30s"
    """
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_timestamp(seconds: float) -> str:
    """
    Format timestamp in seconds to MM:SS or HH:MM:SS.

    Args:
        seconds: Timestamp in seconds

    Returns:
        Formatted timestamp string
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_iso_date(iso_string: str) -> str:
    """
    Format ISO datetime string to human-readable format.

    Args:
        iso_string: ISO format datetime string

    Returns:
        Formatted date string like "Jan 15, 2026 at 10:30 AM"
    """
    if not iso_string:
        return "Unknown"

    try:
        # Handle various ISO formats
        if iso_string.endswith("Z"):
            iso_string = iso_string[:-1] + "+00:00"

        dt = datetime.fromisoformat(iso_string)

        # Convert to local time if timezone aware
        if dt.tzinfo is not None:
            dt = dt.astimezone()

        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return iso_string


def build_transcript_text(
    call_data: dict,
    transcript_data: dict,
    include_timestamps: bool = True,
) -> str:
    """
    Build formatted transcript text from Gong API data.

    Args:
        call_data: Call metadata from Gong API
        transcript_data: Transcript data from Gong API
        include_timestamps: Whether to include timestamps

    Returns:
        Formatted transcript as plain text
    """
    metadata = call_data.get("metaData", {})
    parties = call_data.get("parties", [])

    # Build speaker map
    speaker_map = {}
    for party in parties:
        name = party.get("name", party.get("emailAddress", "Unknown"))
        if name in ["Merged Audio", "Fireflies.Ai Notetaker"]:
            continue

        for key in ["speakerId", "userId", "id", "partyId"]:
            if party.get(key):
                speaker_map[str(party[key])] = name

    # Build header
    lines = []
    title = metadata.get("title", "Untitled Call")
    date = format_iso_date(metadata.get("started", ""))
    duration = format_duration(metadata.get("duration", 0))

    lines.append(f"# {title}")
    lines.append(f"Date: {date}")
    lines.append(f"Duration: {duration}")
    lines.append("")

    # Build conversation
    if "error" not in transcript_data:
        entries = transcript_data.get("transcript", [])

        all_sentences = []
        for entry in entries:
            speaker_id = str(entry.get("speakerId", ""))
            speaker_name = speaker_map.get(speaker_id, f"Speaker {speaker_id[-4:]}")

            for sentence in entry.get("sentences", []):
                start_ms = sentence.get("start", 0)
                text = sentence.get("text", "")
                if text:
                    all_sentences.append({
                        "start": start_ms,
                        "speaker": speaker_name,
                        "text": text,
                    })

        # Sort by timestamp
        all_sentences.sort(key=lambda x: x["start"])

        # Format output
        for sentence in all_sentences:
            if include_timestamps:
                ts = format_timestamp(sentence["start"] / 1000)
                lines.append(f"[{ts}] {sentence['speaker']}: {sentence['text']}")
            else:
                lines.append(f"{sentence['speaker']}: {sentence['text']}")

    return "\n".join(lines)


def build_transcript_json(call_data: dict, transcript_data: dict) -> dict:
    """
    Build structured transcript JSON from Gong API data.

    Args:
        call_data: Call metadata from Gong API
        transcript_data: Transcript data from Gong API

    Returns:
        Structured dict with metadata, participants, and conversation
    """
    metadata = call_data.get("metaData", {})
    parties = call_data.get("parties", [])

    output: dict[str, Any] = {
        "metadata": {},
        "participants": {"internal": [], "external": []},
        "conversation": [],
    }

    # Metadata
    output["metadata"]["call_id"] = metadata.get("id", "")
    output["metadata"]["title"] = metadata.get("title", "Untitled Call")
    output["metadata"]["date"] = metadata.get("started", "")
    output["metadata"]["date_formatted"] = format_iso_date(metadata.get("started", ""))
    output["metadata"]["duration_seconds"] = metadata.get("duration", 0)
    output["metadata"]["duration_formatted"] = format_duration(metadata.get("duration", 0))

    # Build speaker map and participants
    speaker_map = {}
    affiliation_map = {}

    for party in parties:
        name = party.get("name", party.get("emailAddress", "Unknown"))
        email = party.get("emailAddress", "")
        affiliation = party.get("affiliation", "other").lower()

        # Skip noise
        if name in ["Merged Audio", "Fireflies.Ai Notetaker", "Fireflies.ai Notetaker"]:
            continue
        if "Fireflies" in name and "Notetaker" in name:
            continue

        # Map speaker IDs
        for key in ["speakerId", "userId", "id", "partyId"]:
            if party.get(key):
                speaker_map[str(party[key])] = name
                affiliation_map[str(party[key])] = affiliation

        # Add to participants
        participant = {"name": name, "email": email}
        if affiliation == "internal":
            output["participants"]["internal"].append(participant)
        else:
            output["participants"]["external"].append(participant)

    # Build conversation
    if "error" not in transcript_data:
        entries = transcript_data.get("transcript", [])

        all_sentences = []
        for entry in entries:
            speaker_id = str(entry.get("speakerId", ""))
            speaker_name = speaker_map.get(speaker_id, f"Speaker {speaker_id[-4:]}")
            speaker_affiliation = affiliation_map.get(speaker_id, "unknown")

            for sentence in entry.get("sentences", []):
                start_ms = sentence.get("start", 0)
                text = sentence.get("text", "")
                if text:
                    all_sentences.append({
                        "start": start_ms,
                        "speaker": speaker_name,
                        "affiliation": speaker_affiliation,
                        "text": text,
                    })

        all_sentences.sort(key=lambda x: x["start"])

        for sentence in all_sentences:
            output["conversation"].append({
                "timestamp": format_timestamp(sentence["start"] / 1000),
                "speaker": sentence["speaker"],
                "affiliation": sentence["affiliation"],
                "text": sentence["text"],
            })

    return output
