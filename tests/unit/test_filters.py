"""Unit tests for filtering utilities."""

import pytest

from gong_mcp.utils.filters import (
    extract_external_emails,
    filter_calls_by_emails,
    get_matching_call_ids,
)


@pytest.mark.unit
class TestFilterCallsByEmails:
    """Test filter_calls_by_emails function."""

    def test_filter_by_exact_email(self, sample_calls_list):
        """Test filtering by exact email match."""
        emails = ["jane@acme.com"]
        filtered, matched = filter_calls_by_emails(sample_calls_list, emails=emails)

        assert len(filtered) > 0
        assert "jane@acme.com" in matched

    def test_filter_by_domain(self, sample_calls_list):
        """Test filtering by email domain."""
        domains = ["acme.com"]
        filtered, matched = filter_calls_by_emails(sample_calls_list, domains=domains)

        assert len(filtered) > 0
        assert any("acme.com" in email for email in matched)

    def test_filter_by_multiple_emails(self, sample_calls_list):
        """Test filtering by multiple emails."""
        emails = ["john@example.com", "jane@acme.com"]
        filtered, matched = filter_calls_by_emails(sample_calls_list, emails=emails)

        assert len(filtered) > 0
        assert len(matched) >= 1

    def test_filter_case_insensitive(self, sample_calls_list):
        """Test that email matching is case insensitive."""
        emails_upper = ["JANE@ACME.COM"]
        emails_lower = ["jane@acme.com"]

        filtered_upper, _ = filter_calls_by_emails(sample_calls_list, emails=emails_upper)
        filtered_lower, _ = filter_calls_by_emails(sample_calls_list, emails=emails_lower)

        assert len(filtered_upper) == len(filtered_lower)

    def test_filter_no_emails_or_domains(self, sample_calls_list):
        """Test that no filtering occurs when no emails/domains provided."""
        filtered, matched = filter_calls_by_emails(sample_calls_list)

        assert filtered == sample_calls_list
        assert matched == []

    def test_filter_domain_with_at_prefix(self, sample_calls_list):
        """Test that domain matching handles @ prefix."""
        domains_with_at = ["@acme.com"]
        domains_without = ["acme.com"]

        filtered_with, _ = filter_calls_by_emails(sample_calls_list, domains=domains_with_at)
        filtered_without, _ = filter_calls_by_emails(sample_calls_list, domains=domains_without)

        assert len(filtered_with) == len(filtered_without)

    def test_filter_empty_calls_list(self):
        """Test filtering with empty calls list."""
        filtered, matched = filter_calls_by_emails([], emails=["test@example.com"])

        assert filtered == []
        assert matched == []

    def test_filter_calls_with_no_parties(self):
        """Test filtering calls with no parties."""
        calls_no_parties = [{"id": "call_1", "parties": []}]
        filtered, matched = filter_calls_by_emails(calls_no_parties, emails=["test@example.com"])

        assert filtered == []
        assert matched == []

    def test_filter_calls_with_no_email_addresses(self):
        """Test filtering calls with parties but no email addresses."""
        calls_no_emails = [
            {
                "id": "call_1",
                "parties": [{"name": "John", "emailAddress": "", "affiliation": "internal"}],
            }
        ]
        filtered, matched = filter_calls_by_emails(calls_no_emails, emails=["test@example.com"])

        assert filtered == []
        assert matched == []


@pytest.mark.unit
class TestExtractExternalEmails:
    """Test extract_external_emails function."""

    def test_extract_external_emails(self, sample_calls_list):
        """Test extracting external participant emails."""
        emails = extract_external_emails(sample_calls_list)

        assert isinstance(emails, list)
        assert "jane@acme.com" in emails

    def test_extract_only_external(self, sample_calls_list):
        """Test that only external emails are extracted."""
        emails = extract_external_emails(sample_calls_list)

        # Should not include internal emails
        assert "john@example.com" not in emails

    def test_extract_deduplicates(self):
        """Test that duplicate emails are deduplicated."""
        calls = [
            {
                "parties": [
                    {"emailAddress": "external@acme.com", "affiliation": "external"},
                    {"emailAddress": "external@acme.com", "affiliation": "external"},
                ]
            }
        ]
        emails = extract_external_emails(calls)

        assert emails.count("external@acme.com") == 1

    def test_extract_empty_list(self):
        """Test extracting from empty calls list."""
        emails = extract_external_emails([])

        assert emails == []

    def test_extract_no_external_participants(self):
        """Test extracting when no external participants exist."""
        calls = [
            {
                "parties": [
                    {"emailAddress": "internal@example.com", "affiliation": "internal"}
                ]
            }
        ]
        emails = extract_external_emails(calls)

        assert emails == []


@pytest.mark.unit
class TestGetMatchingCallIds:
    """Test get_matching_call_ids function."""

    def test_get_matching_call_ids_by_email(self, sample_calls_list):
        """Test getting call IDs that match email filter."""
        call_ids = get_matching_call_ids(sample_calls_list, emails=["jane@acme.com"])

        assert isinstance(call_ids, list)
        assert len(call_ids) > 0
        assert all(isinstance(cid, str) for cid in call_ids)

    def test_get_matching_call_ids_by_domain(self, sample_calls_list):
        """Test getting call IDs that match domain filter."""
        call_ids = get_matching_call_ids(sample_calls_list, domains=["acme.com"])

        assert isinstance(call_ids, list)

    def test_get_matching_call_ids_no_matches(self):
        """Test getting call IDs when no matches exist."""
        calls = [
            {
                "id": "call_1",
                "parties": [{"emailAddress": "test@example.com", "affiliation": "external"}],
            }
        ]
        call_ids = get_matching_call_ids(calls, emails=["nonexistent@example.com"])

        assert call_ids == []

    def test_get_matching_call_ids_no_id_field(self):
        """Test handling calls without id field."""
        calls = [
            {
                "parties": [{"emailAddress": "test@example.com", "affiliation": "external"}],
            }
        ]
        call_ids = get_matching_call_ids(calls, emails=["test@example.com"])

        # Should skip calls without IDs
        assert call_ids == []
