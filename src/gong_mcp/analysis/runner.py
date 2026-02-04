"""
Analysis Runner

Batch processing logic for analyzing transcripts with Claude API.
Ported from GongWebApp analysis_runner.py with adaptations for MCP.
"""

import json
import os
import time
from typing import Any

import httpx

from .jobs import complete_job, fail_job, update_job_progress

# Configuration
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 16000
BATCH_SIZE = 20
RATE_LIMIT_DELAY = 65  # Seconds between batches (Tier 1 rate limit)
MAX_TOKENS_PER_BATCH = 24000


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    return len(text) // 4


def create_batches(
    transcripts: list[dict],
    batch_size: int = BATCH_SIZE,
    max_tokens_per_batch: int = MAX_TOKENS_PER_BATCH,
) -> list[list[dict]]:
    """
    Split transcripts into batches respecting token limits.

    Args:
        transcripts: List of transcript dicts
        batch_size: Max calls per batch
        max_tokens_per_batch: Max tokens per batch

    Returns:
        List of batches (each batch is a list of transcripts)
    """
    batches = []
    current_batch = []
    current_tokens = 0

    # Reserve space for prompt overhead
    prompt_overhead = 3500  # Approximate prompt size
    safe_limit = int(max_tokens_per_batch * 0.9) - prompt_overhead

    for transcript in transcripts:
        transcript_json = json.dumps(transcript, ensure_ascii=False)
        transcript_tokens = estimate_tokens(transcript_json)

        # Check if we need to start a new batch
        would_exceed_size = len(current_batch) >= batch_size
        would_exceed_tokens = (current_tokens + transcript_tokens) > safe_limit

        if current_batch and (would_exceed_size or would_exceed_tokens):
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(transcript)
        current_tokens += transcript_tokens

    # Don't forget the last batch
    if current_batch:
        batches.append(current_batch)

    return batches


async def call_claude_api(
    batch: list[dict],
    prompt: str,
    batch_num: int,
    total_batches: int,
    max_retries: int = 3,
) -> tuple[str, dict]:
    """
    Send a batch to Claude API for analysis.

    Args:
        batch: List of transcript dicts
        prompt: Analysis prompt
        batch_num: Current batch number
        total_batches: Total number of batches
        max_retries: Max retry attempts

    Returns:
        Tuple of (response_text, stats)
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    # Prepare content
    batch_json = json.dumps(batch, indent=2, ensure_ascii=False)
    full_prompt = f"{prompt}\n\nTranscripts to analyze:\n{batch_json}"
    estimated_tokens = estimate_tokens(full_prompt)

    # Prepare request
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": full_prompt}],
    }

    last_error = None

    async with httpx.AsyncClient(timeout=180.0) as client:
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.post(
                    CLAUDE_API_URL,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json=payload,
                )

                # Handle rate limits
                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", 60))
                    await asyncio.sleep(retry_after)
                    continue

                # Handle overloaded
                if response.status_code == 529:
                    wait_time = min(30 * attempt, 120)
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()
                response_text = data["content"][0]["text"]

                # Calculate stats
                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens", estimated_tokens)
                output_tokens = usage.get("output_tokens", 0)

                # Claude Sonnet pricing
                input_cost = (input_tokens / 1_000_000) * 3.0
                output_cost = (output_tokens / 1_000_000) * 15.0

                stats = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": input_cost + output_cost,
                    "batch_num": batch_num,
                    "calls_count": len(batch),
                }

                return response_text, stats

            except httpx.TimeoutException:
                last_error = "Request timeout"
                if attempt < max_retries:
                    await asyncio.sleep(15 * attempt)
                continue

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(10 * attempt)
                continue

    raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")


# Need to import asyncio for sleep
import asyncio


async def run_analysis(
    job_id: str,
    transcripts: list[dict],
    prompt: str,
) -> dict:
    """
    Run batch analysis on transcripts.

    Args:
        job_id: Job identifier for progress updates
        transcripts: List of transcript dicts
        prompt: Analysis prompt

    Returns:
        Analysis results dict
    """
    try:
        # Create batches
        batches = create_batches(transcripts)
        total_batches = len(batches)

        update_job_progress(
            job_id,
            current_batch=0,
            total_batches=total_batches,
            message=f"Created {total_batches} batches, starting analysis...",
        )

        # Process batches
        all_results = []
        total_cost = 0.0

        for i, batch in enumerate(batches, 1):
            update_job_progress(
                job_id,
                current_batch=i,
                total_batches=total_batches,
                message=f"Processing batch {i}/{total_batches}",
                cost_so_far=total_cost,
            )

            result_text, stats = await call_claude_api(
                batch, prompt, i, total_batches
            )

            all_results.append({
                "batch_num": i,
                "calls_count": stats["calls_count"],
                "analysis": result_text,
            })

            total_cost += stats["cost"]

            # Rate limit delay (except for last batch)
            if i < total_batches:
                update_job_progress(
                    job_id,
                    current_batch=i,
                    total_batches=total_batches,
                    message=f"Waiting {RATE_LIMIT_DELAY}s for rate limit...",
                    cost_so_far=total_cost,
                )
                await asyncio.sleep(RATE_LIMIT_DELAY)

        # Build final results
        results = {
            "job_id": job_id,
            "total_calls": len(transcripts),
            "total_batches": total_batches,
            "total_cost": total_cost,
            "prompt_used": prompt,
            "batch_results": all_results,
        }

        complete_job(job_id, results, total_cost)
        return results

    except Exception as e:
        fail_job(job_id, str(e))
        raise
