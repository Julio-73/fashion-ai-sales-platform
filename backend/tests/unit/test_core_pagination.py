"""Tests for pagination models."""
from __future__ import annotations
import pytest
from pydantic import ValidationError
from app.core.pagination import PageMeta, PageParams


class TestPageParams:
    def test_default_values(self):
        p = PageParams()
        assert p.limit == 25
        assert p.cursor is None

    def test_limit_bounds(self):
        PageParams(limit=1)
        PageParams(limit=100)
        with pytest.raises(ValidationError):
            PageParams(limit=0)
        with pytest.raises(ValidationError):
            PageParams(limit=101)

    def test_with_cursor(self):
        assert PageParams(cursor="abc").cursor == "abc"


class TestPageMeta:
    def test_default_values(self):
        m = PageMeta()
        assert m.next_cursor is None
        assert m.total is None

    def test_with_values(self):
        m = PageMeta(next_cursor="c", total=42)
        assert m.next_cursor == "c"
        assert m.total == 42
