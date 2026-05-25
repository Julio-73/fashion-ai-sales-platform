"""Tests for password hashing."""
from __future__ import annotations
from app.core.security.password import hash_password, verify_password


class TestHashPassword:
    def test_hash_is_string(self):
        assert isinstance(hash_password("pwd"), str)

    def test_unique_hashes(self):
        assert hash_password("same") != hash_password("same")


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        h = hash_password("pwd")
        assert verify_password("pwd", h) is True

    def test_incorrect_password_returns_false(self):
        assert verify_password("wrong", hash_password("correct")) is False
