"""
Filtering utilities for cross-MCP synthesis.
Handles email/domain/participant filtering logic.
"""


def filter_calls_by_emails(
    calls: list[dict],
    emails: list[str] | None = None,
    domains: list[str] | None = None,
) -> tuple[list[dict], list[str]]:
    """
    Filter calls by participant emails or domains.

    Args:
        calls: List of call data from Gong API
        emails: List of email addresses to match
        domains: List of email domains to match

    Returns:
        Tuple of (filtered_calls, matched_emails)
    """
    if not emails and not domains:
        return calls, []

    # Normalize for matching
    email_set = {e.lower() for e in (emails or [])}
    domain_set = {d.lower().lstrip("@") for d in (domains or [])}

    filtered = []
    matched_emails = set()

    for call in calls:
        parties = call.get("parties", [])
        call_matched = False

        for party in parties:
            email = party.get("emailAddress", "").lower()
            if not email:
                continue

            # Match by exact email
            if email in email_set:
                filtered.append(call)
                matched_emails.add(email)
                call_matched = True
                break

            # Match by domain
            if "@" in email and domain_set:
                email_domain = email.split("@")[1]
                if email_domain in domain_set:
                    filtered.append(call)
                    matched_emails.add(email)
                    call_matched = True
                    break

        if call_matched:
            continue

    return filtered, list(matched_emails)


def extract_external_emails(calls: list[dict]) -> list[str]:
    """
    Extract all external participant emails from calls.

    Args:
        calls: List of call data from Gong API

    Returns:
        List of unique external email addresses
    """
    emails = set()

    for call in calls:
        parties = call.get("parties", [])
        for party in parties:
            affiliation = party.get("affiliation", "").lower()
            email = party.get("emailAddress", "")
            if affiliation != "internal" and email:
                emails.add(email.lower())

    return list(emails)


def get_matching_call_ids(
    calls: list[dict],
    emails: list[str] | None = None,
    domains: list[str] | None = None,
) -> list[str]:
    """
    Get call IDs that match the email/domain filter.

    Args:
        calls: List of call data from Gong API
        emails: List of email addresses to match
        domains: List of email domains to match

    Returns:
        List of matching call IDs
    """
    filtered, _ = filter_calls_by_emails(calls, emails, domains)
    return [call.get("id", "") for call in filtered if call.get("id")]
