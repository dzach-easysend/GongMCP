"""
Smart Analysis Router

Decides whether to return transcripts directly (for inline Claude analysis)
or start an async batch job (for large datasets).
"""

import json
import os

# Token thresholds - configurable via environment
CLAUDE_CONTEXT_LIMIT = 180_000
PROMPT_OVERHEAD = 10_000
RESPONSE_BUFFER = 20_000
DEFAULT_DIRECT_THRESHOLD = 150_000


def get_direct_threshold() -> int:
    """Get the token threshold for direct mode from environment or default."""
    try:
        return int(os.getenv("DIRECT_TOKEN_THRESHOLD", DEFAULT_DIRECT_THRESHOLD))
    except ValueError:
        return DEFAULT_DIRECT_THRESHOLD


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses ~4 characters per token approximation.
    This is conservative for English text.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


def estimate_transcripts_tokens(transcripts: list[dict]) -> int:
    """
    Estimate total tokens for a list of transcripts.

    Args:
        transcripts: List of transcript dicts

    Returns:
        Estimated total token count
    """
    total_text = json.dumps(transcripts, ensure_ascii=False)
    return estimate_tokens(total_text)


def should_use_direct_mode(transcripts: list[dict]) -> bool:
    """
    Decide if transcripts should be returned directly for inline analysis.

    Args:
        transcripts: List of transcript dicts

    Returns:
        True if transcripts fit in Claude's context for inline analysis
    """
    estimated_tokens = estimate_transcripts_tokens(transcripts)
    threshold = get_direct_threshold()
    return estimated_tokens < threshold


def estimate_batch_count(total_tokens: int, tokens_per_batch: int = 24_000) -> int:
    """
    Estimate number of batches needed for async processing.

    Args:
        total_tokens: Total estimated tokens
        tokens_per_batch: Max tokens per batch (default from analysis_runner)

    Returns:
        Estimated number of batches
    """
    if total_tokens <= 0:
        return 0
    return max(1, (total_tokens + tokens_per_batch - 1) // tokens_per_batch)


def estimate_processing_time(batch_count: int, seconds_per_batch: int = 65) -> int:
    """
    Estimate total processing time in minutes.

    Args:
        batch_count: Number of batches
        seconds_per_batch: Processing time per batch (including rate limit delay)

    Returns:
        Estimated minutes
    """
    total_seconds = batch_count * seconds_per_batch
    return max(1, total_seconds // 60)


def get_routing_decision(transcripts: list[dict]) -> dict:
    """
    Get a complete routing decision with metadata.

    Args:
        transcripts: List of transcript dicts

    Returns:
        Dict with routing decision and metadata:
        {
            "mode": "direct" | "async",
            "call_count": int,
            "total_tokens": int,
            "threshold": int,
            "estimated_batches": int (only for async),
            "estimated_minutes": int (only for async),
            "reason": str
        }
    """
    call_count = len(transcripts)
    total_tokens = estimate_transcripts_tokens(transcripts)
    threshold = get_direct_threshold()

    if total_tokens < threshold:
        return {
            "mode": "direct",
            "call_count": call_count,
            "total_tokens": total_tokens,
            "threshold": threshold,
            "reason": f"Tokens ({total_tokens:,}) under threshold ({threshold:,})",
        }

    batch_count = estimate_batch_count(total_tokens)
    estimated_minutes = estimate_processing_time(batch_count)

    return {
        "mode": "async",
        "call_count": call_count,
        "total_tokens": total_tokens,
        "threshold": threshold,
        "estimated_batches": batch_count,
        "estimated_minutes": estimated_minutes,
        "reason": f"Tokens ({total_tokens:,}) exceed threshold ({threshold:,})",
    }
