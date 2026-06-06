"""Shared helpers for PDF / XLSX generators."""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable

# Peruvian Sol is the project-wide default; we expose a helper so the
# generators never hardcode the symbol inside format strings.
CURRENCY_SYMBOL = "S/"


def fmt_money(value: Decimal | float | int | None) -> str:
    """Format a number as money, e.g. ``S/ 1,234.50``."""
    if value is None:
        return f"{CURRENCY_SYMBOL} 0.00"
    n = Decimal(str(value))
    sign = "-" if n < 0 else ""
    n_abs = abs(n)
    integer, _, fraction = f"{n_abs:.2f}".partition(".")
    grouped = ""
    while len(integer) > 3:
        grouped = f",{integer[-3:]}{grouped}"
        integer = integer[:-3]
    grouped = f"{integer}{grouped}"
    return f"{sign}{CURRENCY_SYMBOL} {grouped}.{fraction}"


def fmt_int(value: int | None) -> str:
    if value is None:
        return "0"
    n = int(value)
    return f"{n:,}".replace(",", ",")


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "0.0%"
    return f"{float(value):.1f}%"


def safe_truncate(text: str, max_len: int = 60) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def iter_to_table(
    headers: Iterable[str], rows: Iterable[Iterable[str]]
) -> tuple[list[str], list[list[str]]]:
    """Convert a generic iterable of rows into a stable (headers, rows)
    pair used by both PDF and XLSX generators.
    """
    h = list(headers)
    r = [list(map(str, row)) for row in rows]
    return h, r
