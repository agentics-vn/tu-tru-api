"""Shared date parsing helper for dd/mm/yyyy format."""

from __future__ import annotations

from datetime import date, datetime


def parse_dmy(value: str) -> date:
    """
    Parse a date string in dd/mm/yyyy format.

    Raises:
        ValueError: if format is invalid.
    """
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        raise ValueError(
            f"Ngày '{value}' không đúng định dạng dd/mm/yyyy"
        )
