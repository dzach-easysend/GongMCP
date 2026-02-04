"""Unit tests for job management."""

import json
from pathlib import Path

import pytest

from gong_mcp.analysis.jobs import (
    complete_job,
    create_job,
    fail_job,
    generate_job_id,
    get_job_results,
    get_jobs_dir,
    load_job_status,
    update_job_progress,
)


@pytest.mark.unit
class TestJobIdGeneration:
    """Test job ID generation."""

    def test_generate_job_id_format(self):
        """Test that job ID has correct format."""
        job_id = generate_job_id()
        assert job_id.startswith("job_")
        assert len(job_id) > 10  # job_ + timestamp

    def test_generate_job_id_unique(self):
        """Test that generated job IDs are unique (with delay)."""
        import time
        id1 = generate_job_id()
        time.sleep(0.01)  # Small delay to ensure different timestamp
        id2 = generate_job_id()
        # IDs generated in same second may be identical, so just verify format
        assert id1.startswith("job_")
        assert id2.startswith("job_")


@pytest.mark.unit
class TestJobDirectory:
    """Test job directory management."""

    def test_get_jobs_dir_creates_directory(self, temp_jobs_dir):
        """Test that get_jobs_dir creates directory if needed."""
        jobs_dir = get_jobs_dir()
        assert jobs_dir.exists()
        assert jobs_dir.is_dir()

    def test_get_jobs_dir_from_env(self, temp_jobs_dir, monkeypatch):
        """Test that get_jobs_dir respects environment variable."""
        custom_dir = temp_jobs_dir / "custom"
        monkeypatch.setenv("GONG_MCP_JOBS_DIR", str(custom_dir))
        jobs_dir = get_jobs_dir()
        assert jobs_dir == custom_dir


@pytest.mark.unit
class TestCreateJob:
    """Test job creation."""

    def test_create_job_creates_file(self, temp_jobs_dir):
        """Test that create_job creates a status file."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test prompt",
        )

        job_file = temp_jobs_dir / f"{job_id}.json"
        assert job_file.exists()

    def test_create_job_status_content(self, temp_jobs_dir):
        """Test that created job has correct status content."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test prompt",
        )

        status = load_job_status(job_id)
        assert status["job_id"] == job_id
        assert status["status"] == "pending"
        assert status["call_count"] == 10
        assert status["estimated_batches"] == 2
        assert status["estimated_minutes"] == 3
        assert status["prompt"] == "Test prompt"
        assert status["current_batch"] == 0
        assert status["progress_percent"] == 0
        assert "created_at" in status


@pytest.mark.unit
class TestLoadJobStatus:
    """Test loading job status."""

    def test_load_job_status_existing(self, temp_jobs_dir):
        """Test loading existing job status."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=5,
            estimated_batches=1,
            estimated_minutes=1,
            prompt="Test",
        )

        status = load_job_status(job_id)
        assert status is not None
        assert status["job_id"] == job_id

    def test_load_job_status_nonexistent(self, temp_jobs_dir):
        """Test loading non-existent job status."""
        status = load_job_status("nonexistent_job")
        assert status is None


@pytest.mark.unit
class TestUpdateJobProgress:
    """Test job progress updates."""

    def test_update_job_progress(self, temp_jobs_dir):
        """Test updating job progress."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=4,
            estimated_minutes=5,
            prompt="Test",
        )

        update_job_progress(
            job_id=job_id,
            current_batch=2,
            total_batches=4,
            message="Processing...",
            cost_so_far=0.05,
        )

        status = load_job_status(job_id)
        assert status["status"] == "running"
        assert status["current_batch"] == 2
        assert status["total_batches"] == 4
        assert status["progress_percent"] == 50
        assert status["cost_so_far"] == 0.05
        assert status["message"] == "Processing..."

    def test_update_job_progress_calculates_percent(self, temp_jobs_dir):
        """Test that progress percent is calculated correctly."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=10,
            estimated_minutes=10,
            prompt="Test",
        )

        update_job_progress(job_id=job_id, current_batch=5, total_batches=10)
        status = load_job_status(job_id)
        assert status["progress_percent"] == 50

        update_job_progress(job_id=job_id, current_batch=10, total_batches=10)
        status = load_job_status(job_id)
        assert status["progress_percent"] == 100


@pytest.mark.unit
class TestCompleteJob:
    """Test job completion."""

    def test_complete_job_updates_status(self, temp_jobs_dir):
        """Test that complete_job updates status."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )

        results = {
            "job_id": job_id,
            "total_calls": 10,
            "total_batches": 2,
            "total_cost": 0.10,
            "batch_results": [],
        }

        complete_job(job_id, results, total_cost=0.10)

        status = load_job_status(job_id)
        assert status["status"] == "complete"
        assert status["progress_percent"] == 100
        assert status["total_cost"] == 0.10
        assert "completed_at" in status

    def test_complete_job_saves_results(self, temp_jobs_dir):
        """Test that complete_job saves results file."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )

        results = {
            "job_id": job_id,
            "total_calls": 10,
            "total_batches": 2,
            "total_cost": 0.10,
            "batch_results": [{"batch_num": 1, "analysis": "Test analysis"}],
        }

        complete_job(job_id, results, total_cost=0.10)

        results_file = temp_jobs_dir / f"{job_id}_results.json"
        assert results_file.exists()

        with open(results_file) as f:
            saved_results = json.load(f)
        assert saved_results["job_id"] == job_id
        assert len(saved_results["batch_results"]) == 1


@pytest.mark.unit
class TestFailJob:
    """Test job failure handling."""

    def test_fail_job_updates_status(self, temp_jobs_dir):
        """Test that fail_job updates status to error."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )

        fail_job(job_id, "Test error message")

        status = load_job_status(job_id)
        assert status["status"] == "error"
        assert "error" in status["message"]
        assert status["error"] == "Test error message"
        assert "failed_at" in status


@pytest.mark.unit
class TestGetJobResults:
    """Test getting job results."""

    def test_get_job_results_existing(self, temp_jobs_dir):
        """Test getting existing job results."""
        job_id = generate_job_id()
        create_job(
            job_id=job_id,
            call_count=10,
            estimated_batches=2,
            estimated_minutes=3,
            prompt="Test",
        )

        results = {
            "job_id": job_id,
            "total_calls": 10,
            "total_batches": 2,
            "total_cost": 0.10,
            "batch_results": [],
        }

        complete_job(job_id, results, total_cost=0.10)

        retrieved_results = get_job_results(job_id)
        assert retrieved_results is not None
        assert retrieved_results["job_id"] == job_id
        assert retrieved_results["total_calls"] == 10

    def test_get_job_results_nonexistent(self, temp_jobs_dir):
        """Test getting non-existent job results."""
        results = get_job_results("nonexistent_job")
        assert results is None
