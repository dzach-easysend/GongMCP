"""Unit tests for analysis router."""

import os

import pytest

from gong_mcp.analysis.router import (
    estimate_batch_count,
    estimate_processing_time,
    estimate_tokens,
    estimate_transcripts_tokens,
    get_direct_threshold,
    get_routing_decision,
    should_use_direct_mode,
)


@pytest.mark.unit
class TestEstimateTokens:
    """Test estimate_tokens function."""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        # ~4 characters per token
        assert estimate_tokens("hello world") == 2  # 11 chars / 4 = 2
        assert estimate_tokens("test") == 1  # 4 chars / 4 = 1

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_long_text(self):
        """Test token estimation for long text."""
        long_text = "a" * 1000
        assert estimate_tokens(long_text) == 250  # 1000 / 4

    def test_estimate_tokens_unicode(self):
        """Test token estimation with unicode characters."""
        unicode_text = "你好世界"  # 4 characters
        assert estimate_tokens(unicode_text) == 1


@pytest.mark.unit
class TestEstimateTranscriptsTokens:
    """Test estimate_transcripts_tokens function."""

    def test_estimate_transcripts_tokens_empty(self):
        """Test token estimation for empty transcripts."""
        assert estimate_transcripts_tokens([]) == 0

    def test_estimate_transcripts_tokens_single(self):
        """Test token estimation for single transcript."""
        transcripts = [{"text": "hello world", "metadata": {"call_id": "123"}}]
        tokens = estimate_transcripts_tokens(transcripts)
        assert tokens > 0

    def test_estimate_transcripts_tokens_multiple(self):
        """Test token estimation for multiple transcripts."""
        transcripts = [
            {"text": "call 1", "metadata": {}},
            {"text": "call 2", "metadata": {}},
        ]
        tokens = estimate_transcripts_tokens(transcripts)
        assert tokens > 0

    def test_estimate_transcripts_tokens_large(self):
        """Test token estimation for large transcripts."""
        large_transcript = {"text": "x" * 10000, "metadata": {}}
        transcripts = [large_transcript] * 10
        tokens = estimate_transcripts_tokens(transcripts)
        assert tokens > 1000  # Should be substantial


@pytest.mark.unit
class TestGetDirectThreshold:
    """Test get_direct_threshold function."""

    def test_get_direct_threshold_default(self, monkeypatch):
        """Test default threshold when env var not set."""
        monkeypatch.delenv("DIRECT_LLM_TOKEN_LIMIT", raising=False)
        threshold = get_direct_threshold()
        assert threshold == 150_000  # 150K default

    def test_get_direct_threshold_from_env(self, monkeypatch):
        """Test threshold from environment variable (K units)."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "200")  # 200K
        threshold = get_direct_threshold()
        assert threshold == 200_000

    def test_get_direct_threshold_invalid_env(self, monkeypatch):
        """Test threshold with invalid env var falls back to default."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "invalid")
        threshold = get_direct_threshold()
        assert threshold == 150_000

    def test_get_direct_threshold_zero_returns_infinity(self, monkeypatch):
        """Test that zero value returns infinity (always direct mode)."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "0")
        threshold = get_direct_threshold()
        assert threshold == float("inf")

    def test_get_direct_threshold_negative_returns_infinity(self, monkeypatch):
        """Test that negative values return infinity (always direct mode)."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "-1")
        threshold = get_direct_threshold()
        assert threshold == float("inf")

    def test_get_direct_threshold_small_value(self, monkeypatch):
        """Test small K value works correctly."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "1")  # 1K = 1000 tokens
        threshold = get_direct_threshold()
        assert threshold == 1000


@pytest.mark.unit
class TestShouldUseDirectMode:
    """Test should_use_direct_mode function."""

    def test_should_use_direct_mode_small_dataset(self, monkeypatch):
        """Test that small datasets use direct mode."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K
        small_transcripts = [{"text": "small", "metadata": {}}] * 5
        assert should_use_direct_mode(small_transcripts) is True

    def test_should_use_direct_mode_large_dataset(self, monkeypatch):
        """Test that large datasets use async mode."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K
        # Create transcripts that exceed threshold
        large_transcript = {"text": "x" * 50000, "metadata": {}}  # ~12.5k tokens each
        large_transcripts = [large_transcript] * 15  # ~187.5k tokens total
        assert should_use_direct_mode(large_transcripts) is False

    def test_should_use_direct_mode_at_threshold(self, monkeypatch):
        """Test behavior at threshold boundary."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K
        # Create transcripts exactly at threshold
        transcript = {"text": "x" * 600000, "metadata": {}}  # ~150k tokens
        transcripts = [transcript]
        # Should be False (>= threshold means async)
        assert should_use_direct_mode(transcripts) is False

    def test_should_use_direct_mode_empty(self):
        """Test direct mode with empty transcripts."""
        assert should_use_direct_mode([]) is True

    def test_should_use_direct_mode_always_true_when_limit_zero(self, monkeypatch):
        """Test that all transcripts use direct mode when limit is 0."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "0")
        # Even large transcripts should use direct mode
        large_transcript = {"text": "x" * 100000, "metadata": {}}
        large_transcripts = [large_transcript] * 20  # Very large dataset
        assert should_use_direct_mode(large_transcripts) is True

    def test_should_use_direct_mode_always_true_when_limit_negative(self, monkeypatch):
        """Test that all transcripts use direct mode when limit is negative."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "-5")
        large_transcript = {"text": "x" * 100000, "metadata": {}}
        large_transcripts = [large_transcript] * 20
        assert should_use_direct_mode(large_transcripts) is True


@pytest.mark.unit
class TestEstimateBatchCount:
    """Test estimate_batch_count function."""

    def test_estimate_batch_count_single(self):
        """Test batch count for small dataset."""
        tokens = 10000
        batches = estimate_batch_count(tokens)
        assert batches == 1

    def test_estimate_batch_count_multiple(self):
        """Test batch count for large dataset."""
        tokens = 100000
        batches = estimate_batch_count(tokens)
        assert batches > 1

    def test_estimate_batch_count_zero(self):
        """Test batch count for zero tokens."""
        assert estimate_batch_count(0) == 0

    def test_estimate_batch_count_custom_tokens_per_batch(self):
        """Test batch count with custom tokens per batch."""
        tokens = 50000
        batches_default = estimate_batch_count(tokens)
        batches_custom = estimate_batch_count(tokens, tokens_per_batch=10000)
        assert batches_custom > batches_default


@pytest.mark.unit
class TestEstimateProcessingTime:
    """Test estimate_processing_time function."""

    def test_estimate_processing_time_single_batch(self):
        """Test processing time for single batch."""
        minutes = estimate_processing_time(1)
        assert minutes == 1  # 65 seconds / 60 = 1 minute

    def test_estimate_processing_time_multiple_batches(self):
        """Test processing time for multiple batches."""
        minutes = estimate_processing_time(5)
        assert minutes == 5  # 5 * 65 / 60 = 5 minutes

    def test_estimate_processing_time_zero_batches(self):
        """Test processing time for zero batches."""
        minutes = estimate_processing_time(0)
        assert minutes == 1  # Minimum 1 minute

    def test_estimate_processing_time_custom_seconds(self):
        """Test processing time with custom seconds per batch."""
        minutes_default = estimate_processing_time(2)
        minutes_custom = estimate_processing_time(2, seconds_per_batch=120)
        assert minutes_custom > minutes_default


@pytest.mark.unit
class TestGetRoutingDecision:
    """Test get_routing_decision function."""

    def test_get_routing_decision_direct_mode(self, monkeypatch):
        """Test routing decision for direct mode."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K
        small_transcripts = [{"text": "small", "metadata": {}}] * 3
        decision = get_routing_decision(small_transcripts)

        assert decision["mode"] == "direct"
        assert decision["call_count"] == 3
        assert decision["total_tokens"] < 150_000
        assert "threshold" in decision
        assert "reason" in decision

    def test_get_routing_decision_async_mode(self, monkeypatch):
        """Test routing decision for async mode."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K
        large_transcript = {"text": "x" * 50000, "metadata": {}}
        large_transcripts = [large_transcript] * 15
        decision = get_routing_decision(large_transcripts)

        assert decision["mode"] == "async"
        assert decision["call_count"] == 15
        assert decision["total_tokens"] >= 150_000
        assert "estimated_batches" in decision
        assert "estimated_minutes" in decision
        assert decision["estimated_batches"] > 0
        assert decision["estimated_minutes"] > 0

    def test_get_routing_decision_empty(self):
        """Test routing decision for empty transcripts."""
        decision = get_routing_decision([])

        assert decision["mode"] == "direct"
        assert decision["call_count"] == 0
        assert decision["total_tokens"] == 0

    def test_get_routing_decision_metadata(self, monkeypatch):
        """Test that routing decision includes all metadata."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "150")  # 150K
        transcripts = [{"text": "test", "metadata": {}}]
        decision = get_routing_decision(transcripts)

        required_keys = ["mode", "call_count", "total_tokens", "threshold", "reason"]
        for key in required_keys:
            assert key in decision

    def test_get_routing_decision_forced_direct_mode(self, monkeypatch):
        """Test routing decision when limit is 0 (forced direct mode)."""
        monkeypatch.setenv("DIRECT_LLM_TOKEN_LIMIT", "0")
        large_transcript = {"text": "x" * 100000, "metadata": {}}
        large_transcripts = [large_transcript] * 20
        decision = get_routing_decision(large_transcripts)

        assert decision["mode"] == "direct"
        assert decision["threshold"] == "unlimited"
        assert "forced" in decision["reason"].lower()
