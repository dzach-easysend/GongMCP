"""Unit tests for formatting utilities."""

import pytest

from gong_mcp.utils.formatters import (
    build_transcript_json,
    build_transcript_text,
    format_duration,
    format_iso_date,
    format_timestamp,
)


@pytest.mark.unit
class TestFormatDuration:
    """Test format_duration function."""

    def test_format_duration_hours(self):
        """Test formatting duration with hours."""
        assert format_duration(3665) == "1h 1m 5s"
        assert format_duration(7200) == "2h 0m 0s"

    def test_format_duration_minutes(self):
        """Test formatting duration with only minutes."""
        assert format_duration(125) == "2m 5s"
        assert format_duration(60) == "1m 0s"

    def test_format_duration_seconds(self):
        """Test formatting duration with only seconds."""
        assert format_duration(45) == "45s"
        assert format_duration(5) == "5s"

    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0) == "0s"

    def test_format_duration_float(self):
        """Test formatting float duration."""
        assert format_duration(90.7) == "1m 30s"

    def test_format_duration_negative(self):
        """Test formatting negative duration."""
        assert format_duration(-10) == "-10s"


@pytest.mark.unit
class TestFormatTimestamp:
    """Test format_timestamp function."""

    def test_format_timestamp_with_hours(self):
        """Test formatting timestamp with hours."""
        assert format_timestamp(3665) == "01:01:05"
        assert format_timestamp(7200) == "02:00:00"

    def test_format_timestamp_minutes_only(self):
        """Test formatting timestamp with minutes only."""
        assert format_timestamp(125) == "02:05"
        assert format_timestamp(60) == "01:00"

    def test_format_timestamp_seconds_only(self):
        """Test formatting timestamp with seconds only."""
        assert format_timestamp(45) == "00:45"
        assert format_timestamp(5) == "00:05"

    def test_format_timestamp_zero(self):
        """Test formatting zero timestamp."""
        assert format_timestamp(0) == "00:00"

    def test_format_timestamp_float(self):
        """Test formatting float timestamp."""
        assert format_timestamp(90.7) == "01:30"


@pytest.mark.unit
class TestFormatIsoDate:
    """Test format_iso_date function."""

    def test_format_iso_date_with_z(self):
        """Test formatting ISO date with Z timezone."""
        result = format_iso_date("2024-01-15T10:30:00Z")
        assert "Jan 15, 2024" in result
        assert "10:30" in result

    def test_format_iso_date_with_timezone(self):
        """Test formatting ISO date with timezone offset."""
        result = format_iso_date("2024-01-15T10:30:00+00:00")
        assert "Jan 15, 2024" in result

    def test_format_iso_date_invalid(self):
        """Test formatting invalid ISO date."""
        result = format_iso_date("invalid-date")
        assert result == "invalid-date"

    def test_format_iso_date_empty(self):
        """Test formatting empty date."""
        assert format_iso_date("") == "Unknown"

    def test_format_iso_date_none(self):
        """Test formatting None date."""
        assert format_iso_date(None) == "Unknown"


@pytest.mark.unit
class TestBuildTranscriptText:
    """Test build_transcript_text function."""

    def test_build_transcript_text_with_timestamps(self, sample_call_data, sample_transcript_data):
        """Test building transcript text with timestamps."""
        transcript = build_transcript_text(sample_call_data, sample_transcript_data, include_timestamps=True)

        assert isinstance(transcript, str)
        assert "Sales Call with Acme Corp" in transcript
        assert "John Doe" in transcript or "Jane Smith" in transcript
        assert "[" in transcript  # Timestamps present

    def test_build_transcript_text_without_timestamps(self, sample_call_data, sample_transcript_data):
        """Test building transcript text without timestamps."""
        transcript = build_transcript_text(sample_call_data, sample_transcript_data, include_timestamps=False)

        assert isinstance(transcript, str)
        assert "[" not in transcript  # No timestamps

    def test_build_transcript_text_with_error(self, sample_call_data):
        """Test building transcript text when transcript has error."""
        transcript_data = {"error": "No transcript found"}
        transcript = build_transcript_text(sample_call_data, transcript_data)

        assert isinstance(transcript, str)
        assert "Sales Call with Acme Corp" in transcript

    def test_build_transcript_text_filters_noise(self):
        """Test that noise participants are filtered."""
        call_data = {
            "metaData": {"title": "Test Call", "started": "2024-01-15T10:30:00Z", "duration": 100},
            "parties": [
                {"name": "Merged Audio", "emailAddress": "", "speakerId": "speaker_1"},
                {"name": "John Doe", "emailAddress": "john@example.com", "speakerId": "speaker_2"},
            ],
        }
        transcript_data = {
            "transcript": [
                {"speakerId": "speaker_1", "sentences": [{"start": 0, "text": "Noise"}]},
                {"speakerId": "speaker_2", "sentences": [{"start": 1000, "text": "Real content"}]},
            ]
        }

        transcript = build_transcript_text(call_data, transcript_data)
        # Should not include "Merged Audio" in speaker names
        assert "Merged Audio" not in transcript or "Speaker" in transcript


@pytest.mark.unit
class TestBuildTranscriptJson:
    """Test build_transcript_json function."""

    def test_build_transcript_json_structure(self, sample_call_data, sample_transcript_data):
        """Test building transcript JSON structure."""
        transcript = build_transcript_json(sample_call_data, sample_transcript_data)

        assert isinstance(transcript, dict)
        assert "metadata" in transcript
        assert "participants" in transcript
        assert "conversation" in transcript

    def test_build_transcript_json_metadata(self, sample_call_data, sample_transcript_data):
        """Test transcript JSON metadata."""
        transcript = build_transcript_json(sample_call_data, sample_transcript_data)

        assert transcript["metadata"]["call_id"] == "call_12345"
        assert transcript["metadata"]["title"] == "Sales Call with Acme Corp"
        assert "duration_seconds" in transcript["metadata"]
        assert "duration_formatted" in transcript["metadata"]

    def test_build_transcript_json_participants(self, sample_call_data, sample_transcript_data):
        """Test transcript JSON participants."""
        transcript = build_transcript_json(sample_call_data, sample_transcript_data)

        assert "internal" in transcript["participants"]
        assert "external" in transcript["participants"]
        assert len(transcript["participants"]["internal"]) == 1
        assert len(transcript["participants"]["external"]) == 1

    def test_build_transcript_json_conversation(self, sample_call_data, sample_transcript_data):
        """Test transcript JSON conversation."""
        transcript = build_transcript_json(sample_call_data, sample_transcript_data)

        assert isinstance(transcript["conversation"], list)
        assert len(transcript["conversation"]) > 0
        assert "speaker" in transcript["conversation"][0]
        assert "text" in transcript["conversation"][0]
        assert "timestamp" in transcript["conversation"][0]

    def test_build_transcript_json_with_error(self, sample_call_data):
        """Test building transcript JSON when transcript has error."""
        transcript_data = {"error": "No transcript found"}
        transcript = build_transcript_json(sample_call_data, transcript_data)

        assert isinstance(transcript, dict)
        assert transcript["conversation"] == []

    def test_build_transcript_json_filters_noise(self):
        """Test that noise participants are filtered in JSON."""
        call_data = {
            "id": "call_1",
            "metaData": {"title": "Test", "started": "2024-01-15T10:30:00Z", "duration": 100},
            "parties": [
                {"name": "Fireflies.Ai Notetaker", "emailAddress": "", "affiliation": "internal"},
                {"name": "John Doe", "emailAddress": "john@example.com", "affiliation": "internal"},
            ],
        }
        transcript_data = {"transcript": []}

        transcript = build_transcript_json(call_data, transcript_data)

        # Should not include Fireflies in participants
        internal_names = [p["name"] for p in transcript["participants"]["internal"]]
        assert "Fireflies.Ai Notetaker" not in internal_names
