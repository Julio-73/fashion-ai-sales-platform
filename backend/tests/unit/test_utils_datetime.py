"""Tests for datetime utils."""
from __future__ import annotations
from datetime import UTC, datetime
from app.utils.datetime import utc_now


class TestUtcNow:
    def test_returns_datetime(self):
        assert isinstance(utc_now(), datetime)

    def test_returns_utc(self):
        assert utc_now().tzinfo == UTC

    def test_is_recent(self):
        before = datetime.now(UTC)
        result = utc_now()
        after = datetime.now(UTC)
        assert before <= result <= after
