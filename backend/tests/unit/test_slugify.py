"""Tests for slugify function."""
from __future__ import annotations
from app.modules.products.service import _slugify


class TestSlugify:
    def test_basic_slug(self):
        assert _slugify("Vestido Floral") == "vestido-floral"

    def test_special_characters_removed(self):
        assert _slugify("Pantalon! $50 Oferta?") == "pantalon-50-oferta"

    def test_multiple_spaces_and_hyphens(self):
        assert _slugify("  Blusa   de   Seda  ") == "blusa-de-seda"

    def test_trailing_hyphens_removed(self):
        assert not _slugify("Producto-").endswith("-")

    def test_max_length_200(self):
        assert len(_slugify("A " * 200)) <= 200

    def test_empty_string(self):
        assert _slugify("") == ""

    def test_numbers_preserved(self):
        assert _slugify("Polo 2024") == "polo-2024"

    def test_accents_stripped(self):
        assert _slugify("Camiseta Alvarez") == "camiseta-alvarez"
