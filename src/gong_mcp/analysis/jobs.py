"""
Async Job Manager

Manages background analysis jobs with status tracking and result storage.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine

# Default jobs directory
JOBS_DIR = Path(__file__).parent.parent.parent.parent / "jobs"


def get_jobs_dir() -> Path:
    """Get the jobs directory, creating if needed."""
    jobs_dir = Path(os.getenv("GONG_MCP_JOBS_DIR", str(JOBS_DIR)))
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir


def generate_job_id() -> str:
    """Generate a unique job ID based on timestamp."""
    return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_job_path(job_id: str) -> Path:
    """Get the path to a job's status file."""
    return get_jobs_dir() / f"{job_id}.json"


def get_job_results_path(job_id: str) -> Path:
    """Get the path to a job's results file."""
    return get_jobs_dir() / f"{job_id}_results.json"


def create_job(
    job_id: str,
    call_count: int,
    estimated_batches: int,
    estimated_minutes: int,
    prompt: str,
) -> dict:
    """
    Create a new job with initial status.

    Args:
        job_id: Unique job identifier
        call_count: Number of calls to analyze
        estimated_batches: Expected number of batches
        estimated_minutes: Expected processing time
        prompt: Analysis prompt

    Returns:
        Initial job status dict
    """
    status = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "call_count": call_count,
        "estimated_batches": estimated_batches,
        "estimated_minutes": estimated_minutes,
        "prompt": prompt,
        "current_batch": 0,
        "total_batches": estimated_batches,
        "progress_percent": 0,
        "cost_so_far": 0.0,
        "message": "Job created, waiting to start...",
    }

    save_job_status(job_id, status)
    return status


def save_job_status(job_id: str, status: dict) -> None:
    """Save job status to file."""
    status["updated_at"] = datetime.now().isoformat()
    job_path = get_job_path(job_id)
    with open(job_path, "w") as f:
        json.dump(status, f, indent=2)


def load_job_status(job_id: str) -> dict | None:
    """Load job status from file."""
    job_path = get_job_path(job_id)
    if not job_path.exists():
        return None
    with open(job_path) as f:
        return json.load(f)


def update_job_progress(
    job_id: str,
    current_batch: int,
    total_batches: int,
    message: str = "",
    cost_so_far: float = 0.0,
) -> None:
    """
    Update job progress.

    Args:
        job_id: Job identifier
        current_batch: Current batch number
        total_batches: Total number of batches
        message: Status message
        cost_so_far: Cumulative cost
    """
    status = load_job_status(job_id)
    if not status:
        return

    progress = int((current_batch / total_batches) * 100) if total_batches > 0 else 0

    status.update({
        "status": "running",
        "current_batch": current_batch,
        "total_batches": total_batches,
        "progress_percent": progress,
        "cost_so_far": cost_so_far,
        "message": message or f"Processing batch {current_batch}/{total_batches}",
    })

    save_job_status(job_id, status)


def complete_job(job_id: str, results: dict, total_cost: float = 0.0) -> None:
    """
    Mark job as complete and save results.

    Args:
        job_id: Job identifier
        results: Analysis results
        total_cost: Total cost of analysis
    """
    status = load_job_status(job_id)
    if not status:
        return

    status.update({
        "status": "complete",
        "progress_percent": 100,
        "message": "Analysis complete!",
        "total_cost": total_cost,
        "completed_at": datetime.now().isoformat(),
    })

    save_job_status(job_id, status)

    # Save results separately
    results_path = get_job_results_path(job_id)
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)


def fail_job(job_id: str, error: str) -> None:
    """
    Mark job as failed.

    Args:
        job_id: Job identifier
        error: Error message
    """
    status = load_job_status(job_id)
    if not status:
        return

    status.update({
        "status": "error",
        "message": f"Analysis failed: {error}",
        "error": error,
        "failed_at": datetime.now().isoformat(),
    })

    save_job_status(job_id, status)


def get_job_results(job_id: str) -> dict | None:
    """
    Get completed job results.

    Args:
        job_id: Job identifier

    Returns:
        Results dict or None if not found/not complete
    """
    results_path = get_job_results_path(job_id)
    if not results_path.exists():
        return None
    with open(results_path) as f:
        return json.load(f)


def list_jobs(limit: int = 20) -> list[dict]:
    """
    List recent jobs.

    Args:
        limit: Maximum number of jobs to return

    Returns:
        List of job status dicts, most recent first
    """
    jobs_dir = get_jobs_dir()
    job_files = sorted(
        jobs_dir.glob("job_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    # Filter out results files
    job_files = [f for f in job_files if not f.name.endswith("_results.json")]

    jobs = []
    for job_file in job_files[:limit]:
        with open(job_file) as f:
            jobs.append(json.load(f))

    return jobs


# Background task registry
_background_tasks: dict[str, asyncio.Task] = {}


def run_job_in_background(
    job_id: str,
    coro: Coroutine[Any, Any, dict],
) -> None:
    """
    Run a job coroutine in the background.

    Args:
        job_id: Job identifier
        coro: Coroutine to run
    """
    async def wrapper():
        try:
            result = await coro
            return result
        except Exception as e:
            fail_job(job_id, str(e))
            raise
        finally:
            _background_tasks.pop(job_id, None)

    task = asyncio.create_task(wrapper())
    _background_tasks[job_id] = task


def is_job_running(job_id: str) -> bool:
    """Check if a job is currently running."""
    return job_id in _background_tasks
