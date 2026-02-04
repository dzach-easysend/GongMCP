"""
Analysis MCP tools with smart routing.
"""

from datetime import datetime, timedelta

from ..analysis.jobs import (
    create_job,
    generate_job_id,
    get_job_results as _get_job_results,
    load_job_status,
    run_job_in_background,
)
from ..analysis.router import get_routing_decision
from ..analysis.runner import run_analysis
from ..gong_client import GongClient
from ..utils.filters import filter_calls_by_emails
from ..utils.formatters import build_transcript_json


async def analyze_calls(
    from_date: str | None = None,
    to_date: str | None = None,
    prompt: str = "Analyze these call transcripts and extract key insights.",
    call_ids: list[str] | None = None,
    emails: list[str] | None = None,
    domains: list[str] | None = None,
) -> dict:
    """
    Analyze call transcripts with smart routing.

    For small datasets (< 150K tokens): Returns transcripts directly for inline analysis.
    For large datasets: Starts an async job and returns job_id for polling.

    Args:
        from_date: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        to_date: End date (YYYY-MM-DD). Defaults to today.
        prompt: Analysis prompt/instructions.
        call_ids: Specific call IDs to analyze (optional).
        emails: Filter by participant emails (for cross-MCP joins).
        domains: Filter by email domains.

    Returns:
        Either:
        - mode=direct: Includes transcripts for inline analysis
        - mode=async: Includes job_id for polling
    """
    # Default date range
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    from_datetime = f"{from_date}T00:00:00Z"
    to_datetime = f"{to_date}T23:59:59Z"

    async with GongClient() as client:
        # Get calls
        all_calls = await client.get_all_calls(from_datetime, to_datetime)

        # Filter by call_ids if provided
        if call_ids:
            call_id_set = set(call_ids)
            all_calls = [c for c in all_calls if c.get("metaData", {}).get("id") in call_id_set]

        # Filter by emails/domains
        if emails or domains:
            all_calls, matched_emails = filter_calls_by_emails(
                all_calls, emails, domains
            )

        if not all_calls:
            return {
                "mode": "error",
                "error": "No calls found matching the criteria",
                "from_date": from_date,
                "to_date": to_date,
            }

        # Fetch transcripts
        call_ids_to_fetch = [c.get("metaData", {}).get("id") for c in all_calls if c.get("metaData", {}).get("id")]
        transcripts_raw = await client.get_multiple_transcripts(call_ids_to_fetch)

        # Build transcript lookup
        transcript_lookup = {t.get("callId"): t for t in transcripts_raw}

        # Build full transcript objects
        transcripts = []
        for call in all_calls:
            call_id = call.get("metaData", {}).get("id")
            transcript_data = transcript_lookup.get(call_id, {"error": "No transcript"})
            transcripts.append(build_transcript_json(call, transcript_data))

    # Get routing decision
    decision = get_routing_decision(transcripts)

    if decision["mode"] == "direct":
        # Small dataset - return transcripts for inline analysis
        return {
            "mode": "direct",
            "transcripts": transcripts,
            "call_count": decision["call_count"],
            "total_tokens": decision["total_tokens"],
            "message": "Transcripts returned - ready for inline analysis",
            "from_date": from_date,
            "to_date": to_date,
        }

    else:
        # Large dataset - start async job
        job_id = generate_job_id()

        # Create job record
        create_job(
            job_id=job_id,
            call_count=decision["call_count"],
            estimated_batches=decision["estimated_batches"],
            estimated_minutes=decision["estimated_minutes"],
            prompt=prompt,
        )

        # Start background processing
        run_job_in_background(
            job_id,
            run_analysis(job_id, transcripts, prompt),
        )

        return {
            "mode": "async",
            "job_id": job_id,
            "call_count": decision["call_count"],
            "total_tokens": decision["total_tokens"],
            "estimated_batches": decision["estimated_batches"],
            "estimated_minutes": decision["estimated_minutes"],
            "message": "Dataset too large for inline analysis. Started background job.",
            "from_date": from_date,
            "to_date": to_date,
        }


async def get_job_status(job_id: str) -> dict:
    """
    Check the status of an analysis job.

    Args:
        job_id: The job identifier from analyze_calls.

    Returns:
        Current job status with progress info.
    """
    status = load_job_status(job_id)

    if not status:
        return {
            "error": f"Job not found: {job_id}",
            "job_id": job_id,
        }

    return {
        "job_id": status["job_id"],
        "status": status["status"],
        "progress_percent": status.get("progress_percent", 0),
        "current_batch": status.get("current_batch", 0),
        "total_batches": status.get("total_batches", 0),
        "message": status.get("message", ""),
        "cost_so_far": status.get("cost_so_far", 0.0),
        "created_at": status.get("created_at"),
        "updated_at": status.get("updated_at"),
    }


async def get_job_results(job_id: str) -> dict:
    """
    Get the results of a completed analysis job.

    Args:
        job_id: The job identifier from analyze_calls.

    Returns:
        Analysis results or error if not complete.
    """
    status = load_job_status(job_id)

    if not status:
        return {
            "error": f"Job not found: {job_id}",
            "job_id": job_id,
        }

    if status["status"] != "complete":
        return {
            "error": f"Job not complete. Current status: {status['status']}",
            "job_id": job_id,
            "status": status["status"],
            "message": status.get("message", ""),
        }

    results = _get_job_results(job_id)

    if not results:
        return {
            "error": "Results file not found",
            "job_id": job_id,
        }

    return {
        "job_id": job_id,
        "status": "complete",
        "total_calls": results.get("total_calls", 0),
        "total_batches": results.get("total_batches", 0),
        "total_cost": results.get("total_cost", 0.0),
        "batch_results": results.get("batch_results", []),
    }
