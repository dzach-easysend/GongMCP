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
# Default threshold for direct mode (in thousands of tokens)
# Can be overridden via DIRECT_LLM_TOKEN_LIMIT env var (if Cursor passes it)
# Value of 40 means 40K tokens (40,000). Value <= 0 means always direct mode.
DEFAULT_DIRECT_LLM_TOKEN_LIMIT_K = 40  # 40K tokens - triggers async for larger datasets


def get_direct_threshold() -> int | float:
    """Get the token threshold for direct mode.

    DIRECT_LLM_TOKEN_LIMIT is specified in K (thousands of tokens).
    e.g., 150 means 150,000 tokens.

    Values <= 0 mean always use direct mode (never use Anthropic API).

    Returns:
        Token threshold, or float('inf') if always direct mode.
    """
    # #region agent log
    import json as _json; _log_path = "/Users/dannyzach/Documents/gong-mcp-server/.cursor/debug.log"
    _raw_env = os.getenv("DIRECT_LLM_TOKEN_LIMIT") or os.getenv("GONG_TOKEN_LIMIT")
    _all_env_keys = [k for k in os.environ.keys() if "DIRECT" in k or "LLM" in k or "GONG" in k or "ANTHROPIC" in k or "TOKEN" in k]
    with open(_log_path, "a") as _f: _f.write(_json.dumps({"hypothesisId": "F", "location": "router.py:get_direct_threshold:entry", "message": "Raw env value", "data": {"raw_env": _raw_env, "related_env_keys": _all_env_keys, "default": DEFAULT_DIRECT_LLM_TOKEN_LIMIT_K}, "timestamp": __import__("time").time(), "sessionId": "debug-session"}) + "\n")
    # #endregion
    try:
        # Check both env var names (GONG_TOKEN_LIMIT as fallback for Cursor compatibility)
        limit_k = int(os.getenv("DIRECT_LLM_TOKEN_LIMIT") or os.getenv("GONG_TOKEN_LIMIT") or DEFAULT_DIRECT_LLM_TOKEN_LIMIT_K)
        # #region agent log
        with open(_log_path, "a") as _f: _f.write(_json.dumps({"hypothesisId": "C", "location": "router.py:get_direct_threshold:parsed", "message": "Parsed limit_k", "data": {"limit_k": limit_k, "threshold": limit_k * 1000 if limit_k > 0 else "inf"}, "timestamp": __import__("time").time(), "sessionId": "debug-session"}) + "\n")
        # #endregion
        if limit_k <= 0:
            return float("inf")  # Always direct mode
        return limit_k * 1000
    except ValueError as e:
        # #region agent log
        with open(_log_path, "a") as _f: _f.write(_json.dumps({"hypothesisId": "C", "location": "router.py:get_direct_threshold:error", "message": "ValueError parsing", "data": {"error": str(e)}, "timestamp": __import__("time").time(), "sessionId": "debug-session"}) + "\n")
        # #endregion
        return DEFAULT_DIRECT_LLM_TOKEN_LIMIT_K * 1000


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
        # Handle infinity threshold (always direct mode)
        if threshold == float("inf"):
            threshold_display = "unlimited"
            reason = f"Direct mode forced (DIRECT_LLM_TOKEN_LIMIT <= 0)"
        else:
            threshold_display = int(threshold)
            reason = f"Tokens ({total_tokens:,}) under threshold ({threshold_display:,})"

        return {
            "mode": "direct",
            "call_count": call_count,
            "total_tokens": total_tokens,
            "threshold": threshold_display,
            "reason": reason,
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
